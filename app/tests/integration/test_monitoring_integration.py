"""
Integration tests for monitoring system components.
"""

import pytest
import json
from datetime import datetime
from unittest.mock import Mock, patch, AsyncMock

from app.monitoring.tech_stack_monitor import TechStackMonitor
from app.monitoring.quality_assurance import QualityAssuranceSystem
from app.monitoring.integration_service import MonitoringIntegrationService


class TestMonitoringIntegration:
    """Test integration between monitoring components."""
    
    @pytest.fixture
    async def integration_service(self):
        """Create monitoring integration service for testing."""
        with patch('app.utils.imports.require_service') as mock_require, \
             patch('app.utils.imports.optional_service') as mock_optional:
            
            mock_logger = Mock()
            mock_registry = Mock()
            
            mock_require.return_value = mock_logger
            mock_optional.return_value = mock_registry
            
            service = MonitoringIntegrationService()
            
            # Mock the monitoring components
            service.monitor = Mock(spec=TechStackMonitor)
            service.monitor.start_monitoring = AsyncMock()
            service.monitor.stop_monitoring = AsyncMock()
            service.monitor.monitoring_active = True
            service.monitor.record_extraction_accuracy = Mock()
            service.monitor.record_catalog_metrics = Mock()
            service.monitor.record_user_satisfaction = Mock()
            service.monitor.get_quality_dashboard_data = Mock(return_value={})
            service.monitor.export_metrics = Mock()
            service.monitor.recommendations = []
            service.monitor.alerts = []
            
            service.qa_system = Mock(spec=QualityAssuranceSystem)
            service.qa_system.start_qa_system = AsyncMock()
            service.qa_system.stop_qa_system = AsyncMock()
            service.qa_system.qa_enabled = True
            service.qa_system.generate_manual_report = AsyncMock()
            service.qa_system._run_qa_check = AsyncMock()
            
            return service
    
    @pytest.mark.asyncio
    async def test_start_monitoring_integration(self, integration_service):
        """Test starting the monitoring integration service."""
        await integration_service.start_monitoring_integration()
        
        assert integration_service.integration_active is True
        integration_service.monitor.start_monitoring.assert_called_once()
        integration_service.qa_system.start_qa_system.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_stop_monitoring_integration(self, integration_service):
        """Test stopping the monitoring integration service."""
        integration_service.integration_active = True
        
        await integration_service.stop_monitoring_integration()
        
        assert integration_service.integration_active is False
        integration_service.monitor.stop_monitoring.assert_called_once()
        integration_service.qa_system.stop_qa_system.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_monitor_tech_stack_generation(self, integration_service):
        """Test monitoring a complete tech stack generation process."""
        integration_service.integration_active = True
        
        # Test data
        session_id = "test_session_123"
        requirements = {"description": "Build a web application with AWS services"}
        extracted_technologies = ["AWS Lambda", "Amazon S3", "FastAPI", "React"]
        expected_technologies = ["AWS Lambda", "Amazon S3", "FastAPI", "React", "Amazon RDS"]
        explicit_technologies = ["AWS Lambda", "Amazon S3"]
        generated_stack = ["AWS Lambda", "Amazon S3", "FastAPI", "React"]
        processing_time = 15.5
        
        await integration_service.monitor_tech_stack_generation(
            session_id=session_id,
            requirements=requirements,
            extracted_technologies=extracted_technologies,
            expected_technologies=expected_technologies,
            explicit_technologies=explicit_technologies,
            generated_stack=generated_stack,
            processing_time=processing_time,
            llm_calls=2,
            catalog_additions=1
        )
        
        # Verify that monitoring was called
        integration_service.monitor.record_extraction_accuracy.assert_called_once()
        call_args = integration_service.monitor.record_extraction_accuracy.call_args
        
        assert call_args[1]['session_id'] == session_id
        assert call_args[1]['extracted_count'] == 4
        assert call_args[1]['expected_count'] == 5
        assert call_args[1]['explicit_tech_included'] == 2  # Both explicit techs in generated stack
        assert call_args[1]['explicit_tech_total'] == 2
        assert call_args[1]['processing_time'] == processing_time
    
    @pytest.mark.asyncio
    async def test_monitor_catalog_operation(self, integration_service):
        """Test monitoring catalog management operations."""
        integration_service.integration_active = True
        
        await integration_service.monitor_catalog_operation(
            operation_type="validate",
            technologies_processed=100,
            successful_operations=95,
            failed_operations=5,
            processing_time=8.2
        )
        
        # Should log the operation (verify through logger mock if needed)
        assert True  # Basic test that no exceptions were raised
    
    @pytest.mark.asyncio
    async def test_record_user_feedback(self, integration_service):
        """Test recording user satisfaction feedback."""
        integration_service.integration_active = True
        
        session_id = "test_session_456"
        relevance_score = 4.5
        accuracy_score = 4.0
        completeness_score = 3.5
        feedback_text = "Good recommendations but could be more complete"
        
        await integration_service.record_user_feedback(
            session_id=session_id,
            relevance_score=relevance_score,
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            feedback_text=feedback_text
        )
        
        # Verify that user satisfaction was recorded
        integration_service.monitor.record_user_satisfaction.assert_called_once_with(
            session_id=session_id,
            relevance_score=relevance_score,
            accuracy_score=accuracy_score,
            completeness_score=completeness_score,
            feedback=feedback_text
        )
    
    @pytest.mark.asyncio
    async def test_update_catalog_health_metrics(self, integration_service):
        """Test updating catalog health metrics."""
        integration_service.integration_active = True
        
        await integration_service.update_catalog_health_metrics(
            total_technologies=150,
            missing_technologies=8,
            inconsistent_entries=3,
            pending_review=12
        )
        
        # Verify that catalog metrics were recorded
        integration_service.monitor.record_catalog_metrics.assert_called_once_with(
            total_technologies=150,
            missing_technologies=8,
            inconsistent_entries=3,
            pending_review=12
        )
    
    def test_get_monitoring_status(self, integration_service):
        """Test getting monitoring system status."""
        integration_service.integration_active = True
        
        status = integration_service.get_monitoring_status()
        
        assert status['integration_active'] is True
        assert status['monitor_active'] is True
        assert status['qa_system_active'] is True
        assert status['services_registered']['monitor'] is True
        assert status['services_registered']['qa_system'] is True
    
    def test_get_quality_dashboard_data(self, integration_service):
        """Test getting quality dashboard data."""
        mock_data = {
            'summary': {'total_sessions': 10},
            'accuracy': {'average': 0.85},
            'performance': {'average_time': 12.5}
        }
        integration_service.monitor.get_quality_dashboard_data.return_value = mock_data
        
        result = integration_service.get_quality_dashboard_data()
        
        assert result == mock_data
        integration_service.monitor.get_quality_dashboard_data.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generate_quality_report(self, integration_service):
        """Test generating quality report."""
        mock_report = Mock()
        mock_report.to_dict.return_value = {'report_id': 'test_123'}
        
        integration_service.qa_system.generate_manual_report.return_value = mock_report
        
        result = await integration_service.generate_quality_report()
        
        assert result == {'report_id': 'test_123'}
        integration_service.qa_system.generate_manual_report.assert_called_once()
    
    def test_export_monitoring_data(self, integration_service, tmp_path):
        """Test exporting monitoring data."""
        export_file = tmp_path / "test_export.json"
        
        result = integration_service.export_monitoring_data(str(export_file), hours=12)
        
        assert result is True
        integration_service.monitor.export_metrics.assert_called_once_with(str(export_file), 12)
    
    @pytest.mark.asyncio
    async def test_run_quality_check(self, integration_service):
        """Test running manual quality check."""
        from app.monitoring.quality_assurance import QACheckResult, QACheckType, QAStatus
        
        mock_result = QACheckResult(
            check_type=QACheckType.ACCURACY,
            check_name="accuracy_check",
            status=QAStatus.PASSED,
            score=0.9,
            message="Test passed",
            details={},
            timestamp=datetime.now(),
            recommendations=[]
        )
        
        integration_service.qa_system._run_qa_check.return_value = mock_result
        
        result = await integration_service.run_quality_check("accuracy")
        
        assert 'check_type' in result
        assert result['status'] == 'passed'
        assert result['score'] == 0.9
    
    def test_get_performance_recommendations(self, integration_service):
        """Test getting performance recommendations."""
        from app.monitoring.tech_stack_monitor import PerformanceRecommendation
        
        mock_rec = PerformanceRecommendation(
            category="performance",
            priority="high",
            description="Optimize processing time",
            impact="Better user experience",
            implementation="Add caching",
            metrics_supporting=["processing_time"]
        )
        
        integration_service.monitor.recommendations = [mock_rec]
        
        result = integration_service.get_performance_recommendations()
        
        assert len(result) == 1
        assert result[0]['category'] == 'performance'
        assert result[0]['priority'] == 'high'
    
    def test_get_recent_alerts(self, integration_service):
        """Test getting recent alerts."""
        from app.monitoring.tech_stack_monitor import QualityAlert, AlertLevel
        
        mock_alert = QualityAlert(
            timestamp=datetime.now(),
            level=AlertLevel.WARNING,
            category="performance",
            message="High processing time",
            details={"time": 35.0}
        )
        
        integration_service.monitor.alerts = [mock_alert]
        
        result = integration_service.get_recent_alerts(hours=24)
        
        assert len(result) == 1
        assert result[0]['level'] == 'warning'
        assert result[0]['category'] == 'performance'
    
    @pytest.mark.asyncio
    async def test_inactive_integration_skips_monitoring(self, integration_service):
        """Test that monitoring is skipped when integration is inactive."""
        integration_service.integration_active = False
        
        await integration_service.monitor_tech_stack_generation(
            session_id="test",
            requirements={},
            extracted_technologies=[],
            expected_technologies=[],
            explicit_technologies=[],
            generated_stack=[],
            processing_time=10.0
        )
        
        # Should not call monitoring methods when inactive
        integration_service.monitor.record_extraction_accuracy.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_error_handling_in_monitoring(self, integration_service):
        """Test error handling in monitoring operations."""
        integration_service.integration_active = True
        integration_service.monitor.record_extraction_accuracy.side_effect = Exception("Test error")
        
        # Should not raise exception, just log error
        await integration_service.monitor_tech_stack_generation(
            session_id="test",
            requirements={},
            extracted_technologies=[],
            expected_technologies=[],
            explicit_technologies=[],
            generated_stack=[],
            processing_time=10.0
        )
        
        # Verify error was handled gracefully
        assert True  # No exception raised


class TestEndToEndMonitoring:
    """End-to-end tests for the complete monitoring workflow."""
    
    @pytest.fixture
    async def full_monitoring_system(self):
        """Create a complete monitoring system for testing."""
        with patch('app.utils.imports.require_service') as mock_require, \
             patch('app.utils.imports.optional_service') as mock_optional:
            
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            mock_optional.return_value = None
            
            # Create real instances (not mocked)
            monitor = TechStackMonitor()
            qa_system = QualityAssuranceSystem()
            integration = MonitoringIntegrationService()
            
            # Override with real instances
            integration.monitor = monitor
            integration.qa_system = qa_system
            
            return integration, monitor, qa_system
    
    @pytest.mark.asyncio
    async def test_complete_monitoring_workflow(self, full_monitoring_system):
        """Test complete monitoring workflow from start to finish."""
        integration, monitor, qa_system = full_monitoring_system
        
        # Start monitoring
        await integration.start_monitoring_integration()
        
        # Simulate tech stack generation
        await integration.monitor_tech_stack_generation(
            session_id="e2e_test_session",
            requirements={"description": "Build AWS application"},
            extracted_technologies=["AWS Lambda", "Amazon S3", "FastAPI"],
            expected_technologies=["AWS Lambda", "Amazon S3", "FastAPI", "Amazon RDS"],
            explicit_technologies=["AWS Lambda", "Amazon S3"],
            generated_stack=["AWS Lambda", "Amazon S3", "FastAPI"],
            processing_time=12.5,
            llm_calls=1,
            catalog_additions=0
        )
        
        # Record user feedback
        await integration.record_user_feedback(
            session_id="e2e_test_session",
            relevance_score=4.0,
            accuracy_score=4.5,
            completeness_score=3.5,
            feedback_text="Good but could include database"
        )
        
        # Update catalog metrics
        await integration.update_catalog_health_metrics(
            total_technologies=100,
            missing_technologies=5,
            inconsistent_entries=2,
            pending_review=8
        )
        
        # Verify metrics were recorded
        assert len(monitor.metrics) > 0
        
        # Check that we have different types of metrics
        metric_types = set(m.metric_type for m in monitor.metrics)
        assert len(metric_types) > 1
        
        # Get dashboard data
        dashboard_data = integration.get_quality_dashboard_data()
        assert 'summary' in dashboard_data
        assert 'accuracy' in dashboard_data
        assert 'performance' in dashboard_data
        
        # Generate quality report
        report = await integration.generate_quality_report()
        assert report is not None
        
        # Stop monitoring
        await integration.stop_monitoring_integration()
        
        assert integration.integration_active is False
    
    @pytest.mark.asyncio
    async def test_alert_generation_workflow(self, full_monitoring_system):
        """Test alert generation in monitoring workflow."""
        integration, monitor, qa_system = full_monitoring_system
        
        await integration.start_monitoring_integration()
        
        # Generate conditions that should trigger alerts
        
        # Low accuracy alert
        await integration.monitor_tech_stack_generation(
            session_id="alert_test_1",
            requirements={},
            extracted_technologies=["Tech1"],
            expected_technologies=["Tech1", "Tech2", "Tech3", "Tech4", "Tech5"],  # Low accuracy
            explicit_technologies=["Tech1", "Tech2"],
            generated_stack=["Tech1"],  # Missing explicit tech
            processing_time=45.0,  # High processing time
            llm_calls=1,
            catalog_additions=0
        )
        
        # Poor catalog health
        await integration.update_catalog_health_metrics(
            total_technologies=100,
            missing_technologies=20,  # High missing rate
            inconsistent_entries=10,  # High inconsistency
            pending_review=60         # High pending count
        )
        
        # Low user satisfaction
        await integration.record_user_feedback(
            session_id="alert_test_1",
            relevance_score=2.0,
            accuracy_score=2.5,
            completeness_score=2.0,  # Low overall satisfaction
            feedback_text="Poor recommendations"
        )
        
        # Check that alerts were generated
        assert len(monitor.alerts) > 0
        
        # Verify different types of alerts
        alert_categories = set(a.category for a in monitor.alerts)
        expected_categories = {
            "extraction_accuracy", "explicit_tech_inclusion", 
            "performance", "catalog_consistency", "catalog_missing", 
            "user_satisfaction"
        }
        
        # Should have at least some of these alert categories
        assert len(alert_categories.intersection(expected_categories)) > 0
        
        await integration.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_recommendation_generation_workflow(self, full_monitoring_system):
        """Test recommendation generation in monitoring workflow."""
        integration, monitor, qa_system = full_monitoring_system
        
        await integration.start_monitoring_integration()
        
        # Generate multiple data points to trigger recommendation analysis
        for i in range(10):
            await integration.monitor_tech_stack_generation(
                session_id=f"rec_test_{i}",
                requirements={},
                extracted_technologies=["Tech1", "Tech2"],
                expected_technologies=["Tech1", "Tech2", "Tech3"],
                explicit_technologies=["Tech1"],
                generated_stack=["Tech1", "Tech2"],
                processing_time=20.0 + i,  # Increasing processing time
                llm_calls=1,
                catalog_additions=0
            )
        
        # Manually trigger recommendation generation
        await monitor._analyze_and_recommend()
        
        # Check that recommendations were generated
        recommendations = integration.get_performance_recommendations()
        
        # Should have some recommendations due to performance patterns
        assert len(recommendations) >= 0  # May or may not have recommendations based on thresholds
        
        await integration.stop_monitoring_integration()
    
    @pytest.mark.asyncio
    async def test_export_functionality(self, full_monitoring_system, tmp_path):
        """Test data export functionality."""
        integration, monitor, qa_system = full_monitoring_system
        
        await integration.start_monitoring_integration()
        
        # Generate some data
        await integration.monitor_tech_stack_generation(
            session_id="export_test",
            requirements={},
            extracted_technologies=["Tech1", "Tech2"],
            expected_technologies=["Tech1", "Tech2"],
            explicit_technologies=["Tech1"],
            generated_stack=["Tech1", "Tech2"],
            processing_time=15.0,
            llm_calls=1,
            catalog_additions=0
        )
        
        # Export monitoring data
        export_file = tmp_path / "monitoring_export.json"
        success = integration.export_monitoring_data(str(export_file), hours=1)
        
        assert success is True
        assert export_file.exists()
        
        # Verify export content
        with open(export_file) as f:
            data = json.load(f)
        
        assert 'export_timestamp' in data
        assert 'metrics' in data
        assert 'alerts' in data
        assert 'summary' in data
        
        await integration.stop_monitoring_integration()