from unittest.mock import Mock

import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.items.calculated_value_evaluator import CalculatedValueEvaluator


class TestCalculatedValueEvaluator:
    """Test cases for CalculatedValueEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create a calculated value evaluator instance"""
        return CalculatedValueEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        return NrmlRuleContext()

    def test_evaluate_calculated_value_success(self, evaluator, context):
        """Test successful evaluation of a calculated value"""
        # Mock the expression evaluator
        mock_result = create_result(success=True, value=42, source="ExpressionEvaluator")
        evaluator.expression_evaluator.evaluate = Mock(return_value=mock_result)

        item = {"versions": [{"expression": {"type": "conditional"}, "target": "result"}]}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is True
        assert result.Value == 42
        assert len(result.Dependencies) == 1
        assert result.Action == "Determining Calculated value for item test_item"

    def test_evaluate_no_versions(self, evaluator, context):
        """Test evaluation when item has no versions"""
        item = {"versions": []}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is False
        assert "No versions found" in result.Error

    def test_evaluate_missing_versions_key(self, evaluator, context):
        """Test evaluation when versions key is missing"""
        item = {}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is False
        assert "No versions found" in result.Error

    def test_evaluate_no_expression(self, evaluator, context):
        """Test evaluation when version has no expression"""
        item = {"versions": [{"target": "result"}]}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is False
        assert "No expression found" in result.Error

    def test_evaluate_no_target(self, evaluator, context):
        """Test evaluation when version has no target"""
        item = {"versions": [{"expression": {"type": "conditional"}}]}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is False
        assert "No target found" in result.Error

    def test_evaluate_expression_evaluation_error(self, evaluator, context):
        """Test evaluation when expression evaluation raises an exception"""
        evaluator.expression_evaluator.evaluate = Mock(side_effect=ValueError("Invalid expression"))

        item = {"versions": [{"expression": {"type": "conditional"}, "target": "result"}]}

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is False
        assert "Error evaluating expression" in result.Error
        assert "Invalid expression" in result.Error

    def test_evaluate_uses_first_version(self, evaluator, context):
        """Test that evaluation uses the first version when multiple exist"""
        mock_result = create_result(success=True, value=100, source="ExpressionEvaluator")
        evaluator.expression_evaluator.evaluate = Mock(return_value=mock_result)

        item = {
            "versions": [
                {"expression": {"type": "conditional", "id": "first"}, "target": "result1"},
                {"expression": {"type": "conditional", "id": "second"}, "target": "result2"},
            ]
        }

        result = evaluator.evaluate("test_item", item, context)

        assert result.Success is True
        # Verify that the first version's expression was used
        call_args = evaluator.expression_evaluator.evaluate.call_args[0]
        assert call_args[0]["id"] == "first"
