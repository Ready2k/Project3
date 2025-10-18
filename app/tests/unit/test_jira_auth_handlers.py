"""Unit tests for Jira authentication handlers."""

import pytest
import base64

from app.services.jira_auth_handlers import (
    APITokenHandler,
    PATHandler,
    SSOAuthHandler,
    BasicAuthHandler,
)
from app.config import JiraAuthType, JiraConfig


class TestAPITokenHandler:
    """Test cases for APITokenHandler."""

    def test_get_auth_type(self):
        """Test getting authentication type."""
        handler = APITokenHandler()
        assert handler.get_auth_type() == JiraAuthType.API_TOKEN

    def test_validate_config_valid(self):
        """Test config validation with valid configuration."""
        handler = APITokenHandler()

        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
        )

        assert handler.validate_config(config) is True

    def test_validate_config_missing_email(self):
        """Test config validation with missing email."""
        handler = APITokenHandler()

        config = JiraConfig(base_url="https://test.atlassian.net", api_token="token123")

        assert handler.validate_config(config) is False

    def test_validate_config_missing_api_token(self):
        """Test config validation with missing API token."""
        handler = APITokenHandler()

        config = JiraConfig(
            base_url="https://test.atlassian.net", email="test@example.com"
        )

        assert handler.validate_config(config) is False

    def test_validate_config_none_values(self):
        """Test config validation with None values."""
        handler = APITokenHandler()

        config = JiraConfig(
            base_url="https://test.atlassian.net", email=None, api_token=None
        )

        assert handler.validate_config(config) is False

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful API token authentication."""
        handler = APITokenHandler()

        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
        )

        result = await handler.authenticate(config)

        assert result.success is True
        assert result.auth_type == JiraAuthType.API_TOKEN
        assert result.error_message is None

        # Verify Basic Auth header is correctly formatted
        expected_auth = base64.b64encode(b"test@example.com:token123").decode("ascii")
        assert result.headers["Authorization"] == f"Basic {expected_auth}"
        assert result.headers["Accept"] == "application/json"
        assert result.headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_config(self):
        """Test authentication with invalid configuration."""
        handler = APITokenHandler()

        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            # Missing api_token
        )

        result = await handler.authenticate(config)

        assert result.success is False
        assert result.auth_type == JiraAuthType.API_TOKEN
        assert (
            "API token authentication requires email and api_token"
            in result.error_message
        )
        assert result.headers == {}

    @pytest.mark.asyncio
    async def test_authenticate_encoding_error(self):
        """Test authentication with encoding issues."""
        handler = APITokenHandler()

        # Create a config with non-ASCII characters that might cause encoding issues
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            email="test@example.com",
            api_token="token123",
        )

        # Mock the base64 encoding to raise an exception
        original_b64encode = base64.b64encode

        def mock_b64encode(data):
            raise UnicodeEncodeError("ascii", "test", 0, 1, "test error")

        base64.b64encode = mock_b64encode

        try:
            result = await handler.authenticate(config)

            assert result.success is False
            assert result.auth_type == JiraAuthType.API_TOKEN
            assert "API token authentication error" in result.error_message
            assert result.headers == {}
        finally:
            # Restore original function
            base64.b64encode = original_b64encode


class TestPATHandler:
    """Test cases for PATHandler."""

    def test_get_auth_type(self):
        """Test getting authentication type."""
        handler = PATHandler()
        assert handler.get_auth_type() == JiraAuthType.PERSONAL_ACCESS_TOKEN

    def test_validate_config_valid(self):
        """Test config validation with valid configuration."""
        handler = PATHandler()

        config = JiraConfig(
            base_url="https://jira.company.com", personal_access_token="pat_token123"
        )

        assert handler.validate_config(config) is True

    def test_validate_config_missing_pat(self):
        """Test config validation with missing PAT."""
        handler = PATHandler()

        config = JiraConfig(base_url="https://jira.company.com")

        assert handler.validate_config(config) is False

    def test_validate_config_none_pat(self):
        """Test config validation with None PAT."""
        handler = PATHandler()

        config = JiraConfig(
            base_url="https://jira.company.com", personal_access_token=None
        )

        assert handler.validate_config(config) is False

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful PAT authentication."""
        handler = PATHandler()

        config = JiraConfig(
            base_url="https://jira.company.com", personal_access_token="pat_token123"
        )

        result = await handler.authenticate(config)

        assert result.success is True
        assert result.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert result.error_message is None

        # Verify Bearer token header is correctly formatted
        assert result.headers["Authorization"] == "Bearer pat_token123"
        assert result.headers["Accept"] == "application/json"
        assert result.headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_config(self):
        """Test authentication with invalid configuration."""
        handler = PATHandler()

        config = JiraConfig(
            base_url="https://jira.company.com"
            # Missing personal_access_token
        )

        result = await handler.authenticate(config)

        assert result.success is False
        assert result.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert (
            "PAT authentication requires personal_access_token" in result.error_message
        )
        assert result.headers == {}


class TestSSOAuthHandler:
    """Test cases for SSOAuthHandler."""

    def test_get_auth_type(self):
        """Test getting authentication type."""
        handler = SSOAuthHandler()
        assert handler.get_auth_type() == JiraAuthType.SSO

    def test_validate_config_with_use_sso_true(self):
        """Test config validation with use_sso=True."""
        handler = SSOAuthHandler()

        config = JiraConfig(base_url="https://jira.company.com", use_sso=True)

        assert handler.validate_config(config) is True

    def test_validate_config_with_session_cookie(self):
        """Test config validation with existing session cookie."""
        handler = SSOAuthHandler()

        config = JiraConfig(
            base_url="https://jira.company.com", sso_session_cookie="JSESSIONID=abc123"
        )

        assert handler.validate_config(config) is True

    def test_validate_config_invalid(self):
        """Test config validation with invalid configuration."""
        handler = SSOAuthHandler()

        config = JiraConfig(base_url="https://jira.company.com", use_sso=False)

        assert handler.validate_config(config) is False

    @pytest.mark.asyncio
    async def test_authenticate_with_session_cookie(self):
        """Test authentication with existing session cookie."""
        handler = SSOAuthHandler()

        config = JiraConfig(
            base_url="https://jira.company.com", sso_session_cookie="JSESSIONID=abc123"
        )

        result = await handler.authenticate(config)

        assert result.success is True
        assert result.auth_type == JiraAuthType.SSO
        assert result.error_message is None

        # Verify session cookie is included
        assert result.headers["Cookie"] == "JSESSIONID=abc123"
        assert result.headers["Accept"] == "application/json"
        assert result.headers["Content-Type"] == "application/json"

        # Verify session data
        assert result.session_data is not None
        assert result.session_data["session_cookie"] == "JSESSIONID=abc123"

    @pytest.mark.asyncio
    async def test_authenticate_without_session_cookie(self):
        """Test authentication without existing session cookie (should fail for now)."""
        handler = SSOAuthHandler()

        config = JiraConfig(base_url="https://jira.company.com", use_sso=True)

        result = await handler.authenticate(config)

        # Should fail since session detection is not implemented
        assert result.success is False
        assert result.auth_type == JiraAuthType.SSO
        assert "SSO session detection not yet implemented" in result.error_message
        assert result.requires_fallback is True

    @pytest.mark.asyncio
    async def test_authenticate_invalid_config(self):
        """Test authentication with invalid configuration."""
        handler = SSOAuthHandler()

        config = JiraConfig(base_url="https://jira.company.com", use_sso=False)

        result = await handler.authenticate(config)

        assert result.success is False
        assert result.auth_type == JiraAuthType.SSO
        assert (
            "SSO authentication requires use_sso=True or existing session cookie"
            in result.error_message
        )


class TestBasicAuthHandler:
    """Test cases for BasicAuthHandler."""

    def test_get_auth_type(self):
        """Test getting authentication type."""
        handler = BasicAuthHandler()
        assert handler.get_auth_type() == JiraAuthType.BASIC

    def test_validate_config_valid(self):
        """Test config validation with valid configuration."""
        handler = BasicAuthHandler()

        config = JiraConfig(
            base_url="https://jira.company.com",
            username="testuser",
            password="testpass",
        )

        assert handler.validate_config(config) is True

    def test_validate_config_missing_username(self):
        """Test config validation with missing username."""
        handler = BasicAuthHandler()

        config = JiraConfig(base_url="https://jira.company.com", password="testpass")

        assert handler.validate_config(config) is False

    def test_validate_config_missing_password(self):
        """Test config validation with missing password."""
        handler = BasicAuthHandler()

        config = JiraConfig(base_url="https://jira.company.com", username="testuser")

        assert handler.validate_config(config) is False

    def test_validate_config_none_values(self):
        """Test config validation with None values."""
        handler = BasicAuthHandler()

        config = JiraConfig(
            base_url="https://jira.company.com", username=None, password=None
        )

        assert handler.validate_config(config) is False

    @pytest.mark.asyncio
    async def test_authenticate_success(self):
        """Test successful basic authentication."""
        handler = BasicAuthHandler()

        config = JiraConfig(
            base_url="https://jira.company.com",
            username="testuser",
            password="testpass",
        )

        result = await handler.authenticate(config)

        assert result.success is True
        assert result.auth_type == JiraAuthType.BASIC
        assert result.error_message is None

        # Verify Basic Auth header is correctly formatted
        expected_auth = base64.b64encode(b"testuser:testpass").decode("ascii")
        assert result.headers["Authorization"] == f"Basic {expected_auth}"
        assert result.headers["Accept"] == "application/json"
        assert result.headers["Content-Type"] == "application/json"

    @pytest.mark.asyncio
    async def test_authenticate_invalid_config(self):
        """Test authentication with invalid configuration."""
        handler = BasicAuthHandler()

        config = JiraConfig(
            base_url="https://jira.company.com",
            username="testuser",
            # Missing password
        )

        result = await handler.authenticate(config)

        assert result.success is False
        assert result.auth_type == JiraAuthType.BASIC
        assert (
            "Basic authentication requires username and password"
            in result.error_message
        )
        assert result.requires_fallback is True
        assert result.headers == {}
