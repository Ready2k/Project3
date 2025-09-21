#!/usr/bin/env python3
"""
CLI tool for technology catalog management.

This tool provides command-line interface for managing the technology catalog,
including adding, updating, validating technologies, and managing the review queue.
"""

import argparse
import json
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import TechEntry, EcosystemType, MaturityLevel, ReviewStatus
from app.utils.imports import require_service


class CatalogManagerCLI:
    """Command-line interface for catalog management."""
    
    def __init__(self):
        self.manager = IntelligentCatalogManager()
        
    def add_technology(self, args) -> None:
        """Add a new technology to the catalog."""
        try:
            # Parse ecosystem if provided
            ecosystem = None
            if args.ecosystem:
                ecosystem = EcosystemType(args.ecosystem.lower())
            
            # Parse maturity if provided
            maturity = MaturityLevel.STABLE
            if args.maturity:
                maturity = MaturityLevel(args.maturity.lower())
            
            # Create technology entry
            tech_entry = TechEntry(
                id=args.id or self.manager._generate_tech_id(args.name),
                name=args.name,
                canonical_name=args.canonical_name or args.name,
                category=args.category,
                description=args.description,
                aliases=args.aliases or [],
                ecosystem=ecosystem,
                integrates_with=args.integrates_with or [],
                alternatives=args.alternatives or [],
                tags=args.tags or [],
                use_cases=args.use_cases or [],
                license=args.license or "unknown",
                maturity=maturity,
                auto_generated=False,
                pending_review=args.pending_review
            )
            
            # Add to catalog
            self.manager.technologies[tech_entry.id] = tech_entry
            self.manager._rebuild_indexes()
            self.manager._save_catalog()
            
            print(f"✓ Added technology: {tech_entry.name} (ID: {tech_entry.id})")
            
        except Exception as e:
            print(f"✗ Error adding technology: {e}")
            sys.exit(1)
    
    def update_technology(self, args) -> None:
        """Update an existing technology."""
        try:
            if args.tech_id not in self.manager.technologies:
                print(f"✗ Technology not found: {args.tech_id}")
                sys.exit(1)
            
            updates = {}
            
            # Collect updates from arguments
            if args.name:
                updates['name'] = args.name
            if args.canonical_name:
                updates['canonical_name'] = args.canonical_name
            if args.category:
                updates['category'] = args.category
            if args.description:
                updates['description'] = args.description
            if args.ecosystem:
                updates['ecosystem'] = EcosystemType(args.ecosystem.lower())
            if args.maturity:
                updates['maturity'] = MaturityLevel(args.maturity.lower())
            if args.license:
                updates['license'] = args.license
            
            # Handle list fields
            if args.add_alias:
                tech = self.manager.technologies[args.tech_id]
                for alias in args.add_alias:
                    tech.add_alias(alias)
            
            if args.add_integration:
                tech = self.manager.technologies[args.tech_id]
                for integration in args.add_integration:
                    if integration not in tech.integrates_with:
                        tech.integrates_with.append(integration)
            
            if args.add_alternative:
                tech = self.manager.technologies[args.tech_id]
                for alternative in args.add_alternative:
                    if alternative not in tech.alternatives:
                        tech.alternatives.append(alternative)
            
            if args.add_tag:
                tech = self.manager.technologies[args.tech_id]
                for tag in args.add_tag:
                    if tag not in tech.tags:
                        tech.tags.append(tag)
            
            if args.add_use_case:
                tech = self.manager.technologies[args.tech_id]
                for use_case in args.add_use_case:
                    if use_case not in tech.use_cases:
                        tech.use_cases.append(use_case)
            
            # Apply updates
            if updates:
                success = self.manager.update_technology(args.tech_id, updates)
                if success:
                    print(f"✓ Updated technology: {args.tech_id}")
                else:
                    print(f"✗ Failed to update technology: {args.tech_id}")
            else:
                print("✓ Technology updated with list additions")
                
        except Exception as e:
            print(f"✗ Error updating technology: {e}")
            sys.exit(1)
    
    def validate_catalog(self, args) -> None:
        """Validate the entire catalog for consistency."""
        try:
            print("Validating catalog consistency...")
            
            result = self.manager.validate_catalog_consistency()
            
            if result.is_valid:
                print("✓ Catalog validation passed")
            else:
                print("✗ Catalog validation failed")
            
            if result.errors:
                print("\nErrors:")
                for error in result.errors:
                    print(f"  - {error}")
            
            if result.warnings:
                print("\nWarnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")
            
            if result.suggestions:
                print("\nSuggestions:")
                for suggestion in result.suggestions:
                    print(f"  - {suggestion}")
            
            # Validate individual entries if requested
            if args.detailed:
                print("\nValidating individual entries...")
                error_count = 0
                warning_count = 0
                
                for tech_id, tech in self.manager.technologies.items():
                    entry_result = self.manager.validate_catalog_entry(tech)
                    
                    if not entry_result.is_valid:
                        error_count += 1
                        print(f"\n✗ {tech.name} (ID: {tech_id})")
                        for error in entry_result.errors:
                            print(f"    Error: {error}")
                    
                    if entry_result.warnings:
                        warning_count += 1
                        if entry_result.is_valid:  # Only show if no errors
                            print(f"\n⚠ {tech.name} (ID: {tech_id})")
                        for warning in entry_result.warnings:
                            print(f"    Warning: {warning}")
                
                print(f"\nSummary: {error_count} entries with errors, {warning_count} with warnings")
            
        except Exception as e:
            print(f"✗ Error validating catalog: {e}")
            sys.exit(1)
    
    def show_statistics(self, args) -> None:
        """Show catalog statistics."""
        try:
            stats = self.manager.get_catalog_statistics()
            
            print("Catalog Statistics")
            print("=" * 50)
            print(f"Total entries: {stats.total_entries}")
            print(f"Pending review: {stats.pending_review}")
            print(f"Auto-generated: {stats.auto_generated}")
            print(f"Validation errors: {stats.validation_errors}")
            
            if stats.by_ecosystem:
                print("\nBy Ecosystem:")
                for ecosystem, count in sorted(stats.by_ecosystem.items()):
                    print(f"  {ecosystem}: {count}")
            
            if stats.by_category:
                print("\nBy Category:")
                for category, count in sorted(stats.by_category.items()):
                    print(f"  {category}: {count}")
            
            if stats.by_maturity:
                print("\nBy Maturity:")
                for maturity, count in sorted(stats.by_maturity.items()):
                    print(f"  {maturity}: {count}")
            
        except Exception as e:
            print(f"✗ Error getting statistics: {e}")
            sys.exit(1)
    
    def search_technologies(self, args) -> None:
        """Search for technologies."""
        try:
            results = self.manager.search_technologies(args.query, limit=args.limit)
            
            if not results:
                print(f"No technologies found matching: {args.query}")
                return
            
            print(f"Found {len(results)} technologies matching: {args.query}")
            print("=" * 50)
            
            for result in results:
                tech = result.tech_entry
                print(f"\n{tech.name} (ID: {tech.id})")
                print(f"  Category: {tech.category}")
                print(f"  Description: {tech.description}")
                print(f"  Match Score: {result.match_score:.2f}")
                print(f"  Match Type: {result.match_type}")
                
                if tech.aliases:
                    print(f"  Aliases: {', '.join(tech.aliases)}")
                
                if tech.ecosystem:
                    print(f"  Ecosystem: {tech.ecosystem.value}")
                
        except Exception as e:
            print(f"✗ Error searching technologies: {e}")
            sys.exit(1)
    
    def show_technology(self, args) -> None:
        """Show detailed information about a technology."""
        try:
            tech = self.manager.get_technology_by_id(args.tech_id)
            
            if not tech:
                print(f"✗ Technology not found: {args.tech_id}")
                sys.exit(1)
            
            print(f"Technology: {tech.name}")
            print("=" * 50)
            print(f"ID: {tech.id}")
            print(f"Canonical Name: {tech.canonical_name}")
            print(f"Category: {tech.category}")
            print(f"Description: {tech.description}")
            
            if tech.aliases:
                print(f"Aliases: {', '.join(tech.aliases)}")
            
            if tech.ecosystem:
                print(f"Ecosystem: {tech.ecosystem.value}")
            
            print(f"Maturity: {tech.maturity.value}")
            print(f"License: {tech.license}")
            print(f"Confidence Score: {tech.confidence_score}")
            
            if tech.integrates_with:
                print(f"Integrates With: {', '.join(tech.integrates_with)}")
            
            if tech.alternatives:
                print(f"Alternatives: {', '.join(tech.alternatives)}")
            
            if tech.tags:
                print(f"Tags: {', '.join(tech.tags)}")
            
            if tech.use_cases:
                print(f"Use Cases: {', '.join(tech.use_cases)}")
            
            print(f"\nMetadata:")
            print(f"  Auto-generated: {tech.auto_generated}")
            print(f"  Pending Review: {tech.pending_review}")
            print(f"  Review Status: {tech.review_status.value}")
            print(f"  Mention Count: {tech.mention_count}")
            print(f"  Selection Count: {tech.selection_count}")
            
            if tech.added_date:
                print(f"  Added: {tech.added_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if tech.last_updated:
                print(f"  Last Updated: {tech.last_updated.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if tech.validation_errors:
                print(f"\nValidation Errors:")
                for error in tech.validation_errors:
                    print(f"  - {error}")
            
        except Exception as e:
            print(f"✗ Error showing technology: {e}")
            sys.exit(1)
    
    def list_technologies(self, args) -> None:
        """List technologies with optional filtering."""
        try:
            technologies = list(self.manager.technologies.values())
            
            # Apply filters
            if args.category:
                technologies = [t for t in technologies if t.category == args.category]
            
            if args.ecosystem:
                ecosystem = EcosystemType(args.ecosystem.lower())
                technologies = [t for t in technologies if t.ecosystem == ecosystem]
            
            if args.pending_review:
                technologies = [t for t in technologies if t.pending_review]
            
            if args.auto_generated:
                technologies = [t for t in technologies if t.auto_generated]
            
            # Sort technologies
            if args.sort_by == 'name':
                technologies.sort(key=lambda t: t.name.lower())
            elif args.sort_by == 'category':
                technologies.sort(key=lambda t: (t.category, t.name.lower()))
            elif args.sort_by == 'added_date':
                technologies.sort(key=lambda t: t.added_date or datetime.min, reverse=True)
            
            if not technologies:
                print("No technologies found matching the criteria")
                return
            
            print(f"Found {len(technologies)} technologies")
            print("=" * 80)
            
            for tech in technologies:
                status_indicators = []
                if tech.pending_review:
                    status_indicators.append("PENDING")
                if tech.auto_generated:
                    status_indicators.append("AUTO")
                if tech.validation_errors:
                    status_indicators.append("ERRORS")
                
                status_str = f" [{', '.join(status_indicators)}]" if status_indicators else ""
                
                print(f"{tech.id:<20} {tech.name:<30} {tech.category:<15}{status_str}")
                
                if args.verbose:
                    print(f"  Description: {tech.description}")
                    if tech.ecosystem:
                        print(f"  Ecosystem: {tech.ecosystem.value}")
                    print()
            
        except Exception as e:
            print(f"✗ Error listing technologies: {e}")
            sys.exit(1)
    
    def delete_technology(self, args) -> None:
        """Delete a technology from the catalog."""
        try:
            if args.tech_id not in self.manager.technologies:
                print(f"✗ Technology not found: {args.tech_id}")
                sys.exit(1)
            
            tech = self.manager.technologies[args.tech_id]
            
            if not args.force:
                response = input(f"Are you sure you want to delete '{tech.name}' (ID: {args.tech_id})? [y/N]: ")
                if response.lower() != 'y':
                    print("Deletion cancelled")
                    return
            
            # Remove from catalog
            del self.manager.technologies[args.tech_id]
            self.manager._rebuild_indexes()
            self.manager._save_catalog()
            
            print(f"✓ Deleted technology: {tech.name} (ID: {args.tech_id})")
            
        except Exception as e:
            print(f"✗ Error deleting technology: {e}")
            sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Technology Catalog Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Add a new technology
  python -m app.cli.catalog_manager add --name "FastAPI" --category "frameworks" --description "Modern Python web framework"
  
  # Update a technology
  python -m app.cli.catalog_manager update fastapi --add-alias "fast-api" --add-tag "python"
  
  # Search for technologies
  python -m app.cli.catalog_manager search "fast"
  
  # Validate the catalog
  python -m app.cli.catalog_manager validate --detailed
  
  # Show statistics
  python -m app.cli.catalog_manager stats
  
  # List technologies by category
  python -m app.cli.catalog_manager list --category "frameworks"
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # Add command
    add_parser = subparsers.add_parser('add', help='Add a new technology')
    add_parser.add_argument('--name', required=True, help='Technology name')
    add_parser.add_argument('--id', help='Technology ID (auto-generated if not provided)')
    add_parser.add_argument('--canonical-name', help='Canonical name (defaults to name)')
    add_parser.add_argument('--category', required=True, help='Technology category')
    add_parser.add_argument('--description', required=True, help='Technology description')
    add_parser.add_argument('--ecosystem', choices=['aws', 'azure', 'gcp', 'open_source', 'proprietary', 'hybrid'], help='Technology ecosystem')
    add_parser.add_argument('--maturity', choices=['experimental', 'beta', 'stable', 'mature', 'deprecated'], help='Maturity level')
    add_parser.add_argument('--license', help='License type')
    add_parser.add_argument('--aliases', nargs='*', help='Technology aliases')
    add_parser.add_argument('--integrates-with', nargs='*', help='Technologies this integrates with')
    add_parser.add_argument('--alternatives', nargs='*', help='Alternative technologies')
    add_parser.add_argument('--tags', nargs='*', help='Technology tags')
    add_parser.add_argument('--use-cases', nargs='*', help='Use cases')
    add_parser.add_argument('--pending-review', action='store_true', help='Mark as pending review')
    
    # Update command
    update_parser = subparsers.add_parser('update', help='Update an existing technology')
    update_parser.add_argument('tech_id', help='Technology ID to update')
    update_parser.add_argument('--name', help='Update technology name')
    update_parser.add_argument('--canonical-name', help='Update canonical name')
    update_parser.add_argument('--category', help='Update category')
    update_parser.add_argument('--description', help='Update description')
    update_parser.add_argument('--ecosystem', choices=['aws', 'azure', 'gcp', 'open_source', 'proprietary', 'hybrid'], help='Update ecosystem')
    update_parser.add_argument('--maturity', choices=['experimental', 'beta', 'stable', 'mature', 'deprecated'], help='Update maturity')
    update_parser.add_argument('--license', help='Update license')
    update_parser.add_argument('--add-alias', action='append', help='Add an alias (can be used multiple times)')
    update_parser.add_argument('--add-integration', action='append', help='Add an integration (can be used multiple times)')
    update_parser.add_argument('--add-alternative', action='append', help='Add an alternative (can be used multiple times)')
    update_parser.add_argument('--add-tag', action='append', help='Add a tag (can be used multiple times)')
    update_parser.add_argument('--add-use-case', action='append', help='Add a use case (can be used multiple times)')
    
    # Validate command
    validate_parser = subparsers.add_parser('validate', help='Validate catalog consistency')
    validate_parser.add_argument('--detailed', action='store_true', help='Perform detailed validation of individual entries')
    
    # Statistics command
    stats_parser = subparsers.add_parser('stats', help='Show catalog statistics')
    
    # Search command
    search_parser = subparsers.add_parser('search', help='Search for technologies')
    search_parser.add_argument('query', help='Search query')
    search_parser.add_argument('--limit', type=int, default=10, help='Maximum number of results')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show detailed technology information')
    show_parser.add_argument('tech_id', help='Technology ID to show')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List technologies')
    list_parser.add_argument('--category', help='Filter by category')
    list_parser.add_argument('--ecosystem', choices=['aws', 'azure', 'gcp', 'open_source', 'proprietary', 'hybrid'], help='Filter by ecosystem')
    list_parser.add_argument('--pending-review', action='store_true', help='Show only pending review')
    list_parser.add_argument('--auto-generated', action='store_true', help='Show only auto-generated')
    list_parser.add_argument('--sort-by', choices=['name', 'category', 'added_date'], default='name', help='Sort by field')
    list_parser.add_argument('--verbose', action='store_true', help='Show detailed information')
    
    # Delete command
    delete_parser = subparsers.add_parser('delete', help='Delete a technology')
    delete_parser.add_argument('tech_id', help='Technology ID to delete')
    delete_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = CatalogManagerCLI()
    
    # Route to appropriate command handler
    if args.command == 'add':
        cli.add_technology(args)
    elif args.command == 'update':
        cli.update_technology(args)
    elif args.command == 'validate':
        cli.validate_catalog(args)
    elif args.command == 'stats':
        cli.show_statistics(args)
    elif args.command == 'search':
        cli.search_technologies(args)
    elif args.command == 'show':
        cli.show_technology(args)
    elif args.command == 'list':
        cli.list_technologies(args)
    elif args.command == 'delete':
        cli.delete_technology(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()