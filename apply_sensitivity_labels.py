#!/usr/bin/env python3
"""
Apply sensitivity labels to actual law YAML files in the repository.

This script takes the auto-labeling results and updates the law YAML files
with data_sensitivity fields, focusing on high-confidence results first.
"""

import sys
import os
import yaml
import pandas as pd
from pathlib import Path
import argparse
import logging
from typing import Dict, List

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)

def load_labeling_results(csv_file: str) -> pd.DataFrame:
    """Load the auto-labeling results"""
    try:
        df = pd.read_csv(csv_file)
        logging.info(f"Loaded {len(df)} labeling results from {csv_file}")
        return df
    except FileNotFoundError:
        logging.error(f"Labeling results file '{csv_file}' not found!")
        logging.error("Run the auto-labeler first: python run_auto_labeler.py")
        sys.exit(1)

def update_law_file(file_path: Path, field_updates: List[Dict]) -> bool:
    """Update a single law YAML file with sensitivity labels"""
    
    try:
        # Load the YAML file
        with open(file_path, 'r', encoding='utf-8') as f:
            law_data = yaml.safe_load(f)
        
        updated = False
        
        # Update each section that has fields
        for section in ['parameters', 'sources', 'input', 'output']:
            if section not in law_data.get('properties', {}):
                continue
                
            section_fields = law_data['properties'][section]
            
            for field in section_fields:
                field_name = field.get('name')
                if not field_name:
                    continue
                
                # Find matching update
                for update in field_updates:
                    if (update['field_name'] == field_name and 
                        update['section'] == section):
                        
                        # Only apply high-confidence labels or user-approved ones
                        if (update['confidence'] >= 0.85 or 
                            not update['needs_manual_review']):
                            
                            # Add sensitivity label
                            field['data_sensitivity'] = update['predicted_sensitivity']
                            updated = True
                            
                            logging.info(f"  Updated {field_name}: Level {update['predicted_sensitivity']} (confidence: {update['confidence']:.3f})")
        
        # Save the updated file if changes were made
        if updated:
            # Create backup first
            backup_path = file_path.with_suffix('.yaml.backup')
            if not backup_path.exists():
                import shutil
                shutil.copy2(file_path, backup_path)
                logging.debug(f"  Created backup: {backup_path}")
            
            # Write updated YAML
            with open(file_path, 'w', encoding='utf-8') as f:
                yaml.dump(law_data, f, default_flow_style=False, 
                         allow_unicode=True, sort_keys=False, indent=2)
            
            logging.info(f"✅ Updated {file_path}")
            return True
        else:
            logging.debug(f"⏭️  No updates needed for {file_path}")
            return False
            
    except Exception as e:
        logging.error(f"❌ Error updating {file_path}: {e}")
        return False

def apply_labels_to_laws(results_df: pd.DataFrame, law_directory: str, 
                        confidence_threshold: float = 0.85,
                        apply_all: bool = False) -> Dict:
    """Apply sensitivity labels to law files"""
    
    law_dir = Path(law_directory)
    if not law_dir.exists():
        logging.error(f"Law directory '{law_directory}' not found!")
        return {}
    
    # Group results by law file
    file_groups = results_df.groupby(['service', 'law'])
    
    stats = {
        'files_processed': 0,
        'files_updated': 0,
        'fields_labeled': 0,
        'high_confidence_applied': 0,
        'manual_review_skipped': 0
    }
    
    for (service, law), group in file_groups:
        # Find the corresponding YAML file
        law_files = list(law_dir.rglob(f"*{service}*.yaml"))
        matching_files = [f for f in law_files if law in str(f)]
        
        if not matching_files:
            logging.warning(f"⚠️  Could not find law file for {service}.{law}")
            continue
        
        law_file = matching_files[0]  # Take the first match
        
        # Prepare field updates
        field_updates = []
        for _, row in group.iterrows():
            should_apply = False
            
            if apply_all:
                should_apply = True
            elif row['confidence'] >= confidence_threshold:
                should_apply = True
            elif not row['needs_manual_review']:
                should_apply = True
            
            if should_apply:
                field_updates.append({
                    'field_name': row['field_name'],
                    'section': row['section'],
                    'predicted_sensitivity': row['predicted_sensitivity'],
                    'confidence': row['confidence'],
                    'needs_manual_review': row['needs_manual_review']
                })
                
                if row['confidence'] >= confidence_threshold:
                    stats['high_confidence_applied'] += 1
                else:
                    stats['manual_review_skipped'] += 1
            else:
                stats['manual_review_skipped'] += 1
        
        if field_updates:
            logging.info(f"📝 Processing {law_file} ({len(field_updates)} field updates)")
            
            stats['files_processed'] += 1
            if update_law_file(law_file, field_updates):
                stats['files_updated'] += 1
                stats['fields_labeled'] += len(field_updates)
    
    return stats

def main():
    parser = argparse.ArgumentParser(description='Apply sensitivity labels to law YAML files')
    parser.add_argument('--results', default='law_fields_labeled.csv', 
                       help='CSV file with labeling results')
    parser.add_argument('--law-dir', default='law', 
                       help='Directory containing law YAML files')
    parser.add_argument('--confidence-threshold', type=float, default=0.85,
                       help='Minimum confidence threshold for automatic application')
    parser.add_argument('--apply-all', action='store_true',
                       help='Apply all labels regardless of confidence (use with caution)')
    parser.add_argument('--dry-run', action='store_true',
                       help='Show what would be updated without making changes')
    
    args = parser.parse_args()
    
    print("🏷️  Applying Sensitivity Labels to Law Files")
    print("=" * 50)
    
    # Load labeling results
    results_df = load_labeling_results(args.results)
    
    # Show summary of what will be applied
    if args.apply_all:
        applicable = results_df
        print(f"📋 Mode: Apply ALL labels ({len(applicable)} fields)")
    else:
        applicable = results_df[
            (results_df['confidence'] >= args.confidence_threshold) |
            (results_df['needs_manual_review'] == False)
        ]
        print(f"📋 Mode: Apply high-confidence labels only (≥{args.confidence_threshold})")
        print(f"   Will apply: {len(applicable)} fields")
        print(f"   Will skip:  {len(results_df) - len(applicable)} fields (low confidence)")
    
    if args.dry_run:
        print("\n🔍 DRY RUN MODE - No files will be modified")
        
        # Show what would be updated
        print(f"\n📊 Fields that would be labeled:")
        print(f"   {'Field Name':<30} | {'Service':<15} | {'Level'} | {'Conf'} | {'File'}")
        print("   " + "-" * 80)
        
        for _, row in applicable.head(20).iterrows():
            print(f"   {row['field_name']:<30} | {row['service']:<15} | {row['predicted_sensitivity']}     | {row['confidence']:.3f} | {row.get('law_file', 'N/A')}")
        
        if len(applicable) > 20:
            print(f"   ... and {len(applicable) - 20} more fields")
        
        return 0
    
    # Apply the labels
    print(f"\n🚀 Applying sensitivity labels...")
    
    stats = apply_labels_to_laws(
        results_df=applicable,
        law_directory=args.law_dir,
        confidence_threshold=args.confidence_threshold,
        apply_all=args.apply_all
    )
    
    # Show results
    print(f"\n✅ Application Complete!")
    print(f"   Files processed:           {stats['files_processed']}")
    print(f"   Files updated:             {stats['files_updated']}")
    print(f"   Fields labeled:            {stats['fields_labeled']}")
    print(f"   High-confidence applied:   {stats['high_confidence_applied']}")
    print(f"   Manual review skipped:     {stats['manual_review_skipped']}")
    
    if stats['files_updated'] > 0:
        print(f"\n💾 Backup files created with .yaml.backup extension")
        print(f"🔍 Review the changes with: git diff")
        print(f"📝 Commit the changes when satisfied")
    
    print(f"\n💡 Next steps:")
    if not args.apply_all and stats['manual_review_skipped'] > 0:
        print(f"   - Review low-confidence fields manually")
        print(f"   - Use --apply-all flag if you want to apply all labels")
    print(f"   - Test the updated law definitions") 
    print(f"   - Run validation: ./script/validate.py")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())