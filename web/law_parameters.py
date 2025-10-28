"""Utility to extract default law parameters from YAML files using the machine Services."""

import logging
from typing import Any

from machine.law_parameter_config import get_all_law_configs
from machine.service import Services

logger = logging.getLogger(__name__)


def get_auto_discovered_parameters() -> dict[str, dict[str, Any]]:
    """
    Get ALL parameter NAMES from auto-discovery.

    Returns dictionary mapping law UI names to their parameter names with None values.
    Actual values will be read in the simulation subprocess to avoid Services conflicts.

    Includes BOTH definition and input parameters (all overridable parameters).
    """
    try:
        configs = get_all_law_configs()
        parameters = {}

        for ui_name, config in configs.items():
            law_params = {}

            # Include ALL parameters (both definition and input)
            # Definition: Constants in YAML (tax rates, thresholds, etc.)
            # Input: Service references that can be overridden (standaardpremie, etc.)
            for param_name, mapping in config.parameters.items():
                # Use None as placeholder - actual values shown in subprocess
                law_params[param_name] = None

            if law_params:
                parameters[ui_name] = law_params

        logger.info(f"Auto-discovered {sum(len(p) for p in parameters.values())} parameters across {len(parameters)} laws")
        return parameters

    except Exception as e:
        logger.error(f"Error in auto-discovery: {e}")
        return {}


def get_default_law_parameters_subprocess(simulation_date: str = "2025-01-01") -> dict[str, dict[str, Any]]:
    """
    Get default parameter values via subprocess to avoid Services initialization conflicts.

    This calls get_default_law_parameters() in a subprocess to avoid eventsourcing
    registration conflicts with the main web process.

    Args:
        simulation_date: Date to use for selecting law versions

    Returns:
        Dict mapping law UI names to their parameters with proper unit conversions

    Raises:
        RuntimeError: If subprocess fails or returns an error
    """
    import subprocess
    import json

    # Create a simple Python script to run in subprocess
    script = f"""
import json
from web.law_parameters import get_default_law_parameters

try:
    params = get_default_law_parameters("{simulation_date}")
    print(json.dumps(params))
except Exception as e:
    import traceback
    import sys
    print(json.dumps({{"error": str(e), "traceback": traceback.format_exc()}}), file=sys.stderr)
    sys.exit(1)
"""

    result = subprocess.run(
        ["uv", "run", "python", "-c", script],
        capture_output=True,
        text=True,
        check=False,
        timeout=30,
    )

    if result.returncode != 0:
        error_msg = f"Subprocess failed with code {result.returncode}: {result.stderr}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    if not result.stdout.strip():
        error_msg = "Subprocess produced no output"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    data = json.loads(result.stdout)
    if "error" in data:
        error_msg = f"Subprocess error: {data['error']}\n{data.get('traceback', '')}"
        logger.error(error_msg)
        raise RuntimeError(error_msg)

    return data


def get_default_law_parameters(simulation_date: str = "2025-01-01") -> dict[str, dict[str, Any]]:
    """
    Extract default parameter values from law YAML files using the Services system.

    This reads directly from the YAML definitions through the RulesEngine,
    ensuring we have a single source of truth. Uses auto-discovery to find ALL
    overridable parameters (both definition and input types).

    WARNING: This function initializes Services which can cause eventsourcing conflicts
    if called from the main web process. Use get_default_law_parameters_subprocess() instead
    when calling from web routes.

    Args:
        simulation_date: Date to use for selecting law versions

    Returns:
        Dict mapping law UI names to their parameters with proper unit conversions
    """
    try:
        # Import here to avoid circular dependency and to get fresh modules
        from machine.law_parameter_config import discover_law_parameters_with_services
        from machine.utils import RuleResolver

        # Create Services instance ONCE
        services = Services(simulation_date)

        # Discover laws and their parameters manually without using the global registry
        # This avoids the double Services initialization conflict
        resolver = RuleResolver()
        service_laws = resolver.get_discoverable_service_laws("CITIZEN")

        parameters = {}

        # Discover parameters for each law
        for service_name, laws in service_laws.items():
            for law_name in laws:
                try:
                    # Discover parameters using the shared Services instance
                    config = discover_law_parameters_with_services(law_name, service_name, services)
                    if not config or not config.parameters:
                        continue

                    ui_name = config.ui_name
                    parameters[ui_name] = {}

                    # Get the engine for this law
                    try:
                        engine = services.services[service_name]._get_engine(law_name, simulation_date)
                    except Exception as e:
                        logger.warning(f"Could not load engine for {ui_name}: {e}")
                        continue

                    # Extract values for each parameter
                    for param_name, mapping in config.parameters.items():
                        try:
                            if mapping.override_type == "definition":
                                # Get from engine definitions
                                raw_value = engine.definitions.get(mapping.engine_field_name)
                                if isinstance(raw_value, dict):
                                    raw_value = raw_value.get("value")
                                if raw_value is not None:
                                    # Transform to UI format
                                    parameters[ui_name][param_name] = mapping.transform_from_engine(raw_value)

                            elif mapping.override_type == "input":
                                # For input parameters with service_reference, resolve from the source law
                                if mapping.service_name:
                                    try:
                                        # Find the property spec in the original law's engine
                                        # Try multiple case variations
                                        prop_spec = engine.property_specs.get(param_name)
                                        if not prop_spec:
                                            prop_spec = engine.property_specs.get(param_name.upper())
                                        if not prop_spec:
                                            prop_spec = engine.property_specs.get(mapping.engine_field_name)
                                        if not prop_spec:
                                            prop_spec = engine.property_specs.get(mapping.engine_field_name.upper())

                                        if prop_spec and "service_reference" in prop_spec:
                                            service_ref = prop_spec["service_reference"]
                                            ref_service = service_ref.get("service")
                                            ref_law = service_ref.get("law")
                                            ref_field = service_ref.get("field", mapping.ui_param_name)

                                            if ref_service and ref_law and ref_service in services.services:
                                                # Load the referenced law's engine
                                                ref_engine = services.services[ref_service]._get_engine(ref_law, simulation_date)

                                                # Try to get value from definitions (try exact matches first, then fuzzy)
                                                raw_value = ref_engine.definitions.get(ref_field)
                                                if raw_value is None:
                                                    raw_value = ref_engine.definitions.get(ref_field.upper())

                                                # If still not found, search for keys that start with the field name
                                                # (handles cases like STANDAARDPREMIE_2025)
                                                if raw_value is None:
                                                    field_upper = ref_field.upper()
                                                    for def_key in ref_engine.definitions:
                                                        if def_key.upper().startswith(field_upper):
                                                            raw_value = ref_engine.definitions[def_key]
                                                            logger.debug(f"Found fuzzy match: {ref_field} -> {def_key}")
                                                            break

                                                if isinstance(raw_value, dict):
                                                    raw_value = raw_value.get("value")

                                                if raw_value is not None:
                                                    # Transform to UI format
                                                    parameters[ui_name][param_name] = mapping.transform_from_engine(raw_value)
                                                    logger.debug(f"Resolved {ui_name}.{param_name} from {ref_service}.{ref_law}.{ref_field} = {raw_value}")
                                                else:
                                                    logger.debug(f"No value found for {ui_name}.{param_name} in {ref_service}.{ref_law}")
                                                    parameters[ui_name][param_name] = None
                                            else:
                                                logger.debug(f"Service reference incomplete for {ui_name}.{param_name}")
                                                parameters[ui_name][param_name] = None
                                        else:
                                            logger.debug(f"No service_reference in spec for {ui_name}.{param_name}")
                                            parameters[ui_name][param_name] = None
                                    except Exception as e:
                                        logger.debug(f"Could not resolve service reference for {ui_name}.{param_name}: {e}")
                                        parameters[ui_name][param_name] = None
                                else:
                                    # Input parameter without service_name
                                    parameters[ui_name][param_name] = None

                        except Exception as e:
                            logger.debug(f"Could not extract {ui_name}.{param_name}: {e}")
                            parameters[ui_name][param_name] = None

                except Exception as e:
                    logger.debug(f"Could not discover parameters for {service_name}.{law_name}: {e}")

        logger.info(f"Extracted default values for {sum(len(p) for p in parameters.values())} parameters across {len(parameters)} laws")
        return parameters

    except Exception as e:
        logger.error(f"Error in get_default_law_parameters: {e}")
        raise RuntimeError(f"Failed to get law parameters: {e}") from e


def get_default_law_parameters_old(simulation_date: str = "2025-01-01") -> dict[str, dict[str, Any]]:
    """
    OLD IMPLEMENTATION - Kept for reference, should be removed after testing.

    Extract default parameter values from law YAML files using hardcoded law list.
    """
    parameters = {
        "zorgtoeslag": {},
        "huurtoeslag": {},
        "kinderopvang": {},
        "algemeneouderdoms": {},
        "bijstand": {},
        "inkomstenbelasting": {},
        "kies": {},
    }

    try:
        services = Services(simulation_date)

        # Zorgtoeslag - get standaardpremie from regulation
        try:
            engine = services.services["VWS"]._get_engine(
                "zorgtoeslagwet/regelingen/regeling_vaststelling_standaardpremie_en_bestuursrechtelijke_premies",
                simulation_date,
            )
            definitions = engine.definitions
            # STANDAARDPREMIE_2025 is in eurocents yearly, convert to euros monthly
            standaard_premie_yearly_cents = definitions.get("STANDAARDPREMIE_2025", {})
            if isinstance(standaard_premie_yearly_cents, dict):
                standaard_premie_yearly_cents = standaard_premie_yearly_cents.get("value", 211200)
            parameters["zorgtoeslag"]["standaardpremie"] = round(standaard_premie_yearly_cents / 100 / 12, 2)
        except Exception as e:
            logger.warning(f"Error loading zorgtoeslag parameters: {e}")
            parameters["zorgtoeslag"]["standaardpremie"] = 176  # fallback

        # Huurtoeslag
        try:
            engine = services.services["TOESLAGEN"]._get_engine("wet_op_de_huurtoeslag", simulation_date)
            definitions = engine.definitions
            # TODO: Extract actual definitions when they exist in YAML
            parameters["huurtoeslag"]["max_huur"] = 879  # Default for now
            parameters["huurtoeslag"]["basishuur"] = 200  # Default for now
        except Exception as e:
            logger.warning(f"Error loading huurtoeslag parameters: {e}")
            parameters["huurtoeslag"]["max_huur"] = 879
            parameters["huurtoeslag"]["basishuur"] = 200

        # Kinderopvang
        try:
            engine = services.services["TOESLAGEN"]._get_engine("wet_kinderopvang", simulation_date)
            definitions = engine.definitions
            # TODO: Extract actual definitions when they exist in YAML
            parameters["kinderopvang"]["uurprijs"] = 9.27
            parameters["kinderopvang"]["max_uren"] = 230
        except Exception as e:
            logger.warning(f"Error loading kinderopvang parameters: {e}")
            parameters["kinderopvang"]["uurprijs"] = 9.27
            parameters["kinderopvang"]["max_uren"] = 230

        # Algemene Ouderdomswet
        try:
            engine = services.services["SVB"]._get_engine("algemene_ouderdomswet", simulation_date)
            definitions = engine.definitions
            # TODO: Extract actual definitions when they exist in YAML
            parameters["algemeneouderdoms"]["pensioenleeftijd"] = 67
            parameters["algemeneouderdoms"]["basisbedrag"] = 1461
        except Exception as e:
            logger.warning(f"Error loading algemeneouderdoms parameters: {e}")
            parameters["algemeneouderdoms"]["pensioenleeftijd"] = 67
            parameters["algemeneouderdoms"]["basisbedrag"] = 1461

        # Bijstand
        try:
            engine = services.services["GEMEENTE_AMSTERDAM"]._get_engine(
                "participatiewet/bijstand", simulation_date
            )
            definitions = engine.definitions
            # Extract norms (in eurocents yearly, convert to euros monthly)
            norm_alleenstaand = definitions.get("NORM_ALLEENSTAAND", {})
            if isinstance(norm_alleenstaand, dict):
                norm_alleenstaand = norm_alleenstaand.get("value", 145200)
            norm_gehuwd = definitions.get("NORM_GEHUWDEN", {})
            if isinstance(norm_gehuwd, dict):
                norm_gehuwd = norm_gehuwd.get("value", 207500)
            parameters["bijstand"]["norm_alleenstaand"] = round(norm_alleenstaand / 100 / 12, 2)
            parameters["bijstand"]["norm_gehuwd"] = round(norm_gehuwd / 100 / 12, 2)
        except Exception as e:
            logger.warning(f"Error loading bijstand parameters: {e}")
            parameters["bijstand"]["norm_alleenstaand"] = 1210
            parameters["bijstand"]["norm_gehuwd"] = 1729

        # Inkomstenbelasting - READ FROM YAML DEFINITIONS
        try:
            engine = services.services["BELASTINGDIENST"]._get_engine("wet_inkomstenbelasting", simulation_date)
            definitions = engine.definitions

            # BOX1_TARIEF1 is decimal (0.3693), convert to percentage (36.93)
            tarief1 = definitions.get("BOX1_TARIEF1", 0.3693)
            parameters["inkomstenbelasting"]["box1_tarief1"] = round(tarief1 * 100, 2)

            # BOX1_TARIEF2 is decimal (0.4953), convert to percentage (49.53)
            tarief2 = definitions.get("BOX1_TARIEF2", 0.4953)
            parameters["inkomstenbelasting"]["box1_tarief2"] = round(tarief2 * 100, 2)

            # BOX1_SCHIJF1_GRENS is eurocents (7457300), convert to euros (74573)
            grens1 = definitions.get("BOX1_SCHIJF1_GRENS", 7457300)
            parameters["inkomstenbelasting"]["box1_schijf1_grens"] = round(grens1 / 100)

            # ALGEMENE_HEFFINGSKORTING_MAX is eurocents (310400), convert to euros (3104)
            heffingskorting = definitions.get("ALGEMENE_HEFFINGSKORTING_MAX", 310400)
            parameters["inkomstenbelasting"]["algemene_heffingskorting_max"] = round(heffingskorting / 100)
        except Exception as e:
            logger.warning(f"Error loading inkomstenbelasting parameters: {e}")
            # Fallback to actual YAML values
            parameters["inkomstenbelasting"]["box1_tarief1"] = 36.93
            parameters["inkomstenbelasting"]["box1_tarief2"] = 49.53
            parameters["inkomstenbelasting"]["box1_schijf1_grens"] = 74573
            parameters["inkomstenbelasting"]["algemene_heffingskorting_max"] = 3104

        # Kieswet
        try:
            engine = services.services["KIESRAAD"]._get_engine("kieswet", simulation_date)
            definitions = engine.definitions
            # TODO: Extract actual definition when it exists in YAML
            parameters["kies"]["min_leeftijd"] = 18
        except Exception as e:
            logger.warning(f"Error loading kies parameters: {e}")
            parameters["kies"]["min_leeftijd"] = 18

    except Exception as e:
        logger.error(f"Error initializing Services: {e}")
        raise RuntimeError(f"Failed to initialize Services for law parameters: {e}") from e

    return parameters
