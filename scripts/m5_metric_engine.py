#!/usr/bin/env python3
"""Build restricted M5 metric components from approved conformed facts."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import math
import resource
import shutil
import sqlite3
import sys
from collections import defaultdict
from contextlib import closing
from dataclasses import dataclass, field
from pathlib import Path
from statistics import median
from typing import Any, Iterable

import pipeline

PIPELINE_VERSION = "0.5.0"
TOP_N = 10
MISSING = "Missing"
REQUIRED_LOAN_COLUMNS = {
    "report_period", "prefix", "correction_indicator", "current_upb_cents",
    "remaining_months_to_maturity", "loan_age", "legacy_credit_score",
    "classic_fico", "vs4", "updated_legacy_credit_score",
    "updated_classic_fico", "updated_vs4", "days_delinquent",
    "modification_program", "current_deferred_upb_cents", "property_state",
    "seller_name", "servicer_name", "join_reason",
}
SCORE_COLUMNS = (
    "legacy_credit_score", "classic_fico", "vs4",
    "updated_legacy_credit_score", "updated_classic_fico", "updated_vs4",
)

SCHEMA = """
PRAGMA foreign_keys = ON;
CREATE TABLE IF NOT EXISTS input_partition (
  source_file TEXT PRIMARY KEY,
  report_period TEXT NOT NULL,
  source_family TEXT NOT NULL,
  partition_path TEXT NOT NULL,
  partition_sha256 TEXT NOT NULL,
  expected_rows INTEGER NOT NULL,
  scanned_rows INTEGER NOT NULL,
  all_current_upb_cents TEXT NOT NULL,
  active_rows INTEGER NOT NULL,
  active_current_upb_cents TEXT NOT NULL,
  peak_rss_bytes INTEGER NOT NULL,
  catalog_sha256 TEXT NOT NULL
);
CREATE TABLE IF NOT EXISTS partition_component (
  source_file TEXT NOT NULL,
  contract_id TEXT NOT NULL,
  component TEXT NOT NULL,
  report_period TEXT NOT NULL,
  correction_view TEXT NOT NULL,
  grain TEXT NOT NULL,
  dimension TEXT NOT NULL,
  member TEXT NOT NULL,
  numerator TEXT NOT NULL,
  denominator TEXT,
  observations INTEGER NOT NULL,
  PRIMARY KEY (source_file, contract_id, component, report_period,
               correction_view, grain, dimension, member)
);
CREATE TABLE IF NOT EXISTS metric_component (
  contract_id TEXT NOT NULL,
  component TEXT NOT NULL,
  report_period TEXT NOT NULL,
  correction_view TEXT NOT NULL,
  grain TEXT NOT NULL,
  dimension TEXT NOT NULL,
  member TEXT NOT NULL,
  numerator TEXT NOT NULL,
  denominator TEXT,
  observations INTEGER NOT NULL,
  value TEXT,
  released INTEGER NOT NULL CHECK (released IN (0, 1)),
  PRIMARY KEY (contract_id, component, report_period,
               correction_view, grain, dimension, member)
);
CREATE TABLE IF NOT EXISTS run_metadata (
  key TEXT PRIMARY KEY,
  value TEXT NOT NULL
);
"""


class MetricError(ValueError):
    """Fail-closed M5 metric contract or input error."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as stream:
        for block in iter(lambda: stream.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def catalog_sha256(catalog: dict[str, Any]) -> str:
    encoded = json.dumps(catalog, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def load_catalog(path: Path) -> tuple[dict[str, dict[str, Any]], str]:
    catalog = json.loads(path.read_text(encoding="utf-8"))
    statuses = set(catalog["status_values"])
    required = set(catalog["contract_required_fields"])
    defaults = catalog["contract_defaults"]
    release_modes = catalog["status_release_modes"]
    resolved: dict[str, dict[str, Any]] = {}
    for raw in catalog["metrics"]:
        status = raw.get("status")
        if status not in statuses:
            raise MetricError("metric catalog contains an invalid support status")
        contract = {**defaults, "release_modes": release_modes[status], **raw}
        missing = sorted(required - contract.keys())
        if missing:
            raise MetricError(
                f"metric contract {raw.get('technical_name', '<unknown>')} is incomplete: "
                + ", ".join(missing)
            )
        technical_name = contract["technical_name"]
        if technical_name in resolved:
            raise MetricError("metric catalog contains a duplicate technical name")
        resolved[technical_name] = contract
    return resolved, catalog_sha256(catalog)


def integer(raw: str | None) -> int | None:
    if raw is None or not raw.strip():
        return None
    return int(raw)


def adjacent_month(prior: str, current: str, offset: int = 1) -> bool:
    prior_value = int(prior[:4]) * 12 + int(prior[5:])
    current_value = int(current[:4]) * 12 + int(current[5:])
    return current_value - prior_value == offset


def delinquency_band(days: int | None) -> str:
    if days is None:
        return MISSING
    if days <= 0:
        return "Current"
    if days < 30:
        return "1-29"
    if days < 60:
        return "30-59"
    if days < 90:
        return "60-89"
    return "90+"


def safe_ratio(numerator: int, denominator: int | None) -> str | None:
    if denominator is None or denominator <= 0:
        return None
    return format(numerator / denominator, ".15g")


def smm(unscheduled_principal: int, surviving_balance: int) -> float | None:
    if unscheduled_principal < 0 or surviving_balance <= 0:
        return None
    value = unscheduled_principal / surviving_balance
    return value if 0 <= value <= 1 else None


def cpr(monthly_smm: float | None) -> float | None:
    if monthly_smm is None or not 0 <= monthly_smm <= 1:
        return None
    return 1 - (1 - monthly_smm) ** 12


def ending_balance_residual(
    beginning: int,
    additions: int,
    adjustments: int,
    scheduled: int,
    curtailment: int,
    voluntary: int,
    involuntary: int,
    terminations: int,
    ending: int,
) -> int:
    return (
        beginning + additions + adjustments - scheduled - curtailment
        - voluntary - involuntary - terminations - ending
    )


def hhi(components: Iterable[int]) -> float | None:
    values = list(components)
    total = sum(values)
    if total <= 0 or any(value < 0 for value in values):
        return None
    return math.fsum((value / total) ** 2 for value in values)


def current_rss_bytes() -> int:
    peak = resource.getrusage(resource.RUSAGE_SELF).ru_maxrss
    return int(peak if sys.platform == "darwin" else peak * 1024)


@dataclass
class LoanAggregate:
    report_period: str
    rows: int = 0
    all_current_upb: int = 0
    active_rows: int = 0
    active_upb: int = 0
    corrections: int = 0
    correction_upb: int = 0
    deferred_upb: int = 0
    deferred_denominator_upb: int = 0
    deferred_observations: int = 0
    weighted: dict[str, list[int]] = field(default_factory=dict)
    segments: dict[str, dict[str, list[int]]] = field(
        default_factory=lambda: defaultdict(dict)
    )

    def add_weighted(self, name: str, value: int | None, weight: int) -> None:
        if value is None or value < 0:
            return
        target = self.weighted.setdefault(name, [0, 0, 0])
        target[0] += value * weight
        target[1] += weight
        target[2] += 1

    def add_segment(self, dimension: str, member: str | None, upb: int) -> None:
        label = member.strip() if member and member.strip() else MISSING
        target = self.segments[dimension].setdefault(label, [0, 0])
        target[0] += 1
        target[1] += upb


def component_row(
    contract_id: str,
    component: str,
    report_period: str,
    correction_view: str,
    grain: str,
    dimension: str,
    member: str,
    numerator: int,
    denominator: int | None,
    observations: int,
) -> tuple[Any, ...]:
    return (
        contract_id, component, report_period, correction_view, grain,
        dimension, member, str(numerator),
        None if denominator is None else str(denominator), observations,
    )


def scan_loan_partition(path: Path, expected_period: str) -> LoanAggregate:
    aggregate = LoanAggregate(expected_period)
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        try:
            headers = next(reader)
        except StopIteration as error:
            raise MetricError("loan partition is empty") from error
        missing = sorted(REQUIRED_LOAN_COLUMNS - set(headers))
        if missing:
            raise MetricError("loan partition omits approved conformed columns")
        positions = {name: headers.index(name) for name in REQUIRED_LOAN_COLUMNS}
        for row in reader:
            aggregate.rows += 1
            if len(row) != len(headers):
                raise MetricError("loan partition row width changed")
            if row[positions["report_period"]] != expected_period:
                raise MetricError("loan partition contains an unexpected report period")
            current_upb = integer(row[positions["current_upb_cents"]])
            if current_upb is not None:
                aggregate.all_current_upb += current_upb
            correction = row[positions["correction_indicator"]]
            if correction != "N":
                aggregate.corrections += 1
                aggregate.correction_upb += max(current_upb or 0, 0)
            active = (
                row[positions["join_reason"]] == "matched"
                and correction != "D"
                and current_upb is not None
                and current_upb > 0
            )
            if not active:
                continue
            upb = current_upb
            aggregate.active_rows += 1
            aggregate.active_upb += upb
            aggregate.add_weighted(
                "wala", integer(row[positions["loan_age"]]), upb
            )
            aggregate.add_weighted(
                "wam", integer(row[positions["remaining_months_to_maturity"]]), upb
            )
            for score in SCORE_COLUMNS:
                value = integer(row[positions[score]])
                if value is not None:
                    aggregate.add_weighted(score, value, upb)
                    aggregate.add_segment(f"score:{score}", str(value), upb)
            days = integer(row[positions["days_delinquent"]])
            aggregate.add_segment("delinquency_band", delinquency_band(days), upb)
            aggregate.add_segment("prefix", row[positions["prefix"]], upb)
            aggregate.add_segment("state", row[positions["property_state"]], upb)
            aggregate.add_segment("seller", row[positions["seller_name"]], upb)
            aggregate.add_segment("servicer", row[positions["servicer_name"]], upb)
            modified = bool(row[positions["modification_program"]].strip())
            aggregate.add_segment(
                "modification", "Disclosed program" if modified else "No disclosed program", upb
            )
            deferred = integer(row[positions["current_deferred_upb_cents"]])
            if deferred is not None and deferred >= 0:
                aggregate.deferred_upb += deferred
                aggregate.deferred_denominator_upb += upb
                aggregate.deferred_observations += 1
    return aggregate


def loan_component_rows(aggregate: LoanAggregate) -> list[tuple[Any, ...]]:
    period = aggregate.report_period
    rows = [
        component_row(
            "current_outstanding_balance_population", "loan_upb", period,
            "latest", "loan-period", "portfolio", "All", aggregate.active_upb,
            None, aggregate.active_rows,
        ),
        component_row(
            "current_outstanding_balance_population", "loan_count", period,
            "latest", "loan-period", "portfolio", "All", aggregate.active_rows,
            None, aggregate.active_rows,
        ),
        component_row(
            "loan_balance_distribution", "average_current_loan_balance", period,
            "latest", "loan-period", "portfolio", "All", aggregate.active_upb,
            aggregate.active_rows, aggregate.active_rows,
        ),
        component_row(
            "correction_restatement_volume", "loan_correction_count", period,
            "latest", "loan-period", "portfolio", "All", aggregate.corrections,
            None, aggregate.rows,
        ),
        component_row(
            "correction_restatement_volume", "loan_correction_upb", period,
            "latest", "loan-period", "portfolio", "All", aggregate.correction_upb,
            None, aggregate.corrections,
        ),
        component_row(
            "deferred_upb_share", "deferred_upb", period,
            "latest", "loan-period", "portfolio", "All", aggregate.deferred_upb,
            None, aggregate.deferred_observations,
        ),
        component_row(
            "deferred_upb_share", "deferred_share", period,
            "latest", "loan-period", "portfolio", "All", aggregate.deferred_upb,
            aggregate.deferred_denominator_upb, aggregate.deferred_observations,
        ),
    ]
    for name, (numerator, denominator, observations) in aggregate.weighted.items():
        if name in {"wala", "wam"}:
            contract = "weighted_age_maturity"
        else:
            contract = "credit_score_model_metrics"
        rows.append(component_row(
            contract, name, period, "latest", "loan-period", "portfolio", "All",
            numerator, denominator, observations,
        ))
    segment_contract = {
        "delinquency_band": "delinquency_distribution",
        "prefix": "current_outstanding_balance_population",
        "state": "state_composition",
        "seller": "counterparty_composition",
        "servicer": "counterparty_composition",
        "modification": "modification_volume",
    }
    for dimension, members in aggregate.segments.items():
        contract = (
            "credit_score_model_metrics"
            if dimension.startswith("score:") else segment_contract[dimension]
        )
        for member, (count, upb) in members.items():
            rows.append(component_row(
                contract, f"{dimension}_count", period, "latest", "loan-period",
                dimension, member, count, aggregate.active_rows, count,
            ))
            rows.append(component_row(
                contract, f"{dimension}_upb", period, "latest", "loan-period",
                dimension, member, upb, aggregate.active_upb, count,
            ))
    for score in SCORE_COLUMNS:
        _, eligible_upb, eligible_count = aggregate.weighted.get(score, [0, 0, 0])
        rows.append(component_row(
            "credit_score_model_metrics", f"score:{score}_count", period,
            "latest", "loan-period", f"score:{score}", MISSING,
            aggregate.active_rows - eligible_count, aggregate.active_rows,
            aggregate.active_rows - eligible_count,
        ))
        rows.append(component_row(
            "credit_score_model_metrics", f"score:{score}_upb", period,
            "latest", "loan-period", f"score:{score}", MISSING,
            aggregate.active_upb - eligible_upb, aggregate.active_upb,
            aggregate.active_rows - eligible_count,
        ))
    return rows


def insert_partition(
    connection: sqlite3.Connection,
    source: sqlite3.Row,
    partition_root: Path,
    catalog_hash: str,
) -> None:
    path = partition_root / source["partition_path"]
    if not path.is_file() or sha256_file(path) != source["partition_sha256"]:
        raise MetricError("restricted loan partition is missing or changed")
    aggregate = scan_loan_partition(path, source["report_period"])
    if aggregate.rows != source["partition_row_count"]:
        raise MetricError("loan partition row count does not reconcile")
    connection.execute("DELETE FROM partition_component WHERE source_file=?", (source["source_file"],))
    connection.execute("DELETE FROM input_partition WHERE source_file=?", (source["source_file"],))
    connection.executemany(
        "INSERT INTO partition_component VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        [(source["source_file"], *row) for row in loan_component_rows(aggregate)],
    )
    connection.execute(
        "INSERT INTO input_partition VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
        (
            source["source_file"], source["report_period"], source["source_family"],
            source["partition_path"], source["partition_sha256"],
            source["partition_row_count"], aggregate.rows, str(aggregate.all_current_upb),
            aggregate.active_rows, str(aggregate.active_upb), current_rss_bytes(), catalog_hash,
        ),
    )


def consolidate_partitions(connection: sqlite3.Connection) -> None:
    grouped: dict[tuple[str, ...], list[int | None]] = {}
    for row in connection.execute(
        """
        SELECT contract_id, component, report_period, correction_view, grain,
               dimension, member, numerator, denominator, observations
        FROM partition_component
        ORDER BY contract_id, component, report_period, correction_view,
                 grain, dimension, member
        """
    ):
        key = tuple(row[:7])
        target = grouped.setdefault(key, [0, None, 0])
        target[0] = int(target[0]) + int(row[7])
        if row[8] is not None:
            target[1] = int(target[1] or 0) + int(row[8])
        target[2] = int(target[2]) + int(row[9])
    distribution_dimensions = {
        "delinquency_band", "prefix", "state", "seller", "servicer", "modification"
    }
    distribution_totals: dict[tuple[str, ...], int] = defaultdict(int)
    for key, values in grouped.items():
        if key[5] in distribution_dimensions or key[5].startswith("score:"):
            distribution_totals[key[:6]] += int(values[0])
    for key, values in grouped.items():
        if key[:6] in distribution_totals:
            values[1] = distribution_totals[key[:6]]
    connection.execute("DELETE FROM metric_component")
    connection.executemany(
        "INSERT INTO metric_component VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, 1)",
        [
            (*key, str(values[0]), None if values[1] is None else str(values[1]),
             values[2], safe_ratio(int(values[0]), values[1]))
            for key, values in grouped.items()
        ],
    )


def emit_metric(
    connection: sqlite3.Connection,
    contract: str,
    component: str,
    period: str,
    correction_view: str,
    grain: str,
    dimension: str,
    member: str,
    numerator: int,
    denominator: int | None = None,
    observations: int = 0,
    released: bool = True,
    value: str | None = None,
) -> None:
    connection.execute(
        """
        INSERT INTO metric_component VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(contract_id, component, report_period, correction_view,
                    grain, dimension, member)
        DO UPDATE SET numerator=excluded.numerator, denominator=excluded.denominator,
                      observations=excluded.observations, value=excluded.value,
                      released=excluded.released
        """,
        (
            contract, component, period, correction_view, grain, dimension, member,
            str(numerator), None if denominator is None else str(denominator), observations,
            value if value is not None else safe_ratio(numerator, denominator), int(released),
        ),
    )


def build_trust_metrics(
    output: sqlite3.Connection,
    m4: sqlite3.Connection,
    issuance: sqlite3.Connection,
    security_contract: dict[str, Any],
    loan_contract: dict[str, Any],
) -> None:
    schema_history: dict[str, dict[str, set[str]]] = defaultdict(
        lambda: defaultdict(set)
    )
    for row in m4.execute("SELECT * FROM source_manifest ORDER BY report_period, source_family"):
        schema_history[row["source_family"]][row["report_period"]].add(
            row["schema_version"]
        )
        for component in (
            "input_count", "accepted_count", "excluded_count", "rejected_count",
            "duplicate_count", "quarantined_count", "published_count",
        ):
            emit_metric(
                output, "source_population_accounting", component, row["report_period"],
                "latest", "source", "source_family", row["source_family"],
                int(row[component]), observations=int(row["input_count"]),
            )
            emit_metric(
                output, "source_disposition_rates", component.replace("_count", "_rate"),
                row["report_period"], "latest", "source", "source_family",
                row["source_family"], int(row[component]), int(row["input_count"]),
                int(row["input_count"]),
            )
        emit_metric(
            output, "schema_transition_status", "schema_pass", row["report_period"],
            "latest", "source", "source_family", row["source_family"],
            int(row["quality_status"] == "pass"), 1, 1,
        )
    for family, history in schema_history.items():
        prior_period = None
        prior_versions = None
        for period, versions in sorted(history.items()):
            changed = int(
                prior_period is not None
                and adjacent_month(prior_period, period)
                and versions != prior_versions
            )
            emit_metric(
                output, "schema_transition_status", "schema_transition_flag",
                period, "latest", "source", "source_family", family,
                changed, 1, len(versions),
            )
            prior_period, prior_versions = period, versions
    for row in issuance.execute("SELECT * FROM source_manifest ORDER BY report_period"):
        for component in (
            "input_count", "accepted_count", "excluded_count", "rejected_count",
            "duplicate_count", "quarantined_count", "published_count",
        ):
            emit_metric(
                output, "source_population_accounting", component,
                row["report_period"], "latest", "source", "source_family",
                "issuance", int(row[component]), observations=int(row["input_count"]),
            )
    joins = dict(m4.execute(
        "SELECT join_reason, SUM(row_count) FROM join_reconciliation GROUP BY join_reason"
    ))
    total_joins = sum(joins.values())
    for reason in sorted(joins):
        emit_metric(
            output, "join_coverage", reason, "all", "latest", "loan-period",
            "join_reason", reason, joins[reason], total_joins, joins[reason],
        )
    manifests = list(m4.execute(
        "SELECT report_period, source_family, COUNT(*) received FROM source_manifest GROUP BY 1,2"
    ))
    received = {(row[0], row[1]): row[2] for row in manifests}
    for contract in (security_contract, loan_contract):
        for family in contract["source_families"]:
            periods: set[str] = set()
            for schema in family["schema_versions"]:
                start = schema["period_min"]
                end = schema["period_max"]
                cursor = start
                while cursor <= end:
                    periods.add(cursor)
                    year, month = map(int, cursor.split("-"))
                    month += 1
                    if month == 13:
                        year, month = year + 1, 1
                    cursor = f"{year:04d}-{month:02d}"
            for period in sorted(periods):
                count = received.get((period, family["id"]), 0)
                emit_metric(
                    output, "file_completeness", "required_package", period,
                    "latest", "source", "source_family", family["id"], count, 1, count,
                )


def build_issuance_metrics(output: sqlite3.Connection, issuance: sqlite3.Connection) -> None:
    monthly: dict[str, dict[str, Any]] = defaultdict(
        lambda: {"count": 0, "upb": 0, "values": [], "groups": defaultdict(lambda: [0, 0])}
    )
    for period, prefix, upb in issuance.execute(
        "SELECT report_month, security_type, issuance_upb FROM monthly_security ORDER BY report_month"
    ):
        cents = round(float(upb) * 100)
        target = monthly[period]
        target["count"] += 1
        target["upb"] += cents
        target["values"].append(cents)
        group = pipeline.PREFIX_TAXONOMY.get(prefix, pipeline.UNMAPPED_PRODUCT_GROUP)
        target["groups"][group][0] += 1
        target["groups"][group][1] += cents
    for period, target in sorted(monthly.items()):
        emit_metric(output, "issuance_volume", "issuance_upb", period, "latest", "issuance", "portfolio", "All", target["upb"], observations=target["count"])
        emit_metric(output, "issuance_volume", "issued_security_count", period, "latest", "issuance", "portfolio", "All", target["count"], observations=target["count"])
        emit_metric(output, "security_size_distribution", "average_issuance_security_size", period, "latest", "issuance", "portfolio", "All", target["upb"], target["count"], target["count"])
        emit_metric(output, "security_size_distribution", "median_issuance_security_size", period, "latest", "issuance", "portfolio", "All", round(median(target["values"])), observations=target["count"])
        for group, (count, upb) in target["groups"].items():
            emit_metric(output, "issuance_product_mix", "group_count", period, "latest", "issuance", "product_group", group, count, target["count"], count)
            emit_metric(output, "issuance_product_mix", "group_upb", period, "latest", "issuance", "product_group", group, upb, target["upb"], count)
    periods = sorted(monthly)
    for index, period in enumerate(periods):
        for offset, label in ((1, "mom"), (3, "qoq"), (12, "yoy")):
            if index < offset or not adjacent_month(periods[index - offset], period, offset):
                continue
            prior = monthly[periods[index - offset]]
            current = monthly[period]
            for measure in ("upb", "count"):
                emit_metric(output, "period_change", f"issuance_{measure}_{label}", period, "latest", "issuance", "portfolio", "All", current[measure] - prior[measure], prior[measure], current["count"])
        for window in (3, 6, 12):
            selected = periods[index - window + 1:index + 1]
            if len(selected) != window or any(not adjacent_month(a, b) for a, b in zip(selected, selected[1:])):
                continue
            emit_metric(output, "rolling_issuance", f"rolling_{window}_upb", period, "latest", "issuance", "portfolio", "All", sum(monthly[item]["upb"] for item in selected), observations=sum(monthly[item]["count"] for item in selected))
            emit_metric(output, "rolling_issuance", f"rolling_{window}_count", period, "latest", "issuance", "portfolio", "All", sum(monthly[item]["count"] for item in selected), observations=sum(monthly[item]["count"] for item in selected))


def security_rows(connection: sqlite3.Connection, view: str) -> Iterable[sqlite3.Row]:
    if view not in {"FactSecurityPeriodOriginal", "FactSecurityPeriodLatest"}:
        raise MetricError("invalid security correction view")
    return connection.execute(
        f"""
        SELECT report_period, security_id, prefix, security_status,
               correction_indicator, current_upb_cents, factor_e8,
               legacy_credit_score, classic_fico, vs4,
               involuntary_removal_upb_cents, involuntary_removal_count
        FROM {view}
        ORDER BY security_id, report_period
        """
    )


def build_security_metrics(
    output: sqlite3.Connection,
    m4: sqlite3.Connection,
    view_name: str,
    correction_view: str,
) -> int:
    periods: dict[str, dict[str, Any]] = defaultdict(
        lambda: {
            "rows": 0, "active_count": 0, "active_upb": 0,
            "factor_num": 0, "factor_den": 0, "corrections": 0,
            "correction_upb": 0, "removal_upb": 0, "removal_count": 0,
            "prefix": defaultdict(lambda: [0, 0]),
            "scores": defaultdict(lambda: [0, 0, 0]),
        }
    )
    prior_id = prior_period = None
    prior_factor = prior_upb = None
    prior_active = False
    factor_changes: dict[str, list[int]] = defaultdict(lambda: [0, 0, 0])
    row_count = 0
    for row in security_rows(m4, view_name):
        row_count += 1
        period = row["report_period"]
        target = periods[period]
        target["rows"] += 1
        current_upb = row["current_upb_cents"]
        active = row["security_status"] == "A" and current_upb is not None and current_upb > 0
        if row["correction_indicator"] != "N":
            target["corrections"] += 1
            target["correction_upb"] += max(current_upb or 0, 0)
        target["removal_upb"] += max(row["involuntary_removal_upb_cents"] or 0, 0)
        target["removal_count"] += max(row["involuntary_removal_count"] or 0, 0)
        if active:
            target["active_count"] += 1
            target["active_upb"] += current_upb
            target["prefix"][row["prefix"]][0] += 1
            target["prefix"][row["prefix"]][1] += current_upb
            if row["factor_e8"] is not None:
                target["factor_num"] += current_upb * row["factor_e8"]
                target["factor_den"] += current_upb
            for score in ("legacy_credit_score", "classic_fico", "vs4"):
                if row[score] is not None and row[score] >= 0:
                    values = target["scores"][score]
                    values[0] += current_upb * row[score]
                    values[1] += current_upb
                    values[2] += 1
        if (
            row["security_id"] == prior_id and prior_period is not None
            and adjacent_month(prior_period, period) and prior_active and active
            and prior_factor is not None and row["factor_e8"] is not None
            and prior_upb is not None and prior_upb > 0
        ):
            change = factor_changes[period]
            change[0] += prior_upb * (row["factor_e8"] - prior_factor)
            change[1] += prior_upb
            change[2] += 1
        prior_id, prior_period = row["security_id"], period
        prior_factor, prior_upb, prior_active = row["factor_e8"], current_upb, active
    for period, target in periods.items():
        emit_metric(output, "current_outstanding_balance_population", "security_upb", period, correction_view, "security-period", "portfolio", "All", target["active_upb"], observations=target["active_count"])
        emit_metric(output, "current_outstanding_balance_population", "security_count", period, correction_view, "security-period", "portfolio", "All", target["active_count"], observations=target["active_count"])
        emit_metric(output, "security_size_distribution", "average_current_security_balance", period, correction_view, "security-period", "portfolio", "All", target["active_upb"], target["active_count"], target["active_count"])
        emit_metric(
            output, "factor_level_change", "factor_level", period, correction_view,
            "security-period", "portfolio", "All", target["factor_num"],
            target["factor_den"], target["active_count"],
            value=(
                None if not target["factor_den"]
                else format(target["factor_num"] / target["factor_den"] / 100_000_000, ".15g")
            ),
        )
        emit_metric(output, "correction_restatement_volume", "security_correction_count", period, correction_view, "security-period", "portfolio", "All", target["corrections"], observations=target["rows"])
        emit_metric(output, "correction_restatement_volume", "security_correction_upb", period, correction_view, "security-period", "portfolio", "All", target["correction_upb"], observations=target["corrections"])
        emit_metric(output, "involuntary_removal_volume", "involuntary_removal_count", period, correction_view, "security-period", "portfolio", "All", target["removal_count"], observations=target["rows"])
        emit_metric(output, "involuntary_removal_volume", "involuntary_removal_upb", period, correction_view, "security-period", "portfolio", "All", target["removal_upb"], observations=target["rows"])
        for prefix, (count, upb) in target["prefix"].items():
            emit_metric(output, "current_outstanding_balance_population", "security_prefix_count", period, correction_view, "security-period", "prefix", prefix, count, target["active_count"], count)
            emit_metric(output, "current_outstanding_balance_population", "security_prefix_upb", period, correction_view, "security-period", "prefix", prefix, upb, target["active_upb"], count)
        for score, (numerator, denominator, observations) in target["scores"].items():
            emit_metric(output, "credit_score_model_metrics", f"security_{score}", period, correction_view, "security-period", "score_model", score, numerator, denominator, observations)
    for period, (numerator, denominator, observations) in factor_changes.items():
        emit_metric(
            output, "factor_level_change", "factor_change", period, correction_view,
            "security-period", "portfolio", "All", numerator, denominator,
            observations,
            value=(
                None if not denominator
                else format(numerator / denominator / 100_000_000, ".15g")
            ),
        )
    return row_count


def build_candidate_metrics(connection: sqlite3.Connection) -> None:
    for period, dimension in connection.execute(
        """
        SELECT DISTINCT report_period, dimension FROM metric_component
        WHERE contract_id IN ('state_composition','counterparty_composition')
          AND dimension IN ('state','seller','servicer')
    """
    ):
        for basis in ("count", "upb"):
            values = [
                int(row[0]) for row in connection.execute(
                    """
                    SELECT numerator FROM metric_component
                    WHERE report_period=? AND dimension=?
                      AND contract_id IN ('state_composition','counterparty_composition')
                      AND component=?
                    """,
                    (period, dimension, f"{dimension}_{basis}"),
                )
            ]
            candidate = hhi(values)
            if candidate is not None:
                emit_metric(
                    connection, "hhi_concentration",
                    f"{dimension}_{basis}_hhi", period,
                    "latest", "loan-period", dimension, "All", 0, None,
                    len(values), released=False, value=format(candidate, ".15g"),
                )
    thresholds = {"30_plus": {"30-59", "60-89", "90+"}, "60_plus": {"60-89", "90+"}, "90_plus": {"90+"}}
    periods = [row[0] for row in connection.execute(
        "SELECT DISTINCT report_period FROM metric_component WHERE contract_id='delinquency_distribution'"
    )]
    for period in periods:
        components = {
            (row[0], row[1]): (int(row[2]), int(row[3]) if row[3] is not None else None)
            for row in connection.execute(
                """
                SELECT component, member, numerator, denominator FROM metric_component
                WHERE contract_id='delinquency_distribution' AND report_period=?
                """,
                (period,),
            )
        }
        for label, bands in thresholds.items():
            for basis in ("count", "upb"):
                eligible = sum(value[0] for key, value in components.items() if key[0] == f"delinquency_band_{basis}" and key[1] != MISSING)
                numerator = sum(value[0] for key, value in components.items() if key[0] == f"delinquency_band_{basis}" and key[1] in bands)
                emit_metric(connection, "delinquency_threshold_rates", f"{label}_{basis}", period, "latest", "loan-period", "delinquency_threshold", label, numerator, eligible, observations=eligible, released=False)


def add_top_n_components(connection: sqlite3.Connection) -> None:
    for period, dimension in connection.execute(
        """
        SELECT DISTINCT report_period, dimension FROM metric_component
        WHERE contract_id IN ('state_composition','counterparty_composition')
          AND dimension IN ('state','seller','servicer')
        """
    ):
        for basis in ("count", "upb"):
            rows = [
                (row[0], int(row[1]), int(row[2]) if row[2] is not None else 0)
                for row in connection.execute(
                    """
                    SELECT member, numerator, denominator FROM metric_component
                    WHERE report_period=? AND dimension=? AND component=?
                    ORDER BY CAST(numerator AS INTEGER) DESC, member
                    """,
                    (period, dimension, f"{dimension}_{basis}"),
                )
            ]
            if not rows:
                continue
            total = rows[0][2]
            top = sum(item[1] for item in rows[:TOP_N])
            other = sum(item[1] for item in rows[TOP_N:])
            contract = "state_composition" if dimension == "state" else "counterparty_composition"
            emit_metric(connection, contract, f"{dimension}_top_{TOP_N}_{basis}", period, "latest", "loan-period", f"{dimension}_summary", f"Top {TOP_N}", top, total, len(rows[:TOP_N]))
            emit_metric(connection, contract, f"{dimension}_other_{basis}", period, "latest", "loan-period", f"{dimension}_summary", "Other", other, total, len(rows[TOP_N:]))


def normalized_snapshot(connection: sqlite3.Connection) -> str:
    digest = hashlib.sha256()
    for table, query in (
        ("input_partition", "SELECT source_file, report_period, partition_sha256, expected_rows, scanned_rows, all_current_upb_cents, active_rows, active_current_upb_cents, catalog_sha256 FROM input_partition ORDER BY source_file"),
        ("metric_component", "SELECT contract_id, component, report_period, correction_view, grain, dimension, member, numerator, denominator, observations, value, released FROM metric_component ORDER BY 1,2,3,4,5,6,7"),
    ):
        digest.update(table.encode())
        for row in connection.execute(query):
            digest.update(json.dumps(tuple(row), separators=(",", ":")).encode())
    return digest.hexdigest()


def verify(
    output: sqlite3.Connection,
    m4: sqlite3.Connection,
    catalog: dict[str, dict[str, Any]],
    security_rows_latest: int,
) -> dict[str, Any]:
    expected_partitions, expected_loan_rows = m4.execute(
        "SELECT COUNT(*), COALESCE(SUM(partition_row_count),0) FROM source_manifest WHERE partition_path IS NOT NULL AND quality_status='pass'"
    ).fetchone()
    actual_partitions, scanned_loan_rows = output.execute(
        "SELECT COUNT(*), COALESCE(SUM(scanned_rows),0) FROM input_partition"
    ).fetchone()
    if (actual_partitions, scanned_loan_rows) != (expected_partitions, expected_loan_rows):
        raise MetricError("loan source-to-partition reconciliation failed")
    expected_security = m4.execute(
        "SELECT COUNT(*) FROM FactSecurityPeriodLatest"
    ).fetchone()[0]
    if security_rows_latest != expected_security:
        raise MetricError("security source-to-view reconciliation failed")
    released_contracts = {
        row[0] for row in output.execute(
            "SELECT DISTINCT contract_id FROM metric_component WHERE released=1"
        )
    }
    unknown = released_contracts - catalog.keys()
    unsupported = {
        item for item in released_contracts if catalog[item]["status"] != "supported"
    }
    if unknown or unsupported:
        raise MetricError("metric output released an unknown or gated contract")
    supported = {name for name, contract in catalog.items() if contract["status"] == "supported"}
    implemented = supported & released_contracts
    checksum = normalized_snapshot(output)
    return {
        "catalog_metrics": len(catalog),
        "support_counts": {
            status: sum(contract["status"] == status for contract in catalog.values())
            for status in ("supported", "methodology-gated", "contract-extension-required", "external")
        },
        "implemented_supported_contracts": len(implemented),
        "loan_partitions": actual_partitions,
        "loan_rows": scanned_loan_rows,
        "security_rows": security_rows_latest,
        "metric_components": output.execute("SELECT COUNT(*) FROM metric_component").fetchone()[0],
        "released_components": output.execute("SELECT COUNT(*) FROM metric_component WHERE released=1").fetchone()[0],
        "candidate_components": output.execute("SELECT COUNT(*) FROM metric_component WHERE released=0").fetchone()[0],
        "peak_rss_bytes": output.execute("SELECT COALESCE(MAX(peak_rss_bytes),0) FROM input_partition").fetchone()[0],
        "snapshot_sha256": checksum,
    }


def build(
    m4_database: Path,
    partition_root: Path,
    issuance_database: Path,
    output_database: Path,
    catalog_path: Path,
    security_contract_path: Path,
    loan_contract_path: Path,
    incremental: bool = False,
    only_partitions: set[str] | None = None,
) -> dict[str, Any]:
    catalog, catalog_hash = load_catalog(catalog_path)
    security_contract = json.loads(security_contract_path.read_text(encoding="utf-8"))
    loan_contract = json.loads(loan_contract_path.read_text(encoding="utf-8"))
    if not m4_database.is_file() or not issuance_database.is_file():
        raise MetricError("required conformed database is missing")
    output_database.parent.mkdir(parents=True, exist_ok=True)
    target = output_database.with_suffix(output_database.suffix + ".building")
    target.unlink(missing_ok=True)
    if incremental and output_database.is_file():
        shutil.copy2(output_database, target)
    with (
        closing(sqlite3.connect(m4_database)) as m4,
        closing(sqlite3.connect(issuance_database)) as issuance,
        closing(sqlite3.connect(target)) as output,
    ):
        for connection in (m4, issuance, output):
            connection.row_factory = sqlite3.Row
        output.executescript(SCHEMA)
        sources = list(m4.execute(
            "SELECT * FROM source_manifest WHERE partition_path IS NOT NULL AND quality_status='pass' ORDER BY report_period, source_family, source_file"
        ))
        selected = [row for row in sources if not only_partitions or row["source_file"] in only_partitions]
        existing = {
            row["source_file"]: row
            for row in output.execute("SELECT * FROM input_partition")
        }
        prior_pipeline_row = output.execute(
            "SELECT value FROM run_metadata WHERE key='pipeline_version'"
        ).fetchone()
        reusable_pipeline = (
            prior_pipeline_row is not None and prior_pipeline_row[0] == PIPELINE_VERSION
        )
        if only_partitions and not incremental:
            sources = selected
        for index, source in enumerate(selected, start=1):
            prior = existing.get(source["source_file"])
            unchanged = reusable_pipeline and prior is not None and (
                prior["partition_sha256"] == source["partition_sha256"]
                and prior["expected_rows"] == source["partition_row_count"]
                and prior["catalog_sha256"] == catalog_hash
            )
            if unchanged:
                continue
            insert_partition(output, source, partition_root, catalog_hash)
            output.commit()
            print(
                f"M5 loan partition {index}/{len(selected)}: "
                f"rows={source['partition_row_count']} period={source['report_period']}",
                flush=True,
            )
        if not only_partitions:
            loaded = {row[0] for row in output.execute("SELECT source_file FROM input_partition")}
            expected = {row["source_file"] for row in sources}
            if loaded != expected:
                raise MetricError("output does not contain the complete approved loan partition set")
        consolidate_partitions(output)
        build_trust_metrics(output, m4, issuance, security_contract, loan_contract)
        build_issuance_metrics(output, issuance)
        security_original = build_security_metrics(output, m4, "FactSecurityPeriodOriginal", "original")
        security_latest = build_security_metrics(output, m4, "FactSecurityPeriodLatest", "latest")
        if security_original != security_latest:
            # Different counts are possible only with a versioning defect because both views select one row per key.
            raise MetricError("original/latest security populations differ")
        for period, issuance_upb, ending_upb in output.execute(
            """
            SELECT i.report_period, CAST(i.numerator AS INTEGER), CAST(b.numerator AS INTEGER)
            FROM metric_component i JOIN metric_component b USING(report_period)
            WHERE i.contract_id='issuance_volume' AND i.component='issuance_upb'
              AND b.contract_id='current_outstanding_balance_population'
              AND b.component='security_upb' AND b.correction_view='latest'
              AND b.dimension='portfolio'
            """
        ):
            emit_metric(output, "new_issuance_share_ending_book", "issuance_share", period, "latest", "portfolio", "portfolio", "All", issuance_upb, ending_upb)
        add_top_n_components(output)
        build_candidate_metrics(output)
        summary = verify(output, m4, catalog, security_latest)
        output.execute("DELETE FROM run_metadata")
        output.executemany(
            "INSERT INTO run_metadata VALUES (?, ?)",
            [(key, json.dumps(value, sort_keys=True)) for key, value in summary.items()]
            + [("pipeline_version", PIPELINE_VERSION), ("catalog_sha256", catalog_hash)],
        )
        output.commit()
    target.replace(output_database)
    return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--m4-database", type=Path, default=Path("local/m4-conformed.sqlite"))
    parser.add_argument("--partition-root", type=Path, default=Path("local/m4-conformed"))
    parser.add_argument("--issuance-database", type=Path, default=Path("local/mbs.sqlite"))
    parser.add_argument("--output", type=Path, default=Path("local/m5-metrics.sqlite"))
    parser.add_argument("--catalog", type=Path, default=Path("contracts/m5-metric-catalog.json"))
    parser.add_argument("--security-contract", type=Path, default=Path("contracts/m4-source-contract.json"))
    parser.add_argument("--loan-contract", type=Path, default=Path("contracts/m4-loan-source-contract.json"))
    parser.add_argument("--incremental", action="store_true")
    parser.add_argument("--only-partition", action="append", default=[])
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        summary = build(
            args.m4_database, args.partition_root, args.issuance_database,
            args.output, args.catalog, args.security_contract, args.loan_contract,
            args.incremental, set(args.only_partition) or None,
        )
    except (MetricError, OSError, sqlite3.Error, csv.Error, ValueError) as error:
        print(f"M5 metric engine failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            "M5 metrics: PASS | "
            f"catalog={summary['catalog_metrics']} supported={summary['support_counts']['supported']} "
            f"implemented={summary['implemented_supported_contracts']} "
            f"security={summary['security_rows']} loan={summary['loan_rows']} "
            f"components={summary['metric_components']}"
        )
        print(f"Normalized metric snapshot SHA-256: {summary['snapshot_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
