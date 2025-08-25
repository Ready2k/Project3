#!/usr/bin/env python3
"""
Test the status endpoint to ensure it's working consistently.
"""

import requests
import time

API_BASE = "http://localhost:8000"

def test_status_endpoint():
    """Test the status endpoint multiple times to check for consistency."""
    print("🔍 Testing Status Endpoint Reliability")
    print("=" * 40)
    
    # Use the known session ID
    session_id = "ed550eb4-a3e2-4cf3-bc7c-37f9ad8e2c1a"
    
    success_count = 0
    total_tests = 10
    
    for i in range(total_tests):
        try:
            start_time = time.time()
            response = requests.get(f"{API_BASE}/status/{session_id}", timeout=10)
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                print(f"Test {i+1:2d}: ✅ Success ({end_time-start_time:.3f}s) - Phase: {data.get('phase', 'Unknown')}")
                success_count += 1
            else:
                print(f"Test {i+1:2d}: ❌ HTTP {response.status_code}")
                
        except requests.exceptions.Timeout:
            print(f"Test {i+1:2d}: ⏰ Timeout")
        except Exception as e:
            print(f"Test {i+1:2d}: ❌ Error: {e}")
        
        # Small delay between tests
        time.sleep(0.5)
    
    print(f"\nResults: {success_count}/{total_tests} successful ({success_count/total_tests*100:.1f}%)")
    
    if success_count == total_tests:
        print("🎉 Status endpoint is working consistently!")
    elif success_count >= total_tests * 0.8:
        print("⚠️  Status endpoint is mostly working but has some issues.")
    else:
        print("❌ Status endpoint has significant reliability issues.")

if __name__ == "__main__":
    test_status_endpoint()