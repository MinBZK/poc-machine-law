from eventsourcing.dispatch import singledispatchmethod
from eventsourcing.system import ProcessApplication

from .aggregate import Claim


class ClaimProcessor(ProcessApplication):
    """Process application for handling claim events"""

    def __init__(self, rules_engine, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rules_engine = rules_engine
        self._case_manager = None

    @property
    def case_manager(self):
        if self._case_manager is None:
            # Get it from the runner when needed
            self._case_manager = self.runner.get("WrappedCaseManager")
        return self._case_manager

    @singledispatchmethod
    def policy(self, domain_event, process_event) -> None:
        """Sync policy that processes events"""

    @policy.register(Claim.Created)
    @policy.register(Claim.Approved)
    async def handle_claim_approved(self, domain_event, process_event) -> None:
        """
        When a claim is approved:
        1. If linked to a case, update the case
        2. Run any applicable rules
        """
        claim = self.repository.get(domain_event.originator_id)

        # If claim is linked to a case, update it
        if claim.case_id:
            case = self.case_manager.get_case_by_id(claim.case_id)
            if case:
                # Update the case parameter
                case.update_parameter(key=claim.key, new_value=domain_event.verified_value)
                self.case_manager.save(case)

        # Run any applicable rules
        await self.rules_engine.apply_rules(domain_event)
