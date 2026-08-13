#!/usr/bin/env python3
"""Verify restricted M4 values and outputs remain outside tracked artifacts."""

from __future__ import annotations

import subprocess
import sys
import zipfile
from pathlib import Path

from storage import raw_path

ROOT = Path(__file__).resolve().parents[1]
RAW = raw_path()
RESTRICTED_TARGETS = {
    "Security Identifier",
    "Loan Identifier",
    "CUSIP",
    "Seller Name",
    "Servicer Name",
}


def tracked_files() -> list[Path]:
    result = subprocess.run(
        ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
    )
    return [ROOT / name.decode() for name in result.stdout.split(b"\0") if name]


def sampled_restricted_tokens(limit_per_archive: int = 25) -> set[bytes]:
    tokens: set[bytes] = set()
    archives = []
    for pattern in ("fd*.zip", "ar*.zip", "fu*.zip", "au*.zip"):
        matches = sorted(RAW.glob(pattern))
        if matches:
            archives.append(matches[0])
    for path in archives:
        with zipfile.ZipFile(path) as archive:
            member = next(item for item in archive.infolist() if not item.is_dir())
            with archive.open(member) as stream:
                headers = stream.readline().decode("utf-8-sig").rstrip("\r\n").split("|")
                positions = [
                    index for index, name in enumerate(headers) if name in RESTRICTED_TARGETS
                ]
                for row_number, raw in enumerate(stream):
                    if row_number >= limit_per_archive:
                        break
                    fields = raw.rstrip(b"\r\n").split(b"|")
                    for position in positions:
                        value = fields[position].strip()
                        if len(value) >= 5:
                            tokens.add(value)
    return tokens


def main() -> int:
    tracked = tracked_files()
    restricted_paths = [
        path for path in tracked
        if (
            path.is_relative_to(ROOT / "data/raw")
            and path.name != ".gitkeep"
        ) or path.is_relative_to(ROOT / "local")
    ]
    if restricted_paths:
        print("Restricted output safety: FAIL | tracked restricted paths found", file=sys.stderr)
        return 1
    if not RAW.is_dir() or not any(RAW.glob("*.zip")):
        print("Restricted output safety: SKIP | local raw inventory absent")
        return 0
    tokens = sampled_restricted_tokens()
    matches = 0
    for path in tracked:
        if not path.is_file():
            continue
        content = path.read_bytes()
        matches += sum(token in content for token in tokens)
    if matches:
        print(
            f"Restricted output safety: FAIL | sampled_tokens={len(tokens)} tracked_matches={matches}",
            file=sys.stderr,
        )
        return 1
    print(
        f"Restricted output safety: PASS | sampled_tokens={len(tokens)} "
        "tracked_matches=0 tracked_restricted_paths=0"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
