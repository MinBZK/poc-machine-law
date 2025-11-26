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


# Alias for consistency
def get_law_label(law: str) -> str:
    """Get the display label for a law/toeslag type (alias for get_type_label)"""
    return get_type_label(law)


def format_cents(cents: int | None) -> str:
    """Format eurocent amount to display string"""
    if cents is None:
        return "-"
    euros = cents / 100
    # Format with Dutch notation: period for thousands, comma for decimals
    # First format with English notation, then swap: 1,834.24 -> 1.834,24
    formatted = f"{euros:,.2f}"  # e.g., "1,834.24"
    # Replace comma (thousand separator) with temporary marker
    formatted = formatted.replace(",", "TEMP")  # "1TEMP834.24"
    # Replace period (decimal separator) with comma
    formatted = formatted.replace(".", ",")  # "1TEMP834,24"
    # Replace temporary marker with period
    formatted = formatted.replace("TEMP", ".")  # "1.834,24"
    return f"€ {formatted}"


def group_timeline_by_month(timeline: list[dict], simulated_date: date) -> list[tuple[str, list[dict]]]:
    """Group timeline events by month and add display fields.

    Args:
        timeline: List of timeline event dicts (must be sorted by date)
        simulated_date: Current simulated date for is_past calculation

    Returns:
        List of (month_key, events) tuples
    """
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
    return [(k, list(g)) for k, g in groupby(timeline, key=get_month_key)]


def serialize_value(v):
    """Serialize a value for JSON, converting dates to ISO strings."""
    if isinstance(v, date):
        return v.isoformat()
    if isinstance(v, datetime):
        return v.isoformat()
    return v


def serialize_details(details: dict) -> dict:
    """Serialize all values in a details dict for JSON compatibility."""
    return {k: serialize_value(v) for k, v in details.items()}


def build_timeline_for_case(toeslag, format_cents_fn) -> list[dict]:
    """Build timeline events for a single case.

    Args:
        toeslag: Case object
        format_cents_fn: Function to format cents as currency string

    Returns:
        List of timeline event dicts
    """
    timeline = []
    berekeningsjaar = toeslag.berekeningsjaar or (toeslag.created_at.year if toeslag.created_at else "")
    zaak_label = f"{get_law_label(toeslag.law)} {berekeningsjaar}"
    zaak_id = str(toeslag.id)

    # Get aanvraag_datum from created_at
    aanvraag_datum = toeslag.created_at.date().isoformat() if toeslag.created_at else None

    # Check if this is an automatic continuation from previous year
    is_voortzetting = getattr(toeslag, "vorig_jaar_case_id", None) is not None

    # Add aanvraag/voortzetting event - include year in label for multi-year timelines
    aanvraag_label_suffix = f" {berekeningsjaar}" if berekeningsjaar else ""
    if is_voortzetting:
        aanvraag_label = f"Toeslag voortgezet{aanvraag_label_suffix}"
        event_type = "voortzetting"
    else:
        aanvraag_label = f"Aanvraag ingediend{aanvraag_label_suffix}"
        event_type = "aanvraag"

    timeline.append({
        "type": event_type,
        "label": aanvraag_label,
        "date": aanvraag_datum,
        "zaak_label": zaak_label,
        "zaak_id": zaak_id,
        "details": serialize_details({
            "BSN": toeslag.bsn,
            "Berekeningsjaar": toeslag.berekeningsjaar,
        }),
    })

    # Add berekening event if calculated
    if toeslag.heeft_aanspraak is not None:
        berekening_datum_raw = getattr(toeslag, "berekening_datum", None)
        berekening_datum = berekening_datum_raw.isoformat() if berekening_datum_raw else aanvraag_datum
        label_suffix = f" {berekeningsjaar}" if berekeningsjaar else ""
        timeline.append({
            "type": "berekening",
            "label": f"Aanspraak berekend{label_suffix}" if toeslag.heeft_aanspraak else f"Geen aanspraak{label_suffix}",
            "date": berekening_datum,
            "zaak_label": zaak_label,
            "zaak_id": zaak_id,
            "details": serialize_details({
                "Heeft aanspraak": "Ja" if toeslag.heeft_aanspraak else "Nee",
                "Jaarbedrag": format_cents_fn(toeslag.berekend_jaarbedrag),
            }),
        })

    # Beschikking type labels
    BESCHIKKING_LABELS = {
        "VOORSCHOT": "Voorschotbeschikking",
        "DEFINITIEF": "Definitieve beschikking",
        "AFWIJZING": "Afwijzingsbeschikking",
        "HERZIEN_VOORSCHOT": "Herziene voorschotbeschikking",
        "IB_AANSLAG_ONTVANGEN": "IB-aanslag ontvangen",
    }

    # Add beschikkingen
    for beschikking in (toeslag.beschikkingen or []):
        beschikking_type = beschikking.get("type", "ONBEKEND")
        beschikking_datum = beschikking.get("datum")
        if isinstance(beschikking_datum, date):
            beschikking_datum = beschikking_datum.isoformat()

        details = {}
        for k, v in beschikking.items():
            if k in ["type", "datum"]:
                continue
            if k in ["jaarbedrag", "maandbedrag", "bedrag"]:
                details[k.replace("_", " ").title()] = format_cents_fn(v)
            else:
                details[k.replace("_", " ").title()] = serialize_value(v)

        # Use friendly label or fallback to formatted type
        label = BESCHIKKING_LABELS.get(beschikking_type, beschikking_type.replace("_", " ").title())

        timeline.append({
            "type": "beschikking",
            "label": label,
            "date": beschikking_datum,
            "zaak_label": zaak_label,
            "zaak_id": zaak_id,
            "details": details,
        })

    # Dutch month names for display
    MAAND_NAMEN = {
        1: "januari", 2: "februari", 3: "maart", 4: "april",
        5: "mei", 6: "juni", 7: "juli", 8: "augustus",
        9: "september", 10: "oktober", 11: "november", 12: "december",
    }

    # Add monthly calculations
    for berekening in (toeslag.maandelijkse_berekeningen or []):
        berekening_datum = berekening.get("berekening_datum")
        if isinstance(berekening_datum, date):
            berekening_datum = berekening_datum.isoformat()

        maand_nr = berekening["maand"]
        maand_naam = MAAND_NAMEN.get(maand_nr, str(maand_nr))

        timeline.append({
            "type": "herberekening",
            "label": f"Herberekening {maand_naam}",
            "date": berekening_datum,
            "zaak_label": zaak_label,
            "zaak_id": zaak_id,
            "details": serialize_details({
                "Maand": maand_naam.capitalize(),
                "Berekend bedrag": format_cents_fn(berekening["berekend_bedrag"]),
            }),
        })

    # Add monthly payments
    for betaling in (toeslag.maandelijkse_betalingen or []):
        betaal_datum = betaling.get("betaal_datum")
        if isinstance(betaal_datum, date):
            betaal_datum = betaal_datum.isoformat()

        maand_nr = betaling["maand"]
        maand_naam = MAAND_NAMEN.get(maand_nr, str(maand_nr))
        betaald_bedrag = format_cents_fn(betaling.get("betaald_bedrag"))

        timeline.append({
            "type": "betaling",
            "label": f"Betaling {maand_naam}",
            "date": betaal_datum,
            "zaak_label": zaak_label,
            "zaak_id": zaak_id,
            "details": serialize_details({
                "Maand": maand_naam.capitalize(),
                "Bedrag": betaald_bedrag,
            }),
        })

    # Add definitieve beschikking event
    if toeslag.status in [CaseStatus.DEFINITIEF, CaseStatus.VEREFFEND]:
        definitief_datum = getattr(toeslag, "definitieve_beschikking_datum", None)
        if isinstance(definitief_datum, date):
            definitief_datum = definitief_datum.isoformat()

        maandelijkse_berekeningen = getattr(toeslag, "maandelijkse_berekeningen", None) or []
        maandelijkse_betalingen = getattr(toeslag, "maandelijkse_betalingen", None) or []
        totaal_berekend = sum(b.get("berekend_bedrag", 0) for b in maandelijkse_berekeningen)
        totaal_betaald = sum(b.get("betaald_bedrag", 0) for b in maandelijkse_betalingen)
        definitief_jaarbedrag = getattr(toeslag, "definitief_jaarbedrag", None)

        timeline.append({
            "type": "definitieve_beschikking",
            "label": f"Definitieve beschikking {berekeningsjaar}",
            "date": definitief_datum,
            "zaak_label": zaak_label,
            "zaak_id": zaak_id,
            "details": serialize_details({
                "Definitief jaarbedrag": format_cents_fn(definitief_jaarbedrag),
                "Totaal berekend": format_cents_fn(totaal_berekend),
                "Totaal betaald": format_cents_fn(totaal_betaald),
            }),
        })

    # Add vereffening event
    if toeslag.status == CaseStatus.VEREFFEND:
        vereffening_datum = getattr(toeslag, "vereffening_datum", None)
        if isinstance(vereffening_datum, date):
            vereffening_datum = vereffening_datum.isoformat()

        vereffening_type = getattr(toeslag, "vereffening_type", None)
        vereffening_bedrag = getattr(toeslag, "vereffening_bedrag", None)

        timeline.append({
            "type": "vereffening",
            "label": f"Vereffening: {vereffening_type}",
            "date": vereffening_datum,
            "zaak_label": zaak_label,
            "zaak_id": zaak_id,
            "details": serialize_details({
                "Type": vereffening_type,
                "Bedrag": format_cents_fn(vereffening_bedrag),
            }),
        })

    return timeline


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


@router.post("/simulate/reset")
async def reset_simulation(
    request: Request,
    bsn: str = Form(...),
    case_id: str = Form(None),
    reset_date: str = Form(None),
    redirect_url: str = Form(None),
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

    # Use provided redirect_url or fallback to default
    if not redirect_url:
        redirect_url = f"/zaken/{case_id}?bsn={bsn}" if case_id else f"/zaken/?bsn={bsn}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.post("/simulate")
async def simulate_time(
    request: Request,
    target_date: str = Form(...),
    bsn: str = Form(...),
    case_id: str = Form(None),
    redirect_url: str = Form(None),
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_zaken_case_manager),
):
    """Advance simulation date and process all non-finalized toeslagen"""
    current_date = get_simulated_date(request)
    target = date.fromisoformat(target_date)

    logger.warning(f"[SIMULATE] current_date={current_date}, target={target}, bsn={bsn}, case_id={case_id}")

    # Don't process if target is before or equal to current
    if target <= current_date:
        logger.warning("[SIMULATE] Target date not in future, just updating session")
        set_simulated_date(request, target)
        # Use provided redirect_url or fallback to default
        if not redirect_url:
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
    # Use provided redirect_url or fallback to default
    if not redirect_url:
        redirect_url = f"/zaken/{case_id}?bsn={bsn}" if case_id else f"/zaken/?bsn={bsn}"
    return RedirectResponse(url=redirect_url, status_code=303)


@router.get("/tijdlijn")
async def zaken_tijdlijn(
    request: Request,
    bsn: str = "100000001",
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_zaken_case_manager),
):
    """Show combined multi-year timeline for all toeslagen for a BSN"""
    try:
        profile = machine_service.get_profile_data(bsn)
        simulated_date = get_simulated_date(request)

        # Get all toeslagen for this BSN
        all_cases = case_manager.get_cases_by_bsn(bsn)
        toeslagen = [c for c in all_cases if c.service == "TOESLAGEN"]

        # If no toeslagen, redirect to zaken index
        if not toeslagen:
            return RedirectResponse(url=f"/zaken/?bsn={bsn}", status_code=303)

        # Sort by berekeningsjaar to show oldest first (handle None values)
        toeslagen.sort(key=lambda c: c.berekeningsjaar or (c.created_at.year if c.created_at else 0))

        # Build combined timeline from all toeslagen
        timeline = []
        for case in toeslagen:
            timeline.extend(build_timeline_for_case(case, format_cents))

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

        # Group timeline by month
        grouped_timeline = group_timeline_by_month(timeline, simulated_date)

        # Use the first toeslag for display purposes
        toeslag = toeslagen[0]

        # Get profile name
        profile_name = profile.get("name", "") if profile else ""

        # Get aanvraag datum for display (from first case)
        aanvraag_datum_display = toeslag.created_at.date().isoformat() if toeslag.created_at else None

        return templates.TemplateResponse(
            "zaken/detail.html",
            {
                "request": request,
                "bsn": bsn,
                "profile": profile,
                "profile_name": profile_name,
                "toeslag": toeslag,
                "type_label": "Alle toeslagen",
                "status_label": "",
                "status_color": "",
                "timeline": timeline,
                "grouped_timeline": grouped_timeline,
                "totaal_berekend": 0,
                "totaal_betaald": 0,
                "CaseStatus": CaseStatus,
                "format_cents": format_cents,
                "all_profiles": machine_service.get_all_profiles(),
                "simulated_date": simulated_date.isoformat(),
                "today": date.today().isoformat(),
                "aanvraag_datum_display": aanvraag_datum_display,
                "related_cases": toeslagen,
            },
        )
    except Exception as e:
        logger.exception(f"[TIJDLIJN] Error in zaken_tijdlijn: {e}")
        raise


@router.get("/{case_id}")
async def zaken_detail(
    request: Request,
    case_id: str,
    bsn: str = "100000001",
    machine_service: EngineInterface = Depends(get_machine_service),
    case_manager=Depends(get_zaken_case_manager),
):
    """Show toeslag detail with full multi-year timeline"""
    profile = machine_service.get_profile_data(bsn)
    simulated_date = get_simulated_date(request)

    # Get case by ID
    toeslag = case_manager.get_case_by_id(case_id)

    if not toeslag:
        return templates.TemplateResponse(
            "zaken/not_found.html",
            {
                "request": request,
                "bsn": bsn,
                "case_id": case_id,
            },
            status_code=404,
        )

    # Get status badge for current case
    status_label, status_color = get_status_badge(toeslag.status)

    # Get all related cases for multi-year timeline (same BSN and law)
    all_cases = case_manager.get_cases_by_bsn(bsn)
    related_cases = [c for c in all_cases if c.law == toeslag.law]
    # Sort by berekeningsjaar to show oldest first (handle None values)
    related_cases.sort(key=lambda c: c.berekeningsjaar or (c.created_at.year if c.created_at else 0))

    logger.info(f"[ZAKEN] Found {len(related_cases)} related cases for BSN {bsn} and law {toeslag.law}")

    # Build combined timeline from all related cases
    timeline = []
    for case in related_cases:
        timeline.extend(build_timeline_for_case(case, format_cents))

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
    logger.info(f"[ZAKEN] Combined timeline has {len(timeline)} events from {len(related_cases)} cases")
    grouped_timeline = group_timeline_by_month(timeline, simulated_date)
    logger.info(f"[ZAKEN] Grouped timeline has {len(grouped_timeline)} months")

    # Calculate year totals for current case
    totaal_berekend = sum(b.get("berekend_bedrag", 0) for b in (toeslag.maandelijkse_berekeningen or []))
    totaal_betaald = sum(b.get("betaald_bedrag", 0) for b in (toeslag.maandelijkse_betalingen or []))

    # Get profile name
    profile_name = profile.get("name", "") if profile else ""

    # Get aanvraag datum for display
    aanvraag_datum_display = toeslag.created_at.date().isoformat() if toeslag.created_at else None

    return templates.TemplateResponse(
        "zaken/detail.html",
        {
            "request": request,
            "bsn": bsn,
            "profile": profile,
            "profile_name": profile_name,
            "toeslag": toeslag,
            "type_label": get_type_label(toeslag.law),
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
            "today": date.today().isoformat(),
            "aanvraag_datum_display": aanvraag_datum_display,
            "related_cases": related_cases,  # For multi-year display
        },
    )
