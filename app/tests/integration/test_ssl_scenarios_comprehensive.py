"""Comprehensive integration tests for SSL scenarios.

This module provides integration tests for SSL functionality including:
- Connection with SSL verification enabled and valid certificate
- Connection with SSL verification disabled and self-signed certificate
- Error handling with SSL verification enabled and invalid certificate
- SSL setting changes taking effect immediately
"""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock
import httpx

from app.config import JiraConfig
from app.services.jira import JiraService
from app.services.ssl_handler import SSLHandler, SSLCertificateInfo


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


class TestSSLConnectionWithValidCertificate:
    """Test SSL connection scenarios with valid certificates."""

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_ssl_enabled_valid_certificate_success(self, mock_client):
        """Test successful connection with SSL verification enabled and valid certificate."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serverTitle": "Test JIRA",
            "version": "9.12.0",
            "deploymentType": "Server",
        }

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Configure JIRA service with SSL enabled
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None,
        )

        service = JiraService(config)

        # Test connection through deployment detector
        deployment_info = await service.deployment_detector.detect_deployment(
            "https://jira.example.com", {}
        )

        # Verify SSL configuration was used correctly
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert "verify" in call_args.kwargs
        assert call_args.kwargs["verify"] is True

        # Verify successful deployment detection
        assert deployment_info is not None
        assert deployment_info.server_title == "Test JIRA"
        assert deployment_info.version == "9.12.0"

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_ssl_enabled_custom_ca_success(self, mock_client):
        """Test successful connection with SSL verification enabled and custom CA certificate."""
        # Create temporary CA certificate file
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            ca_cert_path = f.name

        try:
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "serverTitle": "Test JIRA Data Center",
                "version": "9.12.0",
                "deploymentType": "DataCenter",
            }

            mock_client_instance = Mock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Configure JIRA service with SSL enabled and custom CA
            config = JiraConfig(
                base_url="https://jira.company.com",
                username="testuser",
                password="testpass",
                verify_ssl=True,
                ca_cert_path=ca_cert_path,
            )

            service = JiraService(config)

            # Test connection through deployment detector
            deployment_info = await service.deployment_detector.detect_deployment(
                "https://jira.company.com", {}
            )

            # Verify SSL configuration was used correctly with custom CA
            mock_client.assert_called()
            call_args = mock_client.call_args
            assert "verify" in call_args.kwargs
            assert call_args.kwargs["verify"] == ca_cert_path

            # Verify successful deployment detection
            assert deployment_info is not None
            assert deployment_info.server_title == "Test JIRA Data Center"
            assert deployment_info.version == "9.12.0"
        finally:
            # Clean up temporary file
            Path(ca_cert_path).unlink(missing_ok=True)

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_api_version_manager_ssl_enabled_success(self, mock_client):
        """Test API version manager with SSL verification enabled."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "3"}

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Configure JIRA service with SSL enabled
        config = JiraConfig(
            base_url="https://jira.example.com",
            personal_access_token="test-pat",
            verify_ssl=True,
            ca_cert_path=None,
        )

        service = JiraService(config)

        # Test API version check
        await service.api_version_manager.test_api_version(
            "https://jira.example.com", {}, "3"
        )

        # Verify SSL configuration was used correctly
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert "verify" in call_args.kwargs
        assert call_args.kwargs["verify"] is True

    @pytest.mark.asyncio
    async def test_ssl_certificate_validation_success(self):
        """Test SSL certificate validation with valid certificate scenario."""
        # Create SSL handler with verification enabled
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)

        # Mock successful certificate validation
        with patch.object(
            handler, "_get_certificate_info"
        ) as mock_get_cert, patch.object(
            handler, "_validate_certificate_with_config"
        ) as mock_validate:

            # Mock certificate info
            mock_cert_info = SSLCertificateInfo(
                subject={"commonName": "jira.example.com"},
                issuer={"commonName": "Valid CA"},
                version=3,
                serial_number="123456789",
                not_before="Jan 1 00:00:00 2024 GMT",
                not_after="Jan 1 00:00:00 2025 GMT",
                is_expired=False,
                is_self_signed=False,
                signature_algorithm="sha256WithRSAEncryption",
                public_key_algorithm="RSA",
            )
            mock_get_cert.return_value = mock_cert_info
            mock_validate.return_value = None  # No validation error

            # Validate SSL certificate
            result = await handler.validate_ssl_certificate("https://jira.example.com")

            # Verify successful validation
            assert result.is_valid is True
            assert result.certificate_info == mock_cert_info
            assert result.error_message is None
            assert result.error_type is None


class TestSSLConnectionWithSelfSignedCertificate:
    """Test SSL connection scenarios with self-signed certificates."""

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_ssl_disabled_self_signed_success(self, mock_client):
        """Test successful connection with SSL verification disabled and self-signed certificate."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "serverTitle": "Internal JIRA",
            "version": "9.12.0",
            "deploymentType": "Server",
        }

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Configure JIRA service with SSL disabled for self-signed certificate
        config = JiraConfig(
            base_url="https://jira.internal.com",
            username="testuser",
            password="testpass",
            verify_ssl=False,
            ca_cert_path=None,
        )

        service = JiraService(config)

        # Test connection through deployment detector
        deployment_info = await service.deployment_detector.detect_deployment(
            "https://jira.internal.com", {}
        )

        # Verify SSL verification was disabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert "verify" in call_args.kwargs
        assert call_args.kwargs["verify"] is False

        # Verify successful deployment detection despite self-signed certificate
        assert deployment_info is not None
        assert deployment_info.server_title == "Internal JIRA"
        assert deployment_info.version == "9.12.0"

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_ssl_disabled_with_ca_path_success(self, mock_client):
        """Test connection with SSL disabled but CA path provided (should ignore CA path)."""
        # Create temporary CA certificate file (should be ignored)
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f:
            f.write(SAMPLE_CERT_PEM)
            ca_cert_path = f.name

        try:
            # Mock successful HTTP response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "serverTitle": "Internal JIRA",
                "version": "9.12.0",
            }

            mock_client_instance = Mock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Configure JIRA service with SSL disabled but CA path provided
            config = JiraConfig(
                base_url="https://jira.internal.com",
                email="test@example.com",
                api_token="test-token",
                verify_ssl=False,
                ca_cert_path=ca_cert_path,  # Should be ignored when SSL is disabled
            )

            service = JiraService(config)

            # Test connection
            deployment_info = await service.deployment_detector.detect_deployment(
                "https://jira.internal.com", {}
            )

            # Verify SSL verification was disabled (CA path ignored)
            mock_client.assert_called()
            call_args = mock_client.call_args
            assert "verify" in call_args.kwargs
            assert call_args.kwargs["verify"] is False  # Not the CA path

            # Verify successful connection
            assert deployment_info is not None
        finally:
            # Clean up temporary file
            Path(ca_cert_path).unlink(missing_ok=True)

    @pytest.mark.asyncio
    async def test_ssl_certificate_validation_self_signed_with_disabled_verification(
        self,
    ):
        """Test SSL certificate validation with self-signed certificate and disabled verification."""
        # Create SSL handler with verification disabled
        handler = SSLHandler(verify_ssl=False, ca_cert_path=None)

        # Mock certificate info for self-signed certificate
        with patch.object(
            handler, "_get_certificate_info"
        ) as mock_get_cert, patch.object(
            handler, "_validate_certificate_with_config"
        ) as mock_validate:

            # Mock self-signed certificate info
            mock_cert_info = SSLCertificateInfo(
                subject={"commonName": "jira.internal.com"},
                issuer={
                    "commonName": "jira.internal.com"
                },  # Same as subject = self-signed
                version=3,
                serial_number="987654321",
                not_before="Jan 1 00:00:00 2024 GMT",
                not_after="Jan 1 00:00:00 2025 GMT",
                is_expired=False,
                is_self_signed=True,
                signature_algorithm="sha256WithRSAEncryption",
                public_key_algorithm="RSA",
            )
            mock_get_cert.return_value = mock_cert_info
            mock_validate.return_value = None  # No validation error when SSL disabled

            # Validate SSL certificate
            result = await handler.validate_ssl_certificate("https://jira.internal.com")

            # Should succeed because SSL verification is disabled
            assert result.is_valid is True
            assert result.certificate_info == mock_cert_info
            assert result.certificate_info.is_self_signed is True


class TestSSLConnectionWithInvalidCertificate:
    """Test SSL connection scenarios with invalid certificates."""

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_ssl_enabled_invalid_certificate_failure(
        self, mock_client
    ):
        """Test connection failure with SSL verification enabled and invalid certificate."""
        # Mock SSL certificate verification failure
        ssl_error = httpx.ConnectError(
            "SSL: CERTIFICATE_VERIFY_FAILED certificate verify failed: self signed certificate"
        )

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(side_effect=ssl_error)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Configure JIRA service with SSL enabled
        config = JiraConfig(
            base_url="https://jira.invalid-cert.com",
            username="testuser",
            password="testpass",
            verify_ssl=True,
            ca_cert_path=None,
        )

        service = JiraService(config)

        # Test connection should fail
        with pytest.raises(
            Exception
        ):  # DeploymentDetectionError wraps the ConnectError
            await service.deployment_detector.detect_deployment(
                "https://jira.invalid-cert.com", {}
            )

        # Verify SSL verification was enabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert "verify" in call_args.kwargs
        assert call_args.kwargs["verify"] is True

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_ssl_enabled_hostname_mismatch_failure(self, mock_client):
        """Test connection failure with SSL verification enabled and hostname mismatch."""
        # Mock SSL hostname mismatch error
        ssl_error = httpx.ConnectError(
            "SSL: CERTIFICATE_VERIFY_FAILED certificate verify failed: hostname mismatch"
        )

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(side_effect=ssl_error)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Configure JIRA service with SSL enabled
        config = JiraConfig(
            base_url="https://192.168.1.100:8443",  # IP address causing hostname mismatch
            personal_access_token="test-pat",
            verify_ssl=True,
            ca_cert_path=None,
        )

        service = JiraService(config)

        # Test connection should fail and return False
        result = await service.api_version_manager.test_api_version(
            "https://192.168.1.100:8443", {}, "3"
        )

        # Should return False due to SSL error
        assert result is False

        # Verify SSL verification was enabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert "verify" in call_args.kwargs
        assert call_args.kwargs["verify"] is True

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_ssl_enabled_expired_certificate_failure(
        self, mock_client
    ):
        """Test connection failure with SSL verification enabled and expired certificate."""
        # Mock SSL expired certificate error
        ssl_error = httpx.ConnectError(
            "SSL: CERTIFICATE_VERIFY_FAILED certificate verify failed: certificate has expired"
        )

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(side_effect=ssl_error)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Configure JIRA service with SSL enabled
        config = JiraConfig(
            base_url="https://jira.expired-cert.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None,
        )

        service = JiraService(config)

        # Test connection should fail
        with pytest.raises(
            Exception
        ):  # DeploymentDetectionError wraps the ConnectError
            await service.deployment_detector.detect_deployment(
                "https://jira.expired-cert.com", {}
            )

        # Verify SSL verification was enabled
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert "verify" in call_args.kwargs
        assert call_args.kwargs["verify"] is True

    @pytest.mark.asyncio
    async def test_ssl_certificate_validation_invalid_certificate_error_handling(self):
        """Test SSL certificate validation error handling with invalid certificate."""
        # Create SSL handler with verification enabled
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)

        # Mock certificate validation failure
        with patch.object(
            handler, "_get_certificate_info"
        ) as mock_get_cert, patch.object(
            handler, "_validate_certificate_with_config"
        ) as mock_validate:

            # Mock certificate info for invalid certificate
            mock_cert_info = SSLCertificateInfo(
                subject={"commonName": "jira.invalid.com"},
                issuer={"commonName": "Invalid CA"},
                version=3,
                serial_number="000000000",
                not_before="Jan 1 00:00:00 2020 GMT",
                not_after="Jan 1 00:00:00 2021 GMT",  # Expired
                is_expired=True,
                is_self_signed=False,
                signature_algorithm="sha256WithRSAEncryption",
                public_key_algorithm="RSA",
            )
            mock_get_cert.return_value = mock_cert_info

            # Mock validation error
            mock_validate.return_value = {
                "message": "SSL certificate verification failed - certificate has expired",
                "type": "certificate_expired",
                "troubleshooting_steps": [
                    "Renew the SSL certificate on the server",
                    "Check the certificate expiration date",
                    "Contact your system administrator",
                ],
            }

            # Validate SSL certificate
            result = await handler.validate_ssl_certificate("https://jira.invalid.com")

            # Should fail with detailed error information
            assert result.is_valid is False
            assert result.certificate_info == mock_cert_info
            assert result.error_type == "certificate_expired"
            assert "certificate has expired" in result.error_message
            assert len(result.troubleshooting_steps) > 0


class TestSSLSettingChangesImmediate:
    """Test that SSL setting changes take effect immediately."""

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_ssl_setting_change_takes_effect_immediately(self, mock_client):
        """Test that SSL setting changes take effect immediately for subsequent API calls."""
        # Mock HTTP responses
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "9.12.0"}

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Start with SSL enabled
        config = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None,
        )

        service = JiraService(config)

        # First call with SSL enabled
        await service.deployment_detector.detect_deployment(
            "https://jira.example.com", {}
        )

        # Verify first call used SSL verification
        first_call_args = mock_client.call_args
        assert first_call_args.kwargs["verify"] is True

        # Reset mock to track next call
        mock_client.reset_mock()

        # Change SSL setting to disabled
        config.verify_ssl = False

        # Create new service with updated config
        service_updated = JiraService(config)

        # Second call with SSL disabled
        await service_updated.deployment_detector.detect_deployment(
            "https://jira.example.com", {}
        )

        # Verify second call used disabled SSL verification
        second_call_args = mock_client.call_args
        assert second_call_args.kwargs["verify"] is False

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_ca_certificate_change_takes_effect_immediately(self, mock_client):
        """Test that CA certificate changes take effect immediately."""
        # Create temporary CA certificate files
        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f1:
            f1.write(SAMPLE_CERT_PEM)
            ca_cert_path_1 = f1.name

        with tempfile.NamedTemporaryFile(mode="w", suffix=".pem", delete=False) as f2:
            f2.write(SAMPLE_CERT_PEM)
            ca_cert_path_2 = f2.name

        try:
            # Mock HTTP responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"version": "3"}

            mock_client_instance = Mock()
            mock_client_instance.get = AsyncMock(return_value=mock_response)
            mock_client.return_value.__aenter__ = AsyncMock(
                return_value=mock_client_instance
            )
            mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

            # Start with first CA certificate
            config = JiraConfig(
                base_url="https://jira.example.com",
                username="testuser",
                password="testpass",
                verify_ssl=True,
                ca_cert_path=ca_cert_path_1,
            )

            service = JiraService(config)

            # First call with first CA certificate
            await service.api_version_manager.test_api_version(
                "https://jira.example.com", "3", {}
            )

            # Verify first call used first CA certificate
            first_call_args = mock_client.call_args
            assert first_call_args.kwargs["verify"] == ca_cert_path_1

            # Reset mock to track next call
            mock_client.reset_mock()

            # Change CA certificate
            config.ca_cert_path = ca_cert_path_2

            # Create new service with updated config
            service_updated = JiraService(config)

            # Second call with second CA certificate
            await service_updated.api_version_manager.test_api_version(
                "https://jira.example.com", "3", {}
            )

            # Verify second call used second CA certificate
            second_call_args = mock_client.call_args
            assert second_call_args.kwargs["verify"] == ca_cert_path_2
        finally:
            # Clean up temporary files
            Path(ca_cert_path_1).unlink(missing_ok=True)
            Path(ca_cert_path_2).unlink(missing_ok=True)

    def test_ssl_handler_configuration_update_immediate(self):
        """Test that SSL handler configuration updates are immediate."""
        # Create SSL handler with initial configuration
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)

        # Verify initial configuration
        assert handler.verify_ssl is True
        assert handler.ca_cert_path is None
        assert handler.get_httpx_verify_config() is True

        # Create new handler with different configuration
        handler_updated = SSLHandler(verify_ssl=False, ca_cert_path="/path/to/ca.pem")

        # Verify updated configuration is immediate
        assert handler_updated.verify_ssl is False
        assert handler_updated.ca_cert_path == "/path/to/ca.pem"
        assert handler_updated.get_httpx_verify_config() is False

    def test_jira_service_ssl_configuration_update_immediate(self):
        """Test that JiraService SSL configuration updates are immediate."""
        # Create initial configuration
        config1 = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=True,
            ca_cert_path=None,
        )

        service1 = JiraService(config1)

        # Verify initial SSL configuration
        assert service1.ssl_handler.verify_ssl is True
        assert service1.ssl_handler.ca_cert_path is None
        assert service1.deployment_detector.verify_ssl is True
        assert service1.api_version_manager.verify_ssl is True

        # Create updated configuration
        config2 = JiraConfig(
            base_url="https://jira.example.com",
            email="test@example.com",
            api_token="test-token",
            verify_ssl=False,
            ca_cert_path="/path/to/ca.pem",
        )

        service2 = JiraService(config2)

        # Verify updated SSL configuration is immediate
        assert service2.ssl_handler.verify_ssl is False
        assert service2.ssl_handler.ca_cert_path == "/path/to/ca.pem"
        assert service2.deployment_detector.verify_ssl is False
        assert service2.deployment_detector.ca_cert_path == "/path/to/ca.pem"
        assert service2.api_version_manager.verify_ssl is False
        assert service2.api_version_manager.ca_cert_path == "/path/to/ca.pem"


class TestSSLIntegrationEdgeCases:
    """Test edge cases for SSL integration scenarios."""

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_connection_with_proxy_and_ssl_disabled(self, mock_client):
        """Test connection with proxy configuration and SSL disabled."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "9.12.0"}

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        # Configure JIRA service with proxy and SSL disabled
        config = JiraConfig(
            base_url="https://jira.internal.com",
            username="testuser",
            password="testpass",
            verify_ssl=False,
            ca_cert_path=None,
            proxy_url="http://proxy.company.com:8080",
        )

        service = JiraService(config)

        # Test connection
        await service.deployment_detector.detect_deployment(
            "https://jira.internal.com", {}
        )

        # Verify both SSL and proxy configuration
        mock_client.assert_called()
        call_args = mock_client.call_args
        assert "verify" in call_args.kwargs
        assert call_args.kwargs["verify"] is False
        # Note: Proxy configuration would be handled by the deployment detector

    @pytest.mark.asyncio
    async def test_ssl_validation_with_http_url(self):
        """Test SSL validation with HTTP URL (no SSL to validate)."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)

        # Validate HTTP URL (no SSL)
        result = await handler.validate_ssl_certificate("http://jira.example.com")

        # Should succeed because there's no SSL to validate
        assert result.is_valid is True
        assert "HTTP" in result.error_message
        assert result.certificate_info is None

    @pytest.mark.asyncio
    async def test_ssl_validation_with_invalid_hostname(self):
        """Test SSL validation with invalid hostname."""
        handler = SSLHandler(verify_ssl=True, ca_cert_path=None)

        # Validate invalid URL
        result = await handler.validate_ssl_certificate("https://")

        # Should fail with hostname error
        assert result.is_valid is False
        assert result.error_type == "invalid_hostname"
        assert "Invalid hostname" in result.error_message
        assert len(result.troubleshooting_steps) > 0

    @patch("httpx.AsyncClient")
    @pytest.mark.asyncio
    async def test_multiple_authentication_methods_same_ssl_config(self, mock_client):
        """Test that multiple authentication methods use the same SSL configuration."""
        # Mock successful HTTP response
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"version": "9.12.0"}

        mock_client_instance = Mock()
        mock_client_instance.get = AsyncMock(return_value=mock_response)
        mock_client.return_value.__aenter__ = AsyncMock(
            return_value=mock_client_instance
        )
        mock_client.return_value.__aexit__ = AsyncMock(return_value=None)

        ssl_config = {"verify_ssl": False, "ca_cert_path": None}

        # Test with different authentication methods
        configs = [
            JiraConfig(
                base_url="https://jira.example.com",
                email="test@example.com",
                api_token="test-token",
                **ssl_config
            ),
            JiraConfig(
                base_url="https://jira.example.com",
                personal_access_token="test-pat",
                **ssl_config
            ),
            JiraConfig(
                base_url="https://jira.example.com",
                username="testuser",
                password="testpass",
                **ssl_config
            ),
        ]

        for config in configs:
            mock_client.reset_mock()

            service = JiraService(config)

            # Test connection
            await service.deployment_detector.detect_deployment(
                "https://jira.example.com", {}
            )

            # Verify SSL configuration is consistent
            call_args = mock_client.call_args
            assert "verify" in call_args.kwargs
            assert call_args.kwargs["verify"] is False

    def test_ssl_configuration_info_across_different_scenarios(self):
        """Test SSL configuration information reporting across different scenarios."""
        scenarios = [
            # SSL enabled, no CA
            {
                "config": {"verify_ssl": True, "ca_cert_path": None},
                "expected_security_level": "HIGH",
                "expected_warnings_count": 0,
            },
            # SSL disabled, no CA
            {
                "config": {"verify_ssl": False, "ca_cert_path": None},
                "expected_security_level": "LOW",
                "expected_warnings_count": 4,  # Multiple security warnings
            },
            # SSL enabled, with CA (file doesn't exist)
            {
                "config": {"verify_ssl": True, "ca_cert_path": "/nonexistent/ca.pem"},
                "expected_security_level": "HIGH",
                "expected_warnings_count": 1,  # Warning about missing CA file
            },
        ]

        for scenario in scenarios:
            handler = SSLHandler(**scenario["config"])
            config_info = handler.get_ssl_configuration_info()

            assert config_info["security_level"] == scenario["expected_security_level"]
            assert len(config_info["warnings"]) >= scenario["expected_warnings_count"]
