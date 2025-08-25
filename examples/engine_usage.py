"""
Examples showing how to use the regular RulesEngine vs MinimizationEngine.

This script demonstrates the different usage patterns and what results you get.
"""

from machine.engine import RulesEngine
from machine.minimization_engine import MinimizationEngine, create_minimization_engine


# Example law specification
AOW_LAW_SPEC = {
    "law": "AOW Wet",
    "service": "pension_service",
    "actions": [
        {
            "output": "age_eligible",
            "expression": {
                "operator": ">=",
                "operands": ["$age", 67]
            }
        },
        {
            "output": "years_of_residence", 
            "expression": {
                "reference": "$residence_years"
            }
        },
        {
            "output": "residence_eligible",
            "expression": {
                "operator": ">=", 
                "operands": ["$years_of_residence", 50]
            }
        },
        {
            "output": "pension_amount",
            "expression": {
                "operator": "if",
                "condition": {
                    "operator": "and",
                    "operands": ["$age_eligible", "$residence_eligible"]
                },
                "then": {"value": 1500},
                "else": {"value": 0}
            }
        },
        {
            "output": "eligible",
            "expression": {
                "operator": "and",
                "operands": ["$age_eligible", "$residence_eligible"]
            }
        }
    ],
    "properties": {
        "parameters": [
            {"name": "age", "type": "integer"},
            {"name": "BSN", "type": "string"},
            {"name": "residence_years", "type": "integer"}
        ],
        "output": [
            {"name": "eligible", "type": "boolean"},
            {"name": "pension_amount", "type": "number"}
        ]
    }
}

STUDENT_LAW_SPEC = {
    "law": "Student Financial Aid",
    "service": "education_service", 
    "actions": [
        {
            "output": "age_eligible",
            "expression": {
                "operator": "<=",
                "operands": ["$age", 30]
            }
        },
        {
            "output": "income_eligible",
            "expression": {
                "operator": "<",
                "operands": ["$yearly_income", 25000]
            }
        },
        {
            "output": "eligible",
            "expression": {
                "operator": "and",
                "operands": ["$age_eligible", "$income_eligible"]
            }
        },
        {
            "output": "benefit_amount",
            "expression": {
                "operator": "if",
                "condition": {"reference": "$eligible"},
                "then": {"value": 800},
                "else": {"value": 0}
            }
        }
    ],
    "properties": {
        "parameters": [
            {"name": "age", "type": "integer"},
            {"name": "yearly_income", "type": "number"},
            {"name": "BSN", "type": "string"}
        ]
    }
}


def demo_regular_engine():
    """Show how to use the regular RulesEngine"""
    print("=" * 60)
    print("REGULAR RULESENGINE USAGE")
    print("=" * 60)
    
    # Create regular engine
    engine = RulesEngine(AOW_LAW_SPEC)
    
    print(f"Law: {engine.law}")
    print(f"Service: {engine.service_name}")
    
    # Test with young person (should be ineligible)
    young_person = {
        "age": 25,
        "BSN": "123456789", 
        "residence_years": 25
    }
    
    print(f"\nEvaluating young person: {young_person}")
    result = engine.evaluate(young_person)
    print(f"Result: {result}")
    
    # Test with elderly person (should be eligible)
    elderly_person = {
        "age": 70,
        "BSN": "987654321",
        "residence_years": 55
    }
    
    print(f"\nEvaluating elderly person: {elderly_person}")
    result = engine.evaluate(elderly_person)
    print(f"Result: {result}")


def demo_minimization_engine():
    """Show how to use the MinimizationEngine"""
    print("\n" + "=" * 60) 
    print("MINIMIZATION ENGINE USAGE")
    print("=" * 60)
    
    # Method 1: Direct construction
    engine = MinimizationEngine(AOW_LAW_SPEC)
    
    print(f"Law: {engine.law}")
    
    # Test with young person - should be eliminated early!
    young_person = {
        "age": 25,
        "BSN": "123456789",  # This sensitive data won't be accessed!
        "residence_years": 25
    }
    
    print(f"\nEvaluating young person: {young_person}")
    result = engine.evaluate(young_person)
    print(f"Result: {result}")
    print(f"Minimization metrics: {result['minimization']}")
    
    # Test with elderly person  
    elderly_person = {
        "age": 70,
        "BSN": "987654321",
        "residence_years": 55
    }
    
    print(f"\nEvaluating elderly person: {elderly_person}")
    result = engine.evaluate(elderly_person)
    print(f"Result: {result}")
    print(f"Minimization metrics: {result['minimization']}")


def demo_factory_function():
    """Show how to use the factory function"""
    print("\n" + "=" * 60)
    print("FACTORY FUNCTION USAGE") 
    print("=" * 60)
    
    # Method 2: Using factory function
    engine = create_minimization_engine(STUDENT_LAW_SPEC)
    
    # Test with elderly person applying for student aid
    elderly_student = {
        "age": 75,  # Too old for student benefits
        "yearly_income": 15000,
        "BSN": "555666777"  # Won't be accessed due to early elimination
    }
    
    print(f"Law: {engine.law}")
    print(f"Evaluating elderly student: {elderly_student}")
    result = engine.evaluate(elderly_student)
    print(f"Result: {result}")
    print(f"Minimization metrics: {result['minimization']}")


def demo_comparison():
    """Compare regular vs minimization engine side by side"""
    print("\n" + "=" * 60)
    print("SIDE-BY-SIDE COMPARISON")
    print("=" * 60)
    
    test_person = {
        "age": 30,  # Young person applying for AOW
        "BSN": "123456789",
        "residence_years": 30
    }
    
    print(f"Test person: {test_person}")
    print(f"Law: {AOW_LAW_SPEC['law']} (requires age 67+)")
    
    # Regular engine
    print("\n--- REGULAR ENGINE ---")
    regular_engine = RulesEngine(AOW_LAW_SPEC)
    regular_result = regular_engine.evaluate(test_person)
    print(f"Accesses all data, computes all actions")
    print(f"Result: eligible = {regular_result.get('output', {}).get('eligible', 'N/A')}")
    
    # Minimization engine  
    print("\n--- MINIMIZATION ENGINE ---")
    min_engine = MinimizationEngine(AOW_LAW_SPEC)
    min_result = min_engine.evaluate(test_person)
    
    if min_result["eliminated"]:
        print("✅ ELIMINATED EARLY - No sensitive data accessed!")
        print(f"Reason: {min_result['reason']}")
        print(f"Savings: {min_result['minimization']}")
    else:
        print("Executed with optimization")
        print(f"Result: {min_result}")


def demo_custom_config():
    """Show how to use custom elimination rules config"""
    print("\n" + "=" * 60)
    print("CUSTOM CONFIG USAGE")
    print("=" * 60)
    
    # You can specify a custom config file
    # engine = MinimizationEngine(law_spec, config_path="custom_rules.yaml")
    
    # Or use default config (elimination_rules.yaml in machine/ folder)
    engine = MinimizationEngine(AOW_LAW_SPEC)
    
    print("Using default config from: machine/elimination_rules.yaml")
    print(f"High sensitivity fields: {len(engine.high_sensitivity_fields)} fields")
    print(f"Elimination rules loaded: {len(engine.elimination_rules)} rules")
    
    # Show sensitivity classification
    print("\nField sensitivity examples:")
    test_fields = ["age", "age_bracket", "BSN", "INKOMEN", "has_partner", "TOTAL_INCOME_2024"]
    for field in test_fields:
        is_sensitive = engine._is_sensitive_field(field)
        level = "HIGH" if is_sensitive else "LOW"
        print(f"  {field:20} → {level}")


if __name__ == "__main__":
    # Run all demos
    demo_regular_engine()
    demo_minimization_engine() 
    demo_factory_function()
    demo_comparison()
    demo_custom_config()
    
    print("\n" + "=" * 60)
    print("SUMMARY")
    print("=" * 60)
    print("""
    REGULAR ENGINE:
    - from machine.engine import RulesEngine
    - engine = RulesEngine(law_spec)
    - result = engine.evaluate(parameters)
    - Accesses all data, executes all actions
    
    MINIMIZATION ENGINE:
    - from machine.minimization_engine import MinimizationEngine
    - engine = MinimizationEngine(law_spec)
    - result = engine.evaluate(parameters)  
    - Eliminates laws early, skips sensitive data when possible
    - Includes minimization metrics in result
    
    FACTORY FUNCTION:
    - from machine.minimization_engine import create_minimization_engine
    - engine = create_minimization_engine(law_spec)
    """)