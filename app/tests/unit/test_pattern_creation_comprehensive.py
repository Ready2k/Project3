"""Comprehensive tests for pattern creation decision logic, validation, and audit logging."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.services.recommendation import RecommendationService
from app.services.pattern_creator import PatternCreator
from app.pattern.matcher import MatchResult


class TestPatternCreationComprehensive:
    """Comprehensive tests for pattern creation functionality."""
    
    @pytest.fixture
    def service(self):
        """Create recommendation service for testing."""
        return RecommendationService(
            confidence_threshold=0.6,
            pattern_library_path=Path("data/patterns"),
            llm_provider=AsyncMock()
        )
    
    @pytest.fixture
    def pattern_creator(self):
        """Create pattern creator for testing."""
        return PatternCreator(
            pattern_library_path=Path("data/patterns"),
            llm_provider=AsyncMock()
        )
    
    @pytest.fixture
    def sample_match(self):
        """Create a sample match result."""
        return MatchResult(
            pattern_id="PAT-001",
            pattern_name="Authentication System",
            feasibility="Automatable",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            confidence=0.8,
            tag_score=0.7,
            vector_score=0.6,
            blended_score=0.65,
            rationale="Test match"
        )
    
    @pytest.fixture
    def novel_tech_requirements(self):
        """Create requirements with novel technologies."""
        return {
            "description": "Build a blockchain-based identity verification system with machine learning fraud detection",
            "tech_stack": ["Ethereum", "Solidity", "TensorFlow", "Kubernetes", "GraphQL"],
            "domain": "fintech",
            "pattern_types": ["blockchain_verification"],
            "compliance": ["KYC", "AML"],
            "session_id": "test-session-novel"
        }
    
    @pytest.fixture
    def similar_requirements(self):
        """Create requirements similar to existing patterns."""
        return {
            "description": "Build a user authentication system with password reset functionality",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            "domain": "authentication",
            "pattern_types": ["authentication_workflow"],
            "compliance": ["GDPR"],
            "session_id": "test-session-similar"
        }

    # Pattern Creation Decision Logic Tests
    
    @pytest.mark.asyncio
    async def test_create_pattern_novel_technologies(self, service, sample_match, novel_tech_requirements):
        """Test that new pattern is created when requirements contain novel technologies."""
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.8), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.6):
            
            result = await service._should_create_new_pattern([sample_match], novel_tech_requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_enhance_pattern_conceptual_similarity(self, service, sample_match, similar_requirements):
        """Test that existing pattern is enhanced when conceptually similar with low novelty."""
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.8), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.3), \
             patch.object(service, '_enhance_existing_pattern', new_callable=AsyncMock) as mock_enhance:
            
            result = await service._should_create_new_pattern([sample_match], similar_requirements, "test-session")
            
            assert result is False
            mock_enhance.assert_called_once_with(sample_match, similar_requirements, "test-session")

    @pytest.mark.asyncio
    async def test_create_pattern_significant_tech_difference(self, service, sample_match):
        """Test that new pattern is created when technology difference is significant."""
        requirements = {
            "description": "Build a React frontend with Node.js backend and MongoDB",
            "tech_stack": ["React", "Node.js", "MongoDB", "GraphQL"],
            "session_id": "test-session"
        }
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.4), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.6), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.8):
            
            result = await service._should_create_new_pattern([sample_match], requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_create_pattern_unique_scenario_detection(self, service, sample_match):
        """Test that new pattern is created for unique scenarios with multiple indicators."""
        requirements = {
            "description": "Build amazon connect integration with real-time translation and blockchain verification for serverless deployment",
            "session_id": "test-session"
        }
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.3):
            
            result = await service._should_create_new_pattern([sample_match], requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_create_pattern_domain_mismatch(self, service, sample_match):
        """Test that new pattern is created for domain-specific requirements with poor matches."""
        sample_match.blended_score = 0.6  # Mediocre score
        requirements = {
            "description": "Healthcare patient data management system",
            "domain": "healthcare",
            "session_id": "test-session"
        }
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.3):
            
            result = await service._should_create_new_pattern([sample_match], requirements, "test-session")
            
            assert result is True

    # Technology Novelty Score Tests
    
    @pytest.mark.asyncio
    async def test_technology_novelty_high_score(self, service):
        """Test technology novelty calculation with novel technologies."""
        requirements = {
            "tech_stack": ["Ethereum", "Solidity", "TensorFlow", "Kubernetes"],
            "description": "Using blockchain and machine learning for verification"
        }
        
        # Mock empty existing patterns
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = []
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            assert score > 0.8

    @pytest.mark.asyncio
    async def test_technology_novelty_low_score(self, service):
        """Test technology novelty calculation with existing technologies."""
        requirements = {
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
            "description": "Standard Python web application"
        }
        
        # Mock existing patterns with same technologies
        mock_patterns = [
            {"pattern_id": "PAT-001", "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"]}
        ]
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = mock_patterns
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            assert score < 0.5

    @pytest.mark.asyncio
    async def test_technology_novelty_llm_tech_stack_parsing(self, service):
        """Test parsing of LLM-generated tech stack recommendations."""
        requirements = {
            "llm_analysis_tech_stack": ["React", "Node.js", "GraphQL", "MongoDB"]
        }
        
        # Mock empty existing patterns
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = []
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            assert score > 0.8

    @pytest.mark.asyncio
    async def test_technology_novelty_description_extraction(self, service):
        """Test technology extraction from description text."""
        requirements = {
            "description": "Build a system using OAuth2 authentication with JWT tokens, store data in DynamoDB, and deploy on Lambda"
        }
        
        # Mock empty existing patterns
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = []
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            assert score > 0.8

    @pytest.mark.asyncio
    async def test_technology_novelty_error_handling(self, service):
        """Test error handling in technology novelty calculation."""
        requirements = {"tech_stack": ["Python"]}
        
        # Mock PatternLoader to raise an exception
        with patch('app.pattern.loader.PatternLoader', side_effect=Exception("Test error")):
            score = await service._calculate_technology_novelty_score([], requirements)
            
            # Should return high novelty score on error (0.8 as per implementation)
            assert score == 0.8

    # Technology Difference Score Tests
    
    @pytest.mark.asyncio
    async def test_technology_difference_high_difference(self, service, sample_match):
        """Test technology difference calculation with high difference."""
        sample_match.tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        requirements = {
            "tech_stack": ["React", "Node.js", "MongoDB", "GraphQL"],
            "description": "Build a modern web application with real-time features"
        }
        
        # Mock pattern data
        mock_pattern = {
            "pattern_id": "PAT-001",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
        }
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = [mock_pattern]
            
            score = await service._calculate_technology_difference_score(sample_match, requirements)
            
            assert score > 0.7

    @pytest.mark.asyncio
    async def test_technology_difference_low_difference(self, service, sample_match):
        """Test technology difference calculation with low difference."""
        sample_match.tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        requirements = {
            "tech_stack": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            "description": "Build a Python web application with caching"
        }
        
        # Mock pattern data
        mock_pattern = {
            "pattern_id": "PAT-001",
            "tech_stack": ["Python", "FastAPI", "PostgreSQL"]
        }
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = [mock_pattern]
            
            score = await service._calculate_technology_difference_score(sample_match, requirements)
            
            assert score < 0.5

    @pytest.mark.asyncio
    async def test_technology_difference_empty_requirements(self, service, sample_match):
        """Test technology difference calculation with empty requirements."""
        requirements = {}
        
        score = await service._calculate_technology_difference_score(sample_match, requirements)
        
        assert score == 0.0

    @pytest.mark.asyncio
    async def test_technology_difference_empty_pattern(self, service):
        """Test technology difference calculation with empty pattern tech stack."""
        match = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Test Pattern",
            feasibility="Automatable",
            tech_stack=[],  # Empty tech stack
            confidence=0.8,
            tag_score=0.7,
            vector_score=0.6,
            blended_score=0.65,
            rationale="Test match"
        )
        
        requirements = {
            "tech_stack": ["Python", "FastAPI"]
        }
        
        # Mock pattern data with empty tech stack
        mock_pattern = {
            "pattern_id": "PAT-001",
            "tech_stack": []
        }
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = [mock_pattern]
            
            score = await service._calculate_technology_difference_score(match, requirements)
            
            assert score == 1.0

    # Conceptual Similarity Score Tests
    
    @pytest.mark.asyncio
    async def test_conceptual_similarity_high_similarity(self, service, sample_match):
        """Test conceptual similarity calculation with high similarity."""
        requirements = {
            "description": "user authentication with two-factor verification and password reset",
            "domain": "security",
            "pattern_types": ["authentication_workflow"],
            "feasibility": "Automatable",
            "compliance": ["GDPR"]
        }
        
        # Mock pattern data
        mock_pattern = {
            "pattern_id": "PAT-001",
            "description": "identity verification and user authentication system with multi-factor auth",
            "domain": "security",
            "pattern_type": ["authentication_workflow"],
            "feasibility": "Automatable",
            "constraints": {
                "compliance_requirements": ["GDPR", "HIPAA"]
            }
        }
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = [mock_pattern]
            
            score = await service._calculate_conceptual_similarity_score(sample_match, requirements)
            
            assert score > 0.7

    @pytest.mark.asyncio
    async def test_conceptual_similarity_different_concepts(self, service, sample_match):
        """Test conceptual similarity calculation for different concepts."""
        requirements = {
            "description": "inventory management system for tracking products and suppliers",
            "domain": "logistics",
            "pattern_types": ["data_processing"],
            "feasibility": "Automatable"
        }
        
        # Mock pattern data for authentication (different concept)
        mock_pattern = {
            "pattern_id": "PAT-001",
            "description": "user authentication with password reset and session management",
            "domain": "security",
            "pattern_type": ["authentication_workflow"],
            "feasibility": "Automatable"
        }
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = [mock_pattern]
            
            score = await service._calculate_conceptual_similarity_score(sample_match, requirements)
            
            assert score < 0.3

    @pytest.mark.asyncio
    async def test_conceptual_similarity_error_handling(self, service, sample_match):
        """Test error handling in conceptual similarity calculation."""
        requirements = {"description": "test"}
        
        # Mock PatternLoader to raise an exception
        with patch('app.pattern.loader.PatternLoader', side_effect=Exception("Test error")):
            score = await service._calculate_conceptual_similarity_score(sample_match, requirements)
            
            assert score == 0.0

    # Pattern Creation Audit Logging Tests
    
    @pytest.mark.asyncio
    async def test_pattern_creation_decision_logging(self, service, sample_match, novel_tech_requirements):
        """Test that pattern creation decisions are properly logged with all factors."""
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.8), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.6), \
             patch.object(service, '_log_pattern_decision') as mock_log:
            
            await service._should_create_new_pattern([sample_match], novel_tech_requirements, "test-session")
            
            # Verify logging was called
            mock_log.assert_called_once()
            args = mock_log.call_args[0]
            assert args[0] is True  # should_create
            assert isinstance(args[1], dict)  # decision_factors
            assert "test-session" in args[2]  # session_id
            assert isinstance(args[3], str)  # rationale

    def test_log_pattern_decision_comprehensive_format(self, service):
        """Test that pattern decision logging includes all required information."""
        decision_factors = {
            "no_matches": False,
            "low_scores": False,
            "technology_novelty": True,
            "conceptual_similarity": False,
            "unique_scenario": False,
            "domain_mismatch": False,
            "significant_tech_difference": True
        }
        
        with patch('app.services.recommendation.app_logger') as mock_logger:
            service._log_pattern_decision(True, decision_factors, "test-session", "High technology novelty detected")
            
            # Verify comprehensive logging
            assert mock_logger.info.call_count >= 3
            
            # Check that all decision factors are logged
            logged_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            factor_logs = [log for log in logged_calls if "Decision Factors" in log]
            assert len(factor_logs) > 0

    # Pattern Validation and Duplicate Prevention Tests
    
    def test_pattern_id_duplicate_prevention(self, pattern_creator):
        """Test that pattern ID generation prevents duplicates."""
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
            
            # Should generate next available ID
            assert pattern_id == "PAT-004"

    def test_pattern_id_handles_malformed_files(self, pattern_creator):
        """Test pattern ID generation handles malformed existing files."""
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

    @pytest.mark.asyncio
    async def test_pattern_validation_input_requirements(self, pattern_creator):
        """Test pattern creation input validation."""
        # Test empty requirements
        with pytest.raises(ValueError, match="Requirements dictionary cannot be empty"):
            await pattern_creator.create_pattern_from_requirements({}, "test-session")
        
        # Test empty session ID
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            await pattern_creator.create_pattern_from_requirements({"description": "test"}, "")
        
        # Test whitespace-only session ID
        with pytest.raises(ValueError, match="Session ID cannot be empty"):
            await pattern_creator.create_pattern_from_requirements({"description": "test"}, "   ")

    @pytest.mark.asyncio
    async def test_pattern_validation_security_checks(self, pattern_creator, novel_tech_requirements):
        """Test pattern creation security validation."""
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(False, "Security validation failed")):
            
            with pytest.raises(ValueError, match="Pattern creation blocked: Security validation failed"):
                await pattern_creator.create_pattern_from_requirements(novel_tech_requirements, "test-session")

    @pytest.mark.asyncio
    async def test_pattern_validation_feasibility_correction(self, pattern_creator, novel_tech_requirements):
        """Test that invalid feasibility values are corrected during validation."""
        # Mock analysis to return invalid feasibility
        invalid_analysis = {
            "feasibility": "InvalidFeasibility",
            "pattern_name": "Test Pattern"
        }
        
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value=invalid_analysis), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(novel_tech_requirements, "test-session")
            
            # Should correct invalid feasibility
            assert result["feasibility"] in ["Automatable", "Partially Automatable", "Not Automatable"]

    @pytest.mark.asyncio
    async def test_pattern_validation_confidence_range_correction(self, pattern_creator, novel_tech_requirements):
        """Test that confidence scores are validated and corrected to valid range."""
        # Mock analysis to return invalid confidence
        invalid_analysis = {
            "confidence_score": 1.5,  # Invalid (> 1.0)
            "pattern_name": "Test Pattern"
        }
        
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value=invalid_analysis), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(novel_tech_requirements, "test-session")
            
            # Should correct invalid confidence to valid range
            assert 0.0 <= result["confidence_score"] <= 1.0

    @pytest.mark.asyncio
    async def test_pattern_validation_tech_stack_type_correction(self, pattern_creator, novel_tech_requirements):
        """Test that tech stack is validated and corrected to proper list format."""
        # Mock analysis to return invalid tech stack
        invalid_analysis = {
            "tech_stack": "not_a_list",  # Invalid type
            "pattern_name": "Test Pattern"
        }
        
        with patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_analyze_requirements', return_value=invalid_analysis), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            result = await pattern_creator.create_pattern_from_requirements(novel_tech_requirements, "test-session")
            
            # Should correct invalid tech stack to list
            assert isinstance(result["tech_stack"], list)

    # Error Handling Tests
    
    @pytest.mark.asyncio
    async def test_pattern_creation_error_handling_comprehensive(self, service, sample_match, novel_tech_requirements):
        """Test comprehensive error handling in pattern creation decision logic."""
        # Mock all calculation methods to raise exceptions
        with patch.object(service, '_calculate_technology_novelty_score', side_effect=Exception("Novelty error")), \
             patch.object(service, '_calculate_conceptual_similarity_score', side_effect=Exception("Similarity error")), \
             patch.object(service, '_calculate_technology_difference_score', side_effect=Exception("Difference error")):
            
            result = await service._should_create_new_pattern([sample_match], novel_tech_requirements, "test-session")
            
            # Should default to creating new pattern on error
            assert result is True

    @pytest.mark.asyncio
    async def test_pattern_creation_critical_error_handling(self, service, sample_match, novel_tech_requirements):
        """Test critical error handling in pattern creation decision logic."""
        # Mock the entire decision logic to fail at logging level
        with patch.object(service, '_log_pattern_decision', side_effect=Exception("Critical logging error")):
            
            result = await service._should_create_new_pattern([sample_match], novel_tech_requirements, "test-session")
            
            # Should default to False on critical error to avoid issues
            assert result is False

    @pytest.mark.asyncio
    async def test_pattern_creator_error_recovery(self, pattern_creator, novel_tech_requirements):
        """Test pattern creator error recovery mechanisms."""
        # Mock ID generation to fail, then succeed with fallback
        with patch.object(pattern_creator, '_generate_pattern_id', side_effect=Exception("ID generation failed")):
            
            with pytest.raises(RuntimeError, match="Pattern ID generation failed"):
                await pattern_creator.create_pattern_from_requirements(novel_tech_requirements, "test-session")

    @pytest.mark.asyncio
    async def test_pattern_creator_llm_failure_fallback(self, pattern_creator, novel_tech_requirements):
        """Test pattern creator fallback when LLM analysis fails."""
        # Mock LLM analysis to fail
        pattern_creator.llm_provider.generate.side_effect = Exception("LLM failed")
        
        # Mock successful pattern saving
        with patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")), \
             patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"):
            
            result = await pattern_creator.create_pattern_from_requirements(novel_tech_requirements, "test-session")
            
            # Should succeed with fallback analysis
            assert result["pattern_id"] == "PAT-001"
            assert result["feasibility"] in ["Automatable", "Partially Automatable", "Not Automatable"]
            assert isinstance(result["tech_stack"], list)

    # Integration Tests
    
    @pytest.mark.asyncio
    async def test_end_to_end_pattern_creation_flow(self, service, pattern_creator, novel_tech_requirements):
        """Test end-to-end pattern creation flow from decision to creation."""
        # Mock pattern creation components
        service.pattern_creator = pattern_creator
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.8), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.4), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.6), \
             patch.object(pattern_creator, '_generate_pattern_id', return_value="PAT-001"), \
             patch.object(pattern_creator, '_save_pattern_securely', return_value=(True, "Success")):
            
            # Test decision logic
            should_create = await service._should_create_new_pattern([], novel_tech_requirements, "test-session")
            assert should_create is True
            
            # Test pattern creation
            new_pattern = await pattern_creator.create_pattern_from_requirements(novel_tech_requirements, "test-session")
            assert new_pattern["pattern_id"] == "PAT-001"
            assert "blockchain" in new_pattern["name"].lower() or "fintech" in new_pattern["name"].lower()

    @pytest.mark.asyncio
    async def test_pattern_enhancement_flow(self, service, sample_match, similar_requirements):
        """Test pattern enhancement flow when similarity is high."""
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.8), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.3), \
             patch.object(service, '_enhance_existing_pattern', new_callable=AsyncMock) as mock_enhance:
            
            should_create = await service._should_create_new_pattern([sample_match], similar_requirements, "test-session")
            
            assert should_create is False
            mock_enhance.assert_called_once_with(sample_match, similar_requirements, "test-session")