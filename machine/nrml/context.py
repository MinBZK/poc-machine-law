from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from machine.events.claim.aggregate import Claim
from ..context import PathNode


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
    item_evaluator: Any = None  # Forward reference to avoid circular imports

    @classmethod
    def from_nrml_engine(
        cls,
        nrml_engine,
        parameters: dict[str, Any],
        sources: dict[str, pd.DataFrame] = None,
        overwrite_input: dict[str, Any] = None,
        calculation_date: str = None,
        claims: dict[str, Claim] = None,
        approved: bool = True,
    ) -> "NrmlRuleContext":
        """Create NrmlRuleContext from NRML rules engine"""

        # Import here to avoid circular imports
        from .item_evaluator import NrmlItemEvaluator

        context = cls(
            calculation_date=calculation_date,
            parameters=parameters,
            nrml_spec=nrml_engine.spec,
            items=nrml_engine.items,
            target_references=nrml_engine._get_all_target_references(),
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

    def get_target_source_item(self, target_ref: str) -> str | None:
        """Get the item ID that has the given target reference"""
        return self.target_references.get(target_ref)
