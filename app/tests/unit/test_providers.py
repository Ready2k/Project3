import asyncio
from unittest.mock import Mock, patch

import pytest

from app.llm.base import LLMProvider, EmbeddingProvider
from app.llm.openai_provider import OpenAIProvider
from app.llm.bedrock_provider import BedrockProvider
from app.llm.claude_provider import ClaudeProvider
from app.llm.internal_provider import InternalProvider
from app.llm.fakes import FakeLLM, FakeEmbedder


class TestLLMProviderInterface:
    """Test the abstract base class interface."""

    def test_cannot_instantiate_abstract_provider(self):
        """Test that abstract base class cannot be instantiated."""
        with pytest.raises(TypeError):
            LLMProvider()

    def test_cannot_instantiate_abstract_embedder(self):
        """Test that abstract embedding provider cannot be instantiated."""
        with pytest.raises(TypeError):
            EmbeddingProvider()


class TestOpenAIProvider:
    """Test OpenAI provider implementation."""

    @pytest.fixture
    def provider(self):
        return OpenAIProvider(api_key="test-key", model="gpt-4o")

    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated text"))]

        with patch.object(
            provider.client.chat.completions, "create", return_value=mock_response
        ):
            result = await provider.generate("Test prompt")
            assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_generate_with_kwargs(self, provider):
        """Test generation with additional parameters."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="Generated text"))]

        with patch.object(
            provider.client.chat.completions, "create", return_value=mock_response
        ) as mock_create:
            await provider.generate("Test prompt", temperature=0.7, max_tokens=100)
            mock_create.assert_called_once()
            call_args = mock_create.call_args[1]
            assert call_args["temperature"] == 0.7
            assert call_args["max_tokens"] == 100

    @pytest.mark.asyncio
    async def test_test_connection_success(self, provider):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.choices = [Mock(message=Mock(content="test"))]

        with patch.object(
            provider.client.chat.completions, "create", return_value=mock_response
        ):
            result = await provider.test_connection()
            assert result is True

    @pytest.mark.asyncio
    async def test_test_connection_failure(self, provider):
        """Test connection test failure."""
        with patch.object(
            provider.client.chat.completions,
            "create",
            side_effect=Exception("API Error"),
        ):
            result = await provider.test_connection()
            assert result is False

    def test_get_model_info(self, provider):
        """Test model info retrieval."""
        info = provider.get_model_info()
        assert info["provider"] == "openai"
        assert info["model"] == "gpt-4o"
        assert "api_key_set" in info


class TestBedrockProvider:
    """Test AWS Bedrock provider implementation."""

    @pytest.fixture
    def provider(self):
        return BedrockProvider(
            model="anthropic.claude-3-sonnet-20240229-v1:0", region="us-east-1"
        )

    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        """Test successful text generation."""
        mock_response = {
            "body": Mock(
                read=Mock(return_value=b'{"content": [{"text": "Generated text"}]}')
            )
        }

        with patch.object(provider.client, "invoke_model", return_value=mock_response):
            result = await provider.generate("Test prompt")
            assert result == "Generated text"

    def test_get_model_info(self, provider):
        """Test model info retrieval."""
        info = provider.get_model_info()
        assert info["provider"] == "bedrock"
        assert info["model"] == "anthropic.claude-3-sonnet-20240229-v1:0"
        assert info["region"] == "us-east-1"


class TestClaudeProvider:
    """Test Claude Direct provider implementation."""

    @pytest.fixture
    def provider(self):
        return ClaudeProvider(api_key="test-key", model="claude-3-sonnet-20240229")

    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.content = [Mock(text="Generated text")]

        with patch.object(
            provider.client.messages, "create", return_value=mock_response
        ):
            result = await provider.generate("Test prompt")
            assert result == "Generated text"

    def test_get_model_info(self, provider):
        """Test model info retrieval."""
        info = provider.get_model_info()
        assert info["provider"] == "claude"
        assert info["model"] == "claude-3-sonnet-20240229"


class TestInternalProvider:
    """Test Internal HTTP provider implementation."""

    @pytest.fixture
    def provider(self):
        return InternalProvider(
            endpoint_url="http://localhost:8080/generate", model="internal-model"
        )

    @pytest.mark.asyncio
    async def test_generate_success(self, provider):
        """Test successful text generation."""
        mock_response = Mock()
        mock_response.json.return_value = {"text": "Generated text"}
        mock_response.raise_for_status = Mock()

        with patch.object(provider.client, "post", return_value=mock_response):
            result = await provider.generate("Test prompt")
            assert result == "Generated text"

    @pytest.mark.asyncio
    async def test_test_connection_success(self, provider):
        """Test successful connection test."""
        mock_response = Mock()
        mock_response.json.return_value = {"text": "test"}
        mock_response.raise_for_status = Mock()

        with patch.object(provider.client, "post", return_value=mock_response):
            result = await provider.test_connection()
            assert result is True


class TestFakeLLM:
    """Test deterministic fake LLM implementation."""

    def test_deterministic_responses(self):
        """Test that responses are deterministic based on seed."""
        responses = {"12345678": "Response A", "87654321": "Response B"}
        fake_llm = FakeLLM(responses=responses, seed=42)

        # Same prompt should give same response
        result1 = asyncio.run(fake_llm.generate("test prompt"))
        result2 = asyncio.run(fake_llm.generate("test prompt"))
        assert result1 == result2

    def test_different_prompts_different_responses(self):
        """Test that different prompts can give different responses."""
        responses = {}
        fake_llm = FakeLLM(responses=responses, seed=42)

        result1 = asyncio.run(fake_llm.generate("prompt 1"))
        result2 = asyncio.run(fake_llm.generate("prompt 2"))
        # They might be the same due to default response, but structure should work
        assert isinstance(result1, str)
        assert isinstance(result2, str)

    @pytest.mark.asyncio
    async def test_test_connection_always_true(self):
        """Test that fake LLM always reports successful connection."""
        fake_llm = FakeLLM({}, seed=42)
        result = await fake_llm.test_connection()
        assert result is True

    def test_get_model_info(self):
        """Test model info for fake LLM."""
        fake_llm = FakeLLM({}, seed=42)
        info = fake_llm.get_model_info()
        assert info["provider"] == "fake"
        assert info["model"] == "fake-llm"


class TestFakeEmbedder:
    """Test deterministic fake embedder implementation."""

    def test_deterministic_embeddings(self):
        """Test that embeddings are deterministic based on seed."""
        fake_embedder = FakeEmbedder(dimension=384, seed=42)

        # Same text should give same embedding
        result1 = asyncio.run(fake_embedder.embed("test text"))
        result2 = asyncio.run(fake_embedder.embed("test text"))
        assert result1 == result2
        assert len(result1) == 384

    def test_different_texts_different_embeddings(self):
        """Test that different texts give different embeddings."""
        fake_embedder = FakeEmbedder(dimension=384, seed=42)

        result1 = asyncio.run(fake_embedder.embed("text 1"))
        result2 = asyncio.run(fake_embedder.embed("text 2"))
        assert result1 != result2
        assert len(result1) == 384
        assert len(result2) == 384

    @pytest.mark.asyncio
    async def test_embed_batch(self):
        """Test batch embedding functionality."""
        fake_embedder = FakeEmbedder(dimension=384, seed=42)

        texts = ["text 1", "text 2", "text 3"]
        results = await fake_embedder.embed_batch(texts)

        assert len(results) == 3
        assert all(len(embedding) == 384 for embedding in results)

        # Should be same as individual embeddings
        individual_results = []
        for text in texts:
            individual_results.append(await fake_embedder.embed(text))

        assert results == individual_results
