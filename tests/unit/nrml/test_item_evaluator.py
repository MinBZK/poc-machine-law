from unittest.mock import Mock

import pytest

from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.item_evaluator import NrmlItemEvaluator
from machine.nrml.item_type_analyzer import NrmlItemType


class TestNrmlItemEvaluator:
    """Test cases for NrmlItemEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create an item evaluator instance"""
        return NrmlItemEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        context = NrmlRuleContext()
        context.items = {}
        context.language = "nl"
        return context

    def test_evaluate_type_definition_item(self, evaluator, context):
        """Test evaluating a type definition item"""
        item = {"versions": [{"type": "Text", "description": {"nl": "Test item"}}]}
        context.items["test_item"] = item

        # Mock the type definition evaluator
        mock_result = create_result(success=True, value="test_value", source="TypeDefinitionEvaluator")
        evaluator.evaluators[NrmlItemType.TYPE_DEFINITION].evaluate = Mock(return_value=mock_result)

        result = evaluator.evaluate_item("test_item", context)

        assert result.Success is True
        assert result.Value == "test_value"
        assert "test_item" in context.evaluation_results

    def test_evaluate_calculated_value_item(self, evaluator, context):
        """Test evaluating a calculated value item"""
        item = {
            "versions": [
                {"target": "result", "expression": {"type": "conditional"}, "description": {"nl": "Calculated item"}}
            ]
        }
        context.items["calc_item"] = item

        # Mock the calculated value evaluator
        mock_result = create_result(success=True, value=42, source="CalculatedValueEvaluator")
        evaluator.evaluators[NrmlItemType.CALCULATED_VALUE].evaluate = Mock(return_value=mock_result)

        result = evaluator.evaluate_item("calc_item", context)

        assert result.Success is True
        assert result.Value == 42
        assert "calc_item" in context.evaluation_results

    def test_evaluate_item_already_evaluated(self, evaluator, context):
        """Test that already evaluated items return cached result"""
        item = {"versions": [{"type": "Text", "description": {"nl": "Test item"}}]}
        context.items["test_item"] = item

        # Pre-populate evaluation result
        cached_result = create_result(success=True, value="cached_value", source="Cache")
        context.evaluation_results["test_item"] = cached_result

        result = evaluator.evaluate_item("test_item", context)

        assert result.Success is True
        assert result.Value == "cached_value"

    def test_evaluate_item_not_implemented_type(self, evaluator, context):
        """Test evaluating a relation definition with invalid arguments"""
        item = {
            "versions": [
                {
                    "arguments": [],  # This makes it a RELATION_DEFINITION but with invalid argument count
                    "description": {"nl": "Relation item"},
                }
            ]
        }
        context.items["relation_item"] = item

        with pytest.raises(ValueError, match="must have exactly 2 arguments"):
            evaluator.evaluate_item("relation_item", context)

    def test_evaluate_item_adds_to_path(self, evaluator, context):
        """Test that evaluation adds and removes path nodes correctly"""
        item = {"versions": [{"type": "Text", "description": {"nl": "Test item"}}]}
        context.items["test_item"] = item

        # Mock the evaluator
        mock_result = create_result(success=True, value="test", source="TypeDefinitionEvaluator")
        evaluator.evaluators[NrmlItemType.TYPE_DEFINITION].evaluate = Mock(return_value=mock_result)

        initial_path_length = len(context.path)
        evaluator.evaluate_item("test_item", context)

        # Path should be restored to original length
        assert len(context.path) == initial_path_length

    def test_evaluate_item_cleans_up_path_on_error(self, evaluator, context):
        """Test that path is cleaned up even when evaluation fails"""
        item = {"versions": [{"type": "Text", "description": {"nl": "Test item"}}]}
        context.items["test_item"] = item

        # Mock evaluator to raise an exception
        evaluator.evaluators[NrmlItemType.TYPE_DEFINITION].evaluate = Mock(side_effect=ValueError("Evaluation error"))

        initial_path_length = len(context.path)

        with pytest.raises(ValueError, match="Evaluation error"):
            evaluator.evaluate_item("test_item", context)

        # Path should still be cleaned up
        assert len(context.path) == initial_path_length

    def test_evaluate_item_stores_result_in_context(self, evaluator, context):
        """Test that evaluation result is stored in context"""
        item = {"versions": [{"type": "Text", "description": {"nl": "Test item"}}]}
        context.items["test_item"] = item

        mock_result = create_result(success=True, value="test", source="TypeDefinitionEvaluator")
        evaluator.evaluators[NrmlItemType.TYPE_DEFINITION].evaluate = Mock(return_value=mock_result)

        evaluator.evaluate_item("test_item", context)

        assert "test_item" in context.evaluation_results
        assert context.evaluation_results["test_item"].Value == "test"
