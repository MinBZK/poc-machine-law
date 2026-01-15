"""
YAML Generator for Law Synthesis

Converts learned ML models (decision tree rules + linear formulas)
into Machine Law YAML format that can be executed by the RulesEngine.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

import yaml

from synthesize.learner import ExtractedRule, LearnedModel, LinearFormula


@dataclass
class YAMLGenerationConfig:
    """Configuration for YAML generation."""

    service_name: str = "TOESLAGEN"
    law_name: str = "geharmoniseerde_toeslag"
    law_display_name: str = "Geharmoniseerde Toeslag"
    description: str = "Geharmoniseerde versie van zorgtoeslag, huurtoeslag en kindgebonden budget"
    valid_from: date | None = None

    def __post_init__(self) -> None:
        if self.valid_from is None:
            self.valid_from = date.today()


class YAMLGenerator:
    """
    Generate Machine Law YAML from learned models.

    Converts decision tree rules to requirements and
    linear formulas to actions.
    """

    # Mapping from simulation feature names to YAML input names
    FEATURE_TO_INPUT = {
        "age": {
            "name": "AGE",
            "description": "Leeftijd van de aanvrager",
            "type": "number",
            "service_reference": {"service": "RvIG", "law": "wet_brp", "field": "age"},
        },
        "income": {
            "name": "INCOME",
            "description": "Jaarlijks toetsingsinkomen",
            "type": "amount",
            "service_reference": {"service": "BELASTINGDIENST", "law": "wet_inkomstenbelasting", "field": "income"},
        },
        "net_worth": {
            "name": "NET_WORTH",
            "description": "Vermogen",
            "type": "amount",
            "service_reference": {"service": "BELASTINGDIENST", "law": "wet_inkomstenbelasting", "field": "net_worth"},
        },
        "rent_amount": {
            "name": "RENT_AMOUNT",
            "description": "Maandelijkse huur",
            "type": "amount",
            "service_reference": {"service": "TOESLAGEN", "law": "wet_op_de_huurtoeslag", "field": "rent"},
        },
        "has_partner": {
            "name": "HAS_PARTNER",
            "description": "Heeft de persoon een toeslagpartner",
            "type": "boolean",
            "service_reference": {"service": "RvIG", "law": "wet_brp", "field": "has_partner"},
        },
        "has_children": {
            "name": "HAS_CHILDREN",
            "description": "Heeft de persoon kinderen",
            "type": "boolean",
            "service_reference": {"service": "RvIG", "law": "wet_brp", "field": "has_children"},
        },
        "children_count": {
            "name": "CHILDREN_COUNT",
            "description": "Aantal kinderen",
            "type": "number",
            "service_reference": {"service": "RvIG", "law": "wet_brp", "field": "children_count"},
        },
        "youngest_child_age": {
            "name": "YOUNGEST_CHILD_AGE",
            "description": "Leeftijd jongste kind",
            "type": "number",
            "service_reference": {"service": "RvIG", "law": "wet_brp", "field": "youngest_child_age"},
        },
        "housing_type_rent": {
            "name": "IS_RENTER",
            "description": "Huurt de persoon een woning",
            "type": "boolean",
            "service_reference": {"service": "TOESLAGEN", "law": "wet_op_de_huurtoeslag", "field": "is_renter"},
        },
        "is_student": {
            "name": "IS_STUDENT",
            "description": "Is de persoon student",
            "type": "boolean",
            "service_reference": {"service": "DUO", "law": "wet_studiefinanciering", "field": "is_student"},
        },
    }

    def __init__(self, config: YAMLGenerationConfig | None = None) -> None:
        self.config = config or YAMLGenerationConfig()

    def generate(self, model: LearnedModel) -> dict[str, Any]:
        """Generate complete Machine Law YAML structure from learned model."""
        # Determine which features are actually used
        used_features = self._get_used_features(model)

        yaml_spec = {
            "$id": "https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.1.4/schema.json",
            "uuid": str(uuid.uuid4()),
            "name": self.config.law_display_name,
            "law": self.config.law_name,
            "law_type": "MATERIELE_WET",
            "legal_character": "BESCHIKKING",
            "decision_type": "TOEKENNING",
            "discoverable": "CITIZEN",
            "valid_from": self.config.valid_from.isoformat(),
            "service": self.config.service_name,
            "description": self.config.description,
            "properties": self._generate_properties(used_features),
            "requirements": self._generate_requirements(model.eligibility_rules),
            "actions": self._generate_actions(model.amount_formulas),
        }

        return yaml_spec

    def _get_used_features(self, model: LearnedModel) -> set[str]:
        """Determine which features are used in the model."""
        used = set()

        # Features from eligibility rules
        for rule in model.eligibility_rules:
            for condition in rule.conditions:
                feature = condition.split()[0]
                used.add(feature)

        # Features from amount formulas
        for formula in model.amount_formulas:
            for feature in formula.coefficients:
                used.add(feature)
            for condition in formula.segment_conditions:
                feature = condition.split()[0]
                used.add(feature)

        return used

    def _generate_properties(self, used_features: set[str]) -> dict[str, Any]:
        """Generate properties section with inputs and outputs."""
        inputs = []

        for feature in used_features:
            if feature in self.FEATURE_TO_INPUT:
                input_spec = self.FEATURE_TO_INPUT[feature].copy()
                # Add BSN parameter reference
                input_spec["service_reference"] = input_spec["service_reference"].copy()
                input_spec["service_reference"]["parameters"] = [{"name": "BSN", "reference": "$BSN"}]
                inputs.append(input_spec)

        return {
            "parameters": [
                {
                    "name": "BSN",
                    "description": "Burgerservicenummer van de aanvrager",
                    "type": "string",
                    "required": True,
                }
            ],
            "input": inputs,
            "output": [
                {
                    "name": "is_eligible",
                    "description": "Heeft de persoon recht op geharmoniseerde toeslag",
                    "type": "boolean",
                    "citizen_relevance": "secondary",
                },
                {
                    "name": "toeslag_bedrag",
                    "description": "Totaalbedrag geharmoniseerde toeslag per maand",
                    "type": "amount",
                    "type_spec": {"unit": "eurocent", "precision": 0, "min": 0},
                    "citizen_relevance": "primary",
                },
            ],
            "definitions": {},
        }

    def _generate_requirements(self, rules: list[ExtractedRule]) -> list[dict[str, Any]]:
        """Generate requirements section from eligibility rules."""
        if not rules:
            return []

        # Convert each rule to a requirement path
        requirement_paths = []

        for rule in rules:
            if rule.prediction != "eligible":
                continue

            conditions = [self._parse_condition(c) for c in rule.conditions]

            if len(conditions) == 1:
                requirement_paths.append(conditions[0])
            elif len(conditions) > 1:
                requirement_paths.append({"all": conditions})

        # Combine all paths with OR (eligible if ANY path matches)
        if len(requirement_paths) == 0:
            return []
        elif len(requirement_paths) == 1:
            return [requirement_paths[0]]
        else:
            return [{"or": requirement_paths}]

    def _parse_condition(self, condition_str: str) -> dict[str, Any]:
        """Parse a condition string to YAML operation format."""
        # Parse "feature <= value" or "feature > value"
        if "<=" in condition_str:
            parts = condition_str.split("<=")
            feature = parts[0].strip()
            value = self._parse_value(parts[1].strip())
            return {
                "operation": "LESS_OR_EQUAL",
                "subject": f"${self._map_feature_name(feature)}",
                "value": value,
            }
        elif ">=" in condition_str:
            parts = condition_str.split(">=")
            feature = parts[0].strip()
            value = self._parse_value(parts[1].strip())
            return {
                "operation": "GREATER_OR_EQUAL",
                "subject": f"${self._map_feature_name(feature)}",
                "value": value,
            }
        elif ">" in condition_str:
            parts = condition_str.split(">")
            feature = parts[0].strip()
            value = self._parse_value(parts[1].strip())
            return {
                "operation": "GREATER_THAN",
                "subject": f"${self._map_feature_name(feature)}",
                "value": value,
            }
        elif "<" in condition_str:
            parts = condition_str.split("<")
            feature = parts[0].strip()
            value = self._parse_value(parts[1].strip())
            return {
                "operation": "LESS_THAN",
                "subject": f"${self._map_feature_name(feature)}",
                "value": value,
            }
        elif "==" in condition_str:
            parts = condition_str.split("==")
            feature = parts[0].strip()
            value = self._parse_value(parts[1].strip())
            return {
                "operation": "EQUALS",
                "subject": f"${self._map_feature_name(feature)}",
                "value": value,
            }
        else:
            raise ValueError(f"Cannot parse condition: {condition_str}")

    def _parse_value(self, value_str: str) -> int | float | bool:
        """Parse a value string to appropriate type."""
        value_str = value_str.strip()

        # Boolean
        if value_str.lower() == "true":
            return True
        if value_str.lower() == "false":
            return False

        # Try integer
        try:
            return int(value_str)
        except ValueError:
            pass

        # Try float
        try:
            return float(value_str)
        except ValueError:
            pass

        return value_str

    def _map_feature_name(self, feature: str) -> str:
        """Map model feature name to YAML input name."""
        if feature in self.FEATURE_TO_INPUT:
            return self.FEATURE_TO_INPUT[feature]["name"]
        return feature.upper()

    def _generate_actions(self, formulas: list[LinearFormula]) -> list[dict[str, Any]]:
        """Generate actions section from amount formulas."""
        actions = [
            # First action: set eligibility to true (requirements already checked)
            {"output": "is_eligible", "value": True}
        ]

        if not formulas:
            # No formulas learned, set amount to 0
            actions.append({"output": "toeslag_bedrag", "value": 0})
            return actions

        if len(formulas) == 1:
            # Single formula for all eligible
            actions.append(self._generate_linear_action(formulas[0]))
        else:
            # Multiple formulas: use IF-THEN-ELSE based on segment conditions
            actions.append(self._generate_segmented_action(formulas))

        return actions

    def _generate_linear_action(self, formula: LinearFormula) -> dict[str, Any]:
        """Generate action for a single linear formula."""
        # Build ADD operation: intercept + sum(coef * feature)
        add_values: list[Any] = []

        # Add intercept if significant
        if abs(formula.intercept) > 0.01:
            add_values.append(round(formula.intercept, 2))

        # Add coefficient * feature terms
        for feature, coef in formula.coefficients.items():
            if abs(coef) > 0.01:
                add_values.append(
                    {"operation": "MULTIPLY", "values": [round(coef, 4), f"${self._map_feature_name(feature)}"]}
                )

        if not add_values:
            return {"output": "toeslag_bedrag", "value": 0}

        # Wrap in MAX to ensure non-negative
        return {
            "output": "toeslag_bedrag",
            "operation": "MAX",
            "values": [
                {"operation": "ADD", "values": add_values} if len(add_values) > 1 else add_values[0],
                0,
            ],
        }

    def _generate_segmented_action(self, formulas: list[LinearFormula]) -> dict[str, Any]:
        """Generate IF-THEN-ELSE action for multiple segments."""
        conditions = []

        for formula in formulas:
            # Build test condition from segment conditions
            if formula.segment_conditions:
                test_parts = [self._parse_condition(c) for c in formula.segment_conditions]
                test = {"operation": "AND", "values": test_parts} if len(test_parts) > 1 else test_parts[0]
            else:
                # No conditions means always true
                test = {"value": True}

            # Build amount formula
            add_values: list[Any] = []
            if abs(formula.intercept) > 0.01:
                add_values.append(round(formula.intercept, 2))

            for feature, coef in formula.coefficients.items():
                if abs(coef) > 0.01:
                    add_values.append(
                        {"operation": "MULTIPLY", "values": [round(coef, 4), f"${self._map_feature_name(feature)}"]}
                    )

            if add_values:
                then_value = {
                    "operation": "MAX",
                    "values": [
                        {"operation": "ADD", "values": add_values} if len(add_values) > 1 else add_values[0],
                        0,
                    ],
                }
            else:
                then_value = {"value": 0}

            conditions.append({"test": test, "then": then_value})

        # Add default else case
        conditions.append({"else": {"value": 0}})

        return {"output": "toeslag_bedrag", "operation": "IF", "conditions": conditions}

    def to_yaml_string(self, spec: dict[str, Any]) -> str:
        """Convert spec to YAML string."""

        # Custom representer for cleaner output
        def str_representer(dumper: yaml.Dumper, data: str) -> yaml.ScalarNode:
            if "\n" in data:
                return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
            return dumper.represent_scalar("tag:yaml.org,2002:str", data)

        yaml.add_representer(str, str_representer)

        return yaml.dump(spec, default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)

    def save_yaml(self, spec: dict[str, Any], filepath: str) -> None:
        """Save spec to YAML file."""
        with open(filepath, "w") as f:
            f.write(self.to_yaml_string(spec))
