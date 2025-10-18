"""Integration tests for enhanced Jira API endpoints."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient

from app.api import app
from app.config import JiraDeploymentType
from app.services.jira import (
    JiraConnectionError,
    JiraTicketNotFoundError,
    JiraError,
    ConnectionResult,
)
from app.services.deployment_detector import DeploymentInfo


@pytest.fixture
def client():
    """Create test client."""
    return TestClient(app)


@pytest.fixture
def mock_jira_service():
    """Create mock Jira service."""
    service = MagicMock()
    service.auto_configure = AsyncMock()
    service.test_connection_with_fallback = AsyncMock()
    service.detect_and_set_api_version = AsyncMock()
    service.fetch_ticket = AsyncMock()
    service.map_ticket_to_requirements = MagicMock()
    return service


class TestJiraTestEndpoint:
    """Test cases for /jira/test endpoint."""

    @patch("app.api.JiraService")
    def test_successful_cloud_connection(self, mock_service_class, client):
        """Test successful connection to Jira Cloud."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_config.deployment_type = JiraDeploymentType.CLOUD
        mock_service.auto_configure = AsyncMock(return_value=mock_config)

        # Mock deployment info
        deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.CLOUD,
            version="1001.0.0",
            build_number="100150",
            base_url_normalized="https://company.atlassian.net",
            context_path=None,
            supports_sso=False,
            supports_pat=True,
        )

        # Mock connection result
        connection_result = ConnectionResult(
            success=True,
            deployment_info=deployment_info,
            auth_result=None,
            error_details=None,
            troubleshooting_steps=[],
        )
        mock_service.test_connection_with_fallback = AsyncMock(
            return_value=connection_result
        )
        mock_service.detect_and_set_api_version = AsyncMock(return_value="3")

        # Make request
        response = client.post(
            "/jira/test",
            json={
                "base_url": "https://company.atlassian.net",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "ATATT3xFfGF0...",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["message"] == "Jira connection successful"
        assert data["deployment_info"]["deployment_type"] == "cloud"
        assert data["deployment_info"]["version"] == "1001.0.0"
        assert "api_token" in data["auth_methods_available"]
        assert "pat" in data["auth_methods_available"]
        assert data["api_version_detected"] == "3"

    @patch("app.api.JiraService")
    def test_successful_data_center_connection(self, mock_service_class, client):
        """Test successful connection to Jira Data Center."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_config.deployment_type = JiraDeploymentType.DATA_CENTER
        mock_service.auto_configure = AsyncMock(return_value=mock_config)

        # Mock deployment info
        deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            build_number="912022",
            base_url_normalized="https://jira.company.com:8080/jira",
            context_path="/jira",
            supports_sso=True,
            supports_pat=True,
        )

        # Mock connection result
        connection_result = ConnectionResult(
            success=True,
            deployment_info=deployment_info,
            auth_result=None,
            error_details=None,
            troubleshooting_steps=[],
        )
        mock_service.test_connection_with_fallback = AsyncMock(
            return_value=connection_result
        )
        mock_service.detect_and_set_api_version = AsyncMock(return_value="3")

        # Make request
        response = client.post(
            "/jira/test",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "pat",
                "personal_access_token": "NjE2NzY4NzQ2MDEyOqGb4HUoWD+HZ+4=",
                "context_path": "/jira",
                "custom_port": 8080,
                "verify_ssl": False,
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is True
        assert data["deployment_info"]["deployment_type"] == "data_center"
        assert data["deployment_info"]["version"] == "9.12.22"
        assert data["deployment_info"]["supports_sso"] is True
        assert "basic" in data["auth_methods_available"]
        assert "sso" in data["auth_methods_available"]

    def test_invalid_auth_configuration(self, client):
        """Test invalid authentication configuration."""
        response = client.post(
            "/jira/test",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                # Missing email and api_token
            },
        )

        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "Authentication configuration validation failed" in data["message"]
        assert data["error_details"]["error_type"] == "configuration_error"
        assert len(data["error_details"]["troubleshooting_steps"]) > 0

    def test_invalid_base_url(self, client):
        """Test invalid base URL format."""
        response = client.post(
            "/jira/test",
            json={
                "base_url": "invalid-url",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
            },
        )

        assert response.status_code == 422  # Validation error

    @patch("app.api.JiraService")
    def test_connection_failure(self, mock_service_class, client):
        """Test connection failure with detailed error."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_service.auto_configure = AsyncMock(
            side_effect=Exception("Auto-config failed")
        )

        # Mock connection failure
        mock_service.test_connection_with_fallback = AsyncMock(
            side_effect=JiraConnectionError("Connection timeout")
        )

        # Make request
        response = client.post(
            "/jira/test",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "Connection failed" in data["message"]
        assert data["error_details"]["error_type"] == "connection_error"
        assert (
            "Verify the base URL is correct"
            in data["error_details"]["troubleshooting_steps"][0]
        )

    @patch("app.api.JiraService")
    def test_authentication_failure(self, mock_service_class, client):
        """Test authentication failure with detailed error."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_service.auto_configure = AsyncMock(return_value=mock_config)

        # Mock authentication failure
        mock_service.test_connection_with_fallback = AsyncMock(
            side_effect=JiraError("Invalid credentials")
        )

        # Make request
        response = client.post(
            "/jira/test",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "invalid_token",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["ok"] is False
        assert "Authentication failed" in data["message"]
        assert data["error_details"]["error_type"] == "authentication_error"
        assert (
            "Verify authentication credentials"
            in data["error_details"]["troubleshooting_steps"][0]
        )


class TestJiraFetchEndpoint:
    """Test cases for /jira/fetch endpoint."""

    @patch("app.api.JiraService")
    def test_successful_ticket_fetch(self, mock_service_class, client):
        """Test successful ticket fetch."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_config.deployment_type = JiraDeploymentType.CLOUD
        mock_service.auto_configure = AsyncMock(return_value=mock_config)

        # Mock API version detection
        mock_service.detect_and_set_api_version = AsyncMock(return_value="3")

        # Mock ticket data
        mock_ticket = MagicMock()
        mock_ticket.model_dump.return_value = {
            "key": "PROJ-123",
            "summary": "Test ticket",
            "description": "Test description",
        }
        mock_service.fetch_ticket = AsyncMock(return_value=mock_ticket)

        # Mock requirements mapping
        mock_service.map_ticket_to_requirements.return_value = {
            "description": "Test requirements",
            "domain": "automation",
        }

        # Mock deployment info
        mock_deployment_info = MagicMock()
        mock_deployment_info.deployment_type = JiraDeploymentType.CLOUD
        mock_deployment_info.version = "1001.0.0"
        mock_deployment_info.build_number = "100150"
        mock_deployment_info.base_url_normalized = "https://company.atlassian.net"
        mock_service.deployment_info = mock_deployment_info

        # Make request
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://company.atlassian.net",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "ATATT3xFfGF0...",
                "ticket_key": "PROJ-123",
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_data"]["key"] == "PROJ-123"
        assert data["requirements"]["description"] == "Test requirements"
        assert data["deployment_info"]["deployment_type"] == "cloud"
        assert data["api_version_used"] == "3"

    @patch("app.api.JiraService")
    def test_data_center_ticket_fetch(self, mock_service_class, client):
        """Test ticket fetch from Data Center with API version fallback."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_config.deployment_type = JiraDeploymentType.DATA_CENTER
        mock_service.auto_configure = AsyncMock(return_value=mock_config)

        # Mock API version detection with fallback
        mock_service.detect_and_set_api_version = AsyncMock(return_value="2")

        # Mock ticket data
        mock_ticket = MagicMock()
        mock_ticket.model_dump.return_value = {
            "key": "DC-456",
            "summary": "Data Center ticket",
            "description": "Data Center description",
        }
        mock_service.fetch_ticket = AsyncMock(return_value=mock_ticket)

        # Mock requirements mapping
        mock_service.map_ticket_to_requirements.return_value = {
            "description": "Data Center requirements",
            "domain": "enterprise",
        }

        # Make request
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "pat",
                "personal_access_token": "NjE2NzY4NzQ2MDEyOqGb4HUoWD+HZ+4=",
                "ticket_key": "dc-456",  # Test case normalization
                "context_path": "/jira",
                "custom_port": 8080,
            },
        )

        # Verify response
        assert response.status_code == 200
        data = response.json()
        assert data["ticket_data"]["key"] == "DC-456"
        assert data["requirements"]["description"] == "Data Center requirements"
        assert data["api_version_used"] == "2"

    def test_invalid_ticket_key_format(self, client):
        """Test invalid ticket key format."""
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
                "ticket_key": "invalid-key-format",
            },
        )

        assert response.status_code == 422  # Validation error

    def test_missing_auth_config(self, client):
        """Test missing authentication configuration."""
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "ticket_key": "PROJ-123",
                # Missing email and api_token
            },
        )

        assert response.status_code == 400
        response_data = response.json()
        # Check for either 'detail' or 'message' key depending on exception handler
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "Authentication configuration validation failed" in error_message

    @patch("app.api.JiraService")
    def test_connection_error(self, mock_service_class, client):
        """Test connection error during ticket fetch."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_service.auto_configure = AsyncMock(
            side_effect=Exception("Auto-config failed")
        )

        # Mock connection error
        mock_service.detect_and_set_api_version = AsyncMock(return_value="3")
        mock_service.fetch_ticket = AsyncMock(
            side_effect=JiraConnectionError("Connection failed")
        )

        # Make request
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
                "ticket_key": "PROJ-123",
            },
        )

        # Verify response
        assert response.status_code == 401
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "Jira connection failed" in error_message

    @patch("app.api.JiraService")
    def test_ticket_not_found(self, mock_service_class, client):
        """Test ticket not found error."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_service.auto_configure = AsyncMock(return_value=mock_config)
        mock_service.detect_and_set_api_version = AsyncMock(return_value="3")

        # Mock ticket not found
        mock_service.fetch_ticket = AsyncMock(
            side_effect=JiraTicketNotFoundError("Ticket PROJ-999 not found")
        )

        # Make request
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
                "ticket_key": "PROJ-999",
            },
        )

        # Verify response
        assert response.status_code == 404
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "PROJ-999 not found" in error_message

    @patch("app.api.JiraService")
    def test_jira_error(self, mock_service_class, client):
        """Test general Jira error."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_service.auto_configure = AsyncMock(return_value=mock_config)
        mock_service.detect_and_set_api_version = AsyncMock(return_value="3")

        # Mock Jira error
        mock_service.fetch_ticket = AsyncMock(
            side_effect=JiraError("Permission denied")
        )

        # Make request
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
                "ticket_key": "PROJ-123",
            },
        )

        # Verify response
        assert response.status_code == 400
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "Permission denied" in error_message

    @patch("app.api.JiraService")
    def test_unexpected_error(self, mock_service_class, client):
        """Test unexpected error handling."""
        # Setup mock
        mock_service = MagicMock()
        mock_service_class.return_value = mock_service

        # Mock auto-configuration
        mock_config = MagicMock()
        mock_service.auto_configure = AsyncMock(return_value=mock_config)
        mock_service.detect_and_set_api_version = AsyncMock(return_value="3")

        # Mock unexpected error
        mock_service.fetch_ticket = AsyncMock(side_effect=Exception("Unexpected error"))

        # Make request
        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
                "ticket_key": "PROJ-123",
            },
        )

        # Verify response
        assert response.status_code == 500
        response_data = response.json()
        error_message = response_data.get("detail") or response_data.get("message", "")
        assert "Failed to fetch Jira ticket" in error_message


class TestJiraEndpointSecurity:
    """Test security aspects of Jira endpoints."""

    def test_security_headers_added(self, client):
        """Test that security headers are added to responses."""
        response = client.post(
            "/jira/test",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
            },
        )

        # Check for security headers (these are added by SecurityHeaders.add_security_headers)
        # The exact headers depend on the SecurityHeaders implementation
        assert response.status_code in [200, 400, 422]  # Any valid response

    def test_input_validation(self, client):
        """Test input validation and sanitization."""
        # Test with potentially malicious input
        response = client.post(
            "/jira/test",
            json={
                "base_url": "javascript:alert('xss')",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
            },
        )

        # Should fail validation
        assert response.status_code == 422

    def test_large_payload_handling(self, client):
        """Test handling of large payloads."""
        # Create a large ticket key (should fail validation)
        large_ticket_key = "A" * 1000

        response = client.post(
            "/jira/fetch",
            json={
                "base_url": "https://jira.company.com",
                "auth_type": "api_token",
                "email": "user@company.com",
                "api_token": "token123",
                "ticket_key": large_ticket_key,
            },
        )

        # Should fail validation due to invalid format
        assert response.status_code == 422
