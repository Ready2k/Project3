#!/usr/bin/env python3
"""
Debug script to identify the specific Streamlit error.
"""

import asyncio
import httpx
import json

API_BASE_URL = "http://localhost:8000"

async def debug_api_call():
    """Debug the API call that's failing in Streamlit."""
    print("🔍 Debugging Streamlit API Error")
    print("=" * 40)
    
    # Use the same session ID from the logs
    session_id = "ed550eb4-a3e2-4cf3-bc7c-37f9ad8e2c1a"
    
    try:
        print(f"1. Testing API call with session: {session_id}")
        
        async with httpx.AsyncClient(timeout=120.0) as client:
            response = await client.post(
                f"{API_BASE_URL}/recommend",
                json={"session_id": session_id, "top_k": 3}
            )
            
            print(f"   Status Code: {response.status_code}")
            
            if response.status_code == 404:
                print("   ❌ Session not found")
                return
            elif response.status_code != 200:
                print(f"   ❌ API error: {response.status_code} - {response.text}")
                return
            
            # Try to parse JSON
            try:
                data = response.json()
                print("   ✅ JSON parsing successful")
                print(f"   Response keys: {list(data.keys())}")
                
                if "recommendations" in data:
                    print(f"   Recommendations count: {len(data['recommendations'])}")
                    if data['recommendations']:
                        rec = data['recommendations'][0]
                        print(f"   First rec keys: {list(rec.keys())}")
                        print(f"   Confidence: {rec.get('confidence', 'N/A')}")
                        print(f"   Feasibility: {rec.get('feasibility', 'N/A')}")
                
                return data
                
            except json.JSONDecodeError as e:
                print(f"   ❌ JSON parsing failed: {e}")
                print(f"   Raw response: {response.text[:200]}...")
                return None
                
    except Exception as e:
        print(f"   ❌ Request failed: {type(e).__name__}: {e}")
        return None

def test_asyncio_run():
    """Test if asyncio.run works in this context."""
    print("\n2. Testing asyncio.run compatibility...")
    
    try:
        result = asyncio.run(debug_api_call())
        if result:
            print("   ✅ asyncio.run works correctly")
            return True
        else:
            print("   ⚠️  asyncio.run executed but returned None")
            return False
    except Exception as e:
        print(f"   ❌ asyncio.run failed: {type(e).__name__}: {e}")
        return False

if __name__ == "__main__":
    success = test_asyncio_run()
    
    if success:
        print("\n🎉 No issues found with the API call!")
        print("The error might be in Streamlit's session state handling.")
    else:
        print("\n🔍 Found the issue! Check the error details above.")