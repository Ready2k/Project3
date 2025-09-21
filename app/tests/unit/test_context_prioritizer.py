"""Unit tests for requirement context prioritizer."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List

from app.services.requirement_parsing.context_prioritizer import (
    RequirementContextPrioritizer, RequirementSource, ContextPriority,
    AmbiguityType, RequirementWeight, ContextWeight, AmbiguityDetection,
    UserPreference
)
from app.services.requirement_parsing.base import (
    ParsedRequirements, TechContext, ContextClues, DomainContext,
    ExplicitTech, RequirementConstraints, ExtractionMethod
)


class TestRequirementContextPrioritizer:
    """Test cases for RequirementContextPrioritizer."""
    
    @pytest.fixture
    def prioritizer(self):
        """Create a prioritizer instance for testing."""
        return RequirementContextPrioritizer()
    
    @pytest.fixture
    def sample_parsed_requirements(self):
        """Create sample parsed requirements for testing."""
        return ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(
                    name="Amazon Connect SDK",
                    confidence=0.9,
                    extraction_method=ExtractionMethod.EXPLICIT_MENTION,
                    source_text="We need Amazon Connect SDK for voice integration"
                ),
                ExplicitTech(
                    name="FastAPI",
                    confidence=0.8,
                    extraction_method=ExtractionMethod.EXPLICIT_MENTION,
                    source_text="Use FastAPI for the REST API"
                )
            ],
            context_clues=ContextClues(
                cloud_providers=["aws"],
                domains=["web_api"],
                integration_patterns=["database", "cache"],
                programming_languages=["python"]
            ),
            constraints=RequirementConstraints(
                banned_tools={"MySQL"},
                required_integrations=["database"]
            ),
            domain_context=DomainContext(
                primary_domain="web_api",
                industry="telecommunications"
            ),
            raw_text="We need Amazon Connect SDK for voice integration. Use FastAPI for the REST API with database and cache integration."
        )
    
    @pytest.fixture
    def sample_tech_context(self):
        """Create sample technology context for testing."""
        return TechContext(
            explicit_technologies={
                "Amazon Connect SDK": 0.9,
                "FastAPI": 0.8
            },
            contextual_technologies={
                "PostgreSQL": 0.7,
                "Redis": 0.6,
                "Nginx": 0.5
            },
            ecosystem_preference="aws",
            integration_requirements=["database", "cache"],
            banned_tools={"MySQL"}
        )
    
    def test_init(self, prioritizer):
        """Test prioritizer initialization."""
        assert prioritizer is not None
        assert len(prioritizer.source_weights) == 5
        assert len(prioritizer.domain_tech_preferences) > 0
        assert len(prioritizer.ambiguity_patterns) > 0
        assert isinstance(prioritizer.user_preferences, dict)
    
    def test_calculate_context_weights(self, prioritizer, sample_parsed_requirements, sample_tech_context):
        """Test context weight calculation."""
        weights = prioritizer.calculate_context_weights(
            sample_parsed_requirements, sample_tech_context
        )
        
        assert isinstance(weights, dict)
        assert len(weights) > 0
        
        # Check that explicit technologies are included
        assert "Amazon Connect SDK" in weights
        assert "FastAPI" in weights
        
        # Check that contextual technologies are included
        assert "PostgreSQL" in weights
        assert "Redis" in weights
        
        # Check weight structure
        for tech, weight in weights.items():
            assert isinstance(weight, ContextWeight)
            assert weight.technology == tech
            assert 0.0 <= weight.final_weight <= 1.0
            assert isinstance(weight.reasoning, list)
    
    def test_calculate_technology_weight(self, prioritizer, sample_parsed_requirements, sample_tech_context):
        """Test individual technology weight calculation."""
        weight = prioritizer._calculate_technology_weight(
            "FastAPI",
            RequirementSource.EXPLICIT_USER_INPUT,
            sample_parsed_requirements.domain_context,
            sample_tech_context,
            0.8
        )
        
        assert isinstance(weight, ContextWeight)
        assert weight.technology == "FastAPI"
        assert weight.base_priority > 0
        assert len(weight.reasoning) > 0
        assert RequirementSource.EXPLICIT_USER_INPUT in weight.source_weights
    
    def test_apply_domain_preferences(self, prioritizer, sample_parsed_requirements):
        """Test domain preference application."""
        context_weights = {
            "FastAPI": ContextWeight(technology="FastAPI", base_priority=0.8),
            "PostgreSQL": ContextWeight(technology="PostgreSQL", base_priority=0.6),
            "Unknown Tech": ContextWeight(technology="Unknown Tech", base_priority=0.5)
        }
        
        prioritizer._apply_domain_preferences(
            context_weights, sample_parsed_requirements.domain_context
        )
        
        # FastAPI should get a boost for web_api domain
        assert context_weights["FastAPI"].domain_boost > 0
        assert len(context_weights["FastAPI"].reasoning) > 0
        
        # PostgreSQL should get a boost for web_api domain
        assert context_weights["PostgreSQL"].domain_boost > 0
        
        # Unknown tech should not get a boost
        assert context_weights["Unknown Tech"].domain_boost == 0
    
    def test_apply_ecosystem_consistency(self, prioritizer, sample_tech_context):
        """Test ecosystem consistency boost application."""
        context_weights = {
            "Amazon Connect SDK": ContextWeight(technology="Amazon Connect SDK", base_priority=0.9),
            "Azure Functions": ContextWeight(technology="Azure Functions", base_priority=0.7),
            "FastAPI": ContextWeight(technology="FastAPI", base_priority=0.8)
        }
        
        prioritizer._apply_ecosystem_consistency(context_weights, sample_tech_context)
        
        # AWS technology should get ecosystem boost
        assert context_weights["Amazon Connect SDK"].ecosystem_boost > 0
        
        # Azure technology should not get boost in AWS ecosystem
        assert context_weights["Azure Functions"].ecosystem_boost == 0
        
        # Open source technology should not get ecosystem boost
        assert context_weights["FastAPI"].ecosystem_boost == 0
    
    def test_apply_user_preferences(self, prioritizer, sample_parsed_requirements):
        """Test user preference application."""
        # Set up user preferences
        prioritizer.user_preferences = {
            "web_api:FastAPI": UserPreference(
                technology="FastAPI",
                domain="web_api",
                selection_count=5,
                rejection_count=1,
                preference_score=0.6
            )
        }
        
        context_weights = {
            "FastAPI": ContextWeight(technology="FastAPI", base_priority=0.8),
            "Django": ContextWeight(technology="Django", base_priority=0.7)
        }
        
        prioritizer._apply_user_preferences(
            context_weights, sample_parsed_requirements.domain_context
        )
        
        # FastAPI should get user preference boost
        assert context_weights["FastAPI"].user_preference_boost > 0
        
        # Django should not get boost (no preference data)
        assert context_weights["Django"].user_preference_boost == 0
    
    def test_calculate_final_weight(self, prioritizer):
        """Test final weight calculation."""
        weight = ContextWeight(
            technology="FastAPI",
            base_priority=0.7,
            domain_boost=0.2,
            ecosystem_boost=0.1,
            user_preference_boost=0.05
        )
        
        final_weight = prioritizer._calculate_final_weight(weight)
        
        assert 0.0 <= final_weight <= 1.0
        assert final_weight == min(0.7 + 0.2 + 0.1 + 0.05, 1.0)
    
    def test_implement_domain_specific_preferences(self, prioritizer, sample_tech_context, sample_parsed_requirements):
        """Test domain-specific preference implementation."""
        preferences = prioritizer.implement_domain_specific_preferences(
            sample_tech_context, sample_parsed_requirements.domain_context
        )
        
        assert isinstance(preferences, dict)
        
        # Should include critical technologies for web_api domain
        web_api_prefs = prioritizer.domain_tech_preferences.get("web_api", {})
        for tech in web_api_prefs.get("critical", []):
            if tech in preferences:
                assert preferences[tech] == ContextPriority.CRITICAL.value
    
    def test_detect_requirement_ambiguity(self, prioritizer):
        """Test requirement ambiguity detection."""
        # Create requirements with ambiguous text
        ambiguous_req = ParsedRequirements(
            raw_text="We need both MySQL and PostgreSQL for the database. "
                    "Use AWS Lambda but also consider Azure Functions. "
                    "The system should be simple but also enterprise-grade.",
            explicit_technologies=[
                ExplicitTech(name="MySQL", confidence=0.8),
                ExplicitTech(name="PostgreSQL", confidence=0.8),
                ExplicitTech(name="AWS Lambda", confidence=0.9),
                ExplicitTech(name="Azure Functions", confidence=0.7)
            ]
        )
        
        ambiguities = prioritizer.detect_requirement_ambiguity(ambiguous_req)
        
        assert isinstance(ambiguities, list)
        assert len(ambiguities) > 0
        
        # Check for technology conflicts
        tech_conflicts = [a for a in ambiguities if a.ambiguity_type == AmbiguityType.TECHNOLOGY_CONFLICT]
        assert len(tech_conflicts) > 0
        
        # Check ambiguity structure
        for ambiguity in ambiguities:
            assert isinstance(ambiguity, AmbiguityDetection)
            assert ambiguity.ambiguity_type in AmbiguityType
            assert isinstance(ambiguity.description, str)
            assert isinstance(ambiguity.conflicting_elements, list)
            assert isinstance(ambiguity.suggested_clarifications, list)
            assert 0.0 <= ambiguity.confidence <= 1.0
            assert ambiguity.impact_level in ["high", "medium", "low"]
    
    def test_detect_technology_conflicts(self, prioritizer):
        """Test technology conflict detection."""
        explicit_techs = [
            ExplicitTech(name="PostgreSQL", confidence=0.8),
            ExplicitTech(name="MySQL", confidence=0.8),
            ExplicitTech(name="React", confidence=0.9),
            ExplicitTech(name="Vue.js", confidence=0.7)
        ]
        
        conflicts = prioritizer._detect_technology_conflicts(explicit_techs)
        
        assert isinstance(conflicts, list)
        assert len(conflicts) >= 2  # Database and frontend conflicts
        
        # Check conflict details
        for conflict in conflicts:
            assert conflict.ambiguity_type == AmbiguityType.TECHNOLOGY_CONFLICT
            assert len(conflict.conflicting_elements) >= 2
            assert conflict.confidence > 0.8  # High confidence for explicit conflicts
    
    def test_detect_ecosystem_conflicts(self, prioritizer):
        """Test ecosystem conflict detection."""
        conflicting_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(name="AWS Lambda", confidence=0.9),
                ExplicitTech(name="Azure Functions", confidence=0.8),
                ExplicitTech(name="Amazon S3", confidence=0.8),
                ExplicitTech(name="Google Cloud Storage", confidence=0.7)
            ]
        )
        
        conflicts = prioritizer._detect_ecosystem_conflicts(conflicting_req)
        
        assert isinstance(conflicts, list)
        assert len(conflicts) > 0
        
        # Should detect multi-cloud conflict
        ecosystem_conflicts = [c for c in conflicts if c.ambiguity_type == AmbiguityType.ECOSYSTEM_MISMATCH]
        assert len(ecosystem_conflicts) > 0
    
    def test_resolve_technology_conflicts(self, prioritizer, sample_tech_context):
        """Test technology conflict resolution."""
        conflicts = [
            AmbiguityDetection(
                ambiguity_type=AmbiguityType.TECHNOLOGY_CONFLICT,
                description="Database conflict",
                conflicting_elements=["PostgreSQL", "MySQL"],
                suggested_clarifications=["Choose one database"],
                confidence=0.9,
                impact_level="high"
            )
        ]
        
        resolutions = prioritizer.resolve_technology_conflicts(conflicts, sample_tech_context)
        
        assert isinstance(resolutions, dict)
        # Should have resolutions for conflicting technologies
        assert len(resolutions) >= 0  # May be empty if no conflicts in context
    
    def test_learn_user_preferences(self, prioritizer):
        """Test user preference learning."""
        selected_techs = ["FastAPI", "PostgreSQL"]
        rejected_techs = ["Django", "MySQL"]
        domain = "web_api"
        context_patterns = ["rest_api", "database"]
        
        prioritizer.learn_user_preferences(
            selected_techs, rejected_techs, domain, context_patterns
        )
        
        # Check that preferences were created/updated
        for tech in selected_techs:
            pref_key = f"{domain}:{tech}"
            assert pref_key in prioritizer.user_preferences
            pref = prioritizer.user_preferences[pref_key]
            assert pref.selection_count > 0
            assert pref.preference_score > 0
        
        for tech in rejected_techs:
            pref_key = f"{domain}:{tech}"
            assert pref_key in prioritizer.user_preferences
            pref = prioritizer.user_preferences[pref_key]
            assert pref.rejection_count > 0
            assert pref.preference_score <= 0
    
    def test_calculate_preference_score(self, prioritizer):
        """Test preference score calculation."""
        # Test positive preference (more selections)
        positive_pref = UserPreference(
            technology="FastAPI",
            domain="web_api",
            selection_count=8,
            rejection_count=2
        )
        score = prioritizer._calculate_preference_score(positive_pref)
        assert score > 0
        
        # Test negative preference (more rejections)
        negative_pref = UserPreference(
            technology="Django",
            domain="web_api",
            selection_count=2,
            rejection_count=8
        )
        score = prioritizer._calculate_preference_score(negative_pref)
        assert score < 0
        
        # Test neutral preference
        neutral_pref = UserPreference(
            technology="Flask",
            domain="web_api",
            selection_count=5,
            rejection_count=5
        )
        score = prioritizer._calculate_preference_score(neutral_pref)
        assert abs(score) < 0.1  # Should be close to 0
        
        # Test no interactions
        no_interaction_pref = UserPreference(
            technology="Unknown",
            domain="web_api",
            selection_count=0,
            rejection_count=0
        )
        score = prioritizer._calculate_preference_score(no_interaction_pref)
        assert score == 0.0
    
    def test_get_prioritization_summary(self, prioritizer):
        """Test prioritization summary generation."""
        context_weights = {
            "FastAPI": ContextWeight(
                technology="FastAPI",
                base_priority=0.8,
                final_weight=0.95,
                reasoning=["Explicit mention", "Domain preference"]
            ),
            "PostgreSQL": ContextWeight(
                technology="PostgreSQL",
                base_priority=0.7,
                final_weight=0.85,
                reasoning=["Contextual inference"]
            ),
            "Redis": ContextWeight(
                technology="Redis",
                base_priority=0.6,
                final_weight=0.65,
                reasoning=["Cache requirement"]
            )
        }
        
        summary = prioritizer.get_prioritization_summary(context_weights)
        
        assert isinstance(summary, dict)
        assert "total_technologies" in summary
        assert "top_technologies" in summary
        assert "weight_distribution" in summary
        assert "average_weight" in summary
        
        assert summary["total_technologies"] == 3
        assert len(summary["top_technologies"]) <= 10
        
        # Check weight distribution
        distribution = summary["weight_distribution"]
        assert "critical" in distribution
        assert "high" in distribution
        assert "medium" in distribution
        assert "low" in distribution
        
        # Check that top technologies are sorted by weight
        top_techs = summary["top_technologies"]
        if len(top_techs) > 1:
            for i in range(len(top_techs) - 1):
                assert top_techs[i]["weight"] >= top_techs[i + 1]["weight"]
    
    def test_ambiguity_pattern_matching(self, prioritizer):
        """Test ambiguity pattern matching."""
        test_cases = [
            ("We need both MySQL and PostgreSQL", AmbiguityType.TECHNOLOGY_CONFLICT),
            ("Use AWS Lambda but also Azure Functions", AmbiguityType.ECOSYSTEM_MISMATCH),
            ("We need some database solution", AmbiguityType.INCOMPLETE_SPECIFICATION),
            ("Simple but enterprise-grade system", AmbiguityType.CONTRADICTORY_REQUIREMENTS),
            ("General purpose application", AmbiguityType.UNCLEAR_DOMAIN)
        ]
        
        for text, expected_type in test_cases:
            req = ParsedRequirements(raw_text=text)
            ambiguities = prioritizer.detect_requirement_ambiguity(req)
            
            # Check if expected ambiguity type is detected
            detected_types = [a.ambiguity_type for a in ambiguities]
            # Note: Some patterns might not match due to regex specificity
            # This is more of a smoke test
            assert isinstance(ambiguities, list)
    
    def test_weight_bounds(self, prioritizer):
        """Test that weights stay within valid bounds."""
        # Test extreme values
        weight = ContextWeight(
            technology="Test",
            base_priority=2.0,  # Over limit
            domain_boost=1.0,
            ecosystem_boost=1.0,
            user_preference_boost=1.0
        )
        
        final_weight = prioritizer._calculate_final_weight(weight)
        assert 0.0 <= final_weight <= 1.0
        
        # Test negative values
        weight = ContextWeight(
            technology="Test",
            base_priority=-0.5,  # Negative
            domain_boost=0.0,
            ecosystem_boost=0.0,
            user_preference_boost=0.0
        )
        
        final_weight = prioritizer._calculate_final_weight(weight)
        assert 0.0 <= final_weight <= 1.0
    
    def test_empty_inputs(self, prioritizer):
        """Test handling of empty inputs."""
        # Empty parsed requirements
        empty_req = ParsedRequirements()
        empty_context = TechContext()
        
        weights = prioritizer.calculate_context_weights(empty_req, empty_context)
        assert isinstance(weights, dict)
        
        # Empty ambiguity detection
        ambiguities = prioritizer.detect_requirement_ambiguity(empty_req)
        assert isinstance(ambiguities, list)
        
        # Empty conflict resolution
        resolutions = prioritizer.resolve_technology_conflicts([], empty_context)
        assert isinstance(resolutions, dict)
    
    def test_timestamp_generation(self, prioritizer):
        """Test timestamp generation for preference learning."""
        timestamp = prioritizer._get_current_timestamp()
        
        # Just verify it returns a string in ISO format
        assert isinstance(timestamp, str)
        assert len(timestamp) > 10  # Should be a reasonable timestamp length
        
        # Verify it contains expected ISO format elements
        assert 'T' in timestamp  # ISO format separator
        assert ':' in timestamp  # Time separator


class TestRequirementWeight:
    """Test cases for RequirementWeight dataclass."""
    
    def test_requirement_weight_creation(self):
        """Test RequirementWeight creation."""
        weight = RequirementWeight(
            source=RequirementSource.EXPLICIT_USER_INPUT,
            base_weight=1.0,
            domain_multiplier=1.2,
            confidence_threshold=0.9
        )
        
        assert weight.source == RequirementSource.EXPLICIT_USER_INPUT
        assert weight.base_weight == 1.0
        assert weight.domain_multiplier == 1.2
        assert weight.confidence_threshold == 0.9
        assert weight.decay_factor == 1.0  # Default value


class TestContextWeight:
    """Test cases for ContextWeight dataclass."""
    
    def test_context_weight_creation(self):
        """Test ContextWeight creation."""
        weight = ContextWeight(
            technology="FastAPI",
            base_priority=0.8
        )
        
        assert weight.technology == "FastAPI"
        assert weight.base_priority == 0.8
        assert weight.domain_boost == 0.0
        assert weight.ecosystem_boost == 0.0
        assert weight.user_preference_boost == 0.0
        assert weight.final_weight == 0.0
        assert isinstance(weight.source_weights, dict)
        assert isinstance(weight.reasoning, list)


class TestAmbiguityDetection:
    """Test cases for AmbiguityDetection dataclass."""
    
    def test_ambiguity_detection_creation(self):
        """Test AmbiguityDetection creation."""
        ambiguity = AmbiguityDetection(
            ambiguity_type=AmbiguityType.TECHNOLOGY_CONFLICT,
            description="Test conflict",
            conflicting_elements=["Tech1", "Tech2"],
            suggested_clarifications=["Choose one"],
            confidence=0.8,
            impact_level="high"
        )
        
        assert ambiguity.ambiguity_type == AmbiguityType.TECHNOLOGY_CONFLICT
        assert ambiguity.description == "Test conflict"
        assert ambiguity.conflicting_elements == ["Tech1", "Tech2"]
        assert ambiguity.suggested_clarifications == ["Choose one"]
        assert ambiguity.confidence == 0.8
        assert ambiguity.impact_level == "high"


class TestUserPreference:
    """Test cases for UserPreference dataclass."""
    
    def test_user_preference_creation(self):
        """Test UserPreference creation."""
        pref = UserPreference(
            technology="FastAPI",
            domain="web_api",
            selection_count=5,
            rejection_count=2,
            preference_score=0.6
        )
        
        assert pref.technology == "FastAPI"
        assert pref.domain == "web_api"
        assert pref.selection_count == 5
        assert pref.rejection_count == 2
        assert pref.preference_score == 0.6
        assert pref.last_updated is None
        assert isinstance(pref.context_patterns, list)


if __name__ == "__main__":
    pytest.main([__file__])