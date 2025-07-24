#!/usr/bin/env python3
"""Test different simulation scenarios."""
import json
import subprocess

scenarios = [
    {
        "name": "Scenario 1: Default parameters - 100 people",
        "params": {
            "num_people": 100,
            "simulation_date": "2025-01-01",
        }
    },
    {
        "name": "Scenario 2: Higher zorgtoeslag premium - 50 people",
        "params": {
            "num_people": 50,
            "simulation_date": "2025-01-01",
            "law_parameters": {
                "zorgtoeslag": {
                    "standaardpremie": 250  # €250/month instead of €176
                }
            }
        }
    },
    {
        "name": "Scenario 3: Economic recession - 200 people",
        "params": {
            "num_people": 200,
            "simulation_date": "2025-01-01",
            "income_distribution": {
                "income_low_pct": 60,  # More low income
                "income_middle_pct": 35,
                "income_high_pct": 5
            },
            "economic_params": {
                "zero_income_prob": 15,  # Higher unemployment
                "rent_percentage": 60,    # More renters
                "student_percentage_young": 20
            }
        }
    },
    {
        "name": "Scenario 4: Aging population - 150 people",
        "params": {
            "num_people": 150,
            "simulation_date": "2025-01-01",
            "age_distribution": {
                "age_18_30": 10,
                "age_30_45": 15,
                "age_45_67": 30,
                "age_67_85": 35,  # More elderly
                "age_85_plus": 10
            }
        }
    },
    {
        "name": "Scenario 5: Young population with children - 100 people",
        "params": {
            "num_people": 100,
            "simulation_date": "2025-01-01",
            "age_distribution": {
                "age_18_30": 35,  # More young people
                "age_30_45": 40,
                "age_45_67": 20,
                "age_67_85": 4,
                "age_85_plus": 1
            }
        }
    }
]

def run_scenario(scenario):
    """Run a single scenario and return results."""
    print(f"\n{'='*60}")
    print(f"Running: {scenario['name']}")
    print(f"{'='*60}")
    
    result = subprocess.run(
        ["uv", "run", "python", "run_simulation.py"],
        input=json.dumps(scenario['params']),
        capture_output=True,
        text=True,
        check=False,
    )
    
    if result.returncode != 0:
        print(f"Error: {result.stderr}")
        return None
    
    try:
        data = json.loads(result.stdout)
        if "summary" in data:
            summary = data['summary']
            print(f"✓ Simulation completed successfully")
            print(f"  Total people: {summary['demographics']['total_people']}")
            print(f"  Average age: {summary['demographics']['avg_age']:.1f}")
            print(f"  Average income: €{summary['income']['avg_annual']:,.0f}/year")
            print("\nLaw results:")
            print(f"  - Zorgtoeslag: {summary['laws']['zorgtoeslag']['eligible_pct']:.1f}% eligible, "
                  f"€{summary['laws']['zorgtoeslag']['avg_amount']:.0f}/month average")
            print(f"  - Huurtoeslag: {summary['laws']['huurtoeslag']['eligible_pct']:.1f}% eligible, "
                  f"€{summary['laws']['huurtoeslag']['avg_amount']:.0f}/month average")
            print(f"  - AOW: {summary['laws']['aow']['eligible_pct']:.1f}% eligible, "
                  f"€{summary['laws']['aow']['avg_amount']:.0f}/month average")
            print(f"  - Bijstand: {summary['laws']['bijstand']['eligible_pct']:.1f}% eligible, "
                  f"€{summary['laws']['bijstand']['avg_amount']:.0f}/month average")
            print(f"  - Kinderopvangtoeslag: {summary['laws']['kinderopvangtoeslag']['eligible_pct']:.1f}% eligible, "
                  f"€{summary['laws']['kinderopvangtoeslag']['avg_amount']:.0f}/month average")
            print(f"  - Kiesrecht: {summary['laws']['voting_rights']['eligible_pct']:.1f}% eligible")
            print(f"\nDisposable income: €{summary['disposable_income']['avg_monthly']:.0f}/month average")
            
            # Check for anomalies
            if summary['laws']['zorgtoeslag']['avg_amount'] > 500:
                print("\n⚠️  WARNING: Zorgtoeslag amount seems too high!")
            
            return data
        else:
            print(f"Error in response: {data}")
            return None
    except Exception as e:
        print(f"Error parsing response: {e}")
        return None

# Run all scenarios
print("Testing Machine Law Simulation Scenarios")
print("=" * 60)

results = []
for scenario in scenarios:
    result = run_scenario(scenario)
    results.append((scenario['name'], result))
    
print(f"\n{'='*60}")
print("Summary of all scenarios:")
print(f"{'='*60}")
successful = sum(1 for _, r in results if r is not None)
print(f"Successful simulations: {successful}/{len(scenarios)}")