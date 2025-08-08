import json
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

from app.pattern.loader import PatternLoader, PatternValidationError


class TestPatternLoader:
    """Test pattern loading and validation."""
    
    @pytest.fixture
    def valid_pattern(self):
        """Create a valid pattern for testing."""
        return {
            "pattern_id": "PAT-001",
            "name": "Test Pattern",
            "description": "A test pattern for validation",
            "feasibility": "Automatable",
            "pattern_type": ["test", "automation"],
            "input_requirements": ["requirement1", "requirement2"],
            "tech_stack": ["Python", "FastAPI"],
            "confidence_score": 0.85,
            "related_patterns": ["PAT-002"],
            "constraints": {
                "banned_tools": ["tool1"],
                "required_integrations": ["integration1"]
            },
            "domain": "testing",
            "complexity": "Low",
            "estimated_effort": "1-2 weeks"
        }
    
    @pytest.fixture
    def invalid_pattern(self):
        """Create an invalid pattern for testing."""
        return {
            "pattern_id": "INVALID-ID",  # Wrong format
            "name": "Test Pattern",
            "description": "A test pattern",
            "feasibility": "Invalid Feasibility",  # Not in enum
            "pattern_type": ["test"],
            "input_requirements": ["requirement1"],
            "tech_stack": ["Python"],
            "confidence_score": 1.5  # Out of range
        }
    
    @pytest.fixture
    def temp_pattern_dir(self, valid_pattern):
        """Create a temporary directory with pattern files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pattern_path = Path(temp_dir) / "PAT-001.json"
            with open(pattern_path, 'w') as f:
                json.dump(valid_pattern, f)
            yield temp_dir
    
    def test_load_schema(self):
        """Test loading the pattern schema."""
        loader = PatternLoader("dummy_path")
        schema = loader._load_schema()
        
        assert "$schema" in schema
        assert "properties" in schema
        assert "pattern_id" in schema["properties"]
        assert "required" in schema
    
    def test_validate_pattern_success(self, valid_pattern):
        """Test successful pattern validation."""
        loader = PatternLoader("dummy_path")
        
        # Should not raise an exception
        loader._validate_pattern(valid_pattern)
    
    def test_validate_pattern_failure(self, invalid_pattern):
        """Test pattern validation failure."""
        loader = PatternLoader("dummy_path")
        
        with pytest.raises(PatternValidationError):
            loader._validate_pattern(invalid_pattern)
    
    def test_validate_pattern_missing_required_field(self):
        """Test validation failure for missing required field."""
        loader = PatternLoader("dummy_path")
        incomplete_pattern = {
            "pattern_id": "PAT-001",
            "name": "Test Pattern"
            # Missing required fields
        }
        
        with pytest.raises(PatternValidationError):
            loader._validate_pattern(incomplete_pattern)
    
    def test_validate_pattern_invalid_pattern_id(self):
        """Test validation failure for invalid pattern ID format."""
        loader = PatternLoader("dummy_path")
        pattern = {
            "pattern_id": "INVALID",  # Should be PAT-XXX format
            "name": "Test Pattern",
            "description": "Test",
            "feasibility": "Automatable",
            "pattern_type": ["test"],
            "input_requirements": ["req"],
            "tech_stack": ["Python"],
            "confidence_score": 0.8
        }
        
        with pytest.raises(PatternValidationError):
            loader._validate_pattern(pattern)
    
    def test_validate_pattern_invalid_confidence_score(self):
        """Test validation failure for invalid confidence score."""
        loader = PatternLoader("dummy_path")
        pattern = {
            "pattern_id": "PAT-001",
            "name": "Test Pattern",
            "description": "Test",
            "feasibility": "Automatable",
            "pattern_type": ["test"],
            "input_requirements": ["req"],
            "tech_stack": ["Python"],
            "confidence_score": 2.0  # Should be 0-1
        }
        
        with pytest.raises(PatternValidationError):
            loader._validate_pattern(pattern)
    
    def test_load_patterns_success(self, temp_pattern_dir):
        """Test successful pattern loading from directory."""
        loader = PatternLoader(temp_pattern_dir)
        patterns = loader.load_patterns()
        
        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] == "PAT-001"
        assert patterns[0]["name"] == "Test Pattern"
    
    def test_load_patterns_empty_directory(self):
        """Test loading patterns from empty directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            loader = PatternLoader(temp_dir)
            patterns = loader.load_patterns()
            assert len(patterns) == 0
    
    def test_load_patterns_invalid_json(self):
        """Test handling of invalid JSON files."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Create invalid JSON file
            invalid_path = Path(temp_dir) / "PAT-002.json"
            with open(invalid_path, 'w') as f:
                f.write("{ invalid json }")
            
            loader = PatternLoader(temp_dir)
            patterns = loader.load_patterns()
            
            # Should skip invalid files and return empty list
            assert len(patterns) == 0
    
    def test_load_patterns_validation_error(self, invalid_pattern):
        """Test handling of patterns that fail validation."""
        with tempfile.TemporaryDirectory() as temp_dir:
            pattern_path = Path(temp_dir) / "PAT-INVALID.json"
            with open(pattern_path, 'w') as f:
                json.dump(invalid_pattern, f)
            
            loader = PatternLoader(temp_dir)
            patterns = loader.load_patterns()
            
            # Should skip invalid patterns
            assert len(patterns) == 0
    
    def test_get_pattern_by_id(self, temp_pattern_dir):
        """Test retrieving pattern by ID."""
        loader = PatternLoader(temp_pattern_dir)
        
        pattern = loader.get_pattern_by_id("PAT-001")
        assert pattern is not None
        assert pattern["pattern_id"] == "PAT-001"
        
        # Test non-existent pattern
        pattern = loader.get_pattern_by_id("PAT-999")
        assert pattern is None
    
    def test_get_patterns_by_domain(self, temp_pattern_dir):
        """Test retrieving patterns by domain."""
        loader = PatternLoader(temp_pattern_dir)
        
        patterns = loader.get_patterns_by_domain("testing")
        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] == "PAT-001"
        
        # Test non-existent domain
        patterns = loader.get_patterns_by_domain("nonexistent")
        assert len(patterns) == 0
    
    def test_get_patterns_by_type(self, temp_pattern_dir):
        """Test retrieving patterns by type."""
        loader = PatternLoader(temp_pattern_dir)
        
        patterns = loader.get_patterns_by_type("test")
        assert len(patterns) == 1
        assert patterns[0]["pattern_id"] == "PAT-001"
        
        patterns = loader.get_patterns_by_type("automation")
        assert len(patterns) == 1
        
        # Test non-existent type
        patterns = loader.get_patterns_by_type("nonexistent")
        assert len(patterns) == 0