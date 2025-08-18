"""Integration tests for Jira ticket fetching with API version support."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.jira import JiraService, JiraConnectionError, JiraTicketNotFoundError, JiraError
from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
from app.services.jira_auth import AuthResult


class TestJiraTicketFetching:
    """Integration tests for ticket fetching across API versions."""
    
    @pytest.fixture
    def data_center_config(self):
        """Jira Data Center configuration."""
        return JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test-pat-token"
        )
    
    @pytest.fixture
    def cloud_config(self):
        """Jira Cloud configuration."""
        return JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="test-token"
        )
    
    @pytest.fixture
    def mock_ticket_response_v3(self):
        """Mock ticket response for API v3."""
        return {
            "key": "PROJ-123",
            "fields": {
                "summary": "Test ticket summary",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "This is a test description with "
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
                },
                "status": {"name": "In Progress", "id": "3"},
                "issuetype": {"name": "Bug", "id": "1"},
                "priority": {"name": "High", "id": "2"},
                "assignee": {
                    "displayName": "John Doe",
                    "accountId": "123456",
                    "emailAddress": "john@example.com"
                },
                "reporter": {
                    "displayName": "Jane Smith",
                    "accountId": "789012",
                    "emailAddress": "jane@example.com"
                },
                "labels": ["urgent", "customer-facing"],
                "components": [
                    {"name": "Backend", "id": "10001"},
                    {"name": "API", "id": "10002"}
                ],
                "created": "2023-01-01T10:00:00.000+0000",
                "updated": "2023-01-02T15:30:00.000+0000",
                "customfield_10001": "Custom value",
                "customfield_10002": {"value": "Select option"},
                "customfield_10003": [
                    {"value": "Multi 1"},
                    {"value": "Multi 2"}
                ]
            }
        }
    
    @pytest.fixture
    def mock_ticket_response_v2(self):
        """Mock ticket response for API v2 (slightly different format)."""
        return {
            "key": "PROJ-456",
            "fields": {
                "summary": "Data Center ticket",
                "description": "Plain text description for Data Center",
                "status": {"name": "Open", "value": "Open"},
                "issuetype": {"name": "Story", "value": "Story"},
                "priority": {"name": "Medium", "value": "Medium"},
                "assignee": {
                    "displayName": "DC User",
                    "name": "dcuser",
                    "key": "dcuser"
                },
                "reporter": {
                    "displayName": "DC Reporter",
                    "name": "dcreporter",
                    "key": "dcreporter"
                },
                "labels": ["datacenter"],
                "components": [{"name": "Frontend"}],
                "created": "2023-01-01T10:00:00.000+0000",
                "updated": "2023-01-02T15:30:00.000+0000"
            }
        }
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_api_v3_success(self, cloud_config, mock_ticket_response_v3):
        """Test successful ticket fetching with API v3."""
        service = JiraService(cloud_config)
        service.api_version = "3"
        
        # Mock authentication
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTp0ZXN0LXRva2Vu"},
            error_message=None
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_ticket_response_v3
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value=mock_auth_result.headers), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         return_value="https://test.atlassian.net/rest/api/3/issue/PROJ-123"), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            ticket = await service.fetch_ticket("PROJ-123")
            
            assert ticket.key == "PROJ-123"
            assert ticket.summary == "Test ticket summary"
            assert "This is a test description with **bold text** and normal text." in ticket.description
            assert ticket.status == "In Progress"
            assert ticket.issue_type == "Bug"
            assert ticket.priority == "High"
            assert ticket.assignee == "John Doe"
            assert ticket.reporter == "Jane Smith"
            assert "urgent" in ticket.labels
            assert "customer-facing" in ticket.labels
            assert "Backend" in ticket.components
            assert "API" in ticket.components
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_api_v2_fallback(self, data_center_config, mock_ticket_response_v2):
        """Test ticket fetching with API v2 fallback."""
        service = JiraService(data_center_config)
        service.api_version = "3"  # Start with v3
        
        # Mock authentication
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            headers={"Authorization": "Bearer test-pat-token"},
            error_message=None
        )
        
        # Mock responses - v3 returns 404, v2 returns 200
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = mock_ticket_response_v2
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value=mock_auth_result.headers), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         side_effect=[
                             "https://jira.company.com/rest/api/3/issue/PROJ-456",
                             "https://jira.company.com/rest/api/2/issue/PROJ-456"
                         ]), \
             patch('httpx.AsyncClient') as mock_client:
            
            # First call (v3) returns 404, second call (v2) returns 200
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_response_404, mock_response_200
            ]
            
            ticket = await service.fetch_ticket("PROJ-456")
            
            assert ticket.key == "PROJ-456"
            assert ticket.summary == "Data Center ticket"
            assert ticket.description == "Plain text description for Data Center"
            assert ticket.status == "Open"
            assert ticket.issue_type == "Story"
            assert ticket.priority == "Medium"
            assert ticket.assignee == "DC User"
            assert ticket.reporter == "DC Reporter"
            assert service.api_version == "2"  # Should be updated to working version
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_authentication_retry(self, cloud_config, mock_ticket_response_v3):
        """Test ticket fetching with authentication retry on 401."""
        service = JiraService(cloud_config)
        
        # Mock authentication results
        mock_auth_result_old = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Basic b2xkLXRva2Vu"},
            error_message=None
        )
        
        mock_auth_result_new = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Basic bmV3LXRva2Vu"},
            error_message=None
        )
        
        # Mock responses - first returns 401, second returns 200
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = mock_ticket_response_v3
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         side_effect=[mock_auth_result_old.headers, mock_auth_result_new.headers]), \
             patch.object(service.auth_manager, 'clear_auth'), \
             patch.object(service.auth_manager, 'authenticate', return_value=mock_auth_result_new), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         return_value="https://test.atlassian.net/rest/api/3/issue/PROJ-123"), \
             patch('httpx.AsyncClient') as mock_client:
            
            # First call returns 401, second call returns 200
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_response_401, mock_response_200
            ]
            
            ticket = await service.fetch_ticket("PROJ-123")
            
            assert ticket.key == "PROJ-123"
            assert ticket.summary == "Test ticket summary"
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_not_found(self, cloud_config):
        """Test ticket fetching when ticket doesn't exist."""
        service = JiraService(cloud_config)
        service.api_version = "3"
        
        # Mock authentication
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTp0ZXN0LXRva2Vu"},
            error_message=None
        )
        
        # Mock 404 response for both API versions
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value=mock_auth_result.headers), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         side_effect=[
                             "https://test.atlassian.net/rest/api/3/issue/NONEXISTENT-123",
                             "https://test.atlassian.net/rest/api/2/issue/NONEXISTENT-123"
                         ]), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Both calls return 404
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response_404
            
            with pytest.raises(JiraTicketNotFoundError) as exc_info:
                await service.fetch_ticket("NONEXISTENT-123")
            
            assert "NONEXISTENT-123" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_with_complex_adf_description(self, cloud_config):
        """Test ticket fetching with complex ADF description."""
        service = JiraService(cloud_config)
        
        # Mock ticket with complex ADF description
        complex_adf_response = {
            "key": "PROJ-789",
            "fields": {
                "summary": "Complex ADF ticket",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "heading",
                            "attrs": {"level": 2},
                            "content": [{"type": "text", "text": "Problem Description"}]
                        },
                        {
                            "type": "paragraph",
                            "content": [
                                {"type": "text", "text": "This is a "},
                                {"type": "text", "text": "complex", "marks": [{"type": "strong"}]},
                                {"type": "text", "text": " issue with multiple formatting."}
                            ]
                        },
                        {
                            "type": "bulletList",
                            "content": [
                                {
                                    "type": "listItem",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "First bullet point"}]
                                        }
                                    ]
                                },
                                {
                                    "type": "listItem",
                                    "content": [
                                        {
                                            "type": "paragraph",
                                            "content": [{"type": "text", "text": "Second bullet point"}]
                                        }
                                    ]
                                }
                            ]
                        },
                        {
                            "type": "codeBlock",
                            "content": [{"type": "text", "text": "console.log('Hello World');"}]
                        }
                    ]
                },
                "status": {"name": "Open"},
                "issuetype": {"name": "Task"},
                "priority": {"name": "Low"},
                "assignee": None,
                "reporter": {"displayName": "Test User"},
                "labels": [],
                "components": [],
                "created": "2023-01-01T10:00:00.000+0000",
                "updated": "2023-01-02T15:30:00.000+0000"
            }
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = complex_adf_response
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value={"Authorization": "Basic test"}), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         return_value="https://test.atlassian.net/rest/api/3/issue/PROJ-789"), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            ticket = await service.fetch_ticket("PROJ-789")
            
            assert ticket.key == "PROJ-789"
            assert ticket.summary == "Complex ADF ticket"
            assert "## Problem Description" in ticket.description
            assert "This is a **complex** issue" in ticket.description
            assert "• First bullet point" in ticket.description
            assert "• Second bullet point" in ticket.description
            assert "```" in ticket.description
            assert "console.log('Hello World');" in ticket.description
    
    @pytest.mark.asyncio
    async def test_get_ticket_transitions(self, data_center_config):
        """Test getting ticket transitions."""
        service = JiraService(data_center_config)
        service.api_version = "3"
        
        # Mock transitions response
        transitions_response = {
            "transitions": [
                {
                    "id": "11",
                    "name": "Start Progress",
                    "to": {"name": "In Progress", "id": "3"},
                    "hasScreen": False
                },
                {
                    "id": "21",
                    "name": "Resolve Issue",
                    "to": {"name": "Resolved", "id": "5"},
                    "hasScreen": True
                }
            ]
        }
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = transitions_response
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value={"Authorization": "Bearer test-pat-token"}), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         return_value="https://jira.company.com/rest/api/3/issue/PROJ-123/transitions"), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            transitions = await service.get_ticket_transitions("PROJ-123")
            
            assert len(transitions) == 2
            assert transitions[0]["id"] == "11"
            assert transitions[0]["name"] == "Start Progress"
            assert transitions[0]["to"] == "In Progress"
            assert transitions[0]["hasScreen"] is False
            assert transitions[1]["id"] == "21"
            assert transitions[1]["name"] == "Resolve Issue"
            assert transitions[1]["to"] == "Resolved"
            assert transitions[1]["hasScreen"] is True
    
    @pytest.mark.asyncio
    async def test_parse_custom_fields(self, data_center_config, mock_ticket_response_v3):
        """Test parsing of custom fields."""
        service = JiraService(data_center_config)
        
        # Extract custom fields from mock response
        fields = mock_ticket_response_v3["fields"]
        custom_fields = service._parse_custom_fields(fields)
        
        assert "customfield_10001" in custom_fields
        assert custom_fields["customfield_10001"] == "Custom value"
        
        assert "customfield_10002" in custom_fields
        assert custom_fields["customfield_10002"] == "Select option"
        
        assert "customfield_10003" in custom_fields
        assert custom_fields["customfield_10003"] == ["Multi 1", "Multi 2"]
    
    @pytest.mark.asyncio
    async def test_handle_api_response_differences(self, data_center_config, mock_ticket_response_v2):
        """Test handling of API response differences between versions."""
        service = JiraService(data_center_config)
        
        # Test API v2 response normalization
        normalized_data = service._handle_api_response_differences(mock_ticket_response_v2, "2")
        
        fields = normalized_data["fields"]
        
        # Should normalize status field
        assert fields["status"]["name"] == "Open"
        
        # Should normalize priority field
        assert fields["priority"]["name"] == "Medium"
        
        # Should normalize issue type field
        assert fields["issuetype"]["name"] == "Story"
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_timeout_error(self, cloud_config):
        """Test ticket fetching with timeout error."""
        service = JiraService(cloud_config)
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value={"Authorization": "Basic test"}), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.TimeoutException("Request timed out")
            
            with pytest.raises(JiraConnectionError) as exc_info:
                await service.fetch_ticket("PROJ-123")
            
            assert "timeout" in str(exc_info.value).lower()
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_connection_error(self, cloud_config):
        """Test ticket fetching with connection error."""
        service = JiraService(cloud_config)
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value={"Authorization": "Basic test"}), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.ConnectError("Connection failed")
            
            with pytest.raises(JiraConnectionError) as exc_info:
                await service.fetch_ticket("PROJ-123")
            
            assert "Failed to connect to Jira" in str(exc_info.value)