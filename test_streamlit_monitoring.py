#!/usr/bin/env python3
"""
Test script to verify monitoring works in Streamlit context.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_monitoring_in_streamlit_context():
    """Test that monitoring can be initialized in Streamlit context."""
    print("🔍 Testing Monitoring in Streamlit Context")
    print("=" * 50)
    
    try:
        # Import the monitoring integration
        from app.monitoring.integration_service import MonitoringIntegrationService
        from app.monitoring.simple_dashboard import render_simple_monitoring_dashboard
        
        # Initialize the monitoring service (as Streamlit would)
        monitoring_service = MonitoringIntegrationService()
        print("✅ MonitoringIntegrationService initialized successfully")
        
        # Test getting monitoring status
        status = monitoring_service.get_monitoring_status()
        print(f"✅ Monitoring status: {status}")
        
        # Test getting performance recommendations
        recommendations = monitoring_service.get_performance_recommendations()
        print(f"✅ Performance recommendations: {len(recommendations)} items")
        
        # Test getting recent alerts
        alerts = monitoring_service.get_recent_alerts(hours=24)
        print(f"✅ Recent alerts: {len(alerts)} items")
        
        # Test getting real-time status
        real_time_status = monitoring_service.get_real_time_system_status()
        print(f"✅ Real-time status keys: {list(real_time_status.keys())}")
        
        print("\n🎉 Monitoring system is ready for Streamlit!")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_streamlit_usage_guide():
    """Show how to use the monitoring in Streamlit."""
    print("\n📋 Streamlit Usage Guide")
    print("=" * 50)
    
    guide = """
    The monitoring system is now integrated into your Streamlit app!
    
    🚀 To use it:
    
    1. Start Streamlit:
       streamlit run streamlit_app.py
    
    2. Navigate to: Observability → Real-time Monitoring
    
    3. Click "🚀 Start Monitoring" to activate
    
    4. Generate some tech stacks in the Analysis tab
    
    5. Return to monitoring to see live data!
    
    🎯 What you'll see:
    
    ✅ System Status - Green/red indicators for service health
    ✅ Control Panel - Start/stop monitoring, generate reports
    ✅ Health Metrics - Overall system health score and components
    ✅ Alert Dashboard - Real-time alerts with severity levels
    ✅ Performance Recommendations - AI-generated optimization tips
    ✅ QA Reports - Comprehensive quality analysis
    ✅ Optimization Controls - Performance tuning and maintenance
    
    🔄 Real-time Features:
    
    • Live accuracy tracking for tech stack generation
    • Automatic alerting for catalog issues
    • User satisfaction monitoring
    • Performance optimization recommendations
    • Quality assurance automation
    
    The monitoring system will automatically track:
    - Technology extraction accuracy
    - Processing times
    - User satisfaction scores
    - Catalog health metrics
    - System performance trends
    """
    
    print(guide)

if __name__ == "__main__":
    success = test_monitoring_in_streamlit_context()
    
    if success:
        show_streamlit_usage_guide()
        print("\n✅ Ready to use monitoring in Streamlit!")
    else:
        print("\n❌ Monitoring system needs attention before use.")
    
    exit(0 if success else 1)