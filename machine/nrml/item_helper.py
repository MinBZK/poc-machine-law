from datetime import datetime
from typing import Any


class NrmlItemHelper:
    """Static helper methods for accessing NRML item properties"""

    @staticmethod
    def get_active_version(item: dict[str, Any], calculation_date: str | None = None) -> dict[str, Any]:
        """Get the active version of an item based on calculation date"""
        versions = item.get("versions", [])
        if not versions:
            raise ValueError("No versions found in item")

        if len(versions) == 1:
            return versions[0]

        # Check if all versions have validFrom dates
        versions_with_dates = [v for v in versions if "validFrom" in v]
        if len(versions_with_dates) != len(versions):
            raise ValueError("Multiple versions found but not all have validFrom dates")

        # Parse calculation date or use current date
        calc_date = datetime.fromisoformat(calculation_date) if calculation_date else datetime.now()

        # Sort versions by validFrom date in descending order and find the first valid one
        sorted_versions = sorted(versions, key=lambda v: datetime.fromisoformat(v["validFrom"]), reverse=True)

        for version in sorted_versions:
            valid_from = datetime.fromisoformat(version["validFrom"])
            if valid_from <= calc_date:
                return version

        raise ValueError("No valid versions found for the calculation date")

    @staticmethod
    def get_item_description(item: dict[str, Any], language_key: str = "en") -> str | None:
        """Get the item description based on the language key"""
        name = item.get("name")
        if isinstance(name, dict) and language_key in name:
            return name[language_key]
        return None
