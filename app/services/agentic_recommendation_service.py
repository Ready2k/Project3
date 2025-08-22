"""Agentic recommendation service that prioritizes autonomous agent solutions."""

import json
import asyncio
from typing import Dict, List, Any, Optional
from pathlib import Path

from app.services.autonomy_assessor import AutonomyAssessor, AutonomyAssessment
from app.pattern.agentic_matcher import AgenticPatternMatcher, AgenticPatternMatch
from app.services.multi_agent_designer import MultiAgentSystemDesigner, MultiAgentSystemDesign
from app.services.agentic_technology_catalog import AgenticTechnologyCatalog
from app.services.pattern_agentic_enhancer import PatternAgenticEnhancer
from app.state.store import Recommendation
from app.llm.base import LLMProvider
from app.utils.logger import app_logger
from app.utils.audit import log_pattern_match


class AgenticRecommendationService:
    """Service for generating agentic automation recommendations that prioritize autonomous solutions."""
    
    def __init__(self, 
                 llm_provider: LLMProvider,
                 pattern_library_path: Optional[Path] = None):
        """Initialize agentic recommendation service.
        
        Args:
            llm_provider: LLM provider for analysis and generation
            pattern_library_path: Path to pattern library
        """
        self.llm_provider = llm_provider
        self.autonomy_assessor = AutonomyAssessor(llm_provider)
        self.multi_agent_designer = MultiAgentSystemDesigner(llm_provider)
        self.agentic_catalog = AgenticTechnologyCatalog()
        
        # Initialize pattern enhancer if library path provided
        self.pattern_enhancer = None
        if pattern_library_path:
            self.pattern_enhancer = PatternAgenticEnhancer(llm_provider, pattern_library_path)
        
        # Agentic-focused thresholds (more optimistic)
        self.min_autonomy_threshold = 0.7  # High autonomy requirement
        self.confidence_boost_factor = 1.2  # Boost confidence for agentic solutions
        
    async def generate_agentic_recommendations(self, 
                                             requirements: Dict[str, Any],
                                             session_id: str = "unknown") -> List[Recommendation]:
        """Generate recommendations prioritizing autonomous agent solutions."""
        
        app_logger.info("Generating agentic recommendations with autonomy prioritization")
        
        # Step 1: Assess autonomy potential (be optimistic)
        autonomy_assessment = await self.autonomy_assessor.assess_autonomy_potential(requirements)
        
        app_logger.info(f"Autonomy assessment: score={autonomy_assessment.overall_score:.2f}, "
                       f"architecture={autonomy_assessment.recommended_architecture.value}")
        
        # Step 2: Apply agentic scope filtering (less restrictive than traditional)
        if not self._passes_agentic_scope_filter(requirements, autonomy_assessment):
            return await self._create_scope_limited_recommendation(requirements, autonomy_assessment)
        
        # Step 3: Match agentic patterns
        agentic_matcher = AgenticPatternMatcher(
            self.autonomy_assessor,
            self.pattern_enhancer,
            None,  # We'll handle base matching differently
            self.llm_provider
        )
        
        agentic_matches = await agentic_matcher.match_agentic_patterns(
            requirements, autonomy_assessment, top_k=5
        )
        
        # Step 4: Design multi-agent system if needed
        multi_agent_design = None
        
        if (autonomy_assessment.recommended_architecture.value in ["multi_agent_collaborative", "hierarchical_agents"] 
            and agentic_matches):
            multi_agent_design = await self.multi_agent_designer.design_system(
                requirements, agentic_matches[:3]
            )
        else:
            # For single-agent scenarios, we should still create agent roles
            # Let's create a simple single-agent design
            multi_agent_design = await self._create_single_agent_design(requirements, autonomy_assessment)
        
        # Step 5: Generate agentic recommendations
        recommendations = []
        
        # Process agentic pattern matches
        for i, match in enumerate(agentic_matches):
            # Create unique agent design for each pattern match to avoid duplication
            if multi_agent_design and multi_agent_design.architecture_type.value == "single_agent":
                # For single-agent scenarios, create unique agent names for each pattern
                unique_agent_design = await self._create_unique_single_agent_design(
                    requirements, autonomy_assessment, match, i
                )
                recommendation = await self._create_agentic_recommendation(
                    match, requirements, autonomy_assessment, unique_agent_design, session_id
                )
            else:
                # For multi-agent scenarios, use the shared design
                recommendation = await self._create_agentic_recommendation(
                    match, requirements, autonomy_assessment, multi_agent_design, session_id
                )
            recommendations.append(recommendation)
        
        # Add multi-agent system recommendation if designed
        if multi_agent_design:
            multi_agent_recommendation = await self._create_multi_agent_recommendation(
                multi_agent_design, requirements, autonomy_assessment, session_id
            )
            recommendations.insert(0, multi_agent_recommendation)  # Prioritize multi-agent
        
        # Step 6: Create new agentic pattern if no good matches
        if not recommendations or all(r.confidence < 0.7 for r in recommendations):
            new_agentic_recommendation = await self._create_new_agentic_pattern_recommendation(
                requirements, autonomy_assessment, session_id
            )
            if new_agentic_recommendation:
                recommendations.insert(0, new_agentic_recommendation)
        
        # Step 7: Sort by autonomy-weighted confidence
        recommendations.sort(key=lambda r: self._calculate_agentic_score(r), reverse=True)
        
        app_logger.info(f"Generated {len(recommendations)} agentic recommendations")
        
        return recommendations[:5]  # Return top 5
    
    def _passes_agentic_scope_filter(self, 
                                   requirements: Dict[str, Any],
                                   autonomy_assessment: AutonomyAssessment) -> bool:
        """Apply agentic scope filtering (more permissive than traditional)."""
        
        description = str(requirements.get('description', '')).lower()
        
        # Only filter out clearly impossible physical tasks
        impossible_physical_indicators = [
            'physically move', 'physically transport', 'manual labor', 'construction work',
            'repair hardware', 'install equipment', 'paint walls', 'clean floors'
        ]
        
        # Check for impossible physical tasks
        for indicator in impossible_physical_indicators:
            if indicator in description:
                app_logger.info(f"Filtered out impossible physical task: {indicator}")
                return False
        
        # Be optimistic - if autonomy assessment is reasonable, allow it
        if autonomy_assessment.overall_score >= 0.5:
            return True
        
        # Even low autonomy tasks might have agentic potential
        return True
    
    async def _create_agentic_recommendation(self, 
                                           match: AgenticPatternMatch,
                                           requirements: Dict[str, Any],
                                           autonomy_assessment: AutonomyAssessment,
                                           multi_agent_design: Optional[MultiAgentSystemDesign],
                                           session_id: str) -> Recommendation:
        """Create recommendation from agentic pattern match."""
        
        # Determine feasibility (aggressive - favor full automation)
        feasibility = self._determine_agentic_feasibility(match, autonomy_assessment)
        
        # Calculate confidence (boosted for agentic solutions)
        confidence = self._calculate_agentic_confidence(match, autonomy_assessment)
        
        # Generate agentic tech stack
        tech_stack = await self._generate_agentic_tech_stack(match, requirements, autonomy_assessment)
        
        # Generate agentic reasoning
        reasoning = await self._generate_agentic_reasoning(match, autonomy_assessment, multi_agent_design)
        
        # Log pattern match for analytics
        try:
            await log_pattern_match(
                session_id=session_id,
                pattern_id=match.pattern_id,
                score=match.autonomy_score,
                accepted=None
            )
        except Exception as e:
            app_logger.error(f"Failed to log agentic pattern match: {e}")
        
        # Extract agent roles from multi-agent design if available
        agent_roles = None
        if multi_agent_design and multi_agent_design.agent_roles:
            agent_roles = [
                {
                    "name": role.name,
                    "responsibility": role.responsibility,
                    "capabilities": role.capabilities,
                    "autonomy_level": role.autonomy_level,
                    "decision_authority": role.decision_authority,
                    "communication_requirements": role.communication_requirements,
                    "interfaces": role.interfaces,
                    "exception_handling": role.exception_handling,
                    "learning_capabilities": role.learning_capabilities
                }
                for role in multi_agent_design.agent_roles
            ]
        
        return Recommendation(
            pattern_id=match.pattern_id,
            feasibility=feasibility,
            confidence=confidence,
            tech_stack=tech_stack,
            reasoning=reasoning,
            agent_roles=agent_roles
        )
    
    def _determine_agentic_feasibility(self, 
                                     match: AgenticPatternMatch,
                                     autonomy_assessment: AutonomyAssessment) -> str:
        """Determine feasibility with agentic bias (aggressive automation)."""
        
        # Start with pattern's enhanced feasibility
        base_feasibility = match.enhanced_pattern.get("feasibility", "Partially Automatable")
        
        # Aggressive agentic assessment - favor full automation
        if match.autonomy_score >= 0.8:
            return "Fully Automatable"
        elif match.autonomy_score >= 0.6:
            # Check if we can upgrade to fully automatable
            if (autonomy_assessment.overall_score >= 0.7 and 
                autonomy_assessment.decision_independence.value in ["high", "full"]):
                return "Fully Automatable"
            else:
                return "Partially Automatable"
        else:
            # Even lower scores might be partially automatable with agents
            if autonomy_assessment.overall_score >= 0.5:
                return "Partially Automatable"
            else:
                return "Not Automatable"
    
    def _calculate_agentic_confidence(self, 
                                    match: AgenticPatternMatch,
                                    autonomy_assessment: AutonomyAssessment) -> float:
        """Calculate confidence with agentic boost."""
        
        base_confidence = match.confidence
        
        # Boost confidence for high autonomy
        autonomy_boost = match.autonomy_score * 0.2  # Up to 20% boost
        
        # Boost for good reasoning capabilities
        reasoning_boost = 0
        if len(match.reasoning_capabilities) >= 3:
            reasoning_boost = 0.1
        
        # Boost for multi-agent potential when needed
        multi_agent_boost = 0
        if (match.multi_agent_potential and 
            autonomy_assessment.recommended_architecture.value != "single_agent"):
            multi_agent_boost = 0.1
        
        # Apply agentic confidence boost factor
        boosted_confidence = (base_confidence + autonomy_boost + reasoning_boost + multi_agent_boost) * self.confidence_boost_factor
        
        return min(1.0, boosted_confidence)
    
    async def _generate_agentic_tech_stack(self, 
                                         match: AgenticPatternMatch,
                                         requirements: Dict[str, Any],
                                         autonomy_assessment: AutonomyAssessment) -> List[str]:
        """Generate technology stack focused on agentic frameworks."""
        
        tech_stack = []
        
        # Add agentic frameworks from pattern
        agentic_frameworks = match.enhanced_pattern.get("agentic_frameworks", [])
        tech_stack.extend(agentic_frameworks)
        
        # Add reasoning engines if needed
        reasoning_engines = match.enhanced_pattern.get("reasoning_engines", [])
        tech_stack.extend(reasoning_engines)
        
        # Get recommendations from agentic catalog
        catalog_recommendations = self.agentic_catalog.recommend_technologies_for_requirements(
            {
                "reasoning_types": autonomy_assessment.reasoning_requirements,
                "decision_authority_level": autonomy_assessment.decision_independence.value,
                "multi_agent_required": match.multi_agent_potential
            },
            top_k=3
        )
        
        # Add top catalog recommendations
        for tech, score in catalog_recommendations:
            if tech.name not in tech_stack and score > 0.6:
                tech_stack.append(tech.name)
        
        # Add base tech stack from pattern (filtered for agentic compatibility)
        base_tech = match.enhanced_pattern.get("tech_stack", [])
        agentic_compatible_tech = self._filter_agentic_compatible_tech(base_tech)
        tech_stack.extend(agentic_compatible_tech)
        
        # Remove duplicates while preserving order
        seen = set()
        unique_tech_stack = []
        for tech in tech_stack:
            if tech not in seen:
                seen.add(tech)
                unique_tech_stack.append(tech)
        
        return unique_tech_stack[:10]  # Limit to top 10
    
    def _filter_agentic_compatible_tech(self, tech_list: List[str]) -> List[str]:
        """Filter technology list for agentic compatibility."""
        
        # Prioritize agentic-friendly technologies
        agentic_friendly = [
            "FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes",
            "Apache Kafka", "RabbitMQ", "Elasticsearch", "MongoDB",
            "Python", "Node.js", "TypeScript", "WebSocket", "GraphQL"
        ]
        
        # Filter and prioritize
        compatible_tech = []
        for tech in tech_list:
            # Check if technology is agentic-friendly
            if any(friendly in tech for friendly in agentic_friendly):
                compatible_tech.append(tech)
            # Include other technologies but with lower priority
            elif not any(exclude in tech.lower() for exclude in ["manual", "human", "review"]):
                compatible_tech.append(tech)
        
        return compatible_tech
    
    async def _generate_agentic_reasoning(self, 
                                        match: AgenticPatternMatch,
                                        autonomy_assessment: AutonomyAssessment,
                                        multi_agent_design: Optional[MultiAgentSystemDesign]) -> str:
        """Generate reasoning that emphasizes agentic capabilities."""
        
        reasoning_parts = []
        
        # Autonomy emphasis
        autonomy_score = match.autonomy_score
        reasoning_parts.append(f"This solution achieves {autonomy_score:.0%} autonomy through advanced AI agent capabilities.")
        
        # Reasoning capabilities
        if match.reasoning_capabilities:
            reasoning_types = ", ".join(match.reasoning_capabilities[:3])
            reasoning_parts.append(f"The agent uses {reasoning_types} reasoning to handle complex scenarios autonomously.")
        
        # Decision-making scope
        decision_scope = match.decision_scope
        if decision_scope.get("autonomous_decisions"):
            decisions = decision_scope["autonomous_decisions"][:2]
            reasoning_parts.append(f"Agent can autonomously: {', '.join(decisions)}.")
        
        # Exception handling
        if match.exception_handling:
            reasoning_parts.append(f"Exception handling: {match.exception_handling}")
        
        # Multi-agent coordination
        if multi_agent_design:
            agent_count = len(multi_agent_design.agent_roles)
            reasoning_parts.append(f"Uses {multi_agent_design.architecture_type.value} architecture with {agent_count} specialized agents for complex coordination.")
        
        # Learning and adaptation
        learning_mechanisms = match.enhanced_pattern.get("learning_mechanisms", [])
        if learning_mechanisms:
            reasoning_parts.append(f"Includes continuous learning through {', '.join(learning_mechanisms[:2])}.")
        
        return " ".join(reasoning_parts)
    
    async def _create_multi_agent_recommendation(self, 
                                               design: MultiAgentSystemDesign,
                                               requirements: Dict[str, Any],
                                               autonomy_assessment: AutonomyAssessment,
                                               session_id: str) -> Recommendation:
        """Create recommendation for multi-agent system."""
        
        # Multi-agent systems are highly autonomous
        confidence = min(1.0, design.autonomy_score * self.confidence_boost_factor)
        
        # Generate multi-agent tech stack
        tech_stack = design.recommended_frameworks.copy()
        
        # Add coordination technologies
        coordination_tech = [
            "Apache Kafka",  # For event-driven communication
            "Redis",         # For shared state
            "Docker",        # For agent containerization
            "Kubernetes"     # For orchestration
        ]
        tech_stack.extend(coordination_tech)
        
        # Generate multi-agent reasoning
        agent_roles = [role.name for role in design.agent_roles]
        reasoning = (f"Multi-agent system using {design.architecture_type.value} architecture "
                    f"with {len(agent_roles)} specialized agents: {', '.join(agent_roles[:3])}. "
                    f"Achieves {design.autonomy_score:.0%} system autonomy through collaborative reasoning "
                    f"and distributed decision-making. {design.deployment_strategy}")
        
        # Extract agent roles from multi-agent design
        agent_roles = [
            {
                "name": role.name,
                "responsibility": role.responsibility,
                "capabilities": role.capabilities,
                "autonomy_level": role.autonomy_level,
                "decision_authority": role.decision_authority,
                "communication_requirements": role.communication_requirements,
                "interfaces": role.interfaces,
                "exception_handling": role.exception_handling,
                "learning_capabilities": role.learning_capabilities
            }
            for role in design.agent_roles
        ]
        
        return Recommendation(
            pattern_id="APAT-00",
            feasibility="Fully Automatable",
            confidence=confidence,
            tech_stack=tech_stack,
            reasoning=reasoning,
            agent_roles=agent_roles
        )
    
    async def _create_new_agentic_pattern_recommendation(self, 
                                                       requirements: Dict[str, Any],
                                                       autonomy_assessment: AutonomyAssessment,
                                                       session_id: str) -> Optional[Recommendation]:
        """Create new agentic pattern when no good matches exist."""
        
        if not self.pattern_enhancer:
            return None
        
        try:
            # Create a base pattern from requirements
            base_pattern = {
                "pattern_id": f"CUSTOM_AGENTIC_{session_id[:8]}",
                "name": f"Custom Autonomous Agent for {requirements.get('description', 'Task')[:50]}",
                "description": requirements.get('description', ''),
                "feasibility": "Partially Automatable",  # Will be enhanced
                "pattern_type": ["custom_agentic"],
                "tech_stack": [],
                "confidence_score": 0.7
            }
            
            # Enhance for autonomy
            enhanced_pattern = await self.pattern_enhancer.enhance_for_autonomy(
                base_pattern, requirements
            )
            
            # Create recommendation from enhanced pattern
            confidence = enhanced_pattern.get("autonomy_level", 0.8) * self.confidence_boost_factor
            
            tech_stack = enhanced_pattern.get("agentic_frameworks", []) + enhanced_pattern.get("tech_stack", [])
            
            reasoning = (f"Custom autonomous agent solution designed specifically for this requirement. "
                        f"Achieves {enhanced_pattern.get('autonomy_level', 0.8):.0%} autonomy through "
                        f"{', '.join(enhanced_pattern.get('reasoning_types', ['advanced']))} reasoning. "
                        f"Agent can handle: {', '.join(enhanced_pattern.get('decision_boundaries', {}).get('autonomous_decisions', ['standard operations'])[:2])}.")
            
            # Generate basic agent roles for custom pattern
            agent_name = await self._generate_agent_name(requirements)
            agent_roles = [
                {
                    "name": agent_name,
                    "responsibility": f"Main autonomous agent responsible for {requirements.get('description', 'the task')[:100]}",
                    "capabilities": enhanced_pattern.get("decision_boundaries", {}).get("autonomous_decisions", ["task_execution", "decision_making"]),
                    "autonomy_level": enhanced_pattern.get("autonomy_level", 0.8),
                    "decision_authority": {
                        "scope": ["operational_decisions", "workflow_management"],
                        "limitations": ["escalate_critical_errors", "human_approval_for_major_changes"]
                    },
                    "communication_requirements": ["status_reporting", "exception_handling"],
                    "interfaces": {
                        "input": ["user_requests", "system_data"],
                        "output": ["task_results", "status_updates"]
                    },
                    "exception_handling": "Autonomous resolution with escalation for critical failures",
                    "learning_capabilities": ["feedback_incorporation", "pattern_recognition"]
                }
            ]
            
            return Recommendation(
                pattern_id=enhanced_pattern["pattern_id"],
                feasibility=enhanced_pattern.get("feasibility", "Fully Automatable"),
                confidence=min(1.0, confidence),
                tech_stack=tech_stack[:8],
                reasoning=reasoning,
                agent_roles=agent_roles
            )
            
        except Exception as e:
            app_logger.error(f"Failed to create new agentic pattern: {e}")
            return None
    
    async def _create_scope_limited_recommendation(self, 
                                                 requirements: Dict[str, Any],
                                                 autonomy_assessment: AutonomyAssessment) -> List[Recommendation]:
        """Create recommendation for scope-limited scenarios."""
        
        description = requirements.get('description', '')
        
        # Even for limited scope, suggest agentic alternatives
        reasoning = (f"While this requirement involves physical components that cannot be directly automated, "
                    f"an autonomous AI agent could handle the digital aspects: monitoring, scheduling, "
                    f"notifications, data tracking, and coordination. The agent could achieve "
                    f"{autonomy_assessment.overall_score:.0%} autonomy for the digital workflow components.")
        
        # Suggest agentic technologies even for limited scope
        agentic_tech = ["LangChain", "OpenAI Assistants API", "FastAPI", "PostgreSQL"]
        
        # Create agent roles for digital assistant
        agent_name = await self._generate_agent_name(requirements)
        # For scope-limited scenarios, make it clear it's a digital assistant
        if "Digital" not in agent_name and "Assistant" not in agent_name:
            agent_name = f"Digital {agent_name}"
        
        agent_roles = [
            {
                "name": agent_name,
                "responsibility": "Autonomous agent handling digital workflow aspects while coordinating with physical processes",
                "capabilities": ["monitoring", "scheduling", "notifications", "data_tracking", "coordination"],
                "autonomy_level": autonomy_assessment.overall_score,
                "decision_authority": {
                    "scope": ["scheduling_decisions", "notification_management", "data_collection"],
                    "limitations": ["no_physical_actions", "escalate_critical_issues"]
                },
                "communication_requirements": ["user_notifications", "system_integration", "status_reporting"],
                "interfaces": {
                    "input": ["user_requests", "system_events", "sensor_data"],
                    "output": ["notifications", "reports", "scheduling_updates"]
                },
                "exception_handling": "Escalate physical task requirements to human operators",
                "learning_capabilities": ["pattern_recognition", "user_preference_learning"]
            }
        ]
        
        limited_recommendation = Recommendation(
            pattern_id="AGENTIC_DIGITAL_ASSISTANT",
            feasibility="Partially Automatable",
            confidence=0.7,  # Still confident in agentic approach
            tech_stack=agentic_tech,
            reasoning=reasoning,
            agent_roles=agent_roles
        )
        
        return [limited_recommendation]
    
    async def _create_single_agent_design(self, 
                                         requirements: Dict[str, Any],
                                         autonomy_assessment: AutonomyAssessment) -> 'MultiAgentSystemDesign':
        """Create a single-agent design for scenarios that don't require multi-agent systems."""
        from app.services.multi_agent_designer import MultiAgentSystemDesign, AgentRole, AgentArchitectureType
        
        # Create a single agent role based on the requirements
        description = requirements.get('description', 'autonomous task')
        
        # Generate a meaningful agent name based on the requirements
        agent_name = await self._generate_agent_name(requirements)
        
        single_agent = AgentRole(
            name=agent_name,
            responsibility=f"Main autonomous agent responsible for {description[:100]}",
            capabilities=[
                "task_execution",
                "decision_making", 
                "exception_handling",
                "learning_adaptation",
                "communication"
            ],
            autonomy_level=autonomy_assessment.overall_score,
            decision_authority={
                "scope": ["operational_decisions", "workflow_management", "resource_allocation"],
                "limitations": ["no_financial_decisions", "escalate_critical_errors"]
            },
            interfaces={
                "input": ["user_requests", "system_events"],
                "output": ["task_results", "status_updates", "exception_reports"]
            },
            exception_handling="Autonomous resolution with escalation for critical failures",
            learning_capabilities=["pattern_recognition", "feedback_incorporation", "performance_optimization"],
            communication_requirements=[
                "status_reporting",
                "exception_escalation",
                "user_interaction"
            ]
        )
        
        # Create a minimal multi-agent design with single agent
        design = MultiAgentSystemDesign(
            architecture_type=AgentArchitectureType.SINGLE_AGENT,
            agent_roles=[single_agent],
            communication_protocols=[],
            coordination_mechanisms=[],
            autonomy_score=autonomy_assessment.overall_score,
            recommended_frameworks=["LangChain", "OpenAI Assistants API"],
            deployment_strategy="Single autonomous agent deployment with monitoring and feedback loops",
            scalability_considerations=["Horizontal scaling through task queuing", "Vertical scaling through enhanced reasoning"],
            monitoring_requirements=["Performance metrics", "Decision accuracy", "Exception rates"]
        )
        
        return design
    
    async def _create_unique_single_agent_design(self, 
                                               requirements: Dict[str, Any],
                                               autonomy_assessment: AutonomyAssessment,
                                               pattern_match: Any,
                                               index: int) -> 'MultiAgentSystemDesign':
        """Create a unique single-agent design for each pattern match to avoid duplication."""
        from app.services.multi_agent_designer import MultiAgentSystemDesign, AgentRole, AgentArchitectureType
        
        # Create a unique agent role based on the pattern and requirements
        description = requirements.get('description', 'autonomous task')
        
        # Generate a unique agent name based on the pattern and index
        base_agent_name = await self._generate_agent_name(requirements)
        
        # Create specialized agent names based on pattern characteristics
        if hasattr(pattern_match, 'pattern_id'):
            pattern_id = pattern_match.pattern_id
            if 'workflow' in pattern_id.lower():
                agent_name = f"Workflow {base_agent_name}"
            elif 'data' in pattern_id.lower():
                agent_name = f"Data Processing {base_agent_name}"
            elif 'integration' in pattern_id.lower():
                agent_name = f"Integration {base_agent_name}"
            elif 'monitoring' in pattern_id.lower():
                agent_name = f"Monitoring {base_agent_name}"
            else:
                agent_name = f"{base_agent_name} #{index + 1}"
        else:
            agent_name = f"{base_agent_name} #{index + 1}"
        
        # Create specialized capabilities based on pattern
        base_capabilities = [
            "task_execution",
            "decision_making", 
            "exception_handling",
            "learning_adaptation",
            "communication"
        ]
        
        # Add pattern-specific capabilities
        if hasattr(pattern_match, 'reasoning_capabilities'):
            base_capabilities.extend(pattern_match.reasoning_capabilities[:2])
        
        unique_agent = AgentRole(
            name=agent_name,
            responsibility=f"Specialized autonomous agent for {description[:100]} using {getattr(pattern_match, 'pattern_id', 'custom')} pattern",
            capabilities=base_capabilities,
            autonomy_level=autonomy_assessment.overall_score,
            decision_authority={
                "scope": ["operational_decisions", "workflow_management", "pattern_specific_decisions"],
                "limitations": ["no_financial_decisions", "escalate_critical_errors"]
            },
            interfaces={
                "input": ["user_requests", "system_events", "pattern_data"],
                "output": ["task_results", "status_updates", "pattern_insights"]
            },
            exception_handling="Autonomous resolution with pattern-specific fallbacks",
            learning_capabilities=["pattern_recognition", "feedback_incorporation", "performance_optimization"],
            communication_requirements=[
                "status_reporting",
                "pattern_coordination",
                "user_interaction"
            ]
        )
        
        # Create a unique single-agent design
        design = MultiAgentSystemDesign(
            architecture_type=AgentArchitectureType.SINGLE_AGENT,
            agent_roles=[unique_agent],
            communication_protocols=[],
            coordination_mechanisms=[],
            autonomy_score=autonomy_assessment.overall_score,
            recommended_frameworks=["LangChain", "OpenAI Assistants API"],
            deployment_strategy=f"Specialized single agent deployment for {getattr(pattern_match, 'pattern_id', 'custom')} pattern",
            scalability_considerations=["Pattern-specific scaling", "Specialized reasoning enhancement"],
            monitoring_requirements=["Pattern performance metrics", "Decision accuracy", "Exception rates"]
        )
        
        return design
    
    def _calculate_agentic_score(self, recommendation: Recommendation) -> float:
        """Calculate agentic score for sorting recommendations."""
        
        base_score = recommendation.confidence
        
        # Boost for "Fully Automatable"
        if recommendation.feasibility == "Fully Automatable":
            base_score *= 1.3
        elif recommendation.feasibility == "Partially Automatable":
            base_score *= 1.1
        
        # Boost for agentic technologies in tech stack
        agentic_tech_count = sum(1 for tech in recommendation.tech_stack 
                                if any(framework in tech for framework in 
                                      ["LangChain", "AutoGPT", "CrewAI", "Semantic Kernel", "Assistants API"]))
        
        agentic_boost = min(0.2, agentic_tech_count * 0.05)  # Up to 20% boost
        
        return min(1.0, base_score + agentic_boost)
    
    async def _generate_agent_name(self, requirements: Dict[str, Any], suffix: str = None) -> str:
        """Generate a meaningful agent name based on requirements with optional suffix for uniqueness."""
        
        description = requirements.get('description', '').lower()
        
        # Extract key domain/function words from description
        domain_keywords = {
            'user': ['user', 'customer', 'client', 'account', 'deceased', 'care'],
            'data': ['data', 'database', 'information', 'record', 'file', 'document'],
            'email': ['email', 'mail', 'notification', 'message', 'letter'],
            'report': ['report', 'analytics', 'dashboard', 'metrics'],
            'workflow': ['workflow', 'process', 'automation', 'task', 'pursue', 'dnp'],
            'integration': ['integration', 'api', 'sync', 'connect', 'system'],
            'monitoring': ['monitor', 'alert', 'watch', 'track', 'status'],
            'security': ['security', 'auth', 'permission', 'access', 'compliance'],
            'content': ['content', 'document', 'file', 'media', 'filing'],
            'communication': ['chat', 'communication', 'collaboration', 'phone', 'connect'],
            'scheduling': ['schedule', 'calendar', 'appointment', 'booking'],
            'inventory': ['inventory', 'stock', 'product', 'item'],
            'financial': ['payment', 'invoice', 'billing', 'financial'],
            'support': ['support', 'help', 'ticket', 'issue', 'case']
        }
        
        # Find all matching domains (not just first one)
        detected_domains = []
        for domain, keywords in domain_keywords.items():
            if any(keyword in description for keyword in keywords):
                detected_domains.append(domain)
        
        # Generate agent name based on primary domain
        primary_domain = detected_domains[0] if detected_domains else None
        
        if primary_domain:
            domain_names = {
                'user': 'User Management Agent',
                'data': 'Data Processing Agent', 
                'email': 'Communication Agent',
                'report': 'Analytics Agent',
                'workflow': 'Workflow Automation Agent',
                'integration': 'Integration Agent',
                'monitoring': 'Monitoring Agent',
                'security': 'Security Agent',
                'content': 'Content Management Agent',
                'communication': 'Communication Agent',
                'scheduling': 'Scheduling Agent',
                'inventory': 'Inventory Management Agent',
                'financial': 'Financial Processing Agent',
                'support': 'Support Agent'
            }
            base_name = domain_names.get(primary_domain, 'Task Automation Agent')
            
            # Add suffix for uniqueness if provided
            if suffix:
                return f"{base_name} {suffix}"
            
            # If multiple domains detected, create a compound name
            if len(detected_domains) > 1:
                secondary_domain = detected_domains[1]
                secondary_names = {
                    'user': 'User',
                    'data': 'Data', 
                    'email': 'Communication',
                    'report': 'Analytics',
                    'workflow': 'Workflow',
                    'integration': 'Integration',
                    'monitoring': 'Monitoring',
                    'security': 'Security',
                    'content': 'Content',
                    'communication': 'Communication',
                    'scheduling': 'Scheduling',
                    'inventory': 'Inventory',
                    'financial': 'Financial',
                    'support': 'Support'
                }
                secondary_name = secondary_names.get(secondary_domain, '')
                if secondary_name and secondary_name not in base_name:
                    return f"{secondary_name} {base_name}"
            
            return base_name
        
        # Fallback: try to extract action words
        action_keywords = {
            'create': 'Creation Agent',
            'update': 'Update Agent', 
            'process': 'Processing Agent',
            'manage': 'Management Agent',
            'analyze': 'Analysis Agent',
            'generate': 'Generation Agent',
            'validate': 'Validation Agent',
            'transform': 'Transformation Agent',
            'sync': 'Synchronization Agent',
            'migrate': 'Migration Agent',
            'mark': 'Status Management Agent',
            'move': 'Transfer Agent'
        }
        
        for action, agent_name in action_keywords.items():
            if action in description:
                if suffix:
                    return f"{agent_name} {suffix}"
                return agent_name
        
        # Final fallback
        if suffix:
            return f'Task Automation Agent {suffix}'
        return 'Task Automation Agent'