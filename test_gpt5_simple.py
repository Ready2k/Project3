#!/usr/bin/env python3
"""Simple GPT-5 test script."""

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

from app.llm.openai_provider import OpenAIProvider

async def test_gpt5_simple():
    """Simple GPT-5 test."""
    
    # Load environment variables
    load_env_file()
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ OPENAI_API_KEY not found in environment or localdev.env")
        print("💡 Make sure your API key is set in localdev.env file")
        return
    
    print(f"✅ API key found: {api_key[:20]}...")
    
    print("🧪 Testing GPT-5 with hotfix...")
    
    try:
        provider = OpenAIProvider(api_key=api_key, model="gpt-5")
        
        # Test with a simple prompt
        response = await provider.generate("Explain AI in one sentence.", max_tokens=100)
        print(f"✅ GPT-5 Response: {response}")
        
    except Exception as e:
        print(f"❌ GPT-5 Test Failed: {e}")
        
        # Provide specific guidance
        if "max_tokens" in str(e) or "truncated" in str(e):
            print("💡 Try increasing max_tokens or using shorter prompts")
        elif "not found" in str(e):
            print("💡 GPT-5 may not be available in your account yet")
        else:
            print("💡 Check your API key and network connection")

if __name__ == "__main__":
    asyncio.run(test_gpt5_simple())
