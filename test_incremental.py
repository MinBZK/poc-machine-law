"""
Test script to demonstrate incremental sensitive parameter access.
"""

import logging
from machine.minimization_engine import MinimizationEngine

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

def test_incremental_access():
    """Test incremental access with multiple sensitive parameters"""
    
    # Mock law specification with multiple sensitive params
    demo_spec = {
        "law": "test_benefit_law",
        "service": "test_service", 
        "actions": [
            {
                "output": "basic_eligible",
                "expression": {"operator": ">=", "operands": ["$age", 18]}
            },
            {
                "output": "income_eligible", 
                "expression": {"operator": "<", "operands": ["$yearly_income", 50000]}
            },
            {
                "output": "asset_eligible",
                "expression": {"operator": "<", "operands": ["$total_assets", 100000]}
            },
            {
                "output": "final_eligible",
                "expression": {
                    "operator": "and", 
                    "operands": ["$basic_eligible", "$income_eligible", "$asset_eligible"]
                }
            }
        ],
        "properties": {
            "parameters": [
                {"name": "age", "type": "integer", "required": False},
                {"name": "BSN", "type": "string", "required": True},  # HIGH sensitivity, required
                {"name": "yearly_income", "type": "number", "required": False},  # HIGH sensitivity, optional
                {"name": "total_assets", "type": "number", "required": False},   # HIGH sensitivity, optional
                {"name": "bank_account", "type": "string", "required": False}    # HIGH sensitivity, optional
            ]
        }
    }
    
    # Person with multiple sensitive parameters
    person_data = {
        "age": 25,                           # LOW sensitivity
        "BSN": "123456789",                  # HIGH sensitivity, required
        "yearly_income": 75000,              # HIGH sensitivity - above threshold!
        "total_assets": 50000,               # HIGH sensitivity 
        "bank_account": "NL91ABNA0417164300" # HIGH sensitivity
    }
    
    print("=" * 80)
    print("🧪 TESTING INCREMENTAL SENSITIVE PARAMETER ACCESS")
    print("=" * 80)
    
    print(f"📋 Person data:")
    for key, value in person_data.items():
        print(f"  {key}: {value}")
    
    print(f"\n💡 Expected outcome:")
    print(f"   - yearly_income (€75,000) > threshold (€50,000)")
    print(f"   - Should determine ineligible after accessing BSN + yearly_income")
    print(f"   - Should skip accessing total_assets + bank_account")
    
    print(f"\n" + "="*50)
    print("🔍 MINIMIZATION ENGINE EXECUTION")
    print("="*50)
    
    engine = MinimizationEngine(demo_spec)
    result = engine.evaluate(person_data)
    
    print(f"\n📊 Result: {result.get('output', {})}")
    
    if result.get('minimization'):
        metrics = result['minimization']
        print(f"\n📈 Minimization Metrics:")
        print(f"   Fields accessed: {metrics.get('fields_accessed', 0)}")
        print(f"   Fields skipped: {metrics.get('fields_skipped', 0)}")
        print(f"   Skip rate: {metrics.get('field_skip_rate_percent', 0)}%")
    
    print("\n" + "="*80)
    print("🎯 SUMMARY")
    print("="*80)
    print("""
    This demonstrates incremental sensitive parameter access:
    1. Start with LOW sensitivity params (age)
    2. Add required sensitive params first (BSN)  
    3. Add optional sensitive params one by one (yearly_income, total_assets, bank_account)
    4. Check for early determination after each addition
    5. Skip remaining sensitive params if result is clear
    """)

if __name__ == "__main__":
    test_incremental_access()