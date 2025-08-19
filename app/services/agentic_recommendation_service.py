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
        
        # Step 5: Generate agentic recommendations
        recommendations = []
        
        # Process agentic pattern matches
        for match in agentic_matches:
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
        
        return Recommendation(
            pattern_id=match.pattern_id,
            feasibility=feasibility,
            confidence=confidence,
            tech_stack=tech_stack,
            reasoning=reasoning
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
        
        return Recommendation(
            pattern_id="MULTI_AGENT_SYSTEM",
            feasibility="Fully Automatable",
            confidence=confidence,
            tech_stack=tech_stack,
            reasoning=reasoning
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
            
            return Recommendation(
                pattern_id=enhanced_pattern["pattern_id"],
                feasibility=enhanced_pattern.get("feasibility", "Fully Automatable"),
                confidence=min(1.0, confidence),
                tech_stack=tech_stack[:8],
                reasoning=reasoning
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
        
        limited_recommendation = Recommendation(
            pattern_id="AGENTIC_DIGITAL_ASSISTANT",
            feasibility="Partially Automatable",
            confidence=0.7,  # Still confident in agentic approach
            tech_stack=agentic_tech,
            reasoning=reasoning
        )
        
        return [limited_recommendation]
    
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