from datetime import date

from eventsourcing.dispatch import singledispatchmethod
from eventsourcing.persistence import Transcoder, Transcoding
from eventsourcing.system import ProcessApplication


class DateAsISO(Transcoding):
    """Transcoding for datetime.date objects to ISO format strings."""

    type = date
    name = "date_iso"

    def encode(self, obj: date) -> str:
        return obj.isoformat()

    def decode(self, data: str) -> date:
        return date.fromisoformat(data)


class ClaimProcessor(ProcessApplication):
    """Process application for handling claim events"""

    def __init__(self, rules_engine, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rules_engine = rules_engine
        self._case_manager = None

    def register_transcodings(self, transcoder: Transcoder) -> None:
        """Register custom transcodings for date serialization."""
        super().register_transcodings(transcoder)
        transcoder.register(DateAsISO())

    @property
    def case_manager(self):
        if self._case_manager is None:
            # Get it from the runner when needed
            self._case_manager = self.runner.get("WrappedCaseManager")
        return self._case_manager

    @singledispatchmethod
    def policy(self, domain_event, process_event) -> None:
        """Sync policy that processes events"""
