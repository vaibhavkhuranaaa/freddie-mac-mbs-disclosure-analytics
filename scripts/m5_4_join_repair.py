#!/usr/bin/env python3
"""Repair the November 2025 join partition in a new immutable M5.4 release."""

from __future__ import annotations

import argparse
import os
import shutil
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import m4_conformance
import m5_4_release
import m5_metric_engine
import source_inventory
import storage
import verify_m5_metrics


class RepairError(RuntimeError):
    """The scoped M5.4 join repair failed closed."""


TARGET_SOURCE = "fu251106.zip"
TARGET_PERIOD = "2025-11"
TARGET_FAMILY = "monthly-loan-level-1"
TARGET_ROWS = 13_099_503


def hardlink_tree(source: Path, destination: Path) -> None:
    destination.mkdir(parents=True)
    for item in sorted(source.rglob("*")):
        relative = item.relative_to(source)
        output = destination / relative
        if item.is_dir():
            output.mkdir()
        elif item.is_file():
            os.link(item, output)
        else:
            raise RepairError(f"unsupported partition entry: {relative}")


def prepare_bundle(active: Path, bundle: Path) -> tuple[Path, Path, Path, Path]:
    if bundle.exists():
        raise RepairError("isolated repair bundle already exists")
    bundle.mkdir(parents=True)
    issuance = bundle / "issuance.sqlite"
    m4_database = bundle / "m4.sqlite"
    m5_database = bundle / "m5.sqlite"
    partitions = bundle / "loan"
    shutil.copy2(active / "issuance.sqlite", issuance)
    shutil.copy2(active / "m4.sqlite", m4_database)
    hardlink_tree(active / "loan", partitions)
    return issuance, m4_database, m5_database, partitions


def prepare_m4_repair(
    database: Path,
    partitions: Path,
    security_contract_path: Path,
    loan_contract_path: Path,
) -> None:
    security_contract = source_inventory.load_contract(security_contract_path)
    loan_contract = source_inventory.load_contract(loan_contract_path)
    new_fingerprint = m4_conformance.build_fingerprint(
        security_contract, loan_contract
    )
    with closing(sqlite3.connect(database)) as connection:
        prior_fingerprints = {
            row[0]
            for row in connection.execute(
                "SELECT DISTINCT build_fingerprint FROM source_manifest"
            )
        }
        if len(prior_fingerprints) != 1 or new_fingerprint in prior_fingerprints:
            raise RepairError("repair requires one prior M4 fingerprint")
        joins = dict(
            connection.execute(
                "SELECT join_reason, SUM(row_count) FROM join_reconciliation GROUP BY join_reason"
            )
        )
        if joins.get("late", 0) != TARGET_ROWS or any(
            joins.get(reason, 0)
            for reason in ("ambiguous", "ineligible", "terminated", "unmatched")
        ):
            raise RepairError("active release is outside the scoped stale-join repair")
        row = connection.execute(
            """
            SELECT source_id, partition_path, partition_sha256, accepted_count
            FROM source_manifest WHERE source_file=? AND source_family=?
            """,
            (TARGET_SOURCE, TARGET_FAMILY),
        ).fetchone()
        if row is None or row[3] != TARGET_ROWS:
            raise RepairError("target loan source does not match the approved repair scope")
        source_id, relative, expected_sha, _ = row
        target_partition = partitions / relative
        if (
            not target_partition.is_file()
            or source_inventory.sha256_file(target_partition) != expected_sha
        ):
            raise RepairError("target loan partition changed before repair")
        with connection:
            connection.execute(
                "DELETE FROM source_issue WHERE source_id=?", (source_id,)
            )
            connection.execute(
                "DELETE FROM row_disposition WHERE source_id=?", (source_id,)
            )
            connection.execute(
                "DELETE FROM source_manifest WHERE source_id=?", (source_id,)
            )
            connection.execute(
                "DELETE FROM join_reconciliation WHERE report_period=? AND source_family=?",
                (TARGET_PERIOD, TARGET_FAMILY),
            )
            connection.execute(
                "DELETE FROM restatement_lineage WHERE entity_type='loan'"
            )
            connection.execute(
                "UPDATE source_manifest SET build_fingerprint=?",
                (new_fingerprint,),
            )


def archive_superseded_release(previous: Path, active: Path) -> Path:
    if previous.resolve() == active.resolve() or not previous.is_dir():
        raise RepairError("superseded release archive target is invalid")
    destination = storage.data_root() / "rollback" / f"superseded-{previous.name}"
    if destination.exists():
        raise RepairError("superseded release rollback destination already exists")
    previous.replace(destination)
    return destination


def repair(release_id: str) -> dict:
    root = storage.data_root()
    previous = storage.current_root()
    if previous.name != "m5-4-v2-20260824":
        raise RepairError("join repair requires the verified initial M5.4 release")
    free_bytes = shutil.disk_usage(root).free
    required = (
        storage.MIN_FREE_BYTES
        + (previous / "m4.sqlite").stat().st_size
        + 2 * (previous / "m5.sqlite").stat().st_size
    )
    if free_bytes < required:
        raise RepairError(
            f"insufficient join-repair headroom: free={free_bytes} required={required}"
        )

    run_root = root / "build" / release_id
    bundle = run_root / "release"
    issuance, m4_database, m5_database, partitions = prepare_bundle(
        previous, bundle
    )
    security_contract = Path("contracts/m4-source-contract.json")
    loan_contract = Path("contracts/m4-loan-source-contract.json")
    catalog = Path("contracts/m5-metric-catalog.json")
    inventory_cache = storage.manifest_path("source-inventory.json")

    prepare_m4_repair(
        m4_database, partitions, security_contract, loan_contract
    )
    repaired_m4 = m4_conformance.build(
        storage.raw_path(), m4_database, security_contract, loan_contract,
        inventory_cache, partitions, incremental=True,
        only_sources={TARGET_SOURCE},
    )
    repeat_m4 = m4_conformance.build(
        storage.raw_path(), m4_database, security_contract, loan_contract,
        inventory_cache, partitions, incremental=True,
        only_sources={TARGET_SOURCE},
    )
    if repaired_m4 != repeat_m4:
        raise RepairError("repaired M4 incremental snapshot is not idempotent")
    verified_m4 = m4_conformance.verify_release(
        storage.raw_path(), m4_database, security_contract, loan_contract,
        inventory_cache, partitions,
    )
    if verified_m4["joins"]["matched"] != TARGET_ROWS + 251_823_050:
        raise RepairError("repaired M4 matched population is incomplete")

    full_m5 = m5_metric_engine.build(
        m4_database, partitions, issuance, m5_database, catalog,
        security_contract, loan_contract,
    )
    repeat_m5 = m5_metric_engine.build(
        m4_database, partitions, issuance, m5_database, catalog,
        security_contract, loan_contract, incremental=True,
    )
    if full_m5 != repeat_m5:
        raise RepairError("repaired M5 full/incremental snapshots differ")
    verify_m5_metrics.verify(m5_database, m4_database, catalog)

    for database in (m4_database, m5_database, issuance):
        m5_4_release.finalize_sqlite_database(database)
    promotion = storage.promote_release(bundle, release_id)
    active = storage.current_root()
    m4_conformance.verify_release(
        storage.raw_path(), active / "m4.sqlite", security_contract,
        loan_contract, inventory_cache, active / "loan",
    )
    verify_m5_metrics.verify(active / "m5.sqlite", active / "m4.sqlite", catalog)
    rollback = archive_superseded_release(previous, active)
    try:
        run_root.rmdir()
    except OSError:
        pass
    stable_bytes = storage.tree_bytes(root / "raw") + storage.tree_bytes(active)
    ceiling = m5_4_release.write_ceiling(stable_bytes, release_id)
    return {
        "status": "pass",
        "release": promotion,
        "m4": verified_m4,
        "m5": full_m5,
        "stable_bytes": stable_bytes,
        "ceiling_bytes": ceiling,
        "rollback_path": str(rollback),
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--release-id", default="m5-4-v2-20260825")
    args = parser.parse_args()
    try:
        result = repair(args.release_id)
    except (
        RepairError,
        m5_4_release.ReleaseError,
        storage.StorageError,
        m4_conformance.ConformanceError,
        m5_metric_engine.MetricError,
        verify_m5_metrics.VerificationError,
        OSError,
        sqlite3.Error,
    ) as error:
        print(f"M5.4 join repair failed: {error}", file=sys.stderr)
        return 2
    print(
        "M5.4 join repair: PASS | "
        f"release={result['release']['release_id']} "
        f"stable={result['stable_bytes']} ceiling={result['ceiling_bytes']}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
