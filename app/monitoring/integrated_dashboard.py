"""
Integrated Monitoring Dashboard and Alerting System

Provides unified dashboard showing real-time tech stack generation metrics,
alert system for quality degradation and performance issues, monitoring system
health checks, and comprehensive monitoring configuration management.
"""

import asyncio
import json
import streamlit as st
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
from pathlib import Path
import pandas as pd

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service

# Try to import Plotly for advanced charts, fall back to simple charts if not available
try:
    import plotly.express as px
    import plotly.graph_objects as go
    from plotly.subplots import make_subplots
    PLOTLY_AVAILABLE = True
except ImportError:
    PLOTLY_AVAILABLE = False


class DashboardSection(Enum):
    """Dashboard sections."""
    OVERVIEW = "overview"
    REAL_TIME_METRICS = "real_time_metrics"
    ALERTS = "alerts"
    QUALITY_MONITORING = "quality_monitoring"
    PERFORMANCE_ANALYTICS = "performance_analytics"
    SYSTEM_HEALTH = "system_health"
    CONFIGURATION = "configuration"
    DATA_RETENTION = "data_retention"


class AlertSeverity(Enum):
    """Alert severity levels for dashboard."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class DashboardConfig:
    """Dashboard configuration settings."""
    auto_refresh_interval: int = 30  # seconds
    max_alerts_display: int = 50
    metrics_retention_hours: int = 168  # 7 days
    alert_retention_hours: int = 720  # 30 days
    real_time_update_enabled: bool = True
    alert_notifications_enabled: bool = True
    performance_threshold_warning: float = 20.0  # seconds
    performance_threshold_critical: float = 45.0  # seconds
    accuracy_threshold_warning: float = 0.80
    accuracy_threshold_critical: float = 0.70
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'DashboardConfig':
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SystemHealthStatus:
    """System health status information."""
    overall_health: str  # excellent, good, fair, poor, critical
    component_status: Dict[str, str]
    active_alerts: int
    critical_alerts: int
    last_update: datetime
    uptime_hours: float
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        data = asdict(self)
        data['last_update'] = self.last_update.isoformat()
        return data


class IntegratedMonitoringDashboard(ConfigurableService):
    """
    Integrated monitoring dashboard and alerting system.
    
    Provides unified real-time monitoring, alerting, system health checks,
    and configuration management for tech stack generation monitoring.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'IntegratedMonitoringDashboard')
        
        # Initialize logger
        try:
            self.logger = require_service('logger', context='IntegratedMonitoringDashboard')
        except Exception:
            import logging
            self.logger = logging.getLogger('IntegratedMonitoringDashboard')
        
        # Dashboard configuration
        self.dashboard_config = DashboardConfig(**(config or {}))
        
        # Service dependencies
        self.tech_stack_monitor = None
        self.quality_assurance = None
        self.performance_analytics = None
        self.real_time_quality_monitor = None
        self.monitoring_integration = None
        
        # Dashboard state
        self.system_start_time = datetime.now()
        self.last_health_check = None
        self.cached_dashboard_data = {}
        self.cache_timestamp = None
        self.cache_ttl_seconds = 30
        
        # Alert management
        self.active_alerts: List[Dict[str, Any]] = []
        self.alert_history: List[Dict[str, Any]] = []
        self.alert_rules: Dict[str, Dict[str, Any]] = {}
        
        # Initialize default alert rules
        self._initialize_default_alert_rules()
    
    async def _do_initialize(self) -> None:
        """Initialize the integrated monitoring dashboard."""
        await self.initialize_dashboard()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the integrated monitoring dashboard."""
        await self.shutdown_dashboard()
    
    async def initialize_dashboard(self) -> None:
        """Initialize the dashboard and its dependencies."""
        try:
            self.logger.info("Initializing integrated monitoring dashboard")
            
            # Initialize service dependencies
            await self._initialize_monitoring_services()
            
            # Load configuration
            await self._load_dashboard_configuration()
            
            # Initialize alert system
            await self._initialize_alert_system()
            
            # Start background tasks
            if self.dashboard_config.real_time_update_enabled:
                asyncio.create_task(self._real_time_update_task())
            
            asyncio.create_task(self._health_check_task())
            asyncio.create_task(self._data_retention_task())
            
            self.logger.info("Integrated monitoring dashboard initialized successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to initialize integrated monitoring dashboard: {e}")
            raise
    
    async def shutdown_dashboard(self) -> None:
        """Shutdown the dashboard."""
        try:
            self.logger.info("Shutting down integrated monitoring dashboard")
            
            # Save configuration
            await self._save_dashboard_configuration()
            
            # Archive alerts
            await self._archive_alerts()
            
            self.logger.info("Integrated monitoring dashboard shutdown complete")
            
        except Exception as e:
            self.logger.error(f"Error shutting down dashboard: {e}")
    
    async def _initialize_monitoring_services(self) -> None:
        """Initialize monitoring service dependencies."""
        try:
            # Get services from registry
            self.tech_stack_monitor = optional_service('tech_stack_monitor', context='IntegratedDashboard')
            self.quality_assurance = optional_service('quality_assurance_system', context='IntegratedDashboard')
            self.performance_analytics = optional_service('performance_analytics', context='IntegratedDashboard')
            self.real_time_quality_monitor = optional_service('real_time_quality_monitor', context='IntegratedDashboard')
            self.monitoring_integration = optional_service('tech_stack_monitoring_integration', context='IntegratedDashboard')
            
            # Try direct imports if services not available
            if not self.tech_stack_monitor:
                try:
                    from app.monitoring.tech_stack_monitor import TechStackMonitor
                    self.tech_stack_monitor = TechStackMonitor()
                except ImportError:
                    self.logger.warning("TechStackMonitor not available")
            
            if not self.quality_assurance:
                try:
                    from app.monitoring.quality_assurance import QualityAssuranceSystem
                    self.quality_assurance = QualityAssuranceSystem()
                except ImportError:
                    self.logger.warning("QualityAssuranceSystem not available")
            
            if not self.performance_analytics:
                try:
                    from app.monitoring.performance_analytics import PerformanceAnalytics
                    self.performance_analytics = PerformanceAnalytics()
                except ImportError:
                    self.logger.warning("PerformanceAnalytics not available")
            
            if not self.real_time_quality_monitor:
                try:
                    from app.monitoring.real_time_quality_monitor import RealTimeQualityMonitor
                    self.real_time_quality_monitor = RealTimeQualityMonitor()
                except ImportError:
                    self.logger.warning("RealTimeQualityMonitor not available")
            
            if not self.monitoring_integration:
                try:
                    from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService
                    self.monitoring_integration = TechStackMonitoringIntegrationService()
                except ImportError:
                    self.logger.warning("MonitoringIntegrationService not available")
            
            self.logger.info(f"Initialized monitoring services: "
                           f"monitor={bool(self.tech_stack_monitor)}, "
                           f"qa={bool(self.quality_assurance)}, "
                           f"analytics={bool(self.performance_analytics)}, "
                           f"real_time_qa={bool(self.real_time_quality_monitor)}, "
                           f"integration={bool(self.monitoring_integration)}")
            
        except Exception as e:
            self.logger.error(f"Error initializing monitoring services: {e}")
    
    def _initialize_default_alert_rules(self) -> None:
        """Initialize default alert rules."""
        self.alert_rules = {
            'performance_degradation': {
                'name': 'Performance Degradation',
                'description': 'Alert when response time exceeds thresholds',
                'metric': 'processing_time',
                'warning_threshold': self.dashboard_config.performance_threshold_warning,
                'critical_threshold': self.dashboard_config.performance_threshold_critical,
                'enabled': True
            },
            'accuracy_degradation': {
                'name': 'Accuracy Degradation',
                'description': 'Alert when extraction accuracy falls below thresholds',
                'metric': 'extraction_accuracy',
                'warning_threshold': self.dashboard_config.accuracy_threshold_warning,
                'critical_threshold': self.dashboard_config.accuracy_threshold_critical,
                'enabled': True
            },
            'high_error_rate': {
                'name': 'High Error Rate',
                'description': 'Alert when error rate exceeds 5%',
                'metric': 'error_rate',
                'warning_threshold': 0.05,
                'critical_threshold': 0.10,
                'enabled': True
            },
            'system_health_degradation': {
                'name': 'System Health Degradation',
                'description': 'Alert when overall system health degrades',
                'metric': 'system_health',
                'warning_threshold': 0.80,
                'critical_threshold': 0.60,
                'enabled': True
            },
            'catalog_inconsistency': {
                'name': 'Catalog Inconsistency',
                'description': 'Alert when catalog consistency falls below threshold',
                'metric': 'catalog_consistency',
                'warning_threshold': 0.95,
                'critical_threshold': 0.90,
                'enabled': True
            }
        }
    
    def render_dashboard(self) -> None:
        """Render the complete integrated monitoring dashboard."""
        st.set_page_config(
            page_title="Integrated Monitoring Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded"
        )
        
        st.title("📊 Integrated Tech Stack Monitoring Dashboard")
        st.markdown("Real-time monitoring, alerting, and system health management")
        
        # Sidebar navigation and controls
        self._render_sidebar()
        
        # Get selected section from sidebar
        selected_section = st.session_state.get('dashboard_section', DashboardSection.OVERVIEW.value)
        
        # Render selected section
        if selected_section == DashboardSection.OVERVIEW.value:
            self._render_overview_section()
        elif selected_section == DashboardSection.REAL_TIME_METRICS.value:
            self._render_real_time_metrics_section()
        elif selected_section == DashboardSection.ALERTS.value:
            self._render_alerts_section()
        elif selected_section == DashboardSection.QUALITY_MONITORING.value:
            self._render_quality_monitoring_section()
        elif selected_section == DashboardSection.PERFORMANCE_ANALYTICS.value:
            self._render_performance_analytics_section()
        elif selected_section == DashboardSection.SYSTEM_HEALTH.value:
            self._render_system_health_section()
        elif selected_section == DashboardSection.CONFIGURATION.value:
            self._render_configuration_section()
        elif selected_section == DashboardSection.DATA_RETENTION.value:
            self._render_data_retention_section()
    
    def _render_sidebar(self) -> None:
        """Render dashboard sidebar with navigation and controls."""
        st.sidebar.header("🧭 Navigation")
        
        # Section selector
        sections = {
            "📈 Overview": DashboardSection.OVERVIEW.value,
            "⚡ Real-time Metrics": DashboardSection.REAL_TIME_METRICS.value,
            "🚨 Alerts": DashboardSection.ALERTS.value,
            "🔍 Quality Monitoring": DashboardSection.QUALITY_MONITORING.value,
            "📊 Performance Analytics": DashboardSection.PERFORMANCE_ANALYTICS.value,
            "🏥 System Health": DashboardSection.SYSTEM_HEALTH.value,
            "⚙️ Configuration": DashboardSection.CONFIGURATION.value,
            "🗄️ Data Retention": DashboardSection.DATA_RETENTION.value
        }
        
        selected_section = st.sidebar.selectbox(
            "Select Section",
            options=list(sections.keys()),
            index=0
        )
        
        st.session_state.dashboard_section = sections[selected_section]
        
        # Dashboard controls
        st.sidebar.header("🎛️ Controls")
        
        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox(
            "Auto Refresh",
            value=self.dashboard_config.real_time_update_enabled,
            help=f"Refresh every {self.dashboard_config.auto_refresh_interval} seconds"
        )
        
        if auto_refresh != self.dashboard_config.real_time_update_enabled:
            self.dashboard_config.real_time_update_enabled = auto_refresh
        
        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now"):
            self._clear_cache()
            st.rerun()
        
        # Time range selector
        time_ranges = {
            "Last Hour": 1,
            "Last 6 Hours": 6,
            "Last 24 Hours": 24,
            "Last 7 Days": 168,
            "Last 30 Days": 720
        }
        
        selected_range = st.sidebar.selectbox(
            "Time Range",
            options=list(time_ranges.keys()),
            index=2  # Default to 24 hours
        )
        
        st.session_state.time_window_hours = time_ranges[selected_range]
        
        # System status indicator
        st.sidebar.header("🔧 System Status")
        self._render_sidebar_system_status()
        
        # Quick actions
        st.sidebar.header("⚡ Quick Actions")
        
        if st.sidebar.button("📊 Export Dashboard Data"):
            self._export_dashboard_data()
        
        if st.sidebar.button("🚨 Test Alert System"):
            self._test_alert_system()
        
        if st.sidebar.button("🧹 Clear Cache"):
            self._clear_cache()
            st.sidebar.success("Cache cleared!")
        
        # Auto-refresh implementation
        if auto_refresh:
            import time
            time.sleep(self.dashboard_config.auto_refresh_interval)
            st.rerun()
    
    def _render_sidebar_system_status(self) -> None:
        """Render system status in sidebar."""
        try:
            health_status = self._get_system_health_status()
            
            # Overall health indicator
            health_colors = {
                'excellent': '🟢',
                'good': '🟡',
                'fair': '🟠',
                'poor': '🔴',
                'critical': '🚨'
            }
            
            health_emoji = health_colors.get(health_status.overall_health, '❓')
            st.sidebar.markdown(f"**Overall Health:** {health_emoji} {health_status.overall_health.title()}")
            
            # Component status
            for component, status in health_status.component_status.items():
                status_emoji = '🟢' if status == 'online' else '🔴' if status == 'offline' else '🟡'
                st.sidebar.markdown(f"**{component}:** {status_emoji}")
            
            # Alert summary
            if health_status.critical_alerts > 0:
                st.sidebar.error(f"🚨 {health_status.critical_alerts} Critical Alerts")
            elif health_status.active_alerts > 0:
                st.sidebar.warning(f"⚠️ {health_status.active_alerts} Active Alerts")
            else:
                st.sidebar.success("✅ No Active Alerts")
            
            # Uptime
            st.sidebar.markdown(f"**Uptime:** {health_status.uptime_hours:.1f} hours")
            
        except Exception as e:
            st.sidebar.error(f"Error getting system status: {e}")
    
    def _render_overview_section(self) -> None:
        """Render dashboard overview section."""
        st.header("📈 System Overview")
        
        # Get dashboard data
        dashboard_data = self._get_dashboard_data()
        
        if not dashboard_data:
            st.warning("No monitoring data available. Please ensure monitoring services are running.")
            return
        
        # Key metrics overview
        col1, col2, col3, col4, col5 = st.columns(5)
        
        with col1:
            total_sessions = dashboard_data.get('summary', {}).get('total_sessions', 0)
            st.metric("Total Sessions", total_sessions, help="Tech stack generation sessions")
        
        with col2:
            avg_accuracy = dashboard_data.get('accuracy', {}).get('average', 0)
            accuracy_trend = dashboard_data.get('accuracy', {}).get('trend', 'stable')
            trend_delta = "↗️" if accuracy_trend == "improving" else "↘️" if accuracy_trend == "declining" else "→"
            st.metric("Avg Accuracy", f"{avg_accuracy:.1%}", delta=trend_delta)
        
        with col3:
            avg_time = dashboard_data.get('performance', {}).get('average_time', 0)
            perf_trend = dashboard_data.get('performance', {}).get('trend', 'stable')
            trend_delta = "↗️" if perf_trend == "improving" else "↘️" if perf_trend == "declining" else "→"
            st.metric("Avg Response Time", f"{avg_time:.1f}s", delta=trend_delta)
        
        with col4:
            satisfaction = dashboard_data.get('satisfaction', {}).get('average', 0)
            sat_trend = dashboard_data.get('satisfaction', {}).get('trend', 'stable')
            trend_delta = "↗️" if sat_trend == "improving" else "↘️" if sat_trend == "declining" else "→"
            st.metric("User Satisfaction", f"{satisfaction:.1f}/5", delta=trend_delta)
        
        with col5:
            active_alerts = len(self.active_alerts)
            critical_alerts = len([a for a in self.active_alerts if a.get('severity') == 'critical'])
            alert_color = "normal" if active_alerts == 0 else "inverse"
            st.metric("Active Alerts", active_alerts, delta=f"{critical_alerts} Critical", delta_color=alert_color)
        
        # Recent activity timeline
        st.subheader("📅 Recent Activity")
        self._render_activity_timeline(dashboard_data)
        
        # System health overview
        st.subheader("🏥 System Health Overview")
        self._render_health_overview()
    
    def _render_real_time_metrics_section(self) -> None:
        """Render real-time metrics section."""
        st.header("⚡ Real-time Metrics")
        
        # Real-time metrics display
        if self.monitoring_integration:
            self._render_live_session_metrics()
        else:
            st.warning("Real-time monitoring integration not available")
        
        # Current system load
        self._render_system_load_metrics()
        
        # Live quality scores
        if self.real_time_quality_monitor:
            self._render_live_quality_scores()
    
    def _render_alerts_section(self) -> None:
        """Render alerts and notifications section."""
        st.header("🚨 Alerts & Notifications")
        
        # Alert summary
        col1, col2, col3, col4 = st.columns(4)
        
        critical_alerts = [a for a in self.active_alerts if a.get('severity') == 'critical']
        error_alerts = [a for a in self.active_alerts if a.get('severity') == 'error']
        warning_alerts = [a for a in self.active_alerts if a.get('severity') == 'warning']
        info_alerts = [a for a in self.active_alerts if a.get('severity') == 'info']
        
        with col1:
            st.metric("🚨 Critical", len(critical_alerts))
        with col2:
            st.metric("❌ Errors", len(error_alerts))
        with col3:
            st.metric("⚠️ Warnings", len(warning_alerts))
        with col4:
            st.metric("ℹ️ Info", len(info_alerts))
        
        # Active alerts table
        if self.active_alerts:
            st.subheader("Active Alerts")
            self._render_alerts_table(self.active_alerts)
        else:
            st.success("✅ No active alerts")
        
        # Alert configuration
        st.subheader("Alert Configuration")
        self._render_alert_configuration()
        
        # Alert history
        if st.checkbox("Show Alert History"):
            st.subheader("Alert History")
            self._render_alerts_table(self.alert_history[-20:])  # Last 20 alerts
    
    def _render_quality_monitoring_section(self) -> None:
        """Render quality monitoring section."""
        st.header("🔍 Quality Monitoring")
        
        if not self.quality_assurance:
            st.warning("Quality Assurance system not available")
            return
        
        # Quality overview
        self._render_quality_overview()
        
        # Quality trends
        self._render_quality_trends()
        
        # Quality recommendations
        self._render_quality_recommendations()
    
    def _render_performance_analytics_section(self) -> None:
        """Render performance analytics section."""
        st.header("📊 Performance Analytics")
        
        if not self.performance_analytics:
            st.warning("Performance Analytics system not available")
            return
        
        # Performance overview
        self._render_performance_overview()
        
        # Bottleneck analysis
        self._render_bottleneck_analysis()
        
        # Usage patterns
        self._render_usage_patterns()
        
        # Predictive insights
        self._render_predictive_insights()
    
    def _render_system_health_section(self) -> None:
        """Render system health section."""
        st.header("🏥 System Health")
        
        # Comprehensive health status
        health_status = self._get_system_health_status()
        
        # Health overview
        col1, col2, col3 = st.columns(3)
        
        with col1:
            health_colors = {
                'excellent': '🟢',
                'good': '🟡',
                'fair': '🟠',
                'poor': '🔴',
                'critical': '🚨'
            }
            health_emoji = health_colors.get(health_status.overall_health, '❓')
            st.metric("Overall Health", f"{health_emoji} {health_status.overall_health.title()}")
        
        with col2:
            st.metric("Uptime", f"{health_status.uptime_hours:.1f} hours")
        
        with col3:
            st.metric("Last Health Check", health_status.last_update.strftime("%H:%M:%S"))
        
        # Component health details
        st.subheader("Component Health")
        self._render_component_health(health_status.component_status)
        
        # Health checks and diagnostics
        st.subheader("Health Checks & Diagnostics")
        self._render_health_diagnostics()
        
        # Self-monitoring capabilities
        st.subheader("Self-Monitoring")
        self._render_self_monitoring()
    
    def _render_configuration_section(self) -> None:
        """Render configuration management section."""
        st.header("⚙️ Configuration Management")
        
        # Dashboard configuration
        st.subheader("Dashboard Configuration")
        self._render_dashboard_configuration()
        
        # Alert thresholds configuration
        st.subheader("Alert Thresholds")
        self._render_threshold_configuration()
        
        # Monitoring service configuration
        st.subheader("Monitoring Services")
        self._render_service_configuration()
        
        # Export/Import configuration
        st.subheader("Configuration Management")
        self._render_config_management()
    
    def _render_data_retention_section(self) -> None:
        """Render data retention and archival section."""
        st.header("🗄️ Data Retention & Archival")
        
        # Current data usage
        st.subheader("Current Data Usage")
        self._render_data_usage_overview()
        
        # Retention policies
        st.subheader("Retention Policies")
        self._render_retention_policies()
        
        # Data archival
        st.subheader("Data Archival")
        self._render_data_archival()
        
        # Data cleanup
        st.subheader("Data Cleanup")
        self._render_data_cleanup()
    
    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data with caching."""
        # Check cache
        if (self.cached_dashboard_data and 
            self.cache_timestamp and 
            (datetime.now() - self.cache_timestamp).total_seconds() < self.cache_ttl_seconds):
            return self.cached_dashboard_data
        
        # Collect data from all monitoring services
        dashboard_data = {}
        
        try:
            # Tech stack monitor data
            if self.tech_stack_monitor:
                monitor_data = self.tech_stack_monitor.get_quality_dashboard_data()
                dashboard_data.update(monitor_data)
            
            # Quality assurance data
            if self.quality_assurance:
                qa_data = self._get_qa_dashboard_data()
                dashboard_data['qa'] = qa_data
            
            # Performance analytics data
            if self.performance_analytics:
                analytics_data = self._get_analytics_dashboard_data()
                dashboard_data['analytics'] = analytics_data
            
            # Real-time quality data
            if self.real_time_quality_monitor:
                real_time_data = self._get_real_time_dashboard_data()
                dashboard_data['real_time'] = real_time_data
            
            # Integration service data
            if self.monitoring_integration:
                integration_data = self._get_integration_dashboard_data()
                dashboard_data['integration'] = integration_data
            
            # Cache the data
            self.cached_dashboard_data = dashboard_data
            self.cache_timestamp = datetime.now()
            
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
        
        return dashboard_data
    
    def _get_system_health_status(self) -> SystemHealthStatus:
        """Get comprehensive system health status."""
        try:
            # Component status
            component_status = {
                'Tech Stack Monitor': 'online' if self.tech_stack_monitor else 'offline',
                'Quality Assurance': 'online' if self.quality_assurance else 'offline',
                'Performance Analytics': 'online' if self.performance_analytics else 'offline',
                'Real-time Quality Monitor': 'online' if self.real_time_quality_monitor else 'offline',
                'Monitoring Integration': 'online' if self.monitoring_integration else 'offline'
            }
            
            # Calculate overall health
            online_components = sum(1 for status in component_status.values() if status == 'online')
            total_components = len(component_status)
            health_ratio = online_components / total_components
            
            if health_ratio >= 0.9:
                overall_health = 'excellent'
            elif health_ratio >= 0.7:
                overall_health = 'good'
            elif health_ratio >= 0.5:
                overall_health = 'fair'
            elif health_ratio >= 0.3:
                overall_health = 'poor'
            else:
                overall_health = 'critical'
            
            # Alert counts
            active_alerts = len(self.active_alerts)
            critical_alerts = len([a for a in self.active_alerts if a.get('severity') == 'critical'])
            
            # Uptime calculation
            uptime_hours = (datetime.now() - self.system_start_time).total_seconds() / 3600
            
            return SystemHealthStatus(
                overall_health=overall_health,
                component_status=component_status,
                active_alerts=active_alerts,
                critical_alerts=critical_alerts,
                last_update=datetime.now(),
                uptime_hours=uptime_hours
            )
            
        except Exception as e:
            self.logger.error(f"Error getting system health status: {e}")
            return SystemHealthStatus(
                overall_health='unknown',
                component_status={},
                active_alerts=0,
                critical_alerts=0,
                last_update=datetime.now(),
                uptime_hours=0.0
            )
    
    def _clear_cache(self) -> None:
        """Clear dashboard data cache."""
        self.cached_dashboard_data = {}
        self.cache_timestamp = None
    
    # Additional helper methods will be implemented in the next part...
    
    async def _real_time_update_task(self) -> None:
        """Background task for real-time updates."""
        while self.dashboard_config.real_time_update_enabled:
            try:
                # Update dashboard data
                self._clear_cache()
                
                # Check for new alerts
                await self._check_alert_conditions()
                
                # Update system health
                self.last_health_check = datetime.now()
                
                await asyncio.sleep(self.dashboard_config.auto_refresh_interval)
                
            except Exception as e:
                self.logger.error(f"Error in real-time update task: {e}")
                await asyncio.sleep(60)  # Wait longer on error
    
    async def _health_check_task(self) -> None:
        """Background task for system health checks."""
        while True:
            try:
                # Perform comprehensive health check
                health_status = self._get_system_health_status()
                
                # Check for health degradation
                if health_status.overall_health in ['poor', 'critical']:
                    await self._create_health_alert(health_status)
                
                # Update last health check time
                self.last_health_check = datetime.now()
                
                await asyncio.sleep(300)  # Health check every 5 minutes
                
            except Exception as e:
                self.logger.error(f"Error in health check task: {e}")
                await asyncio.sleep(60)
    
    async def _data_retention_task(self) -> None:
        """Background task for data retention and cleanup."""
        while True:
            try:
                # Clean up old alerts
                cutoff_time = datetime.now() - timedelta(hours=self.dashboard_config.alert_retention_hours)
                self.alert_history = [a for a in self.alert_history if 
                                    datetime.fromisoformat(a.get('timestamp', '')) > cutoff_time]
                
                # Archive old data if needed
                await self._archive_old_data()
                
                await asyncio.sleep(3600)  # Run every hour
                
            except Exception as e:
                self.logger.error(f"Error in data retention task: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error


def render_integrated_monitoring_dashboard():
    """Render the integrated monitoring dashboard (standalone function for Streamlit)."""
    dashboard = IntegratedMonitoringDashboard()
    dashboard.render_dashboard()   
 
    # Dashboard rendering helper methods
    
    def _render_activity_timeline(self, dashboard_data: Dict[str, Any]) -> None:
        """Render recent activity timeline."""
        try:
            # Get recent events from monitoring integration
            if self.monitoring_integration:
                recent_events = []
                active_sessions = self.monitoring_integration.get_active_sessions()
                
                for session_info in active_sessions[-5:]:  # Last 5 sessions
                    session_id = session_info['session_id']
                    session_events = self.monitoring_integration.get_session_events(session_id)
                    
                    for event in session_events[-3:]:  # Last 3 events per session
                        recent_events.append({
                            'timestamp': event.get('timestamp', ''),
                            'event_type': event.get('event_type', ''),
                            'component': event.get('component', ''),
                            'session_id': session_id[:8],
                            'success': event.get('success', True)
                        })
                
                if recent_events:
                    # Sort by timestamp
                    recent_events.sort(key=lambda x: x['timestamp'], reverse=True)
                    
                    # Display timeline
                    for event in recent_events[:10]:  # Show last 10 events
                        timestamp = datetime.fromisoformat(event['timestamp']).strftime("%H:%M:%S")
                        status_emoji = "✅" if event['success'] else "❌"
                        
                        st.markdown(f"**{timestamp}** {status_emoji} {event['component']} - {event['event_type']} (Session: {event['session_id']})")
                else:
                    st.info("No recent activity to display")
            else:
                st.info("Activity timeline requires monitoring integration service")
                
        except Exception as e:
            st.error(f"Error rendering activity timeline: {e}")
    
    def _render_health_overview(self) -> None:
        """Render system health overview."""
        try:
            health_status = self._get_system_health_status()
            
            # Health status cards
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("### 🏥 System Health")
                health_colors = {
                    'excellent': 'success',
                    'good': 'info',
                    'fair': 'warning',
                    'poor': 'error',
                    'critical': 'error'
                }
                health_color = health_colors.get(health_status.overall_health, 'info')
                
                if health_color == 'success':
                    st.success(f"System health is {health_status.overall_health}")
                elif health_color == 'warning':
                    st.warning(f"System health is {health_status.overall_health}")
                elif health_color == 'error':
                    st.error(f"System health is {health_status.overall_health}")
                else:
                    st.info(f"System health is {health_status.overall_health}")
            
            with col2:
                st.markdown("### 📊 Service Status")
                online_count = sum(1 for status in health_status.component_status.values() if status == 'online')
                total_count = len(health_status.component_status)
                st.metric("Services Online", f"{online_count}/{total_count}")
            
            with col3:
                st.markdown("### 🚨 Alert Status")
                if health_status.critical_alerts > 0:
                    st.error(f"{health_status.critical_alerts} critical alerts")
                elif health_status.active_alerts > 0:
                    st.warning(f"{health_status.active_alerts} active alerts")
                else:
                    st.success("No active alerts")
                    
        except Exception as e:
            st.error(f"Error rendering health overview: {e}")
    
    def _render_live_session_metrics(self) -> None:
        """Render live session metrics."""
        try:
            if not self.monitoring_integration:
                st.warning("Monitoring integration service not available")
                return
            
            active_sessions = self.monitoring_integration.get_active_sessions()
            
            if not active_sessions:
                st.info("No active sessions")
                return
            
            st.subheader("🔴 Live Sessions")
            
            for session_info in active_sessions[-5:]:  # Show last 5 active sessions
                session_id = session_info['session_id']
                start_time = session_info.get('start_time', datetime.now())
                
                with st.expander(f"Session {session_id[:8]} - Started {start_time.strftime('%H:%M:%S')}"):
                    session_events = self.monitoring_integration.get_session_events(session_id)
                    
                    # Session metrics
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("Events", len(session_events))
                    
                    with col2:
                        duration = (datetime.now() - start_time).total_seconds()
                        st.metric("Duration", f"{duration:.1f}s")
                    
                    with col3:
                        success_events = sum(1 for e in session_events if e.get('success', True))
                        success_rate = success_events / len(session_events) if session_events else 1.0
                        st.metric("Success Rate", f"{success_rate:.1%}")
                    
                    # Recent events
                    if session_events:
                        st.markdown("**Recent Events:**")
                        for event in session_events[-3:]:
                            timestamp = datetime.fromisoformat(event.get('timestamp', '')).strftime("%H:%M:%S")
                            status = "✅" if event.get('success', True) else "❌"
                            st.markdown(f"- {timestamp} {status} {event.get('event_type', '')}")
                            
        except Exception as e:
            st.error(f"Error rendering live session metrics: {e}")
    
    def _render_system_load_metrics(self) -> None:
        """Render current system load metrics."""
        try:
            st.subheader("⚡ System Load")
            
            # Get current metrics from monitoring services
            current_metrics = {}
            
            if self.tech_stack_monitor:
                recent_metrics = self.tech_stack_monitor._get_recent_metrics(hours=1)
                
                # Calculate current load indicators
                processing_times = [m.value for m in recent_metrics if m.name == "processing_time"]
                if processing_times:
                    current_metrics['avg_processing_time'] = sum(processing_times) / len(processing_times)
                    current_metrics['max_processing_time'] = max(processing_times)
                
                accuracy_metrics = [m.value for m in recent_metrics if m.name == "extraction_accuracy"]
                if accuracy_metrics:
                    current_metrics['current_accuracy'] = accuracy_metrics[-1] if accuracy_metrics else 0
                
                session_count = len(set(m.session_id for m in recent_metrics if m.session_id))
                current_metrics['active_sessions'] = session_count
            
            # Display load metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                avg_time = current_metrics.get('avg_processing_time', 0)
                color = "normal" if avg_time < 15 else "inverse"
                st.metric("Avg Processing Time", f"{avg_time:.1f}s", delta_color=color)
            
            with col2:
                max_time = current_metrics.get('max_processing_time', 0)
                color = "normal" if max_time < 30 else "inverse"
                st.metric("Max Processing Time", f"{max_time:.1f}s", delta_color=color)
            
            with col3:
                accuracy = current_metrics.get('current_accuracy', 0)
                color = "normal" if accuracy > 0.85 else "inverse"
                st.metric("Current Accuracy", f"{accuracy:.1%}", delta_color=color)
            
            with col4:
                sessions = current_metrics.get('active_sessions', 0)
                st.metric("Sessions (1h)", sessions)
                
        except Exception as e:
            st.error(f"Error rendering system load metrics: {e}")
    
    def _render_live_quality_scores(self) -> None:
        """Render live quality scores."""
        try:
            if not self.real_time_quality_monitor:
                st.info("Real-time quality monitor not available")
                return
            
            st.subheader("🔍 Live Quality Scores")
            
            # Get recent quality scores
            recent_scores = self.real_time_quality_monitor.quality_scores[-10:]  # Last 10 scores
            
            if not recent_scores:
                st.info("No recent quality scores available")
                return
            
            # Display quality metrics
            col1, col2, col3 = st.columns(3)
            
            # Group scores by metric type
            extraction_scores = [s for s in recent_scores if s.metric_type.value == 'extraction_accuracy']
            consistency_scores = [s for s in recent_scores if s.metric_type.value == 'ecosystem_consistency']
            satisfaction_scores = [s for s in recent_scores if s.metric_type.value == 'user_satisfaction']
            
            with col1:
                if extraction_scores:
                    latest_score = extraction_scores[-1].overall_score
                    st.metric("Extraction Quality", f"{latest_score:.1%}")
                else:
                    st.metric("Extraction Quality", "N/A")
            
            with col2:
                if consistency_scores:
                    latest_score = consistency_scores[-1].overall_score
                    st.metric("Ecosystem Consistency", f"{latest_score:.1%}")
                else:
                    st.metric("Ecosystem Consistency", "N/A")
            
            with col3:
                if satisfaction_scores:
                    latest_score = satisfaction_scores[-1].overall_score
                    st.metric("User Satisfaction", f"{latest_score:.1%}")
                else:
                    st.metric("User Satisfaction", "N/A")
            
            # Quality trends (simple visualization)
            if PLOTLY_AVAILABLE and recent_scores:
                import plotly.graph_objects as go
                
                fig = go.Figure()
                
                for metric_type in ['extraction_accuracy', 'ecosystem_consistency', 'user_satisfaction']:
                    scores = [s for s in recent_scores if s.metric_type.value == metric_type]
                    if scores:
                        timestamps = [s.timestamp for s in scores]
                        values = [s.overall_score for s in scores]
                        
                        fig.add_trace(go.Scatter(
                            x=timestamps,
                            y=values,
                            mode='lines+markers',
                            name=metric_type.replace('_', ' ').title()
                        ))
                
                fig.update_layout(
                    title="Quality Score Trends",
                    xaxis_title="Time",
                    yaxis_title="Score",
                    height=300
                )
                
                st.plotly_chart(fig, use_container_width=True)
                
        except Exception as e:
            st.error(f"Error rendering live quality scores: {e}")
    
    def _render_alerts_table(self, alerts: List[Dict[str, Any]]) -> None:
        """Render alerts in a table format."""
        try:
            if not alerts:
                st.info("No alerts to display")
                return
            
            # Prepare alert data for table
            alert_data = []
            for alert in alerts:
                severity = alert.get('severity', 'info')
                severity_emoji = {
                    'critical': '🚨',
                    'error': '❌',
                    'warning': '⚠️',
                    'info': 'ℹ️'
                }.get(severity, 'ℹ️')
                
                timestamp = alert.get('timestamp', '')
                if timestamp:
                    try:
                        timestamp = datetime.fromisoformat(timestamp).strftime("%Y-%m-%d %H:%M:%S")
                    except Exception:
                        pass
                
                alert_data.append({
                    'Severity': f"{severity_emoji} {severity.upper()}",
                    'Timestamp': timestamp,
                    'Message': alert.get('message', ''),
                    'Category': alert.get('category', ''),
                    'Session': alert.get('session_id', 'N/A')[:8] if alert.get('session_id') else 'N/A'
                })
            
            # Create DataFrame and display
            df = pd.DataFrame(alert_data)
            
            # Style the table based on severity
            def style_severity(val):
                if '🚨' in val:
                    return 'background-color: #ffebee'
                elif '❌' in val:
                    return 'background-color: #fff3e0'
                elif '⚠️' in val:
                    return 'background-color: #f3e5f5'
                return ''
            
            styled_df = df.style.applymap(style_severity, subset=['Severity'])
            st.dataframe(styled_df, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error rendering alerts table: {e}")
    
    def _render_alert_configuration(self) -> None:
        """Render alert configuration interface."""
        try:
            st.markdown("### Alert Rules Configuration")
            
            # Display current alert rules
            for rule_id, rule in self.alert_rules.items():
                with st.expander(f"📋 {rule['name']}"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        enabled = st.checkbox(
                            "Enabled",
                            value=rule['enabled'],
                            key=f"alert_enabled_{rule_id}"
                        )
                        
                        warning_threshold = st.number_input(
                            "Warning Threshold",
                            value=rule['warning_threshold'],
                            key=f"alert_warning_{rule_id}"
                        )
                    
                    with col2:
                        critical_threshold = st.number_input(
                            "Critical Threshold",
                            value=rule['critical_threshold'],
                            key=f"alert_critical_{rule_id}"
                        )
                    
                    st.markdown(f"**Description:** {rule['description']}")
                    
                    # Update rule if values changed
                    if (enabled != rule['enabled'] or 
                        warning_threshold != rule['warning_threshold'] or
                        critical_threshold != rule['critical_threshold']):
                        
                        self.alert_rules[rule_id].update({
                            'enabled': enabled,
                            'warning_threshold': warning_threshold,
                            'critical_threshold': critical_threshold
                        })
            
            # Save configuration button
            if st.button("💾 Save Alert Configuration"):
                self._save_alert_configuration()
                st.success("Alert configuration saved!")
                
        except Exception as e:
            st.error(f"Error rendering alert configuration: {e}")
    
    def _render_dashboard_configuration(self) -> None:
        """Render dashboard configuration interface."""
        try:
            st.markdown("### Dashboard Settings")
            
            col1, col2 = st.columns(2)
            
            with col1:
                auto_refresh_interval = st.number_input(
                    "Auto Refresh Interval (seconds)",
                    min_value=10,
                    max_value=300,
                    value=self.dashboard_config.auto_refresh_interval
                )
                
                max_alerts_display = st.number_input(
                    "Max Alerts to Display",
                    min_value=10,
                    max_value=200,
                    value=self.dashboard_config.max_alerts_display
                )
                
                cache_ttl = st.number_input(
                    "Cache TTL (seconds)",
                    min_value=10,
                    max_value=300,
                    value=self.cache_ttl_seconds
                )
            
            with col2:
                real_time_updates = st.checkbox(
                    "Enable Real-time Updates",
                    value=self.dashboard_config.real_time_update_enabled
                )
                
                alert_notifications = st.checkbox(
                    "Enable Alert Notifications",
                    value=self.dashboard_config.alert_notifications_enabled
                )
            
            # Update configuration
            if st.button("💾 Save Dashboard Configuration"):
                self.dashboard_config.auto_refresh_interval = auto_refresh_interval
                self.dashboard_config.max_alerts_display = max_alerts_display
                self.dashboard_config.real_time_update_enabled = real_time_updates
                self.dashboard_config.alert_notifications_enabled = alert_notifications
                self.cache_ttl_seconds = cache_ttl
                
                self._save_dashboard_configuration()
                st.success("Dashboard configuration saved!")
                
        except Exception as e:
            st.error(f"Error rendering dashboard configuration: {e}")
    
    def _render_data_usage_overview(self) -> None:
        """Render data usage overview."""
        try:
            # Calculate data usage statistics
            metrics_count = len(self.tech_stack_monitor.metrics) if self.tech_stack_monitor else 0
            alerts_count = len(self.active_alerts) + len(self.alert_history)
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Stored Metrics", metrics_count)
            
            with col2:
                st.metric("Total Alerts", alerts_count)
            
            with col3:
                # Estimate memory usage (rough calculation)
                estimated_mb = (metrics_count * 0.001) + (alerts_count * 0.0005)
                st.metric("Est. Memory Usage", f"{estimated_mb:.1f} MB")
            
            with col4:
                # Calculate retention period
                if self.tech_stack_monitor and self.tech_stack_monitor.metrics:
                    oldest_metric = min(self.tech_stack_monitor.metrics, key=lambda m: m.timestamp)
                    retention_days = (datetime.now() - oldest_metric.timestamp).days
                    st.metric("Data Age", f"{retention_days} days")
                else:
                    st.metric("Data Age", "N/A")
                    
        except Exception as e:
            st.error(f"Error rendering data usage overview: {e}")
    
    def _render_retention_policies(self) -> None:
        """Render retention policies configuration."""
        try:
            st.markdown("### Retention Policies")
            
            col1, col2 = st.columns(2)
            
            with col1:
                metrics_retention = st.number_input(
                    "Metrics Retention (hours)",
                    min_value=24,
                    max_value=8760,  # 1 year
                    value=self.dashboard_config.metrics_retention_hours
                )
                
                alert_retention = st.number_input(
                    "Alert Retention (hours)",
                    min_value=24,
                    max_value=8760,  # 1 year
                    value=self.dashboard_config.alert_retention_hours
                )
            
            with col2:
                st.markdown("**Current Policies:**")
                st.markdown(f"- Metrics: {self.dashboard_config.metrics_retention_hours} hours")
                st.markdown(f"- Alerts: {self.dashboard_config.alert_retention_hours} hours")
                
                # Calculate cleanup dates
                metrics_cleanup = datetime.now() - timedelta(hours=self.dashboard_config.metrics_retention_hours)
                alerts_cleanup = datetime.now() - timedelta(hours=self.dashboard_config.alert_retention_hours)
                
                st.markdown(f"- Metrics cleanup: {metrics_cleanup.strftime('%Y-%m-%d %H:%M')}")
                st.markdown(f"- Alerts cleanup: {alerts_cleanup.strftime('%Y-%m-%d %H:%M')}")
            
            # Update retention policies
            if st.button("💾 Update Retention Policies"):
                self.dashboard_config.metrics_retention_hours = metrics_retention
                self.dashboard_config.alert_retention_hours = alert_retention
                st.success("Retention policies updated!")
                
        except Exception as e:
            st.error(f"Error rendering retention policies: {e}")
    
    # Data management and utility methods
    
    def _get_qa_dashboard_data(self) -> Dict[str, Any]:
        """Get quality assurance dashboard data."""
        try:
            if not self.quality_assurance:
                return {}
            
            latest_report = self.quality_assurance.get_latest_report() if hasattr(self.quality_assurance, 'get_latest_report') else None
            
            if not latest_report:
                return {}
            
            return {
                'overall_score': latest_report.overall_score,
                'check_results': [r.to_dict() for r in latest_report.check_results],
                'recommendations': latest_report.recommendations,
                'timestamp': latest_report.timestamp.isoformat()
            }
            
        except Exception as e:
            self.logger.error(f"Error getting QA dashboard data: {e}")
            return {}
    
    def _get_analytics_dashboard_data(self) -> Dict[str, Any]:
        """Get performance analytics dashboard data."""
        try:
            if not self.performance_analytics:
                return {}
            
            # Get recent analytics data
            analytics_data = {
                'usage_patterns': [p.to_dict() for p in self.performance_analytics.usage_patterns[-10:]],
                'performance_bottlenecks': [b.to_dict() for b in self.performance_analytics.performance_bottlenecks[-10:]],
                'satisfaction_analyses': [s.to_dict() for s in self.performance_analytics.satisfaction_analyses[-10:]],
                'predictive_insights': [i.to_dict() for i in self.performance_analytics.predictive_insights[-5:]]
            }
            
            return analytics_data
            
        except Exception as e:
            self.logger.error(f"Error getting analytics dashboard data: {e}")
            return {}
    
    def _get_real_time_dashboard_data(self) -> Dict[str, Any]:
        """Get real-time quality monitor dashboard data."""
        try:
            if not self.real_time_quality_monitor:
                return {}
            
            real_time_data = {
                'quality_scores': [s.to_dict() for s in self.real_time_quality_monitor.quality_scores[-20:]],
                'consistency_scores': [s.to_dict() for s in self.real_time_quality_monitor.consistency_scores[-20:]],
                'quality_alerts': [a.to_dict() for a in self.real_time_quality_monitor.quality_alerts[-10:]],
                'quality_trends': {k.value: v.to_dict() for k, v in self.real_time_quality_monitor.quality_trends.items()}
            }
            
            return real_time_data
            
        except Exception as e:
            self.logger.error(f"Error getting real-time dashboard data: {e}")
            return {}
    
    def _get_integration_dashboard_data(self) -> Dict[str, Any]:
        """Get monitoring integration dashboard data."""
        try:
            if not self.monitoring_integration:
                return {}
            
            integration_data = {
                'active_sessions': len(self.monitoring_integration.active_sessions),
                'total_events': sum(len(events) for events in self.monitoring_integration.session_events.values()),
                'service_status': {
                    'tech_stack_monitor': bool(self.monitoring_integration.tech_stack_monitor),
                    'quality_assurance': bool(self.monitoring_integration.quality_assurance),
                    'performance_analytics': bool(self.monitoring_integration.performance_analytics)
                }
            }
            
            return integration_data
            
        except Exception as e:
            self.logger.error(f"Error getting integration dashboard data: {e}")
            return {}
    
    async def _check_alert_conditions(self) -> None:
        """Check alert conditions and create alerts if needed."""
        try:
            dashboard_data = self._get_dashboard_data()
            
            # Check performance alerts
            avg_time = dashboard_data.get('performance', {}).get('average_time', 0)
            if avg_time > 0:
                await self._check_performance_alert(avg_time)
            
            # Check accuracy alerts
            avg_accuracy = dashboard_data.get('accuracy', {}).get('average', 0)
            if avg_accuracy > 0:
                await self._check_accuracy_alert(avg_accuracy)
            
            # Check system health alerts
            health_status = self._get_system_health_status()
            await self._check_health_alert(health_status)
            
        except Exception as e:
            self.logger.error(f"Error checking alert conditions: {e}")
    
    async def _check_performance_alert(self, avg_time: float) -> None:
        """Check and create performance alerts."""
        rule = self.alert_rules.get('performance_degradation')
        if not rule or not rule['enabled']:
            return
        
        if avg_time >= rule['critical_threshold']:
            await self._create_alert('critical', 'performance', 
                                   f"Critical performance degradation: {avg_time:.1f}s average response time")
        elif avg_time >= rule['warning_threshold']:
            await self._create_alert('warning', 'performance',
                                   f"Performance degradation warning: {avg_time:.1f}s average response time")
    
    async def _check_accuracy_alert(self, avg_accuracy: float) -> None:
        """Check and create accuracy alerts."""
        rule = self.alert_rules.get('accuracy_degradation')
        if not rule or not rule['enabled']:
            return
        
        if avg_accuracy <= rule['critical_threshold']:
            await self._create_alert('critical', 'accuracy',
                                   f"Critical accuracy degradation: {avg_accuracy:.1%} average accuracy")
        elif avg_accuracy <= rule['warning_threshold']:
            await self._create_alert('warning', 'accuracy',
                                   f"Accuracy degradation warning: {avg_accuracy:.1%} average accuracy")
    
    async def _check_health_alert(self, health_status: SystemHealthStatus) -> None:
        """Check and create system health alerts."""
        if health_status.overall_health in ['poor', 'critical']:
            severity = 'critical' if health_status.overall_health == 'critical' else 'error'
            await self._create_alert(severity, 'system_health',
                                   f"System health degraded to {health_status.overall_health}")
    
    async def _create_alert(self, severity: str, category: str, message: str, 
                          session_id: Optional[str] = None, details: Optional[Dict[str, Any]] = None) -> None:
        """Create a new alert."""
        alert = {
            'id': f"alert_{int(datetime.now().timestamp())}",
            'timestamp': datetime.now().isoformat(),
            'severity': severity,
            'category': category,
            'message': message,
            'session_id': session_id,
            'details': details or {},
            'resolved': False
        }
        
        self.active_alerts.append(alert)
        self.alert_history.append(alert.copy())
        
        # Limit active alerts
        if len(self.active_alerts) > self.dashboard_config.max_alerts_display:
            self.active_alerts = self.active_alerts[-self.dashboard_config.max_alerts_display:]
        
        self.logger.warning(f"Alert created: [{severity}] {category} - {message}")
    
    async def _create_health_alert(self, health_status: SystemHealthStatus) -> None:
        """Create health-related alert."""
        await self._create_alert(
            'error' if health_status.overall_health == 'critical' else 'warning',
            'system_health',
            f"System health is {health_status.overall_health}",
            details=health_status.to_dict()
        )
    
    def _export_dashboard_data(self) -> None:
        """Export dashboard data to file."""
        try:
            dashboard_data = self._get_dashboard_data()
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            
            export_data = {
                'timestamp': timestamp,
                'dashboard_data': dashboard_data,
                'system_health': self._get_system_health_status().to_dict(),
                'active_alerts': self.active_alerts,
                'alert_history': self.alert_history[-50:],  # Last 50 alerts
                'configuration': self.dashboard_config.to_dict()
            }
            
            filepath = f"exports/dashboard_export_{timestamp}.json"
            Path("exports").mkdir(exist_ok=True)
            
            with open(filepath, 'w') as f:
                json.dump(export_data, f, indent=2, default=str)
            
            st.success(f"✅ Dashboard data exported to {filepath}")
            
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
    
    def _test_alert_system(self) -> None:
        """Test the alert system by creating a test alert."""
        try:
            asyncio.create_task(self._create_alert(
                'info',
                'test',
                'Test alert - Alert system is functioning correctly',
                details={'test': True, 'timestamp': datetime.now().isoformat()}
            ))
            st.success("✅ Test alert created successfully!")
            
        except Exception as e:
            st.error(f"❌ Alert test failed: {str(e)}")
    
    async def _load_dashboard_configuration(self) -> None:
        """Load dashboard configuration from file."""
        try:
            config_path = Path("config/dashboard_config.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    config_data = json.load(f)
                self.dashboard_config = DashboardConfig.from_dict(config_data)
                self.logger.info("Dashboard configuration loaded")
        except Exception as e:
            self.logger.warning(f"Could not load dashboard configuration: {e}")
    
    async def _save_dashboard_configuration(self) -> None:
        """Save dashboard configuration to file."""
        try:
            config_path = Path("config/dashboard_config.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.dashboard_config.to_dict(), f, indent=2)
            
            self.logger.info("Dashboard configuration saved")
        except Exception as e:
            self.logger.error(f"Could not save dashboard configuration: {e}")
    
    def _save_alert_configuration(self) -> None:
        """Save alert configuration to file."""
        try:
            config_path = Path("config/alert_rules.json")
            config_path.parent.mkdir(exist_ok=True)
            
            with open(config_path, 'w') as f:
                json.dump(self.alert_rules, f, indent=2)
            
            self.logger.info("Alert configuration saved")
        except Exception as e:
            self.logger.error(f"Could not save alert configuration: {e}")
    
    async def _initialize_alert_system(self) -> None:
        """Initialize the alert system."""
        try:
            # Load alert rules if they exist
            config_path = Path("config/alert_rules.json")
            if config_path.exists():
                with open(config_path, 'r') as f:
                    saved_rules = json.load(f)
                self.alert_rules.update(saved_rules)
                self.logger.info("Alert rules loaded from configuration")
        except Exception as e:
            self.logger.warning(f"Could not load alert rules: {e}")
    
    async def _archive_alerts(self) -> None:
        """Archive alerts to file."""
        try:
            if self.alert_history:
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                archive_path = Path(f"archives/alerts_{timestamp}.json")
                archive_path.parent.mkdir(exist_ok=True)
                
                with open(archive_path, 'w') as f:
                    json.dump(self.alert_history, f, indent=2, default=str)
                
                self.logger.info(f"Alerts archived to {archive_path}")
        except Exception as e:
            self.logger.error(f"Could not archive alerts: {e}")
    
    async def _archive_old_data(self) -> None:
        """Archive old monitoring data."""
        try:
            # This would implement data archival logic
            # For now, just log that archival would happen
            self.logger.debug("Data archival check completed")
        except Exception as e:
            self.logger.error(f"Error in data archival: {e}")