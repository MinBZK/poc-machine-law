import asyncio
import json
import random
from datetime import datetime
from decimal import Decimal
from typing import Optional, List, Dict, Tuple
from uuid import UUID

from eventsourcing.application import Application
from eventsourcing.dispatch import singledispatchmethod
from eventsourcing.system import ProcessApplication

from .aggregate import ServiceCase, CaseStatus


class RuleProcessor(ProcessApplication):
    def __init__(self, rules_engine, **kwargs):
        super().__init__(**kwargs)
        self.rules_engine = rules_engine

    @singledispatchmethod
    def policy(self, domain_event, process_event):
        """Sync policy that processes events"""
        pass

    @policy.register(ServiceCase.Objected)
    @policy.register(ServiceCase.AutomaticallyDecided)
    @policy.register(ServiceCase.Decided)
    def _(self, domain_event, process_event):
        try:
            # Create a new event loop in a new thread
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(
                    self.rules_engine.apply_rules(domain_event)
                )

            # Run in a separate thread
            import threading

            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join()  # Wait for completion

        except Exception as e:
            print(f"Error processing rules: {e}")


class ServiceCaseManager(Application):
    """
    Application service for managing service cases.
    Handles case submission, verification, decisions, and objections.
    """

    SAMPLE_RATE = 0.50  # 10% sample rate

    def __init__(self, rules_engine, **kwargs):
        super().__init__(**kwargs)
        self.rules_engine = rules_engine
        self._case_index: Dict[
            Tuple[str, str, str], str
        ] = {}  # (bsn, service, law) -> case_id
        # self.follow()

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
                    if abs(
                        verified_result[key] - claimed_result[key]
                    ) / verified_result[key] > Decimal("0.01"):
                        return False
                else:
                    return False
            # For other values, require exact match
            elif verified_result[key] != claimed_result[key]:
                return False

        return True

    async def submit_case(
        self,
        bsn: str,
        service_type: str,
        law: str,
        parameters: Dict,
        claimed_result: Dict,
    ) -> str:
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
            case.decide_automatically(
                verified_result=verified_result,
                parameters=parameters,
                approved=True,
            )
        else:
            # Route to manual review with reason
            reason = "Selected for manual review - " + (
                "results differ" if not results_match else "random sample check"
            )

            case.select_for_manual_review(
                verifier_id="SYSTEM",
                reason=reason,
                claimed_result=claimed_result,
                verified_result=verified_result,
            )

        # Save and index
        self.save(case)
        self._index_case(case)

        return str(case.id)

    def complete_manual_review(
        self,
        case_id: str,
        verifier_id: str,
        approved: bool,
        reason: str,
        override_result: Optional[Dict] = None,
    ) -> str:
        """
        Complete manual review of a case.
        """
        case = self.get_case_by_id(case_id)
        if case.status not in [CaseStatus.IN_REVIEW, CaseStatus.OBJECTED]:
            raise ValueError(
                "Can only complete review for cases in review or objections"
            )

        # Use current verified_result or override if provided
        verified_result = override_result or case.verified_result

        case.decide(
            verified_result=verified_result,
            reason=reason,
            verifier_id=verifier_id,
            approved=approved,
        )

        self.save(case)
        return str(case.id)

    def objection_case(self, case_id: str, reason: str) -> str:
        """
        Submit an objection for a case with newly claimed result.
        Appeals always go to manual review.
        """
        case = self.get_case_by_id(case_id)

        # First record the objection with citizen's new claim
        case.object(reason=reason)

        self.save(case)
        return str(case.id)

    def determine_objection_status(
        self,
        case_id: str,
        possible: Optional[bool] = None,  # bezwaar_mogelijk
        not_possible_reason: Optional[str] = None,  # reden_niet_mogelijk
        objection_period: Optional[int] = None,  # bezwaartermijn
        decision_period: Optional[int] = None,  # beslistermijn
        extension_period: Optional[int] = None,
    ) -> str:  # verdagingstermijn
        """
        Determine the objection status, possibility and periods based on rules/law.
        All parameters are optional.
        Time periods are in weeks.

        Args:
            case_id: ID of the case
            possible: Whether objection is possible (bezwaar_mogelijk)
            not_possible_reason: Reason why objection is not possible (reden_niet_mogelijk)
            objection_period: Weeks allowed for filing objection (bezwaartermijn)
            decision_period: Weeks allowed for decision (beslistermijn)
            extension_period: Possible extension period in weeks (verdagingstermijn)
        """
        case = self.get_case_by_id(case_id)

        case.determine_objection_status(
            possible=possible,
            not_possible_reason=not_possible_reason,
            objection_period=objection_period,
            decision_period=decision_period,
            extension_period=extension_period,
        )

        self.save(case)
        return str(case.id)

    def determine_objection_admissibility(
        self, case_id: str, admissible: Optional[bool] = None
    ) -> str:
        """
        Determine whether an objection is admissible (ontvankelijk)

        Args:
            case_id: ID of the case
            admissible: Whether the objection is admissible (ontvankelijk)
        """
        case = self.get_case_by_id(case_id)

        case.determine_objection_admissibility(admissible=admissible)

        self.save(case)
        return str(case.id)

    # Query methods

    def can_object(self, case_id: str) -> bool:
        return self.get_case_by_id(case_id).can_object()

    def get_case(self, bsn: str, service_type: str, law: str) -> Optional[ServiceCase]:
        """Get case for specific bsn, service and law combination"""
        key = self._index_key(bsn, service_type, law)
        case_id = self._case_index.get(key)
        return self.get_case_by_id(case_id) if case_id else None

    def get_cases_by_status(
        self, service_type: str, status: CaseStatus
    ) -> List[ServiceCase]:
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

    def get_events(self, case_id=None):
        notification_log = self.notification_log
        events = []

        start = 1
        while True:
            try:
                notifications = notification_log.select(start=start, limit=10)
                if not notifications:
                    break

                for notification in notifications:
                    if case_id is not None and notification.originator_id != case_id:
                        continue

                    # Decode the state from bytes to JSON
                    state_data = json.loads(notification.state.decode("utf-8"))

                    # Extract timestamp if available
                    timestamp = state_data.get("timestamp", {}).get("_data_", None)
                    if timestamp:
                        timestamp = datetime.fromisoformat(timestamp)

                    events.append(
                        {
                            "case_id": notification.originator_id,
                            "timestamp": timestamp
                            or str(notification.originator_version),
                            "event_type": notification.topic.split(".")[-1],
                            "data": {
                                k: v
                                for k, v in state_data.items()
                                if k not in ["timestamp", "originator_topic"]
                            },
                        }
                    )

                start += 10
            except ValueError:
                break

        events.sort(key=lambda x: str(x["timestamp"]))

        return events
