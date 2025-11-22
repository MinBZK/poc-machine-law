import logging
from collections import defaultdict
from datetime import date, datetime
from typing import Any

import httpx
import pandas as pd

from web.config_loader import ServiceRoutingConfig

from ..engine_interface import EngineInterface, PathNode, RuleResult
from .machine_client.law_as_code_client import Client

logger = logging.getLogger(__name__)
from .machine_client.law_as_code_client.api.data_frames import set_source_data_frame
from .machine_client.law_as_code_client.api.law import evaluate, rule_spec_get, service_laws_discoverable_list
from .machine_client.law_as_code_client.api.profile import profile_get, profile_list
from .machine_client.law_as_code_client.models import (
    DataFrame,
    Evaluate,
    EvaluateBody,
    EvaluateInput,
    EvaluateParameters,
    Profile,
    ProfileSources,
    SetSourceDataFrameBody,
)
from .machine_client.law_as_code_client.models import (
    PathNode as ApiPathNode,
)
from .machine_client.law_as_code_client.models import (
    ResponseEvaluateSchema as ApiRuleResult,
)
from .machine_client.law_as_code_client.types import UNSET


class MachineService(EngineInterface):
    """
    Implementation of EngineInterface using HTTP calls to the Go backend service.
    Supports service-based routing when enabled in configuration.
    """

    def __init__(
        self, base_url: str = "http://localhost:8081/v0", service_routing_config: ServiceRoutingConfig | None = None
    ):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)
        self.service_routing_enabled = False
        self.service_routes = {}
        self._service_routing_config = service_routing_config

        if service_routing_config and service_routing_config.enabled:
            self.service_routing_enabled = True
            self.service_routes = service_routing_config.services

    def _get_base_url_for_service(self, service: str) -> str:
        """
        Get the appropriate base URL for a service.
        If service routing is enabled and service has a specific route, use that.
        Otherwise, use the default base URL.
        """
        if self.service_routing_enabled and service in self.service_routes:
            url = self.service_routes[service].domain
            return url

        return self.base_url

    def get_rule_spec(self, law: str, reference_date: str, service: str) -> dict[str, Any]:
        """
        Get the rule specification for a specific law.

        Args:
            law: Law identifier
            reference_date: Reference date for rule version (YYYY-MM-DD)
            service: Service provider code (e.g., "TOESLAGEN")

        Returns:
            Dictionary containing the rule specification
        """

        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)

        client = Client(base_url=service_base_url)

        reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

        try:
            with client as client:
                response = rule_spec_get.sync_detailed(
                    client=client, service=service, law=law, reference_date=reference_date
                )

                if response.status_code < 200 or response.status_code >= 300:
                    logger.error(f"[MachineService] Non-2xx status code: {response.status_code}")

                content = response.parsed
                return content.data.to_dict()
        except Exception as e:
            logger.error(f"[MachineService] EXCEPTION in get_rule_spec(): {type(e).__name__}: {e}", exc_info=True)
            logger.error(f"[MachineService] Request was to: {service_base_url} with service={service}, law={law}")
            raise

    def evaluate(
        self,
        service: str,
        law: str,
        parameters: dict[str, Any],
        reference_date: str | None = None,
        effective_date: str | None = None,
        overwrite_input: dict[str, Any] | None = None,
        requested_output: str | None = None,
        approved: bool = False,
    ) -> RuleResult:
        """
        Evaluate rules using HTTP calls to the Go backend service.
        """

        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)

        client = Client(base_url=service_base_url)

        data = Evaluate(
            service=service, law=law, parameters=EvaluateParameters().from_dict(parameters), approved=approved
        )

        if reference_date:
            data.reference_date = datetime.strptime(reference_date, "%Y-%m-%d").date()

        if effective_date:
            data.effective_date = datetime.strptime(effective_date, "%Y-%m-%d").date()

        if overwrite_input:
            data.input_ = EvaluateInput.from_dict(overwrite_input)

        if requested_output:
            data.output = requested_output

        body = EvaluateBody(data=data)

        with client as client:
            response = evaluate.sync_detailed(client=client, body=body)

            return to_rule_result(response.parsed.data)

    def get_discoverable_service_laws(self, discoverable_by="CITIZEN") -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens using HTTP calls to the Go backend service.

        Filters laws based on feature flags if they exist.
        """
        from web.feature_flags import FeatureFlags

        result = defaultdict(set)

        # When service routing is enabled, query all configured services
        if self.service_routing_enabled and self.service_routes:
            for service_name, service_config in self.service_routes.items():
                client = Client(base_url=service_config.domain)
                with client as client:
                    response = service_laws_discoverable_list.sync_detailed(
                        client=client, discoverable_by=discoverable_by
                    )
                    content = response.parsed

                    for item in content.data:
                        for law in item.laws:
                            # Check if the law is enabled in feature flags
                            # If flag doesn't exist, law is enabled by default
                            if FeatureFlags.is_law_enabled(item.name, law.name):
                                result[item.name].add(law.name)

                    logger.debug(f"[MachineService] Found {len(content.data)} services with laws from {service_name}")

            logger.debug(f"[MachineService] Total discoverable services: {len(result)}")
            return result

        # Default behavior: query single base_url
        client = Client(base_url=self.base_url)

        with client as client:
            response = service_laws_discoverable_list.sync_detailed(client=client, discoverable_by=discoverable_by)
            content = response.parsed

            for item in content.data:
                for law in item.laws:
                    # Check if the law is enabled in feature flags
                    # If flag doesn't exist, law is enabled by default
                    if FeatureFlags.is_law_enabled(item.name, law.name):
                        result[item.name].add(law.name)

            return result

    def get_all_profiles(self, effective_date: date | None = None) -> dict[str, dict[str, Any]]:
        if effective_date is None:
            effective_date = UNSET

        # When service routing is enabled and configured to query all services
        service_routing_config = getattr(self, "_service_routing_config", None)
        query_all = (
            service_routing_config and service_routing_config.query_all_for_profiles
            if service_routing_config
            else False
        )

        if self.service_routing_enabled and self.service_routes and query_all:
            result = {}

            for service_name, service_config in self.service_routes.items():
                logger.debug(
                    f"[MachineService] Querying profiles from service: {service_name} at {service_config.domain}"
                )
                client = Client(base_url=service_config.domain)
                with client as client:
                    response = profile_list.sync_detailed(client=client, effective_date=effective_date)
                    content = response.parsed

                    for item in content.data:
                        # Use BSN as key - will overwrite if same profile exists in multiple services
                        result[item.bsn] = profile_transform(item)

                    logger.debug(f"[MachineService] Found {len(content.data)} profiles from {service_name}")

            logger.debug(f"[MachineService] Total unique profiles found: {len(result)}")
            return result

        # Default behavior: query single base_url
        logger.debug(f"[MachineService] get_all_profiles using base_url: {self.base_url}")
        client = Client(base_url=self.base_url)

        with client as client:
            response = profile_list.sync_detailed(client=client, effective_date=effective_date)
            content = response.parsed

            result = {}
            for item in content.data:
                result[item.bsn] = profile_transform(item)

            return result

    def get_profile_data(self, bsn: str, effective_date: date | None = None) -> dict[str, Any] | None:
        if effective_date is None:
            effective_date = UNSET

        # Always use default base_url for profile data (profiles are centralized)
        # Service routing does not apply to individual profile lookups
        client = Client(base_url=self.base_url)

        with client as client:
            response = profile_get.sync_detailed(client=client, bsn=bsn, effective_date=effective_date)
            content = response.parsed

            # Handle different response types
            if response.status_code == 200:
                return profile_transform(content.data)
            elif response.status_code == 404:
                logger.warning(f"[MachineService] Profile not found for BSN: {bsn}")
                return None
            else:
                logger.error(f"[MachineService] Error getting profile for BSN {bsn}: Status {response.status_code}")
                return None

    def set_source_dataframe(self, service: str, table: str, df: pd.DataFrame) -> None:
        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)
        client = Client(base_url=service_base_url)

        data = DataFrame(
            service=service,
            table=table,
            data=df.to_dict("records"),
        )

        body = SetSourceDataFrameBody(data=data)

        with client as client:
            set_source_data_frame.sync_detailed(client=client, body=body)

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)


def profile_transform(profile: Profile) -> dict[str, Any]:
    p = profile.to_dict()
    p["sources"] = source_transform(profile.sources)

    return p


def source_transform(sources: ProfileSources) -> dict[str, Any]:
    s = sources.to_dict()
    return s


def to_rule_result(result: ApiRuleResult) -> RuleResult:
    return RuleResult(
        input=result.input_.to_dict(),
        output=result.output.to_dict(),
        requirements_met=result.requirements_met,
        missing_required=result.missing_required,
        rulespec_uuid=result.rulespec_id,
        path=to_path_node(result.path),
    )


def to_path_node(path_node: ApiPathNode) -> PathNode:
    return PathNode(
        type=path_node.type_ if path_node.type_ is not UNSET else "",
        name=path_node.name if path_node.name is not UNSET else "",
        result=path_node.result if path_node.result is not UNSET else {},
        resolve_type=path_node.resolve_type if path_node.resolve_type is not UNSET else "",
        required=path_node.required if path_node.required is not UNSET else False,
        details=path_node.details.to_dict() if path_node.details is not UNSET else {},
        children=[to_path_node(child) for child in path_node.children] if path_node.children else [],
    )
