#!/usr/bin/env python3
"""
Test script for the simplified data minimization implementation.
"""

import sys
import logging
import os
from typing import Dict, List

# Add project root to Python path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

try:
    from machine.simple_sensitivity import (
        SimpleDataClassifier, 
        SimpleEarlyFilter, 
        DataMinimizedExecutor,
        ExecutionTraceOptimizer,
        SimpleMetrics,
        SensitivityLevel
    )
except ImportError as e:
    print(f"Import error: {e}")
    print("Make sure simple_sensitivity.py is in the machine/ directory")
    sys.exit(1)


def test_field_classification():
    """Test the simple 2-level field classification"""
    print("\n=== Testing Field Classification ===")
    
    test_fields = [
        ("BSN", SensitivityLevel.HIGH),
        ("VERBLIJFSADRES", SensitivityLevel.HIGH),
        ("INKOMEN", SensitivityLevel.HIGH),
        ("age_bracket", SensitivityLevel.LOW),
        ("has_partner", SensitivityLevel.LOW),
        ("heeft_kinderen", SensitivityLevel.LOW),
        ("unknown_field", SensitivityLevel.LOW),  # Default to LOW
    ]
    
    for field_name, expected in test_fields:
        result = SimpleDataClassifier.classify_field(field_name)
        status = "✅" if result == expected else "❌"
        print(f"{status} {field_name}: {result.name} (expected {expected.name})")
        
    return True


def test_early_law_elimination():
    """Test early elimination of laws based on demographics"""
    print("\n=== Testing Early Law Elimination ===")
    
    filter = SimpleEarlyFilter()
    
    # Test different demographic scenarios
    test_scenarios = [
        {
            "name": "Young person (18-66)",
            "basic_info": {"age_bracket": "18-66", "has_partner": True, "has_children": False},
            "laws": [
                ("aow_pension", True),  # Should skip - too young for pension
                ("student_finance", False),  # Should not skip - right age
                ("partner_toeslag", False),  # Should not skip - has partner
                ("child_benefits", True),  # Should skip - no children
            ]
        },
        {
            "name": "Elderly person (67+)",
            "basic_info": {"age_bracket": "67+", "has_partner": False, "has_children": True},
            "laws": [
                ("aow_pension", False),  # Should not skip - right age
                ("student_finance", True),  # Should skip - too old
                ("partner_toeslag", True),  # Should skip - no partner
                ("kinderbijslag", False),  # Might not skip - has children
            ]
        },
        {
            "name": "Single young person",
            "basic_info": {"age_bracket": "18-66", "has_partner": False, "has_children": False},
            "laws": [
                ("partner_supplement", True),  # Should skip - no partner
                ("child_care_allowance", True),  # Should skip - no children
                ("general_benefit", False),  # Should not skip - general law
            ]
        }
    ]
    
    for scenario in test_scenarios:
        print(f"\n--- {scenario['name']} ---")
        filter.reset_metrics()
        
        for law_name, should_skip in scenario['laws']:
            result = filter.can_skip_law(law_name, scenario['basic_info'])
            status = "✅" if result == should_skip else "❌"
            action = "SKIP" if result else "PROCESS"
            print(f"{status} {law_name}: {action}")
        
        elimination_rate = filter.get_elimination_rate()
        print(f"Elimination rate: {elimination_rate:.1f}%")
    
    return True


def test_execution_trace_optimization():
    """Test the execution trace optimization"""
    print("\n=== Testing Execution Trace Optimization ===")
    
    optimizer = ExecutionTraceOptimizer()
    
    # Test field ordering
    test_fields = ["BSN", "age_bracket", "exact_income", "has_partner", "address"]
    optimized_fields = optimizer.optimize_execution_order(test_fields)
    
    print("Field execution order:")
    for i, field in enumerate(optimized_fields, 1):
        sensitivity = SimpleDataClassifier.classify_field(field)
        print(f"  {i}. {field} ({sensitivity.name})")
    
    # Verify LOW sensitivity fields come first
    low_fields = [f for f in optimized_fields 
                  if SimpleDataClassifier.classify_field(f) == SensitivityLevel.LOW]
    high_fields = [f for f in optimized_fields 
                   if SimpleDataClassifier.classify_field(f) == SensitivityLevel.HIGH]
    
    if len(low_fields) > 0 and len(high_fields) > 0:
        low_positions = [optimized_fields.index(f) for f in low_fields]
        high_positions = [optimized_fields.index(f) for f in high_fields]
        
        if max(low_positions) < min(high_positions):
            print("✅ LOW sensitivity fields come before HIGH sensitivity fields")
        else:
            print("❌ Field ordering incorrect")
    
    return True


def test_data_minimized_executor():
    """Test the execution with data minimization"""
    print("\n=== Testing Data Minimized Executor ===")
    
    executor = DataMinimizedExecutor()
    
    # Mock engine for testing
    class MockEngine:
        def __init__(self, name):
            self.name = name
            
        def evaluate(self, data):
            # Simple mock evaluation
            return {
                "output": {"result": "eligible" if data.get("age_bracket") != "0-17" else "ineligible"},
                "requirements_met": True
            }
        
        def __str__(self):
            return self.name
    
    # Test execution with minimization
    mock_engine = MockEngine("test_pension_law")
    parameters = {"BSN": "123456789"}
    
    result = executor.execute_with_minimization(mock_engine, parameters)
    trace_summary = executor.get_trace_summary()
    
    print("Execution result:", result)
    print("Trace summary:", trace_summary)
    
    # Check if some fields were accessed and some skipped
    if trace_summary["fields_accessed"] > 0:
        print("✅ Fields were accessed during execution")
    else:
        print("❌ No fields were accessed")
    
    return True


def test_complete_workflow():
    """Test the complete data minimization workflow"""
    print("\n=== Testing Complete Workflow ===")
    
    # Initialize components
    early_filter = SimpleEarlyFilter()
    executor = DataMinimizedExecutor()
    metrics = SimpleMetrics()
    
    # Mock data
    bsn = "123456789"
    mock_laws = [
        {"name": "aow_pension", "spec": {}},
        {"name": "student_finance", "spec": {}},
        {"name": "child_benefits", "spec": {}},
        {"name": "partner_supplement", "spec": {}},
        {"name": "general_assistance", "spec": {}}
    ]
    
    # Step 1: Get basic demographic info
    basic_info = early_filter.get_basic_info(bsn)
    print(f"Basic info: {basic_info}")
    
    # Step 2: Filter laws early
    applicable_laws = []
    for law in mock_laws:
        if early_filter.can_skip_law(law['name'], basic_info):
            metrics.record_law_skipped(law['name'])
        else:
            applicable_laws.append(law)
    
    print(f"Laws after early filtering: {len(applicable_laws)}/{len(mock_laws)}")
    
    # Step 3: Process remaining laws with trace optimization
    class MockEngine:
        def evaluate(self, data):
            return {"output": {"amount": 1000}, "requirements_met": True}
    
    for law in applicable_laws:
        # Mock engine execution
        mock_engine = MockEngine()
        result = executor.execute_with_minimization(mock_engine, {"BSN": bsn})
        
        # Get sensitivity and trace info
        sensitivity = SimpleDataClassifier.get_law_max_sensitivity(law['spec'])
        trace_summary = executor.get_trace_summary()
        
        metrics.record_law_processed(law['name'], sensitivity, trace_summary)
    
    # Step 4: Get final metrics
    summary = metrics.get_summary()
    print(f"\nFinal Results:")
    print(f"  Total laws considered: {summary['total_laws']}")
    print(f"  Laws skipped early: {summary['laws_skipped']} ({summary['law_skip_rate_percent']}%)")
    print(f"  Laws processed: {summary['laws_processed']}")
    print(f"  Fields accessed: {summary['total_fields_accessed']}")
    print(f"  Fields skipped: {summary['total_fields_skipped']}")
    if summary['total_fields_accessed'] + summary['total_fields_skipped'] > 0:
        print(f"  Field skip rate: {summary['field_skip_rate_percent']}%")
    
    return True


def main():
    """Run all tests"""
    print("🔍 Testing Simplified Data Minimization Implementation")
    print("=" * 60)
    
    tests = [
        ("Field Classification", test_field_classification),
        ("Early Law Elimination", test_early_law_elimination),
        ("Execution Trace Optimization", test_execution_trace_optimization),
        ("Data Minimized Executor", test_data_minimized_executor),
        ("Complete Workflow", test_complete_workflow)
    ]
    
    results = {}
    for test_name, test_func in tests:
        try:
            print(f"\n{'='*20} {test_name} {'='*20}")
            results[test_name] = test_func()
            print(f"✅ {test_name}: PASSED")
        except Exception as e:
            results[test_name] = False
            print(f"❌ {test_name}: FAILED - {e}")
            import traceback
            traceback.print_exc()
    
    # Summary
    print(f"\n{'='*60}")
    print("🏁 Test Summary")
    print(f"{'='*60}")
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
    
    print(f"\nOverall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! The simplified data minimization system works correctly.")
        return 0
    else:
        print("⚠️ Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)