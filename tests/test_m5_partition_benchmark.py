import csv
import gzip
import sys
import tempfile
import unittest
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import benchmark_m5_partition  # noqa: E402
import m4_conformance  # noqa: E402


class M5PartitionBenchmarkTests(unittest.TestCase):
    def write_partition(self, path, rows):
        with gzip.open(path, "wt", encoding="utf-8", newline="", compresslevel=1) as stream:
            writer = csv.writer(stream, lineterminator="\n")
            writer.writerow(m4_conformance.LOAN_PARTITION_COLUMNS)
            writer.writerows(rows)

    def row(self, source_file="fu260107.zip"):
        values = {name: "" for name in m4_conformance.LOAN_PARTITION_COLUMNS}
        values.update(
            report_period="2026-01", loan_id="L1", security_id="S1", prefix="CL",
            correction_indicator="N", current_upb_cents="10000", join_reason="matched",
            record_hash_sha256="a" * 64, source_family="monthly-loan-level-1",
            source_file=source_file, source_row="2",
            schema_version="monthly-loan-level-1-fico-vs4-from-2025-12",
            publication_date="2026-01-07", as_of_timestamp="2026-01-07T23:59:59Z",
        )
        return [values[name] for name in m4_conformance.LOAN_PARTITION_COLUMNS]

    def test_compact_partition_preserves_logical_rows_and_metrics(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "fu.csv.gz"
            rows = [self.row(), self.row()]
            rows[1][m4_conformance.LOAN_PARTITION_COLUMNS.index("loan_id")] = "L2"
            rows[1][m4_conformance.LOAN_PARTITION_COLUMNS.index("source_row")] = "3"
            self.write_partition(source, rows)
            result = benchmark_m5_partition.benchmark(source, root / "out")
        self.assertTrue(result["normalized_parity"])
        self.assertTrue(result["representative_metric_parity"])
        self.assertEqual(result["row_count"], 2)

    def test_partition_constants_fail_closed(self):
        with tempfile.TemporaryDirectory() as folder:
            root = Path(folder)
            source = root / "mixed.csv.gz"
            self.write_partition(source, [self.row(), self.row("fu260205.zip")])
            with self.assertRaisesRegex(
                benchmark_m5_partition.BenchmarkError,
                "source-level values are not partition-constant",
            ):
                benchmark_m5_partition.write_compact(
                    source, root / "compact.gz", root / "compact.json"
                )


if __name__ == "__main__":
    unittest.main()
