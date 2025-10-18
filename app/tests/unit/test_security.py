"""Tests for security validation and middleware."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import Mock
from app.security.validation import InputValidator, SecurityValidator
from app.security.headers import SecurityHeaders
from app.security.middleware import RateLimitMiddleware, SecurityMiddleware
from fastapi import FastAPI
import time


class TestInputValidator:
    """Test input validation functionality."""

    def setup_method(self):
        self.validator = InputValidator()

    def test_validate_session_id_valid(self):
        """Test valid session ID validation."""
        valid_uuid = "123e4567-e89b-12d3-a456-426614174000"
        assert self.validator.validate_session_id(valid_uuid) is True

    def test_validate_session_id_invalid(self):
        """Test invalid session ID validation."""
        invalid_ids = [
            "not-a-uuid",
            "123e4567-e89b-12d3-a456",  # Too short
            "123e4567-e89b-12d3-a456-426614174000-extra",  # Too long
            "",
            None,
        ]

        for invalid_id in invalid_ids:
            assert self.validator.validate_session_id(invalid_id) is False

    def test_validate_provider_name_valid(self):
        """Test valid provider name validation."""
        valid_providers = ["openai", "bedrock", "claude", "internal", "fake"]

        for provider in valid_providers:
            assert self.validator.validate_provider_name(provider) is True
            assert self.validator.validate_provider_name(provider.upper()) is True

    def test_validate_provider_name_invalid(self):
        """Test invalid provider name validation."""
        invalid_providers = ["invalid", "gpt", "anthropic", "", None]

        for provider in invalid_providers:
            assert self.validator.validate_provider_name(provider) is False

    def test_validate_model_name_valid(self):
        """Test valid model name validation."""
        valid_models = [
            "gpt-4o",
            "gpt-3.5-turbo",
            "claude-3-opus",
            "model_name_123",
            "model.name",
        ]

        for model in valid_models:
            assert self.validator.validate_model_name(model) is True

    def test_validate_model_name_invalid(self):
        """Test invalid model name validation."""
        invalid_models = [
            "",
            None,
            "model with spaces",
            "model@invalid",
            "a" * 101,  # Too long
            "model/name",  # Invalid character
        ]

        for model in invalid_models:
            assert self.validator.validate_model_name(model) is False

    def test_validate_export_format_valid(self):
        """Test valid export format validation."""
        valid_formats = [
            "json",
            "md",
            "markdown",
            "comprehensive",
            "report",
            "JSON",
            "MD",
            "COMPREHENSIVE",
        ]

        for format_type in valid_formats:
            assert self.validator.validate_export_format(format_type) is True

    def test_validate_export_format_invalid(self):
        """Test invalid export format validation."""
        invalid_formats = ["pdf", "xml", "csv", "", None]

        for format_type in invalid_formats:
            assert self.validator.validate_export_format(format_type) is False

    def test_validate_requirements_text_valid(self):
        """Test valid requirements text validation."""
        valid_text = "This is a valid requirement with sufficient length."
        is_valid, message = self.validator.validate_requirements_text(valid_text)

        assert is_valid is True
        assert message == "Valid"

    def test_validate_requirements_text_invalid(self):
        """Test invalid requirements text validation."""
        test_cases = [
            ("", "Requirements text is required"),
            ("short", "Requirements text too short (minimum 10 characters)"),
            ("a" * 50001, "Requirements text too long (max 50,000 characters)"),
            (None, "Requirements text is required"),
        ]

        for text, expected_message in test_cases:
            is_valid, message = self.validator.validate_requirements_text(text)
            assert is_valid is False
            assert expected_message in message

    def test_validate_jira_credentials_valid(self):
        """Test valid Jira credentials validation."""
        # Test API token authentication
        is_valid, message = self.validator.validate_jira_credentials(
            base_url="https://company.atlassian.net",
            email="user@company.com",
            api_token="abcd1234567890",
            auth_type="api_token",
        )
        assert is_valid is True
        assert message == "Valid"

        # Test basic authentication
        is_valid, message = self.validator.validate_jira_credentials(
            base_url="https://company.atlassian.net",
            username="testuser",
            password="testpass",
            auth_type="basic",
        )
        assert is_valid is True
        assert message == "Valid"

        # Test PAT authentication
        is_valid, message = self.validator.validate_jira_credentials(
            base_url="https://company.atlassian.net",
            personal_access_token="abcd1234567890",
            auth_type="pat",
        )
        assert is_valid is True
        assert message == "Valid"

    def test_validate_jira_credentials_invalid(self):
        """Test invalid Jira credentials validation."""
        test_cases = [
            # Invalid URL
            (
                "invalid-url",
                "user@company.com",
                "token123",
                None,
                None,
                None,
                "api_token",
                "Invalid Jira base URL format",
            ),
            # Invalid email for API token auth
            (
                "https://company.atlassian.net",
                "invalid-email",
                "token123",
                None,
                None,
                None,
                "api_token",
                "Invalid email format",
            ),
            # Invalid API token
            (
                "https://company.atlassian.net",
                "user@company.com",
                "short",
                None,
                None,
                None,
                "api_token",
                "Invalid API token format",
            ),
            # Missing base URL
            (
                "",
                "user@company.com",
                "token123",
                None,
                None,
                None,
                "api_token",
                "Base URL is required",
            ),
            # Missing credentials for basic auth
            (
                "https://company.atlassian.net",
                None,
                None,
                "testuser",
                None,
                None,
                "basic",
                "Username and password are required",
            ),
            (
                "https://company.atlassian.net",
                None,
                None,
                None,
                "testpass",
                None,
                "basic",
                "Username and password are required",
            ),
            # Missing PAT
            (
                "https://company.atlassian.net",
                None,
                None,
                None,
                None,
                None,
                "pat",
                "Personal Access Token is required",
            ),
        ]

        for (
            base_url,
            email,
            api_token,
            username,
            password,
            pat,
            auth_type,
            expected_message,
        ) in test_cases:
            is_valid, message = self.validator.validate_jira_credentials(
                base_url=base_url,
                email=email,
                api_token=api_token,
                username=username,
                password=password,
                personal_access_token=pat,
                auth_type=auth_type,
            )
            assert is_valid is False
            assert expected_message in message

    def test_validate_api_key_openai_valid(self):
        """Test valid OpenAI API key validation."""
        is_valid, message = self.validator.validate_api_key(
            "sk-1234567890abcdef1234567890abcdef", "openai"
        )

        assert is_valid is True
        assert message == "Valid"

    def test_validate_api_key_openai_invalid(self):
        """Test invalid OpenAI API key validation."""
        test_cases = [
            ("invalid-key", "Invalid OpenAI API key format"),
            ("sk-short", "Invalid OpenAI API key format"),
            ("", "API key is required"),
        ]

        for api_key, expected_message in test_cases:
            is_valid, message = self.validator.validate_api_key(api_key, "openai")
            assert is_valid is False
            assert expected_message in message


class TestSecurityValidator:
    """Test security validation functionality."""

    def setup_method(self):
        self.validator = SecurityValidator()

    def test_sanitize_string_basic(self):
        """Test basic string sanitization."""
        test_string = "Normal text content"
        result = self.validator.sanitize_string(test_string)
        assert result == "Normal text content"

    def test_sanitize_string_html_escape(self):
        """Test HTML escaping in string sanitization."""
        test_string = "<script>alert('xss')</script>"
        result = self.validator.sanitize_string(test_string)
        assert "&lt;script&gt;" in result
        assert "&lt;/script&gt;" in result

    def test_sanitize_string_malicious_patterns(self):
        """Test removal of malicious patterns."""
        test_cases = [
            "<script>alert('xss')</script>",
            "javascript:alert('xss')",
            "onclick=alert('xss')",
            "SELECT * FROM users",
            "../../../etc/passwd",
            "eval(malicious_code)",
        ]

        for test_string in test_cases:
            result = self.validator.sanitize_string(test_string)
            assert "[REMOVED_SUSPICIOUS_CONTENT]" in result or "&lt;" in result

    def test_sanitize_string_length_limit(self):
        """Test string length limiting."""
        long_string = "a" * 15000
        result = self.validator.sanitize_string(long_string, max_length=1000)
        assert len(result) == 1000

    def test_validate_no_banned_tools_clean(self):
        """Test validation with clean text (no banned tools)."""
        clean_text = (
            "This is a normal requirement about automation using Python and FastAPI."
        )
        assert self.validator.validate_no_banned_tools(clean_text) is True

    def test_validate_no_banned_tools_with_banned(self):
        """Test validation with banned tools."""
        banned_text = "We should use metasploit to test the security of our system."
        assert self.validator.validate_no_banned_tools(banned_text) is False

    def test_sanitize_dict_recursive(self):
        """Test recursive dictionary sanitization."""
        test_dict = {
            "normal_key": "normal_value",
            "<script>": "malicious_value",
            "nested": {
                "inner_key": "<script>alert('xss')</script>",
                "safe_key": "safe_value",
            },
        }

        result = self.validator.sanitize_dict(test_dict)

        # Check that malicious content is escaped/removed
        assert any(
            "&lt;" in str(v) or "[REMOVED_SUSPICIOUS_CONTENT]" in str(v)
            for v in result.values()
        )
        assert "normal_value" in str(result)
        assert "safe_value" in str(result)

    def test_sanitize_list_recursive(self):
        """Test recursive list sanitization."""
        test_list = [
            "normal_item",
            "<script>alert('xss')</script>",
            {"nested_key": "javascript:alert('xss')"},
            ["nested_list", "<script>"],
        ]

        result = self.validator.sanitize_list(test_list)

        # Check that malicious content is handled
        assert "normal_item" in result
        assert any(
            "&lt;" in str(item) or "[REMOVED_SUSPICIOUS_CONTENT]" in str(item)
            for item in result
        )


class TestSecurityHeaders:
    """Test security headers functionality."""

    def test_get_security_headers(self):
        """Test getting security headers."""
        headers = SecurityHeaders.get_security_headers()

        expected_headers = [
            "X-Frame-Options",
            "X-Content-Type-Options",
            "X-XSS-Protection",
            "Referrer-Policy",
            "Content-Security-Policy",
            "Strict-Transport-Security",
            "Permissions-Policy",
            "Server",
        ]

        for header in expected_headers:
            assert header in headers
            assert headers[header] is not None

    def test_get_api_response_headers(self):
        """Test getting API-specific response headers."""
        headers = SecurityHeaders.get_api_response_headers()

        # Should include all security headers plus API-specific ones
        assert "Cache-Control" in headers
        assert "Pragma" in headers
        assert "Expires" in headers
        assert "X-Frame-Options" in headers


class TestRateLimitMiddleware:
    """Test rate limiting middleware."""

    def test_rate_limit_middleware_creation(self):
        """Test rate limit middleware can be created."""
        app = FastAPI()
        middleware = RateLimitMiddleware(app, calls_per_minute=10, calls_per_hour=100)

        assert middleware.calls_per_minute == 10
        assert middleware.calls_per_hour == 100

    def test_get_client_ip_forwarded(self):
        """Test client IP extraction from forwarded headers."""
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        # Mock request with forwarded header
        mock_request = Mock()
        mock_request.headers = {"X-Forwarded-For": "192.168.1.1, 10.0.0.1"}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        ip = middleware._get_client_ip(mock_request)
        assert ip == "192.168.1.1"

    def test_get_client_ip_direct(self):
        """Test client IP extraction from direct connection."""
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        # Mock request without forwarded headers
        mock_request = Mock()
        mock_request.headers = {}
        mock_request.client = Mock()
        mock_request.client.host = "127.0.0.1"

        ip = middleware._get_client_ip(mock_request)
        assert ip == "127.0.0.1"

    def test_cleanup_old_requests(self):
        """Test cleanup of old requests."""
        app = FastAPI()
        middleware = RateLimitMiddleware(app)

        current_time = time.time()
        requests_list = [
            current_time - 120,  # 2 minutes ago (should be removed)
            current_time - 30,  # 30 seconds ago (should remain)
            current_time - 10,  # 10 seconds ago (should remain)
        ]

        middleware._cleanup_old_requests(requests_list, 60)  # 1 minute window

        assert len(requests_list) == 2
        assert requests_list[0] == current_time - 30
        assert requests_list[1] == current_time - 10


class TestSecurityMiddleware:
    """Test general security middleware."""

    def test_security_middleware_creation(self):
        """Test security middleware can be created."""
        app = FastAPI()
        middleware = SecurityMiddleware(app, max_request_size=1024)

        assert middleware.max_request_size == 1024


@pytest.mark.asyncio
async def test_security_integration():
    """Test security integration with FastAPI."""
    from app.api import app

    client = TestClient(app)

    # Test health endpoint (should work without issues)
    response = client.get("/health")
    assert response.status_code == 200

    # Check that security headers are present
    assert "X-Frame-Options" in response.headers
    assert "X-Content-Type-Options" in response.headers

    # Test invalid session ID
    response = client.get("/status/invalid-session-id")
    assert response.status_code == 400
    assert "Invalid session ID format" in response.json()["message"]
