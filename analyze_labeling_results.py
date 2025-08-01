#!/usr/bin/env python3
"""
Analyze the auto-labeling results and provide actionable insights.
"""

import pandas as pd
import sys
from collections import Counter

def main():
    if len(sys.argv) > 1:
        csv_file = sys.argv[1]
    else:
        csv_file = 'law_fields_labeled.csv'
    
    try:
        df = pd.read_csv(csv_file)
    except FileNotFoundError:
        print(f"❌ Error: File '{csv_file}' not found!")
        print("Run the auto-labeler first: python run_auto_labeler.py")
        return 1
    
    print("🔍 AUTO-LABELING ANALYSIS REPORT")
    print("=" * 50)
    
    total_fields = len(df)
    auto_labeled = len(df[df['needs_manual_review'] == False])
    needs_review = len(df[df['needs_manual_review'] == True])
    
    print(f"📊 OVERALL PERFORMANCE:")
    print(f"   Total fields discovered:    {total_fields}")
    print(f"   Successfully auto-labeled:  {auto_labeled} ({auto_labeled/total_fields*100:.1f}%)")
    print(f"   Need manual review:         {needs_review} ({needs_review/total_fields*100:.1f}%)")
    
    print(f"\n🎯 SENSITIVITY DISTRIBUTION:")
    sensitivity_dist = df['predicted_sensitivity'].value_counts().sort_index()
    for level, count in sensitivity_dist.items():
        percentage = count / total_fields * 100
        stars = '⭐' * level
        if level == 5:
            print(f"   Level {level} {stars} (Identifiers):    {count:>3} fields ({percentage:>5.1f}%)")
        elif level == 4:
            print(f"   Level {level} {stars} (Personal Exact): {count:>3} fields ({percentage:>5.1f}%)")
        elif level == 3:
            print(f"   Level {level} {stars} (Ranges):         {count:>3} fields ({percentage:>5.1f}%)")
        elif level == 2:
            print(f"   Level {level} {stars} (Demographics):   {count:>3} fields ({percentage:>5.1f}%)")
        else:
            print(f"   Level {level} {stars} (Administrative): {count:>3} fields ({percentage:>5.1f}%)")
    
    print(f"\n💯 CONFIDENCE ANALYSIS:")
    high_conf = len(df[df['confidence'] >= 0.85])
    med_conf = len(df[(df['confidence'] >= 0.7) & (df['confidence'] < 0.85)])
    low_conf = len(df[df['confidence'] < 0.7])
    
    print(f"   High confidence (≥0.85):    {high_conf:>3} fields ({high_conf/total_fields*100:>5.1f}%) ✅")
    print(f"   Medium confidence (0.7-0.85): {med_conf:>3} fields ({med_conf/total_fields*100:>5.1f}%) ⚠️")
    print(f"   Low confidence (<0.7):      {low_conf:>3} fields ({low_conf/total_fields*100:>5.1f}%) ❌")
    
    print(f"\n🏢 SERVICES BREAKDOWN:")
    service_breakdown = df.groupby('service').agg({
        'field_name': 'count',
        'needs_manual_review': lambda x: (x == False).sum(),
        'confidence': 'mean'
    }).round(3)
    service_breakdown.columns = ['Total Fields', 'Auto-Labeled', 'Avg Confidence']
    service_breakdown['Success Rate %'] = (service_breakdown['Auto-Labeled'] / service_breakdown['Total Fields'] * 100).round(1)
    service_breakdown = service_breakdown.sort_values('Total Fields', ascending=False)
    
    print(f"   {'Service':<20} | {'Fields':<6} | {'Auto-OK':<7} | {'Success%':<8} | {'Avg Conf'}")
    print("   " + "-" * 60)
    for service, row in service_breakdown.head(10).iterrows():
        print(f"   {service:<20} | {row['Total Fields']:>6} | {row['Auto-Labeled']:>7} | {row['Success Rate %']:>7.1f}% | {row['Avg Confidence']:>8.3f}")
    
    print(f"\n🔧 MOST USED RULES:")
    rule_usage = df['rule_used'].value_counts().head(8) 
    for rule, count in rule_usage.items():
        print(f"   {rule:<30}: {count:>3} times")
    
    print(f"\n⚠️  PRIORITY MANUAL REVIEWS:")
    print("   Fields with low confidence that need immediate attention:")
    print(f"   {'Field Name':<30} | {'Service':<15} | {'Level'} | {'Conf'}")
    print("   " + "-" * 60)
    
    # Focus on important high-sensitivity fields with low confidence
    priority_review = df[
        (df['needs_manual_review'] == True) & 
        (df['predicted_sensitivity'] >= 4) &
        (df['confidence'] < 0.6)
    ].sort_values('confidence').head(10)
    
    for _, row in priority_review.iterrows():
        print(f"   {row['field_name']:<30} | {row['service']:<15} | {row['predicted_sensitivity']}     | {row['confidence']:.3f}")
    
    print(f"\n✅ HIGH-CONFIDENCE SUCCESSES:")
    print("   Fields successfully auto-labeled with high confidence:")
    print(f"   {'Field Name':<30} | {'Service':<15} | {'Level'} | {'Conf'}")
    print("   " + "-" * 60)
    
    successes = df[df['confidence'] >= 0.9].sort_values('confidence', ascending=False).head(10)
    for _, row in successes.iterrows():
        print(f"   {row['field_name']:<30} | {row['service']:<15} | {row['predicted_sensitivity']}     | {row['confidence']:.3f}")
    
    print(f"\n📈 RECOMMENDATIONS:")
    
    if auto_labeled < total_fields * 0.3:
        print("   🔴 LOW AUTO-LABELING RATE:")
        print("      - Consider expanding rule patterns for common Dutch government terms")
        print("      - Add domain-specific rules for law/policy terminology")
        print("      - Review false negatives in high-confidence manual review cases")
    
    if high_conf < total_fields * 0.5:
        print("   🟡 LOW CONFIDENCE SCORES:")
        print("      - Many fields have ambiguous names that need better pattern matching")
        print("      - Consider adding description-based classification rules")
        print("      - Review field naming conventions across services")
    
    high_sens_fields = len(df[df['predicted_sensitivity'] >= 4])
    print(f"   📊 DATA SENSITIVITY INSIGHTS:")
    print(f"      - {high_sens_fields} fields ({high_sens_fields/total_fields*100:.1f}%) are high sensitivity (Level 4-5)")
    print(f"      - Focus manual review efforts on these high-sensitivity fields first")
    print(f"      - Consider data minimization strategies for laws using many Level 5 fields")
    
    print(f"\n💡 NEXT STEPS:")
    print("   1. Review the priority manual review cases above")
    print("   2. Validate high-confidence auto-labeled fields (spot check)")
    print("   3. Update law YAML files with confirmed sensitivity levels")
    print("   4. Expand auto-labeling rules based on manual review findings")
    print("   5. Re-run auto-labeler on remaining unlabeled fields")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())