"""
Tech Stack Generation Monitoring Integration Service

Bridges tech stack generation workflow with monitoring components,
providing session-based monitoring with correlation IDs and real-time data collection.
"""

import asyncio
import uuid
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Union
import logging
from dataclasses import dataclass, asdict
from enum import Enum

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


class MonitoringEventType(Enum):
    """Types of monitoring events."""
    SESSION_START = "session_start"
    PARSING_START = "parsing_start"
    PARSING_COMPLETE = "parsing_complete"
    EXTRACTION_START = "extraction_start"
    EXTRACTION_COMPLETE = "extraction_complete"
    LLM_CALL_START = "llm_call_start"
    LLM_CALL_COMPLETE = "llm_call_complete"
    VALIDATION_START = "validation_start"
    VALIDATION_COMPLETE = "validation_complete"
    SESSION_COMPLETE = "session_complete"
    SESSION_ERROR = "session_error"


@dataclass
class MonitoringSession:
    """Monitoring session data structure."""
    session_id: str
    correlation_id: str
    start_time: datetime
    end_time: Optional[datetime] = None
    status: str = "active"  # active, completed, error
    requirements: Optional[Dict[str, Any]] = None
    metadata: Optional[Dict[str, Any]] = None
    events: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.events is None:
            self.events = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['start_time'] = self.start_time.isoformat()
        if self.end_time:
            data['end_time'] = self.end_time.isoformat()
        return data


@dataclass
class MonitoringEvent:
    """Individual monitoring event."""
    event_id: str
    session_id: str
    correlation_id: str
    event_type: MonitoringEventType
    timestamp: datetime
    component: str
    operation: str
    data: Dict[str, Any]
    duration_ms: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['event_type'] = self.event_type.value
        return data


class TechStackMonitoringIntegrationService(ConfigurableService):
    """
    Service that integrates monitoring into tech stack generation workflow.
    
    Provides session-based monitoring with correlation IDs, real-time data collection,
    and streaming to monitoring components.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'TechStackMonitoringIntegration')
        
        # Initialize logger
        try:
            self.logger = require_service('logger', context='TechStackMonitoringIntegration')
        except:
            import logging
            self.logger = logging.getLogger('TechStackMonitoringIntegration')
        
        # Session management
        self.active_sessions: Dict[str, MonitoringSession] = {}
        self.session_events: Dict[str, List[MonitoringEvent]] = {}
        
        # Monitoring components
        self.tech_stack_monitor = None
        self.quality_assurance = None
        self.performance_analytics = None
        
        # Configuration
        self.config = {
            'max_session_duration_hours': 24,
            'max_events_per_session': 1000,
            'cleanup_interval_minutes': 60,
            'real_time_streaming': True,
            'buffer_size': 100,
            **config
        } if config else {
            'max_session_duration_hours': 24,
            'max_events_per_session': 1000,
            'cleanup_interval_minutes': 60,
            'real_time_streaming': True,
            'buffer_size': 100
        }
        
        # Event buffer for real-time streaming
        self.event_buffer: List[MonitoringEvent] = []
        self.buffer_lock = asyncio.Lock()
        
        # Service state
        self.is_running = False
        self.cleanup_task = None
        self.streaming_task = None
    
    async def _do_initialize(self) -> None:
        """Initialize the monitoring integration service."""
        await self.start_monitoring_integration()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the monitoring integration service."""
        await self.stop_monitoring_integration()
    
    async def start_monitoring_integration(self) -> None:
        """Start the monitoring integration service."""
        try:
            self.logger.info("Starting tech stack monitoring integration service")
            
            # Initialize monitoring components
            await self._initialize_monitoring_components()
            
            # Start background tasks
            self.is_running = True
            self.cleanup_task = asyncio.create_task(self._cleanup_sessions_task())
            
            if self.config['real_time_streaming']:
                self.streaming_task = asyncio.create_task(self._real_time_streaming_task())
            
            self.logger.info("Tech stack monitoring integration service started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring integration service: {e}")
            raise
    
    async def stop_monitoring_integration(self) -> None:
        """Stop the monitoring integration service."""
        try:
            self.logger.info("Stopping tech stack monitoring integration service")
            
            self.is_running = False
            
            # Cancel background tasks
            if self.cleanup_task:
                self.cleanup_task.cancel()
                try:
                    await self.cleanup_task
                except asyncio.CancelledError:
                    pass
            
            if self.streaming_task:
                self.streaming_task.cancel()
                try:
                    await self.streaming_task
                except asyncio.CancelledError:
                    pass
            
            # Flush remaining events
            await self._flush_event_buffer()
            
            # Complete any active sessions
            await self._complete_active_sessions()
            
            self.logger.info("Tech stack monitoring integration service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring integration service: {e}")
    
    async def _initialize_monitoring_components(self) -> None:
        """Initialize monitoring components."""
        try:
            # Get monitoring components from service registry
            self.tech_stack_monitor = optional_service('tech_stack_monitor', context='MonitoringIntegration')
            self.quality_assurance = optional_service('quality_assurance_system', context='MonitoringIntegration')
            self.performance_analytics = optional_service('performance_analytics', context='MonitoringIntegration')
            
            # If not available from registry, try to import directly
            if not self.tech_stack_monitor:
                try:
                    from app.monitoring.tech_stack_monitor import TechStackMonitor
                    self.tech_stack_monitor = TechStackMonitor()
                    await self.tech_stack_monitor.start_monitoring()
                except ImportError:
                    self.logger.warning("TechStackMonitor not available")
            
            if not self.quality_assurance:
                try:
                    from app.monitoring.quality_assurance import QualityAssuranceSystem
                    self.quality_assurance = QualityAssuranceSystem()
                    await self.quality_assurance.start_qa_system()
                except ImportError:
                    self.logger.warning("QualityAssuranceSystem not available")
            
            if not self.performance_analytics:
                try:
                    from app.monitoring.performance_analytics import PerformanceAnalytics
                    self.performance_analytics = PerformanceAnalytics()
                    await self.performance_analytics.start_analytics()
                except ImportError:
                    self.logger.warning("PerformanceAnalytics not available")
                except Exception as e:
                    self.logger.warning(f"Could not initialize PerformanceAnalytics: {e}")
            
            self.logger.info(f"Initialized monitoring components: "
                           f"monitor={bool(self.tech_stack_monitor)}, "
                           f"qa={bool(self.quality_assurance)}, "
                           f"analytics={bool(self.performance_analytics)}")
            
        except Exception as e:
            self.logger.error(f"Error initializing monitoring components: {e}")
    
    def start_generation_monitoring(self, 
                                  requirements: Dict[str, Any],
                                  metadata: Optional[Dict[str, Any]] = None) -> MonitoringSession:
        """
        Start monitoring for a tech stack generation session.
        
        Args:
            requirements: User requirements being processed
            metadata: Additional session metadata
            
        Returns:
            MonitoringSession object with session and correlation IDs
        """
        session_id = str(uuid.uuid4())
        correlation_id = f"tsg_{int(datetime.now().timestamp())}_{session_id[:8]}"
        
        session = MonitoringSession(
            session_id=session_id,
            correlation_id=correlation_id,
            start_time=datetime.now(),
            requirements=requirements,
            metadata=metadata or {}
        )
        
        self.active_sessions[session_id] = session
        self.session_events[session_id] = []
        
        # Create session start event
        start_event = MonitoringEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            correlation_id=correlation_id,
            event_type=MonitoringEventType.SESSION_START,
            timestamp=datetime.now(),
            component="TechStackGenerator",
            operation="start_generation",
            data={
                'requirements_keys': list(requirements.keys()) if requirements else [],
                'requirements_size': len(str(requirements)) if requirements else 0,
                'metadata': metadata or {}
            }
        )
        
        # Record event synchronously for session start to avoid event loop issues
        self.session_events[session_id].append(start_event)
        
        # Add to buffer for real-time streaming if enabled
        if self.config['real_time_streaming']:
            self.event_buffer.append(start_event)
            
            # Check if buffer needs flushing
            if len(self.event_buffer) >= self.config['buffer_size']:
                # Schedule flush for later if in async context, otherwise skip
                try:
                    asyncio.create_task(self._flush_event_buffer())
                except RuntimeError:
                    # No event loop running, skip async flush
                    pass
        
        self.logger.info(f"Started monitoring session {session_id} with correlation ID {correlation_id}")
        
        return session
    
    async def track_parsing_step(self, 
                               session_id: str,
                               step_name: str,
                               input_data: Dict[str, Any],
                               output_data: Optional[Dict[str, Any]] = None,
                               duration_ms: Optional[float] = None,
                               success: bool = True,
                               error_message: Optional[str] = None) -> None:
        """
        Track a parsing step in tech stack generation.
        
        Args:
            session_id: Session identifier
            step_name: Name of the parsing step
            input_data: Input data for the step
            output_data: Output data from the step
            duration_ms: Step duration in milliseconds
            success: Whether the step succeeded
            error_message: Error message if step failed
        """
        session = self.active_sessions.get(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} not found for parsing step tracking")
            return
        
        event_type = MonitoringEventType.PARSING_COMPLETE if output_data else MonitoringEventType.PARSING_START
        
        event = MonitoringEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            correlation_id=session.correlation_id,
            event_type=event_type,
            timestamp=datetime.now(),
            component="RequirementParser",
            operation=step_name,
            data={
                'input_data': input_data,
                'output_data': output_data,
                'step_name': step_name
            },
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        
        await self._record_event(event)
        
        # Stream to monitoring components
        if self.tech_stack_monitor and output_data:
            await self._stream_parsing_metrics(session_id, step_name, input_data, output_data, duration_ms)
    
    async def track_extraction_step(self,
                                  session_id: str,
                                  extraction_type: str,
                                  extracted_technologies: List[str],
                                  confidence_scores: Dict[str, float],
                                  context_data: Dict[str, Any],
                                  duration_ms: Optional[float] = None,
                                  success: bool = True,
                                  error_message: Optional[str] = None) -> None:
        """
        Track technology extraction step.
        
        Args:
            session_id: Session identifier
            extraction_type: Type of extraction (explicit, contextual, pattern-based)
            extracted_technologies: List of extracted technology names
            confidence_scores: Confidence scores for extracted technologies
            context_data: Context information used in extraction
            duration_ms: Extraction duration in milliseconds
            success: Whether extraction succeeded
            error_message: Error message if extraction failed
        """
        session = self.active_sessions.get(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} not found for extraction step tracking")
            return
        
        event = MonitoringEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            correlation_id=session.correlation_id,
            event_type=MonitoringEventType.EXTRACTION_COMPLETE,
            timestamp=datetime.now(),
            component="TechnologyExtractor",
            operation=extraction_type,
            data={
                'extraction_type': extraction_type,
                'extracted_technologies': extracted_technologies,
                'confidence_scores': confidence_scores,
                'context_data': context_data,
                'extraction_count': len(extracted_technologies)
            },
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        
        await self._record_event(event)
        
        # Stream to monitoring components
        if self.tech_stack_monitor:
            await self._stream_extraction_metrics(
                session_id, extraction_type, extracted_technologies, 
                confidence_scores, duration_ms
            )
    
    async def track_llm_interaction(self,
                                  session_id: str,
                                  provider: str,
                                  model: str,
                                  prompt_data: Dict[str, Any],
                                  response_data: Dict[str, Any],
                                  token_usage: Optional[Dict[str, int]] = None,
                                  duration_ms: Optional[float] = None,
                                  success: bool = True,
                                  error_message: Optional[str] = None) -> None:
        """
        Track LLM interaction during tech stack generation.
        
        Args:
            session_id: Session identifier
            provider: LLM provider name
            model: Model name used
            prompt_data: Prompt information (without full text for privacy)
            response_data: Response information
            token_usage: Token usage statistics
            duration_ms: LLM call duration in milliseconds
            success: Whether LLM call succeeded
            error_message: Error message if call failed
        """
        session = self.active_sessions.get(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} not found for LLM interaction tracking")
            return
        
        event_type = MonitoringEventType.LLM_CALL_COMPLETE if response_data else MonitoringEventType.LLM_CALL_START
        
        event = MonitoringEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            correlation_id=session.correlation_id,
            event_type=event_type,
            timestamp=datetime.now(),
            component="LLMProvider",
            operation=f"{provider}_{model}",
            data={
                'provider': provider,
                'model': model,
                'prompt_data': prompt_data,
                'response_data': response_data,
                'token_usage': token_usage or {},
                'has_response': bool(response_data)
            },
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        
        await self._record_event(event)
        
        # Stream to monitoring components
        if self.tech_stack_monitor and response_data:
            await self._stream_llm_metrics(
                session_id, provider, model, prompt_data, response_data, 
                token_usage, duration_ms, success
            )
    
    async def track_validation_step(self,
                                  session_id: str,
                                  validation_type: str,
                                  input_technologies: List[str],
                                  validation_results: Dict[str, Any],
                                  conflicts_detected: List[Dict[str, Any]],
                                  resolutions_applied: List[Dict[str, Any]],
                                  duration_ms: Optional[float] = None,
                                  success: bool = True,
                                  error_message: Optional[str] = None) -> None:
        """
        Track validation step in tech stack generation.
        
        Args:
            session_id: Session identifier
            validation_type: Type of validation (compatibility, ecosystem, etc.)
            input_technologies: Technologies being validated
            validation_results: Validation results
            conflicts_detected: List of conflicts found
            resolutions_applied: List of resolutions applied
            duration_ms: Validation duration in milliseconds
            success: Whether validation succeeded
            error_message: Error message if validation failed
        """
        session = self.active_sessions.get(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} not found for validation step tracking")
            return
        
        event = MonitoringEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            correlation_id=session.correlation_id,
            event_type=MonitoringEventType.VALIDATION_COMPLETE,
            timestamp=datetime.now(),
            component="TechnologyValidator",
            operation=validation_type,
            data={
                'validation_type': validation_type,
                'input_technologies': input_technologies,
                'validation_results': validation_results,
                'conflicts_detected': conflicts_detected,
                'resolutions_applied': resolutions_applied,
                'conflict_count': len(conflicts_detected),
                'resolution_count': len(resolutions_applied)
            },
            duration_ms=duration_ms,
            success=success,
            error_message=error_message
        )
        
        await self._record_event(event)
        
        # Stream to monitoring components
        if self.quality_assurance:
            await self._stream_validation_metrics(
                session_id, validation_type, input_technologies, 
                validation_results, conflicts_detected, duration_ms
            )
    
    async def complete_generation_monitoring(self,
                                           session_id: str,
                                           final_tech_stack: List[str],
                                           generation_metrics: Dict[str, Any],
                                           success: bool = True,
                                           error_message: Optional[str] = None) -> MonitoringSession:
        """
        Complete monitoring for a tech stack generation session.
        
        Args:
            session_id: Session identifier
            final_tech_stack: Final generated technology stack
            generation_metrics: Overall generation metrics
            success: Whether generation succeeded
            error_message: Error message if generation failed
            
        Returns:
            Completed MonitoringSession object
        """
        session = self.active_sessions.get(session_id)
        if not session:
            self.logger.warning(f"Session {session_id} not found for completion")
            return None
        
        # Update session
        session.end_time = datetime.now()
        session.status = "completed" if success else "error"
        
        # Create completion event
        event_type = MonitoringEventType.SESSION_COMPLETE if success else MonitoringEventType.SESSION_ERROR
        
        completion_event = MonitoringEvent(
            event_id=str(uuid.uuid4()),
            session_id=session_id,
            correlation_id=session.correlation_id,
            event_type=event_type,
            timestamp=datetime.now(),
            component="TechStackGenerator",
            operation="complete_generation",
            data={
                'final_tech_stack': final_tech_stack,
                'generation_metrics': generation_metrics,
                'total_duration_ms': (session.end_time - session.start_time).total_seconds() * 1000,
                'event_count': len(self.session_events.get(session_id, []))
            },
            success=success,
            error_message=error_message
        )
        
        await self._record_event(completion_event)
        
        # Stream final metrics to monitoring components
        await self._stream_completion_metrics(session, final_tech_stack, generation_metrics, success)
        
        # Move session to completed
        completed_session = self.active_sessions.pop(session_id, None)
        
        self.logger.info(f"Completed monitoring session {session_id} - "
                        f"Status: {session.status}, "
                        f"Duration: {(session.end_time - session.start_time).total_seconds():.2f}s, "
                        f"Events: {len(self.session_events.get(session_id, []))}")
        
        return completed_session
    
    async def _record_event(self, event: MonitoringEvent) -> None:
        """Record a monitoring event."""
        try:
            # Add to session events
            if event.session_id in self.session_events:
                self.session_events[event.session_id].append(event)
                
                # Limit events per session
                max_events = self.config['max_events_per_session']
                if len(self.session_events[event.session_id]) > max_events:
                    self.session_events[event.session_id] = self.session_events[event.session_id][-max_events:]
            
            # Add to buffer for real-time streaming
            if self.config['real_time_streaming']:
                async with self.buffer_lock:
                    self.event_buffer.append(event)
                    
                    # Flush buffer if it's full
                    if len(self.event_buffer) >= self.config['buffer_size']:
                        try:
                            await self._flush_event_buffer()
                        except Exception as flush_error:
                            # If async flush fails, do sync buffer management
                            self.logger.error(f"Async buffer flush failed, using sync management: {flush_error}")
                            keep_count = max(1, self.config['buffer_size'] // 2)
                            self.event_buffer = self.event_buffer[-keep_count:]
            
        except Exception as e:
            self.logger.error(f"Error recording monitoring event: {e}")
    
    def _record_event_sync(self, event: MonitoringEvent) -> None:
        """Record a monitoring event synchronously."""
        try:
            # Add to session events
            if event.session_id in self.session_events:
                self.session_events[event.session_id].append(event)
                
                # Limit events per session
                max_events = self.config['max_events_per_session']
                if len(self.session_events[event.session_id]) > max_events:
                    self.session_events[event.session_id] = self.session_events[event.session_id][-max_events:]
            
            # Add to buffer for real-time streaming
            if self.config['real_time_streaming']:
                self.event_buffer.append(event)
                
                # Flush buffer if it's full (synchronously)
                if len(self.event_buffer) >= self.config['buffer_size']:
                    # Keep only the most recent half of the buffer
                    keep_count = max(1, self.config['buffer_size'] // 2)
                    self.event_buffer = self.event_buffer[-keep_count:]
            
        except Exception as e:
            self.logger.error(f"Error recording monitoring event: {e}")
    
    async def _flush_event_buffer(self) -> None:
        """Flush event buffer to monitoring components."""
        if not self.event_buffer:
            return
        
        try:
            async with self.buffer_lock:
                events_to_flush = self.event_buffer.copy()
                self.event_buffer.clear()
            
            # Stream events to monitoring components
            for event in events_to_flush:
                await self._stream_event_to_components(event)
                
        except Exception as e:
            self.logger.error(f"Error flushing event buffer: {e}")
    
    async def _stream_event_to_components(self, event: MonitoringEvent) -> None:
        """Stream individual event to monitoring components."""
        try:
            # Stream to tech stack monitor
            if self.tech_stack_monitor:
                await self._stream_to_tech_stack_monitor(event)
            
            # Stream to quality assurance
            if self.quality_assurance:
                await self._stream_to_quality_assurance(event)
            
            # Stream to performance analytics
            if self.performance_analytics:
                await self._stream_to_performance_analytics(event)
                
        except Exception as e:
            self.logger.error(f"Error streaming event to components: {e}")
    
    async def _stream_parsing_metrics(self, session_id: str, step_name: str, 
                                    input_data: Dict[str, Any], output_data: Dict[str, Any],
                                    duration_ms: Optional[float]) -> None:
        """Stream parsing metrics to monitoring components."""
        if not self.tech_stack_monitor:
            return
        
        try:
            # Extract relevant metrics for tech stack monitor
            extracted_count = len(output_data.get('explicit_technologies', []))
            expected_count = len(input_data.get('requirements', {}).get('technologies', []))
            
            if hasattr(self.tech_stack_monitor, 'record_extraction_accuracy'):
                self.tech_stack_monitor.record_extraction_accuracy(
                    session_id=session_id,
                    extracted_count=extracted_count,
                    expected_count=max(expected_count, extracted_count),  # Avoid division by zero
                    explicit_tech_included=extracted_count,
                    explicit_tech_total=extracted_count,
                    processing_time=(duration_ms or 0) / 1000.0  # Convert to seconds
                )
                
        except Exception as e:
            self.logger.error(f"Error streaming parsing metrics: {e}")
    
    async def _stream_extraction_metrics(self, session_id: str, extraction_type: str,
                                       extracted_technologies: List[str],
                                       confidence_scores: Dict[str, float],
                                       duration_ms: Optional[float]) -> None:
        """Stream extraction metrics to monitoring components."""
        # Implementation would depend on specific monitoring component interfaces
        pass
    
    async def _stream_llm_metrics(self, session_id: str, provider: str, model: str,
                                prompt_data: Dict[str, Any], response_data: Dict[str, Any],
                                token_usage: Optional[Dict[str, int]], duration_ms: Optional[float],
                                success: bool) -> None:
        """Stream LLM metrics to monitoring components."""
        # Implementation would depend on specific monitoring component interfaces
        pass
    
    async def _stream_validation_metrics(self, session_id: str, validation_type: str,
                                       input_technologies: List[str],
                                       validation_results: Dict[str, Any],
                                       conflicts_detected: List[Dict[str, Any]],
                                       duration_ms: Optional[float]) -> None:
        """Stream validation metrics to monitoring components."""
        # Implementation would depend on specific monitoring component interfaces
        pass
    
    async def _stream_completion_metrics(self, session: MonitoringSession,
                                       final_tech_stack: List[str],
                                       generation_metrics: Dict[str, Any],
                                       success: bool) -> None:
        """Stream completion metrics to monitoring components."""
        if not self.tech_stack_monitor:
            return
        
        try:
            # Calculate overall metrics
            total_duration = (session.end_time - session.start_time).total_seconds()
            
            # Get explicit technologies from session requirements
            explicit_techs = []
            if session.requirements:
                # Extract explicit technologies from requirements
                req_text = str(session.requirements)
                # This would need to be enhanced with actual extraction logic
                explicit_techs = generation_metrics.get('explicit_technologies', [])
            
            explicit_included = len([tech for tech in explicit_techs if tech in final_tech_stack])
            
            if hasattr(self.tech_stack_monitor, 'record_extraction_accuracy'):
                self.tech_stack_monitor.record_extraction_accuracy(
                    session_id=session.session_id,
                    extracted_count=len(final_tech_stack),
                    expected_count=generation_metrics.get('expected_count', len(final_tech_stack)),
                    explicit_tech_included=explicit_included,
                    explicit_tech_total=len(explicit_techs),
                    processing_time=total_duration
                )
                
        except Exception as e:
            self.logger.error(f"Error streaming completion metrics: {e}")
    
    async def _stream_to_tech_stack_monitor(self, event: MonitoringEvent) -> None:
        """Stream event to tech stack monitor."""
        # Implementation would depend on TechStackMonitor interface
        pass
    
    async def _stream_to_quality_assurance(self, event: MonitoringEvent) -> None:
        """Stream event to quality assurance system."""
        # Implementation would depend on QualityAssuranceSystem interface
        pass
    
    async def _stream_to_performance_analytics(self, event: MonitoringEvent) -> None:
        """Stream event to performance analytics."""
        try:
            if not self.performance_analytics:
                return
            
            # Convert monitoring event to analytics data
            if event.event_type.value in ['llm_call_complete', 'parsing_complete', 'extraction_complete', 'validation_complete']:
                # Track performance metrics
                await self.performance_analytics.track_performance_metric(
                    component=event.component,
                    operation=event.operation,
                    metric_name='response_time',
                    metric_value=(event.duration_ms or 0) / 1000.0,  # Convert to seconds
                    context={
                        'session_id': event.session_id,
                        'event_type': event.event_type.value,
                        'success': event.success,
                        **event.data
                    },
                    timestamp=event.timestamp
                )
                
                # Track success rate
                await self.performance_analytics.track_performance_metric(
                    component=event.component,
                    operation=event.operation,
                    metric_name='success_rate',
                    metric_value=1.0 if event.success else 0.0,
                    context={
                        'session_id': event.session_id,
                        'event_type': event.event_type.value,
                        'error_message': event.error_message,
                        **event.data
                    },
                    timestamp=event.timestamp
                )
            
            # Track user interactions
            if event.event_type.value in ['session_start', 'session_complete']:
                # Determine user segment (simplified logic)
                user_segment = 'returning_user'  # Default
                if event.data.get('metadata', {}).get('first_time_user'):
                    user_segment = 'new_user'
                elif event.data.get('metadata', {}).get('power_user'):
                    user_segment = 'power_user'
                
                await self.performance_analytics.track_user_interaction(
                    session_id=event.session_id,
                    user_segment=user_segment,
                    interaction_type=event.event_type.value,
                    interaction_data={
                        'component': event.component,
                        'operation': event.operation,
                        'duration_ms': event.duration_ms,
                        'success': event.success,
                        **event.data
                    },
                    timestamp=event.timestamp
                )
                
        except Exception as e:
            self.logger.error(f"Error streaming event to performance analytics: {e}")
    
    async def _cleanup_sessions_task(self) -> None:
        """Background task to clean up old sessions."""
        while self.is_running:
            try:
                await self._cleanup_old_sessions()
                await asyncio.sleep(self.config['cleanup_interval_minutes'] * 60)
            except Exception as e:
                self.logger.error(f"Error in session cleanup task: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def _cleanup_old_sessions(self) -> None:
        """Clean up old sessions and events."""
        cutoff_time = datetime.now() - timedelta(hours=self.config['max_session_duration_hours'])
        
        sessions_to_remove = []
        for session_id, session in list(self.active_sessions.items()):
            if session.start_time < cutoff_time:
                sessions_to_remove.append(session_id)
        
        for session_id in sessions_to_remove:
            session = self.active_sessions.pop(session_id, None)
            if session:
                # Complete session with timeout status
                session.end_time = datetime.now()
                session.status = "timeout"
                
                self.logger.info(f"Cleaned up timed-out session {session_id}")
            
            # Clean up session events
            self.session_events.pop(session_id, None)
    
    async def _real_time_streaming_task(self) -> None:
        """Background task for real-time event streaming."""
        while self.is_running:
            try:
                await self._flush_event_buffer()
                await asyncio.sleep(5)  # Stream every 5 seconds
            except Exception as e:
                self.logger.error(f"Error in real-time streaming task: {e}")
                await asyncio.sleep(10)  # Retry after 10 seconds on error
    
    async def _complete_active_sessions(self) -> None:
        """Complete all active sessions during shutdown."""
        for session_id, session in list(self.active_sessions.items()):
            try:
                await self.complete_generation_monitoring(
                    session_id=session_id,
                    final_tech_stack=[],
                    generation_metrics={'shutdown': True},
                    success=False,
                    error_message="Service shutdown"
                )
            except Exception as e:
                self.logger.error(f"Error completing session {session_id} during shutdown: {e}")
    
    def get_session_status(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get status of a monitoring session."""
        session = self.active_sessions.get(session_id)
        if not session:
            return None
        
        events = self.session_events.get(session_id, [])
        
        return {
            'session': session.to_dict(),
            'event_count': len(events),
            'latest_event': events[-1].to_dict() if events else None,
            'duration_seconds': (datetime.now() - session.start_time).total_seconds()
        }
    
    def get_active_sessions(self) -> List[Dict[str, Any]]:
        """Get all active monitoring sessions."""
        return [
            {
                'session_id': session_id,
                'correlation_id': session.correlation_id,
                'start_time': session.start_time.isoformat(),
                'status': session.status,
                'event_count': len(self.session_events.get(session_id, [])),
                'duration_seconds': (datetime.now() - session.start_time).total_seconds()
            }
            for session_id, session in self.active_sessions.items()
        ]
    
    def get_session_events(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all events for a session."""
        events = self.session_events.get(session_id, [])
        return [event.to_dict() for event in events]
    
    def get_service_metrics(self) -> Dict[str, Any]:
        """Get service-level metrics."""
        return {
            'active_sessions': len(self.active_sessions),
            'total_events_buffered': len(self.event_buffer),
            'is_running': self.is_running,
            'real_time_streaming_enabled': self.config['real_time_streaming'],
            'monitoring_components': {
                'tech_stack_monitor': bool(self.tech_stack_monitor),
                'quality_assurance': bool(self.quality_assurance),
                'performance_analytics': bool(self.performance_analytics)
            }
        }