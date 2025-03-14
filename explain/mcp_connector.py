"""
MCP Connector for connecting LLMs to law services.
Implements the Model Context Protocol (MCP) specification from https://contextprovider.ai/
to create standardized services that can be used by any MCP-compatible LLM.
"""

from typing import Any

from machine.service import Services

from .mcp_services import MCPServiceRegistry


class MCPLawConnector:
    """Connector for making law services available to LLMs via MCP"""

    def __init__(self, services: Services):
        self.registry = MCPServiceRegistry(services)

    def get_system_prompt(self) -> str:
        """Get the system prompt for the LLM that describes available services using a standardized tool-based approach"""
        available_services = self.registry.get_service_names()

        # Build service descriptions based on actual available services and their official descriptions
        service_tools = []

        # Get descriptions from the services
        for service_name in available_services:
            service = self.registry.get_service(service_name)
            if service:
                description = service.description

                # Format as a tool definition for Claude
                service_tools.append(
                    f"""<tool_description>
<tool_name>{service_name}</tool_name>
<description>{description}</description>
<parameters>
    {{}} (Geen parameters nodig - gebruikt automatisch burger profiel)
</parameters>
</tool_description>"""
                )

        # Build the prompt with the actual available services in MCP compatible format
        return f"""
Je bent een behulpzame assistent die Nederlandse burgers helpt met vragen over overheidsregelingen.

Je hebt toegang tot de volgende tools voor het berekenen van wettelijke regelingen:

{chr(10).join(service_tools)}

HOE JE TOOLS MOET GEBRUIKEN:
1. ZEER BELANGRIJK: Wanneer een burger vraagt over een specifieke regeling zoals zorgtoeslag, huurtoeslag, of andere uitkeringen, MOET JE EERST de bijbehorende tool aanroepen VOORDAT je antwoord geeft.
2. WACHT ALTIJD op de resultaten van de tool voordat je inhoudelijk antwoord geeft.
3. Gebruik deze exacte syntax voor het aanroepen van tools:

<tool_use>
<tool_name>[naam_regeling]</tool_name>
<parameters>{{}}</parameters>
</tool_use>

Bijvoorbeeld:
<tool_use>
<tool_name>zorgtoeslag</tool_name>
<parameters>{{}}</parameters>
</tool_use>

BELANGRIJK:
- Het systeem zal je tool aanroepen detecteren, de berekening uitvoeren, en de resultaten terug aan jou geven.
- Geef NOOIT informatie over of iemand recht heeft op een regeling zonder eerst de tool aan te roepen.
- Als een burger vraagt over meerdere regelingen, roep dan één voor één de tools aan voor elke regeling.
- Blijf ALTIJD binnen de tool syntax. Gebruik geen aangepaste JSON formats of andere variaties.

Reageer in het Nederlands tenzij iemand expliciet vraagt om een andere taal.
"""

    async def process_message(self, message: str, bsn: str) -> dict[str, Any]:
        """Process a user message and execute any law services that might be referred to"""
        # Check for service references using @service notation
        service_refs = self._extract_service_references(message)
        print(f"Detected service references: {service_refs}")
        results = {}

        # Execute each referenced service
        for service_name in service_refs:
            print(f"Executing service: {service_name}")
            service = self.registry.get_service(service_name)
            if service:
                try:
                    result = await service.execute(bsn, {})
                    print(f"Service {service_name} result: {result}")
                    results[service_name] = result
                except Exception as e:
                    print(f"Error executing service {service_name}: {str(e)}")
                    import traceback

                    traceback.print_exc()
                    results[service_name] = {"error": str(e)}

        return results

    def _extract_service_references(self, message: str) -> list[str]:
        """Extract service references from LLM responses using tool syntax"""
        available_services = self.registry.get_service_names()
        referenced_services = []

        # Check for Claude tool syntax: <tool_use><tool_name>service</tool_name></tool_use>
        import re

        tool_patterns = re.findall(r"<tool_use>[\s\S]*?<tool_name>(.*?)</tool_name>[\s\S]*?</tool_use>", message)

        if tool_patterns:
            for service_name in tool_patterns:
                service_name = service_name.strip().lower()
                if service_name in available_services and service_name not in referenced_services:
                    print(f"Found tool syntax for service: {service_name}")
                    referenced_services.append(service_name)

            # Early return with found tool syntax matches
            if referenced_services:
                print(f"Extracted service references from tool syntax: {referenced_services}")
                return referenced_services

        # Also check for other common tool syntaxes that Claude might use
        # Check for JSON-like tool calls: {"name": "service_name", ...}
        json_patterns = re.findall(r'{"name"\s*:\s*"([^"]+)"', message)
        if json_patterns:
            for service_name in json_patterns:
                service_name = service_name.strip().lower()
                if service_name in available_services and service_name not in referenced_services:
                    print(f"Found JSON syntax for service: {service_name}")
                    referenced_services.append(service_name)

        # Check for Markdown code block style tool calls
        markdown_patterns = re.findall(r'```(?:json)?\s*\{\s*"name"\s*:\s*"([^"]+)"', message)
        if markdown_patterns:
            for service_name in markdown_patterns:
                service_name = service_name.strip().lower()
                if service_name in available_services and service_name not in referenced_services:
                    print(f"Found Markdown code block syntax for service: {service_name}")
                    referenced_services.append(service_name)

        # Check for @service mentions (alternative syntax)
        message_lower = message.lower()
        at_patterns = re.findall(r"@(\w+)", message_lower)
        for service_name in at_patterns:
            if service_name in available_services and service_name not in referenced_services:
                print(f"Found @service syntax for service: {service_name}")
                referenced_services.append(service_name)

        print(f"Extracted service references: {referenced_services}")
        return referenced_services

    def format_results_for_llm(self, results: dict[str, Any]) -> str:
        """Format service results for inclusion in the LLM context using a standardized markdown structure"""
        if not results:
            return ""

        formatted = "# Resultaten van uitgevoerde regelingen\n\n"

        for service_name, result in results.items():
            # Get service description if available
            service_desc = ""
            service_type = None
            law_path = None

            try:
                service = self.registry.get_service(service_name)
                if service:
                    service_desc = f" ({service.description})"
                    service_type = service.service_type
                    law_path = service.law_path
            except Exception:
                pass

            formatted += f"## {service_name}{service_desc}\n\n"

            if "error" in result:
                formatted += f"**Fout:** {result['error']}\n\n"
                continue

            formatted += f"**Komt in aanmerking:** {'Ja ✅' if result.get('eligibility') else 'Nee ❌'}\n\n"

            # Try to get rule spec for this law to determine types
            money_fields = []
            primary_outputs = []

            try:
                if service_type and law_path:
                    rule_spec = self.registry.services.resolver.get_rule_spec(law_path, "2025-01-01", service_type)
                    # Extract money fields and primary outputs
                    for output in rule_spec.get("properties", {}).get("output", []):
                        output_name = output.get("name")
                        if output.get("type") == "amount" and output.get("type_spec", {}).get("unit") == "eurocent":
                            money_fields.append(output_name)
                        if output.get("citizen_relevance") == "primary":
                            primary_outputs.append(output_name)
            except Exception as e:
                print(f"Error getting rule spec: {e}")

            # Process result data with better formatting
            result_data = result.get("result", {})
            if isinstance(result_data, dict) and result_data:
                formatted += "**Details:**\n\n"

                # First show primary outputs with proper formatting
                primary_shown = False
                for key in primary_outputs:
                    if key in result_data:
                        primary_shown = True
                        value = result_data[key]
                        if key in money_fields and isinstance(value, int | float):
                            formatted += f"- {key} (primaire waarde): **€{value / 100:.2f}**\n"
                        else:
                            formatted += f"- {key} (primaire waarde): **{value}**\n"

                if primary_shown:
                    formatted += "\n"

                # Then show other outputs with improved formatting
                for key, value in result_data.items():
                    if key not in primary_outputs:  # Skip primary outputs already shown
                        # Format monetary values when detected
                        if (
                            key in money_fields
                            and isinstance(value, int | float)
                            or isinstance(value, int | float)
                            and any(term in key.lower() for term in ["bedrag", "toeslag", "uitkering"])
                        ):
                            formatted += f"- {key}: **€{value / 100:.2f}**\n"
                        else:
                            formatted += f"- {key}: {value}\n"
                formatted += "\n"

            # Include missing requirements with better formatting
            if result.get("missing_requirements"):
                formatted += "**Ontbrekende voorwaarden:**\n\n"
                for req in result.get("missing_requirements", []):
                    formatted += f"- {req}\n"
                formatted += "\n"

            # Include explanation with proper formatting
            if result.get("explanation"):
                formatted += f"**Uitleg:** {result.get('explanation')}\n\n"

            # Add separator between results
            formatted += "---\n\n"

        return formatted
