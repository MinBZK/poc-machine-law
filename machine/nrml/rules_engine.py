from typing import Any

import pandas as pd

from ..context import logger
from .context import NrmlRuleContext


class NrmlRulesEngine:
    """Rules engine for evaluating business rules"""

    def __init__(self, spec: dict[str, Any], service_provider: Any | None = None) -> None:
        self.spec = spec
        self.facts = spec.get("facts", {})
        self.law = spec.get("metadata", {}).get("description", {})

        self.inputs = spec.get("inputs", [])
        self.outputs = self._extract_outputs_mapping(spec.get("outputs", []))

        self.items = self._extract_items_from_facts(self.facts)

        self.service_name = "NRML"
        self.service_provider = service_provider

    @staticmethod
    def _find_references_recursive(obj: Any) -> set[str]:
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
                    references.update(NrmlRulesEngine._find_references_recursive(value))

        elif isinstance(obj, list):
            # Search each item in the list
            for item in obj:
                references.update(NrmlRulesEngine._find_references_recursive(item))

        # For primitive types (str, int, bool, None), no references to find
        return references

    @staticmethod
    def _find_target_references(obj: Any) -> str | None:
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
                    references = NrmlRulesEngine._find_references_recursive(value)
                    # Return the first (and should be only) reference found
                    return next(iter(references)) if references else None
                elif isinstance(value, dict | list):
                    # Continue searching in nested structures
                    target_ref = NrmlRulesEngine._find_target_references(value)
                    if target_ref:
                        return target_ref

        elif isinstance(obj, list):
            # Search each item in the list
            for item in obj:
                target_ref = NrmlRulesEngine._find_target_references(item)
                if target_ref:
                    return target_ref

        return None

    @staticmethod
    def _extract_items_from_facts(facts: dict[str, Any]) -> dict[str, dict[str, Any]]:
        """Extract items from facts dictionary with JSON Pointer references as keys"""
        items = {}
        # Fill items dictionary with JSON Pointer references
        for fact_id, fact in facts.items():
            fact_items = fact.get("items", {})
            for item_id, item in fact_items.items():
                ref_key = f"#/facts/{fact_id}/items/{item_id}"
                items[ref_key] = item
        return items

    @staticmethod
    def _get_all_target_references(items: dict[str, dict[str, Any]]) -> dict[str, str]:
        """Get all target references mapped to their source items (target_ref -> item_id)"""
        target_refs = {}
        for item_id, item in items.items():
            ref = NrmlRulesEngine._find_target_references(item)
            if ref:
                target_refs[ref] = item_id
        return target_refs

    @staticmethod
    def _extract_inputs_mapping(inputs: list[dict[str, Any]]) -> dict[str, str]:
        """Extract inputs mapping from target.$ref to source"""
        inputs_mapping = {}
        for input_item in inputs:
            source = input_item.get("name")
            target = input_item.get("target", {})
            target_ref = target.get("$ref")

            if source and target_ref:
                inputs_mapping[target_ref] = source

        return inputs_mapping

    @staticmethod
    def _extract_outputs_mapping(outputs: list[dict[str, Any]]) -> dict[str, str]:
        """Extract outputs mapping from name to source.$ref"""
        outputs_mapping = {}
        for output_item in outputs:
            name = output_item.get("name")
            source = output_item.get("source", {})
            source_ref = source.get("$ref")

            if name and source_ref:
                outputs_mapping[name] = source_ref

        return outputs_mapping

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

        items_to_process = [requested_output] if self.outputs[requested_output] else []

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
            target_references=self._get_all_target_references(self.items),
            inputs=self._extract_inputs_mapping(self.inputs),
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