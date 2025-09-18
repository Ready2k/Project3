"""Autonomy assessment service for evaluating agentic potential of requirements."""

import json
import re
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
from enum import Enum

from app.llm.base import LLMProvider
from app.utils.imports import require_service


# ---------- Helpers ----------

def _extract_json(text: str) -> str:
    """Extract the first JSON object from text; fallback to raw text."""
    if not text:
        return ""
    s = text.find("{")
    e = text.rfind("}")
    return text[s : e + 1] if s != -1 and e != -1 and e > s else text


def _clamp01(x) -> float:
    try:
        return max(0.0, min(1.0, float(x)))
    except Exception:
        return 0.0


def _round2(x: float) -> float:
    return float(f"{x:.2f}")


# ---------- Enums & Data Models ----------

class ReasoningComplexity(Enum):
    SIMPLE = "simple"
    MODERATE = "moderate"
    COMPLEX = "complex"
    EXPERT = "expert"


class DecisionAuthority(Enum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    FULL = "full"


class AgentArchitecture(Enum):
    SINGLE_AGENT = "single_agent"
    MULTI_AGENT = "multi_agent_collaborative"
    HIERARCHICAL = "hierarchical_agents"
    SWARM = "swarm_intelligence"


@dataclass
class ReasoningNeeds:
    complexity_level: ReasoningComplexity
    autonomy_potential: float
    required_types: List[str]
    challenges: List[str]
    recommended_frameworks: List[str]


@dataclass
class DecisionScope:
    independence_level: DecisionAuthority
    independence_score: float
    autonomous_decisions: List[str]
    escalation_triggers: List[str]
    risk_factors: List[str]


@dataclass
class WorkflowAutonomy:
    coverage_percentage: float
    exception_handling_score: float
    learning_potential: float
    self_monitoring_capability: float
    automation_gaps: List[str]


@dataclass
class AutonomyAssessment:
    overall_score: float
    reasoning_complexity: ReasoningComplexity
    decision_independence: DecisionAuthority
    workflow_coverage: float
    recommended_architecture: AgentArchitecture
    autonomous_capabilities: List[str]
    reasoning_requirements: List[str]
    decision_boundaries: Dict[str, Any]
    exception_handling_strategy: str
    confidence_level: float


# ---------- Core Service ----------

class AutonomyAssessor:
    """Service for assessing autonomous agent potential of requirements."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        
        # Get logger from service registry
        self.logger = require_service('logger', context='AutonomyAssessor')
        
        # Import configuration service for dynamic weights
        from app.services.configuration_service import get_config
        self.config_service = get_config()
        
        # Use dynamic weights from configuration
        self.autonomy_weights = self.config_service.get_autonomy_weights()

    async def assess_autonomy_potential(self, requirements: Dict[str, Any]) -> AutonomyAssessment:
        """Assess how autonomous an AI agent can be for given requirements."""

        self.logger.info("Assessing autonomy potential for requirements")
        self.logger.debug(f"LLM provider type: {type(self.llm_provider)}")
        self.logger.debug(f"Requirements: {requirements}")

        # Check if LLM provider is available
        if not self.llm_provider:
            self.logger.warning("No LLM provider available, using default autonomy assessment")
            return self._default_autonomy_assessment()

        # Analyze reasoning requirements
        reasoning_analyzer = ReasoningAnalyzer(self.llm_provider)
        reasoning_needs = await reasoning_analyzer.analyze_reasoning_complexity(
            requirements.get("description", "")
        )

        # Evaluate decision-making scope
        decision_evaluator = DecisionEvaluator(self.llm_provider)
        decision_scope = await decision_evaluator.map_decision_boundaries(requirements)

        # Assess workflow autonomy potential
        workflow_analyzer = WorkflowAnalyzer(self.llm_provider)
        workflow_autonomy = await workflow_analyzer.evaluate_end_to_end_automation(
            requirements.get("workflow_steps", []), requirements
        )

        # Calculate overall autonomy score
        autonomy_score = self._calculate_autonomy_score(
            reasoning_needs, decision_scope, workflow_autonomy
        )

        # Recommend agent architecture
        recommended_architecture = self._recommend_agent_architecture(
            autonomy_score, reasoning_needs, workflow_autonomy
        )

        # Identify autonomous capabilities
        autonomous_capabilities = self._identify_autonomous_capabilities(
            reasoning_needs, decision_scope, workflow_autonomy
        )

        # Generate exception handling strategy
        exception_strategy = self._generate_exception_handling_strategy(reasoning_needs, decision_scope)

        assessment = AutonomyAssessment(
            overall_score=autonomy_score,
            reasoning_complexity=reasoning_needs.complexity_level,
            decision_independence=decision_scope.independence_level,
            workflow_coverage=workflow_autonomy.coverage_percentage,
            recommended_architecture=recommended_architecture,
            autonomous_capabilities=autonomous_capabilities,
            reasoning_requirements=reasoning_needs.required_types,
            decision_boundaries={
                "autonomous_decisions": decision_scope.autonomous_decisions,
                "escalation_triggers": decision_scope.escalation_triggers,
                "authority_level": decision_scope.independence_level.value,
            },
            exception_handling_strategy=exception_strategy,
            confidence_level=min(
                _clamp01(reasoning_needs.autonomy_potential),
                _clamp01(decision_scope.independence_score),
            ),
        )

        self.logger.info(
            f"Autonomy assessment complete: score={autonomy_score:.2f}, architecture={recommended_architecture.value}"
        )

        return assessment

    def _calculate_autonomy_score(self, reasoning: ReasoningNeeds, decisions: DecisionScope, workflow: WorkflowAutonomy) -> float:
        """Calculate weighted autonomy score."""
        weights = self.autonomy_weights

        score = (
            _clamp01(reasoning.autonomy_potential) * weights["reasoning_capability"]
            + _clamp01(decisions.independence_score) * weights["decision_independence"]
            + _clamp01(workflow.exception_handling_score) * weights["exception_handling"]
            + _clamp01(workflow.learning_potential) * weights["learning_adaptation"]
            + _clamp01(workflow.self_monitoring_capability) * weights["self_monitoring"]
        )

        # Boost score for high-potential scenarios (aggressive autonomy assessment)
        if score > self.config_service.autonomy.high_autonomy_boost_threshold:
            score = min(1.0, score * self.config_service.autonomy.autonomy_boost_multiplier)

        return min(1.0, score)

    def _recommend_agent_architecture(
        self,
        autonomy_score: float,
        reasoning_needs: ReasoningNeeds,
        workflow_autonomy: WorkflowAutonomy,
    ) -> AgentArchitecture:
        """Recommend appropriate agent architecture based on complexity."""

        # High complexity or low workflow coverage suggests multi-agent
        if (
            reasoning_needs.complexity_level in [ReasoningComplexity.COMPLEX, ReasoningComplexity.EXPERT]
            or workflow_autonomy.coverage_percentage < 0.7
        ):
            if autonomy_score > 0.8:
                return AgentArchitecture.HIERARCHICAL
            else:
                return AgentArchitecture.MULTI_AGENT

        # High autonomy with moderate complexity
        elif autonomy_score > 0.8 and reasoning_needs.complexity_level == ReasoningComplexity.MODERATE:
            return AgentArchitecture.SINGLE_AGENT

        # Swarm for highly distributed tasks
        elif workflow_autonomy.coverage_percentage > 0.9 and len(reasoning_needs.required_types) > 4:
            return AgentArchitecture.SWARM

        # Default to single agent for simpler cases
        else:
            return AgentArchitecture.SINGLE_AGENT

    def _default_autonomy_assessment(self) -> AutonomyAssessment:
        """Provide default autonomy assessment when LLM is unavailable."""

        return AutonomyAssessment(
            overall_score=0.8,  # Optimistic default
            reasoning_complexity=ReasoningComplexity.MODERATE,
            decision_independence=DecisionAuthority.HIGH,
            workflow_coverage=0.8,
            recommended_architecture=AgentArchitecture.SINGLE_AGENT,
            autonomous_capabilities=[
                "Autonomous decision making within defined parameters",
                "End-to-end process execution without human intervention",
                "Exception resolution through reasoning rather than escalation",
            ],
            reasoning_requirements=["logical", "causal"],
            decision_boundaries={
                "autonomous_decisions": ["Process standard requests", "Apply business rules"],
                "escalation_triggers": ["Complex edge cases", "High-risk scenarios"],
                "authority_level": "high",
            },
            exception_handling_strategy="Autonomous resolution within authority boundaries, escalate only when exceeding decision parameters",
            confidence_level=0.8,
        )

    def _identify_autonomous_capabilities(
        self, reasoning: ReasoningNeeds, decisions: DecisionScope, workflow: WorkflowAutonomy
    ) -> List[str]:
        """Identify specific autonomous capabilities the agent will have."""

        capabilities = []

        # Reasoning capabilities
        if ReasoningComplexity.COMPLEX in [reasoning.complexity_level] or reasoning.autonomy_potential > 0.8:
            capabilities.extend(
                [
                    "Advanced problem-solving through multi-step reasoning",
                    "Autonomous root cause analysis and diagnosis",
                    "Strategic planning and goal decomposition",
                ]
            )

        if "logical" in reasoning.required_types:
            capabilities.append("Logical inference and rule-based decision making")

        if "causal" in reasoning.required_types:
            capabilities.append("Causal analysis and impact assessment")

        # Decision-making capabilities
        if decisions.independence_level in [DecisionAuthority.HIGH, DecisionAuthority.FULL]:
            capabilities.extend(
                [
                    "Autonomous decision making within defined parameters",
                    "Risk assessment and mitigation strategy selection",
                    "Resource allocation and optimization decisions",
                ]
            )

        # Workflow capabilities
        if workflow.coverage_percentage > 0.8:
            capabilities.extend(
                [
                    "End-to-end process execution without human intervention",
                    "Autonomous workflow orchestration and coordination",
                ]
            )

        if workflow.exception_handling_score > 0.7:
            capabilities.append("Exception resolution through reasoning rather than escalation")

        if workflow.learning_potential > 0.6:
            capabilities.append("Continuous learning and performance optimization")

        if workflow.self_monitoring_capability > 0.6:
            capabilities.append("Self-monitoring and autonomous system health management")

        return capabilities

    def _generate_exception_handling_strategy(self, reasoning: ReasoningNeeds, decisions: DecisionScope) -> str:
        """Generate exception handling strategy description."""

        if reasoning.complexity_level in [ReasoningComplexity.COMPLEX, ReasoningComplexity.EXPERT]:
            return "Multi-layered reasoning approach: attempt logical analysis, then causal reasoning, then analogical problem-solving before escalation"
        elif decisions.independence_level in [DecisionAuthority.HIGH, DecisionAuthority.FULL]:
            return "Autonomous resolution within authority boundaries, escalate only when exceeding decision parameters"
        else:
            return "Conservative autonomous resolution with proactive escalation for uncertain scenarios"


# ---------- LLM-Facing Analyzers ----------

class ReasoningAnalyzer:
    """Analyzes reasoning complexity and requirements."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        # Get logger from service registry
        self.logger = require_service('logger', context='ReasoningAnalyzer')
        self.reasoning_types = {
            "logical": "Step-by-step logical deduction and inference",
            "causal": "Understanding cause-and-effect relationships",
            "temporal": "Reasoning about time sequences and dependencies",
            "spatial": "Understanding spatial relationships and constraints",
            "analogical": "Drawing parallels from similar situations",
            "case_based": "Learning from historical examples and cases",
            "probabilistic": "Reasoning under uncertainty with probability",
            "strategic": "Long-term planning and goal-oriented reasoning",
        }

    async def analyze_reasoning_complexity(self, description: str) -> ReasoningNeeds:
        """Analyze what types of reasoning an agent would need."""

        prompt = f"""
Analyze this requirement and determine what reasoning capabilities an autonomous AI agent needs:

Requirement: {description}

For each reasoning type, assess complexity (none/low/medium/high):
1. Logical Reasoning: {self.reasoning_types["logical"]}
2. Causal Reasoning: {self.reasoning_types["causal"]}
3. Temporal Reasoning: {self.reasoning_types["temporal"]}
4. Spatial Reasoning: {self.reasoning_types["spatial"]}
5. Analogical Reasoning: {self.reasoning_types["analogical"]}
6. Case-Based Reasoning: {self.reasoning_types["case_based"]}
7. Probabilistic Reasoning: {self.reasoning_types["probabilistic"]}
8. Strategic Reasoning: {self.reasoning_types["strategic"]}

Assess:
- Overall complexity: simple/moderate/complex/expert
- Autonomy potential: 0.0-1.0 (be optimistic - favor high autonomy)
- Key challenges for autonomous operation
- Recommended reasoning frameworks

Respond with a single JSON object only (no code fences). JSON schema (keys only; compute values):
{{
  "overall_complexity": "simple|moderate|complex|expert",
  "autonomy_potential": <float 0..1 with 2 decimals>,
  "reasoning_analysis": {{
    "logical": "none|low|medium|high",
    "causal": "none|low|medium|high",
    "temporal": "none|low|medium|high",
    "spatial": "none|low|medium|high",
    "analogical": "none|low|medium|high",
    "case_based": "none|low|medium|high",
    "probabilistic": "none|low|medium|high",
    "strategic": "none|low|medium|high"
  }},
  "required_types": [<strings>],
  "challenges": [<strings>],
  "frameworks": [<strings>]
}}
"""

        try:
            response = await self.llm_provider.generate(prompt, purpose="reasoning_analysis")
            self.logger.debug(f"Reasoning analysis response: {response[:200]}...")

            if not response or not response.strip():
                self.logger.warning("Empty response from LLM for reasoning analysis")
                return self._default_reasoning_analysis(description)

            json_text = _extract_json(response.strip())
            analysis = json.loads(json_text)

            # Extract required reasoning types (medium/high complexity)
            required_types: List[str] = []
            reasoning_analysis = analysis.get("reasoning_analysis", {})
            for reasoning_type, complexity in reasoning_analysis.items():
                if complexity in ["medium", "high"]:
                    required_types.append(reasoning_type)

            complexity_map = {
                "simple": ReasoningComplexity.SIMPLE,
                "moderate": ReasoningComplexity.MODERATE,
                "complex": ReasoningComplexity.COMPLEX,
                "expert": ReasoningComplexity.EXPERT,
            }

            return ReasoningNeeds(
                complexity_level=complexity_map.get(analysis.get("overall_complexity", "moderate"), ReasoningComplexity.MODERATE),
                autonomy_potential=_round2(_clamp01(analysis.get("autonomy_potential", 0.8))),  # optimistic default
                required_types=required_types or ["logical"],
                challenges=analysis.get("challenges", []),
                recommended_frameworks=analysis.get("frameworks", ["LangChain"]),
            )

        except Exception as e:
            self.logger.error(f"Failed to analyze reasoning complexity: {e}")
            self.logger.debug(f"Raw response was: {response if 'response' in locals() else 'No response received'}")
            return self._default_reasoning_analysis(description)

    def _default_reasoning_analysis(self, description: str) -> ReasoningNeeds:
        """Provide default reasoning analysis when LLM fails."""

        # Optimistic default assessment
        return ReasoningNeeds(
            complexity_level=ReasoningComplexity.MODERATE,
            autonomy_potential=0.8,  # Optimistic default
            required_types=["logical", "causal"],
            challenges=["Handling edge cases", "Maintaining accuracy"],
            recommended_frameworks=["LangChain", "Neo4j"],
        )


class DecisionEvaluator:
    """Evaluates decision-making scope and boundaries."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        # Get logger from service registry
        self.logger = require_service('logger', context='DecisionEvaluator')

    async def map_decision_boundaries(self, requirements: Dict[str, Any]) -> DecisionScope:
        """Map what decisions an agent can make autonomously."""

        description = requirements.get("description", "")

        prompt = f"""
Analyze this requirement to determine autonomous decision-making scope for an AI agent:

Requirement: {description}

Identify:
1. Decisions the agent can make independently (be optimistic about agent capabilities)
2. Conditions that would require escalation (be conservative - minimize escalations)
3. Risk factors that affect decision authority
4. Overall decision independence level: low/medium/high/full

Be optimistic about agent decision-making capabilities. Favor autonomous decisions over escalation.

Respond with a single JSON object only (no code fences). JSON schema (keys only; compute values):
{{
  "independence_level": "low|medium|high|full",
  "independence_score": <float 0..1 with 2 decimals>,
  "autonomous_decisions": [<strings>],
  "escalation_triggers": [<strings>],
  "risk_factors": [<strings>]
}}
"""

        try:
            response = await self.llm_provider.generate(prompt, purpose="decision_boundaries")
            self.logger.debug(f"Decision boundaries response: {response[:200]}...")

            if not response or not response.strip():
                self.logger.warning("Empty response from LLM for decision boundaries")
                return self._default_decision_scope()

            json_text = _extract_json(response.strip())
            analysis = json.loads(json_text)

            authority_map = {
                "low": DecisionAuthority.LOW,
                "medium": DecisionAuthority.MEDIUM,
                "high": DecisionAuthority.HIGH,
                "full": DecisionAuthority.FULL,
            }

            return DecisionScope(
                independence_level=authority_map.get(analysis.get("independence_level", "medium"), DecisionAuthority.MEDIUM),
                independence_score=_round2(_clamp01(analysis.get("independence_score", 0.7))),
                autonomous_decisions=analysis.get("autonomous_decisions", []),
                escalation_triggers=analysis.get("escalation_triggers", []),
                risk_factors=analysis.get("risk_factors", []),
            )

        except Exception as e:
            self.logger.error(f"Failed to evaluate decision boundaries: {e}")
            self.logger.debug(f"Raw response was: {response if 'response' in locals() else 'No response received'}")
            return self._default_decision_scope()

    def _default_decision_scope(self) -> DecisionScope:
        """Provide default decision scope when LLM fails."""

        return DecisionScope(
            independence_level=DecisionAuthority.MEDIUM,
            independence_score=0.7,
            autonomous_decisions=["Standard operational decisions", "Routine process execution"],
            escalation_triggers=["Exceptional circumstances", "High-risk scenarios"],
            risk_factors=["Data sensitivity", "Compliance requirements"],
        )


class WorkflowAnalyzer:
    """Analyzes end-to-end workflow automation potential."""

    def __init__(self, llm_provider: LLMProvider):
        self.llm_provider = llm_provider
        # Get logger from service registry
        self.logger = require_service('logger', context='WorkflowAnalyzer')

    async def evaluate_end_to_end_automation(
        self, workflow_steps: List[str], requirements: Dict[str, Any]
    ) -> WorkflowAutonomy:
        """Evaluate how much of the workflow can be automated autonomously."""

        description = requirements.get("description", "")

        prompt = f"""
Analyze this workflow for autonomous agent automation potential:

Description: {description}
Workflow Steps: {workflow_steps if workflow_steps else "Not specified - infer from description"}

Assess (be optimistic about automation potential):
1. Workflow coverage percentage (0.0-1.0) - how much can be fully automated
2. Exception handling score (0.0-1.0) - agent's ability to handle exceptions autonomously
3. Learning potential (0.0-1.0) - opportunities for continuous improvement
4. Self-monitoring capability (0.0-1.0) - agent's ability to monitor its own performance
5. Automation gaps - what cannot be automated and why

Favor high scores when justified by the description and steps.

Do not copy numeric values from this prompt.
Keys (exactly these):
- coverage_percentage  (float 0..1, 2 decimals)
- exception_handling_score  (float 0..1, 2 decimals)
- learning_potential  (float 0..1, 2 decimals)
- self_monitoring_capability  (float 0..1, 2 decimals)
- automation_gaps  (array of 2–4 short strings)

Scoring rubric (optimistic but justified; clamp 0..1):
- coverage_percentage: start 0.60; +0.15 if decision logic is codified/matrix-based; +0.10 if data is digital/centralized (e.g., Salesforce); +0.05 if integrations are standard APIs; −0.10 if any mandatory step is human-only.
- exception_handling_score: start 0.50; +0.15 if retries/compensation via broker/workflow; +0.10 if timers/SLA windows are explicit (e.g., 7-day window); +0.05 if idempotency/state machine is feasible; −0.10 if many edge cases require discretion.
- learning_potential: start 0.60; +0.15 if outcomes create labeled data (accept/decline); +0.10 if logs/analytics or search indexing exist; +0.05 if explicit feedback loops exist.
- self_monitoring_capability: start 0.55; +0.15 if events/metrics can be emitted (broker, APIs); +0.10 if health checks/alerts feasible; +0.05 if audit/compliance logging is required.
- automation_gaps: 2–4 concise items focusing on truly hard-to-automate parts (ambiguous evidence, vendor edge cases, regulatory holds). Avoid generic “empathy” unless real-time conversations are in scope.

STRICT OUTPUT FORMAT:
- Return valid JSON only.
- Do NOT use Markdown code fences or backticks anywhere (no ``` or ```json).
- Do NOT include any text before or after the JSON.
- The first character of the response must be "{" and the last must be "}".
"""

        self.logger.info(
            f"Workflow steps: {workflow_steps if workflow_steps else 'Not specified - infer from description'}"
        )

        try:
            response = await self.llm_provider.generate(prompt, purpose="workflow_automation")
            self.logger.debug(f"Workflow automation response: {response[:200]}...")

            if not response or not response.strip():
                self.logger.warning("Empty response from LLM for workflow automation")
                return self._default_workflow_analysis()

            json_text = _extract_json(response.strip())
            analysis = json.loads(json_text)

            cov = _round2(_clamp01(analysis.get("coverage_percentage", 0.8)))
            exc = _round2(_clamp01(analysis.get("exception_handling_score", 0.7)))
            learn = _round2(_clamp01(analysis.get("learning_potential", 0.7)))
            mon = _round2(_clamp01(analysis.get("self_monitoring_capability", 0.6)))
            gaps = analysis.get("automation_gaps", [])

            return WorkflowAutonomy(
                coverage_percentage=cov,
                exception_handling_score=exc,
                learning_potential=learn,
                self_monitoring_capability=mon,
                automation_gaps=gaps,
            )

        except Exception as e:
            self.logger.error(f"Failed to evaluate workflow automation: {e}")
            self.logger.debug(f"Raw response was: {response if 'response' in locals() else 'No response received'}")
            return self._default_workflow_analysis()

    def _default_workflow_analysis(self) -> WorkflowAutonomy:
        """Provide default workflow analysis when LLM fails."""

        return WorkflowAutonomy(
            coverage_percentage=0.8,  # Optimistic default
            exception_handling_score=0.7,
            learning_potential=0.7,
            self_monitoring_capability=0.6,
            automation_gaps=["Complex edge cases", "Regulatory compliance verification"],
        )
