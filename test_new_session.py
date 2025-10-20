#!/usr/bin/env python3
"""Test the new session to see what's happening."""

import asyncio
import httpx

async def test_new_session():
    """Test the new session."""
    
    session_id = "5137e580-add9-4209-bf51-d2a7c4b2e3e2"
    
    print("🔍 Testing New Session")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            # Check session status
            print("📡 1. Checking Session Status")
            status_response = await client.get(f"http://localhost:8000/status/{session_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                print(f"   ✅ Session Status: {status_data.get('phase')} ({status_data.get('progress')}%)")
                
                # Check if LLM analysis is in requirements
                requirements = status_data.get('requirements', {})
                llm_feasibility = requirements.get('llm_analysis_automation_feasibility')
                print(f"   📊 LLM Analysis Feasibility: {llm_feasibility}")
                
                if status_data.get('phase') == 'DONE':
                    print("   ✅ Session is completed, should be able to get recommendations")
                else:
                    print(f"   ⚠️  Session not completed yet: {status_data.get('phase')}")
                    return
                
            else:
                print(f"   ❌ Status check failed: {status_response.status_code}")
                return

            # Try to call recommend endpoint
            print(f"\n📡 2. Testing /recommend Endpoint")
            try:
                rec_response = await client.post(
                    "http://localhost:8000/recommend",
                    json={"session_id": session_id, "top_k": 3},
                    timeout=10.0  # Shorter timeout for testing
                )
                
                if rec_response.status_code == 200:
                    rec_data = rec_response.json()
                    print(f"   ✅ Recommend Response Keys: {list(rec_data.keys())}")
                    print(f"   📊 API Response Feasibility: {rec_data.get('feasibility', 'NOT_FOUND')}")
                    
                    if 'error' in rec_data:
                        print(f"   🚨 API ERROR: {rec_data['error']}")
                    
                else:
                    print(f"   ❌ Recommend API Error: {rec_response.status_code}")
                    print(f"   Error: {rec_response.text}")
                    
            except Exception as e:
                print(f"   ❌ Recommend request failed: {e}")
                
    except Exception as e:
        print(f"❌ Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_new_session())