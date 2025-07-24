#!/usr/bin/env python3
"""Test if zorgtoeslag parameter override is working."""
import json
import subprocess

print("Testing zorgtoeslag parameter override...")
print("="*60)

# Test 1: Default parameters (€176/month)
print("\nTest 1: Default zorgtoeslag premium (€176/month)")
params1 = {
    "num_people": 20,
    "simulation_date": "2025-01-01",
}

result1 = subprocess.run(
    ["uv", "run", "python", "run_simulation.py"],
    input=json.dumps(params1),
    capture_output=True,
    text=True,
    check=False,
)

if result1.returncode == 0:
    data1 = json.loads(result1.stdout)
    avg1 = data1['summary']['laws']['zorgtoeslag']['avg_amount']
    print(f"Average zorgtoeslag: €{avg1:.2f}/month")
else:
    print(f"Error: {result1.stderr}")

# Test 2: Higher premium (€250/month)
print("\nTest 2: Higher zorgtoeslag premium (€250/month)")
params2 = {
    "num_people": 20,
    "simulation_date": "2025-01-01",
    "law_parameters": {
        "zorgtoeslag": {
            "standaardpremie": 250  # €250/month
        }
    }
}

result2 = subprocess.run(
    ["uv", "run", "python", "run_simulation.py"],
    input=json.dumps(params2),
    capture_output=True,
    text=True,
    check=False,
)

if result2.returncode == 0:
    data2 = json.loads(result2.stdout)
    avg2 = data2['summary']['laws']['zorgtoeslag']['avg_amount']
    print(f"Average zorgtoeslag: €{avg2:.2f}/month")
else:
    print(f"Error: {result2.stderr}")

# Test 3: Lower premium (€100/month)
print("\nTest 3: Lower zorgtoeslag premium (€100/month)")
params3 = {
    "num_people": 20,
    "simulation_date": "2025-01-01",
    "law_parameters": {
        "zorgtoeslag": {
            "standaardpremie": 100  # €100/month
        }
    }
}

result3 = subprocess.run(
    ["uv", "run", "python", "run_simulation.py"],
    input=json.dumps(params3),
    capture_output=True,
    text=True,
    check=False,
)

if result3.returncode == 0:
    data3 = json.loads(result3.stdout)
    avg3 = data3['summary']['laws']['zorgtoeslag']['avg_amount']
    print(f"Average zorgtoeslag: €{avg3:.2f}/month")
else:
    print(f"Error: {result3.stderr}")

# Compare results
print("\n" + "="*60)
print("Summary:")
if 'avg1' in locals() and 'avg2' in locals() and 'avg3' in locals():
    print(f"Default (€176/month premium): €{avg1:.2f}/month zorgtoeslag")
    print(f"Higher (€250/month premium):  €{avg2:.2f}/month zorgtoeslag")
    print(f"Lower (€100/month premium):   €{avg3:.2f}/month zorgtoeslag")
    
    # With higher premium, people should get MORE zorgtoeslag
    if avg2 > avg1 > avg3:
        print("\n✅ Parameter override is working correctly!")
        print("   (Higher premium = higher subsidy, lower premium = lower subsidy)")
    else:
        print("\n❌ Parameter override might not be working correctly")
        print("   Expected: avg2 > avg1 > avg3")
        print(f"   Actual: avg2={avg2:.2f}, avg1={avg1:.2f}, avg3={avg3:.2f}")