from typing import Any

from ..context import NrmlRuleContext


class ArgumentResolver:
    """Resolver for NRML expression arguments"""

    def __init__(self, item_evaluator):
        """Initialize with reference to the item evaluator"""
        self.item_evaluator = item_evaluator

    def resolve_argument(self, argument: Any, context: NrmlRuleContext) -> Any:
        """Resolve an argument which may contain references"""
        if isinstance(argument, list):
            # Handle list of arguments
            return [self.resolve_argument(item, context) for item in argument]
        elif isinstance(argument, dict):
            if "$ref" in argument:
                # Extract ref value and evaluate using item evaluator
                ref = argument["$ref"]
                result = self.item_evaluator.evaluate_item(ref, context)
                if result.Success:
                    return result.Value
                else:
                    raise ValueError(f"Failed to evaluate reference {ref}: {result.Value}")

            if "value" in argument:
                return argument["value"]

            raise ValueError(f"Failed to resolve argument reference")

        else:
            # Return primitive values as-is
            return argument