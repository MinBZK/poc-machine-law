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
                "description": "Parameter overrides",
                "examples": [{"inkomen": 25000}, {"woonsituatie": "alleenstaand"}],
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
        "check_eligibility", "Check if a citizen is eligible for a specific benefit or law"
    ),
    "calculate_benefit_amount": create_tool_schema(
        "calculate_benefit_amount",
        "Calculate a specific benefit amount for a citizen",
        {
            "output_field": {
                "type": "string",
                "description": "Output field to calculate",
                "examples": ["hoogte_toeslag", "uitkering_bedrag", "pensioen_bedrag"],
            }
        },
        ["output_field"],
    ),
}
