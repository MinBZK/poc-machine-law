import logging
from typing import Any
from uuid import UUID

import httpx

from web.config_loader import ServiceRoutingConfig

from ..claim_manager_interface import ClaimManagerInterface
from ..models import Claim
from .machine_client.regel_recht_engine_api_client import Client

logger = logging.getLogger(__name__)
from .machine_client.regel_recht_engine_api_client.api.claim import (
    claim_approve,
    claim_list_based_on_bsn,
    claim_list_based_on_bsn_service_law,
    claim_reject,
    claim_submit,
)
from .machine_client.regel_recht_engine_api_client.models import (
    ClaimApprove,
    ClaimApproveBody,
    ClaimReject,
    ClaimRejectBody,
    ClaimSubmit,
    ClaimSubmitBody,
)
from .machine_client.regel_recht_engine_api_client.types import UNSET


class ClaimManager(ClaimManagerInterface):
    """
    Implementation of ClaimManagerInterface that uses the embedded Python machine.service library.
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

    def get_claims_by_bsn(
        self, bsn: str, approved: bool = False, include_rejected: bool = False, effective_date: str | None = None
    ) -> list[Claim]:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """

        # When service routing is enabled and configured to query all services
        service_routing_config = getattr(self, "_service_routing_config", None)
        query_all = (
            service_routing_config and service_routing_config.query_all_for_claims if service_routing_config else False
        )

        if self.service_routing_enabled and self.service_routes and query_all:
            all_claims = []

            for service_name, service_config in self.service_routes.items():
                try:
                    client = Client(base_url=service_config.domain)
                    with client as client:
                        # If effective_date is provided, we need to manually add it as a query parameter
                        if effective_date:
                            # Get the base kwargs and add effective_date parameter
                            kwargs = claim_list_based_on_bsn._get_kwargs(
                                bsn=bsn, approved=approved, include_rejected=include_rejected
                            )
                            kwargs["params"]["effective_date"] = effective_date
                            response_raw = client.get_httpx_client().request(**kwargs)
                            response = claim_list_based_on_bsn._build_response(client=client, response=response_raw)
                        else:
                            response = claim_list_based_on_bsn.sync_detailed(
                                client=client, bsn=bsn, approved=approved, include_rejected=include_rejected
                            )
                        claims = to_claims(response.parsed.data)
                        all_claims.extend(claims)
                except Exception as e:
                    logger.error(f"[ClaimManager] Error querying {service_name}: {e}")
                    # Continue with other services even if one fails
                    continue

            return all_claims

        # Default behavior: query single base_url
        client = Client(base_url=self.base_url)

        with client as client:
            # If effective_date is provided, we need to manually add it as a query parameter
            if effective_date:
                # Get the base kwargs and add effective_date parameter
                kwargs = claim_list_based_on_bsn._get_kwargs(
                    bsn=bsn, approved=approved, include_rejected=include_rejected
                )
                kwargs["params"]["effective_date"] = effective_date
                response_raw = client.get_httpx_client().request(**kwargs)
                response = claim_list_based_on_bsn._build_response(client=client, response=response_raw)
            else:
                response = claim_list_based_on_bsn.sync_detailed(
                    client=client, bsn=bsn, approved=approved, include_rejected=include_rejected
                )

            return to_claims(response.parsed.data)

    def get_claim_by_bsn_service_law(
        self,
        bsn: str,
        service: str,
        law: str,
        approved: bool = False,
        include_rejected: bool = False,
        effective_date: str | None = None,
    ) -> dict[UUID:Claim]:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """

        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)
        client = Client(base_url=service_base_url)

        with client as client:
            # If effective_date is provided, we need to manually add it as a query parameter
            if effective_date:
                # Get the base kwargs and add effective_date parameter
                kwargs = claim_list_based_on_bsn_service_law._get_kwargs(
                    bsn=bsn, service=service, law=law, approved=approved, include_rejected=include_rejected
                )
                kwargs["params"]["effective_date"] = effective_date
                response_raw = client.get_httpx_client().request(**kwargs)
                response = claim_list_based_on_bsn_service_law._build_response(client=client, response=response_raw)
            else:
                response = claim_list_based_on_bsn_service_law.sync_detailed(
                    client=client,
                    bsn=bsn,
                    service=service,
                    law=law,
                    approved=approved,
                    include_rejected=include_rejected,
                )

            return to_dict_claims(response.parsed.data.additional_properties)

    def submit_claim(
        self,
        service: str,
        key: str,
        new_value: Any,
        reason: str,
        claimant: str,
        law: str,
        bsn: str,
        case_id: UUID | None = None,
        old_value: Any | None = None,
        evidence_path: str | None = None,
        auto_approve: bool = False,  # Add this parameter
    ) -> UUID:
        """
        Submit a new claim. Can be linked to an existing case or standalone.
        If auto_approve is True, the claim will be automatically approved.

        Args:
            service:

        Returns:
            A ClaimID
        """

        if case_id == "":
            case_id = None

        # Instantiate the API client with service-specific base URL
        service_base_url = self._get_base_url_for_service(service)
        client = Client(base_url=service_base_url)

        data = ClaimSubmit(
            service=service,
            key=key,
            new_value=new_value,
            reason=reason,
            claimant=claimant,
            law=law,
            bsn=bsn,
            case_id=case_id,
            old_value=old_value,
            evidence_path=evidence_path,
            auto_approve=auto_approve,
        )
        body = ClaimSubmitBody(data=data)

        with client as client:
            response = claim_submit.sync_detailed(client=client, body=body)
            content = response.parsed

            return content.data

    def reject_claim(self, claim_id: UUID, rejected_by: str, rejection_reason: str) -> None:
        """
        Reject a claim with reason

        Args:
            claim_id: Identifier of the claim
            rejected_by: User that rejected the claim
            rejection_reason: Reason of the rejection

        Returns:
            None
        """

        # Instantiate the API client
        logger.debug(f"[ClaimManager] reject_claim using base_url: {self.base_url}")
        client = Client(base_url=self.base_url)

        data = ClaimReject(rejected_by=rejected_by, rejection_reason=rejection_reason)
        body = ClaimRejectBody(data=data)

        with client as client:
            claim_reject.sync_detailed(client=client, claim_id=claim_id, body=body)

    def approve_claim(self, claim_id: UUID, verified_by: str, verified_value: str) -> None:
        """
        Approve a claim with verified value

        Args:
            claim_id: Identifier of the claim
            verified_by: User that verified the claim
            verified_value: Verified value

        Returns:
            None
        """

        # Instantiate the API client
        logger.debug(f"[ClaimManager] approve_claim using base_url: {self.base_url}")
        client = Client(base_url=self.base_url)

        data = ClaimApprove(verified_by=verified_by, verified_value=verified_value)
        body = ClaimApproveBody(data=data)

        with client as client:
            claim_approve.sync_detailed(client=client, claim_id=claim_id, body=body)


def to_claim(claim) -> Claim:
    return Claim(
        id=claim.id,
        service=claim.service,
        key=claim.key,
        new_value=claim.new_value,
        reason=claim.reason,
        claimant=claim.claimant,
        law=claim.law,
        bsn=claim.bsn,
        status=claim.status,
        case_id=claim.case_id if claim.case_id is not UNSET else None,
        old_value=claim.old_value if claim.old_value is not UNSET else None,
        evidence_path=claim.evidence_path if claim.evidence_path is not UNSET else None,
    )


def to_claims(claims: list[Any]) -> list[Claim]:
    return [to_claim(item) for item in claims]


def to_dict_claims(claims: dict[UUID:Any]) -> dict[UUID:Claim]:
    return {k: to_claim(item) for k, item in claims.items()}
