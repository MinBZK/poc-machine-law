"""Extract overridable law parameters directly from YAML definitions.

Reads the `definitions` section from each discoverable law's YAML to
populate the simulation UI with adjustable parameters (tax rates,
thresholds, premiums, etc.).
"""

import logging
from typing import Any

from machine.utils import RuleResolver

logger = logging.getLogger(__name__)

# UI-friendly name derivation: strip common prefixes
_PREFIXES = ["wet_op_het_", "wet_op_de_", "wet_", "algemene_"]


def _derive_ui_name(law_name: str) -> str:
    """Derive a short UI name from a technical law name."""
    name = law_name.split("/")[-1] if "/" in law_name else law_name
    for prefix in _PREFIXES:
        if name.startswith(prefix):
            name = name[len(prefix) :]
            break
    return name.strip("_").replace("_", "").capitalize()


def _is_overridable(key: str, value: Any) -> bool:
    """Check if a definition is a numeric value that makes sense to override."""
    if isinstance(value, dict):
        value = value.get("value")
    return isinstance(value, (int, float))


def _ui_value(key: str, value: Any) -> float:
    """Convert an engine-internal value to a UI-friendly number.

    Handles eurocent→euro and decimal→percentage conversions based on
    naming conventions.
    """
    if isinstance(value, dict):
        value = value.get("value", value)
    if not isinstance(value, (int, float)):
        return value

    key_lower = key.lower()
    # Eurocent values (typically > 1000 and integer) → euros
    if isinstance(value, int) and abs(value) >= 1000:
        return round(value / 100, 2)
    # Decimal rates (0 < x < 1) → percentage
    if 0 < abs(value) < 1 and ("tarief" in key_lower or "percentage" in key_lower or "afbouw" in key_lower):
        return round(value * 100, 4)
    return value


def get_default_law_parameters_subprocess(simulation_date: str = "2025-01-01") -> dict[str, dict[str, Any]]:
    """Read overridable parameters from law YAML definitions.

    Walks all citizen-discoverable laws, reads their YAML files, and
    extracts numeric definitions that can be overridden in the simulation UI.
    """
    resolver = RuleResolver()
    service_laws = resolver.get_discoverable_service_laws("CITIZEN")
    parameters: dict[str, dict[str, Any]] = {}

    for service_name, laws in service_laws.items():
        for law_name in laws:
            try:
                rule = resolver.find_rule(law_name, simulation_date, service_name)
                if not rule:
                    continue

                # Definitions live in rule.properties (parsed from the YAML spec)
                raw_defs = rule.properties.get("definitions", {})
                defs: dict[str, Any] = {}
                for key, value in raw_defs.items():
                    if _is_overridable(key, value):
                        defs[key.lower()] = _ui_value(key, value)

                if defs:
                    ui_name = _derive_ui_name(law_name)
                    parameters[ui_name] = defs

            except Exception as e:
                logger.debug("Could not read parameters for %s.%s: %s", service_name, law_name, e)

    logger.info("Discovered %d parameters across %d laws", sum(len(v) for v in parameters.values()), len(parameters))
    return parameters
