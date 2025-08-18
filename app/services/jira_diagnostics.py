"""
Diagnostic and validation utilities for Jira Data Center integration.

This module provides comprehensive diagnostic tools for troubleshooting
Jira connectivity, configuration, and compatibility issues.
"""

import asyncio
import socket
import ssl
import time
from enum import Enum
from typing import Dict, List, Optional, Any, Tuple
from urllib.parse import urlparse
from pydantic import BaseModel
import httpx
from loguru import logger as app_logger

from app.config import JiraConfig, JiraDeploymentType, JiraAuthType
from app.services.jira_error_handler import JiraErrorHandler, JiraErrorDetail, create_jira_error_handler


class DiagnosticStatus(str, Enum):
    """Status of diagnostic checks."""
    PASS = "pass"
    FAIL = "fail"
    WARNING = "warning"
    SKIP = "skip"


class DiagnosticResult(BaseModel):
    """Result of a single diagnostic check."""
    name: str
    status: DiagnosticStatus
    message: str
    details: Optional[str] = None
    duration_ms: Optional[float] = None
    suggestions: List[str] = []
    technical_info: Optional[Dict[str, Any]] = None


class NetworkConnectivityResult(BaseModel):
    """Result of network connectivity diagnostics."""
    hostname: str
    port: int
    is_reachable: bool
    response_time_ms: Optional[float] = None
    error_message: Optional[str] = None
    ssl_info: Optional[Dict[str, Any]] = None


class ConfigurationValidationResult(BaseModel):
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = []
    warnings: List[str] = []
    suggestions: List[str] = []
    validated_config: Optional[Dict[str, Any]] = None


class VersionCompatibilityResult(BaseModel):
    """Result of version compatibility check."""
    jira_version: Optional[str] = None
    is_compatible: bool = False
    minimum_version: str = "8.0.0"
    recommended_version: str = "9.12.22"
    compatibility_notes: List[str] = []
    feature_support: Dict[str, bool] = {}


class AuthMethodAvailabilityResult(BaseModel):
    """Result of authentication method availability check."""
    available_methods: List[JiraAuthType] = []
    recommended_method: Optional[JiraAuthType] = None
    method_details: Dict[JiraAuthType, Dict[str, Any]] = {}
    sso_available: bool = False
    pat_supported: bool = False


class JiraDiagnostics:
    """Comprehensive diagnostic utilities for Jira integration."""
    
    def __init__(self, config: JiraConfig):
        self.config = config
        self.error_handler = create_jira_error_handler(config.deployment_type)
        self.timeout = config.timeout
        
    async def run_full_diagnostics(self) -> List[DiagnosticResult]:
        """Run all diagnostic checks and return comprehensive results."""
        results = []
        
        app_logger.info("Starting comprehensive Jira diagnostics")
        
        # Configuration validation
        config_result = await self._run_diagnostic_check(
            "Configuration Validation",
            self._validate_configuration
        )
        results.append(config_result)
        
        # Network connectivity
        network_result = await self._run_diagnostic_check(
            "Network Connectivity",
            self._check_network_connectivity
        )
        results.append(network_result)
        
        # SSL/TLS validation
        if self.config.base_url and self.config.base_url.startswith('https://'):
            ssl_result = await self._run_diagnostic_check(
                "SSL/TLS Certificate",
                self._check_ssl_certificate
            )
            results.append(ssl_result)
        
        # DNS resolution
        dns_result = await self._run_diagnostic_check(
            "DNS Resolution",
            self._check_dns_resolution
        )
        results.append(dns_result)
        
        # Proxy configuration (if configured)
        if self.config.proxy_url:
            proxy_result = await self._run_diagnostic_check(
                "Proxy Configuration",
                self._check_proxy_configuration
            )
            results.append(proxy_result)
        
        # Jira version compatibility (if reachable)
        if network_result.status == DiagnosticStatus.PASS:
            version_result = await self._run_diagnostic_check(
                "Version Compatibility",
                self._check_version_compatibility
            )
            results.append(version_result)
            
            # Authentication method availability
            auth_result = await self._run_diagnostic_check(
                "Authentication Methods",
                self._check_auth_method_availability
            )
            results.append(auth_result)
        
        app_logger.info(f"Diagnostics completed: {len(results)} checks performed")
        return results
    
    async def _run_diagnostic_check(self, name: str, check_func) -> DiagnosticResult:
        """Run a single diagnostic check with timing and error handling."""
        start_time = time.time()
        
        try:
            result = await check_func()
            duration_ms = (time.time() - start_time) * 1000
            
            if isinstance(result, DiagnosticResult):
                result.duration_ms = duration_ms
                return result
            else:
                # Handle simple boolean results
                status = DiagnosticStatus.PASS if result else DiagnosticStatus.FAIL
                return DiagnosticResult(
                    name=name,
                    status=status,
                    message="Check completed" if result else "Check failed",
                    duration_ms=duration_ms
                )
                
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            app_logger.error(f"Diagnostic check '{name}' failed: {e}")
            
            error_detail = self.error_handler.create_error_detail(
                error_message=str(e),
                exception=e,
                technical_details=f"Diagnostic check: {name}"
            )
            
            return DiagnosticResult(
                name=name,
                status=DiagnosticStatus.FAIL,
                message=f"Check failed: {str(e)}",
                duration_ms=duration_ms,
                suggestions=error_detail.troubleshooting_steps[:3]  # Limit suggestions
            )
    
    async def _validate_configuration(self) -> DiagnosticResult:
        """Validate Jira configuration for completeness and correctness."""
        errors = []
        warnings = []
        suggestions = []
        
        # Validate base URL
        if not self.config.base_url:
            errors.append("Base URL is required")
        else:
            try:
                parsed = urlparse(self.config.base_url)
                if not parsed.scheme:
                    errors.append("Base URL must include scheme (http:// or https://)")
                elif parsed.scheme not in ['http', 'https']:
                    errors.append("Base URL scheme must be http or https")
                
                if not parsed.hostname:
                    errors.append("Base URL must include hostname")
                
                # Check for common Data Center patterns
                if self.config.deployment_type == JiraDeploymentType.DATA_CENTER:
                    if parsed.port and parsed.port not in [80, 443, 8080, 8443]:
                        warnings.append(f"Unusual port {parsed.port} for Data Center deployment")
                    
                    if parsed.path and parsed.path != '/':
                        suggestions.append(f"Context path detected: {parsed.path}")
                        
            except Exception as e:
                errors.append(f"Invalid base URL format: {e}")
        
        # Validate authentication configuration
        auth_errors = self._validate_auth_config()
        errors.extend(auth_errors)
        
        # Validate network configuration
        if self.config.timeout <= 0:
            errors.append("Timeout must be positive")
        elif self.config.timeout < 10:
            warnings.append("Timeout is very low, may cause connection issues")
        
        if self.config.proxy_url:
            try:
                proxy_parsed = urlparse(self.config.proxy_url)
                if not proxy_parsed.hostname:
                    errors.append("Proxy URL must include hostname")
                if not proxy_parsed.port:
                    warnings.append("Proxy URL should include port")
            except Exception as e:
                errors.append(f"Invalid proxy URL: {e}")
        
        # Determine overall status
        if errors:
            status = DiagnosticStatus.FAIL
            message = f"Configuration has {len(errors)} error(s)"
        elif warnings:
            status = DiagnosticStatus.WARNING
            message = f"Configuration has {len(warnings)} warning(s)"
        else:
            status = DiagnosticStatus.PASS
            message = "Configuration is valid"
        
        return DiagnosticResult(
            name="Configuration Validation",
            status=status,
            message=message,
            details=f"Errors: {len(errors)}, Warnings: {len(warnings)}",
            suggestions=suggestions,
            technical_info={
                "errors": errors,
                "warnings": warnings,
                "config_summary": {
                    "base_url": self.config.base_url,
                    "auth_type": self.config.auth_type.value if self.config.auth_type else None,
                    "deployment_type": self.config.deployment_type.value if self.config.deployment_type else None,
                    "ssl_verification": self.config.verify_ssl,
                    "proxy_configured": bool(self.config.proxy_url)
                }
            }
        )
    
    def _validate_auth_config(self) -> List[str]:
        """Validate authentication configuration."""
        errors = []
        
        if not self.config.auth_type:
            errors.append("Authentication type is required")
            return errors
        
        if self.config.auth_type == JiraAuthType.API_TOKEN:
            if not self.config.email:
                errors.append("Email is required for API token authentication")
            if not self.config.api_token:
                errors.append("API token is required for API token authentication")
                
        elif self.config.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN:
            if not self.config.personal_access_token:
                errors.append("Personal Access Token is required for PAT authentication")
                
        elif self.config.auth_type == JiraAuthType.BASIC:
            if not self.config.username:
                errors.append("Username is required for basic authentication")
            if not self.config.password:
                errors.append("Password is required for basic authentication")
        
        return errors
    
    async def _check_network_connectivity(self) -> DiagnosticResult:
        """Check basic network connectivity to Jira server."""
        if not self.config.base_url:
            return DiagnosticResult(
                name="Network Connectivity",
                status=DiagnosticStatus.SKIP,
                message="Skipped - no base URL configured"
            )
        
        try:
            parsed = urlparse(self.config.base_url)
            hostname = parsed.hostname
            port = parsed.port or (443 if parsed.scheme == 'https' else 80)
            
            # Test TCP connectivity
            start_time = time.time()
            
            try:
                # Create socket with timeout
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                
                result = sock.connect_ex((hostname, port))
                response_time = (time.time() - start_time) * 1000
                
                sock.close()
                
                if result == 0:
                    return DiagnosticResult(
                        name="Network Connectivity",
                        status=DiagnosticStatus.PASS,
                        message=f"Successfully connected to {hostname}:{port}",
                        details=f"Response time: {response_time:.1f}ms",
                        technical_info={
                            "hostname": hostname,
                            "port": port,
                            "response_time_ms": response_time
                        }
                    )
                else:
                    error_detail = self.error_handler.create_error_detail(
                        error_message=f"Cannot connect to {hostname}:{port}",
                        technical_details=f"Socket error code: {result}"
                    )
                    
                    return DiagnosticResult(
                        name="Network Connectivity",
                        status=DiagnosticStatus.FAIL,
                        message=f"Cannot connect to {hostname}:{port}",
                        details=f"Connection refused (error {result})",
                        suggestions=error_detail.troubleshooting_steps[:3]
                    )
                    
            except socket.timeout:
                error_detail = self.error_handler.create_error_detail(
                    error_message=f"Connection timeout to {hostname}:{port}",
                    technical_details=f"Timeout after {self.timeout} seconds"
                )
                
                return DiagnosticResult(
                    name="Network Connectivity",
                    status=DiagnosticStatus.FAIL,
                    message=f"Connection timeout to {hostname}:{port}",
                    details=f"Timeout after {self.timeout} seconds",
                    suggestions=error_detail.troubleshooting_steps[:3]
                )
                
        except Exception as e:
            error_detail = self.error_handler.create_error_detail(
                error_message=f"Network connectivity check failed: {str(e)}",
                exception=e
            )
            
            return DiagnosticResult(
                name="Network Connectivity",
                status=DiagnosticStatus.FAIL,
                message=f"Network check failed: {str(e)}",
                suggestions=error_detail.troubleshooting_steps[:3]
            )
    
    async def _check_ssl_certificate(self) -> DiagnosticResult:
        """Check SSL certificate validity and configuration."""
        if not self.config.base_url or not self.config.base_url.startswith('https://'):
            return DiagnosticResult(
                name="SSL/TLS Certificate",
                status=DiagnosticStatus.SKIP,
                message="Skipped - not using HTTPS"
            )
        
        try:
            parsed = urlparse(self.config.base_url)
            hostname = parsed.hostname
            port = parsed.port or 443
            
            # Create SSL context
            context = ssl.create_default_context()
            if not self.config.verify_ssl:
                context.check_hostname = False
                context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate info
            with socket.create_connection((hostname, port), timeout=self.timeout) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cipher = ssock.cipher()
                    
                    # Extract certificate information
                    cert_info = {
                        "subject": dict(x[0] for x in cert.get('subject', [])),
                        "issuer": dict(x[0] for x in cert.get('issuer', [])),
                        "version": cert.get('version'),
                        "serial_number": cert.get('serialNumber'),
                        "not_before": cert.get('notBefore'),
                        "not_after": cert.get('notAfter'),
                        "cipher": cipher
                    }
                    
                    # Check certificate validity
                    warnings = []
                    if not self.config.verify_ssl:
                        warnings.append("SSL verification is disabled")
                    
                    # Check if certificate is self-signed
                    subject = cert_info.get("subject", {})
                    issuer = cert_info.get("issuer", {})
                    if subject.get("commonName") == issuer.get("commonName"):
                        warnings.append("Certificate appears to be self-signed")
                    
                    status = DiagnosticStatus.WARNING if warnings else DiagnosticStatus.PASS
                    message = "SSL certificate is valid"
                    if warnings:
                        message += f" (with {len(warnings)} warning(s))"
                    
                    return DiagnosticResult(
                        name="SSL/TLS Certificate",
                        status=status,
                        message=message,
                        details=f"Issued by: {issuer.get('organizationName', 'Unknown')}",
                        suggestions=["Consider using proper CA-signed certificates for production"] if warnings else [],
                        technical_info=cert_info
                    )
                    
        except ssl.SSLError as e:
            error_detail = self.error_handler.create_error_detail(
                error_message=f"SSL certificate error: {str(e)}",
                exception=e
            )
            
            return DiagnosticResult(
                name="SSL/TLS Certificate",
                status=DiagnosticStatus.FAIL,
                message=f"SSL certificate error: {str(e)}",
                suggestions=error_detail.troubleshooting_steps[:3]
            )
            
        except Exception as e:
            return DiagnosticResult(
                name="SSL/TLS Certificate",
                status=DiagnosticStatus.FAIL,
                message=f"SSL check failed: {str(e)}",
                suggestions=["Check SSL configuration", "Verify certificate is valid"]
            )
    
    async def _check_dns_resolution(self) -> DiagnosticResult:
        """Check DNS resolution for the Jira hostname."""
        if not self.config.base_url:
            return DiagnosticResult(
                name="DNS Resolution",
                status=DiagnosticStatus.SKIP,
                message="Skipped - no base URL configured"
            )
        
        try:
            parsed = urlparse(self.config.base_url)
            hostname = parsed.hostname
            
            if not hostname:
                return DiagnosticResult(
                    name="DNS Resolution",
                    status=DiagnosticStatus.FAIL,
                    message="No hostname found in base URL"
                )
            
            # Resolve hostname
            start_time = time.time()
            addresses = socket.getaddrinfo(hostname, None)
            resolution_time = (time.time() - start_time) * 1000
            
            # Extract unique IP addresses
            ips = list(set(addr[4][0] for addr in addresses))
            
            return DiagnosticResult(
                name="DNS Resolution",
                status=DiagnosticStatus.PASS,
                message=f"Successfully resolved {hostname}",
                details=f"Resolved to {len(ips)} address(es) in {resolution_time:.1f}ms",
                technical_info={
                    "hostname": hostname,
                    "addresses": ips,
                    "resolution_time_ms": resolution_time
                }
            )
            
        except socket.gaierror as e:
            error_detail = self.error_handler.create_error_detail(
                error_message=f"DNS resolution failed: {str(e)}",
                exception=e
            )
            
            return DiagnosticResult(
                name="DNS Resolution",
                status=DiagnosticStatus.FAIL,
                message=f"DNS resolution failed: {str(e)}",
                suggestions=error_detail.troubleshooting_steps[:3]
            )
            
        except Exception as e:
            return DiagnosticResult(
                name="DNS Resolution",
                status=DiagnosticStatus.FAIL,
                message=f"DNS check failed: {str(e)}",
                suggestions=["Check network connectivity", "Verify hostname is correct"]
            )
    
    async def _check_proxy_configuration(self) -> DiagnosticResult:
        """Check proxy configuration and connectivity."""
        if not self.config.proxy_url:
            return DiagnosticResult(
                name="Proxy Configuration",
                status=DiagnosticStatus.SKIP,
                message="Skipped - no proxy configured"
            )
        
        try:
            # Basic proxy URL validation
            parsed = urlparse(self.config.proxy_url)
            if not parsed.hostname or not parsed.port:
                return DiagnosticResult(
                    name="Proxy Configuration",
                    status=DiagnosticStatus.FAIL,
                    message="Invalid proxy URL format",
                    suggestions=["Use format: http://[username:password@]host:port"]
                )
            
            # Test proxy connectivity
            try:
                start_time = time.time()
                sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                sock.settimeout(self.timeout)
                
                result = sock.connect_ex((parsed.hostname, parsed.port))
                response_time = (time.time() - start_time) * 1000
                
                sock.close()
                
                if result == 0:
                    return DiagnosticResult(
                        name="Proxy Configuration",
                        status=DiagnosticStatus.PASS,
                        message=f"Proxy is reachable at {parsed.hostname}:{parsed.port}",
                        details=f"Response time: {response_time:.1f}ms",
                        technical_info={
                            "proxy_host": parsed.hostname,
                            "proxy_port": parsed.port,
                            "response_time_ms": response_time
                        }
                    )
                else:
                    return DiagnosticResult(
                        name="Proxy Configuration",
                        status=DiagnosticStatus.FAIL,
                        message=f"Cannot connect to proxy {parsed.hostname}:{parsed.port}",
                        suggestions=[
                            "Verify proxy server is running",
                            "Check proxy hostname and port",
                            "Verify network connectivity to proxy"
                        ]
                    )
                    
            except socket.timeout:
                return DiagnosticResult(
                    name="Proxy Configuration",
                    status=DiagnosticStatus.FAIL,
                    message=f"Proxy connection timeout",
                    suggestions=[
                        "Increase timeout value",
                        "Check proxy server availability",
                        "Verify network connectivity"
                    ]
                )
                
        except Exception as e:
            return DiagnosticResult(
                name="Proxy Configuration",
                status=DiagnosticStatus.FAIL,
                message=f"Proxy check failed: {str(e)}",
                suggestions=["Check proxy configuration", "Verify proxy URL format"]
            )
    
    async def _check_version_compatibility(self) -> DiagnosticResult:
        """Check Jira version compatibility."""
        try:
            # Try to get version information via HTTP
            client_config = {
                "verify": self.config.verify_ssl,
                "timeout": self.timeout
            }
            
            if self.config.proxy_url:
                client_config["proxies"] = self.config.proxy_url
            
            async with httpx.AsyncClient(**client_config) as client:
                # Try serverInfo endpoint (usually accessible without auth)
                url = f"{self.config.base_url.rstrip('/')}/rest/api/2/serverInfo"
                
                try:
                    response = await client.get(url)
                    if response.status_code == 200:
                        data = response.json()
                        version = data.get("version", "Unknown")
                        build_number = data.get("buildNumber", "Unknown")
                        deployment_type = data.get("deploymentType", "Unknown")
                        
                        # Check compatibility
                        is_compatible = self._is_version_compatible(version)
                        
                        # Determine feature support
                        feature_support = self._get_feature_support(version)
                        
                        status = DiagnosticStatus.PASS if is_compatible else DiagnosticStatus.FAIL
                        message = f"Jira {version} detected"
                        if not is_compatible:
                            message += " (incompatible)"
                        
                        suggestions = []
                        if not is_compatible:
                            suggestions.extend([
                                f"Minimum supported version is 8.0.0",
                                f"Current version {version} may not work properly",
                                "Consider upgrading Jira Data Center"
                            ])
                        
                        return DiagnosticResult(
                            name="Version Compatibility",
                            status=status,
                            message=message,
                            details=f"Build: {build_number}, Type: {deployment_type}",
                            suggestions=suggestions,
                            technical_info={
                                "version": version,
                                "build_number": build_number,
                                "deployment_type": deployment_type,
                                "is_compatible": is_compatible,
                                "feature_support": feature_support
                            }
                        )
                        
                except httpx.HTTPStatusError as e:
                    if e.response.status_code == 401:
                        return DiagnosticResult(
                            name="Version Compatibility",
                            status=DiagnosticStatus.WARNING,
                            message="Version check requires authentication",
                            details="ServerInfo endpoint requires authentication",
                            suggestions=["Version will be checked during connection test"]
                        )
                    else:
                        raise e
                        
        except Exception as e:
            return DiagnosticResult(
                name="Version Compatibility",
                status=DiagnosticStatus.WARNING,
                message=f"Could not check version: {str(e)}",
                details="Version will be checked during connection test",
                suggestions=["Ensure Jira server is accessible"]
            )
    
    def _is_version_compatible(self, version: str) -> bool:
        """Check if Jira version is compatible."""
        try:
            # Parse version string (e.g., "9.12.22" -> [9, 12, 22])
            version_parts = [int(x) for x in version.split('.')]
            
            # Minimum version is 8.0.0
            min_version = [8, 0, 0]
            
            # Compare version parts
            for i, (current, minimum) in enumerate(zip(version_parts, min_version)):
                if current > minimum:
                    return True
                elif current < minimum:
                    return False
            
            # If all compared parts are equal, check if we have enough parts
            return len(version_parts) >= len(min_version)
            
        except Exception:
            # If we can't parse the version, assume it's compatible
            return True
    
    def _get_feature_support(self, version: str) -> Dict[str, bool]:
        """Get feature support based on Jira version."""
        try:
            version_parts = [int(x) for x in version.split('.')]
            major = version_parts[0] if version_parts else 0
            minor = version_parts[1] if len(version_parts) > 1 else 0
            
            return {
                "rest_api_v3": major >= 8,
                "personal_access_tokens": major > 8 or (major == 8 and minor >= 14),
                "modern_authentication": major >= 8,
                "advanced_search": major >= 7,
                "webhooks": major >= 7,
                "agile_rest_api": major >= 7
            }
            
        except Exception:
            # Default feature support for unknown versions
            return {
                "rest_api_v3": True,
                "personal_access_tokens": True,
                "modern_authentication": True,
                "advanced_search": True,
                "webhooks": True,
                "agile_rest_api": True
            }
    
    async def _check_auth_method_availability(self) -> DiagnosticResult:
        """Check which authentication methods are available."""
        available_methods = []
        method_details = {}
        
        # Always available methods
        available_methods.append(JiraAuthType.BASIC)
        method_details[JiraAuthType.BASIC] = {
            "description": "Username and password authentication",
            "recommended": False,
            "notes": "Fallback method, less secure"
        }
        
        # API Token (Cloud and some Data Center versions)
        if self.config.deployment_type != JiraDeploymentType.DATA_CENTER:
            available_methods.append(JiraAuthType.API_TOKEN)
            method_details[JiraAuthType.API_TOKEN] = {
                "description": "Email and API token authentication",
                "recommended": True,
                "notes": "Recommended for Jira Cloud"
            }
        
        # Personal Access Token (Data Center 8.14+)
        if self.config.deployment_type == JiraDeploymentType.DATA_CENTER:
            available_methods.append(JiraAuthType.PERSONAL_ACCESS_TOKEN)
            method_details[JiraAuthType.PERSONAL_ACCESS_TOKEN] = {
                "description": "Personal Access Token authentication",
                "recommended": True,
                "notes": "Recommended for Data Center 8.14+"
            }
        
        # SSO (if configured)
        sso_available = await self._check_sso_availability()
        if sso_available:
            available_methods.append(JiraAuthType.SSO)
            method_details[JiraAuthType.SSO] = {
                "description": "Single Sign-On authentication",
                "recommended": True,
                "notes": "Uses current session credentials"
            }
        
        # Determine recommended method
        recommended_method = None
        if JiraAuthType.SSO in available_methods:
            recommended_method = JiraAuthType.SSO
        elif JiraAuthType.PERSONAL_ACCESS_TOKEN in available_methods:
            recommended_method = JiraAuthType.PERSONAL_ACCESS_TOKEN
        elif JiraAuthType.API_TOKEN in available_methods:
            recommended_method = JiraAuthType.API_TOKEN
        else:
            recommended_method = JiraAuthType.BASIC
        
        return DiagnosticResult(
            name="Authentication Methods",
            status=DiagnosticStatus.PASS,
            message=f"{len(available_methods)} authentication method(s) available",
            details=f"Recommended: {recommended_method.value if recommended_method else 'None'}",
            suggestions=[
                f"Use {recommended_method.value} for best security" if recommended_method else "Configure proper authentication"
            ],
            technical_info={
                "available_methods": [method.value for method in available_methods],
                "recommended_method": recommended_method.value if recommended_method else None,
                "method_details": {method.value: details for method, details in method_details.items()},
                "sso_available": sso_available
            }
        )
    
    async def _check_sso_availability(self) -> bool:
        """Check if SSO authentication is available."""
        # This is a simplified check - in practice, this would involve
        # checking for SSO configuration, session cookies, etc.
        try:
            # For now, assume SSO is available for Data Center deployments
            # In a real implementation, this would check for:
            # - SAML configuration
            # - OAuth configuration
            # - Current session state
            # - SSO provider availability
            
            return self.config.deployment_type == JiraDeploymentType.DATA_CENTER
            
        except Exception:
            return False


def create_jira_diagnostics(config: JiraConfig) -> JiraDiagnostics:
    """Factory function to create a JiraDiagnostics instance."""
    return JiraDiagnostics(config)