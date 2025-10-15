#!/usr/bin/env python3
"""Test reproducibility of simulation results with same population."""

import json
import subprocess
import sys

def run_subprocess(operation, params):
    """Run operation in subprocess to avoid event sourcing conflicts."""
    cmd = ["uv", "run", "python", "run_simulation.py"]
    input_data = json.dumps({"operation": operation, **params})
    result = subprocess.run(cmd, input=input_data, capture_output=True, text=True)
    if result.returncode != 0:
        print(f"Error running {operation}:", file=sys.stderr)
        print("STDERR:", result.stderr, file=sys.stderr)
        print("STDOUT:", result.stdout, file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout)

def main():
    # Step 1: Create a population
    print("Step 1: Creating population...")
    result = run_subprocess("create_population", {
        "num_people": 10,
        "simulation_date": "2025-03-01",
    })
    population_id = result["population_id"]
    print(f"Created population: {population_id}")
    print(f"Population size: {result['num_people']}")

    # Step 2: Run simulation with this population
    print("\nStep 2: Running first simulation...")
    result1 = run_subprocess("run_simulation", {
        "num_people": 10,
        "simulation_date": "2025-03-01",
        "population_id": population_id,
    })

    # Extract key metrics from results
    zorgtoeslag_eligible_pct_1 = result1["summary"]["laws"]["zorgtoeslag"]["eligible_pct"]
    zorgtoeslag_avg_amount_1 = result1["summary"]["laws"]["zorgtoeslag"]["avg_amount"]
    huurtoeslag_eligible_pct_1 = result1["summary"]["laws"]["huurtoeslag"]["eligible_pct"]
    huurtoeslag_avg_amount_1 = result1["summary"]["laws"]["huurtoeslag"]["avg_amount"]

    print(f"Zorgtoeslag: {zorgtoeslag_eligible_pct_1:.1f}% eligible, avg amount: €{zorgtoeslag_avg_amount_1:.2f}")
    print(f"Huurtoeslag: {huurtoeslag_eligible_pct_1:.1f}% eligible, avg amount: €{huurtoeslag_avg_amount_1:.2f}")

    # Step 3: Run simulation again with same population
    print("\nStep 3: Running second simulation...")
    result2 = run_subprocess("run_simulation", {
        "num_people": 10,
        "simulation_date": "2025-03-01",
        "population_id": population_id,
    })

    # Extract same metrics
    zorgtoeslag_eligible_pct_2 = result2["summary"]["laws"]["zorgtoeslag"]["eligible_pct"]
    zorgtoeslag_avg_amount_2 = result2["summary"]["laws"]["zorgtoeslag"]["avg_amount"]
    huurtoeslag_eligible_pct_2 = result2["summary"]["laws"]["huurtoeslag"]["eligible_pct"]
    huurtoeslag_avg_amount_2 = result2["summary"]["laws"]["huurtoeslag"]["avg_amount"]

    print(f"Zorgtoeslag: {zorgtoeslag_eligible_pct_2:.1f}% eligible, avg amount: €{zorgtoeslag_avg_amount_2:.2f}")
    print(f"Huurtoeslag: {huurtoeslag_eligible_pct_2:.1f}% eligible, avg amount: €{huurtoeslag_avg_amount_2:.2f}")

    # Step 4: Compare results
    print("\n" + "="*80)
    print("COMPARISON RESULTS:")
    print("="*80)

    all_match = True

    if abs(zorgtoeslag_eligible_pct_1 - zorgtoeslag_eligible_pct_2) < 0.01:
        print(f"✅ Zorgtoeslag eligible % matches: {zorgtoeslag_eligible_pct_1:.1f}%")
    else:
        print(f"❌ Zorgtoeslag eligible % DIFFERS: {zorgtoeslag_eligible_pct_1:.1f}% vs {zorgtoeslag_eligible_pct_2:.1f}%")
        all_match = False

    if abs(zorgtoeslag_avg_amount_1 - zorgtoeslag_avg_amount_2) < 0.01:
        print(f"✅ Zorgtoeslag avg amount matches: €{zorgtoeslag_avg_amount_1:.2f}")
    else:
        print(f"❌ Zorgtoeslag avg amount DIFFERS: €{zorgtoeslag_avg_amount_1:.2f} vs €{zorgtoeslag_avg_amount_2:.2f}")
        all_match = False

    if abs(huurtoeslag_eligible_pct_1 - huurtoeslag_eligible_pct_2) < 0.01:
        print(f"✅ Huurtoeslag eligible % matches: {huurtoeslag_eligible_pct_1:.1f}%")
    else:
        print(f"❌ Huurtoeslag eligible % DIFFERS: {huurtoeslag_eligible_pct_1:.1f}% vs {huurtoeslag_eligible_pct_2:.1f}%")
        all_match = False

    if abs(huurtoeslag_avg_amount_1 - huurtoeslag_avg_amount_2) < 0.01:
        print(f"✅ Huurtoeslag avg amount matches: €{huurtoeslag_avg_amount_1:.2f}")
    else:
        print(f"❌ Huurtoeslag avg amount DIFFERS: €{huurtoeslag_avg_amount_1:.2f} vs €{huurtoeslag_avg_amount_2:.2f}")
        all_match = False

    print("="*80)
    if all_match:
        print("🎉 SUCCESS: Simulations are reproducible!")
        return 0
    else:
        print("⚠️  FAILURE: Simulations produced different results!")
        return 1

if __name__ == "__main__":
    exit(main())
