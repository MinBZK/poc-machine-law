from typing import Any

from ..aggregation_context import AggregationContext
from ..conditions.condition_evaluator import ConditionEvaluator
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from .argument_resolver import ArgumentResolver


class AggregationExpressionEvaluator:
    """Evaluator for aggregation expressions (type: 'aggregation')"""

    def __init__(self):
        """Initialize evaluator with internal state"""
        self.condition_evaluator = ConditionEvaluator()
        self.argument_resolver = ArgumentResolver()

    def evaluate(self, expression: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate an aggregation expression"""
        function = expression.get("function")
        if not function:
            raise ValueError("Aggregation expression missing function")

        expr_list = expression.get("expression", [])
        if not expr_list:
            raise ValueError("Aggregation expression missing expression list")

        condition = expression.get("condition")
        default_value = expression.get("default", {}).get("value", 0)

        # Resolve the collection reference
        if not expr_list:
            return create_result(
                success=True,
                value=default_value,
                source=self.__class__.__name__,
                action="Empty expression list, returning default",
            )

        # Get the first expression item (typically a $ref to a collection)
        collection_ref = expr_list[0]
        collection_result = self.argument_resolver.resolve_argument(collection_ref, context)

        if not collection_result.Success:
            return create_result(
                success=False,
                error="Failed to resolve collection reference",
                source=self.__class__.__name__,
                sub_results=[collection_result],
            )

        # Get the collection value (should be a list or iterable)
        collection = collection_result.Value
        if not isinstance(collection, list | tuple):
            # If single value, convert to list
            collection = [collection] if collection is not None else []

        # Apply the aggregation function
        if function == "count":
            count = self._count_with_condition(collection, condition, context)
            return create_result(
                success=True,
                value=count,
                source=self.__class__.__name__,
                action=f"Counted {count} items matching condition",
                node=expression,
            )
        else:
            raise NotImplementedError(f"Aggregation function '{function}' not yet implemented")

    def _count_with_condition(
        self, collection: list[Any], condition: dict[str, Any] | None, context: NrmlRuleContext
    ) -> int:
        """Count items in collection that match the condition"""
        if not condition:
            # No condition, just return the count
            return len(collection)

        count = 0
        for item in collection:
            # Wrap the item in an AggregationContext and evaluate the condition
            agg_context = AggregationContext(active_item=item)
            condition_result = self.condition_evaluator.evaluate(condition, context, agg_context)
            if condition_result.Success and condition_result.Value:
                count += 1

        return count
