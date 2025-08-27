"""Agentic Necessity Assessor - Uses LLM to determine if requirements need agentic AI or traditional automation."""

import json
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
    """LLM-powered service for assessing whether requirements need agentic AI or traditional automation."""
    
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
        """Use LLM to assess whether the requirement needs agentic AI or traditional automation."""
        
        app_logger.info("Assessing agentic necessity using LLM analysis")
        
        description = requirements.get("description", "")
        domain = requirements.get("domain", "")
        
        # Use LLM to analyze the requirement
        llm_analysis = await self._llm_analyze_requirement(description, domain)
        
        # Calculate necessity factors from LLM analysis
        factors = self._extract_factors_from_llm_analysis(llm_analysis)
        
        # Determine recommended solution type
        solution_type, reasoning = self._determine_solution_type(factors)
        
        # Extract justifications from LLM analysis
        agentic_justification = llm_analysis.get("agentic_justification", [])
        traditional_justification = llm_analysis.get("traditional_justification", [])
        
        # Calculate confidence from LLM analysis
        confidence = llm_analysis.get("confidence_level", 0.8)
        
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
        
        app_logger.info(f"LLM agentic necessity assessment: {solution_type.value} (confidence: {confidence:.2f})")
        
        return assessment
    
    async def _llm_analyze_requirement(self, description: str, domain: str) -> Dict[str, Any]:
        """Use LLM to analyze the requirement and determine agentic necessity."""
        
        prompt = f"""Analyze the following requirement to determine whether it needs agentic AI (autonomous agents) or traditional automation.

**Requirement Description:**
{description}

**Domain:** {domain}

Please analyze this requirement across multiple dimensions and provide scores from 0.0 to 1.0 for each factor:

**AGENTIC FACTORS (favor autonomous AI agents):**
1. **Reasoning Complexity** (0.0-1.0): Does this require complex reasoning, analysis, correlation, or intelligent decision-making?
2. **Decision Uncertainty** (0.0-1.0): Are there unpredictable scenarios, exceptions, or situations requiring adaptive responses?
3. **Exception Handling** (0.0-1.0): Does this need creative problem-solving, error recovery, or handling of unexpected situations?
4. **Adaptation Requirements** (0.0-1.0): Would learning, improvement over time, or adaptation to changing conditions be beneficial?
5. **Domain Complexity** (0.0-1.0): Is this a complex domain requiring specialized knowledge or sophisticated reasoning?

**TRADITIONAL FACTORS (favor rule-based automation):**
1. **Workflow Predictability** (0.0-1.0): Are the process steps predictable, routine, and consistent?
2. **Rule-Based Decisions** (0.0-1.0): Can decisions be made using clear rules, criteria, or conditions?
3. **Data Transformation Focus** (0.0-1.0): Is this primarily about data processing, conversion, or transformation?
4. **Fixed Process Flow** (0.0-1.0): Is there a well-defined, unchanging sequence of steps?

**CONTEXT FACTORS:**
1. **Integration Complexity** (0.0-1.0): How complex are the system integrations required?
2. **Real-Time Requirements** (0.0-1.0): Are there real-time or immediate response requirements?

Provide your analysis in the following JSON format:

{{
    "agentic_factors": {{
        "reasoning_complexity": 0.0,
        "decision_uncertainty": 0.0,
        "exception_handling": 0.0,
        "adaptation_requirements": 0.0,
        "domain_complexity": 0.0
    }},
    "traditional_factors": {{
        "workflow_predictability": 0.0,
        "rule_based_decisions": 0.0,
        "data_transformation_focus": 0.0,
        "fixed_process_flow": 0.0
    }},
    "context_factors": {{
        "integration_complexity": 0.0,
        "real_time_requirements": 0.0
    }},
    "agentic_necessity_score": 0.0,
    "traditional_suitability_score": 0.0,
    "confidence_level": 0.0,
    "agentic_justification": [
        "Reason 1 why agentic AI might be needed",
        "Reason 2 why agentic AI might be needed"
    ],
    "traditional_justification": [
        "Reason 1 why traditional automation might work",
        "Reason 2 why traditional automation might work"
    ],
    "key_indicators": [
        "Key phrase or concept that influenced the analysis",
        "Another important indicator"
    ]
}}

Focus on the actual capabilities needed rather than specific keywords. Consider:
- Does this require autonomous decision-making?
- Are there complex, unpredictable scenarios?
- Would an intelligent agent add significant value?
- Is this primarily rule-based processing?

Be objective and consider both perspectives."""

        try:
            response = await self.llm_provider.generate(prompt, purpose="agentic_necessity_assessment")
            
            # Extract JSON from response
            json_start = response.find('{')
            json_end = response.rfind('}') + 1
            
            if json_start >= 0 and json_end > json_start:
                json_str = response[json_start:json_end]
                analysis = json.loads(json_str)
                
                app_logger.info(f"LLM analysis completed: agentic={analysis.get('agentic_necessity_score', 0):.2f}, traditional={analysis.get('traditional_suitability_score', 0):.2f}")
                return analysis
            else:
                app_logger.warning("Could not extract JSON from LLM response, using fallback analysis")
                return self._fallback_analysis(description, domain)
                
        except Exception as e:
            app_logger.error(f"LLM analysis failed: {e}, using fallback analysis")
            return self._fallback_analysis(description, domain)
    
    def _fallback_analysis(self, description: str, domain: str) -> Dict[str, Any]:
        """Fallback analysis when LLM fails - simple heuristic-based approach."""
        
        desc_lower = description.lower()
        
        # Simple heuristics for fallback
        agentic_indicators = [
            "autonomous", "agent", "intelligent", "analyze", "correlate", "triage",
            "decision", "reasoning", "adaptive", "learn", "optimize", "predict"
        ]
        
        traditional_indicators = [
            "process", "transform", "convert", "migrate", "sync", "copy",
            "validate", "check", "routine", "standard", "fixed"
        ]
        
        agentic_score = sum(1 for indicator in agentic_indicators if indicator in desc_lower) / len(agentic_indicators)
        traditional_score = sum(1 for indicator in traditional_indicators if indicator in desc_lower) / len(traditional_indicators)
        
        return {
            "agentic_factors": {
                "reasoning_complexity": min(1.0, agentic_score * 1.2),
                "decision_uncertainty": min(1.0, agentic_score * 1.1),
                "exception_handling": min(1.0, agentic_score * 1.0),
                "adaptation_requirements": min(1.0, agentic_score * 0.8),
                "domain_complexity": 0.5
            },
            "traditional_factors": {
                "workflow_predictability": min(1.0, traditional_score * 1.2),
                "rule_based_decisions": min(1.0, traditional_score * 1.1),
                "data_transformation_focus": min(1.0, traditional_score * 1.0),
                "fixed_process_flow": min(1.0, traditional_score * 0.9)
            },
            "context_factors": {
                "integration_complexity": 0.5,
                "real_time_requirements": 0.5
            },
            "agentic_necessity_score": agentic_score,
            "traditional_suitability_score": traditional_score,
            "confidence_level": 0.6,
            "agentic_justification": ["Fallback analysis detected potential agentic requirements"],
            "traditional_justification": ["Fallback analysis detected potential traditional automation suitability"],
            "key_indicators": ["Fallback heuristic analysis"]
        }
    
    def _extract_factors_from_llm_analysis(self, llm_analysis: Dict[str, Any]) -> AgenticNecessityFactors:
        """Extract necessity factors from LLM analysis."""
        
        agentic_factors = llm_analysis.get("agentic_factors", {})
        traditional_factors = llm_analysis.get("traditional_factors", {})
        context_factors = llm_analysis.get("context_factors", {})
        
        return AgenticNecessityFactors(
            reasoning_complexity_score=agentic_factors.get("reasoning_complexity", 0.0),
            decision_uncertainty_score=agentic_factors.get("decision_uncertainty", 0.0),
            exception_handling_complexity=agentic_factors.get("exception_handling", 0.0),
            adaptation_requirements=agentic_factors.get("adaptation_requirements", 0.0),
            workflow_predictability=traditional_factors.get("workflow_predictability", 0.0),
            rule_based_decisions=traditional_factors.get("rule_based_decisions", 0.0),
            data_transformation_focus=traditional_factors.get("data_transformation_focus", 0.0),
            fixed_process_flow=traditional_factors.get("fixed_process_flow", 0.0),
            domain_complexity=agentic_factors.get("domain_complexity", 0.0),
            integration_complexity=context_factors.get("integration_complexity", 0.0),
            real_time_requirements=context_factors.get("real_time_requirements", 0.0),
            agentic_necessity_score=llm_analysis.get("agentic_necessity_score", 0.0),
            traditional_suitability_score=llm_analysis.get("traditional_suitability_score", 0.0)
        )
    
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
    

    
    def _calculate_confidence(self, factors: AgenticNecessityFactors) -> float:
        """Calculate confidence level based on score separation and factor strength."""
        
        score_difference = abs(factors.agentic_necessity_score - factors.traditional_suitability_score)
        max_score = max(factors.agentic_necessity_score, factors.traditional_suitability_score)
        
        # Higher confidence when scores are well-separated and at least one is high
        confidence = min(1.0, (score_difference * 2) + (max_score * 0.5))
        
        return confidence