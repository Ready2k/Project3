"""Tests for pattern creation decision logic."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path

from app.services.recommendation import RecommendationService
from app.pattern.matcher import MatchResult


class TestPatternCreationDecision:
    """Test pattern creation decision logic."""
    
    @pytest.fixture
    def service(self):
        """Create recommendation service for testing."""
        return RecommendationService(
            confidence_threshold=0.6,
            pattern_library_path=Path("data/patterns"),
            llm_provider=AsyncMock()
        )
    
    @pytest.fixture
    def sample_match(self):
        """Create a sample match result."""
        return MatchResult(
            pattern_id="PAT-001",
            pattern_name="Test Pattern",
            feasibility="Automatable",
            tech_stack=["Python", "FastAPI"],
            confidence=0.8,
            tag_score=0.7,
            vector_score=0.6,
            blended_score=0.65,
            rationale="Test match"
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

    @pytest.mark.asyncio
    async def test_should_create_pattern_no_matches(self, service):
        """Test that new pattern is created when no matches exist."""
        requirements = {"description": "Novel requirement"}
        
        result = await service._should_create_new_pattern([], requirements, "test-session")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_should_create_pattern_low_scores(self, service, sample_match):
        """Test that new pattern is created when all matches have low scores."""
        sample_match.blended_score = 0.3  # Below 0.4 threshold
        requirements = {"description": "Test requirement"}
        
        result = await service._should_create_new_pattern([sample_match], requirements, "test-session")
        
        assert result is True

    @pytest.mark.asyncio
    async def test_should_create_pattern_high_technology_novelty(self, service, sample_match, sample_requirements):
        """Test that new pattern is created when technology novelty is high."""
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.8), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.8):
            
            result = await service._should_create_new_pattern([sample_match], sample_requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_should_enhance_pattern_high_similarity_low_novelty(self, service, sample_match, sample_requirements):
        """Test that existing pattern is enhanced when conceptually similar but not novel."""
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.8), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.3), \
             patch.object(service, '_enhance_existing_pattern', new_callable=AsyncMock) as mock_enhance:
            
            result = await service._should_create_new_pattern([sample_match], sample_requirements, "test-session")
            
            assert result is False
            mock_enhance.assert_called_once()

    @pytest.mark.asyncio
    async def test_should_create_pattern_unique_scenario(self, service, sample_match):
        """Test that new pattern is created for unique scenarios."""
        requirements = {
            "description": "Build amazon connect integration with real-time translation for customer chat"
        }
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5):
            
            result = await service._should_create_new_pattern([sample_match], requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_should_create_pattern_domain_mismatch(self, service, sample_match):
        """Test that new pattern is created for domain-specific requirements with poor matches."""
        sample_match.blended_score = 0.6  # Mediocre score
        requirements = {
            "description": "Healthcare specific requirement",
            "domain": "healthcare"
        }
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5):
            
            result = await service._should_create_new_pattern([sample_match], requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_technology_novelty_score_calculation(self, service):
        """Test technology novelty score calculation."""
        requirements = {
            "tech_stack": ["NewTech1", "NewTech2", "Python"],
            "description": "Using kubernetes and terraform for deployment"
        }
        
        # Mock pattern loader to return existing patterns
        mock_patterns = [
            {"pattern_id": "PAT-001", "tech_stack": ["Python", "FastAPI", "PostgreSQL"]},
            {"pattern_id": "PAT-002", "tech_stack": ["Node.js", "Express", "MongoDB"]}
        ]
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = mock_patterns
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            # Should be high because NewTech1, NewTech2, kubernetes, terraform are novel
            assert score > 0.5

    @pytest.mark.asyncio
    async def test_technology_novelty_score_no_novel_tech(self, service):
        """Test technology novelty score when no novel technologies are present."""
        requirements = {
            "tech_stack": ["Python", "FastAPI"],
            "description": "Standard Python web application"
        }
        
        # Mock pattern loader to return existing patterns with same tech
        mock_patterns = [
            {"pattern_id": "PAT-001", "tech_stack": ["Python", "FastAPI", "PostgreSQL"]}
        ]
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = mock_patterns
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            # Should be low because all technologies already exist
            assert score < 0.5

    @pytest.mark.asyncio
    async def test_conceptual_similarity_score_calculation(self, service, sample_match):
        """Test conceptual similarity score calculation."""
        requirements = {
            "description": "user authentication with two-factor verification",
            "domain": "security",
            "pattern_types": ["authentication_workflow"],
            "feasibility": "Automatable",
            "compliance": ["GDPR"]
        }
        
        # Mock pattern data
        mock_pattern = {
            "pattern_id": "PAT-001",
            "description": "identity verification and user authentication system",
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
            
            # Should be high due to matching keywords, domain, pattern types, etc.
            assert score > 0.7

    @pytest.mark.asyncio
    async def test_conceptual_similarity_score_different_concepts(self, service, sample_match):
        """Test conceptual similarity score for different concepts."""
        requirements = {
            "description": "inventory management system for tracking products",
            "domain": "logistics",
            "pattern_types": ["data_processing"],
            "feasibility": "Automatable"
        }
        
        # Mock pattern data for authentication (different concept)
        mock_pattern = {
            "pattern_id": "PAT-001",
            "description": "user authentication with password reset",
            "domain": "security",
            "pattern_type": ["authentication_workflow"],
            "feasibility": "Automatable"
        }
        
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = [mock_pattern]
            
            score = await service._calculate_conceptual_similarity_score(sample_match, requirements)
            
            # Should be low due to different domains and concepts
            assert score < 0.3

    @pytest.mark.asyncio
    async def test_decision_logging(self, service, sample_match, sample_requirements):
        """Test that pattern creation decisions are properly logged."""
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.8), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5), \
             patch.object(service, '_log_pattern_decision') as mock_log:
            
            await service._should_create_new_pattern([sample_match], sample_requirements, "test-session")
            
            # Verify logging was called
            mock_log.assert_called_once()
            args = mock_log.call_args
            assert args[0][0] is True  # should_create
            assert "test-session" in args[0]  # session_id in args

    def test_log_pattern_decision_format(self, service):
        """Test that pattern decision logging includes all required information."""
        decision_factors = {
            "no_matches": False,
            "low_scores": False,
            "technology_novelty": True,
            "conceptual_similarity": False,
            "unique_scenario": False,
            "domain_mismatch": False
        }
        
        with patch('app.services.recommendation.app_logger') as mock_logger:
            service._log_pattern_decision(True, decision_factors, "test-session", "High technology novelty")
            
            # Verify all expected log calls were made
            assert mock_logger.info.call_count >= 3  # At least decision type, rationale, and factors

    @pytest.mark.asyncio
    async def test_error_handling_in_novelty_calculation(self, service):
        """Test error handling in technology novelty calculation."""
        requirements = {"tech_stack": ["Python"]}
        
        # Mock PatternLoader to raise an exception
        with patch('app.pattern.loader.PatternLoader', side_effect=Exception("Test error")):
            score = await service._calculate_technology_novelty_score([], requirements)
            
            # Should return high novelty score on error (0.8 as per implementation)
            assert score == 0.8

    @pytest.mark.asyncio
    async def test_error_handling_in_similarity_calculation(self, service, sample_match):
        """Test error handling in conceptual similarity calculation."""
        requirements = {"description": "test"}
        
        # Mock PatternLoader to raise an exception
        with patch('app.pattern.loader.PatternLoader', side_effect=Exception("Test error")):
            score = await service._calculate_conceptual_similarity_score(sample_match, requirements)
            
            # Should return 0.0 on error
            assert score == 0.0

    @pytest.mark.asyncio
    async def test_technology_extraction_from_description(self, service):
        """Test that technologies are properly extracted from description text."""
        requirements = {
            "description": "Build a system using OAuth2 authentication with JWT tokens, store data in DynamoDB, and deploy on Lambda"
        }
        
        # Mock empty existing patterns
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = []
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            # Should be high because all mentioned technologies are novel
            assert score > 0.8

    @pytest.mark.asyncio
    async def test_llm_tech_stack_parsing(self, service):
        """Test parsing of LLM-generated tech stack recommendations."""
        requirements = {
            "llm_analysis_tech_stack": ["React", "Node.js", "GraphQL", "MongoDB"]
        }
        
        # Mock empty existing patterns
        with patch('app.pattern.loader.PatternLoader') as mock_loader:
            mock_loader.return_value.load_patterns.return_value = []
            
            score = await service._calculate_technology_novelty_score([], requirements)
            
            # Should be high because all technologies are novel
            assert score > 0.8

    @pytest.mark.asyncio
    async def test_technology_difference_score_high_difference(self, service, sample_match):
        """Test technology difference score calculation with high difference."""
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
            
            # Should be high because tech stacks are very different
            assert score > 0.7

    @pytest.mark.asyncio
    async def test_technology_difference_score_low_difference(self, service, sample_match):
        """Test technology difference score calculation with low difference."""
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
            
            # Should be low because tech stacks are mostly similar
            assert score < 0.5

    @pytest.mark.asyncio
    async def test_should_create_pattern_significant_tech_difference(self, service, sample_match, sample_requirements):
        """Test that new pattern is created when technology difference is significant."""
        sample_requirements["tech_stack"] = ["React", "Node.js", "MongoDB", "GraphQL"]
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.8), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.8):
            
            result = await service._should_create_new_pattern([sample_match], sample_requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_enhanced_unique_scenario_detection(self, service, sample_match):
        """Test enhanced unique scenario detection with new indicators."""
        requirements = {
            "description": "Build a blockchain-based system with machine learning model integration for serverless deployment"
        }
        
        with patch.object(service, '_calculate_technology_novelty_score', return_value=0.3), \
             patch.object(service, '_calculate_conceptual_similarity_score', return_value=0.5), \
             patch.object(service, '_calculate_technology_difference_score', return_value=0.3):
            
            result = await service._should_create_new_pattern([sample_match], requirements, "test-session")
            
            assert result is True

    @pytest.mark.asyncio
    async def test_error_handling_in_decision_logic(self, service, sample_match, sample_requirements):
        """Test error handling in pattern creation decision logic."""
        # Mock methods to raise exceptions
        with patch.object(service, '_calculate_technology_novelty_score', side_effect=Exception("Test error")), \
             patch.object(service, '_calculate_conceptual_similarity_score', side_effect=Exception("Test error")), \
             patch.object(service, '_calculate_technology_difference_score', side_effect=Exception("Test error")):
            
            result = await service._should_create_new_pattern([sample_match], sample_requirements, "test-session")
            
            # Should default to creating new pattern on error
            assert result is True

    @pytest.mark.asyncio
    async def test_critical_error_handling_in_decision_logic(self, service, sample_match, sample_requirements):
        """Test critical error handling in pattern creation decision logic."""
        # Mock the entire decision logic to fail
        with patch.object(service, '_log_pattern_decision', side_effect=Exception("Critical error")):
            
            result = await service._should_create_new_pattern([sample_match], sample_requirements, "test-session")
            
            # Should default to False on critical error to avoid issues
            assert result is False

    @pytest.mark.asyncio
    async def test_technology_difference_error_handling(self, service, sample_match):
        """Test error handling in technology difference calculation."""
        requirements = {"tech_stack": ["Python"]}
        
        # Mock PatternLoader to raise an exception during pattern loading
        # But the method still has access to match.tech_stack, so it calculates based on that
        with patch('app.pattern.loader.PatternLoader', side_effect=Exception("Test error")):
            score = await service._calculate_technology_difference_score(sample_match, requirements)
            
            # Should still calculate based on match.tech_stack even when pattern loading fails
            # The score will be calculated based on the overlap between requirements and match tech stack
            assert 0.0 <= score <= 1.0  # Should be a valid score

    @pytest.mark.asyncio
    async def test_technology_difference_critical_error_handling(self, service):
        """Test critical error handling in technology difference calculation."""
        # Create a match with no tech_stack to trigger the critical error path
        match = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Test Pattern",
            feasibility="Automatable",
            tech_stack=None,  # This will cause issues
            confidence=0.8,
            tag_score=0.7,
            vector_score=0.6,
            blended_score=0.65,
            rationale="Test match"
        )
        
        requirements = {}  # Empty requirements to trigger error conditions
        
        # Mock everything to fail
        with patch('app.pattern.loader.PatternLoader', side_effect=Exception("Critical error")):
            score = await service._calculate_technology_difference_score(match, requirements)
            
            # Should return 0.0 when no technologies found in requirements (correct behavior)
            assert score == 0.0

    @pytest.mark.asyncio
    async def test_technology_difference_empty_requirements(self, service, sample_match):
        """Test technology difference calculation with empty requirements."""
        requirements = {}
        
        score = await service._calculate_technology_difference_score(sample_match, requirements)
        
        # Should return 0.0 when no technologies found in requirements
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
            
            # Should return 1.0 when pattern has no technologies
            assert score == 1.0

    def test_enhanced_decision_factors_logging(self, service):
        """Test that enhanced decision factors are properly logged."""
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
            service._log_pattern_decision(True, decision_factors, "test-session", "Technology difference detected")
            
            # Verify all expected log calls were made including new factor
            assert mock_logger.info.call_count >= 3
            
            # Check that the new factor is logged
            logged_calls = [call.args[0] for call in mock_logger.info.call_args_list]
            factor_logs = [log for log in logged_calls if "significant_tech_difference" in log]
            assert len(factor_logs) > 0