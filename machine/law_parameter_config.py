"""
Law parameter configuration registry for mapping UI parameters to engine overrides.

This module provides a centralized configuration for how UI law parameters should be
transformed and applied to the simulation engine. It supports both input overrides
(for properties with service_reference) and definition overrides (for constants).
"""

from typing import Any, Callable, Literal


class ParameterMapping:
    """Configuration for mapping a UI parameter to an engine override"""

    def __init__(
        self,
        ui_param_name: str,
        engine_field_name: str,
        override_type: Literal["input", "definition"],
        service_name: str | None = None,
        transform_to_engine: Callable[[Any], Any] | None = None,
        transform_from_engine: Callable[[Any], Any] | None = None,
    ):
        """
        Initialize parameter mapping.

        Args:
            ui_param_name: Name of parameter in UI (e.g., "standaardpremie")
            engine_field_name: Name in engine/YAML (e.g., "STANDAARDPREMIE_2025" or "standaardpremie")
            override_type: Whether this is an "input" or "definition" override
            service_name: Service name for input overrides (e.g., "VWS")
            transform_to_engine: Function to convert UI value to engine format
            transform_from_engine: Function to convert engine value to UI format
        """
        self.ui_param_name = ui_param_name
        self.engine_field_name = engine_field_name
        self.override_type = override_type
        self.service_name = service_name
        self.transform_to_engine = transform_to_engine or (lambda x: x)
        self.transform_from_engine = transform_from_engine or (lambda x: x)


class LawConfig:
    """Configuration for a law's parameters"""

    def __init__(self, ui_name: str, law_name: str, service: str):
        """
        Initialize law configuration.

        Args:
            ui_name: UI name (e.g., "inkomstenbelasting")
            law_name: Technical law name (e.g., "wet_inkomstenbelasting")
            service: Service that evaluates this law (e.g., "BELASTINGDIENST")
        """
        self.ui_name = ui_name
        self.law_name = law_name
        self.service = service
        self.parameters: dict[str, ParameterMapping] = {}

    def add_parameter(self, mapping: ParameterMapping) -> None:
        """Add a parameter mapping to this law"""
        self.parameters[mapping.ui_param_name] = mapping


# Global law configuration registry
_LAW_CONFIGS: dict[str, LawConfig] = {}


def register_law(ui_name: str, law_name: str, service: str) -> LawConfig:
    """Register a law and return its configuration for adding parameters"""
    config = LawConfig(ui_name, law_name, service)
    _LAW_CONFIGS[ui_name] = config
    return config


def get_law_config(ui_name: str) -> LawConfig | None:
    """Get law configuration by UI name"""
    return _LAW_CONFIGS.get(ui_name)


def get_all_law_configs() -> dict[str, LawConfig]:
    """Get all law configurations"""
    return _LAW_CONFIGS


def find_law_config_by_technical_name(law_name: str) -> LawConfig | None:
    """Find law configuration by technical law name"""
    for config in _LAW_CONFIGS.values():
        if config.law_name == law_name:
            return config
    return None


# ==============================================================================
# LAW CONFIGURATIONS
# ==============================================================================

# Zorgtoeslag
# ------------
zorgtoeslag = register_law("zorgtoeslag", "zorgtoeslagwet", "TOESLAGEN")
zorgtoeslag.add_parameter(
    ParameterMapping(
        ui_param_name="standaardpremie",
        engine_field_name="standaardpremie",
        override_type="input",
        service_name="VWS",  # This is an input from VWS service
        transform_to_engine=lambda monthly_euros: int(monthly_euros * 12 * 100),  # monthly € → yearly eurocents
        transform_from_engine=lambda yearly_cents: round(yearly_cents / 100 / 12, 2),  # yearly eurocents → monthly €
    )
)

# Inkomstenbelasting (Income Tax)
# --------------------------------
inkomstenbelasting = register_law("inkomstenbelasting", "wet_inkomstenbelasting", "BELASTINGDIENST")
inkomstenbelasting.add_parameter(
    ParameterMapping(
        ui_param_name="tarief_schijf1",
        engine_field_name="BOX1_TARIEF1",
        override_type="definition",  # This is a definition constant
        transform_to_engine=lambda percentage: percentage / 100,  # percentage → decimal (36.93 → 0.3693)
        transform_from_engine=lambda decimal: round(decimal * 100, 2),  # decimal → percentage (0.3693 → 36.93)
    )
)
inkomstenbelasting.add_parameter(
    ParameterMapping(
        ui_param_name="tarief_schijf2",
        engine_field_name="BOX1_TARIEF2",
        override_type="definition",
        transform_to_engine=lambda percentage: percentage / 100,  # percentage → decimal (49.53 → 0.4953)
        transform_from_engine=lambda decimal: round(decimal * 100, 2),  # decimal → percentage (0.4953 → 49.53)
    )
)
inkomstenbelasting.add_parameter(
    ParameterMapping(
        ui_param_name="grens_schijf1",
        engine_field_name="BOX1_SCHIJF1_GRENS",
        override_type="definition",
        transform_to_engine=lambda euros: int(euros * 100),  # euros → eurocents (74573 → 7457300)
        transform_from_engine=lambda cents: round(cents / 100),  # eurocents → euros (7457300 → 74573)
    )
)
inkomstenbelasting.add_parameter(
    ParameterMapping(
        ui_param_name="algemene_heffingskorting",
        engine_field_name="ALGEMENE_HEFFINGSKORTING_MAX",
        override_type="definition",
        transform_to_engine=lambda euros: int(euros * 100),  # euros → eurocents (3104 → 310400)
        transform_from_engine=lambda cents: round(cents / 100),  # eurocents → euros (310400 → 3104)
    )
)

# Huurtoeslag (Rent Subsidy)
# ---------------------------
# TODO: Add when YAML definitions are available
huurtoeslag = register_law("huurtoeslag", "wet_op_de_huurtoeslag", "TOESLAGEN")

# Kinderopvangtoeslag (Childcare Subsidy)
# ----------------------------------------
# TODO: Add when YAML definitions are available
kinderopvangtoeslag = register_law("kinderopvangtoeslag", "wet_kinderopvang", "TOESLAGEN")

# AOW (State Pension)
# -------------------
# TODO: Add when YAML definitions are available
aow = register_law("aow", "algemene_ouderdomswet", "SVB")

# Bijstand (Social Assistance)
# -----------------------------
# TODO: Add when YAML definitions are available
bijstand = register_law("bijstand", "participatiewet/bijstand", "GEMEENTE_AMSTERDAM")

# Kiesrecht (Voting Rights)
# --------------------------
# TODO: Add when YAML definitions are available
kiesrecht = register_law("kiesrecht", "kieswet", "KIESRAAD")


# ==============================================================================
# HELPER FUNCTIONS
# ==============================================================================


def create_overrides(ui_law_name: str, ui_parameters: dict[str, Any]) -> tuple[dict[str, dict[str, Any]], dict[str, Any]]:
    """
    Create override dictionaries from UI parameters.

    Args:
        ui_law_name: UI name of the law (e.g., "inkomstenbelasting")
        ui_parameters: Dict of UI parameter names to values

    Returns:
        Tuple of (overwrite_input, overwrite_definitions)
        - overwrite_input: Dict for input properties {service: {field: value}}
        - overwrite_definitions: Dict for definition constants {field: value}
    """
    config = get_law_config(ui_law_name)
    if not config:
        return {}, {}

    overwrite_input: dict[str, dict[str, Any]] = {}
    overwrite_definitions: dict[str, Any] = {}

    for param_name, value in ui_parameters.items():
        if value is None:
            continue

        mapping = config.parameters.get(param_name)
        if not mapping:
            continue

        # Transform value to engine format
        try:
            transformed = mapping.transform_to_engine(value)
        except Exception as e:
            import logging

            logging.warning(f"Transform failed for {ui_law_name}.{param_name}: {e}")
            continue

        # Add to appropriate override dict
        if mapping.override_type == "input":
            if mapping.service_name:
                if mapping.service_name not in overwrite_input:
                    overwrite_input[mapping.service_name] = {}
                overwrite_input[mapping.service_name][mapping.engine_field_name] = transformed
        elif mapping.override_type == "definition":
            overwrite_definitions[mapping.engine_field_name] = transformed

    return overwrite_input, overwrite_definitions
