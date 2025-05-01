import os

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
    def get_provider() -> str:
        """Get the currently configured LLM provider from environment

        Returns:
            Provider name (defaults to 'claude' if not specified)
        """
        return os.getenv("LLM_PROVIDER", LLMFactory.PROVIDER_CLAUDE).lower()

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
    def is_provider_configured(provider: str) -> bool:
        """Check if a specific provider is properly configured

        Args:
            provider: Provider to check

        Returns:
            True if provider is configured, False otherwise
        """
        try:
            if provider in LLMFactory._provider_map:
                # Try to access the provider to check if it's configured
                service = LLMFactory._provider_map[provider]
                # If the service has a client, it's configured
                return hasattr(service, "client") and service.client is not None
            return False
        except Exception:
            return False


# Initialize factory as singleton
llm_factory = LLMFactory()
