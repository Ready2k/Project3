"""Authentication management system for Jira integration."""

from abc import ABC, abstractmethod
from typing import Dict, Optional, Any
from pydantic import BaseModel

from app.config import JiraAuthType


class AuthResult(BaseModel):
    """Result of an authentication attempt."""
    success: bool
    auth_type: JiraAuthType
    headers: Dict[str, str]
    error_message: Optional[str] = None
    requires_fallback: bool = False
    session_data: Optional[Dict[str, Any]] = None


class AuthenticationHandler(ABC):
    """Abstract base class for authentication handlers."""
    
    @abstractmethod
    async def authenticate(self, config: Any) -> AuthResult:
        """Attempt authentication with the given configuration.
        
        Args:
            config: Configuration object containing authentication details
            
        Returns:
            AuthResult indicating success/failure and authentication headers
        """
        raise NotImplementedError("Subclasses must implement authenticate method")
    
    @abstractmethod
    def get_auth_type(self) -> JiraAuthType:
        """Get the authentication type this handler supports.
        
        Returns:
            JiraAuthType enum value
        """
        raise NotImplementedError("Subclasses must implement get_auth_type method")
    
    @abstractmethod
    def validate_config(self, config: Any) -> bool:
        """Validate that the configuration contains required fields for this auth type.
        
        Args:
            config: Configuration object to validate
            
        Returns:
            True if configuration is valid for this auth type
        """
        raise NotImplementedError("Subclasses must implement validate_config method")


class AuthenticationManager:
    """Manages different authentication methods for Jira."""
    
    def __init__(self, config: Any):
        """Initialize authentication manager with configuration.
        
        Args:
            config: JiraConfig object containing authentication details
        """
        self.config = config
        self.handlers: Dict[JiraAuthType, AuthenticationHandler] = {}
        self._current_auth_result: Optional[AuthResult] = None
    
    def register_handler(self, handler: AuthenticationHandler) -> None:
        """Register an authentication handler.
        
        Args:
            handler: Authentication handler to register
        """
        auth_type = handler.get_auth_type()
        self.handlers[auth_type] = handler
    
    async def authenticate(self) -> AuthResult:
        """Attempt authentication with fallback chain.
        
        Returns:
            AuthResult with authentication details or error information
        """
        # Try the configured authentication type first
        if hasattr(self.config, 'auth_type') and self.config.auth_type in self.handlers:
            handler = self.handlers[self.config.auth_type]
            if handler.validate_config(self.config):
                result = await handler.authenticate(self.config)
                if result.success:
                    self._current_auth_result = result
                    return result
        
        # If primary auth fails or is invalid, try fallback chain
        fallback_order = [
            JiraAuthType.SSO,
            JiraAuthType.API_TOKEN,
            JiraAuthType.PERSONAL_ACCESS_TOKEN,
            JiraAuthType.BASIC
        ]
        
        for auth_type in fallback_order:
            if auth_type in self.handlers and auth_type != getattr(self.config, 'auth_type', None):
                handler = self.handlers[auth_type]
                if handler.validate_config(self.config):
                    result = await handler.authenticate(self.config)
                    if result.success:
                        self._current_auth_result = result
                        return result
        
        # If all authentication methods fail
        return AuthResult(
            success=False,
            auth_type=getattr(self.config, 'auth_type', JiraAuthType.API_TOKEN),
            headers={},
            error_message="All authentication methods failed",
            requires_fallback=True
        )
    
    async def get_auth_headers(self) -> Dict[str, str]:
        """Get authentication headers for API requests.
        
        Returns:
            Dictionary of HTTP headers for authentication
        """
        if self._current_auth_result and self._current_auth_result.success:
            return self._current_auth_result.headers
        
        # Try to authenticate if not already done
        result = await self.authenticate()
        if result.success:
            return result.headers
        
        return {}
    
    def get_current_auth_result(self) -> Optional[AuthResult]:
        """Get the current authentication result.
        
        Returns:
            Current AuthResult or None if not authenticated
        """
        return self._current_auth_result
    
    def clear_auth(self) -> None:
        """Clear current authentication state."""
        self._current_auth_result = None
    
    def is_authenticated(self) -> bool:
        """Check if currently authenticated.
        
        Returns:
            True if authenticated, False otherwise
        """
        return (self._current_auth_result is not None and 
                self._current_auth_result.success)
    
    def get_available_auth_types(self) -> list[JiraAuthType]:
        """Get list of available authentication types based on configuration.
        
        Returns:
            List of JiraAuthType values that can be used with current config
        """
        available = []
        for auth_type, handler in self.handlers.items():
            if handler.validate_config(self.config):
                available.append(auth_type)
        return available