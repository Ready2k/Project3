"""
Automation Suitability Assessment Service

Handles the assessment of requirements for different types of automation:
1. Agentic AI (autonomous agents)
2. Traditional automation (RPA, workflows, etc.)
3. Not suitable for automation

When agentic assessment fails, this service provides fallback analysis.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

from app.llm.base import LLMProvider


class AutomationSuitability(Enum):
    """Types of automation suitability."""
    AGENTIC = "agentic"
    TRADITIONAL = "traditional"
    NOT_SUITABLE = "not_suitable"
    HYBRID = "hybrid"


@dataclass
class SuitabilityAssessment:
    """Result of automation suitability assessment."""
    suitability: AutomationSuitability
    confidence: float
    reasoning: str
    recommended_approach: str
    challenges: List[str]
    next_steps: List[str]
    user_choice_required: bool = False
    warning_message: Optional[str] = None


class AutomationSuitabilityAssessor:
    """Assesses requirements for different types of automation suitability."""
    
    def __init__(self, llm_provider: LLMProvider) -> None:
        """Initialize the assessor.
        
        Args:
            llm_provider: LLM provider for generating assessments
        """
        self.llm_provider = llm_provider
    
    async def assess_automation_suitability(self, 
                                          requirements: Dict[str, Any],
                                          agentic_rejected: bool = False) -> SuitabilityAssessment:
        """Assess what type of automation is suitable for the requirements.
        
        Args:
            requirements: The requirements to assess
            agentic_rejected: Whether agentic assessment already rejected this
            
        Returns:
            SuitabilityAssessment with recommendation and user choice info
        """
        description = requirements.get('description', '')
        constraints = requirements.get('constraints', {})
        
        self.logger.info(f"Assessing automation suitability for: {description[:100]}...")
        self.logger.info(f"Agentic already rejected: {agentic_rejected}")
        
        # Create assessment prompt
        prompt = self._create_assessment_prompt(description, constraints, agentic_rejected)
        
        try:
            # Get LLM assessment
            response = await self.llm_provider.generate(prompt, purpose="automation_suitability")
            
            # Parse response
            assessment = self._parse_assessment_response(response)
            
            self.logger.info(f"Automation suitability assessment: {assessment.suitability.value} (confidence: {assessment.confidence})")
            
            return assessment
            
        except Exception as e:
            self.logger.error(f"Error in automation suitability assessment: {e}")
            # Return conservative fallback assessment
            return SuitabilityAssessment(
                suitability=AutomationSuitability.NOT_SUITABLE,
                confidence=0.3,
                reasoning="Unable to assess automation suitability due to technical error",
                recommended_approach="Manual review recommended",
                challenges=["Technical assessment error"],
                next_steps=["Review requirements manually", "Consider consulting with automation experts"],
                user_choice_required=True,
                warning_message="Assessment failed - recommendations may not be accurate"
            )
    
    def _create_assessment_prompt(self, 
                                description: str, 
                                constraints: Dict[str, Any],
                                agentic_rejected: bool) -> str:
        """Create the LLM prompt for automation suitability assessment."""
        
        agentic_context = ""
        if agentic_rejected:
            agentic_context = """
IMPORTANT CONTEXT: This requirement has already been assessed and REJECTED for Agentic AI automation.
The agentic assessment determined this involves physical-world aspects or lacks sufficient digital control surfaces.
"""
        
        return f"""You are an expert automation consultant specializing in both Agentic AI and Traditional Automation approaches.

{agentic_context}

REQUIREMENT TO ASSESS:
{description}

CONSTRAINTS:
- Banned Technologies: {constraints.get('banned_tools', [])}
- Required Integrations: {constraints.get('required_integrations', [])}
- Compliance Requirements: {constraints.get('compliance_requirements', [])}
- Data Sensitivity: {constraints.get('data_sensitivity', 'Not specified')}

ASSESSMENT TASK:
Determine the most suitable automation approach for this requirement. Consider these options:

1. AGENTIC: Autonomous AI agents that reason, plan, and act (LangChain, AutoGen, etc.)
   - Requires: Complex decision-making, reasoning, adaptability
   - Best for: Dynamic environments, unstructured data, complex workflows

2. TRADITIONAL: Classic automation (RPA, workflows, scripts, APIs)
   - Requires: Structured processes, clear rules, predictable inputs
   - Best for: Repetitive tasks, form filling, data transfer, scheduled jobs

3. HYBRID: Combination of both approaches
   - Agentic for complex decisions, traditional for execution
   - Best for: Complex workflows with both structured and unstructured elements

4. NOT_SUITABLE: Cannot be effectively automated
   - Requires: Human judgment, physical presence, creative work
   - Examples: Physical tasks, highly creative work, complex human interaction

ANALYSIS CRITERIA:
- Physical vs Digital: Does this involve physical world interaction?
- Decision Complexity: Simple rules vs complex reasoning required?
- Data Structure: Structured vs unstructured data?
- Process Variability: Predictable vs highly variable workflows?
- Human Interaction: Level of human judgment required?

OUTPUT FORMAT (JSON only, no other text):
{{
  "suitability": "agentic|traditional|hybrid|not_suitable",
  "confidence": 0.85,
  "reasoning": "Detailed explanation of why this assessment was made",
  "recommended_approach": "Specific recommendation for implementation",
  "challenges": ["challenge1", "challenge2", "challenge3"],
  "next_steps": ["step1", "step2", "step3"],
  "user_choice_required": true,
  "warning_message": "Optional warning if proceeding may not be suitable"
}}

IMPORTANT:
- Set user_choice_required=true if suitability is "not_suitable" or confidence < 0.7
- Include warning_message if there are significant concerns about automation feasibility
- Be honest about limitations - don't oversell automation capabilities
- Consider the specific constraints provided
"""
    
    def _parse_assessment_response(self, response: str) -> SuitabilityAssessment:
        """Parse the LLM response into a SuitabilityAssessment."""
        try:
            from app.utils.json_parser import parse_llm_json_response
            
            data = parse_llm_json_response(response, default_value={}, service_name="automation_suitability")
            
            if not isinstance(data, dict):
                raise ValueError(f"Expected dict, got {type(data)}")
            
            # Map string to enum
            suitability_str = data.get('suitability', 'not_suitable')
            suitability_mapping = {
                'agentic': AutomationSuitability.AGENTIC,
                'traditional': AutomationSuitability.TRADITIONAL,
                'hybrid': AutomationSuitability.HYBRID,
                'not_suitable': AutomationSuitability.NOT_SUITABLE
            }
            
            suitability = suitability_mapping.get(suitability_str, AutomationSuitability.NOT_SUITABLE)
            
            return SuitabilityAssessment(
                suitability=suitability,
                confidence=float(data.get('confidence', 0.5)),
                reasoning=data.get('reasoning', 'No reasoning provided'),
                recommended_approach=data.get('recommended_approach', 'Manual review recommended'),
                challenges=data.get('challenges', []),
                next_steps=data.get('next_steps', []),
                user_choice_required=bool(data.get('user_choice_required', True)),
                warning_message=data.get('warning_message')
            )
            
        except Exception as e:
            self.logger.error(f"Error parsing automation suitability response: {e}")
            self.logger.error(f"Response was: {response}")
            
            # Return conservative fallback
            return SuitabilityAssessment(
                suitability=AutomationSuitability.NOT_SUITABLE,
                confidence=0.3,
                reasoning="Failed to parse automation assessment",
                recommended_approach="Manual review recommended",
                challenges=["Assessment parsing error"],
                next_steps=["Review requirements manually"],
                user_choice_required=True,
                warning_message="Assessment parsing failed - recommendations may not be accurate"
            )
    
    def should_proceed_with_traditional_patterns(self, assessment: SuitabilityAssessment) -> bool:
        """Determine if we should proceed with traditional pattern matching.
        
        Args:
            assessment: The suitability assessment result
            
        Returns:
            True if we should proceed with traditional patterns
        """
        return assessment.suitability in [
            AutomationSuitability.TRADITIONAL,
            AutomationSuitability.HYBRID
        ] and assessment.confidence >= 0.6
    
    def should_require_user_choice(self, assessment: SuitabilityAssessment) -> bool:
        """Determine if user choice is required before proceeding.
        
        Args:
            assessment: The suitability assessment result
            
        Returns:
            True if user should be asked before proceeding
        """
        return (
            assessment.user_choice_required or
            assessment.suitability == AutomationSuitability.NOT_SUITABLE or
            assessment.confidence < 0.7 or
            assessment.warning_message is not None
        )