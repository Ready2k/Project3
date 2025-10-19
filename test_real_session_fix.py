#!/usr/bin/env python3
"""Test script to verify the feasibility fix works with a real API call."""

import asyncio
import json
import httpx
import time


async def test_with_new_session():
    """Test by creating a new session and checking feasibility display."""
    
    print("🧪 Testing Feasibility Fix with New Session")
    print("=" * 50)
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Create a new session
            print("📡 Test 1: Creating New Session")
            
            ingest_request = {
                "source": "text",
                "payload": {
                    "text": "Automate inventory management for a warehouse with barcode scanning and real-time updates",
                    "domain": "logistics",
                    "pattern_types": ["agentic"]
                },
                "provider_config": {
                    "provider": "fake",  # Use fake provider for testing
                    "model": "fake-model"
                }
            }
            
            response = await client.post(
                "http://localhost:8000/ingest",
                json=ingest_request,
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                session_id = data.get('session_id')
                print(f"   ✅ Session created: {session_id}")
                
                # Wait for processing to complete
                print(f"\n🔄 Waiting for processing to complete...")
                max_attempts = 30
                for attempt in range(max_attempts):
                    status_response = await client.get(f"http://localhost:8000/status/{session_id}")
                    if status_response.status_code == 200:
                        status_data = status_response.json()
                        phase = status_data.get('phase', 'UNKNOWN')
                        progress = status_data.get('progress', 0)
                        print(f"   📈 Phase: {phase}, Progress: {progress}%")
                        
                        if phase == 'DONE' and progress == 100:
                            print(f"   ✅ Processing complete!")
                            break
                    
                    await asyncio.sleep(2)
                else:
                    print(f"   ⚠️  Processing didn't complete in time, continuing anyway...")
                
                # Test 2: Get recommendations and check feasibility
                print(f"\n📊 Test 2: Getting Recommendations")
                rec_response = await client.post(
                    "http://localhost:8000/recommend",
                    json={"session_id": session_id, "top_k": 3},
                    timeout=30.0
                )
                
                if rec_response.status_code == 200:
                    rec_data = rec_response.json()
                    print(f"   ✅ Recommendations received")
                    
                    # Debug the response structure
                    print(f"\n🔍 Response Structure Analysis:")
                    print(f"   - Response keys: {list(rec_data.keys())}")
                    print(f"   - Feasibility field: {'feasibility' in rec_data}")
                    
                    if 'feasibility' in rec_data:
                        feasibility = rec_data['feasibility']
                        print(f"   - Feasibility value: '{feasibility}'")
                        
                        # Test the UI mapping logic
                        feasibility_info = {
                            "Yes": {"color": "🟢", "label": "Fully Automatable"},
                            "Partial": {"color": "🟡", "label": "Partially Automatable"},
                            "No": {"color": "🔴", "label": "Not Automatable"},
                            "Automatable": {"color": "🟢", "label": "Fully Automatable"},
                            "Partially Automatable": {"color": "🟡", "label": "Partially Automatable"},
                            "Not Automatable": {"color": "🔴", "label": "Not Automatable"},
                            "Fully Automatable": {"color": "🟢", "label": "Fully Automatable"}
                        }
                        
                        feas_info = feasibility_info.get(feasibility, {
                            "color": "⚪", 
                            "label": feasibility, 
                            "desc": "Assessment pending."
                        })
                        
                        print(f"   🎨 UI would display: {feas_info['color']} Feasibility: {feas_info['label']}")
                        
                        if feas_info['color'] != "⚪":
                            print(f"   ✅ SUCCESS: Feasibility properly extracted and mapped!")
                        else:
                            print(f"   ❌ ISSUE: Feasibility still shows as 'Assessment pending'")
                    else:
                        print(f"   ❌ No feasibility field in response")
                        
                        # Check recommendations for feasibility
                        if 'recommendations' in rec_data and rec_data['recommendations']:
                            first_rec = rec_data['recommendations'][0]
                            if isinstance(first_rec, dict) and 'feasibility' in first_rec:
                                fallback_feasibility = first_rec['feasibility']
                                print(f"   🔄 Fallback feasibility from first recommendation: '{fallback_feasibility}'")
                            else:
                                print(f"   ❌ No feasibility in first recommendation either")
                
                else:
                    print(f"   ❌ Recommendations request failed: {rec_response.status_code}")
                    print(f"   Error: {rec_response.text}")
                
            else:
                print(f"   ❌ Session creation failed: {response.status_code}")
                print(f"   Error: {response.text}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


async def test_health_check():
    """Test API health to ensure it's working."""
    
    print("🏥 Testing API Health")
    print("=" * 30)
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get("http://localhost:8000/health", timeout=10.0)
            
            if response.status_code == 200:
                health_data = response.json()
                print(f"   ✅ API is healthy")
                print(f"   📊 Status: {health_data.get('status')}")
                print(f"   🔢 Version: {health_data.get('version')}")
                return True
            else:
                print(f"   ❌ API health check failed: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"   ❌ API health check error: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting real session feasibility fix test...")
    
    async def run_tests():
        # First check API health
        if await test_health_check():
            print()
            await test_with_new_session()
        else:
            print("❌ API is not healthy, skipping session test")
    
    asyncio.run(run_tests())
    print("\n🎉 Real session test complete!")