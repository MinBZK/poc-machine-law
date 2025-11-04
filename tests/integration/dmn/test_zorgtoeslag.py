"""
Tests for zorgtoeslag_toeslagen_2025.dmn

Tests the main zorgtoeslag law with cross-DMN references.
"""
import pytest
from pathlib import Path
from datetime import date


class TestZorgtoeslag:
    """Test suite for Zorgtoeslag 2025 DMN."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(
            dmn_dir / "zorgtoeslag_toeslagen_2025.dmn"
        )

    def test_dmn_loads(self):
        """Test that the DMN file loads successfully."""
        assert self.dmn_spec is not None
        assert self.dmn_spec.name == "Zorgtoeslag 2025 (Toeslagen)"
        assert len(self.dmn_spec.imports) == 5  # Should have 5 imports

    def test_eligible_single_low_income(
        self,
        test_person_single,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test eligible single person with low income."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_is_verzekerde_zorgtoeslag",
            parameters
        )

        assert result.output["is_verzekerde_zorgtoeslag"] is True

    def test_ineligible_too_young(
        self,
        test_person_young,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test person under 18 is not eligible."""
        parameters = {
            'person': test_person_young,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_is_verzekerde_zorgtoeslag",
            parameters
        )

        assert result.output["is_verzekerde_zorgtoeslag"] is False

    def test_ineligible_not_insured(
        self,
        test_person_not_insured,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test person without insurance is not eligible."""
        parameters = {
            'person': test_person_not_insured,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_is_verzekerde_zorgtoeslag",
            parameters
        )

        assert result.output["is_verzekerde_zorgtoeslag"] is False

    def test_benefit_calculation_single(
        self,
        test_person_single,
        reference_date,
        test_tax_data_low_income,
        test_income_data_employed
    ):
        """Test benefit amount calculation for single person."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_low_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_hoogte_toeslag",
            parameters
        )

        # Should get some benefit
        assert result.output["hoogte_toeslag"] > 0

    def test_no_benefit_high_income(
        self,
        test_person_single,
        reference_date,
        test_tax_data_high_income,
        test_income_data_employed
    ):
        """Test no benefit for high income."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_high_income,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_hoogte_toeslag",
            parameters
        )

        assert result.output["hoogte_toeslag"] == 0

    def test_no_benefit_high_wealth(
        self,
        test_person_single,
        reference_date,
        test_tax_data_high_wealth,
        test_income_data_employed
    ):
        """Test no benefit for high wealth."""
        parameters = {
            'person': test_person_single,
            'reference_date': reference_date,
            'tax_data': test_tax_data_high_wealth,
            'income_data': test_income_data_employed,
            'partner_income_data': None,
        }

        result = self.engine.evaluate(
            self.dmn_spec,
            "decision_hoogte_toeslag",
            parameters
        )

        assert result.output["hoogte_toeslag"] == 0
