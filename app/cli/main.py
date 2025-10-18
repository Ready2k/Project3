#!/usr/bin/env python3
"""
Main CLI entry point for all catalog management tools.

This provides a unified interface to access all catalog management utilities:
- catalog: Basic catalog management (add, update, validate, etc.)
- review: Review queue management
- bulk: Bulk import/export operations
- dashboard: Statistics and health monitoring
"""

import argparse
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.cli.catalog_manager import main as catalog_main
from app.cli.review_manager import main as review_main
from app.cli.bulk_operations import main as bulk_main
from app.cli.catalog_dashboard import main as dashboard_main


def create_parser() -> argparse.ArgumentParser:
    """Create the main argument parser."""
    parser = argparse.ArgumentParser(
        description="Technology Catalog Management Suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Tools:
  catalog    - Basic catalog management (add, update, validate technologies)
  review     - Review queue management (approve, reject, batch operations)
  bulk       - Bulk import/export operations (JSON, CSV, YAML formats)
  dashboard  - Statistics and health monitoring dashboard

Examples:
  # Show catalog overview
  python -m app.cli.main dashboard overview
  
  # Add a new technology
  python -m app.cli.main catalog add --name "FastAPI" --category "frameworks" --description "Modern Python web framework"
  
  # List pending reviews
  python -m app.cli.main review list --verbose
  
  # Export catalog to JSON
  python -m app.cli.main bulk export catalog.json
  
  # Validate catalog
  python -m app.cli.main catalog validate --detailed

For detailed help on any tool, use:
  python -m app.cli.main <tool> --help
        """,
    )

    subparsers = parser.add_subparsers(dest="tool", help="Available tools")

    # Catalog management
    catalog_parser = subparsers.add_parser("catalog", help="Basic catalog management")
    catalog_parser.add_argument(
        "catalog_args", nargs=argparse.REMAINDER, help="Arguments for catalog tool"
    )

    # Review management
    review_parser = subparsers.add_parser("review", help="Review queue management")
    review_parser.add_argument(
        "review_args", nargs=argparse.REMAINDER, help="Arguments for review tool"
    )

    # Bulk operations
    bulk_parser = subparsers.add_parser("bulk", help="Bulk import/export operations")
    bulk_parser.add_argument(
        "bulk_args", nargs=argparse.REMAINDER, help="Arguments for bulk tool"
    )

    # Dashboard
    dashboard_parser = subparsers.add_parser(
        "dashboard", help="Statistics and health monitoring"
    )
    dashboard_parser.add_argument(
        "dashboard_args", nargs=argparse.REMAINDER, help="Arguments for dashboard tool"
    )

    return parser


def main():
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()

    if not args.tool:
        parser.print_help()
        sys.exit(1)

    # Route to appropriate tool
    if args.tool == "catalog":
        # Replace sys.argv with catalog arguments
        sys.argv = ["catalog_manager.py"] + args.catalog_args
        catalog_main()
    elif args.tool == "review":
        sys.argv = ["review_manager.py"] + args.review_args
        review_main()
    elif args.tool == "bulk":
        sys.argv = ["bulk_operations.py"] + args.bulk_args
        bulk_main()
    elif args.tool == "dashboard":
        sys.argv = ["catalog_dashboard.py"] + args.dashboard_args
        dashboard_main()
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
