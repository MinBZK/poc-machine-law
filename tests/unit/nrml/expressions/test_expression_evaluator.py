from unittest.mock import Mock

import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.expressions.expression_evaluator import ExpressionEvaluator


class TestExpressionEvaluator:
    """Test cases for ExpressionEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create an expression evaluator instance"""
        return ExpressionEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        return NrmlRuleContext()

    def test_evaluate_conditional_expression(self, evaluator, context):
        """Test evaluating a conditional expression"""
        # Mock the conditional expression evaluator
        mock_result = create_result(success=True, value=True, source="MockEvaluator")
        evaluator.handlers["conditional"].evaluate = Mock(return_value=mock_result)

        expression = {"type": "conditional", "condition": {}}
        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value is True
        evaluator.handlers["conditional"].evaluate.assert_called_once_with(expression, context)

    def test_evaluate_not_implemented_expression_types(self, evaluator, context):
        """Test that unsupported expression types raise NotImplementedError"""
        expression_types = ["distribution", "function"]

        for expr_type in expression_types:
            expression = {"type": expr_type}
            with pytest.raises(NotImplementedError, match=f"Expression type '{expr_type}' not yet implemented"):
                evaluator.evaluate(expression, context)

    def test_evaluate_unsupported_expression_type(self, evaluator, context):
        """Test that unknown expression types raise NotImplementedError"""
        expression = {"type": "unknown_type"}

        with pytest.raises(NotImplementedError, match="Expression type 'unknown_type' not yet implemented"):
            evaluator.evaluate(expression, context)

    def test_evaluate_missing_type(self, evaluator, context):
        """Test evaluating expression without type field"""
        expression = {}

        with pytest.raises(NotImplementedError, match="Expression type 'None' not yet implemented"):
            evaluator.evaluate(expression, context)
