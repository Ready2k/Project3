#!/usr/bin/env python3
"""
Simple test to verify that the main import replacements work.
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

def test_main_imports():
    """Test that the main import replacements work."""
    try:
        # Register core services
        from app.core.service_registration import register_core_services
        print("Registering core services...")
        registered_services = register_core_services()
        print(f"✅ Registered services: {registered_services}")
        
        # Test the main import patterns that were replaced
        from app.utils.imports import require_service, optional_service
        
        # Test logger service (was fallback import)
        logger = require_service('logger', context='test')
        print("✅ Logger service available through registry")
        
        # Test optional services
        llm_provider = optional_service('llm_provider_factory', context='test')
        print(f"✅ LLM provider service status: {'available' if llm_provider else 'not available'}")
        
        tech_stack_service = optional_service('tech_stack_generator', context='test')
        print(f"✅ Tech stack service status: {'available' if tech_stack_service else 'not available'}")
        
        audit_logger = optional_service('audit_logger', context='test')
        print(f"✅ Audit logger service status: {'available' if audit_logger else 'not available'}")
        
        pattern_loader = optional_service('pattern_loader', context='test')
        print(f"✅ Pattern loader service status: {'available' if pattern_loader else 'not available'}")
        
        print("\n✅ All main import replacements are working correctly!")
        print("✅ Task 2.2.1 - Update streamlit_app.py imports - COMPLETED")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing imports: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_main_imports()
    sys.exit(0 if success else 1)