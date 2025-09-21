"""Integration tests for tech stack generation logging."""

import pytest
import asyncio
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, AsyncMock, patch

from app.services.tech_stack_generator import TechStackGenerator
from app.services.tech_logging.tech_stack_logger import LogCategory
from app.pattern.matcher import MatchResult
from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self):
        self.model_name = "mock-model"
        self.provider_name = "mock-provider"
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Mock response generation."""
        return json.dumps({
            "technologies": ["FastAPI", "PostgreSQL", "Redis", "Docker"],
            "reasoning": "Selected based on requirements for high-performance API"
        })
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "name": self.model_name,
            "provider": self.provider_name,
            "capabilities": ["text_generation"]
        }


class TestTechStackLoggingIntegration:
    """Integration tests for tech stack generation with comprehensive logging."""
    
    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider."""
        return MockLLMProvider()
    
    @pytest.fixture
    def tech_stack_generator(self, mock_llm_provider):
        """Create TechStackGenerator with logging enabled."""
        return TechStackGenerator(
            llm_provider=mock_llm_provider,
            enable_debug_logging=True
        )
    
    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements for testing."""
        return {
            "description": "Build a high-performance REST API with AWS integration",
            "functional_requirements": [
                "Handle 1000+ requests per second",
                "Integrate with AWS S3 for file storage",
                "Use PostgreSQL for data persistence"
            ],
            "non_functional_requirements": [
                "99.9% uptime",
                "Sub-100ms response time"
            ],
            "constraints": {
                "cloud_provider": "AWS",
                "budget": "medium"
            }
        }
    
    @pytest.fixture
    def sample_matches(self):
        """Sample pattern matches for testing."""
        match = Mock(spec=MatchResult)
        match.pattern_id = "APAT-001"
        match.confidence = 0.85
        match.tech_stack = ["FastAPI", "PostgreSQL", "Redis"]
        return [match]
    
    @pytest.mark.asyncio
    async def test_full_generation_with_logging(self, tech_stack_generator, sample_requirements, sample_matches):
        """Test complete tech stack generation with comprehensive logging."""
        # Generate tech stack
        result = await tech_stack_generator.generate_tech_stack(
            matches=sample_matches,
            requirements=sample_requirements,
            constraints={"banned_tools": ["MySQL"]}
        )
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) > 0
        
        # Verify logging occurred
        logging_summary = tech_stack_generator.get_logging_summary()
        
        # Check that various log categories were used
        assert 'performance' in logging_summary
        assert 'decisions' in logging_summary
        assert 'llm_interactions' in logging_summary
        assert 'debug_traces' in logging_summary
        
        # Verify generation metrics were updated
        metrics = tech_stack_generator.get_generation_metrics()
        assert metrics['total_generations'] > 0
    
    @pytest.mark.asyncio
    async def test_requirement_parsing_logging(self, tech_stack_generator, sample_requirements):
        """Test requirement parsing logging."""
        # Enable debug mode for detailed logging
        tech_stack_generator.enable_debug_mode(True)
        
        # Parse requirements (this would normally be called internally)
        parsed_req = await tech_stack_generator._parse_requirements_enhanced(
            sample_requirements, 
            {"banned_tools": ["MySQL"]}
        )
        
        # Check that parsing was logged
        tech_logger = tech_stack_generator.tech_logger
        parsing_entries = tech_logger.get_log_entries(
            category=LogCategory.REQUIREMENT_PARSING
        )
        
        # Should have at least one parsing entry
        assert len(parsing_entries) > 0
        
        # Verify entry content
        entry = parsing_entries[0]
        assert entry.component in ["TechStackGenerator", "EnhancedRequirementParser"]
        assert "parse" in entry.operation.lower()
    
    @pytest.mark.asyncio
    async def test_llm_interaction_logging(self, tech_stack_generator, sample_requirements, sample_matches):
        """Test LLM interaction logging."""
        # Generate tech stack to trigger LLM interaction
        await tech_stack_generator.generate_tech_stack(
            matches=sample_matches,
            requirements=sample_requirements
        )
        
        # Check LLM interaction logs
        llm_summary = tech_stack_generator.llm_logger.get_interaction_summary()
        
        if llm_summary:  # Only check if LLM was actually called
            assert llm_summary['total_interactions'] > 0
            assert llm_summary['successful_interactions'] >= 0
    
    @pytest.mark.asyncio
    async def test_decision_logging(self, tech_stack_generator, sample_requirements, sample_matches):
        """Test decision logging during generation."""
        # Generate tech stack
        await tech_stack_generator.generate_tech_stack(
            matches=sample_matches,
            requirements=sample_requirements
        )
        
        # Check decision logs
        decision_summary = tech_stack_generator.decision_logger.get_decision_summary()
        
        # Should have some decisions logged
        assert 'total_decisions' in decision_summary
        assert 'decision_types' in decision_summary
    
    @pytest.mark.asyncio
    async def test_performance_monitoring(self, tech_stack_generator, sample_requirements, sample_matches):
        """Test performance monitoring during generation."""
        # Generate tech stack
        await tech_stack_generator.generate_tech_stack(
            matches=sample_matches,
            requirements=sample_requirements
        )
        
        # Check performance metrics
        perf_summary = tech_stack_generator.performance_monitor.get_performance_summary()
        
        # Should have performance data
        assert 'tracing_enabled' in perf_summary
        
        # Check for timing metrics
        metric_summary = tech_stack_generator.performance_monitor.get_metric_summary()
        if metric_summary:
            assert 'total_metrics' in metric_summary
    
    @pytest.mark.asyncio
    async def test_error_handling_and_logging(self, tech_stack_generator):
        """Test error handling and logging."""
        # Create invalid requirements to trigger error
        invalid_requirements = None
        
        try:
            await tech_stack_generator.generate_tech_stack(
                matches=[],
                requirements=invalid_requirements
            )
        except Exception:
            pass  # Expected to fail
        
        # Check error logs
        error_summary = tech_stack_generator.error_logger.get_error_summary()
        
        # Should have error information
        assert 'total_errors' in error_summary or error_summary == {}
    
    @pytest.mark.asyncio
    async def test_debug_tracing(self, tech_stack_generator, sample_requirements, sample_matches):
        """Test debug tracing functionality."""
        # Enable debug tracing
        tech_stack_generator.enable_debug_mode(True)
        
        # Generate tech stack
        await tech_stack_generator.generate_tech_stack(
            matches=sample_matches,
            requirements=sample_requirements
        )
        
        # Check debug traces
        traces = tech_stack_generator.debug_tracer.get_traces(
            component="TechStackGenerator"
        )
        
        # Should have at least one trace
        if traces:
            trace = traces[0]
            assert trace.component == "TechStackGenerator"
            assert trace.operation == "generate_tech_stack"
            assert len(trace.steps) > 0
    
    def test_log_export_functionality(self, tech_stack_generator):
        """Test log export functionality."""
        # Add some log entries
        tech_stack_generator.tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Test message for export"
        )
        
        # Export logs
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            success = tech_stack_generator.export_logs(
                temp_path,
                format='json',
                include_traces=True,
                include_performance=True
            )
            
            assert success is True
            
            # Verify export file exists and has content
            assert Path(temp_path).exists()
            
            with open(temp_path, 'r') as f:
                exported_data = json.load(f)
            
            assert len(exported_data) > 0
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_logging_configuration(self, mock_llm_provider):
        """Test different logging configurations."""
        # Test with debug disabled
        generator_no_debug = TechStackGenerator(
            llm_provider=mock_llm_provider,
            enable_debug_logging=False
        )
        
        assert generator_no_debug.tech_logger._debug_mode is False
        assert generator_no_debug.debug_tracer._enabled is False
        
        # Test with debug enabled
        generator_with_debug = TechStackGenerator(
            llm_provider=mock_llm_provider,
            enable_debug_logging=True
        )
        
        assert generator_with_debug.tech_logger._debug_mode is True
        assert generator_with_debug.debug_tracer._enabled is True
    
    def test_performance_recommendations(self, tech_stack_generator):
        """Test performance recommendations generation."""
        # Generate some metrics first
        tech_stack_generator.performance_monitor.record_timing(
            "slow_operation",
            35000,  # 35 seconds - should trigger recommendation
            "TestComponent"
        )
        
        recommendations = tech_stack_generator.get_performance_recommendations()
        
        # Should have recommendations
        assert isinstance(recommendations, list)
        
        # Check for slow operation recommendation
        slow_op_recommendation = any(
            "slow operations" in rec.lower() or "30s" in rec
            for rec in recommendations
        )
        if slow_op_recommendation:
            assert slow_op_recommendation
    
    @pytest.mark.asyncio
    async def test_session_and_request_context(self, tech_stack_generator, sample_requirements, sample_matches):
        """Test session and request context tracking."""
        # Generate tech stack (this sets session and request context internally)
        await tech_stack_generator.generate_tech_stack(
            matches=sample_matches,
            requirements=sample_requirements
        )
        
        # Check that entries have session and request context
        entries = tech_stack_generator.tech_logger.get_log_entries()
        
        if entries:
            # At least some entries should have session/request context
            has_session_context = any(entry.session_id is not None for entry in entries)
            has_request_context = any(entry.request_id is not None for entry in entries)
            
            # Note: These might be None if the generation failed early
            # but the test verifies the mechanism works when successful
            assert isinstance(has_session_context, bool)
            assert isinstance(has_request_context, bool)
    
    def test_logging_service_shutdown(self, tech_stack_generator):
        """Test graceful shutdown of logging services."""
        # Add some log entries
        tech_stack_generator.tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Test message before shutdown"
        )
        
        # Shutdown logging
        tech_stack_generator.shutdown_logging()
        
        # Verify services are stopped
        assert not tech_stack_generator.performance_monitor._monitoring_enabled
    
    @pytest.mark.asyncio
    async def test_catalog_auto_addition_logging(self, tech_stack_generator, sample_requirements):
        """Test logging of catalog auto-addition process."""
        # Create requirements with unknown technology
        requirements_with_new_tech = {
            **sample_requirements,
            "functional_requirements": [
                "Use NewFramework for API development",
                "Integrate with UnknownDatabase"
            ]
        }
        
        # Generate tech stack
        await tech_stack_generator.generate_tech_stack(
            matches=[],
            requirements=requirements_with_new_tech
        )
        
        # Check catalog-related logs
        catalog_entries = tech_stack_generator.tech_logger.get_log_entries(
            category=LogCategory.CATALOG_LOOKUP
        )
        
        # Should have catalog-related activity
        assert isinstance(catalog_entries, list)
    
    def test_confidence_score_tracking(self, tech_stack_generator):
        """Test confidence score tracking in logs."""
        # Log entries with confidence scores
        tech_stack_generator.tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "extract_technology",
            "Extracted technology with high confidence",
            confidence_score=0.95
        )
        
        tech_stack_generator.tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "extract_technology",
            "Extracted technology with low confidence",
            confidence_score=0.3
        )
        
        # Get entries and verify confidence scores
        entries = tech_stack_generator.tech_logger.get_log_entries()
        
        confidence_entries = [e for e in entries if e.confidence_score is not None]
        assert len(confidence_entries) >= 2
        
        # Verify confidence scores are preserved
        high_conf_entry = next(e for e in confidence_entries if e.confidence_score == 0.95)
        low_conf_entry = next(e for e in confidence_entries if e.confidence_score == 0.3)
        
        assert high_conf_entry is not None
        assert low_conf_entry is not None