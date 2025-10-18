"""Proxy configuration and handling for Jira Data Center integration."""

from typing import Optional, Dict, Any, List
from urllib.parse import urlparse, urlunparse
from dataclasses import dataclass

import httpx
from pydantic import BaseModel


@dataclass
class ProxyConfig:
    """Proxy configuration data class."""

    url: str
    username: Optional[str] = None
    password: Optional[str] = None
    no_proxy: Optional[List[str]] = None


class ProxyValidationResult(BaseModel):
    """Result of proxy configuration validation."""

    is_valid: bool
    proxy_config: Optional[Dict[str, str]] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    troubleshooting_steps: List[str] = []
    suggested_config: Optional[Dict[str, Any]] = None


class ProxyTestResult(BaseModel):
    """Result of proxy connectivity test."""

    success: bool
    proxy_used: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    troubleshooting_steps: List[str] = []


class ProxyHandler:
    """Handles proxy configuration and validation for HTTP requests."""

    def __init__(self, proxy_url: Optional[str] = None):
        """Initialize proxy handler.

        Args:
            proxy_url: Proxy URL in format: http://[username:password@]host:port
        # Get logger from service registry
        self.logger = require_service('logger', context='import')
        """
        self.proxy_url = proxy_url
        self.proxy_config = self._parse_proxy_url(proxy_url) if proxy_url else None

    def _parse_proxy_url(self, proxy_url: str) -> Optional[ProxyConfig]:
        """Parse proxy URL into components.

        Args:
            proxy_url: Proxy URL to parse

        Returns:
            ProxyConfig object or None if invalid
        """
        try:
            parsed = urlparse(proxy_url)

            if not parsed.hostname:
                self.logger.error(f"Invalid proxy URL - no hostname: {proxy_url}")
                return None

            if not parsed.port:
                self.logger.error(f"Invalid proxy URL - no port specified: {proxy_url}")
                return None

            # Extract authentication if present
            username = parsed.username
            password = parsed.password

            # Reconstruct URL without credentials for logging
            clean_url = urlunparse(
                (
                    parsed.scheme,
                    f"{parsed.hostname}:{parsed.port}",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )

            return ProxyConfig(url=clean_url, username=username, password=password)

        except Exception as e:
            self.logger.error(f"Failed to parse proxy URL {proxy_url}: {e}")
            return None

    def get_httpx_proxy_config(self) -> Optional[Dict[str, str]]:
        """Get proxy configuration for httpx client.

        Returns:
            Proxy configuration dictionary for httpx or None if no proxy
        """
        if not self.proxy_config:
            return None

        # Build proxy URL with authentication if provided
        if self.proxy_config.username and self.proxy_config.password:
            parsed = urlparse(self.proxy_config.url)
            proxy_url = urlunparse(
                (
                    parsed.scheme,
                    f"{self.proxy_config.username}:{self.proxy_config.password}@{parsed.netloc}",
                    parsed.path,
                    parsed.params,
                    parsed.query,
                    parsed.fragment,
                )
            )
        else:
            proxy_url = self.proxy_config.url

        # Return proxy configuration for both HTTP and HTTPS
        return {"http://": proxy_url, "https://": proxy_url}

    def validate_proxy_config(self) -> ProxyValidationResult:
        """Validate proxy configuration.

        Returns:
            Proxy validation result with detailed information
        """
        if not self.proxy_url:
            return ProxyValidationResult(
                is_valid=True, error_message="No proxy configured"
            )

        if not self.proxy_config:
            return ProxyValidationResult(
                is_valid=False,
                error_message="Invalid proxy URL format",
                error_type="invalid_proxy_url",
                troubleshooting_steps=[
                    "Check proxy URL format: http://[username:password@]host:port",
                    "Ensure hostname and port are specified",
                    "Verify proxy server address is correct",
                ],
            )

        # Validate proxy URL components
        try:
            parsed = urlparse(self.proxy_config.url)
        except Exception as e:
            return ProxyValidationResult(
                is_valid=False,
                error_message=f"Failed to parse proxy URL: {e}",
                error_type="invalid_proxy_url",
                troubleshooting_steps=[
                    "Check proxy URL format: http://[username:password@]host:port",
                    "Ensure hostname and port are specified",
                    "Verify proxy server address is correct",
                ],
            )

        if parsed.scheme not in ["http", "https"]:
            return ProxyValidationResult(
                is_valid=False,
                error_message="Proxy URL must use http:// or https:// scheme",
                error_type="invalid_proxy_scheme",
                troubleshooting_steps=[
                    "Use http:// for HTTP proxy",
                    "Use https:// for HTTPS proxy (less common)",
                    "Most corporate proxies use http://",
                ],
            )

        try:
            port = parsed.port
            if port is None or not (1 <= port <= 65535):
                return ProxyValidationResult(
                    is_valid=False,
                    error_message=f"Invalid proxy port: {port}",
                    error_type="invalid_proxy_port",
                    troubleshooting_steps=[
                        "Check proxy port number (common ports: 8080, 3128, 8888)",
                        "Verify port is accessible and not blocked by firewall",
                        "Contact network administrator for correct proxy settings",
                    ],
                )
        except ValueError as e:
            return ProxyValidationResult(
                is_valid=False,
                error_message=f"Invalid proxy port: {e}",
                error_type="invalid_proxy_port",
                troubleshooting_steps=[
                    "Check proxy port number (common ports: 8080, 3128, 8888)",
                    "Ensure port is a valid number between 1 and 65535",
                    "Contact network administrator for correct proxy settings",
                ],
            )

        # Check for authentication requirements
        if self.proxy_config.username and not self.proxy_config.password:
            return ProxyValidationResult(
                is_valid=False,
                error_message="Proxy username provided but password is missing",
                error_type="incomplete_proxy_auth",
                troubleshooting_steps=[
                    "Provide both username and password for proxy authentication",
                    "Use format: http://username:password@host:port",
                    "Contact network administrator for proxy credentials",
                ],
            )

        return ProxyValidationResult(
            is_valid=True, proxy_config=self.get_httpx_proxy_config()
        )

    async def test_proxy_connectivity(
        self, test_url: str = "https://httpbin.org/ip", timeout: int = 10
    ) -> ProxyTestResult:
        """Test proxy connectivity by making a test request.

        Args:
            test_url: URL to test connectivity with
            timeout: Request timeout in seconds

        Returns:
            Proxy test result with performance and error information
        """
        import time

        if not self.proxy_config:
            return ProxyTestResult(
                success=True,
                proxy_used=False,
                error_message="No proxy configured - direct connection",
            )

        try:
            proxy_config = self.get_httpx_proxy_config()
            start_time = time.time()

            # Build client configuration
            client_config = {"timeout": timeout}
            if proxy_config:
                client_config["proxies"] = proxy_config

            async with httpx.AsyncClient(**client_config) as client:
                response = await client.get(test_url)

                end_time = time.time()
                response_time = (
                    end_time - start_time
                ) * 1000  # Convert to milliseconds

                if response.status_code == 200:
                    return ProxyTestResult(
                        success=True, proxy_used=True, response_time_ms=response_time
                    )
                else:
                    return ProxyTestResult(
                        success=False,
                        proxy_used=True,
                        response_time_ms=response_time,
                        error_message=f"HTTP {response.status_code}: {response.text[:200]}",
                        error_type="proxy_http_error",
                        troubleshooting_steps=[
                            "Check if proxy server is running and accessible",
                            "Verify proxy authentication credentials",
                            "Check if target URL is allowed through proxy",
                        ],
                    )

        except httpx.ProxyError as e:
            return ProxyTestResult(
                success=False,
                proxy_used=True,
                error_message=f"Proxy connection error: {str(e)}",
                error_type="proxy_connection_error",
                troubleshooting_steps=[
                    "Verify proxy server address and port",
                    "Check proxy authentication credentials",
                    "Ensure proxy server is running and accessible",
                    "Check network connectivity to proxy server",
                ],
            )
        except httpx.TimeoutException:
            return ProxyTestResult(
                success=False,
                proxy_used=True,
                error_message=f"Proxy connection timeout after {timeout} seconds",
                error_type="proxy_timeout",
                troubleshooting_steps=[
                    "Check proxy server responsiveness",
                    "Increase timeout value for slow networks",
                    "Verify proxy server is not overloaded",
                    "Check network latency to proxy server",
                ],
            )
        except Exception as e:
            return ProxyTestResult(
                success=False,
                proxy_used=True,
                error_message=f"Unexpected proxy error: {str(e)}",
                error_type="proxy_unexpected_error",
                troubleshooting_steps=[
                    "Check proxy configuration",
                    "Verify network connectivity",
                    "Contact network administrator",
                ],
            )

    def get_proxy_troubleshooting_steps(self, error_type: str) -> List[str]:
        """Get troubleshooting steps for specific proxy error types.

        Args:
            error_type: Type of proxy error

        Returns:
            List of troubleshooting steps
        """
        troubleshooting_steps = {
            "invalid_proxy_url": [
                "Check proxy URL format: http://[username:password@]host:port",
                "Ensure hostname and port are specified",
                "Verify proxy server address is correct",
                "Common proxy ports: 8080, 3128, 8888",
            ],
            "invalid_proxy_scheme": [
                "Use http:// for HTTP proxy (most common)",
                "Use https:// for HTTPS proxy (less common)",
                "Most corporate proxies use HTTP protocol",
                "Contact network administrator for correct scheme",
            ],
            "invalid_proxy_port": [
                "Check proxy port number (common ports: 8080, 3128, 8888)",
                "Verify port is accessible and not blocked by firewall",
                "Ensure port number is between 1 and 65535",
                "Contact network administrator for correct proxy settings",
            ],
            "incomplete_proxy_auth": [
                "Provide both username and password for proxy authentication",
                "Use format: http://username:password@host:port",
                "Contact network administrator for proxy credentials",
                "Some proxies may not require authentication",
            ],
            "proxy_connection_error": [
                "Verify proxy server address and port are correct",
                "Check proxy authentication credentials",
                "Ensure proxy server is running and accessible",
                "Check network connectivity to proxy server",
                "Verify firewall allows connection to proxy",
            ],
            "proxy_timeout": [
                "Check proxy server responsiveness",
                "Increase timeout value for slow networks",
                "Verify proxy server is not overloaded",
                "Check network latency to proxy server",
                "Try different proxy server if available",
            ],
            "proxy_http_error": [
                "Check if proxy server is running and accessible",
                "Verify proxy authentication credentials are correct",
                "Check if target URL is allowed through proxy",
                "Review proxy server logs for more details",
                "Contact network administrator for proxy policies",
            ],
            "proxy_authentication_failed": [
                "Verify proxy username and password are correct",
                "Check if proxy account is active and not locked",
                "Ensure proxy authentication method is supported",
                "Contact network administrator for credential verification",
            ],
        }

        return troubleshooting_steps.get(
            error_type,
            [
                "Check proxy configuration",
                "Verify network connectivity to proxy",
                "Contact your network administrator for assistance",
            ],
        )

    def suggest_proxy_config_for_error(self, error_type: str) -> Dict[str, Any]:
        """Suggest proxy configuration changes for specific error types.

        Args:
            error_type: Type of proxy error

        Returns:
            Suggested configuration changes
        """
        suggestions = {}

        if error_type == "invalid_proxy_url":
            suggestions = {
                "proxy_url": "http://proxy.company.com:8080",
                "note": "Replace with your actual proxy server address and port",
            }
        elif error_type == "invalid_proxy_scheme":
            suggestions = {
                "proxy_url": "http://your-proxy-host:8080",
                "note": "Most corporate proxies use HTTP scheme",
            }
        elif error_type == "incomplete_proxy_auth":
            suggestions = {
                "proxy_url": "http://username:password@proxy.company.com:8080",
                "note": "Include both username and password for authenticated proxy",
            }
        elif error_type == "proxy_timeout":
            suggestions = {
                "timeout": 60,
                "note": "Increase timeout for slow proxy connections",
            }
        elif error_type == "proxy_connection_error":
            suggestions = {
                "proxy_url": None,
                "note": "Temporarily disable proxy to test direct connection",
            }

        return suggestions

    @staticmethod
    def detect_system_proxy() -> Optional[str]:
        """Detect system proxy settings from environment variables.

        Returns:
            Proxy URL if detected, None otherwise
        """
        import os
        import logging

        logger = logging.getLogger(__name__)

        # Check common proxy environment variables
        proxy_vars = ["HTTP_PROXY", "http_proxy", "HTTPS_PROXY", "https_proxy"]

        for var in proxy_vars:
            proxy_url = os.environ.get(var)
            if proxy_url:
                logger.info(f"Detected system proxy from {var}: {proxy_url}")
                return proxy_url

        return None

    @staticmethod
    def is_url_in_no_proxy(url: str, no_proxy_list: List[str]) -> bool:
        """Check if URL should bypass proxy based on no_proxy list.

        Args:
            url: URL to check
            no_proxy_list: List of hosts/patterns that should bypass proxy

        Returns:
            True if URL should bypass proxy, False otherwise
        """
        if not no_proxy_list:
            return False

        try:
            parsed = urlparse(url)
            hostname = parsed.hostname

            if not hostname:
                return False

            for no_proxy_pattern in no_proxy_list:
                no_proxy_pattern = no_proxy_pattern.strip()

                # Exact match
                if hostname == no_proxy_pattern:
                    return True

                # Wildcard match (*.example.com)
                if no_proxy_pattern.startswith("*."):
                    domain = no_proxy_pattern[2:]
                    if hostname.endswith(domain):
                        return True

                # Suffix match (.example.com)
                if no_proxy_pattern.startswith("."):
                    if hostname.endswith(no_proxy_pattern):
                        return True

                # IP range or CIDR (basic check)
                if "/" in no_proxy_pattern or "-" in no_proxy_pattern:
                    # This would require more complex IP matching logic
                    # For now, just do exact match
                    if hostname == no_proxy_pattern:
                        return True

            return False

        except Exception as e:
            import logging

            logger = logging.getLogger(__name__)
            logger.error(f"Error checking no_proxy for {url}: {e}")
            return False

    def should_use_proxy_for_url(self, url: str) -> bool:
        """Determine if proxy should be used for a specific URL.

        Args:
            url: URL to check

        Returns:
            True if proxy should be used, False otherwise
        """
        if not self.proxy_config:
            return False

        # Check no_proxy list if configured
        if self.proxy_config.no_proxy:
            if self.is_url_in_no_proxy(url, self.proxy_config.no_proxy):
                return False

        return True

    def get_proxy_info(self) -> Dict[str, Any]:
        """Get proxy configuration information for debugging.

        Returns:
            Dictionary with proxy information (credentials redacted)
        """
        if not self.proxy_config:
            return {"proxy_enabled": False}

        parsed = urlparse(self.proxy_config.url)

        return {
            "proxy_enabled": True,
            "proxy_host": parsed.hostname,
            "proxy_port": parsed.port,
            "proxy_scheme": parsed.scheme,
            "authentication_enabled": bool(self.proxy_config.username),
            "username": (
                self.proxy_config.username if self.proxy_config.username else None
            ),
            "password_configured": bool(self.proxy_config.password),
        }
