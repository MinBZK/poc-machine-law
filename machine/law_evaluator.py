"""
LawEvaluator - Orchestrates law evaluations without service routing.

This class replaces the Services/RuleService architecture with a simpler
context-based approach where all laws are evaluated through a single evaluator
that manages a shared DataContext.
"""

import logging
from typing import Any

from eventsourcing.system import SingleThreadedRunner, System

from .context import PathNode
from .data_context import DataContext
from .engine import RulesEngine
from .events.case.application import CaseManager
from .events.case.processor import CaseProcessor
from .events.claim.application import ClaimManager
from .events.claim.processor import ClaimProcessor
from .logging_config import IndentLogger
from .service import RuleResult
from .utils import RuleResolver

logger = IndentLogger(logging.getLogger("law_evaluator"))


class LawEvaluator:
    """
    Orchestrates law evaluations using a shared DataContext.

    This class manages:
    - Law registry (via RuleResolver)
    - Data context (shared across all evaluations)
    - Engine caching (one engine per law+date)
    - Event sourcing (case/claim managers)
    """

    def __init__(self, reference_date: str, data_context: DataContext | None = None) -> None:
        """
        Initialize the LawEvaluator.

        Args:
            reference_date: Default reference date for evaluations (YYYY-MM-DD)
            data_context: Optional DataContext to use. If None, creates a new one.
        """
        self.root_reference_date = reference_date
        self.resolver = RuleResolver()
        self.data_context = data_context or DataContext()

        # Cache engines by (law, reference_date)
        self._engines_cache: dict[tuple[str, str], RulesEngine] = {}

        # Impact cache for discoverable laws
        self._impact_cache = None

        # Setup event sourcing
        outer_self = self

        class WrappedCaseProcessor(CaseProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

        class WrappedCaseManager(CaseManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

        class WrappedClaimManager(ClaimManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

        class WrappedClaimProcessor(ClaimProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=outer_self, env=env, **kwargs)

        system = System(
            pipes=[[WrappedCaseManager, WrappedCaseProcessor], [WrappedClaimManager, WrappedClaimProcessor]]
        )

        self.runner = SingleThreadedRunner(system)
        self.runner.start()

        self.case_manager = self.runner.get(WrappedCaseManager)
        self.claim_manager = self.runner.get(WrappedClaimManager)

        self.claim_manager._case_manager = self.case_manager

    def __exit__(self):
        """Cleanup when context manager exits."""
        self.runner.stop()

    def _get_engine(self, law: str, reference_date: str) -> RulesEngine:
        """
        Get or create RulesEngine for a law at a specific date.

        Args:
            law: Law identifier (e.g., "zorgtoeslagwet")
            reference_date: Reference date (YYYY-MM-DD)

        Returns:
            RulesEngine instance

        Raises:
            ValueError: If no rules found for the law at the reference date
        """
        cache_key = (law, reference_date)

        if cache_key in self._engines_cache:
            return self._engines_cache[cache_key]

        # Get rule specification (no service parameter needed in new architecture)
        spec = self.resolver.get_rule_spec(law, reference_date, service=None)
        if not spec:
            raise ValueError(f"No rules found for law '{law}' at date '{reference_date}'")

        # Create engine with reference to this evaluator
        engine = RulesEngine(spec=spec, law_evaluator=self)
        self._engines_cache[cache_key] = engine

        logger.debug(f"Created engine for {law} at {reference_date}")
        return engine

    def evaluate_law(
        self,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        overwrite_definitions: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Evaluate a law with given parameters.

        Args:
            law: Law identifier (e.g., "zorgtoeslagwet")
            parameters: Input parameters (e.g., {"BSN": "123456789"})
            reference_date: Reference date for evaluation (default: root_reference_date)
            overwrite_input: Optional input overrides for testing
            overwrite_definitions: Optional definition overrides for testing
            requested_output: Optional specific output field to compute
            approved: Whether user has approved data access

        Returns:
            RuleResult with outputs and metadata
        """
        reference_date = reference_date or self.root_reference_date

        with logger.indent_block(
            f"{law} ({reference_date} {parameters} {requested_output})",
            double_line=True,
        ):
            # Get engine for this law
            engine = self._get_engine(law, reference_date)

            # Evaluate using shared data context
            result = engine.evaluate(
                parameters=parameters,
                reference_date=reference_date,
                overwrite_input=overwrite_input,
                overwrite_definitions=overwrite_definitions,
                requested_output=requested_output,
                approved=approved,
            )

            # Import RuleResult here to avoid circular dependency
            from machine.service import RuleResult
            return RuleResult.from_engine_result(result, engine.spec.get("uuid"))

    # Backward compatibility methods for event sourcing integration
    def evaluate(
        self,
        service: str,  # Ignored in new architecture
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        overwrite_definitions: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Backward-compatible evaluate method (ignores service parameter).

        This exists for compatibility with event sourcing code that still
        passes a service parameter. The service parameter is ignored.

        Args:
            service: IGNORED - kept for backward compatibility
            law: Law identifier
            parameters: Input parameters
            reference_date: Reference date for evaluation
            overwrite_input: Optional input overrides
            overwrite_definitions: Optional definition overrides
            requested_output: Optional specific output field
            approved: Whether user has approved data access

        Returns:
            RuleResult with outputs and metadata
        """
        if service:
            logger.debug(f"Service parameter '{service}' ignored (deprecated)")

        return self.evaluate_law(
            law=law,
            parameters=parameters,
            reference_date=reference_date,
            overwrite_input=overwrite_input,
            overwrite_definitions=overwrite_definitions,
            requested_output=requested_output,
            approved=approved,
        )

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN"):
        """
        Get discoverable laws (backward compatibility).

        Args:
            discoverable_by: Who can discover the laws ("CITIZEN" or "BUSINESS")

        Returns:
            Dict of laws by service (now just returns laws without service grouping)
        """
        # For backward compatibility, return a dict with a single "ALL" service
        discoverable_laws = set()
        for rule in self.resolver.rules:
            if rule.discoverable == discoverable_by:
                discoverable_laws.add(rule.law)

        return {"ALL": discoverable_laws}

    def get_sorted_discoverable_service_laws(self, bsn):
        """
        Get sorted discoverable laws (backward compatibility).

        Args:
            bsn: BSN to calculate impact for

        Returns:
            List of law info dicts sorted by impact
        """
        discoverable_laws_by_service = self.get_discoverable_service_laws("CITIZEN")

        law_infos = []
        for service, laws in discoverable_laws_by_service.items():
            for law in laws:
                # Find rule spec for this law
                rule = next((r for r in self.resolver.rules if r.law == law), None)
                if not rule:
                    continue

                law_info = {
                    "service": service,  # Will be "ALL"
                    "law": law,
                    "name": rule.name,
                    "uuid": rule.uuid,
                }

                # Calculate impact if this law has an impact definition
                try:
                    spec = self.resolver.get_rule_spec(law, self.root_reference_date)
                    if "impact" in spec.get("properties", {}).get("definitions", {}):
                        result = self.evaluate_law(
                            law=law,
                            parameters={"BSN": bsn},
                            reference_date=self.root_reference_date,
                            requested_output="impact",
                        )
                        law_info["impact_value"] = result.output.get("impact", 0)
                    else:
                        law_info["impact_value"] = 0
                except Exception as e:
                    logger.warning(f"Failed to calculate impact for {law}: {str(e)}")
                    law_info["impact_value"] = 0

                law_infos.append(law_info)

        # Sort by impact (descending), then by name
        return sorted(law_infos, key=lambda x: (-x.get("impact_value", 0), x["law"]))

    def set_source_dataframe(self, source: str, table: str, df) -> None:
        """
        Set a source DataFrame in the data context.

        Args:
            source: Source name (e.g., "toeslagen", "brp")
            table: Table name within the source
            df: pandas DataFrame
        """
        self.data_context.add_source(source, table, df)

    def apply_rules(self, event) -> None:
        """
        Apply rules in response to events.

        Args:
            event: Event to process
        """
        for rule in self.resolver.rules:
            applies = rule.properties.get("applies", [])

            for apply in applies:
                if self._matches_event(event, apply):
                    aggregate_id = str(event.originator_id)
                    aggregate = self.case_manager.get_case_by_id(aggregate_id)
                    parameters = {apply["name"]: aggregate}
                    result = self.evaluate_law(rule.law, parameters)

                    # Apply updates back to aggregate
                    for update in apply.get("update", []):
                        mapping = {
                            name: result.output.get(value[1:])  # Strip $ from value
                            for name, value in update["mapping"].items()
                        }
                        # Apply directly on the event via method
                        method = getattr(self.case_manager, update["method"])
                        method(aggregate_id, **mapping)

    def _matches_event(self, event, apply_config):
        """Check if an event matches the apply configuration."""
        event_type = type(event).__name__
        return apply_config.get("event") == event_type

    @staticmethod
    def extract_value_tree(root: PathNode):
        """
        Extract value tree from path nodes (for tracing).

        Args:
            root: Root PathNode

        Returns:
            Flattened dict of value resolutions
        """
        flattened = {}
        stack = [(root, None)]

        while stack:
            node, parent = stack.pop()

            if not isinstance(node, PathNode):
                continue

            path = node.details.get("path")
            if isinstance(path, str) and path.startswith("$"):
                path = path[1:]

            # Handle resolve nodes
            if (
                node.type == "resolve"
                and node.resolve_type in {"EXTERNAL", "SOURCE", "CLAIM", "NONE"}
                and path
                and isinstance(path, str)
            ):
                resolve_entry = {"result": node.result, "required": node.required, "details": node.details}

                if parent and path not in parent.setdefault("children", {}):
                    parent.setdefault("children", {})[path] = resolve_entry
                elif path not in flattened:
                    flattened[path] = resolve_entry

            # Handle external_evaluation nodes (renamed from service_evaluation)
            elif node.type == "external_evaluation" and path and isinstance(path, str):
                external_entry = {
                    "result": node.result,
                    "required": node.required,
                    "law": node.details.get("law"),
                    "children": {},
                    "details": node.details,
                }

                if parent:
                    parent.setdefault("children", {})[path] = external_entry
                else:
                    flattened[path] = external_entry

                # Prepare to process children with this external_evaluation as parent
                for child in reversed(node.children):
                    stack.append((child, external_entry))
                continue

            # Add children to the stack for further processing
            for child in reversed(node.children):
                stack.append((child, parent))

        return flattened
