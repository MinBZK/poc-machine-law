import asyncio
import json
import logging
import subprocess
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from web.demo_profiles import get_demo_profile_type
from web.dependencies import is_demo_mode, templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/harmonize", tags=["harmonize"])

# Timeout in seconds: ~25 persons/sec means 5000 persons takes ~200s, plus training overhead
SUBPROCESS_TIMEOUT = 300

# Available laws per profile type
_CITIZEN_LAWS = [
    {"id": "zorgtoeslag", "label": "Zorgtoeslag", "group": "Toeslagen"},
    {"id": "huurtoeslag", "label": "Huurtoeslag", "group": "Toeslagen"},
    {"id": "kindgebonden_budget", "label": "Kindgebonden budget", "group": "Toeslagen"},
    {"id": "kinderopvangtoeslag", "label": "Kinderopvangtoeslag", "group": "Toeslagen"},
    {"id": "bijstand", "label": "Bijstand", "group": "Sociale zekerheid"},
    {"id": "aow", "label": "AOW", "group": "Sociale zekerheid"},
    {"id": "ww", "label": "WW-uitkering", "group": "Sociale zekerheid"},
]
_CITIZEN_DEFAULT = ["zorgtoeslag", "huurtoeslag", "kindgebonden_budget"]

_BUSINESS_LAWS = [
    {"id": "alcoholwet", "label": "Alcoholwet", "group": "Vergunningen"},
    {"id": "haccp", "label": "HACCP Voedselveiligheid", "group": "Verplichtingen"},
    {"id": "energie_informatieplicht", "label": "Informatieplicht Energiebesparing", "group": "Verplichtingen"},
    {"id": "cbs_enquete", "label": "CBS Statistiekverplichting", "group": "Rapportageverplichtingen"},
    {"id": "kvk_jaarrekening", "label": "Jaarrekening Deponeringsplicht", "group": "Rapportageverplichtingen"},
    {"id": "nvwa_meldplicht", "label": "Meldplicht Voedselveiligheid", "group": "Rapportageverplichtingen"},
]
_BUSINESS_DEFAULT = [
    "alcoholwet",
    "haccp",
    "energie_informatieplicht",
    "cbs_enquete",
    "kvk_jaarrekening",
    "nvwa_meldplicht",
]


@router.get("/")
async def harmonize_page(request: Request):
    """Render the harmonisatie configuration page."""
    profile_type = get_demo_profile_type()
    is_business = profile_type == "ondernemer"

    if is_business:
        available_laws = _BUSINESS_LAWS
        default_selected = _BUSINESS_DEFAULT
        default_params = {
            "num_people": 500,
            "simulation_date": datetime.now().strftime("%Y-%m-%d"),
            "horeca_percentage": 30,
            "levensmiddelen_percentage": 25,
            "bedrijfsgrootte_klein": 50,
            "bedrijfsgrootte_middel": 35,
            "bedrijfsgrootte_groot": 15,
        }
    else:
        available_laws = _CITIZEN_LAWS
        default_selected = _CITIZEN_DEFAULT
        default_params = {
            "num_people": 1000,
            "simulation_date": datetime.now().strftime("%Y-%m-%d"),
            "age_18_30": 18,
            "age_30_45": 25,
            "age_45_67": 32,
            "age_67_85": 20,
            "age_85_plus": 5,
            "zero_income_prob": 5,
            "rent_percentage": 43,
            "student_percentage_young": 40,
        }

    return templates.TemplateResponse(
        "harmonize.html",
        {
            "request": request,
            "demo_mode": is_demo_mode(request),
            "default_params": default_params,
            "profile_type": profile_type,
            "available_laws": available_laws,
            "default_selected": default_selected,
        },
    )


def _run_synthesize_subprocess(body: dict) -> JSONResponse:
    """Run the synthesis subprocess with proper timeout and error handling."""
    try:
        result = subprocess.run(
            ["uv", "run", "python", "run_synthesize.py"],
            input=json.dumps(body),
            capture_output=True,
            text=True,
            check=False,
            timeout=SUBPROCESS_TIMEOUT,
        )

        if result.returncode != 0:
            # Try to parse structured error from stderr
            stderr = result.stderr.strip()
            try:
                err_data = json.loads(stderr.split("\n")[-1])
                message = err_data.get("message", stderr[-500:])
            except (json.JSONDecodeError, IndexError):
                message = stderr[-500:] if stderr else "Onbekende fout bij training"
            logger.error("Synthesis subprocess failed (rc=%d): %s", result.returncode, stderr[-1000:])
            return JSONResponse(status_code=500, content={"status": "error", "message": message})

        stdout = result.stdout.strip()
        if not stdout:
            return JSONResponse(
                status_code=500, content={"status": "error", "message": "Geen output van trainingsproces"}
            )

        data = json.loads(stdout)
        return JSONResponse(data)

    except subprocess.TimeoutExpired:
        num_people = body.get("num_people", "?")
        logger.error("Synthesis subprocess timed out after %ds (num_people=%s)", SUBPROCESS_TIMEOUT, num_people)
        return JSONResponse(
            status_code=504,
            content={
                "status": "error",
                "message": f"Training duurde te lang (>{SUBPROCESS_TIMEOUT}s). "
                f"Probeer met minder simulatiepersonen (huidig: {num_people}).",
            },
        )
    except json.JSONDecodeError as e:
        logger.error("Failed to parse synthesis output as JSON: %s", str(e))
        return JSONResponse(
            status_code=500, content={"status": "error", "message": "Ongeldig antwoord van trainingsproces"}
        )


VALID_METHODS = {"tree", "bracket", "parametric"}
MAX_NUM_PEOPLE = 10000


def _validate_body(body: dict) -> str | None:
    """Validate request body, return error message or None if valid."""
    num_people = body.get("num_people")
    if num_people is not None:
        try:
            num_people = int(num_people)
        except (TypeError, ValueError):
            return f"num_people moet een geheel getal zijn, kreeg: {num_people}"
        if num_people < 10 or num_people > MAX_NUM_PEOPLE:
            return f"num_people moet tussen 10 en {MAX_NUM_PEOPLE} liggen, kreeg: {num_people}"
        body["num_people"] = num_people

    method = body.get("method")
    if method is not None and method not in VALID_METHODS:
        return f"Onbekende methode: {method}. Kies uit: {', '.join(VALID_METHODS)}"

    selected_laws = body.get("selected_laws")
    if selected_laws is not None and (not isinstance(selected_laws, list) or len(selected_laws) == 0):
        return "Selecteer minimaal één wet"

    return None


@router.post("/train")
async def train_model(request: Request):
    """Train a synthesized law model via subprocess."""
    body = await request.json()
    error = _validate_body(body)
    if error:
        return JSONResponse(status_code=400, content={"status": "error", "message": error})
    body["operation"] = "train"
    return await asyncio.to_thread(_run_synthesize_subprocess, body)


@router.post("/validate")
async def validate_model(request: Request):
    """Validate a synthesized law model via subprocess."""
    body = await request.json()
    error = _validate_body(body)
    if error:
        return JSONResponse(status_code=400, content={"status": "error", "message": error})
    body["operation"] = "validate"
    return await asyncio.to_thread(_run_synthesize_subprocess, body)
