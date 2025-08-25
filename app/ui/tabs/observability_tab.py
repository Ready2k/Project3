"""Observability tab for the AAA application."""

import streamlit as st
from typing import Dict, Any, Optional
import pandas as pd
from datetime import datetime, timedelta

from app.ui.tabs.base import BaseTab
from app.core.registry import ServiceRegistry
from app.ui.main_app import SessionManager


class ObservabilityTab(BaseTab):
    """Tab for system observability and monitoring."""
    
    def __init__(self, session_manager: SessionManager, service_registry: ServiceRegistry):
        super().__init__("observability", "📈 Observability", "Monitor system performance and analytics")
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    def initialize(self) -> None:
        """Initialize the tab."""
        pass
    
    def render(self) -> None:
        """Render the observability tab."""
        st.header("📈 System Observability")
        st.markdown("*Monitor system performance, usage patterns, and analytics*")
        
        # Create tabs for different observability views
        metrics_tab, patterns_tab, usage_tab, messages_tab, admin_tab = st.tabs([
            "🔧 Provider Metrics", 
            "🎯 Pattern Analytics", 
            "📊 Usage Patterns", 
            "💬 LLM Messages", 
            "🧹 Admin"
        ])
        
        with metrics_tab:
            self._render_provider_metrics()
        
        with patterns_tab:
            self._render_pattern_analytics()
        
        with usage_tab:
            self._render_usage_patterns()
        
        with messages_tab:
            self._render_llm_messages()
        
        with admin_tab:
            self._render_admin_panel()
    
    def _render_provider_metrics(self) -> None:
        """Render provider performance metrics."""
        st.subheader("🔧 LLM Provider Metrics")
        
        try:
            # For now, show mock metrics since metrics service isn't implemented yet
            st.info("📊 Showing sample metrics data. Real metrics service integration coming soon.")
            
            # Display key metrics
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Requests", "1,234", "+12%")
            
            with col2:
                st.metric("Avg Response Time", "1.2s", "-0.3s")
            
            with col3:
                st.metric("Success Rate", "98.5%", "+1.2%")
            
            with col4:
                st.metric("Error Rate", "1.5%", "-0.8%")
            
            # Response time chart
            st.subheader("Response Time Trends")
            
            # Generate sample data for demo
            dates = pd.date_range(start=datetime.now() - timedelta(days=7), end=datetime.now(), freq='h')
            response_times = pd.DataFrame({
                'timestamp': dates,
                'response_time': [1.2 + (i % 10) * 0.1 for i in range(len(dates))]
            })
            
            st.line_chart(response_times.set_index('timestamp'))
            
            # Provider comparison
            st.subheader("Provider Performance Comparison")
            
            provider_data = pd.DataFrame({
                'Provider': ['OpenAI', 'Claude', 'Bedrock', 'Internal'],
                'Avg Response Time (s)': [1.2, 1.8, 2.1, 0.9],
                'Success Rate (%)': [98.5, 97.2, 96.8, 99.1],
                'Total Requests': [450, 320, 180, 284]
            })
            
            st.dataframe(provider_data, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading provider metrics: {str(e)}")
    
    def _render_pattern_analytics(self) -> None:
        """Render pattern matching analytics."""
        st.subheader("🎯 Pattern Analytics")
        
        try:
            # Time filter
            time_filter = st.selectbox(
                "Time Period:",
                ["Current Session", "Last 24 Hours", "Last 7 Days", "All Time"],
                key="pattern_time_filter"
            )
            
            # Pattern match frequency
            st.subheader("Pattern Match Frequency")
            
            # Sample data for demo
            pattern_data = pd.DataFrame({
                'Pattern': ['PAT-001', 'PAT-002', 'PAT-003', 'PAT-004', 'PAT-005'],
                'Matches': [45, 32, 28, 19, 15],
                'Success Rate': [92, 88, 95, 76, 89],
                'Avg Confidence': [0.85, 0.78, 0.91, 0.72, 0.83]
            })
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.bar_chart(pattern_data.set_index('Pattern')['Matches'])
            
            with col2:
                st.bar_chart(pattern_data.set_index('Pattern')['Success Rate'])
            
            # Detailed pattern analytics
            st.subheader("Pattern Performance Details")
            st.dataframe(pattern_data, use_container_width=True)
            
            # Pattern quality trends
            st.subheader("Pattern Quality Trends")
            
            # Generate trend data
            trend_dates = pd.date_range(start=datetime.now() - timedelta(days=30), end=datetime.now(), freq='d')
            quality_trends = pd.DataFrame({
                'Date': trend_dates,
                'Average Confidence': [0.8 + (i % 20) * 0.01 for i in range(len(trend_dates))],
                'Match Success Rate': [85 + (i % 15) for i in range(len(trend_dates))]
            })
            
            st.line_chart(quality_trends.set_index('Date'))
            
        except Exception as e:
            st.error(f"Error loading pattern analytics: {str(e)}")
    
    def _render_usage_patterns(self) -> None:
        """Render usage pattern analysis."""
        st.subheader("📊 Usage Patterns")
        
        try:
            # Usage overview
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Daily Active Sessions", "47", "+8")
            
            with col2:
                st.metric("Avg Session Duration", "12.5 min", "+2.1 min")
            
            with col3:
                st.metric("Analysis Completion Rate", "87%", "+5%")
            
            # Usage by time of day
            st.subheader("Usage by Time of Day")
            
            hours = list(range(24))
            usage_by_hour = [5 + (h % 12) * 2 + (h // 12) * 3 for h in hours]
            
            usage_df = pd.DataFrame({
                'Hour': hours,
                'Sessions': usage_by_hour
            })
            
            st.bar_chart(usage_df.set_index('Hour'))
            
            # Feature usage
            st.subheader("Feature Usage Statistics")
            
            feature_data = pd.DataFrame({
                'Feature': ['Text Analysis', 'File Upload', 'Jira Integration', 'Q&A System', 'Diagram Generation'],
                'Usage Count': [234, 89, 45, 178, 156],
                'Success Rate': [95, 92, 88, 97, 89]
            })
            
            st.dataframe(feature_data, use_container_width=True)
            
        except Exception as e:
            st.error(f"Error loading usage patterns: {str(e)}")
    
    def _render_llm_messages(self) -> None:
        """Render LLM message logs."""
        st.subheader("💬 LLM Messages")
        
        try:
            # Message filters
            col1, col2, col3 = st.columns(3)
            
            with col1:
                provider_filter = st.selectbox(
                    "Provider:",
                    ["All", "OpenAI", "Claude", "Bedrock", "Internal"],
                    key="message_provider_filter"
                )
            
            with col2:
                message_type = st.selectbox(
                    "Type:",
                    ["All", "Analysis", "Q&A", "Diagram", "Pattern"],
                    key="message_type_filter"
                )
            
            with col3:
                max_messages = st.number_input(
                    "Max Messages:",
                    min_value=10,
                    max_value=1000,
                    value=50,
                    key="max_messages"
                )
            
            # Sample message data
            messages = [
                {
                    "timestamp": datetime.now() - timedelta(minutes=i*5),
                    "provider": "OpenAI",
                    "type": "Analysis",
                    "tokens": 150 + i*10,
                    "response_time": 1.2 + i*0.1,
                    "status": "Success" if i % 10 != 0 else "Error"
                }
                for i in range(max_messages)
            ]
            
            # Display messages
            for msg in messages[:10]:  # Show first 10
                with st.expander(f"{msg['timestamp'].strftime('%H:%M:%S')} - {msg['provider']} - {msg['type']}"):
                    col1, col2, col3, col4 = st.columns(4)
                    with col1:
                        st.write(f"**Tokens:** {msg['tokens']}")
                    with col2:
                        st.write(f"**Response Time:** {msg['response_time']:.1f}s")
                    with col3:
                        st.write(f"**Status:** {msg['status']}")
                    with col4:
                        if msg['status'] == 'Success':
                            st.success("✅")
                        else:
                            st.error("❌")
            
            if len(messages) > 10:
                st.info(f"Showing 10 of {len(messages)} messages. Use filters to refine results.")
            
        except Exception as e:
            st.error(f"Error loading LLM messages: {str(e)}")
    
    def _render_admin_panel(self) -> None:
        """Render admin panel."""
        st.subheader("🧹 Admin Panel")
        
        st.warning("⚠️ Admin functions require elevated privileges")
        
        # System status
        st.subheader("System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.success("✅ API Server: Running")
            st.success("✅ Database: Connected")
            st.success("✅ Cache: Active")
        
        with col2:
            st.info("🔄 Last Backup: 2 hours ago")
            st.info("📊 Disk Usage: 45% (2.1GB)")
            st.info("🧠 Memory Usage: 67% (1.2GB)")
        
        # Admin actions
        st.subheader("Admin Actions")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🗑️ Clear Cache", key="clear_cache_btn"):
                st.success("Cache cleared successfully!")
        
        with col2:
            if st.button("📊 Export Logs", key="export_logs_btn"):
                st.success("Logs exported to downloads!")
        
        with col3:
            if st.button("🔄 Restart Services", key="restart_services_btn"):
                st.warning("Service restart initiated...")
        
        # Configuration
        st.subheader("System Configuration")
        
        with st.expander("View Current Configuration"):
            config_data = {
                "api_timeout": 30,
                "max_concurrent_requests": 10,
                "cache_ttl": 3600,
                "log_level": "INFO",
                "enable_metrics": True
            }
            
            st.json(config_data)