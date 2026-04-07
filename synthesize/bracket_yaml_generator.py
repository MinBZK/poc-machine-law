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
        "vloeroppervlakte": {"name": "VLOEROPPERVLAKTE", "description": "Vloeroppervlakte (m²)", "type": "number"},
        "terras_oppervlakte": {"name": "TERRAS_OPPERVLAKTE", "description": "Terrasoppervlakte (m²)", "type": "number"},
        "type_bedrijf_horeca": {"name": "TYPE_BEDRIJF_HORECA", "description": "Horecabedrijf", "type": "boolean"},
        "is_onder_curatele": {"name": "IS_ONDER_CURATELE", "description": "Onder curatele", "type": "boolean"},
        "sbi_is_food": {"name": "SBI_IS_FOOD", "description": "Levensmiddelen-SBI", "type": "boolean"},
        "has_terrace": {"name": "HAS_TERRACE", "description": "Heeft terras", "type": "boolean"},
    }

    def __init__(self, config: BracketYAMLConfig | None = None) -> None:
        self.config = config or BracketYAMLConfig()

    def generate(self, model: BracketModel) -> dict[str, Any]:
        """Generate YAML spec from bracket model."""
        is_business = model.primary_feature != "income"
        yaml_spec = {
            "$id": "https://raw.githubusercontent.com/MinBZK/poc-machine-law/refs/heads/main/schema/v0.5.0/schema.json",
            "uuid": str(uuid.uuid4()),
            "name": self.config.law_display_name,
            "law": self.config.law_name,
            "law_type": "MATERIELE_WET",
            "legal_character": "BESCHIKKING",
            "decision_type": "TOEKENNING",
            "discoverable": "BUSINESS" if is_business else "CITIZEN",
            "valid_from": self.config.valid_from.isoformat(),
            "service": self.config.service_name,
            "description": self.config.description,
            "properties": self._generate_properties(model),
            "actions": self._generate_actions(model),
        }
        return yaml_spec

    def _generate_properties(self, model: BracketModel) -> dict[str, Any]:
        """Generate properties section."""
        is_business = model.primary_feature != "income"
        inputs = []
        used_features = {model.primary_feature}  # Always need primary feature
        for seg in model.segments:
            if seg.household_filter:
                used_features.update(seg.household_filter.keys())
        if model.child_supplement > 0:
            used_features.add("children_count")

        for feat in used_features:
            if feat in self.FEATURE_TO_INPUT:
                inputs.append(self.FEATURE_TO_INPUT[feat].copy())

        if is_business:
            parameters = [{"name": "KVK_NUMMER", "description": "KVK-nummer", "type": "string", "required": True}]
            output_name = "nalevingskosten"
            output_desc = "Nalevingskosten (staffelmodel)"
        else:
            parameters = [{"name": "BSN", "description": "Burgerservicenummer", "type": "string", "required": True}]
            output_name = "toeslag_bedrag"
            output_desc = "Maandelijks toeslagbedrag (staffelmodel)"

        return {
            "parameters": parameters,
            "input": inputs,
            "output": [
                {
                    "name": "is_eligible",
                    "description": "Recht op toeslag" if not is_business else "Verplichting van toepassing",
                    "type": "boolean",
                    "citizen_relevance": "secondary",
                },
                {
                    "name": output_name,
                    "description": output_desc,
                    "type": "amount",
                    "type_spec": {"unit": "eurocent", "precision": 0, "min": 0},
                    "citizen_relevance": "primary",
                },
            ],
            "definitions": self._generate_definitions(model),
        }

    def _generate_definitions(self, model: BracketModel) -> dict[str, Any]:
        """Generate definitions with bracket table."""
        is_business = model.primary_feature != "income"
        prefix = "OPPERVLAKTEGRENS" if is_business else "INKOMENSGRENS"
        defs = {}
        for i, boundary in enumerate(model.income_brackets):
            defs[f"{prefix}_{i}"] = int(boundary)
        return defs

    def _generate_actions(self, model: BracketModel) -> list[dict[str, Any]]:
        """Generate actions with IF/THEN per bracket."""
        is_business = model.primary_feature != "income"
        output_name = "nalevingskosten" if is_business else "toeslag_bedrag"
        # Map primary feature to YAML variable name
        pf_input = self.FEATURE_TO_INPUT.get(model.primary_feature, {}).get("name", model.primary_feature.upper())
        pf_var = f"${pf_input}"

        actions: list[dict[str, Any]] = [{"output": "is_eligible", "value": True}]

        # Group segments by household type
        conditions = []
        for seg in model.segments:
            test_parts = []

            # Primary feature range test
            test_parts.append(
                {
                    "operation": "GREATER_OR_EQUAL",
                    "subject": pf_var,
                    "value": int(seg.income_lower),
                }
            )
            test_parts.append(
                {
                    "operation": "LESS_THAN",
                    "subject": pf_var,
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
                                            "values": [pf_var, int(seg.income_lower)],
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

        actions.append({"output": output_name, "operation": "IF", "conditions": conditions})

        # Add child supplement if applicable
        if model.child_supplement > 0:
            actions.append(
                {
                    "output": output_name,
                    "operation": "ADD",
                    "values": [
                        f"${output_name}",
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
