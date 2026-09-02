#!/usr/bin/env python3
"""Build the provider-neutral dashboard payload beside the governed release."""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
from datetime import UTC, datetime
from pathlib import Path


SERIES_COMPONENTS = {
    "loan_count": ("loan_count", "integer"),
    "loan_upb": ("loan_upb", "cents"),
    "average_loan_balance": ("average_current_loan_balance", "cents_value"),
    "delinquency_30_rate": ("30_plus_count", "value"),
    "delinquency_60_rate": ("60_plus_count", "value"),
    "delinquency_90_rate": ("90_plus_count", "value"),
    "modification_rate": ("modification_count_rate", "value"),
    "correction_count": ("loan_correction_count", "integer"),
}

CONCENTRATION_COMPONENTS = {
    "seller": ("seller_top_10_upb", "seller_upb_hhi"),
    "servicer": ("servicer_top_10_upb", "servicer_upb_hhi"),
    "state": ("state_top_10_upb", "state_upb_hhi"),
}

EVIDENCE_COMPONENTS = {
    "outstanding_upb": "loan_upb",
    "modification_rate": "modification_count_rate",
    "seller_concentration": "seller_top_10_upb",
    "servicer_concentration": "servicer_top_10_upb",
    "state_concentration": "state_top_10_upb",
}


def numeric(row: sqlite3.Row, mode: str) -> float | int | None:
    source = row["value"] if mode in {"value", "cents_value"} else row["numerator"]
    if source in (None, ""):
        return None
    value = float(source)
    if mode in {"cents", "cents_value"}:
        value /= 100
    if mode == "integer":
        return int(value)
    return value


def metadata(connection: sqlite3.Connection) -> dict[str, object]:
    values = dict(connection.execute("SELECT key, value FROM run_metadata"))
    return {
        "pipeline_version": values["pipeline_version"],
        "metric_version": "m5.2.0",
        "catalog_contracts": int(values["catalog_metrics"]),
        "supported_contracts": int(values["implemented_supported_contracts"]),
        "released_components": int(values["released_components"]),
        "security_rows": int(values["security_rows"]),
        "loan_rows": int(values["loan_rows"]),
        "snapshot_sha256": json.loads(values["snapshot_sha256"]),
    }


def series(connection: sqlite3.Connection, correction_view: str) -> list[dict[str, object]]:
    component_names = [component for component, _ in SERIES_COMPONENTS.values()]
    placeholders = ",".join("?" for _ in component_names)
    rows = connection.execute(
        f"""
        SELECT component, report_period, numerator, value
        FROM metric_component
        WHERE released = 1
          AND correction_view = ?
          AND component IN ({placeholders})
          AND report_period GLOB '[0-9][0-9][0-9][0-9]-[0-9][0-9]'
          AND member IN ('All', '30_plus', '60_plus', '90_plus')
        ORDER BY report_period, component
        """,
        [correction_view, *component_names],
    ).fetchall()
    by_component = {component: (field, mode) for field, (component, mode) in SERIES_COMPONENTS.items()}
    periods: dict[str, dict[str, object]] = {}
    for row in rows:
        field, mode = by_component[row["component"]]
        periods.setdefault(row["report_period"], {"month": row["report_period"]})[field] = numeric(row, mode)
    required = set(SERIES_COMPONENTS)
    complete = [row for row in periods.values() if required.issubset(row)]
    if len(complete) < 2:
        raise RuntimeError("the M5 release does not contain two complete portfolio periods")
    return complete


def concentration(connection: sqlite3.Connection, correction_view: str, period: str) -> list[dict[str, object]]:
    component_names = [name for pair in CONCENTRATION_COMPONENTS.values() for name in pair]
    placeholders = ",".join("?" for _ in component_names)
    rows = connection.execute(
        f"""
        SELECT component, numerator, denominator, value
        FROM metric_component
        WHERE released = 1 AND correction_view = ? AND report_period = ?
          AND component IN ({placeholders})
        """,
        [correction_view, period, *component_names],
    ).fetchall()
    values = {row["component"]: row for row in rows}
    result = []
    for entity, (top_component, hhi_component) in CONCENTRATION_COMPONENTS.items():
        top = values[top_component]
        hhi = values[hhi_component]
        result.append(
            {
                "entity": entity,
                "top_10_share": float(top["value"]),
                "hhi": float(hhi["value"]),
                "top_10_upb": float(top["numerator"]) / 100,
                "portfolio_upb": float(top["denominator"]) / 100,
            }
        )
    return result


def source_provenance(connection: sqlite3.Connection, periods: list[str]) -> list[dict[str, object]]:
    placeholders = ",".join("?" for _ in periods)
    rows = connection.execute(
        f"""
        SELECT source_file, report_period, source_family, partition_sha256, scanned_rows
        FROM input_partition
        WHERE report_period IN ({placeholders})
        ORDER BY report_period, source_file
        """,
        periods,
    ).fetchall()
    if not rows:
        raise RuntimeError("evidence has no source-partition provenance")
    return [dict(row) for row in rows]


def evidence(connection: sqlite3.Connection, correction_view: str, period: str) -> dict[str, object]:
    components = list(EVIDENCE_COMPONENTS.values())
    placeholders = ",".join("?" for _ in components)
    rows = connection.execute(
        f"""
        SELECT contract_id, component, report_period, correction_view, grain, dimension,
               member, numerator, denominator, observations, value
        FROM metric_component
        WHERE released = 1 AND correction_view = ? AND report_period = ?
          AND component IN ({placeholders})
        ORDER BY component
        """,
        [correction_view, period, *components],
    ).fetchall()
    by_component = {row["component"]: dict(row) for row in rows}
    if set(components) != set(by_component):
        raise RuntimeError("one or more M8 evidence components are absent")
    provenance = source_provenance(connection, [period])
    metric_evidence = {
        evidence_id: {**by_component[component], "provenance": provenance}
        for evidence_id, component in EVIDENCE_COMPONENTS.items()
    }

    transition_rows = connection.execute(
        """
        SELECT contract_id, component, report_period, correction_view, grain, dimension,
               member, numerator, denominator, observations
        FROM transition_component
        WHERE correction_view = ? AND report_period = ?
          AND component = 'transition_count' AND dimension = 'delinquency_transition'
        ORDER BY member
        """,
        (correction_view, period),
    ).fetchall()
    if not transition_rows:
        raise RuntimeError("M8 transition evidence is absent")
    year, month = map(int, period.split("-"))
    prior_period = f"{year - 1}-12" if month == 1 else f"{year}-{month - 1:02d}"
    return {
        "metrics": metric_evidence,
        "transitions": {
            "period": period,
            "rows": [dict(row) for row in transition_rows],
            "provenance": source_provenance(connection, [prior_period, period]),
        },
    }


def issuance_evidence(release_dir: Path, baseline: dict[str, object]) -> dict[str, object]:
    months = baseline.get("months", [])
    mix = baseline.get("mix", [])
    if len(months) < 2:
        raise RuntimeError("issuance evidence requires at least two periods")
    latest = months[-1]
    peak = max(months, key=lambda row: row["issuance_upb"])
    latest_mix = [row for row in mix if row["month"] == latest["month"]]
    if not latest_mix:
        raise RuntimeError("issuance evidence requires latest-period composition")
    leader = max(latest_mix, key=lambda row: row["issuance_upb"])
    database = release_dir / "issuance.sqlite"
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        manifests = {
            period: dict(connection.execute(
                """
                SELECT source_file, report_period, 'issuance' AS source_family,
                       sha256 AS partition_sha256, input_count AS scanned_rows
                FROM source_manifest WHERE report_period = ? AND quality_status = 'pass'
                """,
                (period,),
            ).fetchone())
            for period in {latest["month"], peak["month"]}
        }
    finally:
        connection.close()

    def item(contract_id: str, component: str, row: dict[str, object], dimension: str, member: str, value: float) -> dict[str, object]:
        return {
            "contract_id": contract_id,
            "component": component,
            "report_period": row["month"],
            "correction_view": "latest",
            "grain": "issuance",
            "dimension": dimension,
            "member": member,
            "numerator": str(value),
            "denominator": None,
            "observations": row["security_count"],
            "value": str(value),
            "provenance": [manifests[row["month"]]],
        }

    return {
        "issuance_change": item("issuance_volume", "issuance_upb", latest, "portfolio", "All", latest["issuance_upb"]),
        "issuance_peak": item("issuance_volume", "issuance_upb", peak, "portfolio", "All", peak["issuance_upb"]),
        "issuance_mix": item("issuance_composition", "group_upb", latest, "product_group", leader["product_group"], leader["issuance_upb"]),
    }

def build_payload(release_dir: Path, baseline_path: Path) -> dict[str, object]:
    database = release_dir / "m5.sqlite"
    if not database.is_file():
        raise FileNotFoundError(f"verified M5 database not found: {database}")
    baseline = json.loads(baseline_path.read_text(encoding="utf-8"))
    connection = sqlite3.connect(f"file:{database}?mode=ro", uri=True)
    connection.row_factory = sqlite3.Row
    try:
        correction_view = "latest"
        portfolio_series = series(connection, correction_view)
        latest_period = portfolio_series[-1]["month"]
        semantic = {
            "schema_version": 1,
            "release_id": release_dir.name,
            "generated_at": datetime.now(UTC).isoformat(),
            "correction_view": correction_view,
            "quality": {
                "status": "pass",
                "detail": "Verified M5 release and full-population reconciliation passed.",
            },
            "comparability": {
                "status": "unavailable",
                "detail": "The comparability contract is not released; adjacent-period deltas are descriptive only.",
            },
            "coverage": {
                "period_start": portfolio_series[0]["month"],
                "period_end": latest_period,
                "period_count": len(portfolio_series),
            },
            "metadata": metadata(connection),
            "series": portfolio_series,
            "concentration": concentration(connection, correction_view, latest_period),
            "evidence": evidence(connection, correction_view, latest_period),
        }
    finally:
        connection.close()
    semantic["evidence"]["metrics"].update(issuance_evidence(release_dir, baseline))
    return {**baseline, "semantic": semantic}


def parse_args() -> argparse.Namespace:
    root = Path(__file__).resolve().parents[1]
    data_root = Path(os.environ.get("MBS_DATA_ROOT", root.parent / f"{root.name}-data"))
    release_id = os.environ.get("MBS_RELEASE_ID", "m5-7-history-20260825")
    parser = argparse.ArgumentParser()
    parser.add_argument("--release-dir", type=Path, default=data_root / "releases" / release_id)
    parser.add_argument("--baseline", type=Path, default=root / "app/data/dashboard.json")
    parser.add_argument("--output", type=Path, default=data_root / "product/dashboard.json")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    payload = build_payload(args.release_dir, args.baseline)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    temporary = args.output.with_suffix(".json.tmp")
    temporary.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    temporary.replace(args.output)
    print(
        f"Product payload: pass ({payload['semantic']['coverage']['period_count']} portfolio periods, "
        f"{payload['semantic']['metadata']['supported_contracts']} supported contracts)"
    )


if __name__ == "__main__":
    main()
