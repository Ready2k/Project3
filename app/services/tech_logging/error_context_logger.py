"""
Error context logging service for comprehensive error tracking and recovery.

Provides detailed error logging with context, suggested fixes, recovery actions,
and error pattern analysis for improved debugging and system reliability.
"""

from typing import Dict, Any, List, Optional, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import traceback
from enum import Enum

from .tech_stack_logger import TechStackLogger, LogCategory


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error category classification."""
    PARSING_ERROR = "parsing_error"
    VALIDATION_ERROR = "validation_error"
    LLM_ERROR = "llm_error"
    CATALOG_ERROR = "catalog_error"
    CONFIGURATION_ERROR = "configuration_error"
    NETWORK_ERROR = "network_error"
    DATA_ERROR = "data_error"
    LOGIC_ERROR = "logic_error"
    SYSTEM_ERROR = "system_error"
    USER_ERROR = "user_error"


@dataclass
class ErrorContext:
    """Comprehensive error context information."""
    error_id: str
    error_type: str
    error_message: str
    component: str
    operation: str
    severity: ErrorSeverity
    category: ErrorCategory
    timestamp: str
    stack_trace: Optional[str]
    input_data: Optional[Dict[str, Any]]
    system_state: Optional[Dict[str, Any]]
    user_context: Optional[Dict[str, Any]]


@dataclass
class RecoveryAction:
    """Recovery action suggestion."""
    action_type: str  # "retry", "fallback", "user_input", "configuration_fix"
    description: str
    parameters: Dict[str, Any]
    success_probability: float
    estimated_time: Optional[str]


@dataclass
class ErrorPattern:
    """Error pattern for analysis."""
    pattern_id: str
    error_signature: str
    occurrence_count: int
    first_seen: str
    last_seen: str
    components_affected: List[str]
    common_causes: List[str]
    recommended_fixes: List[str]


class ErrorContextLogger:
    """
    Service for comprehensive error logging with context and recovery suggestions.
    
    Provides detailed error tracking, pattern analysis, and recovery guidance
    to improve system reliability and debugging efficiency.
    """
    
    def __init__(self, tech_stack_logger: TechStackLogger):
        """
        Initialize error context logger.
        
        Args:
            tech_stack_logger: Main tech stack logger instance
        """
        self.logger = tech_stack_logger
        self._error_patterns: Dict[str, ErrorPattern] = {}
        self._recovery_strategies: Dict[str, List[RecoveryAction]] = {}
        self._error_handlers: Dict[str, Callable] = {}
    
    def log_error_with_context(self,
                              component: str,
                              operation: str,
                              error: Exception,
                              severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                              category: ErrorCategory = ErrorCategory.SYSTEM_ERROR,
                              input_data: Optional[Dict[str, Any]] = None,
                              system_state: Optional[Dict[str, Any]] = None,
                              user_context: Optional[Dict[str, Any]] = None,
                              suggested_fixes: Optional[List[str]] = None,
                              recovery_actions: Optional[List[RecoveryAction]] = None) -> str:
        """
        Log error with comprehensive context information.
        
        Args:
            component: Component where error occurred
            operation: Operation being performed
            error: Exception that occurred
            severity: Error severity level
            category: Error category
            input_data: Input data that caused the error
            system_state: System state at time of error
            user_context: User context information
            suggested_fixes: Suggested fixes for the error
            recovery_actions: Possible recovery actions
            
        Returns:
            Error ID for tracking
        """
        # Generate error ID
        error_id = f"{component}_{operation}_{int(datetime.utcnow().timestamp())}"
        
        # Create error context
        error_context = ErrorContext(
            error_id=error_id,
            error_type=type(error).__name__,
            error_message=str(error),
            component=component,
            operation=operation,
            severity=severity,
            category=category,
            timestamp=datetime.utcnow().isoformat(),
            stack_trace=traceback.format_exc(),
            input_data=input_data,
            system_state=system_state,
            user_context=user_context
        )
        
        # Update error patterns
        self._update_error_patterns(error_context)
        
        # Log the error
        self.logger.log_error(
            LogCategory.ERROR_HANDLING,
            component,
            operation,
            f"Error occurred: {error_context.error_message}",
            {
                'error_id': error_id,
                'error_type': error_context.error_type,
                'severity': severity.value,
                'category': category.value,
                'input_data': input_data,
                'system_state': system_state,
                'user_context': user_context,
                'suggested_fixes': suggested_fixes,
                'recovery_actions': [asdict(ra) for ra in recovery_actions] if recovery_actions else None,
                'stack_trace': error_context.stack_trace
            },
            exception=error
        )
        
        # Store recovery actions if provided
        if recovery_actions:
            self._recovery_strategies[error_id] = recovery_actions
        
        return error_id
    
    def log_parsing_error(self,
                         component: str,
                         operation: str,
                         input_text: str,
                         parsing_stage: str,
                         error: Exception,
                         expected_format: Optional[str] = None,
                         partial_results: Optional[Dict[str, Any]] = None) -> str:
        """
        Log parsing-specific error with context.
        
        Args:
            component: Component performing parsing
            operation: Parsing operation
            input_text: Text being parsed
            parsing_stage: Stage where parsing failed
            error: Parsing exception
            expected_format: Expected input format
            partial_results: Any partial parsing results
            
        Returns:
            Error ID
        """
        suggested_fixes = [
            "Check input format and structure",
            "Validate input against expected schema",
            "Try alternative parsing methods"
        ]
        
        if expected_format:
            suggested_fixes.append(f"Ensure input matches expected format: {expected_format}")
        
        recovery_actions = [
            RecoveryAction(
                action_type="retry",
                description="Retry parsing with cleaned input",
                parameters={"clean_input": True, "remove_special_chars": True},
                success_probability=0.6,
                estimated_time="1-2 seconds"
            ),
            RecoveryAction(
                action_type="fallback",
                description="Use alternative parsing method",
                parameters={"method": "regex_based", "strict_mode": False},
                success_probability=0.4,
                estimated_time="2-3 seconds"
            )
        ]
        
        return self.log_error_with_context(
            component=component,
            operation=operation,
            error=error,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.PARSING_ERROR,
            input_data={
                'input_text': input_text[:500] + "..." if len(input_text) > 500 else input_text,
                'parsing_stage': parsing_stage,
                'expected_format': expected_format,
                'partial_results': partial_results
            },
            suggested_fixes=suggested_fixes,
            recovery_actions=recovery_actions
        )
    
    def log_llm_error(self,
                     component: str,
                     operation: str,
                     provider: str,
                     model: str,
                     prompt: str,
                     error: Exception,
                     retry_count: int = 0,
                     response_so_far: Optional[str] = None) -> str:
        """
        Log LLM-specific error with context.
        
        Args:
            component: Component making LLM call
            operation: LLM operation
            provider: LLM provider
            model: Model being used
            prompt: Prompt that caused error
            error: LLM exception
            retry_count: Number of retries attempted
            response_so_far: Partial response if available
            
        Returns:
            Error ID
        """
        suggested_fixes = [
            "Check LLM provider configuration and API keys",
            "Verify model availability and parameters",
            "Reduce prompt length if hitting token limits",
            "Check network connectivity"
        ]
        
        recovery_actions = []
        
        # Suggest retry if not already attempted multiple times
        if retry_count < 3:
            recovery_actions.append(RecoveryAction(
                action_type="retry",
                description="Retry LLM call with exponential backoff",
                parameters={"delay_seconds": 2 ** retry_count, "max_retries": 3},
                success_probability=0.7 - (retry_count * 0.2),
                estimated_time=f"{2 ** retry_count}-{2 ** (retry_count + 1)} seconds"
            ))
        
        # Suggest fallback provider
        recovery_actions.append(RecoveryAction(
            action_type="fallback",
            description="Try alternative LLM provider",
            parameters={"fallback_provider": "openai" if provider != "openai" else "anthropic"},
            success_probability=0.6,
            estimated_time="5-10 seconds"
        ))
        
        # Suggest prompt simplification
        if len(prompt) > 2000:
            recovery_actions.append(RecoveryAction(
                action_type="configuration_fix",
                description="Simplify prompt to reduce token usage",
                parameters={"max_prompt_length": 2000, "preserve_key_context": True},
                success_probability=0.5,
                estimated_time="1-2 seconds"
            ))
        
        return self.log_error_with_context(
            component=component,
            operation=operation,
            error=error,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.LLM_ERROR,
            input_data={
                'provider': provider,
                'model': model,
                'prompt_length': len(prompt),
                'prompt_preview': prompt[:200] + "..." if len(prompt) > 200 else prompt,
                'retry_count': retry_count,
                'response_so_far': response_so_far
            },
            suggested_fixes=suggested_fixes,
            recovery_actions=recovery_actions
        )
    
    def log_validation_error(self,
                            component: str,
                            operation: str,
                            validation_type: str,
                            invalid_data: Any,
                            validation_rules: List[str],
                            error: Exception,
                            field_errors: Optional[Dict[str, str]] = None) -> str:
        """
        Log validation error with detailed context.
        
        Args:
            component: Component performing validation
            operation: Validation operation
            validation_type: Type of validation
            invalid_data: Data that failed validation
            validation_rules: Validation rules that were applied
            error: Validation exception
            field_errors: Field-specific error messages
            
        Returns:
            Error ID
        """
        suggested_fixes = [
            "Check data format and structure",
            "Validate against schema requirements",
            "Review validation rules for correctness"
        ]
        
        if field_errors:
            for field, field_error in field_errors.items():
                suggested_fixes.append(f"Fix {field}: {field_error}")
        
        recovery_actions = [
            RecoveryAction(
                action_type="user_input",
                description="Request corrected input from user",
                parameters={"validation_errors": field_errors or {}, "retry_allowed": True},
                success_probability=0.8,
                estimated_time="User dependent"
            ),
            RecoveryAction(
                action_type="fallback",
                description="Use default values for invalid fields",
                parameters={"use_defaults": True, "strict_validation": False},
                success_probability=0.5,
                estimated_time="1 second"
            )
        ]
        
        return self.log_error_with_context(
            component=component,
            operation=operation,
            error=error,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.VALIDATION_ERROR,
            input_data={
                'validation_type': validation_type,
                'invalid_data': str(invalid_data)[:500],
                'validation_rules': validation_rules,
                'field_errors': field_errors
            },
            suggested_fixes=suggested_fixes,
            recovery_actions=recovery_actions
        )
    
    def log_catalog_error(self,
                         component: str,
                         operation: str,
                         technology_name: str,
                         catalog_operation: str,
                         error: Exception,
                         catalog_state: Optional[Dict[str, Any]] = None) -> str:
        """
        Log catalog-related error.
        
        Args:
            component: Component accessing catalog
            operation: Catalog operation
            technology_name: Technology being processed
            catalog_operation: Specific catalog operation
            error: Catalog exception
            catalog_state: Current catalog state
            
        Returns:
            Error ID
        """
        suggested_fixes = [
            "Check catalog file integrity and permissions",
            "Verify technology name format and spelling",
            "Validate catalog schema and structure"
        ]
        
        recovery_actions = [
            RecoveryAction(
                action_type="retry",
                description="Retry catalog operation",
                parameters={"reload_catalog": True, "validate_first": True},
                success_probability=0.6,
                estimated_time="2-3 seconds"
            ),
            RecoveryAction(
                action_type="fallback",
                description="Use cached catalog data",
                parameters={"use_cache": True, "cache_timeout": 300},
                success_probability=0.4,
                estimated_time="1 second"
            )
        ]
        
        return self.log_error_with_context(
            component=component,
            operation=operation,
            error=error,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.CATALOG_ERROR,
            input_data={
                'technology_name': technology_name,
                'catalog_operation': catalog_operation,
                'catalog_state': catalog_state
            },
            suggested_fixes=suggested_fixes,
            recovery_actions=recovery_actions
        )
    
    def get_recovery_actions(self, error_id: str) -> Optional[List[RecoveryAction]]:
        """
        Get recovery actions for a specific error.
        
        Args:
            error_id: Error identifier
            
        Returns:
            List of recovery actions or None if not found
        """
        return self._recovery_strategies.get(error_id)
    
    def execute_recovery_action(self,
                               error_id: str,
                               action_index: int,
                               component: str,
                               operation: str) -> bool:
        """
        Execute a recovery action and log the result.
        
        Args:
            error_id: Error identifier
            action_index: Index of recovery action to execute
            component: Component executing recovery
            operation: Recovery operation
            
        Returns:
            True if recovery was successful, False otherwise
        """
        recovery_actions = self.get_recovery_actions(error_id)
        if not recovery_actions or action_index >= len(recovery_actions):
            self.logger.log_warning(
                LogCategory.ERROR_HANDLING,
                component,
                operation,
                f"No recovery action found for error {error_id} at index {action_index}",
                {'error_id': error_id, 'action_index': action_index}
            )
            return False
        
        action = recovery_actions[action_index]
        
        try:
            self.logger.log_info(
                LogCategory.ERROR_HANDLING,
                component,
                operation,
                f"Executing recovery action: {action.description}",
                {
                    'error_id': error_id,
                    'action_type': action.action_type,
                    'action_description': action.description,
                    'parameters': action.parameters
                }
            )
            
            # Here you would implement the actual recovery logic
            # For now, we'll just log the attempt
            success = True  # Placeholder - implement actual recovery logic
            
            if success:
                self.logger.log_info(
                    LogCategory.ERROR_HANDLING,
                    component,
                    operation,
                    "Recovery action completed successfully",
                    {'error_id': error_id, 'action_type': action.action_type}
                )
            else:
                self.logger.log_warning(
                    LogCategory.ERROR_HANDLING,
                    component,
                    operation,
                    "Recovery action failed",
                    {'error_id': error_id, 'action_type': action.action_type}
                )
            
            return success
            
        except Exception as recovery_error:
            self.logger.log_error(
                LogCategory.ERROR_HANDLING,
                component,
                operation,
                f"Recovery action execution failed: {recovery_error}",
                {
                    'error_id': error_id,
                    'action_type': action.action_type,
                    'recovery_error': str(recovery_error)
                },
                exception=recovery_error
            )
            return False
    
    def _update_error_patterns(self, error_context: ErrorContext) -> None:
        """Update error pattern tracking."""
        # Create error signature for pattern matching
        signature = f"{error_context.error_type}:{error_context.component}:{error_context.category.value}"
        
        if signature in self._error_patterns:
            pattern = self._error_patterns[signature]
            pattern.occurrence_count += 1
            pattern.last_seen = error_context.timestamp
            if error_context.component not in pattern.components_affected:
                pattern.components_affected.append(error_context.component)
        else:
            self._error_patterns[signature] = ErrorPattern(
                pattern_id=signature,
                error_signature=signature,
                occurrence_count=1,
                first_seen=error_context.timestamp,
                last_seen=error_context.timestamp,
                components_affected=[error_context.component],
                common_causes=[],
                recommended_fixes=[]
            )
    
    def get_error_patterns(self, 
                          min_occurrences: int = 2,
                          time_window_hours: Optional[int] = None) -> List[ErrorPattern]:
        """
        Get error patterns for analysis.
        
        Args:
            min_occurrences: Minimum occurrences to be considered a pattern
            time_window_hours: Time window to consider
            
        Returns:
            List of error patterns
        """
        patterns = []
        
        for pattern in self._error_patterns.values():
            if pattern.occurrence_count >= min_occurrences:
                # Apply time window filter if specified
                if time_window_hours:
                    cutoff_time = datetime.utcnow().timestamp() - (time_window_hours * 3600)
                    last_seen_time = datetime.fromisoformat(pattern.last_seen).timestamp()
                    if last_seen_time < cutoff_time:
                        continue
                
                patterns.append(pattern)
        
        # Sort by occurrence count (most frequent first)
        patterns.sort(key=lambda p: p.occurrence_count, reverse=True)
        return patterns
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive error summary.
        
        Returns:
            Error summary statistics
        """
        # Get error entries from main logger
        error_entries = self.logger.get_log_entries(category=LogCategory.ERROR_HANDLING)
        
        if not error_entries:
            return {}
        
        # Calculate statistics
        total_errors = len(error_entries)
        
        # Group by severity
        severity_counts = {}
        category_counts = {}
        component_counts = {}
        
        for entry in error_entries:
            severity = entry.context.get('severity', 'unknown')
            category = entry.context.get('category', 'unknown')
            component = entry.component
            
            severity_counts[severity] = severity_counts.get(severity, 0) + 1
            category_counts[category] = category_counts.get(category, 0) + 1
            component_counts[component] = component_counts.get(component, 0) + 1
        
        # Get top error patterns
        top_patterns = self.get_error_patterns(min_occurrences=1)[:5]
        
        return {
            'total_errors': total_errors,
            'severity_distribution': severity_counts,
            'category_distribution': category_counts,
            'component_distribution': component_counts,
            'top_error_patterns': [asdict(p) for p in top_patterns],
            'recovery_actions_available': len(self._recovery_strategies)
        }