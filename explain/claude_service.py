import os
from typing import Any

import anthropic

from .base_llm_service import BaseLLMService


class ClaudeService(BaseLLMService):
    """Service for connecting to Claude API"""

    def __init__(self) -> None:
        self.api_key = os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("ANTHROPIC_API_KEY environment variable not set")

        self.client = anthropic.Anthropic(api_key=self.api_key)
        self._model_id = "claude-3-7-sonnet-20250219"

    @property
    def provider_name(self) -> str:
        return "claude"

    @property
    def model_id(self) -> str:
        return self._model_id

    def create_chat_client(self) -> anthropic.Anthropic:
        """Create a new Anthropic client instance

        Returns:
            Anthropic client
        """
        return anthropic.Anthropic(api_key=self.api_key)

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> Any:
        """Make a chat completion request to Claude

        Args:
            messages: List of message objects with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            system: System prompt

        Returns:
            Anthropic API response
        """
        return self.client.messages.create(
            model=self.model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system,
            messages=messages,
        )

    def get_completion_text(self, response: Any) -> str:
        """Extract the completion text from a Claude response

        Args:
            response: Claude API response

        Returns:
            Extracted text content
        """
        return response.content[0].text


# Initialize the service as a singleton
claude_service = ClaudeService()
