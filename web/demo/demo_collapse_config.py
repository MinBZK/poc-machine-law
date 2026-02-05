"""Demo collapse configuration for specific law files.

This module defines which sections should be expanded/collapsed by default
when viewing specific laws in demo mode.
"""

# Demo collapse configuration per law file
DEMO_COLLAPSE_CONFIG = {
    # Zorgtoeslag - Show full calculation path for partners
    "zorgtoeslagwet/TOESLAGEN-2025-01-01": {
        "expand_paths": [
            "references.Wet op de zorgtoeslag",
            "references.zvw",
            "properties.parameters",
            "properties.parameters.BSN",
            "properties.output.is_verzekerde_zorgtoeslag",
            "properties.output.hoogte_toeslag",
            "properties.input.IS_VERZEKERDE",
            "properties.input.IS_VERZEKERDE.service_reference",
            "requirements.Item 1",
            "requirements.Item 1.all",
            "requirements.Item 1.all.$LEEFTIJD",
            "requirements.Item 1.all.$IS_VERZEKERDE",
            "actions.hoogte_toeslag",
            "actions.hoogte_toeslag.conditions",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true",  # Second condition (partner = true)
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else",  # Third item (else block)
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD.values",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD.values.$INKOMEN",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.ADD.values.$PARTNER_INKOMEN",
            "actions.hoogte_toeslag.conditions.$HEEFT_PARTNER=true.then.conditions.else.else.values.ADD.values.IF.conditions.GREATER_THAN.then.values.SUBTRACT.values.$DREMPELINKOMEN_TOESLAGPARTNER",
        ],
        "collapse_all_except_expanded": True,
    },
    # Zorgverzekeringswet - Show actions and specific input
    "zvw/RVZ-2024-01-01": {
        "expand_paths": [
            "properties",
            "properties.input",
            "properties.input.IS_GEDETINEERD",  # Specific input item
            "properties.input.IS_GEDETINEERD.service_reference",
            "actions",
            "actions.is_verzekerde",  # Specific action (note: lowercase in YAML)
            "actions.is_verzekerde.values",  # values array
            "actions.is_verzekerde.values.OR",  # First item (operation: OR)
            "actions.is_verzekerde.values.OR.values",  # Nested values
            "actions.is_verzekerde.values.OR.values.$heeft_verzekering",  # First nested value
            "actions.is_verzekerde.values.OR.values.$heeft_verdragsverzekering",  # Second nested value
            "actions.is_verzekerde.values.$IS_GEDETINEERD",  # Second item
        ],
        "collapse_all_except_expanded": True,
    },
    # Penitentiaire Beginselenwet - Only show specific action
    "penitentiaire_beginselenwet/DJI-2022-01-01": {
        "expand_paths": [
            "actions",
            "actions.is_gedetineerd",  # Specific action (lowercase)
            "actions.is_gedetineerd.values",  # values array
            "actions.is_gedetineerd.values.$INRICHTING_TYPE",  # First item (subject: $INRICHTING_TYPE)
            "actions.is_gedetineerd.values.$INRICHTING_TYPE.values",  # Values for INRICHTING_TYPE
            "actions.is_gedetineerd.values.$DETENTIESTATUS",  # Second item (subject: $DETENTIESTATUS)
            "actions.is_gedetineerd.values.$DETENTIESTATUS.values",  # Values for DETENTIESTATUS
        ],
        "collapse_all_except_expanded": True,
    },
    # AWB Bezwaar - Show properties and actions structure
    "awb/bezwaar/JenV-2024-01-01": {
        "expand_paths": [
            "properties",
            "properties.applies",
            "properties.applies.ZAAK",
            "properties.definitions",
            "properties.definitions.EXCLUDED_DECISION_TYPES",
            "properties.definitions.REQUIRED_LEGAL_CHARACTER",
            "actions",
            "actions.bezwaar_mogelijk",
            "actions.bezwaar_mogelijk.values",
            "actions.bezwaar_mogelijk.values.$WET.decision_type",
            "actions.bezwaar_mogelijk.values.$WET.legal_character",
            "actions.bezwaar_mogelijk.values.EQUALS",
            "actions.bezwaar_mogelijk.values.EQUALS.values",
            "actions.bezwaar_mogelijk.values.EQUALS.values.$GEBEURTENISSEN",
        ],
        "collapse_all_except_expanded": True,
    },
    # Alcoholwet - Collapse most sections, show only key info
    "alcoholwet/vergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "properties",
            "properties.output",
        ],
        "collapse_all_except_expanded": True,
    },
    "alcoholwet/vergunning/VWS-2024-01-01": {
        "expand_paths": [
            "properties",
            "properties.output",
        ],
        "collapse_all_except_expanded": True,
    },
    # Exploitatievergunning - Collapse most sections
    "algemene_plaatselijke_verordening/exploitatievergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "properties",
            "properties.output",
        ],
        "collapse_all_except_expanded": True,
    },
    # Terrasvergunning - Collapse most sections
    "algemene_plaatselijke_verordening/terrassen/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "properties",
            "properties.output",
        ],
        "collapse_all_except_expanded": True,
    },
    # Geluidsontheffing - Collapse most sections
    "algemene_plaatselijke_verordening/ontheffingspas_geluid/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01": {
        "expand_paths": [
            "properties",
            "properties.output",
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
