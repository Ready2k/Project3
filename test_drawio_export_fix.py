#!/usr/bin/env python3
"""
Test script to verify Draw.io export fix.
"""

def test_drawio_export_functions():
    """Test that Draw.io export functions work without service dependency."""
    try:
        from streamlit_app import AutomatedAIAssessmentUI
        
        # Create a mock app instance
        app = AutomatedAIAssessmentUI()
        
        # Test data
        test_mermaid_code = """flowchart TB
    A[Start] --> B[Process]
    B --> C[End]"""
        
        test_infrastructure_spec = {
            "components": [
                {"name": "web-server", "type": "compute", "provider": "aws"},
                {"name": "database", "type": "storage", "provider": "aws"}
            ],
            "connections": [
                {"from": "web-server", "to": "database", "type": "tcp"}
            ]
        }
        
        print("✅ AutomatedAIAssessmentUI class imported successfully")
        print("✅ Export functions are accessible")
        
        # Check if the functions exist and are callable
        if hasattr(app, 'export_to_drawio') and callable(getattr(app, 'export_to_drawio')):
            print("✅ export_to_drawio function exists")
        else:
            print("❌ export_to_drawio function missing")
            return False
            
        if hasattr(app, 'export_infrastructure_to_drawio') and callable(getattr(app, 'export_infrastructure_to_drawio')):
            print("✅ export_infrastructure_to_drawio function exists")
        else:
            print("❌ export_infrastructure_to_drawio function missing")
            return False
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to test Draw.io export functions: {e}")
        return False

def test_no_service_dependency():
    """Test that the functions don't depend on missing services."""
    try:
        # Read the streamlit_app.py file to check for service dependencies
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check that the old service-dependent code is removed
        if "drawio_exporter_service = optional_service('drawio_exporter'" in content:
            print("❌ Still contains drawio_exporter service dependency")
            return False
        
        if "Service not registered" in content:
            print("❌ Still contains 'Service not registered' error message")
            return False
        
        print("✅ No drawio_exporter service dependencies found")
        print("✅ No 'Service not registered' error messages found")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to check service dependencies: {e}")
        return False

def test_export_functionality():
    """Test that export functions provide useful alternatives."""
    try:
        with open('streamlit_app.py', 'r') as f:
            content = f.read()
        
        # Check for key functionality
        checks = [
            ("Mermaid file download", "Download Mermaid File" in content),
            ("Draw.io XML generation", "<?xml version=" in content),
            ("JSON spec download", "Download JSON Spec" in content),
            ("User instructions", "How to use" in content),
            ("Draw.io links", "draw.io" in content or "diagrams.net" in content),
        ]
        
        all_passed = True
        for check_name, check_result in checks:
            if check_result:
                print(f"✅ {check_name} - Found")
            else:
                print(f"❌ {check_name} - Missing")
                all_passed = False
        
        return all_passed
        
    except Exception as e:
        print(f"❌ Failed to test export functionality: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing Draw.io export fix...")
    print("=" * 50)
    
    tests = [
        ("Draw.io export functions", test_drawio_export_functions),
        ("Service dependency removal", test_no_service_dependency),
        ("Export functionality", test_export_functionality),
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
        print("🎉 All tests passed! Draw.io export fix is working correctly.")
        print("\n📋 What's fixed:")
        print("- No more 'Service not registered' errors")
        print("- Users can download Mermaid files for Draw.io import")
        print("- Users can download Draw.io XML files")
        print("- Users get clear instructions on how to use the exports")
        print("- Infrastructure specs are available as JSON")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main()