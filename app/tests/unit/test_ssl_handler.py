"""Unit tests for SSL certificate handling."""

import pytest
import ssl
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, Any

from app.services.ssl_handler import (
    SSLHandler, 
    SSLCertificateInfo, 
    SSLValidationResult
)


class TestSSLHandler:
    """Test cases for SSL certificate handling."""
    
    def test_init_default_config(self):
        """Test SSL handler initialization with default configuration."""
        handler = SSLHandler()
        
        assert handler.verify_ssl is True
        assert handler.ca_cert_path is None
    
    def test_init_custom_config(self):
        """Test SSL handler initialization with custom configuration."""
        handler = SSLHandler(verify_ssl=False, ca_cert_path="/path/to/cert.pem")
        
        assert handler.verify_ssl is False
        assert handler.ca_cert_path == "/path/to/cert.pem"
    
    def test_get_ssl_context_disabled(self):
        """Test SSL context when SSL verification is disabled."""
        handler = SSLHandler(verify_ssl=False)
        
        context = handler.get_ssl_context()
        
        assert context is False
    
    def test_get_ssl_context_default(self):
        """Test SSL context with default configuration."""
        handler = SSLHandler(verify_ssl=True)
        
        context = handler.get_ssl_context()
        
        assert isinstance(context, ssl.SSLContext)
    
    @patch('pathlib.Path.exists')
    @patch('ssl.SSLContext.load_verify_locations')
    def test_get_ssl_context_custom_ca(self, mock_load_verify, mock_exists):
        """Test SSL context with custom CA certificate."""
        mock_exists.return_value = True
        handler = SSLHandler(verify_ssl=True, ca_cert_path="/path/to/cert.pem")
        
        context = handler.get_ssl_context()
        
        assert isinstance(context, ssl.SSLContext)
        mock_load_verify.assert_called_once_with("/path/to/cert.pem")
    
    @patch('pathlib.Path.exists')
    def test_get_ssl_context_ca_not_found(self, mock_exists):
        """Test SSL context when CA certificate file doesn't exist."""
        mock_exists.return_value = False
        handler = SSLHandler(verify_ssl=True, ca_cert_path="/nonexistent/cert.pem")
        
        with pytest.raises(FileNotFoundError, match="CA certificate file not found"):
            handler.get_ssl_context()
    
    @patch('pathlib.Path.exists')
    @patch('ssl.SSLContext.load_verify_locations')
    def test_get_ssl_context_invalid_ca(self, mock_load_verify, mock_exists):
        """Test SSL context with invalid CA certificate."""
        mock_exists.return_value = True
        mock_load_verify.side_effect = ssl.SSLError("Invalid certificate")
        handler = SSLHandler(verify_ssl=True, ca_cert_path="/path/to/invalid.pem")
        
        with pytest.raises(ValueError, match="Invalid CA certificate file"):
            handler.get_ssl_context()
    
    def test_get_httpx_verify_config_disabled(self):
        """Test httpx verify configuration when SSL is disabled."""
        handler = SSLHandler(verify_ssl=False)
        
        config = handler.get_httpx_verify_config()
        
        assert config is False
    
    def test_get_httpx_verify_config_default(self):
        """Test httpx verify configuration with default settings."""
        handler = SSLHandler(verify_ssl=True)
        
        config = handler.get_httpx_verify_config()
        
        assert config is True
    
    @patch('pathlib.Path.exists')
    def test_get_httpx_verify_config_custom_ca(self, mock_exists):
        """Test httpx verify configuration with custom CA."""
        mock_exists.return_value = True
        handler = SSLHandler(verify_ssl=True, ca_cert_path="/path/to/cert.pem")
        
        config = handler.get_httpx_verify_config()
        
        assert config == "/path/to/cert.pem"
    
    @patch('pathlib.Path.exists')
    def test_get_httpx_verify_config_ca_not_found(self, mock_exists):
        """Test httpx verify configuration when CA file doesn't exist."""
        mock_exists.return_value = False
        handler = SSLHandler(verify_ssl=True, ca_cert_path="/nonexistent/cert.pem")
        
        with pytest.raises(FileNotFoundError, match="CA certificate file not found"):
            handler.get_httpx_verify_config()
    
    @pytest.mark.asyncio
    async def test_validate_ssl_certificate_http_url(self):
        """Test SSL validation for HTTP URL (no SSL to validate)."""
        handler = SSLHandler()
        
        result = await handler.validate_ssl_certificate("http://example.com")
        
        assert result.is_valid is True
        assert "HTTP" in result.error_message
    
    @pytest.mark.asyncio
    async def test_validate_ssl_certificate_invalid_hostname(self):
        """Test SSL validation with invalid hostname."""
        handler = SSLHandler()
        
        result = await handler.validate_ssl_certificate("https://")
        
        assert result.is_valid is False
        assert result.error_type == "invalid_hostname"
        assert "Invalid hostname" in result.error_message
    
    @pytest.mark.asyncio
    @patch('app.services.ssl_handler.SSLHandler._get_certificate_info')
    async def test_validate_ssl_certificate_no_cert_info(self, mock_get_cert):
        """Test SSL validation when certificate info cannot be retrieved."""
        mock_get_cert.return_value = None
        handler = SSLHandler()
        
        result = await handler.validate_ssl_certificate("https://example.com")
        
        assert result.is_valid is False
        assert result.error_type == "certificate_retrieval_failed"
        assert "Could not retrieve certificate" in result.error_message
    
    @pytest.mark.asyncio
    @patch('app.services.ssl_handler.SSLHandler._get_certificate_info')
    @patch('app.services.ssl_handler.SSLHandler._validate_certificate_with_config')
    async def test_validate_ssl_certificate_success(self, mock_validate_config, mock_get_cert):
        """Test successful SSL certificate validation."""
        mock_cert_info = SSLCertificateInfo(
            subject={"commonName": "example.com"},
            issuer={"commonName": "Test CA"},
            version=3,
            serial_number="123456",
            not_before="Jan 1 00:00:00 2024 GMT",
            not_after="Jan 1 00:00:00 2025 GMT",
            is_expired=False,
            is_self_signed=False,
            signature_algorithm="sha256WithRSAEncryption",
            public_key_algorithm="RSA"
        )
        mock_get_cert.return_value = mock_cert_info
        mock_validate_config.return_value = None  # No validation error
        
        handler = SSLHandler()
        result = await handler.validate_ssl_certificate("https://example.com")
        
        assert result.is_valid is True
        assert result.certificate_info == mock_cert_info
    
    @pytest.mark.asyncio
    @patch('app.services.ssl_handler.SSLHandler._get_certificate_info')
    @patch('app.services.ssl_handler.SSLHandler._validate_certificate_with_config')
    async def test_validate_ssl_certificate_validation_error(self, mock_validate_config, mock_get_cert):
        """Test SSL certificate validation with configuration error."""
        mock_cert_info = SSLCertificateInfo(
            subject={"commonName": "example.com"},
            issuer={"commonName": "Test CA"},
            version=3,
            serial_number="123456",
            not_before="Jan 1 00:00:00 2024 GMT",
            not_after="Jan 1 00:00:00 2025 GMT",
            is_expired=False,
            is_self_signed=False,
            signature_algorithm="sha256WithRSAEncryption",
            public_key_algorithm="RSA"
        )
        mock_get_cert.return_value = mock_cert_info
        mock_validate_config.return_value = {
            "message": "Certificate verification failed",
            "type": "certificate_verification_failed",
            "troubleshooting_steps": ["Check certificate validity"]
        }
        
        handler = SSLHandler()
        result = await handler.validate_ssl_certificate("https://example.com")
        
        assert result.is_valid is False
        assert result.certificate_info == mock_cert_info
        assert result.error_type == "certificate_verification_failed"
        assert "Certificate verification failed" in result.error_message
    
    @pytest.mark.asyncio
    @patch('socket.create_connection')
    @patch('ssl.create_default_context')
    async def test_get_certificate_info_success(self, mock_ssl_context, mock_socket):
        """Test successful certificate information retrieval."""
        # Mock certificate data
        mock_cert = {
            'subject': (('commonName', 'example.com'),),
            'issuer': (('commonName', 'Test CA'),),
            'version': 3,
            'serialNumber': '123456',
            'notBefore': 'Jan  1 00:00:00 2024 GMT',
            'notAfter': 'Jan  1 00:00:00 2025 GMT',
            'signatureAlgorithm': 'sha256WithRSAEncryption'
        }
        
        # Mock SSL socket
        mock_ssl_socket = Mock()
        mock_ssl_socket.getpeercert.return_value = mock_cert
        mock_ssl_socket.getpeercert.side_effect = [mock_cert, b'cert_data']
        
        # Mock wrapped socket context manager
        mock_wrapped_socket = Mock()
        mock_wrapped_socket.__enter__ = Mock(return_value=mock_ssl_socket)
        mock_wrapped_socket.__exit__ = Mock(return_value=None)
        
        # Mock SSL context
        mock_context_instance = Mock()
        mock_context_instance.wrap_socket.return_value = mock_wrapped_socket
        mock_ssl_context.return_value = mock_context_instance
        
        # Mock regular socket context manager
        mock_socket_instance = Mock()
        mock_socket_cm = Mock()
        mock_socket_cm.__enter__ = Mock(return_value=mock_socket_instance)
        mock_socket_cm.__exit__ = Mock(return_value=None)
        mock_socket.return_value = mock_socket_cm
        
        handler = SSLHandler()
        cert_info = await handler._get_certificate_info("example.com", 443)
        
        assert cert_info is not None
        assert cert_info.subject["commonName"] == "example.com"
        assert cert_info.issuer["commonName"] == "Test CA"
        assert cert_info.is_self_signed is False
    
    @pytest.mark.asyncio
    @patch('socket.create_connection')
    async def test_get_certificate_info_connection_error(self, mock_socket):
        """Test certificate info retrieval with connection error."""
        mock_socket.side_effect = ConnectionError("Connection failed")
        
        handler = SSLHandler()
        cert_info = await handler._get_certificate_info("example.com", 443)
        
        assert cert_info is None
    
    def test_get_ssl_troubleshooting_steps(self):
        """Test SSL troubleshooting steps for different error types."""
        handler = SSLHandler()
        
        # Test certificate verification failed
        steps = handler.get_ssl_troubleshooting_steps("certificate_verification_failed")
        assert any("certificate chain" in step.lower() for step in steps)
        
        # Test hostname mismatch
        steps = handler.get_ssl_troubleshooting_steps("hostname_mismatch")
        assert any("hostname" in step.lower() for step in steps)
        
        # Test self-signed certificate
        steps = handler.get_ssl_troubleshooting_steps("self_signed_certificate")
        assert any("self-signed" in step.lower() for step in steps)
        
        # Test unknown error type
        steps = handler.get_ssl_troubleshooting_steps("unknown_error")
        assert len(steps) > 0
    
    def test_suggest_ssl_config_for_error(self):
        """Test SSL configuration suggestions for different error types."""
        handler = SSLHandler()
        
        # Test self-signed certificate
        config = handler.suggest_ssl_config_for_error("self_signed_certificate", "https://example.com")
        assert "ca_cert_path" in config
        assert config["verify_ssl"] is True
        
        # Test certificate verification failed
        config = handler.suggest_ssl_config_for_error("certificate_verification_failed", "https://example.com")
        assert "ca_cert_path" in config
        
        # Test localhost URL
        config = handler.suggest_ssl_config_for_error("self_signed_certificate", "https://localhost:8443")
        assert "testing_only" in config
        assert config["testing_only"]["verify_ssl"] is False
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('builtins.open')
    @patch('ssl.create_default_context')
    def test_validate_ca_certificate_file_success(self, mock_ssl_context, mock_open, mock_is_file, mock_exists):
        """Test successful CA certificate file validation."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = (
            "-----BEGIN CERTIFICATE-----\ntest_cert_data\n-----END CERTIFICATE-----"
        )
        mock_context = Mock()
        mock_ssl_context.return_value = mock_context
        
        is_valid, error = SSLHandler.validate_ca_certificate_file("/path/to/cert.pem")
        
        assert is_valid is True
        assert error is None
        mock_context.load_verify_locations.assert_called_once()
    
    @patch('pathlib.Path.exists')
    def test_validate_ca_certificate_file_not_exists(self, mock_exists):
        """Test CA certificate file validation when file doesn't exist."""
        mock_exists.return_value = False
        
        is_valid, error = SSLHandler.validate_ca_certificate_file("/nonexistent/cert.pem")
        
        assert is_valid is False
        assert "does not exist" in error
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    def test_validate_ca_certificate_file_not_file(self, mock_is_file, mock_exists):
        """Test CA certificate file validation when path is not a file."""
        mock_exists.return_value = True
        mock_is_file.return_value = False
        
        is_valid, error = SSLHandler.validate_ca_certificate_file("/path/to/directory")
        
        assert is_valid is False
        assert "not a file" in error
    
    @patch('pathlib.Path.exists')
    @patch('pathlib.Path.is_file')
    @patch('builtins.open')
    def test_validate_ca_certificate_file_invalid_format(self, mock_open, mock_is_file, mock_exists):
        """Test CA certificate file validation with invalid format."""
        mock_exists.return_value = True
        mock_is_file.return_value = True
        mock_open.return_value.__enter__.return_value.read.return_value = "invalid certificate data"
        
        is_valid, error = SSLHandler.validate_ca_certificate_file("/path/to/invalid.pem")
        
        assert is_valid is False
        assert "PEM format" in error
    
    @patch('certifi.where')
    def test_get_system_ca_bundle_path(self, mock_certifi_where):
        """Test getting system CA bundle path."""
        mock_certifi_where.return_value = "/system/ca-bundle.pem"
        
        path = SSLHandler.get_system_ca_bundle_path()
        
        assert path == "/system/ca-bundle.pem"
        mock_certifi_where.assert_called_once()


class TestSSLCertificateInfo:
    """Test cases for SSL certificate info model."""
    
    def test_ssl_certificate_info_creation(self):
        """Test SSL certificate info model creation."""
        cert_info = SSLCertificateInfo(
            subject={"commonName": "example.com"},
            issuer={"commonName": "Test CA"},
            version=3,
            serial_number="123456",
            not_before="Jan 1 00:00:00 2024 GMT",
            not_after="Jan 1 00:00:00 2025 GMT",
            is_expired=False,
            is_self_signed=False,
            signature_algorithm="sha256WithRSAEncryption",
            public_key_algorithm="RSA"
        )
        
        assert cert_info.subject["commonName"] == "example.com"
        assert cert_info.issuer["commonName"] == "Test CA"
        assert cert_info.is_expired is False
        assert cert_info.is_self_signed is False


class TestSSLValidationResult:
    """Test cases for SSL validation result model."""
    
    def test_ssl_validation_result_success(self):
        """Test SSL validation result for successful validation."""
        cert_info = SSLCertificateInfo(
            subject={"commonName": "example.com"},
            issuer={"commonName": "Test CA"},
            version=3,
            serial_number="123456",
            not_before="Jan 1 00:00:00 2024 GMT",
            not_after="Jan 1 00:00:00 2025 GMT",
            is_expired=False,
            is_self_signed=False,
            signature_algorithm="sha256WithRSAEncryption",
            public_key_algorithm="RSA"
        )
        
        result = SSLValidationResult(
            is_valid=True,
            certificate_info=cert_info
        )
        
        assert result.is_valid is True
        assert result.certificate_info == cert_info
        assert result.error_message is None
    
    def test_ssl_validation_result_failure(self):
        """Test SSL validation result for failed validation."""
        result = SSLValidationResult(
            is_valid=False,
            error_message="Certificate verification failed",
            error_type="certificate_verification_failed",
            troubleshooting_steps=["Check certificate validity"]
        )
        
        assert result.is_valid is False
        assert result.error_message == "Certificate verification failed"
        assert result.error_type == "certificate_verification_failed"
        assert len(result.troubleshooting_steps) == 1