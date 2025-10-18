"""Jira deployment detection service for identifying deployment type and version."""

import json
import re
from typing import Dict, Optional, Any, Union
from urllib.parse import urlparse, urljoin

import httpx
from pydantic import BaseModel

from app.config import JiraDeploymentType


class DeploymentInfo(BaseModel):
    """Information about a Jira deployment."""

    deployment_type: JiraDeploymentType
    version: str
    build_number: Optional[Union[str, int]] = None
    base_url_normalized: str
    context_path: Optional[str] = None
    supports_sso: bool = False
    supports_pat: bool = False
    server_title: Optional[str] = None
    server_id: Optional[str] = None


class VersionInfo(BaseModel):
    """Jira version information."""

    version: str
    build_number: Optional[Union[str, int]] = None
    build_date: Optional[str] = None
    database_version: Optional[str] = None
    server_id: Optional[str] = None
    server_title: Optional[str] = None


class DeploymentDetectionError(Exception):
    """Exception raised when deployment detection fails."""

    pass


class DeploymentDetector:
    """Service for detecting Jira deployment type and version information."""

    def __init__(
        self,
        timeout: int = 30,
        verify_ssl: bool = True,
        ca_cert_path: Optional[str] = None,
        proxy_url: Optional[str] = None,
    ):
        """Initialize deployment detector.

        Args:
            timeout: HTTP request timeout in seconds
        # Get logger from service registry
        self.logger = require_service('logger', context='DeploymentInfo')
            verify_ssl: Whether to verify SSL certificates
            ca_cert_path: Path to custom CA certificate bundle
            proxy_url: Proxy URL for HTTP requests
        """
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.ca_cert_path = ca_cert_path
        self.proxy_url = proxy_url

        # Known Cloud URL patterns
        self.cloud_patterns = [
            r".*\.atlassian\.net",
            r".*\.atlassian\.com",
            r".*\.jira\.com",
        ]

        # Data Center version requirements
        self.min_data_center_version = "9.0.0"
        self.compatible_data_center_versions = ["9.12.22"]

    def _get_verify_config(self) -> Union[bool, str]:
        """Get SSL verification configuration for httpx.

        Returns:
            SSL verification configuration (bool or path to CA bundle)
        """
        if not self.verify_ssl:
            return False

        if self.ca_cert_path:
            return self.ca_cert_path

        return True

    def _get_proxy_config(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration for httpx.

        Returns:
            Proxy configuration dictionary or None
        """
        if not self.proxy_url:
            return None

        return {"http://": self.proxy_url, "https://": self.proxy_url}

    async def detect_deployment(
        self, base_url: str, auth_headers: Optional[Dict[str, str]] = None
    ) -> DeploymentInfo:
        """Detect Jira deployment type and basic information.

        Args:
            base_url: Jira base URL
            auth_headers: Optional authentication headers

        Returns:
            DeploymentInfo object with deployment details

        Raises:
            DeploymentDetectionError: If detection fails
        """
        try:
            # Normalize the base URL
            normalized_url = self._normalize_base_url(base_url)
            parsed_url = urlparse(normalized_url)

            # Extract context path if present
            context_path = self._extract_context_path(parsed_url.path)

            # First, try URL-based detection
            deployment_type = self._detect_from_url(normalized_url)

            # Get version information
            version_info = await self._get_version_info(normalized_url, auth_headers)

            # If URL-based detection was inconclusive, use version info
            if deployment_type is None:
                deployment_type = self._detect_from_version_info(version_info)

            # Determine feature support based on deployment type and version
            supports_sso = self._supports_sso(deployment_type, version_info.version)
            supports_pat = self._supports_pat(deployment_type, version_info.version)

            self.logger.info(
                f"Detected Jira deployment: {deployment_type.value} version {version_info.version}"
            )

            return DeploymentInfo(
                deployment_type=deployment_type,
                version=version_info.version,
                build_number=version_info.build_number,
                base_url_normalized=normalized_url,
                context_path=context_path,
                supports_sso=supports_sso,
                supports_pat=supports_pat,
                server_title=version_info.server_title,
                server_id=version_info.server_id,
            )

        except Exception as e:
            self.logger.error(f"Failed to detect Jira deployment for {base_url}: {e}")
            raise DeploymentDetectionError(f"Deployment detection failed: {str(e)}")

    async def get_version_info(
        self, base_url: str, auth_headers: Optional[Dict[str, str]] = None
    ) -> VersionInfo:
        """Get detailed Jira version information.

        Args:
            base_url: Jira base URL
            auth_headers: Optional authentication headers

        Returns:
            VersionInfo object with version details

        Raises:
            DeploymentDetectionError: If version detection fails
        """
        return await self._get_version_info(base_url, auth_headers)

    def is_data_center_compatible(self, version: str) -> bool:
        """Check if version is compatible with Data Center implementation.

        Args:
            version: Jira version string

        Returns:
            True if version is compatible
        """
        try:
            # Parse version numbers for comparison
            version_parts = self._parse_version(version)
            min_version_parts = self._parse_version(self.min_data_center_version)

            # Compare major.minor.patch
            for i in range(min(len(version_parts), len(min_version_parts))):
                if version_parts[i] > min_version_parts[i]:
                    return True
                elif version_parts[i] < min_version_parts[i]:
                    return False

            # If all compared parts are equal, check if we have enough parts
            return len(version_parts) >= len(min_version_parts)

        except Exception as e:
            self.logger.warning(f"Failed to parse version {version}: {e}")
            return False

    def _normalize_base_url(self, base_url: str) -> str:
        """Normalize base URL by removing trailing slashes and ensuring protocol.

        Args:
            base_url: Raw base URL

        Returns:
            Normalized base URL
        """
        url = base_url.strip().rstrip("/")

        # Add protocol if missing
        if not url.startswith(("http://", "https://")):
            url = f"https://{url}"

        return url

    def _extract_context_path(self, path: str) -> Optional[str]:
        """Extract context path from URL path.

        Args:
            path: URL path component

        Returns:
            Context path if present, None otherwise
        """
        if not path or path == "/":
            return None

        # Remove leading and trailing slashes
        context = path.strip("/")

        # If we have a path, it's likely a context path
        # Common Jira paths like /jira, /secure, /browse are usually part of the application
        # but custom context paths like /jira-app, /company-jira should be detected
        if context:
            # Common Jira internal paths that are NOT context paths
            jira_internal_paths = ["secure", "browse", "rest", "plugins"]

            # If it's just "jira", it could be either a context path or internal path
            # We'll consider it a context path if it's not one of the known internal paths
            if context not in jira_internal_paths:
                return context

        return None

    def _detect_from_url(self, base_url: str) -> Optional[JiraDeploymentType]:
        """Detect deployment type from URL patterns.

        Args:
            base_url: Normalized base URL

        Returns:
            Deployment type if detectable from URL, None otherwise
        """
        parsed_url = urlparse(base_url)
        hostname = parsed_url.hostname

        if not hostname:
            return None

        # Check against known Cloud patterns
        for pattern in self.cloud_patterns:
            if re.match(pattern, hostname, re.IGNORECASE):
                return JiraDeploymentType.CLOUD

        # If it doesn't match Cloud patterns, it's likely Data Center or Server
        # We'll need version info to distinguish between them
        return None

    async def _get_version_info(
        self, base_url: str, auth_headers: Optional[Dict[str, str]] = None
    ) -> VersionInfo:
        """Get version information from Jira server info endpoint.

        Args:
            base_url: Normalized base URL
            auth_headers: Optional authentication headers

        Returns:
            VersionInfo object

        Raises:
            DeploymentDetectionError: If version info cannot be retrieved
        """
        try:
            verify_config = self._get_verify_config()
            proxy_config = self._get_proxy_config()

            # Build client configuration
            client_config = {"timeout": self.timeout, "verify": verify_config}

            # Only add proxies if configured
            if proxy_config:
                client_config["proxies"] = proxy_config

            async with httpx.AsyncClient(**client_config) as client:
                # Try the server info endpoint first (usually accessible without auth)
                url = urljoin(base_url, "/rest/api/2/serverInfo")
                headers = {"Accept": "application/json"}

                if auth_headers:
                    headers.update(auth_headers)

                self.logger.debug(f"Fetching server info from: {url}")
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    try:
                        data = response.json()
                        return self._parse_server_info(data)
                    except (ValueError, json.JSONDecodeError) as e:
                        self.logger.error(
                            f"Failed to parse JSON response from {url}: {e}"
                        )
                        self.logger.debug(f"Response content: {response.text[:200]}...")
                        raise DeploymentDetectionError(
                            f"Invalid JSON response from server info endpoint: {e}"
                        )

                # If server info fails, try the myself endpoint (requires auth)
                if auth_headers:
                    url = urljoin(base_url, "/rest/api/2/myself")
                    response = await client.get(url, headers=headers)

                    if response.status_code == 200:
                        # The myself endpoint doesn't have version info,
                        # but we can infer it's a working Jira instance
                        self.logger.warning("Could not get version info, using default")
                        return VersionInfo(version="unknown")

                # Try without authentication for public server info
                if auth_headers:
                    headers = {"Accept": "application/json"}
                    url = urljoin(base_url, "/rest/api/2/serverInfo")
                    response = await client.get(url, headers=headers)

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            return self._parse_server_info(data)
                        except (ValueError, json.JSONDecodeError) as e:
                            self.logger.error(
                                f"Failed to parse JSON response from {url}: {e}"
                            )
                            self.logger.debug(
                                f"Response content: {response.text[:200]}..."
                            )
                            raise DeploymentDetectionError(
                                f"Invalid JSON response from server info endpoint: {e}"
                            )

                raise DeploymentDetectionError(
                    f"Could not retrieve version info: HTTP {response.status_code}"
                )

        except httpx.TimeoutException:
            raise DeploymentDetectionError(f"Timeout after {self.timeout} seconds")
        except httpx.ConnectError:
            raise DeploymentDetectionError("Failed to connect to Jira server")
        except Exception as e:
            raise DeploymentDetectionError(f"Version detection failed: {str(e)}")

    def _parse_server_info(self, data: Dict[str, Any]) -> VersionInfo:
        """Parse server info response into VersionInfo object.

        Args:
            data: Server info response data

        Returns:
            VersionInfo object
        """
        return VersionInfo(
            version=data.get("version", "unknown"),
            build_number=data.get("buildNumber"),
            build_date=data.get("buildDate"),
            database_version=data.get("databaseVersion"),
            server_id=data.get("serverId"),
            server_title=data.get("serverTitle", "Jira"),
        )

    def _detect_from_version_info(
        self, version_info: VersionInfo
    ) -> JiraDeploymentType:
        """Detect deployment type from version information.

        Args:
            version_info: Version information

        Returns:
            Detected deployment type
        """
        # Cloud instances typically have specific version patterns
        # and don't expose detailed server info
        if version_info.server_id is None and version_info.build_number is None:
            return JiraDeploymentType.CLOUD

        # Data Center and Server instances expose more detailed info
        # We'll default to Data Center for modern versions
        try:
            version_parts = self._parse_version(version_info.version)
            if len(version_parts) >= 2 and version_parts[0] >= 8:
                return JiraDeploymentType.DATA_CENTER
            else:
                return JiraDeploymentType.SERVER
        except Exception:
            # If we can't parse the version, assume Data Center
            return JiraDeploymentType.DATA_CENTER

    def _supports_sso(self, deployment_type: JiraDeploymentType, version: str) -> bool:
        """Check if deployment supports SSO authentication.

        Args:
            deployment_type: Detected deployment type
            version: Jira version

        Returns:
            True if SSO is supported
        """
        # Cloud always supports SSO
        if deployment_type == JiraDeploymentType.CLOUD:
            return True

        # Data Center supports SSO in most configurations
        if deployment_type == JiraDeploymentType.DATA_CENTER:
            return True

        # Server may support SSO depending on configuration
        return False

    def _supports_pat(self, deployment_type: JiraDeploymentType, version: str) -> bool:
        """Check if deployment supports Personal Access Tokens.

        Args:
            deployment_type: Detected deployment type
            version: Jira version

        Returns:
            True if PAT is supported
        """
        # Cloud supports API tokens (similar to PAT)
        if deployment_type == JiraDeploymentType.CLOUD:
            return True

        # Data Center supports PAT from version 8.14+
        if deployment_type == JiraDeploymentType.DATA_CENTER:
            try:
                version_parts = self._parse_version(version)
                if len(version_parts) >= 2:
                    major, minor = version_parts[0], version_parts[1]
                    return major > 8 or (major == 8 and minor >= 14)
            except Exception:
                pass
            return True  # Assume modern Data Center supports PAT

        # Server may not support PAT
        return False

    def _parse_version(self, version: str) -> list[int]:
        """Parse version string into list of integers.

        Args:
            version: Version string (e.g., "9.12.22")

        Returns:
            List of version parts as integers
        """
        if not version or version == "unknown":
            return [0]

        # Extract numeric parts from version string
        version_match = re.match(r"^(\d+)\.(\d+)\.(\d+)", version)
        if version_match:
            return [int(x) for x in version_match.groups()]

        # Fallback: try to extract any numbers
        numbers = re.findall(r"\d+", version)
        if numbers:
            return [int(x) for x in numbers[:3]]  # Take first 3 numbers

        return [0]


def create_deployment_detector(timeout: int = 30) -> DeploymentDetector:
    """Factory function to create DeploymentDetector instance.

    Args:
        timeout: HTTP request timeout in seconds

    Returns:
        DeploymentDetector instance
    """
    return DeploymentDetector(timeout=timeout)
