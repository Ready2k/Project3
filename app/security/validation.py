"""Input validation and sanitization utilities."""

import re
import html
from typing import Any, Dict, List, Optional, Union
from pydantic import BaseModel, validator
from app.utils.logger import app_logger
from app.utils.redact import PIIRedactor


class SecurityValidator:
    """Validates and sanitizes input for security."""
    
    def __init__(self):
        self.pii_redactor = PIIRedactor()
        
        # Patterns for detecting potentially malicious input
        self.malicious_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),  # XSS
            re.compile(r'javascript:', re.IGNORECASE),  # JavaScript URLs
            re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
            re.compile(r'(union|select|insert|update|delete|drop|create|alter)\s+', re.IGNORECASE),  # SQL injection
            re.compile(r'(\.\./|\.\.\\)', re.IGNORECASE),  # Path traversal
            re.compile(r'(eval|exec|system|shell_exec)\s*\(', re.IGNORECASE),  # Code injection
        ]
        
        # Banned tools/technologies that should never appear in outputs
        self.banned_tools = [
            "metasploit", "burp suite", "sqlmap", "nmap", "masscan", "wireshark",
            "john the ripper", "hashcat", "aircrack", "hydra", "nikto",
            "owasp zap", "beef framework", "maltego", "shodan", "censys"
        ]
    
    def sanitize_string(self, text: str, max_length: int = 10000) -> str:
        """Sanitize string input by removing/escaping dangerous content."""
        if not isinstance(text, str):
            return str(text)
        
        # Truncate if too long
        if len(text) > max_length:
            app_logger.warning(f"Input truncated from {len(text)} to {max_length} characters")
            text = text[:max_length]
        
        # HTML escape to prevent XSS
        text = html.escape(text)
        
        # Remove null bytes and control characters
        text = re.sub(r'[\x00-\x08\x0B\x0C\x0E-\x1F\x7F]', '', text)
        
        # Check for malicious patterns
        for pattern in self.malicious_patterns:
            if pattern.search(text):
                app_logger.warning(f"Potentially malicious pattern detected and removed: {pattern.pattern}")
                text = pattern.sub('[REMOVED_SUSPICIOUS_CONTENT]', text)
        
        return text
    
    def validate_no_banned_tools(self, text: str) -> bool:
        """Check if text contains any banned tools/technologies."""
        text_lower = text.lower()
        found_banned = []
        
        for tool in self.banned_tools:
            # Use word boundaries for better matching, except for multi-word tools
            if " " in tool:
                # Multi-word tools - exact phrase match
                if tool.lower() in text_lower:
                    found_banned.append(tool)
            else:
                # Single word tools - use word boundaries to avoid partial matches
                import re
                pattern = r'\b' + re.escape(tool.lower()) + r'\b'
                if re.search(pattern, text_lower):
                    found_banned.append(tool)
        
        if found_banned:
            app_logger.error(f"Banned tools detected in output: {found_banned}")
            return False
        
        return True
    
    def sanitize_dict(self, data: Dict[str, Any], max_depth: int = 10) -> Dict[str, Any]:
        """Recursively sanitize dictionary values."""
        if max_depth <= 0:
            app_logger.warning("Maximum recursion depth reached during sanitization")
            return {}
        
        sanitized = {}
        for key, value in data.items():
            # Sanitize key
            clean_key = self.sanitize_string(str(key), max_length=100)
            
            # Sanitize value based on type
            if isinstance(value, str):
                sanitized[clean_key] = self.sanitize_string(value)
            elif isinstance(value, dict):
                sanitized[clean_key] = self.sanitize_dict(value, max_depth - 1)
            elif isinstance(value, list):
                sanitized[clean_key] = self.sanitize_list(value, max_depth - 1)
            elif isinstance(value, (int, float, bool)) or value is None:
                sanitized[clean_key] = value
            else:
                # Convert unknown types to string and sanitize
                sanitized[clean_key] = self.sanitize_string(str(value))
        
        return sanitized
    
    def sanitize_list(self, data: List[Any], max_depth: int = 10) -> List[Any]:
        """Recursively sanitize list values."""
        if max_depth <= 0:
            app_logger.warning("Maximum recursion depth reached during list sanitization")
            return []
        
        sanitized = []
        for item in data:
            if isinstance(item, str):
                sanitized.append(self.sanitize_string(item))
            elif isinstance(item, dict):
                sanitized.append(self.sanitize_dict(item, max_depth - 1))
            elif isinstance(item, list):
                sanitized.append(self.sanitize_list(item, max_depth - 1))
            elif isinstance(item, (int, float, bool)) or item is None:
                sanitized.append(item)
            else:
                sanitized.append(self.sanitize_string(str(item)))
        
        return sanitized
    
    def redact_pii_from_logs(self, text: str) -> str:
        """Redact PII from text before logging."""
        return self.pii_redactor.redact(text)


class InputValidator:
    """Validates specific input types for the application."""
    
    def __init__(self):
        self.security_validator = SecurityValidator()
    
    def validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format."""
        if not session_id or not isinstance(session_id, str):
            return False
        
        # Should be a UUID format
        uuid_pattern = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
        return bool(uuid_pattern.match(session_id))
    
    def validate_provider_name(self, provider: str) -> bool:
        """Validate LLM provider name."""
        if not provider or not isinstance(provider, str):
            return False
        allowed_providers = ["openai", "bedrock", "claude", "internal", "fake"]
        return provider.lower() in allowed_providers
    
    def validate_model_name(self, model: str) -> bool:
        """Validate model name format."""
        if not model or not isinstance(model, str):
            return False
        
        # Allow alphanumeric, hyphens, dots, and underscores
        model_pattern = re.compile(r'^[a-zA-Z0-9\-\._]+$')
        return bool(model_pattern.match(model)) and len(model) <= 100
    
    def validate_export_format(self, format_type: str) -> bool:
        """Validate export format."""
        if not format_type or not isinstance(format_type, str):
            return False
        allowed_formats = ["json", "md", "markdown"]
        return format_type.lower() in allowed_formats
    
    def validate_requirements_text(self, text: str) -> tuple[bool, str]:
        """Validate requirements text input."""
        if not text or not isinstance(text, str):
            return False, "Requirements text is required"
        
        # Check length
        if len(text) > 50000:  # 50KB limit
            return False, "Requirements text too long (max 50,000 characters)"
        
        if len(text.strip()) < 10:
            return False, "Requirements text too short (minimum 10 characters)"
        
        # Sanitize and check for malicious content
        sanitized = self.security_validator.sanitize_string(text)
        if sanitized != text:
            app_logger.warning("Requirements text was sanitized due to suspicious content")
        
        return True, "Valid"
    
    def validate_jira_credentials(self, base_url: str, email: str, api_token: str) -> tuple[bool, str]:
        """Validate Jira credentials format."""
        if not all([base_url, email, api_token]):
            return False, "All Jira credentials are required"
        
        # Validate URL format
        url_pattern = re.compile(r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$')
        if not url_pattern.match(base_url):
            return False, "Invalid Jira base URL format"
        
        # Validate email format
        email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
        if not email_pattern.match(email):
            return False, "Invalid email format"
        
        # Validate API token (base64-like format with minimum length)
        if not re.match(r'^[a-zA-Z0-9+/=_-]+$', api_token) or len(api_token) < 10:
            return False, "Invalid API token format"
        
        return True, "Valid"
    
    def validate_api_key(self, api_key: str, provider: str) -> tuple[bool, str]:
        """Validate API key format for different providers."""
        if not api_key or not isinstance(api_key, str):
            return False, "API key is required"
        
        # Remove whitespace
        api_key = api_key.strip()
        
        if provider.lower() == "openai":
            # OpenAI keys start with sk- and are typically 51 characters
            if not api_key.startswith("sk-") or len(api_key) < 20:
                return False, "Invalid OpenAI API key format"
        
        elif provider.lower() == "anthropic":
            # Anthropic keys start with sk-ant- 
            if not api_key.startswith("sk-ant-") or len(api_key) < 20:
                return False, "Invalid Anthropic API key format"
        
        # General validation - should be alphanumeric with some special chars
        if not re.match(r'^[a-zA-Z0-9\-_\.]+$', api_key):
            return False, "API key contains invalid characters"
        
        return True, "Valid"