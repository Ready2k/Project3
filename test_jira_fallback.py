#!/usr/bin/env python3
"""
Test the Jira fallback mechanism for handling empty field responses.
"""

import asyncio
import json
from unittest.mock import AsyncMock, MagicMock
from app.services.jira import JiraService
from app.config import JiraConfig, JiraAuthType


def create_mock_response(status_code, json_data):
    """Create a mock HTTP response."""
    mock_response = MagicMock()
    mock_response.status_code = status_code
    mock_response.json.return_value = json_data
    return mock_response


async def test_fallback_mechanism():
    """Test that the fallback mechanism works when initial request returns empty fields."""
    print("🧪 Testing Jira fallback mechanism...")
    
    # Create Jira service
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test_token"
    )
    jira_service = JiraService(config)
    
    # Mock the authentication
    jira_service.auth_manager.is_authenticated = MagicMock(return_value=True)
    jira_service.auth_manager.get_auth_headers = AsyncMock(return_value={"Authorization": "Bearer test"})
    jira_service.api_version = "3"
    
    # Test Case 1: Empty fields response triggers fallback
    print("\n📋 Test Case 1: Empty fields response")
    
    # Mock responses
    empty_response = create_mock_response(200, {
        "key": "TEST-1",
        "fields": {}  # Empty fields
    })
    
    good_response = create_mock_response(200, {
        "key": "TEST-1", 
        "fields": {
            "summary": "Test ticket with good data",
            "description": "This has actual content",
            "status": {"name": "In Progress"},
            "priority": {"name": "High"},
            "issuetype": {"name": "Story"}
        }
    })
    
    # Mock the HTTP client to return empty response first, then good response
    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=None)
    
    # First call returns empty fields, second call (fallback) returns good data
    mock_client.get = AsyncMock(side_effect=[empty_response, good_response])
    
    # Mock the retry handler to use our mock client
    jira_service.retry_handler.create_http_client_with_retry = MagicMock(return_value=mock_client)
    
    try:
        # This should trigger the fallback mechanism
        ticket = await jira_service.fetch_ticket("TEST-1")
        
        print(f"   ✅ Fallback successful:")
        print(f"      Key: {ticket.key}")
        print(f"      Summary: {ticket.summary}")
        print(f"      Status: {ticket.status}")
        print(f"      Priority: {ticket.priority}")
        print(f"      Issue Type: {ticket.issue_type}")
        
        # Verify we got the good data, not the empty data
        assert ticket.summary == "Test ticket with good data"
        assert ticket.status == "In Progress"
        assert ticket.priority == "High"
        assert ticket.issue_type == "Story"
        
        print(f"   ✅ Fallback mechanism working correctly!")
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    # Test Case 2: Good response on first try (no fallback needed)
    print("\n📋 Test Case 2: Good response on first try")
    
    good_first_response = create_mock_response(200, {
        "key": "TEST-2",
        "fields": {
            "summary": "Good ticket from start",
            "status": {"name": "Done"},
            "priority": {"name": "Medium"}
        }
    })
    
    # Reset mock to return good response immediately
    mock_client.get = AsyncMock(return_value=good_first_response)
    
    try:
        ticket = await jira_service.fetch_ticket("TEST-2")
        
        print(f"   ✅ Direct response successful:")
        print(f"      Key: {ticket.key}")
        print(f"      Summary: {ticket.summary}")
        print(f"      Status: {ticket.status}")
        
        # Verify we got the data
        assert ticket.summary == "Good ticket from start"
        assert ticket.status == "Done"
        
        print(f"   ✅ Direct response working correctly!")
        
    except Exception as e:
        print(f"   ❌ Test failed: {e}")
        return False
    
    return True


def main():
    """Run the fallback mechanism tests."""
    print("🚀 Jira Fallback Mechanism Tests")
    print("=" * 50)
    
    success = asyncio.run(test_fallback_mechanism())
    
    print("\n" + "=" * 50)
    if success:
        print("🎉 All fallback tests passed!")
        print("The fallback mechanism should handle empty field responses.")
    else:
        print("❌ Some tests failed")


if __name__ == "__main__":
    main()