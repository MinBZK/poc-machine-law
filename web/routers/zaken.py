"""Zaken router for workflow-based toeslag management"""

import logging
from datetime import date, datetime
from itertools import groupby

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from machine.events.case.aggregate import CaseStatus
from machine.events.toeslag.timesimulator import TimeSimulator
from web.dependencies import (
    get_machine_service,
    get_simulated_date,
    get_zaken_case_manager,
    set_simulated_date,
    templates,
)
from web.engines import EngineInterface

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zaken", tags=["zaken"])

# Finalized statuses that should not be processed during time simulation
FINALIZED_STATUSES = {
    CaseStatus.DEFINITIEF,
    CaseStatus.VEREFFEND,
    CaseStatus.AFGEWEZEN,
    CaseStatus.BEEINDIGD,
}


def is_processable(case) -> bool:
    """Check if a case should be processed during time simulation"""
    return case.status not in FINALIZED_STATUSES


# Status badge mapping for display
STATUS_BADGES = {
    CaseStatus.SUBMITTED: ("Aanvraag ingediend", "yellow"),
    CaseStatus.IN_REVIEW: ("In behandeling", "yellow"),
    CaseStatus.DECIDED: ("Besloten", "blue"),
    CaseStatus.OBJECTED: ("Bezwaar", "orange"),
    CaseStatus.BEREKEND: ("Berekend", "blue"),
    CaseStatus.VOORSCHOT: ("Voorschot vastgesteld", "purple"),
    CaseStatus.LOPEND: ("Lopend", "green"),
    CaseStatus.DEFINITIEF: ("Definitief", "green"),
    CaseStatus.VEREFFEND: ("Vereffend", "gray"),
    CaseStatus.AFGEWEZEN: ("Afgewezen", "red"),
    CaseStatus.BEEINDIGD: ("Beeindigd", "gray"),
}

# Type labels for display (derived from law name)
LAW_LABELS = {
    "zorgtoeslagwet": "Zorgtoeslag",
    "huurtoeslag": "Huurtoeslag",
    "kindgebonden_budget": "Kindgebonden budget",
    "kinderopvangtoeslag": "Kinderopvangtoeslag",
}


def get_status_badge(status: CaseStatus) -> tuple[str, str]:
    """Get the display label and color for a status"""
    # Handle both enum and string status values
    if isinstance(status, str):
        try:
            status = CaseStatus(status)
        except ValueError:
            return (status, "gray")
    return STATUS_BADGES.get(status, (str(status), "gray"))


def get_type_label(law: str) -> str:
    """Get the display label for a law/toeslag type"""
    return LAW_LABELS.get(law, law.replace("_", " ").title())


def format_cents(cents: int | None) -> str:
    """Format eurocent amount to display string"""
    if cents is None:
        return "-"
    euros = cents / 100
    return f"€ {euros:,.2f}".replace(",", ".").replace(".", ",", 1)


@router.get("/")
async def zaken_index(
    request: Request,
    bsn: str = "100000001",
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_zaken_case_manager),
):
    """List all toeslagen for a citizen"""
    # Get profile for display
    profile = machine_service.get_profile_data(bsn)
    simulated_date = get_simulated_date(request)

    # Get all cases for this BSN (filter for toeslag service)
    all_cases = case_manager.get_cases_by_bsn(bsn)
    toeslagen = [c for c in all_cases if c.service == "TOESLAGEN"]

    # Enrich toeslagen with display data
    toeslagen_display = []
    for case in toeslagen:
        status_label, status_color = get_status_badge(case.status)
        toeslagen_display.append(
            {
                "id": str(case.id),
                "oid": str(case.id)[:8],  # Short ID for display
                "type": case.law,
                "type_label": get_type_label(case.law),
                "berekeningsjaar": case.berekeningsjaar,
                "status": case.status,
                "status_label": status_label,
                "status_color": status_color,
                "aanvraag_datum": case.created_at.date().isoformat() if case.created_at else None,
                "berekend_jaarbedrag": case.berekend_jaarbedrag,
                "berekend_jaarbedrag_display": format_cents(case.berekend_jaarbedrag),
                "voorschot_maandbedrag": case.voorschot_maandbedrag,
                "voorschot_maandbedrag_display": format_cents(case.voorschot_maandbedrag),
            }
        )

    return templates.TemplateResponse(
        "zaken/index.html",
        {
            "request": request,
            "bsn": bsn,
            "profile": profile,
            "toeslagen": toeslagen_display,
            "all_profiles": machine_service.get_all_profiles(),
            "simulated_date": simulated_date.isoformat(),
        },
    )


@router.get("/aanvraag")
async def zaken_aanvraag_form(
    request: Request,
    bsn: str = "100000001",
    machine_service: EngineInterface = Depends(get_machine_service),
):
    """Show the aanvraag form"""
    profile = machine_service.get_profile_data(bsn)
    simulated_date = get_simulated_date(request)

    # Current year and next year as options (based on simulated date)
    current_year = simulated_date.year
    years = [current_year, current_year + 1]

    # Evaluate zorgtoeslag to show expected amount
    try:
        result = machine_service.evaluate(
            service="TOESLAGEN",
            law="zorgtoeslagwet",
            parameters={"BSN": bsn},
            reference_date=simulated_date.isoformat(),
        )
        expected_amount = result.output.get("hoogte_toeslag", 0)
        expected_amount_display = format_cents(expected_amount)
    except Exception:
        expected_amount = 0
        expected_amount_display = "-"

    return templates.TemplateResponse(
        "zaken/aanvraag.html",
        {
            "request": request,
            "bsn": bsn,
            "profile": profile,
            "years": years,
            "current_year": current_year,
            "expected_amount": expected_amount,
            "expected_amount_display": expected_amount_display,
            "all_profiles": machine_service.get_all_profiles(),
            "simulated_date": simulated_date.isoformat(),
        },
    )


@router.post("/aanvraag")
async def zaken_submit_aanvraag(
    request: Request,
    bsn: str = Form(...),
    berekeningsjaar: int = Form(...),
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_zaken_case_manager),
):
    """Verwerk zorgtoeslag aanvraag (AWIR Art. 15)"""
    simulated_date = get_simulated_date(request)

    # Evaluate zorgtoeslag
    result = machine_service.evaluate(
        service="TOESLAGEN",
        law="zorgtoeslagwet",
        parameters={"BSN": bsn, "berekeningsjaar": berekeningsjaar},
        reference_date=simulated_date.isoformat(),
    )

    # Submit case via eventsourcing CaseManager
    case_id = case_manager.submit_case(
        bsn=bsn,
        service_type="TOESLAGEN",
        law="zorgtoeslagwet",
        parameters={"BSN": bsn, "berekeningsjaar": berekeningsjaar},
        claimed_result={},
        approved_claims_only=False,
    )

    # AWIR workflow: bereken aanspraak
    berekend_jaarbedrag = result.output.get("hoogte_toeslag", 0)
    heeft_aanspraak = berekend_jaarbedrag > 0

    case_manager.bereken_aanspraak(
        case_id=case_id,
        heeft_aanspraak=heeft_aanspraak,
        berekend_jaarbedrag=berekend_jaarbedrag,
    )

    if heeft_aanspraak:
        case_manager.stel_voorschot_vast(case_id=case_id)
    else:
        case_manager.wijs_af(case_id=case_id, reden="Geen aanspraak op basis van berekening")

    # Redirect naar detail pagina
    return RedirectResponse(url=f"/zaken/{case_id}?bsn={bsn}", status_code=303)


@router.post("/simulate/reset")
async def reset_simulation(
    request: Request,
    bsn: str = Form(...),
    case_id: str = Form(None),
    reset_date: str = Form(None),
    case_manager=Depends(get_zaken_case_manager),
):
    """Reset simulation date to aanvraag date or specified date"""
    if reset_date:
        new_date = date.fromisoformat(reset_date)
    elif case_id:
        case = case_manager.get_case_by_id(case_id)
        new_date = case.created_at.date() if case and case.created_at else date.today()
    else:
        new_date = date.today()

    set_simulated_date(request, new_date)
    logger.warning(f"[SIMULATE] Reset date to {new_date}")

    redirect_url = f"/zaken/{case_id}?bsn={bsn}" if case_id else f"/zaken/?bsn={bsn}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/simulate")
async def simulate_time(
    request: Request,
    target_date: str = Form(...),
    bsn: str = Form(...),
    case_id: str = Form(None),
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_zaken_case_manager),
):
    """Advance simulation date and process all non-finalized toeslagen"""
    import traceback

    try:
        current_date = get_simulated_date(request)
        target = date.fromisoformat(target_date)

        logger.warning(f"[SIMULATE] current_date={current_date}, target={target}, bsn={bsn}, case_id={case_id}")

        # Don't process if target is before or equal to current
        if target <= current_date:
            logger.warning("[SIMULATE] Target date not in future, just updating session")
            set_simulated_date(request, target)
            redirect_url = f"/zaken/{case_id}?bsn={bsn}" if case_id else f"/zaken/?bsn={bsn}"
            return RedirectResponse(url=redirect_url, status_code=303)

        # Get all non-finalized toeslagen for this BSN
        all_cases = case_manager.get_cases_by_bsn(bsn)
        toeslagen = [c for c in all_cases if c.service == "TOESLAGEN"]
        processable = [t for t in toeslagen if is_processable(t)]

        logger.warning(f"[SIMULATE] Found {len(toeslagen)} toeslagen, {len(processable)} processable")

        # Get the underlying services from machine_service for TimeSimulator
        services = machine_service.get_services()

        # Process each case through time simulation
        for case in processable:
            logger.warning(
                f"[SIMULATE] Processing case {case.id}: status={case.status}, berekeningsjaar={case.berekeningsjaar}"
            )
            simulator = TimeSimulator(
                case_manager=case_manager,
                start_date=current_date,
                services=services,
            )
            results = simulator.step_to_date(
                case_id=str(case.id),
                target_date=target,
                parameters={"BSN": bsn},
            )
            logger.warning(f"[SIMULATE] Processed {len(results)} months for case {case.id}")

        # Update session with new date
        set_simulated_date(request, target)

        # Redirect back to detail page or index
        redirect_url = f"/zaken/{case_id}?bsn={bsn}" if case_id else f"/zaken/?bsn={bsn}"
        return RedirectResponse(url=redirect_url, status_code=303)

    except Exception as e:
        logger.error(f"[SIMULATE] ERROR: {type(e).__name__}: {e}")
        logger.error(f"[SIMULATE] TRACEBACK:\n{traceback.format_exc()}")
        raise


@router.get("/{case_id}")
async def zaken_detail(
    request: Request,
    case_id: str,
    bsn: str = "100000001",
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_zaken_case_manager),
):
    """Show case detail with full timeline"""
    import traceback

    try:
        profile = machine_service.get_profile_data(bsn)
        simulated_date = get_simulated_date(request)

        # Get case by ID
        case = case_manager.get_case_by_id(case_id)

        if not case:
            return templates.TemplateResponse(
                "zaken/not_found.html",
                {
                    "request": request,
                    "bsn": bsn,
                    "case_id": case_id,
                },
                status_code=404,
            )

        # Get status badge
        status_label, status_color = get_status_badge(case.status)

        # Build timeline events
        timeline = []

        # Add aanvraag event
        aanvraag_datum = case.created_at.date().isoformat() if case.created_at else None
        timeline.append(
            {
                "type": "aanvraag",
                "label": "Aanvraag ingediend",
                "date": aanvraag_datum,
                "icon": "document",
                "details": {
                    "BSN": case.bsn,
                    "Berekeningsjaar": case.berekeningsjaar,
                },
            }
        )

        # Add berekening event if calculated
        if case.heeft_aanspraak is not None:
            timeline.append(
                {
                    "type": "berekening",
                    "label": "Aanspraak berekend" if case.heeft_aanspraak else "Geen aanspraak",
                    "date": aanvraag_datum,  # Same day for now
                    "icon": "calculator" if case.heeft_aanspraak else "x-circle",
                    "details": {
                        "Heeft aanspraak": "Ja" if case.heeft_aanspraak else "Nee",
                        "Jaarbedrag": format_cents(case.berekend_jaarbedrag),
                    },
                }
            )

        # Add beschikkingen
        beschikkingen = getattr(case, "beschikkingen", []) or []
        for beschikking in beschikkingen:
            beschikking_type = beschikking.get("type", "ONBEKEND")
            beschikking_datum = beschikking.get("datum")
            if isinstance(beschikking_datum, date):
                beschikking_datum = beschikking_datum.isoformat()

            # Convert any date values in details to strings
            details = {}
            for k, v in beschikking.items():
                if k not in ["type", "datum"]:
                    if isinstance(v, date):
                        details[k] = v.isoformat()
                    else:
                        details[k] = v

            timeline.append(
                {
                    "type": "beschikking",
                    "label": beschikking_type.replace("_", " ").title(),
                    "date": beschikking_datum,
                    "icon": "document-check",
                    "details": details,
                }
            )

        # Add monthly calculations
        berekeningen = getattr(case, "maandelijkse_berekeningen", []) or []
        for berekening in berekeningen:
            berekening_datum = berekening.get("berekening_datum")
            if isinstance(berekening_datum, date):
                berekening_datum = berekening_datum.isoformat()

            # Ensure trigger is a string
            trigger = berekening.get("trigger", "schedule")
            if isinstance(trigger, date):
                trigger = trigger.isoformat()

            timeline.append(
                {
                    "type": "maand_berekening",
                    "label": f"Maand {berekening['maand']} herberekend",
                    "date": berekening_datum,
                    "icon": "refresh",
                    "details": {
                        "Maand": berekening["maand"],
                        "Berekend bedrag": format_cents(berekening["berekend_bedrag"]),
                        "Trigger": trigger,
                    },
                }
            )

        # Add monthly payments
        betalingen = getattr(case, "maandelijkse_betalingen", []) or []
        for betaling in betalingen:
            betaal_datum = betaling.get("betaal_datum")
            if isinstance(betaal_datum, date):
                betaal_datum = betaal_datum.isoformat()

            # Ensure basis is converted if it's a date (shouldn't be, but be safe)
            basis = betaling.get("basis", "voorschot")
            if isinstance(basis, date):
                basis = basis.isoformat()

            timeline.append(
                {
                    "type": "maand_betaling",
                    "label": f"Maand {betaling['maand']} betaald",
                    "date": betaal_datum,
                    "icon": "currency-euro",
                    "details": {
                        "Maand": betaling["maand"],
                        "Betaald bedrag": format_cents(betaling["betaald_bedrag"]),
                    },
                }
            )

        # Sort timeline by date
        def get_sort_date(event):
            d = event.get("date")
            if d is None:
                return datetime.min
            if isinstance(d, str):
                try:
                    return datetime.fromisoformat(d)
                except ValueError:
                    return datetime.min
            if isinstance(d, date):
                return datetime.combine(d, datetime.min.time())
            return datetime.min

        timeline.sort(key=get_sort_date)

        # Calculate totals
        totaal_berekend = sum(b.get("berekend_bedrag", 0) or 0 for b in berekeningen)
        totaal_betaald = sum(b.get("betaald_bedrag", 0) or 0 for b in betalingen)

        # Group timeline events by month
        def get_month_key(event):
            d = event.get("date")
            if d is None:
                return "Onbekend"
            if isinstance(d, str):
                try:
                    dt = datetime.fromisoformat(d)
                    return dt.strftime("%B %Y")
                except ValueError:
                    return "Onbekend"
            if isinstance(d, date):
                return d.strftime("%B %Y")
            return "Onbekend"

        # Add display fields to events
        for event in timeline:
            event["date_formatted"] = event.get("date", "")
            event_date = event.get("date")
            if event_date:
                try:
                    event_dt = datetime.fromisoformat(event_date).date() if isinstance(event_date, str) else event_date
                    event["is_past"] = event_dt <= simulated_date
                except (ValueError, TypeError):
                    event["is_past"] = True
            else:
                event["is_past"] = True

        # Group by month
        grouped_timeline = [(k, list(g)) for k, g in groupby(timeline, key=get_month_key)]

        # Get profile name
        profile_name = profile.get("name", "") if profile else ""

        # Get aanvraag datum for display
        aanvraag_datum_display = case.created_at.date().isoformat() if case.created_at else None

        return templates.TemplateResponse(
            "zaken/detail.html",
            {
                "request": request,
                "bsn": bsn,
                "profile": profile,
                "profile_name": profile_name,
                "toeslag": case,
                "type_label": get_type_label(case.law),
                "status_label": status_label,
                "status_color": status_color,
                "timeline": timeline,
                "grouped_timeline": grouped_timeline,
                "totaal_berekend": totaal_berekend,
                "totaal_betaald": totaal_betaald,
                "CaseStatus": CaseStatus,
                "format_cents": format_cents,
                "all_profiles": machine_service.get_all_profiles(),
                "simulated_date": simulated_date.isoformat(),
                "aanvraag_datum_display": aanvraag_datum_display,
            },
        )
    except Exception as e:
        logger.error(f"[ZAKEN] ERROR in zaken_detail: {type(e).__name__}: {e}")
        logger.error(f"[ZAKEN] TRACEBACK:\n{traceback.format_exc()}")
        raise
