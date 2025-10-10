from unittest.mock import Mock

import pytest

from machine.nrml.aggregation_context import AggregationContext
from machine.nrml.context import NrmlRuleContext
from machine.nrml.evaluation_result import create_result
from machine.nrml.expressions.aggregation_expression_evaluator import AggregationExpressionEvaluator


class TestAggregationExpressionEvaluator:
    """Test cases for AggregationExpressionEvaluator"""

    @pytest.fixture
    def evaluator(self):
        """Create an aggregation expression evaluator instance"""
        return AggregationExpressionEvaluator()

    @pytest.fixture
    def context(self):
        """Create a mock NRML rule context"""
        return NrmlRuleContext()

    def test_count_without_condition(self, evaluator, context):
        """Test count function without a condition returns the collection length"""
        # Mock the argument resolver to return a collection
        collection = [{"age": 5}, {"age": 10}, {"age": 15}]
        collection_result = create_result(success=True, value=collection, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        expression = {"function": "count", "expression": [{"$ref": "#/facts/items"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 3
        assert len(result.Dependencies) == 1
        assert result.Dependencies[0] == collection_result
        assert "No condition to evaluate" in result.Action

    def test_count_with_condition_matching_some_items(self, evaluator, context):
        """Test count function with condition that matches some items"""
        # Mock the argument resolver to return a collection
        collection = [{"age": 5}, {"age": 10}, {"age": 15}]
        collection_result = create_result(success=True, value=collection, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        # Mock condition evaluator to return True, False, False for the three items
        condition_results = [
            create_result(success=True, value=True, source="ConditionEvaluator"),
            create_result(success=True, value=False, source="ConditionEvaluator"),
            create_result(success=True, value=False, source="ConditionEvaluator"),
        ]
        evaluator.condition_evaluator.evaluate = Mock(side_effect=condition_results)

        expression = {
            "function": "count",
            "expression": [{"$ref": "#/facts/items"}],
            "condition": {"type": "comparison", "operator": "lessThanOrEqual"},
        }

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 1
        assert len(result.Dependencies) == 4  # collection_result + 3 condition results
        assert result.Dependencies[0] == collection_result
        assert "Counted 1 items matching condition" in result.Action

    def test_count_with_condition_matching_all_items(self, evaluator, context):
        """Test count function with condition that matches all items"""
        # Mock the argument resolver to return a collection
        collection = [{"age": 5}, {"age": 10}]
        collection_result = create_result(success=True, value=collection, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        # Mock condition evaluator to return True for both items
        condition_results = [
            create_result(success=True, value=True, source="ConditionEvaluator"),
            create_result(success=True, value=True, source="ConditionEvaluator"),
        ]
        evaluator.condition_evaluator.evaluate = Mock(side_effect=condition_results)

        expression = {
            "function": "count",
            "expression": [{"$ref": "#/facts/items"}],
            "condition": {"type": "comparison"},
        }

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 2
        assert len(result.Dependencies) == 3  # collection_result + 2 condition results

    def test_count_with_condition_matching_no_items(self, evaluator, context):
        """Test count function with condition that matches no items"""
        # Mock the argument resolver to return a collection
        collection = [{"age": 5}, {"age": 10}]
        collection_result = create_result(success=True, value=collection, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        # Mock condition evaluator to return False for both items
        condition_results = [
            create_result(success=True, value=False, source="ConditionEvaluator"),
            create_result(success=True, value=False, source="ConditionEvaluator"),
        ]
        evaluator.condition_evaluator.evaluate = Mock(side_effect=condition_results)

        expression = {
            "function": "count",
            "expression": [{"$ref": "#/facts/items"}],
            "condition": {"type": "comparison"},
        }

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 0
        assert "Counted 0 items matching condition" in result.Action

    def test_count_with_empty_collection(self, evaluator, context):
        """Test count function with empty collection"""
        # Mock the argument resolver to return an empty collection
        collection_result = create_result(success=True, value=[], source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        expression = {"function": "count", "expression": [{"$ref": "#/facts/items"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 0
        assert "No condition to evaluate" in result.Action

    def test_count_with_single_value_converted_to_list(self, evaluator, context):
        """Test count function with single value that gets converted to list"""
        # Mock the argument resolver to return a single value (not a list)
        single_value = {"age": 10}
        collection_result = create_result(success=True, value=single_value, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        expression = {"function": "count", "expression": [{"$ref": "#/facts/item"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 1

    def test_count_with_none_value_converted_to_empty_list(self, evaluator, context):
        """Test count function with None value that gets converted to empty list"""
        # Mock the argument resolver to return None
        collection_result = create_result(success=True, value=None, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        expression = {"function": "count", "expression": [{"$ref": "#/facts/item"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 0

    def test_count_with_condition_evaluation_failure(self, evaluator, context):
        """Test count function when condition evaluation fails"""
        # Mock the argument resolver to return a collection
        collection = [{"age": 5}, {"age": 10}]
        collection_result = create_result(success=True, value=collection, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        # Mock condition evaluator to fail on first item
        condition_failure = create_result(success=False, error="Condition failed", source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_failure)

        expression = {
            "function": "count",
            "expression": [{"$ref": "#/facts/items"}],
            "condition": {"type": "comparison"},
        }

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert "Failed to evaluate condition" in result.Action
        assert result.Value == 0
        assert len(result.Dependencies) == 2  # collection_result + failed condition result

    def test_count_passes_aggregation_context_to_condition(self, evaluator, context):
        """Test that count function passes aggregation context when evaluating conditions"""
        # Mock the argument resolver to return a collection
        collection = [{"age": 5}]
        collection_result = create_result(success=True, value=collection, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        # Mock condition evaluator
        condition_result = create_result(success=True, value=True, source="ConditionEvaluator")
        evaluator.condition_evaluator.evaluate = Mock(return_value=condition_result)

        expression = {
            "function": "count",
            "expression": [{"$ref": "#/facts/items"}],
            "condition": {"type": "comparison"},
        }

        result = evaluator.evaluate(expression, context)

        # Verify the result is successful
        assert result.Success is True
        assert result.Value == 1

        # Verify condition evaluator was called with an AggregationContext
        assert evaluator.condition_evaluator.evaluate.called
        call_args = evaluator.condition_evaluator.evaluate.call_args
        agg_context = call_args[0][2]  # Third argument
        assert isinstance(agg_context, AggregationContext)
        assert agg_context.active_item == {"age": 5}

    def test_failed_collection_resolution(self, evaluator, context):
        """Test when collection reference resolution fails"""
        # Mock the argument resolver to fail
        collection_result = create_result(success=False, error="Failed to resolve", source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        expression = {"function": "count", "expression": [{"$ref": "#/facts/invalid"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is False
        assert "Failed to resolve collection reference" in result.Error
        assert len(result.Dependencies) == 1
        assert result.Dependencies[0] == collection_result

    def test_missing_function(self, evaluator, context):
        """Test evaluation fails when function is missing"""
        expression = {"expression": [{"$ref": "#/facts/items"}]}

        with pytest.raises(ValueError, match="Aggregation expression missing function"):
            evaluator.evaluate(expression, context)

    def test_missing_expression_list(self, evaluator, context):
        """Test evaluation fails when expression list is missing"""
        expression = {"function": "count"}

        with pytest.raises(ValueError, match="Aggregation expression missing expression list"):
            evaluator.evaluate(expression, context)

    def test_empty_expression_list(self, evaluator, context):
        """Test evaluation fails when expression list is empty"""
        expression = {"function": "count", "expression": []}

        with pytest.raises(ValueError, match="Aggregation expression missing expression list"):
            evaluator.evaluate(expression, context)

    def test_multiple_expression_arguments_not_implemented(self, evaluator, context):
        """Test evaluation fails when multiple expression arguments are provided"""
        expression = {
            "function": "count",
            "expression": [{"$ref": "#/facts/items1"}, {"$ref": "#/facts/items2"}],
        }

        with pytest.raises(ValueError, match="More then one argument as expression is not implemented"):
            evaluator.evaluate(expression, context)

    def test_unsupported_aggregation_function(self, evaluator, context):
        """Test evaluation fails for unsupported aggregation functions"""
        # Mock the argument resolver to return a collection
        collection_result = create_result(success=True, value=[1, 2, 3], source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        expression = {"function": "sum", "expression": [{"$ref": "#/facts/items"}]}

        with pytest.raises(NotImplementedError, match="Aggregation function 'sum' not yet implemented"):
            evaluator.evaluate(expression, context)

    def test_count_with_tuple_collection(self, evaluator, context):
        """Test count function works with tuple collections"""
        # Mock the argument resolver to return a tuple
        collection = ({"age": 5}, {"age": 10})
        collection_result = create_result(success=True, value=collection, source="ArgumentResolver")
        evaluator.argument_resolver.resolve_argument = Mock(return_value=collection_result)

        expression = {"function": "count", "expression": [{"$ref": "#/facts/items"}]}

        result = evaluator.evaluate(expression, context)

        assert result.Success is True
        assert result.Value == 2
