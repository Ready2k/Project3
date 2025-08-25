#!/usr/bin/env python3
"""
Streamlit application runner for the AAA system.

This script starts the Streamlit UI with the new modular architecture.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Set environment variables for Streamlit
os.environ.setdefault('STREAMLIT_SERVER_PORT', '8501')
os.environ.setdefault('STREAMLIT_SERVER_ADDRESS', '0.0.0.0')
os.environ.setdefault('STREAMLIT_BROWSER_SERVER_ADDRESS', 'localhost')

def main():
    """Run the Streamlit application."""
    try:
        # Import streamlit
        import streamlit as st
        from streamlit.web import cli as stcli
        
        # Configure Streamlit to run our main app
        sys.argv = [
            "streamlit",
            "run",
            "streamlit_app.py",
            "--server.port=8501",
            "--server.address=0.0.0.0",
            "--browser.serverAddress=localhost"
        ]
        
        # Run Streamlit
        stcli.main()
        
    except ImportError as e:
        print(f"❌ Error importing Streamlit: {e}")
        print("💡 Please install Streamlit: pip install streamlit")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error starting Streamlit: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()