#!/usr/bin/env python3
"""
Debug script for the new session showing Unknown feasibility.
"""

import requests
import json

def debug_new_session():
    """Debug the new session with Unknown feasibility."""
    
    session_id = "a44e5735-f53d-4a6a-b96f-fb5a15b6a8ef"
    
    print(f"🔍 Debugging session {session_id}...")
    
    try:
        # Get session status first
        print(f"\n📊 Getting session status...")
        status_response = requests.get(f"http://localhost:8000/status/{session_id}")
        
        if status_response.status_code == 200:
            status_data = status_response.json()
            requirements = status_data.get("requirements", {})
            
            print(f"   Phase: {status_data.get('phase')}")
            print(f"   Progress: {status_data.get('progress')}%")
            
            # Check if LLM analysis exists
            llm_feasibility = requirements.get("llm_analysis_automation_feasibility")
            llm_confidence = requirements.get("llm_analysis_confidence_level")
            
            print(f"\n🤖 LLM Analysis in Session:")
            print(f"   Feasibility: {llm_feasibility}")
            print(f"   Confidence: {llm_confidence}")
            
            if not llm_feasibility:
                print("❌ No LLM analysis found - this explains the Unknown feasibility!")
                print("   The session may not have completed the Q&A phase properly.")
                
                # Check what fields are available
                print(f"\n📋 Available requirement fields:")
                for key in requirements.keys():
                    if key.startswith('llm_'):
                        print(f"   {key}: {requirements[key]}")
                
                return
            
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
            
            if api_feasibility == "Unknown":
                print("❌ API still returns Unknown - need to investigate further")
            else:
                print(f"✅ API returns: {api_feasibility}")
                
        else:
            print(f"❌ Error calling /recommend: {rec_response.status_code}")
            print(rec_response.text)
            
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    debug_new_session()