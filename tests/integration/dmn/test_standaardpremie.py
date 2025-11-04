"""
Tests for standaardpremie_2025.dmn

Tests the simplest DMN file - a literal constant value.
"""
import pytest
from pathlib import Path


class TestStandaardpremie:
    """Test suite for Standaardpremie 2025 DMN."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(dmn_dir / "standaardpremie_2025.dmn")
        self.decision_id = "decision_standaardpremie"

    def test_dmn_loads_successfully(self):
        """Test that the DMN file loads and parses correctly."""
        assert self.dmn_spec is not None
        assert self.dmn_spec.name == "Standaardpremie 2025 (VWS)"
        assert self.dmn_spec.id == "standaardpremie_2025"
        assert "decision_standaardpremie" in self.dmn_spec.decisions

    def test_standaardpremie_value(self):
        """Test that the standard premium constant is correct."""
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {})

        assert result.requirements_met is True
        assert "standaardpremie" in result.output
        assert result.output["standaardpremie"] == 211200  # €2,112

    def test_standaardpremie_no_errors(self):
        """Test that evaluation produces no errors."""
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {})

        assert len(result.errors) == 0
        assert result.missing_required is False

    def test_standaardpremie_with_parameters(self):
        """Test that extra parameters don't affect the constant result."""
        # Standard premium should be constant regardless of inputs
        parameters = {
            'person': {'birth_date': '1990-01-01'},
            'extra_param': 'ignored'
        }

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["standaardpremie"] == 211200

    def test_execution_trace_exists(self):
        """Test that execution trace (PathNode) is generated."""
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {})

        assert result.path is not None
        assert result.path.type == "dmn_evaluation"
        assert result.path.name == "Standaardpremie 2025"
        assert len(result.path.children) > 0  # Should have decision node

    def test_dmn_spec_metadata(self):
        """Test that DMN metadata is correctly parsed."""
        assert self.dmn_spec.namespace == "https://regels.overheid.nl/standaardpremie/VWS-2025-01-01"
        assert self.dmn_spec.exporter == "Claude Code"

    def test_decision_structure(self):
        """Test that the decision structure is correct."""
        decision = self.dmn_spec.decisions[self.decision_id]

        assert decision.name == "Standaardpremie 2025"
        assert decision.variable_name == "standaardpremie"
        assert decision.expression is not None
        assert decision.expression.text == "211200"
