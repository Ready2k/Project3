"""
Performance metrics collection for the AAA system.

This module provides comprehensive performance monitoring and metrics
collection for tracking application performance and identifying bottlenecks.
"""

import time
import psutil
import threading
from typing import Any, Dict, List, Optional, Callable
from dataclasses import dataclass, field
from enum import Enum
from contextlib import contextmanager
from functools import wraps
import statistics

from app.utils.logger import app_logger


class MetricType(Enum):
    """Types of performance metrics."""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class MetricValue:
    """A single metric value with metadata."""
    value: float
    timestamp: float
    labels: Dict[str, str] = field(default_factory=dict)


@dataclass
class MetricSummary:
    """Summary statistics for a metric."""
    name: str
    metric_type: MetricType
    count: int
    total: float
    average: float
    min_value: float
    max_value: float
    percentile_95: float
    percentile_99: float
    labels: Dict[str, str] = field(default_factory=dict)


class PerformanceMetrics:
    """
    Performance metrics collector and analyzer.
    
    Collects various performance metrics including timing, memory usage,
    and custom application metrics.
    """
    
    def __init__(self, max_history: int = 10000):
        """
        Initialize the performance metrics collector.
        
        Args:
            max_history: Maximum number of metric values to keep in memory
        """
        self.max_history = max_history
        self._metrics: Dict[str, List[MetricValue]] = {}
        self._lock = threading.RLock()
        self._start_time = time.time()
        
        # System metrics
        self._process = psutil.Process()
        self._system_metrics_enabled = True
    
    def record_counter(self, name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a counter metric.
        
        Args:
            name: Metric name
            value: Counter increment value
            labels: Optional labels for the metric
        """
        self._record_metric(name, value, labels or {})
    
    def record_gauge(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a gauge metric.
        
        Args:
            name: Metric name
            value: Gauge value
            labels: Optional labels for the metric
        """
        self._record_metric(name, value, labels or {})
    
    def record_histogram(self, name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a histogram metric.
        
        Args:
            name: Metric name
            value: Histogram value
            labels: Optional labels for the metric
        """
        self._record_metric(name, value, labels or {})
    
    def record_timer(self, name: str, duration: float, labels: Optional[Dict[str, str]] = None) -> None:
        """
        Record a timer metric.
        
        Args:
            name: Metric name
            duration: Duration in seconds
            labels: Optional labels for the metric
        """
        self._record_metric(f"{name}_duration_seconds", duration, labels or {})
    
    def _record_metric(self, name: str, value: float, labels: Dict[str, str]) -> None:
        """Internal method to record a metric."""
        with self._lock:
            if name not in self._metrics:
                self._metrics[name] = []
            
            metric_value = MetricValue(
                value=value,
                timestamp=time.time(),
                labels=labels
            )
            
            self._metrics[name].append(metric_value)
            
            # Trim history if needed
            if len(self._metrics[name]) > self.max_history:
                self._metrics[name] = self._metrics[name][-self.max_history:]
    
    @contextmanager
    def timer(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Context manager for timing operations.
        
        Args:
            name: Timer name
            labels: Optional labels for the timer
        """
        start_time = time.time()
        try:
            yield
        finally:
            duration = time.time() - start_time
            self.record_timer(name, duration, labels)
    
    def timed(self, name: str, labels: Optional[Dict[str, str]] = None):
        """
        Decorator for timing function execution.
        
        Args:
            name: Timer name
            labels: Optional labels for the timer
            
        Returns:
            Decorator function
        """
        def decorator(func: Callable) -> Callable:
            @wraps(func)
            def wrapper(*args, **kwargs):
                with self.timer(name, labels):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_metric_summary(self, name: str, time_window: Optional[float] = None) -> Optional[MetricSummary]:
        """
        Get summary statistics for a metric.
        
        Args:
            name: Metric name
            time_window: Time window in seconds (None for all data)
            
        Returns:
            MetricSummary or None if metric not found
        """
        with self._lock:
            if name not in self._metrics:
                return None
            
            values = self._metrics[name]
            
            # Filter by time window if specified
            if time_window is not None:
                cutoff_time = time.time() - time_window
                values = [v for v in values if v.timestamp >= cutoff_time]
            
            if not values:
                return None
            
            # Calculate statistics
            numeric_values = [v.value for v in values]
            
            return MetricSummary(
                name=name,
                metric_type=MetricType.HISTOGRAM,  # Default type
                count=len(numeric_values),
                total=sum(numeric_values),
                average=statistics.mean(numeric_values),
                min_value=min(numeric_values),
                max_value=max(numeric_values),
                percentile_95=statistics.quantiles(numeric_values, n=20)[18] if len(numeric_values) > 1 else numeric_values[0],
                percentile_99=statistics.quantiles(numeric_values, n=100)[98] if len(numeric_values) > 1 else numeric_values[0]
            )
    
    def get_all_metrics(self, time_window: Optional[float] = None) -> Dict[str, MetricSummary]:
        """
        Get summary statistics for all metrics.
        
        Args:
            time_window: Time window in seconds (None for all data)
            
        Returns:
            Dictionary mapping metric names to summaries
        """
        with self._lock:
            summaries = {}
            for name in self._metrics.keys():
                summary = self.get_metric_summary(name, time_window)
                if summary:
                    summaries[name] = summary
            return summaries
    
    def collect_system_metrics(self) -> Dict[str, float]:
        """
        Collect current system metrics.
        
        Returns:
            Dictionary with system metrics
        """
        if not self._system_metrics_enabled:
            return {}
        
        try:
            # Process metrics
            memory_info = self._process.memory_info()
            cpu_percent = self._process.cpu_percent()
            
            # System metrics
            system_memory = psutil.virtual_memory()
            system_cpu = psutil.cpu_percent(interval=0.1)
            
            metrics = {
                "process_memory_rss_bytes": memory_info.rss,
                "process_memory_vms_bytes": memory_info.vms,
                "process_cpu_percent": cpu_percent,
                "system_memory_percent": system_memory.percent,
                "system_memory_available_bytes": system_memory.available,
                "system_cpu_percent": system_cpu,
                "uptime_seconds": time.time() - self._start_time
            }
            
            # Record as gauge metrics
            for name, value in metrics.items():
                self.record_gauge(f"system_{name}", value)
            
            return metrics
            
        except Exception as e:
            app_logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def get_performance_report(self, time_window: Optional[float] = 3600) -> Dict[str, Any]:
        """
        Generate a comprehensive performance report.
        
        Args:
            time_window: Time window in seconds (default: 1 hour)
            
        Returns:
            Performance report dictionary
        """
        # Collect current system metrics
        system_metrics = self.collect_system_metrics()
        
        # Get metric summaries
        metric_summaries = self.get_all_metrics(time_window)
        
        # Identify performance issues
        issues = []
        
        # Check for slow operations
        for name, summary in metric_summaries.items():
            if "duration_seconds" in name and summary.average > 1.0:
                issues.append(f"Slow operation: {name} averages {summary.average:.2f}s")
            
            if "duration_seconds" in name and summary.percentile_99 > 5.0:
                issues.append(f"High latency: {name} 99th percentile is {summary.percentile_99:.2f}s")
        
        # Check system resources
        if system_metrics.get("process_memory_rss_bytes", 0) > 1024 * 1024 * 1024:  # 1GB
            issues.append(f"High memory usage: {system_metrics['process_memory_rss_bytes'] / 1024 / 1024:.0f}MB")
        
        if system_metrics.get("process_cpu_percent", 0) > 80:
            issues.append(f"High CPU usage: {system_metrics['process_cpu_percent']:.1f}%")
        
        # Performance recommendations
        recommendations = []
        
        if len([s for s in metric_summaries.values() if "duration_seconds" in s.name and s.average > 0.5]) > 3:
            recommendations.append("Consider implementing caching for slow operations")
        
        if system_metrics.get("process_memory_rss_bytes", 0) > 512 * 1024 * 1024:  # 512MB
            recommendations.append("Consider optimizing memory usage or implementing memory cleanup")
        
        return {
            "timestamp": time.time(),
            "time_window_seconds": time_window,
            "system_metrics": system_metrics,
            "metric_summaries": {name: {
                "count": s.count,
                "average": round(s.average, 4),
                "min": round(s.min_value, 4),
                "max": round(s.max_value, 4),
                "p95": round(s.percentile_95, 4),
                "p99": round(s.percentile_99, 4)
            } for name, s in metric_summaries.items()},
            "performance_issues": issues,
            "recommendations": recommendations,
            "total_metrics": len(metric_summaries),
            "uptime_seconds": system_metrics.get("uptime_seconds", 0)
        }
    
    def clear_metrics(self, older_than: Optional[float] = None) -> int:
        """
        Clear metrics data.
        
        Args:
            older_than: Clear metrics older than this many seconds (None for all)
            
        Returns:
            Number of metric values cleared
        """
        cleared_count = 0
        
        with self._lock:
            if older_than is None:
                # Clear all metrics
                for name in self._metrics:
                    cleared_count += len(self._metrics[name])
                self._metrics.clear()
            else:
                # Clear old metrics
                cutoff_time = time.time() - older_than
                for name in list(self._metrics.keys()):
                    original_count = len(self._metrics[name])
                    self._metrics[name] = [
                        v for v in self._metrics[name]
                        if v.timestamp >= cutoff_time
                    ]
                    cleared_count += original_count - len(self._metrics[name])
                    
                    # Remove empty metric lists
                    if not self._metrics[name]:
                        del self._metrics[name]
        
        if cleared_count > 0:
            app_logger.info(f"Cleared {cleared_count} old metric values")
        
        return cleared_count


# Global performance metrics instance
_global_metrics: Optional[PerformanceMetrics] = None
_metrics_lock = threading.Lock()


def get_performance_metrics() -> PerformanceMetrics:
    """
    Get the global performance metrics instance.
    
    Returns:
        The global performance metrics collector
    """
    global _global_metrics
    
    if _global_metrics is None:
        with _metrics_lock:
            if _global_metrics is None:
                _global_metrics = PerformanceMetrics()
    
    return _global_metrics


def record_counter(name: str, value: float = 1.0, labels: Optional[Dict[str, str]] = None) -> None:
    """Record a counter metric using the global collector."""
    metrics = get_performance_metrics()
    metrics.record_counter(name, value, labels)


def record_gauge(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Record a gauge metric using the global collector."""
    metrics = get_performance_metrics()
    metrics.record_gauge(name, value, labels)


def record_histogram(name: str, value: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Record a histogram metric using the global collector."""
    metrics = get_performance_metrics()
    metrics.record_histogram(name, value, labels)


def record_timer(name: str, duration: float, labels: Optional[Dict[str, str]] = None) -> None:
    """Record a timer metric using the global collector."""
    metrics = get_performance_metrics()
    metrics.record_timer(name, duration, labels)


@contextmanager
def timer(name: str, labels: Optional[Dict[str, str]] = None):
    """Context manager for timing operations using the global collector."""
    metrics = get_performance_metrics()
    with metrics.timer(name, labels):
        yield


def timed(name: str, labels: Optional[Dict[str, str]] = None):
    """Decorator for timing function execution using the global collector."""
    metrics = get_performance_metrics()
    return metrics.timed(name, labels)


def get_performance_report(time_window: Optional[float] = 3600) -> Dict[str, Any]:
    """Generate a performance report using the global collector."""
    metrics = get_performance_metrics()
    return metrics.get_performance_report(time_window)


def collect_system_metrics() -> Dict[str, float]:
    """Collect system metrics using the global collector."""
    metrics = get_performance_metrics()
    return metrics.collect_system_metrics()