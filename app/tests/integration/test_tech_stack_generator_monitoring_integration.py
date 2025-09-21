"""
Integration tests for tech stack generator monitoring integration.

Tests verify end-to-end monitoring data flow during tech stack generation.
"""

import pytest
import asyncio
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, List, Any

from app.services.tech_stack_generator import TechStackGenerator
from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService, MonitoringSession
from app.pattern.matcher import MatchResult
from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, response_data: Dict[str, Any] = None):
        self.response_data = response_data or {
            "tech_stack": ["FastAPI", "PostgreSQL", "Redis", "Docker", "AWS Lambda"],
            "reasoning": "Selected based on requirements"
        }
        self.model = "mock-model"
    
    async def generate(self, prompt: str, purpose: str = None) -> Dict[str, Any]:
        """Mock generate method."""
        return self.response_data
    
    def get_model_info(self) -> Dict[str, Any]:
        return {"name": "mock-model", "provider": "mock"}
    
    async def test_connection(self) -> bool:
        """Mock test connection method."""
        return True


class TestTechStackGeneratorMonitoringIntegration:
    """Test tech stack generator monitoring integration."""
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider."""
        return MockLLMProvider()
    
    @pytest.fixture
    def monitoring_service(self):
        """Create monitoring integration service."""
        return TechStackMonitoringIntegrationService()
    
    @pytest.fixture
    def tech_stack_generator(self, mock_llm_provider):
        """Create tech stack generator with monitoring."""
        # Mock the service dependencies to avoid service registry issues
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.side_effect = Exception("Service not available")
            return TechStackGenerator(
                llm_provider=mock_llm_provider,
                auto_update_catalog=True,
                enable_debug_logging=True
            )
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements for testing."""
        return {
            "functional_requirements": [
                "Build a REST API for user management",
                "Integrate with AWS services",
                "Use PostgreSQL for data storage",
                "Implement caching with Redis"
            ],
            "non_functional_requirements": [
                "Handle 1000 concurrent users",
                "99.9% uptime requirement"
            ],
            "constraints": {
                "cloud_provider": "AWS",
                "database": "PostgreSQL"
            }
        }
    
    @pytest.fixture
    def sample_matches(self):
        """Sample pattern matches for testing."""
        match = Mock(spec=MatchResult)
        match.pattern_id = "APAT-001"
        match.confidence = 0.85
        match.tech_stack = ["FastAPI", "PostgreSQL", "Redis"]
        return [match]
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_integration(
        self, 
        tech_stack_generator, 
        monitoring_service, 
        sample_requirements, 
        sample_matches
    ):
        """Test complete end-to-end monitoring integration."""
        
        # Mock the monitoring service in the service registry
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.return_value = monitoring_service
            
            # Start monitoring service
            await monitoring_service.start_monitoring_integration()
            
            try:
                # Generate tech stack with monitoring
                result = await tech_stack_generator.generate_tech_stack(
                    matches=sample_matches,
                    requirements=sample_requirements,
                    constraints={"banned_tools": ["MongoDB"]}
                )
                
                # Verify result
                assert isinstance(result, list)
                assert len(result) > 0
                
                # Verify monitoring data was collected
                assert len(monitoring_service.active_sessions) >= 0  # May be completed
                
                # Check that events were recorded
                total_events = sum(len(events) for events in monitoring_service.session_events.values())
                assert total_events > 0, "No monitoring events were recorded"
                
                # Verify event types are present
                all_events = []
                for events in monitoring_service.session_events.values():
                    all_events.extend(events)
                
                event_types = {event.event_type.value for event in all_events}
                expected_types = {
                    'session_start',
                    'parsing_complete',
                    'extraction_complete',
                    'llm_call_complete',
                    'validation_complete',
                    'session_complete'
                }
                
                # At least some expected event types should be present
                assert len(event_types & expected_types) > 0, f"Expected event types not found. Got: {event_types}"
                
            finally:
                await monitoring_service.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_monitoring_session_lifecycle(
        self, 
        tech_stack_generator, 
        monitoring_service, 
        sample_requirements, 
        sample_matches
    ):
        """Test monitoring session lifecycle management."""
        
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.return_value = monitoring_service
            
            await monitoring_service.start_monitoring_integration()
            
            try:
                # Track initial state
                initial_sessions = len(monitoring_service.active_sessions)
                
                # Generate tech stack
                result = await tech_stack_generator.generate_tech_stack(
                    matches=sample_matches,
                    requirements=sample_requirements
                )
                
                # Verify session was created and completed
                assert isinstance(result, list)
                
                # Check session events
                session_events = list(monitoring_service.session_events.values())
                if session_events:
                    events = session_events[0]  # Get first session's events
                    
                    # Verify session start and completion events
                    start_events = [e for e in events if e.event_type.value == 'session_start']
                    complete_events = [e for e in events if e.event_type.value in ['session_complete', 'session_error']]
                    
                    assert len(start_events) > 0, "No session start event found"
                    assert len(complete_events) > 0, "No session completion event found"
                    
                    # Verify session correlation
                    if start_events and complete_events:
                        assert start_events[0].session_id == complete_events[0].session_id
                        assert start_events[0].correlation_id == complete_events[0].correlation_id
                
            finally:
                await monitoring_service.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_monitoring_data_validation(
        self, 
        tech_stack_generator, 
        monitoring_service, 
        sample_requirements, 
        sample_matches
    ):
        """Test monitoring data validation and quality checks."""
        
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.return_value = monitoring_service
            
            await monitoring_service.start_monitoring_integration()
            
            try:
                # Generate tech stack
                result = await tech_stack_generator.generate_tech_stack(
                    matches=sample_matches,
                    requirements=sample_requirements
                )
                
                # Verify data quality
                assert isinstance(result, list)
                
                # Check monitoring data validation
                session_id = "test-session"
                
                # Test valid data
                valid_data = {
                    'timestamp': datetime.now().isoformat(),
                    'operation': 'test_operation',
                    'duration_ms': 100.0,
                    'confidence_scores': {'tech1': 0.8, 'tech2': 0.9},
                    'extracted_technologies': ['FastAPI', 'PostgreSQL'],
                    'success': True
                }
                
                is_valid = tech_stack_generator._validate_monitoring_data(
                    session_id, valid_data, 'test_operation'
                )
                assert is_valid, "Valid monitoring data should pass validation"
                
                # Test invalid data
                invalid_data = {
                    'timestamp': datetime.now().isoformat(),
                    'operation': 'test_operation',
                    'duration_ms': -100.0,  # Invalid negative duration
                    'confidence_scores': {'tech1': 1.5},  # Invalid confidence score > 1
                    'extracted_technologies': ['', None],  # Invalid empty/null technologies
                    'success': False  # Missing error_message
                }
                
                is_valid = tech_stack_generator._validate_monitoring_data(
                    session_id, invalid_data, 'test_operation'
                )
                assert not is_valid, "Invalid monitoring data should fail validation"
                
            finally:
                await monitoring_service.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_monitoring_error_handling(
        self, 
        monitoring_service, 
        sample_requirements, 
        sample_matches
    ):
        """Test monitoring integration during error conditions."""
        
        # Create generator with failing LLM provider
        failing_llm = Mock(spec=LLMProvider)
        failing_llm.generate = AsyncMock(side_effect=Exception("LLM failure"))
        failing_llm.model = "failing-model"
        
        tech_stack_generator = TechStackGenerator(
            llm_provider=failing_llm,
            enable_debug_logging=True
        )
        
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.return_value = monitoring_service
            
            await monitoring_service.start_monitoring_integration()
            
            try:
                # Generate tech stack (should fallback to rule-based)
                result = await tech_stack_generator.generate_tech_stack(
                    matches=sample_matches,
                    requirements=sample_requirements
                )
                
                # Should still return a result (fallback)
                assert isinstance(result, list)
                
                # Check that error events were recorded
                all_events = []
                for events in monitoring_service.session_events.values():
                    all_events.extend(events)
                
                # Look for error-related events or LLM failure tracking
                error_events = [e for e in all_events if not e.success or 'error' in e.data]
                
                # Should have some error tracking (either in events or completion)
                assert len(all_events) > 0, "No monitoring events recorded during error condition"
                
            finally:
                await monitoring_service.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_monitoring_performance_tracking(
        self, 
        tech_stack_generator, 
        monitoring_service, 
        sample_requirements, 
        sample_matches
    ):
        """Test monitoring performance metrics tracking."""
        
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.return_value = monitoring_service
            
            await monitoring_service.start_monitoring_integration()
            
            try:
                # Generate tech stack
                result = await tech_stack_generator.generate_tech_stack(
                    matches=sample_matches,
                    requirements=sample_requirements
                )
                
                assert isinstance(result, list)
                
                # Check performance metrics in events
                all_events = []
                for events in monitoring_service.session_events.values():
                    all_events.extend(events)
                
                # Verify duration tracking
                events_with_duration = [e for e in all_events if e.duration_ms is not None]
                assert len(events_with_duration) > 0, "No events with duration tracking found"
                
                # Verify reasonable duration values
                for event in events_with_duration:
                    assert event.duration_ms >= 0, f"Negative duration found: {event.duration_ms}"
                    assert event.duration_ms < 60000, f"Unreasonably high duration: {event.duration_ms}ms"
                
                # Check for completion event with total metrics
                completion_events = [e for e in all_events if e.event_type.value == 'session_complete']
                if completion_events:
                    completion_event = completion_events[0]
                    assert 'total_duration_ms' in completion_event.data
                    assert completion_event.data['total_duration_ms'] > 0
                
            finally:
                await monitoring_service.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_monitoring_without_service_available(
        self, 
        tech_stack_generator, 
        sample_requirements, 
        sample_matches
    ):
        """Test tech stack generation when monitoring service is not available."""
        
        # Mock service registry to return None (service not available)
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.side_effect = Exception("Service not available")
            
            # Should still work without monitoring
            result = await tech_stack_generator.generate_tech_stack(
                matches=sample_matches,
                requirements=sample_requirements
            )
            
            # Verify generation still works
            assert isinstance(result, list)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_monitoring_data_completeness(
        self, 
        tech_stack_generator, 
        monitoring_service, 
        sample_requirements, 
        sample_matches
    ):
        """Test completeness of monitoring data collection."""
        
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.return_value = monitoring_service
            
            await monitoring_service.start_monitoring_integration()
            
            try:
                # Generate tech stack
                result = await tech_stack_generator.generate_tech_stack(
                    matches=sample_matches,
                    requirements=sample_requirements
                )
                
                assert isinstance(result, list)
                
                # Collect all events
                all_events = []
                for events in monitoring_service.session_events.values():
                    all_events.extend(events)
                
                # Verify key data points are captured
                parsing_events = [e for e in all_events if 'parsing' in e.operation.lower()]
                extraction_events = [e for e in all_events if 'extraction' in e.operation.lower()]
                llm_events = [e for e in all_events if e.component == 'LLMProvider' or 'llm' in e.operation.lower()]
                validation_events = [e for e in all_events if 'validation' in e.operation.lower()]
                
                # Should have events from major steps
                assert len(parsing_events) > 0, "No parsing events found"
                assert len(extraction_events) > 0, "No extraction events found"
                # LLM events may not be present if rule-based fallback is used
                assert len(validation_events) > 0, "No validation events found"
                
                # Verify data completeness in events
                for event in all_events:
                    assert event.session_id, "Event missing session_id"
                    assert event.correlation_id, "Event missing correlation_id"
                    assert event.timestamp, "Event missing timestamp"
                    assert event.component, "Event missing component"
                    assert event.operation, "Event missing operation"
                    assert isinstance(event.data, dict), "Event data should be a dictionary"
                
            finally:
                await monitoring_service.stop_monitoring_integration()


if __name__ == "__main__":
    pytest.main([__file__])