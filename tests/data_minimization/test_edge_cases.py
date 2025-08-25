#!/usr/bin/env python3
"""
Test edge cases for the simplified data minimization system.
"""

import sys
import os

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

from machine.simple_sensitivity import (
    SimpleDataClassifier, 
    SimpleEarlyFilter, 
    DataMinimizedExecutor,
    SimpleMetrics,
    SensitivityLevel
)

def test_edge_cases():
    """Test edge cases and error handling"""
    print("🧪 Testing Edge Cases")
    
    # Test 1: Empty/None inputs
    print("\n--- Testing Empty Inputs ---")
    classifier = SimpleDataClassifier()
    
    try:
        result = classifier.classify_field("")
        print(f"✅ Empty field name: {result.name}")
    except:
        print("❌ Failed on empty field name")
    
    try:
        result = classifier.get_law_max_sensitivity({})
        print(f"✅ Empty law data: {result.name}")
    except:
        print("❌ Failed on empty law data")
    
    # Test 2: Complex field names
    print("\n--- Testing Complex Field Names ---")
    complex_fields = [
        "PARTNER_EXACT_YEARLY_INCOME_2023",  # Should be HIGH (INKOMEN keyword)
        "has_valid_residence_permit_flag",   # Should be LOW (has_ prefix)
        "household_size_category_bracket",   # Should be LOW (no HIGH keywords)
        "medical_diagnosis_code_primary",    # Should be LOW (not in HIGH list)
    ]
    
    for field in complex_fields:
        result = classifier.classify_field(field)
        print(f"  {field}: {result.name}")
    
    # Test 3: Law elimination with missing data
    print("\n--- Testing Missing Basic Info ---")
    filter = SimpleEarlyFilter()
    
    incomplete_info = {"age_bracket": "18-66"}  # Missing partner/children info
    laws = ["partner_supplement", "child_benefits", "general_law"]
    
    for law in laws:
        try:
            result = filter.can_skip_law(law, incomplete_info)
            print(f"  {law} with incomplete info: {'SKIP' if result else 'PROCESS'}")
        except Exception as e:
            print(f"  {law}: ERROR - {e}")
    
    # Test 4: Metrics with zero data
    print("\n--- Testing Metrics Edge Cases ---")
    metrics = SimpleMetrics()
    
    # Get summary with no data
    summary = metrics.get_summary()
    print(f"  Empty metrics summary: {summary}")
    
    # Add some data
    metrics.record_law_skipped("test_law")
    metrics.record_law_processed("another_law", SensitivityLevel.HIGH)
    
    summary = metrics.get_summary()
    print(f"  Metrics with data: skip_rate={summary['law_skip_rate_percent']}%")
    
    print("\n✅ Edge case testing completed")

def test_performance():
    """Test performance with larger datasets"""
    print("\n⚡ Testing Performance")
    
    import time
    
    # Test with many laws
    filter = SimpleEarlyFilter()
    basic_info = {"age_bracket": "18-66", "has_partner": True, "has_children": False}
    
    # Generate many test laws
    test_laws = []
    for i in range(1000):
        law_types = ["aow", "student", "partner", "child", "general"]
        law_type = law_types[i % len(law_types)]
        test_laws.append(f"{law_type}_law_{i}")
    
    start_time = time.time()
    skipped_count = 0
    
    for law in test_laws:
        if filter.can_skip_law(law, basic_info):
            skipped_count += 1
    
    end_time = time.time()
    processing_time = end_time - start_time
    
    print(f"  Processed {len(test_laws)} laws in {processing_time:.4f} seconds")
    print(f"  Skipped {skipped_count} laws ({skipped_count/len(test_laws)*100:.1f}%)")
    print(f"  Rate: {len(test_laws)/processing_time:.0f} laws/second")
    
    if processing_time < 1.0:  # Should be very fast
        print("  ✅ Performance is acceptable")
    else:
        print("  ⚠️ Performance may need optimization")

def test_real_world_scenarios():
    """Test realistic scenarios"""
    print("\n🌍 Testing Real-World Scenarios")
    
    # Scenario 1: Typical young working person
    print("\n--- Young Working Professional ---")
    filter = SimpleEarlyFilter()
    metrics = SimpleMetrics()
    
    young_professional = {
        "age_bracket": "18-66",
        "has_partner": True,
        "has_children": False
    }
    
    realistic_laws = [
        "algemene_ouderdomswet",     # Should skip - too young
        "wet_studiefinanciering",    # Should not skip - could be relevant
        "zorgtoeslag",              # Should not skip - healthcare allowance
        "huurtoeslag",              # Should not skip - rent allowance
        "kinderbijslag",            # Should skip - no children
        "partnertoeslag",           # Should not skip - has partner
        "kinderopvangtoeslag",      # Should skip - no children
        "algemene_bijstandswet"     # Should not skip - general assistance
    ]
    
    applicable_laws = []
    for law in realistic_laws:
        if filter.can_skip_law(law, young_professional):
            metrics.record_law_skipped(law)
        else:
            applicable_laws.append(law)
    
    elimination_rate = filter.get_elimination_rate()
    print(f"  Laws applicable: {len(applicable_laws)}/{len(realistic_laws)}")
    print(f"  Elimination rate: {elimination_rate:.1f}%")
    
    # Scenario 2: Elderly person
    print("\n--- Elderly Person ---")
    filter.reset_metrics()
    
    elderly_person = {
        "age_bracket": "67+",
        "has_partner": False,
        "has_children": True  # Adult children
    }
    
    applicable_laws = []
    for law in realistic_laws:
        if filter.can_skip_law(law, elderly_person):
            metrics.record_law_skipped(law)
        else:
            applicable_laws.append(law)
    
    elimination_rate = filter.get_elimination_rate()
    print(f"  Laws applicable: {len(applicable_laws)}/{len(realistic_laws)}")
    print(f"  Elimination rate: {elimination_rate:.1f}%")
    
    # Scenario 3: Young family
    print("\n--- Young Family ---")
    filter.reset_metrics()
    
    young_family = {
        "age_bracket": "18-66",
        "has_partner": True,
        "has_children": True
    }
    
    applicable_laws = []
    for law in realistic_laws:
        if filter.can_skip_law(law, young_family):
            metrics.record_law_skipped(law)
        else:
            applicable_laws.append(law)
    
    elimination_rate = filter.get_elimination_rate()
    print(f"  Laws applicable: {len(applicable_laws)}/{len(realistic_laws)}")
    print(f"  Elimination rate: {elimination_rate:.1f}%")

if __name__ == "__main__":
    test_edge_cases()
    test_performance()
    test_real_world_scenarios()
    print("\n🏁 All edge case testing completed!")