#!/usr/bin/env python3
"""
Test Enhanced Pattern Loader Compatibility

Test that the enhanced pattern loader provides all the methods
expected by existing code that uses the basic pattern loader.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_enhanced_pattern_loader_compatibility():
    """Test that enhanced pattern loader has all expected methods."""
    try:
        # Register services first
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='CompatibilityTest')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("🧪 Testing Enhanced Pattern Loader Compatibility")
        print("=" * 60)
        
        # Test all expected methods
        expected_methods = [
            'load_patterns',
            'get_pattern_by_id', 
            'get_patterns_by_domain',
            'get_patterns_by_type',
            'get_patterns_by_feasibility',
            'save_pattern',
            'list_patterns',
            'refresh_cache',
            'get_pattern',
            'search_patterns',
            'validate_pattern',
            'get_analytics_summary',
            'get_pattern_statistics',
            'health_check'
        ]
        
        print("\n📋 Method Availability Check:")
        missing_methods = []
        
        for method_name in expected_methods:
            if hasattr(enhanced_loader, method_name):
                print(f"✅ {method_name}")
            else:
                print(f"❌ {method_name} - MISSING")
                missing_methods.append(method_name)
        
        if missing_methods:
            print(f"\n❌ Missing methods: {missing_methods}")
            return False
        
        # Test method calls
        print("\n🔧 Method Functionality Test:")
        
        # Test load_patterns
        try:
            patterns = enhanced_loader.load_patterns()
            print(f"✅ load_patterns() - returned {len(patterns)} patterns")
        except Exception as e:
            print(f"❌ load_patterns() - error: {e}")
            return False
        
        # Test list_patterns
        try:
            pattern_ids = enhanced_loader.list_patterns()
            print(f"✅ list_patterns() - returned {len(pattern_ids)} pattern IDs")
        except Exception as e:
            print(f"❌ list_patterns() - error: {e}")
            return False
        
        # Test get_pattern_by_id with non-existent pattern
        try:
            pattern = enhanced_loader.get_pattern_by_id("non-existent-pattern")
            print(f"✅ get_pattern_by_id() - returned {pattern} for non-existent pattern")
        except Exception as e:
            print(f"❌ get_pattern_by_id() - error: {e}")
            return False
        
        # Test get_patterns_by_domain
        try:
            domain_patterns = enhanced_loader.get_patterns_by_domain("test_domain")
            print(f"✅ get_patterns_by_domain() - returned {len(domain_patterns)} patterns")
        except Exception as e:
            print(f"❌ get_patterns_by_domain() - error: {e}")
            return False
        
        # Test get_patterns_by_type
        try:
            type_patterns = enhanced_loader.get_patterns_by_type("test_type")
            print(f"✅ get_patterns_by_type() - returned {len(type_patterns)} patterns")
        except Exception as e:
            print(f"❌ get_patterns_by_type() - error: {e}")
            return False
        
        # Test refresh_cache
        try:
            enhanced_loader.refresh_cache()
            print("✅ refresh_cache() - completed successfully")
        except Exception as e:
            print(f"❌ refresh_cache() - error: {e}")
            return False
        
        # Test search_patterns
        try:
            search_results = enhanced_loader.search_patterns("test query")
            print(f"✅ search_patterns() - returned {len(search_results)} results")
        except Exception as e:
            print(f"❌ search_patterns() - error: {e}")
            return False
        
        # Test validate_pattern
        try:
            test_pattern = {
                "id": "test-pattern",
                "title": "Test Pattern",
                "description": "A test pattern",
                "type": "PAT"
            }
            is_valid, errors = enhanced_loader.validate_pattern(test_pattern)
            print(f"✅ validate_pattern() - validation result: {is_valid}, errors: {len(errors)}")
        except Exception as e:
            print(f"❌ validate_pattern() - error: {e}")
            return False
        
        # Test analytics methods
        try:
            analytics = enhanced_loader.get_analytics_summary()
            print(f"✅ get_analytics_summary() - returned analytics data")
        except Exception as e:
            print(f"❌ get_analytics_summary() - error: {e}")
            return False
        
        # Test get_pattern_statistics
        try:
            stats = enhanced_loader.get_pattern_statistics()
            print(f"✅ get_pattern_statistics() - returned statistics with {stats.get('total_patterns', 0)} patterns")
        except Exception as e:
            print(f"❌ get_pattern_statistics() - error: {e}")
            return False
        
        # Test save_pattern
        try:
            test_pattern_to_save = {
                "id": "test-save-pattern",
                "title": "Test Save Pattern",
                "description": "A test pattern for save functionality",
                "type": "PAT"
            }
            success, message = enhanced_loader.save_pattern(test_pattern_to_save)
            print(f"✅ save_pattern() - save result: {success}, message: {message[:50]}...")
        except Exception as e:
            print(f"❌ save_pattern() - error: {e}")
            return False
        
        # Test get_patterns_by_feasibility
        try:
            feasibility_patterns = enhanced_loader.get_patterns_by_feasibility("high")
            print(f"✅ get_patterns_by_feasibility() - returned {len(feasibility_patterns)} patterns")
        except Exception as e:
            print(f"❌ get_patterns_by_feasibility() - error: {e}")
            return False
        
        # Test health check
        try:
            is_healthy = enhanced_loader.health_check()
            print(f"✅ health_check() - health status: {is_healthy}")
        except Exception as e:
            print(f"❌ health_check() - error: {e}")
            return False
        
        print("\n" + "=" * 60)
        print("✅ All compatibility tests passed!")
        print("🎉 Enhanced pattern loader is fully compatible with existing code")
        
        return True
        
    except Exception as e:
        print(f"❌ Compatibility test failed: {e}")
        return False


def test_basic_vs_enhanced_interface():
    """Compare basic and enhanced pattern loader interfaces."""
    try:
        print("\n🔍 Interface Comparison:")
        print("=" * 40)
        
        # Get basic pattern loader
        from app.pattern.loader import PatternLoader
        basic_loader = PatternLoader("./data/patterns")
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='InterfaceTest')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available for comparison")
            return False
        
        # Get methods from both
        basic_methods = [method for method in dir(basic_loader) 
                        if not method.startswith('_') and callable(getattr(basic_loader, method))]
        enhanced_methods = [method for method in dir(enhanced_loader) 
                           if not method.startswith('_') and callable(getattr(enhanced_loader, method))]
        
        print(f"📊 Basic Pattern Loader Methods: {len(basic_methods)}")
        for method in sorted(basic_methods):
            print(f"   • {method}")
        
        print(f"\n📊 Enhanced Pattern Loader Methods: {len(enhanced_methods)}")
        for method in sorted(enhanced_methods):
            print(f"   • {method}")
        
        # Check compatibility
        missing_in_enhanced = set(basic_methods) - set(enhanced_methods)
        additional_in_enhanced = set(enhanced_methods) - set(basic_methods)
        
        if missing_in_enhanced:
            print(f"\n⚠️  Methods missing in enhanced loader: {missing_in_enhanced}")
        else:
            print(f"\n✅ Enhanced loader has all basic loader methods")
        
        if additional_in_enhanced:
            print(f"\n➕ Additional methods in enhanced loader: {len(additional_in_enhanced)}")
            for method in sorted(additional_in_enhanced):
                print(f"   • {method}")
        
        return len(missing_in_enhanced) == 0
        
    except Exception as e:
        print(f"❌ Interface comparison failed: {e}")
        return False


def main():
    """Run all compatibility tests."""
    print("🚀 Enhanced Pattern Loader Compatibility Test Suite")
    print("=" * 70)
    
    tests = [
        ("Enhanced Pattern Loader Compatibility", test_enhanced_pattern_loader_compatibility),
        ("Interface Comparison", test_basic_vs_enhanced_interface)
    ]
    
    results = {}
    
    for test_name, test_func in tests:
        print(f"\n📋 Running: {test_name}")
        try:
            results[test_name] = test_func()
        except Exception as e:
            print(f"❌ Test {test_name} crashed: {e}")
            results[test_name] = False
    
    # Summary
    print(f"\n📊 Test Results Summary:")
    print("=" * 40)
    passed = 0
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 Enhanced pattern loader is fully compatible!")
        return 0
    else:
        print("💥 Some compatibility issues found.")
        return 1


if __name__ == "__main__":
    sys.exit(main())