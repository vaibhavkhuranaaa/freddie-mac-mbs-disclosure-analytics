from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from scripts.investigation_store import InvestigationStore
from scripts.serve_product import ProductHandler, make_handler


class ProductApiContractTests(unittest.TestCase):
    def test_bound_handler_has_separate_store_and_secret(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static = root / "app"
            static.mkdir()
            payload = root / "dashboard.json"
            payload.write_text(json.dumps({"semantic": {"release_id": "test"}}), encoding="utf-8")
            database = root / "investigations.sqlite"
            handler = make_handler(static, payload, database, "0123456789abcdef")
            self.assertEqual(handler.api_token, "0123456789abcdef")
            self.assertEqual(handler.payload_path, payload.resolve())
            self.assertIsInstance(handler.investigation_store, InvestigationStore)
            self.assertTrue(database.is_file())

    def test_machine_contract_is_allowlisted_and_forbids_arbitrary_sql(self) -> None:
        root = Path(__file__).resolve().parents[1]
        contract = json.loads((root / "contracts/semantic-api-v1.json").read_text(encoding="utf-8"))
        routes = {(row["method"], row["path"]) for row in contract["routes"]}
        self.assertIn(("GET", "/v1/dashboard"), routes)
        self.assertIn(("GET", "/v1/audit/requests"), routes)
        self.assertIn(("POST", "/v1/assistant"), routes)
        self.assertIn("arbitrary SQL", contract["prohibited"])
        self.assertFalse(contract["authorization"]["secrets_logged"])

    def test_assistant_is_disabled_by_default(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static = root / "app"
            static.mkdir()
            payload = root / "dashboard.json"
            payload.write_text(json.dumps({"semantic": {"release_id": "test"}}), encoding="utf-8")
            handler = make_handler(static, payload, root / "investigations.sqlite", "0123456789abcdef")
            self.assertIsNone(handler.cited_assistant)

    def test_platform_identity_mode_is_explicit(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            static = root / "app"
            static.mkdir()
            payload = root / "dashboard.json"
            payload.write_text(json.dumps({"semantic": {"release_id": "test"}}), encoding="utf-8")
            handler = make_handler(static, payload, root / "investigations.sqlite", "", trust_platform_identity=True)
            self.assertTrue(handler.platform_identity_enabled)
            self.assertEqual(handler.api_token, "")

    def test_platform_identity_overrides_client_supplied_actor(self) -> None:
        handler = object.__new__(ProductHandler)
        handler.trust_platform_identity = True
        handler.api_token = ""
        handler.headers = {
            "X-MS-CLIENT-PRINCIPAL-ID": "entra-principal-id",
            "X-Actor": "forged-actor",
        }
        handler._authorized_state = False
        handler._authenticated_actor = ""
        self.assertTrue(handler._authorized())
        self.assertEqual(handler._actor(), "entra-principal-id")


if __name__ == "__main__":
    unittest.main()
