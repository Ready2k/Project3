"""Multi-agent system designer for complex autonomous workflows."""

from typing import Dict, List, Any
from dataclasses import dataclass
from enum import Enum

from app.llm.base import LLMProvider
from app.utils.imports import require_service


class AgentArchitectureType(Enum):
    SINGLE_AGENT = "single_agent"
    HIERARCHICAL = "hierarchical"
    PEER_TO_PEER = "peer_to_peer"
    COORDINATOR_BASED = "coordinator_based"
    SWARM = "swarm_intelligence"


class CommunicationProtocol(Enum):
    MESSAGE_PASSING = "message_passing"
    SHARED_MEMORY = "shared_memory"
    EVENT_DRIVEN = "event_driven"
    REST_API = "rest_api"
    WEBSOCKET = "websocket"


class CoordinationMechanism(Enum):
    CONSENSUS = "consensus_based"
    VOTING = "voting_based"
    PRIORITY = "priority_based"
    MARKET = "market_based"
    NEGOTIATION = "negotiation_based"


@dataclass
class AgentRole:
    name: str
    responsibility: str
    capabilities: List[str]
    decision_authority: Dict[str, Any]
    autonomy_level: float
    interfaces: Dict[str, Any]
    exception_handling: str
    learning_capabilities: List[str]
    communication_requirements: List[str]


@dataclass
class CommunicationProtocolSpec:
    protocol_type: CommunicationProtocol
    participants: List[str]
    message_format: str
    reliability_requirements: str
    latency_requirements: str


@dataclass
class CoordinationMechanismSpec:
    mechanism_type: CoordinationMechanism
    participants: List[str]
    decision_criteria: List[str]
    conflict_resolution: str
    performance_metrics: List[str]


@dataclass
class MultiAgentSystemDesign:
    architecture_type: AgentArchitectureType
    agent_roles: List[AgentRole]
    communication_protocols: List[CommunicationProtocolSpec]
    coordination_mechanisms: List[CoordinationMechanismSpec]
    autonomy_score: float
    recommended_frameworks: List[str]
    deployment_strategy: str
    scalability_considerations: List[str]
    monitoring_requirements: List[str]


@dataclass
class WorkflowAnalysis:
    complexity_score: float
    parallel_potential: float
    coordination_requirements: List[str]
    specialization_opportunities: List[str]
    bottleneck_identification: List[str]


class MultiAgentSystemDesigner:
    """Designer for multi-agent systems handling complex autonomous workflows."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        # Get logger from service registry
        self.logger = require_service('logger', context='MultiAgentSystemDesigner')
        self.agent_roles = {
            "coordinator": "Orchestrates overall workflow and agent communication",
            "specialist": "Handles domain-specific tasks requiring expertise",
            "validator": "Verifies outputs and ensures quality standards",
            "executor": "Performs concrete actions and implementations",
            "monitor": "Tracks performance and handles exceptions",
            "learner": "Analyzes patterns and improves system performance",
            "negotiator": "Handles external communications and agreements",
            "planner": "Develops strategies and long-term planning"
        }
        
        self.framework_recommendations = {
            AgentArchitectureType.HIERARCHICAL: ["CrewAI", "Microsoft Semantic Kernel"],
            AgentArchitectureType.PEER_TO_PEER: ["LangChain Multi-Agent", "AutoGen"],
            AgentArchitectureType.COORDINATOR_BASED: ["LangChain", "Haystack"],
            AgentArchitectureType.SWARM: ["Mesa", "SUMO", "Custom Swarm Framework"]
        }
    
    async def design_system(self, 
                          requirements: Dict[str, Any],
                          top_patterns: List[Any]) -> MultiAgentSystemDesign:
        """Design a multi-agent system for complex autonomous workflows."""
        
        self.logger.info("Designing multi-agent system for complex workflow")
        
        # Analyze workflow complexity
        workflow_analysis = await self._analyze_workflow_complexity(requirements)
        
        # Determine optimal architecture
        architecture = self._determine_architecture(workflow_analysis, requirements)
        
        # Design agent roles and responsibilities
        agent_roles = await self._define_agent_roles(requirements, workflow_analysis, architecture)
        
        # Design communication protocols
        communication_protocols = await self._design_communication_protocols(
            agent_roles, architecture, workflow_analysis
        )
        
        # Create coordination mechanisms
        coordination_mechanisms = await self._design_coordination_mechanisms(
            agent_roles, workflow_analysis, architecture
        )
        
        # Calculate system autonomy score
        system_autonomy = self._calculate_system_autonomy_score(agent_roles)
        
        # Generate deployment strategy
        deployment_strategy = await self._generate_deployment_strategy(
            architecture, agent_roles, requirements
        )
        
        # Identify scalability considerations
        scalability_considerations = self._identify_scalability_considerations(
            architecture, workflow_analysis
        )
        
        # Define monitoring requirements
        monitoring_requirements = self._define_monitoring_requirements(
            agent_roles, architecture
        )
        
        design = MultiAgentSystemDesign(
            architecture_type=architecture,
            agent_roles=agent_roles,
            communication_protocols=communication_protocols,
            coordination_mechanisms=coordination_mechanisms,
            autonomy_score=system_autonomy,
            recommended_frameworks=self.framework_recommendations.get(architecture, ["LangChain"]),
            deployment_strategy=deployment_strategy,
            scalability_considerations=scalability_considerations,
            monitoring_requirements=monitoring_requirements
        )
        
        self.logger.info(f"Multi-agent system designed: {architecture.value} with {len(agent_roles)} agents, autonomy={system_autonomy:.2f}")
        
        return design
    
    async def _analyze_workflow_complexity(self, requirements: Dict[str, Any]) -> WorkflowAnalysis:
        """Analyze workflow complexity to inform multi-agent design."""
        
        description = requirements.get("description", "")
        workflow_steps = requirements.get("workflow_steps", [])
        
        prompt = f"""
        Analyze this workflow for multi-agent system design:

        Description: {description}
        Workflow Steps: {workflow_steps if workflow_steps else "Not specified - infer from description"}

        Assess:
        1. Complexity score (0.0-1.0) - overall workflow complexity
        2. Parallel potential (0.0-1.0) - how much can be parallelized
        3. Coordination requirements - what coordination is needed between tasks
        4. Specialization opportunities - where specialized agents would be beneficial
        5. Bottleneck identification - potential bottlenecks in the workflow

        Respond in JSON format:
        {{
            "complexity_score": 0.8,
            "parallel_potential": 0.7,
            "coordination_requirements": ["requirement1", "requirement2"],
            "specialization_opportunities": ["opportunity1", "opportunity2"],
            "bottleneck_identification": ["bottleneck1", "bottleneck2"]
        }}
        """
        
        try:
            response = await self.llm_provider.generate(prompt, purpose="workflow_complexity")
            self.logger.debug(f"Workflow complexity response: {response[:200]}...")
            
            from app.utils.json_parser import parse_llm_json_response
            analysis = parse_llm_json_response(response, default_value={}, service_name="multi_agent_designer_workflow")
            
            if not analysis:
                return self._default_workflow_analysis()
            
            return WorkflowAnalysis(
                complexity_score=float(analysis.get("complexity_score", 0.7)),
                parallel_potential=float(analysis.get("parallel_potential", 0.6)),
                coordination_requirements=analysis.get("coordination_requirements", []),
                specialization_opportunities=analysis.get("specialization_opportunities", []),
                bottleneck_identification=analysis.get("bottleneck_identification", [])
            )
            
        except Exception as e:
            self.logger.error(f"Failed to analyze workflow complexity: {e}")
            self.logger.debug(f"Raw response was: {response if 'response' in locals() else 'No response received'}")
            return self._default_workflow_analysis()
    
    def _determine_architecture(self, 
                              workflow_analysis: WorkflowAnalysis,
                              requirements: Dict[str, Any]) -> AgentArchitectureType:
        """Determine optimal multi-agent architecture."""
        
        complexity = workflow_analysis.complexity_score
        parallel_potential = workflow_analysis.parallel_potential
        coordination_needs = len(workflow_analysis.coordination_requirements)
        
        # High complexity with low coordination needs -> Hierarchical
        if complexity > 0.8 and coordination_needs <= 2:
            return AgentArchitectureType.HIERARCHICAL
        
        # High parallel potential with moderate coordination -> Peer-to-peer
        elif parallel_potential > 0.7 and coordination_needs <= 4:
            return AgentArchitectureType.PEER_TO_PEER
        
        # High coordination needs -> Coordinator-based
        elif coordination_needs > 4:
            return AgentArchitectureType.COORDINATOR_BASED
        
        # Very high parallel potential with simple tasks -> Swarm
        elif parallel_potential > 0.9 and complexity < 0.6:
            return AgentArchitectureType.SWARM
        
        # Default to coordinator-based for balanced scenarios
        else:
            return AgentArchitectureType.COORDINATOR_BASED
    
    async def _define_agent_roles(self, 
                                requirements: Dict[str, Any],
                                workflow_analysis: WorkflowAnalysis,
                                architecture: AgentArchitectureType) -> List[AgentRole]:
        """Define specific agent roles for the multi-agent system."""
        
        description = requirements.get("description", "")
        specializations = workflow_analysis.specialization_opportunities
        
        prompt = f"""
        Design agent roles for a {architecture.value} multi-agent system:
        
        Requirement: {description}
        Specialization Opportunities: {specializations}
        Workflow Complexity: {workflow_analysis.complexity_score}
        
        Define 3-6 specialized agents with:
        1. Role name and primary responsibility
        2. Specific capabilities and decision-making authority
        3. Autonomy level (0.0-1.0) - be optimistic about agent capabilities
        4. Exception handling strategies
        5. Learning capabilities
        6. Communication requirements
        
        Focus on maximizing autonomy while ensuring effective coordination.
        
        Respond in JSON format:
        {{
            "agents": [
                {{
                    "name": "Agent Name",
                    "responsibility": "Primary responsibility",
                    "capabilities": ["capability1", "capability2"],
                    "decision_authority": {{
                        "scope": "decision scope",
                        "limits": ["limit1", "limit2"],
                        "escalation_triggers": ["trigger1", "trigger2"]
                    }},
                    "autonomy_level": 0.9,
                    "exception_handling": "exception handling strategy",
                    "learning_capabilities": ["learning1", "learning2"],
                    "communication_requirements": ["comm1", "comm2"]
                }}
            ]
        }}
        """
        
        try:
            response = await self.llm_provider.generate(prompt, purpose="agent_roles")
            self.logger.debug(f"Agent roles response: {response[:200]}...")
            
            from app.utils.json_parser import parse_llm_json_response
            agent_definitions = parse_llm_json_response(response, default_value={"agents": []}, service_name="multi_agent_designer_roles")
            
            if not agent_definitions:
                return self._default_agent_roles(architecture)
            
            agent_roles = []
            for agent_def in agent_definitions.get("agents", []):
                role = AgentRole(
                    name=agent_def["name"],
                    responsibility=agent_def["responsibility"],
                    capabilities=agent_def.get("capabilities", []),
                    decision_authority=agent_def.get("decision_authority", {}),
                    autonomy_level=float(agent_def.get("autonomy_level", 0.8)),
                    interfaces={"input": "structured_data", "output": "structured_results"},
                    exception_handling=agent_def.get("exception_handling", "Standard escalation"),
                    learning_capabilities=agent_def.get("learning_capabilities", []),
                    communication_requirements=agent_def.get("communication_requirements", [])
                )
                agent_roles.append(role)
            
            return agent_roles
            
        except Exception as e:
            self.logger.error(f"Failed to define agent roles: {e}")
            self.logger.debug(f"Raw response was: {response if 'response' in locals() else 'No response received'}")
            return self._default_agent_roles(architecture)
    
    async def _design_communication_protocols(self, 
                                            agent_roles: List[AgentRole],
                                            architecture: AgentArchitectureType,
                                            workflow_analysis: WorkflowAnalysis) -> List[CommunicationProtocolSpec]:
        """Design communication protocols for agent interaction."""
        
        protocols = []
        
        # Determine primary communication protocol based on architecture
        if architecture == AgentArchitectureType.HIERARCHICAL:
            primary_protocol = CommunicationProtocol.MESSAGE_PASSING
            reliability = "High reliability with acknowledgments"
            latency = "Medium latency acceptable"
        elif architecture == AgentArchitectureType.PEER_TO_PEER:
            primary_protocol = CommunicationProtocol.EVENT_DRIVEN
            reliability = "Eventually consistent"
            latency = "Low latency required"
        elif architecture == AgentArchitectureType.COORDINATOR_BASED:
            primary_protocol = CommunicationProtocol.REST_API
            reliability = "High reliability with retries"
            latency = "Medium latency acceptable"
        else:  # SWARM
            primary_protocol = CommunicationProtocol.SHARED_MEMORY
            reliability = "Best effort"
            latency = "Very low latency required"
        
        # Create primary communication protocol
        primary_spec = CommunicationProtocolSpec(
            protocol_type=primary_protocol,
            participants=[role.name for role in agent_roles],
            message_format="JSON with schema validation",
            reliability_requirements=reliability,
            latency_requirements=latency
        )
        protocols.append(primary_spec)
        
        # Add secondary protocols for specific needs
        if workflow_analysis.parallel_potential > 0.7:
            # Add event-driven protocol for parallel coordination
            event_spec = CommunicationProtocolSpec(
                protocol_type=CommunicationProtocol.EVENT_DRIVEN,
                participants=[role.name for role in agent_roles if role.autonomy_level > 0.8],
                message_format="Event schema with metadata",
                reliability_requirements="At-least-once delivery",
                latency_requirements="Low latency for real-time coordination"
            )
            protocols.append(event_spec)
        
        return protocols
    
    async def _design_coordination_mechanisms(self, 
                                            agent_roles: List[AgentRole],
                                            workflow_analysis: WorkflowAnalysis,
                                            architecture: AgentArchitectureType) -> List[CoordinationMechanismSpec]:
        """Design coordination mechanisms for multi-agent collaboration."""
        
        mechanisms = []
        
        # Primary coordination mechanism based on architecture
        if architecture == AgentArchitectureType.HIERARCHICAL:
            primary_mechanism = CoordinationMechanism.PRIORITY
            decision_criteria = ["Agent hierarchy level", "Task priority", "Resource availability"]
            conflict_resolution = "Escalate to higher-level agent"
        elif architecture == AgentArchitectureType.PEER_TO_PEER:
            primary_mechanism = CoordinationMechanism.CONSENSUS
            decision_criteria = ["Majority agreement", "Expertise relevance", "Resource constraints"]
            conflict_resolution = "Consensus building with timeout"
        elif architecture == AgentArchitectureType.COORDINATOR_BASED:
            primary_mechanism = CoordinationMechanism.VOTING
            decision_criteria = ["Coordinator decision", "Agent recommendations", "System constraints"]
            conflict_resolution = "Coordinator override with explanation"
        else:  # SWARM
            primary_mechanism = CoordinationMechanism.MARKET
            decision_criteria = ["Resource cost", "Task efficiency", "Load balancing"]
            conflict_resolution = "Market-based resource allocation"
        
        # Create primary coordination mechanism
        primary_spec = CoordinationMechanismSpec(
            mechanism_type=primary_mechanism,
            participants=[role.name for role in agent_roles],
            decision_criteria=decision_criteria,
            conflict_resolution=conflict_resolution,
            performance_metrics=["Decision latency", "Conflict frequency", "Resource utilization"]
        )
        mechanisms.append(primary_spec)
        
        # Add negotiation mechanism for high-autonomy agents
        high_autonomy_agents = [role.name for role in agent_roles if role.autonomy_level > 0.8]
        if len(high_autonomy_agents) > 2:
            negotiation_spec = CoordinationMechanismSpec(
                mechanism_type=CoordinationMechanism.NEGOTIATION,
                participants=high_autonomy_agents,
                decision_criteria=["Mutual benefit", "Resource optimization", "Goal alignment"],
                conflict_resolution="Multi-round negotiation with mediator",
                performance_metrics=["Negotiation success rate", "Agreement durability", "Satisfaction scores"]
            )
            mechanisms.append(negotiation_spec)
        
        return mechanisms
    
    def _calculate_system_autonomy_score(self, agent_roles: List[AgentRole]) -> float:
        """Calculate overall system autonomy score."""
        
        if not agent_roles:
            return 0.0
        
        # Average autonomy across all agents
        avg_autonomy = sum(role.autonomy_level for role in agent_roles) / len(agent_roles)
        
        # Bonus for high-autonomy agents
        high_autonomy_count = sum(1 for role in agent_roles if role.autonomy_level > 0.8)
        high_autonomy_bonus = (high_autonomy_count / len(agent_roles)) * 0.1
        
        # Bonus for diverse capabilities
        all_capabilities = set()
        for role in agent_roles:
            all_capabilities.update(role.capabilities)
        diversity_bonus = min(0.1, len(all_capabilities) / 20.0)  # Normalize to 20 capabilities
        
        total_score = min(1.0, avg_autonomy + high_autonomy_bonus + diversity_bonus)
        return total_score
    
    async def _generate_deployment_strategy(self, 
                                          architecture: AgentArchitectureType,
                                          agent_roles: List[AgentRole],
                                          requirements: Dict[str, Any]) -> str:
        """Generate deployment strategy for the multi-agent system."""
        
        strategy_templates = {
            AgentArchitectureType.HIERARCHICAL: "Deploy coordinator agent first, then specialist agents in dependency order. Use container orchestration for scaling.",
            AgentArchitectureType.PEER_TO_PEER: "Deploy all agents simultaneously with service discovery. Implement circuit breakers for resilience.",
            AgentArchitectureType.COORDINATOR_BASED: "Deploy coordinator as highly available service, then worker agents. Use load balancing for coordination requests.",
            AgentArchitectureType.SWARM: "Deploy agent instances dynamically based on workload. Use auto-scaling with performance metrics."
        }
        
        base_strategy = strategy_templates.get(architecture, "Standard containerized deployment")
        
        # Add specific considerations
        if len(agent_roles) > 5:
            base_strategy += " Consider microservices architecture for independent scaling."
        
        if any(role.autonomy_level > 0.9 for role in agent_roles):
            base_strategy += " Implement comprehensive monitoring for high-autonomy agents."
        
        return base_strategy
    
    def _identify_scalability_considerations(self, 
                                          architecture: AgentArchitectureType,
                                          workflow_analysis: WorkflowAnalysis) -> List[str]:
        """Identify scalability considerations for the system."""
        
        considerations = []
        
        # Architecture-specific considerations
        if architecture == AgentArchitectureType.HIERARCHICAL:
            considerations.extend([
                "Coordinator bottleneck at high scale",
                "Hierarchical communication overhead",
                "Load balancing across hierarchy levels"
            ])
        elif architecture == AgentArchitectureType.PEER_TO_PEER:
            considerations.extend([
                "Network partition tolerance",
                "Consensus overhead with many agents",
                "Message complexity growth"
            ])
        elif architecture == AgentArchitectureType.COORDINATOR_BASED:
            considerations.extend([
                "Coordinator high availability",
                "Worker agent auto-scaling",
                "Coordination request load balancing"
            ])
        else:  # SWARM
            considerations.extend([
                "Dynamic agent provisioning",
                "Swarm coordination overhead",
                "Resource allocation efficiency"
            ])
        
        # Workflow-specific considerations
        if workflow_analysis.parallel_potential > 0.8:
            considerations.append("High parallelization requires efficient resource management")
        
        if workflow_analysis.complexity_score > 0.8:
            considerations.append("Complex workflows need sophisticated monitoring and debugging")
        
        return considerations
    
    def _define_monitoring_requirements(self, 
                                      agent_roles: List[AgentRole],
                                      architecture: AgentArchitectureType) -> List[str]:
        """Define monitoring requirements for the multi-agent system."""
        
        requirements = [
            "Agent health and availability monitoring",
            "Inter-agent communication metrics",
            "Task completion rates and latencies",
            "Resource utilization per agent",
            "Error rates and exception handling effectiveness"
        ]
        
        # Architecture-specific monitoring
        if architecture == AgentArchitectureType.HIERARCHICAL:
            requirements.extend([
                "Hierarchy level performance metrics",
                "Coordination bottleneck detection"
            ])
        elif architecture == AgentArchitectureType.PEER_TO_PEER:
            requirements.extend([
                "Consensus achievement metrics",
                "Network partition detection"
            ])
        elif architecture == AgentArchitectureType.COORDINATOR_BASED:
            requirements.extend([
                "Coordinator load and response times",
                "Worker agent utilization balance"
            ])
        else:  # SWARM
            requirements.extend([
                "Swarm coordination efficiency",
                "Dynamic scaling effectiveness"
            ])
        
        # High-autonomy agent monitoring
        high_autonomy_agents = [role for role in agent_roles if role.autonomy_level > 0.8]
        if high_autonomy_agents:
            requirements.extend([
                "Autonomous decision quality metrics",
                "Learning and adaptation effectiveness",
                "Exception resolution success rates"
            ])
        
        return requirements
    
    def _default_workflow_analysis(self) -> WorkflowAnalysis:
        """Provide default workflow analysis when LLM fails."""
        
        return WorkflowAnalysis(
            complexity_score=0.7,
            parallel_potential=0.6,
            coordination_requirements=["Task sequencing", "Resource sharing"],
            specialization_opportunities=["Domain expertise", "Technical skills"],
            bottleneck_identification=["Data processing", "External API calls"]
        )
    
    def _default_agent_roles(self, architecture: AgentArchitectureType) -> List[AgentRole]:
        """Provide default agent roles when LLM fails."""
        
        if architecture == AgentArchitectureType.HIERARCHICAL:
            return [
                AgentRole(
                    name="Coordinator Agent",
                    responsibility="Overall workflow orchestration",
                    capabilities=["Task planning", "Resource allocation", "Progress monitoring"],
                    decision_authority={"scope": "System-wide decisions", "limits": [], "escalation_triggers": []},
                    autonomy_level=0.9,
                    interfaces={"input": "requirements", "output": "task_assignments"},
                    exception_handling="Escalate to human supervisor",
                    learning_capabilities=["Performance optimization"],
                    communication_requirements=["Broadcast to all agents"]
                ),
                AgentRole(
                    name="Specialist Agent",
                    responsibility="Domain-specific task execution",
                    capabilities=["Specialized processing", "Quality validation"],
                    decision_authority={"scope": "Domain decisions", "limits": ["Budget constraints"], "escalation_triggers": ["Quality issues"]},
                    autonomy_level=0.8,
                    interfaces={"input": "task_specification", "output": "processed_results"},
                    exception_handling="Retry with alternative approach",
                    learning_capabilities=["Technique refinement"],
                    communication_requirements=["Report to coordinator"]
                )
            ]
        else:
            return [
                AgentRole(
                    name="Processing Agent",
                    responsibility="Core task processing",
                    capabilities=["Data processing", "Result generation"],
                    decision_authority={"scope": "Processing decisions", "limits": [], "escalation_triggers": []},
                    autonomy_level=0.8,
                    interfaces={"input": "data", "output": "results"},
                    exception_handling="Autonomous retry and recovery",
                    learning_capabilities=["Performance optimization"],
                    communication_requirements=["Peer coordination"]
                )
            ]