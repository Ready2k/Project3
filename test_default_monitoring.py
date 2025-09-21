#!/usr/bin/env python3
"""
Test script to verify that monitoring starts by default.
"""

import sys
import os
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

def test_default_monitoring_state():
    """Test that monitoring is enabled by default."""
    print("🔍 Testing Default Monitoring State")
    print("=" * 50)
    
    try:
        from app.monitoring.integration_service import MonitoringIntegrationService
        from app.monitoring.tech_stack_monitor import TechStackMonitor
        from app.monitoring.quality_assurance import QualityAssuranceSystem
        
        # Test integration service default state
        integration_service = MonitoringIntegrationService()
        status = integration_service.get_monitoring_status()
        
        print(f"✅ Integration service initialized")
        print(f"   - Integration active: {status['integration_active']}")
        print(f"   - Monitor active: {status['monitor_active']}")
        print(f"   - QA system active: {status['qa_system_active']}")
        
        # Verify monitoring is active by default
        assert status['integration_active'] == True, "Integration should be active by default"
        print("✅ Integration service is active by default")
        
        # Test individual components
        monitor = TechStackMonitor()
        assert monitor.monitoring_active == True, "TechStackMonitor should be active by default"
        print("✅ TechStackMonitor is active by default")
        
        qa_system = QualityAssuranceSystem()
        assert qa_system.qa_enabled == True, "QualityAssuranceSystem should be enabled by default"
        print("✅ QualityAssuranceSystem is enabled by default")
        
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_monitoring_controls():
    """Test that monitoring can be disabled and re-enabled."""
    print("\n🎛️ Testing Monitoring Controls")
    print("=" * 50)
    
    try:
        from app.monitoring.integration_service import MonitoringIntegrationService
        
        integration_service = MonitoringIntegrationService()
        
        # Test initial state (should be active)
        initial_status = integration_service.get_monitoring_status()
        print(f"✅ Initial state - Integration active: {initial_status['integration_active']}")
        
        # Test stopping monitoring
        import asyncio
        asyncio.run(integration_service.stop_monitoring_integration())
        
        stopped_status = integration_service.get_monitoring_status()
        print(f"✅ After stop - Integration active: {stopped_status['integration_active']}")
        assert stopped_status['integration_active'] == False, "Monitoring should be stopped"
        
        # Test starting monitoring again
        asyncio.run(integration_service.start_monitoring_integration())
        
        restarted_status = integration_service.get_monitoring_status()
        print(f"✅ After restart - Integration active: {restarted_status['integration_active']}")
        assert restarted_status['integration_active'] == True, "Monitoring should be restarted"
        
        print("✅ Monitoring controls working correctly")
        return True
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return False

def show_updated_usage_guide():
    """Show the updated usage guide with default monitoring."""
    print("\n📋 Updated Usage Guide")
    print("=" * 50)
    
    guide = """
    🎉 **Monitoring is now ACTIVE BY DEFAULT!**
    
    🚀 To use the monitoring system:
    
    1. Start Streamlit:
       streamlit run streamlit_app.py
    
    2. Navigate to: Observability → Real-time Monitoring
    
    3. ✅ Monitoring is already active - no need to start it!
    
    4. Generate tech stacks in the Analysis tab
    
    5. Watch live metrics update automatically!
    
    🎛️ **Control Options:**
    
    ⏹️ **Disable Monitoring** - Turn off monitoring if needed
    🔄 **Restart Monitoring** - Restart the monitoring system
    🔄 **Refresh Status** - Update dashboard data
    📊 **Generate QA Report** - Create quality analysis report
    
    💡 **Benefits of Default Monitoring:**
    
    ✅ Immediate visibility into system performance
    ✅ Automatic quality tracking from first use
    ✅ Proactive issue detection
    ✅ Continuous performance optimization
    ✅ Real-time user satisfaction monitoring
    
    🎯 **What's Monitored Automatically:**
    
    • Technology extraction accuracy
    • Processing times and performance
    • User satisfaction scores
    • Catalog health and consistency
    • System alerts and recommendations
    • Quality assurance checks
    
    The system now provides comprehensive monitoring out-of-the-box!
    """
    
    print(guide)

def main():
    """Run all default monitoring tests."""
    print("🔍 Default Monitoring System Test")
    print("=" * 60)
    
    tests = [
        ("Default State Test", test_default_monitoring_state),
        ("Monitoring Controls Test", test_monitoring_controls)
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
        print("Monitoring is now active by default and working correctly.")
        show_updated_usage_guide()
    else:
        print("\n⚠️ SOME TESTS FAILED")
        print("Please check the error messages above and fix any issues.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)