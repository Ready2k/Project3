"""Integration tests for Jira service with mocked responses."""

from unittest.mock import AsyncMock, patch, MagicMock

import httpx
import pytest
from fastapi.testclient import TestClient

from app.api import app
from app.config import JiraConfig
from app.services.jira import (
    JiraService, 
    JiraTicket, 
    JiraConnectionError, 
    JiraTicketNotFoundError
)


class TestJiraService:
    """Test Jira service functionality with mocked HTTP responses."""
    
    @pytest.fixture
    def jira_config(self):
        """Create test Jira configuration."""
        return JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="test_token_123",
            timeout=30
        )
    
    @pytest.fixture
    def jira_service(self, jira_config):
        """Create Jira service instance."""
        return JiraService(jira_config)
    
    @pytest.fixture
    def mock_jira_ticket_response(self):
        """Mock Jira API ticket response."""
        return {
            "key": "PROJ-123",
            "fields": {
                "summary": "Implement user authentication system",
                "description": {
                    "type": "doc",
                    "version": 1,
                    "content": [
                        {
                            "type": "paragraph",
                            "content": [
                                {
                                    "type": "text",
                                    "text": "We need to implement a secure user authentication system with OAuth2 support."
                                }
                            ]
                        }
                    ]
                },
                "priority": {"name": "High"},
                "status": {"name": "In Progress"},
                "issuetype": {"name": "Story"},
                "assignee": {"displayName": "John Doe"},
                "reporter": {"displayName": "Jane Smith"},
                "labels": ["backend", "security"],
                "components": [{"name": "Authentication"}],
                "created": "2024-01-15T10:30:00.000+0000",
                "updated": "2024-01-16T14:20:00.000+0000"
            }
        }
    
    @pytest.fixture
    def mock_user_response(self):
        """Mock Jira API user response for connection testing."""
        return {
            "accountId": "123456789",
            "displayName": "Test User",
            "emailAddress": "test@example.com",
            "active": True
        }
    
    @pytest.mark.asyncio
    async def test_successful_connection(self, jira_service, mock_user_response):
        """Test successful Jira connection."""
        # Create a proper mock response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_user_response
        
        # Mock the entire httpx.AsyncClient context manager
        with patch('httpx.AsyncClient') as mock_client_class:
            # Create async context manager mock
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            # Set up the context manager
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context
            
            success, error_msg = await jira_service.test_connection()
            
            assert success is True
            assert error_msg is None
    
    @pytest.mark.asyncio
    async def test_connection_authentication_failure(self, jira_service):
        """Test Jira connection with authentication failure."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context
            
            success, error_msg = await jira_service.test_connection()
            
            assert success is False
            assert "Authentication failed" in error_msg
    
    @pytest.mark.asyncio
    async def test_connection_timeout(self, jira_service):
        """Test Jira connection timeout."""
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(side_effect=httpx.TimeoutException("Timeout"))
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context
            
            success, error_msg = await jira_service.test_connection()
            
            assert success is False
            assert "timeout" in error_msg.lower()
    
    @pytest.mark.asyncio
    async def test_connection_invalid_config(self):
        """Test Jira connection with invalid configuration."""
        invalid_config = JiraConfig()  # Empty config
        service = JiraService(invalid_config)
        
        success, error_msg = await service.test_connection()
        
        assert success is False
        assert "base URL is required" in error_msg
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_success(self, jira_service, mock_jira_ticket_response):
        """Test successful ticket fetching."""
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = mock_jira_ticket_response
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context
            
            ticket = await jira_service.fetch_ticket("PROJ-123")
            
            assert isinstance(ticket, JiraTicket)
            assert ticket.key == "PROJ-123"
            assert ticket.summary == "Implement user authentication system"
            assert "OAuth2 support" in ticket.description
            assert ticket.priority == "High"
            assert ticket.status == "In Progress"
            assert ticket.issue_type == "Story"
            assert ticket.assignee == "John Doe"
            assert ticket.reporter == "Jane Smith"
            assert "backend" in ticket.labels
            assert "Authentication" in ticket.components
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_not_found(self, jira_service):
        """Test fetching non-existent ticket."""
        mock_response = MagicMock()
        mock_response.status_code = 404
        mock_response.text = "Issue does not exist"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context
            
            with pytest.raises(JiraTicketNotFoundError) as exc_info:
                await jira_service.fetch_ticket("NONEXISTENT-123")
            
            assert "not found" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_authentication_error(self, jira_service):
        """Test fetching ticket with authentication error."""
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.text = "Unauthorized"
        
        with patch('httpx.AsyncClient') as mock_client_class:
            mock_client = AsyncMock()
            mock_client.get = AsyncMock(return_value=mock_response)
            
            mock_context = AsyncMock()
            mock_context.__aenter__ = AsyncMock(return_value=mock_client)
            mock_context.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_context
            
            with pytest.raises(JiraConnectionError) as exc_info:
                await jira_service.fetch_ticket("PROJ-123")
            
            assert "Authentication failed" in str(exc_info.value)
    
    def test_map_ticket_to_requirements(self, jira_service):
        """Test mapping Jira ticket to requirements format."""
        ticket = JiraTicket(
            key="PROJ-123",
            summary="Implement user authentication",
            description="Add OAuth2 support for secure login",
            priority="High",
            status="In Progress",
            issue_type="Story",
            assignee="John Doe",
            reporter="Jane Smith",
            labels=["backend", "security"],
            components=["Authentication", "API"],
            created="2024-01-15T10:30:00.000+0000",
            updated="2024-01-16T14:20:00.000+0000"
        )
        
        requirements = jira_service.map_ticket_to_requirements(ticket)
        
        assert requirements["source"] == "jira"
        assert requirements["jira_key"] == "PROJ-123"
        assert "Implement user authentication" in requirements["description"]
        assert "OAuth2 support" in requirements["description"]
        assert requirements["priority"] == "High"
        assert requirements["status"] == "In Progress"
        assert requirements["issue_type"] == "Story"
        assert requirements["assignee"] == "John Doe"
        assert requirements["reporter"] == "Jane Smith"
        assert requirements["labels"] == ["backend", "security"]
        assert requirements["components"] == ["Authentication", "API"]
        
        # Check domain inference
        assert requirements["domain"] == "backend"
        
        # Check pattern type inference
        assert "feature_development" in requirements["pattern_types"]
        assert "api_development" in requirements["pattern_types"]
    
    def test_extract_text_from_adf(self, jira_service):
        """Test extracting text from Atlassian Document Format."""
        adf_content = {
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
                            "text": "multiple text nodes."
                        }
                    ]
                },
                {
                    "type": "paragraph",
                    "content": [
                        {
                            "type": "text",
                            "text": "Second paragraph here."
                        }
                    ]
                }
            ]
        }
        
        text = jira_service._extract_text_from_adf(adf_content)
        
        assert "This is a test description" in text
        assert "multiple text nodes" in text
        assert "Second paragraph here" in text
    
    def test_extract_text_from_simple_string(self, jira_service):
        """Test extracting text from simple string description."""
        simple_description = "Simple string description"
        
        # When description is already a string, it should be returned as-is
        # This tests the fallback behavior in _parse_ticket_data
        ticket_data = {
            "key": "TEST-1",
            "fields": {
                "summary": "Test summary",
                "description": simple_description,
                "status": {"name": "Open"},
                "issuetype": {"name": "Task"}
            }
        }
        
        ticket = jira_service._parse_ticket_data(ticket_data)
        assert ticket.description == simple_description


class TestJiraAPIEndpoints:
    """Test Jira API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_jira_test_endpoint_success(self, client):
        """Test Jira connection test endpoint with successful connection."""
        with patch('app.services.jira.JiraService.test_connection') as mock_test:
            mock_test.return_value = (True, None)
            
            response = client.post("/jira/test", json={
                "base_url": "https://test.atlassian.net",
                "email": "test@example.com",
                "api_token": "test_token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert "successful" in data["message"]
    
    def test_jira_test_endpoint_failure(self, client):
        """Test Jira connection test endpoint with connection failure."""
        with patch('app.services.jira.JiraService.test_connection') as mock_test:
            mock_test.return_value = (False, "Authentication failed")
            
            response = client.post("/jira/test", json={
                "base_url": "https://test.atlassian.net",
                "email": "test@example.com",
                "api_token": "invalid_token"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is False
            assert "Authentication failed" in data["message"]
    
    def test_jira_fetch_endpoint_success(self, client):
        """Test Jira ticket fetch endpoint with successful fetch."""
        mock_ticket = JiraTicket(
            key="PROJ-123",
            summary="Test ticket",
            description="Test description",
            priority="Medium",
            status="Open",
            issue_type="Task",
            labels=["test"],
            components=["TestComponent"]
        )
        
        with patch('app.services.jira.JiraService.fetch_ticket') as mock_fetch:
            mock_fetch.return_value = mock_ticket
            
            with patch('app.services.jira.JiraService.map_ticket_to_requirements') as mock_map:
                mock_requirements = {
                    "description": "Test ticket - Test description",
                    "source": "jira",
                    "jira_key": "PROJ-123"
                }
                mock_map.return_value = mock_requirements
                
                response = client.post("/jira/fetch", json={
                    "ticket_key": "PROJ-123",
                    "base_url": "https://test.atlassian.net",
                    "email": "test@example.com",
                    "api_token": "test_token"
                })
                
                assert response.status_code == 200
                data = response.json()
                assert data["ticket_data"]["key"] == "PROJ-123"
                assert data["requirements"]["jira_key"] == "PROJ-123"
    
    def test_jira_fetch_endpoint_ticket_not_found(self, client):
        """Test Jira ticket fetch endpoint with ticket not found."""
        with patch('app.services.jira.JiraService.fetch_ticket') as mock_fetch:
            mock_fetch.side_effect = JiraTicketNotFoundError("Ticket 'NONEXISTENT-123' not found")
            
            response = client.post("/jira/fetch", json={
                "ticket_key": "NONEXISTENT-123",
                "base_url": "https://test.atlassian.net",
                "email": "test@example.com",
                "api_token": "test_token"
            })
            
            assert response.status_code == 404
            assert "not found" in response.json()["detail"]
    
    def test_jira_fetch_endpoint_connection_error(self, client):
        """Test Jira ticket fetch endpoint with connection error."""
        with patch('app.services.jira.JiraService.fetch_ticket') as mock_fetch:
            mock_fetch.side_effect = JiraConnectionError("Authentication failed")
            
            response = client.post("/jira/fetch", json={
                "ticket_key": "PROJ-123",
                "base_url": "https://test.atlassian.net",
                "email": "test@example.com",
                "api_token": "invalid_token"
            })
            
            assert response.status_code == 401
            assert "connection failed" in response.json()["detail"]
    
    def test_ingest_jira_source_success(self, client):
        """Test ingest endpoint with Jira source."""
        mock_ticket = JiraTicket(
            key="PROJ-123",
            summary="Test ticket",
            description="Test description",
            priority="Medium",
            status="Open",
            issue_type="Task"
        )
        
        with patch('app.services.jira.JiraService.fetch_ticket') as mock_fetch:
            mock_fetch.return_value = mock_ticket
            
            with patch('app.services.jira.JiraService.map_ticket_to_requirements') as mock_map:
                mock_requirements = {
                    "description": "Test ticket - Test description",
                    "source": "jira",
                    "jira_key": "PROJ-123"
                }
                mock_map.return_value = mock_requirements
                
                response = client.post("/ingest", json={
                    "source": "jira",
                    "payload": {
                        "ticket_key": "PROJ-123",
                        "base_url": "https://test.atlassian.net",
                        "email": "test@example.com",
                        "api_token": "test_token"
                    }
                })
                
                assert response.status_code == 200
                data = response.json()
                assert "session_id" in data
    
    def test_ingest_jira_source_missing_ticket_key(self, client):
        """Test ingest endpoint with Jira source but missing ticket key."""
        response = client.post("/ingest", json={
            "source": "jira",
            "payload": {
                "base_url": "https://test.atlassian.net",
                "email": "test@example.com",
                "api_token": "test_token"
                # Missing ticket_key
            }
        })
        
        assert response.status_code == 400
        assert "ticket_key is required" in response.json()["detail"]
    
    def test_ingest_jira_source_ticket_not_found(self, client):
        """Test ingest endpoint with Jira source and non-existent ticket."""
        with patch('app.services.jira.JiraService.fetch_ticket') as mock_fetch:
            mock_fetch.side_effect = JiraTicketNotFoundError("Ticket not found")
            
            response = client.post("/ingest", json={
                "source": "jira",
                "payload": {
                    "ticket_key": "NONEXISTENT-123",
                    "base_url": "https://test.atlassian.net",
                    "email": "test@example.com",
                    "api_token": "test_token"
                }
            })
            
            assert response.status_code == 404
            assert "Ticket not found" in response.json()["detail"]


class TestJiraConfigurationIntegration:
    """Test Jira configuration integration."""
    
    def test_jira_config_from_environment(self):
        """Test loading Jira configuration from environment variables."""
        import os
        from app.config import load_settings
        
        # Set environment variables
        os.environ["JIRA_BASE_URL"] = "https://env.atlassian.net"
        os.environ["JIRA_EMAIL"] = "env@example.com"
        os.environ["JIRA_API_TOKEN"] = "env_token"
        
        try:
            settings = load_settings()
            assert settings.jira.base_url == "https://env.atlassian.net"
            assert settings.jira.email == "env@example.com"
            assert settings.jira.api_token == "env_token"
        finally:
            # Clean up environment variables
            for key in ["JIRA_BASE_URL", "JIRA_EMAIL", "JIRA_API_TOKEN"]:
                if key in os.environ:
                    del os.environ[key]
    
    def test_jira_config_defaults(self):
        """Test Jira configuration defaults."""
        from app.config import JiraConfig
        
        config = JiraConfig()
        assert config.base_url is None
        assert config.email is None
        assert config.api_token is None
        assert config.timeout == 30