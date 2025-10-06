"""
Security Service Implementation

Provides a centralized security service that wraps existing security components
and implements the Service interface for registry integration.
"""

from typing import Dict, Any, Optional, Tuple

from app.core.service import ConfigurableService
from app.security.validation import SecurityValidator
from app.security.advanced_prompt_defender import AdvancedPromptDefender


class SecurityService(ConfigurableService):
    """
    Centralized security service that provides input validation,
    prompt defense, and security monitoring capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the security service.
        
        Args:
            config: Security service configuration
        """
        super().__init__(config, "security_validator")
        self._dependencies = ["config", "logger"]
        
        # Configuration with defaults
        self.enable_input_validation = self.get_config("enable_input_validation", True)
        self.enable_output_sanitization = self.get_config("enable_output_sanitization", True)
        self.max_input_length = self.get_config("max_input_length", 10000)
        self.blocked_patterns = self.get_config("blocked_patterns", [])
        self.rate_limiting = self.get_config("rate_limiting", {})
        
        # Internal state
        self._security_validator: Optional[SecurityValidator] = None
        self._advanced_defender: Optional[AdvancedPromptDefender] = None
        self._validation_stats = {
            "total_validations": 0,
            "blocked_requests": 0,
            "sanitized_inputs": 0,
            "security_violations": 0
        }
    
    def _do_initialize(self) -> None:
        """Initialize the security service."""
        # Initialize security validator
        self._security_validator = SecurityValidator()
        
        # Initialize advanced prompt defender if available
        try:
            self._advanced_defender = AdvancedPromptDefender()
            self._logger.info("Advanced prompt defender initialized")
        except Exception as e:
            self._logger.warning(f"Advanced prompt defender not available: {e}")
            self._advanced_defender = None
        
        self._logger.info("Security service initialized")
    
    def _do_shutdown(self) -> None:
        """Shutdown the security service."""
        # Clean up any resources
        if self._advanced_defender:
            try:
                # The advanced defender might have cleanup methods
                pass
            except Exception as e:
                self._logger.warning(f"Error during advanced defender shutdown: {e}")
        
        self._logger.info("Security service shut down")
    
    def _do_health_check(self) -> bool:
        """Check if the security service is healthy."""
        try:
            # Test basic validation functionality
            if not self._security_validator:
                return False
            
            # Try a simple validation
            test_input = "test input"
            sanitized = self._security_validator.sanitize_string(test_input)
            
            return sanitized is not None
        except Exception:
            return False
    
    def validate_input(self, input_data: str) -> bool:
        """
        Validate input for security threats.
        
        Args:
            input_data: Input data to validate
            
        Returns:
            True if input is safe, False otherwise
        """
        if not self.enable_input_validation or not self._security_validator:
            return True
        
        try:
            self._validation_stats["total_validations"] += 1
            
            # Check input length
            if len(input_data) > self.max_input_length:
                self._validation_stats["blocked_requests"] += 1
                self._logger.warning(f"Input blocked: exceeds maximum length ({len(input_data)} > {self.max_input_length})")
                return False
            
            # Use advanced defender if available
            if self._advanced_defender:
                try:
                    import asyncio
                    # Try to run async validation
                    try:
                        loop = asyncio.get_event_loop()
                        if loop.is_running():
                            # Can't use run_until_complete in running loop
                            # Fall back to legacy validation
                            is_valid, reason, details = self._security_validator.validate_business_automation_scope(input_data)
                        else:
                            decision = loop.run_until_complete(self._advanced_defender.validate_input(input_data))
                            is_valid = decision.action.value == "pass"
                            if not is_valid:
                                self._validation_stats["security_violations"] += 1
                                self._logger.warning(f"Advanced defender blocked input: {decision.user_message}")
                    except RuntimeError:
                        # No event loop, create one
                        decision = asyncio.run(self._advanced_defender.validate_input(input_data))
                        is_valid = decision.action.value == "pass"
                        if not is_valid:
                            self._validation_stats["security_violations"] += 1
                            self._logger.warning(f"Advanced defender blocked input: {decision.user_message}")
                    
                    return is_valid
                    
                except Exception as e:
                    self._logger.warning(f"Advanced defender validation failed: {e}")
                    # Fall back to legacy validation
            
            # Legacy validation
            is_valid, reason, violations = self._security_validator.validate_business_automation_scope(input_data)
            if not is_valid:
                self._validation_stats["security_violations"] += 1
                self._logger.warning(f"Security validation failed: {reason}")
            
            return is_valid
            
        except Exception as e:
            self._logger.error(f"Input validation error: {e}")
            # Fail secure - reject input on validation error
            self._validation_stats["blocked_requests"] += 1
            return False
    
    def sanitize_input(self, input_data: str) -> str:
        """
        Sanitize input data.
        
        Args:
            input_data: Input data to sanitize
            
        Returns:
            Sanitized input data
        """
        if not self.enable_output_sanitization or not self._security_validator:
            return input_data
        
        try:
            original_length = len(input_data)
            sanitized = self._security_validator.sanitize_string(input_data, self.max_input_length)
            
            if len(sanitized) != original_length:
                self._validation_stats["sanitized_inputs"] += 1
                self._logger.debug("Input was sanitized")
            
            return sanitized
            
        except Exception as e:
            self._logger.error(f"Input sanitization error: {e}")
            # Return original input if sanitization fails
            return input_data
    
    def check_permissions(self, user_id: str, resource: str, action: str) -> bool:
        """
        Check user permissions for resource action.
        
        Args:
            user_id: User identifier
            resource: Resource name
            action: Action to perform
            
        Returns:
            True if action is allowed, False otherwise
        """
        # Placeholder implementation - would integrate with actual auth system
        self._logger.debug(f"Permission check: user={user_id}, resource={resource}, action={action}")
        
        # For now, allow all actions (this would be replaced with real auth logic)
        return True
    
    def encrypt(self, data: str) -> str:
        """
        Encrypt sensitive data.
        
        Args:
            data: Data to encrypt
            
        Returns:
            Encrypted data
        """
        # Placeholder implementation - would use proper encryption
        self._logger.debug("Data encryption requested")
        
        # For now, just return the data (this would be replaced with real encryption)
        return data
    
    def decrypt(self, encrypted_data: str) -> str:
        """
        Decrypt encrypted data.
        
        Args:
            encrypted_data: Encrypted data
            
        Returns:
            Decrypted data
        """
        # Placeholder implementation - would use proper decryption
        self._logger.debug("Data decryption requested")
        
        # For now, just return the data (this would be replaced with real decryption)
        return encrypted_data
    
    def validate_requirements_text(self, text: str) -> Tuple[bool, str]:
        """
        Validate requirements text input using the existing validator.
        
        Args:
            text: Requirements text to validate
            
        Returns:
            Tuple of (is_valid, error_message)
        """
        if not self._security_validator:
            return True, "Valid"
        
        try:
            # Use the existing validation logic from InputValidator
            from app.security.validation import InputValidator
            validator = InputValidator()
            return validator.validate_requirements_text(text)
            
        except Exception as e:
            self._logger.error(f"Requirements text validation error: {e}")
            return False, f"Validation error: {e}"
    
    def get_validation_stats(self) -> Dict[str, Any]:
        """
        Get security validation statistics.
        
        Returns:
            Dictionary with validation statistics
        """
        return {
            **self._validation_stats,
            "input_validation_enabled": self.enable_input_validation,
            "output_sanitization_enabled": self.enable_output_sanitization,
            "max_input_length": self.max_input_length,
            "advanced_defender_available": self._advanced_defender is not None,
            "blocked_patterns_count": len(self.blocked_patterns)
        }
    
    def reset_stats(self) -> None:
        """Reset validation statistics."""
        self._validation_stats = {
            "total_validations": 0,
            "blocked_requests": 0,
            "sanitized_inputs": 0,
            "security_violations": 0
        }
        self._logger.info("Security validation statistics reset")


class AdvancedPromptDefenseService(ConfigurableService):
    """
    Advanced Prompt Defense Service wrapper.
    
    Provides the advanced prompt defense system as a separate service
    for more granular control and configuration.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the advanced prompt defense service.
        
        Args:
            config: Advanced prompt defense configuration
        """
        super().__init__(config, "advanced_prompt_defender")
        self._dependencies = ["config", "logger", "cache"]
        
        # Configuration with defaults
        self.enabled = self.get_config("enabled", True)
        self.detection_confidence_threshold = self.get_config("detection_confidence_threshold", 0.7)
        self.flag_threshold = self.get_config("flag_threshold", 0.5)
        self.block_threshold = self.get_config("block_threshold", 0.9)
        self.max_validation_time_ms = self.get_config("max_validation_time_ms", 100)
        self.enable_caching = self.get_config("enable_caching", True)
        self.cache_ttl_seconds = self.get_config("cache_ttl_seconds", 300)
        self.parallel_detection = self.get_config("parallel_detection", True)
        self.educational_messages = self.get_config("educational_messages", True)
        
        # Internal state
        self._defender: Optional[AdvancedPromptDefender] = None
    
    def _do_initialize(self) -> None:
        """Initialize the advanced prompt defense service."""
        if not self.enabled:
            self._logger.info("Advanced prompt defense service disabled by configuration")
            return
        
        try:
            self._defender = AdvancedPromptDefender()
            self._logger.info("Advanced prompt defense service initialized")
        except Exception as e:
            self._logger.error(f"Failed to initialize advanced prompt defender: {e}")
            raise
    
    def _do_shutdown(self) -> None:
        """Shutdown the advanced prompt defense service."""
        if self._defender:
            # Clean up any resources
            pass
        self._logger.info("Advanced prompt defense service shut down")
    
    def _do_health_check(self) -> bool:
        """Check if the advanced prompt defense service is healthy."""
        if not self.enabled:
            return True  # Service is "healthy" if disabled
        
        return self._defender is not None
    
    async def validate_input(self, input_text: str) -> Dict[str, Any]:
        """
        Validate input using advanced prompt defense.
        
        Args:
            input_text: Input text to validate
            
        Returns:
            Dictionary with validation results
        """
        if not self.enabled or not self._defender:
            return {
                "action": "pass",
                "confidence": 1.0,
                "message": "Advanced prompt defense disabled"
            }
        
        try:
            decision = await self._defender.validate_input(input_text)
            
            return {
                "action": decision.action.value,
                "confidence": decision.confidence,
                "message": decision.user_message,
                "technical_details": decision.technical_details,
                "detected_attacks": [attack.id for attack in decision.detected_attacks]
            }
            
        except Exception as e:
            self._logger.error(f"Advanced prompt defense validation error: {e}")
            return {
                "action": "error",
                "confidence": 0.0,
                "message": f"Validation error: {e}"
            }