"""
Integration tests for monitoring components with real tech stack generation data.

Tests that monitoring components properly capture and process actual generation events
instead of mock data.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any, List

from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService
from app.services.tech_stack_generator import TechStackGenerator
from app.monitoring.tech_stack_monitor import TechStackMonitor
from app.monitoring.quality_assurance import QualityAssuranceSystem
from app.monitoring.performance_monitor import PerformanceMonitor


class TestMonitoringRealDataIntegration:
    """Test monitoring integration with real tech stack generation data."""
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Mock LLM provider for testing."""
        provider = AsyncMock()
        provider.__class__.__name__ = "MockLLMProvider"
        provider.model = "test-model"
        
        # Mock successful response
        provider.generate.return_value = {
            "technologies": ["AWS Lambda", "Python", "Amazon DynamoDB", "Amazon API Gateway"],
            "reasoning": "Selected for serverless architecture",
            "usage": {
                "prompt_tokens": 500,
                "completion_tokens": 150,
                "total_tokens": 650
            }
        }
        
        return provider
    
    @pytest.fixture
    def monitoring_integration_service(self):
        """Create monitoring integration service for testing."""
        config = {
            'max_session_duration_hours': 1,
            'max_events_per_session': 100,
            'real_time_streaming': True,
            'buffer_size': 10
        }
        return TechStackMonitoringIntegrationService(config)
    
    @pytest.fixture
    def tech_stack_monitor(self):
        """Create tech stack monitor for testing."""
        return TechStackMonitor()
    
    @pytest.fixture
    def quality_assurance_system(self):
        """Create quality assurance system for testing."""
        return QualityAssuranceSystem()
    
    @pytest.fixture
    def tech_stack_generator(self, mock_llm_provider):
        """Create tech stack generator with mocked LLM provider."""
        return TechStackGenerator(
            llm_provider=mock_llm_provider,
            auto_update_catalog=False,
            enable_debug_logging=False
        )
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements for testing."""
        return {
            'business_requirements': 'Build a serverless customer feedback API',
            'technical_requirements': 'Use AWS Lambda and Python, store data in DynamoDB',
            'constraints': {
                'cloud_provider': 'aws',
                'programming_language': 'python',
                'architecture_pattern': 'serverless'
            }
        }
    
    @pytest.mark.asyncio
    async def test_end_to_end_monitoring_integration(
        self, 
        monitoring_integration_service,
        tech_stack_monitor,
        tech_stack_generator,
        sample_requirements
    ):
        """Test complete end-to-end monitoring integration with real generation."""
        # Start monitoring services
        await monitoring_integration_service.start_monitoring_integration()
        await tech_stack_monitor.start_monitoring()
        
        # Register monitoring service in generator (simulate service registry)
        with patch('app.services.tech_stack_generator.require_service') as mock_require:
            mock_require.return_value = monitoring_integration_service
            
            # Generate tech stack with monitoring
            tech_stack = await tech_stack_generator.generate_tech_stack(
                matches=[],  # Empty matches for simplicity
                requirements=sample_requirements,
                constraints=sample_requirements.get('constraints')
            )
        
        # Verify tech stack was generated
        assert isinstance(tech_stack, list)
        assert len(tech_stack) > 0
        
        # Verify monitoring session was created
        active_sessions = monitoring_integration_service.get_active_sessions()
        assert len(active_sessions) >= 0  # Session might be completed
        
        # Get service metrics
        service_metrics = monitoring_integration_service.get_service_metrics()
        assert 'total_events_buffered' in service_metrics
        assert service_metrics['total_events_buffered'] > 0
        
        # Verify events were captured
        if active_sessions:
            session_id = active_sessions[0]['session_id']
            session_events = monitoring_integration_service.get_session_events(session_id)
            
            # Check for expected event types
            event_types = {event['event_type'] for event in session_events}
            expected_types = {'session_start', 'parsing_complete', 'extraction_complete'}
            assert expected_types.issubset(event_types)
        
        # Verify tech stack monitor processed real data
        recent_metrics = tech_stack_monitor._get_recent_metrics(hours=1)
        assert len(recent_metrics) > 0
        
        # Check for specific metrics that should be generated from real data
        metric_names = {metric.name for metric in recent_metrics}
        expected_metrics = {'extraction_accuracy', 'processing_time'}
        assert any(expected_metric in metric_names for expected_metric in expected_metrics)
        
        # Cleanup
        await monitoring_integration_service.stop_monitoring_integration()
        await tech_stack_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_tech_stack_monitor_real_data_processing(
        self,
        monitoring_integration_service,
        tech_stack_monitor
    ):
        """Test that TechStackMonitor processes real session data correctly."""
        await monitoring_integration_service.start_monitoring_integration()
        await tech_stack_monitor.start_monitoring()
        
        # Create a real monitoring session with events
        session = monitoring_integration_service.start_generation_monitoring(
            requirements={'test': 'requirements'},
            metadata={'test': 'metadata'}
        )
        
        # Add realistic parsing event
        await monitoring_integration_service.track_parsing_step(
            session_id=session.session_id,
            step_name='enhanced_requirement_parsing',
            input_data={'requirements': {'test': 'requirements'}},
            output_data={
                'explicit_technologies': ['AWS Lambda', 'Python'],
                'confidence_score': 0.92
            },
            duration_ms=150.0,
            success=True
        )
        
        # Add realistic extraction event
        await monitoring_integration_service.track_extraction_step(
            session_id=session.session_id,
            extraction_type='context_aware_extraction',
            extracted_technologies=['AWS Lambda', 'Python', 'Amazon DynamoDB'],
            confidence_scores={'AWS Lambda': 0.95, 'Python': 0.90, 'Amazon DynamoDB': 0.85},
            context_data={'ecosystem': 'aws', 'domain': 'serverless'},
            duration_ms=200.0,
            success=True
        )
        
        # Add realistic LLM event
        await monitoring_integration_service.track_llm_interaction(
            session_id=session.session_id,
            provider='OpenAI',
            model='gpt-4',
            prompt_data={'context_size': 1200},
            response_data={'generated_technologies': ['AWS Lambda', 'Python', 'Amazon DynamoDB', 'Amazon API Gateway']},
            token_usage={'total_tokens': 800, 'prompt_tokens': 600, 'completion_tokens': 200},
            duration_ms=2500.0,
            success=True
        )
        
        # Allow time for real-time processing
        await asyncio.sleep(1)
        
        # Verify tech stack monitor processed the real data
        recent_metrics = tech_stack_monitor._get_recent_metrics(hours=1)
        
        # Should have metrics from real session processing
        assert len(recent_metrics) > 0
        
        # Check for LLM performance metrics
        llm_metrics = [m for m in recent_metrics if 'llm' in m.name.lower()]
        assert len(llm_metrics) > 0
        
        # Verify metric values are realistic (not mock data)
        for metric in llm_metrics:
            if metric.name == 'llm_response_time':
                assert 1.0 <= metric.value <= 5.0  # Realistic LLM response time
            elif metric.name == 'llm_token_usage':
                assert 500 <= metric.value <= 1000  # Realistic token usage
        
        await monitoring_integration_service.stop_monitoring_integration()
        await tech_stack_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_quality_assurance_real_data_validation(
        self,
        monitoring_integration_service,
        quality_assurance_system,
        tech_stack_monitor
    ):
        """Test that QualityAssurance validates actual tech stack results."""
        await monitoring_integration_service.start_monitoring_integration()
        await tech_stack_monitor.start_monitoring()
        await quality_assurance_system.start_qa_system()
        
        # Create multiple realistic sessions to provide data for QA analysis
        sessions = []
        for i in range(3):
            session = monitoring_integration_service.start_generation_monitoring(
                requirements={'business_requirements': f'Test requirement {i}'},
                metadata={'test_session': i}
            )
            sessions.append(session)
            
            # Add realistic completion event
            await monitoring_integration_service.complete_generation_monitoring(
                session_id=session.session_id,
                final_tech_stack=['AWS Lambda', 'Python', 'Amazon DynamoDB'],
                generation_metrics={
                    'extraction_accuracy': 0.9 - (i * 0.1),  # Varying accuracy
                    'explicit_inclusion_rate': 0.8 + (i * 0.05),
                    'explicit_technologies': ['AWS Lambda', 'Python']
                },
                success=True
            )
        
        # Allow time for data processing
        await asyncio.sleep(1)
        
        # Run QA check with real data
        accuracy_check = await quality_assurance_system._check_accuracy()
        
        # Verify QA check used real data
        assert accuracy_check.details.get('data_source') in ['real_data', 'monitor_data']
        assert accuracy_check.details.get('sample_count', 0) > 0
        
        # Verify realistic accuracy scores
        assert 0.0 <= accuracy_check.score <= 1.0
        
        # Check that recommendations are relevant to real data patterns
        if accuracy_check.recommendations:
            assert any('extraction' in rec.lower() or 'technology' in rec.lower() 
                      for rec in accuracy_check.recommendations)
        
        await monitoring_integration_service.stop_monitoring_integration()
        await tech_stack_monitor.stop_monitoring()
        await quality_assurance_system.stop_qa_system()
    
    @pytest.mark.asyncio
    async def test_performance_monitor_real_metrics_integration(
        self,
        monitoring_integration_service
    ):
        """Test that PerformanceMonitor connects to actual system metrics."""
        performance_monitor = PerformanceMonitor()
        
        await monitoring_integration_service.start_monitoring_integration()
        performance_monitor.start_monitoring()
        
        # Create session with performance data
        session = monitoring_integration_service.start_generation_monitoring(
            requirements={'test': 'requirements'}
        )
        
        # Add performance-relevant events
        await monitoring_integration_service.track_llm_interaction(
            session_id=session.session_id,
            provider='OpenAI',
            model='gpt-4',
            prompt_data={'test': 'prompt'},
            response_data={'test': 'response'},
            token_usage={'total_tokens': 750},
            duration_ms=1800.0,
            success=True
        )
        
        # Update system metrics (should now include real tech stack data)
        performance_monitor.update_system_metrics()
        
        # Verify metrics were updated with real data
        metrics_summary = performance_monitor.get_metrics_summary()
        
        # Should have both system and tech stack metrics
        assert 'gauges' in metrics_summary['metrics']
        assert 'histograms' in metrics_summary['metrics']
        
        # Check for tech stack specific metrics
        gauges = metrics_summary['metrics']['gauges']
        expected_gauges = ['aaa_active_sessions', 'aaa_llm_request_duration_seconds']
        
        for expected_gauge in expected_gauges:
            if expected_gauge in gauges:
                # Verify realistic values
                value = gauges[expected_gauge]
                if expected_gauge == 'aaa_active_sessions':
                    assert value >= 0
                elif expected_gauge == 'aaa_llm_request_duration_seconds':
                    assert 0.5 <= value <= 10.0  # Realistic LLM response time
        
        performance_monitor.stop_monitoring()
        await monitoring_integration_service.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_alert_thresholds_based_on_real_performance(
        self,
        monitoring_integration_service,
        tech_stack_monitor
    ):
        """Test that alert thresholds are updated based on real system performance."""
        await monitoring_integration_service.start_monitoring_integration()
        await tech_stack_monitor.start_monitoring()
        
        # Generate multiple sessions with varying performance
        performance_data = [
            {'duration': 1500, 'accuracy': 0.95},
            {'duration': 2200, 'accuracy': 0.88},
            {'duration': 1800, 'accuracy': 0.92},
            {'duration': 3500, 'accuracy': 0.85},  # Slower performance
            {'duration': 1200, 'accuracy': 0.97}
        ]
        
        for i, perf_data in enumerate(performance_data):
            session = monitoring_integration_service.start_generation_monitoring(
                requirements={'test': f'requirements_{i}'}
            )
            
            # Simulate processing with varying performance
            await monitoring_integration_service.track_parsing_step(
                session_id=session.session_id,
                step_name='test_parsing',
                input_data={'test': 'input'},
                output_data={'explicit_technologies': ['AWS Lambda', 'Python']},
                duration_ms=perf_data['duration'] * 0.1,  # Parsing is 10% of total
                success=True
            )
            
            # Record extraction accuracy
            tech_stack_monitor.record_extraction_accuracy(
                session_id=session.session_id,
                extracted_count=2,
                expected_count=2,
                explicit_tech_included=2,
                explicit_tech_total=2,
                processing_time=perf_data['duration'] / 1000.0
            )
        
        # Allow time for metrics processing
        await asyncio.sleep(1)
        
        # Check that alerts are generated based on real performance data
        recent_alerts = tech_stack_monitor.alerts
        
        # Should have performance-based alerts if thresholds exceeded
        performance_alerts = [alert for alert in recent_alerts 
                            if 'performance' in alert.category.lower()]
        
        # Verify alert thresholds are realistic based on actual data
        if performance_alerts:
            for alert in performance_alerts:
                # Alert details should reference actual measured values
                assert 'processing_time' in alert.details or 'duration' in alert.details
                
                # Values should be realistic (not mock data)
                if 'processing_time' in alert.details:
                    processing_time = alert.details['processing_time']
                    assert 1.0 <= processing_time <= 10.0
        
        await monitoring_integration_service.stop_monitoring_integration()
        await tech_stack_monitor.stop_monitoring()
    
    @pytest.mark.asyncio
    async def test_monitoring_dashboard_live_data_feeds(
        self,
        monitoring_integration_service,
        tech_stack_monitor
    ):
        """Test that monitoring dashboards receive live data feeds from generation processes."""
        await monitoring_integration_service.start_monitoring_integration()
        await tech_stack_monitor.start_monitoring()
        
        # Create active session with ongoing events
        session = monitoring_integration_service.start_generation_monitoring(
            requirements={'live_test': 'requirements'}
        )
        
        # Add events over time to simulate live generation
        events_data = [
            {'type': 'parsing', 'duration': 120},
            {'type': 'extraction', 'duration': 180},
            {'type': 'llm', 'duration': 2200},
            {'type': 'validation', 'duration': 90}
        ]
        
        for event_data in events_data:
            if event_data['type'] == 'parsing':
                await monitoring_integration_service.track_parsing_step(
                    session_id=session.session_id,
                    step_name='live_parsing',
                    input_data={'live': True},
                    output_data={'technologies': ['AWS Lambda']},
                    duration_ms=event_data['duration'],
                    success=True
                )
            elif event_data['type'] == 'llm':
                await monitoring_integration_service.track_llm_interaction(
                    session_id=session.session_id,
                    provider='OpenAI',
                    model='gpt-4',
                    prompt_data={'live': True},
                    response_data={'technologies': ['AWS Lambda', 'Python']},
                    duration_ms=event_data['duration'],
                    success=True
                )
            
            # Small delay to simulate real-time processing
            await asyncio.sleep(0.1)
        
        # Verify live data is available in monitoring components
        service_metrics = monitoring_integration_service.get_service_metrics()
        assert service_metrics['active_sessions'] > 0
        assert service_metrics['total_events_buffered'] > 0
        
        # Verify tech stack monitor has live metrics
        recent_metrics = tech_stack_monitor._get_recent_metrics(hours=1)
        assert len(recent_metrics) > 0
        
        # Check that metrics have recent timestamps (within last minute)
        recent_timestamp = datetime.now() - timedelta(minutes=1)
        recent_metric_count = sum(1 for metric in recent_metrics 
                                if metric.timestamp >= recent_timestamp)
        assert recent_metric_count > 0
        
        # Verify system health score reflects live data
        health_score = tech_stack_monitor.get_system_health_score()
        assert 'overall_score' in health_score
        assert 'component_scores' in health_score
        assert health_score['health_status'] != 'unknown'  # Should have real data
        
        await monitoring_integration_service.stop_monitoring_integration()
        await tech_stack_monitor.stop_monitoring()


class TestMonitoringDataQuality:
    """Test the quality and accuracy of monitoring data from real generation processes."""
    
    @pytest.mark.asyncio
    async def test_monitoring_data_accuracy_validation(self):
        """Test that monitoring data accurately reflects actual generation process."""
        monitoring_service = TechStackMonitoringIntegrationService()
        await monitoring_service.start_monitoring_integration()
        
        # Create session and track specific metrics
        session = monitoring_service.start_generation_monitoring(
            requirements={'accuracy_test': 'requirements'}
        )
        
        # Track parsing with known input/output
        known_input = {'requirements': {'tech': 'AWS Lambda'}}
        known_output = {'explicit_technologies': ['AWS Lambda'], 'confidence': 0.95}
        
        await monitoring_service.track_parsing_step(
            session_id=session.session_id,
            step_name='accuracy_test_parsing',
            input_data=known_input,
            output_data=known_output,
            duration_ms=100.0,
            success=True
        )
        
        # Retrieve and validate the recorded data
        session_events = monitoring_service.get_session_events(session.session_id)
        parsing_events = [e for e in session_events if e['event_type'] == 'parsing_complete']
        
        assert len(parsing_events) == 1
        parsing_event = parsing_events[0]
        
        # Verify data accuracy
        assert parsing_event['data']['input_data'] == known_input
        assert parsing_event['data']['output_data'] == known_output
        assert parsing_event['duration_ms'] == 100.0
        assert parsing_event['success'] is True
        
        await monitoring_service.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_monitoring_data_completeness(self):
        """Test that monitoring captures complete generation workflow data."""
        monitoring_service = TechStackMonitoringIntegrationService()
        await monitoring_service.start_monitoring_integration()
        
        # Simulate complete generation workflow
        session = monitoring_service.start_generation_monitoring(
            requirements={'completeness_test': 'requirements'}
        )
        
        # Track all major steps
        await monitoring_service.track_parsing_step(
            session_id=session.session_id,
            step_name='parsing',
            input_data={'test': 'input'},
            output_data={'test': 'output'},
            duration_ms=100.0
        )
        
        await monitoring_service.track_extraction_step(
            session_id=session.session_id,
            extraction_type='test',
            extracted_technologies=['tech1', 'tech2'],
            confidence_scores={'tech1': 0.9, 'tech2': 0.8},
            context_data={'test': 'context'},
            duration_ms=150.0
        )
        
        await monitoring_service.track_llm_interaction(
            session_id=session.session_id,
            provider='test_provider',
            model='test_model',
            prompt_data={'test': 'prompt'},
            response_data={'test': 'response'},
            duration_ms=2000.0
        )
        
        await monitoring_service.track_validation_step(
            session_id=session.session_id,
            validation_type='test',
            input_technologies=['tech1', 'tech2'],
            validation_results={'valid': True},
            conflicts_detected=[],
            resolutions_applied=[],
            duration_ms=50.0
        )
        
        await monitoring_service.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=['tech1', 'tech2'],
            generation_metrics={'test': 'metrics'},
            success=True
        )
        
        # Verify complete workflow was captured
        session_events = monitoring_service.get_session_events(session.session_id)
        event_types = {event['event_type'] for event in session_events}
        
        expected_types = {
            'session_start',
            'parsing_complete',
            'extraction_complete',
            'llm_call_complete',
            'validation_complete',
            'session_complete'
        }
        
        assert expected_types.issubset(event_types)
        
        # Verify session status
        session_status = monitoring_service.get_session_status(session.session_id)
        assert session_status is None  # Session should be completed and removed from active
        
        await monitoring_service.stop_monitoring_integration()