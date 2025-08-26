"""SSL certificate handling for Jira Data Center integration."""

import ssl
import socket
import certifi
from pathlib import Path
from typing import Optional, Dict, Any, List, Tuple, Union
from urllib.parse import urlparse

import httpx
from pydantic import BaseModel

from app.utils.logger import app_logger


class SSLCertificateInfo(BaseModel):
    """Information about an SSL certificate."""
    subject: Dict[str, str]
    issuer: Dict[str, str]
    version: int
    serial_number: str
    not_before: str
    not_after: str
    is_expired: bool
    is_self_signed: bool
    signature_algorithm: str
    public_key_algorithm: str
    key_size: Optional[int] = None


class SSLValidationResult(BaseModel):
    """Result of SSL certificate validation."""
    is_valid: bool
    certificate_info: Optional[SSLCertificateInfo] = None
    error_message: Optional[str] = None
    error_type: Optional[str] = None
    troubleshooting_steps: List[str] = []
    suggested_config: Optional[Dict[str, Any]] = None


class SSLHandler:
    """Handles SSL certificate validation and configuration for Jira connections."""
    
    def __init__(self, verify_ssl: bool = True, ca_cert_path: Optional[str] = None):
        """Initialize SSL handler.
        
        Args:
            verify_ssl: Whether to verify SSL certificates
            ca_cert_path: Path to custom CA certificate bundle
        """
        self.verify_ssl = verify_ssl
        self.ca_cert_path = ca_cert_path
        
        # Log SSL configuration and security warnings
        if not verify_ssl:
            app_logger.warning("⚠️  SSL certificate verification is DISABLED")
            app_logger.warning("🔒 This connection is vulnerable to man-in-the-middle attacks")
            app_logger.warning("📋 Only use this setting for testing with self-signed certificates")
            app_logger.warning("🏭 NEVER disable SSL verification in production environments")
        else:
            if ca_cert_path:
                app_logger.info(f"🔐 SSL verification enabled with custom CA certificate: {ca_cert_path}")
            else:
                app_logger.info("🔐 SSL verification enabled with system CA certificates")
        
    def get_ssl_context(self) -> Optional[ssl.SSLContext]:
        """Get SSL context for HTTP requests.
        
        Returns:
            SSL context configured with custom CA if provided, None if SSL disabled
        """
        if not self.verify_ssl:
            return False  # Disable SSL verification
        
        # Create SSL context
        context = ssl.create_default_context()
        
        # Load custom CA certificate if provided
        if self.ca_cert_path:
            ca_path = Path(self.ca_cert_path)
            if ca_path.exists():
                try:
                    context.load_verify_locations(str(ca_path))
                    app_logger.info(f"Loaded custom CA certificate from: {ca_path}")
                except Exception as e:
                    app_logger.error(f"Failed to load custom CA certificate: {e}")
                    raise ValueError(f"Invalid CA certificate file: {e}")
            else:
                raise FileNotFoundError(f"CA certificate file not found: {ca_path}")
        
        return context
    
    def get_httpx_verify_config(self) -> Union[bool, str]:
        """Get verification configuration for httpx client.
        
        Returns:
            Verification configuration for httpx (bool or path to CA bundle)
        """
        if not self.verify_ssl:
            app_logger.warning("🚨 SSL verification DISABLED - returning False for httpx verify config")
            return False
        
        if self.ca_cert_path:
            ca_path = Path(self.ca_cert_path)
            if ca_path.exists():
                app_logger.info(f"🔐 Using custom CA certificate: {ca_path}")
                return str(ca_path)
            else:
                app_logger.error(f"❌ CA certificate file not found: {ca_path}")
                raise FileNotFoundError(f"CA certificate file not found: {ca_path}")
        
        app_logger.info("🔐 Using system default CA bundle for SSL verification")
        return True  # Use default CA bundle
    
    async def validate_ssl_certificate(self, base_url: str) -> SSLValidationResult:
        """Validate SSL certificate for the given URL.
        
        Args:
            base_url: Base URL to validate SSL certificate for
            
        Returns:
            SSL validation result with certificate information and troubleshooting
        """
        try:
            parsed_url = urlparse(base_url)
            if parsed_url.scheme != 'https':
                return SSLValidationResult(
                    is_valid=True,  # No SSL to validate for HTTP
                    error_message="URL uses HTTP, no SSL certificate to validate"
                )
            
            hostname = parsed_url.hostname
            port = parsed_url.port or 443
            
            if not hostname:
                return SSLValidationResult(
                    is_valid=False,
                    error_message="Invalid hostname in URL",
                    error_type="invalid_hostname",
                    troubleshooting_steps=["Check that the base URL is correctly formatted"]
                )
            
            # Get certificate information
            cert_info = await self._get_certificate_info(hostname, port)
            
            if not cert_info:
                return SSLValidationResult(
                    is_valid=False,
                    error_message="Could not retrieve certificate information",
                    error_type="certificate_retrieval_failed",
                    troubleshooting_steps=[
                        "Check network connectivity to the server",
                        "Verify the hostname and port are correct",
                        "Check if firewall is blocking the connection"
                    ]
                )
            
            # Validate certificate with current configuration
            validation_error = await self._validate_certificate_with_config(base_url)
            
            if validation_error:
                return SSLValidationResult(
                    is_valid=False,
                    certificate_info=cert_info,
                    error_message=validation_error["message"],
                    error_type=validation_error["type"],
                    troubleshooting_steps=validation_error["troubleshooting_steps"],
                    suggested_config=validation_error.get("suggested_config")
                )
            
            return SSLValidationResult(
                is_valid=True,
                certificate_info=cert_info
            )
            
        except Exception as e:
            app_logger.error(f"SSL validation failed for {base_url}: {e}")
            return SSLValidationResult(
                is_valid=False,
                error_message=f"SSL validation error: {str(e)}",
                error_type="validation_error",
                troubleshooting_steps=[
                    "Check network connectivity",
                    "Verify SSL configuration",
                    "Check server certificate validity"
                ]
            )
    
    async def _get_certificate_info(self, hostname: str, port: int) -> Optional[SSLCertificateInfo]:
        """Get certificate information from the server.
        
        Args:
            hostname: Server hostname
            port: Server port
            
        Returns:
            Certificate information or None if failed
        """
        try:
            # Create SSL context that doesn't verify certificates for info gathering
            context = ssl.create_default_context()
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
            
            # Connect and get certificate
            with socket.create_connection((hostname, port), timeout=10) as sock:
                with context.wrap_socket(sock, server_hostname=hostname) as ssock:
                    cert = ssock.getpeercert()
                    cert_der = ssock.getpeercert(binary_form=True)
                    
                    if not cert:
                        return None
                    
                    # Parse certificate information
                    subject = dict(cert.get('subject', []))
                    issuer = dict(cert.get('issuer', []))
                    
                    # Check if self-signed
                    is_self_signed = subject.get('commonName') == issuer.get('commonName')
                    
                    # Get additional certificate details
                    import datetime
                    not_before = datetime.datetime.strptime(cert['notBefore'], '%b %d %H:%M:%S %Y %Z')
                    not_after = datetime.datetime.strptime(cert['notAfter'], '%b %d %H:%M:%S %Y %Z')
                    is_expired = datetime.datetime.now() > not_after
                    
                    return SSLCertificateInfo(
                        subject=subject,
                        issuer=issuer,
                        version=cert.get('version', 0),
                        serial_number=str(cert.get('serialNumber', '')),
                        not_before=cert['notBefore'],
                        not_after=cert['notAfter'],
                        is_expired=is_expired,
                        is_self_signed=is_self_signed,
                        signature_algorithm=cert.get('signatureAlgorithm', 'unknown'),
                        public_key_algorithm='unknown',  # Would need additional parsing
                        key_size=None  # Would need additional parsing
                    )
                    
        except Exception as e:
            app_logger.error(f"Failed to get certificate info for {hostname}:{port}: {e}")
            return None
    
    async def _validate_certificate_with_config(self, base_url: str) -> Optional[Dict[str, Any]]:
        """Validate certificate with current SSL configuration.
        
        Args:
            base_url: URL to validate
            
        Returns:
            Error information if validation fails, None if successful
        """
        try:
            verify_config = self.get_httpx_verify_config()
            
            async with httpx.AsyncClient(verify=verify_config, timeout=10) as client:
                response = await client.get(base_url, follow_redirects=True)
                return None  # Success
                
        except httpx.ConnectError as e:
            error_msg = str(e)
            if "certificate verify failed" in error_msg.lower():
                return {
                    "message": "SSL certificate verification failed - The server's SSL certificate could not be verified",
                    "type": "certificate_verification_failed",
                    "troubleshooting_steps": [
                        "🔍 Check if the certificate is valid and not expired",
                        "🔗 Verify the certificate chain is complete on the server",
                        "📋 For self-signed certificates: Export the certificate and set ca_cert_path",
                        "🏢 For internal CA: Add your organization's CA certificate to ca_cert_path",
                        "⚠️  QUICK FIX (Testing Only): Uncheck 'Verify SSL Certificates' in Jira configuration",
                        "🔧 Alternative: Set environment variable JIRA_VERIFY_SSL=false",
                        "⚠️  Security Warning: Disabling SSL verification makes connections vulnerable to attacks"
                    ],
                    "suggested_config": {
                        "verify_ssl": False,
                        "note": "⚠️  TESTING ONLY - Disables SSL verification. NEVER use in production environments!"
                    }
                }
            elif "name mismatch" in error_msg.lower() or "hostname" in error_msg.lower():
                return {
                    "message": "SSL certificate hostname mismatch - The certificate doesn't match the server hostname",
                    "type": "hostname_mismatch",
                    "troubleshooting_steps": [
                        "🌐 Verify the base URL hostname exactly matches the certificate Common Name",
                        "🔢 Avoid using IP addresses - use the proper hostname instead",
                        "📋 Check if the certificate includes Subject Alternative Names (SAN) for your hostname",
                        "🔍 Use browser developer tools to inspect the certificate details",
                        "🏢 Contact your system administrator to update the certificate with correct hostnames"
                    ]
                }
            elif "self signed certificate" in error_msg.lower():
                return {
                    "message": "Self-signed certificate detected - The server uses a self-signed SSL certificate",
                    "type": "self_signed_certificate",
                    "troubleshooting_steps": [
                        "📥 Export the self-signed certificate from your browser (click the lock icon → Certificate)",
                        "💾 Save the certificate as a .pem or .crt file on your system",
                        "📂 Set 'Custom CA Certificate Path' to point to the saved certificate file",
                        "🔄 Test the connection again with the certificate path configured",
                        "⚠️  QUICK FIX (Testing Only): Uncheck 'Verify SSL Certificates' in configuration",
                        "🔧 Alternative: Set environment variable JIRA_VERIFY_SSL=false",
                        "⚠️  Security Warning: Self-signed certificates should only be used in development/testing"
                    ],
                    "suggested_config": {
                        "ca_cert_path": "/path/to/your/self-signed-certificate.pem",
                        "verify_ssl": False,
                        "note": "💡 Recommended: Add certificate path. Alternative: Disable SSL verification for testing only"
                    }
                }
            else:
                return {
                    "message": f"SSL connection error: {error_msg}",
                    "type": "ssl_connection_error",
                    "troubleshooting_steps": [
                        "🌐 Check network connectivity to the server",
                        "🔧 Verify SSL/TLS configuration on the server",
                        "🛡️  Check if firewall is blocking SSL traffic (port 443)",
                        "🔍 Test the URL in a web browser to see if it loads",
                        "📞 Contact your system administrator for server-side SSL issues",
                        "⚠️  Temporary workaround: Disable SSL verification for testing only"
                    ]
                }
        except Exception as e:
            return {
                "message": f"Unexpected SSL validation error: {str(e)}",
                "type": "unexpected_ssl_error",
                "troubleshooting_steps": [
                    "Check network connectivity",
                    "Verify server is accessible",
                    "Check SSL configuration"
                ]
            }
    
    def get_ssl_troubleshooting_steps(self, error_type: str) -> List[str]:
        """Get troubleshooting steps for specific SSL error types.
        
        Args:
            error_type: Type of SSL error
            
        Returns:
            List of troubleshooting steps
        """
        troubleshooting_steps = {
            "certificate_verification_failed": [
                "Verify the SSL certificate is valid and not expired",
                "Check that the certificate chain is complete",
                "For Data Center with custom CA: Set ca_cert_path to your CA certificate",
                "For self-signed certificates: Add the certificate to ca_cert_path",
                "Ensure the server's intermediate certificates are properly configured"
            ],
            "hostname_mismatch": [
                "Verify the base URL hostname exactly matches the certificate Common Name",
                "Check if the certificate includes Subject Alternative Names (SAN) for your hostname",
                "Avoid using IP addresses - use the proper hostname instead",
                "Ensure DNS resolution is working correctly"
            ],
            "self_signed_certificate": [
                "Export the self-signed certificate from your browser or server",
                "Save the certificate as a .pem or .crt file",
                "Set ca_cert_path in configuration to point to the certificate file",
                "For testing environments only: Set verify_ssl=False (not recommended for production)"
            ],
            "certificate_expired": [
                "Renew the SSL certificate on the Jira server",
                "Check the certificate expiration date",
                "Ensure system clock is synchronized",
                "Contact your system administrator to update the certificate"
            ],
            "ca_not_found": [
                "Verify the ca_cert_path points to a valid certificate file",
                "Check file permissions - ensure the application can read the certificate",
                "Ensure the certificate is in PEM format",
                "Verify the certificate contains the correct CA certificate"
            ]
        }
        
        return troubleshooting_steps.get(error_type, [
            "Check SSL certificate configuration",
            "Verify network connectivity",
            "Contact your system administrator for SSL issues"
        ])
    
    def suggest_ssl_config_for_error(self, error_type: str, base_url: str) -> Dict[str, Any]:
        """Suggest SSL configuration changes for specific error types.
        
        Args:
            error_type: Type of SSL error
            base_url: Base URL that failed
            
        Returns:
            Suggested configuration changes
        """
        suggestions = {}
        
        if error_type == "self_signed_certificate":
            suggestions = {
                "ca_cert_path": "/path/to/your/self-signed-certificate.pem",
                "verify_ssl": True,
                "note": "Replace the path with your actual certificate file location"
            }
        elif error_type == "certificate_verification_failed":
            suggestions = {
                "ca_cert_path": "/path/to/your/ca-bundle.pem",
                "verify_ssl": True,
                "note": "Add your organization's CA certificate bundle"
            }
        elif error_type in ["hostname_mismatch", "certificate_expired"]:
            suggestions = {
                "note": "SSL configuration cannot fix this issue - the server certificate needs to be updated"
            }
        elif error_type == "ca_not_found":
            suggestions = {
                "ca_cert_path": None,
                "verify_ssl": True,
                "note": "Remove invalid ca_cert_path to use system default CA bundle"
            }
        
        # Add testing-only option for non-production environments
        if "localhost" in base_url or "127.0.0.1" in base_url:
            suggestions["testing_only"] = {
                "verify_ssl": False,
                "note": "For localhost testing only - never use in production"
            }
        
        return suggestions
    
    @staticmethod
    def validate_ca_certificate_file(ca_cert_path: str) -> Tuple[bool, Optional[str]]:
        """Validate that a CA certificate file is valid.
        
        Args:
            ca_cert_path: Path to CA certificate file
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        try:
            ca_path = Path(ca_cert_path)
            
            if not ca_path.exists():
                return False, f"Certificate file does not exist: {ca_path}"
            
            if not ca_path.is_file():
                return False, f"Path is not a file: {ca_path}"
            
            # Try to load the certificate
            try:
                with open(ca_path, 'r') as f:
                    content = f.read()
                
                # Basic validation - check for PEM format
                if not content.strip().startswith('-----BEGIN CERTIFICATE-----'):
                    return False, "Certificate file does not appear to be in PEM format"
                
                if not content.strip().endswith('-----END CERTIFICATE-----'):
                    return False, "Certificate file appears to be incomplete or corrupted"
                
                # Try to create SSL context with the certificate
                context = ssl.create_default_context()
                context.load_verify_locations(str(ca_path))
                
                return True, None
                
            except ssl.SSLError as e:
                return False, f"Invalid SSL certificate: {e}"
            except Exception as e:
                return False, f"Error reading certificate file: {e}"
                
        except Exception as e:
            return False, f"Error validating certificate file: {e}"
    
    def get_ssl_security_warnings(self) -> List[str]:
        """Get security warnings related to current SSL configuration.
        
        Returns:
            List of security warning messages
        """
        warnings = []
        
        if not self.verify_ssl:
            warnings.extend([
                "⚠️  SSL certificate verification is DISABLED",
                "🔒 Your connection is vulnerable to man-in-the-middle attacks",
                "🏭 NEVER use this setting in production environments",
                "📋 Only disable SSL verification for testing with self-signed certificates",
                "💡 Recommended: Add the server's certificate to 'Custom CA Certificate Path' instead"
            ])
        
        if self.ca_cert_path:
            ca_path = Path(self.ca_cert_path)
            if not ca_path.exists():
                warnings.append(f"⚠️  Custom CA certificate file not found: {self.ca_cert_path}")
            elif not ca_path.is_file():
                warnings.append(f"⚠️  Custom CA certificate path is not a file: {self.ca_cert_path}")
        
        return warnings
    
    def get_ssl_configuration_info(self) -> Dict[str, Any]:
        """Get information about current SSL configuration.
        
        Returns:
            Dictionary with SSL configuration details
        """
        info = {
            "ssl_verification_enabled": self.verify_ssl,
            "custom_ca_certificate": self.ca_cert_path is not None,
            "ca_certificate_path": self.ca_cert_path,
            "security_level": "HIGH" if self.verify_ssl else "LOW",
            "warnings": self.get_ssl_security_warnings()
        }
        
        if self.ca_cert_path:
            ca_path = Path(self.ca_cert_path)
            info["ca_certificate_exists"] = ca_path.exists()
            info["ca_certificate_readable"] = ca_path.exists() and ca_path.is_file()
        
        return info
    
    @staticmethod
    def get_system_ca_bundle_path() -> str:
        """Get the path to the system CA bundle.
        
        Returns:
            Path to system CA bundle
        """
        return certifi.where()