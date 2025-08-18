"""Unit tests for base Jira authentication components."""

import pytest
from unittest.mock import Mock, AsyncMock
from typing import Dict, Any

from app.services.jira_auth import (
    AuthResult, 
    AuthenticationHandler, 
    AuthenticationManager
)
from app.config import JiraAuthType, JiraConfig


class MockAuthHandler(AuthenticationHandler):
    """Mock authentication handler for testing."""
    
    def __init__(self, auth_type: JiraAuthType, should_succeed: bool = True, 
                 requires_config_fields: list[str] = None):
        self.auth_type = auth_type
        self.should_succeed = should_succeed
        self.required_fields = requires_config_fields or []
        self.authenticate_called = False
        self.validate_config_called = False
    
    async def authenticate(self, config: Any) -> AuthResult:
        """Mock authenticate method."""
        self.authenticate_called = True
        
        if self.should_succeed:
            return AuthResult(
                success=True,
                auth_type=self.auth_type,
                headers={"Authorization": f"Mock {self.auth_type.value}"},
                error_message=None
            )
        else:
            return AuthResult(
                success=False,
                auth_type=self.auth_type,
                headers={},
                error_message=f"Mock {self.auth_type.value} authentication failed"
            )
    
    def get_auth_type(self) -> JiraAuthType:
        """Get the authentication type."""
        return self.auth_type
    
    def validate_config(self, config: Any) -> bool:
        """Mock validate config method."""
        self.validate_config_called = True
        
        # Check if all required fields are present and not None
        for field in self.required_fields:
            if not hasattr(config, field) or getattr(config, field) is None:
                return False
        return True


class TestAuthResult:
    """Test cases for AuthResult model."""
    
    def test_auth_result_success(self):
        """Test successful authentication result."""
        result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Bearer token123"},
            error_message=None
        )
        
        assert result.success is True
        assert result.auth_type == JiraAuthType.API_TOKEN
        assert result.headers == {"Authorization": "Bearer token123"}
        assert result.error_message is None
        assert result.requires_fallback is False
        assert result.session_data is None
    
    def test_auth_result_failure(self):
        """Test failed authentication result."""
        result = AuthResult(
            success=False,
            auth_type=JiraAuthType.BASIC,
            headers={},
            error_message="Invalid credentials",
            requires_fallback=True
        )
        
        assert result.success is False
        assert result.auth_type == JiraAuthType.BASIC
        assert result.headers == {}
        assert result.error_message == "Invalid credentials"
        assert result.requires_fallback is True
    
    def test_auth_result_with_session_data(self):
        """Test authentication result with session data."""
        session_data = {"session_id": "abc123", "expires": "2024-12-31"}
        result = AuthResult(
            success=True,
            auth_type=JiraAuthType.SSO,
            headers={"Cookie": "JSESSIONID=abc123"},
            session_data=session_data
        )
        
        assert result.success is True
        assert result.session_data == session_data


class TestAuthenticationHandler:
    """Test cases for AuthenticationHandler abstract base class."""
    
    def test_abstract_methods_raise_not_implemented(self):
        """Test that abstract methods raise NotImplementedError."""
        # Can't instantiate abstract class directly, so test with a concrete implementation
        # that doesn't override the abstract methods
        
        class IncompleteHandler(AuthenticationHandler):
            pass
        
        with pytest.raises(TypeError):
            IncompleteHandler()


class TestAuthenticationManager:
    """Test cases for AuthenticationManager."""
    
    def test_init(self):
        """Test AuthenticationManager initialization."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        assert manager.config == config
        assert manager.handlers == {}
        assert manager._current_auth_result is None
    
    def test_register_handler(self):
        """Test registering authentication handlers."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        handler = MockAuthHandler(JiraAuthType.API_TOKEN)
        manager.register_handler(handler)
        
        assert JiraAuthType.API_TOKEN in manager.handlers
        assert manager.handlers[JiraAuthType.API_TOKEN] == handler
    
    def test_register_multiple_handlers(self):
        """Test registering multiple authentication handlers."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        api_handler = MockAuthHandler(JiraAuthType.API_TOKEN)
        sso_handler = MockAuthHandler(JiraAuthType.SSO)
        
        manager.register_handler(api_handler)
        manager.register_handler(sso_handler)
        
        assert len(manager.handlers) == 2
        assert manager.handlers[JiraAuthType.API_TOKEN] == api_handler
        assert manager.handlers[JiraAuthType.SSO] == sso_handler
    
    @pytest.mark.asyncio
    async def test_authenticate_success_with_configured_type(self):
        """Test successful authentication with configured auth type."""
        config = Mock()
        config.auth_type = JiraAuthType.API_TOKEN
        
        manager = AuthenticationManager(config)
        handler = MockAuthHandler(JiraAuthType.API_TOKEN, should_succeed=True)
        manager.register_handler(handler)
        
        result = await manager.authenticate()
        
        assert result.success is True
        assert result.auth_type == JiraAuthType.API_TOKEN
        assert handler.authenticate_called is True
        assert handler.validate_config_called is True
        assert manager._current_auth_result == result
    
    @pytest.mark.asyncio
    async def test_authenticate_fallback_on_primary_failure(self):
        """Test authentication fallback when primary method fails."""
        config = Mock()
        config.auth_type = JiraAuthType.API_TOKEN
        
        manager = AuthenticationManager(config)
        
        # Primary handler fails
        primary_handler = MockAuthHandler(JiraAuthType.API_TOKEN, should_succeed=False)
        # Fallback handler succeeds
        fallback_handler = MockAuthHandler(JiraAuthType.SSO, should_succeed=True)
        
        manager.register_handler(primary_handler)
        manager.register_handler(fallback_handler)
        
        result = await manager.authenticate()
        
        assert result.success is True
        assert result.auth_type == JiraAuthType.SSO
        assert primary_handler.authenticate_called is True
        assert fallback_handler.authenticate_called is True
    
    @pytest.mark.asyncio
    async def test_authenticate_all_methods_fail(self):
        """Test authentication when all methods fail."""
        config = Mock()
        config.auth_type = JiraAuthType.API_TOKEN
        
        manager = AuthenticationManager(config)
        
        # All handlers fail
        api_handler = MockAuthHandler(JiraAuthType.API_TOKEN, should_succeed=False)
        sso_handler = MockAuthHandler(JiraAuthType.SSO, should_succeed=False)
        
        manager.register_handler(api_handler)
        manager.register_handler(sso_handler)
        
        result = await manager.authenticate()
        
        assert result.success is False
        assert result.error_message == "All authentication methods failed"
        assert result.requires_fallback is True
    
    @pytest.mark.asyncio
    async def test_authenticate_skips_invalid_config(self):
        """Test authentication skips handlers with invalid config."""
        # Use a simple object instead of Mock to avoid hasattr issues
        class TestConfig:
            def __init__(self):
                self.auth_type = JiraAuthType.API_TOKEN
                # Don't set api_token attribute, so validation should fail
        
        config = TestConfig()
        manager = AuthenticationManager(config)
        
        # Handler with invalid config (requires 'api_token' field)
        invalid_handler = MockAuthHandler(
            JiraAuthType.API_TOKEN, 
            should_succeed=True,
            requires_config_fields=['api_token']
        )
        # Valid fallback handler (no required fields)
        valid_handler = MockAuthHandler(JiraAuthType.SSO, should_succeed=True)
        
        manager.register_handler(invalid_handler)
        manager.register_handler(valid_handler)
        
        # Test that invalid handler validation fails
        assert invalid_handler.validate_config(config) is False
        assert valid_handler.validate_config(config) is True
        
        result = await manager.authenticate()
        
        assert result.success is True
        assert result.auth_type == JiraAuthType.SSO
        assert invalid_handler.authenticate_called is False  # Skipped due to invalid config
        assert valid_handler.authenticate_called is True
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_with_existing_auth(self):
        """Test getting auth headers when already authenticated."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        # Set up existing auth result
        auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Bearer token123"}
        )
        manager._current_auth_result = auth_result
        
        headers = await manager.get_auth_headers()
        
        assert headers == {"Authorization": "Bearer token123"}
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_triggers_authentication(self):
        """Test getting auth headers triggers authentication if not already done."""
        config = Mock()
        config.auth_type = JiraAuthType.API_TOKEN
        
        manager = AuthenticationManager(config)
        handler = MockAuthHandler(JiraAuthType.API_TOKEN, should_succeed=True)
        manager.register_handler(handler)
        
        headers = await manager.get_auth_headers()
        
        assert headers == {"Authorization": "Mock api_token"}
        assert handler.authenticate_called is True
    
    @pytest.mark.asyncio
    async def test_get_auth_headers_returns_empty_on_auth_failure(self):
        """Test getting auth headers returns empty dict when auth fails."""
        config = Mock()
        config.auth_type = JiraAuthType.API_TOKEN
        
        manager = AuthenticationManager(config)
        handler = MockAuthHandler(JiraAuthType.API_TOKEN, should_succeed=False)
        manager.register_handler(handler)
        
        headers = await manager.get_auth_headers()
        
        assert headers == {}
    
    def test_get_current_auth_result(self):
        """Test getting current authentication result."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        # Initially None
        assert manager.get_current_auth_result() is None
        
        # After setting result
        auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Bearer token123"}
        )
        manager._current_auth_result = auth_result
        
        assert manager.get_current_auth_result() == auth_result
    
    def test_clear_auth(self):
        """Test clearing authentication state."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        # Set up auth result
        auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Bearer token123"}
        )
        manager._current_auth_result = auth_result
        
        # Clear auth
        manager.clear_auth()
        
        assert manager._current_auth_result is None
    
    def test_is_authenticated(self):
        """Test checking authentication status."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        # Initially not authenticated
        assert manager.is_authenticated() is False
        
        # After successful auth
        auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Bearer token123"}
        )
        manager._current_auth_result = auth_result
        assert manager.is_authenticated() is True
        
        # After failed auth
        failed_result = AuthResult(
            success=False,
            auth_type=JiraAuthType.API_TOKEN,
            headers={},
            error_message="Auth failed"
        )
        manager._current_auth_result = failed_result
        assert manager.is_authenticated() is False
    
    def test_get_available_auth_types(self):
        """Test getting available authentication types."""
        # Use a simple object instead of Mock to avoid hasattr issues
        class TestConfig:
            def __init__(self):
                self.api_token = "token123"  # Only API token is configured
                # Don't set username or password
        
        config = TestConfig()
        manager = AuthenticationManager(config)
        
        # Handler that requires api_token (should be available)
        api_handler = MockAuthHandler(
            JiraAuthType.API_TOKEN,
            requires_config_fields=['api_token']
        )
        # Handler that requires username (should not be available)
        basic_handler = MockAuthHandler(
            JiraAuthType.BASIC,
            requires_config_fields=['username', 'password']
        )
        
        manager.register_handler(api_handler)
        manager.register_handler(basic_handler)
        
        available = manager.get_available_auth_types()
        
        assert JiraAuthType.API_TOKEN in available
        assert JiraAuthType.BASIC not in available
        assert len(available) == 1
    
    def test_get_available_auth_types_empty_when_no_handlers(self):
        """Test getting available auth types when no handlers registered."""
        config = Mock()
        manager = AuthenticationManager(config)
        
        available = manager.get_available_auth_types()
        
        assert available == []