import logging
from dataclasses import dataclass
from typing import Any

import pandas as pd
from eventsourcing.system import SingleThreadedRunner, System

from .context import PathNode
from .engine import RulesEngine
from .events.case.application import CaseManager
from .events.case.processor import CaseProcessor
from .events.claim.application import ClaimManager
from .events.claim.processor import ClaimProcessor
from .logging_config import IndentLogger
from .utils import RuleResolver

logger = IndentLogger(logging.getLogger("service"))


@dataclass
class RuleResult:
    """Result from rule execution containing output values and metadata"""

    output: dict[str, Any]
    requirements_met: bool
    input: dict[str, Any]
    rulespec_uuid: str
    path: PathNode | None = None

    @classmethod
    def from_engine_result(cls, result: dict[str, Any], rulespec_uuid: str) -> "RuleResult":
        """Create RuleResult from engine evaluation result"""
        return cls(
            output={name: data.get("value") for name, data in result.get("output", {}).items()},
            requirements_met=result.get("requirements_met", False),
            input=result.get("input", {}),
            rulespec_uuid=rulespec_uuid,
            path=result.get("path"),
        )


class RuleService:
    """Interface for executing business rules for a specific service"""

    def __init__(self, service_name: str, services) -> None:
        """
        Initialize service for specific business rules

        Args:
            service_name: Name of the service (e.g. "TOESLAGEN")
            services: parent services
        """
        self.service_name = service_name
        self.services = services
        self.resolver = RuleResolver()
        self._engines: dict[str, dict[str, RulesEngine]] = {}
        self.source_dataframes: dict[str, pd.DataFrame] = {}

    def _get_engine(self, law: str, reference_date: str) -> RulesEngine:
        """Get or create RulesEngine instance for given law and date"""
        if law not in self._engines:
            self._engines[law] = {}

        if reference_date not in self._engines[law]:
            spec = self.resolver.get_rule_spec(law, reference_date, service=self.service_name)
            if not spec:
                raise ValueError(f"No rules found for law '{law}' at date '{reference_date}'")
            if spec.get("service") != self.service_name:
                raise ValueError(
                    f"Rule spec service '{spec.get('service')}' does not match service '{self.service_name}'"
                )
            self._engines[law][reference_date] = RulesEngine(spec=spec, service_provider=self.services)

        return self._engines[law][reference_date]

    async def evaluate(
        self,
        law: str,
        reference_date: str,
        parameters: dict[str, Any],
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Evaluate rules for given law and reference date

        Args:
            law: Name of the law (e.g. "zorgtoeslagwet")
            reference_date: Reference date for rule version (YYYY-MM-DD)
            parameters: Context data for service provider
            overwrite_input: Optional overrides for input values
            requested_output: Optional specific output field to calculate

        Returns:
            RuleResult containing outputs and metadata
        """
        engine = self._get_engine(law, reference_date)
        result = await engine.evaluate(
            parameters=parameters,
            overwrite_input=overwrite_input,
            sources=self.source_dataframes,
            calculation_date=reference_date,
            requested_output=requested_output,
            approved=approved,
        )
        return RuleResult.from_engine_result(result, engine.spec.get("uuid"))

    def get_rule_info(self, law: str, reference_date: str) -> dict[str, Any] | None:
        """
        Get metadata about the rule that would be applied for given law and date

        Returns dict with uuid, name, valid_from if rule is found
        """
        try:
            rule = self.resolver.find_rule(law, reference_date)
            if rule:
                return {
                    "uuid": rule.uuid,
                    "name": rule.name,
                    "valid_from": rule.valid_from.strftime("%Y-%m-%d"),
                }
        except ValueError:
            return None
        return None

    def set_source_dataframe(self, table: str, df: pd.DataFrame) -> None:
        """Set a source DataFrame"""
        self.source_dataframes[table] = df


class Services:
    def __init__(self, reference_date: str) -> None:
        self.resolver = RuleResolver()
        self.services = {service: RuleService(service, self) for service in self.resolver.get_service_laws()}
        self.root_reference_date = reference_date

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
        self.runner.stop()

    @staticmethod
    def extract_value_tree(root):
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
                resolve_entry = {
                    "result": node.result,
                    "required": node.required,
                }

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

    def get_discoverable_service_laws(self):
        return self.resolver.get_discoverable_service_laws()

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        """Set a source DataFrame for a service"""
        self.services[service].set_source_dataframe(table, df)

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
        reference_date = reference_date or self.root_reference_date
        with logger.indent_block(
            f"{service}: {law} ({reference_date} {parameters} {requested_output})",
            double_line=True,
        ):
            return await self.services[service].evaluate(
                law=law,
                reference_date=reference_date,
                parameters=parameters,
                overwrite_input=overwrite_input,
                requested_output=requested_output,
                approved=approved,
            )

    async def apply_rules(self, event) -> None:
        for rule in self.resolver.rules:
            applies = rule.properties.get("applies", [])

            for apply in applies:
                if self._matches_event(event, apply):
                    aggregate_id = str(event.originator_id)
                    aggregate = self.case_manager.get_case_by_id(aggregate_id)
                    parameters = {apply["name"]: aggregate}
                    result = await self.evaluate(rule.service, rule.law, parameters)

                    # Apply updates back to aggregate
                    for update in apply.get("update", []):
                        mapping = {
                            name: result.output.get(value[1:])  # Strip $ from value
                            for name, value in update["mapping"].items()
                        }
                        # Apply directly on the event via method
                        method = getattr(self.case_manager, update["method"])
                        method(aggregate_id, **mapping)

    @staticmethod
    def _matches_event(event, applies) -> bool:
        """Check if event matches the applies spec"""
        if applies["aggregate"] != event.__class__.__qualname__.split(".")[0]:
            return False

        event_type = event.__class__.__name__

        for event_spec in applies["events"]:
            if event_spec["type"].lower() == event_type.lower():
                for key, filter_value in event_spec.get("filter", {}).items():
                    value = getattr(event, key)
                    if value != filter_value:
                        return False
                return True
        return False
