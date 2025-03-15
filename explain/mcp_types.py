"""
Type definitions for the MCP Connector and related classes.
"""

from typing import Any, TypedDict


class ClaimData(TypedDict, total=False):
    """Type definition for a claim data object."""

    service: str
    key: str
    value: str | int | float
    _id: str  # Internal tracking ID


class ClaimResult(TypedDict):
    """Type definition for a claim submission result."""

    claim_id: str
    service: str
    key: str
    value: Any
    status: str


class ClaimError(TypedDict):
    """Type definition for a claim submission error."""

    claim: ClaimData
    error: str


class ClaimsResponse(TypedDict):
    """Type definition for the claims processing response."""

    submitted: list[ClaimResult]
    errors: list[ClaimError]


class ServiceResult(TypedDict, total=False):
    """Type definition for a service execution result."""

    eligibility: bool
    requirements_met: bool
    result: dict[str, Any]
    input_data: dict[str, Any]
    missing_requirements: list[str]
    missing_required: bool
    missing_fields: list[str]
    explanation: str
    error: str  # Present only on error


class MCPResult(TypedDict, total=False):
    """Type definition for the overall MCP processing result."""

    claims: ClaimsResponse
    # Additional keys will be service names mapping to ServiceResult
