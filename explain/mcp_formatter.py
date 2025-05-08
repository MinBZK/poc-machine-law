"""
MCP Formatter for formatting service execution results.
"""

from typing import Any

from .mcp_logging import logger
from .mcp_services import MCPServiceRegistry
from .mcp_types import ClaimsResponse, MCPResult


class MCPResultFormatter:
    """Formatter for MCP results."""

    def __init__(self, registry: MCPServiceRegistry):
        """Initialize the formatter.

        Args:
            registry: The MCP service registry
        """
        self.registry = registry

    def format_for_llm(self, results: MCPResult) -> str:
        """Format service results for inclusion in the LLM context.

        Args:
            results: The results to format

        Returns:
            Formatted results as markdown
        """
        if not results:
            return ""

        formatted = "# Resultaten van uitgevoerde regelingen\n\n"

        # Handle claim results if present
        if "claims" in results:
            formatted += self._format_claims_section(results["claims"])

        # Process service results
        for service_name, result in results.items():
            # Skip the claims entry
            if service_name == "claims":
                continue

            formatted += self._format_service_section(service_name, result)

        return formatted

    def _format_claims_section(self, claims_result: ClaimsResponse) -> str:
        """Format the claims section.

        Args:
            claims_result: The claims result to format

        Returns:
            Formatted claims section
        """
        formatted = "## Ingediende claims\n\n"

        if claims_result.get("submitted"):
            formatted += "**De volgende gegevens zijn succesvol ingediend:**\n\n"
            for claim in claims_result["submitted"]:
                value_display = claim["value"]
                # Format euro values
                if isinstance(value_display, int) and (
                    "inkomen" in claim["key"].lower() or "bedrag" in claim["key"].lower()
                ):
                    value_display = f"€{value_display / 100:.2f}".replace(".", ",")
                formatted += f"- {claim['key'].replace('_', ' ')}: **{value_display}** (voor {claim['service']})\n"
            formatted += "\n"

        if claims_result.get("errors"):
            formatted += "**Er waren problemen met de volgende claims:**\n\n"
            for error in claims_result["errors"]:
                formatted += (
                    f"- {error.get('claim', {}).get('key', 'Onbekend veld')}: {error.get('error', 'Onbekende fout')}\n"
                )
            formatted += "\n"

        formatted += "---\n\n"
        return formatted

    def _format_service_section(self, service_name: str, result: dict[str, Any]) -> str:
        """Format a service section.

        Args:
            service_name: The name of the service
            result: The service result

        Returns:
            Formatted service section
        """
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
        except Exception as e:
            logger.error(f"Error getting service info: {e}")

        formatted = f"## {service_name}{service_desc}\n\n"

        if "error" in result:
            formatted += f"**Fout:** {result['error']}\n\n"
            formatted += "---\n\n"
            return formatted

        # Format eligibility information
        formatted += self._format_eligibility(result)

        # Handle missing required fields
        if result.get("missing_required"):
            formatted += self._format_missing_required(result)

        # Get field types
        money_fields, primary_outputs = self._get_field_types(service_type, law_path)

        # Format result data
        formatted += self._format_result_data(result, money_fields, primary_outputs)

        # Include missing requirements
        formatted += self._format_missing_requirements(result)

        # Include explanation
        if result.get("explanation"):
            formatted += f"**Uitleg:** {result.get('explanation')}\n\n"

        # Add separator
        formatted += "---\n\n"
        return formatted

    def _format_eligibility(self, result: dict[str, Any]) -> str:
        """Format eligibility information.

        Args:
            result: The service result

        Returns:
            Formatted eligibility information
        """
        if "requirements_met" in result:
            if not result.get("requirements_met"):
                return "**Voldoet niet aan alle voorwaarden ❌**\n\n"
            else:
                return "**Voldoet aan alle voorwaarden ✅**\n\n"
        else:
            # Fallback to eligibility field if requirements_met is not available
            return f"**Komt in aanmerking:** {'Ja ✅' if result.get('eligibility') else 'Nee ❌'}\n\n"

    def _format_missing_required(self, result: dict[str, Any]) -> str:
        """Format missing required fields information.

        Args:
            result: The service result

        Returns:
            Formatted missing required fields
        """
        formatted = "**U kunt geen aanvraag indienen omdat er essentiële informatie ontbreekt.**\n\n"

        # If there's a missing_fields list in the result, show those
        if isinstance(result.get("missing_fields"), list) and result.get("missing_fields"):
            formatted += "**Ontbrekende velden:**\n\n"
            for req in result.get("missing_fields", []):
                formatted += f"- {req}\n"
            formatted += "\n"
        # Otherwise just show the generic message
        else:
            formatted += "Vul de benodigde informatie in om verder te gaan.\n\n"

        return formatted

    def _get_field_types(self, service_type: str | None, law_path: str | None) -> tuple[list[str], list[str]]:
        """Get field types from the rule spec.

        Args:
            service_type: The service type
            law_path: The law path

        Returns:
            Tuple of (money_fields, primary_outputs)
        """
        money_fields = []
        primary_outputs = []

        try:
            if service_type and law_path:
                rule_spec = self.registry.services.get_rule_spec(law_path, "2025-01-01", service_type)
                # Extract money fields and primary outputs
                for output in rule_spec.get("properties", {}).get("output", []):
                    output_name = output.get("name")
                    if output.get("type") == "amount" and output.get("type_spec", {}).get("unit") == "eurocent":
                        money_fields.append(output_name)
                    if output.get("citizen_relevance") == "primary":
                        primary_outputs.append(output_name)
        except Exception as e:
            logger.error(f"Error getting rule spec: {e}")

        return money_fields, primary_outputs

    def _format_result_data(self, result: dict[str, Any], money_fields: list[str], primary_outputs: list[str]) -> str:
        """Format result data.

        Args:
            result: The service result
            money_fields: List of money fields
            primary_outputs: List of primary outputs

        Returns:
            Formatted result data
        """
        formatted = ""
        result_data = result.get("result", {})

        if not isinstance(result_data, dict) or not result_data:
            return formatted

        formatted += "**Details:**\n\n"

        # First show primary outputs with proper formatting
        primary_shown = False
        for key in primary_outputs:
            if key in result_data:
                primary_shown = True
                value = result_data[key]
                if key in money_fields and isinstance(value, int | float):
                    formatted += f"- {key} (primaire waarde): **€{value / 100:.2f}".replace(".", ",") + "**\n"
                else:
                    formatted += f"- {key} (primaire waarde): **{value}**\n"

        if primary_shown:
            formatted += "\n"

        # Then show other outputs with improved formatting
        for key, value in result_data.items():
            if key not in primary_outputs:  # Skip primary outputs already shown
                # Format monetary values when detected
                is_money = (
                    key in money_fields
                    and isinstance(value, int | float)
                    or isinstance(value, int | float)
                    and any(term in key.lower() for term in ["bedrag", "toeslag", "uitkering"])
                )

                if is_money:
                    formatted += f"- {key}: **€{value / 100:.2f}".replace(".", ",") + "**\n"
                else:
                    formatted += f"- {key}: {value}\n"

        formatted += "\n"
        return formatted

    def _format_missing_requirements(self, result: dict[str, Any]) -> str:
        """Format missing requirements.

        Args:
            result: The service result

        Returns:
            Formatted missing requirements
        """
        if not result.get("missing_requirements") or result.get("missing_required"):
            return ""

        formatted = "**Ontbrekende voorwaarden (niet-essentieel):**\n\n"
        for req in result.get("missing_requirements", []):
            formatted += f"- {req}\n"
        formatted += "\n"

        return formatted
