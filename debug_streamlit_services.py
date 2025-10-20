#!/usr/bin/env python3
"""Debug script to check what's happening with Streamlit service registration."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def debug_streamlit_services():
    """Debug Streamlit service registration."""
    
    print("🔍 Debugging Streamlit Service Registration...")
    print("=" * 60)
    
    try:
        # Simulate Streamlit environment
        from app.core.service_registration import register_core_services
        from app.core.registry import get_registry
        from app.utils.imports import require_service, optional_service
        
        registry = get_registry()
        
        print("📝 Checking if services are already registered...")
        if registry.has('logger'):
            print("✅ Logger service already registered")
        else:
            print("❌ Logger service not registered")
        
        print("\n📝 Attempting service registration...")
        
        # Try the same logic as Streamlit
        try:
            print("🔄 Trying with skip_async_services=False...")
            registered_services = register_core_services(registry, skip_async_services=False)
            print(f"✅ Registered {len(registered_services)} services with async enabled")
        except RuntimeError as e:
            if "There is no current event loop in thread" in str(e):
                print(f"⚠️ Event loop issue: {e}")
                print("🔄 Trying with skip_async_services=True...")
                registered_services = register_core_services(registry, skip_async_services=True)
                print(f"✅ Registered {len(registered_services)} services with async disabled")
            else:
                raise
        
        print(f"\n📊 Registered services: {registered_services}")
        
        # Check specific services
        print("\n🔍 Checking pattern services:")
        
        enhanced_loader = optional_service('enhanced_pattern_loader', context='debug')
        if enhanced_loader:
            print("✅ enhanced_pattern_loader is available")
        else:
            print("❌ enhanced_pattern_loader is NOT available")
        
        analytics_service = optional_service('pattern_analytics_service', context='debug')
        if analytics_service:
            print("✅ pattern_analytics_service is available")
        else:
            print("❌ pattern_analytics_service is NOT available")
        
        # Check registry directly
        print("\n🔍 Checking registry directly:")
        if registry.has('enhanced_pattern_loader'):
            print("✅ enhanced_pattern_loader is in registry")
        else:
            print("❌ enhanced_pattern_loader is NOT in registry")
            
        if registry.has('pattern_analytics_service'):
            print("✅ pattern_analytics_service is in registry")
        else:
            print("❌ pattern_analytics_service is NOT in registry")
        
        return True
        
    except Exception as e:
        print(f"❌ Error during debug: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("🚀 Starting Streamlit service debug...")
    success = debug_streamlit_services()
    
    if success:
        print("\n✅ Debug completed!")
    else:
        print("\n❌ Debug failed!")