import datetime
from abc import ABC, abstractmethod
from typing import Any
from uuid import UUID

from .models import Case, Event


class CaseManagerInterface(ABC):
    """
    Interface defining case management functionality.
    """

    @abstractmethod
    def get_case(self, bsn: str, service: str, law: str) -> Case | None:
        """
        Retrieves case information based on provided parameters.

        Args:
            bsn: String identifier for the specific case
            service: String identifier for the service where the case is applicable
            law: String identifier for the law where the case is applicable

        Returns:
            A Case containing the case information
        """

    @abstractmethod
    def get_case_by_id(self, id: UUID) -> Case | None:
        """
        Retrieves case information based on provided parameters.

        Args:
            id: uuid identifier for the specific case

        Returns:
            A Case containing the case information
        """

    @abstractmethod
    def get_cases_by_law(self, service: str, law: str) -> list[Case]:
        """
        Retrieves case information based on provided parameters.

        Args:
            service: String identifier for the service where the case is applicable
            law: String identifier for the law where the case is applicable

        Returns:
            All Cases containing the case information filtered on service & law
        """

    @abstractmethod
    def get_cases_by_bsn(self, bsn: str) -> list[Case]:
        """
        Get all cases for a specific citizen by BSN

        Args:
            bsn: identifier of the citizen

        Returns:
            All Cases that are attached to this bsn
        """

    @abstractmethod
    def submit_case(
        self,
        bsn: str,
        service: str,
        law: str,
        parameters: dict[str, Any],
        claimed_result: dict[str, Any],
        approved_claims_only: bool,
        effective_date: datetime.date | None = None,
        created_at: datetime.datetime | None = None,
    ) -> UUID:
        """
        Submit a case with information.

        Args:
            bsn: String identifier for the specific citizen
            service: String identifier for the service where the case is applicable
            law: String identifier for the law where the case is applicable
            parameters: dictionary containing the parameters that where used to execute the law
            claimed_result: dictionary containing the claimed result from the law
            approved_claims_only: Boolean only use approved claims while processing this case
            effective_date: Optional date on which the case, when accepted, should become effective
            created_at: Optional datetime timestamp for when the case was created (for simulation)

        Returns:
            A Case containing the case information
        """

    @abstractmethod
    def complete_manual_review(
        self,
        case_id: UUID,
        verifier_id: str,
        approved: bool,
        reason: str,
    ) -> None:
        """
        Complete a manual review

        Args:
            case_id: UUID identifier of the specific case
            verifier_id: String identifier of the reviewer
            approved: Boolean value with decision
            reason: explained over the decision

        Returns:
            None
        """

    @abstractmethod
    def objection(
        self,
        case_id: UUID,
        reason: str,
    ) -> None:
        """
        Object to a case

        Args:
            case_id: UUID identifier of the specific case
            reason: reason of the objection

        Returns:
            None
        """

    @abstractmethod
    def get_events(
        self,
        case_id: UUID | None = None,
    ) -> list[Event]:
        """
        Get all events, filter on case id if given

        Args:
            case_id: UUID identifier of a specific case

        Returns:
            A List containen all events
        """

    @abstractmethod
    def bereken_aanspraak(
        self,
        case_id: UUID,
        heeft_aanspraak: bool,
        berekend_jaarbedrag: int,
        berekening_datum: datetime.date | None = None,
    ) -> UUID:
        """
        Calculate entitlement for a toeslag case

        Args:
            case_id: UUID identifier of the specific case
            heeft_aanspraak: Boolean indicating if citizen is entitled
            berekend_jaarbedrag: Calculated yearly amount in eurocents
            berekening_datum: Optional date for the calculation (defaults to today)

        Returns:
            The case id
        """

    @abstractmethod
    def stel_voorschot_vast(
        self,
        case_id: UUID,
        jaarbedrag: int | None = None,
        maandbedrag: int | None = None,
        beschikking_datum: datetime.date | None = None,
    ) -> UUID:
        """
        Establish advance payment for a toeslag case

        Args:
            case_id: UUID identifier of the specific case
            jaarbedrag: Optional yearly amount (uses berekend_jaarbedrag if not provided)
            maandbedrag: Optional monthly amount (calculated from yearly if not provided)
            beschikking_datum: Optional date for the besluit (defaults to today)

        Returns:
            The case id
        """
