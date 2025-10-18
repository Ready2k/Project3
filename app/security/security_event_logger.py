"""
Security Event Logger - Comprehensive attack logging and monitoring system.

This module provides detailed security event logging, metrics collection,
progressive response measures, and alerting for the advanced prompt defense system.
"""

import asyncio
import json
import sqlite3
import time
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
from enum import Enum

from app.security.attack_patterns import SecurityDecision, SecurityAction
from app.security.defense_config import get_defense_config
from app.utils.logger import app_logger
from app.utils.redact import PIIRedactor


class AlertSeverity(Enum):
    """Alert severity levels."""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


@dataclass
class SecurityEvent:
    """Security event record."""

    event_id: str
    event_type: str
    timestamp: datetime
    session_id: str
    user_identifier: Optional[str]
    action: SecurityAction
    confidence: float
    processing_time_ms: float
    detected_attacks: List[Dict[str, Any]]
    detector_results: List[Dict[str, Any]]
    input_length: int
    input_preview: str
    evidence: List[str]
    alert_severity: AlertSeverity
    progressive_response_level: int
    metadata: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "event_id": self.event_id,
            "event_type": self.event_type,
            "timestamp": self.timestamp.isoformat(),
            "session_id": self.session_id,
            "user_identifier": self.user_identifier,
            "action": self.action.value,
            "confidence": self.confidence,
            "processing_time_ms": self.processing_time_ms,
            "detected_attacks": self.detected_attacks,
            "detector_results": self.detector_results,
            "input_length": self.input_length,
            "input_preview": self.input_preview,
            "evidence": self.evidence,
            "alert_severity": self.alert_severity.value,
            "progressive_response_level": self.progressive_response_level,
            "metadata": self.metadata,
        }


@dataclass
class SecurityMetrics:
    """Security metrics for monitoring."""

    total_requests: int = 0
    blocked_requests: int = 0
    flagged_requests: int = 0
    passed_requests: int = 0
    avg_processing_time_ms: float = 0.0
    detection_rate: float = 0.0
    false_positive_rate: float = 0.0
    attack_patterns_detected: Dict[str, int] = None
    detector_performance: Dict[str, Dict[str, Any]] = None
    progressive_responses: Dict[int, int] = None

    def __post_init__(self):
        if self.attack_patterns_detected is None:
            self.attack_patterns_detected = {}
        if self.detector_performance is None:
            self.detector_performance = {}
        if self.progressive_responses is None:
            self.progressive_responses = {}


class ProgressiveResponseManager:
    """Manages progressive response measures for repeated attack attempts."""

    def __init__(self, config=None):
        self.config = config or get_defense_config()
        # Track attempts by session/user identifier
        self.attempt_history: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.response_levels: Dict[str, int] = defaultdict(int)
        self.lockout_until: Dict[str, datetime] = {}

        # Progressive response thresholds
        self.level_thresholds = {
            1: 3,  # 3 attacks in window -> level 1
            2: 5,  # 5 attacks in window -> level 2
            3: 10,  # 10 attacks in window -> level 3
            4: 15,  # 15 attacks in window -> level 4 (lockout)
        }

        # Time windows for different levels (minutes)
        self.time_windows = {
            1: 5,  # 5 minutes
            2: 15,  # 15 minutes
            3: 30,  # 30 minutes
            4: 60,  # 60 minutes
        }

        # Lockout durations (minutes)
        self.lockout_durations = {
            1: 1,  # 1 minute
            2: 5,  # 5 minutes
            3: 15,  # 15 minutes
            4: 60,  # 60 minutes
        }

    def record_attack_attempt(
        self, identifier: str, attack_severity: AlertSeverity
    ) -> int:
        """Record an attack attempt and return current response level."""
        now = datetime.utcnow()

        # Check if currently locked out
        if identifier in self.lockout_until:
            if now < self.lockout_until[identifier]:
                return self.response_levels[identifier]
            else:
                # Lockout expired, reset
                del self.lockout_until[identifier]
                self.response_levels[identifier] = max(
                    0, self.response_levels[identifier] - 1
                )

        # Record the attempt with severity weight
        severity_weight = {
            AlertSeverity.LOW: 1,
            AlertSeverity.MEDIUM: 2,
            AlertSeverity.HIGH: 3,
            AlertSeverity.CRITICAL: 5,
        }.get(attack_severity, 1)

        # Add weighted attempts
        for _ in range(severity_weight):
            self.attempt_history[identifier].append(now)

        # Calculate current response level
        current_level = self._calculate_response_level(identifier, now)
        self.response_levels[identifier] = current_level

        # Apply lockout if necessary
        if current_level >= 4:
            lockout_duration = self.lockout_durations.get(current_level, 60)
            self.lockout_until[identifier] = now + timedelta(minutes=lockout_duration)

        return current_level

    def _calculate_response_level(self, identifier: str, now: datetime) -> int:
        """Calculate the current response level based on recent attempts."""
        attempts = self.attempt_history[identifier]

        # Count attempts in different time windows
        for level in sorted(self.level_thresholds.keys(), reverse=True):
            window_minutes = self.time_windows[level]
            threshold = self.level_thresholds[level]
            cutoff_time = now - timedelta(minutes=window_minutes)

            recent_attempts = sum(
                1 for attempt_time in attempts if attempt_time > cutoff_time
            )

            if recent_attempts >= threshold:
                return level

        return 0

    def get_response_level(self, identifier: str) -> int:
        """Get current response level for an identifier."""
        now = datetime.utcnow()

        # Check lockout status
        if identifier in self.lockout_until and now < self.lockout_until[identifier]:
            return self.response_levels[identifier]

        return self._calculate_response_level(identifier, now)

    def is_locked_out(self, identifier: str) -> Tuple[bool, Optional[datetime]]:
        """Check if identifier is currently locked out."""
        if identifier in self.lockout_until:
            lockout_until = self.lockout_until[identifier]
            if datetime.utcnow() < lockout_until:
                return True, lockout_until
            else:
                # Cleanup expired lockout
                del self.lockout_until[identifier]

        return False, None

    def cleanup_old_attempts(self) -> None:
        """Clean up old attempt records to prevent memory leaks."""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)

        for identifier in list(self.attempt_history.keys()):
            attempts = self.attempt_history[identifier]
            # Remove old attempts
            while attempts and attempts[0] < cutoff_time:
                attempts.popleft()

            # Remove empty histories
            if not attempts:
                del self.attempt_history[identifier]
                if identifier in self.response_levels:
                    del self.response_levels[identifier]


class SecurityEventLogger:
    """Comprehensive security event logger with monitoring and alerting."""

    def __init__(self, db_path: str = "security_audit.db", redact_pii: bool = True):
        self.db_path = Path(db_path)
        self.config = get_defense_config()
        self.redact_pii = redact_pii
        self.redactor = PIIRedactor() if redact_pii else None
        self.progressive_response = ProgressiveResponseManager(self.config)

        # Metrics tracking
        self.metrics = SecurityMetrics()
        self.metrics_window_start = datetime.utcnow()

        # Alert tracking
        self.recent_alerts: deque = deque(maxlen=1000)
        self.alert_callbacks: List[callable] = []

        # Initialize database
        self._init_database()

        # Start background cleanup task
        self._cleanup_task = None
        self._start_cleanup_task()

        app_logger.info("SecurityEventLogger initialized")

    def _init_database(self) -> None:
        """Initialize SQLite database for security events."""
        with sqlite3.connect(self.db_path) as conn:
            # Security events table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS security_events (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    event_id TEXT UNIQUE NOT NULL,
                    event_type TEXT NOT NULL,
                    timestamp TIMESTAMP NOT NULL,
                    session_id TEXT NOT NULL,
                    user_identifier TEXT,
                    action TEXT NOT NULL,
                    confidence REAL NOT NULL,
                    processing_time_ms REAL NOT NULL,
                    detected_attacks TEXT,  -- JSON
                    detector_results TEXT,  -- JSON
                    input_length INTEGER NOT NULL,
                    input_preview TEXT,
                    evidence TEXT,  -- JSON
                    alert_severity TEXT NOT NULL,
                    progressive_response_level INTEGER NOT NULL,
                    metadata TEXT  -- JSON
                )
            """
            )

            # Security metrics table
            conn.execute(
                """
                CREATE TABLE IF NOT EXISTS security_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp TIMESTAMP NOT NULL,
                    total_requests INTEGER NOT NULL,
                    blocked_requests INTEGER NOT NULL,
                    flagged_requests INTEGER NOT NULL,
                    passed_requests INTEGER NOT NULL,
                    avg_processing_time_ms REAL NOT NULL,
                    detection_rate REAL NOT NULL,
                    false_positive_rate REAL NOT NULL,
                    attack_patterns_detected TEXT,  -- JSON
                    detector_performance TEXT,  -- JSON
                    progressive_responses TEXT  -- JSON
                )
            """
            )

            # Create indexes
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_security_events_timestamp ON security_events(timestamp)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_security_events_session_id ON security_events(session_id)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_security_events_action ON security_events(action)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_security_events_alert_severity ON security_events(alert_severity)"
            )
            conn.execute(
                "CREATE INDEX IF NOT EXISTS idx_security_metrics_timestamp ON security_metrics(timestamp)"
            )

            conn.commit()

    def _start_cleanup_task(self) -> None:
        """Start background cleanup task."""

        async def cleanup_loop():
            while True:
                try:
                    await asyncio.sleep(3600)  # Run every hour
                    self.progressive_response.cleanup_old_attempts()
                    self._cleanup_old_events()
                except Exception as e:
                    app_logger.error(f"Error in security cleanup task: {e}")

        try:
            loop = asyncio.get_event_loop()
            self._cleanup_task = loop.create_task(cleanup_loop())
        except RuntimeError:
            # No event loop running, cleanup will be manual
            pass

    def _cleanup_old_events(self, days: int = 90) -> None:
        """Clean up old security events."""
        cutoff_date = datetime.utcnow() - timedelta(days=days)

        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute(
                "DELETE FROM security_events WHERE timestamp < ?", (cutoff_date,)
            )
            events_deleted = cursor.rowcount

            cursor = conn.execute(
                "DELETE FROM security_metrics WHERE timestamp < ?", (cutoff_date,)
            )
            metrics_deleted = cursor.rowcount

            conn.commit()

            if events_deleted > 0 or metrics_deleted > 0:
                app_logger.info(
                    f"Cleaned up old security records: {events_deleted} events, {metrics_deleted} metrics"
                )

    def _redact_sensitive_info(self, text: str) -> str:
        """Redact potentially sensitive information from text for logging."""
        if not self.redact_pii or not self.redactor:
            return text

        # Use the redactor first, then apply additional security-specific redaction
        redacted = self.redactor.redact(text)

        # Additional security-specific redaction patterns
        import re

        # Redact potential API keys, tokens, passwords
        redacted = re.sub(r"\b[A-Za-z0-9]{20,}\b", "[REDACTED_TOKEN]", redacted)
        redacted = re.sub(
            r"password\s+is\s+\w+",
            "password is [REDACTED]",
            redacted,
            flags=re.IGNORECASE,
        )
        redacted = re.sub(
            r"password[:\s=]+[^\s]+",
            "password=[REDACTED]",
            redacted,
            flags=re.IGNORECASE,
        )
        redacted = re.sub(
            r"token[:\s=]+[^\s]+", "token=[REDACTED]", redacted, flags=re.IGNORECASE
        )
        redacted = re.sub(
            r"key[:\s=]+[^\s]+", "key=[REDACTED]", redacted, flags=re.IGNORECASE
        )

        # Redact URLs (additional to what redactor might do)
        redacted = re.sub(r"https?://[^\s]+", "[URL]", redacted)

        return redacted

    def _generate_event_id(self) -> str:
        """Generate unique event ID."""
        import uuid

        return f"SEC_{int(time.time())}_{str(uuid.uuid4())[:8]}"

    def _determine_alert_severity(self, decision: SecurityDecision) -> AlertSeverity:
        """Determine alert severity based on security decision."""
        if decision.action == SecurityAction.BLOCK:
            if decision.confidence >= 0.95:
                return AlertSeverity.CRITICAL
            elif decision.confidence >= 0.8:
                return AlertSeverity.HIGH
            else:
                return AlertSeverity.MEDIUM
        elif decision.action == SecurityAction.FLAG:
            if decision.confidence >= 0.8:
                return AlertSeverity.MEDIUM
            else:
                return AlertSeverity.LOW
        else:
            return AlertSeverity.LOW

    def _extract_user_identifier(
        self, session_id: str, metadata: Dict[str, Any]
    ) -> str:
        """Extract user identifier for progressive response tracking."""
        # Use session_id as primary identifier
        # In production, this could be enhanced with IP address, user ID, etc.
        return session_id[:16]  # Use first 16 chars of session ID

    async def log_security_decision(
        self,
        decision: SecurityDecision,
        input_text: str,
        processing_time_ms: float,
        session_id: str = "unknown",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> None:
        """Log a security decision with full context and monitoring."""
        try:
            # Skip logging for PASS actions if configured
            if (
                not self.config.log_all_detections
                and decision.action == SecurityAction.PASS
            ):
                self._update_metrics(decision, processing_time_ms)
                return

            # Prepare event data
            event_id = self._generate_event_id()
            timestamp = datetime.utcnow()
            redacted_input = self._redact_sensitive_info(input_text)
            user_identifier = self._extract_user_identifier(session_id, metadata or {})

            # Determine alert severity
            alert_severity = self._determine_alert_severity(decision)

            # Handle progressive response for attacks
            progressive_response_level = 0
            if (
                decision.action in [SecurityAction.BLOCK, SecurityAction.FLAG]
                and decision.detected_attacks
            ):
                progressive_response_level = (
                    self.progressive_response.record_attack_attempt(
                        user_identifier, alert_severity
                    )
                )

            # Prepare attack data
            detected_attacks = [
                {
                    "pattern_id": pattern.id,
                    "category": pattern.category,
                    "name": pattern.name,
                    "severity": pattern.severity.value,
                    "description": pattern.description,
                }
                for pattern in decision.detected_attacks
            ]

            # Prepare detector results
            detector_results = []
            if hasattr(decision, "detection_results") and decision.detection_results:
                detector_results = [
                    {
                        "detector": result.detector_name,
                        "is_attack": result.is_attack,
                        "confidence": result.confidence,
                        "patterns": [p.id for p in result.matched_patterns],
                        "evidence_count": (
                            len(result.evidence)
                            if isinstance(result.evidence, list)
                            else 1
                        ),
                    }
                    for result in decision.detection_results
                ]

            # Extract evidence
            evidence = []
            if hasattr(decision, "detection_results") and decision.detection_results:
                for result in decision.detection_results:
                    if isinstance(result.evidence, list):
                        evidence.extend(
                            result.evidence[:5]
                        )  # Limit evidence per detector
                    elif result.evidence:
                        evidence.append(str(result.evidence))

            # Create security event
            security_event = SecurityEvent(
                event_id=event_id,
                event_type="security_decision",
                timestamp=timestamp,
                session_id=session_id,
                user_identifier=user_identifier,
                action=decision.action,
                confidence=decision.confidence,
                processing_time_ms=processing_time_ms,
                detected_attacks=detected_attacks,
                detector_results=detector_results,
                input_length=len(input_text),
                input_preview=(
                    redacted_input[:500] + "..."
                    if len(redacted_input) > 500
                    else redacted_input
                ),
                evidence=evidence[:20],  # Limit total evidence
                alert_severity=alert_severity,
                progressive_response_level=progressive_response_level,
                metadata=metadata or {},
            )

            # Store in database
            await self._store_security_event(security_event)

            # Update metrics
            self._update_metrics(decision, processing_time_ms)

            # Log to application logger
            self._log_to_app_logger(security_event)

            # Trigger alerts if necessary
            if self.config.alert_on_attacks and decision.action != SecurityAction.PASS:
                await self._trigger_alert(security_event)

        except Exception as e:
            app_logger.error(f"Error logging security decision: {e}")

    async def _store_security_event(self, event: SecurityEvent) -> None:
        """Store security event in database."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute(
                """
                INSERT INTO security_events (
                    event_id, event_type, timestamp, session_id, user_identifier,
                    action, confidence, processing_time_ms, detected_attacks,
                    detector_results, input_length, input_preview, evidence,
                    alert_severity, progressive_response_level, metadata
                ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
                (
                    event.event_id,
                    event.event_type,
                    event.timestamp,
                    event.session_id,
                    event.user_identifier,
                    event.action.value,
                    event.confidence,
                    event.processing_time_ms,
                    json.dumps(event.detected_attacks),
                    json.dumps(event.detector_results),
                    event.input_length,
                    event.input_preview,
                    json.dumps(event.evidence),
                    event.alert_severity.value,
                    event.progressive_response_level,
                    json.dumps(event.metadata),
                ),
            )
            conn.commit()

    def _update_metrics(
        self, decision: SecurityDecision, processing_time_ms: float
    ) -> None:
        """Update security metrics."""
        self.metrics.total_requests += 1

        if decision.action == SecurityAction.BLOCK:
            self.metrics.blocked_requests += 1
        elif decision.action == SecurityAction.FLAG:
            self.metrics.flagged_requests += 1
        else:
            self.metrics.passed_requests += 1

        # Update processing time (running average)
        if self.metrics.total_requests == 1:
            self.metrics.avg_processing_time_ms = processing_time_ms
        else:
            # Exponential moving average
            alpha = 0.1
            self.metrics.avg_processing_time_ms = (
                alpha * processing_time_ms
                + (1 - alpha) * self.metrics.avg_processing_time_ms
            )

        # Update detection rate
        detected_requests = (
            self.metrics.blocked_requests + self.metrics.flagged_requests
        )
        self.metrics.detection_rate = detected_requests / self.metrics.total_requests

        # Update attack pattern counts
        for pattern in decision.detected_attacks:
            pattern_id = pattern.id
            self.metrics.attack_patterns_detected[pattern_id] = (
                self.metrics.attack_patterns_detected.get(pattern_id, 0) + 1
            )

    def _log_to_app_logger(self, event: SecurityEvent) -> None:
        """Log security event to application logger."""
        log_data = {
            "event_id": event.event_id,
            "action": event.action.value,
            "confidence": event.confidence,
            "processing_time_ms": event.processing_time_ms,
            "attack_count": len(event.detected_attacks),
            "alert_severity": event.alert_severity.value,
            "progressive_level": event.progressive_response_level,
            "input_length": event.input_length,
        }

        if event.action == SecurityAction.BLOCK:
            app_logger.warning(f"SECURITY BLOCK: {log_data}")
        elif event.action == SecurityAction.FLAG:
            app_logger.info(f"SECURITY FLAG: {log_data}")
        else:
            app_logger.debug(f"SECURITY PASS: {log_data}")

    async def _trigger_alert(self, event: SecurityEvent) -> None:
        """Trigger security alert for high-severity events."""
        try:
            # Add to recent alerts
            self.recent_alerts.append(
                {
                    "timestamp": event.timestamp.isoformat(),
                    "event_id": event.event_id,
                    "severity": event.alert_severity.value,
                    "action": event.action.value,
                    "confidence": event.confidence,
                    "attack_count": len(event.detected_attacks),
                    "progressive_level": event.progressive_response_level,
                }
            )

            # Call registered alert callbacks
            for callback in self.alert_callbacks:
                try:
                    if asyncio.iscoroutinefunction(callback):
                        await callback(event)
                    else:
                        callback(event)
                except Exception as e:
                    app_logger.error(f"Error in alert callback: {e}")

            # Log high-severity alerts
            if event.alert_severity in [AlertSeverity.HIGH, AlertSeverity.CRITICAL]:
                app_logger.warning(
                    f"HIGH SEVERITY SECURITY ALERT: {event.event_id} - "
                    f"{event.alert_severity.value} - {len(event.detected_attacks)} attacks detected"
                )

        except Exception as e:
            app_logger.error(f"Error triggering security alert: {e}")

    def register_alert_callback(self, callback: callable) -> None:
        """Register callback for security alerts."""
        self.alert_callbacks.append(callback)

    def get_security_metrics(self, time_window_hours: int = 24) -> SecurityMetrics:
        """Get current security metrics."""
        # Store current metrics snapshot
        if self.config.metrics_enabled:
            try:
                asyncio.create_task(self._store_metrics_snapshot())
            except RuntimeError:
                # No event loop running, skip async metrics storage
                pass

        return self.metrics

    async def _store_metrics_snapshot(self) -> None:
        """Store current metrics snapshot to database."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO security_metrics (
                        timestamp, total_requests, blocked_requests, flagged_requests,
                        passed_requests, avg_processing_time_ms, detection_rate,
                        false_positive_rate, attack_patterns_detected,
                        detector_performance, progressive_responses
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        datetime.utcnow(),
                        self.metrics.total_requests,
                        self.metrics.blocked_requests,
                        self.metrics.flagged_requests,
                        self.metrics.passed_requests,
                        self.metrics.avg_processing_time_ms,
                        self.metrics.detection_rate,
                        self.metrics.false_positive_rate,
                        json.dumps(self.metrics.attack_patterns_detected),
                        json.dumps(self.metrics.detector_performance),
                        json.dumps(self.metrics.progressive_responses),
                    ),
                )
                conn.commit()
        except Exception as e:
            app_logger.error(f"Error storing metrics snapshot: {e}")

    def get_recent_events(
        self,
        limit: int = 100,
        action_filter: Optional[SecurityAction] = None,
        severity_filter: Optional[AlertSeverity] = None,
    ) -> List[Dict[str, Any]]:
        """Get recent security events."""
        query = "SELECT * FROM security_events WHERE 1=1"
        params = []

        if action_filter:
            query += " AND action = ?"
            params.append(action_filter.value)

        if severity_filter:
            query += " AND alert_severity = ?"
            params.append(severity_filter.value)

        query += " ORDER BY timestamp DESC LIMIT ?"
        params.append(limit)

        with sqlite3.connect(self.db_path) as conn:
            conn.row_factory = sqlite3.Row
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()

        events = []
        for row in rows:
            events.append(
                {
                    "event_id": row["event_id"],
                    "timestamp": row["timestamp"],
                    "session_id": row["session_id"],
                    "action": row["action"],
                    "confidence": row["confidence"],
                    "processing_time_ms": row["processing_time_ms"],
                    "detected_attacks": (
                        json.loads(row["detected_attacks"])
                        if row["detected_attacks"]
                        else []
                    ),
                    "alert_severity": row["alert_severity"],
                    "progressive_response_level": row["progressive_response_level"],
                    "input_length": row["input_length"],
                    "input_preview": row["input_preview"],
                }
            )

        return events

    def get_attack_statistics(self, time_window_hours: int = 24) -> Dict[str, Any]:
        """Get attack statistics for the specified time window."""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)

        with sqlite3.connect(self.db_path) as conn:
            # Total events
            cursor = conn.execute(
                "SELECT COUNT(*) FROM security_events WHERE timestamp > ?",
                (cutoff_time,),
            )
            total_events = cursor.fetchone()[0]

            # Events by action
            cursor = conn.execute(
                """
                SELECT action, COUNT(*) as count
                FROM security_events 
                WHERE timestamp > ?
                GROUP BY action
            """,
                (cutoff_time,),
            )
            action_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Events by severity
            cursor = conn.execute(
                """
                SELECT alert_severity, COUNT(*) as count
                FROM security_events 
                WHERE timestamp > ?
                GROUP BY alert_severity
            """,
                (cutoff_time,),
            )
            severity_counts = {row[0]: row[1] for row in cursor.fetchall()}

            # Top attack patterns
            cursor = conn.execute(
                """
                SELECT detected_attacks, COUNT(*) as count
                FROM security_events 
                WHERE timestamp > ? AND detected_attacks != '[]'
                GROUP BY detected_attacks
                ORDER BY count DESC
                LIMIT 10
            """,
                (cutoff_time,),
            )

            pattern_counts = {}
            for row in cursor.fetchall():
                try:
                    attacks = json.loads(row[0])
                    for attack in attacks:
                        pattern_id = attack.get("pattern_id", "unknown")
                        pattern_counts[pattern_id] = (
                            pattern_counts.get(pattern_id, 0) + row[1]
                        )
                except json.JSONDecodeError:
                    continue

        return {
            "time_window_hours": time_window_hours,
            "total_events": total_events,
            "action_counts": action_counts,
            "severity_counts": severity_counts,
            "top_attack_patterns": dict(
                sorted(pattern_counts.items(), key=lambda x: x[1], reverse=True)[:10]
            ),
            "detection_rate": (
                action_counts.get("block", 0) + action_counts.get("flag", 0)
            )
            / max(total_events, 1),
        }

    def get_progressive_response_status(self) -> Dict[str, Any]:
        """Get current progressive response status."""
        return {
            "active_response_levels": dict(self.progressive_response.response_levels),
            "locked_out_users": {
                identifier: until.isoformat()
                for identifier, until in self.progressive_response.lockout_until.items()
                if datetime.utcnow() < until
            },
            "recent_attempt_counts": {
                identifier: len(attempts)
                for identifier, attempts in self.progressive_response.attempt_history.items()
            },
        }

    def reset_progressive_response(self, user_identifier: str) -> bool:
        """Reset progressive response for a user (admin function)."""
        try:
            if user_identifier in self.progressive_response.response_levels:
                del self.progressive_response.response_levels[user_identifier]

            if user_identifier in self.progressive_response.lockout_until:
                del self.progressive_response.lockout_until[user_identifier]

            if user_identifier in self.progressive_response.attempt_history:
                del self.progressive_response.attempt_history[user_identifier]

            app_logger.info(f"Reset progressive response for user: {user_identifier}")
            return True
        except Exception as e:
            app_logger.error(f"Error resetting progressive response: {e}")
            return False

    async def log_performance_alert(
        self, alert_type: str, alert_data: Dict[str, Any]
    ) -> None:
        """Log performance alert for monitoring."""
        try:
            event_id = self._generate_event_id()
            timestamp = datetime.utcnow()

            # Create performance event
            performance_event = {
                "event_id": event_id,
                "event_type": "performance_alert",
                "timestamp": timestamp.isoformat(),
                "alert_type": alert_type,
                "alert_data": alert_data,
                "severity": self._determine_performance_severity(
                    alert_type, alert_data
                ),
            }

            # Store in database
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    """
                    INSERT INTO security_events (
                        event_id, event_type, timestamp, session_id, user_identifier,
                        action, confidence, processing_time_ms, detected_attacks,
                        detector_results, input_length, input_preview, evidence,
                        alert_severity, progressive_response_level, metadata
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                    (
                        event_id,
                        "performance_alert",
                        timestamp.isoformat(),
                        "system",
                        "system",
                        "MONITOR",
                        0.0,
                        alert_data.get("value", 0.0),
                        json.dumps([]),
                        json.dumps([]),
                        0,
                        f"Performance alert: {alert_type}",
                        json.dumps([alert_data.get("message", "")]),
                        performance_event["severity"],
                        0,
                        json.dumps(alert_data),
                    ),
                )
                conn.commit()

            # Log to application logger
            app_logger.warning(
                f"PERFORMANCE ALERT [{alert_type}]: {alert_data.get('message', 'Unknown issue')}"
            )

            # Trigger alert callbacks
            for callback in self.alert_callbacks:
                try:
                    callback(performance_event)
                except Exception as e:
                    app_logger.error(f"Error in performance alert callback: {e}")

        except Exception as e:
            app_logger.error(f"Error logging performance alert: {e}")

    def _determine_performance_severity(
        self, alert_type: str, alert_data: Dict[str, Any]
    ) -> str:
        """Determine severity of performance alert."""
        if alert_type == "high_latency":
            latency = alert_data.get("value", 0)
            if latency > 100:
                return AlertSeverity.HIGH.value
            elif latency > 75:
                return AlertSeverity.MEDIUM.value
            else:
                return AlertSeverity.LOW.value

        elif alert_type == "high_memory_usage":
            memory_mb = alert_data.get("value", 0)
            if memory_mb > 450:  # 90% of 512MB limit
                return AlertSeverity.CRITICAL.value
            elif memory_mb > 400:  # 80% of limit
                return AlertSeverity.HIGH.value
            else:
                return AlertSeverity.MEDIUM.value

        elif alert_type == "timeout_errors":
            return AlertSeverity.HIGH.value

        elif alert_type == "low_cache_hit_rate":
            hit_rate = alert_data.get("value", 100)
            if hit_rate < 10:
                return AlertSeverity.HIGH.value
            elif hit_rate < 30:
                return AlertSeverity.MEDIUM.value
            else:
                return AlertSeverity.LOW.value

        return AlertSeverity.MEDIUM.value

    def __del__(self):
        """Cleanup resources."""
        if hasattr(self, "_cleanup_task") and self._cleanup_task:
            try:
                self._cleanup_task.cancel()
            except Exception:
                pass
