from __future__ import annotations

import tempfile
import unittest
from pathlib import Path

from scripts.investigation_backup import copy_database
from scripts.investigation_store import InvestigationStore


class InvestigationBackupTests(unittest.TestCase):
    def test_backup_and_restore_preserve_consistent_state(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            database, backup = root / "investigations.sqlite", root / "backup.sqlite"
            store = InvestigationStore(database)
            store.initialize()
            first = store.create(self._record("first"), "tester")
            result = copy_database(database, backup)
            self.assertEqual(result["integrity"], "ok")
            store.create(self._record("second"), "tester")
            copy_database(backup, database)
            self.assertEqual([row["id"] for row in store.list()], [first["id"]])

    @staticmethod
    def _record(title: str) -> dict[str, object]:
        return {
            "title": title,
            "owner": "analyst",
            "priority": "medium",
            "status": "open",
            "summary": "Cloud recovery fixture",
            "resolution": None,
            "release_id": "release-test",
            "report_period": "2026-01",
            "correction_view": "latest",
            "metric_version": "test",
            "filter_context": {},
            "evidence": [{
                "contract_id": "test-contract",
                "component": "test-component",
                "period": "2026-01",
                "correction_view": "latest",
                "provenance": "test-fixture",
            }],
        }


if __name__ == "__main__":
    unittest.main()
