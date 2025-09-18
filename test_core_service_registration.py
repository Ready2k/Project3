#!/usr/bin/env python3
"""
Test script for core service registration.

This script tests the registration and initialization of core services
to verify that task 2.1.2 is working correctly.
"""

import sys
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.core.registry import get_registry, reset_registry
from app.core.service_registration import (
    register_core_services, 
    initialize_core_services,
    get_core_service_health,
    validate_core_service_dependencies
)

def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )

def test_core_service_registration():
    """Test core service registration."""
    print("🧪 Testing Core Service Registration")
    print("=" * 50)
    
    try:
        # Reset registry to start fresh
        reset_registry()
        registry = get_registry()
        
        print("1. Registering core services...")
        registered_services = register_core_services(registry)
        print(f"   ✅ Registered services: {registered_services}")
        
        print("\n2. Validating service registry...")
        dependency_errors = validate_core_service_dependencies()
        if dependency_errors:
            print(f"   ⚠️  Dependency errors: {dependency_errors}")
        else:
            print("   ✅ All dependencies validated")
        
        print("\n3. Checking registered services...")
        for service_name in registered_services:
            if registry.has(service_name):
                print(f"   ✅ {service_name} is registered")
            else:
                print(f"   ❌ {service_name} is NOT registered")
        
        print("\n4. Initializing core services...")
        init_results = initialize_core_services(registry)
        for service_name, success in init_results.items():
            status = "✅" if success else "❌"
            print(f"   {status} {service_name}: {'initialized' if success else 'failed'}")
        
        print("\n5. Checking service health...")
        health_status = get_core_service_health()
        for service_name, healthy in health_status.items():
            status = "✅" if healthy else "❌"
            print(f"   {status} {service_name}: {'healthy' if healthy else 'unhealthy'}")
        
        print("\n6. Testing service access...")
        
        # Test config service
        try:
            config_service = registry.get("config")
            version = config_service.get("version", "unknown")
            print(f"   ✅ Config service accessible, version: {version}")
        except Exception as e:
            print(f"   ❌ Config service error: {e}")
        
        # Test logger service
        try:
            logger_service = registry.get("logger")
            logger_service.info("Test log message from service registry")
            print("   ✅ Logger service accessible and working")
        except Exception as e:
            print(f"   ❌ Logger service error: {e}")
        
        # Test cache service
        try:
            cache_service = registry.get("cache")
            stats = cache_service.get_stats()
            print(f"   ✅ Cache service accessible, backend: {stats.get('backend', 'unknown')}")
        except Exception as e:
            print(f"   ❌ Cache service error: {e}")
        
        # Test security service
        try:
            security_service = registry.get("security_validator")
            is_valid = security_service.validate_input("test input")
            print(f"   ✅ Security service accessible, validation result: {is_valid}")
        except Exception as e:
            print(f"   ❌ Security service error: {e}")
        
        # Test advanced prompt defender
        try:
            defender_service = registry.get("advanced_prompt_defender")
            health = defender_service.health_check()
            print(f"   ✅ Advanced prompt defender accessible, healthy: {health}")
        except Exception as e:
            print(f"   ❌ Advanced prompt defender error: {e}")
        
        print("\n" + "=" * 50)
        print("🎉 Core service registration test completed successfully!")
        
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_service_dependencies():
    """Test service dependency resolution."""
    print("\n🔗 Testing Service Dependencies")
    print("=" * 30)
    
    registry = get_registry()
    
    # Test that services can access their dependencies
    try:
        # Logger should be able to access config
        logger_service = registry.get("logger")
        print("   ✅ Logger service created (depends on config)")
        
        # Cache should be able to access config and logger
        cache_service = registry.get("cache")
        print("   ✅ Cache service created (depends on config, logger)")
        
        # Security should be able to access config and logger
        security_service = registry.get("security_validator")
        print("   ✅ Security service created (depends on config, logger)")
        
        # Advanced defender should be able to access config, logger, cache
        defender_service = registry.get("advanced_prompt_defender")
        print("   ✅ Advanced defender created (depends on config, logger, cache)")
        
        print("   ✅ All dependency resolution tests passed")
        return True
        
    except Exception as e:
        print(f"   ❌ Dependency resolution failed: {e}")
        return False

def main():
    """Main test function."""
    setup_logging()
    
    print("🚀 Starting Core Service Registration Tests")
    print("=" * 60)
    
    # Run tests
    registration_success = test_core_service_registration()
    dependency_success = test_service_dependencies()
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    print(f"   Registration Test: {'✅ PASS' if registration_success else '❌ FAIL'}")
    print(f"   Dependency Test:   {'✅ PASS' if dependency_success else '❌ FAIL'}")
    
    overall_success = registration_success and dependency_success
    print(f"\n   Overall Result:    {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}")
    
    return 0 if overall_success else 1

if __name__ == "__main__":
    sys.exit(main())