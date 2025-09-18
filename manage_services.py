#!/usr/bin/env python3
"""
Service Configuration Management CLI

This script provides command-line tools for managing service configuration,
validating dependencies, and troubleshooting the service system.
"""

import sys
import argparse
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def list_services(config_dir: str = "config") -> None:
    """List all configured services."""
    from app.core.service_config import get_service_config_loader
    
    print("Configured Services")
    print("=" * 50)
    
    try:
        loader = get_service_config_loader(config_dir)
        loader.load_configuration()
        
        services = loader.get_service_definitions()
        
        if not services:
            print("No services configured.")
            return
        
        for service in services:
            status = "✅ Enabled" if service.enabled else "❌ Disabled"
            singleton = "Singleton" if service.singleton else "Factory"
            deps = f" (deps: {', '.join(service.dependencies)})" if service.dependencies else ""
            
            print(f"{status} {service.name}")
            print(f"   Class: {service.class_path}")
            print(f"   Type: {singleton}{deps}")
            
            if service.health_check.get('enabled', False):
                interval = service.health_check.get('interval_seconds', 'unknown')
                print(f"   Health Check: Every {interval}s")
            
            print()
    
    except Exception as e:
        print(f"❌ Failed to list services: {e}")
        sys.exit(1)


def list_dependencies(config_dir: str = "config", dep_type: str = "all") -> None:
    """List configured dependencies."""
    from app.core.service_config import get_service_config_loader
    
    print(f"Configured Dependencies ({dep_type})")
    print("=" * 50)
    
    try:
        loader = get_service_config_loader(config_dir)
        loader.load_configuration()
        
        dependencies = loader.get_dependency_definitions()
        
        if dep_type != "all":
            dependencies = [d for d in dependencies if d.dependency_type.value == dep_type]
        
        if not dependencies:
            print(f"No {dep_type} dependencies configured.")
            return
        
        # Group by type
        by_type = {}
        for dep in dependencies:
            dep_type_name = dep.dependency_type.value
            if dep_type_name not in by_type:
                by_type[dep_type_name] = []
            by_type[dep_type_name].append(dep)
        
        for type_name, deps in by_type.items():
            print(f"\n{type_name.title()} Dependencies:")
            print("-" * 30)
            
            for dep in deps:
                constraint = f" ({dep.version_constraint})" if dep.version_constraint else ""
                print(f"📦 {dep.name}{constraint}")
                print(f"   Purpose: {dep.purpose}")
                if dep.alternatives:
                    print(f"   Alternatives: {', '.join(dep.alternatives)}")
                print()
    
    except Exception as e:
        print(f"❌ Failed to list dependencies: {e}")
        sys.exit(1)


def validate_dependencies(config_dir: str = "config", include_dev: bool = False) -> None:
    """Validate all dependencies."""
    from app.core.service_config import get_service_config_loader
    
    print("Dependency Validation")
    print("=" * 50)
    
    try:
        loader = get_service_config_loader(config_dir)
        loader.load_configuration()
        
        validator = loader.setup_dependency_validator()
        result = validator.validate_all(include_dev=include_dev)
        
        if result.is_valid:
            print("✅ All dependencies are valid!")
        else:
            print("❌ Dependency validation failed!")
        
        print(f"\nSummary:")
        print(f"   Missing required: {len(result.missing_required)}")
        print(f"   Missing optional: {len(result.missing_optional)}")
        print(f"   Version conflicts: {len(result.version_conflicts)}")
        print(f"   Warnings: {len(result.warnings)}")
        
        if result.missing_required:
            print(f"\n❌ Missing Required Dependencies:")
            for dep in result.missing_required:
                print(f"   - {dep}")
        
        if result.missing_optional:
            print(f"\nℹ️  Missing Optional Dependencies:")
            for dep in result.missing_optional:
                print(f"   - {dep}")
        
        if result.version_conflicts:
            print(f"\n⚠️  Version Conflicts:")
            for conflict in result.version_conflicts:
                print(f"   - {conflict}")
        
        if result.warnings:
            print(f"\n⚠️  Warnings:")
            for warning in result.warnings:
                print(f"   - {warning}")
        
        if result.installation_instructions:
            print(f"\n📋 Installation Instructions:")
            print(result.installation_instructions)
    
    except Exception as e:
        print(f"❌ Failed to validate dependencies: {e}")
        sys.exit(1)


def show_dependency_groups(config_dir: str = "config") -> None:
    """Show available dependency groups."""
    from app.core.service_config import get_service_config_loader
    
    print("Dependency Groups")
    print("=" * 50)
    
    try:
        loader = get_service_config_loader(config_dir)
        loader.load_configuration()
        
        groups = loader.get_dependency_groups()
        
        if not groups:
            print("No dependency groups configured.")
            return
        
        for group_name, group_config in groups.items():
            description = group_config.get('description', 'No description')
            dependencies = group_config.get('dependencies', [])
            
            print(f"📦 {group_name}")
            print(f"   Description: {description}")
            print(f"   Dependencies: {len(dependencies)}")
            
            # Show installation command
            command = loader.get_installation_command(group_name)
            if command:
                print(f"   Install: {command}")
            
            print()
    
    except Exception as e:
        print(f"❌ Failed to show dependency groups: {e}")
        sys.exit(1)


def run_startup_validation(config_dir: str = "config", include_dev: bool = False) -> None:
    """Run complete startup validation."""
    from app.core.startup import run_application_startup, print_startup_summary
    
    print("Application Startup Validation")
    print("=" * 50)
    
    try:
        results = run_application_startup(config_dir, include_dev)
        print_startup_summary(results)
        
        if not results.get('startup_successful', False):
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Startup validation failed: {e}")
        sys.exit(1)


def install_group(group_name: str, config_dir: str = "config", dry_run: bool = False) -> None:
    """Install a dependency group."""
    from app.core.service_config import get_service_config_loader
    import subprocess
    
    print(f"Installing Dependency Group: {group_name}")
    print("=" * 50)
    
    try:
        loader = get_service_config_loader(config_dir)
        loader.load_configuration()
        
        command = loader.get_installation_command(group_name)
        
        if not command:
            print(f"❌ Dependency group '{group_name}' not found.")
            groups = loader.get_dependency_groups()
            if groups:
                print(f"Available groups: {', '.join(groups.keys())}")
            sys.exit(1)
        
        print(f"Installation command: {command}")
        
        if dry_run:
            print("🔍 Dry run mode - command not executed")
            return
        
        print("🚀 Executing installation...")
        result = subprocess.run(command.split(), capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✅ Installation completed successfully!")
            if result.stdout:
                print("Output:")
                print(result.stdout)
        else:
            print("❌ Installation failed!")
            if result.stderr:
                print("Error:")
                print(result.stderr)
            sys.exit(1)
    
    except Exception as e:
        print(f"❌ Failed to install group: {e}")
        sys.exit(1)


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Service Configuration Management CLI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s list-services                    # List all configured services
  %(prog)s list-deps --type required        # List required dependencies
  %(prog)s validate-deps                    # Validate all dependencies
  %(prog)s show-groups                      # Show dependency groups
  %(prog)s startup-validation               # Run complete startup validation
  %(prog)s install minimal --dry-run        # Show what would be installed
        """
    )
    
    parser.add_argument(
        "--config-dir", 
        default="config", 
        help="Configuration directory (default: config)"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # List services command
    list_services_parser = subparsers.add_parser("list-services", help="List configured services")
    
    # List dependencies command
    list_deps_parser = subparsers.add_parser("list-deps", help="List configured dependencies")
    list_deps_parser.add_argument(
        "--type", 
        choices=["all", "required", "optional", "development"], 
        default="all",
        help="Type of dependencies to list"
    )
    
    # Validate dependencies command
    validate_deps_parser = subparsers.add_parser("validate-deps", help="Validate dependencies")
    validate_deps_parser.add_argument(
        "--include-dev", 
        action="store_true",
        help="Include development dependencies in validation"
    )
    
    # Show dependency groups command
    show_groups_parser = subparsers.add_parser("show-groups", help="Show dependency groups")
    
    # Startup validation command
    startup_parser = subparsers.add_parser("startup-validation", help="Run startup validation")
    startup_parser.add_argument(
        "--include-dev", 
        action="store_true",
        help="Include development dependencies in validation"
    )
    
    # Install group command
    install_parser = subparsers.add_parser("install", help="Install dependency group")
    install_parser.add_argument("group", help="Name of dependency group to install")
    install_parser.add_argument(
        "--dry-run", 
        action="store_true",
        help="Show what would be installed without executing"
    )
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Execute the requested command
    try:
        if args.command == "list-services":
            list_services(args.config_dir)
        elif args.command == "list-deps":
            list_dependencies(args.config_dir, args.type)
        elif args.command == "validate-deps":
            validate_dependencies(args.config_dir, args.include_dev)
        elif args.command == "show-groups":
            show_dependency_groups(args.config_dir)
        elif args.command == "startup-validation":
            run_startup_validation(args.config_dir, args.include_dev)
        elif args.command == "install":
            install_group(args.group, args.config_dir, args.dry_run)
    
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled by user")
        sys.exit(1)


if __name__ == "__main__":
    main()