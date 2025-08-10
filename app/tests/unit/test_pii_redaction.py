"""Tests for PII redaction functionality."""

import pytest
from app.utils.redact import PIIRedactor
from app.security.validation import SecurityValidator


class TestPIIRedactor:
    """Test PII redaction functionality."""
    
    def setup_method(self):
        self.redactor = PIIRedactor()
    
    def test_redact_email(self):
        """Test email redaction."""
        text = "Contact me at john.doe@company.com for more information."
        result = self.redactor.redact(text)
        
        assert "john.doe@company.com" not in result
        assert "[REDACTED_EMAIL]" in result
        assert "Contact me at" in result
        assert "for more information." in result
    
    def test_redact_phone(self):
        """Test phone number redaction."""
        text = "Call me at 555-123-4567 during business hours."
        result = self.redactor.redact(text)
        
        assert "555-123-4567" not in result
        assert "[REDACTED_PHONE]" in result
        assert "Call me at" in result
        assert "during business hours." in result
    
    def test_redact_ssn(self):
        """Test SSN redaction."""
        text = "My SSN is 123-45-6789 for verification."
        result = self.redactor.redact(text)
        
        assert "123-45-6789" not in result
        assert "[REDACTED_SSN]" in result
        assert "My SSN is" in result
        assert "for verification." in result
    
    def test_redact_api_key(self):
        """Test API key redaction."""
        text = "Use API key sk-1234567890abcdef1234567890abcdef for authentication."
        result = self.redactor.redact(text)
        
        assert "sk-1234567890abcdef1234567890abcdef" not in result
        assert "[REDACTED_API_KEY]" in result
        assert "Use API key" in result
        assert "for authentication." in result
    
    def test_redact_multiple_pii_types(self):
        """Test redaction of multiple PII types in one text."""
        text = """
        Contact: john.doe@company.com
        Phone: 555-123-4567
        SSN: 123-45-6789
        API Key: sk-1234567890abcdef1234567890abcdef
        """
        result = self.redactor.redact(text)
        
        # Check that all PII is redacted
        assert "john.doe@company.com" not in result
        assert "555-123-4567" not in result
        assert "123-45-6789" not in result
        assert "sk-1234567890abcdef1234567890abcdef" not in result
        
        # Check that redaction markers are present
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_PHONE]" in result
        assert "[REDACTED_SSN]" in result
        assert "[REDACTED_API_KEY]" in result
        
        # Check that non-PII content remains
        assert "Contact:" in result
        assert "Phone:" in result
        assert "SSN:" in result
        assert "API Key:" in result
    
    def test_redact_empty_string(self):
        """Test redaction of empty string."""
        result = self.redactor.redact("")
        assert result == ""
    
    def test_redact_none(self):
        """Test redaction of None value."""
        result = self.redactor.redact(None)
        assert result is None
    
    def test_redact_no_pii(self):
        """Test redaction of text with no PII."""
        text = "This is a normal text without any sensitive information."
        result = self.redactor.redact(text)
        
        assert result == text
        assert "[REDACTED_" not in result
    
    def test_redact_partial_matches(self):
        """Test that partial matches are not redacted."""
        text = "Email domain is @company.com and phone area is 555."
        result = self.redactor.redact(text)
        
        # These should not be redacted as they're not complete patterns
        assert "@company.com" in result
        assert "555" in result
        assert "[REDACTED_" not in result
    
    def test_redact_multiple_same_type(self):
        """Test redaction of multiple instances of same PII type."""
        text = "Primary email: john@company.com, backup: jane@company.com"
        result = self.redactor.redact(text)
        
        assert "john@company.com" not in result
        assert "jane@company.com" not in result
        assert result.count("[REDACTED_EMAIL]") == 2
    
    def test_redact_case_insensitive_patterns(self):
        """Test that redaction works regardless of case."""
        # Note: Current implementation is case-sensitive for most patterns
        # This test documents the current behavior
        text = "Contact JOHN.DOE@COMPANY.COM for details."
        result = self.redactor.redact(text)
        
        # Email pattern should match regardless of case
        assert "JOHN.DOE@COMPANY.COM" not in result
        assert "[REDACTED_EMAIL]" in result


class TestSecurityValidatorPII:
    """Test PII redaction in SecurityValidator."""
    
    def setup_method(self):
        self.validator = SecurityValidator()
    
    def test_redact_pii_from_logs(self):
        """Test PII redaction from log messages."""
        log_message = "User john.doe@company.com called 555-123-4567 with API key sk-1234567890abcdef"
        result = self.validator.redact_pii_from_logs(log_message)
        
        # Check that PII is redacted
        assert "john.doe@company.com" not in result
        assert "555-123-4567" not in result
        assert "sk-1234567890abcdef" not in result
        
        # Check that redaction markers are present
        assert "[REDACTED_EMAIL]" in result
        assert "[REDACTED_PHONE]" in result
        assert "[REDACTED_API_KEY]" in result
        
        # Check that non-PII content remains
        assert "User" in result
        assert "called" in result
        assert "with API key" in result
    
    def test_sanitize_string_with_pii(self):
        """Test that string sanitization handles PII appropriately."""
        # Note: sanitize_string focuses on security threats, not PII
        # PII redaction is handled separately in logging
        text_with_pii = "Contact john.doe@company.com about <script>alert('xss')</script>"
        result = self.validator.sanitize_string(text_with_pii)
        
        # Should handle XSS but not necessarily PII (that's for logging)
        assert "&lt;script&gt;" in result or "[REMOVED_SUSPICIOUS_CONTENT]" in result
        # PII might still be present in sanitized string (redacted only in logs)


@pytest.mark.asyncio
async def test_pii_redaction_integration():
    """Test PII redaction integration with the application."""
    from app.api import app
    from fastapi.testclient import TestClient
    import json
    
    client = TestClient(app)
    
    # Test that PII in request payload is handled appropriately
    request_data = {
        "source": "text",
        "payload": {
            "text": "Contact john.doe@company.com for requirements about user authentication system.",
            "domain": "authentication"
        }
    }
    
    response = client.post("/ingest", json=request_data)
    
    # Should succeed (PII handling is internal)
    assert response.status_code == 200
    
    # The response should not contain the original PII
    # (though this depends on how the system processes the text)
    response_data = response.json()
    assert "session_id" in response_data


def test_comprehensive_pii_patterns():
    """Test comprehensive PII pattern matching."""
    redactor = PIIRedactor()
    
    test_cases = [
        # Email variations
        ("user@domain.com", "[REDACTED_EMAIL]"),
        ("first.last@company.co.uk", "[REDACTED_EMAIL]"),
        ("user+tag@domain.org", "[REDACTED_EMAIL]"),
        
        # Phone variations
        ("555-123-4567", "[REDACTED_PHONE]"),
        ("800-555-1234", "[REDACTED_PHONE]"),
        
        # SSN variations
        ("123-45-6789", "[REDACTED_SSN]"),
        ("987-65-4321", "[REDACTED_SSN]"),
        
        # API key variations (sk- prefix required)
        ("sk-1234567890abcdef1234567890abcdef", "[REDACTED_API_KEY]"),
        ("sk-abcdef1234567890abcdef1234567890", "[REDACTED_API_KEY]"),
    ]
    
    for original, expected_marker in test_cases:
        text = f"Sensitive data: {original}"
        result = redactor.redact(text)
        
        assert original not in result, f"Original PII '{original}' was not redacted"
        assert expected_marker in result, f"Expected marker '{expected_marker}' not found in result"
        assert "Sensitive data:" in result, "Non-PII content was removed"