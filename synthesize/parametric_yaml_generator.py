"""
YAML Generator for Parametric Formula Model

Converts a ParametricModel into Machine Law YAML format with
named definitions and nested MAX/SUBTRACT/MULTIPLY operations.
"""

import uuid
from dataclasses import dataclass
from datetime import date
from typing import Any

import yaml

from synthesize.constants import to_native
from synthesize.parametric_learner import ParametricModel

LAW_DISPLAY_NAMES = {
    "zorgtoeslag": "Zorgtoeslag",
    "huurtoeslag": "Huurtoeslag",
    "kindgebonden_budget": "Kindgebonden budget",
    "aow": "AOW",
    "bijstand": "Bijstand",
    "ww": "WW-uitkering",
    "kinderopvangtoeslag": "Kinderopvangtoeslag",
}


@dataclass
class ParametricYAMLConfig:
    """Configuration for parametric YAML generation."""

    service_name: str = "TOESLAGEN"
    law_name: str = "geharmoniseerde_toeslag_parametrisch"
    law_display_name: str = "Geharmoniseerde Toeslag (Parametrische formule)"
    description: str = "Geharmoniseerde toeslag op basis van vereenvoudigde formules per wet"
    valid_from: date | None = None

    def __post_init__(self) -> None:
        if self.valid_from is None:
            self.valid_from = date.today()


class ParametricYAMLGenerator:
    """Generate Machine Law YAML from parametric model."""

    def __init__(self, config: ParametricYAMLConfig | None = None) -> None:
        self.config = config or ParametricYAMLConfig()

    def generate(self, model: ParametricModel) -> dict[str, Any]:
        """Generate YAML spec from parametric model."""
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

    def _generate_properties(self, model: ParametricModel) -> dict[str, Any]:
        """Generate properties with definitions for each component."""
        definitions = {}
        for comp in model.template.components:
            prefix = comp.name.upper()
            definitions[f"{prefix}_BASIS_ALLEENSTAAND"] = round(comp.base_single, 2)
            definitions[f"{prefix}_AFBOUWPERCENTAGE_ALLEENSTAAND"] = round(comp.rate_single, 4)
            definitions[f"{prefix}_DREMPELINKOMEN_ALLEENSTAAND"] = round(comp.threshold_single, 2)
            if comp.has_partner_variant:
                definitions[f"{prefix}_BASIS_PARTNER"] = round(comp.base_partner, 2)
                definitions[f"{prefix}_AFBOUWPERCENTAGE_PARTNER"] = round(comp.rate_partner, 4)
                definitions[f"{prefix}_DREMPELINKOMEN_PARTNER"] = round(comp.threshold_partner, 2)

        return {
            "parameters": [{"name": "BSN", "description": "Burgerservicenummer", "type": "string", "required": True}],
            "input": [
                {"name": "INCOME", "description": "Jaarlijks toetsingsinkomen", "type": "amount"},
                {"name": "HAS_PARTNER", "description": "Heeft toeslagpartner", "type": "boolean"},
            ],
            "output": [
                {
                    "name": "is_eligible",
                    "description": "Recht op toeslag",
                    "type": "boolean",
                    "citizen_relevance": "secondary",
                },
                {
                    "name": "toeslag_bedrag",
                    "description": "Maandelijks toeslagbedrag (parametrische formule)",
                    "type": "amount",
                    "type_spec": {"unit": "eurocent", "precision": 0, "min": 0},
                    "citizen_relevance": "primary",
                },
            ],
            "definitions": definitions,
        }

    def _generate_actions(self, model: ParametricModel) -> list[dict[str, Any]]:
        """Generate actions: per component an IF partner/THEN/ELSE with formulas."""
        actions: list[dict[str, Any]] = [{"output": "is_eligible", "value": True}]

        component_refs = []
        for i, comp in enumerate(model.template.components):
            output_name = f"component_{i}_{comp.name}"
            component_refs.append(f"${output_name}")

            if comp.has_partner_variant:
                # IF HAS_PARTNER THEN partner_formula ELSE single_formula
                actions.append(
                    {
                        "output": output_name,
                        "operation": "IF",
                        "conditions": [
                            {
                                "test": {"operation": "EQUALS", "subject": "$HAS_PARTNER", "value": True},
                                "then": self._make_formula(
                                    comp.base_partner, comp.rate_partner, comp.threshold_partner
                                ),
                            },
                            {
                                "else": self._make_formula(comp.base_single, comp.rate_single, comp.threshold_single),
                            },
                        ],
                    }
                )
            else:
                actions.append(
                    {
                        "output": output_name,
                        **self._make_formula(comp.base_single, comp.rate_single, comp.threshold_single),
                    }
                )

        # Total = sum of components
        if len(component_refs) == 1:
            actions.append({"output": "toeslag_bedrag", "value": component_refs[0]})
        else:
            actions.append(
                {
                    "output": "toeslag_bedrag",
                    "operation": "ADD",
                    "values": component_refs,
                }
            )

        return actions

    def _make_formula(self, base: float, rate: float, threshold: float) -> dict[str, Any]:
        """Create max(0, base - rate * max(0, income - threshold))."""
        return {
            "operation": "MAX",
            "values": [
                {
                    "operation": "SUBTRACT",
                    "values": [
                        round(base, 2),
                        {
                            "operation": "MULTIPLY",
                            "values": [
                                round(rate, 4),
                                {
                                    "operation": "MAX",
                                    "values": [
                                        {"operation": "SUBTRACT", "values": ["$INCOME", round(threshold, 2)]},
                                        0,
                                    ],
                                },
                            ],
                        },
                    ],
                },
                0,
            ],
        }

    def to_yaml_string(self, spec: dict[str, Any]) -> str:
        """Convert spec to YAML string."""
        return yaml.dump(to_native(spec), default_flow_style=False, allow_unicode=True, sort_keys=False, width=120)
