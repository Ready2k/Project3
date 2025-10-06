"""Deployment guidance generator for agentic systems."""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

from app.services.multi_agent_designer import MultiAgentSystemDesign, AgentArchitectureType
from app.services.tech_stack_enhancer import TechStackValidationResult


class DeploymentComplexity(Enum):
    """Deployment complexity levels."""
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    ENTERPRISE = "enterprise"


@dataclass
class DeploymentTemplate:
    """Deployment template with configuration examples."""
    name: str
    description: str
    architecture_type: str
    config_files: Dict[str, str]
    setup_commands: List[str]
    monitoring_setup: List[str]
    scaling_instructions: List[str]


@dataclass
class InfrastructureRecommendation:
    """Infrastructure sizing recommendation."""
    component: str
    minimum_specs: Dict[str, str]
    recommended_specs: Dict[str, str]
    scaling_considerations: List[str]
    cost_estimate: str


@dataclass
class DeploymentGuidance:
    """Complete deployment guidance package."""
    complexity_level: DeploymentComplexity
    estimated_setup_time: str
    infrastructure_recommendations: List[InfrastructureRecommendation]
    deployment_templates: List[DeploymentTemplate]
    step_by_step_guide: List[Dict[str, str]]
    monitoring_setup: Dict[str, Any]
    operational_guidance: Dict[str, Any]
    troubleshooting_guide: List[Dict[str, str]]


class DeploymentGuideGenerator:
    """Generates comprehensive deployment guidance for agentic systems."""
    
    def __init__(self):
        self.deployment_templates = {
            "single_agent": self._get_single_agent_template(),
            "multi_agent_collaborative": self._get_multi_agent_template(),
            "hierarchical_agents": self._get_hierarchical_template(),
            "swarm_intelligence": self._get_swarm_template()
        }
        
        self.infrastructure_baselines = {
            "single_agent": {
                "cpu": "2-4 cores",
                "memory": "4-8 GB",
                "storage": "20-50 GB",
                "network": "Standard bandwidth"
            },
            "multi_agent": {
                "cpu": "4-8 cores per agent",
                "memory": "8-16 GB per agent",
                "storage": "50-100 GB shared",
                "network": "High bandwidth for coordination"
            },
            "coordinator": {
                "cpu": "8-16 cores",
                "memory": "16-32 GB",
                "storage": "100-200 GB",
                "network": "Very high bandwidth"
            }
        }
    
    def generate_deployment_guidance(self, 
                                   agent_design: MultiAgentSystemDesign,
                                   tech_validation: TechStackValidationResult,
                                   requirements: Dict[str, Any]) -> DeploymentGuidance:
        """Generate comprehensive deployment guidance."""
        
        self.logger.info("Generating deployment guidance for agent system")
        
        # Determine deployment complexity
        complexity = self._assess_deployment_complexity(agent_design, tech_validation)
        
        # Generate infrastructure recommendations
        infra_recommendations = self._generate_infrastructure_recommendations(
            agent_design, complexity
        )
        
        # Create deployment templates
        templates = self._create_deployment_templates(agent_design, tech_validation)
        
        # Generate step-by-step guide
        step_guide = self._generate_step_by_step_guide(
            agent_design, tech_validation, complexity
        )
        
        # Create monitoring setup
        monitoring_setup = self._generate_monitoring_setup(agent_design)
        
        # Generate operational guidance
        operational_guidance = self._generate_operational_guidance(agent_design)
        
        # Create troubleshooting guide
        troubleshooting_guide = self._generate_troubleshooting_guide(agent_design)
        
        # Estimate setup time
        setup_time = self._estimate_detailed_setup_time(complexity, agent_design, tech_validation)
        
        guidance = DeploymentGuidance(
            complexity_level=complexity,
            estimated_setup_time=setup_time,
            infrastructure_recommendations=infra_recommendations,
            deployment_templates=templates,
            step_by_step_guide=step_guide,
            monitoring_setup=monitoring_setup,
            operational_guidance=operational_guidance,
            troubleshooting_guide=troubleshooting_guide
        )
        
        self.logger.info(f"Deployment guidance generated: {complexity.value} complexity, {setup_time} setup time")
        
        return guidance
    
    def _assess_deployment_complexity(self, 
                                    agent_design: MultiAgentSystemDesign,
                                    tech_validation: TechStackValidationResult) -> DeploymentComplexity:
        """Assess deployment complexity based on system characteristics."""
        
        complexity_score = 0
        
        # Agent count factor
        agent_count = len(agent_design.agent_roles)
        if agent_count == 1:
            complexity_score += 1
        elif agent_count <= 3:
            complexity_score += 2
        elif agent_count <= 6:
            complexity_score += 3
        else:
            complexity_score += 4
        
        # Architecture complexity
        if agent_design.architecture_type == AgentArchitectureType.SINGLE_AGENT:
            complexity_score += 1
        elif agent_design.architecture_type == AgentArchitectureType.COORDINATOR_BASED:
            complexity_score += 2
        elif agent_design.architecture_type == AgentArchitectureType.PEER_TO_PEER:
            complexity_score += 3
        else:  # Hierarchical or Swarm
            complexity_score += 4
        
        # Autonomy level factor
        avg_autonomy = sum(role.autonomy_level for role in agent_design.agent_roles) / len(agent_design.agent_roles)
        if avg_autonomy > 0.8:
            complexity_score += 2
        elif avg_autonomy > 0.6:
            complexity_score += 1
        
        # Tech stack readiness
        if not tech_validation.is_deployment_ready:
            complexity_score += 2
        
        if tech_validation.readiness_score < 0.5:
            complexity_score += 1
        
        # Missing components
        if len(tech_validation.missing_critical_components) > 2:
            complexity_score += 2
        elif len(tech_validation.missing_critical_components) > 0:
            complexity_score += 1
        
        # Map score to complexity level
        if complexity_score <= 4:
            return DeploymentComplexity.SIMPLE
        elif complexity_score <= 7:
            return DeploymentComplexity.MODERATE
        elif complexity_score <= 10:
            return DeploymentComplexity.COMPLEX
        else:
            return DeploymentComplexity.ENTERPRISE
    
    def _generate_infrastructure_recommendations(self, 
                                               agent_design: MultiAgentSystemDesign,
                                               complexity: DeploymentComplexity) -> List[InfrastructureRecommendation]:
        """Generate infrastructure sizing recommendations."""
        
        recommendations = []
        
        # Compute recommendations
        if len(agent_design.agent_roles) == 1:
            baseline = self.infrastructure_baselines["single_agent"]
        elif agent_design.architecture_type == AgentArchitectureType.COORDINATOR_BASED:
            baseline = self.infrastructure_baselines["coordinator"]
        else:
            baseline = self.infrastructure_baselines["multi_agent"]
        
        # Adjust for complexity
        multiplier = {
            DeploymentComplexity.SIMPLE: 1.0,
            DeploymentComplexity.MODERATE: 1.5,
            DeploymentComplexity.COMPLEX: 2.0,
            DeploymentComplexity.ENTERPRISE: 3.0
        }[complexity]
        
        # CPU recommendation
        recommendations.append(InfrastructureRecommendation(
            component="Compute (CPU)",
            minimum_specs={"cores": baseline["cpu"]},
            recommended_specs={"cores": f"{int(baseline['cpu'].split('-')[0]) * multiplier:.0f}-{int(baseline['cpu'].split('-')[1].split()[0]) * multiplier:.0f} cores"},
            scaling_considerations=[
                "Scale horizontally by adding agent instances",
                "Monitor CPU utilization during reasoning tasks",
                "Consider GPU acceleration for complex reasoning"
            ],
            cost_estimate="$50-200/month per agent instance"
        ))
        
        # Memory recommendation
        recommendations.append(InfrastructureRecommendation(
            component="Memory (RAM)",
            minimum_specs={"memory": baseline["memory"]},
            recommended_specs={"memory": f"{int(baseline['memory'].split('-')[0]) * multiplier:.0f}-{int(baseline['memory'].split('-')[1].split()[0]) * multiplier:.0f} GB"},
            scaling_considerations=[
                "Agent state and knowledge storage requires significant memory",
                "Vector databases need memory for embeddings",
                "Consider memory-optimized instances for large knowledge bases"
            ],
            cost_estimate="$20-100/month per agent instance"
        ))
        
        # Storage recommendation
        recommendations.append(InfrastructureRecommendation(
            component="Storage",
            minimum_specs={"storage": baseline["storage"]},
            recommended_specs={"storage": f"{int(baseline['storage'].split('-')[0]) * multiplier:.0f}-{int(baseline['storage'].split('-')[1].split()[0]) * multiplier:.0f} GB SSD"},
            scaling_considerations=[
                "Use SSD for agent state and logs",
                "Separate storage for knowledge bases and embeddings",
                "Implement backup strategy for agent learning data"
            ],
            cost_estimate="$10-50/month per agent instance"
        ))
        
        # Network recommendation
        recommendations.append(InfrastructureRecommendation(
            component="Network",
            minimum_specs={"bandwidth": "100 Mbps"},
            recommended_specs={"bandwidth": "1 Gbps+ for multi-agent coordination"},
            scaling_considerations=[
                "Low latency critical for agent coordination",
                "High bandwidth needed for knowledge sharing",
                "Consider dedicated network for agent communication"
            ],
            cost_estimate="$20-100/month depending on provider"
        ))
        
        return recommendations
    
    def _create_deployment_templates(self, 
                                   agent_design: MultiAgentSystemDesign,
                                   tech_validation: TechStackValidationResult) -> List[DeploymentTemplate]:
        """Create deployment templates with configuration examples."""
        
        templates = []
        architecture_key = agent_design.architecture_type.value
        
        # Get base template
        if architecture_key in self.deployment_templates:
            base_template = self.deployment_templates[architecture_key]
            templates.append(base_template)
        
        # Add monitoring template
        monitoring_template = DeploymentTemplate(
            name="Agent Monitoring Setup",
            description="Comprehensive monitoring for agent performance and health",
            architecture_type="monitoring",
            config_files={
                "prometheus.yml": self._get_prometheus_config(),
                "grafana-dashboard.json": self._get_grafana_dashboard_config(),
                "docker-compose.monitoring.yml": self._get_monitoring_docker_compose()
            },
            setup_commands=[
                "docker-compose -f docker-compose.monitoring.yml up -d",
                "curl -X POST http://localhost:3000/api/dashboards/db -d @grafana-dashboard.json"
            ],
            monitoring_setup=[
                "Configure Prometheus to scrape agent metrics",
                "Import Grafana dashboard for agent visualization",
                "Set up alerting rules for agent failures"
            ],
            scaling_instructions=[
                "Add monitoring for each new agent instance",
                "Configure service discovery for dynamic agents",
                "Scale monitoring infrastructure with agent count"
            ]
        )
        templates.append(monitoring_template)
        
        return templates
    
    def _generate_step_by_step_guide(self, 
                                    agent_design: MultiAgentSystemDesign,
                                    tech_validation: TechStackValidationResult,
                                    complexity: DeploymentComplexity) -> List[Dict[str, str]]:
        """Generate step-by-step deployment guide."""
        
        steps = []
        
        # Step 1: Environment Setup
        steps.append({
            "step": "1",
            "title": "Environment Setup",
            "description": "Prepare the deployment environment and install prerequisites",
            "commands": [
                "# Install Docker and Docker Compose",
                "curl -fsSL https://get.docker.com -o get-docker.sh",
                "sh get-docker.sh",
                "# Install Python 3.10+",
                "python3 --version",
                "pip install --upgrade pip"
            ],
            "validation": "Verify Docker and Python installations are working"
        })
        
        # Step 2: Install Agent Framework
        if tech_validation.missing_critical_components:
            steps.append({
                "step": "2",
                "title": "Install Agent Framework",
                "description": "Install required agent deployment framework",
                "commands": [
                    "# Install LangChain (recommended)",
                    "pip install langchain langchain-community",
                    "# Or install CrewAI for multi-agent systems",
                    "pip install crewai",
                    "# Install vector database",
                    "pip install pinecone-client  # or chromadb"
                ],
                "validation": "Test framework installation with simple agent creation"
            })
        
        # Step 3: Configure Infrastructure
        steps.append({
            "step": "3",
            "title": "Configure Infrastructure",
            "description": "Set up infrastructure components for agent deployment",
            "commands": [
                "# Start Redis for agent state management",
                "docker run -d --name agent-redis -p 6379:6379 redis:alpine",
                "# Start monitoring stack",
                "docker-compose -f monitoring/docker-compose.yml up -d"
            ],
            "validation": "Verify all infrastructure services are running and accessible"
        })
        
        # Step 4: Deploy Agents
        steps.append({
            "step": "4",
            "title": "Deploy Agent System",
            "description": f"Deploy {agent_design.architecture_type.value} agent system",
            "commands": [
                "# Build agent application",
                "docker build -t agent-system .",
                "# Deploy agent containers",
                "docker-compose up -d",
                "# Verify agent startup",
                "docker logs agent-system"
            ],
            "validation": "Check agent logs for successful initialization and health checks"
        })
        
        # Step 5: Configure Monitoring
        steps.append({
            "step": "5",
            "title": "Configure Monitoring",
            "description": "Set up comprehensive monitoring for agent performance",
            "commands": [
                "# Import Grafana dashboards",
                "curl -X POST http://localhost:3000/api/dashboards/db -d @dashboards/agent-dashboard.json",
                "# Configure alerting rules",
                "docker exec prometheus promtool check rules /etc/prometheus/alert.rules"
            ],
            "validation": "Verify metrics are being collected and dashboards are accessible"
        })
        
        # Step 6: Test Agent System
        steps.append({
            "step": "6",
            "title": "Test Agent System",
            "description": "Perform end-to-end testing of agent functionality",
            "commands": [
                "# Run agent health checks",
                "curl http://localhost:8000/health",
                "# Test agent coordination (multi-agent systems)",
                "python test_agent_coordination.py",
                "# Load test agent performance",
                "python load_test_agents.py"
            ],
            "validation": "Verify all agents respond correctly and coordination works as expected"
        })
        
        return steps
    
    def _generate_monitoring_setup(self, agent_design: MultiAgentSystemDesign) -> Dict[str, Any]:
        """Generate monitoring setup configuration."""
        
        return {
            "metrics_to_track": [
                "Agent response time",
                "Decision accuracy rate",
                "Task completion rate",
                "Error rate and types",
                "Resource utilization (CPU, Memory)",
                "Inter-agent communication latency",
                "Autonomy score trends",
                "Exception handling success rate"
            ],
            "alerting_rules": [
                {
                    "name": "Agent Down",
                    "condition": "Agent health check fails for > 2 minutes",
                    "severity": "critical"
                },
                {
                    "name": "High Error Rate",
                    "condition": "Agent error rate > 5% for 5 minutes",
                    "severity": "warning"
                },
                {
                    "name": "Low Autonomy Score",
                    "condition": "Agent autonomy score drops below 0.7",
                    "severity": "warning"
                }
            ],
            "dashboards": [
                "Agent Performance Overview",
                "Multi-Agent Coordination Metrics",
                "Resource Utilization Trends",
                "Error Analysis and Debugging"
            ],
            "log_aggregation": {
                "tool": "ELK Stack or Grafana Loki",
                "retention": "30 days for debug logs, 90 days for audit logs",
                "structured_logging": "JSON format with agent_id, timestamp, level, message"
            }
        }
    
    def _generate_operational_guidance(self, agent_design: MultiAgentSystemDesign) -> Dict[str, Any]:
        """Generate operational guidance for running agent systems."""
        
        return {
            "daily_operations": [
                "Check agent health dashboards",
                "Review error logs and resolution status",
                "Monitor resource utilization trends",
                "Verify backup completion status"
            ],
            "weekly_operations": [
                "Review agent performance metrics",
                "Analyze autonomy score trends",
                "Update agent knowledge bases",
                "Test disaster recovery procedures"
            ],
            "monthly_operations": [
                "Performance optimization review",
                "Security audit and updates",
                "Capacity planning assessment",
                "Agent learning effectiveness analysis"
            ],
            "scaling_procedures": {
                "horizontal_scaling": [
                    "Add new agent instances behind load balancer",
                    "Update service discovery configuration",
                    "Monitor coordination overhead"
                ],
                "vertical_scaling": [
                    "Increase CPU/memory for existing agents",
                    "Monitor performance improvement",
                    "Adjust resource limits in containers"
                ]
            },
            "backup_strategy": {
                "agent_state": "Daily incremental, weekly full backup",
                "knowledge_bases": "Real-time replication to secondary storage",
                "configuration": "Version controlled in Git repository",
                "logs": "Archived to long-term storage after 30 days"
            }
        }
    
    def _generate_troubleshooting_guide(self, agent_design: MultiAgentSystemDesign) -> List[Dict[str, str]]:
        """Generate troubleshooting guide for common issues."""
        
        return [
            {
                "issue": "Agent Not Responding",
                "symptoms": "Health checks failing, no response to requests",
                "diagnosis": "Check agent logs, verify resource availability, test network connectivity",
                "resolution": "Restart agent service, check configuration, verify dependencies"
            },
            {
                "issue": "High Response Latency",
                "symptoms": "Slow agent responses, timeout errors",
                "diagnosis": "Monitor CPU/memory usage, check reasoning complexity, analyze network latency",
                "resolution": "Scale resources, optimize reasoning logic, improve network configuration"
            },
            {
                "issue": "Agent Coordination Failures",
                "symptoms": "Agents not communicating, coordination timeouts",
                "diagnosis": "Check message queue status, verify network connectivity, review coordination logs",
                "resolution": "Restart coordination services, check network configuration, verify agent discovery"
            },
            {
                "issue": "Low Autonomy Performance",
                "symptoms": "Frequent escalations, poor decision quality",
                "diagnosis": "Review decision logs, analyze reasoning patterns, check knowledge base quality",
                "resolution": "Update knowledge bases, retrain decision models, adjust autonomy thresholds"
            },
            {
                "issue": "Resource Exhaustion",
                "symptoms": "Out of memory errors, CPU throttling",
                "diagnosis": "Monitor resource usage trends, identify memory leaks, check for runaway processes",
                "resolution": "Scale infrastructure, optimize memory usage, implement resource limits"
            }
        ]
    
    def _estimate_detailed_setup_time(self, 
                                    complexity: DeploymentComplexity,
                                    agent_design: MultiAgentSystemDesign,
                                    tech_validation: TechStackValidationResult) -> str:
        """Estimate detailed setup time based on complexity factors."""
        
        base_times = {
            DeploymentComplexity.SIMPLE: 3,      # 3 days
            DeploymentComplexity.MODERATE: 7,    # 1 week
            DeploymentComplexity.COMPLEX: 14,    # 2 weeks
            DeploymentComplexity.ENTERPRISE: 30  # 1 month
        }
        
        base_time = base_times[complexity]
        
        # Add time for missing components
        missing_count = len(tech_validation.missing_critical_components)
        base_time += missing_count * 2  # 2 days per missing component
        
        # Add time for low readiness
        if tech_validation.readiness_score < 0.5:
            base_time += 5  # Additional week for setup
        
        # Add time for high autonomy (more testing needed)
        avg_autonomy = sum(role.autonomy_level for role in agent_design.agent_roles) / len(agent_design.agent_roles)
        if avg_autonomy > 0.8:
            base_time += 3  # Additional 3 days for testing
        
        # Convert to human-readable format
        if base_time <= 5:
            return f"{base_time} days"
        elif base_time <= 14:
            return f"{base_time // 7} week{'s' if base_time // 7 > 1 else ''}"
        elif base_time <= 60:
            return f"{base_time // 30} month{'s' if base_time // 30 > 1 else ''}"
        else:
            return f"{base_time // 30} months"
    
    # Template methods for different architectures
    def _get_single_agent_template(self) -> DeploymentTemplate:
        """Get deployment template for single agent systems."""
        
        return DeploymentTemplate(
            name="Single Agent Deployment",
            description="Simple deployment template for single autonomous agent",
            architecture_type="single_agent",
            config_files={
                "docker-compose.yml": """
version: '3.8'
services:
  agent:
    build: .
    ports:
      - "8000:8000"
    environment:
      - REDIS_URL=redis://redis:6379
      - LOG_LEVEL=INFO
    depends_on:
      - redis
  
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
""",
                "Dockerfile": """
FROM python:3.10-slim
WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt
COPY . .
CMD ["python", "agent_main.py"]
"""
            },
            setup_commands=[
                "docker-compose up -d",
                "docker logs agent_agent_1"
            ],
            monitoring_setup=[
                "Configure health check endpoint",
                "Set up basic metrics collection",
                "Monitor agent response times"
            ],
            scaling_instructions=[
                "Scale horizontally with load balancer",
                "Monitor resource usage",
                "Implement circuit breakers"
            ]
        )
    
    def _get_multi_agent_template(self) -> DeploymentTemplate:
        """Get deployment template for multi-agent systems."""
        
        return DeploymentTemplate(
            name="Multi-Agent Collaborative Deployment",
            description="Deployment template for collaborative multi-agent system",
            architecture_type="multi_agent_collaborative",
            config_files={
                "docker-compose.yml": """
version: '3.8'
services:
  agent-1:
    build: .
    environment:
      - AGENT_ROLE=specialist
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - message-queue
  
  agent-2:
    build: .
    environment:
      - AGENT_ROLE=validator
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - message-queue
  
  redis:
    image: redis:alpine
  
  message-queue:
    image: rabbitmq:management
    ports:
      - "15672:15672"
"""
            },
            setup_commands=[
                "docker-compose up -d",
                "docker-compose logs -f"
            ],
            monitoring_setup=[
                "Monitor inter-agent communication",
                "Track coordination metrics",
                "Set up message queue monitoring"
            ],
            scaling_instructions=[
                "Add new agent services to compose file",
                "Configure service discovery",
                "Monitor coordination overhead"
            ]
        )
    
    def _get_hierarchical_template(self) -> DeploymentTemplate:
        """Get deployment template for hierarchical agent systems."""
        
        return DeploymentTemplate(
            name="Hierarchical Agent Deployment",
            description="Deployment template for hierarchical agent architecture",
            architecture_type="hierarchical_agents",
            config_files={
                "docker-compose.yml": """
version: '3.8'
services:
  coordinator:
    build: .
    ports:
      - "8000:8000"
    environment:
      - AGENT_ROLE=coordinator
      - REDIS_URL=redis://redis:6379
    depends_on:
      - redis
      - workflow-engine
  
  specialist-1:
    build: .
    environment:
      - AGENT_ROLE=specialist
      - COORDINATOR_URL=http://coordinator:8000
    depends_on:
      - coordinator
  
  workflow-engine:
    image: apache/airflow:2.5.0
    environment:
      - AIRFLOW__CORE__EXECUTOR=LocalExecutor
"""
            },
            setup_commands=[
                "docker-compose up -d coordinator",
                "sleep 30",
                "docker-compose up -d"
            ],
            monitoring_setup=[
                "Monitor coordinator performance",
                "Track hierarchy communication",
                "Set up workflow monitoring"
            ],
            scaling_instructions=[
                "Scale specialist agents independently",
                "Monitor coordinator bottlenecks",
                "Implement load balancing"
            ]
        )
    
    def _get_swarm_template(self) -> DeploymentTemplate:
        """Get deployment template for swarm intelligence systems."""
        
        return DeploymentTemplate(
            name="Swarm Intelligence Deployment",
            description="Deployment template for swarm-based agent system",
            architecture_type="swarm_intelligence",
            config_files={
                "docker-compose.yml": """
version: '3.8'
services:
  swarm-agent:
    build: .
    deploy:
      replicas: 5
    environment:
      - SWARM_MODE=true
      - DISCOVERY_SERVICE=consul://consul:8500
    depends_on:
      - consul
  
  consul:
    image: consul:latest
    ports:
      - "8500:8500"
    command: agent -server -bootstrap -ui -client=0.0.0.0
"""
            },
            setup_commands=[
                "docker swarm init",
                "docker stack deploy -c docker-compose.yml swarm-agents"
            ],
            monitoring_setup=[
                "Monitor swarm coordination",
                "Track emergent behavior metrics",
                "Set up distributed tracing"
            ],
            scaling_instructions=[
                "Scale swarm replicas dynamically",
                "Monitor coordination efficiency",
                "Implement auto-scaling policies"
            ]
        )
    
    def _get_prometheus_config(self) -> str:
        """Get Prometheus configuration for agent monitoring."""
        
        return """
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'agent-metrics'
    static_configs:
      - targets: ['agent:8000']
    metrics_path: /metrics
    scrape_interval: 5s

  - job_name: 'redis'
    static_configs:
      - targets: ['redis:6379']

rule_files:
  - "alert.rules"

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093
"""
    
    def _get_grafana_dashboard_config(self) -> str:
        """Get Grafana dashboard configuration for agents."""
        
        return """
{
  "dashboard": {
    "title": "Agent Performance Dashboard",
    "panels": [
      {
        "title": "Agent Response Time",
        "type": "graph",
        "targets": [
          {
            "expr": "agent_response_time_seconds",
            "legendFormat": "{{agent_id}}"
          }
        ]
      },
      {
        "title": "Decision Accuracy",
        "type": "stat",
        "targets": [
          {
            "expr": "agent_decision_accuracy_ratio",
            "legendFormat": "Accuracy"
          }
        ]
      }
    ]
  }
}
"""
    
    def _get_monitoring_docker_compose(self) -> str:
        """Get Docker Compose configuration for monitoring stack."""
        
        return """
version: '3.8'
services:
  prometheus:
    image: prom/prometheus
    ports:
      - "9090:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
  
  grafana:
    image: grafana/grafana
    ports:
      - "3000:3000"
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    volumes:
      - grafana-storage:/var/lib/grafana

volumes:
  grafana-storage:
"""