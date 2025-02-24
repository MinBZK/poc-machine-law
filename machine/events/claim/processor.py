from eventsourcing.dispatch import singledispatchmethod
from eventsourcing.system import ProcessApplication


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
