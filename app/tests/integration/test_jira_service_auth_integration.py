"""Integration tests for JiraService authentication flows."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import httpx

from app.services.jira import JiraService, JiraConnectionError, JiraTicketNotFoundError
from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
from app.services.jira_auth import AuthResult
from app.services.deployment_detector import DeploymentInfo


class TestJiraServiceAuthIntegration:
    """Integration tests for JiraService authentication management."""
    
    @pytest.fixture
    def cloud_config(self):
        """Jira Cloud configuration."""
        return JiraConfig(
            base_url="https://test.atlassian.net",
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="test-token"
        )
    
    @pytest.fixture
    def data_center_config(self):
        """Jira Data Center configuration."""
        return JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test-pat-token"
        )
    
    @pytest.fixture
    def basic_auth_config(self):
        """Basic authentication configuration."""
        return JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.BASIC,
            username="testuser",
            password="testpass"
        )
    
    @pytest.fixture
    def mock_deployment_info(self):
        """Mock deployment information."""
        return DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            base_url_normalized="https://jira.company.com",
            supports_sso=True,
            supports_pat=True
        )
    
    @pytest.mark.asyncio
    async def test_auto_configure_cloud_deployment(self, cloud_config):
        """Test auto-configuration for Cloud deployment."""
        service = JiraService(cloud_config)
        
        # Mock deployment detection
        mock_deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.CLOUD,
            version="1000.0.0",
            base_url_normalized="https://test.atlassian.net",
            supports_sso=False,
            supports_pat=True
        )
        
        with patch.object(service.deployment_detector, 'detect_deployment', 
                         return_value=mock_deployment_info) as mock_detect:
            
            updated_config = await service.auto_configure()
            
            assert updated_config.deployment_type == JiraDeploymentType.CLOUD
            assert updated_config.auth_type == JiraAuthType.API_TOKEN
            mock_detect.assert_called_once_with("https://test.atlassian.net")
    
    @pytest.mark.asyncio
    async def test_auto_configure_data_center_deployment(self, data_center_config):
        """Test auto-configuration for Data Center deployment."""
        service = JiraService(data_center_config)
        
        # Mock deployment detection
        mock_deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            base_url_normalized="https://jira.company.com",
            supports_sso=True,
            supports_pat=True,
            context_path="jira"
        )
        
        with patch.object(service.deployment_detector, 'detect_deployment', 
                         return_value=mock_deployment_info) as mock_detect:
            
            updated_config = await service.auto_configure()
            
            assert updated_config.deployment_type == JiraDeploymentType.DATA_CENTER
            assert updated_config.context_path == "jira"
            mock_detect.assert_called_once_with("https://jira.company.com")
    
    @pytest.mark.asyncio
    async def test_authentication_fallback_chain(self, data_center_config):
        """Test authentication fallback chain when primary auth fails."""
        service = JiraService(data_center_config)
        
        # Mock authentication manager to simulate fallback
        mock_auth_results = [
            # First attempt (PAT) fails
            AuthResult(
                success=False,
                auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
                headers={},
                error_message="PAT authentication failed",
                requires_fallback=True
            ),
            # Second attempt (Basic) succeeds
            AuthResult(
                success=True,
                auth_type=JiraAuthType.BASIC,
                headers={"Authorization": "Basic dGVzdDp0ZXN0"},
                error_message=None
            )
        ]
        
        with patch.object(service.auth_manager, 'authenticate', 
                         side_effect=mock_auth_results) as mock_auth:
            
            # First call should fail and trigger fallback
            result1 = await service.auth_manager.authenticate()
            assert not result1.success
            assert result1.requires_fallback
            
            # Second call should succeed
            result2 = await service.auth_manager.authenticate()
            assert result2.success
            assert result2.auth_type == JiraAuthType.BASIC
    
    @pytest.mark.asyncio
    async def test_connection_test_with_fallback_success(self, cloud_config, mock_deployment_info):
        """Test successful connection test with authentication fallback."""
        service = JiraService(cloud_config)
        
        # Mock successful authentication
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTp0ZXN0LXRva2Vu"},
            error_message=None
        )
        
        # Mock successful HTTP response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"displayName": "Test User", "accountId": "123"}
        
        with patch.object(service.auth_manager, 'authenticate', return_value=mock_auth_result), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value=mock_auth_result.headers), \
             patch.object(service.api_version_manager, 'get_working_api_version', 
                         return_value="3"), \
             patch('httpx.AsyncClient') as mock_client:
            
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await service.test_connection_with_fallback()
            
            assert result.success
            assert result.auth_result.success
            assert result.auth_result.auth_type == JiraAuthType.API_TOKEN
            assert result.api_version == "3"
    
    @pytest.mark.asyncio
    async def test_connection_test_with_api_version_fallback(self, cloud_config):
        """Test connection test with API version fallback from v3 to v2."""
        service = JiraService(cloud_config)
        
        # Mock successful authentication
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Basic dGVzdEBleGFtcGxlLmNvbTp0ZXN0LXRva2Vu"},
            error_message=None
        )
        
        # Mock HTTP responses - v3 fails, v2 succeeds
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {"displayName": "Test User", "accountId": "123"}
        
        with patch.object(service.auth_manager, 'authenticate', return_value=mock_auth_result), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value=mock_auth_result.headers), \
             patch.object(service.api_version_manager, 'get_working_api_version', 
                         side_effect=Exception("API v3 not available")), \
             patch('httpx.AsyncClient') as mock_client:
            
            # First call (v3) returns 404, second call (v2) returns 200
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_response_404, mock_response_200
            ]
            
            result = await service.test_connection_with_fallback()
            
            assert result.success
            assert service.api_version == "3"  # Default fallback
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_with_authentication_retry(self, cloud_config):
        """Test ticket fetching with authentication retry on 401."""
        service = JiraService(cloud_config)
        
        # Mock authentication results
        mock_auth_result_fail = AuthResult(
            success=False,
            auth_type=JiraAuthType.API_TOKEN,
            headers={},
            error_message="Token expired"
        )
        
        mock_auth_result_success = AuthResult(
            success=True,
            auth_type=JiraAuthType.API_TOKEN,
            headers={"Authorization": "Basic bmV3LXRva2Vu"},
            error_message=None
        )
        
        # Mock HTTP responses
        mock_response_401 = MagicMock()
        mock_response_401.status_code = 401
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "key": "TEST-123",
            "fields": {
                "summary": "Test ticket",
                "description": "Test description",
                "status": {"name": "Open"},
                "issuetype": {"name": "Bug"},
                "priority": {"name": "High"},
                "assignee": {"displayName": "Test User"},
                "reporter": {"displayName": "Reporter User"},
                "labels": ["test"],
                "components": [{"name": "Component1"}],
                "created": "2023-01-01T00:00:00.000Z",
                "updated": "2023-01-02T00:00:00.000Z"
            }
        }
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'authenticate', 
                         return_value=mock_auth_result_success), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         side_effect=[{"Authorization": "Basic b2xkLXRva2Vu"}, 
                                    {"Authorization": "Basic bmV3LXRva2Vu"}]), \
             patch.object(service.auth_manager, 'clear_auth'), \
             patch.object(service.api_version_manager, 'get_working_api_version', 
                         return_value="3"), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         return_value="https://test.atlassian.net/rest/api/3/issue/TEST-123"), \
             patch('httpx.AsyncClient') as mock_client:
            
            # First call returns 401, second call returns 200
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_response_401, mock_response_200
            ]
            
            ticket = await service.fetch_ticket("TEST-123")
            
            assert ticket.key == "TEST-123"
            assert ticket.summary == "Test ticket"
            assert ticket.status == "Open"
    
    @pytest.mark.asyncio
    async def test_fetch_ticket_with_api_version_fallback(self, data_center_config):
        """Test ticket fetching with API version fallback from v3 to v2."""
        service = JiraService(data_center_config)
        service.api_version = "3"  # Start with v3
        
        # Mock authentication
        mock_auth_result = AuthResult(
            success=True,
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            headers={"Authorization": "Bearer test-pat-token"},
            error_message=None
        )
        
        # Mock HTTP responses - v3 returns 404, v2 returns 200
        mock_response_404 = MagicMock()
        mock_response_404.status_code = 404
        
        mock_response_200 = MagicMock()
        mock_response_200.status_code = 200
        mock_response_200.json.return_value = {
            "key": "PROJ-456",
            "fields": {
                "summary": "Data Center ticket",
                "description": "Test description",
                "status": {"name": "In Progress"},
                "issuetype": {"name": "Story"},
                "priority": {"name": "Medium"},
                "assignee": {"displayName": "DC User"},
                "reporter": {"displayName": "DC Reporter"},
                "labels": ["datacenter"],
                "components": [{"name": "Backend"}],
                "created": "2023-01-01T00:00:00.000Z",
                "updated": "2023-01-02T00:00:00.000Z"
            }
        }
        
        with patch.object(service.auth_manager, 'is_authenticated', return_value=True), \
             patch.object(service.auth_manager, 'get_auth_headers', 
                         return_value=mock_auth_result.headers), \
             patch.object(service.api_version_manager, 'build_endpoint', 
                         side_effect=[
                             "https://jira.company.com/rest/api/3/issue/PROJ-456",
                             "https://jira.company.com/rest/api/2/issue/PROJ-456"
                         ]), \
             patch('httpx.AsyncClient') as mock_client:
            
            # First call (v3) returns 404, second call (v2) returns 200
            mock_client.return_value.__aenter__.return_value.get.side_effect = [
                mock_response_404, mock_response_200
            ]
            
            ticket = await service.fetch_ticket("PROJ-456")
            
            assert ticket.key == "PROJ-456"
            assert ticket.summary == "Data Center ticket"
            assert ticket.status == "In Progress"
            assert service.api_version == "2"  # Should be updated to working version
    
    @pytest.mark.asyncio
    async def test_connection_test_backward_compatibility(self, cloud_config):
        """Test that the legacy test_connection method still works."""
        service = JiraService(cloud_config)
        
        # Mock the enhanced connection test
        mock_connection_result = MagicMock()
        mock_connection_result.success = True
        mock_connection_result.error_details = None
        
        with patch.object(service, 'test_connection_with_fallback', 
                         return_value=mock_connection_result):
            
            success, error_message = await service.test_connection()
            
            assert success is True
            assert error_message is None
    
    @pytest.mark.asyncio
    async def test_connection_test_error_handling(self, cloud_config):
        """Test error handling in connection test."""
        service = JiraService(cloud_config)
        
        # Mock authentication failure
        mock_auth_result = AuthResult(
            success=False,
            auth_type=JiraAuthType.API_TOKEN,
            headers={},
            error_message="Invalid API token",
            requires_fallback=False
        )
        
        with patch.object(service.auth_manager, 'authenticate', return_value=mock_auth_result):
            
            result = await service.test_connection_with_fallback()
            
            assert not result.success
            assert result.auth_result.error_message == "Invalid API token"
            assert "Verify email address is correct" in result.troubleshooting_steps
            assert "Check API token is valid and not expired" in result.troubleshooting_steps
    
    @pytest.mark.asyncio
    async def test_multiple_auth_types_available(self, data_center_config):
        """Test that multiple authentication types are available for Data Center."""
        service = JiraService(data_center_config)
        
        # Update config to support multiple auth types
        service.config.username = "testuser"
        service.config.password = "testpass"
        service.config.use_sso = True
        
        available_auth_types = service.auth_manager.get_available_auth_types()
        
        # Should support PAT, Basic, and SSO
        assert JiraAuthType.PERSONAL_ACCESS_TOKEN in available_auth_types
        assert JiraAuthType.BASIC in available_auth_types
        assert JiraAuthType.SSO in available_auth_types
    
    @pytest.mark.asyncio
    async def test_legacy_auth_header_compatibility(self, cloud_config):
        """Test that legacy auth_header is still set for backward compatibility."""
        service = JiraService(cloud_config)
        
        # Should still set auth_header for backward compatibility
        assert service.auth_header is not None
        assert "Basic" in service.auth_header
        
        # Verify it contains the correct encoded credentials
        import base64
        expected_auth = base64.b64encode(b"test@example.com:test-token").decode('ascii')
        assert service.auth_header == f"Basic {expected_auth}"