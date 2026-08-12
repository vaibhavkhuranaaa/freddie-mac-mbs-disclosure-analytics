import csv
import gzip
import json
import sqlite3
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import m4_conformance  # noqa: E402
import m5_metric_engine  # noqa: E402
import pipeline  # noqa: E402

GOLDEN = json.loads((ROOT / "tests/fixtures/m5/golden_cases.json").read_text())


def add_m4_manifest(
    db,
    source_id,
    source_file,
    family,
    period,
    accepted,
    partition=None,
    schema_version="golden",
):
    db.execute(
        """
        INSERT INTO source_manifest (
          source_id, source_file, source_family, member_name, report_period,
          publication_date, as_of_timestamp, archive_sha256, archive_size_bytes,
          schema_version, pipeline_version, input_count, accepted_count,
          excluded_count, rejected_count, duplicate_count, quarantined_count,
          published_count, partition_path, partition_sha256, partition_row_count,
          quality_status
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, 1, ?, '0.4.0', ?, ?, 0, 0, 0, 0, ?, ?, ?, ?, 'pass')
        """,
        (
            source_id,
            source_file,
            family,
            source_file.replace(".zip", ".txt"),
            period,
            f"{period}-07",
            f"{period}-07T23:59:59Z",
            source_file,
            schema_version,
            accepted,
            accepted,
            accepted,
            None if partition is None else partition[0],
            None if partition is None else partition[1],
            None if partition is None else partition[2],
        ),
    )


def loan_row(**overrides):
    values = {
        "report_period": "2026-01",
        "loan_id": "GLOAN01",
        "security_id": "GSEC01",
        "prefix": "GLD",
        "correction_indicator": "N",
        "mortgage_loan_amount_cents": "10000",
        "issuance_upb_cents": "10000",
        "current_upb_cents": "10000",
        "remaining_months_to_maturity": "348",
        "loan_age": "12",
        "legacy_credit_score": "700",
        "classic_fico": "",
        "vs4": "",
        "updated_legacy_credit_score": "",
        "updated_classic_fico": "",
        "updated_vs4": "",
        "days_delinquent": "0",
        "modification_program": "",
        "current_deferred_upb_cents": "0",
        "property_state": "TX",
        "seller_name": "Golden Seller",
        "servicer_name": "Golden Servicer",
        "join_reason": "matched",
        "record_hash_sha256": "golden",
        "source_family": "monthly-loan-level-1",
        "source_file": "fu260107.zip",
        "source_row": "2",
        "schema_version": "golden",
        "publication_date": "2026-01-07",
        "as_of_timestamp": "2026-01-07T23:59:59Z",
    }
    values.update(overrides)
    return [values[column] for column in m4_conformance.LOAN_PARTITION_COLUMNS]


def write_partition(path):
    rows = [
        loan_row(),
        loan_row(
            loan_id="GLOAN02",
            current_upb_cents="20000",
            loan_age="24",
            remaining_months_to_maturity="336",
            legacy_credit_score="",
            classic_fico="750",
            vs4="760",
            days_delinquent="90",
            modification_program="Golden Program",
            current_deferred_upb_cents="1000",
            property_state="CA",
            seller_name="Second Seller",
            servicer_name="Second Servicer",
            source_row="3",
        ),
        loan_row(
            loan_id="GLOAN03",
            current_upb_cents="0",
            days_delinquent="",
            source_row="4",
        ),
        loan_row(
            loan_id="GLOAN04",
            correction_indicator="D",
            current_upb_cents="5000",
            join_reason="terminated",
            source_row="5",
        ),
    ]
    path.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(path, "wt", encoding="utf-8", newline="") as stream:
        writer = csv.writer(stream, lineterminator="\n")
        writer.writerow(m4_conformance.LOAN_PARTITION_COLUMNS)
        writer.writerows(rows)
    return len(rows)


class M5MetricEngineTests(unittest.TestCase):
    def test_catalog_resolves_complete_contracts_and_support_matrix(self):
        catalog, _ = m5_metric_engine.load_catalog(ROOT / "contracts/m5-metric-catalog.json")
        self.assertEqual(len(catalog), GOLDEN["catalog"]["metrics"])
        counts = {
            status: sum(contract["status"] == status for contract in catalog.values())
            for status in GOLDEN["catalog"]["support_counts"]
        }
        self.assertEqual(counts, GOLDEN["catalog"]["support_counts"])
        required = set(json.loads((ROOT / "contracts/m5-metric-catalog.json").read_text())["contract_required_fields"])
        self.assertTrue(all(required <= contract.keys() for contract in catalog.values()))
        self.assertIn("unreleased", catalog["smm"]["release_modes"]["authorized"])
        self.assertIn("absent", catalog["external_market_valuation_metrics"]["release_modes"]["authorized"])

    def test_formula_gates_are_deterministic_and_fail_closed(self):
        for case in GOLDEN["formula_gates"]:
            self.assertEqual(
                m5_metric_engine.smm(case["unscheduled_principal"], case["surviving_balance"]),
                case["expected"],
                case["id"],
            )
        self.assertAlmostEqual(m5_metric_engine.cpr(0.01), 1 - 0.99**12)
        self.assertIsNone(m5_metric_engine.cpr(None))
        bridge = GOLDEN["balance_bridge"]
        self.assertEqual(
            m5_metric_engine.ending_balance_residual(
                bridge["beginning"], bridge["additions"], bridge["adjustments"],
                bridge["scheduled"], bridge["curtailment"], bridge["voluntary"],
                bridge["involuntary"], bridge["terminations"], bridge["ending"],
            ),
            bridge["expected_residual"],
        )
        for case in GOLDEN["hhi"]:
            actual = m5_metric_engine.hhi(case["components"])
            if case["expected"] is None:
                self.assertIsNone(actual, case["id"])
            else:
                self.assertAlmostEqual(actual, case["expected"], msg=case["id"])

    def test_bands_missing_periods_and_score_models_remain_explicit(self):
        for case in GOLDEN["delinquency_bands"]:
            self.assertEqual(m5_metric_engine.delinquency_band(case["days"]), case["expected"])
        self.assertTrue(m5_metric_engine.adjacent_month("2025-11", "2025-12"))
        self.assertFalse(m5_metric_engine.adjacent_month("2025-11", "2026-01"))
        self.assertNotEqual(
            GOLDEN["score_transition"][0]["allowed_nonmissing"],
            GOLDEN["score_transition"][1]["allowed_nonmissing"],
        )
        grain_cases = {case["grain"]: case for case in GOLDEN["grain_cases"]}
        self.assertEqual(
            set(grain_cases), {"security", "loan", "cohort", "vintage", "segment", "portfolio"}
        )
        self.assertTrue(grain_cases["cohort"]["expected_status"].startswith("blocked"))
        self.assertTrue(grain_cases["vintage"]["expected_status"].startswith("blocked"))
        required_cases = {
            "original-latest-correction", "new-issuance", "missing-period",
            "termination", "involuntary-removal", "low-balance",
            "zero-denominator", "schema-transition", "score-model-transition",
            "comparison-ineligible", "formula-gate-failure", "security-grain",
            "loan-grain", "cohort-grain-blocked-by-field-contract",
            "vintage-grain-blocked-by-field-contract", "segment-grain",
            "portfolio-grain",
        }
        self.assertEqual(set(GOLDEN["coverage_cases"]), required_cases)

    def test_streaming_partition_preserves_additive_components(self):
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "golden.csv.gz"
            write_partition(path)
            aggregate = m5_metric_engine.scan_loan_partition(path, "2026-01")
        expected = GOLDEN["engine_expectations"]
        self.assertEqual(aggregate.rows, expected["loan_rows"])
        self.assertEqual(aggregate.active_rows, expected["active_loan_rows"])
        self.assertEqual(aggregate.active_upb, expected["active_loan_upb"])
        self.assertEqual(aggregate.rows - aggregate.active_rows, expected["terminated_or_zero_balance_rows"])
        self.assertEqual(aggregate.weighted["wala"], [600000, 30000, 2])
        self.assertEqual(aggregate.deferred_upb, 1000)
        self.assertEqual(aggregate.deferred_denominator_upb, 30000)
        self.assertEqual(aggregate.segments["delinquency_band"]["90+"], [1, 20000])

    def test_small_backfill_incremental_parity_and_release_safety(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            partition_root = root / "partitions"
            relative = Path("FactLoanPeriod/2026-01/fu260107.zip.csv.gz")
            rows = write_partition(partition_root / relative)
            partition_hash = m5_metric_engine.sha256_file(partition_root / relative)

            m4_path = root / "m4.sqlite"
            with sqlite3.connect(m4_path) as db:
                m4_conformance.register_functions(db)
                db.executescript(m4_conformance.SCHEMA)
                add_m4_manifest(db, 1, "fd260107.zip", "monthly-security-core-1", "2026-01", 2)
                add_m4_manifest(
                    db, 2, "fu260107.zip", "monthly-loan-level-1", "2026-01", rows,
                    (str(relative), partition_hash, rows),
                )
                add_m4_manifest(
                    db, 3, "fd260207.zip", "monthly-security-core-1", "2026-02", 0,
                    schema_version="golden-v2",
                )
                add_m4_manifest(
                    db, 4, "fd260108.zip", "monthly-security-core-1", "2026-01", 1,
                )
                db.executemany(
                    """
                    INSERT INTO fact_security_period (
                      source_id, source_row, report_period, security_id, prefix,
                      security_status, correction_indicator, current_upb_cents,
                      factor_e8, involuntary_removal_upb_cents,
                      involuntary_removal_count, record_hash
                    ) VALUES (?, ?, '2026-01', ?, 'GLD', ?, ?, ?, ?, ?, ?, ?)
                    """,
                    [
                        (1, 2, "GSEC01", "A", "N", 30000, 99000000, 500, 1, b"one"),
                        (1, 3, "GSEC02", "D", "N", 0, 98000000, 0, 0, b"two"),
                        (4, 2, "GSEC01", "A", "C", 29000, 98000000, 700, 2, b"corrected"),
                    ],
                )
                db.executemany(
                    "INSERT INTO join_reconciliation VALUES ('2026-01','monthly-loan-level-1',?,?)",
                    [("matched", 3), ("terminated", 1)],
                )

            issuance_path = root / "issuance.sqlite"
            with sqlite3.connect(issuance_path) as db:
                db.executescript(pipeline.SCHEMA)
                db.execute(
                    """
                    INSERT INTO source_manifest (
                      source_file, report_period, sha256, pipeline_version, schema_version,
                      input_count, accepted_count, excluded_count, rejected_count,
                      duplicate_count, quarantined_count, published_count, quality_status
                    ) VALUES ('gold.zip','2026-01','gold','0.3.0','gold',1,1,0,0,0,0,1,'pass')
                    """
                )
                db.execute(
                    """
                    INSERT INTO monthly_security VALUES (
                      '2026-01','GISS01','CL',100.00,100.00,1.0,0.0,1,1,0,0,
                      'gold.zip',2,'gold'
                    )
                    """
                )

            output = root / "m5.sqlite"
            args = (
                m4_path, partition_root, issuance_path, output,
                ROOT / "contracts/m5-metric-catalog.json",
                ROOT / "contracts/m4-source-contract.json",
                ROOT / "contracts/m4-loan-source-contract.json",
            )
            backfill = m5_metric_engine.build(*args)
            incremental = m5_metric_engine.build(*args, incremental=True)
            self.assertEqual(backfill["snapshot_sha256"], incremental["snapshot_sha256"])
            expected = GOLDEN["engine_expectations"]
            self.assertEqual(backfill["loan_rows"], expected["loan_rows"])
            with sqlite3.connect(output) as db:
                self.assertEqual(
                    db.execute("SELECT COUNT(*) FROM metric_component WHERE released=1 AND contract_id='smm'").fetchone()[0],
                    0,
                )
                self.assertGreater(
                    db.execute("SELECT COUNT(*) FROM metric_component WHERE released=0 AND contract_id='hhi_concentration'").fetchone()[0],
                    0,
                )
                self.assertEqual(
                    float(db.execute(
                        "SELECT value FROM metric_component WHERE contract_id='factor_level_change' AND component='factor_level' AND correction_view='original'"
                    ).fetchone()[0]),
                    expected["original_security_factor"],
                )
                self.assertEqual(
                    float(db.execute(
                        "SELECT value FROM metric_component WHERE contract_id='factor_level_change' AND component='factor_level' AND correction_view='latest'"
                    ).fetchone()[0]),
                    expected["latest_security_factor"],
                )
                self.assertEqual(
                    int(db.execute(
                        "SELECT numerator FROM metric_component WHERE contract_id='issuance_volume' AND component='issuance_upb'"
                    ).fetchone()[0]),
                    expected["issuance_upb"],
                )
                self.assertEqual(
                    int(db.execute(
                        "SELECT numerator FROM metric_component WHERE contract_id='schema_transition_status' AND component='schema_transition_flag' AND report_period='2026-02' AND member='monthly-security-core-1'"
                    ).fetchone()[0]),
                    expected["schema_transition_flag"],
                )
                self.assertEqual(
                    int(db.execute(
                        "SELECT numerator FROM metric_component WHERE contract_id='involuntary_removal_volume' AND component='involuntary_removal_upb' AND correction_view='latest'"
                    ).fetchone()[0]),
                    expected["latest_involuntary_removal_upb"],
                )
                self.assertEqual(
                    int(db.execute(
                        "SELECT numerator FROM metric_component WHERE contract_id='involuntary_removal_volume' AND component='involuntary_removal_count' AND correction_view='latest'"
                    ).fetchone()[0]),
                    expected["latest_involuntary_removal_count"],
                )
                self.assertEqual(
                    {row[0] for row in db.execute(
                        "SELECT component FROM metric_component WHERE contract_id='hhi_concentration'"
                    )},
                    {
                        "state_count_hhi", "state_upb_hhi",
                        "seller_count_hhi", "seller_upb_hhi",
                        "servicer_count_hhi", "servicer_upb_hhi",
                    },
                )
                summaries = list(db.execute(
                    """
                    SELECT dimension,
                           CASE WHEN component LIKE '%_count' THEN 'count' ELSE 'upb' END,
                           SUM(CAST(numerator AS INTEGER)),
                           MAX(CAST(denominator AS INTEGER)), COUNT(*)
                    FROM metric_component
                    WHERE dimension IN ('state_summary','seller_summary','servicer_summary')
                    GROUP BY 1,2
                    """
                ))
                self.assertEqual(len(summaries), 6)
                self.assertTrue(all(total == denominator and rows == 2 for _, _, total, denominator, rows in summaries))


if __name__ == "__main__":
    unittest.main()
