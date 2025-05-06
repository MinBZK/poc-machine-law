import os

from fastapi import Request

from .base_llm_service import BaseLLMService
from .claude_service import claude_service
from .vlam_service import vlam_service


class LLMFactory:
    """Factory for creating LLM service instances based on configuration"""

    # Available LLM providers
    PROVIDER_CLAUDE = "claude"
    PROVIDER_VLAM = "vlam"

    # Provider mapping
    _provider_map = {PROVIDER_CLAUDE: claude_service, PROVIDER_VLAM: vlam_service}

    @staticmethod
    def get_available_providers() -> list[str]:
        """Get the list of available LLM providers

        Returns:
            List of provider names
        """
        return list(LLMFactory._provider_map.keys())

    @staticmethod
    def get_configured_providers(request: Request | None = None) -> list[str]:
        """Get the list of available AND configured LLM providers

        Args:
            request: Optional request object for checking session keys

        Returns:
            List of configured provider names
        """
        return [
            provider for provider in LLMFactory._provider_map if LLMFactory.is_provider_configured(provider, request)
        ]

    @staticmethod
    def get_provider(request: Request | None = None) -> str:
        """Get the currently configured LLM provider from environment

        Args:
            request: Optional request object for checking session keys

        Returns:
            Provider name (defaults to 'claude' if not specified)
        """
        requested_provider = os.getenv("LLM_PROVIDER", LLMFactory.PROVIDER_CLAUDE).lower()

        # Check if the requested provider is configured
        if LLMFactory.is_provider_configured(requested_provider, request):
            return requested_provider

        # If not, try to find any configured provider
        configured_providers = LLMFactory.get_configured_providers(request)
        if configured_providers:
            return configured_providers[0]

        # If no providers are configured, return the requested one anyway
        # (the service will handle the unconfigured state gracefully)
        return requested_provider

    @staticmethod
    def get_service(provider: str | None = None) -> BaseLLMService:
        """Get the appropriate LLM service based on provider name

        Args:
            provider: Optional provider name (defaults to configured provider)

        Returns:
            LLM service instance
        """
        provider = provider or LLMFactory.get_provider()

        if provider in LLMFactory._provider_map:
            return LLMFactory._provider_map[provider]
        else:
            # Default to Claude
            return claude_service

    @staticmethod
    def set_session_key(request: Request, provider: str, api_key: str) -> bool:
        """Set a temporary API key for a provider in the session

        Args:
            request: The FastAPI request object with session
            provider: The provider name
            api_key: The API key to set

        Returns:
            True if successful, False otherwise
        """
        try:
            if provider not in LLMFactory._provider_map:
                return False

            # Get the service and set the key in the session
            service = LLMFactory._provider_map[provider]
            success = service.set_session_key(request, api_key)

            return success
        except Exception as e:
            print(f"Error setting session key: {e}")
            return False

    @staticmethod
    def clear_session_key(request: Request, provider: str) -> bool:
        """Clear a temporary API key for a provider from the session

        Args:
            request: The FastAPI request object with session
            provider: The provider name

        Returns:
            True if successful, False otherwise
        """
        try:
            service = LLMFactory._provider_map.get(provider)
            if service:
                service.clear_session_key(request)
                return True
            return False
        except Exception:
            return False

    @staticmethod
    def is_provider_configured(provider: str, request: Request | None = None) -> bool:
        """Check if a specific provider is properly configured

        Args:
            provider: Provider to check
            request: Optional request object for checking session keys

        Returns:
            True if provider is configured, False otherwise
        """
        try:
            if provider in LLMFactory._provider_map:
                service = LLMFactory._provider_map[provider]

                # Check if there's a key in the session first
                if request:
                    session_key = service.get_api_key(request)
                    if session_key:
                        return True

                # Use the is_configured property as fallback
                if hasattr(service, "is_configured"):
                    return service.is_configured

                # Fall back to checking for client
                return hasattr(service, "client") and service.client is not None
            return False
        except Exception:
            return False


# Initialize factory as singleton
llm_factory = LLMFactory()
