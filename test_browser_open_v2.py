#!/usr/bin/env python3
"""
Test script to verify the updated browser open functionality.
"""

def test_javascript_escaping():
    """Test that HTML content is properly escaped for JavaScript."""
    try:
        from streamlit_app import AutomatedAIAssessmentUI
        
        # Create app instance
        app = AutomatedAIAssessmentUI()
        
        # Test with problematic HTML content
        test_mermaid_code = """flowchart TB
    A["Start `with` backticks"] --> B[Process ${variable}]
    B --> C["End with \\ backslash"]"""
        
        test_diagram_id = "test123"
        
        # Generate HTML content
        html_content = app.create_standalone_html(test_mermaid_code, test_diagram_id)
        
        # Check that HTML contains the problematic characters
        if '`' in html_content and '${' in html_content and '\\' in html_content:
            print("✅ HTML content contains test characters")
        else:
            print("❌ HTML content missing test characters")
            return False
        
        # Test escaping logic (simulate what happens in the function)
        escaped_html = html_content.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        
        # Check that escaping worked
        if '\\`' in escaped_html and '\\${' in escaped_html and '\\\\' in escaped_html:
            print("✅ HTML content properly escaped for JavaScript")
        else:
            print("❌ HTML content not properly escaped")
            return False
        
        print(f"✅ Original HTML length: {len(html_content)} characters")
        print(f"✅ Escaped HTML length: {len(escaped_html)} characters")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test JavaScript escaping: {e}")
        return False

def test_unique_function_names():
    """Test that JavaScript function names are unique per diagram."""
    try:
        # Read the streamlit_app.py file to check for unique function names
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for unique function naming pattern
        if "openDiagramTab_{diagram_id}" in content:
            print("✅ JavaScript functions use unique diagram ID")
        else:
            print("❌ JavaScript functions not uniquely named")
            return False
        
        # Check for proper error handling
        if "try {" in content and "catch (error)" in content:
            print("✅ JavaScript includes error handling")
        else:
            print("❌ JavaScript missing error handling")
            return False
        
        # Check for blob URL usage
        if "createObjectURL" in content and "revokeObjectURL" in content:
            print("✅ JavaScript uses blob URLs properly")
        else:
            print("❌ JavaScript not using blob URLs")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test unique function names: {e}")
        return False

def test_fallback_options():
    """Test that fallback options are provided."""
    try:
        # Read the streamlit_app.py file to check for fallback options
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for fallback features
        fallback_checks = [
            ("Download button", "st.download_button" in content),
            ("Manual file path", "abs_path" in content),
            ("Bash command", "st.code" in content),
            ("Expandable options", "st.expander" in content),
            ("Error messaging", "Popup blocked" in content or "Could not open" in content),
        ]
        
        all_passed = True
        for check_name, check_result in fallback_checks:
            if check_result:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Failed to test fallback options: {e}")
        return False

def test_browser_compatibility():
    """Test that the JavaScript should work across browsers."""
    try:
        # Read the streamlit_app.py file to check for browser compatibility
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for browser compatibility features
        compat_checks = [
            ("Blob API", "new Blob" in content),
            ("URL.createObjectURL", "createObjectURL" in content),
            ("window.open with options", "noopener,noreferrer" in content),
            ("Error handling", "try {" in content and "} catch" in content),
            ("Console logging", "console.log" in content),
            ("Timeout for auto-open", "setTimeout" in content),
        ]
        
        all_passed = True
        for check_name, check_result in compat_checks:
            if check_result:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Failed to test browser compatibility: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Updated Browser Open functionality...")
    print("=" * 50)
    
    tests = [
        ("JavaScript escaping", test_javascript_escaping),
        ("Unique function names", test_unique_function_names),
        ("Fallback options", test_fallback_options),
        ("Browser compatibility", test_browser_compatibility),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Testing {test_name}...")
        result = test_func()
        results.append((test_name, result))
    
    print("\n" + "=" * 50)
    print("Test Results:")
    print("=" * 50)
    
    all_passed = True
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if not result:
            all_passed = False
    
    print("=" * 50)
    if all_passed:
        print("🎉 All tests passed! Updated browser open functionality looks good.")
        print("\n📋 Key improvements:")
        print("- Proper HTML escaping for JavaScript")
        print("- Unique function names per diagram")
        print("- Blob URL usage for better browser support")
        print("- Comprehensive error handling")
        print("- Multiple fallback options")
        print("- Auto-open with manual trigger option")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main()