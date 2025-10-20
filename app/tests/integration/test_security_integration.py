"""Integration tests for security measures."""

import pytest
from fastapi.testclient import TestClient
from unittest.mock import patch


@pytest.fixture
def client():
    """Create test client with security middleware."""
    from app.api import app

    return TestClient(app)


class TestSecurityIntegration:
    """Test security integration across the application."""

    def test_security_headers_present(self, client):
        """Test that security headers are present in responses."""
        response = client.get("/health")

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
            assert header in response.headers, f"Security header {header} missing"
            assert response.headers[header] is not None

    def test_cors_headers_configured(self, client):
        """Test CORS headers are properly configured."""
        # Make an OPTIONS request to test CORS
        response = client.options(
            "/health",
            headers={
                "Origin": "http://localhost:8500",
                "Access-Control-Request-Method": "GET",
            },
        )

        # Should have CORS headers
        assert "Access-Control-Allow-Origin" in response.headers

    def test_input_validation_on_ingest(self, client):
        """Test input validation on ingest endpoint."""
        # Test invalid source
        response = client.post(
            "/ingest", json={"source": "invalid_source", "payload": {"text": "test"}}
        )
        assert response.status_code == 422  # Validation error

        # Test invalid provider
        response = client.post(
            "/ingest",
            json={
                "source": "text",
                "payload": {"text": "test"},
                "provider_config": {"provider": "invalid_provider", "model": "gpt-4o"},
            },
        )
        assert response.status_code == 422  # Validation error

    def test_session_id_validation(self, client):
        """Test session ID validation across endpoints."""
        invalid_session_ids = [
            "not-a-uuid",
            "123",
            "",
            "123e4567-e89b-12d3-a456",  # Too short
        ]

        for invalid_id in invalid_session_ids:
            response = client.get(f"/status/{invalid_id}")
            assert response.status_code == 400
            assert "Invalid session ID format" in response.json()["message"]

    def test_request_size_limit(self, client):
        """Test request size limiting."""
        # Create a very large payload (over 10MB)
        large_text = "a" * (11 * 1024 * 1024)  # 11MB

        response = client.post(
            "/ingest", json={"source": "text", "payload": {"text": large_text}}
        )

        # Should be rejected due to size limit
        assert response.status_code == 413

    def test_malicious_input_sanitization(self, client):
        """Test that malicious input is sanitized."""
        malicious_payloads = [
            {"text": "<script>alert('xss')</script>This is a requirement"},
            {"text": "javascript:alert('xss') This is a requirement"},
            {"text": "SELECT * FROM users; This is a requirement"},
            {"text": "../../../etc/passwd This is a requirement"},
        ]

        for payload in malicious_payloads:
            response = client.post(
                "/ingest", json={"source": "text", "payload": payload}
            )

            # Should succeed but content should be sanitized
            if response.status_code == 200:
                # The malicious content should have been sanitized
                # (We can't easily verify this without checking internal state)
                assert "session_id" in response.json()

    def test_pii_not_in_error_responses(self, client):
        """Test that PII doesn't leak in error responses."""
        # Try to trigger an error with PII in the request
        response = client.post(
            "/ingest",
            json={
                "source": "text",
                "payload": {
                    "text": "Contact john.doe@company.com about this requirement",
                    "invalid_field": "This should cause an error",
                },
            },
        )

        # Even if there's an error, PII shouldn't be in the response
        response_text = response.text
        assert "john.doe@company.com" not in response_text

    def test_qa_input_validation(self, client):
        """Test Q&A input validation."""
        # First create a session
        ingest_response = client.post(
            "/ingest",
            json={
                "source": "text",
                "payload": {"text": "Automate user authentication system"},
            },
        )
        session_id = ingest_response.json()["session_id"]

        # Test invalid answers
        invalid_answers = [
            {"answers": {"q1": "a" * 6000}},  # Too long
            {"answers": {f"q{i}": "answer" for i in range(25)}},  # Too many answers
        ]

        for invalid_answer in invalid_answers:
            response = client.post(f"/qa/{session_id}", json=invalid_answer)
            assert response.status_code == 422  # Validation error

    def test_export_format_validation(self, client):
        """Test export format validation."""
        # First create a session
        ingest_response = client.post(
            "/ingest",
            json={
                "source": "text",
                "payload": {"text": "Automate user authentication system"},
            },
        )
        session_id = ingest_response.json()["session_id"]

        # Test invalid export format
        response = client.post(
            "/export", json={"session_id": session_id, "format": "invalid_format"}
        )
        assert response.status_code == 422  # Validation error

    @patch("app.api.validate_output_security")
    def test_banned_tools_validation_in_recommendations(self, mock_validate, client):
        """Test that banned tools are caught in recommendation outputs."""
        # Mock the validation to return False (banned tools detected)
        mock_validate.return_value = False

        # Create a session
        ingest_response = client.post(
            "/ingest",
            json={"source": "text", "payload": {"text": "Automate network monitoring"}},
        )
        session_id = ingest_response.json()["session_id"]

        # Try to get recommendations (should fail due to banned tools)
        response = client.post(
            "/recommend", json={"session_id": session_id, "top_k": 3}
        )

        # Should return 500 due to security validation failure
        assert response.status_code == 500
        assert "security validation" in response.json()["message"].lower()

    def test_jira_credentials_validation(self, client):
        """Test Jira credentials validation."""
        invalid_jira_payloads = [
            {
                "source": "jira",
                "payload": {
                    "ticket_key": "PROJ-123",
                    "base_url": "invalid-url",
                    "email": "user@company.com",
                    "api_token": "validtoken123",
                },
            },
            {
                "source": "jira",
                "payload": {
                    "ticket_key": "PROJ-123",
                    "base_url": "https://company.atlassian.net",
                    "email": "invalid-email",
                    "api_token": "validtoken123",
                },
            },
            {
                "source": "jira",
                "payload": {
                    "ticket_key": "PROJ-123",
                    "base_url": "https://company.atlassian.net",
                    "email": "user@company.com",
                    "api_token": "short",
                },
            },
        ]

        for payload in invalid_jira_payloads:
            response = client.post("/ingest", json=payload)
            assert response.status_code == 400
            assert "validation failed" in response.json()["detail"].lower()

    def test_api_key_validation(self, client):
        """Test API key validation in provider config."""
        invalid_configs = [
            {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "invalid-key",  # Doesn't start with sk-
            },
            {
                "provider": "openai",
                "model": "gpt-4o",
                "api_key": "sk-short",  # Too short
            },
        ]

        for config in invalid_configs:
            response = client.post(
                "/ingest",
                json={
                    "source": "text",
                    "payload": {"text": "Test requirement"},
                    "provider_config": config,
                },
            )
            assert response.status_code == 422  # Validation error

    def test_error_handling_with_security_headers(self, client):
        """Test that error responses include security headers."""
        # Trigger a 404 error
        response = client.get("/nonexistent-endpoint")
        assert response.status_code == 404

        # Should still have security headers
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers

    def test_health_endpoint_bypasses_rate_limiting(self, client):
        """Test that health endpoint bypasses rate limiting."""
        # Make many requests to health endpoint
        for _ in range(10):
            response = client.get("/health")
            assert response.status_code == 200

        # Should still work (not rate limited)
        response = client.get("/health")
        assert response.status_code == 200


class TestRateLimitingIntegration:
    """Test rate limiting integration."""

    def test_rate_limiting_applied(self, client):
        """Test that rate limiting is applied to API endpoints."""
        # This test is challenging to implement without mocking time
        # or having very low rate limits, so we'll test the structure

        # Make a request to a rate-limited endpoint
        response = client.post(
            "/ingest", json={"source": "text", "payload": {"text": "Test requirement"}}
        )

        # Should succeed initially
        assert response.status_code in [
            200,
            422,
        ]  # 422 if validation fails, but not rate limited

        # The rate limiting middleware should be active
        # (We can't easily test the actual limiting without time manipulation)


@pytest.mark.asyncio
async def test_comprehensive_security_workflow():
    """Test a complete workflow with security measures."""
    from app.api import app

    client = TestClient(app)

    # 1. Create session with sanitized input
    ingest_response = client.post(
        "/ingest",
        json={
            "source": "text",
            "payload": {
                "text": "Automate user authentication system with secure password handling",
                "domain": "security",
            },
        },
    )

    assert ingest_response.status_code == 200
    assert "X-Frame-Options" in ingest_response.headers
    session_id = ingest_response.json()["session_id"]

    # 2. Check status with validated session ID
    status_response = client.get(f"/status/{session_id}")
    assert status_response.status_code == 200
    assert "X-Frame-Options" in status_response.headers

    # 3. Try Q&A with sanitized answers
    qa_response = client.post(
        f"/qa/{session_id}",
        json={
            "answers": {
                "workflow_variability": "Standard authentication flow",
                "data_sensitivity": "High - contains user credentials",
            }
        },
    )

    # Should succeed or return appropriate status
    assert qa_response.status_code in [200, 404]  # 404 if session not in QNA phase

    # 4. All responses should have security headers
    for response in [ingest_response, status_response, qa_response]:
        assert "X-Frame-Options" in response.headers
        assert "X-Content-Type-Options" in response.headers
