import datetime
import logging
import urllib.parse
from typing import Any
from uuid import UUID

import httpx

from web.config_loader import ServiceRoutingConfig

from ..case_manager_interface import CaseManagerInterface
from ..models import Case, CaseObjectionStatus, CaseStatus, Event
from .machine_client.law_as_code_client import Client

logger = logging.getLogger(__name__)
from .machine_client.law_as_code_client.api.case import (
    case_based_on_bsn_service_law,
    case_get,
    case_list_based_on_bsn,
    case_list_based_on_service_law,
    case_object,
    case_review,
    case_submit,
    event_list_based_on_case_id,
)
from .machine_client.law_as_code_client.api.events import (
    event_list,
)
from .machine_client.law_as_code_client.models import (
    CaseObject,
    CaseObjectBody,
    CaseReview,
    CaseReviewBody,
    CaseSubmit,
    CaseSubmitBody,
)
from .machine_client.law_as_code_client.types import UNSET, Unset


class CaseManager(CaseManagerInterface):
    """
    Implementation of CaseManagerInterface that uses HTTP calls to the Go backend service.
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

    def get_case(self, bsn: str, service: str, law: str) -> Case | None:
        """
        Retrieves case information using HTTP calls to the Go backend service.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Dictionary containing case data if found, None otherwise
        """

        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)
        client = Client(base_url=service_base_url)

        with client as client:
            service = urllib.parse.quote_plus(service)
            law = urllib.parse.quote_plus(law)

            response = case_based_on_bsn_service_law.sync_detailed(
                client=client,
                bsn=bsn,
                service=service,
                law=law,
            )
            if response.status_code == 404:
                return None

            return to_case(response.parsed.data)

    def get_case_by_id(self, id: UUID) -> Case:
        # Instantiate the API client
        logger.debug(f"[CaseManager] get_case_by_id using base_url: {self.base_url}")
        client = Client(base_url=self.base_url)

        with client as client:
            response = case_get.sync_detailed(client=client, case_id=id)
            if response.status_code == 404:
                return None

            return to_case(response.parsed.data)

    def get_cases_by_law(self, service: str, law: str) -> list[Case]:
        """
        Retrieves case information using HTTP calls to the Go backend service.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Dictionary containing case data if found, None otherwise
        """

        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)
        client = Client(base_url=service_base_url)

        with client as client:
            service = urllib.parse.quote_plus(service)
            law = urllib.parse.quote_plus(law)

            response = case_list_based_on_service_law.sync_detailed(client=client, service=service, law=law)

            return to_cases(response.parsed.data)

    def get_cases_by_bsn(self, bsn: str) -> list[Case]:
        # When service routing is enabled and configured to query all services
        service_routing_config = getattr(self, "_service_routing_config", None)
        query_all = (
            service_routing_config and service_routing_config.query_all_for_cases if service_routing_config else False
        )

        if self.service_routing_enabled and self.service_routes and query_all:
            all_cases = []

            for service_name, service_config in self.service_routes.items():
                try:
                    client = Client(base_url=service_config.domain)
                    with client as client:
                        response = case_list_based_on_bsn.sync_detailed(client=client, bsn=bsn)
                        cases = to_cases(response.parsed.data)
                        all_cases.extend(cases)
                except Exception as e:
                    logger.error(f"[CaseManager] Error querying {service_name}: {e}")
                    # Continue with other services even if one fails
                    continue

            return all_cases

        # Default behavior: query single base_url
        client = Client(base_url=self.base_url)

        with client as client:
            response = case_list_based_on_bsn.sync_detailed(client=client, bsn=bsn)

            return to_cases(response.parsed.data)

    def submit_case(
        self,
        bsn: str,
        service: str,
        law: str,
        parameters: dict[str, Any],
        claimed_result: dict[str, Any],
        approved_claims_only: bool,
        effective_date: datetime.date | None = None,
    ) -> UUID:
        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)
        client = Client(base_url=service_base_url)

        data = CaseSubmit(
            bsn=bsn,
            service=service,
            law=law,
            parameters=parameters,
            claimed_result=claimed_result,
            approved_claims_only=approved_claims_only,
            effective_date=effective_date if effective_date is not None else UNSET,
        )
        body = CaseSubmitBody(data=data)

        with client as client:
            response = case_submit.sync_detailed(client=client, body=body)
            content = response.parsed

            return content.data

    def complete_manual_review(
        self,
        case_id: UUID,
        verifier_id: str,
        approved: bool,
        reason: str,
    ) -> None:
        # Instantiate the API client
        client = Client(base_url=self.base_url)

        data = CaseReview(
            verifier_id=verifier_id,
            approved=approved,
            reason=reason,
        )
        body = CaseReviewBody(data=data)

        with client as client:
            case_review.sync_detailed(client=client, case_id=case_id, body=body)

    def objection(
        self,
        case_id: UUID,
        reason: str,
    ) -> UUID:
        # Instantiate the API client
        client = Client(base_url=self.base_url)

        data = CaseObject(
            reason=reason,
        )
        body = CaseObjectBody(data=data)

        with client as client:
            case_object.sync_detailed(client=client, case_id=case_id, body=body)

    def get_events(
        self,
        case_id: UUID | None = None,
    ) -> list[Event]:
        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            if case_id is None:
                response = event_list.sync_detailed(client=client)
            else:
                response = event_list_based_on_case_id.sync_detailed(client=client, case_id=case_id)

            return to_events(response.parsed.data)

    # === AWIR Toeslag Methods ===
    # Note: These methods are not yet implemented in the HTTP backend

    def bereken_aanspraak(
        self,
        case_id: UUID,
        heeft_aanspraak: bool,
        berekend_jaarbedrag: int,
        berekening_datum: datetime.date | None = None,
    ) -> UUID:
        raise NotImplementedError("bereken_aanspraak not supported via HTTP API")

    def wijs_af(
        self,
        case_id: UUID,
        reden: str,
    ) -> UUID:
        raise NotImplementedError("wijs_af not supported via HTTP API")

    def stel_voorschot_vast(
        self,
        case_id: UUID,
        jaarbedrag: int | None = None,
        maandbedrag: int | None = None,
        beschikking_datum: datetime.date | None = None,
    ) -> UUID:
        raise NotImplementedError("stel_voorschot_vast not supported via HTTP API")

    async def __aenter__(self):
        await self.client.__aenter__()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.client.__aexit__(exc_type, exc_val, exc_tb)


def get_value(val: Unset | Any, default: Any = None) -> bool:
    if val is UNSET:
        return default
    return val


def to_case(case) -> Case:
    return Case(
        id=case.id,
        bsn=case.bsn,
        service=case.service,
        law=case.law,
        parameters=case.parameters,
        claimed_result=case.claimed_result,
        verified_result=case.verified_result,
        rulespec_uuid=case.rulespec_id,
        approved_claims_only=case.approved_claims_only,
        status=CaseStatus(case.status),
        approved=get_value(case.approved),
        objection_status=to_objection_status(case.objection_status),
        appeal_status=to_appeal_status(case.appeal_status),
        # AWIR lifecycle fields
        created_at=get_value(getattr(case, "created_at", None)),
        berekeningsjaar=get_value(getattr(case, "berekeningsjaar", None)),
        heeft_aanspraak=get_value(getattr(case, "heeft_aanspraak", None)),
        berekend_jaarbedrag=get_value(getattr(case, "berekend_jaarbedrag", None)),
        berekening_datum=get_value(getattr(case, "berekening_datum", None)),
        voorschot_jaarbedrag=get_value(getattr(case, "voorschot_jaarbedrag", None)),
        voorschot_maandbedrag=get_value(getattr(case, "voorschot_maandbedrag", None)),
        huidige_maand=get_value(getattr(case, "huidige_maand", None)) or 0,
        beschikkingen=get_value(getattr(case, "beschikkingen", None)) or [],
        maandelijkse_berekeningen=get_value(getattr(case, "maandelijkse_berekeningen", None)) or [],
        maandelijkse_betalingen=get_value(getattr(case, "maandelijkse_betalingen", None)) or [],
        definitieve_beschikking_datum=get_value(getattr(case, "definitieve_beschikking_datum", None)),
        definitief_jaarbedrag=get_value(getattr(case, "definitief_jaarbedrag", None)),
        vereffening_datum=get_value(getattr(case, "vereffening_datum", None)),
        vereffening_type=get_value(getattr(case, "vereffening_type", None)),
        vereffening_bedrag=get_value(getattr(case, "vereffening_bedrag", None)),
    )


def to_cases(cases: list[Any]) -> list[Case]:
    return [to_case(item) for item in cases]


def to_appeal_status(appeal) -> dict[str, Any]:
    return appeal.to_dict()


def to_objection_status(objection) -> CaseObjectionStatus:
    if objection is None:
        return None

    return CaseObjectionStatus(
        possible=get_value(objection.possible),
        not_possible_reason=get_value(objection.not_possible_reason),
        objection_period=get_value(objection.objection_period),
        decision_period=get_value(objection.decision_period),
        extension_period=get_value(objection.extension_period),
        admissable=get_value(objection.admissable),
    )


def to_event(event) -> Event:
    return Event(
        event_type=event.event_type,
        timestamp=event.timestamp,
        data=event.data,
    )


def to_events(events: list[Any]) -> list[Event]:
    return [to_event(item) for item in events]
