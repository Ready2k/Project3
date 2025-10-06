"""
Monitoring Integration Service

Integrates monitoring, quality assurance, and alerting systems
with the tech stack generation workflow.
"""

from datetime import datetime
from typing import Dict, List, Optional, Any

from app.core.service import ConfigurableService
from app.utils.imports import require_service, optional_service
from app.monitoring.tech_stack_monitor import TechStackMonitor
from app.monitoring.quality_assurance import QualityAssuranceSystem


class MonitoringIntegrationService(ConfigurableService):
    """
    Service that integrates monitoring and quality assurance
    into the tech stack generation workflow.
    
    Provides seamless monitoring, alerting, and quality tracking
    for all tech stack generation operations.
    """
    
    def __init__(self, config: Dict[str, Any] = None):
        super().__init__(config or {}, 'MonitoringIntegration')
        try:
            self.logger = require_service('logger', context='MonitoringIntegration')
        except Exception:
            # Fallback logger for testing/standalone use
            import logging
            self.logger = logging.getLogger('MonitoringIntegration')
        
        # Initialize monitoring components
        self.monitor = TechStackMonitor()
        self.qa_system = QualityAssuranceSystem()
        
        # Start monitoring by default for production use
        self.integration_active = True
    
    async def _do_initialize(self) -> None:
        """Initialize the monitoring integration service."""
        await self.start_monitoring_integration()
    
    async def _do_shutdown(self) -> None:
        """Shutdown the monitoring integration service."""
        await self.stop_monitoring_integration()
    
    async def start_monitoring_integration(self) -> None:
        """Start the integrated monitoring system."""
        try:
            self.logger.info("Starting monitoring integration service")
            
            # Start monitoring components
            await self.monitor.start_monitoring()
            await self.qa_system.start_qa_system()
            
            self.integration_active = True
            
            # Register monitoring hooks
            self._register_monitoring_hooks()
            
            self.logger.info("Monitoring integration service started successfully")
            
        except Exception as e:
            self.logger.error(f"Failed to start monitoring integration: {e}")
            raise
    
    async def stop_monitoring_integration(self) -> None:
        """Stop the integrated monitoring system."""
        try:
            self.logger.info("Stopping monitoring integration service")
            
            self.integration_active = False
            
            # Stop monitoring components
            await self.monitor.stop_monitoring()
            await self.qa_system.stop_qa_system()
            
            self.logger.info("Monitoring integration service stopped")
            
        except Exception as e:
            self.logger.error(f"Error stopping monitoring integration: {e}")
    
    def _register_monitoring_hooks(self) -> None:
        """Register monitoring hooks with other services."""
        try:
            # Register with service registry for automatic integration
            registry = optional_service('service_registry', context='MonitoringIntegration')
            if registry:
                registry.register_service('tech_stack_monitor', self.monitor)
                registry.register_service('quality_assurance_system', self.qa_system)
                registry.register_service('monitoring_integration', self)
                
                self.logger.info("Registered monitoring services with service registry")
            
        except Exception as e:
            self.logger.warning(f"Could not register monitoring hooks: {e}")
    
    async def monitor_tech_stack_generation(
        self,
        session_id: str,
        requirements: Dict[str, Any],
        extracted_technologies: List[str],
        expected_technologies: List[str],
        explicit_technologies: List[str],
        generated_stack: List[str],
        processing_time: float,
        llm_calls: int = 1,
        catalog_additions: int = 0
    ) -> None:
        """
        Monitor a complete tech stack generation process.
        
        Args:
            session_id: Unique session identifier
            requirements: Original requirements
            extracted_technologies: Technologies extracted from requirements
            expected_technologies: Technologies that should have been extracted
            explicit_technologies: Explicitly mentioned technologies
            generated_stack: Final generated technology stack
            processing_time: Total processing time in seconds
            llm_calls: Number of LLM API calls made
            catalog_additions: Number of technologies added to catalog
        """
        if not self.integration_active:
            return
        
        try:
            # Calculate accuracy metrics
            extracted_count = len(extracted_technologies)
            expected_count = len(expected_technologies)
            explicit_tech_included = len([tech for tech in explicit_technologies if tech in generated_stack])
            explicit_tech_total = len(explicit_technologies)
            
            # Record extraction accuracy
            self.monitor.record_extraction_accuracy(
                session_id=session_id,
                extracted_count=extracted_count,
                expected_count=expected_count,
                explicit_tech_included=explicit_tech_included,
                explicit_tech_total=explicit_tech_total,
                processing_time=processing_time
            )
            
            # Log detailed monitoring data
            self.logger.info(f"Tech stack generation monitored for session {session_id}", extra={
                'session_id': session_id,
                'extraction_accuracy': extracted_count / max(expected_count, 1),
                'explicit_inclusion_rate': explicit_tech_included / max(explicit_tech_total, 1),
                'processing_time': processing_time,
                'llm_calls': llm_calls,
                'catalog_additions': catalog_additions,
                'generated_stack_size': len(generated_stack)
            })
            
        except Exception as e:
            self.logger.error(f"Error monitoring tech stack generation: {e}")
    
    async def monitor_catalog_operation(
        self,
        operation_type: str,
        technologies_processed: int,
        successful_operations: int,
        failed_operations: int,
        processing_time: float
    ) -> None:
        """
        Monitor catalog management operations.
        
        Args:
            operation_type: Type of operation (add, update, validate, etc.)
            technologies_processed: Number of technologies processed
            successful_operations: Number of successful operations
            failed_operations: Number of failed operations
            processing_time: Processing time in seconds
        """
        if not self.integration_active:
            return
        
        try:
            success_rate = successful_operations / max(technologies_processed, 1)
            
            self.logger.info(f"Catalog operation monitored: {operation_type}", extra={
                'operation_type': operation_type,
                'technologies_processed': technologies_processed,
                'success_rate': success_rate,
                'processing_time': processing_time
            })
            
        except Exception as e:
            self.logger.error(f"Error monitoring catalog operation: {e}")
    
    async def record_user_feedback(
        self,
        session_id: str,
        relevance_score: float,
        accuracy_score: float,
        completeness_score: float,
        feedback_text: Optional[str] = None
    ) -> None:
        """
        Record user satisfaction feedback.
        
        Args:
            session_id: Session identifier
            relevance_score: Relevance rating (1-5)
            accuracy_score: Accuracy rating (1-5)
            completeness_score: Completeness rating (1-5)
            feedback_text: Optional text feedback
        """
        if not self.integration_active:
            return
        
        try:
            self.monitor.record_user_satisfaction(
                session_id=session_id,
                relevance_score=relevance_score,
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                feedback=feedback_text
            )
            
            self.logger.info(f"User feedback recorded for session {session_id}", extra={
                'session_id': session_id,
                'relevance_score': relevance_score,
                'accuracy_score': accuracy_score,
                'completeness_score': completeness_score,
                'has_feedback_text': bool(feedback_text)
            })
            
        except Exception as e:
            self.logger.error(f"Error recording user feedback: {e}")
    
    async def update_catalog_health_metrics(
        self,
        total_technologies: int,
        missing_technologies: int,
        inconsistent_entries: int,
        pending_review: int
    ) -> None:
        """
        Update catalog health metrics.
        
        Args:
            total_technologies: Total number of technologies in catalog
            missing_technologies: Number of missing/requested technologies
            inconsistent_entries: Number of inconsistent catalog entries
            pending_review: Number of entries pending review
        """
        if not self.integration_active:
            return
        
        try:
            self.monitor.record_catalog_metrics(
                total_technologies=total_technologies,
                missing_technologies=missing_technologies,
                inconsistent_entries=inconsistent_entries,
                pending_review=pending_review
            )
            
            self.logger.debug("Catalog health metrics updated", extra={
                'total_technologies': total_technologies,
                'missing_technologies': missing_technologies,
                'inconsistent_entries': inconsistent_entries,
                'pending_review': pending_review
            })
            
        except Exception as e:
            self.logger.error(f"Error updating catalog health metrics: {e}")
    
    def get_monitoring_status(self) -> Dict[str, Any]:
        """Get current monitoring system status."""
        return {
            'integration_active': self.integration_active,
            'monitor_active': self.monitor.monitoring_active if self.monitor else False,
            'qa_system_active': self.qa_system.qa_enabled if self.qa_system else False,
            'services_registered': {
                'monitor': bool(self.monitor),
                'qa_system': bool(self.qa_system)
            }
        }
    
    def get_quality_dashboard_data(self) -> Dict[str, Any]:
        """Get comprehensive quality dashboard data."""
        if not self.monitor:
            return {}
        
        return self.monitor.get_quality_dashboard_data()
    
    async def generate_quality_report(self) -> Optional[Dict[str, Any]]:
        """Generate a comprehensive quality report."""
        if not self.qa_system:
            return None
        
        try:
            report = await self.qa_system.generate_manual_report()
            return report.to_dict() if report else None
            
        except Exception as e:
            self.logger.error(f"Error generating quality report: {e}")
            return None
    
    def export_monitoring_data(self, filepath: str, hours: int = 24) -> bool:
        """
        Export monitoring data to file.
        
        Args:
            filepath: Output file path
            hours: Number of hours of data to export
            
        Returns:
            True if export successful, False otherwise
        """
        if not self.monitor:
            return False
        
        try:
            self.monitor.export_metrics(filepath, hours)
            return True
            
        except Exception as e:
            self.logger.error(f"Error exporting monitoring data: {e}")
            return False
    
    async def run_quality_check(self, check_type: Optional[str] = None) -> Dict[str, Any]:
        """
        Run manual quality assurance check.
        
        Args:
            check_type: Specific check type to run (optional)
            
        Returns:
            Quality check results
        """
        if not self.qa_system:
            return {'error': 'QA system not available'}
        
        try:
            if check_type:
                # Run specific check type
                from app.monitoring.quality_assurance import QACheckType
                qa_check_type = QACheckType(check_type)
                result = await self.qa_system._run_qa_check(qa_check_type)
                return result.to_dict()
            else:
                # Run full quality report
                report = await self.qa_system.generate_manual_report()
                return report.to_dict() if report else {'error': 'Failed to generate report'}
                
        except Exception as e:
            self.logger.error(f"Error running quality check: {e}")
            return {'error': str(e)}
    
    def get_performance_recommendations(self) -> List[Dict[str, Any]]:
        """Get current performance optimization recommendations."""
        if not self.monitor:
            return []
        
        return [rec.to_dict() for rec in self.monitor.recommendations]
    
    def get_recent_alerts(self, hours: int = 24) -> List[Dict[str, Any]]:
        """Get recent alerts from the monitoring system."""
        if not self.monitor:
            return []
        
        try:
            from datetime import timedelta as td
            cutoff = datetime.now() - td(hours=hours)
            recent_alerts = [alert for alert in self.monitor.alerts if alert.timestamp >= cutoff]
            return [alert.to_dict() for alert in recent_alerts]
        except Exception as e:
            self.logger.error(f"Error getting recent alerts: {e}")
            return []
    
    async def run_comprehensive_system_audit(self) -> Dict[str, Any]:
        """Run a comprehensive system audit."""
        if not self.qa_system:
            return {'error': 'QA system not available'}
        
        try:
            audit_results = await self.qa_system.run_comprehensive_system_audit()
            
            # Add monitoring system health data
            if self.monitor:
                audit_results['monitoring_health'] = self.monitor.get_system_health_score()
                audit_results['alert_status'] = self.monitor.get_alert_escalation_status()
            
            self.logger.info(f"Comprehensive system audit completed: {audit_results.get('audit_id', 'unknown')}")
            return audit_results
            
        except Exception as e:
            self.logger.error(f"Error running comprehensive audit: {e}")
            return {'error': str(e)}
    
    def get_real_time_system_status(self) -> Dict[str, Any]:
        """Get real-time system status for live monitoring."""
        status = {
            'timestamp': datetime.now().isoformat(),
            'integration_active': self.integration_active,
            'services_status': {
                'monitor': bool(self.monitor and getattr(self.monitor, 'monitoring_active', False)),
                'qa_system': bool(self.qa_system and getattr(self.qa_system, 'qa_enabled', False))
            }
        }
        
        if self.monitor:
            # Get latest metrics
            recent_metrics = self.monitor._get_recent_metrics(hours=1)
            if recent_metrics:
                latest_metrics = {}
                for metric in recent_metrics[-10:]:  # Last 10 metrics
                    latest_metrics[metric.name] = {
                        'value': metric.value,
                        'timestamp': metric.timestamp.isoformat()
                    }
                status['latest_metrics'] = latest_metrics
            
            # Get system health
            status['system_health'] = self.monitor.get_system_health_score()
            
            # Get alert status
            status['alert_status'] = self.monitor.get_alert_escalation_status()
        
        return status
    
    async def trigger_performance_optimization(self) -> Dict[str, Any]:
        """Trigger performance optimization based on current metrics."""
        if not self.monitor:
            return {'error': 'Monitor service not available'}
        
        try:
            # Force recommendation generation
            await self.monitor._analyze_and_recommend()
            
            # Get current recommendations
            recommendations = self.get_performance_recommendations()
            
            # Get system health for context
            health_score = self.monitor.get_system_health_score()
            
            optimization_result = {
                'timestamp': datetime.now().isoformat(),
                'recommendations_generated': len(recommendations),
                'system_health': health_score,
                'optimization_actions': []
            }
            
            # Suggest immediate actions based on health score
            if health_score['overall_score'] < 0.7:
                optimization_result['optimization_actions'].append("Immediate attention required - system health below acceptable threshold")
            
            if health_score['component_scores'].get('performance', 1.0) < 0.6:
                optimization_result['optimization_actions'].append("Performance optimization critical - implement caching and optimize LLM calls")
            
            if health_score['component_scores'].get('accuracy', 1.0) < 0.8:
                optimization_result['optimization_actions'].append("Accuracy improvement needed - review extraction algorithms and catalog completeness")
            
            self.logger.info(f"Performance optimization triggered: {len(recommendations)} recommendations generated")
            return optimization_result
            
        except Exception as e:
            self.logger.error(f"Error triggering performance optimization: {e}")
            return {'error': str(e)}
    
    async def schedule_maintenance_window(self, duration_hours: int = 2) -> Dict[str, Any]:
        """Schedule a maintenance window for system optimization."""
        from datetime import timedelta as td
        maintenance_start = datetime.now()
        maintenance_end = maintenance_start + td(hours=duration_hours)
        
        maintenance_plan = {
            'maintenance_id': f"maint_{maintenance_start.strftime('%Y%m%d_%H%M%S')}",
            'start_time': maintenance_start.isoformat(),
            'end_time': maintenance_end.isoformat(),
            'duration_hours': duration_hours,
            'planned_activities': [],
            'status': 'scheduled'
        }
        
        try:
            # Run comprehensive audit to determine maintenance needs
            audit_results = await self.run_comprehensive_system_audit()
            
            # Plan maintenance activities based on audit
            if audit_results.get('critical_issues'):
                maintenance_plan['planned_activities'].append("Address critical system issues")
            
            performance_analysis = audit_results.get('performance_analysis', {})
            if performance_analysis.get('issues'):
                maintenance_plan['planned_activities'].append("Performance optimization and tuning")
            
            system_health = audit_results.get('system_health', {})
            if system_health.get('concerning_trends'):
                maintenance_plan['planned_activities'].append("Investigate and resolve concerning trends")
            
            # Add routine maintenance activities
            maintenance_plan['planned_activities'].extend([
                "Catalog consistency check and repair",
                "Clear old metrics and logs",
                "Update monitoring thresholds based on recent patterns",
                "Generate comprehensive system report"
            ])
            
            self.logger.info(f"Maintenance window scheduled: {maintenance_plan['maintenance_id']}")
            return maintenance_plan
            
        except Exception as e:
            self.logger.error(f"Error scheduling maintenance window: {e}")
            maintenance_plan['error'] = str(e)
            return maintenance_plan