#!/usr/bin/env python3
"""Test script for LLM provider connections."""

import asyncio
import sys
from app.llm.openai_provider import OpenAIProvider
from app.utils.logger import app_logger

async def test_openai_provider():
    """Test OpenAI provider with different scenarios."""
    
    app_logger.info("🧪 Testing OpenAI Provider")
    app_logger.info("=" * 50)
    
    # Test 1: Invalid API key
    app_logger.info("1. Testing with invalid API key...")
    provider = OpenAIProvider(api_key="invalid-key", model="gpt-4o")
    success, error_msg = await provider.test_connection_detailed()
    app_logger.info(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if not success:
        app_logger.info(f"   Error: {error_msg}")
    
    # Test 2: Invalid model
    app_logger.info("2. Testing with invalid model...")
    provider = OpenAIProvider(api_key="sk-fake", model="gpt-5")
    success, error_msg = await provider.test_connection_detailed()
    app_logger.info(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if not success:
        app_logger.info(f"   Error: {error_msg}")
    
    # Test 3: Valid format but fake key
    app_logger.info("3. Testing with valid format but fake key...")
    provider = OpenAIProvider(api_key="sk-" + "x" * 48, model="gpt-4o")
    success, error_msg = await provider.test_connection_detailed()
    app_logger.info(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if not success:
        app_logger.info(f"   Error: {error_msg}")
    
    app_logger.info("=" * 50)
    app_logger.info("💡 To test with a real API key, set OPENAI_API_KEY environment variable")
    app_logger.info("   and run: python3 test_provider.py <your-api-key>")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided API key
        api_key = sys.argv[1]
        app_logger.info("4. Testing with provided API key...")
        
        async def test_real_key():
            provider = OpenAIProvider(api_key=api_key, model="gpt-4o")
            success, error_msg = await provider.test_connection_detailed()
            app_logger.info(f"   Result: {'✅ Success' if success else '❌ Failed'}")
            if not success:
                app_logger.info(f"   Error: {error_msg}")
            else:
                app_logger.info("   ✅ Your API key works correctly!")
        
        asyncio.run(test_real_key())
    else:
        asyncio.run(test_openai_provider())