#!/usr/bin/env python3
"""Test script to verify Q&A submission is working."""

import subprocess
import json
import sys


def test_qa_submission():
    """Test Q&A submission with a sample session."""
    
    print("🔍 Testing Q&A submission...")
    print("=" * 60)
    
    # First, let's create a new session to test with
    print("📡 Creating a new session...")
    
    create_session_cmd = [
        "curl", "-s", "-X", "POST", 
        "http://localhost:8000/ingest",
        "-H", "Content-Type: application/json",
        "-d", json.dumps({
            "source": "text",
            "payload": {
                "description": "Test automation requirement for Q&A testing",
                "domain": "it"
            },
            "provider_config": {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "test-key"
            }
        })
    ]
    
    result = subprocess.run(create_session_cmd, capture_output=True, text=True)
    
    if result.returncode != 0:
        print(f"❌ Failed to create session: {result.stderr}")
        return False
    
    try:
        session_response = json.loads(result.stdout)
        session_id = session_response.get("session_id")
        
        if not session_id:
            print(f"❌ No session ID in response: {session_response}")
            return False
        
        print(f"✅ Created session: {session_id}")
        
        # Now test Q&A submission
        print("📡 Submitting Q&A answers...")
        
        qa_cmd = [
            "curl", "-s", "-X", "POST", 
            f"http://localhost:8000/qa/{session_id}",
            "-H", "Content-Type: application/json",
            "-d", json.dumps({
                "answers": {
                    "test_question": "test_answer"
                }
            })
        ]
        
        qa_result = subprocess.run(qa_cmd, capture_output=True, text=True)
        
        if qa_result.returncode != 0:
            print(f"❌ Q&A submission failed: {qa_result.stderr}")
            return False
        
        try:
            qa_response = json.loads(qa_result.stdout)
            print(f"✅ Q&A response: {qa_response}")
            
            # Check if response has expected structure
            if "complete" in qa_response:
                print(f"✅ Response has 'complete' field: {qa_response['complete']}")
                return True
            else:
                print(f"❌ Response missing 'complete' field. Keys: {list(qa_response.keys())}")
                return False
                
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse Q&A response: {e}")
            print(f"Raw response: {qa_result.stdout}")
            return False
            
    except json.JSONDecodeError as e:
        print(f"❌ Failed to parse session response: {e}")
        print(f"Raw response: {result.stdout}")
        return False


if __name__ == "__main__":
    print("🚀 Starting Q&A submission test...")
    success = test_qa_submission()
    
    if success:
        print("\n🎉 Test PASSED: Q&A submission is working!")
        sys.exit(0)
    else:
        print("\n💥 Test FAILED: Q&A submission has issues!")
        sys.exit(1)