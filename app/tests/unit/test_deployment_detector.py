"""Unit tests for deployment detector service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.deployment_detector import (
    DeploymentDetector,
    DeploymentInfo,
    VersionInfo,
    DeploymentDetectionError,
    create_deployment_detector,
)
from app.config import JiraDeploymentType


class TestDeploymentDetector:
    """Test cases for DeploymentDetector class."""

    @pytest.fixture
    def detector(self):
        """Create a DeploymentDetector instance for testing."""
        return DeploymentDetector(timeout=10)

    def test_init(self):
        """Test DeploymentDetector initialization."""
        detector = DeploymentDetector(timeout=15)
        assert detector.timeout == 15
        assert len(detector.cloud_patterns) > 0
        assert detector.min_data_center_version == "9.0.0"

    def test_normalize_base_url(self, detector):
        """Test URL normalization."""
        # Test with protocol
        assert (
            detector._normalize_base_url("https://example.com/")
            == "https://example.com"
        )
        assert (
            detector._normalize_base_url("http://example.com") == "http://example.com"
        )

        # Test without protocol
        assert detector._normalize_base_url("example.com") == "https://example.com"
        assert detector._normalize_base_url("example.com/") == "https://example.com"

        # Test with trailing slashes
        assert (
            detector._normalize_base_url("https://example.com///")
            == "https://example.com"
        )

    def test_extract_context_path(self, detector):
        """Test context path extraction."""
        # No context path
        assert detector._extract_context_path("/") is None
        assert detector._extract_context_path("") is None

        # Valid context paths
        assert detector._extract_context_path("/mycontext") == "mycontext"
        assert detector._extract_context_path("/mycontext/") == "mycontext"
        assert detector._extract_context_path("/jira-app") == "jira-app"
        assert detector._extract_context_path("/company-jira") == "company-jira"

        # Jira context path (should be detected)
        assert detector._extract_context_path("/jira") == "jira"

        # Common Jira internal paths (not context paths)
        assert detector._extract_context_path("/secure") is None
        assert detector._extract_context_path("/browse") is None
        assert detector._extract_context_path("/rest") is None

    def test_detect_from_url_cloud(self, detector):
        """Test Cloud detection from URL patterns."""
        cloud_urls = [
            "https://mycompany.atlassian.net",
            "https://test.atlassian.com",
            "https://example.jira.com",
        ]

        for url in cloud_urls:
            result = detector._detect_from_url(url)
            assert result == JiraDeploymentType.CLOUD

    def test_detect_from_url_non_cloud(self, detector):
        """Test non-Cloud URL detection."""
        non_cloud_urls = [
            "https://jira.company.com",
            "https://internal-jira.local",
            "https://192.168.1.100:8080",
        ]

        for url in non_cloud_urls:
            result = detector._detect_from_url(url)
            assert result is None  # Needs version info to determine

    def test_parse_version(self, detector):
        """Test version string parsing."""
        # Standard version format
        assert detector._parse_version("9.12.22") == [9, 12, 22]
        assert detector._parse_version("8.14.0") == [8, 14, 0]

        # Version with extra info
        assert detector._parse_version("9.12.22-build123") == [9, 12, 22]

        # Unknown version
        assert detector._parse_version("unknown") == [0]
        assert detector._parse_version("") == [0]

        # Partial version
        assert detector._parse_version("9.12") == [9, 12]

    def test_is_data_center_compatible(self, detector):
        """Test Data Center version compatibility check."""
        # Compatible versions
        assert detector.is_data_center_compatible("9.12.22") is True
        assert detector.is_data_center_compatible("10.0.0") is True
        assert detector.is_data_center_compatible("9.0.0") is True

        # Incompatible versions
        assert detector.is_data_center_compatible("8.14.0") is False
        assert detector.is_data_center_compatible("7.13.0") is False

        # Edge cases
        assert detector.is_data_center_compatible("unknown") is False
        assert detector.is_data_center_compatible("") is False

    def test_parse_server_info(self, detector):
        """Test server info parsing."""
        server_data = {
            "version": "9.12.22",
            "buildNumber": "912022",
            "buildDate": "2023-10-15T10:30:00.000+0000",
            "databaseVersion": "912022",
            "serverId": "B8E7-9F2A-3C4D-5E6F",
            "serverTitle": "My Jira Instance",
        }

        version_info = detector._parse_server_info(server_data)

        assert version_info.version == "9.12.22"
        assert version_info.build_number == "912022"
        assert version_info.build_date == "2023-10-15T10:30:00.000+0000"
        assert version_info.database_version == "912022"
        assert version_info.server_id == "B8E7-9F2A-3C4D-5E6F"
        assert version_info.server_title == "My Jira Instance"

    def test_detect_from_version_info_cloud(self, detector):
        """Test Cloud detection from version info."""
        # Cloud-like version info (minimal info)
        version_info = VersionInfo(
            version="1001.0.0-SNAPSHOT", server_id=None, build_number=None
        )

        result = detector._detect_from_version_info(version_info)
        assert result == JiraDeploymentType.CLOUD

    def test_detect_from_version_info_data_center(self, detector):
        """Test Data Center detection from version info."""
        # Data Center-like version info (detailed info)
        version_info = VersionInfo(
            version="9.12.22", server_id="B8E7-9F2A-3C4D-5E6F", build_number="912022"
        )

        result = detector._detect_from_version_info(version_info)
        assert result == JiraDeploymentType.DATA_CENTER

    def test_detect_from_version_info_server(self, detector):
        """Test Server detection from version info."""
        # Old version (Server)
        version_info = VersionInfo(
            version="7.13.0", server_id="B8E7-9F2A-3C4D-5E6F", build_number="713000"
        )

        result = detector._detect_from_version_info(version_info)
        assert result == JiraDeploymentType.SERVER

    def test_supports_sso(self, detector):
        """Test SSO support detection."""
        # Cloud always supports SSO
        assert detector._supports_sso(JiraDeploymentType.CLOUD, "1001.0.0") is True

        # Data Center supports SSO
        assert detector._supports_sso(JiraDeploymentType.DATA_CENTER, "9.12.22") is True

        # Server may not support SSO
        assert detector._supports_sso(JiraDeploymentType.SERVER, "7.13.0") is False

    def test_supports_pat(self, detector):
        """Test PAT support detection."""
        # Cloud supports API tokens
        assert detector._supports_pat(JiraDeploymentType.CLOUD, "1001.0.0") is True

        # Data Center supports PAT from 8.14+
        assert detector._supports_pat(JiraDeploymentType.DATA_CENTER, "9.12.22") is True
        assert detector._supports_pat(JiraDeploymentType.DATA_CENTER, "8.14.0") is True
        assert detector._supports_pat(JiraDeploymentType.DATA_CENTER, "8.13.0") is False

        # Server may not support PAT
        assert detector._supports_pat(JiraDeploymentType.SERVER, "7.13.0") is False

    @pytest.mark.asyncio
    async def test_get_version_info_success(self, detector):
        """Test successful version info retrieval."""
        server_data = {
            "version": "9.12.22",
            "buildNumber": "912022",
            "serverId": "B8E7-9F2A-3C4D-5E6F",
            "serverTitle": "Test Jira",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = server_data

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            version_info = await detector._get_version_info("https://jira.example.com")

            assert version_info.version == "9.12.22"
            assert version_info.build_number == "912022"
            assert version_info.server_id == "B8E7-9F2A-3C4D-5E6F"
            assert version_info.server_title == "Test Jira"

    @pytest.mark.asyncio
    async def test_get_version_info_with_auth_fallback(self, detector):
        """Test version info retrieval with authentication fallback."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch("httpx.AsyncClient") as mock_client:
            # First call (serverInfo) fails
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 401

            # Second call (myself) succeeds but no version info
            mock_response_success = MagicMock()
            mock_response_success.status_code = 200
            mock_response_success.json.return_value = {"displayName": "Test User"}

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_response_fail, mock_response_success]
            )

            version_info = await detector._get_version_info(
                "https://jira.example.com", auth_headers
            )

            assert version_info.version == "unknown"

    @pytest.mark.asyncio
    async def test_get_version_info_timeout(self, detector):
        """Test version info retrieval timeout."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            with pytest.raises(DeploymentDetectionError, match="Timeout"):
                await detector._get_version_info("https://jira.example.com")

    @pytest.mark.asyncio
    async def test_get_version_info_connection_error(self, detector):
        """Test version info retrieval connection error."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            with pytest.raises(DeploymentDetectionError, match="Failed to connect"):
                await detector._get_version_info("https://jira.example.com")

    @pytest.mark.asyncio
    async def test_detect_deployment_cloud_success(self, detector):
        """Test successful Cloud deployment detection."""
        server_data = {"version": "1001.0.0-SNAPSHOT", "serverTitle": "Jira Cloud"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = server_data

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            deployment_info = await detector.detect_deployment(
                "https://mycompany.atlassian.net"
            )

            assert deployment_info.deployment_type == JiraDeploymentType.CLOUD
            assert deployment_info.version == "1001.0.0-SNAPSHOT"
            assert (
                deployment_info.base_url_normalized == "https://mycompany.atlassian.net"
            )
            assert deployment_info.supports_sso is True
            assert deployment_info.supports_pat is True

    @pytest.mark.asyncio
    async def test_detect_deployment_data_center_success(self, detector):
        """Test successful Data Center deployment detection."""
        server_data = {
            "version": "9.12.22",
            "buildNumber": "912022",
            "serverId": "B8E7-9F2A-3C4D-5E6F",
            "serverTitle": "Company Jira",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = server_data

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            deployment_info = await detector.detect_deployment(
                "https://jira.company.com"
            )

            assert deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER
            assert deployment_info.version == "9.12.22"
            assert deployment_info.build_number == "912022"
            assert deployment_info.base_url_normalized == "https://jira.company.com"
            assert deployment_info.supports_sso is True
            assert deployment_info.supports_pat is True

    @pytest.mark.asyncio
    async def test_detect_deployment_with_context_path(self, detector):
        """Test deployment detection with custom context path."""
        server_data = {
            "version": "9.12.22",
            "buildNumber": "912022",
            "serverId": "B8E7-9F2A-3C4D-5E6F",
        }

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = server_data

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            deployment_info = await detector.detect_deployment(
                "https://company.com/jira-app"
            )

            assert deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER
            assert deployment_info.context_path == "jira-app"
            assert deployment_info.base_url_normalized == "https://company.com/jira-app"

    @pytest.mark.asyncio
    async def test_detect_deployment_failure(self, detector):
        """Test deployment detection failure."""
        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            with pytest.raises(DeploymentDetectionError):
                await detector.detect_deployment("https://invalid.example.com")

    @pytest.mark.asyncio
    async def test_get_version_info_public_method(self, detector):
        """Test public get_version_info method."""
        server_data = {"version": "9.12.22", "buildNumber": "912022"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = server_data

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            version_info = await detector.get_version_info("https://jira.example.com")

            assert version_info.version == "9.12.22"
            assert version_info.build_number == "912022"


class TestCreateDeploymentDetector:
    """Test cases for create_deployment_detector factory function."""

    def test_create_deployment_detector_default(self):
        """Test factory function with default timeout."""
        detector = create_deployment_detector()
        assert isinstance(detector, DeploymentDetector)
        assert detector.timeout == 30

    def test_create_deployment_detector_custom_timeout(self):
        """Test factory function with custom timeout."""
        detector = create_deployment_detector(timeout=60)
        assert isinstance(detector, DeploymentDetector)
        assert detector.timeout == 60


class TestDeploymentInfo:
    """Test cases for DeploymentInfo model."""

    def test_deployment_info_creation(self):
        """Test DeploymentInfo model creation."""
        info = DeploymentInfo(
            deployment_type=JiraDeploymentType.DATA_CENTER,
            version="9.12.22",
            build_number="912022",
            base_url_normalized="https://jira.company.com",
            context_path="jira",
            supports_sso=True,
            supports_pat=True,
            server_title="Company Jira",
            server_id="B8E7-9F2A-3C4D-5E6F",
        )

        assert info.deployment_type == JiraDeploymentType.DATA_CENTER
        assert info.version == "9.12.22"
        assert info.build_number == "912022"
        assert info.base_url_normalized == "https://jira.company.com"
        assert info.context_path == "jira"
        assert info.supports_sso is True
        assert info.supports_pat is True
        assert info.server_title == "Company Jira"
        assert info.server_id == "B8E7-9F2A-3C4D-5E6F"

    def test_deployment_info_minimal(self):
        """Test DeploymentInfo model with minimal data."""
        info = DeploymentInfo(
            deployment_type=JiraDeploymentType.CLOUD,
            version="1001.0.0",
            base_url_normalized="https://company.atlassian.net",
        )

        assert info.deployment_type == JiraDeploymentType.CLOUD
        assert info.version == "1001.0.0"
        assert info.base_url_normalized == "https://company.atlassian.net"
        assert info.build_number is None
        assert info.context_path is None
        assert info.supports_sso is False
        assert info.supports_pat is False


class TestVersionInfo:
    """Test cases for VersionInfo model."""

    def test_version_info_creation(self):
        """Test VersionInfo model creation."""
        info = VersionInfo(
            version="9.12.22",
            build_number="912022",
            build_date="2023-10-15T10:30:00.000+0000",
            database_version="912022",
            server_id="B8E7-9F2A-3C4D-5E6F",
            server_title="Test Jira",
        )

        assert info.version == "9.12.22"
        assert info.build_number == "912022"
        assert info.build_date == "2023-10-15T10:30:00.000+0000"
        assert info.database_version == "912022"
        assert info.server_id == "B8E7-9F2A-3C4D-5E6F"
        assert info.server_title == "Test Jira"

    def test_version_info_minimal(self):
        """Test VersionInfo model with minimal data."""
        info = VersionInfo(version="unknown")

        assert info.version == "unknown"
        assert info.build_number is None
        assert info.build_date is None
        assert info.database_version is None
        assert info.server_id is None
        assert info.server_title is None
