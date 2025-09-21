#!/usr/bin/env python3
"""
Test Service Initialization

Test that the enhanced pattern loader service is properly initialized.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_service_initialization():
    """Test service initialization."""
    
    print("🔍 Testing Service Initialization")
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
        enhanced_loader = optional_service('enhanced_pattern_loader', context='InitTest')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("✅ Enhanced pattern loader obtained")
        
        # Check if service is initialized
        print(f"\n🔧 Service Status:")
        print(f"   • Is initialized: {enhanced_loader.is_initialized()}")
        print(f"   • Is healthy: {enhanced_loader.is_healthy()}")
        
        # Force initialization if not initialized
        if not enhanced_loader.is_initialized():
            print("   • Service not initialized, initializing...")
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            try:
                loop.run_until_complete(enhanced_loader.initialize())
                print("   ✅ Service initialized successfully")
            except Exception as e:
                print(f"   ❌ Service initialization failed: {e}")
                return False
            finally:
                loop.close()
        
        # Check patterns after initialization
        print(f"\n📊 Patterns After Initialization:")
        print(f"   • Total patterns: {len(enhanced_loader.patterns)}")
        
        if enhanced_loader.patterns:
            print(f"   • Sample pattern IDs: {list(enhanced_loader.patterns.keys())[:3]}")
        
        # Test statistics
        stats = enhanced_loader.get_pattern_statistics()
        print(f"   • Statistics total: {stats['total_patterns']}")
        print(f"   • Pattern types: {stats['pattern_types']}")
        
        if stats['total_patterns'] > 0:
            print("✅ Service initialization successful with patterns loaded!")
            return True
        else:
            print("⚠️  Service initialized but no patterns loaded")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    success = test_service_initialization()
    
    if success:
        print("\n🎉 Service initialization is working!")
        return 0
    else:
        print("\n💥 Service initialization has issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())