#!/usr/bin/env python3
"""
Service Registry Inspector

This script provides tools for inspecting and analyzing the service registry,
including dependency visualization, service lifecycle monitoring, and debugging utilities.
"""

import os
import sys
import json
import argparse
from typing import Dict, List, Any, Optional, Set
from pathlib import Path
from datetime import datetime
import inspect
from dataclasses import asdict

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.registry import get_registry, ServiceRegistry, ServiceInfo
from app.core.service import Service, ConfigurableService


class ServiceInspector:
    """Tool for inspecting and analyzing the service registry."""
    
    def __init__(self):
        """Initialize the service inspector."""
        self.registry = get_registry()
        self.output_dir = Path(project_root) / "docs" / "architecture" / "dependencies"
        self.output_dir.mkdir(parents=True, exist_ok=True)
    
    def inspect_service(self, service_name: str, detailed: bool = False) -> None:
        """
        Inspect a specific service in detail.
        
        Args:
            service_name: Name of the service to inspect
            detailed: Include detailed information like methods and attributes
        """
        print(f"🔍 Inspecting service: {service_name}")
        
        if not self.registry.has(service_name):
            print(f"❌ Service '{service_name}' not found in registry")
            return
        
        service_info = self.registry.get_service_info(service_name)
        if not service_info:
            print(f"❌ Could not get information for service '{service_name}'")
            return
        
        # Basic information
        print(f"\n📋 Basic Information:")
        print(f"   Name: {service_info.name}")
        print(f"   Type: {service_info.service_type}")
        print(f"   Lifecycle: {service_info.lifecycle.value}")
        print(f"   Health Status: {'✅ Healthy' if service_info.health_status else '❌ Unhealthy'}")
        
        if service_info.error_message:
            print(f"   Error: {service_info.error_message}")
        
        # Dependencies
        print(f"\n🔗 Dependencies:")
        if service_info.dependencies:
            for dep in service_info.dependencies:
                dep_status = "✅" if self.registry.has(dep) else "❌"
                print(f"   {dep_status} {dep}")
        else:
            print("   None")
        
        # Dependents (services that depend on this one)
        dependents = self._find_dependents(service_name)
        print(f"\n⬆️  Dependents:")
        if dependents:
            for dependent in dependents:
                print(f"   📦 {dependent}")
        else:
            print("   None")
        
        # Instance information
        if service_info.instance:
            print(f"\n🏗️  Instance Information:")
            instance = service_info.instance
            print(f"   Class: {instance.__class__.__name__}")
            print(f"   Module: {instance.__class__.__module__}")
            
            if hasattr(instance, 'name'):
                print(f"   Service Name: {instance.name}")
            
            if isinstance(instance, ConfigurableService):
                print(f"   State: {instance.state.value}")
                print(f"   Initialized: {instance.is_initialized()}")
            
            if detailed:
                self._inspect_instance_details(instance)
        
        # Factory information
        if service_info.factory:
            print(f"\n🏭 Factory Information:")
            factory = service_info.factory
            print(f"   Function: {factory.__name__}")
            print(f"   Module: {factory.__module__}")
            
            if detailed:
                self._inspect_factory_details(factory)
        
        # Class information
        if service_info.service_class:
            print(f"\n📚 Class Information:")
            cls = service_info.service_class
            print(f"   Class: {cls.__name__}")
            print(f"   Module: {cls.__module__}")
            print(f"   MRO: {' -> '.join(c.__name__ for c in cls.__mro__)}")
            
            if detailed:
                self._inspect_class_details(cls)
    
    def analyze_dependency_chain(self, service_name: str) -> None:
        """
        Analyze the complete dependency chain for a service.
        
        Args:
            service_name: Name of the service to analyze
        """
        print(f"🔗 Analyzing dependency chain for: {service_name}")
        
        if not self.registry.has(service_name):
            print(f"❌ Service '{service_name}' not found in registry")
            return
        
        # Build dependency tree
        dependency_tree = self._build_dependency_tree(service_name)
        
        print(f"\n📊 Dependency Analysis:")
        print(f"   Direct dependencies: {len(dependency_tree.get('direct', []))}")
        print(f"   Total dependencies: {len(dependency_tree.get('all', set()))}")
        print(f"   Dependency depth: {dependency_tree.get('max_depth', 0)}")
        
        # Show dependency tree
        print(f"\n🌳 Dependency Tree:")
        self._print_dependency_tree(service_name, dependency_tree.get('tree', {}), indent=0)
        
        # Check for circular dependencies
        cycles = self._find_cycles_from_service(service_name)
        if cycles:
            print(f"\n⚠️  Circular Dependencies Detected:")
            for cycle in cycles:
                print(f"   🔄 {' -> '.join(cycle)}")
        else:
            print(f"\n✅ No circular dependencies detected")
    
    def generate_service_map(self, output_format: str = "json") -> None:
        """
        Generate a comprehensive map of all services.
        
        Args:
            output_format: Output format (json, yaml, or markdown)
        """
        print(f"🗺️  Generating service map in {output_format} format...")
        
        services = self.registry.list_services()
        service_map = {
            "generated_at": datetime.now().isoformat(),
            "total_services": len(services),
            "services": {}
        }
        
        for service_name in sorted(services):
            service_info = self.registry.get_service_info(service_name)
            if service_info:
                service_data = {
                    "name": service_info.name,
                    "type": service_info.service_type,
                    "lifecycle": service_info.lifecycle.value,
                    "health_status": service_info.health_status,
                    "dependencies": service_info.dependencies,
                    "dependents": self._find_dependents(service_name),
                    "error_message": service_info.error_message
                }
                
                # Add instance information if available
                if service_info.instance:
                    service_data["instance_class"] = service_info.instance.__class__.__name__
                    service_data["instance_module"] = service_info.instance.__class__.__module__
                
                # Add class information if available
                if service_info.service_class:
                    service_data["service_class"] = service_info.service_class.__name__
                    service_data["service_module"] = service_info.service_class.__module__
                
                service_map["services"][service_name] = service_data
        
        # Generate output
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        
        if output_format.lower() == "json":
            output_file = self.output_dir / f"service_map_{timestamp}.json"
            with open(output_file, 'w') as f:
                json.dump(service_map, f, indent=2)
        
        elif output_format.lower() == "yaml":
            import yaml
            output_file = self.output_dir / f"service_map_{timestamp}.yaml"
            with open(output_file, 'w') as f:
                yaml.dump(service_map, f, default_flow_style=False, indent=2)
        
        elif output_format.lower() == "markdown":
            output_file = self.output_dir / f"service_map_{timestamp}.md"
            self._generate_markdown_service_map(service_map, output_file)
        
        else:
            print(f"❌ Unsupported output format: {output_format}")
            return
        
        print(f"✅ Service map generated: {output_file}")
    
    def monitor_service_lifecycle(self, service_name: Optional[str] = None, watch: bool = False) -> None:
        """
        Monitor service lifecycle events.
        
        Args:
            service_name: Specific service to monitor (all if None)
            watch: Continuously monitor for changes
        """
        if watch:
            print("👀 Monitoring service lifecycle (Press Ctrl+C to stop)...")
            # In a real implementation, this would use file system watching
            # or event listeners to monitor changes
            print("⚠️  Continuous monitoring not implemented in this version")
        else:
            print("📊 Current service lifecycle status:")
            
            services = [service_name] if service_name else self.registry.list_services()
            
            for svc_name in sorted(services):
                if self.registry.has(svc_name):
                    service_info = self.registry.get_service_info(svc_name)
                    if service_info:
                        status_icon = {
                            "registered": "🔵",
                            "initializing": "🟡",
                            "initialized": "🟢",
                            "failed": "🔴",
                            "shutdown": "⚫"
                        }.get(service_info.lifecycle.value, "❓")
                        
                        health_icon = "💚" if service_info.health_status else "💔"
                        
                        print(f"   {status_icon} {health_icon} {svc_name} ({service_info.lifecycle.value})")
                        
                        if service_info.error_message:
                            print(f"      ❌ {service_info.error_message}")
    
    def debug_service_issues(self, service_name: Optional[str] = None) -> None:
        """
        Debug service issues and provide recommendations.
        
        Args:
            service_name: Specific service to debug (all if None)
        """
        print("🐛 Debugging service issues...")
        
        services = [service_name] if service_name else self.registry.list_services()
        issues_found = False
        
        for svc_name in sorted(services):
            if not self.registry.has(svc_name):
                continue
            
            service_info = self.registry.get_service_info(svc_name)
            if not service_info:
                continue
            
            service_issues = []
            
            # Check for failed services
            if service_info.lifecycle.value == "failed":
                service_issues.append(f"Service failed to initialize: {service_info.error_message}")
            
            # Check for unhealthy services
            if not service_info.health_status:
                service_issues.append("Service health check failed")
            
            # Check for missing dependencies
            for dep in service_info.dependencies:
                if not self.registry.has(dep):
                    service_issues.append(f"Missing dependency: {dep}")
            
            # Check for circular dependencies
            cycles = self._find_cycles_from_service(svc_name)
            if cycles:
                service_issues.append(f"Circular dependency detected: {cycles[0]}")
            
            if service_issues:
                issues_found = True
                print(f"\n❌ Issues found in service '{svc_name}':")
                for issue in service_issues:
                    print(f"   • {issue}")
                
                # Provide recommendations
                recommendations = self._generate_service_recommendations(svc_name, service_info, service_issues)
                if recommendations:
                    print(f"   💡 Recommendations:")
                    for rec in recommendations:
                        print(f"      - {rec}")
        
        if not issues_found:
            print("✅ No service issues detected")
    
    def _find_dependents(self, service_name: str) -> List[str]:
        """Find services that depend on the given service."""
        dependents = []
        for svc_name in self.registry.list_services():
            service_info = self.registry.get_service_info(svc_name)
            if service_info and service_name in service_info.dependencies:
                dependents.append(svc_name)
        return dependents
    
    def _build_dependency_tree(self, service_name: str, visited: Optional[Set[str]] = None) -> Dict[str, Any]:
        """Build a complete dependency tree for a service."""
        if visited is None:
            visited = set()
        
        if service_name in visited:
            return {"cycle": True}
        
        visited.add(service_name)
        
        service_info = self.registry.get_service_info(service_name)
        if not service_info:
            return {}
        
        tree = {}
        all_deps = set()
        max_depth = 0
        
        for dep in service_info.dependencies:
            if self.registry.has(dep):
                subtree = self._build_dependency_tree(dep, visited.copy())
                tree[dep] = subtree
                
                # Collect all dependencies
                all_deps.add(dep)
                if "all" in subtree:
                    all_deps.update(subtree["all"])
                
                # Track maximum depth
                dep_depth = subtree.get("max_depth", 0) + 1
                max_depth = max(max_depth, dep_depth)
        
        return {
            "tree": tree,
            "direct": service_info.dependencies,
            "all": all_deps,
            "max_depth": max_depth
        }
    
    def _print_dependency_tree(self, service_name: str, tree: Dict[str, Any], indent: int = 0) -> None:
        """Print a dependency tree in a readable format."""
        prefix = "  " * indent
        print(f"{prefix}📦 {service_name}")
        
        for dep_name, subtree in tree.items():
            if isinstance(subtree, dict) and "tree" in subtree:
                self._print_dependency_tree(dep_name, subtree["tree"], indent + 1)
            else:
                print(f"{prefix}  📦 {dep_name}")
    
    def _find_cycles_from_service(self, service_name: str) -> List[List[str]]:
        """Find circular dependencies starting from a specific service."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(current: str, path: List[str]) -> None:
            if current in rec_stack:
                # Found a cycle
                cycle_start = path.index(current)
                cycle = path[cycle_start:] + [current]
                cycles.append(cycle)
                return
            
            if current in visited:
                return
            
            visited.add(current)
            rec_stack.add(current)
            
            service_info = self.registry.get_service_info(current)
            if service_info:
                for dep in service_info.dependencies:
                    if self.registry.has(dep):
                        dfs(dep, path + [current])
            
            rec_stack.remove(current)
        
        dfs(service_name, [])
        return cycles
    
    def _inspect_instance_details(self, instance: Any) -> None:
        """Inspect detailed information about a service instance."""
        print(f"\n🔬 Instance Details:")
        
        # Get all methods
        methods = [name for name, method in inspect.getmembers(instance, predicate=inspect.ismethod)]
        if methods:
            print(f"   Methods: {', '.join(sorted(methods))}")
        
        # Get all attributes
        attributes = [name for name in dir(instance) if not name.startswith('_') and not callable(getattr(instance, name))]
        if attributes:
            print(f"   Attributes: {', '.join(sorted(attributes))}")
        
        # Check for common service interfaces
        if hasattr(instance, 'health_check'):
            print(f"   ✅ Implements health_check")
        if hasattr(instance, 'initialize'):
            print(f"   ✅ Implements initialize")
        if hasattr(instance, 'shutdown'):
            print(f"   ✅ Implements shutdown")
    
    def _inspect_factory_details(self, factory: Any) -> None:
        """Inspect detailed information about a service factory."""
        print(f"\n🔬 Factory Details:")
        
        # Get function signature
        try:
            sig = inspect.signature(factory)
            print(f"   Signature: {factory.__name__}{sig}")
        except Exception as e:
            print(f"   Signature: Could not inspect ({e})")
        
        # Get source file
        try:
            source_file = inspect.getfile(factory)
            print(f"   Source: {source_file}")
        except Exception:
            print(f"   Source: Not available")
    
    def _inspect_class_details(self, cls: type) -> None:
        """Inspect detailed information about a service class."""
        print(f"\n🔬 Class Details:")
        
        # Get constructor signature
        try:
            sig = inspect.signature(cls.__init__)
            print(f"   Constructor: __init__{sig}")
        except Exception as e:
            print(f"   Constructor: Could not inspect ({e})")
        
        # Check for service interface compliance
        if issubclass(cls, Service):
            print(f"   ✅ Implements Service interface")
        if issubclass(cls, ConfigurableService):
            print(f"   ✅ Extends ConfigurableService")
        
        # Get source file
        try:
            source_file = inspect.getfile(cls)
            print(f"   Source: {source_file}")
        except Exception:
            print(f"   Source: Not available")
    
    def _generate_service_recommendations(self, service_name: str, service_info: ServiceInfo, issues: List[str]) -> List[str]:
        """Generate recommendations for fixing service issues."""
        recommendations = []
        
        for issue in issues:
            if "failed to initialize" in issue.lower():
                recommendations.append("Check service configuration and dependencies")
                recommendations.append("Review service logs for detailed error information")
            
            elif "health check failed" in issue.lower():
                recommendations.append("Verify service is properly initialized")
                recommendations.append("Check external dependencies (databases, APIs, etc.)")
            
            elif "missing dependency" in issue.lower():
                recommendations.append("Register the missing dependency in the service registry")
                recommendations.append("Check service configuration for correct dependency names")
            
            elif "circular dependency" in issue.lower():
                recommendations.append("Refactor services to remove circular dependencies")
                recommendations.append("Consider using dependency injection or event-driven patterns")
        
        return recommendations
    
    def _generate_markdown_service_map(self, service_map: Dict[str, Any], output_file: Path) -> None:
        """Generate a Markdown service map."""
        content = [
            "# Service Registry Map",
            "",
            f"**Generated:** {service_map['generated_at']}",
            f"**Total Services:** {service_map['total_services']}",
            "",
            "## Services Overview",
            ""
        ]
        
        # Group services by lifecycle status
        services_by_status = {}
        for service_name, service_data in service_map["services"].items():
            status = service_data["lifecycle"]
            if status not in services_by_status:
                services_by_status[status] = []
            services_by_status[status].append((service_name, service_data))
        
        for status in sorted(services_by_status.keys()):
            services = services_by_status[status]
            status_icon = {
                "registered": "🔵",
                "initializing": "🟡",
                "initialized": "🟢",
                "failed": "🔴",
                "shutdown": "⚫"
            }.get(status, "❓")
            
            content.extend([
                f"### {status_icon} {status.title()} Services ({len(services)})",
                ""
            ])
            
            for service_name, service_data in sorted(services):
                health_icon = "💚" if service_data["health_status"] else "💔"
                content.append(f"- {health_icon} **{service_name}**")
                
                if service_data.get("instance_class"):
                    content.append(f"  - Class: `{service_data['instance_class']}`")
                
                if service_data["dependencies"]:
                    content.append(f"  - Dependencies: {', '.join(service_data['dependencies'])}")
                
                if service_data["dependents"]:
                    content.append(f"  - Dependents: {', '.join(service_data['dependents'])}")
                
                if service_data.get("error_message"):
                    content.append(f"  - ❌ Error: {service_data['error_message']}")
                
                content.append("")
        
        with open(output_file, 'w') as f:
            f.write('\n'.join(content))


def main():
    """Main entry point for the service inspector CLI."""
    parser = argparse.ArgumentParser(description="Service registry inspection and analysis tool")
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Inspect command
    inspect_parser = subparsers.add_parser("inspect", help="Inspect a specific service")
    inspect_parser.add_argument("service", help="Service name to inspect")
    inspect_parser.add_argument("--detailed", "-d", action="store_true", help="Include detailed information")
    
    # Analyze command
    analyze_parser = subparsers.add_parser("analyze", help="Analyze dependency chain")
    analyze_parser.add_argument("service", help="Service name to analyze")
    
    # Map command
    map_parser = subparsers.add_parser("map", help="Generate service map")
    map_parser.add_argument("--format", "-f", choices=["json", "yaml", "markdown"], default="json", help="Output format")
    
    # Monitor command
    monitor_parser = subparsers.add_parser("monitor", help="Monitor service lifecycle")
    monitor_parser.add_argument("--service", "-s", help="Specific service to monitor")
    monitor_parser.add_argument("--watch", "-w", action="store_true", help="Continuously monitor")
    
    # Debug command
    debug_parser = subparsers.add_parser("debug", help="Debug service issues")
    debug_parser.add_argument("--service", "-s", help="Specific service to debug")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        return
    
    inspector = ServiceInspector()
    
    try:
        if args.command == "inspect":
            inspector.inspect_service(args.service, detailed=args.detailed)
        
        elif args.command == "analyze":
            inspector.analyze_dependency_chain(args.service)
        
        elif args.command == "map":
            inspector.generate_service_map(output_format=args.format)
        
        elif args.command == "monitor":
            inspector.monitor_service_lifecycle(service_name=args.service, watch=args.watch)
        
        elif args.command == "debug":
            inspector.debug_service_issues(service_name=args.service)
        
    except KeyboardInterrupt:
        print("\n⚠️  Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n❌ Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()