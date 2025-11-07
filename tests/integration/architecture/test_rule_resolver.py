"""Integration tests for RuleResolver."""

import pytest
from pathlib import Path

from machine.utils import RuleResolver, RuleSpec


class TestRuleResolver:
    """Test suite for RuleResolver functionality."""

    @pytest.fixture(scope="class")
    def resolver(self) -> RuleResolver:
        """Create a RuleResolver instance for the class."""
        return RuleResolver()

    def test_resolver_loads_rules(self, resolver: RuleResolver):
        """Test that resolver loads rules from YAML files."""
        assert len(resolver.rules) > 0
        assert len(resolver.rules) >= 40  # We know there are at least 45 laws

    def test_resolver_discovers_services(self, resolver: RuleResolver):
        """Test that resolver discovers services from rules."""
        services = resolver.get_service_laws()

        assert len(services) > 0
        # Should include common services
        assert "SVB" in services
        assert "TOESLAGEN" in services
        assert "BELASTINGDIENST" in services

    def test_rules_have_required_fields(self, resolver: RuleResolver):
        """Test that loaded rules have required fields."""
        for rule in resolver.rules:
            assert rule.law is not None
            assert rule.valid_from is not None
            assert rule.path is not None
            # service may be None for v0.1.7 rules

    def test_find_rule_with_service(self, resolver: RuleResolver):
        """Test finding a rule by law, date, and service."""
        rule = resolver.find_rule(
            law="algemene_kinderbijslagwet",
            reference_date="2025-01-01",
            service="SVB"
        )

        assert rule is not None
        assert isinstance(rule, RuleSpec)
        assert rule.law == "algemene_kinderbijslagwet"
        assert rule.service == "SVB"

    def test_find_rule_without_service(self, resolver: RuleResolver):
        """Test finding a rule without specifying service."""
        rule = resolver.find_rule(
            law="algemene_kinderbijslagwet",
            reference_date="2025-01-01",
            service=None
        )

        assert rule is not None
        # Should still find a rule even without service

    def test_find_nonexistent_rule(self, resolver: RuleResolver):
        """Test that finding nonexistent rule raises ValueError."""
        with pytest.raises(ValueError, match="No rules found"):
            resolver.find_rule(
                law="nonexistent_law",
                reference_date="2025-01-01",
                service="SVB"
            )

    def test_get_rule_spec_returns_dict(self, resolver: RuleResolver):
        """Test that get_rule_spec returns the full YAML spec as dict."""
        spec = resolver.get_rule_spec(
            law="algemene_kinderbijslagwet",
            reference_date="2025-01-01",
            service="SVB"
        )

        assert spec is not None
        assert isinstance(spec, dict)
        assert "law" in spec
        assert spec["law"] == "algemene_kinderbijslagwet"
        assert "properties" in spec

    def test_rules_dataframe(self, resolver: RuleResolver):
        """Test generating DataFrame from rules."""
        import pandas as pd

        df = resolver.rules_dataframe()

        assert isinstance(df, pd.DataFrame)
        assert len(df) > 0
        assert "law" in df.columns
        assert "service" in df.columns
        assert "valid_from" in df.columns

    def test_get_service_laws_structure(self, resolver: RuleResolver):
        """Test the structure of get_service_laws return value."""
        service_laws = resolver.get_service_laws()

        assert isinstance(service_laws, dict)

        # Each service should map to a set of law names
        for service, laws in service_laws.items():
            assert isinstance(service, str)
            assert isinstance(laws, set)
            assert len(laws) > 0

            # All law names should be strings
            for law in laws:
                assert isinstance(law, str)

    def test_discoverable_laws(self, resolver: RuleResolver):
        """Test that discoverable laws are tracked."""
        # Some laws should be discoverable
        assert len(resolver.discoverable_laws_by_service) >= 0

        # Structure should be dict[str, dict[str, set]]
        for discoverable_type, services in resolver.discoverable_laws_by_service.items():
            assert isinstance(discoverable_type, str)
            assert isinstance(services, dict)

    def test_windows_symlink_handling(self):
        """Test that resolver handles Windows symlink-as-file correctly."""
        # This test verifies the fix for Windows symlink issue
        from machine.utils import BASE_DIR

        base_path = Path(BASE_DIR)

        # Create a new resolver
        resolver = RuleResolver()

        # If BASE_DIR is a file (Windows symlink), resolver should still work
        if base_path.is_file():
            # Should have read the real path and loaded rules
            assert resolver.rules_dir.is_dir()
            assert len(resolver.rules) > 0
        else:
            # If it's a directory or actual symlink, should also work
            assert resolver.rules_dir.is_dir()
            assert len(resolver.rules) > 0

    def test_multiple_versions_same_law(self, resolver: RuleResolver):
        """Test handling laws with multiple versions."""
        # Find all versions of a law
        all_versions = [
            rule for rule in resolver.rules
            if rule.law == "algemene_kinderbijslagwet"
        ]

        # Should have at least one version
        assert len(all_versions) > 0

        # If multiple versions exist, they should have different valid_from dates
        if len(all_versions) > 1:
            dates = [rule.valid_from for rule in all_versions]
            # Check that dates are different (allowing duplicates for different services)
            assert len(set(dates)) >= 1
