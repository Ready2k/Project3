#!/usr/bin/env python3
"""
Test Capabilities Fix

Test that the capabilities KeyError has been resolved.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_capabilities_fix():
    """Test that the capabilities key is now available."""
    
    print("🔍 Testing Capabilities Fix")
    print("=" * 50)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        print("✅ Services registered")
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='CapabilitiesTest')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("✅ Enhanced pattern loader available")
        
        # Test get_pattern_statistics
        stats = enhanced_loader.get_pattern_statistics()
        
        print(f"\n📊 Testing Required Keys:")
        
        # Test capabilities key
        if 'capabilities' in stats:
            print("✅ 'capabilities' key present")
            capabilities = stats['capabilities']
            
            # Test required capability keys
            required_capability_keys = ['has_agentic_features', 'has_detailed_tech_stack', 'has_implementation_guidance']
            for key in required_capability_keys:
                if key in capabilities:
                    print(f"✅ capabilities['{key}'] present: {capabilities[key]}")
                else:
                    print(f"❌ capabilities['{key}'] missing")
                    return False
        else:
            print("❌ 'capabilities' key missing")
            return False
        
        # Test by_type key
        if 'by_type' in stats:
            print(f"✅ 'by_type' key present: {stats['by_type']}")
        else:
            print("❌ 'by_type' key missing")
            return False
        
        # Test that the UI function would work
        print(f"\n🎨 Testing UI Function Compatibility:")
        
        try:
            # Simulate the problematic UI code
            agentic_count = stats["capabilities"].get("has_agentic_features", 0)
            enhanced_count = stats["capabilities"].get("has_detailed_tech_stack", 0)
            guidance_count = stats["capabilities"].get("has_implementation_guidance", 0)
            type_data = stats["by_type"]
            
            print(f"✅ Agentic patterns: {agentic_count}")
            print(f"✅ Enhanced tech stack: {enhanced_count}")
            print(f"✅ Implementation guidance: {guidance_count}")
            print(f"✅ Type data: {type_data}")
            
            print("✅ UI function compatibility test passed!")
            return True
            
        except KeyError as e:
            print(f"❌ KeyError still occurs: {e}")
            return False
        except Exception as e:
            print(f"❌ Other error: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_ui_function_directly():
    """Test calling the UI function directly to see if it works."""
    
    print("\n🎭 Testing UI Function Directly")
    print("=" * 40)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='UITest')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        # We can't actually call the Streamlit function without Streamlit context,
        # but we can test the logic that was failing
        print("✅ Enhanced pattern loader available")
        
        # Test the exact code that was failing
        stats = enhanced_loader.get_pattern_statistics()
        
        # This is the line that was causing the KeyError
        agentic_count = stats["capabilities"].get("has_agentic_features", 0)
        print(f"✅ Successfully accessed capabilities.has_agentic_features: {agentic_count}")
        
        enhanced_count = stats["capabilities"].get("has_detailed_tech_stack", 0)
        print(f"✅ Successfully accessed capabilities.has_detailed_tech_stack: {enhanced_count}")
        
        guidance_count = stats["capabilities"].get("has_implementation_guidance", 0)
        print(f"✅ Successfully accessed capabilities.has_implementation_guidance: {guidance_count}")
        
        type_data = stats["by_type"]
        print(f"✅ Successfully accessed by_type: {type_data}")
        
        print("✅ All UI function calls successful!")
        return True
        
    except Exception as e:
        print(f"❌ UI function test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the tests."""
    print("🚀 Capabilities KeyError Fix Verification")
    print("=" * 60)
    
    # Test 1: Capabilities fix
    capabilities_test_passed = test_capabilities_fix()
    
    # Test 2: UI function compatibility
    ui_test_passed = test_ui_function_directly()
    
    # Summary
    print("\n📊 Test Results:")
    print("=" * 30)
    
    if capabilities_test_passed:
        print("✅ Capabilities fix test: PASS")
    else:
        print("❌ Capabilities fix test: FAIL")
    
    if ui_test_passed:
        print("✅ UI function test: PASS")
    else:
        print("❌ UI function test: FAIL")
    
    overall_success = capabilities_test_passed and ui_test_passed
    
    if overall_success:
        print("\n🎉 SUCCESS: KeyError has been resolved!")
        print("   The UI should now work without KeyError exceptions.")
        return 0
    else:
        print("\n💥 FAILURE: KeyError issues still exist")
        return 1


if __name__ == "__main__":
    sys.exit(main())