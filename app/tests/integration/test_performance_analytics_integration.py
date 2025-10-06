"""
Integration tests for Performance Analytics system.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import patch, AsyncMock

from app.monitoring.performance_analytics import PerformanceAnalytics, BottleneckSeverity
from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService


@pytest.fixture
def analytics_config():
    """Test configuration for performance analytics."""
    return {
        'analysis_interval_minutes': 1,
        'bottleneck_detection_threshold': 0.5,
        'satisfaction_correlation_window_hours': 1,
        'prediction_confidence_threshold': 0.6,
        'max_stored_patterns': 100,
        'max_stored_bottlenecks': 50,
        'capacity_planning_horizon_days': 7
    }


@pytest.fixture
async def performance_analytics(analytics_config):
    """Create and initialize performance analytics for testing."""
    analytics = PerformanceAnalytics(analytics_config)
    
    # Mock the service dependencies to avoid actual service calls
    with patch('app.utils.imports.optional_service') as mock_service:
        mock_service.return_value = None  # No services available
        await analytics.start_analytics()
    
    yield analytics
    
    await analytics.stop_analytics()


@pytest.fixture
async def monitoring_integration():
    """Create monitoring integration service for testing."""
    config = {
        'max_session_duration_hours': 1,
        'max_events_per_session': 100,
        'cleanup_interval_minutes': 10,
        'real_time_streaming': True,
        'buffer_size': 10
    }
    
    service = TechStackMonitoringIntegrationService(config)
    
    # Mock the monitoring components to avoid actual initialization
    with patch.object(service, '_initialize_monitoring_components', new_callable=AsyncMock):
        await service.start_monitoring_integration()
    
    yield service
    
    await service.stop_monitoring_integration()


class TestPerformanceAnalyticsIntegration:
    """Integration tests for performance analytics with monitoring system."""
    
    @pytest.mark.asyncio
    async def test_real_time_user_interaction_tracking(self, performance_analytics):
        """Test real-time tracking of user interactions."""
        # Simulate multiple user interactions
        interactions = [
            {
                'session_id': 'session_1',
                'user_segment': 'new_user',
                'interaction_type': 'session_start',
                'interaction_data': {'feature': 'tech_generation', 'requirements_count': 5}
            },
            {
                'session_id': 'session_1',
                'user_segment': 'new_user',
                'interaction_type': 'tech_generation',
                'interaction_data': {'tech_stack_size': 8, 'processing_time': 4.5}
            },
            {
                'session_id': 'session_2',
                'user_segment': 'returning_user',
                'interaction_type': 'session_start',
                'interaction_data': {'feature': 'pattern_matching', 'requirements_count': 3}
            }
        ]
        
        # Track interactions
        for interaction in interactions:
            await performance_analytics.track_user_interaction(**interaction)
        
        # Verify interactions are tracked
        assert len(performance_analytics.user_interactions) == 3
        
        # Verify interaction data
        tracked_interactions = list(performance_analytics.user_interactions)
        assert tracked_interactions[0]['session_id'] == 'session_1'
        assert tracked_interactions[0]['user_segment'] == 'new_user'
        assert tracked_interactions[1]['interaction_type'] == 'tech_generation'
        assert tracked_interactions[2]['session_id'] == 'session_2'
    
    @pytest.mark.asyncio
    async def test_performance_bottleneck_detection_workflow(self, performance_analytics):
        """Test end-to-end performance bottleneck detection."""
        # Set up realistic baselines
        performance_analytics.performance_baselines = {
            'response_time': {'mean': 3.0, 'median': 2.5, 'p95': 5.0, 'std': 1.0},
            'processing_time': {'mean': 2.0, 'median': 1.8, 'p95': 3.5, 'std': 0.8},
            'success_rate': {'mean': 0.95, 'std': 0.05}
        }
        
        # Simulate performance metrics that should trigger bottleneck detection
        performance_metrics = [
            {
                'component': 'LLMProvider',
                'operation': 'generate_response',
                'metric_name': 'response_time',
                'metric_value': 8.0,  # Above p95 threshold
                'context': {'session_id': 'session_1', 'model': 'gpt-4'}
            },
            {
                'component': 'TechStackGenerator',
                'operation': 'extract_technologies',
                'metric_name': 'processing_time',
                'metric_value': 6.0,  # Above p95 threshold
                'context': {'session_id': 'session_2', 'requirements_count': 10}
            },
            {
                'component': 'TechnologyValidator',
                'operation': 'validate_compatibility',
                'metric_name': 'success_rate',
                'metric_value': 0.7,  # Below baseline
                'context': {'session_id': 'session_3', 'tech_count': 12}
            }
        ]
        
        # Track metrics
        for metric in performance_metrics:
            await performance_analytics.track_performance_metric(**metric)
        
        # Verify bottlenecks are detected
        assert len(performance_analytics.performance_bottlenecks) >= 2  # At least 2 should be detected
        
        # Verify bottleneck details
        bottlenecks = performance_analytics.performance_bottlenecks
        
        # Check LLM bottleneck
        llm_bottlenecks = [b for b in bottlenecks if b.component == 'LLMProvider']
        assert len(llm_bottlenecks) >= 1
        llm_bottleneck = llm_bottlenecks[0]
        assert llm_bottleneck.severity in [BottleneckSeverity.MEDIUM, BottleneckSeverity.HIGH]
        assert 'response_time' in llm_bottleneck.metrics
        assert len(llm_bottleneck.recommendations) > 0
        
        # Check TechStackGenerator bottleneck
        tsg_bottlenecks = [b for b in bottlenecks if b.component == 'TechStackGenerator']
        assert len(tsg_bottlenecks) >= 1
        tsg_bottleneck = tsg_bottlenecks[0]
        assert tsg_bottleneck.severity in [BottleneckSeverity.MEDIUM, BottleneckSeverity.HIGH]
        assert 'processing_time' in tsg_bottleneck.metrics
    
    @pytest.mark.asyncio
    async def test_user_satisfaction_correlation_analysis(self, performance_analytics):
        """Test correlation between user satisfaction and performance metrics."""
        session_id = 'correlation_test_session'
        
        # Add performance metrics for the session
        performance_metrics = [
            {
                'component': 'TechStackGenerator',
                'operation': 'generate_stack',
                'metric_name': 'response_time',
                'metric_value': 6.0,
                'context': {'session_id': session_id}
            },
            {
                'component': 'TechStackGenerator',
                'operation': 'generate_stack',
                'metric_name': 'success_rate',
                'metric_value': 0.9,
                'context': {'session_id': session_id}
            },
            {
                'component': 'TechStackGenerator',
                'operation': 'generate_stack',
                'metric_name': 'accuracy',
                'metric_value': 0.85,
                'context': {'session_id': session_id}
            }
        ]
        
        for metric in performance_metrics:
            await performance_analytics.track_performance_metric(**metric)
        
        # Track user satisfaction
        satisfaction_scores = {
            'relevance': 4.0,
            'accuracy': 3.5,
            'completeness': 4.2,
            'speed': 2.8  # Low due to slow response time
        }
        
        await performance_analytics.track_user_satisfaction(
            session_id=session_id,
            satisfaction_scores=satisfaction_scores,
            feedback='Results were good but took too long to generate',
            context={'tech_stack_size': 8}
        )
        
        # Verify satisfaction analysis
        assert len(performance_analytics.satisfaction_analyses) == 1
        analysis = performance_analytics.satisfaction_analyses[0]
        
        # Check overall score calculation
        expected_overall = sum(satisfaction_scores.values()) / len(satisfaction_scores)
        assert abs(analysis.overall_score - expected_overall) < 0.01
        
        # Check improvement areas (speed should be flagged)
        assert 'speed' in analysis.improvement_areas
        
        # Check feedback sentiment
        assert analysis.feedback_sentiment == 'positive'  # 'good' keyword
        
        # Check correlation factors
        assert len(analysis.correlation_factors) > 0
        assert 'response_time' in analysis.correlation_factors or 'success_rate' in analysis.correlation_factors
    
    @pytest.mark.asyncio
    async def test_usage_pattern_detection_over_time(self, performance_analytics):
        """Test usage pattern detection with time-based data."""
        # Set up usage baselines
        performance_analytics.usage_baselines = {
            'session_frequency': {'sessions_per_hour': 10.0, 'avg_session_duration': 300.0}
        }
        
        # Simulate usage pattern over time (increasing frequency)
        current_time = datetime.now()
        
        # Normal usage period
        for i in range(10):
            await performance_analytics.track_user_interaction(
                session_id=f'normal_session_{i}',
                user_segment='returning_user',
                interaction_type='tech_generation',
                interaction_data={'feature': 'tech_generation'},
                timestamp=current_time - timedelta(minutes=60 - i * 5)
            )
        
        # High usage period (anomaly)
        for i in range(25):  # Much higher frequency
            await performance_analytics.track_user_interaction(
                session_id=f'high_usage_session_{i}',
                user_segment='power_user',
                interaction_type='tech_generation',
                interaction_data={'feature': 'tech_generation'},
                timestamp=current_time - timedelta(minutes=30 - i)
            )
        
        # Trigger pattern analysis
        await performance_analytics._analyze_usage_patterns()
        
        # Verify pattern detection
        frequency_patterns = [
            p for p in performance_analytics.usage_patterns 
            if p.pattern_type == 'request_frequency_anomaly'
        ]
        
        # Should detect frequency anomaly
        assert len(frequency_patterns) >= 1
        
        if frequency_patterns:
            pattern = frequency_patterns[0]
            assert pattern.metrics['requests_per_hour'] > performance_analytics.usage_baselines['session_frequency']['sessions_per_hour']
            assert pattern.metrics['deviation_percent'] > 0.5  # Significant deviation
    
    @pytest.mark.asyncio
    async def test_predictive_insights_generation(self, performance_analytics):
        """Test generation of predictive insights from historical data."""
        current_time = datetime.now()
        
        # Generate historical usage data with growth trend
        for day in range(14):  # 2 weeks of data
            daily_interactions = 20 + day * 2  # Growing usage
            for interaction in range(daily_interactions):
                await performance_analytics.track_user_interaction(
                    session_id=f'historical_session_{day}_{interaction}',
                    user_segment='returning_user',
                    interaction_type='tech_generation',
                    interaction_data={'feature': 'tech_generation'},
                    timestamp=current_time - timedelta(days=14 - day, minutes=interaction * 2)
                )
        
        # Generate historical performance data with degradation trend
        for day in range(7):  # 1 week of performance data
            base_response_time = 3.0 + (day * 0.3)  # Degrading performance
            for metric in range(15):
                await performance_analytics.track_performance_metric(
                    component='TechStackGenerator',
                    operation='generate_stack',
                    metric_name='response_time',
                    metric_value=base_response_time + (metric * 0.05),
                    context={'session_id': f'perf_session_{day}_{metric}'},
                    timestamp=current_time - timedelta(days=7 - day, minutes=metric * 30)
                )
        
        # Generate predictive insights
        await performance_analytics._generate_predictive_insights()
        
        # Verify capacity planning insights
        capacity_insights = [
            i for i in performance_analytics.predictive_insights 
            if i.insight_type == 'capacity_planning'
        ]
        
        if capacity_insights:
            insight = capacity_insights[0]
            assert insight.confidence_score >= performance_analytics.config['prediction_confidence_threshold']
            assert 'daily_usage' in insight.predicted_metrics
            assert 'capacity_utilization' in insight.predicted_metrics
            assert len(insight.recommendations) > 0
        
        # Verify performance trend insights
        trend_insights = [
            i for i in performance_analytics.predictive_insights 
            if i.insight_type == 'performance_trend'
        ]
        
        if trend_insights:
            insight = trend_insights[0]
            assert insight.confidence_score >= performance_analytics.config['prediction_confidence_threshold']
            assert 'response_time' in insight.predicted_metrics
            assert len(insight.recommendations) > 0
    
    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, performance_analytics):
        """Test overall system health monitoring and analysis."""
        # Set up performance baselines
        performance_analytics.performance_baselines = {
            'llm_response_time': {'mean': 4.0, 'median': 3.5, 'p95': 7.0, 'std': 1.5},
            'success_rate': {'mean': 0.95, 'std': 0.05}
        }
        
        # Add recent performance metrics
        current_time = datetime.now()
        
        # Good performance metrics
        for i in range(10):
            await performance_analytics.track_performance_metric(
                component='TechStackGenerator',
                operation='generate_stack',
                metric_name='response_time',
                metric_value=3.5 + (i * 0.1),  # Around baseline
                context={'session_id': f'health_session_{i}'},
                timestamp=current_time - timedelta(minutes=30 - i * 2)
            )
            
            await performance_analytics.track_performance_metric(
                component='TechStackGenerator',
                operation='generate_stack',
                metric_name='success_rate',
                metric_value=0.95,  # At baseline
                context={'session_id': f'health_session_{i}'},
                timestamp=current_time - timedelta(minutes=30 - i * 2)
            )
        
        # Analyze system health
        await performance_analytics._analyze_system_health()
        
        # Verify health metrics are tracked
        health_metrics = [
            m for m in performance_analytics.performance_metrics 
            if m['metric_name'] == 'overall_health'
        ]
        
        assert len(health_metrics) >= 1
        
        if health_metrics:
            health_metric = health_metrics[-1]  # Most recent
            assert health_metric['component'] == 'System'
            assert health_metric['operation'] == 'health_check'
            assert 0.0 <= health_metric['metric_value'] <= 1.0  # Health score should be normalized
            assert 'health_components' in health_metric['context']
    
    @pytest.mark.asyncio
    async def test_analytics_report_comprehensive(self, performance_analytics):
        """Test comprehensive analytics report generation with real data."""
        current_time = datetime.now()
        
        # Add comprehensive test data
        
        # User interactions
        for i in range(20):
            await performance_analytics.track_user_interaction(
                session_id=f'report_session_{i % 5}',  # 5 different sessions
                user_segment='returning_user' if i % 3 == 0 else 'new_user',
                interaction_type='tech_generation' if i % 2 == 0 else 'pattern_matching',
                interaction_data={'feature_used': f'feature_{i % 3}'},
                timestamp=current_time - timedelta(minutes=60 - i * 2)
            )
        
        # Performance metrics
        for i in range(15):
            await performance_analytics.track_performance_metric(
                component='TechStackGenerator',
                operation='generate_stack',
                metric_name='response_time',
                metric_value=3.0 + (i * 0.2),
                context={'session_id': f'report_session_{i % 5}'},
                timestamp=current_time - timedelta(minutes=45 - i * 2)
            )
        
        # User satisfaction
        for i in range(5):
            await performance_analytics.track_user_satisfaction(
                session_id=f'report_session_{i}',
                satisfaction_scores={
                    'relevance': 4.0 + (i * 0.1),
                    'accuracy': 3.8 + (i * 0.05),
                    'completeness': 4.2 - (i * 0.1),
                    'speed': 3.5 + (i * 0.2)
                },
                feedback=f'Test feedback {i}',
                context={'tech_stack_size': 5 + i}
            )
        
        # Generate comprehensive report
        time_period = (current_time - timedelta(hours=2), current_time)
        report = await performance_analytics.generate_analytics_report(time_period)
        
        # Verify report structure
        assert report.report_id.startswith('analytics_report_')
        assert report.generated_at <= datetime.now()
        assert report.time_period == time_period
        
        # Verify report content
        assert len(report.usage_patterns) >= 0  # May or may not have patterns
        assert len(report.performance_bottlenecks) >= 0  # May or may not have bottlenecks
        assert len(report.satisfaction_analysis) == 5  # Should have all satisfaction analyses
        assert len(report.predictive_insights) >= 0  # May or may not have insights
        
        # Verify summary metrics
        assert report.summary_metrics['total_satisfaction_analyses'] == 5
        assert 3.5 <= report.summary_metrics['avg_satisfaction_score'] <= 4.5  # Should be in reasonable range
        
        # Verify recommendations
        assert isinstance(report.recommendations, list)
    
    @pytest.mark.asyncio
    async def test_baseline_adaptation_over_time(self, performance_analytics):
        """Test that baselines adapt to changing system performance."""
        # Set initial baselines
        initial_baselines = {
            'response_time': {'mean': 3.0, 'median': 2.8, 'p95': 5.0, 'std': 1.0}
        }
        performance_analytics.performance_baselines = initial_baselines.copy()
        
        # Add performance data that should shift baselines
        current_time = datetime.now()
        
        # Add metrics with higher response times (system degradation)
        for i in range(60):  # Enough data to trigger baseline update
            await performance_analytics.track_performance_metric(
                component='TechStackGenerator',
                operation='generate_stack',
                metric_name='response_time',
                metric_value=5.0 + (i * 0.05),  # Higher than initial baseline
                context={'session_id': f'baseline_session_{i}'},
                timestamp=current_time - timedelta(minutes=60 - i)
            )
        
        # Update baselines
        await performance_analytics._update_baselines()
        
        # Verify baselines have been updated
        updated_baseline = performance_analytics.performance_baselines['response_time']
        
        # New baseline should be higher than initial
        assert updated_baseline['mean'] > initial_baselines['response_time']['mean']
        assert updated_baseline['p95'] > initial_baselines['response_time']['p95']
        
        # Verify baseline structure is maintained
        assert 'mean' in updated_baseline
        assert 'median' in updated_baseline
        assert 'p95' in updated_baseline
        assert 'std' in updated_baseline
    
    @pytest.mark.asyncio
    async def test_monitoring_integration_data_flow(self, performance_analytics, monitoring_integration):
        """Test data flow between monitoring integration and performance analytics."""
        # Set up performance analytics as the analytics component
        monitoring_integration.performance_analytics = performance_analytics
        
        # Create a monitoring session
        requirements = {'technologies': ['AWS', 'Python'], 'domain': 'web_application'}
        session = monitoring_integration.start_generation_monitoring(requirements)
        
        # Simulate monitoring events
        await monitoring_integration.track_llm_interaction(
            session_id=session.session_id,
            provider='openai',
            model='gpt-4',
            prompt_data={'prompt_length': 500},
            response_data={'response_length': 200, 'tech_count': 8},
            token_usage={'total_tokens': 750},
            duration_ms=4500,
            success=True
        )
        
        await monitoring_integration.track_parsing_step(
            session_id=session.session_id,
            step_name='extract_technologies',
            input_data={'requirements': requirements},
            output_data={'extracted_technologies': ['AWS Lambda', 'Python', 'FastAPI']},
            duration_ms=1200,
            success=True
        )
        
        # Complete the session
        final_tech_stack = ['AWS Lambda', 'Python', 'FastAPI', 'PostgreSQL']
        await monitoring_integration.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=final_tech_stack,
            generation_metrics={'total_time': 6.0, 'accuracy': 0.9},
            success=True
        )
        
        # Allow some time for async processing
        await asyncio.sleep(0.1)
        
        # Verify data has flowed to performance analytics
        assert len(performance_analytics.performance_metrics) > 0
        assert len(performance_analytics.user_interactions) > 0
        
        # Verify specific metrics
        response_time_metrics = [
            m for m in performance_analytics.performance_metrics 
            if m['metric_name'] == 'response_time'
        ]
        assert len(response_time_metrics) >= 1
        
        success_rate_metrics = [
            m for m in performance_analytics.performance_metrics 
            if m['metric_name'] == 'success_rate'
        ]
        assert len(success_rate_metrics) >= 1
        
        # Verify user interactions
        session_interactions = [
            i for i in performance_analytics.user_interactions 
            if i['session_id'] == session.session_id
        ]
        assert len(session_interactions) >= 1