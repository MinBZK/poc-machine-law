from typing import Any

import pandas as pd

from ..context import logger
from .context import NrmlRuleContext
from .item_evaluator import NrmlItemEvaluator
from .item_type_analyzer import NrmlItemType, determine_item_type


class NrmlRulesEngine:
    """Rules engine for evaluating business rules"""

    def __init__(self, spec: dict[str, Any], service_provider: Any | None = None) -> None:
        self.spec = spec
        self.facts = spec.get("facts", {})
        self.items = {}
        self.law = spec.get("metadata", {}).get("description", {})

        # Fill items dictionary with JSON Pointer references
        for fact_id, fact in self.facts.items():
            items = fact.get("items", {})
            for item_id, item in items.items():
                ref_key = f"#/facts/{fact_id}/items/{item_id}"
                self.items[ref_key] = item

        # Build dependency graph
        self.dependencies = {}
        self._build_dependency_graph()

        self.service_name = "NRML"
        self.service_provider = service_provider

    def _build_dependency_graph(self) -> None:
        """Build dependency graph by finding all $ref references in items"""
        for source_ref, item in self.items.items():
            # Find all references and categorize them
            all_references = self._find_references_recursive(item)
            target_reference = self._find_target_references(item)

            # Regular dependencies are all references minus target reference
            regular_dependencies = all_references - {target_reference} if target_reference else all_references

            if regular_dependencies:
                self.dependencies[source_ref] = regular_dependencies

            # Add inverted dependency for target reference
            if target_reference:
                # Invert the dependency: target depends on source
                if target_reference not in self.dependencies:
                    self.dependencies[target_reference] = set()
                self.dependencies[target_reference].add(source_ref)

    def _find_references_recursive(self, obj: Any) -> set[str]:
        """
        Recursively find all $ref references in an object structure.

        Args:
            obj: The object to search (dict, list, or primitive)

        Returns:
            Set of reference strings found
        """
        references = set()

        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "$ref" and isinstance(value, str):
                    # Found a reference
                    references.add(value)
                else:
                    # Recursively search nested objects
                    references.update(self._find_references_recursive(value))

        elif isinstance(obj, list):
            # Search each item in the list
            for item in obj:
                references.update(self._find_references_recursive(item))

        # For primitive types (str, int, bool, None), no references to find

        return references

    def _find_target_references(self, obj: Any) -> str | None:
        """
        Find the $ref reference that is specifically in a 'target' node.
        Returns immediately when target is found since there should be 0 or 1 targets per item.

        Args:
            obj: The object to search

        Returns:
            Target reference string if found, None otherwise
        """
        if isinstance(obj, dict):
            for key, value in obj.items():
                if key == "target":
                    # Found the target node, extract the reference from it and return immediately
                    references = self._find_references_recursive(value)
                    # Return the first (and should be only) reference found
                    return next(iter(references)) if references else None
                elif isinstance(value, dict | list):
                    # Continue searching in nested structures
                    target_ref = self._find_target_references(value)
                    if target_ref:
                        return target_ref

        elif isinstance(obj, list):
            # Search each item in the list
            for item in obj:
                target_ref = self._find_target_references(item)
                if target_ref:
                    return target_ref

        return None

    def evaluate(
        self,
        parameters: dict[str, Any] | None = None,
        overwrite_input: dict[str, Any] | None = None,
        sources: dict[str, pd.DataFrame] | None = None,
        calculation_date=None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> dict[str, Any]:
        """Evaluate rules using service context and sources"""
        parameters = parameters or {}

        items_to_process = [requested_output] if requested_output else []

        logger.debug(f"Evaluating rules for {self.service_name} {self.law} ({calculation_date} {requested_output})")

        claims = None
        if "BSN" in parameters:
            bsn = parameters["BSN"]
            claims = self.service_provider.claim_manager.get_claim_by_bsn_service_law(
                bsn, self.service_name, self.law, approved=approved
            )

        context = NrmlRuleContext.from_nrml_engine(
            self,
            parameters=parameters,
            sources=sources,
            overwrite_input=overwrite_input,
            calculation_date=calculation_date,
            claims=claims,
            approved=approved,
        )

        output_values = {}

        # TODO: determine output values and combine processing?
        for item in items_to_process:
            # TODO: process failures
            evaluation = context.item_evaluator.evaluate_item(item, context)

            self.print_process(evaluation)

            output_values[item] = {
                "description": item,  # TODO: create human readable description
                "process": evaluation,
                "value": evaluation.Value,
            }

        if not output_values:
            logger.warning(f"No output values computed for {calculation_date} {requested_output}")

        return {
            "input": context.resolved_paths,
            "output": output_values,
        }

    def print_process(self, evaluation):
        with logger.indent_block(f"{evaluation.Source} - ACTION: {evaluation.Action}"):
            logger.debug(f"RESULT: {evaluation.Value}")
            for child in evaluation.SubResults:
                self.print_process(child)



    def get_evaluation_order(self) -> list[str]:
        """Get topologically sorted evaluation order for all items"""
        # Simple topological sort using Kahn's algorithm
        in_degree = {item_id: 0 for item_id in self.items}

        # Calculate in-degrees
        for item_id, deps in self.dependencies.items():
            in_degree[item_id] = len(deps)

        # Initialize queue with items that have no dependencies
        queue = [item_id for item_id, degree in in_degree.items() if degree == 0]
        result = []

        while queue:
            current = queue.pop(0)
            result.append(current)

            # Reduce in-degree for dependent items
            for item_id, deps in self.dependencies.items():
                if current in deps:
                    in_degree[item_id] -= 1
                    if in_degree[item_id] == 0:
                        queue.append(item_id)

        return result

    def _get_all_target_references(self) -> dict[str, str]:
        """Get all target references mapped to their source items (target_ref -> item_id)"""
        target_refs = {}
        for item_id, item in self.items.items():
            ref = self._find_target_references(item)
            if ref:
                target_refs[ref] = item_id
        return target_refs
