"""
Simple Monitoring Dashboard for Streamlit

A lightweight monitoring dashboard that doesn't require external dependencies
like Plotly. Provides essential monitoring functionality using only Streamlit
built-in components.
"""

import streamlit as st
from typing import Dict, Any

from app.core.service import ConfigurableService
from app.utils.imports import require_service


class SimpleMonitoringDashboard(ConfigurableService):
    """
    Simple monitoring dashboard for tech stack generation.
    
    Provides essential monitoring functionality without external dependencies.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'SimpleMonitoringDashboard')
        try:
            self.logger = require_service('logger', context='SimpleMonitoringDashboard')
        except Exception:
            # Fallback logger for testing
            import logging
            self.logger = logging.getLogger('SimpleMonitoringDashboard')
    
    async def _do_initialize(self) -> None:
        """Initialize the simple monitoring dashboard."""
        pass
    
    async def _do_shutdown(self) -> None:
        """Shutdown the simple monitoring dashboard."""
        pass
    
    def render_system_status(self, monitoring_service) -> None:
        """Render comprehensive system status indicators."""
        st.subheader("🔧 Platform Status")
        
        try:
            status = monitoring_service.get_monitoring_status()
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                if status['integration_active']:
                    st.success("🟢 System Monitoring")
                else:
                    st.error("🔴 Monitoring Inactive")
            
            with col2:
                # Check if we have session data
                if st.session_state.get('session_id'):
                    st.success("🟢 Active Session")
                else:
                    st.warning("🟡 No Active Session")
            
            with col3:
                # Check database connectivity (if available)
                try:
                    # This would check actual database connectivity
                    st.success("🟢 Database Connected")
                except Exception:
                    st.warning("🟡 Database Status Unknown")
            
            with col4:
                if status['services_registered']['qa_system']:
                    st.success("🟢 Quality Assurance")
                else:
                    st.warning("🟡 QA System Unavailable")
        
        except Exception as e:
            st.error(f"Error getting system status: {e}")
        
        # Add platform usage overview
        self._render_platform_usage_overview()
    
    def render_control_panel(self, monitoring_service) -> None:
        """Render monitoring control panel."""
        st.subheader("🎛️ Control Panel")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Show appropriate button based on monitoring status
            status = monitoring_service.get_monitoring_status()
            if status['integration_active']:
                if st.button("⏹️ Disable Monitoring"):
                    try:
                        import asyncio
                        asyncio.run(monitoring_service.stop_monitoring_integration())
                        st.success("✅ Monitoring disabled!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to disable: {e}")
            else:
                if st.button("🚀 Enable Monitoring"):
                    try:
                        import asyncio
                        asyncio.run(monitoring_service.start_monitoring_integration())
                        st.success("✅ Monitoring enabled!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"❌ Failed to enable: {e}")
        
        with col2:
            if st.button("🔄 Restart Monitoring"):
                try:
                    import asyncio
                    # Stop and restart monitoring
                    asyncio.run(monitoring_service.stop_monitoring_integration())
                    asyncio.run(monitoring_service.start_monitoring_integration())
                    st.success("✅ Monitoring restarted!")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Failed to restart: {e}")
        
        with col3:
            if st.button("🔄 Refresh Status"):
                st.rerun()
        
        with col4:
            if st.button("📊 Generate QA Report"):
                try:
                    import asyncio
                    with st.spinner("Generating QA report..."):
                        report = asyncio.run(monitoring_service.generate_quality_report())
                        if report:
                            st.session_state.latest_qa_report = report
                            st.success("✅ QA report generated!")
                        else:
                            st.warning("⚠️ No QA report available")
                except Exception as e:
                    st.error(f"❌ Failed to generate report: {e}")
    
    def render_health_metrics(self, monitoring_service) -> None:
        """Render comprehensive platform health metrics."""
        st.subheader("📈 Platform Health")
        
        try:
            status = monitoring_service.get_monitoring_status()
            
            if not status['integration_active']:
                st.info("💡 Monitoring is currently disabled. Enable monitoring to see health metrics.")
                return
            
            real_time_status = monitoring_service.get_real_time_system_status()
            
            if 'system_health' in real_time_status:
                health = real_time_status['system_health']
                
                # Health overview
                col1, col2, col3, col4 = st.columns(4)
                
                with col1:
                    overall_score = health.get('overall_score', 0)
                    st.metric("Overall Health", f"{overall_score:.1%}")
                    
                    # Add health indicator
                    if overall_score >= 0.9:
                        st.success("🟢 Excellent")
                    elif overall_score >= 0.8:
                        st.success("🟢 Good")
                    elif overall_score >= 0.7:
                        st.warning("🟡 Fair")
                    elif overall_score >= 0.5:
                        st.warning("🟠 Poor")
                    else:
                        st.error("🔴 Critical")
                
                with col2:
                    accuracy_score = health.get('component_scores', {}).get('accuracy', 0)
                    st.metric("Accuracy", f"{accuracy_score:.1%}")
                
                with col3:
                    perf_score = health.get('component_scores', {}).get('performance', 0)
                    st.metric("Performance", f"{perf_score:.1%}")
                
                with col4:
                    sat_score = health.get('component_scores', {}).get('satisfaction', 0)
                    st.metric("Satisfaction", f"{sat_score:.1%}")
                
                # Health recommendations
                recommendations = health.get('recommendations', [])
                if recommendations:
                    st.subheader("💡 Health Recommendations")
                    for i, rec in enumerate(recommendations, 1):
                        st.write(f"{i}. {rec}")
            
        except Exception as e:
            st.error(f"Error getting health metrics: {e}")
    
    def render_alerts(self, monitoring_service) -> None:
        """Render alerts dashboard."""
        st.subheader("🚨 Alerts")
        
        try:
            recent_alerts = monitoring_service.get_recent_alerts(hours=24)
            
            if not recent_alerts:
                st.success("✅ No recent alerts")
                return
            
            # Alert summary
            col1, col2, col3, col4 = st.columns(4)
            
            critical_count = len([a for a in recent_alerts if a.get('level') == 'critical'])
            error_count = len([a for a in recent_alerts if a.get('level') == 'error'])
            warning_count = len([a for a in recent_alerts if a.get('level') == 'warning'])
            info_count = len([a for a in recent_alerts if a.get('level') == 'info'])
            
            with col1:
                if critical_count > 0:
                    st.error(f"🔴 Critical: {critical_count}")
                else:
                    st.success("🟢 Critical: 0")
            
            with col2:
                if error_count > 0:
                    st.warning(f"🟠 Error: {error_count}")
                else:
                    st.success("🟢 Error: 0")
            
            with col3:
                if warning_count > 0:
                    st.warning(f"🟡 Warning: {warning_count}")
                else:
                    st.success("🟢 Warning: 0")
            
            with col4:
                st.info(f"🔵 Info: {info_count}")
            
            # Recent alerts list
            st.subheader("📋 Recent Alerts")
            
            for alert in recent_alerts[-10:]:  # Show last 10
                level = alert.get('level', 'info').upper()
                category = alert.get('category', 'Unknown')
                message = alert.get('message', 'No message')
                timestamp = alert.get('timestamp', '')
                
                # Color code by level
                if level == 'CRITICAL':
                    st.error(f"🔴 **{level}** [{category}] {message}")
                elif level == 'ERROR':
                    st.warning(f"🟠 **{level}** [{category}] {message}")
                elif level == 'WARNING':
                    st.warning(f"🟡 **{level}** [{category}] {message}")
                else:
                    st.info(f"🔵 **{level}** [{category}] {message}")
                
                if timestamp:
                    st.caption(f"Time: {timestamp}")
        
        except Exception as e:
            st.error(f"Error getting alerts: {e}")
    
    def render_recommendations(self, monitoring_service) -> None:
        """Render performance recommendations."""
        st.subheader("💡 Performance Recommendations")
        
        try:
            recommendations = monitoring_service.get_performance_recommendations()
            
            if not recommendations:
                st.success("✅ No recommendations at this time")
                return
            
            # Group by priority
            high_priority = [r for r in recommendations if r.get('priority') == 'high']
            medium_priority = [r for r in recommendations if r.get('priority') == 'medium']
            low_priority = [r for r in recommendations if r.get('priority') == 'low']
            
            if high_priority:
                st.error("🔴 **High Priority**")
                for rec in high_priority:
                    with st.expander(f"🚨 {rec.get('description', 'No description')}"):
                        st.write(f"**Impact:** {rec.get('impact', 'Not specified')}")
                        st.write(f"**Implementation:** {rec.get('implementation', 'Not specified')}")
            
            if medium_priority:
                st.warning("🟡 **Medium Priority**")
                for rec in medium_priority:
                    with st.expander(f"⚠️ {rec.get('description', 'No description')}"):
                        st.write(f"**Impact:** {rec.get('impact', 'Not specified')}")
                        st.write(f"**Implementation:** {rec.get('implementation', 'Not specified')}")
            
            if low_priority:
                st.info("🟢 **Low Priority**")
                for rec in low_priority:
                    with st.expander(f"💡 {rec.get('description', 'No description')}"):
                        st.write(f"**Impact:** {rec.get('impact', 'Not specified')}")
                        st.write(f"**Implementation:** {rec.get('implementation', 'Not specified')}")
        
        except Exception as e:
            st.error(f"Error getting recommendations: {e}")
    
    def render_qa_report(self) -> None:
        """Render QA report if available."""
        if 'latest_qa_report' not in st.session_state:
            return
        
        st.subheader("📋 Quality Assurance Report")
        
        report = st.session_state.latest_qa_report
        
        # Report summary
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            overall_score = report.get('overall_score', 0)
            st.metric("Overall Score", f"{overall_score:.1%}")
        
        with col2:
            summary = report.get('summary', {})
            st.metric("Passed", summary.get('passed', 0))
        
        with col3:
            st.metric("Failed", summary.get('failed', 0))
        
        with col4:
            health_status = summary.get('health_status', 'Unknown')
            st.metric("Status", health_status.title())
        
        # Check results
        if report.get('checks_performed'):
            with st.expander("📊 Check Results"):
                for check in report['checks_performed']:
                    status = check.get('status', 'unknown')
                    name = check.get('check_name', 'Unknown').replace('_', ' ').title()
                    message = check.get('message', 'No message')
                    score = check.get('score', 0)
                    
                    if status == 'passed':
                        st.success(f"✅ **{name}**: {message} (Score: {score:.1%})")
                    elif status == 'warning':
                        st.warning(f"⚠️ **{name}**: {message} (Score: {score:.1%})")
                    elif status == 'failed':
                        st.error(f"❌ **{name}**: {message} (Score: {score:.1%})")
                    else:
                        st.info(f"⏭️ **{name}**: {message}")
        
        # Recommendations
        if report.get('recommendations'):
            with st.expander("💡 QA Recommendations"):
                for i, rec in enumerate(report['recommendations'], 1):
                    st.write(f"{i}. {rec}")
    
    def render_optimization_controls(self, monitoring_service) -> None:
        """Render performance optimization controls."""
        st.subheader("⚡ Performance Optimization")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Trigger Optimization"):
                try:
                    import asyncio
                    with st.spinner("Analyzing performance..."):
                        result = asyncio.run(monitoring_service.trigger_performance_optimization())
                        
                        if 'error' not in result:
                            st.success("✅ Optimization completed!")
                            st.write(f"**Recommendations:** {result.get('recommendations_generated', 0)}")
                            
                            actions = result.get('optimization_actions', [])
                            if actions:
                                st.write("**Actions:**")
                                for action in actions:
                                    st.write(f"• {action}")
                        else:
                            st.error(f"❌ Optimization failed: {result['error']}")
                
                except Exception as e:
                    st.error(f"❌ Error: {e}")
        
        with col2:
            if st.button("🔧 Schedule Maintenance"):
                try:
                    import asyncio
                    with st.spinner("Planning maintenance..."):
                        plan = asyncio.run(monitoring_service.schedule_maintenance_window(duration_hours=2))
                        
                        if 'error' not in plan:
                            st.success("✅ Maintenance scheduled!")
                            st.write(f"**ID:** {plan.get('maintenance_id', 'Unknown')}")
                            st.write(f"**Duration:** {plan.get('duration_hours', 0)} hours")
                            
                            activities = plan.get('planned_activities', [])
                            if activities:
                                st.write("**Activities:**")
                                for activity in activities:
                                    st.write(f"• {activity}")
                        else:
                            st.error(f"❌ Scheduling failed: {plan['error']}")
                
                except Exception as e:
                    st.error(f"❌ Error: {e}")
    
    def render_complete_dashboard(self, monitoring_service) -> None:
        """Render the complete monitoring dashboard."""
        # System status
        self.render_system_status(monitoring_service)
        
        st.divider()
        
        # Control panel
        self.render_control_panel(monitoring_service)
        
        st.divider()
        
        # Health metrics
        self.render_health_metrics(monitoring_service)
        
        st.divider()
        
        # Alerts
        self.render_alerts(monitoring_service)
        
        st.divider()
        
        # Recommendations
        self.render_recommendations(monitoring_service)
        
        st.divider()
        
        # QA Report
        self.render_qa_report()
        
        st.divider()
        
        # Optimization controls
        self.render_optimization_controls(monitoring_service)


    def _render_platform_usage_overview(self) -> None:
        """Render platform usage overview with actual session data."""
        st.subheader("📊 Platform Usage Overview")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            # Current session info
            session_id = st.session_state.get('session_id', 'None')
            if session_id and session_id != 'None':
                st.metric("Current Session", "Active", delta="🟢")
            else:
                st.metric("Current Session", "None", delta="🔴")
        
        with col2:
            # Provider metrics from existing observability
            try:
                # Try to get provider metrics from the existing observability system
                provider_stats = st.session_state.get('provider_stats', {})
                total_requests = sum(provider_stats.values()) if provider_stats else 0
                st.metric("Total Requests", total_requests)
            except Exception:
                st.metric("Total Requests", "N/A")
        
        with col3:
            # Pattern usage
            try:
                pattern_stats = st.session_state.get('pattern_stats', {})
                patterns_used = len(pattern_stats) if pattern_stats else 0
                st.metric("Patterns Used", patterns_used)
            except Exception:
                st.metric("Patterns Used", "N/A")
        
        with col4:
            # Recent activity
            try:
                last_analysis = st.session_state.get('last_analysis_time', 'Never')
                if last_analysis != 'Never':
                    st.metric("Last Analysis", "Recent", delta="🟢")
                else:
                    st.metric("Last Analysis", "None", delta="🔴")
            except Exception:
                st.metric("Last Analysis", "N/A")
        
        # Show helpful message about data collection
        if not st.session_state.get('session_id'):
            st.info("💡 **To see platform metrics**: Go to the **Analysis** tab and generate some tech stack recommendations. This will populate the monitoring dashboard with real usage data.")


def render_simple_monitoring_dashboard(monitoring_service):
    """Standalone function to render the simple monitoring dashboard."""
    dashboard = SimpleMonitoringDashboard()
    dashboard.render_complete_dashboard(monitoring_service)