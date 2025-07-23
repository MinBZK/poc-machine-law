#!/usr/bin/env python3
"""Standalone simulation runner to avoid class registration conflicts."""

import json
import os
import sys
from datetime import datetime

# Suppress stderr output to avoid progress bar being treated as error
sys.stderr = open(os.devnull, "w")

from simulate import LawSimulator


def run_simulation(params: dict):
    """Run simulation with given parameters and return results as JSON."""
    num_people = params.get("num_people", 1000)
    simulation_date = params.get("simulation_date", datetime.now().strftime("%Y-%m-%d"))
    law_parameters = params.get("law_parameters", {})

    # Create simulator with law parameters
    simulator = LawSimulator(simulation_date, law_parameters)

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

    # Run simulation
    results_df = simulator.run_simulation(num_people)

    # Get summary with breakdowns using the method from simulate.py
    return simulator.get_summary_with_breakdowns(results_df, simulation_date)


if __name__ == "__main__":
    # Read parameters from stdin
    params = json.loads(sys.stdin.read())

    try:
        result = run_simulation(params)
        print(json.dumps(result))
    except Exception as e:
        error_result = {"status": "error", "message": str(e)}
        print(json.dumps(error_result))
        sys.exit(1)
