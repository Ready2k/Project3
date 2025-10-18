#!/usr/bin/env python3
"""Script to run the Streamlit UI for Automated AI Assessment (AAA)."""

import subprocess
import sys
from pathlib import Path
from app.utils.logger import app_logger

def main():
    """Run the Streamlit application."""
    
    # Get the directory containing this script
    script_dir = Path(__file__).parent
    streamlit_app = script_dir / "streamlit_app.py"
    
    if not streamlit_app.exists():
        app_logger.error(f"Streamlit app not found at {streamlit_app}")
        sys.exit(1)
    
    # Run Streamlit with browser auto-open
    cmd = [
        sys.executable, "-m", "streamlit", "run", 
        str(streamlit_app),
        "--server.port", "8500",
        "--server.address", "0.0.0.0",
        "--browser.serverAddress", "localhost"
    ]
    
    app_logger.info("🚀 Starting Automated AI Assessment (AAA) Streamlit UI...")
    app_logger.info("📱 The app will automatically open in your browser at: http://localhost:8500")
    app_logger.info("🔧 Make sure the FastAPI backend is running at: http://localhost:8000")
    app_logger.info("💡 If the browser doesn't open automatically, visit: http://localhost:8500")
    app_logger.info(f"Command: {' '.join(cmd)}")
    
    try:
        subprocess.run(cmd, check=True)
    except KeyboardInterrupt:
        app_logger.info("Streamlit app stopped by user")
    except subprocess.CalledProcessError as e:
        app_logger.error(f"Error running Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()