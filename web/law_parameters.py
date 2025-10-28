"""Utility to extract default law parameters from YAML files using the machine Services."""

import logging
from typing import Any

from machine.service import Services

logger = logging.getLogger(__name__)


def get_default_law_parameters(simulation_date: str = "2025-01-01") -> dict[str, dict[str, Any]]:
    """
    Extract default parameter values from law YAML files using the Services system.

    This reads directly from the YAML definitions through the RulesEngine,
    ensuring we have a single source of truth.

    Args:
        simulation_date: Date to use for selecting law versions

    Returns:
        Dict mapping law UI names to their parameters with proper unit conversions
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
            parameters["inkomstenbelasting"]["tarief_schijf1"] = round(tarief1 * 100, 2)

            # BOX1_TARIEF2 is decimal (0.4953), convert to percentage (49.53)
            tarief2 = definitions.get("BOX1_TARIEF2", 0.4953)
            parameters["inkomstenbelasting"]["tarief_schijf2"] = round(tarief2 * 100, 2)

            # BOX1_SCHIJF1_GRENS is eurocents (7457300), convert to euros (74573)
            grens1 = definitions.get("BOX1_SCHIJF1_GRENS", 7457300)
            parameters["inkomstenbelasting"]["grens_schijf1"] = round(grens1 / 100)

            # ALGEMENE_HEFFINGSKORTING_MAX is eurocents (310400), convert to euros (3104)
            heffingskorting = definitions.get("ALGEMENE_HEFFINGSKORTING_MAX", 310400)
            parameters["inkomstenbelasting"]["algemene_heffingskorting"] = round(heffingskorting / 100)
        except Exception as e:
            logger.warning(f"Error loading inkomstenbelasting parameters: {e}")
            # Fallback to actual YAML values (not the incorrect hardcoded ones!)
            parameters["inkomstenbelasting"]["tarief_schijf1"] = 36.93
            parameters["inkomstenbelasting"]["tarief_schijf2"] = 49.53
            parameters["inkomstenbelasting"]["grens_schijf1"] = 74573
            parameters["inkomstenbelasting"]["algemene_heffingskorting"] = 3104

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
        # Return fallback defaults
        return {
            "zorgtoeslag": {"standaardpremie": 176},
            "huurtoeslag": {"max_huur": 879, "basishuur": 200},
            "kinderopvang": {"uurprijs": 9.27, "max_uren": 230},
            "algemeneouderdoms": {"pensioenleeftijd": 67, "basisbedrag": 1461},
            "bijstand": {"norm_alleenstaand": 1210, "norm_gehuwd": 1729},
            "inkomstenbelasting": {
                "tarief_schijf1": 36.93,
                "tarief_schijf2": 49.53,
                "grens_schijf1": 74573,
                "algemene_heffingskorting": 3104,
            },
            "kies": {"min_leeftijd": 18},
        }

    return parameters
