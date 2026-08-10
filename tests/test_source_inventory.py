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


def header_sha256(headers):
    return hashlib.sha256("|".join(headers).encode("utf-8")).hexdigest()


def write_zip(folder, archive_name, member_name, headers, rows):
    stream = io.StringIO()
    writer = csv.writer(stream, delimiter="|", lineterminator="\n")
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
            "status": source_inventory.APPROVED_STATUS,
            "approved_on": "2026-08-09",
            "authorization": "authorized internal use",
            "public_demo_rights": "aggregates only",
            "retention": "restricted local storage",
            "source_families": [
                {
                    "id": "monthly-security-core-1",
                    "required": True,
                    "archive_pattern": r"^factor-\d{6}\.zip$",
                    "member_pattern": r"^fd\d{6}\.txt$",
                    "period_source": "archive",
                    "period_pattern": r"^factor-(?P<year>20\d{2})(?P<month>\d{2})\.zip$",
                    "schema_versions": [
                        {
                            "version": "fixture-v1",
                            "header_sha256": header_sha256(headers),
                            "column_count": len(headers),
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
            "field_allowlist": ["Security Identifier", "Security Factor"],
            "intended_measures": ["observed factor change"],
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

    def test_approved_contract_rejects_missing_governance_fields(self):
        contract = approved_contract(["A"])
        contract["authorization"] = None
        with tempfile.TemporaryDirectory() as folder:
            path = Path(folder) / "contract.json"
            path.write_text(json.dumps(contract))
            with self.assertRaisesRegex(source_inventory.InventoryError, "authorization"):
                source_inventory.load_contract(path)

    def test_repository_pending_contract_and_raw_inventory_are_fail_closed(self):
        contract = source_inventory.load_contract(ROOT / ".project/m4-source-contract.json")
        inventory = source_inventory.build_inventory(ROOT / "data/raw", contract)
        self.assertEqual(inventory["m4_readiness"]["status"], "blocked")
        self.assertEqual(inventory["summary"]["governed_issuance"], 19)
        self.assertEqual(inventory["summary"]["approved_m4"], 0)

    def test_require_ready_exits_two_for_repository_blocker(self):
        result = subprocess.run(
            [
                sys.executable,
                "scripts/source_inventory.py",
                "--input",
                "data/raw",
                "--contract",
                ".project/m4-source-contract.json",
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
