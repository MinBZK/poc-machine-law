from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result, nested_result


class ArgumentResolver:
    """Resolver for NRML expression arguments"""

    def __init__(self):
        """Initialize stateless resolver"""
        pass

    def resolve_argument(self, argument: Any, context: NrmlRuleContext) -> EvaluationResult:
        """Resolve an argument which may contain references"""

        if "$ref" in argument:
            # Extract ref value and evaluate using item evaluator from context
            ref = argument["$ref"]
            result = context.item_evaluator.evaluate_item(ref, context)
            return nested_result(source=self.__class__.__name__, node=argument, action=f"Resolving argument $ref {ref}", child_result=result)

        if "value" in argument:
            return create_result(success=True, value=argument["value"], source=self.__class__.__name__, node=argument, action="Resolved from argument value")

        raise ValueError(f"Failed to resolve argument reference")


