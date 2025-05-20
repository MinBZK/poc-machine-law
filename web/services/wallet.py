"""Wallet data service for the application.

This module provides mock wallet data for the NL Wallet integration.
"""

from typing import Any

WALLET_DATA = {
    # BSN: 100000001 - Merijn van der Meer
    "100000001": {
        "TOESLAGEN": {
            "wet_op_de_huurtoeslag": {
                "RENT_AMOUNT": 72000,  # €720.00 per maand (kale huurprijs)
                "SERVICE_COSTS": 5000,  # €50.00 per maand (servicekosten)
                "ELIGIBLE_SERVICE_COSTS": 4800,  # €48.00 per maand (subsidiabele servicekosten)
            }
        }
    },
}


def get_wallet_data(bsn: str, service: str | None = None, law: str | None = None) -> dict[str, Any]:
    """
    Get wallet data for a specific BSN, optionally filtered by service and law.

    Args:
        bsn: The BSN number to get data for
        service: Optional service filter (e.g., "TOESLAGEN")
        law: Optional law filter (e.g., "wet_op_de_huurtoeslag")

    Returns:
        Dictionary with wallet data for the specified BSN
    """
    if bsn not in WALLET_DATA:
        return {}

    data = WALLET_DATA[bsn].copy()

    if law and service:
        service_upper = service.upper()
        if service_upper in data and law in data[service_upper]:
            return {service_upper: {law: data[service_upper][law]}}

    return {}
