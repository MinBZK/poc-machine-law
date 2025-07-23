import asyncio
import json
from datetime import datetime
from typing import Dict, Optional
import uuid
import time

from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse
from starlette.responses import Response

from web.dependencies import templates
from web.law_parameters import get_default_law_parameters

# Store simulation progress
simulation_progress = {}

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/")
async def simulation_page(request: Request):
    """Render the simulation configuration page"""
    # Get law parameters from YAML files
    law_params = get_default_law_parameters()
    
    # Default parameters for the simulation
    default_params = {
        "num_people": 1000,
        "simulation_date": datetime.now().strftime("%Y-%m-%d"),
        # Age distribution
        "age_18_30": 18,
        "age_30_45": 25,
        "age_45_67": 32,
        "age_67_85": 20,
        "age_85_plus": 5,
        # Income distribution
        "income_low_pct": 30,
        "income_middle_pct": 50,
        "income_high_pct": 20,
        # Economic parameters
        "zero_income_prob": 5,
        "rent_percentage": 43,
        "student_percentage_young": 40,
        # Rent ranges
        "rent_low_min": 477,
        "rent_low_max": 600,
        "rent_medium_min": 600,
        "rent_medium_max": 750,
        "rent_high_min": 750,
        "rent_high_max": 800,
    }

    return templates.TemplateResponse(
        "simulation.html",
        {
            "request": request,
            "default_params": default_params,
            "law_params": law_params,
            "all_profiles": {},  # Empty dict for compatibility with base template
        },
    )


@router.post("/run")
async def run_simulation(request: Request):
    """Run the simulation with the provided parameters"""
    try:
        import subprocess

        # Parse request body
        body = await request.json()

        # Run simulation in subprocess to avoid class registration conflicts
        result = subprocess.run(
            ["uv", "run", "python", "run_simulation.py"],
            input=json.dumps(body),
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise Exception(f"Simulation failed: {result.stderr}")

        # Parse the result
        if not result.stdout.strip():
            raise Exception("No output from simulation")

        return JSONResponse(json.loads(result.stdout))

    except Exception as e:
        import traceback

        error_details = traceback.format_exc()
        print(f"Simulation error: {error_details}")
        return JSONResponse(status_code=500, content={"status": "error", "message": str(e), "details": error_details})


@router.get("/results/{session_id}")
async def get_results(request: Request, session_id: str):
    """Get detailed simulation results"""
    # TODO: Implement session-based result storage
    # For now, return a placeholder
    return templates.TemplateResponse(
        "simulation_results.html",
        {
            "request": request,
            "session_id": session_id,
        },
    )


@router.get("/export/{session_id}")
async def export_results(session_id: str, format: str = "csv"):
    """Export simulation results in various formats"""
    # TODO: Implement result export
    # For now, return a placeholder CSV

    # Example CSV content
    csv_content = "bsn,age,income,zorgtoeslag_eligible,zorgtoeslag_amount\n"
    csv_content += "100000001,35,25000,true,94.50\n"

    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=simulation_{session_id}.csv"},
    )


def calculate_summary_statistics(df) -> Dict:
    """Calculate summary statistics from simulation results"""
    summary = {
        "demographics": {
            "total_people": len(df),
            "avg_age": float(df["age"].mean()),
            "with_partners_pct": float(df["has_partner"].mean() * 100),
            "students_pct": float(df["is_student"].mean() * 100),
            "renters_pct": float((df["housing_type"] == "rent").mean() * 100),
            "with_children_pct": float(df["has_children"].mean() * 100),
        },
        "income": {
            "avg_annual": float(df["income"].mean()),
            "median_annual": float(df["income"].median()),
            "avg_tax": float(df["tax_due"].mean()),
            "avg_tax_rate": float((df["tax_due"] / df["income"]).mean() * 100),
        },
        "laws": {
            "zorgtoeslag": {
                "eligible_pct": float(df["zorgtoeslag_eligible"].mean() * 100),
                "avg_amount": float(df[df["zorgtoeslag_eligible"]]["zorgtoeslag_amount"].mean())
                if any(df["zorgtoeslag_eligible"])
                else 0,
            },
            "aow": {
                "eligible_pct": float(df["aow_eligible"].mean() * 100),
                "avg_amount": float(df[df["aow_eligible"]]["aow_amount"].mean()) if any(df["aow_eligible"]) else 0,
            },
            "bijstand": {
                "eligible_pct": float(df["bijstand_eligible"].mean() * 100),
                "avg_amount": float(df[df["bijstand_eligible"]]["bijstand_amount"].mean())
                if any(df["bijstand_eligible"])
                else 0,
            },
            "voting_rights": {
                "eligible_pct": float(df["voting_rights"].mean() * 100),
            },
        },
        "disposable_income": {
            "avg_monthly": float(df["disposable_income"].mean()),
            "median_monthly": float(df["disposable_income"].median()),
            "after_housing_avg": float(df["disposable_income_after_housing"].mean()),
        },
    }

    return summary
