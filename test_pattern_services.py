#!/usr/bin/env python3
"""Test script to check if pattern enhancement services are registered."""

import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.utils.pattern_status_utils import check_pattern_enhancement_status, check_pattern_analytics_status


def test_pattern_services():
    """Test if pattern enhancement and analytics services are available."""
    
    print("🔍 Testing Pattern Enhancement Services...")
    print("=" * 60)
    
    # Test pattern enhancement status
    print("📊 Checking Pattern Enhancement Status:")
    is_available, message, details = check_pattern_enhancement_status()
    
    if is_available:
        print(f"✅ {message}")
        if details:
            print(f"📈 Details: {details}")
    else:
        print(f"❌ {message}")
    
    print()
    
    # Test pattern analytics status
    print("📈 Checking Pattern Analytics Status:")
    is_analytics_available, analytics_message, analytics_details = check_pattern_analytics_status()
    
    if is_analytics_available:
        print(f"✅ {analytics_message}")
        if analytics_details:
            print(f"📊 Details: {analytics_details}")
    else:
        print(f"❌ {analytics_message}")
    
    print()
    print("=" * 60)
    
    if is_available and is_analytics_available:
        print("🎉 All pattern services are available!")
        return True
    else:
        print("💥 Some pattern services are missing!")
        return False


if __name__ == "__main__":
    print("🚀 Starting pattern services test...")
    success = test_pattern_services()
    
    if success:
        print("\n✅ Test PASSED: All pattern services are working!")
        sys.exit(0)
    else:
        print("\n❌ Test FAILED: Some pattern services are not available!")
        sys.exit(1)