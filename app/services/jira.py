"""Jira integration service for fetching tickets and mapping to requirements."""

import base64
import html
import json
from typing import Dict, Any, Optional, Tuple

import httpx
from pydantic import BaseModel

from app.config import JiraConfig, JiraAuthType, JiraDeploymentType
from app.services.jira_auth import AuthenticationManager, AuthResult
from app.services.jira_auth_handlers import (
    APITokenHandler,
    PATHandler,
    SSOAuthHandler,
    BasicAuthHandler,
)
from app.services.deployment_detector import DeploymentDetector, DeploymentInfo
from app.services.api_version_manager import APIVersionManager
from app.services.ssl_handler import SSLHandler, SSLValidationResult
from app.services.proxy_handler import ProxyHandler, ProxyValidationResult
from app.services.retry_handler import RetryHandler, RetryConfig, RetryStrategy
from app.services.jira_error_handler import JiraErrorDetail, create_jira_error_handler
from app.utils.imports import require_service
from app.utils.error_boundaries import error_boundary


class JiraTicket(BaseModel):
    """Enhanced Jira ticket data model with comprehensive requirements fields."""

    # Core fields
    key: str
    summary: str
    description: Optional[str] = None
    priority: Optional[str] = None
    status: str
    issue_type: str
    assignee: Optional[str] = None
    reporter: Optional[str] = None
    labels: list[str] = []
    components: list[str] = []
    created: Optional[str] = None
    updated: Optional[str] = None

    # Requirements-specific fields
    acceptance_criteria: Optional[str] = None
    comments: list[dict] = []  # List of comment objects with author, body, created
    attachments: list[dict] = []  # List of attachment info
    custom_fields: dict = {}  # All custom fields for flexibility

    # Additional context fields
    project_key: Optional[str] = None
    project_name: Optional[str] = None
    epic_link: Optional[str] = None
    epic_name: Optional[str] = None
    story_points: Optional[float] = None
    sprint: Optional[str] = None
    fix_versions: list[str] = []
    affects_versions: list[str] = []

    # Relationships
    parent: Optional[str] = None  # Parent issue key
    subtasks: list[str] = []  # List of subtask keys
    linked_issues: list[dict] = []  # List of linked issues with relationship type

    # Workflow and resolution
    resolution: Optional[str] = None
    resolution_date: Optional[str] = None
    due_date: Optional[str] = None

    # Environment and testing
    environment: Optional[str] = None
    test_cases: Optional[str] = None

    # Business context
    business_value: Optional[str] = None
    user_story: Optional[str] = None


class JiraError(Exception):
    """Base exception for Jira-related errors."""

    pass


class JiraConnectionError(JiraError):
    """Jira connection/authentication error."""

    pass


class JiraTicketNotFoundError(JiraError):
    """Jira ticket not found error."""

    pass


class ConnectionResult(BaseModel):
    """Result of a connection test with detailed information."""

    success: bool
    deployment_info: Optional[DeploymentInfo] = None
    auth_result: Optional[AuthResult] = None
    ssl_validation_result: Optional[SSLValidationResult] = None
    proxy_validation_result: Optional[ProxyValidationResult] = None
    error_details: Optional[Dict[str, Any]] = None
    error_detail: Optional[JiraErrorDetail] = None  # New comprehensive error detail
    troubleshooting_steps: list[str] = []
    api_version: Optional[str] = None
    ssl_configuration: Optional[Dict[str, Any]] = None  # SSL configuration information


class JiraService:
    """Service for interacting with Jira API with Data Center support."""

    def __init__(self, config: JiraConfig):
        """Initialize Jira service with enhanced authentication and deployment detection.

        Args:
            config: Jira configuration with Data Center support
        """
        self.config = config
        self.base_url = config.base_url
        self.timeout = config.timeout

        # Get logger from service registry
        self.logger = require_service("logger", context="JiraService")

        # Initialize SSL handler
        self.ssl_handler = SSLHandler(
            verify_ssl=config.verify_ssl, ca_cert_path=config.ca_cert_path
        )

        # Log SSL configuration for debugging and security awareness
        ssl_config_info = self.ssl_handler.get_ssl_configuration_info()
        self.logger.info(
            f"SSL Configuration - Security Level: {ssl_config_info['security_level']}"
        )

        # Log any SSL warnings
        ssl_warnings = ssl_config_info.get("warnings", [])
        for warning in ssl_warnings:
            self.logger.warning(warning)

        # Initialize proxy handler
        self.proxy_handler = ProxyHandler(proxy_url=config.proxy_url)

        # Initialize retry handler
        retry_config = RetryConfig(
            max_attempts=config.max_retries
            + 1,  # +1 because max_retries is additional attempts
            initial_delay=config.retry_delay,
            max_delay=config.max_retry_delay,
            backoff_multiplier=config.retry_backoff_multiplier,
            strategy=RetryStrategy.EXPONENTIAL_BACKOFF,
            timeout_per_attempt=config.timeout,
            total_timeout=config.total_timeout,
        )
        self.retry_handler = RetryHandler(retry_config)

        # Initialize authentication management
        self.auth_manager = AuthenticationManager(config)
        self._register_auth_handlers()

        # Initialize deployment detection and API version management
        self.deployment_detector = DeploymentDetector(
            timeout=self.timeout,
            verify_ssl=config.verify_ssl,
            ca_cert_path=config.ca_cert_path,
            proxy_url=config.proxy_url,
        )
        self.api_version_manager = APIVersionManager(
            timeout=self.timeout,
            verify_ssl=config.verify_ssl,
            ca_cert_path=config.ca_cert_path,
            proxy_url=config.proxy_url,
        )

        # Cache for session management and detected information
        self.session_cache = {}

        # Initialize error handler
        self.error_handler = create_jira_error_handler(config.deployment_type)
        self.deployment_info: Optional[DeploymentInfo] = None
        self.api_version: Optional[str] = None

        # Legacy support - maintain auth_header for backward compatibility
        self.auth_header = None
        if config.email and config.api_token:
            auth_string = f"{config.email}:{config.api_token}"
            auth_bytes = auth_string.encode("ascii")
            auth_b64 = base64.b64encode(auth_bytes).decode("ascii")
            self.auth_header = f"Basic {auth_b64}"

    def _register_auth_handlers(self) -> None:
        """Register all authentication handlers with the authentication manager."""
        self.auth_manager.register_handler(APITokenHandler())
        self.auth_manager.register_handler(PATHandler())
        self.auth_manager.register_handler(SSOAuthHandler())
        self.auth_manager.register_handler(BasicAuthHandler())

    async def auto_configure(self) -> JiraConfig:
        """Auto-detect deployment type and configure appropriately.

        Returns:
            Updated JiraConfig with detected deployment information

        Raises:
            JiraConnectionError: If auto-configuration fails
        """
        try:
            if not self.config.base_url:
                raise JiraConnectionError("Base URL is required for auto-configuration")

            self.logger.info(
                f"Auto-configuring Jira integration for: {self.config.base_url}"
            )

            # Detect deployment type and version
            self.deployment_info = await self.deployment_detector.detect_deployment(
                self.config.base_url
            )

            # Update config with detected information
            self.config.deployment_type = self.deployment_info.deployment_type
            if self.deployment_info.context_path:
                self.config.context_path = self.deployment_info.context_path

            # Set appropriate authentication type if not specified
            if (
                not hasattr(self.config, "auth_type")
                or self.config.auth_type == JiraAuthType.API_TOKEN
            ):
                if self.deployment_info.deployment_type == JiraDeploymentType.CLOUD:
                    self.config.auth_type = JiraAuthType.API_TOKEN
                elif self.deployment_info.supports_pat:
                    self.config.auth_type = JiraAuthType.PERSONAL_ACCESS_TOKEN
                else:
                    self.config.auth_type = JiraAuthType.BASIC

            self.logger.info(
                f"Auto-configured for {self.deployment_info.deployment_type.value} "
                f"deployment with {self.config.auth_type.value} authentication"
            )

            return self.config

        except Exception as e:
            self.logger.error(f"Auto-configuration failed: {e}")
            self.logger.warning(
                f"Auto-configuration failed, using provided config: {str(e)}"
            )
            # Don't fail completely - use the provided configuration as fallback
            return self.config

    def _validate_config(self) -> None:
        """Validate Jira configuration with enhanced validation."""
        if not self.config.base_url:
            raise JiraConnectionError("Jira base URL is required")

        # Validate authentication configuration
        auth_errors = self.config.validate_auth_config()
        if auth_errors:
            raise JiraConnectionError(
                f"Authentication configuration errors: {'; '.join(auth_errors)}"
            )

    async def test_connection(self) -> tuple[bool, Optional[str]]:
        """Test Jira connection and authentication with fallback support.

        This method maintains backward compatibility while using the new enhanced system.

        Returns:
            Tuple of (success, error_message)
        """
        try:
            result = await self.test_connection_with_fallback()
            return result.success, (
                result.error_details.get("message") if result.error_details else None
            )
        except Exception as e:
            self.logger.error(f"Connection test failed: {e}")
            return False, str(e)

    async def test_connection_with_fallback(self) -> ConnectionResult:
        """Test connection with comprehensive error handling and fallback."""
        try:
            return await self._test_connection_internal()
        except Exception as e:
            self.logger.error(
                f"Jira connection test failed: {type(e).__name__}: {str(e)}"
            )
            return ConnectionResult(
                success=False,
                error_details={"message": f"Connection test failed: {str(e)}"},
                deployment_info=None,
                api_version_detected=None,
                auth_methods_available=[],
                ssl_configuration=None,
            )

    @error_boundary(
        "jira_connection_internal", timeout_seconds=30.0, max_retries=2, reraise=True
    )
    async def _test_connection_internal(self) -> ConnectionResult:
        """Test connection with comprehensive authentication fallback and deployment detection.

        Returns:
            ConnectionResult with detailed information about the connection attempt
        """
        ssl_validation_result = None
        proxy_validation_result = None

        try:
            self._validate_config()

            # Validate proxy configuration first
            if self.config.proxy_url:
                self.logger.info("Validating proxy configuration")
                proxy_validation_result = self.proxy_handler.validate_proxy_config()

                if not proxy_validation_result.is_valid:
                    self.logger.warning(
                        f"Proxy validation failed: {proxy_validation_result.error_message}"
                    )
                    error_detail = self.error_handler.create_error_detail(
                        error_message=proxy_validation_result.error_message,
                        technical_details=f"Proxy error type: {proxy_validation_result.error_type}",
                    )

                    return ConnectionResult(
                        success=False,
                        proxy_validation_result=proxy_validation_result,
                        error_details={
                            "message": proxy_validation_result.error_message
                        },
                        error_detail=error_detail,
                        troubleshooting_steps=proxy_validation_result.troubleshooting_steps,
                        ssl_configuration=self.ssl_handler.get_ssl_configuration_info(),
                    )

            # Validate SSL certificate if using HTTPS
            if self.base_url and self.base_url.startswith("https://"):
                self.logger.info("Validating SSL certificate configuration")
                ssl_validation_result = await self.ssl_handler.validate_ssl_certificate(
                    self.base_url
                )

                if not ssl_validation_result.is_valid:
                    self.logger.warning(
                        f"SSL validation failed: {ssl_validation_result.error_message}"
                    )
                    # Continue with connection attempt - SSL issues might be handled by configuration

            # Auto-configure if deployment info is not available
            if not self.deployment_info:
                try:
                    await self.auto_configure()
                except Exception as e:
                    self.logger.warning(
                        f"Auto-configuration failed, continuing with manual config: {e}"
                    )

            # Attempt authentication with fallback chain
            auth_result = await self.auth_manager.authenticate()

            if not auth_result.success:
                # Create comprehensive error detail for authentication failure
                error_detail = self.error_handler.create_error_detail(
                    error_message=auth_result.error_message or "Authentication failed",
                    technical_details=f"Authentication type: {auth_result.auth_type.value if auth_result.auth_type else 'unknown'}",
                )

                return ConnectionResult(
                    success=False,
                    deployment_info=self.deployment_info,
                    auth_result=auth_result,
                    ssl_validation_result=ssl_validation_result,
                    proxy_validation_result=proxy_validation_result,
                    error_details={
                        "message": auth_result.error_message or "Authentication failed"
                    },
                    error_detail=error_detail,
                    troubleshooting_steps=error_detail.troubleshooting_steps,
                    ssl_configuration=self.ssl_handler.get_ssl_configuration_info(),
                )

            # Test the connection with authenticated headers
            auth_headers = await self.auth_manager.get_auth_headers()

            # Detect and set API version
            try:
                self.api_version = (
                    await self.api_version_manager.get_working_api_version(
                        self.base_url, auth_headers
                    )
                )
            except Exception as e:
                self.logger.warning(f"API version detection failed, using default: {e}")
                self.api_version = "3"  # Default to v3

            # Test the connection
            success, user_info, error_message = (
                await self._test_authenticated_connection(auth_headers)
            )

            if success:
                self.logger.info(
                    f"Jira connection successful for user: {user_info.get('displayName', 'Unknown')} "
                    f"using {auth_result.auth_type.value} authentication"
                )

                return ConnectionResult(
                    success=True,
                    deployment_info=self.deployment_info,
                    auth_result=auth_result,
                    ssl_validation_result=ssl_validation_result,
                    proxy_validation_result=proxy_validation_result,
                    api_version=self.api_version,
                    ssl_configuration=self.ssl_handler.get_ssl_configuration_info(),
                )
            else:
                # Create comprehensive error detail for connection failure
                error_detail = self.error_handler.create_error_detail(
                    error_message=error_message,
                    technical_details=f"API version: {self.api_version}, Deployment: {self.deployment_info.deployment_type.value if self.deployment_info else 'unknown'}",
                )

                # Combine with SSL and proxy troubleshooting steps
                combined_steps = error_detail.troubleshooting_steps.copy()
                if ssl_validation_result and not ssl_validation_result.is_valid:
                    combined_steps.extend(ssl_validation_result.troubleshooting_steps)
                if proxy_validation_result and not proxy_validation_result.is_valid:
                    combined_steps.extend(proxy_validation_result.troubleshooting_steps)

                return ConnectionResult(
                    success=False,
                    deployment_info=self.deployment_info,
                    auth_result=auth_result,
                    ssl_validation_result=ssl_validation_result,
                    proxy_validation_result=proxy_validation_result,
                    error_details={"message": error_message},
                    error_detail=error_detail,
                    troubleshooting_steps=combined_steps,
                    api_version=self.api_version,
                    ssl_configuration=self.ssl_handler.get_ssl_configuration_info(),
                )

        except JiraConnectionError as e:
            error_detail = self.error_handler.create_error_detail(
                error_message=str(e),
                technical_details="JiraConnectionError raised during connection test",
            )

            return ConnectionResult(
                success=False,
                ssl_validation_result=ssl_validation_result,
                proxy_validation_result=proxy_validation_result,
                error_details={"message": str(e)},
                error_detail=error_detail,
                troubleshooting_steps=error_detail.troubleshooting_steps,
                ssl_configuration=self.ssl_handler.get_ssl_configuration_info(),
            )
        except Exception as e:
            self.logger.error(f"Unexpected error in connection test: {e}")
            error_detail = self.error_handler.create_error_detail(
                error_message=f"Unexpected error: {str(e)}",
                exception=e,
                technical_details=f"Exception type: {type(e).__name__}",
            )

            return ConnectionResult(
                success=False,
                ssl_validation_result=ssl_validation_result,
                proxy_validation_result=proxy_validation_result,
                error_details={"message": f"Unexpected error: {str(e)}"},
                error_detail=error_detail,
                troubleshooting_steps=error_detail.troubleshooting_steps,
                ssl_configuration=self.ssl_handler.get_ssl_configuration_info(),
            )

    async def _test_authenticated_connection(
        self, auth_headers: Dict[str, str]
    ) -> Tuple[bool, Dict[str, Any], Optional[str]]:
        """Test connection with authenticated headers using retry logic.

        Args:
            auth_headers: Authentication headers to use

        Returns:
            Tuple of (success, user_info, error_message)
        """

        async def _perform_connection_test() -> (
            Tuple[bool, Dict[str, Any], Optional[str]]
        ):
            """Inner function to perform the actual connection test."""
            # Get SSL verification and proxy configuration
            verify_config = self.ssl_handler.get_httpx_verify_config()
            proxy_config = self.proxy_handler.get_httpx_proxy_config()

            # Log SSL configuration for this connection attempt with security context
            if verify_config is False:
                self.logger.warning(
                    "🔓 Connection attempt with SSL verification DISABLED - Security risk!"
                )
                self.logger.warning("🔒 This bypasses ALL SSL certificate validation")
            elif isinstance(verify_config, str):
                self.logger.info(
                    f"🔐 Connection attempt with custom CA certificate: {verify_config}"
                )
            else:
                self.logger.info(
                    "🔐 Connection attempt with SSL verification enabled (system CA)"
                )

            # Create client with retry-friendly configuration - FORCE SSL settings
            client_config = {
                "verify": verify_config,
                "proxies": proxy_config,
                "timeout": self.timeout,
            }

            # Additional SSL bypass for problematic certificates
            if not self.config.verify_ssl:
                # Completely disable SSL verification at multiple levels
                import ssl

                ssl_context = ssl.create_default_context()
                ssl_context.check_hostname = False
                ssl_context.verify_mode = ssl.CERT_NONE
                client_config["verify"] = False
                self.logger.warning(
                    "🚨 SSL verification COMPLETELY DISABLED - bypassing all certificate checks"
                )

            client = self.retry_handler.create_http_client_with_retry(client_config)

            async with client:
                # Use detected API version or default
                api_version = self.api_version or "3"
                url = self.api_version_manager.build_endpoint(
                    self.base_url, "myself", api_version
                )

                headers = {"Accept": "application/json"}
                headers.update(auth_headers)

                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    try:
                        user_data = response.json()
                        return True, user_data, None
                    except (ValueError, json.JSONDecodeError) as e:
                        self.logger.error(
                            f"Failed to parse JSON response from connection test: {e}"
                        )
                        self.logger.debug(f"Response content: {response.text[:200]}...")
                        # Check if response looks like HTML (common when hitting wrong endpoint)
                        if response.text.strip().startswith("<"):
                            return (
                                False,
                                {},
                                "Server returned HTML instead of JSON. Check base URL and endpoint configuration.",
                            )
                        return False, {}, f"Invalid JSON response from server: {e}"
                elif response.status_code == 401:
                    return False, {}, "Authentication failed. Check credentials."
                elif response.status_code == 403:
                    return False, {}, "Access forbidden. Check permissions."
                elif response.status_code == 404:
                    # Try fallback API version
                    if api_version == "3":
                        fallback_url = self.api_version_manager.build_endpoint(
                            self.base_url, "myself", "2"
                        )
                        response = await client.get(fallback_url, headers=headers)
                        if response.status_code == 200:
                            self.api_version = "2"  # Update to working version
                            try:
                                user_data = response.json()
                                return True, user_data, None
                            except (ValueError, json.JSONDecodeError) as e:
                                self.logger.error(
                                    f"Failed to parse JSON response from fallback connection test: {e}"
                                )
                                return (
                                    False,
                                    {},
                                    f"Invalid JSON response from fallback API: {e}",
                                )
                    return (
                        False,
                        {},
                        f"API endpoint not found. Server may not support API version {api_version}.",
                    )
                elif response.status_code in [429, 502, 503, 504]:
                    # These status codes should trigger retry
                    response.raise_for_status()
                else:
                    return False, {}, f"HTTP {response.status_code}: {response.text}"

        # Execute with retry logic
        retry_result = await self.retry_handler.execute_with_retry(
            _perform_connection_test, "Jira connection test"
        )

        if retry_result.success:
            return retry_result.result
        else:
            # Handle different types of failures
            if retry_result.timeout_exceeded:
                return (
                    False,
                    {},
                    f"Connection test timed out after {retry_result.total_duration:.1f}s",
                )
            elif retry_result.final_error:
                # Check for specific error types
                if "certificate verify failed" in retry_result.final_error.lower():
                    return (
                        False,
                        {},
                        "SSL certificate verification failed. Check SSL configuration.",
                    )
                elif "ssl" in retry_result.final_error.lower():
                    return (
                        False,
                        {},
                        f"SSL connection error: {retry_result.final_error}",
                    )
                elif "proxy" in retry_result.final_error.lower():
                    return (
                        False,
                        {},
                        f"Proxy connection error: {retry_result.final_error}",
                    )
                elif "timeout" in retry_result.final_error.lower():
                    return (
                        False,
                        {},
                        f"Connection timeout after {retry_result.total_attempts} attempts",
                    )
                else:
                    return (
                        False,
                        {},
                        f"Connection failed after {retry_result.total_attempts} attempts: {retry_result.final_error}",
                    )
            else:
                return (
                    False,
                    {},
                    f"Connection failed after {retry_result.total_attempts} attempts",
                )

    def _get_auth_troubleshooting_steps(self, auth_result: AuthResult) -> list[str]:
        """Get troubleshooting steps for authentication failures.

        Args:
            auth_result: Failed authentication result

        Returns:
            List of troubleshooting steps
        """
        steps = []

        if auth_result.auth_type == JiraAuthType.API_TOKEN:
            steps.extend(
                [
                    "Verify email address is correct",
                    "Check API token is valid and not expired",
                    "Ensure API token has necessary permissions",
                    "For Jira Cloud, generate token at: https://id.atlassian.com/manage-profile/security/api-tokens",
                ]
            )
        elif auth_result.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN:
            steps.extend(
                [
                    "Verify Personal Access Token is valid",
                    "Check token has necessary permissions",
                    "Ensure token is not expired",
                    "For Jira Data Center, generate token in user profile settings",
                ]
            )
        elif auth_result.auth_type == JiraAuthType.SSO:
            steps.extend(
                [
                    "Ensure you are logged into Jira in your browser",
                    "Check SSO session is active",
                    "Try refreshing your browser session",
                    "Contact administrator if SSO is not configured",
                ]
            )
        elif auth_result.auth_type == JiraAuthType.BASIC:
            steps.extend(
                [
                    "Verify username and password are correct",
                    "Check account is not locked or disabled",
                    "Ensure basic authentication is enabled on the server",
                ]
            )

        # Add deployment-specific steps
        if self.deployment_info:
            if self.deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER:
                steps.extend(
                    [
                        "Verify Jira Data Center server is accessible",
                        "Check network connectivity and firewall settings",
                        "Ensure SSL certificates are valid if using HTTPS",
                    ]
                )

        return steps

    def _get_connection_troubleshooting_steps(self, error_message: str) -> list[str]:
        """Get troubleshooting steps for connection failures.

        Args:
            error_message: Error message from connection attempt

        Returns:
            List of troubleshooting steps
        """
        steps = ["Check base URL is correct and accessible"]

        if "timeout" in error_message.lower():
            steps.extend(
                [
                    "Check network connectivity",
                    "Verify firewall settings allow access",
                    "Consider increasing timeout value for slow networks",
                    "Check if proxy configuration is needed",
                ]
            )
        elif "ssl" in error_message.lower() or "certificate" in error_message.lower():
            steps.extend(
                [
                    "Verify SSL certificate is valid",
                    "Check if custom CA certificate is needed",
                    "For Data Center: Ensure certificate chain is complete",
                    "Consider setting verify_ssl=False for testing (not recommended for production)",
                ]
            )
        elif "404" in error_message or "not found" in error_message.lower():
            steps.extend(
                [
                    "Verify Jira server version supports the API",
                    "Check if custom context path is configured",
                    "Ensure Jira REST API is enabled",
                    "For Data Center: Verify API endpoints are accessible",
                ]
            )
        elif "403" in error_message or "forbidden" in error_message.lower():
            steps.extend(
                [
                    "Check user permissions in Jira",
                    "Verify account has API access enabled",
                    "For Data Center: Check application access permissions",
                ]
            )
        elif "proxy" in error_message.lower():
            steps.extend(
                [
                    "Verify proxy configuration is correct",
                    "Check proxy authentication credentials",
                    "Ensure proxy allows HTTPS traffic to Jira",
                    "Test proxy connectivity with a simple HTTP request",
                    "Check if Jira URL should be in proxy bypass list",
                ]
            )

        # Add deployment-specific troubleshooting
        if self.deployment_info:
            if self.deployment_info.deployment_type == JiraDeploymentType.DATA_CENTER:
                steps.extend(
                    [
                        "Verify Jira Data Center is running and accessible",
                        "Check load balancer configuration if applicable",
                        "Ensure all required ports are open (typically 8080/8443)",
                    ]
                )

        return steps

    async def prompt_basic_auth_fallback(self) -> Optional[Dict[str, str]]:
        """Prompt user for basic auth credentials as fallback.

        This method would be called when other authentication methods fail
        and basic auth is available as a fallback option.

        Returns:
            Dictionary with username and password, or None if cancelled
        """
        # In a real implementation, this would prompt the user through the UI
        # For now, we'll log the need for credentials and return None
        self.logger.info("Basic authentication fallback required - user prompt needed")
        self.logger.info(
            "Implementation note: This should prompt user for username/password in the UI"
        )

        # This would be implemented in the UI layer to actually prompt the user
        # The UI would call this method and handle the user interaction
        return None

    async def validate_deployment_specific_config(self) -> list[str]:
        """Validate configuration for deployment-specific requirements.

        Returns:
            List of validation errors, empty if valid
        """
        errors = []

        if not self.deployment_info:
            return errors

        deployment_type = self.deployment_info.deployment_type

        if deployment_type == JiraDeploymentType.DATA_CENTER:
            # Data Center specific validations
            if self.config.auth_type == JiraAuthType.API_TOKEN:
                errors.append(
                    "API tokens are not supported in Jira Data Center. Use Personal Access Token or Basic authentication."
                )

            if self.config.verify_ssl and not self.config.ca_cert_path:
                if (
                    "localhost" not in self.config.base_url
                    and "127.0.0.1" not in self.config.base_url
                ):
                    self.logger.warning(
                        "Data Center deployment without custom CA certificate - SSL verification may fail"
                    )

            # Check for common Data Center ports
            if self.config.custom_port and self.config.custom_port not in [
                8080,
                8443,
                443,
                80,
            ]:
                self.logger.warning(
                    f"Unusual port {self.config.custom_port} for Data Center deployment"
                )

        elif deployment_type == JiraDeploymentType.CLOUD:
            # Cloud specific validations
            if self.config.auth_type == JiraAuthType.BASIC:
                errors.append(
                    "Basic authentication is not recommended for Jira Cloud. Use API tokens."
                )

            if not self.config.base_url.endswith(".atlassian.net"):
                self.logger.warning("Cloud deployment with non-standard URL pattern")

        return errors

    async def get_deployment_health_info(self) -> Dict[str, Any]:
        """Get health information about the Jira deployment.

        Returns:
            Dictionary with health information
        """
        health_info = {
            "deployment_type": (
                self.deployment_info.deployment_type.value
                if self.deployment_info
                else "unknown"
            ),
            "version": (
                self.deployment_info.version if self.deployment_info else "unknown"
            ),
            "api_version": self.api_version or "unknown",
            "authentication_status": (
                "authenticated"
                if self.auth_manager.is_authenticated()
                else "not_authenticated"
            ),
            "available_auth_types": [
                auth_type.value
                for auth_type in self.auth_manager.get_available_auth_types()
            ],
            "base_url": self.config.base_url,
            "ssl_verification": self.config.verify_ssl,
            "timeout": self.config.timeout,
        }

        if self.deployment_info:
            health_info.update(
                {
                    "supports_sso": self.deployment_info.supports_sso,
                    "supports_pat": self.deployment_info.supports_pat,
                    "context_path": self.deployment_info.context_path,
                    "server_title": self.deployment_info.server_title,
                }
            )

        # Add current authentication details (without sensitive info)
        current_auth = self.auth_manager.get_current_auth_result()
        if current_auth:
            health_info["current_auth_type"] = current_auth.auth_type.value
            health_info["auth_success"] = current_auth.success

        return health_info

    async def fetch_ticket(self, ticket_key: str) -> JiraTicket:
        """Fetch a Jira ticket by key with API version support and enhanced authentication.

        Args:
            ticket_key: Jira ticket key (e.g., "PROJ-123")

        Returns:
            JiraTicket object with ticket data

        Raises:
            JiraConnectionError: If connection/auth fails
            JiraTicketNotFoundError: If ticket doesn't exist
            JiraError: For other Jira API errors
        """
        try:
            self._validate_config()

            # Ensure we have authentication
            if not self.auth_manager.is_authenticated():
                auth_result = await self.auth_manager.authenticate()
                if not auth_result.success:
                    raise JiraConnectionError(
                        f"Authentication failed: {auth_result.error_message}"
                    )

            # Get authentication headers
            auth_headers = await self.auth_manager.get_auth_headers()

            # Detect API version if not already done
            if not self.api_version:
                try:
                    self.api_version = (
                        await self.api_version_manager.get_working_api_version(
                            self.base_url, auth_headers
                        )
                    )
                except Exception as e:
                    self.logger.warning(f"API version detection failed, using v3: {e}")
                    self.api_version = "3"

            # Define the ticket fetching operation with retry logic
            async def _perform_ticket_fetch() -> JiraTicket:
                """Inner function to perform the actual ticket fetch."""
                # Get SSL verification and proxy configuration
                verify_config = self.ssl_handler.get_httpx_verify_config()
                proxy_config = self.proxy_handler.get_httpx_proxy_config()

                # Create client with retry-friendly configuration
                client_config = {"verify": verify_config, "proxies": proxy_config}
                client = self.retry_handler.create_http_client_with_retry(client_config)

                async with client:
                    # Construct API URL with detected version
                    url = self.api_version_manager.build_endpoint(
                        self.base_url, f"issue/{ticket_key}", self.api_version
                    )

                    headers = {"Accept": "application/json"}
                    headers.update(auth_headers)

                    # Try different field parameter strategies based on what works
                    # Start with basic fields that should exist in all Jira instances
                    params = {
                        "fields": "summary,description,priority,status,issuetype,assignee,reporter,created,updated",
                        "expand": "",
                    }

                    self.logger.info(
                        f"Fetching Jira ticket: {ticket_key} using API v{self.api_version}"
                    )
                    self.logger.debug(f"Request URL: {url}")
                    self.logger.debug(f"Request params: {params}")
                    response = await client.get(url, headers=headers, params=params)

                    if response.status_code == 200:
                        try:
                            data = response.json()
                            self.logger.info(
                                f"Received response for {ticket_key} with {len(data.get('fields', {}))} fields"
                            )

                            # Check if we got meaningful data
                            fields = data.get("fields", {})
                            has_basic_data = any(
                                [
                                    fields.get("summary"),
                                    fields.get("description"),
                                    (
                                        fields.get("status", {}).get("name")
                                        if isinstance(fields.get("status"), dict)
                                        else fields.get("status")
                                    ),
                                ]
                            )

                            if not has_basic_data:
                                self.logger.warning(
                                    f"No meaningful field data returned for {ticket_key}, trying fallback request"
                                )
                                # Try a simpler request without field restrictions
                                fallback_response = await client.get(
                                    url, headers=headers
                                )
                                if fallback_response.status_code == 200:
                                    fallback_data = fallback_response.json()
                                    self.logger.info(
                                        f"Fallback response for {ticket_key} with {len(fallback_data.get('fields', {}))} fields"
                                    )
                                    return self._parse_ticket_data(fallback_data)

                            return self._parse_ticket_data(data)
                        except (ValueError, json.JSONDecodeError) as e:
                            self.logger.error(
                                f"Failed to parse JSON response for ticket {ticket_key}: {e}"
                            )
                            self.logger.debug(
                                f"Response content: {response.text[:200]}..."
                            )
                            raise JiraConnectionError(
                                f"Invalid JSON response from Jira API: {e}"
                            )
                    elif response.status_code == 401:
                        # Clear authentication and retry once
                        self.auth_manager.clear_auth()
                        auth_result = await self.auth_manager.authenticate()
                        if auth_result.success:
                            headers.update(await self.auth_manager.get_auth_headers())
                            response = await client.get(
                                url, headers=headers, params=params
                            )
                            if response.status_code == 200:
                                try:
                                    data = response.json()
                                    # Apply same fallback logic for retry
                                    fields = data.get("fields", {})
                                    has_basic_data = any(
                                        [
                                            fields.get("summary"),
                                            fields.get("description"),
                                            (
                                                fields.get("status", {}).get("name")
                                                if isinstance(
                                                    fields.get("status"), dict
                                                )
                                                else fields.get("status")
                                            ),
                                        ]
                                    )

                                    if not has_basic_data:
                                        self.logger.warning(
                                            f"Retry: No meaningful field data for {ticket_key}, trying fallback"
                                        )
                                        fallback_response = await client.get(
                                            url, headers=headers
                                        )
                                        if fallback_response.status_code == 200:
                                            fallback_data = fallback_response.json()
                                            return self._parse_ticket_data(
                                                fallback_data
                                            )

                                    return self._parse_ticket_data(data)
                                except (ValueError, json.JSONDecodeError) as e:
                                    self.logger.error(
                                        f"Failed to parse JSON response for ticket {ticket_key} (retry): {e}"
                                    )
                                    raise JiraConnectionError(
                                        f"Invalid JSON response from Jira API: {e}"
                                    )
                        raise JiraConnectionError(
                            "Authentication failed. Check credentials."
                        )
                    elif response.status_code == 403:
                        raise JiraConnectionError(
                            "Access forbidden. Check permissions."
                        )
                    elif response.status_code == 404:
                        # Try fallback API version if we're using v3
                        if self.api_version == "3":
                            self.logger.info(
                                "Ticket not found with API v3, trying v2 fallback"
                            )
                            fallback_url = self.api_version_manager.build_endpoint(
                                self.base_url, f"issue/{ticket_key}", "2"
                            )
                            response = await client.get(
                                fallback_url, headers=headers, params=params
                            )
                            if response.status_code == 200:
                                self.api_version = "2"  # Update to working version
                                try:
                                    data = response.json()
                                    return self._parse_ticket_data(data)
                                except (ValueError, json.JSONDecodeError) as e:
                                    self.logger.error(
                                        f"Failed to parse JSON response for ticket {ticket_key} (fallback): {e}"
                                    )
                                    raise JiraConnectionError(
                                        f"Invalid JSON response from Jira API: {e}"
                                    )
                            elif response.status_code == 404:
                                raise JiraTicketNotFoundError(
                                    f"Ticket '{ticket_key}' not found"
                                )
                        else:
                            raise JiraTicketNotFoundError(
                                f"Ticket '{ticket_key}' not found"
                            )
                    elif response.status_code in [429, 502, 503, 504]:
                        # These status codes should trigger retry
                        response.raise_for_status()
                    else:
                        raise JiraError(f"HTTP {response.status_code}: {response.text}")

            # Execute with retry logic
            retry_result = await self.retry_handler.execute_with_retry(
                _perform_ticket_fetch, f"Jira ticket fetch ({ticket_key})"
            )

            if retry_result.success:
                return retry_result.result
            else:
                # Handle different types of failures
                if retry_result.timeout_exceeded:
                    raise JiraConnectionError(
                        f"Ticket fetch timed out after {retry_result.total_duration:.1f}s"
                    )
                elif retry_result.final_error:
                    if "404" in retry_result.final_error:
                        raise JiraTicketNotFoundError(
                            f"Ticket '{ticket_key}' not found"
                        )
                    elif (
                        "401" in retry_result.final_error
                        or "403" in retry_result.final_error
                    ):
                        raise JiraConnectionError(
                            f"Authentication/authorization failed: {retry_result.final_error}"
                        )
                    else:
                        raise JiraError(
                            f"Ticket fetch failed after {retry_result.total_attempts} attempts: {retry_result.final_error}"
                        )
                else:
                    raise JiraError(
                        f"Ticket fetch failed after {retry_result.total_attempts} attempts"
                    )

        except httpx.TimeoutException as e:
            error_detail = self.error_handler.create_error_detail(
                error_message=f"Connection timeout after {self.timeout} seconds",
                exception=e,
                technical_details=f"Timeout while fetching ticket {ticket_key}",
            )
            self.logger.error(
                f"Timeout fetching ticket {ticket_key}: {error_detail.troubleshooting_steps}"
            )
            raise JiraConnectionError(
                f"Connection timeout after {self.timeout} seconds"
            )
        except httpx.ConnectError as e:
            error_detail = self.error_handler.create_error_detail(
                error_message="Failed to connect to Jira. Check base URL.",
                exception=e,
                technical_details=f"Connection error while fetching ticket {ticket_key}",
            )
            self.logger.error(
                f"Connection error fetching ticket {ticket_key}: {error_detail.troubleshooting_steps}"
            )
            raise JiraConnectionError("Failed to connect to Jira. Check base URL.")
        except (JiraConnectionError, JiraTicketNotFoundError, JiraError):
            raise
        except Exception as e:
            error_detail = self.error_handler.create_error_detail(
                error_message=f"Unexpected error: {str(e)}",
                exception=e,
                technical_details=f"Unexpected error while fetching ticket {ticket_key}, Exception type: {type(e).__name__}",
            )
            self.logger.error(
                f"Unexpected error fetching Jira ticket {ticket_key}: {e}"
            )
            self.logger.error(
                f"Troubleshooting steps: {error_detail.troubleshooting_steps}"
            )
            raise JiraError(f"Unexpected error: {str(e)}")

    def _parse_ticket_data(self, data: Dict[str, Any]) -> JiraTicket:
        """Parse Jira API response data into enhanced JiraTicket object with comprehensive requirements fields.

        Args:
            data: Raw Jira API response data

        Returns:
            JiraTicket object with all relevant requirements fields
        """
        fields = data.get("fields", {})

        # Debug logging to see what fields we're receiving
        self.logger.info(
            f"Parsing ticket data for {data.get('key', 'UNKNOWN')} - available fields: {len(fields)} total"
        )

        # Log custom fields specifically for acceptance criteria debugging
        custom_fields = {
            k: v for k, v in fields.items() if k.startswith("customfield_")
        }
        if custom_fields:
            self.logger.info(f"Custom fields found: {list(custom_fields.keys())}")
            # Log first few characters of each custom field to help identify acceptance criteria
            for field_name, field_value in list(custom_fields.items())[
                :5
            ]:  # Limit to first 5 for readability
                if field_value:
                    if isinstance(field_value, dict):
                        preview = str(field_value)[:50]
                    elif isinstance(field_value, str):
                        preview = field_value[:50]
                    else:
                        preview = str(field_value)[:50]
                    self.logger.debug(
                        f"  {field_name}: {preview}{'...' if len(str(field_value)) > 50 else ''}"
                    )
        else:
            self.logger.info("No custom fields found in ticket")

        if not fields:
            self.logger.warning(
                f"No fields found in response for ticket {data.get('key', 'UNKNOWN')}"
            )
            self.logger.warning(
                f"Full response data: {json.dumps(data, indent=2)[:1000]}..."
            )

        # Log key field values for debugging
        self.logger.info(
            f"Key field values - summary: '{fields.get('summary', 'MISSING')}', status: {fields.get('status', 'MISSING')}, priority: {fields.get('priority', 'MISSING')}"
        )

        # Extract basic fields with enhanced error handling
        key = data.get("key", "")
        summary = fields.get("summary", "")

        # Handle missing summary gracefully
        if not summary:
            self.logger.warning(f"No summary found for ticket {key}")
            summary = f"Ticket {key}"

        description = fields.get("description", {})

        # Handle description (can be complex Atlassian Document Format or plain text)
        description_text = ""
        if description:
            if isinstance(description, dict):
                # Try to extract plain text from ADF (Atlassian Document Format)
                description_text = self._extract_text_from_adf(description)
            elif isinstance(description, str):
                description_text = description

        # Extract priority with Data Center compatibility
        priority_obj = fields.get("priority")
        priority = None
        if priority_obj:
            if isinstance(priority_obj, dict):
                priority = priority_obj.get("name")
            elif isinstance(priority_obj, str):
                priority = priority_obj

        # Extract status with enhanced error handling
        status_obj = fields.get("status", {})
        status = "Unknown"
        if isinstance(status_obj, dict):
            status = status_obj.get("name", "Unknown")
        elif isinstance(status_obj, str):
            status = status_obj

        # Extract issue type with compatibility handling
        issuetype_obj = fields.get("issuetype", {})
        issue_type = "Unknown"
        if isinstance(issuetype_obj, dict):
            issue_type = issuetype_obj.get("name", "Unknown")
        elif isinstance(issuetype_obj, str):
            issue_type = issuetype_obj

        # Extract assignee and reporter with enhanced handling
        assignee_obj = fields.get("assignee")
        assignee = None
        if assignee_obj:
            if isinstance(assignee_obj, dict):
                assignee = (
                    assignee_obj.get("displayName")
                    or assignee_obj.get("name")
                    or assignee_obj.get("key")
                )
            elif isinstance(assignee_obj, str):
                assignee = assignee_obj

        reporter_obj = fields.get("reporter")
        reporter = None
        if reporter_obj:
            if isinstance(reporter_obj, dict):
                reporter = (
                    reporter_obj.get("displayName")
                    or reporter_obj.get("name")
                    or reporter_obj.get("key")
                )
            elif isinstance(reporter_obj, str):
                reporter = reporter_obj

        # Extract labels with type safety
        labels = fields.get("labels", [])
        if not isinstance(labels, list):
            labels = []

        # Extract components with enhanced error handling
        components_list = fields.get("components", [])
        components = []
        if isinstance(components_list, list):
            for comp in components_list:
                if isinstance(comp, dict):
                    comp_name = comp.get("name", "")
                    if comp_name:
                        components.append(comp_name)
                elif isinstance(comp, str):
                    components.append(comp)

        # Extract dates
        created = fields.get("created")
        updated = fields.get("updated")

        # === NEW: Extract requirements-specific fields ===

        # Extract acceptance criteria (common custom field names)
        acceptance_criteria = self._extract_acceptance_criteria(fields)

        # Extract comments (if available in the response)
        comments = self._extract_comments(data.get("fields", {}).get("comment", {}))

        # Extract attachments
        attachments = self._extract_attachments(fields.get("attachment", []))

        # Extract custom fields that might contain requirements
        custom_fields = self._extract_custom_fields(fields)

        # Extract project information
        project_obj = fields.get("project", {})
        project_key = project_obj.get("key") if isinstance(project_obj, dict) else None
        project_name = (
            project_obj.get("name") if isinstance(project_obj, dict) else None
        )

        # Extract epic information
        epic_link = (
            fields.get("customfield_10014")
            or fields.get("epic link")
            or fields.get("epicLink")
        )
        epic_name = (
            fields.get("customfield_10011")
            or fields.get("epic name")
            or fields.get("epicName")
        )

        # Extract story points (common field names)
        story_points = (
            fields.get("customfield_10016")
            or fields.get("story points")
            or fields.get("storyPoints")
        )
        if story_points and isinstance(story_points, (int, float)):
            story_points = float(story_points)
        else:
            story_points = None

        # Extract sprint information
        sprint = self._extract_sprint_info(fields)

        # Extract versions
        fix_versions = self._extract_versions(fields.get("fixVersions", []))
        affects_versions = self._extract_versions(fields.get("versions", []))

        # Extract relationships
        parent = fields.get("parent", {}).get("key") if fields.get("parent") else None
        subtasks = [st.get("key") for st in fields.get("subtasks", []) if st.get("key")]
        linked_issues = self._extract_linked_issues(
            data.get("fields", {}).get("issuelinks", [])
        )

        # Extract resolution information
        resolution_obj = fields.get("resolution")
        resolution = (
            resolution_obj.get("name") if isinstance(resolution_obj, dict) else None
        )
        resolution_date = fields.get("resolutiondate")
        due_date = fields.get("duedate")

        # Extract environment and testing fields
        environment = fields.get("environment")
        if isinstance(environment, dict):
            environment = self._extract_text_from_adf(environment)

        # Look for test cases in common custom fields
        test_cases = (
            fields.get("customfield_10020")
            or fields.get("test cases")
            or fields.get("testCases")
        )
        if isinstance(test_cases, dict):
            test_cases = self._extract_text_from_adf(test_cases)

        # Extract business context fields
        business_value = (
            fields.get("customfield_10021")
            or fields.get("business value")
            or fields.get("businessValue")
        )
        if isinstance(business_value, dict):
            business_value = self._extract_text_from_adf(business_value)

        # Extract user story field
        user_story = (
            fields.get("customfield_10022")
            or fields.get("user story")
            or fields.get("userStory")
        )
        if isinstance(user_story, dict):
            user_story = self._extract_text_from_adf(user_story)

        self.logger.info(
            f"Enhanced parsing for ticket {key}: status={status}, type={issue_type}, "
            f"assignee={assignee}, components={len(components)}, "
            f"acceptance_criteria={'Yes' if acceptance_criteria else 'No'}, "
            f"comments={len(comments)}, attachments={len(attachments)}"
        )

        # Final validation - ensure we have at least basic data
        if not key:
            self.logger.error("No ticket key found in response data")
        if not summary:
            self.logger.warning(f"No summary found for ticket {key}")
        if status == "Unknown":
            self.logger.warning(f"Status not found for ticket {key}")
        if issue_type == "Unknown":
            self.logger.warning(f"Issue type not found for ticket {key}")

        return JiraTicket(
            # Core fields
            key=key,
            summary=summary,
            description=description_text,
            priority=priority,
            status=status,
            issue_type=issue_type,
            assignee=assignee,
            reporter=reporter,
            labels=labels,
            components=components,
            created=created,
            updated=updated,
            # Requirements-specific fields
            acceptance_criteria=acceptance_criteria,
            comments=comments,
            attachments=attachments,
            custom_fields=custom_fields,
            # Additional context fields
            project_key=project_key,
            project_name=project_name,
            epic_link=epic_link,
            epic_name=epic_name,
            story_points=story_points,
            sprint=sprint,
            fix_versions=fix_versions,
            affects_versions=affects_versions,
            # Relationships
            parent=parent,
            subtasks=subtasks,
            linked_issues=linked_issues,
            # Workflow and resolution
            resolution=resolution,
            resolution_date=resolution_date,
            due_date=due_date,
            # Environment and testing
            environment=environment,
            test_cases=test_cases,
            # Business context
            business_value=business_value,
            user_story=user_story,
        )

    def _extract_acceptance_criteria(self, fields: Dict[str, Any]) -> Optional[str]:
        """Extract acceptance criteria from various possible field locations."""
        # Common field names for acceptance criteria (exact matches)
        ac_field_names = [
            "customfield_10015",  # Common Jira Cloud field
            "customfield_10019",  # Another common field
            "customfield_10020",  # Additional common field
            "customfield_10021",  # Additional common field
            "customfield_10022",  # Additional common field
            "customfield_10023",  # Additional common field
            "customfield_10024",  # Additional common field
            "customfield_10025",  # Additional common field
            "customfield_10026",  # Additional common field
            "customfield_10027",  # Additional common field
            "customfield_10028",  # Additional common field
            "customfield_10029",  # Additional common field
            "customfield_10030",  # Additional common field
            "acceptance criteria",
            "acceptanceCriteria",
            "ac",
            "definition of done",
            "definitionOfDone",
            "dod",
        ]

        # First, try exact field name matches
        for field_name in ac_field_names:
            field_value = fields.get(field_name)
            if field_value:
                if isinstance(field_value, dict):
                    extracted_text = self._extract_text_from_adf(field_value)
                    if extracted_text and extracted_text.strip():
                        self.logger.info(
                            f"Found acceptance criteria in field '{field_name}': {len(extracted_text)} characters"
                        )
                        return extracted_text
                elif isinstance(field_value, str) and field_value.strip():
                    self.logger.info(
                        f"Found acceptance criteria in field '{field_name}': {len(field_value)} characters"
                    )
                    return field_value

        # If no exact matches, search through all custom fields for acceptance criteria keywords
        self.logger.debug(
            "No exact field matches found, searching through all custom fields for acceptance criteria"
        )

        acceptance_keywords = [
            "acceptance",
            "criteria",
            "definition",
            "done",
            "requirements",
            "conditions",
            "specifications",
            "specs",
            "validation",
            "verify",
        ]

        for field_name, field_value in fields.items():
            # Only check custom fields and fields that might contain acceptance criteria
            if field_name.startswith("customfield_") or any(
                keyword in field_name.lower() for keyword in acceptance_keywords
            ):

                if field_value:
                    extracted_text = None
                    if isinstance(field_value, dict):
                        extracted_text = self._extract_text_from_adf(field_value)
                    elif isinstance(field_value, str):
                        extracted_text = field_value

                    # Check if the content looks like acceptance criteria
                    if (
                        extracted_text
                        and extracted_text.strip()
                        and len(extracted_text) > 10  # Must have substantial content
                        and any(
                            keyword in extracted_text.lower()
                            for keyword in acceptance_keywords
                        )
                    ):

                        self.logger.info(
                            f"Found potential acceptance criteria in field '{field_name}': {len(extracted_text)} characters"
                        )
                        self.logger.debug(f"Content preview: {extracted_text[:100]}...")
                        return extracted_text

        # Log available custom fields for debugging
        custom_fields = [k for k in fields.keys() if k.startswith("customfield_")]
        if custom_fields:
            self.logger.debug(
                f"Available custom fields: {custom_fields[:10]}{'...' if len(custom_fields) > 10 else ''}"
            )
        else:
            self.logger.debug("No custom fields found in ticket")

        return None

    def _extract_comments(self, comment_data: Dict[str, Any]) -> list[dict]:
        """Extract comments with author and content information."""
        comments = []
        comment_list = comment_data.get("comments", [])

        for comment in comment_list:
            if isinstance(comment, dict):
                author_obj = comment.get("author", {})
                author = (
                    (
                        author_obj.get("displayName")
                        or author_obj.get("name")
                        or "Unknown"
                    )
                    if isinstance(author_obj, dict)
                    else str(author_obj)
                )

                body = comment.get("body", "")
                if isinstance(body, dict):
                    body = self._extract_text_from_adf(body)

                created = comment.get("created", "")

                if body:  # Only include comments with content
                    comments.append(
                        {"author": author, "body": body, "created": created}
                    )

        return comments

    def _extract_attachments(self, attachment_list: list) -> list[dict]:
        """Extract attachment information."""
        attachments = []

        for attachment in attachment_list:
            if isinstance(attachment, dict):
                attachments.append(
                    {
                        "filename": attachment.get("filename", ""),
                        "size": attachment.get("size", 0),
                        "mimeType": attachment.get("mimeType", ""),
                        "created": attachment.get("created", ""),
                        "author": attachment.get("author", {}).get(
                            "displayName", "Unknown"
                        ),
                    }
                )

        return attachments

    def _extract_custom_fields(self, fields: Dict[str, Any]) -> dict:
        """Extract all custom fields that might contain requirements information."""
        custom_fields = {}

        for field_name, field_value in fields.items():
            if field_name.startswith("customfield_"):
                # Try to extract meaningful content
                if isinstance(field_value, dict):
                    # Check if it's ADF content
                    if "content" in field_value or "type" in field_value:
                        extracted_text = self._extract_text_from_adf(field_value)
                        if extracted_text:
                            custom_fields[field_name] = extracted_text
                    else:
                        # It might be an object with name/value
                        if "name" in field_value:
                            custom_fields[field_name] = field_value["name"]
                        elif "value" in field_value:
                            custom_fields[field_name] = field_value["value"]
                elif isinstance(field_value, (str, int, float, bool)) and field_value:
                    custom_fields[field_name] = field_value
                elif isinstance(field_value, list) and field_value:
                    # Handle arrays of values
                    values = []
                    for item in field_value:
                        if isinstance(item, dict) and "name" in item:
                            values.append(item["name"])
                        elif isinstance(item, dict) and "value" in item:
                            values.append(item["value"])
                        elif isinstance(item, str):
                            values.append(item)
                    if values:
                        custom_fields[field_name] = values

        return custom_fields

    def _extract_sprint_info(self, fields: Dict[str, Any]) -> Optional[str]:
        """Extract sprint information from various possible locations."""
        # Common sprint field names
        sprint_fields = [
            "customfield_10020",  # Common Jira Cloud sprint field
            "customfield_10010",  # Another common field
            "sprint",
            "sprints",
        ]

        for field_name in sprint_fields:
            sprint_data = fields.get(field_name)
            if sprint_data:
                if isinstance(sprint_data, list) and sprint_data:
                    # Take the latest sprint
                    latest_sprint = sprint_data[-1]
                    if isinstance(latest_sprint, dict):
                        return latest_sprint.get("name", "")
                    elif isinstance(latest_sprint, str):
                        return latest_sprint
                elif isinstance(sprint_data, dict):
                    return sprint_data.get("name", "")
                elif isinstance(sprint_data, str):
                    return sprint_data

        return None

    def _extract_versions(self, version_list: list) -> list[str]:
        """Extract version names from version objects."""
        versions = []
        for version in version_list:
            if isinstance(version, dict):
                name = version.get("name", "")
                if name:
                    versions.append(name)
            elif isinstance(version, str):
                versions.append(version)
        return versions

    def _extract_linked_issues(self, issuelinks: list) -> list[dict]:
        """Extract linked issues with relationship information."""
        linked_issues = []

        for link in issuelinks:
            if isinstance(link, dict):
                link_type = link.get("type", {})
                relationship = (
                    link_type.get("name", "Unknown")
                    if isinstance(link_type, dict)
                    else "Unknown"
                )

                # Check both inward and outward links
                for direction in ["inwardIssue", "outwardIssue"]:
                    linked_issue = link.get(direction)
                    if linked_issue and isinstance(linked_issue, dict):
                        linked_issues.append(
                            {
                                "key": linked_issue.get("key", ""),
                                "summary": linked_issue.get("fields", {}).get(
                                    "summary", ""
                                ),
                                "relationship": relationship,
                                "direction": direction,
                            }
                        )

        return linked_issues

    def _extract_text_from_adf(self, adf_content: Dict[str, Any]) -> str:
        """Extract plain text from Atlassian Document Format with enhanced Data Center support.

        Args:
            adf_content: ADF content dictionary

        Returns:
            Plain text string
        """

        def extract_text_recursive(node):
            if isinstance(node, dict):
                text_parts = []

                # Handle text nodes
                if node.get("type") == "text":
                    text = node.get("text", "")
                    # Handle text formatting marks
                    marks = node.get("marks", [])
                    if marks:
                        # Add basic formatting indicators
                        for mark in marks:
                            mark_type = mark.get("type", "")
                            if mark_type == "strong":
                                text = f"**{text}**"
                            elif mark_type == "em":
                                text = f"*{text}*"
                            elif mark_type == "code":
                                text = f"`{text}`"
                    return text

                # Handle paragraph nodes
                elif node.get("type") == "paragraph":
                    content = node.get("content", [])
                    if isinstance(content, list):
                        para_text = []
                        for child in content:
                            child_text = extract_text_recursive(child)
                            if child_text:
                                para_text.append(child_text)
                        return " ".join(para_text) + "\n"

                # Handle list nodes
                elif node.get("type") in ["bulletList", "orderedList"]:
                    content = node.get("content", [])
                    if isinstance(content, list):
                        list_items = []
                        for item in content:
                            item_text = extract_text_recursive(item)
                            if item_text:
                                prefix = (
                                    "• " if node.get("type") == "bulletList" else "1. "
                                )
                                list_items.append(f"{prefix}{item_text.strip()}")
                        return "\n".join(list_items) + "\n"

                # Handle list item nodes
                elif node.get("type") == "listItem":
                    content = node.get("content", [])
                    if isinstance(content, list):
                        item_parts = []
                        for child in content:
                            child_text = extract_text_recursive(child)
                            if child_text:
                                item_parts.append(child_text.strip())
                        return " ".join(item_parts)

                # Handle heading nodes
                elif node.get("type") == "heading":
                    level = node.get("attrs", {}).get("level", 1)
                    content = node.get("content", [])
                    if isinstance(content, list):
                        heading_text = []
                        for child in content:
                            child_text = extract_text_recursive(child)
                            if child_text:
                                heading_text.append(child_text)
                        heading = " ".join(heading_text)
                        return f"{'#' * level} {heading}\n"

                # Handle code block nodes
                elif node.get("type") == "codeBlock":
                    content = node.get("content", [])
                    if isinstance(content, list):
                        code_parts = []
                        for child in content:
                            child_text = extract_text_recursive(child)
                            if child_text:
                                code_parts.append(child_text)
                        return f"```\n{' '.join(code_parts)}\n```\n"

                # Handle other node types with content
                else:
                    content = node.get("content", [])
                    if isinstance(content, list):
                        for child in content:
                            child_text = extract_text_recursive(child)
                            if child_text:
                                text_parts.append(child_text)

                return " ".join(text_parts)
            elif isinstance(node, list):
                text_parts = []
                for item in node:
                    item_text = extract_text_recursive(item)
                    if item_text:
                        text_parts.append(item_text)
                return " ".join(text_parts)
            else:
                return str(node) if node else ""

        try:
            extracted_text = extract_text_recursive(adf_content).strip()
            # Clean up excessive whitespace and newlines
            import re

            extracted_text = re.sub(
                r"\n\s*\n", "\n\n", extracted_text
            )  # Normalize paragraph breaks
            extracted_text = re.sub(r" +", " ", extracted_text)  # Normalize spaces
            return extracted_text
        except Exception as e:
            self.logger.warning(f"Failed to extract text from ADF: {e}")
            # Fallback to simple string conversion
            return (
                str(adf_content)[:1000] + "..."
                if len(str(adf_content)) > 1000
                else str(adf_content)
            )

    def _decode_html_entities(self, text: Optional[str]) -> Optional[str]:
        """Decode HTML entities in text content, handling double-encoding.

        Args:
            text: Text that may contain HTML entities (possibly double-encoded)

        Returns:
            Text with HTML entities decoded, or None if input was None
        """
        if text is None:
            return None

        # Handle double-encoded entities by decoding twice if needed
        decoded = html.unescape(text)

        # Check if there are still encoded entities (indicating double-encoding)
        if (
            "&amp;" in decoded
            or "&lt;" in decoded
            or "&gt;" in decoded
            or "&quot;" in decoded
        ):
            decoded = html.unescape(decoded)

        return decoded

    def map_ticket_to_requirements(self, ticket: JiraTicket) -> Dict[str, Any]:
        """Map Jira ticket data to comprehensive requirements format with all relevant fields.

        Args:
            ticket: JiraTicket object

        Returns:
            Requirements dictionary with comprehensive requirements information
        """
        # Build comprehensive description from all relevant fields
        description_parts = []

        # Start with summary and description (decode HTML entities)
        if ticket.summary:
            description_parts.append(
                f"**Summary:** {self._decode_html_entities(ticket.summary)}"
            )

        if ticket.description:
            description_parts.append(
                f"**Description:** {self._decode_html_entities(ticket.description)}"
            )

        # Add acceptance criteria if available
        if ticket.acceptance_criteria:
            description_parts.append(
                f"**Acceptance Criteria:** {self._decode_html_entities(ticket.acceptance_criteria)}"
            )

        # Add user story if available
        if ticket.user_story:
            description_parts.append(
                f"**User Story:** {self._decode_html_entities(ticket.user_story)}"
            )

        # Add business value if available
        if ticket.business_value:
            description_parts.append(
                f"**Business Value:** {self._decode_html_entities(ticket.business_value)}"
            )

        # Add environment details if available
        if ticket.environment:
            description_parts.append(
                f"**Environment:** {self._decode_html_entities(ticket.environment)}"
            )

        # Add test cases if available
        if ticket.test_cases:
            description_parts.append(
                f"**Test Cases:** {self._decode_html_entities(ticket.test_cases)}"
            )

        # Add relevant comments (limit to most recent 3 to avoid overwhelming)
        if ticket.comments:
            recent_comments = ticket.comments[-3:]  # Get last 3 comments
            comments_text = []
            for comment in recent_comments:
                decoded_body = self._decode_html_entities(comment["body"])
                comments_text.append(
                    f"- {comment['author']}: {decoded_body[:200]}{'...' if len(decoded_body) > 200 else ''}"
                )
            if comments_text:
                description_parts.append(
                    "**Recent Comments:**\n" + "\n".join(comments_text)
                )

        # Add custom fields that might contain requirements
        if ticket.custom_fields:
            relevant_custom_fields = []
            for field_name, field_value in ticket.custom_fields.items():
                # Only include text-based custom fields that might contain requirements
                if isinstance(field_value, str) and len(field_value) > 10:
                    decoded_value = self._decode_html_entities(field_value)
                    relevant_custom_fields.append(
                        f"- {field_name}: {decoded_value[:150]}{'...' if len(decoded_value) > 150 else ''}"
                    )
            if relevant_custom_fields:
                description_parts.append(
                    "**Additional Requirements (Custom Fields):**\n"
                    + "\n".join(relevant_custom_fields)
                )

        # Create comprehensive requirements object
        requirements = {
            "description": "\n\n".join(description_parts),
            "source": "jira",
            "jira_key": ticket.key,
            # Add metadata for context
            "metadata": {
                "issue_type": ticket.issue_type,
                "priority": ticket.priority,
                "status": ticket.status,
                "assignee": ticket.assignee,
                "reporter": ticket.reporter,
                "project": (
                    f"{ticket.project_name} ({ticket.project_key})"
                    if ticket.project_name and ticket.project_key
                    else None
                ),
                "epic": ticket.epic_name if ticket.epic_name else ticket.epic_link,
                "story_points": ticket.story_points,
                "sprint": ticket.sprint,
                "components": ticket.components,
                "labels": ticket.labels,
                "due_date": ticket.due_date,
                "attachments_count": (
                    len(ticket.attachments) if ticket.attachments else 0
                ),
                "linked_issues_count": (
                    len(ticket.linked_issues) if ticket.linked_issues else 0
                ),
                "subtasks_count": len(ticket.subtasks) if ticket.subtasks else 0,
            },
        }

        # Try to infer domain from components or labels (for logging only)
        domain_hints = []
        if ticket.components:
            domain_hints.extend(ticket.components)
        if ticket.labels:
            domain_hints.extend(ticket.labels)

        # Map common Jira fields to domain categories
        domain_mapping = {
            "backend": "backend",
            "frontend": "frontend",
            "api": "backend",
            "ui": "frontend",
            "database": "data",
            "data": "data",
            "integration": "integration",
            "automation": "automation",
            "testing": "testing",
            "devops": "devops",
            "infrastructure": "devops",
        }

        inferred_domains = []
        for hint in domain_hints:
            hint_lower = hint.lower()
            for key, domain in domain_mapping.items():
                if key in hint_lower:
                    inferred_domains.append(domain)

        # Only add domain if it's clearly identifiable and useful
        if inferred_domains:
            requirements["domain"] = inferred_domains[0]  # Take first match

        # Try to infer pattern types from issue type and description (for logging only)
        pattern_types = []
        issue_type_lower = ticket.issue_type.lower() if ticket.issue_type else ""
        description_lower = (ticket.summary + " " + (ticket.description or "")).lower()

        # Pattern type inference rules
        if "story" in issue_type_lower or "feature" in issue_type_lower:
            pattern_types.append("feature_development")
        elif "bug" in issue_type_lower or "defect" in issue_type_lower:
            pattern_types.append("bug_fix")
        elif "task" in issue_type_lower:
            if any(
                word in description_lower for word in ["deploy", "release", "build"]
            ):
                pattern_types.append("deployment")
            elif any(word in description_lower for word in ["test", "qa", "quality"]):
                pattern_types.append("testing")
            else:
                pattern_types.append("maintenance")

        # Add pattern types based on description keywords
        components_text = (
            " ".join(ticket.components).lower() if ticket.components else ""
        )
        combined_text = description_lower + " " + components_text
        if any(word in combined_text for word in ["api", "endpoint", "service"]):
            pattern_types.append("api_development")
        if any(word in combined_text for word in ["database", "migration", "schema"]):
            pattern_types.append("data_processing")
        if any(word in combined_text for word in ["automate", "automation", "script"]):
            pattern_types.append("automation")

        # Only add pattern types if they're clearly identifiable and useful
        if pattern_types:
            requirements["pattern_types"] = list(
                set(pattern_types)
            )  # Remove duplicates

        self.logger.info(
            f"Mapped Jira ticket {ticket.key} to requirements with domain: {requirements.get('domain')} and pattern_types: {requirements.get('pattern_types')}"
        )

        return requirements

    async def fetch_ticket_with_version_fallback(self, ticket_key: str) -> JiraTicket:
        """Fetch ticket with comprehensive API version fallback and error handling.

        This method provides enhanced error handling and API version fallback
        specifically for Data Center deployments.

        Args:
            ticket_key: Jira ticket key (e.g., "PROJ-123")

        Returns:
            JiraTicket object with ticket data

        Raises:
            JiraConnectionError: If connection/auth fails
            JiraTicketNotFoundError: If ticket doesn't exist
            JiraError: For other Jira API errors
        """
        # Use the main fetch_ticket method which already has fallback logic
        return await self.fetch_ticket(ticket_key)

    def _handle_api_response_differences(
        self, data: Dict[str, Any], api_version: str
    ) -> Dict[str, Any]:
        """Handle API response differences between versions.

        Args:
            data: Raw API response data
            api_version: API version used for the request

        Returns:
            Normalized response data
        """
        # API v2 and v3 have some differences in response format
        if api_version == "2":
            # API v2 specific handling
            fields = data.get("fields", {})

            # In API v2, some fields might have different structures
            # Normalize status field
            if "status" in fields and isinstance(fields["status"], dict):
                # Ensure status has the expected structure
                if "name" not in fields["status"] and "value" in fields["status"]:
                    fields["status"]["name"] = fields["status"]["value"]

            # Normalize priority field
            if "priority" in fields and isinstance(fields["priority"], dict):
                if "name" not in fields["priority"] and "value" in fields["priority"]:
                    fields["priority"]["name"] = fields["priority"]["value"]

            # Normalize issue type field
            if "issuetype" in fields and isinstance(fields["issuetype"], dict):
                if "name" not in fields["issuetype"] and "value" in fields["issuetype"]:
                    fields["issuetype"]["name"] = fields["issuetype"]["value"]

        elif api_version == "3":
            # API v3 specific handling
            fields = data.get("fields", {})

            # API v3 might have additional nested structures
            # Handle any v3-specific normalization here
            pass

        return data

    def _parse_custom_fields(self, fields: Dict[str, Any]) -> Dict[str, Any]:
        """Parse custom fields from Jira response with Data Center compatibility.

        Args:
            fields: Fields dictionary from Jira API response

        Returns:
            Dictionary of parsed custom fields
        """
        custom_fields = {}

        for field_key, field_value in fields.items():
            # Custom fields typically start with "customfield_"
            if field_key.startswith("customfield_"):
                try:
                    # Handle different custom field types
                    if isinstance(field_value, dict):
                        # Complex custom field (select, user, etc.)
                        if "value" in field_value:
                            custom_fields[field_key] = field_value["value"]
                        elif "displayName" in field_value:
                            custom_fields[field_key] = field_value["displayName"]
                        elif "name" in field_value:
                            custom_fields[field_key] = field_value["name"]
                        else:
                            custom_fields[field_key] = str(field_value)
                    elif isinstance(field_value, list):
                        # Multi-value custom field
                        values = []
                        for item in field_value:
                            if isinstance(item, dict):
                                if "value" in item:
                                    values.append(item["value"])
                                elif "name" in item:
                                    values.append(item["name"])
                                else:
                                    values.append(str(item))
                            else:
                                values.append(str(item))
                        custom_fields[field_key] = values
                    else:
                        # Simple custom field
                        custom_fields[field_key] = field_value
                except Exception as e:
                    self.logger.warning(
                        f"Failed to parse custom field {field_key}: {e}"
                    )
                    custom_fields[field_key] = str(field_value)

        return custom_fields

    async def get_ticket_transitions(self, ticket_key: str) -> list[Dict[str, Any]]:
        """Get available transitions for a ticket.

        Args:
            ticket_key: Jira ticket key

        Returns:
            List of available transitions

        Raises:
            JiraConnectionError: If connection/auth fails
            JiraTicketNotFoundError: If ticket doesn't exist
            JiraError: For other Jira API errors
        """
        try:
            self._validate_config()

            # Ensure we have authentication
            if not self.auth_manager.is_authenticated():
                auth_result = await self.auth_manager.authenticate()
                if not auth_result.success:
                    raise JiraConnectionError(
                        f"Authentication failed: {auth_result.error_message}"
                    )

            # Get authentication headers
            auth_headers = await self.auth_manager.get_auth_headers()

            # Use detected API version or default
            api_version = self.api_version or "3"

            # Get SSL verification and proxy configuration
            verify_config = self.ssl_handler.get_httpx_verify_config()
            proxy_config = self.proxy_handler.get_httpx_proxy_config()

            # Create client with proper SSL and proxy configuration
            client_config = {
                "timeout": self.timeout,
                "verify": verify_config,
                "proxies": proxy_config,
            }

            async with httpx.AsyncClient(**client_config) as client:
                # Construct transitions API URL
                url = self.api_version_manager.build_endpoint(
                    self.base_url, f"issue/{ticket_key}/transitions", api_version
                )

                headers = {"Accept": "application/json"}
                headers.update(auth_headers)

                self.logger.info(f"Fetching transitions for ticket: {ticket_key}")
                response = await client.get(url, headers=headers)

                if response.status_code == 200:
                    data = response.json()
                    transitions = data.get("transitions", [])

                    # Normalize transition data
                    normalized_transitions = []
                    for transition in transitions:
                        normalized_transitions.append(
                            {
                                "id": transition.get("id"),
                                "name": transition.get("name"),
                                "to": transition.get("to", {}).get("name"),
                                "hasScreen": transition.get("hasScreen", False),
                            }
                        )

                    return normalized_transitions
                elif response.status_code == 404:
                    raise JiraTicketNotFoundError(f"Ticket '{ticket_key}' not found")
                elif response.status_code == 401:
                    raise JiraConnectionError(
                        "Authentication failed. Check credentials."
                    )
                elif response.status_code == 403:
                    raise JiraConnectionError("Access forbidden. Check permissions.")
                else:
                    raise JiraError(f"HTTP {response.status_code}: {response.text}")

        except (JiraConnectionError, JiraTicketNotFoundError, JiraError):
            raise
        except Exception as e:
            self.logger.error(
                f"Unexpected error fetching transitions for {ticket_key}: {e}"
            )
            raise JiraError(f"Unexpected error: {str(e)}")


def create_jira_service(config: JiraConfig) -> JiraService:
    """Factory function to create JiraService instance.

    Args:
        config: Jira configuration

    Returns:
        JiraService instance
    """
    return JiraService(config)
