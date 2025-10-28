#!/usr/bin/env python3
"""Standalone simulation runner to avoid class registration conflicts."""

import json
import sys
from datetime import datetime

# Import simulate before suppressing stderr
from simulate import LawSimulator


def create_population(params: dict):
    """Create a population and return its ID and metadata."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    population_params = params.get("population_params", {})

    # Create simulator
    simulator = LawSimulator(simulation_date)

    # Apply custom parameters if provided
    apply_custom_parameters(simulator, params)

    # Create and save population
    population_id, people = simulator.create_population(num_people, save=True, population_params=population_params)

    # Return population metadata
    return {
        "status": "success",
        "population_id": population_id,
        "num_people": len(people),
        "demographics": {
            "avg_age": sum(p["age"] for p in people) / len(people),
            "with_partners_pct": sum(1 for p in people if p["has_partner"]) / len(people) * 100,
            "students_pct": sum(1 for p in people if p["is_student"]) / len(people) * 100,
            "renters_pct": sum(1 for p in people if p["housing_type"] == "rent") / len(people) * 100,
            "with_children_pct": sum(1 for p in people if p["has_children"]) / len(people) * 100,
        },
    }


def apply_custom_parameters(simulator: LawSimulator, params: dict):
    """Apply custom demographic parameters to simulator."""
    # Apply custom parameters if provided
    if "age_distribution" in params:
        age_dist = params["age_distribution"]
        simulator.age_distribution = {
            (18, 30): age_dist.get("age_18_30", 18) / 100,
            (30, 45): age_dist.get("age_30_45", 25) / 100,
            (45, 67): age_dist.get("age_45_67", 32) / 100,
            (67, 85): age_dist.get("age_67_85", 20) / 100,
            (85, 100): age_dist.get("age_85_plus", 5) / 100,
        }

    if "income_distribution" in params:
        income_dist = params["income_distribution"]
        total = sum([income_dist.get(k, 0) for k in ["income_low_pct", "income_middle_pct", "income_high_pct"]])
        if total > 0:
            simulator.income_distribution = {
                "low": income_dist.get("income_low_pct", 30) / 100,
                "middle": income_dist.get("income_middle_pct", 50) / 100,
                "high": income_dist.get("income_high_pct", 20) / 100,
            }

    if "economic_params" in params:
        econ = params["economic_params"]
        simulator.zero_income_prob = econ.get("zero_income_prob", 5) / 100
        simulator.housing_distribution = {
            "rent": econ.get("rent_percentage", 43) / 100,
            "own": 1 - (econ.get("rent_percentage", 43) / 100),
        }

    if "rent_ranges" in params:
        rent = params["rent_ranges"]
        simulator.rent_distribution = {
            "low": (rent.get("rent_low_min", 550), rent.get("rent_low_max", 700)),
            "medium": (rent.get("rent_medium_min", 700), rent.get("rent_medium_max", 850)),
            "high": (rent.get("rent_high_min", 850), rent.get("rent_high_max", 1200)),
        }


def run_simulation(params: dict):
    """Run simulation with given parameters and return results as JSON."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    law_parameters = params.get("law_parameters", {})
    population_id = params.get("population_id")  # Optional: use existing population

    # Create simulator with law parameters
    simulator = LawSimulator(simulation_date, law_parameters)

    # Apply custom parameters if not using existing population
    if not population_id:
        apply_custom_parameters(simulator, params)

    # Run simulation with optional population_id
    results_df = simulator.run_simulation(num_people=num_people, population_id=population_id)

    # Get summary with breakdowns using the method from simulate.py
    return simulator.get_summary_with_breakdowns(results_df, simulation_date)


if __name__ == "__main__":
    # Read parameters from stdin
    params = json.loads(sys.stdin.read())

    # Determine operation: create_population or run_simulation
    operation = params.get("operation", "run_simulation")

    # Don't suppress stderr temporarily to see debug logs
    try:
        result = create_population(params) if operation == "create_population" else run_simulation(params)
        print(json.dumps(result))
    except Exception as e:
        import traceback

        error_result = {"status": "error", "message": str(e), "traceback": traceback.format_exc()}
        print(json.dumps(error_result), file=sys.stderr)
        sys.exit(1)
