#!/usr/bin/env python3
"""
Service System Integration Test Runner

This script runs the comprehensive integration tests for the service system,
covering all aspects of service registration, lifecycle management, error handling,
and graceful degradation scenarios.

Requirements covered: 2.1, 2.5, 5.1, 5.3
"""

import sys
import subprocess
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def run_integration_tests():
    """Run the service system integration tests."""
    print("🧪 Running Service System Integration Tests")
    print("=" * 60)
    
    # Test file path
    test_file = "app/tests/integration/test_service_system_integration.py"
    
    # Check if test file exists
    if not Path(test_file).exists():
        print(f"❌ Test file not found: {test_file}")
        return False
    
    try:
        # Run pytest with verbose output
        cmd = [
            sys.executable, "-m", "pytest", 
            test_file,
            "-v",
            "--tb=short",
            "--no-header",
            "--disable-warnings"
        ]
        
        print(f"🚀 Running command: {' '.join(cmd)}")
        print()
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Print output
        if result.stdout:
            print("📊 Test Output:")
            print(result.stdout)
        
        if result.stderr:
            print("⚠️  Warnings/Errors:")
            print(result.stderr)
        
        # Check result
        if result.returncode == 0:
            print("\n✅ All integration tests passed!")
            print("\n📋 Test Coverage Summary:")
            print("   ✓ Complete service registration and startup")
            print("   ✓ Service lifecycle management")
            print("   ✓ Error handling for missing services")
            print("   ✓ Graceful degradation scenarios")
            print("   ✓ Service dependency resolution")
            print("   ✓ Circular dependency detection")
            print("   ✓ Async service integration")
            print("   ✓ Service configuration integration")
            print("   ✓ Factory vs singleton behavior")
            print("   ✓ Application startup integration")
            return True
        else:
            print(f"\n❌ Tests failed with exit code: {result.returncode}")
            return False
            
    except Exception as e:
        print(f"❌ Error running tests: {e}")
        return False

def main():
    """Main function."""
    print("🔧 Service System Integration Test Suite")
    print("Testing Requirements: 2.1, 2.5, 5.1, 5.3")
    print()
    
    success = run_integration_tests()
    
    print("\n" + "=" * 60)
    if success:
        print("🎉 Integration test suite completed successfully!")
        print("\nThe service system demonstrates:")
        print("• Robust service registration and initialization")
        print("• Proper lifecycle management with cleanup")
        print("• Comprehensive error handling and recovery")
        print("• Graceful degradation under failure conditions")
        print("• Complex dependency resolution")
        print("• Integration with application startup")
        sys.exit(0)
    else:
        print("💥 Integration test suite failed!")
        print("Please check the test output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    main()