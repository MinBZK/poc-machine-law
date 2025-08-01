"""
Rule-based automatic data sensitivity labeling system.

This module provides intelligent automatic labeling of data fields based on
comprehensive rules that analyze field names, types, and descriptions to assign
appropriate sensitivity levels (1-5).
"""

import re
import yaml
import logging
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass
from collections import defaultdict, Counter
import pandas as pd

logger = logging.getLogger(__name__)


@dataclass
class LabelingRule:
    """A rule for automatic sensitivity labeling"""
    name: str
    sensitivity_level: int
    confidence: float
    patterns: Dict[str, List[str]]
    conditions: Dict[str, any]
    description: str


class RuleBasedAutoLabeler:
    """Rule-based automatic sensitivity labeling system"""
    
    def __init__(self):
        self.rules = self._initialize_comprehensive_rules()
        self.statistics = {
            'total_processed': 0,
            'auto_labeled': 0,
            'high_confidence': 0,
            'needs_review': 0,
            'rule_usage': Counter()
        }
        
    def _initialize_comprehensive_rules(self) -> List[LabelingRule]:
        """Initialize comprehensive rule set for Dutch government data"""
        
        return [
            # ===== LEVEL 5 - IDENTIFIERS (Highest Sensitivity) =====
            LabelingRule(
                name="BSN_identifiers",
                sensitivity_level=5,
                confidence=0.99,
                patterns={
                    'exact_match': ['BSN', 'BURGERSERVICENUMMER'],
                    'contains': ['BSN_', '_BSN'],
                    'starts_with': ['BSN_'],
                    'ends_with': ['_BSN']
                },
                conditions={'type': ['string']},
                description="Burgerservicenummer - highest sensitivity identifier"
            ),
            
            LabelingRule(
                name="full_addresses",
                sensitivity_level=5,
                confidence=0.95,
                patterns={
                    'exact_match': ['VERBLIJFSADRES', 'POSTADRES', 'WOONADRES', 'VOLLEDIG_ADRES'],
                    'contains': ['ADRES', 'ADDRESS', 'STRAAT', 'HUISNUMMER'],
                    'ends_with': ['ADRES', 'ADDRESS']
                },
                conditions={},
                description="Full address information"
            ),
            
            LabelingRule(
                name="exact_financial_amounts",
                sensitivity_level=5,
                confidence=0.90,
                patterns={
                    'contains': ['EXACT_INKOMEN', 'PRECIEZE_', 'TOTAAL_VERMOGEN'],
                    'regex': [r'.*INKOMEN(?!.*BRACKET).*', r'.*VERMOGEN(?!.*RANGE).*']
                },
                conditions={'type': ['amount', 'number']},
                description="Exact financial amounts without aggregation"
            ),
            
            LabelingRule(
                name="medical_identifiers", 
                sensitivity_level=5,
                confidence=0.95,
                patterns={
                    'contains': ['ZORGVERZEKERINGS', 'PATIENT_ID', 'MEDISCH_DOSSIER'],
                    'exact_match': ['ZORGVERZEKERINGSNUMMER', 'BSN_ZORG']
                },
                conditions={},
                description="Medical and healthcare identifiers"
            ),
            
            # ===== LEVEL 4 - PERSONAL EXACT DATA (High Sensitivity) =====
            LabelingRule(
                name="birth_dates",
                sensitivity_level=4,
                confidence=0.95,
                patterns={
                    'exact_match': ['GEBOORTEDATUM', 'BIRTH_DATE'],
                    'contains': ['GEBOORTEDATUM', 'BIRTH_DATE', 'GEBOREN_OP'],
                    'ends_with': ['GEBOORTEDATUM']
                },
                conditions={'type': ['date']},
                description="Exact birth dates"
            ),
            
            LabelingRule(
                name="detailed_income",
                sensitivity_level=4,
                confidence=0.85,
                patterns={
                    'contains': ['INKOMEN', 'SALARIS', 'LOON', 'UITKERING', 'TOETSINGSINKOMEN'],
                    'starts_with': ['INKOMEN_', 'SALARIS_', 'BRUTO_', 'NETTO_'],
                    'regex': [r'.*BOX[123].*', r'.*INKOMEN.*(?!BRACKET|RANGE)']
                },
                conditions={'type': ['amount', 'number']},
                description="Detailed income information"
            ),
            
            LabelingRule(
                name="partner_personal_data",
                sensitivity_level=4,
                confidence=0.88,
                patterns={
                    'starts_with': ['PARTNER_'],
                    'contains': ['PARTNER_BSN', 'PARTNER_INKOMEN', 'PARTNER_GEBOORTEDATUM'],
                    'regex': [r'PARTNER.*(?:BSN|INKOMEN|GEBOORTEDATUM)']
                },
                conditions={},
                description="Detailed partner information"
            ),
            
            LabelingRule(
                name="detailed_assets",
                sensitivity_level=4,
                confidence=0.85,
                patterns={
                    'contains': ['VERMOGEN', 'SPAARGELD', 'BELEGGINGEN', 'ONROEREND_GOED', 'SCHULDEN'],
                    'starts_with': ['VERMOGEN_', 'BEZIT_'],
                    'regex': [r'BOX[23].*']
                },
                conditions={'type': ['amount', 'number']},
                description="Detailed asset and wealth information"
            ),
            
            # ===== LEVEL 3 - RANGES/CATEGORIES (Medium Sensitivity) =====
            LabelingRule(
                name="income_brackets",
                sensitivity_level=3,
                confidence=0.90,
                patterns={
                    'contains': ['BRACKET', 'RANGE', 'CATEGORIE', 'KLASSE'],
                    'regex': [r'.*INKOMEN.*(BRACKET|RANGE|CATEGORIE).*']
                },
                conditions={},
                description="Income ranges and brackets"
            ),
            
            LabelingRule(
                name="location_categories",
                sensitivity_level=3,
                confidence=0.85,
                patterns={
                    'exact_match': ['WOONPLAATS', 'GEMEENTE', 'PROVINCIE', 'REGIO'],
                    'contains': ['VERBLIJFSLAND', 'NATIONALITEIT', 'HERKOMSTLAND'],
                    'ends_with': ['PLAATS', 'LAND']
                },
                conditions={},
                description="Location and geographic categories"
            ),
            
            LabelingRule(
                name="work_categories",
                sensitivity_level=3,
                confidence=0.80,
                patterns={
                    'contains': ['BEROEP', 'SECTOR', 'BEDRIJFSTAK', 'WERKGEVER'],
                    'exact_match': ['ARBEIDSSTATUS', 'WERKSTATUS', 'DIENSTVERBAND']
                },
                conditions={},
                description="Employment and work categorization"
            ),
            
            LabelingRule(
                name="housing_situation",
                sensitivity_level=3,
                confidence=0.80,
                patterns={
                    'contains': ['WOONSITUATIE', 'HUURPRIJS', 'WOONKOSTEN', 'EIGENDOM'],
                    'exact_match': ['WONINGTYPE', 'HUURDER', 'EIGENAAR']
                },
                conditions={},
                description="Housing and living situation categories"
            ),
            
            # ===== LEVEL 2 - DEMOGRAPHICS (Low Sensitivity) =====
            LabelingRule(
                name="age_demographics",
                sensitivity_level=2,
                confidence=0.90,
                patterns={
                    'exact_match': ['LEEFTIJD', 'AGE', 'OUDERDOM'],
                    'contains': ['LEEFTIJD', 'PENSIOENLEEFTIJD', 'AGE_'],
                    'ends_with': ['LEEFTIJD']
                },
                conditions={'type': ['number']},
                description="Age and age-related demographics"
            ),
            
            LabelingRule(
                name="household_composition",
                sensitivity_level=2,
                confidence=0.85,
                patterns={
                    'contains': ['HUISHOUD', 'GEZIN', 'AANTAL_KINDEREN', 'KINDEREN_ONDER'],
                    'exact_match': ['HUISHOUDGROOTTE', 'GEZINSGROOTTE', 'AANTAL_PERSONEN'],
                    'starts_with': ['AANTAL_']
                },
                conditions={},
                description="Household and family composition"
            ),
            
            LabelingRule(
                name="general_categories",
                sensitivity_level=2,
                confidence=0.75,
                patterns={
                    'contains': ['GROOTTE', 'AANTAL', 'TYPE', 'SOORT', 'CATEGORIE'],
                    'regex': [r'AANTAL_[A-Z_]+', r'TYPE_[A-Z_]+']
                },
                conditions={},
                description="General demographic categories"
            ),
            
            LabelingRule(
                name="education_level",
                sensitivity_level=2,
                confidence=0.80,
                patterns={
                    'contains': ['OPLEIDING', 'DIPLOMA', 'STUDIE', 'ONDERWIJS'],
                    'exact_match': ['OPLEIDINGSNIVEAU', 'STUDENT', 'STUDIEFINANCIERING']
                },
                conditions={},
                description="Education and study information"
            ),
            
            # ===== LEVEL 1 - ADMINISTRATIVE (Lowest Sensitivity) =====
            LabelingRule(
                name="boolean_flags",
                sensitivity_level=1,
                confidence=0.95,
                patterns={
                    'starts_with': ['HEEFT_', 'IS_', 'HAS_', 'CAN_'],
                    'ends_with': ['_FLAG', '_INDICATOR'],
                    'exact_match': ['GERECHTIGD', 'ELIGIBLE', 'ACTIEF', 'GELDIG']
                },
                conditions={'type': ['boolean']},
                description="Boolean flags and indicators"
            ),
            
            LabelingRule(
                name="dates_administrative",
                sensitivity_level=1,
                confidence=0.90,
                patterns={
                    'contains': ['DATUM', 'DATE', '_ON', 'VANAF', 'TOT'],
                    'exact_match': ['CALCULATION_DATE', 'REFERENCE_DATE', 'VALID_FROM', 'GELDIG_VANAF'],
                    'ends_with': ['DATUM', 'DATE']
                },
                conditions={'type': ['date']},
                description="Administrative and reference dates"
            ),
            
            LabelingRule(
                name="identifiers_administrative",
                sensitivity_level=1,
                confidence=0.85,
                patterns={
                    'contains': ['UUID', 'REFERENCE', 'CODE', 'NUMMER'],
                    'starts_with': ['REF_', 'ID_'],
                    'ends_with': ['_ID', '_CODE', '_REF']
                },
                conditions={'type': ['string']},
                description="Administrative identifiers and codes"
            ),
            
            LabelingRule(
                name="system_metadata",
                sensitivity_level=1,
                confidence=0.90,
                patterns={
                    'contains': ['VERSION', 'VERSIE', 'STATUS', 'STATE'],
                    'exact_match': ['CREATED_AT', 'UPDATED_AT', 'PROCESSED_AT'],
                    'starts_with': ['SYSTEM_', 'META_']
                },
                conditions={},
                description="System and metadata fields"
            )
        ]
    
    def label_field(self, field_name: str, field_type: str = None, 
                   description: str = None, context: Dict = None) -> Dict:
        """Label a single field with comprehensive rule matching"""
        
        field_name_upper = field_name.upper() if field_name else ""
        description_lower = (description or "").lower()
        context = context or {}
        
        # Find all matching rules with scores
        rule_matches = []
        
        for rule in self.rules:
            match_score = self._calculate_rule_match_score(
                field_name_upper, field_type, description_lower, rule, context
            )
            
            if match_score > 0:
                rule_matches.append({
                    'rule': rule,
                    'score': match_score,
                    'confidence': rule.confidence * match_score
                })
        
        # Sort by confidence (score * rule confidence)
        rule_matches.sort(key=lambda x: x['confidence'], reverse=True)
        
        if rule_matches:
            best_match = rule_matches[0]
            rule = best_match['rule']
            confidence = best_match['confidence']
            
            # Update statistics
            self.statistics['rule_usage'][rule.name] += 1
            self.statistics['auto_labeled'] += 1
            
            if confidence >= 0.85:
                self.statistics['high_confidence'] += 1
            elif confidence < 0.7:
                self.statistics['needs_review'] += 1
            
            return {
                'field_name': field_name,
                'predicted_sensitivity': rule.sensitivity_level,
                'confidence': round(confidence, 3),
                'rule_used': rule.name,
                'rule_description': rule.description,
                'needs_manual_review': confidence < 0.7,
                'alternative_matches': [
                    {
                        'rule': m['rule'].name,
                        'sensitivity': m['rule'].sensitivity_level,
                        'confidence': round(m['confidence'], 3)
                    }
                    for m in rule_matches[1:3]  # Show top 2 alternatives
                ],
                'reasoning': self._explain_rule_match(field_name_upper, rule, best_match['score'])
            }
        else:
            # No rules matched - default to medium sensitivity with manual review
            self.statistics['needs_review'] += 1
            
            return {
                'field_name': field_name,
                'predicted_sensitivity': 3,  # Default medium sensitivity
                'confidence': 0.3,
                'rule_used': 'default_fallback',
                'rule_description': 'No rules matched - defaulted to medium sensitivity',
                'needs_manual_review': True,
                'alternative_matches': [],
                'reasoning': 'Field did not match any classification rules'
            }
    
    def _calculate_rule_match_score(self, field_name: str, field_type: str, 
                                  description: str, rule: LabelingRule, context: Dict) -> float:
        """Calculate how well a field matches a rule (0.0 to 1.0)"""
        
        score = 0.0
        max_possible_score = 0.0
        
        # Check type conditions first (if specified)
        if 'type' in rule.conditions:
            max_possible_score += 0.2
            if field_type and field_type in rule.conditions['type']:
                score += 0.2
            elif field_type and field_type not in rule.conditions['type']:
                return 0.0  # Type mismatch - rule doesn't apply
        
        # Pattern matching
        patterns = rule.patterns
        
        # Exact match (highest weight)
        if 'exact_match' in patterns:
            max_possible_score += 0.4
            if field_name in patterns['exact_match']:
                score += 0.4
        
        # Starts with patterns
        if 'starts_with' in patterns:
            max_possible_score += 0.3
            for pattern in patterns['starts_with']:
                if field_name.startswith(pattern):
                    score += 0.3
                    break
        
        # Ends with patterns  
        if 'ends_with' in patterns:
            max_possible_score += 0.3
            for pattern in patterns['ends_with']:
                if field_name.endswith(pattern):
                    score += 0.3
                    break
        
        # Contains patterns
        if 'contains' in patterns:
            max_possible_score += 0.25
            for pattern in patterns['contains']:
                if pattern in field_name:
                    score += 0.25
                    break
        
        # Regex patterns
        if 'regex' in patterns:
            max_possible_score += 0.2
            for pattern in patterns['regex']:
                if re.search(pattern, field_name):
                    score += 0.2
                    break
        
        # Description matching (bonus)
        if description and any(keyword in description for keyword in 
                             ['personal', 'identifier', 'financial', 'address', 'income']):
            score += 0.1
            max_possible_score += 0.1
        
        # Normalize score
        if max_possible_score > 0:
            return min(1.0, score / max_possible_score)
        else:
            return 0.0
    
    def _explain_rule_match(self, field_name: str, rule: LabelingRule, score: float) -> str:
        """Generate human-readable explanation for rule match"""
        
        explanations = []
        
        # Check which patterns matched
        patterns = rule.patterns
        
        if 'exact_match' in patterns and field_name in patterns['exact_match']:
            explanations.append(f"Exact match with '{field_name}'")
        
        if 'starts_with' in patterns:
            for pattern in patterns['starts_with']:
                if field_name.startswith(pattern):
                    explanations.append(f"Starts with '{pattern}'")
                    break
        
        if 'ends_with' in patterns:
            for pattern in patterns['ends_with']:
                if field_name.endswith(pattern):
                    explanations.append(f"Ends with '{pattern}'")
                    break
        
        if 'contains' in patterns:
            for pattern in patterns['contains']:
                if pattern in field_name:
                    explanations.append(f"Contains '{pattern}'")
                    break
        
        if explanations:
            return f"Matched rule '{rule.name}': " + ", ".join(explanations)
        else:
            return f"Partial match with rule '{rule.name}' (score: {score:.2f})"
    
    def label_fields_bulk(self, fields: List[Dict]) -> pd.DataFrame:
        """Label multiple fields efficiently"""
        
        results = []
        total_fields = len(fields)
        
        logger.info(f"Starting bulk labeling of {total_fields} fields")
        
        for i, field in enumerate(fields):
            # Progress tracking
            if i % 100 == 0 and i > 0:
                logger.info(f"Processed {i}/{total_fields} fields ({i/total_fields*100:.1f}%)")
            
            result = self.label_field(
                field_name=field.get('field_name'),
                field_type=field.get('field_type'),
                description=field.get('description'),
                context=field
            )
            
            # Add original field metadata
            result.update({
                'service': field.get('service'),
                'law': field.get('law'),
                'section': field.get('section'),
                'existing_sensitivity': field.get('existing_sensitivity')
            })
            
            results.append(result)
        
        self.statistics['total_processed'] = total_fields
        
        logger.info(f"Bulk labeling completed: {self.statistics}")
        
        return pd.DataFrame(results)
    
    def discover_and_label_all_fields(self, law_directory: str) -> pd.DataFrame:
        """Discover all fields in law directory and label them"""
        
        logger.info(f"Discovering fields in {law_directory}")
        
        all_fields = []
        law_files = list(Path(law_directory).rglob("*.yaml"))
        
        logger.info(f"Found {len(law_files)} law files")
        
        for file_path in law_files:
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    law_data = yaml.safe_load(f)
                
                # Extract fields from all sections
                for section in ['parameters', 'sources', 'input', 'output']:
                    section_fields = law_data.get('properties', {}).get(section, [])
                    
                    for field in section_fields:
                        all_fields.append({
                            'field_name': field.get('name'),
                            'field_type': field.get('type'),
                            'description': field.get('description'),
                            'section': section,
                            'service': law_data.get('service'),
                            'law': law_data.get('law'),
                            'law_file': str(file_path),
                            'existing_sensitivity': field.get('data_sensitivity'),
                            'citizen_relevance': field.get('citizen_relevance')
                        })
                        
            except Exception as e:
                logger.warning(f"Error processing {file_path}: {e}")
                continue
        
        logger.info(f"Discovered {len(all_fields)} fields total")
        
        # Label all discovered fields
        return self.label_fields_bulk(all_fields)
    
    def get_statistics(self) -> Dict:
        """Get labeling statistics and insights"""
        
        stats = self.statistics.copy()
        
        if stats['total_processed'] > 0:
            stats['auto_labeling_rate'] = stats['auto_labeled'] / stats['total_processed']
            stats['high_confidence_rate'] = stats['high_confidence'] / stats['total_processed']
            stats['manual_review_rate'] = stats['needs_review'] / stats['total_processed']
        
        return stats
    
    def generate_report(self, results_df: pd.DataFrame, output_file: str = None):
        """Generate comprehensive labeling report"""
        
        report = {
            'summary': {
                'total_fields': len(results_df),
                'sensitivity_distribution': results_df['predicted_sensitivity'].value_counts().to_dict(),
                'confidence_distribution': {
                    'high (≥0.85)': len(results_df[results_df['confidence'] >= 0.85]),
                    'medium (0.7-0.85)': len(results_df[(results_df['confidence'] >= 0.7) & (results_df['confidence'] < 0.85)]),
                    'low (<0.7)': len(results_df[results_df['confidence'] < 0.7])
                },
                'needs_manual_review': len(results_df[results_df['needs_manual_review'] == True]),
                'auto_labeled_successfully': len(results_df[results_df['needs_manual_review'] == False])
            },
            'rule_usage': dict(self.statistics['rule_usage']),
            'service_breakdown': results_df.groupby('service')['predicted_sensitivity'].value_counts().to_dict(),
            'fields_needing_review': results_df[results_df['needs_manual_review'] == True][
                ['field_name', 'service', 'predicted_sensitivity', 'confidence', 'reasoning']
            ].to_dict('records')
        }
        
        if output_file:
            import json
            with open(output_file, 'w') as f:
                json.dump(report, f, indent=2, default=str)
            logger.info(f"Report saved to {output_file}")
        
        return report


def main():
    """Demo/test function for auto-labeling"""
    
    # Initialize labeler
    labeler = RuleBasedAutoLabeler()
    
    # Test with sample fields
    test_fields = [
        {'field_name': 'BSN', 'field_type': 'string', 'description': 'Burgerservicenummer'},
        {'field_name': 'LEEFTIJD', 'field_type': 'number', 'description': 'Age of person'},
        {'field_name': 'HEEFT_PARTNER', 'field_type': 'boolean', 'description': 'Has partner flag'},
        {'field_name': 'TOETSINGSINKOMEN', 'field_type': 'amount', 'description': 'Income for testing'},
        {'field_name': 'WOONPLAATS', 'field_type': 'string', 'description': 'City of residence'},
        {'field_name': 'CALCULATION_DATE', 'field_type': 'date', 'description': 'Reference date'},
        {'field_name': 'UNKNOWN_FIELD', 'field_type': 'string', 'description': 'Some unknown field'}
    ]
    
    print("=== Auto-Labeling Demo ===")
    
    for field in test_fields:
        result = labeler.label_field(
            field['field_name'], 
            field['field_type'], 
            field['description']
        )
        
        print(f"\nField: {field['field_name']}")
        print(f"  Predicted Sensitivity: {result['predicted_sensitivity']}")
        print(f"  Confidence: {result['confidence']:.3f}")
        print(f"  Rule Used: {result['rule_used']}")
        print(f"  Needs Review: {result['needs_manual_review']}")
        print(f"  Reasoning: {result['reasoning']}")
    
    # Show statistics
    print(f"\n=== Statistics ===")
    stats = labeler.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")


if __name__ == "__main__":
    main()