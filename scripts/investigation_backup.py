#!/usr/bin/env python3
"""Back up or restore the investigation SQLite database."""

from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from contextlib import closing
from pathlib import Path


def copy_database(source: Path, target: Path) -> dict[str, object]:
    if not source.is_file():
        raise FileNotFoundError(source)
    target.parent.mkdir(parents=True, exist_ok=True)
    with closing(sqlite3.connect(f"file:{source.resolve()}?mode=ro", uri=True)) as source_db:
        with closing(sqlite3.connect(target)) as target_db, target_db:
            source_db.backup(target_db)
            integrity = target_db.execute("PRAGMA integrity_check").fetchone()[0]
    if integrity != "ok":
        raise RuntimeError(f"backup integrity failed: {integrity}")
    contents = target.read_bytes()
    return {
        "source": str(source),
        "target": str(target),
        "bytes": len(contents),
        "sha256": hashlib.sha256(contents).hexdigest(),
        "integrity": integrity,
    }


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("operation", choices=("backup", "restore"))
    parser.add_argument("--database", type=Path, default=Path("/data/investigations.sqlite"))
    parser.add_argument("--backup", type=Path, default=Path("/data/backups/investigations.sqlite"))
    args = parser.parse_args()
    source, target = (args.database, args.backup) if args.operation == "backup" else (args.backup, args.database)
    print(json.dumps({"operation": args.operation, **copy_database(source, target)}, sort_keys=True))


if __name__ == "__main__":
    main()
