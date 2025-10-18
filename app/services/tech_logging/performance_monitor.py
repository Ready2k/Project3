"""
Performance monitoring service for tech stack generation.

Provides comprehensive performance monitoring including timing, resource usage,
throughput metrics, and performance optimization recommendations.
"""

from typing import Dict, Any, List, Optional
from dataclasses import dataclass, asdict
from datetime import datetime, timedelta
import time
import threading
import psutil
import gc
from collections import defaultdict, deque
from contextlib import contextmanager
from enum import Enum

from .tech_stack_logger import TechStackLogger, LogCategory


class MetricType(Enum):
    """Performance metric types."""

    TIMING = "timing"
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    THROUGHPUT = "throughput"


@dataclass
class PerformanceMetric:
    """Individual performance metric."""

    name: str
    metric_type: MetricType
    value: float
    timestamp: str
    tags: Dict[str, str]
    component: str
    operation: str
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class ResourceUsage:
    """System resource usage snapshot."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    disk_io_read_mb: float
    disk_io_write_mb: float
    network_io_sent_mb: float
    network_io_recv_mb: float
    gc_collections: Dict[str, int]


@dataclass
class PerformanceAlert:
    """Performance alert for threshold violations."""

    alert_id: str
    metric_name: str
    threshold_type: str  # "max", "min", "avg"
    threshold_value: float
    actual_value: float
    severity: str  # "warning", "critical"
    component: str
    operation: str
    timestamp: str
    message: str


class PerformanceMonitor:
    """
    Comprehensive performance monitoring service for tech stack generation.

    Provides timing, resource usage, throughput monitoring, and performance
    optimization recommendations with alerting capabilities.
    """

    def __init__(self, tech_stack_logger: TechStackLogger):
        """
        Initialize performance monitor.

        Args:
            tech_stack_logger: Main tech stack logger instance
        """
        self.logger = tech_stack_logger
        self._metrics: Dict[str, deque] = defaultdict(lambda: deque(maxlen=1000))
        self._active_timers: Dict[str, float] = {}
        self._counters: Dict[str, int] = defaultdict(int)
        self._gauges: Dict[str, float] = {}
        self._resource_history: deque = deque(maxlen=100)
        self._thresholds: Dict[str, Dict[str, float]] = {}
        self._alerts: List[PerformanceAlert] = []
        self._monitoring_enabled = False
        self._monitoring_thread: Optional[threading.Thread] = None
        self._stop_monitoring = threading.Event()

        # Initialize baseline resource usage
        self._baseline_resources: Optional[ResourceUsage] = None

    def start_monitoring(
        self, interval_seconds: float = 5.0, enable_resource_monitoring: bool = True
    ) -> None:
        """
        Start performance monitoring.

        Args:
            interval_seconds: Monitoring interval in seconds
            enable_resource_monitoring: Whether to monitor system resources
        """
        if self._monitoring_enabled:
            return

        self._monitoring_enabled = True
        self._enable_resource_monitoring = enable_resource_monitoring
        self._monitoring_interval = interval_seconds

        if enable_resource_monitoring:
            self._monitoring_thread = threading.Thread(
                target=self._resource_monitoring_loop, daemon=True
            )
            self._monitoring_thread.start()

        # Capture baseline
        if enable_resource_monitoring:
            self._baseline_resources = self._capture_resource_usage()

        self.logger.log_info(
            LogCategory.PERFORMANCE,
            "PerformanceMonitor",
            "start_monitoring",
            f"Performance monitoring started (interval: {interval_seconds}s)",
            {
                "interval_seconds": interval_seconds,
                "resource_monitoring": enable_resource_monitoring,
            },
        )

    def stop_monitoring(self) -> None:
        """Stop performance monitoring."""
        if not self._monitoring_enabled:
            return

        self._monitoring_enabled = False
        self._stop_monitoring.set()

        if self._monitoring_thread:
            self._monitoring_thread.join(timeout=5.0)
            self._monitoring_thread = None

        self.logger.log_info(
            LogCategory.PERFORMANCE,
            "PerformanceMonitor",
            "stop_monitoring",
            "Performance monitoring stopped",
            {},
        )

    @contextmanager
    def time_operation(
        self, operation_name: str, component: str, tags: Optional[Dict[str, str]] = None
    ):
        """
        Context manager for timing operations.

        Args:
            operation_name: Name of the operation
            component: Component performing the operation
            tags: Additional tags for the metric
        """
        timer_id = f"{component}_{operation_name}_{int(time.time() * 1000)}"
        start_time = time.time()

        try:
            yield timer_id
        finally:
            duration_ms = (time.time() - start_time) * 1000
            self.record_timing(operation_name, duration_ms, component, tags or {})

    def record_timing(
        self,
        operation_name: str,
        duration_ms: float,
        component: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record timing metric.

        Args:
            operation_name: Name of the operation
            duration_ms: Duration in milliseconds
            component: Component that performed the operation
            tags: Additional tags
        """
        metric = PerformanceMetric(
            name=f"{operation_name}_duration",
            metric_type=MetricType.TIMING,
            value=duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            tags=tags or {},
            component=component,
            operation=operation_name,
        )

        self._metrics[metric.name].append(metric)

        # Check thresholds
        self._check_thresholds(metric)

        # Log if significant duration
        if duration_ms > 1000:  # Log operations taking more than 1 second
            self.logger.log_info(
                LogCategory.PERFORMANCE,
                component,
                operation_name,
                f"Operation completed in {duration_ms:.2f}ms",
                {"duration_ms": duration_ms, "tags": tags},
            )

    def increment_counter(
        self,
        counter_name: str,
        component: str,
        operation: str,
        increment: int = 1,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Increment a counter metric.

        Args:
            counter_name: Name of the counter
            component: Component incrementing the counter
            operation: Operation context
            increment: Amount to increment by
            tags: Additional tags
        """
        self._counters[counter_name] += increment

        metric = PerformanceMetric(
            name=counter_name,
            metric_type=MetricType.COUNTER,
            value=self._counters[counter_name],
            timestamp=datetime.utcnow().isoformat(),
            tags=tags or {},
            component=component,
            operation=operation,
        )

        self._metrics[counter_name].append(metric)

        # Log counter updates for debugging
        self.logger.log_debug(
            LogCategory.PERFORMANCE,
            component,
            operation,
            f"Counter {counter_name} incremented to {self._counters[counter_name]}",
            {
                "counter_name": counter_name,
                "current_value": self._counters[counter_name],
                "increment": increment,
                "tags": tags,
            },
        )

    def set_gauge(
        self,
        gauge_name: str,
        value: float,
        component: str,
        operation: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Set a gauge metric value.

        Args:
            gauge_name: Name of the gauge
            value: Gauge value
            component: Component setting the gauge
            operation: Operation context
            tags: Additional tags
        """
        self._gauges[gauge_name] = value

        metric = PerformanceMetric(
            name=gauge_name,
            metric_type=MetricType.GAUGE,
            value=value,
            timestamp=datetime.utcnow().isoformat(),
            tags=tags or {},
            component=component,
            operation=operation,
        )

        self._metrics[gauge_name].append(metric)

        # Check thresholds
        self._check_thresholds(metric)

    def record_throughput(
        self,
        operation_name: str,
        items_processed: int,
        duration_ms: float,
        component: str,
        tags: Optional[Dict[str, str]] = None,
    ) -> None:
        """
        Record throughput metric.

        Args:
            operation_name: Name of the operation
            items_processed: Number of items processed
            duration_ms: Duration in milliseconds
            component: Component performing the operation
            tags: Additional tags
        """
        throughput = (items_processed / duration_ms) * 1000  # items per second

        metric = PerformanceMetric(
            name=f"{operation_name}_throughput",
            metric_type=MetricType.THROUGHPUT,
            value=throughput,
            timestamp=datetime.utcnow().isoformat(),
            tags=tags or {},
            component=component,
            operation=operation_name,
            metadata={"items_processed": items_processed, "duration_ms": duration_ms},
        )

        self._metrics[metric.name].append(metric)

        self.logger.log_info(
            LogCategory.PERFORMANCE,
            component,
            operation_name,
            f"Throughput: {throughput:.2f} items/sec ({items_processed} items in {duration_ms:.2f}ms)",
            {
                "throughput_items_per_sec": throughput,
                "items_processed": items_processed,
                "duration_ms": duration_ms,
                "tags": tags,
            },
        )

    def set_threshold(
        self,
        metric_name: str,
        threshold_type: str,
        threshold_value: float,
        severity: str = "warning",
    ) -> None:
        """
        Set performance threshold for alerting.

        Args:
            metric_name: Name of the metric
            threshold_type: Type of threshold ("max", "min", "avg")
            threshold_value: Threshold value
            severity: Alert severity ("warning", "critical")
        """
        if metric_name not in self._thresholds:
            self._thresholds[metric_name] = {}

        self._thresholds[metric_name][threshold_type] = {
            "value": threshold_value,
            "severity": severity,
        }

        self.logger.log_info(
            LogCategory.PERFORMANCE,
            "PerformanceMonitor",
            "set_threshold",
            f"Set {threshold_type} threshold for {metric_name}: {threshold_value} ({severity})",
            {
                "metric_name": metric_name,
                "threshold_type": threshold_type,
                "threshold_value": threshold_value,
                "severity": severity,
            },
        )

    def _check_thresholds(self, metric: PerformanceMetric) -> None:
        """Check if metric violates any thresholds."""
        if metric.name not in self._thresholds:
            return

        thresholds = self._thresholds[metric.name]

        for threshold_type, threshold_config in thresholds.items():
            threshold_value = threshold_config["value"]
            severity = threshold_config["severity"]
            violated = False

            if threshold_type == "max" and metric.value > threshold_value:
                violated = True
            elif threshold_type == "min" and metric.value < threshold_value:
                violated = True
            elif threshold_type == "avg":
                # Check average of recent values
                recent_metrics = list(self._metrics[metric.name])[
                    -10:
                ]  # Last 10 values
                if recent_metrics:
                    avg_value = sum(m.value for m in recent_metrics) / len(
                        recent_metrics
                    )
                    if avg_value > threshold_value:
                        violated = True

            if violated:
                self._create_alert(metric, threshold_type, threshold_value, severity)

    def _create_alert(
        self,
        metric: PerformanceMetric,
        threshold_type: str,
        threshold_value: float,
        severity: str,
    ) -> None:
        """Create performance alert."""
        alert = PerformanceAlert(
            alert_id=f"{metric.name}_{threshold_type}_{int(time.time())}",
            metric_name=metric.name,
            threshold_type=threshold_type,
            threshold_value=threshold_value,
            actual_value=metric.value,
            severity=severity,
            component=metric.component,
            operation=metric.operation,
            timestamp=metric.timestamp,
            message=f"{metric.name} {threshold_type} threshold violated: {metric.value} > {threshold_value}",
        )

        self._alerts.append(alert)

        # Log alert
        log_level = LogCategory.PERFORMANCE
        if severity == "critical":
            self.logger.log_error(
                log_level,
                metric.component,
                metric.operation,
                alert.message,
                asdict(alert),
            )
        else:
            self.logger.log_warning(
                log_level,
                metric.component,
                metric.operation,
                alert.message,
                asdict(alert),
            )

    def _capture_resource_usage(self) -> ResourceUsage:
        """Capture current system resource usage."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()

            # Disk I/O
            disk_io = psutil.disk_io_counters()
            disk_read_mb = disk_io.read_bytes / (1024 * 1024) if disk_io else 0
            disk_write_mb = disk_io.write_bytes / (1024 * 1024) if disk_io else 0

            # Network I/O
            net_io = psutil.net_io_counters()
            net_sent_mb = net_io.bytes_sent / (1024 * 1024) if net_io else 0
            net_recv_mb = net_io.bytes_recv / (1024 * 1024) if net_io else 0

            # Garbage collection
            gc_stats = {
                f"gen_{i}": gc.get_count()[i] for i in range(len(gc.get_count()))
            }

            return ResourceUsage(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_mb=memory.used / (1024 * 1024),
                disk_io_read_mb=disk_read_mb,
                disk_io_write_mb=disk_write_mb,
                network_io_sent_mb=net_sent_mb,
                network_io_recv_mb=net_recv_mb,
                gc_collections=gc_stats,
            )

        except Exception as e:
            self.logger.log_error(
                LogCategory.PERFORMANCE,
                "PerformanceMonitor",
                "capture_resources",
                f"Failed to capture resource usage: {e}",
                {},
                exception=e,
            )
            return ResourceUsage(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=0.0,
                memory_percent=0.0,
                memory_mb=0.0,
                disk_io_read_mb=0.0,
                disk_io_write_mb=0.0,
                network_io_sent_mb=0.0,
                network_io_recv_mb=0.0,
                gc_collections={},
            )

    def _resource_monitoring_loop(self) -> None:
        """Background thread for resource monitoring."""
        while not self._stop_monitoring.is_set():
            try:
                usage = self._capture_resource_usage()
                self._resource_history.append(usage)

                # Log resource usage if significant changes
                if self._baseline_resources:
                    cpu_diff = abs(
                        usage.cpu_percent - self._baseline_resources.cpu_percent
                    )
                    memory_diff = abs(
                        usage.memory_percent - self._baseline_resources.memory_percent
                    )

                    if cpu_diff > 20 or memory_diff > 10:  # Significant changes
                        self.logger.log_info(
                            LogCategory.PERFORMANCE,
                            "PerformanceMonitor",
                            "resource_monitoring",
                            f"Resource usage: CPU {usage.cpu_percent:.1f}%, Memory {usage.memory_percent:.1f}%",
                            {
                                "cpu_percent": usage.cpu_percent,
                                "memory_percent": usage.memory_percent,
                                "memory_mb": usage.memory_mb,
                            },
                        )

                # Check resource thresholds
                self.set_gauge(
                    "cpu_percent",
                    usage.cpu_percent,
                    "PerformanceMonitor",
                    "resource_monitoring",
                )
                self.set_gauge(
                    "memory_percent",
                    usage.memory_percent,
                    "PerformanceMonitor",
                    "resource_monitoring",
                )

            except Exception as e:
                self.logger.log_error(
                    LogCategory.PERFORMANCE,
                    "PerformanceMonitor",
                    "resource_monitoring",
                    f"Error in resource monitoring: {e}",
                    {},
                    exception=e,
                )

            # Wait for next interval
            self._stop_monitoring.wait(self._monitoring_interval)

    def get_metric_summary(
        self,
        metric_name: Optional[str] = None,
        component: Optional[str] = None,
        time_window_minutes: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Get metric summary statistics.

        Args:
            metric_name: Filter by metric name
            component: Filter by component
            time_window_minutes: Time window in minutes

        Returns:
            Metric summary statistics
        """
        # Filter metrics
        all_metrics = []
        for name, metric_deque in self._metrics.items():
            if metric_name and name != metric_name:
                continue

            for metric in metric_deque:
                if component and metric.component != component:
                    continue

                if time_window_minutes:
                    cutoff_time = datetime.utcnow() - timedelta(
                        minutes=time_window_minutes
                    )
                    metric_time = datetime.fromisoformat(metric.timestamp)
                    if metric_time < cutoff_time:
                        continue

                all_metrics.append(metric)

        if not all_metrics:
            return {}

        # Calculate statistics by metric type
        timing_metrics = [m for m in all_metrics if m.metric_type == MetricType.TIMING]
        counter_metrics = [
            m for m in all_metrics if m.metric_type == MetricType.COUNTER
        ]
        gauge_metrics = [m for m in all_metrics if m.metric_type == MetricType.GAUGE]
        throughput_metrics = [
            m for m in all_metrics if m.metric_type == MetricType.THROUGHPUT
        ]

        summary = {
            "total_metrics": len(all_metrics),
            "metric_types": {
                "timing": len(timing_metrics),
                "counter": len(counter_metrics),
                "gauge": len(gauge_metrics),
                "throughput": len(throughput_metrics),
            },
        }

        # Timing statistics
        if timing_metrics:
            durations = [m.value for m in timing_metrics]
            summary["timing_stats"] = {
                "count": len(durations),
                "min_ms": min(durations),
                "max_ms": max(durations),
                "avg_ms": sum(durations) / len(durations),
                "total_ms": sum(durations),
            }

        # Throughput statistics
        if throughput_metrics:
            throughputs = [m.value for m in throughput_metrics]
            summary["throughput_stats"] = {
                "count": len(throughputs),
                "min_items_per_sec": min(throughputs),
                "max_items_per_sec": max(throughputs),
                "avg_items_per_sec": sum(throughputs) / len(throughputs),
            }

        return summary

    def get_resource_summary(self) -> Dict[str, Any]:
        """
        Get resource usage summary.

        Returns:
            Resource usage summary
        """
        if not self._resource_history:
            return {}

        recent_usage = list(self._resource_history)

        # Calculate averages
        avg_cpu = sum(r.cpu_percent for r in recent_usage) / len(recent_usage)
        avg_memory = sum(r.memory_percent for r in recent_usage) / len(recent_usage)
        avg_memory_mb = sum(r.memory_mb for r in recent_usage) / len(recent_usage)

        # Find peaks
        max_cpu = max(r.cpu_percent for r in recent_usage)
        max_memory = max(r.memory_percent for r in recent_usage)

        return {
            "monitoring_enabled": self._monitoring_enabled,
            "samples_collected": len(recent_usage),
            "average_cpu_percent": avg_cpu,
            "average_memory_percent": avg_memory,
            "average_memory_mb": avg_memory_mb,
            "peak_cpu_percent": max_cpu,
            "peak_memory_percent": max_memory,
            "baseline_cpu": (
                self._baseline_resources.cpu_percent
                if self._baseline_resources
                else None
            ),
            "baseline_memory": (
                self._baseline_resources.memory_percent
                if self._baseline_resources
                else None
            ),
        }

    def get_alerts(
        self,
        severity: Optional[str] = None,
        component: Optional[str] = None,
        limit: Optional[int] = None,
    ) -> List[PerformanceAlert]:
        """
        Get performance alerts.

        Args:
            severity: Filter by severity
            component: Filter by component
            limit: Maximum number of alerts to return

        Returns:
            List of performance alerts
        """
        alerts = self._alerts

        # Apply filters
        if severity:
            alerts = [a for a in alerts if a.severity == severity]
        if component:
            alerts = [a for a in alerts if a.component == component]

        # Sort by timestamp (most recent first)
        alerts.sort(key=lambda a: a.timestamp, reverse=True)

        # Apply limit
        if limit:
            alerts = alerts[:limit]

        return alerts

    def clear_alerts(self) -> None:
        """Clear all performance alerts."""
        cleared_count = len(self._alerts)
        self._alerts.clear()

        self.logger.log_info(
            LogCategory.PERFORMANCE,
            "PerformanceMonitor",
            "clear_alerts",
            f"Cleared {cleared_count} performance alerts",
            {"cleared_count": cleared_count},
        )

    def get_performance_recommendations(self) -> List[str]:
        """
        Get performance optimization recommendations.

        Returns:
            List of performance recommendations
        """
        recommendations = []

        # Analyze timing metrics
        timing_summary = self.get_metric_summary()
        if "timing_stats" in timing_summary:
            stats = timing_summary["timing_stats"]
            if stats["avg_ms"] > 5000:  # Average > 5 seconds
                recommendations.append(
                    "Consider optimizing slow operations (average duration > 5s)"
                )
            if stats["max_ms"] > 30000:  # Max > 30 seconds
                recommendations.append(
                    "Investigate extremely slow operations (max duration > 30s)"
                )

        # Analyze resource usage
        resource_summary = self.get_resource_summary()
        if resource_summary:
            if resource_summary.get("peak_cpu_percent", 0) > 80:
                recommendations.append(
                    "High CPU usage detected - consider optimizing CPU-intensive operations"
                )
            if resource_summary.get("peak_memory_percent", 0) > 85:
                recommendations.append(
                    "High memory usage detected - check for memory leaks or optimize memory usage"
                )

        # Analyze alerts
        critical_alerts = self.get_alerts(severity="critical", limit=10)
        if critical_alerts:
            recommendations.append(
                f"Address {len(critical_alerts)} critical performance alerts"
            )

        # Check for frequent operations
        for metric_name, metric_deque in self._metrics.items():
            if len(metric_deque) > 500:  # High frequency
                recommendations.append(
                    f"High frequency metric '{metric_name}' - consider batching or optimization"
                )

        return recommendations
