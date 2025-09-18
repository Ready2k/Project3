#!/usr/bin/env python3
"""
Integration test for LLM Provider Factory.

This script demonstrates how to use the LLM provider factory in a real application context.
"""

import asyncio
import os
import sys
import logging

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.registry import get_registry, reset_registry
from app.core.service_registration import register_core_services
from app.utils.imports import require_service, optional_service


async def demonstrate_llm_factory_usage():
    """Demonstrate how to use the LLM factory in practice."""
    print("🚀 LLM Provider Factory Integration Demo")
    
    # Set up logging
    logging.basicConfig(level=logging.INFO)
    
    # Reset and set up services
    reset_registry()
    register_core_services()
    
    print("\n=== Getting LLM Factory from Service Registry ===")
    
    # Get the factory using the service registry
    llm_factory = require_service("llm_provider_factory")
    print(f"✅ Got LLM factory: {llm_factory.name}")
    
    # Initialize the factory
    llm_factory.initialize()
    
    print("\n=== Checking Available Providers ===")
    
    # Check what providers are available
    available_providers = llm_factory.get_available_providers()
    print(f"Available providers: {available_providers}")
    
    # Get detailed status
    status = llm_factory.get_provider_status()
    for provider_name, provider_status in status.items():
        availability = "✅" if provider_status["available"] else "❌"
        error_msg = f" ({provider_status['error_message']})" if provider_status.get("error_message") else ""
        print(f"{availability} {provider_name}: {provider_status['provider_type']}{error_msg}")
    
    print("\n=== Creating LLM Provider with Fallback ===")
    
    # Try to create a provider with fallback
    result = llm_factory.create_provider_with_fallback("openai")  # Will fallback to available provider
    
    if result.is_success():
        provider = result.value
        model_info = provider.get_model_info()
        print(f"✅ Created provider: {model_info['provider']} ({model_info.get('model', 'unknown model')})")
        
        print("\n=== Testing Provider Functionality ===")
        
        # Test connection
        connection_ok = await provider.test_connection()
        print(f"Connection test: {'✅ OK' if connection_ok else '❌ Failed'}")
        
        # Generate some text
        test_prompts = [
            "What is artificial intelligence?",
            "Explain machine learning in simple terms.",
            "What are the benefits of using AI?"
        ]
        
        for i, prompt in enumerate(test_prompts, 1):
            print(f"\n--- Test {i}: {prompt[:50]}... ---")
            try:
                response = await provider.generate(prompt, max_tokens=100)
                print(f"Response: {response[:200]}...")
                
                # Show token usage if available
                if hasattr(provider, 'last_tokens_used') and provider.last_tokens_used:
                    print(f"Tokens used: {provider.last_tokens_used}")
                    
            except Exception as e:
                print(f"❌ Generation failed: {e}")
        
        print("\n=== Testing Multiple Provider Creation ===")
        
        # Create multiple providers to test caching
        result2 = llm_factory.create_provider_with_fallback("fake")
        if result2.is_success():
            provider2 = result2.value
            
            # Check if it's the same instance (should be cached)
            same_instance = provider is provider2
            print(f"Same instance (cached): {'✅ Yes' if same_instance else '❌ No'}")
            
            # Create with different config (should be different instance)
            result3 = llm_factory.create_provider("fake", model="different-model")
            if result3.is_success():
                provider3 = result3.value
                different_instance = provider is not provider3
                print(f"Different instance (different config): {'✅ Yes' if different_instance else '❌ No'}")
        
    else:
        print(f"❌ Failed to create provider: {result.error}")
    
    print("\n=== Testing Provider Health Monitoring ===")
    
    # Test individual provider
    if available_providers:
        test_provider = available_providers[0]
        test_result = await llm_factory.test_provider(test_provider)
        if test_result.is_success():
            print(f"✅ Provider {test_provider} health check passed")
        else:
            print(f"❌ Provider {test_provider} health check failed: {test_result.error}")
    
    # Test factory health check
    factory_healthy = llm_factory.health_check()
    print(f"Factory health: {'✅ Healthy' if factory_healthy else '❌ Unhealthy'}")
    
    print("\n=== Demonstrating Error Handling ===")
    
    # Try to create a non-existent provider
    bad_result = llm_factory.create_provider("nonexistent_provider")
    if bad_result.is_error():
        print(f"✅ Proper error handling: {bad_result.error}")
    
    # Try to test a non-existent provider
    bad_test = await llm_factory.test_provider("nonexistent_provider")
    if bad_test.is_error():
        print(f"✅ Proper test error handling: {bad_test.error}")
    
    print("\n🎉 Integration demo completed successfully!")


def demonstrate_service_usage_patterns():
    """Demonstrate different patterns for using the LLM factory."""
    print("\n=== Service Usage Patterns ===")
    
    # Pattern 1: Direct service registry access
    registry = get_registry()
    if registry.has("llm_provider_factory"):
        factory = registry.get("llm_provider_factory")
        print("✅ Pattern 1: Direct registry access")
    
    # Pattern 2: Using import utilities
    factory = require_service("llm_provider_factory")
    print("✅ Pattern 2: Using require_service utility")
    
    # Pattern 3: Optional service with fallback
    factory = optional_service("llm_provider_factory", default=None)
    if factory:
        print("✅ Pattern 3: Using optional_service utility")
    else:
        print("❌ Pattern 3: Service not available")
    
    # Pattern 4: Checking service availability
    if registry.has("llm_provider_factory"):
        print("✅ Pattern 4: Service availability check")


if __name__ == "__main__":
    try:
        # Run the integration demo
        asyncio.run(demonstrate_llm_factory_usage())
        
        # Show usage patterns
        demonstrate_service_usage_patterns()
        
        print("\n✅ All integration tests completed successfully!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
    
    finally:
        # Clean up
        reset_registry()