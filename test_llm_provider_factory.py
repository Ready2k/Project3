#!/usr/bin/env python3
"""
Test script for LLM Provider Factory implementation.

This script tests the LLM provider factory functionality including:
- Provider availability checking
- Factory pattern implementation
- Graceful fallback behavior
- Service registry integration
"""

import asyncio
import os
import sys
import logging
from typing import Dict, Any

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '.'))

from app.core.registry import get_registry, reset_registry
from app.core.service_registration import register_core_services
from app.llm.factory import LLMProviderFactory, ProviderType
from app.llm.base import LLMProvider


def setup_logging():
    """Set up logging for the test."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )


def test_provider_factory_creation():
    """Test basic factory creation and configuration."""
    print("\n=== Testing LLM Provider Factory Creation ===")
    
    config = {
        "default_provider": "fake",
        "fallback_providers": ["fake"],
        "timeout_seconds": 30,
        "max_retries": 3
    }
    
    factory = LLMProviderFactory(config)
    
    # Test basic properties
    assert factory.name == "llm_provider_factory"
    assert factory.get_config("default_provider") == "fake"
    assert factory.get_config("timeout_seconds") == 30
    
    print("✅ Factory creation test passed")


def test_provider_availability_checking():
    """Test provider availability checking."""
    print("\n=== Testing Provider Availability Checking ===")
    
    config = {
        "default_provider": "fake",
        "fallback_providers": ["fake"]
    }
    
    factory = LLMProviderFactory(config)
    factory.initialize()
    
    # Check available providers
    available_providers = factory.get_available_providers()
    print(f"Available providers: {available_providers}")
    
    # Fake provider should always be available
    assert "fake" in available_providers
    assert factory.is_provider_available("fake")
    
    # Check provider info
    fake_info = factory.get_provider_info("fake")
    assert fake_info is not None
    assert fake_info.provider_type == ProviderType.FAKE
    assert fake_info.is_available
    
    print("✅ Provider availability checking test passed")


async def test_provider_creation():
    """Test provider instance creation."""
    print("\n=== Testing Provider Creation ===")
    
    config = {
        "default_provider": "fake",
        "fallback_providers": ["fake"]
    }
    
    factory = LLMProviderFactory(config)
    factory.initialize()
    
    # Test creating fake provider
    result = factory.create_provider("fake")
    assert result.is_success(), f"Failed to create fake provider: {result.error if result.is_error() else 'Unknown error'}"
    
    provider = result.value
    assert isinstance(provider, LLMProvider)
    
    # Test provider functionality
    response = await provider.generate("Hello, world!")
    assert isinstance(response, str)
    assert len(response) > 0
    
    # Test connection
    connection_ok = await provider.test_connection()
    assert connection_ok
    
    # Test model info
    model_info = provider.get_model_info()
    assert isinstance(model_info, dict)
    assert model_info["provider"] == "fake"
    
    print("✅ Provider creation test passed")


async def test_fallback_behavior():
    """Test graceful fallback behavior."""
    print("\n=== Testing Fallback Behavior ===")
    
    config = {
        "default_provider": "nonexistent",
        "fallback_providers": ["fake"]
    }
    
    factory = LLMProviderFactory(config)
    factory.initialize()
    
    # Test fallback when preferred provider is not available
    result = factory.create_provider_with_fallback("nonexistent")
    assert result.is_success(), f"Fallback failed: {result.error if result.is_error() else 'Unknown error'}"
    
    provider = result.value
    model_info = provider.get_model_info()
    assert model_info["provider"] == "fake"  # Should have fallen back to fake
    
    print("✅ Fallback behavior test passed")


def test_service_registry_integration():
    """Test integration with service registry."""
    print("\n=== Testing Service Registry Integration ===")
    
    # Reset registry for clean test
    reset_registry()
    registry = get_registry()
    
    # Register core services (including LLM factory)
    registered_services = register_core_services()
    assert "llm_provider_factory" in registered_services
    
    # Get factory from registry
    factory = registry.get("llm_provider_factory")
    assert isinstance(factory, LLMProviderFactory)
    
    # Test factory health check
    health_status = registry.health_check("llm_provider_factory")
    print(f"Health status: {health_status}")
    
    # Initialize the factory first
    factory.initialize()
    health_status = registry.health_check("llm_provider_factory")
    print(f"Health status after initialization: {health_status}")
    assert health_status["llm_provider_factory"] is True
    
    print("✅ Service registry integration test passed")


async def test_provider_status():
    """Test provider status reporting."""
    print("\n=== Testing Provider Status Reporting ===")
    
    config = {
        "default_provider": "fake",
        "fallback_providers": ["fake"]
    }
    
    factory = LLMProviderFactory(config)
    factory.initialize()
    
    # Get provider status
    status = factory.get_provider_status()
    assert isinstance(status, dict)
    
    # Check fake provider status
    fake_status = status.get("fake")
    assert fake_status is not None
    assert fake_status["available"] is True
    assert fake_status["provider_type"] == "fake"
    assert fake_status["error_message"] is None
    
    # Check other providers (should be unavailable without proper setup)
    for provider_name in ["openai", "anthropic", "bedrock"]:
        provider_status = status.get(provider_name)
        if provider_status:
            print(f"Provider {provider_name}: available={provider_status['available']}, error={provider_status.get('error_message', 'None')}")
    
    print("✅ Provider status reporting test passed")


async def test_provider_testing():
    """Test provider connection testing."""
    print("\n=== Testing Provider Connection Testing ===")
    
    config = {
        "default_provider": "fake",
        "fallback_providers": ["fake"]
    }
    
    factory = LLMProviderFactory(config)
    factory.initialize()
    
    # Test fake provider connection
    result = await factory.test_provider("fake")
    assert result.is_success(), f"Provider test failed: {result.error if result.is_error() else 'Unknown error'}"
    assert result.value is True
    
    # Test non-existent provider
    result = await factory.test_provider("nonexistent")
    assert result.is_error()
    
    print("✅ Provider connection testing test passed")


def test_configuration_handling():
    """Test configuration handling and overrides."""
    print("\n=== Testing Configuration Handling ===")
    
    base_config = {
        "default_provider": "fake",
        "timeout_seconds": 30,
        "fake_config": {
            "model": "custom-fake-model",
            "seed": 123
        }
    }
    
    factory = LLMProviderFactory(base_config)
    factory.initialize()
    
    # Test provider creation with custom config
    result = factory.create_provider("fake", model="override-model", seed=456)
    assert result.is_success()
    
    provider = result.value
    model_info = provider.get_model_info()
    
    # The model should be overridden by kwargs
    assert model_info["model"] == "override-model"
    assert model_info["seed"] == 456
    
    print("✅ Configuration handling test passed")


async def run_all_tests():
    """Run all tests."""
    print("🚀 Starting LLM Provider Factory Tests")
    
    try:
        # Synchronous tests
        test_provider_factory_creation()
        test_provider_availability_checking()
        test_service_registry_integration()
        test_configuration_handling()
        
        # Asynchronous tests
        await test_provider_creation()
        await test_fallback_behavior()
        await test_provider_status()
        await test_provider_testing()
        
        print("\n🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    setup_logging()
    
    # Run tests
    success = asyncio.run(run_all_tests())
    
    # Clean up
    reset_registry()
    
    sys.exit(0 if success else 1)