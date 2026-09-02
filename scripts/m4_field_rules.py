#!/usr/bin/env python3
"""Validate contracted M4 provider fields without emitting disclosure values."""

from __future__ import annotations

import json
import re
from datetime import datetime
from decimal import Decimal, InvalidOperation
from pathlib import Path
from typing import Any


class FieldRuleError(ValueError):
    """A provider rule or value is invalid."""


RULE_KEYS = {
    "target",
    "source_names",
    "provider_field_id",
    "definition",
    "type",
    "raw_format",
    "max_length",
    "scale",
    "unit",
    "nullable",
    "null_tokens",
    "sentinels",
    "valid_values",
    "range",
    "schema_profile",
    "applies_when",
    "correction_rule",
    "sensitivity",
    "release_rules",
    "authorized_use",
    "limitation",
}
ALLOWED_TYPES = {"text", "integer", "decimal", "date", "enum", "timestamp"}
PRESENCE = {"required", "absent"}


def load_rules(path: Path) -> dict[str, Any]:
    try:
        contract = json.loads(path.read_text(encoding="utf-8"))
    except (FileNotFoundError, json.JSONDecodeError) as error:
        raise FieldRuleError(f"invalid field-rule contract: {path}") from error
    validate_contract(contract)
    return contract


def validate_contract(contract: dict[str, Any]) -> None:
    required = {
        "version", "contract_id", "status", "provider_guide",
        "schema_profiles", "field_contracts",
    }
    if not isinstance(contract, dict) or not required.issubset(contract):
        raise FieldRuleError("field-rule contract is incomplete")
    guide = contract["provider_guide"]
    if not isinstance(guide, dict) or not {"version", "effective_on", "url"}.issubset(guide):
        raise FieldRuleError("provider guide metadata is incomplete")
    profiles = contract["schema_profiles"]
    if not isinstance(profiles, dict) or not profiles:
        raise FieldRuleError("schema_profiles must be non-empty")
    for windows in profiles.values():
        if not isinstance(windows, list) or not windows:
            raise FieldRuleError("schema profile must contain windows")
        for window in windows:
            if not {"family", "schema_version", "period_min", "period_max", "presence"}.issubset(window):
                raise FieldRuleError("schema window is incomplete")
            if window["presence"] not in PRESENCE:
                raise FieldRuleError("schema presence must be required or absent")
    fields = contract["field_contracts"]
    if not isinstance(fields, list) or not fields:
        raise FieldRuleError("field_contracts must be non-empty")
    targets: set[str] = set()
    for field in fields:
        validate_rule(field)
        if field["schema_profile"] not in profiles:
            raise FieldRuleError(f"unknown schema profile: {field['schema_profile']}")
        if field["target"] in targets:
            raise FieldRuleError(f"duplicate field target: {field['target']}")
        targets.add(field["target"])


def validate_rule(field: dict[str, Any]) -> None:
    if not isinstance(field, dict) or not RULE_KEYS.issubset(field):
        raise FieldRuleError("field contract is incomplete")
    if field["type"] not in ALLOWED_TYPES:
        raise FieldRuleError(f"unsupported field type: {field['type']}")
    if not field["source_names"] or field["sensitivity"] != "restricted":
        raise FieldRuleError("source names and restricted sensitivity are required")
    if not isinstance(field["nullable"], bool) or not isinstance(field["null_tokens"], list):
        raise FieldRuleError("null rules are invalid")
    if field["type"] == "enum" and not field["valid_values"]:
        raise FieldRuleError("enum field requires valid_values")
    if field["type"] != "enum" and field["valid_values"]:
        raise FieldRuleError("valid_values are allowed only for enum fields")
    if field["range"] is not None and not {"min", "max", "out_of_range_action"}.issubset(field["range"]):
        raise FieldRuleError("range rule is incomplete")
    if not field["schema_profile"]:
        raise FieldRuleError("schema profile is required")
    if not {"indicators", "behavior"}.issubset(field["correction_rule"]):
        raise FieldRuleError("correction rule is incomplete")
    if set(field["release_rules"]) != {"authorized", "reviewer", "public"}:
        raise FieldRuleError("release rules are incomplete")


def field_map(contract: dict[str, Any]) -> dict[str, dict[str, Any]]:
    return {
        field["target"]: {
            **field,
            "schema_windows": contract["schema_profiles"][field["schema_profile"]],
        }
        for field in contract["field_contracts"]
    }


def validate_value(field: dict[str, Any], raw: str | None, context: dict[str, str]) -> dict[str, Any]:
    family = context.get("family")
    schema = context.get("schema_version")
    period = context.get("report_period")
    windows = [
        window
        for window in field["schema_windows"]
        if window["family"] == family
        and window["schema_version"] == schema
        and (window["period_min"] is None or period >= window["period_min"])
        and (window["period_max"] is None or period <= window["period_max"])
    ]
    if len(windows) != 1:
        raise FieldRuleError(f"{field['target']} has no unique schema window")
    value = "" if raw is None else raw.strip()
    window = windows[0]
    if window["presence"] == "absent":
        if value:
            raise FieldRuleError(f"{field['target']} must be absent for {family}")
        return {"status": "not_applicable", "value": None}

    indicator = context.get("correction_indicator")
    if indicator not in field["correction_rule"]["indicators"]:
        raise FieldRuleError(f"{field['target']} has invalid correction context")
    row_classes = field["applies_when"].get("row_classes", [])
    if row_classes and context.get("row_class") not in row_classes:
        if value:
            raise FieldRuleError(f"{field['target']} is populated outside its applicable row class")
        return {"status": "not_applicable", "value": None}
    if field["target"] in context.get("prohibited_targets", set()):
        if value in field["null_tokens"]:
            return {"status": "not_applicable", "value": None}
        for sentinel in field["sentinels"]:
            if value == sentinel["raw"]:
                return {"status": sentinel["meaning"], "value": None}
        raise FieldRuleError(
            f"{field['target']} is populated for a prohibited row class"
        )
    if value in field["null_tokens"]:
        if not field["nullable"]:
            raise FieldRuleError(f"{field['target']} is required")
        return {"status": "null", "value": None}
    for sentinel in field["sentinels"]:
        if value == sentinel["raw"]:
            return {"status": sentinel["meaning"], "value": None}
    if len(value) > field["max_length"]:
        raise FieldRuleError(f"{field['target']} exceeds max length")

    parsed = parse_value(field, value)
    rule_range = field["range"]
    if rule_range is not None and not (Decimal(str(rule_range["min"])) <= Decimal(str(parsed)) <= Decimal(str(rule_range["max"]))):
        if rule_range["out_of_range_action"] == "not_available":
            return {"status": "not_available", "value": None}
        raise FieldRuleError(f"{field['target']} is outside its approved range")
    return {"status": "valid", "value": parsed}


def parse_value(field: dict[str, Any], value: str) -> Any:
    value_type = field["type"]
    if value_type == "enum":
        if value not in field["valid_values"]:
            raise FieldRuleError(f"{field['target']} has an unknown code")
        return value
    if value_type == "integer":
        if not re.fullmatch(r"-?\d+", value):
            raise FieldRuleError(f"{field['target']} is not an integer")
        return int(value)
    if value_type == "decimal":
        if not re.fullmatch(r"-?\d+(?:\.\d+)?", value):
            raise FieldRuleError(f"{field['target']} is not a decimal")
        fraction = value.partition(".")[2]
        if len(fraction) > field["scale"]:
            raise FieldRuleError(f"{field['target']} exceeds approved scale")
        try:
            return Decimal(value)
        except InvalidOperation as error:
            raise FieldRuleError(f"{field['target']} is not a decimal") from error
    if value_type == "date":
        formats = {"MMCCYY": "%m%Y", "MMDDCCYY": "%m%d%Y"}
        try:
            datetime.strptime(value, formats[field["raw_format"]])
        except (KeyError, ValueError) as error:
            raise FieldRuleError(f"{field['target']} has an invalid date") from error
        if field.get("fixed_day") and value[2:4] != field["fixed_day"]:
            raise FieldRuleError(f"{field['target']} has an invalid provider-defaulted day")
        return value
    if value_type == "timestamp":
        if not re.fullmatch(r"\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}Z", value):
            raise FieldRuleError(f"{field['target']} is not UTC RFC3339 seconds")
        datetime.strptime(value, "%Y-%m-%dT%H:%M:%SZ")
        return value
    if not value:
        raise FieldRuleError(f"{field['target']} is empty")
    return value
