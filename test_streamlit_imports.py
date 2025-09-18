#!/usr/bin/env python3
"""
Test script to verify that streamlit_app.py imports work correctly with service registry.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_streamlit_imports():
    """Test that streamlit_app.py can be imported without fallback import errors."""
    try:
        # First, register core services
        from app.core.service_registration import register_core_services
        from app.core.registry import get_registry
        
        print("Registering core services...")
        registered_services = register_core_services()
        print(f"✅ Registered services: {registered_services}")
        
        # Verify services are available
        registry = get_registry()
        for service_name in registered_services:
            if registry.has(service_name):
                print(f"✅ Service '{service_name}' is available")
            else:
                print(f"❌ Service '{service_name}' is not available")
        
        # Now try to import streamlit_app
        print("\nTesting streamlit_app.py imports...")
        
        # Import the main module (this will trigger all the import statements)
        import streamlit_app
        print("✅ streamlit_app.py imported successfully")
        
        # Test that the logger service is working
        if hasattr(streamlit_app, 'app_logger'):
            print("✅ app_logger is available")
            streamlit_app.app_logger.info("Test log message from service registry")
        else:
            print("❌ app_logger is not available")
        
        # Test that LLM provider service availability is detected
        if hasattr(streamlit_app, 'OPENAI_AVAILABLE'):
            print(f"✅ OPENAI_AVAILABLE status: {streamlit_app.OPENAI_AVAILABLE}")
        else:
            print("❌ OPENAI_AVAILABLE is not available")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing streamlit imports: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_streamlit_imports()
    sys.exit(0 if success else 1)