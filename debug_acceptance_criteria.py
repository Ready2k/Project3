#!/usr/bin/env python3
"""
Debug script to identify the correct field name for Acceptance Criteria in your Jira instance.

This script will:
1. Fetch a Jira ticket
2. Display all available fields
3. Help identify which field contains your Acceptance Criteria
4. Show the content of custom fields to help you identify the right one

Usage:
    python debug_acceptance_criteria.py TICKET-123
"""

import asyncio
import json
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.config import Settings
from app.services.jira import JiraService


async def debug_acceptance_criteria(ticket_key: str):
    """Debug acceptance criteria field detection for a specific ticket."""
    
    print(f"🔍 Debugging Acceptance Criteria field for ticket: {ticket_key}")
    print("=" * 60)
    
    # Load configuration
    try:
        settings = Settings()
        jira_config = settings.jira
        
        if not jira_config.base_url:
            print("❌ Jira configuration not found. Please check your config.yaml or .env file.")
            return
            
        print(f"📡 Connecting to Jira: {jira_config.base_url}")
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return
    
    # Create Jira service
    jira_service = JiraService(jira_config)
    
    # Test connection
    print("\n🔗 Testing Jira connection...")
    try:
        success, error = await jira_service.test_connection()
        if not success:
            print(f"❌ Connection failed: {error}")
            return
        print("✅ Connection successful!")
        
    except Exception as e:
        print(f"❌ Connection error: {e}")
        return
    
    # Fetch the ticket
    print(f"\n📋 Fetching ticket {ticket_key}...")
    try:
        ticket = await jira_service.get_ticket(ticket_key)
        print(f"✅ Ticket fetched: {ticket.summary}")
        
    except Exception as e:
        print(f"❌ Failed to fetch ticket: {e}")
        return
    
    # Display acceptance criteria status
    print(f"\n📝 Acceptance Criteria Status:")
    print(f"   Current value: {'✅ Found' if ticket.acceptance_criteria else '❌ Not found'}")
    if ticket.acceptance_criteria:
        print(f"   Length: {len(ticket.acceptance_criteria)} characters")
        print(f"   Preview: {ticket.acceptance_criteria[:100]}{'...' if len(ticket.acceptance_criteria) > 100 else ''}")
    
    # Now let's fetch the raw ticket data to see all fields
    print(f"\n🔍 Analyzing all available fields...")
    try:
        # Get raw ticket data
        auth_headers = await jira_service.auth_manager.get_auth_headers()
        
        # Build URL for ticket with all fields
        api_version = jira_service.api_version or "3"
        url = f"{jira_service.base_url}/rest/api/{api_version}/issue/{ticket_key}"
        
        # Get SSL and proxy config
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        proxy_config = jira_service.proxy_handler.get_httpx_proxy_config()
        
        import httpx
        async with httpx.AsyncClient(verify=verify_config, proxies=proxy_config, timeout=30.0) as client:
            headers = {"Accept": "application/json"}
            headers.update(auth_headers)
            
            response = await client.get(url, headers=headers)
            response.raise_for_status()
            
            raw_data = response.json()
            fields = raw_data.get("fields", {})
            
            print(f"📊 Total fields available: {len(fields)}")
            
            # Separate custom fields
            custom_fields = {k: v for k, v in fields.items() if k.startswith("customfield_")}
            standard_fields = {k: v for k, v in fields.items() if not k.startswith("customfield_")}
            
            print(f"   Standard fields: {len(standard_fields)}")
            print(f"   Custom fields: {len(custom_fields)}")
            
            # Display custom fields with content analysis
            print(f"\n📋 Custom Fields Analysis:")
            print("-" * 40)
            
            acceptance_candidates = []
            
            for field_name, field_value in custom_fields.items():
                if field_value is None:
                    continue
                    
                # Extract text content
                content = ""
                if isinstance(field_value, dict):
                    # Could be ADF (Atlassian Document Format) or other structured data
                    if "content" in field_value:
                        content = str(field_value)
                    else:
                        content = json.dumps(field_value)
                elif isinstance(field_value, str):
                    content = field_value
                else:
                    content = str(field_value)
                
                # Check if this could be acceptance criteria
                is_candidate = False
                if content and len(content) > 10:
                    content_lower = content.lower()
                    acceptance_keywords = [
                        "acceptance", "criteria", "given", "when", "then", 
                        "should", "must", "verify", "validate", "test",
                        "requirement", "condition", "specification"
                    ]
                    
                    keyword_matches = [kw for kw in acceptance_keywords if kw in content_lower]
                    if keyword_matches:
                        is_candidate = True
                        acceptance_candidates.append({
                            "field": field_name,
                            "content": content,
                            "keywords": keyword_matches,
                            "length": len(content)
                        })
                
                # Display field info
                status = "🎯 CANDIDATE" if is_candidate else "📄 Data"
                preview = content[:80].replace('\n', ' ').replace('\r', ' ')
                print(f"   {status} {field_name}: {len(content)} chars")
                if content:
                    print(f"      Preview: {preview}{'...' if len(content) > 80 else ''}")
                print()
            
            # Show the most likely candidates
            if acceptance_candidates:
                print(f"\n🎯 LIKELY ACCEPTANCE CRITERIA CANDIDATES:")
                print("=" * 50)
                
                # Sort by number of keywords and content length
                acceptance_candidates.sort(key=lambda x: (len(x["keywords"]), x["length"]), reverse=True)
                
                for i, candidate in enumerate(acceptance_candidates[:3], 1):
                    print(f"\n#{i} Field: {candidate['field']}")
                    print(f"   Keywords found: {', '.join(candidate['keywords'])}")
                    print(f"   Content length: {candidate['length']} characters")
                    print(f"   Content preview:")
                    print(f"   {candidate['content'][:200]}{'...' if len(candidate['content']) > 200 else ''}")
                    
                    if i == 1:
                        print(f"\n💡 RECOMMENDATION: Add '{candidate['field']}' to the acceptance criteria field list")
                        print(f"   You can update the _extract_acceptance_criteria function in app/services/jira.py")
                        print(f"   Add this line to the ac_field_names list:")
                        print(f"   \"{candidate['field']}\",  # Your instance's acceptance criteria field")
            else:
                print(f"\n❌ No obvious acceptance criteria candidates found")
                print(f"   This could mean:")
                print(f"   1. Acceptance criteria is stored in a standard field (description, summary)")
                print(f"   2. The field name doesn't contain obvious keywords")
                print(f"   3. This ticket doesn't have acceptance criteria filled in")
                
                # Show all custom fields with content for manual inspection
                print(f"\n📋 All custom fields with content (for manual inspection):")
                for field_name, field_value in custom_fields.items():
                    if field_value:
                        content = str(field_value)[:100]
                        print(f"   {field_name}: {content}{'...' if len(str(field_value)) > 100 else ''}")
            
    except Exception as e:
        print(f"❌ Error analyzing fields: {e}")
        return
    
    print(f"\n✅ Analysis complete!")
    print(f"💡 If you found your acceptance criteria field, update the code and test again.")


def main():
    """Main function to run the debug script."""
    if len(sys.argv) != 2:
        print("Usage: python debug_acceptance_criteria.py TICKET-123")
        print("Example: python debug_acceptance_criteria.py PROJ-456")
        sys.exit(1)
    
    ticket_key = sys.argv[1]
    asyncio.run(debug_acceptance_criteria(ticket_key))


if __name__ == "__main__":
    main()