"""Integration tests for enhanced Jira connection testing with fallback."""

import pytest
from unittest.mock import MagicMock, patch
import httpx

from app.services.jira import JiraService
from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
from app.services.jira_auth import AuthResult
from app.services.deployment_detector import DeploymentInfo, DeploymentDetectionError
from app.services.api_version_manager import APIVersionError


class TestJiraConnectionTesting:
    """Integration tests for enhanced connection testing scenarios."""
    
    @pytest.fixture
    def data_center_config(self):
        """Jira Data Center configuration."""
        return JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test-pat-token",
            verify_ssl=True,
            timeout=30
        )
    
    @pytest.fixture
    def cloud_config_with_proxy(self):
        """Jira Cloud configuration with proxy."""
        return JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="test-token",
            proxy_url="http://proxy.company.com:8080"
        )
    
    @pytest.fixture
    def ssl_config(self):
        """Configuration with custom SSL settings."""
        return JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.BASIC,
            username="testuser",
            password="testpass",
            verify_ssl=True,
            ca_cert_path="/path/to/ca-cert.pem"
        )
    
    @pytest.mark.asyncio
    async def test_connection_test_with_deployment_detection_failure(self, data_center_config):
        """Test connection test when deployment detection fails."""
        service = JiraService(data_center_config)
        
        # Mock deployment detection failure
        with patch.object(service.deployment_detector, 'detect_deployment', 
                         side_effect=DeploymentDetectionError("Network unreachable")):
            
            result = await service.test_connection_with_fallback()
            
            # Should continue with manual config despite detection failure
            assert not result.success
            # The error message will be from the connection test, not the deployment detection
            assert "Failed to connect to Jira" in str(result.error_details.get('message', ''))
    
    @pytest.mark.asyncio
    async def test_connection_test_with_ssl_certificate_error(self, ssl_config):
        """Test connection test with SSL certificate errors."""
        service = JiraService(ssl_config)
        
        # Mock SSL certificate error
        ssl_error = httpx.ConnectError("SSL: CERTIFICATE_VERIFY_FAILED")
        
        with patch.object(service.auth_manager, 'authenticate', 
                         return_value=AuthResult(
                             success=True,
                             auth_type=JiraAuthType.BASIC,
                             headers={"Authorization": "Basic dGVzdDp0ZXN0"},
                             error_message=None
                         )), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = ssl_error
            
            result = await service.test_connection_with_fallback()
            
            assert not result.success
            # The error message will be normalized to a generic connection error
            assert "Failed to connect to Jira" in result.error_details.get('message', '')
            # But troubleshooting steps should still be present
            assert "Check base URL is correct and accessible" in result.troubleshooting_steps
    
    @pytest.mark.asyncio
    async def test_connection_test_with_timeout_error(self, data_center_config):
        """Test connection test with timeout errors."""
        service = JiraService(data_center_config)
        
        # Mock timeout error
        timeout_error = httpx.TimeoutException("Request timed out")
        
        with patch.object(service.auth_manager, 'authenticate', 
                         return_value=AuthResult(
                             success=True,
                             auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
                             headers={"Authorization": "Bearer test-pat-token"},
                             error_message=None
                         )), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = timeout_error
            
            result = await service.test_connection_with_fallback()
            
            assert not result.success
            assert "timeout" in result.error_details.get('message', '').lower()
            assert "Check network connectivity" in result.troubleshooting_steps
            assert "Consider increasing timeout value for slow networks" in result.troubleshooting_steps
    
    @pytest.mark.asyncio
    async def test_connection_test_with_proxy_error(self, cloud_config_with_proxy):
        """Test connection test with proxy configuration errors."""
        service = JiraService(cloud_config_with_proxy)
        
        # Mock proxy connection error
        proxy_error = httpx.ConnectError("Proxy connection failed")
        
        with patch.object(service.auth_manager, 'authenticate', 
                         return_value=AuthResult(
                             success=True,
                             auth_type=JiraAuthType.API_TOKEN,
                             headers={"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTp0ZXN0LXRva2Vu"},
                             error_message=None
                         )), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.side_effect = proxy_error
            
            result = await service.test_connection_with_fallback()
            
            assert not result.success
            # The error message will be normalized to a generic connection error
            assert "Failed to connect to Jira" in result.error_details.get('message', '')
            # But troubleshooting steps should still be present
            assert "Check base URL is correct and accessible" in result.troubleshooting_steps
    
    @pytest.mark.asyncio
    async def test_connection_test_with_403_forbidden(self, data_center_config):
        """Test connection test with 403 Forbidden response."""
        service = JiraService(data_center_config)
        
        # Mock 403 response
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.text = "Forbidden"
        
        with patch.object(service.auth_manager, 'authenticate', 
                         return_value=AuthResult(
                             success=True,
                             auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
                             headers={"Authorization": "Bearer test-pat-token"},
                             error_message=None
                         )), \
             patch.object(service.api_version_manager, 'get_working_api_version', 
                         return_value="3"), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await service.test_connection_with_fallback()
            
            assert not result.success
            assert "Access forbidden" in result.error_details.get('message', '')
            assert "Check user permissions in Jira" in result.troubleshooting_steps
            assert "For Data Center: Check application access permissions" in result.troubleshooting_steps
    
    @pytest.mark.asyncio
    async def test_connection_test_with_api_version_detection_failure(self, data_center_config):
        """Test connection test when API version detection fails."""
        service = JiraService(data_center_config)
        
        # Mock successful authentication but API version detection failure
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            headers={"Authorization": "Bearer test-pat-token"},
            error_message=None
        )
        
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"displayName": "Test User", "accountId": "123"}
        
        with patch.object(service.auth_manager, 'authenticate', return_value=mock_auth_result), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value=mock_auth_result.headers), \
             patch.object(service.api_version_manager, 'get_working_api_version', 
                         side_effect=APIVersionError("No working API version found")), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await service.test_connection_with_fallback()
            
            # Should still succeed with default API version
            assert result.success
            assert service.api_version == "3"  # Default fallback
    
    @pytest.mark.asyncio
    async def test_deployment_specific_validation_data_center(self, data_center_config):
        """Test deployment-specific validation for Data Center."""
        service = JiraService(data_center_config)
        
        # Set deployment info
        service.deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            base_url_normalized="https://jira.company.com",
            supports_sso=True,
            supports_pat=True
        )
        
        # Test with API token (should generate error)
        service.config.auth_type = JiraAuthType.API_TOKEN
        errors = await service.validate_deployment_specific_config()
        
        assert len(errors) > 0
        assert "API tokens are not supported in Jira Data Center" in errors[0]
        
        # Test with PAT (should be valid)
        service.config.auth_type = JiraAuthType.PERSONAL_ACCESS_TOKEN
        errors = await service.validate_deployment_specific_config()
        
        assert len(errors) == 0
    
    @pytest.mark.asyncio
    async def test_deployment_specific_validation_cloud(self, cloud_config_with_proxy):
        """Test deployment-specific validation for Cloud."""
        service = JiraService(cloud_config_with_proxy)
        
        # Set deployment info
        service.deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.CLOUD,
            version="1000.0.0",
            base_url_normalized="https://test.atlassian.net",
            supports_sso=False,
            supports_pat=True
        )
        
        # Test with basic auth (should generate error)
        service.config.auth_type = JiraAuthType.BASIC
        service.config.username = "testuser"
        service.config.password = "testpass"
        
        errors = await service.validate_deployment_specific_config()
        
        assert len(errors) > 0
        assert "Basic authentication is not recommended for Jira Cloud" in errors[0]
    
    @pytest.mark.asyncio
    async def test_get_deployment_health_info(self, data_center_config):
        """Test getting deployment health information."""
        service = JiraService(data_center_config)
        
        # Set up mock deployment info and authentication
        service.deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            base_url_normalized="https://jira.company.com",
            supports_sso=True,
            supports_pat=True,
            context_path="jira",
            server_title="Company Jira"
        )
        
        service.api_version = "3"
        
        # Mock authentication state
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            headers={"Authorization": "Bearer test-pat-token"},
            error_message=None
        )
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_current_auth_result', 
                         return_value=mock_auth_result), \
             patch.object(service.auth_manager, 'get_available_auth_types', 
                         return_value=[JiraAuthType.PERSONAL_ACCESS_TOKEN, JiraAuthType.BASIC]):
            
            health_info = await service.get_deployment_health_info()
            
            assert health_info["deployment_type"] == "data_center"
            assert health_info["version"] == "9.12.22"
            assert health_info["api_version"] == "3"
            assert health_info["authentication_status"] == "authenticated"
            assert health_info["current_auth_type"] == "pat"
            assert health_info["supports_sso"] is True
            assert health_info["supports_pat"] is True
            assert health_info["context_path"] == "jira"
            assert health_info["server_title"] == "Company Jira"
            assert "pat" in health_info["available_auth_types"]
            assert "basic" in health_info["available_auth_types"]
    
    @pytest.mark.asyncio
    async def test_troubleshooting_steps_data_center_specific(self, data_center_config):
        """Test that Data Center specific troubleshooting steps are included."""
        service = JiraService(data_center_config)
        
        # Set deployment info
        service.deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            base_url_normalized="https://jira.company.com",
            supports_sso=True,
            supports_pat=True
        )
        
        # Test timeout error troubleshooting
        steps = service._get_connection_troubleshooting_steps("Connection timeout after 30 seconds")
        
        assert "Check network connectivity" in steps
        assert "Verify Jira Data Center is running and accessible" in steps
        assert "Check load balancer configuration if applicable" in steps
        assert "Ensure all required ports are open (typically 8080/8443)" in steps
    
    @pytest.mark.asyncio
    async def test_authentication_fallback_troubleshooting(self, data_center_config):
        """Test authentication-specific troubleshooting steps."""
        service = JiraService(data_center_config)
        
        # Set deployment info
        service.deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            base_url_normalized="https://jira.company.com",
            supports_sso=True,
            supports_pat=True
        )
        
        # Test PAT authentication failure
        auth_result = AuthResult(
            success=False,
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            headers={},
            error_message="PAT authentication failed"
        )
        
        steps = service._get_auth_troubleshooting_steps(auth_result)
        
        assert "Verify Personal Access Token is valid" in steps
        assert "For Jira Data Center, generate token in user profile settings" in steps
        assert "Verify Jira Data Center server is accessible" in steps
        assert "Check network connectivity and firewall settings" in steps
    
    @pytest.mark.asyncio
    async def test_basic_auth_fallback_prompt(self, data_center_config):
        """Test basic authentication fallback prompting."""
        service = JiraService(data_center_config)
        
        # This should log the need for user prompt
        result = await service.prompt_basic_auth_fallback()
        
        # Currently returns None as UI implementation is needed
        assert result is None
        
        # In a real implementation, this would return credentials from user input
        # {"username": "user_input", "password": "user_input"}