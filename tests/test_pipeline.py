import csv
import hashlib
import io
import json
import sqlite3
import subprocess
import sys
import tempfile
import unittest
import zipfile
from pathlib import Path
from unittest import mock

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import pipeline  # noqa: E402

RELEASE_DASHBOARD = ROOT / "app/data/dashboard.json"
OFFICIAL_HEADERS = [
    "Prefix",
    "Security Identifier",
    "Issuance Investor Security UPB",
    "Current Investor Security UPB",
    "Security Factor",
    "Security Data Correction Indicator",
]


def schema_for(headers, version="fixture-v1", period_min=None, period_max=None):
    fingerprint = hashlib.sha256("|".join(headers).encode("utf-8")).hexdigest()
    return {
        fingerprint: {
            "version": version,
            "column_count": len(headers),
            "period_min": period_min,
            "period_max": period_max,
        }
    }


def official_row(security_id="SEC-1", issuance="100", current="100", factor="1", prefix="PC"):
    return {
        "Prefix": prefix,
        "Security Identifier": security_id,
        "Issuance Investor Security UPB": issuance,
        "Current Investor Security UPB": current,
        "Security Factor": factor,
        "Security Data Correction Indicator": "false",
    }


def write_official_zip(folder, period, rows, headers=None, extra_member=False):
    headers = headers or OFFICIAL_HEADERS
    archive_path = Path(folder) / f"FRE_IS_{period}.zip"
    stream = io.StringIO()
    writer = csv.DictWriter(stream, fieldnames=headers, delimiter="|", lineterminator="\n")
    writer.writeheader()
    writer.writerows(rows)
    with zipfile.ZipFile(archive_path, "w", compression=zipfile.ZIP_DEFLATED) as archive:
        archive.writestr(f"FRE_IS_{period}.txt", stream.getvalue())
        if extra_member:
            archive.writestr("unexpected.txt", "unexpected")
    return archive_path


class PipelineTests(unittest.TestCase):
    def test_sample_loads_and_publishes_with_quality_metadata(self):
        with tempfile.TemporaryDirectory() as folder:
            database, output = Path(folder) / "mbs.sqlite", Path(folder) / "dashboard.json"
            result = subprocess.run(
                [
                    sys.executable,
                    "scripts/pipeline.py",
                    "--input",
                    "tests/fixtures/issuance-sample",
                    "--database",
                    str(database),
                    "--output",
                    str(output),
                ],
                cwd=ROOT,
                check=True,
                capture_output=True,
                text=True,
            )
            self.assertIn("Loaded 18 accepted records", result.stdout)
            connection = sqlite3.connect(database)
            self.assertEqual(connection.execute("SELECT COUNT(*) FROM monthly_security").fetchone()[0], 18)
            manifest = connection.execute(
                "SELECT input_count, accepted_count, excluded_count, rejected_count, duplicate_count, quality_status FROM source_manifest"
            ).fetchone()
            connection.close()
            self.assertEqual(manifest, (18, 18, 0, 0, 0, "pass"))
            payload = json.loads(output.read_text())
            self.assertEqual(payload["metadata"]["observation_count"], 18)
            self.assertEqual(payload["metadata"]["quality"]["published_count"], 18)
            self.assertEqual(
                payload["metadata"]["mix"]["unmapped_observation_count"], 18
            )
            self.assertEqual(payload["metadata"]["period_start"], "2026-01")
            self.assertEqual(payload["metadata"]["period_end"], "2026-06")
            self.assertEqual(len(payload["months"]), 6)

    def test_official_zip_schema_versions_and_aggregate_accuracy(self):
        with tempfile.TemporaryDirectory() as folder:
            legacy_headers = OFFICIAL_HEADERS
            fico_headers = [*OFFICIAL_HEADERS, "WA Classic FICO"]
            schemas = {
                **schema_for(legacy_headers, "legacy-test", period_max="2025-11"),
                **schema_for(fico_headers, "fico-test", period_min="2025-12"),
            }
            write_official_zip(
                folder,
                "202511",
                [
                    official_row("SEC-1", "100", "90", ".9"),
                    official_row("SEC-2", "150", "140", ".8"),
                ],
                legacy_headers,
            )
            fico_row = official_row("SEC-3", "200", "200", "1")
            fico_row["WA Classic FICO"] = "740"
            write_official_zip(folder, "202512", [fico_row], fico_headers)
            database, output = Path(folder) / "mbs.sqlite", Path(folder) / "dashboard.json"
            with mock.patch.object(pipeline, "OFFICIAL_SCHEMAS", schemas):
                self.assertEqual(pipeline.load(Path(folder), database), 3)
                pipeline.publish(database, output)
            payload = json.loads(output.read_text())
            self.assertEqual(payload["metadata"]["schema_versions"], ["fico-test", "legacy-test"])
            self.assertEqual(payload["metadata"]["quality"]["input_count"], 3)
            self.assertEqual(payload["months"][0]["issuance_upb"], 250)
            self.assertAlmostEqual(payload["months"][0]["average_factor"], 0.85)
            november_mix = [row for row in payload["mix"] if row["month"] == "2025-11"]
            self.assertEqual(sum(row["security_count"] for row in november_mix), 2)

    def test_official_schema_period_mismatch_blocks_publication(self):
        with tempfile.TemporaryDirectory() as folder:
            write_official_zip(folder, "202512", [official_row()])
            database = Path(folder) / "mbs.sqlite"
            schemas = schema_for(OFFICIAL_HEADERS, "legacy-test", period_max="2025-11")
            with mock.patch.object(pipeline, "OFFICIAL_SCHEMAS", schemas):
                with self.assertRaisesRegex(pipeline.QualityGateError, "failed quality checks"):
                    pipeline.load(Path(folder), database)
            connection = sqlite3.connect(database)
            status = connection.execute("SELECT quality_status FROM source_manifest").fetchone()[0]
            detail = connection.execute("SELECT detail FROM quality_issue").fetchone()[0]
            connection.close()
            self.assertEqual(status, "fail")
            self.assertIn("not valid after 2025-11", detail)

    def test_missing_header_is_quarantined(self):
        with tempfile.TemporaryDirectory() as folder:
            headers = [header for header in OFFICIAL_HEADERS if header != "Security Factor"]
            row = official_row()
            row.pop("Security Factor")
            write_official_zip(folder, "202601", [row], headers)
            database = Path(folder) / "mbs.sqlite"
            with self.assertRaises(pipeline.QualityGateError):
                pipeline.load(Path(folder), database)
            connection = sqlite3.connect(database)
            issue = connection.execute("SELECT issue_code, detail FROM quality_issue").fetchone()
            connection.close()
            self.assertEqual(issue[0], "INVALID_SOURCE")
            self.assertIn("missing required official columns", issue[1])

    def test_invalid_value_is_rejected_and_counted(self):
        with tempfile.TemporaryDirectory() as folder:
            write_official_zip(folder, "202601", [official_row(current="101")])
            database = Path(folder) / "mbs.sqlite"
            with mock.patch.object(
                pipeline,
                "OFFICIAL_SCHEMAS",
                schema_for(OFFICIAL_HEADERS, "fico-test", period_min="2025-12"),
            ):
                with self.assertRaises(pipeline.QualityGateError):
                    pipeline.load(Path(folder), database)
            connection = sqlite3.connect(database)
            counts = connection.execute(
                "SELECT input_count, accepted_count, excluded_count, rejected_count, duplicate_count, quarantined_count FROM source_manifest"
            ).fetchone()
            connection.close()
            self.assertEqual(counts, (1, 0, 0, 1, 0, 1))

    def test_cancelled_blank_balance_row_is_documented_exclusion(self):
        with tempfile.TemporaryDirectory() as folder:
            headers = [*OFFICIAL_HEADERS, "Security Status Indicator"]
            active = official_row("SEC-1")
            active["Security Status Indicator"] = "A"
            cancelled = official_row("SEC-2", issuance="", current="", factor="")
            cancelled["Security Status Indicator"] = "C"
            write_official_zip(folder, "202601", [active, cancelled], headers)
            database, output = Path(folder) / "mbs.sqlite", Path(folder) / "dashboard.json"
            with mock.patch.object(
                pipeline,
                "OFFICIAL_SCHEMAS",
                schema_for(headers, "fico-test", period_min="2025-12"),
            ):
                self.assertEqual(pipeline.load(Path(folder), database), 1)
                pipeline.publish(database, output)
            connection = sqlite3.connect(database)
            manifest = connection.execute(
                "SELECT input_count, accepted_count, excluded_count, rejected_count, quality_status FROM source_manifest"
            ).fetchone()
            event = connection.execute(
                "SELECT severity, issue_code FROM quality_issue"
            ).fetchone()
            connection.close()
            self.assertEqual(manifest, (2, 1, 1, 0, "pass"))
            self.assertEqual(event, ("info", "EXCLUDED_CANCELLED_SECURITY"))
            self.assertEqual(json.loads(output.read_text())["metadata"]["quality"]["excluded_count"], 1)

    def test_duplicate_business_key_is_quarantined(self):
        with tempfile.TemporaryDirectory() as folder:
            write_official_zip(folder, "202601", [official_row(), official_row()])
            database = Path(folder) / "mbs.sqlite"
            with mock.patch.object(
                pipeline,
                "OFFICIAL_SCHEMAS",
                schema_for(OFFICIAL_HEADERS, "fico-test", period_min="2025-12"),
            ):
                with self.assertRaises(pipeline.QualityGateError):
                    pipeline.load(Path(folder), database)
            connection = sqlite3.connect(database)
            counts = connection.execute(
                "SELECT input_count, accepted_count, excluded_count, rejected_count, duplicate_count, quarantined_count FROM source_manifest"
            ).fetchone()
            self.assertEqual(counts, (2, 1, 0, 0, 1, 1))
            self.assertEqual(
                connection.execute("SELECT COUNT(*) FROM quality_issue WHERE issue_code = 'DUPLICATE_BUSINESS_KEY'").fetchone()[0],
                1,
            )
            connection.close()

    def test_archive_layout_must_match_source_period(self):
        with tempfile.TemporaryDirectory() as folder:
            write_official_zip(folder, "202601", [official_row()], extra_member=True)
            database = Path(folder) / "mbs.sqlite"
            with self.assertRaises(pipeline.QualityGateError):
                pipeline.load(Path(folder), database)
            connection = sqlite3.connect(database)
            detail = connection.execute("SELECT detail FROM quality_issue").fetchone()[0]
            connection.close()
            self.assertIn("expected only FRE_IS_202601.txt", detail)

    def test_rebuild_is_idempotent_except_generated_timestamp(self):
        with tempfile.TemporaryDirectory() as folder:
            database, first, second = (
                Path(folder) / "mbs.sqlite",
                Path(folder) / "first.json",
                Path(folder) / "second.json",
            )
            pipeline.load(ROOT / "tests/fixtures/issuance-sample", database)
            pipeline.publish(database, first)
            pipeline.load(ROOT / "tests/fixtures/issuance-sample", database)
            pipeline.publish(database, second)
            first_payload = json.loads(first.read_text())
            second_payload = json.loads(second.read_text())
            first_payload["metadata"].pop("generated_at")
            second_payload["metadata"].pop("generated_at")
            self.assertEqual(first_payload, second_payload)

    def test_known_official_fingerprints_define_the_observed_transition(self):
        legacy = pipeline.OFFICIAL_SCHEMAS[
            "d51157584e87d8ea5ace4804b3b429184a0c7e2ae30b6484f4e5c4cc31207f46"
        ]
        fico = pipeline.OFFICIAL_SCHEMAS[
            "03eb8bdeba4ff7726b35058c9cb2e2bb46183131cc66b38e9dd2d9b9e545a541"
        ]
        self.assertEqual(legacy["period_max"], "2025-11")
        self.assertEqual(fico["period_min"], "2025-12")
        self.assertNotEqual(legacy["column_count"], fico["column_count"])

    def test_sample_command_and_dashboard_validation_preserve_released_dashboard(self):
        before = hashlib.sha256(RELEASE_DASHBOARD.read_bytes()).hexdigest()
        sample = subprocess.run(
            ["npm", "run", "load:sample"], cwd=ROOT, check=True, capture_output=True, text=True
        )
        self.assertIn("Loaded 18 accepted records", sample.stdout)
        self.assertTrue((ROOT / "local/sample-dashboard.json").is_file())
        self.assertEqual(before, hashlib.sha256(RELEASE_DASHBOARD.read_bytes()).hexdigest())

        validation = subprocess.run(
            ["npm", "run", "validate:dashboard"], cwd=ROOT, check=True, capture_output=True, text=True
        )
        self.assertIn("Dashboard payload validation: pass", validation.stdout)
        self.assertEqual(before, hashlib.sha256(RELEASE_DASHBOARD.read_bytes()).hexdigest())

    def test_dashboard_validator_rejects_payload_missing_app_field(self):
        with tempfile.TemporaryDirectory() as folder:
            invalid_payload = Path(folder) / "invalid-dashboard.json"
            invalid_payload.write_text(
                json.dumps(
                    {
                        "months": [
                            {"month": "2026-01", "security_count": 1},
                            {"month": "2026-02", "security_count": 1},
                        ],
                        "mix": [{}],
                        "metadata": {"observation_count": 2, "source_file_count": 1},
                    }
                ),
                encoding="utf-8",
            )
            result = subprocess.run(
                ["node", "scripts/validate_dashboard.mjs", str(invalid_payload)],
                cwd=ROOT,
                capture_output=True,
                text=True,
            )
            self.assertNotEqual(result.returncode, 0)
            self.assertIn("Missing or invalid issuance_upb", result.stderr)


if __name__ == "__main__":
    unittest.main()
