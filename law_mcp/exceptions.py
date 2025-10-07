"""
Custom exception hierarchy for MCP law execution server.
Provides specific error types for better error handling and debugging.
"""


class MCPLawException(Exception):
    """Base exception for all MCP law execution errors"""

    def __init__(self, message: str, error_code: str = None, details: dict = None):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.details = details or {}


class ValidationError(MCPLawException):
    """Raised when input validation fails"""


class BSNValidationError(ValidationError):
    """Raised when BSN validation fails"""

    def __init__(self, bsn: str):
        super().__init__(f"Invalid BSN format: {bsn}", error_code="INVALID_BSN", details={"bsn": bsn})


class LawExecutionError(MCPLawException):
    """Raised when law execution fails"""

    def __init__(self, service: str, law: str, message: str, details: dict = None):
        super().__init__(
            f"Failed to execute {service}.{law}: {message}",
            error_code="LAW_EXECUTION_FAILED",
            details={"service": service, "law": law, **(details or {})},
        )


class LawNotFoundError(MCPLawException):
    """Raised when a law specification is not found"""

    def __init__(self, service: str, law: str):
        super().__init__(
            f"Law specification not found for {service}.{law}",
            error_code="LAW_NOT_FOUND",
            details={"service": service, "law": law},
        )


class ServiceNotFoundError(MCPLawException):
    """Raised when a service is not available"""

    def __init__(self, service: str, available_services: list[str] = None):
        super().__init__(
            f"Service {service} not available",
            error_code="SERVICE_NOT_FOUND",
            details={"service": service, "available_services": available_services or []},
        )


class ProfileNotFoundError(MCPLawException):
    """Raised when citizen profile is not found"""

    def __init__(self, bsn: str):
        super().__init__(f"Profile not found for BSN {bsn}", error_code="PROFILE_NOT_FOUND", details={"bsn": bsn})


class CacheError(MCPLawException):
    """Raised when cache operations fail"""


class ConfigurationError(MCPLawException):
    """Raised when configuration is invalid"""


class RateLimitError(MCPLawException):
    """Raised when rate limit is exceeded"""

    def __init__(self, identifier: str, limit: int):
        super().__init__(
            f"Rate limit exceeded for {identifier}: {limit} requests per minute",
            error_code="RATE_LIMIT_EXCEEDED",
            details={"identifier": identifier, "limit": limit},
        )


class TimeoutError(MCPLawException):
    """Raised when operations timeout"""

    def __init__(self, operation: str, timeout: float):
        super().__init__(
            f"Operation {operation} timed out after {timeout}s",
            error_code="OPERATION_TIMEOUT",
            details={"operation": operation, "timeout": timeout},
        )


class SecurityError(MCPLawException):
    """Raised when security validation fails"""


def handle_exception(e: Exception) -> MCPLawException:
    """Convert generic exceptions to specific MCP exceptions when possible"""
    if isinstance(e, MCPLawException):
        return e

    error_message = str(e)

    # Map common exceptions to specific types
    if "BSN" in error_message and "invalid" in error_message.lower():
        return ValidationError(error_message, "INVALID_BSN")

    if "not found" in error_message.lower():
        return LawNotFoundError("unknown", "unknown")

    if "timeout" in error_message.lower():
        return TimeoutError("unknown", 0)

    # Generic wrapper
    return MCPLawException(
        f"Unexpected error: {error_message}", error_code="INTERNAL_ERROR", details={"original_type": type(e).__name__}
    )
