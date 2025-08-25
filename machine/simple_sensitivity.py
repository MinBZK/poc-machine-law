"""
Simple utilities for data sensitivity classification and metrics.

This module now provides basic utilities that support the main MinimizationEngine.
Most functionality has been moved to minimization_engine.py for better organization.
"""

from typing import Dict
from enum import IntEnum
import logging


class SensitivityLevel(IntEnum):
    """Simplified data sensitivity levels"""
    LOW = 1   # Basic demographic info, age brackets, boolean flags
    HIGH = 2  # Personal identifiers, exact financial data, addresses


class SimpleMetrics:
    """Simple metrics tracking for data minimization"""
    
    def __init__(self):
        self.reset()
    
    def reset(self):
        """Reset all metrics"""
        self.laws_skipped = 0
        self.laws_processed = 0
        self.high_sensitivity_laws = 0
        self.total_fields_accessed = 0
        self.total_fields_skipped = 0
    
    def record_law_skipped(self, law_name: str):
        """Record that a law was skipped early"""
        self.laws_skipped += 1
        logging.info(f"Skipped law: {law_name}")
    
    def record_law_processed(self, law_name: str, sensitivity: SensitivityLevel, trace_summary: Dict = None):
        """Record that a law was processed with trace info"""
        self.laws_processed += 1
        if sensitivity == SensitivityLevel.HIGH:
            self.high_sensitivity_laws += 1
            
        if trace_summary:
            self.total_fields_accessed += trace_summary.get("fields_accessed", 0)
            self.total_fields_skipped += trace_summary.get("fields_skipped", 0)
            
        logging.info(f"Processed law: {law_name} (sensitivity: {sensitivity.name})")
    
    def get_summary(self) -> Dict:
        """Get comprehensive summary of data minimization"""
        total_laws = self.laws_skipped + self.laws_processed
        law_skip_rate = (self.laws_skipped / total_laws * 100) if total_laws > 0 else 0
        
        total_fields = self.total_fields_accessed + self.total_fields_skipped
        field_skip_rate = (self.total_fields_skipped / total_fields * 100) if total_fields > 0 else 0
        
        return {
            "total_laws": total_laws,
            "laws_skipped": self.laws_skipped,
            "laws_processed": self.laws_processed,
            "law_skip_rate_percent": round(law_skip_rate, 1),
            "high_sensitivity_laws": self.high_sensitivity_laws,
            "total_fields_accessed": self.total_fields_accessed,
            "total_fields_skipped": self.total_fields_skipped,
            "field_skip_rate_percent": round(field_skip_rate, 1)
        }