"""
Real-Time Quality Monitoring and Validation System

Provides live quality assessment during tech stack generation with real-time alerts,
ecosystem consistency checking, user satisfaction prediction, and quality trend analysis.
"""

import asyncio
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import statistics

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


class QualityMetricType(Enum):
    """Types of quality metrics tracked in real-time."""

    EXTRACTION_ACCURACY = "extraction_accuracy"
    ECOSYSTEM_CONSISTENCY = "ecosystem_consistency"
    TECHNOLOGY_INCLUSION = "technology_inclusion"
    CATALOG_COMPLETENESS = "catalog_completeness"
    USER_SATISFACTION = "user_satisfaction"
    RESPONSE_QUALITY = "response_quality"


class QualityAlertSeverity(Enum):
    """Quality alert severity levels."""

    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


@dataclass
class QualityScore:
    """Quality assessment score with detailed breakdown."""

    overall_score: float  # 0.0 to 1.0
    metric_type: QualityMetricType
    component_scores: Dict[str, float]
    confidence: float
    timestamp: datetime
    session_id: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class ConsistencyScore:
    """Ecosystem consistency assessment score."""

    consistency_score: float  # 0.0 to 1.0
    ecosystem_detected: Optional[str]  # aws, azure, gcp, mixed, unknown
    inconsistencies: List[Dict[str, Any]]
    recommendations: List[str]
    confidence: float
    timestamp: datetime
    session_id: Optional[str] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        return data


@dataclass
class QualityAlert:
    """Real-time quality alert."""

    alert_id: str
    timestamp: datetime
    severity: QualityAlertSeverity
    metric_type: QualityMetricType
    message: str
    current_value: float
    threshold_value: float
    session_id: Optional[str]
    details: Dict[str, Any]
    resolved: bool = False
    resolution_time: Optional[datetime] = None

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["timestamp"] = self.timestamp.isoformat()
        data["severity"] = self.severity.value
        data["metric_type"] = self.metric_type.value
        if self.resolution_time:
            data["resolution_time"] = self.resolution_time.isoformat()
        return data


@dataclass
class QualityTrend:
    """Quality trend analysis data."""

    metric_type: QualityMetricType
    time_window_hours: int
    trend_direction: str  # improving, declining, stable
    trend_strength: float  # 0.0 to 1.0
    current_average: float
    previous_average: float
    change_rate: float
    data_points: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data["metric_type"] = self.metric_type.value
        data["timestamp"] = self.timestamp.isoformat()
        return data


class RealTimeQualityMonitor(ConfigurableService):
    """
    Real-time quality monitoring and validation system for tech stack generation.

    Provides live quality assessment, ecosystem consistency checking, user satisfaction
    prediction, quality threshold monitoring with automatic alerting, and quality trend
    analysis with degradation detection.
    """

    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, "RealTimeQualityMonitor")

        # Initialize logger
        try:
            self.logger = require_service("logger", context="RealTimeQualityMonitor")
        except Exception:
            import logging

            self.logger = logging.getLogger("RealTimeQualityMonitor")

        # Quality monitoring state
        self.quality_scores: List[QualityScore] = []
        self.consistency_scores: List[ConsistencyScore] = []
        self.quality_alerts: List[QualityAlert] = []
        self.quality_trends: Dict[QualityMetricType, QualityTrend] = {}

        # Configuration
        self.config = (
            {
                "monitoring_enabled": True,
                "alert_thresholds": {
                    QualityMetricType.EXTRACTION_ACCURACY: 0.85,
                    QualityMetricType.ECOSYSTEM_CONSISTENCY: 0.90,
                    QualityMetricType.TECHNOLOGY_INCLUSION: 0.70,
                    QualityMetricType.CATALOG_COMPLETENESS: 0.80,
                    QualityMetricType.USER_SATISFACTION: 0.75,
                    QualityMetricType.RESPONSE_QUALITY: 0.80,
                },
                "trend_analysis_window_hours": 24,
                "real_time_update_interval": 30,  # seconds
                "max_stored_scores": 1000,
                "max_stored_alerts": 500,
                "degradation_threshold": 0.1,  # 10% degradation triggers alert
                **config,
            }
            if config
            else {
                "monitoring_enabled": True,
                "alert_thresholds": {
                    QualityMetricType.EXTRACTION_ACCURACY: 0.85,
                    QualityMetricType.ECOSYSTEM_CONSISTENCY: 0.90,
                    QualityMetricType.TECHNOLOGY_INCLUSION: 0.70,
                    QualityMetricType.CATALOG_COMPLETENESS: 0.80,
                    QualityMetricType.USER_SATISFACTION: 0.75,
                    QualityMetricType.RESPONSE_QUALITY: 0.80,
                },
                "trend_analysis_window_hours": 24,
                "real_time_update_interval": 30,
                "max_stored_scores": 1000,
                "max_stored_alerts": 500,
                "degradation_threshold": 0.1,
            }
        )

        # Service dependencies
        self.tech_stack_monitor = None
        self.monitoring_integration = None
        self.catalog_manager = None

        # Monitoring state
        self.is_monitoring = False
        self.monitoring_task = None
        self.trend_analysis_task = None

        # Ecosystem detection patterns
        self.ecosystem_patterns = {
            "aws": [
                "aws",
                "amazon",
                "bedrock",
                "lambda",
                "s3",
                "ec2",
                "rds",
                "dynamodb",
                "cloudformation",
            ],
            "azure": [
                "azure",
                "microsoft",
                "cosmos",
                "functions",
                "storage",
                "sql",
                "resource",
            ],
            "gcp": [
                "google",
                "gcp",
                "cloud storage",
                "firestore",
                "functions",
                "storage",
                "sql",
                "deployment",
            ],
            "open_source": [
                "docker",
                "kubernetes",
                "postgresql",
                "redis",
                "nginx",
                "apache",
                "postgres",
            ],
        }

    async def _do_initialize(self) -> None:
        """Initialize the real-time quality monitor."""
        await self.start_real_time_monitoring()

    async def _do_shutdown(self) -> None:
        """Shutdown the real-time quality monitor."""
        await self.stop_real_time_monitoring()

    async def start_real_time_monitoring(self) -> None:
        """Start real-time quality monitoring."""
        if not self.config["monitoring_enabled"]:
            self.logger.info("Real-time quality monitoring is disabled")
            return

        try:
            self.logger.info("Starting real-time quality monitoring")

            # Initialize service dependencies
            await self._initialize_dependencies()

            # Start monitoring tasks
            self.is_monitoring = True
            self.monitoring_task = asyncio.create_task(
                self._real_time_monitoring_loop()
            )
            self.trend_analysis_task = asyncio.create_task(self._trend_analysis_loop())

            self.logger.info("Real-time quality monitoring started successfully")

        except Exception as e:
            self.logger.error(f"Failed to start real-time quality monitoring: {e}")
            raise

    async def stop_real_time_monitoring(self) -> None:
        """Stop real-time quality monitoring."""
        try:
            self.logger.info("Stopping real-time quality monitoring")

            self.is_monitoring = False

            # Cancel monitoring tasks
            if self.monitoring_task:
                self.monitoring_task.cancel()
                try:
                    await self.monitoring_task
                except asyncio.CancelledError:
                    pass

            if self.trend_analysis_task:
                self.trend_analysis_task.cancel()
                try:
                    await self.trend_analysis_task
                except asyncio.CancelledError:
                    pass

            self.logger.info("Real-time quality monitoring stopped")

        except Exception as e:
            self.logger.error(f"Error stopping real-time quality monitoring: {e}")

    async def _initialize_dependencies(self) -> None:
        """Initialize service dependencies."""
        try:
            # Get services from registry
            self.tech_stack_monitor = optional_service(
                "tech_stack_monitor", context="RealTimeQualityMonitor"
            )
            self.monitoring_integration = optional_service(
                "tech_stack_monitoring_integration", context="RealTimeQualityMonitor"
            )
            self.catalog_manager = optional_service(
                "intelligent_catalog_manager", context="RealTimeQualityMonitor"
            )

            # Try direct imports if services not available
            if not self.tech_stack_monitor:
                try:
                    from app.monitoring.tech_stack_monitor import TechStackMonitor

                    self.tech_stack_monitor = TechStackMonitor()
                except ImportError:
                    self.logger.warning("TechStackMonitor not available")

            if not self.monitoring_integration:
                try:
                    from app.services.monitoring_integration_service import (
                        TechStackMonitoringIntegrationService,
                    )

                    self.monitoring_integration = (
                        TechStackMonitoringIntegrationService()
                    )
                except ImportError:
                    self.logger.warning("MonitoringIntegrationService not available")

            self.logger.info(
                f"Initialized dependencies: "
                f"monitor={bool(self.tech_stack_monitor)}, "
                f"integration={bool(self.monitoring_integration)}, "
                f"catalog={bool(self.catalog_manager)}"
            )

        except Exception as e:
            self.logger.error(f"Error initializing dependencies: {e}")

    async def validate_extraction_quality(
        self,
        extracted_techs: List[str],
        requirements: str,
        session_id: Optional[str] = None,
    ) -> QualityScore:
        """
        Validate technology extraction quality in real-time.

        Args:
            extracted_techs: List of extracted technology names
            requirements: Original requirements text
            session_id: Optional session identifier

        Returns:
            QualityScore with detailed assessment
        """
        try:
            timestamp = datetime.now()

            # Component quality assessments
            component_scores = {}

            # 1. Extraction completeness (are key technologies mentioned in requirements extracted?)
            completeness_score = await self._assess_extraction_completeness(
                extracted_techs, requirements
            )
            component_scores["completeness"] = completeness_score

            # 2. Extraction accuracy (are extracted technologies actually mentioned?)
            accuracy_score = await self._assess_extraction_accuracy(
                extracted_techs, requirements
            )
            component_scores["accuracy"] = accuracy_score

            # 3. Technology relevance (are extracted technologies relevant to requirements?)
            relevance_score = await self._assess_technology_relevance(
                extracted_techs, requirements
            )
            component_scores["relevance"] = relevance_score

            # 4. Catalog coverage (are extracted technologies in catalog?)
            coverage_score = await self._assess_catalog_coverage(extracted_techs)
            component_scores["catalog_coverage"] = coverage_score

            # Calculate overall score (weighted average)
            overall_score = (
                completeness_score * 0.3
                + accuracy_score * 0.3
                + relevance_score * 0.25
                + coverage_score * 0.15
            )

            # Calculate confidence based on data quality
            confidence = self._calculate_confidence(
                extracted_techs, requirements, component_scores
            )

            # Create quality score
            quality_score = QualityScore(
                overall_score=overall_score,
                metric_type=QualityMetricType.EXTRACTION_ACCURACY,
                component_scores=component_scores,
                confidence=confidence,
                timestamp=timestamp,
                session_id=session_id,
                details={
                    "extracted_count": len(extracted_techs),
                    "requirements_length": len(requirements),
                    "extracted_technologies": extracted_techs,
                },
            )

            # Store score and check for alerts
            await self._store_quality_score(quality_score)
            await self._check_quality_alerts(quality_score)

            return quality_score

        except Exception as e:
            self.logger.error(f"Error validating extraction quality: {e}")
            # Return default score on error
            return QualityScore(
                overall_score=0.0,
                metric_type=QualityMetricType.EXTRACTION_ACCURACY,
                component_scores={"error": 0.0},
                confidence=0.0,
                timestamp=datetime.now(),
                session_id=session_id,
                details={"error": str(e)},
            )

    async def check_ecosystem_consistency(
        self, tech_stack: List[str], session_id: Optional[str] = None
    ) -> ConsistencyScore:
        """
        Check ecosystem consistency in real-time with alerts.

        Args:
            tech_stack: List of technologies in the stack
            session_id: Optional session identifier

        Returns:
            ConsistencyScore with detailed assessment
        """
        try:
            timestamp = datetime.now()

            # Detect ecosystems present in the tech stack
            ecosystem_scores = self._detect_ecosystems(tech_stack)

            # Determine primary ecosystem
            primary_ecosystem = (
                max(ecosystem_scores.items(), key=lambda x: x[1])[0]
                if ecosystem_scores
                else "unknown"
            )

            # Calculate consistency score
            consistency_score = await self._calculate_ecosystem_consistency(
                tech_stack, ecosystem_scores
            )

            # Identify inconsistencies
            inconsistencies = self._identify_ecosystem_inconsistencies(
                tech_stack, ecosystem_scores, primary_ecosystem
            )

            # Generate recommendations
            recommendations = self._generate_ecosystem_recommendations(
                inconsistencies, primary_ecosystem
            )

            # Calculate confidence
            confidence = self._calculate_ecosystem_confidence(
                tech_stack, ecosystem_scores
            )

            # Create consistency score
            consistency_result = ConsistencyScore(
                consistency_score=consistency_score,
                ecosystem_detected=primary_ecosystem,
                inconsistencies=inconsistencies,
                recommendations=recommendations,
                confidence=confidence,
                timestamp=timestamp,
                session_id=session_id,
            )

            # Store score and check for alerts
            await self._store_consistency_score(consistency_result)
            await self._check_consistency_alerts(consistency_result)

            return consistency_result

        except Exception as e:
            self.logger.error(f"Error checking ecosystem consistency: {e}")
            return ConsistencyScore(
                consistency_score=0.0,
                ecosystem_detected="unknown",
                inconsistencies=[{"error": str(e)}],
                recommendations=["Investigate consistency check failure"],
                confidence=0.0,
                timestamp=datetime.now(),
                session_id=session_id,
            )

    async def calculate_user_satisfaction_score(
        self,
        result: Dict[str, Any],
        feedback: Optional[Dict[str, Any]] = None,
        session_id: Optional[str] = None,
    ) -> float:
        """
        Calculate predicted user satisfaction score based on generation results.

        Args:
            result: Tech stack generation result
            feedback: Optional user feedback
            session_id: Optional session identifier

        Returns:
            Predicted user satisfaction score (0.0 to 1.0)
        """
        try:
            # Extract relevant metrics from result
            tech_stack = result.get("tech_stack", [])
            generation_metrics = result.get("generation_metrics", {})
            processing_time = result.get("processing_time", 0)

            # Component satisfaction scores
            component_scores = {}

            # 1. Technology relevance satisfaction
            relevance_satisfaction = await self._predict_relevance_satisfaction(
                tech_stack, generation_metrics
            )
            component_scores["relevance"] = relevance_satisfaction

            # 2. Completeness satisfaction
            completeness_satisfaction = await self._predict_completeness_satisfaction(
                tech_stack, generation_metrics
            )
            component_scores["completeness"] = completeness_satisfaction

            # 3. Performance satisfaction (response time)
            performance_satisfaction = self._predict_performance_satisfaction(
                processing_time
            )
            component_scores["performance"] = performance_satisfaction

            # 4. Quality satisfaction (overall generation quality)
            quality_satisfaction = await self._predict_quality_satisfaction(result)
            component_scores["quality"] = quality_satisfaction

            # 5. Incorporate actual feedback if available
            feedback_satisfaction = (
                self._incorporate_feedback(feedback) if feedback else 0.75
            )  # Default neutral
            component_scores["feedback"] = feedback_satisfaction

            # Calculate overall satisfaction (weighted average)
            overall_satisfaction = (
                relevance_satisfaction * 0.25
                + completeness_satisfaction * 0.20
                + performance_satisfaction * 0.15
                + quality_satisfaction * 0.20
                + feedback_satisfaction * 0.20
            )

            # Create and store satisfaction score
            satisfaction_score = QualityScore(
                overall_score=overall_satisfaction,
                metric_type=QualityMetricType.USER_SATISFACTION,
                component_scores=component_scores,
                confidence=0.8,  # Prediction confidence
                timestamp=datetime.now(),
                session_id=session_id,
                details={
                    "tech_stack_size": len(tech_stack),
                    "processing_time": processing_time,
                    "has_feedback": bool(feedback),
                    "generation_metrics": generation_metrics,
                },
            )

            await self._store_quality_score(satisfaction_score)
            await self._check_quality_alerts(satisfaction_score)

            return overall_satisfaction

        except Exception as e:
            self.logger.error(f"Error calculating user satisfaction score: {e}")
            return 0.5  # Default neutral satisfaction on error

    async def _real_time_monitoring_loop(self) -> None:
        """Main real-time monitoring loop."""
        while self.is_monitoring:
            try:
                # Get real-time data from monitoring integration service
                if self.monitoring_integration:
                    await self._process_real_time_data()

                # Check for quality degradation
                await self._check_quality_degradation()

                # Update quality thresholds based on recent performance
                await self._update_dynamic_thresholds()

                # Clean up old data
                await self._cleanup_old_data()

                # Wait for next monitoring cycle
                await asyncio.sleep(self.config["real_time_update_interval"])

            except Exception as e:
                self.logger.error(f"Error in real-time monitoring loop: {e}")
                await asyncio.sleep(60)  # Wait longer on error

    async def _trend_analysis_loop(self) -> None:
        """Quality trend analysis loop."""
        while self.is_monitoring:
            try:
                # Analyze trends for each quality metric type
                for metric_type in QualityMetricType:
                    trend = await self._analyze_quality_trend(metric_type)
                    if trend:
                        self.quality_trends[metric_type] = trend

                        # Check for significant degradation
                        if (
                            trend.trend_direction == "declining"
                            and trend.trend_strength > 0.7
                            and abs(trend.change_rate)
                            > self.config["degradation_threshold"]
                        ):

                            await self._create_degradation_alert(trend)

                # Wait for next trend analysis cycle (every hour)
                await asyncio.sleep(3600)

            except Exception as e:
                self.logger.error(f"Error in trend analysis loop: {e}")
                await asyncio.sleep(1800)  # Wait 30 minutes on error

    async def _process_real_time_data(self) -> None:
        """Process real-time data from monitoring integration service."""
        try:
            # Get active sessions
            active_sessions = self.monitoring_integration.get_active_sessions()

            for session_info in active_sessions:
                session_id = session_info["session_id"]
                session_events = self.monitoring_integration.get_session_events(
                    session_id
                )

                # Process extraction events for quality assessment
                extraction_events = [
                    e
                    for e in session_events
                    if e.get("event_type") == "extraction_complete"
                ]

                for event in extraction_events:
                    data = event.get("data", {})
                    extracted_techs = data.get("extracted_technologies", [])

                    if extracted_techs:
                        # Validate extraction quality in real-time
                        requirements = session_info.get("requirements", {}).get(
                            "text", ""
                        )
                        await self.validate_extraction_quality(
                            extracted_techs, requirements, session_id
                        )

                # Process completion events for satisfaction prediction
                completion_events = [
                    e
                    for e in session_events
                    if e.get("event_type") == "session_complete"
                ]

                for event in completion_events:
                    data = event.get("data", {})
                    final_tech_stack = data.get("final_tech_stack", [])
                    generation_metrics = data.get("generation_metrics", {})

                    if final_tech_stack:
                        # Check ecosystem consistency
                        await self.check_ecosystem_consistency(
                            final_tech_stack, session_id
                        )

                        # Predict user satisfaction
                        result = {
                            "tech_stack": final_tech_stack,
                            "generation_metrics": generation_metrics,
                            "processing_time": data.get("total_duration_ms", 0)
                            / 1000.0,
                        }
                        await self.calculate_user_satisfaction_score(
                            result, session_id=session_id
                        )

        except Exception as e:
            self.logger.error(f"Error processing real-time data: {e}")

    # Quality assessment helper methods
    async def _assess_extraction_completeness(
        self, extracted_techs: List[str], requirements: str
    ) -> float:
        """Assess how complete the technology extraction is."""
        try:
            # Simple heuristic: look for technology-related keywords in requirements
            tech_keywords = [
                "api",
                "database",
                "cloud",
                "service",
                "framework",
                "library",
                "tool",
                "platform",
                "web",
                "application",
            ]

            # Count technology mentions in requirements (case-insensitive)
            requirements_lower = requirements.lower()
            mentioned_keywords = sum(
                1 for keyword in tech_keywords if keyword in requirements_lower
            )

            # Count extracted technologies
            extracted_count = len(extracted_techs)

            # Calculate completeness (with reasonable bounds)
            if mentioned_keywords == 0:
                return (
                    0.5 if extracted_count == 0 else 0.8
                )  # No tech keywords, so some extraction expected

            # If no technologies extracted but keywords present, low completeness
            if extracted_count == 0 and mentioned_keywords > 0:
                return 0.2

            completeness = min(1.0, extracted_count / max(mentioned_keywords, 1))
            return max(0.0, completeness)

        except Exception as e:
            self.logger.error(f"Error assessing extraction completeness: {e}")
            return 0.5

    async def _assess_extraction_accuracy(
        self, extracted_techs: List[str], requirements: str
    ) -> float:
        """Assess how accurate the technology extraction is."""
        try:
            if not extracted_techs:
                return 1.0  # No false positives if nothing extracted

            requirements_lower = requirements.lower()
            accurate_extractions = 0

            for tech in extracted_techs:
                tech_lower = tech.lower()
                # Check if technology name or parts of it appear in requirements
                tech_words = tech_lower.split()

                # Consider extraction accurate if any significant word from tech name appears
                if any(
                    word in requirements_lower for word in tech_words if len(word) > 2
                ):
                    accurate_extractions += 1

            accuracy = accurate_extractions / len(extracted_techs)
            return max(0.0, min(1.0, accuracy))

        except Exception as e:
            self.logger.error(f"Error assessing extraction accuracy: {e}")
            return 0.5

    async def _assess_technology_relevance(
        self, extracted_techs: List[str], requirements: str
    ) -> float:
        """Assess how relevant extracted technologies are to requirements."""
        try:
            if not extracted_techs:
                return 1.0

            # Simple relevance scoring based on context clues
            requirements_lower = requirements.lower()

            # Context indicators
            web_indicators = ["web", "api", "http", "rest", "frontend", "backend"]
            data_indicators = ["data", "database", "storage", "analytics", "sql"]
            cloud_indicators = ["cloud", "aws", "azure", "gcp", "serverless"]
            ai_indicators = ["ai", "ml", "machine learning", "nlp", "model"]

            # Detect context
            contexts = {
                "web": any(
                    indicator in requirements_lower for indicator in web_indicators
                ),
                "data": any(
                    indicator in requirements_lower for indicator in data_indicators
                ),
                "cloud": any(
                    indicator in requirements_lower for indicator in cloud_indicators
                ),
                "ai": any(
                    indicator in requirements_lower for indicator in ai_indicators
                ),
            }

            relevant_count = 0
            for tech in extracted_techs:
                tech_lower = tech.lower()

                # Check relevance based on detected contexts
                is_relevant = False

                if contexts["web"] and any(
                    web_tech in tech_lower
                    for web_tech in ["fastapi", "react", "node", "express", "django"]
                ):
                    is_relevant = True
                elif contexts["data"] and any(
                    data_tech in tech_lower
                    for data_tech in ["sql", "postgres", "mongo", "redis"]
                ):
                    is_relevant = True
                elif contexts["cloud"] and any(
                    cloud_tech in tech_lower
                    for cloud_tech in ["aws", "azure", "gcp", "lambda"]
                ):
                    is_relevant = True
                elif contexts["ai"] and any(
                    ai_tech in tech_lower
                    for ai_tech in ["openai", "tensorflow", "pytorch", "hugging"]
                ):
                    is_relevant = True
                else:
                    # Default relevance for common technologies
                    is_relevant = True

                if is_relevant:
                    relevant_count += 1

            relevance = relevant_count / len(extracted_techs)
            return max(0.0, min(1.0, relevance))

        except Exception as e:
            self.logger.error(f"Error assessing technology relevance: {e}")
            return 0.7  # Default reasonable relevance

    async def _assess_catalog_coverage(self, extracted_techs: List[str]) -> float:
        """Assess how well extracted technologies are covered in catalog."""
        try:
            if not extracted_techs:
                return 1.0

            if not self.catalog_manager:
                return 0.8  # Default reasonable coverage if catalog not available

            covered_count = 0
            for tech in extracted_techs:
                # Check if technology exists in catalog
                catalog_entry = await self.catalog_manager.lookup_technology(tech)
                if catalog_entry:
                    covered_count += 1

            coverage = covered_count / len(extracted_techs)
            return max(0.0, min(1.0, coverage))

        except Exception as e:
            self.logger.error(f"Error assessing catalog coverage: {e}")
            return 0.8

    def _calculate_confidence(
        self,
        extracted_techs: List[str],
        requirements: str,
        component_scores: Dict[str, float],
    ) -> float:
        """Calculate confidence in quality assessment."""
        try:
            # Base confidence on data quality indicators
            confidence_factors = []

            # Requirements length factor (longer requirements = higher confidence)
            req_length_factor = min(
                1.0, len(requirements) / 200
            )  # Normalize to 200 chars
            confidence_factors.append(req_length_factor)

            # Extraction count factor (reasonable number of techs = higher confidence)
            extraction_count = len(extracted_techs)
            if extraction_count == 0:
                extraction_count_factor = 0.3  # Low confidence for no extraction
            elif extraction_count <= 5:
                extraction_count_factor = min(
                    1.0, extraction_count / 3
                )  # Normalize to 3 techs
            else:
                extraction_count_factor = max(
                    0.7, 1.0 - (extraction_count - 5) * 0.1
                )  # Penalize too many
            confidence_factors.append(extraction_count_factor)

            # Component score consistency factor
            if component_scores:
                scores = list(component_scores.values())
                avg_score = sum(scores) / len(scores)

                # Higher average scores = higher confidence
                score_factor = avg_score
                confidence_factors.append(score_factor)

                # Lower variance = higher confidence
                if len(scores) > 1:
                    score_std = statistics.stdev(scores)
                    consistency_factor = max(0.0, 1.0 - score_std)
                    confidence_factors.append(consistency_factor)

            # Calculate overall confidence
            confidence = (
                sum(confidence_factors) / len(confidence_factors)
                if confidence_factors
                else 0.5
            )
            return max(0.1, min(1.0, confidence))

        except Exception as e:
            self.logger.error(f"Error calculating confidence: {e}")
            return 0.5

    def _detect_ecosystems(self, tech_stack: List[str]) -> Dict[str, float]:
        """Detect ecosystems present in tech stack."""
        ecosystem_scores = {
            ecosystem: 0.0 for ecosystem in self.ecosystem_patterns.keys()
        }

        for tech in tech_stack:
            tech_lower = tech.lower()

            # Check each ecosystem for matches (allow multiple matches for mixed stacks)
            for ecosystem, patterns in self.ecosystem_patterns.items():
                for pattern in patterns:
                    if pattern in tech_lower:
                        ecosystem_scores[ecosystem] += 1.0
                        break  # Count each tech only once per ecosystem

        # Normalize scores
        total_techs = len(tech_stack)
        if total_techs > 0:
            for ecosystem in ecosystem_scores:
                ecosystem_scores[ecosystem] /= total_techs

        return ecosystem_scores

    async def _calculate_ecosystem_consistency(
        self, tech_stack: List[str], ecosystem_scores: Dict[str, float]
    ) -> float:
        """Calculate ecosystem consistency score."""
        try:
            if not ecosystem_scores or not tech_stack:
                return 1.0

            # Find dominant ecosystem
            max_score = max(ecosystem_scores.values())

            if max_score == 0:
                return 1.0  # No specific ecosystem detected, so consistent by default

            # Calculate consistency based on how many technologies belong to the dominant ecosystem
            # If all technologies belong to one ecosystem, consistency = 1.0
            # If technologies are spread across ecosystems, consistency decreases

            # Count non-zero ecosystem scores (ecosystems with technologies)
            active_ecosystems = [
                score for score in ecosystem_scores.values() if score > 0
            ]

            if len(active_ecosystems) == 1:
                # All technologies belong to one ecosystem
                return 1.0
            elif len(active_ecosystems) == 0:
                # No ecosystem detected
                return 1.0
            else:
                # Multiple ecosystems detected - calculate consistency as dominance
                total_ecosystem_presence = sum(ecosystem_scores.values())
                consistency = max_score / total_ecosystem_presence

                # Boost consistency if the dominant ecosystem has most technologies
                if max_score >= 0.6:  # 60% or more in one ecosystem
                    consistency = min(1.0, consistency * 1.2)

                return max(0.0, min(1.0, consistency))

        except Exception as e:
            self.logger.error(f"Error calculating ecosystem consistency: {e}")
            return 0.5

    def _identify_ecosystem_inconsistencies(
        self,
        tech_stack: List[str],
        ecosystem_scores: Dict[str, float],
        primary_ecosystem: str,
    ) -> List[Dict[str, Any]]:
        """Identify specific ecosystem inconsistencies."""
        inconsistencies = []

        try:
            # Find technologies that don't belong to primary ecosystem
            primary_patterns = self.ecosystem_patterns.get(primary_ecosystem, [])

            for tech in tech_stack:
                tech_lower = tech.lower()
                belongs_to_primary = any(
                    pattern in tech_lower for pattern in primary_patterns
                )

                if not belongs_to_primary:
                    # Check which ecosystem this tech belongs to
                    tech_ecosystems = []
                    for ecosystem, patterns in self.ecosystem_patterns.items():
                        if ecosystem != primary_ecosystem:
                            if any(pattern in tech_lower for pattern in patterns):
                                tech_ecosystems.append(ecosystem)

                    if tech_ecosystems:
                        inconsistencies.append(
                            {
                                "technology": tech,
                                "primary_ecosystem": primary_ecosystem,
                                "conflicting_ecosystems": tech_ecosystems,
                                "severity": (
                                    "high" if len(tech_ecosystems) > 1 else "medium"
                                ),
                            }
                        )

        except Exception as e:
            self.logger.error(f"Error identifying ecosystem inconsistencies: {e}")

        return inconsistencies

    def _generate_ecosystem_recommendations(
        self, inconsistencies: List[Dict[str, Any]], primary_ecosystem: str
    ) -> List[str]:
        """Generate ecosystem consistency recommendations."""
        recommendations = []

        if not inconsistencies:
            recommendations.append(
                f"Ecosystem consistency is good - all technologies align with {primary_ecosystem}"
            )
            return recommendations

        high_severity_count = sum(
            1 for inc in inconsistencies if inc.get("severity") == "high"
        )
        medium_severity_count = len(inconsistencies) - high_severity_count

        if high_severity_count > 0:
            recommendations.append(
                f"Resolve {high_severity_count} high-severity ecosystem conflicts"
            )

        if medium_severity_count > 0:
            recommendations.append(
                f"Consider alternatives for {medium_severity_count} technologies to improve {primary_ecosystem} consistency"
            )

        # Specific recommendations
        conflicting_techs = [inc["technology"] for inc in inconsistencies[:3]]  # Top 3
        if conflicting_techs:
            recommendations.append(
                f"Consider {primary_ecosystem} alternatives for: {', '.join(conflicting_techs)}"
            )

        return recommendations

    def _calculate_ecosystem_confidence(
        self, tech_stack: List[str], ecosystem_scores: Dict[str, float]
    ) -> float:
        """Calculate confidence in ecosystem consistency assessment."""
        try:
            # Base confidence on clarity of ecosystem signals
            max_score = max(ecosystem_scores.values()) if ecosystem_scores else 0
            total_score = sum(ecosystem_scores.values()) if ecosystem_scores else 0

            if total_score == 0:
                return 0.5  # Neutral confidence if no ecosystem detected

            # Higher confidence when one ecosystem clearly dominates
            dominance = max_score / total_score

            # Adjust confidence based on tech stack size
            size_factor = min(
                1.0, len(tech_stack) / 5
            )  # More confidence with more technologies

            confidence = (dominance * 0.7) + (size_factor * 0.3)
            return max(0.1, min(1.0, confidence))

        except Exception as e:
            self.logger.error(f"Error calculating ecosystem confidence: {e}")
            return 0.5

    # User satisfaction prediction methods
    async def _predict_relevance_satisfaction(
        self, tech_stack: List[str], generation_metrics: Dict[str, Any]
    ) -> float:
        """Predict user satisfaction with technology relevance."""
        try:
            # Base satisfaction on explicit technology inclusion rate
            explicit_inclusion_rate = generation_metrics.get(
                "explicit_inclusion_rate", 0.7
            )

            # Adjust based on tech stack size appropriateness
            stack_size = len(tech_stack)
            size_satisfaction = 1.0

            if stack_size < 3:
                size_satisfaction = 0.6  # Too few technologies
            elif stack_size > 15:
                size_satisfaction = 0.7  # Too many technologies

            # Combine factors
            relevance_satisfaction = (explicit_inclusion_rate * 0.7) + (
                size_satisfaction * 0.3
            )
            return max(0.0, min(1.0, relevance_satisfaction))

        except Exception as e:
            self.logger.error(f"Error predicting relevance satisfaction: {e}")
            return 0.7

    async def _predict_completeness_satisfaction(
        self, tech_stack: List[str], generation_metrics: Dict[str, Any]
    ) -> float:
        """Predict user satisfaction with completeness."""
        try:
            # Base satisfaction on catalog coverage and completeness
            catalog_coverage = generation_metrics.get("catalog_coverage", 0.8)
            missing_tech_count = generation_metrics.get("missing_technologies", 0)

            # Penalize missing technologies
            missing_penalty = min(0.3, missing_tech_count * 0.1)

            completeness_satisfaction = catalog_coverage - missing_penalty
            return max(0.0, min(1.0, completeness_satisfaction))

        except Exception as e:
            self.logger.error(f"Error predicting completeness satisfaction: {e}")
            return 0.75

    def _predict_performance_satisfaction(self, processing_time: float) -> float:
        """Predict user satisfaction with performance."""
        try:
            # Satisfaction decreases with processing time
            if processing_time <= 5.0:
                return 1.0  # Excellent
            elif processing_time <= 15.0:
                return 0.9  # Good
            elif processing_time <= 30.0:
                return 0.7  # Acceptable
            elif processing_time <= 60.0:
                return 0.5  # Poor
            else:
                return 0.3  # Very poor

        except Exception as e:
            self.logger.error(f"Error predicting performance satisfaction: {e}")
            return 0.7

    async def _predict_quality_satisfaction(self, result: Dict[str, Any]) -> float:
        """Predict user satisfaction with overall quality."""
        try:
            # Base quality on various result indicators
            quality_indicators = []

            # Check for validation results
            validation_results = result.get("validation_results", {})
            if validation_results:
                validation_score = validation_results.get("overall_score", 0.8)
                quality_indicators.append(validation_score)

            # Check for conflicts resolved
            conflicts_resolved = result.get("conflicts_resolved", 0)
            conflicts_total = result.get("conflicts_total", 0)

            if conflicts_total > 0:
                conflict_resolution_rate = conflicts_resolved / conflicts_total
                quality_indicators.append(conflict_resolution_rate)

            # Default quality if no specific indicators
            if not quality_indicators:
                quality_indicators.append(0.8)

            quality_satisfaction = sum(quality_indicators) / len(quality_indicators)
            return max(0.0, min(1.0, quality_satisfaction))

        except Exception as e:
            self.logger.error(f"Error predicting quality satisfaction: {e}")
            return 0.8

    def _incorporate_feedback(self, feedback: Dict[str, Any]) -> float:
        """Incorporate actual user feedback into satisfaction score."""
        try:
            # Extract feedback scores (assuming 1-5 scale)
            relevance_feedback = feedback.get("relevance", 4.0)
            accuracy_feedback = feedback.get("accuracy", 4.0)
            completeness_feedback = feedback.get("completeness", 4.0)

            # Convert to 0-1 scale
            relevance_score = (relevance_feedback - 1) / 4
            accuracy_score = (accuracy_feedback - 1) / 4
            completeness_score = (completeness_feedback - 1) / 4

            # Weighted average
            feedback_satisfaction = (
                relevance_score * 0.4 + accuracy_score * 0.3 + completeness_score * 0.3
            )
            return max(0.0, min(1.0, feedback_satisfaction))

        except Exception as e:
            self.logger.error(f"Error incorporating feedback: {e}")
            return 0.75

    # Storage and alert methods
    async def _store_quality_score(self, quality_score: QualityScore) -> None:
        """Store quality score and manage storage limits."""
        try:
            self.quality_scores.append(quality_score)

            # Limit stored scores
            max_scores = self.config["max_stored_scores"]
            if len(self.quality_scores) > max_scores:
                self.quality_scores = self.quality_scores[-max_scores:]

        except Exception as e:
            self.logger.error(f"Error storing quality score: {e}")

    async def _store_consistency_score(
        self, consistency_score: ConsistencyScore
    ) -> None:
        """Store consistency score."""
        try:
            self.consistency_scores.append(consistency_score)

            # Limit stored scores
            max_scores = self.config["max_stored_scores"]
            if len(self.consistency_scores) > max_scores:
                self.consistency_scores = self.consistency_scores[-max_scores:]

        except Exception as e:
            self.logger.error(f"Error storing consistency score: {e}")

    async def _check_quality_alerts(self, quality_score: QualityScore) -> None:
        """Check if quality score triggers alerts."""
        try:
            threshold = self.config["alert_thresholds"].get(
                quality_score.metric_type, 0.8
            )

            if quality_score.overall_score < threshold:
                severity = self._determine_alert_severity(
                    quality_score.overall_score, threshold
                )

                alert = QualityAlert(
                    alert_id=f"quality_{quality_score.metric_type.value}_{int(time.time())}",
                    timestamp=datetime.now(),
                    severity=severity,
                    metric_type=quality_score.metric_type,
                    message=f"Quality score below threshold: {quality_score.overall_score:.2f} < {threshold:.2f}",
                    current_value=quality_score.overall_score,
                    threshold_value=threshold,
                    session_id=quality_score.session_id,
                    details={
                        "component_scores": quality_score.component_scores,
                        "confidence": quality_score.confidence,
                        "details": quality_score.details,
                    },
                )

                await self._store_alert(alert)
                await self._notify_alert(alert)

        except Exception as e:
            self.logger.error(f"Error checking quality alerts: {e}")

    async def _check_consistency_alerts(
        self, consistency_score: ConsistencyScore
    ) -> None:
        """Check if consistency score triggers alerts."""
        try:
            threshold = self.config["alert_thresholds"].get(
                QualityMetricType.ECOSYSTEM_CONSISTENCY, 0.9
            )

            if consistency_score.consistency_score < threshold:
                severity = self._determine_alert_severity(
                    consistency_score.consistency_score, threshold
                )

                alert = QualityAlert(
                    alert_id=f"consistency_{int(time.time())}",
                    timestamp=datetime.now(),
                    severity=severity,
                    metric_type=QualityMetricType.ECOSYSTEM_CONSISTENCY,
                    message=f"Ecosystem consistency below threshold: {consistency_score.consistency_score:.2f} < {threshold:.2f}",
                    current_value=consistency_score.consistency_score,
                    threshold_value=threshold,
                    session_id=consistency_score.session_id,
                    details={
                        "ecosystem_detected": consistency_score.ecosystem_detected,
                        "inconsistencies": consistency_score.inconsistencies,
                        "recommendations": consistency_score.recommendations,
                    },
                )

                await self._store_alert(alert)
                await self._notify_alert(alert)

        except Exception as e:
            self.logger.error(f"Error checking consistency alerts: {e}")

    def _determine_alert_severity(
        self, current_value: float, threshold: float
    ) -> QualityAlertSeverity:
        """Determine alert severity based on how far below threshold the value is."""
        difference = threshold - current_value

        if difference >= 0.25:  # 25% below threshold
            return QualityAlertSeverity.CRITICAL
        elif difference >= 0.15:  # 15% below threshold
            return QualityAlertSeverity.ERROR
        elif difference >= 0.05:  # 5% below threshold
            return QualityAlertSeverity.WARNING
        else:
            return QualityAlertSeverity.INFO

    async def _store_alert(self, alert: QualityAlert) -> None:
        """Store quality alert."""
        try:
            self.quality_alerts.append(alert)

            # Limit stored alerts
            max_alerts = self.config["max_stored_alerts"]
            if len(self.quality_alerts) > max_alerts:
                self.quality_alerts = self.quality_alerts[-max_alerts:]

        except Exception as e:
            self.logger.error(f"Error storing alert: {e}")

    async def _notify_alert(self, alert: QualityAlert) -> None:
        """Notify about quality alert."""
        try:
            # Log the alert
            log_level = {
                QualityAlertSeverity.INFO: logging.INFO,
                QualityAlertSeverity.WARNING: logging.WARNING,
                QualityAlertSeverity.ERROR: logging.ERROR,
                QualityAlertSeverity.CRITICAL: logging.CRITICAL,
            }[alert.severity]

            self.logger.log(
                log_level,
                f"Quality Alert [{alert.metric_type.value}]: {alert.message}",
                extra={
                    "alert_id": alert.alert_id,
                    "session_id": alert.session_id,
                    "current_value": alert.current_value,
                    "threshold_value": alert.threshold_value,
                    "details": alert.details,
                },
            )

            # TODO: Add integration with external alerting systems (email, Slack, etc.)

        except Exception as e:
            self.logger.error(f"Error notifying alert: {e}")

    # Trend analysis methods
    async def _analyze_quality_trend(
        self, metric_type: QualityMetricType
    ) -> Optional[QualityTrend]:
        """Analyze quality trend for a specific metric type."""
        try:
            # Get recent scores for this metric type
            window_hours = self.config["trend_analysis_window_hours"]
            cutoff_time = datetime.now() - timedelta(hours=window_hours)

            recent_scores = [
                score
                for score in self.quality_scores
                if score.metric_type == metric_type and score.timestamp >= cutoff_time
            ]

            if len(recent_scores) < 5:  # Need minimum data points for trend analysis
                return None

            # Sort by timestamp
            recent_scores.sort(key=lambda x: x.timestamp)

            # Split into two halves for comparison
            mid_point = len(recent_scores) // 2
            first_half = recent_scores[:mid_point]
            second_half = recent_scores[mid_point:]

            # Calculate averages
            first_avg = sum(score.overall_score for score in first_half) / len(
                first_half
            )
            second_avg = sum(score.overall_score for score in second_half) / len(
                second_half
            )

            # Calculate trend
            change_rate = second_avg - first_avg

            # Determine trend direction and strength
            if abs(change_rate) < 0.05:  # 5% threshold for stability
                trend_direction = "stable"
                trend_strength = 0.0
            elif change_rate > 0:
                trend_direction = "improving"
                trend_strength = min(
                    1.0, change_rate / 0.3
                )  # Normalize to 30% change = 1.0 strength
            else:
                trend_direction = "declining"
                trend_strength = min(1.0, abs(change_rate) / 0.3)

            return QualityTrend(
                metric_type=metric_type,
                time_window_hours=window_hours,
                trend_direction=trend_direction,
                trend_strength=trend_strength,
                current_average=second_avg,
                previous_average=first_avg,
                change_rate=change_rate,
                data_points=len(recent_scores),
                timestamp=datetime.now(),
            )

        except Exception as e:
            self.logger.error(f"Error analyzing quality trend for {metric_type}: {e}")
            return None

    async def _create_degradation_alert(self, trend: QualityTrend) -> None:
        """Create alert for quality degradation."""
        try:
            alert = QualityAlert(
                alert_id=f"degradation_{trend.metric_type.value}_{int(time.time())}",
                timestamp=datetime.now(),
                severity=QualityAlertSeverity.WARNING,
                metric_type=trend.metric_type,
                message=f"Quality degradation detected: {trend.metric_type.value} declining by {abs(trend.change_rate):.1%}",
                current_value=trend.current_average,
                threshold_value=trend.previous_average,
                session_id=None,
                details={
                    "trend_direction": trend.trend_direction,
                    "trend_strength": trend.trend_strength,
                    "change_rate": trend.change_rate,
                    "time_window_hours": trend.time_window_hours,
                    "data_points": trend.data_points,
                },
            )

            await self._store_alert(alert)
            await self._notify_alert(alert)

        except Exception as e:
            self.logger.error(f"Error creating degradation alert: {e}")

    # Maintenance methods
    async def _check_quality_degradation(self) -> None:
        """Check for overall quality degradation across all metrics."""
        try:
            # Get recent quality scores (last hour)
            cutoff_time = datetime.now() - timedelta(hours=1)
            recent_scores = [
                score for score in self.quality_scores if score.timestamp >= cutoff_time
            ]

            if len(recent_scores) < 3:
                return

            # Calculate average quality by metric type
            metric_averages = {}
            for metric_type in QualityMetricType:
                type_scores = [
                    score.overall_score
                    for score in recent_scores
                    if score.metric_type == metric_type
                ]
                if type_scores:
                    metric_averages[metric_type] = sum(type_scores) / len(type_scores)

            # Check for degradation
            degraded_metrics = []
            for metric_type, avg_score in metric_averages.items():
                threshold = self.config["alert_thresholds"].get(metric_type, 0.8)
                if avg_score < threshold - self.config["degradation_threshold"]:
                    degraded_metrics.append((metric_type, avg_score, threshold))

            # Create degradation alert if multiple metrics affected
            if len(degraded_metrics) >= 2:
                alert = QualityAlert(
                    alert_id=f"multi_degradation_{int(time.time())}",
                    timestamp=datetime.now(),
                    severity=QualityAlertSeverity.ERROR,
                    metric_type=QualityMetricType.RESPONSE_QUALITY,  # General quality metric
                    message=f"Multiple quality metrics degraded: {len(degraded_metrics)} metrics below thresholds",
                    current_value=sum(score for _, score, _ in degraded_metrics)
                    / len(degraded_metrics),
                    threshold_value=sum(
                        threshold for _, _, threshold in degraded_metrics
                    )
                    / len(degraded_metrics),
                    session_id=None,
                    details={
                        "degraded_metrics": [
                            {
                                "metric": metric.value,
                                "score": score,
                                "threshold": threshold,
                            }
                            for metric, score, threshold in degraded_metrics
                        ]
                    },
                )

                await self._store_alert(alert)
                await self._notify_alert(alert)

        except Exception as e:
            self.logger.error(f"Error checking quality degradation: {e}")

    async def _update_dynamic_thresholds(self) -> None:
        """Update quality thresholds based on recent performance."""
        try:
            # Get recent performance data (last 7 days)
            cutoff_time = datetime.now() - timedelta(days=7)
            recent_scores = [
                score for score in self.quality_scores if score.timestamp >= cutoff_time
            ]

            if len(recent_scores) < 20:  # Need sufficient data
                return

            # Update thresholds for each metric type
            for metric_type in QualityMetricType:
                type_scores = [
                    score.overall_score
                    for score in recent_scores
                    if score.metric_type == metric_type
                ]

                if len(type_scores) >= 10:
                    # Calculate new threshold as 2 standard deviations below mean
                    mean_score = statistics.mean(type_scores)
                    std_score = statistics.stdev(type_scores)

                    new_threshold = max(
                        0.5, mean_score - (2 * std_score)
                    )  # Don't go below 0.5
                    current_threshold = self.config["alert_thresholds"].get(
                        metric_type, 0.8
                    )

                    # Only update if change is significant (>5%)
                    if abs(new_threshold - current_threshold) > 0.05:
                        self.config["alert_thresholds"][metric_type] = new_threshold

                        self.logger.info(
                            f"Updated {metric_type.value} threshold: {current_threshold:.2f} -> {new_threshold:.2f}"
                        )

        except Exception as e:
            self.logger.error(f"Error updating dynamic thresholds: {e}")

    async def _cleanup_old_data(self) -> None:
        """Clean up old quality data to prevent memory issues."""
        try:
            # Remove data older than 7 days
            cutoff_time = datetime.now() - timedelta(days=7)

            # Clean up quality scores
            self.quality_scores = [
                score for score in self.quality_scores if score.timestamp >= cutoff_time
            ]

            # Clean up consistency scores
            self.consistency_scores = [
                score
                for score in self.consistency_scores
                if score.timestamp >= cutoff_time
            ]

            # Clean up resolved alerts older than 24 hours
            alert_cutoff = datetime.now() - timedelta(hours=24)
            self.quality_alerts = [
                alert
                for alert in self.quality_alerts
                if not alert.resolved or alert.timestamp >= alert_cutoff
            ]

        except Exception as e:
            self.logger.error(f"Error cleaning up old data: {e}")

    # Public API methods
    def get_current_quality_status(self) -> Dict[str, Any]:
        """Get current quality status across all metrics."""
        try:
            # Get recent scores (last hour)
            cutoff_time = datetime.now() - timedelta(hours=1)
            recent_scores = [
                score for score in self.quality_scores if score.timestamp >= cutoff_time
            ]

            # Calculate current status by metric type
            status = {}
            for metric_type in QualityMetricType:
                type_scores = [
                    score.overall_score
                    for score in recent_scores
                    if score.metric_type == metric_type
                ]

                if type_scores:
                    avg_score = sum(type_scores) / len(type_scores)
                    threshold = self.config["alert_thresholds"].get(metric_type, 0.8)

                    status[metric_type.value] = {
                        "current_score": avg_score,
                        "threshold": threshold,
                        "status": "good" if avg_score >= threshold else "degraded",
                        "sample_count": len(type_scores),
                        "last_updated": max(
                            score.timestamp
                            for score in recent_scores
                            if score.metric_type == metric_type
                        ).isoformat(),
                    }
                else:
                    status[metric_type.value] = {
                        "current_score": None,
                        "threshold": self.config["alert_thresholds"].get(
                            metric_type, 0.8
                        ),
                        "status": "no_data",
                        "sample_count": 0,
                        "last_updated": None,
                    }

            return {
                "overall_status": (
                    "good"
                    if all(
                        s.get("status") in ["good", "no_data"] for s in status.values()
                    )
                    else "degraded"
                ),
                "metrics": status,
                "active_alerts": len(
                    [alert for alert in self.quality_alerts if not alert.resolved]
                ),
                "monitoring_enabled": self.is_monitoring,
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting current quality status: {e}")
            return {
                "overall_status": "error",
                "metrics": {},
                "active_alerts": 0,
                "monitoring_enabled": False,
                "error": str(e),
            }

    def get_quality_trends(self) -> Dict[str, Any]:
        """Get quality trends for all metrics."""
        try:
            trends = {}
            for metric_type, trend in self.quality_trends.items():
                trends[metric_type.value] = trend.to_dict()

            return {
                "trends": trends,
                "analysis_window_hours": self.config["trend_analysis_window_hours"],
                "last_updated": datetime.now().isoformat(),
            }

        except Exception as e:
            self.logger.error(f"Error getting quality trends: {e}")
            return {"trends": {}, "error": str(e)}

    def get_active_alerts(self) -> List[Dict[str, Any]]:
        """Get all active quality alerts."""
        try:
            active_alerts = [
                alert for alert in self.quality_alerts if not alert.resolved
            ]
            return [alert.to_dict() for alert in active_alerts]

        except Exception as e:
            self.logger.error(f"Error getting active alerts: {e}")
            return []

    async def resolve_alert(self, alert_id: str) -> bool:
        """Resolve a quality alert."""
        try:
            for alert in self.quality_alerts:
                if alert.alert_id == alert_id and not alert.resolved:
                    alert.resolved = True
                    alert.resolution_time = datetime.now()

                    self.logger.info(f"Resolved quality alert: {alert_id}")
                    return True

            return False

        except Exception as e:
            self.logger.error(f"Error resolving alert {alert_id}: {e}")
            return False
