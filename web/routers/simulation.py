import json
import logging
import uuid
from datetime import datetime

from fastapi import APIRouter, HTTPException, Request
from fastapi.responses import JSONResponse, StreamingResponse

from simulate import LawSimulator
from web.dependencies import templates
from web.law_parameters import get_default_law_parameters_subprocess

logger = logging.getLogger(__name__)

# Store simulation progress and results
simulation_progress = {}
simulation_results = {}

router = APIRouter(prefix="/simulation", tags=["simulation"])


@router.get("/debug/law-params")
async def debug_law_params():
    """Debug endpoint to see raw law parameters"""
    try:
        law_params = get_default_law_parameters_subprocess()
        return JSONResponse(
            {
                "status": "success",
                "law_count": len(law_params),
                "law_keys": list(law_params.keys()),
                "sample_data": {
                    k: {
                        "param_count": len(v),
                        "params_with_values": {pk: pv for pk, pv in list(v.items())[:5] if pv is not None},
                    }
                    for k, v in list(law_params.items())[:3]
                },
                "full_data": law_params,
            }
        )
    except Exception as e:
        # Log error server-side for debugging
        logger.error("Error in debug_law_params: %s", str(e), exc_info=True)
        return JSONResponse({"status": "error", "message": "An internal error occurred"}, status_code=500)


@router.get("/")
async def simulation_page(request: Request):
    """Render the simulation configuration page"""
    # Get default values via subprocess (avoids Services initialization conflicts)
    # This will have all auto-discovered parameters with their default values
    law_params = get_default_law_parameters_subprocess()

    # Debug: log what we're passing to template
    logger.info(f"Law params keys: {list(law_params.keys())}")
    if law_params:
        first_law = list(law_params.keys())[0]
        logger.info(f"First law: {first_law}, param count: {len(law_params[first_law])}")
        # Show a sample parameter with value
        for param_name, param_value in law_params[first_law].items():
            if param_value is not None:
                logger.info(f"  Sample: {param_name} = {param_value}")
                break

    # Default parameters for the simulation
    default_params = {
        "num_people": 10,
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


@router.post("/population/create")
async def create_population(request: Request):
    """Create a new population and save it"""
    try:
        import subprocess

        # Parse request body
        body = await request.json()
        body["operation"] = "create_population"  # Add operation type

        # Run population creation in subprocess
        result = subprocess.run(
            ["uv", "run", "python", "run_simulation.py"],
            input=json.dumps(body),
            capture_output=True,
            text=True,
            check=False,
        )

        if result.returncode != 0:
            raise Exception(f"Population creation failed: {result.stderr}")

        # Parse the result
        if not result.stdout.strip():
            raise Exception("No output from population creation")

        population_data = json.loads(result.stdout)

        return JSONResponse(population_data)

    except Exception as e:
        # Log error server-side for debugging
        logger.error("Population creation error: %s", str(e), exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": "An internal error occurred"})


@router.get("/population/list")
async def list_populations():
    """List all saved populations"""
    try:
        populations = LawSimulator.list_populations()
        return JSONResponse({"status": "success", "populations": populations})
    except Exception as e:
        # Log error server-side for debugging
        logger.error("List populations error: %s", str(e), exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": "An internal error occurred"})


@router.get("/population/{population_id}")
async def get_population(population_id: str):
    """Get details about a specific population"""
    try:
        # Load metadata
        from pathlib import Path

        metadata_file = Path("data/populations") / f"{population_id}.meta.json"
        if not metadata_file.exists():
            raise HTTPException(status_code=404, detail="Population not found")

        with open(metadata_file) as f:
            metadata = json.load(f)

        return JSONResponse({"status": "success", "population": metadata})
    except HTTPException:
        raise
    except Exception as e:
        # Log error server-side for debugging
        logger.error("Get population error: %s", str(e), exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": "An internal error occurred"})


@router.delete("/population/{population_id}")
async def delete_population(population_id: str):
    """Delete a saved population"""
    try:
        deleted = LawSimulator.delete_population(population_id)
        if not deleted:
            raise HTTPException(status_code=404, detail="Population not found")

        return JSONResponse({"status": "success", "message": f"Population {population_id} deleted"})
    except HTTPException:
        raise
    except Exception as e:
        # Log error server-side for debugging
        logger.error("Delete population error: %s", str(e), exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": "An internal error occurred"})


@router.post("/run")
async def run_simulation(request: Request):
    """Run the simulation with the provided parameters (optionally with existing population)"""
    try:
        import subprocess

        # Parse request body
        body = await request.json()
        body["operation"] = "run_simulation"  # Add operation type (default)

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

        simulation_data = json.loads(result.stdout)

        # Generate a unique session ID for this simulation
        session_id = str(uuid.uuid4())

        # Store the results for export
        simulation_results[session_id] = simulation_data

        # Add session_id to response
        simulation_data["session_id"] = session_id

        return JSONResponse(simulation_data)

    except Exception as e:
        # Log error server-side for debugging
        logger.error("Simulation error: %s", str(e), exc_info=True)
        return JSONResponse(status_code=500, content={"status": "error", "message": "An internal error occurred"})


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
    import io

    import pandas as pd

    # Check if we have results for this session
    if session_id not in simulation_results:
        raise HTTPException(status_code=404, detail="Simulation results not found")

    data = simulation_results[session_id]

    if format == "csv":
        # Convert results to CSV
        if "results" in data:
            df = pd.DataFrame(data["results"])

            # Create CSV content
            csv_buffer = io.StringIO()
            df.to_csv(csv_buffer, index=False)
            csv_content = csv_buffer.getvalue()

            return StreamingResponse(
                iter([csv_content]),
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename=simulation_{session_id}.csv"},
            )

    elif format == "json":
        # Return full JSON data
        json_content = json.dumps(data, indent=2, ensure_ascii=False)

        return StreamingResponse(
            iter([json_content]),
            media_type="application/json",
            headers={"Content-Disposition": f"attachment; filename=simulation_{session_id}.json"},
        )

    else:
        raise HTTPException(status_code=400, detail=f"Unsupported format: {format}")


def calculate_summary_statistics(df) -> dict:
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
