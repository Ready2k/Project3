"""Comprehensive integration tests for Jira Data Center compatibility."""

import pytest
from unittest.mock import Mock, patch, AsyncMock

from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
from app.services.jira import JiraService
from app.services.deployment_detector import DeploymentDetector, DeploymentInfo
from app.services.jira_error_handler import JiraErrorHandler
from app.services.jira_diagnostics import JiraDiagnostics


class TestJiraDataCenterIntegration:
    """Integration tests for Jira Data Center functionality."""

    @pytest.fixture
    def data_center_config(self):
        """Data Center configuration fixture."""
        return JiraConfig(
            base_url="https://jira.company.com",
            deployment_type=JiraDeploymentType.DATA_CENTER,
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test_pat_token",
            verify_ssl=True,
            timeout=30,
        )

    @pytest.fixture
    def cloud_config(self):
        """Cloud configuration fixture."""
        return JiraConfig(
            base_url="https://mycompany.atlassian.net",
            deployment_type=JiraDeploymentType.CLOUD,
            auth_type=JiraAuthType.API_TOKEN,
            email="test@example.com",
            api_token="test_api_token",
        )

    @pytest.fixture
    def jira_service(self, data_center_config):
        """JiraService fixture with Data Center config."""
        return JiraService(data_center_config)

    @pytest.mark.asyncio
    async def test_end_to_end_data_center_authentication_flow(self, data_center_config):
        """Test complete authentication flow for Data Center."""
        service = JiraService(data_center_config)

        # Mock successful deployment detection
        mock_deployment_info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            build_number="912022",
            base_url_normalized="https://jira.company.com",
            supports_sso=True,
            supports_pat=True,
            server_title="Company Jira",
        )

        with patch.object(
            service.deployment_detector,
            "detect_deployment",
            return_value=mock_deployment_info,
        ), patch.object(
            service.api_version_manager, "get_working_api_version", return_value="3"
        ), patch(
            "httpx.AsyncClient"
        ) as mock_client:

            # Mock successful connection test
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"myself": {"displayName": "Test User"}}

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Test connection
            result = await service.test_connection()

            assert result.success is True
            assert (
                result.deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER
            )
            assert result.deployment_info.version == "9.12.22"
            assert result.deployment_info.supports_pat is True

    @pytest.mark.asyncio
    async def test_authentication_fallback_chain(self, data_center_config):
        """Test authentication fallback from PAT to basic auth."""
        # Configure for basic auth fallback
        config = data_center_config.model_copy()
        config.auth_type = JiraAuthType.BASIC
        config.username = "testuser"
        config.password = "testpass"
        config.personal_access_token = None

        service = JiraService(config)

        with patch("httpx.AsyncClient") as mock_client:
            # First attempt (PAT) fails with 401
            mock_response_fail = Mock()
            mock_response_fail.status_code = 401
            mock_response_fail.json.return_value = {"errorMessages": ["Invalid token"]}

            # Second attempt (basic auth) succeeds
            mock_response_success = Mock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {
                "myself": {"displayName": "Test User"}
            }

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_response_fail, mock_response_success]
            )

            # Mock deployment detection
            mock_deployment_info = DeploymentInfo(
                deployment_type=JiraDeploymentType.DATA_CENTER,
                version="9.12.22",
                build_number="912022",
                base_url_normalized="https://jira.company.com",
                supports_sso=True,
                supports_pat=True,
            )

            with patch.object(
                service.deployment_detector,
                "detect_deployment",
                return_value=mock_deployment_info,
            ), patch.object(
                service.api_version_manager, "get_working_api_version", return_value="3"
            ):

                result = await service.test_connection()

                # Should succeed with fallback authentication
                assert result.success is True

    @pytest.mark.asyncio
    async def test_api_version_fallback_v3_to_v2(self, data_center_config):
        """Test API version fallback from v3 to v2."""
        service = JiraService(data_center_config)

        with patch("httpx.AsyncClient") as mock_client:
            # v3 endpoint fails with 404
            mock_response_v3_fail = Mock()
            mock_response_v3_fail.status_code = 404

            # v2 endpoint succeeds
            mock_response_v2_success = Mock()
            mock_response_v2_success.status_code = 200
            mock_response_v2_success.json.return_value = {
                "myself": {"displayName": "Test User"}
            }

            # Ticket fetch with v2 succeeds
            mock_ticket_response = Mock()
            mock_ticket_response.status_code = 200
            mock_ticket_response.json.return_value = {
                "key": "PROJ-123",
                "fields": {
                    "summary": "Test Issue",
                    "description": "Test Description",
                    "status": {"name": "Open"},
                    "priority": {"name": "Medium"},
                    "issuetype": {"name": "Bug"},
                },
            }

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[
                    mock_response_v3_fail,
                    mock_response_v2_success,
                    mock_ticket_response,
                ]
            )

            # Mock deployment detection
            mock_deployment_info = DeploymentInfo(
                deployment_type=JiraDeploymentType.DATA_CENTER,
                version="9.12.22",
                build_number="912022",
                base_url_normalized="https://jira.company.com",
                supports_pat=True,
            )

            with patch.object(
                service.deployment_detector,
                "detect_deployment",
                return_value=mock_deployment_info,
            ):
                # Test connection (should use v2 after v3 fails)
                connection_result = await service.test_connection()
                assert connection_result.success is True

                # Test ticket fetching with v2
                ticket = await service.fetch_ticket("PROJ-123")
                assert ticket["key"] == "PROJ-123"
                assert ticket["summary"] == "Test Issue"

    @pytest.mark.asyncio
    async def test_deployment_detection_data_center_vs_cloud(self):
        """Test deployment detection distinguishing Data Center from Cloud."""
        detector = DeploymentDetector()

        # Test Data Center detection
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "9.12.22",
                "buildNumber": "912022",
                "serverId": "B8E7-9F2A-3C4D-5E6F",
                "serverTitle": "Company Jira",
            }

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            deployment_info = await detector.detect_deployment(
                "https://jira.company.com"
            )

            assert deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER
            assert deployment_info.version == "9.12.22"
            assert deployment_info.supports_pat is True
            assert deployment_info.supports_sso is True

        # Test Cloud detection
        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "1001.0.0-SNAPSHOT",
                "serverTitle": "Jira Cloud",
            }

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            deployment_info = await detector.detect_deployment(
                "https://mycompany.atlassian.net"
            )

            assert deployment_info.deployment_type == JiraDeploymentType.CLOUD
            assert deployment_info.supports_pat is False
            assert deployment_info.supports_sso is False

    @pytest.mark.asyncio
    async def test_network_configuration_ssl_and_proxy(self):
        """Test network configuration with SSL and proxy settings."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test_token",
            verify_ssl=False,
            ca_cert_path="/path/to/ca.pem",
            proxy_url="http://proxy.company.com:8080",
            timeout=60,
        )

        service = JiraService(config)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"myself": {"displayName": "Test User"}}

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Mock deployment detection
            mock_deployment_info = DeploymentInfo(
                deployment_type=JiraDeploymentType.DATA_CENTER,
                version="9.12.22",
                build_number="912022",
                base_url_normalized="https://jira.company.com",
                supports_pat=True,
            )

            with patch.object(
                service.deployment_detector,
                "detect_deployment",
                return_value=mock_deployment_info,
            ), patch.object(
                service.api_version_manager, "get_working_api_version", return_value="3"
            ):

                result = await service.test_connection()

                assert result.success is True

                # Verify httpx client was configured with correct settings
                mock_client.assert_called()
                call_kwargs = mock_client.call_args[1]
                assert call_kwargs["verify"] is False  # SSL verification disabled
                assert call_kwargs["timeout"] == 60
                assert "proxies" in call_kwargs

    @pytest.mark.asyncio
    async def test_error_handling_and_troubleshooting(self, data_center_config):
        """Test comprehensive error handling with Data Center specific guidance."""
        service = JiraService(data_center_config)
        error_handler = JiraErrorHandler(JiraDeploymentType.DATA_CENTER)

        # Test SSL certificate error
        with patch("httpx.AsyncClient") as mock_client:
            import ssl

            ssl_error = ssl.SSLError("certificate verify failed")
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=ssl_error
            )

            try:
                await service.test_connection()
                assert False, "Should have raised an exception"
            except Exception as e:
                error_detail = error_handler.create_error_detail(
                    error_message=str(e), exception=ssl_error
                )

                assert "SSL" in error_detail.error_type
                assert len(error_detail.troubleshooting_steps) > 0
                assert any(
                    "certificate" in step.lower()
                    for step in error_detail.troubleshooting_steps
                )

    @pytest.mark.asyncio
    async def test_backward_compatibility_with_cloud(self, cloud_config):
        """Test that existing Cloud configurations continue to work."""
        service = JiraService(cloud_config)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"myself": {"displayName": "Cloud User"}}

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Mock Cloud deployment detection
            mock_deployment_info = DeploymentInfo(
                deployment_type=JiraDeploymentType.CLOUD,
                version="1001.0.0-SNAPSHOT",
                base_url_normalized="https://mycompany.atlassian.net",
                supports_pat=False,
                supports_sso=False,
            )

            with patch.object(
                service.deployment_detector,
                "detect_deployment",
                return_value=mock_deployment_info,
            ), patch.object(
                service.api_version_manager, "get_working_api_version", return_value="3"
            ):

                result = await service.test_connection()

                assert result.success is True
                assert (
                    result.deployment_info.deployment_type == JiraDeploymentType.CLOUD
                )

    @pytest.mark.asyncio
    async def test_comprehensive_diagnostics_data_center(self, data_center_config):
        """Test comprehensive diagnostics for Data Center environment."""
        diagnostics = JiraDiagnostics(data_center_config)

        with patch("socket.socket") as mock_socket, patch(
            "socket.getaddrinfo"
        ) as mock_getaddrinfo, patch("httpx.AsyncClient") as mock_client:

            # Mock successful network connectivity
            mock_sock = Mock()
            mock_sock.connect_ex.return_value = 0  # Success
            mock_socket.return_value = mock_sock

            # Mock successful DNS resolution
            mock_getaddrinfo.return_value = [(2, 1, 6, "", ("192.168.1.100", 443))]

            # Mock successful version check
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "9.12.22",
                "buildNumber": "912022",
                "deploymentType": "DataCenter",
            }

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Run full diagnostics
            results = await diagnostics.run_full_diagnostics()

            assert len(results) > 0

            # Check that we have key diagnostic results
            result_names = [r.name for r in results]
            assert "Configuration Validation" in result_names
            assert "Network Connectivity" in result_names
            assert "DNS Resolution" in result_names
            assert "Version Compatibility" in result_names

    def test_configuration_validation_data_center_specific(self):
        """Test configuration validation for Data Center specific settings."""
        # Valid Data Center PAT configuration
        valid_config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test_pat_token",
            deployment_type=JiraDeploymentType.DATA_CENTER,
        )

        diagnostics = JiraDiagnostics(valid_config)
        errors = diagnostics._validate_configuration()

        assert len(errors) == 0

        # Invalid configuration - missing PAT
        invalid_config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            deployment_type=JiraDeploymentType.DATA_CENTER,
            # Missing personal_access_token
        )

        diagnostics = JiraDiagnostics(invalid_config)
        errors = diagnostics._validate_configuration()

        assert len(errors) > 0
        assert any("Personal Access Token" in error for error in errors)

    @pytest.mark.asyncio
    async def test_context_path_handling(self):
        """Test handling of custom context paths in Data Center deployments."""
        config = JiraConfig(
            base_url="https://company.com/jira-app",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test_token",
        )

        service = JiraService(config)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {
                "version": "9.12.22",
                "buildNumber": "912022",
                "serverId": "B8E7-9F2A-3C4D-5E6F",
            }

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            deployment_info = await service.deployment_detector.detect_deployment(
                config.base_url
            )

            assert deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER
            assert deployment_info.context_path == "/jira-app"
            assert deployment_info.base_url_normalized == "https://company.com/jira-app"

    @pytest.mark.asyncio
    async def test_sso_authentication_flow(self):
        """Test SSO authentication flow for Data Center."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.SSO,
            use_sso=True,
            sso_session_cookie="JSESSIONID=ABC123",
        )

        service = JiraService(config)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"myself": {"displayName": "SSO User"}}

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Mock deployment detection
            mock_deployment_info = DeploymentInfo(
                deployment_type=JiraDeploymentType.DATA_CENTER,
                version="9.12.22",
                build_number="912022",
                base_url_normalized="https://jira.company.com",
                supports_sso=True,
                supports_pat=True,
            )

            with patch.object(
                service.deployment_detector,
                "detect_deployment",
                return_value=mock_deployment_info,
            ), patch.object(
                service.api_version_manager, "get_working_api_version", return_value="3"
            ):

                result = await service.test_connection()

                assert result.success is True

                # Verify SSO cookie was used in request
                call_args = (
                    mock_client.return_value.__aenter__.return_value.get.call_args
                )
                headers = call_args[1].get("headers", {})
                assert "Cookie" in headers or "cookie" in headers

    @pytest.mark.asyncio
    async def test_performance_with_enterprise_timeouts(self):
        """Test performance with enterprise network timeouts."""
        config = JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test_token",
            timeout=120,  # Extended timeout for enterprise networks
        )

        service = JiraService(config)

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"myself": {"displayName": "Test User"}}

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Mock deployment detection
            mock_deployment_info = DeploymentInfo(
                deployment_type=JiraDeploymentType.DATA_CENTER,
                version="9.12.22",
                build_number="912022",
                base_url_normalized="https://jira.company.com",
                supports_pat=True,
            )

            with patch.object(
                service.deployment_detector,
                "detect_deployment",
                return_value=mock_deployment_info,
            ), patch.object(
                service.api_version_manager, "get_working_api_version", return_value="3"
            ):

                result = await service.test_connection()

                assert result.success is True

                # Verify timeout was configured correctly
                call_kwargs = mock_client.call_args[1]
                assert call_kwargs["timeout"] == 120


class TestJiraDataCenterAPIEndpoints:
    """Integration tests for API endpoints with Data Center support."""

    @pytest.fixture
    def data_center_config(self):
        """Data Center configuration fixture."""
        return JiraConfig(
            base_url="https://jira.company.com",
            auth_type=JiraAuthType.PERSONAL_ACCESS_TOKEN,
            personal_access_token="test_pat_token",
        )

    @pytest.mark.asyncio
    async def test_jira_test_endpoint_data_center_success(self, data_center_config):
        """Test /jira/test endpoint with Data Center configuration."""
        from app.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch("app.services.jira.JiraService.test_connection") as mock_test:
            from app.services.jira import JiraConnectionResult
            from app.services.deployment_detector import DeploymentInfo

            mock_result = JiraConnectionResult(
                success=True,
                message="Connection successful",
                deployment_info=DeploymentInfo(
                    deployment_type=JiraDeploymentType.DATA_CENTER,
                    version="9.12.22",
                    build_number="912022",
                    base_url_normalized="https://jira.company.com",
                    supports_pat=True,
                    supports_sso=True,
                ),
            )
            mock_test.return_value = mock_result

            response = client.post(
                "/jira/test",
                json={
                    "base_url": "https://jira.company.com",
                    "auth_type": "personal_access_token",
                    "personal_access_token": "test_pat_token",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ok"] is True
            assert data["deployment_info"]["deployment_type"] == "data_center"
            assert data["deployment_info"]["version"] == "9.12.22"

    @pytest.mark.asyncio
    async def test_jira_fetch_endpoint_data_center_success(self, data_center_config):
        """Test /jira/fetch endpoint with Data Center configuration."""
        from app.api import app
        from fastapi.testclient import TestClient

        client = TestClient(app)

        with patch("app.services.jira.JiraService.fetch_ticket") as mock_fetch:
            mock_ticket = {
                "key": "PROJ-123",
                "summary": "Test Issue",
                "description": "Test Description",
                "status": "Open",
                "priority": "Medium",
                "issue_type": "Bug",
            }
            mock_fetch.return_value = mock_ticket

            response = client.post(
                "/jira/fetch",
                json={
                    "base_url": "https://jira.company.com",
                    "auth_type": "personal_access_token",
                    "personal_access_token": "test_pat_token",
                    "ticket_key": "PROJ-123",
                },
            )

            assert response.status_code == 200
            data = response.json()
            assert data["ticket"]["key"] == "PROJ-123"
            assert data["ticket"]["summary"] == "Test Issue"
