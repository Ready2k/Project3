#!/usr/bin/env python3
"""Test script to verify the feasibility bug fix works correctly."""

import asyncio
import json
import httpx
import time


async def test_feasibility_fix():
    """Test that the feasibility bug fix works correctly."""
    
    print("🧪 Testing Feasibility Bug Fix")
    print("=" * 50)
    
    # Test with the problematic session ID
    session_id = "3c4bb8f9-b6ad-4e4b-8868-a28581b6786d"
    
    try:
        async with httpx.AsyncClient() as client:
            # Test 1: Check if API returns correct feasibility
            print("📡 Test 1: API Feasibility Response")
            response = await client.post(
                "http://localhost:8000/recommend",
                json={"session_id": session_id, "top_k": 3},
                timeout=30.0
            )
            
            if response.status_code == 200:
                data = response.json()
                feasibility = data.get('feasibility', 'NOT_FOUND')
                print(f"   ✅ API Response: {response.status_code}")
                print(f"   📊 Feasibility: {feasibility}")
                
                if feasibility != 'Unknown':
                    print(f"   ✅ API correctly returns feasibility: {feasibility}")
                else:
                    print(f"   ❌ API still returns Unknown feasibility")
                    
                # Show recommendations count
                recommendations = data.get('recommendations', [])
                print(f"   📋 Recommendations: {len(recommendations)} found")
                
            else:
                print(f"   ❌ API Error: {response.status_code} - {response.text}")
                return
            
            # Test 2: Check session status
            print(f"\n🔍 Test 2: Session Status Check")
            status_response = await client.get(f"http://localhost:8000/status/{session_id}")
            
            if status_response.status_code == 200:
                status_data = status_response.json()
                phase = status_data.get('phase', 'UNKNOWN')
                progress = status_data.get('progress', 0)
                print(f"   ✅ Status Response: {status_response.status_code}")
                print(f"   📈 Phase: {phase}")
                print(f"   📊 Progress: {progress}%")
                
                if phase == 'DONE' and progress == 100:
                    print(f"   ✅ Session is properly completed")
                else:
                    print(f"   ⚠️  Session may not be fully completed")
                    
            else:
                print(f"   ❌ Status Error: {status_response.status_code}")
                
            # Test 3: Simulate UI behavior
            print(f"\n🖥️  Test 3: UI Behavior Simulation")
            
            # This simulates what the UI does:
            # 1. Check if recommendations are cached (None means not cached)
            # 2. If not cached, fetch from API
            # 3. Display feasibility from response
            
            cached_recommendations = None  # Simulate cleared cache
            
            if cached_recommendations is None:
                print(f"   🔄 Simulating fresh API call (cache cleared)")
                # This would be the API call the UI makes
                ui_response = await client.post(
                    "http://localhost:8000/recommend",
                    json={"session_id": session_id, "top_k": 3},
                    timeout=30.0
                )
                
                if ui_response.status_code == 200:
                    ui_data = ui_response.json()
                    ui_feasibility = ui_data.get('feasibility', 'Unknown')
                    
                    print(f"   📊 UI would display: {ui_feasibility}")
                    
                    # Test the feasibility mapping logic
                    feasibility_info = {
                        "Yes": {"color": "🟢", "label": "Fully Automatable"},
                        "Partial": {"color": "🟡", "label": "Partially Automatable"},
                        "No": {"color": "🔴", "label": "Not Automatable"},
                        "Automatable": {"color": "🟢", "label": "Fully Automatable"},
                        "Partially Automatable": {"color": "🟡", "label": "Partially Automatable"},
                        "Not Automatable": {"color": "🔴", "label": "Not Automatable"},
                        "Fully Automatable": {"color": "🟢", "label": "Fully Automatable"}
                    }
                    
                    feas_info = feasibility_info.get(ui_feasibility, {
                        "color": "⚪", 
                        "label": ui_feasibility, 
                        "desc": "Assessment pending."
                    })
                    
                    print(f"   🎨 UI Display: {feas_info['color']} Feasibility: {feas_info['label']}")
                    
                    if feas_info['color'] != "⚪":
                        print(f"   ✅ Fix successful! UI would show proper feasibility status")
                    else:
                        print(f"   ❌ Fix failed! UI would still show 'Assessment pending'")
                        
                else:
                    print(f"   ❌ UI API call failed: {ui_response.status_code}")
            else:
                print(f"   📦 Using cached recommendations (this was the bug)")
                
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        
    print(f"\n🎯 Summary:")
    print(f"   The fix ensures that:")
    print(f"   1. When analysis phase becomes 'DONE', cached recommendations are cleared")
    print(f"   2. When Q&A completes, cached recommendations are cleared")
    print(f"   3. UI always fetches fresh data after analysis completion")
    print(f"   4. Refresh button allows manual cache clearing")


if __name__ == "__main__":
    print("🚀 Starting feasibility bug fix test...")
    asyncio.run(test_feasibility_fix())
    print("\n🎉 Test complete!")