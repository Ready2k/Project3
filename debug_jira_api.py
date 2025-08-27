#!/usr/bin/env python3
"""
Debug script to test Jira API field extraction.
"""

import asyncio
import json
from app.services.jira import JiraService
from app.config import JiraConfig, JiraAuthType


async def debug_jira_fetch():
    """Debug Jira ticket fetching to see what fields are returned."""
    print("🔍 Debug: Testing Jira API field extraction...")
    
    # You'll need to configure these with your actual Jira details
    config = JiraConfig(
        base_url="https://your-domain.atlassian.net",  # Replace with your Jira URL
        email="your-email@example.com",  # Replace with your email
        api_token="your-api-token",  # Replace with your API token
        auth_type=JiraAuthType.API_TOKEN
    )
    
    jira_service = JiraService(config)
    
    try:
        # Test connection first
        print("🔗 Testing connection...")
        success, error = await jira_service.test_connection()
        if not success:
            print(f"❌ Connection failed: {error}")
            return
        
        print("✅ Connection successful!")
        
        # Try to fetch a ticket (replace with an actual ticket key)
        ticket_key = "AR-1"  # Replace with your actual ticket key
        print(f"📋 Fetching ticket: {ticket_key}")
        
        ticket = await jira_service.fetch_ticket(ticket_key)
        
        print(f"✅ Successfully fetched ticket: {ticket.key}")
        print(f"   Summary: {ticket.summary}")
        print(f"   Description: {ticket.description[:100]}..." if ticket.description else "   Description: None")
        print(f"   Status: {ticket.status}")
        print(f"   Priority: {ticket.priority}")
        print(f"   Issue Type: {ticket.issue_type}")
        print(f"   Assignee: {ticket.assignee}")
        print(f"   Reporter: {ticket.reporter}")
        print(f"   Components: {ticket.components}")
        print(f"   Labels: {ticket.labels}")
        print(f"   Acceptance Criteria: {'Present' if ticket.acceptance_criteria else 'None'}")
        print(f"   Comments: {len(ticket.comments)} comments")
        print(f"   Attachments: {len(ticket.attachments)} attachments")
        print(f"   Custom Fields: {len(ticket.custom_fields)} fields")
        
        # Test requirements mapping
        print(f"\n🔄 Testing requirements mapping...")
        requirements = jira_service.map_ticket_to_requirements(ticket)
        print(f"   Requirements description length: {len(requirements['description'])} characters")
        print(f"   Metadata fields: {len(requirements['metadata'])} fields")
        
        # Show first 300 characters of requirements
        print(f"\n📄 Requirements preview:")
        print("-" * 50)
        print(requirements['description'][:300] + "..." if len(requirements['description']) > 300 else requirements['description'])
        
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


def main():
    """Run the debug test."""
    print("🚀 Jira API Debug Test")
    print("=" * 50)
    print("⚠️  Please update the config in this script with your actual Jira details")
    print("   - base_url: Your Jira instance URL")
    print("   - email: Your Jira email")
    print("   - api_token: Your Jira API token")
    print("   - ticket_key: An actual ticket key to test with")
    print("=" * 50)
    
    asyncio.run(debug_jira_fetch())


if __name__ == "__main__":
    main()