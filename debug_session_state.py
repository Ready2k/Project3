#!/usr/bin/env python3
"""Debug script to check what's in session state for the problematic session."""

import asyncio
import httpx

async def debug_session_state():
    """Debug the session state and API response."""
    
    session_id = "7d21965c-b6c5-43cd-84fe-7be18aa3999f"
    
    print("🔍 Debugging Session State Issue")
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
                
            # Call the recommend endpoint
            print(f"\n📡 2. Calling /recommend Endpoint")
            rec_response = await client.post(
                "http://localhost:8000/recommend",
                json={"session_id": session_id, "top_k": 3},
                timeout=30.0
            )
            
            if rec_response.status_code == 200:
                rec_data = rec_response.json()
                print(f"   ✅ Recommend Response Keys: {list(rec_data.keys())}")
                print(f"   📊 API Response Feasibility: {rec_data.get('feasibility', 'NOT_FOUND')}")
                
                # Check if recommendations array exists
                if 'recommendations' in rec_data:
                    recommendations = rec_data['recommendations']
                    print(f"   📋 Recommendations Count: {len(recommendations)}")
                    if recommendations and len(recommendations) > 0:
                        first_rec = recommendations[0]
                        if isinstance(first_rec, dict):
                            print(f"   📊 First Recommendation Feasibility: {first_rec.get('feasibility', 'NOT_FOUND')}")
                
                # Simulate UI logic
                print(f"\n🖥️  3. Simulating UI Logic")
                
                # This is what the UI does
                rec = rec_data  # This is st.session_state.recommendations
                feasibility = rec.get('feasibility', 'Unknown')
                print(f"   📊 Primary extraction: '{feasibility}'")
                
                # Fallback logic
                if feasibility == 'Unknown':
                    print(f"   🔄 Trying fallbacks...")
                    
                    # Try recommendations fallback
                    if rec.get('recommendations') and len(rec['recommendations']) > 0:
                        first_rec = rec['recommendations'][0]
                        if isinstance(first_rec, dict):
                            alt_feasibility = first_rec.get('feasibility', 'Unknown')
                            if alt_feasibility != 'Unknown':
                                feasibility = alt_feasibility
                                print(f"   🔄 Using recommendation fallback: '{feasibility}'")
                
                print(f"   🎯 Final feasibility: '{feasibility}'")
                
                # Test UI mapping
                feasibility_info = {
                    "Automatable": {"color": "🟢", "label": "Fully Automatable"},
                    "Partially Automatable": {"color": "🟡", "label": "Partially Automatable"},
                    "Not Automatable": {"color": "🔴", "label": "Not Automatable"},
                }
                
                feas_info = feasibility_info.get(feasibility, {
                    "color": "⚪", 
                    "label": feasibility, 
                    "desc": "Assessment pending."
                })
                
                print(f"   🎨 UI Display: {feas_info['color']} Feasibility: {feas_info['label']}")
                
            else:
                print(f"   ❌ Recommend API Error: {rec_response.status_code}")
                print(f"   Error: {rec_response.text}")
                
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(debug_session_state())