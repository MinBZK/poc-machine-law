"""
MCP Claim processing module for handling user claims in the MCP system.
"""

import json
import re

from .mcp_exceptions import (
    MCPClaimParsingError,
    MCPClaimSubmissionError,
    MCPClaimValidationError,
    MCPServiceNotFoundError,
)
from .mcp_logging import log_claim_submission, log_error, logger
from .mcp_services import MCPServiceRegistry
from .mcp_types import ClaimData, ClaimsResponse


class MCPClaimProcessor:
    """Processor for handling claims in MCP messages."""

    def __init__(self, registry: MCPServiceRegistry):
        """Initialize the claim processor.

        Args:
            registry: The MCP service registry for resolving services
        """
        self.registry = registry

    def extract_claims(self, message: str) -> list[ClaimData]:
        """Extract claims from the message.

        Args:
            message: The message to extract claims from

        Returns:
            List of extracted claim data
        """
        claims = []

        # Search for claim_value tool calls
        claim_pattern = r"<tool_use>[\s\S]*?<tool_name>claim_value</tool_name>[\s\S]*?<parameters>([\s\S]*?)</parameters>[\s\S]*?</tool_use>"

        # Find all matches
        matches = re.findall(claim_pattern, message)

        for match in matches:
            try:
                # Clean up the JSON string - remove extra whitespace, fix quotes
                clean_json = match.strip().replace("'", '"')
                if not clean_json.startswith("{"):
                    logger.warning(f"Skipping invalid claim format: {match}")
                    continue

                # Process JSON with enhanced error handling
                claim_data = self._parse_claim_json(clean_json)

                # Add a unique ID to the claim data to prevent duplicate processing
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
                    logger.debug(f"Parsed claim: {claim_with_id}")
                else:
                    logger.info(f"Skipping duplicate claim: {claim_with_id}")

            except MCPClaimParsingError as e:
                log_error(e)
                continue
            except Exception as e:
                log_error(e, {"match": match})
                continue

        return claims

    def _parse_claim_json(self, json_str: str) -> ClaimData:
        """Parse a claim JSON string.

        Args:
            json_str: The JSON string to parse

        Returns:
            Parsed claim data

        Raises:
            MCPClaimParsingError: If parsing fails
        """
        try:
            # First try standard JSON parsing with some cleanup
            clean_json = re.sub(r",\s*}", "}", json_str)  # Remove trailing commas
            clean_json = re.sub(r'"\s*:\s*"([^"]*?)(\d+)"', r'": \2', clean_json)  # Fix numeric values in quotes

            claim_data = json.loads(clean_json)
            return claim_data
        except json.JSONDecodeError:
            # Additional attempt with more robust parsing
            try:
                # Extract key-value pairs manually with regex
                service_match = re.search(r'"service"\s*:\s*"([^"]+)"', json_str)
                key_match = re.search(r'"key"\s*:\s*"([^"]+)"', json_str)
                value_match = re.search(r'"value"\s*:\s*([^,}]+)', json_str)

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

                    return {"service": service, "key": key, "value": value}
                else:
                    logger.warning(f"Couldn't extract claim data from: {json_str}")
                    raise MCPClaimParsingError(Exception("Missing required fields in claim"), json_str)
            except Exception as e:
                raise MCPClaimParsingError(e, json_str)

    def process_claims(self, claims: list[ClaimData], bsn: str) -> ClaimsResponse:
        """Process claim references and create claims.

        Args:
            claims: List of claims to process
            bsn: The BSN of the user

        Returns:
            Processed claims response
        """
        results: ClaimsResponse = {"submitted": [], "errors": []}

        for claim in claims:
            try:
                # Validate claim data
                self._validate_claim(claim)

                service_name = claim["service"]
                key = claim["key"]
                value = claim["value"]

                # Find the service
                service = self.registry.get_service(service_name)
                if not service:
                    raise MCPServiceNotFoundError(service_name)

                # Log claim submission
                log_claim_submission(service_name, key, bsn)

                # Submit the claim
                try:
                    claim_id = self.registry.claim_manager.submit_claim(
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
                        {
                            "claim_id": claim_id,
                            "service": service_name,
                            "key": key,
                            "value": value,
                            "status": "approved",
                        }
                    )

                    logger.info(f"Created claim {claim_id} for {key}={value} for service {service_name}")

                except Exception as e:
                    raise MCPClaimSubmissionError(e, claim)

            except (MCPClaimValidationError, MCPServiceNotFoundError, MCPClaimSubmissionError) as e:
                log_error(e)
                results["errors"].append({"claim": claim, "error": str(e)})
            except Exception as e:
                log_error(e, {"claim": claim})
                results["errors"].append({"claim": claim, "error": f"Unexpected error: {str(e)}"})

        return results

    def _validate_claim(self, claim: ClaimData) -> None:
        """Validate claim data.

        Args:
            claim: The claim data to validate

        Raises:
            MCPClaimValidationError: If validation fails
        """
        # Check required fields
        service_name = claim.get("service")
        key = claim.get("key")
        value = claim.get("value")

        if not all([service_name, key, value is not None]):
            raise MCPClaimValidationError("Missing required claim parameters (service, key, value)", claim)
