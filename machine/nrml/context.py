from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from machine.events.claim.aggregate import Claim

from ..context import PathNode
from .evaluation_result import EvaluationResult


@dataclass
class NrmlRuleContext:
    """NRML-specific rule evaluation context"""

    # Core fields actually used by NRML evaluators
    calculation_date: str | None = None
    parameters: dict[str, Any] = field(default_factory=dict)
    resolved_paths: dict[str, Any] = field(default_factory=dict)
    path: list[PathNode] = field(default_factory=list)

    # NRML-specific fields
    nrml_spec: dict[str, Any] = field(default_factory=dict)
    items: dict[str, dict[str, Any]] = field(default_factory=dict)
    target_references: dict[str, str] = field(default_factory=dict)  # Maps target_ref -> item_id
    inputs: dict[str, str] = field(default_factory=dict)  # Maps target.$ref -> source
    includes: dict[str, dict[str, Any]] = field(default_factory=dict)  # Maps target.$ref -> include config
    item_evaluator: Any = None  # Forward reference to avoid circular imports
    evaluation_results: dict[str, EvaluationResult] = field(default_factory=dict)
    language: str = "nl"
    value_providers: list[Any] = field(default_factory=list)
    service_provider: Any = None  # Service provider for evaluating includes

    def get_value_provider_for(self, name: str) -> Any | None:
        """Get the first value provider that can provide a value for the given name"""
        for provider in self.value_providers:
            if provider.can_provide_value(name):
                return provider
        return None

    @classmethod
    def from_nrml_engine(
        cls,
        nrml_engine,
        parameters: dict[str, Any],
        target_references: dict[str, str],
        inputs: dict[str, str],
        includes: dict[str, dict[str, Any]] = None,
        sources: dict[str, pd.DataFrame] = None,
        overwrite_input: dict[str, Any] = None,
        calculation_date: str = None,
        claims: dict[str, Claim] = None,
        approved: bool = True,
        table_value_providers: list[Any] = None,
        service_provider: Any = None,
    ) -> "NrmlRuleContext":
        """Create NrmlRuleContext from NRML rules engine"""

        # Import here to avoid circular imports
        from .item_evaluator import NrmlItemEvaluator

        context = cls(
            calculation_date=calculation_date,
            parameters=parameters,
            nrml_spec=nrml_engine.spec,
            items=nrml_engine.items,
            target_references=target_references,
            inputs=inputs,
            includes=includes or {},
            value_providers=table_value_providers or [],
            service_provider=service_provider,
        )

        # Create and store the item evaluator in context
        context.item_evaluator = NrmlItemEvaluator()

        return context

    def add_to_path(self, node: PathNode) -> None:
        """Add node to evaluation path"""
        if self.path:
            self.path[-1].children.append(node)
        self.path.append(node)

    def pop_path(self) -> None:
        """Remove last node from path"""
        if self.path:
            self.path.pop()

    def get_evaluation_result(self, item_key: str) -> EvaluationResult | None:
        """Get the evaluation result for an item key, or None if it doesn't exist"""
        return self.evaluation_results.get(item_key)

    def add_evaluation_result(self, item_key: str, result: EvaluationResult) -> None:
        """Add an evaluation result for an item key"""
        if item_key in self.evaluation_results:
            raise ValueError(f"Evaluation result for item '{item_key}' already exists")
        self.evaluation_results[item_key] = result

    def get_target_source_item(self, target_ref: str) -> str | None:
        """Get the item ID that has the given target reference"""
        return self.target_references.get(target_ref)

    def get_parameter_value(self, input_source: str) -> str | None:
        """Get the parameter name for the given target reference"""
        return self.parameters.get(input_source)

    def get_input_source(self, target_ref: str) -> str | None:
        """Get the input source for the given target reference"""
        return self.inputs.get(target_ref)

    def get_include_for_target(self, target_ref: str) -> dict[str, Any] | None:
        """Get the include configuration for the given target reference"""
        return self.includes.get(target_ref)
