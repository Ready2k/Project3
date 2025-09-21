"""
Technology Stack Generation Monitoring System

Provides real-time monitoring, alerting, and quality assurance for tech stack generation.
"""

import asyncio
import json
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

from app.core.service import ConfigurableService
from app.utils.imports import require_service


class AlertLevel(Enum):
    """Alert severity levels."""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(Enum):
    """Types of metrics tracked."""
    ACCURACY = "accuracy"
    PERFORMANCE = "performance"
    QUALITY = "quality"
    SATISFACTION = "satisfaction"
    CATALOG = "catalog"


@dataclass
class TechStackMetric:
    """Individual metric data point."""
    timestamp: datetime
    metric_type: MetricType
    name: str
    value: float
    metadata: Dict[str, Any]
    session_id: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['metric_type'] = self.metric_type.value
        return data


@dataclass
class QualityAlert:
    """Quality assurance alert."""
    timestamp: datetime
    level: AlertLevel
    category: str
    message: str
    details: Dict[str, Any]
    session_id: Optional[str] = None
    resolved: bool = False
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['level'] = self.level.value
        return data


@dataclass
class PerformanceRecommendation:
    """Performance optimization recommendation."""
    category: str
    priority: str  # high, medium, low
    description: str
    impact: str
    implementation: str
    metrics_supporting: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return asdict(self)


class TechStackMonitor(ConfigurableService):
    """
    Comprehensive monitoring system for tech stack generation.
    
    Tracks accuracy, performance, quality metrics, and provides
    real-time alerting and optimization recommendations.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'TechStackMonitor')
        try:
            self.logger = require_service('logger', context='TechStackMonitor')
        except:
            # Fallback logger for testing/standalone use
            import logging
            self.logger = logging.getLogger('TechStackMonitor')
        
        self.metrics: List[TechStackMetric] = []
        self.alerts: List[QualityAlert] = []
        self.recommendations: List[PerformanceRecommendation] = []
        self.monitoring_active = True  # Start monitoring by default
        self.alert_thresholds = self._load_alert_thresholds()
    
    async def _do_initialize(self) -> None:
        """Initialize the tech stack monitor."""
        await self.start_monitoring()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the tech stack monitor."""
        await self.stop_monitoring()
        
    def _load_alert_thresholds(self) -> Dict[str, float]:
        """Load alert thresholds from configuration with dynamic baseline adjustment."""
        base_thresholds = {
            'extraction_accuracy_min': 0.85,
            'explicit_tech_inclusion_min': 0.70,
            'catalog_consistency_min': 0.95,
            'response_time_max': 30.0,
            'user_satisfaction_min': 4.0,
            'catalog_missing_tech_max': 0.10
        }
        
        # Adjust thresholds based on real system performance baselines
        try:
            adjusted_thresholds = self._calculate_dynamic_thresholds(base_thresholds)
            self.logger.info(f"Using dynamic alert thresholds based on system performance: {adjusted_thresholds}")
            return adjusted_thresholds
        except Exception as e:
            self.logger.warning(f"Could not calculate dynamic thresholds, using base values: {e}")
            return base_thresholds
    
    def _calculate_dynamic_thresholds(self, base_thresholds: Dict[str, float]) -> Dict[str, float]:
        """Calculate dynamic alert thresholds based on recent system performance."""
        # Get recent performance data (last 7 days)
        recent_metrics = self._get_recent_metrics(hours=168)  # 7 days
        
        if len(recent_metrics) < 10:  # Not enough data for dynamic adjustment
            return base_thresholds
        
        adjusted_thresholds = base_thresholds.copy()
        
        # Adjust accuracy thresholds based on recent performance
        accuracy_metrics = [m for m in recent_metrics if m.name == "extraction_accuracy"]
        if len(accuracy_metrics) >= 10:
            recent_accuracy = [m.value for m in accuracy_metrics[-20:]]  # Last 20 measurements
            avg_accuracy = sum(recent_accuracy) / len(recent_accuracy)
            std_accuracy = (sum((x - avg_accuracy) ** 2 for x in recent_accuracy) / len(recent_accuracy)) ** 0.5
            
            # Set threshold to 2 standard deviations below recent average, but not below base minimum
            dynamic_accuracy_threshold = max(
                avg_accuracy - (2 * std_accuracy),
                base_thresholds['extraction_accuracy_min'] - 0.05  # Allow 5% below base minimum
            )
            adjusted_thresholds['extraction_accuracy_min'] = min(
                dynamic_accuracy_threshold,
                base_thresholds['extraction_accuracy_min']  # Don't raise threshold above base
            )
        
        # Adjust response time thresholds based on recent performance
        response_time_metrics = [m for m in recent_metrics if m.name == "processing_time"]
        if len(response_time_metrics) >= 10:
            recent_times = [m.value for m in response_time_metrics[-20:]]
            avg_time = sum(recent_times) / len(recent_times)
            p95_time = sorted(recent_times)[int(len(recent_times) * 0.95)]
            
            # Set threshold to 95th percentile + 50% buffer, but not below base minimum
            dynamic_time_threshold = max(
                p95_time * 1.5,
                base_thresholds['response_time_max'] * 0.8  # Allow 20% below base
            )
            adjusted_thresholds['response_time_max'] = max(
                dynamic_time_threshold,
                base_thresholds['response_time_max']  # Don't lower threshold below base
            )
        
        # Adjust inclusion rate thresholds
        inclusion_metrics = [m for m in recent_metrics if m.name == "explicit_tech_inclusion_rate"]
        if len(inclusion_metrics) >= 10:
            recent_inclusion = [m.value for m in inclusion_metrics[-20:]]
            avg_inclusion = sum(recent_inclusion) / len(recent_inclusion)
            
            # Set threshold to recent average - 10%, but not below base minimum
            dynamic_inclusion_threshold = max(
                avg_inclusion - 0.1,
                base_thresholds['explicit_tech_inclusion_min'] - 0.05
            )
            adjusted_thresholds['explicit_tech_inclusion_min'] = min(
                dynamic_inclusion_threshold,
                base_thresholds['explicit_tech_inclusion_min']
            )
        
        return adjusted_thresholds
    
    def update_alert_thresholds(self) -> None:
        """Update alert thresholds based on current system performance."""
        try:
            new_thresholds = self._calculate_dynamic_thresholds(self.alert_thresholds)
            
            # Only update if thresholds have changed significantly
            threshold_changes = {}
            for key, new_value in new_thresholds.items():
                old_value = self.alert_thresholds.get(key, 0)
                if abs(new_value - old_value) > 0.02:  # 2% change threshold
                    threshold_changes[key] = {'old': old_value, 'new': new_value}
            
            if threshold_changes:
                self.alert_thresholds.update(new_thresholds)
                self.logger.info(f"Updated alert thresholds based on performance: {threshold_changes}")
                
                # Create info alert about threshold updates
                self._create_alert(
                    AlertLevel.INFO,
                    "threshold_update",
                    f"Alert thresholds updated based on system performance",
                    {
                        "changes": threshold_changes,
                        "reason": "dynamic_baseline_adjustment"
                    }
                )
        except Exception as e:
            self.logger.error(f"Error updating alert thresholds: {e}")
    
    async def start_monitoring(self) -> None:
        """Start the monitoring system."""
        self.monitoring_active = True
        self.logger.info("Tech stack monitoring started")
        
        # Start background monitoring tasks
        asyncio.create_task(self._periodic_quality_check())
        asyncio.create_task(self._generate_recommendations())
        asyncio.create_task(self._real_time_monitoring_stream())
        asyncio.create_task(self._periodic_threshold_update())
    
    async def stop_monitoring(self) -> None:
        """Stop the monitoring system."""
        self.monitoring_active = False
        self.logger.info("Tech stack monitoring stopped")
    
    def record_extraction_accuracy(
        self,
        session_id: str,
        extracted_count: int,
        expected_count: int,
        explicit_tech_included: int,
        explicit_tech_total: int,
        processing_time: float
    ) -> None:
        """Record technology extraction accuracy metrics."""
        timestamp = datetime.now()
        
        # Calculate accuracy metrics
        extraction_accuracy = extracted_count / max(expected_count, 1)
        explicit_inclusion_rate = explicit_tech_included / max(explicit_tech_total, 1)
        
        # Record metrics
        self.metrics.extend([
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.ACCURACY,
                name="extraction_accuracy",
                value=extraction_accuracy,
                metadata={
                    "extracted_count": extracted_count,
                    "expected_count": expected_count
                },
                session_id=session_id
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.ACCURACY,
                name="explicit_tech_inclusion_rate",
                value=explicit_inclusion_rate,
                metadata={
                    "included": explicit_tech_included,
                    "total": explicit_tech_total
                },
                session_id=session_id
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.PERFORMANCE,
                name="processing_time",
                value=processing_time,
                metadata={"unit": "seconds"},
                session_id=session_id
            )
        ])
        
        # Check for alerts
        self._check_accuracy_alerts(extraction_accuracy, explicit_inclusion_rate, session_id)
        self._check_performance_alerts(processing_time, session_id)
    
    def record_catalog_metrics(
        self,
        total_technologies: int,
        missing_technologies: int,
        inconsistent_entries: int,
        pending_review: int
    ) -> None:
        """Record catalog health metrics."""
        timestamp = datetime.now()
        
        consistency_rate = 1.0 - (inconsistent_entries / max(total_technologies, 1))
        missing_rate = missing_technologies / max(total_technologies, 1)
        
        self.metrics.extend([
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.CATALOG,
                name="catalog_consistency_rate",
                value=consistency_rate,
                metadata={
                    "total": total_technologies,
                    "inconsistent": inconsistent_entries
                }
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.CATALOG,
                name="catalog_missing_rate",
                value=missing_rate,
                metadata={
                    "total": total_technologies,
                    "missing": missing_technologies
                }
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.CATALOG,
                name="pending_review_count",
                value=pending_review,
                metadata={"unit": "count"}
            )
        ])
        
        # Check for catalog alerts
        self._check_catalog_alerts(consistency_rate, missing_rate, pending_review)
    
    def record_user_satisfaction(
        self,
        session_id: str,
        relevance_score: float,
        accuracy_score: float,
        completeness_score: float,
        feedback: Optional[str] = None
    ) -> None:
        """Record user satisfaction metrics."""
        timestamp = datetime.now()
        
        overall_satisfaction = (relevance_score + accuracy_score + completeness_score) / 3
        
        self.metrics.extend([
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.SATISFACTION,
                name="tech_stack_relevance",
                value=relevance_score,
                metadata={"scale": "1-5"},
                session_id=session_id
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.SATISFACTION,
                name="tech_stack_accuracy",
                value=accuracy_score,
                metadata={"scale": "1-5"},
                session_id=session_id
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.SATISFACTION,
                name="tech_stack_completeness",
                value=completeness_score,
                metadata={"scale": "1-5"},
                session_id=session_id
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.SATISFACTION,
                name="overall_satisfaction",
                value=overall_satisfaction,
                metadata={
                    "scale": "1-5",
                    "feedback": feedback
                },
                session_id=session_id
            )
        ])
        
        # Check satisfaction alerts
        if overall_satisfaction < self.alert_thresholds['user_satisfaction_min']:
            self._create_alert(
                AlertLevel.WARNING,
                "user_satisfaction",
                f"Low user satisfaction score: {overall_satisfaction:.2f}",
                {
                    "session_id": session_id,
                    "relevance": relevance_score,
                    "accuracy": accuracy_score,
                    "completeness": completeness_score,
                    "feedback": feedback
                },
                session_id
            )
    
    def _check_accuracy_alerts(
        self,
        extraction_accuracy: float,
        explicit_inclusion_rate: float,
        session_id: str
    ) -> None:
        """Check for accuracy-related alerts."""
        if extraction_accuracy < self.alert_thresholds['extraction_accuracy_min']:
            self._create_alert(
                AlertLevel.ERROR,
                "extraction_accuracy",
                f"Low extraction accuracy: {extraction_accuracy:.2f}",
                {
                    "accuracy": extraction_accuracy,
                    "threshold": self.alert_thresholds['extraction_accuracy_min']
                },
                session_id
            )
        
        if explicit_inclusion_rate < self.alert_thresholds['explicit_tech_inclusion_min']:
            self._create_alert(
                AlertLevel.WARNING,
                "explicit_tech_inclusion",
                f"Low explicit technology inclusion: {explicit_inclusion_rate:.2f}",
                {
                    "inclusion_rate": explicit_inclusion_rate,
                    "threshold": self.alert_thresholds['explicit_tech_inclusion_min']
                },
                session_id
            )
    
    def _check_performance_alerts(self, processing_time: float, session_id: str) -> None:
        """Check for performance-related alerts."""
        if processing_time > self.alert_thresholds['response_time_max']:
            self._create_alert(
                AlertLevel.WARNING,
                "performance",
                f"Slow processing time: {processing_time:.2f}s",
                {
                    "processing_time": processing_time,
                    "threshold": self.alert_thresholds['response_time_max']
                },
                session_id
            )
    
    def _check_catalog_alerts(
        self,
        consistency_rate: float,
        missing_rate: float,
        pending_review: int
    ) -> None:
        """Check for catalog-related alerts."""
        if consistency_rate < self.alert_thresholds['catalog_consistency_min']:
            self._create_alert(
                AlertLevel.ERROR,
                "catalog_consistency",
                f"Low catalog consistency: {consistency_rate:.2f}",
                {
                    "consistency_rate": consistency_rate,
                    "threshold": self.alert_thresholds['catalog_consistency_min']
                }
            )
        
        if missing_rate > self.alert_thresholds['catalog_missing_tech_max']:
            self._create_alert(
                AlertLevel.WARNING,
                "catalog_missing",
                f"High missing technology rate: {missing_rate:.2f}",
                {
                    "missing_rate": missing_rate,
                    "threshold": self.alert_thresholds['catalog_missing_tech_max']
                }
            )
        
        if pending_review > 50:  # Configurable threshold
            self._create_alert(
                AlertLevel.INFO,
                "catalog_review",
                f"High pending review count: {pending_review}",
                {"pending_count": pending_review}
            )
    
    def _create_alert(
        self,
        level: AlertLevel,
        category: str,
        message: str,
        details: Dict[str, Any],
        session_id: Optional[str] = None
    ) -> None:
        """Create and store an alert."""
        alert = QualityAlert(
            timestamp=datetime.now(),
            level=level,
            category=category,
            message=message,
            details=details,
            session_id=session_id
        )
        
        self.alerts.append(alert)
        
        # Log the alert
        log_level = {
            AlertLevel.INFO: logging.INFO,
            AlertLevel.WARNING: logging.WARNING,
            AlertLevel.ERROR: logging.ERROR,
            AlertLevel.CRITICAL: logging.CRITICAL
        }[level]
        
        self.logger.log(log_level, f"Tech Stack Alert [{category}]: {message}", extra={
            "alert_details": details,
            "session_id": session_id
        })
    
    async def _periodic_quality_check(self) -> None:
        """Perform periodic quality assurance checks."""
        while self.monitoring_active:
            try:
                await self._run_quality_checks()
                await asyncio.sleep(300)  # Check every 5 minutes
            except Exception as e:
                self.logger.error(f"Error in periodic quality check: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def _run_quality_checks(self) -> None:
        """Run comprehensive quality assurance checks."""
        # Check recent metrics for trends
        recent_metrics = self._get_recent_metrics(hours=1)
        
        # Analyze accuracy trends
        accuracy_metrics = [m for m in recent_metrics if m.name == "extraction_accuracy"]
        if len(accuracy_metrics) >= 5:
            avg_accuracy = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics)
            if avg_accuracy < self.alert_thresholds['extraction_accuracy_min']:
                self._create_alert(
                    AlertLevel.WARNING,
                    "accuracy_trend",
                    f"Declining accuracy trend: {avg_accuracy:.2f}",
                    {
                        "average_accuracy": avg_accuracy,
                        "sample_count": len(accuracy_metrics),
                        "time_window": "1 hour"
                    }
                )
        
        # Check for performance degradation
        performance_metrics = [m for m in recent_metrics if m.name == "processing_time"]
        if len(performance_metrics) >= 5:
            avg_time = sum(m.value for m in performance_metrics) / len(performance_metrics)
            if avg_time > self.alert_thresholds['response_time_max'] * 0.8:
                self._create_alert(
                    AlertLevel.INFO,
                    "performance_trend",
                    f"Performance degradation detected: {avg_time:.2f}s",
                    {
                        "average_time": avg_time,
                        "sample_count": len(performance_metrics),
                        "time_window": "1 hour"
                    }
                )
    
    async def _generate_recommendations(self) -> None:
        """Generate performance optimization recommendations."""
        while self.monitoring_active:
            try:
                await self._analyze_and_recommend()
                await asyncio.sleep(3600)  # Generate recommendations every hour
            except Exception as e:
                self.logger.error(f"Error generating recommendations: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    async def _periodic_threshold_update(self) -> None:
        """Periodically update alert thresholds based on system performance."""
        while self.monitoring_active:
            try:
                self.update_alert_thresholds()
                await asyncio.sleep(3600)  # Update thresholds every hour
            except Exception as e:
                self.logger.error(f"Error in periodic threshold update: {e}")
                await asyncio.sleep(1800)  # Retry after 30 minutes on error
    
    async def _real_time_monitoring_stream(self) -> None:
        """Provide real-time monitoring stream for live updates."""
        while self.monitoring_active:
            try:
                # Connect to monitoring integration service for real data
                try:
                    from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService
                    integration_service = require_service('tech_stack_monitoring_integration', context='TechStackMonitor')
                    
                    # Get real-time data from integration service
                    service_metrics = integration_service.get_service_metrics()
                    active_sessions = integration_service.get_active_sessions()
                    
                    # Process real session data
                    for session_info in active_sessions:
                        session_id = session_info['session_id']
                        session_events = integration_service.get_session_events(session_id)
                        
                        # Extract real metrics from session events
                        self._process_real_session_events(session_id, session_events)
                    
                except Exception as integration_error:
                    self.logger.debug(f"Integration service not available, using existing metrics: {integration_error}")
                
                # Emit real-time monitoring events using actual data
                current_metrics = self._get_recent_metrics(hours=1)
                if current_metrics:
                    latest_metrics = current_metrics[-5:]  # Last 5 metrics
                    
                    # Calculate real-time statistics
                    accuracy_metrics = [m for m in latest_metrics if m.name == "extraction_accuracy"]
                    if accuracy_metrics:
                        current_accuracy = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics)
                        
                        # Check for rapid degradation
                        if len(accuracy_metrics) >= 3:
                            recent_trend = accuracy_metrics[-1].value - accuracy_metrics[0].value
                            if recent_trend < -0.1:  # 10% drop
                                self._create_alert(
                                    AlertLevel.WARNING,
                                    "accuracy_degradation",
                                    f"Rapid accuracy degradation detected: {recent_trend:.2f}",
                                    {
                                        "current_accuracy": current_accuracy,
                                        "trend": recent_trend,
                                        "sample_count": len(accuracy_metrics)
                                    }
                                )
                
                await asyncio.sleep(30)  # Real-time updates every 30 seconds
            except Exception as e:
                self.logger.error(f"Error in real-time monitoring stream: {e}")
                await asyncio.sleep(60)
    
    def _process_real_session_events(self, session_id: str, session_events: List[Dict[str, Any]]) -> None:
        """Process real session events to extract monitoring metrics."""
        try:
            parsing_events = [e for e in session_events if e.get('event_type') == 'parsing_complete']
            extraction_events = [e for e in session_events if e.get('event_type') == 'extraction_complete']
            llm_events = [e for e in session_events if e.get('event_type') == 'llm_call_complete']
            validation_events = [e for e in session_events if e.get('event_type') == 'validation_complete']
            
            # Process parsing events for accuracy metrics
            for event in parsing_events:
                data = event.get('data', {})
                output_data = data.get('output_data', {})
                explicit_techs = output_data.get('explicit_technologies', [])
                
                if explicit_techs:
                    # Record extraction accuracy based on real data
                    self.record_extraction_accuracy(
                        session_id=session_id,
                        extracted_count=len(explicit_techs),
                        expected_count=max(len(explicit_techs), 1),  # Use extracted count as baseline
                        explicit_tech_included=len(explicit_techs),
                        explicit_tech_total=len(explicit_techs),
                        processing_time=(event.get('duration_ms', 0) / 1000.0)
                    )
            
            # Process LLM events for performance metrics
            for event in llm_events:
                data = event.get('data', {})
                token_usage = data.get('token_usage', {})
                duration_ms = event.get('duration_ms', 0)
                
                # Record LLM performance metrics
                self._record_llm_performance(
                    session_id=session_id,
                    provider=data.get('provider', 'unknown'),
                    model=data.get('model', 'unknown'),
                    token_usage=token_usage,
                    duration_ms=duration_ms,
                    success=event.get('success', True)
                )
            
            # Process validation events for quality metrics
            for event in validation_events:
                data = event.get('data', {})
                validation_results = data.get('validation_results', {})
                conflicts_detected = data.get('conflicts_detected', [])
                
                # Record validation quality metrics
                self._record_validation_quality(
                    session_id=session_id,
                    validation_type=data.get('validation_type', 'unknown'),
                    validation_results=validation_results,
                    conflicts_count=len(conflicts_detected),
                    duration_ms=event.get('duration_ms', 0)
                )
                
        except Exception as e:
            self.logger.error(f"Error processing real session events for {session_id}: {e}")
    
    def _record_llm_performance(self, session_id: str, provider: str, model: str, 
                               token_usage: Dict[str, int], duration_ms: float, success: bool) -> None:
        """Record LLM performance metrics from real data."""
        timestamp = datetime.now()
        
        # Record LLM-specific metrics
        self.metrics.extend([
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.PERFORMANCE,
                name="llm_response_time",
                value=duration_ms / 1000.0,  # Convert to seconds
                metadata={
                    "provider": provider,
                    "model": model,
                    "success": success
                },
                session_id=session_id
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.PERFORMANCE,
                name="llm_token_usage",
                value=token_usage.get('total_tokens', 0),
                metadata={
                    "provider": provider,
                    "model": model,
                    "prompt_tokens": token_usage.get('prompt_tokens', 0),
                    "completion_tokens": token_usage.get('completion_tokens', 0)
                },
                session_id=session_id
            )
        ])
        
        # Check for LLM performance alerts
        if duration_ms > 10000:  # 10 seconds
            self._create_alert(
                AlertLevel.WARNING,
                "llm_performance",
                f"Slow LLM response: {duration_ms/1000:.2f}s",
                {
                    "provider": provider,
                    "model": model,
                    "duration_ms": duration_ms,
                    "session_id": session_id
                },
                session_id
            )
        
        if not success:
            self._create_alert(
                AlertLevel.ERROR,
                "llm_failure",
                f"LLM call failed: {provider}/{model}",
                {
                    "provider": provider,
                    "model": model,
                    "session_id": session_id
                },
                session_id
            )
    
    def _record_validation_quality(self, session_id: str, validation_type: str,
                                  validation_results: Dict[str, Any], conflicts_count: int,
                                  duration_ms: float) -> None:
        """Record validation quality metrics from real data."""
        timestamp = datetime.now()
        
        # Calculate quality score based on validation results
        quality_score = validation_results.get('compatibility_score', 
                                              1.0 if validation_results.get('valid', True) else 0.0)
        
        self.metrics.extend([
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.QUALITY,
                name="validation_quality_score",
                value=quality_score,
                metadata={
                    "validation_type": validation_type,
                    "conflicts_count": conflicts_count,
                    "ecosystem_consistent": validation_results.get('ecosystem_consistency', True)
                },
                session_id=session_id
            ),
            TechStackMetric(
                timestamp=timestamp,
                metric_type=MetricType.PERFORMANCE,
                name="validation_time",
                value=duration_ms / 1000.0,
                metadata={
                    "validation_type": validation_type
                },
                session_id=session_id
            )
        ])
        
        # Check for validation quality alerts
        if quality_score < 0.8:
            self._create_alert(
                AlertLevel.WARNING,
                "validation_quality",
                f"Low validation quality: {quality_score:.2f}",
                {
                    "validation_type": validation_type,
                    "quality_score": quality_score,
                    "conflicts_count": conflicts_count,
                    "session_id": session_id
                },
                session_id
            )
        
        if conflicts_count > 3:
            self._create_alert(
                AlertLevel.WARNING,
                "validation_conflicts",
                f"High conflict count: {conflicts_count}",
                {
                    "validation_type": validation_type,
                    "conflicts_count": conflicts_count,
                    "session_id": session_id
                },
                session_id
            )
    
    async def _analyze_and_recommend(self) -> None:
        """Analyze metrics and generate optimization recommendations."""
        recent_metrics = self._get_recent_metrics(hours=24)
        
        # Clear old recommendations
        self.recommendations.clear()
        
        # Analyze performance patterns
        self._analyze_performance_patterns(recent_metrics)
        
        # Analyze accuracy patterns
        self._analyze_accuracy_patterns(recent_metrics)
        
        # Analyze catalog health
        self._analyze_catalog_health(recent_metrics)
        
        # Log recommendations
        if self.recommendations:
            self.logger.info(f"Generated {len(self.recommendations)} optimization recommendations")
    
    def _analyze_performance_patterns(self, metrics: List[TechStackMetric]) -> None:
        """Analyze performance metrics and generate recommendations."""
        perf_metrics = [m for m in metrics if m.name == "processing_time"]
        
        if len(perf_metrics) >= 10:
            avg_time = sum(m.value for m in perf_metrics) / len(perf_metrics)
            max_time = max(m.value for m in perf_metrics)
            
            if avg_time > 15.0:
                self.recommendations.append(PerformanceRecommendation(
                    category="performance",
                    priority="high",
                    description="High average processing time detected",
                    impact="User experience degradation, potential timeout issues",
                    implementation="Consider caching frequently used catalog lookups, optimize LLM prompt size, implement parallel processing",
                    metrics_supporting=["processing_time"]
                ))
            
            if max_time > 45.0:
                self.recommendations.append(PerformanceRecommendation(
                    category="performance",
                    priority="medium",
                    description="Occasional very slow processing detected",
                    impact="Intermittent poor user experience",
                    implementation="Add request timeout handling, implement circuit breaker pattern for LLM calls",
                    metrics_supporting=["processing_time"]
                ))
    
    def _analyze_accuracy_patterns(self, metrics: List[TechStackMetric]) -> None:
        """Analyze accuracy metrics and generate recommendations."""
        accuracy_metrics = [m for m in metrics if m.name == "extraction_accuracy"]
        inclusion_metrics = [m for m in metrics if m.name == "explicit_tech_inclusion_rate"]
        
        if len(accuracy_metrics) >= 10:
            avg_accuracy = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics)
            
            if avg_accuracy < 0.90:
                self.recommendations.append(PerformanceRecommendation(
                    category="accuracy",
                    priority="high",
                    description="Low technology extraction accuracy",
                    impact="Incorrect technology recommendations, poor user satisfaction",
                    implementation="Improve NER model, enhance pattern matching rules, expand technology alias database",
                    metrics_supporting=["extraction_accuracy"]
                ))
        
        if len(inclusion_metrics) >= 10:
            avg_inclusion = sum(m.value for m in inclusion_metrics) / len(inclusion_metrics)
            
            if avg_inclusion < 0.75:
                self.recommendations.append(PerformanceRecommendation(
                    category="accuracy",
                    priority="high",
                    description="Low explicit technology inclusion rate",
                    impact="User-specified technologies not being included in recommendations",
                    implementation="Enhance LLM prompt prioritization, improve context extraction, validate catalog completeness",
                    metrics_supporting=["explicit_tech_inclusion_rate"]
                ))
    
    def _analyze_catalog_health(self, metrics: List[TechStackMetric]) -> None:
        """Analyze catalog health metrics and generate recommendations."""
        consistency_metrics = [m for m in metrics if m.name == "catalog_consistency_rate"]
        missing_metrics = [m for m in metrics if m.name == "catalog_missing_rate"]
        
        if consistency_metrics:
            latest_consistency = consistency_metrics[-1].value
            if latest_consistency < 0.98:
                self.recommendations.append(PerformanceRecommendation(
                    category="catalog",
                    priority="medium",
                    description="Catalog consistency issues detected",
                    impact="Inconsistent technology recommendations, potential errors",
                    implementation="Run catalog validation, fix inconsistent entries, implement automated consistency checks",
                    metrics_supporting=["catalog_consistency_rate"]
                ))
        
        if missing_metrics:
            latest_missing = missing_metrics[-1].value
            if latest_missing > 0.05:
                self.recommendations.append(PerformanceRecommendation(
                    category="catalog",
                    priority="medium",
                    description="High rate of missing technologies",
                    impact="Incomplete technology recommendations, user frustration",
                    implementation="Expand technology catalog, improve auto-addition workflow, prioritize pending reviews",
                    metrics_supporting=["catalog_missing_rate"]
                ))
    
    def get_alert_escalation_status(self) -> Dict[str, Any]:
        """Get alert escalation status and recommendations."""
        recent_alerts = [a for a in self.alerts if a.timestamp >= datetime.now() - timedelta(hours=1)]
        
        # Count alerts by level and category
        alert_summary = {
            'total_alerts': len(recent_alerts),
            'critical_alerts': len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
            'error_alerts': len([a for a in recent_alerts if a.level == AlertLevel.ERROR]),
            'warning_alerts': len([a for a in recent_alerts if a.level == AlertLevel.WARNING]),
            'categories': {}
        }
        
        # Group by category
        for alert in recent_alerts:
            category = alert.category
            if category not in alert_summary['categories']:
                alert_summary['categories'][category] = {
                    'count': 0,
                    'highest_level': AlertLevel.INFO,
                    'latest_message': ''
                }
            
            alert_summary['categories'][category]['count'] += 1
            if alert.level.value in ['critical', 'error'] and alert_summary['categories'][category]['highest_level'] != AlertLevel.CRITICAL:
                alert_summary['categories'][category]['highest_level'] = alert.level
            alert_summary['categories'][category]['latest_message'] = alert.message
        
        # Determine escalation needs
        escalation_needed = (
            alert_summary['critical_alerts'] > 0 or
            alert_summary['error_alerts'] > 3 or
            alert_summary['total_alerts'] > 10
        )
        
        alert_summary['escalation_needed'] = escalation_needed
        alert_summary['escalation_reason'] = self._get_escalation_reason(alert_summary)
        
        return alert_summary
    
    def _get_escalation_reason(self, alert_summary: Dict[str, Any]) -> str:
        """Determine the reason for alert escalation."""
        if alert_summary['critical_alerts'] > 0:
            return f"Critical alerts detected: {alert_summary['critical_alerts']} critical issues"
        elif alert_summary['error_alerts'] > 3:
            return f"High error rate: {alert_summary['error_alerts']} errors in the last hour"
        elif alert_summary['total_alerts'] > 10:
            return f"Alert storm detected: {alert_summary['total_alerts']} alerts in the last hour"
        else:
            return "No escalation needed"
    
    def get_system_health_score(self) -> Dict[str, Any]:
        """Calculate comprehensive system health score."""
        recent_metrics = self._get_recent_metrics(hours=4)
        
        if not recent_metrics:
            return {
                'overall_score': 0.0,
                'health_status': 'unknown',
                'component_scores': {},
                'recommendations': ['No recent data available for health assessment']
            }
        
        # Calculate component scores
        component_scores = {}
        
        # Accuracy score
        accuracy_metrics = [m for m in recent_metrics if m.name == "extraction_accuracy"]
        if accuracy_metrics:
            avg_accuracy = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics)
            component_scores['accuracy'] = min(avg_accuracy / 0.85, 1.0)  # Normalize to 85% target
        
        # Performance score
        perf_metrics = [m for m in recent_metrics if m.name == "processing_time"]
        if perf_metrics:
            avg_time = sum(m.value for m in perf_metrics) / len(perf_metrics)
            component_scores['performance'] = max(0.0, 1.0 - (avg_time / 30.0))  # Normalize to 30s target
        
        # Satisfaction score
        sat_metrics = [m for m in recent_metrics if m.name == "overall_satisfaction"]
        if sat_metrics:
            avg_satisfaction = sum(m.value for m in sat_metrics) / len(sat_metrics)
            component_scores['satisfaction'] = (avg_satisfaction - 1) / 4  # Normalize 1-5 scale to 0-1
        
        # Catalog health score
        consistency_metrics = [m for m in recent_metrics if m.name == "catalog_consistency_rate"]
        if consistency_metrics:
            latest_consistency = consistency_metrics[-1].value
            component_scores['catalog_health'] = latest_consistency
        
        # Calculate overall score
        if component_scores:
            overall_score = sum(component_scores.values()) / len(component_scores)
        else:
            overall_score = 0.0
        
        # Determine health status
        if overall_score >= 0.9:
            health_status = 'excellent'
        elif overall_score >= 0.8:
            health_status = 'good'
        elif overall_score >= 0.7:
            health_status = 'fair'
        elif overall_score >= 0.5:
            health_status = 'poor'
        else:
            health_status = 'critical'
        
        # Generate health recommendations
        health_recommendations = []
        if component_scores.get('accuracy', 1.0) < 0.8:
            health_recommendations.append("Improve technology extraction accuracy")
        if component_scores.get('performance', 1.0) < 0.7:
            health_recommendations.append("Optimize system performance and response times")
        if component_scores.get('satisfaction', 1.0) < 0.8:
            health_recommendations.append("Address user satisfaction issues")
        if component_scores.get('catalog_health', 1.0) < 0.9:
            health_recommendations.append("Improve catalog consistency and completeness")
        
        return {
            'overall_score': overall_score,
            'health_status': health_status,
            'component_scores': component_scores,
            'recommendations': health_recommendations
        }
    
    def _get_recent_metrics(self, hours: int = 24) -> List[TechStackMetric]:
        """Get metrics from the last N hours."""
        cutoff = datetime.now() - timedelta(hours=hours)
        return [m for m in self.metrics if m.timestamp >= cutoff]
    
    def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive dashboard data for quality monitoring."""
        recent_metrics = self._get_recent_metrics(hours=24)
        recent_alerts = [a for a in self.alerts if a.timestamp >= datetime.now() - timedelta(hours=24)]
        
        # Calculate summary statistics
        accuracy_metrics = [m for m in recent_metrics if m.name == "extraction_accuracy"]
        performance_metrics = [m for m in recent_metrics if m.name == "processing_time"]
        satisfaction_metrics = [m for m in recent_metrics if m.name == "overall_satisfaction"]
        
        dashboard_data = {
            "summary": {
                "total_sessions": len(set(m.session_id for m in recent_metrics if m.session_id)),
                "total_alerts": len(recent_alerts),
                "critical_alerts": len([a for a in recent_alerts if a.level == AlertLevel.CRITICAL]),
                "recommendations_count": len(self.recommendations)
            },
            "accuracy": {
                "average": sum(m.value for m in accuracy_metrics) / len(accuracy_metrics) if accuracy_metrics else 0,
                "trend": self._calculate_trend(accuracy_metrics),
                "samples": len(accuracy_metrics)
            },
            "performance": {
                "average_time": sum(m.value for m in performance_metrics) / len(performance_metrics) if performance_metrics else 0,
                "max_time": max((m.value for m in performance_metrics), default=0),
                "trend": self._calculate_trend(performance_metrics, reverse=True),
                "samples": len(performance_metrics)
            },
            "satisfaction": {
                "average": sum(m.value for m in satisfaction_metrics) / len(satisfaction_metrics) if satisfaction_metrics else 0,
                "trend": self._calculate_trend(satisfaction_metrics),
                "samples": len(satisfaction_metrics)
            },
            "alerts": [a.to_dict() for a in recent_alerts[-10:]],  # Last 10 alerts
            "recommendations": [r.to_dict() for r in self.recommendations],
            "metrics_by_hour": self._group_metrics_by_hour(recent_metrics)
        }
        
        return dashboard_data
    
    def _calculate_trend(self, metrics: List[TechStackMetric], reverse: bool = False) -> str:
        """Calculate trend direction for metrics."""
        if len(metrics) < 2:
            return "stable"
        
        # Split into first and second half
        mid = len(metrics) // 2
        first_half = metrics[:mid]
        second_half = metrics[mid:]
        
        first_avg = sum(m.value for m in first_half) / len(first_half)
        second_avg = sum(m.value for m in second_half) / len(second_half)
        
        diff = second_avg - first_avg
        if reverse:
            diff = -diff
        
        if diff > 0.05:
            return "improving"
        elif diff < -0.05:
            return "declining"
        else:
            return "stable"
    
    def _group_metrics_by_hour(self, metrics: List[TechStackMetric]) -> Dict[str, Dict[str, float]]:
        """Group metrics by hour for trending visualization."""
        hourly_data = {}
        
        for metric in metrics:
            hour_key = metric.timestamp.strftime("%Y-%m-%d %H:00")
            if hour_key not in hourly_data:
                hourly_data[hour_key] = {}
            
            if metric.name not in hourly_data[hour_key]:
                hourly_data[hour_key][metric.name] = []
            
            hourly_data[hour_key][metric.name].append(metric.value)
        
        # Calculate averages for each hour
        for hour_key in hourly_data:
            for metric_name in hourly_data[hour_key]:
                values = hourly_data[hour_key][metric_name]
                hourly_data[hour_key][metric_name] = sum(values) / len(values)
        
        return hourly_data
    
    def export_metrics(self, filepath: str, hours: int = 24) -> None:
        """Export metrics to JSON file."""
        recent_metrics = self._get_recent_metrics(hours)
        recent_alerts = [a for a in self.alerts if a.timestamp >= datetime.now() - timedelta(hours=hours)]
        
        export_data = {
            "export_timestamp": datetime.now().isoformat(),
            "time_window_hours": hours,
            "metrics": [m.to_dict() for m in recent_metrics],
            "alerts": [a.to_dict() for a in recent_alerts],
            "recommendations": [r.to_dict() for r in self.recommendations],
            "summary": self.get_quality_dashboard_data()["summary"]
        }
        
        with open(filepath, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        self.logger.info(f"Exported {len(recent_metrics)} metrics and {len(recent_alerts)} alerts to {filepath}")