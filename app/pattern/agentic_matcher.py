"""Agentic pattern matching engine that prioritizes autonomous solutions."""

import json
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from pathlib import Path

from app.services.autonomy_assessor import AutonomyAssessment, AutonomyAssessor
from app.services.pattern_agentic_enhancer import PatternAgenticEnhancer
from app.pattern.matcher import PatternMatcher
from app.llm.base import LLMProvider
from app.utils.logger import app_logger


@dataclass
class AgenticPatternMatch:
    pattern_id: str
    base_pattern: Dict[str, Any]
    enhanced_pattern: Dict[str, Any]
    autonomy_score: float
    reasoning_capabilities: List[str]
    decision_scope: Dict[str, Any]
    exception_handling: str
    multi_agent_potential: bool
    recommended_frameworks: List[str]
    confidence: float
    rationale: str


class AgenticPatternMatcher:
    """Pattern matcher that prioritizes autonomous agent solutions."""
    
    def __init__(self,
                 autonomy_assessor: AutonomyAssessor,
                 pattern_enhancer: PatternAgenticEnhancer,
                 base_matcher: PatternMatcher,
                 llm_provider: LLMProvider):
        self.autonomy_assessor = autonomy_assessor
        self.pattern_enhancer = pattern_enhancer
        self.base_matcher = base_matcher
        self.llm_provider = llm_provider
        
        # Agentic scoring weights
        self.scoring_weights = {
            "autonomy_level": 0.4,      # Heavily weight autonomy
            "reasoning_capability": 0.25,
            "decision_independence": 0.2,
            "exception_handling": 0.1,
            "learning_potential": 0.05
        }
        
        # Minimum autonomy threshold for recommendations
        self.min_autonomy_threshold = 0.7
    
    async def match_agentic_patterns(self, 
                                   requirements: Dict[str, Any],
                                   autonomy_assessment: AutonomyAssessment,
                                   top_k: int = 5) -> List[AgenticPatternMatch]:
        """Match patterns prioritizing autonomous agent solutions."""
        
        app_logger.info("Matching agentic patterns with autonomy prioritization")
        
        # Get base pattern matches (if base matcher is available)
        base_matches = []
        if self.base_matcher:
            base_matches = await self.base_matcher.match_patterns(requirements, top_k * 2)
        
        # Load agentic patterns (APAT-* patterns)
        agentic_patterns = await self._load_agentic_patterns()
        
        # Score and enhance all patterns for autonomy
        scored_patterns = []
        
        # Process existing agentic patterns first (higher priority)
        for pattern in agentic_patterns:
            autonomy_score = self._score_pattern_autonomy(pattern, autonomy_assessment)
            
            if autonomy_score >= self.min_autonomy_threshold:
                agentic_match = AgenticPatternMatch(
                    pattern_id=pattern["pattern_id"],
                    base_pattern=pattern,
                    enhanced_pattern=pattern,  # Already agentic
                    autonomy_score=autonomy_score,
                    reasoning_capabilities=pattern.get("reasoning_types", []),
                    decision_scope=pattern.get("decision_boundaries", {}),
                    exception_handling=self._extract_exception_handling(pattern),
                    multi_agent_potential=pattern.get("agent_architecture") != "single_agent",
                    recommended_frameworks=pattern.get("agentic_frameworks", []),
                    confidence=pattern.get("confidence_score", 0.8),
                    rationale=self._generate_agentic_rationale(pattern, autonomy_assessment)
                )
                scored_patterns.append(agentic_match)
        
        # Process and enhance base patterns
        for match in base_matches:
            try:
                # Load full pattern data
                pattern = await self._load_pattern_by_id(match.pattern_id)
                if not pattern:
                    continue
                
                # Enhance pattern for autonomy
                enhanced_pattern = await self.pattern_enhancer.enhance_for_autonomy(
                    pattern, requirements
                )
                
                # Score enhanced pattern
                autonomy_score = self._score_pattern_autonomy(enhanced_pattern, autonomy_assessment)
                
                # Only include if meets autonomy threshold
                if autonomy_score >= self.min_autonomy_threshold:
                    agentic_match = AgenticPatternMatch(
                        pattern_id=pattern["pattern_id"],
                        base_pattern=pattern,
                        enhanced_pattern=enhanced_pattern,
                        autonomy_score=autonomy_score,
                        reasoning_capabilities=enhanced_pattern.get("reasoning_types", []),
                        decision_scope=enhanced_pattern.get("decision_boundaries", {}),
                        exception_handling=self._extract_exception_handling(enhanced_pattern),
                        multi_agent_potential=enhanced_pattern.get("agent_architecture") != "single_agent",
                        recommended_frameworks=enhanced_pattern.get("agentic_frameworks", []),
                        confidence=enhanced_pattern.get("confidence_score", 0.8),
                        rationale=self._generate_enhancement_rationale(pattern, enhanced_pattern, autonomy_assessment)
                    )
                    scored_patterns.append(agentic_match)
                    
            except Exception as e:
                app_logger.error(f"Failed to enhance pattern {match.pattern_id}: {e}")
                continue
        
        # Sort by autonomy score (highest first)
        scored_patterns.sort(key=lambda x: x.autonomy_score, reverse=True)
        
        # Apply constraint filtering
        filtered_patterns = await self._apply_agentic_constraints(scored_patterns, requirements)
        
        app_logger.info(f"Matched {len(filtered_patterns)} agentic patterns (from {len(base_matches)} base matches)")
        
        return filtered_patterns[:top_k]
    
    def _score_pattern_autonomy(self, 
                              pattern: Dict[str, Any], 
                              assessment: AutonomyAssessment) -> float:
        """Score pattern based on autonomy capabilities."""
        
        weights = self.scoring_weights
        
        # Base autonomy score from pattern
        autonomy_level = pattern.get("autonomy_level", 0.5)
        
        # Reasoning capability score
        pattern_reasoning = set(pattern.get("reasoning_types", []))
        required_reasoning = set(assessment.reasoning_requirements)
        reasoning_coverage = len(pattern_reasoning.intersection(required_reasoning)) / max(len(required_reasoning), 1)
        
        # Decision independence score
        decision_authority = pattern.get("decision_boundaries", {}).get("decision_authority_level", "medium")
        authority_scores = {"low": 0.3, "medium": 0.6, "high": 0.8, "full": 1.0}
        decision_score = authority_scores.get(decision_authority, 0.6)
        
        # Exception handling score
        exception_strategy = pattern.get("exception_handling_strategy", {})
        exception_approaches = len(exception_strategy.get("autonomous_resolution_approaches", []))
        exception_score = min(1.0, exception_approaches / 3.0)  # Normalize to 3 approaches
        
        # Learning potential score
        learning_mechanisms = len(pattern.get("learning_mechanisms", []))
        learning_score = min(1.0, learning_mechanisms / 4.0)  # Normalize to 4 mechanisms
        
        # Calculate weighted score
        total_score = (
            autonomy_level * weights["autonomy_level"] +
            reasoning_coverage * weights["reasoning_capability"] +
            decision_score * weights["decision_independence"] +
            exception_score * weights["exception_handling"] +
            learning_score * weights["learning_potential"]
        )
        
        # Bonus for agentic pattern types
        agentic_types = [
            "agentic_reasoning", "autonomous_decision", "self_healing",
            "continuous_learning", "exception_reasoning", "multi_agent"
        ]
        pattern_types = pattern.get("pattern_type", [])
        agentic_bonus = sum(0.05 for ptype in pattern_types if ptype in agentic_types)
        
        # Penalty for human-in-the-loop requirements
        human_penalty = -0.2 if "human_in_loop" in pattern_types else 0
        
        # Alignment bonus with assessment
        alignment_bonus = 0.1 if assessment.overall_score > 0.8 else 0
        
        final_score = min(1.0, total_score + agentic_bonus + human_penalty + alignment_bonus)
        
        app_logger.debug(f"Pattern {pattern.get('pattern_id')} autonomy score: {final_score:.3f}")
        
        return final_score
    
    async def _load_agentic_patterns(self) -> List[Dict[str, Any]]:
        """Load all agentic patterns (APAT-* patterns)."""
        
        patterns = []
        pattern_dir = Path("data/patterns")
        
        if not pattern_dir.exists():
            app_logger.warning("Pattern directory not found")
            return patterns
        
        # Load APAT patterns (agentic patterns)
        for pattern_file in pattern_dir.glob("APAT-*.json"):
            try:
                with open(pattern_file, 'r') as f:
                    pattern = json.load(f)
                    patterns.append(pattern)
            except Exception as e:
                app_logger.error(f"Failed to load agentic pattern {pattern_file}: {e}")
        
        app_logger.info(f"Loaded {len(patterns)} agentic patterns")
        return patterns
    
    async def _load_pattern_by_id(self, pattern_id: str) -> Optional[Dict[str, Any]]:
        """Load a specific pattern by ID."""
        
        pattern_file = Path(f"data/patterns/{pattern_id}.json")
        
        if not pattern_file.exists():
            app_logger.warning(f"Pattern file not found: {pattern_file}")
            return None
        
        try:
            with open(pattern_file, 'r') as f:
                return json.load(f)
        except Exception as e:
            app_logger.error(f"Failed to load pattern {pattern_id}: {e}")
            return None
    
    def _extract_exception_handling(self, pattern: Dict[str, Any]) -> str:
        """Extract exception handling strategy description."""
        
        strategy = pattern.get("exception_handling_strategy", {})
        
        if isinstance(strategy, dict):
            approaches = strategy.get("autonomous_resolution_approaches", [])
            if approaches:
                return f"Autonomous resolution through: {', '.join(approaches[:2])}"
            else:
                return "Standard exception handling with escalation"
        else:
            return str(strategy)
    
    def _generate_agentic_rationale(self, 
                                  pattern: Dict[str, Any],
                                  assessment: AutonomyAssessment) -> str:
        """Generate rationale for agentic pattern match."""
        
        autonomy_level = pattern.get("autonomy_level", 0.5)
        reasoning_types = pattern.get("reasoning_types", [])
        architecture = pattern.get("agent_architecture", "single_agent")
        
        rationale = f"This agentic pattern achieves {autonomy_level:.0%} autonomy through {', '.join(reasoning_types[:2])} reasoning. "
        
        if architecture != "single_agent":
            rationale += f"Uses {architecture.replace('_', ' ')} architecture for complex coordination. "
        
        decision_authority = pattern.get("decision_boundaries", {}).get("decision_authority_level", "medium")
        rationale += f"Agent has {decision_authority} decision-making authority with autonomous exception handling."
        
        return rationale
    
    def _generate_enhancement_rationale(self, 
                                      original: Dict[str, Any],
                                      enhanced: Dict[str, Any],
                                      assessment: AutonomyAssessment) -> str:
        """Generate rationale for enhanced pattern."""
        
        original_feasibility = original.get("feasibility", "Partially Automatable")
        enhanced_autonomy = enhanced.get("autonomy_level", 0.8)
        
        rationale = f"Enhanced from '{original_feasibility}' to achieve {enhanced_autonomy:.0%} autonomy. "
        
        reasoning_types = enhanced.get("reasoning_types", [])
        if reasoning_types:
            rationale += f"Added {', '.join(reasoning_types[:2])} reasoning capabilities. "
        
        decision_boundaries = enhanced.get("decision_boundaries", {})
        autonomous_decisions = decision_boundaries.get("autonomous_decisions", [])
        if autonomous_decisions:
            rationale += f"Agent can autonomously handle: {autonomous_decisions[0]}."
        
        return rationale
    
    async def _apply_agentic_constraints(self, 
                                       patterns: List[AgenticPatternMatch],
                                       requirements: Dict[str, Any]) -> List[AgenticPatternMatch]:
        """Apply agentic-specific constraints and filtering."""
        
        filtered_patterns = []
        
        # Get constraint preferences
        constraints = requirements.get("constraints", {})
        banned_tools = constraints.get("banned_tools", [])
        required_integrations = constraints.get("required_integrations", [])
        
        # Agentic framework preferences
        preferred_frameworks = [
            "LangChain", "AutoGPT", "CrewAI", "Microsoft Semantic Kernel",
            "OpenAI Assistants API", "Anthropic Claude Computer Use"
        ]
        
        for pattern in patterns:
            # Check if pattern uses banned tools
            pattern_tech = pattern.enhanced_pattern.get("tech_stack", [])
            if any(banned in " ".join(pattern_tech).lower() for banned in [tool.lower() for tool in banned_tools]):
                app_logger.debug(f"Filtered out pattern {pattern.pattern_id} due to banned tools")
                continue
            
            # Boost patterns that use preferred agentic frameworks
            pattern_frameworks = pattern.enhanced_pattern.get("agentic_frameworks", [])
            if any(framework in pattern_frameworks for framework in preferred_frameworks):
                pattern.autonomy_score = min(1.0, pattern.autonomy_score * 1.1)  # 10% boost
            
            # Check required integrations
            pattern_integrations = pattern.enhanced_pattern.get("constraints", {}).get("required_integrations", [])
            integration_coverage = 0
            if required_integrations:
                covered_integrations = sum(1 for req in required_integrations 
                                         if any(req.lower() in integration.lower() 
                                               for integration in pattern_integrations))
                integration_coverage = covered_integrations / len(required_integrations)
            
            # Boost patterns with good integration coverage
            if integration_coverage > 0.5:
                pattern.autonomy_score = min(1.0, pattern.autonomy_score * (1 + integration_coverage * 0.1))
            
            filtered_patterns.append(pattern)
        
        # Re-sort after constraint adjustments
        filtered_patterns.sort(key=lambda x: x.autonomy_score, reverse=True)
        
        return filtered_patterns


class AutonomyScoringEngine:
    """Engine for scoring patterns based on autonomy capabilities."""
    
    def __init__(self):
        self.autonomy_factors = {
            "reasoning_depth": 0.3,
            "decision_scope": 0.25,
            "exception_handling": 0.2,
            "learning_capability": 0.15,
            "self_monitoring": 0.1
        }
    
    def calculate_autonomy_score(self, 
                               pattern: Dict[str, Any],
                               requirements: Dict[str, Any]) -> float:
        """Calculate comprehensive autonomy score for a pattern."""
        
        # Reasoning depth score
        reasoning_types = pattern.get("reasoning_types", [])
        reasoning_score = min(1.0, len(reasoning_types) / 4.0)  # Normalize to 4 types
        
        # Decision scope score
        decision_boundaries = pattern.get("decision_boundaries", {})
        autonomous_decisions = decision_boundaries.get("autonomous_decisions", [])
        decision_score = min(1.0, len(autonomous_decisions) / 5.0)  # Normalize to 5 decisions
        
        # Exception handling score
        exception_strategy = pattern.get("exception_handling_strategy", {})
        resolution_approaches = exception_strategy.get("autonomous_resolution_approaches", [])
        exception_score = min(1.0, len(resolution_approaches) / 3.0)  # Normalize to 3 approaches
        
        # Learning capability score
        learning_mechanisms = pattern.get("learning_mechanisms", [])
        learning_score = min(1.0, len(learning_mechanisms) / 4.0)  # Normalize to 4 mechanisms
        
        # Self-monitoring score
        monitoring_capabilities = pattern.get("self_monitoring_capabilities", [])
        monitoring_score = min(1.0, len(monitoring_capabilities) / 3.0)  # Normalize to 3 capabilities
        
        # Calculate weighted score
        total_score = (
            reasoning_score * self.autonomy_factors["reasoning_depth"] +
            decision_score * self.autonomy_factors["decision_scope"] +
            exception_score * self.autonomy_factors["exception_handling"] +
            learning_score * self.autonomy_factors["learning_capability"] +
            monitoring_score * self.autonomy_factors["self_monitoring"]
        )
        
        return min(1.0, total_score)