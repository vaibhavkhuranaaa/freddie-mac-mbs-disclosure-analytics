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
from storage import current_path


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
        expected_schema_scopes = scalar(
            m4,
            "SELECT COUNT(*) FROM (SELECT DISTINCT report_period, source_family FROM source_manifest)",
        )
        actual_schema_scopes = scalar(
            metrics,
            """
            SELECT COUNT(*) FROM metric_component
            WHERE contract_id='schema_transition_status'
              AND component='schema_transition_flag' AND released=1
            """,
        )
        if actual_schema_scopes != expected_schema_scopes:
            raise VerificationError("schema transition coverage failed")

        parity_checks = 0
        for period, correction_view, grain, dimension, component, denominator, component_sum in metrics.execute(
            """
            SELECT report_period, correction_view, grain, dimension, component,
                   MAX(CAST(denominator AS INTEGER)),
                   SUM(CAST(numerator AS INTEGER))
            FROM metric_component
            WHERE released=1
              AND contract_id IN (
                'delinquency_distribution',
                'current_outstanding_balance_population',
                'state_composition',
                'counterparty_composition',
                'modification_volume'
              )
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

        for period, correction_view, grain, dimension, basis, denominator, component_sum, rows in metrics.execute(
            """
            SELECT report_period, correction_view, grain, dimension,
                   CASE WHEN component LIKE '%_count' THEN 'count' ELSE 'upb' END,
                   MAX(CAST(denominator AS INTEGER)),
                   SUM(CAST(numerator AS INTEGER)), COUNT(*)
            FROM metric_component
            WHERE released=1
              AND dimension IN ('state_summary','seller_summary','servicer_summary')
            GROUP BY 1, 2, 3, 4, 5
            """
        ):
            parity_checks += 1
            if rows != 2 or denominator != component_sum:
                raise VerificationError("top-N and Other summary parity failed")

        hhi_basis_gaps = scalar(
            metrics,
            """
            SELECT COUNT(*) FROM (
              SELECT report_period, dimension,
                     COUNT(DISTINCT CASE
                       WHEN component LIKE '%_count_hhi' THEN 'count'
                       WHEN component LIKE '%_upb_hhi' THEN 'upb'
                     END) AS bases
              FROM metric_component
              WHERE contract_id='hhi_concentration' AND released=1
              GROUP BY report_period, dimension
              HAVING bases != 2
            )
            """,
        )
        if hhi_basis_gaps:
            raise VerificationError("HHI count/UPB derived coverage failed")
        expected_hhi = scalar(
            metrics,
            """
            SELECT COUNT(*) * 2 FROM (
              SELECT DISTINCT report_period, dimension FROM metric_component
              WHERE contract_id IN ('state_composition','counterparty_composition')
                AND dimension IN ('state','seller','servicer')
            )
            """,
        )
        actual_hhi = scalar(
            metrics,
            "SELECT COUNT(*) FROM metric_component WHERE contract_id='hhi_concentration' AND released=1",
        )
        if actual_hhi != expected_hhi:
            raise VerificationError("HHI derived population coverage failed")

        derived_formula_checks = 0
        for period, dimension, component, value in metrics.execute(
            """
            SELECT report_period, dimension, component, value
            FROM metric_component
            WHERE contract_id='hhi_concentration' AND released=1
            """
        ):
            basis = "count" if component.endswith("_count_hhi") else "upb"
            values = [
                int(row[0]) for row in metrics.execute(
                    """
                    SELECT numerator FROM metric_component
                    WHERE released=1 AND report_period=? AND correction_view='latest'
                      AND dimension=? AND component=?
                    """,
                    (period, dimension, f"{dimension}_{basis}"),
                )
            ]
            expected = m5_metric_engine.hhi(values)
            derived_formula_checks += 1
            if expected is None or value is None or abs(float(value) - expected) > 1e-12:
                raise VerificationError("HHI formula reconciliation failed")

        threshold_bands = {
            "30_plus": {"30-59", "60-89", "90+"},
            "60_plus": {"60-89", "90+"},
            "90_plus": {"90+"},
        }
        for period, component, numerator, denominator in metrics.execute(
            """
            SELECT report_period, component, numerator, denominator
            FROM metric_component
            WHERE contract_id='delinquency_threshold_rates' AND released=1
            """
        ):
            label, basis = component.rsplit("_", 1)
            components = {
                row[0]: int(row[1]) for row in metrics.execute(
                    """
                    SELECT member, numerator FROM metric_component
                    WHERE released=1 AND contract_id='delinquency_distribution'
                      AND report_period=? AND correction_view='latest'
                      AND component=?
                    """,
                    (period, f"delinquency_band_{basis}"),
                )
            }
            expected_denominator = sum(
                amount for member, amount in components.items() if member != m5_metric_engine.MISSING
            )
            expected_numerator = sum(
                amount for member, amount in components.items()
                if member in threshold_bands[label]
            )
            derived_formula_checks += 1
            if (int(numerator), int(denominator)) != (
                expected_numerator, expected_denominator
            ):
                raise VerificationError("delinquency threshold reconciliation failed")

        expected_thresholds = scalar(
            metrics,
            "SELECT COUNT(DISTINCT report_period) * 6 FROM metric_component WHERE contract_id='delinquency_distribution'",
        )
        actual_thresholds = scalar(
            metrics,
            "SELECT COUNT(*) FROM metric_component WHERE contract_id='delinquency_threshold_rates' AND released=1",
        )
        if actual_thresholds != expected_thresholds:
            raise VerificationError("delinquency threshold population coverage failed")

        for period, component, numerator, denominator in metrics.execute(
            """
            SELECT report_period, component, numerator, denominator
            FROM metric_component
            WHERE contract_id='modification_rate' AND released=1
            """
        ):
            basis = "count" if component.endswith("_count_rate") else "upb"
            source = metrics.execute(
                """
                SELECT CAST(numerator AS INTEGER), CAST(denominator AS INTEGER)
                FROM metric_component
                WHERE contract_id='modification_volume' AND report_period=?
                  AND component=? AND member='Disclosed program'
                """,
                (period, f"modification_{basis}"),
            ).fetchone()
            expected_numerator = 0 if source is None else source[0]
            expected_denominator = metrics.execute(
                """
                SELECT CAST(numerator AS INTEGER) FROM metric_component
                WHERE contract_id='current_outstanding_balance_population'
                  AND report_period=? AND correction_view='latest'
                  AND dimension='portfolio' AND component=?
                """,
                (period, f"loan_{basis}"),
            ).fetchone()[0]
            derived_formula_checks += 1
            if (int(numerator), int(denominator)) != (
                expected_numerator, expected_denominator
            ):
                raise VerificationError("modification-rate reconciliation failed")
        expected_modification = scalar(
            metrics,
            "SELECT COUNT(DISTINCT report_period) * 2 FROM metric_component WHERE contract_id='current_outstanding_balance_population' AND component='loan_count'",
        )
        actual_modification = scalar(
            metrics,
            "SELECT COUNT(*) FROM metric_component WHERE contract_id='modification_rate' AND released=1",
        )
        if actual_modification != expected_modification:
            raise VerificationError("modification-rate population coverage failed")

        expected_removal_rows = 0
        for correction_view in ("original", "latest"):
            periods = [
                row[0] for row in metrics.execute(
                    """
                    SELECT report_period FROM metric_component
                    WHERE contract_id='current_outstanding_balance_population'
                      AND component='security_count' AND correction_view=?
                    ORDER BY report_period
                    """,
                    (correction_view,),
                )
            ]
            expected_removal_rows += 2 * sum(
                m5_metric_engine.adjacent_month(prior, current)
                for prior, current in zip(periods, periods[1:])
            )
        actual_removal_rows = scalar(
            metrics,
            "SELECT COUNT(*) FROM metric_component WHERE contract_id='involuntary_removal_share' AND released=1",
        )
        if actual_removal_rows != expected_removal_rows:
            raise VerificationError("involuntary-removal-share population coverage failed")
        for period, correction_view, component, numerator, denominator in metrics.execute(
            """
            SELECT report_period, correction_view, component, numerator, denominator
            FROM metric_component
            WHERE contract_id='involuntary_removal_share' AND released=1
            """
        ):
            periods = [
                row[0] for row in metrics.execute(
                    """
                    SELECT report_period FROM metric_component
                    WHERE contract_id='current_outstanding_balance_population'
                      AND component='security_count' AND correction_view=?
                      AND report_period < ? ORDER BY report_period DESC LIMIT 1
                    """,
                    (correction_view, period),
                )
            ]
            if not periods or not m5_metric_engine.adjacent_month(periods[0], period):
                raise VerificationError("involuntary-removal-share interval is not adjacent")
            basis = "count" if component.endswith("_count_share") else "upb"
            expected_numerator = metrics.execute(
                """
                SELECT CAST(numerator AS INTEGER) FROM metric_component
                WHERE contract_id='involuntary_removal_volume' AND report_period=?
                  AND correction_view=? AND component=?
                """,
                (period, correction_view, f"involuntary_removal_{basis}"),
            ).fetchone()[0]
            if basis == "count":
                active_rows, missing_rows, active_loan_count = m4.execute(
                    f"""
                    SELECT COUNT(*),
                           SUM(CASE WHEN loan_count IS NULL THEN 1 ELSE 0 END),
                           COALESCE(SUM(loan_count),0)
                    FROM FactSecurityPeriod{correction_view.title()}
                    WHERE report_period=? AND security_status='A' AND current_upb_cents > 0
                    """,
                    (periods[0],),
                ).fetchone()
                expected_denominator = None if missing_rows else active_loan_count
            else:
                expected_denominator = metrics.execute(
                    """
                    SELECT CAST(numerator AS INTEGER) FROM metric_component
                    WHERE contract_id='current_outstanding_balance_population'
                      AND report_period=? AND correction_view=?
                      AND component='security_upb' AND dimension='portfolio'
                    """,
                    (periods[0], correction_view),
                ).fetchone()[0]
            source_column = (
                "involuntary_removal_count" if basis == "count"
                else "involuntary_removal_upb_cents"
            )
            if scalar(
                m4,
                f"""
                SELECT COUNT(*) FROM FactSecurityPeriod{correction_view.title()}
                WHERE report_period=? AND {source_column} IS NULL
                """,
                (period,),
            ):
                expected_denominator = None
            derived_formula_checks += 1
            actual_denominator = None if denominator is None else int(denominator)
            if (int(numerator), actual_denominator) != (
                expected_numerator, expected_denominator
            ):
                raise VerificationError("involuntary-removal-share reconciliation failed")

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
              AND contract_id NOT IN (
                'hhi_concentration','delinquency_threshold_rates','modification_rate'
              )
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

        placeholders = ",".join("?" for _ in supported)
        if scalar(
            metrics,
            f"SELECT COUNT(*) FROM metric_component WHERE released=0 AND contract_id IN ({placeholders})",
            tuple(sorted(supported)),
        ):
            raise VerificationError("a supported metric component remained unreleased")
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
            "derived_formula_checks": derived_formula_checks,
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
    parser.add_argument("--database", type=Path, default=current_path("m5.sqlite"))
    parser.add_argument("--m4-database", type=Path, default=current_path("m4.sqlite"))
    parser.add_argument("--catalog", type=Path, default=Path("contracts/m5-metric-catalog.json"))
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
