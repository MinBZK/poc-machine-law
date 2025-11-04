"""
Pytest fixtures for DMN integration tests.
"""
import pytest
from datetime import date
from pathlib import Path

from machine.dmn import DMNEngine


@pytest.fixture
def dmn_engine():
    """Create a fresh DMN engine instance for each test."""
    return DMNEngine()


@pytest.fixture
def dmn_dir():
    """Path to the DMN files directory."""
    return Path("dmn")


@pytest.fixture
def reference_date():
    """Standard reference date for tests."""
    return date(2025, 1, 1)


@pytest.fixture
def test_person_single():
    """Test data: single person."""
    return {
        'birth_date': date(1985, 5, 15),
        'partnership_status': 'alleenstaand',
        'health_insurance_status': 'verzekerd',
        'is_resident': True,
    }


@pytest.fixture
def test_person_married():
    """Test data: married person."""
    return {
        'birth_date': date(1990, 3, 20),
        'partnership_status': 'gehuwd',
        'health_insurance_status': 'verzekerd',
        'is_resident': True,
    }


@pytest.fixture
def test_person_young():
    """Test data: person under 18."""
    return {
        'birth_date': date(2010, 6, 15),
        'partnership_status': 'alleenstaand',
        'health_insurance_status': 'verzekerd',
        'is_resident': True,
    }


@pytest.fixture
def test_person_not_insured():
    """Test data: person without insurance."""
    return {
        'birth_date': date(1985, 5, 15),
        'partnership_status': 'alleenstaand',
        'health_insurance_status': 'niet_verzekerd',
        'is_resident': True,
    }


@pytest.fixture
def test_tax_data_low_income():
    """Test data: low income and wealth."""
    return {
        'box1_inkomen': 2500000,  # €25,000
        'box2_inkomen': 0,
        'box3_inkomen': 0,
        'vermogen': 5000000,  # €50,000
    }


@pytest.fixture
def test_tax_data_high_income():
    """Test data: high income above threshold."""
    return {
        'box1_inkomen': 5000000,  # €50,000
        'box2_inkomen': 0,
        'box3_inkomen': 0,
        'vermogen': 5000000,  # €50,000
    }


@pytest.fixture
def test_tax_data_high_wealth():
    """Test data: wealth above limit."""
    return {
        'box1_inkomen': 2500000,  # €25,000
        'box2_inkomen': 0,
        'box3_inkomen': 0,
        'vermogen': 15000000,  # €150,000 (above limit)
    }


@pytest.fixture
def test_income_data_employed():
    """Test data: employed person income."""
    return {
        'work_income': 3500000,  # €35,000
        'unemployment_benefit': 0,
        'disability_benefit': 0,
        'pension': 0,
        'other_benefits': 0,
    }


@pytest.fixture
def test_income_data_unemployed():
    """Test data: unemployed person with benefits."""
    return {
        'work_income': 0,
        'unemployment_benefit': 1800000,  # €18,000
        'disability_benefit': 0,
        'pension': 0,
        'other_benefits': 0,
    }


@pytest.fixture
def test_income_data_retired():
    """Test data: retired person with pension."""
    return {
        'work_income': 0,
        'unemployment_benefit': 0,
        'disability_benefit': 0,
        'pension': 2000000,  # €20,000
        'other_benefits': 0,
    }


@pytest.fixture
def test_income_data_high_income():
    """Test data: high income above threshold."""
    return {
        'work_income': 5000000,  # €50,000 (above threshold)
        'unemployment_benefit': 0,
        'disability_benefit': 0,
        'pension': 0,
        'other_benefits': 0,
    }
