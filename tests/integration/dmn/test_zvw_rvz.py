"""
Tests for zvw_rvz.dmn

Tests health insurance status decision table.
"""
import pytest
from pathlib import Path


class TestZVW:
    """Test suite for ZVW (Health Insurance Law) DMN."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(dmn_dir / "zvw_rvz.dmn")
        self.decision_id = "decision_verzekerd_voor_zvw"

    def test_dmn_loads_successfully(self):
        """Test that the DMN file loads correctly."""
        assert self.dmn_spec is not None
        assert self.dmn_spec.name == "Zorgverzekeringswet (RVZ)"
        assert self.decision_id in self.dmn_spec.decisions

    def test_insured_and_resident(self):
        """Test person who is insured and resident."""
        person = {
            'health_insurance_status': 'verzekerd',
            'is_resident': True
        }
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {'person': person})

        assert result.output["verzekerd_voor_zvw"] is True

    def test_basic_insurance_and_resident(self):
        """Test person with basic insurance and resident."""
        person = {
            'health_insurance_status': 'basisverzekering',
            'is_resident': True
        }
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {'person': person})

        assert result.output["verzekerd_voor_zvw"] is True

    def test_not_insured(self):
        """Test person who is not insured."""
        person = {
            'health_insurance_status': 'niet_verzekerd',
            'is_resident': True
        }
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {'person': person})

        assert result.output["verzekerd_voor_zvw"] is False

    def test_not_resident(self):
        """Test person who is not a resident."""
        person = {
            'health_insurance_status': 'verzekerd',
            'is_resident': False
        }
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {'person': person})

        assert result.output["verzekerd_voor_zvw"] is False

    def test_unknown_status(self):
        """Test person with unknown insurance status."""
        person = {
            'health_insurance_status': 'onbekend',
            'is_resident': True
        }
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {'person': person})

        assert result.output["verzekerd_voor_zvw"] is False

    def test_null_insurance_status(self):
        """Test person with null insurance status."""
        person = {
            'health_insurance_status': None,
            'is_resident': True
        }
        result = self.engine.evaluate(self.dmn_spec, self.decision_id, {'person': person})

        assert result.output["verzekerd_voor_zvw"] is False
