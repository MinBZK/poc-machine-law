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
    @policy.register(Case.VoorschotBeschikkingVastgesteld)
    @policy.register(Case.Afgewezen)
    @policy.register(Case.DefinitieveBeschikkingVastgesteld)
    def _(self, domain_event, process_event) -> None:
        try:
            # apply_rules is a sync method
            self.rules_engine.apply_rules(domain_event)
        except Exception as e:
            print(f"Error processing rules: {e}")
