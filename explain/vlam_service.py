import os
from typing import Any

from openai import OpenAI

from .base_llm_service import BaseLLMService


class VLAMService(BaseLLMService):
    """Service for connecting to VLAM.ai LLM with OpenAI-compatible API"""

    def __init__(self) -> None:
        self.api_key = os.getenv("VLAM_API_KEY")
        self.base_url = os.getenv("VLAM_BASE_URL", "https://api.demo.vlam.ai/v2.1/projects/poc/openai-compatible/v1")
        self._model_id = os.getenv("VLAM_MODEL_ID", "ubiops-deployment/bzk-dig-chat//chat-model")

        if not self.api_key:
            raise ValueError("VLAM_API_KEY environment variable not set")

        # Create OpenAI client with custom base URL
        self.client = OpenAI(api_key=self.api_key, base_url=self.base_url)

    @property
    def provider_name(self) -> str:
        return "vlam"

    @property
    def model_id(self) -> str:
        return self._model_id

    def create_chat_client(self) -> OpenAI:
        """Create a new OpenAI client instance for VLAM.ai

        Returns:
            OpenAI client configured for VLAM.ai
        """
        return OpenAI(api_key=self.api_key, base_url=self.base_url)

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system: str | None = None,
    ) -> Any:
        """Make a chat completion request to VLAM.ai using OpenAI-compatible API

        Args:
            messages: List of message objects with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            system: System prompt

        Returns:
            OpenAI API response
        """
        # If system is provided, add it as the first message
        all_messages = messages.copy()
        if system:
            all_messages.insert(0, {"role": "system", "content": system})

        return self.client.chat.completions.create(
            model=self.model_id,
            messages=all_messages,
            max_tokens=max_tokens,
            temperature=temperature,
        )

    def get_completion_text(self, response: Any) -> str:
        """Extract the completion text from an OpenAI-compatible response

        Args:
            response: OpenAI API response

        Returns:
            Extracted text content
        """
        return response.choices[0].message.content


# Initialize as singleton if needed
vlam_service = VLAMService()
