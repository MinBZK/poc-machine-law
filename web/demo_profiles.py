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
        "graph_selected_laws": [
            "292c11ff-8318-4b7a-bb11-3ea545b04c8e",  # Bepalen detentiestatus
            "60e71675-38bc-4297-87ac-0c145613e481",  # Zorgtoeslag
            "aba2b8fa-4b34-420f-883a-e78da326a8f4",  # Bepalen verzekeringsstatus
        ],
        # Laws disabled for the portal/burger tab (feature flags)
        "disabled_laws": {
            "BELASTINGDIENST": ["zorgverzekeringswet/bijdrage", "zvw"],
            "GEMEENTE_ROTTERDAM": [
                "alcoholwet/vergunning",
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
        "graph_selected_laws": [
            "7c2e8f4a-3b9d-4e1f-a5c2-9d8b7e6f4a3c",  # Alcoholwet Rotterdam
            "8a3f9b5c-4d2e-4f0a-b6c3-1e9d8f7a5b4c",  # Alcoholvergunning (nationaal)
            "3e7f9b2a-5d8c-4a1e-9f6b-8c2d4e7a3b1f",  # Terrasvergunning
            "b5d8e2f4-3a6c-4b9e-a7d1-9c4f2e8b1a53",  # Precariobelasting
            "8a3f4b2c-7d1e-4f8a-9c3b-5e6d7f8a9b0c",  # Exploitatievergunning
            "9c4e8f2a-7d3b-4e1f-8a5c-6f9d2e3a7b4c",  # BAG register
            "8b59ef92-03f8-4294-bce9-4eaac01ba0ed",  # Bepalen ondernemerschap
            "1b3c8d9e-5f2a-4c7b-8e1d-9a2b3c4d5e6f",  # Bedrijfsgegevens organisatie
        ],
        # Laws disabled for the portal tab (feature flags)
        "disabled_laws": {
            "BELASTINGDIENST": ["zorgverzekeringswet/bijdrage", "zvw"],
            "DUO": ["wet_studiefinanciering"],
            "GEMEENTE_AMSTERDAM": ["participatiewet/bijstand"],
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
                "wet_inkomstenbelasting",
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
