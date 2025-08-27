#!/usr/bin/env python3
"""
Diagnostic script to identify Jira API issues.
"""

import asyncio
import json
import httpx
from app.config import JiraConfig, JiraAuthType


async def test_raw_api_call():
    """Test raw Jira API call to see what we get back."""
    print("🔍 Testing raw Jira API call...")
    
    # Configure with your actual Jira details
    base_url = "https://your-domain.atlassian.net"  # Replace
    email = "your-email@example.com"  # Replace  
    api_token = "your-api-token"  # Replace
    ticket_key = "AR-1"  # Replace with actual ticket
    
    # Create auth header
    import base64
    auth_string = f"{email}:{api_token}"
    auth_bytes = auth_string.encode('ascii')
    auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
    auth_header = f"Basic {auth_b64}"
    
    # Test different field combinations
    test_cases = [
        {"fields": "summary,description,status", "expand": ""},
        {"fields": "summary,description,priority,status,issuetype", "expand": ""},
        {"fields": "*all", "expand": ""},
        {"fields": "summary,description,priority,status,issuetype,assignee,reporter", "expand": "renderedFields"}
    ]
    
    async with httpx.AsyncClient(verify=False, timeout=30.0) as client:
        for i, params in enumerate(test_cases, 1):
            print(f"\n📋 Test Case {i}: {params}")
            
            try:
                url = f"{base_url}/rest/api/3/issue/{ticket_key}"
                headers = {
                    "Authorization": auth_header,
                    "Accept": "application/json"
                }
                
                response = await client.get(url, headers=headers, params=params)
                print(f"   Status: {response.status_code}")
                
                if response.status_code == 200:
                    data = response.json()
                    fields = data.get("fields", {})
                    print(f"   Fields returned: {len(fields)}")
                    print(f"   Field names: {list(fields.keys())[:10]}...")
                    print(f"   Summary: '{fields.get('summary', 'MISSING')}'")
                    print(f"   Status: {fields.get('status', 'MISSING')}")
                else:
                    print(f"   Error: {response.text[:200]}...")
                    
            except Exception as e:
                print(f"   Exception: {e}")


if __name__ == "__main__":
    print("🚀 Jira API Diagnostic Tool")
    print("⚠️  Update the credentials and ticket key in this script")
    asyncio.run(test_raw_api_call())