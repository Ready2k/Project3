"""
Unit tests for Jira diagnostics and validation utilities.
"""

import pytest
import socket
import ssl
from unittest.mock import Mock, patch
import httpx

from app.services.jira_diagnostics import (
    JiraDiagnostics,
    DiagnosticStatus,
    DiagnosticResult,
    NetworkConnectivityResult,
    ConfigurationValidationResult,
    VersionCompatibilityResult,
    AuthMethodAvailabilityResult,
    create_jira_diagnostics
)
from app.config import JiraConfig, JiraAuthType, JiraDeploymentType


class TestJiraDiagnostics:
    """Test cases for JiraDiagnostics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.config = JiraConfig(
            base_url="https://jira.example.com:8443",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            deployment_type=JiraDeploymentType.DATA_CENTER,
            personal_access_token="test-pat-token",
            verify_ssl=True,
            timeout=30
        )
        self.diagnostics = JiraDiagnostics(self.config)
    
    def test_init(self):
        """Test JiraDiagnostics initialization."""
        assert self.diagnostics.config == self.config
        assert self.diagnostics.timeout == 30
        assert self.diagnostics.error_handler is not None
    
    @pytest.mark.asyncio
    async def test_run_full_diagnostics(self):
        """Test running full diagnostic suite."""
        with patch.object(self.diagnostics, '_run_diagnostic_check') as mock_check:
            # Mock all diagnostic checks to return PASS
            mock_check.return_value = DiagnosticResult(
                name="Test Check",
                status=DiagnosticStatus.PASS,
                message="Test passed"
            )
            
            results = await self.diagnostics.run_full_diagnostics()
            
            # Should run multiple checks
            assert len(results) >= 4  # At minimum: config, network, ssl, dns
            assert all(isinstance(result, DiagnosticResult) for result in results)
            
            # Verify specific checks were called
            check_names = [call[0][0] for call in mock_check.call_args_list]
            assert "Configuration Validation" in check_names
            assert "Network Connectivity" in check_names
            assert "SSL/TLS Certificate" in check_names
            assert "DNS Resolution" in check_names
    
    @pytest.mark.asyncio
    async def test_run_diagnostic_check_success(self):
        """Test successful diagnostic check execution."""
        async def mock_check():
            return DiagnosticResult(
                name="Test Check",
                status=DiagnosticStatus.PASS,
                message="Check passed"
            )
        
        result = await self.diagnostics._run_diagnostic_check("Test Check", mock_check)
        
        assert result.name == "Test Check"
        assert result.status == DiagnosticStatus.PASS
        assert result.message == "Check passed"
        assert result.duration_ms is not None
        assert result.duration_ms >= 0
    
    @pytest.mark.asyncio
    async def test_run_diagnostic_check_failure(self):
        """Test diagnostic check with exception handling."""
        async def mock_check():
            raise Exception("Test error")
        
        result = await self.diagnostics._run_diagnostic_check("Test Check", mock_check)
        
        assert result.name == "Test Check"
        assert result.status == DiagnosticStatus.FAIL
        assert "Test error" in result.message
        assert result.duration_ms is not None
        assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_valid(self):
        """Test configuration validation with valid config."""
        result = await self.diagnostics._validate_configuration()
        
        assert result.name == "Configuration Validation"
        assert result.status in [DiagnosticStatus.PASS, DiagnosticStatus.WARNING]
        assert result.technical_info is not None
        assert "config_summary" in result.technical_info
    
    @pytest.mark.asyncio
    async def test_validate_configuration_invalid_url(self):
        """Test configuration validation with invalid URL."""
        invalid_config = JiraConfig(
            base_url="invalid-url",
            auth_type=JiraAuthType.BASIC,
            username="test",
            password="test"
        )
        diagnostics = JiraDiagnostics(invalid_config)
        
        result = await diagnostics._validate_configuration()
        
        assert result.status == DiagnosticStatus.FAIL
        assert "errors" in result.technical_info
        assert len(result.technical_info["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_validate_configuration_missing_auth(self):
        """Test configuration validation with missing authentication."""
        invalid_config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.API_TOKEN
            # Missing email and api_token
        )
        diagnostics = JiraDiagnostics(invalid_config)
        
        result = await diagnostics._validate_configuration()
        
        assert result.status == DiagnosticStatus.FAIL
        assert "Email is required" in str(result.technical_info["errors"])
        assert "API token is required" in str(result.technical_info["errors"])
    
    def test_validate_auth_config_api_token(self):
        """Test authentication configuration validation for API token."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="test-token"
        )
        diagnostics = JiraDiagnostics(config)
        
        errors = diagnostics._validate_auth_config()
        assert len(errors) == 0
    
    def test_validate_auth_config_pat(self):
        """Test authentication configuration validation for PAT."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test-pat"
        )
        diagnostics = JiraDiagnostics(config)
        
        errors = diagnostics._validate_auth_config()
        assert len(errors) == 0
    
    def test_validate_auth_config_basic(self):
        """Test authentication configuration validation for basic auth."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.BASIC,
            username="testuser",
            password="testpass"
        )
        diagnostics = JiraDiagnostics(config)
        
        errors = diagnostics._validate_auth_config()
        assert len(errors) == 0
    
    def test_validate_auth_config_missing_fields(self):
        """Test authentication configuration validation with missing fields."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.API_TOKEN
            # Missing email and api_token
        )
        diagnostics = JiraDiagnostics(config)
        
        errors = diagnostics._validate_auth_config()
        assert len(errors) == 2
        assert "Email is required" in errors
        assert "API token is required" in errors
    
    @pytest.mark.asyncio
    async def test_check_network_connectivity_success(self):
        """Test successful network connectivity check."""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0  # Success
            mock_socket.return_value = mock_sock
            
            result = await self.diagnostics._check_network_connectivity()
            
            assert result.status == DiagnosticStatus.PASS
            assert "Successfully connected" in result.message
            assert result.technical_info is not None
            assert "hostname" in result.technical_info
            assert "port" in result.technical_info
    
    @pytest.mark.asyncio
    async def test_check_network_connectivity_failure(self):
        """Test failed network connectivity check."""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 111  # Connection refused
            mock_socket.return_value = mock_sock
            
            result = await self.diagnostics._check_network_connectivity()
            
            assert result.status == DiagnosticStatus.FAIL
            assert "Cannot connect" in result.message
            assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_check_network_connectivity_timeout(self):
        """Test network connectivity check with timeout."""
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.side_effect = socket.timeout("Connection timeout")
            mock_socket.return_value = mock_sock
            
            result = await self.diagnostics._check_network_connectivity()
            
            assert result.status == DiagnosticStatus.FAIL
            assert "timeout" in result.message.lower()
            assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_check_network_connectivity_no_url(self):
        """Test network connectivity check with no URL configured."""
        config = JiraConfig(auth_type=JiraAuthType.BASIC)  # No base_url
        diagnostics = JiraDiagnostics(config)
        
        result = await diagnostics._check_network_connectivity()
        
        assert result.status == DiagnosticStatus.SKIP
        assert "no base URL" in result.message
    
    @pytest.mark.asyncio
    async def test_check_ssl_certificate_success(self):
        """Test successful SSL certificate check."""
        mock_cert = {
            'subject': [('commonName', 'jira.example.com')],
            'issuer': [('organizationName', 'Test CA')],
            'version': 3,
            'serialNumber': '12345',
            'notBefore': 'Jan 1 00:00:00 2024 GMT',
            'notAfter': 'Jan 1 00:00:00 2025 GMT'
        }
        
        with patch('socket.create_connection'), \
             patch('ssl.create_default_context') as mock_context:
            
            mock_ssl_context = Mock()
            mock_context.return_value = mock_ssl_context
            
            mock_ssl_sock = Mock()
            mock_ssl_sock.getpeercert.return_value = mock_cert
            mock_ssl_sock.cipher.return_value = ('TLS_AES_256_GCM_SHA384', 'TLSv1.3', 256)
            
            mock_ssl_context.wrap_socket.return_value.__enter__.return_value = mock_ssl_sock
            
            result = await self.diagnostics._check_ssl_certificate()
            
            assert result.status in [DiagnosticStatus.PASS, DiagnosticStatus.WARNING]
            assert "certificate is valid" in result.message
            assert result.technical_info is not None
    
    @pytest.mark.asyncio
    async def test_check_ssl_certificate_error(self):
        """Test SSL certificate check with SSL error."""
        with patch('socket.create_connection'), \
             patch('ssl.create_default_context') as mock_context:
            
            mock_ssl_context = Mock()
            mock_context.return_value = mock_ssl_context
            mock_ssl_context.wrap_socket.side_effect = ssl.SSLError("Certificate verification failed")
            
            result = await self.diagnostics._check_ssl_certificate()
            
            assert result.status == DiagnosticStatus.FAIL
            assert "SSL certificate error" in result.message
            assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_check_ssl_certificate_skip_http(self):
        """Test SSL certificate check skipped for HTTP."""
        config = JiraConfig(
            base_url="http://jira.example.com",
            auth_type=JiraAuthType.BASIC
        )
        diagnostics = JiraDiagnostics(config)
        
        result = await diagnostics._check_ssl_certificate()
        
        assert result.status == DiagnosticStatus.SKIP
        assert "not using HTTPS" in result.message
    
    @pytest.mark.asyncio
    async def test_check_dns_resolution_success(self):
        """Test successful DNS resolution check."""
        mock_addresses = [
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.100', 8443)),
            (socket.AF_INET, socket.SOCK_STREAM, 6, '', ('192.168.1.101', 8443))
        ]
        
        with patch('socket.getaddrinfo', return_value=mock_addresses):
            result = await self.diagnostics._check_dns_resolution()
            
            assert result.status == DiagnosticStatus.PASS
            assert "Successfully resolved" in result.message
            assert result.technical_info is not None
            assert "addresses" in result.technical_info
            assert len(result.technical_info["addresses"]) == 2
    
    @pytest.mark.asyncio
    async def test_check_dns_resolution_failure(self):
        """Test failed DNS resolution check."""
        with patch('socket.getaddrinfo', side_effect=socket.gaierror("Name resolution failed")):
            result = await self.diagnostics._check_dns_resolution()
            
            assert result.status == DiagnosticStatus.FAIL
            assert "DNS resolution failed" in result.message
            assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_check_proxy_configuration_success(self):
        """Test successful proxy configuration check."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.BASIC,
            proxy_url="http://proxy.example.com:8080"
        )
        diagnostics = JiraDiagnostics(config)
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0  # Success
            mock_socket.return_value = mock_sock
            
            result = await diagnostics._check_proxy_configuration()
            
            assert result.status == DiagnosticStatus.PASS
            assert "Proxy is reachable" in result.message
            assert result.technical_info is not None
    
    @pytest.mark.asyncio
    async def test_check_proxy_configuration_skip(self):
        """Test proxy configuration check skipped when no proxy."""
        result = await self.diagnostics._check_proxy_configuration()
        
        assert result.status == DiagnosticStatus.SKIP
        assert "no proxy configured" in result.message
    
    @pytest.mark.asyncio
    async def test_check_proxy_configuration_invalid_url(self):
        """Test proxy configuration check with invalid URL."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.BASIC,
            proxy_url="invalid-proxy-url"
        )
        diagnostics = JiraDiagnostics(config)
        
        result = await diagnostics._check_proxy_configuration()
        
        assert result.status == DiagnosticStatus.FAIL
        assert "Invalid proxy URL" in result.message
        assert len(result.suggestions) > 0
    
    @pytest.mark.asyncio
    async def test_check_version_compatibility_success(self):
        """Test successful version compatibility check."""
        mock_response_data = {
            "version": "9.12.22",
            "buildNumber": "912022",
            "deploymentType": "DataCenter"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await self.diagnostics._check_version_compatibility()
            
            assert result.status == DiagnosticStatus.PASS
            assert "9.12.22" in result.message
            assert result.technical_info is not None
            assert result.technical_info["is_compatible"] is True
    
    @pytest.mark.asyncio
    async def test_check_version_compatibility_incompatible(self):
        """Test version compatibility check with incompatible version."""
        mock_response_data = {
            "version": "7.13.0",
            "buildNumber": "713000",
            "deploymentType": "DataCenter"
        }
        
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_response_data
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await self.diagnostics._check_version_compatibility()
            
            assert result.status == DiagnosticStatus.FAIL
            assert "incompatible" in result.message
            assert len(result.suggestions) > 0
            assert "upgrade" in result.suggestions[0].lower()
    
    @pytest.mark.asyncio
    async def test_check_version_compatibility_auth_required(self):
        """Test version compatibility check when authentication is required."""
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 401
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = httpx.HTTPStatusError(
                "Unauthorized", request=Mock(), response=mock_response
            )
            
            result = await self.diagnostics._check_version_compatibility()
            
            assert result.status == DiagnosticStatus.WARNING
            assert "requires authentication" in result.message
    
    def test_is_version_compatible(self):
        """Test version compatibility checking logic."""
        # Compatible versions
        assert self.diagnostics._is_version_compatible("9.12.22") is True
        assert self.diagnostics._is_version_compatible("8.0.0") is True
        assert self.diagnostics._is_version_compatible("8.14.1") is True
        assert self.diagnostics._is_version_compatible("10.0.0") is True
        
        # Incompatible versions
        assert self.diagnostics._is_version_compatible("7.13.0") is False
        assert self.diagnostics._is_version_compatible("6.4.14") is False
        
        # Edge cases
        assert self.diagnostics._is_version_compatible("8.0") is True
        assert self.diagnostics._is_version_compatible("invalid") is True  # Assume compatible if can't parse
    
    def test_get_feature_support(self):
        """Test feature support detection based on version."""
        # Modern version
        features_9 = self.diagnostics._get_feature_support("9.12.22")
        assert features_9["rest_api_v3"] is True
        assert features_9["personal_access_tokens"] is True
        assert features_9["modern_authentication"] is True
        
        # Older version
        features_8_13 = self.diagnostics._get_feature_support("8.13.0")
        assert features_8_13["rest_api_v3"] is True
        assert features_8_13["personal_access_tokens"] is False  # PAT requires 8.14+
        
        # Very old version
        features_7 = self.diagnostics._get_feature_support("7.13.0")
        assert features_7["rest_api_v3"] is False
        assert features_7["personal_access_tokens"] is False
    
    @pytest.mark.asyncio
    async def test_check_auth_method_availability_data_center(self):
        """Test authentication method availability for Data Center."""
        with patch.object(self.diagnostics, '_check_sso_availability', return_value=True):
            result = await self.diagnostics._check_auth_method_availability()
            
            assert result.status == DiagnosticStatus.PASS
            assert len(result.technical_info["available_methods"]) >= 3
            assert "personal_access_token" in result.technical_info["available_methods"]
            assert "basic" in result.technical_info["available_methods"]
            assert "sso" in result.technical_info["available_methods"]
    
    @pytest.mark.asyncio
    async def test_check_auth_method_availability_cloud(self):
        """Test authentication method availability for Cloud."""
        config = JiraConfig(
            base_url="https://company.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            deployment_type=JiraDeploymentType.CLOUD
        )
        diagnostics = JiraDiagnostics(config)
        
        with patch.object(diagnostics, '_check_sso_availability', return_value=False):
            result = await diagnostics._check_auth_method_availability()
            
            assert result.status == DiagnosticStatus.PASS
            assert "api_token" in result.technical_info["available_methods"]
            assert "basic" in result.technical_info["available_methods"]
            assert "personal_access_token" not in result.technical_info["available_methods"]
    
    @pytest.mark.asyncio
    async def test_check_sso_availability(self):
        """Test SSO availability check."""
        # Data Center should support SSO
        result = await self.diagnostics._check_sso_availability()
        assert result is True
        
        # Cloud typically doesn't support SSO in this context
        config = JiraConfig(
            base_url="https://company.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            deployment_type=JiraDeploymentType.CLOUD
        )
        diagnostics = JiraDiagnostics(config)
        result = await diagnostics._check_sso_availability()
        assert result is False


class TestJiraDiagnosticsFactory:
    """Test cases for the factory function."""
    
    def test_create_jira_diagnostics(self):
        """Test creating JiraDiagnostics instance via factory."""
        config = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.BASIC
        )
        
        diagnostics = create_jira_diagnostics(config)
        
        assert isinstance(diagnostics, JiraDiagnostics)
        assert diagnostics.config == config


class TestDiagnosticModels:
    """Test cases for diagnostic result models."""
    
    def test_diagnostic_result_creation(self):
        """Test creating DiagnosticResult with all fields."""
        result = DiagnosticResult(
            name="Test Check",
            status=DiagnosticStatus.PASS,
            message="Check passed",
            details="Additional details",
            duration_ms=123.45,
            suggestions=["Suggestion 1", "Suggestion 2"],
            technical_info={"key": "value"}
        )
        
        assert result.name == "Test Check"
        assert result.status == DiagnosticStatus.PASS
        assert result.message == "Check passed"
        assert result.details == "Additional details"
        assert result.duration_ms == 123.45
        assert len(result.suggestions) == 2
        assert result.technical_info == {"key": "value"}
    
    def test_diagnostic_result_minimal(self):
        """Test creating DiagnosticResult with minimal fields."""
        result = DiagnosticResult(
            name="Test Check",
            status=DiagnosticStatus.FAIL,
            message="Check failed"
        )
        
        assert result.name == "Test Check"
        assert result.status == DiagnosticStatus.FAIL
        assert result.message == "Check failed"
        assert result.details is None
        assert result.duration_ms is None
        assert result.suggestions == []
        assert result.technical_info is None
    
    def test_network_connectivity_result(self):
        """Test NetworkConnectivityResult model."""
        result = NetworkConnectivityResult(
            hostname="jira.example.com",
            port=8443,
            is_reachable=True,
            response_time_ms=45.6,
            ssl_info={"version": "TLSv1.3"}
        )
        
        assert result.hostname == "jira.example.com"
        assert result.port == 8443
        assert result.is_reachable is True
        assert result.response_time_ms == 45.6
        assert result.ssl_info == {"version": "TLSv1.3"}
    
    def test_configuration_validation_result(self):
        """Test ConfigurationValidationResult model."""
        result = ConfigurationValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1"],
            validated_config={"key": "value"}
        )
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1
        assert result.validated_config == {"key": "value"}
    
    def test_version_compatibility_result(self):
        """Test VersionCompatibilityResult model."""
        result = VersionCompatibilityResult(
            jira_version="9.12.22",
            is_compatible=True,
            minimum_version="8.0.0",
            recommended_version="9.12.22",
            compatibility_notes=["Note 1"],
            feature_support={"rest_api_v3": True}
        )
        
        assert result.jira_version == "9.12.22"
        assert result.is_compatible is True
        assert result.minimum_version == "8.0.0"
        assert result.recommended_version == "9.12.22"
        assert len(result.compatibility_notes) == 1
        assert result.feature_support == {"rest_api_v3": True}
    
    def test_auth_method_availability_result(self):
        """Test AuthMethodAvailabilityResult model."""
        result = AuthMethodAvailabilityResult(
            available_methods=[JiraAuthType.BASIC, JiraAuthType.PERSONAL_ACCESS_TOKEN],
            recommended_method=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            method_details={
                JiraAuthType.BASIC: {"description": "Basic auth"},
                JiraAuthType.PERSONAL_ACCESS_TOKEN: {"description": "PAT auth"}
            },
            sso_available=False,
            pat_supported=True
        )
        
        assert len(result.available_methods) == 2
        assert result.recommended_method == JiraAuthType.PERSONAL_ACCESS_TOKEN
        assert len(result.method_details) == 2
        assert result.sso_available is False
        assert result.pat_supported is True