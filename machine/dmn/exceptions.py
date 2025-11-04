"""
DMN-specific exceptions for the custom DMN interpreter.
"""


class DMNError(Exception):
    """Base exception for all DMN-related errors."""
    pass


class DMNFileNotFoundError(DMNError):
    """Raised when a DMN file cannot be found."""
    pass


class DMNParseError(DMNError):
    """Raised when a DMN XML file cannot be parsed."""
    pass


class DMNValidationError(DMNError):
    """Raised when a DMN model fails validation."""
    pass


class DMNExecutionError(DMNError):
    """Raised when a DMN decision execution fails."""
    pass


class FEELSyntaxError(DMNError):
    """Raised when a FEEL expression has syntax errors."""
    pass


class FEELEvaluationError(DMNError):
    """Raised when a FEEL expression cannot be evaluated."""
    pass


class DecisionNotFoundError(DMNError):
    """Raised when a referenced decision does not exist."""
    pass


class DecisionServiceNotFoundError(DMNError):
    """Raised when a referenced decision service does not exist."""
    pass


class CircularDependencyError(DMNError):
    """Raised when circular dependencies are detected between decisions."""
    pass


class UnsupportedFEELFeatureError(DMNError):
    """Raised when a FEEL feature is not supported by the interpreter."""
    pass
