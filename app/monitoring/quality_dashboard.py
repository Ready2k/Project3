"""
Quality Metrics Dashboard for Tech Stack Generation

Provides comprehensive visualization and reporting of quality metrics,
performance data, and system health indicators.
"""

import streamlit as st
from datetime import datetime
from typing import Dict, Any
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import pandas as pd

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


class QualityDashboard(ConfigurableService):
    """
    Interactive quality metrics dashboard for tech stack generation monitoring.

    Provides real-time visualization of system performance, quality metrics,
    alerts, and recommendations through a Streamlit interface.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, "QualityDashboard")
        self.logger = require_service("logger", context="QualityDashboard")
        self.monitor = optional_service(
            "tech_stack_monitor", context="QualityDashboard"
        )
        self.qa_system = optional_service(
            "quality_assurance_system", context="QualityDashboard"
        )

    def render_dashboard(self) -> None:
        """Render the complete quality metrics dashboard."""
        st.set_page_config(
            page_title="Tech Stack Quality Dashboard",
            page_icon="📊",
            layout="wide",
            initial_sidebar_state="expanded",
        )

        st.title("🔍 Tech Stack Generation Quality Dashboard")
        st.markdown(
            "Real-time monitoring and quality assurance for technology stack generation"
        )

        # Sidebar controls
        self._render_sidebar()

        # Check service availability
        if not self.monitor and not self.qa_system:
            st.error(
                "⚠️ Monitoring services are not available. Please check system configuration."
            )
            return

        # Main dashboard content
        self._render_overview()
        self._render_metrics_section()
        self._render_alerts_section()
        self._render_qa_section()
        self._render_recommendations_section()
        self._render_detailed_analytics()

    def _render_sidebar(self) -> None:
        """Render dashboard sidebar with controls."""
        st.sidebar.header("Dashboard Controls")

        # Time range selector
        time_ranges = {
            "Last Hour": 1,
            "Last 6 Hours": 6,
            "Last 24 Hours": 24,
            "Last 7 Days": 168,
            "Last 30 Days": 720,
        }

        selected_range = st.sidebar.selectbox(
            "Time Range",
            options=list(time_ranges.keys()),
            index=2,  # Default to 24 hours
        )

        st.session_state.time_window_hours = time_ranges[selected_range]

        # Auto-refresh toggle
        auto_refresh = st.sidebar.checkbox("Auto Refresh (30s)", value=True)
        if auto_refresh:
            st.rerun()

        # Manual refresh button
        if st.sidebar.button("🔄 Refresh Now"):
            st.rerun()

        # Export options
        st.sidebar.header("Export Options")

        if st.sidebar.button("📊 Export Metrics"):
            self._export_metrics()

        if st.sidebar.button("📋 Export QA Report"):
            self._export_qa_report()

        # System status
        st.sidebar.header("System Status")
        self._render_system_status()

    def _render_system_status(self) -> None:
        """Render system status indicators."""
        monitor_status = "🟢 Online" if self.monitor else "🔴 Offline"
        qa_status = "🟢 Online" if self.qa_system else "🔴 Offline"

        st.sidebar.markdown(f"**Monitor Service:** {monitor_status}")
        st.sidebar.markdown(f"**QA System:** {qa_status}")

        if self.monitor:
            st.sidebar.markdown(
                f"**Monitoring:** {'🟢 Active' if self.monitor.monitoring_active else '🟡 Inactive'}"
            )

        if self.qa_system:
            st.sidebar.markdown(
                f"**QA Checks:** {'🟢 Active' if self.qa_system.qa_enabled else '🟡 Inactive'}"
            )

    def _render_overview(self) -> None:
        """Render dashboard overview section."""
        st.header("📈 System Overview")

        # Get dashboard data
        dashboard_data = self._get_dashboard_data()

        if not dashboard_data:
            st.warning("No data available for the selected time range.")
            return

        # Overview metrics
        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric(
                "Total Sessions",
                dashboard_data.get("summary", {}).get("total_sessions", 0),
                help="Number of tech stack generation sessions",
            )

        with col2:
            accuracy = dashboard_data.get("accuracy", {}).get("average", 0)
            trend = dashboard_data.get("accuracy", {}).get("trend", "stable")
            delta_color = (
                "normal"
                if trend == "improving"
                else "inverse" if trend == "declining" else None
            )

            st.metric(
                "Avg Accuracy",
                f"{accuracy:.1%}",
                delta=trend.title(),
                delta_color=delta_color,
                help="Average technology extraction accuracy",
            )

        with col3:
            perf_time = dashboard_data.get("performance", {}).get("average_time", 0)
            perf_trend = dashboard_data.get("performance", {}).get("trend", "stable")
            delta_color = (
                "normal"
                if perf_trend == "improving"
                else "inverse" if perf_trend == "declining" else None
            )

            st.metric(
                "Avg Response Time",
                f"{perf_time:.1f}s",
                delta=perf_trend.title(),
                delta_color=delta_color,
                help="Average processing time for tech stack generation",
            )

        with col4:
            satisfaction = dashboard_data.get("satisfaction", {}).get("average", 0)
            sat_trend = dashboard_data.get("satisfaction", {}).get("trend", "stable")
            delta_color = (
                "normal"
                if sat_trend == "improving"
                else "inverse" if sat_trend == "declining" else None
            )

            st.metric(
                "User Satisfaction",
                f"{satisfaction:.1f}/5",
                delta=sat_trend.title(),
                delta_color=delta_color,
                help="Average user satisfaction rating",
            )

    def _render_metrics_section(self) -> None:
        """Render detailed metrics visualization."""
        st.header("📊 Detailed Metrics")

        dashboard_data = self._get_dashboard_data()
        if not dashboard_data:
            return

        # Metrics over time
        hourly_data = dashboard_data.get("metrics_by_hour", {})
        if hourly_data:
            self._render_metrics_charts(hourly_data)

        # Metric distribution
        col1, col2 = st.columns(2)

        with col1:
            self._render_accuracy_breakdown(dashboard_data)

        with col2:
            self._render_performance_breakdown(dashboard_data)

    def _render_metrics_charts(self, hourly_data: Dict[str, Dict[str, float]]) -> None:
        """Render time-series charts for metrics."""
        if not hourly_data:
            return

        # Prepare data for plotting
        df_data = []
        for hour, metrics in hourly_data.items():
            for metric_name, value in metrics.items():
                df_data.append({"hour": hour, "metric": metric_name, "value": value})

        if not df_data:
            return

        df = pd.DataFrame(df_data)
        df["hour"] = pd.to_datetime(df["hour"])

        # Create subplots for different metric types
        fig = make_subplots(
            rows=2,
            cols=2,
            subplot_titles=(
                "Accuracy Metrics",
                "Performance Metrics",
                "Satisfaction Metrics",
                "Catalog Metrics",
            ),
            specs=[
                [{"secondary_y": False}, {"secondary_y": False}],
                [{"secondary_y": False}, {"secondary_y": False}],
            ],
        )

        # Accuracy metrics
        accuracy_metrics = df[
            df["metric"].str.contains("accuracy|inclusion", case=False, na=False)
        ]
        if not accuracy_metrics.empty:
            for metric in accuracy_metrics["metric"].unique():
                metric_data = accuracy_metrics[accuracy_metrics["metric"] == metric]
                fig.add_trace(
                    go.Scatter(
                        x=metric_data["hour"],
                        y=metric_data["value"],
                        name=metric,
                        mode="lines+markers",
                    ),
                    row=1,
                    col=1,
                )

        # Performance metrics
        perf_metrics = df[
            df["metric"].str.contains("time|performance", case=False, na=False)
        ]
        if not perf_metrics.empty:
            for metric in perf_metrics["metric"].unique():
                metric_data = perf_metrics[perf_metrics["metric"] == metric]
                fig.add_trace(
                    go.Scatter(
                        x=metric_data["hour"],
                        y=metric_data["value"],
                        name=metric,
                        mode="lines+markers",
                    ),
                    row=1,
                    col=2,
                )

        # Satisfaction metrics
        sat_metrics = df[
            df["metric"].str.contains("satisfaction", case=False, na=False)
        ]
        if not sat_metrics.empty:
            for metric in sat_metrics["metric"].unique():
                metric_data = sat_metrics[sat_metrics["metric"] == metric]
                fig.add_trace(
                    go.Scatter(
                        x=metric_data["hour"],
                        y=metric_data["value"],
                        name=metric,
                        mode="lines+markers",
                    ),
                    row=2,
                    col=1,
                )

        # Catalog metrics
        catalog_metrics = df[df["metric"].str.contains("catalog", case=False, na=False)]
        if not catalog_metrics.empty:
            for metric in catalog_metrics["metric"].unique():
                metric_data = catalog_metrics[catalog_metrics["metric"] == metric]
                fig.add_trace(
                    go.Scatter(
                        x=metric_data["hour"],
                        y=metric_data["value"],
                        name=metric,
                        mode="lines+markers",
                    ),
                    row=2,
                    col=2,
                )

        fig.update_layout(height=600, showlegend=True, title_text="Metrics Over Time")
        st.plotly_chart(fig, width="content")

    def _render_accuracy_breakdown(self, dashboard_data: Dict[str, Any]) -> None:
        """Render accuracy metrics breakdown."""
        st.subheader("🎯 Accuracy Breakdown")

        accuracy_data = dashboard_data.get("accuracy", {})
        if not accuracy_data:
            st.info("No accuracy data available")
            return

        # Create gauge chart for accuracy
        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=accuracy_data.get("average", 0) * 100,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Extraction Accuracy (%)"},
                delta={"reference": 85},
                gauge={
                    "axis": {"range": [None, 100]},
                    "bar": {"color": "darkblue"},
                    "steps": [
                        {"range": [0, 70], "color": "lightgray"},
                        {"range": [70, 85], "color": "yellow"},
                        {"range": [85, 100], "color": "green"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 85,
                    },
                },
            )
        )

        fig.update_layout(height=300)
        st.plotly_chart(fig, width="content")

        # Accuracy details
        st.markdown(f"**Samples:** {accuracy_data.get('samples', 0)}")
        st.markdown(f"**Trend:** {accuracy_data.get('trend', 'Unknown').title()}")

    def _render_performance_breakdown(self, dashboard_data: Dict[str, Any]) -> None:
        """Render performance metrics breakdown."""
        st.subheader("⚡ Performance Breakdown")

        performance_data = dashboard_data.get("performance", {})
        if not performance_data:
            st.info("No performance data available")
            return

        # Create performance gauge
        avg_time = performance_data.get("average_time", 0)
        max_time = performance_data.get("max_time", 0)

        fig = go.Figure(
            go.Indicator(
                mode="gauge+number+delta",
                value=avg_time,
                domain={"x": [0, 1], "y": [0, 1]},
                title={"text": "Avg Response Time (s)"},
                delta={"reference": 15},
                gauge={
                    "axis": {"range": [None, 60]},
                    "bar": {"color": "darkgreen"},
                    "steps": [
                        {"range": [0, 15], "color": "green"},
                        {"range": [15, 30], "color": "yellow"},
                        {"range": [30, 60], "color": "red"},
                    ],
                    "threshold": {
                        "line": {"color": "red", "width": 4},
                        "thickness": 0.75,
                        "value": 30,
                    },
                },
            )
        )

        fig.update_layout(height=300)
        st.plotly_chart(fig, width="content")

        # Performance details
        st.markdown(f"**Max Time:** {max_time:.1f}s")
        st.markdown(f"**Samples:** {performance_data.get('samples', 0)}")
        st.markdown(f"**Trend:** {performance_data.get('trend', 'Unknown').title()}")

    def _render_alerts_section(self) -> None:
        """Render alerts and notifications section."""
        st.header("🚨 Alerts & Notifications")

        dashboard_data = self._get_dashboard_data()
        alerts = dashboard_data.get("alerts", [])

        if not alerts:
            st.success("✅ No recent alerts")
            return

        # Alert summary
        col1, col2, col3 = st.columns(3)

        critical_alerts = [a for a in alerts if a.get("level") == "critical"]
        error_alerts = [a for a in alerts if a.get("level") == "error"]
        warning_alerts = [a for a in alerts if a.get("level") == "warning"]

        with col1:
            st.metric("Critical", len(critical_alerts), help="Critical system alerts")

        with col2:
            st.metric("Errors", len(error_alerts), help="Error-level alerts")

        with col3:
            st.metric("Warnings", len(warning_alerts), help="Warning-level alerts")

        # Recent alerts table
        st.subheader("Recent Alerts")

        alert_data = []
        for alert in alerts[-10:]:  # Show last 10 alerts
            alert_data.append(
                {
                    "Timestamp": alert.get("timestamp", ""),
                    "Level": alert.get("level", "").upper(),
                    "Category": alert.get("category", ""),
                    "Message": alert.get("message", ""),
                    "Session ID": alert.get("session_id", "N/A"),
                }
            )

        if alert_data:
            df_alerts = pd.DataFrame(alert_data)

            # Color code by level
            def color_level(val):
                if val == "CRITICAL":
                    return "background-color: #ffebee"
                elif val == "ERROR":
                    return "background-color: #fff3e0"
                elif val == "WARNING":
                    return "background-color: #f3e5f5"
                return ""

            styled_df = df_alerts.style.applymap(color_level, subset=["Level"])
            st.dataframe(styled_df, use_container_width=True)

    def _render_qa_section(self) -> None:
        """Render quality assurance section."""
        st.header("🔍 Quality Assurance")

        if not self.qa_system:
            st.warning("Quality Assurance system is not available")
            return

        # Get latest QA report
        latest_report = self.qa_system.get_latest_report()

        if not latest_report:
            st.info("No QA reports available")
            return

        # QA summary
        summary = latest_report.summary

        col1, col2, col3, col4 = st.columns(4)

        with col1:
            st.metric("Overall Score", f"{latest_report.overall_score:.1%}")

        with col2:
            st.metric("Passed Checks", summary.get("passed", 0))

        with col3:
            st.metric("Failed Checks", summary.get("failed", 0))

        with col4:
            health_status = summary.get("health_status", "unknown")
            health_emoji = {
                "excellent": "🟢",
                "good": "🟡",
                "fair": "🟠",
                "poor": "🔴",
                "critical": "🚨",
            }.get(health_status, "❓")

            st.metric("Health Status", f"{health_emoji} {health_status.title()}")

        # QA check results
        st.subheader("Quality Check Results")

        check_data = []
        for result in latest_report.check_results:
            status_emoji = {
                "passed": "✅",
                "warning": "⚠️",
                "failed": "❌",
                "skipped": "⏭️",
            }.get(result.status.value, "❓")

            check_data.append(
                {
                    "Check": result.check_name.replace("_", " ").title(),
                    "Status": f"{status_emoji} {result.status.value.title()}",
                    "Score": f"{result.score:.1%}" if result.score > 0 else "N/A",
                    "Message": result.message,
                }
            )

        if check_data:
            df_checks = pd.DataFrame(check_data)
            st.dataframe(df_checks, use_container_width=True)

        # QA report timestamp
        st.caption(
            f"Report generated: {latest_report.timestamp.strftime('%Y-%m-%d %H:%M:%S')}"
        )

    def _render_recommendations_section(self) -> None:
        """Render recommendations section."""
        st.header("💡 Recommendations")

        dashboard_data = self._get_dashboard_data()
        recommendations = dashboard_data.get("recommendations", [])

        # Get QA recommendations
        if self.qa_system:
            latest_report = self.qa_system.get_latest_report()
            if latest_report:
                recommendations.extend(latest_report.recommendations)

        if not recommendations:
            st.success("✅ No recommendations at this time")
            return

        # Group recommendations by priority/category
        high_priority = []
        medium_priority = []
        low_priority = []

        for rec in recommendations:
            if isinstance(rec, dict):
                priority = rec.get("priority", "medium")
                if priority == "high":
                    high_priority.append(rec)
                elif priority == "low":
                    low_priority.append(rec)
                else:
                    medium_priority.append(rec)
            else:
                # String recommendations (from QA system)
                medium_priority.append({"description": rec, "priority": "medium"})

        # Display recommendations by priority
        if high_priority:
            st.subheader("🔴 High Priority")
            for rec in high_priority:
                with st.expander(f"🚨 {rec.get('description', rec)}"):
                    if isinstance(rec, dict) and "implementation" in rec:
                        st.markdown(f"**Impact:** {rec.get('impact', 'Not specified')}")
                        st.markdown(
                            f"**Implementation:** {rec.get('implementation', 'Not specified')}"
                        )

        if medium_priority:
            st.subheader("🟡 Medium Priority")
            for rec in medium_priority:
                desc = rec.get("description", rec) if isinstance(rec, dict) else rec
                with st.expander(f"⚠️ {desc}"):
                    if isinstance(rec, dict):
                        if "impact" in rec:
                            st.markdown(
                                f"**Impact:** {rec.get('impact', 'Not specified')}"
                            )
                        if "implementation" in rec:
                            st.markdown(
                                f"**Implementation:** {rec.get('implementation', 'Not specified')}"
                            )

        if low_priority:
            st.subheader("🟢 Low Priority")
            for rec in low_priority:
                with st.expander(f"💡 {rec.get('description', rec)}"):
                    if isinstance(rec, dict) and "implementation" in rec:
                        st.markdown(f"**Impact:** {rec.get('impact', 'Not specified')}")
                        st.markdown(
                            f"**Implementation:** {rec.get('implementation', 'Not specified')}"
                        )

    def _render_detailed_analytics(self) -> None:
        """Render detailed analytics section."""
        st.header("📈 Detailed Analytics")

        # Add tabs for different analytics views
        tab1, tab2, tab3 = st.tabs(["Trends", "Distributions", "Correlations"])

        with tab1:
            self._render_trend_analysis()

        with tab2:
            self._render_distribution_analysis()

        with tab3:
            self._render_correlation_analysis()

    def _render_trend_analysis(self) -> None:
        """Render trend analysis charts."""
        st.subheader("📊 Trend Analysis")

        dashboard_data = self._get_dashboard_data()
        hourly_data = dashboard_data.get("metrics_by_hour", {})

        if not hourly_data:
            st.info("No trend data available")
            return

        # Convert to DataFrame for easier analysis
        trend_data = []
        for hour, metrics in hourly_data.items():
            row = {"hour": hour}
            row.update(metrics)
            trend_data.append(row)

        if not trend_data:
            return

        df = pd.DataFrame(trend_data)
        df["hour"] = pd.to_datetime(df["hour"])
        df = df.sort_values("hour")

        # Select metrics to display
        metric_columns = [col for col in df.columns if col != "hour"]
        selected_metrics = st.multiselect(
            "Select metrics to display:",
            options=metric_columns,
            default=metric_columns[:3] if len(metric_columns) >= 3 else metric_columns,
        )

        if selected_metrics:
            fig = go.Figure()

            for metric in selected_metrics:
                if metric in df.columns:
                    fig.add_trace(
                        go.Scatter(
                            x=df["hour"],
                            y=df[metric],
                            mode="lines+markers",
                            name=metric.replace("_", " ").title(),
                        )
                    )

            fig.update_layout(
                title="Metric Trends Over Time",
                xaxis_title="Time",
                yaxis_title="Value",
                height=400,
            )

            st.plotly_chart(fig, width="content")

    def _render_distribution_analysis(self) -> None:
        """Render distribution analysis charts."""
        st.subheader("📊 Distribution Analysis")
        st.info(
            "Distribution analysis will be implemented with more detailed metric data"
        )

    def _render_correlation_analysis(self) -> None:
        """Render correlation analysis charts."""
        st.subheader("📊 Correlation Analysis")
        st.info(
            "Correlation analysis will be implemented with more detailed metric data"
        )

    def _get_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data."""
        if not self.monitor:
            return {}

        try:
            return self.monitor.get_quality_dashboard_data()
        except Exception as e:
            self.logger.error(f"Error getting dashboard data: {e}")
            return {}

    def _export_metrics(self) -> None:
        """Export metrics data."""
        if not self.monitor:
            st.error("Monitor service not available")
            return

        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"exports/tech_stack_metrics_{timestamp}.json"

            self.monitor.export_metrics(
                filepath, st.session_state.get("time_window_hours", 24)
            )
            st.success(f"✅ Metrics exported to {filepath}")

        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")

    def _export_qa_report(self) -> None:
        """Export QA report."""
        if not self.qa_system:
            st.error("QA system not available")
            return

        try:
            latest_report = self.qa_system.get_latest_report()
            if not latest_report:
                st.error("No QA report available")
                return

            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filepath = f"exports/qa_report_{timestamp}.json"

            self.qa_system.export_report(latest_report, filepath)
            st.success(f"✅ QA report exported to {filepath}")

        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")


def render_quality_dashboard():
    """Render the quality dashboard (standalone function for Streamlit)."""
    dashboard = QualityDashboard()
    dashboard.render_dashboard()
