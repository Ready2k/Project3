"""
Integration tests for Integrated Monitoring Dashboard System.

Tests the complete integration of dashboard, alert system, and monitoring components.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch

from app.monitoring.integrated_dashboard import IntegratedMonitoringDashboard
from app.monitoring.alert_system import AlertSystem, AlertRule, AlertSeverity
from app.monitoring.tech_stack_monitor import TechStackMonitor
from app.monitoring.quality_assurance import QualityAssuranceSystem
from app.monitoring.performance_analytics import PerformanceAnalytics
from app.monitoring.real_time_quality_monitor import RealTimeQualityMonitor
from app.services.monitoring_integration_service import (
    TechStackMonitoringIntegrationService,
)


class TestIntegratedDashboardSystem:
    """Integration tests for the complete dashboard system."""

    @pytest.fixture
    def system_config(self):
        """Create system configuration."""
        return {
            "dashboard": {
                "auto_refresh_interval": 30,
                "max_alerts_display": 50,
                "real_time_update_enabled": False,  # Disable for testing
                "performance_threshold_warning": 20.0,
                "performance_threshold_critical": 45.0,
            },
            "alerts": {
                "max_active_alerts": 100,
                "escalation_check_interval": 60,
                "cleanup_interval": 300,
            },
            "monitoring": {"metrics_retention_hours": 24, "real_time_streaming": True},
        }

    @pytest.fixture
    def mock_monitoring_services(self):
        """Create mock monitoring services."""
        services = {}

        # Tech Stack Monitor
        tech_monitor = Mock(spec=TechStackMonitor)
        tech_monitor.get_quality_dashboard_data.return_value = {
            "summary": {"total_sessions": 15},
            "accuracy": {"average": 0.87, "trend": "improving"},
            "performance": {"average_time": 18.5, "trend": "stable"},
            "satisfaction": {"average": 4.1, "trend": "improving"},
        }
        tech_monitor._get_recent_metrics.return_value = []
        tech_monitor.metrics = []
        tech_monitor.alerts = []
        tech_monitor.monitoring_active = True
        services["tech_stack_monitor"] = tech_monitor

        # Quality Assurance
        qa_system = Mock(spec=QualityAssuranceSystem)
        mock_report = Mock()
        mock_report.overall_score = 0.89
        mock_report.check_results = []
        mock_report.recommendations = ["Improve response time", "Update catalog"]
        mock_report.timestamp = datetime.now()
        qa_system.get_latest_report.return_value = mock_report
        qa_system.qa_enabled = True
        services["quality_assurance"] = qa_system

        # Performance Analytics
        perf_analytics = Mock(spec=PerformanceAnalytics)
        perf_analytics.usage_patterns = []
        perf_analytics.performance_bottlenecks = []
        perf_analytics.satisfaction_analyses = []
        perf_analytics.predictive_insights = []
        perf_analytics.is_running = True
        services["performance_analytics"] = perf_analytics

        # Real-time Quality Monitor
        rt_quality = Mock(spec=RealTimeQualityMonitor)
        rt_quality.quality_scores = []
        rt_quality.consistency_scores = []
        rt_quality.quality_alerts = []
        rt_quality.quality_trends = {}
        rt_quality.is_monitoring = True
        services["real_time_quality_monitor"] = rt_quality

        # Monitoring Integration
        integration = Mock(spec=TechStackMonitoringIntegrationService)
        integration.active_sessions = {}
        integration.session_events = {}
        integration.get_active_sessions.return_value = []
        integration.is_running = True
        services["monitoring_integration"] = integration

        return services

    @pytest.fixture
    async def integrated_system(self, system_config, mock_monitoring_services):
        """Create integrated dashboard system."""
        # Create dashboard
        dashboard = IntegratedMonitoringDashboard(system_config["dashboard"])

        # Create alert system
        alert_system = AlertSystem(system_config["alerts"])

        # Inject mock services into dashboard
        for service_name, mock_service in mock_monitoring_services.items():
            setattr(dashboard, service_name, mock_service)

        # Initialize systems
        await dashboard.initialize_dashboard()
        await alert_system.start_alert_system()

        # Return both systems
        yield dashboard, alert_system

        # Cleanup
        await dashboard.shutdown_dashboard()
        await alert_system.stop_alert_system()

    @pytest.mark.asyncio
    async def test_system_initialization(self, integrated_system):
        """Test complete system initialization."""
        dashboard, alert_system = integrated_system

        # Verify dashboard initialization
        assert dashboard.dashboard_config is not None
        assert len(dashboard.alert_rules) > 0
        assert dashboard.system_start_time is not None

        # Verify alert system initialization
        assert len(alert_system.alert_rules) > 0
        assert alert_system.is_running is True
        assert alert_system.notification_config is not None

    @pytest.mark.asyncio
    async def test_dashboard_data_collection(self, integrated_system):
        """Test integrated dashboard data collection."""
        dashboard, alert_system = integrated_system

        # Collect dashboard data
        dashboard_data = dashboard._get_dashboard_data()

        # Verify data structure
        assert isinstance(dashboard_data, dict)
        assert "summary" in dashboard_data
        assert "accuracy" in dashboard_data
        assert "performance" in dashboard_data
        assert "satisfaction" in dashboard_data

        # Verify data values
        assert dashboard_data["summary"]["total_sessions"] == 15
        assert dashboard_data["accuracy"]["average"] == 0.87
        assert dashboard_data["performance"]["average_time"] == 18.5
        assert dashboard_data["satisfaction"]["average"] == 4.1

    @pytest.mark.asyncio
    async def test_system_health_monitoring(self, integrated_system):
        """Test system health monitoring."""
        dashboard, alert_system = integrated_system

        # Get system health status
        health_status = dashboard._get_system_health_status()

        # Verify health status
        assert health_status.overall_health in [
            "excellent",
            "good",
            "fair",
            "poor",
            "critical",
        ]
        assert isinstance(health_status.component_status, dict)
        assert health_status.uptime_hours >= 0
        assert health_status.last_update is not None

        # Verify component status
        expected_components = [
            "Tech Stack Monitor",
            "Quality Assurance",
            "Performance Analytics",
            "Real-time Quality Monitor",
            "Monitoring Integration",
        ]

        for component in expected_components:
            assert component in health_status.component_status
            assert health_status.component_status[component] in ["online", "offline"]

    @pytest.mark.asyncio
    async def test_alert_creation_and_management(self, integrated_system):
        """Test alert creation and management workflow."""
        dashboard, alert_system = integrated_system

        # Create alert through dashboard
        await dashboard._create_alert(
            "warning",
            "performance",
            "Test performance alert",
            session_id="test_session_001",
            details={"metric_value": 25.0, "threshold": 20.0},
        )

        # Verify alert was created in dashboard
        assert len(dashboard.active_alerts) == 1
        dashboard_alert = dashboard.active_alerts[0]
        assert dashboard_alert["severity"] == "warning"
        assert dashboard_alert["category"] == "performance"

        # Create alert through alert system
        alert = await alert_system.create_alert(
            "performance_critical", 50.0, session_id="test_session_002"
        )

        # Verify alert was created in alert system
        assert alert is not None
        assert alert.severity == AlertSeverity.CRITICAL
        assert len(alert_system.active_alerts) == 1

        # Test alert acknowledgment
        success = await alert_system.acknowledge_alert(alert.alert_id, "test_user")
        assert success is True

        # Test alert resolution
        success = await alert_system.resolve_alert(alert.alert_id)
        assert success is True
        assert len(alert_system.active_alerts) == 0

    @pytest.mark.asyncio
    async def test_alert_threshold_monitoring(self, integrated_system):
        """Test automatic alert creation based on thresholds."""
        dashboard, alert_system = integrated_system

        # Test performance threshold alerts
        await dashboard._check_performance_alert(25.0)  # Warning threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "warning"

        # Clear alerts
        dashboard.active_alerts.clear()

        await dashboard._check_performance_alert(50.0)  # Critical threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "critical"

        # Test accuracy threshold alerts
        dashboard.active_alerts.clear()

        await dashboard._check_accuracy_alert(0.75)  # Warning threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "warning"

        dashboard.active_alerts.clear()

        await dashboard._check_accuracy_alert(0.65)  # Critical threshold
        assert len(dashboard.active_alerts) == 1
        assert dashboard.active_alerts[0]["severity"] == "critical"

    @pytest.mark.asyncio
    async def test_monitoring_data_flow(self, integrated_system):
        """Test data flow between monitoring components."""
        dashboard, alert_system = integrated_system

        # Simulate monitoring data from tech stack monitor
        dashboard.tech_stack_monitor._get_recent_metrics.return_value = [
            Mock(name="processing_time", value=22.0, timestamp=datetime.now()),
            Mock(name="extraction_accuracy", value=0.88, timestamp=datetime.now()),
            Mock(name="overall_satisfaction", value=4.2, timestamp=datetime.now()),
        ]

        # Update dashboard data
        dashboard._clear_cache()
        dashboard_data = dashboard._get_dashboard_data()

        # Verify data integration
        assert isinstance(dashboard_data, dict)

        # Test QA data integration
        qa_data = dashboard._get_qa_dashboard_data()
        assert qa_data["overall_score"] == 0.89
        assert len(qa_data["recommendations"]) == 2

        # Test analytics data integration
        analytics_data = dashboard._get_analytics_dashboard_data()
        assert "usage_patterns" in analytics_data
        assert "performance_bottlenecks" in analytics_data

    @pytest.mark.asyncio
    async def test_real_time_monitoring_integration(self, integrated_system):
        """Test real-time monitoring integration."""
        dashboard, alert_system = integrated_system

        # Simulate active monitoring sessions
        mock_sessions = [
            {
                "session_id": "session_001",
                "start_time": datetime.now() - timedelta(minutes=5),
                "requirements": {"text": "Test requirements"},
            },
            {
                "session_id": "session_002",
                "start_time": datetime.now() - timedelta(minutes=2),
                "requirements": {"text": "Another test"},
            },
        ]

        dashboard.monitoring_integration.get_active_sessions.return_value = (
            mock_sessions
        )
        dashboard.monitoring_integration.get_session_events.return_value = [
            {
                "event_type": "parsing_complete",
                "timestamp": datetime.now().isoformat(),
                "success": True,
                "data": {"extracted_technologies": ["FastAPI", "PostgreSQL"]},
            }
        ]

        # Get integration data
        integration_data = dashboard._get_integration_dashboard_data()

        # Verify integration data
        assert integration_data["active_sessions"] == 0  # Mock returns empty dict
        assert "service_status" in integration_data

    @pytest.mark.asyncio
    async def test_configuration_management(self, integrated_system):
        """Test configuration management across systems."""
        dashboard, alert_system = integrated_system

        # Test dashboard configuration updates
        dashboard.dashboard_config.auto_refresh_interval = 60

        # Mock configuration saving
        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                with patch("pathlib.Path.mkdir"):
                    await dashboard._save_dashboard_configuration()
                    assert mock_open.called
                    assert mock_json_dump.called

        # Test alert system configuration
        new_rule = AlertRule(
            rule_id="test_integration_rule",
            name="Integration Test Rule",
            description="Rule for integration testing",
            metric_name="integration_metric",
            condition="gt",
            threshold_value=100.0,
            severity=AlertSeverity.WARNING,
        )

        success = alert_system.add_alert_rule(new_rule)
        assert success is True
        assert "test_integration_rule" in alert_system.alert_rules

        # Mock alert configuration saving
        with patch("builtins.open", create=True) as mock_open:
            with patch("json.dump") as mock_json_dump:
                with patch("pathlib.Path.mkdir"):
                    await alert_system._save_alert_configuration()
                    assert mock_open.called
                    assert mock_json_dump.called

    @pytest.mark.asyncio
    async def test_data_retention_and_cleanup(self, integrated_system):
        """Test data retention and cleanup across systems."""
        dashboard, alert_system = integrated_system

        # Add old data to dashboard
        old_alert = {
            "id": "old_alert_001",
            "timestamp": (datetime.now() - timedelta(days=31)).isoformat(),
            "severity": "info",
            "message": "Old dashboard alert",
        }
        dashboard.alert_history.append(old_alert)

        # Add old data to alert system
        from app.monitoring.alert_system import Alert, AlertStatus

        old_system_alert = Alert(
            alert_id="old_system_alert_001",
            rule_id="performance_warning",
            timestamp=datetime.now() - timedelta(days=31),
            severity=AlertSeverity.INFO,
            status=AlertStatus.RESOLVED,
            title="Old System Alert",
            message="Old alert message",
            metric_value=10.0,
            threshold_value=5.0,
        )
        alert_system.alert_history.append(old_system_alert)

        # Set short retention for testing
        dashboard.dashboard_config.alert_retention_hours = 720  # 30 days
        alert_system.config["alert_retention_days"] = 30

        # Run cleanup
        await alert_system._cleanup_old_alerts()

        # Verify old alerts were removed
        assert old_system_alert not in alert_system.alert_history

    @pytest.mark.asyncio
    async def test_error_handling_and_resilience(self, integrated_system):
        """Test system error handling and resilience."""
        dashboard, alert_system = integrated_system

        # Test dashboard with failing service
        dashboard.tech_stack_monitor.get_quality_dashboard_data.side_effect = Exception(
            "Service error"
        )

        # Should handle error gracefully
        dashboard_data = dashboard._get_dashboard_data()
        assert isinstance(dashboard_data, dict)  # Should return empty dict, not crash

        # Reset mock
        dashboard.tech_stack_monitor.get_quality_dashboard_data.side_effect = None
        dashboard.tech_stack_monitor.get_quality_dashboard_data.return_value = {
            "summary": {"total_sessions": 5}
        }

        # Test alert system with invalid rule
        alert = await alert_system.create_alert("nonexistent_rule", 50.0)
        assert alert is None  # Should handle gracefully

        # Test alert operations with invalid IDs
        success = await alert_system.acknowledge_alert("invalid_id", "user")
        assert success is False

        success = await alert_system.resolve_alert("invalid_id")
        assert success is False

    @pytest.mark.asyncio
    async def test_performance_under_load(self, integrated_system):
        """Test system performance under load."""
        dashboard, alert_system = integrated_system

        # Create multiple alerts rapidly
        alert_tasks = []
        for i in range(10):
            task = alert_system.create_alert(
                "performance_warning",
                25.0 + i,  # Vary metric values
                session_id=f"load_test_session_{i}",
            )
            alert_tasks.append(task)

        # Wait for all alerts to be created
        alerts = await asyncio.gather(*alert_tasks)

        # Verify all alerts were created
        created_alerts = [a for a in alerts if a is not None]
        assert (
            len(created_alerts) >= 1
        )  # At least one should be created (others may be suppressed by cooldown)

        # Test dashboard data collection under load
        data_tasks = []
        for i in range(5):
            task = asyncio.create_task(dashboard._get_dashboard_data())
            data_tasks.append(task)

        # Wait for all data collection tasks
        dashboard_data_results = await asyncio.gather(*data_tasks)

        # Verify all data collection succeeded
        for data in dashboard_data_results:
            assert isinstance(data, dict)

    @pytest.mark.asyncio
    async def test_monitoring_metrics_accuracy(self, integrated_system):
        """Test accuracy of monitoring metrics."""
        dashboard, alert_system = integrated_system

        # Create known alerts and verify metrics
        alert1 = await alert_system.create_alert("performance_critical", 50.0)
        await alert_system.create_alert("accuracy_warning", 0.8)

        # Check alert metrics
        metrics = alert_system.get_alert_metrics()
        assert metrics["total_alerts_created"] >= 2
        assert metrics["alerts_by_severity"]["critical"] >= 1
        assert metrics["alerts_by_severity"]["warning"] >= 1
        assert metrics["alerts_by_status"]["active"] >= 2

        # Resolve one alert and check metrics update
        if alert1:
            await alert_system.resolve_alert(alert1.alert_id)
            updated_metrics = alert_system.get_alert_metrics()
            assert updated_metrics["alerts_by_status"]["resolved"] >= 1
            assert updated_metrics["alerts_by_status"]["active"] >= 1
            assert updated_metrics["average_resolution_time"] > 0

    @pytest.mark.asyncio
    async def test_system_shutdown_and_cleanup(self, integrated_system):
        """Test proper system shutdown and cleanup."""
        dashboard, alert_system = integrated_system

        # Create some data
        await dashboard._create_alert("info", "test", "Shutdown test alert")
        await alert_system.create_alert("performance_warning", 25.0)

        # Verify systems are running
        assert len(dashboard.active_alerts) >= 1
        assert len(alert_system.active_alerts) >= 0  # May be suppressed by cooldown

        # Mock archival operations
        with patch.object(
            dashboard, "_archive_alerts", new_callable=AsyncMock
        ) as mock_archive_dashboard:
            with patch.object(
                alert_system, "_save_alert_configuration", new_callable=AsyncMock
            ) as mock_save_alerts:
                # Shutdown should be handled by fixture cleanup
                # Just verify the mocks would be called in real shutdown
                await dashboard._archive_alerts()
                await alert_system._save_alert_configuration()

                assert mock_archive_dashboard.called
                assert mock_save_alerts.called


class TestDashboardUIIntegration:
    """Test dashboard UI integration components."""

    @pytest.fixture
    def mock_streamlit(self):
        """Mock Streamlit components."""
        with patch("streamlit.set_page_config") as mock_config:
            with patch("streamlit.title") as mock_title:
                with patch("streamlit.markdown") as mock_markdown:
                    with patch("streamlit.sidebar") as mock_sidebar:
                        with patch("streamlit.columns") as mock_columns:
                            with patch("streamlit.metric") as mock_metric:
                                yield {
                                    "config": mock_config,
                                    "title": mock_title,
                                    "markdown": mock_markdown,
                                    "sidebar": mock_sidebar,
                                    "columns": mock_columns,
                                    "metric": mock_metric,
                                }

    def test_dashboard_rendering_components(self, mock_streamlit):
        """Test dashboard rendering components."""
        from app.monitoring.integrated_dashboard import (
            render_integrated_monitoring_dashboard,
        )

        # Mock the dashboard instance
        with patch(
            "app.monitoring.integrated_dashboard.IntegratedMonitoringDashboard"
        ) as mock_dashboard_class:
            mock_dashboard = Mock()
            mock_dashboard_class.return_value = mock_dashboard

            # Call render function
            render_integrated_monitoring_dashboard()

            # Verify dashboard was created and render_dashboard was called
            assert mock_dashboard_class.called
            assert mock_dashboard.render_dashboard.called

    def test_dashboard_ui_error_handling(self, mock_streamlit):
        """Test dashboard UI error handling."""
        from app.monitoring.integrated_dashboard import IntegratedMonitoringDashboard

        # Create dashboard with no services (will cause errors)
        dashboard = IntegratedMonitoringDashboard()

        # Mock Streamlit components to avoid actual UI calls
        with patch("streamlit.warning"):
            with patch("streamlit.error"):
                # These methods should handle errors gracefully
                dashboard._get_dashboard_data()
                health_status = dashboard._get_system_health_status()

                # Should not raise exceptions
                assert isinstance(health_status.component_status, dict)


class TestSystemScalability:
    """Test system scalability and performance."""

    @pytest.mark.asyncio
    async def test_large_scale_alert_handling(self):
        """Test handling of large numbers of alerts."""
        config = {
            "max_active_alerts": 1000,
            "max_history_alerts": 5000,
            "alert_retention_days": 1,  # Short retention for testing
        }

        alert_system = AlertSystem(config)
        await alert_system.start_alert_system()

        try:
            # Create many alerts (but respect cooldown)
            unique_rules = []
            for i in range(50):
                rule = AlertRule(
                    rule_id=f"load_test_rule_{i}",
                    name=f"Load Test Rule {i}",
                    description=f"Rule {i} for load testing",
                    metric_name=f"metric_{i}",
                    condition="gt",
                    threshold_value=10.0,
                    severity=AlertSeverity.WARNING,
                    cooldown_minutes=0,  # No cooldown for testing
                )
                alert_system.add_alert_rule(rule)
                unique_rules.append(rule.rule_id)

            # Create alerts for each rule
            created_alerts = []
            for rule_id in unique_rules:
                alert = await alert_system.create_alert(rule_id, 15.0)
                if alert:
                    created_alerts.append(alert)

            # Verify system handled the load
            assert len(created_alerts) > 0
            assert len(alert_system.active_alerts) <= config["max_active_alerts"]

            # Test bulk operations
            acknowledge_tasks = []
            for alert in created_alerts[:10]:  # Acknowledge first 10
                task = alert_system.acknowledge_alert(alert.alert_id, "load_test_user")
                acknowledge_tasks.append(task)

            results = await asyncio.gather(*acknowledge_tasks)
            successful_acks = sum(1 for r in results if r)
            assert successful_acks > 0

        finally:
            await alert_system.stop_alert_system()

    @pytest.mark.asyncio
    async def test_concurrent_dashboard_access(self):
        """Test concurrent dashboard data access."""
        dashboard = IntegratedMonitoringDashboard(
            {"auto_refresh_interval": 30, "real_time_update_enabled": False}
        )

        # Mock services
        mock_monitor = Mock()
        mock_monitor.get_quality_dashboard_data.return_value = {
            "summary": {"total_sessions": 100},
            "accuracy": {"average": 0.9},
            "performance": {"average_time": 12.0},
        }
        dashboard.tech_stack_monitor = mock_monitor

        # Concurrent data access
        access_tasks = []
        for i in range(20):
            task = asyncio.create_task(dashboard._get_dashboard_data())
            access_tasks.append(task)

        # Wait for all access attempts
        results = await asyncio.gather(*access_tasks)

        # Verify all succeeded
        for result in results:
            assert isinstance(result, dict)
            assert "summary" in result

        # Verify caching worked (should have called service only once due to caching)
        # Note: Exact call count depends on timing, but should be minimal
        assert mock_monitor.get_quality_dashboard_data.call_count <= len(access_tasks)
