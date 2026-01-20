from datetime import datetime
from unittest.mock import patch

import pytest

from machine.nrml.item_helper import NrmlItemHelper


class TestNrmlItemHelper:
    """Test cases for NrmlItemHelper"""

    # Tests for get_active_version

    def test_get_active_version_single_version(self):
        """Test getting active version when only one version exists"""
        item = {"versions": [{"type": "Text", "description": {"nl": "Single version"}}]}

        result = NrmlItemHelper.get_active_version(item)

        assert result == item["versions"][0]
        assert result["type"] == "Text"

    def test_get_active_version_no_versions(self):
        """Test error when item has no versions"""
        item = {"versions": []}

        with pytest.raises(ValueError, match="No versions found in item"):
            NrmlItemHelper.get_active_version(item)

    def test_get_active_version_missing_versions_key(self):
        """Test error when item has no versions key"""
        item = {"name": "test"}

        with pytest.raises(ValueError, match="No versions found in item"):
            NrmlItemHelper.get_active_version(item)

    def test_get_active_version_multiple_versions_with_dates(self):
        """Test getting active version with multiple versions and calculation date"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01", "type": "Text", "value": "v1"},
                {"validFrom": "2022-01-01", "type": "Text", "value": "v2"},
                {"validFrom": "2024-01-01", "type": "Text", "value": "v3"},
            ]
        }

        # Test with date that should match v2
        result = NrmlItemHelper.get_active_version(item, "2023-06-15")
        assert result["value"] == "v2"
        assert result["validFrom"] == "2022-01-01"

    def test_get_active_version_exact_date_match(self):
        """Test getting active version when calculation date exactly matches validFrom"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01", "type": "Text", "value": "v1"},
                {"validFrom": "2022-01-01", "type": "Text", "value": "v2"},
            ]
        }

        result = NrmlItemHelper.get_active_version(item, "2022-01-01")
        assert result["value"] == "v2"

    def test_get_active_version_before_all_dates(self):
        """Test error when calculation date is before all validFrom dates"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01", "type": "Text", "value": "v1"},
                {"validFrom": "2022-01-01", "type": "Text", "value": "v2"},
            ]
        }

        with pytest.raises(ValueError, match="No valid versions found for the calculation date"):
            NrmlItemHelper.get_active_version(item, "2019-01-01")

    def test_get_active_version_latest_version(self):
        """Test getting active version with recent date returns latest version"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01", "type": "Text", "value": "v1"},
                {"validFrom": "2022-01-01", "type": "Text", "value": "v2"},
                {"validFrom": "2024-01-01", "type": "Text", "value": "v3"},
            ]
        }

        result = NrmlItemHelper.get_active_version(item, "2025-01-01")
        assert result["value"] == "v3"

    def test_get_active_version_unsorted_versions(self):
        """Test that versions are correctly sorted even if provided unsorted"""
        item = {
            "versions": [
                {"validFrom": "2024-01-01", "type": "Text", "value": "v3"},
                {"validFrom": "2020-01-01", "type": "Text", "value": "v1"},
                {"validFrom": "2022-01-01", "type": "Text", "value": "v2"},
            ]
        }

        result = NrmlItemHelper.get_active_version(item, "2023-06-15")
        assert result["value"] == "v2"

    def test_get_active_version_no_calculation_date_provided(self):
        """Test getting active version without providing calculation date uses current date"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01", "type": "Text", "value": "v1"},
                {"validFrom": "2022-01-01", "type": "Text", "value": "v2"},
            ]
        }

        # Mock datetime.now() to return a known date
        with patch("machine.nrml.item_helper.datetime") as mock_datetime:
            mock_datetime.now.return_value = datetime(2023, 6, 15)
            mock_datetime.fromisoformat = datetime.fromisoformat

            result = NrmlItemHelper.get_active_version(item, None)
            assert result["value"] == "v2"

    def test_get_active_version_multiple_versions_missing_some_dates(self):
        """Test error when multiple versions exist but not all have validFrom dates"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01", "type": "Text", "value": "v1"},
                {"type": "Text", "value": "v2"},  # Missing validFrom
            ]
        }

        with pytest.raises(ValueError, match="Multiple versions found but not all have validFrom dates"):
            NrmlItemHelper.get_active_version(item, "2023-01-01")

    def test_get_active_version_with_time_component(self):
        """Test getting active version with ISO format including time"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01T00:00:00", "type": "Text", "value": "v1"},
                {"validFrom": "2022-06-15T12:30:00", "type": "Text", "value": "v2"},
            ]
        }

        result = NrmlItemHelper.get_active_version(item, "2022-06-15T15:00:00")
        assert result["value"] == "v2"

    # Tests for get_item_description

    def test_get_item_description_with_language_dict(self):
        """Test getting item description with multilingual name dictionary"""
        item = {"name": {"en": "English description", "nl": "Nederlandse beschrijving", "de": "Deutsche Beschreibung"}}

        result = NrmlItemHelper.get_item_description(item, "nl")
        assert result == "Nederlandse beschrijving"

    def test_get_item_description_default_language(self):
        """Test getting item description with default language (en)"""
        item = {"name": {"en": "English description", "nl": "Nederlandse beschrijving"}}

        result = NrmlItemHelper.get_item_description(item, "en")
        assert result == "English description"

    def test_get_item_description_language_not_found(self):
        """Test getting item description when requested language is not available"""
        item = {"name": {"en": "English description", "nl": "Nederlandse beschrijving"}}

        result = NrmlItemHelper.get_item_description(item, "fr")
        assert result is None

    def test_get_item_description_name_is_string(self):
        """Test getting item description when name is a string instead of dict"""
        item = {"name": "Simple string name"}

        result = NrmlItemHelper.get_item_description(item, "en")
        assert result is None

    def test_get_item_description_name_missing(self):
        """Test getting item description when name key is missing"""
        item = {"type": "Text"}

        result = NrmlItemHelper.get_item_description(item, "en")
        assert result is None

    def test_get_item_description_empty_name_dict(self):
        """Test getting item description with empty name dictionary"""
        item = {"name": {}}

        result = NrmlItemHelper.get_item_description(item, "en")
        assert result is None

    def test_get_item_description_name_is_none(self):
        """Test getting item description when name is None"""
        item = {"name": None}

        result = NrmlItemHelper.get_item_description(item, "en")
        assert result is None

    def test_get_item_description_case_sensitive_language_key(self):
        """Test that language key lookup is case-sensitive"""
        item = {"name": {"en": "English", "EN": "ENGLISH UPPERCASE"}}

        result_lower = NrmlItemHelper.get_item_description(item, "en")
        result_upper = NrmlItemHelper.get_item_description(item, "EN")

        assert result_lower == "English"
        assert result_upper == "ENGLISH UPPERCASE"

    def test_helper_methods_are_static(self):
        """Test that helper methods can be called without instantiation"""
        item = {"versions": [{"type": "Text"}]}

        # Should not raise an error - can call without creating instance
        result = NrmlItemHelper.get_active_version(item)
        assert result is not None

    def test_get_active_version_with_timezone_aware_dates(self):
        """Test getting active version with timezone-aware ISO dates"""
        item = {
            "versions": [
                {"validFrom": "2020-01-01T00:00:00+00:00", "type": "Text", "value": "v1"},
                {"validFrom": "2022-01-01T00:00:00+00:00", "type": "Text", "value": "v2"},
            ]
        }

        result = NrmlItemHelper.get_active_version(item, "2023-01-01T00:00:00+00:00")
        assert result["value"] == "v2"
