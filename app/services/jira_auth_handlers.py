"""Concrete authentication handlers for Jira integration."""

import base64
from typing import Dict, Optional, Any

from app.services.jira_auth import AuthenticationHandler, AuthResult
from app.config import JiraAuthType, JiraConfig
from app.utils.logger import app_logger


class APITokenHandler(AuthenticationHandler):
    """Authentication handler for Jira API tokens (Cloud)."""
    
    def get_auth_type(self) -> JiraAuthType:
        """Get the authentication type this handler supports."""
        return JiraAuthType.API_TOKEN
    
    def validate_config(self, config: JiraConfig) -> bool:
        """Validate that the configuration contains required fields for API token auth.
        
        Args:
            config: JiraConfig object to validate
            
        Returns:
            True if configuration is valid for API token authentication
        """
        return (hasattr(config, 'email') and config.email is not None and
                hasattr(config, 'api_token') and config.api_token is not None)
    
    async def authenticate(self, config: JiraConfig) -> AuthResult:
        """Attempt API token authentication.
        
        Args:
            config: JiraConfig containing email and api_token
            
        Returns:
            AuthResult with authentication headers or error information
        """
        try:
            if not self.validate_config(config):
                return AuthResult(
                    success=False,
                    auth_type=self.get_auth_type(),
                    headers={},
                    error_message="API token authentication requires email and api_token"
                )
            
            # Create Basic Auth header with email:api_token
            auth_string = f"{config.email}:{config.api_token}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            app_logger.info(f"API token authentication configured for email: {config.email}")
            
            return AuthResult(
                success=True,
                auth_type=self.get_auth_type(),
                headers=headers,
                error_message=None
            )
            
        except Exception as e:
            app_logger.error(f"API token authentication failed: {e}")
            return AuthResult(
                success=False,
                auth_type=self.get_auth_type(),
                headers={},
                error_message=f"API token authentication error: {str(e)}"
            )


class PATHandler(AuthenticationHandler):
    """Authentication handler for Personal Access Tokens (Data Center)."""
    
    def get_auth_type(self) -> JiraAuthType:
        """Get the authentication type this handler supports."""
        return JiraAuthType.PERSONAL_ACCESS_TOKEN
    
    def validate_config(self, config: JiraConfig) -> bool:
        """Validate that the configuration contains required fields for PAT auth.
        
        Args:
            config: JiraConfig object to validate
            
        Returns:
            True if configuration is valid for PAT authentication
        """
        return (hasattr(config, 'personal_access_token') and 
                config.personal_access_token is not None)
    
    async def authenticate(self, config: JiraConfig) -> AuthResult:
        """Attempt Personal Access Token authentication.
        
        Args:
            config: JiraConfig containing personal_access_token
            
        Returns:
            AuthResult with authentication headers or error information
        """
        try:
            if not self.validate_config(config):
                return AuthResult(
                    success=False,
                    auth_type=self.get_auth_type(),
                    headers={},
                    error_message="PAT authentication requires personal_access_token"
                )
            
            # PAT uses Bearer token authentication
            headers = {
                "Authorization": f"Bearer {config.personal_access_token}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            app_logger.info("Personal Access Token authentication configured")
            
            return AuthResult(
                success=True,
                auth_type=self.get_auth_type(),
                headers=headers,
                error_message=None
            )
            
        except Exception as e:
            app_logger.error(f"PAT authentication failed: {e}")
            return AuthResult(
                success=False,
                auth_type=self.get_auth_type(),
                headers={},
                error_message=f"PAT authentication error: {str(e)}"
            )


class SSOAuthHandler(AuthenticationHandler):
    """Authentication handler for SSO/session-based authentication."""
    
    def get_auth_type(self) -> JiraAuthType:
        """Get the authentication type this handler supports."""
        return JiraAuthType.SSO
    
    def validate_config(self, config: JiraConfig) -> bool:
        """Validate that the configuration supports SSO authentication.
        
        Args:
            config: JiraConfig object to validate
            
        Returns:
            True if configuration supports SSO authentication
        """
        # SSO can work with just use_sso=True, or with existing session cookie
        return (hasattr(config, 'use_sso') and config.use_sso is True) or \
               (hasattr(config, 'sso_session_cookie') and config.sso_session_cookie is not None)
    
    async def authenticate(self, config: JiraConfig) -> AuthResult:
        """Attempt SSO authentication.
        
        Args:
            config: JiraConfig with SSO configuration
            
        Returns:
            AuthResult with authentication headers or error information
        """
        try:
            if not self.validate_config(config):
                return AuthResult(
                    success=False,
                    auth_type=self.get_auth_type(),
                    headers={},
                    error_message="SSO authentication requires use_sso=True or existing session cookie"
                )
            
            headers = {
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            session_data = {}
            
            # If we have an existing session cookie, use it
            if hasattr(config, 'sso_session_cookie') and config.sso_session_cookie:
                headers["Cookie"] = config.sso_session_cookie
                session_data["session_cookie"] = config.sso_session_cookie
                app_logger.info("SSO authentication using existing session cookie")
            else:
                # For now, we'll attempt to detect current session
                # This would be enhanced in a real implementation to detect browser sessions
                app_logger.info("SSO authentication configured - session detection not yet implemented")
                
                # Return failure for now since we don't have session detection implemented
                return AuthResult(
                    success=False,
                    auth_type=self.get_auth_type(),
                    headers={},
                    error_message="SSO session detection not yet implemented",
                    requires_fallback=True
                )
            
            return AuthResult(
                success=True,
                auth_type=self.get_auth_type(),
                headers=headers,
                session_data=session_data,
                error_message=None
            )
            
        except Exception as e:
            app_logger.error(f"SSO authentication failed: {e}")
            return AuthResult(
                success=False,
                auth_type=self.get_auth_type(),
                headers={},
                error_message=f"SSO authentication error: {str(e)}",
                requires_fallback=True
            )


class BasicAuthHandler(AuthenticationHandler):
    """Authentication handler for basic username/password authentication."""
    
    def get_auth_type(self) -> JiraAuthType:
        """Get the authentication type this handler supports."""
        return JiraAuthType.BASIC
    
    def validate_config(self, config: JiraConfig) -> bool:
        """Validate that the configuration contains required fields for basic auth.
        
        Args:
            config: JiraConfig object to validate
            
        Returns:
            True if configuration is valid for basic authentication
        """
        return (hasattr(config, 'username') and config.username is not None and
                hasattr(config, 'password') and config.password is not None)
    
    async def authenticate(self, config: JiraConfig) -> AuthResult:
        """Attempt basic authentication.
        
        Args:
            config: JiraConfig containing username and password
            
        Returns:
            AuthResult with authentication headers or error information
        """
        try:
            if not self.validate_config(config):
                return AuthResult(
                    success=False,
                    auth_type=self.get_auth_type(),
                    headers={},
                    error_message="Basic authentication requires username and password",
                    requires_fallback=True
                )
            
            # Create Basic Auth header with username:password
            auth_string = f"{config.username}:{config.password}"
            auth_bytes = auth_string.encode('ascii')
            auth_b64 = base64.b64encode(auth_bytes).decode('ascii')
            
            headers = {
                "Authorization": f"Basic {auth_b64}",
                "Accept": "application/json",
                "Content-Type": "application/json"
            }
            
            app_logger.info(f"Basic authentication configured for username: {config.username}")
            
            return AuthResult(
                success=True,
                auth_type=self.get_auth_type(),
                headers=headers,
                error_message=None
            )
            
        except Exception as e:
            app_logger.error(f"Basic authentication failed: {e}")
            return AuthResult(
                success=False,
                auth_type=self.get_auth_type(),
                headers={},
                error_message=f"Basic authentication error: {str(e)}",
                requires_fallback=True
            )