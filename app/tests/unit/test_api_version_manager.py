"""Unit tests for API version manager service."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx

from app.services.api_version_manager import (
    APIVersionManager,
    APIVersionInfo,
    APIVersionError,
    create_api_version_manager,
)


class TestAPIVersionManager:
    """Test cases for APIVersionManager class."""

    @pytest.fixture
    def manager(self):
        """Create an APIVersionManager instance for testing."""
        return APIVersionManager(preferred_version="3", timeout=10)

    def test_init(self):
        """Test APIVersionManager initialization."""
        manager = APIVersionManager(preferred_version="2", timeout=15)
        assert manager.preferred_version == "2"
        assert manager.fallback_version == "2"
        assert manager.timeout == 15
        assert "3" in manager.known_versions
        assert "2" in manager.known_versions

    def test_build_endpoint_default_version(self, manager):
        """Test endpoint building with default version."""
        endpoint = manager.build_endpoint("https://jira.example.com", "issue/PROJ-123")
        assert endpoint == "https://jira.example.com/rest/api/3/issue/PROJ-123"

    def test_build_endpoint_specific_version(self, manager):
        """Test endpoint building with specific version."""
        endpoint = manager.build_endpoint("https://jira.example.com", "myself", "2")
        assert endpoint == "https://jira.example.com/rest/api/2/myself"

    def test_build_endpoint_with_leading_slash(self, manager):
        """Test endpoint building with leading slash in resource."""
        endpoint = manager.build_endpoint("https://jira.example.com", "/issue/PROJ-123")
        assert endpoint == "https://jira.example.com/rest/api/3/issue/PROJ-123"

    def test_build_endpoint_unknown_version(self, manager):
        """Test endpoint building with unknown version falls back."""
        endpoint = manager.build_endpoint("https://jira.example.com", "myself", "999")
        assert endpoint == "https://jira.example.com/rest/api/2/myself"

    def test_build_endpoint_with_context_path(self, manager):
        """Test endpoint building with base URL containing context path."""
        endpoint = manager.build_endpoint("https://company.com/jira", "myself")
        assert endpoint == "https://company.com/jira/rest/api/3/myself"

    def test_parse_version(self, manager):
        """Test version string parsing."""
        # Standard version format
        assert manager._parse_version("9.12.22") == [9, 12, 22]
        assert manager._parse_version("8.14.0") == [8, 14, 0]

        # Version with extra info
        assert manager._parse_version("9.12.22-build123") == [9, 12, 22]

        # Unknown version
        assert manager._parse_version("unknown") == [0]
        assert manager._parse_version("") == [0]

        # Partial version
        assert manager._parse_version("9.12") == [9, 12]

    def test_is_version_greater_or_equal(self, manager):
        """Test version comparison."""
        # Greater versions
        assert manager._is_version_greater_or_equal("9.12.22", "9.12.21") is True
        assert manager._is_version_greater_or_equal("9.13.0", "9.12.22") is True
        assert manager._is_version_greater_or_equal("10.0.0", "9.12.22") is True

        # Equal versions
        assert manager._is_version_greater_or_equal("9.12.22", "9.12.22") is True

        # Lesser versions
        assert manager._is_version_greater_or_equal("9.12.21", "9.12.22") is False
        assert manager._is_version_greater_or_equal("8.14.0", "9.0.0") is False

        # Different length versions
        assert manager._is_version_greater_or_equal("9.12", "9.12.0") is True
        assert manager._is_version_greater_or_equal("9.12.0", "9.12") is True

    def test_get_preferred_api_version(self, manager):
        """Test preferred API version selection based on Jira version."""
        # Modern versions should prefer v3
        assert manager.get_preferred_api_version("9.12.22") == "3"
        assert manager.get_preferred_api_version("8.14.0") == "3"
        assert manager.get_preferred_api_version("7.0.0") == "3"

        # Older versions should use v2
        assert manager.get_preferred_api_version("6.4.0") == "2"
        assert manager.get_preferred_api_version("4.0.0") == "2"

        # Unknown versions should use default
        assert manager.get_preferred_api_version("unknown") == "3"
        assert manager.get_preferred_api_version("") == "3"

    def test_is_version_compatible(self, manager):
        """Test API version compatibility with Jira versions."""
        # API v3 compatibility (requires Jira 7.0+)
        assert manager.is_version_compatible("3", "9.12.22") is True
        assert manager.is_version_compatible("3", "7.0.0") is True
        assert manager.is_version_compatible("3", "6.4.0") is False

        # API v2 compatibility (requires Jira 4.0+)
        assert manager.is_version_compatible("2", "9.12.22") is True
        assert manager.is_version_compatible("2", "4.0.0") is True
        assert manager.is_version_compatible("2", "3.13.0") is False

        # Unknown API version
        assert manager.is_version_compatible("999", "9.12.22") is False

    def test_get_version_features(self, manager):
        """Test getting features for API versions."""
        # API v3 features
        v3_features = manager.get_version_features("3")
        assert "modern_fields" in v3_features
        assert "enhanced_search" in v3_features
        assert "bulk_operations" in v3_features

        # API v2 features
        v2_features = manager.get_version_features("2")
        assert "basic_operations" in v2_features
        assert "legacy_compatibility" in v2_features

        # Unknown version
        unknown_features = manager.get_version_features("999")
        assert unknown_features == []

    @pytest.mark.asyncio
    async def test_test_api_version_success(self, manager):
        """Test successful API version testing."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await manager.test_api_version(
                "https://jira.example.com", auth_headers, "3"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_test_api_version_auth_error_still_working(self, manager):
        """Test API version testing with auth error (endpoint exists)."""
        auth_headers = {"Authorization": "Bearer invalid"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 401  # Auth error means endpoint exists

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await manager.test_api_version(
                "https://jira.example.com", auth_headers, "3"
            )
            assert result is True

    @pytest.mark.asyncio
    async def test_test_api_version_not_found(self, manager):
        """Test API version testing with not found error."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 404  # Endpoint doesn't exist

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            result = await manager.test_api_version(
                "https://jira.example.com", auth_headers, "3"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_test_api_version_timeout(self, manager):
        """Test API version testing with timeout."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.TimeoutException("Timeout")
            )

            result = await manager.test_api_version(
                "https://jira.example.com", auth_headers, "3"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_test_api_version_connection_error(self, manager):
        """Test API version testing with connection error."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch("httpx.AsyncClient") as mock_client:
            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=httpx.ConnectError("Connection failed")
            )

            result = await manager.test_api_version(
                "https://jira.example.com", auth_headers, "3"
            )
            assert result is False

    @pytest.mark.asyncio
    async def test_get_working_api_version_preferred_works(self, manager):
        """Test getting working API version when preferred version works."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch.object(manager, "test_api_version") as mock_test:
            mock_test.return_value = True

            result = await manager.get_working_api_version(
                "https://jira.example.com", auth_headers
            )
            assert result == "3"
            mock_test.assert_called_once_with(
                "https://jira.example.com", auth_headers, "3"
            )

    @pytest.mark.asyncio
    async def test_get_working_api_version_fallback_works(self, manager):
        """Test getting working API version when fallback version works."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch.object(manager, "test_api_version") as mock_test:
            # Preferred fails, fallback works
            mock_test.side_effect = [False, True]

            result = await manager.get_working_api_version(
                "https://jira.example.com", auth_headers
            )
            assert result == "2"
            assert mock_test.call_count == 2

    @pytest.mark.asyncio
    async def test_get_working_api_version_none_work(self, manager):
        """Test getting working API version when none work."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch.object(manager, "test_api_version") as mock_test:
            mock_test.return_value = False

            with pytest.raises(APIVersionError, match="No working API version found"):
                await manager.get_working_api_version(
                    "https://jira.example.com", auth_headers
                )

    @pytest.mark.asyncio
    async def test_detect_api_version_alias(self, manager):
        """Test detect_api_version as alias for get_working_api_version."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch.object(manager, "get_working_api_version") as mock_get:
            mock_get.return_value = "3"

            result = await manager.detect_api_version(
                "https://jira.example.com", auth_headers
            )
            assert result == "3"
            mock_get.assert_called_once_with("https://jira.example.com", auth_headers)

    @pytest.mark.asyncio
    async def test_get_api_version_info_multiple_versions(self, manager):
        """Test getting comprehensive API version info with multiple versions."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch.object(manager, "test_api_version") as mock_test:
            # Both v3 and v2 work
            mock_test.side_effect = [True, True]

            info = await manager.get_api_version_info(
                "https://jira.example.com", auth_headers
            )

            assert info.available_versions == ["3", "2"]
            assert info.preferred_version == "3"
            assert info.working_version == "3"
            assert info.fallback_version == "2"

    @pytest.mark.asyncio
    async def test_get_api_version_info_single_version(self, manager):
        """Test getting API version info with single working version."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch.object(manager, "test_api_version") as mock_test:
            # Only v2 works
            mock_test.side_effect = [False, True]

            info = await manager.get_api_version_info(
                "https://jira.example.com", auth_headers
            )

            assert info.available_versions == ["2"]
            assert info.preferred_version == "3"
            assert info.working_version == "2"
            assert info.fallback_version == "2"

    @pytest.mark.asyncio
    async def test_get_api_version_info_no_versions(self, manager):
        """Test getting API version info with no working versions."""
        auth_headers = {"Authorization": "Bearer token123"}

        with patch.object(manager, "test_api_version") as mock_test:
            mock_test.return_value = False

            info = await manager.get_api_version_info(
                "https://jira.example.com", auth_headers
            )

            assert info.available_versions == []
            assert info.preferred_version == "3"
            assert info.working_version is None
            assert info.fallback_version is None


class TestCreateAPIVersionManager:
    """Test cases for create_api_version_manager factory function."""

    def test_create_api_version_manager_default(self):
        """Test factory function with default parameters."""
        manager = create_api_version_manager()
        assert isinstance(manager, APIVersionManager)
        assert manager.preferred_version == "3"
        assert manager.timeout == 30

    def test_create_api_version_manager_custom(self):
        """Test factory function with custom parameters."""
        manager = create_api_version_manager(preferred_version="2", timeout=60)
        assert isinstance(manager, APIVersionManager)
        assert manager.preferred_version == "2"
        assert manager.timeout == 60


class TestAPIVersionInfo:
    """Test cases for APIVersionInfo model."""

    def test_api_version_info_creation(self):
        """Test APIVersionInfo model creation."""
        info = APIVersionInfo(
            available_versions=["3", "2"],
            preferred_version="3",
            working_version="3",
            fallback_version="2",
        )

        assert info.available_versions == ["3", "2"]
        assert info.preferred_version == "3"
        assert info.working_version == "3"
        assert info.fallback_version == "2"

    def test_api_version_info_minimal(self):
        """Test APIVersionInfo model with minimal data."""
        info = APIVersionInfo(available_versions=["2"], preferred_version="3")

        assert info.available_versions == ["2"]
        assert info.preferred_version == "3"
        assert info.working_version is None
        assert info.fallback_version is None


class TestAPIVersionManagerIntegration:
    """Integration test cases for APIVersionManager."""

    @pytest.fixture
    def manager(self):
        """Create an APIVersionManager instance for integration testing."""
        return APIVersionManager(preferred_version="3", timeout=5)

    @pytest.mark.asyncio
    async def test_full_workflow_preferred_version_works(self, manager):
        """Test full workflow when preferred version works."""
        auth_headers = {"Authorization": "Bearer token123"}
        base_url = "https://jira.example.com"

        with patch("httpx.AsyncClient") as mock_client:
            mock_response = MagicMock()
            mock_response.status_code = 200

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Test the full workflow
            working_version = await manager.get_working_api_version(
                base_url, auth_headers
            )
            assert working_version == "3"

            # Build endpoint with detected version
            endpoint = manager.build_endpoint(
                base_url, "issue/PROJ-123", working_version
            )
            assert endpoint == "https://jira.example.com/rest/api/3/issue/PROJ-123"

            # Check compatibility
            assert manager.is_version_compatible(working_version, "9.12.22") is True

            # Get features
            features = manager.get_version_features(working_version)
            assert "modern_fields" in features

    @pytest.mark.asyncio
    async def test_full_workflow_fallback_version_works(self, manager):
        """Test full workflow when only fallback version works."""
        auth_headers = {"Authorization": "Bearer token123"}
        base_url = "https://jira.example.com"

        with patch("httpx.AsyncClient") as mock_client:
            # First call (v3) fails with 404, second call (v2) succeeds
            mock_response_fail = MagicMock()
            mock_response_fail.status_code = 404

            mock_response_success = MagicMock()
            mock_response_success.status_code = 200

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                side_effect=[mock_response_fail, mock_response_success]
            )

            # Test the full workflow
            working_version = await manager.get_working_api_version(
                base_url, auth_headers
            )
            assert working_version == "2"

            # Build endpoint with detected version
            endpoint = manager.build_endpoint(
                base_url, "issue/PROJ-123", working_version
            )
            assert endpoint == "https://jira.example.com/rest/api/2/issue/PROJ-123"

            # Check compatibility
            assert manager.is_version_compatible(working_version, "9.12.22") is True

            # Get features
            features = manager.get_version_features(working_version)
            assert "basic_operations" in features
