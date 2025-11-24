"""
ToeslagApplication - Application service voor het beheren van toeslagen.

Beheert de levenscyclus van een toeslag voor een burger per berekeningsjaar,
volgens het AWIR-proces.
"""

from datetime import date
from typing import Any
from uuid import UUID

from eventsourcing.application import Application

from .aggregate import Toeslag, ToeslagStatus, ToeslagType, TOESLAG_TYPE_REGELING


class ToeslagApplication(Application):
    """
    Application service voor het beheren van toeslagen per burger per jaar.

    Volgt het AWIR-proces:
    1. Aanvraag indienen
    2. Aanspraak berekenen
    3. Voorschotbeschikking vaststellen
    4. Maandelijkse herberekeningen en betalingen
    5. Definitieve beschikking
    6. Vereffening
    """

    def __init__(self, rules_engine=None, **kwargs) -> None:
        super().__init__(**kwargs)
        self.rules_engine = rules_engine
        # Index: (bsn, toeslag_type, berekeningsjaar) -> toeslag_id
        self._toeslag_index: dict[tuple[str, ToeslagType, int], str] = {}

    @staticmethod
    def _index_key(bsn: str, toeslag_type: ToeslagType, berekeningsjaar: int) -> tuple[str, ToeslagType, int]:
        """Generate index key"""
        return (bsn, toeslag_type, berekeningsjaar)

    def _index_toeslag(self, toeslag: Toeslag) -> None:
        """Add toeslag to index"""
        key = self._index_key(toeslag.bsn, toeslag.type, toeslag.berekeningsjaar)
        self._toeslag_index[key] = str(toeslag.id)

    # === Aanvraag fase ===

    def dien_aanvraag_in(
        self,
        bsn: str,
        toeslag_type: ToeslagType,
        berekeningsjaar: int,
        aanvraag_datum: date | None = None,
    ) -> str:
        """
        Dien een aanvraag in voor een toeslag (AWIR Art. 15).

        Args:
            bsn: BSN van de aanvrager
            toeslag_type: Type toeslag (ZORGTOESLAG, HUURTOESLAG, etc.)
            berekeningsjaar: Het jaar waarvoor de toeslag wordt aangevraagd
            aanvraag_datum: Datum van aanvraag (default: vandaag)

        Returns:
            OID van de nieuwe Toeslag
        """
        # Check of er al een toeslag bestaat voor deze combinatie
        bestaande = self.get_toeslag(bsn, toeslag_type, berekeningsjaar)
        if bestaande is not None:
            raise ValueError(
                f"Er bestaat al een toeslag voor BSN {bsn}, {toeslag_type.value}, jaar {berekeningsjaar}"
            )

        toeslag = Toeslag(
            bsn=bsn,
            toeslag_type=toeslag_type,
            berekeningsjaar=berekeningsjaar,
            aanvraag_datum=aanvraag_datum,
        )

        self.save(toeslag)
        self._index_toeslag(toeslag)

        return str(toeslag.id)

    def bereken_aanspraak(
        self,
        toeslag_id: str,
        heeft_aanspraak: bool,
        berekend_jaarbedrag: int,
        berekening_datum: date | None = None,
        berekening_details: dict[str, Any] | None = None,
    ) -> str:
        """
        Bereken de aanspraak op toeslag (AWIR Art. 16 lid 1).

        Als de burger geen aanspraak heeft, wordt de aanvraag afgewezen.

        Args:
            toeslag_id: ID van de toeslag
            heeft_aanspraak: Of de burger recht heeft op toeslag
            berekend_jaarbedrag: Het berekende jaarbedrag in eurocent
            berekening_datum: Datum van berekening
            berekening_details: Extra details van de berekening

        Returns:
            ID van de toeslag
        """
        toeslag = self.get_toeslag_by_id(toeslag_id)

        toeslag.bereken_aanspraak(
            heeft_aanspraak=heeft_aanspraak,
            berekend_jaarbedrag=berekend_jaarbedrag,
            berekening_datum=berekening_datum,
            berekening_details=berekening_details,
        )

        if not heeft_aanspraak:
            toeslag.wijs_af(reden="Geen aanspraak op toeslag")

        self.save(toeslag)
        return str(toeslag.id)

    # === Voorschot fase ===

    def stel_voorschot_vast(
        self,
        toeslag_id: str,
        jaarbedrag: int | None = None,
        beschikking_datum: date | None = None,
    ) -> str:
        """
        Stel de voorschotbeschikking vast (AWIR Art. 16).

        Args:
            toeslag_id: ID van de toeslag
            jaarbedrag: Het voorschotbedrag (default: berekend jaarbedrag)
            beschikking_datum: Datum van beschikking

        Returns:
            ID van de toeslag
        """
        toeslag = self.get_toeslag_by_id(toeslag_id)

        if toeslag.status == ToeslagStatus.AFGEWEZEN:
            raise ValueError("Kan geen voorschot vaststellen voor afgewezen aanvraag")

        # Gebruik berekend bedrag als geen specifiek bedrag is opgegeven
        if jaarbedrag is None:
            jaarbedrag = toeslag.berekend_jaarbedrag

        if jaarbedrag is None:
            raise ValueError("Geen jaarbedrag beschikbaar voor voorschot")

        # Bereken maandbedrag (jaarbedrag / 12, afgerond)
        maandbedrag = jaarbedrag // 12

        toeslag.stel_voorschot_vast(
            jaarbedrag=jaarbedrag,
            maandbedrag=maandbedrag,
            beschikking_datum=beschikking_datum,
        )

        self.save(toeslag)
        return str(toeslag.id)

    # === Maandelijkse cyclus ===

    def start_maand(self, toeslag_id: str, maand: int) -> str:
        """Start een nieuwe maand in het toeslagjaar"""
        toeslag = self.get_toeslag_by_id(toeslag_id)
        toeslag.start_maand(maand)
        self.save(toeslag)
        return str(toeslag.id)

    def herbereken_maand(
        self,
        toeslag_id: str,
        maand: int,
        berekend_bedrag: int,
        berekening_datum: date | None = None,
        trigger: str = "schedule",
        gewijzigde_data: list[str] | None = None,
    ) -> str:
        """
        Voer maandelijkse herberekening uit (AWIR Art. 16 lid 5, Art. 17).

        Args:
            toeslag_id: ID van de toeslag
            maand: De maand (1-12)
            berekend_bedrag: Het herberekende maandbedrag in eurocent
            berekening_datum: Datum van berekening
            trigger: Wat triggerde de herberekening ("schedule" of "data_change")
            gewijzigde_data: Lijst van gewijzigde datavelden (bij data_change)

        Returns:
            ID van de toeslag
        """
        toeslag = self.get_toeslag_by_id(toeslag_id)

        toeslag.herbereken_maand(
            maand=maand,
            berekend_bedrag=berekend_bedrag,
            berekening_datum=berekening_datum,
            trigger=trigger,
            gewijzigde_data=gewijzigde_data,
        )

        self.save(toeslag)
        return str(toeslag.id)

    def betaal_maand(
        self,
        toeslag_id: str,
        maand: int,
        betaald_bedrag: int | None = None,
        betaal_datum: date | None = None,
        basis: str = "voorschot",
    ) -> str:
        """
        Voer maandelijkse betaling uit (AWIR Art. 22).

        Args:
            toeslag_id: ID van de toeslag
            maand: De maand (1-12)
            betaald_bedrag: Het betaalde bedrag (default: voorschot maandbedrag)
            betaal_datum: Datum van betaling
            basis: Op basis van welke beschikking ("voorschot" of "herzien")

        Returns:
            ID van de toeslag
        """
        toeslag = self.get_toeslag_by_id(toeslag_id)

        # Gebruik voorschot maandbedrag als geen specifiek bedrag is opgegeven
        if betaald_bedrag is None:
            betaald_bedrag = toeslag.voorschot_maandbedrag

        if betaald_bedrag is None:
            raise ValueError("Geen betaalbedrag beschikbaar")

        toeslag.betaal_maand(
            maand=maand,
            betaald_bedrag=betaald_bedrag,
            betaal_datum=betaal_datum,
            basis=basis,
        )

        self.save(toeslag)
        return str(toeslag.id)

    def herzien_voorschot(
        self,
        toeslag_id: str,
        nieuw_jaarbedrag: int,
        reden: str,
        herzien_datum: date | None = None,
    ) -> str:
        """
        Herzien het voorschot (AWIR Art. 16 lid 5).

        Args:
            toeslag_id: ID van de toeslag
            nieuw_jaarbedrag: Het nieuwe jaarbedrag
            reden: Reden voor herziening
            herzien_datum: Datum van herziening

        Returns:
            ID van de toeslag
        """
        toeslag = self.get_toeslag_by_id(toeslag_id)

        nieuw_maandbedrag = nieuw_jaarbedrag // 12

        toeslag.herzien_voorschot(
            nieuw_jaarbedrag=nieuw_jaarbedrag,
            nieuw_maandbedrag=nieuw_maandbedrag,
            reden=reden,
            herzien_datum=herzien_datum,
        )

        self.save(toeslag)
        return str(toeslag.id)

    # === Definitieve beschikking ===

    def stel_definitief_vast(
        self,
        toeslag_id: str,
        definitief_jaarbedrag: int,
        beschikking_datum: date | None = None,
    ) -> str:
        """
        Stel de definitieve beschikking vast (AWIR Art. 19).

        Args:
            toeslag_id: ID van de toeslag
            definitief_jaarbedrag: Het definitieve jaarbedrag
            beschikking_datum: Datum van beschikking

        Returns:
            ID van de toeslag
        """
        toeslag = self.get_toeslag_by_id(toeslag_id)

        toeslag.stel_definitief_vast(
            definitief_jaarbedrag=definitief_jaarbedrag,
            beschikking_datum=beschikking_datum,
        )

        self.save(toeslag)
        return str(toeslag.id)

    def vereffen(
        self,
        toeslag_id: str,
        vereffening_datum: date | None = None,
    ) -> str:
        """
        Voer vereffening uit (AWIR Art. 24, Art. 26a).

        Berekent automatisch of er een nabetaling of terugvordering is.

        Args:
            toeslag_id: ID van de toeslag
            vereffening_datum: Datum van vereffening

        Returns:
            ID van de toeslag
        """
        toeslag = self.get_toeslag_by_id(toeslag_id)

        if toeslag.definitief_jaarbedrag is None:
            raise ValueError("Kan niet vereffenen zonder definitief jaarbedrag")

        verschil = toeslag.definitief_jaarbedrag - toeslag.totaal_betaald

        if verschil > 0:
            vereffening_type = "NABETALING"
        elif verschil < 0:
            vereffening_type = "TERUGVORDERING"
        else:
            vereffening_type = "GEEN"

        toeslag.vereffen(
            vereffening_type=vereffening_type,
            vereffening_bedrag=abs(verschil),
            vereffening_datum=vereffening_datum,
        )

        self.save(toeslag)
        return str(toeslag.id)

    # === Query methods ===

    def get_toeslag(
        self, bsn: str, toeslag_type: ToeslagType, berekeningsjaar: int
    ) -> Toeslag | None:
        """Haal toeslag op voor specifieke combinatie van bsn, type en jaar"""
        key = self._index_key(bsn, toeslag_type, berekeningsjaar)
        toeslag_id = self._toeslag_index.get(key)
        return self.get_toeslag_by_id(toeslag_id) if toeslag_id else None

    def get_toeslag_by_oid(self, oid: str) -> Toeslag | None:
        """
        Haal toeslag op via OID (Object Identifier).

        OID format: NL.TOESLAGEN.{TYPE}.{BSN}.{JAAR}
        Voorbeeld: NL.TOESLAGEN.ZORGTOESLAG.123456789.2025
        """
        # Parse de OID
        parts = oid.split(".")
        if len(parts) != 5 or parts[0] != "NL" or parts[1] != "TOESLAGEN":
            return None

        try:
            toeslag_type = ToeslagType(parts[2])
            bsn = parts[3]
            berekeningsjaar = int(parts[4])
            return self.get_toeslag(bsn, toeslag_type, berekeningsjaar)
        except (ValueError, KeyError):
            return None

    def get_toeslag_by_id(self, toeslag_id: str | UUID | None) -> Toeslag | None:
        """Haal toeslag op via ID"""
        if not toeslag_id:
            return None

        if isinstance(toeslag_id, str):
            toeslag_id = UUID(toeslag_id)

        return self.repository.get(toeslag_id)

    def get_toeslagen_by_bsn(self, bsn: str) -> list[Toeslag]:
        """Haal alle toeslagen op voor een burger"""
        toeslagen = []
        for key_tuple, toeslag_id in self._toeslag_index.items():
            key_bsn, _, _ = key_tuple
            if key_bsn == bsn:
                toeslag = self.get_toeslag_by_id(toeslag_id)
                if toeslag:
                    toeslagen.append(toeslag)
        return toeslagen

    def get_toeslagen_by_type(
        self, toeslag_type: ToeslagType, berekeningsjaar: int | None = None
    ) -> list[Toeslag]:
        """Haal alle toeslagen op van een bepaald type (optioneel gefilterd op jaar)"""
        toeslagen = []
        for key_tuple, toeslag_id in self._toeslag_index.items():
            _, key_type, key_jaar = key_tuple
            if key_type == toeslag_type:
                if berekeningsjaar is None or key_jaar == berekeningsjaar:
                    toeslag = self.get_toeslag_by_id(toeslag_id)
                    if toeslag:
                        toeslagen.append(toeslag)
        return toeslagen

    def get_toeslagen_by_status(self, status: ToeslagStatus) -> list[Toeslag]:
        """Haal alle toeslagen op met een bepaalde status"""
        toeslagen = []
        for toeslag_id in self._toeslag_index.values():
            toeslag = self.get_toeslag_by_id(toeslag_id)
            if toeslag and toeslag.status == status:
                toeslagen.append(toeslag)
        return toeslagen
