#!/usr/bin/env python3
"""
Helper script to automatically fix the acceptance criteria field detection.

This script will:
1. Analyze a ticket to find the acceptance criteria field
2. Automatically update the Jira service code with the correct field name
3. Test the fix to ensure it works

Usage:
    python fix_acceptance_criteria_field.py TICKET-123
"""

import asyncio
import re
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent / "app"))

from app.config import Settings
from app.services.jira import JiraService


async def find_and_fix_acceptance_criteria_field(ticket_key: str):
    """Find the correct acceptance criteria field and update the code."""
    
    print(f"🔧 Auto-fixing Acceptance Criteria field for ticket: {ticket_key}")
    print("=" * 60)
    
    # Load configuration and create service
    try:
        settings = Settings()
        jira_config = settings.jira
        jira_service = JiraService(jira_config)
        
        # Test connection
        success, error = await jira_service.test_connection()
        if not success:
            print(f"❌ Connection failed: {error}")
            return False
            
        print("✅ Connected to Jira successfully")
        
    except Exception as e:
        print(f"❌ Setup error: {e}")
        return False
    
    # Fetch ticket and analyze fields
    try:
        # Get raw ticket data
        auth_headers = await jira_service.auth_manager.get_auth_headers()
        api_version = jira_service.api_version or "3"
        url = f"{jira_service.base_url}/rest/api/{api_version}/issue/{ticket_key}"
        
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
            
        print(f"📊 Analyzing {len(fields)} fields...")
        
        # Find acceptance criteria candidates
        custom_fields = {k: v for k, v in fields.items() if k.startswith("customfield_")}
        acceptance_candidates = []
        
        acceptance_keywords = [
            "acceptance", "criteria", "given", "when", "then", 
            "should", "must", "verify", "validate", "test",
            "requirement", "condition", "specification", "scenario"
        ]
        
        for field_name, field_value in custom_fields.items():
            if not field_value:
                continue
                
            # Extract text content
            content = ""
            if isinstance(field_value, dict):
                content = str(field_value)
            elif isinstance(field_value, str):
                content = field_value
            else:
                content = str(field_value)
            
            if content and len(content) > 20:  # Must have substantial content
                content_lower = content.lower()
                keyword_matches = [kw for kw in acceptance_keywords if kw in content_lower]
                
                if keyword_matches:
                    acceptance_candidates.append({
                        "field": field_name,
                        "content": content,
                        "keywords": keyword_matches,
                        "score": len(keyword_matches) * 10 + len(content) / 100
                    })
        
        if not acceptance_candidates:
            print("❌ No acceptance criteria candidates found in this ticket")
            print("💡 Try with a ticket that has acceptance criteria filled in")
            return False
        
        # Sort by score and pick the best candidate
        acceptance_candidates.sort(key=lambda x: x["score"], reverse=True)
        best_candidate = acceptance_candidates[0]
        
        print(f"🎯 Best candidate found: {best_candidate['field']}")
        print(f"   Keywords: {', '.join(best_candidate['keywords'])}")
        print(f"   Content length: {len(best_candidate['content'])} characters")
        print(f"   Preview: {best_candidate['content'][:150]}...")
        
        # Update the Jira service code
        jira_service_path = Path("app/services/jira.py")
        if not jira_service_path.exists():
            print(f"❌ Could not find {jira_service_path}")
            return False
        
        print(f"\n🔧 Updating {jira_service_path}...")
        
        # Read the current file
        with open(jira_service_path, 'r') as f:
            content = f.read()
        
        # Find the ac_field_names list and add our field
        field_to_add = best_candidate['field']
        
        # Pattern to match the ac_field_names list
        pattern = r'(ac_field_names = \[\s*)(.*?)(\s*\])'
        
        def add_field_to_list(match):
            start = match.group(1)
            existing_fields = match.group(2)
            end = match.group(3)
            
            # Check if field is already there
            if field_to_add in existing_fields:
                print(f"✅ Field {field_to_add} already in the list")
                return match.group(0)  # Return unchanged
            
            # Add the field at the beginning (highest priority)
            new_field_line = f'            "{field_to_add}",  # Auto-detected acceptance criteria field\n'
            return start + new_field_line + existing_fields + end
        
        # Apply the update
        updated_content = re.sub(pattern, add_field_to_list, content, flags=re.DOTALL)
        
        if updated_content == content:
            print("❌ Could not find the ac_field_names list to update")
            return False
        
        # Write the updated file
        with open(jira_service_path, 'w') as f:
            f.write(updated_content)
        
        print(f"✅ Updated {jira_service_path} with field: {field_to_add}")
        
        # Test the fix
        print(f"\n🧪 Testing the fix...")
        
        # Reload the module (this is a bit tricky in Python)
        import importlib
        import app.services.jira
        importlib.reload(app.services.jira)
        
        # Create a new service instance
        from app.services.jira import JiraService
        new_jira_service = JiraService(jira_config)
        
        # Fetch the ticket again
        ticket = await new_jira_service.get_ticket(ticket_key)
        
        if ticket.acceptance_criteria:
            print(f"✅ SUCCESS! Acceptance criteria now detected:")
            print(f"   Length: {len(ticket.acceptance_criteria)} characters")
            print(f"   Preview: {ticket.acceptance_criteria[:200]}...")
            return True
        else:
            print(f"❌ Fix didn't work - acceptance criteria still not detected")
            return False
            
    except Exception as e:
        print(f"❌ Error during analysis: {e}")
        return False


def main():
    """Main function."""
    if len(sys.argv) != 2:
        print("Usage: python fix_acceptance_criteria_field.py TICKET-123")
        print("Example: python fix_acceptance_criteria_field.py PROJ-456")
        print("\nThis script will:")
        print("1. Analyze the ticket to find acceptance criteria")
        print("2. Automatically update the Jira service code")
        print("3. Test the fix")
        sys.exit(1)
    
    ticket_key = sys.argv[1]
    success = asyncio.run(find_and_fix_acceptance_criteria_field(ticket_key))
    
    if success:
        print(f"\n🎉 All done! Your acceptance criteria should now be pulled from Jira.")
        print(f"💡 Test it by running the AAA system with ticket {ticket_key}")
    else:
        print(f"\n❌ Auto-fix failed. Try the debug script first:")
        print(f"   python debug_acceptance_criteria.py {ticket_key}")


if __name__ == "__main__":
    main()