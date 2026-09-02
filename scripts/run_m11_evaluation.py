#!/usr/bin/env python3
"""Verify M11 acceptance from raw receipts and local release artifacts."""

from __future__ import annotations

import argparse
import hashlib
import json
import math
import re
from datetime import datetime
from pathlib import Path


THRESHOLDS = {
    "m11_release_acceptance_rate": ("maximize", 1.0),
    "m11_p95_latency_ms": ("minimize", 2000.0),
    "m11_cost_usd": ("minimize", 1.0),
}
HEX_256 = re.compile(r"^[0-9a-f]{64}$")
DIGEST_256 = re.compile(r"^sha256:[0-9a-f]{64}$")


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _normalized_json_sha256(path: Path) -> str:
    payload = json.loads(path.read_text(encoding="utf-8"))
    canonical = json.dumps(payload, sort_keys=True, separators=(",", ":")) + "\n"
    return hashlib.sha256(canonical.encode()).hexdigest()


def _timestamp(value: object) -> datetime:
    if not isinstance(value, str) or not value.endswith("Z"):
        raise ValueError(f"invalid UTC timestamp: {value!r}")
    parsed = datetime.fromisoformat(value[:-1] + "+00:00")
    if parsed.utcoffset() is None:
        raise ValueError(f"timestamp lacks timezone: {value!r}")
    return parsed


def _nonnegative(value: object, name: str) -> float:
    number = float(value)
    if not math.isfinite(number) or number < 0:
        raise ValueError(f"{name} must be finite and nonnegative")
    return number


def _p95(values: list[float]) -> float:
    if not values:
        raise ValueError("load receipt is empty")
    return sorted(values)[math.ceil(len(values) * 0.95) - 1]


def metrics(
    evidence: dict[str, object],
    repo_root: Path | None = None,
    data_root: Path | None = None,
) -> dict[str, float]:
    repo = (repo_root or Path(__file__).resolve().parents[1]).resolve()
    data = (data_root or repo.parent / f"{repo.name}-data").resolve()
    started = _timestamp(evidence["started_at"])
    captured = _timestamp(evidence["evidence_captured_at"])
    ended = _timestamp(evidence["ended_at"])
    if not started <= captured <= ended:
        raise ValueError("evidence timestamps are out of order")
    if evidence.get("version") != 2 or evidence.get("status") != "passed":
        raise ValueError("unsupported or non-passing M11 evidence")
    if evidence.get("provider") != "Microsoft Azure" or evidence.get("region") != "centralus":
        raise ValueError("unexpected provider or region")

    security = evidence["security"]
    probes = {row["name"]: row["status"] for row in security["probes"]}
    expected_probes = {
        "unauthenticated": 401,
        "spoofed_platform_header": 401,
        "authorized": 200,
        "ai_disabled": 503,
    }
    if len(probes) != len(security["probes"]):
        raise ValueError("duplicate security probe")

    recovery = evidence["recovery"]
    observability = evidence["observability"]
    queries = observability["queries"]
    log_times = [_timestamp(queries[name]["latest_timestamp"]) for name in ("system", "console")]

    load = evidence["load"]
    request_receipts = load["requests"]
    latencies = [_nonnegative(row["latency_ms"], "load latency") for row in request_receipts]
    statuses = [row["status"] for row in request_receipts]
    p95_latency = _p95(latencies)

    rollback = evidence["rollback"]
    lineage = evidence["lineage"]
    payload = data / "product/dashboard.json"
    local_hashes = {
        "payload_sha256": _sha256(payload),
        "normalized_payload_sha256": _normalized_json_sha256(payload),
        "reviewed_foundation_bicep_sha256": _sha256(repo / "infra/m11/foundation.bicep"),
        "reviewed_app_bicep_sha256": _sha256(repo / "infra/m11/app.bicep"),
        "image_source_dockerfile_sha256": _sha256(repo / "infra/m11/Dockerfile"),
    }

    cost = evidence["cost"]
    components = [_nonnegative(row["upper_bound_usd"], "cost component") for row in cost["components"]]
    computed_cost = round(sum(components), 6)
    upper_bound = _nonnegative(cost["upper_bound_usd"], "cost upper bound")
    observed_spend = _nonnegative(cost["observed_budget_spend_usd"], "observed spend")

    teardown = evidence["teardown"]
    teardown_probes = {(row["target_type"], row["target_id"]): row["exists"] for row in teardown["probes"]}
    expected_teardown_targets = {
        ("azure_resource_group", evidence["resource_group"]),
        ("entra_application", teardown["entra_application_id"]),
        ("entra_service_principal", teardown["entra_service_principal_id"]),
    }
    prior_teardown_probes = teardown.get("prior_failed_run_probes", [])
    temp_paths_absent = all(not Path(path).exists() for path in teardown["temporary_paths"])

    derived_checks = {
        "security": (
            probes == expected_probes
            and security["entra_enabled"] is True
            and security["https_required"] is True
            and security["allow_insecure"] is False
            and security["maximum_replicas"] == 1
            and security["container_uid"] == 10001
            and security["template_auth_configured"] is True
            and bool(security["trusted_actor"])
            and security["trusted_actor"] != "forged-actor"
        ),
        "recovery": (
            recovery["backup_integrity"] == "ok"
            and recovery["cases_before_restore"] > recovery["cases_after_restore"] == 1
            and recovery["restored_id"] == recovery["expected_id"]
        ),
        "observability": (
            observability["request_audit_rows"] > 0
            and queries["system"]["row_count"] > 0
            and queries["console"]["row_count"] > 0
            and all(started <= value <= captured for value in log_times)
        ),
        "load": (
            len(request_receipts) >= 50
            and load["concurrency"] >= 10
            and all(status == 200 for status in statuses)
            and p95_latency <= THRESHOLDS["m11_p95_latency_ms"][1]
        ),
        "rollback": (
            rollback["health_status"] == 200
            and rollback["state_preserved"] is True
            and rollback["source_revision"] != rollback["probe_revision"]
            and rollback["result_revision"] != rollback["probe_revision"]
            and rollback["result_image"].endswith("@" + lineage["image_digest"])
        ),
        "lineage": (
            all(HEX_256.fullmatch(value) for value in local_hashes.values())
            and all(lineage[name] == value for name, value in local_hashes.items())
            and lineage["cloud_normalized_payload_sha256"] == local_hashes["normalized_payload_sha256"]
            and DIGEST_256.fullmatch(lineage["image_digest"]) is not None
            and HEX_256.fullmatch(lineage["deployed_app_bicep_sha256"]) is not None
            and lineage["rollback_revision"] == rollback["result_revision"]
        ),
        "cost": (
            math.isclose(computed_cost, upper_bound, abs_tol=0.000001)
            and observed_spend <= upper_bound
            and upper_bound <= _nonnegative(cost["evaluation_threshold_usd"], "cost threshold")
            and upper_bound <= _nonnegative(cost["ceiling_usd"], "cost ceiling")
        ),
        "teardown": (
            set(teardown_probes) == expected_teardown_targets
            and all(exists is False for exists in teardown_probes.values())
            and all(started <= _timestamp(row["checked_at"]) <= ended for row in teardown["probes"])
            and all(row["exists"] is False for row in prior_teardown_probes)
            and all(started <= _timestamp(row["checked_at"]) <= ended for row in prior_teardown_probes)
            and temp_paths_absent
        ),
    }
    if evidence.get("checks") != derived_checks:
        raise ValueError("recorded checks do not match verified evidence")
    return {
        "m11_release_acceptance_rate": sum(derived_checks.values()) / len(derived_checks),
        "m11_p95_latency_ms": p95_latency,
        "m11_cost_usd": upper_bound,
    }


def verify(values: dict[str, float]) -> None:
    failures = []
    for name, value in values.items():
        if not math.isfinite(value) or value < 0:
            failures.append(f"{name} is not finite and nonnegative")
            continue
        direction, threshold = THRESHOLDS[name]
        passed = value >= threshold if direction == "maximize" else value <= threshold
        if not passed:
            failures.append(f"{name}={value} missed {threshold}")
    if failures:
        raise ValueError("; ".join(failures))


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--evidence", type=Path, required=True)
    parser.add_argument("--repo-root", type=Path)
    parser.add_argument("--data-root", type=Path)
    parser.add_argument("--metric", choices=sorted(THRESHOLDS))
    args = parser.parse_args()
    values = metrics(
        json.loads(args.evidence.read_text(encoding="utf-8")),
        repo_root=args.repo_root,
        data_root=args.data_root,
    )
    verify(values)
    if args.metric:
        print(values[args.metric])
    else:
        print(json.dumps({"status": "passed", "metrics": values}, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
