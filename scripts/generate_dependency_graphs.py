#!/usr/bin/env python3
"""
Dependency Graph Generator

This script generates visual dependency graphs from the service registry
and creates comprehensive documentation of service relationships.
"""

import os
import sys
import json
import yaml
from typing import Dict, List, Set, Any, Optional, Tuple
from pathlib import Path
from dataclasses import dataclass, asdict
from datetime import datetime
import argparse

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from app.core.registry import ServiceRegistry, get_registry


@dataclass
class ServiceNode:
    """Represents a service node in the dependency graph."""
    name: str
    service_type: str
    dependencies: List[str]
    dependents: List[str]
    class_path: Optional[str] = None
    config: Optional[Dict[str, Any]] = None
    health_check_enabled: bool = False
    singleton: bool = True
    category: str = "unknown"


@dataclass
class DependencyGraph:
    """Represents the complete dependency graph."""
    nodes: Dict[str, ServiceNode]
    edges: List[Tuple[str, str]]  # (from, to) pairs
    cycles: List[List[str]]
    orphaned_services: List[str]
    root_services: List[str]
    leaf_services: List[str]
    service_categories: Dict[str, List[str]]


class DependencyGraphGenerator:
    """Generates dependency graphs and documentation from service registry."""
    
    def __init__(self, config_path: str = "config/services.yaml"):
        """
        Initialize the dependency graph generator.
        
        Args:
            config_path: Path to the services configuration file
        """
        self.config_path = Path(project_root) / config_path
        self.output_dir = Path(project_root) / "docs" / "architecture" / "dependencies"
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Load service configuration
        self.service_config = self._load_service_config()
        
        # Service categories for better organization
        self.service_categories = {
            "core": ["logger", "config", "cache"],
            "security": ["security_validator", "advanced_prompt_defender"],
            "llm": ["llm_provider_factory", "openai_provider", "anthropic_provider", "bedrock_provider"],
            "diagram": ["diagram_service_factory", "mermaid_service", "infrastructure_diagram_service"],
            "analysis": ["pattern_matcher", "agentic_matcher", "embedding_engine"],
            "export": ["export_service"],
            "monitoring": ["performance_monitor", "health_checker"],
            "integration": ["jira_service"],
            "pattern": ["pattern_loader"]
        }
    
    def generate_all(self) -> None:
        """Generate all dependency graphs and documentation."""
        print("Generating dependency graphs and documentation...")
        
        # Generate dependency graph
        graph = self._build_dependency_graph()
        
        # Generate various outputs
        self._generate_mermaid_diagram(graph)
        self._generate_graphviz_diagram(graph)
        self._generate_json_report(graph)
        self._generate_markdown_documentation(graph)
        self._generate_api_documentation()
        self._generate_dependency_report_template()
        
        print(f"Documentation generated in: {self.output_dir}")
    
    def _load_service_config(self) -> Dict[str, Any]:
        """Load service configuration from YAML file."""
        try:
            with open(self.config_path, 'r') as f:
                return yaml.safe_load(f)
        except Exception as e:
            print(f"Error loading service config: {e}")
            return {"services": {}}
    
    def _build_dependency_graph(self) -> DependencyGraph:
        """Build the complete dependency graph from service configuration."""
        nodes = {}
        edges = []
        
        services = self.service_config.get("services", {})
        
        # Create nodes
        for service_name, service_config in services.items():
            dependencies = service_config.get("dependencies", [])
            
            # Determine service category
            category = "unknown"
            for cat, services_in_cat in self.service_categories.items():
                if service_name in services_in_cat:
                    category = cat
                    break
            
            node = ServiceNode(
                name=service_name,
                service_type=service_config.get("class_path", "unknown"),
                dependencies=dependencies,
                dependents=[],  # Will be populated later
                class_path=service_config.get("class_path"),
                config=service_config.get("config", {}),
                health_check_enabled=service_config.get("health_check", {}).get("enabled", False),
                singleton=service_config.get("singleton", True),
                category=category
            )
            nodes[service_name] = node
            
            # Create edges
            for dep in dependencies:
                edges.append((service_name, dep))
        
        # Populate dependents
        for service_name, dep_name in edges:
            if dep_name in nodes:
                nodes[dep_name].dependents.append(service_name)
        
        # Analyze graph structure
        cycles = self._detect_cycles(nodes, edges)
        orphaned_services = self._find_orphaned_services(nodes)
        root_services = self._find_root_services(nodes)
        leaf_services = self._find_leaf_services(nodes)
        service_categories = self._categorize_services(nodes)
        
        return DependencyGraph(
            nodes=nodes,
            edges=edges,
            cycles=cycles,
            orphaned_services=orphaned_services,
            root_services=root_services,
            leaf_services=leaf_services,
            service_categories=service_categories
        )
    
    def _detect_cycles(self, nodes: Dict[str, ServiceNode], edges: List[Tuple[str, str]]) -> List[List[str]]:
        """Detect circular dependencies in the graph."""
        cycles = []
        visited = set()
        rec_stack = set()
        
        def dfs(node: str, path: List[str]) -> None:
            if node in rec_stack:
                # Found a cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return
            
            if node in visited:
                return
            
            visited.add(node)
            rec_stack.add(node)
            
            # Visit dependencies
            if node in nodes:
                for dep in nodes[node].dependencies:
                    if dep in nodes:
                        dfs(dep, path + [node])
            
            rec_stack.remove(node)
        
        for node_name in nodes:
            if node_name not in visited:
                dfs(node_name, [])
        
        return cycles
    
    def _find_orphaned_services(self, nodes: Dict[str, ServiceNode]) -> List[str]:
        """Find services with no dependencies and no dependents."""
        orphaned = []
        for name, node in nodes.items():
            if not node.dependencies and not node.dependents:
                orphaned.append(name)
        return orphaned
    
    def _find_root_services(self, nodes: Dict[str, ServiceNode]) -> List[str]:
        """Find services with no dependencies (root nodes)."""
        roots = []
        for name, node in nodes.items():
            if not node.dependencies:
                roots.append(name)
        return roots
    
    def _find_leaf_services(self, nodes: Dict[str, ServiceNode]) -> List[str]:
        """Find services with no dependents (leaf nodes)."""
        leaves = []
        for name, node in nodes.items():
            if not node.dependents:
                leaves.append(name)
        return leaves
    
    def _categorize_services(self, nodes: Dict[str, ServiceNode]) -> Dict[str, List[str]]:
        """Categorize services by their type."""
        categories = {}
        for name, node in nodes.items():
            category = node.category
            if category not in categories:
                categories[category] = []
            categories[category].append(name)
        return categories
    
    def _generate_mermaid_diagram(self, graph: DependencyGraph) -> None:
        """Generate Mermaid diagram for the dependency graph."""
        mermaid_content = ["graph TD"]
        
        # Add style definitions for different categories
        category_styles = {
            "core": "fill:#e1f5fe,stroke:#01579b,stroke-width:2px",
            "security": "fill:#fff3e0,stroke:#e65100,stroke-width:2px",
            "llm": "fill:#f3e5f5,stroke:#4a148c,stroke-width:2px",
            "diagram": "fill:#e8f5e8,stroke:#1b5e20,stroke-width:2px",
            "analysis": "fill:#fff8e1,stroke:#ff6f00,stroke-width:2px",
            "export": "fill:#fce4ec,stroke:#880e4f,stroke-width:2px",
            "monitoring": "fill:#f1f8e9,stroke:#33691e,stroke-width:2px",
            "integration": "fill:#e0f2f1,stroke:#00695c,stroke-width:2px",
            "pattern": "fill:#f9fbe7,stroke:#827717,stroke-width:2px",
            "unknown": "fill:#f5f5f5,stroke:#616161,stroke-width:2px"
        }
        
        # Add nodes with categories
        for name, node in graph.nodes.items():
            safe_name = name.replace("-", "_").replace(".", "_")
            display_name = name.replace("_", " ").title()
            
            if node.singleton:
                shape = f"{safe_name}[{display_name}]"
            else:
                shape = f"{safe_name}({display_name})"
            
            mermaid_content.append(f"    {shape}")
        
        # Add edges
        for from_service, to_service in graph.edges:
            safe_from = from_service.replace("-", "_").replace(".", "_")
            safe_to = to_service.replace("-", "_").replace(".", "_")
            mermaid_content.append(f"    {safe_from} --> {safe_to}")
        
        # Add styles
        mermaid_content.append("")
        for category, style in category_styles.items():
            services_in_category = graph.service_categories.get(category, [])
            for service in services_in_category:
                safe_name = service.replace("-", "_").replace(".", "_")
                mermaid_content.append(f"    classDef {category}Style {style}")
                mermaid_content.append(f"    class {safe_name} {category}Style")
        
        # Highlight cycles if any
        if graph.cycles:
            mermaid_content.append("")
            mermaid_content.append("    %% Circular Dependencies Detected")
            for i, cycle in enumerate(graph.cycles):
                mermaid_content.append(f"    %% Cycle {i+1}: {' -> '.join(cycle)}")
        
        # Write to file
        output_file = self.output_dir / "service_dependency_graph.mmd"
        with open(output_file, 'w') as f:
            f.write('\n'.join(mermaid_content))
        
        print(f"Generated Mermaid diagram: {output_file}")
    
    def _generate_graphviz_diagram(self, graph: DependencyGraph) -> None:
        """Generate Graphviz DOT diagram for the dependency graph."""
        dot_content = ["digraph ServiceDependencies {"]
        dot_content.append("    rankdir=TB;")
        dot_content.append("    node [shape=box, style=rounded];")
        dot_content.append("")
        
        # Define colors for categories
        category_colors = {
            "core": "lightblue",
            "security": "orange",
            "llm": "purple",
            "diagram": "green",
            "analysis": "yellow",
            "export": "pink",
            "monitoring": "lightgreen",
            "integration": "cyan",
            "pattern": "lime",
            "unknown": "lightgray"
        }
        
        # Add nodes
        for name, node in graph.nodes.items():
            color = category_colors.get(node.category, "lightgray")
            shape = "box" if node.singleton else "ellipse"
            
            dot_content.append(f'    "{name}" [fillcolor={color}, style=filled, shape={shape}];')
        
        dot_content.append("")
        
        # Add edges
        for from_service, to_service in graph.edges:
            dot_content.append(f'    "{from_service}" -> "{to_service}";')
        
        # Highlight cycles
        if graph.cycles:
            dot_content.append("")
            dot_content.append("    // Circular Dependencies")
            for cycle in graph.cycles:
                for i in range(len(cycle) - 1):
                    dot_content.append(f'    "{cycle[i]}" -> "{cycle[i+1]}" [color=red, penwidth=3];')
        
        dot_content.append("}")
        
        # Write to file
        output_file = self.output_dir / "service_dependency_graph.dot"
        with open(output_file, 'w') as f:
            f.write('\n'.join(dot_content))
        
        print(f"Generated Graphviz diagram: {output_file}")
    
    def _generate_json_report(self, graph: DependencyGraph) -> None:
        """Generate JSON report of the dependency graph."""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_services": len(graph.nodes),
                "total_dependencies": len(graph.edges),
                "circular_dependencies": len(graph.cycles),
                "orphaned_services": len(graph.orphaned_services),
                "root_services": len(graph.root_services),
                "leaf_services": len(graph.leaf_services)
            },
            "services": {name: asdict(node) for name, node in graph.nodes.items()},
            "dependencies": [{"from": from_svc, "to": to_svc} for from_svc, to_svc in graph.edges],
            "analysis": {
                "cycles": graph.cycles,
                "orphaned_services": graph.orphaned_services,
                "root_services": graph.root_services,
                "leaf_services": graph.leaf_services,
                "service_categories": graph.service_categories
            }
        }
        
        output_file = self.output_dir / "dependency_analysis.json"
        with open(output_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"Generated JSON report: {output_file}")
    
    def _generate_markdown_documentation(self, graph: DependencyGraph) -> None:
        """Generate comprehensive Markdown documentation."""
        content = [
            "# Service Dependency Documentation",
            "",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "",
            f"This document provides a comprehensive overview of the service dependency graph for the Automated AI Assessment (AAA) system.",
            "",
            "### Summary Statistics",
            "",
            f"- **Total Services**: {len(graph.nodes)}",
            f"- **Total Dependencies**: {len(graph.edges)}",
            f"- **Circular Dependencies**: {len(graph.cycles)}",
            f"- **Orphaned Services**: {len(graph.orphaned_services)}",
            f"- **Root Services**: {len(graph.root_services)}",
            f"- **Leaf Services**: {len(graph.leaf_services)}",
            ""
        ]
        
        # Service Categories
        content.extend([
            "## Service Categories",
            "",
            "Services are organized into the following categories:",
            ""
        ])
        
        for category, services in graph.service_categories.items():
            content.append(f"### {category.title()} Services")
            content.append("")
            for service in sorted(services):
                node = graph.nodes[service]
                content.append(f"- **{service}**: {node.class_path or 'Unknown class'}")
            content.append("")
        
        # Dependency Analysis
        content.extend([
            "## Dependency Analysis",
            "",
            "### Root Services (No Dependencies)",
            "",
            "These services have no dependencies and can be initialized first:",
            ""
        ])
        
        for service in sorted(graph.root_services):
            node = graph.nodes[service]
            content.append(f"- **{service}** ({node.category}): {node.class_path or 'Unknown'}")
        
        content.extend([
            "",
            "### Leaf Services (No Dependents)",
            "",
            "These services are not depended upon by other services:",
            ""
        ])
        
        for service in sorted(graph.leaf_services):
            node = graph.nodes[service]
            content.append(f"- **{service}** ({node.category}): {node.class_path or 'Unknown'}")
        
        # Circular Dependencies
        if graph.cycles:
            content.extend([
                "",
                "### ⚠️ Circular Dependencies",
                "",
                "The following circular dependencies were detected and should be resolved:",
                ""
            ])
            
            for i, cycle in enumerate(graph.cycles, 1):
                content.append(f"**Cycle {i}**: {' → '.join(cycle)}")
                content.append("")
        
        # Orphaned Services
        if graph.orphaned_services:
            content.extend([
                "### Orphaned Services",
                "",
                "These services have no dependencies and no dependents:",
                ""
            ])
            
            for service in sorted(graph.orphaned_services):
                node = graph.nodes[service]
                content.append(f"- **{service}**: {node.class_path or 'Unknown'}")
            content.append("")
        
        # Detailed Service Information
        content.extend([
            "## Detailed Service Information",
            "",
            "### Service Registry",
            ""
        ])
        
        for service_name in sorted(graph.nodes.keys()):
            node = graph.nodes[service_name]
            content.extend([
                f"#### {service_name}",
                "",
                f"- **Type**: {node.service_type}",
                f"- **Category**: {node.category}",
                f"- **Class Path**: {node.class_path or 'Not specified'}",
                f"- **Singleton**: {'Yes' if node.singleton else 'No'}",
                f"- **Health Check**: {'Enabled' if node.health_check_enabled else 'Disabled'}",
                f"- **Dependencies**: {', '.join(node.dependencies) if node.dependencies else 'None'}",
                f"- **Dependents**: {', '.join(node.dependents) if node.dependents else 'None'}",
                ""
            ])
        
        # Initialization Order
        content.extend([
            "## Recommended Initialization Order",
            "",
            "Based on the dependency analysis, services should be initialized in the following order:",
            ""
        ])
        
        # Simple topological sort for initialization order
        init_order = self._calculate_initialization_order(graph)
        for i, service in enumerate(init_order, 1):
            node = graph.nodes[service]
            content.append(f"{i}. **{service}** ({node.category})")
        
        content.extend([
            "",
            "## Diagrams",
            "",
            "### Mermaid Diagram",
            "",
            "```mermaid"
        ])
        
        # Include the Mermaid diagram content
        mermaid_file = self.output_dir / "service_dependency_graph.mmd"
        if mermaid_file.exists():
            with open(mermaid_file, 'r') as f:
                mermaid_content = f.read()
            content.append(mermaid_content)
        
        content.extend([
            "```",
            "",
            "### Graphviz Diagram",
            "",
            f"A Graphviz DOT file is available at: `{self.output_dir.relative_to(project_root)}/service_dependency_graph.dot`",
            "",
            "To generate a visual diagram:",
            "",
            "```bash",
            "dot -Tpng service_dependency_graph.dot -o service_dependency_graph.png",
            "```",
            ""
        ])
        
        # Write to file
        output_file = self.output_dir / "SERVICE_DEPENDENCIES.md"
        with open(output_file, 'w') as f:
            f.write('\n'.join(content))
        
        print(f"Generated Markdown documentation: {output_file}")
    
    def _calculate_initialization_order(self, graph: DependencyGraph) -> List[str]:
        """Calculate the recommended initialization order using topological sort."""
        # Kahn's algorithm for topological sorting
        in_degree = {name: 0 for name in graph.nodes}
        
        # Calculate in-degrees
        for from_service, to_service in graph.edges:
            if to_service in in_degree:
                in_degree[to_service] += 1
        
        # Start with nodes that have no dependencies
        queue = [name for name, degree in in_degree.items() if degree == 0]
        result = []
        
        while queue:
            # Sort to ensure consistent ordering
            queue.sort()
            current = queue.pop(0)
            result.append(current)
            
            # Update in-degrees of dependent services
            if current in graph.nodes:
                for dependent in graph.nodes[current].dependents:
                    if dependent in in_degree:
                        in_degree[dependent] -= 1
                        if in_degree[dependent] == 0:
                            queue.append(dependent)
        
        return result
    
    def _generate_api_documentation(self) -> None:
        """Generate API documentation from type hints."""
        content = [
            "# Service Registry API Documentation",
            "",
            f"Generated on: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Overview",
            "",
            "This document provides comprehensive API documentation for the Service Registry system,",
            "including all classes, methods, and protocols.",
            "",
            "## Core Classes",
            "",
            "### ServiceRegistry",
            "",
            "The main service registry class that manages service registration and dependency injection.",
            "",
            "#### Methods",
            "",
            "##### `register_singleton(name: str, service: Any, dependencies: Optional[List[str]] = None) -> None`",
            "",
            "Register a singleton service instance.",
            "",
            "**Parameters:**",
            "- `name`: Service name for registry lookup",
            "- `service`: Service instance to register",
            "- `dependencies`: List of dependency service names",
            "",
            "**Raises:**",
            "- No exceptions raised directly",
            "",
            "##### `register_factory(name: str, factory: Callable[[], T], dependencies: Optional[List[str]] = None) -> None`",
            "",
            "Register a service factory for on-demand creation.",
            "",
            "**Parameters:**",
            "- `name`: Service name for registry lookup",
            "- `factory`: Factory function that creates service instances",
            "- `dependencies`: List of dependency service names",
            "",
            "##### `register_class(name: str, cls: Type[T], dependencies: Optional[List[str]] = None) -> None`",
            "",
            "Register a class with automatic dependency injection.",
            "",
            "**Parameters:**",
            "- `name`: Service name for registry lookup",
            "- `cls`: Service class to register",
            "- `dependencies`: List of dependency service names (auto-detected if None)",
            "",
            "##### `get(name: str) -> Any`",
            "",
            "Get service instance, creating if necessary.",
            "",
            "**Parameters:**",
            "- `name`: Service name to retrieve",
            "",
            "**Returns:**",
            "- Service instance",
            "",
            "**Raises:**",
            "- `ServiceNotFoundError`: If service is not registered",
            "- `CircularDependencyError`: If circular dependency detected",
            "- `ServiceInitializationError`: If service initialization fails",
            "",
            "##### `has(name: str) -> bool`",
            "",
            "Check if service is registered.",
            "",
            "**Parameters:**",
            "- `name`: Service name to check",
            "",
            "**Returns:**",
            "- `True` if service is registered, `False` otherwise",
            "",
            "##### `validate_dependencies() -> List[str]`",
            "",
            "Validate all registered dependencies can be resolved.",
            "",
            "**Returns:**",
            "- List of validation error messages (empty if all valid)",
            "",
            "##### `health_check(name: Optional[str] = None) -> Dict[str, bool]`",
            "",
            "Perform health check on services.",
            "",
            "**Parameters:**",
            "- `name`: Specific service name to check (all services if None)",
            "",
            "**Returns:**",
            "- Dictionary mapping service names to health status",
            "",
            "### Service Protocols",
            "",
            "#### LoggerProtocol",
            "",
            "Protocol for logger services with standard logging methods.",
            "",
            "#### ConfigProtocol",
            "",
            "Protocol for configuration services with get/set operations.",
            "",
            "#### CacheProtocol",
            "",
            "Protocol for cache services with standard cache operations.",
            "",
            "#### DatabaseProtocol",
            "",
            "Protocol for database services with connection and query methods.",
            "",
            "#### SecurityProtocol",
            "",
            "Protocol for security services with validation and encryption methods.",
            "",
            "#### MonitoringProtocol",
            "",
            "Protocol for monitoring services with metrics recording methods.",
            "",
            "## Usage Examples",
            "",
            "### Basic Service Registration",
            "",
            "```python",
            "from app.core.registry import get_registry",
            "",
            "# Get the global registry",
            "registry = get_registry()",
            "",
            "# Register a singleton service",
            "registry.register_singleton('logger', logger_instance)",
            "",
            "# Register a factory",
            "registry.register_factory('cache', lambda: CacheService())",
            "",
            "# Register a class with auto-dependency injection",
            "registry.register_class('analyzer', AnalyzerService)",
            "```",
            "",
            "### Service Retrieval",
            "",
            "```python",
            "# Get a service (creates if needed)",
            "logger = registry.get('logger')",
            "",
            "# Check if service exists",
            "if registry.has('cache'):",
            "    cache = registry.get('cache')",
            "```",
            "",
            "### Health Monitoring",
            "",
            "```python",
            "# Check all services",
            "health_status = registry.health_check()",
            "",
            "# Check specific service",
            "logger_health = registry.health_check('logger')",
            "```",
            "",
            "### Dependency Validation",
            "",
            "```python",
            "# Validate all dependencies",
            "errors = registry.validate_dependencies()",
            "if errors:",
            "    print('Dependency errors:', errors)",
            "```",
            ""
        ]
        
        output_file = self.output_dir / "API_DOCUMENTATION.md"
        with open(output_file, 'w') as f:
            f.write('\n'.join(content))
        
        print(f"Generated API documentation: {output_file}")
    
    def _generate_dependency_report_template(self) -> None:
        """Generate dependency report templates for monitoring."""
        
        # HTML Template
        html_template = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Service Dependency Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .header { background-color: #f5f5f5; padding: 20px; border-radius: 5px; }
        .summary { display: flex; gap: 20px; margin: 20px 0; }
        .metric { background-color: #e3f2fd; padding: 15px; border-radius: 5px; text-align: center; }
        .metric h3 { margin: 0; color: #1976d2; }
        .metric p { margin: 5px 0 0 0; font-size: 24px; font-weight: bold; }
        .section { margin: 20px 0; }
        .service-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(300px, 1fr)); gap: 15px; }
        .service-card { border: 1px solid #ddd; padding: 15px; border-radius: 5px; }
        .service-card h4 { margin: 0 0 10px 0; color: #333; }
        .healthy { border-left: 4px solid #4caf50; }
        .unhealthy { border-left: 4px solid #f44336; }
        .warning { border-left: 4px solid #ff9800; }
        .dependency-list { list-style-type: none; padding: 0; }
        .dependency-list li { padding: 2px 0; }
        .error { color: #f44336; font-weight: bold; }
        .success { color: #4caf50; font-weight: bold; }
    </style>
</head>
<body>
    <div class="header">
        <h1>Service Dependency Report</h1>
        <p>Generated on: {{timestamp}}</p>
    </div>
    
    <div class="summary">
        <div class="metric">
            <h3>Total Services</h3>
            <p>{{total_services}}</p>
        </div>
        <div class="metric">
            <h3>Dependencies</h3>
            <p>{{total_dependencies}}</p>
        </div>
        <div class="metric">
            <h3>Healthy Services</h3>
            <p>{{healthy_services}}</p>
        </div>
        <div class="metric">
            <h3>Issues</h3>
            <p>{{total_issues}}</p>
        </div>
    </div>
    
    <div class="section">
        <h2>Service Status</h2>
        <div class="service-grid">
            {{service_cards}}
        </div>
    </div>
    
    <div class="section">
        <h2>Dependency Analysis</h2>
        {{dependency_analysis}}
    </div>
    
    <div class="section">
        <h2>Issues and Recommendations</h2>
        {{issues_section}}
    </div>
</body>
</html>"""
        
        # JSON Template
        json_template = {
            "report_metadata": {
                "generated_at": "{{timestamp}}",
                "report_type": "service_dependency_analysis",
                "version": "1.0"
            },
            "summary": {
                "total_services": "{{total_services}}",
                "total_dependencies": "{{total_dependencies}}",
                "healthy_services": "{{healthy_services}}",
                "unhealthy_services": "{{unhealthy_services}}",
                "circular_dependencies": "{{circular_dependencies}}",
                "orphaned_services": "{{orphaned_services}}"
            },
            "services": "{{services_data}}",
            "dependency_graph": {
                "nodes": "{{graph_nodes}}",
                "edges": "{{graph_edges}}"
            },
            "analysis": {
                "initialization_order": "{{init_order}}",
                "critical_path": "{{critical_path}}",
                "bottlenecks": "{{bottlenecks}}"
            },
            "issues": "{{issues_list}}",
            "recommendations": "{{recommendations_list}}"
        }
        
        # Markdown Template
        markdown_template = """# Service Dependency Report

**Generated:** {{timestamp}}

## Summary

| Metric | Value |
|--------|-------|
| Total Services | {{total_services}} |
| Total Dependencies | {{total_dependencies}} |
| Healthy Services | {{healthy_services}} |
| Unhealthy Services | {{unhealthy_services}} |
| Circular Dependencies | {{circular_dependencies}} |
| Orphaned Services | {{orphaned_services}} |

## Service Status

{{service_status_table}}

## Dependency Analysis

### Initialization Order

{{initialization_order}}

### Critical Dependencies

{{critical_dependencies}}

## Issues and Recommendations

{{issues_and_recommendations}}

## Detailed Service Information

{{detailed_service_info}}
"""
        
        # Write templates
        templates_dir = self.output_dir / "templates"
        templates_dir.mkdir(exist_ok=True)
        
        with open(templates_dir / "dependency_report.html", 'w') as f:
            f.write(html_template)
        
        with open(templates_dir / "dependency_report.json", 'w') as f:
            json.dump(json_template, f, indent=2)
        
        with open(templates_dir / "dependency_report.md", 'w') as f:
            f.write(markdown_template)
        
        print(f"Generated report templates in: {templates_dir}")


def main():
    """Main entry point for the dependency graph generator."""
    parser = argparse.ArgumentParser(description="Generate service dependency graphs and documentation")
    parser.add_argument(
        "--config", 
        default="config/services.yaml",
        help="Path to services configuration file"
    )
    parser.add_argument(
        "--output-dir",
        default="docs/architecture/dependencies",
        help="Output directory for generated files"
    )
    
    args = parser.parse_args()
    
    try:
        generator = DependencyGraphGenerator(args.config)
        if args.output_dir != "docs/architecture/dependencies":
            generator.output_dir = Path(project_root) / args.output_dir
            generator.output_dir.mkdir(parents=True, exist_ok=True)
        
        generator.generate_all()
        print("\n✅ Dependency graph generation completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Error generating dependency graphs: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()