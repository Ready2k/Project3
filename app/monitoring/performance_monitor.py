"""Performance monitoring and alerting system for AAA application."""

import time
import asyncio
import threading
from typing import Dict, Any, List, Optional, Callable, Union
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from collections import defaultdict, deque
import statistics
import json

from app.utils.logger import app_logger
from app.utils.error_boundaries import error_boundary


class MetricType(Enum):
    """Types of performance metrics."""

    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


class AlertSeverity(Enum):
    """Alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class MetricValue:
    """A single metric measurement."""

    name: str
    value: Union[int, float]
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metric_type: MetricType = MetricType.GAUGE


@dataclass
class AlertRule:
    """Performance alert rule configuration."""

    name: str
    metric_name: str
    condition: str  # e.g., "> 1000", "< 0.95", "== 0"
    threshold: Union[int, float]
    severity: AlertSeverity
    window_minutes: int = 5
    min_samples: int = 1
    callback: Optional[Callable[[Dict[str, Any]], None]] = None
    enabled: bool = True


@dataclass
class Alert:
    """Performance alert instance."""

    rule_name: str
    metric_name: str
    current_value: Union[int, float]
    threshold: Union[int, float]
    severity: AlertSeverity
    message: str
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)


class PerformanceMetrics:
    """Collects and manages performance metrics."""

    def __init__(self, max_history: int = 10000) -> None:
        self.max_history = max_history
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=max_history))
        self._counters: Dict[str, float] = defaultdict(float)
        self._gauges: Dict[str, float] = defaultdict(float)
        self._histograms: Dict[str, List[float]] = defaultdict(list)
        self._lock = threading.RLock()

    def increment_counter(
        self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Increment a counter metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._counters[key] += value
            self._add_metric(
                MetricValue(
                    name=name,
                    value=self._counters[key],
                    timestamp=datetime.now(),
                    labels=labels or {},
                    metric_type=MetricType.COUNTER,
                )
            )

    def set_gauge(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Set a gauge metric value."""
        with self._lock:
            key = self._make_key(name, labels)
            self._gauges[key] = value
            self._add_metric(
                MetricValue(
                    name=name,
                    value=value,
                    timestamp=datetime.now(),
                    labels=labels or {},
                    metric_type=MetricType.GAUGE,
                )
            )

    def record_histogram(
        self, name: str, value: float, labels: Optional[Dict[str, str]] = None
    ) -> None:
        """Record a value in a histogram metric."""
        with self._lock:
            key = self._make_key(name, labels)
            self._histograms[key].append(value)

            # Keep only recent values
            if len(self._histograms[key]) > 1000:
                self._histograms[key] = self._histograms[key][-1000:]

            self._add_metric(
                MetricValue(
                    name=name,
                    value=value,
                    timestamp=datetime.now(),
                    labels=labels or {},
                    metric_type=MetricType.HISTOGRAM,
                )
            )

    def time_operation(self, name: str, labels: Optional[Dict[str, str]] = None):
        """Context manager for timing operations."""
        return TimerContext(self, name, labels)

    def _make_key(self, name: str, labels: Optional[Dict[str, str]]) -> str:
        """Create a unique key for metric with labels."""
        if not labels:
            return name

        label_str = ",".join(f"{k}={v}" for k, v in sorted(labels.items()))
        return f"{name}{{{label_str}}}"

    def _add_metric(self, metric: MetricValue):
        """Add a metric to the history."""
        key = self._make_key(metric.name, metric.labels)
        self._metrics[key].append(metric)

    def get_current_value(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Optional[float]:
        """Get the current value of a metric."""
        with self._lock:
            key = self._make_key(name, labels)

            if key in self._counters:
                return self._counters[key]
            elif key in self._gauges:
                return self._gauges[key]
            elif key in self._histograms and self._histograms[key]:
                return self._histograms[key][-1]

            return None

    def get_histogram_stats(
        self, name: str, labels: Optional[Dict[str, str]] = None
    ) -> Dict[str, float]:
        """Get statistics for a histogram metric."""
        with self._lock:
            key = self._make_key(name, labels)
            values = self._histograms.get(key, [])

            if not values:
                return {}

            return {
                "count": len(values),
                "min": min(values),
                "max": max(values),
                "mean": statistics.mean(values),
                "median": statistics.median(values),
                "p95": self._percentile(values, 0.95),
                "p99": self._percentile(values, 0.99),
            }

    def _percentile(self, values: List[float], percentile: float) -> float:
        """Calculate percentile of values."""
        if not values:
            return 0.0

        sorted_values = sorted(values)
        index = int(len(sorted_values) * percentile)
        return sorted_values[min(index, len(sorted_values) - 1)]

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a summary of all metrics."""
        with self._lock:
            summary = {
                "counters": dict(self._counters),
                "gauges": dict(self._gauges),
                "histograms": {},
            }

            for key, values in self._histograms.items():
                if values:
                    summary["histograms"][key] = self.get_histogram_stats(
                        key.split("{")[0], {}
                    )

            return summary


class TimerContext:
    """Context manager for timing operations."""

    def __init__(
        self,
        metrics: PerformanceMetrics,
        name: str,
        labels: Optional[Dict[str, str]] = None,
    ):
        self.metrics = metrics
        self.name = name
        self.labels = labels
        self.start_time = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.start_time:
            duration = time.time() - self.start_time
            self.metrics.record_histogram(
                f"{self.name}_duration_seconds", duration, self.labels
            )

            # Also record as a timer metric
            self.metrics.set_gauge(
                f"{self.name}_last_duration_seconds", duration, self.labels
            )


class AlertManager:
    """Manages performance alerts and notifications."""

    def __init__(self, metrics: PerformanceMetrics):
        self.metrics = metrics
        self.rules: Dict[str, AlertRule] = {}
        self.active_alerts: Dict[str, Alert] = {}
        self.alert_history: List[Alert] = []
        self._lock = threading.RLock()
        self._running = False
        self._check_task = None

    def add_rule(self, rule: AlertRule):
        """Add an alert rule."""
        with self._lock:
            self.rules[rule.name] = rule
            app_logger.info(f"Added alert rule: {rule.name}")

    def remove_rule(self, rule_name: str):
        """Remove an alert rule."""
        with self._lock:
            if rule_name in self.rules:
                del self.rules[rule_name]
                app_logger.info(f"Removed alert rule: {rule_name}")

    def start_monitoring(self, check_interval_seconds: int = 30):
        """Start the alert monitoring loop."""
        if self._running:
            return

        self._running = True

        async def monitor_loop():
            while self._running:
                try:
                    await self._check_alerts()
                    await asyncio.sleep(check_interval_seconds)
                except Exception as e:
                    app_logger.error(f"Error in alert monitoring loop: {e}")
                    await asyncio.sleep(check_interval_seconds)

        self._check_task = asyncio.create_task(monitor_loop())
        app_logger.info("Started alert monitoring")

    def stop_monitoring(self):
        """Stop the alert monitoring loop."""
        self._running = False
        if self._check_task:
            self._check_task.cancel()
        app_logger.info("Stopped alert monitoring")

    async def _check_alerts(self):
        """Check all alert rules."""
        with self._lock:
            for rule_name, rule in self.rules.items():
                if not rule.enabled:
                    continue

                try:
                    await self._check_rule(rule)
                except Exception as e:
                    app_logger.error(f"Error checking alert rule {rule_name}: {e}")

    async def _check_rule(self, rule: AlertRule):
        """Check a specific alert rule."""
        current_value = self.metrics.get_current_value(rule.metric_name)

        if current_value is None:
            return

        # Evaluate condition
        condition_met = self._evaluate_condition(
            current_value, rule.condition, rule.threshold
        )

        alert_key = f"{rule.name}_{rule.metric_name}"

        if condition_met:
            # Create or update alert
            if alert_key not in self.active_alerts:
                alert = Alert(
                    rule_name=rule.name,
                    metric_name=rule.metric_name,
                    current_value=current_value,
                    threshold=rule.threshold,
                    severity=rule.severity,
                    message=f"Metric {rule.metric_name} {rule.condition} {rule.threshold} (current: {current_value})",
                    timestamp=datetime.now(),
                )

                self.active_alerts[alert_key] = alert
                self.alert_history.append(alert)

                # Trigger callback
                if rule.callback:
                    try:
                        await self._call_alert_callback(rule.callback, alert)
                    except Exception as e:
                        app_logger.error(f"Error calling alert callback: {e}")

                app_logger.warning(f"ALERT: {alert.message}")
        else:
            # Clear alert if it exists
            if alert_key in self.active_alerts:
                del self.active_alerts[alert_key]
                app_logger.info(f"Alert cleared: {rule.name}")

    def _evaluate_condition(
        self, value: float, condition: str, threshold: float
    ) -> bool:
        """Evaluate an alert condition."""
        condition = condition.strip()

        if condition.startswith(">="):
            return value >= threshold
        elif condition.startswith("<="):
            return value <= threshold
        elif condition.startswith(">"):
            return value > threshold
        elif condition.startswith("<"):
            return value < threshold
        elif condition.startswith("=="):
            return abs(value - threshold) < 0.001  # Float comparison
        elif condition.startswith("!="):
            return abs(value - threshold) >= 0.001
        else:
            app_logger.warning(f"Unknown condition: {condition}")
            return False

    async def _call_alert_callback(self, callback: Callable, alert: Alert):
        """Call an alert callback function."""
        alert_data = {
            "rule_name": alert.rule_name,
            "metric_name": alert.metric_name,
            "current_value": alert.current_value,
            "threshold": alert.threshold,
            "severity": alert.severity.value,
            "message": alert.message,
            "timestamp": alert.timestamp.isoformat(),
        }

        if asyncio.iscoroutinefunction(callback):
            await callback(alert_data)
        else:
            callback(alert_data)

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts."""
        with self._lock:
            return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get recent alert history."""
        with self._lock:
            return self.alert_history[-limit:]


class PerformanceMonitor:
    """Main performance monitoring system."""

    def __init__(self, config_path: Optional[str] = None):
        self.metrics = PerformanceMetrics()
        self.alert_manager = AlertManager(self.metrics)
        self.config_path = config_path
        self._setup_default_metrics()
        self._setup_default_alerts()

    def _setup_default_metrics(self):
        """Setup default application metrics."""
        # API metrics
        self.metrics.set_gauge("aaa_api_requests_total", 0)
        self.metrics.set_gauge("aaa_api_request_duration_seconds", 0)
        self.metrics.set_gauge("aaa_api_errors_total", 0)

        # LLM metrics
        self.metrics.set_gauge("aaa_llm_requests_total", 0)
        self.metrics.set_gauge("aaa_llm_request_duration_seconds", 0)
        self.metrics.set_gauge("aaa_llm_tokens_used", 0)
        self.metrics.set_gauge("aaa_llm_errors_total", 0)

        # Session metrics
        self.metrics.set_gauge("aaa_active_sessions", 0)
        self.metrics.set_gauge("aaa_session_duration_seconds", 0)

        # System metrics
        self.metrics.set_gauge("aaa_memory_usage_bytes", 0)
        self.metrics.set_gauge("aaa_cpu_usage_percent", 0)

    def _setup_default_alerts(self):
        """Setup default alert rules."""
        # High error rate alert
        self.alert_manager.add_rule(
            AlertRule(
                name="high_api_error_rate",
                metric_name="aaa_api_errors_total",
                condition=">",
                threshold=10,
                severity=AlertSeverity.WARNING,
                window_minutes=5,
                callback=self._default_alert_callback,
            )
        )

        # Slow API response alert
        self.alert_manager.add_rule(
            AlertRule(
                name="slow_api_response",
                metric_name="aaa_api_request_duration_seconds",
                condition=">",
                threshold=30.0,
                severity=AlertSeverity.WARNING,
                window_minutes=1,
                callback=self._default_alert_callback,
            )
        )

        # High LLM token usage alert
        self.alert_manager.add_rule(
            AlertRule(
                name="high_llm_token_usage",
                metric_name="aaa_llm_tokens_used",
                condition=">",
                threshold=100000,
                severity=AlertSeverity.INFO,
                window_minutes=60,
                callback=self._default_alert_callback,
            )
        )

    async def _default_alert_callback(self, alert_data: Dict[str, Any]):
        """Default alert callback that logs alerts."""
        severity = alert_data["severity"]
        message = alert_data["message"]

        if severity == "critical":
            app_logger.critical(f"CRITICAL ALERT: {message}")
        elif severity == "error":
            app_logger.error(f"ERROR ALERT: {message}")
        elif severity == "warning":
            app_logger.warning(f"WARNING ALERT: {message}")
        else:
            app_logger.info(f"INFO ALERT: {message}")

    @error_boundary("performance_monitor_start")
    def start_monitoring(self, check_interval_seconds: int = 30):
        """Start performance monitoring."""
        self.alert_manager.start_monitoring(check_interval_seconds)
        app_logger.info("Performance monitoring started")

    def stop_monitoring(self):
        """Stop performance monitoring."""
        self.alert_manager.stop_monitoring()
        app_logger.info("Performance monitoring stopped")

    def record_api_request(
        self, endpoint: str, method: str, duration: float, status_code: int
    ):
        """Record an API request metric."""
        labels = {"endpoint": endpoint, "method": method, "status": str(status_code)}

        self.metrics.increment_counter("aaa_api_requests_total", 1.0, labels)
        self.metrics.record_histogram(
            "aaa_api_request_duration_seconds", duration, labels
        )

        if status_code >= 400:
            self.metrics.increment_counter("aaa_api_errors_total", 1.0, labels)

    def record_llm_request(
        self, provider: str, model: str, duration: float, tokens: int, success: bool
    ):
        """Record an LLM request metric."""
        labels = {"provider": provider, "model": model, "success": str(success)}

        self.metrics.increment_counter("aaa_llm_requests_total", 1.0, labels)
        self.metrics.record_histogram(
            "aaa_llm_request_duration_seconds", duration, labels
        )
        self.metrics.increment_counter("aaa_llm_tokens_used", tokens, labels)

        if not success:
            self.metrics.increment_counter("aaa_llm_errors_total", 1.0, labels)

    def record_session_metric(
        self, session_id: str, phase: str, duration: Optional[float] = None
    ):
        """Record session-related metrics."""
        labels = {"phase": phase}

        if duration:
            self.metrics.record_histogram(
                "aaa_session_duration_seconds", duration, labels
            )

    def update_system_metrics(self):
        """Update system resource metrics with real data from tech stack generation."""
        try:
            import psutil

            # Memory usage
            memory = psutil.virtual_memory()
            self.metrics.set_gauge("aaa_memory_usage_bytes", memory.used)
            self.metrics.set_gauge("aaa_memory_usage_percent", memory.percent)

            # CPU usage
            cpu_percent = psutil.cpu_percent(interval=1)
            self.metrics.set_gauge("aaa_cpu_usage_percent", cpu_percent)

            # Connect to real tech stack generation metrics
            self._update_tech_stack_metrics()

        except ImportError:
            # psutil not available
            pass
        except Exception as e:
            app_logger.warning(f"Failed to update system metrics: {e}")

    def _update_tech_stack_metrics(self):
        """Update tech stack generation specific metrics from real data."""
        try:
            # Try to get real data from monitoring integration service
            from app.utils.imports import optional_service

            integration_service = optional_service(
                "tech_stack_monitoring_integration", context="PerformanceMonitor"
            )

            if integration_service:
                # Get real-time service metrics
                service_metrics = integration_service.get_service_metrics()
                active_sessions = integration_service.get_active_sessions()

                # Update active sessions metric
                self.metrics.set_gauge(
                    "aaa_active_sessions", service_metrics.get("active_sessions", 0)
                )

                # Calculate average session duration from active sessions
                if active_sessions:
                    total_duration = sum(
                        session.get("duration_seconds", 0)
                        for session in active_sessions
                    )
                    avg_duration = total_duration / len(active_sessions)
                    self.metrics.set_gauge("aaa_session_duration_seconds", avg_duration)

                # Update event buffer metrics
                self.metrics.set_gauge(
                    "aaa_monitoring_events_buffered",
                    service_metrics.get("total_events_buffered", 0),
                )

                # Process session events for detailed metrics
                for session_info in active_sessions:
                    session_id = session_info["session_id"]
                    session_events = integration_service.get_session_events(session_id)

                    # Extract performance metrics from real events
                    self._process_session_performance_metrics(
                        session_id, session_events
                    )

            # Try to get metrics from tech stack monitor
            tech_monitor = optional_service(
                "tech_stack_monitor", context="PerformanceMonitor"
            )
            if tech_monitor:
                recent_metrics = tech_monitor._get_recent_metrics(hours=1)

                # Extract LLM performance metrics
                llm_metrics = [
                    m for m in recent_metrics if m.name == "llm_response_time"
                ]
                if llm_metrics:
                    avg_llm_time = sum(m.value for m in llm_metrics) / len(llm_metrics)
                    self.metrics.set_gauge(
                        "aaa_llm_request_duration_seconds", avg_llm_time
                    )

                # Extract processing time metrics
                processing_metrics = [
                    m for m in recent_metrics if m.name == "processing_time"
                ]
                if processing_metrics:
                    avg_processing_time = sum(
                        m.value for m in processing_metrics
                    ) / len(processing_metrics)
                    self.metrics.set_gauge(
                        "aaa_api_request_duration_seconds", avg_processing_time
                    )

                # Count error metrics
                error_count = len(
                    [
                        m
                        for m in recent_metrics
                        if "error" in m.name.lower() or not getattr(m, "success", True)
                    ]
                )
                self.metrics.set_gauge("aaa_api_errors_total", error_count)

        except Exception as e:
            app_logger.debug(f"Could not update tech stack metrics from real data: {e}")

    def _process_session_performance_metrics(
        self, session_id: str, session_events: List[Dict[str, Any]]
    ):
        """Process session events to extract performance metrics."""
        try:
            # Extract LLM call metrics
            llm_events = [
                e for e in session_events if e.get("event_type") == "llm_call_complete"
            ]
            for event in llm_events:
                duration_ms = event.get("duration_ms", 0)
                data = event.get("data", {})
                provider = data.get("provider", "unknown")
                model = data.get("model", "unknown")
                token_usage = data.get("token_usage", {})
                success = event.get("success", True)

                # Record LLM request metrics
                self.record_llm_request(
                    provider=provider,
                    model=model,
                    duration=duration_ms / 1000.0,  # Convert to seconds
                    tokens=token_usage.get("total_tokens", 0),
                    success=success,
                )

            # Extract parsing performance metrics
            parsing_events = [
                e for e in session_events if e.get("event_type") == "parsing_complete"
            ]
            for event in parsing_events:
                duration_ms = event.get("duration_ms", 0)
                if duration_ms > 0:
                    self.metrics.record_histogram(
                        "aaa_parsing_duration_seconds", duration_ms / 1000.0
                    )

            # Extract validation performance metrics
            validation_events = [
                e
                for e in session_events
                if e.get("event_type") == "validation_complete"
            ]
            for event in validation_events:
                duration_ms = event.get("duration_ms", 0)
                if duration_ms > 0:
                    self.metrics.record_histogram(
                        "aaa_validation_duration_seconds", duration_ms / 1000.0
                    )

            # Calculate total session processing time
            session_start = None
            session_end = None

            for event in session_events:
                event_time = event.get("timestamp")
                if event_time:
                    if event.get("event_type") == "session_start":
                        session_start = event_time
                    elif event.get("event_type") in [
                        "session_complete",
                        "session_error",
                    ]:
                        session_end = event_time

            if session_start and session_end:
                try:
                    from datetime import datetime

                    start_time = datetime.fromisoformat(
                        session_start.replace("Z", "+00:00")
                    )
                    end_time = datetime.fromisoformat(
                        session_end.replace("Z", "+00:00")
                    )
                    total_duration = (end_time - start_time).total_seconds()

                    self.record_session_metric(session_id, "complete", total_duration)
                except Exception as time_error:
                    app_logger.debug(
                        f"Could not calculate session duration: {time_error}"
                    )

        except Exception as e:
            app_logger.error(
                f"Error processing session performance metrics for {session_id}: {e}"
            )

    def get_metrics_summary(self) -> Dict[str, Any]:
        """Get a comprehensive metrics summary."""
        return {
            "metrics": self.metrics.get_metrics_summary(),
            "active_alerts": [
                {
                    "rule_name": alert.rule_name,
                    "metric_name": alert.metric_name,
                    "current_value": alert.current_value,
                    "threshold": alert.threshold,
                    "severity": alert.severity.value,
                    "message": alert.message,
                    "timestamp": alert.timestamp.isoformat(),
                }
                for alert in self.alert_manager.get_active_alerts()
            ],
            "alert_rules": [
                {
                    "name": rule.name,
                    "metric_name": rule.metric_name,
                    "condition": rule.condition,
                    "threshold": rule.threshold,
                    "severity": rule.severity.value,
                    "enabled": rule.enabled,
                }
                for rule in self.alert_manager.rules.values()
            ],
        }

    def export_metrics(self, file_path: str):
        """Export metrics to a file."""
        summary = self.get_metrics_summary()

        with open(file_path, "w") as f:
            json.dump(summary, f, indent=2, default=str)

        app_logger.info(f"Metrics exported to {file_path}")


# Global performance monitor instance
_global_monitor: Optional[PerformanceMonitor] = None


def get_performance_monitor() -> PerformanceMonitor:
    """Get the global performance monitor instance."""
    global _global_monitor
    if _global_monitor is None:
        _global_monitor = PerformanceMonitor()
    return _global_monitor


def start_performance_monitoring(check_interval_seconds: int = 30):
    """Start global performance monitoring."""
    monitor = get_performance_monitor()
    monitor.start_monitoring(check_interval_seconds)


def stop_performance_monitoring():
    """Stop global performance monitoring."""
    global _global_monitor
    if _global_monitor:
        _global_monitor.stop_monitoring()


# Decorator for automatic performance monitoring
def monitor_performance(metric_name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator to automatically monitor function performance."""

    def decorator(func):
        if asyncio.iscoroutinefunction(func):

            async def async_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                with monitor.metrics.time_operation(metric_name, labels):
                    return await func(*args, **kwargs)

            return async_wrapper
        else:

            def sync_wrapper(*args, **kwargs):
                monitor = get_performance_monitor()
                with monitor.metrics.time_operation(metric_name, labels):
                    return func(*args, **kwargs)

            return sync_wrapper

    return decorator
