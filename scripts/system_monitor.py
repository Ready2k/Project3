#!/usr/bin/env python3
"""
Unified System Monitoring CLI

This script provides a unified interface for all dependency validation,
service monitoring, and system health tools.
"""

import os
import sys
import argparse
from pathlib import Path
from typing import Dict, Any, Optional

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


def main():
    """Main entry point for the unified system monitor CLI."""
    parser = argparse.ArgumentParser(
        description="Unified System Monitoring and Validation CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Available Tools:
  dependency-validator    Validate dependencies and generate reports
  service-inspector      Inspect and analyze service registry
  health-dashboard       Monitor service health with web dashboard
  dependency-notifier    Monitor for dependency updates and security issues
  service-manager        Manage service configuration

Examples:
  %(prog)s dependency-validator validate --verbose
  %(prog)s service-inspector inspect logger --detailed
  %(prog)s health-dashboard dashboard --open
  %(prog)s dependency-notifier check --force
  %(prog)s service-manager list-services

For detailed help on each tool:
  %(prog)s <tool-name> --help
        """
    )
    
    parser.add_argument(
        "tool",
        choices=[
            "dependency-validator",
            "service-inspector", 
            "health-dashboard",
            "dependency-notifier",
            "service-manager"
        ],
        help="Tool to run"
    )
    
    # Parse known args to get the tool name
    args, remaining_args = parser.parse_known_args()
    
    # Import and run the appropriate tool
    try:
        if args.tool == "dependency-validator":
            from scripts.dependency_validator import main as validator_main
            sys.argv = ["dependency_validator.py"] + remaining_args
            validator_main()
        
        elif args.tool == "service-inspector":
            from scripts.service_inspector import main as inspector_main
            sys.argv = ["service_inspector.py"] + remaining_args
            inspector_main()
        
        elif args.tool == "health-dashboard":
            from scripts.health_dashboard import main as dashboard_main
            sys.argv = ["health_dashboard.py"] + remaining_args
            dashboard_main()
        
        elif args.tool == "dependency-notifier":
            from scripts.dependency_notifier import main as notifier_main
            sys.argv = ["dependency_notifier.py"] + remaining_args
            notifier_main()
        
        elif args.tool == "service-manager":
            from manage_services import main as manager_main
            sys.argv = ["manage_services.py"] + remaining_args
            manager_main()
    
    except ImportError as e:
        print(f"❌ Error importing tool '{args.tool}': {e}")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error running tool '{args.tool}': {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()