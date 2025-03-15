"""
Logging utilities for the MCP connector.
"""

import logging
from typing import Any

# Configure logging
logger = logging.getLogger("mcp")


def setup_logging(level: int = logging.INFO) -> None:
    """Set up logging for the MCP connector.

    Args:
        level: The logging level (default: INFO)
    """
    logger.setLevel(level)

    # Create console handler if not already present
    if not logger.handlers:
        handler = logging.StreamHandler()
        formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)


def log_service_execution(service_name: str, bsn: str, params: dict[str, Any] | None = None) -> None:
    """Log service execution.

    Args:
        service_name: The name of the service
        bsn: The BSN of the user
        params: Optional parameters for the service
    """
    masked_bsn = f"{bsn[:3]}...{bsn[-3:]}" if len(bsn) > 6 else "***"
    logger.info(f"Executing service '{service_name}' for BSN {masked_bsn}")
    if params:
        logger.debug(f"Service params: {params}")


def log_claim_submission(service_name: str, key: str, bsn: str) -> None:
    """Log claim submission.

    Args:
        service_name: The name of the service
        key: The key of the claim
        bsn: The BSN of the user
    """
    masked_bsn = f"{bsn[:3]}...{bsn[-3:]}" if len(bsn) > 6 else "***"
    logger.info(f"Submitting claim '{key}' for service '{service_name}' and BSN {masked_bsn}")


def log_error(error: Exception, context: dict[str, Any] | None = None) -> None:
    """Log an error.

    Args:
        error: The error to log
        context: Optional context information
    """
    error_message = str(error)
    if context:
        logger.error(f"Error: {error_message} (Context: {context})")
    else:
        logger.error(f"Error: {error_message}")

    # Log traceback for debugging
    logger.debug("Exception details:", exc_info=error)
