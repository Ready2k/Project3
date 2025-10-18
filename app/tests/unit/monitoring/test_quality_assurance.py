"""
Unit tests for QualityAssuranceSystem.
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.monitoring.quality_assurance import (
    QualityAssuranceSystem,
    QACheckResult,
    QAReport,
    QACheckType,
    QAStatus,
)


class TestQualityAssuranceSystem:
    """Test cases for QualityAssuranceSystem."""

    @pytest.fixture
    def qa_system(self):
        """Create a QualityAssuranceSystem instance for testing."""
        with patch("app.utils.imports.require_service") as mock_require, patch(
            "app.utils.imports.optional_service"
        ) as mock_optional:

            mock_logger = Mock()
            mock_monitor = Mock()
            mock_catalog = Mock()

            mock_require.return_value = mock_logger
            mock_optional.side_effect = lambda service, **kwargs: {
                "tech_stack_monitor": mock_monitor,
                "intelligent_catalog_manager": mock_catalog,
            }.get(service)

            qa_system = QualityAssuranceSystem()
            qa_system.qa_enabled = True
            return qa_system

    def test_initialization(self, qa_system):
        """Test QA system initialization."""
        assert qa_system is not None
        assert hasattr(qa_system, "qa_enabled")
        assert hasattr(qa_system, "check_intervals")
        assert hasattr(qa_system, "quality_thresholds")
        assert hasattr(qa_system, "recent_reports")
        assert isinstance(qa_system.recent_reports, list)

    @pytest.mark.asyncio
    async def test_start_stop_qa_system(self, qa_system):
        """Test starting and stopping QA system."""
        # Test start
        await qa_system.start_qa_system()
        assert qa_system.qa_enabled is True

        # Test stop
        await qa_system.stop_qa_system()
        assert qa_system.qa_enabled is False

    @pytest.mark.asyncio
    async def test_check_accuracy_with_data(self, qa_system):
        """Test accuracy check with available data."""
        # Mock monitor with test data
        mock_metrics = [
            Mock(name="extraction_accuracy", value=0.85),
            Mock(name="extraction_accuracy", value=0.90),
            Mock(name="explicit_tech_inclusion_rate", value=0.75),
            Mock(name="explicit_tech_inclusion_rate", value=0.80),
        ]

        qa_system.monitor._get_recent_metrics.return_value = mock_metrics

        result = await qa_system._check_accuracy()

        assert isinstance(result, QACheckResult)
        assert result.check_type == QACheckType.ACCURACY
        assert result.status in [QAStatus.PASSED, QAStatus.WARNING, QAStatus.FAILED]
        assert 0.0 <= result.score <= 1.0
        assert result.message is not None
        assert isinstance(result.recommendations, list)

    @pytest.mark.asyncio
    async def test_check_accuracy_no_data(self, qa_system):
        """Test accuracy check with no available data."""
        qa_system.monitor._get_recent_metrics.return_value = []

        result = await qa_system._check_accuracy()

        assert result.status == QAStatus.SKIPPED
        assert "No recent accuracy data available" in result.message

    @pytest.mark.asyncio
    async def test_check_accuracy_no_monitor(self, qa_system):
        """Test accuracy check with no monitor service."""
        qa_system.monitor = None

        result = await qa_system._check_accuracy()

        assert result.status == QAStatus.SKIPPED
        assert "Monitor service not available" in result.message

    @pytest.mark.asyncio
    async def test_check_consistency_success(self, qa_system):
        """Test consistency check with successful validation."""
        mock_validation_result = {
            "consistency_score": 0.96,
            "duplicate_entries": 2,
            "missing_metadata": 5,
            "inconsistent_categories": 1,
        }

        qa_system.catalog_manager.validate_catalog_consistency = AsyncMock(
            return_value=mock_validation_result
        )

        result = await qa_system._check_consistency()

        assert result.check_type == QACheckType.CONSISTENCY
        assert result.status == QAStatus.PASSED
        assert result.score == 0.96
        assert (
            len(result.recommendations) >= 3
        )  # Should have recommendations for each issue

    @pytest.mark.asyncio
    async def test_check_consistency_failure(self, qa_system):
        """Test consistency check with validation failure."""
        qa_system.catalog_manager.validate_catalog_consistency = AsyncMock(
            side_effect=Exception("Validation failed")
        )

        result = await qa_system._check_consistency()

        assert result.status == QAStatus.FAILED
        assert result.score == 0.0
        assert "Consistency check failed" in result.message

    @pytest.mark.asyncio
    async def test_check_completeness(self, qa_system):
        """Test completeness check."""
        mock_metrics = [
            Mock(name="catalog_missing_rate", value=0.08)  # 8% missing = 92% complete
        ]

        qa_system.monitor._get_recent_metrics.return_value = mock_metrics

        result = await qa_system._check_completeness()

        assert result.check_type == QACheckType.COMPLETENESS
        assert result.score == 0.92  # 1 - 0.08
        assert result.status == QAStatus.PASSED  # Above 80% threshold

    @pytest.mark.asyncio
    async def test_check_performance(self, qa_system):
        """Test performance check."""
        mock_metrics = [
            Mock(name="processing_time", value=12.5),
            Mock(name="processing_time", value=18.0),
            Mock(name="processing_time", value=15.2),
        ]

        qa_system.monitor._get_recent_metrics.return_value = mock_metrics

        result = await qa_system._check_performance()

        assert result.check_type == QACheckType.PERFORMANCE
        expected_avg = (12.5 + 18.0 + 15.2) / 3
        assert result.details["average_time"] == expected_avg
        assert result.details["max_time"] == 18.0
        assert result.status == QAStatus.PASSED  # Below 30s threshold

    @pytest.mark.asyncio
    async def test_check_catalog_health(self, qa_system):
        """Test catalog health check."""
        mock_health_metrics = {
            "consistency_score": 0.95,
            "completeness_score": 0.88,
            "freshness_score": 0.92,
        }

        qa_system.catalog_manager.get_health_metrics = AsyncMock(
            return_value=mock_health_metrics
        )

        result = await qa_system._check_catalog_health()

        assert result.check_type == QACheckType.CATALOG_HEALTH
        # Overall health = (0.95 * 0.4) + (0.88 * 0.4) + (0.92 * 0.2) = 0.916
        expected_health = (0.95 * 0.4) + (0.88 * 0.4) + (0.92 * 0.2)
        assert abs(result.score - expected_health) < 0.01
        assert result.status == QAStatus.PASSED

    @pytest.mark.asyncio
    async def test_check_user_satisfaction(self, qa_system):
        """Test user satisfaction check."""
        mock_metrics = [
            Mock(name="overall_satisfaction", value=4.2),
            Mock(name="overall_satisfaction", value=3.8),
            Mock(name="overall_satisfaction", value=4.5),
        ]

        qa_system.monitor._get_recent_metrics.return_value = mock_metrics

        result = await qa_system._check_user_satisfaction()

        assert result.check_type == QACheckType.USER_SATISFACTION
        expected_avg = (4.2 + 3.8 + 4.5) / 3
        assert result.details["average_satisfaction"] == expected_avg
        assert result.status == QAStatus.PASSED  # Above 4.0 threshold

    @pytest.mark.asyncio
    async def test_generate_qa_report(self, qa_system):
        """Test generating a comprehensive QA report."""
        # Mock all check methods to return test results
        with patch.object(qa_system, "_run_qa_check") as mock_check:
            mock_results = []
            for check_type in QACheckType:
                mock_result = QACheckResult(
                    check_type=check_type,
                    check_name=f"{check_type.value}_check",
                    status=QAStatus.PASSED,
                    score=0.9,
                    message="Test check passed",
                    details={},
                    timestamp=datetime.now(),
                    recommendations=["Test recommendation"],
                )
                mock_results.append(mock_result)

            mock_check.side_effect = mock_results

            report = await qa_system._generate_qa_report()

            assert isinstance(report, QAReport)
            assert report.report_id.startswith("qa_report_")
            assert len(report.check_results) == len(QACheckType)
            assert report.overall_score == 1.0  # All checks passed
            assert report.summary["passed"] == len(QACheckType)
            assert report.summary["failed"] == 0
            assert len(report.recommendations) > 0

    @pytest.mark.asyncio
    async def test_generate_qa_report_mixed_results(self, qa_system):
        """Test generating QA report with mixed check results."""
        with patch.object(qa_system, "_run_qa_check") as mock_check:
            mock_results = [
                QACheckResult(
                    check_type=QACheckType.ACCURACY,
                    check_name="accuracy_check",
                    status=QAStatus.PASSED,
                    score=0.9,
                    message="Accuracy check passed",
                    details={},
                    timestamp=datetime.now(),
                    recommendations=[],
                ),
                QACheckResult(
                    check_type=QACheckType.PERFORMANCE,
                    check_name="performance_check",
                    status=QAStatus.WARNING,
                    score=0.7,
                    message="Performance check warning",
                    details={},
                    timestamp=datetime.now(),
                    recommendations=["Optimize performance"],
                ),
                QACheckResult(
                    check_type=QACheckType.CONSISTENCY,
                    check_name="consistency_check",
                    status=QAStatus.FAILED,
                    score=0.0,
                    message="Consistency check failed",
                    details={},
                    timestamp=datetime.now(),
                    recommendations=["Fix consistency issues"],
                ),
            ]

            # Add remaining checks as skipped
            for check_type in list(QACheckType)[3:]:
                mock_results.append(
                    QACheckResult(
                        check_type=check_type,
                        check_name=f"{check_type.value}_check",
                        status=QAStatus.SKIPPED,
                        score=0.0,
                        message="Check skipped",
                        details={},
                        timestamp=datetime.now(),
                        recommendations=[],
                    )
                )

            mock_check.side_effect = mock_results

            report = await qa_system._generate_qa_report()

            # Overall score should be (1.0 + 0.7 + 0.0) / 3 = 0.567
            expected_score = (1.0 + 0.7 + 0.0) / 3
            assert abs(report.overall_score - expected_score) < 0.01
            assert report.summary["passed"] == 1
            assert report.summary["warnings"] == 1
            assert report.summary["failed"] == 1
            assert report.summary["skipped"] == len(QACheckType) - 3

    def test_determine_health_status(self, qa_system):
        """Test health status determination."""
        # Test excellent health
        status = qa_system._determine_health_status(0.98, [])
        assert status == "excellent"

        # Test good health
        status = qa_system._determine_health_status(0.90, [])
        assert status == "good"

        # Test fair health
        status = qa_system._determine_health_status(0.80, [])
        assert status == "fair"

        # Test poor health
        status = qa_system._determine_health_status(0.65, [])
        assert status == "poor"

        # Test critical health (with critical failures)
        critical_failure = QACheckResult(
            check_type=QACheckType.ACCURACY,
            check_name="accuracy_check",
            status=QAStatus.FAILED,
            score=0.0,
            message="Critical failure",
            details={},
            timestamp=datetime.now(),
            recommendations=[],
        )
        status = qa_system._determine_health_status(0.90, [critical_failure])
        assert status == "critical"

    @pytest.mark.asyncio
    async def test_generate_manual_report(self, qa_system):
        """Test generating manual QA report."""
        with patch.object(qa_system, "_generate_qa_report") as mock_generate:
            mock_report = Mock()
            mock_generate.return_value = mock_report

            result = await qa_system.generate_manual_report()

            assert result == mock_report
            mock_generate.assert_called_once()

    def test_get_latest_report(self, qa_system):
        """Test getting latest report."""
        # No reports initially
        assert qa_system.get_latest_report() is None

        # Add a report
        mock_report = Mock()
        qa_system.recent_reports.append(mock_report)

        assert qa_system.get_latest_report() == mock_report

    def test_get_reports(self, qa_system):
        """Test getting recent reports."""
        # Add multiple reports
        reports = [Mock() for _ in range(15)]
        qa_system.recent_reports.extend(reports)

        # Get default limit (10)
        recent = qa_system.get_reports()
        assert len(recent) == 10
        assert recent == reports[-10:]

        # Get custom limit
        recent = qa_system.get_reports(limit=5)
        assert len(recent) == 5
        assert recent == reports[-5:]

    def test_export_report(self, qa_system, tmp_path):
        """Test exporting QA report."""
        # Create mock report
        mock_report = Mock()
        mock_report.report_id = "test_report_123"
        mock_report.to_dict.return_value = {"test": "data"}

        # Export report
        export_file = tmp_path / "test_report.json"
        qa_system.export_report(mock_report, str(export_file))

        # Check that file was created
        assert export_file.exists()

        # Check file content
        import json

        with open(export_file) as f:
            data = json.load(f)

        assert data == {"test": "data"}
        mock_report.to_dict.assert_called_once()


class TestQACheckResult:
    """Test cases for QACheckResult dataclass."""

    def test_check_result_creation(self):
        """Test creating a QA check result."""
        timestamp = datetime.now()
        result = QACheckResult(
            check_type=QACheckType.ACCURACY,
            check_name="accuracy_test",
            status=QAStatus.PASSED,
            score=0.85,
            message="Test passed",
            details={"test": "data"},
            timestamp=timestamp,
            recommendations=["Test recommendation"],
        )

        assert result.check_type == QACheckType.ACCURACY
        assert result.check_name == "accuracy_test"
        assert result.status == QAStatus.PASSED
        assert result.score == 0.85
        assert result.message == "Test passed"
        assert result.details == {"test": "data"}
        assert result.timestamp == timestamp
        assert result.recommendations == ["Test recommendation"]

    def test_check_result_to_dict(self):
        """Test converting check result to dictionary."""
        timestamp = datetime.now()
        result = QACheckResult(
            check_type=QACheckType.PERFORMANCE,
            check_name="performance_test",
            status=QAStatus.WARNING,
            score=0.7,
            message="Performance warning",
            details={"avg_time": 25.0},
            timestamp=timestamp,
            recommendations=["Optimize performance"],
        )

        data = result.to_dict()

        assert data["check_type"] == "performance"
        assert data["check_name"] == "performance_test"
        assert data["status"] == "warning"
        assert data["score"] == 0.7
        assert data["message"] == "Performance warning"
        assert data["details"] == {"avg_time": 25.0}
        assert data["timestamp"] == timestamp.isoformat()
        assert data["recommendations"] == ["Optimize performance"]


class TestQAReport:
    """Test cases for QAReport dataclass."""

    def test_report_creation(self):
        """Test creating a QA report."""
        timestamp = datetime.now()
        check_results = [
            QACheckResult(
                check_type=QACheckType.ACCURACY,
                check_name="accuracy_check",
                status=QAStatus.PASSED,
                score=0.9,
                message="Accuracy check passed",
                details={},
                timestamp=timestamp,
                recommendations=[],
            )
        ]

        report = QAReport(
            report_id="test_report_123",
            timestamp=timestamp,
            time_window_hours=24,
            overall_score=0.9,
            check_results=check_results,
            summary={"passed": 1, "failed": 0},
            recommendations=["Test recommendation"],
        )

        assert report.report_id == "test_report_123"
        assert report.timestamp == timestamp
        assert report.time_window_hours == 24
        assert report.overall_score == 0.9
        assert len(report.check_results) == 1
        assert report.summary == {"passed": 1, "failed": 0}
        assert report.recommendations == ["Test recommendation"]

    def test_report_to_dict(self):
        """Test converting report to dictionary."""
        timestamp = datetime.now()
        check_result = QACheckResult(
            check_type=QACheckType.ACCURACY,
            check_name="accuracy_check",
            status=QAStatus.PASSED,
            score=0.9,
            message="Test passed",
            details={},
            timestamp=timestamp,
            recommendations=[],
        )

        report = QAReport(
            report_id="test_report_456",
            timestamp=timestamp,
            time_window_hours=12,
            overall_score=0.85,
            check_results=[check_result],
            summary={"total": 1},
            recommendations=["Improve accuracy"],
        )

        data = report.to_dict()

        assert data["report_id"] == "test_report_456"
        assert data["timestamp"] == timestamp.isoformat()
        assert data["time_window_hours"] == 12
        assert data["overall_score"] == 0.85
        assert len(data["check_results"]) == 1
        assert data["check_results"][0]["check_name"] == "accuracy_check"
        assert data["summary"] == {"total": 1}
        assert data["recommendations"] == ["Improve accuracy"]
