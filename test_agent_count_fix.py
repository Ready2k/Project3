#!/usr/bin/env python3
"""Test script to verify the agent count fix is working."""

import asyncio
import sys
import os

# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.ui.api_client import AAA_APIClient


async def test_agent_count_fix():
    """Test that the agent count fix is working."""
    
    session_id = "4fec72a7-a02b-48b9-ad8c-30976a199080"
    
    print(f"🔍 Testing agent count fix for session: {session_id}")
    print("=" * 60)
    
    # Create API client
    api_client = AAA_APIClient(base_url="http://localhost:8000")
    
    try:
        # Get recommendations
        print("📡 Calling /recommend endpoint...")
        result = await api_client.get_recommendations(session_id, top_k=3)
        
        if result and not result.get("error"):
            print("✅ Successfully retrieved recommendations")
            
            # Check if we have recommendations
            recommendations = result.get("recommendations", [])
            if recommendations:
                print(f"📊 Found {len(recommendations)} recommendation(s)")
                
                # Check the first recommendation for agent_roles
                first_rec = recommendations[0]
                agent_roles = first_rec.get("agent_roles", [])
                
                print(f"🤖 Agent roles in first recommendation: {len(agent_roles)}")
                
                if agent_roles:
                    print("✅ SUCCESS: Agent roles are present!")
                    print("\n🤖 Agent roles found:")
                    for i, role in enumerate(agent_roles, 1):
                        name = role.get("name", "Unknown Agent")
                        responsibility = role.get("responsibility", "No responsibility defined")
                        autonomy = role.get("autonomy_level", 0)
                        print(f"  {i}. {name}")
                        print(f"     Responsibility: {responsibility}")
                        print(f"     Autonomy Level: {autonomy}")
                        print()
                    
                    return True
                else:
                    print("❌ FAILURE: Agent roles are empty!")
                    return False
            else:
                print("❌ No recommendations found")
                return False
        else:
            error_msg = result.get("error", "Unknown error") if result else "No response"
            print(f"❌ API Error: {error_msg}")
            return False
            
    except Exception as e:
        print(f"❌ Exception occurred: {e}")
        return False


if __name__ == "__main__":
    print("🚀 Starting agent count fix test...")
    success = asyncio.run(test_agent_count_fix())
    
    if success:
        print("\n🎉 Test PASSED: Agent count fix is working!")
        sys.exit(0)
    else:
        print("\n💥 Test FAILED: Agent count fix is not working!")
        sys.exit(1)