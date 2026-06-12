"""Demo profile system for switching between burger and ondernemer demos.

Provides centralized profile configurations with BSN, KVK, default laws,
feature paths, and other demo-specific settings.

Law visibility per profile is controlled by two whitelists:
- sidebar_laws: law paths shown in the Wetten tab sidebar
- graph_laws: law paths shown in the Graaf analyse tab
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
        # Wetten tab sidebar: None = show all laws
        "sidebar_laws": None,
        # Graaf analyse: no whitelist = show all non-hidden laws
        "graph_laws": None,
        # Pre-select the detentiestatus → zorgtoeslag → verzekeringsstatus chain (UUIDs)
        # Cleared: UUIDs may change across schema versions; empty list selects all laws
        "graph_selected_laws": [],
        # Laws disabled for the portal/burger tab (feature flags)
        "disabled_laws": {
            "BELASTINGDIENST": ["zorgverzekeringswet/bijdrage", "zvw", "zvw/werkgeversbijdrage"],
            "GEMEENTE_ROTTERDAM": [
                "alcoholwet/vergunning/rotterdam",
                "algemene_plaatselijke_verordening/exploitatievergunning",
                "algemene_plaatselijke_verordening/terrassen",
                "algemene_plaatselijke_verordening/ontheffingspas_geluid",
                "verordening_precariobelasting",
            ],
            "KVK": ["handelsregisterwet/jaarrekening"],
            "NVWA": ["warenwet/haccp", "warenwet/meldplicht"],
            "PENSIOENFONDS": ["pensioenwet"],
            "RVO": [
                "omgevingswet/werkgebonden_personenmobiliteit",
                "omgevingswet/energiebesparing/informatieplicht",
            ],
            "SVB": [
                "algemene_kinderbijslagwet",
                "algemene_nabestaandenwet",
                "algemene_ouderdomswet/leeftijdsbepaling",
                "algemene_ouderdomswet_gegevens",
                "participatiewet/aio",
            ],
            "TOESLAGEN": ["wet_kinderopvang"],
        },
    },
    "claudia": {
        "name": "Claudia",
        "type": "ondernemer",
        "bsn": "999999990",
        "kvk": "85234567",
        "default_law_path": "verordening_precariobelasting/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01",
        "default_feature_path": "features/overig/precariobelasting_GEMEENTE_ROTTERDAM-2024-01-01.feature",
        "default_law_tabs": [
            {
                "id": "law-tab-1",
                "path": "verordening_precariobelasting/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01",
                "name": "Precariobelasting",
                "law": "verordening_precariobelasting",
                "service": "GEMEENTE_ROTTERDAM",
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
        # Wetten tab sidebar: only precariobelasting
        "sidebar_laws": [
            "verordening_precariobelasting/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01",
        ],
        # Graaf analyse: no whitelist = show all non-hidden laws
        "graph_laws": None,
        # Pre-select the horeca Rotterdam law chain (UUIDs)
        # Cleared: UUIDs may change across schema versions; empty list selects all laws
        "graph_selected_laws": [],
        # Laws disabled for the portal tab (feature flags)
        "disabled_laws": {
            "BELASTINGDIENST": ["zorgverzekeringswet/bijdrage", "zvw", "zvw/werkgeversbijdrage"],
            "DUO": ["wet_studiefinanciering"],
            "GEMEENTE_AMSTERDAM": ["participatiewet/bijstand/amsterdam"],
            "KIESRAAD": ["kieswet"],
            "PENSIOENFONDS": ["pensioenwet"],
            "RVO": ["omgevingswet/werkgebonden_personenmobiliteit"],
            "SVB": [
                "algemene_kinderbijslagwet",
                "algemene_nabestaandenwet",
                "algemene_ouderdomswet/leeftijdsbepaling",
                "algemene_ouderdomswet_gegevens",
                "participatiewet/aio",
            ],
            "SZW": ["participatiewet/bijstand", "besluit_bijstandverlening_zelfstandigen"],
            "TOESLAGEN": [
                "zorgtoeslagwet",
                "wet_op_de_huurtoeslag",
                "wet_op_het_kindgebonden_budget",
                "wet_kinderopvang",
            ],
            "UWV": [
                "werkloosheidswet",
                "ziektewet",
                "uwv_toetsingsinkomen",
                "uwv_werkgegevens",
                "wet_werk_en_inkomen_naar_arbeidsvermogen",
                "wet_structuur_uitvoeringsorganisatie_werk_en_inkomen",
                "wet_inkomstenbelasting/toetsingsinkomen",
            ],
        },
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
        """Apply the feature flags and law visibility from the active profile."""
        profile = cls.get_active_profile()
        for flag_name, value in profile.get("feature_flags", {}).items():
            FeatureFlags.set(flag_name, value)

        # Reset all law flags, then disable profile-specific laws
        FeatureFlags.reset_law_flags()
        for service, laws in profile.get("disabled_laws", {}).items():
            for law in laws:
                FeatureFlags.disable_law(service, law)


def get_demo_bsn() -> str:
    """Get the BSN for the active demo profile."""
    return DemoProfiles.get_active_profile()["bsn"]


def get_demo_kvk() -> str | None:
    """Get the KVK number for the active demo profile (None for burger)."""
    return DemoProfiles.get_active_profile()["kvk"]


def get_demo_profile_type() -> str:
    """Get the profile type ('burger' or 'ondernemer') for the active profile."""
    return DemoProfiles.get_active_profile()["type"]
