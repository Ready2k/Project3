#!/usr/bin/env python3
"""Debug script to investigate the feasibility bug for session 3c4bb8f9-b6ad-4e4b-8868-a28581b6786d"""

import asyncio
import json
import httpx


async def debug_session_feasibility():
    """Debug the feasibility issue for the specific session."""
    
    session_id = "3c4bb8f9-b6ad-4e4b-8868-a28581b6786d"
    
    print(f"🔍 Debugging feasibility bug for session: {session_id}")
    print("=" * 60)
    
    try:
        # Test the API endpoint directly
        print(f"🔗 Testing API /recommend endpoint:")
        
        async with httpx.AsyncClient() as client:
            try:
                response = await client.post(
                    "http://localhost:8000/recommend",
                    json={"session_id": session_id, "top_k": 3},
                    timeout=30.0
                )
                
                if response.status_code == 200:
                    data = response.json()
                    print(f"   ✅ API Response Status: {response.status_code}")
                    print(f"   Feasibility: {data.get('feasibility', 'NOT_FOUND')}")
                    print(f"   Recommendations Count: {len(data.get('recommendations', []))}")
                    print(f"   Tech Stack Count: {len(data.get('tech_stack', []))}")
                    
                    # Show the full response structure
                    print(f"\n📄 Full API Response Structure:")
                    response_str = json.dumps(data, indent=2)
                    if len(response_str) > 2000:
                        print(response_str[:2000] + "\n... (truncated)")
                    else:
                        print(response_str)
                    
                    # Check if feasibility is properly set
                    feasibility = data.get('feasibility')
                    if feasibility and feasibility != 'Unknown':
                        print(f"\n✅ API is returning correct feasibility: {feasibility}")
                        print(f"   This suggests the bug is in the UI session state management.")
                    else:
                        print(f"\n❌ API is returning Unknown feasibility")
                        print(f"   This suggests the bug is in the API logic.")
                    
                else:
                    print(f"   ❌ API Response Status: {response.status_code}")
                    print(f"   Error: {response.text}")
                    
            except Exception as e:
                print(f"   ❌ API Request Failed: {e}")
                print(f"   Make sure the API server is running on localhost:8000")
                
        print(f"\n💡 Next Steps:")
        print(f"   1. If API returns correct feasibility, check UI session state caching")
        print(f"   2. If API returns Unknown, check LLM analysis storage in session")
        print(f"   3. Check if UI refresh button clears the cached recommendations")
        
    except Exception as e:
        print(f"❌ Error during debugging: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    print("🚀 Starting feasibility bug investigation...")
    asyncio.run(debug_session_feasibility())
    print("\n🎉 Investigation complete!")