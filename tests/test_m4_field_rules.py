import copy
import json
import sys
import unittest
from decimal import Decimal
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

import m4_field_rules  # noqa: E402
import source_inventory  # noqa: E402


PATHS = {
    "security": ROOT / "contracts/m4-source-contract.json",
    "loan": ROOT / "contracts/m4-loan-source-contract.json",
    "acquisition": ROOT / "contracts/source-acquisition-metadata-v1.json",
}
FIXTURES = json.loads(
    (ROOT / "tests/fixtures/m4/provider_rules_v2.json").read_text(encoding="utf-8")
)


class M4FieldRuleTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.contracts = {name: m4_field_rules.load_rules(path) for name, path in PATHS.items()}
        cls.fields = {
            name: m4_field_rules.field_map(contract)
            for name, contract in cls.contracts.items()
        }

    def context(self, contract_name, field, case=None):
        context = copy.deepcopy(FIXTURES[f"{contract_name}_context"])
        if case and case.get("row_class"):
            context["row_class"] = case["row_class"]
        elif field["applies_when"]["row_classes"]:
            context["row_class"] = field["applies_when"]["row_classes"][0]
        return context

    def test_all_45_approved_fields_have_executable_golden_cases(self):
        self.assertEqual(
            {name: len(fields) for name, fields in self.fields.items()},
            {"security": 14, "loan": 30, "acquisition": 1},
        )
        expected = {
            (name, target) for name, fields in self.fields.items() for target in fields
        }
        actual = {(case["contract"], case["target"]) for case in FIXTURES["cases"]}
        self.assertEqual(actual, expected)
        for case in FIXTURES["cases"]:
            field = self.fields[case["contract"]][case["target"]]
            context = self.context(case["contract"], field, case)
            self.assertEqual(
                m4_field_rules.validate_value(field, case["valid"], context)["status"],
                "valid",
                case["target"],
            )
            with self.assertRaises(m4_field_rules.FieldRuleError, msg=case["target"]):
                m4_field_rules.validate_value(field, case["invalid"], context)

    def test_every_code_sentinel_null_and_range_rule_executes(self):
        for contract_name, fields in self.fields.items():
            for field in fields.values():
                context = self.context(contract_name, field)
                for code in field["valid_values"]:
                    result = m4_field_rules.validate_value(field, code, context)
                    self.assertEqual(result, {"status": "valid", "value": code})
                for sentinel in field["sentinels"]:
                    result = m4_field_rules.validate_value(field, sentinel["raw"], context)
                    self.assertEqual(result["status"], sentinel["meaning"])
                    self.assertIsNone(result["value"])
                for token in field["null_tokens"]:
                    self.assertEqual(
                        m4_field_rules.validate_value(field, token, context)["status"],
                        "null",
                    )
                rule_range = field["range"]
                if rule_range is None:
                    continue
                for boundary in (rule_range["min"], rule_range["max"]):
                    self.assertEqual(
                        m4_field_rules.validate_value(field, str(boundary), context)["status"],
                        "valid",
                    )
                below = str(Decimal(str(rule_range["min"])) - Decimal("1"))
                if rule_range["out_of_range_action"] == "not_available":
                    self.assertEqual(
                        m4_field_rules.validate_value(field, below, context)["status"],
                        "not_available",
                    )
                else:
                    with self.assertRaises(m4_field_rules.FieldRuleError):
                        m4_field_rules.validate_value(field, below, context)

    def test_family_schema_presence_and_conditional_applicability_fail_closed(self):
        case_by_target = {
            (case["contract"], case["target"]): case for case in FIXTURES["cases"]
        }
        for contract_name, fields in self.fields.items():
            for target, field in fields.items():
                case = case_by_target[(contract_name, target)]
                for window in field["schema_windows"]:
                    context = self.context(contract_name, field, case)
                    context.update(
                        family=window["family"],
                        schema_version=window["schema_version"],
                        report_period=window["period_min"] or "2026-01",
                    )
                    if window["presence"] == "absent":
                        self.assertEqual(
                            m4_field_rules.validate_value(field, "", context)["status"],
                            "not_applicable",
                        )
                        with self.assertRaises(m4_field_rules.FieldRuleError):
                            m4_field_rules.validate_value(field, case["valid"], context)
                    else:
                        self.assertEqual(
                            m4_field_rules.validate_value(field, case["valid"], context)["status"],
                            "valid",
                        )
                if field["applies_when"]["row_classes"]:
                    context = self.context(contract_name, field, case)
                    context["row_class"] = "standard"
                    self.assertEqual(
                        m4_field_rules.validate_value(field, "", context)["status"],
                        "not_applicable",
                    )
                    with self.assertRaises(m4_field_rules.FieldRuleError):
                        m4_field_rules.validate_value(field, case["valid"], context)

    def test_correction_and_release_boundaries_are_complete(self):
        case_by_target = {
            (case["contract"], case["target"]): case for case in FIXTURES["cases"]
        }
        for contract_name, fields in self.fields.items():
            for target, field in fields.items():
                case = case_by_target[(contract_name, target)]
                context = self.context(contract_name, field, case)
                for indicator in field["correction_rule"]["indicators"]:
                    context["correction_indicator"] = indicator
                    self.assertEqual(
                        m4_field_rules.validate_value(field, case["valid"], context)["status"],
                        "valid",
                    )
                context["correction_indicator"] = "?"
                with self.assertRaises(m4_field_rules.FieldRuleError):
                    m4_field_rules.validate_value(field, case["valid"], context)
                self.assertEqual(field["sensitivity"], "restricted")
                self.assertEqual(field["release_rules"]["reviewer"], "not approved")
                self.assertEqual(field["release_rules"]["public"], "not approved")

    def test_v2_rules_load_through_inventory_and_change_cache_signature(self):
        security = source_inventory.load_contract(PATHS["security"])
        loan = source_inventory.load_contract(PATHS["loan"])
        self.assertEqual((security["version"], loan["version"]), (2, 2))
        changed = copy.deepcopy(security)
        changed["field_contracts"][0]["limitation"] += " changed"
        self.assertNotEqual(
            source_inventory.contract_signature(security),
            source_inventory.contract_signature(changed),
        )

    def test_acquisition_timestamp_cannot_be_inferred(self):
        contract = self.contracts["acquisition"]
        self.assertIn("never derive", contract["immutable_rule"])
        field = self.fields["acquisition"]["acquired_at"]
        self.assertFalse(field["nullable"])
        self.assertIn("No current ledger", field["limitation"])

    def test_official_prefix_classes_enforce_negative_applicability(self):
        prefix_contract = json.loads(
            (ROOT / "contracts/freddie-prefix-row-classes-v1.json").read_text()
        )
        classified = [
            prefix
            for prefixes in prefix_contract["classes"].values()
            for prefix in prefixes
        ]
        self.assertEqual(len(classified), len(set(classified)))
        field = self.fields["loan"]["current_interest_rate"]
        context = self.context("loan", field)
        context.update(row_class="arm", prohibited_targets={"current_interest_rate"})
        self.assertEqual(
            m4_field_rules.validate_value(field, "", context)["status"],
            "not_applicable",
        )
        self.assertEqual(
            m4_field_rules.validate_value(field, "99.999", context)["status"],
            "not_available",
        )
        with self.assertRaisesRegex(m4_field_rules.FieldRuleError, "prohibited"):
            m4_field_rules.validate_value(field, "5.125", context)

    def test_out_of_range_provider_mission_values_remain_explicitly_unavailable(self):
        density = self.fields["security"]["mission_density_score"]
        share = self.fields["security"]["mission_criteria_share"]
        context = self.context("security", density)
        self.assertEqual(
            m4_field_rules.validate_value(density, "2.69", context),
            {"status": "not_available", "value": None},
        )
        self.assertEqual(
            m4_field_rules.validate_value(share, "221.11", context),
            {"status": "not_available", "value": None},
        )


if __name__ == "__main__":
    unittest.main()
