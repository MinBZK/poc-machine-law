"""
TimeSimulator - Simuleert tijdsverloop voor toeslagen.

Maakt het mogelijk om tijd te laten verstrijken in intervals (maanden),
waarbij bij elk interval automatisch herberekeningen en betalingsverplichtingen
worden aangemaakt.
"""

import logging
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import date
from typing import TYPE_CHECKING, Any

from dateutil.relativedelta import relativedelta

from machine.events.case.aggregate import CaseStatus

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from machine.events.case.application import CaseManager
    from machine.events.message.application import MessageManager
    from machine.service import Services


@dataclass
class MonthResult:
    """Resultaat van een maandelijkse verwerking"""

    maand: int
    reference_date: date
    berekend_bedrag: int
    betaald_bedrag: int
    trigger: str = "schedule"
    gewijzigde_data: list[str] = field(default_factory=list)


@dataclass
class YearResult:
    """Resultaat van een volledige jaarverwerking"""

    berekeningsjaar: int
    maanden: list[MonthResult] = field(default_factory=list)
    totaal_berekend: int = 0
    totaal_betaald: int = 0

    def add_month(self, month_result: MonthResult) -> None:
        self.maanden.append(month_result)
        self.totaal_berekend += month_result.berekend_bedrag
        self.totaal_betaald += month_result.betaald_bedrag


class TimeSimulator:
    """
    Simuleert het verstrijken van tijd voor toeslag verwerking.

    Verantwoordelijkheden:
    - Tijdvoortgang per maand
    - Automatische herberekening via rules engine
    - Aanmaken betalingsverplichtingen
    - Bijhouden van maandresultaten

    Usage:
        simulator = TimeSimulator(
            services_factory=lambda date: Services(date),
            case_manager=context.services.case_manager,
            start_date=date(2025, 1, 1)
        )

        # Verwerk 6 maanden
        results = simulator.advance_months(
            case_id=case_uuid,
            months=6,
            parameters={"BSN": "123456789"}
        )

        # Of verwerk een heel jaar
        year_result = simulator.run_full_year(
            case_id=case_uuid,
            parameters={"BSN": "123456789"}
        )
    """

    def __init__(
        self,
        case_manager: "CaseManager",
        start_date: date,
        services_factory: Callable[[str], "Services"] | None = None,
        services: "Services | None" = None,
        message_manager: "MessageManager | None" = None,
    ) -> None:
        """
        Initialiseer de simulator.

        Args:
            case_manager: De CaseManager voor state management
            start_date: Startdatum voor de simulatie
            services_factory: Factory functie die een Services instance maakt voor een datum (optioneel)
            services: Directe Services instance (optioneel, heeft voorrang boven factory)
            message_manager: De MessageManager voor berichten generatie (optioneel)
        """
        self.services_factory = services_factory
        self._services: Services | None = services
        self.case_manager = case_manager
        self.message_manager: MessageManager | None = message_manager
        self.current_date = start_date
        self._initial_start_date = start_date  # Store for reference in step_to_date

    @property
    def services(self) -> "Services":
        """Huidige Services instance voor de huidige datum"""
        if self._services is None:
            if self.services_factory is None:
                raise ValueError("No services or services_factory provided")
            self._services = self.services_factory(self.current_date.isoformat())
        return self._services

    def _advance_date(self, months: int = 1) -> None:
        """Verschuif de huidige datum met N maanden"""
        self.current_date = self.current_date + relativedelta(months=months)
        # Only invalidate if using factory - direct services instance blijft behouden
        if self.services_factory is not None:
            self._services = None

    def _evaluate_case(
        self,
        case_id: str,
        parameters: dict[str, Any],
    ) -> dict[str, Any]:
        """
        Evalueer de toeslag via de rules engine.

        Returns:
            Dict met berekende waarden (hoogte_toeslag, heeft_recht, etc.)
        """
        case = self.case_manager.get_case_by_id(case_id)
        if case is None:
            raise ValueError(f"Case niet gevonden: {case_id}")

        result = self.services.evaluate(
            service="TOESLAGEN",
            law=case.law,
            parameters=parameters,
            reference_date=self.current_date.isoformat(),
        )

        return {
            "hoogte_toeslag": result.output.get("hoogte_toeslag", 0),
            "heeft_recht": result.requirements_met,
            "output": result.output,
        }

    def process_month(
        self,
        case_id: str,
        maand: int,
        parameters: dict[str, Any],
        trigger: str = "schedule",
        gewijzigde_data: list[str] | None = None,
    ) -> MonthResult:
        """
        Verwerk een enkele maand: herberekening + betaling.

        Args:
            case_id: ID van de case
            maand: Maandnummer (1-12)
            parameters: Parameters voor de rules engine (moet BSN bevatten)
            trigger: Trigger type ("schedule" of "data_change")
            gewijzigde_data: Lijst van gewijzigde velden (bij data_change)

        Returns:
            MonthResult met de verwerkte gegevens
        """
        # Evalueer de toeslag voor deze maand
        evaluation = self._evaluate_case(case_id, parameters)

        # Bereken maandbedrag (jaarbedrag / 12)
        jaarbedrag = evaluation["hoogte_toeslag"]
        maandbedrag = jaarbedrag // 12 if jaarbedrag else 0

        # Herberekening registreren
        self.case_manager.herbereken_maand(
            case_id=case_id,
            maand=maand,
            berekend_bedrag=maandbedrag,
            trigger=trigger,
            berekening_datum=self.current_date,  # Use simulated date
        )

        # Betaling uitvoeren (op basis van voorschot, niet herberekening)
        case = self.case_manager.get_case_by_id(case_id)
        betaald_bedrag = case.voorschot_maandbedrag or maandbedrag

        self.case_manager.betaal_maand(
            case_id=case_id,
            maand=maand,
            betaald_bedrag=betaald_bedrag,
            betaal_datum=self.current_date,  # Use simulated date
        )

        return MonthResult(
            maand=maand,
            reference_date=self.current_date,
            berekend_bedrag=maandbedrag,
            betaald_bedrag=betaald_bedrag,
            trigger=trigger,
            gewijzigde_data=gewijzigde_data or [],
        )

    def advance_months(
        self,
        case_id: str,
        months: int,
        parameters: dict[str, Any],
        start_month: int = 1,
    ) -> list[MonthResult]:
        """
        Laat tijd verstrijken voor N maanden met automatische verwerking.

        Args:
            case_id: ID van de case
            months: Aantal maanden om te verwerken
            parameters: Parameters voor de rules engine
            start_month: Startmaand (1-12, default 1)

        Returns:
            Lijst van MonthResult objecten
        """
        results = []

        # Zorg dat de case in LOPEND status is
        case = self.case_manager.get_case_by_id(case_id)
        if case.huidige_maand == 0:
            self.case_manager.start_maand(case_id, start_month)

        for i in range(months):
            maand = start_month + i
            if maand > 12:
                break  # Stop bij einde jaar

            # Verwerk deze maand
            result = self.process_month(
                case_id=case_id,
                maand=maand,
                parameters=parameters,
            )
            results.append(result)

            # Verschuif naar volgende maand (behalve na laatste)
            if i < months - 1:
                self._advance_date(months=1)

        return results

    def advance_to_month(
        self,
        case_id: str,
        target_month: int,
        parameters: dict[str, Any],
    ) -> list[MonthResult]:
        """
        Verwerk alle maanden tot en met de doelmaand.

        Args:
            case_id: ID van de case
            target_month: Doelmaand (1-12)
            parameters: Parameters voor de rules engine

        Returns:
            Lijst van MonthResult objecten
        """
        case = self.case_manager.get_case_by_id(case_id)
        current_month = max(case.huidige_maand, 1)

        if target_month <= current_month:
            return []

        months_to_process = target_month - current_month + 1
        return self.advance_months(
            case_id=case_id,
            months=months_to_process,
            parameters=parameters,
            start_month=current_month,
        )

    def run_full_year(
        self,
        case_id: str,
        parameters: dict[str, Any],
    ) -> YearResult:
        """
        Verwerk een volledig toeslagjaar (12 maanden).

        Args:
            case_id: ID van de case
            parameters: Parameters voor de rules engine

        Returns:
            YearResult met alle maandresultaten
        """
        case = self.case_manager.get_case_by_id(case_id)
        year_result = YearResult(berekeningsjaar=case.berekeningsjaar)

        month_results = self.advance_months(
            case_id=case_id,
            months=12,
            parameters=parameters,
            start_month=1,
        )

        for result in month_results:
            year_result.add_month(result)

        return year_result

    def inject_data_change(
        self,
        case_id: str,
        maand: int,
        parameters: dict[str, Any],
        gewijzigde_data: list[str],
    ) -> MonthResult:
        """
        Simuleer een data-wijziging die een herberekening triggert.

        Args:
            case_id: ID van de case
            maand: Maand waarin de wijziging plaatsvindt
            parameters: Nieuwe parameters voor de berekening
            gewijzigde_data: Lijst van velden die gewijzigd zijn

        Returns:
            MonthResult van de herberekening
        """
        return self.process_month(
            case_id=case_id,
            maand=maand,
            parameters=parameters,
            trigger="data_change",
            gewijzigde_data=gewijzigde_data,
        )

    # === Step-by-step iteration support ===

    def step(
        self,
        case_id: str,
        parameters: dict[str, Any],
    ) -> MonthResult | None:
        """
        Verwerk de volgende maand (step-by-step mode).

        Gebruik dit om door de maanden te stappen in plaats van alles in één keer.

        Args:
            case_id: ID van de case
            parameters: Parameters voor de rules engine

        Returns:
            MonthResult voor de verwerkte maand, of None als het jaar voorbij is
        """
        case = self.case_manager.get_case_by_id(case_id)

        # Bepaal de volgende maand
        next_month = case.huidige_maand + 1 if case.huidige_maand > 0 else 1

        if next_month > 12:
            return None  # Jaar is voorbij

        # Start maand als dit de eerste is
        if case.huidige_maand == 0:
            self.case_manager.start_maand(case_id, next_month)

        # Verwerk de maand
        result = self.process_month(
            case_id=case_id,
            maand=next_month,
            parameters=parameters,
        )

        # Verschuif datum naar volgende maand
        self._advance_date(months=1)

        return result

    def _log_workflow_state(self, case_id: str, action: str = "") -> None:
        """Log de huidige workflow state voor debugging"""
        case = self.case_manager.get_case_by_id(case_id)
        berekende_maanden = sorted([b["maand"] for b in case.maandelijkse_berekeningen])
        betaalde_maanden = sorted([b["maand"] for b in case.maandelijkse_betalingen])
        created_at = case.created_at.date() if hasattr(case, "created_at") and case.created_at else "onbekend"

        logger.debug("╔══════════════════════════════════════════════════════════════")
        logger.debug(f"║ WORKFLOW STATE {action}")
        logger.debug("╠══════════════════════════════════════════════════════════════")
        logger.debug(f"║ Datum:           {self.current_date.isoformat()}")
        logger.debug(f"║ Case ID:         {case_id[:8]}...")
        logger.debug(f"║ Created at:      {created_at}")
        logger.debug(f"║ Status:          {case.status.value}")
        logger.debug(f"║ Huidige maand:   {case.huidige_maand}")
        logger.debug(f"║ Berekend:        maanden {berekende_maanden}")
        logger.debug(f"║ Betaald:         maanden {betaalde_maanden}")
        logger.debug(f"║ Voorschot/jaar:  €{(case.voorschot_jaarbedrag or 0) / 100:.2f}")
        logger.debug(f"║ Voorschot/mnd:   €{(case.voorschot_maandbedrag or 0) / 100:.2f}")
        logger.debug("╚══════════════════════════════════════════════════════════════")

    def _check_year_completion(
        self,
        case_id: str,
        current_date: date,
        parameters: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Controleer of jaarafsluiting nodig is en voer automatisch uit.

        Workflow volgens AWIR:
        1. Na berekeningsjaar (1 april volgend jaar): IB-aanslag simuleren
        2. Na IB-aanslag + 6 maanden: Definitief vaststellen (Art. 19)
        3. Na definitief + 4 weken: Vereffenen (Art. 24)

        Args:
            case_id: ID van de case
            current_date: Huidige gesimuleerde datum
            parameters: Parameters voor herberekening

        Returns:
            Dict met uitgevoerde actie en details, of None als geen actie
        """
        from datetime import timedelta

        case = self.case_manager.get_case_by_id(case_id)

        # Skip als er geen berekeningsjaar is
        if not hasattr(case, "berekeningsjaar") or case.berekeningsjaar is None:
            return None

        volgend_jaar = case.berekeningsjaar + 1

        # =========================================================================
        # Stap 1: IB-aanslag simuleren (1 april volgend jaar)
        # =========================================================================
        ib_aanslag_datum = date(volgend_jaar, 4, 1)
        # IB-aanslag kan worden ontvangen als case LOPEND of VOORSCHOT is
        # VOORSCHOT: case heeft voorschot maar geen maandelijkse verwerking gehad
        # LOPEND: case is in actieve maandelijkse cyclus
        if (
            current_date >= ib_aanslag_datum
            and case.status in {CaseStatus.LOPEND, CaseStatus.VOORSCHOT}
            and case.ib_aanslag_datum is None
        ):
            # Simuleer IB-aanslag met herberekend inkomen
            # We gebruiken het inkomen dat eerder is vastgesteld, of berekenen opnieuw
            vastgesteld_inkomen = self._bereken_werkelijk_inkomen(case_id, parameters)

            logger.debug(f"║ → IB-aanslag simulatie: €{vastgesteld_inkomen / 100:.2f} op {ib_aanslag_datum}")

            self.case_manager.ontvang_ib_aanslag(
                case_id=case_id,
                vastgesteld_inkomen=vastgesteld_inkomen,
                aanslag_datum=ib_aanslag_datum,
            )

            return {
                "actie": "IB_AANSLAG_ONTVANGEN",
                "datum": ib_aanslag_datum,
                "vastgesteld_inkomen": vastgesteld_inkomen,
            }

        # Refresh case na mogelijke IB-aanslag
        case = self.case_manager.get_case_by_id(case_id)

        # =========================================================================
        # Stap 2: Definitief vaststellen (6 maanden na IB-aanslag)
        # =========================================================================
        if (
            hasattr(case, "ib_aanslag_datum")
            and case.ib_aanslag_datum is not None
            and case.status in {CaseStatus.LOPEND, CaseStatus.VOORSCHOT}
            and hasattr(case, "deadline_definitief")
            and case.deadline_definitief is not None
            and current_date >= case.deadline_definitief
        ):
            # Herbereken definitief bedrag op basis van werkelijk inkomen
            definitief_bedrag = self._bereken_definitief_jaarbedrag(case_id, parameters)

            logger.debug(
                f"║ → Definitieve vaststelling: €{definitief_bedrag / 100:.2f} "
                f"(deadline was {case.deadline_definitief})"
            )

            self.case_manager.stel_definitief_vast(
                case_id=case_id,
                definitief_jaarbedrag=definitief_bedrag,
                beschikking_datum=current_date,
            )

            # Genereer bericht voor burger
            self._create_workflow_bericht(
                case_id=case_id,
                bericht_type="DEFINITIEVE_BESCHIKKING",
                details={"definitief_jaarbedrag": definitief_bedrag},
            )

            return {
                "actie": "DEFINITIEF_VASTGESTELD",
                "datum": current_date,
                "definitief_jaarbedrag": definitief_bedrag,
            }

        # Refresh case na mogelijke definitieve vaststelling
        case = self.case_manager.get_case_by_id(case_id)

        # =========================================================================
        # Stap 3: Vereffenen (4 weken na definitieve beschikking)
        # =========================================================================
        if case.status == CaseStatus.DEFINITIEF and case.vereffening_type is None:
            # Bepaal datum van definitieve beschikking
            definitief_datum = None
            if hasattr(case, "beschikkingen") and case.beschikkingen:
                for b in reversed(case.beschikkingen):
                    if b.get("type") == "DEFINITIEF":
                        definitief_datum = b.get("datum")
                        break

            if definitief_datum is None:
                definitief_datum = case.definitieve_beschikking_datum

            if definitief_datum is not None:
                vereffening_deadline = definitief_datum + timedelta(weeks=4)

                if current_date >= vereffening_deadline:
                    logger.debug(f"║ → Vereffening uitvoeren (deadline was {vereffening_deadline})")

                    result = self.case_manager.vereffen(case_id=case_id, vereffening_datum=current_date)

                    # Genereer bericht voor burger
                    if result["type"] == "KWIJTGESCHOLDEN":
                        # Haal de oorspronkelijke case op voor het oorspronkelijke bedrag
                        updated_case = self.case_manager.get_case_by_id(case_id)
                        self._create_workflow_bericht(
                            case_id=case_id,
                            bericht_type="KWIJTSCHELDING_BESCHIKKING",
                            details={
                                "oorspronkelijk_bedrag": result.get("bedrag", 0),
                                "kwijtschelding_reden": getattr(updated_case, "kwijtschelding_reden", "Art. 26a AWIR"),
                            },
                        )
                    else:
                        self._create_workflow_bericht(
                            case_id=case_id,
                            bericht_type="VEREFFENING_BESCHIKKING",
                            details={
                                "vereffening_type": result["type"],
                                "vereffening_bedrag": result["bedrag"],
                            },
                        )

                    return {
                        "actie": "VEREFFEND",
                        "datum": current_date,
                        "vereffening_type": result["type"],
                        "vereffening_bedrag": result["bedrag"],
                    }

        return None

    def _bereken_werkelijk_inkomen(self, case_id: str, parameters: dict[str, Any]) -> int:
        """
        Bereken het werkelijke inkomen voor de IB-aanslag simulatie.

        In een echte situatie zou dit inkomen van de Belastingdienst komen.
        Voor de simulatie gebruiken we het inkomen uit de parameters of
        een herberekening.

        Returns:
            Werkelijk inkomen in eurocent
        """
        # Gebruik het inkomen uit parameters als beschikbaar
        if "inkomen" in parameters:
            return parameters["inkomen"]

        # Anders: haal uit de case of services
        case = self.case_manager.get_case_by_id(case_id)

        # Probeer uit de parameters van de oorspronkelijke aanvraag
        if hasattr(case, "parameters") and case.parameters and "inkomen" in case.parameters:
            return case.parameters["inkomen"]

        # Fallback: evalueer opnieuw
        evaluation = self._evaluate_case(case_id, parameters)
        # Neem het toetsinginkomen uit de output als beschikbaar
        if "toetsingsinkomen" in evaluation.get("output", {}):
            return evaluation["output"]["toetsingsinkomen"]

        # Laatste fallback: gebruik voorschot als basis
        return case.voorschot_jaarbedrag or 0

    def _bereken_definitief_jaarbedrag(self, case_id: str, parameters: dict[str, Any]) -> int:
        """
        Bereken het definitieve jaarbedrag op basis van werkelijk inkomen.

        Dit is de herberekening die plaatsvindt bij definitieve vaststelling.

        Returns:
            Definitief jaarbedrag in eurocent
        """
        case = self.case_manager.get_case_by_id(case_id)

        # Evalueer met het IB-aanslag inkomen als dat beschikbaar is
        if hasattr(case, "ib_aanslag_inkomen") and case.ib_aanslag_inkomen is not None:
            params = {**parameters, "inkomen": case.ib_aanslag_inkomen}
        else:
            params = parameters

        evaluation = self._evaluate_case(case_id, params)

        return evaluation.get("hoogte_toeslag", 0)

    def _create_workflow_bericht(
        self,
        case_id: str,
        bericht_type: str,
        details: dict[str, Any],
    ) -> str | None:
        """
        Genereer een bericht voor een workflow stap.

        Args:
            case_id: ID van de case
            bericht_type: Type bericht (DEFINITIEVE_BESCHIKKING, VEREFFENING_BESCHIKKING, etc.)
            details: Details voor het bericht

        Returns:
            ID van het aangemaakte bericht, of None als message_manager niet beschikbaar is
        """
        if self.message_manager is None:
            logger.debug("║ → Geen message_manager beschikbaar, bericht niet aangemaakt")
            return None

        case = self.case_manager.get_case_by_id(case_id)

        # Bepaal onderwerp en inhoud op basis van type
        if bericht_type == "DEFINITIEVE_BESCHIKKING":
            onderwerp = f"Definitieve beschikking {case.law} {case.berekeningsjaar}"
            definitief_bedrag = details.get("definitief_jaarbedrag", 0)
            inhoud = (
                f"Geachte heer/mevrouw,\n\n"
                f"Hierbij ontvangt u de definitieve beschikking voor uw {case.law} over {case.berekeningsjaar}.\n\n"
                f"Het definitief vastgestelde jaarbedrag is: €{definitief_bedrag / 100:.2f}\n\n"
                f"Dit bedrag is berekend op basis van uw werkelijke inkomen zoals vastgesteld in uw IB-aanslag.\n\n"
                f"Binnen 4 weken ontvangt u bericht over de vereffening.\n\n"
                f"Met vriendelijke groet,\nBelastingdienst/Toeslagen"
            )
            rechtsmiddel_info = (
                "Tegen deze beschikking kunt u binnen 6 weken bezwaar maken. "
                "Zie voor meer informatie: www.toeslagen.nl/bezwaar"
            )

        elif bericht_type == "VEREFFENING_BESCHIKKING":
            onderwerp = f"Vereffening {case.law} {case.berekeningsjaar}"
            vereffening_type = details.get("vereffening_type", "GEEN")
            vereffening_bedrag = details.get("vereffening_bedrag", 0)

            if vereffening_type == "NABETALING":
                inhoud = (
                    f"Geachte heer/mevrouw,\n\n"
                    f"Uit de vereffening van uw {case.law} over {case.berekeningsjaar} blijkt dat u recht heeft op "
                    f"een nabetaling van €{vereffening_bedrag / 100:.2f}.\n\n"
                    f"Dit bedrag wordt binnen 10 werkdagen op uw rekening gestort.\n\n"
                    f"Met vriendelijke groet,\nBelastingdienst/Toeslagen"
                )
            elif vereffening_type == "TERUGVORDERING":
                inhoud = (
                    f"Geachte heer/mevrouw,\n\n"
                    f"Uit de vereffening van uw {case.law} over {case.berekeningsjaar} blijkt dat u "
                    f"€{vereffening_bedrag / 100:.2f} moet terugbetalen.\n\n"
                    f"U ontvangt binnenkort een factuur met betalingsgegevens.\n\n"
                    f"Met vriendelijke groet,\nBelastingdienst/Toeslagen"
                )
            else:
                inhoud = (
                    f"Geachte heer/mevrouw,\n\n"
                    f"Uit de vereffening van uw {case.law} over {case.berekeningsjaar} blijkt dat "
                    f"er geen verschil is tussen het voorschot en het definitieve bedrag.\n\n"
                    f"Er volgt geen nabetaling of terugvordering.\n\n"
                    f"Met vriendelijke groet,\nBelastingdienst/Toeslagen"
                )
            rechtsmiddel_info = (
                "Tegen deze beschikking kunt u binnen 6 weken bezwaar maken. "
                "Zie voor meer informatie: www.toeslagen.nl/bezwaar"
            )

        elif bericht_type == "KWIJTSCHELDING_BESCHIKKING":
            onderwerp = f"Kwijtschelding terugvordering {case.law} {case.berekeningsjaar}"
            oorspronkelijk_bedrag = details.get("oorspronkelijk_bedrag", 0)
            inhoud = (
                f"Geachte heer/mevrouw,\n\n"
                f"Uit de vereffening van uw {case.law} over {case.berekeningsjaar} bleek een "
                f"terugvordering van €{oorspronkelijk_bedrag / 100:.2f}.\n\n"
                f"Omdat dit bedrag onder de doelmatigheidsgrens van €116,00 ligt, wordt deze "
                f"terugvordering kwijtgescholden (AWIR Art. 26a).\n\n"
                f"U hoeft niets terug te betalen.\n\n"
                f"Met vriendelijke groet,\nBelastingdienst/Toeslagen"
            )
            rechtsmiddel_info = None  # Geen bezwaar tegen kwijtschelding nodig

        else:
            logger.warning(f"Onbekend bericht type: {bericht_type}")
            return None

        # Maak het bericht aan
        message_id = self.message_manager.create_message(
            bsn=case.bsn,
            case_id=case_id,
            message_type=bericht_type,
            onderwerp=onderwerp,
            inhoud=inhoud,
            rechtsmiddel_info=rechtsmiddel_info,
            law=case.law,
            created_at=datetime.combine(self.current_date, datetime.min.time()),  # Use simulated date
        )

        logger.debug(f"║ → Bericht aangemaakt: {bericht_type} (ID: {message_id[:8]}...)")
        return message_id

    def step_to_date(
        self,
        case_id: str,
        target_date: date,
        parameters: dict[str, Any],
    ) -> list[MonthResult]:
        """
        Simuleer dag voor dag tot aan de doeldatum.

        Voor elke dag wordt gecontroleerd of er al een maandelijkse
        berekening bestaat voor de huidige maand. Zo niet, dan wordt
        deze aangemaakt (AWIR maandelijkse verwerking).

        Na het berekeningsjaar worden automatisch de volgende stappen uitgevoerd:
        - IB-aanslag simulatie (1 april volgend jaar)
        - Definitieve vaststelling (6 maanden na IB-aanslag)
        - Vereffening (4 weken na definitieve beschikking)

        Args:
            case_id: ID van de case
            target_date: Doeldatum
            parameters: Parameters voor de rules engine

        Returns:
            Lijst van MonthResult objecten voor de verwerkte maanden
        """
        from datetime import timedelta

        results = []
        year_completion_results = []
        case = self.case_manager.get_case_by_id(case_id)

        logger.debug("╔══════════════════════════════════════════════════════════════")
        logger.debug(f"║ TIME SIMULATION: {self.current_date} → {target_date}")
        logger.debug("╚══════════════════════════════════════════════════════════════")

        # Zorg dat de case in LOPEND status is als we nog in het berekeningsjaar zijn
        if case.huidige_maand == 0 and self.current_date.year == case.berekeningsjaar:
            logger.debug("║ → Transitie: VOORSCHOT → LOPEND (start maand 1)")
            self.case_manager.start_maand(case_id, 1)

        self._log_workflow_state(case_id, "START")

        # Simuleer dag voor dag
        last_logged_month = 0
        while self.current_date <= target_date:
            current_month = self.current_date.month

            # Controleer of er al een berekening is voor deze maand
            case = self.case_manager.get_case_by_id(case_id)

            # =====================================================================
            # Maandverwerking binnen berekeningsjaar
            # =====================================================================
            if self.current_date.year == case.berekeningsjaar and case.status == CaseStatus.LOPEND:
                berekende_maanden = {b["maand"] for b in case.maandelijkse_berekeningen}

                # Verwerk alle gemiste maanden vanaf de simulatie startdatum tot en met de huidige maand
                # We gebruiken de _initial_start_date (bewaard bij initialisatie) in plaats van created_at
                # omdat created_at de echte systeemtijd is, niet de gesimuleerde tijd
                simulation_start = self._initial_start_date

                # Start vanaf maand 1 als simulatie start voor het berekeningsjaar,
                # anders gebruik de maand van de simulatie startdatum
                aanvraag_maand = 1 if simulation_start.year < case.berekeningsjaar else simulation_start.month
                for maand in range(aanvraag_maand, current_month + 1):
                    if maand not in berekende_maanden:
                        logger.debug(f"╠─ Maand {maand}: geen berekening gevonden, triggering AWIR...")
                        # Nog geen berekening voor deze maand - voer AWIR maandverwerking uit
                        result = self.process_month(
                            case_id=case_id,
                            maand=maand,
                            parameters=parameters,
                        )
                        results.append(result)
                        berekende_maanden.add(maand)
                        logger.debug(
                            f"╠─ Maand {maand}: berekend €{result.berekend_bedrag / 100:.2f}, "
                            f"betaald €{result.betaald_bedrag / 100:.2f}"
                        )

            # =====================================================================
            # Jaarafsluiting check (IB-aanslag, definitief, vereffening)
            # =====================================================================
            year_completion_result = self._check_year_completion(
                case_id=case_id,
                current_date=self.current_date,
                parameters=parameters,
            )
            if year_completion_result:
                year_completion_results.append(year_completion_result)
                logger.debug(f"╠─ Jaarafsluiting: {year_completion_result['actie']}")

            # Log bij maandovergang
            if current_month != last_logged_month:
                last_logged_month = current_month

            # Ga naar de volgende dag
            self.current_date = self.current_date + timedelta(days=1)

        self._log_workflow_state(case_id, "EINDE")

        # Log year completion results if any
        if year_completion_results:
            logger.debug("╔══════════════════════════════════════════════════════════════")
            logger.debug("║ JAARAFSLUITING RESULTATEN:")
            for result in year_completion_results:
                logger.debug(f"║   - {result['actie']}: {result}")
            logger.debug("╚══════════════════════════════════════════════════════════════")

        return results

    def __iter__(self):
        """Maak de simulator iterable voor step-by-step gebruik"""
        return self

    def __next__(self) -> date:
        """
        Verschuif naar de volgende maand (voor iteratie).

        Returns:
            De nieuwe huidige datum

        Raises:
            StopIteration als het jaar voorbij is (maand > 12)
        """
        if self.current_date.month >= 12:
            raise StopIteration

        self._advance_date(months=1)
        return self.current_date
