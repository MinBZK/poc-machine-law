"""
YAML Generator for Bracket/Staffel Model

Converts a BracketModel into Machine Law YAML format with
IF/THEN/ELSE segments and linear formulas per bracket.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

import yaml

from synthesize.bracket_learner import BracketModel
from synthesize.constants import to_native


@dataclass
class BracketYAMLConfig:
    """Configuration for bracket YAML generation."""

    service_name: str = "TOESLAGEN"
    law_name: str = "geharmoniseerde_toeslag_staffel"
    law_display_name: str = "Geharmoniseerde Toeslag (Staffelmodel)"
    description: str = "Geharmoniseerde toeslag op basis van inkomensafhankelijke staffels"
    valid_from: date | None = None

    def __post_init__(self) -> None:
        if self.valid_from is None:
            self.valid_from = date.today()


class BracketYAMLGenerator:
    """Generate Machine Law YAML from bracket model."""

    FEATURE_TO_INPUT = {
        "income": {"name": "INCOME", "description": "Jaarlijks toetsingsinkomen", "type": "amount"},
        "has_partner": {"name": "HAS_PARTNER", "description": "Heeft toeslagpartner", "type": "boolean"},
        "has_children": {"name": "HAS_CHILDREN", "description": "Heeft kinderen", "type": "boolean"},
        "children_count": {"name": "CHILDREN_COUNT", "description": "Aantal kinderen", "type": "number"},
        "housing_type_rent": {"name": "IS_RENTER", "description": "Huurt woning", "type": "boolean"},
    }

    def __init__(self, config: BracketYAMLConfig | None = None) -> None:
        self.config = config or BracketYAMLConfig()

    def generate(self, model: BracketModel) -> dict[str, Any]:
        """Generate YAML spec from bracket model."""
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
            "properties": self._generate_properties(model),
            "actions": self._generate_actions(model),
        }
        return yaml_spec

    def _generate_properties(self, model: BracketModel) -> dict[str, Any]:
        """Generate properties section."""
        inputs = []
        used_features = {"income"}  # Always need income
        for seg in model.segments:
            if seg.household_filter:
                used_features.update(seg.household_filter.keys())
        if model.child_supplement > 0:
            used_features.add("children_count")

        for feat in used_features:
            if feat in self.FEATURE_TO_INPUT:
                inputs.append(self.FEATURE_TO_INPUT[feat].copy())

        return {
            "parameters": [{"name": "BSN", "description": "Burgerservicenummer", "type": "string", "required": True}],
            "input": inputs,
            "output": [
                {
                    "name": "is_eligible",
                    "description": "Recht op toeslag",
                    "type": "boolean",
                    "citizen_relevance": "secondary",
                },
                {
                    "name": "toeslag_bedrag",
                    "description": "Maandelijks toeslagbedrag (staffelmodel)",
                    "type": "amount",
                    "type_spec": {"unit": "eurocent", "precision": 0, "min": 0},
                    "citizen_relevance": "primary",
                },
            ],
            "definitions": self._generate_definitions(model),
        }

    def _generate_definitions(self, model: BracketModel) -> dict[str, Any]:
        """Generate definitions with bracket table."""
        defs = {}
        for i, boundary in enumerate(model.income_brackets):
            defs[f"INKOMENSGRENS_{i}"] = int(boundary)
        return defs

    def _generate_actions(self, model: BracketModel) -> list[dict[str, Any]]:
        """Generate actions with IF/THEN per bracket."""
        actions: list[dict[str, Any]] = [{"output": "is_eligible", "value": True}]

        # Group segments by household type
        conditions = []
        for seg in model.segments:
            test_parts = []

            # Income range test
            test_parts.append(
                {
                    "operation": "GREATER_OR_EQUAL",
                    "subject": "$INCOME",
                    "value": int(seg.income_lower),
                }
            )
            test_parts.append(
                {
                    "operation": "LESS_THAN",
                    "subject": "$INCOME",
                    "value": int(seg.income_upper),
                }
            )

            # Household filter
            if seg.household_filter:
                for key, val in seg.household_filter.items():
                    mapped = self.FEATURE_TO_INPUT.get(key, {}).get("name", key.upper())
                    test_parts.append(
                        {
                            "operation": "EQUALS",
                            "subject": f"${mapped}",
                            "value": bool(val) if key.startswith(("has_", "housing_")) else val,
                        }
                    )

            test = {"operation": "AND", "values": test_parts} if len(test_parts) > 1 else test_parts[0]

            # Linear interpolation: amt_lower + slope * (income - income_lower)
            slope = seg.slope
            if abs(slope) < 0.001 and seg.amount_at_lower == 0:
                then_value: dict[str, Any] = {"value": 0}
            elif abs(slope) < 0.001:
                then_value = {"value": round(seg.amount_at_lower, 2)}
            else:
                then_value = {
                    "operation": "MAX",
                    "values": [
                        {
                            "operation": "ADD",
                            "values": [
                                round(seg.amount_at_lower, 2),
                                {
                                    "operation": "MULTIPLY",
                                    "values": [
                                        round(slope, 6),
                                        {
                                            "operation": "SUBTRACT",
                                            "values": ["$INCOME", int(seg.income_lower)],
                                        },
                                    ],
                                },
                            ],
                        },
                        0,
                    ],
                }

            conditions.append({"test": test, "then": then_value})

        conditions.append({"else": {"value": 0}})

        actions.append({"output": "toeslag_bedrag", "operation": "IF", "conditions": conditions})

        # Add child supplement if applicable
        if model.child_supplement > 0:
            actions.append(
                {
                    "output": "toeslag_bedrag",
                    "operation": "ADD",
                    "values": [
                        "$toeslag_bedrag",
                        {
                            "operation": "MULTIPLY",
                            "values": [round(model.child_supplement, 2), "$CHILDREN_COUNT"],
                        },
                    ],
                }
            )

        return actions

    def to_yaml_string(self, spec: dict[str, Any]) -> str:
        """Convert spec to YAML string."""
        return yaml.dump(to_native(spec), default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
