"""
Alert System for Integrated Monitoring Dashboard

Provides comprehensive alerting capabilities including rule management,
notification delivery, alert correlation, and escalation policies.
"""

import asyncio
import json
import smtplib
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable, Union
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


class AlertSeverity(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status."""
    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


class NotificationChannel(Enum):
    """Notification delivery channels."""
    EMAIL = "email"
    WEBHOOK = "webhook"
    LOG = "log"
    STREAMLIT = "streamlit"


@dataclass
class AlertRule:
    """Alert rule configuration."""
    rule_id: str
    name: str
    description: str
    metric_name: str
    condition: str  # gt, lt, eq, gte, lte
    threshold_value: float
    severity: AlertSeverity
    enabled: bool = True
    cooldown_minutes: int = 15
    notification_channels: List[NotificationChannel] = None
    escalation_rules: List[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.notification_channels is None:
            self.notification_channels = [NotificationChannel.LOG]
        if self.escalation_rules is None:
            self.escalation_rules = []
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['severity'] = self.severity.value
        data['notification_channels'] = [c.value for c in self.notification_channels]
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AlertRule':
        """Create from dictionary."""
        data['severity'] = AlertSeverity(data['severity'])
        data['notification_channels'] = [NotificationChannel(c) for c in data.get('notification_channels', ['log'])]
        return cls(**data)


@dataclass
class Alert:
    """Alert instance."""
    alert_id: str
    rule_id: str
    timestamp: datetime
    severity: AlertSeverity
    status: AlertStatus
    title: str
    message: str
    metric_value: float
    threshold_value: float
    session_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None
    escalated: bool = False
    escalation_level: int = 0
    notification_attempts: int = 0
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['severity'] = self.severity.value
        data['status'] = self.status.value
        if self.acknowledged_at:
            data['acknowledged_at'] = self.acknowledged_at.isoformat()
        if self.resolved_at:
            data['resolved_at'] = self.resolved_at.isoformat()
        return data
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Alert':
        """Create from dictionary."""
        data['timestamp'] = datetime.fromisoformat(data['timestamp'])
        data['severity'] = AlertSeverity(data['severity'])
        data['status'] = AlertStatus(data['status'])
        if data.get('acknowledged_at'):
            data['acknowledged_at'] = datetime.fromisoformat(data['acknowledged_at'])
        if data.get('resolved_at'):
            data['resolved_at'] = datetime.fromisoformat(data['resolved_at'])
        return cls(**data)


@dataclass
class NotificationConfig:
    """Notification configuration."""
    email_smtp_server: Optional[str] = None
    email_smtp_port: int = 587
    email_username: Optional[str] = None
    email_password: Optional[str] = None
    email_from: Optional[str] = None
    email_to: List[str] = None
    webhook_urls: List[str] = None
    webhook_timeout: int = 30
    
    def __post_init__(self):
        if self.email_to is None:
            self.email_to = []
        if self.webhook_urls is None:
            self.webhook_urls = []


class AlertSystem(ConfigurableService):
    """
    Comprehensive alert system for monitoring dashboard.
    
    Provides alert rule management, notification delivery, alert correlation,
    escalation policies, and alert lifecycle management.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'AlertSystem')
        
        # Initialize logger
        try:
            self.logger = require_service('logger', context='AlertSystem')
        except:
            import logging
            self.logger = logging.getLogger('AlertSystem')
        
        # Alert management
        self.alert_rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        
        # Notification configuration
        self.notification_config = NotificationConfig(**(config.get('notifications', {}) if config else {}))
        
        # Alert system state
        self.is_running = False
        self.alert_processing_task = None
        self.escalation_task = None
        self.cleanup_task = None
        
        # Configuration
        self.config = {
            'max_active_alerts': 1000,
            'max_history_alerts': 5000,
            'alert_retention_days': 30,
            'escalation_check_interval': 300,  # 5 minutes
            'cleanup_interval': 3600,  # 1 hour
            'notification_retry_attempts': 3,
            'notification_retry_delay': 60,  # 1 minute
            **config
        } if config else {
            'max_active_alerts': 1000,
            'max_history_alerts': 5000,
            'alert_retention_days': 30,
            'escalation_check_interval': 300,
            'cleanup_interval': 3600,
            'notification_retry_attempts': 3,
            'notification_retry_delay': 60
        }
        
        # Alert correlation
        self.correlation_rules: List[Dict[str, Any]] = []
        self.suppression_rules: List[Dict[str, Any]] = []
        
        # Metrics tracking
        self.alert_metrics = {
            'total_alerts_created': 0,
            'alerts_by_severity': {s.value: 0 for s in AlertSeverity},
            'alerts_by_status': {s.value: 0 for s in AlertStatus},
            'notification_success_rate': 0.0,
            'average_resolution_time': 0.0
        }
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    async def _do_initialize(self) -> None:
        """Initialize the alert system."""
        await self.start_alert_system()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the alert system."""
        await self.stop_alert_system()
    
    async def start_alert_system(self) -> None:
        """Start the alert system."""
        try:
            self.logger.info("Starting alert system")
            
            # Load configuration
            await self._load_alert_configuration()
            
            # Start background tasks
            self.is_running = True
            self.alert_processing_task = asyncio.create_task(self._alert_processing_loop())
            self.escalation_task = asyncio.create_task(self._escalation_loop())
            self.cleanup_task = asyncio.create_task(self._cleanup_loop())
            
            self.logger.info("Alert system started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start alert system: {e}")
            raise
    
    async def stop_alert_system(self) -> None:
        """Stop the alert system."""
        try:
            self.logger.info("Stopping alert system")
            
            self.is_running = False
            
            # Cancel background tasks
            for task in [self.alert_processing_task, self.escalation_task, self.cleanup_task]:
                if task:
                    task.cancel()
                    try:
                        await task
                    except asyncio.CancelledError:
                        pass
            
            # Save configuration
            await self._save_alert_configuration()
            
            self.logger.info("Alert system stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping alert system: {e}")
    
    def _initialize_default_rules(self) -> None:
        """Initialize default alert rules."""
        default_rules = [
            AlertRule(
                rule_id="performance_critical",
                name="Critical Performance Degradation",
                description="Alert when response time exceeds critical threshold",
                metric_name="processing_time",
                condition="gt",
                threshold_value=45.0,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=10,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.LOG]
            ),
            AlertRule(
                rule_id="performance_warning",
                name="Performance Warning",
                description="Alert when response time exceeds warning threshold",
                metric_name="processing_time",
                condition="gt",
                threshold_value=20.0,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=15,
                notification_channels=[NotificationChannel.LOG]
            ),
            AlertRule(
                rule_id="accuracy_critical",
                name="Critical Accuracy Degradation",
                description="Alert when accuracy falls below critical threshold",
                metric_name="extraction_accuracy",
                condition="lt",
                threshold_value=0.70,
                severity=AlertSeverity.CRITICAL,
                cooldown_minutes=10,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.LOG]
            ),
            AlertRule(
                rule_id="accuracy_warning",
                name="Accuracy Warning",
                description="Alert when accuracy falls below warning threshold",
                metric_name="extraction_accuracy",
                condition="lt",
                threshold_value=0.85,
                severity=AlertSeverity.WARNING,
                cooldown_minutes=15,
                notification_channels=[NotificationChannel.LOG]
            ),
            AlertRule(
                rule_id="error_rate_high",
                name="High Error Rate",
                description="Alert when error rate exceeds threshold",
                metric_name="error_rate",
                condition="gt",
                threshold_value=0.05,
                severity=AlertSeverity.ERROR,
                cooldown_minutes=10,
                notification_channels=[NotificationChannel.EMAIL, NotificationChannel.LOG]
            )
        ]
        
        for rule in default_rules:
            self.alert_rules[rule.rule_id] = rule
    
    async def create_alert(self, 
                         rule_id: str,
                         metric_value: float,
                         session_id: Optional[str] = None,
                         details: Optional[Dict[str, Any]] = None) -> Optional[Alert]:
        """
        Create a new alert based on a rule.
        
        Args:
            rule_id: ID of the alert rule
            metric_value: Current metric value that triggered the alert
            session_id: Optional session identifier
            details: Additional alert details
            
        Returns:
            Created Alert object or None if alert was suppressed
        """
        try:
            rule = self.alert_rules.get(rule_id)
            if not rule or not rule.enabled:
                return None
            
            # Check if alert should be suppressed due to cooldown
            if self._is_alert_suppressed(rule_id, metric_value):
                return None
            
            # Create alert
            alert_id = f"alert_{rule_id}_{int(datetime.now().timestamp())}"
            
            alert = Alert(
                alert_id=alert_id,
                rule_id=rule_id,
                timestamp=datetime.now(),
                severity=rule.severity,
                status=AlertStatus.ACTIVE,
                title=rule.name,
                message=self._generate_alert_message(rule, metric_value),
                metric_value=metric_value,
                threshold_value=rule.threshold_value,
                session_id=session_id,
                details=details or {}
            )
            
            # Store alert
            self.active_alerts[alert_id] = alert
            self.alert_history.append(alert)
            
            # Update metrics
            self.alert_metrics['total_alerts_created'] += 1
            self.alert_metrics['alerts_by_severity'][rule.severity.value] += 1
            self.alert_metrics['alerts_by_status'][AlertStatus.ACTIVE.value] += 1
            
            # Queue for notification
            await self._queue_alert_notification(alert)
            
            self.logger.warning(f"Alert created: {alert.title} - {alert.message}")
            
            return alert
            
        except Exception as e:
            self.logger.error(f"Error creating alert: {e}")
            return None
    
    async def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """
        Acknowledge an alert.
        
        Args:
            alert_id: Alert identifier
            acknowledged_by: User who acknowledged the alert
            
        Returns:
            True if alert was acknowledged successfully
        """
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return False
            
            alert.status = AlertStatus.ACKNOWLEDGED
            alert.acknowledged_by = acknowledged_by
            alert.acknowledged_at = datetime.now()
            
            # Update metrics
            self.alert_metrics['alerts_by_status'][AlertStatus.ACTIVE.value] -= 1
            self.alert_metrics['alerts_by_status'][AlertStatus.ACKNOWLEDGED.value] += 1
            
            self.logger.info(f"Alert acknowledged: {alert_id} by {acknowledged_by}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error acknowledging alert: {e}")
            return False
    
    async def resolve_alert(self, alert_id: str, resolved_by: Optional[str] = None) -> bool:
        """
        Resolve an alert.
        
        Args:
            alert_id: Alert identifier
            resolved_by: User who resolved the alert
            
        Returns:
            True if alert was resolved successfully
        """
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return False
            
            old_status = alert.status
            alert.status = AlertStatus.RESOLVED
            alert.resolved_at = datetime.now()
            
            # Calculate resolution time for metrics
            resolution_time = (alert.resolved_at - alert.timestamp).total_seconds()
            self._update_resolution_time_metric(resolution_time)
            
            # Update metrics
            self.alert_metrics['alerts_by_status'][old_status.value] -= 1
            self.alert_metrics['alerts_by_status'][AlertStatus.RESOLVED.value] += 1
            
            # Remove from active alerts
            del self.active_alerts[alert_id]
            
            self.logger.info(f"Alert resolved: {alert_id} (resolution time: {resolution_time:.1f}s)")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error resolving alert: {e}")
            return False
    
    async def suppress_alert(self, alert_id: str, suppressed_by: str, reason: str) -> bool:
        """
        Suppress an alert.
        
        Args:
            alert_id: Alert identifier
            suppressed_by: User who suppressed the alert
            reason: Reason for suppression
            
        Returns:
            True if alert was suppressed successfully
        """
        try:
            alert = self.active_alerts.get(alert_id)
            if not alert:
                return False
            
            old_status = alert.status
            alert.status = AlertStatus.SUPPRESSED
            alert.details['suppressed_by'] = suppressed_by
            alert.details['suppression_reason'] = reason
            alert.details['suppressed_at'] = datetime.now().isoformat()
            
            # Update metrics
            self.alert_metrics['alerts_by_status'][old_status.value] -= 1
            self.alert_metrics['alerts_by_status'][AlertStatus.SUPPRESSED.value] += 1
            
            self.logger.info(f"Alert suppressed: {alert_id} by {suppressed_by} - {reason}")
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error suppressing alert: {e}")
            return False
    
    def add_alert_rule(self, rule: AlertRule) -> bool:
        """
        Add a new alert rule.
        
        Args:
            rule: AlertRule to add
            
        Returns:
            True if rule was added successfully
        """
        try:
            self.alert_rules[rule.rule_id] = rule
            self.logger.info(f"Alert rule added: {rule.rule_id} - {rule.name}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error adding alert rule: {e}")
            return False
    
    def update_alert_rule(self, rule_id: str, updates: Dict[str, Any]) -> bool:
        """
        Update an existing alert rule.
        
        Args:
            rule_id: Rule identifier
            updates: Dictionary of updates to apply
            
        Returns:
            True if rule was updated successfully
        """
        try:
            rule = self.alert_rules.get(rule_id)
            if not rule:
                return False
            
            # Apply updates
            for key, value in updates.items():
                if hasattr(rule, key):
                    setattr(rule, key, value)
            
            self.logger.info(f"Alert rule updated: {rule_id}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error updating alert rule: {e}")
            return False
    
    def remove_alert_rule(self, rule_id: str) -> bool:
        """
        Remove an alert rule.
        
        Args:
            rule_id: Rule identifier
            
        Returns:
            True if rule was removed successfully
        """
        try:
            if rule_id in self.alert_rules:
                del self.alert_rules[rule_id]
                self.logger.info(f"Alert rule removed: {rule_id}")
                return True
            return False
            
        except Exception as e:
            self.logger.error(f"Error removing alert rule: {e}")
            return False
    
    def get_active_alerts(self, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        Get active alerts, optionally filtered by severity.
        
        Args:
            severity: Optional severity filter
            
        Returns:
            List of active alerts
        """
        alerts = list(self.active_alerts.values())
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return alerts
    
    def get_alert_history(self, hours: int = 24, severity: Optional[AlertSeverity] = None) -> List[Alert]:
        """
        Get alert history for specified time period.
        
        Args:
            hours: Number of hours to look back
            severity: Optional severity filter
            
        Returns:
            List of historical alerts
        """
        cutoff_time = datetime.now() - timedelta(hours=hours)
        alerts = [a for a in self.alert_history if a.timestamp >= cutoff_time]
        
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        
        # Sort by timestamp (newest first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)
        
        return alerts
    
    def get_alert_metrics(self) -> Dict[str, Any]:
        """Get alert system metrics."""
        return self.alert_metrics.copy()
    
    def _is_alert_suppressed(self, rule_id: str, metric_value: float) -> bool:
        """Check if alert should be suppressed due to cooldown or correlation rules."""
        try:
            rule = self.alert_rules.get(rule_id)
            if not rule:
                return True
            
            # Check cooldown period
            cutoff_time = datetime.now() - timedelta(minutes=rule.cooldown_minutes)
            recent_alerts = [a for a in self.alert_history 
                           if a.rule_id == rule_id and a.timestamp >= cutoff_time]
            
            if recent_alerts:
                return True
            
            # Check suppression rules
            for suppression_rule in self.suppression_rules:
                if self._matches_suppression_rule(rule_id, metric_value, suppression_rule):
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking alert suppression: {e}")
            return False
    
    def _matches_suppression_rule(self, rule_id: str, metric_value: float, suppression_rule: Dict[str, Any]) -> bool:
        """Check if alert matches a suppression rule."""
        # This would implement suppression rule logic
        # For now, return False (no suppression)
        return False
    
    def _generate_alert_message(self, rule: AlertRule, metric_value: float) -> str:
        """Generate alert message based on rule and metric value."""
        condition_text = {
            'gt': 'exceeded',
            'gte': 'exceeded',
            'lt': 'fell below',
            'lte': 'fell below',
            'eq': 'equals'
        }.get(rule.condition, 'triggered')
        
        return f"{rule.metric_name} {condition_text} threshold: {metric_value} (threshold: {rule.threshold_value})"
    
    async def _queue_alert_notification(self, alert: Alert) -> None:
        """Queue alert for notification delivery."""
        try:
            rule = self.alert_rules.get(alert.rule_id)
            if not rule:
                return
            
            # Send notifications through configured channels
            for channel in rule.notification_channels:
                await self._send_notification(alert, channel)
                
        except Exception as e:
            self.logger.error(f"Error queuing alert notification: {e}")
    
    async def _send_notification(self, alert: Alert, channel: NotificationChannel) -> bool:
        """
        Send notification through specified channel.
        
        Args:
            alert: Alert to send notification for
            channel: Notification channel
            
        Returns:
            True if notification was sent successfully
        """
        try:
            if channel == NotificationChannel.LOG:
                return await self._send_log_notification(alert)
            elif channel == NotificationChannel.EMAIL:
                return await self._send_email_notification(alert)
            elif channel == NotificationChannel.WEBHOOK:
                return await self._send_webhook_notification(alert)
            elif channel == NotificationChannel.STREAMLIT:
                return await self._send_streamlit_notification(alert)
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error sending notification via {channel.value}: {e}")
            return False
    
    async def _send_log_notification(self, alert: Alert) -> bool:
        """Send log notification."""
        log_level = {
            AlertSeverity.INFO: logging.INFO,
            AlertSeverity.WARNING: logging.WARNING,
            AlertSeverity.ERROR: logging.ERROR,
            AlertSeverity.CRITICAL: logging.CRITICAL
        }.get(alert.severity, logging.INFO)
        
        self.logger.log(log_level, f"ALERT: {alert.title} - {alert.message}")
        return True
    
    async def _send_email_notification(self, alert: Alert) -> bool:
        """Send email notification."""
        try:
            if not self.notification_config.email_smtp_server or not self.notification_config.email_to:
                return False
            
            # Create email message
            msg = MIMEMultipart()
            msg['From'] = self.notification_config.email_from or 'alerts@monitoring.system'
            msg['To'] = ', '.join(self.notification_config.email_to)
            msg['Subject'] = f"[{alert.severity.value.upper()}] {alert.title}"
            
            # Email body
            body = f"""
Alert Details:
- Alert ID: {alert.alert_id}
- Severity: {alert.severity.value.upper()}
- Timestamp: {alert.timestamp.strftime('%Y-%m-%d %H:%M:%S')}
- Message: {alert.message}
- Metric Value: {alert.metric_value}
- Threshold: {alert.threshold_value}
- Session ID: {alert.session_id or 'N/A'}

Additional Details:
{json.dumps(alert.details, indent=2) if alert.details else 'None'}
"""
            
            msg.attach(MIMEText(body, 'plain'))
            
            # Send email
            server = smtplib.SMTP(self.notification_config.email_smtp_server, self.notification_config.email_smtp_port)
            server.starttls()
            
            if self.notification_config.email_username and self.notification_config.email_password:
                server.login(self.notification_config.email_username, self.notification_config.email_password)
            
            server.send_message(msg)
            server.quit()
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending email notification: {e}")
            return False
    
    async def _send_webhook_notification(self, alert: Alert) -> bool:
        """Send webhook notification."""
        try:
            if not self.notification_config.webhook_urls:
                return False
            
            import aiohttp
            
            payload = {
                'alert_id': alert.alert_id,
                'rule_id': alert.rule_id,
                'severity': alert.severity.value,
                'title': alert.title,
                'message': alert.message,
                'timestamp': alert.timestamp.isoformat(),
                'metric_value': alert.metric_value,
                'threshold_value': alert.threshold_value,
                'session_id': alert.session_id,
                'details': alert.details
            }
            
            success_count = 0
            
            async with aiohttp.ClientSession() as session:
                for webhook_url in self.notification_config.webhook_urls:
                    try:
                        async with session.post(
                            webhook_url,
                            json=payload,
                            timeout=aiohttp.ClientTimeout(total=self.notification_config.webhook_timeout)
                        ) as response:
                            if response.status == 200:
                                success_count += 1
                    except Exception as e:
                        self.logger.error(f"Error sending webhook to {webhook_url}: {e}")
            
            return success_count > 0
            
        except Exception as e:
            self.logger.error(f"Error sending webhook notification: {e}")
            return False
    
    async def _send_streamlit_notification(self, alert: Alert) -> bool:
        """Send Streamlit notification (store for display in UI)."""
        try:
            # This would integrate with Streamlit's notification system
            # For now, just log that it would be displayed
            self.logger.info(f"Streamlit notification: {alert.title}")
            return True
            
        except Exception as e:
            self.logger.error(f"Error sending Streamlit notification: {e}")
            return False
    
    def _update_resolution_time_metric(self, resolution_time: float) -> None:
        """Update average resolution time metric."""
        try:
            current_avg = self.alert_metrics['average_resolution_time']
            resolved_count = self.alert_metrics['alerts_by_status'][AlertStatus.RESOLVED.value]
            
            if resolved_count == 1:
                self.alert_metrics['average_resolution_time'] = resolution_time
            else:
                # Calculate running average
                self.alert_metrics['average_resolution_time'] = (
                    (current_avg * (resolved_count - 1) + resolution_time) / resolved_count
                )
                
        except Exception as e:
            self.logger.error(f"Error updating resolution time metric: {e}")
    
    async def _alert_processing_loop(self) -> None:
        """Background loop for processing alerts."""
        while self.is_running:
            try:
                # Process any pending alert operations
                await self._process_pending_notifications()
                
                # Check for auto-resolution conditions
                await self._check_auto_resolution()
                
                await asyncio.sleep(30)  # Process every 30 seconds
                
            except Exception as e:
                self.logger.error(f"Error in alert processing loop: {e}")
                await asyncio.sleep(60)
    
    async def _escalation_loop(self) -> None:
        """Background loop for alert escalation."""
        while self.is_running:
            try:
                # Check for alerts that need escalation
                await self._check_escalation()
                
                await asyncio.sleep(self.config['escalation_check_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in escalation loop: {e}")
                await asyncio.sleep(300)
    
    async def _cleanup_loop(self) -> None:
        """Background loop for cleanup operations."""
        while self.is_running:
            try:
                # Clean up old alerts
                await self._cleanup_old_alerts()
                
                # Limit active alerts
                await self._limit_active_alerts()
                
                await asyncio.sleep(self.config['cleanup_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in cleanup loop: {e}")
                await asyncio.sleep(1800)
    
    async def _process_pending_notifications(self) -> None:
        """Process any pending notification retries."""
        # This would implement notification retry logic
        pass
    
    async def _check_auto_resolution(self) -> None:
        """Check for alerts that can be auto-resolved."""
        # This would implement auto-resolution logic based on metric improvements
        pass
    
    async def _check_escalation(self) -> None:
        """Check for alerts that need escalation."""
        # This would implement escalation logic based on time and severity
        pass
    
    async def _cleanup_old_alerts(self) -> None:
        """Clean up old alerts from history."""
        try:
            cutoff_time = datetime.now() - timedelta(days=self.config['alert_retention_days'])
            
            # Remove old alerts from history
            self.alert_history = [a for a in self.alert_history if a.timestamp >= cutoff_time]
            
        except Exception as e:
            self.logger.error(f"Error cleaning up old alerts: {e}")
    
    async def _limit_active_alerts(self) -> None:
        """Limit the number of active alerts."""
        try:
            if len(self.active_alerts) > self.config['max_active_alerts']:
                # Remove oldest resolved alerts first
                resolved_alerts = [(k, v) for k, v in self.active_alerts.items() 
                                 if v.status == AlertStatus.RESOLVED]
                resolved_alerts.sort(key=lambda x: x[1].resolved_at or x[1].timestamp)
                
                for alert_id, _ in resolved_alerts[:len(resolved_alerts)//2]:
                    del self.active_alerts[alert_id]
                    
        except Exception as e:
            self.logger.error(f"Error limiting active alerts: {e}")
    
    async def _load_alert_configuration(self) -> None:
        """Load alert configuration from file."""
        try:
            config_path = Path("config/alert_system.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Load alert rules
                if 'alert_rules' in config_data:
                    for rule_data in config_data['alert_rules']:
                        rule = AlertRule.from_dict(rule_data)
                        self.alert_rules[rule.rule_id] = rule
                
                # Load notification config
                if 'notification_config' in config_data:
                    self.notification_config = NotificationConfig(**config_data['notification_config'])
                
                self.logger.info("Alert configuration loaded")
                
        except Exception as e:
            self.logger.warning(f"Could not load alert configuration: {e}")
    
    async def _save_alert_configuration(self) -> None:
        """Save alert configuration to file."""
        try:
            config_path = Path("config/alert_system.json")
            config_path.parent.mkdir(exist_ok=True)
            
            config_data = {
                'alert_rules': [rule.to_dict() for rule in self.alert_rules.values()],
                'notification_config': asdict(self.notification_config)
            }
            
            with open(config_path, 'w') as f:
                json.dump(config_data, f, indent=2)
            
            self.logger.info("Alert configuration saved")
            
        except Exception as e:
            self.logger.error(f"Could not save alert configuration: {e}")