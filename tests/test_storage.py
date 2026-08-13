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
                storage.record_verified_release("m4", "m5")
                cleaned = storage.cleanup(None)
                self.assertEqual(cleaned["removed_files"], 6)
                finalized = storage.finalize_ledger(None)
                self.assertEqual(finalized["checksum_mismatches"], 0)
                report = storage.final_preflight(None)
                self.assertEqual(report["active_releases"], 1)
                self.assertEqual(report["temporary_files"], 0)


if __name__ == "__main__":
    unittest.main()
