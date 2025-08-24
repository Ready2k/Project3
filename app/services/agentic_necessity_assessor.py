"""Agentic Necessity Assessor - Determines if requirements need agentic AI or traditional automation."""

import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.llm.base import LLMProvider
from app.utils.logger import app_logger


class SolutionType(Enum):
    """Types of automation solutions."""
    TRADITIONAL_AUTOMATION = "traditional_automation"
    AGENTIC_AI = "agentic_ai"
    HYBRID = "hybrid"


@dataclass
class AgenticNecessityFactors:
    """Factors that influence whether agentic AI is necessary."""
    
    # Complexity factors (favor agentic)
    reasoning_complexity_score: float  # 0-1, complex reasoning needs
    decision_uncertainty_score: float  # 0-1, unpredictable scenarios
    exception_handling_complexity: float  # 0-1, creative problem solving needed
    adaptation_requirements: float  # 0-1, learning and adaptation needed
    
    # Simplicity factors (favor traditional)
    workflow_predictability: float  # 0-1, predictable process flow
    rule_based_decisions: float  # 0-1, clear decision rules exist
    data_transformation_focus: float  # 0-1, mainly data processing
    fixed_process_flow: float  # 0-1, unchanging workflow
    
    # Context factors
    domain_complexity: float  # 0-1, domain-specific complexity
    integration_complexity: float  # 0-1, system integration needs
    real_time_requirements: float  # 0-1, real-time processing needs
    
    # Calculated scores
    agentic_necessity_score: float  # 0-1, overall necessity for agentic approach
    traditional_suitability_score: float  # 0-1, suitability for traditional automation


@dataclass
class AgenticNecessityAssessment:
    """Assessment of whether agentic AI is necessary for the requirement."""
    
    recommended_solution_type: SolutionType
    agentic_necessity_score: float
    traditional_suitability_score: float
    confidence_level: float
    
    # Detailed factors
    factors: AgenticNecessityFactors
    
    # Reasoning
    agentic_justification: List[str]  # Why agentic AI is/isn't needed
    traditional_justification: List[str]  # Why traditional automation would/wouldn't work
    recommendation_reasoning: str
    
    # Thresholds used
    agentic_threshold: float
    traditional_threshold: float


class AgenticNecessityAssessor:
    """Service for assessing whether requirements need agentic AI or traditional automation."""
    
    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        
        # Import configuration service for dynamic thresholds
        from app.services.configuration_service import get_config
        self.config_service = get_config()
        
        # Use configurable thresholds
        self.agentic_necessity_threshold = self.config_service.autonomy.agentic_necessity_threshold
        self.traditional_suitability_threshold = self.config_service.autonomy.traditional_suitability_threshold
        self.hybrid_zone_threshold = self.config_service.autonomy.hybrid_zone_threshold
    
    async def assess_agentic_necessity(self, requirements: Dict[str, Any]) -> AgenticNecessityAssessment:
        """Assess whether the requirement needs agentic AI or traditional automation."""
        
        app_logger.info("Assessing agentic necessity for requirements")
        
        description = requirements.get("description", "")
        domain = requirements.get("domain", "")
        
        # Analyze complexity factors that favor agentic solutions
        agentic_factors = await self._analyze_agentic_factors(description, domain)
        
        # Analyze simplicity factors that favor traditional automation
        traditional_factors = await self._analyze_traditional_factors(description, domain)
        
        # Calculate necessity factors
        factors = self._calculate_necessity_factors(agentic_factors, traditional_factors, description)
        
        # Determine recommended solution type
        solution_type, reasoning = self._determine_solution_type(factors)
        
        # Generate justifications
        agentic_justification = self._generate_agentic_justification(factors, description)
        traditional_justification = self._generate_traditional_justification(factors, description)
        
        # Calculate confidence based on score separation
        confidence = self._calculate_confidence(factors)
        
        assessment = AgenticNecessityAssessment(
            recommended_solution_type=solution_type,
            agentic_necessity_score=factors.agentic_necessity_score,
            traditional_suitability_score=factors.traditional_suitability_score,
            confidence_level=confidence,
            factors=factors,
            agentic_justification=agentic_justification,
            traditional_justification=traditional_justification,
            recommendation_reasoning=reasoning,
            agentic_threshold=self.agentic_necessity_threshold,
            traditional_threshold=self.traditional_suitability_threshold
        )
        
        app_logger.info(f"Agentic necessity assessment: {solution_type.value} (confidence: {confidence:.2f})")
        
        return assessment
    
    async def _analyze_agentic_factors(self, description: str, domain: str) -> Dict[str, float]:
        """Analyze factors that indicate need for agentic AI."""
        
        factors = {}
        desc_lower = description.lower()
        
        # Reasoning complexity indicators
        reasoning_keywords = [
            "complex decision", "analyze", "evaluate", "assess", "determine best",
            "optimize", "predict", "recommend", "intelligent", "smart",
            "contextual", "adaptive", "personalized", "strategic"
        ]
        factors["reasoning_complexity"] = self._calculate_keyword_score(desc_lower, reasoning_keywords)
        
        # Decision uncertainty indicators
        uncertainty_keywords = [
            "unpredictable", "variable", "changing", "dynamic", "flexible",
            "exception", "edge case", "unusual", "unexpected", "varies",
            "depends on", "situational", "contextual"
        ]
        factors["decision_uncertainty"] = self._calculate_keyword_score(desc_lower, uncertainty_keywords)
        
        # Exception handling complexity
        exception_keywords = [
            "handle exceptions", "error recovery", "fallback", "alternative",
            "problem solving", "troubleshoot", "resolve issues", "creative solution",
            "adapt", "learn from", "improve"
        ]
        factors["exception_handling"] = self._calculate_keyword_score(desc_lower, exception_keywords)
        
        # Adaptation requirements
        adaptation_keywords = [
            "learn", "improve", "adapt", "evolve", "optimize over time",
            "feedback", "experience", "pattern recognition", "self-improving",
            "machine learning", "AI", "intelligent"
        ]
        factors["adaptation"] = self._calculate_keyword_score(desc_lower, adaptation_keywords)
        
        # Domain complexity boost
        complex_domains = [
            "healthcare", "finance", "legal", "research", "analysis",
            "strategy", "planning", "negotiation", "diagnosis"
        ]
        factors["domain_complexity"] = self._calculate_keyword_score(domain.lower(), complex_domains)
        
        return factors
    
    async def _analyze_traditional_factors(self, description: str, domain: str) -> Dict[str, float]:
        """Analyze factors that indicate suitability for traditional automation."""
        
        factors = {}
        desc_lower = description.lower()
        
        # Workflow predictability indicators
        predictable_keywords = [
            "standard process", "routine", "regular", "consistent", "same steps",
            "fixed workflow", "predetermined", "established process", "standard operating",
            "always", "every time", "systematic"
        ]
        factors["workflow_predictability"] = self._calculate_keyword_score(desc_lower, predictable_keywords)
        
        # Rule-based decision indicators
        rule_keywords = [
            "if then", "rules", "criteria", "conditions", "requirements",
            "policy", "procedure", "guideline", "standard", "specification",
            "validate", "check", "verify", "confirm"
        ]
        factors["rule_based"] = self._calculate_keyword_score(desc_lower, rule_keywords)
        
        # Data transformation focus
        data_keywords = [
            "convert", "transform", "format", "parse", "extract", "process data",
            "import", "export", "migrate", "sync", "transfer", "copy",
            "database", "file", "document", "record"
        ]
        factors["data_transformation"] = self._calculate_keyword_score(desc_lower, data_keywords)
        
        # Fixed process flow indicators
        fixed_keywords = [
            "step 1", "step 2", "first", "then", "next", "finally",
            "sequence", "order", "workflow", "process", "procedure",
            "manual", "current process", "existing process"
        ]
        factors["fixed_process"] = self._calculate_keyword_score(desc_lower, fixed_keywords)
        
        # Simple domains
        simple_domains = [
            "data entry", "form processing", "file management", "basic workflow",
            "simple automation", "routine tasks", "administrative"
        ]
        factors["simple_domain"] = self._calculate_keyword_score(domain.lower(), simple_domains)
        
        return factors
    
    def _calculate_keyword_score(self, text: str, keywords: List[str]) -> float:
        """Calculate score based on keyword presence and frequency."""
        if not text or not keywords:
            return 0.0
        
        matches = 0
        total_words = len(text.split())
        
        for keyword in keywords:
            if keyword in text:
                matches += text.count(keyword)
        
        # Normalize by text length and keyword count
        score = min(1.0, (matches * 2) / max(1, len(keywords)))
        return score
    
    def _calculate_necessity_factors(self, agentic_factors: Dict[str, float], 
                                   traditional_factors: Dict[str, float], 
                                   description: str) -> AgenticNecessityFactors:
        """Calculate overall necessity factors."""
        
        # Calculate agentic necessity score (weighted average)
        agentic_weights = {
            "reasoning_complexity": 0.3,
            "decision_uncertainty": 0.25,
            "exception_handling": 0.2,
            "adaptation": 0.15,
            "domain_complexity": 0.1
        }
        
        agentic_score = sum(
            agentic_factors.get(factor, 0) * weight 
            for factor, weight in agentic_weights.items()
        )
        
        # Calculate traditional suitability score (weighted average)
        traditional_weights = {
            "workflow_predictability": 0.3,
            "rule_based": 0.25,
            "data_transformation": 0.2,
            "fixed_process": 0.15,
            "simple_domain": 0.1
        }
        
        traditional_score = sum(
            traditional_factors.get(factor, 0) * weight 
            for factor, weight in traditional_weights.items()
        )
        
        # Additional context factors
        integration_complexity = self._assess_integration_complexity(description)
        real_time_needs = self._assess_real_time_requirements(description)
        
        return AgenticNecessityFactors(
            reasoning_complexity_score=agentic_factors.get("reasoning_complexity", 0),
            decision_uncertainty_score=agentic_factors.get("decision_uncertainty", 0),
            exception_handling_complexity=agentic_factors.get("exception_handling", 0),
            adaptation_requirements=agentic_factors.get("adaptation", 0),
            workflow_predictability=traditional_factors.get("workflow_predictability", 0),
            rule_based_decisions=traditional_factors.get("rule_based", 0),
            data_transformation_focus=traditional_factors.get("data_transformation", 0),
            fixed_process_flow=traditional_factors.get("fixed_process", 0),
            domain_complexity=agentic_factors.get("domain_complexity", 0),
            integration_complexity=integration_complexity,
            real_time_requirements=real_time_needs,
            agentic_necessity_score=agentic_score,
            traditional_suitability_score=traditional_score
        )
    
    def _assess_integration_complexity(self, description: str) -> float:
        """Assess complexity of system integrations."""
        integration_keywords = [
            "multiple systems", "integrate", "api", "connect", "sync",
            "third party", "external", "legacy system", "database"
        ]
        return self._calculate_keyword_score(description.lower(), integration_keywords)
    
    def _assess_real_time_requirements(self, description: str) -> float:
        """Assess real-time processing requirements."""
        realtime_keywords = [
            "real time", "immediate", "instant", "live", "streaming",
            "real-time", "on-demand", "responsive", "fast"
        ]
        return self._calculate_keyword_score(description.lower(), realtime_keywords)
    
    def _determine_solution_type(self, factors: AgenticNecessityFactors) -> tuple[SolutionType, str]:
        """Determine recommended solution type based on factors."""
        
        agentic_score = factors.agentic_necessity_score
        traditional_score = factors.traditional_suitability_score
        
        score_difference = abs(agentic_score - traditional_score)
        
        # Clear preference for agentic
        if agentic_score >= self.agentic_necessity_threshold and agentic_score > traditional_score:
            if score_difference > self.hybrid_zone_threshold:
                return SolutionType.AGENTIC_AI, f"High agentic necessity (score: {agentic_score:.2f}) with complex reasoning, decision uncertainty, or adaptation requirements."
            else:
                return SolutionType.HYBRID, f"Moderate agentic necessity (score: {agentic_score:.2f}) suggests hybrid approach combining autonomous agents with traditional automation."
        
        # Clear preference for traditional
        elif traditional_score >= self.traditional_suitability_threshold and traditional_score > agentic_score:
            if score_difference > self.hybrid_zone_threshold:
                return SolutionType.TRADITIONAL_AUTOMATION, f"High traditional suitability (score: {traditional_score:.2f}) with predictable workflows and rule-based decisions."
            else:
                return SolutionType.HYBRID, f"Moderate traditional suitability (score: {traditional_score:.2f}) suggests hybrid approach with some autonomous capabilities."
        
        # Hybrid zone - scores are close or both low
        elif score_difference <= self.hybrid_zone_threshold:
            return SolutionType.HYBRID, f"Balanced scores (agentic: {agentic_score:.2f}, traditional: {traditional_score:.2f}) suggest hybrid approach."
        
        # Default to traditional if both scores are low
        else:
            return SolutionType.TRADITIONAL_AUTOMATION, f"Low complexity scores suggest traditional automation approach (agentic: {agentic_score:.2f}, traditional: {traditional_score:.2f})."
    
    def _generate_agentic_justification(self, factors: AgenticNecessityFactors, description: str) -> List[str]:
        """Generate justification for why agentic AI might be needed."""
        
        justifications = []
        
        if factors.reasoning_complexity_score > 0.3:
            justifications.append("Complex reasoning and decision-making requirements detected")
        
        if factors.decision_uncertainty_score > 0.3:
            justifications.append("Unpredictable scenarios requiring adaptive responses")
        
        if factors.exception_handling_complexity > 0.3:
            justifications.append("Complex exception handling requiring creative problem-solving")
        
        if factors.adaptation_requirements > 0.3:
            justifications.append("Learning and adaptation capabilities needed for improvement over time")
        
        if factors.domain_complexity > 0.3:
            justifications.append("Domain complexity requires specialized knowledge and reasoning")
        
        if not justifications:
            justifications.append("Standard automation capabilities may be sufficient")
        
        return justifications
    
    def _generate_traditional_justification(self, factors: AgenticNecessityFactors, description: str) -> List[str]:
        """Generate justification for why traditional automation might be suitable."""
        
        justifications = []
        
        if factors.workflow_predictability > 0.3:
            justifications.append("Predictable workflow with consistent process steps")
        
        if factors.rule_based_decisions > 0.3:
            justifications.append("Clear decision rules and criteria can be implemented")
        
        if factors.data_transformation_focus > 0.3:
            justifications.append("Primary focus on data processing and transformation")
        
        if factors.fixed_process_flow > 0.3:
            justifications.append("Well-defined process flow with established procedures")
        
        if factors.integration_complexity < 0.3:
            justifications.append("Straightforward system integration requirements")
        
        if not justifications:
            justifications.append("May require more sophisticated autonomous capabilities")
        
        return justifications
    
    def _calculate_confidence(self, factors: AgenticNecessityFactors) -> float:
        """Calculate confidence level based on score separation and factor strength."""
        
        score_difference = abs(factors.agentic_necessity_score - factors.traditional_suitability_score)
        max_score = max(factors.agentic_necessity_score, factors.traditional_suitability_score)
        
        # Higher confidence when scores are well-separated and at least one is high
        confidence = min(1.0, (score_difference * 2) + (max_score * 0.5))
        
        return confidence