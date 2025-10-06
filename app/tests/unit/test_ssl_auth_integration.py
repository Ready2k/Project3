"""Tests for SSL verification behavior with different authentication methods.

This module tests that SSL configuration works consistently across all
authentication methods supported by the JIRA integration.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import base64

from app.services.jira import JiraService, JiraConfig
from app.config import JiraAuthType
from app.services.jira_auth_handlers import APITokenHandler, PATHandler, BasicAuthHandler


# Sample valid certificate for testing
SAMPLE_CERT_PEM = """-----BEGIN CERTIFICATE-----
MIIDXTCCAkWgAwIBAgIJAKoK/heBjcOuMA0GCSqGSIb3DQEBBQUAMEUxCzAJBgNV
BAYTAkFVMRMwEQYDVQQIDApTb21lLVN0YXRlMSEwHwYDVQQKDBhJbnRlcm5ldCBX
aWRnaXRzIFB0eSBMdGQwHhcNMTIwOTEyMjE1MjAyWhcNMTUwOTEyMjE1MjAyWjBF
MQswCQYDVQQGEwJBVTETMBEGA1UECAwKU29tZS1TdGF0ZTEhMB8GA1UECgwYSW50
ZXJuZXQgV2lkZ2l0cyBQdHkgTHRkMIIBIjANBgkqhkiG9w0BAQEFAAOCAQ8AMIIB
CgKCAQEAwuqTiuGqAXGHYAg220aoIwNiI8QS4dqCM2qzAI7VwplBNJ8rKyN0rsdK
03o1GONSuGDiTANiUS8Q+2M6oa6NnZUCgfwxgHQekfmHqHdJ3z8d5JEVoGQpQtpd
MpGOeE5Y2q7HjFvksxhGMzJtsaZuYWFkcmduS4xQjALHBhrxtsBhw1n5Ks+x6/a+
U6GQryuA5w9MzXccMlPS9f9sEAMlw1Yqkn+10TkjpBOHjxmAHeTRkN/lIgVvqV1H
VUzXXFc2VsqaXdM5eSllrzrgbNTemLt3i8v5aRIKOfIpRY7Oe0h6I0/lbB1QYVY0
/UIRu61M7VsSOdKHgDGGHZ+4wdtCkwIDAQABo1AwTjAdBgNVHQ4EFgQUZRrHA5Zp
nVJK3s03j2+rmUOHuIcwHwYDVR0jBBgwFoAUZRrHA5ZpnVJK3s03j2+rmUOHuIcw
DAYDVR0TBAUwAwEB/zANBgkqhkiG9w0BAQUFAAOCAQEAWjsHVQQqm5CE6Ro7k6id
qly1nassqqodjIww/E/jIa3+3VcfCQPMoraBWm+TywzJ3aa0K2s4j6iwrXxmjW3s
3IKhRlycWAQHHe+YzRNWcIEtw16LuO4OBqxhxtqz4z4O5lnqoKB0S2fKmjloX0XU
ClcVMYgBBVqxSGbX8SHg7A+WjJ7dLaNu3fIOqBjV9fcEo10A2UOKqxprRaV9C/x/
LQ1gE4DEPxIRpfDfnq5+6RK6XJXjNQbI/xqpvc0Q0F0SMe1BGdBF2MfyRmlBXCM9
hMvBjEnLiHbhiQ5uFkk2oCsVnVniaM6b8vMM8RfcZx9jN7DbRvtb6Fl6zeqXEq+3
+A==
-----END CERTIFICATE-----"""


class TestSSLWithUsernamePasswordAuth:
    """Test SSL verification with username/password authentication."""
    
    def test_ssl_enabled_with_username_password_auth(self):
        """Test SSL verification enabled with username/password authentication."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            username="testuser",
            password="testpass",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL configuration is properly set
        assert jira_service.ssl_handler.verify_ssl is True
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is True
        
        # Verify all components have consistent SSL configuration
        assert jira_service.deployment_detector.verify_ssl is True
        assert jira_service.api_version_manager.verify_ssl is True
    
    def test_ssl_disabled_with_username_password_auth(self):
        """Test SSL verification disabled with username/password authentication."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            username="testuser",
            password="testpass",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL configuration is properly set
        assert jira_service.ssl_handler.verify_ssl is False
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is False
        
        # Verify all components have consistent SSL configuration
        assert jira_service.deployment_detector.verify_ssl is False
        assert jira_service.api_version_manager.verify_ssl is False
    
    def test_ssl_with_custom_ca_and_username_password_auth(self):
        """Test SSL verification with custom CA and username/password authentication."""
        # Create a temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            ca_cert_path = f.name
        
        try:
            config = JiraConfig(
                base_url="https://jira.example.com",
                username="testuser",
                password="testpass",
                verify_ssl=True,
                ca_cert_path=ca_cert_path
            )
            
            jira_service = JiraService(config)
            
            # Verify SSL configuration is properly set
            assert jira_service.ssl_handler.verify_ssl is True
            assert jira_service.ssl_handler.ca_cert_path == ca_cert_path
            
            # Verify SSL handler returns correct httpx configuration
            verify_config = jira_service.ssl_handler.get_httpx_verify_config()
            assert verify_config == ca_cert_path
            
            # Verify all components have consistent SSL configuration
            assert jira_service.deployment_detector.verify_ssl is True
            assert jira_service.deployment_detector.ca_cert_path == ca_cert_path
            assert jira_service.api_version_manager.verify_ssl is True
            assert jira_service.api_version_manager.ca_cert_path == ca_cert_path
        finally:
            # Clean up temporary file
            Path(ca_cert_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_basic_auth_handler_with_ssl_configuration(self):
        """Test that BasicAuthHandler works with SSL configuration."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            username="testuser",
            password="testpass",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        handler = BasicAuthHandler()
        
        # Verify handler validates config correctly
        assert handler.validate_config(config) is True
        assert handler.get_auth_type() == JiraAuthType.BASIC
        
        # Test authentication
        auth_result = await handler.authenticate(config)
        
        assert auth_result.success is True
        assert auth_result.auth_type == JiraAuthType.BASIC
        assert "Authorization" in auth_result.headers
        
        # Verify Basic Auth header is correctly formatted
        auth_header = auth_result.headers["Authorization"]
        assert auth_header.startswith("Basic ")
        
        # Decode and verify credentials
        encoded_creds = auth_header.split(" ")[1]
        decoded_creds = base64.b64decode(encoded_creds).decode('ascii')
        assert decoded_creds == "testuser:testpass"


class TestSSLWithAPITokenAuth:
    """Test SSL verification with API token authentication."""
    
    def test_ssl_enabled_with_api_token_auth(self):
        """Test SSL verification enabled with API token authentication."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-api-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL configuration is properly set
        assert jira_service.ssl_handler.verify_ssl is True
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is True
        
        # Verify all components have consistent SSL configuration
        assert jira_service.deployment_detector.verify_ssl is True
        assert jira_service.api_version_manager.verify_ssl is True
    
    def test_ssl_disabled_with_api_token_auth(self):
        """Test SSL verification disabled with API token authentication."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-api-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL configuration is properly set
        assert jira_service.ssl_handler.verify_ssl is False
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is False
        
        # Verify all components have consistent SSL configuration
        assert jira_service.deployment_detector.verify_ssl is False
        assert jira_service.api_version_manager.verify_ssl is False
    
    @pytest.mark.asyncio
    async def test_api_token_handler_with_ssl_configuration(self):
        """Test that APITokenHandler works with SSL configuration."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-api-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        handler = APITokenHandler()
        
        # Verify handler validates config correctly
        assert handler.validate_config(config) is True
        assert handler.get_auth_type() == JiraAuthType.API_TOKEN
        
        # Test authentication
        auth_result = await handler.authenticate(config)
        
        assert auth_result.success is True
        assert auth_result.auth_type == JiraAuthType.API_TOKEN
        assert "Authorization" in auth_result.headers
        
        # Verify Basic Auth header is correctly formatted for API token
        auth_header = auth_result.headers["Authorization"]
        assert auth_header.startswith("Basic ")
        
        # Decode and verify credentials (email:api_token)
        encoded_creds = auth_header.split(" ")[1]
        decoded_creds = base64.b64decode(encoded_creds).decode('ascii')
        assert decoded_creds == "test@example.com:test-api-token"


class TestSSLWithPATAuth:
    """Test SSL verification with Personal Access Token authentication."""
    
    def test_ssl_enabled_with_pat_auth(self):
        """Test SSL verification enabled with PAT authentication."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            personal_access_token="test-pat-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL configuration is properly set
        assert jira_service.ssl_handler.verify_ssl is True
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is True
        
        # Verify all components have consistent SSL configuration
        assert jira_service.deployment_detector.verify_ssl is True
        assert jira_service.api_version_manager.verify_ssl is True
    
    def test_ssl_disabled_with_pat_auth(self):
        """Test SSL verification disabled with PAT authentication."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            personal_access_token="test-pat-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL configuration is properly set
        assert jira_service.ssl_handler.verify_ssl is False
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is False
        
        # Verify all components have consistent SSL configuration
        assert jira_service.deployment_detector.verify_ssl is False
        assert jira_service.api_version_manager.verify_ssl is False
    
    @pytest.mark.asyncio
    async def test_pat_handler_with_ssl_configuration(self):
        """Test that PATHandler works with SSL configuration."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            personal_access_token="test-pat-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        handler = PATHandler()
        
        # Verify handler validates config correctly
        assert handler.validate_config(config) is True
        assert handler.get_auth_type() == JiraAuthType.PERSONAL_ACCESS_TOKEN
        
        # Test authentication
        auth_result = await handler.authenticate(config)
        
        assert auth_result.success is True
        assert auth_result.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert "Authorization" in auth_result.headers
        
        # Verify Bearer token header is correctly formatted
        auth_header = auth_result.headers["Authorization"]
        assert auth_header == "Bearer test-pat-token"


class TestSSLConsistencyAcrossAuthMethods:
    """Test that SSL configuration is consistent across all authentication methods."""
    
    def test_ssl_consistency_across_all_auth_methods(self):
        """Test that SSL configuration is consistent regardless of authentication method."""
        base_ssl_config = {
            "base_url": "https://jira.example.com",
            "verify_ssl": False,
            "ca_cert_path": "/path/to/cert.pem"
        }
        
        # Test with username/password auth
        config_basic = JiraConfig(
            username="testuser",
            password="testpass",
            **base_ssl_config
        )
        jira_basic = JiraService(config_basic)
        
        # Test with API token auth
        config_api = JiraConfig(
            email="test@example.com",
            api_token="test-token",
            **base_ssl_config
        )
        jira_api = JiraService(config_api)
        
        # Test with PAT auth
        config_pat = JiraConfig(
            personal_access_token="test-pat",
            **base_ssl_config
        )
        jira_pat = JiraService(config_pat)
        
        # All services should have identical SSL configuration
        services = [jira_basic, jira_api, jira_pat]
        
        for service in services:
            assert service.ssl_handler.verify_ssl is False
            assert service.ssl_handler.ca_cert_path == "/path/to/cert.pem"
            assert service.deployment_detector.verify_ssl is False
            assert service.deployment_detector.ca_cert_path == "/path/to/cert.pem"
            assert service.api_version_manager.verify_ssl is False
            assert service.api_version_manager.ca_cert_path == "/path/to/cert.pem"
            
            # All should return the same verify config
            verify_config = service.ssl_handler.get_httpx_verify_config()
            assert verify_config is False
    
    def test_ssl_security_warnings_consistent_across_auth_methods(self):
        """Test that SSL security warnings are consistent across authentication methods."""
        base_ssl_config = {
            "base_url": "https://jira.example.com",
            "verify_ssl": False,
            "ca_cert_path": None
        }
        
        # Test with different auth methods
        configs = [
            JiraConfig(username="user", password="pass", **base_ssl_config),
            JiraConfig(email="test@example.com", api_token="token", **base_ssl_config),
            JiraConfig(personal_access_token="pat", **base_ssl_config)
        ]
        
        services = [JiraService(config) for config in configs]
        
        # All services should generate the same SSL warnings
        for service in services:
            warnings = service.ssl_handler.get_ssl_security_warnings()
            assert len(warnings) > 0
            assert any("SSL certificate verification is DISABLED" in warning for warning in warnings)
            assert any("vulnerable to man-in-the-middle attacks" in warning for warning in warnings)
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_http_client_ssl_config_consistent_across_auth_methods(self, mock_client):
        """Test that HTTP clients use consistent SSL configuration across auth methods."""
        # Mock the async context manager and response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "9.12.0"}
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        base_ssl_config = {
            "base_url": "https://jira.example.com",
            "verify_ssl": True,
            "ca_cert_path": None
        }
        
        # Test with different auth methods
        configs = [
            JiraConfig(username="user", password="pass", **base_ssl_config),
            JiraConfig(email="test@example.com", api_token="token", **base_ssl_config),
            JiraConfig(personal_access_token="pat", **base_ssl_config)
        ]
        
        for config in configs:
            mock_client.reset_mock()
            
            jira_service = JiraService(config)
            
            # Test deployment detector HTTP client configuration
            await jira_service.deployment_detector.detect_deployment(
                "https://jira.example.com", {}
            )
            
            # Verify httpx.AsyncClient was called with correct SSL configuration
            mock_client.assert_called()
            call_args = mock_client.call_args
            assert 'verify' in call_args.kwargs
            assert call_args.kwargs['verify'] is True


class TestSSLAuthIntegrationEdgeCases:
    """Test edge cases for SSL and authentication integration."""
    
    def test_ssl_config_with_missing_auth_credentials(self):
        """Test SSL configuration when authentication credentials are missing."""
        # Config with SSL settings but no auth credentials
        config = JiraConfig(
            base_url="https://jira.example.com",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # SSL configuration should still be properly set
        assert jira_service.ssl_handler.verify_ssl is False
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Components should have consistent SSL configuration
        assert jira_service.deployment_detector.verify_ssl is False
        assert jira_service.api_version_manager.verify_ssl is False
    
    def test_ssl_config_with_invalid_ca_path_across_auth_methods(self):
        """Test SSL configuration with invalid CA path across different auth methods."""
        base_config = {
            "base_url": "https://jira.example.com",
            "verify_ssl": True,
            "ca_cert_path": "/nonexistent/cert.pem"
        }
        
        configs = [
            JiraConfig(username="user", password="pass", **base_config),
            JiraConfig(email="test@example.com", api_token="token", **base_config),
            JiraConfig(personal_access_token="pat", **base_config)
        ]
        
        for config in configs:
            jira_service = JiraService(config)
            
            # SSL handler should be created but will fail when trying to use invalid CA
            assert jira_service.ssl_handler.verify_ssl is True
            assert jira_service.ssl_handler.ca_cert_path == "/nonexistent/cert.pem"
            
            # Should raise FileNotFoundError when trying to get SSL context
            with pytest.raises(FileNotFoundError):
                jira_service.ssl_handler.get_ssl_context()
            
            # Should raise FileNotFoundError when trying to get httpx verify config
            with pytest.raises(FileNotFoundError):
                jira_service.ssl_handler.get_httpx_verify_config()
    
    def test_ssl_configuration_info_with_different_auth_methods(self):
        """Test SSL configuration info reporting with different authentication methods."""
        base_config = {
            "base_url": "https://jira.example.com",
            "verify_ssl": True,
            "ca_cert_path": None
        }
        
        configs = [
            JiraConfig(username="user", password="pass", **base_config),
            JiraConfig(email="test@example.com", api_token="token", **base_config),
            JiraConfig(personal_access_token="pat", **base_config)
        ]
        
        for config in configs:
            jira_service = JiraService(config)
            ssl_info = jira_service.ssl_handler.get_ssl_configuration_info()
            
            # All should report the same SSL configuration info
            assert ssl_info["ssl_verification_enabled"] is True
            assert ssl_info["custom_ca_certificate"] is False
            assert ssl_info["ca_certificate_path"] is None
            assert ssl_info["security_level"] == "HIGH"
            assert len(ssl_info["warnings"]) == 0  # No warnings for properly configured SSL