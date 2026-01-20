from unittest.mock import Mock

import pytest

from machine.nrml.conditions.comparison_evaluator import ComparisonEvaluator
from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result


class TestComparisonEvaluator:
    """Test cases for ComparisonEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create a comparison evaluator instance"""
        return ComparisonEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        return NrmlRuleContext()

    def test_evaluate_in_comparison_success(self, evaluator, context):
        """Test successful 'in' comparison"""
        # Mock argument resolver to return successful results
        left_result = create_result(success=True, value="apple", source="ArgumentResolver")
        right_result = create_result(success=True, value=["apple", "banana", "orange"], source="ArgumentResolver")

        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[left_result, right_result])

        expression = {"operator": "in", "arguments": [{"value": "apple"}, {"value": ["apple", "banana", "orange"]}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value is True
        assert len(result.Dependencies) == 2

    def test_evaluate_in_comparison_not_found(self, evaluator, context):
        """Test 'in' comparison when value is not in collection"""
        left_result = create_result(success=True, value="grape", source="ArgumentResolver")
        right_result = create_result(success=True, value=["apple", "banana", "orange"], source="ArgumentResolver")

        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[left_result, right_result])

        expression = {"operator": "in", "arguments": [{"value": "grape"}, {"value": ["apple", "banana", "orange"]}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value is False

    def test_evaluate_in_comparison_wrong_argument_count(self, evaluator, context):
        """Test 'in' comparison with incorrect number of arguments"""
        expression = {"operator": "in", "arguments": [{"value": "apple"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert "Comparison operator 'in' expects 2 arguments" in result.Error

    def test_evaluate_in_comparison_resolution_failure(self, evaluator, context):
        """Test 'in' comparison when argument resolution fails"""
        left_result = create_result(success=False, error="Failed to resolve", source="ArgumentResolver")
        right_result = create_result(success=True, value=["apple", "banana"], source="ArgumentResolver")

        evaluator.argument_resolver.resolve_argument = Mock(side_effect=[left_result, right_result])

        expression = {"operator": "in", "arguments": [{"$ref": "unknown"}, {"value": ["apple", "banana"]}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert "Unable to resolve all arguments" in result.Error

    def test_check_in_collection_with_tuple(self, evaluator):
        """Test checking membership in a tuple"""
        result = evaluator._check_in_collection("apple", ("apple", "banana"))
        assert result is True

    def test_check_in_collection_with_set(self, evaluator):
        """Test checking membership in a set"""
        result = evaluator._check_in_collection("apple", {"apple", "banana"})
        assert result is True

    def test_check_in_collection_with_unhashable_types(self, evaluator):
        """Test checking membership with unhashable types (fallback to string comparison)"""
        result = evaluator._check_in_collection({"key": "value"}, [{"key": "value"}, {"key": "other"}])
        assert result is True

    def test_check_in_collection_invalid_collection_type(self, evaluator):
        """Test that non-collection types raise ValueError"""
        with pytest.raises(ValueError, match="Expected collection"):
            evaluator._check_in_collection("apple", "not a collection")

    def test_evaluate_unsupported_operator(self, evaluator, context):
        """Test that unsupported operators raise ValueError"""
        expression = {"operator": "equals", "arguments": [{"value": "a"}, {"value": "b"}]}

        with pytest.raises(ValueError, match="Unsupported comparison operator: equals"):
            evaluator.evaluate(expression, context)
