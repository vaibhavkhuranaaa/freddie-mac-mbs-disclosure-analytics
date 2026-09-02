#!/usr/bin/env python3
"""Build, verify, and atomically promote the restricted M4/M5 v2 bundle."""

from __future__ import annotations

import argparse
import json
import math
import shutil
import sqlite3
import sys
from contextlib import closing
from datetime import UTC, datetime
from pathlib import Path

import m4_conformance
import m5_metric_engine
import source_inventory
import storage
import verify_m5_metrics


class ReleaseError(RuntimeError):
    """The M5.4 release lifecycle failed closed."""


MISSION_RANGE_ISSUES = {
    "mission_density_score is outside its approved range",
    "mission_criteria_share is outside its approved range",
}


def require_headroom() -> None:
    root = storage.data_root()
    active_bytes = storage.tree_bytes(storage.current_root())
    free_bytes = shutil.disk_usage(root).free
    required = active_bytes + storage.MIN_FREE_BYTES
    if free_bytes < required:
        raise ReleaseError(
            f"insufficient isolated-build headroom: free={free_bytes} required={required}"
        )


def require_resume_headroom(run_root: Path) -> None:
    failed_database = run_root / "release" / "m4.sqlite.building"
    if not failed_database.is_file():
        raise ReleaseError("resume headroom check requires the failed M4 database")
    free_bytes = shutil.disk_usage(storage.data_root()).free
    required = failed_database.stat().st_size + storage.MIN_FREE_BYTES
    if free_bytes < required:
        raise ReleaseError(
            f"insufficient security-resume headroom: free={free_bytes} required={required}"
        )


def require_finalization_headroom() -> None:
    free_bytes = shutil.disk_usage(storage.data_root()).free
    if free_bytes < storage.MIN_FREE_BYTES:
        raise ReleaseError(
            f"insufficient finalization headroom: free={free_bytes} required={storage.MIN_FREE_BYTES}"
        )


def finalize_sqlite_database(database: Path) -> None:
    if not database.is_file():
        raise ReleaseError(f"SQLite finalization target is missing: {database.name}")
    with closing(sqlite3.connect(database)) as connection:
        busy, _, _ = connection.execute("PRAGMA wal_checkpoint(TRUNCATE)").fetchone()
        if busy:
            raise ReleaseError(f"SQLite WAL checkpoint is busy: {database.name}")
        mode = connection.execute("PRAGMA journal_mode=DELETE").fetchone()[0]
        if mode.lower() != "delete":
            raise ReleaseError(f"SQLite journal finalization failed: {database.name}")
    sidecars = [
        database.with_name(database.name + suffix)
        for suffix in ("-wal", "-shm")
        if database.with_name(database.name + suffix).exists()
    ]
    if sidecars:
        raise ReleaseError(f"SQLite sidecars remain after finalization: {database.name}")


def write_ceiling(stable_bytes: int, release_id: str) -> int:
    gib = 1024**3
    ceiling = math.ceil(stable_bytes / gib) * gib
    path = storage.manifest_path(storage.STORAGE_CEILING_NAME)
    temporary = path.with_suffix(".json.building")
    temporary.write_text(
        json.dumps(
            {
                "version": 1,
                "release_id": release_id,
                "measured_stable_bytes": stable_bytes,
                "ceiling_bytes": ceiling,
                "rounding": "next whole GiB",
                "approval_id": "M5-STORAGE-BUDGET-EXCEPTION-2026-08-24",
            },
            indent=2,
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    temporary.replace(path)
    return ceiling


def archive_verified_legacy_current(
    active_release: Path, release_id: str
) -> Path | None:
    legacy = storage.data_root() / "current"
    if not legacy.exists():
        return None
    if legacy.resolve() == active_release.resolve():
        raise ReleaseError("refusing to remove the active release")
    expected = {"issuance.sqlite", "m4.sqlite", "m5.sqlite", "loan"}
    if not legacy.is_dir() or {item.name for item in legacy.iterdir()} != expected:
        raise ReleaseError("legacy release cleanup target is not the verified v1 layout")
    destination = storage.data_root() / "rollback" / f"legacy-v1-before-{release_id}"
    if destination.exists():
        raise ReleaseError("legacy rollback destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    legacy.replace(destination)
    return destination


def resume_security_rule_revalidation(
    failed_database: Path,
    database: Path,
    partitions: Path,
    security_contract_path: Path,
    loan_contract_path: Path,
    inventory_cache: Path,
) -> dict:
    """Reuse checked loan artifacts after a security-only monotonic rule relaxation."""
    if database.exists() or not failed_database.is_file():
        raise ReleaseError("security-rule resume requires one failed full M4 database")
    security_contract = source_inventory.load_contract(security_contract_path)
    loan_contract = source_inventory.load_contract(loan_contract_path)
    new_fingerprint = m4_conformance.build_fingerprint(
        security_contract, loan_contract
    )
    with closing(sqlite3.connect(failed_database)) as connection:
        prior_fingerprints = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT build_fingerprint FROM source_manifest"
            )
        }
        if len(prior_fingerprints) != 1 or new_fingerprint in prior_fingerprints:
            raise ReleaseError("failed M4 database does not have one prior fingerprint")
        issues = {
            row[0]
            for row in connection.execute(
                """
                SELECT DISTINCT i.detail
                FROM source_issue i
                JOIN source_manifest m ON m.source_id=i.source_id
                WHERE m.quality_status != 'pass'
                """
            )
        }
        failed_families = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT source_family FROM source_manifest WHERE quality_status != 'pass'"
            )
        }
        if issues != MISSION_RANGE_ISSUES or any(
            not family.startswith("monthly-security-core")
            for family in failed_families
        ):
            raise ReleaseError("failed M4 database is outside the approved mission-range resume")
        loan_rows = connection.execute(
            """
            SELECT source_file, partition_path, partition_sha256
            FROM source_manifest
            WHERE source_family LIKE 'monthly-loan-level%'
              AND quality_status='pass'
              AND rejected_count=0 AND duplicate_count=0 AND quarantined_count=0
            ORDER BY source_file
            """
        ).fetchall()
        if len(loan_rows) != 35:
            raise ReleaseError("security-rule resume requires all 35 verified loan sources")
        for source_file, relative, expected_sha in loan_rows:
            output = partitions / relative
            if (
                not output.is_file()
                or source_inventory.sha256_file(output) != expected_sha
            ):
                raise ReleaseError(
                    f"loan partition changed before resume: {source_file}"
                )
        security_ids = [
            row[0]
            for row in connection.execute(
                "SELECT source_id FROM source_manifest WHERE source_family LIKE 'monthly-security-%'"
            )
        ]
        if len(security_ids) != 71:
            raise ReleaseError("security-rule resume requires all 71 security sources")
        placeholders = ",".join("?" for _ in security_ids)
        with connection:
            connection.execute("DELETE FROM restatement_lineage")
            connection.execute(
                f"DELETE FROM fact_security_period WHERE source_id IN ({placeholders})",
                security_ids,
            )
            connection.execute(
                f"DELETE FROM source_issue WHERE source_id IN ({placeholders})",
                security_ids,
            )
            connection.execute(
                f"DELETE FROM row_disposition WHERE source_id IN ({placeholders})",
                security_ids,
            )
            connection.execute(
                f"DELETE FROM source_manifest WHERE source_id IN ({placeholders})",
                security_ids,
            )
            connection.execute(
                "UPDATE source_manifest SET build_fingerprint=?",
                (new_fingerprint,),
            )
    failed_database.replace(database)
    return m4_conformance.build(
        storage.raw_path(),
        database,
        security_contract_path,
        loan_contract_path,
        inventory_cache,
        partitions,
        incremental=True,
    )


def build_release(
    release_id: str,
    ops_root: Path | None,
    resume_security_rules: bool = False,
    resume_promotion: bool = False,
) -> dict:
    root = storage.data_root()
    run_root = root / "build" / release_id
    if resume_security_rules:
        require_resume_headroom(run_root)
    elif resume_promotion:
        require_finalization_headroom()
    else:
        require_headroom()
    bundle = run_root / "release"
    if run_root.exists() and not (resume_security_rules or resume_promotion):
        raise ReleaseError("isolated run directory already exists")
    bundle.mkdir(
        parents=True,
        exist_ok=resume_security_rules or resume_promotion,
    )

    issuance = bundle / "issuance.sqlite"
    if not issuance.exists():
        shutil.copy2(storage.current_path("issuance.sqlite"), issuance)
    m4_database = bundle / "m4.sqlite"
    partitions = bundle / "loan"
    m5_database = bundle / "m5.sqlite"
    security_contract = Path("contracts/m4-source-contract.json")
    loan_contract = Path("contracts/m4-loan-source-contract.json")
    catalog = Path("contracts/m5-metric-catalog.json")
    inventory_cache = storage.manifest_path("source-inventory.json")

    if resume_promotion:
        full_m4 = m4_conformance.verify_release(
            storage.raw_path(), m4_database, security_contract, loan_contract,
            inventory_cache, partitions,
        )
        full_m5 = verify_m5_metrics.verify(
            m5_database, m4_database, catalog
        )
    elif resume_security_rules:
        full_m4 = resume_security_rule_revalidation(
            m4_database.with_suffix(m4_database.suffix + ".building"),
            m4_database,
            partitions,
            security_contract,
            loan_contract,
            inventory_cache,
        )
    else:
        full_m4 = m4_conformance.build(
            storage.raw_path(), m4_database, security_contract, loan_contract,
            inventory_cache, partitions,
        )
    if not resume_promotion:
        repeat_m4 = m4_conformance.build(
            storage.raw_path(), m4_database, security_contract, loan_contract,
            inventory_cache, partitions, incremental=True,
        )
        second_repeat_m4 = m4_conformance.build(
            storage.raw_path(), m4_database, security_contract, loan_contract,
            inventory_cache, partitions, incremental=True,
        )
        if not (full_m4 == repeat_m4 == second_repeat_m4):
            raise ReleaseError("M4 full/incremental/repeat snapshots differ")

        full_m5 = m5_metric_engine.build(
            m4_database, partitions, issuance, m5_database, catalog,
            security_contract, loan_contract,
        )
        repeat_m5 = m5_metric_engine.build(
            m4_database, partitions, issuance, m5_database, catalog,
            security_contract, loan_contract, incremental=True,
        )
        if full_m5 != repeat_m5:
            raise ReleaseError("M5 full/incremental snapshots differ")

        m4_conformance.verify_release(
            storage.raw_path(), m4_database, security_contract, loan_contract,
            inventory_cache, partitions,
        )
        verify_m5_metrics.verify(m5_database, m4_database, catalog)

    finalize_sqlite_database(m4_database)
    finalize_sqlite_database(m5_database)
    finalize_sqlite_database(issuance)

    promotion = storage.promote_release(bundle, release_id)
    active = storage.current_root()
    m4_conformance.verify_release(
        storage.raw_path(), active / "m4.sqlite", security_contract, loan_contract,
        inventory_cache, active / "loan",
    )
    verify_m5_metrics.verify(active / "m5.sqlite", active / "m4.sqlite", catalog)

    rollback = archive_verified_legacy_current(active, release_id)
    try:
        run_root.rmdir()
    except OSError:
        pass
    stable_bytes = storage.tree_bytes(root / "raw") + storage.tree_bytes(active)
    ceiling = write_ceiling(stable_bytes, release_id)
    return {
        "status": "pass",
        "release": promotion,
        "m4": full_m4,
        "m5": full_m5,
        "stable_bytes": stable_bytes,
        "ceiling_bytes": ceiling,
        "rollback_path": None if rollback is None else str(rollback),
        "rollback_bytes": 0 if rollback is None else storage.tree_bytes(rollback),
        "final_preflight": "pending explicit rollback cleanup authorization",
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-id",
        default=datetime.now(UTC).strftime("m5-4-v2-%Y%m%dT%H%M%SZ"),
    )
    parser.add_argument("--ops-root", type=Path)
    parser.add_argument(
        "--resume-security-rules",
        action="store_true",
        help="resume a failed full build after the approved mission-range rule relaxation",
    )
    parser.add_argument(
        "--resume-promotion",
        action="store_true",
        help="reverify and promote a complete staged bundle after finalization",
    )
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        if args.resume_security_rules and args.resume_promotion:
            raise ReleaseError("resume modes are mutually exclusive")
        result = build_release(
            args.release_id,
            args.ops_root,
            resume_security_rules=args.resume_security_rules,
            resume_promotion=args.resume_promotion,
        )
    except (
        ReleaseError,
        storage.StorageError,
        m4_conformance.ConformanceError,
        m5_metric_engine.MetricError,
        verify_m5_metrics.VerificationError,
        OSError,
    ) as error:
        print(f"M5.4 release failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(result, sort_keys=True))
    else:
        print(
            "M5.4 release: PASS | "
            f"release={result['release']['release_id']} "
            f"stable={result['stable_bytes']} ceiling={result['ceiling_bytes']}"
        )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
