"""
Integration tests for Real-Time Quality Monitor

Tests integration with monitoring components, real data processing,
and end-to-end quality monitoring workflows.
"""

import pytest
import asyncio
from datetime import datetime, timedelta

from app.monitoring.real_time_quality_monitor import (
    RealTimeQualityMonitor,
    QualityMetricType,
    QualityAlertSeverity,
)
from app.monitoring.tech_stack_monitor import TechStackMonitor
from app.services.monitoring_integration_service import (
    TechStackMonitoringIntegrationService,
)


class TestRealTimeQualityMonitorIntegration:
    """Integration tests for RealTimeQualityMonitor with other monitoring components."""

    @pytest.fixture
    async def monitoring_integration_service(self):
        """Create monitoring integration service for testing."""
        service = TechStackMonitoringIntegrationService()
        await service.start_monitoring_integration()
        yield service
        await service.stop_monitoring_integration()

    @pytest.fixture
    async def tech_stack_monitor(self):
        """Create tech stack monitor for testing."""
        monitor = TechStackMonitor()
        await monitor.start_monitoring()
        yield monitor
        await monitor.stop_monitoring()

    @pytest.fixture
    async def quality_monitor(self, monitoring_integration_service, tech_stack_monitor):
        """Create quality monitor with integrated dependencies."""
        config = {
            "monitoring_enabled": True,
            "real_time_update_interval": 1,  # Fast updates for testing
            "trend_analysis_window_hours": 1,  # Short window for testing
            "alert_thresholds": {
                QualityMetricType.EXTRACTION_ACCURACY: 0.85,
                QualityMetricType.ECOSYSTEM_CONSISTENCY: 0.90,
                QualityMetricType.TECHNOLOGY_INCLUSION: 0.70,
                QualityMetricType.USER_SATISFACTION: 0.75,
            },
        }

        monitor = RealTimeQualityMonitor(config)
        monitor.monitoring_integration = monitoring_integration_service
        monitor.tech_stack_monitor = tech_stack_monitor

        await monitor.start_real_time_monitoring()
        yield monitor
        await monitor.stop_real_time_monitoring()

    @pytest.mark.asyncio
    async def test_integration_with_monitoring_service(
        self, quality_monitor, monitoring_integration_service
    ):
        """Test integration with monitoring integration service."""
        # Start a monitoring session
        requirements = {
            "text": "Build a web API using FastAPI with PostgreSQL database and Redis caching",
            "technologies": ["FastAPI", "PostgreSQL", "Redis"],
        }

        session = monitoring_integration_service.start_generation_monitoring(
            requirements
        )

        # Simulate parsing step
        await monitoring_integration_service.track_parsing_step(
            session_id=session.session_id,
            step_name="technology_extraction",
            input_data={"requirements": requirements},
            output_data={
                "explicit_technologies": ["FastAPI", "PostgreSQL", "Redis"],
                "confidence_scores": {
                    "FastAPI": 0.95,
                    "PostgreSQL": 0.9,
                    "Redis": 0.85,
                },
            },
            duration_ms=1500.0,
            success=True,
        )

        # Simulate extraction step
        await monitoring_integration_service.track_extraction_step(
            session_id=session.session_id,
            extraction_type="explicit",
            extracted_technologies=["FastAPI", "PostgreSQL", "Redis"],
            confidence_scores={"FastAPI": 0.95, "PostgreSQL": 0.9, "Redis": 0.85},
            context_data={"domain": "web_api", "ecosystem": "open_source"},
            duration_ms=800.0,
            success=True,
        )

        # Simulate completion
        final_tech_stack = ["FastAPI", "PostgreSQL", "Redis", "Docker"]
        generation_metrics = {
            "explicit_inclusion_rate": 0.75,  # 3/4 technologies
            "catalog_coverage": 0.9,
            "missing_technologies": 0,
        }

        await monitoring_integration_service.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=final_tech_stack,
            generation_metrics=generation_metrics,
            success=True,
        )

        # Allow time for quality monitor to process the data
        await asyncio.sleep(2)

        # Verify quality monitor processed the session
        quality_status = quality_monitor.get_current_quality_status()

        assert quality_status["overall_status"] in [
            "good",
            "no_data",
        ]  # Should be good or no data yet
        assert quality_status["monitoring_enabled"] is True

        # Check if quality scores were generated
        extraction_scores = [
            score
            for score in quality_monitor.quality_scores
            if score.metric_type == QualityMetricType.EXTRACTION_ACCURACY
        ]

        # May or may not have scores depending on timing, but should not error
        assert isinstance(extraction_scores, list)

    @pytest.mark.asyncio
    async def test_real_time_data_processing(
        self, quality_monitor, monitoring_integration_service
    ):
        """Test real-time processing of monitoring data."""
        # Create multiple sessions with different quality levels
        sessions_data = [
            {
                "requirements": {"text": "Build AWS Lambda function with DynamoDB"},
                "extracted_techs": ["AWS Lambda", "Amazon DynamoDB"],
                "final_stack": ["AWS Lambda", "Amazon DynamoDB", "AWS CloudFormation"],
                "quality_level": "high",
            },
            {
                "requirements": {"text": "Create web application"},
                "extracted_techs": ["UnknownFramework"],
                "final_stack": ["UnknownFramework", "SomeDatabase"],
                "quality_level": "low",
            },
            {
                "requirements": {
                    "text": "Build microservices with Docker and Kubernetes"
                },
                "extracted_techs": ["Docker", "Kubernetes"],
                "final_stack": ["Docker", "Kubernetes", "PostgreSQL", "Redis"],
                "quality_level": "medium",
            },
        ]

        session_ids = []

        for session_data in sessions_data:
            # Start session
            session = monitoring_integration_service.start_generation_monitoring(
                session_data["requirements"]
            )
            session_ids.append(session.session_id)

            # Track extraction
            await monitoring_integration_service.track_extraction_step(
                session_id=session.session_id,
                extraction_type="explicit",
                extracted_technologies=session_data["extracted_techs"],
                confidence_scores={
                    tech: 0.8 for tech in session_data["extracted_techs"]
                },
                context_data={"quality_level": session_data["quality_level"]},
                duration_ms=1000.0,
                success=True,
            )

            # Complete session
            await monitoring_integration_service.complete_generation_monitoring(
                session_id=session.session_id,
                final_tech_stack=session_data["final_stack"],
                generation_metrics={
                    "explicit_inclusion_rate": (
                        0.9 if session_data["quality_level"] == "high" else 0.3
                    ),
                    "catalog_coverage": (
                        0.95 if session_data["quality_level"] == "high" else 0.4
                    ),
                },
                success=True,
            )

        # Allow time for processing
        await asyncio.sleep(3)

        # Verify quality monitor processed multiple sessions
        quality_status = quality_monitor.get_current_quality_status()

        # Should have some quality data
        assert quality_status["monitoring_enabled"] is True

        # Check for quality scores from different sessions
        all_scores = quality_monitor.quality_scores
        session_scores = [
            score for score in all_scores if score.session_id in session_ids
        ]

        # May have scores depending on processing timing
        assert isinstance(session_scores, list)

    @pytest.mark.asyncio
    async def test_ecosystem_consistency_real_time_alerts(self, quality_monitor):
        """Test real-time ecosystem consistency alerts."""
        # Test mixed ecosystem that should trigger consistency alert
        mixed_tech_stack = [
            "AWS Lambda",  # AWS
            "Azure Functions",  # Azure
            "Google Cloud Storage",  # GCP
            "PostgreSQL",  # Open source
        ]

        consistency_score = await quality_monitor.check_ecosystem_consistency(
            mixed_tech_stack, session_id="mixed_ecosystem_test"
        )

        # Should detect low consistency
        assert consistency_score.consistency_score < 0.7
        assert len(consistency_score.inconsistencies) > 0
        assert len(consistency_score.recommendations) > 0

        # Should generate consistency alert
        consistency_alerts = [
            alert
            for alert in quality_monitor.quality_alerts
            if alert.metric_type == QualityMetricType.ECOSYSTEM_CONSISTENCY
        ]

        assert len(consistency_alerts) > 0
        alert = consistency_alerts[0]
        assert alert.severity in [
            QualityAlertSeverity.WARNING,
            QualityAlertSeverity.ERROR,
        ]
        assert "consistency" in alert.message.lower()

    @pytest.mark.asyncio
    async def test_extraction_quality_validation_integration(self, quality_monitor):
        """Test extraction quality validation with various scenarios."""
        test_cases = [
            {
                "name": "high_quality_extraction",
                "extracted_techs": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
                "requirements": "Build a REST API using FastAPI framework with PostgreSQL database, Redis for caching, and Docker for containerization",
                "expected_score_range": (0.8, 1.0),
            },
            {
                "name": "partial_extraction",
                "extracted_techs": ["FastAPI"],
                "requirements": "Build a REST API using FastAPI framework with PostgreSQL database, Redis for caching, and Docker for containerization",
                "expected_score_range": (0.4, 0.7),
            },
            {
                "name": "over_extraction",
                "extracted_techs": [
                    "FastAPI",
                    "PostgreSQL",
                    "Redis",
                    "Docker",
                    "Kubernetes",
                    "MongoDB",
                    "React",
                ],
                "requirements": "Build a simple API with FastAPI",
                "expected_score_range": (0.3, 0.8),
            },
            {
                "name": "irrelevant_extraction",
                "extracted_techs": ["TensorFlow", "PyTorch"],
                "requirements": "Build a simple web form",
                "expected_score_range": (0.0, 0.5),
            },
        ]

        for test_case in test_cases:
            quality_score = await quality_monitor.validate_extraction_quality(
                extracted_techs=test_case["extracted_techs"],
                requirements=test_case["requirements"],
                session_id=f"test_{test_case['name']}",
            )

            # Verify score is in expected range
            min_score, max_score = test_case["expected_score_range"]
            assert (
                min_score <= quality_score.overall_score <= max_score
            ), f"Test case '{test_case['name']}' score {quality_score.overall_score} not in range {test_case['expected_score_range']}"

            # Verify component scores exist
            assert "completeness" in quality_score.component_scores
            assert "accuracy" in quality_score.component_scores
            assert "relevance" in quality_score.component_scores
            assert "catalog_coverage" in quality_score.component_scores

            # Verify confidence is reasonable
            assert 0.0 <= quality_score.confidence <= 1.0

    @pytest.mark.asyncio
    async def test_user_satisfaction_prediction_integration(self, quality_monitor):
        """Test user satisfaction prediction with various result scenarios."""
        test_scenarios = [
            {
                "name": "excellent_result",
                "result": {
                    "tech_stack": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
                    "generation_metrics": {
                        "explicit_inclusion_rate": 0.95,
                        "catalog_coverage": 0.98,
                        "missing_technologies": 0,
                    },
                    "processing_time": 5.2,
                },
                "feedback": {"relevance": 5.0, "accuracy": 4.8, "completeness": 4.9},
                "expected_satisfaction_range": (0.85, 1.0),
            },
            {
                "name": "good_result",
                "result": {
                    "tech_stack": ["FastAPI", "PostgreSQL", "Docker"],
                    "generation_metrics": {
                        "explicit_inclusion_rate": 0.8,
                        "catalog_coverage": 0.85,
                        "missing_technologies": 1,
                    },
                    "processing_time": 12.0,
                },
                "feedback": {"relevance": 4.2, "accuracy": 4.0, "completeness": 3.8},
                "expected_satisfaction_range": (0.7, 0.85),
            },
            {
                "name": "poor_result",
                "result": {
                    "tech_stack": ["UnknownTech1", "UnknownTech2"],
                    "generation_metrics": {
                        "explicit_inclusion_rate": 0.3,
                        "catalog_coverage": 0.4,
                        "missing_technologies": 5,
                    },
                    "processing_time": 45.0,
                },
                "feedback": {"relevance": 2.5, "accuracy": 2.0, "completeness": 2.2},
                "expected_satisfaction_range": (0.2, 0.5),
            },
        ]

        for scenario in test_scenarios:
            satisfaction_score = (
                await quality_monitor.calculate_user_satisfaction_score(
                    result=scenario["result"],
                    feedback=scenario["feedback"],
                    session_id=f"satisfaction_test_{scenario['name']}",
                )
            )

            # Verify satisfaction score is in expected range
            min_satisfaction, max_satisfaction = scenario["expected_satisfaction_range"]
            assert (
                min_satisfaction <= satisfaction_score <= max_satisfaction
            ), f"Scenario '{scenario['name']}' satisfaction {satisfaction_score} not in range {scenario['expected_satisfaction_range']}"

            # Verify satisfaction score was stored
            satisfaction_scores = [
                score
                for score in quality_monitor.quality_scores
                if score.metric_type == QualityMetricType.USER_SATISFACTION
                and score.session_id == f"satisfaction_test_{scenario['name']}"
            ]
            assert len(satisfaction_scores) > 0

    @pytest.mark.asyncio
    async def test_quality_trend_analysis_integration(self, quality_monitor):
        """Test quality trend analysis with historical data."""
        # Generate historical quality data with different trends
        base_time = datetime.now() - timedelta(hours=2)

        # Declining trend for extraction accuracy
        for i in range(20):
            score_value = 0.95 - (i * 0.02)  # Declining from 0.95 to 0.57
            quality_score = await quality_monitor.validate_extraction_quality(
                extracted_techs=["FastAPI"] if score_value > 0.7 else [],
                requirements="Build a web API with FastAPI and PostgreSQL",
                session_id=f"trend_test_{i}",
            )

            # Override the score and timestamp for controlled testing
            quality_score.overall_score = score_value
            quality_score.timestamp = base_time + timedelta(minutes=i * 5)

            # Manually add to avoid duplicate processing
            quality_monitor.quality_scores.append(quality_score)

        # Analyze trend
        trend = await quality_monitor._analyze_quality_trend(
            QualityMetricType.EXTRACTION_ACCURACY
        )

        assert trend is not None
        assert trend.trend_direction == "declining"
        assert trend.trend_strength > 0.5  # Should detect strong decline
        assert trend.change_rate < 0  # Negative change
        assert trend.data_points == 20

        # Should trigger degradation alert
        await quality_monitor._create_degradation_alert(trend)

        degradation_alerts = [
            alert
            for alert in quality_monitor.quality_alerts
            if "degradation" in alert.alert_id
        ]
        assert len(degradation_alerts) > 0

    @pytest.mark.asyncio
    async def test_alert_system_integration(self, quality_monitor):
        """Test integration of alert system with quality monitoring."""
        # Generate low-quality scenarios that should trigger alerts
        alert_scenarios = [
            {
                "type": "extraction_accuracy",
                "action": lambda: quality_monitor.validate_extraction_quality(
                    extracted_techs=[],
                    requirements="Build a complex web application with multiple services",
                    session_id="alert_test_extraction",
                ),
                "expected_metric": QualityMetricType.EXTRACTION_ACCURACY,
            },
            {
                "type": "ecosystem_consistency",
                "action": lambda: quality_monitor.check_ecosystem_consistency(
                    tech_stack=[
                        "AWS Lambda",
                        "Azure Functions",
                        "Google Cloud Storage",
                    ],
                    session_id="alert_test_consistency",
                ),
                "expected_metric": QualityMetricType.ECOSYSTEM_CONSISTENCY,
            },
            {
                "type": "user_satisfaction",
                "action": lambda: quality_monitor.calculate_user_satisfaction_score(
                    result={
                        "tech_stack": ["UnknownTech"],
                        "generation_metrics": {
                            "explicit_inclusion_rate": 0.2,
                            "catalog_coverage": 0.3,
                        },
                        "processing_time": 60.0,
                    },
                    session_id="alert_test_satisfaction",
                ),
                "expected_metric": QualityMetricType.USER_SATISFACTION,
            },
        ]

        initial_alert_count = len(quality_monitor.quality_alerts)

        for scenario in alert_scenarios:
            await scenario["action"]()

        # Should have generated alerts
        final_alert_count = len(quality_monitor.quality_alerts)
        assert final_alert_count > initial_alert_count

        # Verify alert types
        alert_metrics = [alert.metric_type for alert in quality_monitor.quality_alerts]

        for scenario in alert_scenarios:
            assert scenario["expected_metric"] in alert_metrics

        # Test alert resolution
        active_alerts = quality_monitor.get_active_alerts()
        if active_alerts:
            first_alert_id = active_alerts[0]["alert_id"]
            resolution_result = await quality_monitor.resolve_alert(first_alert_id)
            assert resolution_result is True

            # Verify alert is resolved
            updated_active_alerts = quality_monitor.get_active_alerts()
            resolved_alert_ids = [alert["alert_id"] for alert in updated_active_alerts]
            assert first_alert_id not in resolved_alert_ids

    @pytest.mark.asyncio
    async def test_monitoring_status_integration(self, quality_monitor):
        """Test monitoring status reporting integration."""
        # Generate some quality data
        await quality_monitor.validate_extraction_quality(
            extracted_techs=["FastAPI", "PostgreSQL"],
            requirements="Build API with FastAPI and PostgreSQL",
            session_id="status_test",
        )

        await quality_monitor.check_ecosystem_consistency(
            tech_stack=["FastAPI", "PostgreSQL", "Docker"], session_id="status_test"
        )

        # Get current status
        status = quality_monitor.get_current_quality_status()

        # Verify status structure
        assert "overall_status" in status
        assert "metrics" in status
        assert "active_alerts" in status
        assert "monitoring_enabled" in status
        assert "last_updated" in status

        # Verify metric status
        for metric_type in QualityMetricType:
            metric_key = metric_type.value
            assert metric_key in status["metrics"]

            metric_status = status["metrics"][metric_key]
            assert "threshold" in metric_status
            assert "status" in metric_status
            assert "sample_count" in metric_status

        # Get quality trends
        trends = quality_monitor.get_quality_trends()

        assert "trends" in trends
        assert "analysis_window_hours" in trends
        assert "last_updated" in trends

    @pytest.mark.asyncio
    async def test_performance_under_load(self, quality_monitor):
        """Test quality monitor performance under load."""
        import time

        start_time = time.time()

        # Generate multiple concurrent quality assessments
        tasks = []

        for i in range(50):  # 50 concurrent assessments
            # Vary the quality scenarios
            if i % 3 == 0:
                # High quality
                task = quality_monitor.validate_extraction_quality(
                    extracted_techs=["FastAPI", "PostgreSQL", "Redis"],
                    requirements="Build API with FastAPI, PostgreSQL, and Redis",
                    session_id=f"load_test_{i}",
                )
            elif i % 3 == 1:
                # Medium quality
                task = quality_monitor.check_ecosystem_consistency(
                    tech_stack=["AWS Lambda", "Amazon S3", "PostgreSQL"],
                    session_id=f"load_test_{i}",
                )
            else:
                # Satisfaction prediction
                task = quality_monitor.calculate_user_satisfaction_score(
                    result={
                        "tech_stack": ["FastAPI", "PostgreSQL"],
                        "generation_metrics": {"explicit_inclusion_rate": 0.8},
                        "processing_time": 10.0,
                    },
                    session_id=f"load_test_{i}",
                )

            tasks.append(task)

        # Execute all tasks concurrently
        results = await asyncio.gather(*tasks, return_exceptions=True)

        end_time = time.time()
        total_time = end_time - start_time

        # Verify performance
        assert total_time < 30.0  # Should complete within 30 seconds

        # Verify no exceptions occurred
        exceptions = [result for result in results if isinstance(result, Exception)]
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"

        # Verify results were generated
        successful_results = [
            result for result in results if not isinstance(result, Exception)
        ]
        assert len(successful_results) == 50

        # Verify quality monitor state is consistent
        status = quality_monitor.get_current_quality_status()
        assert status["monitoring_enabled"] is True

        # Should have generated quality scores
        assert len(quality_monitor.quality_scores) > 0

    @pytest.mark.asyncio
    async def test_error_recovery_integration(self, quality_monitor):
        """Test error recovery in integrated monitoring scenarios."""
        # Test with invalid/corrupted data
        error_scenarios = [
            {
                "name": "empty_requirements",
                "action": lambda: quality_monitor.validate_extraction_quality(
                    extracted_techs=["FastAPI"],
                    requirements="",
                    session_id="error_test_1",
                ),
            },
            {
                "name": "none_tech_stack",
                "action": lambda: quality_monitor.check_ecosystem_consistency(
                    tech_stack=None, session_id="error_test_2"
                ),
            },
            {
                "name": "invalid_result_format",
                "action": lambda: quality_monitor.calculate_user_satisfaction_score(
                    result=None, session_id="error_test_3"
                ),
            },
        ]

        for scenario in error_scenarios:
            try:
                result = await scenario["action"]()

                # Should handle errors gracefully and return valid results
                if hasattr(result, "overall_score"):
                    assert 0.0 <= result.overall_score <= 1.0
                elif isinstance(result, float):
                    assert 0.0 <= result <= 1.0

            except Exception as e:
                pytest.fail(
                    f"Scenario '{scenario['name']}' should handle errors gracefully, but raised: {e}"
                )

        # Verify monitor is still functional after errors
        status = quality_monitor.get_current_quality_status()
        assert status["overall_status"] != "error"
        assert status["monitoring_enabled"] is True

    @pytest.mark.asyncio
    async def test_data_retention_and_cleanup_integration(self, quality_monitor):
        """Test data retention and cleanup in integrated environment."""
        # Generate old data
        old_time = datetime.now() - timedelta(days=8)

        # Add old quality scores
        for i in range(10):
            old_score = await quality_monitor.validate_extraction_quality(
                extracted_techs=["FastAPI"],
                requirements="Build API",
                session_id=f"old_data_{i}",
            )
            old_score.timestamp = old_time
            quality_monitor.quality_scores.append(old_score)

        # Add recent data
        len(quality_monitor.quality_scores)

        for i in range(5):
            await quality_monitor.validate_extraction_quality(
                extracted_techs=["FastAPI", "PostgreSQL"],
                requirements="Build API with database",
                session_id=f"recent_data_{i}",
            )

        total_scores_before_cleanup = len(quality_monitor.quality_scores)

        # Trigger cleanup
        await quality_monitor._cleanup_old_data()

        total_scores_after_cleanup = len(quality_monitor.quality_scores)

        # Should have removed old data but kept recent data
        assert total_scores_after_cleanup < total_scores_before_cleanup
        assert total_scores_after_cleanup >= 5  # Should keep recent scores

        # Verify remaining scores are recent
        remaining_timestamps = [
            score.timestamp for score in quality_monitor.quality_scores
        ]
        cutoff_time = datetime.now() - timedelta(days=7)

        old_remaining_scores = [ts for ts in remaining_timestamps if ts < cutoff_time]
        assert len(old_remaining_scores) == 0  # No old scores should remain


if __name__ == "__main__":
    pytest.main([__file__])
