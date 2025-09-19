#!/usr/bin/env python3
"""
Simple Dependency Validation Tool

This script provides basic dependency validation without complex integration.
"""

import os
import sys
import json
import yaml
import argparse
import importlib
import subprocess
from typing import Dict, List, Any, Optional, Tuple
from pathlib import Path
from datetime import datetime
from dataclasses import dataclass

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))


@dataclass
class SimpleValidationResult:
    """Simple validation result."""
    is_available: bool
    installed_version: Optional[str] = None
    error_message: Optional[str] = None
    installation_instructions: Optional[str] = None


class SimpleDependencyValidator:
    """Simple dependency validator."""
    
    def validate_dependency(self, name: str, import_name: str, installation_name: str) -> SimpleValidationResult:
        """Validate a single dependency."""
        try:
            module = importlib.import_module(import_name)
            
            # Try to get version
            version = None
            for attr in ['__version__', 'version', 'VERSION']:
                if hasattr(module, attr):
                    version = getattr(module, attr)
                    break
            
            return SimpleValidationResult(
                is_available=True,
                installed_version=version,
                installation_instructions=f"pip install {installation_name}"
            )
            
        except ImportError as e:
            return SimpleValidationResult(
                is_available=False,
                error_message=str(e),
                installation_instructions=f"pip install {installation_name}"
            )


class DependencyMonitor:
    """CLI tool for dependency validation and monitoring."""
    
    def __init__(self):
        """Initialize the dependency monitor."""
        self.project_root = project_root
        self.config_dir = self.project_root / "config"
        self.validator = SimpleDependencyValidator()
    
    def validate_all_dependencies(self, verbose: bool = False) -> bool:
        """
        Validate all system dependencies.
        
        Args:
            verbose: Enable verbose output
            
        Returns:
            True if all dependencies are valid, False otherwise
        """
        print("🔍 Validating system dependencies...")
        
        # Load dependency configuration
        deps_config = self._load_dependencies_config()
        if not deps_config:
            print("❌ Could not load dependency configuration")
            return False
        
        all_valid = True
        
        # Validate required dependencies
        required_deps = deps_config.get("dependencies", {}).get("required", [])
        print(f"\n📋 Checking {len(required_deps)} required dependencies...")
        
        for dep_config in required_deps:
            name = dep_config["name"]
            import_name = dep_config["import_name"]
            installation_name = dep_config["installation_name"]
            
            result = self.validator.validate_dependency(name, import_name, installation_name)
            
            if result.is_available:
                status = "✅"
                if verbose:
                    version_info = f" ({result.installed_version})" if result.installed_version else ""
                    print(f"{status} {name}{version_info}")
            else:
                status = "❌"
                all_valid = False
                print(f"{status} {name} - {result.error_message}")
                if result.installation_instructions:
                    print(f"   💡 Install with: {result.installation_instructions}")
        
        # Validate optional dependencies
        optional_deps = deps_config.get("dependencies", {}).get("optional", [])
        print(f"\n📋 Checking {len(optional_deps)} optional dependencies...")
        
        optional_available = 0
        for dep_config in optional_deps:
            name = dep_config["name"]
            import_name = dep_config["import_name"]
            installation_name = dep_config["installation_name"]
            
            result = self.validator.validate_dependency(name, import_name, installation_name)
            
            if result.is_available:
                status = "✅"
                optional_available += 1
                if verbose:
                    version_info = f" ({result.installed_version})" if result.installed_version else ""
                    print(f"{status} {name}{version_info}")
            else:
                status = "⚠️ "
                if verbose:
                    print(f"{status} {name} - Optional (not installed)")
        
        print(f"\n📊 Summary:")
        print(f"   Required dependencies: {'✅ All satisfied' if all_valid else '❌ Missing dependencies'}")
        print(f"   Optional dependencies: {optional_available}/{len(optional_deps)} available")
        
        return all_valid
    
    def generate_dependency_report(self, output_file: Optional[str] = None) -> None:
        """
        Generate comprehensive dependency report.
        
        Args:
            output_file: Output file path (auto-generated if None)
        """
        print("📄 Generating dependency report...")
        
        # Collect data
        deps_config = self._load_dependencies_config()
        
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "system_info": self._get_system_info(),
            "dependency_validation": self._validate_all_deps_for_report(deps_config)
        }
        
        # Generate output file name if not provided
        if output_file is None:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_file = f"dependency_report_{timestamp}.json"
        
        output_path = Path(output_file)
        if not output_path.is_absolute():
            output_path = self.project_root / "docs" / "architecture" / "dependencies" / output_path
            output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Write report
        with open(output_path, 'w') as f:
            json.dump(report_data, f, indent=2)
        
        print(f"✅ Report generated: {output_path}")
        
        # Also generate a human-readable summary
        self._generate_summary_report(report_data, output_path.with_suffix('.md'))
    
    def install_missing_dependencies(self, dry_run: bool = False) -> None:
        """
        Install missing required dependencies.
        
        Args:
            dry_run: Show what would be installed without actually installing
        """
        print("📦 Installing missing dependencies...")
        
        deps_config = self._load_dependencies_config()
        if not deps_config:
            print("❌ Could not load dependency configuration")
            return
        
        required_deps = deps_config.get("dependencies", {}).get("required", [])
        missing_deps = []
        
        for dep_config in required_deps:
            name = dep_config["name"]
            import_name = dep_config["import_name"]
            installation_name = dep_config["installation_name"]
            
            result = self.validator.validate_dependency(name, import_name, installation_name)
            if not result.is_available:
                missing_deps.append((name, installation_name, result))
        
        if not missing_deps:
            print("✅ All required dependencies are already installed")
            return
        
        print(f"Found {len(missing_deps)} missing dependencies:")
        
        for name, installation_name, result in missing_deps:
            print(f"   📦 {name}: {result.installation_instructions}")
            
            if not dry_run:
                try:
                    # Install using pip
                    cmd = ["pip", "install", installation_name]
                    
                    print(f"      Running: {' '.join(cmd)}")
                    subprocess.run(cmd, check=True, capture_output=True, text=True)
                    print(f"      ✅ Installed {name}")
                    
                except subprocess.CalledProcessError as e:
                    print(f"      ❌ Failed to install {name}: {e}")
                except Exception as e:
                    print(f"      ❌ Error installing {name}: {e}")
        
        if dry_run:
            print("\n💡 This was a dry run. Use --install to actually install packages.")
    
    def _load_dependencies_config(self) -> Optional[Dict[str, Any]]:
        """Load dependencies configuration."""
        config_file = self.config_dir / "dependencies.yaml"
        try:
            with open(config_file, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading dependencies config: {e}")
            return None
    
    def _get_system_info(self) -> Dict[str, Any]:
        """Get system information."""
        import platform
        
        return {
            "python_version": platform.python_version(),
            "platform": platform.platform(),
            "architecture": platform.architecture(),
            "processor": platform.processor(),
            "working_directory": str(Path.cwd()),
            "project_root": str(self.project_root)
        }
    
    def _validate_all_deps_for_report(self, deps_config: Dict[str, Any]) -> Dict[str, Any]:
        """Validate all dependencies for report generation."""
        if not deps_config:
            return {"error": "Could not load dependency configuration"}
        
        required_results = []
        optional_results = []
        
        # Validate required dependencies
        for dep_config in deps_config.get("dependencies", {}).get("required", []):
            name = dep_config["name"]
            import_name = dep_config["import_name"]
            installation_name = dep_config["installation_name"]
            
            result = self.validator.validate_dependency(name, import_name, installation_name)
            required_results.append({
                "name": name,
                "available": result.is_available,
                "version": result.installed_version,
                "error": result.error_message,
                "installation": result.installation_instructions
            })
        
        # Validate optional dependencies
        for dep_config in deps_config.get("dependencies", {}).get("optional", []):
            name = dep_config["name"]
            import_name = dep_config["import_name"]
            installation_name = dep_config["installation_name"]
            
            result = self.validator.validate_dependency(name, import_name, installation_name)
            optional_results.append({
                "name": name,
                "available": result.is_available,
                "version": result.installed_version,
                "error": result.error_message,
                "installation": result.installation_instructions
            })
        
        return {
            "required": required_results,
            "optional": optional_results,
            "summary": {
                "required_satisfied": all(r["available"] for r in required_results),
                "required_count": len(required_results),
                "required_available": sum(1 for r in required_results if r["available"]),
                "optional_count": len(optional_results),
                "optional_available": sum(1 for r in optional_results if r["available"])
            }
        }
    
    def _generate_summary_report(self, report_data: Dict[str, Any], output_path: Path) -> None:
        """Generate human-readable summary report."""
        content = [
            "# Dependency Validation Report",
            "",
            f"**Generated:** {report_data['generated_at']}",
            "",
            "## System Information",
            "",
            f"- **Python Version:** {report_data['system_info']['python_version']}",
            f"- **Platform:** {report_data['system_info']['platform']}",
            f"- **Project Root:** {report_data['system_info']['project_root']}",
            "",
            "## Dependency Status",
            ""
        ]
        
        # Dependency validation summary
        dep_validation = report_data.get("dependency_validation", {})
        if "summary" in dep_validation:
            summary = dep_validation["summary"]
            content.extend([
                f"### Required Dependencies: {'✅' if summary['required_satisfied'] else '❌'}",
                "",
                f"- **Available:** {summary['required_available']}/{summary['required_count']}",
                "",
                f"### Optional Dependencies",
                "",
                f"- **Available:** {summary['optional_available']}/{summary['optional_count']}",
                ""
            ])
        
        # Write summary
        with open(output_path, 'w') as f:
            f.write('\n'.join(content))
        
        print(f"✅ Summary report generated: {output_path}")


def main():
    """Main entry point for the dependency validator CLI."""
    parser = argparse.ArgumentParser(description="Dependency validation and monitoring tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Validate command
    validate_parser = subparsers.add_parser("validate", help="Validate all dependencies")
    validate_parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    # Report command
    report_parser = subparsers.add_parser("report", help="Generate dependency report")
    report_parser.add_argument("--output", "-o", help="Output file path")
    
    # Install command
    install_parser = subparsers.add_parser("install", help="Install missing dependencies")
    install_parser.add_argument("--dry-run", action="store_true", help="Show what would be installed")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    monitor = DependencyMonitor()
    
    try:
        if args.command == "validate":
            success = monitor.validate_all_dependencies(verbose=args.verbose)
            if not success:
                sys.exit(1)
        
        elif args.command == "report":
            monitor.generate_dependency_report(args.output)
        
        elif args.command == "install":
            monitor.install_missing_dependencies(dry_run=args.dry_run)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()