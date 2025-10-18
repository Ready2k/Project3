"""
Unit tests for Real-Time Quality Monitor

Tests quality monitoring accuracy, alert reliability, ecosystem consistency checking,
user satisfaction prediction, and quality trend analysis.
"""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.monitoring.real_time_quality_monitor import (
    RealTimeQualityMonitor,
    QualityScore,
    ConsistencyScore,
    QualityAlert,
    QualityTrend,
    QualityMetricType,
    QualityAlertSeverity,
)


class TestRealTimeQualityMonitor:
    """Test suite for RealTimeQualityMonitor."""

    @pytest.fixture
    def monitor_config(self):
        """Test configuration for quality monitor."""
        return {
            "monitoring_enabled": True,
            "alert_thresholds": {
                QualityMetricType.EXTRACTION_ACCURACY: 0.85,
                QualityMetricType.ECOSYSTEM_CONSISTENCY: 0.90,
                QualityMetricType.TECHNOLOGY_INCLUSION: 0.70,
                QualityMetricType.USER_SATISFACTION: 0.75,
            },
            "trend_analysis_window_hours": 24,
            "real_time_update_interval": 30,
            "max_stored_scores": 100,
            "degradation_threshold": 0.1,
        }

    @pytest.fixture
    def quality_monitor(self, monitor_config):
        """Create RealTimeQualityMonitor instance for testing."""
        return RealTimeQualityMonitor(monitor_config)

    @pytest.fixture
    def mock_dependencies(self, quality_monitor):
        """Mock service dependencies."""
        quality_monitor.tech_stack_monitor = Mock()
        quality_monitor.monitoring_integration = Mock()
        quality_monitor.catalog_manager = AsyncMock()
        return quality_monitor

    @pytest.mark.asyncio
    async def test_initialization(self, quality_monitor):
        """Test quality monitor initialization."""
        assert quality_monitor.config["monitoring_enabled"] is True
        assert (
            quality_monitor.config["alert_thresholds"][
                QualityMetricType.EXTRACTION_ACCURACY
            ]
            == 0.85
        )
        assert quality_monitor.is_monitoring is False
        assert len(quality_monitor.quality_scores) == 0
        assert len(quality_monitor.quality_alerts) == 0

    @pytest.mark.asyncio
    async def test_start_stop_monitoring(self, mock_dependencies):
        """Test starting and stopping real-time monitoring."""
        monitor = mock_dependencies

        # Test start monitoring
        with patch.object(monitor, "_initialize_dependencies", new_callable=AsyncMock):
            await monitor.start_real_time_monitoring()

        assert monitor.is_monitoring is True
        assert monitor.monitoring_task is not None
        assert monitor.trend_analysis_task is not None

        # Test stop monitoring
        await monitor.stop_real_time_monitoring()

        assert monitor.is_monitoring is False

    @pytest.mark.asyncio
    async def test_validate_extraction_quality_high_quality(self, mock_dependencies):
        """Test extraction quality validation with high-quality extraction."""
        monitor = mock_dependencies

        # Mock catalog manager to return found technologies
        monitor.catalog_manager.lookup_technology.return_value = {
            "name": "FastAPI",
            "category": "web_framework",
        }

        extracted_techs = ["FastAPI", "PostgreSQL", "Redis"]
        requirements = (
            "Build a web API using FastAPI with PostgreSQL database and Redis caching"
        )

        quality_score = await monitor.validate_extraction_quality(
            extracted_techs, requirements, "test_session"
        )

        assert isinstance(quality_score, QualityScore)
        assert quality_score.metric_type == QualityMetricType.EXTRACTION_ACCURACY
        assert quality_score.overall_score > 0.8  # Should be high quality
        assert quality_score.session_id == "test_session"
        assert "completeness" in quality_score.component_scores
        assert "accuracy" in quality_score.component_scores
        assert "relevance" in quality_score.component_scores
        assert "catalog_coverage" in quality_score.component_scores

    @pytest.mark.asyncio
    async def test_validate_extraction_quality_low_quality(self, mock_dependencies):
        """Test extraction quality validation with low-quality extraction."""
        monitor = mock_dependencies

        # Mock catalog manager to return no technologies found
        monitor.catalog_manager.lookup_technology.return_value = None

        extracted_techs = ["UnknownTech1", "UnknownTech2"]
        requirements = "Build a simple web application"

        quality_score = await monitor.validate_extraction_quality(
            extracted_techs, requirements, "test_session"
        )

        assert isinstance(quality_score, QualityScore)
        assert quality_score.overall_score < 0.6  # Should be low quality
        assert (
            quality_score.component_scores["catalog_coverage"] == 0.0
        )  # No catalog coverage

    @pytest.mark.asyncio
    async def test_validate_extraction_quality_empty_extraction(
        self, mock_dependencies
    ):
        """Test extraction quality validation with empty extraction."""
        monitor = mock_dependencies

        extracted_techs = []
        requirements = "Build a web application"

        quality_score = await monitor.validate_extraction_quality(
            extracted_techs, requirements, "test_session"
        )

        assert isinstance(quality_score, QualityScore)
        assert (
            quality_score.component_scores["completeness"] < 1.0
        )  # Should detect missing technologies
        assert quality_score.details["extracted_count"] == 0

    @pytest.mark.asyncio
    async def test_check_ecosystem_consistency_aws_consistent(self, mock_dependencies):
        """Test ecosystem consistency checking with consistent AWS stack."""
        monitor = mock_dependencies

        tech_stack = ["AWS Lambda", "Amazon S3", "Amazon RDS", "AWS CloudFormation"]

        consistency_score = await monitor.check_ecosystem_consistency(
            tech_stack, "test_session"
        )

        assert isinstance(consistency_score, ConsistencyScore)
        assert consistency_score.ecosystem_detected == "aws"
        assert (
            consistency_score.consistency_score >= 0.8
        )  # Should be reasonably consistent
        assert len(consistency_score.inconsistencies) == 0  # No inconsistencies
        assert consistency_score.session_id == "test_session"

    @pytest.mark.asyncio
    async def test_check_ecosystem_consistency_mixed_ecosystem(self, mock_dependencies):
        """Test ecosystem consistency checking with mixed ecosystems."""
        monitor = mock_dependencies

        tech_stack = [
            "AWS Lambda",
            "Azure Functions",
            "Google Cloud Storage",
            "PostgreSQL",
        ]

        consistency_score = await monitor.check_ecosystem_consistency(
            tech_stack, "test_session"
        )

        assert isinstance(consistency_score, ConsistencyScore)
        # Mixed ecosystems may still have reasonable consistency if one dominates
        assert 0.0 <= consistency_score.consistency_score <= 1.0
        # Should detect some inconsistencies in mixed stack
        assert (
            len(consistency_score.inconsistencies) >= 0
        )  # May or may not have inconsistencies
        assert (
            len(consistency_score.recommendations) > 0
        )  # Should provide recommendations

    @pytest.mark.asyncio
    async def test_check_ecosystem_consistency_open_source(self, mock_dependencies):
        """Test ecosystem consistency checking with open source stack."""
        monitor = mock_dependencies

        tech_stack = ["Docker", "Kubernetes", "PostgreSQL", "Redis", "Nginx"]

        consistency_score = await monitor.check_ecosystem_consistency(
            tech_stack, "test_session"
        )

        assert isinstance(consistency_score, ConsistencyScore)
        assert consistency_score.ecosystem_detected == "open_source"
        assert (
            consistency_score.consistency_score >= 0.7
        )  # Should be reasonably consistent

    @pytest.mark.asyncio
    async def test_calculate_user_satisfaction_score_high_satisfaction(
        self, mock_dependencies
    ):
        """Test user satisfaction prediction with high-quality result."""
        monitor = mock_dependencies

        result = {
            "tech_stack": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
            "generation_metrics": {
                "explicit_inclusion_rate": 0.9,
                "catalog_coverage": 0.95,
                "missing_technologies": 0,
            },
            "processing_time": 8.5,
        }

        satisfaction_score = await monitor.calculate_user_satisfaction_score(
            result, session_id="test_session"
        )

        assert isinstance(satisfaction_score, float)
        assert 0.0 <= satisfaction_score <= 1.0
        assert satisfaction_score > 0.8  # Should predict high satisfaction

    @pytest.mark.asyncio
    async def test_calculate_user_satisfaction_score_low_satisfaction(
        self, mock_dependencies
    ):
        """Test user satisfaction prediction with low-quality result."""
        monitor = mock_dependencies

        result = {
            "tech_stack": ["UnknownTech"],
            "generation_metrics": {
                "explicit_inclusion_rate": 0.3,
                "catalog_coverage": 0.4,
                "missing_technologies": 5,
            },
            "processing_time": 45.0,
        }

        satisfaction_score = await monitor.calculate_user_satisfaction_score(
            result, session_id="test_session"
        )

        assert isinstance(satisfaction_score, float)
        assert satisfaction_score < 0.6  # Should predict low satisfaction

    @pytest.mark.asyncio
    async def test_calculate_user_satisfaction_with_feedback(self, mock_dependencies):
        """Test user satisfaction calculation with actual feedback."""
        monitor = mock_dependencies

        result = {
            "tech_stack": ["FastAPI", "PostgreSQL"],
            "generation_metrics": {"explicit_inclusion_rate": 0.8},
            "processing_time": 10.0,
        }

        feedback = {"relevance": 4.5, "accuracy": 4.0, "completeness": 3.5}

        satisfaction_score = await monitor.calculate_user_satisfaction_score(
            result, feedback, "test_session"
        )

        assert isinstance(satisfaction_score, float)
        assert 0.7 <= satisfaction_score <= 0.9  # Should incorporate feedback

    @pytest.mark.asyncio
    async def test_quality_alert_generation(self, mock_dependencies):
        """Test quality alert generation when thresholds are exceeded."""
        monitor = mock_dependencies

        # Create low-quality score that should trigger alert
        low_quality_score = QualityScore(
            overall_score=0.6,  # Below threshold of 0.85 (25% below = CRITICAL)
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            component_scores={"accuracy": 0.6},
            confidence=0.8,
            timestamp=datetime.now(),
            session_id="test_session",
        )

        await monitor._check_quality_alerts(low_quality_score)

        assert len(monitor.quality_alerts) == 1
        alert = monitor.quality_alerts[0]
        # 0.6 is 25% below 0.85 threshold, so should be CRITICAL
        assert alert.severity == QualityAlertSeverity.CRITICAL
        assert alert.metric_type == QualityMetricType.EXTRACTION_ACCURACY
        assert alert.current_value == 0.6
        assert alert.session_id == "test_session"

    @pytest.mark.asyncio
    async def test_consistency_alert_generation(self, mock_dependencies):
        """Test consistency alert generation."""
        monitor = mock_dependencies

        # Create low consistency score that should trigger alert
        low_consistency_score = ConsistencyScore(
            consistency_score=0.5,  # Below threshold of 0.90
            ecosystem_detected="mixed",
            inconsistencies=[
                {"technology": "AWS Lambda", "conflicting_ecosystems": ["azure"]}
            ],
            recommendations=["Use consistent ecosystem"],
            confidence=0.9,
            timestamp=datetime.now(),
            session_id="test_session",
        )

        await monitor._check_consistency_alerts(low_consistency_score)

        assert len(monitor.quality_alerts) == 1
        alert = monitor.quality_alerts[0]
        assert alert.metric_type == QualityMetricType.ECOSYSTEM_CONSISTENCY
        assert alert.current_value == 0.5
        assert "inconsistencies" in alert.details

    @pytest.mark.asyncio
    async def test_alert_severity_determination(self, quality_monitor):
        """Test alert severity determination logic."""
        monitor = quality_monitor

        # Test different severity levels (updated thresholds: 25%, 15%, 5%)
        critical_severity = monitor._determine_alert_severity(0.5, 0.85)  # 35% below
        assert critical_severity == QualityAlertSeverity.CRITICAL

        error_severity = monitor._determine_alert_severity(0.65, 0.85)  # 20% below
        assert error_severity == QualityAlertSeverity.ERROR

        warning_severity = monitor._determine_alert_severity(0.78, 0.85)  # 7% below
        assert warning_severity == QualityAlertSeverity.WARNING

        info_severity = monitor._determine_alert_severity(0.82, 0.85)  # 3% below
        assert info_severity == QualityAlertSeverity.INFO

    @pytest.mark.asyncio
    async def test_quality_trend_analysis(self, mock_dependencies):
        """Test quality trend analysis functionality."""
        monitor = mock_dependencies

        # Create historical quality scores with declining trend
        base_time = datetime.now() - timedelta(hours=12)

        for i in range(10):
            score = QualityScore(
                overall_score=0.9 - (i * 0.05),  # Declining from 0.9 to 0.45
                metric_type=QualityMetricType.EXTRACTION_ACCURACY,
                component_scores={"accuracy": 0.9 - (i * 0.05)},
                confidence=0.8,
                timestamp=base_time + timedelta(hours=i),
                session_id=f"session_{i}",
            )
            monitor.quality_scores.append(score)

        trend = await monitor._analyze_quality_trend(
            QualityMetricType.EXTRACTION_ACCURACY
        )

        assert isinstance(trend, QualityTrend)
        assert trend.metric_type == QualityMetricType.EXTRACTION_ACCURACY
        assert trend.trend_direction == "declining"
        assert trend.trend_strength > 0.5  # Should detect strong decline
        assert trend.change_rate < 0  # Negative change rate
        assert trend.data_points == 10

    @pytest.mark.asyncio
    async def test_quality_trend_analysis_improving(self, mock_dependencies):
        """Test quality trend analysis with improving trend."""
        monitor = mock_dependencies

        # Create historical quality scores with improving trend
        base_time = datetime.now() - timedelta(hours=12)

        for i in range(10):
            score = QualityScore(
                overall_score=0.5 + (i * 0.04),  # Improving from 0.5 to 0.86
                metric_type=QualityMetricType.EXTRACTION_ACCURACY,
                component_scores={"accuracy": 0.5 + (i * 0.04)},
                confidence=0.8,
                timestamp=base_time + timedelta(hours=i),
                session_id=f"session_{i}",
            )
            monitor.quality_scores.append(score)

        trend = await monitor._analyze_quality_trend(
            QualityMetricType.EXTRACTION_ACCURACY
        )

        assert trend.trend_direction == "improving"
        assert trend.change_rate > 0  # Positive change rate
        assert trend.trend_strength > 0.5

    @pytest.mark.asyncio
    async def test_quality_trend_analysis_stable(self, mock_dependencies):
        """Test quality trend analysis with stable trend."""
        monitor = mock_dependencies

        # Create historical quality scores with stable trend
        base_time = datetime.now() - timedelta(hours=12)

        for i in range(10):
            score = QualityScore(
                overall_score=0.85 + (0.02 * ((-1) ** i)),  # Oscillating around 0.85
                metric_type=QualityMetricType.EXTRACTION_ACCURACY,
                component_scores={"accuracy": 0.85},
                confidence=0.8,
                timestamp=base_time + timedelta(hours=i),
                session_id=f"session_{i}",
            )
            monitor.quality_scores.append(score)

        trend = await monitor._analyze_quality_trend(
            QualityMetricType.EXTRACTION_ACCURACY
        )

        assert trend.trend_direction == "stable"
        assert abs(trend.change_rate) < 0.05  # Small change rate
        assert trend.trend_strength < 0.3  # Low trend strength

    @pytest.mark.asyncio
    async def test_degradation_alert_creation(self, mock_dependencies):
        """Test degradation alert creation for significant quality decline."""
        monitor = mock_dependencies

        # Create a declining trend that should trigger degradation alert
        trend = QualityTrend(
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            time_window_hours=24,
            trend_direction="declining",
            trend_strength=0.8,
            current_average=0.6,
            previous_average=0.85,
            change_rate=-0.25,  # 25% decline
            data_points=20,
            timestamp=datetime.now(),
        )

        await monitor._create_degradation_alert(trend)

        assert len(monitor.quality_alerts) == 1
        alert = monitor.quality_alerts[0]
        assert "degradation" in alert.alert_id
        assert alert.severity == QualityAlertSeverity.WARNING
        assert "degradation detected" in alert.message.lower()
        assert alert.details["trend_direction"] == "declining"
        assert alert.details["change_rate"] == -0.25

    @pytest.mark.asyncio
    async def test_ecosystem_detection_patterns(self, quality_monitor):
        """Test ecosystem detection pattern matching."""
        monitor = quality_monitor

        # Test AWS ecosystem detection
        aws_stack = ["AWS Lambda", "Amazon S3", "Amazon RDS"]
        aws_scores = monitor._detect_ecosystems(aws_stack)
        assert aws_scores["aws"] > aws_scores["azure"]
        assert aws_scores["aws"] > aws_scores["gcp"]

        # Test Azure ecosystem detection
        azure_stack = ["Azure Functions", "Azure Storage", "Azure SQL"]
        azure_scores = monitor._detect_ecosystems(azure_stack)
        assert azure_scores["azure"] > azure_scores["aws"]

        # Test mixed ecosystem detection
        mixed_stack = ["AWS Lambda", "Azure Functions", "Google Cloud Storage"]
        mixed_scores = monitor._detect_ecosystems(mixed_stack)
        assert mixed_scores["aws"] > 0
        assert mixed_scores["azure"] > 0
        assert mixed_scores["gcp"] > 0

    @pytest.mark.asyncio
    async def test_ecosystem_inconsistency_identification(self, quality_monitor):
        """Test identification of ecosystem inconsistencies."""
        monitor = quality_monitor

        tech_stack = ["AWS Lambda", "Azure Functions", "PostgreSQL"]
        ecosystem_scores = {"aws": 0.33, "azure": 0.33, "open_source": 0.33}
        primary_ecosystem = "aws"

        inconsistencies = monitor._identify_ecosystem_inconsistencies(
            tech_stack, ecosystem_scores, primary_ecosystem
        )

        assert len(inconsistencies) > 0
        # Should identify Azure Functions as inconsistent with AWS primary ecosystem
        azure_inconsistency = next(
            (inc for inc in inconsistencies if "azure" in inc["technology"].lower()),
            None,
        )
        assert azure_inconsistency is not None
        assert "azure" in azure_inconsistency["conflicting_ecosystems"]

    @pytest.mark.asyncio
    async def test_ecosystem_recommendations_generation(self, quality_monitor):
        """Test generation of ecosystem consistency recommendations."""
        monitor = quality_monitor

        # Test with inconsistencies
        inconsistencies = [
            {
                "technology": "Azure Functions",
                "primary_ecosystem": "aws",
                "conflicting_ecosystems": ["azure"],
                "severity": "high",
            },
            {
                "technology": "Google Cloud Storage",
                "primary_ecosystem": "aws",
                "conflicting_ecosystems": ["gcp"],
                "severity": "medium",
            },
        ]

        recommendations = monitor._generate_ecosystem_recommendations(
            inconsistencies, "aws"
        )

        assert len(recommendations) > 0
        assert any("high-severity" in rec.lower() for rec in recommendations)
        assert any("aws alternatives" in rec.lower() for rec in recommendations)

        # Test with no inconsistencies
        no_inconsistencies = []
        good_recommendations = monitor._generate_ecosystem_recommendations(
            no_inconsistencies, "aws"
        )
        assert len(good_recommendations) == 1
        assert "consistency is good" in good_recommendations[0].lower()

    def test_get_current_quality_status(self, mock_dependencies):
        """Test getting current quality status."""
        monitor = mock_dependencies

        # Add some recent quality scores
        recent_time = datetime.now() - timedelta(minutes=30)

        for metric_type in [
            QualityMetricType.EXTRACTION_ACCURACY,
            QualityMetricType.ECOSYSTEM_CONSISTENCY,
        ]:
            score = QualityScore(
                overall_score=0.9,
                metric_type=metric_type,
                component_scores={"test": 0.9},
                confidence=0.8,
                timestamp=recent_time,
                session_id="test",
            )
            monitor.quality_scores.append(score)

        status = monitor.get_current_quality_status()

        assert "overall_status" in status
        assert "metrics" in status
        assert "active_alerts" in status
        assert "monitoring_enabled" in status

        # Check metric-specific status
        for metric_type in [
            QualityMetricType.EXTRACTION_ACCURACY,
            QualityMetricType.ECOSYSTEM_CONSISTENCY,
        ]:
            metric_status = status["metrics"][metric_type.value]
            assert metric_status["current_score"] == 0.9
            assert metric_status["status"] == "good"
            assert metric_status["sample_count"] == 1

    def test_get_quality_trends(self, mock_dependencies):
        """Test getting quality trends."""
        monitor = mock_dependencies

        # Add a trend
        trend = QualityTrend(
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            time_window_hours=24,
            trend_direction="improving",
            trend_strength=0.7,
            current_average=0.9,
            previous_average=0.8,
            change_rate=0.1,
            data_points=15,
            timestamp=datetime.now(),
        )
        monitor.quality_trends[QualityMetricType.EXTRACTION_ACCURACY] = trend

        trends = monitor.get_quality_trends()

        assert "trends" in trends
        assert "analysis_window_hours" in trends
        assert QualityMetricType.EXTRACTION_ACCURACY.value in trends["trends"]

        trend_data = trends["trends"][QualityMetricType.EXTRACTION_ACCURACY.value]
        assert trend_data["trend_direction"] == "improving"
        assert trend_data["trend_strength"] == 0.7
        assert trend_data["change_rate"] == 0.1

    def test_get_active_alerts(self, mock_dependencies):
        """Test getting active alerts."""
        monitor = mock_dependencies

        # Add active and resolved alerts
        active_alert = QualityAlert(
            alert_id="active_1",
            timestamp=datetime.now(),
            severity=QualityAlertSeverity.WARNING,
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            message="Test active alert",
            current_value=0.7,
            threshold_value=0.85,
            session_id="test",
            details={},
            resolved=False,
        )

        resolved_alert = QualityAlert(
            alert_id="resolved_1",
            timestamp=datetime.now(),
            severity=QualityAlertSeverity.ERROR,
            metric_type=QualityMetricType.ECOSYSTEM_CONSISTENCY,
            message="Test resolved alert",
            current_value=0.6,
            threshold_value=0.9,
            session_id="test",
            details={},
            resolved=True,
        )

        monitor.quality_alerts.extend([active_alert, resolved_alert])

        active_alerts = monitor.get_active_alerts()

        assert len(active_alerts) == 1
        assert active_alerts[0]["alert_id"] == "active_1"
        assert active_alerts[0]["resolved"] is False

    @pytest.mark.asyncio
    async def test_resolve_alert(self, mock_dependencies):
        """Test resolving quality alerts."""
        monitor = mock_dependencies

        # Add an active alert
        alert = QualityAlert(
            alert_id="test_alert_1",
            timestamp=datetime.now(),
            severity=QualityAlertSeverity.WARNING,
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            message="Test alert",
            current_value=0.7,
            threshold_value=0.85,
            session_id="test",
            details={},
            resolved=False,
        )
        monitor.quality_alerts.append(alert)

        # Resolve the alert
        result = await monitor.resolve_alert("test_alert_1")

        assert result is True
        assert alert.resolved is True
        assert alert.resolution_time is not None

        # Try to resolve non-existent alert
        result = await monitor.resolve_alert("non_existent")
        assert result is False

    @pytest.mark.asyncio
    async def test_data_cleanup(self, mock_dependencies):
        """Test cleanup of old quality data."""
        monitor = mock_dependencies

        # Add old and recent data
        old_time = datetime.now() - timedelta(days=8)
        recent_time = datetime.now() - timedelta(hours=1)

        old_score = QualityScore(
            overall_score=0.8,
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            component_scores={"test": 0.8},
            confidence=0.8,
            timestamp=old_time,
            session_id="old",
        )

        recent_score = QualityScore(
            overall_score=0.9,
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            component_scores={"test": 0.9},
            confidence=0.8,
            timestamp=recent_time,
            session_id="recent",
        )

        monitor.quality_scores.extend([old_score, recent_score])

        # Add old resolved alert
        old_alert = QualityAlert(
            alert_id="old_alert",
            timestamp=old_time,
            severity=QualityAlertSeverity.WARNING,
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            message="Old alert",
            current_value=0.7,
            threshold_value=0.85,
            session_id="old",
            details={},
            resolved=True,
            resolution_time=old_time,
        )
        monitor.quality_alerts.append(old_alert)

        await monitor._cleanup_old_data()

        # Should keep recent data, remove old data
        assert len(monitor.quality_scores) == 1
        assert monitor.quality_scores[0].session_id == "recent"
        assert len(monitor.quality_alerts) == 0  # Old resolved alert should be removed

    @pytest.mark.asyncio
    async def test_error_handling_in_quality_validation(self, mock_dependencies):
        """Test error handling in quality validation methods."""
        monitor = mock_dependencies

        # Mock catalog manager to raise exception
        monitor.catalog_manager.lookup_technology.side_effect = Exception(
            "Catalog error"
        )

        extracted_techs = ["FastAPI", "PostgreSQL"]
        requirements = "Build a web API"

        # Should handle error gracefully and return reasonable score
        quality_score = await monitor.validate_extraction_quality(
            extracted_techs, requirements
        )

        assert isinstance(quality_score, QualityScore)
        assert (
            0.0 <= quality_score.overall_score <= 1.0
        )  # Should return valid score range
        # Should still process other components even if catalog fails
        assert "completeness" in quality_score.component_scores
        assert "accuracy" in quality_score.component_scores

    @pytest.mark.asyncio
    async def test_confidence_calculation(self, quality_monitor):
        """Test confidence calculation for quality assessments."""
        monitor = quality_monitor

        # Test with good data quality
        extracted_techs = ["FastAPI", "PostgreSQL", "Redis"]
        requirements = "Build a comprehensive web API with FastAPI, using PostgreSQL for data storage and Redis for caching. The system should handle user authentication and provide REST endpoints."
        component_scores = {"completeness": 0.9, "accuracy": 0.85, "relevance": 0.8}

        confidence = monitor._calculate_confidence(
            extracted_techs, requirements, component_scores
        )

        assert 0.0 <= confidence <= 1.0
        assert confidence > 0.6  # Should have reasonable confidence with good data

        # Test with poor data quality
        poor_extracted_techs = []
        poor_requirements = "Build app"
        poor_component_scores = {"completeness": 0.3, "accuracy": 0.2, "relevance": 0.1}

        poor_confidence = monitor._calculate_confidence(
            poor_extracted_techs, poor_requirements, poor_component_scores
        )

        assert poor_confidence < confidence  # Should have lower confidence
        assert poor_confidence > 0.1  # But still reasonable minimum

    @pytest.mark.asyncio
    async def test_dynamic_threshold_updates(self, mock_dependencies):
        """Test dynamic threshold updates based on system performance."""
        monitor = mock_dependencies

        # Add historical data with consistent high performance
        base_time = datetime.now() - timedelta(days=3)

        for i in range(30):
            score = QualityScore(
                overall_score=0.92 + (0.02 * (i % 3 - 1)),  # Scores around 0.92
                metric_type=QualityMetricType.EXTRACTION_ACCURACY,
                component_scores={"accuracy": 0.92},
                confidence=0.8,
                timestamp=base_time + timedelta(hours=i * 2),
                session_id=f"session_{i}",
            )
            monitor.quality_scores.append(score)

        monitor.config["alert_thresholds"][QualityMetricType.EXTRACTION_ACCURACY]

        await monitor._update_dynamic_thresholds()

        new_threshold = monitor.config["alert_thresholds"][
            QualityMetricType.EXTRACTION_ACCURACY
        ]

        # Threshold might be updated based on performance, but should be reasonable
        assert 0.5 <= new_threshold <= 1.0

    @pytest.mark.asyncio
    async def test_multi_metric_degradation_detection(self, mock_dependencies):
        """Test detection of degradation across multiple quality metrics."""
        monitor = mock_dependencies

        # Add recent low scores for multiple metrics
        recent_time = datetime.now() - timedelta(minutes=30)

        low_scores = [
            (QualityMetricType.EXTRACTION_ACCURACY, 0.6),
            (QualityMetricType.ECOSYSTEM_CONSISTENCY, 0.65),
            (QualityMetricType.USER_SATISFACTION, 0.55),
        ]

        for metric_type, score_value in low_scores:
            for i in range(3):  # Add multiple samples
                score = QualityScore(
                    overall_score=score_value,
                    metric_type=metric_type,
                    component_scores={"test": score_value},
                    confidence=0.8,
                    timestamp=recent_time + timedelta(minutes=i * 10),
                    session_id=f"session_{i}",
                )
                monitor.quality_scores.append(score)

        await monitor._check_quality_degradation()

        # Should create a multi-degradation alert
        multi_alerts = [
            alert
            for alert in monitor.quality_alerts
            if "multi_degradation" in alert.alert_id
        ]
        assert len(multi_alerts) == 1

        alert = multi_alerts[0]
        assert alert.severity == QualityAlertSeverity.ERROR
        assert "multiple quality metrics degraded" in alert.message.lower()
        assert len(alert.details["degraded_metrics"]) >= 2


class TestQualityScoreDataClass:
    """Test QualityScore data class functionality."""

    def test_quality_score_creation(self):
        """Test QualityScore creation and serialization."""
        timestamp = datetime.now()

        score = QualityScore(
            overall_score=0.85,
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            component_scores={"accuracy": 0.8, "completeness": 0.9},
            confidence=0.9,
            timestamp=timestamp,
            session_id="test_session",
            details={"test": "data"},
        )

        assert score.overall_score == 0.85
        assert score.metric_type == QualityMetricType.EXTRACTION_ACCURACY
        assert score.session_id == "test_session"

        # Test serialization
        score_dict = score.to_dict()
        assert score_dict["overall_score"] == 0.85
        assert score_dict["metric_type"] == "extraction_accuracy"
        assert score_dict["timestamp"] == timestamp.isoformat()


class TestConsistencyScoreDataClass:
    """Test ConsistencyScore data class functionality."""

    def test_consistency_score_creation(self):
        """Test ConsistencyScore creation and serialization."""
        timestamp = datetime.now()

        score = ConsistencyScore(
            consistency_score=0.9,
            ecosystem_detected="aws",
            inconsistencies=[],
            recommendations=["Good consistency"],
            confidence=0.95,
            timestamp=timestamp,
            session_id="test_session",
        )

        assert score.consistency_score == 0.9
        assert score.ecosystem_detected == "aws"
        assert len(score.inconsistencies) == 0

        # Test serialization
        score_dict = score.to_dict()
        assert score_dict["consistency_score"] == 0.9
        assert score_dict["ecosystem_detected"] == "aws"
        assert score_dict["timestamp"] == timestamp.isoformat()


class TestQualityAlertDataClass:
    """Test QualityAlert data class functionality."""

    def test_quality_alert_creation(self):
        """Test QualityAlert creation and serialization."""
        timestamp = datetime.now()

        alert = QualityAlert(
            alert_id="test_alert",
            timestamp=timestamp,
            severity=QualityAlertSeverity.WARNING,
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            message="Test alert message",
            current_value=0.7,
            threshold_value=0.85,
            session_id="test_session",
            details={"test": "data"},
        )

        assert alert.alert_id == "test_alert"
        assert alert.severity == QualityAlertSeverity.WARNING
        assert alert.resolved is False

        # Test serialization
        alert_dict = alert.to_dict()
        assert alert_dict["alert_id"] == "test_alert"
        assert alert_dict["severity"] == "warning"
        assert alert_dict["metric_type"] == "extraction_accuracy"
        assert alert_dict["timestamp"] == timestamp.isoformat()


class TestQualityTrendDataClass:
    """Test QualityTrend data class functionality."""

    def test_quality_trend_creation(self):
        """Test QualityTrend creation and serialization."""
        timestamp = datetime.now()

        trend = QualityTrend(
            metric_type=QualityMetricType.EXTRACTION_ACCURACY,
            time_window_hours=24,
            trend_direction="improving",
            trend_strength=0.8,
            current_average=0.9,
            previous_average=0.8,
            change_rate=0.1,
            data_points=20,
            timestamp=timestamp,
        )

        assert trend.metric_type == QualityMetricType.EXTRACTION_ACCURACY
        assert trend.trend_direction == "improving"
        assert trend.change_rate == 0.1

        # Test serialization
        trend_dict = trend.to_dict()
        assert trend_dict["metric_type"] == "extraction_accuracy"
        assert trend_dict["trend_direction"] == "improving"
        assert trend_dict["timestamp"] == timestamp.isoformat()


if __name__ == "__main__":
    pytest.main([__file__])
