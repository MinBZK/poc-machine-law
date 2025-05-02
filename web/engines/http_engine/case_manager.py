import urllib.parse
from typing import Any
from uuid import UUID

import httpx

from ..case_manager_interface import CaseManagerInterface
from ..models import Case, CaseObjectionStatus, CaseStatus, Event
from .machine_client.law_as_code_client import Client
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
    """

    def __init__(self, base_url: str = "http://localhost:8081/v0"):
        self.base_url = base_url
        self.client = httpx.AsyncClient(base_url=self.base_url)

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

        # Instantiate the API client
        client = Client(base_url=self.base_url)

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

        # Instantiate the API client
        client = Client(base_url=self.base_url)

        with client as client:
            service = urllib.parse.quote_plus(service)
            law = urllib.parse.quote_plus(law)

            response = case_list_based_on_service_law.sync_detailed(client=client, service=service, law=law)

            return to_cases(response.parsed.data)

    def get_cases_by_bsn(self, bsn: str) -> list[Case]:
        # Instantiate the API client
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
    ) -> UUID:
        # Instantiate the API client
        client = Client(base_url=self.base_url)

        data = CaseSubmit(
            bsn=bsn,
            service=service,
            law=law,
            parameters=parameters,
            claimed_result=claimed_result,
            approved_claims_only=approved_claims_only,
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
        appeal_status=case.appeal_status,
    )


def to_cases(cases: list[Any]) -> list[Case]:
    return [to_case(item) for item in cases]


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
