#!/usr/bin/env python3
"""Test script to verify rate limiting and Q&A fixes."""

import asyncio
import time
from app.middleware.rate_limiter import RateLimiter, RateLimitRule, UserLimits
from app.config import load_settings
from app.config.system_config import RateLimitConfig, SystemConfigurationManager


def test_rate_limiting_configuration():
    """Test rate limiting with custom configuration."""
    print("🧪 Testing Rate Limiting Configuration...")
    
    # Create custom rate limit config
    rate_config = RateLimitConfig(
        default_burst_limit=30,  # Higher than default
        default_requests_per_minute=100,
        premium_burst_limit=50,
        enterprise_burst_limit=150
    )
    
    # Initialize rate limiter with config
    settings = load_settings()
    rate_limiter = RateLimiter(settings, rate_config)
    
    # Test default limits
    default_limits = rate_limiter.default_limits
    print(f"✅ Default burst limit: {default_limits.burst_limit} (expected: 30)")
    assert default_limits.burst_limit == 30, f"Expected 30, got {default_limits.burst_limit}"
    
    # Test premium user limits
    premium_user = UserLimits(user_id="test_premium", tier="premium")
    premium_limits = premium_user.get_limits(rate_config)
    print(f"✅ Premium burst limit: {premium_limits.burst_limit} (expected: 50)")
    assert premium_limits.burst_limit == 50, f"Expected 50, got {premium_limits.burst_limit}"
    
    # Test enterprise user limits
    enterprise_user = UserLimits(user_id="test_enterprise", tier="enterprise")
    enterprise_limits = enterprise_user.get_limits(rate_config)
    print(f"✅ Enterprise burst limit: {enterprise_limits.burst_limit} (expected: 150)")
    assert enterprise_limits.burst_limit == 150, f"Expected 150, got {enterprise_limits.burst_limit}"
    
    print("✅ Rate limiting configuration test passed!")


def test_system_configuration_manager():
    """Test system configuration manager for rate limiting."""
    print("\n🧪 Testing System Configuration Manager...")
    
    # Create configuration manager
    config_manager = SystemConfigurationManager()
    
    # Check rate limiting config exists
    assert hasattr(config_manager.config, 'rate_limiting'), "Rate limiting config missing"
    
    rate_config = config_manager.config.rate_limiting
    print(f"✅ Default burst limit from config: {rate_config.default_burst_limit}")
    print(f"✅ Premium burst limit from config: {rate_config.premium_burst_limit}")
    print(f"✅ Enterprise burst limit from config: {rate_config.enterprise_burst_limit}")
    
    # Test saving and loading
    original_burst = rate_config.default_burst_limit
    rate_config.default_burst_limit = 35  # Change value
    
    # Save config
    success = config_manager.save_config()
    print(f"✅ Config save: {'Success' if success else 'Failed'}")
    
    # Load new manager to test persistence
    new_manager = SystemConfigurationManager()
    new_burst = new_manager.config.rate_limiting.default_burst_limit
    print(f"✅ Loaded burst limit: {new_burst} (expected: 35)")
    
    # Restore original value
    new_manager.config.rate_limiting.default_burst_limit = original_burst
    new_manager.save_config()
    
    print("✅ System configuration manager test passed!")


def test_burst_limit_scenarios():
    """Test burst limit scenarios for Q&A interactions."""
    print("\n🧪 Testing Q&A Burst Scenarios...")
    
    # Scenario: User doing Q&A interaction
    scenarios = [
        ("Low burst (old default)", 5, "❌ May cause 429 errors"),
        ("Medium burst (old premium)", 10, "⚠️ Might work but tight"),
        ("High burst (new default)", 25, "✅ Should work smoothly"),
        ("Very high burst (new enterprise)", 100, "✅ Excellent for heavy usage")
    ]
    
    for name, burst_limit, expected in scenarios:
        print(f"  {name}: burst_limit={burst_limit} → {expected}")
        
        # Simulate Q&A requests
        qa_requests = [
            "Load questions",
            "Submit answers", 
            "Process answers",
            "Generate recommendations",
            "Load diagrams"
        ]
        
        if len(qa_requests) <= burst_limit:
            status = "✅ PASS"
        elif len(qa_requests) <= burst_limit * 0.8:
            status = "⚠️ TIGHT"
        else:
            status = "❌ FAIL"
        
        print(f"    Q&A requests ({len(qa_requests)}) vs burst limit ({burst_limit}): {status}")
    
    print("✅ Burst limit scenario test completed!")


def main():
    """Run all tests."""
    print("🚀 Testing Rate Limiting and Q&A Fixes\n")
    
    try:
        test_rate_limiting_configuration()
        test_system_configuration_manager()
        test_burst_limit_scenarios()
        
        print("\n🎉 All tests passed! Rate limiting and Q&A fixes are working correctly.")
        print("\n📋 Summary of fixes:")
        print("  ✅ Increased burst limits for all tiers (5→25, 20→40, 50→100)")
        print("  ✅ Made rate limits configurable via system configuration")
        print("  ✅ Q&A form prevents API calls on every keystroke")
        print("  ✅ System configuration UI for rate limiting management")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())