"""
Simple unit tests for monitoring data validation.

Tests the monitoring data validation functionality without complex dependencies.
"""

import pytest
import uuid
from datetime import datetime
from unittest.mock import Mock, patch

from app.services.tech_stack_generator import TechStackGenerator


class TestMonitoringDataValidation:
    """Test monitoring data validation methods."""
    
    @pytest.fixture
    def tech_stack_generator(self):
        """Create a minimal tech stack generator for testing."""
        with patch('app.utils.imports.require_service') as mock_require:
            mock_require.side_effect = Exception("Service not available")
            return TechStackGenerator(enable_debug_logging=False)
    
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
    
    def test_calculate_explicit_inclusion_rate_perfect(self, tech_stack_generator):
        """Test explicit inclusion rate calculation with perfect inclusion."""
        # Mock parsed requirements
        parsed_req = Mock()
        explicit_tech = Mock()
        explicit_tech.name = "FastAPI"
        explicit_tech.canonical_name = "FastAPI"
        parsed_req.explicit_technologies = [explicit_tech]
        
        tech_stack = ["FastAPI", "PostgreSQL", "Redis", "Docker"]
        
        rate = tech_stack_generator._calculate_explicit_inclusion_rate(
            parsed_req, tech_stack
        )
        
        assert rate == 1.0
    
    def test_calculate_explicit_inclusion_rate_partial(self, tech_stack_generator):
        """Test explicit inclusion rate calculation with partial inclusion."""
        # Mock parsed requirements with multiple explicit technologies
        parsed_req = Mock()
        explicit_techs = []
        for name in ["FastAPI", "PostgreSQL", "Redis"]:
            tech = Mock()
            tech.name = name
            tech.canonical_name = name
            explicit_techs.append(tech)
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
    
    def test_calculate_explicit_inclusion_rate_zero_inclusion(self, tech_stack_generator):
        """Test explicit inclusion rate calculation with zero inclusion."""
        # Mock parsed requirements
        parsed_req = Mock()
        explicit_tech = Mock()
        explicit_tech.name = "MongoDB"
        explicit_tech.canonical_name = "MongoDB"
        parsed_req.explicit_technologies = [explicit_tech]
        
        tech_stack = ["FastAPI", "PostgreSQL", "Redis"]  # No MongoDB
        
        rate = tech_stack_generator._calculate_explicit_inclusion_rate(
            parsed_req, tech_stack
        )
        
        assert rate == 0.0


if __name__ == "__main__":
    pytest.main([__file__])