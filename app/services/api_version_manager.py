"""Jira API version detection and management service."""

import re
from typing import Dict, Optional, List, Union
from urllib.parse import urljoin

import httpx
from pydantic import BaseModel

from app.utils.logger import app_logger


class APIVersionInfo(BaseModel):
    """Information about available API versions."""
    available_versions: List[str]
    preferred_version: str
    working_version: Optional[str] = None
    fallback_version: Optional[str] = None


class APIVersionError(Exception):
    """Exception raised when API version operations fail."""
    pass


class APIVersionManager:
    """Service for managing Jira API version selection and endpoint construction."""
    
    def __init__(self, preferred_version: str = "3", timeout: int = 30, verify_ssl: bool = True, ca_cert_path: Optional[str] = None, proxy_url: Optional[str] = None):
        """Initialize API version manager.
        
        Args:
            preferred_version: Preferred API version to use (default: "3")
            timeout: HTTP request timeout in seconds
            verify_ssl: Whether to verify SSL certificates
            ca_cert_path: Path to custom CA certificate bundle
            proxy_url: Proxy URL for HTTP requests
        """
        self.preferred_version = preferred_version
        self.fallback_version = "2"
        self.timeout = timeout
        self.verify_ssl = verify_ssl
        self.ca_cert_path = ca_cert_path
        self.proxy_url = proxy_url
        
        # Known API versions in order of preference
        self.known_versions = ["3", "2"]
        
        # Version-specific endpoint mappings
        self.version_endpoints = {
            "3": "/rest/api/3",
            "2": "/rest/api/2"
        }
        
        # Version compatibility requirements (minimum Jira version)
        self.version_compatibility = {
            "3": {
                "min_jira_version": "7.0.0",
                "features": ["modern_fields", "enhanced_search", "bulk_operations"]
            },
            "2": {
                "min_jira_version": "4.0.0", 
                "features": ["basic_operations", "legacy_compatibility"]
            }
        }
    
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
        
        return {
            "http://": self.proxy_url,
            "https://": self.proxy_url
        }
    
    def build_endpoint(self, base_url: str, resource: str, api_version: Optional[str] = None) -> str:
        """Build API endpoint URL with appropriate version.
        
        Args:
            base_url: Jira base URL
            resource: API resource path (e.g., "issue/PROJ-123", "myself")
            api_version: Specific API version to use (defaults to preferred)
            
        Returns:
            Complete API endpoint URL
        """
        version = api_version or self.preferred_version
        
        # Ensure version is supported
        if version not in self.version_endpoints:
            app_logger.warning(f"Unknown API version {version}, falling back to {self.fallback_version}")
            version = self.fallback_version
        
        # Build the endpoint URL
        api_base = self.version_endpoints[version]
        resource = resource.lstrip('/')  # Remove leading slash if present
        
        # Ensure base_url ends with slash for proper joining
        base_url = base_url.rstrip('/') + '/'
        api_path = api_base.lstrip('/') + '/' + resource
        
        endpoint = urljoin(base_url, api_path)
        
        app_logger.debug(f"Built endpoint: {endpoint} (version: {version})")
        return endpoint
    
    async def test_api_version(self, base_url: str, auth_headers: Dict[str, str], version: str) -> bool:
        """Test if specific API version is available and working.
        
        Args:
            base_url: Jira base URL
            auth_headers: Authentication headers
            version: API version to test
            
        Returns:
            True if API version is working, False otherwise
        """
        try:
            # Test with a simple endpoint that should exist in all versions
            endpoint = self.build_endpoint(base_url, "myself", version)
            
            verify_config = self._get_verify_config()
            proxy_config = self._get_proxy_config()
            
            # Build client configuration
            client_config = {
                "timeout": self.timeout,
                "verify": verify_config
            }
            
            # Only add proxies if configured
            if proxy_config:
                client_config["proxies"] = proxy_config
            
            async with httpx.AsyncClient(**client_config) as client:
                headers = {"Accept": "application/json"}
                headers.update(auth_headers)
                
                app_logger.debug(f"Testing API version {version} at: {endpoint}")
                response = await client.get(endpoint, headers=headers)
                
                # Consider it working if we get a successful response or auth error
                # (auth error means the endpoint exists but we need proper auth)
                is_working = response.status_code in [200, 401, 403]
                
                if is_working:
                    app_logger.info(f"API version {version} is available")
                else:
                    app_logger.warning(f"API version {version} test failed: HTTP {response.status_code}")
                
                return is_working
                
        except httpx.TimeoutException:
            app_logger.warning(f"Timeout testing API version {version}")
            return False
        except httpx.ConnectError:
            app_logger.warning(f"Connection error testing API version {version}")
            return False
        except Exception as e:
            app_logger.warning(f"Error testing API version {version}: {e}")
            return False
    
    async def get_working_api_version(self, base_url: str, auth_headers: Dict[str, str]) -> str:
        """Get working API version with fallback logic.
        
        Args:
            base_url: Jira base URL
            auth_headers: Authentication headers
            
        Returns:
            Working API version string
            
        Raises:
            APIVersionError: If no API version is working
        """
        # Test preferred version first
        if await self.test_api_version(base_url, auth_headers, self.preferred_version):
            app_logger.info(f"Using preferred API version: {self.preferred_version}")
            return self.preferred_version
        
        # Test fallback version
        if await self.test_api_version(base_url, auth_headers, self.fallback_version):
            app_logger.info(f"Using fallback API version: {self.fallback_version}")
            return self.fallback_version
        
        # Test all known versions as last resort
        for version in self.known_versions:
            if version not in [self.preferred_version, self.fallback_version]:
                if await self.test_api_version(base_url, auth_headers, version):
                    app_logger.info(f"Using discovered API version: {version}")
                    return version
        
        # If nothing works, raise an error
        raise APIVersionError("No working API version found")
    
    async def detect_api_version(self, base_url: str, auth_headers: Dict[str, str]) -> str:
        """Detect which API version to use based on availability.
        
        This is an alias for get_working_api_version for backward compatibility.
        
        Args:
            base_url: Jira base URL
            auth_headers: Authentication headers
            
        Returns:
            Detected API version string
            
        Raises:
            APIVersionError: If no API version is working
        """
        return await self.get_working_api_version(base_url, auth_headers)
    
    def get_preferred_api_version(self, jira_version: str) -> str:
        """Get preferred API version based on Jira version.
        
        Args:
            jira_version: Jira version string
            
        Returns:
            Recommended API version for the given Jira version
        """
        try:
            # Parse version for comparison
            version_parts = self._parse_version(jira_version)
            
            # If we can't parse the version or it's unknown, use preferred
            if not version_parts or version_parts == [0]:
                return self.preferred_version
            
            if len(version_parts) >= 2:
                major, minor = version_parts[0], version_parts[1]
                
                # API v3 is available from Jira 7.0+
                if major >= 7:
                    return "3"
                # API v2 is available from Jira 4.0+
                elif major >= 4:
                    return "2"
            
            # Default to v2 for very old versions
            return "2"
            
        except Exception as e:
            app_logger.warning(f"Failed to parse Jira version {jira_version}: {e}")
            return self.preferred_version
    
    async def get_api_version_info(self, base_url: str, auth_headers: Dict[str, str]) -> APIVersionInfo:
        """Get comprehensive API version information.
        
        Args:
            base_url: Jira base URL
            auth_headers: Authentication headers
            
        Returns:
            APIVersionInfo with available versions and recommendations
        """
        available_versions = []
        working_version = None
        
        # Test all known versions
        for version in self.known_versions:
            if await self.test_api_version(base_url, auth_headers, version):
                available_versions.append(version)
                if working_version is None:
                    working_version = version
        
        # Determine fallback version
        fallback_version = None
        if len(available_versions) > 1:
            # Use the second available version as fallback
            fallback_version = available_versions[1]
        elif len(available_versions) == 1 and available_versions[0] != self.preferred_version:
            fallback_version = available_versions[0]
        
        return APIVersionInfo(
            available_versions=available_versions,
            preferred_version=self.preferred_version,
            working_version=working_version,
            fallback_version=fallback_version
        )
    
    def is_version_compatible(self, api_version: str, jira_version: str) -> bool:
        """Check if API version is compatible with Jira version.
        
        Args:
            api_version: API version to check
            jira_version: Jira version string
            
        Returns:
            True if compatible, False otherwise
        """
        if api_version not in self.version_compatibility:
            return False
        
        try:
            min_version = self.version_compatibility[api_version]["min_jira_version"]
            return self._is_version_greater_or_equal(jira_version, min_version)
        except Exception:
            return False
    
    def get_version_features(self, api_version: str) -> List[str]:
        """Get list of features available in specific API version.
        
        Args:
            api_version: API version string
            
        Returns:
            List of feature names
        """
        if api_version in self.version_compatibility:
            return self.version_compatibility[api_version]["features"]
        return []
    
    def _parse_version(self, version: str) -> List[int]:
        """Parse version string into list of integers.
        
        Args:
            version: Version string (e.g., "9.12.22")
            
        Returns:
            List of version parts as integers
        """
        if not version or version == "unknown":
            return [0]
        
        # Extract numeric parts from version string
        version_match = re.match(r'^(\d+)\.(\d+)\.(\d+)', version)
        if version_match:
            return [int(x) for x in version_match.groups()]
        
        # Fallback: try to extract any numbers
        numbers = re.findall(r'\d+', version)
        if numbers:
            return [int(x) for x in numbers[:3]]  # Take first 3 numbers
        
        return [0]
    
    def _is_version_greater_or_equal(self, version1: str, version2: str) -> bool:
        """Compare two version strings.
        
        Args:
            version1: First version string
            version2: Second version string
            
        Returns:
            True if version1 >= version2
        """
        v1_parts = self._parse_version(version1)
        v2_parts = self._parse_version(version2)
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        # Compare part by part
        for i in range(max_len):
            if v1_parts[i] > v2_parts[i]:
                return True
            elif v1_parts[i] < v2_parts[i]:
                return False
        
        return True  # Equal versions


def create_api_version_manager(preferred_version: str = "3", timeout: int = 30) -> APIVersionManager:
    """Factory function to create APIVersionManager instance.
    
    Args:
        preferred_version: Preferred API version to use
        timeout: HTTP request timeout in seconds
        
    Returns:
        APIVersionManager instance
    """
    return APIVersionManager(preferred_version=preferred_version, timeout=timeout)