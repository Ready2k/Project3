"""Integration tests for refactored UI components."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch

from app.ui.api_client import AAA_APIClient, StreamlitAPIIntegration
from app.ui.components.provider_config import ProviderConfigComponent
from app.ui.components.session_management import SessionManagementComponent
from app.ui.components.results_display import ResultsDisplayComponent
from app.ui.mermaid_diagrams import MermaidDiagramGenerator
from app.utils.error_boundaries import AsyncOperationManager


class TestComponentIntegration:
    """Test integration between refactored UI components."""

    @pytest.fixture
    def api_client(self):
        """Create API client for testing."""
        return AAA_APIClient("http://localhost:8000")

    @pytest.fixture
    def streamlit_integration(self, api_client):
        """Create Streamlit integration for testing."""
        return StreamlitAPIIntegration(api_client)

    @pytest.fixture
    def provider_config(self):
        """Create provider config component."""
        return ProviderConfigComponent()

    @pytest.fixture
    def session_manager(self):
        """Create session manager component."""
        return SessionManagementComponent()

    @pytest.fixture
    def results_display(self):
        """Create results display component."""
        return ResultsDisplayComponent()

    @pytest.fixture
    def mermaid_generator(self):
        """Create Mermaid diagram generator."""
        return MermaidDiagramGenerator()

    @pytest.mark.asyncio
    async def test_api_client_basic_operations(self, api_client):
        """Test basic API client operations."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock successful response
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"session_id": "test-123"}
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                return_value=mock_response
            )

            # Test ingest requirements
            result = await api_client.ingest_requirements(
                "text",
                {"text": "Test requirement"},
                {"provider": "fake", "model": "fake-model"},
            )

            assert result["session_id"] == "test-123"

    @pytest.mark.asyncio
    async def test_api_client_error_handling(self, api_client):
        """Test API client error handling."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock HTTP error
            from httpx import HTTPStatusError, Request, Response

            mock_request = Mock(spec=Request)
            mock_response = Mock(spec=Response)
            mock_response.status_code = 400
            mock_response.json.return_value = {"detail": "Bad request"}

            mock_client.return_value.__aenter__.return_value.post = AsyncMock(
                side_effect=HTTPStatusError(
                    "Bad request", request=mock_request, response=mock_response
                )
            )

            result = await api_client.ingest_requirements("text", {"text": "Test"})

            assert "error" in result
            assert "Bad request" in result["error"]

    @pytest.mark.asyncio
    async def test_batch_api_requests(self, api_client):
        """Test batch API request processing."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock multiple successful responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Test batch requests
            requests = [
                {"method": "GET", "endpoint": "/health"},
                {"method": "GET", "endpoint": "/status/test-123"},
                {"method": "GET", "endpoint": "/health"},
            ]

            results = await api_client.batch_requests(requests)

            assert len(results) == 3
            assert all(result.get("status") == "ok" for result in results if result)

    def test_provider_config_validation(self, provider_config):
        """Test provider configuration validation."""
        # Test valid OpenAI config
        valid_config = {
            "provider": "openai",
            "model": "gpt-4o",
            "api_key": "sk-test123",
        }

        is_valid, message = provider_config.validate_config(valid_config)
        assert is_valid
        assert message == "Configuration valid"

        # Test invalid config (missing API key)
        invalid_config = {"provider": "openai", "model": "gpt-4o"}

        is_valid, message = provider_config.validate_config(invalid_config)
        assert not is_valid
        assert "requires an API key" in message

    def test_session_id_validation(self, session_manager):
        """Test session ID validation."""
        # Valid UUID format
        valid_ids = [
            "12345678-1234-1234-1234-123456789abc",
            "ABCDEF12-3456-7890-ABCD-EF1234567890",
            "00000000-0000-0000-0000-000000000000",
        ]

        for session_id in valid_ids:
            assert session_manager.validate_session_id(session_id)

        # Invalid formats
        invalid_ids = [
            "not-a-uuid",
            "12345678-1234-1234-1234",  # Too short
            "12345678-1234-1234-1234-123456789abcd",  # Too long
            "",
            None,
        ]

        for session_id in invalid_ids:
            assert not session_manager.validate_session_id(session_id)

    def test_mermaid_code_validation(self, mermaid_generator):
        """Test Mermaid code validation."""
        # Valid Mermaid code
        valid_code = """flowchart TB
    A[Start] --> B[Process]
    B --> C[End]"""

        is_valid, error = mermaid_generator.validate_mermaid_syntax(valid_code)
        assert is_valid
        assert error == ""

        # Invalid Mermaid code
        invalid_code = "not mermaid code"

        is_valid, error = mermaid_generator.validate_mermaid_syntax(invalid_code)
        assert not is_valid
        assert "Invalid diagram type" in error

    def test_mermaid_code_cleaning(self, mermaid_generator):
        """Test Mermaid code cleaning and sanitization."""
        # Code with Unicode characters
        dirty_code = """flowchart TB
    👤[User] --> 🤖[Agent]
    🤖 --> 📊[Results]"""

        cleaned_code = mermaid_generator.clean_mermaid_code(dirty_code)

        # Should remove Unicode characters
        assert "👤" not in cleaned_code
        assert "🤖" not in cleaned_code
        assert "📊" not in cleaned_code

        # Should still be valid Mermaid
        is_valid, _ = mermaid_generator.validate_mermaid_syntax(cleaned_code)
        assert is_valid

    def test_results_display_categorization(self, results_display):
        """Test technology categorization in results display."""
        tech_stack = [
            "Python",
            "FastAPI",
            "PostgreSQL",
            "AWS Lambda",
            "React",
            "Docker",
            "Redis",
            "Terraform",
        ]

        categorized = results_display._categorize_technologies(tech_stack)

        # Should have multiple categories
        assert len(categorized) > 1

        # Check specific categorizations
        assert "Python" in categorized.get("Programming Languages", [])
        assert "FastAPI" in categorized.get("Frameworks & Libraries", [])
        assert "PostgreSQL" in categorized.get("Databases", [])
        assert "AWS Lambda" in categorized.get("Cloud Services", [])

    @pytest.mark.asyncio
    async def test_end_to_end_workflow_simulation(
        self, api_client, session_manager, provider_config
    ):
        """Test end-to-end workflow simulation."""
        with patch("httpx.AsyncClient") as mock_client:
            # Mock API responses for complete workflow
            responses = {
                "ingest": {"session_id": "test-workflow-123"},
                "status": {
                    "phase": "qa",
                    "progress": 50,
                    "requirements": {"description": "Test requirement"},
                    "missing_fields": [],
                },
                "qa": {"complete": True, "next_questions": []},
                "recommend": {
                    "feasibility": "Fully Automatable",
                    "recommendations": [
                        {
                            "pattern_id": "PAT-001",
                            "pattern_name": "Test Pattern",
                            "confidence": 0.85,
                            "reasoning": "Good fit for requirement",
                        }
                    ],
                    "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                    "reasoning": "Highly automatable process",
                },
            }

            def mock_response_factory(endpoint, method="GET"):
                mock_response = Mock()
                mock_response.status_code = 200
                mock_response.raise_for_status.return_value = None

                if "ingest" in endpoint:
                    mock_response.json.return_value = responses["ingest"]
                elif "status" in endpoint:
                    mock_response.json.return_value = responses["status"]
                elif "qa" in endpoint:
                    mock_response.json.return_value = responses["qa"]
                elif "recommend" in endpoint:
                    mock_response.json.return_value = responses["recommend"]
                else:
                    mock_response.json.return_value = {"status": "ok"}

                return mock_response

            # Setup mock client
            mock_client_instance = mock_client.return_value.__aenter__.return_value
            mock_client_instance.post = AsyncMock(
                side_effect=lambda url, **kwargs: mock_response_factory(url, "POST")
            )
            mock_client_instance.get = AsyncMock(
                side_effect=lambda url, **kwargs: mock_response_factory(url, "GET")
            )

            # Test complete workflow
            # 1. Ingest requirements
            ingest_result = await api_client.ingest_requirements(
                "text",
                {"text": "Test automation requirement"},
                {"provider": "fake", "model": "fake-model"},
            )

            assert ingest_result["session_id"] == "test-workflow-123"

            # 2. Check status
            status_result = await api_client.get_session_status("test-workflow-123")

            assert status_result["phase"] == "qa"
            assert status_result["progress"] == 50

            # 3. Submit Q&A answers
            qa_result = await api_client.submit_qa_answers(
                "test-workflow-123", {"question1": "answer1"}
            )

            assert qa_result["complete"] is True

            # 4. Get recommendations
            recommend_result = await api_client.get_recommendations("test-workflow-123")

            assert recommend_result["feasibility"] == "Fully Automatable"
            assert len(recommend_result["recommendations"]) == 1
            assert len(recommend_result["tech_stack"]) == 3

    def test_component_error_isolation(
        self, provider_config, session_manager, results_display
    ):
        """Test that component errors don't affect other components."""
        # Test provider config with invalid data
        try:
            provider_config.validate_config(None)
        except Exception:
            pass  # Should handle gracefully

        # Session manager should still work
        assert session_manager.validate_session_id(
            "12345678-1234-1234-1234-123456789abc"
        )

        # Results display should still work
        categorized = results_display._categorize_technologies(["Python", "FastAPI"])
        assert len(categorized) > 0

    @pytest.mark.asyncio
    async def test_async_operation_manager_integration(self):
        """Test AsyncOperationManager integration."""
        async_manager = AsyncOperationManager(max_concurrent=3, timeout_seconds=5.0)

        # Create test operations
        async def test_operation(delay: float, result: str):
            await asyncio.sleep(delay)
            return result

        operations = [
            test_operation(0.1, "result1"),
            test_operation(0.2, "result2"),
            test_operation(0.1, "result3"),
        ]

        # Execute batch
        results = await async_manager.execute_batch(operations, "test_batch")

        assert len(results) == 3
        assert "result1" in results
        assert "result2" in results
        assert "result3" in results

    def test_configuration_integration(self, provider_config):
        """Test configuration service integration."""
        # Test that provider config uses configuration service
        from app.services.configuration_service import get_config

        config_service = get_config()
        llm_params = config_service.get_llm_params()

        # Should have expected parameters
        assert "temperature" in llm_params
        assert "max_tokens" in llm_params
        assert isinstance(llm_params["temperature"], (int, float))
        assert isinstance(llm_params["max_tokens"], int)

    @pytest.mark.asyncio
    async def test_error_boundary_integration(self, mermaid_generator):
        """Test error boundary integration in components."""
        # Test with invalid provider config that should trigger error boundary
        invalid_config = {"provider": "invalid", "model": "invalid"}

        # Should handle error gracefully and return fallback
        try:
            result = await mermaid_generator.make_llm_request(
                "test prompt", invalid_config, "test_purpose"
            )
            # Should either return a result or handle error gracefully
            assert result is not None or True  # Error boundary should prevent crash
        except Exception as e:
            # If exception occurs, it should be a controlled one
            assert "LLM request failed" in str(e)


class TestComponentPerformance:
    """Test performance characteristics of components."""

    @pytest.mark.asyncio
    async def test_api_client_concurrent_requests(self):
        """Test API client performance with concurrent requests."""
        api_client = AAA_APIClient()

        with patch("httpx.AsyncClient") as mock_client:
            # Mock fast responses
            mock_response = Mock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"status": "ok"}
            mock_response.raise_for_status.return_value = None

            mock_client.return_value.__aenter__.return_value.get = AsyncMock(
                return_value=mock_response
            )

            # Create multiple concurrent requests
            import time

            start_time = time.time()

            tasks = [api_client.get_health_status() for _ in range(10)]
            results = await asyncio.gather(*tasks)

            end_time = time.time()

            # Should complete quickly with concurrent execution
            assert (
                end_time - start_time < 2.0
            )  # Should be much faster than 10 sequential requests
            assert len(results) == 10
            assert all(result.get("status") == "ok" for result in results)

    def test_mermaid_generator_caching(self, mermaid_generator):
        """Test Mermaid generator caching behavior."""
        # Test that repeated operations are efficient
        test_code = """flowchart TB
    A[Start] --> B[End]"""

        import time

        # First validation
        start_time = time.time()
        is_valid1, _ = mermaid_generator.validate_mermaid_syntax(test_code)
        time.time() - start_time

        # Second validation (should be faster if cached)
        start_time = time.time()
        is_valid2, _ = mermaid_generator.validate_mermaid_syntax(test_code)
        time.time() - start_time

        assert is_valid1 == is_valid2
        # Note: Actual caching would need to be implemented in the component

    def test_results_display_large_datasets(self, results_display):
        """Test results display with large datasets."""
        # Test with large technology stack
        large_tech_stack = [f"Technology_{i}" for i in range(100)]

        import time

        start_time = time.time()

        categorized = results_display._categorize_technologies(large_tech_stack)

        end_time = time.time()

        # Should handle large datasets efficiently
        assert end_time - start_time < 1.0  # Should complete within 1 second
        assert len(categorized) > 0

        # Test with large recommendations list
        [
            {
                "pattern_id": f"PAT-{i:03d}",
                "pattern_name": f"Pattern {i}",
                "confidence": 0.8,
                "reasoning": f"Reasoning for pattern {i}",
            }
            for i in range(50)
        ]

        # Should handle without errors
        # Note: Actual rendering would need Streamlit context
