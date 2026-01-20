from typing import Any

from ..context import NrmlRuleContext
from ..evaluation_result import EvaluationResult, create_result
from ..item_helper import NrmlItemHelper
from ..item_type_analyzer import NrmlItemType


class RelationDefinitionEvaluator:
    """Evaluator for relation definition items"""

    ITEM_TYPE = NrmlItemType.RELATION_DEFINITION

    def __init__(self):
        """Initialize stateless evaluator"""

    def _find_input_for_fact(self, fact_ref: str, context: NrmlRuleContext) -> tuple[str, dict[str, Any]] | None:
        """Find an input that matches the given fact reference

        Args:
            fact_ref: Fact reference like "#/facts/child"
            context: The rule context

        Returns:
            Tuple of (input_name, input_config) if found, None otherwise
        """
        inputs = context.nrml_spec.get("inputs", {})

        for input_name, input_config in inputs.items():
            input_type = input_config.get("type", {})
            type_ref = input_type.get("$ref")

            if type_ref == fact_ref:
                return (input_name, input_config)

        return None

    def _get_property_mappings(self, input_config: dict[str, Any]) -> dict[str, str]:
        """Extract property mappings from input configuration

        Args:
            input_config: Input configuration with optional properties field

        Returns:
            Dictionary mapping property names to fact item references
        """
        return input_config.get("properties", {})

    def _resolve_argument_data(self, fact_ref: str, context: NrmlRuleContext) -> list[dict[str, Any]]:
        result = []

        if not fact_ref:
            return result

        # Find input that matches this fact type
        input_result = self._find_input_for_fact(fact_ref, context)
        if not input_result:
            return result

        input_name, input_config = input_result

        # Get the parameter value for this input
        param_value = context.get_parameter_value(input_name)
        if not param_value:
            return result

        # Extract property mappings
        property_mappings = self._get_property_mappings(input_config)

        for input_objects in param_value:
            resolved_object = {}
            for property_name, property_value in property_mappings.items():
                resolved_object[property_value] = input_objects.get(property_name, {})
            result.append(resolved_object)

        return result

    def evaluate(self, item_key: str, item: dict[str, Any], context: NrmlRuleContext) -> EvaluationResult:
        """Evaluate a relation definition item"""
        active_version = NrmlItemHelper.get_active_version(item, context.calculation_date)

        # Extract fact schemas and find matching inputs for each argument
        resolved_data = []

        arguments = active_version.get("arguments", [])

        # Validate that we have exactly 2 arguments for relation definition
        if len(arguments) != 2:
            raise ValueError(
                f"Invalid relation definition for {item_key}: must have exactly 2 arguments, found {len(arguments)}"
            )

        # Resolve each argument
        arg_0_ref = arguments[0].get("objectType", {}).get("$ref")
        arg_0_results = self._resolve_argument_data(arg_0_ref, context)

        arg_1_ref = arguments[1].get("objectType", {}).get("$ref")
        arg_1_results = self._resolve_argument_data(arg_1_ref, context)

        # Create all combinations
        for result_0 in arg_0_results:
            for result_1 in arg_1_results:
                resolved_data.append(
                    {
                        arg_0_ref: result_0,
                        arg_1_ref: result_1,
                    }
                )

        return create_result(
            success=True,
            value=resolved_data,
            source=self.__class__.__name__,
            node=item,
            action=f"Relation {item_key} resolved with {len(resolved_data)} arguments",
        )
