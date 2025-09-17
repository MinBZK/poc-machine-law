"""
Mock data for testing the MCP server functionality.
In production, this would be replaced with real data sources.
"""

from typing import Any


def get_mock_profile_data(bsn: str) -> dict[str, Any]:
    """
    Get mock profile data for a BSN.

    In production, this would connect to:
    - RvIG/BRP (Dutch citizen registry)
    - Municipal records
    - Tax administration data
    """
    return {
        "bsn": bsn,
        "geboortedatum": "1990-01-01",
        "postcode": "1234AB",
        "woonplaats": "Amsterdam",
        "huishouding": "ALLEENSTAANDE",
        "inkomen": 25000,
        "verzekerd": True,
        "nationaliteit": "Nederlandse",
    }


# Additional mock data that could be expanded
MOCK_INSURANCE_POLICIES = {
    "123456782": {"verzekeraar": "Zilveren Kruis", "polisnummer": "123456789", "eigen_risico": 385}
}

MOCK_HOUSING_DATA = {"123456782": {"huurprijs": 750, "woningwaardering": 142, "huurgrens": 808.06}}
