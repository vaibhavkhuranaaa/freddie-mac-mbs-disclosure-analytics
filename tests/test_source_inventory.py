import csv
import hashlib
import io
import json
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import source_inventory  # noqa: E402
import storage  # noqa: E402


def header_sha256(headers):
    return hashlib.sha256("|".join(headers).encode("utf-8")).hexdigest()


def write_zip(folder, archive_name, member_name, headers, rows, *, has_header=True):
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter="|", lineterminator="\n")
    if has_header:
        writer.writerow(headers)
    writer.writerows(rows)
    path = Path(folder) / archive_name
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(member_name, stream.getvalue())
    return path


def pending_contract():
    return {
        "version": 1,
        "status": source_inventory.PENDING_STATUS,
        "approved_on": None,
        "authorization": None,
        "public_demo_rights": None,
        "retention": None,
        "source_families": [],
        "join_contract": {
            "grain": None,
            "effective_period": None,
            "business_keys": [],
            "correction_behavior": None,
            "unmatched_policy": None,
        },
        "field_allowlist": [],
        "intended_measures": [],
    }


def approved_contract(headers):
    contract = pending_contract()
    contract.update(
        {
            "contract_id": "fixture-contract",
            "status": source_inventory.APPROVED_STATUS,
            "approved_on": "2026-08-09",
            "authorization": "authorized internal use",
            "public_demo_rights": "aggregates only",
            "retention": "restricted local storage",
            "native_grain": {"fixture": "one row"},
            "timing": {"report_period": "fixture period"},
            "keys": {"business_key": ["fixture_id"]},
            "correction_precedence": {"precedence": ["as_of"]},
            "release_modes": {"authorized": "fixture", "reviewer": "excluded"},
            "retention_policy": {"duration_years_from_acquisition": 7},
            "dispositions": ["accepted", "excluded", "rejected", "duplicate", "quarantined", "published-to-conformed"],
            "source_families": [
                {
                    "id": "monthly-security-core-1",
                    "required": True,
                    "archive_pattern": r"^factor-\d{6}\.zip$",
                    "member_pattern": r"^fd\d{6}\.txt$",
                    "has_header": True,
                    "record_type_column": None,
                    "period_source": "archive",
                    "period_pattern": r"^factor-(?P<year>20\d{2})(?P<month>\d{2})\.zip$",
                    "schema_versions": [
                        {
                            "version": "fixture-v1",
                            "header_sha256": header_sha256(headers),
                            "column_count": len(headers),
                            "record_layouts": None,
                            "period_min": "2026-01",
                            "period_max": None,
                        }
                    ],
                }
            ],
            "join_contract": {
                "grain": "one security per reporting period",
                "effective_period": "member release date",
                "business_keys": ["security_id", "report_period"],
                "correction_behavior": "latest approved correction supersedes original",
                "unmatched_policy": "retain and report reason",
            },
            "field_allowlist": [
                {
                    "target": "security_id",
                    "source_names": ["Security Identifier"],
                    "type": "text",
                    "nullable": False,
                    "null_tokens": [],
                    "sensitivity": "restricted",
                    "authorized_use": "fixture",
                    "reviewer_rule": "excluded",
                }
            ],
            "intended_measures": [{"name": "source reconciliation"}],
        }
    )
    return contract


class SourceInventoryTests(unittest.TestCase):
    def test_pending_contract_blocks_readiness_without_inspecting_row_values(self):
        with tempfile.TemporaryDirectory() as folder:
            write_zip(
                folder,
                "candidate.zip",
                "fd260807.txt",
                ["A", "B"],
                [["secret", "value"]],
            )
            inventory = source_inventory.build_inventory(Path(folder), pending_contract())
            self.assertEqual(inventory["m4_readiness"]["status"], "blocked")
            self.assertEqual(inventory["summary"]["unapproved_candidates"], 1)
            serialized = json.dumps(inventory)
            self.assertNotIn("secret", serialized)
            self.assertNotIn("value", serialized)
            member = inventory["files"][0]["members"][0]
            self.assertEqual(member["physical_row_count"], 1)
            self.assertEqual(member["column_count"], 2)

    def test_archive_outside_configured_families_is_metadata_only(self):
        contract = approved_contract(["Security Identifier", "Security Factor"])
        contract["status"] = source_inventory.PENDING_STATUS
        with tempfile.TemporaryDirectory() as folder:
            write_zip(
                folder,
                "fu260807.zip",
                "fu260807.txt",
                ["Loan Identifier", "Current Investor Loan UPB"],
                [["restricted-loan", "restricted-balance"]],
            )
            inventory = source_inventory.build_inventory(Path(folder), contract)
            self.assertEqual(inventory["summary"]["unrelated"], 1)
            member = inventory["files"][0]["members"][0]
            self.assertNotIn("physical_row_count", member)
            serialized = json.dumps(inventory)
            self.assertNotIn("restricted-loan", serialized)
            self.assertNotIn("restricted-balance", serialized)

    def test_approved_contract_requires_matching_file_member_and_schema(self):
        headers = ["Security Identifier", "Security Factor"]
        with tempfile.TemporaryDirectory() as folder:
            write_zip(
                folder,
                "factor-202607.zip",
                "fd260807.txt",
                headers,
                [["SEC1", "0.9"]],
            )
            inventory = source_inventory.build_inventory(Path(folder), approved_contract(headers))
            self.assertEqual(inventory["m4_readiness"]["status"], "ready")
            self.assertEqual(inventory["summary"]["approved_m4"], 1)
            self.assertEqual(inventory["files"][0]["schema_version"], "fixture-v1")
            self.assertEqual(inventory["files"][0]["report_period"], "2026-07")

    def test_unapproved_schema_keeps_approved_contract_blocked(self):
        headers = ["Security Identifier", "Security Factor"]
        with tempfile.TemporaryDirectory() as folder:
            write_zip(
                folder,
                "factor-202607.zip",
                "fd260807.txt",
                [*headers, "Unexpected"],
                [["SEC1", "0.9", "x"]],
            )
            inventory = source_inventory.build_inventory(Path(folder), approved_contract(headers))
            self.assertEqual(inventory["m4_readiness"]["status"], "blocked")
            self.assertEqual(inventory["summary"]["invalid"], 1)
            self.assertEqual(
                inventory["m4_readiness"]["missing_required_families"],
                ["monthly-security-core-1"],
            )

    def test_headerless_family_counts_first_record_and_validates_column_count(self):
        contract = approved_contract(["unused-a", "unused-b"])
        family = contract["source_families"][0]
        family.update(
            {
                "id": "monthly-security-supplemental-1",
                "archive_pattern": r"^fq\d{6}\.zip$",
                "member_pattern": r"^fq\d{6}\.txt$",
                "has_header": False,
                "record_type_column": 0,
                "period_source": "member",
                "period_pattern": r"^fq(?P<year>\d{2})(?P<month>\d{2})\d{2}\.txt$",
                "schema_versions": [
                    {
                        "version": "headerless-fixture-v1",
                        "header_sha256": None,
                        "column_count": None,
                        "record_layouts": {"1": 2},
                        "period_min": "2026-07",
                        "period_max": "2026-07",
                    }
                ],
            }
        )
        with tempfile.TemporaryDirectory() as folder:
            write_zip(
                folder,
                "fq260707.zip",
                "fq260707.txt",
                ["unused-a", "unused-b"],
                [["1", "value-1"], ["1", "value-2"]],
                has_header=False,
            )
            inventory = source_inventory.build_inventory(Path(folder), contract)
            member = inventory["files"][0]["members"][0]
            self.assertEqual(inventory["m4_readiness"]["status"], "ready")
            self.assertEqual(member["physical_row_count"], 2)
            self.assertIsNone(member["column_count"])
            self.assertFalse(member["has_header"])
            self.assertIsNone(member["header_sha256"])
            self.assertEqual(member["record_layouts"], {"1": 2})
            self.assertEqual(member["record_layout_counts"], {"1": 2})
            serialized = json.dumps(inventory)
            self.assertNotIn("restricted-1", serialized)
            self.assertNotIn("value-2", serialized)

    def test_approved_contract_rejects_missing_governance_fields(self):
        contract = approved_contract(["A"])
        contract["authorization"] = None
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "contract.json"
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(source_inventory.InventoryError, "authorization"):
                source_inventory.load_contract(path)

    def test_repository_approved_contracts_and_raw_inventory_are_ready(self):
        contract = source_inventory.load_contract_bundle(
            [
                ROOT / "contracts/m4-source-contract.json",
                ROOT / "contracts/m4-loan-source-contract.json",
            ]
        )
        inventory = source_inventory.build_inventory(
            storage.raw_path(), contract, storage.manifest_path("source-inventory.json")
        )
        self.assertEqual(inventory["m4_readiness"]["status"], "ready")
        self.assertEqual(inventory["summary"]["governed_issuance"], 19)
        self.assertEqual(inventory["summary"]["approved_m4"], 106)
        self.assertEqual(inventory["summary"]["unapproved_candidates"], 0)
        self.assertEqual(inventory["summary"]["invalid"], 0)

    def test_missing_required_period_is_reported(self):
        headers = ["Security Identifier", "Security Factor"]
        contract = approved_contract(headers)
        schema = contract["source_families"][0]["schema_versions"][0]
        schema["period_min"] = "2026-01"
        schema["period_max"] = "2026-03"
        with tempfile.TemporaryDirectory() as folder:
            write_zip(
                folder,
                "factor-202601.zip",
                "fd260107.txt",
                headers,
                [["GOLD01", "0.9"]],
            )
            inventory = source_inventory.build_inventory(Path(folder), contract)
        self.assertEqual(inventory["m4_readiness"]["status"], "blocked")
        self.assertEqual(
            inventory["m4_readiness"]["missing_required_periods"],
            {"monthly-security-core-1": ["2026-02", "2026-03"]},
        )

    def test_require_ready_exits_two_for_repository_blocker(self):
        with tempfile.TemporaryDirectory() as folder:
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/source_inventory.py",
                    "--input",
                    folder,
                    "--contract",
                    "contracts/m4-source-contract.json",
                    "--require-ready",
                ],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
        self.assertEqual(result.returncode, 2)
        self.assertIn("M4 readiness: BLOCKED", result.stdout)


if __name__ == "__main__":
    unittest.main()
