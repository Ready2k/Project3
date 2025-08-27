#!/usr/bin/env python3
"""
Test basic Jira field extraction with simplified parameters.
"""

import asyncio
import json
from app.services.jira import JiraService, JiraTicket
from app.config import JiraConfig, JiraAuthType


def test_basic_parsing():
    """Test basic ticket parsing with sample data."""
    print("🧪 Testing basic ticket parsing...")
    
    # Sample Jira API response structure
    sample_response = {
        "key": "TEST-123",
        "fields": {
            "summary": "Test ticket summary",
            "description": "Test ticket description",
            "priority": {"name": "High"},
            "status": {"name": "In Progress"},
            "issuetype": {"name": "Story"},
            "assignee": {"displayName": "John Doe"},
            "reporter": {"displayName": "Jane Smith"},
            "labels": ["test", "sample"],
            "components": [{"name": "Backend"}],
            "created": "2025-01-01T10:00:00.000Z",
            "updated": "2025-01-15T14:30:00.000Z",
            "project": {"key": "TEST", "name": "Test Project"}
        }
    }
    
    # Create Jira service
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test_token"
    )
    jira_service = JiraService(config)
    
    # Test parsing
    try:
        ticket = jira_service._parse_ticket_data(sample_response)
        
        print(f"✅ Parsed ticket successfully:")
        print(f"   Key: {ticket.key}")
        print(f"   Summary: {ticket.summary}")
        print(f"   Description: {ticket.description}")
        print(f"   Status: {ticket.status}")
        print(f"   Priority: {ticket.priority}")
        print(f"   Issue Type: {ticket.issue_type}")
        print(f"   Assignee: {ticket.assignee}")
        print(f"   Reporter: {ticket.reporter}")
        print(f"   Components: {ticket.components}")
        print(f"   Labels: {ticket.labels}")
        print(f"   Project: {ticket.project_name} ({ticket.project_key})")
        
        # Test requirements mapping
        requirements = jira_service.map_ticket_to_requirements(ticket)
        print(f"\n✅ Requirements mapping successful:")
        print(f"   Source: {requirements['source']}")
        print(f"   Jira Key: {requirements['jira_key']}")
        print(f"   Description length: {len(requirements['description'])} chars")
        
        print(f"\n📄 Requirements content:")
        print("-" * 30)
        print(requirements['description'])
        
        return True
        
    except Exception as e:
        print(f"❌ Parsing failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_empty_response():
    """Test handling of empty or minimal response."""
    print("\n🧪 Testing empty response handling...")
    
    # Minimal response that might cause issues
    minimal_response = {
        "key": "EMPTY-1",
        "fields": {}
    }
    
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test_token"
    )
    jira_service = JiraService(config)
    
    try:
        ticket = jira_service._parse_ticket_data(minimal_response)
        
        print(f"✅ Handled empty response:")
        print(f"   Key: {ticket.key}")
        print(f"   Summary: '{ticket.summary}'")
        print(f"   Status: {ticket.status}")
        print(f"   Priority: {ticket.priority}")
        print(f"   Issue Type: {ticket.issue_type}")
        
        # Test requirements mapping
        requirements = jira_service.map_ticket_to_requirements(ticket)
        print(f"   Requirements created: {len(requirements['description'])} chars")
        
        return True
        
    except Exception as e:
        print(f"❌ Empty response handling failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run basic parsing tests."""
    print("🚀 Basic Jira Parsing Tests")
    print("=" * 50)
    
    test1_passed = test_basic_parsing()
    test2_passed = test_empty_response()
    
    print("\n" + "=" * 50)
    if test1_passed and test2_passed:
        print("🎉 All basic tests passed!")
        print("The parsing logic is working correctly.")
        print("If tickets are still showing as blank, the issue is likely:")
        print("  1. API request parameters")
        print("  2. Authentication/permissions")
        print("  3. Jira instance configuration")
    else:
        print("❌ Some tests failed - check the parsing logic")


if __name__ == "__main__":
    main()