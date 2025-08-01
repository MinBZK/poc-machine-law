"""
Early elimination filtering for data minimization optimization.

This module implements early filtering logic that can eliminate laws from consideration
using minimal data, reducing the need for sensitive data collection.
"""

from typing import Dict, List, Optional, Tuple
import logging
from datetime import datetime, date

from machine.sensitivity import DataSensitivityClassifier, DataMinimizationMetrics


class EarlyEliminationFilter:
    """Filter laws using minimal data to avoid unnecessary sensitive data collection"""

    def __init__(self, metrics: Optional[DataMinimizationMetrics] = None):
        self.metrics = metrics or DataMinimizationMetrics()
        self.classifier = DataSensitivityClassifier()

    def get_minimal_eligibility_data(self, bsn: str, calculation_date: Optional[date] = None) -> Dict:
        """
        Collect only the minimal data needed for early law elimination.

        This function collects the least sensitive data possible to enable
        early filtering of laws that definitely don't apply.

        Args:
            bsn: Burgerservicenummer (required for any data lookup)
            calculation_date: Reference date for calculations

        Returns:
            Dictionary with minimal data fields for early elimination
        """
        if calculation_date is None:
            calculation_date = date.today()

        minimal_data = {}

        try:
            # Get age bracket instead of exact age (Sensitivity Level 2 vs 4)
            age_bracket = self._get_age_bracket_from_service(bsn, calculation_date)
            if age_bracket:
                minimal_data["age_bracket"] = age_bracket
                minimal_data["age_approx"] = self._bracket_to_approx_age(age_bracket)
                self.metrics.record_field_access("RvIG", "age_bracket", 2)

            # Get simple partner flag (Sensitivity Level 1)
            has_partner = self._get_partner_flag(bsn, calculation_date)
            if has_partner is not None:
                minimal_data["has_partner"] = has_partner
                self.metrics.record_field_access("RvIG", "has_partner", 1)

            # Get residence country only (Sensitivity Level 3 vs 5 for full address)
            residence_country = self._get_residence_country(bsn, calculation_date)
            if residence_country:
                minimal_data["residence_country"] = residence_country
                self.metrics.record_field_access("RvIG", "residence_country", 3)

            # Get children flag (Sensitivity Level 1)
            has_children = self._get_children_flag(bsn, calculation_date)
            if has_children is not None:
                minimal_data["has_children"] = has_children
                self.metrics.record_field_access("RvIG", "has_children", 1)

            # Get employment status flag (Sensitivity Level 2)
            is_employed = self._get_employment_flag(bsn, calculation_date)
            if is_employed is not None:
                minimal_data["is_employed"] = is_employed
                self.metrics.record_field_access("UWV", "is_employed", 2)

            logging.info(f"Collected minimal data for BSN {bsn[:3]}***: {list(minimal_data.keys())}")

        except Exception as e:
            logging.warning(f"Error collecting minimal data for BSN {bsn[:3]}***: {e}")

        return minimal_data

    def filter_applicable_laws(self, laws: List[Dict], minimal_data: Dict) -> Tuple[List[Dict], List[str]]:
        """
        Filter laws based on minimal data, returning applicable laws and eliminated law names.

        Args:
            laws: List of law definitions to filter
            minimal_data: Minimal data collected for early elimination

        Returns:
            Tuple of (applicable_laws, eliminated_law_names)
        """
        applicable_laws = []
        eliminated_laws = []

        for law in laws:
            law_name = law.get("name", "Unknown")

            if self.classifier.can_eliminate_early(law, minimal_data):
                eliminated_laws.append(law_name)
                self.metrics.record_early_elimination(law_name)
                logging.info(f"Early elimination: {law_name}")
            else:
                applicable_laws.append(law)

        elimination_rate = len(eliminated_laws) / len(laws) * 100 if laws else 0
        logging.info(f"Early elimination filtered {len(eliminated_laws)}/{len(laws)} laws ({elimination_rate:.1f}%)")

        return applicable_laws, eliminated_laws

    def _get_age_bracket_from_service(self, bsn: str, calculation_date: date) -> Optional[str]:
        """
        Get age bracket instead of exact age to minimize sensitivity.

        Uses RvIG service but requests age bracket instead of exact birth date.
        """
        try:
            # This would call the actual RvIG service
            # For now, we simulate the logic
            birth_date = self._simulate_birth_date_lookup(bsn)
            if birth_date:
                age = (calculation_date - birth_date).days // 365
                return self._age_to_bracket(age)
        except Exception as e:
            logging.warning(f"Failed to get age bracket for BSN {bsn[:3]}***: {e}")
        return None

    def _get_partner_flag(self, bsn: str, calculation_date: date) -> Optional[bool]:
        """Get simple boolean partner flag instead of partner details"""
        try:
            # This would call the actual RvIG service for partner status only
            # For now, we simulate
            return self._simulate_partner_lookup(bsn)
        except Exception as e:
            logging.warning(f"Failed to get partner flag for BSN {bsn[:3]}***: {e}")
        return None

    def _get_residence_country(self, bsn: str, calculation_date: date) -> Optional[str]:
        """Get only country of residence, not full address"""
        try:
            # Call RvIG for country only, not full address
            return self._simulate_country_lookup(bsn)
        except Exception as e:
            logging.warning(f"Failed to get residence country for BSN {bsn[:3]}***: {e}")
        return None

    def _get_children_flag(self, bsn: str, calculation_date: date) -> Optional[bool]:
        """Get boolean flag for having children, not detailed child information"""
        try:
            # Call RvIG for children flag only
            return self._simulate_children_lookup(bsn)
        except Exception as e:
            logging.warning(f"Failed to get children flag for BSN {bsn[:3]}***: {e}")
        return None

    def _get_employment_flag(self, bsn: str, calculation_date: date) -> Optional[bool]:
        """Get boolean employment status, not detailed work information"""
        try:
            # Call UWV for employment status only
            return self._simulate_employment_lookup(bsn)
        except Exception as e:
            logging.warning(f"Failed to get employment flag for BSN {bsn[:3]}***: {e}")
        return None

    @staticmethod
    def _age_to_bracket(age: int) -> str:
        """Convert exact age to age bracket for privacy"""
        if age < 18:
            return "0-17"
        elif age < 67:
            return "18-66"
        else:
            return "67+"

    @staticmethod
    def _bracket_to_approx_age(bracket: str) -> int:
        """Convert age bracket to approximate age for filtering logic"""
        if bracket == "0-17":
            return 16
        elif bracket == "18-66":
            return 35
        elif bracket == "67+":
            return 70
        return 35  # Default

    # Simulation methods (replace with actual service calls)

    def _simulate_birth_date_lookup(self, bsn: str) -> Optional[date]:
        """Simulate birth date lookup - replace with actual RvIG call"""
        # This is just for testing - real implementation would call RvIG service
        return date(1985, 6, 15)  # Simulate a birth date

    def _simulate_partner_lookup(self, bsn: str) -> Optional[bool]:
        """Simulate partner lookup - replace with actual RvIG call"""
        # Simulate based on BSN pattern for testing
        return len(bsn) % 2 == 0

    def _simulate_country_lookup(self, bsn: str) -> Optional[str]:
        """Simulate country lookup - replace with actual RvIG call"""
        return "NL"  # Most common case

    def _simulate_children_lookup(self, bsn: str) -> Optional[bool]:
        """Simulate children lookup - replace with actual RvIG call"""
        # Simulate based on BSN pattern for testing
        return int(bsn[-1]) % 3 == 0

    def _simulate_employment_lookup(self, bsn: str) -> Optional[bool]:
        """Simulate employment lookup - replace with actual UWV call"""
        # Simulate based on BSN pattern for testing
        return int(bsn[-1]) % 2 == 1


class LawEligibilityRules:
    """Define eligibility rules for early elimination of laws"""

    # Age-based law eligibility rules
    AGE_RULES = {
        "algemene_ouderdomswet": {"min_age": 67, "description": "AOW pension starts at 67"},
        "wet_studiefinanciering": {"max_age": 30, "description": "Student finance typically under 30"},
        "wet_kinderopvang": {"max_age": 50, "description": "Childcare benefits typically for parents under 50"},
        "kinderbijslag": {"max_age": 55, "description": "Child benefits for parents typically under 55"},
        "jeugdwet": {"max_age": 18, "description": "Youth law applies only to minors"},
    }

    # Partner-dependent laws
    PARTNER_DEPENDENT_LAWS = {
        "partnertoeslag",
        "partner_pension_supplement",
        "gezamenlijk_aanslag",  # Joint tax assessment
    }

    # Child-dependent laws
    CHILD_DEPENDENT_LAWS = {
        "kinderbijslag",
        "kinderopvangtoeslag",
        "wet_kinderopvang",
        "kindgebonden_budget",
    }

    # Employment-dependent laws
    EMPLOYMENT_DEPENDENT_LAWS = {
        "werkloosheidswet",
        "ziektewet",
        "arbeidsongeschiktheidswet",
    }

    @classmethod
    def get_elimination_rules(cls, law_name: str) -> Dict:
        """Get elimination rules for a specific law"""
        rules = {}

        # Check age rules
        for law_pattern, age_rule in cls.AGE_RULES.items():
            if law_pattern in law_name.lower():
                rules.update(age_rule)
                break

        # Check dependency rules
        if any(pattern in law_name.lower() for pattern in cls.PARTNER_DEPENDENT_LAWS):
            rules["requires_partner"] = True

        if any(pattern in law_name.lower() for pattern in cls.CHILD_DEPENDENT_LAWS):
            rules["requires_children"] = True

        if any(pattern in law_name.lower() for pattern in cls.EMPLOYMENT_DEPENDENT_LAWS):
            rules["requires_employment"] = True

        return rules
