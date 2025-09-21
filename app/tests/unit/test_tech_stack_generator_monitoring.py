"""
Unit tests for tech stack generator monitoring integration components.

Tests individual monitoring methods and data validation.
"""

import pytest
import uuid
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime
from typing import Dict, List, Any

from app.services.tech_stack_generator import TechStackGenerator
from app.services.monitoring_integration_service import MonitoringSession
from app.services.requirement_parsing.base import ParsedRequirements, TechContext, ExplicitTech, ContextClues
from app.pattern.matcher import MatchResult


class TestTechStackGeneratorMonitoring:
    """Test tech stack generator monitoring methods."""
    
    @pytest.fixture
    def tech_stack_generator(self):
        """Create tech stack generator for testing."""
        return TechStackGenerator(enable_debug_logging=True)
    
    @pytest.fixture
    def sample_parsed_requirements(self):
        """Create sample parsed requirements."""
        explicit_tech = ExplicitTech(
            name="FastAPI",
            canonical_name="FastAPI",
            confidence=0.9,
            context="REST API framework"
        )
        
        context_clues = ContextClues(
            domains=["web", "api"],
            cloud_providers=["AWS"],
            integration_patterns=["REST", "microservices"],
            programming_languages=["Python"]
        )
        
        return ParsedRequirements(
            explicit_technologies=[explicit_tech],
            context_clues=context_clues,
            integration_patterns=["REST API", "microservices"],
            domain_context=Mock(),
            confidence_score=0.85
        )
    
    @pytest.fixture
    def sample_tech_context(self):
        """Create sample technology context."""
        context = Mock(spec=TechContext)
        context.explicit_technologies = {"FastAPI": 0.9, "PostgreSQL": 0.8}
        context.contextual_technologies = {"Redis": 0.7, "Docker": 0.6}
        context.ecosystem_preference = "AWS"
        context.domain_context = Mock()
        context.banned_tools = set()
        context.priority_weights = {}
        return context
    
    def test_validate_monitoring_data_valid(self, tech_stack_generator):
        """Test monitoring data validation with valid data."""
        session_id = str(uuid.uuid4())
        valid_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'test_operation',
            'duration_ms': 150.5,
            'confidence_scores': {'FastAPI': 0.9, 'PostgreSQL': 0.8},
            'extracted_technologies': ['FastAPI', 'PostgreSQL', 'Redis'],
            'success': True
        }
        
        result = tech_stack_generator._validate_monitoring_data(
            session_id, valid_data, 'test_operation'
        )
        
        assert result is True
    
    def test_validate_monitoring_data_invalid_duration(self, tech_stack_generator):
        """Test monitoring data validation with invalid duration."""
        session_id = str(uuid.uuid4())
        invalid_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'test_operation',
            'duration_ms': -100.0,  # Invalid negative duration
            'success': True
        }
        
        result = tech_stack_generator._validate_monitoring_data(
            session_id, invalid_data, 'test_operation'
        )
        
        assert result is False
    
    def test_validate_monitoring_data_invalid_confidence_scores(self, tech_stack_generator):
        """Test monitoring data validation with invalid confidence scores."""
        session_id = str(uuid.uuid4())
        invalid_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'test_operation',
            'confidence_scores': {'FastAPI': 1.5, 'PostgreSQL': -0.1},  # Invalid scores
            'success': True
        }
        
        result = tech_stack_generator._validate_monitoring_data(
            session_id, invalid_data, 'test_operation'
        )
        
        assert result is False
    
    def test_validate_monitoring_data_invalid_technology_list(self, tech_stack_generator):
        """Test monitoring data validation with invalid technology list."""
        session_id = str(uuid.uuid4())
        invalid_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'test_operation',
            'extracted_technologies': ['FastAPI', '', None, 123],  # Invalid entries
            'success': True
        }
        
        result = tech_stack_generator._validate_monitoring_data(
            session_id, invalid_data, 'test_operation'
        )
        
        assert result is False
    
    def test_validate_monitoring_data_missing_error_message(self, tech_stack_generator):
        """Test monitoring data validation with missing error message for failed operation."""
        session_id = str(uuid.uuid4())
        invalid_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'test_operation',
            'success': False  # Failed operation but no error_message
        }
        
        result = tech_stack_generator._validate_monitoring_data(
            session_id, invalid_data, 'test_operation'
        )
        
        assert result is False
    
    def test_validate_monitoring_data_invalid_session_id(self, tech_stack_generator):
        """Test monitoring data validation with invalid session ID."""
        invalid_session_ids = [None, "", 123, []]
        
        valid_data = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'test_operation',
            'success': True
        }
        
        for invalid_session_id in invalid_session_ids:
            result = tech_stack_generator._validate_monitoring_data(
                invalid_session_id, valid_data, 'test_operation'
            )
            assert result is False, f"Should reject invalid session_id: {invalid_session_id}"
    
    def test_validate_monitoring_data_unreasonable_duration(self, tech_stack_generator):
        """Test monitoring data validation with unreasonably high duration."""
        session_id = str(uuid.uuid4())
        data_with_high_duration = {
            'timestamp': datetime.now().isoformat(),
            'operation': 'test_operation',
            'duration_ms': 400000.0,  # > 5 minutes, should trigger warning
            'success': True
        }
        
        # Should still be valid but log a warning
        result = tech_stack_generator._validate_monitoring_data(
            session_id, data_with_high_duration, 'test_operation'
        )
        
        assert result is True  # Valid but with warning
    
    def test_validate_monitoring_data_exception_handling(self, tech_stack_generator):
        """Test monitoring data validation exception handling."""
        session_id = str(uuid.uuid4())
        
        # Create data that will cause an exception during validation
        problematic_data = Mock()
        problematic_data.__contains__ = Mock(side_effect=Exception("Test exception"))
        
        result = tech_stack_generator._validate_monitoring_data(
            session_id, problematic_data, 'test_operation'
        )
        
        assert result is False
    
    @pytest.mark.asyncio
    async def test_validate_and_enforce_explicit_inclusion_no_explicit_techs(
        self, tech_stack_generator, sample_tech_context
    ):
        """Test validation when no explicit technologies are present."""
        tech_stack = ["FastAPI", "PostgreSQL", "Redis"]
        
        # Create parsed requirements with no explicit technologies
        parsed_req = Mock()
        parsed_req.explicit_technologies = []
        
        # Mock monitoring service
        tech_stack_generator._current_session_id = "test-session"
        tech_stack_generator._monitoring_service = Mock()
        tech_stack_generator._monitoring_service.track_validation_step = AsyncMock()
        
        result = await tech_stack_generator._validate_and_enforce_explicit_inclusion(
            tech_stack, parsed_req, sample_tech_context
        )
        
        assert result == tech_stack
        # Should track validation step even with no explicit technologies
        tech_stack_generator._monitoring_service.track_validation_step.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_validate_and_enforce_explicit_inclusion_sufficient_rate(
        self, tech_stack_generator, sample_parsed_requirements, sample_tech_context
    ):
        """Test validation when explicit inclusion rate is sufficient."""
        tech_stack = ["FastAPI", "PostgreSQL", "Redis", "Docker"]
        
        # Mock monitoring service
        tech_stack_generator._current_session_id = "test-session"
        tech_stack_generator._monitoring_service = Mock()
        tech_stack_generator._monitoring_service.track_validation_step = AsyncMock()
        
        result = await tech_stack_generator._validate_and_enforce_explicit_inclusion(
            tech_stack, sample_parsed_requirements, sample_tech_context
        )
        
        assert result == tech_stack
        tech_stack_generator._monitoring_service.track_validation_step.assert_called_once()
        
        # Check validation results
        call_args = tech_stack_generator._monitoring_service.track_validation_step.call_args
        validation_results = call_args[1]['validation_results']
        assert validation_results['enforcement_applied'] is False
    
    @pytest.mark.asyncio
    async def test_validate_and_enforce_explicit_inclusion_insufficient_rate(
        self, tech_stack_generator, sample_parsed_requirements, sample_tech_context
    ):
        """Test validation when explicit inclusion rate is insufficient."""
        tech_stack = ["Redis", "Docker", "Nginx"]  # No explicit technologies included
        
        # Mock catalog manager
        tech_stack_generator.catalog_manager = Mock()
        tech_stack_generator.catalog_manager.lookup_technology = Mock(return_value=True)
        tech_stack_generator.auto_update_catalog = True
        
        # Mock monitoring service
        tech_stack_generator._current_session_id = "test-session"
        tech_stack_generator._monitoring_service = Mock()
        tech_stack_generator._monitoring_service.track_validation_step = AsyncMock()
        
        result = await tech_stack_generator._validate_and_enforce_explicit_inclusion(
            tech_stack, sample_parsed_requirements, sample_tech_context
        )
        
        # Should add explicit technology
        assert "FastAPI" in result
        assert len(result) > len(tech_stack)
        
        tech_stack_generator._monitoring_service.track_validation_step.assert_called_once()
        
        # Check validation results
        call_args = tech_stack_generator._monitoring_service.track_validation_step.call_args
        validation_results = call_args[1]['validation_results']
        assert validation_results['enforcement_applied'] is True
        assert validation_results['technologies_added'] > 0
    
    @pytest.mark.asyncio
    async def test_auto_add_missing_technologies_disabled(
        self, tech_stack_generator, sample_tech_context
    ):
        """Test auto-add when disabled."""
        tech_stack = ["NewTech1", "NewTech2"]
        tech_stack_generator.auto_update_catalog = False
        
        # Should return without doing anything
        await tech_stack_generator._auto_add_missing_technologies(tech_stack, sample_tech_context)
        
        # No assertions needed - just verify no exceptions
    
    @pytest.mark.asyncio
    async def test_auto_add_missing_technologies_with_monitoring(
        self, tech_stack_generator, sample_tech_context
    ):
        """Test auto-add with monitoring integration."""
        tech_stack = ["NewTech1", "ExistingTech", "NewTech2"]
        tech_stack_generator.auto_update_catalog = True
        
        # Mock catalog manager
        tech_stack_generator.catalog_manager = Mock()
        tech_stack_generator.catalog_manager.lookup_technology = Mock(side_effect=lambda x: x == "ExistingTech")
        tech_stack_generator.catalog_manager.auto_add_technology = Mock(return_value=Mock(id="new-tech-id"))
        
        # Mock monitoring service
        tech_stack_generator._current_session_id = "test-session"
        tech_stack_generator._monitoring_service = Mock()
        tech_stack_generator._monitoring_service.track_validation_step = AsyncMock()
        
        await tech_stack_generator._auto_add_missing_technologies(tech_stack, sample_tech_context)
        
        # Should add new technologies
        assert tech_stack_generator.catalog_manager.auto_add_technology.call_count == 2
        
        # Should track validation step
        tech_stack_generator._monitoring_service.track_validation_step.assert_called_once()
        
        # Check validation results
        call_args = tech_stack_generator._monitoring_service.track_validation_step.call_args
        validation_results = call_args[1]['validation_results']
        assert validation_results['technologies_added'] == 2
        assert validation_results['technologies_failed'] == 0
    
    @pytest.mark.asyncio
    async def test_auto_add_missing_technologies_with_failures(
        self, tech_stack_generator, sample_tech_context
    ):
        """Test auto-add with some failures."""
        tech_stack = ["NewTech1", "NewTech2"]
        tech_stack_generator.auto_update_catalog = True
        
        # Mock catalog manager with failures
        tech_stack_generator.catalog_manager = Mock()
        tech_stack_generator.catalog_manager.lookup_technology = Mock(return_value=False)
        tech_stack_generator.catalog_manager.auto_add_technology = Mock(
            side_effect=[Mock(id="tech1-id"), Exception("Add failed")]
        )
        
        # Mock monitoring service
        tech_stack_generator._current_session_id = "test-session"
        tech_stack_generator._monitoring_service = Mock()
        tech_stack_generator._monitoring_service.track_validation_step = AsyncMock()
        
        await tech_stack_generator._auto_add_missing_technologies(tech_stack, sample_tech_context)
        
        # Should track validation step with mixed results
        tech_stack_generator._monitoring_service.track_validation_step.assert_called_once()
        
        # Check validation results
        call_args = tech_stack_generator._monitoring_service.track_validation_step.call_args
        validation_results = call_args[1]['validation_results']
        assert validation_results['technologies_added'] == 1
        assert validation_results['technologies_failed'] == 1
        assert validation_results['success_rate'] == 0.5
    
    def test_calculate_explicit_inclusion_rate(self, tech_stack_generator, sample_parsed_requirements):
        """Test explicit inclusion rate calculation."""
        tech_stack = ["FastAPI", "PostgreSQL", "Redis", "Docker"]
        
        rate = tech_stack_generator._calculate_explicit_inclusion_rate(
            sample_parsed_requirements, tech_stack
        )
        
        # Should be 1.0 since FastAPI is in both explicit technologies and tech stack
        assert rate == 1.0
    
    def test_calculate_explicit_inclusion_rate_partial(self, tech_stack_generator):
        """Test explicit inclusion rate calculation with partial inclusion."""
        # Create parsed requirements with multiple explicit technologies
        explicit_techs = [
            ExplicitTech(name="FastAPI", canonical_name="FastAPI", confidence=0.9, context=""),
            ExplicitTech(name="PostgreSQL", canonical_name="PostgreSQL", confidence=0.8, context=""),
            ExplicitTech(name="Redis", canonical_name="Redis", confidence=0.7, context="")
        ]
        
        parsed_req = Mock()
        parsed_req.explicit_technologies = explicit_techs
        
        tech_stack = ["FastAPI", "Docker", "Nginx"]  # Only 1 out of 3 explicit technologies
        
        rate = tech_stack_generator._calculate_explicit_inclusion_rate(parsed_req, tech_stack)
        
        # Should be 1/3 ≈ 0.33
        assert abs(rate - (1/3)) < 0.01
    
    def test_calculate_explicit_inclusion_rate_no_explicit(self, tech_stack_generator):
        """Test explicit inclusion rate calculation with no explicit technologies."""
        parsed_req = Mock()
        parsed_req.explicit_technologies = []
        
        tech_stack = ["FastAPI", "PostgreSQL", "Redis"]
        
        rate = tech_stack_generator._calculate_explicit_inclusion_rate(parsed_req, tech_stack)
        
        # Should be 1.0 when no explicit technologies exist
        assert rate == 1.0


if __name__ == "__main__":
    pytest.main([__file__])