#!/usr/bin/env python3
"""
CLI tool for managing the technology catalog review queue.

This tool provides command-line interface for reviewing pending technologies,
approving/rejecting entries, and managing the review workflow.
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import ReviewStatus


class ReviewManagerCLI:
    """Command-line interface for review queue management."""
    
    def __init__(self):
        self.manager = IntelligentCatalogManager()
        
    def list_pending(self, args) -> None:
        """List all technologies pending review."""
        try:
            pending_techs = self.manager.get_pending_review_queue()
            
            if not pending_techs:
                print("No technologies pending review")
                return
            
            print(f"Found {len(pending_techs)} technologies pending review")
            print("=" * 80)
            
            for tech in pending_techs:
                status_str = f"[{tech.review_status.value.upper()}]"
                auto_str = "[AUTO]" if tech.auto_generated else ""
                confidence_str = f"(confidence: {tech.confidence_score:.2f})" if tech.auto_generated else ""
                
                print(f"{tech.id:<20} {tech.name:<25} {tech.category:<15} {status_str} {auto_str} {confidence_str}")
                
                if args.verbose:
                    print(f"  Description: {tech.description}")
                    if tech.source_context:
                        print(f"  Source Context: {tech.source_context}")
                    if tech.review_notes:
                        print(f"  Review Notes: {tech.review_notes}")
                    if tech.added_date:
                        print(f"  Added: {tech.added_date.strftime('%Y-%m-%d %H:%M:%S')}")
                    print()
            
        except Exception as e:
            print(f"✗ Error listing pending reviews: {e}")
            sys.exit(1)
    
    def show_review_details(self, args) -> None:
        """Show detailed information for review."""
        try:
            tech = self.manager.get_technology_by_id(args.tech_id)
            
            if not tech:
                print(f"✗ Technology not found: {args.tech_id}")
                sys.exit(1)
            
            print(f"Review Details: {tech.name}")
            print("=" * 60)
            print(f"ID: {tech.id}")
            print(f"Name: {tech.name}")
            print(f"Canonical Name: {tech.canonical_name}")
            print(f"Category: {tech.category}")
            print(f"Description: {tech.description}")
            
            if tech.aliases:
                print(f"Aliases: {', '.join(tech.aliases)}")
            
            if tech.ecosystem:
                print(f"Ecosystem: {tech.ecosystem.value}")
            
            print(f"Maturity: {tech.maturity.value}")
            print(f"License: {tech.license}")
            
            if tech.integrates_with:
                print(f"Integrates With: {', '.join(tech.integrates_with)}")
            
            if tech.alternatives:
                print(f"Alternatives: {', '.join(tech.alternatives)}")
            
            if tech.tags:
                print(f"Tags: {', '.join(tech.tags)}")
            
            if tech.use_cases:
                print(f"Use Cases: {', '.join(tech.use_cases)}")
            
            print("\nReview Information:")
            print(f"  Status: {tech.review_status.value}")
            print(f"  Auto-generated: {tech.auto_generated}")
            print(f"  Confidence Score: {tech.confidence_score}")
            print(f"  Pending Review: {tech.pending_review}")
            
            if tech.source_context:
                print(f"  Source Context: {tech.source_context}")
            
            if tech.added_date:
                print(f"  Added: {tech.added_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if tech.reviewed_by:
                print(f"  Reviewed By: {tech.reviewed_by}")
                print(f"  Reviewed Date: {tech.reviewed_date.strftime('%Y-%m-%d %H:%M:%S')}")
            
            if tech.review_notes:
                print(f"  Review Notes: {tech.review_notes}")
            
            # Validate the entry
            validation_result = self.manager.validate_catalog_entry(tech)
            
            print("\nValidation Status:")
            if validation_result.is_valid:
                print("  ✓ Entry is valid")
            else:
                print("  ✗ Entry has validation issues")
            
            if validation_result.errors:
                print("  Errors:")
                for error in validation_result.errors:
                    print(f"    - {error}")
            
            if validation_result.warnings:
                print("  Warnings:")
                for warning in validation_result.warnings:
                    print(f"    - {warning}")
            
            if validation_result.suggestions:
                print("  Suggestions:")
                for suggestion in validation_result.suggestions:
                    print(f"    - {suggestion}")
            
        except Exception as e:
            print(f"✗ Error showing review details: {e}")
            sys.exit(1)
    
    def approve_technology(self, args) -> None:
        """Approve a technology entry."""
        try:
            tech = self.manager.get_technology_by_id(args.tech_id)
            
            if not tech:
                print(f"✗ Technology not found: {args.tech_id}")
                sys.exit(1)
            
            if not tech.pending_review:
                print(f"✗ Technology is not pending review: {tech.name}")
                sys.exit(1)
            
            # Show summary before approval
            if not args.force:
                print(f"Approving technology: {tech.name}")
                print(f"  Category: {tech.category}")
                print(f"  Description: {tech.description}")
                
                response = input("Proceed with approval? [y/N]: ")
                if response.lower() != 'y':
                    print("Approval cancelled")
                    return
            
            # Approve the technology
            success = self.manager.approve_technology(args.tech_id, args.reviewer, args.notes)
            
            if success:
                print(f"✓ Approved technology: {tech.name}")
            else:
                print(f"✗ Failed to approve technology: {tech.name}")
                sys.exit(1)
            
        except Exception as e:
            print(f"✗ Error approving technology: {e}")
            sys.exit(1)
    
    def reject_technology(self, args) -> None:
        """Reject a technology entry."""
        try:
            tech = self.manager.get_technology_by_id(args.tech_id)
            
            if not tech:
                print(f"✗ Technology not found: {args.tech_id}")
                sys.exit(1)
            
            if not tech.pending_review:
                print(f"✗ Technology is not pending review: {tech.name}")
                sys.exit(1)
            
            if not args.notes:
                print("✗ Rejection notes are required")
                sys.exit(1)
            
            # Show summary before rejection
            if not args.force:
                print(f"Rejecting technology: {tech.name}")
                print(f"  Reason: {args.notes}")
                
                response = input("Proceed with rejection? [y/N]: ")
                if response.lower() != 'y':
                    print("Rejection cancelled")
                    return
            
            # Reject the technology
            success = self.manager.reject_technology(args.tech_id, args.reviewer, args.notes)
            
            if success:
                print(f"✓ Rejected technology: {tech.name}")
            else:
                print(f"✗ Failed to reject technology: {tech.name}")
                sys.exit(1)
            
        except Exception as e:
            print(f"✗ Error rejecting technology: {e}")
            sys.exit(1)
    
    def request_update(self, args) -> None:
        """Request updates to a technology entry."""
        try:
            tech = self.manager.get_technology_by_id(args.tech_id)
            
            if not tech:
                print(f"✗ Technology not found: {args.tech_id}")
                sys.exit(1)
            
            if not args.notes:
                print("✗ Update request notes are required")
                sys.exit(1)
            
            # Request update
            success = self.manager.request_technology_update(args.tech_id, args.reviewer, args.notes)
            
            if success:
                print(f"✓ Requested update for technology: {tech.name}")
            else:
                print(f"✗ Failed to request update for technology: {tech.name}")
                sys.exit(1)
            
        except Exception as e:
            print(f"✗ Error requesting update: {e}")
            sys.exit(1)
    
    def batch_approve(self, args) -> None:
        """Batch approve technologies based on criteria."""
        try:
            pending_techs = self.manager.get_pending_review_queue()
            
            # Filter technologies based on criteria
            candidates = []
            
            for tech in pending_techs:
                # Apply filters
                if args.min_confidence and tech.confidence_score < args.min_confidence:
                    continue
                
                if args.category and tech.category != args.category:
                    continue
                
                if args.auto_generated_only and not tech.auto_generated:
                    continue
                
                # Validate the entry
                validation_result = self.manager.validate_catalog_entry(tech)
                
                if args.valid_only and not validation_result.is_valid:
                    continue
                
                candidates.append(tech)
            
            if not candidates:
                print("No technologies match the batch approval criteria")
                return
            
            print(f"Found {len(candidates)} technologies for batch approval:")
            for tech in candidates:
                confidence_str = f"(confidence: {tech.confidence_score:.2f})" if tech.auto_generated else ""
                print(f"  - {tech.name} [{tech.category}] {confidence_str}")
            
            if not args.force:
                response = input(f"\nApprove all {len(candidates)} technologies? [y/N]: ")
                if response.lower() != 'y':
                    print("Batch approval cancelled")
                    return
            
            # Approve all candidates
            approved_count = 0
            failed_count = 0
            
            for tech in candidates:
                success = self.manager.approve_technology(tech.id, args.reviewer, "Batch approval")
                if success:
                    approved_count += 1
                    print(f"✓ Approved: {tech.name}")
                else:
                    failed_count += 1
                    print(f"✗ Failed to approve: {tech.name}")
            
            print(f"\nBatch approval complete: {approved_count} approved, {failed_count} failed")
            
        except Exception as e:
            print(f"✗ Error in batch approval: {e}")
            sys.exit(1)
    
    def review_statistics(self, args) -> None:
        """Show review queue statistics."""
        try:
            pending_techs = self.manager.get_pending_review_queue()
            all_techs = list(self.manager.technologies.values())
            
            # Calculate statistics
            total_count = len(all_techs)
            pending_count = len(pending_techs)
            approved_count = len([t for t in all_techs if t.review_status == ReviewStatus.APPROVED])
            rejected_count = len([t for t in all_techs if t.review_status == ReviewStatus.REJECTED])
            needs_update_count = len([t for t in all_techs if t.review_status == ReviewStatus.NEEDS_UPDATE])
            auto_generated_count = len([t for t in all_techs if t.auto_generated])
            
            print("Review Queue Statistics")
            print("=" * 50)
            print(f"Total technologies: {total_count}")
            print(f"Pending review: {pending_count}")
            print(f"Approved: {approved_count}")
            print(f"Rejected: {rejected_count}")
            print(f"Needs update: {needs_update_count}")
            print(f"Auto-generated: {auto_generated_count}")
            
            if pending_count > 0:
                print("\nPending Review Breakdown:")
                
                # By status
                status_counts = {}
                for tech in pending_techs:
                    status = tech.review_status.value
                    status_counts[status] = status_counts.get(status, 0) + 1
                
                for status, count in sorted(status_counts.items()):
                    print(f"  {status}: {count}")
                
                # By category
                category_counts = {}
                for tech in pending_techs:
                    category = tech.category
                    category_counts[category] = category_counts.get(category, 0) + 1
                
                print("\nBy Category:")
                for category, count in sorted(category_counts.items()):
                    print(f"  {category}: {count}")
                
                # Confidence distribution for auto-generated
                auto_pending = [t for t in pending_techs if t.auto_generated]
                if auto_pending:
                    print("\nAuto-generated Confidence Distribution:")
                    high_conf = len([t for t in auto_pending if t.confidence_score >= 0.8])
                    med_conf = len([t for t in auto_pending if 0.6 <= t.confidence_score < 0.8])
                    low_conf = len([t for t in auto_pending if t.confidence_score < 0.6])
                    
                    print(f"  High (≥0.8): {high_conf}")
                    print(f"  Medium (0.6-0.8): {med_conf}")
                    print(f"  Low (<0.6): {low_conf}")
            
        except Exception as e:
            print(f"✗ Error getting review statistics: {e}")
            sys.exit(1)


def create_parser() -> argparse.ArgumentParser:
    """Create the argument parser."""
    parser = argparse.ArgumentParser(
        description="Technology Catalog Review Queue Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # List all pending reviews
  python -m app.cli.review_manager list --verbose
  
  # Show detailed review information
  python -m app.cli.review_manager show fastapi
  
  # Approve a technology
  python -m app.cli.review_manager approve fastapi --reviewer "john.doe" --notes "Looks good"
  
  # Reject a technology
  python -m app.cli.review_manager reject unknown_tech --reviewer "jane.smith" --notes "Not a real technology"
  
  # Batch approve high-confidence auto-generated entries
  python -m app.cli.review_manager batch-approve --reviewer "admin" --min-confidence 0.8 --auto-generated-only
  
  # Show review statistics
  python -m app.cli.review_manager stats
        """
    )
    
    subparsers = parser.add_subparsers(dest='command', help='Available commands')
    
    # List command
    list_parser = subparsers.add_parser('list', help='List technologies pending review')
    list_parser.add_argument('--verbose', action='store_true', help='Show detailed information')
    
    # Show command
    show_parser = subparsers.add_parser('show', help='Show detailed review information')
    show_parser.add_argument('tech_id', help='Technology ID to review')
    
    # Approve command
    approve_parser = subparsers.add_parser('approve', help='Approve a technology')
    approve_parser.add_argument('tech_id', help='Technology ID to approve')
    approve_parser.add_argument('--reviewer', required=True, help='Reviewer name/ID')
    approve_parser.add_argument('--notes', help='Approval notes')
    approve_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Reject command
    reject_parser = subparsers.add_parser('reject', help='Reject a technology')
    reject_parser.add_argument('tech_id', help='Technology ID to reject')
    reject_parser.add_argument('--reviewer', required=True, help='Reviewer name/ID')
    reject_parser.add_argument('--notes', required=True, help='Rejection reason (required)')
    reject_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Request update command
    update_parser = subparsers.add_parser('request-update', help='Request updates to a technology')
    update_parser.add_argument('tech_id', help='Technology ID to request update for')
    update_parser.add_argument('--reviewer', required=True, help='Reviewer name/ID')
    update_parser.add_argument('--notes', required=True, help='Update request notes (required)')
    
    # Batch approve command
    batch_parser = subparsers.add_parser('batch-approve', help='Batch approve technologies')
    batch_parser.add_argument('--reviewer', required=True, help='Reviewer name/ID')
    batch_parser.add_argument('--min-confidence', type=float, help='Minimum confidence score for auto-generated entries')
    batch_parser.add_argument('--category', help='Only approve technologies in this category')
    batch_parser.add_argument('--auto-generated-only', action='store_true', help='Only approve auto-generated entries')
    batch_parser.add_argument('--valid-only', action='store_true', help='Only approve entries that pass validation')
    batch_parser.add_argument('--force', action='store_true', help='Skip confirmation prompt')
    
    # Statistics command
    subparsers.add_parser('stats', help='Show review queue statistics')
    
    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    cli = ReviewManagerCLI()
    
    # Route to appropriate command handler
    if args.command == 'list':
        cli.list_pending(args)
    elif args.command == 'show':
        cli.show_review_details(args)
    elif args.command == 'approve':
        cli.approve_technology(args)
    elif args.command == 'reject':
        cli.reject_technology(args)
    elif args.command == 'request-update':
        cli.request_update(args)
    elif args.command == 'batch-approve':
        cli.batch_approve(args)
    elif args.command == 'stats':
        cli.review_statistics(args)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == '__main__':
    main()