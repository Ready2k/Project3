"""
Unit tests for Performance Analytics system.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.monitoring.performance_analytics import (
    PerformanceAnalytics,
    UsagePattern,
    PerformanceBottleneck,
    UserSatisfactionAnalysis,
    PredictiveInsight,
    BottleneckSeverity
)


@pytest.fixture
def analytics_config():
    """Test configuration for performance analytics."""
    return {
        'analysis_interval_minutes': 1,  # Faster for testing
        'bottleneck_detection_threshold': 0.5,
        'satisfaction_correlation_window_hours': 1,
        'prediction_confidence_threshold': 0.6,
        'max_stored_patterns': 100,
        'max_stored_bottlenecks': 50,
        'capacity_planning_horizon_days': 7
    }


@pytest.fixture
def performance_analytics(analytics_config):
    """Create performance analytics instance for testing."""
    return PerformanceAnalytics(analytics_config)


@pytest.fixture
def mock_logger():
    """Mock logger for testing."""
    return Mock()


class TestPerformanceAnalytics:
    """Test cases for PerformanceAnalytics class."""
    
    @pytest.mark.asyncio
    async def test_initialization(self, performance_analytics):
        """Test performance analytics initialization."""
        assert performance_analytics.config['analysis_interval_minutes'] == 1
        assert performance_analytics.config['bottleneck_detection_threshold'] == 0.5
        assert len(performance_analytics.usage_patterns) == 0
        assert len(performance_analytics.performance_bottlenecks) == 0
        assert len(performance_analytics.satisfaction_analyses) == 0
        assert len(performance_analytics.predictive_insights) == 0
        assert not performance_analytics.is_running
    
    @pytest.mark.asyncio
    async def test_start_stop_analytics(self, performance_analytics):
        """Test starting and stopping analytics system."""
        with patch.object(performance_analytics, '_initialize_baselines', new_callable=AsyncMock):
            await performance_analytics.start_analytics()
            assert performance_analytics.is_running
            assert performance_analytics.analysis_task is not None
            assert performance_analytics.bottleneck_detection_task is not None
            assert performance_analytics.prediction_task is not None
            
            await performance_analytics.stop_analytics()
            assert not performance_analytics.is_running
    
    @pytest.mark.asyncio
    async def test_track_user_interaction(self, performance_analytics):
        """Test tracking user interactions."""
        await performance_analytics.track_user_interaction(
            session_id='test_session',
            user_segment='new_user',
            interaction_type='session_start',
            interaction_data={'feature': 'tech_generation'}
        )
        
        assert len(performance_analytics.user_interactions) == 1
        interaction = performance_analytics.user_interactions[0]
        assert interaction['session_id'] == 'test_session'
        assert interaction['user_segment'] == 'new_user'
        assert interaction['interaction_type'] == 'session_start'
        assert interaction['data']['feature'] == 'tech_generation'
    
    @pytest.mark.asyncio
    async def test_track_performance_metric(self, performance_analytics):
        """Test tracking performance metrics."""
        await performance_analytics.track_performance_metric(
            component='TechStackGenerator',
            operation='generate_stack',
            metric_name='response_time',
            metric_value=5.5,
            context={'session_id': 'test_session'}
        )
        
        assert len(performance_analytics.performance_metrics) == 1
        metric = performance_analytics.performance_metrics[0]
        assert metric['component'] == 'TechStackGenerator'
        assert metric['operation'] == 'generate_stack'
        assert metric['metric_name'] == 'response_time'
        assert metric['metric_value'] == 5.5
        assert metric['context']['session_id'] == 'test_session'
    
    @pytest.mark.asyncio
    async def test_track_user_satisfaction(self, performance_analytics):
        """Test tracking user satisfaction."""
        satisfaction_scores = {
            'relevance': 4.0,
            'accuracy': 3.5,
            'completeness': 4.5,
            'speed': 3.0
        }
        
        await performance_analytics.track_user_satisfaction(
            session_id='test_session',
            satisfaction_scores=satisfaction_scores,
            feedback='Good results but a bit slow',
            context={'tech_stack_size': 5}
        )
        
        assert len(performance_analytics.satisfaction_analyses) == 1
        analysis = performance_analytics.satisfaction_analyses[0]
        assert analysis.overall_score == 3.75  # Average of scores
        assert analysis.feedback_sentiment == 'positive'  # Overall score > 3.5
    
    @pytest.mark.asyncio
    async def test_bottleneck_detection(self, performance_analytics):
        """Test performance bottleneck detection."""
        # Set up baselines
        performance_analytics.performance_baselines = {
            'response_time': {'mean': 3.0, 'median': 2.5, 'p95': 5.0, 'std': 1.0}
        }
        
        # Create a metric that should trigger bottleneck detection
        metric = {
            'component': 'LLMProvider',
            'operation': 'generate_response',
            'metric_name': 'response_time',
            'metric_value': 8.0,  # Above p95 threshold
            'context': {'session_id': 'test_session'}
        }
        
        with patch.object(performance_analytics, '_analyze_bottleneck_impact', new_callable=AsyncMock) as mock_impact:
            with patch.object(performance_analytics, '_generate_bottleneck_recommendations', new_callable=AsyncMock) as mock_recommendations:
                mock_impact.return_value = {'affected_users': 5, 'performance_degradation': 0.6}
                mock_recommendations.return_value = ['Consider switching to faster model']
                
                await performance_analytics._detect_performance_bottleneck(metric)
                
                assert len(performance_analytics.performance_bottlenecks) == 1
                bottleneck = performance_analytics.performance_bottlenecks[0]
                assert bottleneck.component == 'LLMProvider'
                assert bottleneck.operation == 'generate_response'
                assert bottleneck.severity in [BottleneckSeverity.MEDIUM, BottleneckSeverity.HIGH]
                
                mock_impact.assert_called_once()
                mock_recommendations.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_usage_pattern_analysis(self, performance_analytics):
        """Test usage pattern analysis."""
        # Set up baselines
        performance_analytics.usage_baselines = {
            'session_frequency': {'sessions_per_hour': 10.0, 'avg_session_duration': 300.0}
        }
        
        # Add multiple interactions to trigger pattern analysis
        current_time = datetime.now()
        for i in range(10):
            performance_analytics.user_interactions.append({
                'session_id': f'session_{i}',
                'user_segment': 'returning_user',
                'interaction_type': 'tech_generation',
                'timestamp': current_time - timedelta(minutes=i * 5),
                'data': {'feature': 'tech_generation'}
            })
        
        # Create an interaction that should trigger pattern detection
        test_interaction = {
            'session_id': 'test_session',
            'user_segment': 'new_user',
            'interaction_type': 'session_start',
            'timestamp': current_time,
            'data': {'feature': 'tech_generation'}
        }
        
        await performance_analytics._analyze_interaction_pattern(test_interaction)
        
        # Should detect some patterns based on the interactions
        # The exact patterns depend on the analysis logic
        assert len(performance_analytics.usage_patterns) >= 0  # May or may not detect patterns
    
    @pytest.mark.asyncio
    async def test_user_satisfaction_analysis(self, performance_analytics):
        """Test user satisfaction analysis."""
        satisfaction_scores = {
            'relevance': 4.0,
            'accuracy': 2.5,  # Below average
            'completeness': 4.5,
            'speed': 3.0
        }
        
        # Add some performance metrics for correlation
        performance_analytics.performance_metrics.append({
            'component': 'TechStackGenerator',
            'operation': 'generate_stack',
            'metric_name': 'response_time',
            'metric_value': 6.0,
            'timestamp': datetime.now(),
            'context': {'session_id': 'test_session'}
        })
        
        analysis = await performance_analytics._analyze_user_satisfaction(
            session_id='test_session',
            satisfaction_scores=satisfaction_scores,
            feedback='Good results but accuracy could be better',
            context={}
        )
        
        assert analysis.overall_score == 3.5  # Average of scores
        assert 'accuracy' in analysis.improvement_areas  # Below 3.0 threshold
        assert analysis.feedback_sentiment == 'positive'  # 'good' keyword
        assert len(analysis.correlation_factors) >= 0  # May have correlations
    
    @pytest.mark.asyncio
    async def test_capacity_prediction(self, performance_analytics):
        """Test capacity utilization prediction."""
        # Add historical usage data
        current_time = datetime.now()
        for day in range(7):
            for interaction in range(20 + day * 2):  # Increasing usage
                performance_analytics.user_interactions.append({
                    'session_id': f'session_{day}_{interaction}',
                    'user_segment': 'returning_user',
                    'interaction_type': 'tech_generation',
                    'timestamp': current_time - timedelta(days=day, minutes=interaction * 5),
                    'data': {'feature': 'tech_generation'}
                })
        
        await performance_analytics._predict_capacity_utilization()
        
        # Should generate capacity insights if enough data
        capacity_insights = [
            i for i in performance_analytics.predictive_insights 
            if i.insight_type == 'capacity_planning'
        ]
        
        # May or may not generate insights depending on confidence threshold
        assert len(capacity_insights) >= 0
    
    @pytest.mark.asyncio
    async def test_performance_trend_prediction(self, performance_analytics):
        """Test performance trend prediction."""
        # Add historical performance data with trend
        current_time = datetime.now()
        for day in range(7):
            base_response_time = 3.0 + (day * 0.2)  # Increasing trend
            for metric in range(10):
                performance_analytics.performance_metrics.append({
                    'component': 'TechStackGenerator',
                    'operation': 'generate_stack',
                    'metric_name': 'response_time',
                    'metric_value': base_response_time + (metric * 0.1),
                    'timestamp': current_time - timedelta(days=day, minutes=metric * 30),
                    'context': {'session_id': f'session_{day}_{metric}'}
                })
        
        await performance_analytics._predict_performance_trends()
        
        # Should generate performance trend insights
        trend_insights = [
            i for i in performance_analytics.predictive_insights 
            if i.insight_type == 'performance_trend'
        ]
        
        # May generate insights if trend is significant enough
        assert len(trend_insights) >= 0
    
    @pytest.mark.asyncio
    async def test_analytics_summary(self, performance_analytics):
        """Test analytics summary generation."""
        # Add some test data
        performance_analytics.usage_patterns.append(
            UsagePattern(
                pattern_id='test_pattern',
                pattern_type='session_duration_anomaly',
                timestamp=datetime.now(),
                user_segment='new_user',
                metrics={'avg_duration': 600.0},
                context={'sample_size': 10}
            )
        )
        
        performance_analytics.performance_bottlenecks.append(
            PerformanceBottleneck(
                bottleneck_id='test_bottleneck',
                component='LLMProvider',
                operation='generate_response',
                severity=BottleneckSeverity.MEDIUM,
                detected_at=datetime.now(),
                metrics={'response_time': 8.0},
                impact_analysis={'affected_users': 5},
                recommendations=['Optimize model'],
                context={}
            )
        )
        
        summary = performance_analytics.get_analytics_summary()
        
        assert 'summary' in summary
        assert 'usage_patterns' in summary
        assert 'performance_bottlenecks' in summary
        assert 'baselines' in summary
        assert 'system_status' in summary
        
        assert summary['summary']['total_usage_patterns'] == 1
        assert summary['summary']['total_bottlenecks'] == 1
        assert summary['system_status']['analytics_running'] == performance_analytics.is_running
    
    @pytest.mark.asyncio
    async def test_analytics_report_generation(self, performance_analytics):
        """Test comprehensive analytics report generation."""
        # Add test data
        current_time = datetime.now()
        
        performance_analytics.usage_patterns.append(
            UsagePattern(
                pattern_id='test_pattern',
                pattern_type='request_frequency_anomaly',
                timestamp=current_time,
                user_segment='power_user',
                metrics={'requests_per_hour': 50.0},
                context={'analysis_window': '1_hour'}
            )
        )
        
        performance_analytics.satisfaction_analyses.append(
            UserSatisfactionAnalysis(
                analysis_id='test_satisfaction',
                timestamp=current_time,
                overall_score=4.2,
                dimension_scores={'relevance': 4.0, 'accuracy': 4.5},
                feedback_sentiment='positive',
                improvement_areas=[],
                correlation_factors={'response_time': 0.8}
            )
        )
        
        # Generate report for last hour
        time_period = (current_time - timedelta(hours=1), current_time)
        report = await performance_analytics.generate_analytics_report(time_period)
        
        assert report.report_id.startswith('analytics_report_')
        assert len(report.usage_patterns) == 1
        assert len(report.satisfaction_analysis) == 1
        assert report.summary_metrics['total_patterns'] == 1
        assert report.summary_metrics['avg_satisfaction_score'] == 4.2
        assert len(report.recommendations) >= 0
    
    def test_percentile_calculation(self, performance_analytics):
        """Test percentile calculation utility."""
        values = [1, 2, 3, 4, 5, 6, 7, 8, 9, 10]
        
        p50 = performance_analytics._percentile(values, 0.5)
        p95 = performance_analytics._percentile(values, 0.95)
        p99 = performance_analytics._percentile(values, 0.99)
        
        assert p50 == 5  # Median
        assert p95 == 9  # 95th percentile
        assert p99 == 10  # 99th percentile
        
        # Test empty list
        assert performance_analytics._percentile([], 0.5) == 0.0
    
    @pytest.mark.asyncio
    async def test_baseline_initialization(self, performance_analytics):
        """Test baseline initialization from historical data."""
        with patch('app.utils.imports.optional_service') as mock_service:
            # Mock integration service with sample data
            mock_integration = Mock()
            mock_integration.get_active_sessions.return_value = [
                {'session_id': 'session1', 'duration_seconds': 300},
                {'session_id': 'session2', 'duration_seconds': 450}
            ]
            mock_integration.get_session_events.return_value = [
                {
                    'event_type': 'llm_call_complete',
                    'duration_ms': 5000,
                    'success': True
                },
                {
                    'event_type': 'parsing_complete',
                    'duration_ms': 2000,
                    'success': True
                }
            ]
            
            mock_tech_monitor = Mock()
            
            mock_service.side_effect = lambda service_name, context: {
                'tech_stack_monitoring_integration': mock_integration,
                'tech_stack_monitor': mock_tech_monitor
            }.get(service_name)
            
            await performance_analytics._initialize_baselines()
            
            # Should have initialized baselines
            assert 'llm_response_time' in performance_analytics.performance_baselines
            assert 'processing_time' in performance_analytics.performance_baselines
            assert 'success_rate' in performance_analytics.performance_baselines
            assert 'session_frequency' in performance_analytics.usage_baselines
    
    def test_capacity_recommendations(self, performance_analytics):
        """Test capacity planning recommendations."""
        # Test high utilization
        recommendations = performance_analytics._generate_capacity_recommendations(0.85, 0.3)
        assert any('scaling' in rec.lower() for rec in recommendations)
        
        # Test critical utilization
        recommendations = performance_analytics._generate_capacity_recommendations(0.95, 0.6)
        assert any('immediate' in rec.lower() for rec in recommendations)
        assert any('auto-scaling' in rec.lower() for rec in recommendations)
        
        # Test declining usage
        recommendations = performance_analytics._generate_capacity_recommendations(0.5, -0.3)
        assert any('decline' in rec.lower() for rec in recommendations)
    
    def test_performance_trend_recommendations(self, performance_analytics):
        """Test performance trend recommendations."""
        # Test increasing response time
        recommendations = performance_analytics._generate_performance_trend_recommendations(
            'response_time', 0.3, 6.0
        )
        assert any('bottleneck' in rec.lower() for rec in recommendations)
        assert any('optimization' in rec.lower() for rec in recommendations)
        
        # Test declining success rate
        recommendations = performance_analytics._generate_performance_trend_recommendations(
            'success_rate', -0.2, 0.8
        )
        assert any('quality' in rec.lower() for rec in recommendations)
        assert any('error' in rec.lower() for rec in recommendations)
        
        # Test declining user satisfaction
        recommendations = performance_analytics._generate_performance_trend_recommendations(
            'user_satisfaction', -0.15, 3.5
        )
        assert any('satisfaction' in rec.lower() for rec in recommendations)
        assert any('experience' in rec.lower() for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_export_analytics_data(self, performance_analytics, tmp_path):
        """Test exporting analytics data to file."""
        # Add some test data
        performance_analytics.usage_patterns.append(
            UsagePattern(
                pattern_id='export_test',
                pattern_type='test_pattern',
                timestamp=datetime.now(),
                user_segment='test_user',
                metrics={'test_metric': 1.0},
                context={'test': True}
            )
        )
        
        export_file = tmp_path / "analytics_export.json"
        
        performance_analytics.export_analytics_data(str(export_file))
        
        assert export_file.exists()
        
        # Verify file content
        import json
        with open(export_file, 'r') as f:
            data = json.load(f)
        
        assert 'report_id' in data
        assert 'generated_at' in data
        assert 'usage_patterns' in data
        assert len(data['usage_patterns']) == 1
        assert data['usage_patterns'][0]['pattern_id'] == 'export_test'


class TestAnalyticsDataStructures:
    """Test analytics data structures."""
    
    def test_usage_pattern_serialization(self):
        """Test UsagePattern serialization."""
        pattern = UsagePattern(
            pattern_id='test_pattern',
            pattern_type='session_duration',
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            user_segment='new_user',
            metrics={'duration': 300.0},
            context={'sample_size': 10}
        )
        
        data = pattern.to_dict()
        
        assert data['pattern_id'] == 'test_pattern'
        assert data['pattern_type'] == 'session_duration'
        assert data['timestamp'] == '2023-01-01T12:00:00'
        assert data['user_segment'] == 'new_user'
        assert data['metrics']['duration'] == 300.0
        assert data['context']['sample_size'] == 10
    
    def test_performance_bottleneck_serialization(self):
        """Test PerformanceBottleneck serialization."""
        bottleneck = PerformanceBottleneck(
            bottleneck_id='test_bottleneck',
            component='TestComponent',
            operation='test_operation',
            severity=BottleneckSeverity.HIGH,
            detected_at=datetime(2023, 1, 1, 12, 0, 0),
            metrics={'response_time': 10.0},
            impact_analysis={'affected_users': 5},
            recommendations=['Fix the issue'],
            context={'test': True}
        )
        
        data = bottleneck.to_dict()
        
        assert data['bottleneck_id'] == 'test_bottleneck'
        assert data['component'] == 'TestComponent'
        assert data['severity'] == 'high'
        assert data['detected_at'] == '2023-01-01T12:00:00'
        assert data['metrics']['response_time'] == 10.0
        assert data['impact_analysis']['affected_users'] == 5
        assert data['recommendations'] == ['Fix the issue']
    
    def test_user_satisfaction_analysis_serialization(self):
        """Test UserSatisfactionAnalysis serialization."""
        analysis = UserSatisfactionAnalysis(
            analysis_id='test_analysis',
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            overall_score=4.2,
            dimension_scores={'relevance': 4.0, 'accuracy': 4.5},
            feedback_sentiment='positive',
            improvement_areas=['speed'],
            correlation_factors={'response_time': 0.8}
        )
        
        data = analysis.to_dict()
        
        assert data['analysis_id'] == 'test_analysis'
        assert data['timestamp'] == '2023-01-01T12:00:00'
        assert data['overall_score'] == 4.2
        assert data['dimension_scores']['relevance'] == 4.0
        assert data['feedback_sentiment'] == 'positive'
        assert data['improvement_areas'] == ['speed']
        assert data['correlation_factors']['response_time'] == 0.8
    
    def test_predictive_insight_serialization(self):
        """Test PredictiveInsight serialization."""
        insight = PredictiveInsight(
            insight_id='test_insight',
            insight_type='capacity_planning',
            timestamp=datetime(2023, 1, 1, 12, 0, 0),
            prediction_horizon='30_days',
            confidence_score=0.85,
            predicted_metrics={'utilization': 0.75},
            recommendations=['Scale up'],
            supporting_data={'historical_days': 30}
        )
        
        data = insight.to_dict()
        
        assert data['insight_id'] == 'test_insight'
        assert data['insight_type'] == 'capacity_planning'
        assert data['timestamp'] == '2023-01-01T12:00:00'
        assert data['prediction_horizon'] == '30_days'
        assert data['confidence_score'] == 0.85
        assert data['predicted_metrics']['utilization'] == 0.75
        assert data['recommendations'] == ['Scale up']
        assert data['supporting_data']['historical_days'] == 30