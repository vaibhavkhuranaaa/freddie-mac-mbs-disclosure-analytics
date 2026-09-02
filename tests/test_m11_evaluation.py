from __future__ import annotations

import hashlib
import json
import tempfile
import unittest
from pathlib import Path

from scripts.run_m11_evaluation import metrics, verify


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


class M11EvaluationTests(unittest.TestCase):
    def setUp(self) -> None:
        self.temporary = tempfile.TemporaryDirectory()
        root = Path(self.temporary.name)
        self.repo = root / "repo"
        self.data = root / "data"
        (self.repo / "infra/m11").mkdir(parents=True)
        (self.data / "product").mkdir(parents=True)
        for name, content in (
            ("foundation.bicep", "foundation\n"),
            ("app.bicep", "app\n"),
            ("Dockerfile", "FROM scratch\n"),
        ):
            (self.repo / "infra/m11" / name).write_text(content, encoding="utf-8")
        payload = self.data / "product/dashboard.json"
        payload.write_text('{"semantic":{"release_id":"test"}}\n', encoding="utf-8")
        normalized = json.dumps(json.loads(payload.read_text()), sort_keys=True, separators=(",", ":")) + "\n"
        self.evidence = {
            "version": 2,
            "status": "passed",
            "provider": "Microsoft Azure",
            "region": "centralus",
            "resource_group": "rg-test",
            "started_at": "2026-09-01T16:00:00Z",
            "evidence_captured_at": "2026-09-01T16:30:00Z",
            "ended_at": "2026-09-01T16:45:00Z",
            "checks": {name: True for name in ("security", "recovery", "observability", "load", "rollback", "lineage", "cost", "teardown")},
            "security": {
                "probes": [
                    {"name": "unauthenticated", "status": 401},
                    {"name": "spoofed_platform_header", "status": 401},
                    {"name": "authorized", "status": 200},
                    {"name": "ai_disabled", "status": 503},
                ],
                "entra_enabled": True,
                "https_required": True,
                "allow_insecure": False,
                "maximum_replicas": 1,
                "container_uid": 10001,
                "template_auth_configured": True,
                "trusted_actor": "entra-principal-id",
            },
            "recovery": {"backup_integrity": "ok", "cases_before_restore": 2, "cases_after_restore": 1, "restored_id": "INV-1", "expected_id": "INV-1"},
            "observability": {
                "request_audit_rows": 50,
                "queries": {
                    "system": {"row_count": 1, "latest_timestamp": "2026-09-01T16:20:00Z"},
                    "console": {"row_count": 1, "latest_timestamp": "2026-09-01T16:25:00Z"},
                },
            },
            "load": {"concurrency": 10, "requests": [{"status": 200, "latency_ms": float(value)} for value in range(1, 51)]},
            "rollback": {"source_revision": "v1", "probe_revision": "v2", "result_revision": "rb1", "health_status": 200, "state_preserved": True, "result_image": "registry.example/mbs@sha256:" + "c" * 64},
            "lineage": {
                "payload_sha256": sha256(payload),
                "normalized_payload_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
                "cloud_normalized_payload_sha256": hashlib.sha256(normalized.encode()).hexdigest(),
                "reviewed_foundation_bicep_sha256": sha256(self.repo / "infra/m11/foundation.bicep"),
                "reviewed_app_bicep_sha256": sha256(self.repo / "infra/m11/app.bicep"),
                "image_source_dockerfile_sha256": sha256(self.repo / "infra/m11/Dockerfile"),
                "deployed_app_bicep_sha256": "d" * 64,
                "image_digest": "sha256:" + "c" * 64,
                "rollback_revision": "rb1",
            },
            "cost": {
                "ceiling_usd": 5.0,
                "evaluation_threshold_usd": 1.0,
                "observed_budget_spend_usd": 0.0,
                "upper_bound_usd": 0.25,
                "components": [{"name": "registry", "upper_bound_usd": 0.2}, {"name": "other", "upper_bound_usd": 0.05}],
            },
            "teardown": {
                "entra_application_id": "app-id",
                "entra_service_principal_id": "sp-id",
                "temporary_paths": [str(root / "absent")],
                "probes": [
                    {"target_type": "azure_resource_group", "target_id": "rg-test", "exists": False, "checked_at": "2026-09-01T16:40:00Z"},
                    {"target_type": "entra_application", "target_id": "app-id", "exists": False, "checked_at": "2026-09-01T16:41:00Z"},
                    {"target_type": "entra_service_principal", "target_id": "sp-id", "exists": False, "checked_at": "2026-09-01T16:42:00Z"},
                ],
            },
        }

    def tearDown(self) -> None:
        self.temporary.cleanup()

    def test_passing_receipts_recompute_metrics(self) -> None:
        values = metrics(self.evidence, self.repo, self.data)
        verify(values)
        self.assertEqual(values["m11_release_acceptance_rate"], 1.0)
        self.assertEqual(values["m11_p95_latency_ms"], 48.0)

    def test_invalid_hash_timestamp_latency_and_cost_fail_closed(self) -> None:
        mutations = (
            lambda evidence: evidence["lineage"].update(payload_sha256="x" * 64),
            lambda evidence: evidence["observability"]["queries"]["system"].update(latest_timestamp="not-a-timestamp"),
            lambda evidence: evidence["load"]["requests"][0].update(latency_ms=-1),
            lambda evidence: evidence["cost"].update(upper_bound_usd=-1),
        )
        for mutate in mutations:
            with self.subTest(mutation=mutate):
                copy = json.loads(json.dumps(self.evidence))
                mutate(copy)
                with self.assertRaises((KeyError, TypeError, ValueError)):
                    metrics(copy, self.repo, self.data)

    def test_missing_raw_receipts_fail_closed(self) -> None:
        evidence = json.loads(json.dumps(self.evidence))
        evidence["load"]["requests"] = []
        with self.assertRaises(ValueError):
            metrics(evidence, self.repo, self.data)


if __name__ == "__main__":
    unittest.main()
