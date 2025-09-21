"""
Unit tests for TechStackMonitor.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, AsyncMock

from app.monitoring.tech_stack_monitor import (
    TechStackMonitor, TechStackMetric, QualityAlert, 
    MetricType, AlertLevel, PerformanceRecommendation
)


class TestTechStackMonitor:
    """Test cases for TechStackMonitor."""
    
    @pytest.fixture
    def monitor(self):
        """Create a TechStackMonitor instance for testing."""
        with patch('app.utils.imports.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            monitor = TechStackMonitor()
            monitor.monitoring_active = True
            return monitor
    
    def test_initialization(self, monitor):
        """Test monitor initialization."""
        assert monitor is not None
        assert hasattr(monitor, 'metrics')
        assert hasattr(monitor, 'alerts')
        assert hasattr(monitor, 'recommendations')
        assert hasattr(monitor, 'alert_thresholds')
        assert isinstance(monitor.metrics, list)
        assert isinstance(monitor.alerts, list)
        assert isinstance(monitor.recommendations, list)
    
    def test_record_extraction_accuracy(self, monitor):
        """Test recording extraction accuracy metrics."""
        session_id = "test_session_123"
        extracted_count = 8
        expected_count = 10
        explicit_tech_included = 6
        explicit_tech_total = 8
        processing_time = 15.5
        
        monitor.record_extraction_accuracy(
            session_id=session_id,
            extracted_count=extracted_count,
            expected_count=expected_count,
            explicit_tech_included=explicit_tech_included,
            explicit_tech_total=explicit_tech_total,
            processing_time=processing_time
        )
        
        # Check that metrics were recorded
        assert len(monitor.metrics) == 3  # accuracy, inclusion rate, processing time
        
        # Check accuracy metric
        accuracy_metrics = [m for m in monitor.metrics if m.name == "extraction_accuracy"]
        assert len(accuracy_metrics) == 1
        assert accuracy_metrics[0].value == 0.8  # 8/10
        assert accuracy_metrics[0].session_id == session_id
        
        # Check inclusion rate metric
        inclusion_metrics = [m for m in monitor.metrics if m.name == "explicit_tech_inclusion_rate"]
        assert len(inclusion_metrics) == 1
        assert inclusion_metrics[0].value == 0.75  # 6/8
        
        # Check processing time metric
        time_metrics = [m for m in monitor.metrics if m.name == "processing_time"]
        assert len(time_metrics) == 1
        assert time_metrics[0].value == processing_time
    
    def test_record_catalog_metrics(self, monitor):
        """Test recording catalog health metrics."""
        total_technologies = 100
        missing_technologies = 5
        inconsistent_entries = 2
        pending_review = 10
        
        monitor.record_catalog_metrics(
            total_technologies=total_technologies,
            missing_technologies=missing_technologies,
            inconsistent_entries=inconsistent_entries,
            pending_review=pending_review
        )
        
        # Check that metrics were recorded
        assert len(monitor.metrics) == 3  # consistency, missing rate, pending count
        
        # Check consistency rate
        consistency_metrics = [m for m in monitor.metrics if m.name == "catalog_consistency_rate"]
        assert len(consistency_metrics) == 1
        assert consistency_metrics[0].value == 0.98  # 1 - (2/100)
        
        # Check missing rate
        missing_metrics = [m for m in monitor.metrics if m.name == "catalog_missing_rate"]
        assert len(missing_metrics) == 1
        assert missing_metrics[0].value == 0.05  # 5/100
    
    def test_record_user_satisfaction(self, monitor):
        """Test recording user satisfaction metrics."""
        session_id = "test_session_456"
        relevance_score = 4.5
        accuracy_score = 4.0
        completeness_score = 3.5
        feedback = "Good recommendations but missing some technologies"
        
        monitor.record_user_satisfaction(
            session_id=session_id,
            relevance_score=relevance_score,
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            feedback=feedback
        )
        
        # Check that metrics were recorded
        satisfaction_metrics = [m for m in monitor.metrics if "satisfaction" in m.name]
        assert len(satisfaction_metrics) == 4  # relevance, accuracy, completeness, overall
        
        # Check overall satisfaction calculation
        overall_metrics = [m for m in monitor.metrics if m.name == "overall_satisfaction"]
        assert len(overall_metrics) == 1
        expected_overall = (relevance_score + accuracy_score + completeness_score) / 3
        assert overall_metrics[0].value == expected_overall
        assert overall_metrics[0].metadata.get('feedback') == feedback
    
    def test_accuracy_alerts(self, monitor):
        """Test accuracy-related alert generation."""
        # Set low accuracy to trigger alert
        monitor.record_extraction_accuracy(
            session_id="test_session",
            extracted_count=5,
            expected_count=10,  # 50% accuracy - below threshold
            explicit_tech_included=3,
            explicit_tech_total=8,  # 37.5% inclusion - below threshold
            processing_time=10.0
        )
        
        # Check that alerts were generated
        accuracy_alerts = [a for a in monitor.alerts if a.category == "extraction_accuracy"]
        inclusion_alerts = [a for a in monitor.alerts if a.category == "explicit_tech_inclusion"]
        
        assert len(accuracy_alerts) == 1
        assert accuracy_alerts[0].level == AlertLevel.ERROR
        
        assert len(inclusion_alerts) == 1
        assert inclusion_alerts[0].level == AlertLevel.WARNING
    
    def test_performance_alerts(self, monitor):
        """Test performance-related alert generation."""
        # Set high processing time to trigger alert
        monitor.record_extraction_accuracy(
            session_id="test_session",
            extracted_count=8,
            expected_count=10,
            explicit_tech_included=7,
            explicit_tech_total=8,
            processing_time=45.0  # Above threshold
        )
        
        # Check that performance alert was generated
        perf_alerts = [a for a in monitor.alerts if a.category == "performance"]
        assert len(perf_alerts) == 1
        assert perf_alerts[0].level == AlertLevel.WARNING
    
    def test_catalog_alerts(self, monitor):
        """Test catalog-related alert generation."""
        # Set poor catalog metrics to trigger alerts
        monitor.record_catalog_metrics(
            total_technologies=100,
            missing_technologies=15,  # 15% missing - above threshold
            inconsistent_entries=8,   # 92% consistency - below threshold
            pending_review=60         # High pending count
        )
        
        # Check that catalog alerts were generated
        consistency_alerts = [a for a in monitor.alerts if a.category == "catalog_consistency"]
        missing_alerts = [a for a in monitor.alerts if a.category == "catalog_missing"]
        review_alerts = [a for a in monitor.alerts if a.category == "catalog_review"]
        
        assert len(consistency_alerts) == 1
        assert consistency_alerts[0].level == AlertLevel.ERROR
        
        assert len(missing_alerts) == 1
        assert missing_alerts[0].level == AlertLevel.WARNING
        
        assert len(review_alerts) == 1
        assert review_alerts[0].level == AlertLevel.INFO
    
    def test_satisfaction_alerts(self, monitor):
        """Test user satisfaction alert generation."""
        # Set low satisfaction to trigger alert
        monitor.record_user_satisfaction(
            session_id="test_session",
            relevance_score=2.0,
            accuracy_score=2.5,
            completeness_score=3.0,  # Overall: 2.5 - below threshold
            feedback="Poor recommendations"
        )
        
        # Check that satisfaction alert was generated
        sat_alerts = [a for a in monitor.alerts if a.category == "user_satisfaction"]
        assert len(sat_alerts) == 1
        assert sat_alerts[0].level == AlertLevel.WARNING
    
    def test_get_recent_metrics(self, monitor):
        """Test getting recent metrics."""
        # Add some metrics with different timestamps
        now = datetime.now()
        old_metric = TechStackMetric(
            timestamp=now - timedelta(hours=25),  # Older than 24 hours
            metric_type=MetricType.ACCURACY,
            name="test_metric",
            value=0.8,
            metadata={}
        )
        recent_metric = TechStackMetric(
            timestamp=now - timedelta(hours=1),   # Within 24 hours
            metric_type=MetricType.ACCURACY,
            name="test_metric",
            value=0.9,
            metadata={}
        )
        
        monitor.metrics.extend([old_metric, recent_metric])
        
        # Get recent metrics (last 24 hours)
        recent = monitor._get_recent_metrics(hours=24)
        
        assert len(recent) == 1
        assert recent[0] == recent_metric
    
    def test_quality_dashboard_data(self, monitor):
        """Test getting quality dashboard data."""
        # Add some test metrics
        monitor.record_extraction_accuracy(
            session_id="test_session_1",
            extracted_count=8,
            expected_count=10,
            explicit_tech_included=7,
            explicit_tech_total=8,
            processing_time=15.0
        )
        
        monitor.record_user_satisfaction(
            session_id="test_session_1",
            relevance_score=4.0,
            accuracy_score=4.5,
            completeness_score=4.0
        )
        
        # Get dashboard data
        dashboard_data = monitor.get_quality_dashboard_data()
        
        assert 'summary' in dashboard_data
        assert 'accuracy' in dashboard_data
        assert 'performance' in dashboard_data
        assert 'satisfaction' in dashboard_data
        assert 'alerts' in dashboard_data
        assert 'recommendations' in dashboard_data
        assert 'metrics_by_hour' in dashboard_data
        
        # Check summary data
        summary = dashboard_data['summary']
        assert summary['total_sessions'] == 1
        assert summary['total_alerts'] >= 0
        
        # Check accuracy data
        accuracy = dashboard_data['accuracy']
        assert accuracy['average'] == 0.8  # 8/10
        assert accuracy['samples'] == 1
    
    def test_calculate_trend(self, monitor):
        """Test trend calculation."""
        # Create metrics with improving trend
        metrics = []
        for i in range(10):
            metric = TechStackMetric(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_type=MetricType.ACCURACY,
                name="test_metric",
                value=0.7 + (i * 0.02),  # Improving from 0.7 to 0.88
                metadata={}
            )
            metrics.append(metric)
        
        trend = monitor._calculate_trend(metrics)
        assert trend == "improving"
        
        # Create metrics with declining trend
        declining_metrics = []
        for i in range(10):
            metric = TechStackMetric(
                timestamp=datetime.now() - timedelta(hours=i),
                metric_type=MetricType.ACCURACY,
                name="test_metric",
                value=0.9 - (i * 0.02),  # Declining from 0.9 to 0.72
                metadata={}
            )
            declining_metrics.append(metric)
        
        trend = monitor._calculate_trend(declining_metrics)
        assert trend == "declining"
    
    def test_export_metrics(self, monitor, tmp_path):
        """Test metrics export functionality."""
        # Add some test metrics
        monitor.record_extraction_accuracy(
            session_id="test_session",
            extracted_count=8,
            expected_count=10,
            explicit_tech_included=7,
            explicit_tech_total=8,
            processing_time=15.0
        )
        
        # Export metrics
        export_file = tmp_path / "test_metrics.json"
        monitor.export_metrics(str(export_file), hours=24)
        
        # Check that file was created
        assert export_file.exists()
        
        # Check file content
        import json
        with open(export_file) as f:
            data = json.load(f)
        
        assert 'export_timestamp' in data
        assert 'time_window_hours' in data
        assert 'metrics' in data
        assert 'alerts' in data
        assert 'recommendations' in data
        assert 'summary' in data
        
        assert len(data['metrics']) == 3  # accuracy, inclusion, processing time
    
    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, monitor):
        """Test starting and stopping monitoring."""
        # Test start monitoring
        await monitor.start_monitoring()
        assert monitor.monitoring_active is True
        
        # Test stop monitoring
        await monitor.stop_monitoring()
        assert monitor.monitoring_active is False
    
    def test_group_metrics_by_hour(self, monitor):
        """Test grouping metrics by hour."""
        # Add metrics with different timestamps
        now = datetime.now()
        
        # Add metrics for current hour
        for i in range(3):
            metric = TechStackMetric(
                timestamp=now - timedelta(minutes=i*10),
                metric_type=MetricType.ACCURACY,
                name="test_metric",
                value=0.8 + (i * 0.05),
                metadata={}
            )
            monitor.metrics.append(metric)
        
        # Add metrics for previous hour
        prev_hour = now - timedelta(hours=1)
        for i in range(2):
            metric = TechStackMetric(
                timestamp=prev_hour - timedelta(minutes=i*10),
                metric_type=MetricType.ACCURACY,
                name="test_metric",
                value=0.7 + (i * 0.05),
                metadata={}
            )
            monitor.metrics.append(metric)
        
        # Group by hour
        hourly_data = monitor._group_metrics_by_hour(monitor.metrics)
        
        assert len(hourly_data) == 2  # Two different hours
        
        # Check that averages were calculated
        for hour_key, metrics in hourly_data.items():
            assert 'test_metric' in metrics
            assert isinstance(metrics['test_metric'], float)


class TestTechStackMetric:
    """Test cases for TechStackMetric dataclass."""
    
    def test_metric_creation(self):
        """Test creating a metric."""
        timestamp = datetime.now()
        metric = TechStackMetric(
            timestamp=timestamp,
            metric_type=MetricType.ACCURACY,
            name="test_metric",
            value=0.85,
            metadata={"test": "data"},
            session_id="test_session"
        )
        
        assert metric.timestamp == timestamp
        assert metric.metric_type == MetricType.ACCURACY
        assert metric.name == "test_metric"
        assert metric.value == 0.85
        assert metric.metadata == {"test": "data"}
        assert metric.session_id == "test_session"
    
    def test_metric_to_dict(self):
        """Test converting metric to dictionary."""
        timestamp = datetime.now()
        metric = TechStackMetric(
            timestamp=timestamp,
            metric_type=MetricType.PERFORMANCE,
            name="processing_time",
            value=15.5,
            metadata={"unit": "seconds"}
        )
        
        data = metric.to_dict()
        
        assert data['timestamp'] == timestamp.isoformat()
        assert data['metric_type'] == 'performance'
        assert data['name'] == 'processing_time'
        assert data['value'] == 15.5
        assert data['metadata'] == {"unit": "seconds"}


class TestQualityAlert:
    """Test cases for QualityAlert dataclass."""
    
    def test_alert_creation(self):
        """Test creating an alert."""
        timestamp = datetime.now()
        alert = QualityAlert(
            timestamp=timestamp,
            level=AlertLevel.WARNING,
            category="test_category",
            message="Test alert message",
            details={"test": "details"},
            session_id="test_session"
        )
        
        assert alert.timestamp == timestamp
        assert alert.level == AlertLevel.WARNING
        assert alert.category == "test_category"
        assert alert.message == "Test alert message"
        assert alert.details == {"test": "details"}
        assert alert.session_id == "test_session"
        assert alert.resolved is False
    
    def test_alert_to_dict(self):
        """Test converting alert to dictionary."""
        timestamp = datetime.now()
        alert = QualityAlert(
            timestamp=timestamp,
            level=AlertLevel.ERROR,
            category="accuracy",
            message="Low accuracy detected",
            details={"accuracy": 0.6}
        )
        
        data = alert.to_dict()
        
        assert data['timestamp'] == timestamp.isoformat()
        assert data['level'] == 'error'
        assert data['category'] == 'accuracy'
        assert data['message'] == 'Low accuracy detected'
        assert data['details'] == {"accuracy": 0.6}


class TestPerformanceRecommendation:
    """Test cases for PerformanceRecommendation dataclass."""
    
    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        rec = PerformanceRecommendation(
            category="performance",
            priority="high",
            description="Optimize processing time",
            impact="Improved user experience",
            implementation="Add caching layer",
            metrics_supporting=["processing_time", "response_time"]
        )
        
        assert rec.category == "performance"
        assert rec.priority == "high"
        assert rec.description == "Optimize processing time"
        assert rec.impact == "Improved user experience"
        assert rec.implementation == "Add caching layer"
        assert rec.metrics_supporting == ["processing_time", "response_time"]
    
    def test_recommendation_to_dict(self):
        """Test converting recommendation to dictionary."""
        rec = PerformanceRecommendation(
            category="accuracy",
            priority="medium",
            description="Improve extraction accuracy",
            impact="Better technology recommendations",
            implementation="Enhance NER model",
            metrics_supporting=["extraction_accuracy"]
        )
        
        data = rec.to_dict()
        
        assert data['category'] == 'accuracy'
        assert data['priority'] == 'medium'
        assert data['description'] == 'Improve extraction accuracy'
        assert data['impact'] == 'Better technology recommendations'
        assert data['implementation'] == 'Enhance NER model'
        assert data['metrics_supporting'] == ['extraction_accuracy']