from typing import Any

from ..context import PathNode, RuleContext, logger
from .context import NrmlRuleContext
from .evaluators.calculated_value_evaluator import CalculatedValueEvaluator
from .evaluators.type_definition_evaluator import TypeDefinitionEvaluator
from .evaluation_result import FactItemEvaluationResult
from .expressions.expression_evaluator import ExpressionEvaluator
from .item_helper import NrmlItemHelper
from .item_type_analyzer import NrmlItemType, determine_item_type


class NrmlItemEvaluator:
    """Evaluator for different NRML item types"""

    def __init__(self):
        # Initialize evaluator dictionary
        self.evaluators = {
            NrmlItemType.TYPE_DEFINITION: TypeDefinitionEvaluator(),
            NrmlItemType.CALCULATED_VALUE: CalculatedValueEvaluator(),
        }

    def evaluate_item(self, item_key: str, context: NrmlRuleContext) -> FactItemEvaluationResult:
        """
        Evaluate an NRML item based on its type

        Args:
            item_key: The NRML item dictionary key
            context: The rule evaluation context

        Returns:
            The evaluation result
        """

        # Determine the item type
        item = context.items[item_key]
        item_type = determine_item_type(item)

        # TODO: we could just process the items in topologically sorted order, but then we dont know the indentation
        #  or the optionality of any relations (ex in case of x OR y)

        with logger.indent_block("Evaluating item"):
            item_node = PathNode(type="item", name=f"Evaluate item: {item_type.value}", result=None)
            context.add_to_path(item_node)

            try:
                # Handle different item types using evaluator dictionary
                evaluator = self.evaluators.get(item_type)
                if evaluator:
                    result = evaluator.evaluate(item_key, item, context)
                else:
                    raise NotImplementedError(f"Evaluator not implemented for item type: {item_type.value}")

                item_node.result = result
                return result
            finally:
                context.pop_path()
