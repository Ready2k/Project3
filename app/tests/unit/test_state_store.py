import json
from datetime import datetime
from unittest.mock import AsyncMock, patch

import pytest

from app.state.store import SessionStore, DiskCacheStore, RedisStore, SessionState, Phase, QAExchange, PatternMatch, Recommendation


class TestSessionState:
    """Test SessionState data model."""
    
    def test_session_state_creation(self):
        """Test creating a session state."""
        state = SessionState(
            session_id="test-123",
            phase=Phase.PARSING,
            progress=25,
            requirements={"description": "Test requirement"},
            missing_fields=["priority", "timeline"],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert state.session_id == "test-123"
        assert state.phase == Phase.PARSING
        assert state.progress == 25
        assert "description" in state.requirements
        assert len(state.missing_fields) == 2
    
    def test_qa_exchange_creation(self):
        """Test creating a QA exchange."""
        exchange = QAExchange(
            questions=["What is the priority?", "What is the timeline?"],
            answers={"priority": "high", "timeline": "2 weeks"},
            timestamp=datetime.now()
        )
        
        assert len(exchange.questions) == 2
        assert exchange.answers["priority"] == "high"
        assert isinstance(exchange.timestamp, datetime)
    
    def test_pattern_match_creation(self):
        """Test creating a pattern match."""
        match = PatternMatch(
            pattern_id="PAT-001",
            score=0.85,
            rationale="High similarity in requirements",
            confidence=0.9
        )
        
        assert match.pattern_id == "PAT-001"
        assert match.score == 0.85
        assert match.confidence == 0.9
    
    def test_recommendation_creation(self):
        """Test creating a recommendation."""
        rec = Recommendation(
            pattern_id="PAT-001",
            feasibility="Automatable",
            confidence=0.9,
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            reasoning="Well-defined requirements with clear automation path"
        )
        
        assert rec.pattern_id == "PAT-001"
        assert rec.feasibility == "Automatable"
        assert len(rec.tech_stack) == 3


class TestSessionStoreInterface:
    """Test the abstract session store interface."""
    
    def test_cannot_instantiate_abstract_store(self):
        """Test that abstract base class cannot be instantiated."""
        with pytest.raises(TypeError):
            SessionStore()


class TestDiskCacheStore:
    """Test DiskCache-based session store."""
    
    @pytest.fixture
    def store(self):
        return DiskCacheStore(cache_dir="test_cache")
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_session(self, store):
        """Test storing and retrieving a session."""
        session_id = "test-session-123"
        state = SessionState(
            session_id=session_id,
            phase=Phase.VALIDATING,
            progress=50,
            requirements={"description": "Test requirement"},
            missing_fields=["priority"],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store session
        await store.update_session(session_id, state)
        
        # Retrieve session
        retrieved = await store.get_session(session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == session_id
        assert retrieved.phase == Phase.VALIDATING
        assert retrieved.progress == 50
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session(self, store):
        """Test retrieving a non-existent session."""
        result = await store.get_session("nonexistent")
        assert result is None
    
    @pytest.mark.asyncio
    async def test_delete_session(self, store):
        """Test deleting a session."""
        session_id = "test-delete-123"
        state = SessionState(
            session_id=session_id,
            phase=Phase.DONE,
            progress=100,
            requirements={},
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Store and verify
        await store.update_session(session_id, state)
        retrieved = await store.get_session(session_id)
        assert retrieved is not None
        
        # Delete and verify
        await store.delete_session(session_id)
        retrieved = await store.get_session(session_id)
        assert retrieved is None
    
    @pytest.mark.asyncio
    async def test_update_existing_session(self, store):
        """Test updating an existing session."""
        session_id = "test-update-123"
        
        # Create initial state
        initial_state = SessionState(
            session_id=session_id,
            phase=Phase.PARSING,
            progress=25,
            requirements={"description": "Initial"},
            missing_fields=["priority"],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        await store.update_session(session_id, initial_state)
        
        # Update state
        updated_state = SessionState(
            session_id=session_id,
            phase=Phase.QNA,
            progress=75,
            requirements={"description": "Updated", "priority": "high"},
            missing_fields=[],
            qa_history=[QAExchange(
                questions=["What is the priority?"],
                answers={"priority": "high"},
                timestamp=datetime.now()
            )],
            matches=[],
            recommendations=[],
            created_at=initial_state.created_at,
            updated_at=datetime.now()
        )
        
        await store.update_session(session_id, updated_state)
        
        # Verify update
        retrieved = await store.get_session(session_id)
        assert retrieved.phase == Phase.QNA
        assert retrieved.progress == 75
        assert retrieved.requirements["priority"] == "high"
        assert len(retrieved.qa_history) == 1


class TestRedisStore:
    """Test Redis-based session store."""
    
    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client."""
        mock_redis = AsyncMock()
        return mock_redis
    
    @pytest.fixture
    def store(self, mock_redis):
        with patch('redis.asyncio.Redis', return_value=mock_redis):
            return RedisStore(host="localhost", port=6379, db=0)
    
    @pytest.mark.asyncio
    async def test_store_and_retrieve_session(self, store, mock_redis):
        """Test storing and retrieving a session with Redis."""
        session_id = "test-redis-123"
        state = SessionState(
            session_id=session_id,
            phase=Phase.MATCHING,
            progress=80,
            requirements={"description": "Redis test"},
            missing_fields=[],
            qa_history=[],
            matches=[PatternMatch(
                pattern_id="PAT-001",
                score=0.9,
                rationale="Test match",
                confidence=0.85
            )],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Mock Redis get to return None initially
        mock_redis.get.return_value = None
        
        # Store session
        await store.update_session(session_id, state)
        
        # Verify Redis set was called
        mock_redis.set.assert_called_once()
        call_args = mock_redis.set.call_args
        assert call_args[0][0] == f"session:{session_id}"
        
        # Mock Redis get to return stored data
        stored_data = json.dumps(state.to_dict())
        mock_redis.get.return_value = stored_data.encode()
        
        # Retrieve session
        retrieved = await store.get_session(session_id)
        
        assert retrieved is not None
        assert retrieved.session_id == session_id
        assert retrieved.phase == Phase.MATCHING
        assert len(retrieved.matches) == 1
    
    @pytest.mark.asyncio
    async def test_delete_session_redis(self, store, mock_redis):
        """Test deleting a session from Redis."""
        session_id = "test-redis-delete"
        
        await store.delete_session(session_id)
        
        mock_redis.delete.assert_called_once_with(f"session:{session_id}")
    
    @pytest.mark.asyncio
    async def test_get_nonexistent_session_redis(self, store, mock_redis):
        """Test retrieving non-existent session from Redis."""
        mock_redis.get.return_value = None
        
        result = await store.get_session("nonexistent")
        assert result is None