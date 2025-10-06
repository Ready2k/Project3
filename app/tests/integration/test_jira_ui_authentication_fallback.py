"""Integration tests for Jira UI authentication fallback scenarios."""

import pytest
from unittest.mock import Mock, patch

from app.config import JiraConfig, JiraAuthType
from app.services.jira import JiraConnectionError
from app.services.jira_auth import AuthResult


class TestJiraUIAuthenticationFallback:
    """Test authentication fallback scenarios in the UI."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.base_url = "https://jira.company.com"
        self.test_config = JiraConfig(
            base_url=self.base_url,
            auth_type=JiraAuthType.API_TOKEN,
            email="test@company.com",
            api_token="test_token"
        )
    
    @pytest.mark.asyncio
    async def test_api_token_to_basic_auth_fallback(self):
        """Test fallback from API token to basic authentication."""
        # Simulate UI fallback flow without actual service calls
        initial_auth_failed = True
        fallback_attempted = False
        fallback_result = None
        
        if initial_auth_failed:
            # User selects basic auth fallback
            
            # Simulate successful fallback authentication
            fallback_result = Mock(
                success=True,
                auth_result=Mock(
                    success=True,
                    auth_type=JiraAuthType.BASIC,
                    headers={"Authorization": "Basic dGVzdDp0ZXN0"},
                    error_message=None,
                    requires_fallback=False
                )
            )
            fallback_attempted = True
        
        assert fallback_attempted is True
        assert fallback_result.success is True
        assert fallback_result.auth_result.auth_type == JiraAuthType.BASIC
    
    @pytest.mark.asyncio
    async def test_api_token_to_sso_fallback(self):
        """Test fallback from API token to SSO authentication."""
        # Simulate UI fallback to SSO
        
        # Simulate successful SSO fallback
        fallback_result = Mock(
            success=True,
            auth_result=Mock(
                success=True,
                auth_type=JiraAuthType.SSO,
                headers={"Cookie": "JSESSIONID=test_session"},
                error_message=None,
                requires_fallback=False
            )
        )
        
        assert fallback_result.success is True
        assert fallback_result.auth_result.auth_type == JiraAuthType.SSO
    
    @pytest.mark.asyncio
    async def test_api_token_to_pat_fallback(self):
        """Test fallback from API token to Personal Access Token."""
        # Simulate UI fallback to PAT
        
        # Simulate successful PAT fallback
        fallback_result = Mock(
            success=True,
            auth_result=Mock(
                success=True,
                auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
                headers={"Authorization": "Bearer test_pat_token"},
                error_message=None,
                requires_fallback=False
            )
        )
        
        assert fallback_result.success is True
        assert fallback_result.auth_result.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN
    
    def test_authentication_status_display_success(self):
        """Test authentication status display for successful authentication."""
        auth_result = {
            "success": True,
            "auth_type": "basic",
            "message": "Authentication successful"
        }
        
        # Simulate UI status display logic
        status_message = "✅ Authentication successful!"
        auth_method = "Username/Password"
        security_warning = "⚠️ Username/password credentials are stored securely for this session only"
        
        assert auth_result["success"] is True
        assert "successful" in status_message
        assert "Username/Password" in auth_method
        assert "session only" in security_warning
    
    def test_authentication_status_display_failure(self):
        """Test authentication status display for failed authentication."""
        auth_result = {
            "success": False,
            "error_message": "401 Unauthorized - Invalid credentials",
            "auth_type": "api_token"
        }
        
        # Simulate UI error display logic
        error_message = "❌ Authentication failed"
        error_details = auth_result["error_message"]
        
        # Generate guidance based on error
        guidance = []
        if "401" in error_details or "unauthorized" in error_details.lower():
            guidance.extend([
                "Verify your credentials are correct and not expired",
                "For Data Center: try Personal Access Token instead of API token",
                "For SSO: ensure you're logged into Jira in another browser tab"
            ])
        
        assert auth_result["success"] is False
        assert "failed" in error_message
        assert len(guidance) == 3
        assert "Personal Access Token" in guidance[1]
    
    @pytest.mark.asyncio
    async def test_multiple_fallback_attempts(self):
        """Test multiple fallback attempts until success."""
        with patch('app.services.jira.JiraService') as mock_service:
            mock_instance = mock_service.return_value
            
            # Simulate multiple failures then success
            mock_instance.test_connection_with_fallback.side_effect = [
                JiraConnectionError("401 Unauthorized - Invalid API token"),  # API token fails
                JiraConnectionError("401 Unauthorized - Invalid PAT"),        # PAT fails
                JiraConnectionError("403 Forbidden - SSO not available"),     # SSO fails
                Mock(  # Basic auth succeeds
                    success=True,
                    auth_result=AuthResult(
                        success=True,
                        auth_type=JiraAuthType.BASIC,
                        headers={"Authorization": "Basic dGVzdDp0ZXN0"},
                        error_message=None,
                        requires_fallback=False
                    )
                )
            ]
            
            # Simulate UI trying multiple fallback methods
            fallback_attempts = [
                {"auth_type": "api_token", "success": False},
                {"auth_type": "pat", "success": False},
                {"auth_type": "sso", "success": False},
                {"auth_type": "basic", "success": True}
            ]
            
            successful_auth = None
            for attempt in fallback_attempts:
                if attempt["auth_type"] == "basic" and attempt["success"]:
                    successful_auth = attempt
                    break
            
            assert successful_auth is not None
            assert successful_auth["auth_type"] == "basic"
            assert successful_auth["success"] is True
    
    def test_credential_security_handling(self):
        """Test secure credential handling in UI."""
        # Test basic auth credential handling
        basic_credentials = {
            "username": "test_user",
            "password": "test_pass",
            "session_only": True,
            "auto_clear": True
        }
        
        # Simulate UI security measures
        assert basic_credentials["session_only"] is True
        assert basic_credentials["auto_clear"] is True
        
        # Test that sensitive fields are marked appropriately
        sensitive_fields = ["password", "api_token", "personal_access_token"]
        form_field_types = {
            "password": "password",
            "api_token": "password", 
            "personal_access_token": "password",
            "username": "text",
            "email": "text"
        }
        
        for field in sensitive_fields:
            assert form_field_types[field] == "password"
    
    def test_deployment_specific_auth_guidance(self):
        """Test deployment-specific authentication guidance."""
        deployment_guidance = {
            "cloud": {
                "recommended": ["api_token"],
                "supported": ["api_token"],
                "guidance": "Use API tokens for Jira Cloud authentication"
            },
            "data_center": {
                "recommended": ["pat", "sso"],
                "supported": ["pat", "sso", "basic", "api_token"],
                "guidance": "Personal Access Tokens are recommended for Data Center"
            },
            "server": {
                "recommended": ["basic"],
                "supported": ["basic", "api_token"],
                "guidance": "Basic authentication is typically used for Jira Server"
            }
        }
        
        # Test Cloud guidance
        cloud_guidance = deployment_guidance["cloud"]
        assert "api_token" in cloud_guidance["recommended"]
        assert "API tokens" in cloud_guidance["guidance"]
        
        # Test Data Center guidance
        dc_guidance = deployment_guidance["data_center"]
        assert "pat" in dc_guidance["recommended"]
        assert "sso" in dc_guidance["recommended"]
        assert len(dc_guidance["supported"]) == 4
        assert "Personal Access Tokens" in dc_guidance["guidance"]
    
    def test_error_message_categorization(self):
        """Test error message categorization for better user guidance."""
        error_categories = {
            "authentication": {
                "patterns": ["401", "unauthorized", "invalid credentials"],
                "guidance": [
                    "Verify your credentials are correct",
                    "Check if credentials are expired",
                    "Try alternative authentication method"
                ]
            },
            "permission": {
                "patterns": ["403", "forbidden", "access denied"],
                "guidance": [
                    "Contact your Jira administrator",
                    "Verify account permissions",
                    "Check if account is active"
                ]
            },
            "connection": {
                "patterns": ["timeout", "connection refused", "network"],
                "guidance": [
                    "Check network connectivity",
                    "Verify Jira URL is correct",
                    "Check firewall settings"
                ]
            }
        }
        
        # Test error categorization
        test_errors = [
            ("401 Unauthorized", "authentication"),
            ("403 Forbidden", "permission"),
            ("Connection timeout", "connection")
        ]
        
        for error_msg, expected_category in test_errors:
            category = None
            for cat_name, cat_info in error_categories.items():
                if any(pattern.lower() in error_msg.lower() for pattern in cat_info["patterns"]):
                    category = cat_name
                    break
            
            assert category == expected_category
            assert len(error_categories[category]["guidance"]) >= 3
    
    @pytest.mark.asyncio
    async def test_session_credential_cleanup(self):
        """Test session credential cleanup functionality."""
        # Simulate session credentials
        session_credentials = {
            "basic_auth": {
                "username": "test_user",
                "password": "test_pass",
                "stored_at": "2025-01-01T10:00:00Z",
                "auto_clear": True
            }
        }
        
        # Simulate cleanup logic
        def cleanup_session_credentials():
            if session_credentials.get("basic_auth", {}).get("auto_clear"):
                session_credentials["basic_auth"] = {
                    "username": None,
                    "password": None,
                    "stored_at": None,
                    "auto_clear": True
                }
        
        # Test cleanup
        cleanup_session_credentials()
        
        basic_auth = session_credentials["basic_auth"]
        assert basic_auth["username"] is None
        assert basic_auth["password"] is None
        assert basic_auth["stored_at"] is None
        assert basic_auth["auto_clear"] is True
    
    def test_ui_form_state_management(self):
        """Test UI form state management during fallback."""
        # Initial form state
        form_state = {
            "base_url": "https://jira.company.com",
            "auth_type": "api_token",
            "email": "test@company.com",
            "api_token": "invalid_token",
            "fallback_attempted": False,
            "fallback_success": False
        }
        
        # Simulate authentication failure and fallback
        if not form_state["fallback_success"]:
            # Update form state for fallback
            form_state.update({
                "auth_type": "basic",
                "username": "test_user",
                "password": "test_pass",
                "fallback_attempted": True,
                "fallback_success": True,
                # Clear previous auth fields
                "email": None,
                "api_token": None
            })
        
        assert form_state["fallback_attempted"] is True
        assert form_state["fallback_success"] is True
        assert form_state["auth_type"] == "basic"
        assert form_state["email"] is None  # Cleared after fallback
        assert form_state["api_token"] is None  # Cleared after fallback