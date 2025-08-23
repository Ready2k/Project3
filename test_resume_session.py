#!/usr/bin/env python3
"""Test script for resume session functionality."""

import asyncio
import httpx
import re

API_BASE_URL = "http://localhost:8000"

async def test_resume_session():
    """Test the resume session functionality."""
    print("🧪 Testing Resume Session Functionality")
    print("=" * 50)
    
    # Test session ID validation
    print("\n1. Testing Session ID Validation:")
    
    valid_session_ids = [
        "7249c0d9-7896-4fdf-931b-4f4aafbc44e0",
        "12345678-1234-1234-1234-123456789abc",
        "abcdef12-3456-7890-abcd-ef1234567890"
    ]
    
    invalid_session_ids = [
        "invalid-session-id",
        "7249c0d9-7896-4fdf-931b",  # too short
        "7249c0d9-7896-4fdf-931b-4f4aafbc44e0-extra",  # too long
        "7249c0d9_7896_4fdf_931b_4f4aafbc44e0",  # wrong separator
        ""
    ]
    
    session_id_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
    
    print("Valid Session IDs:")
    for session_id in valid_session_ids:
        is_valid = bool(re.match(session_id_pattern, session_id.lower()))
        print(f"  {session_id}: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    print("\nInvalid Session IDs:")
    for session_id in invalid_session_ids:
        is_valid = bool(re.match(session_id_pattern, session_id.lower()))
        print(f"  {session_id}: {'✅ Valid' if is_valid else '❌ Invalid'}")
    
    # Test API endpoint with a known session (if exists)
    print("\n2. Testing API Status Endpoint:")
    
    test_session_id = "7249c0d9-7896-4fdf-931b-4f4aafbc44e0"
    
    try:
        async with httpx.AsyncClient(timeout=10.0) as client:
            response = await client.get(f"{API_BASE_URL}/status/{test_session_id}")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ Session {test_session_id[:8]}... found!")
                print(f"   Phase: {data.get('phase', 'Unknown')}")
                print(f"   Progress: {data.get('progress', 0)}%")
                print(f"   Requirements: {'Yes' if data.get('requirements') else 'No'}")
            elif response.status_code == 404:
                print(f"❌ Session {test_session_id[:8]}... not found (404)")
                print("   This is expected if the session doesn't exist")
            else:
                print(f"❌ Unexpected response: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error testing API: {str(e)}")
        print("   Make sure the API server is running on localhost:8000")
    
    # Test creating a new session to get a valid session ID
    print("\n3. Testing Session Creation (for testing resume):")
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Create a test session
            ingest_payload = {
                "source": "text",
                "payload": {
                    "text": "Test requirement for resume functionality testing",
                    "domain": "testing",
                    "pattern_types": ["workflow"]
                }
            }
            
            response = await client.post(f"{API_BASE_URL}/ingest", json=ingest_payload)
            
            if response.status_code == 200:
                data = response.json()
                new_session_id = data.get('session_id')
                print(f"✅ Created test session: {new_session_id}")
                print(f"   You can use this session ID to test the resume functionality!")
                
                # Wait a moment and check status
                await asyncio.sleep(2)
                
                status_response = await client.get(f"{API_BASE_URL}/status/{new_session_id}")
                if status_response.status_code == 200:
                    status_data = status_response.json()
                    print(f"   Current status: {status_data.get('phase')} ({status_data.get('progress')}%)")
                
            else:
                print(f"❌ Failed to create test session: {response.status_code}")
                print(f"   Response: {response.text}")
                
    except Exception as e:
        print(f"❌ Error creating test session: {str(e)}")
    
    print("\n" + "=" * 50)
    print("🎉 Resume Session Test Complete!")
    print("\nTo test in the UI:")
    print("1. Go to the Analysis tab")
    print("2. Select 'Resume Previous Session'")
    print("3. Enter a valid session ID")
    print("4. Click 'Resume Session'")

if __name__ == "__main__":
    asyncio.run(test_resume_session())