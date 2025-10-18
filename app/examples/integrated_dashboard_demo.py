"""
Integrated Monitoring Dashboard Demo

Demonstrates the usage of the integrated monitoring dashboard and alert system
for tech stack generation monitoring.
"""

import asyncio
import time

from app.monitoring.integrated_dashboard import IntegratedMonitoringDashboard
from app.monitoring.alert_system import (
    AlertSystem,
    AlertRule,
    AlertSeverity,
    NotificationChannel,
)


async def demo_integrated_dashboard():
    """Demonstrate integrated monitoring dashboard functionality."""
    print("🚀 Starting Integrated Monitoring Dashboard Demo")
    print("=" * 60)

    # Configuration
    dashboard_config = {
        "auto_refresh_interval": 30,
        "max_alerts_display": 50,
        "real_time_update_enabled": False,  # Disable for demo
        "performance_threshold_warning": 20.0,
        "performance_threshold_critical": 45.0,
        "accuracy_threshold_warning": 0.80,
        "accuracy_threshold_critical": 0.70,
    }

    alert_config = {
        "max_active_alerts": 100,
        "alert_retention_days": 7,
        "notifications": {
            "email_smtp_server": "smtp.example.com",
            "email_to": ["admin@example.com"],
        },
    }

    # Create systems
    dashboard = IntegratedMonitoringDashboard(dashboard_config)
    alert_system = AlertSystem(alert_config)

    try:
        # Initialize systems
        print("\n📊 Initializing Dashboard and Alert System...")
        await dashboard.initialize_dashboard()
        await alert_system.start_alert_system()

        print("✅ Systems initialized successfully")

        # Demo 1: System Health Monitoring
        print("\n🏥 Demo 1: System Health Monitoring")
        print("-" * 40)

        health_status = dashboard._get_system_health_status()
        print(f"Overall Health: {health_status.overall_health}")
        print(f"Active Alerts: {health_status.active_alerts}")
        print(f"Critical Alerts: {health_status.critical_alerts}")
        print(f"Uptime: {health_status.uptime_hours:.1f} hours")

        print("\nComponent Status:")
        for component, status in health_status.component_status.items():
            status_emoji = "🟢" if status == "online" else "🔴"
            print(f"  {status_emoji} {component}: {status}")

        # Demo 2: Alert Management
        print("\n🚨 Demo 2: Alert Management")
        print("-" * 40)

        # Create custom alert rule
        custom_rule = AlertRule(
            rule_id="demo_custom_rule",
            name="Demo Custom Alert",
            description="Custom alert rule for demonstration",
            metric_name="demo_metric",
            condition="gt",
            threshold_value=100.0,
            severity=AlertSeverity.WARNING,
            cooldown_minutes=1,  # Short cooldown for demo
            notification_channels=[NotificationChannel.LOG],
        )

        alert_system.add_alert_rule(custom_rule)
        print(f"✅ Added custom alert rule: {custom_rule.name}")

        # Create alerts
        print("\nCreating demo alerts...")

        # Performance alert
        perf_alert = await alert_system.create_alert(
            "performance_critical",
            50.0,  # Above critical threshold
            session_id="demo_session_001",
            details={"component": "LLMProvider", "operation": "generate"},
        )

        if perf_alert:
            print(f"🚨 Created performance alert: {perf_alert.title}")

        # Custom alert
        custom_alert = await alert_system.create_alert(
            "demo_custom_rule",
            150.0,  # Above threshold
            session_id="demo_session_002",
            details={"demo_data": "test_value"},
        )

        if custom_alert:
            print(f"⚠️ Created custom alert: {custom_alert.title}")

        # Dashboard alert
        await dashboard._create_alert(
            "info",
            "demo",
            "Dashboard demo alert",
            session_id="demo_session_003",
            details={"demo": True},
        )

        print("📊 Created dashboard alert")

        # Show alert status
        active_alerts = alert_system.get_active_alerts()
        print(f"\n📈 Active Alerts: {len(active_alerts)}")

        for alert in active_alerts:
            severity_emoji = {
                "info": "ℹ️",
                "warning": "⚠️",
                "error": "❌",
                "critical": "🚨",
            }.get(alert.severity.value, "❓")

            print(f"  {severity_emoji} {alert.title} - {alert.message}")

        # Demo 3: Alert Lifecycle Management
        print("\n🔄 Demo 3: Alert Lifecycle Management")
        print("-" * 40)

        if active_alerts:
            demo_alert = active_alerts[0]

            # Acknowledge alert
            success = await alert_system.acknowledge_alert(
                demo_alert.alert_id, "demo_user"
            )
            if success:
                print(f"✅ Acknowledged alert: {demo_alert.title}")

            # Wait a moment
            await asyncio.sleep(1)

            # Resolve alert
            success = await alert_system.resolve_alert(demo_alert.alert_id)
            if success:
                print(f"✅ Resolved alert: {demo_alert.title}")

        # Demo 4: Dashboard Data Collection
        print("\n📊 Demo 4: Dashboard Data Collection")
        print("-" * 40)

        dashboard_data = dashboard._get_dashboard_data()
        print("Dashboard data structure:")
        for key, value in dashboard_data.items():
            if isinstance(value, dict):
                print(f"  📁 {key}: {len(value)} items")
            elif isinstance(value, list):
                print(f"  📋 {key}: {len(value)} items")
            else:
                print(f"  📄 {key}: {type(value).__name__}")

        # Demo 5: Alert Metrics
        print("\n📈 Demo 5: Alert Metrics")
        print("-" * 40)

        metrics = alert_system.get_alert_metrics()
        print("Alert System Metrics:")
        print(f"  Total Alerts Created: {metrics['total_alerts_created']}")
        print(f"  Average Resolution Time: {metrics['average_resolution_time']:.1f}s")

        print("\nAlerts by Severity:")
        for severity, count in metrics["alerts_by_severity"].items():
            if count > 0:
                print(f"  {severity.title()}: {count}")

        print("\nAlerts by Status:")
        for status, count in metrics["alerts_by_status"].items():
            if count > 0:
                print(f"  {status.title()}: {count}")

        # Demo 6: Configuration Management
        print("\n⚙️ Demo 6: Configuration Management")
        print("-" * 40)

        print("Dashboard Configuration:")
        config_dict = dashboard.dashboard_config.to_dict()
        for key, value in config_dict.items():
            print(f"  {key}: {value}")

        # Demo 7: Alert Rule Management
        print("\n📋 Demo 7: Alert Rule Management")
        print("-" * 40)

        print(f"Total Alert Rules: {len(alert_system.alert_rules)}")

        print("\nAlert Rules:")
        for rule_id, rule in alert_system.alert_rules.items():
            enabled_status = "✅" if rule.enabled else "❌"
            print(f"  {enabled_status} {rule.name} ({rule.severity.value})")
            print(
                f"    Metric: {rule.metric_name} {rule.condition} {rule.threshold_value}"
            )
            print(f"    Cooldown: {rule.cooldown_minutes} minutes")

        # Demo 8: Data Export
        print("\n💾 Demo 8: Data Export")
        print("-" * 40)

        print("Exporting dashboard data...")
        try:
            dashboard._export_dashboard_data()
            print("✅ Dashboard data exported successfully")
        except Exception as e:
            print(f"⚠️ Export demo (would export in real usage): {e}")

        # Demo 9: Alert History
        print("\n📚 Demo 9: Alert History")
        print("-" * 40)

        alert_history = alert_system.get_alert_history(hours=24)
        print(f"Alert History (24h): {len(alert_history)} alerts")

        for alert in alert_history[-3:]:  # Show last 3
            timestamp = alert.timestamp.strftime("%H:%M:%S")
            print(f"  {timestamp} - {alert.title} ({alert.status.value})")

        # Demo 10: System Performance
        print("\n⚡ Demo 10: System Performance")
        print("-" * 40)

        # Simulate performance test
        start_time = time.time()

        # Multiple dashboard data requests
        for i in range(5):
            dashboard._get_dashboard_data()

        end_time = time.time()
        avg_time = (end_time - start_time) / 5

        print("Dashboard data collection performance:")
        print(f"  Average time per request: {avg_time*1000:.1f}ms")
        print(
            f"  Caching enabled: {'Yes' if dashboard.cached_dashboard_data else 'No'}"
        )

        # Test alert creation performance
        start_time = time.time()

        test_alerts = []
        for i in range(3):
            alert = await alert_system.create_alert(
                "demo_custom_rule",
                110.0 + i,  # Vary values to avoid suppression
                session_id=f"perf_test_{i}",
            )
            if alert:
                test_alerts.append(alert)

        end_time = time.time()

        if test_alerts:
            avg_alert_time = (end_time - start_time) / len(test_alerts)
            print("\nAlert creation performance:")
            print(f"  Average time per alert: {avg_alert_time*1000:.1f}ms")
            print(f"  Alerts created: {len(test_alerts)}")

        print("\n🎉 Demo completed successfully!")
        print("=" * 60)

        # Summary
        print("\n📋 Demo Summary:")
        print("  • Dashboard initialized and configured")
        print(f"  • Alert system with {len(alert_system.alert_rules)} rules")
        print(f"  • {len(alert_system.active_alerts)} active alerts")
        print(f"  • {len(alert_system.alert_history)} total alerts in history")
        print(f"  • System health: {health_status.overall_health}")
        print(f"  • Uptime: {health_status.uptime_hours:.1f} hours")

    except Exception as e:
        print(f"❌ Demo error: {e}")
        import traceback

        traceback.print_exc()

    finally:
        # Cleanup
        print("\n🧹 Cleaning up...")
        try:
            await dashboard.shutdown_dashboard()
            await alert_system.stop_alert_system()
            print("✅ Cleanup completed")
        except Exception as e:
            print(f"⚠️ Cleanup warning: {e}")


def demo_dashboard_configuration():
    """Demonstrate dashboard configuration options."""
    print("\n⚙️ Dashboard Configuration Demo")
    print("-" * 40)

    # Basic configuration
    basic_config = {
        "auto_refresh_interval": 30,
        "max_alerts_display": 50,
        "real_time_update_enabled": True,
    }

    # Advanced configuration
    advanced_config = {
        "auto_refresh_interval": 15,
        "max_alerts_display": 100,
        "metrics_retention_hours": 168,  # 7 days
        "alert_retention_hours": 720,  # 30 days
        "real_time_update_enabled": True,
        "alert_notifications_enabled": True,
        "performance_threshold_warning": 15.0,
        "performance_threshold_critical": 30.0,
        "accuracy_threshold_warning": 0.85,
        "accuracy_threshold_critical": 0.75,
    }

    print("Basic Configuration:")
    for key, value in basic_config.items():
        print(f"  {key}: {value}")

    print("\nAdvanced Configuration:")
    for key, value in advanced_config.items():
        print(f"  {key}: {value}")

    # Alert system configuration
    alert_config = {
        "max_active_alerts": 1000,
        "max_history_alerts": 5000,
        "alert_retention_days": 30,
        "escalation_check_interval": 300,
        "cleanup_interval": 3600,
        "notification_retry_attempts": 3,
        "notifications": {
            "email_smtp_server": "smtp.gmail.com",
            "email_smtp_port": 587,
            "email_username": "alerts@company.com",
            "email_to": ["admin@company.com", "ops@company.com"],
            "webhook_urls": ["https://hooks.slack.com/webhook"],
            "webhook_timeout": 30,
        },
    }

    print("\nAlert System Configuration:")
    for key, value in alert_config.items():
        if key != "notifications":
            print(f"  {key}: {value}")

    print("\nNotification Configuration:")
    for key, value in alert_config["notifications"].items():
        if "password" not in key.lower():  # Don't show passwords
            print(f"  {key}: {value}")


async def demo_alert_rules():
    """Demonstrate custom alert rule creation."""
    print("\n📋 Custom Alert Rules Demo")
    print("-" * 40)

    # Create alert system
    alert_system = AlertSystem()
    await alert_system.start_alert_system()

    try:
        # Custom performance rule
        perf_rule = AlertRule(
            rule_id="custom_performance",
            name="Custom Performance Alert",
            description="Alert when custom performance metric exceeds threshold",
            metric_name="custom_response_time",
            condition="gt",
            threshold_value=25.0,
            severity=AlertSeverity.WARNING,
            cooldown_minutes=10,
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.LOG],
        )

        # Custom accuracy rule
        accuracy_rule = AlertRule(
            rule_id="custom_accuracy",
            name="Custom Accuracy Alert",
            description="Alert when accuracy falls below custom threshold",
            metric_name="custom_accuracy",
            condition="lt",
            threshold_value=0.90,
            severity=AlertSeverity.ERROR,
            cooldown_minutes=5,
            notification_channels=[
                NotificationChannel.WEBHOOK,
                NotificationChannel.LOG,
            ],
        )

        # Custom business rule
        business_rule = AlertRule(
            rule_id="business_metric",
            name="Business Metric Alert",
            description="Alert for business-specific metrics",
            metric_name="user_satisfaction",
            condition="lt",
            threshold_value=4.0,
            severity=AlertSeverity.CRITICAL,
            cooldown_minutes=30,
            notification_channels=[
                NotificationChannel.EMAIL,
                NotificationChannel.WEBHOOK,
            ],
        )

        # Add rules
        rules = [perf_rule, accuracy_rule, business_rule]
        for rule in rules:
            success = alert_system.add_alert_rule(rule)
            print(f"{'✅' if success else '❌'} Added rule: {rule.name}")

        # Test rules
        print("\nTesting alert rules...")

        # Test performance rule
        alert1 = await alert_system.create_alert("custom_performance", 30.0)
        if alert1:
            print(f"🚨 Performance alert: {alert1.message}")

        # Test accuracy rule
        alert2 = await alert_system.create_alert("custom_accuracy", 0.85)
        if alert2:
            print(f"⚠️ Accuracy alert: {alert2.message}")

        # Test business rule
        alert3 = await alert_system.create_alert("business_metric", 3.5)
        if alert3:
            print(f"🚨 Business alert: {alert3.message}")

        print(f"\nCreated {len([a for a in [alert1, alert2, alert3] if a])} alerts")

    finally:
        await alert_system.stop_alert_system()


if __name__ == "__main__":
    print("🎯 Integrated Monitoring Dashboard Demo Suite")
    print("=" * 60)

    # Run configuration demo
    demo_dashboard_configuration()

    # Run alert rules demo
    asyncio.run(demo_alert_rules())

    # Run main dashboard demo
    asyncio.run(demo_integrated_dashboard())

    print("\n🏁 All demos completed!")
    print("=" * 60)
    print("\nNext steps:")
    print("1. Review the dashboard documentation in docs/monitoring/")
    print("2. Configure your notification channels")
    print("3. Set up custom alert rules for your environment")
    print("4. Integrate with your Streamlit application")
    print("5. Monitor your tech stack generation performance!")
