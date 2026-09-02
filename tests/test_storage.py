import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import storage  # noqa: E402


class StorageTests(unittest.TestCase):
    def test_data_root_rejects_repository_storage(self):
        with mock.patch.dict(os.environ, {"MBS_DATA_ROOT": str(storage.REPOSITORY)}):
            with self.assertRaisesRegex(storage.StorageError, "outside"):
                storage.data_root()

    def test_full_build_requires_isolated_path(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            with mock.patch.dict(os.environ, {"MBS_DATA_ROOT": str(root)}):
                storage.require_isolated_build(root / "build/run-1/m4.sqlite")
                with self.assertRaisesRegex(storage.StorageError, "full builds"):
                    storage.require_isolated_build(root / "current/m4.sqlite")

    def test_complete_bundle_promotes_through_one_atomic_pointer(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            bundle = root / "build/run-2/release"
            (bundle / "loan").mkdir(parents=True)
            for name in ("issuance.sqlite", "m4.sqlite", "m5.sqlite"):
                (bundle / name).write_bytes(name.encode())
            (bundle / "loan/partition.csv.gz").write_bytes(b"partition")
            with mock.patch.dict(os.environ, {"MBS_DATA_ROOT": str(root)}):
                self.assertEqual(storage.current_root(), root.resolve() / "current")
                promoted = storage.promote_release(bundle, "release-v2")
                self.assertEqual(promoted["release_id"], "release-v2")
                self.assertEqual(
                    storage.current_root(), root.resolve() / "releases/release-v2"
                )
                self.assertTrue(storage.current_path("m4.sqlite").is_file())
                pointer = json.loads(
                    (root / "manifests/active-release.json").read_text()
                )
                self.assertEqual(pointer, {"release_id": "release-v2"})

    def test_active_destination_follows_a_replacement_release(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            destination = root / "releases/release-v3/m4.sqlite"
            destination.parent.mkdir(parents=True)
            destination.write_bytes(b"m4")
            (root / "manifests").mkdir()
            (root / "manifests/active-release.json").write_text(
                json.dumps({"release_id": "release-v3"})
            )
            item = {
                "artifact_class": "active-m4-release",
                "destination_path": "MBS_DATA_ROOT/releases/release-v2/m4.sqlite",
            }
            with mock.patch.dict(os.environ, {"MBS_DATA_ROOT": str(root)}):
                self.assertEqual(storage.active_destination(item), destination.resolve())
                self.assertEqual(
                    item["destination_path"],
                    "MBS_DATA_ROOT/releases/release-v3/m4.sqlite",
                )

    def test_small_migration_finalizes_with_one_release_and_no_residue(self):
        with tempfile.TemporaryDirectory() as folder:
            base = Path(folder)
            repository = base / "product"
            root = base / "restricted"
            raw = repository / "data/raw"
            local = repository / "local/m4-conformed/FactLoanPeriod/2026-01"
            raw.mkdir(parents=True)
            local.mkdir(parents=True)
            (raw / "source.zip").write_bytes(b"canonical")
            (repository / "local/mbs.sqlite").write_bytes(b"issuance")
            (repository / "local/m4-conformed.sqlite").write_bytes(b"m4")
            (repository / "local/m5-metrics.sqlite").write_bytes(b"m5")
            (repository / "local/m4-inventory-cache.json").write_text("{}")
            (local / "partition.csv.gz").write_bytes(b"partition")
            with (
                mock.patch.object(storage, "REPOSITORY", repository),
                mock.patch.dict(os.environ, {"MBS_DATA_ROOT": str(root)}),
            ):
                result = storage.migrate(None)
                self.assertEqual(result["migrated"], 6)
                ledger = json.loads((root / "manifests/recovery-ledger.json").read_text())
                self.assertTrue(all(item["sha256"] for item in ledger["items"]))
                (root / "releases").mkdir()
                (root / "current").replace(root / "releases/release-v2")
                (root / "manifests/active-release.json").write_text(
                    json.dumps({"release_id": "release-v2"})
                )
                storage.record_verified_release("m4", "m5")
                ledger = json.loads((root / "manifests/recovery-ledger.json").read_text())
                active_destinations = [
                    item["destination_path"]
                    for item in ledger["items"]
                    if item["artifact_class"].startswith("active-")
                ]
                self.assertTrue(
                    all(
                        destination.startswith("MBS_DATA_ROOT/releases/release-v2/")
                        or destination == "MBS_DATA_ROOT/manifests/source-inventory.json"
                        for destination in active_destinations
                    )
                )
                cleaned = storage.cleanup(None)
                self.assertEqual(cleaned["removed_files"], 6)
                finalized = storage.finalize_ledger(None)
                self.assertEqual(finalized["checksum_mismatches"], 0)
                report = storage.final_preflight(None)
                self.assertEqual(report["active_releases"], 1)
                self.assertEqual(report["temporary_files"], 0)
                with mock.patch.object(
                    storage.shutil, "disk_usage", return_value=mock.Mock(free=0)
                ):
                    closure = storage.final_preflight(
                        None, require_build_headroom=False
                    )
                    self.assertFalse(closure["headroom_pass"])
                    with self.assertRaisesRegex(
                        storage.StorageError, "insufficient build headroom"
                    ):
                        storage.final_preflight(None)


if __name__ == "__main__":
    unittest.main()
