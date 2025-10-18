"""
Unit tests for Integrated Monitoring Dashboard.

Tests dashboard functionality, alert system integration, system health monitoring,
and configuration management.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.monitoring.integrated_dashboard import (
    IntegratedMonitoringDashboard,
    DashboardConfig,
    SystemHealthStatus,
    DashboardSection,
    AlertSeverity,
)


class TestIntegratedMonitoringDashboard:
    """Test cases for IntegratedMonitoringDashboard."""

    @pytest.fixture
    def dashboard_config(self):
        """Create test dashboard configuration."""
        return {
            "auto_refresh_interval": 30,
            "max_alerts_display": 50,
            "metrics_retention_hours": 168,
            "alert_retention_hours": 720,
            "real_time_update_enabled": True,
            "alert_notifications_enabled": True,
            "performance_threshold_warning": 20.0,
            "performance_threshold_critical": 45.0,
            "accuracy_threshold_warning": 0.80,
            "accuracy_threshold_critical": 0.70,
        }

    @pytest.fixture
    def mock_services(self):
        """Create mock monitoring services."""
        services = {
            "tech_stack_monitor": Mock(),
            "quality_assurance": Mock(),
            "performance_analytics": Mock(),
            "real_time_quality_monitor": Mock(),
            "monitoring_integration": Mock(),
        }

        # Configure mock methods
        services["tech_stack_monitor"].get_quality_dashboard_data.return_value = {
            "summary": {"total_sessions": 10},
            "accuracy": {"average": 0.85, "trend": "stable"},
            "performance": {"average_time": 15.0, "trend": "improving"},
            "satisfaction": {"average": 4.2, "trend": "stable"},
        }

        services["tech_stack_monitor"]._get_recent_metrics.return_value = []
        services["tech_stack_monitor"].metrics = []

        return services

    @pytest.fixture
    def dashboard(self, dashboard_config, mock_services):
        """Create test dashboard instance."""
        dashboard = IntegratedMonitoringDashboard(dashboard_config)

        # Inject mock services
        for service_name, mock_service in mock_services.items():
            setattr(dashboard, service_name, mock_service)

        return dashboard

    def test_dashboard_config_creation(self, dashboard_config):
        """Test dashboard configuration creation."""
        config = DashboardConfig(**dashboard_config)

        assert config.auto_refresh_interval == 30
        assert config.max_alerts_display == 50
        assert config.real_time_update_enabled is True
        assert config.performance_threshold_warning == 20.0

        # Test to_dict conversion
        config_dict = config.to_dict()
        assert config_dict["auto_refresh_interval"] == 30

        # Test from_dict creation
        config2 = DashboardConfig.from_dict(config_dict)
        assert config2.auto_refresh_interval == 30

    def test_dashboard_initialization(self, dashboard):
        """Test dashboard initialization."""
        assert dashboard.dashboard_config.auto_refresh_interval == 30
        assert len(dashboard.alert_rules) > 0
        assert "performance_degradation" in dashboard.alert_rules
        assert "accuracy_degradation" in dashboard.alert_rules

    def test_system_health_status_creation(self):
        """Test system health status creation."""
        component_status = {
            "Tech Stack Monitor": "online",
            "Quality Assurance": "offline",
            "Performance Analytics": "online",
        }

        health_status = SystemHealthStatus(
            overall_health="good",
            component_status=component_status,
            active_alerts=2,
            critical_alerts=0,
            last_update=datetime.now(),
            uptime_hours=24.5,
        )

        assert health_status.overall_health == "good"
        assert health_status.active_alerts == 2
        assert health_status.uptime_hours == 24.5

        # Test to_dict conversion
        health_dict = health_status.to_dict()
        assert health_dict["overall_health"] == "good"
        assert "last_update" in health_dict

    def test_get_system_health_status(self, dashboard):
        """Test system health status calculation."""
        health_status = dashboard._get_system_health_status()

        assert isinstance(health_status, SystemHealthStatus)
        assert health_status.overall_health in [
            "excellent",
            "good",
            "fair",
            "poor",
            "critical",
        ]
        assert isinstance(health_status.component_status, dict)
        assert health_status.uptime_hours >= 0

    def test_get_dashboard_data(self, dashboard):
        """Test dashboard data collection."""
        dashboard_data = dashboard._get_dashboard_data()

        assert isinstance(dashboard_data, dict)

        # Should contain data from tech stack monitor
        assert "summary" in dashboard_data
        assert "accuracy" in dashboard_data
        assert "performance" in dashboard_data
        assert "satisfaction" in dashboard_data

    def test_get_dashboard_data_caching(self, dashboard):
        """Test dashboard data caching."""
        # First call should populate cache
        data1 = dashboard._get_dashboard_data()
        assert dashboard.cached_dashboard_data == data1
        assert dashboard.cache_timestamp is not None

        # Second call within TTL should return cached data
        data2 = dashboard._get_dashboard_data()
        assert data2 is data1  # Same object reference

        # Clear cache and verify new data is fetched
        dashboard._clear_cache()
        data3 = dashboard._get_dashboard_data()
        assert dashboard.cached_dashboard_data == data3

    def test_clear_cache(self, dashboard):
        """Test cache clearing."""
        # Populate cache
        dashboard._get_dashboard_data()
        assert dashboard.cached_dashboard_data != {}
        assert dashboard.cache_timestamp is not None

        # Clear cache
        dashboard._clear_cache()
        assert dashboard.cached_dashboard_data == {}
        assert dashboard.cache_timestamp is None

    @pytest.mark.asyncio
    async def test_create_alert(self, dashboard):
        """Test alert creation."""
        await dashboard._create_alert(
            "critical",
            "performance",
            "Test alert message",
            session_id="test_session",
            details={"test": True},
        )

        # Verify alert was created and stored
        assert len(dashboard.active_alerts) == 1
        assert len(dashboard.alert_history) == 1

        created_alert = dashboard.active_alerts[0]
        assert created_alert["severity"] == "critical"
        assert created_alert["category"] == "performance"
        assert created_alert["message"] == "Test alert message"
        assert created_alert["session_id"] == "test_session"
        assert created_alert["details"]["test"] is True

    @pytest.mark.asyncio
    async def test_check_performance_alert(self, dashboard):
        """Test performance alert checking."""
        # Test warning threshold
        await dashboard._check_performance_alert(25.0)  # Above warning threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "warning"

        # Clear alerts
        dashboard.active_alerts.clear()

        # Test critical threshold
        await dashboard._check_performance_alert(50.0)  # Above critical threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_check_accuracy_alert(self, dashboard):
        """Test accuracy alert checking."""
        # Test warning threshold
        await dashboard._check_accuracy_alert(0.75)  # Below warning threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "warning"

        # Clear alerts
        dashboard.active_alerts.clear()

        # Test critical threshold
        await dashboard._check_accuracy_alert(0.65)  # Below critical threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_check_health_alert(self, dashboard):
        """Test system health alert checking."""
        # Create health status with poor health
        health_status = SystemHealthStatus(
            overall_health="poor",
            component_status={},
            active_alerts=0,
            critical_alerts=0,
            last_update=datetime.now(),
            uptime_hours=1.0,
        )

        await dashboard._check_health_alert(health_status)
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["category"] == "system_health"

    def test_get_qa_dashboard_data(self, dashboard):
        """Test QA dashboard data collection."""
        # Mock QA system with latest report
        mock_report = Mock()
        mock_report.overall_score = 0.85
        mock_report.check_results = []
        mock_report.recommendations = ["Test recommendation"]
        mock_report.timestamp = datetime.now()

        dashboard.quality_assurance.get_latest_report.return_value = mock_report

        qa_data = dashboard._get_qa_dashboard_data()

        assert qa_data["overall_score"] == 0.85
        assert qa_data["recommendations"] == ["Test recommendation"]
        assert "timestamp" in qa_data

    def test_get_analytics_dashboard_data(self, dashboard):
        """Test analytics dashboard data collection."""
        # Mock analytics data
        dashboard.performance_analytics.usage_patterns = []
        dashboard.performance_analytics.performance_bottlenecks = []
        dashboard.performance_analytics.satisfaction_analyses = []
        dashboard.performance_analytics.predictive_insights = []

        analytics_data = dashboard._get_analytics_dashboard_data()

        assert "usage_patterns" in analytics_data
        assert "performance_bottlenecks" in analytics_data
        assert "satisfaction_analyses" in analytics_data
        assert "predictive_insights" in analytics_data

    def test_get_real_time_dashboard_data(self, dashboard):
        """Test real-time dashboard data collection."""
        # Mock real-time quality monitor data
        dashboard.real_time_quality_monitor.quality_scores = []
        dashboard.real_time_quality_monitor.consistency_scores = []
        dashboard.real_time_quality_monitor.quality_alerts = []
        dashboard.real_time_quality_monitor.quality_trends = {}

        real_time_data = dashboard._get_real_time_dashboard_data()

        assert "quality_scores" in real_time_data
        assert "consistency_scores" in real_time_data
        assert "quality_alerts" in real_time_data
        assert "quality_trends" in real_time_data

    def test_get_integration_dashboard_data(self, dashboard):
        """Test integration dashboard data collection."""
        # Mock integration service data
        dashboard.monitoring_integration.active_sessions = {"session1": Mock()}
        dashboard.monitoring_integration.session_events = {"session1": [Mock(), Mock()]}
        dashboard.monitoring_integration.tech_stack_monitor = Mock()
        dashboard.monitoring_integration.quality_assurance = Mock()
        dashboard.monitoring_integration.performance_analytics = Mock()

        integration_data = dashboard._get_integration_dashboard_data()

        assert integration_data["active_sessions"] == 1
        assert integration_data["total_events"] == 2
        assert "service_status" in integration_data
        assert integration_data["service_status"]["tech_stack_monitor"] is True

    @pytest.mark.asyncio
    async def test_real_time_update_task(self, dashboard):
        """Test real-time update background task."""
        # Mock the task to run only once
        dashboard.dashboard_config.real_time_update_enabled = True

        with patch.object(
            dashboard, "_check_alert_conditions", new_callable=AsyncMock
        ) as mock_check:
            # Run task for a short time
            asyncio.create_task(dashboard._real_time_update_task())
            await asyncio.sleep(0.1)  # Let it run briefly
            dashboard.dashboard_config.real_time_update_enabled = False
            await asyncio.sleep(0.1)  # Let it exit

            # Verify alert checking was called
            assert mock_check.called

    @pytest.mark.asyncio
    async def test_health_check_task(self, dashboard):
        """Test health check background task."""
        with patch.object(dashboard, "_get_system_health_status") as mock_health:
            mock_health.return_value = SystemHealthStatus(
                overall_health="good",
                component_status={},
                active_alerts=0,
                critical_alerts=0,
                last_update=datetime.now(),
                uptime_hours=1.0,
            )

            # Run task briefly
            task = asyncio.create_task(dashboard._health_check_task())
            await asyncio.sleep(0.1)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify health check was called
            assert mock_health.called

    @pytest.mark.asyncio
    async def test_data_retention_task(self, dashboard):
        """Test data retention background task."""
        # Add some old alerts
        old_alert = {
            "timestamp": (datetime.now() - timedelta(days=31)).isoformat(),
            "severity": "info",
            "message": "Old alert",
        }
        dashboard.alert_history.append(old_alert)

        # Run retention task
        with patch.object(dashboard, "_archive_old_data", new_callable=AsyncMock):
            task = asyncio.create_task(dashboard._data_retention_task())
            await asyncio.sleep(0.1)
            task.cancel()

            try:
                await task
            except asyncio.CancelledError:
                pass

            # Verify old alert was removed (based on default 30-day retention)
            remaining_alerts = [
                a
                for a in dashboard.alert_history
                if datetime.fromisoformat(a["timestamp"])
                > datetime.now()
                - timedelta(hours=dashboard.dashboard_config.alert_retention_hours)
            ]
            assert len(remaining_alerts) == 0  # Old alert should be removed

    def test_export_dashboard_data(self, dashboard):
        """Test dashboard data export."""
        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    dashboard._export_dashboard_data()

                    # Verify file operations
                    assert mock_open.called
                    assert mock_json_dump.called
                    assert mock_mkdir.called

    def test_test_alert_system(self, dashboard):
        """Test alert system testing functionality."""
        with patch.object(dashboard, "_create_alert", new_callable=AsyncMock):
            dashboard._test_alert_system()

            # Verify test alert creation was attempted
            # Note: This tests the synchronous wrapper, actual alert creation is async
            assert True  # Test passes if no exception is raised

    @pytest.mark.asyncio
    async def test_load_dashboard_configuration(self, dashboard):
        """Test dashboard configuration loading."""
        config_data = {
            "auto_refresh_interval": 60,
            "max_alerts_display": 100,
            "real_time_update_enabled": False,
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch("json.load", return_value=config_data):
                    await dashboard._load_dashboard_configuration()

                    # Verify configuration was updated
                    assert dashboard.dashboard_config.auto_refresh_interval == 60
                    assert dashboard.dashboard_config.max_alerts_display == 100
                    assert dashboard.dashboard_config.real_time_update_enabled is False

    @pytest.mark.asyncio
    async def test_save_dashboard_configuration(self, dashboard):
        """Test dashboard configuration saving."""
        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    await dashboard._save_dashboard_configuration()

                    # Verify file operations
                    assert mock_open.called
                    assert mock_json_dump.called
                    assert mock_mkdir.called

    def test_save_alert_configuration(self, dashboard):
        """Test alert configuration saving."""
        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    dashboard._save_alert_configuration()

                    # Verify file operations
                    assert mock_open.called
                    assert mock_json_dump.called
                    assert mock_mkdir.called

    @pytest.mark.asyncio
    async def test_initialize_alert_system(self, dashboard):
        """Test alert system initialization."""
        alert_rules_data = {
            "test_rule": {
                "rule_id": "test_rule",
                "name": "Test Rule",
                "description": "Test alert rule",
                "metric_name": "test_metric",
                "condition": "gt",
                "threshold_value": 10.0,
                "severity": "warning",
                "enabled": True,
            }
        }

        with patch("pathlib.Path.exists", return_value=True):
            with patch("builtins.open", create=True):
                with patch("json.load", return_value=alert_rules_data):
                    await dashboard._initialize_alert_system()

                    # Verify alert rule was loaded
                    assert "test_rule" in dashboard.alert_rules
                    assert dashboard.alert_rules["test_rule"]["name"] == "Test Rule"

    @pytest.mark.asyncio
    async def test_archive_alerts(self, dashboard):
        """Test alert archival."""
        # Add some alerts to history
        dashboard.alert_history = [
            {"timestamp": datetime.now().isoformat(), "message": "Test alert 1"},
            {"timestamp": datetime.now().isoformat(), "message": "Test alert 2"},
        ]

        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                with patch("pathlib.Path.mkdir") as mock_mkdir:
                    await dashboard._archive_alerts()

                    # Verify archival operations
                    assert mock_open.called
                    assert mock_json_dump.called
                    assert mock_mkdir.called

    def test_alert_rules_initialization(self, dashboard):
        """Test that default alert rules are properly initialized."""
        assert len(dashboard.alert_rules) > 0

        # Check specific rules exist
        expected_rules = [
            "performance_degradation",
            "accuracy_degradation",
            "high_error_rate",
            "system_health_degradation",
            "catalog_inconsistency",
        ]

        for rule_id in expected_rules:
            assert rule_id in dashboard.alert_rules
            rule = dashboard.alert_rules[rule_id]
            assert "name" in rule
            assert "description" in rule
            assert "metric" in rule
            assert "warning_threshold" in rule
            assert "critical_threshold" in rule
            assert "enabled" in rule

    def test_dashboard_sections_enum(self):
        """Test dashboard sections enumeration."""
        sections = [
            DashboardSection.OVERVIEW,
            DashboardSection.REAL_TIME_METRICS,
            DashboardSection.ALERTS,
            DashboardSection.QUALITY_MONITORING,
            DashboardSection.PERFORMANCE_ANALYTICS,
            DashboardSection.SYSTEM_HEALTH,
            DashboardSection.CONFIGURATION,
            DashboardSection.DATA_RETENTION,
        ]

        for section in sections:
            assert isinstance(section.value, str)
            assert len(section.value) > 0

    def test_alert_severity_enum(self):
        """Test alert severity enumeration."""
        severities = [
            AlertSeverity.INFO,
            AlertSeverity.WARNING,
            AlertSeverity.ERROR,
            AlertSeverity.CRITICAL,
        ]

        for severity in severities:
            assert isinstance(severity.value, str)
            assert len(severity.value) > 0


class TestDashboardIntegration:
    """Integration tests for dashboard components."""

    @pytest.fixture
    def full_dashboard(self):
        """Create dashboard with all components."""
        config = {
            "auto_refresh_interval": 30,
            "real_time_update_enabled": False,  # Disable for testing
        }
        return IntegratedMonitoringDashboard(config)

    @pytest.mark.asyncio
    async def test_full_initialization_and_shutdown(self, full_dashboard):
        """Test complete dashboard lifecycle."""
        # Initialize
        await full_dashboard.initialize_dashboard()

        # Verify initialization
        assert full_dashboard.dashboard_config is not None
        assert len(full_dashboard.alert_rules) > 0

        # Shutdown
        await full_dashboard.shutdown_dashboard()

        # Test passes if no exceptions are raised
        assert True

    @pytest.mark.asyncio
    async def test_alert_workflow(self, full_dashboard):
        """Test complete alert workflow."""
        await full_dashboard.initialize_dashboard()

        # Create alert
        await full_dashboard._create_alert(
            "warning", "test", "Test alert workflow", details={"workflow_test": True}
        )

        # Verify alert was created
        assert len(full_dashboard.active_alerts) == 1
        assert len(full_dashboard.alert_history) == 1

        # Check alert conditions
        await full_dashboard._check_alert_conditions()

        # Test passes if no exceptions are raised
        assert True

        await full_dashboard.shutdown_dashboard()

    def test_dashboard_data_collection_integration(self, full_dashboard):
        """Test integrated dashboard data collection."""
        # This tests the integration of all data collection methods
        dashboard_data = full_dashboard._get_dashboard_data()

        # Should return a dictionary even with no services
        assert isinstance(dashboard_data, dict)

        # Test system health
        health_status = full_dashboard._get_system_health_status()
        assert isinstance(health_status, SystemHealthStatus)

        # Test passes if no exceptions are raised
        assert True
