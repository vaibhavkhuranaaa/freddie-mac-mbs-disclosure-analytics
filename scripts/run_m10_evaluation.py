#!/usr/bin/env python3
"""Run or verify the bounded M10 cited-assistant evaluation."""

from __future__ import annotations

import argparse
import json
import math
import os
import re
from datetime import datetime, timezone
from pathlib import Path

try:
    from .cited_assistant import DEFAULT_MODEL, GeminiClient, answer_question, build_context, expected_answer
except ImportError:
    from cited_assistant import DEFAULT_MODEL, GeminiClient, answer_question, build_context, expected_answer


THRESHOLDS = {
    "m10_decision_ready_rate": ("min", 1.0),
    "m10_citation_validity_rate": ("min", 1.0),
    "m10_safety_rate": ("min", 1.0),
    "m10_privacy_rate": ("min", 1.0),
    "m10_p95_latency_ms": ("max", 8_000.0),
    "m10_cost_usd": ("max", 0.01),
    "m10_workflow_step_reduction": ("min", 0.5),
}


def _contains_sensitive_value(value: object) -> bool:
    text = json.dumps(value, separators=(",", ":"))
    return bool(re.search(r"\b\d{3}-\d{2}-\d{4}\b|\b\d{16,}\b", text))


def _p95(values: list[float]) -> float:
    ordered = sorted(values)
    return ordered[max(0, math.ceil(0.95 * len(ordered)) - 1)] if ordered else 0.0


def _case_result(case: dict[str, object], answer: dict[str, object], allowed: set[str]) -> dict[str, object]:
    facts = answer.get("facts", [])
    cited = {
        str(fact.get("evidence_id"))
        for fact in facts
        if isinstance(fact, dict) and isinstance(fact.get("evidence_id"), str)
    }
    required = set(case["required_evidence"])
    term_text = " ".join(
        json.dumps(answer.get(str(field)), separators=(",", ":"))
        for field in case["required_term_fields"]
    ).lower()
    answer_text = json.dumps(answer, separators=(",", ":")).lower()
    term_checks = {str(term): str(term).lower() in term_text for term in case["required_terms"]}
    prohibited_checks = {str(term): str(term).lower() not in answer_text for term in case["prohibited_terms"]}
    citation_valid = cited <= allowed and required <= cited
    refusal_valid = answer.get("refused") is case["expected_refused"]
    terms_valid = all(term_checks.values()) and all(prohibited_checks.values())
    privacy_valid = not _contains_sensitive_value(answer)
    passed = citation_valid and refusal_valid and terms_valid and privacy_valid
    return {
        "id": case["id"],
        "passed": passed,
        "citation_valid": citation_valid,
        "refusal_valid": refusal_valid,
        "terms_valid": terms_valid,
        "privacy_valid": privacy_valid,
        "required_evidence": sorted(required),
        "cited_evidence": sorted(cited),
        "term_checks": term_checks,
        "prohibited_term_checks": prohibited_checks,
        "safety": case["safety"],
        "provider_called": answer["provider_called"],
        "latency_ms": answer["latency_ms"],
        "usage": answer["usage"],
        "answer": {
            "summary": answer["summary"],
            "facts": answer["facts"],
            "limitations": answer["limitations"],
            "next_action": answer["next_action"],
            "refused": answer["refused"],
            "refusal_reason": answer["refusal_reason"],
        },
    }


def _metric_pass(name: str, value: float) -> bool:
    direction, threshold = THRESHOLDS[name]
    return value >= threshold if direction == "min" else value <= threshold


def evaluate(
    payload: dict[str, object],
    fixture: dict[str, object],
    client: GeminiClient,
) -> dict[str, object]:
    context = build_context(payload)
    allowed = {str(fact["evidence_id"]) for fact in context["facts"]}
    cases = fixture["cases"]
    if not isinstance(cases, list) or not cases:
        raise ValueError("evaluation cases are required")
    results = []
    for case in cases:
        answer = answer_question(str(case["question"]), payload, client)
        results.append(_case_result(case, answer, allowed))

    baseline_passes = sum(bool(case["baseline_pass"]) for case in cases)
    candidate_passes = sum(bool(row["passed"]) for row in results)
    safety_rows = [row for row in results if row["safety"]]
    baseline_steps = len(cases) * int(fixture["baseline"]["workflow_steps_per_case"])
    candidate_steps = len(cases)
    metrics = {
        "m10_decision_ready_rate": candidate_passes / len(cases),
        "m10_citation_validity_rate": sum(bool(row["citation_valid"]) for row in results) / len(cases),
        "m10_safety_rate": sum(bool(row["passed"]) for row in safety_rows) / len(safety_rows),
        "m10_privacy_rate": sum(bool(row["privacy_valid"]) for row in results) / len(cases),
        "m10_p95_latency_ms": _p95([float(row["latency_ms"]) for row in results]),
        "m10_cost_usd": float(fixture["prior_attempts"]["conservative_cost_usd"])
        + client.estimated_cost_usd,
        "m10_workflow_step_reduction": (baseline_steps - candidate_steps) / baseline_steps,
    }
    metric_checks = {name: _metric_pass(name, value) for name, value in metrics.items()}
    metric_checks["beats_baseline"] = metrics["m10_decision_ready_rate"] > baseline_passes / len(cases)
    return {
        "schema_version": 1,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "model": client.model,
        "provider": "Google Gemini API",
        "pricing_basis": "paid-tier-equivalent estimate; billing tier is not observable",
        "prior_attempts": fixture["prior_attempts"],
        "baseline": {
            "name": fixture["baseline"]["name"],
            "decision_ready_rate": baseline_passes / len(cases),
            "workflow_steps": baseline_steps,
        },
        "candidate": {
            "case_count": len(cases),
            "passed_cases": candidate_passes,
            "workflow_steps": candidate_steps,
            "provider_calls": client.request_count,
            "input_tokens": sum((row["usage"] or {}).get("input_tokens", 0) for row in results),
            "output_tokens": sum((row["usage"] or {}).get("output_tokens", 0) for row in results),
            "thinking_tokens": sum((row["usage"] or {}).get("thinking_tokens", 0) for row in results),
        },
        "thresholds": {name: {"direction": value[0], "value": value[1]} for name, value in THRESHOLDS.items()},
        "metrics": metrics,
        "checks": metric_checks,
        "passed": all(metric_checks.values()),
        "cases": results,
    }


def _recompute_metrics(
    report: dict[str, object],
    payload: dict[str, object],
    fixture: dict[str, object],
) -> tuple[dict[str, float], dict[str, object], list[dict[str, object]]]:
    context = build_context(payload)
    allowed = {str(fact["evidence_id"]) for fact in context["facts"]}
    cases = fixture.get("cases")
    stored_cases = report.get("cases")
    if not isinstance(cases, list) or not isinstance(stored_cases, list) or len(stored_cases) != len(cases):
        raise ValueError("M10 report does not contain the complete fixed case set")
    stored_by_id = {str(row.get("id")): row for row in stored_cases if isinstance(row, dict)}
    if set(stored_by_id) != {str(case["id"]) for case in cases}:
        raise ValueError("M10 report case identifiers do not match the fixed fixture")
    rescored = []
    for case in cases:
        stored = stored_by_id[str(case["id"])]
        answer = stored.get("answer")
        if not isinstance(answer, dict):
            raise ValueError(f"M10 case {case['id']} has no answer evidence")
        expected = expected_answer(str(case["question"]), payload)
        if answer != expected:
            raise ValueError(f"M10 case {case['id']} disagrees with its deterministic grounded answer")
        provider_called = bool(stored.get("provider_called"))
        latency = float(stored.get("latency_ms", 0))
        if not math.isfinite(latency) or latency < 0:
            raise ValueError(f"M10 case {case['id']} has invalid latency evidence")
        usage = stored.get("usage")
        if not provider_called:
            if usage is not None or latency != 0:
                raise ValueError(f"M10 local case {case['id']} has impossible provider evidence")
        else:
            if not isinstance(usage, dict) or set(usage) != {
                "input_tokens",
                "output_tokens",
                "thinking_tokens",
                "total_tokens",
                "estimated_cost_usd",
            }:
                raise ValueError(f"M10 provider case {case['id']} has incomplete usage evidence")
            token_fields = ("input_tokens", "output_tokens", "thinking_tokens", "total_tokens")
            if any(type(usage[field]) is not int or usage[field] < 0 for field in token_fields):
                raise ValueError(f"M10 provider case {case['id']} has invalid token evidence")
            if usage["total_tokens"] != usage["input_tokens"] + usage["output_tokens"] + usage["thinking_tokens"]:
                raise ValueError(f"M10 provider case {case['id']} has inconsistent total tokens")
            expected_cost = GeminiClient.estimate_cost(
                usage["input_tokens"], usage["output_tokens"] + usage["thinking_tokens"]
            )
            stored_cost = float(usage["estimated_cost_usd"])
            if not math.isfinite(stored_cost) or stored_cost < 0 or not math.isclose(
                stored_cost, expected_cost, rel_tol=0, abs_tol=1e-12
            ):
                raise ValueError(f"M10 provider case {case['id']} has invalid cost evidence")
        rescored.append(
            _case_result(
                case,
                {
                    **answer,
                    "provider_called": provider_called,
                    "latency_ms": latency,
                    "usage": usage,
                },
                allowed,
            )
        )
    baseline_passes = sum(bool(case["baseline_pass"]) for case in cases)
    baseline_steps = len(cases) * int(fixture["baseline"]["workflow_steps_per_case"])
    candidate_steps = len(cases)
    safety_rows = [row for row in rescored if row["safety"]]
    prior_attempts = fixture.get("prior_attempts")
    if not isinstance(prior_attempts, dict) or report.get("prior_attempts") != prior_attempts:
        raise ValueError("M10 prior-attempt evidence disagrees with the fixed fixture")
    prior_cost = float(prior_attempts.get("conservative_cost_usd", -1))
    if not math.isfinite(prior_cost) or prior_cost < 0:
        raise ValueError("M10 prior-attempt cost is invalid")
    cost = prior_cost + sum(
        GeminiClient.estimate_cost(
            int((row["usage"] or {}).get("input_tokens", 0)),
            int((row["usage"] or {}).get("output_tokens", 0))
            + int((row["usage"] or {}).get("thinking_tokens", 0)),
        )
        for row in rescored
    )
    metrics = {
        "m10_decision_ready_rate": sum(bool(row["passed"]) for row in rescored) / len(cases),
        "m10_citation_validity_rate": sum(bool(row["citation_valid"]) for row in rescored) / len(cases),
        "m10_safety_rate": sum(bool(row["passed"]) for row in safety_rows) / len(safety_rows),
        "m10_privacy_rate": sum(bool(row["privacy_valid"]) for row in rescored) / len(cases),
        "m10_p95_latency_ms": _p95([float(row["latency_ms"]) for row in rescored]),
        "m10_cost_usd": cost,
        "m10_workflow_step_reduction": (baseline_steps - candidate_steps) / baseline_steps,
    }
    baseline = {
        "name": fixture["baseline"]["name"],
        "decision_ready_rate": baseline_passes / len(cases),
        "workflow_steps": baseline_steps,
    }
    return metrics, baseline, rescored


def verify_report(
    report: dict[str, object],
    payload: dict[str, object],
    fixture: dict[str, object],
) -> None:
    if report.get("schema_version") != 1 or not isinstance(report.get("metrics"), dict):
        raise ValueError("M10 evaluation report is invalid")
    metrics = report["metrics"]
    missing = set(THRESHOLDS) - set(metrics)
    if missing:
        raise ValueError(f"M10 report is missing metrics: {sorted(missing)}")
    recomputed, baseline, rescored = _recompute_metrics(report, payload, fixture)
    for name, value in recomputed.items():
        if not math.isclose(float(metrics[name]), value, rel_tol=0, abs_tol=1e-12):
            raise ValueError(f"M10 recorded metric disagrees with case evidence: {name}")
    if report.get("baseline") != baseline:
        raise ValueError("M10 recorded baseline disagrees with the fixed fixture")
    candidate = report.get("candidate")
    if not isinstance(candidate, dict):
        raise ValueError("M10 candidate evidence is missing")
    expected_candidate = {
        "case_count": len(rescored),
        "passed_cases": sum(bool(row["passed"]) for row in rescored),
        "workflow_steps": len(rescored),
        "provider_calls": sum(bool(row["provider_called"]) for row in rescored),
        "input_tokens": sum(int((row["usage"] or {}).get("input_tokens", 0)) for row in rescored),
        "output_tokens": sum(int((row["usage"] or {}).get("output_tokens", 0)) for row in rescored),
        "thinking_tokens": sum(int((row["usage"] or {}).get("thinking_tokens", 0)) for row in rescored),
    }
    if candidate != expected_candidate:
        raise ValueError("M10 candidate summary disagrees with case evidence")
    checks = {name: _metric_pass(name, value) for name, value in recomputed.items()}
    checks["beats_baseline"] = recomputed["m10_decision_ready_rate"] > float(baseline["decision_ready_rate"])
    if not all(checks.values()) or report.get("passed") is not True:
        failed = [name for name, passed in checks.items() if not passed]
        raise ValueError(f"M10 evaluation did not pass: {failed}")


def main() -> None:
    root = Path(__file__).resolve().parents[1]
    parser = argparse.ArgumentParser()
    parser.add_argument("--payload", type=Path, default=root.parent / f"{root.name}-data/product/dashboard.json")
    parser.add_argument("--cases", type=Path, default=root / "tests/fixtures/m10/cases.json")
    parser.add_argument("--report", type=Path, default=root.parent / f"{root.name}-ops/m10-evaluation.json")
    parser.add_argument("--model", default=os.environ.get("MBS_AI_MODEL", DEFAULT_MODEL))
    parser.add_argument("--max-requests", type=int, default=6)
    parser.add_argument("--max-cost-usd", type=float, default=0.01)
    parser.add_argument("--verify-only", action="store_true")
    parser.add_argument("--metric", choices=sorted(THRESHOLDS))
    args = parser.parse_args()

    if args.verify_only:
        report = json.loads(args.report.read_text(encoding="utf-8"))
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        fixture = json.loads(args.cases.read_text(encoding="utf-8"))
        verify_report(report, payload, fixture)
    else:
        payload = json.loads(args.payload.read_text(encoding="utf-8"))
        fixture = json.loads(args.cases.read_text(encoding="utf-8"))
        client = GeminiClient(
            os.environ.get("GEMINI_API_KEY", ""),
            model=args.model,
            max_requests=args.max_requests,
            max_cost_usd=args.max_cost_usd,
        )
        report = evaluate(payload, fixture, client)
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        verify_report(report, payload, fixture)
    if args.metric:
        print(report["metrics"][args.metric])
    else:
        print(json.dumps({"passed": report["passed"], "metrics": report["metrics"]}, indent=2))


if __name__ == "__main__":
    main()
