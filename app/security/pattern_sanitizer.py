"""Pattern sanitization to prevent storage of malicious patterns."""

import asyncio
from typing import Dict, Any, List, Tuple
from app.utils.logger import app_logger
from app.security.validation import SecurityValidator


class PatternSanitizer:
    """Sanitizes patterns to prevent storage of malicious content."""
    
    def __init__(self):
        self.security_validator = SecurityValidator()
        self._advanced_defender = None  # Lazy initialization
        
        # Patterns that indicate security testing rather than business automation
        self.security_testing_indicators = [
            "penetration", "vulnerability", "exploit", "attack",
            "hack", "breach", "backdoor", "rootkit", "malware", "trojan",
            "privilege escalation", "lateral movement", "sql injection",
            "xss", "csrf", "ssrf", "brute force", "dictionary attack",
            "reverse shell", "web shell", "credential dump", "network scan",
            "port scan", "service enumeration"
        ]
        
        # Domains that are clearly security testing
        self.security_testing_domains = [
            "penetration testing", "security testing", "vulnerability assessment",
            "security audit", "red team", "blue team", "threat hunting",
            "incident response", "forensics", "malware analysis"
        ]
    
    def is_security_testing_pattern(self, pattern: Dict[str, Any]) -> Tuple[bool, str]:
        """Check if pattern is for security testing rather than business automation."""
        
        # Check pattern name
        name = pattern.get('name', '').lower()
        for indicator in self.security_testing_indicators:
            if indicator in name:
                return True, f"Pattern name contains security testing indicator: '{indicator}'"
        
        # Check description
        description = pattern.get('description', '').lower()
        for indicator in self.security_testing_indicators:
            if indicator in description:
                return True, f"Pattern description contains security testing indicator: '{indicator}'"
        
        # Check domain
        domain = pattern.get('domain', '').lower()
        for testing_domain in self.security_testing_domains:
            if testing_domain in domain:
                return True, f"Pattern domain indicates security testing: '{testing_domain}'"
        
        # Check tech stack for banned tools
        tech_stack = pattern.get('tech_stack', [])
        if isinstance(tech_stack, list):
            tech_stack_text = ' '.join(tech_stack).lower()
            if not self.security_validator.validate_no_banned_tools(tech_stack_text):
                return True, "Pattern tech stack contains banned security tools"
        
        # Check required integrations for SSRF patterns
        required_integrations = pattern.get('constraints', {}).get('required_integrations', [])
        if isinstance(required_integrations, list):
            for integration in required_integrations:
                if isinstance(integration, str):
                    has_ssrf, ssrf_patterns = self.security_validator.detect_ssrf_attempts(integration)
                    if has_ssrf:
                        return True, f"Pattern contains SSRF attempt in required integrations: {ssrf_patterns}"
                    
                    # Check for formula injection in integrations
                    has_formula, formula_patterns = self.security_validator.detect_formula_injection(integration)
                    if has_formula:
                        return True, f"Pattern contains formula injection in required integrations: {formula_patterns}"
        
        # Check all text fields for formula injection
        text_fields = ['name', 'description', 'domain', 'llm_recommended_approach']
        for field in text_fields:
            if field in pattern and isinstance(pattern[field], str):
                has_formula, formula_patterns = self.security_validator.detect_formula_injection(pattern[field])
                if has_formula:
                    return True, f"Pattern contains formula injection in {field}: {formula_patterns}"
        
        return False, ""
    
    def sanitize_pattern_for_storage(self, pattern: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """Sanitize pattern before storage, return (should_store, sanitized_pattern, reason)."""
        
        # Check if this is a security testing pattern
        is_security_testing, reason = self.is_security_testing_pattern(pattern)
        if is_security_testing:
            app_logger.error(f"Blocking storage of security testing pattern: {reason}")
            app_logger.error(f"Pattern details: {pattern.get('name', 'Unknown')} - {pattern.get('description', 'No description')}")
            return False, {}, f"Pattern blocked: {reason}"
        
        # Create sanitized copy
        sanitized = pattern.copy()
        
        # Sanitize text fields
        text_fields = ['name', 'description', 'domain', 'llm_recommended_approach']
        for field in text_fields:
            if field in sanitized and isinstance(sanitized[field], str):
                sanitized[field] = self.security_validator.sanitize_string(sanitized[field])
        
        # Sanitize lists of strings
        list_fields = ['pattern_type', 'input_requirements', 'tech_stack', 'llm_insights', 'llm_challenges']
        for field in list_fields:
            if field in sanitized and isinstance(sanitized[field], list):
                sanitized[field] = [
                    self.security_validator.sanitize_string(str(item)) 
                    for item in sanitized[field]
                ]
        
        # Sanitize constraints
        if 'constraints' in sanitized and isinstance(sanitized['constraints'], dict):
            constraints = sanitized['constraints']
            
            # Remove any SSRF attempts and formula injection from required integrations
            if 'required_integrations' in constraints:
                clean_integrations = []
                for integration in constraints['required_integrations']:
                    if isinstance(integration, str):
                        has_ssrf, _ = self.security_validator.detect_ssrf_attempts(integration)
                        has_formula, _ = self.security_validator.detect_formula_injection(integration)
                        
                        if not has_ssrf and not has_formula:
                            clean_integrations.append(self.security_validator.sanitize_string(integration))
                        else:
                            if has_ssrf:
                                app_logger.warning(f"Removed SSRF attempt from pattern integrations: {integration}")
                            if has_formula:
                                app_logger.warning(f"Removed formula injection from pattern integrations: {integration}")
                constraints['required_integrations'] = clean_integrations
        
        app_logger.info(f"Pattern sanitized and approved for storage: {sanitized.get('name', 'Unknown')}")
        return True, sanitized, "Pattern sanitized successfully"
    
    def validate_existing_patterns(self, patterns: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Validate existing patterns and remove any that are security testing patterns."""
        clean_patterns = []
        removed_count = 0
        
        for pattern in patterns:
            is_security_testing, reason = self.is_security_testing_pattern(pattern)
            if is_security_testing:
                app_logger.warning(f"Removing existing security testing pattern: {pattern.get('pattern_id', 'Unknown')} - {reason}")
                removed_count += 1
            else:
                clean_patterns.append(pattern)
        
        if removed_count > 0:
            app_logger.info(f"Removed {removed_count} security testing patterns from pattern library")
        
        return clean_patterns
    
    def _get_advanced_defender(self):
        """Get the advanced prompt defender instance (lazy initialization)."""
        if self._advanced_defender is None:
            try:
                from app.security.advanced_prompt_defender import AdvancedPromptDefender
                self._advanced_defender = AdvancedPromptDefender()
                app_logger.info("AdvancedPromptDefender integrated with PatternSanitizer")
            except ImportError as e:
                app_logger.warning(f"AdvancedPromptDefender not available: {e}")
                self._advanced_defender = False  # Mark as unavailable
        return self._advanced_defender if self._advanced_defender is not False else None
    
    async def validate_pattern_with_advanced_defense(self, pattern: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Validate pattern using advanced prompt defense system.
        
        Returns:
            Tuple of (is_valid, reason)
        """
        defender = self._get_advanced_defender()
        if not defender:
            # Fall back to legacy validation
            return self.is_security_testing_pattern(pattern)
        
        try:
            # Combine all text fields from pattern for validation
            text_fields = ['name', 'description', 'domain', 'llm_recommended_approach']
            combined_text = []
            
            for field in text_fields:
                if field in pattern and isinstance(pattern[field], str):
                    combined_text.append(f"{field}: {pattern[field]}")
            
            # Add tech stack
            if 'tech_stack' in pattern and isinstance(pattern['tech_stack'], list):
                combined_text.append(f"tech_stack: {' '.join(pattern['tech_stack'])}")
            
            # Add required integrations
            if 'constraints' in pattern and isinstance(pattern['constraints'], dict):
                constraints = pattern['constraints']
                if 'required_integrations' in constraints:
                    integrations = constraints['required_integrations']
                    if isinstance(integrations, list):
                        combined_text.append(f"required_integrations: {' '.join(integrations)}")
            
            full_text = "\n".join(combined_text)
            
            decision = await defender.validate_input(full_text)
            
            # If any attacks are detected, reject the pattern
            if decision.action.value != "pass":
                attack_names = [p.name for p in decision.detected_attacks]
                return True, f"Pattern contains attack patterns: {', '.join(attack_names)}"
            
            return False, ""
            
        except Exception as e:
            app_logger.error(f"Advanced defense pattern validation failed: {e}")
            # Fall back to legacy validation
            return self.is_security_testing_pattern(pattern)
    
    def validate_pattern_with_advanced_defense_sync(self, pattern: Dict[str, Any]) -> Tuple[bool, str]:
        """
        Synchronous wrapper for advanced defense pattern validation.
        
        Returns:
            Tuple of (is_security_testing, reason)
        """
        try:
            # Use thread-based approach to avoid event loop conflicts
            from concurrent.futures import ThreadPoolExecutor
            
            def run_in_thread():
                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                try:
                    return loop.run_until_complete(self.validate_pattern_with_advanced_defense(pattern))
                finally:
                    loop.close()
            
            with ThreadPoolExecutor() as executor:
                future = executor.submit(run_in_thread)
                return future.result(timeout=30)  # 30 second timeout
                
        except Exception as e:
            app_logger.error(f"Sync advanced defense pattern validation failed: {e}")
            # Fall back to legacy validation
            return self.is_security_testing_pattern(pattern)
    
    def sanitize_pattern_for_storage_enhanced(self, pattern: Dict[str, Any]) -> Tuple[bool, Dict[str, Any], str]:
        """
        Enhanced pattern sanitization using advanced prompt defense.
        
        Returns:
            Tuple of (should_store, sanitized_pattern, reason)
        """
        # First check with advanced defense if available
        try:
            is_security_testing, reason = self.validate_pattern_with_advanced_defense_sync(pattern)
            if is_security_testing:
                app_logger.error(f"Blocking storage of pattern with advanced defense: {reason}")
                app_logger.error(f"Pattern details: {pattern.get('name', 'Unknown')} - {pattern.get('description', 'No description')}")
                return False, {}, f"Pattern blocked by advanced defense: {reason}"
        except Exception as e:
            app_logger.warning(f"Advanced defense pattern validation failed, using legacy: {e}")
        
        # Fall back to legacy sanitization
        return self.sanitize_pattern_for_storage(pattern)