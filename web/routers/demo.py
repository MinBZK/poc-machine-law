"""Demo mode router for presenting law files and running features."""

import asyncio
import json
import uuid
from pathlib import Path
from typing import Any

from fastapi import APIRouter, BackgroundTasks, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse, RedirectResponse

from web.demo.feature_parser import discover_feature_files, parse_feature_file
from web.demo.feature_renderer import render_feature_to_html
from web.demo.feature_runner import run_feature_file
from web.demo.yaml_renderer import discover_laws, parse_law_yaml, render_yaml_to_html
from web.dependencies import templates

router = APIRouter(prefix="/demo", tags=["demo"])

LAW_DIR = Path("law")
FEATURES_DIR = Path("features")
SUBMODULE_LAWS_DIR = Path("submodules/regelrecht-laws/laws")

# Store for ongoing test runs (run_id -> output)
_test_runs: dict[str, dict[str, Any]] = {}
# Store for task references to prevent garbage collection
_active_tasks: set[asyncio.Task] = set()


def filter_behave_output(output: str) -> str:
    """Filter behave output to show only DEBUG and WARNING lines."""
    if not output:
        return ""

    import re
    lines = output.split("\n")
    filtered_lines = []

    for line in lines:
        # Skip HTTP connection logs
        if "Starting new HTTP connection" in line or 'http://localhost' in line:
            continue

        # Check if line starts with whitespace followed by DEBUG or WARNING
        # Pattern: optional whitespace, then DEBUG or WARNING
        match = re.match(r'^(\s*)(DEBUG|WARNING)\s', line)
        if match:
            # Remove the whitespace + DEBUG/WARNING prefix, keep everything else including ║
            prefix_end = match.end()
            filtered_lines.append(line[prefix_end:])

    return "\n".join(filtered_lines) if filtered_lines else output


async def _run_behave_async(run_id: str, feature_path: str, line_number: int | None = None) -> None:
    """Run behave in the background and stream output."""
    print(f"DEBUG: _run_behave_async started for run_id {run_id}")
    try:
        # Ensure run_id exists in _test_runs
        if run_id not in _test_runs:
            print(f"DEBUG: run_id {run_id} not in _test_runs, adding it")
            _test_runs[run_id] = {
                "status": "running",
                "output": "",
                "raw_output": "",
            }
        else:
            print(f"DEBUG: run_id {run_id} already in _test_runs")

        # Build command
        if line_number:
            cmd = ["uv", "run", "behave", f"{feature_path}:{line_number}", "--no-capture", "-v"]
        else:
            cmd = ["uv", "run", "behave", str(feature_path), "--no-capture", "-v"]

        print(f"DEBUG: About to create subprocess with cmd: {cmd}")
        # Create subprocess
        process = await asyncio.create_subprocess_exec(
            *cmd,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
        )
        print(f"DEBUG: Subprocess created, PID: {process.pid}")

        # Stream output with timeout (using wait_for for compatibility)
        timeout_seconds = 60
        output_lines = []

        async def read_output():
            """Read output line by line."""
            while True:
                line = await process.stdout.readline()
                if not line:
                    break
                output_lines.append(line.decode("utf-8"))
                raw_output = "".join(output_lines)
                _test_runs[run_id]["raw_output"] = raw_output
                _test_runs[run_id]["output"] = filter_behave_output(raw_output)
            await process.wait()

        try:
            await asyncio.wait_for(read_output(), timeout=timeout_seconds)
        except asyncio.TimeoutError:
            # Kill process on timeout
            process.kill()
            await process.wait()
            _test_runs[run_id]["status"] = "timeout"
            _test_runs[run_id]["output"] += "\n\n[Timeout after 60 seconds]"
            return

        # Update final status
        _test_runs[run_id]["status"] = "completed" if process.returncode == 0 else "failed"
        _test_runs[run_id]["return_code"] = process.returncode

    except Exception as e:
        if run_id in _test_runs:
            _test_runs[run_id]["status"] = "error"
            _test_runs[run_id]["output"] += f"\n\nError: {str(e)}"
        else:
            # If run_id doesn't exist, create it with error
            _test_runs[run_id] = {
                "status": "error",
                "output": f"Error: {str(e)}",
            }


@router.get("/", response_class=RedirectResponse)
async def demo_index() -> RedirectResponse:
    """Redirect to default law."""
    return RedirectResponse(url="/demo/law/zorgtoeslagwet/TOESLAGEN-2025-01-01", status_code=302)


@router.get("/api/laws", response_class=JSONResponse)
async def get_laws() -> JSONResponse:
    """Get list of all available laws as JSON."""
    laws = discover_laws(LAW_DIR)
    return JSONResponse(content=laws)


@router.get("/law/{law_path:path}", response_class=HTMLResponse)
async def view_law(request: Request, law_path: str) -> HTMLResponse:
    """View a specific law YAML file with collapsible sections."""
    yaml_file = LAW_DIR / f"{law_path}.yaml"

    if not yaml_file.exists():
        raise HTTPException(status_code=404, detail=f"Law file not found: {law_path}")

    try:
        law_data = parse_law_yaml(yaml_file, law_dir=LAW_DIR, law_path=law_path)
        grouped_laws = discover_laws(LAW_DIR, grouped=True)

        # Render YAML to HTML
        yaml_html = render_yaml_to_html(law_data)

        return templates.TemplateResponse(
            "demo/law_viewer.html",
            {
                "request": request,
                "law_path": law_path,
                "law_data": law_data,
                "grouped_laws": grouped_laws,
                "yaml_html": yaml_html,
                "active_tab": "laws",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing law file: {str(e)}")


@router.get("/api/features", response_class=JSONResponse)
async def get_features_api() -> JSONResponse:
    """Get list of all available feature files as JSON (grouped)."""
    base_dirs = [FEATURES_DIR]
    if SUBMODULE_LAWS_DIR.exists():
        base_dirs.append(SUBMODULE_LAWS_DIR)

    grouped_features = discover_feature_files(base_dirs)
    return JSONResponse(content=grouped_features)


@router.get("/features", response_class=RedirectResponse)
async def list_features() -> RedirectResponse:
    """Redirect to default feature."""
    return RedirectResponse(
        url="/demo/feature/submodules/regelrecht-laws/laws/zorgtoeslagwet/TOESLAGEN-2025-01-01.feature",
        status_code=302,
    )


@router.post("/feature/run-scenario", response_class=JSONResponse)
async def run_scenario(request: Request) -> JSONResponse:
    """Run a specific scenario and return run_id for polling output."""
    body = await request.json()
    feature_path = body.get("feature_path")
    scenario_index = body.get("scenario_index")

    if not feature_path:
        raise HTTPException(status_code=400, detail="feature_path is required")
    if scenario_index is None:
        raise HTTPException(status_code=400, detail="scenario_index is required")

    # Parse feature to get scenario line number
    feature_file = Path(feature_path)
    if not feature_file.exists():
        raise HTTPException(status_code=404, detail=f"Feature file not found: {feature_path}")

    try:
        parsed = parse_feature_file(feature_file)
        if scenario_index >= len(parsed.get("scenarios", [])):
            raise HTTPException(status_code=400, detail="Invalid scenario_index")

        scenario = parsed["scenarios"][scenario_index]
        line_number = scenario["line_number"]

        # Initialize run tracking
        run_id = str(uuid.uuid4())
        _test_runs[run_id] = {
            "status": "running",
            "output": "",
            "raw_output": "",
            "scenario_name": scenario["name"],
        }

        print(f"DEBUG: Created run_id {run_id}, _test_runs now has {len(_test_runs)} entries")
        print(f"DEBUG: _test_runs keys: {list(_test_runs.keys())}")

        # Start async task and keep reference to prevent garbage collection
        task = asyncio.create_task(_run_behave_async(run_id, feature_path, line_number))
        _active_tasks.add(task)
        task.add_done_callback(_active_tasks.discard)

        print(f"DEBUG: Started async task for run_id {run_id}")

        return JSONResponse(content={"run_id": run_id, "status": "started"})

    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running scenario: {str(e)}")


@router.get("/feature/run-status/{run_id}", response_class=JSONResponse)
async def get_run_status(run_id: str) -> JSONResponse:
    """Get status and output of a running test."""
    print(f"DEBUG: get_run_status called for run_id {run_id}")
    print(f"DEBUG: _test_runs has {len(_test_runs)} entries: {list(_test_runs.keys())}")

    if run_id not in _test_runs:
        print(f"DEBUG: run_id {run_id} NOT FOUND in _test_runs!")
        raise HTTPException(status_code=404, detail="Run ID not found")

    print(f"DEBUG: Returning status for run_id {run_id}: {_test_runs[run_id]}")
    return JSONResponse(content=_test_runs[run_id])


@router.post("/run-feature", response_class=JSONResponse)
@router.get("/feature/{feature_path:path}", response_class=HTMLResponse)
async def view_feature(request: Request, feature_path: str) -> HTMLResponse:
    """View a specific feature file with parsed Gherkin and collapsible scenarios."""
    # Try to find feature file
    feature_file = None
    if Path(feature_path).exists():
        feature_file = Path(feature_path)
    elif (FEATURES_DIR / feature_path).exists():
        feature_file = FEATURES_DIR / feature_path
    elif SUBMODULE_LAWS_DIR.exists() and (SUBMODULE_LAWS_DIR / feature_path).exists():
        feature_file = SUBMODULE_LAWS_DIR / feature_path

    if not feature_file or not feature_file.exists():
        raise HTTPException(status_code=404, detail=f"Feature file not found: {feature_path}")

    try:
        # Parse feature
        parsed_feature = parse_feature_file(feature_file)

        # Render to HTML
        feature_html = render_feature_to_html(parsed_feature)

        # Get all features for sidebar
        base_dirs = [FEATURES_DIR]
        if SUBMODULE_LAWS_DIR.exists():
            base_dirs.append(SUBMODULE_LAWS_DIR)
        grouped_features = discover_feature_files(base_dirs)

        return templates.TemplateResponse(
            "demo/feature_viewer.html",
            {
                "request": request,
                "feature_path": str(feature_file),
                "feature_data": parsed_feature,
                "feature_html": feature_html,
                "grouped_features": grouped_features,
                "active_tab": "features",
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing feature file: {str(e)}")


async def run_feature(request: Request) -> JSONResponse:
    """Run entire feature file and return results."""
    body = await request.json()
    feature_path = body.get("feature_path")

    if not feature_path:
        raise HTTPException(status_code=400, detail="feature_path is required")

    feature_file = Path(feature_path)
    if not feature_file.exists():
        raise HTTPException(status_code=404, detail=f"Feature file not found: {feature_path}")

    try:
        run_id = str(uuid.uuid4())
        _test_runs[run_id] = {
            "status": "running",
            "output": "",
            "raw_output": "",
        }

        # Start async task and keep reference to prevent garbage collection
        task = asyncio.create_task(_run_behave_async(run_id, feature_path, None))
        _active_tasks.add(task)
        task.add_done_callback(_active_tasks.discard)

        return JSONResponse(content={"run_id": run_id, "status": "started"})
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running feature: {str(e)}")
