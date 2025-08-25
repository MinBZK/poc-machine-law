"""
Pytest-compatible tests for the simplified data minimization system.
"""

import pytest
import sys
import os

# Add parent directory to path to import machine module
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from machine.simple_sensitivity import (
    SimpleDataClassifier, 
    SimpleEarlyFilter, 
    DataMinimizedExecutor,
    ExecutionTraceOptimizer,
    SimpleMetrics,
    SensitivityLevel
)


class TestSimpleDataClassifier:
    """Test the simple 2-level field classification"""
    
    def test_field_classification(self):
        """Test classification of various field types"""
        test_cases = [
            ("BSN", SensitivityLevel.HIGH),
            ("VERBLIJFSADRES", SensitivityLevel.HIGH),
            ("INKOMEN", SensitivityLevel.HIGH),
            ("age_bracket", SensitivityLevel.LOW),
            ("has_partner", SensitivityLevel.LOW),
            ("heeft_kinderen", SensitivityLevel.LOW),
            ("unknown_field", SensitivityLevel.LOW),  # Default to LOW
        ]
        
        for field_name, expected in test_cases:
            result = SimpleDataClassifier.classify_field(field_name)
            assert result == expected, f"Field {field_name} should be {expected.name}, got {result.name}"
    
    def test_keyword_matching(self):
        """Test that keyword matching works correctly"""
        high_sensitivity_fields = [
            "PARTNER_EXACT_YEARLY_INCOME_2023",  # Contains INCOME
            "USER_HOME_ADDRESS",                  # Contains ADRES
            "BIRTH_DATE_FIELD",                   # Contains GEBOORTE
            "TOTAL_AMOUNT_DUE"                    # Contains AMOUNT
        ]
        
        for field in high_sensitivity_fields:
            result = SimpleDataClassifier.classify_field(field)
            assert result == SensitivityLevel.HIGH, f"Field {field} should be HIGH sensitivity"
    
    def test_law_sensitivity_scoring(self):
        """Test law-level sensitivity scoring"""
        law_data = {
            "properties": {
                "parameters": [
                    {"name": "age_bracket"},
                    {"name": "BSN"}
                ]
            }
        }
        
        result = SimpleDataClassifier.get_law_max_sensitivity(law_data)
        assert result == SensitivityLevel.HIGH, "Law with BSN should have HIGH sensitivity"


class TestSimpleEarlyFilter:
    """Test early elimination of laws"""
    
    @pytest.fixture
    def filter(self):
        return SimpleEarlyFilter()
    
    def test_age_based_elimination(self, filter):
        """Test elimination based on age brackets"""
        young_person = {"age_bracket": "18-66", "has_partner": True, "has_children": False}
        elderly_person = {"age_bracket": "67+", "has_partner": True, "has_children": False}
        
        # AOW should be skipped for young people
        assert filter.can_skip_law("aow_pension", young_person) == True
        assert filter.can_skip_law("aow_pension", elderly_person) == False
        
        # Student benefits should be skipped for elderly
        assert filter.can_skip_law("student_finance", elderly_person) == True
        assert filter.can_skip_law("student_finance", young_person) == False
    
    def test_partner_based_elimination(self, filter):
        """Test elimination based on partner status"""
        single_person = {"age_bracket": "18-66", "has_partner": False, "has_children": False}
        coupled_person = {"age_bracket": "18-66", "has_partner": True, "has_children": False}
        
        # Partner-dependent laws should be skipped for singles
        assert filter.can_skip_law("partner_supplement", single_person) == True
        assert filter.can_skip_law("partner_supplement", coupled_person) == False
    
    def test_children_based_elimination(self, filter):
        """Test elimination based on children status"""
        childless = {"age_bracket": "18-66", "has_partner": True, "has_children": False}
        with_children = {"age_bracket": "18-66", "has_partner": True, "has_children": True}
        
        # Child benefits should be skipped for childless people
        assert filter.can_skip_law("kinderbijslag", childless) == True
        assert filter.can_skip_law("kinderbijslag", with_children) == False
    
    def test_basic_info_collection(self, filter):
        """Test basic demographic info collection"""
        basic_info = filter.get_basic_info("123456789")
        
        required_keys = ["age_bracket", "has_partner", "has_children"]
        for key in required_keys:
            assert key in basic_info, f"Basic info should contain {key}"
        
        # Check value types
        assert basic_info["age_bracket"] in ["0-17", "18-66", "67+"]
        assert isinstance(basic_info["has_partner"], bool)
        assert isinstance(basic_info["has_children"], bool)


class TestExecutionTraceOptimizer:
    """Test execution trace optimization"""
    
    @pytest.fixture
    def optimizer(self):
        return ExecutionTraceOptimizer()
    
    def test_field_ordering(self, optimizer):
        """Test that LOW sensitivity fields come before HIGH sensitivity fields"""
        test_fields = ["BSN", "age_bracket", "exact_income", "has_partner", "address"]
        optimized_fields = optimizer.optimize_execution_order(test_fields)
        
        # Get positions of first HIGH and LOW sensitivity fields
        low_positions = []
        high_positions = []
        
        for i, field in enumerate(optimized_fields):
            sensitivity = SimpleDataClassifier.classify_field(field)
            if sensitivity == SensitivityLevel.LOW:
                low_positions.append(i)
            else:
                high_positions.append(i)
        
        # LOW sensitivity fields should come before HIGH sensitivity fields
        if low_positions and high_positions:
            assert max(low_positions) < min(high_positions), \
                "LOW sensitivity fields should come before HIGH sensitivity fields"


class TestSimpleMetrics:
    """Test metrics tracking"""
    
    @pytest.fixture
    def metrics(self):
        return SimpleMetrics()
    
    def test_law_tracking(self, metrics):
        """Test law skipping and processing metrics"""
        # Record some activities
        metrics.record_law_skipped("test_law_1")
        metrics.record_law_processed("test_law_2", SensitivityLevel.HIGH)
        metrics.record_law_processed("test_law_3", SensitivityLevel.LOW, 
                                   {"fields_accessed": 3, "fields_skipped": 2})
        
        summary = metrics.get_summary()
        
        # Check basic counts
        assert summary["total_laws"] == 3
        assert summary["laws_skipped"] == 1
        assert summary["laws_processed"] == 2
        assert summary["law_skip_rate_percent"] == 33.3
        
        # Check field tracking
        assert summary["total_fields_accessed"] == 3
        assert summary["total_fields_skipped"] == 2
    
    def test_empty_metrics(self, metrics):
        """Test metrics with no data"""
        summary = metrics.get_summary()
        
        assert summary["total_laws"] == 0
        assert summary["law_skip_rate_percent"] == 0
        assert summary["field_skip_rate_percent"] == 0


class TestIntegration:
    """Integration tests combining multiple components"""
    
    def test_complete_workflow(self):
        """Test the complete data minimization workflow"""
        # Initialize components
        early_filter = SimpleEarlyFilter()
        executor = DataMinimizedExecutor()
        metrics = SimpleMetrics()
        
        # Mock laws
        mock_laws = [
            {"name": "aow_pension", "spec": {}},
            {"name": "student_finance", "spec": {}},
            {"name": "child_benefits", "spec": {}},
            {"name": "general_assistance", "spec": {}}
        ]
        
        # Get basic info
        basic_info = early_filter.get_basic_info("123456789")
        
        # Filter laws
        applicable_laws = []
        for law in mock_laws:
            if early_filter.can_skip_law(law['name'], basic_info):
                metrics.record_law_skipped(law['name'])
            else:
                applicable_laws.append(law)
        
        # Should have filtered some laws
        assert len(applicable_laws) < len(mock_laws), "Some laws should be filtered out"
        
        # Process remaining laws
        for law in applicable_laws:
            sensitivity = SimpleDataClassifier.get_law_max_sensitivity(law['spec'])
            metrics.record_law_processed(law['name'], sensitivity)
        
        # Get final summary
        summary = metrics.get_summary()
        assert summary["total_laws"] == len(mock_laws)
        assert summary["laws_skipped"] > 0 or summary["laws_processed"] > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])