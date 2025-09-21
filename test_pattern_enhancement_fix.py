#!/usr/bin/env python3
"""
Test Pattern Enhancement Fix

Test that the pattern enhancement error message has been resolved.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_pattern_enhancement_status():
    """Test pattern enhancement status checking."""
    
    print("🔍 Testing Pattern Enhancement Status")
    print("=" * 50)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        print("✅ Services registered")
        
        # Test the utility function
        from app.utils.pattern_status_utils import get_pattern_enhancement_error_or_success
        
        status_msg = get_pattern_enhancement_error_or_success()
        print(f"\n📊 Pattern Enhancement Status:")
        print(f"   Message: {status_msg}")
        
        if status_msg.startswith("✅"):
            print("✅ Pattern enhancement is available!")
            success = True
        else:
            print("❌ Pattern enhancement is not available")
            success = False
        
        # Test service availability directly
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='test')
        
        print(f"\n🔧 Service Availability:")
        print(f"   Enhanced Pattern Loader: {'✅ Available' if enhanced_loader else '❌ Not Available'}")
        
        if enhanced_loader:
            print(f"   • Is initialized: {enhanced_loader.is_initialized()}")
            print(f"   • Is healthy: {enhanced_loader.is_healthy()}")
            print(f"   • Patterns loaded: {len(enhanced_loader.patterns)}")
        
        # Test UI functions
        print(f"\n🎨 UI Function Availability:")
        try:
            from app.ui.enhanced_pattern_management import render_pattern_overview, render_pattern_analytics
            print("✅ render_pattern_overview: Available")
            print("✅ render_pattern_analytics: Available")
            ui_functions_available = True
        except ImportError as e:
            print(f"❌ UI functions not available: {e}")
            ui_functions_available = False
        
        overall_success = success and enhanced_loader is not None and ui_functions_available
        
        return overall_success
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def simulate_streamlit_tab_logic():
    """Simulate the logic that would run in the Streamlit pattern enhancement tab."""
    
    print("\n🎭 Simulating Streamlit Tab Logic")
    print("=" * 40)
    
    try:
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='pattern enhancement')
        analytics_service = optional_service('pattern_analytics_service', context='pattern enhancement')
        
        print(f"Enhanced Loader Available: {'✅' if enhanced_loader else '❌'}")
        print(f"Analytics Service Available: {'✅' if analytics_service else '❌'}")
        
        if enhanced_loader:
            print("✅ Would show: Pattern enhancement available")
            print("✅ Would render: Pattern Overview and Analytics tabs")
            
            # Test that we can call the UI functions
            try:
                from app.ui.enhanced_pattern_management import render_pattern_overview, render_pattern_analytics
                print("✅ UI functions can be imported successfully")
                
                # We can't actually call them without Streamlit context, but we can verify they exist
                print("✅ render_pattern_overview function exists")
                print("✅ render_pattern_analytics function exists")
                
                return True
            except Exception as e:
                print(f"❌ Error with UI functions: {e}")
                return False
        else:
            # This is the fallback case
            from app.utils.pattern_status_utils import get_pattern_enhancement_error_or_success
            status_msg = get_pattern_enhancement_error_or_success()
            
            if status_msg.startswith("✅"):
                print("✅ Would show: Success message (service available but couldn't access)")
            else:
                print("ℹ️ Would show: Info message about service not being available")
            
            return False
        
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        return False


def main():
    """Run the tests."""
    print("🚀 Pattern Enhancement Fix Verification")
    print("=" * 60)
    
    # Test 1: Status checking
    status_test_passed = test_pattern_enhancement_status()
    
    # Test 2: Streamlit logic simulation
    streamlit_test_passed = simulate_streamlit_tab_logic()
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 30)
    
    if status_test_passed:
        print("✅ Pattern enhancement status test: PASS")
    else:
        print("❌ Pattern enhancement status test: FAIL")
    
    if streamlit_test_passed:
        print("✅ Streamlit tab logic test: PASS")
    else:
        print("❌ Streamlit tab logic test: FAIL")
    
    overall_success = status_test_passed and streamlit_test_passed
    
    if overall_success:
        print("\n🎉 SUCCESS: Pattern enhancement error message has been resolved!")
        print("   The UI should now show proper status instead of hardcoded error messages.")
        return 0
    else:
        print("\n💥 FAILURE: Some issues still exist")
        return 1


if __name__ == "__main__":
    sys.exit(main())