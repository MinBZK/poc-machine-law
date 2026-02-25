"""Demo profile system for switching between burger and ondernemer demos.

Provides centralized profile configurations with BSN, KVK, default laws,
feature paths, and other demo-specific settings.
"""

import os

from web.feature_flags import FeatureFlags

DEMO_PROFILES: dict[str, dict] = {
    "merijn": {
        "name": "Merijn",
        "type": "burger",
        "bsn": "100000001",
        "kvk": None,
        "default_law_path": "zorgtoeslagwet/TOESLAGEN-2025-01-01",
        "default_feature_path": "features/toeslagen/zorgtoeslagwet_TOESLAGEN-2025-01-01.feature",
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
        "feature_flags": {
            "DELEGATION": False,
            "AUTO_APPROVE_CLAIMS": False,
            "HARMONIZE": False,
        },
        "graph_selected_laws": [],
    },
    "claudia": {
        "name": "Claudia",
        "type": "ondernemer",
        "bsn": "999999990",
        "kvk": "85234567",
        "default_law_path": "alcoholwet/vergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01",
        "default_feature_path": "features/overig/alcoholwet_GEMEENTE_ROTTERDAM-2024-01-01.feature",
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
            {
                "id": "law-tab-3",
                "path": "omgevingswet/energiebesparing/informatieplicht/RVO-2024-01-01",
                "name": "Informatieplicht Energie",
                "law": "omgevingswet/energiebesparing/informatieplicht",
                "service": "RVO",
            },
            {
                "id": "law-tab-4",
                "path": "warenwet/haccp/NVWA-2024-01-01",
                "name": "HACCP Voedselveiligheid",
                "law": "warenwet/haccp",
                "service": "NVWA",
            },
        ],
        "zaaksysteem_service": "GEMEENTE_ROTTERDAM",
        "feature_flags": {
            "DELEGATION": True,
            "AUTO_APPROVE_CLAIMS": True,
            "HARMONIZE": True,
        },
        "graph_selected_laws": [
            "8a3f9b5c-4d2e-4f0a-b6c3-1e9d8f7a5b4c",
            "7c2e8f4a-3b9d-4e1f-a5c2-9d8b7e6f4a3c",
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

    @classmethod
    def apply_feature_flags(cls) -> None:
        """Apply the feature flags from the active profile via FeatureFlags.set()."""
        profile = cls.get_active_profile()
        for flag_name, value in profile.get("feature_flags", {}).items():
            FeatureFlags.set(flag_name, value)


def get_demo_bsn() -> str:
    """Get the BSN for the active demo profile."""
    return DemoProfiles.get_active_profile()["bsn"]


def get_demo_kvk() -> str | None:
    """Get the KVK number for the active demo profile (None for burger)."""
    return DemoProfiles.get_active_profile()["kvk"]


def get_demo_profile_type() -> str:
    """Get the profile type ('burger' or 'ondernemer') for the active profile."""
    return DemoProfiles.get_active_profile()["type"]
