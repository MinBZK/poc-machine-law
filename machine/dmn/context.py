"""
DMN execution context - tracks state during decision evaluation.
"""
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

from machine.context import PathNode


@dataclass
class DMNContext:
    """
    Execution context for DMN decision evaluation.

    Maintains state during the evaluation of a DMN model, including:
    - Input parameters
    - Evaluated decision results (cache)
    - BKM results (cache)
    - Execution trace for transparency
    """

    # Input parameters provided by caller
    parameters: Dict[str, Any] = field(default_factory=dict)

    # Cache of evaluated decisions (decision_id -> result)
    decision_results: Dict[str, Any] = field(default_factory=dict)

    # Cache of BKM invocations (bkm_id -> result)
    bkm_results: Dict[str, Any] = field(default_factory=dict)

    # Execution trace tree
    path: Optional[PathNode] = None

    # Current path node being built
    current_path: Optional[PathNode] = None

    # Errors encountered during evaluation
    errors: list[str] = field(default_factory=list)

    def add_decision_result(self, decision_id: str, result: Any) -> None:
        """Cache the result of a decision evaluation."""
        self.decision_results[decision_id] = result

    def get_decision_result(self, decision_id: str) -> Optional[Any]:
        """Get cached decision result if available."""
        return self.decision_results.get(decision_id)

    def has_decision_result(self, decision_id: str) -> bool:
        """Check if a decision has been evaluated."""
        return decision_id in self.decision_results

    def add_bkm_result(self, bkm_id: str, result: Any) -> None:
        """Cache the result of a BKM invocation."""
        self.bkm_results[bkm_id] = result

    def get_bkm_result(self, bkm_id: str) -> Optional[Any]:
        """Get cached BKM result if available."""
        return self.bkm_results.get(bkm_id)

    def add_error(self, error: str) -> None:
        """Add an error to the error list."""
        self.errors.append(error)

    def get_all_values(self) -> Dict[str, Any]:
        """Get all available values (parameters + decision results)."""
        all_values = {}
        all_values.update(self.parameters)
        all_values.update(self.decision_results)
        return all_values

    def create_child_path(self, node_type: str, details: Optional[Dict[str, Any]] = None) -> PathNode:
        """Create a child path node for tracing."""
        child = PathNode(
            type=node_type,
            result=None,
            details=details or {},
            children=[],
        )

        if self.current_path is not None:
            self.current_path.children.append(child)
        elif self.path is None:
            self.path = child

        return child

    def push_path(self, node: PathNode) -> None:
        """Push a new path node onto the stack."""
        old_path = self.current_path
        self.current_path = node

        if old_path is not None:
            old_path.children.append(node)
        elif self.path is None:
            self.path = node

    def pop_path(self, result: Any) -> None:
        """Pop the current path node and set its result."""
        if self.current_path is not None:
            self.current_path.result = result
