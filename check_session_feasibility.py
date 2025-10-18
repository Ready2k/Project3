#!/usr/bin/env python3
"""
Check the current session feasibility data.
"""

import requests
import json

def check_session_feasibility():
    """Check the current session feasibility."""
    
    session_id = "a2af4df3-ec7d-4b97-bc7b-6af716587c66"
    
    print(f"🔍 Checking session {session_id}...")
    
    try:
        # Get session status
        status_response = requests.get(f"http://localhost:8000/status/{session_id}")
        if status_response.status_code == 200:
            status_data = status_response.json()
            requirements = status_data.get("requirements", {})
            
            print("📊 Session Requirements:")
            print(f"   Phase: {status_data.get('phase')}")
            print(f"   Progress: {status_data.get('progress')}%")
            
            # Check LLM analysis fields
            llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
            llm_confidence = requirements.get("llm_analysis_confidence_level")
            
            print(f"\n🤖 LLM Analysis:")
            print(f"   Feasibility: {llm_feasibility}")
            print(f"   Confidence: {llm_confidence}")
            
            # Now test the recommendations endpoint
            print(f"\n🎯 Testing /recommend endpoint...")
            rec_response = requests.post(
                "http://localhost:8000/recommend",
                json={"session_id": session_id, "top_k": 3}
            )
            
            if rec_response.status_code == 200:
                rec_data = rec_response.json()
                api_feasibility = rec_data.get("feasibility")
                
                print(f"   API Feasibility: {api_feasibility}")
                print(f"   Expected: {llm_feasibility}")
                
                if api_feasibility == llm_feasibility:
                    print("✅ SUCCESS: API returns correct LLM feasibility!")
                else:
                    print("❌ ISSUE: API feasibility doesn't match LLM analysis")
                    
            else:
                print(f"❌ Error calling /recommend: {rec_response.status_code}")
                print(rec_response.text)
                
        else:
            print(f"❌ Error getting session status: {status_response.status_code}")
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    check_session_feasibility()