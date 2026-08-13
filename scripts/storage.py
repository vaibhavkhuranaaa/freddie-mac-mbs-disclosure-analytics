#!/usr/bin/env python3
"""Resolve restricted storage, migrate it safely, and enforce storage gates."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import sys
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

REPOSITORY = Path(__file__).resolve().parents[1]
DEFAULT_DATA_ROOT = REPOSITORY.parent / f"{REPOSITORY.name}-data"
MIN_FREE_BYTES = 10 * 1024**3
STABLE_TARGET_BYTES = 34 * 1024**3
LEDGER_NAME = "recovery-ledger.json"


class StorageError(RuntimeError):
    """Raised when restricted storage violates a safety gate."""


def data_root() -> Path:
    configured = os.environ.get("MBS_DATA_ROOT")
    root = Path(configured).expanduser() if configured else DEFAULT_DATA_ROOT
    if not root.is_absolute():
        raise StorageError("MBS_DATA_ROOT must be an absolute path")
    root = root.resolve()
    repository = REPOSITORY.resolve()
    if root == repository or repository in root.parents or root in repository.parents:
        raise StorageError("MBS_DATA_ROOT must be outside the product repository")
    return root


def raw_path() -> Path:
    return data_root() / "raw"


def current_path(name: str) -> Path:
    return data_root() / "current" / name


def manifest_path(name: str) -> Path:
    return data_root() / "manifests" / name


def require_isolated_build(path: Path) -> None:
    resolved = path.resolve()
    build_root = (data_root() / "build").resolve()
    if resolved == build_root or build_root not in resolved.parents:
        raise StorageError("full builds must use MBS_DATA_ROOT/build/<run-id>")


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def files_under(path: Path) -> Iterable[Path]:
    if path.is_file():
        yield path
    elif path.is_dir():
        yield from sorted(item for item in path.rglob("*") if item.is_file())


def tree_bytes(path: Path) -> int:
    return sum(item.stat().st_size for item in files_under(path))


def release_mappings() -> list[tuple[Path, Path, str, str, list[str]]]:
    root = data_root()
    mappings = [
        (
            REPOSITORY / "local/mbs.sqlite",
            root / "current/issuance.sqlite",
            "active-issuance-release",
            "scripts/pipeline.py",
            ["scripts/m5_metric_engine.py"],
        ),
        (
            REPOSITORY / "local/m4-conformed.sqlite",
            root / "current/m4.sqlite",
            "active-m4-release",
            "scripts/m4_conformance.py",
            ["scripts/m4_conformance.py", "scripts/m5_metric_engine.py", "scripts/verify_m5_metrics.py"],
        ),
        (
            REPOSITORY / "local/m5-metrics.sqlite",
            root / "current/m5.sqlite",
            "active-m5-release",
            "scripts/m5_metric_engine.py",
            ["scripts/m5_metric_engine.py", "scripts/verify_m5_metrics.py"],
        ),
        (
            REPOSITORY / "local/m4-inventory-cache.json",
            root / "manifests/source-inventory.json",
            "active-source-manifest",
            "scripts/source_inventory.py",
            ["scripts/source_inventory.py", "scripts/m4_conformance.py"],
        ),
    ]
    partition_root = REPOSITORY / "local/m4-conformed"
    for source in files_under(partition_root):
        mappings.append(
            (
                source,
                root / "current/loan" / source.relative_to(partition_root),
                "active-m4-loan-partition",
                "scripts/m4_conformance.py",
                ["scripts/m4_conformance.py", "scripts/m5_metric_engine.py"],
            )
        )
    return mappings


def raw_mappings() -> list[tuple[Path, Path, str, str, list[str]]]:
    source_root = REPOSITORY / "data/raw"
    return [
        (
            source,
            raw_path() / source.name,
            "canonical-raw-archive",
            "official Freddie Mac acquisition",
            ["scripts/pipeline.py", "scripts/source_inventory.py", "scripts/m4_conformance.py"],
        )
        for source in files_under(source_root)
        if source.name != ".gitkeep"
    ]


def cleanup_roots(ops_root: Path | None) -> list[Path]:
    roots = [
        REPOSITORY / "graphify-out",
        REPOSITORY / ".cursor",
        REPOSITORY / "data/sample",
    ]
    roots.extend(sorted(REPOSITORY.rglob("__pycache__")))
    roots.extend(
        REPOSITORY / relative
        for relative in (
            "scripts/project_kit.py",
            "docs/PROJECT_CONTEXT.md",
            "docs/takeover-prompt.md",
            "docs/continuation-guide.md",
            "docs/NEXT_CHAT_PROMPT.md",
            ".project",
        )
    )
    mapped = {source.resolve() for source, *_ in release_mappings()}
    roots.extend(
        path for path in files_under(REPOSITORY / "local") if path.resolve() not in mapped
    )
    if ops_root is not None:
        roots.append(ops_root / "legacy")
    return roots


def display_path(path: Path, ops_root: Path | None = None) -> str:
    if path.is_relative_to(REPOSITORY):
        return f"repository/{path.relative_to(REPOSITORY)}"
    if ops_root is not None and path.is_relative_to(ops_root):
        return f"ops/{path.relative_to(ops_root)}"
    if path.is_relative_to(data_root()):
        return f"MBS_DATA_ROOT/{path.relative_to(data_root())}"
    return str(path)


def cleanup_metadata(path: Path, ops_root: Path | None) -> tuple[str, str, list[str], str]:
    relative = display_path(path, ops_root)
    if "/legacy/" in relative:
        return (
            "migrated-legacy-record",
            "legacy project workspace",
            ["private project-kit records"],
            "current private approvals, evidence, contracts, decisions, and handoff",
        )
    if "graphify-out" in relative:
        return (
            "reproducible-graph-output",
            "project-kit graph sync",
            ["diagnostic review only"],
            "project-kit graph sync from tracked source",
        )
    if "__pycache__" in relative or path.suffix in {".pyc", ".pyo"}:
        return ("python-bytecode", "Python runtime", [], "rerun Python command")
    if ".cursor" in relative:
        return ("stale-assistant-config", "local editor", [], "no recovery required")
    if "sample" in relative:
        return (
            "reproducible-sample-output",
            "sample pipeline",
            ["local test only"],
            "tests/fixtures plus scripts/pipeline.py",
        )
    if path.name == "project_kit.py":
        return ("copied-tool", "legacy project kit", [], "installed project-delivery kit")
    if "prompt" in path.name.lower() or "continuation" in path.name.lower():
        return ("stale-prompt", "legacy delivery workflow", [], "current private handoff")
    return ("reproducible-cache", "local workflow", [], "rerun documented producer")


def ledger_item(
    source: Path,
    destination: Path | None,
    artifact_class: str,
    producer: str,
    consumers: list[str],
    ops_root: Path | None,
) -> dict[str, Any]:
    retention = (
        "seven years from acquisition or earlier authorization end"
        if artifact_class == "canonical-raw-archive"
        else "retain one active release until verified replacement"
        if artifact_class.startswith("active-")
        else "delete after recovery and acceptance checks"
    )
    recovery_source = (
        "official provider archive plus this checksum ledger"
        if artifact_class == "canonical-raw-archive"
        else "canonical raw archives, public contracts, and tracked producers"
        if artifact_class.startswith("active-")
        else cleanup_metadata(source, ops_root)[3]
    )
    return {
        "artifact_class": artifact_class,
        "source_path": display_path(source, ops_root),
        "destination_path": display_path(destination, ops_root) if destination else None,
        "size_bytes": source.stat().st_size,
        "sha256": sha256_file(source),
        "producer": producer,
        "consumers": consumers,
        "retention": retention,
        "recovery_source": recovery_source,
        "cleanup_action": (
            "remove repository copy after destination checksum parity and M4/M5 verification"
            if destination
            else "remove after recovery facts are confirmed"
        ),
        "state": "pending-migration" if destination else "pending-cleanup",
    }


def required_copy_bytes(mappings: list[tuple[Path, Path, str, str, list[str]]]) -> int:
    total = 0
    for source, destination, *_ in mappings:
        if not source.is_file():
            raise StorageError(f"required migration source is missing: {source}")
        if destination.exists():
            if destination.stat().st_size != source.stat().st_size:
                raise StorageError(f"destination exists with a different size: {destination}")
        else:
            total += source.stat().st_size
    return total


def migration_preflight() -> dict[str, Any]:
    root = data_root()
    mappings = raw_mappings() + release_mappings()
    if not raw_mappings():
        raise StorageError("repository canonical raw archive set is empty")
    missing_bytes = required_copy_bytes(mappings)
    probe = root if root.exists() else root.parent
    free_bytes = shutil.disk_usage(probe).free
    required_free = missing_bytes + MIN_FREE_BYTES
    if free_bytes < required_free:
        raise StorageError(
            f"insufficient migration headroom: free={free_bytes} required={required_free}"
        )
    return {
        "status": "pass",
        "data_root": str(root),
        "files": len(mappings),
        "copy_bytes": missing_bytes,
        "free_bytes": free_bytes,
        "required_free_bytes": required_free,
    }


def copy_with_parity(source: Path, destination: Path, expected_sha256: str) -> None:
    destination.parent.mkdir(parents=True, exist_ok=True)
    if destination.exists():
        if destination.stat().st_size != source.stat().st_size:
            raise StorageError(f"refusing to overwrite different destination: {destination}")
        if sha256_file(destination) != expected_sha256:
            raise StorageError(f"destination checksum differs: {destination}")
        return
    temporary = destination.with_name(destination.name + ".migrating")
    temporary.unlink(missing_ok=True)
    shutil.copy2(source, temporary)
    if temporary.stat().st_size != source.stat().st_size or sha256_file(temporary) != expected_sha256:
        temporary.unlink(missing_ok=True)
        raise StorageError(f"destination checksum parity failed: {destination}")
    temporary.replace(destination)


def migrate(ops_root: Path | None) -> dict[str, Any]:
    preflight = migration_preflight()
    root = data_root()
    for relative in ("raw", "current/loan", "build", "manifests"):
        (root / relative).mkdir(parents=True, exist_ok=True)
    items: list[dict[str, Any]] = []
    mappings = raw_mappings() + release_mappings()
    for index, (source, destination, artifact_class, producer, consumers) in enumerate(
        mappings, start=1
    ):
        item = ledger_item(
            source, destination, artifact_class, producer, consumers, ops_root
        )
        copy_with_parity(source, destination, item["sha256"])
        item["state"] = "parity-verified"
        items.append(item)
        print(f"Storage migration {index}/{len(mappings)}: {artifact_class}", flush=True)
    seen_cleanup: set[Path] = set()
    for root_or_file in cleanup_roots(ops_root):
        for source in files_under(root_or_file):
            resolved = source.resolve()
            if resolved in seen_cleanup:
                continue
            seen_cleanup.add(resolved)
            artifact_class, producer, consumers, _ = cleanup_metadata(source, ops_root)
            items.append(
                ledger_item(
                    source, None, artifact_class, producer, consumers, ops_root
                )
            )
    ledger = {
        "version": 1,
        "created_at": datetime.now(UTC).isoformat(),
        "data_root_environment": "MBS_DATA_ROOT",
        "default_data_root": str(DEFAULT_DATA_ROOT),
        "policies": {
            "canonical_raw_copies": 1,
            "active_releases": 1,
            "minimum_free_bytes": MIN_FREE_BYTES,
            "stable_target_bytes": STABLE_TARGET_BYTES,
            "temporary_residue": 0,
        },
        "migration_preflight": preflight,
        "items": sorted(items, key=lambda item: item["source_path"]),
    }
    path = manifest_path(LEDGER_NAME)
    path.write_text(json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8")
    return {
        "status": "pass",
        "ledger": str(path),
        "items": len(items),
        "migrated": len(mappings),
    }


def load_ledger() -> dict[str, Any]:
    path = manifest_path(LEDGER_NAME)
    if not path.is_file():
        raise StorageError(f"recovery ledger is missing: {path}")
    return json.loads(path.read_text(encoding="utf-8"))


def source_from_display(value: str, ops_root: Path | None) -> Path:
    if value.startswith("repository/"):
        return REPOSITORY / value.removeprefix("repository/")
    if value.startswith("ops/"):
        if ops_root is None:
            raise StorageError("ops root is required to verify legacy cleanup")
        return ops_root / value.removeprefix("ops/")
    if value.startswith("MBS_DATA_ROOT/"):
        return data_root() / value.removeprefix("MBS_DATA_ROOT/")
    return Path(value)


def finalize_ledger(ops_root: Path | None) -> dict[str, Any]:
    ledger = load_ledger()
    for item in ledger["items"]:
        source = source_from_display(item["source_path"], ops_root)
        destination_value = item.get("destination_path")
        if source.exists():
            raise StorageError(f"cleanup target remains: {item['source_path']}")
        if destination_value:
            destination = source_from_display(destination_value, ops_root)
            if not destination.is_file():
                raise StorageError(f"migrated artifact is missing: {destination_value}")
            expected_size = item.get("verified_size_bytes", item["size_bytes"])
            expected_sha256 = item.get("verified_sha256", item["sha256"])
            if destination.stat().st_size != expected_size:
                raise StorageError(f"migrated artifact size changed: {destination_value}")
            if sha256_file(destination) != expected_sha256:
                raise StorageError(f"migrated artifact checksum changed: {destination_value}")
            item["state"] = "retained-destination-source-removed"
        else:
            item["state"] = "removed-recoverable-or-valueless"
    ledger["finalized_at"] = datetime.now(UTC).isoformat()
    ledger["summary"] = {
        "items": len(ledger["items"]),
        "canonical_raw": sum(
            item["artifact_class"] == "canonical-raw-archive" for item in ledger["items"]
        ),
        "active_release_files": sum(
            item["artifact_class"].startswith("active-") for item in ledger["items"]
        ),
        "removed_items": sum(item["destination_path"] is None for item in ledger["items"]),
        "checksum_mismatches": 0,
    }
    manifest_path(LEDGER_NAME).write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"status": "pass", **ledger["summary"]}


def record_verified_release(m4_snapshot: str, m5_snapshot: str) -> dict[str, Any]:
    ledger = load_ledger()
    updated = 0
    for item in ledger["items"]:
        if not item["artifact_class"].startswith("active-"):
            continue
        destination = source_from_display(item["destination_path"], None)
        if not destination.is_file():
            raise StorageError(f"verified active artifact is missing: {item['destination_path']}")
        item["verified_size_bytes"] = destination.stat().st_size
        item["verified_sha256"] = sha256_file(destination)
        item["state"] = "release-verified"
        updated += 1
    ledger["release_verification"] = {
        "verified_at": datetime.now(UTC).isoformat(),
        "m4_snapshot_sha256": m4_snapshot,
        "m5_snapshot_sha256": m5_snapshot,
        "active_files": updated,
    }
    manifest_path(LEDGER_NAME).write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"status": "pass", "active_files": updated}


def cleanup(ops_root: Path | None) -> dict[str, Any]:
    ledger = load_ledger()
    if "release_verification" not in ledger:
        raise StorageError("release verification is not recorded")
    removed = 0
    for item in ledger["items"]:
        source = source_from_display(item["source_path"], ops_root)
        if not source.exists():
            continue
        if not source.is_file():
            raise StorageError(f"ledger cleanup target is not a file: {item['source_path']}")
        if source.stat().st_size != item["size_bytes"] or sha256_file(source) != item["sha256"]:
            raise StorageError(f"cleanup target changed after inventory: {item['source_path']}")
        destination_value = item.get("destination_path")
        if destination_value:
            destination = source_from_display(destination_value, ops_root)
            expected_size = item.get("verified_size_bytes", item["size_bytes"])
            expected_sha256 = item.get("verified_sha256", item["sha256"])
            if not destination.is_file():
                raise StorageError(f"recovery destination is missing: {destination_value}")
            if destination.stat().st_size != expected_size or sha256_file(destination) != expected_sha256:
                raise StorageError(f"recovery destination changed: {destination_value}")
        source.unlink()
        removed += 1
    removable_roots = [
        REPOSITORY / "local",
        REPOSITORY / "graphify-out",
        REPOSITORY / ".cursor",
        REPOSITORY / "data/sample",
        *sorted(REPOSITORY.rglob("__pycache__")),
    ]
    if ops_root is not None:
        removable_roots.append(ops_root / "legacy")
    directories = sorted(
        {
            directory
            for root in removable_roots
            if root.exists()
            for directory in [root, *(path for path in root.rglob("*") if path.is_dir())]
        },
        key=lambda path: len(path.parts),
        reverse=True,
    )
    for directory in directories:
        if not directory.is_dir():
            continue
        try:
            directory.rmdir()
        except OSError:
            pass
    return {"status": "pass", "removed_files": removed}


def record_cleanup_candidates(ops_root: Path | None) -> dict[str, Any]:
    ledger = load_ledger()
    known = {item["source_path"]: item for item in ledger["items"]}
    added = 0
    refreshed = 0
    for root_or_file in cleanup_roots(ops_root):
        for source in files_under(root_or_file):
            source_path = display_path(source, ops_root)
            artifact_class, producer, consumers, _ = cleanup_metadata(source, ops_root)
            current = ledger_item(
                source, None, artifact_class, producer, consumers, ops_root
            )
            prior = known.get(source_path)
            if prior is None:
                ledger["items"].append(current)
                known[source_path] = current
                added += 1
            elif prior.get("destination_path") is None and (
                prior["size_bytes"] != current["size_bytes"]
                or prior["sha256"] != current["sha256"]
            ):
                prior.update(current)
                refreshed += 1
    ledger["items"].sort(key=lambda item: item["source_path"])
    manifest_path(LEDGER_NAME).write_text(
        json.dumps(ledger, indent=2, sort_keys=True) + "\n", encoding="utf-8"
    )
    return {"status": "pass", "added": added, "refreshed": refreshed}


def remaining_repository_artifacts(ops_root: Path | None) -> list[str]:
    paths: list[Path] = []
    paths.extend(
        item for item in files_under(REPOSITORY / "data/raw") if item.name != ".gitkeep"
    )
    paths.extend(files_under(REPOSITORY / "local"))
    for target in cleanup_roots(ops_root):
        paths.extend(files_under(target))
    return sorted({display_path(path, ops_root) for path in paths})


def final_preflight(ops_root: Path | None, enforce_budget: bool = False) -> dict[str, Any]:
    root = data_root()
    ledger = load_ledger()
    expected_current = {"issuance.sqlite", "m4.sqlite", "m5.sqlite", "loan"}
    actual_current = {item.name for item in (root / "current").iterdir()}
    if actual_current != expected_current:
        raise StorageError(
            f"active release layout differs: expected={sorted(expected_current)} actual={sorted(actual_current)}"
        )
    required_files = [
        root / "current/issuance.sqlite",
        root / "current/m4.sqlite",
        root / "current/m5.sqlite",
    ]
    if any(not path.is_file() for path in required_files):
        raise StorageError("active release is incomplete")
    if not any(files_under(root / "current/loan")):
        raise StorageError("active loan partition set is empty")
    temporary = list(files_under(root / "build")) + list(root.rglob("*.building")) + list(
        root.rglob("*.migrating")
    )
    if temporary:
        raise StorageError(f"temporary residue remains: {temporary[0]}")
    residue = remaining_repository_artifacts(ops_root)
    if residue:
        raise StorageError(f"repository or legacy residue remains: {residue[0]}")
    expected_raw = {
        item["destination_path"]
        for item in ledger["items"]
        if item["artifact_class"] == "canonical-raw-archive"
    }
    actual_raw = {display_path(path, ops_root) for path in files_under(root / "raw")}
    if actual_raw != expected_raw:
        raise StorageError("canonical raw inventory differs from the recovery ledger")
    stable_bytes = tree_bytes(root / "raw") + tree_bytes(root / "current")
    budget_pass = stable_bytes <= STABLE_TARGET_BYTES
    if enforce_budget and not budget_pass:
        raise StorageError(
            f"stable storage exceeds target: actual={stable_bytes} target={STABLE_TARGET_BYTES}"
        )
    free_bytes = shutil.disk_usage(root).free
    estimated_build_bytes = tree_bytes(root / "current")
    required_free = estimated_build_bytes + MIN_FREE_BYTES
    if free_bytes < required_free:
        raise StorageError(
            f"insufficient build headroom: free={free_bytes} required={required_free}"
        )
    return {
        "status": "pass",
        "data_root": str(root),
        "canonical_raw_files": len(actual_raw),
        "active_releases": 1,
        "temporary_files": 0,
        "repository_residue": 0,
        "stable_bytes": stable_bytes,
        "stable_target_bytes": STABLE_TARGET_BYTES,
        "stable_budget_pass": budget_pass,
        "free_bytes": free_bytes,
        "required_build_free_bytes": required_free,
        "headroom_pass": True,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    subparsers = parser.add_subparsers(dest="command", required=True)
    migrate_parser = subparsers.add_parser("migrate")
    migrate_parser.add_argument("--ops-root", type=Path)
    finalize_parser = subparsers.add_parser("finalize")
    finalize_parser.add_argument("--ops-root", type=Path)
    cleanup_parser = subparsers.add_parser("cleanup")
    cleanup_parser.add_argument("--ops-root", type=Path)
    cleanup_inventory_parser = subparsers.add_parser("record-cleanup")
    cleanup_inventory_parser.add_argument("--ops-root", type=Path)
    verified_parser = subparsers.add_parser("record-verified")
    verified_parser.add_argument("--m4-snapshot", required=True)
    verified_parser.add_argument("--m5-snapshot", required=True)
    preflight_parser = subparsers.add_parser("preflight")
    preflight_parser.add_argument("--phase", choices=("migration", "final"), default="final")
    preflight_parser.add_argument("--ops-root", type=Path)
    preflight_parser.add_argument("--enforce-budget", action="store_true")
    args = parser.parse_args()
    try:
        if args.command == "migrate":
            result = migrate(args.ops_root)
        elif args.command == "finalize":
            result = finalize_ledger(args.ops_root)
        elif args.command == "cleanup":
            result = cleanup(args.ops_root)
        elif args.command == "record-cleanup":
            result = record_cleanup_candidates(args.ops_root)
        elif args.command == "record-verified":
            result = record_verified_release(args.m4_snapshot, args.m5_snapshot)
        elif args.phase == "migration":
            result = migration_preflight()
        else:
            result = final_preflight(args.ops_root, args.enforce_budget)
    except (OSError, StorageError, ValueError, json.JSONDecodeError) as error:
        print(f"Storage check failed: {error}", file=sys.stderr)
        return 2
    print(json.dumps(result, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
