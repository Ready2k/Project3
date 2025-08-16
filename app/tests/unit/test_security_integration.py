"""
Unit tests for security integration components.

Tests the individual methods and functions added for integrating
AdvancedPromptDefender with existing security components.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock

from app.security.validation import SecurityValidator, InputValidator
from app.security.pattern_sanitizer import PatternSanitizer
from app.security.middleware import SecurityMiddleware
from app.security.attack_patterns import SecurityAction, SecurityDecision, AttackPattern, AttackSeverity


class TestSecurityValidatorMethods:
    """Test SecurityValidator integration methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SecurityValidator()
    
    def test_get_advanced_defender_lazy_initialization(self):
        """Test lazy initialization of advanced defender."""
        # Initially should be None
        assert self.validator._advanced_defender is None
        
        # First call should initialize
        defender = self.validator._get_advanced_defender()
        assert defender is not None or self.validator._advanced_defender is False
        
        # Second call should return cached instance
        defender2 = self.validator._get_advanced_defender()
        assert defender2 is defender
    
    def test_get_advanced_defender_import_error(self):
        """Test handling of import errors."""
        # Create a new validator and patch the import inside the method
        validator = SecurityValidator()
        
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            defender = validator._get_advanced_defender()
            
            assert defender is None
            assert validator._advanced_defender is False
    
    @pytest.mark.asyncio
    async def test_validate_with_advanced_defense_success(self):
        """Test successful validation with advanced defense."""
        mock_decision = SecurityDecision(
            action=SecurityAction.PASS,
            confidence=0.1,
            detected_attacks=[],
            user_message="",
            technical_details="No issues detected"
        )
        
        with patch.object(self.validator, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(return_value=mock_decision)
            mock_get_defender.return_value = mock_defender
            
            is_valid, reason, details = await self.validator.validate_with_advanced_defense("test input")
            
            assert is_valid is True
            assert "Valid business automation requirement" in reason
            assert details["action"] == "pass"
            assert details["confidence"] == 0.1
    
    @pytest.mark.asyncio
    async def test_validate_with_advanced_defense_block(self):
        """Test blocked validation with advanced defense."""
        mock_attack = AttackPattern(
            id="TEST-001",
            category="C",
            name="Test Attack",
            description="Test attack pattern",
            pattern_regex="test",
            semantic_indicators=[],
            severity=AttackSeverity.HIGH,
            response_action=SecurityAction.BLOCK,
            examples=[],
            false_positive_indicators=[]
        )
        
        mock_decision = SecurityDecision(
            action=SecurityAction.BLOCK,
            confidence=0.9,
            detected_attacks=[mock_attack],
            user_message="Request blocked",
            technical_details="Attack detected"
        )
        
        with patch.object(self.validator, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(return_value=mock_decision)
            mock_get_defender.return_value = mock_defender
            
            is_valid, reason, details = await self.validator.validate_with_advanced_defense("malicious input")
            
            assert is_valid is False
            assert reason == "Request blocked"
            assert details["action"] == "block"
            assert details["confidence"] == 0.9
            assert details["detected_attacks"] == ["TEST-001"]
    
    @pytest.mark.asyncio
    async def test_validate_with_advanced_defense_fallback(self):
        """Test fallback to legacy validation."""
        with patch.object(self.validator, '_get_advanced_defender', return_value=None):
            with patch.object(self.validator, 'validate_business_automation_scope') as mock_legacy:
                mock_legacy.return_value = (True, "Valid", {})
                
                is_valid, reason, details = await self.validator.validate_with_advanced_defense("test input")
                
                assert is_valid is True
                assert reason == "Valid"
                mock_legacy.assert_called_once_with("test input")
    
    @pytest.mark.asyncio
    async def test_validate_with_advanced_defense_error_handling(self):
        """Test error handling in advanced defense validation."""
        with patch.object(self.validator, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(side_effect=Exception("Validation error"))
            mock_get_defender.return_value = mock_defender
            
            with patch.object(self.validator, 'validate_business_automation_scope') as mock_legacy:
                mock_legacy.return_value = (True, "Valid", {})
                
                is_valid, reason, details = await self.validator.validate_with_advanced_defense("test input")
                
                assert is_valid is True
                assert reason == "Valid"
                mock_legacy.assert_called_once_with("test input")
    
    def test_sync_wrapper_with_running_loop(self):
        """Test sync wrapper when event loop is already running."""
        with patch('asyncio.get_event_loop') as mock_get_loop:
            mock_loop = Mock()
            mock_loop.is_running.return_value = True
            mock_get_loop.return_value = mock_loop
            
            with patch.object(self.validator, 'validate_business_automation_scope') as mock_legacy:
                mock_legacy.return_value = (True, "Valid", {})
                
                is_valid, reason, details = self.validator.validate_with_advanced_defense_sync("test input")
                
                assert is_valid is True
                assert reason == "Valid"
                mock_legacy.assert_called_once_with("test input")
    
    def test_sync_wrapper_no_loop(self):
        """Test sync wrapper when no event loop exists."""
        with patch('asyncio.get_event_loop', side_effect=RuntimeError("No event loop")):
            with patch('asyncio.run') as mock_run:
                mock_run.return_value = (True, "Valid", {})
                
                is_valid, reason, details = self.validator.validate_with_advanced_defense_sync("test input")
                
                assert is_valid is True
                assert reason == "Valid"
                mock_run.assert_called_once()


class TestPatternSanitizerMethods:
    """Test PatternSanitizer integration methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = PatternSanitizer()
    
    def test_get_advanced_defender_initialization(self):
        """Test advanced defender initialization in sanitizer."""
        defender = self.sanitizer._get_advanced_defender()
        assert defender is not None or self.sanitizer._advanced_defender is False
    
    @pytest.mark.asyncio
    async def test_validate_pattern_with_advanced_defense_pass(self):
        """Test pattern validation that passes."""
        pattern = {
            "name": "Test Pattern",
            "description": "Test description",
            "domain": "Test",
            "tech_stack": ["Python"]
        }
        
        mock_decision = SecurityDecision(
            action=SecurityAction.PASS,
            confidence=0.1,
            detected_attacks=[],
            user_message="",
            technical_details=""
        )
        
        with patch.object(self.sanitizer, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(return_value=mock_decision)
            mock_get_defender.return_value = mock_defender
            
            is_security_testing, reason = await self.sanitizer.validate_pattern_with_advanced_defense(pattern)
            
            # When action is PASS, should return False for is_security_testing
            assert is_security_testing is False
            assert reason == ""
    
    @pytest.mark.asyncio
    async def test_validate_pattern_with_advanced_defense_block(self):
        """Test pattern validation that blocks."""
        pattern = {
            "name": "Malicious Pattern",
            "description": "Extract system data",
            "domain": "Security",
            "tech_stack": ["metasploit"]
        }
        
        mock_attack = AttackPattern(
            id="TEST-001",
            category="C",
            name="Test Attack",
            description="Test attack pattern",
            pattern_regex="test",
            semantic_indicators=[],
            severity=AttackSeverity.HIGH,
            response_action=SecurityAction.BLOCK,
            examples=[],
            false_positive_indicators=[]
        )
        
        mock_decision = SecurityDecision(
            action=SecurityAction.BLOCK,
            confidence=0.9,
            detected_attacks=[mock_attack],
            user_message="Blocked",
            technical_details="Attack detected"
        )
        
        with patch.object(self.sanitizer, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(return_value=mock_decision)
            mock_get_defender.return_value = mock_defender
            
            is_security_testing, reason = await self.sanitizer.validate_pattern_with_advanced_defense(pattern)
            
            assert is_security_testing is True
            assert "Test Attack" in reason
    
    def test_validate_pattern_sync_wrapper(self):
        """Test synchronous wrapper for pattern validation."""
        pattern = {
            "name": "Test Pattern",
            "description": "Test description"
        }
        
        with patch.object(self.sanitizer, 'is_security_testing_pattern') as mock_legacy:
            mock_legacy.return_value = (False, "")
            
            with patch('asyncio.get_event_loop', side_effect=RuntimeError("No loop")):
                with patch('asyncio.run') as mock_run:
                    mock_run.return_value = (False, "")
                    
                    is_security_testing, reason = self.sanitizer.validate_pattern_with_advanced_defense_sync(pattern)
                    
                    assert is_security_testing is False
                    assert reason == ""
    
    def test_enhanced_sanitization_workflow(self):
        """Test enhanced sanitization workflow."""
        pattern = {
            "name": "Test Pattern",
            "description": "Test description"
        }
        
        with patch.object(self.sanitizer, 'validate_pattern_with_advanced_defense_sync') as mock_advanced:
            mock_advanced.return_value = (False, "")
            
            with patch.object(self.sanitizer, 'sanitize_pattern_for_storage') as mock_legacy:
                mock_legacy.return_value = (True, pattern, "Success")
                
                should_store, sanitized, reason = self.sanitizer.sanitize_pattern_for_storage_enhanced(pattern)
                
                assert should_store is True
                assert sanitized == pattern
                assert reason == "Success"
                mock_advanced.assert_called_once_with(pattern)
    
    def test_enhanced_sanitization_blocks_malicious(self):
        """Test enhanced sanitization blocks malicious patterns."""
        pattern = {
            "name": "Malicious Pattern",
            "description": "Extract data"
        }
        
        with patch.object(self.sanitizer, 'validate_pattern_with_advanced_defense_sync') as mock_advanced:
            mock_advanced.return_value = (True, "Attack detected")
            
            should_store, sanitized, reason = self.sanitizer.sanitize_pattern_for_storage_enhanced(pattern)
            
            assert should_store is False
            assert sanitized == {}
            assert "blocked by advanced defense" in reason.lower()


class TestSecurityMiddlewareMethods:
    """Test SecurityMiddleware integration methods."""
    
    def setup_method(self):
        """Set up test fixtures."""
        self.app = Mock()
        self.middleware = SecurityMiddleware(self.app)
    
    def test_get_advanced_defender_initialization(self):
        """Test advanced defender initialization in middleware."""
        defender = self.middleware._get_advanced_defender()
        assert defender is not None or self.middleware._advanced_defender is False
    
    @pytest.mark.asyncio
    async def test_validate_request_body_non_post(self):
        """Test request body validation skips non-POST requests."""
        request = Mock()
        request.method = "GET"
        
        is_valid = await self.middleware._validate_request_body(request)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_request_body_non_json(self):
        """Test request body validation skips non-JSON requests."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "text/plain"}
        
        is_valid = await self.middleware._validate_request_body(request)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_request_body_empty(self):
        """Test request body validation handles empty bodies."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.body = AsyncMock(return_value=b'')
        
        is_valid = await self.middleware._validate_request_body(request)
        
        assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_request_body_invalid_utf8(self):
        """Test request body validation handles invalid UTF-8."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.body = AsyncMock(return_value=b'\xff\xfe\x00\x00')  # Invalid UTF-8
        
        is_valid = await self.middleware._validate_request_body(request)
        
        assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_validate_request_body_pass_decision(self):
        """Test request body validation with PASS decision."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        
        mock_decision = SecurityDecision(
            action=SecurityAction.PASS,
            confidence=0.1,
            detected_attacks=[],
            user_message="",
            technical_details=""
        )
        
        with patch.object(self.middleware, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(return_value=mock_decision)
            mock_get_defender.return_value = mock_defender
            
            is_valid = await self.middleware._validate_request_body(request)
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_request_body_block_decision(self):
        """Test request body validation with BLOCK decision."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.body = AsyncMock(return_value=b'{"malicious": "content"}')
        
        mock_decision = SecurityDecision(
            action=SecurityAction.BLOCK,
            confidence=0.9,
            detected_attacks=[],
            user_message="Blocked",
            technical_details="Attack detected"
        )
        
        with patch.object(self.middleware, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(return_value=mock_decision)
            mock_get_defender.return_value = mock_defender
            
            is_valid = await self.middleware._validate_request_body(request)
            
            assert is_valid is False
    
    @pytest.mark.asyncio
    async def test_validate_request_body_flag_decision(self):
        """Test request body validation with FLAG decision."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.body = AsyncMock(return_value=b'{"suspicious": "content"}')
        
        mock_decision = SecurityDecision(
            action=SecurityAction.FLAG,
            confidence=0.6,
            detected_attacks=[],
            user_message="Flagged",
            technical_details="Potential issue"
        )
        
        with patch.object(self.middleware, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(return_value=mock_decision)
            mock_get_defender.return_value = mock_defender
            
            is_valid = await self.middleware._validate_request_body(request)
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_request_body_no_defender(self):
        """Test request body validation when defender is unavailable."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        
        with patch.object(self.middleware, '_get_advanced_defender', return_value=None):
            is_valid = await self.middleware._validate_request_body(request)
            
            assert is_valid is True
    
    @pytest.mark.asyncio
    async def test_validate_request_body_error_handling(self):
        """Test request body validation error handling."""
        request = Mock()
        request.method = "POST"
        request.headers = {"content-type": "application/json"}
        request.body = AsyncMock(return_value=b'{"test": "data"}')
        
        with patch.object(self.middleware, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(side_effect=Exception("Validation error"))
            mock_get_defender.return_value = mock_defender
            
            is_valid = await self.middleware._validate_request_body(request)
            
            assert is_valid is True  # Should allow on error


class TestErrorHandling:
    """Test error handling in security integration."""
    
    def test_import_error_handling(self):
        """Test handling of import errors for AdvancedPromptDefender."""
        validator = SecurityValidator()
        
        with patch('builtins.__import__', side_effect=ImportError("Module not found")):
            defender = validator._get_advanced_defender()
            
            assert defender is None
            assert validator._advanced_defender is False
    
    def test_runtime_error_handling(self):
        """Test handling of runtime errors during validation."""
        validator = SecurityValidator()
        
        with patch.object(validator, '_get_advanced_defender') as mock_get_defender:
            mock_defender = Mock()
            mock_defender.validate_input = AsyncMock(side_effect=RuntimeError("Runtime error"))
            mock_get_defender.return_value = mock_defender
            
            # Should fall back to legacy validation
            with patch.object(validator, 'validate_business_automation_scope') as mock_legacy:
                mock_legacy.return_value = (True, "Valid", {})
                
                is_valid, reason, details = validator.validate_with_advanced_defense_sync("test")
                
                assert is_valid is True
                assert reason == "Valid"
                mock_legacy.assert_called_once_with("test")


if __name__ == "__main__":
    pytest.main([__file__])