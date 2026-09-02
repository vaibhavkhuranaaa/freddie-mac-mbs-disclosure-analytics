#!/usr/bin/env python3
"""Persist governed investigation records separately from disclosure facts."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sqlite3
import threading
import uuid
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


PRIORITIES = {"low", "medium", "high"}
STATUSES = {"open", "in_progress", "resolved"}
MUTABLE_FIELDS = {"title", "owner", "priority", "status", "summary", "resolution"}


def now() -> str:
    return datetime.now(UTC).isoformat()


def canonical(value: object) -> str:
    return json.dumps(value, sort_keys=True, separators=(",", ":"))


def digest(value: object | None) -> str | None:
    return hashlib.sha256(canonical(value).encode()).hexdigest() if value is not None else None


class InvestigationStore:
    def __init__(self, database: Path):
        self.database = database
        backup = os.environ.get("MBS_INVESTIGATION_BACKUP", "").strip()
        self.backup = Path(backup) if backup else None
        self._write_lock = threading.RLock()

    def connect(self) -> sqlite3.Connection:
        connection = sqlite3.connect(self.database, timeout=5)
        connection.row_factory = sqlite3.Row
        connection.execute("PRAGMA foreign_keys = ON")
        connection.execute("PRAGMA busy_timeout = 5000")
        return connection

    def initialize(self) -> None:
        with self._write_lock:
            self.database.parent.mkdir(parents=True, exist_ok=True)
            if self.backup and self.backup.is_file():
                shutil.copyfile(self.backup, self.database)
            with closing(self.connect()) as connection, connection:
                journal_mode = os.environ.get("MBS_SQLITE_JOURNAL_MODE", "WAL")
                if journal_mode not in {"DELETE", "WAL"}:
                    raise ValueError("MBS_SQLITE_JOURNAL_MODE must be DELETE or WAL")
                connection.execute(f"PRAGMA journal_mode = {journal_mode}")
                connection.executescript(
                    """
                BEGIN IMMEDIATE;
                CREATE TABLE IF NOT EXISTS investigation (
                    id TEXT PRIMARY KEY,
                    title TEXT NOT NULL,
                    owner TEXT NOT NULL,
                    priority TEXT NOT NULL CHECK (priority IN ('low', 'medium', 'high')),
                    status TEXT NOT NULL CHECK (status IN ('open', 'in_progress', 'resolved')),
                    summary TEXT NOT NULL,
                    resolution TEXT,
                    release_id TEXT NOT NULL,
                    report_period TEXT NOT NULL,
                    correction_view TEXT NOT NULL,
                    metric_version TEXT NOT NULL,
                    filter_context_json TEXT NOT NULL,
                    evidence_json TEXT NOT NULL,
                    created_at TEXT NOT NULL,
                    updated_at TEXT NOT NULL
                );
                CREATE TABLE IF NOT EXISTS investigation_audit (
                    event_id TEXT PRIMARY KEY,
                    investigation_id TEXT NOT NULL REFERENCES investigation(id),
                    action TEXT NOT NULL,
                    actor TEXT NOT NULL,
                    event_at TEXT NOT NULL,
                    before_sha256 TEXT,
                    after_sha256 TEXT NOT NULL
                );
                CREATE INDEX IF NOT EXISTS investigation_status_updated
                    ON investigation(status, updated_at DESC);
                CREATE INDEX IF NOT EXISTS investigation_audit_record
                    ON investigation_audit(investigation_id, event_at);
                CREATE TABLE IF NOT EXISTS api_request_audit (
                    event_id TEXT PRIMARY KEY,
                    request_at TEXT NOT NULL,
                    method TEXT NOT NULL,
                    path TEXT NOT NULL,
                    status INTEGER NOT NULL,
                    actor TEXT NOT NULL,
                    authorized INTEGER NOT NULL CHECK (authorized IN (0, 1)),
                    duration_ms REAL NOT NULL
                );
                CREATE INDEX IF NOT EXISTS api_request_audit_time
                    ON api_request_audit(request_at DESC);
                COMMIT;
                """
                )
            self._persist()

    def create(self, payload: dict[str, Any], actor: str) -> dict[str, Any]:
        record = self._validated_create(payload)
        timestamp = now()
        record.update(
            {
                "id": f"INV-{timestamp[:10].replace('-', '')}-{uuid.uuid4().hex[:8]}",
                "created_at": timestamp,
                "updated_at": timestamp,
            }
        )
        with self._write_lock:
            with closing(self.connect()) as connection, connection:
                connection.execute(
                """
                INSERT INTO investigation (
                    id, title, owner, priority, status, summary, resolution,
                    release_id, report_period, correction_view, metric_version,
                    filter_context_json, evidence_json, created_at, updated_at
                ) VALUES (
                    :id, :title, :owner, :priority, :status, :summary, :resolution,
                    :release_id, :report_period, :correction_view, :metric_version,
                    :filter_context_json, :evidence_json, :created_at, :updated_at
                )
                """,
                    record,
                )
                self._audit(connection, record["id"], "create", actor, None, self._public(record))
            self._persist()
        return self._public(record)

    def update(self, investigation_id: str, changes: dict[str, Any], actor: str) -> dict[str, Any]:
        unknown = set(changes) - MUTABLE_FIELDS
        if unknown:
            raise ValueError(f"immutable or unknown fields: {', '.join(sorted(unknown))}")
        with self._write_lock:
            with closing(self.connect()) as connection, connection:
                row = connection.execute("SELECT * FROM investigation WHERE id = ?", (investigation_id,)).fetchone()
                if row is None:
                    raise KeyError(investigation_id)
                before = self._public(dict(row))
                candidate = {**before, **changes}
                self._validate_mutable(candidate)
                assignments = ", ".join(f"{field} = ?" for field in changes)
                updated_at = now()
                connection.execute(
                    f"UPDATE investigation SET {assignments}, updated_at = ? WHERE id = ?",
                    [*(changes[field] for field in changes), updated_at, investigation_id],
                )
                updated = dict(connection.execute("SELECT * FROM investigation WHERE id = ?", (investigation_id,)).fetchone())
                after = self._public(updated)
                self._audit(connection, investigation_id, "update", actor, before, after)
            self._persist()
        return after

    def list(self, status: str | None = None) -> list[dict[str, Any]]:
        if status is not None and status not in STATUSES:
            raise ValueError(f"invalid status: {status}")
        sql = "SELECT * FROM investigation"
        parameters: list[str] = []
        if status:
            sql += " WHERE status = ?"
            parameters.append(status)
        sql += " ORDER BY updated_at DESC, id"
        with closing(self.connect()) as connection, connection:
            return [self._public(dict(row)) for row in connection.execute(sql, parameters)]

    def audit(self, investigation_id: str) -> list[dict[str, Any]]:
        with closing(self.connect()) as connection, connection:
            return [dict(row) for row in connection.execute(
                "SELECT * FROM investigation_audit WHERE investigation_id = ? ORDER BY event_at, event_id",
                (investigation_id,),
            )]

    def record_api_request(self, method: str, path: str, status: int, actor: str, authorized: bool, duration_ms: float) -> None:
        if not method or not path or status < 100 or duration_ms < 0:
            raise ValueError("invalid API audit event")
        with self._write_lock:
            with closing(self.connect()) as connection, connection:
                connection.execute(
                    "INSERT INTO api_request_audit VALUES (?, ?, ?, ?, ?, ?, ?, ?)",
                    (uuid.uuid4().hex, now(), method, path, status, actor, int(authorized), duration_ms),
                )
            self._persist()

    def list_api_audit(self, limit: int = 100) -> list[dict[str, Any]]:
        if limit < 1 or limit > 1000:
            raise ValueError("audit limit must be between 1 and 1000")
        with closing(self.connect()) as connection, connection:
            return [dict(row) for row in connection.execute(
                "SELECT * FROM api_request_audit ORDER BY request_at DESC, event_id DESC LIMIT ?",
                (limit,),
            )]

    def _persist(self) -> None:
        if not self.backup:
            return
        self.backup.parent.mkdir(parents=True, exist_ok=True)
        temporary = self.backup.with_name(f".{self.backup.name}.{uuid.uuid4().hex}.tmp")
        try:
            shutil.copyfile(self.database, temporary)
            os.replace(temporary, self.backup)
        finally:
            temporary.unlink(missing_ok=True)

    @staticmethod
    def _validated_create(payload: dict[str, Any]) -> dict[str, Any]:
        required = {
            "title", "owner", "priority", "status", "summary", "release_id",
            "report_period", "correction_view", "metric_version", "filter_context", "evidence",
        }
        missing = sorted(required - set(payload))
        if missing:
            raise ValueError(f"missing fields: {', '.join(missing)}")
        candidate = {field: payload[field] for field in required}
        candidate["resolution"] = payload.get("resolution")
        InvestigationStore._validate_mutable(candidate)
        if candidate["correction_view"] not in {"latest", "original"}:
            raise ValueError("invalid correction_view")
        if not isinstance(candidate["filter_context"], dict):
            raise ValueError("filter_context must be an object")
        if not isinstance(candidate["evidence"], list) or not candidate["evidence"]:
            raise ValueError("evidence must be a non-empty list")
        for item in candidate["evidence"]:
            if not isinstance(item, dict) or not {"contract_id", "component", "period", "correction_view", "provenance"}.issubset(item):
                raise ValueError("every evidence item needs contract, component, period, correction view, and provenance")
        candidate["filter_context_json"] = canonical(candidate.pop("filter_context"))
        candidate["evidence_json"] = canonical(candidate.pop("evidence"))
        return candidate

    @staticmethod
    def _validate_mutable(candidate: dict[str, Any]) -> None:
        for field in ("title", "owner", "summary"):
            if not isinstance(candidate.get(field), str) or not candidate[field].strip():
                raise ValueError(f"{field} is required")
        if candidate.get("priority") not in PRIORITIES:
            raise ValueError("invalid priority")
        if candidate.get("status") not in STATUSES:
            raise ValueError("invalid status")
        if candidate.get("status") == "resolved" and not str(candidate.get("resolution") or "").strip():
            raise ValueError("resolved investigations require a resolution")

    @staticmethod
    def _public(record: dict[str, Any]) -> dict[str, Any]:
        result = dict(record)
        if "filter_context_json" in result:
            result["filter_context"] = json.loads(result.pop("filter_context_json"))
        if "evidence_json" in result:
            result["evidence"] = json.loads(result.pop("evidence_json"))
        return result

    @staticmethod
    def _audit(
        connection: sqlite3.Connection,
        investigation_id: str,
        action: str,
        actor: str,
        before: dict[str, Any] | None,
        after: dict[str, Any],
    ) -> None:
        if not actor.strip():
            raise ValueError("actor is required")
        connection.execute(
            "INSERT INTO investigation_audit VALUES (?, ?, ?, ?, ?, ?, ?)",
            (uuid.uuid4().hex, investigation_id, action, actor, now(), digest(before), digest(after)),
        )


def default_database() -> Path:
    root = Path(__file__).resolve().parents[1]
    data_root = Path(os.environ.get("MBS_DATA_ROOT", root.parent / f"{root.name}-data"))
    return data_root / "product/investigations.sqlite"


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--database", type=Path, default=default_database())
    subparsers = parser.add_subparsers(dest="command", required=True)
    subparsers.add_parser("init")
    listing = subparsers.add_parser("list")
    listing.add_argument("--status", choices=sorted(STATUSES))
    creation = subparsers.add_parser("create")
    creation.add_argument("--input", type=Path, required=True)
    creation.add_argument("--actor", required=True)
    update = subparsers.add_parser("update")
    update.add_argument("id")
    update.add_argument("--input", type=Path, required=True)
    update.add_argument("--actor", required=True)
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    store = InvestigationStore(args.database)
    store.initialize()
    if args.command == "init":
        print(f"Investigation store: pass ({args.database})")
    elif args.command == "list":
        print(json.dumps(store.list(args.status), indent=2))
    elif args.command == "create":
        print(json.dumps(store.create(json.loads(args.input.read_text(encoding="utf-8")), args.actor), indent=2))
    elif args.command == "update":
        print(json.dumps(store.update(args.id, json.loads(args.input.read_text(encoding="utf-8")), args.actor), indent=2))


if __name__ == "__main__":
    main()
