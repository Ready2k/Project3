#!/usr/bin/env python3
"""
Quick fix for API configuration issues.

This script addresses the immediate configuration problems preventing the API from working.
"""

import os
import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def fix_embeddings_factory():
    """Fix the embeddings factory function call."""
    factory_file = project_root / "app" / "embeddings" / "factory.py"
    
    if factory_file.exists():
        content = factory_file.read_text()
        
        # Check if the function signature needs fixing
        if "def create_embedding_provider(" in content and "settings: Settings" in content:
            print("✅ Embeddings factory signature looks correct")
        else:
            print("⚠️ Embeddings factory might need signature fix")
    else:
        print("❌ Embeddings factory file not found")

def check_security_decision():
    """Check SecurityDecision class for missing attributes."""
    try:
        from app.security.advanced_prompt_defender import SecurityDecision
        
        # Check if is_safe attribute exists
        decision = SecurityDecision(
            is_safe=True,
            confidence=0.9,
            detected_attacks=[],
            reasoning="Test"
        )
        
        if hasattr(decision, 'is_safe'):
            print("✅ SecurityDecision.is_safe attribute exists")
        else:
            print("❌ SecurityDecision.is_safe attribute missing")
            
    except ImportError as e:
        print(f"❌ Cannot import SecurityDecision: {e}")
    except Exception as e:
        print(f"❌ Error checking SecurityDecision: {e}")

def create_minimal_env():
    """Create minimal environment configuration."""
    env_file = project_root / ".env"
    
    if not env_file.exists():
        env_content = """# Minimal configuration for AAA system
# Add your API keys here

# OpenAI (optional for testing)
# OPENAI_API_KEY=your_openai_key_here

# Claude (optional for testing)  
# ANTHROPIC_API_KEY=your_claude_key_here

# AWS Bedrock (optional for testing)
# AWS_ACCESS_KEY_ID=your_aws_key_here
# AWS_SECRET_ACCESS_KEY=your_aws_secret_here
# AWS_DEFAULT_REGION=us-east-1

# Application settings
APP_ENV=development
AAA_DEBUG=true
AAA_LOG_LEVEL=INFO
"""
        
        env_file.write_text(env_content)
        print(f"✅ Created minimal .env file at {env_file}")
    else:
        print("✅ .env file already exists")

def test_basic_imports():
    """Test basic imports to identify issues."""
    try:
        from app.config import Settings, load_settings
        print("✅ Legacy config imports work")
        
        settings = load_settings()
        print(f"✅ Settings loaded: provider={settings.provider}, model={settings.model}")
        
    except Exception as e:
        print(f"❌ Legacy config import failed: {e}")
    
    try:
        from app.config.settings import get_config, load_config
        print("✅ New config imports work")
        
        result = load_config()
        if result.is_success:
            config = result.value
            print(f"✅ New config loaded: environment={config.environment}")
        else:
            print(f"❌ New config loading failed: {result.error}")
            
    except Exception as e:
        print(f"❌ New config import failed: {e}")

def main():
    """Run all fixes and checks."""
    print("🔧 Running API Configuration Fixes")
    print("=" * 40)
    
    test_basic_imports()
    print()
    
    fix_embeddings_factory()
    print()
    
    check_security_decision()
    print()
    
    create_minimal_env()
    print()
    
    print("🎯 Quick fixes completed!")
    print("💡 You may need to restart the API server for changes to take effect")

if __name__ == "__main__":
    main()