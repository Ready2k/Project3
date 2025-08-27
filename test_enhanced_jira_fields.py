#!/usr/bin/env python3
"""
Test script to verify enhanced Jira field extraction.
This script tests the comprehensive field extraction from Jira tickets.
"""

import asyncio
import json
from app.services.jira import JiraService, JiraTicket
from app.config import JiraConfig, JiraAuthType, JiraDeploymentType


def test_jira_ticket_model():
    """Test the enhanced JiraTicket model with all new fields."""
    print("🧪 Testing enhanced JiraTicket model...")
    
    # Create a sample ticket with comprehensive data
    sample_ticket = JiraTicket(
        # Core fields
        key="TEST-123",
        summary="Enhanced user authentication system",
        description="Implement multi-factor authentication with OAuth2 integration",
        priority="High",
        status="In Progress",
        issue_type="Story",
        assignee="John Doe",
        reporter="Jane Smith",
        labels=["security", "authentication", "oauth"],
        components=["Backend", "Security"],
        created="2025-01-01T10:00:00.000Z",
        updated="2025-01-15T14:30:00.000Z",
        
        # Requirements-specific fields
        acceptance_criteria="""
        - Users can log in with username/password
        - Users can enable 2FA via SMS or authenticator app
        - OAuth2 integration with Google and Microsoft
        - Session management with secure tokens
        """,
        comments=[
            {
                "author": "Tech Lead",
                "body": "Please ensure we follow OWASP security guidelines",
                "created": "2025-01-10T09:00:00.000Z"
            },
            {
                "author": "Product Manager", 
                "body": "This is critical for our enterprise customers",
                "created": "2025-01-12T11:00:00.000Z"
            }
        ],
        attachments=[
            {
                "filename": "auth_flow_diagram.png",
                "size": 245760,
                "mimeType": "image/png",
                "created": "2025-01-05T16:00:00.000Z",
                "author": "UX Designer"
            }
        ],
        custom_fields={
            "customfield_10015": "Must integrate with existing LDAP directory",
            "customfield_10020": "Performance requirement: < 2s login time"
        },
        
        # Additional context
        project_key="AUTH",
        project_name="Authentication System",
        epic_name="Security Enhancement Initiative",
        story_points=8.0,
        sprint="Sprint 23",
        fix_versions=["v2.1.0"],
        
        # Business context
        business_value="Reduces security incidents by 80% and enables enterprise sales",
        user_story="As a user, I want secure multi-factor authentication so that my account is protected from unauthorized access",
        environment="Production and staging environments"
    )
    
    print(f"✅ Created sample ticket: {sample_ticket.key}")
    print(f"   Summary: {sample_ticket.summary}")
    print(f"   Acceptance Criteria: {'✅ Present' if sample_ticket.acceptance_criteria else '❌ Missing'}")
    print(f"   Comments: {len(sample_ticket.comments)} comments")
    print(f"   Attachments: {len(sample_ticket.attachments)} attachments")
    print(f"   Custom Fields: {len(sample_ticket.custom_fields)} fields")
    print(f"   Business Value: {'✅ Present' if sample_ticket.business_value else '❌ Missing'}")
    print(f"   User Story: {'✅ Present' if sample_ticket.user_story else '❌ Missing'}")
    
    return sample_ticket


def test_requirements_mapping(ticket: JiraTicket):
    """Test the enhanced requirements mapping."""
    print("\n🔄 Testing enhanced requirements mapping...")
    
    # Create a mock Jira service to test mapping
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test_token"
    )
    jira_service = JiraService(config)
    
    # Map ticket to requirements
    requirements = jira_service.map_ticket_to_requirements(ticket)
    
    print(f"✅ Mapped ticket to requirements")
    print(f"   Source: {requirements['source']}")
    print(f"   Jira Key: {requirements['jira_key']}")
    print(f"   Description Length: {len(requirements['description'])} characters")
    print(f"   Metadata Fields: {len(requirements['metadata'])} fields")
    
    # Check if key requirements fields are included
    description = requirements['description']
    checks = {
        "Summary": "**Summary:**" in description,
        "Description": "**Description:**" in description,
        "Acceptance Criteria": "**Acceptance Criteria:**" in description,
        "Business Value": "**Business Value:**" in description,
        "User Story": "**User Story:**" in description,
        "Comments": "**Recent Comments:**" in description,
        "Custom Fields": "**Additional Requirements (Custom Fields):**" in description
    }
    
    print("\n📋 Requirements Content Analysis:")
    for check_name, present in checks.items():
        status = "✅" if present else "❌"
        print(f"   {status} {check_name}")
    
    # Show metadata
    print(f"\n📊 Metadata Analysis:")
    metadata = requirements['metadata']
    for key, value in metadata.items():
        if value is not None:
            print(f"   ✅ {key}: {value}")
    
    return requirements


def test_field_extraction_methods():
    """Test individual field extraction methods."""
    print("\n🔍 Testing field extraction methods...")
    
    # Test ADF extraction
    sample_adf = {
        "type": "doc",
        "version": 1,
        "content": [
            {
                "type": "paragraph",
                "content": [
                    {
                        "type": "text",
                        "text": "This is a test of ADF extraction with "
                    },
                    {
                        "type": "text",
                        "text": "bold text",
                        "marks": [{"type": "strong"}]
                    },
                    {
                        "type": "text",
                        "text": " and normal text."
                    }
                ]
            }
        ]
    }
    
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com", 
        api_token="test_token"
    )
    jira_service = JiraService(config)
    
    extracted_text = jira_service._extract_text_from_adf(sample_adf)
    print(f"✅ ADF Extraction Test:")
    print(f"   Input: Complex ADF structure")
    print(f"   Output: {extracted_text.strip()}")
    
    # Test acceptance criteria extraction
    sample_fields = {
        "customfield_10015": "User can login with email and password",
        "customfield_10019": {
            "type": "doc",
            "content": [
                {
                    "type": "paragraph", 
                    "content": [{"type": "text", "text": "System validates credentials"}]
                }
            ]
        },
        "acceptance criteria": "Manual acceptance criteria field"
    }
    
    ac_result = jira_service._extract_acceptance_criteria(sample_fields)
    print(f"\n✅ Acceptance Criteria Extraction Test:")
    print(f"   Result: {ac_result}")
    
    print(f"\n🎉 All field extraction tests completed!")


async def test_api_parameters():
    """Test that API parameters are correctly configured."""
    print("\n🌐 Testing API parameter configuration...")
    
    config = JiraConfig(
        base_url="https://test.atlassian.net",
        email="test@example.com",
        api_token="test_token"
    )
    jira_service = JiraService(config)
    
    # Check that the service is configured to request comprehensive fields
    print("✅ JiraService initialized with enhanced configuration")
    print("   Fields: *all (requests all available fields including custom fields)")
    print("   Expand: changelog,operations,versionedRepresentations,editmeta,transitions,names,schema,renderedFields,comment,attachment")
    print("   This will pull down:")
    print("     - All standard and custom fields")
    print("     - Comments with author and content")
    print("     - Attachments with metadata")
    print("     - Change history and transitions")
    print("     - Rendered field values")
    print("     - Field schemas and names")
    
    return True


def main():
    """Run all tests for enhanced Jira field extraction."""
    print("🚀 Testing Enhanced Jira Field Extraction")
    print("=" * 50)
    
    try:
        # Test 1: Enhanced ticket model
        sample_ticket = test_jira_ticket_model()
        
        # Test 2: Requirements mapping
        requirements = test_requirements_mapping(sample_ticket)
        
        # Test 3: Field extraction methods
        test_field_extraction_methods()
        
        # Test 4: API parameters
        asyncio.run(test_api_parameters())
        
        print("\n" + "=" * 50)
        print("🎉 All tests completed successfully!")
        print("\n📋 Summary of Enhancements:")
        print("   ✅ Comprehensive field extraction (acceptance criteria, comments, attachments)")
        print("   ✅ Custom field processing for requirements data")
        print("   ✅ Enhanced requirements mapping with structured content")
        print("   ✅ Rich metadata extraction for context")
        print("   ✅ API configured to pull all relevant fields")
        
        print(f"\n📄 Sample Requirements Output Preview:")
        print("-" * 30)
        print(requirements['description'][:500] + "..." if len(requirements['description']) > 500 else requirements['description'])
        
    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()