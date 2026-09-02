from __future__ import annotations

import tempfile
import unittest
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from unittest.mock import patch

from scripts.investigation_store import InvestigationStore


def case() -> dict[str, object]:
    return {
        "title": "Review servicer concentration",
        "owner": "disclosure-ops",
        "priority": "high",
        "status": "open",
        "summary": "Top-ten share needs composition review.",
        "release_id": "m5-test",
        "report_period": "2026-08",
        "correction_view": "latest",
        "metric_version": "m5.2.0",
        "filter_context": {"entity": "servicer"},
        "evidence": [
            {
                "contract_id": "servicer_concentration",
                "component": "servicer_top_10_upb",
                "period": "2026-08",
                "correction_view": "latest",
                "provenance": "snapshot:abc",
            }
        ],
    }


class InvestigationStoreTests(unittest.TestCase):
    def test_concurrent_delete_journal_initialization_serializes(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = InvestigationStore(Path(directory) / "investigations.sqlite")
            with patch.dict("os.environ", {"MBS_SQLITE_JOURNAL_MODE": "DELETE"}):
                with ThreadPoolExecutor(max_workers=4) as pool:
                    list(pool.map(lambda _: store.initialize(), range(4)))
            self.assertEqual(store.list(), [])

    def test_backup_mirror_restores_state_on_startup(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database, backup = root / "runtime" / "investigations.sqlite", root / "durable" / "backup.sqlite"
            with patch.dict("os.environ", {"MBS_INVESTIGATION_BACKUP": str(backup)}):
                store = InvestigationStore(database)
                store.initialize()
                created = store.create(case(), "analyst-a")
                self.assertTrue(backup.is_file())
                database.unlink()
                restored = InvestigationStore(database)
                restored.initialize()
                self.assertEqual(restored.list()[0]["id"], created["id"])

    def test_create_update_and_audit_preserve_evidence(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = InvestigationStore(Path(directory) / "investigations.sqlite")
            store.initialize()
            created = store.create(case(), "analyst-a")
            self.assertTrue(created["id"].startswith("INV-"))
            self.assertEqual(store.list()[0]["evidence"], created["evidence"])
            resolved = store.update(
                created["id"],
                {"status": "resolved", "resolution": "Composition reviewed and documented."},
                "analyst-b",
            )
            self.assertEqual(resolved["status"], "resolved")
            self.assertEqual(len(store.audit(created["id"])), 2)

    def test_rejects_immutable_changes_and_unresolved_resolution(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = InvestigationStore(Path(directory) / "investigations.sqlite")
            store.initialize()
            created = store.create(case(), "analyst-a")
            with self.assertRaisesRegex(ValueError, "immutable"):
                store.update(created["id"], {"release_id": "different"}, "analyst-a")
            with self.assertRaisesRegex(ValueError, "require a resolution"):
                store.update(created["id"], {"status": "resolved"}, "analyst-a")

    def test_requires_complete_evidence_pointer(self) -> None:
        payload = case()
        payload["evidence"] = [{"component": "loan_upb"}]
        with tempfile.TemporaryDirectory() as directory:
            store = InvestigationStore(Path(directory) / "investigations.sqlite")
            store.initialize()
            with self.assertRaisesRegex(ValueError, "every evidence"):
                store.create(payload, "analyst-a")

    def test_api_audit_records_outcome_without_headers_or_body(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            store = InvestigationStore(Path(directory) / "investigations.sqlite")
            store.initialize()
            store.record_api_request("GET", "/v1/dashboard", 401, "", False, 1.25)
            store.record_api_request("GET", "/v1/dashboard", 200, "ops", True, 2.5)
            rows = store.list_api_audit()
            self.assertEqual(len(rows), 2)
            self.assertEqual({row["authorized"] for row in rows}, {0, 1})
            self.assertNotIn("authorization", rows[0])
            self.assertNotIn("body", rows[0])
            with self.assertRaisesRegex(ValueError, "between"):
                store.list_api_audit(1001)


if __name__ == "__main__":
    unittest.main()
