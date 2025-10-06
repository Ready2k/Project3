"""
Monitoring Optimization Manager

Manages performance optimizations for the monitoring system to reduce
CPU and memory usage while maintaining essential functionality.
"""

import asyncio
import yaml
import psutil
from datetime import datetime
from typing import Dict, List, Any
from pathlib import Path
import logging

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service
from app.monitoring.performance_optimizer import MonitoringPerformanceOptimizer


class MonitoringOptimizationManager(ConfigurableService):
    """
    Manages performance optimizations for the entire monitoring system.
    
    Coordinates optimization across all monitoring components and provides
    centralized configuration management for performance tuning.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'MonitoringOptimizationManager')
        
        # Initialize logger
        try:
            self.logger = require_service('logger', context='MonitoringOptimizationManager')
        except Exception:
            import logging
            self.logger = logging.getLogger('MonitoringOptimizationManager')
        
        # Load optimization configuration
        self.optimization_config = self._load_optimization_config()
        
        # Performance optimizer
        self.performance_optimizer = None
        
        # Component references
        self.monitoring_components: Dict[str, Any] = {}
        
        # Optimization state
        self.optimization_active = False
        self.emergency_mode_active = False
        self.current_performance_level = 'normal'  # normal, optimized, emergency
        
        # Performance tracking
        self.performance_history: List[Dict[str, Any]] = []
        self.optimization_history: List[Dict[str, Any]] = []
    
    async def _do_initialize(self) -> None:
        """Initialize the optimization manager."""
        await self.initialize_optimization()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the optimization manager."""
        await self.shutdown_optimization()
    
    def _load_optimization_config(self) -> Dict[str, Any]:
        """Load optimization configuration from file."""
        try:
            config_path = Path("config/monitoring_optimization.yaml")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config = yaml.safe_load(f)
                self.logger.info("Loaded monitoring optimization configuration")
                return config
            else:
                self.logger.warning("Optimization config file not found, using defaults")
                return self._get_default_optimization_config()
                
        except Exception as e:
            self.logger.error(f"Error loading optimization config: {e}")
            return self._get_default_optimization_config()
    
    def _get_default_optimization_config(self) -> Dict[str, Any]:
        """Get default optimization configuration."""
        return {
            'performance_optimizer': {
                'enabled': True,
                'cpu_threshold_warning': 70.0,
                'cpu_threshold_critical': 85.0,
                'memory_threshold_warning': 80.0,
                'memory_threshold_critical': 90.0
            },
            'monitoring_components': {
                'tech_stack_monitor': {
                    'quality_check_interval': 600,
                    'real_time_update_interval': 60
                },
                'quality_assurance': {
                    'accuracy_check_interval': 600,
                    'report_generation_interval': 7200
                },
                'performance_analytics': {
                    'analysis_interval_minutes': 30,
                    'bottleneck_detection_interval': 300
                }
            },
            'data_retention': {
                'metrics_retention_hours': 72,
                'alert_retention_hours': 360
            }
        }
    
    async def initialize_optimization(self) -> None:
        """Initialize monitoring optimization."""
        try:
            self.logger.info("Initializing monitoring optimization manager")
            
            # Initialize performance optimizer if enabled
            if self.optimization_config.get('performance_optimizer', {}).get('enabled', True):
                optimizer_config = self.optimization_config.get('performance_optimizer', {})
                self.performance_optimizer = MonitoringPerformanceOptimizer(optimizer_config)
                await self.performance_optimizer.initialize()
            
            # Discover and register monitoring components
            await self._discover_monitoring_components()
            
            # Apply initial optimizations
            await self._apply_initial_optimizations()
            
            # Start monitoring system performance
            asyncio.create_task(self._performance_monitoring_loop())
            
            self.logger.info("Monitoring optimization manager initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize optimization manager: {e}")
            raise
    
    async def shutdown_optimization(self) -> None:
        """Shutdown monitoring optimization."""
        try:
            self.logger.info("Shutting down monitoring optimization manager")
            
            # Stop performance optimizer
            if self.performance_optimizer:
                await self.performance_optimizer.shutdown()
            
            # Reset component configurations if needed
            await self._reset_component_configurations()
            
            self.logger.info("Monitoring optimization manager shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error shutting down optimization manager: {e}")
    
    async def _discover_monitoring_components(self) -> None:
        """Discover available monitoring components."""
        try:
            # Try to get components from service registry
            component_names = [
                'tech_stack_monitor',
                'quality_assurance_system',
                'performance_analytics',
                'real_time_quality_monitor',
                'alert_system',
                'integrated_dashboard'
            ]
            
            for component_name in component_names:
                try:
                    component = optional_service(component_name, context='OptimizationManager')
                    if component:
                        self.monitoring_components[component_name] = component
                        self.logger.debug(f"Discovered monitoring component: {component_name}")
                except Exception as e:
                    self.logger.debug(f"Component {component_name} not available: {e}")
            
            self.logger.info(f"Discovered {len(self.monitoring_components)} monitoring components")
            
        except Exception as e:
            self.logger.error(f"Error discovering monitoring components: {e}")
    
    async def _apply_initial_optimizations(self) -> None:
        """Apply initial performance optimizations."""
        try:
            # Check current system performance
            cpu_usage = psutil.cpu_percent(interval=1)
            memory_usage = psutil.virtual_memory().percent
            
            self.logger.info(f"Initial system performance: CPU={cpu_usage:.1f}%, Memory={memory_usage:.1f}%")
            
            # Apply optimizations based on current performance
            if cpu_usage > 80.0 or memory_usage > 80.0:
                self.logger.warning("High resource usage detected, applying aggressive optimizations")
                await self._apply_optimization_level('emergency')
            elif cpu_usage > 60.0 or memory_usage > 60.0:
                self.logger.info("Moderate resource usage detected, applying standard optimizations")
                await self._apply_optimization_level('optimized')
            else:
                self.logger.info("Normal resource usage, applying minimal optimizations")
                await self._apply_optimization_level('normal')
                
        except Exception as e:
            self.logger.error(f"Error applying initial optimizations: {e}")
    
    async def _apply_optimization_level(self, level: str) -> None:
        """Apply optimization level to all components."""
        try:
            self.current_performance_level = level
            self.logger.info(f"Applying optimization level: {level}")
            
            # Get optimization settings for this level
            optimization_settings = self._get_optimization_settings(level)
            
            # Apply to each component
            for component_name, component in self.monitoring_components.items():
                try:
                    await self._apply_component_optimization(
                        component_name, 
                        component, 
                        optimization_settings.get(component_name, {})
                    )
                except Exception as e:
                    self.logger.error(f"Error optimizing component {component_name}: {e}")
            
            # Record optimization change
            self.optimization_history.append({
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'reason': 'manual_application',
                'settings': optimization_settings
            })
            
            self.optimization_active = (level != 'normal')
            
        except Exception as e:
            self.logger.error(f"Error applying optimization level {level}: {e}")
    
    def _get_optimization_settings(self, level: str) -> Dict[str, Dict[str, Any]]:
        """Get optimization settings for a specific level."""
        try:
            base_settings = self.optimization_config.get('monitoring_components', {})
            
            if level == 'normal':
                # Use base settings with minimal optimization
                return {
                    component: {
                        **settings,
                        'optimization_multiplier': 1.0
                    }
                    for component, settings in base_settings.items()
                }
            
            elif level == 'optimized':
                # Apply moderate optimization
                return {
                    component: {
                        **settings,
                        'optimization_multiplier': 1.5,
                        **{k: v * 1.5 if 'interval' in k else v for k, v in settings.items()}
                    }
                    for component, settings in base_settings.items()
                }
            
            elif level == 'emergency':
                # Apply aggressive optimization
                emergency_config = self.optimization_config.get('emergency_mode', {})
                multiplier = emergency_config.get('increase_all_intervals_by', 3.0)
                
                return {
                    component: {
                        **settings,
                        'optimization_multiplier': multiplier,
                        **{k: v * multiplier if 'interval' in k else v for k, v in settings.items()},
                        'disable_non_critical': True
                    }
                    for component, settings in base_settings.items()
                }
            
            else:
                self.logger.warning(f"Unknown optimization level: {level}")
                return base_settings
                
        except Exception as e:
            self.logger.error(f"Error getting optimization settings for level {level}: {e}")
            return {}
    
    async def _apply_component_optimization(self, component_name: str, component: Any, settings: Dict[str, Any]) -> None:
        """Apply optimization settings to a specific component."""
        try:
            # Apply settings based on component type
            if hasattr(component, 'update_configuration'):
                # Component has built-in configuration update method
                await component.update_configuration(settings)
                
            elif hasattr(component, 'config'):
                # Component has config attribute
                component.config.update(settings)
                
            else:
                # Try to set individual attributes
                for key, value in settings.items():
                    if hasattr(component, key):
                        setattr(component, key, value)
            
            self.logger.debug(f"Applied optimization to {component_name}: {settings}")
            
        except Exception as e:
            self.logger.error(f"Error applying optimization to {component_name}: {e}")
    
    async def _performance_monitoring_loop(self) -> None:
        """Monitor system performance and adjust optimizations."""
        while True:
            try:
                # Collect performance metrics
                cpu_usage = psutil.cpu_percent(interval=1)
                memory_usage = psutil.virtual_memory().percent
                
                # Record performance
                performance_record = {
                    'timestamp': datetime.now().isoformat(),
                    'cpu_usage': cpu_usage,
                    'memory_usage': memory_usage,
                    'optimization_level': self.current_performance_level,
                    'optimization_active': self.optimization_active
                }
                
                self.performance_history.append(performance_record)
                
                # Limit history size
                if len(self.performance_history) > 100:
                    self.performance_history = self.performance_history[-100:]
                
                # Check if optimization level needs adjustment
                await self._check_optimization_adjustment(cpu_usage, memory_usage)
                
                # Sleep before next check
                await asyncio.sleep(60)  # Check every minute
                
            except Exception as e:
                self.logger.error(f"Error in performance monitoring loop: {e}")
                await asyncio.sleep(60)
    
    async def _check_optimization_adjustment(self, cpu_usage: float, memory_usage: float) -> None:
        """Check if optimization level needs adjustment."""
        try:
            emergency_config = self.optimization_config.get('emergency_mode', {})
            cpu_emergency = emergency_config.get('cpu_threshold', 95.0)
            memory_emergency = emergency_config.get('memory_threshold', 95.0)
            
            optimizer_config = self.optimization_config.get('performance_optimizer', {})
            cpu_critical = optimizer_config.get('cpu_threshold_critical', 85.0)
            memory_critical = optimizer_config.get('memory_threshold_critical', 90.0)
            cpu_warning = optimizer_config.get('cpu_threshold_warning', 70.0)
            memory_warning = optimizer_config.get('memory_threshold_warning', 80.0)
            
            # Determine required optimization level
            required_level = 'normal'
            
            if cpu_usage >= cpu_emergency or memory_usage >= memory_emergency:
                required_level = 'emergency'
            elif cpu_usage >= cpu_critical or memory_usage >= memory_critical:
                required_level = 'optimized'
            elif cpu_usage >= cpu_warning or memory_usage >= memory_warning:
                required_level = 'optimized'
            
            # Apply optimization if level changed
            if required_level != self.current_performance_level:
                self.logger.info(f"Performance level change required: {self.current_performance_level} -> {required_level}")
                await self._apply_optimization_level(required_level)
            
        except Exception as e:
            self.logger.error(f"Error checking optimization adjustment: {e}")
    
    async def _reset_component_configurations(self) -> None:
        """Reset component configurations to defaults."""
        try:
            self.logger.info("Resetting component configurations to defaults")
            
            # Apply normal optimization level to reset everything
            await self._apply_optimization_level('normal')
            
        except Exception as e:
            self.logger.error(f"Error resetting component configurations: {e}")
    
    def get_optimization_status(self) -> Dict[str, Any]:
        """Get current optimization status."""
        try:
            latest_performance = self.performance_history[-1] if self.performance_history else {}
            
            status = {
                'optimization_active': self.optimization_active,
                'current_performance_level': self.current_performance_level,
                'emergency_mode_active': self.emergency_mode_active,
                'components_managed': list(self.monitoring_components.keys()),
                'performance_optimizer_active': bool(self.performance_optimizer),
                'latest_performance': latest_performance,
                'optimization_history_count': len(self.optimization_history),
                'performance_history_count': len(self.performance_history)
            }
            
            # Add performance optimizer status if available
            if self.performance_optimizer:
                status['performance_optimizer_status'] = self.performance_optimizer.get_optimization_status()
            
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
            
            latest_performance = self.performance_history[-1]
            cpu_usage = latest_performance.get('cpu_usage', 0)
            memory_usage = latest_performance.get('memory_usage', 0)
            
            # CPU recommendations
            if cpu_usage > 90:
                recommendations.append("CRITICAL: CPU usage is extremely high - consider emergency optimizations")
                recommendations.append("Disable non-essential monitoring components immediately")
            elif cpu_usage > 80:
                recommendations.append("HIGH: CPU usage is very high - aggressive optimizations recommended")
                recommendations.append("Increase monitoring intervals and reduce data retention")
            elif cpu_usage > 70:
                recommendations.append("MEDIUM: CPU usage is elevated - standard optimizations recommended")
            
            # Memory recommendations
            if memory_usage > 90:
                recommendations.append("CRITICAL: Memory usage is extremely high - immediate action required")
                recommendations.append("Enable aggressive data cleanup and reduce cache sizes")
            elif memory_usage > 80:
                recommendations.append("HIGH: Memory usage is very high - reduce data retention periods")
            elif memory_usage > 70:
                recommendations.append("MEDIUM: Memory usage is elevated - monitor data growth")
            
            # Optimization status recommendations
            if self.current_performance_level == 'emergency':
                recommendations.append("Emergency optimizations are active - some monitoring features are disabled")
            elif self.current_performance_level == 'optimized':
                recommendations.append("Performance optimizations are active - monitoring frequency is reduced")
            
            # Component-specific recommendations
            if len(self.monitoring_components) > 5:
                recommendations.append("Consider disabling unused monitoring components")
            
            # Performance optimizer recommendations
            if self.performance_optimizer:
                optimizer_recommendations = self.performance_optimizer.get_performance_recommendations()
                recommendations.extend(optimizer_recommendations)
            
            if not recommendations:
                recommendations.append("System performance is within acceptable parameters")
            
            return recommendations
            
        except Exception as e:
            self.logger.error(f"Error generating performance recommendations: {e}")
            return [f"Error generating recommendations: {e}"]
    
    async def force_optimization_level(self, level: str) -> bool:
        """Force a specific optimization level."""
        try:
            if level not in ['normal', 'optimized', 'emergency']:
                raise ValueError(f"Invalid optimization level: {level}")
            
            self.logger.info(f"Forcing optimization level to: {level}")
            await self._apply_optimization_level(level)
            
            # Record forced optimization
            self.optimization_history.append({
                'timestamp': datetime.now().isoformat(),
                'level': level,
                'reason': 'forced_by_user',
                'forced': True
            })
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error forcing optimization level: {e}")
            return False
    
    async def reset_optimizations(self) -> bool:
        """Reset all optimizations to normal level."""
        try:
            self.logger.info("Resetting all optimizations to normal level")
            await self._apply_optimization_level('normal')
            return True
            
        except Exception as e:
            self.logger.error(f"Error resetting optimizations: {e}")
            return False


# Utility function for easy integration
async def optimize_monitoring_system(level: str = 'auto') -> bool:
    """
    Optimize the monitoring system performance.
    
    Args:
        level: Optimization level ('auto', 'normal', 'optimized', 'emergency')
        
    Returns:
        True if optimization was successful
    """
    try:
        # Get or create optimization manager
        manager = optional_service('monitoring_optimization_manager', context='optimization')
        
        if not manager:
            # Create new manager
            manager = MonitoringOptimizationManager()
            await manager.initialize()
        
        if level == 'auto':
            # Let the manager determine the appropriate level
            return True
        else:
            # Force specific level
            return await manager.force_optimization_level(level)
            
    except Exception as e:
        logging.error(f"Error optimizing monitoring system: {e}")
        return False