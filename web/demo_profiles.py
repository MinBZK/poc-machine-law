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
        "portal_tab_label": "Burger.nl",
        "portal_heading": "Waar heb ik recht op? Wat zijn mijn plichten?",
        "portal_subtitle": "Bekijk hier uw toeslagen, uitkeringen, aangiften, en andere regelingen van de overheid.",
        "feature_flags": {
            "DELEGATION": False,
            "AUTO_APPROVE_CLAIMS": False,
            "HARMONIZE": False,
            "SIMULATION": True,
        },
        "graph_selected_laws": [
            "cdd0ec9f-4975-4969-9d8a-808f2d6abfc9",  # Inkomstenbelasting
            "60e71675-38bc-4297-87ac-0c145613e481",  # Zorgtoeslag (2025)
            "a611a7ea-98d5-42f5-a05c-475b1be4590e",  # Huurtoeslag (2025)
            "5d8e4b3a-6f9c-4a2d-8e7b-1c9f2a5b8d3e",  # Kindgebonden Budget (2025)
            "f8e7d6c5-4321-4f0f-bbbb-123456789abc",  # Kinderopvangtoeslag
            "2b4c6d8e-1a3f-4e5b-8c7d-9f0e1a2b3c4d",  # Inkomensafhankelijke bijdrage Zvw
            "7d4e8f2a-3b6c-4a9d-8e1f-5c2d7a9b4e3f",  # Bbz 2004
            "8a7f3c2d-9e4b-4f5a-b8c1-2d6e9f1a3b7c",  # Werkloosheidswet
            "b1d3a15b-45a2-44a3-b26a-d636785032c0",  # Bijstand Amsterdam
            "13dc8a31-91eb-4598-998c-012c9129b9ea",  # AOW-uitkering
            "3c5d7e9f-2b4a-4f6c-9d8e-0a1b2c3d4e5f",  # Anw-uitkering
            "4d6e8f0a-3c5b-4e7f-a8b9-1c2d3e4f5a6b",  # AIO-aanvulling
            "8a3f5c2d-4e6b-4a1f-9c8d-7e2f3a4b5c6d",  # Pensioenuitkering
            "96d926a0-b45f-4cf3-92af-01b167221a00",  # Kiesrecht
        ],
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
                "path": "handelsregisterwet/jaarrekening/KVK-2024-01-01",
                "name": "Jaarrekening (KVK)",
                "law": "handelsregisterwet/jaarrekening",
                "service": "KVK",
            },
            {
                "id": "law-tab-5",
                "path": "warenwet/meldplicht/NVWA-2024-01-01",
                "name": "Meldplicht Voedselveiligheid",
                "law": "warenwet/meldplicht",
                "service": "NVWA",
            },
        ],
        "zaaksysteem_service": "GEMEENTE_ROTTERDAM",
        "portal_tab_label": "Overheid.nl",
        "portal_heading": "Welke regelingen passen bij mijn bedrijf?",
        "portal_subtitle": (
            "Bekijk beschikbare subsidies, rapportageverplichtingen, vergunningen,"
            " wetten en andere ondernemersregelingen."
        ),
        "feature_flags": {
            "DELEGATION": True,
            "AUTO_APPROVE_CLAIMS": True,
            "HARMONIZE": True,
            "SIMULATION": False,
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
