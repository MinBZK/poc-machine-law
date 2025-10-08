from unittest.mock import Mock

import pytest

from machine.nrml.conditions.condition_evaluator import ConditionEvaluator
from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result


class TestConditionEvaluator:
    """Test cases for ConditionEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create a condition evaluator instance"""
        return ConditionEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        return NrmlRuleContext()

    def test_evaluate_comparison_condition(self, evaluator, context):
        """Test evaluating a comparison condition"""
        # Mock the comparison evaluator
        mock_result = create_result(success=True, value=True, source="MockEvaluator")
        evaluator.handlers["comparison"].evaluate = Mock(return_value=mock_result)

        condition = {"type": "comparison", "operator": "in", "arguments": []}
        result = evaluator.evaluate(condition, context)

        assert result.Success is True
        assert result.Value is True
        evaluator.handlers["comparison"].evaluate.assert_called_once_with(condition, context, None)

    def test_evaluate_unsupported_condition_type(self, evaluator, context):
        """Test that unsupported condition types raise NotImplementedError"""
        condition = {"type": "unknown_type"}

        with pytest.raises(NotImplementedError, match="Condition type 'unknown_type' not yet implemented"):
            evaluator.evaluate(condition, context)

    def test_evaluate_missing_type(self, evaluator, context):
        """Test evaluating condition without type field"""
        condition = {}

        with pytest.raises(NotImplementedError, match="Condition type 'None' not yet implemented"):
            evaluator.evaluate(condition, context)
