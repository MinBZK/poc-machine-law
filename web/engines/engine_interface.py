from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


@dataclass
class PathNode:
    """Node for tracking evaluation path"""

    type: str
    name: str
    result: Any
    resolve_type: str = None
    required: bool = False
    details: dict[str, Any] = field(default_factory=dict)
    children: list["PathNode"] = field(default_factory=list)


@dataclass
class RuleResult:
    """Result from rule execution containing output values and metadata"""

    output: dict[str, Any]
    requirements_met: bool
    input: dict[str, Any]
    rulespec_uuid: str
    path: PathNode | None = None
    missing_required: bool = False


class EngineInterface(ABC):
    """
    Interface for machine law evaluation services.
    Abstracts the underlying implementation (Python or Go).
    """

    @abstractmethod
    async def get_rule_spec(self, law: str, reference_date: str, service: str) -> dict[str, Any]:
        """
        Get the rule specification for a specific law.

        Args:
            law: Law identifier
            reference_date: Reference date for rule version (YYYY-MM-DD)
            service: Service provider code (e.g., "TOESLAGEN")

        Returns:
            Dictionary containing the rule specification
        """

    @abstractmethod
    async def get_profile_data(self, bsn: str) -> dict[str, Any]:
        """
        Get profile data for a specific BSN.

        Args:
            bsn: BSN identifier for the individual

        Returns:
            Dictionary containing profile data or None if not found
        """

    @abstractmethod
    async def get_all_profiles(self) -> dict[str, dict[str, Any]]:
        """
        Get all available profiles.

        Returns:
            Dictionary mapping BSNs to profile data
        """

    @abstractmethod
    async def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Evaluate rules for given law and reference date.

        Args:
            service: Service provider code (e.g., "TOESLAGEN")
            law: Name of the law (e.g., "zorgtoeslagwet")
            parameters: Context data for service provider
            reference_date: Reference date for rule version (YYYY-MM-DD)
            overwrite_input: Optional overrides for input values
            requested_output: Optional specific output field to calculate
            approved: Whether this evaluation is for an approved claim

        Returns:
            Dictionary containing evaluation results
        """

    @abstractmethod
    async def get_discoverable_service_laws(self, discoverable_by="CITIZEN") -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens.

        Returns:
            Dictionary mapping service names to lists of law names
        """

    @abstractmethod
    async def get_sorted_discoverable_service_laws(self, bsn: str) -> list[dict[str, Any]]:
        """
        Return laws discoverable by citizens, sorted by impact for this specific person.

        Args:
            bsn: BSN identifier for the individual

        Returns:
            List of dictionaries containing service, law, and impact information
        """

    @staticmethod
    def extract_value_tree(root: PathNode):
        flattened = {}
        stack = [(root, None)]

        while stack:
            node, service_parent = stack.pop()
            if not isinstance(node, PathNode):
                continue

            path = node.details.get("path")
            if isinstance(path, str) and path.startswith("$"):
                path = path[1:]

            # Handle resolve nodes
            if (
                node.type == "resolve"
                and node.resolve_type in {"SERVICE", "SOURCE", "CLAIM", "NONE"}
                and path
                and isinstance(path, str)
            ):
                resolve_entry = {"result": node.result, "required": node.required, "details": node.details}

                if service_parent and path not in service_parent.setdefault("children", {}):
                    service_parent.setdefault("children", {})[path] = resolve_entry
                elif path not in flattened:
                    flattened[path] = resolve_entry

            # Handle service_evaluation nodes
            elif node.type == "service_evaluation" and path and isinstance(path, str):
                service_entry = {
                    "result": node.result,
                    "required": node.required,
                    "service": node.details.get("service"),
                    "law": node.details.get("law"),
                    "children": {},
                    "details": node.details,
                }

                if service_parent:
                    service_parent.setdefault("children", {})[path] = service_entry
                else:
                    flattened[path] = service_entry

                # Prepare to process children with this service_evaluation as parent
                for child in reversed(node.children):
                    stack.append((child, service_entry))

                continue

            # Add children to the stack for further processing
            for child in reversed(node.children):
                stack.append((child, service_parent))

        return flattened
