#!/usr/bin/env python3
"""Test script to verify simulation parameter overrides work correctly."""

import json
import subprocess
import sys


def run_simulation(num_people=5, law_overrides=None):
    """Run simulation via subprocess and return results."""
    payload = {
        "operation": "run_simulation",
        "num_people": num_people,
        "simulation_date": "2025-01-01",
        # Age distribution
        "age_18_30": 20,
        "age_30_45": 30,
        "age_45_67": 30,
        "age_67_85": 15,
        "age_85_plus": 5,
        # Income distribution
        "income_low_pct": 30,
        "income_middle_pct": 50,
        "income_high_pct": 20,
        # Economic parameters
        "zero_income_prob": 5,
        "rent_percentage": 50,
        "student_percentage_young": 30,
        # Rent ranges
        "rent_low_min": 477,
        "rent_low_max": 600,
        "rent_medium_min": 600,
        "rent_medium_max": 750,
        "rent_high_min": 750,
        "rent_high_max": 800,
    }

    if law_overrides:
        payload["law_parameters"] = law_overrides

    result = subprocess.run(
        ["uv", "run", "python", "run_simulation.py"],
        input=json.dumps(payload),
        capture_output=True,
        text=True,
        check=False,
    )

    if result.returncode != 0:
        print(f"Simulation failed: {result.stderr}", file=sys.stderr)
        sys.exit(1)

    return json.loads(result.stdout)


def main():
    print("Testing simulation parameter overrides...\n")

    # Test 1: Run with default parameters
    print("1. Running simulation with default tax parameters...")
    default_results = run_simulation(num_people=10)

    if default_results.get("status") == "error":
        print(f"ERROR: {default_results.get('message')}")
        sys.exit(1)

    default_avg_tax = default_results["summary"]["laws"]["inkomstenbelasting"]["avg_tax"]
    print(f"   Default avg tax: €{default_avg_tax:.2f}")

    # Test 2: Run with very low tax rate (should reduce tax significantly)
    print("\n2. Running simulation with 10% tax rate override (was ~37%)...")
    override_results = run_simulation(
        num_people=10,
        law_overrides={
            "inkomstenbelasting": {
                "box1_tarief1": 10.0,  # Override to 10%
                "box1_tarief2": 10.0,  # Override to 10%
            }
        },
    )

    if override_results.get("status") == "error":
        print(f"ERROR: {override_results.get('message')}")
        sys.exit(1)

    override_avg_tax = override_results["summary"]["laws"]["inkomstenbelasting"]["avg_tax"]
    print(f"   Override avg tax: €{override_avg_tax:.2f}")

    # Verify tax decreased
    print("\n3. Verifying parameter override affected results...")
    tax_decrease = default_avg_tax - override_avg_tax
    tax_decrease_pct = (tax_decrease / default_avg_tax * 100) if default_avg_tax > 0 else 0

    print(f"   Tax decreased by: €{tax_decrease:.2f} ({tax_decrease_pct:.1f}%)")

    if override_avg_tax < default_avg_tax * 0.8:  # Should be at least 20% less
        print("\n✅ SUCCESS: Parameter overrides are working correctly!")
        print(f"   Lowering tax rate from ~37% to 10% reduced average tax by {tax_decrease_pct:.1f}%")
        print(f"   Override tax is {(override_avg_tax/default_avg_tax*100):.1f}% of default tax")
        return 0
    else:
        print(
            f"\n❌ FAILURE: Parameter override did not have expected effect"
            f"\n   Expected override tax to be <80% of default, but got {(override_avg_tax/default_avg_tax*100):.1f}%"
        )
        return 1


if __name__ == "__main__":
    sys.exit(main())
