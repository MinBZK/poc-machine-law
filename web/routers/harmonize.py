import asyncio
import json
import logging
import os
import subprocess
from datetime import datetime

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from explain.llm_factory import LLMFactory, llm_factory
from web.demo.translations import get_lang, get_translations
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
    {"id": "precariobelasting", "label": "Precariobelasting", "group": "Belastingen"},
    {"id": "cbs_enquete", "label": "CBS Statistiekverplichting", "group": "Rapportageverplichtingen"},
    {"id": "kvk_jaarrekening", "label": "Jaarrekening Deponeringsplicht", "group": "Rapportageverplichtingen"},
    {"id": "nvwa_meldplicht", "label": "Meldplicht Voedselveiligheid", "group": "Rapportageverplichtingen"},
]
_BUSINESS_DEFAULT = [
    "alcoholwet",
    "haccp",
    "energie_informatieplicht",
    "precariobelasting",
    "cbs_enquete",
    "kvk_jaarrekening",
    "nvwa_meldplicht",
]


@router.get("/")
async def harmonize_page(request: Request):
    """Render the harmonisatie configuration page."""
    lang = get_lang(request)
    t = get_translations(lang)

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
            "t": t,
            "lang": lang,
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


PROSE_SYSTEM_PROMPT = (
    "Je bent een ervaren wetgevingsjurist bij de Directie Wetgeving van het Ministerie van "
    "Sociale Zaken en Werkgelegenheid. Je schrijft wetteksten conform de Aanwijzingen voor de "
    "regelgeving (Ar) en in de stijl van het Staatsblad van het Koninkrijk der Nederlanden. "
    "Je kent de Wet op de zorgtoeslag, de Participatiewet en de Algemene wet inkomensafhankelijke "
    "regelingen (Awir) goed en gebruikt dezelfde formuleringen en structuur."
)

PROSE_USER_PROMPT = """Hieronder staat een machine-leesbare wetspecificatie in YAML-formaat die \
een geharmoniseerde regeling beschrijft. Schrijf hiervan een volledige, formele Nederlandse wettekst.

## Structuur (volg de Aanwijzingen voor de regelgeving)

Gebruik EXACT deze opbouw:

1. **Aanhef**: Begin met de considerans in de vorm:
   "Wet van [huidige datum], houdende regels inzake [korte omschrijving] ([citeertitel])"
   Gevolgd door: "Wij Willem-Alexander, bij de gratie Gods, Koning der Nederlanden, ..."
   En: "Alzo Wij in overweging genomen hebben, dat het wenselijk is [motivering];"
   Eindigend met: "Zo is het, dat Wij, de Raad van State gehoord, en met gemeen overleg \
der Staten-Generaal, hebben goedgevonden en verstaan, gelijk Wij goedvinden en verstaan bij deze:"

2. **Hoofdstuk 1 – Algemene bepalingen**: Met een Artikel 1 "Begripsbepalingen" dat begint met:
   "In deze wet en de daarop berustende bepalingen wordt verstaan onder:"
   Gevolgd door een alfabetisch geordende opsomming (a. b. c.) van alle termen uit de YAML, \
gescheiden door puntkomma's.

3. **Hoofdstuk 2 – Aanspraken en berekeningen**: Artikelen die de daadwerkelijke berekeningen \
beschrijven. Gebruik de volgende formuleringen:
   - Voor bedragen: "EUR [bedrag]" (bijv. "EUR 160" — de YAML bevat hele euro's per maand)
   - Voor percentages: "bedraagt [X]% van [grondslag]"
   - Voor optelling: "vermeerderd met"
   - Voor aftrek: "verminderd met"
   - Voor drempels: "voorzover dat [bedrag] het [drempel] te boven gaat"
   - Voor voorwaarden: "Indien" (niet "Als")
   - Voor uitzonderingen: "In afwijking van [artikel X]" of "tenzij anders bepaald"
   - Voor aanspraken: "heeft de belanghebbende aanspraak op" of "bestaat recht op"
   - Voor afwezigheid van recht: "Geen aanspraak op [X] bestaat indien"

4. **Hoofdstuk 3 – Slotbepalingen**: Met:
   - Inwerkingtredingsartikel: "Deze wet treedt in werking op een bij koninklijk besluit \
te bepalen tijdstip."
   - Citeertitelartikel: "Deze wet wordt aangehaald als: [naam]."

## Artikelopbouw (conform Ar 3.58 en 3.59)

- Elk artikel heeft een nummer: "Artikel 1.", "Artikel 2.", etc.
- Binnen een artikel zijn leden genummerd: 1. 2. 3.
- Opsommingen binnen een lid gebruiken letters: a. b. c. (gescheiden door puntkomma's)
- Sub-onderdelen gebruiken: 1°. 2°. 3°.
- Verwijs naar andere artikelen als: "bedoeld in artikel [X], [N]e lid, onderdeel [Y]"

## Taalgebruik

- Schrijf in de tegenwoordige tijd, lijdende vorm waar passend
- Gebruik "de belanghebbende", "de verzekerde", "het toetsingsinkomen" — niet "u" of "je"
- Gebruik "Onze Minister" voor delegatiebepalingen
- Gebruik "Bij ministeriële regeling" of "Bij algemene maatregel van bestuur" voor delegatie
- Elke berekening, toeslag, drempel en voorwaarde uit de YAML MOET in de wettekst staan

## Markdown-opmaak

- `#` voor de citeertitel
- `##` voor hoofdstukken ("## Hoofdstuk 1. Algemene bepalingen")
- `###` voor artikelen ("### Artikel 1. Begripsbepalingen")
- Gewone tekst voor leden (genummerd met 1. 2. 3.)
- Opsommingen met a. b. c. voor onderdelen
- `---` als scheiding tussen de aanhef en het eerste hoofdstuk

## YAML-specificatie

```yaml
{yaml_text}
```
{extra_context}
Schrijf nu de volledige wettekst. Neem ALLE berekeningen, operaties, bedragen, toeslagen \
en voorwaarden uit de YAML nauwkeurig over — mis geen enkele regel of component."""


MAX_YAML_SIZE = 50_000  # ~50KB limit for YAML sent to LLM


def _make_llm_call(provider: str, api_key: str, yaml_text: str, extra_context: str = "") -> str:
    """Create a request-scoped LLM client and generate prose law text.

    This avoids mutating the shared singleton service, making it safe
    to call from a worker thread without racing other requests.

    Raises:
        RuntimeError: If the LLM call fails or returns no response.
    """
    ctx = ""
    if extra_context:
        ctx = f"\nSamenvatting van het model (ter referentie):\n{extra_context}\n"
    messages = [{"role": "user", "content": PROSE_USER_PROMPT.format(yaml_text=yaml_text, extra_context=ctx)}]

    if provider == LLMFactory.PROVIDER_CLAUDE:
        import anthropic

        client = anthropic.Anthropic(api_key=api_key)
        response = client.messages.create(
            model="claude-opus-4-6",
            max_tokens=8000,
            temperature=0.3,
            system=PROSE_SYSTEM_PROMPT,
            messages=messages,
        )
        return response.content[0].text

    elif provider == LLMFactory.PROVIDER_VLAM:
        from openai import OpenAI

        base_url = os.getenv("VLAM_BASE_URL", "https://api.demo.vlam.ai/v2.1/projects/poc/openai-compatible/v1")
        model_id = os.getenv("VLAM_MODEL_ID", "ubiops-deployment/bzk-dig-chat//chat-model")
        client = OpenAI(api_key=api_key, base_url=base_url)
        all_messages = [{"role": "system", "content": PROSE_SYSTEM_PROMPT}, *messages]
        response = client.chat.completions.create(
            model=model_id,
            messages=all_messages,
            max_tokens=4000,
            temperature=0.3,
        )
        return response.choices[0].message.content

    else:
        raise RuntimeError(f"Onbekende LLM provider: {provider}")


@router.post("/generate-prose")
async def generate_prose(request: Request):
    """Generate a prose law text from a YAML specification using an LLM."""
    body = await request.json()
    yaml_text = body.get("yaml", "")
    explanation = body.get("explanation", "")

    if not yaml_text:
        return JSONResponse(status_code=400, content={"status": "error", "message": "Geen YAML opgegeven"})

    if len(yaml_text) > MAX_YAML_SIZE:
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"YAML is te groot ({len(yaml_text)} tekens, max {MAX_YAML_SIZE}).",
            },
        )

    provider = llm_factory.get_provider(request)
    if not llm_factory.is_provider_configured(provider, request):
        return JSONResponse(
            status_code=400,
            content={
                "status": "error",
                "message": f"LLM provider '{provider}' is niet geconfigureerd. "
                "Stel een API-sleutel in via de instellingen.",
            },
        )

    # Extract the API key on the async thread (safe to access request.session here).
    service = llm_factory.get_service(provider)
    api_key = service.get_api_key(request)

    try:
        prose = await asyncio.to_thread(_make_llm_call, provider, api_key, yaml_text, explanation)
        return JSONResponse({"status": "success", "prose": prose, "provider": provider})
    except Exception as e:
        logger.error("Failed to generate prose: %s", str(e))
        return JSONResponse(
            status_code=500,
            content={"status": "error", "message": "Wettekst genereren mislukt. Probeer het later opnieuw."},
        )
