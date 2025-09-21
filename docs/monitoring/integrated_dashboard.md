# Integrated Monitoring Dashboard

The Integrated Monitoring Dashboard provides a unified interface for monitoring tech stack generation performance, quality metrics, system health, and alert management. It combines real-time monitoring, comprehensive alerting, and system health checks into a single, cohesive dashboard.

## Overview

The dashboard integrates multiple monitoring components:

- **Tech Stack Monitor**: Core metrics and performance tracking
- **Quality Assurance System**: Automated quality checks and validation
- **Performance Analytics**: Usage patterns and bottleneck analysis
- **Real-time Quality Monitor**: Live quality assessment and alerts
- **Alert System**: Comprehensive alerting and notification management

## Features

### 📈 Real-time Monitoring
- Live session tracking and metrics
- Real-time quality scores and consistency checks
- System load and performance indicators
- Active session monitoring with event tracking

### 🚨 Comprehensive Alerting
- Configurable alert rules with multiple severity levels
- Multiple notification channels (email, webhook, log, Streamlit)
- Alert lifecycle management (acknowledge, resolve, suppress)
- Escalation policies and cooldown periods
- Alert correlation and suppression rules

### 🏥 System Health Monitoring
- Component status tracking
- Overall system health assessment
- Uptime monitoring and availability metrics
- Self-monitoring capabilities with health checks

### ⚙️ Configuration Management
- Dashboard settings and preferences
- Alert threshold configuration
- Data retention policies
- Notification channel setup

## Dashboard Sections

### 1. Overview
- Key performance indicators (KPIs)
- System health summary
- Recent activity timeline
- Alert status overview

### 2. Real-time Metrics
- Live session monitoring
- Current system load
- Real-time quality scores
- Performance indicators

### 3. Alerts & Notifications
- Active alerts management
- Alert configuration interface
- Alert history and trends
- Notification settings

### 4. Quality Monitoring
- Quality assurance reports
- Quality trends and analysis
- Recommendations and improvements
- Quality threshold monitoring

### 5. Performance Analytics
- Usage pattern analysis
- Performance bottleneck detection
- User satisfaction tracking
- Predictive insights

### 6. System Health
- Component health status
- Health diagnostics
- Self-monitoring capabilities
- System maintenance tools

### 7. Configuration
- Dashboard preferences
- Alert rule management
- Threshold configuration
- Service settings

### 8. Data Retention
- Data usage overview
- Retention policies
- Data archival management
- Cleanup utilities

## Getting Started

### Installation

The integrated dashboard is part of the monitoring system and requires the following components:

```python
from app.monitoring.integrated_dashboard import IntegratedMonitoringDashboard
from app.monitoring.alert_system import AlertSystem

# Create dashboard with configuration
dashboard_config = {
    'auto_refresh_interval': 30,
    'max_alerts_display': 50,
    'real_time_update_enabled': True,
    'performance_threshold_warning': 20.0,
    'performance_threshold_critical': 45.0
}

dashboard = IntegratedMonitoringDashboard(dashboard_config)
```

### Basic Usage

#### Initialize the Dashboard

```python
import asyncio

async def setup_dashboard():
    # Initialize dashboard
    await dashboard.initialize_dashboard()
    
    # Dashboard is now ready for use
    print("Dashboard initialized successfully")

# Run initialization
asyncio.run(setup_dashboard())
```

#### Access Dashboard Data

```python
# Get comprehensive dashboard data
dashboard_data = dashboard._get_dashboard_data()

# Get system health status
health_status = dashboard._get_system_health_status()

# Check for alerts
active_alerts = dashboard.active_alerts
```

### Streamlit Integration

To render the dashboard in Streamlit:

```python
from app.monitoring.integrated_dashboard import render_integrated_monitoring_dashboard

# In your Streamlit app
render_integrated_monitoring_dashboard()
```

## Configuration

### Dashboard Configuration

```python
dashboard_config = {
    # Refresh settings
    'auto_refresh_interval': 30,  # seconds
    'real_time_update_enabled': True,
    
    # Display settings
    'max_alerts_display': 50,
    'cache_ttl_seconds': 30,
    
    # Data retention
    'metrics_retention_hours': 168,  # 7 days
    'alert_retention_hours': 720,    # 30 days
    
    # Alert thresholds
    'performance_threshold_warning': 20.0,
    'performance_threshold_critical': 45.0,
    'accuracy_threshold_warning': 0.80,
    'accuracy_threshold_critical': 0.70,
    
    # Notifications
    'alert_notifications_enabled': True
}
```

### Alert System Configuration

```python
alert_config = {
    # Alert limits
    'max_active_alerts': 1000,
    'max_history_alerts': 5000,
    'alert_retention_days': 30,
    
    # Background tasks
    'escalation_check_interval': 300,  # 5 minutes
    'cleanup_interval': 3600,          # 1 hour
    
    # Notifications
    'notification_retry_attempts': 3,
    'notification_retry_delay': 60,    # 1 minute
    
    # Notification channels
    'notifications': {
        'email_smtp_server': 'smtp.example.com',
        'email_smtp_port': 587,
        'email_username': 'alerts@example.com',
        'email_password': 'password',
        'email_from': 'alerts@example.com',
        'email_to': ['admin@example.com'],
        'webhook_urls': ['https://webhook.example.com/alerts'],
        'webhook_timeout': 30
    }
}
```

## Alert Management

### Creating Alert Rules

```python
from app.monitoring.alert_system import AlertRule, AlertSeverity, NotificationChannel

# Create custom alert rule
custom_rule = AlertRule(
    rule_id='custom_performance_rule',
    name='Custom Performance Alert',
    description='Alert when custom metric exceeds threshold',
    metric_name='custom_processing_time',
    condition='gt',  # greater than
    threshold_value=30.0,
    severity=AlertSeverity.WARNING,
    enabled=True,
    cooldown_minutes=15,
    notification_channels=[
        NotificationChannel.EMAIL,
        NotificationChannel.LOG
    ]
)

# Add rule to alert system
alert_system.add_alert_rule(custom_rule)
```

### Managing Alerts

```python
# Create alert
alert = await alert_system.create_alert(
    rule_id='performance_critical',
    metric_value=50.0,
    session_id='session_123',
    details={'component': 'LLMProvider', 'operation': 'generate'}
)

# Acknowledge alert
await alert_system.acknowledge_alert(alert.alert_id, 'admin_user')

# Resolve alert
await alert_system.resolve_alert(alert.alert_id)

# Suppress alert
await alert_system.suppress_alert(
    alert.alert_id, 
    'admin_user', 
    'False positive - system maintenance'
)
```

### Getting Alert Information

```python
# Get active alerts
active_alerts = alert_system.get_active_alerts()
critical_alerts = alert_system.get_active_alerts(AlertSeverity.CRITICAL)

# Get alert history
recent_alerts = alert_system.get_alert_history(hours=24)
critical_history = alert_system.get_alert_history(
    hours=168, 
    severity=AlertSeverity.CRITICAL
)

# Get alert metrics
metrics = alert_system.get_alert_metrics()
print(f"Total alerts created: {metrics['total_alerts_created']}")
print(f"Average resolution time: {metrics['average_resolution_time']:.1f}s")
```

## Monitoring Integration

### Service Integration

The dashboard automatically integrates with available monitoring services:

```python
# Services are automatically detected and integrated
services = {
    'tech_stack_monitor': TechStackMonitor(),
    'quality_assurance': QualityAssuranceSystem(),
    'performance_analytics': PerformanceAnalytics(),
    'real_time_quality_monitor': RealTimeQualityMonitor(),
    'monitoring_integration': TechStackMonitoringIntegrationService()
}

# Dashboard will use available services
dashboard = IntegratedMonitoringDashboard(config)
```

### Custom Monitoring Integration

```python
# Add custom monitoring data
async def add_custom_metrics():
    # Create custom alert
    await dashboard._create_alert(
        severity='warning',
        category='custom',
        message='Custom monitoring alert',
        session_id='custom_session',
        details={'custom_metric': 'value'}
    )
    
    # Update system health
    health_status = dashboard._get_system_health_status()
    print(f"System health: {health_status.overall_health}")
```

## API Reference

### IntegratedMonitoringDashboard

#### Methods

- `initialize_dashboard()`: Initialize dashboard and dependencies
- `shutdown_dashboard()`: Shutdown dashboard and cleanup
- `render_dashboard()`: Render complete Streamlit dashboard
- `_get_dashboard_data()`: Get comprehensive dashboard data
- `_get_system_health_status()`: Get system health status
- `_create_alert()`: Create new alert
- `_check_alert_conditions()`: Check alert conditions
- `_export_dashboard_data()`: Export dashboard data

#### Properties

- `dashboard_config`: Dashboard configuration
- `active_alerts`: List of active alerts
- `alert_history`: Alert history
- `alert_rules`: Alert rule definitions
- `system_start_time`: System start timestamp

### AlertSystem

#### Methods

- `start_alert_system()`: Start alert system
- `stop_alert_system()`: Stop alert system
- `create_alert()`: Create new alert
- `acknowledge_alert()`: Acknowledge alert
- `resolve_alert()`: Resolve alert
- `suppress_alert()`: Suppress alert
- `add_alert_rule()`: Add alert rule
- `update_alert_rule()`: Update alert rule
- `remove_alert_rule()`: Remove alert rule
- `get_active_alerts()`: Get active alerts
- `get_alert_history()`: Get alert history
- `get_alert_metrics()`: Get alert metrics

#### Properties

- `alert_rules`: Dictionary of alert rules
- `active_alerts`: Dictionary of active alerts
- `alert_history`: List of alert history
- `notification_config`: Notification configuration
- `alert_metrics`: Alert system metrics

## Best Practices

### Dashboard Configuration

1. **Set appropriate refresh intervals**: Balance real-time updates with system performance
2. **Configure alert thresholds**: Set thresholds based on your system's baseline performance
3. **Enable caching**: Use caching to improve dashboard performance
4. **Limit data retention**: Set appropriate retention periods to manage storage

### Alert Management

1. **Use meaningful alert names**: Make alerts easy to understand and actionable
2. **Set appropriate cooldown periods**: Prevent alert spam while ensuring important issues are caught
3. **Configure multiple notification channels**: Ensure critical alerts reach the right people
4. **Regular alert rule review**: Periodically review and update alert rules

### Performance Optimization

1. **Monitor dashboard performance**: Track dashboard load times and optimize as needed
2. **Use background tasks**: Leverage background tasks for non-critical operations
3. **Implement proper error handling**: Ensure dashboard remains functional during service outages
4. **Regular cleanup**: Implement data cleanup to prevent storage issues

### Security Considerations

1. **Secure notification channels**: Use secure SMTP and webhook configurations
2. **Access control**: Implement proper access controls for dashboard and alert management
3. **Data privacy**: Ensure sensitive data is not exposed in alerts or logs
4. **Audit logging**: Maintain audit logs for alert management actions

## Troubleshooting

### Common Issues

#### Dashboard Not Loading
- Check service dependencies are available
- Verify configuration is correct
- Check logs for initialization errors

#### Alerts Not Triggering
- Verify alert rules are enabled
- Check metric values against thresholds
- Review cooldown periods
- Check alert rule conditions

#### Notifications Not Sending
- Verify notification configuration
- Check SMTP/webhook settings
- Review notification channel settings
- Check network connectivity

#### Performance Issues
- Review cache settings
- Check data retention policies
- Monitor background task performance
- Optimize database queries

### Debug Mode

Enable debug logging for troubleshooting:

```python
import logging

# Enable debug logging
logging.getLogger('IntegratedMonitoringDashboard').setLevel(logging.DEBUG)
logging.getLogger('AlertSystem').setLevel(logging.DEBUG)

# Dashboard will now provide detailed debug information
```

### Health Checks

Use built-in health checks to diagnose issues:

```python
# Get detailed system health
health_status = dashboard._get_system_health_status()

print(f"Overall health: {health_status.overall_health}")
print(f"Component status: {health_status.component_status}")
print(f"Active alerts: {health_status.active_alerts}")
print(f"Uptime: {health_status.uptime_hours:.1f} hours")
```

## Support

For additional support:

1. Check the logs for detailed error information
2. Review the configuration documentation
3. Use the built-in health checks and diagnostics
4. Consult the API reference for detailed method documentation

## Changelog

### Version 1.0.0
- Initial release of integrated monitoring dashboard
- Comprehensive alerting system
- Real-time monitoring capabilities
- System health monitoring
- Configuration management interface
- Data retention and archival policies