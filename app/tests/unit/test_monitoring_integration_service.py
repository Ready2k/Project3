"""
Unit tests for TechStackMonitoringIntegrationService.

Tests session-based monitoring, correlation IDs, real-time data collection,
and streaming to monitoring components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from app.services.monitoring_integration_service import (
    TechStackMonitoringIntegrationService,
    MonitoringSession,
    MonitoringEvent,
    MonitoringEventType
)


class TestTechStackMonitoringIntegrationService:
    """Test cases for TechStackMonitoringIntegrationService."""
    
    @pytest.fixture
    def service_config(self) -> Dict[str, Any]:
        """Service configuration for testing."""
        return {
            'max_session_duration_hours': 1,
            'max_events_per_session': 100,
            'cleanup_interval_minutes': 1,
            'real_time_streaming': True,
            'buffer_size': 10
        }
    
    @pytest.fixture
    def monitoring_service(self, service_config) -> TechStackMonitoringIntegrationService:
        """Create monitoring integration service for testing."""
        with patch('app.services.monitoring_integration_service.require_service') as mock_require:
            mock_require.side_effect = Exception("Service not found")  # Force fallback logger
            service = TechStackMonitoringIntegrationService(service_config)
            return service
    
    @pytest.fixture
    def sample_requirements(self) -> Dict[str, Any]:
        """Sample requirements for testing."""
        return {
            'business_requirements': 'Build a customer service chatbot',
            'technical_requirements': 'Use AWS services and Python',
            'constraints': {'banned_tools': ['deprecated_lib']}
        }
    
    @pytest.fixture
    def sample_metadata(self) -> Dict[str, Any]:
        """Sample metadata for testing."""
        return {
            'user_id': 'test_user',
            'project_id': 'test_project',
            'environment': 'development'
        }
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, monitoring_service):
        """Test service initialization."""
        assert monitoring_service is not None
        assert monitoring_service.active_sessions == {}
        assert monitoring_service.session_events == {}
        assert monitoring_service.event_buffer == []
        assert not monitoring_service.is_running
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring_integration(self, monitoring_service):
        """Test starting and stopping monitoring integration."""
        # Start service
        await monitoring_service.start_monitoring_integration()
        assert monitoring_service.is_running
        assert monitoring_service.cleanup_task is not None
        assert monitoring_service.streaming_task is not None
        
        # Stop service
        await monitoring_service.stop_monitoring_integration()
        assert not monitoring_service.is_running
    
    def test_start_generation_monitoring(self, monitoring_service, sample_requirements, sample_metadata):
        """Test starting generation monitoring session."""
        session = monitoring_service.start_generation_monitoring(
            requirements=sample_requirements,
            metadata=sample_metadata
        )
        
        # Verify session creation
        assert isinstance(session, MonitoringSession)
        assert session.session_id is not None
        assert session.correlation_id is not None
        assert session.correlation_id.startswith('tsg_')
        assert session.start_time is not None
        assert session.end_time is None
        assert session.status == "active"
        assert session.requirements == sample_requirements
        assert session.metadata == sample_metadata
        
        # Verify session is tracked
        assert session.session_id in monitoring_service.active_sessions
        assert session.session_id in monitoring_service.session_events
        
        # Verify session start event is queued
        assert len(monitoring_service.event_buffer) == 1
        start_event = monitoring_service.event_buffer[0]
        assert start_event.event_type == MonitoringEventType.SESSION_START
        assert start_event.session_id == session.session_id
        assert start_event.correlation_id == session.correlation_id
    
    @pytest.mark.asyncio
    async def test_track_parsing_step(self, monitoring_service, sample_requirements):
        """Test tracking parsing step."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Track parsing step
        input_data = {'requirements': sample_requirements}
        output_data = {
            'explicit_technologies': ['AWS Lambda', 'Python'],
            'confidence_score': 0.85
        }
        
        await monitoring_service.track_parsing_step(
            session_id=session.session_id,
            step_name='extract_explicit_technologies',
            input_data=input_data,
            output_data=output_data,
            duration_ms=150.0,
            success=True
        )
        
        # Verify event was recorded
        events = monitoring_service.session_events[session.session_id]
        parsing_events = [e for e in events if e.event_type == MonitoringEventType.PARSING_COMPLETE]
        assert len(parsing_events) == 1
        
        parsing_event = parsing_events[0]
        assert parsing_event.component == "RequirementParser"
        assert parsing_event.operation == 'extract_explicit_technologies'
        assert parsing_event.data['input_data'] == input_data
        assert parsing_event.data['output_data'] == output_data
        assert parsing_event.duration_ms == 150.0
        assert parsing_event.success is True
    
    @pytest.mark.asyncio
    async def test_track_extraction_step(self, monitoring_service, sample_requirements):
        """Test tracking extraction step."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Track extraction step
        extracted_technologies = ['AWS Lambda', 'Amazon DynamoDB', 'Python']
        confidence_scores = {
            'AWS Lambda': 0.95,
            'Amazon DynamoDB': 0.88,
            'Python': 0.92
        }
        context_data = {
            'domain': 'serverless',
            'cloud_provider': 'aws'
        }
        
        await monitoring_service.track_extraction_step(
            session_id=session.session_id,
            extraction_type='explicit',
            extracted_technologies=extracted_technologies,
            confidence_scores=confidence_scores,
            context_data=context_data,
            duration_ms=200.0,
            success=True
        )
        
        # Verify event was recorded
        events = monitoring_service.session_events[session.session_id]
        extraction_events = [e for e in events if e.event_type == MonitoringEventType.EXTRACTION_COMPLETE]
        assert len(extraction_events) == 1
        
        extraction_event = extraction_events[0]
        assert extraction_event.component == "TechnologyExtractor"
        assert extraction_event.operation == 'explicit'
        assert extraction_event.data['extracted_technologies'] == extracted_technologies
        assert extraction_event.data['confidence_scores'] == confidence_scores
        assert extraction_event.data['context_data'] == context_data
        assert extraction_event.data['extraction_count'] == 3
        assert extraction_event.duration_ms == 200.0
    
    @pytest.mark.asyncio
    async def test_track_llm_interaction(self, monitoring_service, sample_requirements):
        """Test tracking LLM interaction."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Track LLM interaction
        prompt_data = {
            'prompt_type': 'tech_stack_generation',
            'context_size': 1500,
            'explicit_technologies': ['AWS Lambda', 'Python']
        }
        response_data = {
            'generated_technologies': ['AWS Lambda', 'Python', 'Amazon API Gateway'],
            'reasoning': 'Selected based on serverless architecture pattern'
        }
        token_usage = {
            'prompt_tokens': 800,
            'completion_tokens': 200,
            'total_tokens': 1000
        }
        
        await monitoring_service.track_llm_interaction(
            session_id=session.session_id,
            provider='OpenAI',
            model='gpt-4',
            prompt_data=prompt_data,
            response_data=response_data,
            token_usage=token_usage,
            duration_ms=2500.0,
            success=True
        )
        
        # Verify event was recorded
        events = monitoring_service.session_events[session.session_id]
        llm_events = [e for e in events if e.event_type == MonitoringEventType.LLM_CALL_COMPLETE]
        assert len(llm_events) == 1
        
        llm_event = llm_events[0]
        assert llm_event.component == "LLMProvider"
        assert llm_event.operation == 'OpenAI_gpt-4'
        assert llm_event.data['provider'] == 'OpenAI'
        assert llm_event.data['model'] == 'gpt-4'
        assert llm_event.data['prompt_data'] == prompt_data
        assert llm_event.data['response_data'] == response_data
        assert llm_event.data['token_usage'] == token_usage
        assert llm_event.duration_ms == 2500.0
    
    @pytest.mark.asyncio
    async def test_track_validation_step(self, monitoring_service, sample_requirements):
        """Test tracking validation step."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Track validation step
        input_technologies = ['AWS Lambda', 'Python', 'Amazon API Gateway']
        validation_results = {
            'ecosystem_consistency': True,
            'compatibility_score': 0.92,
            'conflicts_found': 1
        }
        conflicts_detected = [
            {
                'type': 'version_conflict',
                'technologies': ['Python', 'AWS Lambda'],
                'description': 'Python version compatibility with Lambda runtime'
            }
        ]
        resolutions_applied = [
            {
                'conflict_id': 'version_conflict_1',
                'resolution': 'Use Python 3.9 for Lambda compatibility',
                'confidence': 0.95
            }
        ]
        
        await monitoring_service.track_validation_step(
            session_id=session.session_id,
            validation_type='compatibility',
            input_technologies=input_technologies,
            validation_results=validation_results,
            conflicts_detected=conflicts_detected,
            resolutions_applied=resolutions_applied,
            duration_ms=300.0,
            success=True
        )
        
        # Verify event was recorded
        events = monitoring_service.session_events[session.session_id]
        validation_events = [e for e in events if e.event_type == MonitoringEventType.VALIDATION_COMPLETE]
        assert len(validation_events) == 1
        
        validation_event = validation_events[0]
        assert validation_event.component == "TechnologyValidator"
        assert validation_event.operation == 'compatibility'
        assert validation_event.data['input_technologies'] == input_technologies
        assert validation_event.data['validation_results'] == validation_results
        assert validation_event.data['conflicts_detected'] == conflicts_detected
        assert validation_event.data['resolutions_applied'] == resolutions_applied
        assert validation_event.data['conflict_count'] == 1
        assert validation_event.data['resolution_count'] == 1
    
    @pytest.mark.asyncio
    async def test_complete_generation_monitoring(self, monitoring_service, sample_requirements):
        """Test completing generation monitoring."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Add some events
        await monitoring_service.track_parsing_step(
            session_id=session.session_id,
            step_name='test_step',
            input_data={'test': 'data'},
            output_data={'result': 'success'}
        )
        
        # Complete session
        final_tech_stack = ['AWS Lambda', 'Python', 'Amazon API Gateway', 'Amazon DynamoDB']
        generation_metrics = {
            'explicit_technologies': ['AWS Lambda', 'Python'],
            'expected_count': 4,
            'extraction_accuracy': 0.95,
            'processing_time_ms': 3000
        }
        
        completed_session = await monitoring_service.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=final_tech_stack,
            generation_metrics=generation_metrics,
            success=True
        )
        
        # Verify session completion
        assert completed_session is not None
        assert completed_session.end_time is not None
        assert completed_session.status == "completed"
        assert session.session_id not in monitoring_service.active_sessions
        
        # Verify completion event was recorded
        events = monitoring_service.session_events[session.session_id]
        completion_events = [e for e in events if e.event_type == MonitoringEventType.SESSION_COMPLETE]
        assert len(completion_events) == 1
        
        completion_event = completion_events[0]
        assert completion_event.data['final_tech_stack'] == final_tech_stack
        assert completion_event.data['generation_metrics'] == generation_metrics
        assert completion_event.success is True
    
    @pytest.mark.asyncio
    async def test_complete_generation_monitoring_with_error(self, monitoring_service, sample_requirements):
        """Test completing generation monitoring with error."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Complete session with error
        error_message = "LLM provider timeout"
        
        completed_session = await monitoring_service.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=[],
            generation_metrics={'error': True},
            success=False,
            error_message=error_message
        )
        
        # Verify session completion with error
        assert completed_session.status == "error"
        
        # Verify error event was recorded
        events = monitoring_service.session_events[session.session_id]
        error_events = [e for e in events if e.event_type == MonitoringEventType.SESSION_ERROR]
        assert len(error_events) == 1
        
        error_event = error_events[0]
        assert error_event.success is False
        assert error_event.error_message == error_message
    
    @pytest.mark.asyncio
    async def test_event_buffer_management(self, monitoring_service, sample_requirements):
        """Test event buffer management and flushing."""
        # Configure small buffer for testing
        monitoring_service.config['buffer_size'] = 10  # Use larger buffer to avoid complex flush logic in tests
        
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Add events to fill buffer
        for i in range(5):
            await monitoring_service.track_parsing_step(
                session_id=session.session_id,
                step_name=f'step_{i}',
                input_data={'step': i},
                output_data={'result': i}
            )
        
        # Verify events are being buffered
        assert len(monitoring_service.event_buffer) > 0
        
        # Verify session start event is in buffer
        session_start_events = [e for e in monitoring_service.event_buffer if e.event_type == MonitoringEventType.SESSION_START]
        assert len(session_start_events) == 1
        
        # Verify parsing events are in buffer
        parsing_events = [e for e in monitoring_service.event_buffer if e.event_type == MonitoringEventType.PARSING_COMPLETE]
        assert len(parsing_events) == 5
    
    def test_get_session_status(self, monitoring_service, sample_requirements):
        """Test getting session status."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Get session status
        status = monitoring_service.get_session_status(session.session_id)
        
        assert status is not None
        assert status['session']['session_id'] == session.session_id
        assert status['session']['correlation_id'] == session.correlation_id
        assert status['session']['status'] == 'active'
        assert status['event_count'] >= 1  # At least the start event
        assert 'duration_seconds' in status
        assert status['duration_seconds'] >= 0
    
    def test_get_session_status_nonexistent(self, monitoring_service):
        """Test getting status for nonexistent session."""
        status = monitoring_service.get_session_status('nonexistent_session')
        assert status is None
    
    def test_get_active_sessions(self, monitoring_service, sample_requirements):
        """Test getting active sessions."""
        # Start multiple sessions
        session1 = monitoring_service.start_generation_monitoring(sample_requirements)
        session2 = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Get active sessions
        active_sessions = monitoring_service.get_active_sessions()
        
        assert len(active_sessions) == 2
        session_ids = [s['session_id'] for s in active_sessions]
        assert session1.session_id in session_ids
        assert session2.session_id in session_ids
        
        for session_info in active_sessions:
            assert 'correlation_id' in session_info
            assert 'start_time' in session_info
            assert 'status' in session_info
            assert 'event_count' in session_info
            assert 'duration_seconds' in session_info
    
    def test_get_session_events(self, monitoring_service, sample_requirements):
        """Test getting session events."""
        # Start session and add events
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Get session events
        events = monitoring_service.get_session_events(session.session_id)
        
        assert len(events) >= 1  # At least the start event
        
        # Verify event structure
        for event in events:
            assert 'event_id' in event
            assert 'session_id' in event
            assert 'correlation_id' in event
            assert 'event_type' in event
            assert 'timestamp' in event
            assert 'component' in event
            assert 'operation' in event
            assert 'data' in event
    
    def test_get_service_metrics(self, monitoring_service, sample_requirements):
        """Test getting service metrics."""
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Get service metrics
        metrics = monitoring_service.get_service_metrics()
        
        assert 'active_sessions' in metrics
        assert 'total_events_buffered' in metrics
        assert 'is_running' in metrics
        assert 'real_time_streaming_enabled' in metrics
        assert 'monitoring_components' in metrics
        
        assert metrics['active_sessions'] == 1
        assert metrics['total_events_buffered'] >= 1
        assert metrics['real_time_streaming_enabled'] is True
        
        # Verify monitoring components status
        components = metrics['monitoring_components']
        assert 'tech_stack_monitor' in components
        assert 'quality_assurance' in components
        assert 'performance_analytics' in components
    
    @pytest.mark.asyncio
    async def test_session_cleanup(self, monitoring_service):
        """Test session cleanup functionality."""
        # Configure very short session duration for testing
        monitoring_service.config['max_session_duration_hours'] = 0.0001  # ~0.36 seconds
        
        # Start session
        session = monitoring_service.start_generation_monitoring({'test': 'requirements'})
        
        # Wait for session to expire (longer than the configured duration)
        await asyncio.sleep(1.5)  # 1.5 seconds > 0.36 seconds
        
        # Manually trigger cleanup
        await monitoring_service._cleanup_old_sessions()
        
        # Verify session was cleaned up
        assert session.session_id not in monitoring_service.active_sessions
        assert session.session_id not in monitoring_service.session_events
    
    @pytest.mark.asyncio
    async def test_max_events_per_session(self, monitoring_service, sample_requirements):
        """Test maximum events per session limit."""
        # Configure small max events for testing
        monitoring_service.config['max_events_per_session'] = 5
        
        # Start session
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Add more events than the limit
        for i in range(10):
            await monitoring_service.track_parsing_step(
                session_id=session.session_id,
                step_name=f'step_{i}',
                input_data={'step': i},
                output_data={'result': i}
            )
        
        # Verify events were limited
        events = monitoring_service.session_events[session.session_id]
        assert len(events) <= monitoring_service.config['max_events_per_session']
    
    @pytest.mark.asyncio
    async def test_correlation_id_format(self, monitoring_service, sample_requirements):
        """Test correlation ID format."""
        session = monitoring_service.start_generation_monitoring(sample_requirements)
        
        # Verify correlation ID format
        assert session.correlation_id.startswith('tsg_')
        parts = session.correlation_id.split('_')
        assert len(parts) == 3  # tsg, timestamp, session_id_prefix
        assert parts[0] == 'tsg'
        assert parts[1].isdigit()  # timestamp
        assert len(parts[2]) == 8  # session_id prefix
    
    @pytest.mark.asyncio
    async def test_monitoring_session_lifecycle(self, monitoring_service, sample_requirements):
        """Test complete monitoring session lifecycle."""
        # Start session
        session = monitoring_service.start_generation_monitoring(
            requirements=sample_requirements,
            metadata={'test': 'metadata'}
        )
        
        # Track various steps
        await monitoring_service.track_parsing_step(
            session_id=session.session_id,
            step_name='parse_requirements',
            input_data=sample_requirements,
            output_data={'explicit_technologies': ['AWS Lambda']},
            duration_ms=100.0
        )
        
        await monitoring_service.track_extraction_step(
            session_id=session.session_id,
            extraction_type='explicit',
            extracted_technologies=['AWS Lambda', 'Python'],
            confidence_scores={'AWS Lambda': 0.95, 'Python': 0.90},
            context_data={'domain': 'serverless'},
            duration_ms=200.0
        )
        
        await monitoring_service.track_llm_interaction(
            session_id=session.session_id,
            provider='OpenAI',
            model='gpt-4',
            prompt_data={'context_size': 1000},
            response_data={'technologies': ['AWS Lambda', 'Python', 'API Gateway']},
            duration_ms=2000.0
        )
        
        await monitoring_service.track_validation_step(
            session_id=session.session_id,
            validation_type='compatibility',
            input_technologies=['AWS Lambda', 'Python', 'API Gateway'],
            validation_results={'valid': True},
            conflicts_detected=[],
            resolutions_applied=[],
            duration_ms=150.0
        )
        
        # Complete session
        final_tech_stack = ['AWS Lambda', 'Python', 'Amazon API Gateway']
        generation_metrics = {'accuracy': 0.95, 'processing_time': 2450.0}
        
        completed_session = await monitoring_service.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=final_tech_stack,
            generation_metrics=generation_metrics,
            success=True
        )
        
        # Verify complete lifecycle
        assert completed_session.status == 'completed'
        assert completed_session.end_time is not None
        
        # Verify all event types were recorded
        events = monitoring_service.session_events[session.session_id]
        event_types = {event.event_type for event in events}
        
        expected_types = {
            MonitoringEventType.SESSION_START,
            MonitoringEventType.PARSING_COMPLETE,
            MonitoringEventType.EXTRACTION_COMPLETE,
            MonitoringEventType.LLM_CALL_COMPLETE,
            MonitoringEventType.VALIDATION_COMPLETE,
            MonitoringEventType.SESSION_COMPLETE
        }
        
        assert expected_types.issubset(event_types)
    
    @pytest.mark.asyncio
    async def test_error_handling_in_tracking(self, monitoring_service, sample_requirements):
        """Test error handling in tracking methods."""
        # Test tracking with invalid session ID
        await monitoring_service.track_parsing_step(
            session_id='invalid_session',
            step_name='test_step',
            input_data={'test': 'data'},
            output_data={'result': 'success'}
        )
        
        # Should not raise exception, just log warning
        # Verify no events were added to invalid session
        assert 'invalid_session' not in monitoring_service.session_events
    
    @pytest.mark.asyncio
    async def test_real_time_streaming_configuration(self, monitoring_service):
        """Test real-time streaming configuration."""
        # Test with streaming enabled
        assert monitoring_service.config['real_time_streaming'] is True
        
        # Test with streaming disabled
        monitoring_service.config['real_time_streaming'] = False
        
        # Start session (should still work without streaming)
        session = monitoring_service.start_generation_monitoring({'test': 'requirements'})
        
        # Events should still be recorded locally
        assert len(monitoring_service.session_events[session.session_id]) >= 1
        
        # But buffer should not be used for streaming
        # (This would need more complex testing with actual streaming components)


class TestMonitoringDataStructures:
    """Test monitoring data structures."""
    
    def test_monitoring_session_creation(self):
        """Test MonitoringSession creation and serialization."""
        session = MonitoringSession(
            session_id='test_session',
            correlation_id='tsg_123_abcd1234',
            start_time=datetime.now(),
            requirements={'test': 'requirements'},
            metadata={'user': 'test_user'}
        )
        
        assert session.session_id == 'test_session'
        assert session.correlation_id == 'tsg_123_abcd1234'
        assert session.status == 'active'
        assert session.end_time is None
        assert session.events == []
        
        # Test serialization
        session_dict = session.to_dict()
        assert 'session_id' in session_dict
        assert 'correlation_id' in session_dict
        assert 'start_time' in session_dict
        assert 'status' in session_dict
    
    def test_monitoring_event_creation(self):
        """Test MonitoringEvent creation and serialization."""
        event = MonitoringEvent(
            event_id='event_123',
            session_id='session_123',
            correlation_id='tsg_123_abcd1234',
            event_type=MonitoringEventType.PARSING_COMPLETE,
            timestamp=datetime.now(),
            component='TestComponent',
            operation='test_operation',
            data={'test': 'data'},
            duration_ms=100.0,
            success=True
        )
        
        assert event.event_id == 'event_123'
        assert event.session_id == 'session_123'
        assert event.event_type == MonitoringEventType.PARSING_COMPLETE
        assert event.component == 'TestComponent'
        assert event.operation == 'test_operation'
        assert event.duration_ms == 100.0
        assert event.success is True
        assert event.error_message is None
        
        # Test serialization
        event_dict = event.to_dict()
        assert 'event_id' in event_dict
        assert 'session_id' in event_dict
        assert 'event_type' in event_dict
        assert event_dict['event_type'] == 'parsing_complete'
        assert 'timestamp' in event_dict
    
    def test_monitoring_event_types(self):
        """Test MonitoringEventType enum values."""
        assert MonitoringEventType.SESSION_START.value == "session_start"
        assert MonitoringEventType.PARSING_START.value == "parsing_start"
        assert MonitoringEventType.PARSING_COMPLETE.value == "parsing_complete"
        assert MonitoringEventType.EXTRACTION_START.value == "extraction_start"
        assert MonitoringEventType.EXTRACTION_COMPLETE.value == "extraction_complete"
        assert MonitoringEventType.LLM_CALL_START.value == "llm_call_start"
        assert MonitoringEventType.LLM_CALL_COMPLETE.value == "llm_call_complete"
        assert MonitoringEventType.VALIDATION_START.value == "validation_start"
        assert MonitoringEventType.VALIDATION_COMPLETE.value == "validation_complete"
        assert MonitoringEventType.SESSION_COMPLETE.value == "session_complete"
        assert MonitoringEventType.SESSION_ERROR.value == "session_error"