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


@dataclass
class YearEndResult:
    """Resultaat van jaar-einde verwerking"""

    berekeningsjaar: int
    totaal_berekend: int
    totaal_betaald: int
    definitief_jaarbedrag: int
    vereffening_type: str  # NABETALING / TERUGVORDERING / GEEN
    vereffening_bedrag: int
    new_case_id: str | None = None


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

    _eval_count = 0  # Class-level counter for debugging

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
        TimeSimulator._eval_count += 1
        logger.warning(f"[EVAL #{TimeSimulator._eval_count}] Evaluating case {case_id[:8]}... at {self.current_date}")

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
        process_date: date | None = None,
    ) -> MonthResult:
        """
        Verwerk een enkele maand: herberekening + betaling.

        Args:
            case_id: ID van de case
            maand: Maandnummer (1-12)
            parameters: Parameters voor de rules engine (moet BSN bevatten)
            trigger: Trigger type ("schedule" of "data_change")
            gewijzigde_data: Lijst van gewijzigde velden (bij data_change)
            process_date: Datum voor berekening/betaling (default: self.current_date)

        Returns:
            MonthResult met de verwerkte gegevens
        """
        # Gebruik process_date als gegeven, anders current_date
        effective_date = process_date if process_date is not None else self.current_date

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
            berekening_datum=effective_date,
        )

        # Betaling uitvoeren (op basis van voorschot, niet herberekening)
        case = self.case_manager.get_case_by_id(case_id)
        betaald_bedrag = case.voorschot_maandbedrag or maandbedrag

        self.case_manager.betaal_maand(
            case_id=case_id,
            maand=maand,
            betaald_bedrag=betaald_bedrag,
            betaal_datum=effective_date,
        )

        return MonthResult(
            maand=maand,
            reference_date=effective_date,
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

    def _check_awir_workflow(
        self,
        case_id: str,
        current_date: date,
        parameters: dict[str, Any],
    ) -> dict[str, Any] | None:
        """
        Controleer of AWIR workflow stappen nodig zijn en voer uit.

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

        from machine.events.case.aggregate import CaseStatus

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
        if (
            current_date >= ib_aanslag_datum
            and case.status in {CaseStatus.LOPEND, CaseStatus.VOORSCHOT}
            and (not hasattr(case, "ib_aanslag_datum") or case.ib_aanslag_datum is None)
        ):
            # Gebruik het toetsinkomen als vastgesteld inkomen
            vastgesteld_inkomen = parameters.get("toetsinkomen", case.berekend_jaarbedrag or 0)

            logger.debug(f"╠─ IB-aanslag simulatie: €{vastgesteld_inkomen / 100:.2f} op {ib_aanslag_datum}")

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
            # Herbereken definitief bedrag - gebruik IB inkomen
            definitief_bedrag = case.berekend_jaarbedrag or 0

            logger.debug(
                f"╠─ Definitieve vaststelling: €{definitief_bedrag / 100:.2f} "
                f"(deadline was {case.deadline_definitief})"
            )

            self.case_manager.stel_definitief_vast(
                case_id=case_id,
                definitief_jaarbedrag=definitief_bedrag,
                beschikking_datum=current_date,
            )

            return {
                "actie": "DEFINITIEF_VASTGESTELD",
                "datum": current_date,
                "definitief_jaarbedrag": definitief_bedrag,
            }

        # Refresh case na mogelijke definitieve vaststelling
        case = self.case_manager.get_case_by_id(case_id)

        # =========================================================================
        # Stap 3: Vereffenen (4 weken na definitief)
        # =========================================================================
        if (
            case.status == CaseStatus.DEFINITIEF
            and case.definitieve_beschikking_datum is not None
            and current_date >= case.definitieve_beschikking_datum + timedelta(weeks=4)
        ):
            logger.debug(f"╠─ Vereffening: 4 weken na definitief ({case.definitieve_beschikking_datum})")

            self.case_manager.vereffen(case_id=case_id, vereffening_datum=current_date)

            # Refresh case
            case = self.case_manager.get_case_by_id(case_id)

            return {
                "actie": "VEREFFEND",
                "datum": current_date,
                "vereffening_type": case.vereffening_type,
                "vereffening_bedrag": case.vereffening_bedrag,
            }

        return None

    def process_year_end(
        self,
        case_id: str,
        year_end_date: date,
        definitief_inkomen: int | None = None,
    ) -> YearEndResult:
        """
        Process year-end settlement and final calculation.

        Args:
            case_id: ID of the case to process
            year_end_date: Date of year-end processing
            definitief_inkomen: Final definitive income (if provided, triggers re-evaluation)

        Returns:
            YearEndResult with settlement details
        """
        case = self.case_manager.get_case_by_id(case_id)

        # Calculate totals from monthly data
        totaal_berekend = sum(b.get("berekend_bedrag", 0) for b in case.maandelijkse_berekeningen)
        totaal_betaald = sum(b.get("betaald_bedrag", 0) for b in case.maandelijkse_betalingen)

        # Re-evaluate with definitief inkomen if provided
        if definitief_inkomen is not None:
            # Use definitief inkomen for final calculation
            params_for_final = case.parameters.copy()
            params_for_final["inkomen"] = definitief_inkomen

            result = self.services.evaluate(
                service="TOESLAGEN",
                law=case.law,
                parameters=params_for_final,
                reference_date=year_end_date.isoformat(),
            )
            definitief_jaarbedrag = result.output.get("jaarbedrag", 0)
        else:
            # Use original calculation
            definitief_jaarbedrag = case.berekend_jaarbedrag

        # Call stel_definitief_vast
        self.case_manager.stel_definitief_vast(
            case_id=case_id,
            definitief_jaarbedrag=definitief_jaarbedrag,
        )

        # Call vereffen to execute settlement
        self.case_manager.vereffen(case_id=case_id)

        # Reload case to get updated vereffening data
        case = self.case_manager.get_case_by_id(case_id)

        return YearEndResult(
            berekeningsjaar=case.berekeningsjaar,
            totaal_berekend=totaal_berekend,
            totaal_betaald=totaal_betaald,
            definitief_jaarbedrag=definitief_jaarbedrag,
            vereffening_type=case.vereffening_type,
            vereffening_bedrag=case.vereffening_bedrag,
        )

    def _get_primary_amount_value(self, rule_spec: dict, output: dict) -> int:
        """
        Get the sum of primary output values based on citizen_relevance: primary.

        Dynamically looks up field names from rule specification instead of
        hardcoded field name checks (hoogte_toeslag, subsidiebedrag, etc.).

        Args:
            rule_spec: The rule specification dictionary from YAML
            output: The output dictionary from evaluation result

        Returns:
            Sum of primary amount/number output values, or 0 if none found
        """
        total = 0
        output_definitions = rule_spec.get("properties", {}).get("output", [])

        for output_def in output_definitions:
            if output_def.get("citizen_relevance") != "primary":
                continue

            output_name = output_def.get("name")
            output_type = output_def.get("type", "")

            # Only numeric types for amount calculation
            if output_type not in ["amount", "number"]:
                continue

            value = output.get(output_name)
            if value is not None:
                try:
                    total += int(value)
                except (ValueError, TypeError):
                    pass

        return total

    def start_new_year(
        self,
        old_case_id: str,
        new_year: int,
        start_date: date,
        updated_inkomen: int | None = None,
    ) -> str:
        """
        Create and initialize a new case for the next year.

        Args:
            old_case_id: ID of the previous year's case
            new_year: Year for the new case
            start_date: Start date for the new case
            updated_inkomen: Updated income for the new year (if different)

        Returns:
            ID of the newly created case
        """
        old_case = self.case_manager.get_case_by_id(old_case_id)

        # Prepare parameters for new year
        new_params = old_case.parameters.copy()
        new_params["berekeningsjaar"] = new_year
        if updated_inkomen is not None:
            new_params["inkomen"] = updated_inkomen

        # Create new case with simulated start date
        new_case_id = self.case_manager.submit_case(
            bsn=old_case.bsn,
            service_type=old_case.service,
            law=old_case.law,
            parameters=new_params,
            claimed_result={},  # AWIR workflow
            approved_claims_only=old_case.approved_claims_only,
            aanvraag_datum=start_date,
        )

        # Link to old case
        new_case = self.case_manager.get_case_by_id(new_case_id)
        new_case.vorig_jaar_case_id = str(old_case_id)
        self.case_manager.save(new_case)

        # Evaluate eligibility
        result = self.services.evaluate(
            service="TOESLAGEN",
            law=old_case.law,
            parameters=new_params,
            reference_date=start_date.isoformat(),
        )

        # Get rule_spec to use dynamic field detection
        rule_spec = self.services.get_rule_spec(
            law=old_case.law,
            reference_date=start_date.isoformat(),
            service=old_case.service,
        )

        # Use dynamic field detection like laws.py does
        berekend_jaarbedrag = self._get_primary_amount_value(rule_spec, result.output)
        heeft_aanspraak = berekend_jaarbedrag > 0

        logger.debug(
            f"╠─ start_new_year: berekend_jaarbedrag={berekend_jaarbedrag}, "
            f"heeft_aanspraak={heeft_aanspraak}, output={result.output}"
        )

        # Call bereken_aanspraak
        self.case_manager.bereken_aanspraak(
            case_id=new_case_id,
            heeft_aanspraak=heeft_aanspraak,
            berekend_jaarbedrag=berekend_jaarbedrag,
            berekening_datum=start_date,
        )

        # Always set voorschot (even if 0) to transition case to VOORSCHOT status
        # This allows time simulation to continue processing months
        maandbedrag = berekend_jaarbedrag // 12 if heeft_aanspraak else 0
        self.case_manager.stel_voorschot_vast(
            case_id=new_case_id,
            jaarbedrag=berekend_jaarbedrag if heeft_aanspraak else 0,
            maandbedrag=maandbedrag,
            beschikking_datum=start_date,
        )

        return new_case_id

    def step_to_date(
        self,
        case_id: str,
        target_date: date,
        parameters: dict[str, Any],
    ) -> list[MonthResult | YearEndResult]:
        """
        Simuleer maand voor maand tot aan de doeldatum.

        Voor elke maand wordt gecontroleerd of er al een maandelijkse
        berekening bestaat. Zo niet, dan wordt deze aangemaakt
        (AWIR maandelijkse verwerking).

        AWIR workflow:
        - Bij jaargrens: Start nieuw jaar case (continuering)
        - 1 april volgend jaar: IB-aanslag ontvangen
        - 6 maanden na IB-aanslag: Definitief vaststellen
        - 4 weken na definitief: Vereffening

        Args:
            case_id: ID van de case
            target_date: Doeldatum
            parameters: Parameters voor de rules engine

        Returns:
            Lijst van MonthResult en YearEndResult objecten voor de verwerkte maanden
        """
        from machine.events.case.aggregate import CaseStatus

        results: list[MonthResult | YearEndResult] = []
        case = self.case_manager.get_case_by_id(case_id)

        # Track alle actieve cases (huidige + oude jaren die nog vereffend moeten worden)
        active_cases: dict[int, str] = {}  # berekeningsjaar -> case_id
        if case.berekeningsjaar:
            active_cases[case.berekeningsjaar] = case_id

        logger.debug("╔══════════════════════════════════════════════════════════════")
        logger.debug(f"║ TIME SIMULATION: {self.current_date} → {target_date}")
        logger.debug("╚══════════════════════════════════════════════════════════════")

        # Zorg dat de case in LOPEND status is
        if case.huidige_maand == 0:
            logger.debug("║ → Transitie: VOORSCHOT → LOPEND (start maand 1)")
            self.case_manager.start_maand(case_id, 1)

        self._log_workflow_state(case_id, "START")

        # Iterate month by month
        while self.current_date <= target_date:
            current_month = self.current_date.month
            current_year = self.current_date.year

            # Refresh current case
            case = self.case_manager.get_case_by_id(case_id)
            berekende_maanden = {b["maand"] for b in case.maandelijkse_berekeningen}

            # =========================================================================
            # Check AWIR workflow voor alle actieve cases (oude jaren)
            # =========================================================================
            for jaar, old_case_id in list(active_cases.items()):
                if jaar < current_year:  # Alleen voor oude jaren
                    old_case = self.case_manager.get_case_by_id(old_case_id)
                    # Skip als al vereffend
                    if old_case.status == CaseStatus.VEREFFEND:
                        del active_cases[jaar]
                        continue

                    # Check AWIR workflow stappen
                    awir_result = self._check_awir_workflow(
                        case_id=old_case_id,
                        current_date=self.current_date,
                        parameters=parameters,
                    )
                    if awir_result:
                        logger.debug(f"╠─ AWIR [{jaar}]: {awir_result['actie']}")

                        # Verwijder uit actieve cases als vereffend
                        old_case = self.case_manager.get_case_by_id(old_case_id)
                        if old_case.status == CaseStatus.VEREFFEND:
                            del active_cases[jaar]

            # =========================================================================
            # Detecteer jaar grens: start nieuw jaar case bij januari
            # =========================================================================
            if (
                case.berekeningsjaar is not None
                and current_year > case.berekeningsjaar
                and current_year not in active_cases
            ):
                logger.debug(f"╠─ JAAR GRENS: Start nieuw jaar {current_year} (oude case blijft actief)")

                # Start new year case (oude case blijft actief voor AWIR workflow)
                new_case_id = self.start_new_year(
                    old_case_id=case_id,
                    new_year=current_year,
                    start_date=date(current_year, 1, 1),
                    updated_inkomen=parameters.get("inkomen"),
                )
                logger.debug(f"╠─ Nieuw jaar {current_year} gestart: case_id={new_case_id[:8]}...")

                # Track beide cases
                active_cases[current_year] = new_case_id

                # Switch to the new case voor maandelijkse verwerking
                case_id = new_case_id
                case = self.case_manager.get_case_by_id(case_id)

                # Ensure new case is in LOPEND status
                if case.huidige_maand == 0:
                    self.case_manager.start_maand(case_id, 1)

                # Refresh berekende_maanden for new case
                berekende_maanden = {b["maand"] for b in case.maandelijkse_berekeningen}

            # =========================================================================
            # Verwerk maanden voor huidige case
            # =========================================================================
            sim_start = self._initial_start_date

            # Start vanaf maand 1 als simulatie is gestart voor het berekeningsjaar,
            # anders gebruik de maand van de simulatie startdatum
            aanvraag_maand = 1 if case.berekeningsjaar and sim_start.year < case.berekeningsjaar else sim_start.month

            # Maanden verwerken voor het huidige berekeningsjaar
            # Dit gebeurt ongeacht of oude jaren al vereffend zijn - uitbetaling gaat gewoon door
            if case.berekeningsjaar == current_year:
                for maand in range(aanvraag_maand, current_month + 1):
                    if maand not in berekende_maanden:
                        logger.debug(f"╠─ Maand {maand}: geen berekening gevonden, triggering AWIR...")
                        maand_eerste = date(current_year, maand, 1)
                        result = self.process_month(
                            case_id=case_id,
                            maand=maand,
                            parameters=parameters,
                            process_date=maand_eerste,
                        )
                        results.append(result)
                        berekende_maanden.add(maand)
                        logger.debug(
                            f"╠─ Maand {maand}: berekend €{result.berekend_bedrag / 100:.2f}, "
                            f"betaald €{result.betaald_bedrag / 100:.2f}"
                        )

            # Jump to next month (instead of day by day for performance)
            self.current_date = self.current_date + relativedelta(months=1)

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
