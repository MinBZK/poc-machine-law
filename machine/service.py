from dataclasses import dataclass
from typing import Any

import pandas as pd
from eventsourcing.system import SingleThreadedRunner, System

from .events.case.application import CaseManager
from .events.case.processor import CaseProcessor
from .events.claim.application import ClaimManager
from .events.claim.processor import ClaimProcessor
from .utils import RuleResolver


@dataclass
class RuleResult:
    """Result from rule execution containing output values and metadata"""

    output: dict[str, Any]
    requirements_met: bool
    input: dict[str, Any]
    rulespec_uuid: str
    path: Any | None = None
    missing_required: bool = False


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
        self.source_dataframes: dict[str, pd.DataFrame] = {}

    def set_source_dataframe(self, table: str, df: pd.DataFrame) -> None:
        """Set a source DataFrame"""
        self.source_dataframes[table] = df


class Services:
    def __init__(self, reference_date: str, rules_engine: Any = None) -> None:
        self.resolver = RuleResolver()
        self.services = {service: RuleService(service, self) for service in self.resolver.get_service_laws()}
        self.root_reference_date = reference_date

        # The rules_engine passed into the case/claim managers is whatever object
        # exposes .evaluate(service, law, parameters, ...). When Services is wrapped
        # by RegelrechtServices, we route it back to the wrapper so the Rust engine
        # is used; otherwise self is used (legacy callers without an engine wrapper).
        engine_ref = rules_engine if rules_engine is not None else self

        class WrappedCaseProcessor(CaseProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

        class WrappedCaseManager(CaseManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

        class WrappedClaimManager(ClaimManager):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

        class WrappedClaimProcessor(ClaimProcessor):
            def __init__(self, env=None, **kwargs) -> None:
                super().__init__(rules_engine=engine_ref, env=env, **kwargs)

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

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN"):
        return self.resolver.get_discoverable_service_laws(discoverable_by)

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        """Set a source DataFrame for a service"""
        self.services[service].set_source_dataframe(table, df)

    def get_law(self, service: str, law: str, reference_date: str | None = None) -> dict[str, Any] | None:
        """Get the law specification for a given service and law.

        Args:
            service: Name of the service (e.g., "KVK")
            law: Name of the law (e.g., "machtigingenwet")
            reference_date: Reference date for rule version (YYYY-MM-DD)

        Returns:
            The law specification dictionary, or None if not found
        """
        reference_date = reference_date or self.root_reference_date
        return self.resolver.get_rule_spec(law, reference_date, service=service)
