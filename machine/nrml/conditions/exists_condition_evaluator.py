from typing import Any

from ..aggregation_context import AggregationContext
from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from ..expressions.argument_resolver import ArgumentResolver


class ExistsConditionEvaluator:
    """Evaluator for exists conditions (checking characteristic presence)"""

    def __init__(self):
        """Initialize evaluator with argument resolver"""
        self.argument_resolver = ArgumentResolver()

    def _find_characteristic_item(self, characteristic_ref: list, context: NrmlRuleContext) -> str | None:
        """Find the item key for a characteristic reference

        Args:
            characteristic_ref: Array of refs like [{"$ref": "#/facts/child"}, {"$ref": "#/facts/child/items/jong-kind"}]
            context: The NRML rule context

        Returns:
            The item key (e.g., "#/facts/child/items/jong-kind") or None
        """
        # The second element should be the characteristic item reference
        if (
            isinstance(characteristic_ref, list)
            and len(characteristic_ref) >= 2
            and isinstance(characteristic_ref[1], dict)
            and "$ref" in characteristic_ref[1]
        ):
            return characteristic_ref[1]["$ref"]
        return None

    def _find_conditional_characteristic_source(
        self, characteristic_item_key: str, context: NrmlRuleContext
    ) -> str | None:
        """Find a conditional characteristic that targets this characteristic

        Args:
            characteristic_item_key: The characteristic item key to search for
            context: The NRML rule context

        Returns:
            The source item key that assigns this characteristic, or None
        """
        # Search through target_references to find items that target this characteristic
        # target_references is {target_ref: source_item_id}
        for target_key, source_key in context.target_references.items():
            if target_key == characteristic_item_key:
                return source_key
        return None

    def evaluate(
        self,
        condition: dict[str, Any],
        context: NrmlRuleContext,
        aggregation_context: AggregationContext | None = None,
    ) -> EvaluationResult:
        """Evaluate an exists condition

        Checks if a characteristic exists by:
        1. First trying to resolve it from the aggregation context (if already assigned)
        2. If not found, looking for a conditional characteristic and evaluating its condition

        Args:
            condition: The condition dictionary with "characteristic" field
            context: The NRML rule context
            aggregation_context: The aggregation context (required for exists checks)

        Returns:
            EvaluationResult with True if characteristic exists, False otherwise
        """
        characteristic_arg = condition.get("characteristic")

        if not characteristic_arg:
            return create_result(
                success=False,
                error="Exists condition requires a 'characteristic' argument",
                source=self.__class__.__name__,
            )

        if not aggregation_context:
            return create_result(
                success=False,
                error="Exists condition requires an aggregation context",
                source=self.__class__.__name__,
            )

        # Try to resolve the characteristic from aggregation context first
        characteristic_result = self.argument_resolver.resolve_argument(
            characteristic_arg, context, aggregation_context
        )

        # If successfully resolved and truthy, the characteristic exists
        if characteristic_result.Success and characteristic_result.Value:
            return create_result(
                success=True,
                value=True,
                source=self.__class__.__name__,
                dependencies=[characteristic_result],
                action="Characteristic exists (resolved from context)",
            )

        # If not found in context, try to find and evaluate the conditional characteristic
        characteristic_item_key = self._find_characteristic_item(characteristic_arg, context)
        if characteristic_item_key:
            source_key = self._find_conditional_characteristic_source(characteristic_item_key, context)
            if source_key and source_key in context.items:
                item = context.items[source_key]
                # Get the first version and its condition
                versions = item.get("versions", [])
                if versions:
                    version = versions[0]
                    cond = version.get("condition")
                    if cond:
                        # Import here to avoid circular dependency
                        from .condition_evaluator import ConditionEvaluator

                        condition_evaluator = ConditionEvaluator()

                        # Evaluate the condition in the current aggregation context
                        cond_result = condition_evaluator.evaluate(cond, context, aggregation_context)
                        return create_result(
                            success=True,
                            value=bool(cond_result.Value) if cond_result.Success else False,
                            source=self.__class__.__name__,
                            dependencies=[cond_result],
                            action=f"Characteristic exists: {bool(cond_result.Value) if cond_result.Success else False} (evaluated from conditional characteristic)",
                        )

        # Characteristic doesn't exist
        return create_result(
            success=True,
            value=False,
            source=self.__class__.__name__,
            action="Characteristic does not exist",
        )
