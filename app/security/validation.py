"""Input validation and sanitization utilities."""

import re
import html
import asyncio
from typing import Any, Dict, List, Optional, Union, Tuple
from pydantic import BaseModel, validator
from app.utils.logger import app_logger
from app.utils.redact import PIIRedactor


class SecurityValidator:
    """Validates and sanitizes input for security."""
    
    def __init__(self):
        self.pii_redactor = PIIRedactor()
        self._advanced_defender = None  # Lazy initialization to avoid circular imports
        
        # Patterns for detecting potentially malicious input
        self.malicious_patterns = [
            re.compile(r'<script[^>]*>.*?</script>', re.IGNORECASE | re.DOTALL),  # XSS
            re.compile(r'javascript:', re.IGNORECASE),  # JavaScript URLs
            re.compile(r'on\w+\s*=', re.IGNORECASE),  # Event handlers
            re.compile(r'(union\s+select|select\s+\*|insert\s+into|update\s+set|delete\s+from|drop\s+(table|database|schema)|create\s+(table|database|schema|index)|alter\s+(table|database))', re.IGNORECASE),  # SQL injection
            re.compile(r'(\.\./|\.\.\\)', re.IGNORECASE),  # Path traversal
            re.compile(r'(eval|exec|system|shell_exec)\s*\(', re.IGNORECASE),  # Code injection
        ]
        
        # Formula injection patterns (Excel/Sheets/CSV injection)
        self.formula_injection_patterns = [
            re.compile(r'^=', re.IGNORECASE),  # Starts with equals
            re.compile(r'^@[A-Z]', re.IGNORECASE),  # Starts with at symbol followed by letter (not email)
            re.compile(r'^\+[0-9]', re.IGNORECASE),  # Starts with plus followed by number (not bullet)
            re.compile(r'^-[0-9]', re.IGNORECASE),  # Starts with minus followed by number (not bullet point)
            re.compile(r'=\s*(WEBSERVICE|HYPERLINK|IMPORTXML|IMPORTHTML|IMPORTDATA|IMPORTRANGE|IMPORTFEED)', re.IGNORECASE),  # Dangerous functions
            re.compile(r'=\s*(CMD|SYSTEM|SHELL|EXEC)', re.IGNORECASE),  # Command execution
            re.compile(r'=\s*(DDE|DDEAUTO)', re.IGNORECASE),  # Dynamic Data Exchange
        ]
        
        # Banned tools/technologies that should never appear in outputs
        self.banned_tools = [
            "metasploit", "burp suite", "sqlmap", "nmap", "masscan", "wireshark",
            "john the ripper", "hashcat", "aircrack", "hydra", "nikto",
            "owasp zap", "beef framework", "maltego", "shodan", "censys"
        ]
        
        # SSRF and malicious URL patterns
        self.ssrf_patterns = [
            re.compile(r'169\.254\.169\.254', re.IGNORECASE),  # AWS metadata
            re.compile(r'169\.254\.170\.2', re.IGNORECASE),   # AWS metadata v2
            re.compile(r'metadata\.google\.internal', re.IGNORECASE),  # GCP metadata
            re.compile(r'169\.254\.169\.254/latest/meta-data', re.IGNORECASE),  # AWS specific
            re.compile(r'169\.254\.169\.254/computeMetadata', re.IGNORECASE),   # GCP specific
            re.compile(r'localhost:\d+', re.IGNORECASE),      # Local services
            re.compile(r'127\.0\.0\.1:\d+', re.IGNORECASE),   # Local services
            re.compile(r'0\.0\.0\.0:\d+', re.IGNORECASE),     # Local services
            re.compile(r'10\.\d+\.\d+\.\d+', re.IGNORECASE),  # Private IP range
            re.compile(r'192\.168\.\d+\.\d+', re.IGNORECASE), # Private IP range
            re.compile(r'172\.(1[6-9]|2[0-9]|3[0-1])\.\d+\.\d+', re.IGNORECASE), # Private IP range
        ]
        
        # Malicious intent patterns
        self.malicious_intent_patterns = [
            re.compile(r'\b(penetration|pen)\s+test(ing)?\b', re.IGNORECASE),
            re.compile(r'\bsecurity\s+(test|audit|assessment)\b', re.IGNORECASE),
            re.compile(r'\b(vulnerability|vuln)\s+(scan|test|assessment)\b', re.IGNORECASE),
            re.compile(r'\b(exploit|attack|hack|breach)\b', re.IGNORECASE),
            re.compile(r'\b(backdoor|rootkit|malware|trojan)\b', re.IGNORECASE),
            re.compile(r'\b(privilege\s+escalation|lateral\s+movement)\b', re.IGNORECASE),
            re.compile(r'\b(sql\s+injection|xss|csrf|ssrf)\b', re.IGNORECASE),
            re.compile(r'\b(brute\s+force|dictionary\s+attack)\b', re.IGNORECASE),
            re.compile(r'\b(reverse\s+shell|web\s+shell)\b', re.IGNORECASE),
            re.compile(r'\b(credential\s+(dump|harvest|steal))\b', re.IGNORECASE),
            re.compile(r'\b(network\s+(scan|reconnaissance))\b', re.IGNORECASE),
            re.compile(r'\b(port\s+scan|service\s+enumeration)\b', re.IGNORECASE),
        ]
        
        # Out-of-scope patterns (not legitimate business automation)
        self.out_of_scope_patterns = [
            re.compile(r'\b(test|check|verify)\s+(security|vulnerabilities?)\b', re.IGNORECASE),
            re.compile(r'\b(access|retrieve|get)\s+(metadata|secrets?|credentials?)\b', re.IGNORECASE),
            re.compile(r'\b(bypass|circumvent|disable)\s+(security|authentication|authorization)\b', re.IGNORECASE),
            re.compile(r'\b(enumerate|discover|map)\s+(services?|ports?|endpoints?)\b', re.IGNORECASE),
            re.compile(r'\b(extract|dump|steal|harvest)\s+(data|information|files?|credentials?)\b', re.IGNORECASE),
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
        
        # Check for formula injection patterns and sanitize
        for pattern in self.formula_injection_patterns:
            if pattern.search(text):
                app_logger.warning(f"Formula injection pattern detected and sanitized: {pattern.pattern}")
                # Replace dangerous formula starts with safe alternatives
                text = re.sub(r'^=', "'=", text, flags=re.MULTILINE)  # Prefix with quote to disable formula
                text = re.sub(r'^@', "'@", text, flags=re.MULTILINE)
                text = re.sub(r'^\+', "'+", text, flags=re.MULTILINE)
                text = re.sub(r'^-', "'-", text, flags=re.MULTILINE)
        
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
    
    def detect_ssrf_attempts(self, text: str) -> tuple[bool, List[str]]:
        """Detect SSRF attempts in text."""
        found_ssrf = []
        
        for pattern in self.ssrf_patterns:
            matches = pattern.findall(text)
            if matches:
                found_ssrf.extend(matches)
        
        if found_ssrf:
            app_logger.error(f"SSRF patterns detected: {found_ssrf}")
            return True, found_ssrf
        
        return False, []
    
    def detect_malicious_intent(self, text: str) -> tuple[bool, List[str]]:
        """Detect malicious intent patterns in text."""
        found_malicious = []
        
        for pattern in self.malicious_intent_patterns:
            matches = pattern.findall(text)
            if matches:
                # Convert tuples to strings for logging
                if isinstance(matches[0], tuple):
                    found_malicious.extend([' '.join(match) for match in matches])
                else:
                    found_malicious.extend(matches)
        
        if found_malicious:
            app_logger.error(f"Malicious intent patterns detected: {found_malicious}")
            return True, found_malicious
        
        return False, []
    
    def detect_out_of_scope(self, text: str) -> tuple[bool, List[str]]:
        """Detect out-of-scope requests (not legitimate business automation)."""
        found_out_of_scope = []
        
        for pattern in self.out_of_scope_patterns:
            matches = pattern.findall(text)
            if matches:
                # Convert tuples to strings for logging
                if isinstance(matches[0], tuple):
                    found_out_of_scope.extend([' '.join(match) for match in matches])
                else:
                    found_out_of_scope.extend(matches)
        
        if found_out_of_scope:
            app_logger.warning(f"Out-of-scope patterns detected: {found_out_of_scope}")
            return True, found_out_of_scope
        
        return False, []
    
    def validate_business_automation_scope(self, text: str) -> tuple[bool, str, Dict[str, List[str]]]:
        """Comprehensive validation for legitimate business automation requirements."""
        violations = {}
        
        # Check for formula injection attempts (CRITICAL - check first)
        has_formula_injection, formula_patterns = self.detect_formula_injection(text)
        if has_formula_injection:
            violations['formula_injection'] = formula_patterns
        
        # Check for SSRF attempts
        has_ssrf, ssrf_patterns = self.detect_ssrf_attempts(text)
        if has_ssrf:
            violations['ssrf'] = ssrf_patterns
        
        # Check for malicious intent
        has_malicious, malicious_patterns = self.detect_malicious_intent(text)
        if has_malicious:
            violations['malicious_intent'] = malicious_patterns
        
        # Check for out-of-scope requests
        has_out_of_scope, out_of_scope_patterns = self.detect_out_of_scope(text)
        if has_out_of_scope:
            violations['out_of_scope'] = out_of_scope_patterns
        
        if violations:
            # Generate intelligent feedback without exposing malicious content to LLMs
            from app.security.intelligent_feedback import SecurityFeedbackGenerator
            feedback_generator = SecurityFeedbackGenerator()
            detailed_feedback = feedback_generator.generate_feedback(violations)
            
            return False, detailed_feedback, violations
        
        return True, "Valid business automation requirement", {}
    
    def detect_formula_injection(self, text: str) -> tuple[bool, List[str]]:
        """Detect formula injection attempts in text."""
        found_formulas = []
        
        # Check each line for formula injection patterns
        lines = text.split('\n')
        for line_num, line in enumerate(lines, 1):
            line = line.strip()
            if not line:
                continue
                
            for pattern in self.formula_injection_patterns:
                if pattern.search(line):
                    found_formulas.append(f"Line {line_num}: {line[:50]}...")
                    break  # One match per line is enough
        
        if found_formulas:
            app_logger.error(f"Formula injection patterns detected: {found_formulas}")
            return True, found_formulas
        
        return False, []
    
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
    
    def _get_advanced_defender(self):
        """Get the advanced prompt defender instance (lazy initialization)."""
        if self._advanced_defender is None:
            try:
                from app.security.advanced_prompt_defender import AdvancedPromptDefender
                self._advanced_defender = AdvancedPromptDefender()
                app_logger.info("AdvancedPromptDefender integrated with SecurityValidator")
            except ImportError as e:
                app_logger.warning(f"AdvancedPromptDefender not available: {e}")
                self._advanced_defender = False  # Mark as unavailable
        return self._advanced_defender if self._advanced_defender is not False else None
    
    async def validate_with_advanced_defense(self, text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Validate text using advanced prompt defense system.
        
        Returns:
            Tuple of (is_valid, reason, details)
        """
        defender = self._get_advanced_defender()
        if not defender:
            # Fall back to legacy validation
            return self.validate_business_automation_scope(text)
        
        try:
            decision = await defender.validate_input(text)
            
            # Convert SecurityDecision to legacy format
            if decision.action.value == "pass":
                return True, "Valid business automation requirement", {
                    "action": decision.action.value,
                    "confidence": decision.confidence,
                    "detected_attacks": [p.id for p in decision.detected_attacks]
                }
            else:
                return False, decision.user_message or "Security validation failed", {
                    "action": decision.action.value,
                    "confidence": decision.confidence,
                    "detected_attacks": [p.id for p in decision.detected_attacks],
                    "technical_details": decision.technical_details
                }
                
        except Exception as e:
            app_logger.error(f"Advanced defense validation failed: {e}")
            # Fall back to legacy validation
            return self.validate_business_automation_scope(text)
    
    def validate_with_advanced_defense_sync(self, text: str) -> Tuple[bool, str, Dict[str, Any]]:
        """
        Synchronous wrapper for advanced defense validation.
        
        Returns:
            Tuple of (is_valid, reason, details)
        """
        try:
            # Try to get existing event loop
            loop = asyncio.get_event_loop()
            if loop.is_running():
                # If we're already in an async context, we can't use run_until_complete
                # Fall back to legacy validation
                app_logger.debug("Already in async context, using legacy validation")
                return self.validate_business_automation_scope(text)
            else:
                return loop.run_until_complete(self.validate_with_advanced_defense(text))
        except RuntimeError:
            # No event loop, create one
            return asyncio.run(self.validate_with_advanced_defense(text))
        except Exception as e:
            app_logger.error(f"Sync advanced defense validation failed: {e}")
            return self.validate_business_automation_scope(text)


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
        
        # Allow alphanumeric, hyphens, dots, underscores, and colons (for Bedrock models)
        model_pattern = re.compile(r'^[a-zA-Z0-9\-\._:]+$')
        return bool(model_pattern.match(model)) and len(model) <= 100
    
    def validate_export_format(self, format_type: str) -> bool:
        """Validate export format."""
        if not format_type or not isinstance(format_type, str):
            return False
        allowed_formats = ["json", "md", "markdown", "comprehensive", "report"]
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
        
        # Use advanced defense validation if available
        try:
            is_valid_scope, scope_reason, violations = self.security_validator.validate_with_advanced_defense_sync(text)
            if not is_valid_scope:
                app_logger.error(f"Requirements validation failed - advanced defense: {scope_reason}")
                app_logger.error(f"Violation details: {violations}")
                return False, scope_reason
        except Exception as e:
            app_logger.error(f"Advanced defense validation error: {e}")
            # Fall back to legacy validation
            is_valid_scope, scope_reason, violations = self.security_validator.validate_business_automation_scope(text)
            if not is_valid_scope:
                app_logger.error(f"Requirements validation failed - legacy validation: {scope_reason}")
                app_logger.error(f"Violation details: {violations}")
                return False, scope_reason
        
        # Sanitize and check for malicious content
        sanitized = self.security_validator.sanitize_string(text)
        if sanitized != text:
            app_logger.warning("Requirements text was sanitized due to suspicious content")
        
        return True, "Valid"
    
    def validate_jira_credentials(self, base_url: str, email: str = None, api_token: str = None, 
                                 username: str = None, password: str = None, 
                                 personal_access_token: str = None, auth_type: str = "api_token") -> tuple[bool, str]:
        """Validate Jira credentials format based on authentication type."""
        if not base_url:
            return False, "Base URL is required"
        
        # Validate URL format
        url_pattern = re.compile(r'^https?://[a-zA-Z0-9\-\.]+\.[a-zA-Z]{2,}(/.*)?$')
        if not url_pattern.match(base_url):
            return False, "Invalid Jira base URL format"
        
        # Validate credentials based on auth type
        if auth_type == "api_token":
            if not all([email, api_token]):
                return False, "Email and API token are required for API token authentication"
            
            # Validate email format
            email_pattern = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')
            if not email_pattern.match(email):
                return False, "Invalid email format"
            
            # Validate API token (base64-like format with minimum length)
            if not re.match(r'^[a-zA-Z0-9+/=_-]+$', api_token) or len(api_token) < 10:
                return False, "Invalid API token format"
                
        elif auth_type == "basic":
            if not all([username, password]):
                return False, "Username and password are required for basic authentication"
            
            # Basic validation for username and password
            if len(username.strip()) == 0:
                return False, "Username cannot be empty"
            if len(password.strip()) == 0:
                return False, "Password cannot be empty"
                
        elif auth_type == "pat":
            if not personal_access_token:
                return False, "Personal Access Token is required for PAT authentication"
            
            # Validate PAT format (similar to API token)
            if not re.match(r'^[a-zA-Z0-9+/=_-]+$', personal_access_token) or len(personal_access_token) < 10:
                return False, "Invalid Personal Access Token format"
                
        elif auth_type == "sso":
            # SSO doesn't require additional credential validation
            pass
        else:
            return False, f"Unsupported authentication type: {auth_type}"
        
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