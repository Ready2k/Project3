"""Audit and observability system for tracking LLM calls and pattern matches."""

import sqlite3
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
import json
import logging

from .redact import PIIRedactor


logger = logging.getLogger(__name__)


@dataclass
class AuditRun:
    """Audit record for LLM provider calls."""
    session_id: str
    provider: str
    model: str
    latency_ms: int
    tokens: Optional[int] = None
    prompt: Optional[str] = None
    response: Optional[str] = None
    purpose: Optional[str] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


@dataclass
class AuditMatch:
    """Audit record for pattern matching operations."""
    session_id: str
    pattern_id: str
    score: float
    accepted: Optional[bool] = None
    created_at: Optional[datetime] = None
    id: Optional[int] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class AuditLogger:
    """SQLite-based audit logging system with PII redaction."""
    
    def __init__(self, db_path: str = "audit.db", redact_pii: bool = True):
        self.db_path = Path(db_path)
        self.redact_pii = redact_pii
        self.redactor = PIIRedactor() if redact_pii else None
        self._init_database()
    
    def _init_database(self) -> None:
        """Initialize SQLite database with required tables and handle migrations."""
        with sqlite3.connect(self.db_path) as conn:
            # Create tables with current schema
            conn.execute("""
                CREATE TABLE IF NOT EXISTS runs (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    provider TEXT NOT NULL,
                    model TEXT NOT NULL,
                    latency_ms INTEGER NOT NULL,
                    tokens INTEGER,
                    prompt TEXT,
                    response TEXT,
                    purpose TEXT,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            conn.execute("""
                CREATE TABLE IF NOT EXISTS matches (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_id TEXT NOT NULL,
                    pattern_id TEXT NOT NULL,
                    score REAL NOT NULL,
                    accepted BOOLEAN,
                    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Handle migrations for existing databases
            self._migrate_database(conn)
            
            # Create indexes for better query performance
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_session_id ON runs(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_runs_created_at ON runs(created_at)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_session_id ON matches(session_id)")
            conn.execute("CREATE INDEX IF NOT EXISTS idx_matches_created_at ON matches(created_at)")
            
            conn.commit()
    
    def _migrate_database(self, conn) -> None:
        """Handle database schema migrations."""
        try:
            # Check if prompt and response columns exist
            cursor = conn.execute("PRAGMA table_info(runs)")
            columns = [row[1] for row in cursor.fetchall()]
            
            # Add prompt column if it doesn't exist
            if 'prompt' not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN prompt TEXT")
                logger.info("Added 'prompt' column to runs table")
            
            # Add response column if it doesn't exist
            if 'response' not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN response TEXT")
                logger.info("Added 'response' column to runs table")
            
            # Add purpose column if it doesn't exist
            if 'purpose' not in columns:
                conn.execute("ALTER TABLE runs ADD COLUMN purpose TEXT")
                logger.info("Added 'purpose' column to runs table")
                
        except Exception as e:
            logger.error(f"Database migration failed: {e}")
            # Continue anyway - the application should still work with basic functionality
    
    def _redact_session_id(self, session_id: str) -> str:
        """Redact session ID for privacy while maintaining uniqueness."""
        if not self.redact_pii or not self.redactor:
            return session_id
        
        # Keep first 8 characters for debugging, redact the rest
        if len(session_id) > 8:
            return session_id[:8] + "[REDACTED]"
        return session_id
    
    async def log_llm_call(self, 
                          session_id: str,
                          provider: str,
                          model: str,
                          latency_ms: int,
                          tokens: Optional[int] = None,
                          prompt: Optional[str] = None,
                          response: Optional[str] = None,
                          purpose: Optional[str] = None) -> None:
        """Log an LLM provider call with optional prompt, response, and purpose."""
        try:
            # Input validation
            if not session_id or not isinstance(session_id, str):
                raise ValueError("session_id must be a non-empty string")
            if not provider or not isinstance(provider, str):
                raise ValueError("provider must be a non-empty string")
            if not model or not isinstance(model, str):
                raise ValueError("model must be a non-empty string")
            if not isinstance(latency_ms, (int, float)) or latency_ms < 0:
                raise ValueError("latency_ms must be a non-negative number")
            if tokens is not None and (not isinstance(tokens, int) or tokens < 0):
                raise ValueError("tokens must be a non-negative integer")
            if prompt is not None and not isinstance(prompt, str):
                raise ValueError("prompt must be a string")
            if response is not None and not isinstance(response, str):
                raise ValueError("response must be a string")
            if purpose is not None and not isinstance(purpose, str):
                raise ValueError("purpose must be a string")
            
            # Redact PII from prompt and response if enabled
            redacted_prompt = None
            redacted_response = None
            
            if prompt is not None:
                # Convert prompt to string if it's not already
                prompt_str = str(prompt) if not isinstance(prompt, str) else prompt
                redacted_prompt = self.redactor.redact(prompt_str) if self.redact_pii and self.redactor else prompt_str
            
            if response is not None:
                # Convert response to string if it's not already
                response_str = str(response) if not isinstance(response, str) else response
                redacted_response = self.redactor.redact(response_str) if self.redact_pii and self.redactor else response_str
            
            audit_run = AuditRun(
                session_id=self._redact_session_id(session_id),
                provider=provider,
                model=model,
                latency_ms=latency_ms,
                tokens=tokens,
                prompt=redacted_prompt,
                response=redacted_response,
                purpose=purpose
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO runs (session_id, provider, model, latency_ms, tokens, prompt, response, purpose, created_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    audit_run.session_id,
                    audit_run.provider,
                    audit_run.model,
                    audit_run.latency_ms,
                    audit_run.tokens,
                    audit_run.prompt,
                    audit_run.response,
                    audit_run.purpose,
                    audit_run.created_at
                ))
                conn.commit()
                
            logger.debug(f"Logged LLM call: {provider}/{model} - {latency_ms}ms")
            
        except Exception as e:
            logger.error(f"Failed to log LLM call: {e}")
    
    async def log_pattern_match(self,
                               session_id: str,
                               pattern_id: str,
                               score: float,
                               accepted: Optional[bool] = None) -> None:
        """Log a pattern matching operation."""
        try:
            # Input validation
            if not session_id or not isinstance(session_id, str):
                raise ValueError("session_id must be a non-empty string")
            if not pattern_id or not isinstance(pattern_id, str):
                raise ValueError("pattern_id must be a non-empty string")
            if not isinstance(score, (int, float)) or score < 0 or score > 1:
                raise ValueError("score must be a number between 0 and 1")
            if accepted is not None and not isinstance(accepted, bool):
                raise ValueError("accepted must be a boolean or None")
            
            audit_match = AuditMatch(
                session_id=self._redact_session_id(session_id),
                pattern_id=pattern_id,
                score=score,
                accepted=accepted
            )
            
            with sqlite3.connect(self.db_path) as conn:
                conn.execute("""
                    INSERT INTO matches (session_id, pattern_id, score, accepted, created_at)
                    VALUES (?, ?, ?, ?, ?)
                """, (
                    audit_match.session_id,
                    audit_match.pattern_id,
                    audit_match.score,
                    audit_match.accepted,
                    audit_match.created_at
                ))
                conn.commit()
                
            logger.debug(f"Logged pattern match: {pattern_id} - score {score}")
            
        except Exception as e:
            logger.error(f"Failed to log pattern match: {e}")
    
    def get_runs(self, 
                 session_id: Optional[str] = None,
                 provider: Optional[str] = None,
                 limit: int = 100) -> List[AuditRun]:
        """Retrieve LLM call audit records."""
        query = "SELECT * FROM runs WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(self._redact_session_id(session_id))
        
        if provider:
            query += " AND provider = ?"
            params.append(provider)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        return [
            AuditRun(
                id=row['id'],
                session_id=row['session_id'],
                provider=row['provider'],
                model=row['model'],
                latency_ms=row['latency_ms'],
                tokens=row['tokens'],
                prompt=row.get('prompt'),
                response=row.get('response'),
                purpose=row.get('purpose'),
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def get_matches(self,
                   session_id: Optional[str] = None,
                   pattern_id: Optional[str] = None,
                   limit: int = 100) -> List[AuditMatch]:
        """Retrieve pattern match audit records."""
        query = "SELECT * FROM matches WHERE 1=1"
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(self._redact_session_id(session_id))
        
        if pattern_id:
            query += " AND pattern_id = ?"
            params.append(pattern_id)
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        return [
            AuditMatch(
                id=row['id'],
                session_id=row['session_id'],
                pattern_id=row['pattern_id'],
                score=row['score'],
                accepted=row['accepted'],
                created_at=datetime.fromisoformat(row['created_at']) if row['created_at'] else None
            )
            for row in rows
        ]
    
    def get_provider_stats(self, 
                          time_filter: str = "All Time",
                          include_test_providers: bool = False,
                          session_id: Optional[str] = None) -> Dict[str, Any]:
        """Get aggregated statistics by provider with filtering options."""
        
        # Build the WHERE clause based on filters
        where_conditions = []
        params = []
        
        # Time filtering
        if time_filter != "All Time":
            if time_filter == "Last 24 Hours":
                where_conditions.append("created_at >= datetime('now', '-1 day')")
            elif time_filter == "Last 7 Days":
                where_conditions.append("created_at >= datetime('now', '-7 days')")
            elif time_filter == "Last 30 Days":
                where_conditions.append("created_at >= datetime('now', '-30 days')")
        
        # Filter out test/mock providers unless explicitly requested
        if not include_test_providers:
            test_providers = ['fake', 'MockLLM', 'error-provider', 'AuditedLLMProvider']
            placeholders = ','.join(['?' for _ in test_providers])
            where_conditions.append(f"provider NOT IN ({placeholders})")
            params.extend(test_providers)
        
        # Session filtering
        if session_id:
            where_conditions.append("session_id = ?")
            params.append(self._redact_session_id(session_id))
        
        # Build the complete query
        where_clause = " AND ".join(where_conditions) if where_conditions else "1=1"
        
        query = f"""
            SELECT 
                provider,
                model,
                COUNT(*) as call_count,
                AVG(latency_ms) as avg_latency,
                MIN(latency_ms) as min_latency,
                MAX(latency_ms) as max_latency,
                SUM(tokens) as total_tokens,
                MIN(created_at) as first_call,
                MAX(created_at) as last_call
            FROM runs 
            WHERE {where_clause}
            GROUP BY provider, model
            ORDER BY call_count DESC
        """
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(query, params)
            
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'provider': row[0],
                    'model': row[1],
                    'call_count': row[2],
                    'avg_latency': round(row[3], 2) if row[3] else 0,
                    'min_latency': row[4],
                    'max_latency': row[5],
                    'total_tokens': row[6] or 0,
                    'first_call': row[7],
                    'last_call': row[8]
                })
            
            return {'provider_stats': stats}
    
    def get_pattern_stats(self) -> Dict[str, Any]:
        """Get aggregated statistics by pattern."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT 
                    pattern_id,
                    COUNT(*) as match_count,
                    AVG(score) as avg_score,
                    MIN(score) as min_score,
                    MAX(score) as max_score,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted_count
                FROM matches 
                GROUP BY pattern_id
                ORDER BY match_count DESC
            """)
            
            stats = []
            for row in cursor.fetchall():
                stats.append({
                    'pattern_id': row[0],
                    'match_count': row[1],
                    'avg_score': round(row[2], 3) if row[2] else 0,
                    'min_score': row[3],
                    'max_score': row[4],
                    'accepted_count': row[5],
                    'acceptance_rate': round(row[5] / row[1], 3) if row[1] > 0 else 0
                })
            
            return {'pattern_stats': stats}
    
    def get_llm_messages(self, 
                        session_id: Optional[str] = None,
                        limit: int = 50) -> List[Dict[str, Any]]:
        """Get LLM messages (prompts and responses) for observability dashboard."""
        query = """
            SELECT id, session_id, provider, model, latency_ms, tokens, 
                   prompt, response, purpose, created_at
            FROM runs 
            WHERE 1=1
        """
        params = []
        
        if session_id:
            query += " AND session_id = ?"
            params.append(self._redact_session_id(session_id))
        
        query += " ORDER BY created_at DESC LIMIT ?"
        params.append(limit)
        
        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
        
        messages = []
        for row in rows:
            messages.append({
                'id': row['id'],
                'session_id': row['session_id'],
                'provider': row['provider'],
                'model': row['model'],
                'latency_ms': row['latency_ms'],
                'tokens': row['tokens'],
                'prompt': row['prompt'] if row['prompt'] else None,
                'response': row['response'] if row['response'] else None,
                'purpose': row['purpose'] if row['purpose'] else 'unknown',
                'created_at': row['created_at'],
                'timestamp': datetime.fromisoformat(row['created_at']).strftime('%Y-%m-%d %H:%M:%S') if row['created_at'] else 'Unknown'
            })
        
        return messages
    
    def cleanup_old_records(self, days: int = 30) -> int:
        """Remove audit records older than specified days."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)
        
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("DELETE FROM runs WHERE created_at < ?", (cutoff_date,))
            runs_deleted = cursor.rowcount
            
            cursor = conn.execute("DELETE FROM matches WHERE created_at < ?", (cutoff_date,))
            matches_deleted = cursor.rowcount
            
            conn.commit()
            
            total_deleted = runs_deleted + matches_deleted
            logger.info(f"Cleaned up {total_deleted} old audit records (runs: {runs_deleted}, matches: {matches_deleted})")
            
            return total_deleted


# Global audit logger instance
_audit_logger: Optional[AuditLogger] = None


def get_audit_logger(db_path: str = "audit.db", redact_pii: bool = True) -> AuditLogger:
    """Get or create the global audit logger instance."""
    global _audit_logger
    if _audit_logger is None:
        _audit_logger = AuditLogger(db_path=db_path, redact_pii=redact_pii)
    return _audit_logger


async def log_llm_call(session_id: str, provider: str, model: str, latency_ms: int, tokens: Optional[int] = None, prompt: Optional[str] = None, response: Optional[str] = None, purpose: Optional[str] = None) -> None:
    """Convenience function to log LLM calls."""
    audit_logger = get_audit_logger()
    await audit_logger.log_llm_call(session_id, provider, model, latency_ms, tokens, prompt, response, purpose)


async def log_pattern_match(session_id: str, pattern_id: str, score: float, accepted: Optional[bool] = None) -> None:
    """Convenience function to log pattern matches."""
    audit_logger = get_audit_logger()
    await audit_logger.log_pattern_match(session_id, pattern_id, score, accepted)