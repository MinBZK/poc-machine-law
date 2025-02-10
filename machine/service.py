import logging
from dataclasses import dataclass
from typing import Dict, Any, Optional

import pandas as pd

from machine.events.application import ServiceCaseManager
from .engine import RulesEngine, AbstractServiceProvider
from .logging_config import IndentLogger
from .utils import RuleResolver

logger = IndentLogger(logging.getLogger('service'))


@dataclass
class RuleResult:
    """Result from rule execution containing output values and metadata"""
    output: Dict[str, Any]
    requirements_met: bool
    input: Dict[str, Any]
    rulespec_uuid: str

    @classmethod
    def from_engine_result(cls, result: Dict[str, Any], rulespec_uuid: str) -> 'RuleResult':
        """Create RuleResult from engine evaluation result"""
        return cls(
            output={
                name: data.get('value')
                for name, data in result.get('output', {}).items()
            },
            requirements_met=result.get('requirements_met', False),
            input=result.get('input', {}),
            rulespec_uuid=rulespec_uuid,
        )


class RuleService:
    """Interface for executing business rules for a specific service"""

    def __init__(self, service_name: str, services):
        """
        Initialize service for specific business rules

        Args:
            service_name: Name of the service (e.g. "TOESLAGEN")
            services: parent services
        """
        self.service_name = service_name
        self.services = services
        self.resolver = RuleResolver()
        self._engines: Dict[str, Dict[str, RulesEngine]] = {}
        self.source_dataframes: Dict[str, pd.DataFrame] = {}

    def _get_engine(self, law: str, reference_date: str) -> RulesEngine:
        """Get or create RulesEngine instance for given law and date"""
        if law not in self._engines:
            self._engines[law] = {}

        if reference_date not in self._engines[law]:
            spec = self.resolver.get_rule_spec(law, reference_date, service=self.service_name)
            if not spec:
                raise ValueError(
                    f"No rules found for law '{law}' at date '{reference_date}'"
                )
            if spec.get('service') != self.service_name:
                raise ValueError(
                    f"Rule spec service '{spec.get('service')}' does not match "
                    f"service '{self.service_name}'"
                )
            self._engines[law][reference_date] = RulesEngine(
                spec=spec,
                service_provider=self.services
            )

        return self._engines[law][reference_date]

    async def evaluate(
            self,
            law: str,
            reference_date: str,
            parameters: Dict[str, Any],
            overwrite_input: Optional[Dict[str, Any]] = None,
            requested_output: str = None
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
        )
        return RuleResult.from_engine_result(result, engine.spec.get('uuid'))

    def get_rule_info(self, law: str, reference_date: str) -> Optional[Dict[str, Any]]:
        """
        Get metadata about the rule that would be applied for given law and date

        Returns dict with uuid, name, valid_from if rule is found
        """
        try:
            rule = self.resolver.find_rule(law, reference_date)
            if rule:
                return {
                    'uuid': rule.uuid,
                    'name': rule.name,
                    'valid_from': rule.valid_from.strftime('%Y-%m-%d')
                }
        except ValueError:
            return None
        return None

    def set_source_dataframe(self, table: str, df: pd.DataFrame):
        """Set a source DataFrame"""
        self.source_dataframes[table] = df


class Services(AbstractServiceProvider):
    def __init__(self, reference_date: str):
        self.resolver = RuleResolver()
        self.services = {service: RuleService(service, self) for service in self.resolver.get_service_laws()}
        self.root_reference_date = reference_date
        self.manager = ServiceCaseManager(rules_engine=self)

    def get_discoverable_service_laws(self):
        return self.resolver.get_discoverable_service_laws()

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame):
        """Set a source DataFrame for a service"""
        self.services[service].set_source_dataframe(table, df)

    async def evaluate(self, service: str,
                       law: str,
                       parameters: Dict[str, Any],
                       reference_date: str = None,
                       overwrite_input: Optional[Dict[str, Any]] = None,
                       requested_output: str = None, ) -> RuleResult:
        reference_date = reference_date or self.root_reference_date
        with logger.indent_block(f"{service}: {law} ({reference_date} {parameters} {requested_output})",
                                 double_line=True):
            return await self.services[service].evaluate(
                law=law,
                reference_date=reference_date,
                parameters=parameters,
                overwrite_input=overwrite_input,
                requested_output=requested_output,
            )

    async def get_value(
            self,
            service: str,
            law: str,
            field: str,
            context: Dict[str, Any],
            overwrite_input: Dict[str, Any],
            reference_date: str) -> Any:
        # reference_date = self.root_reference_date
        result = await self.evaluate(service, law, context, reference_date, overwrite_input, requested_output=field)
        return result.output.get(field)
