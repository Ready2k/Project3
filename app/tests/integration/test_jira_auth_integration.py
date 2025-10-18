"""Integration tests for Jira authentication system."""

import pytest

from app.services.jira_auth import AuthenticationManager
from app.services.jira_auth_handlers import (
    APITokenHandler,
    PATHandler,
    SSOAuthHandler,
    BasicAuthHandler,
)
from app.config import JiraConfig, JiraAuthType


class TestJiraAuthenticationIntegration:
    """Integration tests for the complete authentication system."""

    def setup_method(self):
        """Set up test fixtures."""
        self.manager = None

    def create_manager_with_all_handlers(
        self, config: JiraConfig
    ) -> AuthenticationManager:
        """Create authentication manager with all handlers registered."""
        manager = AuthenticationManager(config)

        # Register all handlers
        manager.register_handler(APITokenHandler())
        manager.register_handler(PATHandler())
        manager.register_handler(SSOAuthHandler())
        manager.register_handler(BasicAuthHandler())

        return manager

    @pytest.mark.asyncio
    async def test_api_token_authentication_flow(self):
        """Test complete API token authentication flow."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="token123",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Test authentication
        result = await manager.authenticate()

        assert result.success is True
        assert result.auth_type == JiraAuthType.API_TOKEN
        assert "Basic" in result.headers["Authorization"]

        # Test getting auth headers
        headers = await manager.get_auth_headers()
        assert "Authorization" in headers
        assert headers["Accept"] == "application/json"

        # Test authentication status
        assert manager.is_authenticated() is True

        # Test available auth types
        available = manager.get_available_auth_types()
        assert JiraAuthType.API_TOKEN in available

    @pytest.mark.asyncio
    async def test_pat_authentication_flow(self):
        """Test complete PAT authentication flow."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="pat_token123",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Test authentication
        result = await manager.authenticate()

        assert result.success is True
        assert result.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert result.headers["Authorization"] == "Bearer pat_token123"

        # Test getting auth headers
        headers = await manager.get_auth_headers()
        assert headers["Authorization"] == "Bearer pat_token123"

        # Test authentication status
        assert manager.is_authenticated() is True

    @pytest.mark.asyncio
    async def test_sso_authentication_with_cookie_flow(self):
        """Test complete SSO authentication flow with existing cookie."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.SSO,
            sso_session_cookie="JSESSIONID=abc123",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Test authentication
        result = await manager.authenticate()

        assert result.success is True
        assert result.auth_type == JiraAuthType.SSO
        assert result.headers["Cookie"] == "JSESSIONID=abc123"
        assert result.session_data["session_cookie"] == "JSESSIONID=abc123"

        # Test getting auth headers
        headers = await manager.get_auth_headers()
        assert headers["Cookie"] == "JSESSIONID=abc123"

    @pytest.mark.asyncio
    async def test_basic_authentication_flow(self):
        """Test complete basic authentication flow."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.BASIC,
            username="testuser",
            password="testpass",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Test authentication
        result = await manager.authenticate()

        assert result.success is True
        assert result.auth_type == JiraAuthType.BASIC
        assert "Basic" in result.headers["Authorization"]

        # Test getting auth headers
        headers = await manager.get_auth_headers()
        assert "Authorization" in headers

    @pytest.mark.asyncio
    async def test_authentication_fallback_chain(self):
        """Test authentication fallback when primary method fails."""
        # Configure for API token but don't provide the token
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            # Missing api_token, so should fallback
            personal_access_token="pat_token123",  # This should work as fallback
        )

        manager = self.create_manager_with_all_handlers(config)

        # Test authentication - should fallback to PAT
        result = await manager.authenticate()

        assert result.success is True
        assert result.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert result.headers["Authorization"] == "Bearer pat_token123"

    @pytest.mark.asyncio
    async def test_authentication_fallback_to_basic(self):
        """Test authentication fallback to basic auth."""
        # Configure for SSO but without session cookie, should fallback to basic
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.SSO,
            use_sso=True,  # SSO enabled but no session cookie
            username="testuser",
            password="testpass",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Test authentication - should fallback to basic
        result = await manager.authenticate()

        assert result.success is True
        assert result.auth_type == JiraAuthType.BASIC
        assert "Basic" in result.headers["Authorization"]

    @pytest.mark.asyncio
    async def test_all_authentication_methods_fail(self):
        """Test when all authentication methods fail."""
        # Configure with no valid credentials
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.API_TOKEN,
            # No credentials provided
        )

        manager = self.create_manager_with_all_handlers(config)

        # Test authentication - should fail
        result = await manager.authenticate()

        assert result.success is False
        assert result.error_message == "All authentication methods failed"
        assert result.requires_fallback is True

        # Test getting auth headers returns empty
        headers = await manager.get_auth_headers()
        assert headers == {}

        # Test authentication status
        assert manager.is_authenticated() is False

    @pytest.mark.asyncio
    async def test_multiple_valid_auth_methods(self):
        """Test when multiple authentication methods are valid."""
        # Configure with both API token and PAT
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="token123",
            personal_access_token="pat_token123",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Should use the configured auth type (API_TOKEN) first
        result = await manager.authenticate()

        assert result.success is True
        assert result.auth_type == JiraAuthType.API_TOKEN
        assert "Basic" in result.headers["Authorization"]

        # Test available auth types includes both
        available = manager.get_available_auth_types()
        assert JiraAuthType.API_TOKEN in available
        assert JiraAuthType.PERSONAL_ACCESS_TOKEN in available

    @pytest.mark.asyncio
    async def test_clear_authentication(self):
        """Test clearing authentication state."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="token123",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Authenticate first
        result = await manager.authenticate()
        assert result.success is True
        assert manager.is_authenticated() is True

        # Clear authentication
        manager.clear_auth()

        # Should no longer be authenticated
        assert manager.is_authenticated() is False
        assert manager.get_current_auth_result() is None

    @pytest.mark.asyncio
    async def test_re_authentication_after_clear(self):
        """Test re-authentication after clearing state."""
        config = JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="token123",
        )

        manager = self.create_manager_with_all_handlers(config)

        # Authenticate, clear, then authenticate again
        result1 = await manager.authenticate()
        assert result1.success is True

        manager.clear_auth()
        assert manager.is_authenticated() is False

        result2 = await manager.authenticate()
        assert result2.success is True
        assert result2.auth_type == JiraAuthType.API_TOKEN
        assert manager.is_authenticated() is True

    def test_get_available_auth_types_comprehensive(self):
        """Test getting available auth types with various configurations."""
        # Test with all auth methods configured
        config = JiraConfig(
            base_url="https://jira.company.com",
            email="test@example.com",
            api_token="token123",
            personal_access_token="pat_token123",
            username="testuser",
            password="testpass",
            sso_session_cookie="JSESSIONID=abc123",
        )

        manager = self.create_manager_with_all_handlers(config)
        available = manager.get_available_auth_types()

        # All auth types should be available
        assert JiraAuthType.API_TOKEN in available
        assert JiraAuthType.PERSONAL_ACCESS_TOKEN in available
        assert JiraAuthType.BASIC in available
        assert JiraAuthType.SSO in available
        assert len(available) == 4

    def test_get_available_auth_types_partial(self):
        """Test getting available auth types with partial configuration."""
        # Test with only some auth methods configured
        config = JiraConfig(
            base_url="https://jira.company.com",
            personal_access_token="pat_token123",
            username="testuser",
            # Missing password, api_token, email, sso config
        )

        manager = self.create_manager_with_all_handlers(config)
        available = manager.get_available_auth_types()

        # Only PAT should be available (basic needs both username AND password)
        assert JiraAuthType.PERSONAL_ACCESS_TOKEN in available
        assert JiraAuthType.API_TOKEN not in available
        assert JiraAuthType.BASIC not in available
        assert JiraAuthType.SSO not in available
        assert len(available) == 1
