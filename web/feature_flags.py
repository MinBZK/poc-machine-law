"""Feature flags service for the application.

This module provides a simple way to manage feature flags using environment variables.
All feature flags are prefixed with "FEATURE_" to namespace them.
"""

import os


class FeatureFlags:
    """Service for managing feature flags."""

    # Prefix for all feature flag environment variables
    PREFIX = "FEATURE_"

    # Prefix for law-specific feature flags
    LAW_PREFIX = "LAW_"

    # Default values for feature flags
    DEFAULTS = {
        "WALLET": False,  # Wallet feature is disabled by default
        "CHAT": True,  # Chat feature is enabled by default
        "CHANGE_WIZARD": False,  # Change wizard is disabled by default
        "TOTAL_INCOME_WIDGET": False,  # Total income dashboard widget is disabled by default
    }

    @classmethod
    def get_all(cls) -> dict[str, bool]:
        """Get all feature flags with their current values (excluding law flags)."""
        flags = {}

        # Start with defaults
        for key, default_value in cls.DEFAULTS.items():
            flag_key = f"{cls.PREFIX}{key}"
            # Check if flag is set in environment
            env_value = os.environ.get(flag_key)

            if env_value is not None:
                # Convert string to boolean
                flags[key] = env_value.lower() in ("1", "true", "yes", "y")
            else:
                # Use default value
                flags[key] = default_value

        # Look for any dynamically set feature flags (excluding law flags)
        for key, value in os.environ.items():
            # Only include keys that start with PREFIX but not LAW_PREFIX
            if key.startswith(cls.PREFIX) and not key.startswith(f"{cls.PREFIX}{cls.LAW_PREFIX}"):
                # Extract the flag name from the key
                flag_name = key[len(cls.PREFIX) :]
                # Don't overwrite defaults that were already processed
                if flag_name not in flags and flag_name not in cls.DEFAULTS:
                    # Convert value to boolean
                    flags[flag_name] = value.lower() in ("1", "true", "yes", "y")

        return flags

    @classmethod
    def get_law_flags(cls, service_laws: dict[str, list[str]]) -> dict[str, dict[str, bool]]:
        """
        Get all law-specific feature flags with their current values.

        Args:
            service_laws: Dictionary mapping service names to lists of law names

        Returns:
            Dictionary with service names as keys and dictionaries of law names to boolean values as values
        """
        flags = {}

        # Initialize with all laws enabled by default
        for service, laws in service_laws.items():
            flags[service] = {}
            for law in laws:
                # Use is_law_enabled which defaults to True if not set
                flags[service][law] = cls.is_law_enabled(service, law)

        return flags

    @classmethod
    def is_enabled(cls, flag_name: str) -> bool:
        """Check if a feature flag is enabled."""
        flag_name = flag_name.upper()
        flag_key = f"{cls.PREFIX}{flag_name}"

        # Check if flag is set in environment
        env_value = os.environ.get(flag_key)

        if env_value is not None:
            return env_value.lower() in ("1", "true", "yes", "y")

        # Return default value if available
        if flag_name in cls.DEFAULTS:
            return cls.DEFAULTS[flag_name]

        # Default to False if not defined
        return False

    @classmethod
    def is_law_enabled(cls, service: str, law: str) -> bool:
        """
        Check if a specific law is enabled.

        Args:
            service: Service name (e.g., "TOESLAGEN")
            law: Law name (e.g., "zorgtoeslagwet" or "participatiewet/bijstand")

        Returns:
            Boolean indicating if the law is enabled (default is True if not set)
        """
        # Sanitize law name for environment variable
        # Replace slashes with double underscores for safe environment variable names
        sanitized_law = law.replace("/", "__")

        flag_name = f"{cls.LAW_PREFIX}{service}_{sanitized_law}".upper()
        flag_key = f"{cls.PREFIX}{flag_name}"

        # Check if flag is set in environment
        env_value = os.environ.get(flag_key)

        # Default to True (enabled) if not set
        if env_value is None:
            return True

        # Otherwise, convert the value to boolean
        return env_value.lower() in ("1", "true", "yes", "y")

    @classmethod
    def set(cls, flag_name: str, value: bool) -> None:
        """Set the value of a feature flag."""
        flag_name = flag_name.upper()
        flag_key = f"{cls.PREFIX}{flag_name}"

        # Convert boolean to string and set in environment
        os.environ[flag_key] = "1" if value else "0"


# Convenience functions for checking flags
def is_wallet_enabled() -> bool:
    """Check if the wallet feature is enabled."""
    return FeatureFlags.is_enabled("WALLET")


def is_chat_enabled() -> bool:
    """Check if the chat feature is enabled."""
    return FeatureFlags.is_enabled("CHAT")


def is_change_wizard_enabled() -> bool:
    """Check if the change wizard feature is enabled."""
    return FeatureFlags.is_enabled("CHANGE_WIZARD")


def is_total_income_widget_enabled() -> bool:
    """Check if the total income widget is enabled."""
    return FeatureFlags.is_enabled("TOTAL_INCOME_WIDGET")
