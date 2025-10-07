"""
Profile loader module for loading test profiles from YAML files.
"""

import logging
from pathlib import Path
from typing import Any

import yaml

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

    with open(yaml_path, "r") as f:
        data = yaml.safe_load(f)

    if not data or "profiles" not in data:
        raise ValueError(f"Invalid profile YAML file: {yaml_path}. Must contain 'profiles' key.")

    profiles = data["profiles"]
    # Note: globalServices are now handled separately in factory.py to avoid duplication
    # We don't merge them into profiles here anymore

    logger.info(f"Successfully loaded {len(profiles)} profiles")

    return profiles


def get_project_root() -> Path:
    """Get the project root directory."""
    # Start from this file's location and go up to find project root
    current = Path(__file__).parent
    while current != current.parent:
        if (current / "data").exists() or (current / "pyproject.toml").exists():
            return current
        current = current.parent
    return Path.cwd()
