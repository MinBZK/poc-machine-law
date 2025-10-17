"""
Schema definitions for MCP tools - DRY principle applied
"""

from typing import Any

# Base schema components - reusable building blocks
SERVICE_FIELD = {
    "type": "string",
    "description": "Service provider code (e.g., TOESLAGEN, RVO)",
    "examples": ["TOESLAGEN", "SVB", "GEMEENTE_AMSTERDAM", "KIESRAAD", "RVO"],
}

LAW_FIELD = {
    "type": "string",
    "description": "Law identifier (e.g., zorgtoeslagwet, wpm)",
    "examples": ["zorgtoeslagwet", "algemene_ouderdomswet", "participatiewet/bijstand", "kieswet", "wpm"],
}

REFERENCE_DATE_FIELD = {
    "type": "string",
    "description": "Reference date (YYYY-MM-DD)",
    "format": "date",
    "examples": ["2024-01-01", "2024-12-31"],
}

PARAMETERS_FIELD = {
    "type": "object",
    "description": "Parameters required by the law (e.g., BSN for citizen laws, kvk-nummer for business laws)",
    "examples": [
        {"BSN": "100000001"},
        {"kvk-nummer": "12345678"},
        {"BSN": "100000001", "inkomen": 25000},
    ],
    "additionalProperties": True,
}

# Base law execution schema
BASE_LAW_SCHEMA = {
    "type": "object",
    "properties": {
        "service": SERVICE_FIELD,
        "law": LAW_FIELD,
        "parameters": PARAMETERS_FIELD,
        "reference_date": REFERENCE_DATE_FIELD,
    },
    "required": ["service", "law", "parameters"],
}


def create_tool_schema(
    name: str, description: str, additional_fields: dict[str, Any] = None, additional_required: list[str] = None
) -> dict[str, Any]:
    """Create a tool schema with base law fields plus additional fields"""
    schema = {
        "name": name,
        "description": description,
        "inputSchema": {
            "type": "object",
            "properties": dict(BASE_LAW_SCHEMA["properties"]),
            "required": list(BASE_LAW_SCHEMA["required"]),
        },
    }

    if additional_fields:
        schema["inputSchema"]["properties"].update(additional_fields)

    if additional_required:
        schema["inputSchema"]["required"].extend(additional_required)

    return schema


# Tool schema definitions using the factory
TOOL_SCHEMAS = {
    "execute_law": create_tool_schema(
        "execute_law",
        "Execute a Dutch law for a specific citizen with optional parameter overrides",
        {
            "overrides": {
                "type": "object",
                "description": "Parameter overrides to test scenarios. Two types: (1) Service overrides use lowercase field names for external data like UWV income, (2) Source overrides use ALL CAPS for internal law sources like RVO employee counts. Format: SERVICE_NAME -> field_name -> value",
                "examples": [
                    {"UWV": {"inkomen": 3000000}},
                    {"BELASTINGDIENST": {"vermogen": 500000}},
                    {"RVO": {"AANTAL_WERKNEMERS": 150}},
                    {"UWV": {"inkomen": 2500000}, "RVO": {"AANTAL_WERKNEMERS": 200}},
                ],
                "additionalProperties": {"type": "object", "additionalProperties": True},
            },
            "requested_output": {
                "type": "string",
                "description": "Specific output field to calculate",
                "examples": ["hoogte_toeslag", "is_verzekerde_zorgtoeslag", "uitkering_bedrag"],
            },
            "approved": {
                "type": "boolean",
                "description": "Whether this is for an approved claim",
                "default": False,
                "examples": [True, False],
            },
        },
    ),
    "check_eligibility": create_tool_schema(
        "check_eligibility",
        "Check if a citizen is eligible for a specific benefit or law",
        {
            "overrides": {
                "type": "object",
                "description": "Parameter overrides for eligibility testing. Service overrides (lowercase): UWV income, tax data. Source overrides (ALL CAPS): internal law sources like employee counts",
                "examples": [
                    {"UWV": {"inkomen": 3000000}},
                    {"BELASTINGDIENST": {"vermogen": 500000}},
                    {"RVO": {"AANTAL_WERKNEMERS": 150}},
                ],
                "additionalProperties": {"type": "object", "additionalProperties": True},
            }
        },
    ),
    "calculate_benefit_amount": create_tool_schema(
        "calculate_benefit_amount",
        "Calculate a specific benefit amount for a citizen",
        {
            "output_field": {
                "type": "string",
                "description": "Output field to calculate",
                "examples": ["hoogte_toeslag", "uitkering_bedrag", "pensioen_bedrag"],
            },
            "overrides": {
                "type": "object",
                "description": "Parameter overrides for benefit calculation scenarios. Service overrides (lowercase): external data. Source overrides (ALL CAPS): internal law sources",
                "examples": [
                    {"UWV": {"inkomen": 3000000}},
                    {"BELASTINGDIENST": {"vermogen": 500000}},
                    {"RVO": {"AANTAL_WERKNEMERS": 150}},
                ],
                "additionalProperties": {"type": "object", "additionalProperties": True},
            },
        },
        ["output_field"],
    ),
    "get_available_roles": {
        "name": "get_available_roles",
        "description": "Get all roles (authorizations) that a person can assume - acting as themselves, on behalf of others (via ouderlijk gezag, curatele, volmacht), or for organizations (via KVK registration)",
        "inputSchema": {
            "type": "object",
            "properties": {
                "actor_bsn": {
                    "type": "string",
                    "description": "BSN of the person whose available roles to check",
                    "examples": ["100000001", "300000001"],
                },
                "reference_date": {
                    "type": "string",
                    "description": "Reference date (YYYY-MM-DD) - defaults to today",
                    "format": "date",
                    "examples": ["2024-01-01", "2025-10-17"],
                },
            },
            "required": ["actor_bsn"],
        },
    },
    "select_role": {
        "name": "select_role",
        "description": "Select a role to act as - switches context for subsequent law executions. After selecting a role, all law evaluations will be performed on behalf of the target person/organization.",
        "inputSchema": {
            "type": "object",
            "properties": {
                "actor_bsn": {
                    "type": "string",
                    "description": "BSN of the person selecting the role",
                    "examples": ["100000001", "300000001"],
                },
                "target_type": {
                    "type": "string",
                    "description": "Type of target to act on behalf of",
                    "enum": ["PERSON", "ORGANIZATION", "SELF"],
                    "examples": ["PERSON", "ORGANIZATION", "SELF"],
                },
                "target_id": {
                    "type": "string",
                    "description": "BSN (if PERSON) or RSIN (if ORGANIZATION) to act on behalf of. Not needed if target_type is SELF.",
                    "examples": ["100000001", "001234567"],
                },
                "action": {
                    "type": "string",
                    "description": "Optional: specific action/scope to verify (e.g., 'financial' for bewindvoering)",
                    "examples": ["financial", "medical", "belasting_aangifte"],
                },
                "reference_date": {
                    "type": "string",
                    "description": "Reference date (YYYY-MM-DD) - defaults to today",
                    "format": "date",
                    "examples": ["2024-01-01", "2025-10-17"],
                },
            },
            "required": ["actor_bsn", "target_type"],
        },
    },
}
