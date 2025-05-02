"""
MCP Service Executor for executing law services and formatting results.
"""

import re
from typing import Any

from .mcp_exceptions import MCPServiceExecutionError, MCPServiceNotFoundError
from .mcp_logging import log_error, log_service_execution, logger
from .mcp_services import MCPServiceRegistry
from .mcp_types import ServiceResult


class MCPServiceExecutor:
    """Executor for MCP law services."""

    def __init__(self, registry: MCPServiceRegistry):
        """Initialize the service executor.

        Args:
            registry: The MCP service registry
        """
        self.registry = registry

    def extract_service_references(self, message: str) -> list[str]:
        """Extract service references from LLM responses using tool syntax.

        Args:
            message: The message to extract service references from

        Returns:
            List of service references
        """
        available_services = self.registry.get_service_names()
        referenced_services = []

        # Import here to avoid circular imports
        import re

        # Check for Claude tool syntax: <tool_use><tool_name>service</tool_name></tool_use>
        tool_patterns = re.findall(r"<tool_use>[\s\S]*?<tool_name>(.*?)</tool_name>[\s\S]*?</tool_use>", message)

        # Alternative patterns that Claude sometimes uses
        tool_patterns_alt1 = re.findall(r"<tool>\s*<n>(.*?)</n>", message)
        tool_patterns_alt2 = re.findall(r"<tool name=\"([^\"]+)\"", message)

        # Combine all pattern matches
        all_tool_patterns = tool_patterns + tool_patterns_alt1 + tool_patterns_alt2

        if all_tool_patterns:
            for service_name in all_tool_patterns:
                service_name = service_name.strip().lower()
                if service_name in available_services and service_name not in referenced_services:
                    logger.debug(f"Found tool syntax for service: {service_name}")
                    referenced_services.append(service_name)

            # Early return with found tool syntax matches
            if referenced_services:
                logger.info(f"Extracted service references from tool syntax: {referenced_services}")
                return referenced_services

        # Check for other tool syntaxes that Claude might use
        self._check_additional_syntaxes(message, available_services, referenced_services)

        logger.info(f"Extracted service references: {referenced_services}")
        return referenced_services

    def _check_additional_syntaxes(
        self, message: str, available_services: list[str], referenced_services: list[str]
    ) -> None:
        """Check for additional tool syntaxes that Claude might use.

        This method modifies the referenced_services list in-place.

        Args:
            message: The message to check
            available_services: List of available services
            referenced_services: List of referenced services to be updated
        """
        # Check for JSON-like tool calls: {"name": "service_name", ...}
        json_patterns = re.findall(r'{"name"\s*:\s*"([^"]+)"', message)
        if json_patterns:
            for service_name in json_patterns:
                service_name = service_name.strip().lower()
                if service_name in available_services and service_name not in referenced_services:
                    logger.debug(f"Found JSON syntax for service: {service_name}")
                    referenced_services.append(service_name)

        # Check for Markdown code block style tool calls
        markdown_patterns = re.findall(r'```(?:json)?\s*\{\s*"name"\s*:\s*"([^"]+)"', message)
        if markdown_patterns:
            for service_name in markdown_patterns:
                service_name = service_name.strip().lower()
                if service_name in available_services and service_name not in referenced_services:
                    logger.debug(f"Found Markdown code block syntax for service: {service_name}")
                    referenced_services.append(service_name)

        # Check for @service mentions (alternative syntax)
        message_lower = message.lower()
        at_patterns = re.findall(r"@(\w+)", message_lower)
        for service_name in at_patterns:
            if service_name in available_services and service_name not in referenced_services:
                logger.debug(f"Found @service syntax for service: {service_name}")
                referenced_services.append(service_name)

    def execute_service(self, service_name: str, bsn: str, params: dict[str, Any] | None = None) -> ServiceResult:
        """Execute a law service.

        Args:
            service_name: The name of the service to execute
            bsn: The BSN of the user
            params: Optional parameters for the service

        Returns:
            The service result

        Raises:
            MCPServiceNotFoundError: If the service is not found
            MCPServiceExecutionError: If the service execution fails
        """
        # Log service execution
        log_service_execution(service_name, bsn, params)

        # Get the service
        service = self.registry.get_service(service_name)
        if not service:
            error = f"Service '{service_name}' not found"
            logger.error(error)
            raise MCPServiceNotFoundError(service_name)

        # Execute the service
        try:
            result = service.execute(bsn, params or {})
            logger.info(f"Service {service_name} executed successfully")
            logger.debug(f"Service {service_name} result: {result}")
            return result
        except Exception as e:
            log_error(e, {"service_name": service_name})
            raise MCPServiceExecutionError(service_name, e)

    def execute_services(
        self, service_names: list[str], bsn: str, params: dict[str, Any] | None = None
    ) -> dict[str, ServiceResult]:
        """Execute multiple law services.

        Args:
            service_names: The names of the services to execute
            bsn: The BSN of the user
            params: Optional parameters for the services

        Returns:
            Dictionary of service results
        """
        results = {}

        # Execute each service
        for service_name in service_names:
            try:
                result = self.execute_service(service_name, bsn, params)
                results[service_name] = result
            except MCPServiceExecutionError as e:
                logger.error(f"Error executing service {service_name}: {str(e)}")
                results[service_name] = {"error": str(e)}
            except MCPServiceNotFoundError:
                logger.error(f"Service not found: {service_name}")
                results[service_name] = {"error": f"Service '{service_name}' not found"}
            except Exception as e:
                logger.error(f"Unexpected error executing service {service_name}: {str(e)}")
                results[service_name] = {"error": f"Unexpected error: {str(e)}"}

        return results
