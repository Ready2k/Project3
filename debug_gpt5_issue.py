#!/usr/bin/env python3
"""
Debug script to identify where the GPT-5 max_tokens issue is occurring.
"""

import asyncio
import os
from app.llm.openai_provider import OpenAIProvider
from app.api import create_llm_provider, ProviderConfig


async def debug_gpt5_issue():
    """Debug the GPT-5 max_tokens issue step by step."""
    
    print("🔍 Debugging GPT-5 max_tokens Issue")
    print("=" * 50)
    
    # Check if API key is available
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment")
        print("   Set your OpenAI API key to debug the issue")
        return False
    
    print(f"✅ API key found: {api_key[:10]}...")
    
    # Test 1: Direct OpenAI Provider with GPT-5
    print(f"\n🧪 Test 1: Direct OpenAI Provider with GPT-5")
    print("-" * 40)
    
    try:
        provider = OpenAIProvider(api_key=api_key, model="gpt-5")
        
        # Test parameter detection
        token_param = provider._get_token_parameter()
        print(f"Token parameter detected: {token_param}")
        
        # Test kwargs preparation
        test_kwargs = {"max_tokens": 50, "temperature": 0.7}
        prepared_kwargs = provider._prepare_kwargs(test_kwargs)
        print(f"Original kwargs: {test_kwargs}")
        print(f"Prepared kwargs: {prepared_kwargs}")
        
        # Test actual generation
        print("Testing generation with max_tokens=50...")
        try:
            response = await provider.generate("Say hello", max_tokens=50)
            print(f"✅ Success: {response[:100]}...")
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            if "max_tokens" in str(e):
                print("   🚨 This is the max_tokens parameter error!")
                return False
    
    except Exception as e:
        print(f"❌ Provider creation failed: {e}")
        return False
    
    # Test 2: Through create_llm_provider function
    print(f"\n🧪 Test 2: Through create_llm_provider function")
    print("-" * 40)
    
    try:
        config = ProviderConfig(
            provider="openai",
            model="gpt-5",
            api_key=api_key,
            temperature=0.7,
            max_tokens=50
        )
        
        print(f"Provider config: {config.model_dump()}")
        
        llm_provider = create_llm_provider(config, "debug-session")
        
        # Check if it's wrapped
        print(f"Provider type: {type(llm_provider)}")
        print(f"Underlying provider type: {type(llm_provider.provider) if hasattr(llm_provider, 'provider') else 'N/A'}")
        
        # Test generation through the wrapper
        print("Testing generation through wrapper...")
        try:
            response = await llm_provider.generate("Say hello", max_tokens=50)
            print(f"✅ Success: {response[:100]}...")
        except Exception as e:
            print(f"❌ Generation failed: {e}")
            if "max_tokens" in str(e):
                print("   🚨 This is where the max_tokens error occurs!")
                
                # Check if the underlying provider has our fix
                if hasattr(llm_provider, 'provider'):
                    underlying = llm_provider.provider
                    if hasattr(underlying, '_prepare_kwargs'):
                        print("   ✅ Underlying provider has _prepare_kwargs method")
                        test_prepared = underlying._prepare_kwargs({"max_tokens": 50})
                        print(f"   Underlying preparation result: {test_prepared}")
                    else:
                        print("   ❌ Underlying provider missing _prepare_kwargs method")
                
                return False
    
    except Exception as e:
        print(f"❌ create_llm_provider failed: {e}")
        return False
    
    # Test 3: Check configuration defaults
    print(f"\n🧪 Test 3: Check Configuration Defaults")
    print("-" * 40)
    
    try:
        from app.services.configuration_service import get_config
        config_service = get_config()
        llm_params = config_service.get_llm_params()
        print(f"Default LLM params: {llm_params}")
        
        if 'max_tokens' in llm_params:
            print(f"Default max_tokens value: {llm_params['max_tokens']}")
    except Exception as e:
        print(f"Configuration check failed: {e}")
    
    # Test 4: Check if there are any hardcoded defaults
    print(f"\n🧪 Test 4: Check OpenAI Client Direct Call")
    print("-" * 40)
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        # Try the old parameter
        print("Testing direct OpenAI client with max_tokens...")
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": "Say hello"}],
                max_tokens=50
            )
            print("✅ Direct client with max_tokens worked (unexpected)")
        except Exception as e:
            print(f"❌ Direct client with max_tokens failed: {e}")
            if "max_tokens" in str(e) and "max_completion_tokens" in str(e):
                print("   ✅ This confirms GPT-5 needs max_completion_tokens")
        
        # Try the new parameter
        print("Testing direct OpenAI client with max_completion_tokens...")
        try:
            response = client.chat.completions.create(
                model="gpt-5",
                messages=[{"role": "user", "content": "Say hello"}],
                max_completion_tokens=50
            )
            print(f"✅ Direct client with max_completion_tokens worked: {response.choices[0].message.content[:50]}...")
        except Exception as e:
            print(f"❌ Direct client with max_completion_tokens failed: {e}")
    
    except Exception as e:
        print(f"Direct client test failed: {e}")
    
    print(f"\n" + "=" * 50)
    print("🎯 DEBUGGING COMPLETE")
    
    return True


async def test_parameter_conversion_detailed():
    """Test parameter conversion with detailed logging."""
    
    print(f"\n🔧 Detailed Parameter Conversion Test")
    print("-" * 40)
    
    # Test with fake API key for logic testing
    provider = OpenAIProvider(api_key="fake-key", model="gpt-5")
    
    test_cases = [
        {"max_tokens": 100},
        {"max_tokens": 200, "temperature": 0.7},
        {"temperature": 0.5},  # No max_tokens
        {"max_completion_tokens": 150},  # Already correct parameter
    ]
    
    for i, kwargs in enumerate(test_cases, 1):
        print(f"\nTest case {i}: {kwargs}")
        
        # Test parameter detection
        token_param = provider._get_token_parameter()
        print(f"  Token parameter for {provider.model}: {token_param}")
        
        # Test kwargs preparation
        prepared = provider._prepare_kwargs(kwargs)
        print(f"  Original: {kwargs}")
        print(f"  Prepared: {prepared}")
        
        # Validate conversion
        if "max_tokens" in kwargs and token_param == "max_completion_tokens":
            if "max_completion_tokens" in prepared and "max_tokens" not in prepared:
                print(f"  ✅ Conversion successful")
            else:
                print(f"  ❌ Conversion failed")
        elif "max_tokens" in kwargs and token_param == "max_tokens":
            if "max_tokens" in prepared and "max_completion_tokens" not in prepared:
                print(f"  ✅ Preservation successful")
            else:
                print(f"  ❌ Preservation failed")
        else:
            print(f"  ✅ No conversion needed")


async def main():
    """Run all debugging tests."""
    
    # Test parameter conversion logic (doesn't need real API key)
    await test_parameter_conversion_detailed()
    
    # Test actual API calls (needs real API key)
    await debug_gpt5_issue()


if __name__ == "__main__":
    asyncio.run(main())