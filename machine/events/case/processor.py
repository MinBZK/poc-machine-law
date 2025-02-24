import asyncio

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
            # Create a new event loop in a new thread
            def run_async():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                return loop.run_until_complete(self.rules_engine.apply_rules(domain_event))

            # Run in a separate thread
            import threading

            thread = threading.Thread(target=run_async)
            thread.start()
            thread.join()  # Wait for completion

        except Exception as e:
            print(f"Error processing rules: {e}")
