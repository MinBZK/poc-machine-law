"""
Utility functions for MCP law execution server.
"""

import logging
from datetime import datetime
from typing import Any


def setup_logging(level: str = "INFO") -> None:
    """Setup logging configuration"""
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )


def format_currency(amount: float, currency: str = "EUR") -> str:
    """Format amount as currency"""
    if currency == "EUR":
        return f"€{amount:,.2f}"
    return f"{amount:,.2f} {currency}"


def format_date(date_str: str) -> str:
    """Format date string for display"""
    try:
        date_obj = datetime.strptime(date_str, "%Y-%m-%d")
        return date_obj.strftime("%d %B %Y")
    except (ValueError, TypeError):
        return date_str


def extract_financial_impact(output: dict[str, Any], spec: dict[str, Any]) -> float:
    """Extract financial impact from law execution output"""
    impact_value = 0.0

    if not output or not spec:
        return impact_value

    # Get output definitions
    output_definitions = {}
    for output_def in spec.get("properties", {}).get("output", []):
        output_name = output_def.get("name")
        if output_name:
            output_definitions[output_name] = output_def

    # Process outputs according to their relevance
    for output_name, output_data in output.items():
        output_def = output_definitions.get(output_name)

        # Skip if no definition found or not marked as primary
        if not output_def or output_def.get("citizen_relevance") != "primary":
            continue

        try:
            output_type = output_def.get("type", "")

            # Handle numeric types (amount, number)
            if output_type in ["amount", "number"]:
                numeric_value = float(output_data)

                # Normalize to yearly values based on temporal definition
                temporal = output_def.get("temporal", {})
                if temporal.get("type") == "period" and temporal.get("period_type") == "month":
                    numeric_value *= 12

                impact_value += abs(numeric_value)

            # Handle boolean types with standard importance for eligibility
            elif output_type == "boolean" and output_data is True:
                impact_value = max(impact_value, 50000)  # Assign importance to eligibility

        except (ValueError, TypeError):
            continue

    return impact_value


def validate_bsn(bsn: str) -> bool:
    """Validate Dutch BSN (Burgerservicenummer)"""
    if not bsn or not bsn.isdigit() or len(bsn) != 9:
        return False

    # BSN validation using the 11-test
    weights = [9, 8, 7, 6, 5, 4, 3, 2, -1]
    total = sum(int(digit) * weight for digit, weight in zip(bsn, weights))

    return total % 11 == 0


def sanitize_input(data: dict[str, Any], max_length: int = 1000) -> dict[str, Any]:
    """Sanitize input data for security with comprehensive protection"""
    import html
    import re

    sanitized = {}

    # Dangerous keys that should be excluded
    dangerous_keys = {
        "password",
        "secret",
        "token",
        "key",
        "auth",
        "credential",
        "session",
        "cookie",
        "jwt",
        "oauth",
        "api_key",
    }

    for key, value in data.items():
        # Remove potential dangerous keys (case-insensitive)
        if (
            key.startswith("_")
            or key.lower() in dangerous_keys
            or any(danger in key.lower() for danger in dangerous_keys)
        ):
            continue

        # Sanitize string values
        if isinstance(value, str):
            # HTML escape for XSS prevention
            value = html.escape(value, quote=True)

            # Remove potentially dangerous patterns
            # Remove script tags and event handlers
            value = re.sub(r"<script[^>]*>.*?</script>", "", value, flags=re.IGNORECASE | re.DOTALL)
            value = re.sub(r"on\w+\s*=", "", value, flags=re.IGNORECASE)
            value = re.sub(r"javascript:", "", value, flags=re.IGNORECASE)

            # Remove null bytes and control characters
            value = re.sub(r"[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]", "", value)

            # Limit length
            value = value[:max_length]

            # Trim whitespace
            value = value.strip()

        # Recursively sanitize nested dictionaries
        elif isinstance(value, dict):
            value = sanitize_input(value, max_length)

        # Sanitize lists
        elif isinstance(value, list):
            value = [
                sanitize_input({"item": item}, max_length).get("item", item) if isinstance(item, str | dict) else item
                for item in value
            ]

        sanitized[key] = value

    return sanitized


def get_current_date() -> str:
    """Get current date in YYYY-MM-DD format"""
    return datetime.now().strftime("%Y-%m-%d")
