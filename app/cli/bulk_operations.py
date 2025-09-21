#!/usr/bin/env python3
"""
CLI tool for bulk catalog operations (import/export).

This tool provides command-line interface for bulk importing and exporting
technology catalog data, with support for various formats and validation.
"""

import argparse
import json
import csv
import sys
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import TechEntry, EcosystemType, MaturityLevel, ReviewStatus
from app.utils.imports import require_service


class BulkOperationsCLI:
    """Command-line interface for bulk catalog operations."""
    
    def __init__(self):
        self.manager = IntelligentCatalogManager()
        
    def export_catalog(self, args) -> None:
        """Export catalog to various formats."""
        try:
            output_path = Path(args.output)
            
            # Determine format from extension if not specified
            if not args.format:
                if output_path.suffix.lower() == '.json':
                    args.format = 'json'
                elif output_path.suffix.lower() == '.csv':
                    args.format = 'csv'
                elif output_path.suffix.lower() in ['.yml', '.yaml']:
                    args.format = 'yaml'
                else:
                    print("✗ Cannot determine format from file extension. Please specify --format")
                    sys.exit(1)
            
            # Get technologies to export
            technologies = list(self.manager.technologies.values())
            
            # Apply filters
            if args.category:
                technologies = [t for t in technologies if t.category == args.category]
            
            if args.ecosystem:
                ecosystem = EcosystemType(args.ecosystem.lower())
                technologies = [t for t in technologies if t.ecosystem == ecosystem]
            
            if args.pending_only:
                technologies = [t for t in technologies if t.pending_review]
            
            if args.approved_only:
                technologies = [t for t in technologies if t.review_status == ReviewStatus.APPROVED]
            
            if not technologies:
                print("No technologies match the export criteria")
                return
            
            # Export based on format
            if args.format == 'json':
                self._export_json(technologies, output_path, args)
            elif args.format == 'csv':
                self._export_csv(technologies, output_path, args)
            elif args.format == 'yaml':
                self._export_yaml(technologies, output_path, args)
            else:
                print(f"✗ Unsupported format: {args.format}")
                sys.exit(1)
            
            print(f"✓ Exported {len(technologies)} technologies to {output_path}")
            
        except Exception as e:
            print(f"✗ Error exporting catalog: {e}")
            sys.exit(1)
    
    def _export_json(self, technologies: List[TechEntry], output_path: Path, args) -> None:
        """Export to JSON format."""
        data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_entries": len(technologies),
                "format_version": "1.0"
            },
            "technologies": {}
        }
        
        for tech in technologies:
            if args.minimal:
                # Minimal export with only essential fields
                data["technologies"][tech.id] = {
                    "name": tech.name,
                    "category": tech.category,
                    "description": tech.description,
                    "ecosystem": tech.ecosystem.value if tech.ecosystem else None,
                    "maturity": tech.maturity.value
                }
            else:
                # Full export
                data["technologies"][tech.id] = tech.to_dict()
        
        with open(output_path, 'w') as f:
            json.dump(data, f, indent=2)
    
    def _export_csv(self, technologies: List[TechEntry], output_path: Path, args) -> None:
        """Export to CSV format."""
        fieldnames = [
            'id', 'name', 'canonical_name', 'category', 'description',
            'ecosystem', 'maturity', 'license', 'confidence_score',
            'pending_review', 'auto_generated', 'review_status'
        ]
        
        if not args.minimal:
            fieldnames.extend([
                'aliases', 'integrates_with', 'alternatives', 'tags', 'use_cases',
                'added_date', 'last_updated', 'reviewed_by', 'review_notes'
            ])
        
        with open(output_path, 'w', newline='') as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            
            for tech in technologies:
                row = {
                    'id': tech.id,
                    'name': tech.name,
                    'canonical_name': tech.canonical_name,
                    'category': tech.category,
                    'description': tech.description,
                    'ecosystem': tech.ecosystem.value if tech.ecosystem else '',
                    'maturity': tech.maturity.value,
                    'license': tech.license,
                    'confidence_score': tech.confidence_score,
                    'pending_review': tech.pending_review,
                    'auto_generated': tech.auto_generated,
                    'review_status': tech.review_status.value
                }
                
                if not args.minimal:
                    row.update({
                        'aliases': ';'.join(tech.aliases),
                        'integrates_with': ';'.join(tech.integrates_with),
                        'alternatives': ';'.join(tech.alternatives),
                        'tags': ';'.join(tech.tags),
                        'use_cases': ';'.join(tech.use_cases),
                        'added_date': tech.added_date.isoformat() if tech.added_date else '',
                        'last_updated': tech.last_updated.isoformat() if tech.last_updated else '',
                        'reviewed_by': tech.reviewed_by or '',
                        'review_notes': tech.review_notes or ''
                    })
                
                writer.writerow(row)
    
    def _export_yaml(self, technologies: List[TechEntry], output_path: Path, args) -> None:
        """Export to YAML format."""
        data = {
            "metadata": {
                "export_date": datetime.now().isoformat(),
                "total_entries": len(technologies),
                "format_version": "1.0"
            },
            "technologies": {}
        }
        
        for tech in technologies:
            if args.minimal:
                data["technologies"][tech.id] = {
                    "name": tech.name,
                    "category": tech.category,
                    "description": tech.description,
                    "ecosystem": tech.ecosystem.value if tech.ecosystem else None,
                    "maturity": tech.maturity.value
                }
            else:
                data["technologies"][tech.id] = tech.to_dict()
        
        with open(output_path, 'w') as f:
            yaml.dump(data, f, default_flow_style=False, sort_keys=False)
    
    def import_catalog(self, args) -> None:
        """Import catalog from various formats."""
        try:
            input_path = Path(args.input)
            
            if not input_path.exists():
                print(f"✗ Input file not found: {input_path}")
                sys.exit(1)
            
            # Determine format from extension if not specified
            if not args.format:
                if input_path.suffix.lower() == '.json':
                    args.format = 'json'
                elif input_path.suffix.lower() == '.csv':
                    args.format = 'csv'
                elif input_path.suffix.lower() in ['.yml', '.yaml']:
                    args.format = 'yaml'
                else:
                    print("✗ Cannot determine format from file extension. Please specify --format")
                    sys.exit(1)
            
            # Import based on format
            if args.format == 'json':
                technologies = self._import_json(input_path, args)
            elif args.format == 'csv':
                technologies = self._import_csv(input_path, args)
            elif args.format == 'yaml':
                technologies = self._import_yaml(input_path, args)
            else:
                print(f"✗ Unsupported format: {args.format}")
                sys.exit(1)
            
            if not technologies:
                print("No technologies found in import file")
                return
            
            # Process technologies
            added_count = 0
            updated_count = 0
            skipped_count = 0
            error_count = 0
            
            for tech in technologies:
                try:
                    existing_tech = self.manager.get_technology_by_id(tech.id)
                    
                    if existing_tech and not args.update_existing:
                        skipped_count += 1
                        if args.verbose:
                            print(f"Skipped existing: {tech.name} (use --update-existing to overwrite)")
                        continue
                    
                    # Validate technology
                    validation_result = self.manager.validate_catalog_entry(tech)
                    
                    if not validation_result.is_valid and not args.ignore_validation:
                        error_count += 1
                        print(f"✗ Validation failed for {tech.name}: {', '.join(validation_result.errors)}")
                        continue
                    
                    # Add or update technology
                    self.manager.technologies[tech.id] = tech
                    
                    if existing_tech:
                        updated_count += 1
                        if args.verbose:
                            print(f"Updated: {tech.name}")
                    else:
                        added_count += 1
                        if args.verbose:
                            print(f"Added: {tech.name}")
                
                except Exception as e:
                    error_count += 1
                    print(f"✗ Error processing {tech.name if hasattr(tech, 'name') else 'unknown'}: {e}")
            
            # Save changes
            if added_count > 0 or updated_count > 0:
                self.manager._rebuild_indexes()
                self.manager._save_catalog()
            
            print(f"\nImport Summary:")
            print(f"  Added: {added_count}")
            print(f"  Updated: {updated_count}")
            print(f"  Skipped: {skipped_count}")
            print(f"  Errors: {error_count}")
            
        except Exception as e:
            print(f"✗ Error importing catalog: {e}")
            sys.exit(1)
    
    def _import_json(self, input_path: Path, args) -> List[TechEntry]:
        """Import from JSON format."""
        with open(input_path, 'r') as f:
            data = json.load(f)
        
        technologies = []
        
        if "technologies" in data:
            for tech_id, tech_data in data["technologies"].items():
                try:
                    if "id" not in tech_data:
                        tech_data["id"] = tech_id
                    
                    tech = TechEntry.from_dict(tech_data)
                    technologies.append(tech)
                    
                except Exception as e:
                    print(f"✗ Error parsing technology {tech_id}: {e}")
        
        return technologies
    
    def _import_csv(self, input_path: Path, args) -> List[TechEntry]:
        """Import from CSV format."""
        technologies = []
        
        with open(input_path, 'r') as f:
            reader = csv.DictReader(f)
            
            for row in reader:
                try:
                    # Parse basic fields
                    tech_data = {
                        "id": row["id"],
                        "name": row["name"],
                        "canonical_name": row.get("canonical_name", row["name"]),
                        "category": row["category"],
                        "description": row["description"],
                        "license": row.get("license", "unknown"),
                        "confidence_score": float(row.get("confidence_score", 1.0)),
                        "pending_review": row.get("pending_review", "").lower() == "true",
                        "auto_generated": row.get("auto_generated", "").lower() == "true"
                    }
                    
                    # Parse enum fields
                    if row.get("ecosystem"):
                        tech_data["ecosystem"] = row["ecosystem"]
                    
                    if row.get("maturity"):
                        tech_data["maturity"] = row["maturity"]
                    
                    if row.get("review_status"):
                        tech_data["review_status"] = row["review_status"]
                    
                    # Parse list fields (semicolon-separated)
                    for field in ["aliases", "integrates_with", "alternatives", "tags", "use_cases"]:
                        if row.get(field):
                            tech_data[field] = [item.strip() for item in row[field].split(';') if item.strip()]
                    
                    # Parse date fields
                    for field in ["added_date", "last_updated"]:
                        if row.get(field):
                            tech_data[field] = row[field]
                    
                    # Parse other fields
                    for field in ["reviewed_by", "review_notes"]:
                        if row.get(field):
                            tech_data[field] = row[field]
                    
                    tech = TechEntry.from_dict(tech_data)
                    technologies.append(tech)
                    
                except Exception as e:
                    print(f"✗ Error parsing CSV row for {row.get('name', 'unknown')}: {e}")
        
        return technologies
    
    def _import_yaml(self, input_path: Path, args) -> List[TechEntry]:
        """Import from YAML format."""
        with open(input_path, 'r') as f:
            data = yaml.safe_load(f)
        
        technologies = []
        
        if "technologies" in data:
            for tech_id, tech_data in data["technologies"].items():
                try:
                    if "id" not in tech_data:
                        tech_data["id"] = tech_id
                    
                    tech = TechEntry.from_dict(tech_data)
                    technologies.append(tech)
                    
                except Exception as e:
                    print(f"✗ Error parsing technology {tech_id}: {e}")
        
        return technologies
    
    def backup_catalog(self, args) -> None:
        """Create a backup of the current catalog."""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_path = Path(args.output or f"catalog_backup_{timestamp}.json")
            
            # Export full catalog
            technologies = list(self.manager.technologies.values())
            
            data = {
                "metadata": {
                    "backup_date": datetime.now().isoformat(),
                    "total_entries": len(technologies),
                    "format_version": "1.0",
                    "backup_type": "full"
                },
                "technologies": {}
            }
            
            for tech in technologies:
                data["technologies"][tech.id] = tech.to_dict()
            
            with open(backup_path, 'w') as f:
                json.dump(data, f, indent=2)
            
            print(f"✓ Created backup with {len(technologies)} technologies: {backup_path}")
            
        except Exception as e:
            print(f"✗ Error creating backup: {e}")
            sys.exit(1)
    
    def restore_catalog(self, args) -> None:
        """Restore catalog from backup."""
        try:
            backup_path = Path(args.backup)
            
            if not backup_path.exists():
                print(f"✗ Backup file not found: {backup_path}")
                sys.exit(1)
            
            # Confirm restoration
            if not args.force:
                current_count = len(self.manager.technologies)
                response = input(f"This will replace the current catalog ({current_count} technologies). Continue? [y/N]: ")
                if response.lower() != 'y':
                    print("Restoration cancelled")
                    return
            
            # Load backup
            with open(backup_path, 'r') as f:
                data = json.load(f)
            
            if "technologies" not in data:
                print("✗ Invalid backup file format")
                sys.exit(1)
            
            # Clear current catalog
            self.manager.technologies.clear()
            
            # Restore technologies
            restored_count = 0
            error_count = 0
            
            for tech_id, tech_data in data["technologies"].items():
                try:
                    if "id" not in tech_data:
                        tech_data["id"] = tech_id
                    
                    tech = TechEntry.from_dict(tech_data)
                    self.manager.technologies[tech_id] = tech
                    restored_count += 1
                    
                except Exception as e:
                    error_count += 1
                    print(f"✗ Error restoring technology {tech_id}: {e}")
            
            # Rebuild indexes and save
            self.manager._rebuild_indexes()
            self.manager._save_catalog()
            
            print(f"✓ Restored {restored_count} technologies from backup")
            if error_count > 0:
                print(f"⚠ {error_count} technologies could not be restored")
            
        except Exception as e:
            print(f"✗ Error restoring catalog: {e}")
            sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Bulk Catalog Operations CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Export entire catalog to JSON
  python -m app.cli.bulk_operations export catalog.json
  
  # Export only AWS technologies to CSV
  python -m app.cli.bulk_operations export aws_techs.csv --ecosystem aws --format csv
  
  # Import technologies from JSON file
  python -m app.cli.bulk_operations import new_techs.json --update-existing
  
  # Create a backup
  python -m app.cli.bulk_operations backup
  
  # Restore from backup
  python -m app.cli.bulk_operations restore backup_20231201_120000.json
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Export command
    export_parser = subparsers.add_parser('export', help='Export catalog data')
    export_parser.add_argument('output', help='Output file path')
    export_parser.add_argument('--format', choices=['json', 'csv', 'yaml'], help='Export format (auto-detected from extension)')
    export_parser.add_argument('--category', help='Export only this category')
    export_parser.add_argument('--ecosystem', choices=['aws', 'azure', 'gcp', 'open_source', 'proprietary', 'hybrid'], help='Export only this ecosystem')
    export_parser.add_argument('--pending-only', action='store_true', help='Export only pending review technologies')
    export_parser.add_argument('--approved-only', action='store_true', help='Export only approved technologies')
    export_parser.add_argument('--minimal', action='store_true', help='Export minimal fields only')
    
    # Import command
    import_parser = subparsers.add_parser('import', help='Import catalog data')
    import_parser.add_argument('input', help='Input file path')
    import_parser.add_argument('--format', choices=['json', 'csv', 'yaml'], help='Import format (auto-detected from extension)')
    import_parser.add_argument('--update-existing', action='store_true', help='Update existing technologies')
    import_parser.add_argument('--ignore-validation', action='store_true', help='Import even if validation fails')
    import_parser.add_argument('--verbose', action='store_true', help='Show detailed import progress')
    
    # Backup command
    backup_parser = subparsers.add_parser('backup', help='Create catalog backup')
    backup_parser.add_argument('--output', help='Backup file path (auto-generated if not provided)')
    
    # Restore command
    restore_parser = subparsers.add_parser('restore', help='Restore catalog from backup')
    restore_parser.add_argument('backup', help='Backup file path')
    restore_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = BulkOperationsCLI()
    
    # Route to appropriate command handler
    if args.command == 'export':
        cli.export_catalog(args)
    elif args.command == 'import':
        cli.import_catalog(args)
    elif args.command == 'backup':
        cli.backup_catalog(args)
    elif args.command == 'restore':
        cli.restore_catalog(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()