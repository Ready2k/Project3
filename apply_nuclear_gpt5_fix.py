#!/usr/bin/env python3
"""
Nuclear option: Apply the most aggressive GPT-5 fix possible.
This patches ALL possible code paths to handle GPT-5 properly.
"""

import os
import re
from pathlib import Path

def apply_nuclear_fix():
    """Apply the most aggressive GPT-5 fix to all possible locations."""
    
    print("☢️  APPLYING NUCLEAR GPT-5 FIX")
    print("=" * 50)
    print("This will aggressively patch ALL code paths to handle GPT-5")
    print("=" * 50)
    
    project_root = Path(__file__).parent
    
    # 1. Patch the base OpenAI provider to be EXTREMELY aggressive
    openai_provider_path = project_root / "app/llm/openai_provider.py"
    
    if openai_provider_path.exists():
        print("🔧 Applying nuclear patch to OpenAI provider...")
        
        with open(openai_provider_path, 'r') as f:
            content = f.read()
        
        # Add nuclear-level error handling
        nuclear_patch = '''
    def __init__(self, api_key: str, model: str = "gpt-4o"):
        self.api_key = api_key
        self.model = model
        self.client = openai.OpenAI(api_key=api_key)
        
        # NUCLEAR FIX: Force high token limits for GPT-5 family
        self.is_gpt5_family = model.startswith("gpt-5") or model.startswith("o1")
        if self.is_gpt5_family:
            print(f"🚀 NUCLEAR FIX: GPT-5 family detected ({model}), applying aggressive settings")
    
    def _get_token_parameter(self) -> str:
        """Get the appropriate token parameter based on model version."""
        # GPT-5 and newer models use max_completion_tokens
        if self.model.startswith("gpt-5") or self.model.startswith("o1"):
            return "max_completion_tokens"
        # Older models use max_tokens
        return "max_tokens"
    
    def _prepare_kwargs(self, kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare kwargs with correct token parameter."""
        prepared_kwargs = kwargs.copy()
        
        # NUCLEAR FIX: For GPT-5, always use high token limits
        if self.is_gpt5_family:
            if "max_tokens" not in prepared_kwargs:
                prepared_kwargs["max_tokens"] = 4000  # Very high default
            elif prepared_kwargs["max_tokens"] < 2000:
                prepared_kwargs["max_tokens"] = max(prepared_kwargs["max_tokens"] * 3, 2000)
                print(f"🚀 NUCLEAR FIX: Increased tokens to {prepared_kwargs['max_tokens']}")
        
        # Handle token parameter conversion
        if "max_tokens" in prepared_kwargs:
            token_param = self._get_token_parameter()
            if token_param == "max_completion_tokens":
                # Convert max_tokens to max_completion_tokens for newer models
                prepared_kwargs["max_completion_tokens"] = prepared_kwargs.pop("max_tokens")
                print(f"🚀 NUCLEAR FIX: Converted to max_completion_tokens: {prepared_kwargs['max_completion_tokens']}")
        
        return prepared_kwargs'''
        
        # Replace the __init__ and helper methods
        # First, find and replace __init__
        init_pattern = r'(    def __init__\(self, api_key: str, model: str = "gpt-4o"\):.*?)(\n    def)'
        
        def replace_init(match):
            return nuclear_patch + '\n' + match.group(2)
        
        content = re.sub(init_pattern, replace_init, content, flags=re.DOTALL)
        
        # Write back
        with open(openai_provider_path, 'w') as f:
            f.write(content)
        
        print("✅ Nuclear patch applied to OpenAI provider")
    
    # 2. Create a global monkey patch for ALL OpenAI calls
    monkey_patch_file = project_root / "app/llm/gpt5_monkey_patch.py"
    
    monkey_patch_code = '''"""
Global monkey patch for GPT-5 compatibility.
This patches the OpenAI library itself to handle GPT-5 automatically.
"""

import openai
from typing import Any, Dict

# Store original method
_original_create = None

def gpt5_aware_create(self, **kwargs):
    """Monkey-patched create method that handles GPT-5 automatically."""
    
    # Get model from kwargs
    model = kwargs.get("model", "")
    
    # If it's GPT-5 family, apply aggressive fixes
    if model.startswith("gpt-5") or model.startswith("o1"):
        print(f"🚀 MONKEY PATCH: GPT-5 detected ({model}), applying fixes")
        
        # Ensure high token limits
        if "max_tokens" in kwargs:
            if kwargs["max_tokens"] < 2000:
                kwargs["max_tokens"] = max(kwargs["max_tokens"] * 3, 2000)
                print(f"🚀 MONKEY PATCH: Increased max_tokens to {kwargs['max_tokens']}")
            
            # Convert parameter for GPT-5
            kwargs["max_completion_tokens"] = kwargs.pop("max_tokens")
            print(f"🚀 MONKEY PATCH: Converted to max_completion_tokens: {kwargs['max_completion_tokens']}")
        
        elif "max_completion_tokens" not in kwargs:
            # No token limit specified, use high default
            kwargs["max_completion_tokens"] = 4000
            print(f"🚀 MONKEY PATCH: Set default max_completion_tokens: 4000")
    
    # Call original method
    return _original_create(self, **kwargs)

def apply_monkey_patch():
    """Apply the monkey patch to OpenAI client."""
    global _original_create
    
    if _original_create is None:  # Only patch once
        _original_create = openai.OpenAI().chat.completions.create.__func__
        openai.resources.chat.completions.Completions.create = gpt5_aware_create
        print("🐒 MONKEY PATCH: Applied global GPT-5 fix to OpenAI library")

def remove_monkey_patch():
    """Remove the monkey patch."""
    global _original_create
    
    if _original_create is not None:
        openai.resources.chat.completions.Completions.create = _original_create
        _original_create = None
        print("🐒 MONKEY PATCH: Removed global GPT-5 fix")

# Auto-apply when imported
apply_monkey_patch()
'''
    
    with open(monkey_patch_file, 'w') as f:
        f.write(monkey_patch_code)
    
    print("✅ Created global monkey patch")
    
    # 3. Update all config files to use maximum token limits
    config_files = [
        "config/development.yaml",
        "config/production.yaml", 
        "config/staging.yaml",
        "config/testing.yaml"
    ]
    
    for config_file in config_files:
        config_path = project_root / config_file
        if config_path.exists():
            with open(config_path, 'r') as f:
                content = f.read()
            
            # Set to maximum reasonable token limits
            content = re.sub(r'max_tokens: \d+', 'max_tokens: 8000', content)
            
            with open(config_path, 'w') as f:
                f.write(content)
            
            print(f"✅ Updated {config_file} to max tokens")
    
    # 4. Create an auto-import that applies the monkey patch everywhere
    init_file = project_root / "app/__init__.py"
    
    init_content = '''"""
Auto-apply GPT-5 fixes when the app module is imported.
"""

# Auto-apply GPT-5 monkey patch
try:
    from app.llm.gpt5_monkey_patch import apply_monkey_patch
    apply_monkey_patch()
except ImportError:
    pass  # Monkey patch not available
'''
    
    with open(init_file, 'w') as f:
        f.write(init_content)
    
    print("✅ Created auto-import for monkey patch")
    
    # 5. Create environment variable override
    env_file = project_root / ".env"
    env_content = '''# Nuclear GPT-5 fix environment variables
GPT5_NUCLEAR_FIX=true
GPT5_MIN_TOKENS=4000
GPT5_MAX_TOKENS=8000
GPT5_AUTO_RETRY=true
'''
    
    # Append to existing .env or create new
    if env_file.exists():
        with open(env_file, 'a') as f:
            f.write('\n' + env_content)
    else:
        with open(env_file, 'w') as f:
            f.write(env_content)
    
    print("✅ Added nuclear fix environment variables")
    
    print(f"\n☢️  NUCLEAR FIX COMPLETE!")
    print("=" * 50)
    
    print(f"\n📋 What was applied:")
    print("  🔧 Nuclear patch to OpenAI provider")
    print("  🐒 Global monkey patch to OpenAI library")
    print("  ⚙️  Maximum token limits in all configs (8000)")
    print("  🚀 Auto-import system for patches")
    print("  🌍 Environment variable overrides")
    
    print(f"\n🚨 RESTART REQUIRED:")
    print("  1. Restart your Streamlit app")
    print("  2. Restart any Python processes")
    print("  3. Clear any caches")
    
    print(f"\n⚡ This should eliminate ALL GPT-5 token errors!")
    
    return True

if __name__ == "__main__":
    apply_nuclear_fix()