#!/usr/bin/env python3
"""Script to run the Streamlit UI for AgenticOrNot."""

import subprocess
import sys
from pathlib import Path

def main():
    """Run the Streamlit application."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    streamlit_app = script_dir / "streamlit_app.py"
    
    if not streamlit_app.exists():
        print(f"Error: Streamlit app not found at {streamlit_app}")
        sys.exit(1)
    
    # Run Streamlit with browser auto-open
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(streamlit_app),
        "--server.port", "8501",
        "--server.address", "0.0.0.0",
        "--browser.serverAddress", "localhost"
    ]
    
    print("🚀 Starting AgenticOrNot Streamlit UI...")
    print("📱 The app will automatically open in your browser at: http://localhost:8501")
    print("🔧 Make sure the FastAPI backend is running at: http://localhost:8000")
    print("💡 If the browser doesn't open automatically, visit: http://localhost:8501")
    print("")
    print(f"Command: {' '.join(cmd)}")
    print("")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        print("\nStreamlit app stopped.")
    except subprocess.CalledProcessError as e:
        print(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()