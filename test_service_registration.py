#!/usr/bin/env python3
"""Test script to check service registration directly."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.service_registration import register_core_services
from app.core.registry import get_registry


def test_service_registration():
    """Test service registration directly."""
    
    print("🔍 Testing Service Registration...")
    print("=" * 60)
    
    try:
        # Get registry
        registry = get_registry()
        
        # Register services
        print("📝 Registering core services...")
        registered_services = register_core_services(registry, skip_async_services=False)
        
        print(f"✅ Registered {len(registered_services)} services:")
        for service in registered_services:
            print(f"  - {service}")
        
        print()
        
        # Check specific services
        print("🔍 Checking specific pattern services:")
        
        # Check enhanced pattern loader
        if registry.has('enhanced_pattern_loader'):
            print("✅ enhanced_pattern_loader is registered")
            service = registry.get('enhanced_pattern_loader')
            print(f"   Type: {type(service).__name__}")
        else:
            print("❌ enhanced_pattern_loader is NOT registered")
        
        # Check pattern analytics service
        if registry.has('pattern_analytics_service'):
            print("✅ pattern_analytics_service is registered")
            service = registry.get('pattern_analytics_service')
            print(f"   Type: {type(service).__name__}")
        else:
            print("❌ pattern_analytics_service is NOT registered")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during service registration: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting service registration test...")
    success = test_service_registration()
    
    if success:
        print("\n✅ Service registration test completed!")
    else:
        print("\n❌ Service registration test failed!")