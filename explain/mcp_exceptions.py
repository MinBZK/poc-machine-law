"""
Custom exceptions for the MCP connector.
"""


class MCPError(Exception):
    """Base class for all MCP-related errors."""


class MCPServiceNotFoundError(MCPError):
    """Raised when a service is not found in the registry."""

    def __init__(self, service_name: str):
        self.service_name = service_name
        super().__init__(f"Service '{service_name}' not found")


class MCPServiceExecutionError(MCPError):
    """Raised when a service execution fails."""

    def __init__(self, service_name: str, original_error: Exception):
        self.service_name = service_name
        self.original_error = original_error
        super().__init__(f"Error executing service '{service_name}': {str(original_error)}")


class MCPClaimError(MCPError):
    """Base class for claim-related errors."""


class MCPClaimParsingError(MCPClaimError):
    """Raised when parsing a claim fails."""

    def __init__(self, original_error: Exception, raw_data: str = None):
        self.original_error = original_error
        self.raw_data = raw_data
        message = f"Error parsing claim: {str(original_error)}"
        if raw_data:
            message += f" (Raw data: {raw_data})"
        super().__init__(message)


class MCPClaimValidationError(MCPClaimError):
    """Raised when claim validation fails."""

    def __init__(self, reason: str, claim_data: dict = None):
        self.reason = reason
        self.claim_data = claim_data
        message = f"Claim validation failed: {reason}"
        if claim_data:
            message += f" (Claim data: {claim_data})"
        super().__init__(message)


class MCPClaimSubmissionError(MCPClaimError):
    """Raised when claim submission fails."""

    def __init__(self, original_error: Exception, claim_data: dict = None):
        self.original_error = original_error
        self.claim_data = claim_data
        message = f"Error submitting claim: {str(original_error)}"
        if claim_data:
            message += f" (Claim data: {claim_data})"
        super().__init__(message)
