#!/usr/bin/env python3
"""
Test the current session to see what the API returns.
"""

import requests
import json

def test_current_session():
    """Test the current session feasibility."""
    
    session_id = "bdda5420-504e-4590-9964-06bff1e38ac1"
    
    print(f"🔍 Testing current session: {session_id}")
    
    try:
        # Test the recommendations endpoint
        print(f"\n🎯 Calling /recommend endpoint...")
        rec_response = requests.post(
            "http://localhost:8000/recommend",
            json={"session_id": session_id, "top_k": 3}
        )
        
        if rec_response.status_code == 200:
            rec_data = rec_response.json()
            feasibility = rec_data.get("feasibility")
            
            print(f"✅ API Response:")
            print(f"   Feasibility: {feasibility}")
            print(f"   Tech Stack Count: {len(rec_data.get('tech_stack', []))}")
            print(f"   Has Reasoning: {bool(rec_data.get('reasoning'))}")
            
            if feasibility == "Automatable":
                print(f"\n🎉 SUCCESS: API correctly returns 'Automatable'!")
                print(f"   The UI should show: 🟢 Feasibility: Fully Automatable")
                print(f"   If you're still seeing ⚪ Unknown, the UI needs to refresh.")
            else:
                print(f"\n❌ ISSUE: Expected 'Automatable', got '{feasibility}'")
                
        else:
            print(f"❌ API Error: {rec_response.status_code}")
            print(rec_response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_current_session()