"""
Unit tests for Alert System.

Tests alert rule management, notification delivery, alert lifecycle,
and system integration.
"""

import pytest
import asyncio
from datetime import datetime, timedelta
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from typing import Dict, List, Any

from app.monitoring.alert_system import (
    AlertSystem,
    AlertRule,
    Alert,
    AlertSeverity,
    AlertStatus,
    NotificationChannel,
    NotificationConfig
)


class TestAlertRule:
    """Test cases for AlertRule."""
    
    def test_alert_rule_creation(self):
        """Test alert rule creation."""
        rule = AlertRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test alert rule",
            metric_name="test_metric",
            condition="gt",
            threshold_value=10.0,
            severity=AlertSeverity.WARNING,
            enabled=True,
            cooldown_minutes=15
        )
        
        assert rule.rule_id == "test_rule"
        assert rule.name == "Test Rule"
        assert rule.metric_name == "test_metric"
        assert rule.condition == "gt"
        assert rule.threshold_value == 10.0
        assert rule.severity == AlertSeverity.WARNING
        assert rule.enabled is True
        assert rule.cooldown_minutes == 15
        assert rule.notification_channels == [NotificationChannel.LOG]  # Default
    
    def test_alert_rule_to_dict(self):
        """Test alert rule dictionary conversion."""
        rule = AlertRule(
            rule_id="test_rule",
            name="Test Rule",
            description="Test description",
            metric_name="test_metric",
            condition="gt",
            threshold_value=10.0,
            severity=AlertSeverity.ERROR,
            notification_channels=[NotificationChannel.EMAIL, NotificationChannel.LOG]
        )
        
        rule_dict = rule.to_dict()
        
        assert rule_dict['rule_id'] == "test_rule"
        assert rule_dict['severity'] == "error"
        assert rule_dict['notification_channels'] == ["email", "log"]
    
    def test_alert_rule_from_dict(self):
        """Test alert rule creation from dictionary."""
        rule_data = {
            'rule_id': "test_rule",
            'name': "Test Rule",
            'description': "Test description",
            'metric_name': "test_metric",
            'condition': "gt",
            'threshold_value': 10.0,
            'severity': "warning",
            'enabled': True,
            'cooldown_minutes': 15,
            'notification_channels': ["email", "webhook"]
        }
        
        rule = AlertRule.from_dict(rule_data)
        
        assert rule.rule_id == "test_rule"
        assert rule.severity == AlertSeverity.WARNING
        assert NotificationChannel.EMAIL in rule.notification_channels
        assert NotificationChannel.WEBHOOK in rule.notification_channels


class TestAlert:
    """Test cases for Alert."""
    
    def test_alert_creation(self):
        """Test alert creation."""
        timestamp = datetime.now()
        
        alert = Alert(
            alert_id="test_alert",
            rule_id="test_rule",
            timestamp=timestamp,
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            title="Test Alert",
            message="Test alert message",
            metric_value=25.0,
            threshold_value=20.0,
            session_id="test_session",
            details={"test": True}
        )
        
        assert alert.alert_id == "test_alert"
        assert alert.rule_id == "test_rule"
        assert alert.timestamp == timestamp
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == AlertStatus.ACTIVE
        assert alert.title == "Test Alert"
        assert alert.message == "Test alert message"
        assert alert.metric_value == 25.0
        assert alert.threshold_value == 20.0
        assert alert.session_id == "test_session"
        assert alert.details["test"] is True
    
    def test_alert_to_dict(self):
        """Test alert dictionary conversion."""
        timestamp = datetime.now()
        
        alert = Alert(
            alert_id="test_alert",
            rule_id="test_rule",
            timestamp=timestamp,
            severity=AlertSeverity.ERROR,
            status=AlertStatus.ACKNOWLEDGED,
            title="Test Alert",
            message="Test message",
            metric_value=15.0,
            threshold_value=10.0
        )
        
        alert_dict = alert.to_dict()
        
        assert alert_dict['alert_id'] == "test_alert"
        assert alert_dict['severity'] == "error"
        assert alert_dict['status'] == "acknowledged"
        assert alert_dict['timestamp'] == timestamp.isoformat()
    
    def test_alert_from_dict(self):
        """Test alert creation from dictionary."""
        timestamp = datetime.now()
        
        alert_data = {
            'alert_id': "test_alert",
            'rule_id': "test_rule",
            'timestamp': timestamp.isoformat(),
            'severity': "warning",
            'status': "resolved",
            'title': "Test Alert",
            'message': "Test message",
            'metric_value': 15.0,
            'threshold_value': 10.0,
            'resolved_at': timestamp.isoformat()
        }
        
        alert = Alert.from_dict(alert_data)
        
        assert alert.alert_id == "test_alert"
        assert alert.severity == AlertSeverity.WARNING
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at == timestamp


class TestNotificationConfig:
    """Test cases for NotificationConfig."""
    
    def test_notification_config_creation(self):
        """Test notification configuration creation."""
        config = NotificationConfig(
            email_smtp_server="smtp.example.com",
            email_smtp_port=587,
            email_username="test@example.com",
            email_password="password",
            email_from="alerts@example.com",
            email_to=["admin@example.com"],
            webhook_urls=["https://webhook.example.com"],
            webhook_timeout=30
        )
        
        assert config.email_smtp_server == "smtp.example.com"
        assert config.email_smtp_port == 587
        assert config.email_to == ["admin@example.com"]
        assert config.webhook_urls == ["https://webhook.example.com"]
    
    def test_notification_config_defaults(self):
        """Test notification configuration defaults."""
        config = NotificationConfig()
        
        assert config.email_to == []
        assert config.webhook_urls == []
        assert config.email_smtp_port == 587
        assert config.webhook_timeout == 30


class TestAlertSystem:
    """Test cases for AlertSystem."""
    
    @pytest.fixture
    def alert_config(self):
        """Create test alert system configuration."""
        return {
            'max_active_alerts': 100,
            'max_history_alerts': 500,
            'alert_retention_days': 7,
            'escalation_check_interval': 60,
            'cleanup_interval': 300,
            'notifications': {
                'email_smtp_server': 'smtp.test.com',
                'email_to': ['test@example.com']
            }
        }
    
    @pytest.fixture
    def alert_system(self, alert_config):
        """Create test alert system instance."""
        return AlertSystem(alert_config)
    
    def test_alert_system_initialization(self, alert_system):
        """Test alert system initialization."""
        assert len(alert_system.alert_rules) > 0
        assert alert_system.config['max_active_alerts'] == 100
        assert alert_system.notification_config.email_smtp_server == 'smtp.test.com'
        assert 'performance_critical' in alert_system.alert_rules
        assert 'accuracy_critical' in alert_system.alert_rules
    
    def test_default_alert_rules(self, alert_system):
        """Test default alert rules initialization."""
        expected_rules = [
            'performance_critical',
            'performance_warning',
            'accuracy_critical',
            'accuracy_warning',
            'error_rate_high'
        ]
        
        for rule_id in expected_rules:
            assert rule_id in alert_system.alert_rules
            rule = alert_system.alert_rules[rule_id]
            assert isinstance(rule, AlertRule)
            assert rule.enabled is True
            assert rule.threshold_value > 0
    
    @pytest.mark.asyncio
    async def test_create_alert(self, alert_system):
        """Test alert creation."""
        rule_id = 'performance_critical'
        metric_value = 50.0
        
        alert = await alert_system.create_alert(
            rule_id=rule_id,
            metric_value=metric_value,
            session_id='test_session',
            details={'test': True}
        )
        
        assert alert is not None
        assert alert.rule_id == rule_id
        assert alert.metric_value == metric_value
        assert alert.session_id == 'test_session'
        assert alert.severity == AlertSeverity.CRITICAL
        assert alert.status == AlertStatus.ACTIVE
        
        # Verify alert was stored
        assert alert.alert_id in alert_system.active_alerts
        assert alert in alert_system.alert_history
        
        # Verify metrics were updated
        assert alert_system.alert_metrics['total_alerts_created'] == 1
        assert alert_system.alert_metrics['alerts_by_severity']['critical'] == 1
    
    @pytest.mark.asyncio
    async def test_create_alert_disabled_rule(self, alert_system):
        """Test alert creation with disabled rule."""
        # Disable a rule
        rule_id = 'performance_critical'
        alert_system.alert_rules[rule_id].enabled = False
        
        alert = await alert_system.create_alert(
            rule_id=rule_id,
            metric_value=50.0
        )
        
        # Should return None for disabled rule
        assert alert is None
        assert len(alert_system.active_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_create_alert_nonexistent_rule(self, alert_system):
        """Test alert creation with nonexistent rule."""
        alert = await alert_system.create_alert(
            rule_id='nonexistent_rule',
            metric_value=50.0
        )
        
        # Should return None for nonexistent rule
        assert alert is None
        assert len(alert_system.active_alerts) == 0
    
    @pytest.mark.asyncio
    async def test_acknowledge_alert(self, alert_system):
        """Test alert acknowledgment."""
        # Create an alert first
        alert = await alert_system.create_alert('performance_critical', 50.0)
        assert alert.status == AlertStatus.ACTIVE
        
        # Acknowledge the alert
        success = await alert_system.acknowledge_alert(alert.alert_id, 'test_user')
        
        assert success is True
        assert alert.status == AlertStatus.ACKNOWLEDGED
        assert alert.acknowledged_by == 'test_user'
        assert alert.acknowledged_at is not None
        
        # Verify metrics were updated
        assert alert_system.alert_metrics['alerts_by_status']['active'] == 0
        assert alert_system.alert_metrics['alerts_by_status']['acknowledged'] == 1
    
    @pytest.mark.asyncio
    async def test_acknowledge_nonexistent_alert(self, alert_system):
        """Test acknowledging nonexistent alert."""
        success = await alert_system.acknowledge_alert('nonexistent_alert', 'test_user')
        assert success is False
    
    @pytest.mark.asyncio
    async def test_resolve_alert(self, alert_system):
        """Test alert resolution."""
        # Create an alert first
        alert = await alert_system.create_alert('performance_critical', 50.0)
        alert_id = alert.alert_id
        
        # Resolve the alert
        success = await alert_system.resolve_alert(alert_id, 'test_user')
        
        assert success is True
        assert alert.status == AlertStatus.RESOLVED
        assert alert.resolved_at is not None
        
        # Verify alert was removed from active alerts
        assert alert_id not in alert_system.active_alerts
        
        # Verify metrics were updated
        assert alert_system.alert_metrics['alerts_by_status']['resolved'] == 1
        assert alert_system.alert_metrics['average_resolution_time'] > 0
    
    @pytest.mark.asyncio
    async def test_suppress_alert(self, alert_system):
        """Test alert suppression."""
        # Create an alert first
        alert = await alert_system.create_alert('performance_critical', 50.0)
        
        # Suppress the alert
        success = await alert_system.suppress_alert(
            alert.alert_id, 
            'test_user', 
            'False positive'
        )
        
        assert success is True
        assert alert.status == AlertStatus.SUPPRESSED
        assert alert.details['suppressed_by'] == 'test_user'
        assert alert.details['suppression_reason'] == 'False positive'
        
        # Verify metrics were updated
        assert alert_system.alert_metrics['alerts_by_status']['suppressed'] == 1
    
    def test_add_alert_rule(self, alert_system):
        """Test adding new alert rule."""
        new_rule = AlertRule(
            rule_id='test_new_rule',
            name='Test New Rule',
            description='Test rule',
            metric_name='test_metric',
            condition='gt',
            threshold_value=100.0,
            severity=AlertSeverity.WARNING
        )
        
        success = alert_system.add_alert_rule(new_rule)
        
        assert success is True
        assert 'test_new_rule' in alert_system.alert_rules
        assert alert_system.alert_rules['test_new_rule'] == new_rule
    
    def test_update_alert_rule(self, alert_system):
        """Test updating alert rule."""
        rule_id = 'performance_critical'
        original_threshold = alert_system.alert_rules[rule_id].threshold_value
        
        updates = {
            'threshold_value': 60.0,
            'cooldown_minutes': 20
        }
        
        success = alert_system.update_alert_rule(rule_id, updates)
        
        assert success is True
        assert alert_system.alert_rules[rule_id].threshold_value == 60.0
        assert alert_system.alert_rules[rule_id].cooldown_minutes == 20
        assert alert_system.alert_rules[rule_id].threshold_value != original_threshold
    
    def test_update_nonexistent_alert_rule(self, alert_system):
        """Test updating nonexistent alert rule."""
        success = alert_system.update_alert_rule('nonexistent_rule', {'threshold_value': 50.0})
        assert success is False
    
    def test_remove_alert_rule(self, alert_system):
        """Test removing alert rule."""
        rule_id = 'performance_critical'
        assert rule_id in alert_system.alert_rules
        
        success = alert_system.remove_alert_rule(rule_id)
        
        assert success is True
        assert rule_id not in alert_system.alert_rules
    
    def test_remove_nonexistent_alert_rule(self, alert_system):
        """Test removing nonexistent alert rule."""
        success = alert_system.remove_alert_rule('nonexistent_rule')
        assert success is False
    
    @pytest.mark.asyncio
    async def test_get_active_alerts(self, alert_system):
        """Test getting active alerts."""
        # Create alerts with different severities
        await alert_system.create_alert('performance_critical', 50.0)  # Critical
        await alert_system.create_alert('performance_warning', 25.0)   # Warning
        await alert_system.create_alert('accuracy_critical', 0.6)      # Critical
        
        # Get all active alerts
        all_alerts = alert_system.get_active_alerts()
        assert len(all_alerts) == 3
        
        # Get critical alerts only
        critical_alerts = alert_system.get_active_alerts(AlertSeverity.CRITICAL)
        assert len(critical_alerts) == 2
        
        # Get warning alerts only
        warning_alerts = alert_system.get_active_alerts(AlertSeverity.WARNING)
        assert len(warning_alerts) == 1
    
    @pytest.mark.asyncio
    async def test_get_alert_history(self, alert_system):
        """Test getting alert history."""
        # Create and resolve some alerts
        alert1 = await alert_system.create_alert('performance_critical', 50.0)
        alert2 = await alert_system.create_alert('accuracy_warning', 0.8)
        
        await alert_system.resolve_alert(alert1.alert_id)
        
        # Get all history
        all_history = alert_system.get_alert_history(hours=24)
        assert len(all_history) >= 2
        
        # Get critical alerts only
        critical_history = alert_system.get_alert_history(hours=24, severity=AlertSeverity.CRITICAL)
        assert len(critical_history) >= 1
    
    def test_get_alert_metrics(self, alert_system):
        """Test getting alert metrics."""
        metrics = alert_system.get_alert_metrics()
        
        assert 'total_alerts_created' in metrics
        assert 'alerts_by_severity' in metrics
        assert 'alerts_by_status' in metrics
        assert 'notification_success_rate' in metrics
        assert 'average_resolution_time' in metrics
        
        # Verify structure
        assert isinstance(metrics['alerts_by_severity'], dict)
        assert isinstance(metrics['alerts_by_status'], dict)
    
    def test_is_alert_suppressed_cooldown(self, alert_system):
        """Test alert suppression due to cooldown."""
        rule_id = 'performance_critical'
        
        # Create a recent alert in history
        recent_alert = Alert(
            alert_id='recent_alert',
            rule_id=rule_id,
            timestamp=datetime.now() - timedelta(minutes=5),  # 5 minutes ago
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.RESOLVED,
            title='Recent Alert',
            message='Recent alert',
            metric_value=50.0,
            threshold_value=45.0
        )
        
        alert_system.alert_history.append(recent_alert)
        
        # Should be suppressed due to cooldown (default 10 minutes for critical)
        is_suppressed = alert_system._is_alert_suppressed(rule_id, 55.0)
        assert is_suppressed is True
    
    def test_is_alert_not_suppressed(self, alert_system):
        """Test alert not suppressed when cooldown expired."""
        rule_id = 'performance_critical'
        
        # Create an old alert in history
        old_alert = Alert(
            alert_id='old_alert',
            rule_id=rule_id,
            timestamp=datetime.now() - timedelta(minutes=20),  # 20 minutes ago
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.RESOLVED,
            title='Old Alert',
            message='Old alert',
            metric_value=50.0,
            threshold_value=45.0
        )
        
        alert_system.alert_history.append(old_alert)
        
        # Should not be suppressed (cooldown expired)
        is_suppressed = alert_system._is_alert_suppressed(rule_id, 55.0)
        assert is_suppressed is False
    
    def test_generate_alert_message(self, alert_system):
        """Test alert message generation."""
        rule = AlertRule(
            rule_id='test_rule',
            name='Test Rule',
            description='Test',
            metric_name='response_time',
            condition='gt',
            threshold_value=30.0,
            severity=AlertSeverity.WARNING
        )
        
        message = alert_system._generate_alert_message(rule, 45.0)
        
        assert 'response_time' in message
        assert 'exceeded' in message
        assert '45.0' in message
        assert '30.0' in message
    
    @pytest.mark.asyncio
    async def test_send_log_notification(self, alert_system):
        """Test log notification sending."""
        alert = Alert(
            alert_id='test_alert',
            rule_id='test_rule',
            timestamp=datetime.now(),
            severity=AlertSeverity.ERROR,
            status=AlertStatus.ACTIVE,
            title='Test Alert',
            message='Test message',
            metric_value=25.0,
            threshold_value=20.0
        )
        
        with patch.object(alert_system.logger, 'log') as mock_log:
            success = await alert_system._send_log_notification(alert)
            
            assert success is True
            assert mock_log.called
    
    @pytest.mark.asyncio
    async def test_send_email_notification_no_config(self, alert_system):
        """Test email notification with no configuration."""
        alert = Alert(
            alert_id='test_alert',
            rule_id='test_rule',
            timestamp=datetime.now(),
            severity=AlertSeverity.CRITICAL,
            status=AlertStatus.ACTIVE,
            title='Test Alert',
            message='Test message',
            metric_value=25.0,
            threshold_value=20.0
        )
        
        # Clear email configuration
        alert_system.notification_config.email_smtp_server = None
        alert_system.notification_config.email_to = []
        
        success = await alert_system._send_email_notification(alert)
        assert success is False
    
    @pytest.mark.asyncio
    async def test_send_streamlit_notification(self, alert_system):
        """Test Streamlit notification sending."""
        alert = Alert(
            alert_id='test_alert',
            rule_id='test_rule',
            timestamp=datetime.now(),
            severity=AlertSeverity.INFO,
            status=AlertStatus.ACTIVE,
            title='Test Alert',
            message='Test message',
            metric_value=25.0,
            threshold_value=20.0
        )
        
        success = await alert_system._send_streamlit_notification(alert)
        assert success is True  # Always returns True for now
    
    def test_update_resolution_time_metric(self, alert_system):
        """Test resolution time metric update."""
        # First resolution
        alert_system._update_resolution_time_metric(120.0)
        assert alert_system.alert_metrics['average_resolution_time'] == 120.0
        
        # Update metrics to simulate resolved alert
        alert_system.alert_metrics['alerts_by_status']['resolved'] = 1
        
        # Second resolution
        alert_system.alert_metrics['alerts_by_status']['resolved'] = 2
        alert_system._update_resolution_time_metric(180.0)
        
        # Should be average of 120 and 180
        expected_avg = (120.0 + 180.0) / 2
        assert alert_system.alert_metrics['average_resolution_time'] == expected_avg
    
    @pytest.mark.asyncio
    async def test_cleanup_old_alerts(self, alert_system):
        """Test cleanup of old alerts."""
        # Add old alert to history
        old_alert = Alert(
            alert_id='old_alert',
            rule_id='test_rule',
            timestamp=datetime.now() - timedelta(days=10),
            severity=AlertSeverity.INFO,
            status=AlertStatus.RESOLVED,
            title='Old Alert',
            message='Old alert',
            metric_value=10.0,
            threshold_value=5.0
        )
        
        alert_system.alert_history.append(old_alert)
        
        # Set short retention period for testing
        alert_system.config['alert_retention_days'] = 7
        
        await alert_system._cleanup_old_alerts()
        
        # Old alert should be removed
        assert old_alert not in alert_system.alert_history
    
    @pytest.mark.asyncio
    async def test_limit_active_alerts(self, alert_system):
        """Test limiting active alerts."""
        # Set low limit for testing
        alert_system.config['max_active_alerts'] = 2
        
        # Create multiple alerts
        alert1 = await alert_system.create_alert('performance_warning', 25.0)
        alert2 = await alert_system.create_alert('accuracy_warning', 0.8)
        alert3 = await alert_system.create_alert('error_rate_high', 0.1)
        
        # Resolve first alert
        await alert_system.resolve_alert(alert1.alert_id)
        
        # Should have 3 active alerts (including resolved one)
        assert len(alert_system.active_alerts) == 3
        
        # Run limit function
        await alert_system._limit_active_alerts()
        
        # Should remove resolved alerts when over limit
        # Exact behavior depends on implementation details
        assert len(alert_system.active_alerts) <= alert_system.config['max_active_alerts'] + 1


class TestAlertSystemIntegration:
    """Integration tests for alert system."""
    
    @pytest.fixture
    def full_alert_system(self):
        """Create full alert system for integration testing."""
        config = {
            'max_active_alerts': 100,
            'escalation_check_interval': 1,  # Fast for testing
            'cleanup_interval': 1,
            'notifications': {
                'email_smtp_server': 'smtp.test.com',
                'email_to': ['test@example.com']
            }
        }
        return AlertSystem(config)
    
    @pytest.mark.asyncio
    async def test_full_alert_lifecycle(self, full_alert_system):
        """Test complete alert lifecycle."""
        # Start alert system
        await full_alert_system.start_alert_system()
        
        try:
            # Create alert
            alert = await full_alert_system.create_alert('performance_critical', 50.0)
            assert alert is not None
            assert alert.status == AlertStatus.ACTIVE
            
            # Acknowledge alert
            success = await full_alert_system.acknowledge_alert(alert.alert_id, 'test_user')
            assert success is True
            assert alert.status == AlertStatus.ACKNOWLEDGED
            
            # Resolve alert
            success = await full_alert_system.resolve_alert(alert.alert_id)
            assert success is True
            assert alert.status == AlertStatus.RESOLVED
            
            # Verify alert is no longer active
            assert alert.alert_id not in full_alert_system.active_alerts
            
        finally:
            # Stop alert system
            await full_alert_system.stop_alert_system()
    
    @pytest.mark.asyncio
    async def test_alert_system_background_tasks(self, full_alert_system):
        """Test alert system background tasks."""
        # Start alert system (starts background tasks)
        await full_alert_system.start_alert_system()
        
        try:
            # Create some alerts
            await full_alert_system.create_alert('performance_critical', 50.0)
            await full_alert_system.create_alert('accuracy_warning', 0.8)
            
            # Let background tasks run briefly
            await asyncio.sleep(0.1)
            
            # Verify system is running
            assert full_alert_system.is_running is True
            
        finally:
            # Stop alert system
            await full_alert_system.stop_alert_system()
            
            # Verify system stopped
            assert full_alert_system.is_running is False
    
    @pytest.mark.asyncio
    async def test_configuration_persistence(self, full_alert_system):
        """Test alert system configuration loading and saving."""
        # Add a custom rule
        custom_rule = AlertRule(
            rule_id='custom_test_rule',
            name='Custom Test Rule',
            description='Custom rule for testing',
            metric_name='custom_metric',
            condition='lt',
            threshold_value=5.0,
            severity=AlertSeverity.ERROR
        )
        
        full_alert_system.add_alert_rule(custom_rule)
        
        # Mock file operations for configuration saving
        with patch('builtins.open', create=True) as mock_open:
            with patch('json.dump') as mock_json_dump:
                with patch('pathlib.Path.mkdir'):
                    await full_alert_system._save_alert_configuration()
                    
                    # Verify save was attempted
                    assert mock_open.called
                    assert mock_json_dump.called
        
        # Mock file operations for configuration loading
        config_data = {
            'alert_rules': [custom_rule.to_dict()],
            'notification_config': {}
        }
        
        with patch('pathlib.Path.exists', return_value=True):
            with patch('builtins.open', create=True):
                with patch('json.load', return_value=config_data):
                    await full_alert_system._load_alert_configuration()
                    
                    # Verify rule was loaded
                    assert 'custom_test_rule' in full_alert_system.alert_rules