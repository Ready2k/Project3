"""
Comprehensive error handling and troubleshooting for Jira Data Center integration.

This module provides specialized error detection, categorization, and troubleshooting
guidance for various Jira Data Center deployment scenarios.
"""

from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel
import re
import httpx

from app.config import JiraDeploymentType


class JiraErrorType(str, Enum):
    """Categories of Jira integration errors."""

    # Connection errors
    CONNECTION_TIMEOUT = "connection_timeout"
    CONNECTION_REFUSED = "connection_refused"
    DNS_RESOLUTION = "dns_resolution"
    NETWORK_UNREACHABLE = "network_unreachable"

    # SSL/TLS errors
    SSL_CERTIFICATE_ERROR = "ssl_certificate_error"
    SSL_HANDSHAKE_FAILED = "ssl_handshake_failed"
    SSL_VERIFICATION_FAILED = "ssl_verification_failed"

    # Authentication errors
    AUTH_INVALID_CREDENTIALS = "auth_invalid_credentials"
    AUTH_TOKEN_EXPIRED = "auth_token_expired"
    AUTH_INSUFFICIENT_PERMISSIONS = "auth_insufficient_permissions"
    AUTH_SSO_FAILED = "auth_sso_failed"
    AUTH_METHOD_NOT_SUPPORTED = "auth_method_not_supported"

    # API errors
    API_VERSION_NOT_SUPPORTED = "api_version_not_supported"
    API_ENDPOINT_NOT_FOUND = "api_endpoint_not_found"
    API_RATE_LIMITED = "api_rate_limited"
    API_SERVER_ERROR = "api_server_error"

    # Configuration errors
    CONFIG_INVALID_URL = "config_invalid_url"
    CONFIG_MISSING_REQUIRED_FIELD = "config_missing_required_field"
    CONFIG_INVALID_DEPLOYMENT_TYPE = "config_invalid_deployment_type"

    # Data Center specific errors
    DC_VERSION_INCOMPATIBLE = "dc_version_incompatible"
    DC_CONTEXT_PATH_INVALID = "dc_context_path_invalid"
    DC_CUSTOM_PORT_BLOCKED = "dc_custom_port_blocked"
    DC_PROXY_CONFIGURATION = "dc_proxy_configuration"

    # Ticket/Data errors
    TICKET_NOT_FOUND = "ticket_not_found"
    TICKET_ACCESS_DENIED = "ticket_access_denied"
    TICKET_PARSING_ERROR = "ticket_parsing_error"

    # Generic errors
    UNKNOWN_ERROR = "unknown_error"


class JiraErrorDetail(BaseModel):
    """Detailed error information with troubleshooting guidance."""

    error_type: JiraErrorType
    error_code: Optional[str] = None
    message: str
    technical_details: Optional[str] = None
    troubleshooting_steps: List[str] = []
    documentation_links: List[str] = []
    suggested_config_changes: Optional[Dict[str, Any]] = None
    deployment_specific_guidance: Optional[str] = None

    class Config:
        use_enum_values = True


class JiraErrorHandler:
    """Handles Jira error detection, categorization, and troubleshooting guidance."""

    def __init__(self, deployment_type: Optional[JiraDeploymentType] = None):
        self.deployment_type = deployment_type
        self._init_error_patterns()
        self._init_troubleshooting_guides()

    def _init_error_patterns(self):
        """Initialize error detection patterns."""
        self.error_patterns = {
            # Connection patterns
            JiraErrorType.CONNECTION_TIMEOUT: [
                r"timeout|timed out|connection timeout",
                r"read timeout|connect timeout",
                r"TimeoutException|ConnectTimeout",
            ],
            JiraErrorType.CONNECTION_REFUSED: [
                r"connection refused|connection denied",
                r"ConnectError|ConnectionRefusedError",
                r"No connection could be made",
            ],
            JiraErrorType.DNS_RESOLUTION: [
                r"name resolution failed|dns resolution",
                r"getaddrinfo failed|Name or service not known",
                r"nodename nor servname provided",
            ],
            JiraErrorType.NETWORK_UNREACHABLE: [
                r"network is unreachable|no route to host",
                r"NetworkError|NetworkUnreachable",
            ],
            # SSL patterns
            JiraErrorType.SSL_CERTIFICATE_ERROR: [
                r"certificate verify failed|ssl certificate",
                r"CERTIFICATE_VERIFY_FAILED|SSL_CERTIFICATE_ERROR",
                r"certificate has expired|certificate is not valid",
            ],
            JiraErrorType.SSL_HANDSHAKE_FAILED: [
                r"ssl handshake failed|handshake failure",
                r"SSL_HANDSHAKE_FAILURE|SSLError",
            ],
            JiraErrorType.SSL_VERIFICATION_FAILED: [
                r"hostname.*doesn't match|certificate verification failed",
                r"SSL: CERTIFICATE_VERIFY_FAILED",
            ],
            # Authentication patterns
            JiraErrorType.AUTH_INVALID_CREDENTIALS: [
                r"401|unauthorized|invalid credentials",
                r"authentication failed|login failed",
                r"invalid username or password",
            ],
            JiraErrorType.AUTH_TOKEN_EXPIRED: [
                r"token expired|token invalid|token has expired",
                r"JWT.*expired|access token.*expired",
            ],
            JiraErrorType.AUTH_INSUFFICIENT_PERMISSIONS: [
                r"403|forbidden|insufficient permissions",
                r"access denied|permission denied",
                r"not authorized to access",
            ],
            JiraErrorType.AUTH_SSO_FAILED: [
                r"sso.*failed|single sign.on.*failed",
                r"saml.*error|oauth.*error",
            ],
            # API patterns
            JiraErrorType.API_VERSION_NOT_SUPPORTED: [
                r"api version.*not supported|unsupported api version",
                r"endpoint.*not found.*api.*version",
            ],
            JiraErrorType.API_ENDPOINT_NOT_FOUND: [
                r"404|not found|endpoint.*not found",
                r"resource not found|path not found",
            ],
            JiraErrorType.API_RATE_LIMITED: [
                r"429|rate limit|too many requests",
                r"quota exceeded|throttled",
            ],
            JiraErrorType.API_SERVER_ERROR: [
                r"500|502|503|504|internal server error",
                r"bad gateway|service unavailable|gateway timeout",
            ],
            # Configuration patterns
            JiraErrorType.CONFIG_INVALID_URL: [
                r"invalid url|malformed url|url.*invalid",
                r"invalid scheme|invalid hostname",
            ],
            # Data Center specific patterns
            JiraErrorType.DC_VERSION_INCOMPATIBLE: [
                r"version.*not supported|incompatible version",
                r"requires.*version|minimum version",
            ],
            JiraErrorType.DC_CONTEXT_PATH_INVALID: [
                r"context path.*invalid|path.*not found",
                r"application.*not found",
            ],
            # Ticket patterns
            JiraErrorType.TICKET_NOT_FOUND: [
                r"issue.*not found|ticket.*not found",
                r"issue.*does not exist|key.*not found",
            ],
            JiraErrorType.TICKET_ACCESS_DENIED: [
                r"issue.*access denied|ticket.*access denied",
                r"permission.*view.*issue",
            ],
        }

    def _init_troubleshooting_guides(self):
        """Initialize troubleshooting guidance for each error type."""
        self.troubleshooting_guides = {
            JiraErrorType.CONNECTION_TIMEOUT: {
                "steps": [
                    "Check if the Jira server is running and accessible",
                    "Verify the base URL is correct and includes the proper port",
                    "Test network connectivity: ping the Jira server hostname",
                    "Check if corporate firewall is blocking the connection",
                    "Try increasing the timeout value in configuration",
                    "For Data Center: Verify the application is deployed and started",
                ],
                "data_center_specific": [
                    "Check Tomcat server status on the Data Center instance",
                    "Verify the application context is properly deployed",
                    "Check Data Center cluster node health if using clustering",
                ],
                "config_suggestions": {
                    "timeout": 60,
                    "verify_ssl": False,  # For testing only
                },
            },
            JiraErrorType.CONNECTION_REFUSED: {
                "steps": [
                    "Verify the Jira server is running on the specified port",
                    "Check if the port is correct (default: 8080 for Data Center)",
                    "Ensure no firewall is blocking the port",
                    "Verify the hostname/IP address is correct",
                    "For Data Center: Check if Tomcat is listening on the configured port",
                ],
                "data_center_specific": [
                    "Check server.xml configuration for correct port settings",
                    "Verify Tomcat connector configuration",
                    "Check if Data Center is bound to localhost only vs all interfaces",
                ],
            },
            JiraErrorType.SSL_CERTIFICATE_ERROR: {
                "steps": [
                    "For self-signed certificates: Set verify_ssl to False (testing only)",
                    "Add the certificate to your system's trusted certificate store",
                    "Provide a custom CA certificate bundle path",
                    "Contact your system administrator for the proper certificate",
                    "Verify the certificate is not expired",
                ],
                "data_center_specific": [
                    "Data Center often uses self-signed or internal CA certificates",
                    "Check with your IT team for the internal CA certificate bundle",
                    "Consider using HTTP instead of HTTPS for internal networks (if policy allows)",
                ],
                "config_suggestions": {
                    "verify_ssl": False,
                    "ca_cert_path": "/path/to/internal-ca-bundle.pem",
                },
            },
            JiraErrorType.AUTH_INVALID_CREDENTIALS: {
                "steps": [
                    "Verify username and password/token are correct",
                    "Check if the account is locked or disabled",
                    "For API tokens: Ensure the token is not expired",
                    "For PAT: Verify Personal Access Token is valid and has required permissions",
                    "Try logging in through the web interface to verify credentials",
                ],
                "data_center_specific": [
                    "Data Center supports both API tokens and Personal Access Tokens (PAT)",
                    "PAT is recommended for Data Center 8.14+ for better security",
                    "Check if SSO is configured and interfering with direct authentication",
                    "Verify the user has 'Browse Projects' permission at minimum",
                ],
            },
            JiraErrorType.AUTH_SSO_FAILED: {
                "steps": [
                    "Try the basic authentication fallback option",
                    "Clear browser cookies and try again",
                    "Contact your IT administrator about SSO configuration",
                    "Verify you're logged into the corporate network/VPN",
                ],
                "data_center_specific": [
                    "Data Center SSO integration may require specific configuration",
                    "Check if SAML/OAuth is properly configured on the Data Center instance",
                    "Verify SSO provider is accessible from the AAA system",
                ],
            },
            JiraErrorType.API_VERSION_NOT_SUPPORTED: {
                "steps": [
                    "The system will automatically try API v2 if v3 fails",
                    "Verify your Jira version supports the required API version",
                    "Check Jira documentation for API version compatibility",
                ],
                "data_center_specific": [
                    "Data Center 9.12.22 supports both REST API v2 and v3",
                    "Some endpoints may only be available in specific API versions",
                    "The system automatically detects and uses the best available version",
                ],
            },
            JiraErrorType.DC_VERSION_INCOMPATIBLE: {
                "steps": [
                    "Verify your Jira Data Center version is 8.0 or higher",
                    "Check the Jira version in Administration > System Info",
                    "Consider upgrading Jira Data Center if version is too old",
                    "Contact your Jira administrator about version compatibility",
                ],
                "data_center_specific": [
                    "This integration is tested with Data Center 9.12.22",
                    "Minimum supported version is Data Center 8.0",
                    "Some features may not work with older versions",
                ],
            },
            JiraErrorType.DC_CONTEXT_PATH_INVALID: {
                "steps": [
                    "Check if Jira is deployed at the root path or a custom context",
                    "Common context paths: /jira, /atlassian-jira, or custom paths",
                    "Verify the full URL including context path",
                    "Check with your Jira administrator for the correct URL",
                ],
                "data_center_specific": [
                    "Data Center deployments often use custom context paths",
                    "Check server.xml for the configured context path",
                    "The context path should be included in the base URL",
                ],
            },
            JiraErrorType.DC_PROXY_CONFIGURATION: {
                "steps": [
                    "Configure proxy settings if your network requires it",
                    "Verify proxy hostname, port, and authentication",
                    "Check if the proxy supports HTTPS connections",
                    "Test proxy connectivity independently",
                ],
                "data_center_specific": [
                    "Corporate networks often require proxy for Data Center access",
                    "Verify proxy configuration allows connections to internal servers",
                    "Check if proxy authentication is required",
                ],
            },
            JiraErrorType.TICKET_NOT_FOUND: {
                "steps": [
                    "Verify the ticket key is correct (e.g., PROJ-123)",
                    "Check if the ticket exists in the Jira instance",
                    "Ensure you have permission to view the ticket",
                    "Verify the project key is correct",
                ],
                "data_center_specific": [
                    "Data Center may have different project configurations",
                    "Check project permissions and user access rights",
                    "Verify the ticket is in a project you have access to",
                ],
            },
        }

    def detect_error_type(
        self,
        error_message: str,
        status_code: Optional[int] = None,
        exception: Optional[Exception] = None,
    ) -> JiraErrorType:
        """
        Detect the error type based on error message, status code, and exception.

        Args:
            error_message: The error message to analyze
            status_code: HTTP status code if available
            exception: The original exception if available

        Returns:
            The detected error type
        """
        error_message_lower = error_message.lower()

        # Check status code first for quick identification
        if status_code:
            if status_code == 401:
                return JiraErrorType.AUTH_INVALID_CREDENTIALS
            elif status_code == 403:
                return JiraErrorType.AUTH_INSUFFICIENT_PERMISSIONS
            elif status_code == 404:
                return JiraErrorType.API_ENDPOINT_NOT_FOUND
            elif status_code == 429:
                return JiraErrorType.API_RATE_LIMITED
            elif status_code >= 500:
                return JiraErrorType.API_SERVER_ERROR

        # Check exception type
        if exception:
            if isinstance(exception, httpx.TimeoutException):
                return JiraErrorType.CONNECTION_TIMEOUT
            elif isinstance(exception, httpx.ConnectError):
                return JiraErrorType.CONNECTION_REFUSED
            elif isinstance(exception, httpx.NetworkError):
                return JiraErrorType.NETWORK_UNREACHABLE

        # Pattern matching on error message
        for error_type, patterns in self.error_patterns.items():
            for pattern in patterns:
                if re.search(pattern, error_message_lower, re.IGNORECASE):
                    return error_type

        return JiraErrorType.UNKNOWN_ERROR

    def create_error_detail(
        self,
        error_message: str,
        status_code: Optional[int] = None,
        exception: Optional[Exception] = None,
        technical_details: Optional[str] = None,
    ) -> JiraErrorDetail:
        """
        Create a detailed error object with troubleshooting guidance.

        Args:
            error_message: The main error message
            status_code: HTTP status code if available
            exception: The original exception if available
            technical_details: Additional technical information

        Returns:
            Detailed error information with troubleshooting steps
        """
        error_type = self.detect_error_type(error_message, status_code, exception)

        # Get troubleshooting guidance
        guidance = self.troubleshooting_guides.get(error_type, {})
        troubleshooting_steps = guidance.get("steps", [])

        # Add deployment-specific guidance
        deployment_specific_guidance = None
        if self.deployment_type == JiraDeploymentType.DATA_CENTER:
            dc_steps = guidance.get("data_center_specific", [])
            if dc_steps:
                troubleshooting_steps.extend(dc_steps)
                deployment_specific_guidance = "Data Center specific guidance included"

        # Get suggested configuration changes
        suggested_config = guidance.get("config_suggestions")

        # Add documentation links
        doc_links = self._get_documentation_links(error_type)

        return JiraErrorDetail(
            error_type=error_type,
            error_code=str(status_code) if status_code else None,
            message=error_message,
            technical_details=technical_details,
            troubleshooting_steps=troubleshooting_steps,
            documentation_links=doc_links,
            suggested_config_changes=suggested_config,
            deployment_specific_guidance=deployment_specific_guidance,
        )

    def _get_documentation_links(self, error_type: JiraErrorType) -> List[str]:
        """Get relevant documentation links for the error type."""
        base_docs = [
            "https://confluence.atlassian.com/adminjiraserver/",
            "https://developer.atlassian.com/server/jira/platform/rest-apis/",
        ]

        specific_links = {
            JiraErrorType.SSL_CERTIFICATE_ERROR: [
                "https://confluence.atlassian.com/kb/unable-to-connect-to-ssl-services-due-to-pkix-path-building-failed-779355358.html"
            ],
            JiraErrorType.AUTH_INVALID_CREDENTIALS: [
                "https://confluence.atlassian.com/jirasoftwareserver/personal-access-tokens-1018784848.html"
            ],
            JiraErrorType.DC_VERSION_INCOMPATIBLE: [
                "https://confluence.atlassian.com/adminjiraserver/supported-platforms-938846830.html"
            ],
        }

        return base_docs + specific_links.get(error_type, [])

    def get_error_category_summary(self) -> Dict[str, List[JiraErrorType]]:
        """Get a summary of error types grouped by category."""
        categories = {
            "Connection Issues": [
                JiraErrorType.CONNECTION_TIMEOUT,
                JiraErrorType.CONNECTION_REFUSED,
                JiraErrorType.DNS_RESOLUTION,
                JiraErrorType.NETWORK_UNREACHABLE,
            ],
            "SSL/Security Issues": [
                JiraErrorType.SSL_CERTIFICATE_ERROR,
                JiraErrorType.SSL_HANDSHAKE_FAILED,
                JiraErrorType.SSL_VERIFICATION_FAILED,
            ],
            "Authentication Issues": [
                JiraErrorType.AUTH_INVALID_CREDENTIALS,
                JiraErrorType.AUTH_TOKEN_EXPIRED,
                JiraErrorType.AUTH_INSUFFICIENT_PERMISSIONS,
                JiraErrorType.AUTH_SSO_FAILED,
                JiraErrorType.AUTH_METHOD_NOT_SUPPORTED,
            ],
            "API Issues": [
                JiraErrorType.API_VERSION_NOT_SUPPORTED,
                JiraErrorType.API_ENDPOINT_NOT_FOUND,
                JiraErrorType.API_RATE_LIMITED,
                JiraErrorType.API_SERVER_ERROR,
            ],
            "Configuration Issues": [
                JiraErrorType.CONFIG_INVALID_URL,
                JiraErrorType.CONFIG_MISSING_REQUIRED_FIELD,
                JiraErrorType.CONFIG_INVALID_DEPLOYMENT_TYPE,
            ],
            "Data Center Specific": [
                JiraErrorType.DC_VERSION_INCOMPATIBLE,
                JiraErrorType.DC_CONTEXT_PATH_INVALID,
                JiraErrorType.DC_CUSTOM_PORT_BLOCKED,
                JiraErrorType.DC_PROXY_CONFIGURATION,
            ],
            "Data Issues": [
                JiraErrorType.TICKET_NOT_FOUND,
                JiraErrorType.TICKET_ACCESS_DENIED,
                JiraErrorType.TICKET_PARSING_ERROR,
            ],
        }

        return categories


def create_jira_error_handler(
    deployment_type: Optional[JiraDeploymentType] = None,
) -> JiraErrorHandler:
    """Factory function to create a JiraErrorHandler instance."""
    return JiraErrorHandler(deployment_type)
