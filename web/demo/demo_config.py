"""Demo configuration for law files.

This module defines:
1. Which laws are enabled/disabled in demo mode (using feature flags)
2. Which sections should be expanded/collapsed by default when viewing specific laws
"""

# Per-profile disabled laws are now configured in demo_profiles.py (DemoProfiles).
# Each profile has its own "disabled_laws" dict that explicitly controls law visibility.

# Demo collapse configuration per law file
DEMO_COLLAPSE_CONFIG = {
    # Zorgtoeslag - Show full calculation path for partners (v0.5.0 article-based)
    "zorgtoeslagwet/TOESLAGEN-2025-01-01": {
        "expand_paths": [
            "articles",
            "articles.2",  # Article number "2"
            "articles.2.machine_readable",
            "articles.2.machine_readable.definitions",
            "articles.2.machine_readable.execution",
            "articles.2.machine_readable.execution.parameters",
            "articles.2.machine_readable.execution.parameters.BSN",
            "articles.2.machine_readable.execution.output",
            "articles.2.machine_readable.execution.output.is_verzekerde_zorgtoeslag",
            "articles.2.machine_readable.execution.output.hoogte_toeslag",
            "articles.2.machine_readable.execution.input",
            "articles.2.machine_readable.execution.input.IS_VERZEKERDE",
            "articles.2.machine_readable.execution.input.IS_VERZEKERDE.source",
            "articles.2.machine_readable.execution.requirements",
            "articles.2.machine_readable.execution.requirements.Item 1",
            "articles.2.machine_readable.execution.requirements.Item 1.all",
            "articles.2.machine_readable.execution.requirements.Item 1.all.$LEEFTIJD",
            "articles.2.machine_readable.execution.requirements.Item 1.all.$IS_VERZEKERDE",
            "articles.2.machine_readable.execution.actions",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD.values",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD.values.$INKOMEN",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD.values.$PARTNER_INKOMEN",
            "articles.2.machine_readable.execution.actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.$DREMPELINKOMEN_TOESLAGPARTNER",
        ],
        "collapse_all_except_expanded": True,
    },
    # Zorgverzekeringswet - Show actions and specific input (v0.5.0 article-based)
    "zvw/RVZ-2024-01-01": {
        "expand_paths": [
            "articles",
            "articles.1",  # Article number "1"
            "articles.1.machine_readable",
            "articles.1.machine_readable.execution",
            "articles.1.machine_readable.execution.input",
            "articles.1.machine_readable.execution.input.IS_GEDETINEERD",
            "articles.1.machine_readable.execution.input.IS_GEDETINEERD.source",
            "articles.1.machine_readable.execution.actions",
            "articles.1.machine_readable.execution.actions.is_verzekerde",
            "articles.1.machine_readable.execution.actions.is_verzekerde.values",
            "articles.1.machine_readable.execution.actions.is_verzekerde.values.OR",
            "articles.1.machine_readable.execution.actions.is_verzekerde.values.OR.values",
            "articles.1.machine_readable.execution.actions.is_verzekerde.values.OR.values.$heeft_verzekering",
            "articles.1.machine_readable.execution.actions.is_verzekerde.values.OR.values.$heeft_verdragsverzekering",
            "articles.1.machine_readable.execution.actions.is_verzekerde.values.$IS_GEDETINEERD",
        ],
        "collapse_all_except_expanded": True,
    },
    # Penitentiaire Beginselenwet - Only show specific action (v0.5.0 article-based)
    "penitentiaire_beginselenwet/DJI-2022-01-01": {
        "expand_paths": [
            "articles",
            "articles.2",  # Article number "2"
            "articles.2.machine_readable",
            "articles.2.machine_readable.execution",
            "articles.2.machine_readable.execution.actions",
            "articles.2.machine_readable.execution.actions.is_gedetineerd",
            "articles.2.machine_readable.execution.actions.is_gedetineerd.values",
            "articles.2.machine_readable.execution.actions.is_gedetineerd.values.$INRICHTING_TYPE",
            "articles.2.machine_readable.execution.actions.is_gedetineerd.values.$INRICHTING_TYPE.values",
            "articles.2.machine_readable.execution.actions.is_gedetineerd.values.$DETENTIESTATUS",
            "articles.2.machine_readable.execution.actions.is_gedetineerd.values.$DETENTIESTATUS.values",
        ],
        "collapse_all_except_expanded": True,
    },
    # AWB Bezwaar - Show definitions and actions structure (v0.5.0 article-based)
    "awb/bezwaar/JenV-2024-01-01": {
        "expand_paths": [
            "articles",
            "articles.7:1",  # Article number "7:1"
            "articles.7:1.machine_readable",
            "articles.7:1.machine_readable.definitions",
            "articles.7:1.machine_readable.definitions.EXCLUDED_DECISION_TYPES",
            "articles.7:1.machine_readable.definitions.REQUIRED_LEGAL_CHARACTER",
            "articles.7:1.machine_readable.execution",
            "articles.7:1.machine_readable.execution.actions",
            "articles.7:1.machine_readable.execution.actions.bezwaar_mogelijk",
            "articles.7:1.machine_readable.execution.actions.bezwaar_mogelijk.values",
            "articles.7:1.machine_readable.execution.actions.bezwaar_mogelijk.values.$WET.decision_type",
            "articles.7:1.machine_readable.execution.actions.bezwaar_mogelijk.values.$WET.legal_character",
            "articles.7:1.machine_readable.execution.actions.bezwaar_mogelijk.values.EQUALS",
            "articles.7:1.machine_readable.execution.actions.bezwaar_mogelijk.values.EQUALS.values",
            "articles.7:1.machine_readable.execution.actions.bezwaar_mogelijk.values.EQUALS.values.$GEBEURTENISSEN",
        ],
        "collapse_all_except_expanded": True,
    },
    # Alcoholwet - Collapse most sections, show articles
    "alcoholwet/vergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    "alcoholwet/vergunning/VWS-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # Exploitatievergunning - Collapse most sections
    "algemene_plaatselijke_verordening/exploitatievergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # Terrasvergunning - Collapse most sections
    "algemene_plaatselijke_verordening/terrassen/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # Geluidsontheffing - Collapse most sections
    "algemene_plaatselijke_verordening/ontheffingspas_geluid/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # Informatieplicht Energiebesparing - Show articles
    "omgevingswet/energiebesparing/informatieplicht/RVO-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # HACCP Voedselveiligheid - Show articles
    "warenwet/haccp/NVWA-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # CBS Statistiekverplichting - Show articles
    "wet_op_het_centraal_bureau_voor_de_statistiek/enquete/CBS-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # KVK Jaarrekening Deponeringsplicht - Show articles
    "handelsregisterwet/jaarrekening/KVK-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
    # NVWA Meldplicht Voedselveiligheidsincident - Show articles
    "warenwet/meldplicht/NVWA-2024-01-01": {
        "expand_paths": [
            "articles",
        ],
        "collapse_all_except_expanded": True,
    },
}


def get_demo_collapse_config(law_path: str) -> dict | None:
    """
    Get demo collapse configuration for a specific law.

    Args:
        law_path: Path to the law file (e.g., "zorgtoeslagwet/TOESLAGEN-2025-01-01")

    Returns:
        Configuration dict or None if no demo config exists
    """
    return DEMO_COLLAPSE_CONFIG.get(law_path)


def should_expand_in_demo_mode(law_path: str, item_path: str) -> bool:
    """
    Check if a specific path should be expanded in demo mode.

    Args:
        law_path: Path to the law file
        item_path: Dot-separated path to the item (e.g., "properties.input.IS_VERZEKERDE")

    Returns:
        True if should be expanded, False otherwise
    """
    config = get_demo_collapse_config(law_path)
    if not config:
        return None  # No demo config, use default behavior

    if not config.get("collapse_all_except_expanded", False):
        return None  # Not using demo mode collapse

    # Check if this path or any parent path is in expand_paths
    expand_paths = config.get("expand_paths", [])

    # Exact match
    if item_path in expand_paths:
        return True

    # Check if any parent path is expanded (which means children are visible)
    for expand_path in expand_paths:
        if item_path.startswith(expand_path + "."):
            # This is a child of an expanded path
            # Only expand if it's explicitly in the list
            return item_path in expand_paths

    # Default: collapse if not in expand paths
    return False


def configure_demo_feature_flags() -> None:
    """
    Configure feature flags for demo mode based on the active profile.

    Delegates to DemoProfiles.apply_feature_flags() which handles both
    general feature flags and per-profile law visibility.
    """
    from web.demo_profiles import DemoProfiles

    DemoProfiles.apply_feature_flags()


def is_law_enabled_in_demo(law: str, service: str) -> bool:
    """
    Check if a law should be shown in demo mode using feature flags.

    Args:
        law: Law identifier (e.g., "zorgtoeslagwet")
        service: Service identifier (e.g., "TOESLAGEN")

    Returns:
        True if law is enabled in demo mode, False otherwise
    """
    from web.feature_flags import FeatureFlags

    return FeatureFlags.is_law_enabled(service, law)
