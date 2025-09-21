#!/usr/bin/env python3
"""
Verify Pattern Statistics Fix

Verify that the get_pattern_statistics AttributeError has been resolved.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def verify_pattern_statistics_fix():
    """Verify that the AttributeError for get_pattern_statistics is fixed."""
    
    print("🔍 Verifying Pattern Statistics Fix")
    print("=" * 50)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader (simulating the UI call)
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='UISimulation')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("✅ Enhanced pattern loader service available")
        
        # Test the exact call that was failing in the UI
        print("\n🧪 Testing UI Call Simulation:")
        print("   Simulating: stats = pattern_loader.get_pattern_statistics()")
        
        try:
            # This is the exact call that was failing
            stats = enhanced_loader.get_pattern_statistics()
            
            print("✅ get_pattern_statistics() call successful!")
            print(f"   • Returned type: {type(stats)}")
            print(f"   • Total patterns: {stats.get('total_patterns', 'N/A')}")
            print(f"   • Pattern types: {stats.get('pattern_types', {})}")
            
            # Verify all expected keys are present
            expected_keys = [
                'total_patterns', 'pattern_types', 'domains', 'complexity_scores',
                'feasibility_levels', 'autonomy_levels', 'avg_complexity', 'avg_autonomy'
            ]
            
            missing_keys = [key for key in expected_keys if key not in stats]
            
            if missing_keys:
                print(f"⚠️  Missing keys: {missing_keys}")
            else:
                print("✅ All expected keys present in statistics")
            
            return True
            
        except AttributeError as e:
            print(f"❌ AttributeError still occurs: {e}")
            return False
        except Exception as e:
            print(f"❌ Other error occurred: {e}")
            return False
    
    except Exception as e:
        print(f"❌ Setup failed: {e}")
        return False


def simulate_ui_usage():
    """Simulate the exact usage pattern from the UI."""
    
    print("\n🎭 Simulating UI Usage Pattern")
    print("=" * 40)
    
    try:
        # This simulates the exact code from enhanced_pattern_management.py
        from app.utils.imports import optional_service
        
        # Get the pattern loader (as the UI does)
        pattern_loader = optional_service('enhanced_pattern_loader', context='UISimulation')
        
        if not pattern_loader:
            print("❌ Pattern loader not available")
            return False
        
        print("✅ Pattern loader obtained")
        
        # Simulate the UI calls
        print("\n📋 Simulating UI method calls:")
        
        # 1. Load patterns (line 401 in UI)
        try:
            patterns = pattern_loader.load_patterns()
            print(f"✅ load_patterns() - {len(patterns)} patterns loaded")
        except Exception as e:
            print(f"❌ load_patterns() failed: {e}")
            return False
        
        # 2. Get pattern statistics (line 402 in UI - the failing call)
        try:
            stats = pattern_loader.get_pattern_statistics()
            print(f"✅ get_pattern_statistics() - statistics retrieved")
        except Exception as e:
            print(f"❌ get_pattern_statistics() failed: {e}")
            return False
        
        # 3. Other UI calls
        try:
            pattern_loader.refresh_cache()
            print("✅ refresh_cache() - cache refreshed")
        except Exception as e:
            print(f"❌ refresh_cache() failed: {e}")
            return False
        
        try:
            test_pattern = pattern_loader.get_pattern_by_id("non-existent")
            print(f"✅ get_pattern_by_id() - returned {test_pattern}")
        except Exception as e:
            print(f"❌ get_pattern_by_id() failed: {e}")
            return False
        
        print("\n🎉 All UI method calls successful!")
        return True
        
    except Exception as e:
        print(f"❌ UI simulation failed: {e}")
        return False


def main():
    """Run the verification."""
    
    print("🚀 Pattern Statistics AttributeError Fix Verification")
    print("=" * 60)
    
    # Test 1: Basic fix verification
    fix_verified = verify_pattern_statistics_fix()
    
    # Test 2: UI usage simulation
    ui_simulation_passed = simulate_ui_usage()
    
    # Summary
    print("\n📊 Verification Results:")
    print("=" * 30)
    
    if fix_verified:
        print("✅ Pattern statistics fix verified")
    else:
        print("❌ Pattern statistics fix failed")
    
    if ui_simulation_passed:
        print("✅ UI usage simulation passed")
    else:
        print("❌ UI usage simulation failed")
    
    overall_success = fix_verified and ui_simulation_passed
    
    if overall_success:
        print("\n🎉 SUCCESS: AttributeError has been resolved!")
        print("   The enhanced pattern loader now has the get_pattern_statistics() method")
        print("   and is fully compatible with the UI expectations.")
        return 0
    else:
        print("\n💥 FAILURE: Issues still exist")
        return 1


if __name__ == "__main__":
    sys.exit(main())