"""
Service for interacting with the Anthropic Claude API.
"""

import os
import re

import anthropic

from explain.mcp_connector import MCPLawConnector
from machine.service import Services


class LLMService:
    """Service for interacting with Claude LLM."""

    def __init__(self, services: Services):
        """Initialize the LLM service.

        Args:
            services: The core services
        """
        self.services = services
        self.mcp_connector = MCPLawConnector(services)

        # Set up Anthropic client
        api_key = os.getenv("ANTHROPIC_API_KEY")
        if not api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=api_key)
        self.model = "claude-3-7-sonnet-20250219"
        self.max_tokens = 2000
        self.temperature = 0.7

    def get_system_prompt(self, profile: dict) -> str:
        """Generate a system prompt for the LLM.

        Args:
            profile: The user profile data

        Returns:
            A system prompt
        """
        bsn = profile.get("bsn", "")
        return self.mcp_connector.jinja_env.get_template("chat_system_prompt.j2").render(
            profile=profile, bsn=bsn, mcp_system_prompt=self.mcp_connector.get_system_prompt()
        )

    async def generate_response(self, messages: list[dict], system_prompt: str) -> str:
        """Generate a response from Claude.

        Args:
            messages: The conversation history
            system_prompt: The system prompt

        Returns:
            The generated response
        """
        response = self.client.messages.create(
            model=self.model,
            max_tokens=self.max_tokens,
            system=system_prompt,
            messages=messages,
            temperature=self.temperature,
        )

        return response.content[0].text

    async def process_message_with_services(self, message: str, bsn: str) -> dict:
        """Process a message and execute any services referenced in it.

        Args:
            message: The message to process
            bsn: The BSN of the user

        Returns:
            The results of processing the message
        """
        return await self.mcp_connector.process_message(message, bsn)

    def format_service_results(self, results: dict) -> str:
        """Format service results for the LLM.

        Args:
            results: The service results

        Returns:
            Formatted results
        """
        return self.mcp_connector.format_results_for_llm(results)

    @staticmethod
    def clean_message(message_text: str) -> str:
        """Clean an LLM message by removing tool blocks.

        Args:
            message_text: The message text to clean

        Returns:
            The cleaned message
        """
        # Remove tool_use blocks
        cleaned = re.sub(r"<tool_use>[\s\S]*?<\/tool_use>", "", message_text)
        # Remove any empty lines that might be left
        cleaned = re.sub(r"\n\s*\n+", "\n\n", cleaned)
        return cleaned.strip()
