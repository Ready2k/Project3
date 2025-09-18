"""Agent data formatter for UI display of agentic agent roles and coordination."""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from enum import Enum

from app.services.multi_agent_designer import MultiAgentSystemDesign, AgentRole
from app.utils.imports import require_service, optional_service


class AutonomyLevel(Enum):
    """Autonomy level classifications with descriptions."""
    MANUAL = (0.0, 0.3, "Manual", "Primarily human-driven with AI assistance")
    ASSISTED = (0.3, 0.5, "Assisted", "Significant human oversight required")
    SEMI_AUTONOMOUS = (0.5, 0.7, "Semi-Autonomous", "Requires periodic human guidance")
    HIGHLY_AUTONOMOUS = (0.7, 0.9, "Highly Autonomous", "Makes most decisions independently")
    FULLY_AUTONOMOUS = (0.9, 1.0, "Fully Autonomous", "Operates independently with minimal oversight")

    def __init__(self, min_val: float, max_val: float, name: str, description: str):
        self.min_val = min_val
        self.max_val = max_val
        self.display_name = name
        self.description = description

    @classmethod
    def from_score(cls, score: float) -> 'AutonomyLevel':
        """Get autonomy level from score."""
        for level in cls:
            if level.min_val <= score < level.max_val:
                return level
        return cls.FULLY_AUTONOMOUS if score >= 0.9 else cls.MANUAL


@dataclass
class AgentRoleDisplay:
    """Formatted agent role data for UI display."""
    name: str
    responsibility: str
    autonomy_level: float
    autonomy_description: str
    capabilities: List[str]
    decision_authority: Dict[str, Any]
    decision_boundaries: List[str]
    learning_capabilities: List[str]
    exception_handling: str
    communication_requirements: List[str]
    performance_metrics: List[str]
    infrastructure_requirements: Dict[str, Any]
    security_requirements: List[str]


@dataclass
class AgentCoordinationDisplay:
    """Formatted coordination data for UI display."""
    architecture_type: str
    architecture_description: str
    communication_protocols: List[Dict[str, str]]
    coordination_mechanisms: List[Dict[str, str]]
    interaction_patterns: List[Dict[str, Any]]
    conflict_resolution: str
    workflow_distribution: Dict[str, Any]


@dataclass
class AgentSystemDisplay:
    """Complete agent system display data."""
    has_agents: bool
    system_autonomy_score: float
    agent_roles: List[AgentRoleDisplay]
    coordination: Optional[AgentCoordinationDisplay]
    deployment_requirements: Dict[str, Any]
    tech_stack_validation: Dict[str, Any]
    implementation_guidance: List[Dict[str, str]]


class AgentDataFormatter:
    """Formats agent system design data for UI display."""
    
    def __init__(self):
        # Performance optimization: cache for formatted data
        self._format_cache = {}
        self._cache_max_size = 100
        
        self.autonomy_descriptions = {
            (0.9, 1.0): "Fully Autonomous - Operates independently with minimal oversight",
            (0.7, 0.9): "Highly Autonomous - Makes most decisions independently",
            (0.5, 0.7): "Semi-Autonomous - Requires periodic human guidance",
            (0.3, 0.5): "Assisted - Significant human oversight required",
            (0.0, 0.3): "Manual - Primarily human-driven with AI assistance"
        }
        
        self.architecture_descriptions = {
            "hierarchical": "Structured command hierarchy with clear reporting relationships",
            "peer_to_peer": "Collaborative agents with equal authority and shared decision-making",
            "coordinator_based": "Central coordinator manages and orchestrates worker agents",
            "swarm_intelligence": "Distributed agents with emergent collective behavior"
        }
    
    def format_agent_system(self, 
                           agent_design: Optional[MultiAgentSystemDesign],
                           tech_stack: List[str],
                           session_data: Dict[str, Any]) -> AgentSystemDisplay:
        """Format complete agent system for UI display with caching."""
        
        # Performance optimization: check cache first
        cache_key = self._generate_cache_key(agent_design, tech_stack, session_data)
        if cache_key in self._format_cache:
            app_logger.debug("Using cached agent system format")
            return self._format_cache[cache_key]
        
        # Get logger service
        app_logger = require_service('logger', context="format_agent_system")
        app_logger.info("Formatting agent system for UI display")
        
        if not agent_design:
            app_logger.debug("No agent design provided, returning empty display")
            empty_display = AgentSystemDisplay(
                has_agents=False,
                system_autonomy_score=0.0,
                agent_roles=[],
                coordination=None,
                deployment_requirements={},
                tech_stack_validation={},
                implementation_guidance=[]
            )
            self._cache_result(cache_key, empty_display)
            return empty_display
        
        try:
            # Format individual agent roles
            formatted_roles = [
                self._format_agent_role(role) for role in agent_design.agent_roles
            ]
            
            # Format coordination information
            coordination = self._format_coordination(agent_design)
            
            # Validate and enhance tech stack for agent deployment
            tech_validation = self._validate_tech_stack_for_agents(
                tech_stack, agent_design
            )
            
            # Generate deployment requirements
            deployment_reqs = self._generate_deployment_requirements(agent_design)
            
            # Create implementation guidance
            implementation_guide = self._generate_implementation_guidance(
                agent_design, tech_validation
            )
            
            result = AgentSystemDisplay(
                has_agents=True,
                system_autonomy_score=agent_design.autonomy_score,
                agent_roles=formatted_roles,
                coordination=coordination,
                deployment_requirements=deployment_reqs,
                tech_stack_validation=tech_validation,
                implementation_guidance=implementation_guide
            )
            
            app_logger.info(f"Formatted agent system with {len(formatted_roles)} agents, autonomy={agent_design.autonomy_score:.2f}")
            
            # Cache the result for performance
            self._cache_result(cache_key, result)
            return result
            
        except Exception as e:
            app_logger.error(f"Error formatting agent system: {e}")
            return self._create_error_display(str(e))
    
    def _generate_cache_key(self, agent_design: Optional[MultiAgentSystemDesign], 
                           tech_stack: List[str], session_data: Dict[str, Any]) -> str:
        """Generate cache key for performance optimization."""
        
        import hashlib
        
        # Create a hash of the input parameters
        key_data = {
            "agent_design_id": id(agent_design) if agent_design else None,
            "tech_stack": sorted(tech_stack),
            "session_id": session_data.get("session_id", "")
        }
        
        key_string = str(key_data)
        return hashlib.md5(key_string.encode()).hexdigest()
    
    def _cache_result(self, cache_key: str, result: AgentSystemDisplay):
        """Cache the formatting result for performance."""
        
        # Implement LRU cache behavior
        if len(self._format_cache) >= self._cache_max_size:
            # Remove oldest entry
            oldest_key = next(iter(self._format_cache))
            del self._format_cache[oldest_key]
        
        self._format_cache[cache_key] = result
    
    def _format_agent_role(self, role: AgentRole) -> AgentRoleDisplay:
        """Format individual agent role for display."""
        
        # Get human-readable autonomy description
        autonomy_desc = self._get_autonomy_description(role.autonomy_level)
        
        # Format decision boundaries
        decision_boundaries = self._format_decision_boundaries(role.decision_authority)
        
        # Extract communication requirements
        comm_requirements = self._extract_communication_requirements(role)
        
        # Generate performance metrics
        performance_metrics = self._generate_performance_metrics(role)
        
        # Determine infrastructure requirements
        infra_requirements = self._determine_infrastructure_requirements(role)
        
        # Extract security requirements
        security_requirements = self._extract_security_requirements(role)
        
        return AgentRoleDisplay(
            name=role.name,
            responsibility=role.responsibility,
            autonomy_level=role.autonomy_level,
            autonomy_description=autonomy_desc,
            capabilities=role.capabilities,
            decision_authority=role.decision_authority,
            decision_boundaries=decision_boundaries,
            learning_capabilities=role.learning_capabilities,
            exception_handling=role.exception_handling,
            communication_requirements=comm_requirements,
            performance_metrics=performance_metrics,
            infrastructure_requirements=infra_requirements,
            security_requirements=security_requirements
        )
    
    def _format_coordination(self, agent_design: MultiAgentSystemDesign) -> Optional[AgentCoordinationDisplay]:
        """Format coordination information for display."""
        
        if len(agent_design.agent_roles) <= 1:
            return None
        
        # Format communication protocols
        comm_protocols = []
        for protocol in agent_design.communication_protocols:
            comm_protocols.append({
                "type": protocol.protocol_type.value,
                "participants": ", ".join(protocol.participants),
                "format": protocol.message_format,
                "reliability": protocol.reliability_requirements,
                "latency": protocol.latency_requirements
            })
        
        # Format coordination mechanisms
        coord_mechanisms = []
        for mechanism in agent_design.coordination_mechanisms:
            coord_mechanisms.append({
                "type": mechanism.mechanism_type.value,
                "participants": ", ".join(mechanism.participants),
                "criteria": ", ".join(mechanism.decision_criteria),
                "conflict_resolution": mechanism.conflict_resolution,
                "metrics": ", ".join(mechanism.performance_metrics)
            })
        
        # Generate interaction patterns
        interaction_patterns = self._generate_interaction_patterns(agent_design)
        
        # Generate workflow distribution
        workflow_distribution = self._generate_workflow_distribution(agent_design)
        
        return AgentCoordinationDisplay(
            architecture_type=agent_design.architecture_type.value,
            architecture_description=self.architecture_descriptions.get(
                agent_design.architecture_type.value, 
                "Custom agent architecture"
            ),
            communication_protocols=comm_protocols,
            coordination_mechanisms=coord_mechanisms,
            interaction_patterns=interaction_patterns,
            conflict_resolution=coord_mechanisms[0]["conflict_resolution"] if coord_mechanisms else "Standard escalation",
            workflow_distribution=workflow_distribution
        )
    
    def _validate_tech_stack_for_agents(self, 
                                      tech_stack: List[str],
                                      agent_design: MultiAgentSystemDesign) -> Dict[str, Any]:
        """Validate and enhance tech stack for agent deployment."""
        
        validation_result = {
            "is_agent_ready": False,
            "missing_components": [],
            "recommended_additions": [],
            "deployment_frameworks": [],
            "orchestration_tools": [],
            "monitoring_tools": [],
            "reasoning_engines": []
        }
        
        # Check for agent deployment frameworks
        agent_frameworks = ["LangChain", "AutoGPT", "CrewAI", "Microsoft Semantic Kernel", "AutoGen"]
        found_frameworks = [fw for fw in agent_frameworks if fw in tech_stack]
        
        if not found_frameworks:
            validation_result["missing_components"].append("Agent Deployment Framework")
            validation_result["recommended_additions"].extend([
                "LangChain - For flexible agent orchestration",
                "CrewAI - For multi-agent collaboration"
            ])
        else:
            validation_result["deployment_frameworks"] = found_frameworks
        
        # Check for orchestration tools (multi-agent systems)
        if len(agent_design.agent_roles) > 1:
            orchestration_tools = ["Apache Airflow", "Celery", "Redis", "RabbitMQ", "Apache Kafka"]
            found_orchestration = [tool for tool in orchestration_tools if tool in tech_stack]
            
            if not found_orchestration:
                validation_result["missing_components"].append("Agent Orchestration")
                validation_result["recommended_additions"].extend([
                    "Redis - For agent communication and state management",
                    "Celery - For distributed agent task execution"
                ])
            else:
                validation_result["orchestration_tools"] = found_orchestration
        
        # Check for reasoning engines
        reasoning_engines = ["Neo4j", "Elasticsearch", "Pinecone", "Weaviate", "ChromaDB"]
        found_reasoning = [engine for engine in reasoning_engines if engine in tech_stack]
        
        if not found_reasoning:
            validation_result["recommended_additions"].extend([
                "Neo4j - For knowledge graph reasoning",
                "Pinecone - For vector-based reasoning and memory"
            ])
        else:
            validation_result["reasoning_engines"] = found_reasoning
        
        # Check for monitoring tools
        monitoring_tools = ["Prometheus", "Grafana", "DataDog", "New Relic", "LangSmith"]
        found_monitoring = [tool for tool in monitoring_tools if tool in tech_stack]
        
        if not found_monitoring:
            validation_result["recommended_additions"].extend([
                "Prometheus - For agent performance monitoring",
                "Grafana - For agent analytics dashboards"
            ])
        else:
            validation_result["monitoring_tools"] = found_monitoring
        
        # Determine if tech stack is agent-ready
        validation_result["is_agent_ready"] = (
            len(found_frameworks) > 0 and
            (len(agent_design.agent_roles) == 1 or len(found_orchestration) > 0)
        )
        
        return validation_result
    
    def _generate_deployment_requirements(self, agent_design: MultiAgentSystemDesign) -> Dict[str, Any]:
        """Generate deployment requirements for the agent system."""
        
        # Enhanced deployment requirements with more detail
        requirements = {
            "architecture": agent_design.architecture_type.value,
            "agent_count": len(agent_design.agent_roles),
            "deployment_strategy": agent_design.deployment_strategy,
            "scalability_considerations": agent_design.scalability_considerations,
            "monitoring_requirements": agent_design.monitoring_requirements,
            "recommended_frameworks": agent_design.recommended_frameworks,
            "infrastructure_needs": {
                "compute": "Medium to High - Agent reasoning requires significant CPU",
                "memory": "High - Agent state and knowledge storage",
                "storage": "Medium - Agent logs and learning data",
                "network": "Medium - Inter-agent communication"
            }
        }
        
        # Add complexity assessment
        complexity_factors = []
        if len(agent_design.agent_roles) > 3:
            complexity_factors.append("Multiple specialized agents require coordination")
        
        avg_autonomy = sum(role.autonomy_level for role in agent_design.agent_roles) / len(agent_design.agent_roles)
        if avg_autonomy > 0.8:
            complexity_factors.append("High autonomy agents need extensive testing")
        
        if agent_design.architecture_type.value in ["hierarchical_agents", "swarm_intelligence"]:
            complexity_factors.append("Complex architecture requires specialized deployment")
        
        requirements["complexity_factors"] = complexity_factors
        
        # Add estimated timeline
        if len(complexity_factors) == 0:
            requirements["estimated_timeline"] = "1-2 weeks"
        elif len(complexity_factors) <= 2:
            requirements["estimated_timeline"] = "2-4 weeks"
        else:
            requirements["estimated_timeline"] = "1-2 months"
        
        return requirements
    
    def _generate_implementation_guidance(self, 
                                        agent_design: MultiAgentSystemDesign,
                                        tech_validation: Dict[str, Any]) -> List[Dict[str, str]]:
        """Generate implementation guidance for the agent system."""
        
        guidance = []
        
        # Framework selection guidance
        if tech_validation.get("deployment_frameworks"):
            framework = tech_validation["deployment_frameworks"][0]
            guidance.append({
                "type": "framework",
                "title": "Agent Framework Selection",
                "content": f"Use {framework} for agent implementation. "
                          f"This framework supports {agent_design.architecture_type.value} architectures. "
                          f"Install with: pip install {framework.lower().replace(' ', '-')}"
            })
        else:
            guidance.append({
                "type": "framework",
                "title": "Install Agent Framework",
                "content": "Install LangChain for flexible agent orchestration: pip install langchain langchain-community. "
                          "For multi-agent systems, consider CrewAI: pip install crewai"
            })
        
        # Architecture guidance
        guidance.append({
            "type": "architecture",
            "title": "System Architecture",
            "content": f"Implement {agent_design.architecture_type.value.replace('_', ' ').title()} architecture with "
                      f"{len(agent_design.agent_roles)} specialized agents. "
                      f"Deployment strategy: {agent_design.deployment_strategy}"
        })
        
        # Infrastructure setup guidance
        guidance.append({
            "type": "infrastructure",
            "title": "Infrastructure Setup",
            "content": "Set up Redis for agent state management, configure monitoring with Prometheus/Grafana, "
                      "and ensure adequate compute resources for agent reasoning tasks."
        })
        
        # Communication guidance
        if agent_design.communication_protocols:
            protocol = agent_design.communication_protocols[0]
            guidance.append({
                "type": "communication",
                "title": "Agent Communication",
                "content": f"Implement {protocol.protocol_type.value.replace('_', ' ').title()} for agent communication. "
                          f"Use {protocol.message_format} with {protocol.reliability_requirements}. "
                          f"Ensure low latency for coordination: {protocol.latency_requirements}."
            })
        
        # Security guidance
        guidance.append({
            "type": "security",
            "title": "Security Configuration",
            "content": "Implement secure API authentication, encrypt inter-agent communication, "
                      "enable audit logging for all agent decisions, and configure access controls."
        })
        
        # Monitoring guidance
        guidance.append({
            "type": "monitoring",
            "title": "Agent Monitoring",
            "content": "Implement comprehensive monitoring for agent performance, decision quality, "
                      "and inter-agent coordination. Track autonomy metrics, exception handling success rates, "
                      "and resource utilization. Set up alerting for agent failures and performance degradation."
        })
        
        # Testing guidance
        guidance.append({
            "type": "testing",
            "title": "Testing Strategy",
            "content": "Implement unit tests for individual agent functions, integration tests for agent coordination, "
                      "and end-to-end tests for complete workflows. Test exception handling and failover scenarios."
        })
        
        # Deployment guidance
        guidance.append({
            "type": "deployment",
            "title": "Deployment Process",
            "content": "Use containerization (Docker) for consistent deployments, implement health checks, "
                      "configure auto-scaling based on workload, and establish backup/recovery procedures."
        })
        
        return guidance
    
    def _get_autonomy_description(self, autonomy_level: float) -> str:
        """Get human-readable autonomy description."""
        
        for (min_val, max_val), description in self.autonomy_descriptions.items():
            if min_val <= autonomy_level < max_val:
                return description
        
        # Handle edge case for 1.0
        if autonomy_level >= 0.9:
            return self.autonomy_descriptions[(0.9, 1.0)]
        
        return self.autonomy_descriptions[(0.0, 0.3)]
    
    def _format_decision_boundaries(self, decision_authority: Dict[str, Any]) -> List[str]:
        """Format decision boundaries for display."""
        
        boundaries = []
        
        scope = decision_authority.get("scope", "")
        if scope:
            boundaries.append(f"Authority Scope: {scope}")
        
        limits = decision_authority.get("limits", [])
        if limits:
            boundaries.extend([f"Limit: {limit}" for limit in limits])
        
        escalation_triggers = decision_authority.get("escalation_triggers", [])
        if escalation_triggers:
            boundaries.extend([f"Escalate when: {trigger}" for trigger in escalation_triggers])
        
        return boundaries or ["Standard operational decisions within defined parameters"]
    
    def _extract_communication_requirements(self, role: AgentRole) -> List[str]:
        """Extract communication requirements from agent role."""
        
        # Use communication_requirements if available, otherwise infer from interfaces
        if hasattr(role, 'communication_requirements') and role.communication_requirements:
            return role.communication_requirements
        
        # Infer from interfaces
        requirements = []
        interfaces = role.interfaces or {}
        
        if "input" in interfaces:
            requirements.append(f"Receives: {interfaces['input']}")
        
        if "output" in interfaces:
            requirements.append(f"Produces: {interfaces['output']}")
        
        return requirements or ["Standard inter-agent communication protocols"]
    
    def _generate_performance_metrics(self, role: AgentRole) -> List[str]:
        """Generate performance metrics for agent role."""
        
        # Core performance metrics
        metrics = [
            "Task completion rate (%)",
            "Decision accuracy (%)",
            "Average response time (ms)",
            "Error rate (%)",
            "Uptime availability (%)"
        ]
        
        # Add autonomy-specific metrics
        if role.autonomy_level > 0.8:
            metrics.extend([
                "Autonomous decision success rate (%)",
                "Exception resolution without escalation (%)",
                "Learning adaptation effectiveness (%)"
            ])
        elif role.autonomy_level > 0.6:
            metrics.extend([
                "Semi-autonomous decision accuracy (%)",
                "Human intervention frequency"
            ])
        
        # Add role-specific metrics
        if "coordinator" in role.name.lower():
            metrics.extend([
                "Coordination efficiency score",
                "Resource utilization optimization (%)",
                "Agent synchronization latency (ms)",
                "Workflow orchestration success rate (%)"
            ])
        
        if "specialist" in role.name.lower():
            metrics.extend([
                "Domain expertise accuracy (%)",
                "Specialized task quality score",
                "Knowledge application effectiveness (%)"
            ])
        
        if "monitor" in role.name.lower():
            metrics.extend([
                "Alert accuracy and precision (%)",
                "Detection latency (ms)",
                "False positive rate (%)",
                "System health prediction accuracy (%)"
            ])
        
        if "validator" in role.name.lower():
            metrics.extend([
                "Validation accuracy (%)",
                "Quality assurance score",
                "Defect detection rate (%)"
            ])
        
        # Add capability-specific metrics
        if "api_integration" in role.capabilities:
            metrics.extend([
                "API call success rate (%)",
                "Integration reliability score"
            ])
        
        if "data_processing" in role.capabilities:
            metrics.extend([
                "Data processing throughput (records/min)",
                "Data quality score (%)"
            ])
        
        if "learning" in role.capabilities or role.learning_capabilities:
            metrics.extend([
                "Learning curve progression",
                "Knowledge retention score (%)",
                "Adaptation speed (time to proficiency)"
            ])
        
        return metrics
    
    def _determine_infrastructure_requirements(self, role: AgentRole) -> Dict[str, Any]:
        """Determine infrastructure requirements for agent role."""
        
        # Base requirements
        requirements = {
            "cpu": "2-4 cores",
            "memory": "4-8 GB",
            "storage": "10-50 GB",
            "network": "Standard bandwidth"
        }
        
        # Adjust based on role complexity
        if role.autonomy_level > 0.8:
            requirements["cpu"] = "4-8 cores"
            requirements["memory"] = "8-16 GB"
        
        if "coordinator" in role.name.lower():
            requirements["cpu"] = "4-8 cores"
            requirements["memory"] = "8-16 GB"
            requirements["network"] = "High bandwidth"
        
        if len(role.capabilities) > 5:
            requirements["memory"] = "8-16 GB"
            requirements["storage"] = "50-100 GB"
        
        return requirements
    
    def _extract_security_requirements(self, role: AgentRole) -> List[str]:
        """Extract security requirements for agent role."""
        
        requirements = [
            "Secure API authentication",
            "Encrypted inter-agent communication",
            "Audit logging for all decisions"
        ]
        
        # Add role-specific security requirements
        if role.autonomy_level > 0.8:
            requirements.extend([
                "Enhanced decision validation",
                "Autonomous action approval workflows"
            ])
        
        if "coordinator" in role.name.lower():
            requirements.extend([
                "Privileged access management",
                "System-wide security monitoring"
            ])
        
        # Check for data handling capabilities
        data_capabilities = ["data_processing", "database_access", "file_processing"]
        if any(cap in role.capabilities for cap in data_capabilities):
            requirements.extend([
                "Data encryption at rest and in transit",
                "PII protection and redaction"
            ])
        
        return requirements
    
    def _generate_interaction_patterns(self, agent_design: MultiAgentSystemDesign) -> List[Dict[str, Any]]:
        """Generate interaction patterns between agents."""
        
        patterns = []
        
        if agent_design.architecture_type.value == "hierarchical":
            patterns.append({
                "type": "Command Flow",
                "description": "Top-down task delegation and bottom-up status reporting",
                "participants": "All agents in hierarchy"
            })
        
        elif agent_design.architecture_type.value == "peer_to_peer":
            patterns.append({
                "type": "Collaborative Decision",
                "description": "Consensus-based decision making among peer agents",
                "participants": "All peer agents"
            })
        
        elif agent_design.architecture_type.value == "coordinator_based":
            patterns.append({
                "type": "Hub and Spoke",
                "description": "Central coordinator manages all agent interactions",
                "participants": "Coordinator and worker agents"
            })
        
        else:  # swarm
            patterns.append({
                "type": "Emergent Coordination",
                "description": "Self-organizing behavior through local interactions",
                "participants": "All swarm agents"
            })
        
        return patterns
    
    def _generate_workflow_distribution(self, agent_design: MultiAgentSystemDesign) -> Dict[str, Any]:
        """Generate workflow distribution information."""
        
        return {
            "distribution_strategy": f"{agent_design.architecture_type.value} task allocation",
            "load_balancing": "Dynamic based on agent capacity and specialization",
            "fault_tolerance": "Automatic failover to backup agents",
            "scaling_approach": "Horizontal scaling of specialized agent types"
        }
    
    def _create_error_display(self, error_message: str) -> AgentSystemDisplay:
        """Create error display when formatting fails."""
        
        return AgentSystemDisplay(
            has_agents=False,
            system_autonomy_score=0.0,
            agent_roles=[],
            coordination=None,
            deployment_requirements={},
            tech_stack_validation={"error": f"Unable to format agent data: {error_message}"},
            implementation_guidance=[{
                "type": "error",
                "title": "Agent Information Unavailable",
                "content": "Agent role information temporarily unavailable due to formatting error"
            }]
        )