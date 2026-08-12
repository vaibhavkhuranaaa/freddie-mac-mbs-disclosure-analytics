import csv
import hashlib
import io
import json
import sqlite3
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import m4_conformance  # noqa: E402
import source_inventory  # noqa: E402

GOLDEN = json.loads((ROOT / "tests/fixtures/m4/golden_cases.json").read_text())


def connection():
    db = sqlite3.connect(":memory:")
    m4_conformance.register_functions(db)
    db.executescript(m4_conformance.SCHEMA)
    return db


def add_manifest(db, source_file, as_of, family="monthly-security-core-1"):
    published = as_of[:10]
    cursor = db.execute(
        """
        INSERT INTO source_manifest (
          source_file, source_family, member_name, report_period, publication_date,
          as_of_timestamp, archive_sha256, archive_size_bytes, schema_version,
          pipeline_version, input_count, accepted_count, excluded_count,
          rejected_count, duplicate_count, quarantined_count, published_count,
          quality_status
        ) VALUES (?, ?, ?, '2026-01', ?, ?, ?, 1, 'golden', '0.4.0', 1, 1, 0, 0, 0, 0, 1, 'pass')
        """,
        (source_file, family, source_file.replace(".zip", ".txt"), published, as_of, source_file),
    )
    return cursor.lastrowid


def add_security(db, source_id, record_hash, security_id="GSEC01"):
    db.execute(
        """
        INSERT OR IGNORE INTO fact_security_period (
          source_id, source_row, report_period, security_id, prefix,
          security_status, correction_indicator, record_hash
        ) VALUES (?, 2, '2026-01', ?, 'GLD', 'A', 'N', ?)
        """,
        (source_id, security_id, record_hash),
    )


def write_zip(folder, archive_name, member_name, headers, rows):
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter="|", lineterminator="\n")
    writer.writerow(headers)
    writer.writerows(rows)
    with zipfile.ZipFile(Path(folder) / archive_name, "w", zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member_name, stream.getvalue())


def fixture_contract(kind, headers):
    security = kind == "security"
    prefix = "fd" if security else "fu"
    family = "monthly-security-core-1" if security else "monthly-loan-level-1"
    fields = (
        [
            ("prefix", ["Prefix"], "text", False),
            ("security_id", ["Security Identifier"], "text", False),
            ("security_factor_date", ["Security Factor Date"], "date", False),
            ("security_factor", ["Security Factor"], "decimal", True),
            ("security_correction_indicator", ["Security Data Correction Indicator"], "enum", False),
            ("security_status", ["Security Status Indicator"], "enum", False),
            ("issuance_security_upb", ["Issuance Investor Security UPB"], "decimal", True),
            ("current_security_upb", ["Current Investor Security UPB"], "decimal", True),
        ]
        if security
        else [
            ("loan_id", ["Loan Identifier"], "text", False),
            ("loan_correction_indicator", ["Loan Correction Indicator"], "enum", False),
            ("prefix", ["Prefix"], "text", False),
            ("security_id", ["Security Identifier"], "text", False),
            ("mortgage_loan_amount", ["Mortgage Loan Amount"], "decimal", True),
            ("issuance_loan_upb", ["Issuance Investor Loan UPB"], "decimal", True),
            ("current_loan_upb", ["Current Investor Loan UPB"], "decimal", True),
        ]
    )
    return {
        "version": 1,
        "contract_id": f"golden-{kind}",
        "status": "approved",
        "approved_on": "2026-08-10",
        "authorization": "non-sensitive fixture",
        "public_demo_rights": "fixture only",
        "retention": "temporary fixture",
        "native_grain": {kind: "one fixture row"},
        "timing": {"report_period": "publication period"},
        "keys": {"business_key": ["fixture"]},
        "correction_precedence": {"precedence": ["as_of"]},
        "release_modes": {"authorized": "fixture", "reviewer": "fixture"},
        "retention_policy": {"duration_years_from_acquisition": 0},
        "dispositions": ["accepted", "excluded", "rejected", "duplicate", "quarantined", "published-to-conformed"],
        "source_families": [
            {
                "id": family,
                "required": True,
                "archive_pattern": rf"^{prefix}\d{{6}}\.zip$",
                "member_pattern": rf"^{prefix}\d{{6}}\.txt$",
                "has_header": True,
                "record_type_column": None,
                "period_source": "member",
                "period_pattern": rf"^{prefix}(?P<year>\d{{2}})(?P<month>\d{{2}})\d{{2}}\.txt$",
                "schema_versions": [
                    {
                        "version": f"golden-{kind}-v1",
                        "header_sha256": hashlib.sha256("|".join(headers).encode()).hexdigest(),
                        "column_count": len(headers),
                        "record_layouts": None,
                        "period_min": "2026-01",
                        "period_max": "2026-01",
                    }
                ],
            }
        ],
        "join_contract": {
            "grain": "fixture row",
            "effective_period": "2026-01",
            "business_keys": ["fixture"],
            "correction_behavior": "latest wins",
            "unmatched_policy": "reason coded",
        },
        "field_allowlist": [
            {
                "target": target,
                "source_names": names,
                "type": value_type,
                "nullable": nullable,
                "null_tokens": [""] if nullable else [],
                "sensitivity": "restricted",
                "authorized_use": "golden test",
                "reviewer_rule": "fixture only",
            }
            for target, names, value_type, nullable in fields
        ],
        "intended_measures": [{"name": "fixture reconciliation"}],
    }


class M4ConformanceTests(unittest.TestCase):
    def test_repository_contracts_are_approved_and_machine_valid(self):
        security = source_inventory.load_contract(ROOT / "contracts/m4-source-contract.json")
        loan = source_inventory.load_contract(ROOT / "contracts/m4-loan-source-contract.json")
        self.assertEqual(security["status"], "approved")
        self.assertEqual(loan["status"], "approved")
        self.assertEqual(len(security["source_families"]), 4)
        self.assertEqual(len(loan["source_families"]), 2)
        self.assertIn("legacy_credit_score", {field["target"] for field in loan["field_allowlist"]})
        self.assertIn("classic_fico", {field["target"] for field in loan["field_allowlist"]})
        self.assertIn("vs4", {field["target"] for field in loan["field_allowlist"]})

    def test_golden_schema_boundaries_keep_score_models_separate(self):
        cases = {case["id"]: case for case in GOLDEN["schema_cases"]}
        self.assertEqual(cases["security-legacy"]["score_fields"], ["legacy_credit_score"])
        self.assertEqual(cases["security-fico-vs4"]["score_fields"], ["classic_fico", "vs4"])
        self.assertFalse(cases["april-2026-consolidation"]["economic_event"])

    def test_every_join_reason_uses_the_golden_taxonomy(self):
        for case in GOLDEN["join_cases"]:
            actual = m4_conformance.classify_join(
                case["correction"],
                case["security_id"],
                case["security_statuses"],
                case["late"],
            )
            self.assertEqual(actual, case["expected"], case["id"])
        self.assertEqual(
            {case["expected"] for case in GOLDEN["join_cases"]},
            m4_conformance.JOIN_REASONS,
        )

    def test_original_latest_and_as_of_views_preserve_correction_lineage(self):
        db = connection()
        first = add_manifest(db, "gold-original.zip", "2026-01-07T23:59:59Z")
        second = add_manifest(db, "gold-corrected.zip", "2026-01-08T23:59:59Z")
        add_security(db, first, b"original")
        add_security(db, second, b"corrected")
        m4_conformance.refresh_lineage(db)
        original = db.execute("SELECT record_hash FROM FactSecurityPeriodOriginal").fetchone()[0]
        latest = db.execute("SELECT record_hash FROM FactSecurityPeriodLatest").fetchone()[0]
        self.assertEqual(original, b"original")
        self.assertEqual(latest, b"corrected")
        self.assertEqual(
            db.execute("SELECT changed_record FROM restatement_lineage").fetchone()[0], 1
        )
        self.assertNotEqual(
            m4_conformance.normalized_snapshot(db, "2026-01-07T23:59:59Z"),
            m4_conformance.normalized_snapshot(db, "2026-01-08T23:59:59Z"),
        )
        db.close()

    def test_backfill_incremental_parity_and_idempotence(self):
        backfill, incremental = connection(), connection()
        versions = GOLDEN["correction_versions"]
        for db in (backfill, incremental):
            source_ids = [
                add_manifest(db, f"gold-{version['source_version']}.zip", version["as_of"])
                for version in versions
            ]
            for source_id, version in zip(source_ids, versions):
                add_security(db, source_id, version["record_hash"].encode())
        before = m4_conformance.normalized_snapshot(incremental)
        add_security(incremental, 2, b"corrected")
        after = m4_conformance.normalized_snapshot(incremental)
        self.assertEqual(m4_conformance.normalized_snapshot(backfill), before)
        self.assertEqual(before, after)
        backfill.close()
        incremental.close()

    def test_duplicate_and_malformed_rows_fail_closed(self):
        db = connection()
        source_id = add_manifest(db, "gold-duplicate.zip", "2026-01-07T23:59:59Z")
        rows = [
            (source_id, 2, "2026-01", "GSEC01", "GLD", "A", "N", b"one"),
            (source_id, 3, "2026-01", "GSEC01", "GLD", "A", "N", b"two"),
        ]
        accepted, duplicates = m4_conformance.insert_batches(
            db,
            """
            INSERT OR IGNORE INTO fact_security_period (
              source_id, source_row, report_period, security_id, prefix,
              security_status, correction_indicator, record_hash
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            rows,
        )
        self.assertEqual((accepted, duplicates), (1, 1))
        with self.assertRaisesRegex(m4_conformance.ConformanceError, "valid decimal"):
            m4_conformance.parse_scaled(b"malformed", 2, "golden amount")
        db.close()

    def test_small_archive_backfill_and_incremental_paths_match(self):
        security_headers = [
            "Prefix", "Security Identifier", "Security Factor Date", "Security Factor",
            "Security Data Correction Indicator", "Security Status Indicator",
            "Issuance Investor Security UPB", "Current Investor Security UPB",
        ]
        loan_headers = [
            "Loan Identifier", "Loan Correction Indicator", "Prefix", "Security Identifier",
            "Mortgage Loan Amount", "Issuance Investor Loan UPB", "Current Investor Loan UPB",
        ]
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            write_zip(root, "fd260107.zip", "fd260107.txt", security_headers, [["GLD", "GSEC01", "012026", "1", "N", "A", "100", "100"]])
            write_zip(root, "fu260107.zip", "fu260107.txt", loan_headers, [["GLOAN01", "N", "GLD", "GSEC01", "100", "100", "100"]])
            security_path, loan_path = root / "security.json", root / "loan.json"
            security_path.write_text(json.dumps(fixture_contract("security", security_headers)))
            loan_path.write_text(json.dumps(fixture_contract("loan", loan_headers)))
            database, cache = root / "m4.sqlite", root / "inventory.json"
            backfill = m4_conformance.build(root, database, security_path, loan_path, cache)
            incremental = m4_conformance.build(
                root, database, security_path, loan_path, cache, incremental=True
            )
        self.assertEqual(backfill, incremental)
        self.assertEqual(backfill["sources"], 2)
        self.assertEqual(backfill["joins"]["matched"], 1)


if __name__ == "__main__":
    unittest.main()
