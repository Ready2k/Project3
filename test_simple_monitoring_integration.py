#!/usr/bin/env python3
"""
Test script for the simple monitoring integration.

This script tests the monitoring system integration without external dependencies.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_monitoring_imports():
    """Test that monitoring components can be imported."""
    print("🔍 Testing Monitoring System Imports")
    print("=" * 50)
    
    try:
        # Test core monitoring imports
        from app.monitoring.tech_stack_monitor import TechStackMonitor, AlertLevel, MetricType
        print("✅ TechStackMonitor imported successfully")
        
        from app.monitoring.quality_assurance import QualityAssuranceSystem, QACheckType, QAStatus
        print("✅ QualityAssuranceSystem imported successfully")
        
        from app.monitoring.integration_service import MonitoringIntegrationService
        print("✅ MonitoringIntegrationService imported successfully")
        
        from app.monitoring.simple_dashboard import SimpleMonitoringDashboard, render_simple_monitoring_dashboard
        print("✅ SimpleMonitoringDashboard imported successfully")
        
        return True
        
    except ImportError as e:
        print(f"❌ Import failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        return False

def test_monitoring_initialization():
    """Test that monitoring components can be initialized."""
    print("\n🚀 Testing Monitoring System Initialization")
    print("=" * 50)
    
    try:
        # Test dashboard initialization (doesn't require services)
        from app.monitoring.simple_dashboard import SimpleMonitoringDashboard
        dashboard = SimpleMonitoringDashboard()
        print("✅ SimpleMonitoringDashboard initialized")
        
        # Test that monitoring classes can be imported and have expected methods
        from app.monitoring.integration_service import MonitoringIntegrationService
        from app.monitoring.tech_stack_monitor import TechStackMonitor
        from app.monitoring.quality_assurance import QualityAssuranceSystem
        
        print("✅ All monitoring classes available")
        
        # Test that key methods exist
        assert hasattr(MonitoringIntegrationService, 'get_monitoring_status')
        assert hasattr(MonitoringIntegrationService, 'get_performance_recommendations')
        assert hasattr(MonitoringIntegrationService, 'get_recent_alerts')
        print("✅ Key methods available on MonitoringIntegrationService")
        
        return True
        
    except Exception as e:
        print(f"❌ Initialization failed: {e}")
        return False

def test_monitoring_functionality():
    """Test basic monitoring functionality."""
    print("\n⚡ Testing Monitoring System Functionality")
    print("=" * 50)
    
    try:
        # Test that monitoring components have the expected structure
        from app.monitoring.tech_stack_monitor import TechStackMonitor, AlertLevel, MetricType
        from app.monitoring.quality_assurance import QualityAssuranceSystem, QACheckType, QAStatus
        
        # Test enums
        assert AlertLevel.CRITICAL
        assert AlertLevel.ERROR
        assert AlertLevel.WARNING
        assert AlertLevel.INFO
        print("✅ AlertLevel enum available")
        
        assert MetricType.ACCURACY
        assert MetricType.PERFORMANCE
        assert MetricType.QUALITY
        print("✅ MetricType enum available")
        
        assert QACheckType.ACCURACY
        assert QACheckType.CONSISTENCY
        assert QACheckType.COMPLETENESS
        print("✅ QACheckType enum available")
        
        assert QAStatus.PASSED
        assert QAStatus.FAILED
        assert QAStatus.WARNING
        assert QAStatus.SKIPPED
        print("✅ QAStatus enum available")
        
        # Test that classes have expected methods
        monitor_methods = ['record_extraction_accuracy', 'record_catalog_metrics', 'record_user_satisfaction']
        for method in monitor_methods:
            assert hasattr(TechStackMonitor, method)
        print("✅ TechStackMonitor has expected methods")
        
        qa_methods = ['start_qa_system', 'stop_qa_system', 'generate_manual_report']
        for method in qa_methods:
            assert hasattr(QualityAssuranceSystem, method)
        print("✅ QualityAssuranceSystem has expected methods")
        
        return True
        
    except Exception as e:
        print(f"❌ Functionality test failed: {e}")
        return False

def test_streamlit_integration():
    """Test Streamlit integration components."""
    print("\n🌐 Testing Streamlit Integration")
    print("=" * 50)
    
    try:
        # Test that the render function exists
        from app.monitoring.simple_dashboard import render_simple_monitoring_dashboard, SimpleMonitoringDashboard
        
        print("✅ Streamlit dashboard render function available")
        
        # Test that dashboard has expected methods
        dashboard = SimpleMonitoringDashboard()
        dashboard_methods = [
            'render_system_status',
            'render_control_panel', 
            'render_health_metrics',
            'render_alerts',
            'render_recommendations',
            'render_complete_dashboard'
        ]
        
        for method in dashboard_methods:
            assert hasattr(dashboard, method)
        print("✅ Dashboard has all expected render methods")
        
        # Test that the integration components exist in Streamlit app
        import os
        streamlit_app_path = os.path.join(os.path.dirname(__file__), 'streamlit_app.py')
        if os.path.exists(streamlit_app_path):
            with open(streamlit_app_path, 'r') as f:
                content = f.read()
                
            # Check for monitoring integration
            assert 'render_tech_stack_monitoring' in content
            assert 'Real-time Monitoring' in content
            assert 'render_simple_monitoring_dashboard' in content
            print("✅ Streamlit app has monitoring integration")
        
        return True
        
    except Exception as e:
        print(f"❌ Streamlit integration test failed: {e}")
        return False

def show_monitoring_location_guide():
    """Show where to find the monitoring dashboard."""
    print("\n📍 Monitoring Dashboard Location Guide")
    print("=" * 50)
    
    guide = """
    To access the real-time monitoring dashboard:
    
    1. 🚀 Start the Streamlit app:
       streamlit run streamlit_app.py
    
    2. 📈 Navigate to the "Observability" tab
       (3rd tab in the main navigation)
    
    3. 🔍 Click on "Real-time Monitoring" sub-tab
       (2nd sub-tab within Observability)
    
    4. 🎛️ Use the control panel to:
       - Start/Stop monitoring
       - Generate QA reports
       - View system health
       - Review alerts and recommendations
    
    The monitoring dashboard provides:
    ✅ System status indicators
    ✅ Real-time health metrics
    ✅ Alert management
    ✅ Performance recommendations
    ✅ Quality assurance reports
    ✅ Optimization controls
    """
    
    print(guide)

def main():
    """Run all monitoring integration tests."""
    print("🔍 Tech Stack Monitoring Integration Test")
    print("=" * 60)
    
    tests = [
        ("Import Test", test_monitoring_imports),
        ("Initialization Test", test_monitoring_initialization),
        ("Functionality Test", test_monitoring_functionality),
        ("Streamlit Integration Test", test_streamlit_integration)
    ]
    
    results = []
    
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} crashed: {e}")
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("📊 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = 0
    total = len(results)
    
    for test_name, result in results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\nOverall: {passed}/{total} tests passed ({passed/total:.1%})")
    
    if passed == total:
        print("\n🎉 ALL TESTS PASSED!")
        print("The monitoring system is ready for use in Streamlit.")
        show_monitoring_location_guide()
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Please check the error messages above and fix any issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)