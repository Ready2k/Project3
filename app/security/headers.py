"""Security headers configuration for FastAPI responses."""

from fastapi import Response
from typing import Dict


class SecurityHeaders:
    """Manages security headers for HTTP responses."""
    
    @staticmethod
    def get_security_headers() -> Dict[str, str]:
        """Get standard security headers."""
        return {
            # Prevent clickjacking
            "X-Frame-Options": "DENY",
            
            # Prevent MIME type sniffing
            "X-Content-Type-Options": "nosniff",
            
            # Enable XSS protection
            "X-XSS-Protection": "1; mode=block",
            
            # Referrer policy
            "Referrer-Policy": "strict-origin-when-cross-origin",
            
            # Content Security Policy
            "Content-Security-Policy": (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' 'unsafe-eval'; "
                "style-src 'self' 'unsafe-inline'; "
                "img-src 'self' data: https:; "
                "font-src 'self' data:; "
                "connect-src 'self'; "
                "frame-ancestors 'none'; "
                "base-uri 'self'; "
                "form-action 'self'"
            ),
            
            # Strict Transport Security (HTTPS only)
            "Strict-Transport-Security": "max-age=31536000; includeSubDomains",
            
            # Permissions Policy (formerly Feature Policy)
            "Permissions-Policy": (
                "geolocation=(), "
                "microphone=(), "
                "camera=(), "
                "payment=(), "
                "usb=(), "
                "magnetometer=(), "
                "gyroscope=(), "
                "speaker=()"
            ),
            
            # Server identification
            "Server": "AAA/1.0"
        }
    
    @staticmethod
    def add_security_headers(response: Response) -> Response:
        """Add security headers to a FastAPI response."""
        headers = SecurityHeaders.get_security_headers()
        
        for header_name, header_value in headers.items():
            response.headers[header_name] = header_value
        
        return response
    
    @staticmethod
    def get_api_response_headers() -> Dict[str, str]:
        """Get headers specific to API responses."""
        base_headers = SecurityHeaders.get_security_headers()
        
        # Add API-specific headers
        api_headers = {
            **base_headers,
            "Cache-Control": "no-cache, no-store, must-revalidate",
            "Pragma": "no-cache",
            "Expires": "0"
        }
        
        return api_headers