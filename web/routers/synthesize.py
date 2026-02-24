import asyncio
import json
import logging
import subprocess

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from web.dependencies import is_demo_mode, templates

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/synthesize", tags=["synthesize"])

# Timeout in seconds: ~25 persons/sec means 5000 persons takes ~200s, plus training overhead
SUBPROCESS_TIMEOUT = 300


@router.get("/")
async def synthesize_page(request: Request):
    """Render the synthesis configuration page."""
    return templates.TemplateResponse(
        "synthesize.html",
        {
            "request": request,
            "demo_mode": is_demo_mode(request),
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


@router.post("/train")
async def train_model(request: Request):
    """Train a synthesized law model via subprocess."""
    body = await request.json()
    body["operation"] = "train"
    return await asyncio.to_thread(_run_synthesize_subprocess, body)


@router.post("/validate")
async def validate_model(request: Request):
    """Validate a synthesized law model via subprocess."""
    body = await request.json()
    body["operation"] = "validate"
    return await asyncio.to_thread(_run_synthesize_subprocess, body)
