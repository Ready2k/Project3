"""
Integration tests for Jira diagnostics and validation utilities.
"""

import pytest
from unittest.mock import patch, Mock
import httpx

from app.services.jira_diagnostics import (
    JiraDiagnostics,
    DiagnosticStatus,
    create_jira_diagnostics
)
from app.config import JiraConfig, JiraAuthType, JiraDeploymentType


class TestJiraDiagnosticsIntegration:
    """Integration test cases for JiraDiagnostics."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.valid_config = JiraConfig(
            base_url="https://jira.example.com:8443",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            deployment_type=JiraDeploymentType.DATA_CENTER,
            personal_access_token="test-pat-token",
            verify_ssl=True,
            timeout=30
        )
        
        self.invalid_config = JiraConfig(
            base_url="invalid-url",
            auth_type=JiraAuthType.API_TOKEN,
            # Missing required fields
        )
    
    @pytest.mark.asyncio
    async def test_full_diagnostics_with_valid_config(self):
        """Test running full diagnostics with valid configuration."""
        diagnostics = create_jira_diagnostics(self.valid_config)
        
        # Mock network calls to avoid actual network requests
        with patch('socket.socket') as mock_socket, \
             patch('socket.getaddrinfo') as mock_getaddrinfo, \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock successful network connectivity
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock
            
            # Mock successful DNS resolution
            mock_getaddrinfo.return_value = [
                (2, 1, 6, '', ('192.168.1.100', 8443))
            ]
            
            # Mock Jira version response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "9.12.22",
                "buildNumber": "912022",
                "deploymentType": "DataCenter"
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            results = await diagnostics.run_full_diagnostics()
            
            # Should have multiple diagnostic results
            assert len(results) >= 5
            
            # Check that we have the expected diagnostic checks
            check_names = [result.name for result in results]
            assert "Configuration Validation" in check_names
            assert "Network Connectivity" in check_names
            assert "SSL/TLS Certificate" in check_names
            assert "DNS Resolution" in check_names
            assert "Version Compatibility" in check_names
            assert "Authentication Methods" in check_names
            
            # Most checks should pass with mocked successful responses
            passed_checks = [r for r in results if r.status == DiagnosticStatus.PASS]
            assert len(passed_checks) >= 3
    
    @pytest.mark.asyncio
    async def test_full_diagnostics_with_invalid_config(self):
        """Test running full diagnostics with invalid configuration."""
        diagnostics = create_jira_diagnostics(self.invalid_config)
        
        results = await diagnostics.run_full_diagnostics()
        
        # Should still run diagnostics but configuration validation should fail
        config_result = next((r for r in results if r.name == "Configuration Validation"), None)
        assert config_result is not None
        assert config_result.status == DiagnosticStatus.FAIL
        
        # Should have error details
        assert config_result.technical_info is not None
        assert "errors" in config_result.technical_info
        assert len(config_result.technical_info["errors"]) > 0
    
    @pytest.mark.asyncio
    async def test_diagnostics_with_network_failure(self):
        """Test diagnostics when network connectivity fails."""
        diagnostics = create_jira_diagnostics(self.valid_config)
        
        with patch('socket.socket') as mock_socket:
            # Mock network connection failure
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 111  # Connection refused
            mock_socket.return_value = mock_sock
            
            results = await diagnostics.run_full_diagnostics()
            
            # Network connectivity should fail
            network_result = next((r for r in results if r.name == "Network Connectivity"), None)
            assert network_result is not None
            assert network_result.status == DiagnosticStatus.FAIL
            assert "Cannot connect" in network_result.message
            
            # Should not run version compatibility check if network fails
            version_result = next((r for r in results if r.name == "Version Compatibility"), None)
            assert version_result is None  # Should be skipped
    
    @pytest.mark.asyncio
    async def test_diagnostics_with_ssl_issues(self):
        """Test diagnostics when SSL certificate has issues."""
        diagnostics = create_jira_diagnostics(self.valid_config)
        
        with patch('socket.create_connection'), \
             patch('ssl.create_default_context') as mock_context:
            
            # Mock SSL certificate error
            mock_ssl_context = Mock()
            mock_context.return_value = mock_ssl_context
            mock_ssl_context.wrap_socket.side_effect = Exception("SSL certificate verify failed")
            
            results = await diagnostics.run_full_diagnostics()
            
            # SSL check should fail
            ssl_result = next((r for r in results if r.name == "SSL/TLS Certificate"), None)
            assert ssl_result is not None
            assert ssl_result.status == DiagnosticStatus.FAIL
            assert "SSL" in ssl_result.message
    
    @pytest.mark.asyncio
    async def test_diagnostics_with_proxy_config(self):
        """Test diagnostics with proxy configuration."""
        config_with_proxy = JiraConfig(
            base_url="https://jira.example.com",
            auth_type=JiraAuthType.BASIC,
            username="testuser",
            password="testpass",
            proxy_url="http://proxy.example.com:8080"
        )
        diagnostics = create_jira_diagnostics(config_with_proxy)
        
        with patch('socket.socket') as mock_socket:
            # Mock successful proxy connectivity
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock
            
            results = await diagnostics.run_full_diagnostics()
            
            # Should include proxy configuration check
            proxy_result = next((r for r in results if r.name == "Proxy Configuration"), None)
            assert proxy_result is not None
            assert proxy_result.status == DiagnosticStatus.PASS
            assert "Proxy is reachable" in proxy_result.message
    
    @pytest.mark.asyncio
    async def test_diagnostics_version_compatibility_scenarios(self):
        """Test version compatibility checking with different scenarios."""
        diagnostics = create_jira_diagnostics(self.valid_config)
        
        # Test compatible version
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "9.12.22",
                "buildNumber": "912022",
                "deploymentType": "DataCenter"
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            # Mock network connectivity success
            with patch('socket.socket') as mock_socket:
                mock_sock = Mock()
                mock_sock.connect_ex.return_value = 0
                mock_socket.return_value = mock_sock
                
                results = await diagnostics.run_full_diagnostics()
                
                version_result = next((r for r in results if r.name == "Version Compatibility"), None)
                assert version_result is not None
                assert version_result.status == DiagnosticStatus.PASS
                assert "9.12.22" in version_result.message
    
    @pytest.mark.asyncio
    async def test_diagnostics_auth_method_detection(self):
        """Test authentication method detection for different deployment types."""
        # Test Data Center
        dc_config = JiraConfig(
            base_url="https://jira-dc.example.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            deployment_type=JiraDeploymentType.DATA_CENTER,
            personal_access_token="test-pat"
        )
        dc_diagnostics = create_jira_diagnostics(dc_config)
        
        with patch('socket.socket') as mock_socket:
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock
            
            results = await dc_diagnostics.run_full_diagnostics()
            
            auth_result = next((r for r in results if r.name == "Authentication Methods"), None)
            assert auth_result is not None
            assert auth_result.status == DiagnosticStatus.PASS
            
            # Data Center should support PAT and SSO
            available_methods = auth_result.technical_info["available_methods"]
            assert "personal_access_token" in available_methods
            assert "basic" in available_methods
            assert "sso" in available_methods
    
    @pytest.mark.asyncio
    async def test_diagnostics_error_handling_and_recovery(self):
        """Test that diagnostics handle errors gracefully and continue."""
        diagnostics = create_jira_diagnostics(self.valid_config)
        
        # Mock some checks to fail and others to succeed
        with patch.object(diagnostics, '_check_network_connectivity') as mock_network, \
             patch.object(diagnostics, '_check_dns_resolution') as mock_dns:
            
            # Network check fails
            mock_network.side_effect = Exception("Network check failed")
            
            # DNS check succeeds
            from app.services.jira_diagnostics import DiagnosticResult, DiagnosticStatus
            mock_dns.return_value = DiagnosticResult(
                name="DNS Resolution",
                status=DiagnosticStatus.PASS,
                message="DNS resolution successful"
            )
            
            results = await diagnostics.run_full_diagnostics()
            
            # Should still have results despite some failures
            assert len(results) > 0
            
            # Failed network check should be handled gracefully
            network_result = next((r for r in results if r.name == "Network Connectivity"), None)
            assert network_result is not None
            assert network_result.status == DiagnosticStatus.FAIL
            assert "Network check failed" in network_result.message
            
            # DNS check should still succeed
            dns_result = next((r for r in results if r.name == "DNS Resolution"), None)
            assert dns_result is not None
            assert dns_result.status == DiagnosticStatus.PASS
    
    @pytest.mark.asyncio
    async def test_diagnostics_timing_information(self):
        """Test that diagnostic results include timing information."""
        diagnostics = create_jira_diagnostics(self.valid_config)
        
        results = await diagnostics.run_full_diagnostics()
        
        # All results should have timing information
        for result in results:
            assert result.duration_ms is not None
            assert result.duration_ms >= 0
            # Reasonable upper bound for test execution
            assert result.duration_ms < 10000  # 10 seconds
    
    @pytest.mark.asyncio
    async def test_diagnostics_suggestions_and_troubleshooting(self):
        """Test that failed diagnostics provide helpful suggestions."""
        # Use invalid config to trigger failures
        diagnostics = create_jira_diagnostics(self.invalid_config)
        
        results = await diagnostics.run_full_diagnostics()
        
        # Failed checks should have suggestions
        failed_results = [r for r in results if r.status == DiagnosticStatus.FAIL]
        assert len(failed_results) > 0
        
        for failed_result in failed_results:
            # Should have either suggestions or technical info with troubleshooting
            has_suggestions = len(failed_result.suggestions) > 0
            has_technical_info = failed_result.technical_info is not None
            assert has_suggestions or has_technical_info
    
    @pytest.mark.asyncio
    async def test_diagnostics_comprehensive_coverage(self):
        """Test that diagnostics cover all major areas comprehensively."""
        diagnostics = create_jira_diagnostics(self.valid_config)
        
        # Mock all external dependencies for comprehensive test
        with patch('socket.socket') as mock_socket, \
             patch('socket.getaddrinfo') as mock_getaddrinfo, \
             patch('socket.create_connection'), \
             patch('ssl.create_default_context'), \
             patch('httpx.AsyncClient') as mock_client:
            
            # Mock successful responses
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0
            mock_socket.return_value = mock_sock
            
            mock_getaddrinfo.return_value = [(2, 1, 6, '', ('192.168.1.100', 8443))]
            
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "9.12.22",
                "buildNumber": "912022",
                "deploymentType": "DataCenter"
            }
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            results = await diagnostics.run_full_diagnostics()
            
            # Should cover all major diagnostic areas
            expected_checks = [
                "Configuration Validation",
                "Network Connectivity", 
                "SSL/TLS Certificate",
                "DNS Resolution",
                "Version Compatibility",
                "Authentication Methods"
            ]
            
            actual_checks = [result.name for result in results]
            
            for expected_check in expected_checks:
                assert expected_check in actual_checks, f"Missing diagnostic check: {expected_check}"
            
            # Should have reasonable success rate with mocked successful responses
            passed_checks = [r for r in results if r.status == DiagnosticStatus.PASS]
            total_checks = len(results)
            success_rate = len(passed_checks) / total_checks
            
            # At least 70% should pass with successful mocks
            assert success_rate >= 0.7, f"Success rate too low: {success_rate:.2%}"