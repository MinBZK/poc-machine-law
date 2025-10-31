"""Demo mode router for presenting law files and running features."""

import json
from pathlib import Path
from typing import Any

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, JSONResponse

from web.demo.feature_runner import run_feature_file
from web.demo.yaml_renderer import discover_laws, parse_law_yaml, render_yaml_to_html
from web.dependencies import templates

router = APIRouter(prefix="/demo", tags=["demo"])

LAW_DIR = Path("law")
FEATURES_DIR = Path("features")


@router.get("/", response_class=HTMLResponse)
async def demo_index(request: Request) -> HTMLResponse:
    """Main demo page with law selector."""
    grouped_laws = discover_laws(LAW_DIR, grouped=True)
    return templates.TemplateResponse(
        "demo/index.html",
        {
            "request": request,
            "grouped_laws": grouped_laws,
            "active_tab": "laws",
        },
    )


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


@router.get("/features", response_class=HTMLResponse)
async def list_features(request: Request) -> HTMLResponse:
    """List all available feature files."""
    # Discover law-specific features
    law_features = []
    for feature_file in LAW_DIR.rglob("*.feature"):
        relative_path = feature_file.relative_to(LAW_DIR)
        law_features.append({
            "path": str(relative_path),
            "name": feature_file.stem,
            "type": "law-specific",
            "full_path": str(feature_file),
        })

    # Discover standalone features
    standalone_features = []
    for feature_file in FEATURES_DIR.glob("*.feature"):
        standalone_features.append({
            "path": str(feature_file.relative_to(FEATURES_DIR)),
            "name": feature_file.stem,
            "type": "standalone",
            "full_path": str(feature_file),
        })

    laws = discover_laws(LAW_DIR)

    return templates.TemplateResponse(
        "demo/feature_viewer.html",
        {
            "request": request,
            "law_features": law_features,
            "standalone_features": standalone_features,
            "laws": laws,
            "active_tab": "features",
        },
    )


@router.post("/run-feature", response_class=JSONResponse)
async def run_feature(request: Request) -> JSONResponse:
    """Run a feature file and return the results."""
    body = await request.json()
    feature_path = body.get("feature_path")

    if not feature_path:
        raise HTTPException(status_code=400, detail="feature_path is required")

    # Try to find the feature file
    feature_file = Path(feature_path)
    if not feature_file.exists():
        # Try in law directory
        feature_file = LAW_DIR / feature_path
        if not feature_file.exists():
            # Try in features directory
            feature_file = FEATURES_DIR / feature_path
            if not feature_file.exists():
                raise HTTPException(status_code=404, detail=f"Feature file not found: {feature_path}")

    try:
        result = run_feature_file(feature_file)
        return JSONResponse(content=result)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error running feature: {str(e)}")
