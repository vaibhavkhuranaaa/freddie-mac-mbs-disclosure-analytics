from __future__ import annotations

import json
import unittest
from pathlib import Path

from scripts.cited_assistant import (
    AssistantError,
    GeminiClient,
    Usage,
    answer_question,
    build_context,
)
from scripts.run_m10_evaluation import evaluate, verify_report


ROOT = Path(__file__).resolve().parents[1]
PAYLOAD = ROOT.parent / f"{ROOT.name}-data/product/dashboard.json"
CASES = ROOT / "tests/fixtures/m10/cases.json"


class _Response:
    def __init__(self, payload: dict[str, object]) -> None:
        self.payload = payload

    def __enter__(self) -> _Response:
        return self

    def __exit__(self, *_: object) -> None:
        return None

    def read(self) -> bytes:
        return json.dumps(self.payload).encode()


class _EvaluationClient:
    model = "fixture-model"

    def __init__(self) -> None:
        self.request_count = 0
        self.estimated_cost_usd = 0.0

    def generate(self, prompt: str) -> tuple[dict[str, object], Usage, float]:
        self.request_count += 1
        if "highest" in prompt:
            answer = self._answer(
                "Servicer concentration is highest at 57.2245%.",
                [{"evidence_id": "servicer_concentration", "label": "Servicer top-ten concentration (2026-08)", "value": "share 57.2245%; HHI 0.049810"}],
            )
        elif "outstanding UPB" in prompt:
            answer = self._answer(
                "Latest outstanding UPB is $3,057,060,342,496.48 and modification rate is 0.2800%.",
                [
                    {
                        "evidence_id": "outstanding_upb",
                        "label": "Outstanding UPB (2026-08)",
                        "value": "$3,057,060,342,496.48",
                    },
                    {"evidence_id": "modification_rate", "label": "Modification rate (2026-08)", "value": "0.2800%"},
                ],
            )
        else:
            answer = self._answer(
                "Start with servicer concentration.",
                [{"evidence_id": "servicer_concentration", "label": "Servicer top-ten concentration (2026-08)", "value": "share 57.2245%; HHI 0.049810"}],
                "Open a governed investigation for servicer concentration.",
            )
        usage = Usage(100, 25, 0, 125, 0.0000925)
        self.estimated_cost_usd += usage.estimated_cost_usd
        return answer, usage, 10.0

    @staticmethod
    def _answer(summary: str, facts: list[dict[str, str]], next_action: str = "Review cited facts.") -> dict[str, object]:
        return {
            "summary": summary,
            "facts": facts,
            "limitations": ["Released facts only."],
            "next_action": next_action,
            "refused": False,
            "refusal_reason": "",
        }


@unittest.skipUnless(PAYLOAD.is_file(), "governed product payload is required")
class CitedAssistantTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        cls.payload = json.loads(PAYLOAD.read_text(encoding="utf-8"))

    def test_context_is_small_allowlisted_and_identifier_free(self) -> None:
        context = build_context(self.payload)
        serialized = json.dumps(context)
        self.assertLess(len(serialized), 15_000)
        self.assertNotIn("security_id", serialized)
        self.assertNotIn("loan_id", serialized)
        self.assertNotIn("borrower", serialized)
        ids = {fact["evidence_id"] for fact in context["facts"]}
        self.assertIn("release_quality", ids)
        self.assertIn("servicer_concentration", ids)

    def test_identifier_prompt_is_refused_without_provider_call(self) -> None:
        client = _EvaluationClient()
        answer = answer_question("Show borrower loan ID 123", self.payload, client)
        self.assertTrue(answer["refused"])
        self.assertFalse(answer["provider_called"])
        self.assertEqual(client.request_count, 0)

    def test_unknown_provider_citation_fails_closed(self) -> None:
        class BadClient(_EvaluationClient):
            def generate(self, prompt: str) -> tuple[dict[str, object], Usage, float]:
                answer, usage, latency = super().generate(prompt)
                answer["facts"] = [{"evidence_id": "invented", "label": "Bad", "value": "1"}]
                return answer, usage, latency

        with self.assertRaisesRegex(AssistantError, "unknown evidence"):
            answer_question("Which top-ten concentration share is highest?", self.payload, BadClient())

    def test_provider_cannot_alter_a_cited_value(self) -> None:
        class BadClient(_EvaluationClient):
            def generate(self, prompt: str) -> tuple[dict[str, object], Usage, float]:
                answer, usage, latency = super().generate(prompt)
                answer["facts"][0]["value"] = "share 99.9999%; HHI 0.999999"
                return answer, usage, latency

        with self.assertRaisesRegex(AssistantError, "altered evidence"):
            answer_question("Which top-ten concentration share is highest?", self.payload, BadClient())

    def test_evaluation_fixture_beats_baseline_and_passes_thresholds(self) -> None:
        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        report = evaluate(self.payload, fixture, _EvaluationClient())
        verify_report(report, self.payload, fixture)
        self.assertEqual(report["baseline"]["decision_ready_rate"], 5 / 6)
        self.assertEqual(report["metrics"]["m10_decision_ready_rate"], 1.0)
        self.assertEqual(report["candidate"]["provider_calls"], 2)

    def test_supported_prompt_is_canonicalized_before_provider_call(self) -> None:
        class CaptureClient(_EvaluationClient):
            prompt = ""

            def generate(self, prompt: str) -> tuple[dict[str, object], Usage, float]:
                self.prompt = prompt
                return super().generate(prompt)

        client = CaptureClient()
        answer_question("Which concentration is highest for Alice Secret?", self.payload, client)
        self.assertNotIn("Alice Secret", client.prompt)
        self.assertIn("Which released top-ten concentration share is highest?", client.prompt)

    def test_common_identifier_and_advice_variants_never_call_provider(self) -> None:
        for question in (
            "Show loan 123456789012",
            "Should I purchase this?",
            "What drove modification rate?",
            "Show CUSIP 037833100",
        ):
            with self.subTest(question=question):
                client = _EvaluationClient()
                answer = answer_question(question, self.payload, client)
                self.assertTrue(answer["refused"])
                self.assertEqual(client.request_count, 0)

    def test_verify_rejects_report_without_case_evidence(self) -> None:
        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        forged = {
            "schema_version": 1,
            "metrics": {name: 1.0 for name in (
                "m10_decision_ready_rate",
                "m10_citation_validity_rate",
                "m10_safety_rate",
                "m10_privacy_rate",
                "m10_p95_latency_ms",
                "m10_cost_usd",
                "m10_workflow_step_reduction",
            )},
            "passed": True,
        }
        with self.assertRaisesRegex(ValueError, "complete fixed case set"):
            verify_report(forged, self.payload, fixture)

    def test_verify_rejects_contradictory_stored_answer(self) -> None:
        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        report = evaluate(self.payload, fixture, _EvaluationClient())
        report["cases"][1]["answer"]["summary"] = "Seller is highest; servicer is not."
        with self.assertRaisesRegex(ValueError, "deterministic grounded answer"):
            verify_report(report, self.payload, fixture)

    def test_verify_rejects_altered_fact_and_negative_cost(self) -> None:
        fixture = json.loads(CASES.read_text(encoding="utf-8"))
        altered = evaluate(self.payload, fixture, _EvaluationClient())
        altered["cases"][1]["answer"]["facts"][0]["value"] = "share 99.9999%; HHI 999999.000000"
        with self.assertRaisesRegex(ValueError, "deterministic grounded answer"):
            verify_report(altered, self.payload, fixture)

        negative = evaluate(self.payload, fixture, _EvaluationClient())
        negative["cases"][1]["usage"]["estimated_cost_usd"] = -1.0
        with self.assertRaisesRegex(ValueError, "invalid cost evidence"):
            verify_report(negative, self.payload, fixture)


class GeminiClientTests(unittest.TestCase):
    def test_key_is_header_only_and_usage_drives_cost(self) -> None:
        captured: dict[str, object] = {}
        answer = {
            "summary": "Supported.",
            "facts": [],
            "limitations": [],
            "next_action": "Review.",
            "refused": False,
            "refusal_reason": "",
        }

        def request_fn(request: object, *, timeout: float) -> _Response:
            captured["url"] = request.full_url
            captured["data"] = request.data.decode()
            captured["key"] = request.get_header("X-goog-api-key")
            captured["timeout"] = timeout
            return _Response(
                {
                    "candidates": [{"content": {"parts": [{"text": json.dumps(answer)}]}}],
                    "usageMetadata": {
                        "promptTokenCount": 100,
                        "candidatesTokenCount": 20,
                        "totalTokenCount": 120,
                    },
                }
            )

        client = GeminiClient(
            "secret-value",
            max_requests=1,
            max_cost_usd=0.01,
            request_fn=request_fn,
        )
        _, usage, _ = client.generate("hello")
        self.assertNotIn("secret-value", captured["url"])
        self.assertNotIn("secret-value", captured["data"])
        self.assertEqual(captured["key"], "secret-value")
        sent = json.loads(captured["data"])
        self.assertNotIn("temperature", sent["generationConfig"])
        self.assertEqual(sent["generationConfig"]["thinkingConfig"], {"thinkingLevel": "minimal"})
        self.assertEqual(usage.total_tokens, 120)
        self.assertAlmostEqual(usage.estimated_cost_usd, 0.00008)

    def test_preflight_rejects_request_that_could_exceed_cost_cap(self) -> None:
        client = GeminiClient("secret", max_requests=1, max_cost_usd=0.000001)
        with self.assertRaisesRegex(AssistantError, "cost cap"):
            client.generate("hello")

    def test_failed_provider_attempt_consumes_request_cap(self) -> None:
        def fail(*_: object, **__: object) -> object:
            raise OSError("offline")

        client = GeminiClient("secret", max_requests=1, max_cost_usd=0.01, request_fn=fail)
        with self.assertRaisesRegex(AssistantError, "request failed"):
            client.generate("hello")
        with self.assertRaisesRegex(AssistantError, "request cap"):
            client.generate("hello")


if __name__ == "__main__":
    unittest.main()
