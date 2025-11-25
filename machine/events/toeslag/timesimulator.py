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

logger = logging.getLogger(__name__)

if TYPE_CHECKING:
    from machine.events.case.application import CaseManager
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
    ) -> None:
        """
        Initialiseer de simulator.

        Args:
            case_manager: De CaseManager voor state management
            start_date: Startdatum voor de simulatie
            services_factory: Factory functie die een Services instance maakt voor een datum (optioneel)
            services: Directe Services instance (optioneel, heeft voorrang boven factory)
        """
        self.services_factory = services_factory
        self._services: Services | None = services
        self.case_manager = case_manager
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
        )

        # Betaling uitvoeren (op basis van voorschot, niet herberekening)
        case = self.case_manager.get_case_by_id(case_id)
        betaald_bedrag = case.voorschot_maandbedrag or maandbedrag

        self.case_manager.betaal_maand(
            case_id=case_id,
            maand=maand,
            betaald_bedrag=betaald_bedrag,
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

        Args:
            case_id: ID van de case
            target_date: Doeldatum
            parameters: Parameters voor de rules engine

        Returns:
            Lijst van MonthResult objecten voor de verwerkte maanden
        """
        from datetime import timedelta

        results = []
        case = self.case_manager.get_case_by_id(case_id)

        logger.debug("╔══════════════════════════════════════════════════════════════")
        logger.debug(f"║ TIME SIMULATION: {self.current_date} → {target_date}")
        logger.debug("╚══════════════════════════════════════════════════════════════")

        # Alleen verwerken als doeldatum binnen het berekeningsjaar valt
        if target_date.year != case.berekeningsjaar:
            logger.debug(f"║ ⚠ Doeldatum {target_date.year} buiten berekeningsjaar {case.berekeningsjaar}")
            return results

        # Zorg dat de case in LOPEND status is
        if case.huidige_maand == 0:
            logger.debug("║ → Transitie: VOORSCHOT → LOPEND (start maand 1)")
            self.case_manager.start_maand(case_id, 1)

        self._log_workflow_state(case_id, "START")

        # Simuleer dag voor dag
        last_logged_month = 0
        while self.current_date <= target_date:
            current_month = self.current_date.month

            # Controleer of er al een berekening is voor deze maand
            case = self.case_manager.get_case_by_id(case_id)
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
                        f"╠─ Maand {maand}: berekend €{result.berekend_bedrag / 100:.2f}, betaald €{result.betaald_bedrag / 100:.2f}"
                    )

            # Log bij maandovergang
            if current_month != last_logged_month:
                last_logged_month = current_month

            # Ga naar de volgende dag
            self.current_date = self.current_date + timedelta(days=1)

        self._log_workflow_state(case_id, "EINDE")
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
