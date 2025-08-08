"""Unit tests for recommendation service."""

import pytest
from unittest.mock import Mock

from app.services.recommendation import RecommendationService
from app.pattern.matcher import MatchResult
from app.state.store import Recommendation


class TestRecommendationService:
    """Test cases for RecommendationService."""
    
    @pytest.fixture
    def service(self):
        """Create recommendation service instance."""
        return RecommendationService(confidence_threshold=0.6)
    
    @pytest.fixture
    def sample_match_result(self):
        """Create sample match result."""
        return MatchResult(
            pattern_id="PAT-001",
            pattern_name="Data Processing Pipeline",
            feasibility="Automatable",
            tech_stack=["Python", "FastAPI", "PostgreSQL"],
            confidence=0.85,
            tag_score=0.8,
            vector_score=0.7,
            blended_score=0.75,
            rationale="Strong match based on requirements"
        )
    
    @pytest.fixture
    def sample_requirements(self):
        """Create sample requirements."""
        return {
            "description": "Process customer data from multiple sources",
            "domain": "data_processing",
            "workflow_steps": ["extract", "transform", "load"],
            "integrations": ["database", "api"],
            "data_sensitivity": "medium",
            "volume": {"daily": 1000},
            "sla": {"response_time_ms": 5000},
            "compliance": ["GDPR"],
            "human_review": "optional"
        }
    
    def test_generate_recommendations_basic(self, service, sample_match_result, sample_requirements):
        """Test basic recommendation generation."""
        matches = [sample_match_result]
        
        recommendations = service.generate_recommendations(matches, sample_requirements)
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert isinstance(rec, Recommendation)
        assert rec.pattern_id == "PAT-001"
        assert rec.feasibility in ["Yes", "Partial", "No"]
        assert 0.0 <= rec.confidence <= 1.0
        assert isinstance(rec.tech_stack, list)
        assert isinstance(rec.reasoning, str)
        assert len(rec.reasoning) > 0
    
    def test_generate_recommendations_multiple_matches(self, service, sample_requirements):
        """Test recommendation generation with multiple matches."""
        matches = [
            MatchResult(
                pattern_id="PAT-001",
                pattern_name="Pattern 1",
                feasibility="Automatable",
                tech_stack=["Python"],
                confidence=0.9,
                tag_score=0.8,
                vector_score=0.85,
                blended_score=0.85,
                rationale="High quality match"
            ),
            MatchResult(
                pattern_id="PAT-002",
                pattern_name="Pattern 2",
                feasibility="Partially Automatable",
                tech_stack=["Java"],
                confidence=0.7,
                tag_score=0.6,
                vector_score=0.65,
                blended_score=0.65,
                rationale="Moderate match"
            )
        ]
        
        recommendations = service.generate_recommendations(matches, sample_requirements)
        
        assert len(recommendations) == 2
        # Should be sorted by confidence (descending)
        assert recommendations[0].confidence >= recommendations[1].confidence
    
    def test_determine_feasibility_automatable_low_complexity(self, service, sample_requirements):
        """Test feasibility determination for automatable pattern with low complexity."""
        match = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Simple Pattern",
            feasibility="Automatable",
            tech_stack=["Python"],
            confidence=0.9,
            tag_score=0.8,
            vector_score=0.85,
            blended_score=0.85,
            rationale="Simple automation"
        )
        
        # Low complexity requirements
        simple_requirements = {
            "description": "Simple task",
            "data_sensitivity": "low",
            "integrations": ["api"],
            "compliance": [],
            "human_review": "none"
        }
        
        feasibility = service._determine_feasibility(match, simple_requirements)
        assert feasibility == "Yes"
    
    def test_determine_feasibility_automatable_high_complexity(self, service):
        """Test feasibility determination for automatable pattern with high complexity."""
        match = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Complex Pattern",
            feasibility="Automatable",
            tech_stack=["Python"],
            confidence=0.9,
            tag_score=0.8,
            vector_score=0.85,
            blended_score=0.85,
            rationale="Complex automation"
        )
        
        # High complexity requirements
        complex_requirements = {
            "description": "Complex task",
            "data_sensitivity": "high",
            "integrations": ["db1", "db2", "api1", "api2", "queue"],
            "compliance": ["GDPR", "HIPAA"],
            "human_review": "required",
            "workflow_steps": list(range(15))  # Many steps
        }
        
        feasibility = service._determine_feasibility(match, complex_requirements)
        assert feasibility in ["Partial", "No"]
    
    def test_determine_feasibility_partial_pattern(self, service, sample_requirements):
        """Test feasibility determination for partially automatable pattern."""
        match = MatchResult(
            pattern_id="PAT-002",
            pattern_name="Partial Pattern",
            feasibility="Partially Automatable",
            tech_stack=["Python"],
            confidence=0.7,
            tag_score=0.6,
            vector_score=0.65,
            blended_score=0.65,
            rationale="Partial automation"
        )
        
        feasibility = service._determine_feasibility(match, sample_requirements)
        assert feasibility in ["Partial", "No"]
    
    def test_determine_feasibility_not_automatable_pattern(self, service, sample_requirements):
        """Test feasibility determination for non-automatable pattern."""
        match = MatchResult(
            pattern_id="PAT-003",
            pattern_name="Manual Pattern",
            feasibility="Not Automatable",
            tech_stack=[],
            confidence=0.5,
            tag_score=0.4,
            vector_score=0.45,
            blended_score=0.45,
            rationale="Manual process"
        )
        
        feasibility = service._determine_feasibility(match, sample_requirements)
        # Could be "Partial" if match quality is very high and complexity is low
        assert feasibility in ["Partial", "No"]
    
    def test_analyze_complexity_factors(self, service):
        """Test complexity factor analysis."""
        requirements = {
            "data_sensitivity": "high",
            "integrations": ["db1", "db2", "api1", "api2"],
            "workflow_steps": list(range(12)),
            "volume": {"daily": 15000}
        }
        
        factors = service._analyze_complexity_factors(requirements)
        
        assert "data_sensitivity" in factors
        assert factors["data_sensitivity"] == 2  # High sensitivity
        assert "integrations" in factors
        assert factors["integrations"] == 2  # 4 integrations
        assert "workflow_complexity" in factors
        assert factors["workflow_complexity"] == 2  # 12 steps
        assert "volume" in factors
        assert factors["volume"] == 2  # High volume
    
    def test_analyze_risk_factors(self, service):
        """Test risk factor analysis."""
        requirements = {
            "compliance": ["GDPR", "HIPAA"],
            "human_review": "required",
            "sla": {"response_time_ms": 500}
        }
        
        factors = service._analyze_risk_factors(requirements)
        
        assert "compliance" in factors
        assert factors["compliance"] == 3  # High-risk compliance
        assert "human_review" in factors
        assert factors["human_review"] == 2  # Required review
        assert "sla" in factors
        assert factors["sla"] == 2  # Sub-second SLA
    
    def test_calculate_confidence(self, service, sample_match_result, sample_requirements):
        """Test confidence calculation."""
        confidence = service._calculate_confidence(
            sample_match_result, 
            sample_requirements, 
            "Yes"
        )
        
        assert 0.0 <= confidence <= 1.0
        assert isinstance(confidence, float)
    
    def test_calculate_confidence_feasibility_adjustment(self, service, sample_match_result, sample_requirements):
        """Test confidence adjustment based on feasibility."""
        confidence_yes = service._calculate_confidence(
            sample_match_result, sample_requirements, "Yes"
        )
        confidence_partial = service._calculate_confidence(
            sample_match_result, sample_requirements, "Partial"
        )
        confidence_no = service._calculate_confidence(
            sample_match_result, sample_requirements, "No"
        )
        
        # Confidence should decrease with feasibility
        assert confidence_yes > confidence_partial > confidence_no
    
    def test_calculate_completeness_score(self, service):
        """Test requirements completeness scoring."""
        # Complete requirements
        complete_requirements = {
            "description": "Complete description",
            "domain": "test_domain",
            "workflow_steps": ["step1", "step2"],
            "integrations": ["api1"],
            "data_sensitivity": "medium",
            "volume": {"daily": 100},
            "sla": {"response_time_ms": 1000}
        }
        
        complete_score = service._calculate_completeness_score(complete_requirements)
        assert complete_score == 1.0
        
        # Incomplete requirements
        incomplete_requirements = {
            "description": "Basic description",
            "domain": "test_domain"
        }
        
        incomplete_score = service._calculate_completeness_score(incomplete_requirements)
        assert 0.0 < incomplete_score < 1.0
        
        # Empty requirements
        empty_score = service._calculate_completeness_score({})
        assert empty_score == 0.0
    
    def test_suggest_tech_stack_basic(self, service, sample_match_result, sample_requirements):
        """Test basic tech stack suggestion."""
        tech_stack = service._suggest_tech_stack(sample_match_result, sample_requirements)
        
        assert isinstance(tech_stack, list)
        # Should include original tech stack
        for tech in sample_match_result.tech_stack:
            assert tech in tech_stack
    
    def test_suggest_tech_stack_database_integration(self, service, sample_match_result):
        """Test tech stack suggestion with database integration."""
        requirements = {
            "integrations": ["database", "postgresql"]
        }
        
        tech_stack = service._suggest_tech_stack(sample_match_result, requirements)
        
        # Should suggest SQLAlchemy for database integration
        assert "SQLAlchemy" in tech_stack or any("SQL" in tech for tech in tech_stack)
    
    def test_suggest_tech_stack_api_integration(self, service, sample_match_result):
        """Test tech stack suggestion with API integration."""
        requirements = {
            "integrations": ["rest_api", "external_api"]
        }
        
        tech_stack = service._suggest_tech_stack(sample_match_result, requirements)
        
        # Should suggest HTTP client library
        assert "httpx" in tech_stack or "requests" in tech_stack
    
    def test_suggest_tech_stack_high_volume(self, service, sample_match_result):
        """Test tech stack suggestion for high volume requirements."""
        requirements = {
            "volume": {"daily": 50000}
        }
        
        tech_stack = service._suggest_tech_stack(sample_match_result, requirements)
        
        # Should suggest caching and containerization
        assert "Redis" in tech_stack
        assert "Docker" in tech_stack
    
    def test_suggest_tech_stack_compliance(self, service, sample_match_result):
        """Test tech stack suggestion for compliance requirements."""
        requirements = {
            "compliance": ["GDPR", "HIPAA"]
        }
        
        tech_stack = service._suggest_tech_stack(sample_match_result, requirements)
        
        # Should suggest cryptography for compliance
        assert "cryptography" in tech_stack
    
    def test_generate_reasoning_comprehensive(self, service, sample_match_result, sample_requirements):
        """Test comprehensive reasoning generation."""
        reasoning = service._generate_reasoning(
            sample_match_result, 
            sample_requirements, 
            "Yes", 
            0.85
        )
        
        assert isinstance(reasoning, str)
        assert len(reasoning) > 50  # Should be detailed
        assert "pattern match" in reasoning.lower()
        assert "automation" in reasoning.lower()
        assert "confidence" in reasoning.lower()
        assert reasoning.endswith(".")
    
    def test_generate_reasoning_different_feasibilities(self, service, sample_match_result, sample_requirements):
        """Test reasoning generation for different feasibility levels."""
        reasoning_yes = service._generate_reasoning(
            sample_match_result, sample_requirements, "Yes", 0.9
        )
        reasoning_partial = service._generate_reasoning(
            sample_match_result, sample_requirements, "Partial", 0.7
        )
        reasoning_no = service._generate_reasoning(
            sample_match_result, sample_requirements, "No", 0.3
        )
        
        assert "recommended" in reasoning_yes.lower()
        assert "partial" in reasoning_partial.lower()
        assert "not recommended" in reasoning_no.lower()
    
    def test_empty_matches_list(self, service, sample_requirements):
        """Test handling of empty matches list."""
        recommendations = service.generate_recommendations([], sample_requirements)
        assert recommendations == []
    
    def test_missing_requirements_fields(self, service, sample_match_result):
        """Test handling of missing requirements fields."""
        minimal_requirements = {"description": "Basic task"}
        
        recommendations = service.generate_recommendations([sample_match_result], minimal_requirements)
        
        assert len(recommendations) == 1
        rec = recommendations[0]
        assert rec.feasibility in ["Yes", "Partial", "No"]
        assert 0.0 <= rec.confidence <= 1.0
    
    def test_confidence_threshold_initialization(self):
        """Test service initialization with custom confidence threshold."""
        service = RecommendationService(confidence_threshold=0.8)
        assert service.confidence_threshold == 0.8
        
        # Test default threshold
        default_service = RecommendationService()
        assert default_service.confidence_threshold == 0.6


class TestRecommendationServiceEdgeCases:
    """Test edge cases and error conditions."""
    
    @pytest.fixture
    def service(self):
        """Create recommendation service instance."""
        return RecommendationService()
    
    def test_zero_confidence_match(self, service):
        """Test handling of zero confidence match."""
        match = MatchResult(
            pattern_id="PAT-ZERO",
            pattern_name="Zero Confidence",
            feasibility="Automatable",
            tech_stack=[],
            confidence=0.0,
            tag_score=0.0,
            vector_score=0.0,
            blended_score=0.0,
            rationale="No match"
        )
        
        requirements = {"description": "Test"}
        recommendations = service.generate_recommendations([match], requirements)
        
        assert len(recommendations) == 1
        assert recommendations[0].confidence >= 0.0
    
    def test_perfect_confidence_match(self, service):
        """Test handling of perfect confidence match."""
        match = MatchResult(
            pattern_id="PAT-PERFECT",
            pattern_name="Perfect Match",
            feasibility="Automatable",
            tech_stack=["Python"],
            confidence=1.0,
            tag_score=1.0,
            vector_score=1.0,
            blended_score=1.0,
            rationale="Perfect match"
        )
        
        requirements = {
            "description": "Perfect task",
            "domain": "test",
            "workflow_steps": ["step1"],
            "integrations": ["api"],
            "data_sensitivity": "low",
            "volume": {"daily": 10},
            "sla": {"response_time_ms": 10000}
        }
        
        recommendations = service.generate_recommendations([match], requirements)
        
        assert len(recommendations) == 1
        assert recommendations[0].confidence <= 1.0
        assert recommendations[0].feasibility == "Yes"
    
    def test_string_compliance_field(self, service):
        """Test handling of compliance field as string instead of list."""
        requirements = {
            "compliance": "GDPR"  # String instead of list
        }
        
        factors = service._analyze_risk_factors(requirements)
        assert factors["compliance"] == 3  # Should handle string correctly
    
    def test_empty_tech_stack(self, service):
        """Test handling of empty tech stack in pattern."""
        match = MatchResult(
            pattern_id="PAT-EMPTY",
            pattern_name="Empty Tech Stack",
            feasibility="Automatable",
            tech_stack=[],
            confidence=0.8,
            tag_score=0.7,
            vector_score=0.75,
            blended_score=0.75,
            rationale="No tech stack"
        )
        
        requirements = {"description": "Test"}
        tech_stack = service._suggest_tech_stack(match, requirements)
        
        assert isinstance(tech_stack, list)
        # Should still suggest technologies based on requirements
    
    def test_duplicate_tech_stack_removal(self, service):
        """Test removal of duplicate technologies in suggested stack."""
        match = MatchResult(
            pattern_id="PAT-DUP",
            pattern_name="Duplicate Tech",
            feasibility="Automatable",
            tech_stack=["Python", "httpx"],
            confidence=0.8,
            tag_score=0.7,
            vector_score=0.75,
            blended_score=0.75,
            rationale="Has duplicates"
        )
        
        requirements = {
            "integrations": ["api"],  # Would suggest httpx
            "volume": {"daily": 20000}  # Would suggest Redis, Docker
        }
        
        tech_stack = service._suggest_tech_stack(match, requirements)
        
        # Should not have duplicates
        assert len(tech_stack) == len(set(tech_stack))
        assert "httpx" in tech_stack  # Should appear only once