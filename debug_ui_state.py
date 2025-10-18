#!/usr/bin/env python3
"""
Debug script to check what the UI should be showing.
"""

import requests
import json

def debug_ui_state():
    """Debug the UI state for the current session."""
    
    session_id = "a2af4df3-ec7d-4b97-bc7b-6af716587c66"
    
    print(f"🔍 Debugging UI state for session {session_id}...")
    
    try:
        # Test the recommendations endpoint that the UI calls
        print(f"\n🎯 Testing /recommend endpoint (what UI calls)...")
        rec_response = requests.post(
            "http://localhost:8000/recommend",
            json={"session_id": session_id, "top_k": 3}
        )
        
        if rec_response.status_code == 200:
            rec_data = rec_response.json()
            
            print(f"📊 API Response:")
            print(f"   Feasibility: {rec_data.get('feasibility')}")
            print(f"   Tech Stack: {rec_data.get('tech_stack', [])}")
            print(f"   Reasoning: {rec_data.get('reasoning', 'N/A')[:100]}...")
            
            # Check what the UI mapping would show
            feasibility = rec_data.get('feasibility', 'Unknown')
            feasibility_info = {
                "Yes": {"color": "🟢", "label": "Fully Automatable"},
                "Partial": {"color": "🟡", "label": "Partially Automatable"},
                "No": {"color": "🔴", "label": "Not Automatable"},
                "Automatable": {"color": "🟢", "label": "Fully Automatable"},
                "Partially Automatable": {"color": "🟡", "label": "Partially Automatable"},
                "Not Automatable": {"color": "🔴", "label": "Not Automatable"},
                "Fully Automatable": {"color": "🟢", "label": "Fully Automatable"}
            }
            
            feas_info = feasibility_info.get(feasibility, {"color": "⚪", "label": feasibility})
            
            print(f"\n🎨 UI Display Mapping:")
            print(f"   Raw Feasibility: '{feasibility}'")
            print(f"   UI Display: {feas_info['color']} Feasibility: {feas_info['label']}")
            
            if feasibility == "Automatable":
                print("✅ API returns 'Automatable' - UI should show green checkmark")
            else:
                print(f"❌ Unexpected feasibility value: {feasibility}")
                
        else:
            print(f"❌ Error calling /recommend: {rec_response.status_code}")
            print(rec_response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_ui_state()