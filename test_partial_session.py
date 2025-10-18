#!/usr/bin/env python3
"""
Test the partial feasibility session to verify the fix is working.
"""

import requests
import json

def test_partial_session():
    """Test the session with partial feasibility."""
    
    session_id = "3e3d72cd-4c73-4d54-9561-3f3ac3bfecc0"
    
    print(f"🔍 Testing session: {session_id}")
    
    try:
        # Get session status first
        print(f"\n📊 Getting session status...")
        status_response = requests.get(f"http://localhost:8000/status/{session_id}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            requirements = status_data.get("requirements", {})
            
            print(f"   Phase: {status_data.get('phase')}")
            print(f"   Progress: {status_data.get('progress')}%")
            
            # Check LLM analysis
            llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
            llm_confidence = requirements.get("llm_analysis_confidence_level")
            
            print(f"\n🤖 LLM Analysis:")
            print(f"   Feasibility: {llm_feasibility}")
            print(f"   Confidence: {llm_confidence}")
            
        else:
            print(f"❌ Error getting session status: {status_response.status_code}")
            return
            
        # Test the recommendations endpoint
        print(f"\n🎯 Testing /recommend endpoint...")
        rec_response = requests.post(
            "http://localhost:8000/recommend",
            json={"session_id": session_id, "top_k": 3}
        )
        
        if rec_response.status_code == 200:
            rec_data = rec_response.json()
            api_feasibility = rec_data.get("feasibility")
            
            print(f"   API Feasibility: {api_feasibility}")
            
            # Check if API and LLM match
            if api_feasibility == llm_feasibility:
                print(f"✅ SUCCESS: API correctly uses LLM feasibility!")
                
                # Show what UI should display
                feasibility_mapping = {
                    "Automatable": "🟢 Feasibility: Fully Automatable",
                    "Partially Automatable": "🟡 Feasibility: Partially Automatable", 
                    "Not Automatable": "🔴 Feasibility: Not Automatable"
                }
                
                ui_display = feasibility_mapping.get(api_feasibility, f"⚪ Feasibility: {api_feasibility}")
                print(f"   UI Should Show: {ui_display}")
                
            else:
                print(f"❌ MISMATCH:")
                print(f"   LLM Analysis: {llm_feasibility}")
                print(f"   API Returns: {api_feasibility}")
                
        else:
            print(f"❌ API Error: {rec_response.status_code}")
            print(rec_response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    test_partial_session()