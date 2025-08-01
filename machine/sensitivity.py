"""
Data sensitivity classification and scoring system for data minimization optimization.

This module implements a formal 1-5 scale sensitivity classification system where:
- Level 1: Administrative metadata, dates, boolean flags
- Level 2: Age ranges, general demographics, household size categories
- Level 3: Financial brackets/ranges, employment status, location data
- Level 4: Exact financial amounts, detailed personal attributes, family relationships
- Level 5: BSN, exact income, assets, medical status, detailed addresses
"""

from typing import Dict, List, Tuple, Optional, Set
from enum import IntEnum
import logging


class SensitivityLevel(IntEnum):
    """Data sensitivity levels from 1 (lowest) to 5 (highest)"""

    ADMINISTRATIVE = 1  # Dates, IDs, boolean flags
    DEMOGRAPHIC = 2  # Age ranges, general categories
    RANGES = 3  # Financial brackets, location areas
    PERSONAL_EXACT = 4  # Exact amounts, detailed attributes
    IDENTIFIERS = 5  # BSN, addresses, medical data


class DataSensitivityClassifier:
    """Classifies data fields based on sensitivity patterns and predefined rules"""

    # Predefined sensitivity mappings for common fields
    FIELD_SENSITIVITY_MAP = {
        # Level 5 - Highest sensitivity (Identifiers, exact personal data)
        "BSN": SensitivityLevel.IDENTIFIERS,
        "BURGERSERVICENUMMER": SensitivityLevel.IDENTIFIERS,
        "VERBLIJFSADRES": SensitivityLevel.IDENTIFIERS,
        "POSTADRES": SensitivityLevel.IDENTIFIERS,
        "EXACT_INKOMEN": SensitivityLevel.IDENTIFIERS,
        "VERMOGEN": SensitivityLevel.IDENTIFIERS,
        "PARTNER_BSN": SensitivityLevel.IDENTIFIERS,
        # Level 4 - High sensitivity (Exact personal attributes)
        "GEBOORTEDATUM": SensitivityLevel.PERSONAL_EXACT,
        "PARTNER_GEBOORTEDATUM": SensitivityLevel.PERSONAL_EXACT,
        "INKOMEN": SensitivityLevel.PERSONAL_EXACT,
        "PARTNER_INKOMEN": SensitivityLevel.PERSONAL_EXACT,
        "TOETSINGSINKOMEN": SensitivityLevel.PERSONAL_EXACT,
        "GEZINSINKOMEN": SensitivityLevel.PERSONAL_EXACT,
        "BEDRIJFSINKOMEN": SensitivityLevel.PERSONAL_EXACT,
        # Level 3 - Medium sensitivity (Ranges, location data)
        "WOONPLAATS": SensitivityLevel.RANGES,
        "INKOMEN_BRACKET": SensitivityLevel.RANGES,
        "VERMOGEN_BRACKET": SensitivityLevel.RANGES,
        "WOONSITUATIE": SensitivityLevel.RANGES,
        "VERBLIJFSLAND": SensitivityLevel.RANGES,
        "NATIONALITEIT": SensitivityLevel.RANGES,
        # Level 2 - Low sensitivity (Demographics, general categories)
        "LEEFTIJD": SensitivityLevel.DEMOGRAPHIC,
        "PARTNER_LEEFTIJD": SensitivityLevel.DEMOGRAPHIC,
        "LEEFTIJD_BRACKET": SensitivityLevel.DEMOGRAPHIC,
        "HUISHOUDGROOTTE": SensitivityLevel.DEMOGRAPHIC,
        "AANTAL_KINDEREN": SensitivityLevel.DEMOGRAPHIC,
        "PARTNERTYPE": SensitivityLevel.DEMOGRAPHIC,
        # Level 1 - Lowest sensitivity (Administrative, boolean flags)
        "HEEFT_PARTNER": SensitivityLevel.ADMINISTRATIVE,
        "IS_VERZEKERD": SensitivityLevel.ADMINISTRATIVE,
        "IS_GERECHTIGD": SensitivityLevel.ADMINISTRATIVE,
        "CALCULATION_DATE": SensitivityLevel.ADMINISTRATIVE,
        "VALID_FROM": SensitivityLevel.ADMINISTRATIVE,
        "REFERENCE_DATE": SensitivityLevel.ADMINISTRATIVE,
    }

    # Pattern-based classification rules
    SENSITIVITY_PATTERNS = {
        # Identifiers pattern
        ("BSN", "NUMMER", "ID", "ADRES"): SensitivityLevel.IDENTIFIERS,
        # Exact amounts pattern
        ("BEDRAG", "INKOMEN", "VERMOGEN", "KOSTEN"): SensitivityLevel.PERSONAL_EXACT,
        # Range/bracket pattern
        ("BRACKET", "RANGE", "CATEGORIE"): SensitivityLevel.RANGES,
        # Demographic pattern
        ("LEEFTIJD", "AANTAL", "GROOTTE"): SensitivityLevel.DEMOGRAPHIC,
        # Administrative pattern
        ("HEEFT_", "IS_", "DATE", "FLAG"): SensitivityLevel.ADMINISTRATIVE,
    }

    @classmethod
    def classify_field(cls, field_name: str, field_type: str = None, description: str = None) -> SensitivityLevel:
        """
        Classify a data field's sensitivity level based on name, type, and description.

        Args:
            field_name: The name of the field (e.g., 'BSN', 'LEEFTIJD')
            field_type: The data type (e.g., 'string', 'number', 'date')
            description: Human-readable description of the field

        Returns:
            SensitivityLevel enum value (1-5)
        """
        field_upper = field_name.upper()

        # Check exact matches first
        if field_upper in cls.FIELD_SENSITIVITY_MAP:
            return cls.FIELD_SENSITIVITY_MAP[field_upper]

        # Check pattern matches
        for patterns, sensitivity in cls.SENSITIVITY_PATTERNS.items():
            if any(pattern in field_upper for pattern in patterns):
                return sensitivity

        # Type-based fallback classification
        if field_type:
            if field_type == "date" and "GEBOORTE" in field_upper:
                return SensitivityLevel.PERSONAL_EXACT
            elif field_type == "boolean":
                return SensitivityLevel.ADMINISTRATIVE
            elif field_type in ("amount", "number") and any(
                keyword in field_upper for keyword in ["BEDRAG", "INKOMEN", "VERMOGEN"]
            ):
                return SensitivityLevel.PERSONAL_EXACT

        # Default to medium sensitivity if unable to classify
        logging.warning(f"Unable to classify field '{field_name}', defaulting to RANGES")
        return SensitivityLevel.RANGES

    @classmethod
    def get_law_sensitivity_score(cls, law_data: Dict) -> Tuple[int, float, int]:
        """
        Calculate sensitivity score for a law based on its data requirements.

        Args:
            law_data: Dictionary containing law definition with parameters/sources/inputs

        Returns:
            Tuple of (max_sensitivity, avg_sensitivity, total_fields) for sorting
        """
        sensitivities = []

        # Analyze parameters
        for param in law_data.get("properties", {}).get("parameters", []):
            sensitivity = param.get("data_sensitivity")
            if sensitivity is None:
                # Auto-classify if not specified
                sensitivity = cls.classify_field(param["name"], param.get("type"), param.get("description")).value
            sensitivities.append(sensitivity)

        # Analyze sources
        for source in law_data.get("properties", {}).get("sources", []):
            sensitivity = source.get("data_sensitivity")
            if sensitivity is None:
                sensitivity = cls.classify_field(source["name"], source.get("type"), source.get("description")).value
            sensitivities.append(sensitivity)

        # Analyze inputs
        for inp in law_data.get("properties", {}).get("input", []):
            sensitivity = inp.get("data_sensitivity")
            if sensitivity is None:
                sensitivity = cls.classify_field(inp["name"], inp.get("type"), inp.get("description")).value
            sensitivities.append(sensitivity)

        if not sensitivities:
            return (1, 1.0, 0)  # No sensitive data

        max_sensitivity = max(sensitivities)
        avg_sensitivity = sum(sensitivities) / len(sensitivities)
        total_fields = len(sensitivities)

        return (max_sensitivity, avg_sensitivity, total_fields)

    @classmethod
    def can_eliminate_early(cls, law_data: Dict, available_data: Dict) -> bool:
        """
        Determine if a law can be eliminated early based on minimal available data.

        Args:
            law_data: Law definition dictionary
            available_data: Minimal data available for early elimination

        Returns:
            True if law can be eliminated without additional data collection
        """
        data_min = law_data.get("data_minimization", {})

        # Check age requirements
        if "age" in available_data or "age_bracket" in available_data:
            min_age = data_min.get("min_age")
            max_age = data_min.get("max_age")

            if min_age is not None:
                age = available_data.get("age") or cls._get_age_from_bracket(available_data.get("age_bracket"))
                if age is not None and age < min_age:
                    return True

            if max_age is not None:
                age = available_data.get("age") or cls._get_age_from_bracket(available_data.get("age_bracket"))
                if age is not None and age > max_age:
                    return True

        # Check partner requirements
        if data_min.get("requires_partner") and not available_data.get("has_partner"):
            return True

        # Check children requirements
        if data_min.get("requires_children") and not available_data.get("has_children"):
            return True

        return False

    @staticmethod
    def _get_age_from_bracket(age_bracket: str) -> Optional[int]:
        """Convert age bracket to representative age for elimination logic"""
        if age_bracket == "0-17":
            return 16
        elif age_bracket == "18-66":
            return 35
        elif age_bracket == "67+":
            return 70
        return None


class DataMinimizationMetrics:
    """Track and report data minimization effectiveness"""

    def __init__(self):
        self.reset()

    def reset(self):
        """Reset all metrics"""
        self.laws_eliminated_early = 0
        self.laws_processed = 0
        self.max_sensitivity_accessed = 0
        self.total_sensitivity_score = 0
        self.services_called = set()
        self.fields_accessed = []

    def record_early_elimination(self, law_name: str):
        """Record that a law was eliminated early"""
        self.laws_eliminated_early += 1
        logging.info(f"Early elimination: {law_name}")

    def record_law_processing(self, law_name: str, sensitivity_score: Tuple[int, float, int]):
        """Record processing of a law with its sensitivity score"""
        self.laws_processed += 1
        max_sens, avg_sens, field_count = sensitivity_score
        self.max_sensitivity_accessed = max(self.max_sensitivity_accessed, max_sens)
        self.total_sensitivity_score += avg_sens
        logging.info(f"Processed law: {law_name}, sensitivity: max={max_sens}, avg={avg_sens:.2f}")

    def record_field_access(self, service: str, field: str, sensitivity: int):
        """Record access to a specific field"""
        self.services_called.add(service)
        self.fields_accessed.append({"service": service, "field": field, "sensitivity": sensitivity})
        self.max_sensitivity_accessed = max(self.max_sensitivity_accessed, sensitivity)

    def get_summary(self) -> Dict:
        """Get summary of data minimization metrics"""
        total_laws = self.laws_eliminated_early + self.laws_processed
        elimination_rate = (self.laws_eliminated_early / total_laws * 100) if total_laws > 0 else 0
        avg_sensitivity = (self.total_sensitivity_score / self.laws_processed) if self.laws_processed > 0 else 0

        return {
            "total_laws_considered": total_laws,
            "laws_eliminated_early": self.laws_eliminated_early,
            "laws_processed": self.laws_processed,
            "early_elimination_rate_percent": round(elimination_rate, 2),
            "max_sensitivity_accessed": self.max_sensitivity_accessed,
            "average_sensitivity_score": round(avg_sensitivity, 2),
            "services_called_count": len(self.services_called),
            "services_called": list(self.services_called),
            "total_fields_accessed": len(self.fields_accessed),
            "sensitivity_distribution": self._get_sensitivity_distribution(),
        }

    def _get_sensitivity_distribution(self) -> Dict[int, int]:
        """Get distribution of field accesses by sensitivity level"""
        distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
        for field in self.fields_accessed:
            distribution[field["sensitivity"]] += 1
        return distribution
