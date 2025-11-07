"""Integration tests for DataContext."""

import pytest
import pandas as pd

from machine.data_context import DataContext


class TestDataContext:
    """Test suite for DataContext functionality."""

    def test_data_context_creation(self, data_context: DataContext):
        """Test that DataContext can be created."""
        assert data_context is not None
        assert isinstance(data_context.sources, dict)
        assert isinstance(data_context.claims, dict)
        assert isinstance(data_context.accessed_sources, set)

    def test_add_and_retrieve_source(self, data_context: DataContext):
        """Test adding and retrieving a data source."""
        # Create test data
        df_test = pd.DataFrame([
            {"id": "1", "name": "Alice"},
            {"id": "2", "name": "Bob"}
        ])

        # Add source
        data_context.add_source("test_service", "test_table", df_test)

        # Retrieve source
        retrieved = data_context.get_source("test_service", "test_table")

        assert retrieved is not None
        assert len(retrieved) == 2
        assert retrieved.iloc[0]["name"] == "Alice"
        assert retrieved.iloc[1]["name"] == "Bob"

    def test_access_tracking(self, data_context: DataContext):
        """Test that data access is tracked."""
        df_test = pd.DataFrame([{"id": "1"}])
        data_context.add_source("service1", "table1", df_test)

        # Access count should be 0 initially
        assert len(data_context.accessed_sources) == 0

        # Access the source
        data_context.get_source("service1", "table1")

        # Access should be tracked
        assert ("service1", "table1") in data_context.accessed_sources
        assert len(data_context.accessed_sources) == 1

    def test_nonexistent_source(self, data_context: DataContext):
        """Test retrieving a non-existent source returns None."""
        result = data_context.get_source("nonexistent", "table")
        assert result is None

    def test_merge_sources(self, data_context: DataContext):
        """Test merging data into existing source."""
        # Add initial data
        df1 = pd.DataFrame([{"id": "1", "value": "A"}])
        data_context.add_source("service", "table", df1)

        # Add more data
        df2 = pd.DataFrame([{"id": "2", "value": "B"}])

        # Get existing and concatenate (simulating merge)
        existing = data_context.get_source("service", "table")
        merged = pd.concat([existing, df2], ignore_index=True)
        data_context.add_source("service", "table", merged)

        # Verify merged data
        result = data_context.get_source("service", "table")
        assert len(result) == 2
        assert result.iloc[0]["id"] == "1"
        assert result.iloc[1]["id"] == "2"

    def test_has_source(self, data_context: DataContext):
        """Test checking if source exists."""
        df_test = pd.DataFrame([{"id": "1"}])
        data_context.add_source("service", "table", df_test)

        assert data_context.has_source("service", "table")
        assert not data_context.has_source("service", "nonexistent")
        assert not data_context.has_source("nonexistent", "table")

    def test_multiple_services(self, data_context: DataContext):
        """Test managing data from multiple services."""
        df_svb = pd.DataFrame([{"bsn": "123"}])
        df_toeslagen = pd.DataFrame([{"bsn": "456"}])
        df_belastingdienst = pd.DataFrame([{"bsn": "789"}])

        data_context.add_source("SVB", "personen", df_svb)
        data_context.add_source("TOESLAGEN", "personen", df_toeslagen)
        data_context.add_source("BELASTINGDIENST", "personen", df_belastingdienst)

        # All sources should be independently accessible
        assert data_context.get_source("SVB", "personen").iloc[0]["bsn"] == "123"
        assert data_context.get_source("TOESLAGEN", "personen").iloc[0]["bsn"] == "456"
        assert data_context.get_source("BELASTINGDIENST", "personen").iloc[0]["bsn"] == "789"
