"""
Unit tests for Jira error handling and troubleshooting system.
"""

import httpx

from app.services.jira_error_handler import (
    JiraErrorHandler,
    JiraErrorType,
    JiraErrorDetail,
    create_jira_error_handler,
)
from app.config import JiraDeploymentType


class TestJiraErrorHandler:
    """Test cases for JiraErrorHandler."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = JiraErrorHandler()
        self.dc_handler = JiraErrorHandler(JiraDeploymentType.DATA_CENTER)

    def test_init_with_deployment_type(self):
        """Test initialization with deployment type."""
        handler = JiraErrorHandler(JiraDeploymentType.DATA_CENTER)
        assert handler.deployment_type == JiraDeploymentType.DATA_CENTER

        handler = JiraErrorHandler(JiraDeploymentType.CLOUD)
        assert handler.deployment_type == JiraDeploymentType.CLOUD

    def test_detect_error_type_by_status_code(self):
        """Test error type detection based on HTTP status codes."""
        # Test authentication errors
        assert (
            self.handler.detect_error_type("Auth failed", status_code=401)
            == JiraErrorType.AUTH_INVALID_CREDENTIALS
        )
        assert (
            self.handler.detect_error_type("Forbidden", status_code=403)
            == JiraErrorType.AUTH_INSUFFICIENT_PERMISSIONS
        )

        # Test API errors
        assert (
            self.handler.detect_error_type("Not found", status_code=404)
            == JiraErrorType.API_ENDPOINT_NOT_FOUND
        )
        assert (
            self.handler.detect_error_type("Rate limited", status_code=429)
            == JiraErrorType.API_RATE_LIMITED
        )
        assert (
            self.handler.detect_error_type("Server error", status_code=500)
            == JiraErrorType.API_SERVER_ERROR
        )
        assert (
            self.handler.detect_error_type("Bad gateway", status_code=502)
            == JiraErrorType.API_SERVER_ERROR
        )

    def test_detect_error_type_by_exception(self):
        """Test error type detection based on exception types."""
        timeout_exception = httpx.TimeoutException("Request timed out")
        assert (
            self.handler.detect_error_type("Timeout", exception=timeout_exception)
            == JiraErrorType.CONNECTION_TIMEOUT
        )

        connect_exception = httpx.ConnectError("Connection refused")
        assert (
            self.handler.detect_error_type(
                "Connect failed", exception=connect_exception
            )
            == JiraErrorType.CONNECTION_REFUSED
        )

        network_exception = httpx.NetworkError("Network unreachable")
        assert (
            self.handler.detect_error_type("Network error", exception=network_exception)
            == JiraErrorType.NETWORK_UNREACHABLE
        )

    def test_detect_error_type_by_message_patterns(self):
        """Test error type detection based on message patterns."""
        # Connection errors
        assert (
            self.handler.detect_error_type("Connection timeout occurred")
            == JiraErrorType.CONNECTION_TIMEOUT
        )
        assert (
            self.handler.detect_error_type("Connection refused by server")
            == JiraErrorType.CONNECTION_REFUSED
        )
        assert (
            self.handler.detect_error_type("DNS resolution failed")
            == JiraErrorType.DNS_RESOLUTION
        )
        assert (
            self.handler.detect_error_type("Network is unreachable")
            == JiraErrorType.NETWORK_UNREACHABLE
        )

        # SSL errors
        assert (
            self.handler.detect_error_type("SSL certificate verify failed")
            == JiraErrorType.SSL_CERTIFICATE_ERROR
        )
        assert (
            self.handler.detect_error_type("SSL handshake failed")
            == JiraErrorType.SSL_HANDSHAKE_FAILED
        )
        assert (
            self.handler.detect_error_type("Hostname doesn't match certificate")
            == JiraErrorType.SSL_VERIFICATION_FAILED
        )

        # Authentication errors
        assert (
            self.handler.detect_error_type("Invalid credentials provided")
            == JiraErrorType.AUTH_INVALID_CREDENTIALS
        )
        assert (
            self.handler.detect_error_type("Token has expired")
            == JiraErrorType.AUTH_TOKEN_EXPIRED
        )
        assert (
            self.handler.detect_error_type("SSO authentication failed")
            == JiraErrorType.AUTH_SSO_FAILED
        )

        # API errors
        assert (
            self.handler.detect_error_type("API version not supported")
            == JiraErrorType.API_VERSION_NOT_SUPPORTED
        )
        assert (
            self.handler.detect_error_type("Rate limit exceeded")
            == JiraErrorType.API_RATE_LIMITED
        )

        # Data Center specific
        assert (
            self.handler.detect_error_type("Version not supported")
            == JiraErrorType.DC_VERSION_INCOMPATIBLE
        )
        assert (
            self.handler.detect_error_type("Context path invalid")
            == JiraErrorType.DC_CONTEXT_PATH_INVALID
        )

        # Ticket errors
        assert (
            self.handler.detect_error_type("Issue not found")
            == JiraErrorType.TICKET_NOT_FOUND
        )
        assert (
            self.handler.detect_error_type("Issue access denied")
            == JiraErrorType.TICKET_ACCESS_DENIED
        )

    def test_detect_error_type_unknown(self):
        """Test detection of unknown error types."""
        assert (
            self.handler.detect_error_type("Some random error message")
            == JiraErrorType.UNKNOWN_ERROR
        )

    def test_create_error_detail_basic(self):
        """Test creating basic error detail."""
        error_detail = self.handler.create_error_detail(
            error_message="Connection timeout occurred",
            status_code=None,
            exception=None,
        )

        assert error_detail.error_type == JiraErrorType.CONNECTION_TIMEOUT
        assert error_detail.message == "Connection timeout occurred"
        assert error_detail.error_code is None
        assert len(error_detail.troubleshooting_steps) > 0
        assert len(error_detail.documentation_links) > 0

    def test_create_error_detail_with_status_code(self):
        """Test creating error detail with status code."""
        error_detail = self.handler.create_error_detail(
            error_message="Authentication failed", status_code=401
        )

        assert error_detail.error_type == JiraErrorType.AUTH_INVALID_CREDENTIALS
        assert error_detail.error_code == "401"
        assert (
            "Verify username and password/token are correct"
            in error_detail.troubleshooting_steps
        )

    def test_create_error_detail_with_exception(self):
        """Test creating error detail with exception."""
        timeout_exception = httpx.TimeoutException("Request timed out")
        error_detail = self.handler.create_error_detail(
            error_message="Request failed", exception=timeout_exception
        )

        assert error_detail.error_type == JiraErrorType.CONNECTION_TIMEOUT
        assert (
            "Check if the Jira server is running" in error_detail.troubleshooting_steps
        )

    def test_create_error_detail_with_technical_details(self):
        """Test creating error detail with technical details."""
        error_detail = self.handler.create_error_detail(
            error_message="SSL error",
            technical_details="Certificate chain validation failed",
        )

        assert error_detail.technical_details == "Certificate chain validation failed"

    def test_data_center_specific_guidance(self):
        """Test Data Center specific troubleshooting guidance."""
        error_detail = self.dc_handler.create_error_detail(
            error_message="Connection timeout occurred"
        )

        # Should include Data Center specific steps
        dc_specific_found = any(
            "Data Center" in step or "Tomcat" in step or "cluster" in step
            for step in error_detail.troubleshooting_steps
        )
        assert dc_specific_found
        assert error_detail.deployment_specific_guidance is not None

    def test_ssl_certificate_error_guidance(self):
        """Test SSL certificate error specific guidance."""
        error_detail = self.handler.create_error_detail(
            error_message="SSL certificate verify failed"
        )

        assert error_detail.error_type == JiraErrorType.SSL_CERTIFICATE_ERROR
        assert any(
            "self-signed" in step.lower() for step in error_detail.troubleshooting_steps
        )
        assert any("verify_ssl" in str(error_detail.suggested_config_changes).lower())

    def test_authentication_error_guidance(self):
        """Test authentication error specific guidance."""
        error_detail = self.dc_handler.create_error_detail(
            error_message="Invalid credentials", status_code=401
        )

        assert error_detail.error_type == JiraErrorType.AUTH_INVALID_CREDENTIALS
        assert any("PAT" in step for step in error_detail.troubleshooting_steps)
        assert any(
            "Personal Access Token" in step
            for step in error_detail.troubleshooting_steps
        )

    def test_api_version_error_guidance(self):
        """Test API version error specific guidance."""
        error_detail = self.handler.create_error_detail(
            error_message="API version not supported"
        )

        assert error_detail.error_type == JiraErrorType.API_VERSION_NOT_SUPPORTED
        assert any(
            "automatically try API v2" in step
            for step in error_detail.troubleshooting_steps
        )

    def test_data_center_version_error_guidance(self):
        """Test Data Center version compatibility error guidance."""
        error_detail = self.dc_handler.create_error_detail(
            error_message="Version not supported for Data Center"
        )

        assert error_detail.error_type == JiraErrorType.DC_VERSION_INCOMPATIBLE
        assert any("9.12.22" in step for step in error_detail.troubleshooting_steps)
        assert any("8.0" in step for step in error_detail.troubleshooting_steps)

    def test_context_path_error_guidance(self):
        """Test Data Center context path error guidance."""
        error_detail = self.dc_handler.create_error_detail(
            error_message="Context path invalid"
        )

        assert error_detail.error_type == JiraErrorType.DC_CONTEXT_PATH_INVALID
        assert any("/jira" in step for step in error_detail.troubleshooting_steps)
        assert any("server.xml" in step for step in error_detail.troubleshooting_steps)

    def test_ticket_not_found_error_guidance(self):
        """Test ticket not found error guidance."""
        error_detail = self.handler.create_error_detail(
            error_message="Issue PROJ-123 not found"
        )

        assert error_detail.error_type == JiraErrorType.TICKET_NOT_FOUND
        assert any(
            "ticket key is correct" in step
            for step in error_detail.troubleshooting_steps
        )
        assert any("PROJ-123" in step for step in error_detail.troubleshooting_steps)

    def test_get_error_category_summary(self):
        """Test getting error category summary."""
        categories = self.handler.get_error_category_summary()

        assert "Connection Issues" in categories
        assert "SSL/Security Issues" in categories
        assert "Authentication Issues" in categories
        assert "API Issues" in categories
        assert "Configuration Issues" in categories
        assert "Data Center Specific" in categories
        assert "Data Issues" in categories

        # Check that each category has error types
        for category, error_types in categories.items():
            assert len(error_types) > 0
            assert all(
                isinstance(error_type, JiraErrorType) for error_type in error_types
            )

    def test_documentation_links_included(self):
        """Test that documentation links are included in error details."""
        error_detail = self.handler.create_error_detail(
            error_message="SSL certificate error"
        )

        assert len(error_detail.documentation_links) > 0
        assert any("atlassian.com" in link for link in error_detail.documentation_links)

    def test_suggested_config_changes(self):
        """Test that suggested configuration changes are provided when appropriate."""
        # SSL error should suggest config changes
        ssl_error = self.handler.create_error_detail(
            error_message="SSL certificate verify failed"
        )
        assert ssl_error.suggested_config_changes is not None
        assert "verify_ssl" in ssl_error.suggested_config_changes

        # Timeout error should suggest config changes
        timeout_error = self.handler.create_error_detail(
            error_message="Connection timeout"
        )
        assert timeout_error.suggested_config_changes is not None
        assert "timeout" in timeout_error.suggested_config_changes

    def test_case_insensitive_pattern_matching(self):
        """Test that error pattern matching is case insensitive."""
        # Test various cases
        assert (
            self.handler.detect_error_type("CONNECTION TIMEOUT")
            == JiraErrorType.CONNECTION_TIMEOUT
        )
        assert (
            self.handler.detect_error_type("connection timeout")
            == JiraErrorType.CONNECTION_TIMEOUT
        )
        assert (
            self.handler.detect_error_type("Connection Timeout")
            == JiraErrorType.CONNECTION_TIMEOUT
        )
        assert (
            self.handler.detect_error_type("SSL CERTIFICATE ERROR")
            == JiraErrorType.SSL_CERTIFICATE_ERROR
        )

    def test_multiple_pattern_matching(self):
        """Test that multiple patterns can match the same error type."""
        # Connection timeout has multiple patterns
        assert (
            self.handler.detect_error_type("timeout occurred")
            == JiraErrorType.CONNECTION_TIMEOUT
        )
        assert (
            self.handler.detect_error_type("connection timed out")
            == JiraErrorType.CONNECTION_TIMEOUT
        )
        assert (
            self.handler.detect_error_type("TimeoutException raised")
            == JiraErrorType.CONNECTION_TIMEOUT
        )

    def test_priority_of_detection_methods(self):
        """Test that status code takes priority over message patterns."""
        # Status code should take priority
        error_detail = self.handler.create_error_detail(
            error_message="Connection timeout occurred",  # Would normally be CONNECTION_TIMEOUT
            status_code=401,  # Should override to AUTH_INVALID_CREDENTIALS
        )
        assert error_detail.error_type == JiraErrorType.AUTH_INVALID_CREDENTIALS

        # Exception should take priority over message patterns
        timeout_exception = httpx.TimeoutException("Request timed out")
        error_detail = self.handler.create_error_detail(
            error_message="Some other error",  # Would normally be UNKNOWN_ERROR
            exception=timeout_exception,  # Should override to CONNECTION_TIMEOUT
        )
        assert error_detail.error_type == JiraErrorType.CONNECTION_TIMEOUT


class TestJiraErrorHandlerFactory:
    """Test cases for the factory function."""

    def test_create_jira_error_handler_default(self):
        """Test creating error handler with default parameters."""
        handler = create_jira_error_handler()
        assert isinstance(handler, JiraErrorHandler)
        assert handler.deployment_type is None

    def test_create_jira_error_handler_with_deployment_type(self):
        """Test creating error handler with specific deployment type."""
        handler = create_jira_error_handler(JiraDeploymentType.DATA_CENTER)
        assert isinstance(handler, JiraErrorHandler)
        assert handler.deployment_type == JiraDeploymentType.DATA_CENTER

        handler = create_jira_error_handler(JiraDeploymentType.CLOUD)
        assert isinstance(handler, JiraErrorHandler)
        assert handler.deployment_type == JiraDeploymentType.CLOUD


class TestJiraErrorDetail:
    """Test cases for JiraErrorDetail model."""

    def test_error_detail_creation(self):
        """Test creating JiraErrorDetail with all fields."""
        error_detail = JiraErrorDetail(
            error_type=JiraErrorType.CONNECTION_TIMEOUT,
            error_code="TIMEOUT",
            message="Connection timed out",
            technical_details="TCP connection timeout after 30 seconds",
            troubleshooting_steps=["Check network connectivity", "Increase timeout"],
            documentation_links=["https://example.com/docs"],
            suggested_config_changes={"timeout": 60},
            deployment_specific_guidance="Data Center specific guidance",
        )

        assert error_detail.error_type == JiraErrorType.CONNECTION_TIMEOUT
        assert error_detail.error_code == "TIMEOUT"
        assert error_detail.message == "Connection timed out"
        assert (
            error_detail.technical_details == "TCP connection timeout after 30 seconds"
        )
        assert len(error_detail.troubleshooting_steps) == 2
        assert len(error_detail.documentation_links) == 1
        assert error_detail.suggested_config_changes == {"timeout": 60}
        assert (
            error_detail.deployment_specific_guidance == "Data Center specific guidance"
        )

    def test_error_detail_minimal(self):
        """Test creating JiraErrorDetail with minimal required fields."""
        error_detail = JiraErrorDetail(
            error_type=JiraErrorType.UNKNOWN_ERROR, message="Unknown error occurred"
        )

        assert error_detail.error_type == JiraErrorType.UNKNOWN_ERROR
        assert error_detail.message == "Unknown error occurred"
        assert error_detail.error_code is None
        assert error_detail.technical_details is None
        assert error_detail.troubleshooting_steps == []
        assert error_detail.documentation_links == []
        assert error_detail.suggested_config_changes is None
        assert error_detail.deployment_specific_guidance is None

    def test_error_detail_enum_serialization(self):
        """Test that enum values are properly serialized."""
        error_detail = JiraErrorDetail(
            error_type=JiraErrorType.CONNECTION_TIMEOUT, message="Test error"
        )

        # Test that the model can be serialized to dict
        error_dict = error_detail.model_dump()
        assert error_dict["error_type"] == "connection_timeout"  # Enum value, not name

        # Test that the model can be serialized to JSON
        error_json = error_detail.model_dump_json()
        assert "connection_timeout" in error_json
