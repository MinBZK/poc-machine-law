import logging
import urllib.parse
from collections import defaultdict
from datetime import date, datetime
from typing import Any

import httpx
import pandas as pd

from web.config_loader import ServiceRoutingConfig

from ..engine_interface import EngineInterface, PathNode, RuleResult
from .machine_client.regel_recht_engine_api_client import Client
from .machine_client.regel_recht_engine_api_client.errors import UnexpectedStatus

logger = logging.getLogger(__name__)
from .machine_client.regel_recht_engine_api_client.api.data_frames import set_source_data_frame
from .machine_client.regel_recht_engine_api_client.api.engine import reset_engine
from .machine_client.regel_recht_engine_api_client.api.law import (
    evaluate,
    rule_spec_get,
    service_laws_discoverable_list,
)
from .machine_client.regel_recht_engine_api_client.api.profile import profile_get, profile_list
from .machine_client.regel_recht_engine_api_client.models import (
    DataFrame,
    Evaluate,
    EvaluateBody,
    EvaluateInput,
    EvaluateParameters,
    Profile,
    ProfileSources,
    SetSourceDataFrameBody,
)
from .machine_client.regel_recht_engine_api_client.models import (
    PathNode as ApiPathNode,
)
from .machine_client.regel_recht_engine_api_client.models import (
    ResponseEvaluateSchema as ApiRuleResult,
)
from .machine_client.regel_recht_engine_api_client.types import UNSET


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
                # URL encode service and law parameters
                encoded_service = urllib.parse.quote_plus(service)
                encoded_law = urllib.parse.quote_plus(law)

                response = rule_spec_get.sync_detailed(
                    client=client, service=encoded_service, law=encoded_law, reference_date=reference_date
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

    def get_discoverable_service_laws(
        self, discoverable_by="CITIZEN", filter_disabled: bool = True
    ) -> dict[str, list[str]]:
        """
        Get laws discoverable by citizens using HTTP calls to the Go backend service.

        Args:
            discoverable_by: The type of entity discovering laws (CITIZEN, BUSINESS, DELEGATION_PROVIDER)
            filter_disabled: If True, filter out laws disabled via feature flags. Set to False for admin UI.

        Returns:
            Dictionary mapping service names to sets of law names
        """
        from web.feature_flags import FeatureFlags

        result = defaultdict(set)

        def should_include_law(service_name: str, law_name: str) -> bool:
            """Check if law should be included based on filter_disabled flag."""
            if not filter_disabled:
                return True
            return FeatureFlags.is_law_enabled(service_name, law_name)

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
                            if should_include_law(item.name, law.name):
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
                    if should_include_law(item.name, law.name):
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
                        result[item.bsn] = self.profile_transform(item)

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
                result[item.bsn] = self.profile_transform(item)

            return result

    def get_profile_data(self, bsn: str, effective_date: date | None = None) -> dict[str, Any] | None:
        if effective_date is None:
            effective_date = UNSET

        # Always use default base_url for profile data (profiles are centralized)
        # Service routing does not apply to individual profile lookups
        client = Client(base_url=self.base_url)

        try:
            with client as client:
                response = profile_get.sync_detailed(client=client, bsn=bsn, effective_date=effective_date)
                content = response.parsed

                # Handle different response types
                if response.status_code == 200:
                    return self.profile_transform(content.data)
                elif response.status_code == 404:
                    logger.warning(f"[MachineService] Profile not found for BSN: {bsn}")
                    return None
                else:
                    logger.error(f"[MachineService] Error getting profile for BSN {bsn}: Status {response.status_code}")
                    return None
        except UnexpectedStatus as e:
            # Log the detailed error and re-raise with more context
            error_message = e.content.decode("utf-8") if e.content else "No response content"
            logger.error(f"[MachineService] Connection error getting profile for BSN {bsn}: {error_message}")
            # Re-raise the exception so it can be handled by the calling code
            raise

    def get_business_profile(self, kvk_nummer: str) -> dict[str, Any] | None:
        """
        Get business profile data for a specific KVK number.

        Note: The HTTP API does not currently have a business profile endpoint.
        This method returns None until the API is extended to support business profiles.

        Args:
            kvk_nummer: KVK registration number for the business

        Returns:
            None (API endpoint not available)
        """
        logger.warning(f"[MachineService] get_business_profile not available via HTTP API for KVK: {kvk_nummer}")
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

    def reset(self) -> None:
        import time
        from concurrent.futures import ThreadPoolExecutor

        def reset_service(service_name: str, service_config) -> None:
            start_time = time.time()
            logger.warning(f"[MachineService] resetting {service_name} - started at {start_time}")
            client = Client(base_url=service_config.domain)
            with client as client:
                reset_engine.sync_detailed(client=client)
            elapsed = time.time() - start_time
            logger.warning(f"[MachineService] resetting {service_name} - completed in {elapsed:.3f}s")

        # Run all reset calls in parallel using threads
        logger.warning(f"[MachineService] Starting parallel reset of {len(self.service_routes)} services")
        overall_start = time.time()

        with ThreadPoolExecutor() as executor:
            futures = [
                executor.submit(reset_service, service_name, service_config)
                for service_name, service_config in self.service_routes.items()
            ]
            # Wait for all to complete
            for future in futures:
                future.result()

        overall_elapsed = time.time() - overall_start
        logger.warning(f"[MachineService] All resets completed in {overall_elapsed:.3f}s total")

    def get_services(self):
        """Get the underlying Services instance.

        Note: This is not available in the HTTP engine.
        """
        raise NotImplementedError(
            "Services is only available with the Python engine. "
            "The HTTP engine does not support direct Services access."
        )

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)

    def profile_transform(self, profile: Profile) -> dict[str, Any]:
        p = profile.to_dict()
        p["sources"] = source_transform(profile.sources)
        # Merge static properties from profile with dynamically generated ones
        static_properties = p.get("properties", []) or []
        dynamic_properties = super().get_profile_properties(p)
        p["properties"] = static_properties + dynamic_properties
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
