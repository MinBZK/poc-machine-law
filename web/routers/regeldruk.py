"""
Regeldruk Router - Demonstrates regulatory burden reduction through machine-readable laws.

This router provides a scenarios-style view showing horeca-related feature files,
demonstrating how machine-readable law specifications reduce administrative burden
by automatically sharing data between related permits.
"""

from pathlib import Path

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import HTMLResponse, RedirectResponse

from web.demo.feature_parser import parse_feature_file
from web.demo.feature_renderer import render_feature_to_html
from web.dependencies import templates
from web.services.regeldruk import calculate_combined_metrics

router = APIRouter(prefix="/regeldruk", tags=["regeldruk"])

# Paths to horeca feature files
HORECA_FEATURES = {
    "exploitatievergunning": {
        "path": "submodules/regelrecht-laws/laws/algemene_plaatselijke_verordening/exploitatievergunning/gemeenten/GEMEENTE_ROTTERDAM-2024-01-01.feature",
        "name": "Exploitatievergunning",
        "description": "Horeca exploitatievergunning",
    },
    "terrassen": {
        "path": "submodules/regelrecht-laws/laws/algemene_plaatselijke_verordening/terrassen/GEMEENTE_ROTTERDAM-2024-01-01.feature",
        "name": "Terrasvergunning",
        "description": "Terrasvergunning bij horecabedrijf",
    },
}


def get_horeca_features() -> dict:
    """Get horeca feature files with metadata."""
    features = {}
    for key, info in HORECA_FEATURES.items():
        feature_path = Path(info["path"])
        if feature_path.exists():
            try:
                parsed = parse_feature_file(feature_path)
                features[key] = {
                    "path": str(feature_path),
                    "name": info["name"],
                    "description": info["description"],
                    "scenario_count": len(parsed.get("scenarios", [])),
                    "feature_name": parsed.get("name", info["name"]),
                }
            except Exception:
                features[key] = {
                    "path": str(feature_path),
                    "name": info["name"],
                    "description": info["description"],
                    "scenario_count": 0,
                    "feature_name": info["name"],
                }
    return features


@router.get("/", response_class=HTMLResponse)
async def regeldruk_index(request: Request):
    """
    Regeldruk page - redirects to default feature (exploitatievergunning).
    """
    # Preserve demo query parameter in redirect
    demo_mode = request.query_params.get("demo", "")
    redirect_url = "/regeldruk/feature/exploitatievergunning"
    if demo_mode:
        redirect_url += f"?demo={demo_mode}"
    return RedirectResponse(url=redirect_url, status_code=307)


@router.get("/feature/{feature_key}", response_class=HTMLResponse)
async def regeldruk_feature(request: Request, feature_key: str):
    """
    Show a specific horeca feature file in the regeldruk viewer.
    """
    if feature_key not in HORECA_FEATURES:
        raise HTTPException(status_code=404, detail=f"Feature not found: {feature_key}")

    feature_info = HORECA_FEATURES[feature_key]
    feature_path = Path(feature_info["path"])

    if not feature_path.exists():
        raise HTTPException(status_code=404, detail=f"Feature file not found: {feature_path}")

    try:
        # Parse the feature file
        parsed_feature = parse_feature_file(feature_path)
        feature_html = render_feature_to_html(parsed_feature)

        # Get all horeca features for sidebar
        horeca_features = get_horeca_features()

        # Calculate regeldruk metrics for the summary
        metrics = calculate_combined_metrics(
            [
                ("GEMEENTE_ROTTERDAM", "algemene_plaatselijke_verordening/exploitatievergunning"),
                ("GEMEENTE_ROTTERDAM", "algemene_plaatselijke_verordening/terrassen"),
            ]
        )

        # Demo mode flag
        demo_mode = request.query_params.get("demo", "").lower() in ("true", "1", "yes")

        return templates.TemplateResponse(
            "regeldruk/index.html",
            {
                "request": request,
                "feature_path": str(feature_path),
                "feature_key": feature_key,
                "feature_data": parsed_feature,
                "feature_html": feature_html,
                "horeca_features": horeca_features,
                "metrics": metrics,
                "demo_mode": demo_mode,
            },
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error parsing feature file: {str(e)}")
