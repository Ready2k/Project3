#!/usr/bin/env python3
"""Test script for LLM provider connections."""

import asyncio
import sys
from app.llm.openai_provider import OpenAIProvider

async def test_openai_provider():
    """Test OpenAI provider with different scenarios."""
    
    print("🧪 Testing OpenAI Provider")
    print("=" * 50)
    
    # Test 1: Invalid API key
    print("\n1. Testing with invalid API key...")
    provider = OpenAIProvider(api_key="invalid-key", model="gpt-4o")
    success, error_msg = await provider.test_connection_detailed()
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if not success:
        print(f"   Error: {error_msg}")
    
    # Test 2: Invalid model
    print("\n2. Testing with invalid model...")
    provider = OpenAIProvider(api_key="sk-fake", model="gpt-5")
    success, error_msg = await provider.test_connection_detailed()
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if not success:
        print(f"   Error: {error_msg}")
    
    # Test 3: Valid format but fake key
    print("\n3. Testing with valid format but fake key...")
    provider = OpenAIProvider(api_key="sk-" + "x" * 48, model="gpt-4o")
    success, error_msg = await provider.test_connection_detailed()
    print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
    if not success:
        print(f"   Error: {error_msg}")
    
    print("\n" + "=" * 50)
    print("💡 To test with a real API key, set OPENAI_API_KEY environment variable")
    print("   and run: python3 test_provider.py <your-api-key>")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # Test with provided API key
        api_key = sys.argv[1]
        print(f"\n4. Testing with provided API key...")
        
        async def test_real_key():
            provider = OpenAIProvider(api_key=api_key, model="gpt-4o")
            success, error_msg = await provider.test_connection_detailed()
            print(f"   Result: {'✅ Success' if success else '❌ Failed'}")
            if not success:
                print(f"   Error: {error_msg}")
            else:
                print("   ✅ Your API key works correctly!")
        
        asyncio.run(test_real_key())
    else:
        asyncio.run(test_openai_provider())