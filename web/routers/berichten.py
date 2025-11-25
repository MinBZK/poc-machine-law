"""
Berichten router voor de berichtenbox functionaliteit.

Wettelijke grondslag:
- AWIR Art. 13: Elektronisch berichtenverkeer
- AWB Art. 3:40-3:45: Bekendmaking besluiten
"""

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from web.dependencies import (
    get_machine_service,
    get_message_manager,
    get_zaken_case_manager,
    templates,
)

router = APIRouter(prefix="/berichten", tags=["berichten"])

# Rechtsmiddelenclausule conform AWB Art. 3:45
RECHTSMIDDEL_INFO = """Bent u het niet eens met deze beslissing? Dan kunt u binnen 6 weken bezwaar maken. Ga naar mijn.toeslagen.nl of bel de BelastingTelefoon."""


@router.get("/", response_class=HTMLResponse)
async def berichten_index(
    request: Request,
    bsn: str,
    message_manager=Depends(get_message_manager),
    services=Depends(get_machine_service),
):
    """
    Berichtenbox - overzicht van alle berichten voor een burger.
    """
    messages = message_manager.get_messages_by_bsn(bsn)
    unread_count = message_manager.get_unread_count(bsn)

    return templates.TemplateResponse(
        "berichten/index.html",
        {
            "request": request,
            "bsn": bsn,
            "messages": messages,
            "unread_count": unread_count,
            "all_profiles": services.get_all_profiles(),
            "chat_enabled": False,
        },
    )


@router.get("/{message_id}", response_class=HTMLResponse)
async def bericht_detail(
    request: Request,
    message_id: str,
    bsn: str,
    message_manager=Depends(get_message_manager),
    case_manager=Depends(get_zaken_case_manager),
    services=Depends(get_machine_service),
):
    """
    Bericht detail - toont het volledige bericht en markeert als gelezen.
    Conform AWB Art. 3:40: Besluit treedt in werking na bekendmaking.
    """
    message = message_manager.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Bericht niet gevonden")

    # Controleer of het bericht bij deze BSN hoort
    if message.bsn != bsn:
        raise HTTPException(status_code=403, detail="Geen toegang tot dit bericht")

    # Markeer als gelezen
    message_manager.mark_as_read(message_id)

    # Haal gerelateerde zaak op indien beschikbaar
    case = None
    if message.case_id:
        case = case_manager.get_case_by_id(message.case_id)

    unread_count = message_manager.get_unread_count(bsn)

    return templates.TemplateResponse(
        "berichten/detail.html",
        {
            "request": request,
            "bsn": bsn,
            "message": message,
            "case": case,
            "unread_count": unread_count,
            "all_profiles": services.get_all_profiles(),
            "chat_enabled": False,
        },
    )


@router.post("/{message_id}/archive")
async def archive_bericht(
    message_id: str,
    bsn: str,
    message_manager=Depends(get_message_manager),
):
    """
    Archiveer een bericht.
    """
    message = message_manager.get_message_by_id(message_id)
    if not message:
        raise HTTPException(status_code=404, detail="Bericht niet gevonden")

    if message.bsn != bsn:
        raise HTTPException(status_code=403, detail="Geen toegang tot dit bericht")

    message_manager.archive_message(message_id)

    return RedirectResponse(url=f"/berichten?bsn={bsn}", status_code=303)


@router.get("/api/unread-count")
async def get_unread_count(
    bsn: str,
    message_manager=Depends(get_message_manager),
):
    """
    API endpoint om het aantal ongelezen berichten op te halen.
    Kan gebruikt worden voor polling of HTMX updates.
    """
    count = message_manager.get_unread_count(bsn)
    return {"unread_count": count}
