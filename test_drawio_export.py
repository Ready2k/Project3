#!/usr/bin/env python3
"""
Test script to verify Draw.io export functionality is working properly.
"""

import sys
import os
sys.path.append('app')

from exporters.drawio_exporter import DrawIOExporter
import tempfile

def test_drawio_export():
    """Test the Draw.io export functionality."""
    
    print("🧪 Testing Draw.io Export Functionality...")
    
    # Create test Mermaid diagram
    test_mermaid = """
graph TD
    A[User Request] --> B[AI Agent]
    B --> C{Decision Point}
    C -->|Yes| D[Execute Action]
    C -->|No| E[Request Clarification]
    D --> F[Return Result]
    E --> A
    F --> G[End]
    
    style A fill:#e1f5fe
    style B fill:#f3e5f5
    style C fill:#fff3e0
    style D fill:#e8f5e8
    style E fill:#fff8e1
    style F fill:#e8f5e8
    style G fill:#ffebee
"""
    
    try:
        # Create exporter
        exporter = DrawIOExporter()
        print("✅ DrawIOExporter created successfully")
        
        # Create temporary directory for test
        with tempfile.TemporaryDirectory() as temp_dir:
            output_path = os.path.join(temp_dir, "test_diagram")
            
            # Export to Draw.io
            result_file = exporter.export_mermaid_diagram(
                test_mermaid, 
                "Test Agent Workflow", 
                output_path
            )
            
            print(f"✅ Export completed: {result_file}")
            
            # Verify file exists and has content
            if os.path.exists(result_file):
                with open(result_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                print(f"✅ File created with {len(content)} characters")
                
                # Check if it contains expected Draw.io XML structure
                if '<mxfile' in content and 'mermaid' in content.lower():
                    print("✅ File contains valid Draw.io XML with Mermaid content")
                    return True
                else:
                    print("❌ File doesn't contain expected Draw.io structure")
                    return False
            else:
                print("❌ Output file was not created")
                return False
                
    except Exception as e:
        print(f"❌ Export failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_render_mermaid_integration():
    """Test that render_mermaid function accepts diagram_type parameter."""
    
    print("\n🧪 Testing render_mermaid integration...")
    
    try:
        # Import the main app class
        from streamlit_app import AutomatedAIAssessmentUI
        
        # Create instance (this might fail due to Streamlit context, but we just want to check the method)
        print("✅ AutomatedAIAssessmentUI class imported successfully")
        
        # Check if render_mermaid method exists and has correct signature
        import inspect
        if hasattr(AutomatedAIAssessmentUI, 'render_mermaid'):
            method = getattr(AutomatedAIAssessmentUI, 'render_mermaid')
            sig = inspect.signature(method)
            params = list(sig.parameters.keys())
            
            print(f"✅ render_mermaid method found with parameters: {params}")
            
            if 'diagram_type' in params:
                print("✅ diagram_type parameter is present")
                return True
            else:
                print("❌ diagram_type parameter is missing")
                return False
        else:
            print("❌ render_mermaid method not found")
            return False
            
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False

if __name__ == "__main__":
    print("🚀 Starting Draw.io Export Tests...\n")
    
    # Test 1: Basic export functionality
    export_test = test_drawio_export()
    
    # Test 2: Integration with render_mermaid
    integration_test = test_render_mermaid_integration()
    
    print(f"\n📊 Test Results:")
    print(f"   Draw.io Export: {'✅ PASS' if export_test else '❌ FAIL'}")
    print(f"   Integration:    {'✅ PASS' if integration_test else '❌ FAIL'}")
    
    if export_test and integration_test:
        print("\n🎉 All tests passed! Draw.io export should be working properly.")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed. Please check the issues above.")
        sys.exit(1)