from dataclasses import dataclass, field
from typing import Any

import pandas as pd

from machine.events.claim.aggregate import Claim

from ..context import RuleContext


@dataclass
class NrmlRuleContext(RuleContext):
    """NRML-specific rule evaluation context with additional NRML features"""

    # NRML-specific fields
    nrml_spec: dict[str, Any] = field(default_factory=dict)
    items: dict[str, dict[str, Any]] = field(default_factory=dict)
    dependency_graph: dict[str, set[str]] = field(default_factory=dict)
    evaluation_order: list[str] = field(default_factory=list)
    target_references: dict[str, str] = field(default_factory=dict)  # Maps target_ref -> item_id
    item_types: dict[str, str] = field(default_factory=dict)

    @classmethod
    def from_nrml_engine(
        cls,
        nrml_engine,
        parameters: dict[str, Any],
        sources: dict[str, pd.DataFrame] = None,
        overwrite_input: dict[str, Any] = None,
        calculation_date: str = None,
        claims: dict[str, Claim] = None,
        approved: bool = True
    ) -> "NrmlRuleContext":
        """Create NrmlRuleContext from NRML rules engine"""

        # TODO: check and remove duplicate properties
        return cls(
            definitions=nrml_engine.facts,
            service_provider="NRML",
            parameters=parameters,
            property_specs={},
            output_specs={},
            sources=sources or {},
            overwrite_input=overwrite_input or {},
            calculation_date=calculation_date,
            service_name=nrml_engine.service_name,
            claims=claims,
            approved=approved,
            # NRML-specific initialization
            nrml_spec=nrml_engine.spec,
            items=nrml_engine.items,
            dependency_graph=nrml_engine.dependencies,
            evaluation_order=nrml_engine.get_evaluation_order(),
            target_references=nrml_engine._get_all_target_references(),
            item_types={
                item_id: nrml_engine._get_item_type(nrml_engine.items[item_id]).value
                for item_id in nrml_engine.items
            }
        )

    def get_item_dependencies(self, item_id: str) -> set[str]:
        """Get dependencies for a specific NRML item"""
        return self.dependency_graph.get(item_id, set())

    def get_item(self, item_id: str) -> dict[str, Any] | None:
        """Get an NRML item by its ID"""
        return self.items.get(item_id)

    def get_all_items(self) -> dict[str, dict[str, Any]]:
        """Get all NRML items"""
        return self.items

    def get_item_type(self, item_id: str) -> str:
        """Get the type of a specific NRML item"""
        return self.item_types.get(item_id, "unknown")

    def is_target_reference(self, item_id: str, reference: str) -> bool:
        """Check if a reference is a target reference for an item"""
        return self.target_references.get(reference) == item_id

    def get_evaluation_dependencies(self, item_id: str) -> list[str]:
        """Get ordered list of dependencies that need to be evaluated first"""
        deps = self.get_item_dependencies(item_id)
        # Return dependencies in evaluation order
        return [dep for dep in self.evaluation_order if dep in deps]

    def add_target_reference(self, item_id: str, target_ref: str) -> None:
        """Add a target reference for an item"""
        self.target_references[target_ref] = item_id

    def get_target_source_item(self, target_ref: str) -> str | None:
        """Get the item ID that has the given target reference"""
        return self.target_references.get(target_ref)

    def get_item_target_reference(self, item_id: str) -> str | None:
        """Get the target reference for a given item ID"""
        for target_ref, source_item_id in self.target_references.items():
            if source_item_id == item_id:
                return target_ref
        return None

    def get_fact_item_by_reference(self, reference: str) -> dict[str, Any] | None:
        """Get fact item by JSON Pointer reference (e.g., #/facts/fact_id/items/item_id)"""
        if not reference.startswith("#/facts/"):
            return None

        try:
            # Parse reference: #/facts/{fact_id}/items/{item_id}
            parts = reference.split("/")
            if len(parts) >= 5 and parts[3] == "items":
                fact_id = parts[2]
                item_id = parts[4]

                fact = self.definitions.get(fact_id)
                if fact and "items" in fact:
                    return fact["items"].get(item_id)
        except (IndexError, KeyError):
            pass

        return None

    def resolve_target_value(self, target_reference: str) -> Any:
        """Resolve the value at a target reference"""
        item = self.get_fact_item_by_reference(target_reference)
        if item and "value" in item:
            return item["value"]
        return None
