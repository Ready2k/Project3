"""Unit tests for audit and observability system."""

import pytest
import sqlite3
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch

from app.utils.audit import (
    AuditLogger, 
    AuditRun, 
    AuditMatch, 
    get_audit_logger,
    log_llm_call,
    log_pattern_match
)


class TestAuditRun:
    """Test AuditRun dataclass."""
    
    def test_audit_run_creation(self):
        """Test AuditRun creation with all fields."""
        run = AuditRun(
            session_id="test-session",
            provider="openai",
            model="gpt-4",
            latency_ms=1500,
            tokens=100
        )
        
        assert run.session_id == "test-session"
        assert run.provider == "openai"
        assert run.model == "gpt-4"
        assert run.latency_ms == 1500
        assert run.tokens == 100
        assert run.created_at is not None
        assert run.id is None
    
    def test_audit_run_auto_timestamp(self):
        """Test that created_at is automatically set."""
        before = datetime.utcnow()
        run = AuditRun(
            session_id="test-session",
            provider="openai",
            model="gpt-4",
            latency_ms=1500
        )
        after = datetime.utcnow()
        
        assert before <= run.created_at <= after
    
    def test_audit_run_custom_timestamp(self):
        """Test AuditRun with custom timestamp."""
        custom_time = datetime(2023, 1, 1, 12, 0, 0)
        run = AuditRun(
            session_id="test-session",
            provider="openai",
            model="gpt-4",
            latency_ms=1500,
            created_at=custom_time
        )
        
        assert run.created_at == custom_time


class TestAuditMatch:
    """Test AuditMatch dataclass."""
    
    def test_audit_match_creation(self):
        """Test AuditMatch creation with all fields."""
        match = AuditMatch(
            session_id="test-session",
            pattern_id="PAT-001",
            score=0.85,
            accepted=True
        )
        
        assert match.session_id == "test-session"
        assert match.pattern_id == "PAT-001"
        assert match.score == 0.85
        assert match.accepted is True
        assert match.created_at is not None
        assert match.id is None
    
    def test_audit_match_auto_timestamp(self):
        """Test that created_at is automatically set."""
        before = datetime.utcnow()
        match = AuditMatch(
            session_id="test-session",
            pattern_id="PAT-001",
            score=0.85
        )
        after = datetime.utcnow()
        
        assert before <= match.created_at <= after
    
    def test_audit_match_optional_accepted(self):
        """Test AuditMatch with optional accepted field."""
        match = AuditMatch(
            session_id="test-session",
            pattern_id="PAT-001",
            score=0.85
        )
        
        assert match.accepted is None


class TestAuditLogger:
    """Test AuditLogger class."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)
    
    @pytest.fixture
    def audit_logger(self, temp_db):
        """Create AuditLogger instance with temporary database."""
        return AuditLogger(db_path=temp_db, redact_pii=False)
    
    @pytest.fixture
    def audit_logger_with_redaction(self, temp_db):
        """Create AuditLogger instance with PII redaction enabled."""
        return AuditLogger(db_path=temp_db, redact_pii=True)
    
    def test_database_initialization(self, temp_db):
        """Test that database tables are created correctly."""
        AuditLogger(db_path=temp_db)
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [row[0] for row in cursor.fetchall()]
            
            assert 'runs' in tables
            assert 'matches' in tables
            
            # Check runs table schema
            cursor = conn.execute("PRAGMA table_info(runs)")
            columns = [row[1] for row in cursor.fetchall()]
            expected_columns = ['id', 'session_id', 'provider', 'model', 'latency_ms', 'tokens', 'created_at']
            assert all(col in columns for col in expected_columns)
            
            # Check matches table schema
            cursor = conn.execute("PRAGMA table_info(matches)")
            columns = [row[1] for row in cursor.fetchall()]
            expected_columns = ['id', 'session_id', 'pattern_id', 'score', 'accepted', 'created_at']
            assert all(col in columns for col in expected_columns)
    
    def test_database_indexes(self, temp_db):
        """Test that database indexes are created."""
        AuditLogger(db_path=temp_db)
        
        with sqlite3.connect(temp_db) as conn:
            cursor = conn.execute("SELECT name FROM sqlite_master WHERE type='index'")
            indexes = [row[0] for row in cursor.fetchall()]
            
            expected_indexes = [
                'idx_runs_session_id',
                'idx_runs_created_at',
                'idx_matches_session_id',
                'idx_matches_created_at'
            ]
            
            for index in expected_indexes:
                assert index in indexes
    
    @pytest.mark.asyncio
    async def test_log_llm_call(self, audit_logger):
        """Test logging LLM calls."""
        await audit_logger.log_llm_call(
            session_id="test-session-123",
            provider="openai",
            model="gpt-4",
            latency_ms=1500,
            tokens=100
        )
        
        runs = audit_logger.get_runs()
        assert len(runs) == 1
        
        run = runs[0]
        assert run.session_id == "test-session-123"
        assert run.provider == "openai"
        assert run.model == "gpt-4"
        assert run.latency_ms == 1500
        assert run.tokens == 100
        assert run.id is not None
        assert run.created_at is not None
    
    @pytest.mark.asyncio
    async def test_log_llm_call_without_tokens(self, audit_logger):
        """Test logging LLM calls without token count."""
        await audit_logger.log_llm_call(
            session_id="test-session-123",
            provider="bedrock",
            model="claude-3",
            latency_ms=2000
        )
        
        runs = audit_logger.get_runs()
        assert len(runs) == 1
        
        run = runs[0]
        assert run.tokens is None
    
    @pytest.mark.asyncio
    async def test_log_pattern_match(self, audit_logger):
        """Test logging pattern matches."""
        await audit_logger.log_pattern_match(
            session_id="test-session-123",
            pattern_id="PAT-001",
            score=0.85,
            accepted=True
        )
        
        matches = audit_logger.get_matches()
        assert len(matches) == 1
        
        match = matches[0]
        assert match.session_id == "test-session-123"
        assert match.pattern_id == "PAT-001"
        assert match.score == 0.85
        assert match.accepted
        assert match.id is not None
        assert match.created_at is not None
    
    @pytest.mark.asyncio
    async def test_log_pattern_match_without_accepted(self, audit_logger):
        """Test logging pattern matches without accepted status."""
        await audit_logger.log_pattern_match(
            session_id="test-session-123",
            pattern_id="PAT-002",
            score=0.65
        )
        
        matches = audit_logger.get_matches()
        assert len(matches) == 1
        
        match = matches[0]
        assert match.accepted is None
    
    def test_session_id_redaction(self, audit_logger_with_redaction):
        """Test session ID redaction for privacy."""
        long_session_id = "very-long-session-id-with-sensitive-info"
        redacted = audit_logger_with_redaction._redact_session_id(long_session_id)
        
        assert redacted == "very-lon[REDACTED]"
        assert len(redacted) < len(long_session_id)
    
    def test_session_id_no_redaction_short(self, audit_logger_with_redaction):
        """Test that short session IDs are not redacted."""
        short_session_id = "short123"
        redacted = audit_logger_with_redaction._redact_session_id(short_session_id)
        
        assert redacted == short_session_id
    
    def test_session_id_no_redaction_disabled(self, audit_logger):
        """Test that redaction is disabled when configured."""
        long_session_id = "very-long-session-id-with-sensitive-info"
        redacted = audit_logger._redact_session_id(long_session_id)
        
        assert redacted == long_session_id
    
    @pytest.mark.asyncio
    async def test_get_runs_filtering(self, audit_logger):
        """Test filtering runs by session_id and provider."""
        # Add multiple runs
        await audit_logger.log_llm_call("session-1", "openai", "gpt-4", 1000, 50)
        await audit_logger.log_llm_call("session-1", "bedrock", "claude-3", 1500, 75)
        await audit_logger.log_llm_call("session-2", "openai", "gpt-4", 1200, 60)
        
        # Test session filtering
        session_1_runs = audit_logger.get_runs(session_id="session-1")
        assert len(session_1_runs) == 2
        assert all(run.session_id == "session-1" for run in session_1_runs)
        
        # Test provider filtering
        openai_runs = audit_logger.get_runs(provider="openai")
        assert len(openai_runs) == 2
        assert all(run.provider == "openai" for run in openai_runs)
        
        # Test combined filtering
        session_1_openai = audit_logger.get_runs(session_id="session-1", provider="openai")
        assert len(session_1_openai) == 1
        assert session_1_openai[0].session_id == "session-1"
        assert session_1_openai[0].provider == "openai"
    
    @pytest.mark.asyncio
    async def test_get_matches_filtering(self, audit_logger):
        """Test filtering matches by session_id and pattern_id."""
        # Add multiple matches
        await audit_logger.log_pattern_match("session-1", "PAT-001", 0.8, True)
        await audit_logger.log_pattern_match("session-1", "PAT-002", 0.6, False)
        await audit_logger.log_pattern_match("session-2", "PAT-001", 0.9, True)
        
        # Test session filtering
        session_1_matches = audit_logger.get_matches(session_id="session-1")
        assert len(session_1_matches) == 2
        assert all(match.session_id == "session-1" for match in session_1_matches)
        
        # Test pattern filtering
        pat_001_matches = audit_logger.get_matches(pattern_id="PAT-001")
        assert len(pat_001_matches) == 2
        assert all(match.pattern_id == "PAT-001" for match in pat_001_matches)
        
        # Test combined filtering
        session_1_pat_001 = audit_logger.get_matches(session_id="session-1", pattern_id="PAT-001")
        assert len(session_1_pat_001) == 1
        assert session_1_pat_001[0].session_id == "session-1"
        assert session_1_pat_001[0].pattern_id == "PAT-001"
    
    @pytest.mark.asyncio
    async def test_get_provider_stats(self, audit_logger):
        """Test provider statistics aggregation."""
        # Add test data
        await audit_logger.log_llm_call("session-1", "openai", "gpt-4", 1000, 50)
        await audit_logger.log_llm_call("session-2", "openai", "gpt-4", 1500, 75)
        await audit_logger.log_llm_call("session-3", "bedrock", "claude-3", 2000, 100)
        
        stats = audit_logger.get_provider_stats()
        
        assert 'provider_stats' in stats
        provider_stats = stats['provider_stats']
        
        # Should have 2 provider/model combinations
        assert len(provider_stats) == 2
        
        # Find OpenAI stats
        openai_stats = next(s for s in provider_stats if s['provider'] == 'openai')
        assert openai_stats['model'] == 'gpt-4'
        assert openai_stats['call_count'] == 2
        assert openai_stats['avg_latency'] == 1250.0  # (1000 + 1500) / 2
        assert openai_stats['min_latency'] == 1000
        assert openai_stats['max_latency'] == 1500
        assert openai_stats['total_tokens'] == 125  # 50 + 75
        
        # Find Bedrock stats
        bedrock_stats = next(s for s in provider_stats if s['provider'] == 'bedrock')
        assert bedrock_stats['model'] == 'claude-3'
        assert bedrock_stats['call_count'] == 1
        assert bedrock_stats['avg_latency'] == 2000.0
        assert bedrock_stats['total_tokens'] == 100
    
    @pytest.mark.asyncio
    async def test_get_pattern_stats(self, audit_logger):
        """Test pattern statistics aggregation."""
        # Add test data
        await audit_logger.log_pattern_match("session-1", "PAT-001", 0.8, True)
        await audit_logger.log_pattern_match("session-2", "PAT-001", 0.9, True)
        await audit_logger.log_pattern_match("session-3", "PAT-001", 0.7, False)
        await audit_logger.log_pattern_match("session-4", "PAT-002", 0.6, True)
        
        stats = audit_logger.get_pattern_stats()
        
        assert 'pattern_stats' in stats
        pattern_stats = stats['pattern_stats']
        
        # Should have 2 patterns
        assert len(pattern_stats) == 2
        
        # Find PAT-001 stats
        pat_001_stats = next(s for s in pattern_stats if s['pattern_id'] == 'PAT-001')
        assert pat_001_stats['match_count'] == 3
        assert pat_001_stats['avg_score'] == 0.8  # (0.8 + 0.9 + 0.7) / 3
        assert pat_001_stats['min_score'] == 0.7
        assert pat_001_stats['max_score'] == 0.9
        assert pat_001_stats['accepted_count'] == 2
        assert pat_001_stats['acceptance_rate'] == 0.667  # 2/3 rounded
        
        # Find PAT-002 stats
        pat_002_stats = next(s for s in pattern_stats if s['pattern_id'] == 'PAT-002')
        assert pat_002_stats['match_count'] == 1
        assert pat_002_stats['accepted_count'] == 1
        assert pat_002_stats['acceptance_rate'] == 1.0
    
    @pytest.mark.asyncio
    async def test_cleanup_old_records(self, audit_logger):
        """Test cleanup of old audit records."""
        # Add recent records
        await audit_logger.log_llm_call("session-1", "openai", "gpt-4", 1000)
        await audit_logger.log_pattern_match("session-1", "PAT-001", 0.8)
        
        # Add old records by directly inserting with old timestamps
        old_timestamp = datetime.utcnow() - timedelta(days=35)
        
        with sqlite3.connect(audit_logger.db_path) as conn:
            conn.execute("""
                INSERT INTO runs (session_id, provider, model, latency_ms, created_at)
                VALUES (?, ?, ?, ?, ?)
            """, ("old-session", "openai", "gpt-4", 1000, old_timestamp))
            
            conn.execute("""
                INSERT INTO matches (session_id, pattern_id, score, created_at)
                VALUES (?, ?, ?, ?)
            """, ("old-session", "PAT-001", 0.8, old_timestamp))
            
            conn.commit()
        
        # Verify we have 2 runs and 2 matches
        assert len(audit_logger.get_runs(limit=10)) == 2
        assert len(audit_logger.get_matches(limit=10)) == 2
        
        # Cleanup records older than 30 days
        deleted_count = audit_logger.cleanup_old_records(days=30)
        
        # Should have deleted 2 records (1 run + 1 match)
        assert deleted_count == 2
        
        # Should have 1 run and 1 match remaining
        assert len(audit_logger.get_runs(limit=10)) == 1
        assert len(audit_logger.get_matches(limit=10)) == 1
    
    @pytest.mark.asyncio
    async def test_error_handling_log_llm_call(self, audit_logger):
        """Test error handling in log_llm_call."""
        # Close the database connection to simulate an error
        audit_logger.db_path = "/invalid/path/audit.db"
        
        # Should not raise an exception, but log the error
        with patch('app.utils.audit.logger') as mock_logger:
            await audit_logger.log_llm_call("session", "provider", "model", 1000)
            mock_logger.error.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_error_handling_log_pattern_match(self, audit_logger):
        """Test error handling in log_pattern_match."""
        # Close the database connection to simulate an error
        audit_logger.db_path = "/invalid/path/audit.db"
        
        # Should not raise an exception, but log the error
        with patch('app.utils.audit.logger') as mock_logger:
            await audit_logger.log_pattern_match("session", "pattern", 0.8)
            mock_logger.error.assert_called_once()


class TestGlobalFunctions:
    """Test global audit functions."""
    
    @pytest.fixture
    def temp_db(self):
        """Create a temporary database for testing."""
        with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
            db_path = f.name
        yield db_path
        Path(db_path).unlink(missing_ok=True)
    
    def test_get_audit_logger_singleton(self, temp_db):
        """Test that get_audit_logger returns singleton instance."""
        # Clear the global instance
        import app.utils.audit
        app.utils.audit._audit_logger = None
        
        logger1 = get_audit_logger(db_path=temp_db)
        logger2 = get_audit_logger(db_path=temp_db)
        
        assert logger1 is logger2
    
    @pytest.mark.asyncio
    async def test_convenience_functions(self, temp_db):
        """Test convenience functions for logging."""
        # Clear the global instance
        import app.utils.audit
        app.utils.audit._audit_logger = None
        
        # Create a real audit logger for testing
        audit_logger = AuditLogger(db_path=temp_db, redact_pii=False)
        
        with patch('app.utils.audit.get_audit_logger', return_value=audit_logger):
            # Test log_llm_call convenience function
            await log_llm_call("session", "provider", "model", 1000, 50)
            
            # Verify the call was logged
            runs = audit_logger.get_runs()
            assert len(runs) == 1
            assert runs[0].session_id == "session"
            assert runs[0].provider == "provider"
            
            # Test log_pattern_match convenience function
            await log_pattern_match("session", "pattern", 0.8, True)
            
            # Verify the match was logged
            matches = audit_logger.get_matches()
            assert len(matches) == 1
            assert matches[0].session_id == "session"
            assert matches[0].pattern_id == "pattern"