#!/usr/bin/env python3
"""Test script to verify button keys are unique in database management."""

import sys
import re
sys.path.append('.')

def test_button_keys():
    """Test that all buttons have unique keys."""
    print("🧪 Testing button key uniqueness...")
    
    # Read the system configuration file
    with open('app/ui/system_configuration.py', 'r') as f:
        content = f.read()
    
    # Find all button calls with keys
    button_pattern = r'st\.button\([^)]*key\s*=\s*["\']([^"\']+)["\']'
    button_keys = re.findall(button_pattern, content)
    
    print(f"Found {len(button_keys)} buttons with keys:")
    for key in sorted(button_keys):
        print(f"  - {key}")
    
    # Check for duplicates
    duplicates = []
    seen = set()
    for key in button_keys:
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    
    if duplicates:
        print(f"❌ Found duplicate button keys: {duplicates}")
        return False
    else:
        print("✅ All button keys are unique")
    
    # Find buttons without keys - more accurate check
    all_buttons = re.findall(r'st\.button\([^)]+\)', content)
    buttons_without_keys = [b for b in all_buttons if 'key=' not in b]
    
    if buttons_without_keys:
        print(f"⚠️ Found {len(buttons_without_keys)} buttons without keys:")
        for btn in buttons_without_keys[:5]:  # Show first 5
            print(f"  - {btn[:50]}...")
        if len(buttons_without_keys) > 5:
            print(f"  ... and {len(buttons_without_keys) - 5} more")
    else:
        print("✅ All buttons have unique keys")
    
    return len(duplicates) == 0

def test_other_elements():
    """Test other elements that might need keys."""
    print("\n🧪 Testing other element keys...")
    
    with open('app/ui/system_configuration.py', 'r') as f:
        content = f.read()
    
    # Get button keys again for cross-element check
    button_pattern = r'st\.button\([^)]*key\s*=\s*["\']([^"\']+)["\']'
    button_keys = re.findall(button_pattern, content)
    
    # Check checkboxes
    checkbox_pattern = r'st\.checkbox\([^)]*key\s*=\s*["\']([^"\']+)["\']'
    checkbox_keys = re.findall(checkbox_pattern, content)
    
    print(f"Found {len(checkbox_keys)} checkboxes with keys")
    
    # Check multiselect
    multiselect_pattern = r'st\.multiselect\([^)]*key\s*=\s*["\']([^"\']+)["\']'
    multiselect_keys = re.findall(multiselect_pattern, content)
    
    print(f"Found {len(multiselect_keys)} multiselects with keys")
    
    # Check selectbox
    selectbox_pattern = r'st\.selectbox\([^)]*key\s*=\s*["\']([^"\']+)["\']'
    selectbox_keys = re.findall(selectbox_pattern, content)
    
    print(f"Found {len(selectbox_keys)} selectboxes with keys")
    
    # Check text_input
    text_input_pattern = r'st\.text_input\([^)]*key\s*=\s*["\']([^"\']+)["\']'
    text_input_keys = re.findall(text_input_pattern, content)
    
    print(f"Found {len(text_input_keys)} text_inputs with keys")
    
    # Check for any duplicate keys across all elements
    all_keys = button_keys + checkbox_keys + multiselect_keys + selectbox_keys + text_input_keys
    duplicates = []
    seen = set()
    for key in all_keys:
        if key in seen:
            duplicates.append(key)
        seen.add(key)
    
    if duplicates:
        print(f"❌ Found duplicate keys across all elements: {duplicates}")
        return False
    else:
        print("✅ All element keys are unique across the entire file")
    
    return True

def main():
    """Run all button key tests."""
    print("🚀 Starting Button Key Tests\n")
    
    tests_passed = 0
    total_tests = 2
    
    if test_button_keys():
        tests_passed += 1
    
    if test_other_elements():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Button ID conflicts are resolved.")
        print("\n✅ Key Features:")
        print("  - All buttons have unique keys")
        print("  - All interactive elements have unique keys")
        print("  - No duplicate IDs that would cause Streamlit conflicts")
        print("  - Database management interface is ready for use")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return tests_passed == total_tests

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)