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

        # Store services instance
        self.services = services

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

    async def get_cases_context(self, bsn: str) -> str:
        """Get formatted context about a user's existing cases (applications).

        Args:
            bsn: The BSN of the user

        Returns:
            Formatted cases context for the system prompt
        """
        # Get all cases for this user from the case manager using our new method
        cases = self.services.case_manager.get_cases_by_bsn(bsn)

        if not cases:
            return self.jinja_env.get_template("includes/cases_context.j2").render(cases=None)

        # Prepare case data for template
        case_data = []

        # Check if we have a profile for this BSN
        profile = None
        try:
            from web.services.profiles import get_profile_data

            profile = get_profile_data(bsn)
        except Exception as e:
            logger.warning(f"Error fetching profile for BSN {bsn}: {e}")

        for case in cases:
            # Get service name from registry
            service_obj = None
            for service_name in self.registry.get_service_names():
                service = self.registry.get_service(service_name)
                if service and service.service_type == case.service and service.law_path == case.law:
                    service_obj = service
                    break

            service_name = service_name if service_obj else case.service

            # Check if objection or appeal is possible
            can_object = False
            can_appeal = False
            try:
                can_object = case.can_object()
            except:
                pass

            try:
                can_appeal = case.can_appeal()
            except:
                pass

            # Get objection and appeal status info if available
            objection_info = (
                case.objection_status if hasattr(case, "objection_status") and case.objection_status else None
            )
            appeal_info = case.appeal_status if hasattr(case, "appeal_status") and case.appeal_status else None

            # Check for differences between current calculation and case
            current_result = None
            has_differences = False
            differences_details = None

            try:
                if profile and hasattr(case, "verified_result") and case.verified_result:
                    # Run a current calculation with approved=False to see current situation
                    parameters = {"BSN": bsn}
                    result = await self.services.evaluate(
                        case.service, law=case.law, parameters=parameters, approved=False
                    )

                    if result and result.output:
                        current_result = result.output

                        # Get the rule spec to check for citizen_relevance markings
                        rule_spec = self.services.resolver.get_rule_spec(case.law, "2025-01-01", service=case.service)

                        # Extract primary value marked with citizen_relevance: primary
                        primary_field = None
                        if rule_spec and "properties" in rule_spec and "output" in rule_spec["properties"]:
                            for output_def in rule_spec["properties"]["output"]:
                                if output_def.get("citizen_relevance") == "primary":
                                    primary_field = output_def.get("name")
                                    break

                        if primary_field and primary_field in current_result and primary_field in case.verified_result:
                            # Use the field marked as primary for comparison
                            current_amount = current_result.get(primary_field)
                            case_amount = case.verified_result.get(primary_field)

                            # Handle numbers - assume monetary amounts if fairly large (> 100)
                            if isinstance(current_amount, int | float) and isinstance(case_amount, int | float):
                                # Check if we need to format as money
                                is_money = abs(current_amount) > 100 or abs(case_amount) > 100

                                # Calculate difference and percentage
                                abs_diff = abs(current_amount - case_amount)
                                if case_amount != 0:
                                    pct_diff = abs_diff / abs(case_amount) * 100

                                    # Only flag significant differences (>1% or >€1)
                                    if pct_diff > 1 or (is_money and abs_diff > 100):
                                        has_differences = True

                                        if is_money:
                                            # Format as money (assuming cents)
                                            differences_details = (
                                                f"Bedrag verschil: €{abs_diff / 100:.2f} ({pct_diff:.1f}%)"
                                            )

                                            if current_amount > case_amount:
                                                differences_details += f" (nu €{current_amount / 100:.2f}, eerder €{case_amount / 100:.2f})"
                                            else:
                                                differences_details += f" (nu €{current_amount / 100:.2f}, eerder €{case_amount / 100:.2f})"
                                        else:
                                            # Format as regular number
                                            differences_details = (
                                                f"Verschil in {primary_field}: {abs_diff} ({pct_diff:.1f}%)"
                                            )

                                            if current_amount > case_amount:
                                                differences_details += f" (nu {current_amount}, eerder {case_amount})"
                                            else:
                                                differences_details += f" (nu {current_amount}, eerder {case_amount})"
                        else:
                            # Fallback to common amount fields if no primary field found
                            for field_name in ["bedrag", "toeslag", "uitkering", "amount"]:
                                if field_name in current_result and field_name in case.verified_result:
                                    current_amount = current_result.get(field_name)
                                    case_amount = case.verified_result.get(field_name)

                                    # If amounts differ by more than 1 euro
                                    if abs(current_amount - case_amount) > 100:  # amounts in cents
                                        has_differences = True
                                        differences_details = (
                                            f"Bedrag verschil: €{abs(current_amount - case_amount) / 100:.2f}"
                                        )

                                        if current_amount > case_amount:
                                            differences_details += (
                                                f" (nu €{current_amount / 100:.2f}, eerder €{case_amount / 100:.2f})"
                                            )
                                        else:
                                            differences_details += (
                                                f" (nu €{current_amount / 100:.2f}, eerder €{case_amount / 100:.2f})"
                                            )
                                    break
            except Exception as e:
                logger.warning(f"Error calculating current result for comparison: {e}")

            case_info = {
                "id": case.id,
                "service": case.service,
                "service_name": service_name,
                "law": case.law,
                "status": case.status,
                "approved": case.approved,
                "created_at": case.created_at.strftime("%d-%m-%Y")
                if hasattr(case, "created_at") and case.created_at
                else None,
                "can_object": can_object,
                "can_appeal": can_appeal,
                "objection_info": objection_info,
                "appeal_info": appeal_info,
                "has_differences": has_differences,
                "differences_details": differences_details,
                "current_result": current_result,
                "case_result": case.verified_result if hasattr(case, "verified_result") else None,
            }
            case_data.append(case_info)

        # Sort by most recent created date
        case_data.sort(key=lambda x: x["created_at"] or "", reverse=True)

        # Log the number of cases found
        logger.info(f"Found {len(case_data)} cases for BSN {bsn}")

        # Render the cases context template
        cases_template = self.jinja_env.get_template("includes/cases_context.j2")
        return cases_template.render(cases=case_data)

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
