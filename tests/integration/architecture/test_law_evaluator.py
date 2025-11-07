"""Integration tests for LawEvaluator."""

import pytest
import pandas as pd

from machine.law_evaluator import LawEvaluator
from machine.data_context import DataContext
from machine.service import RuleResult


class TestLawEvaluator:
    """Test suite for LawEvaluator functionality."""

    def test_law_evaluator_creation(self, law_evaluator: LawEvaluator):
        """Test that LawEvaluator can be created."""
        assert law_evaluator is not None
        assert law_evaluator.resolver is not None
        assert law_evaluator.data_context is not None
        assert isinstance(law_evaluator._engines_cache, dict)

    def test_law_evaluator_with_data_context(self, reference_date: str, law_evaluator: LawEvaluator):
        """Test LawEvaluator with pre-populated DataContext."""
        # Use the session fixture evaluator and clear its data
        law_evaluator.data_context.sources.clear()

        # Populate data context
        df_personen = pd.DataFrame([{
            "bsn": "123456789",
            "geboortedatum": "1990-01-01"
        }])
        law_evaluator.data_context.add_source("SVB", "personen", df_personen)

        # Verify data context is populated
        assert law_evaluator.data_context.has_source("SVB", "personen")

    def test_evaluate_simple_law(self, law_evaluator: LawEvaluator, sample_person_data: pd.DataFrame):
        """Test evaluating a simple law."""
        # Clear any existing data first (since fixture is session-scoped)
        law_evaluator.data_context.sources.clear()

        # Add test data
        law_evaluator.data_context.add_source("SVB", "personen", sample_person_data)

        # Evaluate law
        result = law_evaluator.evaluate_law(
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date="2025-01-01"
        )

        # Verify result structure
        assert isinstance(result, RuleResult)
        assert isinstance(result.requirements_met, bool)
        assert isinstance(result.output, dict)
        assert result.rulespec_uuid is not None

    def test_engine_caching(self, law_evaluator: LawEvaluator):
        """Test that engines are cached by (law, reference_date)."""
        # Note: Since fixture is session-scoped, cache may already have entries
        # Clear cache for this test
        law_evaluator._engines_cache.clear()

        # First call should create engine
        cache_key = ("algemene_kinderbijslagwet", "2025-01-01")
        assert cache_key not in law_evaluator._engines_cache

        # Get engine
        engine1 = law_evaluator._get_engine("algemene_kinderbijslagwet", "2025-01-01")

        # Should now be cached
        assert cache_key in law_evaluator._engines_cache

        # Second call should return cached engine
        engine2 = law_evaluator._get_engine("algemene_kinderbijslagwet", "2025-01-01")
        assert engine1 is engine2

    def test_different_dates_different_engines(self, law_evaluator: LawEvaluator):
        """Test that different reference dates create different engines."""
        engine_2025 = law_evaluator._get_engine("algemene_kinderbijslagwet", "2025-01-01")
        engine_2024 = law_evaluator._get_engine("algemene_kinderbijslagwet", "2024-01-01")

        # Should be different engine instances
        assert engine_2025 is not engine_2024

    def test_law_not_found(self, law_evaluator: LawEvaluator):
        """Test evaluating a non-existent law raises appropriate error."""
        with pytest.raises(ValueError, match="No rules found"):
            law_evaluator.evaluate_law(
                law="nonexistent_law",
                parameters={"BSN": "123456789"},
                reference_date="2025-01-01"
            )

    def test_evaluate_with_overrides(self, law_evaluator: LawEvaluator, sample_person_data: pd.DataFrame):
        """Test law evaluation with input overrides."""
        # Clear and add test data
        law_evaluator.data_context.sources.clear()
        law_evaluator.data_context.add_source("SVB", "personen", sample_person_data)

        # Evaluate with overrides
        result = law_evaluator.evaluate_law(
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date="2025-01-01",
            overwrite_input={"aantal_kinderen": 3}
        )

        assert isinstance(result, RuleResult)
        # The override should be reflected in the evaluation

    def test_requested_output(self, law_evaluator: LawEvaluator, sample_person_data: pd.DataFrame):
        """Test requesting specific output field."""
        # Clear and add test data
        law_evaluator.data_context.sources.clear()
        law_evaluator.data_context.add_source("SVB", "personen", sample_person_data)

        # Request specific output
        result = law_evaluator.evaluate_law(
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date="2025-01-01",
            requested_output="ontvangt_kinderbijslag"
        )

        assert isinstance(result, RuleResult)
        # Result should contain the requested output

    def test_shared_data_context_across_evaluations(self, law_evaluator: LawEvaluator):
        """Test that DataContext is shared across multiple evaluations."""
        # Clear and add data once
        law_evaluator.data_context.sources.clear()
        df_personen = pd.DataFrame([{"bsn": "123456789", "geboortedatum": "1990-01-01"}])
        law_evaluator.data_context.add_source("SVB", "personen", df_personen)

        # First evaluation
        result1 = law_evaluator.evaluate_law(
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date="2025-01-01"
        )

        # Second evaluation should use same data
        result2 = law_evaluator.evaluate_law(
            law="algemene_kinderbijslagwet",
            parameters={"BSN": "123456789"},
            reference_date="2025-01-01"
        )

        # Both should succeed using the same data context
        assert isinstance(result1, RuleResult)
        assert isinstance(result2, RuleResult)
