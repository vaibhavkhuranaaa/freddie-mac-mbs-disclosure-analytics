from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.prepare_m12_publication import build_manifest, prepare_stage, verify_local, verify_remote


class M12PublicationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.data = root / "data"
        for directory in ("raw", "releases/release-1/loan/2026-01", "manifests", "product"):
            (self.data / directory).mkdir(parents=True)
        (self.data / "raw/source.zip").write_bytes(b"source")
        (self.data / "releases/release-1/m4.sqlite").write_bytes(b"m4")
        (self.data / "releases/release-1/loan/2026-01/loan.csv.gz").write_bytes(b"loan")
        (self.data / "product/dashboard.json").write_text("{}\n")
        (self.data / "manifests/active-release.json").write_text('{"release_id":"release-1"}\n')
        (self.data / "manifests/recovery-ledger.json").write_text(
            '{"path":"/Users/private/ops","repository_metadata":["private-file"]}\n'
        )
        for name in ("source-inventory.json", "storage-ceiling.json"):
            (self.data / "manifests" / name).write_text("{}\n")
        self.card = root / "DATASET.md"
        self.card.write_text("# Dataset\n")

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_prepare_covers_exact_immutable_publication_boundary(self) -> None:
        manifest = build_manifest(self.data)
        self.assertEqual(manifest["artifact_count"], 7)
        logical_paths = {item["logical_path"] for item in manifest["artifacts"]}
        self.assertNotIn("manifests/recovery-ledger.json", logical_paths)
        self.assertNotIn("product/investigations.sqlite", logical_paths)
        verify_local(manifest, self.data)

        stage = Path(self.temporary.name) / "stage"
        prepared = prepare_stage(self.data, stage, self.card)
        first = prepared["artifacts"][0]
        self.assertEqual(
            (self.data / first["logical_path"]).stat().st_ino,
            (stage / "assets" / first["asset_name"]).stat().st_ino,
        )
        self.assertFalse((stage / "assets/manifests--recovery-ledger.json").exists())

    def test_local_and_remote_changes_fail_closed(self) -> None:
        manifest = build_manifest(self.data)
        duplicate = {**manifest, "artifacts": [*manifest["artifacts"], manifest["artifacts"][0]]}
        duplicate["artifact_count"] += 1
        duplicate["total_bytes"] += manifest["artifacts"][0]["size_bytes"]
        with self.assertRaisesRegex(ValueError, "duplicate"):
            verify_local(duplicate, self.data)

        target = self.data / manifest["artifacts"][0]["logical_path"]
        target.write_bytes(b"changed")
        with self.assertRaises(ValueError):
            verify_local(manifest, self.data)

        remote = [
            {
                "name": item["asset_name"],
                "size": item["size_bytes"],
                "digest": "sha256:" + item["sha256"],
            }
            for item in manifest["artifacts"]
        ]
        verify_remote(manifest, remote)
        remote.append(
            {
                "name": "manifests--recovery-ledger.json",
                "size": 1,
                "digest": "sha256:" + hashlib.sha256(b"private").hexdigest(),
            }
        )
        with self.assertRaisesRegex(ValueError, "exactly match"):
            verify_remote(manifest, remote)
        remote.pop()
        remote[0]["digest"] = "sha256:" + hashlib.sha256(b"wrong").hexdigest()
        with self.assertRaises(ValueError):
            verify_remote(manifest, remote)

    def test_active_release_cannot_escape_the_release_directory(self) -> None:
        (self.data / "manifests/active-release.json").write_text(
            '{"release_id":"../manifests"}\n'
        )
        with self.assertRaisesRegex(ValueError, "identifier is invalid"):
            build_manifest(self.data)


if __name__ == "__main__":
    unittest.main()
