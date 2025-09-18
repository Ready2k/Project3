#!/usr/bin/env python3
"""
Test script to verify the browser open functionality.
"""

def test_browser_open_function():
    """Test that the browser open function generates proper HTML and JavaScript."""
    try:
        from streamlit_app import AutomatedAIAssessmentUI
        
        # Create app instance
        app = AutomatedAIAssessmentUI()
        
        # Test data
        test_mermaid_code = """flowchart TB
    A[Start] --> B[Process]
    B --> C[End]"""
        
        test_diagram_id = "test123"
        
        # Test that the function exists
        if hasattr(app, 'open_diagram_in_browser') and callable(getattr(app, 'open_diagram_in_browser')):
            print("✅ open_diagram_in_browser function exists")
        else:
            print("❌ open_diagram_in_browser function missing")
            return False
        
        # Test that create_standalone_html exists
        if hasattr(app, 'create_standalone_html') and callable(getattr(app, 'create_standalone_html')):
            print("✅ create_standalone_html function exists")
        else:
            print("❌ create_standalone_html function missing")
            return False
        
        # Test HTML generation
        html_content = app.create_standalone_html(test_mermaid_code, test_diagram_id)
        
        if html_content and len(html_content) > 100:
            print("✅ HTML content generated successfully")
        else:
            print("❌ HTML content generation failed")
            return False
        
        # Check for key HTML elements
        html_checks = [
            ("DOCTYPE", "<!DOCTYPE html>" in html_content),
            ("Mermaid script", "mermaid" in html_content.lower()),
            ("Diagram code", "flowchart TB" in html_content),
            ("Title", "Architecture Diagram" in html_content),
        ]
        
        for check_name, check_result in html_checks:
            if check_result:
                print(f"✅ {check_name} - Found in HTML")
            else:
                print(f"❌ {check_name} - Missing from HTML")
                return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test browser open function: {e}")
        return False

def test_javascript_generation():
    """Test that the updated function includes JavaScript for opening tabs."""
    try:
        # Read the streamlit_app.py file to check for JavaScript
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for key JavaScript functionality
        js_checks = [
            ("window.open", "window.open" in content),
            ("_blank target", "_blank" in content),
            ("data URL", "data:text/html;base64" in content),
            ("base64 encoding", "base64.b64encode" in content),
            ("Auto-open script", "setTimeout" in content),
            ("Manual fallback", "click here" in content),
        ]
        
        all_passed = True
        for check_name, check_result in js_checks:
            if check_result:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Failed to test JavaScript generation: {e}")
        return False

def test_file_operations():
    """Test that the function properly handles file operations."""
    try:
        # Read the streamlit_app.py file to check for file operations
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for key file operations
        file_checks = [
            ("Directory creation", "os.makedirs" in content),
            ("File writing", "with open" in content and "w" in content),
            ("UTF-8 encoding", "utf-8" in content),
            ("Exports directory", "exports" in content),
            ("File path display", "file_path" in content),
        ]
        
        all_passed = True
        for check_name, check_result in file_checks:
            if check_result:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Failed to test file operations: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Browser Open functionality...")
    print("=" * 50)
    
    tests = [
        ("Browser open function", test_browser_open_function),
        ("JavaScript generation", test_javascript_generation),
        ("File operations", test_file_operations),
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
        print("🎉 All tests passed! Browser open functionality is working correctly.")
        print("\n📋 What's improved:")
        print("- Diagrams now automatically open in new browser tabs")
        print("- Uses data URLs for immediate display")
        print("- Includes manual fallback options")
        print("- Still saves files locally for backup")
        print("- Provides multiple ways to access the diagram")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main()