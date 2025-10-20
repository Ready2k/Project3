#!/usr/bin/env python3
"""Simple test script to verify the agent count fix using curl."""

import subprocess
import json
import sys


def test_agent_count_fix():
    """Test that the agent count fix is working using curl."""
    
    session_id = "4fec72a7-a02b-48b9-ad8c-30976a199080"
    
    print(f"🔍 Testing agent count fix for session: {session_id}")
    print("=" * 60)
    
    try:
        # Call the recommend endpoint using curl
        print("📡 Calling /recommend endpoint...")
        
        curl_cmd = [
            "curl", "-s", "-X", "POST", 
            "http://localhost:8000/recommend",
            "-H", "Content-Type: application/json",
            "-d", f'{{"session_id": "{session_id}", "top_k": 3}}'
        ]
        
        result = subprocess.run(curl_cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            print(f"❌ Curl command failed: {result.stderr}")
            return False
        
        # Parse JSON response
        try:
            response = json.loads(result.stdout)
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse JSON response: {e}")
            print(f"Raw response: {result.stdout}")
            return False
        
        # Check for errors
        if "error" in response:
            print(f"❌ API Error: {response['error']}")
            return False
        
        # Check recommendations
        recommendations = response.get("recommendations", [])
        if not recommendations:
            print("❌ No recommendations found")
            return False
        
        print(f"📊 Found {len(recommendations)} recommendation(s)")
        
        # Check agent roles in first recommendation
        first_rec = recommendations[0]
        agent_roles = first_rec.get("agent_roles", [])
        
        print(f"🤖 Agent roles in first recommendation: {len(agent_roles)}")
        
        if agent_roles:
            print("✅ SUCCESS: Agent roles are present!")
            print(f"\n🤖 Found {len(agent_roles)} agent roles:")
            for i, role in enumerate(agent_roles, 1):
                name = role.get("name", "Unknown Agent")
                responsibility = role.get("responsibility", "No responsibility defined")
                autonomy = role.get("autonomy_level", 0)
                print(f"  {i}. {name}")
                print(f"     Responsibility: {responsibility[:100]}...")
                print(f"     Autonomy Level: {autonomy}")
                print()
            
            return True
        else:
            print("❌ FAILURE: Agent roles are empty!")
            print(f"First recommendation keys: {list(first_rec.keys())}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting agent count fix test...")
    success = test_agent_count_fix()
    
    if success:
        print("\n🎉 Test PASSED: Agent count fix is working!")
        sys.exit(0)
    else:
        print("\n💥 Test FAILED: Agent count fix is not working!")
        sys.exit(1)