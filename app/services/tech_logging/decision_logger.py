"""
Decision logging service for tracking technology selection decisions.

Provides detailed logging of decision-making processes including confidence scores,
reasoning, alternatives considered, and decision criteria.
"""

from typing import Dict, Any, List, Optional, Union
from dataclasses import dataclass, asdict
from datetime import datetime
import json

from .tech_stack_logger import TechStackLogger, LogCategory


@dataclass
class DecisionContext:
    """Context information for a decision."""
    decision_id: str
    decision_type: str  # e.g., "technology_selection", "conflict_resolution"
    component: str
    operation: str
    input_data: Dict[str, Any]
    constraints: Dict[str, Any]
    available_options: List[str]


@dataclass
class DecisionCriteria:
    """Criteria used for making a decision."""
    criterion_name: str
    weight: float
    description: str
    evaluation_method: str


@dataclass
class OptionEvaluation:
    """Evaluation of a single option."""
    option_name: str
    scores: Dict[str, float]  # criterion_name -> score
    total_score: float
    confidence: float
    reasoning: str
    pros: List[str]
    cons: List[str]


@dataclass
class DecisionResult:
    """Result of a decision-making process."""
    selected_option: str
    confidence_score: float
    reasoning: str
    alternatives_considered: List[str]
    decision_factors: Dict[str, Any]
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DecisionTrace:
    """Complete trace of a decision-making process."""
    context: DecisionContext
    criteria: List[DecisionCriteria]
    evaluations: List[OptionEvaluation]
    result: DecisionResult
    timestamp: str
    duration_ms: float


class DecisionLogger:
    """
    Service for logging technology selection and decision-making processes.
    
    Provides detailed tracking of how decisions are made, including confidence
    scores, reasoning, alternatives, and decision criteria.
    """
    
    def __init__(self, tech_stack_logger: TechStackLogger):
        """
        Initialize decision logger.
        
        Args:
            tech_stack_logger: Main tech stack logger instance
        """
        self.logger = tech_stack_logger
        self._active_decisions: Dict[str, Dict[str, Any]] = {}
    
    def start_decision(self, 
                      decision_id: str,
                      decision_type: str,
                      component: str,
                      operation: str,
                      input_data: Dict[str, Any],
                      constraints: Optional[Dict[str, Any]] = None,
                      available_options: Optional[List[str]] = None) -> DecisionContext:
        """
        Start tracking a decision-making process.
        
        Args:
            decision_id: Unique identifier for this decision
            decision_type: Type of decision being made
            component: Component making the decision
            operation: Operation context
            input_data: Input data for the decision
            constraints: Decision constraints
            available_options: Available options to choose from
            
        Returns:
            Decision context object
        """
        context = DecisionContext(
            decision_id=decision_id,
            decision_type=decision_type,
            component=component,
            operation=operation,
            input_data=input_data,
            constraints=constraints or {},
            available_options=available_options or []
        )
        
        self._active_decisions[decision_id] = {
            'context': context,
            'start_time': datetime.utcnow(),
            'criteria': [],
            'evaluations': [],
            'result': None
        }
        
        self.logger.log_info(
            LogCategory.DECISION_MAKING,
            component,
            operation,
            f"Started decision process: {decision_type}",
            {
                'decision_id': decision_id,
                'decision_type': decision_type,
                'input_data': input_data,
                'constraints': constraints,
                'available_options': available_options
            }
        )
        
        return context
    
    def add_decision_criteria(self,
                             decision_id: str,
                             criteria: List[DecisionCriteria]) -> None:
        """
        Add decision criteria for evaluation.
        
        Args:
            decision_id: Decision identifier
            criteria: List of decision criteria
        """
        if decision_id not in self._active_decisions:
            raise ValueError(f"No active decision found with ID: {decision_id}")
        
        self._active_decisions[decision_id]['criteria'].extend(criteria)
        
        self.logger.log_debug(
            LogCategory.DECISION_MAKING,
            "DecisionLogger",
            "add_criteria",
            f"Added {len(criteria)} decision criteria",
            {
                'decision_id': decision_id,
                'criteria': [asdict(c) for c in criteria]
            }
        )
    
    def log_option_evaluation(self,
                             decision_id: str,
                             evaluation: OptionEvaluation) -> None:
        """
        Log evaluation of a single option.
        
        Args:
            decision_id: Decision identifier
            evaluation: Option evaluation details
        """
        if decision_id not in self._active_decisions:
            raise ValueError(f"No active decision found with ID: {decision_id}")
        
        self._active_decisions[decision_id]['evaluations'].append(evaluation)
        
        self.logger.log_debug(
            LogCategory.DECISION_MAKING,
            "DecisionLogger",
            "evaluate_option",
            f"Evaluated option: {evaluation.option_name}",
            {
                'decision_id': decision_id,
                'option_name': evaluation.option_name,
                'total_score': evaluation.total_score,
                'confidence': evaluation.confidence,
                'reasoning': evaluation.reasoning,
                'scores': evaluation.scores
            },
            confidence_score=evaluation.confidence
        )
    
    def complete_decision(self,
                         decision_id: str,
                         result: DecisionResult) -> DecisionTrace:
        """
        Complete a decision-making process and log the final result.
        
        Args:
            decision_id: Decision identifier
            result: Final decision result
            
        Returns:
            Complete decision trace
        """
        if decision_id not in self._active_decisions:
            raise ValueError(f"No active decision found with ID: {decision_id}")
        
        decision_data = self._active_decisions.pop(decision_id)
        
        # Calculate duration
        start_time = decision_data['start_time']
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        # Create decision trace
        trace = DecisionTrace(
            context=decision_data['context'],
            criteria=decision_data['criteria'],
            evaluations=decision_data['evaluations'],
            result=result,
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=duration_ms
        )
        
        # Log decision completion
        self.logger.log_info(
            LogCategory.DECISION_MAKING,
            decision_data['context'].component,
            decision_data['context'].operation,
            f"Decision completed: {result.selected_option}",
            {
                'decision_id': decision_id,
                'selected_option': result.selected_option,
                'confidence_score': result.confidence_score,
                'reasoning': result.reasoning,
                'alternatives_considered': result.alternatives_considered,
                'decision_factors': result.decision_factors,
                'duration_ms': duration_ms,
                'evaluations_count': len(decision_data['evaluations'])
            },
            confidence_score=result.confidence_score,
            metadata={'decision_trace': asdict(trace)}
        )
        
        return trace
    
    def log_technology_selection(self,
                                component: str,
                                operation: str,
                                selected_technologies: List[str],
                                explicit_technologies: List[str],
                                contextual_technologies: List[str],
                                rejected_technologies: List[str],
                                selection_reasoning: Dict[str, str],
                                confidence_scores: Dict[str, float]) -> None:
        """
        Log technology selection decision with detailed context.
        
        Args:
            component: Component making the selection
            operation: Operation context
            selected_technologies: Technologies that were selected
            explicit_technologies: Explicitly mentioned technologies
            contextual_technologies: Contextually inferred technologies
            rejected_technologies: Technologies that were rejected
            selection_reasoning: Reasoning for each selection
            confidence_scores: Confidence scores for each selection
        """
        self.logger.log_info(
            LogCategory.DECISION_MAKING,
            component,
            operation,
            f"Technology selection completed: {len(selected_technologies)} selected",
            {
                'selected_technologies': selected_technologies,
                'explicit_technologies': explicit_technologies,
                'contextual_technologies': contextual_technologies,
                'rejected_technologies': rejected_technologies,
                'selection_reasoning': selection_reasoning,
                'confidence_scores': confidence_scores,
                'selection_stats': {
                    'total_selected': len(selected_technologies),
                    'explicit_selected': len([t for t in selected_technologies if t in explicit_technologies]),
                    'contextual_selected': len([t for t in selected_technologies if t in contextual_technologies]),
                    'total_rejected': len(rejected_technologies)
                }
            }
        )
    
    def log_conflict_resolution(self,
                               component: str,
                               operation: str,
                               conflict_type: str,
                               conflicting_technologies: List[str],
                               resolution_strategy: str,
                               resolved_selection: str,
                               resolution_reasoning: str,
                               confidence_score: float) -> None:
        """
        Log conflict resolution decision.
        
        Args:
            component: Component resolving the conflict
            operation: Operation context
            conflict_type: Type of conflict (e.g., "ecosystem_mismatch", "incompatible_versions")
            conflicting_technologies: Technologies in conflict
            resolution_strategy: Strategy used to resolve conflict
            resolved_selection: Final selection after resolution
            resolution_reasoning: Reasoning for the resolution
            confidence_score: Confidence in the resolution
        """
        self.logger.log_info(
            LogCategory.DECISION_MAKING,
            component,
            operation,
            f"Conflict resolved: {conflict_type}",
            {
                'conflict_type': conflict_type,
                'conflicting_technologies': conflicting_technologies,
                'resolution_strategy': resolution_strategy,
                'resolved_selection': resolved_selection,
                'resolution_reasoning': resolution_reasoning
            },
            confidence_score=confidence_score
        )
    
    def log_catalog_decision(self,
                            component: str,
                            operation: str,
                            technology_name: str,
                            decision_type: str,  # "auto_add", "manual_review", "reject"
                            reasoning: str,
                            metadata: Optional[Dict[str, Any]] = None,
                            confidence_score: Optional[float] = None) -> None:
        """
        Log catalog management decision.
        
        Args:
            component: Component making the decision
            operation: Operation context
            technology_name: Technology being considered
            decision_type: Type of decision made
            reasoning: Reasoning for the decision
            metadata: Additional metadata
            confidence_score: Confidence in the decision
        """
        self.logger.log_info(
            LogCategory.CATALOG_LOOKUP,
            component,
            operation,
            f"Catalog decision: {decision_type} for {technology_name}",
            {
                'technology_name': technology_name,
                'decision_type': decision_type,
                'reasoning': reasoning,
                'metadata': metadata or {}
            },
            confidence_score=confidence_score
        )
    
    def log_validation_decision(self,
                               component: str,
                               operation: str,
                               validation_type: str,
                               technologies: List[str],
                               validation_result: bool,
                               issues_found: List[str],
                               resolution_actions: List[str],
                               confidence_score: float) -> None:
        """
        Log validation decision and actions.
        
        Args:
            component: Component performing validation
            operation: Operation context
            validation_type: Type of validation performed
            technologies: Technologies being validated
            validation_result: Whether validation passed
            issues_found: List of issues found
            resolution_actions: Actions taken to resolve issues
            confidence_score: Confidence in the validation
        """
        self.logger.log_info(
            LogCategory.VALIDATION,
            component,
            operation,
            f"Validation {validation_type}: {'PASSED' if validation_result else 'FAILED'}",
            {
                'validation_type': validation_type,
                'technologies': technologies,
                'validation_result': validation_result,
                'issues_found': issues_found,
                'resolution_actions': resolution_actions,
                'issue_count': len(issues_found)
            },
            confidence_score=confidence_score
        )
    
    def get_decision_summary(self, 
                            component: Optional[str] = None,
                            decision_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Get summary of decisions made.
        
        Args:
            component: Filter by component
            decision_type: Filter by decision type
            
        Returns:
            Decision summary statistics
        """
        # Get decision-related log entries
        decision_entries = self.logger.get_log_entries(
            category=LogCategory.DECISION_MAKING,
            component=component
        )
        
        if decision_type:
            decision_entries = [
                e for e in decision_entries 
                if e.context.get('decision_type') == decision_type
            ]
        
        # Calculate summary statistics
        total_decisions = len(decision_entries)
        avg_confidence = 0.0
        decision_types = {}
        
        if decision_entries:
            confidences = [e.confidence_score for e in decision_entries if e.confidence_score is not None]
            if confidences:
                avg_confidence = sum(confidences) / len(confidences)
            
            # Count decision types
            for entry in decision_entries:
                dt = entry.context.get('decision_type', 'unknown')
                decision_types[dt] = decision_types.get(dt, 0) + 1
        
        return {
            'total_decisions': total_decisions,
            'average_confidence': avg_confidence,
            'decision_types': decision_types,
            'components': list(set(e.component for e in decision_entries))
        }