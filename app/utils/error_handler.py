"""
Centralized error handling for the AAA system.

This module provides standardized error handling, logging, and user-friendly
error messages throughout the application.
"""

import traceback
import sys
from typing import Any, Dict, List, Optional, Type, Union, Callable
from dataclasses import dataclass
from enum import Enum
from datetime import datetime
import logging

from app.utils.result import Result


class ErrorSeverity(Enum):
    """Error severity levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(Enum):
    """Error categories for classification."""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    CONFIGURATION = "configuration"
    EXTERNAL_SERVICE = "external_service"
    DATABASE = "database"
    NETWORK = "network"
    FILE_SYSTEM = "file_system"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


@dataclass
class ErrorContext:
    """Additional context information for errors."""
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    additional_data: Optional[Dict[str, Any]] = None


@dataclass
class ErrorInfo:
    """Comprehensive error information."""
    error_id: str
    message: str
    user_message: str
    category: ErrorCategory
    severity: ErrorSeverity
    timestamp: datetime
    exception: Optional[Exception] = None
    stack_trace: Optional[str] = None
    context: Optional[ErrorContext] = None
    recovery_suggestions: List[str] = None
    
    def __post_init__(self):
        if self.recovery_suggestions is None:
            self.recovery_suggestions = []


class AAException(Exception):
    """
    Base exception class for AAA system.
    
    Provides structured error information and user-friendly messages.
    """
    
    def __init__(self, message: str, user_message: str = None, 
                 category: ErrorCategory = ErrorCategory.UNKNOWN,
                 severity: ErrorSeverity = ErrorSeverity.MEDIUM,
                 context: ErrorContext = None,
                 recovery_suggestions: List[str] = None):
        """
        Initialize the exception.
        
        Args:
            message: Technical error message
            user_message: User-friendly error message
            category: Error category
            severity: Error severity
            context: Additional context
            recovery_suggestions: List of recovery suggestions
        """
        super().__init__(message)
        self.message = message
        self.user_message = user_message or self._generate_user_message()
        self.category = category
        self.severity = severity
        self.context = context or ErrorContext()
        self.recovery_suggestions = recovery_suggestions or []
    
    def _generate_user_message(self) -> str:
        """Generate a user-friendly message based on the category."""
        category_messages = {
            ErrorCategory.VALIDATION: "Please check your input and try again.",
            ErrorCategory.AUTHENTICATION: "Please check your credentials and try again.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.CONFIGURATION: "There's a configuration issue. Please contact support.",
            ErrorCategory.EXTERNAL_SERVICE: "An external service is temporarily unavailable. Please try again later.",
            ErrorCategory.DATABASE: "There's a database issue. Please try again later.",
            ErrorCategory.NETWORK: "There's a network connectivity issue. Please check your connection.",
            ErrorCategory.FILE_SYSTEM: "There's a file system issue. Please try again later.",
            ErrorCategory.BUSINESS_LOGIC: "Unable to complete the operation. Please try again.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again later.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again later."
        }
        return category_messages.get(self.category, "An error occurred. Please try again.")


class ValidationException(AAException):
    """Exception for validation errors."""
    
    def __init__(self, message: str, field: str = None, value: Any = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.VALIDATION,
            severity=ErrorSeverity.LOW,
            **kwargs
        )
        self.field = field
        self.value = value


class ConfigurationException(AAException):
    """Exception for configuration errors."""
    
    def __init__(self, message: str, config_key: str = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.CONFIGURATION,
            severity=ErrorSeverity.HIGH,
            **kwargs
        )
        self.config_key = config_key


class ExternalServiceException(AAException):
    """Exception for external service errors."""
    
    def __init__(self, message: str, service_name: str = None, status_code: int = None, **kwargs):
        super().__init__(
            message=message,
            category=ErrorCategory.EXTERNAL_SERVICE,
            severity=ErrorSeverity.MEDIUM,
            **kwargs
        )
        self.service_name = service_name
        self.status_code = status_code


class ErrorHandler:
    """
    Centralized error handler for the AAA system.
    
    Provides error logging, user message generation, and recovery mechanisms.
    """
    
    def __init__(self, logger: logging.Logger = None):
        """
        Initialize the error handler.
        
        Args:
            logger: Logger instance to use for error logging
        """
        self.logger = logger or logging.getLogger(__name__)
        self._error_count = 0
        self._error_history: List[ErrorInfo] = []
        self._max_history = 1000
    
    def handle_exception(self, exception: Exception, context: ErrorContext = None) -> ErrorInfo:
        """
        Handle an exception and create error information.
        
        Args:
            exception: The exception to handle
            context: Additional context information
            
        Returns:
            ErrorInfo object with comprehensive error details
        """
        self._error_count += 1
        error_id = f"ERR_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{self._error_count:04d}"
        
        # Determine error details based on exception type
        if isinstance(exception, AAException):
            category = exception.category
            severity = exception.severity
            user_message = exception.user_message
            recovery_suggestions = exception.recovery_suggestions
            context = context or exception.context
        else:
            category = self._categorize_exception(exception)
            severity = self._determine_severity(exception)
            user_message = self._generate_user_message(exception, category)
            recovery_suggestions = self._generate_recovery_suggestions(exception, category)
        
        # Create error info
        error_info = ErrorInfo(
            error_id=error_id,
            message=str(exception),
            user_message=user_message,
            category=category,
            severity=severity,
            timestamp=datetime.now(),
            exception=exception,
            stack_trace=traceback.format_exc(),
            context=context,
            recovery_suggestions=recovery_suggestions
        )
        
        # Log the error
        self._log_error(error_info)
        
        # Store in history
        self._add_to_history(error_info)
        
        return error_info
    
    def handle_result_error(self, result: Result, context: ErrorContext = None) -> ErrorInfo:
        """
        Handle a Result error and create error information.
        
        Args:
            result: Result object containing an error
            context: Additional context information
            
        Returns:
            ErrorInfo object with comprehensive error details
        """
        if result.is_success:
            raise ValueError("Cannot handle error from successful result")
        
        error = result.error
        if isinstance(error, Exception):
            return self.handle_exception(error, context)
        else:
            # Create a generic exception from the error value
            exception = Exception(str(error))
            return self.handle_exception(exception, context)
    
    def _categorize_exception(self, exception: Exception) -> ErrorCategory:
        """Categorize an exception based on its type and message."""
        exception_type = type(exception).__name__.lower()
        message = str(exception).lower()
        
        # Type-based categorization
        if 'validation' in exception_type or 'value' in exception_type:
            return ErrorCategory.VALIDATION
        elif 'permission' in exception_type or 'auth' in exception_type:
            return ErrorCategory.AUTHORIZATION
        elif 'connection' in exception_type or 'timeout' in exception_type:
            return ErrorCategory.NETWORK
        elif 'file' in exception_type or 'io' in exception_type:
            return ErrorCategory.FILE_SYSTEM
        elif 'database' in exception_type or 'sql' in exception_type:
            return ErrorCategory.DATABASE
        
        # Message-based categorization
        if any(keyword in message for keyword in ['invalid', 'validation', 'format']):
            return ErrorCategory.VALIDATION
        elif any(keyword in message for keyword in ['permission', 'unauthorized', 'forbidden']):
            return ErrorCategory.AUTHORIZATION
        elif any(keyword in message for keyword in ['connection', 'network', 'timeout']):
            return ErrorCategory.NETWORK
        elif any(keyword in message for keyword in ['file', 'directory', 'path']):
            return ErrorCategory.FILE_SYSTEM
        elif any(keyword in message for keyword in ['database', 'sql', 'query']):
            return ErrorCategory.DATABASE
        elif any(keyword in message for keyword in ['config', 'setting']):
            return ErrorCategory.CONFIGURATION
        
        return ErrorCategory.UNKNOWN
    
    def _determine_severity(self, exception: Exception) -> ErrorSeverity:
        """Determine the severity of an exception."""
        exception_type = type(exception).__name__.lower()
        message = str(exception).lower()
        
        # Critical errors
        if any(keyword in exception_type for keyword in ['system', 'memory', 'security']):
            return ErrorSeverity.CRITICAL
        
        # High severity errors
        if any(keyword in exception_type for keyword in ['database', 'connection', 'auth']):
            return ErrorSeverity.HIGH
        
        # Low severity errors
        if any(keyword in exception_type for keyword in ['validation', 'value']):
            return ErrorSeverity.LOW
        
        # Message-based severity
        if any(keyword in message for keyword in ['critical', 'fatal', 'security']):
            return ErrorSeverity.CRITICAL
        elif any(keyword in message for keyword in ['invalid', 'validation']):
            return ErrorSeverity.LOW
        
        return ErrorSeverity.MEDIUM
    
    def _generate_user_message(self, exception: Exception, category: ErrorCategory) -> str:
        """Generate a user-friendly error message."""
        category_messages = {
            ErrorCategory.VALIDATION: "Please check your input and try again.",
            ErrorCategory.AUTHENTICATION: "Please check your credentials and try again.",
            ErrorCategory.AUTHORIZATION: "You don't have permission to perform this action.",
            ErrorCategory.CONFIGURATION: "There's a configuration issue. Please contact support.",
            ErrorCategory.EXTERNAL_SERVICE: "An external service is temporarily unavailable. Please try again later.",
            ErrorCategory.DATABASE: "There's a database issue. Please try again later.",
            ErrorCategory.NETWORK: "There's a network connectivity issue. Please check your connection.",
            ErrorCategory.FILE_SYSTEM: "There's a file system issue. Please try again later.",
            ErrorCategory.BUSINESS_LOGIC: "Unable to complete the operation. Please try again.",
            ErrorCategory.SYSTEM: "A system error occurred. Please try again later.",
            ErrorCategory.UNKNOWN: "An unexpected error occurred. Please try again later."
        }
        return category_messages.get(category, "An error occurred. Please try again.")
    
    def _generate_recovery_suggestions(self, exception: Exception, category: ErrorCategory) -> List[str]:
        """Generate recovery suggestions based on the error."""
        suggestions = []
        
        if category == ErrorCategory.VALIDATION:
            suggestions.extend([
                "Check that all required fields are filled",
                "Verify that input formats are correct",
                "Ensure values are within acceptable ranges"
            ])
        elif category == ErrorCategory.NETWORK:
            suggestions.extend([
                "Check your internet connection",
                "Try again in a few moments",
                "Contact support if the problem persists"
            ])
        elif category == ErrorCategory.EXTERNAL_SERVICE:
            suggestions.extend([
                "Wait a few minutes and try again",
                "Check service status pages",
                "Contact support if the issue continues"
            ])
        elif category == ErrorCategory.CONFIGURATION:
            suggestions.extend([
                "Contact your system administrator",
                "Check configuration documentation",
                "Verify environment settings"
            ])
        else:
            suggestions.extend([
                "Try the operation again",
                "Refresh the page and retry",
                "Contact support if the problem continues"
            ])
        
        return suggestions
    
    def _log_error(self, error_info: ErrorInfo) -> None:
        """Log error information."""
        log_level = {
            ErrorSeverity.LOW: logging.WARNING,
            ErrorSeverity.MEDIUM: logging.ERROR,
            ErrorSeverity.HIGH: logging.ERROR,
            ErrorSeverity.CRITICAL: logging.CRITICAL
        }.get(error_info.severity, logging.ERROR)
        
        log_message = (
            f"Error {error_info.error_id}: {error_info.message} "
            f"[Category: {error_info.category.value}, Severity: {error_info.severity.value}]"
        )
        
        if error_info.context:
            context_info = []
            if error_info.context.user_id:
                context_info.append(f"User: {error_info.context.user_id}")
            if error_info.context.session_id:
                context_info.append(f"Session: {error_info.context.session_id}")
            if error_info.context.component:
                context_info.append(f"Component: {error_info.context.component}")
            if error_info.context.operation:
                context_info.append(f"Operation: {error_info.context.operation}")
            
            if context_info:
                log_message += f" [Context: {', '.join(context_info)}]"
        
        # Use appropriate logger method based on log level
        if log_level == "DEBUG":
            self.logger.debug(log_message)
        elif log_level == "INFO":
            self.logger.info(log_message)
        elif log_level == "WARNING":
            self.logger.warning(log_message)
        elif log_level == "ERROR":
            self.logger.error(log_message)
        else:
            self.logger.error(log_message)  # Default to error for unknown levels
        
        # Log stack trace for high severity errors
        if error_info.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL] and error_info.stack_trace:
            self.logger.log(log_level, f"Stack trace for {error_info.error_id}:\n{error_info.stack_trace}")
    
    def _add_to_history(self, error_info: ErrorInfo) -> None:
        """Add error to history, maintaining size limit."""
        self._error_history.append(error_info)
        
        # Trim history if it exceeds maximum size
        if len(self._error_history) > self._max_history:
            self._error_history = self._error_history[-self._max_history:]
    
    def get_error_history(self, limit: int = 100) -> List[ErrorInfo]:
        """
        Get recent error history.
        
        Args:
            limit: Maximum number of errors to return
            
        Returns:
            List of recent ErrorInfo objects
        """
        return self._error_history[-limit:]
    
    def get_error_stats(self) -> Dict[str, Any]:
        """
        Get error statistics.
        
        Returns:
            Dictionary with error statistics
        """
        if not self._error_history:
            return {
                "total_errors": 0,
                "by_category": {},
                "by_severity": {},
                "recent_errors": 0
            }
        
        # Count by category
        by_category = {}
        for error in self._error_history:
            category = error.category.value
            by_category[category] = by_category.get(category, 0) + 1
        
        # Count by severity
        by_severity = {}
        for error in self._error_history:
            severity = error.severity.value
            by_severity[severity] = by_severity.get(severity, 0) + 1
        
        # Count recent errors (last hour)
        recent_cutoff = datetime.now().timestamp() - 3600
        recent_errors = sum(1 for error in self._error_history 
                          if error.timestamp.timestamp() > recent_cutoff)
        
        return {
            "total_errors": len(self._error_history),
            "by_category": by_category,
            "by_severity": by_severity,
            "recent_errors": recent_errors
        }


# Global error handler instance
_global_error_handler: Optional[ErrorHandler] = None


def get_error_handler() -> ErrorHandler:
    """
    Get the global error handler instance.
    
    Returns:
        The global error handler
    """
    global _global_error_handler
    
    if _global_error_handler is None:
        _global_error_handler = ErrorHandler()
    
    return _global_error_handler


def handle_exception(exception: Exception, context: ErrorContext = None) -> ErrorInfo:
    """
    Handle an exception using the global error handler.
    
    Args:
        exception: The exception to handle
        context: Additional context information
        
    Returns:
        ErrorInfo object with comprehensive error details
    """
    handler = get_error_handler()
    return handler.handle_exception(exception, context)


def safe_execute(func: Callable, context: ErrorContext = None, 
                default_return: Any = None) -> Result[Any, ErrorInfo]:
    """
    Safely execute a function and handle any exceptions.
    
    Args:
        func: Function to execute
        context: Error context information
        default_return: Default value to return on error
        
    Returns:
        Result containing the function result or error information
    """
    try:
        result = func()
        return Result.success(result)
    except Exception as e:
        error_info = handle_exception(e, context)
        return Result.error(error_info)