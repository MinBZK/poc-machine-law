"""Pytest configuration for integration tests."""

import pytest
import pandas as pd
from datetime import datetime

from machine.data_context import DataContext
from machine.law_evaluator import LawEvaluator
from machine.service import Services


@pytest.fixture(scope="session")
def reference_date() -> str:
    """Default reference date for tests."""
    return "2025-01-01"


@pytest.fixture
def data_context() -> DataContext:
    """Create a fresh DataContext for each test."""
    return DataContext()


@pytest.fixture(scope="session")
def law_evaluator(reference_date: str) -> LawEvaluator:
    """Create a LawEvaluator with fresh DataContext.

    Note: Session-scoped to avoid event sourcing TopicError from creating
    multiple instances with wrapped event sourcing classes.
    """
    data_context = DataContext()
    return LawEvaluator(reference_date=reference_date, data_context=data_context)


@pytest.fixture(scope="session")
def services(reference_date: str) -> Services:
    """Create a Services instance for backward compatibility tests.

    Note: Session-scoped to avoid event sourcing TopicError from creating
    multiple instances with wrapped event sourcing classes.
    """
    return Services(reference_date=reference_date)


@pytest.fixture
def sample_person_data() -> pd.DataFrame:
    """Sample person data for testing."""
    return pd.DataFrame([{
        "bsn": "123456789",
        "geboortedatum": "1990-01-01",
        "partner_bsn": None
    }])


@pytest.fixture
def sample_brp_data() -> pd.DataFrame:
    """Sample BRP registration data for testing."""
    return pd.DataFrame([{
        "bsn": "123456789",
        "postcode": "1234AB",
        "huisnummer": "1"
    }])
