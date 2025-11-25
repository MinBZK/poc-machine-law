import asyncio
from datetime import date

from eventsourcing.dispatch import singledispatchmethod
from eventsourcing.persistence import Transcoder, Transcoding
from eventsourcing.system import ProcessApplication

from machine.events.case.aggregate import Case


class DateAsISO(Transcoding):
    """Transcoding for datetime.date objects to ISO format strings."""

    type = date
    name = "date_iso"

    def encode(self, obj: date) -> str:
        return obj.isoformat()

    def decode(self, data: str) -> date:
        return date.fromisoformat(data)


class CaseProcessor(ProcessApplication):
    def __init__(self, rules_engine, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rules_engine = rules_engine

    def register_transcodings(self, transcoder: Transcoder) -> None:
        """Register custom transcodings for date serialization."""
        super().register_transcodings(transcoder)
        transcoder.register(DateAsISO())

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
