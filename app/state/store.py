"""Session state management and storage."""

import json
from abc import ABC, abstractmethod
from dataclasses import dataclass, asdict
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

import diskcache
import redis.asyncio as redis


class Phase(Enum):
    """Processing phases for session state machine."""
    PARSING = "PARSING"
    VALIDATING = "VALIDATING"
    QNA = "QNA"
    MATCHING = "MATCHING"
    RECOMMENDING = "RECOMMENDING"
    DONE = "DONE"


@dataclass
class QAExchange:
    """Question and answer exchange data."""
    questions: List[str]
    answers: Dict[str, str]
    timestamp: datetime
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "questions": self.questions,
            "answers": self.answers,
            "timestamp": self.timestamp.isoformat()
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "QAExchange":
        """Create from dictionary."""
        return cls(
            questions=data["questions"],
            answers=data["answers"],
            timestamp=datetime.fromisoformat(data["timestamp"])
        )


@dataclass
class PatternMatch:
    """Pattern matching result data."""
    pattern_id: str
    score: float
    rationale: str
    confidence: float
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "PatternMatch":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class Recommendation:
    """Recommendation result data."""
    pattern_id: str
    feasibility: str
    confidence: float
    tech_stack: List[str]
    reasoning: str
    enhanced_tech_stack: Optional[List[str]] = None
    architecture_explanation: Optional[str] = None
    agent_roles: Optional[List[Dict[str, Any]]] = None
    necessity_assessment: Optional[Any] = None  # AgenticNecessityAssessment
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Recommendation":
        """Create from dictionary."""
        return cls(**data)


@dataclass
class SessionState:
    """Complete session state data."""
    session_id: str
    phase: Phase
    progress: int
    requirements: Dict[str, Any]
    missing_fields: List[str]
    qa_history: List[QAExchange]
    matches: List[PatternMatch]
    recommendations: List[Recommendation]
    created_at: datetime
    updated_at: datetime
    provider_config: Optional[Dict[str, Any]] = None
    
    def dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "session_id": self.session_id,
            "phase": self.phase.value,
            "progress": self.progress,
            "requirements": self.requirements,
            "missing_fields": self.missing_fields,
            "qa_history": [qa.dict() for qa in self.qa_history],
            "matches": [match.dict() for match in self.matches],
            "recommendations": [rec.dict() for rec in self.recommendations],
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "provider_config": self.provider_config
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "SessionState":
        """Create from dictionary."""
        return cls(
            session_id=data["session_id"],
            phase=Phase(data["phase"]),
            progress=data["progress"],
            requirements=data["requirements"],
            missing_fields=data["missing_fields"],
            qa_history=[QAExchange.from_dict(qa) for qa in data["qa_history"]],
            matches=[PatternMatch.from_dict(match) for match in data["matches"]],
            recommendations=[Recommendation.from_dict(rec) for rec in data["recommendations"]],
            created_at=datetime.fromisoformat(data["created_at"]),
            updated_at=datetime.fromisoformat(data["updated_at"]),
            provider_config=data.get("provider_config")
        )


class SessionStore(ABC):
    """Abstract base class for session storage."""
    
    @abstractmethod
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve session state by ID."""
        raise NotImplementedError("Subclasses must implement get_session")
    
    @abstractmethod
    async def update_session(self, session_id: str, state: SessionState) -> None:
        """Store or update session state."""
        raise NotImplementedError("Subclasses must implement update_session")
    
    @abstractmethod
    async def delete_session(self, session_id: str) -> None:
        """Delete session state."""
        raise NotImplementedError("Subclasses must implement delete_session")


class DiskCacheStore(SessionStore):
    """DiskCache-based session storage implementation."""
    
    def __init__(self, cache_dir: str = "cache"):
        self.cache = diskcache.Cache(cache_dir)
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve session from disk cache."""
        try:
            data = self.cache.get(f"session:{session_id}")
            if data is None:
                return None
            return SessionState.from_dict(data)
        except Exception:
            return None
    
    async def update_session(self, session_id: str, state: SessionState) -> None:
        """Store session to disk cache."""
        try:
            self.cache.set(f"session:{session_id}", state.dict())
        except Exception as e:
            raise RuntimeError(f"Failed to store session: {e}")
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session from disk cache."""
        try:
            self.cache.delete(f"session:{session_id}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete session: {e}")


class RedisStore(SessionStore):
    """Redis-based session storage implementation."""
    
    def __init__(self, host: str = "localhost", port: int = 6379, db: int = 0):
        self.redis = redis.Redis(host=host, port=port, db=db)
    
    async def get_session(self, session_id: str) -> Optional[SessionState]:
        """Retrieve session from Redis."""
        try:
            data = await self.redis.get(f"session:{session_id}")
            if data is None:
                return None
            return SessionState.from_dict(json.loads(data.decode()))
        except Exception:
            return None
    
    async def update_session(self, session_id: str, state: SessionState) -> None:
        """Store session to Redis."""
        try:
            data = json.dumps(state.dict())
            await self.redis.set(f"session:{session_id}", data, ex=3600)  # 1 hour TTL
        except Exception as e:
            raise RuntimeError(f"Failed to store session: {e}")
    
    async def delete_session(self, session_id: str) -> None:
        """Delete session from Redis."""
        try:
            await self.redis.delete(f"session:{session_id}")
        except Exception as e:
            raise RuntimeError(f"Failed to delete session: {e}")