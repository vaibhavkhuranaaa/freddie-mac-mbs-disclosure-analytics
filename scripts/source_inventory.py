#!/usr/bin/env python3
"""Inventory restricted source archives without emitting disclosure row values."""

from __future__ import annotations

import argparse
import csv
import hashlib
import json
import re
import sys
import zipfile
from datetime import datetime
from pathlib import Path
from typing import Any

import pipeline

PENDING_STATUS = "pending-owner-data-and-contract-approval"
APPROVED_STATUS = "approved"
CONTRACT_STATUSES = {PENDING_STATUS, APPROVED_STATUS}


class InventoryError(ValueError):
    """The source inventory or contract is structurally invalid."""


def sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    with path.open("rb") as handle:
        for block in iter(lambda: handle.read(1024 * 1024), b""):
            digest.update(block)
    return digest.hexdigest()


def load_contract(path: Path) -> dict[str, Any]:
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except FileNotFoundError as error:
        raise InventoryError(f"contract not found: {path}") from error
    except json.JSONDecodeError as error:
        raise InventoryError(f"contract is not valid JSON: {error}") from error

    required = {
        "version",
        "status",
        "approved_on",
        "authorization",
        "public_demo_rights",
        "retention",
        "source_families",
        "join_contract",
        "field_allowlist",
        "intended_measures",
    }
    missing = sorted(required - set(contract))
    if missing:
        raise InventoryError(f"contract missing keys: {', '.join(missing)}")
    if contract["version"] != 1:
        raise InventoryError("unsupported contract version")
    if contract["status"] not in CONTRACT_STATUSES:
        raise InventoryError("unsupported contract status")
    if not isinstance(contract["source_families"], list):
        raise InventoryError("source_families must be a list")

    if contract["status"] == APPROVED_STATUS:
        approval_fields = ("approved_on", "authorization", "public_demo_rights", "retention")
        empty = [name for name in approval_fields if not contract[name]]
        if empty:
            raise InventoryError(f"approved contract has empty fields: {', '.join(empty)}")
        if not contract["source_families"]:
            raise InventoryError("approved contract must define at least one source family")
        if not contract["field_allowlist"] or not contract["intended_measures"]:
            raise InventoryError(
                "approved contract must define a field allowlist and intended measures"
            )
        validate_join_contract(contract["join_contract"])

    family_ids = [
        family.get("id")
        for family in contract["source_families"]
        if isinstance(family, dict)
    ]
    if len(family_ids) != len(set(family_ids)):
        raise InventoryError("source family ids must be unique")
    for family in contract["source_families"]:
        validate_family(family)
    return contract


def validate_join_contract(join_contract: Any) -> None:
    if not isinstance(join_contract, dict):
        raise InventoryError("join_contract must be an object")
    required = {
        "grain",
        "effective_period",
        "business_keys",
        "correction_behavior",
        "unmatched_policy",
    }
    missing = sorted(required - set(join_contract))
    if missing:
        raise InventoryError(f"join_contract missing keys: {', '.join(missing)}")
    empty = [
        name
        for name in ("grain", "effective_period", "correction_behavior", "unmatched_policy")
        if not join_contract[name]
    ]
    if empty or not join_contract["business_keys"]:
        names = [*empty, *([] if join_contract["business_keys"] else ["business_keys"])]
        raise InventoryError(f"approved join contract has empty fields: {', '.join(names)}")


def validate_family(family: Any) -> None:
    if not isinstance(family, dict):
        raise InventoryError("each source family must be an object")
    required = {
        "id",
        "required",
        "archive_pattern",
        "member_pattern",
        "period_source",
        "period_pattern",
        "schema_versions",
    }
    missing = sorted(required - set(family))
    if missing:
        raise InventoryError(f"source family missing keys: {', '.join(missing)}")
    if not family["id"] or not isinstance(family["required"], bool):
        raise InventoryError("source family id and boolean required flag are mandatory")
    try:
        re.compile(family["archive_pattern"])
        re.compile(family["member_pattern"])
        period_pattern = re.compile(family["period_pattern"])
    except re.error as error:
        raise InventoryError(f"invalid source-family regex: {error}") from error
    if family["period_source"] not in {"archive", "member"}:
        raise InventoryError("period_source must be archive or member")
    if not {"year", "month"}.issubset(period_pattern.groupindex):
        raise InventoryError("period_pattern must define named year and month groups")
    if not family["schema_versions"]:
        raise InventoryError(f"source family {family['id']} has no schema versions")
    for schema in family["schema_versions"]:
        if set(schema) != {"version", "header_sha256", "column_count", "period_min", "period_max"}:
            raise InventoryError(f"source family {family['id']} has an invalid schema contract")
        if not re.fullmatch(r"[0-9a-f]{64}", schema["header_sha256"]):
            raise InventoryError(f"source family {family['id']} has an invalid header fingerprint")
        if not isinstance(schema["column_count"], int) or schema["column_count"] < 1:
            raise InventoryError(f"source family {family['id']} has an invalid column count")


def extract_report_period(
    item: dict[str, Any], member: dict[str, Any], family: dict[str, Any]
) -> str | None:
    source = item["name"] if family["period_source"] == "archive" else member["name"]
    match = re.fullmatch(family["period_pattern"], source)
    if not match:
        return None
    year = match.group("year")
    if len(year) == 2:
        year = f"20{year}"
    period = f"{year}-{match.group('month')}"
    try:
        datetime.strptime(period, "%Y-%m")
    except ValueError:
        return None
    return period


def inspect_text_member(archive: zipfile.ZipFile, member: zipfile.ZipInfo) -> dict[str, Any]:
    with archive.open(member) as binary:
        header_line = binary.readline().decode("utf-8-sig").rstrip("\r\n")
        headers = next(csv.reader([header_line], delimiter="|"), [])
        row_count = sum(1 for line in binary if line.strip())
    fingerprint = hashlib.sha256("|".join(headers).encode("utf-8")).hexdigest()
    return {
        "name": member.filename,
        "size_bytes": member.file_size,
        "encrypted": bool(member.flag_bits & 0x1),
        "column_count": len(headers),
        "header_sha256": fingerprint,
        "physical_row_count": row_count,
    }


def inspect_zip(path: Path) -> dict[str, Any]:
    result: dict[str, Any] = {
        "name": path.name,
        "size_bytes": path.stat().st_size,
        "sha256": sha256_file(path),
        "kind": "unapproved-candidate",
        "status": "observed",
        "source_family": None,
        "members": [],
        "issues": [],
    }
    try:
        with zipfile.ZipFile(path) as archive:
            members = sorted(
                [member for member in archive.infolist() if not member.is_dir()],
                key=lambda member: member.filename,
            )
            if not members:
                result["issues"].append("archive contains no files")
            for member in members:
                if member.filename.lower().endswith(".txt") and not member.flag_bits & 0x1:
                    result["members"].append(inspect_text_member(archive, member))
                else:
                    if member.flag_bits & 0x1:
                        result["issues"].append(
                            f"encrypted member is not supported: {member.filename}"
                        )
                    result["members"].append(
                        {
                            "name": member.filename,
                            "size_bytes": member.file_size,
                            "encrypted": bool(member.flag_bits & 0x1),
                        }
                    )
    except (OSError, UnicodeDecodeError, zipfile.BadZipFile, RuntimeError) as error:
        result["status"] = "invalid"
        result["issues"].append(f"archive inspection failed: {type(error).__name__}")
    if result["issues"]:
        result["status"] = "invalid"
    return result


def recognize_issuance(item: dict[str, Any]) -> bool:
    match = pipeline.OFFICIAL_ZIP_PATTERN.fullmatch(item["name"])
    if not match or item["status"] != "observed" or len(item["members"]) != 1:
        return False
    expected_member = f"FRE_IS_{match.group(1)}{match.group(2)}.txt"
    member = item["members"][0]
    schema = pipeline.OFFICIAL_SCHEMAS.get(member.get("header_sha256"))
    if member.get("name") != expected_member or not schema:
        return False
    report_period = f"{match.group(1)}-{match.group(2)}"
    if schema["period_min"] and report_period < schema["period_min"]:
        return False
    if schema["period_max"] and report_period > schema["period_max"]:
        return False
    item["kind"] = "governed-issuance"
    item["source_family"] = "fre-is"
    item["schema_version"] = schema["version"]
    item["report_period"] = report_period
    return True


def match_family(item: dict[str, Any], family: dict[str, Any]) -> bool:
    if not re.fullmatch(family["archive_pattern"], item["name"]):
        return False
    candidates = [
        member
        for member in item["members"]
        if re.fullmatch(family["member_pattern"], member["name"])
    ]
    if len(candidates) != 1:
        item["issues"].append(
            f"{family['id']} expected exactly one matching member; found {len(candidates)}"
        )
        return False
    member = candidates[0]
    schemas = {
        schema["header_sha256"]: schema for schema in family["schema_versions"]
    }
    schema = schemas.get(member.get("header_sha256"))
    if not schema or member.get("column_count") != schema["column_count"]:
        item["issues"].append(f"{family['id']} has an unapproved schema fingerprint")
        return False
    report_period = extract_report_period(item, member, family)
    if not report_period:
        item["issues"].append(f"{family['id']} report period cannot be derived")
        return False
    if schema["period_min"] and report_period < schema["period_min"]:
        item["issues"].append(f"{family['id']} schema is not valid before {schema['period_min']}")
        return False
    if schema["period_max"] and report_period > schema["period_max"]:
        item["issues"].append(f"{family['id']} schema is not valid after {schema['period_max']}")
        return False
    item["kind"] = "approved-m4"
    item["source_family"] = family["id"]
    item["schema_version"] = schema["version"]
    item["report_period"] = report_period
    return True


def build_inventory(input_dir: Path, contract: dict[str, Any]) -> dict[str, Any]:
    if not input_dir.is_dir():
        raise InventoryError(f"input directory not found: {input_dir}")
    files = []
    for path in sorted(input_dir.iterdir()):
        if not path.is_file() or path.name == ".gitkeep":
            continue
        if path.suffix.lower() != ".zip":
            files.append(
                {
                    "name": path.name,
                    "size_bytes": path.stat().st_size,
                    "sha256": sha256_file(path),
                    "kind": "unrelated-file",
                    "status": "observed",
                    "source_family": None,
                    "members": [],
                    "issues": ["only ZIP archives are eligible source packages"],
                }
            )
            continue
        item = inspect_zip(path)
        issuance_named = bool(pipeline.OFFICIAL_ZIP_PATTERN.fullmatch(item["name"]))
        issuance_recognized = recognize_issuance(item)
        if issuance_named and not issuance_recognized:
            item["issues"].append(
                "issuance-shaped archive failed the governed member, schema, or period contract"
            )
            item["status"] = "invalid"
        if not issuance_recognized and contract["status"] == APPROVED_STATUS:
            matched = any(
                match_family(item, family) for family in contract["source_families"]
            )
            if not matched and item["issues"]:
                item["status"] = "invalid"
        files.append(item)

    counts = {
        "governed_issuance": sum(item["kind"] == "governed-issuance" for item in files),
        "approved_m4": sum(item["kind"] == "approved-m4" for item in files),
        "unapproved_candidates": sum(item["kind"] == "unapproved-candidate" for item in files),
        "unrelated": sum(item["kind"] == "unrelated-file" for item in files),
        "invalid": sum(item["status"] == "invalid" for item in files),
    }
    matched_families = {
        item["source_family"] for item in files if item["kind"] == "approved-m4"
    }
    missing_families = [
        family["id"]
        for family in contract["source_families"]
        if family["required"] and family["id"] not in matched_families
    ]
    blockers = []
    if contract["status"] != APPROVED_STATUS:
        blockers.append("M4 source contract is not approved")
    if missing_families:
        blockers.append(f"missing required source families: {', '.join(missing_families)}")
    if counts["invalid"]:
        blockers.append(
            f"{counts['invalid']} source package(s) failed inspection or contract matching"
        )
    readiness = "ready" if not blockers else "blocked"
    return {
        "contract_version": contract["version"],
        "contract_status": contract["status"],
        "input_directory": str(input_dir),
        "summary": counts,
        "m4_readiness": {
            "status": readiness,
            "missing_required_families": missing_families,
            "blockers": blockers,
        },
        "files": files,
    }


def text_summary(inventory: dict[str, Any]) -> str:
    summary = inventory["summary"]
    readiness = inventory["m4_readiness"]
    lines = [
        f"M4 readiness: {readiness['status'].upper()}",
        f"Contract: {inventory['contract_status']}",
        (
            "Inventory: "
            f"{summary['governed_issuance']} governed issuance, "
            f"{summary['approved_m4']} approved M4, "
            f"{summary['unapproved_candidates']} unapproved candidate, "
            f"{summary['unrelated']} unrelated, {summary['invalid']} invalid"
        ),
    ]
    lines.extend(f"Blocker: {blocker}" for blocker in readiness["blockers"])
    return "\n".join(lines)


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--input", type=Path, default=Path("data/raw"))
    parser.add_argument(
        "--contract", type=Path, default=Path(".project/m4-source-contract.json")
    )
    parser.add_argument("--json", action="store_true", help="emit the complete safe inventory")
    parser.add_argument(
        "--require-ready",
        action="store_true",
        help="exit 2 unless the approved M4 source contract and required files pass",
    )
    args = parser.parse_args()
    try:
        inventory = build_inventory(args.input, load_contract(args.contract))
    except InventoryError as error:
        print(f"Source inventory failed: {error}", file=sys.stderr)
        return 1
    if args.json:
        print(json.dumps(inventory, indent=2, sort_keys=True))
    else:
        print(text_summary(inventory))
    if args.require_ready and inventory["m4_readiness"]["status"] != "ready":
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
