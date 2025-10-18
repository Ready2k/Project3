"""Integration tests for audit system with other components."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, AsyncMock

from app.utils.audit import AuditLogger, log_pattern_match
from app.utils.audit_integration import AuditedLLMProvider, create_audited_provider
from app.llm.fakes import FakeLLM


class TestAuditIntegration:
    """Test audit system integration with other components."""

    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)

    @pytest.fixture
    def audit_logger(self, temp_db):
        """Create AuditLogger instance with temporary database."""
        return AuditLogger(db_path=temp_db, redact_pii=False)

    @pytest.mark.asyncio
    async def test_audited_llm_provider_wrapper(self, audit_logger):
        """Test that AuditedLLMProvider logs calls correctly."""
        # Create a fake LLM provider with hash-based responses
        import hashlib

        prompt = "test prompt"
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        fake_llm = FakeLLM(responses={prompt_hash: "test response"})

        # Wrap it with audit logging
        audited_provider = AuditedLLMProvider(fake_llm, session_id="test-session")

        # Make a call
        result = await audited_provider.generate(prompt)

        assert result == "test response"

        # Check that the call was logged by patching the global audit logger
        import app.utils.audit

        original_logger = app.utils.audit._audit_logger
        app.utils.audit._audit_logger = audit_logger

        try:
            # Make another call to test logging
            await audited_provider.generate(prompt)

            runs = audit_logger.get_runs()
            assert len(runs) == 1

            run = runs[0]
            assert run.session_id == "test-session"
            assert run.provider == "fake"
            assert run.model == "fake-llm"
            assert run.latency_ms >= 0
        finally:
            app.utils.audit._audit_logger = original_logger

    @pytest.mark.asyncio
    async def test_audited_provider_factory(self, audit_logger):
        """Test the create_audited_provider factory function."""
        import hashlib

        prompt = "hello"
        prompt_hash = hashlib.md5(prompt.encode()).hexdigest()[:8]
        fake_llm = FakeLLM(responses={prompt_hash: "world"})

        audited_provider = create_audited_provider(fake_llm, "factory-session")

        result = await audited_provider.generate(prompt)
        assert result == "world"

        # Patch global audit logger for testing
        import app.utils.audit

        original_logger = app.utils.audit._audit_logger
        app.utils.audit._audit_logger = audit_logger

        try:
            # Make another call to test logging
            await audited_provider.generate(prompt)

            runs = audit_logger.get_runs()
            assert len(runs) == 1
            assert runs[0].session_id == "factory-session"
        finally:
            app.utils.audit._audit_logger = original_logger

    @pytest.mark.asyncio
    async def test_audited_provider_error_handling(self, audit_logger):
        """Test that errors are still logged in audit system."""
        # Create a mock provider that raises an exception
        mock_provider = MagicMock()
        mock_provider.generate = AsyncMock(side_effect=RuntimeError("Test error"))
        mock_provider.get_model_info.return_value = {
            "provider": "error-provider",
            "model": "error-model",
        }

        audited_provider = AuditedLLMProvider(mock_provider, "error-session")

        # Patch global audit logger for testing
        import app.utils.audit

        original_logger = app.utils.audit._audit_logger
        app.utils.audit._audit_logger = audit_logger

        try:
            # The call should raise an exception
            with pytest.raises(RuntimeError, match="Test error"):
                await audited_provider.generate("test prompt")

            # But the call should still be logged
            runs = audit_logger.get_runs()
            assert len(runs) == 1

            run = runs[0]
            assert run.session_id == "error-session"
            assert run.provider == "error-provider"
            assert run.model == "error-model"
            assert run.latency_ms >= 0
        finally:
            app.utils.audit._audit_logger = original_logger

    @pytest.mark.asyncio
    async def test_pattern_matching_audit_flow(self, audit_logger):
        """Test a complete flow with pattern matching and audit logging."""
        session_id = "pattern-test-session"

        # Patch global audit logger for testing
        import app.utils.audit

        original_logger = app.utils.audit._audit_logger
        app.utils.audit._audit_logger = audit_logger

        try:
            # Simulate pattern matching results
            patterns = [
                {"pattern_id": "PAT-001", "score": 0.85, "accepted": True},
                {"pattern_id": "PAT-002", "score": 0.65, "accepted": False},
                {"pattern_id": "PAT-003", "score": 0.92, "accepted": True},
            ]

            # Log each pattern match
            for pattern in patterns:
                await log_pattern_match(
                    session_id=session_id,
                    pattern_id=pattern["pattern_id"],
                    score=pattern["score"],
                    accepted=pattern["accepted"],
                )

            # Verify all matches were logged
            matches = audit_logger.get_matches(session_id=session_id)
            assert len(matches) == 3

            # Check specific matches
            pat_001_match = next(m for m in matches if m.pattern_id == "PAT-001")
            assert pat_001_match.score == 0.85
            assert pat_001_match.accepted

            pat_002_match = next(m for m in matches if m.pattern_id == "PAT-002")
            assert pat_002_match.score == 0.65
            assert not pat_002_match.accepted

            # Test pattern statistics
            pattern_stats = audit_logger.get_pattern_stats()
            assert len(pattern_stats["pattern_stats"]) == 3

            # Find PAT-001 stats
            pat_001_stats = next(
                s
                for s in pattern_stats["pattern_stats"]
                if s["pattern_id"] == "PAT-001"
            )
            assert pat_001_stats["match_count"] == 1
            assert pat_001_stats["accepted_count"] == 1
            assert pat_001_stats["acceptance_rate"] == 1.0
        finally:
            app.utils.audit._audit_logger = original_logger

    @pytest.mark.asyncio
    async def test_combined_llm_and_pattern_audit(self, audit_logger):
        """Test combined LLM calls and pattern matching in one session."""
        session_id = "combined-test-session"

        # Patch global audit logger for testing
        import app.utils.audit

        original_logger = app.utils.audit._audit_logger
        app.utils.audit._audit_logger = audit_logger

        try:
            # Simulate LLM calls with hash-based responses
            import hashlib

            prompt1 = "analyze requirements"
            prompt2 = "generate questions"
            hash1 = hashlib.md5(prompt1.encode()).hexdigest()[:8]
            hash2 = hashlib.md5(prompt2.encode()).hexdigest()[:8]

            fake_llm = FakeLLM(
                responses={hash1: "analysis complete", hash2: "questions generated"}
            )
            audited_provider = AuditedLLMProvider(fake_llm, session_id)

            # Make LLM calls
            result1 = await audited_provider.generate(prompt1)
            result2 = await audited_provider.generate(prompt2)

            assert result1 == "analysis complete"
            assert result2 == "questions generated"

            # Simulate pattern matching
            await log_pattern_match(session_id, "PAT-001", 0.88, True)
            await log_pattern_match(session_id, "PAT-002", 0.72, True)

            # Verify both types of audit records
            runs = audit_logger.get_runs(session_id=session_id)
            matches = audit_logger.get_matches(session_id=session_id)

            assert len(runs) == 2
            assert len(matches) == 2

            # All records should have the same session ID
            assert all(run.session_id == session_id for run in runs)
            assert all(match.session_id == session_id for match in matches)

            # Test combined statistics
            provider_stats = audit_logger.get_provider_stats()
            pattern_stats = audit_logger.get_pattern_stats()

            assert len(provider_stats["provider_stats"]) == 1
            assert len(pattern_stats["pattern_stats"]) == 2

            fake_provider_stats = provider_stats["provider_stats"][0]
            assert fake_provider_stats["provider"] == "fake"
            assert fake_provider_stats["call_count"] == 2
        finally:
            app.utils.audit._audit_logger = original_logger

    @pytest.mark.asyncio
    async def test_audit_with_pii_redaction(self):
        """Test audit logging with PII redaction enabled."""
        with tempfile.NamedTemporaryFile(suffix=".db", delete=False) as f:
            db_path = f.name

        try:
            # Create audit logger with PII redaction enabled
            audit_logger = AuditLogger(db_path=db_path, redact_pii=True)

            # Use a session ID that looks like it might contain PII
            sensitive_session_id = "user-john.doe@company.com-session-12345"

            # Log some calls
            await audit_logger.log_llm_call(
                session_id=sensitive_session_id,
                provider="openai",
                model="gpt-4",
                latency_ms=1500,
                tokens=100,
            )

            await audit_logger.log_pattern_match(
                session_id=sensitive_session_id,
                pattern_id="PAT-001",
                score=0.85,
                accepted=True,
            )

            # Verify that session IDs are redacted
            runs = audit_logger.get_runs()
            matches = audit_logger.get_matches()

            assert len(runs) == 1
            assert len(matches) == 1

            # Session ID should be redacted (first 8 chars + [REDACTED])
            assert runs[0].session_id == "user-joh[REDACTED]"
            assert matches[0].session_id == "user-joh[REDACTED]"

        finally:
            Path(db_path).unlink(missing_ok=True)
