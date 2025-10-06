"""Agent system export functionality for various formats."""

from typing import Dict, Any
from datetime import datetime

from app.ui.agent_formatter import AgentSystemDisplay
from app.utils.logger import app_logger


class AgentSystemExporter:
    """Exports agent system information to various formats."""
    
    def __init__(self):
        self.export_timestamp = datetime.now().isoformat()
    
    def export_to_json(self, agent_system: AgentSystemDisplay, session_id: str) -> Dict[str, Any]:
        """Export agent system to JSON format."""
        
        app_logger.info(f"Exporting agent system to JSON for session {session_id}")
        
        export_data = {
            "export_metadata": {
                "session_id": session_id,
                "export_timestamp": self.export_timestamp,
                "export_format": "json",
                "exporter_version": "1.0.0"
            },
            "agent_system": {
                "has_agents": agent_system.has_agents,
                "system_autonomy_score": agent_system.system_autonomy_score,
                "agent_count": len(agent_system.agent_roles),
                "architecture_type": agent_system.coordination.architecture_type if agent_system.coordination else "single_agent"
            },
            "agent_roles": [],
            "coordination": None,
            "deployment_requirements": agent_system.deployment_requirements,
            "tech_stack_validation": agent_system.tech_stack_validation,
            "implementation_guidance": agent_system.implementation_guidance
        }
        
        # Export agent roles
        for agent in agent_system.agent_roles:
            agent_data = {
                "name": agent.name,
                "responsibility": agent.responsibility,
                "autonomy_level": agent.autonomy_level,
                "autonomy_description": agent.autonomy_description,
                "capabilities": agent.capabilities,
                "decision_authority": agent.decision_authority,
                "decision_boundaries": agent.decision_boundaries,
                "learning_capabilities": agent.learning_capabilities,
                "exception_handling": agent.exception_handling,
                "communication_requirements": agent.communication_requirements,
                "performance_metrics": agent.performance_metrics,
                "infrastructure_requirements": agent.infrastructure_requirements,
                "security_requirements": agent.security_requirements
            }
            export_data["agent_roles"].append(agent_data)
        
        # Export coordination information
        if agent_system.coordination:
            export_data["coordination"] = {
                "architecture_type": agent_system.coordination.architecture_type,
                "architecture_description": agent_system.coordination.architecture_description,
                "communication_protocols": agent_system.coordination.communication_protocols,
                "coordination_mechanisms": agent_system.coordination.coordination_mechanisms,
                "interaction_patterns": agent_system.coordination.interaction_patterns,
                "conflict_resolution": agent_system.coordination.conflict_resolution,
                "workflow_distribution": agent_system.coordination.workflow_distribution
            }
        
        return export_data
    
    def export_to_markdown(self, agent_system: AgentSystemDisplay, session_id: str) -> str:
        """Export agent system to Markdown format."""
        
        app_logger.info(f"Exporting agent system to Markdown for session {session_id}")
        
        md_content = []
        
        # Header
        md_content.append("# Agentic Solution Design")
        md_content.append(f"**Session ID:** {session_id}")
        md_content.append(f"**Export Date:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        md_content.append("")
        
        # System Overview
        md_content.append("## System Overview")
        md_content.append(f"- **System Autonomy Score:** {agent_system.system_autonomy_score:.1f}")
        md_content.append(f"- **Number of Agents:** {len(agent_system.agent_roles)}")
        
        if agent_system.coordination:
            architecture = agent_system.coordination.architecture_type.replace("_", " ").title()
            md_content.append(f"- **Architecture:** {architecture}")
        else:
            md_content.append("- **Architecture:** Single Agent")
        
        md_content.append("")
        
        # Agent Roles
        md_content.append("## Agent Roles")
        
        for i, agent in enumerate(agent_system.agent_roles, 1):
            md_content.append(f"### {i}. {agent.name}")
            md_content.append(f"**Autonomy Level:** {agent.autonomy_level:.1f} - {agent.autonomy_description}")
            md_content.append("")
            md_content.append("**Primary Responsibility:**")
            md_content.append(agent.responsibility)
            md_content.append("")
            
            # Capabilities
            if agent.capabilities:
                md_content.append("**Core Capabilities:**")
                for capability in agent.capabilities:
                    md_content.append(f"- {capability}")
                md_content.append("")
            
            # Decision Boundaries
            if agent.decision_boundaries:
                md_content.append("**Decision Boundaries:**")
                for boundary in agent.decision_boundaries:
                    md_content.append(f"- {boundary}")
                md_content.append("")
            
            # Learning Capabilities
            if agent.learning_capabilities:
                md_content.append("**Learning Capabilities:**")
                for learning in agent.learning_capabilities:
                    md_content.append(f"- {learning}")
                md_content.append("")
            
            # Exception Handling
            md_content.append("**Exception Handling:**")
            md_content.append(agent.exception_handling)
            md_content.append("")
            
            # Performance Metrics
            if agent.performance_metrics:
                md_content.append("**Performance Metrics:**")
                for metric in agent.performance_metrics:
                    md_content.append(f"- {metric}")
                md_content.append("")
            
            # Infrastructure Requirements
            if agent.infrastructure_requirements:
                md_content.append("**Infrastructure Requirements:**")
                for key, value in agent.infrastructure_requirements.items():
                    md_content.append(f"- **{key.replace('_', ' ').title()}:** {value}")
                md_content.append("")
            
            # Security Requirements
            if agent.security_requirements:
                md_content.append("**Security Requirements:**")
                for security in agent.security_requirements:
                    md_content.append(f"- {security}")
                md_content.append("")
        
        # Coordination
        if agent_system.coordination:
            md_content.append("## Agent Coordination")
            md_content.append(f"**Architecture Type:** {agent_system.coordination.architecture_type.replace('_', ' ').title()}")
            md_content.append(agent_system.coordination.architecture_description)
            md_content.append("")
            
            # Communication Protocols
            if agent_system.coordination.communication_protocols:
                md_content.append("### Communication Protocols")
                for protocol in agent_system.coordination.communication_protocols:
                    md_content.append(f"**{protocol['type'].replace('_', ' ').title()}:**")
                    md_content.append(f"- Participants: {protocol['participants']}")
                    md_content.append(f"- Format: {protocol['format']}")
                    md_content.append(f"- Reliability: {protocol['reliability']}")
                    md_content.append(f"- Latency: {protocol['latency']}")
                    md_content.append("")
            
            # Coordination Mechanisms
            if agent_system.coordination.coordination_mechanisms:
                md_content.append("### Coordination Mechanisms")
                for mechanism in agent_system.coordination.coordination_mechanisms:
                    md_content.append(f"**{mechanism['type'].replace('_', ' ').title()}:**")
                    md_content.append(f"- Participants: {mechanism['participants']}")
                    md_content.append(f"- Decision Criteria: {mechanism['criteria']}")
                    md_content.append(f"- Conflict Resolution: {mechanism['conflict_resolution']}")
                    md_content.append("")
        
        # Tech Stack Validation
        md_content.append("## Tech Stack Validation")
        
        tech_validation = agent_system.tech_stack_validation
        if tech_validation.get("is_agent_ready"):
            md_content.append("✅ **Tech stack is ready for agent deployment**")
        else:
            md_content.append("⚠️ **Tech stack needs enhancements for agent deployment**")
        
        md_content.append("")
        
        # Available components
        if tech_validation.get("deployment_frameworks"):
            md_content.append("**Available Agent Frameworks:**")
            for framework in tech_validation["deployment_frameworks"]:
                md_content.append(f"- ✅ {framework}")
            md_content.append("")
        
        # Missing components
        if tech_validation.get("missing_components"):
            md_content.append("**Missing Components:**")
            for component in tech_validation["missing_components"]:
                md_content.append(f"- ❌ {component}")
            md_content.append("")
        
        # Recommended additions
        if tech_validation.get("recommended_additions"):
            md_content.append("**Recommended Additions:**")
            for addition in tech_validation["recommended_additions"]:
                md_content.append(f"- ➕ {addition}")
            md_content.append("")
        
        # Deployment Requirements
        if agent_system.deployment_requirements:
            md_content.append("## Deployment Requirements")
            
            deploy_reqs = agent_system.deployment_requirements
            
            if "architecture" in deploy_reqs:
                md_content.append(f"**Architecture:** {deploy_reqs['architecture']}")
            
            if "agent_count" in deploy_reqs:
                md_content.append(f"**Agent Count:** {deploy_reqs['agent_count']}")
            
            if "infrastructure_needs" in deploy_reqs:
                md_content.append("**Infrastructure Needs:**")
                for key, value in deploy_reqs["infrastructure_needs"].items():
                    md_content.append(f"- **{key.title()}:** {value}")
            
            md_content.append("")
        
        # Implementation Guidance
        if agent_system.implementation_guidance:
            md_content.append("## Implementation Guidance")
            
            for guidance in agent_system.implementation_guidance:
                title = guidance.get("title", "Guidance")
                content = guidance.get("content", "")
                
                md_content.append(f"### {title}")
                md_content.append(content)
                md_content.append("")
        
        return "\n".join(md_content)
    
    def export_to_html(self, agent_system: AgentSystemDisplay, session_id: str) -> str:
        """Export agent system to interactive HTML format."""
        
        app_logger.info(f"Exporting agent system to HTML for session {session_id}")
        
        # Convert markdown to HTML (simplified version)
        markdown_content = self.export_to_markdown(agent_system, session_id)
        
        html_template = f"""
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Agentic Solution Design - {session_id}</title>
    <style>
        body {{
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            line-height: 1.6;
            color: #333;
            max-width: 1200px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f8f9fa;
        }}
        .container {{
            background: white;
            padding: 30px;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        h1 {{
            color: #2c3e50;
            border-bottom: 3px solid #3498db;
            padding-bottom: 10px;
        }}
        h2 {{
            color: #34495e;
            margin-top: 30px;
            border-left: 4px solid #3498db;
            padding-left: 15px;
        }}
        h3 {{
            color: #2c3e50;
            margin-top: 25px;
        }}
        .agent-card {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 6px;
            padding: 20px;
            margin: 15px 0;
        }}
        .autonomy-score {{
            display: inline-block;
            background: #28a745;
            color: white;
            padding: 4px 8px;
            border-radius: 4px;
            font-weight: bold;
        }}
        .metric-list {{
            display: grid;
            grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
            gap: 10px;
            margin: 15px 0;
        }}
        .metric-item {{
            background: #e9ecef;
            padding: 8px 12px;
            border-radius: 4px;
            font-size: 0.9em;
        }}
        .status-ready {{
            color: #28a745;
            font-weight: bold;
        }}
        .status-warning {{
            color: #ffc107;
            font-weight: bold;
        }}
        .status-error {{
            color: #dc3545;
            font-weight: bold;
        }}
        .export-info {{
            background: #e3f2fd;
            border: 1px solid #bbdefb;
            border-radius: 4px;
            padding: 15px;
            margin-bottom: 20px;
        }}
        pre {{
            background: #f8f9fa;
            border: 1px solid #dee2e6;
            border-radius: 4px;
            padding: 15px;
            overflow-x: auto;
        }}
        ul, ol {{
            padding-left: 20px;
        }}
        li {{
            margin: 5px 0;
        }}
        .print-button {{
            background: #007bff;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 4px;
            cursor: pointer;
            margin: 10px 0;
        }}
        .print-button:hover {{
            background: #0056b3;
        }}
        @media print {{
            body {{
                background: white;
            }}
            .container {{
                box-shadow: none;
            }}
            .print-button {{
                display: none;
            }}
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="export-info">
            <strong>Export Information:</strong><br>
            Session ID: {session_id}<br>
            Export Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}<br>
            Format: Interactive HTML
        </div>
        
        <button class="print-button" onclick="window.print()">🖨️ Print / Save as PDF</button>
        
        <div class="content">
            {self._markdown_to_html(markdown_content)}
        </div>
        
        <script>
            // Add interactivity
            document.addEventListener('DOMContentLoaded', function() {{
                // Add click-to-expand functionality for agent cards
                const agentCards = document.querySelectorAll('.agent-card');
                agentCards.forEach(card => {{
                    card.style.cursor = 'pointer';
                    card.addEventListener('click', function() {{
                        const details = this.querySelector('.agent-details');
                        if (details) {{
                            details.style.display = details.style.display === 'none' ? 'block' : 'none';
                        }}
                    }});
                }});
            }});
        </script>
    </div>
</body>
</html>
"""
        
        return html_template
    
    def _markdown_to_html(self, markdown_content: str) -> str:
        """Convert markdown content to HTML (simplified)."""
        
        html_lines = []
        lines = markdown_content.split('\n')
        
        for line in lines:
            line = line.strip()
            
            if line.startswith('# '):
                html_lines.append(f'<h1>{line[2:]}</h1>')
            elif line.startswith('## '):
                html_lines.append(f'<h2>{line[3:]}</h2>')
            elif line.startswith('### '):
                html_lines.append(f'<h3>{line[4:]}</h3>')
            elif line.startswith('**') and line.endswith('**'):
                html_lines.append(f'<strong>{line[2:-2]}</strong>')
            elif line.startswith('- '):
                html_lines.append(f'<li>{line[2:]}</li>')
            elif line.startswith('✅'):
                html_lines.append(f'<div class="status-ready">{line}</div>')
            elif line.startswith('⚠️'):
                html_lines.append(f'<div class="status-warning">{line}</div>')
            elif line.startswith('❌'):
                html_lines.append(f'<div class="status-error">{line}</div>')
            elif line == '':
                html_lines.append('<br>')
            else:
                html_lines.append(f'<p>{line}</p>')
        
        return '\n'.join(html_lines)
    
    def create_deployment_blueprint(self, agent_system: AgentSystemDisplay, session_id: str) -> Dict[str, Any]:
        """Create a deployment blueprint with configuration files."""
        
        blueprint = {
            "metadata": {
                "session_id": session_id,
                "created_at": self.export_timestamp,
                "blueprint_version": "1.0.0"
            },
            "architecture": {
                "type": agent_system.coordination.architecture_type if agent_system.coordination else "single_agent",
                "agent_count": len(agent_system.agent_roles),
                "autonomy_score": agent_system.system_autonomy_score
            },
            "agents": [],
            "deployment_configs": {},
            "monitoring_configs": {},
            "security_configs": {}
        }
        
        # Add agent specifications
        for agent in agent_system.agent_roles:
            agent_spec = {
                "name": agent.name,
                "role": agent.responsibility,
                "autonomy_level": agent.autonomy_level,
                "capabilities": agent.capabilities,
                "infrastructure": agent.infrastructure_requirements,
                "security": agent.security_requirements
            }
            blueprint["agents"].append(agent_spec)
        
        # Add deployment configurations
        blueprint["deployment_configs"] = {
            "docker_compose": self._generate_docker_compose(agent_system),
            "kubernetes": self._generate_kubernetes_config(agent_system),
            "environment_variables": self._generate_env_config(agent_system)
        }
        
        # Add monitoring configurations
        blueprint["monitoring_configs"] = {
            "prometheus": self._generate_prometheus_config(agent_system),
            "grafana_dashboard": self._generate_grafana_config(agent_system)
        }
        
        return blueprint
    
    def _generate_docker_compose(self, agent_system: AgentSystemDisplay) -> str:
        """Generate Docker Compose configuration."""
        
        compose_config = """version: '3.8'
services:"""
        
        for i, agent in enumerate(agent_system.agent_roles):
            agent_name = agent.name.lower().replace(' ', '-')
            compose_config += f"""
  {agent_name}:
    build: .
    environment:
      - AGENT_ROLE={agent.name}
      - AUTONOMY_LEVEL={agent.autonomy_level}
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis"""
        
        compose_config += """
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
  
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml"""
        
        return compose_config
    
    def _generate_kubernetes_config(self, agent_system: AgentSystemDisplay) -> str:
        """Generate Kubernetes deployment configuration."""
        
        k8s_config = """apiVersion: apps/v1
kind: Deployment
metadata:
  name: agent-system
spec:
  replicas: """ + str(len(agent_system.agent_roles)) + """
  selector:
    matchLabels:
      app: agent-system
  template:
    metadata:
      labels:
        app: agent-system
    spec:
      containers:"""
        
        for agent in agent_system.agent_roles:
            agent_name = agent.name.lower().replace(' ', '-')
            k8s_config += f"""
      - name: {agent_name}
        image: agent-system:latest
        env:
        - name: AGENT_ROLE
          value: "{agent.name}"
        - name: AUTONOMY_LEVEL
          value: "{agent.autonomy_level}"
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m" """
        
        return k8s_config
    
    def _generate_env_config(self, agent_system: AgentSystemDisplay) -> Dict[str, str]:
        """Generate environment configuration."""
        
        return {
            "AGENT_SYSTEM_TYPE": agent_system.coordination.architecture_type if agent_system.coordination else "single_agent",
            "AGENT_COUNT": str(len(agent_system.agent_roles)),
            "SYSTEM_AUTONOMY_SCORE": str(agent_system.system_autonomy_score),
            "REDIS_URL": "redis://localhost:6379",
            "LOG_LEVEL": "INFO",
            "MONITORING_ENABLED": "true"
        }
    
    def _generate_prometheus_config(self, agent_system: AgentSystemDisplay) -> str:
        """Generate Prometheus monitoring configuration."""
        
        return """global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agent-metrics'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['localhost:6379']"""
    
    def _generate_grafana_config(self, agent_system: AgentSystemDisplay) -> Dict[str, Any]:
        """Generate Grafana dashboard configuration."""
        
        return {
            "dashboard": {
                "title": "Agent System Performance",
                "panels": [
                    {
                        "title": "Agent Response Time",
                        "type": "graph",
                        "targets": [{"expr": "agent_response_time_seconds"}]
                    },
                    {
                        "title": "Decision Accuracy",
                        "type": "stat",
                        "targets": [{"expr": "agent_decision_accuracy_ratio"}]
                    },
                    {
                        "title": "System Autonomy Score",
                        "type": "gauge",
                        "targets": [{"expr": "agent_system_autonomy_score"}]
                    }
                ]
            }
        }