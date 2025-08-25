#!/usr/bin/env python3
"""
Simple service starter for the AAA system.

This script starts both the API and Streamlit services with proper error handling.
"""

import subprocess
import time
import sys
import signal
import os
from pathlib import Path

def cleanup_processes():
    """Clean up any existing processes."""
    try:
        subprocess.run(["pkill", "-f", "uvicorn"], check=False)
        subprocess.run(["pkill", "-f", "streamlit"], check=False)
        time.sleep(2)
    except Exception:
        pass

def start_api():
    """Start the FastAPI server."""
    print("🚀 Starting FastAPI server...")
    try:
        api_process = subprocess.Popen([
            sys.executable, "-m", "uvicorn", 
            "app.api:app", 
            "--reload", 
            "--host", "0.0.0.0", 
            "--port", "8000"
        ])
        return api_process
    except Exception as e:
        print(f"❌ Failed to start API: {e}")
        return None

def start_streamlit():
    """Start the Streamlit server."""
    print("📱 Starting Streamlit UI...")
    try:
        streamlit_process = subprocess.Popen([
            sys.executable, "-m", "streamlit", 
            "run", "streamlit_app.py",
            "--server.port", "8501",
            "--server.address", "0.0.0.0",
            "--browser.serverAddress", "localhost"
        ])
        return streamlit_process
    except Exception as e:
        print(f"❌ Failed to start Streamlit: {e}")
        return None

def wait_for_service(url, service_name, timeout=30):
    """Wait for a service to become available."""
    import requests
    
    print(f"⏳ Waiting for {service_name} to start...")
    start_time = time.time()
    
    while time.time() - start_time < timeout:
        try:
            response = requests.get(url, timeout=5)
            if response.status_code == 200:
                print(f"✅ {service_name} is ready!")
                return True
        except:
            pass
        time.sleep(1)
    
    print(f"❌ {service_name} failed to start within {timeout} seconds")
    return False

def main():
    """Main function to start services."""
    print("🤖 Starting AAA System Services")
    print("=" * 40)
    
    # Clean up any existing processes
    cleanup_processes()
    
    # Start API server
    api_process = start_api()
    if not api_process:
        print("❌ Failed to start API server")
        sys.exit(1)
    
    # Wait for API to be ready
    if not wait_for_service("http://localhost:8000/health", "API"):
        api_process.terminate()
        sys.exit(1)
    
    # Start Streamlit
    streamlit_process = start_streamlit()
    if not streamlit_process:
        print("❌ Failed to start Streamlit")
        api_process.terminate()
        sys.exit(1)
    
    # Wait for Streamlit to be ready
    if not wait_for_service("http://localhost:8501", "Streamlit"):
        api_process.terminate()
        streamlit_process.terminate()
        sys.exit(1)
    
    print("\n🎉 All services started successfully!")
    print("🔧 API available at: http://localhost:8000")
    print("📱 Streamlit UI available at: http://localhost:8501")
    print("\n💡 Press Ctrl+C to stop all services")
    
    # Set up signal handler for graceful shutdown
    def signal_handler(sig, frame):
        print("\n🛑 Shutting down services...")
        api_process.terminate()
        streamlit_process.terminate()
        
        # Wait for processes to terminate
        api_process.wait()
        streamlit_process.wait()
        
        print("✅ All services stopped")
        sys.exit(0)
    
    signal.signal(signal.SIGINT, signal_handler)
    
    # Keep the script running
    try:
        while True:
            # Check if processes are still running
            if api_process.poll() is not None:
                print("❌ API process died unexpectedly")
                break
            if streamlit_process.poll() is not None:
                print("❌ Streamlit process died unexpectedly")
                break
            time.sleep(1)
    except KeyboardInterrupt:
        pass
    
    # Clean shutdown
    signal_handler(None, None)

if __name__ == "__main__":
    main()