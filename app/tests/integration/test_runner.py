#!/usr/bin/env python3
"""
Simple test runner to verify comprehensive attack defense tests work correctly.
"""

import sys
import subprocess
import os

def run_test(test_path, test_name=None):
    """Run a specific test and return the result."""
    cmd = ["python3", "-m", "pytest", test_path, "-v", "--tb=short"]
    if test_name:
        cmd[3] = f"{test_path}::{test_name}"
    
    print(f"Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
        return result.returncode == 0, result.stdout, result.stderr
    except subprocess.TimeoutExpired:
        return False, "", "Test timed out after 60 seconds"
    except Exception as e:
        return False, "", str(e)

def main():
    """Run key tests to verify implementation."""
    os.chdir(os.path.dirname(os.path.abspath(__file__)))
    
    # Test cases to verify
    test_cases = [
        # Basic functionality test
        ("app/tests/unit/test_advanced_prompt_defender.py", "TestAdvancedPromptDefender::test_legitimate_request_passes"),
        
        # Attack pack validation test
        ("app/tests/unit/test_attack_pack_validation.py", "TestAttackPackValidation::test_pattern_01_invoice_automation_feasibility"),
        
        # Integration test
        ("app/tests/integration/test_advanced_prompt_defender.py", "TestAdvancedPromptDefenderIntegration::test_legitimate_business_request_passes"),
    ]
    
    print("=" * 80)
    print("COMPREHENSIVE ATTACK DEFENSE TEST VERIFICATION")
    print("=" * 80)
    
    passed = 0
    failed = 0
    
    for test_path, test_name in test_cases:
        print(f"\nTesting: {test_name}")
        print("-" * 60)
        
        success, stdout, stderr = run_test(test_path, test_name)
        
        if success:
            print("✅ PASSED")
            passed += 1
        else:
            print("❌ FAILED")
            print("STDOUT:", stdout[-500:] if stdout else "None")  # Last 500 chars
            print("STDERR:", stderr[-500:] if stderr else "None")  # Last 500 chars
            failed += 1
    
    print("\n" + "=" * 80)
    print(f"SUMMARY: {passed} passed, {failed} failed")
    print("=" * 80)
    
    if failed == 0:
        print("🎉 All key tests passed! Implementation appears to be working correctly.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1

if __name__ == "__main__":
    sys.exit(main())