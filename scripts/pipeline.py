#!/usr/bin/env python3
"""Validate Freddie Mac issuance extracts and publish governed aggregates."""

from __future__ import annotations

import argparse
import csv
import hashlib
import io
import json
import os
import re
import sqlite3
import subprocess
import zipfile
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Iterable

PIPELINE_VERSION = "0.2.0"
OFFICIAL_ZIP_PATTERN = re.compile(r"^FRE_IS_(20\d{2})(0[1-9]|1[0-2])\.zip$")
MONTH_PATTERN = re.compile(r"^20\d{2}-(0[1-9]|1[0-2])$")
SEMVER_PATTERN = re.compile(r"^\d+\.\d+\.\d+$")

# Exact ordered-header fingerprints observed in the authorized official files.
# A new header must be reviewed and added as a new schema version; it must not be
# silently accepted as an existing version.
OFFICIAL_SCHEMAS = {
    "d51157584e87d8ea5ace4804b3b429184a0c7e2ae30b6484f4e5c4cc31207f46": {
        "version": "fre-is-legacy-v1",
        "column_count": 96,
        "period_min": None,
        "period_max": "2025-11",
    },
    "03eb8bdeba4ff7726b35058c9cb2e2bb46183131cc66b38e9dd2d9b9e545a541": {
        "version": "fre-is-fico-v2",
        "column_count": 98,
        "period_min": "2025-12",
        "period_max": None,
    },
}

OFFICIAL_REQUIRED = {
    "Security Identifier",
    "Prefix",
    "Issuance Investor Security UPB",
    "Current Investor Security UPB",
    "Security Factor",
    "Security Data Correction Indicator",
}

SAMPLE_REQUIRED = {
    "report_month",
    "security_id",
    "security_type",
    "issuance_upb",
    "current_upb",
    "factor",
    "cpr_pct",
    "published_files",
    "expected_files",
    "release_lag_days",
    "revision_flag",
}

SCHEMA = """
DROP TABLE IF EXISTS quality_issue;
DROP TABLE IF EXISTS source_manifest;
DROP TABLE IF EXISTS monthly_security;

CREATE TABLE monthly_security (
 report_month TEXT NOT NULL,
 security_id TEXT NOT NULL,
 security_type TEXT NOT NULL,
 issuance_upb REAL NOT NULL,
 current_upb REAL NOT NULL,
 factor REAL NOT NULL,
 cpr_pct REAL NOT NULL,
 published_files INTEGER NOT NULL,
 expected_files INTEGER NOT NULL,
 release_lag_days INTEGER NOT NULL,
 revision_flag INTEGER NOT NULL,
 source_file TEXT NOT NULL,
 source_row INTEGER NOT NULL,
 schema_version TEXT NOT NULL,
 PRIMARY KEY (report_month, security_id)
);

CREATE TABLE source_manifest (
 source_file TEXT PRIMARY KEY,
 report_period TEXT,
 sha256 TEXT NOT NULL,
 loaded_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP,
 pipeline_version TEXT NOT NULL,
 schema_version TEXT NOT NULL,
 input_count INTEGER NOT NULL,
 accepted_count INTEGER NOT NULL,
 excluded_count INTEGER NOT NULL,
 rejected_count INTEGER NOT NULL,
 duplicate_count INTEGER NOT NULL,
 quarantined_count INTEGER NOT NULL,
 published_count INTEGER NOT NULL DEFAULT 0,
 quality_status TEXT NOT NULL CHECK (quality_status IN ('pass', 'fail'))
);

CREATE TABLE quality_issue (
 issue_id INTEGER PRIMARY KEY AUTOINCREMENT,
 source_file TEXT NOT NULL,
 source_row INTEGER NOT NULL,
 severity TEXT NOT NULL CHECK (severity IN ('info', 'error')),
 issue_code TEXT NOT NULL,
 detail TEXT NOT NULL,
 FOREIGN KEY (source_file) REFERENCES source_manifest(source_file)
);
"""


class PipelineError(ValueError):
    """Base class for expected data-pipeline failures."""


class SourceValidationError(PipelineError):
    """The file or archive cannot be treated as a supported source."""


class QualityGateError(PipelineError):
    """One or more source rows failed validation or duplicate checks."""


class ExcludedRow(PipelineError):
    """A source row is valid but outside the issuance aggregate population."""


@dataclass(frozen=True)
class QualityIssue:
    source_row: int
    severity: str
    code: str
    detail: str


@dataclass
class SourceBatch:
    source_file: str
    report_period: str | None
    sha256: str
    schema_version: str
    input_count: int = 0
    records: list[tuple] = field(default_factory=list)
    issues: list[QualityIssue] = field(default_factory=list)
    duplicate_count: int = 0

    @property
    def rejected_count(self) -> int:
        return len(
            [
                issue
                for issue in self.issues
                if issue.severity == "error" and issue.code != "DUPLICATE_BUSINESS_KEY"
            ]
        )

    @property
    def excluded_count(self) -> int:
        return len([issue for issue in self.issues if issue.severity == "info"])

    @property
    def quarantined_count(self) -> int:
        return self.rejected_count + self.duplicate_count

    @property
    def quality_status(self) -> str:
        reconciles = self.input_count == (
            len(self.records) + self.excluded_count + self.rejected_count + self.duplicate_count
        )
        has_errors = any(issue.severity == "error" for issue in self.issues)
        return "pass" if self.records and not has_errors and reconciles else "fail"


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def parse_flag(value: str | None) -> int:
    normalized = (value or "").strip().lower()
    if normalized in {"true", "1", "yes", "y"}:
        return 1
    if normalized in {"false", "0", "no", "n", ""}:
        return 0
    raise PipelineError("revision flag must be true/false or 1/0")


def validate_month(value: str) -> str:
    normalized = value.strip()
    if not MONTH_PATTERN.fullmatch(normalized):
        raise PipelineError("report_month must be YYYY-MM")
    return normalized


def validate_record(record: tuple) -> tuple:
    month, security_id, security_type, issuance, current, factor, cpr, published, expected, lag, *_ = record
    validate_month(month)
    if not security_id.strip():
        raise PipelineError("security identifier is required")
    if not security_type.strip():
        raise PipelineError("security type is required")
    if min(issuance, current, cpr, published, expected, lag) < 0:
        raise PipelineError("numeric measures cannot be negative")
    if issuance <= 0 or current > issuance:
        raise PipelineError("balances violate issuance/current UPB constraints")
    if not 0 < factor <= 1:
        raise PipelineError("security factor must be greater than 0 and at most 1")
    if cpr > 100:
        raise PipelineError("CPR percent cannot exceed 100")
    if published > expected:
        raise PipelineError("published file count cannot exceed expected file count")
    return record


def identify_official_schema(headers: list[str], report_period: str) -> str:
    missing = OFFICIAL_REQUIRED - set(headers)
    if missing:
        raise SourceValidationError(f"missing required official columns: {', '.join(sorted(missing))}")
    fingerprint = hashlib.sha256("|".join(headers).encode("utf-8")).hexdigest()
    schema = OFFICIAL_SCHEMAS.get(fingerprint)
    if not schema:
        raise SourceValidationError(
            f"unrecognized official header fingerprint {fingerprint[:12]} ({len(headers)} columns)"
        )
    if len(headers) != schema["column_count"]:
        raise SourceValidationError(
            f"{schema['version']} expects {schema['column_count']} columns, found {len(headers)}"
        )
    period_min = schema["period_min"]
    period_max = schema["period_max"]
    if period_min and report_period < period_min:
        raise SourceValidationError(f"{schema['version']} is not valid before {period_min}")
    if period_max and report_period > period_max:
        raise SourceValidationError(f"{schema['version']} is not valid after {period_max}")
    return str(schema["version"])


def official_record(row: dict[str | None, str | list[str] | None], report_period: str, path: Path, line: int, schema_version: str) -> tuple:
    if None in row:
        raise PipelineError("row has more fields than the official header")
    balance_fields = (
        "Issuance Investor Security UPB",
        "Current Investor Security UPB",
        "Security Factor",
    )
    blank_balances = [not str(row.get(key) or "").strip() for key in balance_fields]
    if all(blank_balances) and str(row.get("Security Status Indicator") or "").strip() == "C":
        raise ExcludedRow("status-C security has no issuance balances and is excluded from issuance aggregates")
    if any(blank_balances):
        raise PipelineError("issuance UPB, current UPB, and security factor are required together")
    try:
        record = (
            report_period,
            str(row["Security Identifier"] or "").strip(),
            str(row["Prefix"] or "").strip(),
            float(str(row["Issuance Investor Security UPB"] or "")),
            float(str(row["Current Investor Security UPB"] or "")),
            float(str(row["Security Factor"] or "")),
            0.0,
            1,
            1,
            0,
            parse_flag(str(row["Security Data Correction Indicator"] or "")),
            path.name,
            line,
            schema_version,
        )
    except (KeyError, TypeError, ValueError) as error:
        raise PipelineError(f"required official value is invalid: {error}") from error
    return validate_record(record)


def parse_official_zip(path: Path) -> SourceBatch:
    match = OFFICIAL_ZIP_PATTERN.fullmatch(path.name)
    if not match:
        raise SourceValidationError("official ZIP name must be FRE_IS_YYYYMM.zip")
    report_period = f"{match.group(1)}-{match.group(2)}"
    expected_member = f"FRE_IS_{match.group(1)}{match.group(2)}.txt"
    try:
        archive = zipfile.ZipFile(path)
    except zipfile.BadZipFile as error:
        raise SourceValidationError("invalid ZIP archive") from error
    with archive:
        members = [item for item in archive.infolist() if not item.is_dir()]
        if len(members) != 1 or members[0].filename != expected_member:
            found = ", ".join(item.filename for item in members) or "no files"
            raise SourceValidationError(f"expected only {expected_member}; found {found}")
        if members[0].flag_bits & 0x1:
            raise SourceValidationError("encrypted official archives are not supported")
        with archive.open(members[0]) as binary:
            text = io.TextIOWrapper(binary, encoding="utf-8-sig", newline="")
            reader = csv.DictReader(text, delimiter="|")
            headers = reader.fieldnames or []
            schema_version = identify_official_schema(headers, report_period)
            batch = SourceBatch(path.name, report_period, sha256_file(path), schema_version)
            for line, row in enumerate(reader, start=2):
                batch.input_count += 1
                try:
                    batch.records.append(official_record(row, report_period, path, line, schema_version))
                except ExcludedRow as error:
                    batch.issues.append(QualityIssue(line, "info", "EXCLUDED_CANCELLED_SECURITY", str(error)))
                except PipelineError as error:
                    batch.issues.append(QualityIssue(line, "error", "INVALID_ROW", str(error)))
    if batch.input_count == 0:
        batch.issues.append(QualityIssue(1, "error", "EMPTY_SOURCE", "official source contains no data rows"))
    return batch


def sample_record(row: dict[str, str], path: Path, line: int) -> tuple:
    try:
        record = (
            validate_month(row["report_month"]),
            row["security_id"].strip(),
            row["security_type"].strip(),
            float(row["issuance_upb"]),
            float(row["current_upb"]),
            float(row["factor"]),
            float(row["cpr_pct"]),
            int(row["published_files"]),
            int(row["expected_files"]),
            int(row["release_lag_days"]),
            parse_flag(row["revision_flag"]),
            path.name,
            line,
            "sample-v1",
        )
    except (KeyError, TypeError, ValueError) as error:
        raise PipelineError(f"required delimited value is invalid: {error}") from error
    return validate_record(record)


def parse_delimited(path: Path) -> SourceBatch:
    delimiter = "|" if path.suffix.lower() == ".txt" else ","
    batch = SourceBatch(path.name, None, sha256_file(path), "sample-v1")
    with path.open(newline="", encoding="utf-8-sig") as handle:
        reader = csv.DictReader(handle, delimiter=delimiter)
        missing = SAMPLE_REQUIRED - set(reader.fieldnames or [])
        if missing:
            raise SourceValidationError(f"missing required columns: {', '.join(sorted(missing))}")
        periods: set[str] = set()
        for line, row in enumerate(reader, start=2):
            batch.input_count += 1
            try:
                record = sample_record(row, path, line)
                batch.records.append(record)
                periods.add(record[0])
            except PipelineError as error:
                batch.issues.append(QualityIssue(line, "error", "INVALID_ROW", str(error)))
    if periods:
        first, last = min(periods), max(periods)
        batch.report_period = first if first == last else f"{first}..{last}"
    if batch.input_count == 0:
        batch.issues.append(QualityIssue(1, "error", "EMPTY_SOURCE", "source contains no data rows"))
    return batch


def parse_source(path: Path) -> SourceBatch:
    if path.suffix.lower() == ".zip":
        return parse_official_zip(path)
    return parse_delimited(path)


def source_failure(path: Path, error: Exception) -> SourceBatch:
    period = None
    match = OFFICIAL_ZIP_PATTERN.fullmatch(path.name)
    if match:
        period = f"{match.group(1)}-{match.group(2)}"
    batch = SourceBatch(path.name, period, sha256_file(path), "unrecognized")
    batch.input_count = 1
    batch.issues.append(QualityIssue(0, "error", "INVALID_SOURCE", str(error)))
    return batch


def deduplicate(batch: SourceBatch, seen: set[tuple[str, str]]) -> None:
    accepted: list[tuple] = []
    for record in batch.records:
        key = (record[0], record[1])
        if key in seen:
            batch.duplicate_count += 1
            batch.issues.append(
                QualityIssue(
                    record[12],
                    "error",
                    "DUPLICATE_BUSINESS_KEY",
                    "duplicate report_month/security_id",
                )
            )
            continue
        seen.add(key)
        accepted.append(record)
    batch.records = accepted


def insert_batch(connection: sqlite3.Connection, batch: SourceBatch) -> None:
    connection.execute(
        """
        INSERT INTO source_manifest (
          source_file, report_period, sha256, pipeline_version, schema_version,
          input_count, accepted_count, excluded_count, rejected_count,
          duplicate_count, quarantined_count, published_count, quality_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 0, ?)
        """,
        (
            batch.source_file,
            batch.report_period,
            batch.sha256,
            PIPELINE_VERSION,
            batch.schema_version,
            batch.input_count,
            len(batch.records),
            batch.excluded_count,
            batch.rejected_count,
            batch.duplicate_count,
            batch.quarantined_count,
            batch.quality_status,
        ),
    )
    connection.executemany(
        "INSERT INTO monthly_security VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        batch.records,
    )
    connection.executemany(
        "INSERT INTO quality_issue (source_file, source_row, severity, issue_code, detail) VALUES (?, ?, ?, ?, ?)",
        [
            (batch.source_file, issue.source_row, issue.severity, issue.code, issue.detail)
            for issue in batch.issues
        ],
    )


def load(input_dir: Path, database: Path) -> int:
    files = sorted([*input_dir.glob("*.csv"), *input_dir.glob("*.txt"), *input_dir.glob("*.zip")])
    if not files:
        raise SourceValidationError(f"no .csv, .txt, or .zip files found in {input_dir}")
    database.parent.mkdir(parents=True, exist_ok=True)
    seen: set[tuple[str, str]] = set()
    batches: list[SourceBatch] = []
    with sqlite3.connect(database) as connection:
        connection.execute("PRAGMA foreign_keys = ON")
        connection.executescript(SCHEMA)
        for path in files:
            try:
                batch = parse_source(path)
            except (OSError, PipelineError, UnicodeError, csv.Error) as error:
                batch = source_failure(path, error)
            deduplicate(batch, seen)
            insert_batch(connection, batch)
            batches.append(batch)
    failed = [batch for batch in batches if batch.quality_status == "fail"]
    if failed:
        rejected = sum(batch.rejected_count for batch in failed)
        duplicates = sum(batch.duplicate_count for batch in failed)
        raise QualityGateError(
            f"{len(failed)} source file(s) failed quality checks; "
            f"{rejected} rejected and {duplicates} duplicate row(s) quarantined"
        )
    return sum(len(batch.records) for batch in batches)


def pipeline_revision() -> str:
    configured = os.environ.get("PIPELINE_REVISION", "").strip()
    if configured:
        return configured
    result = subprocess.run(
        ["git", "rev-parse", "--short=12", "HEAD"],
        cwd=Path(__file__).resolve().parents[1],
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout.strip() if result.returncode == 0 else "uncommitted"


def build_id(manifest: Iterable[sqlite3.Row]) -> str:
    evidence = [
        {
            "source_file": row["source_file"],
            "sha256": row["sha256"],
            "schema_version": row["schema_version"],
            "accepted_count": row["accepted_count"],
            "excluded_count": row["excluded_count"],
        }
        for row in manifest
    ]
    encoded = json.dumps(
        {"pipeline_version": PIPELINE_VERSION, "sources": evidence},
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def publish(database: Path, output: Path) -> None:
    with sqlite3.connect(database) as connection:
        connection.row_factory = sqlite3.Row
        manifest = list(connection.execute("SELECT * FROM source_manifest ORDER BY source_file"))
        if not manifest:
            raise QualityGateError("source manifest is empty")
        if any(row["quality_status"] != "pass" for row in manifest):
            raise QualityGateError("publication blocked because source quality status is not pass")
        totals = {
            key: sum(row[key] for row in manifest)
            for key in (
                "input_count",
                "accepted_count",
                "excluded_count",
                "rejected_count",
                "duplicate_count",
                "quarantined_count",
                "published_count",
            )
        }
        if totals["input_count"] != (
            totals["accepted_count"]
            + totals["excluded_count"]
            + totals["rejected_count"]
            + totals["duplicate_count"]
        ):
            raise QualityGateError("source manifest counts do not reconcile")
        if totals["quarantined_count"] != totals["rejected_count"] + totals["duplicate_count"]:
            raise QualityGateError("quarantine counts do not reconcile")
        months = [
            dict(row)
            for row in connection.execute(
                """
                SELECT report_month AS month,
                       COUNT(*) AS security_count,
                       SUM(issuance_upb) AS issuance_upb,
                       SUM(current_upb) AS current_upb,
                       AVG(factor) AS average_factor,
                       SUM(revision_flag) AS correction_count
                FROM monthly_security
                GROUP BY report_month
                ORDER BY report_month
                """
            )
        ]
        observation_count = connection.execute("SELECT COUNT(*) FROM monthly_security").fetchone()[0]
        if observation_count != totals["accepted_count"]:
            raise QualityGateError("accepted source rows do not equal stored observations")
        connection.execute("UPDATE source_manifest SET published_count = accepted_count")
        totals["published_count"] = totals["accepted_count"]
    if not months:
        raise QualityGateError("no records are available to publish")
    metadata = {
        "observation_count": observation_count,
        "source_file_count": len(manifest),
        "period_start": months[0]["month"],
        "period_end": months[-1]["month"],
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z"),
        "pipeline_version": PIPELINE_VERSION,
        "pipeline_revision": pipeline_revision(),
        "build_id": build_id(manifest),
        "schema_versions": sorted({row["schema_version"] for row in manifest}),
        "quality": {
            "status": "pass",
            "input_count": totals["input_count"],
            "accepted_count": totals["accepted_count"],
            "excluded_count": totals["excluded_count"],
            "rejected_count": totals["rejected_count"],
            "duplicate_count": totals["duplicate_count"],
            "quarantined_count": totals["quarantined_count"],
            "published_count": totals["published_count"],
        },
    }
    if not SEMVER_PATTERN.fullmatch(metadata["pipeline_version"]):
        raise QualityGateError("pipeline version is not semantic-version formatted")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps({"months": months, "metadata": metadata}, indent=2) + "\n", encoding="utf-8")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", type=Path, required=True)
    parser.add_argument("--database", type=Path, default=Path("local/mbs.sqlite"))
    parser.add_argument("--output", type=Path, default=Path("app/data/dashboard.json"))
    args = parser.parse_args()
    try:
        count = load(args.input, args.database)
        publish(args.database, args.output)
    except (OSError, PipelineError, sqlite3.Error) as error:
        parser.exit(1, f"Pipeline failed: {error}\n")
    print(f"Loaded {count} accepted records into {args.database} and wrote {args.output}.")


if __name__ == "__main__":
    main()
