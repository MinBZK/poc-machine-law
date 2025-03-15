"""
Chat session management for handling conversations.
"""

import logging
from typing import Any

from web.services.chat_connection import manager as connection_manager
from web.services.llm_service import LLMService
from web.services.profiles import get_profile_data

# Set up logging
logger = logging.getLogger(__name__)

# Configure logging format if not already configured
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s - %(name)s - %(levelname)s - %(message)s")
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    logger.setLevel(logging.INFO)


class ChatSession:
    """Manages a chat session with a user."""

    def __init__(self, client_id: str, llm_service: LLMService):
        """Initialize a chat session.

        Args:
            client_id: The client ID for the chat session
            llm_service: The LLM service to use
        """
        self.client_id = client_id
        self.llm_service = llm_service
        self.messages: list[dict[str, str]] = []
        self.system_prompt: str | None = None
        self.bsn = self._extract_bsn_from_client_id(client_id)
        self.profile = get_profile_data(self.bsn)
        self.processed_services: set[str] = set()

    def _extract_bsn_from_client_id(self, client_id: str) -> str:
        """Extract the BSN from the client ID.

        Args:
            client_id: The client ID

        Returns:
            The BSN
        """
        return client_id.split("_")[1] if "_" in client_id else "100000001"

    def setup_system_prompt(self) -> None:
        """Set up the system prompt for the session."""
        if not self.profile:
            raise ValueError(f"Profile not found for BSN: {self.bsn}")

        self.system_prompt = self.llm_service.get_system_prompt(self.profile)

    async def add_user_message(self, content: str) -> None:
        """Add a user message to the conversation.

        Args:
            content: The message content
        """
        self.messages.append({"role": "user", "content": content})

    async def generate_response(self) -> str:
        """Generate a response from the LLM.

        Returns:
            The generated response
        """
        response = await self.llm_service.generate_response(messages=self.messages, system_prompt=self.system_prompt)

        # Add the response to the conversation history
        self.messages.append({"role": "assistant", "content": response})

        return response

    async def process_service_calls(self, message: str) -> dict[str, Any] | None:
        """Process any service calls in the message.

        Args:
            message: The message to process

        Returns:
            The service results, if any
        """
        results = await self.llm_service.process_message_with_services(message, self.bsn)
        if not results:
            return None

        return results

    async def generate_response_with_tool_results(self, tool_results: dict[str, Any]) -> str:
        """Generate a response with tool results.

        Args:
            tool_results: The tool results

        Returns:
            The generated response
        """
        # Format the results
        formatted_results = self.llm_service.format_service_results(tool_results)

        # Get the last assistant message
        last_assistant_message = self.messages[-1]["content"]

        # Create a tool message
        tool_message = {"role": "assistant", "content": last_assistant_message}

        # Get template for tool response
        if "claims" in tool_results:
            missing_fields = []
            for service_name, result in tool_results.items():
                if service_name == "claims":
                    continue
                if isinstance(result.get("missing_fields"), list) and result.get("missing_fields"):
                    missing_fields.extend([(service_name, field) for field in result.get("missing_fields")])

            content = self.llm_service.mcp_connector.jinja_env.get_template("tool_response.j2").render(
                service_context=formatted_results, missing_fields=missing_fields if missing_fields else None
            )
        else:
            # Determine the source of the result
            service_name = next(iter([k for k in tool_results if k != "claims"]), "")

            # Check if this was from a claim
            is_from_claim = False  # This would need to be determined from context

            if is_from_claim:
                content = self.llm_service.mcp_connector.jinja_env.get_template("claim_processing.j2").render(
                    service_name=service_name, service_context=formatted_results
                )
            else:
                content = self.llm_service.mcp_connector.jinja_env.get_template("chained_service.j2").render(
                    service_name=service_name, service_context=formatted_results
                )

        # Add tool response as user message
        tool_response = {"role": "user", "content": content}

        # Create a new conversation with the tool interaction
        tool_conversation = self.messages.copy()
        tool_conversation.append(tool_message)
        tool_conversation.append(tool_response)

        # Get a new response from Claude with the tool results
        final_response = await self.llm_service.generate_response(
            messages=tool_conversation, system_prompt=self.system_prompt
        )

        # Update conversation history
        self.messages.append(tool_message)
        self.messages.append(tool_response)
        self.messages.append({"role": "assistant", "content": final_response})

        return final_response

    async def process_next_step(self, assistant_message: str) -> tuple[bool, str | None]:
        """Process the next step in the conversation chain recursively.

        This handles both claim_value tools and service tools in a single recursive function.
        For claims, it processes them and then re-executes the relevant service.
        For service tools, it executes the requested service.
        In both cases, it continues the recursion with the new response.

        Args:
            assistant_message: The assistant's message

        Returns:
            A tuple of (continue_processing, response_message)
        """
        logger.info("Processing next step in chain")

        # Create fresh list of services to execute for this recursion level only
        services_to_execute = []

        # First check for claims - they take precedence
        claim_refs = self.llm_service.mcp_connector.claim_processor.extract_claims(assistant_message)
        claims_detected = bool(claim_refs)

        if claim_refs:
            logger.info(f"Found {len(claim_refs)} claim references in message")
            claims_result = await self.llm_service.mcp_connector.claim_processor.process_claims(claim_refs, self.bsn)

            if claims_result and claims_result.get("submitted"):
                # Collect affected services for execution
                for claim in claims_result.get("submitted", []):
                    service_name = claim.get("service")
                    if service_name and service_name not in services_to_execute:
                        services_to_execute.append(service_name)
                        logger.info(f"Adding service {service_name} to execution list due to claim")

        # Then check for service references
        service_refs = self.llm_service.mcp_connector.service_executor.extract_service_references(assistant_message)
        if service_refs:
            for service_name in service_refs:
                if service_name not in services_to_execute:
                    services_to_execute.append(service_name)
                    logger.info(f"Adding service {service_name} to execution list due to tool call")

        # If no services to execute, we're done with the recursion
        if not services_to_execute:
            logger.info("No services to execute, ending recursion")
            return False, None

        # Execute each service in order, but skip already processed ones in this chain
        for service_name in services_to_execute:
            # Skip if we've already processed this service in this chain
            if service_name in self.processed_services:
                logger.info(f"Skipping already processed service {service_name} in this chain")
                continue

            # Add to processed services set
            self.processed_services.add(service_name)

            service = self.llm_service.mcp_connector.registry.get_service(service_name)
            if not service:
                logger.warning(f"Service {service_name} not found, skipping")
                continue

            # Let the user know we're executing this service
            await connection_manager.send_processing_indicator(
                f"Ik ga nu kijken naar uw recht op {service_name}... ⏳", self.client_id
            )

            try:
                # Execute the service
                result = await service.execute(self.bsn, {})
                service_results = {service_name: result}

                # Format the results
                service_context = self.llm_service.format_service_results(service_results)

                # Create message prompt based on context
                is_from_claim = claims_detected

                if is_from_claim:
                    content = self.llm_service.mcp_connector.jinja_env.get_template("claim_processing.j2").render(
                        service_name=service_name, service_context=service_context
                    )
                else:
                    content = self.llm_service.mcp_connector.jinja_env.get_template("chained_service.j2").render(
                        service_name=service_name, service_context=service_context
                    )

                # Create a new response from the LLM with service results
                # First add the content to the message history
                self.messages.append({"role": "user", "content": content})

                # Generate the response
                next_message = await self.llm_service.generate_response(
                    messages=self.messages, system_prompt=self.system_prompt
                )

                # Add the LLM response to the conversation history
                self.messages.append({"role": "assistant", "content": next_message})

                # Clean the message before sending to client
                cleaned_next_message = self.llm_service.clean_message(next_message)

                # Send to client
                await connection_manager.send_json({"message": cleaned_next_message}, self.client_id)

                # Return the message for further processing
                # Do NOT recursively process here - that would lead to infinite recursion
                # Instead, we'll handle recursion in _recursive_process_next_steps
                return True, next_message

            except Exception as e:
                logger.error(f"Error executing service {service_name}: {str(e)}")
                import traceback

                logger.error(f"Traceback: {traceback.format_exc()}")

        # If we got here, we processed all services but none of them were executable
        return False, None

    async def _recursive_process_next_steps(self, message: str) -> None:
        """Process next steps recursively to handle complex chains.

        Args:
            message: The message to process
        """
        # Reset the processed_services set for a new chain
        # This is important because we want to evaluate all services mentioned in each message
        self.processed_services = set()

        # Continue processing recursively to handle multiple chained services
        continue_processing = True
        current_message = message

        # Limit the recursion depth to prevent infinite loops
        max_depth = 5
        current_depth = 0

        # Loop until we have no more services to process or reach max depth
        while continue_processing and current_depth < max_depth:
            current_depth += 1
            logger.info(f"Processing chain recursion depth: {current_depth}")

            # Reset the processed_services set for each new message
            # This allows the same service to be processed again if referenced in a new message
            self.processed_services = set()

            # Process the current message
            continue_processing, next_message = await self.process_next_step(current_message)

            # If we got a new message, use it for the next iteration
            if continue_processing and next_message:
                logger.info("Chain continues to next message")
                current_message = next_message
            else:
                logger.info("Chain complete - no more services to process")
                continue_processing = False
