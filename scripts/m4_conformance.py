#!/usr/bin/env python3
"""Build restricted M4 conformed facts without emitting disclosure values."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import re
import sqlite3
import sys
import zipfile
from collections import Counter
from contextlib import closing
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Iterable

import source_inventory
from storage import StorageError, current_path, manifest_path, raw_path, require_isolated_build

PIPELINE_VERSION = "0.4.0"
JOIN_REASONS = {"matched", "unmatched", "ambiguous", "late", "ineligible", "terminated"}
SECURITY_STATUSES = {"A", "P", "C", "D"}
SECURITY_CORRECTIONS = {"Y", "N"}
LOAN_CORRECTIONS = {"Y", "N", "A", "D"}
BATCH_SIZE = 10_000

SCHEMA = """
PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS source_manifest (
  source_id INTEGER PRIMARY KEY,
  source_file TEXT NOT NULL UNIQUE,
  source_family TEXT NOT NULL,
  member_name TEXT NOT NULL,
  report_period TEXT NOT NULL,
  publication_date TEXT NOT NULL,
  as_of_timestamp TEXT NOT NULL,
  archive_sha256 TEXT NOT NULL,
  archive_size_bytes INTEGER NOT NULL,
  schema_version TEXT NOT NULL,
  pipeline_version TEXT NOT NULL,
  input_count INTEGER NOT NULL,
  accepted_count INTEGER NOT NULL,
  excluded_count INTEGER NOT NULL,
  rejected_count INTEGER NOT NULL,
  duplicate_count INTEGER NOT NULL,
  quarantined_count INTEGER NOT NULL,
  published_count INTEGER NOT NULL,
  partition_path TEXT,
  partition_sha256 TEXT,
  partition_row_count INTEGER,
  quality_status TEXT NOT NULL CHECK (quality_status IN ('pass', 'fail')),
  CHECK (input_count = accepted_count + excluded_count + rejected_count + duplicate_count),
  CHECK (quarantined_count = rejected_count + duplicate_count)
);

CREATE TABLE IF NOT EXISTS row_disposition (
  source_id INTEGER NOT NULL,
  disposition TEXT NOT NULL,
  reason_code TEXT NOT NULL,
  row_count INTEGER NOT NULL CHECK (row_count >= 0),
  PRIMARY KEY (source_id, disposition, reason_code),
  FOREIGN KEY (source_id) REFERENCES source_manifest(source_id)
);

CREATE TABLE IF NOT EXISTS source_issue (
  source_id INTEGER NOT NULL,
  source_row INTEGER NOT NULL,
  issue_code TEXT NOT NULL,
  detail TEXT NOT NULL,
  FOREIGN KEY (source_id) REFERENCES source_manifest(source_id)
);

CREATE TABLE IF NOT EXISTS fact_security_period (
  security_version_id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL,
  source_row INTEGER NOT NULL,
  report_period TEXT NOT NULL,
  security_id TEXT NOT NULL,
  prefix TEXT NOT NULL,
  security_status TEXT NOT NULL,
  correction_indicator TEXT NOT NULL,
  issuance_upb_cents INTEGER,
  current_upb_cents INTEGER,
  factor_e8 INTEGER,
  loan_count INTEGER,
  legacy_credit_score INTEGER,
  classic_fico INTEGER,
  vs4 INTEGER,
  involuntary_removal_upb_cents INTEGER,
  involuntary_removal_count INTEGER,
  record_hash BLOB NOT NULL,
  UNIQUE (report_period, security_id, source_id),
  FOREIGN KEY (source_id) REFERENCES source_manifest(source_id)
);
CREATE INDEX IF NOT EXISTS idx_security_id_period
  ON fact_security_period (security_id, report_period);

CREATE TABLE IF NOT EXISTS fact_loan_period (
  loan_version_id INTEGER PRIMARY KEY,
  source_id INTEGER NOT NULL,
  source_row INTEGER NOT NULL,
  report_period TEXT NOT NULL,
  loan_id TEXT NOT NULL,
  security_id TEXT,
  prefix TEXT NOT NULL,
  correction_indicator TEXT NOT NULL,
  mortgage_loan_amount_cents INTEGER,
  issuance_upb_cents INTEGER,
  current_upb_cents INTEGER,
  remaining_months_to_maturity INTEGER,
  loan_age INTEGER,
  legacy_credit_score INTEGER,
  classic_fico INTEGER,
  vs4 INTEGER,
  updated_legacy_credit_score INTEGER,
  updated_classic_fico INTEGER,
  updated_vs4 INTEGER,
  days_delinquent INTEGER,
  modification_program TEXT,
  current_deferred_upb_cents INTEGER,
  property_state TEXT,
  seller_name TEXT,
  servicer_name TEXT,
  join_reason TEXT NOT NULL CHECK (join_reason IN ('matched', 'unmatched', 'ambiguous', 'late', 'ineligible', 'terminated')),
  record_hash BLOB NOT NULL,
  UNIQUE (report_period, loan_id, security_id, source_id),
  FOREIGN KEY (source_id) REFERENCES source_manifest(source_id)
);

CREATE TABLE IF NOT EXISTS restatement_lineage (
  entity_type TEXT NOT NULL,
  business_key_hash BLOB NOT NULL,
  report_period TEXT NOT NULL,
  prior_source_id INTEGER NOT NULL,
  replacement_source_id INTEGER NOT NULL,
  precedence_reason TEXT NOT NULL,
  changed_record INTEGER NOT NULL CHECK (changed_record IN (0, 1)),
  PRIMARY KEY (entity_type, business_key_hash, report_period, prior_source_id, replacement_source_id)
);

CREATE TABLE IF NOT EXISTS join_reconciliation (
  report_period TEXT NOT NULL,
  source_family TEXT NOT NULL,
  join_reason TEXT NOT NULL,
  row_count INTEGER NOT NULL,
  PRIMARY KEY (report_period, source_family, join_reason)
);

DROP VIEW IF EXISTS FactSecurityPeriodOriginal;
CREATE VIEW FactSecurityPeriodOriginal AS
SELECT * FROM (
  SELECT f.*, ROW_NUMBER() OVER (
    PARTITION BY f.report_period, f.security_id
    ORDER BY m.as_of_timestamp, m.publication_date, m.source_id
  ) AS version_rank
  FROM fact_security_period f
  JOIN source_manifest m USING (source_id)
  WHERE m.quality_status = 'pass'
) WHERE version_rank = 1;

DROP VIEW IF EXISTS FactSecurityPeriodLatest;
CREATE VIEW FactSecurityPeriodLatest AS
SELECT * FROM (
  SELECT f.*, ROW_NUMBER() OVER (
    PARTITION BY f.report_period, f.security_id
    ORDER BY m.as_of_timestamp DESC, m.publication_date DESC, m.source_id DESC
  ) AS version_rank
  FROM fact_security_period f
  JOIN source_manifest m USING (source_id)
  WHERE m.quality_status = 'pass'
) WHERE version_rank = 1;

DROP VIEW IF EXISTS FactLoanPeriodOriginal;
CREATE VIEW FactLoanPeriodOriginal AS
SELECT * FROM (
  SELECT f.*, ROW_NUMBER() OVER (
    PARTITION BY f.report_period, f.loan_id, COALESCE(f.security_id, '')
    ORDER BY m.as_of_timestamp, m.publication_date, m.source_id
  ) AS version_rank
  FROM fact_loan_period f
  JOIN source_manifest m USING (source_id)
  WHERE m.quality_status = 'pass'
) WHERE version_rank = 1;

DROP VIEW IF EXISTS FactLoanPeriodLatest;
CREATE VIEW FactLoanPeriodLatest AS
SELECT * FROM (
  SELECT f.*, ROW_NUMBER() OVER (
    PARTITION BY f.report_period, f.loan_id, COALESCE(f.security_id, '')
    ORDER BY m.as_of_timestamp DESC, m.publication_date DESC, m.source_id DESC
  ) AS version_rank
  FROM fact_loan_period f
  JOIN source_manifest m USING (source_id)
  WHERE m.quality_status = 'pass'
) WHERE version_rank = 1;
"""


class ConformanceError(ValueError):
    """Expected fail-closed M4 conformance failure."""


@dataclass
class SourceResult:
    input_count: int = 0
    accepted_count: int = 0
    excluded_count: int = 0
    rejected_count: int = 0
    duplicate_count: int = 0
    issues: list[tuple[int, str, str]] | None = None

    def __post_init__(self) -> None:
        if self.issues is None:
            self.issues = []

    @property
    def status(self) -> str:
        reconciles = self.input_count == (
            self.accepted_count
            + self.excluded_count
            + self.rejected_count
            + self.duplicate_count
        )
        return "pass" if reconciles and not self.rejected_count and not self.duplicate_count else "fail"


def publication_date(member_name: str) -> str:
    match = re.fullmatch(r"[a-z]{2}(\d{2})(\d{2})(\d{2})\.txt", member_name)
    if not match:
        raise ConformanceError("embedded member does not contain an exact publication date")
    year, month, day = match.groups()
    return f"20{year}-{month}-{day}"


def parse_scaled(raw: bytes, scale: int, field: str, nullable: bool = True) -> int | None:
    value = raw.strip()
    if not value:
        if nullable:
            return None
        raise ConformanceError(f"{field} is required")
    negative = value.startswith(b"-")
    if negative:
        value = value[1:]
    if value.count(b".") > 1:
        raise ConformanceError(f"{field} is not a valid decimal")
    whole, _, fraction = value.partition(b".")
    if not whole:
        whole = b"0"
    if not whole.isdigit() or (fraction and not fraction.isdigit()) or len(fraction) > scale:
        raise ConformanceError(f"{field} is not a valid decimal")
    result = int(whole) * (10**scale) + int((fraction + b"0" * scale)[:scale] or b"0")
    return -result if negative else result


def parse_integer(raw: bytes, field: str) -> int | None:
    value = raw.strip()
    if not value:
        return None
    try:
        return int(value)
    except ValueError as error:
        raise ConformanceError(f"{field} is not a valid integer") from error


def parse_factor_date(raw: bytes, expected_period: str) -> str:
    value = raw.strip()
    if not re.fullmatch(rb"(0[1-9]|1[0-2])20\d{2}", value):
        raise ConformanceError("Security Factor Date is not MMCCYY")
    period = f"{value[2:].decode()}-{value[:2].decode()}"
    if period != expected_period:
        raise ConformanceError("Security Factor Date does not match publication period")
    return period


def field_positions(headers: list[str], contract: dict[str, Any]) -> dict[str, int | None]:
    positions: dict[str, int | None] = {}
    for field in contract["field_allowlist"]:
        positions[field["target"]] = next(
            (headers.index(name) for name in field["source_names"] if name in headers),
            None,
        )
    return positions


def cell(fields: list[bytes], positions: dict[str, int | None], target: str) -> bytes:
    position = positions.get(target)
    return b"" if position is None else fields[position]


def insert_batches(
    connection: sqlite3.Connection,
    sql: str,
    rows: Iterable[tuple[Any, ...]],
) -> tuple[int, int]:
    accepted = duplicates = 0
    batch: list[tuple[Any, ...]] = []
    for row in rows:
        batch.append(row)
        if len(batch) == BATCH_SIZE:
            before = connection.total_changes
            connection.executemany(sql, batch)
            changed = connection.total_changes - before
            accepted += changed
            duplicates += len(batch) - changed
            batch.clear()
    if batch:
        before = connection.total_changes
        connection.executemany(sql, batch)
        changed = connection.total_changes - before
        accepted += changed
        duplicates += len(batch) - changed
    return accepted, duplicates


def source_metadata(item: dict[str, Any]) -> tuple[str, str, str]:
    member = item["members"][0]["name"]
    published = publication_date(member)
    return member, published, f"{published}T23:59:59Z"


def create_manifest(
    connection: sqlite3.Connection,
    item: dict[str, Any],
    result: SourceResult,
    partition: tuple[str, str, int] | None = None,
) -> int:
    member, published, as_of = source_metadata(item)
    cursor = connection.execute(
        """
        INSERT INTO source_manifest (
          source_file, source_family, member_name, report_period, publication_date,
          as_of_timestamp, archive_sha256, archive_size_bytes, schema_version,
          pipeline_version, input_count, accepted_count, excluded_count,
          rejected_count, duplicate_count, quarantined_count, published_count,
          partition_path, partition_sha256, partition_row_count, quality_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        """,
        (
            item["name"], item["source_family"], member, item["report_period"],
            published, as_of, item["sha256"], item["size_bytes"], item["schema_version"],
            PIPELINE_VERSION, result.input_count, result.accepted_count,
            result.excluded_count, result.rejected_count, result.duplicate_count,
            result.rejected_count + result.duplicate_count,
            result.accepted_count if result.status == "pass" else 0,
            *(partition or (None, None, None)),
            result.status,
        ),
    )
    source_id = int(cursor.lastrowid)
    dispositions = {
        "accepted": result.accepted_count,
        "excluded": result.excluded_count,
        "rejected": result.rejected_count,
        "duplicate": result.duplicate_count,
        "quarantined": result.rejected_count + result.duplicate_count,
        "published-to-conformed": result.accepted_count if result.status == "pass" else 0,
    }
    connection.executemany(
        "INSERT INTO row_disposition VALUES (?, ?, ?, ?)",
        [
            (source_id, disposition, "SOURCE_CONFORMANCE", count)
            for disposition, count in dispositions.items()
        ],
    )
    connection.executemany(
        "INSERT INTO source_issue VALUES (?, ?, ?, ?)",
        [(source_id, row, code, detail) for row, code, detail in result.issues or []],
    )
    return source_id


def supplemental_result(item: dict[str, Any]) -> SourceResult:
    count = int(item["members"][0]["physical_row_count"])
    return SourceResult(input_count=count, excluded_count=count)


def iter_security_rows(
    archive_path: Path,
    item: dict[str, Any],
    contract: dict[str, Any],
    result: SourceResult,
) -> Iterable[tuple[Any, ...]]:
    with zipfile.ZipFile(archive_path) as archive, archive.open(item["members"][0]["name"]) as stream:
        headers = stream.readline().decode("utf-8-sig").rstrip("\r\n").split("|")
        positions = field_positions(headers, contract)
        required = ["prefix", "security_id", "security_factor_date", "security_correction_indicator", "security_status"]
        if any(positions.get(name) is None for name in required):
            raise ConformanceError("security schema omits a required allowlisted field")
        for row_number, raw in enumerate(stream, start=2):
            if not raw.strip():
                continue
            result.input_count += 1
            fields = raw.rstrip(b"\r\n").split(b"|")
            try:
                if len(fields) != len(headers):
                    raise ConformanceError("row width does not match approved schema")
                prefix = cell(fields, positions, "prefix").strip().decode()
                security_id = cell(fields, positions, "security_id").strip().decode()
                if not prefix or not security_id:
                    raise ConformanceError("security business key is incomplete")
                report_period = parse_factor_date(
                    cell(fields, positions, "security_factor_date"), item["report_period"]
                )
                correction = cell(fields, positions, "security_correction_indicator").strip().decode()
                status = cell(fields, positions, "security_status").strip().decode()
                if correction not in SECURITY_CORRECTIONS:
                    raise ConformanceError("Security Data Correction Indicator is invalid")
                if status not in SECURITY_STATUSES:
                    raise ConformanceError("Security Status Indicator is invalid")
                values = (
                    parse_scaled(cell(fields, positions, "issuance_security_upb"), 2, "Issuance Investor Security UPB"),
                    parse_scaled(cell(fields, positions, "current_security_upb"), 2, "Current Investor Security UPB"),
                    parse_scaled(cell(fields, positions, "security_factor"), 8, "Security Factor"),
                    parse_integer(cell(fields, positions, "loan_count"), "Loan Count"),
                    parse_integer(cell(fields, positions, "legacy_credit_score"), "legacy credit score"),
                    parse_integer(cell(fields, positions, "classic_fico"), "Classic FICO"),
                    parse_integer(cell(fields, positions, "vs4"), "VS4"),
                    parse_scaled(cell(fields, positions, "involuntary_removal_upb"), 2, "Involuntary Loan Removal UPB"),
                    parse_integer(cell(fields, positions, "involuntary_removal_count"), "Involuntary Loan Removal count"),
                )
                record_hash = hashlib.sha256(b"\x1f".join(cell(fields, positions, target) for target in positions)).digest()
                yield (
                    row_number, report_period, security_id, prefix, status, correction,
                    *values, record_hash,
                )
            except (ConformanceError, UnicodeDecodeError) as error:
                result.rejected_count += 1
                result.issues.append((row_number, "INVALID_SECURITY_ROW", str(error)))


def security_index(connection: sqlite3.Connection, report_period: str) -> dict[str, list[str]]:
    index: dict[str, list[str]] = {}
    for security_id, status in connection.execute(
        """
        SELECT f.security_id, f.security_status
        FROM fact_security_period f JOIN source_manifest m USING (source_id)
        WHERE f.report_period = ? AND m.quality_status = 'pass'
        """,
        (report_period,),
    ):
        index.setdefault(security_id, []).append(status)
    return index


def late_security(
    connection: sqlite3.Connection,
    security_id: str,
    report_period: str,
    cache: dict[tuple[str, str], bool],
) -> bool:
    key = (security_id, report_period)
    if key not in cache:
        cache[key] = connection.execute(
            "SELECT 1 FROM fact_security_period WHERE security_id = ? AND report_period > ? LIMIT 1",
            key,
        ).fetchone() is not None
    return cache[key]


def classify_join(
    correction: str,
    security_id: str | None,
    matches: list[str],
    is_late: bool,
) -> str:
    if correction == "D" or any(status in {"P", "C", "D"} for status in matches):
        return "terminated"
    if security_id is None:
        return "ineligible"
    if len(matches) > 1:
        return "ambiguous"
    if len(matches) == 1:
        return "matched"
    return "late" if is_late else "unmatched"


def iter_loan_rows(
    connection: sqlite3.Connection,
    archive_path: Path,
    item: dict[str, Any],
    contract: dict[str, Any],
    result: SourceResult,
    securities: dict[str, list[str]],
    late_cache: dict[tuple[str, str], bool],
) -> Iterable[tuple[Any, ...]]:
    with zipfile.ZipFile(archive_path) as archive, archive.open(item["members"][0]["name"]) as stream:
        headers = stream.readline().decode("utf-8-sig").rstrip("\r\n").split("|")
        positions = field_positions(headers, contract)
        required = ["loan_id", "loan_correction_indicator", "prefix", "security_id"]
        if any(positions.get(name) is None for name in required):
            raise ConformanceError("loan schema omits a required allowlisted field")
        for row_number, raw in enumerate(stream, start=2):
            if not raw.strip():
                continue
            result.input_count += 1
            fields = raw.rstrip(b"\r\n").split(b"|")
            try:
                if len(fields) != len(headers):
                    raise ConformanceError("row width does not match approved schema")
                loan_id = cell(fields, positions, "loan_id").strip().decode()
                security_id = cell(fields, positions, "security_id").strip().decode() or None
                prefix = cell(fields, positions, "prefix").strip().decode()
                correction = cell(fields, positions, "loan_correction_indicator").strip().decode()
                if not loan_id or not prefix:
                    raise ConformanceError("loan business key is incomplete")
                if correction not in LOAN_CORRECTIONS:
                    raise ConformanceError("Loan Correction Indicator is invalid")
                matches = [] if security_id is None else securities.get(security_id, [])
                join_reason = classify_join(
                    correction,
                    security_id,
                    matches,
                    bool(security_id) and not matches and late_security(
                        connection, security_id, item["report_period"], late_cache
                    ),
                )
                values = (
                    parse_scaled(cell(fields, positions, "mortgage_loan_amount"), 2, "Mortgage Loan Amount"),
                    parse_scaled(cell(fields, positions, "issuance_loan_upb"), 2, "Issuance Investor Loan UPB"),
                    parse_scaled(cell(fields, positions, "current_loan_upb"), 2, "Current Investor Loan UPB"),
                    parse_integer(cell(fields, positions, "remaining_months_to_maturity"), "Remaining Months to Maturity"),
                    parse_integer(cell(fields, positions, "loan_age"), "Loan Age"),
                    parse_integer(cell(fields, positions, "legacy_credit_score"), "legacy credit score"),
                    parse_integer(cell(fields, positions, "classic_fico"), "Classic FICO"),
                    parse_integer(cell(fields, positions, "vs4"), "VS4"),
                    parse_integer(cell(fields, positions, "updated_legacy_credit_score"), "updated legacy credit score"),
                    parse_integer(cell(fields, positions, "updated_classic_fico"), "Updated Classic FICO"),
                    parse_integer(cell(fields, positions, "updated_vs4"), "Updated VS4"),
                    parse_integer(cell(fields, positions, "days_delinquent"), "Days Delinquent"),
                    cell(fields, positions, "modification_program").strip().decode() or None,
                    parse_scaled(cell(fields, positions, "current_deferred_upb"), 2, "Current Deferred UPB"),
                    cell(fields, positions, "property_state").strip().decode() or None,
                    cell(fields, positions, "seller_name").strip().decode() or None,
                    cell(fields, positions, "servicer_name").strip().decode() or None,
                )
                record_hash = hashlib.sha256(b"\x1f".join(cell(fields, positions, target) for target in positions)).digest()
                yield (
                    row_number, item["report_period"], loan_id, security_id, prefix,
                    correction, *values, join_reason, record_hash,
                )
            except (ConformanceError, UnicodeDecodeError) as error:
                result.rejected_count += 1
                result.issues.append((row_number, "INVALID_LOAN_ROW", str(error)))


def stage_supplemental(connection: sqlite3.Connection, item: dict[str, Any]) -> None:
    result = supplemental_result(item)
    source_id = create_manifest(connection, item, result)
    connection.execute(
        "UPDATE row_disposition SET reason_code = 'SUPPLEMENTAL_NATIVE_GRAIN_M5_DEFERRED' WHERE source_id = ? AND disposition = 'excluded'",
        (source_id,),
    )


def stage_security(
    connection: sqlite3.Connection,
    input_dir: Path,
    item: dict[str, Any],
    contract: dict[str, Any],
    seen_keys: set[bytes],
) -> None:
    result = SourceResult()
    source_id = create_manifest(connection, item, result)
    sql = """
      INSERT OR IGNORE INTO fact_security_period (
        source_id, source_row, report_period, security_id, prefix, security_status,
        correction_indicator, issuance_upb_cents, current_upb_cents, factor_e8,
        loan_count, legacy_credit_score, classic_fico, vs4,
        involuntary_removal_upb_cents, involuntary_removal_count, record_hash
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    def rows() -> Iterable[tuple[Any, ...]]:
        for row in iter_security_rows(input_dir / item["name"], item, contract, result):
            key = hashlib.blake2b(
                f"{row[1]}\x1f{row[2]}".encode(), digest_size=16
            ).digest()
            if key in seen_keys:
                result.duplicate_count += 1
                continue
            seen_keys.add(key)
            yield (source_id, *row)

    accepted, duplicates = insert_batches(connection, sql, rows())
    result.accepted_count = accepted
    result.duplicate_count += duplicates
    finalize_manifest(connection, source_id, result)


def stage_loan(
    connection: sqlite3.Connection,
    input_dir: Path,
    item: dict[str, Any],
    contract: dict[str, Any],
    securities: dict[str, list[str]],
    late_cache: dict[tuple[str, str], bool],
) -> None:
    result = SourceResult()
    source_id = create_manifest(connection, item, result)
    sql = """
      INSERT OR IGNORE INTO fact_loan_period (
        source_id, source_row, report_period, loan_id, security_id, prefix,
        correction_indicator, mortgage_loan_amount_cents, issuance_upb_cents,
        current_upb_cents, remaining_months_to_maturity, loan_age,
        legacy_credit_score, classic_fico, vs4, updated_legacy_credit_score,
        updated_classic_fico, updated_vs4, days_delinquent, modification_program,
        current_deferred_upb_cents, property_state, seller_name, servicer_name,
        join_reason, record_hash
      ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """
    rows = (
        (source_id, *row)
        for row in iter_loan_rows(
            connection, input_dir / item["name"], item, contract, result,
            securities, late_cache,
        )
    )
    accepted, duplicates = insert_batches(connection, sql, rows)
    result.accepted_count, result.duplicate_count = accepted, duplicates
    finalize_manifest(connection, source_id, result)


LOAN_PARTITION_COLUMNS = [
    "report_period", "loan_id", "security_id", "prefix", "correction_indicator",
    "mortgage_loan_amount_cents", "issuance_upb_cents", "current_upb_cents",
    "remaining_months_to_maturity", "loan_age", "legacy_credit_score",
    "classic_fico", "vs4", "updated_legacy_credit_score", "updated_classic_fico",
    "updated_vs4", "days_delinquent", "modification_program",
    "current_deferred_upb_cents", "property_state", "seller_name", "servicer_name",
    "join_reason", "record_hash_sha256", "source_family", "source_file",
    "source_row", "schema_version", "publication_date", "as_of_timestamp",
]


def stage_loan_partition(
    connection: sqlite3.Connection,
    input_dir: Path,
    partition_dir: Path,
    item: dict[str, Any],
    contract: dict[str, Any],
    securities: dict[str, list[str]],
    late_cache: dict[tuple[str, str], bool],
    seen_keys: set[bytes],
) -> None:
    result = SourceResult()
    member, published, as_of = source_metadata(item)
    relative = Path("FactLoanPeriod") / item["report_period"] / f"{item['name']}.csv.gz"
    output = partition_dir / relative
    temporary = output.with_suffix(output.suffix + ".building")
    output.parent.mkdir(parents=True, exist_ok=True)
    join_counts: Counter[str] = Counter()
    with gzip.open(temporary, "wt", encoding="utf-8", newline="", compresslevel=1) as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(LOAN_PARTITION_COLUMNS)
        for row in iter_loan_rows(
            connection, input_dir / item["name"], item, contract, result,
            securities, late_cache,
        ):
            key = hashlib.blake2b(
                f"{row[1]}\x1f{row[2]}\x1f{row[3] or ''}".encode(),
                digest_size=16,
            ).digest()
            if key in seen_keys:
                result.duplicate_count += 1
                continue
            seen_keys.add(key)
            result.accepted_count += 1
            join_counts[row[23]] += 1
            writer.writerow(
                [*row[1:23], row[23], row[24].hex(), item["source_family"],
                 item["name"], row[0], item["schema_version"], published, as_of]
            )
    partition = None
    if result.status == "pass":
        temporary.replace(output)
        partition = (
            str(relative), source_inventory.sha256_file(output), result.accepted_count
        )
    else:
        temporary.unlink(missing_ok=True)
    source_id = create_manifest(connection, item, result, partition)
    if result.status == "pass":
        connection.executemany(
            """
            INSERT INTO join_reconciliation VALUES (?, ?, ?, ?)
            ON CONFLICT(report_period, source_family, join_reason)
            DO UPDATE SET row_count = row_count + excluded.row_count
            """,
            [
                (item["report_period"], item["source_family"], reason, count)
                for reason, count in join_counts.items()
            ],
        )
    if result.status != "pass":
        connection.execute(
            "UPDATE row_disposition SET reason_code='FAIL_CLOSED_LOAN_PARTITION' WHERE source_id=? AND disposition IN ('duplicate','rejected','quarantined')",
            (source_id,),
        )


def finalize_manifest(connection: sqlite3.Connection, source_id: int, result: SourceResult) -> None:
    connection.execute(
        """
        UPDATE source_manifest SET input_count=?, accepted_count=?, excluded_count=?,
          rejected_count=?, duplicate_count=?, quarantined_count=?, published_count=?,
          quality_status=? WHERE source_id=?
        """,
        (
            result.input_count, result.accepted_count, result.excluded_count,
            result.rejected_count, result.duplicate_count,
            result.rejected_count + result.duplicate_count,
            result.accepted_count if result.status == "pass" else 0,
            result.status, source_id,
        ),
    )
    connection.execute("DELETE FROM row_disposition WHERE source_id=?", (source_id,))
    dispositions = {
        "accepted": result.accepted_count,
        "excluded": result.excluded_count,
        "rejected": result.rejected_count,
        "duplicate": result.duplicate_count,
        "quarantined": result.rejected_count + result.duplicate_count,
        "published-to-conformed": result.accepted_count if result.status == "pass" else 0,
    }
    connection.executemany(
        "INSERT INTO row_disposition VALUES (?, ?, 'SOURCE_CONFORMANCE', ?)",
        [(source_id, disposition, count) for disposition, count in dispositions.items()],
    )
    connection.executemany(
        "INSERT INTO source_issue VALUES (?, ?, ?, ?)",
        [(source_id, row, code, detail) for row, code, detail in result.issues or []],
    )


def refresh_lineage(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM restatement_lineage")
    for entity, table, key_columns in (
        ("security", "fact_security_period", "f.security_id"),
        ("loan", "fact_loan_period", "f.loan_id || ':' || COALESCE(f.security_id, '')"),
    ):
        connection.execute(
            f"""
            INSERT INTO restatement_lineage
            SELECT ?, sha256_key(business_key), report_period, prior_source_id, source_id,
                   'later accepted source version', record_hash != prior_hash
            FROM (
              SELECT {key_columns} AS business_key, f.report_period, f.source_id, f.record_hash,
                     LAG(f.source_id) OVER (PARTITION BY f.report_period, {key_columns} ORDER BY m.as_of_timestamp, m.source_id) prior_source_id,
                     LAG(f.record_hash) OVER (PARTITION BY f.report_period, {key_columns} ORDER BY m.as_of_timestamp, m.source_id) prior_hash
              FROM {table} f JOIN source_manifest m USING (source_id)
              WHERE m.quality_status='pass'
            ) WHERE prior_source_id IS NOT NULL
            """,
            (entity,),
        )


def refresh_join_reconciliation(connection: sqlite3.Connection) -> None:
    connection.execute("DELETE FROM join_reconciliation")
    connection.execute(
        """
        INSERT INTO join_reconciliation
        SELECT f.report_period, m.source_family, f.join_reason, COUNT(*)
        FROM fact_loan_period f JOIN source_manifest m USING (source_id)
        WHERE m.quality_status='pass'
        GROUP BY f.report_period, m.source_family, f.join_reason
        """
    )


def register_functions(connection: sqlite3.Connection) -> None:
    connection.create_function(
        "sha256_key", 1,
        lambda value: hashlib.sha256(str(value).encode("utf-8")).digest(),
        deterministic=True,
    )


def normalized_snapshot(connection: sqlite3.Connection, as_of: str | None = None) -> str:
    clauses = "" if as_of is None else " AND m.as_of_timestamp <= ?"
    params: tuple[Any, ...] = () if as_of is None else (as_of,)
    digest = hashlib.sha256()
    for table, partition, keys in (
        (
            "fact_security_period",
            "f.report_period, f.security_id",
            "report_period, security_id, hex(record_hash)",
        ),
        (
            "fact_loan_period",
            "f.report_period, f.loan_id, COALESCE(f.security_id,'')",
            "report_period, loan_id, COALESCE(security_id,''), hex(record_hash), join_reason",
        ),
    ):
        for row in connection.execute(
            f"""
            SELECT {keys} FROM (
              SELECT f.*, ROW_NUMBER() OVER (
                PARTITION BY {partition}
                ORDER BY m.as_of_timestamp DESC, m.publication_date DESC, m.source_id DESC
              ) AS snapshot_rank
              FROM {table} f JOIN source_manifest m USING(source_id)
              WHERE m.quality_status='pass'{clauses}
            ) WHERE snapshot_rank=1 ORDER BY 1,2,3
            """,
            params,
        ):
            digest.update(json.dumps(row, separators=(",", ":")).encode("utf-8"))
    partition_clause = "" if as_of is None else " AND as_of_timestamp <= ?"
    for row in connection.execute(
        """
        SELECT report_period, source_family, source_file, partition_sha256,
               partition_row_count
        FROM source_manifest
        WHERE quality_status='pass' AND partition_path IS NOT NULL
        """ + partition_clause + " ORDER BY report_period, source_family, source_file",
        params,
    ):
        digest.update(json.dumps(row, separators=(",", ":")).encode("utf-8"))
    return digest.hexdigest()


def verify(connection: sqlite3.Connection, expected_sources: int) -> dict[str, Any]:
    source_count, failed = connection.execute(
        "SELECT COUNT(*), SUM(quality_status != 'pass') FROM source_manifest"
    ).fetchone()
    if source_count != expected_sources or failed:
        raise ConformanceError("source population is incomplete or contains failed sources")
    if connection.execute(
        "SELECT COUNT(*) FROM source_manifest WHERE input_count != accepted_count + excluded_count + rejected_count + duplicate_count"
    ).fetchone()[0]:
        raise ConformanceError("source dispositions do not reconcile")
    loan_count = connection.execute(
        """
        SELECT COALESCE(SUM(accepted_count),0) FROM source_manifest
        WHERE quality_status='pass' AND source_family LIKE 'monthly-loan-level%'
        """
    ).fetchone()[0]
    join_count = connection.execute("SELECT COALESCE(SUM(row_count),0) FROM join_reconciliation").fetchone()[0]
    if loan_count != join_count:
        raise ConformanceError("loan join reasons do not reconcile")
    totals = connection.execute(
        """
        SELECT SUM(input_count), SUM(accepted_count), SUM(excluded_count),
               SUM(rejected_count), SUM(duplicate_count), SUM(quarantined_count),
               SUM(published_count) FROM source_manifest
        """
    ).fetchone()
    joins = dict(connection.execute("SELECT join_reason, SUM(row_count) FROM join_reconciliation GROUP BY join_reason"))
    return {
        "sources": source_count,
        "input": totals[0],
        "accepted": totals[1],
        "excluded": totals[2],
        "rejected": totals[3],
        "duplicate": totals[4],
        "quarantined": totals[5],
        "published": totals[6],
        "security_facts": connection.execute("SELECT COUNT(*) FROM FactSecurityPeriodLatest").fetchone()[0],
        "loan_facts": loan_count,
        "joins": {reason: joins.get(reason, 0) for reason in sorted(JOIN_REASONS)},
        "snapshot_sha256": normalized_snapshot(connection),
    }


def build(
    input_dir: Path,
    database: Path,
    security_contract_path: Path,
    loan_contract_path: Path,
    inventory_cache: Path,
    partition_dir: Path | None = None,
    incremental: bool = False,
    only_sources: set[str] | None = None,
) -> dict[str, Any]:
    security_contract = source_inventory.load_contract(security_contract_path)
    loan_contract = source_inventory.load_contract(loan_contract_path)
    bundle = source_inventory.load_contract_bundle([security_contract_path, loan_contract_path])
    inventory = source_inventory.build_inventory(input_dir, bundle, inventory_cache)
    if inventory["m4_readiness"]["status"] != "ready":
        raise ConformanceError("approved source inventory is not ready")
    all_approved = [item for item in inventory["files"] if item["kind"] == "approved-m4"]
    approved = all_approved
    if only_sources:
        approved = [item for item in approved if item["name"] in only_sources]
    database.parent.mkdir(parents=True, exist_ok=True)
    partition_dir = partition_dir or database.parent / "m4-conformed"
    target = database if incremental else database.with_suffix(database.suffix + ".building")
    if not incremental and target.exists():
        target.unlink()
    with closing(sqlite3.connect(target)) as connection:
        register_functions(connection)
        connection.execute("PRAGMA page_size=65536")
        connection.execute("PRAGMA cache_size=-262144")
        connection.execute("PRAGMA temp_store=MEMORY")
        connection.execute("PRAGMA synchronous=OFF")
        connection.execute("PRAGMA journal_mode=OFF" if not incremental else "PRAGMA journal_mode=WAL")
        connection.executescript(SCHEMA)
        existing = {
            row[0]: row[1:]
            for row in connection.execute(
                "SELECT source_file, archive_sha256, partition_path, partition_sha256 FROM source_manifest"
            )
        }
        selected = []
        for item in approved:
            if item["name"] in existing:
                archive_sha, partition_path, partition_sha = existing[item["name"]]
                if archive_sha != item["sha256"]:
                    raise ConformanceError("an immutable source archive changed after loading")
                if partition_path:
                    output = partition_dir / partition_path
                    if not output.is_file() or source_inventory.sha256_file(output) != partition_sha:
                        raise ConformanceError("a restricted conformed partition is missing or changed")
                continue
            selected.append(item)
        supplemental = [item for item in selected if not item["members"][0].get("has_header")]
        security = [item for item in selected if item["source_family"].startswith("monthly-security-core")]
        loans = [item for item in selected if item["source_family"].startswith("monthly-loan-level")]
        with connection:
            for item in supplemental:
                stage_supplemental(connection, item)
            cached_security_period = None
            security_keys: set[bytes] = set()
            for item in sorted(security, key=lambda value: (value["report_period"], value["source_family"])):
                if cached_security_period != item["report_period"]:
                    cached_security_period = item["report_period"]
                    security_keys = set()
                stage_security(connection, input_dir, item, security_contract, security_keys)
        cached_period = None
        securities: dict[str, list[str]] = {}
        late_cache: dict[tuple[str, str], bool] = {}
        loan_keys: set[bytes] = set()
        for item in sorted(loans, key=lambda value: (value["report_period"], value["source_family"])):
            if cached_period != item["report_period"]:
                cached_period = item["report_period"]
                securities = security_index(connection, cached_period)
                loan_keys = set()
            with connection:
                stage_loan_partition(
                    connection, input_dir, partition_dir, item, loan_contract,
                    securities, late_cache, loan_keys,
                )
        with connection:
            refresh_lineage(connection)
        expected_sources = len(all_approved)
        summary = verify(connection, expected_sources)
    if not incremental:
        target.replace(database)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=raw_path())
    parser.add_argument("--database", type=Path, default=current_path("m4.sqlite"))
    parser.add_argument("--security-contract", type=Path, default=Path("contracts/m4-source-contract.json"))
    parser.add_argument("--loan-contract", type=Path, default=Path("contracts/m4-loan-source-contract.json"))
    parser.add_argument("--inventory-cache", type=Path, default=manifest_path("source-inventory.json"))
    parser.add_argument("--partition-dir", type=Path, default=current_path("loan"))
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--only-source", action="append", default=[])
    parser.add_argument("--json", action="store_true", help="emit value-free reconciliation JSON")
    args = parser.parse_args()
    try:
        if not args.incremental:
            require_isolated_build(args.database)
        summary = build(
            args.input, args.database, args.security_contract, args.loan_contract,
            args.inventory_cache, args.partition_dir, args.incremental,
            set(args.only_source) or None,
        )
    except (ConformanceError, source_inventory.InventoryError, StorageError, OSError, sqlite3.Error, zipfile.BadZipFile) as error:
        print(f"M4 conformance failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            "M4 conformance: PASS | "
            f"sources={summary['sources']} input={summary['input']} accepted={summary['accepted']} "
            f"excluded={summary['excluded']} rejected={summary['rejected']} duplicate={summary['duplicate']} "
            f"published={summary['published']} security={summary['security_facts']} loan={summary['loan_facts']}"
        )
        print("Join reconciliation: " + " ".join(f"{reason}={count}" for reason, count in summary["joins"].items()))
        print(f"Normalized snapshot SHA-256: {summary['snapshot_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
