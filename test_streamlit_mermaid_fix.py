#!/usr/bin/env python3
"""
Test script to verify streamlit_mermaid import fix.
"""

def test_streamlit_mermaid_import():
    """Test that streamlit_mermaid can be imported correctly."""
    try:
        import streamlit_mermaid as stmd
        print("✅ streamlit_mermaid imported successfully")
        
        # Check if the main function exists
        if hasattr(stmd, 'st_mermaid'):
            print("✅ st_mermaid function is available")
        else:
            print("❌ st_mermaid function not found")
            return False
            
        return True
    except ImportError as e:
        print(f"❌ Failed to import streamlit_mermaid: {e}")
        return False

def test_streamlit_app_imports():
    """Test that the main streamlit app imports without errors."""
    try:
        import streamlit_app
        print("✅ streamlit_app imports successfully")
        return True
    except Exception as e:
        print(f"❌ Failed to import streamlit_app: {e}")
        return False

def test_ui_modules():
    """Test that UI modules import without errors."""
    try:
        from app.ui.analysis_display import AgentRolesUIComponent
        print("✅ analysis_display imports successfully")
        
        from app.ui.mermaid_diagrams import MermaidDiagramGenerator
        print("✅ mermaid_diagrams imports successfully")
        
        return True
    except Exception as e:
        print(f"❌ Failed to import UI modules: {e}")
        return False

def main():
    """Run all tests."""
    print("Testing streamlit_mermaid fix...")
    print("=" * 50)
    
    tests = [
        ("streamlit_mermaid import", test_streamlit_mermaid_import),
        ("streamlit_app import", test_streamlit_app_imports),
        ("UI modules import", test_ui_modules),
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
        print("🎉 All tests passed! streamlit_mermaid fix is working correctly.")
    else:
        print("⚠️  Some tests failed. Please check the errors above.")
    
    return all_passed

if __name__ == "__main__":
    main()