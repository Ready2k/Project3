"""Unit tests for enhanced Jira API request models."""

import pytest
from pydantic import ValidationError

from app.api import (
    JiraTestRequest,
    JiraFetchRequest,
    JiraErrorDetail,
    JiraTestResponse,
    JiraFetchResponse,
)


class TestJiraTestRequest:
    """Test cases for JiraTestRequest model."""

    def test_basic_api_token_request(self):
        """Test basic API token request validation."""
        request = JiraTestRequest(
            base_url="https://company.atlassian.net",
            auth_type="api_token",
            email="user@company.com",
            api_token="ATATT3xFfGF0...",
        )

        assert request.base_url == "https://company.atlassian.net"
        assert request.auth_type == "api_token"
        assert request.email == "user@company.com"
        assert request.api_token == "ATATT3xFfGF0..."
        assert request.verify_ssl is True
        assert request.timeout == 30
        assert request.max_retries == 3

    def test_data_center_pat_request(self):
        """Test Data Center PAT request validation."""
        request = JiraTestRequest(
            base_url="https://jira.company.com",
            auth_type="pat",
            personal_access_token="NjE2NzY4NzQ2MDEyOqGb4HUoWD+HZ+4=",
            context_path="/jira",
            custom_port=8080,
            verify_ssl=False,
        )

        assert request.base_url == "https://jira.company.com"
        assert request.auth_type == "pat"
        assert request.personal_access_token == "NjE2NzY4NzQ2MDEyOqGb4HUoWD+HZ+4="
        assert request.context_path == "/jira"
        assert request.custom_port == 8080
        assert request.verify_ssl is False

    def test_sso_request(self):
        """Test SSO request validation."""
        request = JiraTestRequest(
            base_url="https://jira.company.com",
            auth_type="sso",
            use_sso=True,
            sso_session_cookie="JSESSIONID=ABC123",
        )

        assert request.base_url == "https://jira.company.com"
        assert request.auth_type == "sso"
        assert request.use_sso is True
        assert request.sso_session_cookie == "JSESSIONID=ABC123"

    def test_basic_auth_request(self):
        """Test basic authentication request validation."""
        request = JiraTestRequest(
            base_url="https://jira.company.com",
            auth_type="basic",
            username="admin",
            password="password123",
        )

        assert request.base_url == "https://jira.company.com"
        assert request.auth_type == "basic"
        assert request.username == "admin"
        assert request.password == "password123"

    def test_network_configuration(self):
        """Test network configuration options."""
        request = JiraTestRequest(
            base_url="https://jira.company.com",
            auth_type="api_token",
            email="user@company.com",
            api_token="token123",
            ca_cert_path="/path/to/ca.crt",
            proxy_url="http://proxy.company.com:8080",
            timeout=60,
            max_retries=5,
            retry_delay=2.0,
        )

        assert request.ca_cert_path == "/path/to/ca.crt"
        assert request.proxy_url == "http://proxy.company.com:8080"
        assert request.timeout == 60
        assert request.max_retries == 5
        assert request.retry_delay == 2.0

    def test_base_url_normalization(self):
        """Test base URL normalization."""
        request = JiraTestRequest(
            base_url="https://jira.company.com/",
            auth_type="api_token",
            email="user@company.com",
            api_token="token123",
        )

        # Trailing slash should be removed
        assert request.base_url == "https://jira.company.com"

    def test_invalid_base_url(self):
        """Test invalid base URL validation."""
        with pytest.raises(ValidationError) as exc_info:
            JiraTestRequest(
                base_url="invalid-url",
                auth_type="api_token",
                email="user@company.com",
                api_token="token123",
            )

        assert "Base URL must start with http:// or https://" in str(exc_info.value)

    def test_invalid_auth_type(self):
        """Test invalid authentication type validation."""
        with pytest.raises(ValidationError) as exc_info:
            JiraTestRequest(
                base_url="https://jira.company.com",
                auth_type="invalid_auth",
                email="user@company.com",
                api_token="token123",
            )

        assert "Invalid auth_type" in str(exc_info.value)

    def test_invalid_custom_port(self):
        """Test invalid custom port validation."""
        with pytest.raises(ValidationError) as exc_info:
            JiraTestRequest(
                base_url="https://jira.company.com",
                auth_type="api_token",
                email="user@company.com",
                api_token="token123",
                custom_port=70000,
            )

        assert "Custom port must be between 1 and 65535" in str(exc_info.value)

    def test_invalid_timeout(self):
        """Test invalid timeout validation."""
        with pytest.raises(ValidationError) as exc_info:
            JiraTestRequest(
                base_url="https://jira.company.com",
                auth_type="api_token",
                email="user@company.com",
                api_token="token123",
                timeout=0,
            )

        assert "Timeout must be at least 1 second" in str(exc_info.value)

    def test_auth_config_validation_api_token(self):
        """Test authentication configuration validation for API token."""
        request = JiraTestRequest(
            base_url="https://jira.company.com", auth_type="api_token"
        )

        errors = request.validate_auth_config()
        assert "Email is required for API token authentication" in errors
        assert "API token is required for API token authentication" in errors

    def test_auth_config_validation_pat(self):
        """Test authentication configuration validation for PAT."""
        request = JiraTestRequest(base_url="https://jira.company.com", auth_type="pat")

        errors = request.validate_auth_config()
        assert "Personal access token is required for PAT authentication" in errors

    def test_auth_config_validation_basic(self):
        """Test authentication configuration validation for basic auth."""
        request = JiraTestRequest(
            base_url="https://jira.company.com", auth_type="basic"
        )

        errors = request.validate_auth_config()
        assert "Username is required for basic authentication" in errors
        assert "Password is required for basic authentication" in errors

    def test_auth_config_validation_sso(self):
        """Test authentication configuration validation for SSO."""
        request = JiraTestRequest(
            base_url="https://jira.company.com", auth_type="sso", use_sso=False
        )

        errors = request.validate_auth_config()
        assert "SSO must be enabled for SSO authentication" in errors

    def test_valid_auth_config(self):
        """Test valid authentication configuration."""
        request = JiraTestRequest(
            base_url="https://jira.company.com",
            auth_type="api_token",
            email="user@company.com",
            api_token="token123",
        )

        errors = request.validate_auth_config()
        assert len(errors) == 0


class TestJiraFetchRequest:
    """Test cases for JiraFetchRequest model."""

    def test_valid_fetch_request(self):
        """Test valid fetch request."""
        request = JiraFetchRequest(
            base_url="https://jira.company.com",
            auth_type="api_token",
            email="user@company.com",
            api_token="token123",
            ticket_key="PROJ-123",
        )

        assert request.ticket_key == "PROJ-123"
        assert request.base_url == "https://jira.company.com"
        assert request.auth_type == "api_token"

    def test_ticket_key_normalization(self):
        """Test ticket key normalization to uppercase."""
        request = JiraFetchRequest(
            base_url="https://jira.company.com",
            auth_type="api_token",
            email="user@company.com",
            api_token="token123",
            ticket_key="proj-123",
        )

        assert request.ticket_key == "PROJ-123"

    def test_invalid_ticket_key_format(self):
        """Test invalid ticket key format validation."""
        with pytest.raises(ValidationError) as exc_info:
            JiraFetchRequest(
                base_url="https://jira.company.com",
                auth_type="api_token",
                email="user@company.com",
                api_token="token123",
                ticket_key="invalid-key",
            )

        assert "Invalid ticket key format" in str(exc_info.value)

    def test_empty_ticket_key(self):
        """Test empty ticket key validation."""
        with pytest.raises(ValidationError) as exc_info:
            JiraFetchRequest(
                base_url="https://jira.company.com",
                auth_type="api_token",
                email="user@company.com",
                api_token="token123",
                ticket_key="",
            )

        assert "Ticket key is required" in str(exc_info.value)

    def test_complex_ticket_key(self):
        """Test complex ticket key formats."""
        valid_keys = ["PROJ-123", "ABC123-456", "A-1", "PROJECT123-999"]

        for key in valid_keys:
            request = JiraFetchRequest(
                base_url="https://jira.company.com",
                auth_type="api_token",
                email="user@company.com",
                api_token="token123",
                ticket_key=key,
            )
            assert request.ticket_key == key.upper()


class TestJiraErrorDetail:
    """Test cases for JiraErrorDetail model."""

    def test_basic_error_detail(self):
        """Test basic error detail creation."""
        error = JiraErrorDetail(
            error_type="connection_error",
            message="Failed to connect to Jira",
            troubleshooting_steps=[
                "Check network connectivity",
                "Verify base URL is correct",
            ],
        )

        assert error.error_type == "connection_error"
        assert error.message == "Failed to connect to Jira"
        assert len(error.troubleshooting_steps) == 2
        assert error.error_code is None
        assert len(error.documentation_links) == 0

    def test_detailed_error_detail(self):
        """Test detailed error detail with all fields."""
        error = JiraErrorDetail(
            error_type="authentication_error",
            error_code="401",
            message="Invalid credentials",
            troubleshooting_steps=[
                "Check API token is valid",
                "Verify email address is correct",
            ],
            documentation_links=[
                "https://support.atlassian.com/atlassian-account/docs/manage-api-tokens-for-your-atlassian-account/"
            ],
            suggested_config_changes={"auth_type": "pat", "use_sso": True},
        )

        assert error.error_type == "authentication_error"
        assert error.error_code == "401"
        assert error.message == "Invalid credentials"
        assert len(error.troubleshooting_steps) == 2
        assert len(error.documentation_links) == 1
        assert error.suggested_config_changes["auth_type"] == "pat"


class TestJiraTestResponse:
    """Test cases for JiraTestResponse model."""

    def test_successful_response(self):
        """Test successful test response."""
        response = JiraTestResponse(
            ok=True,
            message="Connection successful",
            deployment_info={
                "deployment_type": "data_center",
                "version": "9.12.22",
                "build_number": "912022",
            },
            auth_methods_available=["api_token", "pat", "sso"],
            api_version_detected="3",
        )

        assert response.ok is True
        assert response.message == "Connection successful"
        assert response.deployment_info["deployment_type"] == "data_center"
        assert "pat" in response.auth_methods_available
        assert response.api_version_detected == "3"

    def test_error_response(self):
        """Test error response with troubleshooting."""
        error_detail = JiraErrorDetail(
            error_type="ssl_error",
            message="SSL certificate verification failed",
            troubleshooting_steps=[
                "Add CA certificate to trust store",
                "Set verify_ssl to false for testing",
            ],
        )

        response = JiraTestResponse(
            ok=False, message="SSL verification failed", error_details=error_detail
        )

        assert response.ok is False
        assert response.message == "SSL verification failed"
        assert response.error_details.error_type == "ssl_error"
        assert len(response.error_details.troubleshooting_steps) == 2


class TestJiraFetchResponse:
    """Test cases for JiraFetchResponse model."""

    def test_successful_fetch_response(self):
        """Test successful fetch response."""
        response = JiraFetchResponse(
            ticket_data={
                "key": "PROJ-123",
                "summary": "Test ticket",
                "description": "Test description",
            },
            requirements={"description": "Test requirements", "domain": "automation"},
            deployment_info={"deployment_type": "cloud", "version": "1001.0.0"},
            api_version_used="3",
        )

        assert response.ticket_data["key"] == "PROJ-123"
        assert response.requirements["description"] == "Test requirements"
        assert response.deployment_info["deployment_type"] == "cloud"
        assert response.api_version_used == "3"

    def test_minimal_fetch_response(self):
        """Test minimal fetch response."""
        response = JiraFetchResponse(
            ticket_data={"key": "PROJ-123"}, requirements={"description": "Test"}
        )

        assert response.ticket_data["key"] == "PROJ-123"
        assert response.requirements["description"] == "Test"
        assert response.deployment_info is None
        assert response.api_version_used is None
