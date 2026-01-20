from typing import Any

from ..aggregation_context import AggregationContext
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result, nested_result


class ArgumentResolver:
    """Resolver for NRML expression arguments"""

    def __init__(self):
        """Initialize stateless resolver"""

    def resolve_argument(
        self, argument: Any, context: NrmlRuleContext, aggregation_context: AggregationContext | None = None
    ) -> EvaluationResult:
        """Resolve an argument which may contain references"""

        # Handle array arguments (paths like [{"$ref": "#/facts/child"}, {"$ref": "#/facts/child/items/age"}])
        if isinstance(argument, list) and aggregation_context is not None:
            # Extract $ref values from each dict in the list to use as keys
            keys = [item.get("$ref") for item in argument if isinstance(item, dict) and "$ref" in item]

            if keys:
                value = aggregation_context.resolve_value(*keys)
                return create_result(
                    success=True,
                    value=value,
                    source=self.__class__.__name__,
                    node=argument,
                    action=f"Resolved path {keys} from aggregation context",
                )
            else:
                return create_result(
                    success=False,
                    error="No $ref values found in list argument",
                    source=self.__class__.__name__,
                    node=argument,
                )

        if isinstance(argument, dict):
            if "$ref" in argument:
                # Extract ref value
                ref = argument["$ref"]

                # Check if aggregation_context contains this reference in active_item
                if aggregation_context and ref in aggregation_context.active_item:
                    value = aggregation_context.active_item[ref]
                    return create_result(
                        success=True,
                        value=value,
                        source=self.__class__.__name__,
                        node=argument,
                        action=f"Resolved {ref} from aggregation context active item",
                    )

                # Fall back to evaluating using item evaluator from context
                result = context.item_evaluator.evaluate_item(ref, context)
                return nested_result(
                    source=self.__class__.__name__,
                    node=argument,
                    action=f"Resolving argument $ref {ref}",
                    child_result=result,
                )

            if "value" in argument:
                return create_result(
                    success=True,
                    value=argument["value"],
                    source=self.__class__.__name__,
                    node=argument,
                    action="Resolved from argument value",
                )

            # Check if this is a nested expression (has "type" field)
            if "type" in argument:
                # Import here to avoid circular dependency
                from .expression_evaluator import ExpressionEvaluator

                expression_evaluator = ExpressionEvaluator()
                result = expression_evaluator.evaluate(argument, context)
                return nested_result(
                    source=self.__class__.__name__,
                    node=argument,
                    action=f"Resolving nested expression of type '{argument.get('type')}'",
                    child_result=result,
                )

        raise ValueError("Failed to resolve argument reference")
