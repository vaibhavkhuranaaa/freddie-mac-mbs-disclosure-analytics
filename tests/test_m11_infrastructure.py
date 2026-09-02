from __future__ import annotations

import unittest
from pathlib import Path


class M11InfrastructureTests(unittest.TestCase):
    def test_external_ingress_has_fail_closed_entra_auth(self) -> None:
        root = Path(__file__).resolve().parents[1]
        template = (root / "infra/m11/app.bicep").read_text(encoding="utf-8")
        required = (
            "Microsoft.App/containerApps/authConfigs@2024-03-01",
            "unauthenticatedClientAction: 'Return401'",
            "requireHttps: true",
            "azureActiveDirectory:",
            "allowedAudiences:",
            "allowedApplications:",
            "@secure()",
            "MBS_TRUST_PLATFORM_IDENTITY",
        )
        for value in required:
            with self.subTest(value=value):
                self.assertIn(value, template)


if __name__ == "__main__":
    unittest.main()
