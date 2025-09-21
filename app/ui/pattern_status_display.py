"""
Pattern Status Display Component

Provides UI components for displaying pattern enhancement and analytics status.
"""

import streamlit as st
from typing import Dict, Any, Optional
import logging

from app.utils.imports import optional_service


class PatternStatusDisplay:
    """UI component for displaying pattern system status."""
    
    def __init__(self):
        self.logger = logging.getLogger(__name__)
    
    def display_pattern_enhancement_status(self) -> None:
        """Display pattern enhancement service status."""
        try:
            # Try to get enhanced pattern loader service
            enhanced_loader = optional_service('enhanced_pattern_loader', context='PatternStatusDisplay')
            
            if enhanced_loader:
                # Service is available
                st.success("✅ Pattern enhancement available: Enhanced pattern system services are registered.")
                
                # Show additional info if available
                try:
                    if hasattr(enhanced_loader, 'get_analytics_summary'):
                        summary = enhanced_loader.get_analytics_summary()
                        if summary:
                            with st.expander("📊 Pattern Enhancement Details"):
                                col1, col2, col3 = st.columns(3)
                                with col1:
                                    st.metric("Total Patterns", summary.get('total_patterns', 0))
                                with col2:
                                    st.metric("Total Accesses", summary.get('total_accesses', 0))
                                with col3:
                                    cache_status = "Enabled" if summary.get('cache_enabled', False) else "Disabled"
                                    st.metric("Cache Status", cache_status)
                except Exception as e:
                    self.logger.debug(f"Could not get enhancement details: {e}")
            else:
                # Service not available - show helpful message
                st.info("💡 Pattern enhancement not available: Enhanced pattern system services are not registered. This feature requires the enhanced pattern system services to be registered.")
                
                with st.expander("ℹ️ How to enable pattern enhancement"):
                    st.markdown("""
                    **Pattern Enhancement Features:**
                    - Advanced pattern analytics
                    - Performance metrics
                    - Usage tracking
                    - Enhanced caching
                    
                    **To enable:**
                    1. Ensure enhanced pattern services are registered in the service registry
                    2. Restart the application
                    3. Check service health status
                    """)
                    
        except Exception as e:
            st.error(f"❌ Error checking pattern enhancement status: {str(e)}")
            self.logger.error(f"Error in pattern enhancement status display: {e}")
    
    def display_pattern_analytics_status(self) -> None:
        """Display pattern analytics service status."""
        try:
            # Try to get pattern analytics service
            analytics_service = optional_service('pattern_analytics_service', context='PatternStatusDisplay')
            
            if analytics_service:
                # Service is available
                st.success("✅ Pattern analytics available: Enhanced pattern analytics service is registered.")
                
                # Show analytics summary if available
                try:
                    if hasattr(analytics_service, 'get_real_time_metrics'):
                        metrics = analytics_service.get_real_time_metrics()
                        if metrics:
                            with st.expander("📈 Real-time Analytics"):
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.metric("Patterns Accessed", metrics.get('total_patterns_accessed', 0))
                                    st.metric("Success Rate", f"{metrics.get('success_rate', 0.0):.1%}")
                                with col2:
                                    st.metric("Avg Response Time", f"{metrics.get('average_response_time_ms', 0.0):.1f}ms")
                                    st.metric("Last Updated", metrics.get('last_updated', 'Never')[-8:] if metrics.get('last_updated') else 'Never')
                except Exception as e:
                    self.logger.debug(f"Could not get analytics details: {e}")
            else:
                # Service not available - show helpful message
                st.info("💡 Pattern analytics not available: Enhanced pattern loader service is not registered. This feature requires the enhanced pattern system services to be registered.")
                
                with st.expander("ℹ️ How to enable pattern analytics"):
                    st.markdown("""
                    **Pattern Analytics Features:**
                    - Real-time usage metrics
                    - Performance tracking
                    - Trend analysis
                    - Alert system
                    
                    **To enable:**
                    1. Ensure pattern analytics service is registered in the service registry
                    2. Restart the application
                    3. Check service health status
                    """)
                    
        except Exception as e:
            st.error(f"❌ Error checking pattern analytics status: {str(e)}")
            self.logger.error(f"Error in pattern analytics status display: {e}")
    
    def display_combined_status(self) -> None:
        """Display combined status for both pattern enhancement and analytics."""
        st.subheader("🔧 Pattern System Status")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("**Pattern Enhancement**")
            self.display_pattern_enhancement_status()
        
        with col2:
            st.markdown("**Pattern Analytics**")
            self.display_pattern_analytics_status()
    
    def display_service_health_check(self) -> Dict[str, bool]:
        """Display service health check results."""
        try:
            from app.core.registry import get_registry
            registry = get_registry()
            
            # Check pattern-related services
            pattern_services = {
                'pattern_loader': 'Basic Pattern Loader',
                'enhanced_pattern_loader': 'Enhanced Pattern Loader',
                'pattern_analytics_service': 'Pattern Analytics Service'
            }
            
            health_status = {}
            
            st.subheader("🏥 Service Health Check")
            
            for service_name, display_name in pattern_services.items():
                try:
                    if registry.has(service_name):
                        service = registry.get(service_name)
                        if hasattr(service, 'health_check'):
                            is_healthy = service.health_check()
                        else:
                            is_healthy = True  # Assume healthy if no health check method
                        
                        health_status[service_name] = is_healthy
                        
                        if is_healthy:
                            st.success(f"✅ {display_name}: Healthy")
                        else:
                            st.error(f"❌ {display_name}: Unhealthy")
                    else:
                        health_status[service_name] = False
                        st.warning(f"⚠️ {display_name}: Not registered")
                        
                except Exception as e:
                    health_status[service_name] = False
                    st.error(f"❌ {display_name}: Error - {str(e)}")
            
            return health_status
            
        except Exception as e:
            st.error(f"❌ Error performing health check: {str(e)}")
            return {}
    
    def display_pattern_usage_summary(self) -> None:
        """Display pattern usage summary if analytics are available."""
        try:
            analytics_service = optional_service('pattern_analytics_service', context='PatternStatusDisplay')
            
            if analytics_service and hasattr(analytics_service, 'get_usage_analytics'):
                st.subheader("📊 Pattern Usage Summary")
                
                # Get usage analytics for last 24 hours
                usage_data = analytics_service.get_usage_analytics(24)
                
                if usage_data and usage_data.get('total_events', 0) > 0:
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.metric("Total Events", usage_data.get('total_events', 0))
                    
                    with col2:
                        st.metric("Success Rate", f"{usage_data.get('success_rate', 0.0):.1%}")
                    
                    with col3:
                        st.metric("Avg Response Time", f"{usage_data.get('average_response_time_ms', 0.0):.1f}ms")
                    
                    with col4:
                        most_used = usage_data.get('most_used_patterns', [])
                        top_pattern = most_used[0][0] if most_used else "None"
                        st.metric("Top Pattern", top_pattern)
                    
                    # Show most used patterns
                    if usage_data.get('most_used_patterns'):
                        with st.expander("🏆 Most Used Patterns"):
                            for pattern_id, count in usage_data['most_used_patterns'][:5]:
                                st.write(f"• **{pattern_id}**: {count} uses")
                else:
                    st.info("No pattern usage data available for the last 24 hours.")
            else:
                st.info("Pattern usage summary requires pattern analytics service.")
                
        except Exception as e:
            st.error(f"Error displaying pattern usage summary: {str(e)}")
            self.logger.error(f"Error in pattern usage summary: {e}")


def display_pattern_system_status():
    """Convenience function to display pattern system status."""
    display = PatternStatusDisplay()
    display.display_combined_status()


def display_pattern_health_check():
    """Convenience function to display pattern service health check."""
    display = PatternStatusDisplay()
    return display.display_service_health_check()


def display_pattern_usage_dashboard():
    """Convenience function to display pattern usage dashboard."""
    display = PatternStatusDisplay()
    display.display_pattern_usage_summary()