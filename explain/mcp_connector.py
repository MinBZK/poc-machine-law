"""
MCP Connector for connecting LLMs to law services.
Implements the Model Context Protocol (MCP) specification from https://contextprovider.ai/
to create standardized services that can be used by any MCP-compatible LLM.
"""

import json
import os

import jinja2

from machine.service import Services

from .mcp_claims import MCPClaimProcessor
from .mcp_formatter import MCPResultFormatter
from .mcp_logging import logger, setup_logging
from .mcp_service_executor import MCPServiceExecutor
from .mcp_services import MCPServiceRegistry
from .mcp_types import MCPResult


class MCPLawConnector:
    """Connector for making law services available to LLMs via MCP"""

    def __init__(self, services: Services):
        """Initialize the MCP law connector.

        Args:
            services: The services instance for executing law calculations
        """
        # Set up logging
        setup_logging()

        # Initialize components
        self.registry = MCPServiceRegistry(services)
        self.claim_processor = MCPClaimProcessor(self.registry)
        self.service_executor = MCPServiceExecutor(self.registry)
        self.formatter = MCPResultFormatter(self.registry)

        # Set up Jinja2 environment for templates
        template_dir = os.path.join(os.path.dirname(__file__), "prompts")
        self.jinja_env = jinja2.Environment(
            loader=jinja2.FileSystemLoader(template_dir),
            autoescape=False,
            trim_blocks=True,
            lstrip_blocks=True,
        )

        logger.info("MCP Law Connector initialized")

    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM that describes available services using a standardized tool-based approach

        Returns:
            System prompt describing available services
        """
        available_services = self.registry.get_service_names()
        logger.info(f"Generating system prompt with {len(available_services)} available services")

        # Build service descriptions based on actual available services and their official descriptions
        service_tools = []

        # Get descriptions from the services
        service_tool_template = self.jinja_env.get_template("service_tool_template.j2")
        for service_name in available_services:
            service = self.registry.get_service(service_name)
            if service:
                description = service.description
                # Format as a tool definition for Claude
                service_tools.append(service_tool_template.render(service_name=service_name, description=description))

        # Add a claim tool for submitting values
        claim_tool_template = self.jinja_env.get_template("claim_tool_template.j2")
        service_tools.append(claim_tool_template.render())

        # Add application form tool
        application_tool_template = self.jinja_env.get_template("application_form_tool_template.j2")
        service_tools.append(application_tool_template.render())

        # Build the prompt with the actual available services in MCP compatible format
        system_prompt_template = self.jinja_env.get_template("mcp_system_prompt.j2")
        return system_prompt_template.render(service_tools=service_tools)

    def extract_application_form_reference(self, message: str) -> str | None:
        """Extract application form references from LLM responses.

        Args:
            message: The message to extract application form references from

        Returns:
            Service name to show application form for, or None if no reference found
        """
        # Import here to avoid circular imports
        import re

        # Check for show_application_form tool call
        app_form_pattern = r"<tool_use>[\s\S]*?<tool_name>show_application_form</tool_name>[\s\S]*?<parameters>([\s\S]*?)</parameters>[\s\S]*?</tool_use>"

        # Find matches
        matches = re.findall(app_form_pattern, message)

        if matches:
            try:
                for match in matches:
                    # Clean up the JSON string
                    clean_json = match.strip().replace("'", '"')
                    if not clean_json.startswith("{"):
                        logger.warning(f"Skipping invalid application form format: {match}")
                        continue

                    try:
                        # Parse JSON
                        data = json.loads(clean_json)
                        service_name = data.get("service")

                        if service_name and service_name in self.registry.get_service_names():
                            logger.info(f"Found application form reference for service: {service_name}")
                            return service_name
                    except json.JSONDecodeError:
                        # Try to extract with regex
                        service_match = re.search(r'"service"\s*:\s*"([^"]+)"', clean_json)
                        if service_match:
                            service_name = service_match.group(1)
                            if service_name in self.registry.get_service_names():
                                logger.info(f"Found application form reference for service: {service_name}")
                                return service_name
            except Exception as e:
                logger.error(f"Error extracting application form reference: {str(e)}")

        return None

    async def process_message(self, message: str, bsn: str) -> MCPResult:
        """Process a user message and execute any law services that might be referred to

        Args:
            message: The user message to process
            bsn: The BSN of the user

        Returns:
            The processing results
        """
        # Extract service references and claims from the message
        service_refs = self.service_executor.extract_service_references(message)
        claim_refs = self.claim_processor.extract_claims(message)
        application_form_ref = self.extract_application_form_reference(message)

        logger.info(
            f"Processing message with {len(service_refs)} service references, {len(claim_refs)} claim references, "
            f"and application form reference: {application_form_ref}"
        )

        results: MCPResult = {}

        # Process any claims first
        if claim_refs:
            logger.info(f"Processing {len(claim_refs)} claims")
            claims_result = await self.claim_processor.process_claims(claim_refs, bsn)
            if claims_result:
                results["claims"] = claims_result

        # Execute each referenced service
        if service_refs:
            logger.info(f"Executing {len(service_refs)} services")
            service_results = await self.service_executor.execute_services(service_refs, bsn)
            # Add service results to the overall results
            for service_name, result in service_results.items():
                results[service_name] = result

        # Add application form reference if found
        if application_form_ref:
            logger.info(f"Application form reference found for service: {application_form_ref}")
            results["application_form"] = {"service": application_form_ref}

        return results

    def format_results_for_llm(self, results: MCPResult) -> str:
        """Format service results for inclusion in the LLM context

        Args:
            results: The results to format

        Returns:
            Formatted results as markdown
        """
        return self.formatter.format_for_llm(results)
