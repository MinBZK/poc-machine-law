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

        # Add a claim tool for submitting values
        claim_tool = """<tool_description>
<tool_name>claim_value</tool_name>
<description>Gebruiken wanneer een burger specifieke informatie verstrekt over zichzelf die nodig is voor een berekening</description>
<parameters>
    {"service": "De regeling waarvoor deze waarde geldt (bijv. zorgtoeslag)",
     "key": "De naam van het gegeven (bijv. inkomen, leeftijd, aantal_kinderen)",
     "value": "De waarde die de burger heeft opgegeven. BELANGRIJK: voor geldbedragen, zet deze om naar EUROCENTEN (bijv. €42,50 wordt 4250)"}
</parameters>
</tool_description>"""

        service_tools.append(claim_tool)

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

CLAIMS VOOR ONTBREKENDE GEGEVENS:
Wanneer de berekening aangeeft dat er essentiële gegevens ontbreken:
1. Vraag de burger vriendelijk om de ontbrekende informatie
2. Wanneer de burger antwoordt met de waarde, gebruik de claim_value tool:

<tool_use>
<tool_name>claim_value</tool_name>
<parameters>
  {{"service": "zorgtoeslag", "key": "inkomen", "value": 3500000}}
</parameters>
</tool_use>

3. Roep daarna meteen opnieuw de oorspronkelijke regeling-tool aan om een nieuwe berekening te maken met de ingevulde waarde

GECHAINEDE WETTEN:
Alleen als de gebruiker er om vraagt, of als het logisch is:
1. Voeg NA je antwoord aan de burger een tweede tool call toe met de gerelateerde regeling:

<tool_use>
<tool_name>zorgtoeslag</tool_name>
<parameters>{{}}</parameters>
</tool_use>

Het systeem zal automatisch deze tweede regeling uitvoeren nadat de burger jouw eerste antwoord heeft gezien.

Je kunt MEERDERE WETTEN ACHTER ELKAAR CHAINEN als dat nodig is kun je na je antwoord over de tweede wet een volgende
tool call toevoegen voor de derde wet.
Dit kan doorgaan zo lang als nodig is om de burger volledig te informeren.


BELANGRIJK:
- Het systeem zal je tool aanroepen detecteren, de berekening uitvoeren, en de resultaten terug aan jou geven.
- Geef NOOIT informatie over of iemand recht heeft op een regeling zonder eerst de tool aan te roepen.
- Als een burger vraagt over meerdere regelingen, roep dan één voor één de tools aan voor elke regeling.
- Blijf ALTIJD binnen de tool syntax. Gebruik geen aangepaste JSON formats of andere variaties.
- Als essentiële gegevens ontbreken, vraag hier expliciet naar en gebruik de claim_value tool om ze toe te voegen.
- Gebruik gechainede wetten alleen als dit logisch is of als er om gevraagd wordt
- Verwijs NOOIT naar externe websites of applicaties zoals toeslagen.nl, belastingdienst.nl, DUO, of overheids-apps
- Hou je focus op de uitleg van de wet en rechten zoals berekend door de tool; geef geen advies over hoe aanvragen buiten dit systeem gedaan moeten worden
- Geen verwijzingen naar "aanvragen" of "indienen" bij externe instanties - ga ervan uit dat alles via dit systeem gebeurt
- BELANGRIJK: Zorg dat je bij geldbedragen ALTIJD EUROCENTEN gebruikt (bijv. €42,50 wordt 4250 cent)

Reageer in het Nederlands tenzij iemand expliciet vraagt om een andere taal.
"""

    async def process_message(self, message: str, bsn: str) -> dict[str, Any]:
        """Process a user message and execute any law services that might be referred to"""
        # Check for service references using @service notation and claim value tool
        service_refs = self._extract_service_references(message)
        claim_refs = self._extract_claim_references(message)

        print(f"Detected service references: {service_refs}")
        print(f"Detected claim references: {claim_refs}")

        results = {}

        # Process any claims first
        if claim_refs:
            claims_result = await self._process_claims(claim_refs, bsn)
            if claims_result:
                results["claims"] = claims_result

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

    def _extract_claim_references(self, message: str) -> list[dict]:
        """Extract claim references from the message"""
        import json
        import re

        claims = []

        # Search for claim_value tool calls
        claim_pattern = r"<tool_use>[\s\S]*?<tool_name>claim_value</tool_name>[\s\S]*?<parameters>([\s\S]*?)</parameters>[\s\S]*?</tool_use>"

        # Find all matches
        matches = re.findall(claim_pattern, message)

        for match in matches:
            try:
                # Try to parse the JSON parameters
                # Clean up the JSON string - remove extra whitespace, fix quotes
                clean_json = match.strip().replace("'", '"')
                if not clean_json.startswith("{"):
                    continue

                # Sometimes JSON is malformed due to LLM output formatting issues
                try:
                    clean_json = re.sub(r",\s*}", "}", clean_json)  # Remove trailing commas
                    clean_json = re.sub(
                        r'"\s*:\s*"([^"]*?)(\d+)"', r'": \2', clean_json
                    )  # Fix numeric values in quotes

                    claim_data = json.loads(clean_json)
                except json.JSONDecodeError:
                    # Additional attempt with more robust parsing
                    try:
                        # Extract key-value pairs manually with regex
                        service_match = re.search(r'"service"\s*:\s*"([^"]+)"', clean_json)
                        key_match = re.search(r'"key"\s*:\s*"([^"]+)"', clean_json)
                        value_match = re.search(r'"value"\s*:\s*([^,}]+)', clean_json)

                        if service_match and key_match and value_match:
                            service = service_match.group(1)
                            key = key_match.group(1)
                            value_str = value_match.group(1).strip('"')

                            # Try to convert value to appropriate type
                            try:
                                value = int(value_str)
                            except ValueError:
                                try:
                                    value = float(value_str)
                                except ValueError:
                                    value = value_str

                            claim_data = {"service": service, "key": key, "value": value}
                        else:
                            print(f"Couldn't extract claim data from: {clean_json}")
                            continue
                    except Exception as e:
                        print(f"Error with manual claim parsing: {e}")
                        continue
                # Add a unique ID to the claim data to prevent duplicate processing
                # This is based on the exact content of the claim
                claim_with_id = claim_data.copy()
                claim_with_id["_id"] = f"{claim_data.get('service', '')}-{claim_data.get('key', '')}"

                # Check if this is a duplicate claim within this batch
                is_duplicate = False
                for existing_claim in claims:
                    if existing_claim.get("_id") == claim_with_id.get("_id"):
                        is_duplicate = True
                        break

                if not is_duplicate:
                    claims.append(claim_with_id)
                    print(f"Parsed claim: {claim_with_id}")
                else:
                    print(f"Skipping duplicate claim: {claim_with_id}")
            except json.JSONDecodeError as e:
                print(f"Error parsing claim JSON: {e}")
                print(f"Raw match: {match}")
                continue
            except Exception as e:
                print(f"Error processing claim: {e}")
                continue

        return claims

    async def _process_claims(self, claims: list[dict], bsn: str) -> dict:
        """Process claim references and create claims"""
        import traceback

        results = {"submitted": [], "errors": []}

        for claim in claims:
            try:
                service_name = claim.get("service")
                key = claim.get("key")
                value = claim.get("value")

                if not all([service_name, key, value is not None]):
                    error = "Missing required claim parameters (service, key, value)"
                    results["errors"].append({"claim": claim, "error": error})
                    continue

                # Find the service
                service = self.registry.get_service(service_name)
                if not service:
                    error = f"Unknown service: {service_name}"
                    results["errors"].append({"claim": claim, "error": error})
                    continue

                # Submit the claim
                claim_id = self.registry.services.claim_manager.submit_claim(
                    service=service.service_type,
                    key=key,
                    new_value=value,
                    reason="Gebruiker gaf waarde door via chat.",
                    claimant=f"CHAT_USER_{bsn}",
                    law=service.law_path,
                    bsn=bsn,
                    auto_approve=True,  # Auto-approve user-provided values in chat
                )

                results["submitted"].append(
                    {"claim_id": claim_id, "service": service_name, "key": key, "value": value, "status": "approved"}
                )

                print(f"Created claim {claim_id} for {key}={value} for service {service_name}")

            except Exception as e:
                print(f"Error submitting claim: {str(e)}")
                traceback.print_exc()
                results["errors"].append({"claim": claim, "error": str(e)})

        return results

    def _extract_service_references(self, message: str) -> list[str]:
        """Extract service references from LLM responses using tool syntax"""
        available_services = self.registry.get_service_names()
        referenced_services = []

        # Check for Claude tool syntax: <tool_use><tool_name>service</tool_name></tool_use>
        import re

        # Check multiple patterns that Claude might use for tool calls
        tool_patterns = re.findall(r"<tool_use>[\s\S]*?<tool_name>(.*?)</tool_name>[\s\S]*?</tool_use>", message)
        # Alternative patterns that Claude sometimes uses
        tool_patterns_alt1 = re.findall(r"<tool>\s*<name>(.*?)</name>", message)
        tool_patterns_alt2 = re.findall(r"<tool name=\"([^\"]+)\"", message)

        # Combine all pattern matches
        all_tool_patterns = tool_patterns + tool_patterns_alt1 + tool_patterns_alt2

        if all_tool_patterns:
            for service_name in all_tool_patterns:
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

        # Handle claim results if present
        if "claims" in results:
            claims_result = results["claims"]
            formatted += "## Ingediende claims\n\n"

            if claims_result.get("submitted"):
                formatted += "**De volgende gegevens zijn succesvol ingediend:**\n\n"
                for claim in claims_result["submitted"]:
                    value_display = claim["value"]
                    # Format euro values
                    if isinstance(value_display, int) and (
                        "inkomen" in claim["key"].lower() or "bedrag" in claim["key"].lower()
                    ):
                        value_display = f"€{value_display / 100:.2f}"
                    formatted += f"- {claim['key'].replace('_', ' ')}: **{value_display}** (voor {claim['service']})\n"
                formatted += "\n"

            if claims_result.get("errors"):
                formatted += "**Er waren problemen met de volgende claims:**\n\n"
                for error in claims_result["errors"]:
                    formatted += f"- {error.get('claim', {}).get('key', 'Onbekend veld')}: {error.get('error', 'Onbekende fout')}\n"
                formatted += "\n"

            formatted += "---\n\n"

        # Process service results
        for service_name, result in results.items():
            # Skip the claims entry
            if service_name == "claims":
                continue

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

            # Check requirements_met and missing_required fields first
            # These are important to understand if the person is eligible
            if "requirements_met" in result:
                if not result.get("requirements_met"):
                    formatted += "**Voldoet niet aan alle voorwaarden ❌**\n\n"
                else:
                    formatted += "**Voldoet aan alle voorwaarden ✅**\n\n"
            else:
                # Fallback to eligibility field if requirements_met is not available
                formatted += f"**Komt in aanmerking:** {'Ja ✅' if result.get('eligibility') else 'Nee ❌'}\n\n"

            # Handle missing_required specifically
            if result.get("missing_required"):
                formatted += "**U kunt geen aanvraag indienen omdat er essentiële informatie ontbreekt.**\n\n"

                # If there's a missing_fields list in the result, show those
                if isinstance(result.get("missing_fields"), list) and result.get("missing_fields"):
                    formatted += "**Ontbrekende velden:**\n\n"
                    for req in result.get("missing_fields", []):
                        formatted += f"- {req}\n"
                    formatted += "\n"
                # Otherwise just show the generic message
                else:
                    formatted += "Vul de benodigde informatie in om verder te gaan.\n\n"

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

            # Include missing requirements with better formatting (only if not missing_required)
            if result.get("missing_requirements") and not result.get("missing_required"):
                formatted += "**Ontbrekende voorwaarden (niet-essentieel):**\n\n"
                for req in result.get("missing_requirements", []):
                    formatted += f"- {req}\n"
                formatted += "\n"

            # Include explanation with proper formatting
            if result.get("explanation"):
                formatted += f"**Uitleg:** {result.get('explanation')}\n\n"

            # Add separator between results
            formatted += "---\n\n"

        return formatted
