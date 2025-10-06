"""Comprehensive unit tests for SSL configuration.

This module provides comprehensive unit tests for SSL configuration across
JiraConfig creation, SSL handler initialization, and httpx client configuration.
Tests cover all SSL configuration scenarios including verification enabled/disabled,
custom CA certificates, and error handling.
"""

import pytest
import ssl
import tempfile
from pathlib import Path
from unittest.mock import patch
import httpx

from app.config import JiraConfig, JiraDeploymentType
from app.services.ssl_handler import SSLHandler
from app.services.jira import JiraService


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


class TestJiraConfigSSLCreation:
    """Test JiraConfig creation with verify_ssl parameter."""
    
    def test_jira_config_default_ssl_settings(self):
        """Test JiraConfig creation with default SSL settings."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token"
        )
        
        # Default SSL settings should be secure
        assert config.verify_ssl is True
        assert config.ca_cert_path is None
        assert config.proxy_url is None
        assert config.timeout == 30
    
    def test_jira_config_ssl_verification_enabled(self):
        """Test JiraConfig creation with SSL verification explicitly enabled."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        assert config.verify_ssl is True
        assert config.ca_cert_path is None
    
    def test_jira_config_ssl_verification_disabled(self):
        """Test JiraConfig creation with SSL verification disabled."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        assert config.verify_ssl is False
        assert config.ca_cert_path is None
    
    def test_jira_config_ssl_with_custom_ca_certificate(self):
        """Test JiraConfig creation with custom CA certificate."""
        ca_cert_path = "/path/to/custom/ca.pem"
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=ca_cert_path
        )
        
        assert config.verify_ssl is True
        assert config.ca_cert_path == ca_cert_path
    
    def test_jira_config_ssl_disabled_with_ca_certificate(self):
        """Test JiraConfig creation with SSL disabled but CA certificate provided."""
        ca_cert_path = "/path/to/custom/ca.pem"
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=ca_cert_path
        )
        
        # CA certificate should be preserved even if SSL is disabled
        assert config.verify_ssl is False
        assert config.ca_cert_path == ca_cert_path
    
    def test_jira_config_ssl_convenience_methods(self):
        """Test JiraConfig SSL convenience methods."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token"
        )
        
        # Test disable SSL verification
        config.disable_ssl_verification()
        assert config.verify_ssl is False
        assert config.ca_cert_path is None
        
        # Test enable SSL verification
        config.enable_ssl_verification()
        assert config.verify_ssl is True
        assert config.ca_cert_path is None
        
        # Test enable SSL verification with CA certificate
        ca_path = "/path/to/ca.pem"
        config.enable_ssl_verification(ca_cert_path=ca_path)
        assert config.verify_ssl is True
        assert config.ca_cert_path == ca_path
    
    def test_jira_config_ssl_config_summary(self):
        """Test JiraConfig SSL configuration summary."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path="/path/to/ca.pem"
        )
        
        summary = config.get_ssl_config_summary()
        
        assert summary["ssl_verification_enabled"] is False
        assert summary["custom_ca_certificate"] is True
        assert summary["ca_cert_path"] == "/path/to/ca.pem"
        assert summary["base_url_uses_https"] is True
        assert "ssl_troubleshooting_tip" in summary
    
    def test_jira_config_ssl_with_different_auth_types(self):
        """Test JiraConfig SSL settings with different authentication types."""
        ssl_config = {
            "verify_ssl": False,
            "ca_cert_path": "/path/to/ca.pem"
        }
        
        # API Token authentication
        config_api = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            **ssl_config
        )
        
        # Personal Access Token authentication
        config_pat = JiraConfig(
            base_url="https://jira.example.com",
            personal_access_token="test-pat",
            **ssl_config
        )
        
        # Basic authentication
        config_basic = JiraConfig(
            base_url="https://jira.example.com",
            username="testuser",
            password="testpass",
            **ssl_config
        )
        
        # All should have the same SSL configuration
        for config in [config_api, config_pat, config_basic]:
            assert config.verify_ssl is False
            assert config.ca_cert_path == "/path/to/ca.pem"
    
    def test_jira_config_ssl_with_deployment_types(self):
        """Test JiraConfig SSL settings with different deployment types."""
        ssl_config = {
            "verify_ssl": True,
            "ca_cert_path": "/path/to/ca.pem"
        }
        
        # Cloud deployment
        config_cloud = JiraConfig(
            base_url="https://company.atlassian.net",
            deployment_type=JiraDeploymentType.CLOUD,
            email="test@example.com",
            api_token="test-token",
            **ssl_config
        )
        
        # Data Center deployment
        config_dc = JiraConfig(
            base_url="https://jira.company.com",
            deployment_type=JiraDeploymentType.DATA_CENTER,
            username="testuser",
            password="testpass",
            **ssl_config
        )
        
        # Server deployment
        config_server = JiraConfig(
            base_url="https://jira.company.com",
            deployment_type=JiraDeploymentType.SERVER,
            username="testuser",
            password="testpass",
            **ssl_config
        )
        
        # All should have the same SSL configuration
        for config in [config_cloud, config_dc, config_server]:
            assert config.verify_ssl is True
            assert config.ca_cert_path == "/path/to/ca.pem"


class TestSSLHandlerInitialization:
    """Test SSL handler initialization with various configurations."""
    
    def test_ssl_handler_default_initialization(self):
        """Test SSL handler initialization with default parameters."""
        handler = SSLHandler()
        
        assert handler.verify_ssl is True
        assert handler.ca_cert_path is None
    
    def test_ssl_handler_ssl_enabled_initialization(self):
        """Test SSL handler initialization with SSL verification enabled."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        assert handler.verify_ssl is True
        assert handler.ca_cert_path is None
    
    def test_ssl_handler_ssl_disabled_initialization(self):
        """Test SSL handler initialization with SSL verification disabled."""
        handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        assert handler.verify_ssl is False
        assert handler.ca_cert_path is None
    
    def test_ssl_handler_with_custom_ca_initialization(self):
        """Test SSL handler initialization with custom CA certificate."""
        ca_cert_path = "/path/to/custom/ca.pem"
        handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        
        assert handler.verify_ssl is True
        assert handler.ca_cert_path == ca_cert_path
    
    def test_ssl_handler_disabled_with_ca_initialization(self):
        """Test SSL handler initialization with SSL disabled but CA certificate provided."""
        ca_cert_path = "/path/to/custom/ca.pem"
        handler = SSLHandler(verify_ssl=False, ca_cert_path=ca_cert_path)
        
        assert handler.verify_ssl is False
        assert handler.ca_cert_path == ca_cert_path
    
    @patch('app.services.ssl_handler.app_logger')
    def test_ssl_handler_logging_ssl_enabled(self, mock_logger):
        """Test SSL handler logs appropriate messages when SSL is enabled."""
        SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        # Should log SSL verification enabled
        mock_logger.info.assert_called_with("🔐 SSL verification enabled with system CA certificates")
    
    @patch('app.services.ssl_handler.app_logger')
    def test_ssl_handler_logging_ssl_disabled(self, mock_logger):
        """Test SSL handler logs security warnings when SSL is disabled."""
        SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        # Should log multiple security warnings
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        assert len(warning_calls) >= 4  # Should have multiple security warnings
        
        # Check for specific warning messages
        warning_messages = [str(call[0][0]) for call in warning_calls]
        assert any("SSL certificate verification is DISABLED" in msg for msg in warning_messages)
        assert any("vulnerable to man-in-the-middle attacks" in msg for msg in warning_messages)
        assert any("NEVER disable SSL verification in production" in msg for msg in warning_messages)
    
    @patch('app.services.ssl_handler.app_logger')
    def test_ssl_handler_logging_custom_ca(self, mock_logger):
        """Test SSL handler logs custom CA certificate usage."""
        ca_cert_path = "/path/to/custom/ca.pem"
        SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        
        # Should log custom CA certificate usage
        mock_logger.info.assert_called_with(f"🔐 SSL verification enabled with custom CA certificate: {ca_cert_path}")
    
    def test_ssl_handler_get_ssl_context_enabled(self):
        """Test SSL handler SSL context creation when verification is enabled."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        context = handler.get_ssl_context()
        
        assert context is not False
        assert isinstance(context, ssl.SSLContext)
    
    def test_ssl_handler_get_ssl_context_disabled(self):
        """Test SSL handler SSL context creation when verification is disabled."""
        handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        context = handler.get_ssl_context()
        
        assert context is False
    
    @patch('pathlib.Path.exists')
    @patch('ssl.SSLContext.load_verify_locations')
    def test_ssl_handler_get_ssl_context_with_valid_ca(self, mock_load_verify, mock_exists):
        """Test SSL handler SSL context creation with valid custom CA."""
        mock_exists.return_value = True
        ca_cert_path = "/path/to/custom/ca.pem"
        handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        
        context = handler.get_ssl_context()
        
        assert isinstance(context, ssl.SSLContext)
        mock_load_verify.assert_called_once_with(ca_cert_path)
    
    @patch('pathlib.Path.exists')
    def test_ssl_handler_get_ssl_context_with_invalid_ca_path(self, mock_exists):
        """Test SSL handler SSL context creation with invalid CA certificate path."""
        mock_exists.return_value = False
        ca_cert_path = "/nonexistent/ca.pem"
        handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        
        with pytest.raises(FileNotFoundError, match="CA certificate file not found"):
            handler.get_ssl_context()
    
    @patch('pathlib.Path.exists')
    @patch('ssl.SSLContext.load_verify_locations')
    def test_ssl_handler_get_ssl_context_with_invalid_ca_content(self, mock_load_verify, mock_exists):
        """Test SSL handler SSL context creation with invalid CA certificate content."""
        mock_exists.return_value = True
        mock_load_verify.side_effect = ssl.SSLError("Invalid certificate")
        ca_cert_path = "/path/to/invalid/ca.pem"
        handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        
        with pytest.raises(ValueError, match="Invalid CA certificate file"):
            handler.get_ssl_context()


class TestSSLHandlerHttpxConfiguration:
    """Test httpx client configuration with SSL settings."""
    
    def test_httpx_verify_config_ssl_enabled_default(self):
        """Test httpx verify configuration with SSL enabled and default CA."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        verify_config = handler.get_httpx_verify_config()
        
        assert verify_config is True
    
    def test_httpx_verify_config_ssl_disabled(self):
        """Test httpx verify configuration with SSL disabled."""
        handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        verify_config = handler.get_httpx_verify_config()
        
        assert verify_config is False
    
    @patch('pathlib.Path.exists')
    def test_httpx_verify_config_ssl_enabled_custom_ca(self, mock_exists):
        """Test httpx verify configuration with SSL enabled and custom CA."""
        mock_exists.return_value = True
        ca_cert_path = "/path/to/custom/ca.pem"
        handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        
        verify_config = handler.get_httpx_verify_config()
        
        assert verify_config == ca_cert_path
    
    @patch('pathlib.Path.exists')
    def test_httpx_verify_config_ssl_enabled_invalid_ca_path(self, mock_exists):
        """Test httpx verify configuration with SSL enabled and invalid CA path."""
        mock_exists.return_value = False
        ca_cert_path = "/nonexistent/ca.pem"
        handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        
        with pytest.raises(FileNotFoundError, match="CA certificate file not found"):
            handler.get_httpx_verify_config()
    
    def test_httpx_verify_config_ssl_disabled_with_ca_path(self):
        """Test httpx verify configuration with SSL disabled but CA path provided."""
        ca_cert_path = "/path/to/custom/ca.pem"
        handler = SSLHandler(verify_ssl=False, ca_cert_path=ca_cert_path)
        
        verify_config = handler.get_httpx_verify_config()
        
        # Should return False regardless of CA path when SSL is disabled
        assert verify_config is False
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_httpx_client_creation_ssl_enabled(self, mock_client):
        """Test httpx client creation with SSL verification enabled."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        verify_config = handler.get_httpx_verify_config()
        
        # Create httpx client with SSL configuration
        async with httpx.AsyncClient(verify=verify_config, timeout=30):
            pass
        
        # Verify httpx.AsyncClient was called with correct SSL configuration
        mock_client.assert_called_once()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] is True
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_httpx_client_creation_ssl_disabled(self, mock_client):
        """Test httpx client creation with SSL verification disabled."""
        handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        verify_config = handler.get_httpx_verify_config()
        
        # Create httpx client with SSL configuration
        async with httpx.AsyncClient(verify=verify_config, timeout=30):
            pass
        
        # Verify httpx.AsyncClient was called with correct SSL configuration
        mock_client.assert_called_once()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] is False
    
    @patch('httpx.AsyncClient')
    @patch('pathlib.Path.exists')
    @pytest.mark.asyncio
    async def test_httpx_client_creation_ssl_enabled_custom_ca(self, mock_exists, mock_client):
        """Test httpx client creation with SSL verification enabled and custom CA."""
        mock_exists.return_value = True
        ca_cert_path = "/path/to/custom/ca.pem"
        handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
        verify_config = handler.get_httpx_verify_config()
        
        # Create httpx client with SSL configuration
        async with httpx.AsyncClient(verify=verify_config, timeout=30):
            pass
        
        # Verify httpx.AsyncClient was called with correct SSL configuration
        mock_client.assert_called_once()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] == ca_cert_path


class TestJiraServiceSSLIntegration:
    """Test JiraService SSL configuration integration."""
    
    def test_jira_service_ssl_handler_initialization_enabled(self):
        """Test JiraService initializes SSL handler correctly when SSL is enabled."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        assert service.ssl_handler is not None
        assert service.ssl_handler.verify_ssl is True
        assert service.ssl_handler.ca_cert_path is None
    
    def test_jira_service_ssl_handler_initialization_disabled(self):
        """Test JiraService initializes SSL handler correctly when SSL is disabled."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        assert service.ssl_handler is not None
        assert service.ssl_handler.verify_ssl is False
        assert service.ssl_handler.ca_cert_path is None
    
    def test_jira_service_ssl_handler_initialization_custom_ca(self):
        """Test JiraService initializes SSL handler correctly with custom CA."""
        ca_cert_path = "/path/to/custom/ca.pem"
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=ca_cert_path
        )
        
        service = JiraService(config)
        
        assert service.ssl_handler is not None
        assert service.ssl_handler.verify_ssl is True
        assert service.ssl_handler.ca_cert_path == ca_cert_path
    
    def test_jira_service_ssl_configuration_propagation(self):
        """Test SSL configuration is properly propagated to all components."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path="/path/to/ca.pem"
        )
        
        service = JiraService(config)
        
        # SSL handler should have correct configuration
        assert service.ssl_handler.verify_ssl is False
        assert service.ssl_handler.ca_cert_path == "/path/to/ca.pem"
        
        # Deployment detector should have correct configuration
        assert service.deployment_detector.verify_ssl is False
        assert service.deployment_detector.ca_cert_path == "/path/to/ca.pem"
        
        # API version manager should have correct configuration
        assert service.api_version_manager.verify_ssl is False
        assert service.api_version_manager.ca_cert_path == "/path/to/ca.pem"
    
    @patch('app.services.jira.app_logger')
    def test_jira_service_ssl_configuration_logging(self, mock_logger):
        """Test JiraService logs SSL configuration information."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        JiraService(config)
        
        # Should log SSL configuration security level
        info_calls = [call for call in mock_logger.info.call_args_list]
        assert any("Security Level: LOW" in str(call) for call in info_calls)
        
        # Should log SSL warnings
        warning_calls = [call for call in mock_logger.warning.call_args_list]
        assert len(warning_calls) > 0
    
    def test_jira_service_ssl_configuration_consistency(self):
        """Test SSL configuration consistency across different authentication methods."""
        ssl_config = {
            "verify_ssl": True,
            "ca_cert_path": "/path/to/ca.pem"
        }
        
        # Test with API token authentication
        config_api = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            **ssl_config
        )
        service_api = JiraService(config_api)
        
        # Test with Personal Access Token authentication
        config_pat = JiraConfig(
            base_url="https://jira.example.com",
            personal_access_token="test-pat",
            **ssl_config
        )
        service_pat = JiraService(config_pat)
        
        # Test with Basic authentication
        config_basic = JiraConfig(
            base_url="https://jira.example.com",
            username="testuser",
            password="testpass",
            **ssl_config
        )
        service_basic = JiraService(config_basic)
        
        # All services should have identical SSL configuration
        services = [service_api, service_pat, service_basic]
        for service in services:
            assert service.ssl_handler.verify_ssl is True
            assert service.ssl_handler.ca_cert_path == "/path/to/ca.pem"
            assert service.deployment_detector.verify_ssl is True
            assert service.deployment_detector.ca_cert_path == "/path/to/ca.pem"
            assert service.api_version_manager.verify_ssl is True
            assert service.api_version_manager.ca_cert_path == "/path/to/ca.pem"


class TestSSLConfigurationEdgeCases:
    """Test edge cases for SSL configuration."""
    
    def test_ssl_handler_with_empty_ca_path(self):
        """Test SSL handler with empty CA certificate path."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path="")
        
        # Empty string should be treated as None
        context = handler.get_ssl_context()
        assert isinstance(context, ssl.SSLContext)
        
        verify_config = handler.get_httpx_verify_config()
        assert verify_config is True
    
    def test_ssl_handler_with_whitespace_ca_path(self):
        """Test SSL handler with whitespace-only CA certificate path."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path="   ")
        
        # Whitespace-only path should be treated as a real path
        with pytest.raises(FileNotFoundError):
            handler.get_ssl_context()
    
    def test_jira_config_ssl_with_http_url(self):
        """Test JiraConfig SSL settings with HTTP URL (no SSL needed)."""
        config = JiraConfig(
            base_url="http://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path="/path/to/ca.pem"
        )
        
        # SSL settings should be preserved even for HTTP URLs
        assert config.verify_ssl is True
        assert config.ca_cert_path == "/path/to/ca.pem"
        
        summary = config.get_ssl_config_summary()
        assert summary["base_url_uses_https"] is False
    
    def test_ssl_handler_security_warnings_with_missing_ca_file(self):
        """Test SSL handler security warnings when CA file is missing."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path="/nonexistent/ca.pem")
        
        warnings = handler.get_ssl_security_warnings()
        
        # Should warn about missing CA file
        assert any("CA certificate file not found" in warning for warning in warnings)
    
    def test_ssl_handler_security_warnings_with_directory_ca_path(self):
        """Test SSL handler security warnings when CA path is a directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            handler = SSLHandler(verify_ssl=True, ca_cert_path=temp_dir)
            
            warnings = handler.get_ssl_security_warnings()
            
            # Should warn about CA path not being a file
            assert any("not a file" in warning for warning in warnings)
    
    def test_ssl_configuration_info_comprehensive(self):
        """Test comprehensive SSL configuration information reporting."""
        # Create a temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            ca_cert_path = f.name
        
        try:
            handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
            
            config_info = handler.get_ssl_configuration_info()
            
            assert config_info["ssl_verification_enabled"] is True
            assert config_info["custom_ca_certificate"] is True
            assert config_info["ca_certificate_path"] == ca_cert_path
            assert config_info["security_level"] == "HIGH"
            assert config_info["ca_certificate_exists"] is True
            assert config_info["ca_certificate_readable"] is True
            assert len(config_info["warnings"]) == 0
        finally:
            # Clean up temporary file
            Path(ca_cert_path).unlink(missing_ok=True)
    
    def test_ssl_validate_ca_certificate_file_comprehensive(self):
        """Test comprehensive CA certificate file validation."""
        # Test with valid certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            valid_ca_path = f.name
        
        try:
            is_valid, error = SSLHandler.validate_ca_certificate_file(valid_ca_path)
            assert is_valid is True
            assert error is None
        finally:
            Path(valid_ca_path).unlink(missing_ok=True)
        
        # Test with nonexistent file
        is_valid, error = SSLHandler.validate_ca_certificate_file("/nonexistent/ca.pem")
        assert is_valid is False
        assert "does not exist" in error
        
        # Test with directory instead of file
        with tempfile.TemporaryDirectory() as temp_dir:
            is_valid, error = SSLHandler.validate_ca_certificate_file(temp_dir)
            assert is_valid is False
            assert "not a file" in error
        
        # Test with invalid certificate content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("invalid certificate content")
            invalid_ca_path = f.name
        
        try:
            is_valid, error = SSLHandler.validate_ca_certificate_file(invalid_ca_path)
            assert is_valid is False
            assert "PEM format" in error
        finally:
            Path(invalid_ca_path).unlink(missing_ok=True)