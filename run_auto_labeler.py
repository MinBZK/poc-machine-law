#!/usr/bin/env python3
"""
Practical script to run rule-based auto-labeling on the entire law codebase.

This script will:
1. Discover all data fields in the law directory
2. Apply rule-based automatic sensitivity labeling
3. Generate comprehensive reports
4. Show fields that need manual review
"""

import sys
import os
import argparse
import logging
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from machine.auto_labeler import RuleBasedAutoLabeler

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def main():
    parser = argparse.ArgumentParser(description='Auto-label data sensitivity for all law fields')
    parser.add_argument('--law-dir', default='law', help='Directory containing law YAML files')
    parser.add_argument('--output', default='auto_labeling_results.csv', help='Output CSV file')
    parser.add_argument('--report', default='auto_labeling_report.json', help='Output report file')
    parser.add_argument('--demo', action='store_true', help='Run demo with sample fields only')
    
    args = parser.parse_args()
    
    # Initialize the auto-labeler
    labeler = RuleBasedAutoLabeler()
    
    if args.demo:
        print("🔍 Running Auto-Labeling Demo")
        print("=" * 50)
        
        # Demo with sample fields
        demo_fields = [
            {'field_name': 'BSN', 'field_type': 'string', 'description': 'Burgerservicenummer van de persoon'},
            {'field_name': 'PARTNER_BSN', 'field_type': 'string', 'description': 'BSN van de partner'},
            {'field_name': 'GEBOORTEDATUM', 'field_type': 'date', 'description': 'Geboortedatum van de persoon'},
            {'field_name': 'LEEFTIJD', 'field_type': 'number', 'description': 'Leeftijd van de persoon'},
            {'field_name': 'HEEFT_PARTNER', 'field_type': 'boolean', 'description': 'Geeft aan of persoon een partner heeft'},
            {'field_name': 'INKOMEN', 'field_type': 'amount', 'description': 'Totaal inkomen voor belasting'},
            {'field_name': 'INKOMEN_BRACKET', 'field_type': 'string', 'description': 'Inkomensklasse van de persoon'},
            {'field_name': 'WOONPLAATS', 'field_type': 'string', 'description': 'Woonplaats van de persoon'},
            {'field_name': 'VERBLIJFSADRES', 'field_type': 'string', 'description': 'Volledig verblijfsadres'},
            {'field_name': 'IS_VERZEKERD', 'field_type': 'boolean', 'description': 'Verzekeringsstatus'},
            {'field_name': 'CALCULATION_DATE', 'field_type': 'date', 'description': 'Datum van berekening'},
            {'field_name': 'HUISHOUDGROOTTE', 'field_type': 'number', 'description': 'Aantal personen in huishouden'},
            {'field_name': 'UNKNOWN_MYSTERY_FIELD', 'field_type': 'string', 'description': 'Some field we dont know about'}
        ]
        
        print(f"\n📋 Labeling {len(demo_fields)} demo fields...")
        
        for field in demo_fields:
            result = labeler.label_field(
                field['field_name'], 
                field['field_type'], 
                field['description']
            )
            
            # Color coding for terminal output
            sensitivity = result['predicted_sensitivity']
            confidence = result['confidence']
            
            if sensitivity == 5:
                color = '\033[91m'  # Red
            elif sensitivity == 4:
                color = '\033[93m'  # Yellow
            elif sensitivity == 3:
                color = '\033[94m'  # Blue
            elif sensitivity == 2:
                color = '\033[92m'  # Green
            else:
                color = '\033[37m'  # White
            
            reset_color = '\033[0m'
            
            confidence_indicator = "🔴" if confidence < 0.7 else "🟡" if confidence < 0.85 else "🟢"
            
            print(f"\n{color}📊 {field['field_name']:<25}{reset_color}")
            print(f"   Sensitivity: Level {sensitivity} ({'⭐' * sensitivity})")
            print(f"   Confidence:  {confidence:.3f} {confidence_indicator}")
            print(f"   Rule:        {result['rule_used']}")
            print(f"   Review:      {'⚠️  YES' if result['needs_manual_review'] else '✅ NO'}")
            print(f"   Reason:      {result['reasoning']}")
        
        # Show statistics
        print(f"\n📈 Demo Statistics:")
        stats = labeler.get_statistics()
        for key, value in stats.items():
            if isinstance(value, float):
                print(f"   {key}: {value:.3f}")
            else:
                print(f"   {key}: {value}")
        
    else:
        print("🏷️  Auto-Labeling All Law Fields")
        print("=" * 50)
        
        law_directory = Path(args.law_dir)
        if not law_directory.exists():
            print(f"❌ Error: Law directory '{law_directory}' not found!")
            return 1
        
        print(f"📂 Scanning law directory: {law_directory}")
        
        # Discover and label all fields
        try:
            results_df = labeler.discover_and_label_all_fields(str(law_directory))
            
            print(f"\n✅ Successfully labeled {len(results_df)} fields!")
            
            # Save results
            results_df.to_csv(args.output, index=False)
            print(f"💾 Results saved to: {args.output}")
            
            # Generate report
            report = labeler.generate_report(results_df, args.report)
            print(f"📊 Report saved to: {args.report}")
            
            # Show summary
            print(f"\n📈 Summary:")
            summary = report['summary']
            print(f"   Total fields processed: {summary['total_fields']}")
            print(f"   Auto-labeled successfully: {summary['auto_labeled_successfully']}")
            print(f"   Need manual review: {summary['needs_manual_review']}")
            print(f"   Auto-labeling success rate: {(summary['auto_labeled_successfully'] / summary['total_fields'] * 100):.1f}%")
            
            print(f"\n🎯 Sensitivity Distribution:")
            for level, count in summary['sensitivity_distribution'].items():
                stars = '⭐' * int(level)
                print(f"   Level {level} {stars:<5}: {count:>4} fields")
            
            print(f"\n🔍 Confidence Levels:")
            for level, count in summary['confidence_distribution'].items():
                print(f"   {level:<15}: {count:>4} fields")
            
            # Show fields needing review
            needs_review = results_df[results_df['needs_manual_review'] == True]
            if len(needs_review) > 0:
                print(f"\n⚠️  Fields Needing Manual Review ({len(needs_review)}):")
                print("-" * 80)
                
                for _, field in needs_review.head(10).iterrows():  # Show first 10
                    print(f"   {field['field_name']:<30} | Level {field['predicted_sensitivity']} | {field['confidence']:.3f} | {field['service']}")
                
                if len(needs_review) > 10:
                    print(f"   ... and {len(needs_review) - 10} more (see {args.output} for full list)")
                
                print(f"\n💡 Tip: Focus on fields with confidence < 0.7 for manual review")
            
            # Show top rule usage
            print(f"\n🏆 Most Used Rules:")
            rule_usage = report['rule_usage']
            top_rules = sorted(rule_usage.items(), key=lambda x: x[1], reverse=True)[:5]
            for rule_name, count in top_rules:
                print(f"   {rule_name:<25}: {count:>3} times")
            
        except Exception as e:
            print(f"❌ Error during auto-labeling: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    print(f"\n✨ Auto-labeling completed successfully!")
    return 0

if __name__ == "__main__":
    sys.exit(main())