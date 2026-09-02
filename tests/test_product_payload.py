from __future__ import annotations

import json
import sqlite3
import tempfile
import unittest
from pathlib import Path

from scripts.build_product_payload import build_payload


class ProductPayloadTests(unittest.TestCase):
    def test_builds_semantic_payload_without_writing_source_rows(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            release = root / "release-test"
            release.mkdir()
            baseline = root / "baseline.json"
            baseline.write_text(json.dumps({
                "months": [
                    {"month": "2026-01", "security_count": 2, "issuance_upb": 100},
                    {"month": "2026-02", "security_count": 3, "issuance_upb": 120},
                ],
                "mix": [{"month": "2026-02", "product_group": "30-year", "security_count": 3, "issuance_upb": 120, "issuance_share": 1}],
                "metadata": {},
            }), encoding="utf-8")
            issuance = sqlite3.connect(release / "issuance.sqlite")
            issuance.execute(
                "CREATE TABLE source_manifest (source_file TEXT, report_period TEXT, sha256 TEXT, input_count INTEGER, quality_status TEXT)"
            )
            issuance.executemany(
                "INSERT INTO source_manifest VALUES (?, ?, ?, ?, 'pass')",
                [("is-202601.zip", "2026-01", "a" * 64, 2), ("is-202602.zip", "2026-02", "b" * 64, 3)],
            )
            issuance.commit()
            issuance.close()
            connection = sqlite3.connect(release / "m5.sqlite")
            connection.executescript(
                """
                CREATE TABLE run_metadata (key TEXT PRIMARY KEY, value TEXT NOT NULL);
                CREATE TABLE metric_component (
                    contract_id TEXT, component TEXT, report_period TEXT, correction_view TEXT,
                    grain TEXT, dimension TEXT, member TEXT, numerator TEXT, denominator TEXT,
                    observations INTEGER, value TEXT, released INTEGER
                );
                CREATE TABLE input_partition (
                    source_file TEXT PRIMARY KEY, report_period TEXT, source_family TEXT,
                    partition_path TEXT, partition_sha256 TEXT, expected_rows INTEGER,
                    scanned_rows INTEGER, all_current_upb_cents TEXT, active_rows INTEGER,
                    active_current_upb_cents TEXT, peak_rss_bytes INTEGER,
                    catalog_sha256 TEXT, build_fingerprint TEXT
                );
                CREATE TABLE transition_component (
                    contract_id TEXT, component TEXT, report_period TEXT, correction_view TEXT,
                    grain TEXT, dimension TEXT, member TEXT, numerator TEXT, denominator TEXT,
                    observations INTEGER
                );
                """
            )
            run_values = {
                "pipeline_version": "test",
                "catalog_metrics": "54",
                "implemented_supported_contracts": "38",
                "released_components": "16",
                "security_rows": "12",
                "loan_rows": "34",
                "snapshot_sha256": '"abc"',
            }
            connection.executemany("INSERT INTO run_metadata VALUES (?, ?)", run_values.items())
            for period, count in (("2026-01", 10), ("2026-02", 12)):
                for field, (component, mode) in SERIES_COMPONENTS_FOR_TEST.items():
                    numerator = str(count * 100) if "upb" in field or field == "average_loan_balance" else str(count)
                    value = "0.1" if mode == "value" else ("10000" if mode == "cents_value" else None)
                    member = component.removesuffix("_count") if component.startswith(("30_", "60_", "90_")) else "All"
                    connection.execute(
                        "INSERT INTO metric_component VALUES (?, ?, ?, 'latest', 'loan-period', 'portfolio', ?, ?, ?, ?, ?, 1)",
                        ("test", component, period, member, numerator, str(count), count, value),
                    )
                    connection.execute(
                        "INSERT INTO input_partition VALUES (?, ?, 'loan', 'partition', ?, ?, ?, '0', ?, '0', 1, 'catalog', 'build') ON CONFLICT(source_file) DO NOTHING",
                        (f"source-{period}.zip", period, period.replace("-", "") * 4, count, count, count),
                    )
            for entity in ("seller", "servicer", "state"):
                connection.execute(
                    "INSERT INTO metric_component VALUES (?, ?, '2026-02', 'latest', 'loan-period', 'summary', 'Top 10', '600', '1200', 12, '0.5', 1)",
                    ("test", f"{entity}_top_10_upb"),
                )
                connection.execute(
                    "INSERT INTO metric_component VALUES (?, ?, '2026-02', 'latest', 'loan-period', ?, 'All', '0', NULL, 12, '0.04', 1)",
                    ("test", f"{entity}_upb_hhi", entity),
                )
            for component in ("loan_upb", "modification_count_rate", "seller_top_10_upb", "servicer_top_10_upb", "state_top_10_upb"):
                existing = connection.execute(
                    "SELECT 1 FROM metric_component WHERE report_period='2026-02' AND component=?",
                    (component,),
                ).fetchone()
                if not existing:
                    connection.execute(
                        "INSERT INTO metric_component VALUES ('test', ?, '2026-02', 'latest', 'loan-period', 'portfolio', 'All', '50', '100', 12, '0.5', 1)",
                        (component,),
                    )
            connection.execute(
                "INSERT INTO transition_component VALUES ('delinquency_roll_cure', 'transition_count', '2026-02', 'latest', 'loan-cohort', 'delinquency_transition', 'Current to Current', '10', '12', 10)"
            )
            connection.commit()
            connection.close()

            payload = build_payload(release, baseline)
            self.assertEqual(payload["semantic"]["release_id"], "release-test")
            self.assertEqual(payload["semantic"]["series"][-1]["loan_count"], 12)
            self.assertEqual(payload["semantic"]["series"][-1]["average_loan_balance"], 100)
            self.assertEqual(payload["semantic"]["concentration"][0]["top_10_share"], 0.5)
            self.assertEqual(payload["semantic"]["evidence"]["transitions"]["rows"][0]["numerator"], "10")
            self.assertTrue(payload["semantic"]["evidence"]["metrics"]["outstanding_upb"]["provenance"])
            self.assertEqual(payload["semantic"]["evidence"]["metrics"]["issuance_mix"]["member"], "30-year")
            self.assertNotIn("source_rows", payload["semantic"])


SERIES_COMPONENTS_FOR_TEST = {
    "loan_count": ("loan_count", "integer"),
    "loan_upb": ("loan_upb", "cents"),
    "average_loan_balance": ("average_current_loan_balance", "cents_value"),
    "delinquency_30_rate": ("30_plus_count", "value"),
    "delinquency_60_rate": ("60_plus_count", "value"),
    "delinquency_90_rate": ("90_plus_count", "value"),
    "modification_rate": ("modification_count_rate", "value"),
    "correction_count": ("loan_correction_count", "integer"),
}


if __name__ == "__main__":
    unittest.main()
