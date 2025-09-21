#!/usr/bin/env python3
"""
Test Direct Service Creation

Test creating the enhanced pattern loader service directly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_direct_service_creation():
    """Test creating the service directly."""
    
    print("🔍 Testing Direct Service Creation")
    print("=" * 50)
    
    try:
        # Import the service class directly
        from app.services.enhanced_pattern_loader import EnhancedPatternLoader
        
        print("✅ Service class imported")
        
        # Create service instance directly
        config = {
            'pattern_library_path': './data/patterns',
            'enable_analytics': True,
            'enable_caching': True,
            'cache_ttl_seconds': 3600,
            'enable_validation': True,
            'auto_reload': False,
            'performance_tracking': True
        }
        
        enhanced_loader = EnhancedPatternLoader(config)
        print("✅ Service instance created")
        
        # Check initial state
        print(f"\n🔧 Initial State:")
        print(f"   • Is initialized: {enhanced_loader.is_initialized()}")
        print(f"   • Patterns loaded: {len(enhanced_loader.patterns)}")
        
        # Try to initialize
        print(f"\n🚀 Initializing service...")
        try:
            enhanced_loader.initialize()
            print("✅ Service initialized successfully")
        except Exception as e:
            print(f"❌ Service initialization failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
        # Check state after initialization
        print(f"\n📊 State After Initialization:")
        print(f"   • Is initialized: {enhanced_loader.is_initialized()}")
        print(f"   • Is healthy: {enhanced_loader.is_healthy()}")
        print(f"   • Patterns loaded: {len(enhanced_loader.patterns)}")
        
        if enhanced_loader.patterns:
            print(f"   • Sample pattern IDs: {list(enhanced_loader.patterns.keys())[:3]}")
        
        # Test statistics
        stats = enhanced_loader.get_pattern_statistics()
        print(f"   • Statistics total: {stats['total_patterns']}")
        print(f"   • Pattern types: {stats['pattern_types']}")
        
        if stats['total_patterns'] > 0:
            print("✅ Direct service creation successful!")
            return True
        else:
            print("⚠️  Service created but no patterns loaded")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    success = test_direct_service_creation()
    
    if success:
        print("\n🎉 Direct service creation is working!")
        return 0
    else:
        print("\n💥 Direct service creation has issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())