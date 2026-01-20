from pathlib import Path

from machine import utils
from machine.service import RuleService


class TestRuleServiceIntegration:
    """Integration tests for RuleService using NRML law specifications"""

    def test_evaluate_simple_law(self, monkeypatch):
        """Test that RuleService.evaluate() can load and evaluate a simple NRML law"""
        # Point NRML_BASE_DIR to test fixtures directory
        fixtures_dir = Path(__file__).parent / "fixtures"
        monkeypatch.setattr("machine.utils.NRML_BASE_DIR", str(fixtures_dir))

        # Clear the file cache to ensure clean state
        utils._file_cache.clear()

        # Create a minimal services mock - RuleService just needs it as a reference
        class MockServices:
            pass

        services = MockServices()

        # Create RuleService for NRML service
        service = RuleService(service_name="NRML", services=services)

        # Evaluate the kinderbijslag_maximum_leeftijd law
        result = service.evaluate(
            law="kinderbijslag_maximum_leeftijd",
            reference_date="2020-01-01",
            parameters={},
            requested_output="maximum_leeftijd",
        )

        # Verify result structure
        assert result is not None
        assert result.output is not None
        assert "maximum_leeftijd" in result.output

        # Verify the value is correct
        assert result.output["maximum_leeftijd"] == 10

    def test_evaluate_law_with_include(self, monkeypatch):
        """Test that RuleService.evaluate() can load and evaluate a law that includes another law"""
        # Point NRML_BASE_DIR to test fixtures directory
        fixtures_dir = Path(__file__).parent / "fixtures"
        monkeypatch.setattr("machine.utils.NRML_BASE_DIR", str(fixtures_dir))

        # Clear file cache to ensure clean state
        utils._file_cache.clear()

        # Create a minimal services mock with NRML service
        class MockServices:
            pass

        services = MockServices()

        # Create RuleService for NRML service
        service = RuleService(service_name="NRML", services=services)

        # Add the service to services.NRML so includes can reference it
        services.NRML = service

        # Evaluate the kinderbijslag_aantal_kinderen law which includes kinderbijslag_maximum_leeftijd
        children_data = [{"age": 8}, {"age": 9}, {"age": 15}]
        aanvrager_data = [{}]

        result = service.evaluate(
            law="kinderbijslag_aantal_kinderen",
            reference_date="2020-01-01",
            parameters={"kinderen": children_data, "aanvrager": aanvrager_data},
            requested_output="young_children_count",
        )

        # Verify result structure
        assert result is not None
        assert result.output is not None
        assert "young_children_count" in result.output

        # Verify the count is correct - should count 2 children with age <= 10
        # The max age of 10 comes from the included kinderbijslag_maximum_leeftijd law
        assert result.output["young_children_count"] == 2
