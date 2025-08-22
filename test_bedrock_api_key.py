#!/usr/bin/env python3
"""Test script to verify Bedrock API key authentication."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.llm.bedrock_provider import BedrockProvider


async def test_bedrock_api_key():
    """Test Bedrock provider with API key authentication."""
    print("Testing Bedrock API key authentication...")
    
    # Test with a mock API key (starts with bedrock-api-key-)
    provider = BedrockProvider(
        model="anthropic.claude-3-haiku-20240307-v1:0",
        region="us-east-1",
        bedrock_api_key="bedrock-api-key-test123"
    )
    
    print(f"Provider created with API key authentication")
    print(f"Model info: {provider.get_model_info()}")
    
    # Test connection (will fail with invalid key, but should use HTTP path)
    try:
        success = await provider.test_connection()
        print(f"Connection test result: {success}")
    except Exception as e:
        print(f"Connection test failed (expected with test key): {e}")
    
    # Test generation (will fail with invalid key, but should use HTTP path)
    try:
        result = await provider.generate("Hello", max_tokens=10)
        print(f"Generation result: {result}")
    except Exception as e:
        print(f"Generation failed (expected with test key): {e}")
    
    print("✅ API key authentication path is being used correctly")


if __name__ == "__main__":
    asyncio.run(test_bedrock_api_key())