"""Tests for SSL configuration flow validation.

This module tests that SSL configuration is properly propagated through
the entire JIRA service stack, from configuration to HTTP clients.
"""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from pathlib import Path
import tempfile
import ssl

from app.services.jira import JiraService, JiraConfig
from app.services.ssl_handler import SSLHandler


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


class TestSSLConfigurationFlow:
    """Test SSL configuration propagation through the system."""
    
    def test_ssl_handler_initialization_with_verification_enabled(self):
        """Test SSL handler is properly initialized with SSL verification enabled."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL handler is created with correct configuration
        assert jira_service.ssl_handler is not None
        assert jira_service.ssl_handler.verify_ssl is True
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is True
    
    def test_ssl_handler_initialization_with_verification_disabled(self):
        """Test SSL handler is properly initialized with SSL verification disabled."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Verify SSL handler is created with correct configuration
        assert jira_service.ssl_handler is not None
        assert jira_service.ssl_handler.verify_ssl is False
        assert jira_service.ssl_handler.ca_cert_path is None
        
        # Verify SSL handler returns correct httpx configuration
        verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        assert verify_config is False
    
    def test_ssl_handler_initialization_with_custom_ca_certificate(self):
        """Test SSL handler is properly initialized with custom CA certificate."""
        # Create a temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            ca_cert_path = f.name
        
        try:
            config = JiraConfig(
                base_url="https://jira.example.com",
                email="test@example.com",
                api_token="test-token",
                verify_ssl=True,
                ca_cert_path=ca_cert_path
            )
            
            jira_service = JiraService(config)
            
            # Verify SSL handler is created with correct configuration
            assert jira_service.ssl_handler is not None
            assert jira_service.ssl_handler.verify_ssl is True
            assert jira_service.ssl_handler.ca_cert_path == ca_cert_path
            
            # Verify SSL handler returns correct httpx configuration
            verify_config = jira_service.ssl_handler.get_httpx_verify_config()
            assert verify_config == ca_cert_path
        finally:
            # Clean up temporary file
            Path(ca_cert_path).unlink(missing_ok=True)
    
    def test_deployment_detector_ssl_configuration(self):
        """Test that DeploymentDetector receives correct SSL configuration."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path="/path/to/cert.pem"
        )
        
        jira_service = JiraService(config)
        
        # Verify deployment detector has correct SSL configuration
        assert jira_service.deployment_detector.verify_ssl is False
        assert jira_service.deployment_detector.ca_cert_path == "/path/to/cert.pem"
        
        # Verify deployment detector returns correct verify config
        verify_config = jira_service.deployment_detector._get_verify_config()
        assert verify_config is False
    
    def test_api_version_manager_ssl_configuration(self):
        """Test that APIVersionManager receives correct SSL configuration."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path="/path/to/cert.pem"
        )
        
        jira_service = JiraService(config)
        
        # Verify API version manager has correct SSL configuration
        assert jira_service.api_version_manager.verify_ssl is True
        assert jira_service.api_version_manager.ca_cert_path == "/path/to/cert.pem"
        
        # Verify API version manager returns correct verify config
        verify_config = jira_service.api_version_manager._get_verify_config()
        assert verify_config == "/path/to/cert.pem"
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_deployment_detector_httpx_client_configuration(self, mock_client):
        """Test that DeploymentDetector configures httpx client with correct SSL settings."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        
        # Mock the async context manager and response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serverTitle": "Test JIRA",
            "version": "9.12.0"
        }
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Call detect_deployment which should create httpx client with SSL config
        await jira_service.deployment_detector.detect_deployment(
            "https://jira.example.com", {}
        )
        
        # Verify httpx.AsyncClient was called with correct SSL configuration
        mock_client.assert_called_once()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] is False
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_api_version_manager_httpx_client_configuration(self, mock_client):
        """Test that APIVersionManager configures httpx client with correct SSL settings."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path="/path/to/cert.pem"
        )
        
        jira_service = JiraService(config)
        
        # Mock the async context manager
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock()
        mock_client_instance.get.return_value.status_code = 200
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Call test_api_version which should create httpx client with SSL config
        await jira_service.api_version_manager.test_api_version(
            "https://jira.example.com", "3", {}
        )
        
        # Verify httpx.AsyncClient was called with correct SSL configuration
        mock_client.assert_called_once()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] == "/path/to/cert.pem"
    
    def test_ssl_handler_get_ssl_context_with_verification_enabled(self):
        """Test SSL context creation with verification enabled."""
        ssl_handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        ssl_context = ssl_handler.get_ssl_context()
        
        # Should return an SSL context, not False
        assert ssl_context is not False
        assert isinstance(ssl_context, ssl.SSLContext)
    
    def test_ssl_handler_get_ssl_context_with_verification_disabled(self):
        """Test SSL context creation with verification disabled."""
        ssl_handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        ssl_context = ssl_handler.get_ssl_context()
        
        # Should return False to disable SSL verification
        assert ssl_context is False
    
    def test_ssl_handler_get_ssl_context_with_custom_ca(self):
        """Test SSL context creation with custom CA certificate."""
        # Create a temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            ca_cert_path = f.name
        
        try:
            ssl_handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
            
            ssl_context = ssl_handler.get_ssl_context()
            
            # Should return an SSL context with custom CA loaded
            assert ssl_context is not False
            assert isinstance(ssl_context, ssl.SSLContext)
        finally:
            # Clean up temporary file
            Path(ca_cert_path).unlink(missing_ok=True)
    
    def test_ssl_handler_get_ssl_context_with_invalid_ca_path(self):
        """Test SSL context creation with invalid CA certificate path."""
        ssl_handler = SSLHandler(verify_ssl=True, ca_cert_path="/nonexistent/cert.pem")
        
        # Should raise FileNotFoundError for invalid CA path
        with pytest.raises(FileNotFoundError):
            ssl_handler.get_ssl_context()
    
    def test_ssl_configuration_consistency_across_components(self):
        """Test that SSL configuration is consistent across all components."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path="/path/to/cert.pem"
        )
        
        jira_service = JiraService(config)
        
        # All components should have the same SSL configuration
        assert jira_service.ssl_handler.verify_ssl is False
        assert jira_service.ssl_handler.ca_cert_path == "/path/to/cert.pem"
        
        assert jira_service.deployment_detector.verify_ssl is False
        assert jira_service.deployment_detector.ca_cert_path == "/path/to/cert.pem"
        
        assert jira_service.api_version_manager.verify_ssl is False
        assert jira_service.api_version_manager.ca_cert_path == "/path/to/cert.pem"
        
        # All components should return the same verify config
        ssl_verify_config = jira_service.ssl_handler.get_httpx_verify_config()
        detector_verify_config = jira_service.deployment_detector._get_verify_config()
        api_verify_config = jira_service.api_version_manager._get_verify_config()
        
        assert ssl_verify_config is False
        assert detector_verify_config is False
        assert api_verify_config is False
    
    def test_ssl_configuration_info_reporting(self):
        """Test that SSL configuration information is properly reported."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        jira_service = JiraService(config)
        ssl_info = jira_service.ssl_handler.get_ssl_configuration_info()
        
        # Verify SSL configuration info
        assert ssl_info["ssl_verification_enabled"] is False
        assert ssl_info["custom_ca_certificate"] is False
        assert ssl_info["ca_certificate_path"] is None
        assert ssl_info["security_level"] == "LOW"
        assert len(ssl_info["warnings"]) > 0  # Should have warnings for disabled SSL
    
    def test_ssl_security_warnings_for_disabled_verification(self):
        """Test that security warnings are generated when SSL verification is disabled."""
        ssl_handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        warnings = ssl_handler.get_ssl_security_warnings()
        
        # Should have multiple security warnings
        assert len(warnings) > 0
        assert any("SSL certificate verification is DISABLED" in warning for warning in warnings)
        assert any("vulnerable to man-in-the-middle attacks" in warning for warning in warnings)
        assert any("NEVER use this setting in production" in warning for warning in warnings)
    
    def test_ssl_no_warnings_for_enabled_verification(self):
        """Test that no security warnings are generated when SSL verification is enabled."""
        ssl_handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        warnings = ssl_handler.get_ssl_security_warnings()
        
        # Should have no warnings for properly configured SSL
        assert len(warnings) == 0


class TestSSLHandlerHttpxIntegration:
    """Test SSL handler integration with httpx clients."""
    
    def test_httpx_verify_config_ssl_enabled_no_ca(self):
        """Test httpx verify config with SSL enabled and no custom CA."""
        ssl_handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        verify_config = ssl_handler.get_httpx_verify_config()
        
        assert verify_config is True
    
    def test_httpx_verify_config_ssl_disabled(self):
        """Test httpx verify config with SSL disabled."""
        ssl_handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        verify_config = ssl_handler.get_httpx_verify_config()
        
        assert verify_config is False
    
    def test_httpx_verify_config_ssl_enabled_with_ca(self):
        """Test httpx verify config with SSL enabled and custom CA."""
        # Create a temporary certificate file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            ca_cert_path = f.name
        
        try:
            ssl_handler = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
            
            verify_config = ssl_handler.get_httpx_verify_config()
            
            assert verify_config == ca_cert_path
        finally:
            # Clean up temporary file
            Path(ca_cert_path).unlink(missing_ok=True)
    
    def test_httpx_verify_config_ssl_enabled_with_invalid_ca(self):
        """Test httpx verify config with SSL enabled and invalid CA path."""
        ssl_handler = SSLHandler(verify_ssl=True, ca_cert_path="/nonexistent/cert.pem")
        
        # Should raise FileNotFoundError for invalid CA path
        with pytest.raises(FileNotFoundError):
            ssl_handler.get_httpx_verify_config()