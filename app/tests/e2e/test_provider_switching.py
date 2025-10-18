"""End-to-end tests for provider switching and export functionality."""

import pytest
import asyncio
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from streamlit_app import AutomatedAIAssessmentUI
from app.llm.fakes import FakeLLM
from app.llm.openai_provider import OpenAIProvider
from app.llm.claude_provider import ClaudeProvider
from app.llm.bedrock_provider import BedrockProvider
from app.llm.internal_provider import InternalProvider


class TestProviderSwitching:
    """Test switching between different LLM providers."""

    @pytest.fixture
    def ui_app(self):
        """Create UI app instance."""
        return AutomatedAIAssessmentUI()

    @pytest.fixture
    def mock_session_state(self):
        """Mock Streamlit session state."""

        class MockSessionState:
            def __init__(self):
                self.session_id = "test-session-123"
                self.current_provider = "openai"
                self.provider_config = {
                    "openai": {"model": "gpt-4", "api_key": "test-key"},
                    "claude": {"model": "claude-3-sonnet", "api_key": "test-key"},
                    "bedrock": {"model": "claude-3-sonnet", "region": "us-east-1"},
                    "internal": {
                        "base_url": "http://localhost:8080",
                        "model": "internal-model",
                    },
                }
                self.requirements = "Test automation requirements"
                self.qa_questions = []
                self.recommendations = []

        return MockSessionState()

    @pytest.mark.asyncio
    async def test_openai_provider_switching(self, ui_app, mock_session_state):
        """Test switching to OpenAI provider."""
        with patch("streamlit.session_state", mock_session_state):
            with patch("app.llm.openai_provider.OpenAI") as mock_openai:
                # Mock OpenAI client
                mock_client = Mock()
                mock_client.chat.completions.create = AsyncMock(
                    return_value=Mock(
                        choices=[Mock(message=Mock(content="Test response"))],
                        usage=Mock(total_tokens=100),
                    )
                )
                mock_openai.return_value = mock_client

                # Test provider creation
                provider = ui_app._create_llm_provider(
                    "openai", mock_session_state.provider_config["openai"]
                )

                assert isinstance(provider, OpenAIProvider)

                # Test connection
                connection_result = await provider.test_connection()
                assert connection_result is True

    @pytest.mark.asyncio
    async def test_claude_provider_switching(self, ui_app, mock_session_state):
        """Test switching to Claude provider."""
        with patch("streamlit.session_state", mock_session_state):
            with patch("app.llm.claude_provider.Anthropic") as mock_anthropic:
                # Mock Anthropic client
                mock_client = Mock()
                mock_client.messages.create = AsyncMock(
                    return_value=Mock(
                        content=[Mock(text="Test response")],
                        usage=Mock(input_tokens=50, output_tokens=50),
                    )
                )
                mock_anthropic.return_value = mock_client

                # Test provider creation
                provider = ui_app._create_llm_provider(
                    "claude", mock_session_state.provider_config["claude"]
                )

                assert isinstance(provider, ClaudeProvider)

                # Test generation
                response = await provider.generate("Test prompt")
                assert response == "Test response"

    @pytest.mark.asyncio
    async def test_bedrock_provider_switching(self, ui_app, mock_session_state):
        """Test switching to Bedrock provider."""
        with patch("streamlit.session_state", mock_session_state):
            with patch("app.llm.bedrock_provider.boto3") as mock_boto3:
                # Mock Bedrock client
                mock_client = Mock()
                mock_client.invoke_model = Mock(
                    return_value={
                        "body": Mock(
                            read=Mock(return_value=b'{"completion": "Test response"}')
                        )
                    }
                )
                mock_boto3.client.return_value = mock_client

                # Test provider creation
                provider = ui_app._create_llm_provider(
                    "bedrock", mock_session_state.provider_config["bedrock"]
                )

                assert isinstance(provider, BedrockProvider)

    @pytest.mark.asyncio
    async def test_internal_provider_switching(self, ui_app, mock_session_state):
        """Test switching to internal provider."""
        with patch("streamlit.session_state", mock_session_state):
            with patch("httpx.AsyncClient") as mock_httpx:
                # Mock HTTP client
                mock_client = Mock()
                mock_client.post = AsyncMock(
                    return_value=Mock(
                        json=Mock(return_value={"response": "Test response"}),
                        status_code=200,
                    )
                )
                mock_httpx.return_value.__aenter__.return_value = mock_client

                # Test provider creation
                provider = ui_app._create_llm_provider(
                    "internal", mock_session_state.provider_config["internal"]
                )

                assert isinstance(provider, InternalProvider)

                # Test connection
                connection_result = await provider.test_connection()
                assert connection_result is True

    @pytest.mark.asyncio
    async def test_provider_error_handling(self, ui_app, mock_session_state):
        """Test error handling when provider fails."""
        with patch("streamlit.session_state", mock_session_state):
            with patch("app.llm.openai_provider.OpenAI") as mock_openai:
                # Mock OpenAI client to raise exception
                mock_openai.side_effect = Exception("API key invalid")

                # Should handle error gracefully
                try:
                    provider = ui_app._create_llm_provider(
                        "openai", mock_session_state.provider_config["openai"]
                    )
                    await provider.test_connection()
                except Exception as e:
                    assert "API key invalid" in str(e)

    def test_provider_configuration_validation(self, ui_app):
        """Test provider configuration validation."""
        # Test valid configurations
        valid_configs = {
            "openai": {"model": "gpt-4", "api_key": "sk-test"},
            "claude": {"model": "claude-3-sonnet", "api_key": "test-key"},
            "bedrock": {"model": "claude-3-sonnet", "region": "us-east-1"},
            "internal": {"base_url": "http://localhost:8080", "model": "test-model"},
        }

        for provider_type, config in valid_configs.items():
            # Should not raise exception
            provider = ui_app._create_llm_provider(provider_type, config)
            assert provider is not None

    @pytest.mark.asyncio
    async def test_provider_switching_workflow(self, ui_app, mock_session_state):
        """Test complete provider switching workflow."""
        with patch("streamlit.session_state", mock_session_state):
            with patch("streamlit.selectbox") as mock_selectbox, patch(
                "streamlit.text_input"
            ) as mock_text_input, patch("streamlit.button") as mock_button, patch(
                "streamlit.success"
            ) as mock_success, patch(
                "streamlit.error"
            ):

                # Mock user selections
                mock_selectbox.return_value = "claude"
                mock_text_input.return_value = "test-api-key"
                mock_button.return_value = True

                # Mock provider creation and testing
                with patch.object(
                    ui_app, "_create_llm_provider"
                ) as mock_create, patch.object(
                    ui_app, "test_provider_connection"
                ) as mock_test:

                    mock_provider = Mock()
                    mock_create.return_value = mock_provider
                    mock_test.return_value = AsyncMock(return_value=True)

                    # Test provider configuration UI
                    ui_app.render_provider_config()

                    # Should create provider and test connection
                    mock_create.assert_called()

                    # Should show success message
                    if mock_button.return_value:
                        mock_success.assert_called()


class TestExportFunctionality:
    """Test export functionality end-to-end."""

    @pytest.fixture
    def ui_app(self):
        """Create UI app instance."""
        return AutomatedAIAssessmentUI()

    @pytest.fixture
    def mock_session_state_with_data(self):
        """Mock session state with analysis data."""

        class MockSessionState:
            def __init__(self):
                self.session_id = "export-test-session"
                self.requirements = "Test automation requirements"
                self.recommendations = [
                    {
                        "pattern_id": "PAT-001",
                        "pattern_name": "Test Pattern",
                        "feasibility": "Automatable",
                        "confidence": 0.85,
                        "reasoning": "Test reasoning",
                    }
                ]
                self.qa_exchanges = [
                    {"question": "What is the frequency?", "answer": "Daily"}
                ]

        return MockSessionState()

    @pytest.fixture
    def temp_export_dir(self):
        """Create temporary export directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)

    @pytest.mark.asyncio
    async def test_json_export_workflow(
        self, ui_app, mock_session_state_with_data, temp_export_dir
    ):
        """Test JSON export workflow."""
        with patch("streamlit.session_state", mock_session_state_with_data):
            with patch("app.api.get_export_service") as mock_get_service:
                # Mock export service
                mock_service = Mock()
                export_file = temp_export_dir / "test-export.json"
                mock_service.export_session = AsyncMock(
                    return_value={
                        "file_path": str(export_file),
                        "download_url": f"/downloads/{export_file.name}",
                        "file_size": 1024,
                    }
                )
                mock_get_service.return_value = mock_service

                # Create mock export file
                export_file.write_text('{"test": "data"}')

                # Test export
                result = await ui_app.export_results("json")

                assert result is not None
                assert "file_path" in result
                assert "download_url" in result
                mock_service.export_session.assert_called_once_with(
                    mock_session_state_with_data.session_id, "json"
                )

    @pytest.mark.asyncio
    async def test_markdown_export_workflow(
        self, ui_app, mock_session_state_with_data, temp_export_dir
    ):
        """Test Markdown export workflow."""
        with patch("streamlit.session_state", mock_session_state_with_data):
            with patch("app.api.get_export_service") as mock_get_service:
                # Mock export service
                mock_service = Mock()
                export_file = temp_export_dir / "test-export.md"
                mock_service.export_session = AsyncMock(
                    return_value={
                        "file_path": str(export_file),
                        "download_url": f"/downloads/{export_file.name}",
                        "file_size": 2048,
                    }
                )
                mock_get_service.return_value = mock_service

                # Create mock export file
                export_file.write_text("# Test Export\n\nTest content")

                # Test export
                result = await ui_app.export_results("markdown")

                assert result is not None
                assert "file_path" in result
                assert "download_url" in result
                mock_service.export_session.assert_called_once_with(
                    mock_session_state_with_data.session_id, "markdown"
                )

    def test_export_ui_workflow(self, ui_app, mock_session_state_with_data):
        """Test export UI workflow."""
        with patch("streamlit.session_state", mock_session_state_with_data):
            with patch("streamlit.subheader") as mock_subheader, patch(
                "streamlit.selectbox"
            ) as mock_selectbox, patch("streamlit.button") as mock_button, patch(
                "streamlit.download_button"
            ), patch(
                "streamlit.success"
            ) as mock_success:

                # Mock user selections
                mock_selectbox.return_value = "json"
                mock_button.return_value = True

                # Mock successful export
                with patch.object(ui_app, "export_results") as mock_export:
                    mock_export.return_value = AsyncMock(
                        return_value={
                            "file_path": "/tmp/test.json",
                            "download_url": "/downloads/test.json",
                            "file_size": 1024,
                        }
                    )

                    # Test export UI
                    ui_app.render_export_section()

                    # Should show export options
                    mock_subheader.assert_called()
                    mock_selectbox.assert_called()

                    # Should handle export button click
                    if mock_button.return_value:
                        mock_success.assert_called()

    @pytest.mark.asyncio
    async def test_export_error_handling(self, ui_app, mock_session_state_with_data):
        """Test export error handling."""
        with patch("streamlit.session_state", mock_session_state_with_data):
            with patch("app.api.get_export_service") as mock_get_service:
                # Mock export service to raise exception
                mock_service = Mock()
                mock_service.export_session = AsyncMock(
                    side_effect=Exception("Export failed")
                )
                mock_get_service.return_value = mock_service

                # Test export with error
                with patch("streamlit.error") as mock_error:
                    result = await ui_app.export_results("json")

                    assert result is None
                    mock_error.assert_called()

    def test_export_without_data(self, ui_app):
        """Test export when no analysis data exists."""

        class EmptySessionState:
            def __init__(self):
                self.session_id = None
                self.recommendations = []

        mock_session_state = EmptySessionState()

        with patch("streamlit.session_state", mock_session_state):
            with patch("streamlit.warning") as mock_warning:
                # Should show warning when no data to export
                ui_app.render_export_section()
                mock_warning.assert_called()

    @pytest.mark.asyncio
    async def test_large_export_workflow(self, ui_app, temp_export_dir):
        """Test export with large datasets."""

        # Create session state with large dataset
        class LargeDataSessionState:
            def __init__(self):
                self.session_id = "large-export-session"
                self.requirements = "Large dataset automation"
                self.recommendations = [
                    {
                        "pattern_id": f"PAT-{i:03d}",
                        "pattern_name": f"Pattern {i}",
                        "feasibility": "Automatable",
                        "confidence": 0.8 + (i % 2) * 0.1,
                        "reasoning": f"Detailed reasoning for pattern {i}" * 10,
                    }
                    for i in range(100)  # 100 recommendations
                ]
                self.qa_exchanges = [
                    {"question": f"Question {i}?", "answer": f"Answer {i}"}
                    for i in range(50)  # 50 Q&A exchanges
                ]

        mock_session_state = LargeDataSessionState()

        with patch("streamlit.session_state", mock_session_state):
            with patch("app.api.get_export_service") as mock_get_service:
                # Mock export service
                mock_service = Mock()
                export_file = temp_export_dir / "large-export.json"
                mock_service.export_session = AsyncMock(
                    return_value={
                        "file_path": str(export_file),
                        "download_url": f"/downloads/{export_file.name}",
                        "file_size": 50000,  # 50KB file
                    }
                )
                mock_get_service.return_value = mock_service

                # Create large mock export file
                large_data = {"recommendations": mock_session_state.recommendations}
                export_file.write_text(str(large_data))

                # Test export
                import time

                start_time = time.time()

                result = await ui_app.export_results("json")

                end_time = time.time()
                export_time = end_time - start_time

                # Should complete within reasonable time
                assert export_time < 5.0
                assert result is not None
                assert result["file_size"] > 1000  # Should be substantial file


class TestProviderPerformance:
    """Test provider performance and reliability."""

    @pytest.fixture
    def ui_app(self):
        """Create UI app instance."""
        return AutomatedAIAssessmentUI()

    @pytest.mark.asyncio
    async def test_provider_response_times(self, ui_app):
        """Test provider response times."""
        providers = {
            "fake": FakeLLM(),
            "fake_slow": FakeLLM(response_delay=0.1),  # 100ms delay
        }

        test_prompt = "Test prompt for performance measurement"

        for provider_name, provider in providers.items():
            import time

            start_time = time.time()

            response = await provider.generate(test_prompt)

            end_time = time.time()
            response_time = end_time - start_time

            # Fake provider should be fast, slow fake should be slower
            if provider_name == "fake":
                assert response_time < 0.1
            elif provider_name == "fake_slow":
                assert response_time >= 0.1

            assert isinstance(response, str)
            assert len(response) > 0

    @pytest.mark.asyncio
    async def test_concurrent_provider_requests(self, ui_app):
        """Test concurrent requests to providers."""
        provider = FakeLLM()

        # Create multiple concurrent requests
        prompts = [f"Concurrent prompt {i}" for i in range(10)]

        async def make_request(prompt):
            return await provider.generate(prompt)

        import time

        start_time = time.time()

        # Execute all requests concurrently
        responses = await asyncio.gather(*[make_request(prompt) for prompt in prompts])

        end_time = time.time()
        total_time = end_time - start_time

        # All requests should complete
        assert len(responses) == 10
        assert all(isinstance(response, str) for response in responses)

        # Concurrent execution should be faster than sequential
        assert total_time < 1.0  # Should complete within 1 second

    @pytest.mark.asyncio
    async def test_provider_reliability(self, ui_app):
        """Test provider reliability with multiple requests."""
        provider = FakeLLM()

        # Make many requests to test reliability
        success_count = 0
        total_requests = 50

        for i in range(total_requests):
            try:
                response = await provider.generate(f"Test prompt {i}")
                if response and len(response) > 0:
                    success_count += 1
            except Exception:
                pass  # Count as failure

        # Should have high success rate
        success_rate = success_count / total_requests
        assert success_rate >= 0.95  # 95% success rate

    @pytest.mark.asyncio
    async def test_provider_memory_usage(self, ui_app):
        """Test provider memory usage doesn't grow excessively."""
        provider = FakeLLM()

        # Make many requests and check memory doesn't grow excessively
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        # Make 100 requests
        for i in range(100):
            await provider.generate(f"Memory test prompt {i}")

        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory

        # Memory growth should be reasonable (< 50MB)
        assert memory_growth < 50 * 1024 * 1024
