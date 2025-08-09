"""Jira integration service for fetching tickets and mapping to requirements."""

import base64
import json
from typing import Dict, Any, Optional
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from app.config import JiraConfig
from app.utils.logger import app_logger


class JiraTicket(BaseModel):
    """Jira ticket data model."""
    key: str
    summary: str
    description: Optional[str] = None
    priority: Optional[str] = None
    status: str
    issue_type: str
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    labels: list[str] = []
    components: list[str] = []
    created: Optional[str] = None
    updated: Optional[str] = None


class JiraError(Exception):
    """Base exception for Jira-related errors."""
    pass


class JiraConnectionError(JiraError):
    """Jira connection/authentication error."""
    pass


class JiraTicketNotFoundError(JiraError):
    """Jira ticket not found error."""
    pass


class JiraService:
    """Service for interacting with Jira API."""
    
    def __init__(self, config: JiraConfig):
        """Initialize Jira service with configuration.
        
        Args:
            config: Jira configuration containing base_url, email, and api_token
        """
        self.config = config
        self.base_url = config.base_url
        self.timeout = config.timeout
        
        # Create authentication header
        if config.email and config.api_token:
            auth_string = f"{config.email}:{config.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            self.auth_header = f"Basic {auth_b64}"
        else:
            self.auth_header = None
    
    def _validate_config(self) -> None:
        """Validate Jira configuration."""
        if not self.config.base_url:
            raise JiraConnectionError("Jira base URL is required")
        if not self.config.email:
            raise JiraConnectionError("Jira email is required")
        if not self.config.api_token:
            raise JiraConnectionError("Jira API token is required")
    
    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test Jira connection and authentication.
        
        Returns:
            Tuple of (success, error_message)
        """
        try:
            self._validate_config()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                url = urljoin(self.base_url, "/rest/api/3/myself")
                headers = {
                    "Authorization": self.auth_header,
                    "Accept": "application/json"
                }
                
                response = await client.get(url, headers=headers)
                
                if response.status_code == 200:
                    user_data = response.json()
                    app_logger.info(f"Jira connection successful for user: {user_data.get('displayName', 'Unknown')}")
                    return True, None
                elif response.status_code == 401:
                    return False, "Authentication failed. Check email and API token."
                elif response.status_code == 403:
                    return False, "Access forbidden. Check permissions."
                else:
                    return False, f"HTTP {response.status_code}: {response.text}"
                    
        except httpx.TimeoutException:
            return False, f"Connection timeout after {self.timeout} seconds"
        except httpx.ConnectError:
            return False, "Failed to connect to Jira. Check base URL."
        except JiraConnectionError as e:
            return False, str(e)
        except Exception as e:
            app_logger.error(f"Unexpected error testing Jira connection: {e}")
            return False, f"Unexpected error: {str(e)}"
    
    async def fetch_ticket(self, ticket_key: str) -> JiraTicket:
        """Fetch a Jira ticket by key.
        
        Args:
            ticket_key: Jira ticket key (e.g., "PROJ-123")
            
        Returns:
            JiraTicket object with ticket data
            
        Raises:
            JiraConnectionError: If connection/auth fails
            JiraTicketNotFoundError: If ticket doesn't exist
            JiraError: For other Jira API errors
        """
        try:
            self._validate_config()
            
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                # Construct API URL
                url = urljoin(self.base_url, f"/rest/api/3/issue/{ticket_key}")
                headers = {
                    "Authorization": self.auth_header,
                    "Accept": "application/json"
                }
                
                # Add fields parameter to get specific data
                params = {
                    "fields": "summary,description,priority,status,issuetype,assignee,reporter,labels,components,created,updated"
                }
                
                app_logger.info(f"Fetching Jira ticket: {ticket_key}")
                response = await client.get(url, headers=headers, params=params)
                
                if response.status_code == 200:
                    data = response.json()
                    return self._parse_ticket_data(data)
                elif response.status_code == 401:
                    raise JiraConnectionError("Authentication failed. Check email and API token.")
                elif response.status_code == 403:
                    raise JiraConnectionError("Access forbidden. Check permissions.")
                elif response.status_code == 404:
                    raise JiraTicketNotFoundError(f"Ticket '{ticket_key}' not found")
                else:
                    raise JiraError(f"HTTP {response.status_code}: {response.text}")
                    
        except httpx.TimeoutException:
            raise JiraConnectionError(f"Connection timeout after {self.timeout} seconds")
        except httpx.ConnectError:
            raise JiraConnectionError("Failed to connect to Jira. Check base URL.")
        except (JiraConnectionError, JiraTicketNotFoundError, JiraError):
            raise
        except Exception as e:
            app_logger.error(f"Unexpected error fetching Jira ticket {ticket_key}: {e}")
            raise JiraError(f"Unexpected error: {str(e)}")
    
    def _parse_ticket_data(self, data: Dict[str, Any]) -> JiraTicket:
        """Parse Jira API response data into JiraTicket object.
        
        Args:
            data: Raw Jira API response data
            
        Returns:
            JiraTicket object
        """
        fields = data.get("fields", {})
        
        # Extract basic fields
        key = data.get("key", "")
        summary = fields.get("summary", "")
        description = fields.get("description", {})
        
        # Handle description (can be complex Atlassian Document Format)
        description_text = ""
        if description:
            if isinstance(description, dict):
                # Try to extract plain text from ADF (Atlassian Document Format)
                description_text = self._extract_text_from_adf(description)
            elif isinstance(description, str):
                description_text = description
        
        # Extract priority
        priority_obj = fields.get("priority")
        priority = priority_obj.get("name") if priority_obj else None
        
        # Extract status
        status_obj = fields.get("status", {})
        status = status_obj.get("name", "Unknown")
        
        # Extract issue type
        issuetype_obj = fields.get("issuetype", {})
        issue_type = issuetype_obj.get("name", "Unknown")
        
        # Extract assignee and reporter
        assignee_obj = fields.get("assignee")
        assignee = assignee_obj.get("displayName") if assignee_obj else None
        
        reporter_obj = fields.get("reporter")
        reporter = reporter_obj.get("displayName") if reporter_obj else None
        
        # Extract labels
        labels = fields.get("labels", [])
        
        # Extract components
        components_list = fields.get("components", [])
        components = [comp.get("name", "") for comp in components_list]
        
        # Extract dates
        created = fields.get("created")
        updated = fields.get("updated")
        
        return JiraTicket(
            key=key,
            summary=summary,
            description=description_text,
            priority=priority,
            status=status,
            issue_type=issue_type,
            assignee=assignee,
            reporter=reporter,
            labels=labels,
            components=components,
            created=created,
            updated=updated
        )
    
    def _extract_text_from_adf(self, adf_content: Dict[str, Any]) -> str:
        """Extract plain text from Atlassian Document Format.
        
        Args:
            adf_content: ADF content dictionary
            
        Returns:
            Plain text string
        """
        def extract_text_recursive(node):
            if isinstance(node, dict):
                text_parts = []
                
                # Handle text nodes
                if node.get("type") == "text":
                    return node.get("text", "")
                
                # Handle other node types with content
                content = node.get("content", [])
                if isinstance(content, list):
                    for child in content:
                        child_text = extract_text_recursive(child)
                        if child_text:
                            text_parts.append(child_text)
                
                return " ".join(text_parts)
            elif isinstance(node, list):
                text_parts = []
                for item in node:
                    item_text = extract_text_recursive(item)
                    if item_text:
                        text_parts.append(item_text)
                return " ".join(text_parts)
            else:
                return str(node) if node else ""
        
        try:
            return extract_text_recursive(adf_content).strip()
        except Exception as e:
            app_logger.warning(f"Failed to extract text from ADF: {e}")
            return str(adf_content)
    
    def map_ticket_to_requirements(self, ticket: JiraTicket) -> Dict[str, Any]:
        """Map Jira ticket data to requirements format.
        
        Args:
            ticket: JiraTicket object
            
        Returns:
            Requirements dictionary compatible with the system
        """
        # Combine summary and description for the main description
        description_parts = [ticket.summary]
        if ticket.description:
            description_parts.append(ticket.description)
        
        requirements = {
            "description": " - ".join(description_parts),
            "source": "jira",
            "jira_key": ticket.key,
            "priority": ticket.priority,
            "status": ticket.status,
            "issue_type": ticket.issue_type,
            "assignee": ticket.assignee,
            "reporter": ticket.reporter,
            "labels": ticket.labels,
            "components": ticket.components,
            "created": ticket.created,
            "updated": ticket.updated
        }
        
        # Try to infer domain from components or labels
        domain_hints = []
        domain_hints.extend(ticket.components)
        domain_hints.extend(ticket.labels)
        
        # Map common Jira fields to domain categories
        domain_mapping = {
            "backend": "backend",
            "frontend": "frontend", 
            "api": "backend",
            "ui": "frontend",
            "database": "data",
            "data": "data",
            "integration": "integration",
            "automation": "automation",
            "testing": "testing",
            "devops": "devops",
            "infrastructure": "devops"
        }
        
        inferred_domains = []
        for hint in domain_hints:
            hint_lower = hint.lower()
            for key, domain in domain_mapping.items():
                if key in hint_lower:
                    inferred_domains.append(domain)
        
        if inferred_domains:
            requirements["domain"] = inferred_domains[0]  # Take first match
        
        # Try to infer pattern types from issue type and description
        pattern_types = []
        issue_type_lower = ticket.issue_type.lower()
        description_lower = (ticket.summary + " " + (ticket.description or "")).lower()
        
        # Pattern type inference rules
        if "story" in issue_type_lower or "feature" in issue_type_lower:
            pattern_types.append("feature_development")
        elif "bug" in issue_type_lower or "defect" in issue_type_lower:
            pattern_types.append("bug_fix")
        elif "task" in issue_type_lower:
            if any(word in description_lower for word in ["deploy", "release", "build"]):
                pattern_types.append("deployment")
            elif any(word in description_lower for word in ["test", "qa", "quality"]):
                pattern_types.append("testing")
            else:
                pattern_types.append("maintenance")
        
        # Add pattern types based on description keywords
        combined_text = description_lower + " " + " ".join(ticket.components).lower()
        if any(word in combined_text for word in ["api", "endpoint", "service"]):
            pattern_types.append("api_development")
        if any(word in combined_text for word in ["database", "migration", "schema"]):
            pattern_types.append("data_processing")
        if any(word in combined_text for word in ["automate", "automation", "script"]):
            pattern_types.append("automation")
        
        if pattern_types:
            requirements["pattern_types"] = list(set(pattern_types))  # Remove duplicates
        
        app_logger.info(f"Mapped Jira ticket {ticket.key} to requirements with domain: {requirements.get('domain')} and pattern_types: {requirements.get('pattern_types')}")
        
        return requirements


def create_jira_service(config: JiraConfig) -> JiraService:
    """Factory function to create JiraService instance.
    
    Args:
        config: Jira configuration
        
    Returns:
        JiraService instance
    """
    return JiraService(config)