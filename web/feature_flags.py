"""Feature flags service for the application.

This module provides a simple way to manage feature flags using environment variables.
All feature flags are prefixed with "FEATURE_" to namespace them.
"""

import os


class FeatureFlags:
    """Service for managing feature flags."""

    # Prefix for all feature flag environment variables
    PREFIX = "FEATURE_"

    # Default values for feature flags
    DEFAULTS = {
        "WALLET": False,  # Wallet feature is disabled by default
        "CHAT": True,  # Chat feature is enabled by default
    }

    @classmethod
    def get_all(cls) -> dict[str, bool]:
        """Get all feature flags with their current values."""
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
