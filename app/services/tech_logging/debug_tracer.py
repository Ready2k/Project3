"""
Debug tracer service for step-by-step execution tracing.

Provides detailed debug tracing capabilities with step-by-step execution logs,
variable state tracking, and interactive debugging support.
"""

from typing import Dict, Any, List, Optional, Union, Callable
from dataclasses import dataclass, asdict
from datetime import datetime
import time
import json
from contextlib import contextmanager
from enum import Enum

from .tech_stack_logger import TechStackLogger, LogCategory


class TraceLevel(Enum):
    """Debug trace levels."""
    MINIMAL = "minimal"      # Only major steps
    NORMAL = "normal"        # Standard debugging info
    DETAILED = "detailed"    # Detailed step-by-step
    VERBOSE = "verbose"      # Everything including variable states


@dataclass
class TraceStep:
    """Individual trace step."""
    step_id: str
    step_name: str
    component: str
    operation: str
    timestamp: str
    duration_ms: Optional[float]
    input_data: Optional[Dict[str, Any]]
    output_data: Optional[Dict[str, Any]]
    variables: Optional[Dict[str, Any]]
    metadata: Optional[Dict[str, Any]]
    parent_step_id: Optional[str]
    children_step_ids: List[str]


@dataclass
class ExecutionTrace:
    """Complete execution trace."""
    trace_id: str
    component: str
    operation: str
    start_time: str
    end_time: Optional[str]
    total_duration_ms: Optional[float]
    steps: List[TraceStep]
    success: bool
    error_message: Optional[str]
    metadata: Optional[Dict[str, Any]]


class DebugTracer:
    """
    Service for detailed debug tracing of tech stack generation processes.
    
    Provides step-by-step execution tracing with variable state tracking,
    performance monitoring, and interactive debugging capabilities.
    """
    
    def __init__(self, tech_stack_logger: TechStackLogger):
        """
        Initialize debug tracer.
        
        Args:
            tech_stack_logger: Main tech stack logger instance
        """
        self.logger = tech_stack_logger
        self._trace_level = TraceLevel.NORMAL
        self._active_traces: Dict[str, Dict[str, Any]] = {}
        self._step_stack: List[str] = []
        self._execution_traces: List[ExecutionTrace] = []
        self._enabled = False
    
    def enable_tracing(self, 
                      trace_level: TraceLevel = TraceLevel.NORMAL,
                      max_traces: int = 100) -> None:
        """
        Enable debug tracing.
        
        Args:
            trace_level: Level of detail for tracing
            max_traces: Maximum number of traces to keep in memory
        """
        self._enabled = True
        self._trace_level = trace_level
        self._max_traces = max_traces
        
        self.logger.log_info(
            LogCategory.DEBUG_TRACE,
            "DebugTracer",
            "enable_tracing",
            f"Debug tracing enabled at level: {trace_level.value}",
            {
                'trace_level': trace_level.value,
                'max_traces': max_traces
            }
        )
    
    def disable_tracing(self) -> None:
        """Disable debug tracing."""
        self._enabled = False
        
        self.logger.log_info(
            LogCategory.DEBUG_TRACE,
            "DebugTracer",
            "disable_tracing",
            "Debug tracing disabled",
            {}
        )
    
    def start_trace(self,
                   trace_id: str,
                   component: str,
                   operation: str,
                   metadata: Optional[Dict[str, Any]] = None) -> str:
        """
        Start a new execution trace.
        
        Args:
            trace_id: Unique trace identifier
            component: Component being traced
            operation: Operation being traced
            metadata: Additional metadata
            
        Returns:
            Trace ID
        """
        if not self._enabled:
            return trace_id
        
        self._active_traces[trace_id] = {
            'trace_id': trace_id,
            'component': component,
            'operation': operation,
            'start_time': datetime.utcnow(),
            'steps': [],
            'step_counter': 0,
            'metadata': metadata or {}
        }
        
        if self._trace_level in [TraceLevel.DETAILED, TraceLevel.VERBOSE]:
            self.logger.log_debug(
                LogCategory.DEBUG_TRACE,
                component,
                operation,
                f"Started execution trace: {trace_id}",
                {
                    'trace_id': trace_id,
                    'metadata': metadata
                }
            )
        
        return trace_id
    
    def end_trace(self,
                 trace_id: str,
                 success: bool = True,
                 error_message: Optional[str] = None) -> Optional[ExecutionTrace]:
        """
        End an execution trace.
        
        Args:
            trace_id: Trace identifier
            success: Whether execution was successful
            error_message: Error message if failed
            
        Returns:
            Complete execution trace or None if tracing disabled
        """
        if not self._enabled or trace_id not in self._active_traces:
            return None
        
        trace_data = self._active_traces.pop(trace_id)
        end_time = datetime.utcnow()
        duration_ms = (end_time - trace_data['start_time']).total_seconds() * 1000
        
        # Create execution trace
        execution_trace = ExecutionTrace(
            trace_id=trace_id,
            component=trace_data['component'],
            operation=trace_data['operation'],
            start_time=trace_data['start_time'].isoformat(),
            end_time=end_time.isoformat(),
            total_duration_ms=duration_ms,
            steps=trace_data['steps'],
            success=success,
            error_message=error_message,
            metadata=trace_data['metadata']
        )
        
        # Store trace
        self._execution_traces.append(execution_trace)
        
        # Limit number of stored traces
        if len(self._execution_traces) > self._max_traces:
            self._execution_traces = self._execution_traces[-self._max_traces:]
        
        # Log trace completion
        self.logger.log_info(
            LogCategory.DEBUG_TRACE,
            trace_data['component'],
            trace_data['operation'],
            f"Execution trace completed: {trace_id}",
            {
                'trace_id': trace_id,
                'duration_ms': duration_ms,
                'step_count': len(trace_data['steps']),
                'success': success,
                'error_message': error_message
            }
        )
        
        return execution_trace
    
    @contextmanager
    def trace_step(self,
                   trace_id: str,
                   step_name: str,
                   input_data: Optional[Dict[str, Any]] = None,
                   capture_variables: bool = False):
        """
        Context manager for tracing individual steps.
        
        Args:
            trace_id: Trace identifier
            step_name: Name of the step
            input_data: Input data for the step
            capture_variables: Whether to capture local variables
        """
        if not self._enabled or trace_id not in self._active_traces:
            yield None
            return
        
        trace_data = self._active_traces[trace_id]
        step_id = f"{trace_id}_step_{trace_data['step_counter']}"
        trace_data['step_counter'] += 1
        
        # Create step
        step = TraceStep(
            step_id=step_id,
            step_name=step_name,
            component=trace_data['component'],
            operation=trace_data['operation'],
            timestamp=datetime.utcnow().isoformat(),
            duration_ms=None,
            input_data=input_data,
            output_data=None,
            variables=None,
            metadata=None,
            parent_step_id=self._step_stack[-1] if self._step_stack else None,
            children_step_ids=[]
        )
        
        # Add to parent's children if there's a parent
        if self._step_stack:
            parent_step_id = self._step_stack[-1]
            for existing_step in trace_data['steps']:
                if existing_step.step_id == parent_step_id:
                    existing_step.children_step_ids.append(step_id)
                    break
        
        self._step_stack.append(step_id)
        start_time = time.time()
        
        try:
            # Log step start
            if self._trace_level in [TraceLevel.DETAILED, TraceLevel.VERBOSE]:
                self.logger.log_debug(
                    LogCategory.DEBUG_TRACE,
                    trace_data['component'],
                    f"step_{step_name}",
                    f"Starting step: {step_name}",
                    {
                        'trace_id': trace_id,
                        'step_id': step_id,
                        'step_name': step_name,
                        'input_data': input_data
                    }
                )
            
            yield step
            
        except Exception as e:
            # Log step error
            self.logger.log_error(
                LogCategory.DEBUG_TRACE,
                trace_data['component'],
                f"step_{step_name}",
                f"Step failed: {step_name}",
                {
                    'trace_id': trace_id,
                    'step_id': step_id,
                    'step_name': step_name,
                    'error': str(e)
                },
                exception=e
            )
            raise
        
        finally:
            # Calculate duration and finalize step
            duration_ms = (time.time() - start_time) * 1000
            step.duration_ms = duration_ms
            
            # Capture variables if requested and at verbose level
            if capture_variables and self._trace_level == TraceLevel.VERBOSE:
                import inspect
                frame = inspect.currentframe().f_back
                step.variables = {
                    k: str(v)[:100] for k, v in frame.f_locals.items()
                    if not k.startswith('_') and not callable(v)
                }
            
            # Add step to trace
            trace_data['steps'].append(step)
            
            # Remove from stack
            if self._step_stack and self._step_stack[-1] == step_id:
                self._step_stack.pop()
            
            # Log step completion
            if self._trace_level in [TraceLevel.DETAILED, TraceLevel.VERBOSE]:
                self.logger.log_debug(
                    LogCategory.DEBUG_TRACE,
                    trace_data['component'],
                    f"step_{step_name}",
                    f"Completed step: {step_name} in {duration_ms:.2f}ms",
                    {
                        'trace_id': trace_id,
                        'step_id': step_id,
                        'step_name': step_name,
                        'duration_ms': duration_ms
                    }
                )
    
    def log_variable_state(self,
                          trace_id: str,
                          variable_name: str,
                          variable_value: Any,
                          context: Optional[str] = None) -> None:
        """
        Log variable state during execution.
        
        Args:
            trace_id: Trace identifier
            variable_name: Name of the variable
            variable_value: Current value of the variable
            context: Additional context about the variable
        """
        if not self._enabled or self._trace_level != TraceLevel.VERBOSE:
            return
        
        if trace_id not in self._active_traces:
            return
        
        trace_data = self._active_traces[trace_id]
        
        self.logger.log_debug(
            LogCategory.DEBUG_TRACE,
            trace_data['component'],
            "variable_state",
            f"Variable {variable_name} = {str(variable_value)[:100]}",
            {
                'trace_id': trace_id,
                'variable_name': variable_name,
                'variable_value': str(variable_value)[:200],
                'variable_type': type(variable_value).__name__,
                'context': context
            }
        )
    
    def log_decision_point(self,
                          trace_id: str,
                          decision_name: str,
                          condition: str,
                          result: bool,
                          reasoning: Optional[str] = None) -> None:
        """
        Log decision points in execution flow.
        
        Args:
            trace_id: Trace identifier
            decision_name: Name of the decision
            condition: Condition being evaluated
            result: Result of the decision
            reasoning: Reasoning for the decision
        """
        if not self._enabled or trace_id not in self._active_traces:
            return
        
        trace_data = self._active_traces[trace_id]
        
        self.logger.log_debug(
            LogCategory.DEBUG_TRACE,
            trace_data['component'],
            "decision_point",
            f"Decision {decision_name}: {condition} -> {result}",
            {
                'trace_id': trace_id,
                'decision_name': decision_name,
                'condition': condition,
                'result': result,
                'reasoning': reasoning
            }
        )
    
    def log_data_transformation(self,
                               trace_id: str,
                               transformation_name: str,
                               input_data: Any,
                               output_data: Any,
                               transformation_rules: Optional[List[str]] = None) -> None:
        """
        Log data transformations.
        
        Args:
            trace_id: Trace identifier
            transformation_name: Name of the transformation
            input_data: Input data
            output_data: Output data
            transformation_rules: Rules applied during transformation
        """
        if not self._enabled or trace_id not in self._active_traces:
            return
        
        trace_data = self._active_traces[trace_id]
        
        self.logger.log_debug(
            LogCategory.DEBUG_TRACE,
            trace_data['component'],
            "data_transformation",
            f"Transformation {transformation_name}: {type(input_data).__name__} -> {type(output_data).__name__}",
            {
                'trace_id': trace_id,
                'transformation_name': transformation_name,
                'input_type': type(input_data).__name__,
                'output_type': type(output_data).__name__,
                'input_size': len(str(input_data)),
                'output_size': len(str(output_data)),
                'transformation_rules': transformation_rules
            }
        )
    
    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """
        Get a specific execution trace.
        
        Args:
            trace_id: Trace identifier
            
        Returns:
            Execution trace or None if not found
        """
        for trace in self._execution_traces:
            if trace.trace_id == trace_id:
                return trace
        return None
    
    def get_traces(self,
                  component: Optional[str] = None,
                  operation: Optional[str] = None,
                  success_only: bool = False,
                  limit: Optional[int] = None) -> List[ExecutionTrace]:
        """
        Get execution traces with optional filtering.
        
        Args:
            component: Filter by component
            operation: Filter by operation
            success_only: Only return successful traces
            limit: Maximum number of traces to return
            
        Returns:
            List of execution traces
        """
        traces = self._execution_traces
        
        # Apply filters
        if component:
            traces = [t for t in traces if t.component == component]
        if operation:
            traces = [t for t in traces if t.operation == operation]
        if success_only:
            traces = [t for t in traces if t.success]
        
        # Apply limit
        if limit:
            traces = traces[-limit:]
        
        return traces
    
    def export_trace(self,
                    trace_id: str,
                    file_path: str,
                    format: str = 'json') -> bool:
        """
        Export a trace to file.
        
        Args:
            trace_id: Trace identifier
            file_path: Output file path
            format: Export format (json, text)
            
        Returns:
            True if export successful, False otherwise
        """
        trace = self.get_trace(trace_id)
        if not trace:
            return False
        
        try:
            if format == 'json':
                with open(file_path, 'w') as f:
                    json.dump(asdict(trace), f, indent=2, default=str)
            else:  # text format
                with open(file_path, 'w') as f:
                    f.write(f"Execution Trace: {trace.trace_id}\n")
                    f.write(f"Component: {trace.component}\n")
                    f.write(f"Operation: {trace.operation}\n")
                    f.write(f"Duration: {trace.total_duration_ms:.2f}ms\n")
                    f.write(f"Success: {trace.success}\n")
                    if trace.error_message:
                        f.write(f"Error: {trace.error_message}\n")
                    f.write("\nSteps:\n")
                    
                    for step in trace.steps:
                        indent = "  " * (len([s for s in trace.steps if step.step_id in s.children_step_ids]))
                        f.write(f"{indent}- {step.step_name} ({step.duration_ms:.2f}ms)\n")
            
            return True
            
        except Exception as e:
            self.logger.log_error(
                LogCategory.DEBUG_TRACE,
                "DebugTracer",
                "export_trace",
                f"Failed to export trace {trace_id}: {e}",
                {'trace_id': trace_id, 'file_path': file_path, 'format': format},
                exception=e
            )
            return False
    
    def get_performance_summary(self) -> Dict[str, Any]:
        """
        Get performance summary from traces.
        
        Returns:
            Performance summary statistics
        """
        if not self._execution_traces:
            return {}
        
        # Calculate statistics
        durations = [t.total_duration_ms for t in self._execution_traces if t.total_duration_ms]
        step_counts = [len(t.steps) for t in self._execution_traces]
        success_count = len([t for t in self._execution_traces if t.success])
        
        # Component and operation statistics
        components = {}
        operations = {}
        
        for trace in self._execution_traces:
            components[trace.component] = components.get(trace.component, 0) + 1
            operations[trace.operation] = operations.get(trace.operation, 0) + 1
        
        return {
            'total_traces': len(self._execution_traces),
            'successful_traces': success_count,
            'success_rate': success_count / len(self._execution_traces),
            'average_duration_ms': sum(durations) / len(durations) if durations else 0,
            'average_steps': sum(step_counts) / len(step_counts) if step_counts else 0,
            'component_distribution': components,
            'operation_distribution': operations,
            'trace_level': self._trace_level.value,
            'tracing_enabled': self._enabled
        }