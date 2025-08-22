#!/usr/bin/env python3
"""Test script to verify the provider config fix."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.api import ProviderConfig

def test_bedrock_with_aws_credentials():
    """Test Bedrock provider config with AWS credentials (no API key)."""
    print("Testing Bedrock with AWS credentials...")
    
    try:
        config = ProviderConfig(
            provider="bedrock",
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            api_key=None,  # No API key for AWS credentials
            region="us-east-1",
            aws_access_key_id="AKIA...",
            aws_secret_access_key="secret...",
            aws_session_token=None
        )
        print("✅ SUCCESS: Bedrock config with AWS credentials created successfully")
        print(f"   Provider: {config.provider}")
        print(f"   Model: {config.model}")
        print(f"   API Key: {config.api_key}")
        print(f"   Region: {config.region}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_bedrock_with_api_key():
    """Test Bedrock provider config with API key."""
    print("\nTesting Bedrock with API key...")
    
    try:
        config = ProviderConfig(
            provider="bedrock",
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            api_key="test-api-key-123",
            region="us-east-1"
        )
        print("✅ SUCCESS: Bedrock config with API key created successfully")
        print(f"   Provider: {config.provider}")
        print(f"   Model: {config.model}")
        print(f"   API Key: {config.api_key}")
        print(f"   Region: {config.region}")
        return True
    except Exception as e:
        print(f"❌ FAILED: {e}")
        return False

def test_bedrock_with_empty_api_key():
    """Test Bedrock provider config with empty API key (should fail)."""
    print("\nTesting Bedrock with empty API key...")
    
    try:
        config = ProviderConfig(
            provider="bedrock",
            model="anthropic.claude-3-sonnet-20240229-v1:0",
            api_key="",  # Empty string should fail
            region="us-east-1"
        )
        print("❌ UNEXPECTED: Empty API key should have failed but didn't")
        return False
    except Exception as e:
        print(f"✅ EXPECTED FAILURE: {e}")
        return True

if __name__ == "__main__":
    print("Testing Provider Config Fixes")
    print("=" * 50)
    
    results = []
    results.append(test_bedrock_with_aws_credentials())
    results.append(test_bedrock_with_api_key())
    results.append(test_bedrock_with_empty_api_key())
    
    print("\n" + "=" * 50)
    print(f"Results: {sum(results)}/{len(results)} tests passed")
    
    if all(results):
        print("🎉 All tests passed! The fix is working correctly.")
    else:
        print("⚠️  Some tests failed. The fix may need more work.")