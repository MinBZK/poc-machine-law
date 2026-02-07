"""Demo profile system for switching between burger and ondernemer demos.

Provides centralized profile configurations with BSN, KVK, default laws,
feature paths, and other demo-specific settings.
"""

import os

DEMO_PROFILES: dict[str, dict] = {
    "merijn": {
        "name": "Merijn",
        "type": "burger",
        "bsn": "100000001",
        "kvk": None,
        "default_law_path": "zorgtoeslagwet/TOESLAGEN-2025-01-01",
        "default_feature_path": "submodules/regelrecht-laws/laws/zorgtoeslagwet/TOESLAGEN-2025-01-01.feature",
        "default_law_tabs": [
            {
                "id": "law-tab-1",
                "path": "zorgtoeslagwet/TOESLAGEN-2025-01-01",
                "name": "Zorgtoeslag",
                "law": "zorgtoeslagwet",
                "service": "TOESLAGEN",
            },
        ],
        "zaaksysteem_service": "TOESLAGEN",
        "scenario_features": {},
        "scenario_metrics_laws": [],
    },
    "claudia": {
        "name": "Claudia",
        "type": "ondernemer",
        "bsn": "999999990",
        "kvk": "85234567",
        "default_law_path": "alcoholwet/vergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01",
        "default_feature_path": "submodules/regelrecht-laws/laws/algemene_plaatselijke_verordening/exploitatievergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01.feature",
        "default_law_tabs": [
            {
                "id": "law-tab-1",
                "path": "alcoholwet/vergunning/VWS-2024-01-01",
                "name": "Alcoholwet (nationaal)",
                "law": "alcoholwet/vergunning",
                "service": "VWS",
            },
            {
                "id": "law-tab-2",
                "path": "alcoholwet/vergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01",
                "name": "Alcoholwet (Rotterdam)",
                "law": "alcoholwet/vergunning",
                "service": "GEMEENTE_ROTTERDAM",
            },
        ],
        "zaaksysteem_service": "GEMEENTE_ROTTERDAM",
        "scenario_features": {
            "exploitatievergunning": {
                "path": "submodules/regelrecht-laws/laws/algemene_plaatselijke_verordening/exploitatievergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01.feature",
                "name": "Exploitatievergunning",
                "description": "Horeca exploitatievergunning",
            },
            "terrassen": {
                "path": "submodules/regelrecht-laws/laws/algemene_plaatselijke_verordening/terrassen/GEMEENTE_ROTTERDAM-2024-01-01.feature",
                "name": "Terrasvergunning",
                "description": "Terrasvergunning bij horecabedrijf",
            },
        },
        "scenario_metrics_laws": [
            ("GEMEENTE_ROTTERDAM", "algemene_plaatselijke_verordening/exploitatievergunning"),
            ("GEMEENTE_ROTTERDAM", "algemene_plaatselijke_verordening/terrassen"),
        ],
    },
}

DEFAULT_PROFILE = "merijn"


class DemoProfiles:
    """Manage demo profile selection via environment variable."""

    ENV_KEY = "DEMO_PROFILE"

    @classmethod
    def get_active_profile_name(cls) -> str:
        """Get the name of the currently active profile."""
        return os.environ.get(cls.ENV_KEY, DEFAULT_PROFILE)

    @classmethod
    def get_active_profile(cls) -> dict:
        """Get the full config dict for the active profile."""
        name = cls.get_active_profile_name()
        return DEMO_PROFILES.get(name, DEMO_PROFILES[DEFAULT_PROFILE])

    @classmethod
    def set_active_profile(cls, profile_name: str) -> None:
        """Set the active demo profile."""
        if profile_name not in DEMO_PROFILES:
            raise ValueError(f"Unknown profile: {profile_name}. Available: {list(DEMO_PROFILES.keys())}")
        os.environ[cls.ENV_KEY] = profile_name

    @classmethod
    def get_all_profiles(cls) -> dict[str, dict]:
        """Get all available profiles."""
        return DEMO_PROFILES


def get_demo_bsn() -> str:
    """Get the BSN for the active demo profile."""
    return DemoProfiles.get_active_profile()["bsn"]


def get_demo_kvk() -> str | None:
    """Get the KVK number for the active demo profile (None for burger)."""
    return DemoProfiles.get_active_profile()["kvk"]


def get_demo_profile_type() -> str:
    """Get the profile type ('burger' or 'ondernemer') for the active profile."""
    return DemoProfiles.get_active_profile()["type"]
