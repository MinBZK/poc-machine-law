import random
from decimal import Decimal
from typing import Optional, List, Dict, Tuple
from uuid import UUID

from eventsourcing.application import Application

from .aggregate import ServiceCase, CaseStatus


class ServiceCaseManager(Application):
    """
    Application service for managing service cases.
    Handles case submission, verification, decisions, and appeals.
    """

    SAMPLE_RATE = 0.50  # 10% sample rate

    def __init__(self, rules_engine):
        super().__init__()
        self.rules_engine = rules_engine
        self._case_index: Dict[Tuple[str, str, str], str] = {}  # (bsn, service, law) -> case_id

    def _index_key(self, bsn: str, service_type: str, law: str) -> Tuple[str, str, str]:
        """Generate index key for the combination of bsn, service and law"""
        return (bsn, service_type, law)

    def _index_case(self, case: ServiceCase):
        """Add case to index"""
        key = self._index_key(case.bsn, case.service, case.law)
        self._case_index[key] = str(case.id)

    def _results_match(self, claimed_result: Dict, verified_result: Dict) -> bool:
        """
        Compare claimed and verified results to determine if they match.
        For numeric values, uses a 1% tolerance.
        For other values, requires exact match.
        """
        for key in verified_result:
            if key not in claimed_result:
                return False

            # For numeric values, compare with tolerance
            if isinstance(verified_result[key], (int, float)):
                if isinstance(claimed_result[key], (int, float)):
                    if abs(verified_result[key] - claimed_result[key]) / verified_result[key] > Decimal('0.01'):
                        return False
                else:
                    return False
            # For other values, require exact match
            elif verified_result[key] != claimed_result[key]:
                return False

        return True

    async def submit_case(self,
                          bsn: str,
                          service_type: str,
                          law: str,
                          parameters: Dict,
                          claimed_result: Dict) -> str:
        """
        Submit a new case and automatically process it if possible.
        A case starts with the citizen's claimed result which is then verified.
        """

        result = await self.rules_engine.evaluate(service_type, law, parameters)

        # Create new case with citizen's claimed result
        case = ServiceCase(
            bsn=bsn,
            service_type=service_type,
            law=law,
            parameters=parameters,
            claimed_result=claimed_result,
            rulespec_uuid=result.rulespec_uuid,
        )

        # Verify using rules engine
        verified_result = result.output

        # Check if results match and if manual review is needed
        results_match = self._results_match(claimed_result, verified_result)
        needs_manual_review = random.random() < self.SAMPLE_RATE

        if results_match and not needs_manual_review:
            # Automatic approval
            case.add_automatic_decision(
                verified_result=verified_result,
                parameters=parameters,
                approved=True,
            )
        else:
            # Route to manual review with reason
            reason = "Selected for manual review - " + (
                "results differ" if not results_match
                else "random sample check"
            )

            case.add_to_manual_review(
                verifier_id="SYSTEM",
                reason=reason,
                claimed_result=claimed_result,
                verified_result=verified_result,
            )

        # Save and index
        self.save(case)
        self._index_case(case)

        return str(case.id)

    def complete_manual_review(self,
                               case_id: str,
                               verifier_id: str,
                               approved: bool,
                               reason: str,
                               override_result: Optional[Dict] = None) -> str:
        """
        Complete manual review of a case.
        """
        case = self.get_case_by_id(case_id)
        if case.status != CaseStatus.IN_REVIEW:
            raise ValueError("Can only complete review for cases in review")

        # Use current verified_result or override if provided
        verified_result = override_result or case.verified_result

        case.add_manual_decision(
            verified_result=verified_result,
            reason=reason,
            verifier_id=verifier_id,
            approved=approved,
        )

        self.save(case)
        return str(case.id)

    def appeal_case(self,
                    case_id: str,
                    disputed_parameters: Dict,
                    evidence: List[str],
                    reason: str,
                    claimed_result: Dict) -> str:
        """
        Submit an appeal for a case with newly claimed result.
        Appeals always go to manual review.
        """
        case = self.get_case_by_id(case_id)

        # First record the appeal with citizen's new claim
        case.add_appeal(
            disputed_parameters=disputed_parameters,
            claimed_result=claimed_result,
            evidence=evidence,
            reason=reason
        )

        # Calculate verified result based on disputed parameters
        result = self.rules_engine.evaluate(case.service, case.law, disputed_parameters)
        verified_result = result.output

        # Appeals always go to manual review
        case.add_to_manual_review(
            verifier_id="SYSTEM",
            reason="Appeal requires manual review",
            claimed_result=claimed_result,
            verified_result=verified_result
        )

        self.save(case)
        return str(case.id)

    # Query methods

    def get_case(self, bsn: str, service_type: str, law: str) -> Optional[ServiceCase]:
        """Get case for specific bsn, service and law combination"""
        key = self._index_key(bsn, service_type, law)
        case_id = self._case_index.get(key)
        return self.get_case_by_id(case_id) if case_id else None

    def get_cases_by_status(self, service_type: str, status: CaseStatus) -> List[ServiceCase]:
        """Get all cases for a service in a particular status"""
        return [
            self.get_case_by_id(case_id)
            for case_id in self._case_index.values()
            if self.repository.get(case_id).service == service_type
               and self.repository.get(case_id).status == status
        ]

    def get_case_by_id(self, case_id: Optional[str]) -> Optional[ServiceCase]:
        """Get case by ID"""
        if not case_id:
            return None
        return self.repository.get(UUID(case_id))

    def get_cases_by_law(self, law: str, service_type: str) -> List[ServiceCase]:
        """Get all cases for a specific law and service combination"""
        cases = []
        for key, case_id in self._case_index.items():
            case = self.get_case_by_id(case_id)
            if case.law == law and case.service == service_type:
                cases.append(case)
        return cases
