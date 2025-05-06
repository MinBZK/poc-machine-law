import os
from typing import Any

from fastapi import Request
from openai import OpenAI

from .base_llm_service import BaseLLMService


class VLAMService(BaseLLMService):
    """Service for connecting to VLAM.ai LLM with OpenAI-compatible API"""

    SESSION_KEY = "vlam_api_key"
    ENV_KEY = "VLAM_API_KEY"

    def __init__(self) -> None:
        self.api_key = os.getenv(self.ENV_KEY)
        self.base_url = os.getenv("VLAM_BASE_URL", "https://api.demo.vlam.ai/v2.1/projects/poc/openai-compatible/v1")
        self._model_id = os.getenv("VLAM_MODEL_ID", "ubiops-deployment/bzk-dig-chat//chat-model")
        self.client = None
        self._session_key = None

        # Try to initialize with environment variable
        self._initialize_client()

    def _initialize_client(self, key: str | None = None) -> None:
        """Initialize the API client with the given key or the stored API key

        Args:
            key: Optional API key to use for initialization
        """
        # Use the provided key, or fall back to the stored one
        api_key = key or self.api_key

        if not api_key:
            self.client = None
            self._session_key = None
            return

        try:
            # Create an actual OpenAI client with the API key
            self.client = OpenAI(api_key=api_key, base_url=self.base_url)

            # If we're using a session key, store it
            if key and key != self.api_key:
                self._session_key = key
        except Exception:
            # Fail silently but keep client as None
            self.client = None
            self._session_key = None

    def set_session_key(self, request: Request, api_key: str) -> bool:
        """Set the API key for the current session

        Args:
            request: The FastAPI request object with session
            api_key: The API key to store in the session

        Returns:
            True if the API key was valid and set, False otherwise
        """
        # Test if the key is valid by initializing a client
        try:
            # This will throw an exception if the API key format is invalid,
            # but we don't actually make an API call here
            OpenAI(api_key=api_key, base_url=self.base_url)

            # Store in the session
            request.session[self.SESSION_KEY] = api_key

            # Also update current instance
            self._initialize_client(api_key)

            return True
        except Exception as e:
            # Invalid key
            print(f"Error setting VLAM API key: {e}")
            return False

    def get_api_key(self, request: Request | None = None) -> str | None:
        """Get the API key from session or environment

        Args:
            request: Optional request object with session

        Returns:
            API key if found, None otherwise
        """
        # First check session
        if request and self.SESSION_KEY in request.session:
            return request.session[self.SESSION_KEY]

        # Then check environment variable
        env_key = os.getenv(self.ENV_KEY)

        # For consistency, we won't set the session key if we're using env var
        return env_key

    def configure_for_request(self, request: Request) -> None:
        """Configure the service with the API key from the request session

        Args:
            request: The FastAPI request object with session
        """
        if request and self.SESSION_KEY in request.session:
            session_key = request.session[self.SESSION_KEY]
            if session_key != self._session_key:
                self._initialize_client(session_key)

    @property
    def provider_name(self) -> str:
        return "vlam"

    @property
    def model_id(self) -> str:
        return self._model_id

    def chat_completion(
        self,
        messages: list[dict[str, str]],
        max_tokens: int = 2000,
        temperature: float = 0.7,
        system: str | None = None,
        request: Request | None = None,
    ) -> Any | None:
        """Make a chat completion request to VLAM.ai using OpenAI-compatible API

        Args:
            messages: List of message objects with 'role' and 'content'
            max_tokens: Maximum number of tokens to generate
            temperature: Temperature for sampling
            system: System prompt
            request: Optional request object to get session key

        Returns:
            OpenAI API response or None if service not configured
        """
        # Configure client for this request if needed
        if request:
            self.configure_for_request(request)

        if not self.is_configured:
            return None

        try:
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
        except Exception as e:
            print(f"Error in VLAM chat completion: {e}")
            return None

    def get_completion_text(self, response: Any) -> str:
        """Extract the completion text from an OpenAI-compatible response

        Args:
            response: OpenAI API response

        Returns:
            Extracted text content
        """
        if response is None:
            return "Service not configured. Please set API key in the admin interface or as environment variable."

        try:
            return response.choices[0].message.content
        except Exception as e:
            print(f"Error extracting completion text from VLAM response: {e}")
            return "Er is een fout opgetreden bij het genereren van de uitleg. Probeer het later opnieuw of selecteer een andere LLM provider."

    def clear_session_key(self, request: Request) -> None:
        """Clear the API key from the session

        Args:
            request: The FastAPI request object with session
        """
        if self.SESSION_KEY in request.session:
            del request.session[self.SESSION_KEY]
            self._session_key = None
            # Reinitialize with environment variable
            self._initialize_client()


# Initialize as singleton if needed
vlam_service = VLAMService()
