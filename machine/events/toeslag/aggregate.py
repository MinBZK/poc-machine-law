"""
Toeslag Aggregate

Representeert de staat van een toeslag voor een burger voor een specifiek berekeningsjaar.
Bijvoorbeeld: de zorgtoeslag van burger 123456789 voor het jaar 2025.

Het object is generiek (volgt AWIR-proces) maar heeft een specifiek type dat aangeeft
welke toeslag het is (ZORGTOESLAG, HUURTOESLAG, etc.).

Deze aggregate volgt het AWIR-proces:
1. Aanvraag ingediend
2. Aanspraak berekend
3. Voorschotbeschikking vastgesteld
4. Maandelijkse herberekeningen en betalingen
5. Definitieve beschikking
6. Vereffening (nabetaling of terugvordering)
"""

from datetime import date, datetime
from enum import Enum
from typing import Any

from eventsourcing.domain import Aggregate, event


class ToeslagType(str, Enum):
    """Type toeslag - bepaalt welke regeling wordt gebruikt"""

    ZORGTOESLAG = "ZORGTOESLAG"
    HUURTOESLAG = "HUURTOESLAG"
    KINDGEBONDEN_BUDGET = "KINDGEBONDEN_BUDGET"
    KINDEROPVANGTOESLAG = "KINDEROPVANGTOESLAG"


# Mapping van type naar regeling (wet)
TOESLAG_TYPE_REGELING = {
    ToeslagType.ZORGTOESLAG: "zorgtoeslagwet",
    ToeslagType.HUURTOESLAG: "wet_op_de_huurtoeslag",
    ToeslagType.KINDGEBONDEN_BUDGET: "wet_op_het_kindgebonden_budget",
    ToeslagType.KINDEROPVANGTOESLAG: "wet_kinderopvang",
}


class ToeslagStatus(str, Enum):
    """Status van de toeslag in het AWIR-proces"""

    AANVRAAG = "AANVRAAG"
    BEREKEND = "BEREKEND"
    VOORSCHOT = "VOORSCHOT"
    LOPEND = "LOPEND"  # Maandelijkse cyclus actief
    DEFINITIEF = "DEFINITIEF"
    VEREFFEND = "VEREFFEND"
    AFGEWEZEN = "AFGEWEZEN"
    BEEINDIGD = "BEEINDIGD"


class Toeslag(Aggregate):
    """
    De staat van een toeslag voor een burger voor een specifiek jaar.

    Identifier (oid): UUID van het aggregate
    Business key: BSN + type + berekeningsjaar
    Bijvoorbeeld: 123456789 + ZORGTOESLAG + 2025
    """

    @event("AanvraagIngediend")
    def __init__(
        self,
        bsn: str,
        toeslag_type: ToeslagType,
        berekeningsjaar: int,
        aanvraag_datum: date | None = None,
    ) -> None:
        """Burger dient aanvraag in voor toeslag (AWIR Art. 15)"""
        self.bsn = bsn
        self.type = toeslag_type
        self.regeling = TOESLAG_TYPE_REGELING[toeslag_type]
        self.berekeningsjaar = berekeningsjaar
        # Store as ISO string for eventsourcing serialization
        if aanvraag_datum:
            self.aanvraag_datum = aanvraag_datum if isinstance(aanvraag_datum, str) else aanvraag_datum.isoformat()
        else:
            self.aanvraag_datum = date.today().isoformat()

        self.status = ToeslagStatus.AANVRAAG

        # Berekende aanspraak
        self.heeft_aanspraak: bool | None = None
        self.berekend_jaarbedrag: int | None = None  # in eurocent

        # Voorschot
        self.voorschot_jaarbedrag: int | None = None
        self.voorschot_maandbedrag: int | None = None
        self.voorschot_beschikking_datum: date | None = None

        # Maandelijkse gegevens
        self.huidige_maand: int = 0
        self.maandelijkse_berekeningen: list[dict[str, Any]] = []
        self.maandelijkse_betalingen: list[dict[str, Any]] = []

        # Definitieve afrekening
        self.definitief_jaarbedrag: int | None = None
        self.definitieve_beschikking_datum: date | None = None

        # Vereffening
        self.vereffening_type: str | None = None  # NABETALING, TERUGVORDERING, GEEN
        self.vereffening_bedrag: int | None = None

        # Beschikkingen historie
        self.beschikkingen: list[dict[str, Any]] = []

        # Metadata
        self.created_at = datetime.now()

    @property
    def oid(self) -> str:
        """
        Object Identifier (OID) - gestructureerde identificatie van deze toeslag.

        Format: NL.TOESLAGEN.{TYPE}.{BSN}.{JAAR}
        Voorbeeld: NL.TOESLAGEN.ZORGTOESLAG.123456789.2025

        Dit is een leesbare business identifier, naast de technische UUID (self.id).
        """
        # Type kan een ToeslagType enum of string zijn (na event sourcing)
        type_value = self.type.value if isinstance(self.type, ToeslagType) else self.type
        return f"NL.TOESLAGEN.{type_value}.{self.bsn}.{self.berekeningsjaar}"

    @event("AanspraakBerekend")
    def bereken_aanspraak(
        self,
        heeft_aanspraak: bool,
        berekend_jaarbedrag: int,
        berekening_datum: date | None = None,
        berekening_details: dict[str, Any] | None = None,
    ) -> None:
        """Aanspraak op toeslag berekend (AWIR Art. 16 lid 1)"""
        self.heeft_aanspraak = heeft_aanspraak
        self.berekend_jaarbedrag = berekend_jaarbedrag
        self.status = ToeslagStatus.BEREKEND

    @event("Afgewezen")
    def wijs_af(
        self,
        reden: str,
        afwijzing_datum: date | None = None,
    ) -> None:
        """Aanvraag afgewezen wegens geen aanspraak (AWIR Art. 16 lid 4)"""
        self.status = ToeslagStatus.AFGEWEZEN
        self.beschikkingen.append(
            {
                "type": "AFWIJZING",
                "datum": afwijzing_datum or date.today(),
                "reden": reden,
            }
        )

    @event("VoorschotBeschikkingVastgesteld")
    def stel_voorschot_vast(
        self,
        jaarbedrag: int,
        maandbedrag: int,
        beschikking_datum: date | None = None,
    ) -> None:
        """Voorschotbeschikking vastgesteld (AWIR Art. 16)"""
        self.voorschot_jaarbedrag = jaarbedrag
        self.voorschot_maandbedrag = maandbedrag
        self.voorschot_beschikking_datum = beschikking_datum or date.today()
        self.status = ToeslagStatus.VOORSCHOT

        self.beschikkingen.append(
            {
                "type": "VOORSCHOT",
                "datum": self.voorschot_beschikking_datum,
                "jaarbedrag": jaarbedrag,
                "maandbedrag": maandbedrag,
            }
        )

    @event("MaandGestart")
    def start_maand(self, maand: int) -> None:
        """Start van een nieuwe maand in het toeslagjaar"""
        self.huidige_maand = maand
        if self.status == ToeslagStatus.VOORSCHOT:
            self.status = ToeslagStatus.LOPEND

    @event("MaandHerberekend")
    def herbereken_maand(
        self,
        maand: int,
        berekend_bedrag: int,
        berekening_datum: date | None = None,
        trigger: str = "schedule",  # "schedule" of "data_change"
        gewijzigde_data: list[str] | None = None,
    ) -> None:
        """Maandelijkse herberekening uitgevoerd (AWIR Art. 16 lid 5, Art. 17)"""
        self.maandelijkse_berekeningen.append(
            {
                "maand": maand,
                "berekend_bedrag": berekend_bedrag,
                "berekening_datum": berekening_datum or date.today(),
                "trigger": trigger,
                "gewijzigde_data": gewijzigde_data or [],
            }
        )

    @event("MaandBetaald")
    def betaal_maand(
        self,
        maand: int,
        betaald_bedrag: int,
        betaal_datum: date | None = None,
        basis: str = "voorschot",  # "voorschot" of "herzien"
    ) -> None:
        """Maandelijkse betaling uitgevoerd (AWIR Art. 22)"""
        self.maandelijkse_betalingen.append(
            {
                "maand": maand,
                "betaald_bedrag": betaald_bedrag,
                "betaal_datum": betaal_datum or date.today(),
                "basis": basis,
            }
        )

    @event("VoorschotHerzien")
    def herzien_voorschot(
        self,
        nieuw_jaarbedrag: int,
        nieuw_maandbedrag: int,
        reden: str,
        herzien_datum: date | None = None,
    ) -> None:
        """Voorschot herzien na wijziging (AWIR Art. 16 lid 5)"""
        self.voorschot_jaarbedrag = nieuw_jaarbedrag
        self.voorschot_maandbedrag = nieuw_maandbedrag

        self.beschikkingen.append(
            {
                "type": "HERZIEN_VOORSCHOT",
                "datum": herzien_datum or date.today(),
                "jaarbedrag": nieuw_jaarbedrag,
                "maandbedrag": nieuw_maandbedrag,
                "reden": reden,
            }
        )

    @event("DefinitieveBeschikkingVastgesteld")
    def stel_definitief_vast(
        self,
        definitief_jaarbedrag: int,
        beschikking_datum: date | None = None,
    ) -> None:
        """Definitieve beschikking vastgesteld (AWIR Art. 19)"""
        self.definitief_jaarbedrag = definitief_jaarbedrag
        self.definitieve_beschikking_datum = beschikking_datum or date.today()
        self.status = ToeslagStatus.DEFINITIEF

        self.beschikkingen.append(
            {
                "type": "DEFINITIEF",
                "datum": self.definitieve_beschikking_datum,
                "jaarbedrag": definitief_jaarbedrag,
            }
        )

    @event("Vereffend")
    def vereffen(
        self,
        vereffening_type: str,  # "NABETALING", "TERUGVORDERING", "GEEN"
        vereffening_bedrag: int,
        vereffening_datum: date | None = None,
    ) -> None:
        """Vereffening uitgevoerd (AWIR Art. 24, Art. 26a)"""
        self.vereffening_type = vereffening_type
        self.vereffening_bedrag = vereffening_bedrag
        self.status = ToeslagStatus.VEREFFEND

        self.beschikkingen.append(
            {
                "type": f"VEREFFENING_{vereffening_type}",
                "datum": vereffening_datum or date.today(),
                "bedrag": vereffening_bedrag,
            }
        )

    @event("Beeindigd")
    def beeindig(self, reden: str, einddatum: date | None = None) -> None:
        """Toeslag beëindigd (bijv. geen voortzetting volgend jaar)"""
        self.status = ToeslagStatus.BEEINDIGD

    # Helper properties

    @property
    def totaal_betaald(self) -> int:
        """Som van alle betaalde bedragen"""
        return sum(b["betaald_bedrag"] for b in self.maandelijkse_betalingen)

    @property
    def totaal_berekend(self) -> int:
        """Som van alle herberekende bedragen"""
        return sum(b["berekend_bedrag"] for b in self.maandelijkse_berekeningen)

    @property
    def verschil_met_voorschot(self) -> int | None:
        """Verschil tussen herberekend en voorschot (positief = nabetaling)"""
        if self.definitief_jaarbedrag is None:
            return None
        return self.definitief_jaarbedrag - self.totaal_betaald

    def get_berekening_voor_maand(self, maand: int) -> dict[str, Any] | None:
        """Haal de laatste berekening op voor een specifieke maand"""
        for b in reversed(self.maandelijkse_berekeningen):
            if b["maand"] == maand:
                return b
        return None

    def get_betaling_voor_maand(self, maand: int) -> dict[str, Any] | None:
        """Haal de betaling op voor een specifieke maand"""
        for b in self.maandelijkse_betalingen:
            if b["maand"] == maand:
                return b
        return None
