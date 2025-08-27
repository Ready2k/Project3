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
from app.services.agentic_necessity_assessor import AgenticNecessityAssessor, AgenticNecessityAssessment, SolutionType
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
        self.necessity_assessor = AgenticNecessityAssessor(llm_provider)
        
        # Initialize pattern enhancer if library path provided
        self.pattern_enhancer = None
        if pattern_library_path:
            self.pattern_enhancer = PatternAgenticEnhancer(llm_provider, pattern_library_path)
        
        # Import configuration service for dynamic thresholds
        from app.services.configuration_service import get_config
        self.config_service = get_config()
        
        # Use dynamic thresholds from configuration
        self.min_autonomy_threshold = self.config_service.autonomy.min_autonomy_threshold
        self.confidence_boost_factor = self.config_service.autonomy.confidence_boost_factor
        
    async def generate_agentic_recommendations(self, 
                                             requirements: Dict[str, Any],
                                             session_id: str = "unknown") -> List[Recommendation]:
        """Generate recommendations prioritizing autonomous agent solutions."""
        
        app_logger.info("Generating agentic recommendations with autonomy prioritization")
        
        # Step 0: Assess agentic necessity first
        necessity_assessment = await self.necessity_assessor.assess_agentic_necessity(requirements)
        
        app_logger.info(f"Agentic necessity assessment: {necessity_assessment.recommended_solution_type.value} "
                       f"(agentic: {necessity_assessment.agentic_necessity_score:.2f}, "
                       f"traditional: {necessity_assessment.traditional_suitability_score:.2f})")
        
        # If traditional automation is clearly better, return traditional recommendation
        if necessity_assessment.recommended_solution_type == SolutionType.TRADITIONAL_AUTOMATION:
            return await self._create_traditional_automation_recommendation(requirements, necessity_assessment, session_id)
        
        # Step 1: Assess autonomy potential (be optimistic)
        autonomy_assessment = await self.autonomy_assessor.assess_autonomy_potential(requirements)
        
        app_logger.info(f"Autonomy assessment: score={autonomy_assessment.overall_score:.2f}, "
                       f"architecture={autonomy_assessment.recommended_architecture.value}")
        
        # Step 2: Apply agentic scope filtering (less restrictive than traditional)
        if not self._passes_agentic_scope_filter(requirements, autonomy_assessment):
            return await self._create_scope_limited_recommendation(requirements, autonomy_assessment, necessity_assessment)
        
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
        if multi_agent_design and multi_agent_design.architecture_type.value == "single_agent":
            # For single-agent scenarios, create one comprehensive recommendation instead of multiple duplicates
            if agentic_matches:
                # Use the best pattern match for the single agent
                best_match = agentic_matches[0]
                recommendation = await self._create_agentic_recommendation(
                    best_match, requirements, autonomy_assessment, multi_agent_design, session_id, necessity_assessment
                )
                recommendations.append(recommendation)
        else:
            # For multi-agent scenarios, process each pattern match
            for i, match in enumerate(agentic_matches):
                recommendation = await self._create_agentic_recommendation(
                    match, requirements, autonomy_assessment, multi_agent_design, session_id, necessity_assessment
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
                requirements, autonomy_assessment, session_id, necessity_assessment
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
                                           session_id: str,
                                           necessity_assessment: Optional[AgenticNecessityAssessment] = None) -> Recommendation:
        """Create recommendation from agentic pattern match."""
        
        # Determine feasibility (aggressive - favor full automation)
        feasibility = self._determine_agentic_feasibility(match, autonomy_assessment, requirements)
        
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
            agent_roles=agent_roles,
            necessity_assessment=necessity_assessment
        )
    
    def _determine_agentic_feasibility(self, 
                                     match: AgenticPatternMatch,
                                     autonomy_assessment: AutonomyAssessment,
                                     requirements: Dict[str, Any]) -> str:
        """Determine feasibility with agentic bias (aggressive automation)."""
        
        # First, check if we have LLM analysis from Q&A phase - this should take priority
        # The LLM analysis is more contextual and considers user-specific constraints
        llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
        if llm_feasibility:
            app_logger.info(f"Using LLM feasibility assessment from Q&A: {llm_feasibility}")
            # Map to our standard format if needed
            if llm_feasibility in ["Automatable", "Fully Automatable", "Partially Automatable", "Not Automatable"]:
                return llm_feasibility
        
        # Fallback to autonomy score-based assessment
        app_logger.info(f"No LLM feasibility found, using autonomy score-based assessment")
        
        # Start with pattern's enhanced feasibility
        base_feasibility = match.enhanced_pattern.get("feasibility", "Partially Automatable")
        
        # Aggressive agentic assessment - favor full automation
        if self.config_service.is_fully_automatable(match.autonomy_score):
            return "Fully Automatable"
        elif self.config_service.is_partially_automatable(match.autonomy_score):
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
                                               session_id: str,
                                               necessity_assessment: Optional[AgenticNecessityAssessment] = None) -> Recommendation:
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
        
        # Generate unique APAT pattern ID for multi-agent system
        pattern_id = self._generate_agentic_pattern_id()
        
        # Determine feasibility - respect LLM analysis if available
        llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
        if llm_feasibility and llm_feasibility in ["Automatable", "Fully Automatable", "Partially Automatable", "Not Automatable"]:
            feasibility = llm_feasibility
            app_logger.info(f"Using LLM feasibility assessment for multi-agent recommendation: {llm_feasibility}")
        else:
            feasibility = "Fully Automatable"  # Default for multi-agent systems
            app_logger.info("No LLM feasibility found, using default 'Fully Automatable' for multi-agent recommendation")
        
        # Create and save the multi-agent pattern
        multi_agent_pattern = {
            "pattern_id": pattern_id,
            "name": f"Multi-Agent {design.architecture_type.value.title()} System",
            "description": f"Multi-agent system with {len(design.agent_roles)} specialized agents",
            "feasibility": feasibility,
            "autonomy_level": design.autonomy_score,
            "agentic_frameworks": design.recommended_frameworks,
            "tech_stack": tech_stack
        }
        
        # Save the multi-agent pattern (fire and forget - don't block on save)
        asyncio.create_task(self._save_multi_agent_pattern(multi_agent_pattern, design, requirements, autonomy_assessment, session_id))
        
        app_logger.info(f"Created multi-agent APAT pattern {pattern_id} for session {session_id}")
        
        return Recommendation(
            pattern_id=pattern_id,
            feasibility=feasibility,
            confidence=confidence,
            tech_stack=tech_stack,
            reasoning=reasoning,
            agent_roles=agent_roles,
            necessity_assessment=necessity_assessment
        )
    
    async def _create_new_agentic_pattern_recommendation(self, 
                                                       requirements: Dict[str, Any],
                                                       autonomy_assessment: AutonomyAssessment,
                                                       session_id: str,
                                                       necessity_assessment: Optional[AgenticNecessityAssessment] = None) -> Optional[Recommendation]:
        """Create new agentic pattern when no good matches exist."""
        
        if not self.pattern_enhancer:
            return None
        
        try:
            # Generate unique APAT pattern ID
            pattern_id = self._generate_agentic_pattern_id()
            
            # Create a base pattern from requirements
            base_pattern = {
                "pattern_id": pattern_id,
                "name": f"Autonomous Agent for {requirements.get('description', 'Task')}",
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
            
            # Save the new APAT pattern to the pattern library
            await self._save_agentic_pattern(enhanced_pattern, requirements, autonomy_assessment, session_id)
            
            # Create recommendation from enhanced pattern
            confidence = enhanced_pattern.get("autonomy_level", 0.8) * self.confidence_boost_factor
            
            tech_stack = enhanced_pattern.get("agentic_frameworks", []) + enhanced_pattern.get("tech_stack", [])
            
            reasoning = (f"New autonomous agent pattern created specifically for this requirement. "
                        f"Achieves {enhanced_pattern.get('autonomy_level', 0.8):.0%} autonomy through "
                        f"{', '.join(enhanced_pattern.get('reasoning_types', ['advanced']))} reasoning. "
                        f"Agent can handle: {', '.join(enhanced_pattern.get('decision_boundaries', {}).get('autonomous_decisions', ['standard operations'])[:2])}.")
            
            # Generate basic agent roles for custom pattern
            agent_name = await self._generate_agent_name(requirements)
            agent_roles = [
                {
                    "name": agent_name,
                    "responsibility": await self._generate_agent_responsibility(requirements, agent_name),
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
            
            # Determine feasibility - respect LLM analysis if available
            llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
            if llm_feasibility and llm_feasibility in ["Automatable", "Fully Automatable", "Partially Automatable", "Not Automatable"]:
                feasibility = llm_feasibility
                app_logger.info(f"Using LLM feasibility assessment for new agentic pattern: {llm_feasibility}")
            else:
                feasibility = enhanced_pattern.get("feasibility", "Fully Automatable")
                app_logger.info(f"No LLM feasibility found, using enhanced pattern feasibility: {feasibility}")
            
            app_logger.info(f"Created new APAT pattern {pattern_id} for session {session_id}")
            
            return Recommendation(
                pattern_id=pattern_id,
                feasibility=feasibility,
                confidence=min(1.0, confidence),
                tech_stack=tech_stack[:8],
                reasoning=reasoning,
                agent_roles=agent_roles,
                necessity_assessment=necessity_assessment
            )
            
        except Exception as e:
            app_logger.error(f"Failed to create new agentic pattern: {e}")
            return None
    
    async def _create_scope_limited_recommendation(self, 
                                                 requirements: Dict[str, Any],
                                                 autonomy_assessment: AutonomyAssessment,
                                                 necessity_assessment: Optional[AgenticNecessityAssessment] = None) -> List[Recommendation]:
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
                "responsibility": await self._generate_agent_responsibility(requirements, agent_name),
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
        
        # Determine feasibility - respect LLM analysis if available
        llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
        if llm_feasibility and llm_feasibility in ["Automatable", "Fully Automatable", "Partially Automatable", "Not Automatable"]:
            feasibility = llm_feasibility
            app_logger.info(f"Using LLM feasibility assessment for scope-limited recommendation: {llm_feasibility}")
        else:
            feasibility = "Partially Automatable"  # Default for scope-limited scenarios
            app_logger.info("No LLM feasibility found, using default 'Partially Automatable' for scope-limited recommendation")
        
        limited_recommendation = Recommendation(
            pattern_id="AGENTIC_DIGITAL_ASSISTANT",
            feasibility=feasibility,
            confidence=0.7,  # Still confident in agentic approach
            tech_stack=agentic_tech,
            reasoning=reasoning,
            agent_roles=agent_roles,
            necessity_assessment=necessity_assessment
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
        
        # Create domain-specific capabilities
        base_capabilities = [
            "task_execution",
            "decision_making", 
            "exception_handling",
            "learning_adaptation",
            "communication"
        ]
        
        # Add domain-specific capabilities based on the agent name/description
        if "order" in description.lower() or "Order" in agent_name:
            base_capabilities.extend([
                "order_processing",
                "workflow_coordination",
                "real_time_communication",
                "status_tracking",
                "validation_and_verification"
            ])
        elif "data" in description.lower() or "Data" in agent_name:
            base_capabilities.extend([
                "data_processing",
                "information_extraction",
                "data_validation",
                "storage_management"
            ])
        elif "workflow" in description.lower() or "Workflow" in agent_name:
            base_capabilities.extend([
                "process_automation",
                "task_orchestration",
                "workflow_optimization"
            ])
        
        # Generate proper agent responsibility using LLM
        agent_responsibility = await self._generate_agent_responsibility(requirements, agent_name)
        
        single_agent = AgentRole(
            name=agent_name,
            responsibility=agent_responsibility,
            capabilities=base_capabilities,
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
    
    async def _create_traditional_automation_recommendation(self, 
                                                          requirements: Dict[str, Any],
                                                          necessity_assessment: AgenticNecessityAssessment,
                                                          session_id: str) -> List[Recommendation]:
        """Create recommendation for traditional automation approach."""
        
        app_logger.info("Creating traditional automation recommendation")
        
        # Generate traditional tech stack
        tech_stack = await self._generate_traditional_tech_stack(requirements)
        
        # Create reasoning that explains why traditional automation is better
        reasoning = self._generate_traditional_reasoning(necessity_assessment, requirements)
        
        # Determine feasibility - respect LLM analysis if available
        llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
        if llm_feasibility and llm_feasibility in ["Automatable", "Fully Automatable", "Partially Automatable", "Not Automatable"]:
            feasibility = llm_feasibility
            app_logger.info(f"Using LLM feasibility assessment for traditional automation: {llm_feasibility}")
        else:
            feasibility = "Fully Automatable"  # Default for traditional automation
            app_logger.info("No LLM feasibility found, using default 'Fully Automatable' for traditional automation")
        
        # Create traditional automation recommendation
        recommendation = Recommendation(
            pattern_id="TRAD-AUTO-001",  # Traditional automation pattern
            feasibility=feasibility,
            confidence=necessity_assessment.confidence_level,
            tech_stack=tech_stack,
            reasoning=reasoning,
            agent_roles=[],  # No agent roles for traditional automation
            necessity_assessment=necessity_assessment  # Include the assessment
        )
        
        # Save the traditional pattern (fire and forget - don't block on save)
        asyncio.create_task(self._save_traditional_pattern(requirements, necessity_assessment, tech_stack, reasoning, session_id))
        
        app_logger.info(f"Created traditional automation recommendation with confidence {necessity_assessment.confidence_level:.2f}")
        
        return [recommendation]
    
    async def _generate_traditional_tech_stack(self, requirements: Dict[str, Any]) -> List[str]:
        """Generate appropriate tech stack for traditional automation."""
        
        description = requirements.get("description", "").lower()
        
        # Base traditional automation technologies
        tech_stack = []
        
        # Workflow engines
        if any(keyword in description for keyword in ["workflow", "process", "steps", "sequence"]):
            tech_stack.extend(["Apache Airflow", "Zapier", "Microsoft Power Automate"])
        
        # Data processing
        if any(keyword in description for keyword in ["data", "file", "document", "record"]):
            tech_stack.extend(["Apache Kafka", "ETL Tools", "Database Systems"])
        
        # Web automation
        if any(keyword in description for keyword in ["web", "browser", "form", "website"]):
            tech_stack.extend(["Selenium", "REST APIs", "Web Scraping Tools"])
        
        # Integration platforms
        if any(keyword in description for keyword in ["integrate", "connect", "sync", "api"]):
            tech_stack.extend(["MuleSoft", "Apache Camel", "API Gateway"])
        
        # Business process management
        if any(keyword in description for keyword in ["business process", "bpm", "workflow"]):
            tech_stack.extend(["Camunda", "jBPM", "Business Process Management"])
        
        # Restaurant/food service specific
        if any(keyword in description for keyword in ["order", "food", "restaurant", "kitchen"]):
            tech_stack.extend(["POS Systems", "Kitchen Display Systems", "Order Management Software"])
        
        # Default technologies if none detected
        if not tech_stack:
            tech_stack = ["Workflow Automation Platform", "Database System", "API Integration"]
        
        return tech_stack[:8]  # Limit to reasonable number
    
    def _generate_traditional_reasoning(self, necessity_assessment: AgenticNecessityAssessment, 
                                      requirements: Dict[str, Any]) -> str:
        """Generate reasoning for why traditional automation is recommended."""
        
        reasoning_parts = [
            f"Traditional automation approach recommended based on analysis showing {necessity_assessment.traditional_suitability_score:.0%} suitability for conventional workflow automation."
        ]
        
        # Add specific justifications
        if necessity_assessment.traditional_justification:
            reasoning_parts.append("Key factors supporting traditional automation:")
            for justification in necessity_assessment.traditional_justification[:3]:
                reasoning_parts.append(f"• {justification}")
        
        # Add efficiency benefits
        reasoning_parts.append("Traditional automation benefits: Lower complexity, faster implementation, proven reliability, and cost-effective maintenance.")
        
        # Add when to consider agentic upgrade
        if necessity_assessment.agentic_necessity_score > 0.4:
            reasoning_parts.append(f"Future consideration: If requirements evolve to need more complex reasoning or adaptation (current agentic score: {necessity_assessment.agentic_necessity_score:.0%}), consider upgrading to autonomous agent approach.")
        
        return " ".join(reasoning_parts)
    
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
            responsibility=await self._generate_agent_responsibility(requirements, agent_name),
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
    
    async def _generate_agent_responsibility(self, requirements: Dict[str, Any], agent_name: str) -> str:
        """Generate a meaningful agent responsibility description using LLM."""
        description = requirements.get('description', '')
        
        if not self.llm_provider:
            # Fallback if no LLM available
            return f"Autonomous agent responsible for automating the described workflow"
        
        prompt = f"""You are an expert in agentic AI systems. Given a user requirement, generate a concise, professional description of what an autonomous AI agent will DO to solve this problem.

USER REQUIREMENT:
{description}

AGENT NAME: {agent_name}

Generate a responsibility statement that describes the ACTIONS and CAPABILITIES the agent will perform, not the user's problem. Focus on:
- What the agent will automate
- Key processes it will handle
- Decisions it will make autonomously
- Systems it will integrate with

Format: "Autonomous agent responsible for [specific actions and capabilities]"

Examples:
- User: "I need help processing invoices" → Agent: "Autonomous agent responsible for extracting invoice data, validating payment terms, routing approvals, and updating accounting systems"
- User: "I want to automate customer support" → Agent: "Autonomous agent responsible for analyzing support tickets, categorizing issues, providing automated responses, and escalating complex cases"

Respond with ONLY the responsibility statement, no other text."""

        try:
            response = await self.llm_provider.generate(prompt, purpose="agent_responsibility_generation")
            
            # Clean up the response
            responsibility = response.strip()
            
            # Ensure it starts with appropriate text
            if not responsibility.lower().startswith(('autonomous agent', 'main autonomous agent')):
                responsibility = f"Autonomous agent responsible for {responsibility}"
            
            return responsibility
            
        except Exception as e:
            app_logger.error(f"Error generating agent responsibility: {e}")
            # Fallback to a generic but better description
            return f"Autonomous agent responsible for automating and optimizing the workflow described in the requirements"

    async def _generate_agent_name(self, requirements: Dict[str, Any], suffix: str = None) -> str:
        """Generate a meaningful agent name based on requirements with optional suffix for uniqueness."""
        
        description = requirements.get('description', '').lower()
        
        # Extract key domain/function words from description
        domain_keywords = {
            'order_management': ['order', 'orders', 'ordering', 'food', 'restaurant', 'kitchen', 'chef', 'wait', 'waitress', 'waiter', 'menu'],
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
                'order_management': 'Order Management Agent',
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
                    'order_management': 'Order',
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
    
    def _generate_agentic_pattern_id(self) -> str:
        """Generate a unique APAT pattern ID with duplicate validation.
        
        Returns:
            Unique pattern ID in format APAT-XXX
            
        Raises:
            ValueError: If unable to generate unique ID after multiple attempts
        """
        try:
            # Find the highest existing APAT pattern number from files
            pattern_library_path = Path("data/patterns")
            existing_patterns = list(pattern_library_path.glob("APAT-*.json"))
            max_num = 0
            existing_ids = set()
            
            for pattern_file in existing_patterns:
                try:
                    pattern_id = pattern_file.stem
                    existing_ids.add(pattern_id)
                    
                    # Extract number for max calculation
                    num_str = pattern_id.split("-")[1]
                    num = int(num_str)
                    max_num = max(max_num, num)
                except (IndexError, ValueError) as e:
                    app_logger.warning(f"Could not parse APAT pattern ID from file {pattern_file}: {e}")
                    continue
            
            # Generate new ID and validate uniqueness
            max_attempts = 100  # Prevent infinite loop
            for attempt in range(max_attempts):
                new_id = f"APAT-{max_num + 1 + attempt:03d}"
                
                if new_id not in existing_ids:
                    app_logger.info(f"Generated unique APAT pattern ID: {new_id}")
                    return new_id
                    
                app_logger.warning(f"APAT pattern ID {new_id} already exists, trying next number")
            
            # If we get here, we couldn't generate a unique ID
            raise ValueError(f"Unable to generate unique APAT pattern ID after {max_attempts} attempts")
            
        except Exception as e:
            app_logger.error(f"Error generating APAT pattern ID: {e}")
            # Fallback to UUID-based ID to ensure uniqueness
            import uuid
            fallback_id = f"APAT-{str(uuid.uuid4())[:8].upper()}"
            app_logger.warning(f"Using fallback UUID-based APAT pattern ID: {fallback_id}")
            return fallback_id
    
    async def _save_agentic_pattern(self, 
                                  enhanced_pattern: Dict[str, Any],
                                  requirements: Dict[str, Any],
                                  autonomy_assessment: AutonomyAssessment,
                                  session_id: str) -> bool:
        """Save the new APAT pattern to the pattern library.
        
        Args:
            enhanced_pattern: Enhanced pattern from pattern enhancer
            requirements: Original requirements
            autonomy_assessment: Autonomy assessment results
            session_id: Session ID for tracking
            
        Returns:
            True if pattern was saved successfully, False otherwise
        """
        try:
            pattern_library_path = Path("data/patterns")
            pattern_library_path.mkdir(exist_ok=True)
            
            # Create the APAT pattern structure similar to existing patterns
            agentic_pattern = {
                "pattern_id": enhanced_pattern["pattern_id"],
                "name": enhanced_pattern.get("name", f"Autonomous Agent Pattern"),
                "description": enhanced_pattern.get("description", requirements.get("description", "")),
                "feasibility": enhanced_pattern.get("feasibility", "Fully Automatable"),
                "pattern_type": enhanced_pattern.get("pattern_type", ["autonomous_agent"]),
                "autonomy_level": enhanced_pattern.get("autonomy_level", 0.85),
                "reasoning_capabilities": enhanced_pattern.get("reasoning_types", ["logical_reasoning", "pattern_matching"]),
                "decision_scope": enhanced_pattern.get("decision_boundaries", {
                    "autonomous_decisions": ["task_execution", "workflow_management", "exception_handling"],
                    "escalation_triggers": ["critical_errors", "policy_violations", "resource_limits"]
                }),
                "exception_handling": "Autonomous resolution with escalation for critical failures",
                "learning_mechanisms": ["feedback_incorporation", "pattern_recognition", "performance_optimization"],
                "tech_stack": enhanced_pattern.get("agentic_frameworks", []) + enhanced_pattern.get("tech_stack", []),
                "related_patterns": [],  # Will be populated as more patterns are created
                "confidence_score": enhanced_pattern.get("autonomy_level", 0.85),
                "constraints": {
                    "min_autonomy_level": 0.8,
                    "requires_human_oversight": False,
                    "compliance_requirements": requirements.get("compliance_requirements", []),
                    "data_sensitivity": requirements.get("data_sensitivity", "Internal")
                },
                "enhanced_pattern": {
                    "creation_session": session_id,
                    "autonomy_score": autonomy_assessment.overall_score,
                    "reasoning_complexity": autonomy_assessment.reasoning_complexity.value,
                    "decision_boundaries": autonomy_assessment.decision_boundaries,
                    "workflow_coverage": autonomy_assessment.workflow_coverage,
                    "created_timestamp": str(Path().cwd().stat().st_mtime)  # Simple timestamp
                }
            }
            
            # Save to file with better error handling
            pattern_file_path = pattern_library_path / f"{enhanced_pattern['pattern_id']}.json"
            
            # First, validate that the pattern can be serialized to JSON
            try:
                json_str = json.dumps(agentic_pattern, indent=2, ensure_ascii=False)
            except (TypeError, ValueError) as json_error:
                app_logger.error(f"JSON serialization failed for pattern {enhanced_pattern['pattern_id']}: {json_error}")
                return False
            
            # Write to file
            with open(pattern_file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            # Validate the written file
            try:
                with open(pattern_file_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Validate JSON is readable
                app_logger.info(f"Successfully saved and validated APAT pattern {enhanced_pattern['pattern_id']} to {pattern_file_path}")
                return True
            except json.JSONDecodeError as validation_error:
                app_logger.error(f"JSON validation failed for saved pattern {enhanced_pattern['pattern_id']}: {validation_error}")
                # Clean up the invalid file
                if pattern_file_path.exists():
                    pattern_file_path.unlink()
                return False
            
        except Exception as e:
            app_logger.error(f"Failed to save APAT pattern {enhanced_pattern.get('pattern_id', 'unknown')}: {e}")
            return False
    
    async def _save_multi_agent_pattern(self, 
                                      multi_agent_pattern: Dict[str, Any],
                                      design: 'MultiAgentSystemDesign',
                                      requirements: Dict[str, Any],
                                      autonomy_assessment: AutonomyAssessment,
                                      session_id: str) -> bool:
        """Save the multi-agent pattern to the pattern library.
        
        Args:
            multi_agent_pattern: Multi-agent pattern data
            design: Multi-agent system design
            requirements: Original requirements
            autonomy_assessment: Autonomy assessment results
            session_id: Session ID for tracking
            
        Returns:
            True if pattern was saved successfully, False otherwise
        """
        try:
            pattern_library_path = Path("data/patterns")
            pattern_library_path.mkdir(exist_ok=True)
            
            # Create the multi-agent APAT pattern structure
            agentic_pattern = {
                "pattern_id": multi_agent_pattern["pattern_id"],
                "name": multi_agent_pattern["name"],
                "description": f"{multi_agent_pattern['description']} for {requirements.get('description', 'complex automation task')}",
                "feasibility": "Fully Automatable",
                "pattern_type": ["multi_agent_system", design.architecture_type.value],
                "autonomy_level": design.autonomy_score,
                "reasoning_capabilities": ["collaborative_reasoning", "distributed_decision_making", "system_coordination"],
                "decision_scope": {
                    "autonomous_decisions": ["agent_coordination", "task_distribution", "resource_allocation", "exception_handling"],
                    "escalation_triggers": ["system_wide_failures", "conflicting_agent_decisions", "resource_exhaustion"]
                },
                "exception_handling": "Multi-agent collaborative resolution with system-level escalation",
                "learning_mechanisms": ["inter_agent_learning", "system_optimization", "performance_adaptation"],
                "tech_stack": multi_agent_pattern["tech_stack"],
                "agent_architecture": design.architecture_type.value,
                "input_requirements": [
                    "multi_agent_coordination",
                    "distributed_processing",
                    "system_monitoring",
                    "error_handling"
                ],
                "related_patterns": ["APAT-001", "APAT-002"],
                "confidence_score": design.autonomy_score,
                "constraints": {
                    "banned_tools": [],
                    "required_integrations": multi_agent_pattern.get("tech_stack", [])[:3]  # First 3 as required
                },
                "domain": self._extract_domain_from_requirements(requirements),
                "complexity": "High",
                "estimated_effort": "8-12 weeks",
                "reasoning_types": ["logical", "causal", "collaborative"],
                "decision_boundaries": {
                    "autonomous_decisions": ["agent_coordination", "task_distribution", "resource_allocation"],
                    "escalation_triggers": ["system_failures", "conflicting_decisions", "resource_exhaustion"]
                },
                "autonomy_assessment": {
                    "overall_score": autonomy_assessment.overall_score,
                    "reasoning_complexity": autonomy_assessment.reasoning_complexity.value,
                    "workflow_coverage": autonomy_assessment.workflow_coverage,
                    "decision_independence": "high"
                },
                "self_monitoring_capabilities": [
                    "performance_tracking",
                    "error_detection",
                    "system_health_monitoring"
                ],
                "integration_requirements": multi_agent_pattern.get("tech_stack", [])[-2:],  # Last 2 as integration
                "created_from_session": session_id,
                "auto_generated": True,
                "llm_insights": [
                    "Multi-agent coordination enables distributed processing",
                    "Collaborative reasoning improves decision accuracy",
                    "System-level monitoring ensures reliability"
                ],
                "llm_challenges": [
                    "Coordinating multiple agents effectively",
                    "Managing distributed decision making",
                    "Ensuring system-wide consistency"
                ],
                "llm_recommended_approach": f"Implement {design.architecture_type.value} architecture with specialized agent roles, use robust communication protocols, maintain comprehensive monitoring and error handling.",
                "enhanced_by_llm": True,
                "enhanced_from_session": session_id,
                "color": "🟢"
            }
            
            # Save to file with better error handling
            pattern_file_path = pattern_library_path / f"{multi_agent_pattern['pattern_id']}.json"
            
            # First, validate that the pattern can be serialized to JSON
            try:
                json_str = json.dumps(agentic_pattern, indent=2, ensure_ascii=False)
            except (TypeError, ValueError) as json_error:
                app_logger.error(f"JSON serialization failed for pattern {multi_agent_pattern['pattern_id']}: {json_error}")
                return False
            
            # Write to file
            with open(pattern_file_path, 'w', encoding='utf-8') as f:
                f.write(json_str)
            
            # Validate the written file
            try:
                with open(pattern_file_path, 'r', encoding='utf-8') as f:
                    json.load(f)  # Validate JSON is readable
                app_logger.info(f"Successfully saved and validated multi-agent APAT pattern {multi_agent_pattern['pattern_id']} to {pattern_file_path}")
                return True
            except json.JSONDecodeError as validation_error:
                app_logger.error(f"JSON validation failed for saved pattern {multi_agent_pattern['pattern_id']}: {validation_error}")
                # Clean up the invalid file
                if pattern_file_path.exists():
                    pattern_file_path.unlink()
                return False
            
        except Exception as e:
            app_logger.error(f"Failed to save multi-agent APAT pattern {multi_agent_pattern.get('pattern_id', 'unknown')}: {e}")
            return False

    def _extract_domain_from_requirements(self, requirements: Dict[str, Any]) -> str:
        """Extract domain from requirements description."""
        description = requirements.get('description', '').lower()
        
        # Domain mapping based on keywords
        domain_keywords = {
            'financial': ['payment', 'credit', 'financial', 'money', 'budget', 'invoice'],
            'incident_management': ['incident', 'alert', 'monitoring', 'outage', 'failure'],
            'user_management': ['user', 'account', 'authentication', 'profile'],
            'data_processing': ['data', 'analytics', 'processing', 'analysis'],
            'communication': ['email', 'notification', 'message', 'chat'],
            'workflow_automation': ['workflow', 'process', 'automation', 'task']
        }
        
        for domain, keywords in domain_keywords.items():
            if any(keyword in description for keyword in keywords):
                return domain
        
        return 'general_automation'

    async def _save_traditional_pattern(self, 
                                      requirements: Dict[str, Any],
                                      necessity_assessment: AgenticNecessityAssessment,
                                      tech_stack: List[str],
                                      reasoning: str,
                                      session_id: str) -> bool:
        """Save traditional automation pattern to the pattern library."""
        try:
            pattern_library_path = Path("data/patterns")
            pattern_library_path.mkdir(parents=True, exist_ok=True)
            
            # Check if TRAD-AUTO-001 already exists
            pattern_file_path = pattern_library_path / "TRAD-AUTO-001.json"
            if pattern_file_path.exists():
                app_logger.info("TRAD-AUTO-001 pattern already exists, skipping save")
                return True
            
            # Create traditional automation pattern
            traditional_pattern = {
                "pattern_id": "TRAD-AUTO-001",
                "name": "Traditional Workflow Automation",
                "description": "Conventional automation approach using established workflow engines, APIs, and integration tools for predictable, rule-based processes.",
                "feasibility": "Fully Automatable",
                "tech_stack": tech_stack,
                "reasoning": reasoning,
                "category": "Traditional Automation",
                "tags": ["workflow", "automation", "integration", "api", "traditional"],
                "autonomy_level": 0.3,  # Low autonomy - rule-based
                "complexity": "Medium",
                "implementation_time": "2-4 weeks",
                "maintenance_effort": "Low",
                "use_cases": [
                    "Data processing workflows",
                    "API integrations", 
                    "File processing automation",
                    "Scheduled tasks",
                    "Simple business process automation"
                ],
                "advantages": [
                    "Lower complexity and faster implementation",
                    "Proven reliability and stability",
                    "Cost-effective maintenance",
                    "Well-established tooling and expertise",
                    "Predictable behavior and outcomes"
                ],
                "limitations": [
                    "Limited adaptability to changing requirements",
                    "Requires manual intervention for exceptions",
                    "Cannot handle complex reasoning or decision-making",
                    "Rigid rule-based logic",
                    "Limited learning capabilities"
                ],
                "when_to_use": [
                    "Predictable, rule-based processes",
                    "Well-defined workflows with clear steps",
                    "Limited exception handling requirements",
                    "Cost-sensitive implementations",
                    "Quick deployment needs"
                ],
                "upgrade_path": "Consider agentic AI when requirements include complex reasoning, exception handling, or adaptive behavior",
                "metadata": {
                    "creation_session": session_id,
                    "necessity_score": necessity_assessment.traditional_suitability_score,
                    "confidence_level": necessity_assessment.confidence_level,
                    "solution_type": "traditional_automation",
                    "created_timestamp": str(Path().cwd().stat().st_mtime)
                }
            }
            
            # Save to file
            with open(pattern_file_path, 'w', encoding='utf-8') as f:
                json.dump(traditional_pattern, f, indent=2, ensure_ascii=False)
            
            app_logger.info(f"Successfully saved traditional automation pattern TRAD-AUTO-001 to {pattern_file_path}")
            
            # Log pattern match for analytics
            try:
                log_pattern_match(
                    session_id=session_id,
                    pattern_id="TRAD-AUTO-001",
                    match_score=necessity_assessment.traditional_suitability_score,
                    match_type="traditional_automation"
                )
            except Exception as e:
                app_logger.warning(f"Failed to log pattern match for TRAD-AUTO-001: {e}")
            
            return True
            
        except Exception as e:
            app_logger.error(f"Failed to save traditional automation pattern TRAD-AUTO-001: {e}")
            return False