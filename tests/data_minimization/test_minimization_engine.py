"""
Tests for the consolidated MinimizationEngine.
"""

import pytest
import tempfile
import yaml
from pathlib import Path
from machine.minimization_engine import MinimizationEngine, create_minimization_engine, SensitivityLevel
from machine.simple_sensitivity import SimpleMetrics


class TestMinimizationEngine:
    """Test cases for the consolidated MinimizationEngine"""
    
    def test_engine_creation(self):
        """Test basic engine creation"""
        spec = {
            "law": "Test Law",
            "service": "test_service",
            "actions": [],
            "properties": {
                "parameters": [],
                "input": [],
                "sources": [],
                "output": []
            }
        }
        
        engine = MinimizationEngine(spec)
        
        assert engine.law == "Test Law"
        assert engine.spec == spec
        assert engine.laws_eliminated == 0
        assert engine.laws_evaluated == 0
    
    def test_factory_function(self):
        """Test the factory function"""
        spec = {"law": "Factory Test", "actions": []}
        engine = create_minimization_engine(spec)
        
        assert isinstance(engine, MinimizationEngine)
        assert engine.law == "Factory Test"
    
    def test_basic_info_extraction(self):
        """Test extraction of basic demographic info"""
        spec = {"law": "Test Law", "actions": []}
        engine = MinimizationEngine(spec)
        
        parameters = {
            "age": 25,
            "BSN": "123456789",  # Should be filtered out
            "has_partner": True,
            "exact_income": 50000,  # Should be filtered out
            "has_children": False
        }
        
        basic_info = engine._extract_basic_info(parameters)
        
        assert "age_bracket" in basic_info
        assert basic_info["age_bracket"] == "18-66"
        assert basic_info["has_partner"] is True
        assert basic_info["has_children"] is False
        assert "BSN" not in basic_info
        assert "exact_income" not in basic_info
    
    def test_age_bracket_conversion(self):
        """Test age to age_bracket conversion"""
        spec = {"law": "Test Law", "actions": []}
        engine = MinimizationEngine(spec)
        
        # Test different age groups
        assert engine._extract_basic_info({"age": 16})["age_bracket"] == "0-17"
        assert engine._extract_basic_info({"age": 35})["age_bracket"] == "18-66"  
        assert engine._extract_basic_info({"age": 70})["age_bracket"] == "67+"
    
    def test_condition_evaluation(self):
        """Test rule condition evaluation"""
        spec = {"law": "Test Law", "actions": []}
        engine = MinimizationEngine(spec)
        
        # Test different operators
        assert engine._evaluate_condition("67+", "equals", "67+") is True
        assert engine._evaluate_condition("18-66", "equals", "67+") is False
        assert engine._evaluate_condition("18-66", "not_equals", "67+") is True
        assert engine._evaluate_condition(False, "equals", False) is True
        assert engine._evaluate_condition("active", "contains", "act") is True
    
    def test_early_elimination_with_aow(self):
        """Test early elimination for AOW law"""
        spec = {
            "law": "AOW Wet",
            "actions": [
                {"output": "pension_amount", "expression": {"value": 1500}},
                {"output": "eligible", "expression": {"value": True}}
            ]
        }
        
        engine = MinimizationEngine(spec)
        parameters = {"age": 25, "BSN": "123456789"}
        
        result = engine.evaluate(parameters)
        
        assert result["eliminated"] is True
        assert result["reason"] == "early_elimination"
        assert result["law"] == "AOW Wet"
        assert result["minimization"]["laws_eliminated"] == 1
    
    def test_no_elimination_for_eligible_person(self):
        """Test that eligible person doesn't get eliminated early"""
        spec = {
            "law": "AOW Wet",
            "actions": [
                {"output": "eligible", "expression": {"value": True}}
            ]
        }
        
        engine = MinimizationEngine(spec)
        parameters = {"age": 70, "BSN": "123456789"}
        
        result = engine.evaluate(parameters)
        
        assert result["eliminated"] is False
        assert result["minimization"]["laws_evaluated"] == 1
        assert result["minimization"]["laws_eliminated"] == 0
    
    def test_sensitivity_field_detection(self):
        """Test HIGH sensitivity field detection"""
        spec = {"law": "Test Law", "actions": []}
        engine = MinimizationEngine(spec)
        
        # Test fields from default config
        assert engine._is_sensitive_field("BSN") is True
        assert engine._is_sensitive_field("INKOMEN") is True
        assert engine._is_sensitive_field("TOTAL_INKOMEN_2024") is True  # Keyword match
        
        # Test LOW sensitivity fields
        assert engine._is_sensitive_field("age_bracket") is False
        assert engine._is_sensitive_field("has_partner") is False
    
    def test_law_sensitivity_classification(self):
        """Test overall law sensitivity classification"""
        # HIGH sensitivity law (has BSN parameter)
        high_spec = {
            "law": "High Sensitivity Law",
            "actions": [],
            "properties": {
                "parameters": [{"name": "BSN", "type": "string"}]
            }
        }
        engine = MinimizationEngine(high_spec)
        assert engine.get_law_sensitivity() == SensitivityLevel.HIGH
        
        # LOW sensitivity law (only basic parameters)
        low_spec = {
            "law": "Low Sensitivity Law", 
            "actions": [],
            "properties": {
                "parameters": [{"name": "age_bracket", "type": "string"}]
            }
        }
        engine = MinimizationEngine(low_spec)
        assert engine.get_law_sensitivity() == SensitivityLevel.LOW
    
    def test_metrics_tracking(self):
        """Test that metrics are tracked correctly"""
        spec = {
            "law": "Student Benefits",
            "actions": [
                {"output": "age_eligible", "expression": {"value": True}}
            ]
        }
        
        engine = MinimizationEngine(spec)
        parameters = {"age": 25}
        
        result = engine.evaluate(parameters)
        
        metrics = result["minimization"]
        assert "laws_evaluated" in metrics
        assert "fields_accessed" in metrics
        assert "field_skip_rate_percent" in metrics
        assert "elimination_rate_percent" in metrics
    
    def test_custom_config_path(self):
        """Test using custom elimination rules config"""
        # Create temporary config
        custom_rules = {
            "sensitivity": {
                "high_sensitivity_fields": ["CUSTOM_FIELD"],
                "high_sensitivity_keywords": ["CUSTOM"]
            },
            "elimination_rules": {
                "custom": [{
                    "rule_id": "custom_rule",
                    "name": "Custom Rule",
                    "description": "Custom elimination rule",
                    "triggers": {"law_name_contains": ["custom"]},
                    "conditions": [{"field": "age_bracket", "operator": "equals", "value": "18-66"}],
                    "action": "eliminate",
                    "log_message": "custom rule triggered"
                }]
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(custom_rules, f)
            temp_path = f.name
        
        try:
            spec = {"law": "Custom Law", "actions": []}
            engine = MinimizationEngine(spec, config_path=temp_path)
            
            # Should load custom configuration
            assert "CUSTOM_FIELD" in engine.high_sensitivity_fields
            assert len(engine.elimination_rules) == 1
            assert engine.elimination_rules[0]["rule_id"] == "custom_rule"
            
        finally:
            Path(temp_path).unlink()


class TestIntegrationScenarios:
    """Test realistic integration scenarios"""
    
    def test_aow_young_person_scenario(self):
        """Complete test of AOW law for young person"""
        spec = {
            "law": "AOW Ouderdomspensioen",
            "actions": [
                {"output": "age_check", "expression": {"operator": ">=", "operands": ["$age", 67]}},
                {"output": "pension_amount", "expression": {"value": 1500}},
                {"output": "eligible", "expression": {"reference": "$age_check"}}
            ],
            "properties": {
                "parameters": [
                    {"name": "age", "type": "integer"},
                    {"name": "BSN", "type": "string"}
                ]
            }
        }
        
        engine = MinimizationEngine(spec)
        parameters = {"age": 30, "BSN": "123456789"}
        
        result = engine.evaluate(parameters)
        
        # Should be eliminated early - no sensitive data accessed
        assert result["eliminated"] is True
        metrics = result["minimization"]
        assert metrics["laws_eliminated"] == 1
        assert metrics["elimination_rate_percent"] == 100.0
    
    def test_housing_allowance_no_elimination(self):
        """Test law that doesn't trigger elimination rules"""
        spec = {
            "law": "Housing Allowance",  # No elimination rules for this
            "actions": [
                {"output": "age_ok", "expression": {"operator": ">=", "operands": ["$age", 18]}},
                {"output": "eligible", "expression": {"reference": "$age_ok"}}
            ]
        }
        
        engine = MinimizationEngine(spec)
        parameters = {"age": 25}
        
        result = engine.evaluate(parameters)
        
        # Should execute normally, not eliminated
        assert result["eliminated"] is False
        metrics = result["minimization"]
        assert metrics["laws_evaluated"] == 1
        assert metrics["laws_eliminated"] == 0


class TestSimpleMetrics:
    """Test the SimpleMetrics utility class"""
    
    def test_metrics_creation_and_reset(self):
        """Test metrics creation and reset functionality"""
        metrics = SimpleMetrics()
        
        assert metrics.laws_skipped == 0
        assert metrics.laws_processed == 0
        
        metrics.record_law_skipped("Test Law")
        assert metrics.laws_skipped == 1
        
        metrics.reset()
        assert metrics.laws_skipped == 0
    
    def test_metrics_summary(self):
        """Test metrics summary calculation"""
        metrics = SimpleMetrics()
        
        metrics.record_law_skipped("Law 1")
        metrics.record_law_processed("Law 2", SensitivityLevel.HIGH)
        
        summary = metrics.get_summary()
        
        assert summary["total_laws"] == 2
        assert summary["laws_skipped"] == 1
        assert summary["laws_processed"] == 1
        assert summary["law_skip_rate_percent"] == 50.0
        assert summary["high_sensitivity_laws"] == 1


if __name__ == "__main__":
    pytest.main([__file__])