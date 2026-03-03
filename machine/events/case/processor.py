from eventsourcing.dispatch import singledispatchmethod
from eventsourcing.system import ProcessApplication

from machine.events.case.aggregate import Case


class CaseProcessor(ProcessApplication):
    def __init__(self, rules_engine, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rules_engine = rules_engine

    @singledispatchmethod
    def policy(self, domain_event, process_event) -> None:
        """Sync policy that processes events"""

    @policy.register(Case.Objected)
    @policy.register(Case.AutomaticallyDecided)
    @policy.register(Case.Decided)
    def _(self, domain_event, process_event) -> None:
        try:
            self.rules_engine.apply_rules(domain_event)
        except Exception as e:
            print(f"Error processing rules: {e}")
