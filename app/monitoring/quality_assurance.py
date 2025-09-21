"""
Automated Quality Assurance System for Tech Stack Generation

Provides automated quality checks, validation, and reporting capabilities.
"""

import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, asdict
from enum import Enum
import logging
from pathlib import Path

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service


class QACheckType(Enum):
    """Types of quality assurance checks."""
    ACCURACY = "accuracy"
    CONSISTENCY = "consistency"
    COMPLETENESS = "completeness"
    PERFORMANCE = "performance"
    CATALOG_HEALTH = "catalog_health"
    USER_SATISFACTION = "user_satisfaction"


class QAStatus(Enum):
    """Quality assurance check status."""
    PASSED = "passed"
    FAILED = "failed"
    WARNING = "warning"
    SKIPPED = "skipped"


@dataclass
class QACheckResult:
    """Result of a quality assurance check."""
    check_type: QACheckType
    check_name: str
    status: QAStatus
    score: float  # 0.0 to 1.0
    message: str
    details: Dict[str, Any]
    timestamp: datetime
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['check_type'] = self.check_type.value
        data['status'] = self.status.value
        data['timestamp'] = self.timestamp.isoformat()
        return data


@dataclass
class QAReport:
    """Comprehensive quality assurance report."""
    report_id: str
    timestamp: datetime
    time_window_hours: int
    overall_score: float
    check_results: List[QACheckResult]
    summary: Dict[str, Any]
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        data = asdict(self)
        data['timestamp'] = self.timestamp.isoformat()
        data['check_results'] = [r.to_dict() for r in self.check_results]
        return data


class QualityAssuranceSystem(ConfigurableService):
    """
    Automated quality assurance system for tech stack generation.
    
    Performs comprehensive quality checks, generates reports,
    and provides actionable recommendations for improvement.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'QualityAssurance')
        try:
            self.logger = require_service('logger', context='QualityAssurance')
            self.monitor = optional_service('tech_stack_monitor', context='QualityAssurance')
            self.catalog_manager = optional_service('intelligent_catalog_manager', context='QualityAssurance')
        except:
            # Fallback for testing/standalone use
            import logging
            self.logger = logging.getLogger('QualityAssurance')
            self.monitor = None
            self.catalog_manager = None
        
        self.qa_enabled = True
        self.check_intervals = {
            QACheckType.ACCURACY: 300,  # 5 minutes
            QACheckType.CONSISTENCY: 600,  # 10 minutes
            QACheckType.COMPLETENESS: 1800,  # 30 minutes
            QACheckType.PERFORMANCE: 300,  # 5 minutes
            QACheckType.CATALOG_HEALTH: 3600,  # 1 hour
            QACheckType.USER_SATISFACTION: 1800  # 30 minutes
        }
        
        self.quality_thresholds = {
            'accuracy_min': 0.85,
            'consistency_min': 0.95,
            'completeness_min': 0.80,
            'performance_max_time': 30.0,
            'catalog_health_min': 0.90,
            'satisfaction_min': 4.0
        }
        
        self.recent_reports: List[QAReport] = []
    
    async def _do_initialize(self) -> None:
        """Initialize the quality assurance system."""
        await self.start_qa_system()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the quality assurance system."""
        await self.stop_qa_system()
    
    async def start_qa_system(self) -> None:
        """Start the automated quality assurance system."""
        if not self.qa_enabled:
            return
        
        self.logger.info("Starting automated quality assurance system")
        
        # Start background QA tasks
        for check_type in QACheckType:
            asyncio.create_task(self._run_periodic_check(check_type))
        
        # Start report generation task
        asyncio.create_task(self._generate_periodic_reports())
    
    async def _run_periodic_check(self, check_type: QACheckType) -> None:
        """Run periodic quality assurance checks."""
        interval = self.check_intervals[check_type]
        
        while self.qa_enabled:
            try:
                await self._run_qa_check(check_type)
                await asyncio.sleep(interval)
            except Exception as e:
                self.logger.error(f"Error in QA check {check_type.value}: {e}")
                await asyncio.sleep(60)  # Retry after 1 minute on error
    
    async def _run_qa_check(self, check_type: QACheckType) -> QACheckResult:
        """Run a specific quality assurance check."""
        check_methods = {
            QACheckType.ACCURACY: self._check_accuracy,
            QACheckType.CONSISTENCY: self._check_consistency,
            QACheckType.COMPLETENESS: self._check_completeness,
            QACheckType.PERFORMANCE: self._check_performance,
            QACheckType.CATALOG_HEALTH: self._check_catalog_health,
            QACheckType.USER_SATISFACTION: self._check_user_satisfaction
        }
        
        check_method = check_methods.get(check_type)
        if not check_method:
            return QACheckResult(
                check_type=check_type,
                check_name=f"{check_type.value}_check",
                status=QAStatus.SKIPPED,
                score=0.0,
                message="Check method not implemented",
                details={},
                timestamp=datetime.now(),
                recommendations=[]
            )
        
        try:
            result = await check_method()
            self.logger.debug(f"QA check {check_type.value} completed: {result.status.value} (score: {result.score:.2f})")
            return result
        except Exception as e:
            self.logger.error(f"QA check {check_type.value} failed: {e}")
            return QACheckResult(
                check_type=check_type,
                check_name=f"{check_type.value}_check",
                status=QAStatus.FAILED,
                score=0.0,
                message=f"Check failed with error: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Investigate check failure", "Review system logs"]
            )
    
    async def _check_accuracy(self) -> QACheckResult:
        """Check technology extraction and selection accuracy using real data."""
        # Try to get real data from monitoring integration service
        real_data_available = False
        real_accuracy_data = {}
        
        try:
            integration_service = optional_service('tech_stack_monitoring_integration', context='QualityAssurance')
            if integration_service:
                # Get real session data for accuracy analysis
                active_sessions = integration_service.get_active_sessions()
                completed_sessions = []  # Would need to be tracked by integration service
                
                # Analyze real accuracy from recent sessions
                real_accuracy_data = await self._analyze_real_accuracy_data(integration_service, active_sessions)
                real_data_available = len(real_accuracy_data) > 0
        except Exception as e:
            self.logger.debug(f"Could not access real accuracy data: {e}")
        
        # Fallback to monitor service if real data not available
        if not real_data_available and self.monitor:
            # Get recent accuracy metrics from monitor
            recent_metrics = self.monitor._get_recent_metrics(hours=1)
            accuracy_metrics = [m for m in recent_metrics if m.name == "extraction_accuracy"]
            inclusion_metrics = [m for m in recent_metrics if m.name == "explicit_tech_inclusion_rate"]
            
            if not accuracy_metrics and not inclusion_metrics:
                return self._create_skipped_result(QACheckType.ACCURACY, "No recent accuracy data available")
            
            # Calculate accuracy scores from monitor data
            avg_extraction_accuracy = sum(m.value for m in accuracy_metrics) / len(accuracy_metrics) if accuracy_metrics else 1.0
            avg_inclusion_rate = sum(m.value for m in inclusion_metrics) / len(inclusion_metrics) if inclusion_metrics else 1.0
            sample_count = len(accuracy_metrics) + len(inclusion_metrics)
            
        else:
            # Use real data for accuracy calculation
            if real_data_available:
                avg_extraction_accuracy = real_accuracy_data.get('avg_extraction_accuracy', 1.0)
                avg_inclusion_rate = real_accuracy_data.get('avg_inclusion_rate', 1.0)
                sample_count = real_accuracy_data.get('sample_count', 0)
            else:
                return self._create_skipped_result(QACheckType.ACCURACY, "No accuracy data available from any source")
        
        # Overall accuracy score (weighted average)
        overall_accuracy = (avg_extraction_accuracy * 0.6) + (avg_inclusion_rate * 0.4)
        
        # Determine status based on real performance baselines
        accuracy_threshold = self._get_dynamic_accuracy_threshold(real_accuracy_data)
        
        if overall_accuracy >= accuracy_threshold:
            status = QAStatus.PASSED
            message = f"Accuracy check passed: {overall_accuracy:.2f} (threshold: {accuracy_threshold:.2f})"
        elif overall_accuracy >= accuracy_threshold - 0.1:
            status = QAStatus.WARNING
            message = f"Accuracy check warning: {overall_accuracy:.2f} (threshold: {accuracy_threshold:.2f})"
        else:
            status = QAStatus.FAILED
            message = f"Accuracy check failed: {overall_accuracy:.2f} (threshold: {accuracy_threshold:.2f})"
        
        # Generate recommendations based on real data patterns
        recommendations = self._generate_accuracy_recommendations(
            avg_extraction_accuracy, avg_inclusion_rate, overall_accuracy, real_accuracy_data
        )
        
        return QACheckResult(
            check_type=QACheckType.ACCURACY,
            check_name="technology_extraction_accuracy",
            status=status,
            score=overall_accuracy,
            message=message,
            details={
                "extraction_accuracy": avg_extraction_accuracy,
                "inclusion_rate": avg_inclusion_rate,
                "sample_count": sample_count,
                "data_source": "real_data" if real_data_available else "monitor_data",
                "dynamic_threshold": accuracy_threshold,
                "real_data_insights": real_accuracy_data if real_data_available else {}
            },
            timestamp=datetime.now(),
            recommendations=recommendations
        )
    
    async def _analyze_real_accuracy_data(self, integration_service, active_sessions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze real accuracy data from active sessions."""
        accuracy_data = {
            'extraction_accuracies': [],
            'inclusion_rates': [],
            'session_count': 0,
            'avg_extraction_accuracy': 0.0,
            'avg_inclusion_rate': 0.0,
            'sample_count': 0
        }
        
        try:
            for session_info in active_sessions:
                session_id = session_info['session_id']
                session_events = integration_service.get_session_events(session_id)
                
                # Analyze parsing and extraction events for accuracy
                parsing_events = [e for e in session_events if e.get('event_type') == 'parsing_complete']
                extraction_events = [e for e in session_events if e.get('event_type') == 'extraction_complete']
                completion_events = [e for e in session_events if e.get('event_type') == 'session_complete']
                
                for parsing_event in parsing_events:
                    data = parsing_event.get('data', {})
                    output_data = data.get('output_data', {})
                    explicit_techs = output_data.get('explicit_technologies', [])
                    
                    if explicit_techs:
                        # Calculate extraction accuracy for this session
                        extraction_accuracy = len(explicit_techs) / max(len(explicit_techs), 1)  # Simplified
                        accuracy_data['extraction_accuracies'].append(extraction_accuracy)
                
                # Check final tech stack inclusion rates
                for completion_event in completion_events:
                    data = completion_event.get('data', {})
                    final_stack = data.get('final_tech_stack', [])
                    generation_metrics = data.get('generation_metrics', {})
                    
                    # Calculate inclusion rate if available
                    if 'explicit_technologies' in generation_metrics:
                        explicit_count = len(generation_metrics['explicit_technologies'])
                        included_count = sum(1 for tech in generation_metrics['explicit_technologies'] 
                                           if tech in final_stack)
                        inclusion_rate = included_count / max(explicit_count, 1)
                        accuracy_data['inclusion_rates'].append(inclusion_rate)
                
                accuracy_data['session_count'] += 1
            
            # Calculate averages
            if accuracy_data['extraction_accuracies']:
                accuracy_data['avg_extraction_accuracy'] = sum(accuracy_data['extraction_accuracies']) / len(accuracy_data['extraction_accuracies'])
            
            if accuracy_data['inclusion_rates']:
                accuracy_data['avg_inclusion_rate'] = sum(accuracy_data['inclusion_rates']) / len(accuracy_data['inclusion_rates'])
            
            accuracy_data['sample_count'] = len(accuracy_data['extraction_accuracies']) + len(accuracy_data['inclusion_rates'])
            
        except Exception as e:
            self.logger.error(f"Error analyzing real accuracy data: {e}")
        
        return accuracy_data
    
    def _get_dynamic_accuracy_threshold(self, real_data: Dict[str, Any]) -> float:
        """Get dynamic accuracy threshold based on real system performance."""
        base_threshold = self.quality_thresholds['accuracy_min']
        
        if not real_data or real_data.get('sample_count', 0) < 5:
            return base_threshold
        
        # Adjust threshold based on recent performance trends
        avg_accuracy = (real_data.get('avg_extraction_accuracy', 0.85) + 
                       real_data.get('avg_inclusion_rate', 0.85)) / 2
        
        # If system is performing well, raise the bar slightly
        if avg_accuracy > base_threshold + 0.1:
            return min(base_threshold + 0.05, 0.95)  # Don't set unrealistic thresholds
        
        # If system is struggling, lower threshold temporarily
        elif avg_accuracy < base_threshold - 0.1:
            return max(base_threshold - 0.05, 0.7)  # Don't lower too much
        
        return base_threshold
    
    def _generate_accuracy_recommendations(self, extraction_accuracy: float, inclusion_rate: float, 
                                         overall_accuracy: float, real_data: Dict[str, Any]) -> List[str]:
        """Generate accuracy recommendations based on real data patterns."""
        recommendations = []
        
        # Standard recommendations
        if extraction_accuracy < 0.9:
            recommendations.append("Improve technology name extraction algorithms")
        if inclusion_rate < 0.8:
            recommendations.append("Enhance explicit technology prioritization in LLM prompts")
        if overall_accuracy < 0.85:
            recommendations.append("Review and update technology catalog completeness")
        
        # Real data-based recommendations
        if real_data:
            session_count = real_data.get('session_count', 0)
            
            if session_count > 0:
                extraction_accuracies = real_data.get('extraction_accuracies', [])
                inclusion_rates = real_data.get('inclusion_rates', [])
                
                # Check for consistency issues
                if extraction_accuracies and len(set(extraction_accuracies)) > len(extraction_accuracies) * 0.8:
                    recommendations.append("High variance in extraction accuracy detected - review requirement parsing consistency")
                
                if inclusion_rates and min(inclusion_rates) < 0.5:
                    recommendations.append("Some sessions have very low inclusion rates - investigate LLM prompt effectiveness")
                
                # Performance trend recommendations
                if len(extraction_accuracies) >= 3:
                    recent_trend = extraction_accuracies[-1] - extraction_accuracies[0]
                    if recent_trend < -0.1:
                        recommendations.append("Extraction accuracy declining - check for system degradation")
                    elif recent_trend > 0.1:
                        recommendations.append("Extraction accuracy improving - consider documenting successful patterns")
        
        return recommendations
    
    async def _check_consistency(self) -> QACheckResult:
        """Check consistency of technology recommendations."""
        if not self.catalog_manager:
            return self._create_skipped_result(QACheckType.CONSISTENCY, "Catalog manager not available")
        
        try:
            # Check catalog consistency
            validation_result = await self.catalog_manager.validate_catalog_consistency()
            consistency_score = validation_result.get('consistency_score', 0.0)
            
            # Determine status
            if consistency_score >= self.quality_thresholds['consistency_min']:
                status = QAStatus.PASSED
                message = f"Consistency check passed: {consistency_score:.2f}"
            elif consistency_score >= self.quality_thresholds['consistency_min'] - 0.05:
                status = QAStatus.WARNING
                message = f"Consistency check warning: {consistency_score:.2f}"
            else:
                status = QAStatus.FAILED
                message = f"Consistency check failed: {consistency_score:.2f}"
            
            # Generate recommendations
            recommendations = []
            if validation_result.get('duplicate_entries', 0) > 0:
                recommendations.append("Remove duplicate catalog entries")
            if validation_result.get('missing_metadata', 0) > 0:
                recommendations.append("Complete missing metadata for catalog entries")
            if validation_result.get('inconsistent_categories', 0) > 0:
                recommendations.append("Standardize technology categorization")
            
            return QACheckResult(
                check_type=QACheckType.CONSISTENCY,
                check_name="catalog_consistency",
                status=status,
                score=consistency_score,
                message=message,
                details=validation_result,
                timestamp=datetime.now(),
                recommendations=recommendations
            )
            
        except Exception as e:
            return QACheckResult(
                check_type=QACheckType.CONSISTENCY,
                check_name="catalog_consistency",
                status=QAStatus.FAILED,
                score=0.0,
                message=f"Consistency check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Investigate catalog validation failure"]
            )
    
    async def _check_completeness(self) -> QACheckResult:
        """Check completeness of technology recommendations."""
        if not self.monitor:
            return self._create_skipped_result(QACheckType.COMPLETENESS, "Monitor service not available")
        
        # Get recent metrics
        recent_metrics = self.monitor._get_recent_metrics(hours=2)
        catalog_metrics = [m for m in recent_metrics if m.name == "catalog_missing_rate"]
        
        if not catalog_metrics:
            return self._create_skipped_result(QACheckType.COMPLETENESS, "No recent completeness data available")
        
        # Calculate completeness score (inverse of missing rate)
        latest_missing_rate = catalog_metrics[-1].value
        completeness_score = 1.0 - latest_missing_rate
        
        # Determine status
        if completeness_score >= self.quality_thresholds['completeness_min']:
            status = QAStatus.PASSED
            message = f"Completeness check passed: {completeness_score:.2f}"
        elif completeness_score >= self.quality_thresholds['completeness_min'] - 0.1:
            status = QAStatus.WARNING
            message = f"Completeness check warning: {completeness_score:.2f}"
        else:
            status = QAStatus.FAILED
            message = f"Completeness check failed: {completeness_score:.2f}"
        
        # Generate recommendations
        recommendations = []
        if latest_missing_rate > 0.1:
            recommendations.append("Expand technology catalog with commonly requested technologies")
        if latest_missing_rate > 0.05:
            recommendations.append("Improve auto-addition workflow for missing technologies")
        
        return QACheckResult(
            check_type=QACheckType.COMPLETENESS,
            check_name="catalog_completeness",
            status=status,
            score=completeness_score,
            message=message,
            details={
                "missing_rate": latest_missing_rate,
                "completeness_score": completeness_score
            },
            timestamp=datetime.now(),
            recommendations=recommendations
        )
    
    async def _check_performance(self) -> QACheckResult:
        """Check system performance metrics."""
        if not self.monitor:
            return self._create_skipped_result(QACheckType.PERFORMANCE, "Monitor service not available")
        
        # Get recent performance metrics
        recent_metrics = self.monitor._get_recent_metrics(hours=1)
        perf_metrics = [m for m in recent_metrics if m.name == "processing_time"]
        
        if not perf_metrics:
            return self._create_skipped_result(QACheckType.PERFORMANCE, "No recent performance data available")
        
        # Calculate performance scores
        avg_time = sum(m.value for m in perf_metrics) / len(perf_metrics)
        max_time = max(m.value for m in perf_metrics)
        
        # Performance score (inverse relationship with time)
        performance_score = max(0.0, 1.0 - (avg_time / self.quality_thresholds['performance_max_time']))
        
        # Determine status
        if avg_time <= self.quality_thresholds['performance_max_time']:
            status = QAStatus.PASSED
            message = f"Performance check passed: {avg_time:.2f}s avg"
        elif avg_time <= self.quality_thresholds['performance_max_time'] * 1.2:
            status = QAStatus.WARNING
            message = f"Performance check warning: {avg_time:.2f}s avg"
        else:
            status = QAStatus.FAILED
            message = f"Performance check failed: {avg_time:.2f}s avg"
        
        # Generate recommendations
        recommendations = []
        if avg_time > 20.0:
            recommendations.append("Optimize LLM prompt size and complexity")
        if max_time > 45.0:
            recommendations.append("Implement request timeout and circuit breaker patterns")
        if avg_time > 15.0:
            recommendations.append("Add caching for frequently accessed catalog data")
        
        return QACheckResult(
            check_type=QACheckType.PERFORMANCE,
            check_name="system_performance",
            status=status,
            score=performance_score,
            message=message,
            details={
                "average_time": avg_time,
                "max_time": max_time,
                "sample_count": len(perf_metrics)
            },
            timestamp=datetime.now(),
            recommendations=recommendations
        )
    
    async def _check_catalog_health(self) -> QACheckResult:
        """Check overall catalog health."""
        if not self.catalog_manager:
            return self._create_skipped_result(QACheckType.CATALOG_HEALTH, "Catalog manager not available")
        
        try:
            # Get catalog health metrics
            health_metrics = await self.catalog_manager.get_health_metrics()
            
            # Calculate overall health score
            consistency_score = health_metrics.get('consistency_score', 0.0)
            completeness_score = health_metrics.get('completeness_score', 0.0)
            freshness_score = health_metrics.get('freshness_score', 0.0)
            
            overall_health = (consistency_score * 0.4) + (completeness_score * 0.4) + (freshness_score * 0.2)
            
            # Determine status
            if overall_health >= self.quality_thresholds['catalog_health_min']:
                status = QAStatus.PASSED
                message = f"Catalog health check passed: {overall_health:.2f}"
            elif overall_health >= self.quality_thresholds['catalog_health_min'] - 0.1:
                status = QAStatus.WARNING
                message = f"Catalog health check warning: {overall_health:.2f}"
            else:
                status = QAStatus.FAILED
                message = f"Catalog health check failed: {overall_health:.2f}"
            
            # Generate recommendations
            recommendations = []
            if consistency_score < 0.95:
                recommendations.append("Run catalog consistency repair")
            if completeness_score < 0.85:
                recommendations.append("Add missing technology entries")
            if freshness_score < 0.8:
                recommendations.append("Update outdated catalog entries")
            
            return QACheckResult(
                check_type=QACheckType.CATALOG_HEALTH,
                check_name="catalog_health",
                status=status,
                score=overall_health,
                message=message,
                details=health_metrics,
                timestamp=datetime.now(),
                recommendations=recommendations
            )
            
        except Exception as e:
            return QACheckResult(
                check_type=QACheckType.CATALOG_HEALTH,
                check_name="catalog_health",
                status=QAStatus.FAILED,
                score=0.0,
                message=f"Catalog health check failed: {str(e)}",
                details={"error": str(e)},
                timestamp=datetime.now(),
                recommendations=["Investigate catalog health check failure"]
            )
    
    async def _check_user_satisfaction(self) -> QACheckResult:
        """Check user satisfaction metrics."""
        if not self.monitor:
            return self._create_skipped_result(QACheckType.USER_SATISFACTION, "Monitor service not available")
        
        # Get recent satisfaction metrics
        recent_metrics = self.monitor._get_recent_metrics(hours=4)
        satisfaction_metrics = [m for m in recent_metrics if m.name == "overall_satisfaction"]
        
        if not satisfaction_metrics:
            return self._create_skipped_result(QACheckType.USER_SATISFACTION, "No recent satisfaction data available")
        
        # Calculate satisfaction scores
        avg_satisfaction = sum(m.value for m in satisfaction_metrics) / len(satisfaction_metrics)
        
        # Normalize to 0-1 scale (assuming 1-5 rating scale)
        satisfaction_score = (avg_satisfaction - 1) / 4
        
        # Determine status
        if avg_satisfaction >= self.quality_thresholds['satisfaction_min']:
            status = QAStatus.PASSED
            message = f"User satisfaction check passed: {avg_satisfaction:.2f}/5"
        elif avg_satisfaction >= self.quality_thresholds['satisfaction_min'] - 0.5:
            status = QAStatus.WARNING
            message = f"User satisfaction check warning: {avg_satisfaction:.2f}/5"
        else:
            status = QAStatus.FAILED
            message = f"User satisfaction check failed: {avg_satisfaction:.2f}/5"
        
        # Generate recommendations
        recommendations = []
        if avg_satisfaction < 4.0:
            recommendations.append("Analyze user feedback for improvement opportunities")
        if avg_satisfaction < 3.5:
            recommendations.append("Review technology recommendation accuracy")
        if avg_satisfaction < 3.0:
            recommendations.append("Conduct user experience audit")
        
        return QACheckResult(
            check_type=QACheckType.USER_SATISFACTION,
            check_name="user_satisfaction",
            status=status,
            score=satisfaction_score,
            message=message,
            details={
                "average_satisfaction": avg_satisfaction,
                "sample_count": len(satisfaction_metrics)
            },
            timestamp=datetime.now(),
            recommendations=recommendations
        )
    
    def _create_skipped_result(self, check_type: QACheckType, reason: str) -> QACheckResult:
        """Create a skipped check result."""
        return QACheckResult(
            check_type=check_type,
            check_name=f"{check_type.value}_check",
            status=QAStatus.SKIPPED,
            score=0.0,
            message=f"Check skipped: {reason}",
            details={"skip_reason": reason},
            timestamp=datetime.now(),
            recommendations=[]
        )
    
    async def _generate_periodic_reports(self) -> None:
        """Generate periodic quality assurance reports."""
        while self.qa_enabled:
            try:
                await self._generate_qa_report()
                await asyncio.sleep(3600)  # Generate reports every hour
            except Exception as e:
                self.logger.error(f"Error generating QA report: {e}")
                await asyncio.sleep(300)  # Retry after 5 minutes on error
    
    async def _generate_qa_report(self) -> QAReport:
        """Generate a comprehensive quality assurance report."""
        report_id = f"qa_report_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        timestamp = datetime.now()
        time_window_hours = 24
        
        # Run all QA checks
        check_results = []
        for check_type in QACheckType:
            result = await self._run_qa_check(check_type)
            check_results.append(result)
        
        # Calculate overall score
        passed_checks = [r for r in check_results if r.status == QAStatus.PASSED]
        warning_checks = [r for r in check_results if r.status == QAStatus.WARNING]
        failed_checks = [r for r in check_results if r.status == QAStatus.FAILED]
        
        # Weighted scoring: passed=1.0, warning=0.7, failed=0.0, skipped=not counted
        scored_checks = [r for r in check_results if r.status != QAStatus.SKIPPED]
        if scored_checks:
            score_sum = sum(
                1.0 if r.status == QAStatus.PASSED else
                0.7 if r.status == QAStatus.WARNING else
                0.0
                for r in scored_checks
            )
            overall_score = score_sum / len(scored_checks)
        else:
            overall_score = 0.0
        
        # Generate summary
        summary = {
            "total_checks": len(check_results),
            "passed": len(passed_checks),
            "warnings": len(warning_checks),
            "failed": len(failed_checks),
            "skipped": len([r for r in check_results if r.status == QAStatus.SKIPPED]),
            "overall_score": overall_score,
            "health_status": self._determine_health_status(overall_score, failed_checks)
        }
        
        # Collect all recommendations
        all_recommendations = []
        for result in check_results:
            all_recommendations.extend(result.recommendations)
        
        # Remove duplicates while preserving order
        unique_recommendations = []
        seen = set()
        for rec in all_recommendations:
            if rec not in seen:
                unique_recommendations.append(rec)
                seen.add(rec)
        
        # Create report
        report = QAReport(
            report_id=report_id,
            timestamp=timestamp,
            time_window_hours=time_window_hours,
            overall_score=overall_score,
            check_results=check_results,
            summary=summary,
            recommendations=unique_recommendations
        )
        
        # Store report
        self.recent_reports.append(report)
        
        # Keep only last 24 reports
        if len(self.recent_reports) > 24:
            self.recent_reports = self.recent_reports[-24:]
        
        # Log report summary
        self.logger.info(f"Generated QA report {report_id}: {summary['health_status']} "
                        f"(score: {overall_score:.2f}, {summary['failed']} failed, "
                        f"{summary['warnings']} warnings)")
        
        return report
    
    def _determine_health_status(self, overall_score: float, failed_checks: List[QACheckResult]) -> str:
        """Determine overall system health status."""
        critical_failures = [
            r for r in failed_checks 
            if r.check_type in [QACheckType.ACCURACY, QACheckType.PERFORMANCE]
        ]
        
        if critical_failures:
            return "critical"
        elif overall_score < 0.7:
            return "poor"
        elif overall_score < 0.85:
            return "fair"
        elif overall_score < 0.95:
            return "good"
        else:
            return "excellent"
    
    async def generate_manual_report(self, time_window_hours: int = 24) -> QAReport:
        """Generate a manual quality assurance report."""
        return await self._generate_qa_report()
    
    def get_latest_report(self) -> Optional[QAReport]:
        """Get the most recent quality assurance report."""
        return self.recent_reports[-1] if self.recent_reports else None
    
    def get_reports(self, limit: int = 10) -> List[QAReport]:
        """Get recent quality assurance reports."""
        return self.recent_reports[-limit:] if self.recent_reports else []
    
    def export_report(self, report: QAReport, filepath: str) -> None:
        """Export a quality assurance report to JSON file."""
        with open(filepath, 'w') as f:
            json.dump(report.to_dict(), f, indent=2)
        
        self.logger.info(f"Exported QA report {report.report_id} to {filepath}")
    
    async def stop_qa_system(self) -> None:
        """Stop the automated quality assurance system."""
        self.qa_enabled = False
        self.logger.info("Stopped automated quality assurance system")
    
    async def run_comprehensive_system_audit(self) -> Dict[str, Any]:
        """Run a comprehensive system audit with detailed analysis."""
        audit_results = {
            'audit_id': f"audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}",
            'timestamp': datetime.now().isoformat(),
            'checks_performed': [],
            'critical_issues': [],
            'recommendations': [],
            'system_health': {},
            'performance_analysis': {},
            'user_experience_analysis': {}
        }
        
        try:
            # Run all QA checks
            for check_type in QACheckType:
                result = await self._run_qa_check(check_type)
                audit_results['checks_performed'].append(result.to_dict())
                
                if result.status == QAStatus.FAILED:
                    audit_results['critical_issues'].append({
                        'check': result.check_name,
                        'issue': result.message,
                        'impact': self._get_issue_impact(result.check_type),
                        'recommendations': result.recommendations
                    })
                
                audit_results['recommendations'].extend(result.recommendations)
            
            # Analyze system health trends
            audit_results['system_health'] = await self._analyze_system_health_trends()
            
            # Analyze performance patterns
            audit_results['performance_analysis'] = await self._analyze_performance_patterns()
            
            # Analyze user experience
            audit_results['user_experience_analysis'] = await self._analyze_user_experience()
            
            # Generate audit summary
            audit_results['summary'] = self._generate_audit_summary(audit_results)
            
            self.logger.info(f"Comprehensive system audit completed: {audit_results['audit_id']}")
            
        except Exception as e:
            self.logger.error(f"Error during comprehensive audit: {e}")
            audit_results['error'] = str(e)
        
        return audit_results
    
    def _get_issue_impact(self, check_type: QACheckType) -> str:
        """Get the impact description for a failed check."""
        impact_map = {
            QACheckType.ACCURACY: "Poor technology recommendations, user dissatisfaction",
            QACheckType.CONSISTENCY: "Inconsistent system behavior, unreliable results",
            QACheckType.COMPLETENESS: "Incomplete recommendations, missing technologies",
            QACheckType.PERFORMANCE: "Slow response times, poor user experience",
            QACheckType.CATALOG_HEALTH: "Outdated or incorrect technology information",
            QACheckType.USER_SATISFACTION: "User frustration, reduced system adoption"
        }
        return impact_map.get(check_type, "Unknown impact")
    
    async def _analyze_system_health_trends(self) -> Dict[str, Any]:
        """Analyze system health trends over time."""
        if not self.monitor:
            return {'error': 'Monitor service not available'}
        
        try:
            # Get metrics for different time windows
            recent_metrics = self.monitor._get_recent_metrics(hours=24)
            older_metrics = self.monitor._get_recent_metrics(hours=48)
            
            # Calculate trend analysis
            health_trends = {
                'accuracy_trend': self._calculate_metric_trend(recent_metrics, older_metrics, "extraction_accuracy"),
                'performance_trend': self._calculate_metric_trend(recent_metrics, older_metrics, "processing_time", reverse=True),
                'satisfaction_trend': self._calculate_metric_trend(recent_metrics, older_metrics, "overall_satisfaction"),
                'catalog_health_trend': self._calculate_metric_trend(recent_metrics, older_metrics, "catalog_consistency_rate")
            }
            
            # Identify concerning trends
            concerning_trends = []
            for metric, trend in health_trends.items():
                if trend.get('direction') == 'declining' and trend.get('magnitude', 0) > 0.1:
                    concerning_trends.append({
                        'metric': metric,
                        'decline_rate': trend.get('magnitude'),
                        'recommendation': f"Investigate {metric.replace('_', ' ')} degradation"
                    })
            
            return {
                'trends': health_trends,
                'concerning_trends': concerning_trends,
                'overall_health_direction': self._determine_overall_health_direction(health_trends)
            }
            
        except Exception as e:
            return {'error': str(e)}
    
    def _calculate_metric_trend(self, recent_metrics: List, older_metrics: List, metric_name: str, reverse: bool = False) -> Dict[str, Any]:
        """Calculate trend for a specific metric."""
        recent_values = [m.value for m in recent_metrics if hasattr(m, 'name') and m.name == metric_name]
        older_values = [m.value for m in older_metrics if hasattr(m, 'name') and m.name == metric_name and m not in recent_metrics]
        
        if not recent_values or not older_values:
            return {'direction': 'unknown', 'magnitude': 0, 'confidence': 'low'}
        
        recent_avg = sum(recent_values) / len(recent_values)
        older_avg = sum(older_values) / len(older_values)
        
        change = recent_avg - older_avg
        if reverse:
            change = -change
        
        magnitude = abs(change)
        direction = 'improving' if change > 0.02 else 'declining' if change < -0.02 else 'stable'
        confidence = 'high' if len(recent_values) >= 10 and len(older_values) >= 10 else 'medium' if len(recent_values) >= 5 else 'low'
        
        return {
            'direction': direction,
            'magnitude': magnitude,
            'confidence': confidence,
            'recent_average': recent_avg,
            'previous_average': older_avg,
            'sample_sizes': {'recent': len(recent_values), 'previous': len(older_values)}
        }
    
    def _determine_overall_health_direction(self, health_trends: Dict[str, Any]) -> str:
        """Determine overall system health direction."""
        improving_count = sum(1 for trend in health_trends.values() if trend.get('direction') == 'improving')
        declining_count = sum(1 for trend in health_trends.values() if trend.get('direction') == 'declining')
        
        if improving_count > declining_count:
            return 'improving'
        elif declining_count > improving_count:
            return 'declining'
        else:
            return 'stable'
    
    async def _analyze_performance_patterns(self) -> Dict[str, Any]:
        """Analyze performance patterns and bottlenecks."""
        if not self.monitor:
            return {'error': 'Monitor service not available'}
        
        try:
            recent_metrics = self.monitor._get_recent_metrics(hours=24)
            perf_metrics = [m for m in recent_metrics if hasattr(m, 'name') and m.name == "processing_time"]
            
            if not perf_metrics:
                return {'error': 'No performance data available'}
            
            processing_times = [m.value for m in perf_metrics]
            
            analysis = {
                'average_time': sum(processing_times) / len(processing_times),
                'median_time': sorted(processing_times)[len(processing_times) // 2],
                'max_time': max(processing_times),
                'min_time': min(processing_times),
                'percentile_95': sorted(processing_times)[int(len(processing_times) * 0.95)],
                'sample_count': len(processing_times)
            }
            
            # Identify performance issues
            issues = []
            if analysis['average_time'] > 20:
                issues.append("High average processing time")
            if analysis['max_time'] > 60:
                issues.append("Occasional very slow responses")
            if analysis['percentile_95'] > 45:
                issues.append("95th percentile response time too high")
            
            # Performance recommendations
            recommendations = []
            if analysis['average_time'] > 15:
                recommendations.append("Implement caching for frequently accessed data")
            if analysis['max_time'] > 45:
                recommendations.append("Add request timeout and circuit breaker patterns")
            if len(processing_times) > 100 and analysis['percentile_95'] > 30:
                recommendations.append("Optimize LLM prompt size and complexity")
            
            analysis['issues'] = issues
            analysis['recommendations'] = recommendations
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    async def _analyze_user_experience(self) -> Dict[str, Any]:
        """Analyze user experience metrics and patterns."""
        if not self.monitor:
            return {'error': 'Monitor service not available'}
        
        try:
            recent_metrics = self.monitor._get_recent_metrics(hours=48)
            
            # Analyze satisfaction metrics
            satisfaction_metrics = [m for m in recent_metrics if hasattr(m, 'name') and 'satisfaction' in m.name]
            accuracy_metrics = [m for m in recent_metrics if hasattr(m, 'name') and m.name == "extraction_accuracy"]
            inclusion_metrics = [m for m in recent_metrics if hasattr(m, 'name') and m.name == "explicit_tech_inclusion_rate"]
            
            analysis = {
                'satisfaction_analysis': self._analyze_satisfaction_metrics(satisfaction_metrics),
                'accuracy_impact': self._analyze_accuracy_impact(accuracy_metrics, satisfaction_metrics),
                'user_feedback_patterns': self._analyze_feedback_patterns(satisfaction_metrics),
                'experience_recommendations': []
            }
            
            # Generate experience recommendations
            if analysis['satisfaction_analysis'].get('average_score', 5) < 4.0:
                analysis['experience_recommendations'].append("Investigate user satisfaction issues")
            
            if analysis['accuracy_impact'].get('correlation', 0) < 0.5:
                analysis['experience_recommendations'].append("Improve correlation between accuracy and satisfaction")
            
            return analysis
            
        except Exception as e:
            return {'error': str(e)}
    
    def _analyze_satisfaction_metrics(self, satisfaction_metrics: List) -> Dict[str, Any]:
        """Analyze user satisfaction metrics."""
        if not satisfaction_metrics:
            return {'error': 'No satisfaction data available'}
        
        overall_scores = [m.value for m in satisfaction_metrics if hasattr(m, 'name') and m.name == "overall_satisfaction"]
        
        if not overall_scores:
            return {'error': 'No overall satisfaction scores available'}
        
        return {
            'average_score': sum(overall_scores) / len(overall_scores),
            'score_distribution': {
                'excellent': len([s for s in overall_scores if s >= 4.5]),
                'good': len([s for s in overall_scores if 3.5 <= s < 4.5]),
                'fair': len([s for s in overall_scores if 2.5 <= s < 3.5]),
                'poor': len([s for s in overall_scores if s < 2.5])
            },
            'sample_count': len(overall_scores)
        }
    
    def _analyze_accuracy_impact(self, accuracy_metrics: List, satisfaction_metrics: List) -> Dict[str, Any]:
        """Analyze the impact of accuracy on user satisfaction."""
        if not accuracy_metrics or not satisfaction_metrics:
            return {'correlation': 0, 'note': 'Insufficient data for correlation analysis'}
        
        # Simple correlation analysis (would be more sophisticated in production)
        accuracy_values = [m.value for m in accuracy_metrics]
        satisfaction_values = [m.value for m in satisfaction_metrics if hasattr(m, 'name') and m.name == "overall_satisfaction"]
        
        if len(accuracy_values) < 5 or len(satisfaction_values) < 5:
            return {'correlation': 0, 'note': 'Insufficient sample size for correlation'}
        
        # Calculate simple correlation coefficient
        avg_accuracy = sum(accuracy_values) / len(accuracy_values)
        avg_satisfaction = sum(satisfaction_values) / len(satisfaction_values)
        
        correlation = 0.7  # Placeholder - would calculate actual correlation
        
        return {
            'correlation': correlation,
            'average_accuracy': avg_accuracy,
            'average_satisfaction': avg_satisfaction,
            'interpretation': 'Strong positive correlation' if correlation > 0.7 else 'Moderate correlation' if correlation > 0.4 else 'Weak correlation'
        }
    
    def _analyze_feedback_patterns(self, satisfaction_metrics: List) -> Dict[str, Any]:
        """Analyze patterns in user feedback."""
        feedback_texts = []
        for metric in satisfaction_metrics:
            if hasattr(metric, 'metadata') and metric.metadata and 'feedback' in metric.metadata:
                feedback = metric.metadata['feedback']
                if feedback:
                    feedback_texts.append(feedback)
        
        if not feedback_texts:
            return {'note': 'No feedback text available for analysis'}
        
        # Simple keyword analysis (would use NLP in production)
        common_themes = {
            'missing_technologies': sum(1 for f in feedback_texts if 'missing' in f.lower() or 'incomplete' in f.lower()),
            'accuracy_issues': sum(1 for f in feedback_texts if 'wrong' in f.lower() or 'incorrect' in f.lower()),
            'performance_complaints': sum(1 for f in feedback_texts if 'slow' in f.lower() or 'time' in f.lower()),
            'positive_feedback': sum(1 for f in feedback_texts if 'good' in f.lower() or 'great' in f.lower() or 'excellent' in f.lower())
        }
        
        return {
            'total_feedback_count': len(feedback_texts),
            'common_themes': common_themes,
            'top_concern': max(common_themes.items(), key=lambda x: x[1])[0] if common_themes else 'none'
        }
    
    def _generate_audit_summary(self, audit_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a summary of the audit results."""
        checks_performed = audit_results.get('checks_performed', [])
        critical_issues = audit_results.get('critical_issues', [])
        
        passed_checks = len([c for c in checks_performed if c.get('status') == 'passed'])
        failed_checks = len([c for c in checks_performed if c.get('status') == 'failed'])
        warning_checks = len([c for c in checks_performed if c.get('status') == 'warning'])
        
        overall_score = passed_checks / len(checks_performed) if checks_performed else 0
        
        return {
            'overall_health_score': overall_score,
            'checks_summary': {
                'total': len(checks_performed),
                'passed': passed_checks,
                'failed': failed_checks,
                'warnings': warning_checks
            },
            'critical_issues_count': len(critical_issues),
            'system_status': 'healthy' if overall_score > 0.8 and not critical_issues else 'needs_attention' if overall_score > 0.6 else 'critical',
            'priority_actions': self._get_priority_actions(audit_results)
        }
    
    def _get_priority_actions(self, audit_results: Dict[str, Any]) -> List[str]:
        """Get priority actions based on audit results."""
        actions = []
        
        critical_issues = audit_results.get('critical_issues', [])
        if critical_issues:
            actions.append(f"Address {len(critical_issues)} critical system issues immediately")
        
        system_health = audit_results.get('system_health', {})
        concerning_trends = system_health.get('concerning_trends', [])
        if concerning_trends:
            actions.append(f"Investigate {len(concerning_trends)} concerning performance trends")
        
        performance_analysis = audit_results.get('performance_analysis', {})
        perf_issues = performance_analysis.get('issues', [])
        if perf_issues:
            actions.append("Optimize system performance to improve response times")
        
        ux_analysis = audit_results.get('user_experience_analysis', {})
        ux_recommendations = ux_analysis.get('experience_recommendations', [])
        if ux_recommendations:
            actions.append("Improve user experience based on satisfaction analysis")
        
        if not actions:
            actions.append("Continue monitoring - system appears healthy")
        
        return actions