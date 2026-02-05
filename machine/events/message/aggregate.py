from datetime import date, datetime
from enum import Enum

from eventsourcing.domain import Aggregate, event


class MessageStatus(str, Enum):
    """Status van een bericht aan de burger"""

    CREATED = "CREATED"  # Bericht aangemaakt
    SENT = "SENT"  # Verzonden naar burger (AWB Art. 3:41)
    READ = "READ"  # Gelezen door burger
    ARCHIVED = "ARCHIVED"  # Gearchiveerd


class MessageType(str, Enum):
    """Type bericht gebaseerd op AWIR beschikkingen"""

    VOORSCHOT_BESCHIKKING = "VOORSCHOT_BESCHIKKING"  # AWIR Art. 16
    DEFINITIEVE_BESCHIKKING = "DEFINITIEVE_BESCHIKKING"  # AWIR Art. 19
    AFWIJZING = "AFWIJZING"  # AWIR Art. 16 lid 4


class Message(Aggregate):
    """
    Bericht aggregate voor communicatie met burgers.

    Wettelijke grondslag:
    - AWIR Art. 13: Elektronisch berichtenverkeer
    - AWIR Art. 16: Voorschotbeschikking
    - AWIR Art. 19: Definitieve toekenning
    - AWB Art. 3:40: Besluit treedt niet in werking voor bekendmaking
    - AWB Art. 3:41: Bekendmaking door toezending/uitreiking
    - AWB Art. 3:45: Rechtsmiddelenclausule
    """

    @event("Created")
    def __init__(
        self,
        bsn: str,
        case_id: str,
        message_type: MessageType,
        onderwerp: str,
        inhoud: str,
        rechtsmiddel_info: str | None = None,
        law: str | None = None,
        datum: str | None = None,  # ISO date string (YYYY-MM-DD) for eventsourcing serialization
    ) -> None:
        self.bsn = bsn
        self.case_id = case_id
        self.message_type = message_type
        self.onderwerp = onderwerp
        self.inhoud = inhoud
        self.rechtsmiddel_info = rechtsmiddel_info
        self.law = law
        self.status = MessageStatus.CREATED
        # Use provided datum (from beschikking) or fall back to now
        # datum is expected as ISO string (YYYY-MM-DD) for eventsourcing compatibility
        if datum is not None:
            if isinstance(datum, str):
                self.created_at = datetime.fromisoformat(datum)
            elif isinstance(datum, date) and not isinstance(datum, datetime):
                self.created_at = datetime.combine(datum, datetime.min.time())
            else:
                self.created_at = datum
        else:
            self.created_at = datetime.now()
        self.sent_at: datetime | None = None
        self.read_at: datetime | None = None

    @event("Sent")
    def mark_sent(self) -> None:
        """Bericht verzonden (AWB Art. 3:41 - bekendmaking)"""
        self.status = MessageStatus.SENT
        self.sent_at = datetime.now()

    @event("Read")
    def mark_read(self) -> None:
        """Bericht gelezen door burger"""
        self.status = MessageStatus.READ
        self.read_at = datetime.now()

    @event("Archived")
    def archive(self) -> None:
        """Bericht gearchiveerd door burger"""
        self.status = MessageStatus.ARCHIVED

    @property
    def is_unread(self) -> bool:
        """Check of het bericht nog niet gelezen is"""
        return self.status in [MessageStatus.CREATED, MessageStatus.SENT]

    @property
    def is_beschikking(self) -> bool:
        """Check of dit bericht een beschikking is (rechtsmiddel van toepassing)"""
        return self.message_type in [
            MessageType.VOORSCHOT_BESCHIKKING,
            MessageType.DEFINITIEVE_BESCHIKKING,
            MessageType.AFWIJZING,
        ]
