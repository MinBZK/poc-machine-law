import datetime
from typing import Any
from uuid import UUID

from machine.service import Services

from ..case_manager_interface import CaseManagerInterface
from ..models import Case, CaseObjectionStatus, CaseStatus, Event


class CaseManager(CaseManagerInterface):
    """
    Implementation of CaseManagerInterface that uses the embedded Python machine.service library.
    """

    def __init__(self, services: Services):
        self.case_manager = services.case_manager

    def get_case(self, bsn: str, service: str, law: str) -> Case | None:
        """
        Retrieves case information using the embedded Python machine.service library.

        Args:
            bsn: BSN identifier for the individual
            service: Service provider code (e.g., "TOESLAGEN")
            law: Law identifier (e.g., "zorgtoeslagwet")

        Returns:
            Case object if found, None otherwise
        """
        case = self.case_manager.get_case(bsn, service, law)
        if case is not None:
            return to_case(case)

        return None

    def get_case_by_id(self, id: UUID) -> Case:
        case = self.case_manager.get_case_by_id(id)
        if case is not None:
            return to_case(case)

        return None

    def get_cases_by_law(self, service: str, law: str) -> list[Case]:
        cases = self.case_manager.get_cases_by_law(law, service)
        return to_cases(cases)

    def get_cases_by_bsn(self, bsn: str) -> list[Case]:
        cases = self.case_manager.get_cases_by_bsn(bsn)
        return to_cases(cases)

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
        # Note: The underlying machine.service library does not support effective_date yet
        # For now, we pass the existing parameters and ignore effective_date
        return self.case_manager.submit_case(
            bsn=bsn,
            service_type=service,
            law=law,
            parameters=parameters,
            claimed_result=claimed_result,
            approved_claims_only=approved_claims_only,
        )

    def complete_manual_review(
        self,
        case_id: UUID,
        verifier_id: str,
        approved: bool,
        reason: str,
    ) -> UUID:
        return self.case_manager.complete_manual_review(
            case_id=case_id,
            verifier_id=verifier_id,
            approved=approved,
            reason=reason,
        )

    def objection(
        self,
        case_id: UUID,
        reason: str,
    ) -> UUID:
        return self.case_manager.objection_case(case_id, reason)

    def get_events(
        self,
        case_id: UUID | None = None,
    ) -> list[dict[str, Any]]:
        events = self.case_manager.get_events(case_id)
        return to_events(events)

    # === AWIR Toeslag Methods ===

    def bereken_aanspraak(
        self,
        case_id: UUID,
        heeft_aanspraak: bool,
        berekend_jaarbedrag: int,
    ) -> UUID:
        result = self.case_manager.bereken_aanspraak(
            case_id=str(case_id),
            heeft_aanspraak=heeft_aanspraak,
            berekend_jaarbedrag=berekend_jaarbedrag,
        )
        return UUID(result)

    def wijs_af(
        self,
        case_id: UUID,
        reden: str,
    ) -> UUID:
        result = self.case_manager.wijs_af(
            case_id=str(case_id),
            reden=reden,
        )
        return UUID(result)

    def stel_voorschot_vast(
        self,
        case_id: UUID,
        jaarbedrag: int | None = None,
        maandbedrag: int | None = None,
    ) -> UUID:
        result = self.case_manager.stel_voorschot_vast(
            case_id=str(case_id),
            jaarbedrag=jaarbedrag,
            maandbedrag=maandbedrag,
        )
        return UUID(result)


def to_case(case) -> Case:
    return Case(
        id=case.id,
        bsn=case.bsn,
        service=case.service,
        law=case.law,
        parameters=case.parameters,
        claimed_result=case.claimed_result,
        verified_result=case.verified_result,
        rulespec_uuid=case.rulespec_uuid,
        approved_claims_only=case.approved_claims_only,
        status=CaseStatus(case.status),
        approved=case.approved,
        objection_status=to_objection_status(getattr(case, "objection_status", None)),
        appeal_status=getattr(case, "appeal_status", None),
    )


def to_cases(cases: list[Any]) -> list[Case]:
    return [to_case(item) for item in cases]


def to_objection_status(objection) -> CaseObjectionStatus:
    if objection is None:
        return None

    return CaseObjectionStatus(
        possible=objection.get("possible", None),
        not_possible_reason=objection.get("not_possible_reason", None),
        objection_period=objection.get("objection_period", None),
        decision_period=objection.get("decision_period", None),
        extension_period=objection.get("extension_period", None),
        admissable=objection.get("admissable", None),
    )


def to_event(event) -> Event:
    return Event(
        event_type=event.get("event_type"),
        timestamp=event.get("timestamp"),
        data=event.get("data"),
    )


def to_events(events: list[Any]) -> list[Event]:
    return [to_event(item) for item in events]
