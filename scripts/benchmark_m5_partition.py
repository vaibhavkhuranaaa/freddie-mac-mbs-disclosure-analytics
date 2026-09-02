#!/usr/bin/env python3
"""Benchmark a compact standard-library M4 loan partition."""

from __future__ import annotations

import argparse
import csv
import gzip
import hashlib
import json
import time
from pathlib import Path
from typing import Any, Iterable


REPEATED_COLUMNS = (
    "report_period",
    "source_family",
    "source_file",
    "schema_version",
    "publication_date",
    "as_of_timestamp",
)
METRIC_COLUMNS = ("current_upb_cents", "correction_indicator", "join_reason")


class BenchmarkError(ValueError):
    """The benchmark input or parity result is invalid."""


def update_digest(digest: Any, values: Iterable[str]) -> None:
    digest.update("\x1f".join(values).encode("utf-8"))
    digest.update(b"\n")


def metrics(positions: dict[str, int], row: list[str], totals: dict[str, int]) -> None:
    totals["rows"] += 1
    raw_upb = row[positions["current_upb_cents"]]
    totals["current_upb_cents"] += int(raw_upb) if raw_upb else 0
    totals["corrections"] += row[positions["correction_indicator"]] != "N"
    totals["matched"] += row[positions["join_reason"]] == "matched"


def scan_baseline(path: Path) -> dict[str, object]:
    started = time.perf_counter()
    digest = hashlib.sha256()
    totals = {"rows": 0, "current_upb_cents": 0, "corrections": 0, "matched": 0}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        headers = next(reader)
        positions = {name: headers.index(name) for name in METRIC_COLUMNS}
        for row in reader:
            if len(row) != len(headers):
                raise BenchmarkError("baseline row width changed")
            update_digest(digest, row)
            metrics(positions, row, totals)
    return {"seconds": time.perf_counter() - started, "sha256": digest.hexdigest(), **totals}


def write_compact(source: Path, output: Path, manifest: Path) -> dict[str, object]:
    started = time.perf_counter()
    output.parent.mkdir(parents=True, exist_ok=True)
    with gzip.open(source, "rt", encoding="utf-8", newline="") as source_stream:
        reader = csv.reader(source_stream)
        headers = next(reader)
        missing = sorted(set((*REPEATED_COLUMNS, *METRIC_COLUMNS)) - set(headers))
        if missing:
            raise BenchmarkError("partition misses required columns: " + ", ".join(missing))
        repeated_positions = {name: headers.index(name) for name in REPEATED_COLUMNS}
        compact_headers = [name for name in headers if name not in REPEATED_COLUMNS]
        compact_positions = [headers.index(name) for name in compact_headers]
        metadata: dict[str, str] | None = None
        rows = 0
        with gzip.open(output, "wt", encoding="utf-8", newline="", compresslevel=1) as output_stream:
            writer = csv.writer(output_stream, lineterminator="\n")
            writer.writerow(compact_headers)
            for row in reader:
                if len(row) != len(headers):
                    raise BenchmarkError("baseline row width changed")
                current = {name: row[position] for name, position in repeated_positions.items()}
                if metadata is None:
                    metadata = current
                elif current != metadata:
                    raise BenchmarkError("source-level values are not partition-constant")
                writer.writerow([row[position] for position in compact_positions])
                rows += 1
    if metadata is None:
        raise BenchmarkError("partition contains no rows")
    payload = {
        "format": "m4-loan-compact-csv-gzip-v1",
        "logical_headers": headers,
        "compact_headers": compact_headers,
        "partition_constants": metadata,
        "rows": rows,
    }
    manifest.write_text(json.dumps(payload, sort_keys=True), encoding="utf-8")
    return {"seconds": time.perf_counter() - started, "rows": rows}


def scan_compact(path: Path, manifest: Path) -> dict[str, object]:
    payload = json.loads(manifest.read_text(encoding="utf-8"))
    logical_headers = payload["logical_headers"]
    constants = payload["partition_constants"]
    started = time.perf_counter()
    digest = hashlib.sha256()
    totals = {"rows": 0, "current_upb_cents": 0, "corrections": 0, "matched": 0}
    positions = {name: logical_headers.index(name) for name in METRIC_COLUMNS}
    with gzip.open(path, "rt", encoding="utf-8", newline="") as stream:
        reader = csv.reader(stream)
        compact_headers = next(reader)
        if compact_headers != payload["compact_headers"]:
            raise BenchmarkError("compact header differs from manifest")
        for compact_row in reader:
            if len(compact_row) != len(compact_headers):
                raise BenchmarkError("compact row width changed")
            values = dict(zip(compact_headers, compact_row))
            values.update(constants)
            row = [values[name] for name in logical_headers]
            update_digest(digest, row)
            metrics(positions, row, totals)
    return {"seconds": time.perf_counter() - started, "sha256": digest.hexdigest(), **totals}


def benchmark(source: Path, output_dir: Path) -> dict[str, object]:
    compact = output_dir / f"{source.name}.compact.gz"
    manifest = output_dir / f"{source.name}.compact.json"
    baseline = scan_baseline(source)
    write = write_compact(source, compact, manifest)
    compact_scan = scan_compact(compact, manifest)
    parity_keys = ("sha256", "rows", "current_upb_cents", "corrections", "matched")
    parity = all(baseline[key] == compact_scan[key] for key in parity_keys)
    savings = 1 - compact.stat().st_size / source.stat().st_size
    slowdown = compact_scan["seconds"] / baseline["seconds"] - 1
    adopted = parity and savings >= 0.20 and slowdown <= 0.10
    return {
        "source_name": source.name,
        "baseline_bytes": source.stat().st_size,
        "compact_bytes": compact.stat().st_size,
        "storage_savings": savings,
        "baseline_scan_seconds": baseline["seconds"],
        "compact_write_seconds": write["seconds"],
        "compact_scan_seconds": compact_scan["seconds"],
        "scan_slowdown": slowdown,
        "row_count": baseline["rows"],
        "normalized_parity": parity,
        "representative_metric_parity": parity,
        "adoption_gate_pass": adopted,
        "decision": "adopt" if adopted else "retain-current-format",
    }


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("sources", nargs="+", type=Path)
    parser.add_argument("--output-dir", required=True, type=Path)
    parser.add_argument("--report", type=Path)
    args = parser.parse_args()
    results = [benchmark(source, args.output_dir) for source in args.sources]
    report = {
        "format": "m5.3-compact-partition-benchmark-v1",
        "results": results,
        "adoption_gate_pass": all(result["adoption_gate_pass"] for result in results),
    }
    encoded = json.dumps(report, indent=2, sort_keys=True)
    if args.report:
        args.report.parent.mkdir(parents=True, exist_ok=True)
        args.report.write_text(encoded + "\n", encoding="utf-8")
    print(encoded)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
