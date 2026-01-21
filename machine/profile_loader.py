"""
Profile loader module for loading test profiles from YAML files.
"""

import logging
from datetime import datetime
from pathlib import Path
from typing import Any

import yaml
from dateutil.relativedelta import relativedelta

logger = logging.getLogger(__name__)


def load_profiles_from_yaml(yaml_path: str | Path) -> dict[str, dict[str, Any]]:
    """
    Load profiles from a YAML file.

    Args:
        yaml_path: Path to the YAML file containing profiles data

    Returns:
        Dictionary mapping BSN/KVK numbers to profile data

    The YAML file should have the structure:
        globalServices:
          SERVICE_NAME:
            table_name:
              - data rows...
        profiles:
          BSN_OR_KVK:
            name: "Profile Name"
            description: "Profile description"
            sources:
              SERVICE_NAME:
                table_name:
                  - data rows...
    """
    yaml_path = Path(yaml_path)

    if not yaml_path.exists():
        raise FileNotFoundError(f"Profile YAML file not found: {yaml_path}")

    logger.info(f"Loading profiles from {yaml_path}")

    with open(yaml_path) as f:
        data = yaml.safe_load(f)

    if not data or "profiles" not in data:
        raise ValueError(f"Invalid profile YAML file: {yaml_path}. Must contain 'profiles' key.")

    profiles = data["profiles"]
    # Note: globalServices are now handled separately in factory.py to avoid duplication
    # We don't merge them into profiles here anymore

    logger.info(f"Successfully loaded {len(profiles)} profiles")

    # Add properties (badges) to each profile
    # Merge static properties from YAML with dynamically generated ones
    for bsn, profile in profiles.items():
        static_properties = profile.get("properties", [])
        dynamic_properties = get_profile_properties(profile)
        profile["properties"] = static_properties + dynamic_properties

    return profiles


def get_profile_properties(profile: dict) -> list[str]:
    """Extract key properties from a profile with emoji representations"""
    properties = []

    # Check if sources and RvIG data exist
    if not profile.get("sources") or not profile["sources"].get("RvIG"):
        return properties

    rvig_data = profile["sources"]["RvIG"]

    # Extract person data
    person_data = next(iter(rvig_data.get("personen", [])), {})
    if not person_data:
        return properties

    # Add nationality
    nationality = person_data.get("nationaliteit")
    if nationality:
        if nationality == "NEDERLANDS":
            properties.append("🇳🇱 Nederlands")
        elif nationality == "DUITS":
            properties.append("🇩🇪 Duits")
        elif nationality == "MAROKKAANS":
            properties.append("🇲🇦 Marokkaans")
        else:
            properties.append(f"🌍 {nationality}")

    # Add age
    if "geboortedatum" in person_data:
        birth_date_str = person_data["geboortedatum"]
        birth_date = datetime.strptime(birth_date_str, "%Y-%m-%d")
        current_date = datetime.now()
        age = relativedelta(current_date, birth_date).years
        properties.append(f"🗓️ {age} jaar")

    # Add children
    children_data = rvig_data.get("CHILDREN_DATA", [])
    for child_entry in children_data:
        if "kinderen" in child_entry:
            num_children = len(child_entry["kinderen"])
            if num_children == 1:
                properties.append("👶 1 kind")
            elif num_children > 1:
                properties.append(f"👨‍👩‍👧‍👦 {num_children} kinderen")

    # Add housing status
    address_data = next(iter(rvig_data.get("verblijfplaats", [])), {})
    if address_data:
        address_type = address_data.get("type")
        if address_type == "WOONADRES":
            properties.append("🏠 Vast woonadres")
        elif address_type == "BRIEFADRES":
            properties.append("📫 Briefadres")

    # Add work status
    is_entrepreneur = False
    if "KVK" in profile["sources"]:
        kvk_data = profile["sources"]["KVK"]
        if any(entry.get("waarde") for entry in kvk_data.get("is_entrepreneur", [])):
            is_entrepreneur = True
            properties.append("💼 ZZP'er")

    if "UWV" in profile["sources"]:
        uwv_data = profile["sources"]["UWV"]
        if "arbeidsverhoudingen" in uwv_data:
            for relation in uwv_data["arbeidsverhoudingen"]:
                if relation.get("dienstverband_type") != "GEEN" and not is_entrepreneur:
                    properties.append("👔 In loondienst")

    # Add student status
    if "DUO" in profile["sources"]:
        duo_data = profile["sources"]["DUO"]
        if "inschrijvingen" in duo_data:
            for enrollment in duo_data["inschrijvingen"]:
                if enrollment.get("onderwijssoort") != "GEEN":
                    properties.append("🎓 Student")

    # Add disability status
    if "UWV" in profile["sources"] and "arbeidsongeschiktheid" in profile["sources"]["UWV"]:
        for disability in profile["sources"]["UWV"]["arbeidsongeschiktheid"]:
            percentage = disability.get("percentage")
            if percentage:
                properties.append(f"♿ {percentage}% arbeidsongeschikt")

    return properties


def get_project_root() -> Path:
    """Get the project root directory."""
    # Start from this file's location and go up to find project root
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "data").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()
