#!/usr/bin/env python3
"""
Comprehensive test for GPT-5 across all code paths.
"""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Load environment variables from localdev.env
def load_env_file():
    """Load environment variables from localdev.env file."""
    env_file = project_root / "localdev.env"
    if env_file.exists():
        print(f"📁 Loading environment from {env_file}")
        with open(env_file, 'r') as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#') and '=' in line:
                    key, value = line.split('=', 1)
                    os.environ[key.strip()] = value.strip()
        print("✅ Environment variables loaded")
    else:
        print(f"⚠️  Environment file not found: {env_file}")

async def test_all_gpt5_paths():
    """Test GPT-5 across all possible code paths."""
    
    print("🧪 Comprehensive GPT-5 Test Across All Code Paths")
    print("=" * 60)
    
    # Load environment
    load_env_file()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found")
        return False
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    results = []
    
    # Test 1: Direct OpenAI Provider (should use enhanced for GPT-5)
    print(f"\n🔧 Test 1: Direct OpenAI Provider")
    print("-" * 40)
    
    try:
        from app.llm.openai_provider import OpenAIProvider
        provider = OpenAIProvider(api_key=api_key, model="gpt-5")
        
        response = await provider.generate("Say hello", max_tokens=100)
        print(f"✅ Direct provider: {response[:50]}...")
        results.append(("Direct Provider", True, "Success"))
    except Exception as e:
        print(f"❌ Direct provider failed: {e}")
        results.append(("Direct Provider", False, str(e)))
    
    # Test 2: LLM Factory
    print(f"\n🏭 Test 2: LLM Factory")
    print("-" * 40)
    
    try:
        from app.llm.factory import LLMProviderFactory
        factory = LLMProviderFactory()
        
        result = factory.create_provider("openai", model="gpt-5", api_key=api_key)
        if result.is_success():
            provider = result.value
            print(f"Provider type: {type(provider).__name__}")
            
            response = await provider.generate("Say hello", max_tokens=100)
            print(f"✅ Factory provider: {response[:50]}...")
            results.append(("Factory Provider", True, "Success"))
        else:
            print(f"❌ Factory failed: {result.error}")
            results.append(("Factory Provider", False, result.error))
    except Exception as e:
        print(f"❌ Factory test failed: {e}")
        results.append(("Factory Provider", False, str(e)))
    
    # Test 3: API create_llm_provider function
    print(f"\n🌐 Test 3: API create_llm_provider")
    print("-" * 40)
    
    try:
        from app.api import create_llm_provider, ProviderConfig
        
        config = ProviderConfig(
            provider="openai",
            model="gpt-5",
            api_key=api_key,
            temperature=0.7,
            max_tokens=100
        )
        
        provider = create_llm_provider(config, "test-session")
        response = await provider.generate("Say hello", max_tokens=100)
        print(f"✅ API provider: {response[:50]}...")
        results.append(("API Provider", True, "Success"))
    except Exception as e:
        print(f"❌ API provider failed: {e}")
        results.append(("API Provider", False, str(e)))
    
    # Test 4: Enhanced GPT-5 Provider directly
    print(f"\n⚡ Test 4: Enhanced GPT-5 Provider")
    print("-" * 40)
    
    try:
        from app.llm.gpt5_enhanced_provider import GPT5EnhancedProvider
        provider = GPT5EnhancedProvider(api_key=api_key, model="gpt-5")
        
        response = await provider.generate("Say hello", max_tokens=100)
        print(f"✅ Enhanced provider: {response[:50]}...")
        results.append(("Enhanced Provider", True, "Success"))
    except Exception as e:
        print(f"❌ Enhanced provider failed: {e}")
        results.append(("Enhanced Provider", False, str(e)))
    
    # Test 5: Connection test (this might be where your error is coming from)
    print(f"\n🔗 Test 5: Connection Tests")
    print("-" * 40)
    
    try:
        from app.llm.gpt5_enhanced_provider import GPT5EnhancedProvider
        provider = GPT5EnhancedProvider(api_key=api_key, model="gpt-5")
        
        success, error = await provider.test_connection_detailed()
        if success:
            print(f"✅ Connection test: Success")
            results.append(("Connection Test", True, "Success"))
        else:
            print(f"❌ Connection test failed: {error}")
            results.append(("Connection Test", False, error))
    except Exception as e:
        print(f"❌ Connection test error: {e}")
        results.append(("Connection Test", False, str(e)))
    
    # Test 6: Test with small token limit (should trigger retry)
    print(f"\n🔄 Test 6: Small Token Limit (Retry Test)")
    print("-" * 40)
    
    try:
        from app.llm.gpt5_enhanced_provider import GPT5EnhancedProvider
        provider = GPT5EnhancedProvider(api_key=api_key, model="gpt-5")
        
        # Use a very small token limit to trigger retry logic
        response = await provider.generate(
            "Write a detailed explanation of quantum computing and its applications in modern technology", 
            max_tokens=20  # Very small - should trigger retry
        )
        print(f"✅ Retry test: {response[:50]}...")
        results.append(("Retry Logic", True, "Success"))
    except Exception as e:
        print(f"❌ Retry test failed: {e}")
        results.append(("Retry Logic", False, str(e)))
    
    # Summary
    print(f"\n" + "=" * 60)
    print("📊 COMPREHENSIVE TEST RESULTS")
    print("=" * 60)
    
    for test_name, success, message in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {test_name}")
        if not success:
            print(f"      Error: {message}")
    
    successful_tests = sum(1 for _, success, _ in results if success)
    total_tests = len(results)
    
    print(f"\n📈 Results: {successful_tests}/{total_tests} tests passed")
    
    if successful_tests == total_tests:
        print("🎉 ALL TESTS PASSED! GPT-5 is working across all code paths.")
    else:
        print("⚠️  Some tests failed. Check the errors above.")
        
        # Provide specific guidance for failed tests
        failed_tests = [name for name, success, _ in results if not success]
        if "Connection Test" in failed_tests:
            print("\n💡 Connection Test failed - this might be where your error is coming from!")
            print("   The connection test uses minimal tokens and might still hit limits.")
    
    return successful_tests == total_tests


async def main():
    """Run comprehensive GPT-5 tests."""
    await test_all_gpt5_paths()


if __name__ == "__main__":
    asyncio.run(main())