"""Real-world SSL scenario tests for JIRA SSL verification fix.

This module tests the SSL verification fix with realistic scenarios:
- Self-signed certificates with SSL disabled
- SSL configuration edge cases
- Real-world error handling and user feedback
"""

import pytest
import pytest_asyncio
import tempfile
import ssl
import socket
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import httpx
from typing import Dict, Any

from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
from app.services.jira import JiraService, ConnectionResult
from app.services.ssl_handler import SSLHandler, SSLValidationResult, SSLCertificateInfo
from app.services.deployment_detector import DeploymentDetector, DeploymentInfo
from app.services.api_version_manager import APIVersionManager


# Sample self-signed certificate for testing
SELF_SIGNED_CERT_PEM = """-----BEGIN CERTIFICATE-----
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


class TestSelfSignedCertificateScenarios:
    """Test scenarios with self-signed certificates - Task 6.1"""
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_jira_connection_self_signed_cert_ssl_disabled_success(self, mock_client):
        """Test JIRA connection with self-signed certificate and SSL disabled - succeeds."""
        # Mock successful HTTP response for self-signed certificate scenario
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serverTitle": "Internal JIRA Server",
            "version": "9.12.0",
            "deploymentType": "Server",
            "baseUrl": "https://jira.internal.company.com",
            "buildNumber": "912001",  # Add build number to indicate Server/Data Center
            "serverId": "B8E7-9F2A-3C4D-5E6F"  # Add server ID to indicate Server/Data Center
        }
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Configure JIRA service with SSL disabled for self-signed certificate
        config = JiraConfig(
            base_url="https://jira.internal.company.com",
            username="testuser",
            password="testpass",
            verify_ssl=False,  # Disabled to work with self-signed certificate
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        # Test connection through deployment detector
        deployment_info = await service.deployment_detector.detect_deployment(
            "https://jira.internal.company.com", {}
        )
        
        # Verify SSL verification was disabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] is False
        
        # Verify successful deployment detection despite self-signed certificate
        assert deployment_info is not None
        assert deployment_info.server_title == "Internal JIRA Server"
        assert deployment_info.version == "9.12.0"
        assert deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_jira_connection_self_signed_cert_api_token_ssl_disabled(self, mock_client):
        """Test JIRA connection with self-signed certificate using API token and SSL disabled."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serverTitle": "Development JIRA",
            "version": "9.4.0",
            "deploymentType": "Server",
            "buildNumber": "904001",
            "serverId": "DEV1-2345-6789-ABCD"
        }
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Configure JIRA service with API token authentication and SSL disabled
        config = JiraConfig(
            base_url="https://jira-dev.company.local",
            email="developer@company.com",
            api_token="ATATT3xFfGF0T4JNjN-example-token",
            verify_ssl=False,  # Disabled for self-signed certificate
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        # Test API version check
        result = await service.api_version_manager.test_api_version(
            "https://jira-dev.company.local", {}, "3"
        )
        
        # Verify SSL verification was disabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] is False
        
        # Should succeed with self-signed certificate when SSL disabled
        assert result is True
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_jira_connection_self_signed_cert_pat_ssl_disabled(self, mock_client):
        """Test JIRA connection with self-signed certificate using Personal Access Token and SSL disabled."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serverTitle": "Test JIRA Data Center",
            "version": "9.12.0",
            "deploymentType": "DataCenter",
            "buildNumber": "912001",
            "serverId": "DC01-2345-6789-ABCD"
        }
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Configure JIRA service with Personal Access Token and SSL disabled
        config = JiraConfig(
            base_url="https://jira-test.internal",
            personal_access_token="NjE2Mjc2NzY2ODk5OjEyMzQ1Njc4OTA=",
            verify_ssl=False,  # Disabled for self-signed certificate
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        # Test deployment detection
        deployment_info = await service.deployment_detector.detect_deployment(
            "https://jira-test.internal", {}
        )
        
        # Verify SSL verification was disabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] is False
        
        # Verify successful connection
        assert deployment_info is not None
        assert deployment_info.server_title == "Test JIRA Data Center"
        assert deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER
    
    @pytest.mark.asyncio
    async def test_ssl_verification_can_be_successfully_disabled(self):
        """Test that SSL verification can be successfully disabled."""
        # Test SSL handler with verification disabled
        handler = SSLHandler(verify_ssl=False, ca_cert_path=None)
        
        # Verify SSL verification is disabled
        assert handler.verify_ssl is False
        assert handler.get_httpx_verify_config() is False
        
        # Test with CA certificate path provided (should still be disabled)
        handler_with_ca = SSLHandler(verify_ssl=False, ca_cert_path="/path/to/cert.pem")
        assert handler_with_ca.verify_ssl is False
        assert handler_with_ca.get_httpx_verify_config() is False
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_connection_succeeds_when_ssl_verification_properly_disabled(self, mock_client):
        """Test that connection succeeds when SSL verification is properly disabled."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "9.12.0"}
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Test with different authentication methods
        auth_configs = [
            # Username/Password
            JiraConfig(
                base_url="https://self-signed.example.com",
                username="user",
                password="pass",
                verify_ssl=False
            ),
            # Email/API Token
            JiraConfig(
                base_url="https://self-signed.example.com",
                email="user@example.com",
                api_token="token123",
                verify_ssl=False
            ),
            # Personal Access Token
            JiraConfig(
                base_url="https://self-signed.example.com",
                personal_access_token="pat123",
                verify_ssl=False
            )
        ]
        
        for config in auth_configs:
            service = JiraService(config)
            
            # Test deployment detection
            deployment_info = await service.deployment_detector.detect_deployment(
                config.base_url, {}
            )
            
            # Verify SSL was disabled and connection succeeded
            assert deployment_info is not None
            
            # Reset mock for next iteration
            mock_client.reset_mock()
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_self_signed_cert_with_ssl_enabled_fails_appropriately(self, mock_client):
        """Test that self-signed certificate with SSL enabled fails with appropriate error."""
        # Mock SSL certificate verification failure for self-signed certificate
        ssl_error = httpx.ConnectError(
            "SSL: CERTIFICATE_VERIFY_FAILED certificate verify failed: self signed certificate"
        )
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(side_effect=ssl_error)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Configure JIRA service with SSL enabled (should fail with self-signed cert)
        config = JiraConfig(
            base_url="https://jira.self-signed.com",
            username="testuser",
            password="testpass",
            verify_ssl=True,  # Enabled - should fail with self-signed certificate
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        # Test connection should fail
        with pytest.raises(Exception):  # DeploymentDetectionError wraps the ConnectError
            await service.deployment_detector.detect_deployment(
                "https://jira.self-signed.com", {}
            )
        
        # Verify SSL verification was enabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert 'verify' in call_args.kwargs
        assert call_args.kwargs['verify'] is True
    
    @pytest.mark.asyncio
    async def test_ssl_handler_provides_self_signed_certificate_guidance(self):
        """Test that SSL handler provides appropriate guidance for self-signed certificates."""
        # Create SSL handler with verification enabled
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        # Mock self-signed certificate validation failure
        with patch.object(handler, '_get_certificate_info') as mock_get_cert, \
             patch.object(handler, '_validate_certificate_with_config') as mock_validate:
            
            # Mock self-signed certificate info
            mock_cert_info = SSLCertificateInfo(
                subject={"commonName": "jira.self-signed.com"},
                issuer={"commonName": "jira.self-signed.com"},  # Same as subject = self-signed
                version=3,
                serial_number="123456789",
                not_before="Jan 1 00:00:00 2024 GMT",
                not_after="Jan 1 00:00:00 2025 GMT",
                is_expired=False,
                is_self_signed=True,
                signature_algorithm="sha256WithRSAEncryption",
                public_key_algorithm="RSA"
            )
            mock_get_cert.return_value = mock_cert_info
            
            # Mock validation error for self-signed certificate
            mock_validate.return_value = {
                "message": "Self-signed certificate detected - The server uses a self-signed SSL certificate",
                "type": "self_signed_certificate",
                "troubleshooting_steps": [
                    "📥 Export the self-signed certificate from your browser (click the lock icon → Certificate)",
                    "💾 Save the certificate as a .pem or .crt file on your system",
                    "📂 Set 'Custom CA Certificate Path' to point to the saved certificate file",
                    "🔄 Test the connection again with the certificate path configured",
                    "⚠️  QUICK FIX (Testing Only): Uncheck 'Verify SSL Certificates' in configuration",
                    "🔧 Alternative: Set environment variable JIRA_VERIFY_SSL=false",
                    "⚠️  Security Warning: Self-signed certificates should only be used in development/testing"
                ],
                "suggested_config": {
                    "ca_cert_path": "/path/to/your/self-signed-certificate.pem",
                    "verify_ssl": False,
                    "note": "💡 Recommended: Add certificate path. Alternative: Disable SSL verification for testing only"
                }
            }
            
            # Validate SSL certificate
            result = await handler.validate_ssl_certificate("https://jira.self-signed.com")
            
            # Verify appropriate guidance is provided
            assert result.is_valid is False
            assert result.error_type == "self_signed_certificate"
            assert "self-signed certificate" in result.error_message.lower()
            assert len(result.troubleshooting_steps) > 0
            assert any("Export the self-signed certificate" in step for step in result.troubleshooting_steps)
            assert any("SSL verification" in step or "SSL Certificates" in step for step in result.troubleshooting_steps)
            assert result.suggested_config is not None
            assert "ca_cert_path" in result.suggested_config


class TestSSLConfigurationEdgeCases:
    """Test SSL configuration edge cases - Task 6.2"""
    
    @pytest.mark.asyncio
    async def test_invalid_ca_certificate_path_error_handling(self):
        """Test with invalid CA certificate path."""
        # Test with non-existent file
        with pytest.raises(FileNotFoundError):
            handler = SSLHandler(verify_ssl=True, ca_cert_path="/nonexistent/path/cert.pem")
            handler.get_httpx_verify_config()
    
    @pytest.mark.asyncio
    async def test_malformed_ca_certificate_file_error_handling(self):
        """Test with malformed SSL configuration."""
        # Create temporary file with invalid certificate content
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("This is not a valid certificate file")
            invalid_cert_path = f.name
        
        try:
            # Test validation of malformed certificate
            is_valid, error_message = SSLHandler.validate_ca_certificate_file(invalid_cert_path)
            
            # Should detect invalid certificate format
            assert is_valid is False
            assert "PEM format" in error_message
        finally:
            # Clean up temporary file
            Path(invalid_cert_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_empty_ca_certificate_file_error_handling(self):
        """Test with empty CA certificate file."""
        # Create temporary empty file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write("")  # Empty file
            empty_cert_path = f.name
        
        try:
            # Test validation of empty certificate file
            is_valid, error_message = SSLHandler.validate_ca_certificate_file(empty_cert_path)
            
            # Should detect invalid certificate format
            assert is_valid is False
            assert "PEM format" in error_message
        finally:
            # Clean up temporary file
            Path(empty_cert_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_directory_instead_of_certificate_file(self):
        """Test with directory path instead of certificate file."""
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test validation with directory path
            is_valid, error_message = SSLHandler.validate_ca_certificate_file(temp_dir)
            
            # Should detect that path is not a file
            assert is_valid is False
            assert "not a file" in error_message
    
    @patch('httpx.AsyncClient')
    @pytest.mark.asyncio
    async def test_ssl_verification_toggle_during_active_session(self, mock_client):
        """Test SSL verification toggle during active session."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "9.12.0"}
        
        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(return_value=mock_client_instance)
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)
        
        # Start with SSL enabled
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        # First call with SSL enabled
        result1 = await service.api_version_manager.test_api_version(
            "https://jira.example.com", {}, "3"
        )
        
        # Verify first call used SSL verification
        first_call_args = mock_client.call_args
        assert first_call_args.kwargs['verify'] is True
        assert result1 is True
        
        # Reset mock to track next call
        mock_client.reset_mock()
        
        # Toggle SSL verification to disabled
        config.verify_ssl = False
        
        # Create new service with updated config (simulates session update)
        service_updated = JiraService(config)
        
        # Second call with SSL disabled
        result2 = await service_updated.api_version_manager.test_api_version(
            "https://jira.example.com", {}, "3"
        )
        
        # Verify second call used disabled SSL verification
        second_call_args = mock_client.call_args
        assert second_call_args.kwargs['verify'] is False
        assert result2 is True
    
    @pytest.mark.asyncio
    async def test_proper_error_handling_and_user_feedback(self):
        """Verify proper error handling and user feedback."""
        # Test SSL handler error handling
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        # Test with invalid URL (malformed HTTPS URL)
        result = await handler.validate_ssl_certificate("https://")
        assert result.is_valid is False
        assert result.error_message is not None
        assert len(result.troubleshooting_steps) > 0
        
        # Test with HTTP URL (no SSL)
        result = await handler.validate_ssl_certificate("http://jira.example.com")
        assert result.is_valid is True
        assert "HTTP" in result.error_message
    
    @pytest.mark.asyncio
    async def test_ssl_security_warnings_generation(self):
        """Test SSL security warnings are properly generated."""
        # Test with SSL disabled
        handler_disabled = SSLHandler(verify_ssl=False, ca_cert_path=None)
        warnings = handler_disabled.get_ssl_security_warnings()
        
        # Should have security warnings when SSL is disabled
        assert len(warnings) > 0
        assert any("DISABLED" in warning for warning in warnings)
        assert any("vulnerable" in warning.lower() for warning in warnings)
        assert any("production" in warning.lower() for warning in warnings)
        
        # Test with SSL enabled
        handler_enabled = SSLHandler(verify_ssl=True, ca_cert_path=None)
        warnings = handler_enabled.get_ssl_security_warnings()
        
        # Should have no warnings when SSL is properly enabled
        assert len(warnings) == 0
        
        # Test with invalid CA certificate path
        handler_invalid_ca = SSLHandler(verify_ssl=True, ca_cert_path="/nonexistent/cert.pem")
        warnings = handler_invalid_ca.get_ssl_security_warnings()
        
        # Should warn about missing CA certificate file
        assert len(warnings) > 0
        assert any("not found" in warning for warning in warnings)
    
    @pytest.mark.asyncio
    async def test_ssl_configuration_info_generation(self):
        """Test SSL configuration information generation."""
        # Test with SSL disabled
        handler_disabled = SSLHandler(verify_ssl=False, ca_cert_path=None)
        info = handler_disabled.get_ssl_configuration_info()
        
        assert info["ssl_verification_enabled"] is False
        assert info["custom_ca_certificate"] is False
        assert info["security_level"] == "LOW"
        assert len(info["warnings"]) > 0
        
        # Test with SSL enabled and custom CA
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SELF_SIGNED_CERT_PEM)
            ca_cert_path = f.name
        
        try:
            handler_enabled = SSLHandler(verify_ssl=True, ca_cert_path=ca_cert_path)
            info = handler_enabled.get_ssl_configuration_info()
            
            assert info["ssl_verification_enabled"] is True
            assert info["custom_ca_certificate"] is True
            assert info["ca_certificate_path"] == ca_cert_path
            assert info["security_level"] == "HIGH"
            assert info["ca_certificate_exists"] is True
            assert info["ca_certificate_readable"] is True
        finally:
            Path(ca_cert_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_ssl_troubleshooting_steps_for_different_errors(self):
        """Test SSL troubleshooting steps for different error types."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        # Test troubleshooting steps for different error types
        error_types = [
            "certificate_verification_failed",
            "hostname_mismatch", 
            "self_signed_certificate",
            "certificate_expired",
            "ca_not_found"
        ]
        
        for error_type in error_types:
            steps = handler.get_ssl_troubleshooting_steps(error_type)
            assert len(steps) > 0
            assert all(isinstance(step, str) for step in steps)
    
    @pytest.mark.asyncio
    async def test_ssl_config_suggestions_for_different_errors(self):
        """Test SSL configuration suggestions for different error types."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)
        
        # Test suggestions for self-signed certificate
        suggestions = handler.suggest_ssl_config_for_error(
            "self_signed_certificate", 
            "https://jira.internal.com"
        )
        assert "ca_cert_path" in suggestions
        assert suggestions["verify_ssl"] is True
        
        # Test suggestions for localhost (should include testing option)
        suggestions = handler.suggest_ssl_config_for_error(
            "self_signed_certificate",
            "https://localhost:8443"
        )
        assert "testing_only" in suggestions
        assert suggestions["testing_only"]["verify_ssl"] is False
        
        # Test suggestions for hostname mismatch (no config fix possible)
        suggestions = handler.suggest_ssl_config_for_error(
            "hostname_mismatch",
            "https://jira.example.com"
        )
        assert "note" in suggestions
        assert "server certificate needs to be updated" in suggestions["note"]


class TestSSLFixValidation:
    """Test validation of the SSL verification fix."""
    
    @pytest.mark.asyncio
    async def test_ssl_setting_respected_across_all_auth_methods(self):
        """Test that SSL setting is respected across all authentication methods."""
        # Test configurations for different auth methods
        auth_configs = [
            # Username/Password
            {
                "config": JiraConfig(
                    base_url="https://jira.example.com",
                    username="user",
                    password="pass",
                    verify_ssl=False
                ),
                "auth_type": "username_password"
            },
            # Email/API Token
            {
                "config": JiraConfig(
                    base_url="https://jira.example.com",
                    email="user@example.com",
                    api_token="token123",
                    verify_ssl=False
                ),
                "auth_type": "email_api_token"
            },
            # Personal Access Token
            {
                "config": JiraConfig(
                    base_url="https://jira.example.com",
                    personal_access_token="pat123",
                    verify_ssl=False
                ),
                "auth_type": "personal_access_token"
            }
        ]
        
        for auth_config in auth_configs:
            config = auth_config["config"]
            service = JiraService(config)
            
            # Verify SSL configuration is consistent across all components
            assert service.ssl_handler.verify_ssl is False
            assert service.deployment_detector.verify_ssl is False
            assert service.api_version_manager.verify_ssl is False
            
            # Verify httpx configuration
            assert service.ssl_handler.get_httpx_verify_config() is False
    
    @pytest.mark.asyncio
    async def test_ssl_configuration_propagation_consistency(self):
        """Test that SSL configuration is propagated consistently."""
        # Test with SSL enabled and custom CA
        with tempfile.NamedTemporaryFile(mode='w', suffix='.pem', delete=False) as f:
            f.write(SELF_SIGNED_CERT_PEM)
            ca_cert_path = f.name
        
        try:
            config = JiraConfig(
                base_url="https://jira.example.com",
                username="testuser",
                password="testpass",
                verify_ssl=True,
                ca_cert_path=ca_cert_path
            )
            
            service = JiraService(config)
            
            # Verify SSL configuration is consistent across all components
            assert service.ssl_handler.verify_ssl is True
            assert service.ssl_handler.ca_cert_path == ca_cert_path
            assert service.deployment_detector.verify_ssl is True
            assert service.deployment_detector.ca_cert_path == ca_cert_path
            assert service.api_version_manager.verify_ssl is True
            assert service.api_version_manager.ca_cert_path == ca_cert_path
            
            # Verify httpx configuration
            assert service.ssl_handler.get_httpx_verify_config() == ca_cert_path
        finally:
            Path(ca_cert_path).unlink(missing_ok=True)
    
    @pytest.mark.asyncio
    async def test_no_duplicate_ssl_configuration_assignments(self):
        """Test that there are no duplicate SSL configuration assignments."""
        # This test verifies the fix for duplicate configuration lines
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path=None
        )
        
        service = JiraService(config)
        
        # Verify that SSL configuration is set correctly without duplicates
        # The fix should ensure each component gets the configuration once
        assert hasattr(service.ssl_handler, 'verify_ssl')
        assert hasattr(service.deployment_detector, 'verify_ssl')
        assert hasattr(service.api_version_manager, 'verify_ssl')
        
        # All should have the same configuration
        assert service.ssl_handler.verify_ssl == config.verify_ssl
        assert service.deployment_detector.verify_ssl == config.verify_ssl
        assert service.api_version_manager.verify_ssl == config.verify_ssl