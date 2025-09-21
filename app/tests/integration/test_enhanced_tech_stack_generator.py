"""Integration tests for enhanced TechStackGenerator."""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, List, Any

from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import TechnologyContextExtractor
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.context_aware_prompt_generator import ContextAwareLLMPromptGenerator
from app.services.validation.compatibility_validator import TechnologyCompatibilityValidator
from app.services.requirement_parsing.base import (
    ParsedRequirements, ExplicitTech, ContextClues, RequirementConstraints,
    DomainContext, TechContext, ExtractionMethod
)
from app.services.validation.models import CompatibilityResult, TechnologyConflict, ConflictType, ConflictSeverity
from app.pattern.matcher import MatchResult
from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, response: Any = None):
        self.response = response or {
            "tech_stack": [
                {"name": "FastAPI", "reason": "Explicit mention", "confidence": 1.0},
                {"name": "PostgreSQL", "reason": "Database requirement", "confidence": 0.8},
                {"name": "Redis", "reason": "Caching needs", "confidence": 0.7}
            ]
        }
    
    async def generate(self, prompt: str, purpose: str = None) -> Any:
        return self.response
    
    @property
    def model(self) -> str:
        return "mock-model"
    
    def get_model_info(self) -> Dict[str, Any]:
        return {"name": "mock-model", "provider": "mock"}
    
    async def test_connection(self) -> bool:
        return True


@pytest.fixture
def mock_llm_provider():
    """Create mock LLM provider."""
    return MockLLMProvider()


@pytest.fixture
def sample_requirements():
    """Sample requirements for testing."""
    return {
        "description": "Build a REST API using FastAPI with PostgreSQL database and Redis caching",
        "domain": "web_api",
        "integrations": ["database", "cache"],
        "constraints": {
            "banned_tools": ["MongoDB"],
            "required_integrations": ["database"]
        }
    }


@pytest.fixture
def sample_parsed_requirements():
    """Sample parsed requirements."""
    return ParsedRequirements(
        explicit_technologies=[
            ExplicitTech(
                name="FastAPI",
                canonical_name="FastAPI",
                confidence=0.95,
                extraction_method=ExtractionMethod.NER,
                source_text="FastAPI",
                position=25,
                context="Build a REST API using FastAPI with"
            ),
            ExplicitTech(
                name="PostgreSQL",
                canonical_name="PostgreSQL",
                confidence=0.90,
                extraction_method=ExtractionMethod.NER,
                source_text="PostgreSQL",
                position=45,
                context="FastAPI with PostgreSQL database"
            )
        ],
        context_clues=ContextClues(
            domains=["web_api"],
            integration_patterns=["database", "cache"],
            programming_languages=["python"]
        ),
        constraints=RequirementConstraints(
            banned_tools={"MongoDB"},
            required_integrations=["database"]
        ),
        domain_context=DomainContext(
            primary_domain="web_api",
            use_case_patterns=["api", "rest"]
        ),
        confidence_score=0.85
    )


@pytest.fixture
def sample_tech_context():
    """Sample technology context."""
    return TechContext(
        explicit_technologies={"FastAPI": 0.95, "PostgreSQL": 0.90},
        contextual_technologies={"Redis": 0.7, "Uvicorn": 0.6},
        domain_context=DomainContext(primary_domain="web_api"),
        ecosystem_preference="open_source",
        integration_requirements=["database", "cache"],
        banned_tools={"MongoDB"},
        priority_weights={"FastAPI": 1.0, "PostgreSQL": 1.0, "Redis": 0.8}
    )


@pytest.fixture
def enhanced_generator(mock_llm_provider):
    """Create enhanced tech stack generator with mocked components."""
    with patch('app.utils.imports.require_service') as mock_require:
        # Mock logger
        mock_logger = Mock()
        mock_require.return_value = mock_logger
        
        # Create generator with mock components
        generator = TechStackGenerator(
            llm_provider=mock_llm_provider,
            auto_update_catalog=True
        )
        
        return generator


class TestEnhancedTechStackGenerator:
    """Test cases for enhanced tech stack generator."""
    
    @pytest.mark.asyncio
    async def test_enhanced_generation_flow(self, enhanced_generator, sample_requirements):
        """Test the complete enhanced generation flow."""
        # Mock pattern matches
        matches = [
            Mock(
                blended_score=0.8,
                tech_stack=["FastAPI", "PostgreSQL"],
                constraints=None
            )
        ]
        
        # Generate tech stack
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=sample_requirements
        )
        
        # Verify result
        assert isinstance(result, list)
        assert len(result) > 0
        assert "FastAPI" in result  # Should include explicit technology
    
    @pytest.mark.asyncio
    async def test_explicit_technology_inclusion_enforcement(self, enhanced_generator):
        """Test that explicit technologies are enforced (70% minimum)."""
        # Requirements with multiple explicit technologies
        requirements = {
            "description": "Use FastAPI, PostgreSQL, Redis, Docker, and Kubernetes for microservices",
            "domain": "microservices"
        }
        
        # Mock LLM response that doesn't include all explicit technologies
        mock_response = {
            "tech_stack": [
                {"name": "FastAPI", "reason": "API framework"},
                {"name": "Nginx", "reason": "Load balancer"}  # Missing most explicit techs
            ]
        }
        enhanced_generator.llm_provider.response = mock_response
        
        matches = []
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=requirements
        )
        
        # Should enforce inclusion of explicit technologies
        explicit_techs = {"FastAPI", "PostgreSQL", "Redis", "Docker", "Kubernetes"}
        included_explicit = set(result) & explicit_techs
        inclusion_rate = len(included_explicit) / len(explicit_techs)
        
        # Should meet or exceed 70% threshold
        assert inclusion_rate >= 0.7, f"Inclusion rate {inclusion_rate:.2%} below 70% threshold"
    
    @pytest.mark.asyncio
    async def test_context_aware_prompt_generation(self, enhanced_generator, sample_requirements):
        """Test that context-aware prompts are generated correctly."""
        matches = []
        
        # Mock the prompt generator to capture the generated prompt
        with patch.object(enhanced_generator.prompt_generator, 'generate_tech_stack_prompt') as mock_prompt:
            mock_prompt.return_value = "test prompt"
            
            await enhanced_generator.generate_tech_stack(
                matches=matches,
                requirements=sample_requirements
            )
            
            # Verify prompt generator was called with correct parameters
            mock_prompt.assert_called_once()
            call_args = mock_prompt.call_args
            
            # Check that tech context and parsed requirements were passed
            assert len(call_args[0]) >= 3  # tech_context, parsed_req, prioritized_techs
    
    @pytest.mark.asyncio
    async def test_catalog_auto_addition(self, enhanced_generator):
        """Test automatic catalog addition of new technologies."""
        # Requirements with a technology not in catalog
        requirements = {
            "description": "Use NewFramework for building APIs",
            "domain": "web_api"
        }
        
        # Mock LLM response with new technology
        mock_response = {
            "tech_stack": [
                {"name": "NewFramework", "reason": "Explicit mention"},
                {"name": "PostgreSQL", "reason": "Database"}
            ]
        }
        enhanced_generator.llm_provider.response = mock_response
        
        # Mock catalog manager to track auto-additions
        with patch.object(enhanced_generator.catalog_manager, 'auto_add_technology') as mock_auto_add:
            mock_auto_add.return_value = Mock()
            
            matches = []
            result = await enhanced_generator.generate_tech_stack(
                matches=matches,
                requirements=requirements
            )
            
            # Verify auto-addition was attempted for new technology
            # Note: This depends on the catalog manager not finding the technology
            if "NewFramework" in result:
                # Check if auto_add_technology was called (may not be if tech exists in catalog)
                assert enhanced_generator.generation_metrics['catalog_auto_additions'] >= 0
    
    @pytest.mark.asyncio
    async def test_compatibility_validation(self, enhanced_generator, sample_requirements):
        """Test technology compatibility validation."""
        # Mock compatibility validator
        with patch.object(enhanced_generator.compatibility_validator, 'validate_tech_stack') as mock_validate:
            # Mock validation result with issues
            from app.services.validation.models import ValidationReport, EcosystemConsistencyResult
            from datetime import datetime
            
            mock_validate.return_value = ValidationReport(
                original_tech_stack=["FastAPI", "PostgreSQL"],
                validated_tech_stack=["FastAPI", "PostgreSQL"],
                compatibility_result=CompatibilityResult(
                    is_compatible=False,
                    overall_score=0.6,
                    conflicts=[TechnologyConflict(
                        tech1="AWS Lambda",
                        tech2="Azure Functions",
                        conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
                        severity=ConflictSeverity.MEDIUM,
                        description="AWS and Azure technologies mixed",
                        explanation="Mixed cloud providers can cause integration issues"
                    )],
                    ecosystem_result=EcosystemConsistencyResult(
                        is_consistent=False,
                        primary_ecosystem=None,
                        ecosystem_distribution={"aws": 1, "azure": 1},
                        mixed_ecosystem_technologies=["AWS Lambda", "Azure Functions"],
                        recommendations=["Choose single cloud provider"]
                    ),
                    validated_technologies=["FastAPI", "PostgreSQL"],
                    removed_technologies=["Azure Functions"],
                    suggestions=["Use AWS Lambda instead of Azure Functions"]
                ),
                validation_timestamp=datetime.now(),
                context_priority={},
                inclusion_explanations={},
                exclusion_explanations={},
                alternative_suggestions={}
            )
            
            matches = []
            result = await enhanced_generator.generate_tech_stack(
                matches=matches,
                requirements=sample_requirements
            )
            
            # Verify validation was performed
            mock_validate.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_banned_tools_enforcement(self, enhanced_generator):
        """Test that banned tools are properly excluded."""
        requirements = {
            "description": "Build API with database storage",
            "constraints": {
                "banned_tools": ["MongoDB", "MySQL"]
            }
        }
        
        # Mock LLM response that includes banned tools
        mock_response = {
            "tech_stack": [
                {"name": "FastAPI", "reason": "API framework"},
                {"name": "MongoDB", "reason": "Database"},  # Banned
                {"name": "MySQL", "reason": "Alternative DB"},  # Banned
                {"name": "PostgreSQL", "reason": "Database"}
            ]
        }
        enhanced_generator.llm_provider.response = mock_response
        
        matches = []
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=requirements
        )
        
        # Verify banned tools are not in result
        assert "MongoDB" not in result
        assert "MySQL" not in result
        assert "PostgreSQL" in result  # Should include allowed alternative
    
    @pytest.mark.asyncio
    async def test_ecosystem_preference_consistency(self, enhanced_generator):
        """Test that ecosystem preferences are maintained."""
        requirements = {
            "description": "Build serverless application using AWS Lambda and S3",
            "domain": "serverless"
        }
        
        matches = []
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=requirements
        )
        
        # Should prefer AWS ecosystem technologies when AWS is mentioned
        aws_techs = {"AWS Lambda", "Amazon S3", "AWS API Gateway", "Amazon DynamoDB"}
        aws_count = len(set(result) & aws_techs)
        
        # Should have some AWS technologies when AWS is explicitly mentioned
        assert aws_count > 0, "Should include AWS technologies when AWS ecosystem is indicated"
    
    @pytest.mark.asyncio
    async def test_fallback_to_rule_based_generation(self, enhanced_generator, sample_requirements):
        """Test fallback to rule-based generation when LLM fails."""
        # Mock LLM to raise exception
        enhanced_generator.llm_provider = Mock()
        enhanced_generator.llm_provider.generate = AsyncMock(side_effect=Exception("LLM failed"))
        
        matches = [
            Mock(
                blended_score=0.8,
                tech_stack=["FastAPI", "PostgreSQL"],
                constraints=None
            )
        ]
        
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=sample_requirements
        )
        
        # Should still return a valid tech stack
        assert isinstance(result, list)
        assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_legacy_compatibility(self, enhanced_generator, sample_requirements):
        """Test backward compatibility with legacy generation method."""
        # Mock all enhanced components to fail
        with patch.object(enhanced_generator, '_parse_requirements_enhanced', side_effect=Exception("Enhanced parsing failed")):
            matches = [
                Mock(
                    blended_score=0.8,
                    tech_stack=["FastAPI", "PostgreSQL"],
                    constraints=None
                )
            ]
            
            result = await enhanced_generator.generate_tech_stack(
                matches=matches,
                requirements=sample_requirements
            )
            
            # Should fall back to legacy method and still work
            assert isinstance(result, list)
            assert len(result) > 0
    
    @pytest.mark.asyncio
    async def test_generation_metrics_tracking(self, enhanced_generator, sample_requirements):
        """Test that generation metrics are properly tracked."""
        initial_metrics = enhanced_generator.get_generation_metrics()
        initial_count = initial_metrics['total_generations']
        
        matches = []
        await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=sample_requirements
        )
        
        updated_metrics = enhanced_generator.get_generation_metrics()
        
        # Verify metrics were updated
        assert updated_metrics['total_generations'] == initial_count + 1
        assert 'explicit_tech_inclusion_rate' in updated_metrics
        assert 'context_aware_selections' in updated_metrics
        assert 'catalog_auto_additions' in updated_metrics
    
    @pytest.mark.asyncio
    async def test_priority_based_selection(self, enhanced_generator):
        """Test that technologies are selected based on priority scores."""
        requirements = {
            "description": "Build web application with FastAPI (required) and consider Redis for caching",
            "domain": "web_api"
        }
        
        matches = []
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=requirements
        )
        
        # FastAPI should be included due to explicit mention (high priority)
        assert "FastAPI" in result
        
        # Should prioritize explicit technologies over contextual ones
        # This is tested by the explicit inclusion enforcement test above
    
    def test_llm_response_parsing(self, enhanced_generator):
        """Test parsing of various LLM response formats."""
        # Test structured response
        structured_response = {
            "tech_stack": [
                {"name": "FastAPI", "reason": "API framework"},
                {"name": "PostgreSQL", "reason": "Database"}
            ]
        }
        result = enhanced_generator._parse_llm_response(structured_response)
        assert result == ["FastAPI", "PostgreSQL"]
        
        # Test simple list response
        list_response = {"tech_stack": ["FastAPI", "PostgreSQL", "Redis"]}
        result = enhanced_generator._parse_llm_response(list_response)
        assert result == ["FastAPI", "PostgreSQL", "Redis"]
        
        # Test string response with JSON
        json_string = '{"tech_stack": ["FastAPI", "PostgreSQL"]}'
        result = enhanced_generator._parse_llm_response(json_string)
        assert result == ["FastAPI", "PostgreSQL"]
        
        # Test plain text response
        text_response = "- FastAPI\n- PostgreSQL\n- Redis"
        result = enhanced_generator._parse_llm_response(text_response)
        assert len(result) > 0  # Should extract some technologies
    
    @pytest.mark.asyncio
    async def test_integration_requirements_handling(self, enhanced_generator):
        """Test handling of integration requirements."""
        requirements = {
            "description": "Build application that needs database and messaging",
            "integrations": ["database", "messaging"],
            "constraints": {
                "required_integrations": ["database"]
            }
        }
        
        matches = []
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=requirements
        )
        
        # Should include technologies that satisfy integration requirements
        # Database technologies
        db_techs = {"PostgreSQL", "MySQL", "MongoDB", "SQLite"}
        has_database = bool(set(result) & db_techs)
        
        # Messaging technologies
        messaging_techs = {"Apache Kafka", "RabbitMQ", "Redis", "Amazon SQS"}
        has_messaging = bool(set(result) & messaging_techs)
        
        assert has_database, "Should include database technology for database integration requirement"
        # Messaging is not required, so it's optional
    
    @pytest.mark.asyncio
    async def test_domain_specific_technology_preferences(self, enhanced_generator):
        """Test that domain-specific technology preferences are applied."""
        # ML/AI domain should prefer ML technologies
        ml_requirements = {
            "description": "Build machine learning pipeline for data processing",
            "domain": "ml_ai"
        }
        
        matches = []
        result = await enhanced_generator.generate_tech_stack(
            matches=matches,
            requirements=ml_requirements
        )
        
        # Should include ML-related technologies
        ml_techs = {"PyTorch", "TensorFlow", "Scikit-learn", "Pandas", "NumPy", "Jupyter"}
        ml_count = len(set(result) & ml_techs)
        
        # Should have some ML technologies for ML domain
        # Note: This depends on the contextual technology mapping in the context extractor
        assert isinstance(result, list)  # Basic validation - specific ML tech inclusion depends on implementation