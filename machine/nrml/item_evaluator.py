from ..context import PathNode
from .context import NrmlRuleContext
from .evaluation_result import EvaluationResult
from .item_helper import NrmlItemHelper
from .item_type_analyzer import determine_item_type
from .items.calculated_value_evaluator import CalculatedValueEvaluator
from .items.conditional_characteristic_evaluator import ConditionalCharacteristicEvaluator
from .items.relation_definition_evaluator import RelationDefinitionEvaluator
from .items.type_definition_evaluator import TypeDefinitionEvaluator


class NrmlItemEvaluator:
    """Evaluator for different NRML item types"""

    def __init__(self):
        # Initialize evaluator dictionary
        self.evaluators = {
            TypeDefinitionEvaluator.ITEM_TYPE: TypeDefinitionEvaluator(),
            CalculatedValueEvaluator.ITEM_TYPE: CalculatedValueEvaluator(),
            RelationDefinitionEvaluator.ITEM_TYPE: RelationDefinitionEvaluator(),
            ConditionalCharacteristicEvaluator.ITEM_TYPE: ConditionalCharacteristicEvaluator(),
        }

    def evaluate_item(self, item_key: str, context: NrmlRuleContext) -> EvaluationResult:
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

        description = NrmlItemHelper.get_item_description(item, context.language)
        item_node = PathNode(
            type="item", name=f"Evaluate item: {item_key} {description} (type: {item_type})", result=None
        )
        context.add_to_path(item_node)

        try:
            existing_result = context.get_evaluation_result(item_key)
            if existing_result:
                return existing_result

            # Handle different item types using evaluator dictionary
            evaluator = self.evaluators.get(item_type)
            if evaluator:
                result = evaluator.evaluate(item_key, item, context)
                context.add_evaluation_result(item_key, result)
            else:
                raise NotImplementedError(f"Evaluator not implemented for item type: {item_type.value}")
            return result
        finally:
            context.pop_path()
