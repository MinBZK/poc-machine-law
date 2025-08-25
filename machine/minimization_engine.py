"""
Data minimization engine that wraps the core RulesEngine with privacy-preserving features.

This module consolidates all data minimization functionality:
- Early law elimination based on basic demographics
- Field sensitivity classification (LOW/HIGH)  
- Execution trace optimization
- Configuration-driven elimination rules
"""

import yaml
import logging
from typing import Dict, List, Optional, Any, Union
from pathlib import Path
from enum import IntEnum
from copy import copy

from .engine import RulesEngine
from .context import RuleContext


class SensitivityLevel(IntEnum):
    """Data sensitivity levels for privacy classification"""
    LOW = 1   # Basic demographic info, age brackets, boolean flags
    HIGH = 2  # Personal identifiers, exact financial data, addresses


class MinimizationEngine:
    """
    Privacy-preserving wrapper for RulesEngine that minimizes sensitive data access.
    
    Features:
    1. Early law elimination - Skip laws based on basic demographics only
    2. Field sensitivity classification - Identify sensitive vs non-sensitive data
    3. Execution optimization - Process LOW sensitivity data first, terminate early when possible
    4. Configuration-driven rules - YAML-based elimination rules
    """
    
    def __init__(self, spec: Dict[str, Any], service_provider: Any = None, config_path: Optional[str] = None):
        """
        Initialize minimization engine.
        
        Args:
            spec: Law specification dictionary (same as RulesEngine)
            service_provider: Optional service provider for data access
            config_path: Path to elimination rules YAML (optional)
        """
        # Core engine (unchanged)
        self.engine = RulesEngine(spec, service_provider)
        
        # Load minimization configuration
        if config_path is None:
            config_path = Path(__file__).parent / "elimination_rules.yaml"
        self.config_path = Path(config_path)
        self._load_config()
        
        # Metrics tracking
        self.reset_metrics()
    
    def evaluate(
        self,
        parameters: Dict = None,
        overwrite_input: Dict = None,
        sources: Dict = None,
        calculation_date=None,
        requested_output: str = None,
        approved: bool = False,
    ) -> Dict:
        """
        Evaluate law with data minimization.
        
        Compatible with RulesEngine interface.
        
        Args:
            parameters: Input parameters for law evaluation
            overwrite_input: Optional input overrides (passed to base engine)
            sources: Source dataframes (passed to base engine)
            calculation_date: Reference date (passed to base engine)
            requested_output: Specific output requested (passed to base engine)
            approved: Whether to use approved rules (passed to base engine)
            
        Returns:
            Result dictionary with minimization metrics
        """
        parameters = parameters or {}
        self.reset_metrics()
        
        # Step 1: Try early elimination
        if self._try_early_elimination(parameters):
            return {
                "eliminated": True,
                "reason": "early_elimination",
                "law": self.engine.law,
                "minimization": self._get_metrics()
            }
        
        # Step 2: Execute with trace optimization
        try:
            result = self._execute_optimized(parameters, overwrite_input, sources, calculation_date, requested_output, approved)
            result["minimization"] = self._get_metrics()
            return result
        except Exception as e:
            logging.warning(f"Optimized execution failed, falling back to regular: {e}")
            result = self.engine.evaluate(
                parameters=parameters,
                overwrite_input=overwrite_input,
                sources=sources,
                calculation_date=calculation_date,
                requested_output=requested_output,
                approved=approved
            )
            result["minimization"] = self._get_metrics()
            return result
    
    def _try_early_elimination(self, parameters: Dict) -> bool:
        """Check if law can be eliminated using basic demographics only"""
        law_name = self.engine.law or "unknown"
        basic_info = self._extract_basic_info(parameters)
        
        # Log what basic info we extracted (vs full parameters)
        logging.info(f"🔍 Basic info extracted: {basic_info}")
        logging.info(f"📊 Full parameters available: {list(parameters.keys())}")
        sensitive_params = [k for k in parameters.keys() if self._is_sensitive_field(k)]
        logging.info(f"⚠️  Sensitive parameters: {sensitive_params}")
        
        for rule in self.elimination_rules:
            if self._rule_matches(rule, law_name, basic_info):
                self.laws_eliminated += 1
                logging.info(f"🚫 EARLY ELIMINATION: {law_name} ({rule.get('log_message', 'rule matched')})")
                logging.info(f"💰 PRIVACY SAVED: Skipped accessing {len(sensitive_params)} sensitive fields!")
                return True
        
        self.laws_evaluated += 1
        return False
    
    def _extract_basic_info(self, parameters: Dict) -> Dict:
        """Extract only LOW sensitivity demographic fields"""
        basic_fields = ["age_bracket", "has_partner", "has_children", "age", "marital_status"]
        basic_info = {}
        
        for field in basic_fields:
            if field in parameters:
                basic_info[field] = parameters[field]
        
        # Convert age to age_bracket if needed
        if "age" in parameters and "age_bracket" not in basic_info:
            age = parameters["age"]
            if age < 18:
                basic_info["age_bracket"] = "0-17"
            elif age >= 67:
                basic_info["age_bracket"] = "67+"
            else:
                basic_info["age_bracket"] = "18-66"
        
        return basic_info
    
    def _rule_matches(self, rule: Dict, law_name: str, basic_info: Dict) -> bool:
        """Check if elimination rule matches law and conditions"""
        # Check triggers
        triggers = rule.get("triggers", {})
        law_lower = law_name.lower()
        
        # Check law_name_contains
        contains_triggers = triggers.get("law_name_contains", [])
        if contains_triggers and not any(trigger.lower() in law_lower for trigger in contains_triggers):
            return False
        
        # Check and_contains (all must be present)
        and_contains = triggers.get("and_contains", [])
        if and_contains and not all(trigger.lower() in law_lower for trigger in and_contains):
            return False
        
        # Check conditions
        for condition in rule.get("conditions", []):
            field = condition["field"]
            operator = condition["operator"]
            value = condition["value"]
            
            field_value = basic_info.get(field)
            if not self._evaluate_condition(field_value, operator, value):
                return False
        
        return True
    
    def _evaluate_condition(self, field_value: Any, operator: str, expected_value: Any) -> bool:
        """Evaluate a single rule condition"""
        if field_value is None:
            return False
            
        if operator == "equals":
            return field_value == expected_value
        elif operator == "not_equals":
            return field_value != expected_value
        elif operator == "greater_than":
            return field_value > expected_value
        elif operator == "less_than":
            return field_value < expected_value
        elif operator == "contains":
            return str(expected_value).lower() in str(field_value).lower()
        elif operator == "in":
            return field_value in expected_value
        
        return False
    
    def _execute_optimized(self, parameters: Dict, overwrite_input: Dict, sources: Dict, 
                          calculation_date, requested_output: str, approved: bool) -> Dict:
        """Execute with real sensitivity-aware optimization"""
        
        logging.info("🔍 Executing with minimization optimization")
        
        # Step 1: Try to evaluate using only LOW sensitivity data first
        low_sens_params = self._extract_low_sensitivity_params(parameters)
        logging.info(f"📊 LOW sensitivity params: {list(low_sens_params.keys())}")
        
        # Step 2: Try incremental sensitive parameter access
        high_sens_params = self._get_high_sensitivity_params(parameters)
        
        # Always try minimal execution first, regardless of "required" status
        if len(low_sens_params) > 0:
            logging.info("🔍 Attempting execution with LOW sensitivity data only...")
            try:
                minimal_result = self.engine.evaluate(
                    parameters=low_sens_params,
                    overwrite_input=overwrite_input,
                    sources=sources,
                    calculation_date=calculation_date,
                    requested_output=requested_output,
                    approved=approved
                )
                
                if self._can_determine_result_early(minimal_result):
                    logging.info("✅ EARLY DETERMINATION: Result determined from low-sensitivity data only!")
                    logging.info(f"💰 PRIVACY SAVED: Avoided accessing {len(high_sens_params)} sensitive fields: {list(high_sens_params.keys())}")
                    self.fields_skipped = len(high_sens_params)
                    self.fields_accessed = len(low_sens_params)
                    return minimal_result
                else:
                    logging.info("🔄 Low-sensitivity data insufficient - need more parameters")
                    
            except Exception as e:
                logging.debug(f"Minimal execution failed (expected): {e}")
        
        # If minimal execution didn't work, try incremental sensitive access
        if len(high_sens_params) <= 1:
            logging.info("🔒 Need sensitive parameters - using standard execution")
        else:
            # Multiple sensitive params - try incremental access
            logging.info(f"🔍 Multiple sensitive params detected: {list(high_sens_params.keys())}")
            logging.info("🎯 Attempting incremental sensitive parameter access...")
            
            result = self._execute_incremental_access(
                low_sens_params, high_sens_params, 
                overwrite_input, sources, calculation_date, requested_output, approved
            )
            if result:
                return result
        
        # Step 3: Fall back to full execution if needed
        logging.info("⚠️  Need full data - executing with all parameters")
        self.fields_accessed = len(parameters)
        self.fields_skipped = 0
        
        result = self.engine.evaluate(
            parameters=parameters,
            overwrite_input=overwrite_input,
            sources=sources,
            calculation_date=calculation_date,
            requested_output=requested_output,
            approved=approved
        )
        
        return result
    
    def _extract_low_sensitivity_params(self, parameters: Dict) -> Dict:
        """Extract only LOW sensitivity parameters"""
        low_sens_params = {}
        for key, value in parameters.items():
            if not self._is_sensitive_field(key):
                low_sens_params[key] = value
        return low_sens_params
    
    def _get_high_sensitivity_params(self, parameters: Dict) -> Dict:
        """Get HIGH sensitivity parameters"""
        high_sens_params = {}
        for key, value in parameters.items():
            if self._is_sensitive_field(key):
                high_sens_params[key] = value
        return high_sens_params
    
    def _can_determine_result_early(self, result: Dict) -> bool:
        """
        Check if we can determine final eligibility from this partial result.
        
        More aggressive heuristics to maximize BSN avoidance:
        - If requirements clearly not met → can determine early
        - If output shows clear ineligibility → can determine early
        - If partial evaluation succeeded without errors → might be sufficient
        """
        # Check if requirements are clearly not met
        if not result.get("requirements_met", True):
            logging.debug("Early determination: Requirements not met")
            return True
        
        # Check output for clear ineligibility indicators
        output = result.get("output", {})
        for key, value in output.items():
            # Look for eligibility-related outputs that are clearly False
            key_lower = key.lower()
            if any(word in key_lower for word in ["eligible", "entitled", "qualified", "recht"]):
                if value is False:
                    logging.debug(f"Early determination: {key} = False")
                    return True
            
            # Look for amount/benefit outputs that are 0
            if any(word in key_lower for word in ["amount", "benefit", "toeslag", "bedrag"]):
                if isinstance(value, (int, float)) and value == 0:
                    logging.debug(f"Early determination: {key} = 0")
                    return True
        
        # Check if we have a complete successful evaluation without sensitive data
        if output and all(v is not None for v in output.values()):
            logging.debug("Early determination: Complete evaluation without sensitive data")
            return True
        
        return False
    
    def _requires_sensitive_params(self) -> bool:
        """Check if this law requires sensitive parameters as mandatory input"""
        # Check if any required parameters are sensitive
        for param in self.engine.parameter_specs:
            if param.get("required", False) and self._is_sensitive_field(param["name"]):
                return True
        return False
    
    def _execute_incremental_access(self, low_sens_params: Dict, high_sens_params: Dict,
                                   overwrite_input: Dict, sources: Dict, calculation_date,
                                   requested_output: str, approved: bool) -> Optional[Dict]:
        """
        Try accessing sensitive parameters one by one, checking for early determination.
        
        Returns result if early determination possible, None if full execution needed.
        """
        current_params = low_sens_params.copy()
        sensitive_keys = list(high_sens_params.keys())
        
        # Sort sensitive params by "criticality" (required params first)
        required_sensitive = []
        optional_sensitive = []
        
        for key in sensitive_keys:
            is_required = any(
                param.get("name") == key and param.get("required", False) 
                for param in self.engine.parameter_specs
            )
            if is_required:
                required_sensitive.append(key)
            else:
                optional_sensitive.append(key)
        
        # Try adding required sensitive params first, then optional ones
        ordered_sensitive = required_sensitive + optional_sensitive
        
        logging.info(f"📝 Ordered sensitive access: required={required_sensitive}, optional={optional_sensitive}")
        
        for i, sensitive_key in enumerate(ordered_sensitive):
            # Add one more sensitive parameter
            current_params[sensitive_key] = high_sens_params[sensitive_key]
            accessed_count = len(low_sens_params) + i + 1
            remaining_count = len(sensitive_keys) - i - 1
            
            logging.info(f"🔐 Adding sensitive param {i+1}/{len(sensitive_keys)}: '{sensitive_key}'")
            
            try:
                partial_result = self.engine.evaluate(
                    parameters=current_params,
                    overwrite_input=overwrite_input,
                    sources=sources,
                    calculation_date=calculation_date,
                    requested_output=requested_output,
                    approved=approved
                )
                
                # Check if we can determine result with current subset
                if self._can_determine_result_early(partial_result):
                    logging.info(f"✅ INCREMENTAL DETERMINATION: Result determined with {accessed_count}/{len(high_sens_params)+len(low_sens_params)} parameters!")
                    remaining_sensitive = [k for k in sensitive_keys[i+1:]]
                    logging.info(f"💰 PRIVACY SAVED: Skipped {remaining_count} sensitive fields: {remaining_sensitive}")
                    
                    self.fields_accessed = accessed_count
                    self.fields_skipped = remaining_count
                    return partial_result
                    
            except Exception as e:
                logging.debug(f"Incremental execution failed with {accessed_count} params: {e}")
                continue
        
        # Could not determine result incrementally
        logging.info("🤷 Cannot determine result incrementally - need all parameters")
        return None
    
    def _classify_actions(self) -> Dict[str, SensitivityLevel]:
        """Classify each action by its sensitivity level"""
        action_sensitivity = {}
        
        for action in self.engine.actions:
            output_name = action.get("output", "")
            
            # Check if action depends on sensitive fields
            dependencies = self.engine.analyze_dependencies(action)
            max_sensitivity = SensitivityLevel.LOW
            
            for dep in dependencies:
                if self._is_sensitive_field(dep):
                    max_sensitivity = SensitivityLevel.HIGH
                    break
            
            # Check if output itself is sensitive
            if self._is_sensitive_field(output_name):
                max_sensitivity = SensitivityLevel.HIGH
            
            action_sensitivity[output_name] = max_sensitivity
        
        return action_sensitivity
    
    def _is_sensitive_field(self, field_name: str) -> bool:
        """Check if field is HIGH sensitivity"""
        field_upper = field_name.upper()
        
        # Check exact matches
        if field_upper in self.high_sensitivity_fields:
            return True
        
        # Check keywords
        for keyword in self.high_sensitivity_keywords:
            if keyword in field_upper:
                return True
        
        return False
    
    def _separate_actions_by_sensitivity(self, action_sensitivity: Dict) -> tuple[List, List]:
        """Separate actions by sensitivity while preserving dependencies"""
        # Get actions in dependency order
        all_actions = self.engine.get_required_actions("", self.engine.actions)
        
        low_actions = []
        high_actions = []
        
        for action in all_actions:
            output_name = action.get("output", "")
            if action_sensitivity.get(output_name, SensitivityLevel.LOW) == SensitivityLevel.LOW:
                low_actions.append(action)
            else:
                high_actions.append(action)
        
        return low_actions, high_actions
    
    def _execute_action(self, action: Dict, context: RuleContext):
        """Execute a single action (delegate to core engine)"""
        self.engine._execute_action(action, context)
    
    def _can_terminate_early(self, context: RuleContext) -> bool:
        """Check if we can determine result early"""
        # Simple heuristics for early termination
        for key, value in context.output_values.items():
            if "eligible" in key.lower() and value is False:
                return True
            if "disqualified" in key.lower() and value is True:
                return True
            if "meets_requirements" in key.lower() and value is False:
                return True
        
        return False
    
    def _extract_result(self, context: RuleContext) -> Dict:
        """Extract final result from execution context"""
        return {
            "parameters": dict(context.parameters),
            "output": dict(context.output_values),
            "eliminated": False
        }
    
    def _load_config(self):
        """Load elimination rules and sensitivity configuration"""
        try:
            with open(self.config_path, 'r', encoding='utf-8') as f:
                config = yaml.safe_load(f)
            
            # Load sensitivity configuration
            sensitivity = config.get("sensitivity", {})
            self.high_sensitivity_fields = set(sensitivity.get("high_sensitivity_fields", []))
            self.high_sensitivity_keywords = set(sensitivity.get("high_sensitivity_keywords", []))
            
            # Load elimination rules
            self.elimination_rules = []
            rules = config.get("elimination_rules", {})
            for category, rule_list in rules.items():
                self.elimination_rules.extend(rule_list)
            
            logging.info(f"Loaded {len(self.elimination_rules)} elimination rules")
            
        except Exception as e:
            logging.error(f"Failed to load minimization config: {e}")
            self.high_sensitivity_fields = set()
            self.high_sensitivity_keywords = set()
            self.elimination_rules = []
    
    def reset_metrics(self):
        """Reset minimization metrics"""
        self.laws_eliminated = 0
        self.laws_evaluated = 0
        self.fields_accessed = 0
        self.fields_skipped = 0
    
    def _get_metrics(self) -> Dict:
        """Get minimization effectiveness metrics"""
        total_laws = self.laws_eliminated + self.laws_evaluated
        elimination_rate = (self.laws_eliminated / total_laws * 100) if total_laws > 0 else 0
        
        total_fields = self.fields_accessed + self.fields_skipped
        skip_rate = (self.fields_skipped / total_fields * 100) if total_fields > 0 else 0
        
        return {
            "laws_eliminated": self.laws_eliminated,
            "laws_evaluated": self.laws_evaluated,
            "elimination_rate_percent": round(elimination_rate, 1),
            "fields_accessed": self.fields_accessed,
            "fields_skipped": self.fields_skipped,
            "field_skip_rate_percent": round(skip_rate, 1)
        }
    
    # Convenience properties for compatibility
    @property
    def law(self) -> str:
        return self.engine.law
    
    @property 
    def spec(self) -> Dict:
        return self.engine.spec
    
    def get_law_sensitivity(self) -> SensitivityLevel:
        """Get overall sensitivity level of this law"""
        # Check all parameters, sources, inputs for HIGH sensitivity fields
        for param in self.spec.get("properties", {}).get("parameters", []):
            if self._is_sensitive_field(param["name"]):
                return SensitivityLevel.HIGH
        
        for source in self.spec.get("properties", {}).get("sources", []):
            if self._is_sensitive_field(source["name"]):
                return SensitivityLevel.HIGH
        
        for inp in self.spec.get("properties", {}).get("input", []):
            if self._is_sensitive_field(inp["name"]):
                return SensitivityLevel.HIGH
        
        return SensitivityLevel.LOW


# Convenience factory function
def create_minimization_engine(spec: Dict[str, Any], service_provider: Any = None, 
                             config_path: Optional[str] = None) -> MinimizationEngine:
    """
    Factory function to create a data minimization engine.
    
    Args:
        spec: Law specification dictionary
        service_provider: Optional service provider
        config_path: Optional path to elimination rules YAML
        
    Returns:
        MinimizationEngine instance
    """
    return MinimizationEngine(spec, service_provider, config_path)