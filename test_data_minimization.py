#!/usr/bin/env python3
"""
Test script to demonstrate the data minimization optimization system.

This script shows how the new data minimization features work:
1. Early elimination using minimal sensitive data
2. Sensitivity-based law ordering (least sensitive first)
3. Metrics tracking for data minimization effectiveness
"""

import sys
import os
import logging
from datetime import date

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from machine.service import Services
from machine.sensitivity import DataSensitivityClassifier, SensitivityLevel
from machine.early_filter import EarlyEliminationFilter

# Configure logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")


def test_data_sensitivity_classifier():
    """Test the data sensitivity classification system"""
    print("\n=== Testing Data Sensitivity Classifier ===")

    classifier = DataSensitivityClassifier()

    # Test field classification
    test_fields = [
        ("BSN", "string", "Burgerservicenummer"),
        ("LEEFTIJD", "number", "Age of person"),
        ("HEEFT_PARTNER", "boolean", "Has partner flag"),
        ("INKOMEN", "amount", "Exact income"),
        ("INKOMEN_BRACKET", "string", "Income range"),
        ("GEBOORTEDATUM", "date", "Birth date"),
        ("WOONPLAATS", "string", "City of residence"),
    ]

    print("Field sensitivity classifications:")
    for field_name, field_type, description in test_fields:
        sensitivity = classifier.classify_field(field_name, field_type, description)
        print(f"  {field_name:20} -> Level {sensitivity.value} ({sensitivity.name})")


def test_early_elimination():
    """Test early elimination filtering"""
    print("\n=== Testing Early Elimination Filter ===")

    # Create mock law data
    mock_laws = [
        {"name": "AOW_Pension", "data_minimization": {"min_age": 67}},
        {"name": "Student_Finance", "data_minimization": {"max_age": 30}},
        {"name": "Child_Benefits", "data_minimization": {"requires_children": True}},
        {
            "name": "Income_Tax",
            "data_minimization": {},  # No early elimination rules
        },
    ]

    # Test with different minimal data scenarios
    test_scenarios = [
        {
            "name": "Young adult (25), no partner, no children",
            "data": {"age_bracket": "18-66", "age_approx": 25, "has_partner": False, "has_children": False},
        },
        {
            "name": "Senior (70), has partner, has children",
            "data": {"age_bracket": "67+", "age_approx": 70, "has_partner": True, "has_children": True},
        },
        {
            "name": "Middle-aged (40), has children",
            "data": {"age_bracket": "18-66", "age_approx": 40, "has_partner": False, "has_children": True},
        },
    ]

    classifier = DataSensitivityClassifier()

    for scenario in test_scenarios:
        print(f"\nScenario: {scenario['name']}")
        print(f"Available data: {scenario['data']}")

        applicable = []
        eliminated = []

        for law in mock_laws:
            if classifier.can_eliminate_early(law, scenario["data"]):
                eliminated.append(law["name"])
            else:
                applicable.append(law["name"])

        print(f"  Applicable laws: {applicable}")
        print(f"  Eliminated laws: {eliminated}")


def test_data_minimization_integration():
    """Test the full data minimization system integration"""
    print("\n=== Testing Full Data Minimization Integration ===")

    try:
        # Initialize services with data minimization
        services = Services(reference_date="2025-01-01")

        # Test BSN (using a test BSN)
        test_bsn = "123456789"

        print(f"Testing with BSN: {test_bsn}")

        # Test original impact-based sorting
        print("\n--- Original Impact-Based Sorting ---")
        try:
            original_laws = services.get_sorted_discoverable_service_laws(test_bsn)
            print(f"Found {len(original_laws)} laws using impact-based sorting")
            for i, law in enumerate(original_laws[:5]):  # Show first 5
                print(f"  {i + 1}. {law.get('service')}.{law.get('law')} (impact: {law.get('impact_value', 0)})")
        except Exception as e:
            print(f"Error in original sorting: {e}")

        # Test new data minimization sorting
        print("\n--- Data Minimization Sorting ---")
        try:
            dm_result = services.get_data_minimized_sorted_laws(test_bsn)

            applicable_laws = dm_result["applicable_laws"]
            eliminated_laws = dm_result["eliminated_laws"]
            metrics = dm_result["metrics"]

            print(f"Early elimination removed: {len(eliminated_laws)} laws")
            print(f"Remaining applicable laws: {len(applicable_laws)}")

            print("\nEliminated laws:")
            for law_name in eliminated_laws[:5]:  # Show first 5
                print(f"  - {law_name}")

            print("\nApplicable laws (sorted by sensitivity):")
            for i, law in enumerate(applicable_laws[:5]):  # Show first 5
                sensitivity_score = law.get("sensitivity_score", (0, 0, 0))
                print(
                    f"  {i + 1}. {law.get('name')} (sensitivity: max={sensitivity_score[0]}, avg={sensitivity_score[1]:.2f})"
                )

            print(f"\nData Minimization Metrics:")
            print(f"  Early elimination rate: {metrics['early_elimination_rate_percent']:.1f}%")
            print(f"  Max sensitivity accessed: {metrics['max_sensitivity_accessed']}")
            print(f"  Average sensitivity score: {metrics['average_sensitivity_score']:.2f}")
            print(f"  Services called: {metrics['services_called_count']}")
            print(f"  Total fields accessed: {metrics['total_fields_accessed']}")

        except Exception as e:
            print(f"Error in data minimization sorting: {e}")
            import traceback

            traceback.print_exc()

    except Exception as e:
        print(f"Error initializing services: {e}")
        import traceback

        traceback.print_exc()


def main():
    """Run all data minimization tests"""
    print("Data Minimization System Test Suite")
    print("=" * 50)

    test_data_sensitivity_classifier()
    test_early_elimination()
    test_data_minimization_integration()

    print("\n" + "=" * 50)
    print("Test suite completed!")


if __name__ == "__main__":
    main()
