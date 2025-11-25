"""Zaken router for workflow-based toeslag management"""

import logging
from collections import defaultdict
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from machine.events.case.aggregate import CaseStatus
from machine.events.toeslag.timesimulator import TimeSimulator
from web.dependencies import (
    get_case_manager,
    get_machine_service,
    get_simulated_date,
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
    CaseStatus.BEREKEND: ("Berekend", "blue"),
    CaseStatus.VOORSCHOT: ("Voorschot vastgesteld", "purple"),
    CaseStatus.LOPEND: ("Lopend", "green"),
    CaseStatus.DEFINITIEF: ("Definitief", "green"),
    CaseStatus.VEREFFEND: ("Vereffend", "gray"),
    CaseStatus.AFGEWEZEN: ("Afgewezen", "red"),
    CaseStatus.BEEINDIGD: ("Beeindigd", "gray"),
    CaseStatus.IN_REVIEW: ("In behandeling", "yellow"),
    CaseStatus.DECIDED: ("Besloten", "blue"),
    CaseStatus.OBJECTED: ("Bezwaar", "orange"),
}

# Service type labels for display
SERVICE_LABELS = {
    "TOESLAGEN": "Toeslagen",
}

# Law labels for display
LAW_LABELS = {
    "zorgtoeslagwet": "Zorgtoeslag",
    "huurtoeslag": "Huurtoeslag",
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


def get_law_label(law: str) -> str:
    """Get the display label for a law"""
    return LAW_LABELS.get(law, law)


def format_cents(cents: int | None) -> str:
    """Format eurocent amount to display string"""
    if cents is None:
        return "-"
    euros = cents / 100
    return f"€ {euros:,.2f}".replace(",", ".").replace(".", ",", 1)


# Dutch month names for display
DUTCH_MONTHS = {
    1: "januari",
    2: "februari",
    3: "maart",
    4: "april",
    5: "mei",
    6: "juni",
    7: "juli",
    8: "augustus",
    9: "september",
    10: "oktober",
    11: "november",
    12: "december",
}


def group_timeline_by_month(timeline: list[dict], simulated_date: date) -> list[tuple[str, list[dict]]]:
    """Group timeline events by year-month for display.

    Creates new event dicts with display fields - does not mutate original events.

    Args:
        timeline: List of timeline events with 'date' field
        simulated_date: Current simulated date to determine past/future

    Returns:
        List of (month_label, events) tuples sorted by date descending
    """
    grouped = defaultdict(list)

    for event in timeline:
        event_date_str = event.get("date")
        if not event_date_str:
            continue

        # Parse the date
        if isinstance(event_date_str, str):
            try:
                event_date = datetime.fromisoformat(event_date_str).date()
            except ValueError:
                continue
        elif isinstance(event_date_str, date):
            event_date = event_date_str
        else:
            continue

        # Create month key (e.g., "December 2025")
        month_name = DUTCH_MONTHS[event_date.month]
        month_key = f"{month_name.capitalize()} {event_date.year}"

        # Create a new dict with display fields (don't mutate original)
        display_event = {
            **event,
            "date_formatted": event_date.strftime("%d-%m-%Y"),
            "is_past": event_date <= simulated_date,
        }

        grouped[month_key].append(display_event)

    # Sort events within each month by date descending
    for month_key in grouped:
        grouped[month_key].sort(key=lambda e: e.get("date", ""), reverse=True)

    # Sort months by date descending
    def month_sort_key(month_label: str) -> tuple[int, int]:
        parts = month_label.split()
        month_name = parts[0].lower()
        year = int(parts[1])
        month_num = [k for k, v in DUTCH_MONTHS.items() if v == month_name][0]
        return (-year, -month_num)

    sorted_months = sorted(grouped.keys(), key=month_sort_key)
    return [(month, grouped[month]) for month in sorted_months]


@router.get("/")
async def zaken_index(
    request: Request,
    bsn: str = "100000001",
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_case_manager),
):
    """List all toeslagen for a citizen"""
    # Get profile for display
    profile = machine_service.get_profile_data(bsn)
    simulated_date = get_simulated_date(request)

    # Get all cases for this BSN (filter to AWIR toeslag cases)
    all_cases = case_manager.get_cases_by_bsn(bsn)
    toeslag_cases = [c for c in all_cases if c.service == "TOESLAGEN"]

    # Enrich cases with display data
    toeslagen_display = []
    for case in toeslag_cases:
        status_label, status_color = get_status_badge(case.status)
        # Get aanvraag_datum from created_at
        aanvraag_datum = case.created_at.date().isoformat() if case.created_at else None
        toeslagen_display.append({
            "id": str(case.id),
            "law": case.law,
            "type_label": get_law_label(case.law),
            "berekeningsjaar": case.berekeningsjaar,
            "status": case.status,
            "status_label": status_label,
            "status_color": status_color,
            "aanvraag_datum": aanvraag_datum,
            "berekend_jaarbedrag": case.berekend_jaarbedrag,
            "berekend_jaarbedrag_display": format_cents(case.berekend_jaarbedrag),
            "voorschot_maandbedrag": case.voorschot_maandbedrag,
            "voorschot_maandbedrag_display": format_cents(case.voorschot_maandbedrag),
        })

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
async def zaken_aanvraag_submit(
    request: Request,
    bsn: str = Form(...),
    berekeningsjaar: int = Form(...),
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_case_manager),
):
    """Submit a zorgtoeslag aanvraag"""
    simulated_date = get_simulated_date(request)
    simulated_date_str = simulated_date.isoformat()

    try:
        # 1. Calculate eligibility using rules engine with simulated date
        result = machine_service.evaluate(
            service="TOESLAGEN",
            law="zorgtoeslagwet",
            parameters={"BSN": bsn, "berekeningsjaar": berekeningsjaar},
            reference_date=simulated_date_str,
        )

        # 2. Submit case via case_manager
        # Convert simulated_date to datetime for created_at
        created_at = datetime.combine(simulated_date, datetime.min.time())
        case_id = case_manager.submit_case(
            bsn=bsn,
            service="TOESLAGEN",
            law="zorgtoeslagwet",
            parameters={"BSN": bsn, "berekeningsjaar": berekeningsjaar},
            claimed_result={},  # Empty for AWIR workflow
            approved_claims_only=True,
            created_at=created_at,
        )

        # 3. Determine eligibility and amount
        berekend_jaarbedrag = result.output.get("hoogte_toeslag", 0)
        heeft_aanspraak = berekend_jaarbedrag > 0

        # 4. Update case with calculation result
        case_manager.bereken_aanspraak(
            case_id=case_id,
            heeft_aanspraak=heeft_aanspraak,
            berekend_jaarbedrag=berekend_jaarbedrag,
            berekening_datum=simulated_date,
        )

        # 5. If eligible, automatically set voorschot
        if heeft_aanspraak:
            case_manager.stel_voorschot_vast(case_id=case_id, beschikking_datum=simulated_date)

        # 6. Redirect to detail page
        return RedirectResponse(
            url=f"/zaken/{case_id}?bsn={bsn}",
            status_code=303,
        )

    except ValueError as e:
        # Handle duplicate application error
        profile = machine_service.get_profile_data(bsn)
        current_year = simulated_date.year
        return templates.TemplateResponse(
            "zaken/aanvraag.html",
            {
                "request": request,
                "bsn": bsn,
                "profile": profile,
                "years": [current_year, current_year + 1],
                "current_year": current_year,
                "error": str(e),
                "all_profiles": machine_service.get_all_profiles(),
                "simulated_date": simulated_date.isoformat(),
            },
        )


@router.post("/simulate/reset")
async def reset_simulation(
    request: Request,
    bsn: str = Form(...),
    toeslag_id: str = Form(None),
    reset_date: str = Form(None),
    case_manager=Depends(get_case_manager),
):
    """Reset simulation date to aanvraag date or specified date"""
    if reset_date:
        new_date = date.fromisoformat(reset_date)
    elif toeslag_id:
        case = case_manager.get_case_by_id(toeslag_id)
        if case and case.created_at:
            new_date = case.created_at.date()
        else:
            new_date = date.today()
    else:
        new_date = date.today()

    set_simulated_date(request, new_date)
    logger.warning(f"[SIMULATE] Reset date to {new_date}")

    redirect_url = f"/zaken/{toeslag_id}?bsn={bsn}" if toeslag_id else f"/zaken/?bsn={bsn}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/simulate")
async def simulate_time(
    request: Request,
    target_date: str = Form(...),
    bsn: str = Form(...),
    toeslag_id: str = Form(None),
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_case_manager),
):
    """Advance simulation date and process all non-finalized toeslagen"""
    current_date = get_simulated_date(request)
    target = date.fromisoformat(target_date)

    logger.warning(f"[SIMULATE] current_date={current_date}, target={target}, bsn={bsn}, toeslag_id={toeslag_id}")

    # Don't process if target is before or equal to current
    if target <= current_date:
        logger.warning("[SIMULATE] Target date not in future, just updating session")
        set_simulated_date(request, target)
        redirect_url = f"/zaken/{toeslag_id}?bsn={bsn}" if toeslag_id else f"/zaken/?bsn={bsn}"
        return RedirectResponse(url=redirect_url, status_code=303)

    # Get all non-finalized cases for this BSN (filter to TOESLAGEN)
    all_cases = case_manager.get_cases_by_bsn(bsn)
    toeslag_cases = [c for c in all_cases if c.service == "TOESLAGEN"]
    processable = [c for c in toeslag_cases if is_processable(c)]

    logger.warning(f"[SIMULATE] Found {len(toeslag_cases)} toeslag cases, {len(processable)} processable")

    # Get the underlying services from machine_service for TimeSimulator
    services = machine_service.get_services()

    # Process each case through time simulation
    for case in processable:
        logger.warning(f"[SIMULATE] Processing case {case.id}: status={case.status}, berekeningsjaar={case.berekeningsjaar}")
        simulator = TimeSimulator(
            case_manager=services.case_manager,
            start_date=current_date,
            services=services,
        )
        results = simulator.step_to_date(
            case_id=str(case.id),
            target_date=target,
            parameters={"BSN": bsn, "berekeningsjaar": case.berekeningsjaar},
        )
        logger.warning(f"[SIMULATE] Processed {len(results)} events for case {case.id}")

    # Update session with new date
    set_simulated_date(request, target)

    # Redirect back to detail page or index
    redirect_url = f"/zaken/{toeslag_id}?bsn={bsn}" if toeslag_id else f"/zaken/?bsn={bsn}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/{toeslag_id}")
async def zaken_detail(
    request: Request,
    toeslag_id: str,
    bsn: str = "100000001",
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_case_manager),
):
    """Show toeslag detail with full timeline"""
    profile = machine_service.get_profile_data(bsn)
    simulated_date = get_simulated_date(request)

    # Get case by ID
    try:
        toeslag = case_manager.get_case_by_id(toeslag_id)
    except Exception:
        toeslag = None

    if not toeslag:
        return templates.TemplateResponse(
            "zaken/not_found.html",
            {
                "request": request,
                "bsn": bsn,
                "toeslag_id": toeslag_id,
            },
            status_code=404,
        )

    # Get status badge
    status_label, status_color = get_status_badge(toeslag.status)

    # Get aanvraag_datum from created_at
    aanvraag_datum = toeslag.created_at.date().isoformat() if toeslag.created_at else None

    # Build timeline events
    timeline = []

    # Add aanvraag event
    timeline.append({
        "type": "aanvraag",
        "label": "Aanvraag ingediend",
        "date": aanvraag_datum,
        "icon": "document",
        "details": {
            "BSN": toeslag.bsn,
            "Berekeningsjaar": toeslag.berekeningsjaar,
        },
    })

    # Add berekening event if calculated
    if toeslag.heeft_aanspraak is not None:
        # Use berekening_datum if available, otherwise fall back to aanvraag_datum
        berekening_datum = toeslag.berekening_datum.isoformat() if toeslag.berekening_datum else aanvraag_datum
        timeline.append({
            "type": "berekening",
            "label": "Aanspraak berekend" if toeslag.heeft_aanspraak else "Geen aanspraak",
            "date": berekening_datum,
            "icon": "calculator" if toeslag.heeft_aanspraak else "x-circle",
            "details": {
                "Heeft aanspraak": "Ja" if toeslag.heeft_aanspraak else "Nee",
                "Jaarbedrag": format_cents(toeslag.berekend_jaarbedrag),
            },
        })

    # Add beschikkingen
    for beschikking in (toeslag.beschikkingen or []):
        beschikking_type = beschikking.get("type", "ONBEKEND")
        beschikking_datum = beschikking.get("datum")
        # Convert date to string if needed
        if isinstance(beschikking_datum, date):
            beschikking_datum = beschikking_datum.isoformat()

        # Format details, converting amounts to display format
        details = {}
        for k, v in beschikking.items():
            if k in ["type", "datum"]:
                continue
            if k in ["jaarbedrag", "maandbedrag", "bedrag"]:
                details[k.replace("_", " ").title()] = format_cents(v)
            else:
                details[k.replace("_", " ").title()] = v

        timeline.append({
            "type": "beschikking",
            "label": beschikking_type.replace("_", " ").title(),
            "date": beschikking_datum,
            "icon": "document-check",
            "details": details,
        })

    # Add monthly calculations
    for berekening in (toeslag.maandelijkse_berekeningen or []):
        berekening_datum = berekening.get("berekening_datum")
        if isinstance(berekening_datum, date):
            berekening_datum = berekening_datum.isoformat()

        timeline.append({
            "type": "maand_berekening",
            "label": f"Maand {berekening['maand']} herberekend",
            "date": berekening_datum,
            "icon": "refresh",
            "details": {
                "Maand": berekening["maand"],
                "Berekend bedrag": format_cents(berekening["berekend_bedrag"]),
                "Trigger": berekening.get("trigger", "schedule"),
            },
        })

    # Add monthly payments
    for betaling in (toeslag.maandelijkse_betalingen or []):
        betaal_datum = betaling.get("betaal_datum")
        if isinstance(betaal_datum, date):
            betaal_datum = betaal_datum.isoformat()

        timeline.append({
            "type": "maand_betaling",
            "label": f"Maand {betaling['maand']} betaald",
            "date": betaal_datum,
            "icon": "currency-euro",
            "details": {
                "Maand": betaling["maand"],
                "Betaald bedrag": format_cents(betaling.get("betaald_bedrag")),
            },
        })

    # Add definitieve beschikking event if status is DEFINITIEF or VEREFFEND
    if toeslag.status in [CaseStatus.DEFINITIEF, CaseStatus.VEREFFEND]:
        definitief_datum = toeslag.definitieve_beschikking_datum
        if isinstance(definitief_datum, date):
            definitief_datum = definitief_datum.isoformat()

        totaal_berekend = sum(b.get("berekend_bedrag", 0) for b in (toeslag.maandelijkse_berekeningen or []))
        totaal_betaald = sum(b.get("betaald_bedrag", 0) for b in (toeslag.maandelijkse_betalingen or []))

        timeline.append({
            "type": "definitieve_beschikking",
            "label": f"Definitieve beschikking {toeslag.berekeningsjaar}",
            "date": definitief_datum,
            "icon": "document-check",
            "details": {
                "Definitief jaarbedrag": format_cents(toeslag.definitief_jaarbedrag),
                "Totaal berekend": format_cents(totaal_berekend),
                "Totaal betaald": format_cents(totaal_betaald),
            },
        })

    # Add vereffening event if status is VEREFFEND
    if toeslag.status == CaseStatus.VEREFFEND:
        vereffening_datum = toeslag.vereffening_datum
        if isinstance(vereffening_datum, date):
            vereffening_datum = vereffening_datum.isoformat()

        timeline.append({
            "type": "vereffening",
            "label": f"Vereffening: {toeslag.vereffening_type}",
            "date": vereffening_datum,
            "icon": "currency-euro",
            "details": {
                "Type": toeslag.vereffening_type,
                "Bedrag": format_cents(toeslag.vereffening_bedrag),
            },
        })

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

    # Group timeline by month for the new design
    logger.info(f"[ZAKEN] Timeline has {len(timeline)} events")
    grouped_timeline = group_timeline_by_month(timeline, simulated_date)
    logger.info(f"[ZAKEN] Grouped timeline has {len(grouped_timeline)} months")

    # Calculate year totals for summary card
    totaal_berekend = sum(b.get("berekend_bedrag", 0) for b in (toeslag.maandelijkse_berekeningen or []))
    totaal_betaald = sum(b.get("betaald_bedrag", 0) for b in (toeslag.maandelijkse_betalingen or []))

    # Get profile name for display
    profile_name = profile.get("naam", bsn) if profile else bsn

    return templates.TemplateResponse(
        "zaken/detail.html",
        {
            "request": request,
            "bsn": bsn,
            "profile": profile,
            "profile_name": profile_name,
            "toeslag": toeslag,
            "type_label": get_law_label(toeslag.law),
            "status_label": status_label,
            "status_color": status_color,
            "timeline": timeline,
            "grouped_timeline": grouped_timeline,
            "format_cents": format_cents,
            "all_profiles": machine_service.get_all_profiles(),
            "simulated_date": simulated_date.isoformat(),
            "totaal_berekend": totaal_berekend,
            "totaal_betaald": totaal_betaald,
            "CaseStatus": CaseStatus,  # For template status checks
        },
    )
