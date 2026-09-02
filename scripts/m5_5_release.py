#!/usr/bin/env python3
"""Rebuild M5 metadata and atomically promote an immutable M5.5 bundle."""

from __future__ import annotations

import argparse
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path

import m4_conformance
import m5_4_release
import m5_metric_engine
import storage
import verify_m5_metrics


class ReleaseError(RuntimeError):
    """Fail-closed M5.5 release error."""


def clone_active_bundle(active: Path, bundle: Path) -> None:
    if bundle.exists():
        raise ReleaseError("isolated release bundle already exists")
    shutil.copytree(active, bundle, copy_function=os.link)


def archive_previous_release(previous_id: str, release_id: str) -> Path:
    root = storage.data_root()
    previous = root / "releases" / previous_id
    active = storage.current_root()
    if previous.resolve() == active.resolve() or not previous.is_dir():
        raise ReleaseError("previous release is not an inactive immutable bundle")
    destination = root / "rollback" / f"superseded-{previous_id}-before-{release_id}"
    if destination.exists():
        raise ReleaseError("rollback destination already exists")
    destination.parent.mkdir(parents=True, exist_ok=True)
    previous.replace(destination)
    return destination


def build_release(release_id: str, ops_root: Path | None) -> dict:
    root = storage.data_root()
    previous_id = storage.active_release_id()
    if previous_id is None:
        raise ReleaseError("M5.5 requires an immutable active release")
    active = storage.current_root()
    required = storage.tree_bytes(active) + storage.MIN_FREE_BYTES
    free = shutil.disk_usage(root).free
    if free < required:
        raise ReleaseError(f"insufficient build headroom: free={free} required={required}")

    run_root = root / "build" / release_id
    bundle = run_root / "release"
    clone_active_bundle(active, bundle)
    catalog = Path("contracts/m5-metric-catalog.json")
    security_contract = Path("contracts/m4-source-contract.json")
    loan_contract = Path("contracts/m4-loan-source-contract.json")
    inventory = storage.manifest_path("source-inventory.json")

    m4_summary = m4_conformance.verify_release(
        storage.raw_path(), bundle / "m4.sqlite", security_contract,
        loan_contract, inventory, bundle / "loan",
    )
    m5_summary = m5_metric_engine.build(
        bundle / "m4.sqlite", bundle / "loan", bundle / "issuance.sqlite",
        bundle / "m5.sqlite", catalog, security_contract, loan_contract,
        incremental=True,
    )
    repeated = m5_metric_engine.build(
        bundle / "m4.sqlite", bundle / "loan", bundle / "issuance.sqlite",
        bundle / "m5.sqlite", catalog, security_contract, loan_contract,
        incremental=True,
    )
    if m5_summary != repeated:
        raise ReleaseError("M5 full-change and repeated incremental snapshots differ")
    verify_m5_metrics.verify(bundle / "m5.sqlite", bundle / "m4.sqlite", catalog)
    m5_4_release.finalize_sqlite_database(bundle / "m5.sqlite")

    promotion = storage.promote_release(bundle, release_id)
    current = storage.current_root()
    m4_conformance.verify_release(
        storage.raw_path(), current / "m4.sqlite", security_contract,
        loan_contract, inventory, current / "loan",
    )
    verify_m5_metrics.verify(current / "m5.sqlite", current / "m4.sqlite", catalog)
    rollback = archive_previous_release(previous_id, release_id)
    storage.record_verified_release(
        m4_summary["snapshot_sha256"], m5_summary["snapshot_sha256"]
    )
    storage.finalize_ledger(ops_root)
    try:
        run_root.rmdir()
    except OSError:
        pass
    stable = storage.tree_bytes(root / "raw") + storage.tree_bytes(current)
    ceiling = m5_4_release.write_ceiling(stable, release_id)
    return {
        "status": "pass",
        "release": promotion,
        "previous_release": previous_id,
        "rollback_path": str(rollback),
        "rollback_bytes": storage.tree_bytes(rollback),
        "m4": m4_summary,
        "m5": m5_summary,
        "stable_bytes": stable,
        "ceiling_bytes": ceiling,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--release-id",
        default=datetime.now(UTC).strftime("m5-5-methodology-%Y%m%dT%H%M%SZ"),
    )
    parser.add_argument("--ops-root", type=Path)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        result = build_release(args.release_id, args.ops_root)
    except (
        ReleaseError, storage.StorageError, m4_conformance.ConformanceError,
        m5_metric_engine.MetricError, verify_m5_metrics.VerificationError,
        OSError,
    ) as error:
        print(f"M5.5 release failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True) if args.json else (
        f"M5.5 release: PASS | release={result['release']['release_id']} "
        f"stable={result['stable_bytes']}"
    ))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
