#!/usr/bin/env python3
"""Verify M5 metric reconciliation without emitting restricted dimension values."""

from __future__ import annotations

import argparse
import json
import sqlite3
import sys
from contextlib import closing
from pathlib import Path

import m5_metric_engine


class VerificationError(ValueError):
    """M5 metric evidence failed."""


def scalar(connection: sqlite3.Connection, query: str, params=()) -> int:
    return int(connection.execute(query, params).fetchone()[0])


def verify(database: Path, m4_database: Path, catalog_path: Path) -> dict:
    catalog, _ = m5_metric_engine.load_catalog(catalog_path)
    with (
        closing(sqlite3.connect(database)) as metrics,
        closing(sqlite3.connect(m4_database)) as m4,
    ):
        metrics.row_factory = sqlite3.Row
        m4.row_factory = sqlite3.Row
        supported = {name for name, item in catalog.items() if item["status"] == "supported"}
        released = {
            row[0] for row in metrics.execute(
                "SELECT DISTINCT contract_id FROM metric_component WHERE released=1"
            )
        }
        if supported != released:
            raise VerificationError("supported metric contracts do not match released contracts")
        expected_partitions, expected_loan_rows = m4.execute(
            "SELECT COUNT(*), SUM(partition_row_count) FROM source_manifest WHERE partition_path IS NOT NULL AND quality_status='pass'"
        ).fetchone()
        actual_partitions, scanned_rows = metrics.execute(
            "SELECT COUNT(*), SUM(scanned_rows) FROM input_partition"
        ).fetchone()
        if (actual_partitions, scanned_rows) != (expected_partitions, expected_loan_rows):
            raise VerificationError("source-to-loan row bridge failed")
        if scalar(metrics, "SELECT COUNT(*) FROM input_partition WHERE expected_rows != scanned_rows"):
            raise VerificationError("a loan partition row bridge failed")

        expected_security = scalar(m4, "SELECT COUNT(*) FROM FactSecurityPeriodLatest")
        security_population_rows = scalar(
            metrics,
            """
            SELECT COUNT(DISTINCT report_period || ':' || correction_view)
            FROM metric_component
            WHERE contract_id='current_outstanding_balance_population'
              AND component='security_count' AND dimension='portfolio'
            """,
        )
        security_periods = scalar(m4, "SELECT COUNT(DISTINCT report_period) FROM FactSecurityPeriodLatest")
        if security_population_rows != security_periods * 2:
            raise VerificationError("original/latest security period coverage failed")

        parity_checks = 0
        for period, correction_view, grain, dimension, component, denominator, component_sum in metrics.execute(
            """
            SELECT report_period, correction_view, grain, dimension, component,
                   MAX(CAST(denominator AS INTEGER)),
                   SUM(CAST(numerator AS INTEGER))
            FROM metric_component
            WHERE released=1
              AND dimension IN ('delinquency_band','prefix','state','seller','servicer','modification')
            GROUP BY report_period, correction_view, grain, dimension, component
            """
        ):
            parity_checks += 1
            if denominator != component_sum:
                raise VerificationError("segment-to-portfolio count or UPB parity failed")

        for period, correction_view, grain, dimension, component, denominator, component_sum in metrics.execute(
            """
            SELECT report_period, correction_view, grain, dimension, component,
                   MAX(CAST(denominator AS INTEGER)),
                   SUM(CAST(numerator AS INTEGER))
            FROM metric_component
            WHERE released=1 AND dimension LIKE 'score:%'
            GROUP BY report_period, correction_view, grain, dimension, component
            """
        ):
            parity_checks += 1
            if denominator != component_sum:
                raise VerificationError("score-model distribution parity failed")

        partition_components = {
            tuple(row[:7]): (int(row[7]), None if row[8] is None else int(row[8]), int(row[9]))
            for row in metrics.execute(
                """
                SELECT contract_id, component, report_period, correction_view,
                       grain, dimension, member,
                       SUM(CAST(numerator AS INTEGER)),
                       CASE WHEN COUNT(denominator)=0 THEN NULL
                            ELSE SUM(CAST(denominator AS INTEGER)) END,
                       SUM(observations)
                FROM partition_component
                GROUP BY 1,2,3,4,5,6,7
                """
            )
        }
        for row in metrics.execute(
            """
            SELECT contract_id, component, report_period, correction_view,
                   grain, dimension, member, numerator, denominator, observations
            FROM metric_component
            WHERE grain='loan-period'
              AND contract_id NOT IN ('hhi_concentration','delinquency_threshold_rates')
              AND dimension NOT LIKE '%_summary'
            """
        ):
            key = tuple(row[:7])
            expected = partition_components.get(key)
            actual = (int(row[7]), None if row[8] is None else int(row[8]), int(row[9]))
            distribution = row[5] in {
                "delinquency_band", "prefix", "state", "seller", "servicer", "modification"
            } or row[5].startswith("score:")
            if expected is not None and (
                (distribution and (actual[0], actual[2]) != (expected[0], expected[2]))
                or (not distribution and actual != expected)
            ):
                raise VerificationError("weighted or additive partition consolidation failed")

        if scalar(
            metrics,
            "SELECT COUNT(*) FROM metric_component WHERE released=1 AND contract_id IN ('smm','cpr','paydown_runoff','delinquency_roll_cure','hhi_concentration')",
        ):
            raise VerificationError("methodology-gated formula was released")
        if scalar(
            metrics,
            "SELECT COUNT(*) FROM metric_component WHERE component LIKE 'rolling_%' AND contract_id='current_outstanding_balance_population'",
        ):
            raise VerificationError("a balance snapshot was summed across time")

        summary = {
            "catalog_metrics": len(catalog),
            "released_contracts": len(released),
            "loan_partitions": actual_partitions,
            "loan_rows": scanned_rows,
            "security_rows": expected_security,
            "segment_weighted_parity_checks": parity_checks,
            "candidate_components": scalar(metrics, "SELECT COUNT(*) FROM metric_component WHERE released=0"),
            "peak_rss_bytes": scalar(metrics, "SELECT MAX(peak_rss_bytes) FROM input_partition"),
            "snapshot_sha256": m5_metric_engine.normalized_snapshot(metrics),
        }
        stored = json.loads(
            metrics.execute("SELECT value FROM run_metadata WHERE key='snapshot_sha256'").fetchone()[0]
        )
        if stored != summary["snapshot_sha256"]:
            raise VerificationError("stored metric snapshot checksum is stale")
        return summary


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--database", type=Path, default=Path("local/m5-metrics.sqlite"))
    parser.add_argument("--m4-database", type=Path, default=Path("local/m4-conformed.sqlite"))
    parser.add_argument("--catalog", type=Path, default=Path(".project/m5-metric-catalog.json"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()
    try:
        summary = verify(args.database, args.m4_database, args.catalog)
    except (VerificationError, m5_metric_engine.MetricError, OSError, sqlite3.Error) as error:
        print(f"M5 metric verification failed: {error}", file=sys.stderr)
        return 2
    if args.json:
        print(json.dumps(summary, sort_keys=True))
    else:
        print(
            "M5 metric verification: PASS | "
            f"catalog={summary['catalog_metrics']} released={summary['released_contracts']} "
            f"security={summary['security_rows']} loan={summary['loan_rows']} "
            f"parity_checks={summary['segment_weighted_parity_checks']}"
        )
        print(f"Normalized metric snapshot SHA-256: {summary['snapshot_sha256']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
