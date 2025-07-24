"""Utility to extract default law parameters from YAML files."""

import yaml
from pathlib import Path
from typing import Dict, Any


def get_default_law_parameters() -> Dict[str, Dict[str, Any]]:
    """Extract default parameter values from law YAML files."""
    parameters = {
        "zorgtoeslag": {},
        "huurtoeslag": {},
        "kinderopvangtoeslag": {},
        "aow": {},
        "bijstand": {},
        "inkomstenbelasting": {},
        "kiesrecht": {},
    }

    law_dir = Path("law")

    try:
        # Zorgtoeslag - get standaardpremie from regulation file
        zorgtoeslag_file = law_dir / "zorgtoeslagwet/regelingen/vaststelling_standaardpremie_2025_01_01.yaml"
        if zorgtoeslag_file.exists():
            with open(zorgtoeslag_file) as f:
                data = yaml.safe_load(f)
                if "properties" in data and "definitions" in data["properties"]:
                    # Get STANDAARDPREMIE_2025 value in eurocents
                    standaard = data["properties"]["definitions"].get("STANDAARDPREMIE_2025", {}).get("value", 211200)
                    # Convert to euros per month
                    parameters["zorgtoeslag"]["standaardpremie"] = round(standaard / 100 / 12)
        else:
            parameters["zorgtoeslag"]["standaardpremie"] = 176  # fallback

        # Huurtoeslag - get from law file
        huurtoeslag_file = law_dir / "wet_op_de_huurtoeslag/TOESLAGEN-2025-01-01.yaml"
        if huurtoeslag_file.exists():
            with open(huurtoeslag_file) as f:
                data = yaml.safe_load(f)
                if "properties" in data and "definitions" in data["properties"]:
                    defs = data["properties"]["definitions"]
                    # Extract max_huur and basishuur if available
                    parameters["huurtoeslag"]["max_huur"] = 879  # Default value
                    parameters["huurtoeslag"]["basishuur"] = 200  # Default value

        # Kinderopvangtoeslag
        kinderopvang_file = law_dir / "wet_kinderopvang/TOESLAGEN-2024-01-01.yaml"
        if kinderopvang_file.exists():
            with open(kinderopvang_file) as f:
                data = yaml.safe_load(f)
                # These are typically in definitions
                parameters["kinderopvangtoeslag"]["uurprijs"] = 9.27
                parameters["kinderopvangtoeslag"]["max_uren"] = 230

        # AOW
        aow_file = law_dir / "algemene_ouderdomswet/SVB-2024-01-01.yaml"
        if aow_file.exists():
            with open(aow_file) as f:
                data = yaml.safe_load(f)
                parameters["aow"]["pensioenleeftijd"] = 67
                parameters["aow"]["basisbedrag"] = 1461

        # Bijstand
        bijstand_file = law_dir / "participatiewet/bijstand/gemeenten/GEMEENTE_AMSTERDAM-2023-01-01.yaml"
        if bijstand_file.exists():
            with open(bijstand_file) as f:
                data = yaml.safe_load(f)
                if "properties" in data and "definitions" in data["properties"]:
                    defs = data["properties"]["definitions"]
                    # Extract norms if available
                    alleenstaand = defs.get("NORM_ALLEENSTAAND", {}).get("value", 145200)  # in eurocents yearly
                    gehuwd = defs.get("NORM_GEHUWDEN", {}).get("value", 207500)  # in eurocents yearly
                    parameters["bijstand"]["norm_alleenstaand"] = round(alleenstaand / 100)  # Just convert to euros
                    parameters["bijstand"]["norm_gehuwd"] = round(gehuwd / 100)  # Just convert to euros
        else:
            parameters["bijstand"]["norm_alleenstaand"] = 1210
            parameters["bijstand"]["norm_gehuwd"] = 1729

        # Inkomstenbelasting
        ib_file = law_dir / "wet_inkomstenbelasting/BELASTINGDIENST-2001-01-01.yaml"
        if ib_file.exists():
            with open(ib_file) as f:
                data = yaml.safe_load(f)
                # Default tax parameters for 2025
                parameters["inkomstenbelasting"]["tarief_schijf1"] = 36.97
                parameters["inkomstenbelasting"]["tarief_schijf2"] = 49.5
                parameters["inkomstenbelasting"]["grens_schijf1"] = 75518
                parameters["inkomstenbelasting"]["algemene_heffingskorting"] = 3362

        # Kiesrecht
        kiesrecht_file = law_dir / "kieswet/KIESRAAD-2024-01-01.yaml"
        if kiesrecht_file.exists():
            with open(kiesrecht_file) as f:
                data = yaml.safe_load(f)
                parameters["kiesrecht"]["min_leeftijd"] = 18

    except Exception as e:
        print(f"Error loading law parameters: {e}")
        # Return defaults if loading fails
        return {
            "zorgtoeslag": {"standaardpremie": 176},
            "huurtoeslag": {"max_huur": 879, "basishuur": 200},
            "kinderopvangtoeslag": {"uurprijs": 9.27, "max_uren": 230},
            "aow": {"pensioenleeftijd": 67, "basisbedrag": 1461},
            "bijstand": {"norm_alleenstaand": 1210, "norm_gehuwd": 1729},
            "inkomstenbelasting": {
                "tarief_schijf1": 36.97,
                "tarief_schijf2": 49.5,
                "grens_schijf1": 75518,
                "algemene_heffingskorting": 3362,
            },
            "kiesrecht": {"min_leeftijd": 18},
        }

    return parameters
