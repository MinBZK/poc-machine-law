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
from web.demo_profiles import DemoProfiles
from web.dependencies import templates
from web.services.regeldruk import calculate_combined_metrics

router = APIRouter(prefix="/regeldruk", tags=["regeldruk"])


def get_horeca_features() -> dict:
    """Get scenario feature files with metadata from active profile."""
    scenario_features = DemoProfiles.get_active_profile()["scenario_features"]
    features = {}
    for key, info in scenario_features.items():
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
    Regeldruk page - redirects to default feature from active profile.
    """
    scenario_features = DemoProfiles.get_active_profile()["scenario_features"]

    if not scenario_features:
        # No scenarios for this profile, show empty state
        demo_mode = request.query_params.get("demo", "").lower() in ("true", "1", "yes")
        return templates.TemplateResponse(
            "regeldruk/index.html",
            {
                "request": request,
                "feature_path": "",
                "feature_key": "",
                "feature_data": {},
                "feature_html": "",
                "horeca_features": {},
                "metrics": {},
                "demo_mode": demo_mode,
            },
        )

    # Preserve demo query parameter in redirect
    demo_mode = request.query_params.get("demo", "")
    first_key = next(iter(scenario_features))
    redirect_url = f"/regeldruk/feature/{first_key}"
    if demo_mode:
        redirect_url += f"?demo={demo_mode}"
    return RedirectResponse(url=redirect_url, status_code=307)


@router.get("/feature/{feature_key}", response_class=HTMLResponse)
async def regeldruk_feature(request: Request, feature_key: str):
    """
    Show a specific feature file in the regeldruk/scenarios viewer.
    """
    active_profile = DemoProfiles.get_active_profile()
    scenario_features = active_profile["scenario_features"]

    if feature_key not in scenario_features:
        raise HTTPException(status_code=404, detail=f"Feature not found: {feature_key}")

    feature_info = scenario_features[feature_key]
    feature_path = Path(feature_info["path"])

    if not feature_path.exists():
        raise HTTPException(status_code=404, detail=f"Feature file not found: {feature_path}")

    try:
        # Parse the feature file
        parsed_feature = parse_feature_file(feature_path)
        feature_html = render_feature_to_html(parsed_feature)

        # Get all scenario features for sidebar
        horeca_features = get_horeca_features()

        # Calculate regeldruk metrics from active profile
        metrics_laws = active_profile["scenario_metrics_laws"]
        metrics = calculate_combined_metrics(metrics_laws) if metrics_laws else {}

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
