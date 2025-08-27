#!/usr/bin/env python3
"""
Quick test to reproduce the blank ticket issue.
"""

from app.services.jira import JiraService, JiraTicket
from app.config import JiraConfig, JiraAuthType


def test_blank_ticket_issue():
    """Test what happens when we get a response with missing fields."""
    print("🧪 Testing blank ticket issue...")
    
    # Simulate the kind of response that might be causing blank tickets
    problematic_responses = [
        # Case 1: Empty fields
        {"key": "AR-1", "fields": {}},
        
        # Case 2: Null values
        {"key": "AR-2", "fields": {"summary": None, "status": None, "priority": None}},
        
        # Case 3: Different field structure
        {"key": "AR-3", "fields": {"summary": "", "status": {}, "priority": {}}},
        
        # Case 4: Missing key fields
        {"key": "AR-4", "fields": {"description": "Some description", "labels": []}}
    ]
    
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test_token"
    )
    jira_service = JiraService(config)
    
    for i, response_data in enumerate(problematic_responses, 1):
        print(f"\n📋 Test Case {i}: {response_data['key']}")
        
        try:
            ticket = jira_service._parse_ticket_data(response_data)
            
            print(f"   ✅ Parsed successfully:")
            print(f"      Key: '{ticket.key}'")
            print(f"      Summary: '{ticket.summary}'")
            print(f"      Status: '{ticket.status}'")
            print(f"      Priority: '{ticket.priority}'")
            print(f"      Issue Type: '{ticket.issue_type}'")
            print(f"      Assignee: '{ticket.assignee}'")
            print(f"      Reporter: '{ticket.reporter}'")
            
            # Check if this would show as "blank" in the UI
            is_blank = (not ticket.summary or ticket.summary == f"Ticket {ticket.key}") and \
                      ticket.status == "Unknown" and \
                      ticket.priority is None and \
                      ticket.issue_type == "Unknown" and \
                      ticket.assignee is None and \
                      ticket.reporter is None
            
            if is_blank:
                print(f"      ⚠️  This would appear BLANK in the UI!")
            else:
                print(f"      ✅ This would show data in the UI")
                
        except Exception as e:
            print(f"   ❌ Parsing failed: {e}")


if __name__ == "__main__":
    test_blank_ticket_issue()