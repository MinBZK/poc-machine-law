from uuid import UUID

from eventsourcing.application import Application

from .aggregate import Message, MessageStatus, MessageType


class MessageManager(Application):
    """
    Application service voor het beheren van berichten aan burgers.

    Wettelijke grondslag:
    - AWIR Art. 13: Elektronisch berichtenverkeer
    - AWB Art. 3:40-3:45: Bekendmaking besluiten
    """

    def __init__(self, **kwargs) -> None:
        super().__init__(**kwargs)
        # Index: bsn -> set of message_ids
        self._bsn_index: dict[str, set[str]] = {}
        # Index: case_id -> set of message_ids
        self._case_index: dict[str, set[str]] = {}

    def _index_message(self, message: Message) -> None:
        """Add message to indices"""
        message_id = str(message.id)

        # BSN index
        if message.bsn not in self._bsn_index:
            self._bsn_index[message.bsn] = set()
        self._bsn_index[message.bsn].add(message_id)

        # Case index
        if message.case_id not in self._case_index:
            self._case_index[message.case_id] = set()
        self._case_index[message.case_id].add(message_id)

    def create_message(
        self,
        bsn: str,
        case_id: str,
        message_type: str,
        onderwerp: str,
        inhoud: str,
        rechtsmiddel_info: str | None = None,
        law: str | None = None,
        created_at=None,
    ) -> str:
        """
        Maak een nieuw bericht aan voor een burger.

        Args:
            bsn: BSN van de burger
            case_id: ID van de gerelateerde zaak
            message_type: Type bericht (VOORSCHOT_BESCHIKKING, DEFINITIEVE_BESCHIKKING, AFWIJZING)
            onderwerp: Onderwerp van het bericht
            inhoud: Inhoud van het bericht
            rechtsmiddel_info: Optionele rechtsmiddelenclausule (AWB Art. 3:45)
            law: Optionele wet identifier (bijv. "huurtoeslag", "zorgtoeslag")
            created_at: Optional timestamp for the message creation (defaults to now)

        Returns:
            ID van het aangemaakte bericht
        """
        message = Message(
            bsn=bsn,
            case_id=case_id,
            message_type=MessageType(message_type),
            onderwerp=onderwerp,
            inhoud=inhoud,
            rechtsmiddel_info=rechtsmiddel_info,
            law=law,
            created_at=created_at,
        )

        # Markeer direct als verzonden (AWB Art. 3:41)
        message.mark_sent(sent_at=created_at)

        self.save(message)
        self._index_message(message)

        return str(message.id)

    def get_message_by_id(self, message_id: str | UUID | None) -> Message | None:
        """Haal bericht op basis van ID"""
        if not message_id:
            return None

        if isinstance(message_id, str):
            message_id = UUID(message_id)

        return self.repository.get(message_id)

    def get_messages_by_bsn(self, bsn: str, include_archived: bool = False) -> list[Message]:
        """
        Haal alle berichten op voor een burger.

        Args:
            bsn: BSN van de burger
            include_archived: Of gearchiveerde berichten meegenomen moeten worden

        Returns:
            Lijst van berichten, gesorteerd op aanmaakdatum (nieuwste eerst)
        """
        message_ids = self._bsn_index.get(bsn, set())
        messages = []

        for message_id in message_ids:
            message = self.get_message_by_id(message_id)
            if message and (include_archived or message.status != MessageStatus.ARCHIVED):
                messages.append(message)

        # Sorteer op aanmaakdatum, nieuwste eerst
        return sorted(messages, key=lambda m: m.created_at, reverse=True)

    def get_messages_by_case(self, case_id: str) -> list[Message]:
        """
        Haal alle berichten op voor een specifieke zaak.

        Args:
            case_id: ID van de zaak

        Returns:
            Lijst van berichten, gesorteerd op aanmaakdatum
        """
        message_ids = self._case_index.get(case_id, set())
        messages = []

        for message_id in message_ids:
            message = self.get_message_by_id(message_id)
            if message:
                messages.append(message)

        return sorted(messages, key=lambda m: m.created_at, reverse=True)

    def get_unread_count(self, bsn: str) -> int:
        """
        Haal het aantal ongelezen berichten op voor een burger.

        Args:
            bsn: BSN van de burger

        Returns:
            Aantal ongelezen berichten
        """
        messages = self.get_messages_by_bsn(bsn)
        return sum(1 for m in messages if m.is_unread)

    def mark_as_read(self, message_id: str) -> None:
        """
        Markeer een bericht als gelezen.

        Args:
            message_id: ID van het bericht
        """
        message = self.get_message_by_id(message_id)
        if message and message.is_unread:
            message.mark_read()
            self.save(message)

    def archive_message(self, message_id: str) -> None:
        """
        Archiveer een bericht.

        Args:
            message_id: ID van het bericht
        """
        message = self.get_message_by_id(message_id)
        if message and message.status != MessageStatus.ARCHIVED:
            message.archive()
            self.save(message)
