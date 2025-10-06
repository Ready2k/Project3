"""Unit tests for audit integration utilities."""

import pytest
from unittest.mock import Mock, AsyncMock

from app.utils.audit_integration import AuditedLLMProvider, create_audited_provider
from app.llm.fakes import FakeLLM
from app.utils.audit import AuditLogger


class TestAuditedLLMProvider:
    """Test audited LLM provider wrapper."""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger."""
        logger = Mock(spec=AuditLogger)
        logger.log_llm_call = AsyncMock()
        return logger
    
    @pytest.fixture
    def base_provider(self):
        """Create base LLM provider."""
        return FakeLLM()
    
    @pytest.fixture
    def audited_provider(self, base_provider, mock_audit_logger):
        """Create audited provider."""
        return AuditedLLMProvider(base_provider, mock_audit_logger, "test-session")
    
    @pytest.mark.asyncio
    async def test_generate_with_audit(self, audited_provider, mock_audit_logger):
        """Test generate method with audit logging."""
        prompt = "Test prompt"
        
        response = await audited_provider.generate(prompt)
        
        # Should return response from base provider
        assert isinstance(response, str)
        assert len(response) > 0
        
        # Should log the call
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        assert call_args["session_id"] == "test-session"
        assert call_args["prompt"] == prompt
        assert call_args["response"] == response
        assert "provider" in call_args
        assert "model" in call_args
        assert "latency_ms" in call_args
    
    @pytest.mark.asyncio
    async def test_generate_with_kwargs(self, audited_provider, mock_audit_logger):
        """Test generate method with additional kwargs."""
        prompt = "Test prompt"
        kwargs = {"temperature": 0.7, "max_tokens": 100}
        
        response = await audited_provider.generate(prompt, **kwargs)
        
        assert isinstance(response, str)
        
        # Should log with kwargs
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        assert call_args["prompt"] == prompt
    
    @pytest.mark.asyncio
    async def test_generate_error_handling(self, mock_audit_logger):
        """Test error handling in generate method."""
        # Create provider that raises exception
        error_provider = Mock()
        error_provider.generate = AsyncMock(side_effect=Exception("Provider error"))
        error_provider.provider_name = "error_provider"
        error_provider.model_name = "error_model"
        
        audited_provider = AuditedLLMProvider(error_provider, mock_audit_logger, "test-session")
        
        # Should propagate the exception
        with pytest.raises(Exception, match="Provider error"):
            await audited_provider.generate("test prompt")
        
        # Should still log the failed call
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        assert call_args["session_id"] == "test-session"
        assert call_args["response"] == ""  # Empty response for error
    
    @pytest.mark.asyncio
    async def test_test_connection_passthrough(self, audited_provider):
        """Test test_connection method passthrough."""
        result = await audited_provider.test_connection()
        
        # Should pass through to base provider
        assert result is True
    
    def test_get_model_info_passthrough(self, audited_provider):
        """Test get_model_info method passthrough."""
        model_info = audited_provider.get_model_info()
        
        # Should pass through to base provider
        assert isinstance(model_info, dict)
        assert "provider" in model_info
        assert "model" in model_info
    
    def test_property_passthrough(self, audited_provider, base_provider):
        """Test property passthrough."""
        assert audited_provider.provider_name == base_provider.provider_name
        assert audited_provider.model_name == base_provider.model_name
    
    @pytest.mark.asyncio
    async def test_latency_measurement(self, audited_provider, mock_audit_logger):
        """Test latency measurement accuracy."""
        # Use a provider with known delay
        slow_provider = FakeLLM(response_delay=0.1)  # 100ms delay
        audited_slow = AuditedLLMProvider(slow_provider, mock_audit_logger, "test-session")
        
        await audited_slow.generate("test prompt")
        
        # Should measure latency
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        latency_ms = call_args["latency_ms"]
        
        # Should be approximately 100ms (allow some variance)
        assert 80 <= latency_ms <= 200
    
    @pytest.mark.asyncio
    async def test_token_counting(self, audited_provider, mock_audit_logger):
        """Test token counting when available."""
        # Mock provider with token counting
        token_provider = Mock()
        token_provider.generate = AsyncMock(return_value="Test response")
        token_provider.provider_name = "token_provider"
        token_provider.model_name = "token_model"
        token_provider.last_tokens_used = 50  # Mock token count
        
        audited_token = AuditedLLMProvider(token_provider, mock_audit_logger, "test-session")
        
        await audited_token.generate("test prompt")
        
        # Should log token count
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        assert call_args["tokens_used"] == 50


class TestCreateAuditedProvider:
    """Test create_audited_provider factory function."""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger."""
        logger = Mock(spec=AuditLogger)
        logger.log_llm_call = AsyncMock()
        return logger
    
    def test_create_audited_provider(self, mock_audit_logger):
        """Test creating audited provider."""
        base_provider = FakeLLM()
        session_id = "test-session-123"
        
        audited = create_audited_provider(base_provider, mock_audit_logger, session_id)
        
        assert isinstance(audited, AuditedLLMProvider)
        assert audited.base_provider == base_provider
        assert audited.audit_logger == mock_audit_logger
        assert audited.session_id == session_id
    
    def test_create_audited_provider_with_none_logger(self):
        """Test creating audited provider with None logger."""
        base_provider = FakeLLM()
        
        # Should handle None logger gracefully
        audited = create_audited_provider(base_provider, None, "test-session")
        
        # Should return the base provider unchanged
        assert audited == base_provider
    
    def test_create_audited_provider_with_none_session(self, mock_audit_logger):
        """Test creating audited provider with None session."""
        base_provider = FakeLLM()
        
        audited = create_audited_provider(base_provider, mock_audit_logger, None)
        
        # Should still create audited provider
        assert isinstance(audited, AuditedLLMProvider)
        assert audited.session_id is None


class TestAuditIntegrationEdgeCases:
    """Test edge cases in audit integration."""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger."""
        logger = Mock(spec=AuditLogger)
        logger.log_llm_call = AsyncMock()
        return logger
    
    @pytest.mark.asyncio
    async def test_audit_logger_exception(self, mock_audit_logger):
        """Test handling audit logger exceptions."""
        # Make audit logger raise exception
        mock_audit_logger.log_llm_call = AsyncMock(side_effect=Exception("Audit failed"))
        
        base_provider = FakeLLM()
        audited_provider = AuditedLLMProvider(base_provider, mock_audit_logger, "test-session")
        
        # Should not fail even if audit logging fails
        response = await audited_provider.generate("test prompt")
        
        assert isinstance(response, str)
        assert len(response) > 0
    
    @pytest.mark.asyncio
    async def test_empty_prompt_handling(self, mock_audit_logger):
        """Test handling empty prompts."""
        base_provider = FakeLLM()
        audited_provider = AuditedLLMProvider(base_provider, mock_audit_logger, "test-session")
        
        response = await audited_provider.generate("")
        
        # Should handle empty prompt
        assert isinstance(response, str)
        
        # Should still log
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        assert call_args["prompt"] == ""
    
    @pytest.mark.asyncio
    async def test_very_long_prompt_handling(self, mock_audit_logger):
        """Test handling very long prompts."""
        base_provider = FakeLLM()
        audited_provider = AuditedLLMProvider(base_provider, mock_audit_logger, "test-session")
        
        # Create very long prompt
        long_prompt = "test " * 10000  # 50,000 characters
        
        response = await audited_provider.generate(long_prompt)
        
        # Should handle long prompt
        assert isinstance(response, str)
        
        # Should log (potentially truncated)
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        assert len(call_args["prompt"]) > 0
    
    @pytest.mark.asyncio
    async def test_unicode_handling(self, mock_audit_logger):
        """Test handling unicode characters."""
        base_provider = FakeLLM()
        audited_provider = AuditedLLMProvider(base_provider, mock_audit_logger, "test-session")
        
        # Test with unicode characters
        unicode_prompt = "Test with émojis 🚀 and ñoñó characters"
        
        response = await audited_provider.generate(unicode_prompt)
        
        # Should handle unicode
        assert isinstance(response, str)
        
        # Should log unicode correctly
        mock_audit_logger.log_llm_call.assert_called_once()
        call_args = mock_audit_logger.log_llm_call.call_args[1]
        assert call_args["prompt"] == unicode_prompt
    
    @pytest.mark.asyncio
    async def test_concurrent_requests(self, mock_audit_logger):
        """Test concurrent requests to audited provider."""
        base_provider = FakeLLM()
        audited_provider = AuditedLLMProvider(base_provider, mock_audit_logger, "test-session")
        
        # Make multiple concurrent requests
        import asyncio
        prompts = [f"Concurrent prompt {i}" for i in range(10)]
        
        responses = await asyncio.gather(*[
            audited_provider.generate(prompt) for prompt in prompts
        ])
        
        # All should succeed
        assert len(responses) == 10
        assert all(isinstance(response, str) for response in responses)
        
        # Should log all calls
        assert mock_audit_logger.log_llm_call.call_count == 10
    
    def test_provider_without_model_info(self, mock_audit_logger):
        """Test provider without get_model_info method."""
        # Create minimal provider
        minimal_provider = Mock()
        minimal_provider.generate = AsyncMock(return_value="test response")
        minimal_provider.provider_name = "minimal"
        minimal_provider.model_name = "minimal_model"
        # No get_model_info method
        
        audited_provider = AuditedLLMProvider(minimal_provider, mock_audit_logger, "test-session")
        
        # Should handle missing method gracefully
        try:
            model_info = audited_provider.get_model_info()
            # If method exists, should return something
            assert isinstance(model_info, dict)
        except AttributeError:
            # If method doesn't exist, that's also fine
            pass
    
    @pytest.mark.asyncio
    async def test_provider_without_test_connection(self, mock_audit_logger):
        """Test provider without test_connection method."""
        # Create minimal provider
        minimal_provider = Mock()
        minimal_provider.generate = AsyncMock(return_value="test response")
        minimal_provider.provider_name = "minimal"
        minimal_provider.model_name = "minimal_model"
        # No test_connection method
        
        audited_provider = AuditedLLMProvider(minimal_provider, mock_audit_logger, "test-session")
        
        # Should handle missing method gracefully
        try:
            result = await audited_provider.test_connection()
            assert isinstance(result, bool)
        except AttributeError:
            # If method doesn't exist, that's also fine
            pass


class TestAuditIntegrationPerformance:
    """Test performance impact of audit integration."""
    
    @pytest.fixture
    def mock_audit_logger(self):
        """Create mock audit logger."""
        logger = Mock(spec=AuditLogger)
        logger.log_llm_call = AsyncMock()
        return logger
    
    @pytest.mark.asyncio
    async def test_audit_overhead(self, mock_audit_logger):
        """Test audit logging overhead."""
        base_provider = FakeLLM()
        audited_provider = AuditedLLMProvider(base_provider, mock_audit_logger, "test-session")
        
        import time
        
        # Measure base provider performance
        start_time = time.time()
        await base_provider.generate("test prompt")
        base_time = time.time() - start_time
        
        # Measure audited provider performance
        start_time = time.time()
        await audited_provider.generate("test prompt")
        audited_time = time.time() - start_time
        
        # Audit overhead should be minimal (< 50% increase)
        overhead_ratio = audited_time / base_time if base_time > 0 else 1
        assert overhead_ratio < 1.5  # Less than 50% overhead
    
    @pytest.mark.asyncio
    async def test_memory_usage(self, mock_audit_logger):
        """Test memory usage of audited provider."""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss
        
        # Create many audited providers
        providers = []
        for i in range(100):
            base_provider = FakeLLM()
            audited_provider = AuditedLLMProvider(base_provider, mock_audit_logger, f"session-{i}")
            providers.append(audited_provider)
        
        # Make requests
        for provider in providers[:10]:  # Test subset to avoid long test
            await provider.generate("test prompt")
        
        final_memory = process.memory_info().rss
        memory_growth = final_memory - initial_memory
        
        # Memory growth should be reasonable (< 10MB for 100 providers)
        assert memory_growth < 10 * 1024 * 1024