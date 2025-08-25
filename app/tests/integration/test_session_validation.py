#!/usr/bin/env python3
"""Test session ID validation logic."""

import re

def validate_session_id(session_id: str) -> bool:
    """Validate session ID format (same logic as in Streamlit app)."""
    session_id_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    return bool(re.match(session_id_pattern, session_id.strip().lower()))

def test_validation():
    """Test session ID validation with various inputs."""
    test_cases = [
        # Valid cases
        ("7249c0d9-7896-4fdf-931b-4f4aafbc44e0", True, "Standard UUID format"),
        ("ABCDEF12-3456-7890-ABCD-EF1234567890", True, "Uppercase letters"),
        ("12345678-1234-1234-1234-123456789abc", True, "Mixed case"),
        ("00000000-0000-0000-0000-000000000000", True, "All zeros"),
        ("ffffffff-ffff-ffff-ffff-ffffffffffff", True, "All f's"),
        
        # Invalid cases
        ("", False, "Empty string"),
        ("invalid-session-id", False, "Non-UUID format"),
        ("7249c0d9-7896-4fdf-931b", False, "Too short"),
        ("7249c0d9-7896-4fdf-931b-4f4aafbc44e0-extra", False, "Too long"),
        ("7249c0d9_7896_4fdf_931b_4f4aafbc44e0", False, "Wrong separator"),
        ("7249c0d9-7896-4fdf-931b-4f4aafbc44e", False, "Missing character"),
        ("g249c0d9-7896-4fdf-931b-4f4aafbc44e0", False, "Invalid character (g)"),
        ("7249c0d9-7896-4fdf-931b-4f4aafbc44e0 ", True, "Trailing space (should be stripped)"),
        (" 7249c0d9-7896-4fdf-931b-4f4aafbc44e0", True, "Leading space (should be stripped)"),
        ("7249c0d9--7896-4fdf-931b-4f4aafbc44e0", False, "Double dash"),
        ("7249c0d97896-4fdf-931b-4f4aafbc44e0", False, "Missing dash"),
    ]
    
    print("🧪 Testing Session ID Validation")
    print("=" * 60)
    
    passed = 0
    failed = 0
    
    for session_id, expected, description in test_cases:
        result = validate_session_id(session_id)
        status = "✅ PASS" if result == expected else "❌ FAIL"
        
        if result == expected:
            passed += 1
        else:
            failed += 1
        
        print(f"{status} | {description}")
        print(f"      Input: '{session_id}'")
        print(f"      Expected: {expected}, Got: {result}")
        print()
    
    print("=" * 60)
    print(f"📊 Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed!")
        return True
    else:
        print("❌ Some tests failed!")
        return False

if __name__ == "__main__":
    success = test_validation()
    exit(0 if success else 1)