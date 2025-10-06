"""
Main tech stack logging service with structured logging capabilities.

Provides centralized logging for all tech stack generation activities with
structured data, context tracking, and configurable output formats.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from pathlib import Path
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.service import ConfigurableService


class LogLevel(Enum):
    """Log level enumeration."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class LogCategory(Enum):
    """Log category enumeration for tech stack operations."""
    REQUIREMENT_PARSING = "requirement_parsing"
    TECHNOLOGY_EXTRACTION = "technology_extraction"
    CONTEXT_ANALYSIS = "context_analysis"
    CATALOG_LOOKUP = "catalog_lookup"
    LLM_INTERACTION = "llm_interaction"
    VALIDATION = "validation"
    DECISION_MAKING = "decision_making"
    PERFORMANCE = "performance"
    ERROR_HANDLING = "error_handling"
    DEBUG_TRACE = "debug_trace"


@dataclass
class LogEntry:
    """Structured log entry for tech stack operations."""
    timestamp: str
    level: str
    category: str
    component: str
    operation: str
    message: str
    context: Dict[str, Any]
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    duration_ms: Optional[float] = None
    confidence_score: Optional[float] = None
    metadata: Optional[Dict[str, Any]] = None


class TechStackLogger(ConfigurableService):
    """
    Comprehensive logging service for tech stack generation.
    
    Provides structured logging with context tracking, performance monitoring,
    and configurable output formats for debugging and analysis.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize tech stack logger.
        
        Args:
            config: Logger configuration including:
                - log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
                - output_format: Output format (json, text, structured)
                - log_file: Optional log file path
                - enable_console: Whether to log to console
                - enable_debug_mode: Whether to enable debug tracing
                - buffer_size: Number of log entries to buffer
                - auto_flush: Whether to auto-flush logs
        """
        super().__init__(config, "TechStackLogger")
        self._log_entries: List[LogEntry] = []
        self._session_context: Dict[str, Any] = {}
        self._request_context: Dict[str, Any] = {}
        self._debug_mode = False
        self._performance_tracking = {}
        
    def _do_initialize(self) -> None:
        """Initialize logging infrastructure."""
        # Configure log level
        log_level = self.get_config('log_level', 'INFO')
        self._log_level = getattr(logging, log_level.upper())
        
        # Configure output format
        self._output_format = self.get_config('output_format', 'structured')
        
        # Configure file logging
        log_file = self.get_config('log_file')
        if log_file:
            self._setup_file_logging(log_file)
        
        # Configure console logging
        self._enable_console = self.get_config('enable_console', True)
        if self._enable_console:
            self._setup_console_logging()
        
        # Configure debug mode
        self._debug_mode = self.get_config('enable_debug_mode', False)
        
        # Configure buffering
        self._buffer_size = self.get_config('buffer_size', 1000)
        self._auto_flush = self.get_config('auto_flush', True)
        
        self._logger.info("TechStackLogger initialized successfully")
    
    def _do_shutdown(self) -> None:
        """Shutdown logging service."""
        self.flush_logs()
        self._logger.info("TechStackLogger shutdown completed")
    
    def _setup_file_logging(self, log_file: str) -> None:
        """Setup file-based logging."""
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Create file handler with rotation
        file_handler = logging.FileHandler(log_path)
        file_handler.setLevel(self._log_level)
        
        # Set formatter based on output format
        if self._output_format == 'json':
            formatter = logging.Formatter('%(message)s')
        else:
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        
        file_handler.setFormatter(formatter)
        self._logger.addHandler(file_handler)
    
    def _setup_console_logging(self) -> None:
        """Setup console logging."""
        console_handler = logging.StreamHandler()
        console_handler.setLevel(self._log_level)
        
        # Set formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        console_handler.setFormatter(formatter)
        self._logger.addHandler(console_handler)
    
    def set_session_context(self, session_id: str, context: Dict[str, Any]) -> None:
        """
        Set session context for all subsequent logs.
        
        Args:
            session_id: Session identifier
            context: Session context data
        """
        self._session_context = {
            'session_id': session_id,
            **context
        }
    
    def set_request_context(self, request_id: str, context: Dict[str, Any]) -> None:
        """
        Set request context for current operation.
        
        Args:
            request_id: Request identifier
            context: Request context data
        """
        self._request_context = {
            'request_id': request_id,
            **context
        }
    
    def clear_request_context(self) -> None:
        """Clear current request context."""
        self._request_context = {}
    
    def enable_debug_mode(self, enabled: bool = True) -> None:
        """
        Enable or disable debug mode.
        
        Args:
            enabled: Whether to enable debug mode
        """
        self._debug_mode = enabled
        self.log_info(
            LogCategory.DEBUG_TRACE,
            "TechStackLogger",
            "debug_mode_changed",
            f"Debug mode {'enabled' if enabled else 'disabled'}",
            {"debug_mode": enabled}
        )
    
    def log_debug(self, 
                  category: LogCategory,
                  component: str,
                  operation: str,
                  message: str,
                  context: Optional[Dict[str, Any]] = None,
                  confidence_score: Optional[float] = None,
                  metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log debug message."""
        if self._debug_mode:
            self._log_entry(LogLevel.DEBUG, category, component, operation, 
                          message, context, confidence_score, metadata)
    
    def log_info(self,
                 category: LogCategory,
                 component: str,
                 operation: str,
                 message: str,
                 context: Optional[Dict[str, Any]] = None,
                 confidence_score: Optional[float] = None,
                 metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log info message."""
        self._log_entry(LogLevel.INFO, category, component, operation,
                       message, context, confidence_score, metadata)
    
    def log_warning(self,
                    category: LogCategory,
                    component: str,
                    operation: str,
                    message: str,
                    context: Optional[Dict[str, Any]] = None,
                    confidence_score: Optional[float] = None,
                    metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log warning message."""
        self._log_entry(LogLevel.WARNING, category, component, operation,
                       message, context, confidence_score, metadata)
    
    def log_error(self,
                  category: LogCategory,
                  component: str,
                  operation: str,
                  message: str,
                  context: Optional[Dict[str, Any]] = None,
                  confidence_score: Optional[float] = None,
                  metadata: Optional[Dict[str, Any]] = None,
                  exception: Optional[Exception] = None) -> None:
        """Log error message."""
        error_context = context or {}
        if exception:
            error_context.update({
                'exception_type': type(exception).__name__,
                'exception_message': str(exception)
            })
        
        self._log_entry(LogLevel.ERROR, category, component, operation,
                       message, error_context, confidence_score, metadata)
    
    def log_critical(self,
                     category: LogCategory,
                     component: str,
                     operation: str,
                     message: str,
                     context: Optional[Dict[str, Any]] = None,
                     confidence_score: Optional[float] = None,
                     metadata: Optional[Dict[str, Any]] = None) -> None:
        """Log critical message."""
        self._log_entry(LogLevel.CRITICAL, category, component, operation,
                       message, context, confidence_score, metadata)
    
    def start_performance_tracking(self, operation_id: str) -> None:
        """
        Start performance tracking for an operation.
        
        Args:
            operation_id: Unique operation identifier
        """
        self._performance_tracking[operation_id] = time.time()
    
    def end_performance_tracking(self, 
                                operation_id: str,
                                category: LogCategory,
                                component: str,
                                operation: str,
                                context: Optional[Dict[str, Any]] = None) -> float:
        """
        End performance tracking and log duration.
        
        Args:
            operation_id: Operation identifier
            category: Log category
            component: Component name
            operation: Operation name
            context: Additional context
            
        Returns:
            Duration in milliseconds
        """
        if operation_id not in self._performance_tracking:
            self.log_warning(
                LogCategory.PERFORMANCE,
                "TechStackLogger",
                "performance_tracking",
                f"No start time found for operation: {operation_id}",
                {"operation_id": operation_id}
            )
            return 0.0
        
        start_time = self._performance_tracking.pop(operation_id)
        duration_ms = (time.time() - start_time) * 1000
        
        perf_context = context or {}
        perf_context.update({
            'operation_id': operation_id,
            'duration_ms': duration_ms
        })
        
        self.log_info(
            category,
            component,
            operation,
            f"Operation completed in {duration_ms:.2f}ms",
            perf_context,
            metadata={'performance_data': True}
        )
        
        return duration_ms
    
    def _log_entry(self,
                   level: LogLevel,
                   category: LogCategory,
                   component: str,
                   operation: str,
                   message: str,
                   context: Optional[Dict[str, Any]] = None,
                   confidence_score: Optional[float] = None,
                   metadata: Optional[Dict[str, Any]] = None) -> None:
        """Create and store log entry."""
        # Create log entry
        entry = LogEntry(
            timestamp=datetime.utcnow().isoformat(),
            level=level.value,
            category=category.value,
            component=component,
            operation=operation,
            message=message,
            context=self._merge_context(context),
            session_id=self._session_context.get('session_id'),
            request_id=self._request_context.get('request_id'),
            confidence_score=confidence_score,
            metadata=metadata
        )
        
        # Store entry
        self._log_entries.append(entry)
        
        # Output log entry
        self._output_log_entry(entry)
        
        # Auto-flush if enabled and buffer is full
        if self._auto_flush and len(self._log_entries) >= self._buffer_size:
            self.flush_logs()
    
    def _merge_context(self, context: Optional[Dict[str, Any]]) -> Dict[str, Any]:
        """Merge session, request, and operation context."""
        merged = {}
        merged.update(self._session_context)
        merged.update(self._request_context)
        if context:
            merged.update(context)
        return merged
    
    def _output_log_entry(self, entry: LogEntry) -> None:
        """Output log entry to configured destinations."""
        if self._output_format == 'json':
            log_data = json.dumps(asdict(entry), default=str)
            self._logger.info(log_data)
        elif self._output_format == 'structured':
            log_msg = (
                f"[{entry.category}] {entry.component}.{entry.operation}: "
                f"{entry.message}"
            )
            if entry.confidence_score is not None:
                log_msg += f" (confidence: {entry.confidence_score:.3f})"
            
            # Log at appropriate level
            log_level = getattr(logging, entry.level)
            self._logger.log(log_level, log_msg, extra={'context': entry.context})
        else:
            # Simple text format
            self._logger.log(
                getattr(logging, entry.level),
                f"{entry.component}.{entry.operation}: {entry.message}"
            )
    
    def get_log_entries(self, 
                       category: Optional[LogCategory] = None,
                       component: Optional[str] = None,
                       session_id: Optional[str] = None,
                       request_id: Optional[str] = None,
                       limit: Optional[int] = None) -> List[LogEntry]:
        """
        Get filtered log entries.
        
        Args:
            category: Filter by category
            component: Filter by component
            session_id: Filter by session ID
            request_id: Filter by request ID
            limit: Maximum number of entries to return
            
        Returns:
            Filtered log entries
        """
        entries = self._log_entries
        
        # Apply filters
        if category:
            entries = [e for e in entries if e.category == category.value]
        if component:
            entries = [e for e in entries if e.component == component]
        if session_id:
            entries = [e for e in entries if e.session_id == session_id]
        if request_id:
            entries = [e for e in entries if e.request_id == request_id]
        
        # Apply limit
        if limit:
            entries = entries[-limit:]
        
        return entries
    
    def get_performance_summary(self, 
                               component: Optional[str] = None,
                               operation: Optional[str] = None) -> Dict[str, Any]:
        """
        Get performance summary from logged entries.
        
        Args:
            component: Filter by component
            operation: Filter by operation
            
        Returns:
            Performance summary statistics
        """
        # Filter performance entries
        perf_entries = [
            e for e in self._log_entries 
            if e.category == LogCategory.PERFORMANCE.value and 
               e.metadata and e.metadata.get('performance_data')
        ]
        
        if component:
            perf_entries = [e for e in perf_entries if e.component == component]
        if operation:
            perf_entries = [e for e in perf_entries if e.operation == operation]
        
        if not perf_entries:
            return {}
        
        # Extract durations
        durations = []
        for entry in perf_entries:
            if 'duration_ms' in entry.context:
                durations.append(entry.context['duration_ms'])
        
        if not durations:
            return {}
        
        # Calculate statistics
        return {
            'count': len(durations),
            'min_ms': min(durations),
            'max_ms': max(durations),
            'avg_ms': sum(durations) / len(durations),
            'total_ms': sum(durations)
        }
    
    def flush_logs(self) -> None:
        """Flush buffered log entries."""
        if self._log_entries:
            self._logger.info(f"Flushing {len(self._log_entries)} log entries")
            # In a real implementation, this might write to a database or file
            # For now, we just clear the buffer
            self._log_entries.clear()
    
    def export_logs(self, 
                   file_path: str,
                   format: str = 'json',
                   filters: Optional[Dict[str, Any]] = None) -> None:
        """
        Export log entries to file.
        
        Args:
            file_path: Output file path
            format: Export format (json, csv, text)
            filters: Optional filters to apply
        """
        entries = self._log_entries
        
        # Apply filters if provided
        if filters:
            if 'category' in filters:
                entries = [e for e in entries if e.category == filters['category']]
            if 'component' in filters:
                entries = [e for e in entries if e.component == filters['component']]
            if 'level' in filters:
                entries = [e for e in entries if e.level == filters['level']]
        
        # Export based on format
        output_path = Path(file_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        if format == 'json':
            with open(output_path, 'w') as f:
                json.dump([asdict(e) for e in entries], f, indent=2, default=str)
        elif format == 'csv':
            import csv
            with open(output_path, 'w', newline='') as f:
                if entries:
                    writer = csv.DictWriter(f, fieldnames=asdict(entries[0]).keys())
                    writer.writeheader()
                    for entry in entries:
                        writer.writerow(asdict(entry))
        else:  # text format
            with open(output_path, 'w') as f:
                for entry in entries:
                    f.write(f"{entry.timestamp} [{entry.level}] {entry.component}.{entry.operation}: {entry.message}\n")
        
        self.log_info(
            LogCategory.DEBUG_TRACE,
            "TechStackLogger",
            "export_logs",
            f"Exported {len(entries)} log entries to {file_path}",
            {"file_path": file_path, "format": format, "entry_count": len(entries)}
        )