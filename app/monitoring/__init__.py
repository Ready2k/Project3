"""
Tech Stack Generation Monitoring Module

Provides comprehensive monitoring, quality assurance, and alerting
capabilities for technology stack generation processes.

This module includes:
- Real-time monitoring of tech stack generation accuracy and performance
- Automated quality assurance checks and reporting
- Intelligent alerting for system issues and degradation
- Performance optimization recommendations
- Interactive quality dashboard
- Data export and analysis capabilities
"""

from .tech_stack_monitor import (
    TechStackMonitor,
    TechStackMetric,
    QualityAlert,
    PerformanceRecommendation,
    MetricType,
    AlertLevel
)

from .quality_assurance import (
    QualityAssuranceSystem,
    QACheckResult,
    QAReport,
    QACheckType,
    QAStatus
)

from .integration_service import MonitoringIntegrationService

# Dashboard imports with fallback
try:
    from .quality_dashboard import QualityDashboard, render_quality_dashboard
    DASHBOARD_AVAILABLE = True
except ImportError:
    # Fallback to simple dashboard if Plotly is not available
    from .simple_dashboard import SimpleMonitoringDashboard as QualityDashboard
    from .simple_dashboard import render_simple_monitoring_dashboard as render_quality_dashboard
    DASHBOARD_AVAILABLE = False

# Integrated dashboard and alert system
from .integrated_dashboard import IntegratedMonitoringDashboard, render_integrated_monitoring_dashboard
from .alert_system import AlertSystem, AlertRule, Alert, AlertSeverity, AlertStatus, NotificationChannel

# Performance optimization
from .performance_optimizer import MonitoringPerformanceOptimizer, get_optimized_interval, should_skip_task
from .optimization_manager import MonitoringOptimizationManager, optimize_monitoring_system

__all__ = [
    # Core monitoring
    'TechStackMonitor',
    'TechStackMetric',
    'QualityAlert',
    'PerformanceRecommendation',
    'MetricType',
    'AlertLevel',
    
    # Quality assurance
    'QualityAssuranceSystem',
    'QACheckResult',
    'QAReport',
    'QACheckType',
    'QAStatus',
    
    # Integration
    'MonitoringIntegrationService',
    
    # Dashboard
    'QualityDashboard',
    'render_quality_dashboard',
    
    # Integrated dashboard and alerting
    'IntegratedMonitoringDashboard',
    'render_integrated_monitoring_dashboard',
    'AlertSystem',
    'AlertRule',
    'Alert',
    'AlertSeverity',
    'AlertStatus',
    'NotificationChannel',
    
    # Performance optimization
    'MonitoringPerformanceOptimizer',
    'MonitoringOptimizationManager',
    'optimize_monitoring_system',
    'get_optimized_interval',
    'should_skip_task'
]

# Version information
__version__ = '1.0.0'
__author__ = 'Tech Stack Generation Team'
__description__ = 'Comprehensive monitoring and quality assurance for tech stack generation'