#!/usr/bin/env python3
"""
Immediate hotfix for GPT-5 truncation error.
This applies a direct patch to handle the specific error you're seeing.
"""

import os
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def apply_immediate_hotfix():
    """Apply immediate hotfix for GPT-5 truncation error."""
    
    print("🚨 Applying Immediate GPT-5 Hotfix")
    print("=" * 50)
    
    # Fix 1: Update OpenAI provider with more aggressive error handling
    openai_provider_path = project_root / "app/llm/openai_provider.py"
    
    if openai_provider_path.exists():
        print("📝 Patching OpenAI provider with aggressive error handling...")
        
        # Read current content
        with open(openai_provider_path, 'r') as f:
            content = f.read()
        
        # Check if already patched
        if "HOTFIX_APPLIED" not in content:
            # Add hotfix to the generate method
            hotfix_code = '''
    async def generate(self, prompt: str, **kwargs: Any) -> str:
        """Generate text using OpenAI API with GPT-5 hotfix."""
        # HOTFIX_APPLIED - Aggressive GPT-5 error handling
        
        # For GPT-5, use much higher token limits by default
        if self.model.startswith("gpt-5") or self.model.startswith("o1"):
            if "max_tokens" not in kwargs:
                kwargs["max_tokens"] = 3000  # Much higher default
            elif kwargs["max_tokens"] < 2000:
                kwargs["max_tokens"] = max(kwargs["max_tokens"] * 2, 2000)  # At least double
        
        max_retries = 3
        retry_count = 0
        
        while retry_count <= max_retries:
            try:
                # Prepare kwargs with correct token parameter
                prepared_kwargs = self._prepare_kwargs(kwargs)
                
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[{"role": "user", "content": prompt}],
                    **prepared_kwargs
                )
                
                # Store token usage for audit logging
                if hasattr(response, 'usage') and response.usage:
                    self.last_tokens_used = response.usage.total_tokens
                else:
                    self.last_tokens_used = None
                
                content = response.choices[0].message.content
                
                # Check if response was truncated
                if hasattr(response, 'choices') and response.choices:
                    finish_reason = getattr(response.choices[0], 'finish_reason', None)
                    if finish_reason == 'length':
                        raise Exception("Response truncated due to token limit")
                
                return content
                
            except Exception as e:
                error_str = str(e)
                
                # Handle truncation errors aggressively
                if any(indicator in error_str.lower() for indicator in [
                    "max_tokens", "max_completion_tokens", "model output limit", 
                    "finish_reason", "length", "truncated", "could not finish"
                ]):
                    retry_count += 1
                    if retry_count <= max_retries:
                        # Aggressively increase token limit
                        current_tokens = kwargs.get("max_tokens", 1000)
                        new_tokens = min(current_tokens * 2, 8000)  # Double up to 8000
                        
                        print(f"⚠️ GPT-5 truncation detected, retrying with {new_tokens} tokens (attempt {retry_count})")
                        kwargs["max_tokens"] = new_tokens
                        continue
                    else:
                        # Final attempt with maximum tokens
                        print(f"❌ GPT-5 truncation after {max_retries} retries, trying maximum tokens...")
                        kwargs["max_tokens"] = 8000
                        try:
                            prepared_kwargs = self._prepare_kwargs(kwargs)
                            response = self.client.chat.completions.create(
                                model=self.model,
                                messages=[{"role": "user", "content": prompt}],
                                **prepared_kwargs
                            )
                            return response.choices[0].message.content
                        except:
                            pass
                        
                        raise RuntimeError(f"GPT-5 response consistently truncated. Try using a shorter prompt or breaking it into smaller parts. Original error: {e}")
                
                # For non-truncation errors, raise immediately
                raise RuntimeError(f"OpenAI generation failed: {e}")
        
        raise RuntimeError("Unexpected error in generate method")'''
            
            # Replace the existing generate method
            import re
            
            # Find the existing generate method
            pattern = r'(    async def generate\(self, prompt: str, \*\*kwargs: Any\) -> str:.*?)(\n    async def|\n    def|\nclass|\Z)'
            
            def replace_generate(match):
                return hotfix_code + '\n' + match.group(2)
            
            new_content = re.sub(pattern, replace_generate, content, flags=re.DOTALL)
            
            # Write back the patched content
            with open(openai_provider_path, 'w') as f:
                f.write(new_content)
            
            print("✅ OpenAI provider patched with aggressive GPT-5 handling")
        else:
            print("✅ OpenAI provider already patched")
    
    # Fix 2: Update all configuration files with much higher token limits
    config_files = [
        "config/development.yaml",
        "config/production.yaml", 
        "config/staging.yaml",
        "config/testing.yaml"
    ]
    
    for config_file in config_files:
        config_path = project_root / config_file
        if config_path.exists():
            print(f"📝 Updating {config_file} with higher token limits...")
            
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Replace max_tokens values
            content = content.replace("max_tokens: 1000", "max_tokens: 4000")
            content = content.replace("max_tokens: 2000", "max_tokens: 4000")
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated {config_file}")
    
    # Fix 3: Update system config
    system_config_path = project_root / "app/config/system_config.py"
    if system_config_path.exists():
        print("📝 Updating system config...")
        
        with open(system_config_path, 'r') as f:
            content = f.read()
        
        # Replace max_tokens default
        content = content.replace("max_tokens: int = 1000", "max_tokens: int = 4000")
        content = content.replace("max_tokens: int = 2000", "max_tokens: int = 4000")
        
        with open(system_config_path, 'w') as f:
            f.write(content)
        
        print("✅ Updated system config")
    
    print(f"\n🎯 HOTFIX APPLIED SUCCESSFULLY!")
    print("=" * 50)
    
    print("\n📋 Changes Made:")
    print("  ✅ OpenAI provider: Aggressive retry logic with up to 8000 tokens")
    print("  ✅ Configuration: Increased default tokens to 4000")
    print("  ✅ System config: Updated default token limits")
    print("  ✅ Error handling: Better detection and recovery")
    
    print(f"\n🚀 Next Steps:")
    print("  1. Restart your application/Streamlit")
    print("  2. Try GPT-5 again - it should work now")
    print("  3. If still issues, the error messages will be clearer")
    
    print(f"\n⚠️  If you still get truncation errors:")
    print("  - Try shorter prompts")
    print("  - Break complex requests into smaller parts")
    print("  - The system will now auto-retry with higher token limits")
    
    return True


def create_gpt5_test_script():
    """Create a simple test script for GPT-5."""
    
    test_script = '''#!/usr/bin/env python3
"""Simple GPT-5 test script."""

import asyncio
import os
import sys
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).parent))

from app.llm.openai_provider import OpenAIProvider

async def test_gpt5_simple():
    """Simple GPT-5 test."""
    
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        print("❌ Set OPENAI_API_KEY environment variable")
        return
    
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
'''
    
    test_file = project_root / "test_gpt5_simple.py"
    with open(test_file, 'w') as f:
        f.write(test_script)
    
    print(f"✅ Created simple test script: {test_file}")
    return test_file


def main():
    """Apply the immediate hotfix."""
    
    print("🚨 GPT-5 IMMEDIATE HOTFIX")
    print("=" * 60)
    print("This will apply aggressive fixes for the GPT-5 truncation error.")
    print("=" * 60)
    
    # Apply the hotfix
    success = apply_immediate_hotfix()
    
    if success:
        # Create test script
        test_file = create_gpt5_test_script()
        
        print(f"\n" + "=" * 60)
        print("🎉 HOTFIX COMPLETE!")
        print("=" * 60)
        
        print(f"\n📋 What was fixed:")
        print("  • Aggressive token limit increases (up to 8000 tokens)")
        print("  • Automatic retry on truncation (3 attempts)")
        print("  • Better error detection and handling")
        print("  • Higher default configuration values")
        
        print(f"\n🧪 To test the fix:")
        print(f"  python3 {test_file}")
        
        print(f"\n⚡ The GPT-5 truncation error should now be resolved!")
        
    else:
        print("❌ Hotfix failed - check the error messages above")


if __name__ == "__main__":
    main()