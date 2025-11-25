"""Zaken router for workflow-based toeslag management"""

import logging
from datetime import date, datetime

from fastapi import APIRouter, Depends, Form, Request
from fastapi.responses import RedirectResponse

from machine.events.toeslag.aggregate import ToeslagStatus, ToeslagType
from machine.events.toeslag.timesimulator import TimeSimulator
from web.dependencies import (
    TODAY,
    get_machine_service,
    get_simulated_date,
    get_toeslag_manager,
    set_simulated_date,
    templates,
)
from web.engines import EngineInterface

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/zaken", tags=["zaken"])

# Finalized statuses that should not be processed during time simulation
FINALIZED_STATUSES = {
    ToeslagStatus.DEFINITIEF,
    ToeslagStatus.VEREFFEND,
    ToeslagStatus.AFGEWEZEN,
    ToeslagStatus.BEEINDIGD,
}


def is_processable(toeslag) -> bool:
    """Check if a toeslag should be processed during time simulation"""
    return toeslag.status not in FINALIZED_STATUSES

# Status badge mapping for display
STATUS_BADGES = {
    ToeslagStatus.AANVRAAG: ("Aanvraag ingediend", "yellow"),
    ToeslagStatus.BEREKEND: ("Berekend", "blue"),
    ToeslagStatus.VOORSCHOT: ("Voorschot vastgesteld", "purple"),
    ToeslagStatus.LOPEND: ("Lopend", "green"),
    ToeslagStatus.DEFINITIEF: ("Definitief", "green"),
    ToeslagStatus.VEREFFEND: ("Vereffend", "gray"),
    ToeslagStatus.AFGEWEZEN: ("Afgewezen", "red"),
    ToeslagStatus.BEEINDIGD: ("Beeindigd", "gray"),
}

# Type labels for display
TYPE_LABELS = {
    ToeslagType.ZORGTOESLAG: "Zorgtoeslag",
    ToeslagType.HUURTOESLAG: "Huurtoeslag",
    ToeslagType.KINDGEBONDEN_BUDGET: "Kindgebonden budget",
    ToeslagType.KINDEROPVANGTOESLAG: "Kinderopvangtoeslag",
}


def get_status_badge(status: ToeslagStatus) -> tuple[str, str]:
    """Get the display label and color for a status"""
    # Handle both enum and string status values
    if isinstance(status, str):
        try:
            status = ToeslagStatus(status)
        except ValueError:
            return (status, "gray")
    return STATUS_BADGES.get(status, (str(status), "gray"))


def get_type_label(toeslag_type: ToeslagType) -> str:
    """Get the display label for a toeslag type"""
    # Handle both enum and string type values
    if isinstance(toeslag_type, str):
        try:
            toeslag_type = ToeslagType(toeslag_type)
        except ValueError:
            return toeslag_type
    return TYPE_LABELS.get(toeslag_type, str(toeslag_type))


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
    toeslag_manager=Depends(get_toeslag_manager),
):
    """List all toeslagen for a citizen"""
    # Get profile for display
    profile = machine_service.get_profile_data(bsn)
    simulated_date = get_simulated_date(request)

    # Get all toeslagen for this BSN
    toeslagen = toeslag_manager.get_toeslagen_by_bsn(bsn)

    # Enrich toeslagen with display data
    toeslagen_display = []
    for toeslag in toeslagen:
        status_label, status_color = get_status_badge(toeslag.status)
        toeslagen_display.append({
            "id": str(toeslag.id),
            "oid": toeslag.oid,
            "type": toeslag.type,
            "type_label": get_type_label(toeslag.type),
            "berekeningsjaar": toeslag.berekeningsjaar,
            "status": toeslag.status,
            "status_label": status_label,
            "status_color": status_color,
            "aanvraag_datum": toeslag.aanvraag_datum,
            "berekend_jaarbedrag": toeslag.berekend_jaarbedrag,
            "berekend_jaarbedrag_display": format_cents(toeslag.berekend_jaarbedrag),
            "voorschot_maandbedrag": toeslag.voorschot_maandbedrag,
            "voorschot_maandbedrag_display": format_cents(toeslag.voorschot_maandbedrag),
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
    toeslag_manager=Depends(get_toeslag_manager),
):
    """Submit a zorgtoeslag aanvraag"""
    simulated_date = get_simulated_date(request)
    simulated_date_str = simulated_date.isoformat()

    try:
        # 1. Create toeslag via toeslag_manager with simulated date
        toeslag_id = toeslag_manager.dien_aanvraag_in(
            bsn=bsn,
            toeslag_type=ToeslagType.ZORGTOESLAG,
            berekeningsjaar=berekeningsjaar,
            aanvraag_datum=simulated_date_str,
        )

        # 2. Calculate eligibility using rules engine with simulated date
        result = machine_service.evaluate(
            service="TOESLAGEN",
            law="zorgtoeslagwet",
            parameters={"BSN": bsn},
            reference_date=simulated_date_str,
        )

        # 3. Determine eligibility and amount
        berekend_jaarbedrag = result.output.get("hoogte_toeslag", 0)
        heeft_aanspraak = berekend_jaarbedrag > 0

        # 4. Update toeslag with calculation result using simulated date
        toeslag_manager.bereken_aanspraak(
            toeslag_id=toeslag_id,
            heeft_aanspraak=heeft_aanspraak,
            berekend_jaarbedrag=berekend_jaarbedrag,
            berekening_datum=simulated_date_str,
        )

        # 5. If eligible, automatically set voorschot using simulated date
        if heeft_aanspraak:
            toeslag_manager.stel_voorschot_vast(
                toeslag_id=toeslag_id,
                beschikking_datum=simulated_date_str,
            )

        # 6. Redirect to detail page
        return RedirectResponse(
            url=f"/zaken/{toeslag_id}?bsn={bsn}",
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
    toeslag_manager=Depends(get_toeslag_manager),
):
    """Reset simulation date to aanvraag date or specified date"""
    if reset_date:
        new_date = date.fromisoformat(reset_date)
    elif toeslag_id:
        toeslag = toeslag_manager.get_toeslag_by_id(toeslag_id)
        if toeslag and toeslag.aanvraag_datum:
            new_date = date.fromisoformat(toeslag.aanvraag_datum)
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
    toeslag_manager=Depends(get_toeslag_manager),
):
    """Advance simulation date and process all non-finalized toeslagen"""
    current_date = get_simulated_date(request)
    target = date.fromisoformat(target_date)

    logger.warning(f"[SIMULATE] current_date={current_date}, target={target}, bsn={bsn}, toeslag_id={toeslag_id}")

    # Don't process if target is before or equal to current
    if target <= current_date:
        logger.warning(f"[SIMULATE] Target date not in future, just updating session")
        set_simulated_date(request, target)
        redirect_url = f"/zaken/{toeslag_id}?bsn={bsn}" if toeslag_id else f"/zaken/?bsn={bsn}"
        return RedirectResponse(url=redirect_url, status_code=303)

    # Get all non-finalized toeslagen for this BSN
    toeslagen = toeslag_manager.get_toeslagen_by_bsn(bsn)
    processable = [t for t in toeslagen if is_processable(t)]

    logger.warning(f"[SIMULATE] Found {len(toeslagen)} toeslagen, {len(processable)} processable")

    # Get the underlying services from machine_service for TimeSimulator
    services = machine_service.get_services()

    # Process each toeslag through time simulation
    for toeslag in processable:
        logger.warning(f"[SIMULATE] Processing toeslag {toeslag.id}: status={toeslag.status}, berekeningsjaar={toeslag.berekeningsjaar}")
        simulator = TimeSimulator(
            toeslag_manager=toeslag_manager,
            start_date=current_date,
            services=services,
        )
        results = simulator.step_to_date(
            toeslag_id=str(toeslag.id),
            target_date=target,
            parameters={"BSN": bsn},
        )
        logger.warning(f"[SIMULATE] Processed {len(results)} months for toeslag {toeslag.id}")

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
    toeslag_manager=Depends(get_toeslag_manager),
):
    """Show toeslag detail with full timeline"""
    profile = machine_service.get_profile_data(bsn)
    simulated_date = get_simulated_date(request)

    # Get toeslag by ID
    toeslag = toeslag_manager.get_toeslag_by_id(toeslag_id)

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

    # Build timeline events
    timeline = []

    # Add aanvraag event
    timeline.append({
        "type": "aanvraag",
        "label": "Aanvraag ingediend",
        "date": toeslag.aanvraag_datum,
        "icon": "document",
        "details": {
            "BSN": toeslag.bsn,
            "Berekeningsjaar": toeslag.berekeningsjaar,
        },
    })

    # Add berekening event if calculated
    if toeslag.heeft_aanspraak is not None:
        timeline.append({
            "type": "berekening",
            "label": "Aanspraak berekend" if toeslag.heeft_aanspraak else "Geen aanspraak",
            "date": toeslag.aanvraag_datum,  # Same day for now
            "icon": "calculator" if toeslag.heeft_aanspraak else "x-circle",
            "details": {
                "Heeft aanspraak": "Ja" if toeslag.heeft_aanspraak else "Nee",
                "Jaarbedrag": format_cents(toeslag.berekend_jaarbedrag),
            },
        })

    # Add beschikkingen
    for beschikking in toeslag.beschikkingen:
        beschikking_type = beschikking.get("type", "ONBEKEND")
        timeline.append({
            "type": "beschikking",
            "label": beschikking_type.replace("_", " ").title(),
            "date": beschikking.get("datum"),
            "icon": "document-check",
            "details": {k: v for k, v in beschikking.items() if k != "type" and k != "datum"},
        })

    # Add monthly calculations
    for berekening in toeslag.maandelijkse_berekeningen:
        timeline.append({
            "type": "maand_berekening",
            "label": f"Maand {berekening['maand']} herberekend",
            "date": berekening.get("berekening_datum"),
            "icon": "refresh",
            "details": {
                "Maand": berekening["maand"],
                "Berekend bedrag": format_cents(berekening["berekend_bedrag"]),
                "Trigger": berekening.get("trigger", "schedule"),
            },
        })

    # Add monthly payments
    for betaling in toeslag.maandelijkse_betalingen:
        timeline.append({
            "type": "maand_betaling",
            "label": f"Maand {betaling['maand']} betaald",
            "date": betaling.get("betaal_datum"),
            "icon": "currency-euro",
            "details": {
                "Maand": betaling["maand"],
                "Betaald bedrag": format_cents(betaling["betaald_bedrag"]),
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

    return templates.TemplateResponse(
        "zaken/detail.html",
        {
            "request": request,
            "bsn": bsn,
            "profile": profile,
            "toeslag": toeslag,
            "type_label": get_type_label(toeslag.type),
            "status_label": status_label,
            "status_color": status_color,
            "timeline": timeline,
            "format_cents": format_cents,
            "all_profiles": machine_service.get_all_profiles(),
            "simulated_date": simulated_date.isoformat(),
        },
    )
