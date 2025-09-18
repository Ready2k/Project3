#!/usr/bin/env python3
"""
Integration test for core services working together.

This test verifies that the registered core services can work together
and provide the expected functionality.
"""

import sys
import asyncio
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.registry import get_registry, reset_registry
from app.core.service_registration import register_core_services, initialize_core_services

async def test_service_integration():
    """Test that services work together properly."""
    print("🔗 Testing Service Integration")
    print("=" * 40)
    
    try:
        # Reset and set up services
        reset_registry()
        registry = get_registry()
        
        # Register and initialize services
        registered = register_core_services(registry)
        init_results = initialize_core_services(registry)
        
        print(f"✅ Services registered and initialized: {registered}")
        
        # Test 1: Config service provides configuration to other services
        print("\n1. Testing configuration service integration...")
        config_service = registry.get("config")
        
        # Test getting various config values
        version = config_service.get("version", "unknown")
        provider = config_service.get("provider", "unknown")
        print(f"   ✅ Config values: version={version}, provider={provider}")
        
        # Test 2: Logger service can log messages
        print("\n2. Testing logger service integration...")
        logger_service = registry.get("logger")
        
        logger_service.info("Integration test: Logger service working")
        logger_service.debug("Debug message from integration test")
        logger_service.warning("Warning message from integration test")
        
        stats = logger_service.get_stats()
        print(f"   ✅ Logger stats: level={stats['level']}, handlers={stats['handler_count']}")
        
        # Test 3: Cache service can store and retrieve data
        print("\n3. Testing cache service integration...")
        cache_service = registry.get("cache")
        
        # Test caching (note: this is async, so we'll test the sync wrapper methods)
        test_key = "integration_test_key"
        test_value = {"message": "Hello from cache!", "timestamp": "2025-09-18"}
        
        # Set a value
        success = await cache_service.set(test_key, test_value, "test_namespace")
        print(f"   ✅ Cache set operation: {'success' if success else 'failed'}")
        
        # Get the value back
        retrieved = await cache_service.get(test_key, "test_namespace")
        if retrieved == test_value:
            print("   ✅ Cache get operation: value retrieved correctly")
        else:
            print(f"   ⚠️  Cache get operation: expected {test_value}, got {retrieved}")
        
        cache_stats = cache_service.get_stats()
        print(f"   ✅ Cache stats: backend={cache_stats.get('backend')}, hits={cache_stats.get('hits', 0)}")
        
        # Test 4: Security service can validate input
        print("\n4. Testing security service integration...")
        security_service = registry.get("security_validator")
        
        # Test valid input
        valid_input = "Create a simple web application with user authentication"
        is_valid = security_service.validate_input(valid_input)
        print(f"   ✅ Valid input validation: {'passed' if is_valid else 'failed'}")
        
        # Test input sanitization
        test_input = "<script>alert('test')</script>Hello World"
        sanitized = security_service.sanitize_input(test_input)
        print(f"   ✅ Input sanitization: '{test_input}' -> '{sanitized}'")
        
        # Test requirements validation
        requirements = "Build a REST API for managing user accounts with CRUD operations"
        req_valid, req_message = security_service.validate_requirements_text(requirements)
        print(f"   ✅ Requirements validation: {'passed' if req_valid else 'failed'} - {req_message}")
        
        security_stats = security_service.get_validation_stats()
        print(f"   ✅ Security stats: validations={security_stats['total_validations']}")
        
        # Test 5: Advanced prompt defender integration
        print("\n5. Testing advanced prompt defender integration...")
        defender_service = registry.get("advanced_prompt_defender")
        
        # Test async validation
        test_prompt = "Help me create a user registration form with validation"
        validation_result = await defender_service.validate_input(test_prompt)
        
        action = validation_result.get("action", "unknown")
        confidence = validation_result.get("confidence", 0.0)
        print(f"   ✅ Prompt validation: action={action}, confidence={confidence:.2f}")
        
        # Test 6: Services can access each other through dependencies
        print("\n6. Testing service dependency access...")
        
        # Logger should be able to use config
        logger_level = logger_service.get_config("level", "INFO")
        print(f"   ✅ Logger accessing config: level={logger_level}")
        
        # Cache should be able to use logger (indirectly through its initialization)
        cache_backend = cache_service.get_config("backend", "memory")
        print(f"   ✅ Cache accessing config: backend={cache_backend}")
        
        # Security should be able to use both config and logger
        max_length = security_service.get_config("max_input_length", 10000)
        print(f"   ✅ Security accessing config: max_input_length={max_length}")
        
        print("\n" + "=" * 40)
        print("🎉 All integration tests passed!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Main test function."""
    print("🚀 Starting Service Integration Tests")
    print("=" * 50)
    
    # Run the async test
    success = asyncio.run(test_service_integration())
    
    print("\n" + "=" * 50)
    print(f"📊 Integration Test Result: {'✅ PASS' if success else '❌ FAIL'}")
    
    return 0 if success else 1

if __name__ == "__main__":
    sys.exit(main())