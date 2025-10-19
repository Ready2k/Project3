#!/usr/bin/env python3
"""Test script to verify the feasibility fix works with the original problematic session."""

import asyncio
import json
import httpx
import time


async def test_original_session():
    """Test with the original problematic session ID."""
    
    print("🧪 Testing Original Problematic Session")
    print("=" * 50)
    
    # The original problematic session ID
    session_id = "3c4bb8f9-b6ad-4e4b-8868-a28581b6786d"
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Check session status
            print(f"📡 Test 1: Checking Session Status")
            print(f"   Session ID: {session_id}")
            
            try:
                status_response = await client.get(f"http://localhost:8000/status/{session_id}", timeout=10.0)
                
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    phase = status_data.get('phase', 'UNKNOWN')
                    progress = status_data.get('progress', 0)
                    print(f"   ✅ Session exists")
                    print(f"   📈 Phase: {phase}, Progress: {progress}%")
                    
                    if phase == 'DONE' and progress == 100:
                        print(f"   ✅ Session is completed")
                    else:
                        print(f"   ⚠️  Session may not be fully completed")
                        
                elif status_response.status_code == 404:
                    print(f"   ❌ Session not found (404)")
                    print(f"   💡 This is expected if the session has expired")
                    return
                else:
                    print(f"   ❌ Status check failed: {status_response.status_code}")
                    return
                    
            except Exception as e:
                print(f"   ❌ Status check error: {e}")
                return
            
            # Test 2: Get recommendations
            print(f"\n📊 Test 2: Getting Recommendations")
            
            try:
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
                    print(f"   - Has feasibility field: {'feasibility' in rec_data}")
                    
                    if 'feasibility' in rec_data:
                        feasibility = rec_data['feasibility']
                        print(f"   - Feasibility value: '{feasibility}'")
                        
                        # Test the UI mapping logic (same as in streamlit_app.py)
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
                        
                        print(f"\n🎨 UI Display Test:")
                        print(f"   - Before fix: ⚪ Feasibility: Unknown - Assessment pending")
                        print(f"   - After fix:  {feas_info['color']} Feasibility: {feas_info['label']}")
                        
                        if feas_info['color'] != "⚪":
                            print(f"   ✅ SUCCESS: Fix resolved the issue!")
                            print(f"   🎯 The UI will now show proper feasibility instead of 'Unknown'")
                        else:
                            print(f"   ❌ ISSUE: Still showing 'Assessment pending'")
                            
                            # Try fallback logic
                            if 'recommendations' in rec_data and rec_data['recommendations']:
                                first_rec = rec_data['recommendations'][0]
                                if isinstance(first_rec, dict) and 'feasibility' in first_rec:
                                    fallback_feasibility = first_rec['feasibility']
                                    print(f"   🔄 Fallback feasibility available: '{fallback_feasibility}'")
                                    
                                    fallback_info = feasibility_info.get(fallback_feasibility, {
                                        "color": "⚪", 
                                        "label": fallback_feasibility, 
                                        "desc": "Assessment pending."
                                    })
                                    
                                    if fallback_info['color'] != "⚪":
                                        print(f"   ✅ Fallback would work: {fallback_info['color']} {fallback_info['label']}")
                    else:
                        print(f"   ❌ No feasibility field in response")
                        
                        # Check recommendations for feasibility
                        if 'recommendations' in rec_data and rec_data['recommendations']:
                            print(f"   🔍 Checking recommendations for feasibility...")
                            for i, rec in enumerate(rec_data['recommendations']):
                                if isinstance(rec, dict) and 'feasibility' in rec:
                                    rec_feasibility = rec['feasibility']
                                    print(f"     - Recommendation {i+1}: '{rec_feasibility}'")
                
                elif rec_response.status_code == 404:
                    print(f"   ❌ Session not found for recommendations (404)")
                else:
                    print(f"   ❌ Recommendations request failed: {rec_response.status_code}")
                    print(f"   Error: {rec_response.text}")
                    
            except Exception as e:
                print(f"   ❌ Recommendations request error: {e}")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting original session feasibility fix test...")
    print("🎯 Testing the specific session mentioned in the bug report")
    print()
    
    asyncio.run(test_original_session())
    print("\n🎉 Original session test complete!")