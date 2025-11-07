"""
DataContext - Manages all data sources for law evaluation.

This class provides a unified interface to access data from various sources
(dataframes, claims, etc.) without needing to know about service routing.
"""

import logging
from typing import Any

import pandas as pd

from machine.events.claim.aggregate import Claim

logger = logging.getLogger(__name__)


class DataContext:
    """
    Context for managing all data sources during law evaluation.

    Data is organized by source name and table name. For example:
    - sources["toeslagen"]["personen"] = DataFrame of person data from Toeslagen
    - sources["brp"]["inschrijvingen"] = DataFrame of BRP registrations
    - sources["bag"]["verblijfsobjecten"] = DataFrame of BAG objects

    This allows laws to reference data without needing to know which
    organizational service provides it.
    """

    def __init__(self) -> None:
        """Initialize an empty DataContext."""
        # Sources organized as: sources[source_name][table_name] = DataFrame
        self.sources: dict[str, dict[str, pd.DataFrame]] = {}

        # Claims from event sourcing
        self.claims: dict[str, Claim] = {}

        # Track which data sources have been accessed (for auditing/tracing)
        self.accessed_sources: set[tuple[str, str]] = set()

    def add_source(self, source_name: str, table_name: str, dataframe: pd.DataFrame) -> None:
        """
        Add a data source to the context.

        Args:
            source_name: Name of the data source (e.g., "toeslagen", "brp", "belastingdienst")
            table_name: Name of the table within the source (e.g., "personen", "adressen")
            dataframe: The data as a pandas DataFrame
        """
        if source_name not in self.sources:
            self.sources[source_name] = {}

        self.sources[source_name][table_name] = dataframe
        logger.debug(f"Added data source: {source_name}.{table_name} with {len(dataframe)} rows")

    def get_source(self, source_name: str, table_name: str) -> pd.DataFrame | None:
        """
        Get a data source from the context.

        Args:
            source_name: Name of the data source
            table_name: Name of the table within the source

        Returns:
            DataFrame if found, None otherwise
        """
        # Track access
        self.accessed_sources.add((source_name, table_name))

        if source_name not in self.sources:
            logger.warning(f"Data source '{source_name}' not found in context")
            return None

        if table_name not in self.sources[source_name]:
            logger.warning(f"Table '{table_name}' not found in source '{source_name}'")
            return None

        return self.sources[source_name][table_name]

    def has_source(self, source_name: str, table_name: str) -> bool:
        """
        Check if a data source exists in the context.

        Args:
            source_name: Name of the data source
            table_name: Name of the table within the source

        Returns:
            True if the source exists, False otherwise
        """
        return source_name in self.sources and table_name in self.sources[source_name]

    def add_claim(self, claim_id: str, claim: Claim) -> None:
        """
        Add a claim to the context.

        Args:
            claim_id: Unique identifier for the claim
            claim: The claim object
        """
        self.claims[claim_id] = claim
        logger.debug(f"Added claim: {claim_id}")

    def get_claim(self, claim_id: str) -> Claim | None:
        """
        Get a claim from the context.

        Args:
            claim_id: Unique identifier for the claim

        Returns:
            Claim if found, None otherwise
        """
        return self.claims.get(claim_id)

    def merge_sources(self, other: "DataContext") -> None:
        """
        Merge data sources from another DataContext into this one.

        Args:
            other: Another DataContext to merge from
        """
        for source_name, tables in other.sources.items():
            for table_name, df in tables.items():
                if source_name in self.sources and table_name in self.sources[source_name]:
                    # Concatenate dataframes if both exist
                    existing_df = self.sources[source_name][table_name]
                    self.sources[source_name][table_name] = pd.concat(
                        [existing_df, df], ignore_index=True
                    )
                    logger.debug(
                        f"Merged data source: {source_name}.{table_name} "
                        f"(now {len(self.sources[source_name][table_name])} rows)"
                    )
                else:
                    # Add new source
                    self.add_source(source_name, table_name, df)

        # Merge claims
        self.claims.update(other.claims)

    def list_sources(self) -> list[tuple[str, str, int]]:
        """
        List all available data sources.

        Returns:
            List of tuples (source_name, table_name, row_count)
        """
        result = []
        for source_name, tables in self.sources.items():
            for table_name, df in tables.items():
                result.append((source_name, table_name, len(df)))
        return sorted(result)

    def get_accessed_sources(self) -> list[tuple[str, str]]:
        """
        Get list of data sources that have been accessed.

        Returns:
            List of tuples (source_name, table_name)
        """
        return sorted(list(self.accessed_sources))

    def clear_access_tracking(self) -> None:
        """Clear the access tracking."""
        self.accessed_sources.clear()

    def __repr__(self) -> str:
        """String representation of the DataContext."""
        source_count = sum(len(tables) for tables in self.sources.values())
        claim_count = len(self.claims)
        return f"DataContext(sources={source_count}, claims={claim_count})"
