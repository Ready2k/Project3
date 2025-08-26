#!/usr/bin/env python3
"""
Test script to verify Graphviz installation for AAA Infrastructure Diagrams.
Run this script to check if your system is ready for infrastructure diagrams.
"""

import sys
import subprocess
import tempfile
import os
from pathlib import Path

def test_graphviz_command():
    """Test if the dot command is available."""
    print("🔍 Testing Graphviz 'dot' command...")
    try:
        result = subprocess.run(['dot', '-V'], capture_output=True, text=True, timeout=10)
        if result.returncode == 0:
            version_info = result.stderr.strip()  # Graphviz outputs version to stderr
            print(f"✅ Graphviz found: {version_info}")
            return True
        else:
            print(f"❌ Graphviz command failed: {result.stderr}")
            return False
    except FileNotFoundError:
        print("❌ Graphviz 'dot' command not found in PATH")
        return False
    except subprocess.TimeoutExpired:
        print("❌ Graphviz command timed out")
        return False
    except Exception as e:
        print(f"❌ Error testing Graphviz: {e}")
        return False

def test_diagrams_library():
    """Test if the diagrams library is available."""
    print("\n🔍 Testing Python 'diagrams' library...")
    try:
        import diagrams
        print(f"✅ Diagrams library found: version {diagrams.__version__}")
        return True
    except ImportError:
        print("❌ Diagrams library not found")
        print("   Install with: pip install diagrams")
        return False
    except Exception as e:
        print(f"❌ Error importing diagrams: {e}")
        return False

def test_simple_diagram():
    """Test creating a simple diagram."""
    print("\n🔍 Testing diagram generation...")
    
    try:
        from diagrams import Diagram
        from diagrams.aws.compute import Lambda
        from diagrams.aws.database import Dynamodb
        
        with tempfile.TemporaryDirectory() as temp_dir:
            # Change to temp directory
            original_cwd = os.getcwd()
            os.chdir(temp_dir)
            
            try:
                # Create a simple diagram
                with Diagram("Test Infrastructure", show=False, filename="test_diagram"):
                    lambda_func = Lambda("Function")
                    database = Dynamodb("Database")
                    lambda_func >> database
                
                # Check if files were created
                png_file = Path("test_diagram.png")
                if png_file.exists():
                    file_size = png_file.stat().st_size
                    print(f"✅ Diagram generated successfully: {png_file} ({file_size} bytes)")
                    return True
                else:
                    print("❌ Diagram file not created")
                    return False
                    
            finally:
                os.chdir(original_cwd)
                
    except ImportError as e:
        print(f"❌ Missing required imports: {e}")
        return False
    except Exception as e:
        print(f"❌ Error generating diagram: {e}")
        return False

def print_installation_help():
    """Print installation instructions."""
    print("\n" + "="*60)
    print("📥 INSTALLATION INSTRUCTIONS")
    print("="*60)
    
    print("\n🪟 Windows:")
    print("   choco install graphviz")
    print("   # OR")
    print("   winget install graphviz")
    
    print("\n🍎 macOS:")
    print("   brew install graphviz")
    
    print("\n🐧 Linux (Ubuntu/Debian):")
    print("   sudo apt-get install graphviz")
    
    print("\n🐧 Linux (CentOS/RHEL):")
    print("   sudo yum install graphviz")
    
    print("\n📦 Python diagrams library:")
    print("   pip install diagrams")
    
    print("\n✅ Verify installation:")
    print("   dot -V")
    print("   python -c \"import diagrams; print(diagrams.__version__)\"")

def main():
    """Run all tests."""
    print("🧪 AAA Infrastructure Diagram Requirements Test")
    print("="*50)
    
    # Test results
    graphviz_ok = test_graphviz_command()
    diagrams_ok = test_diagrams_library()
    
    if graphviz_ok and diagrams_ok:
        diagram_ok = test_simple_diagram()
    else:
        diagram_ok = False
    
    # Summary
    print("\n" + "="*50)
    print("📊 TEST SUMMARY")
    print("="*50)
    
    print(f"Graphviz Command:     {'✅ PASS' if graphviz_ok else '❌ FAIL'}")
    print(f"Diagrams Library:     {'✅ PASS' if diagrams_ok else '❌ FAIL'}")
    print(f"Diagram Generation:   {'✅ PASS' if diagram_ok else '❌ FAIL'}")
    
    if graphviz_ok and diagrams_ok and diagram_ok:
        print("\n🎉 SUCCESS! Your system is ready for AAA Infrastructure Diagrams!")
        print("   You can now use the Infrastructure Diagram feature in the AAA application.")
    else:
        print("\n⚠️  ISSUES FOUND! Infrastructure diagrams may not work properly.")
        print("   Please follow the installation instructions below.")
        print_installation_help()
    
    return 0 if (graphviz_ok and diagrams_ok and diagram_ok) else 1

if __name__ == "__main__":
    sys.exit(main())