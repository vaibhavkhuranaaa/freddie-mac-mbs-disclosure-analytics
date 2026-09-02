#!/usr/bin/env python3
"""Prepare and verify the complete M12 GitHub release payload."""

from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import urllib.request
from pathlib import Path


MAX_ASSET_BYTES = 2 * 1024**3
MAX_ASSETS = 1000
PUBLIC_MANIFESTS = (
    "active-release.json",
    "source-inventory.json",
    "storage-ceiling.json",
)

# TODO: Add resumable upload support before any future asset exceeds the current single-request boundary.


def sha256(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for chunk in iter(lambda: handle.read(8 * 1024 * 1024), b""):
            digest.update(chunk)
    return digest.hexdigest()


def encoded_manifest(manifest: dict[str, object]) -> bytes:
    return (json.dumps(manifest, indent=2, sort_keys=True) + "\n").encode()


def active_release_id(data_root: Path) -> str:
    active = json.loads((data_root / "manifests/active-release.json").read_text())
    release_id = active.get("release_id")
    if not isinstance(release_id, str) or not re.fullmatch(
        r"[a-zA-Z0-9][a-zA-Z0-9._-]{0,79}", release_id
    ):
        raise ValueError("active release identifier is invalid")
    return release_id


def selected_files(data_root: Path) -> list[Path]:
    release = data_root / "releases" / active_release_id(data_root)
    paths = [path for path in (data_root / "raw").rglob("*") if path.is_file()]
    paths.extend(path for path in release.rglob("*") if path.is_file())
    paths.extend(data_root / "manifests" / name for name in PUBLIC_MANIFESTS)
    paths.append(data_root / "product/dashboard.json")
    if any(not path.is_file() for path in paths):
        raise ValueError("publication selection contains a missing file")
    return sorted(set(paths))


def asset_name(data_root: Path, path: Path) -> str:
    return path.relative_to(data_root).as_posix().replace("/", "--")


def build_manifest(data_root: Path) -> dict[str, object]:
    release_id = active_release_id(data_root)
    artifacts = []
    names = set()
    for path in selected_files(data_root):
        name = asset_name(data_root, path)
        size = path.stat().st_size
        if name in names:
            raise ValueError(f"duplicate release asset name: {name}")
        if size >= MAX_ASSET_BYTES:
            raise ValueError(f"release asset reaches GitHub's 2 GiB limit: {path}")
        names.add(name)
        artifacts.append(
            {
                "asset_name": name,
                "logical_path": path.relative_to(data_root).as_posix(),
                "size_bytes": size,
                "sha256": sha256(path),
            }
        )
    if len(artifacts) > MAX_ASSETS:
        raise ValueError("publication exceeds GitHub's 1,000-asset release limit")
    return {
        "version": 1,
        "release_id": release_id,
        "artifact_count": len(artifacts),
        "total_bytes": sum(item["size_bytes"] for item in artifacts),
        "artifacts": artifacts,
        "exclusions": [
            "mutable investigation records",
            "SQLite WAL and shared-memory files",
            "temporary build and rollback directories",
            "private delivery records and credentials",
        ],
    }


def verify_local(manifest: dict[str, object], data_root: Path) -> None:
    artifacts = manifest["artifacts"]
    if manifest["artifact_count"] != len(artifacts):
        raise ValueError("manifest artifact count disagrees with entries")
    if manifest["total_bytes"] != sum(item["size_bytes"] for item in artifacts):
        raise ValueError("manifest byte total disagrees with entries")
    expected = {path.relative_to(data_root).as_posix() for path in selected_files(data_root)}
    recorded_paths = [item["logical_path"] for item in artifacts]
    recorded_names = [item["asset_name"] for item in artifacts]
    if len(recorded_paths) != len(set(recorded_paths)) or len(recorded_names) != len(
        set(recorded_names)
    ):
        raise ValueError("manifest contains duplicate artifacts")
    recorded = set(recorded_paths)
    if expected != recorded:
        raise ValueError("manifest does not cover the exact publication selection")
    for item in artifacts:
        path = data_root / item["logical_path"]
        if path.stat().st_size != item["size_bytes"] or sha256(path) != item["sha256"]:
            raise ValueError(f"local artifact changed: {item['logical_path']}")


def prepare_stage(data_root: Path, output: Path, card: Path) -> dict[str, object]:
    if output.exists():
        raise ValueError(f"stage already exists: {output}")
    manifest = build_manifest(data_root)
    assets = output / "assets"
    assets.mkdir(parents=True)
    for item in manifest["artifacts"]:
        os.link(data_root / item["logical_path"], assets / item["asset_name"])
    (output / "publication-manifest.json").write_bytes(encoded_manifest(manifest))
    (output / "DATASET.md").write_text(card.read_text(encoding="utf-8"), encoding="utf-8")
    return manifest


def github_assets(repository: str, tag: str) -> list[dict[str, object]]:
    request = urllib.request.Request(
        f"https://api.github.com/repos/{repository}/releases/tags/{tag}",
        headers={"Accept": "application/vnd.github+json", "User-Agent": "m12-verifier"},
    )
    with urllib.request.urlopen(request) as response:
        release = json.load(response)
    assets = []
    page = 1
    while True:
        request = urllib.request.Request(
            f"https://api.github.com/repos/{repository}/releases/{release['id']}/assets?per_page=100&page={page}",
            headers={"Accept": "application/vnd.github+json", "User-Agent": "m12-verifier"},
        )
        with urllib.request.urlopen(request) as response:
            batch = json.load(response)
        assets.extend(batch)
        if len(batch) < 100:
            return assets
        page += 1


def verify_remote(manifest: dict[str, object], assets: list[dict[str, object]]) -> None:
    manifest_payload = encoded_manifest(manifest)
    expected = [
        *manifest["artifacts"],
        {
            "asset_name": "publication-manifest.json",
            "size_bytes": len(manifest_payload),
            "sha256": hashlib.sha256(manifest_payload).hexdigest(),
        },
    ]
    expected_names = [item["asset_name"] for item in expected]
    remote_names = [item["name"] for item in assets]
    if len(expected_names) != len(set(expected_names)):
        raise ValueError("manifest contains duplicate asset names")
    if len(remote_names) != len(set(remote_names)):
        raise ValueError("remote release contains duplicate asset names")
    if set(remote_names) != set(expected_names):
        raise ValueError("remote assets do not exactly match the publication manifest")
    remote = {item["name"]: item for item in assets}
    for item in expected:
        found = remote.get(item["asset_name"])
        if found is None:
            raise ValueError(f"remote asset missing: {item['asset_name']}")
        if found["size"] != item["size_bytes"]:
            raise ValueError(f"remote asset size mismatch: {item['asset_name']}")
        if found.get("digest") != f"sha256:{item['sha256']}":
            raise ValueError(f"remote asset digest mismatch: {item['asset_name']}")


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--data-root",
        type=Path,
        default=Path(os.environ.get("MBS_DATA_ROOT", Path(__file__).resolve().parents[2] / "freddie-mac-mbs-disclosure-analytics-data")),
    )
    subparsers = parser.add_subparsers(dest="command", required=True)
    prepare = subparsers.add_parser("prepare")
    prepare.add_argument("--output", type=Path, required=True)
    prepare.add_argument("--card", type=Path, default=Path(__file__).resolve().parents[1] / "DATASET.md")
    verify = subparsers.add_parser("verify-local")
    verify.add_argument("--manifest", type=Path, required=True)
    remote = subparsers.add_parser("verify-remote")
    remote.add_argument("--manifest", type=Path, required=True)
    remote.add_argument("--repository", required=True)
    remote.add_argument("--tag", default="data-v1")
    args = parser.parse_args()

    data_root = args.data_root.expanduser().resolve()
    if args.command == "prepare":
        manifest = prepare_stage(data_root, args.output.expanduser().resolve(), args.card)
    else:
        manifest = json.loads(args.manifest.read_text(encoding="utf-8"))
        if args.command == "verify-local":
            verify_local(manifest, data_root)
        else:
            verify_remote(manifest, github_assets(args.repository, args.tag))
    print(json.dumps({"artifact_count": manifest["artifact_count"], "total_bytes": manifest["total_bytes"]}))


if __name__ == "__main__":
    main()
