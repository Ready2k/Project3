"""Tests for enhanced pattern creator with duplicate validation and error handling."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from pathlib import Path
import json

from app.services.pattern_creator import PatternCreator


class TestEnhancedPatternCreator:
    """Test enhanced pattern creator functionality."""
    
    @pytest.fixture
    def pattern_creator(self):
        """Create pattern creator for testing."""
        return PatternCreator(
            pattern_library_path=Path("data/patterns"),
            llm_provider=AsyncMock()
        )
    
    @pytest.fixture
    def sample_requirements(self):
        """Create sample requirements."""
        return {
            "description": "Build a user authentication system with OAuth2 and JWT tokens",
            "tech_stack": ["OAuth2", "JWT", "Redis", "PostgreSQL"],
            "domain": "authentication",
            "pattern_types": ["authentication_workflow"],
            "compliance": ["GDPR"],
            "session_id": "test-session"
        }

    def test_generate_pattern_id_unique_validation(self, pattern_creator):
        """Test that pattern ID generation validates uniqueness."""
        # Mock existing pattern files
        existing_files = [
            MagicMock(name="PAT-001.json", stem="PAT-001"),
            MagicMock(name="PAT-002.json", stem="PAT-002"),
            MagicMock(name="PAT-003.json", stem="PAT-003")
        ]
        
        # Mock loaded patterns
        mock_patterns = [
            {"pattern_id": "PAT-001"},
            {"pattern_id": "PAT-002"},
            {"pattern_id": "PAT-003"}
        ]
        
        with patch('pathlib.Path.glob', return_value=existing_files), \
             patch('app.pattern.loader.PatternLoader') as mock_loader:
            
            mock_loader.return_value.load_patterns.return_value = mock_patterns
            
            pattern_id = pattern_creator._generate_pattern_id()
            
            # Should generate PAT-004 (next available)
            assert pattern_id == "PAT-004"

    def test_generate_pattern_id_handles_gaps(self, pattern_creator):
        """Test that pattern ID generation handles gaps in numbering."""
        # Mock existing pattern files with gaps
        existing_files = [
            MagicMock(name="PAT-001.json", stem="PAT-001"),
            MagicMock(name="PAT-003.json", stem="PAT-003"),  # Gap at PAT-002
            MagicMock(name="PAT-005.json", stem="PAT-005")   # Gap at PAT-004
        ]
        
        mock_patterns = [
            {"pattern_id": "PAT-001"},
            {"pattern_id": "PAT-003"},
            {"pattern_id": "PAT-005"}
        ]
        
        with patch('pathlib.Path.glob', return_value=existing_files), \
             patch('app.pattern.loader.PatternLoader') as mock_loader:
            
            mock_loader.return_value.load_patterns.return_value = mock_patterns
            
            pattern_id = pattern_creator._generate_pattern_id()
            
            # Should generate PAT-006 (next after highest)
            assert pattern_id == "PAT-006"

    def test_generate_pattern_id_fallback_to_uuid(self, pattern_creator):
        """Test that pattern ID generation falls back to UUID on error."""
        # Mock glob to raise an exception
        with patch('pathlib.Path.glob', side_effect=Exception("File system error")):
            
            pattern_id = pattern_creator._generate_pattern_id()
            
            # Should generate UUID-based fallback
            assert pattern_id.startswith("PAT-")
            assert len(pattern_id) == 12  # PAT- + 8 character UUID

    def test_generate_pattern_id_max_attempts_exceeded(self, pattern_creator):
        """Test pattern ID generation when max attempts are exceeded."""
        # Create a scenario where many IDs already exist
        existing_files = [MagicMock(name=f"PAT-{i:03d}.json", stem=f"PAT-{i:03d}") for i in range(1, 200)]
        mock_patterns = [{"pattern_id": f"PAT-{i:03d}"} for i in range(1, 200)]
        
        with patch('pathlib.Path.glob', return_value=existing_files), \
             patch('app.pattern.loader.PatternLoader') as mock_loader:
            
            mock_loader.return_value.load_patterns.return_value = mock_patterns
            
            # Should still find an available ID
            pattern_id = pattern_creator._generate_pattern_id()
            assert pattern_id == "PAT-200"

    @pytest.mark.asyncio
    async def test_create_pattern_input_validation(self, pattern_creator):
        """Test input validation in pattern creation."""
        # Test empty requirements
        with pytest.raises(ValueError, match="Requirements dictionary cannot be empty"):
            await pattern_creator.create_pattern_from_requirements({}, "test-session")
        
        # Test empty session ID
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            await pattern_creator.create_pattern_from_requirements({"description": "test"}, "")

    @pytest.mark.asyncio
    async def test_create_pattern_id_generation_failure(self, pattern_creator, sample_requirements):
        """Test pattern creation when ID generation fails."""
        with patch.object(pattern_creator, '_generate_pattern_id', side_effect=Exception("ID generation failed")):
            
            with pytest.raises(RuntimeError, match="Pattern ID generation failed"):
                await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")

    @pytest.mark.asyncio
    async def test_create_pattern_llm_analysis_failure_fallback(self, pattern_creator, sample_requirements):
        """Test pattern creation with LLM analysis failure and fallback."""
        # Mock LLM analysis to fail
        pattern_creator.llm_provider.generate.side_effect = Exception("LLM failed")
        
        # Mock successful pattern saving
        with patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")), \
             patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"):
            
            result = await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")
            
            # Should succeed with fallback analysis
            assert result["pattern_id"] == "PAT-001"
            assert "Authentication" in result["name"]  # Should contain domain name
            assert "Automation" in result["name"]  # Should contain automation type

    @pytest.mark.asyncio
    async def test_create_pattern_security_validation_failure(self, pattern_creator, sample_requirements):
        """Test pattern creation when security validation fails."""
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(False, "Security validation failed")):
            
            with pytest.raises(ValueError, match="Pattern creation blocked: Security validation failed"):
                await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")

    @pytest.mark.asyncio
    async def test_create_pattern_save_operation_failure(self, pattern_creator, sample_requirements):
        """Test pattern creation when save operation fails unexpectedly."""
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_save_pattern_securely', side_effect=Exception("Unexpected save error")):
            
            with pytest.raises(RuntimeError, match="Pattern save operation failed"):
                await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")

    @pytest.mark.asyncio
    async def test_create_pattern_comprehensive_error_handling(self, pattern_creator, sample_requirements):
        """Test comprehensive error handling throughout pattern creation."""
        # Mock various components to succeed
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value={}), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")
            
            # Should succeed with fallback values
            assert result["pattern_id"] == "PAT-001"
            assert result["feasibility"] in ["Automatable", "Partially Automatable", "Not Automatable"]
            assert isinstance(result["tech_stack"], list)

    def test_create_fallback_analysis(self, pattern_creator):
        """Test creation of fallback analysis when LLM fails."""
        requirements = {
            "description": "Build a user authentication system with OAuth2",
            "domain": "security",
            "integrations": ["database", "api"]
        }
        
        analysis = pattern_creator._create_fallback_analysis(requirements)
        
        assert "Security" in analysis["pattern_name"]
        assert "Automation" in analysis["pattern_name"]
        assert analysis["feasibility"] == "Automatable"
        assert "general_automation" in analysis["pattern_types"]
        assert "Python" in analysis["tech_stack"]
        assert analysis["confidence_score"] == 0.7

    def test_create_fallback_analysis_error_handling(self, pattern_creator):
        """Test fallback analysis creation with error handling."""
        # Pass invalid requirements to trigger error handling
        requirements = None
        
        analysis = pattern_creator._create_fallback_analysis(requirements)
        
        # Should return minimal fallback
        assert analysis["pattern_name"] == "General Automation Pattern"
        assert analysis["feasibility"] == "Automatable"
        assert analysis["confidence_score"] == 0.6

    @pytest.mark.asyncio
    async def test_create_pattern_empty_description_handling(self, pattern_creator):
        """Test pattern creation with empty description."""
        requirements = {
            "description": "",  # Empty description
            "domain": "test"
        }
        
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(requirements, "test-session")
            
            # Should handle empty description gracefully
            assert result["pattern_id"] == "PAT-001"
            assert "automation" in result["description"].lower()

    @pytest.mark.asyncio
    async def test_create_pattern_invalid_feasibility_handling(self, pattern_creator, sample_requirements):
        """Test pattern creation with invalid feasibility from analysis."""
        # Mock analysis to return invalid feasibility
        invalid_analysis = {
            "feasibility": "InvalidFeasibility",
            "pattern_name": "Test Pattern"
        }
        
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value=invalid_analysis), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")
            
            # Should default to valid feasibility
            assert result["feasibility"] == "Automatable"

    @pytest.mark.asyncio
    async def test_create_pattern_invalid_confidence_handling(self, pattern_creator, sample_requirements):
        """Test pattern creation with invalid confidence score."""
        # Mock analysis to return invalid confidence
        invalid_analysis = {
            "confidence_score": 1.5,  # Invalid (> 1.0)
            "pattern_name": "Test Pattern"
        }
        
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value=invalid_analysis), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")
            
            # Should default to valid confidence
            assert result["confidence_score"] == 0.7

    @pytest.mark.asyncio
    async def test_create_pattern_tech_stack_generation_failure(self, pattern_creator, sample_requirements):
        """Test pattern creation when tech stack generation fails."""
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value={}), \
             patch.object(pattern_creator, '_generate_intelligent_tech_stack', side_effect=Exception("Tech stack failed")), \
             patch.object(pattern_creator, '_generate_fallback_tech_stack', return_value=["Python", "FastAPI"]), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")
            
            # Should use fallback tech stack
            assert result["tech_stack"] == ["Python", "FastAPI"]

    @pytest.mark.asyncio
    async def test_create_pattern_constraint_extraction_error(self, pattern_creator, sample_requirements):
        """Test pattern creation when constraint extraction fails."""
        # Mock analysis to return invalid constraint data
        invalid_analysis = {
            "banned_tools_suggestions": "not_a_list",  # Invalid type
            "required_integrations_suggestions": None,
            "compliance_considerations": 123
        }
        
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value=invalid_analysis), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(sample_requirements, "test-session")
            
            # Should handle invalid constraint data gracefully
            assert isinstance(result["constraints"]["banned_tools"], list)
            assert isinstance(result["constraints"]["required_integrations"], list)
            assert isinstance(result["constraints"]["compliance_requirements"], list)

    def test_pattern_id_parsing_error_handling(self, pattern_creator):
        """Test pattern ID generation with malformed existing files."""
        # Mock files with malformed names
        malformed_files = [
            MagicMock(name="invalid.json", stem="invalid"),
            MagicMock(name="PAT-abc.json", stem="PAT-abc"),  # Non-numeric
            MagicMock(name="PAT-001.json", stem="PAT-001"),  # Valid
            MagicMock(name="NOT-PAT-002.json", stem="NOT-PAT-002")  # Wrong format
        ]
        
        with patch('pathlib.Path.glob', return_value=malformed_files), \
             patch('app.pattern.loader.PatternLoader') as mock_loader:
            
            mock_loader.return_value.load_patterns.return_value = [{"pattern_id": "PAT-001"}]
            
            pattern_id = pattern_creator._generate_pattern_id()
            
            # Should handle malformed files and generate next valid ID
            assert pattern_id == "PAT-002"