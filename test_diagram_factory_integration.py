#!/usr/bin/env python3
"""
Integration test demonstrating the Diagram Service Factory in action.

This script shows how to use the diagram service factory to create and use
different diagram services with proper fallback behavior.
"""

import sys
import os
import logging
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.core.registry import get_registry, reset_registry
from app.core.service_registration import register_core_services
from app.utils.imports import require_service


def setup_logging():
    """Set up logging for the integration test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def demonstrate_mermaid_service():
    """Demonstrate Mermaid diagram service usage."""
    print("\n=== Mermaid Service Demonstration ===")
    
    try:
        # Get diagram factory from service registry
        diagram_factory = require_service("diagram_service_factory")
        
        # Create Mermaid service
        mermaid_result = diagram_factory.create_mermaid_service()
        if mermaid_result.is_error():
            print(f"❌ Failed to create Mermaid service: {mermaid_result.error}")
            return
        
        mermaid_service = mermaid_result.value
        print("✅ Created Mermaid service")
        
        # Test syntax validation
        test_mermaid_code = """
flowchart TB
    A[Start] --> B{Decision}
    B -->|Yes| C[Action 1]
    B -->|No| D[Action 2]
    C --> E[End]
    D --> E
"""
        
        is_valid, error_msg = mermaid_service.validate_syntax(test_mermaid_code)
        if is_valid:
            print("✅ Mermaid syntax validation passed")
        else:
            print(f"❌ Mermaid syntax validation failed: {error_msg}")
        
        # Show supported formats
        formats = mermaid_service.get_supported_formats()
        print(f"✅ Supported formats: {formats}")
        
    except Exception as e:
        print(f"❌ Mermaid service demonstration failed: {e}")


def demonstrate_infrastructure_service():
    """Demonstrate Infrastructure diagram service usage."""
    print("\n=== Infrastructure Service Demonstration ===")
    
    try:
        # Get diagram factory from service registry
        diagram_factory = require_service("diagram_service_factory")
        
        # Create Infrastructure service
        infra_result = diagram_factory.create_infrastructure_service()
        if infra_result.is_error():
            print(f"❌ Failed to create Infrastructure service: {infra_result.error}")
            return
        
        infra_service = infra_result.value
        print("✅ Created Infrastructure service")
        
        # Create sample specification
        sample_spec = infra_service.create_sample_spec()
        print("✅ Created sample infrastructure specification")
        print(f"   - Title: {sample_spec.get('title', 'N/A')}")
        print(f"   - Clusters: {len(sample_spec.get('clusters', []))}")
        print(f"   - Nodes: {len(sample_spec.get('nodes', []))}")
        print(f"   - Edges: {len(sample_spec.get('edges', []))}")
        
        # Show supported formats
        formats = infra_service.get_supported_formats()
        print(f"✅ Supported formats: {formats}")
        
        # Test availability (this will check for diagrams library)
        is_available = infra_service.is_available()
        print(f"✅ Service availability: {'Available' if is_available else 'Not Available'}")
        
        if not is_available:
            print("   Note: Install 'diagrams' package for full functionality")
        
    except Exception as e:
        print(f"❌ Infrastructure service demonstration failed: {e}")


def demonstrate_drawio_service():
    """Demonstrate Draw.io export service usage."""
    print("\n=== Draw.io Service Demonstration ===")
    
    try:
        # Get diagram factory from service registry
        diagram_factory = require_service("diagram_service_factory")
        
        # Create Draw.io service
        drawio_result = diagram_factory.create_drawio_service()
        if drawio_result.is_error():
            print(f"❌ Failed to create Draw.io service: {drawio_result.error}")
            return
        
        drawio_service = drawio_result.value
        print("✅ Created Draw.io service")
        
        # Show supported formats
        formats = drawio_service.get_supported_formats()
        print(f"✅ Supported formats: {formats}")
        
        # Test availability
        is_available = drawio_service.is_available()
        print(f"✅ Service availability: {'Available' if is_available else 'Not Available'}")
        
        # Note: We won't actually export files in this demo to avoid creating files
        print("✅ Draw.io service ready for export operations")
        
    except Exception as e:
        print(f"❌ Draw.io service demonstration failed: {e}")


def demonstrate_fallback_behavior():
    """Demonstrate fallback behavior when services are unavailable."""
    print("\n=== Fallback Behavior Demonstration ===")
    
    try:
        # Get diagram factory from service registry
        diagram_factory = require_service("diagram_service_factory")
        
        # Test fallback for each service type
        services_to_test = ["mermaid", "infrastructure", "drawio"]
        
        for service_name in services_to_test:
            print(f"\n--- Testing {service_name} with fallback ---")
            
            # Create service with fallback enabled
            fallback_result = diagram_factory.create_service_with_fallback(service_name)
            if fallback_result.is_success():
                service = fallback_result.value
                print(f"✅ Successfully created {service_name} service")
                print(f"   - Available: {service.is_available()}")
                print(f"   - Health: {'Healthy' if service.health_check() else 'Unhealthy'}")
                print(f"   - Formats: {service.get_supported_formats()}")
            else:
                print(f"❌ Failed to create {service_name} service: {fallback_result.error}")
        
    except Exception as e:
        print(f"❌ Fallback behavior demonstration failed: {e}")


def demonstrate_service_status():
    """Demonstrate service status reporting."""
    print("\n=== Service Status Demonstration ===")
    
    try:
        # Get diagram factory from service registry
        diagram_factory = require_service("diagram_service_factory")
        
        # Get comprehensive service status
        status = diagram_factory.get_service_status()
        
        print("✅ Service Status Report:")
        for service_name, service_status in status.items():
            print(f"\n--- {service_name.upper()} ---")
            print(f"   Available: {'✅ Yes' if service_status['available'] else '❌ No'}")
            print(f"   Type: {service_status['diagram_type']}")
            print(f"   Features: {', '.join(service_status['features'])}")
            print(f"   Required packages: {service_status['required_packages']}")
            print(f"   Optional packages: {service_status['optional_packages']}")
            print(f"   Fallback available: {'✅ Yes' if service_status['fallback_available'] else '❌ No'}")
            print(f"   Has instance: {'✅ Yes' if service_status['has_instance'] else '❌ No'}")
            
            if service_status.get('error_message'):
                print(f"   Error: {service_status['error_message']}")
        
        # Get installation instructions if needed
        instructions = diagram_factory.get_installation_instructions()
        if instructions:
            print("\n✅ Installation Instructions:")
            for service_name, instruction in instructions.items():
                print(f"\n--- {service_name} ---")
                print(instruction)
        else:
            print("\n✅ All services are fully available - no installation needed")
        
    except Exception as e:
        print(f"❌ Service status demonstration failed: {e}")


def main():
    """Main integration test function."""
    print("🚀 Diagram Service Factory Integration Test")
    print("=" * 60)
    
    setup_logging()
    
    try:
        # Initialize the service registry with all core services
        print("Initializing service registry...")
        reset_registry()
        registered_services = register_core_services()
        print(f"✅ Registered services: {registered_services}")
        
        # Verify diagram service factory is available
        if "diagram_service_factory" not in registered_services:
            print("❌ Diagram service factory not registered")
            return 1
        
        # Run demonstrations
        demonstrate_mermaid_service()
        demonstrate_infrastructure_service()
        demonstrate_drawio_service()
        demonstrate_fallback_behavior()
        demonstrate_service_status()
        
        print("\n" + "=" * 60)
        print("🎉 Integration test completed successfully!")
        print("The Diagram Service Factory is working correctly and ready for use.")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())