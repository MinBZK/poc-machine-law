"""
Law parameter configuration registry for mapping UI parameters to engine overrides.

This module automatically discovers law parameters from YAML files and builds
transformation mappings based on type specifications. It supports both input overrides
(for properties with service_reference) and definition overrides (for constants).
"""

import logging
from typing import Any, Callable, Literal

from machine.service import Services
from machine.utils import RuleResolver

logger = logging.getLogger(__name__)


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
_REGISTRY_INITIALIZED: bool = False


def _ensure_registry_initialized() -> None:
    """Lazily initialize the registry on first access."""
    global _REGISTRY_INITIALIZED
    if not _REGISTRY_INITIALIZED:
        try:
            auto_populate_registry()
            logger.info(f"Auto-populated law parameter registry with {len(_LAW_CONFIGS)} laws")
            _REGISTRY_INITIALIZED = True
        except Exception as e:
            logger.warning(f"Failed to auto-populate law parameter registry: {e}")
            # Mark as initialized even if it failed to avoid repeated attempts
            # This is especially important in subprocess contexts where Services
            # initialization may conflict with parent process
            _REGISTRY_INITIALIZED = True
            # Continue with empty registry if auto-discovery fails


def register_law(ui_name: str, law_name: str, service: str) -> LawConfig:
    """Register a law and return its configuration for adding parameters"""
    config = LawConfig(ui_name, law_name, service)
    _LAW_CONFIGS[ui_name] = config
    return config


def get_law_config(ui_name: str) -> LawConfig | None:
    """Get law configuration by UI name"""
    _ensure_registry_initialized()
    return _LAW_CONFIGS.get(ui_name)


def get_all_law_configs() -> dict[str, LawConfig]:
    """Get all law configurations"""
    _ensure_registry_initialized()
    return _LAW_CONFIGS


def find_law_config_by_technical_name(law_name: str) -> LawConfig | None:
    """Find law configuration by technical law name"""
    _ensure_registry_initialized()
    for config in _LAW_CONFIGS.values():
        if config.law_name == law_name:
            return config
    return None


# ==============================================================================
# AUTOMATIC PARAMETER DISCOVERY
# ==============================================================================


def derive_ui_name_from_law_name(law_name: str) -> str:
    """
    Automatically derive a UI-friendly name from a technical law name.

    Args:
        law_name: Technical law name (e.g., "wet_inkomstenbelasting", "participatiewet/bijstand")

    Returns:
        UI-friendly name derived using generic rules

    Examples:
        - "wet_inkomstenbelasting" → "inkomstenbelasting"
        - "participatiewet/bijstand" → "bijstand"
        - "wet_op_de_huurtoeslag" → "huurtoeslag"
        - "zorgtoeslagwet" → "zorgtoeslag"
    """
    # If it's a path, take the last component
    if "/" in law_name:
        law_name = law_name.split("/")[-1]

    # Remove common prefixes in order of specificity
    if law_name.startswith("wet_op_de_"):
        law_name = law_name[len("wet_op_de_"):]
    elif law_name.startswith("wet_"):
        law_name = law_name[len("wet_"):]

    # Remove "wet" suffix if present
    if law_name.endswith("wet"):
        law_name = law_name[:-len("wet")]

    # Clean up underscores
    law_name = law_name.strip("_")
    law_name = law_name.replace("_", "")

    return law_name


def infer_transformation_from_type_spec(param_name: str, value: Any, type_spec: dict | None = None) -> tuple[Callable, Callable]:
    """
    Infer transformation functions from parameter type specification.

    Returns:
        Tuple of (transform_to_engine, transform_from_engine)
    """
    # Default: no transformation
    to_engine = lambda x: x
    from_engine = lambda x: x

    if type_spec:
        unit = type_spec.get("unit")

        # Handle eurocent conversions
        if unit == "eurocent":
            # Check if this is a monthly value based on naming conventions
            if "standaardpremie" in param_name.lower() or "premie" in param_name.lower():
                # Monthly euros → yearly eurocents
                to_engine = lambda x: int(x * 12 * 100)
                from_engine = lambda x: round(x / 100 / 12, 2)
            else:
                # Regular euros → eurocents
                to_engine = lambda x: int(x * 100)
                from_engine = lambda x: round(x / 100)

        # Handle percentage/decimal conversions
        elif unit == "percentage":
            # Percentage (36.93) → decimal (0.3693)
            to_engine = lambda x: x / 100
            from_engine = lambda x: round(x * 100, 2)

    # Fallback: infer from value type and magnitude
    elif isinstance(value, (int, float)):
        # If value is between 0 and 1, likely a decimal percentage
        if 0 < value < 1:
            to_engine = lambda x: x / 100
            from_engine = lambda x: round(x * 100, 2)
        # If value is very large (> 1000), might be in eurocents
        elif value > 10000:
            to_engine = lambda x: int(x * 100)
            from_engine = lambda x: round(x / 100)

    return to_engine, from_engine


def discover_law_parameters_with_services(law_name: str, service: str, services: Services) -> LawConfig | None:
    """
    Automatically discover parameters from a law's YAML definition using a shared Services instance.

    Args:
        law_name: Technical law name (e.g., "wet_inkomstenbelasting")
        service: Service that evaluates this law (e.g., "BELASTINGDIENST")
        services: Shared Services instance to avoid re-initialization

    Returns:
        LawConfig with auto-discovered parameters
    """
    # Derive UI-friendly name automatically
    ui_name = derive_ui_name_from_law_name(law_name)

    # Create law config
    config = LawConfig(ui_name, law_name, service)

    # Load the law spec to get definitions
    engine = services.services[service]._get_engine(law_name, services.root_reference_date)

    # Discover definitions that could be overridden
    definitions = engine.definitions or {}
    output_specs = engine.output_specs or {}

    for def_name, def_value in definitions.items():
        # Extract actual value if it's a dict with 'value' key
        actual_value = def_value.get("value") if isinstance(def_value, dict) else def_value

        # Skip if not a numeric value
        if not isinstance(actual_value, (int, float)):
            continue

        # Create UI-friendly parameter name (just lowercase to preserve semantic prefixes)
        # We keep prefixes like box1_, box2_, norm_, etc. to prevent collisions
        ui_param_name = def_name.lower()

        # Try to find matching output spec for type information
        type_spec = None
        for output_name, spec in output_specs.items():
            if output_name.upper() == def_name or def_name in output_name.upper():
                type_spec = {
                    "unit": spec.unit,
                    "type": spec.type,
                    "precision": spec.precision
                }
                break

        # Infer transformations
        to_engine, from_engine = infer_transformation_from_type_spec(ui_param_name, actual_value, type_spec)

        # Create parameter mapping
        mapping = ParameterMapping(
            ui_param_name=ui_param_name,
            engine_field_name=def_name,
            override_type="definition",
            transform_to_engine=to_engine,
            transform_from_engine=from_engine,
        )

        config.add_parameter(mapping)
        logger.debug(f"Discovered parameter {law_name}.{ui_param_name} -> {def_name}")

    # Also check for input properties with service_reference
    for prop_name, prop_spec in engine.property_specs.items():
        if "service_reference" in prop_spec:
            service_ref = prop_spec["service_reference"]

            # Create UI-friendly name
            ui_param_name = prop_name.lower()

            # Infer transformations from type spec
            type_spec = None
            if prop_name in output_specs:
                spec = output_specs[prop_name]
                type_spec = {
                    "unit": spec.unit,
                    "type": spec.type,
                    "precision": spec.precision
                }

            to_engine, from_engine = infer_transformation_from_type_spec(ui_param_name, 0, type_spec)

            mapping = ParameterMapping(
                ui_param_name=ui_param_name,
                engine_field_name=service_ref.get("field", prop_name),
                override_type="input",
                service_name=service_ref.get("service"),
                transform_to_engine=to_engine,
                transform_from_engine=from_engine,
            )

            config.add_parameter(mapping)
            logger.debug(f"Discovered input parameter {law_name}.{ui_param_name} -> {service_ref}")

    logger.info(f"Auto-discovered {len(config.parameters)} parameters for {law_name}")
    return config


def discover_law_parameters(law_name: str, service: str, simulation_date: str = "2025-01-01") -> LawConfig | None:
    """
    Automatically discover parameters from a law's YAML definition.

    This is a convenience wrapper that creates a Services instance.
    For bulk discovery, use auto_populate_registry() instead to reuse a single Services instance.

    Args:
        law_name: Technical law name (e.g., "wet_inkomstenbelasting")
        service: Service that evaluates this law (e.g., "BELASTINGDIENST")
        simulation_date: Date to use for loading law version

    Returns:
        LawConfig with auto-discovered parameters
    """
    try:
        services = Services(simulation_date)
        return discover_law_parameters_with_services(law_name, service, services)
    except Exception as e:
        logger.warning(f"Could not auto-discover parameters for {law_name}: {e}")
        return None


def auto_populate_registry(simulation_date: str = "2025-01-01", discoverable_by: str = "CITIZEN") -> None:
    """
    Automatically populate the registry by discovering parameters from discoverable laws.

    This function discovers citizen-discoverable laws from the RuleResolver and attempts
    to auto-discover their parameters. No hardcoded law lists required!

    Args:
        simulation_date: Date to use for loading law versions
        discoverable_by: Filter to laws discoverable by this actor (default: "CITIZEN")
    """
    # Create Services instance once to avoid eventsourcing registration conflicts
    try:
        services = Services(simulation_date)
    except Exception as e:
        logger.error(f"Failed to initialize Services for auto-discovery: {e}")
        return

    # Discover citizen-discoverable laws from the resolver
    resolver = RuleResolver()
    service_laws = resolver.get_discoverable_service_laws(discoverable_by)

    # Iterate through all services and their laws
    for service_name, laws in service_laws.items():
        for law_name in laws:
            try:
                config = discover_law_parameters_with_services(law_name, service_name, services)
                if config and config.parameters:
                    # Only register if we found parameters
                    _LAW_CONFIGS[config.ui_name] = config
                    logger.debug(f"Registered {law_name} as {config.ui_name} with {len(config.parameters)} parameters")
            except Exception as e:
                logger.debug(f"Could not auto-discover parameters for {service_name}.{law_name}: {e}")


# ==============================================================================
# REGISTRY INITIALIZATION
# ==============================================================================

# Registry is now lazily initialized on first access via _ensure_registry_initialized()
# This avoids eventsourcing registration conflicts in subprocesses

# ==============================================================================
# MANUAL REGISTRATION (Fallback/Override)
# ==============================================================================
# If auto-discovery fails or you need to override specific parameters,
# you can manually register them here:
#
# Example:
# zorgtoeslag = register_law("zorgtoeslag", "zorgtoeslagwet", "TOESLAGEN")
# zorgtoeslag.add_parameter(
#     ParameterMapping(
#         ui_param_name="standaardpremie",
#         engine_field_name="standaardpremie",
#         override_type="input",
#         service_name="VWS",
#         transform_to_engine=lambda monthly_euros: int(monthly_euros * 12 * 100),
#         transform_from_engine=lambda yearly_cents: round(yearly_cents / 100 / 12, 2),
#     )
# )


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
