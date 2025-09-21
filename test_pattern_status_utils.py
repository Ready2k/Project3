#!/usr/bin/env python3
"""
Test Pattern Status Utilities

Test the pattern status utility functions.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_pattern_status_utils():
    """Test pattern status utility functions."""
    try:
        # Register services first
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Import utilities
        from app.utils.pattern_status_utils import (
            get_pattern_enhancement_error_or_success,
            get_pattern_analytics_error_or_success,
            format_pattern_status_for_ui,
            get_combined_pattern_status
        )
        
        print("🧪 Testing Pattern Status Utilities")
        print("=" * 50)
        
        # Test enhancement status
        print("\n📊 Pattern Enhancement Status:")
        enhancement_msg = get_pattern_enhancement_error_or_success()
        print(enhancement_msg)
        
        # Test analytics status
        print("\n📈 Pattern Analytics Status:")
        analytics_msg = get_pattern_analytics_error_or_success()
        print(analytics_msg)
        
        # Test combined status
        print("\n🔧 Combined Status:")
        combined_status = get_combined_pattern_status()
        print(f"Overall Status: {'✅ All services available' if combined_status['overall_status'] else '❌ Some services unavailable'}")
        
        # Test formatted UI output
        print("\n📱 Formatted UI Output:")
        ui_output = format_pattern_status_for_ui()
        print(ui_output)
        
        print("\n" + "=" * 50)
        print("✅ Pattern status utilities test complete!")
        
        return True
        
    except Exception as e:
        print(f"❌ Error testing pattern status utilities: {e}")
        return False


if __name__ == "__main__":
    success = test_pattern_status_utils()
    sys.exit(0 if success else 1)