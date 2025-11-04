"""
Tests for wet_brp_rvig.dmn

Tests age calculation using FEEL years() function and decision tables
for partnership status determination.
"""
import pytest
from datetime import date
from pathlib import Path


class TestWetBRPRvig:
    """Test suite for Wet BRP (RvIG) DMN."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(dmn_dir / "wet_brp_rvig.dmn")

    def test_dmn_loads_successfully(self):
        """Test that the DMN file loads and parses correctly."""
        assert self.dmn_spec is not None
        assert self.dmn_spec.name == "Wet Basisregistratie Personen (RvIG)"
        assert len(self.dmn_spec.decisions) == 2
        assert "decision_leeftijd" in self.dmn_spec.decisions
        assert "decision_heeft_toeslagpartner" in self.dmn_spec.decisions


class TestLeeftijdCalculation:
    """Tests for age calculation decision."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(dmn_dir / "wet_brp_rvig.dmn")
        self.decision_id = "decision_leeftijd"

    def test_age_calculation_basic(self, reference_date):
        """Test basic age calculation."""
        person = {'birth_date': date(1985, 5, 15), 'partnership_status': 'alleenstaand'}
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.requirements_met is True
        assert result.output["leeftijd"] == 39  # Born May 15, 1985; ref date Jan 1, 2025

    def test_age_calculation_birthday_on_reference_date(self):
        """Test age when birthday is exactly on reference date."""
        person = {'birth_date': date(1985, 1, 1), 'partnership_status': 'alleenstaand'}
        reference_date = date(2025, 1, 1)
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["leeftijd"] == 40  # Birthday is today

    def test_age_calculation_birthday_after_reference_date(self):
        """Test age when birthday hasn't occurred yet this year."""
        person = {'birth_date': date(1985, 12, 31), 'partnership_status': 'alleenstaand'}
        reference_date = date(2025, 1, 1)
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["leeftijd"] == 39  # Birthday not yet in 2025

    def test_age_calculation_young_person(self):
        """Test age calculation for someone under 18."""
        person = {'birth_date': date(2010, 6, 15), 'partnership_status': 'alleenstaand'}
        reference_date = date(2025, 1, 1)
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["leeftijd"] == 14

    def test_age_calculation_elderly_person(self):
        """Test age calculation for elderly person."""
        person = {'birth_date': date(1950, 3, 10), 'partnership_status': 'alleenstaand'}
        reference_date = date(2025, 1, 1)
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["leeftijd"] == 74

    def test_age_no_errors(self, test_person_single, reference_date):
        """Test that age calculation produces no errors."""
        parameters = {'person': test_person_single, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert len(result.errors) == 0


class TestToeslagpartnerDecision:
    """Tests for partnership status decision table."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(dmn_dir / "wet_brp_rvig.dmn")
        self.decision_id = "decision_heeft_toeslagpartner"

    def test_single_person_no_partner(self, test_person_single, reference_date):
        """Test that single person has no toeslagpartner."""
        parameters = {'person': test_person_single, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["heeft_toeslagpartner"] is False

    def test_married_person_has_partner(self, test_person_married, reference_date):
        """Test that married person has toeslagpartner."""
        parameters = {'person': test_person_married, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["heeft_toeslagpartner"] is True

    def test_registered_partnership(self, reference_date):
        """Test registered partnership status."""
        person = {
            'birth_date': date(1990, 1, 1),
            'partnership_status': 'geregistreerd_partnerschap'
        }
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["heeft_toeslagpartner"] is True

    def test_fiscal_partner(self, reference_date):
        """Test fiscal partner status."""
        person = {
            'birth_date': date(1990, 1, 1),
            'partnership_status': 'fiscaal_partner'
        }
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["heeft_toeslagpartner"] is True

    def test_divorced_person(self, reference_date):
        """Test divorced person has no partner."""
        person = {
            'birth_date': date(1980, 1, 1),
            'partnership_status': 'gescheiden'
        }
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["heeft_toeslagpartner"] is False

    def test_widowed_person(self, reference_date):
        """Test widowed person has no partner."""
        person = {
            'birth_date': date(1970, 1, 1),
            'partnership_status': 'weduwe'
        }
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["heeft_toeslagpartner"] is False

    def test_partnership_null_value(self, reference_date):
        """Test null partnership status."""
        person = {
            'birth_date': date(1990, 1, 1),
            'partnership_status': None
        }
        parameters = {'person': person, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert result.output["heeft_toeslagpartner"] is False

    def test_decision_table_no_errors(self, test_person_single, reference_date):
        """Test that decision table evaluation produces no errors."""
        parameters = {'person': test_person_single, 'reference_date': reference_date}

        result = self.engine.evaluate(self.dmn_spec, self.decision_id, parameters)

        assert len(result.errors) == 0
        assert result.requirements_met is True


class TestBRPIntegration:
    """Integration tests combining multiple decisions."""

    @pytest.fixture(autouse=True)
    def setup(self, dmn_engine, dmn_dir):
        """Load the DMN file before each test."""
        self.engine = dmn_engine
        self.dmn_spec = self.engine.load_dmn(dmn_dir / "wet_brp_rvig.dmn")

    def test_single_adult_profile(self, reference_date):
        """Test complete profile for single adult."""
        person = {
            'birth_date': date(1985, 5, 15),
            'partnership_status': 'alleenstaand'
        }
        parameters = {'person': person, 'reference_date': reference_date}

        # Evaluate age
        age_result = self.engine.evaluate(
            self.dmn_spec, "decision_leeftijd", parameters
        )
        assert age_result.output["leeftijd"] == 39

        # Evaluate partnership
        partner_result = self.engine.evaluate(
            self.dmn_spec, "decision_heeft_toeslagpartner", parameters
        )
        assert partner_result.output["heeft_toeslagpartner"] is False

    def test_married_adult_profile(self, reference_date):
        """Test complete profile for married adult."""
        person = {
            'birth_date': date(1990, 3, 20),
            'partnership_status': 'gehuwd'
        }
        parameters = {'person': person, 'reference_date': reference_date}

        # Evaluate age
        age_result = self.engine.evaluate(
            self.dmn_spec, "decision_leeftijd", parameters
        )
        assert age_result.output["leeftijd"] == 34

        # Evaluate partnership
        partner_result = self.engine.evaluate(
            self.dmn_spec, "decision_heeft_toeslagpartner", parameters
        )
        assert partner_result.output["heeft_toeslagpartner"] is True
