"""
Performance Optimizer for Monitoring System

Provides performance optimization utilities to reduce CPU usage and improve
efficiency of the monitoring system components.
"""

import asyncio
import time
import psutil
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Callable
from dataclasses import dataclass
import logging

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


@dataclass
class PerformanceMetrics:
    """Performance metrics for monitoring optimization."""
    cpu_usage: float
    memory_usage: float
    task_count: int
    avg_task_duration: float
    timestamp: datetime
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = {
            'cpu_usage': self.cpu_usage,
            'memory_usage': self.memory_usage,
            'task_count': self.task_count,
            'avg_task_duration': self.avg_task_duration,
            'timestamp': self.timestamp.isoformat()
        }
        return data


class MonitoringPerformanceOptimizer(ConfigurableService):
    """
    Performance optimizer for monitoring system.
    
    Monitors system resource usage and automatically adjusts monitoring
    intervals and task scheduling to optimize performance.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'MonitoringPerformanceOptimizer')
        
        # Initialize logger
        try:
            self.logger = require_service('logger', context='MonitoringPerformanceOptimizer')
        except:
            import logging
            self.logger = logging.getLogger('MonitoringPerformanceOptimizer')
        
        # Configuration
        self.config = {
            'cpu_threshold_warning': 70.0,
            'cpu_threshold_critical': 85.0,
            'memory_threshold_warning': 80.0,
            'memory_threshold_critical': 90.0,
            'optimization_check_interval': 60,  # seconds
            'adaptive_intervals': True,
            'max_interval_multiplier': 4.0,
            'min_interval_seconds': 10,
            **config
        } if config else {
            'cpu_threshold_warning': 70.0,
            'cpu_threshold_critical': 85.0,
            'memory_threshold_warning': 80.0,
            'memory_threshold_critical': 90.0,
            'optimization_check_interval': 60,
            'adaptive_intervals': True,
            'max_interval_multiplier': 4.0,
            'min_interval_seconds': 10
        }
        
        # State
        self.is_optimizing = False
        self.optimization_task = None
        self.performance_history: List[PerformanceMetrics] = []
        self.current_multipliers: Dict[str, float] = {}
        self.task_registry: Dict[str, Dict[str, Any]] = {}
        
        # Performance baselines
        self.baseline_cpu = 0.0
        self.baseline_memory = 0.0
        self.baseline_established = False
    
    async def _do_initialize(self) -> None:
        """Initialize the performance optimizer."""
        await self.start_optimization()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the performance optimizer."""
        await self.stop_optimization()
    
    async def start_optimization(self) -> None:
        """Start performance optimization."""
        try:
            self.logger.info("Starting monitoring performance optimization")
            
            # Establish baseline
            await self._establish_baseline()
            
            # Start optimization task
            self.is_optimizing = True
            self.optimization_task = asyncio.create_task(self._optimization_loop())
            
            self.logger.info("Performance optimization started")
            
        except Exception as e:
            self.logger.error(f"Failed to start performance optimization: {e}")
            raise
    
    async def stop_optimization(self) -> None:
        """Stop performance optimization."""
        try:
            self.logger.info("Stopping performance optimization")
            
            self.is_optimizing = False
            
            if self.optimization_task:
                self.optimization_task.cancel()
                try:
                    await self.optimization_task
                except asyncio.CancelledError:
                    pass
            
            self.logger.info("Performance optimization stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping performance optimization: {e}")
    
    async def _establish_baseline(self) -> None:
        """Establish performance baseline."""
        try:
            # Take multiple samples to establish baseline
            cpu_samples = []
            memory_samples = []
            
            for _ in range(5):
                cpu_samples.append(psutil.cpu_percent(interval=1))
                memory_samples.append(psutil.virtual_memory().percent)
                await asyncio.sleep(1)
            
            self.baseline_cpu = sum(cpu_samples) / len(cpu_samples)
            self.baseline_memory = sum(memory_samples) / len(memory_samples)
            self.baseline_established = True
            
            self.logger.info(f"Performance baseline established: CPU={self.baseline_cpu:.1f}%, Memory={self.baseline_memory:.1f}%")
            
        except Exception as e:
            self.logger.error(f"Error establishing baseline: {e}")
            # Use default baselines
            self.baseline_cpu = 20.0
            self.baseline_memory = 30.0
            self.baseline_established = True
    
    async def _optimization_loop(self) -> None:
        """Main optimization loop."""
        while self.is_optimizing:
            try:
                # Collect performance metrics
                metrics = await self._collect_performance_metrics()
                self.performance_history.append(metrics)
                
                # Limit history size
                if len(self.performance_history) > 100:
                    self.performance_history = self.performance_history[-100:]
                
                # Check if optimization is needed
                if await self._should_optimize(metrics):
                    await self._apply_optimizations(metrics)
                
                # Check if we can relax optimizations
                elif await self._can_relax_optimizations(metrics):
                    await self._relax_optimizations(metrics)
                
                await asyncio.sleep(self.config['optimization_check_interval'])
                
            except Exception as e:
                self.logger.error(f"Error in optimization loop: {e}")
                await asyncio.sleep(60)
    
    async def _collect_performance_metrics(self) -> PerformanceMetrics:
        """Collect current performance metrics."""
        try:
            # Get system metrics
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            
            # Get asyncio task count
            try:
                all_tasks = asyncio.all_tasks()
                task_count = len(all_tasks)
                
                # Estimate average task duration (simplified)
                avg_task_duration = 0.1  # Default estimate
                
            except Exception:
                task_count = 0
                avg_task_duration = 0.0
            
            metrics = PerformanceMetrics(
                cpu_usage=cpu_usage,
                memory_usage=memory_usage,
                task_count=task_count,
                avg_task_duration=avg_task_duration,
                timestamp=datetime.now()
            )
            
            return metrics
            
        except Exception as e:
            self.logger.error(f"Error collecting performance metrics: {e}")
            # Return default metrics
            return PerformanceMetrics(
                cpu_usage=0.0,
                memory_usage=0.0,
                task_count=0,
                avg_task_duration=0.0,
                timestamp=datetime.now()
            )
    
    async def _should_optimize(self, metrics: PerformanceMetrics) -> bool:
        """Check if optimization is needed."""
        try:
            # Check CPU usage
            if metrics.cpu_usage > self.config['cpu_threshold_warning']:
                self.logger.warning(f"High CPU usage detected: {metrics.cpu_usage:.1f}%")
                return True
            
            # Check memory usage
            if metrics.memory_usage > self.config['memory_threshold_warning']:
                self.logger.warning(f"High memory usage detected: {metrics.memory_usage:.1f}%")
                return True
            
            # Check if usage is significantly above baseline
            if self.baseline_established:
                cpu_increase = metrics.cpu_usage - self.baseline_cpu
                memory_increase = metrics.memory_usage - self.baseline_memory
                
                if cpu_increase > 20.0 or memory_increase > 20.0:
                    self.logger.info(f"Resource usage above baseline: CPU +{cpu_increase:.1f}%, Memory +{memory_increase:.1f}%")
                    return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking optimization need: {e}")
            return False
    
    async def _can_relax_optimizations(self, metrics: PerformanceMetrics) -> bool:
        """Check if optimizations can be relaxed."""
        try:
            # Only relax if we have active optimizations
            if not self.current_multipliers:
                return False
            
            # Check if resource usage is low enough
            if (metrics.cpu_usage < self.config['cpu_threshold_warning'] - 10.0 and
                metrics.memory_usage < self.config['memory_threshold_warning'] - 10.0):
                
                # Check recent history for stability
                if len(self.performance_history) >= 5:
                    recent_metrics = self.performance_history[-5:]
                    avg_cpu = sum(m.cpu_usage for m in recent_metrics) / len(recent_metrics)
                    avg_memory = sum(m.memory_usage for m in recent_metrics) / len(recent_metrics)
                    
                    if (avg_cpu < self.config['cpu_threshold_warning'] - 5.0 and
                        avg_memory < self.config['memory_threshold_warning'] - 5.0):
                        return True
            
            return False
            
        except Exception as e:
            self.logger.error(f"Error checking relaxation possibility: {e}")
            return False
    
    async def _apply_optimizations(self, metrics: PerformanceMetrics) -> None:
        """Apply performance optimizations."""
        try:
            optimization_level = self._calculate_optimization_level(metrics)
            
            self.logger.info(f"Applying performance optimizations (level: {optimization_level:.1f})")
            
            # Calculate interval multipliers based on optimization level
            base_multiplier = 1.0 + (optimization_level * 2.0)  # 1.0 to 3.0
            
            # Apply different multipliers for different types of tasks
            optimizations = {
                'real_time_monitoring': min(base_multiplier * 0.5, 2.0),  # Less aggressive for real-time
                'quality_checks': min(base_multiplier, self.config['max_interval_multiplier']),
                'analytics': min(base_multiplier * 1.5, self.config['max_interval_multiplier']),
                'cleanup_tasks': min(base_multiplier * 0.8, self.config['max_interval_multiplier']),
                'health_checks': min(base_multiplier * 1.2, self.config['max_interval_multiplier'])
            }
            
            # Store current multipliers
            self.current_multipliers.update(optimizations)
            
            # Log optimization details
            for task_type, multiplier in optimizations.items():
                self.logger.debug(f"Applied {multiplier:.1f}x interval multiplier to {task_type}")
            
            # Notify monitoring components about optimization
            await self._notify_components_optimization(optimizations)
            
        except Exception as e:
            self.logger.error(f"Error applying optimizations: {e}")
    
    async def _relax_optimizations(self, metrics: PerformanceMetrics) -> None:
        """Relax performance optimizations."""
        try:
            self.logger.info("Relaxing performance optimizations")
            
            # Gradually reduce multipliers
            relaxed_multipliers = {}
            for task_type, current_multiplier in self.current_multipliers.items():
                # Reduce multiplier by 20%
                new_multiplier = max(current_multiplier * 0.8, 1.0)
                relaxed_multipliers[task_type] = new_multiplier
            
            # Update current multipliers
            self.current_multipliers = {k: v for k, v in relaxed_multipliers.items() if v > 1.0}
            
            # Notify components
            await self._notify_components_optimization(relaxed_multipliers)
            
            if not self.current_multipliers:
                self.logger.info("All optimizations relaxed - normal operation resumed")
            
        except Exception as e:
            self.logger.error(f"Error relaxing optimizations: {e}")
    
    def _calculate_optimization_level(self, metrics: PerformanceMetrics) -> float:
        """Calculate optimization level based on metrics."""
        try:
            # Calculate CPU pressure
            cpu_pressure = 0.0
            if metrics.cpu_usage > self.config['cpu_threshold_warning']:
                cpu_pressure = (metrics.cpu_usage - self.config['cpu_threshold_warning']) / 30.0
            
            # Calculate memory pressure
            memory_pressure = 0.0
            if metrics.memory_usage > self.config['memory_threshold_warning']:
                memory_pressure = (metrics.memory_usage - self.config['memory_threshold_warning']) / 20.0
            
            # Calculate task pressure
            task_pressure = 0.0
            if metrics.task_count > 50:  # Arbitrary threshold
                task_pressure = (metrics.task_count - 50) / 100.0
            
            # Combined optimization level (0.0 to 1.0)
            optimization_level = min(max(cpu_pressure, memory_pressure, task_pressure), 1.0)
            
            return optimization_level
            
        except Exception as e:
            self.logger.error(f"Error calculating optimization level: {e}")
            return 0.5  # Default moderate optimization
    
    async def _notify_components_optimization(self, multipliers: Dict[str, float]) -> None:
        """Notify monitoring components about optimization changes."""
        try:
            # This would integrate with actual monitoring components
            # For now, just log the optimization
            self.logger.debug(f"Optimization multipliers: {multipliers}")
            
            # In a real implementation, this would:
            # 1. Update monitoring component configurations
            # 2. Adjust background task intervals
            # 3. Modify data collection frequencies
            # 4. Adjust alert checking intervals
            
        except Exception as e:
            self.logger.error(f"Error notifying components: {e}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        try:
            latest_metrics = self.performance_history[-1] if self.performance_history else None
            
            status = {
                'is_optimizing': self.is_optimizing,
                'baseline_established': self.baseline_established,
                'baseline_cpu': self.baseline_cpu,
                'baseline_memory': self.baseline_memory,
                'current_multipliers': self.current_multipliers.copy(),
                'optimization_active': len(self.current_multipliers) > 0,
                'latest_metrics': latest_metrics.to_dict() if latest_metrics else None,
                'performance_history_size': len(self.performance_history)
            }
            
            return status
            
        except Exception as e:
            self.logger.error(f"Error getting optimization status: {e}")
            return {'error': str(e)}
    
    def get_performance_recommendations(self) -> List[str]:
        """Get performance optimization recommendations."""
        try:
            recommendations = []
            
            if not self.performance_history:
                return ["No performance data available"]
            
            latest_metrics = self.performance_history[-1]
            
            # CPU recommendations
            if latest_metrics.cpu_usage > self.config['cpu_threshold_critical']:
                recommendations.append("Critical: CPU usage is very high - consider reducing monitoring frequency")
                recommendations.append("Consider disabling non-essential monitoring components")
            elif latest_metrics.cpu_usage > self.config['cpu_threshold_warning']:
                recommendations.append("Warning: CPU usage is elevated - monitoring intervals have been increased")
            
            # Memory recommendations
            if latest_metrics.memory_usage > self.config['memory_threshold_critical']:
                recommendations.append("Critical: Memory usage is very high - consider reducing data retention")
                recommendations.append("Enable aggressive cleanup of old monitoring data")
            elif latest_metrics.memory_usage > self.config['memory_threshold_warning']:
                recommendations.append("Warning: Memory usage is elevated - consider reducing cache sizes")
            
            # Task recommendations
            if latest_metrics.task_count > 100:
                recommendations.append("High number of async tasks - consider consolidating background operations")
            
            # General recommendations
            if len(self.current_multipliers) > 0:
                recommendations.append("Performance optimizations are active - some monitoring features may be reduced")
            
            if not recommendations:
                recommendations.append("System performance is within normal parameters")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating recommendations: {e}")
            return [f"Error generating recommendations: {e}"]


# Utility functions for integration with existing monitoring components

def get_optimized_interval(base_interval: float, task_type: str = 'default') -> float:
    """
    Get optimized interval for a monitoring task.
    
    Args:
        base_interval: Base interval in seconds
        task_type: Type of task for optimization
        
    Returns:
        Optimized interval in seconds
    """
    try:
        # Try to get optimizer instance
        optimizer = optional_service('monitoring_performance_optimizer', context='optimization')
        
        if optimizer and hasattr(optimizer, 'current_multipliers'):
            multiplier = optimizer.current_multipliers.get(task_type, 1.0)
            optimized_interval = base_interval * multiplier
            
            # Ensure minimum interval
            min_interval = getattr(optimizer.config, 'min_interval_seconds', 10)
            return max(optimized_interval, min_interval)
        
        return base_interval
        
    except Exception:
        return base_interval


def should_skip_task(task_type: str, skip_probability: float = 0.0) -> bool:
    """
    Check if a task should be skipped for performance optimization.
    
    Args:
        task_type: Type of task
        skip_probability: Base probability of skipping (0.0 to 1.0)
        
    Returns:
        True if task should be skipped
    """
    try:
        # Try to get optimizer instance
        optimizer = optional_service('monitoring_performance_optimizer', context='optimization')
        
        if optimizer and hasattr(optimizer, 'current_multipliers'):
            multiplier = optimizer.current_multipliers.get(task_type, 1.0)
            
            # Higher multiplier = higher chance of skipping
            if multiplier > 2.0:
                skip_probability = min(skip_probability + 0.3, 0.8)
            elif multiplier > 1.5:
                skip_probability = min(skip_probability + 0.1, 0.5)
        
        import random
        return random.random() < skip_probability
        
    except Exception:
        return False