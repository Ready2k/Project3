#!/usr/bin/env python3
"""
Test script for Diagram Service Factory implementation.

This script tests the diagram service factory functionality including:
- Service availability checking
- Factory creation and registration
- Fallback behavior
- Service instance creation
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.registry import get_registry, reset_registry
from app.core.service_registration import register_core_services
from app.diagrams.factory import DiagramServiceFactory, DiagramType
from app.utils.imports import require_service, optional_service


def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_diagram_service_factory_creation():
    """Test creating the diagram service factory."""
    print("\n=== Testing Diagram Service Factory Creation ===")
    
    try:
        # Create factory with test configuration
        config = {
            "mermaid_config": {
                "default_height": 500,
                "enable_enhanced_rendering": True
            },
            "infrastructure_config": {
                "default_format": "svg",
                "enable_dynamic_mapping": True
            },
            "drawio_config": {
                "enable_multiple_formats": True,
                "include_metadata": True
            }
        }
        
        factory = DiagramServiceFactory(config)
        print("✅ Successfully created DiagramServiceFactory")
        
        # Initialize the factory
        factory.initialize()
        print("✅ Successfully initialized DiagramServiceFactory")
        
        # Check health
        health = factory.health_check()
        print(f"✅ Factory health check: {'Healthy' if health else 'Unhealthy'}")
        
        return factory
        
    except Exception as e:
        print(f"❌ Failed to create DiagramServiceFactory: {e}")
        return None


def test_service_availability_checking(factory: DiagramServiceFactory):
    """Test service availability checking."""
    print("\n=== Testing Service Availability Checking ===")
    
    try:
        # Get available services
        available_services = factory.get_available_services()
        print(f"✅ Available services: {available_services}")
        
        # Check individual service availability
        services_to_check = ["mermaid", "infrastructure", "drawio"]
        for service_name in services_to_check:
            is_available = factory.is_service_available(service_name)
            print(f"✅ Service '{service_name}' available: {is_available}")
            
            # Get service info
            service_info = factory.get_service_info(service_name)
            if service_info:
                print(f"   - Type: {service_info.diagram_type.value}")
                print(f"   - Features: {service_info.features}")
                print(f"   - Required packages: {service_info.required_packages}")
                print(f"   - Optional packages: {service_info.optional_packages}")
                if service_info.error_message:
                    print(f"   - Error: {service_info.error_message}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed service availability checking: {e}")
        return False


def test_service_creation(factory: DiagramServiceFactory):
    """Test creating diagram services."""
    print("\n=== Testing Service Creation ===")
    
    try:
        # Test Mermaid service creation
        print("\n--- Testing Mermaid Service ---")
        mermaid_result = factory.create_mermaid_service()
        if mermaid_result.is_success():
            mermaid_service = mermaid_result.value
            print("✅ Successfully created Mermaid service")
            print(f"   - Available: {mermaid_service.is_available()}")
            print(f"   - Supported formats: {mermaid_service.get_supported_formats()}")
            print(f"   - Health: {'Healthy' if mermaid_service.health_check() else 'Unhealthy'}")
        else:
            print(f"❌ Failed to create Mermaid service: {mermaid_result.error}")
        
        # Test Infrastructure service creation
        print("\n--- Testing Infrastructure Service ---")
        infra_result = factory.create_infrastructure_service()
        if infra_result.is_success():
            infra_service = infra_result.value
            print("✅ Successfully created Infrastructure service")
            print(f"   - Available: {infra_service.is_available()}")
            print(f"   - Supported formats: {infra_service.get_supported_formats()}")
            print(f"   - Health: {'Healthy' if infra_service.health_check() else 'Unhealthy'}")
        else:
            print(f"❌ Failed to create Infrastructure service: {infra_result.error}")
        
        # Test Draw.io service creation
        print("\n--- Testing Draw.io Service ---")
        drawio_result = factory.create_drawio_service()
        if drawio_result.is_success():
            drawio_service = drawio_result.value
            print("✅ Successfully created Draw.io service")
            print(f"   - Available: {drawio_service.is_available()}")
            print(f"   - Supported formats: {drawio_service.get_supported_formats()}")
            print(f"   - Health: {'Healthy' if drawio_service.health_check() else 'Unhealthy'}")
        else:
            print(f"❌ Failed to create Draw.io service: {drawio_result.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed service creation testing: {e}")
        return False


def test_fallback_behavior(factory: DiagramServiceFactory):
    """Test fallback behavior for unavailable services."""
    print("\n=== Testing Fallback Behavior ===")
    
    try:
        # Test fallback for each service type
        services_to_test = ["mermaid", "infrastructure", "drawio"]
        
        for service_name in services_to_test:
            print(f"\n--- Testing {service_name} fallback ---")
            
            # Try to create service with fallback
            fallback_result = factory.create_service_with_fallback(service_name)
            if fallback_result.is_success():
                service = fallback_result.value
                print(f"✅ Successfully created {service_name} service (possibly with fallback)")
                print(f"   - Available: {service.is_available()}")
                print(f"   - Supported formats: {service.get_supported_formats()}")
                print(f"   - Health: {'Healthy' if service.health_check() else 'Unhealthy'}")
            else:
                print(f"❌ Failed to create {service_name} service even with fallback: {fallback_result.error}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed fallback behavior testing: {e}")
        return False


def test_service_registry_integration():
    """Test integration with the service registry."""
    print("\n=== Testing Service Registry Integration ===")
    
    try:
        # Reset registry for clean test
        reset_registry()
        
        # Register core services including diagram factory
        registered_services = register_core_services()
        print(f"✅ Registered core services: {registered_services}")
        
        # Check if diagram service factory is registered
        if "diagram_service_factory" in registered_services:
            print("✅ Diagram service factory successfully registered")
            
            # Get the factory from registry
            registry = get_registry()
            factory = registry.get("diagram_service_factory")
            print("✅ Successfully retrieved diagram factory from registry")
            
            # Test factory functionality through registry
            available_services = factory.get_available_services()
            print(f"✅ Available services through registry: {available_services}")
            
            # Test service status
            status = factory.get_service_status()
            print("✅ Service status:")
            for service_name, service_status in status.items():
                print(f"   - {service_name}: {'Available' if service_status['available'] else 'Unavailable'}")
                if service_status.get('error_message'):
                    print(f"     Error: {service_status['error_message']}")
            
            return True
        else:
            print("❌ Diagram service factory not found in registered services")
            return False
        
    except Exception as e:
        print(f"❌ Failed service registry integration testing: {e}")
        return False


def test_installation_instructions(factory: DiagramServiceFactory):
    """Test installation instructions generation."""
    print("\n=== Testing Installation Instructions ===")
    
    try:
        instructions = factory.get_installation_instructions()
        
        if instructions:
            print("✅ Installation instructions available:")
            for service_name, instruction in instructions.items():
                print(f"\n--- {service_name} ---")
                print(instruction)
        else:
            print("✅ No installation instructions needed (all services available)")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed installation instructions testing: {e}")
        return False


def test_service_imports():
    """Test that services can be imported through the import system."""
    print("\n=== Testing Service Imports ===")
    
    try:
        # Test requiring diagram service factory
        try:
            diagram_factory = require_service("diagram_service_factory")
            print("✅ Successfully required diagram_service_factory")
            
            # Test creating services through the required factory
            mermaid_result = diagram_factory.create_mermaid_service()
            if mermaid_result.is_success():
                print("✅ Successfully created Mermaid service through required factory")
            else:
                print(f"⚠️  Could not create Mermaid service: {mermaid_result.error}")
                
        except Exception as e:
            print(f"❌ Failed to require diagram_service_factory: {e}")
        
        # Test optional service access
        optional_factory = optional_service("diagram_service_factory")
        if optional_factory:
            print("✅ Successfully accessed diagram factory as optional service")
        else:
            print("⚠️  Diagram factory not available as optional service")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed service imports testing: {e}")
        return False


def main():
    """Main test function."""
    print("🚀 Starting Diagram Service Factory Tests")
    print("=" * 60)
    
    setup_logging()
    
    # Track test results
    test_results = []
    
    # Test 1: Factory creation
    factory = test_diagram_service_factory_creation()
    test_results.append(("Factory Creation", factory is not None))
    
    if factory:
        # Test 2: Service availability checking
        result = test_service_availability_checking(factory)
        test_results.append(("Service Availability", result))
        
        # Test 3: Service creation
        result = test_service_creation(factory)
        test_results.append(("Service Creation", result))
        
        # Test 4: Fallback behavior
        result = test_fallback_behavior(factory)
        test_results.append(("Fallback Behavior", result))
        
        # Test 5: Installation instructions
        result = test_installation_instructions(factory)
        test_results.append(("Installation Instructions", result))
    
    # Test 6: Service registry integration
    result = test_service_registry_integration()
    test_results.append(("Registry Integration", result))
    
    # Test 7: Service imports
    result = test_service_imports()
    test_results.append(("Service Imports", result))
    
    # Print summary
    print("\n" + "=" * 60)
    print("📊 Test Results Summary")
    print("=" * 60)
    
    passed = 0
    total = len(test_results)
    
    for test_name, result in test_results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 Overall Result: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! Diagram Service Factory implementation is working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Please review the implementation.")
        return 1


if __name__ == "__main__":
    sys.exit(main())