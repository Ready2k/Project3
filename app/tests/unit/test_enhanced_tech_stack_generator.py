"""Unit tests for enhanced TechStackGenerator methods."""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, Any

from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.base import (
    ParsedRequirements, ExplicitTech, ContextClues, RequirementConstraints,
    DomainContext, TechContext, ExtractionMethod
)
from app.services.validation.models import CompatibilityResult, TechnologyConflict, ConflictType, ConflictSeverity, ValidationReport, EcosystemConsistencyResult
from app.llm.base import LLMProvider
from datetime import datetime


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, response: Any = None):
        self.response = response or {"tech_stack": ["FastAPI", "PostgreSQL"]}
    
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
def mock_generator():
    """Create TechStackGenerator with mocked dependencies."""
    with patch('app.services.tech_stack_generator.require_service') as mock_require:
        mock_logger = Mock()
        mock_require.return_value = mock_logger
        
        # Also patch the require_service calls in the enhanced components
        with patch('app.services.requirement_parsing.enhanced_parser.require_service', return_value=mock_logger), \
             patch('app.services.requirement_parsing.context_extractor.require_service', return_value=mock_logger), \
             patch('app.services.catalog.intelligent_manager.require_service', return_value=mock_logger), \
             patch('app.services.context_aware_prompt_generator.require_service', return_value=mock_logger), \
             patch('app.services.validation.compatibility_validator.require_service', return_value=mock_logger):
            
            generator = TechStackGenerator(llm_provider=MockLLMProvider())
            
            # Mock the enhanced components
            generator.enhanced_parser = Mock()
            generator.context_extractor = Mock()
            generator.catalog_manager = Mock()
            generator.prompt_generator = Mock()
            generator.compatibility_validator = Mock()
            
            return generator


class TestEnhancedTechStackGeneratorMethods:
    """Test individual methods of enhanced TechStackGenerator."""
    
    @pytest.mark.asyncio
    async def test_parse_requirements_enhanced(self, mock_generator):
        """Test enhanced requirement parsing."""
        requirements = {
            "description": "Build API with FastAPI",
            "domain": "web_api"
        }
        constraints = {"banned_tools": ["MongoDB"]}
        
        # Mock parser response
        mock_parsed = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(
                    name="FastAPI",
                    canonical_name="FastAPI",
                    confidence=0.95,
                    extraction_method=ExtractionMethod.NER,
                    source_text="FastAPI",
                    position=15,
                    context="Build API with FastAPI"
                )
            ],
            context_clues=ContextClues(domains=["web_api"]),
            constraints=RequirementConstraints(banned_tools={"MongoDB"}),
            domain_context=DomainContext(primary_domain="web_api"),
            confidence_score=0.85
        )
        mock_generator.enhanced_parser.parse_requirements.return_value = mock_parsed
        
        result = await mock_generator._parse_requirements_enhanced(requirements, constraints)
        
        # Verify parser was called with merged requirements
        mock_generator.enhanced_parser.parse_requirements.assert_called_once()
        call_args = mock_generator.enhanced_parser.parse_requirements.call_args[0][0]
        assert call_args["description"] == "Build API with FastAPI"
        assert call_args["constraints"] == constraints
        
        # Verify result
        assert result == mock_parsed
        assert len(result.explicit_technologies) == 1
        assert result.explicit_technologies[0].name == "FastAPI"
    
    @pytest.mark.asyncio
    async def test_generate_context_aware_llm_tech_stack(self, mock_generator):
        """Test context-aware LLM tech stack generation."""
        # Setup test data
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(name="FastAPI", canonical_name="FastAPI", confidence=0.95,
                           extraction_method=ExtractionMethod.NER, source_text="FastAPI", position=0)
            ],
            context_clues=ContextClues(),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(),
            confidence_score=0.8
        )
        
        tech_context = TechContext(
            explicit_technologies={"FastAPI": 0.95},
            contextual_technologies={"PostgreSQL": 0.8},
            domain_context=DomainContext(primary_domain="web_api"),
            ecosystem_preference="open_source",
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        prioritized_techs = {"FastAPI": 0.95, "PostgreSQL": 0.8}
        matches = []
        
        # Mock prompt generator
        mock_generator.prompt_generator.generate_tech_stack_prompt.return_value = "test prompt"
        mock_generator.prompt_generator.validate_prompt.return_value = Mock(
            is_valid=True, issues=[], suggestions=[]
        )
        
        # Mock LLM response
        mock_generator.llm_provider.response = {
            "tech_stack": [
                {"name": "FastAPI", "reason": "Explicit mention"},
                {"name": "PostgreSQL", "reason": "Database need"}
            ]
        }
        
        with patch('app.utils.audit.log_llm_call') as mock_log:
            result = await mock_generator._generate_context_aware_llm_tech_stack(
                parsed_req, tech_context, prioritized_techs, matches
            )
        
        # Verify prompt generation
        mock_generator.prompt_generator.generate_tech_stack_prompt.assert_called_once_with(
            tech_context, parsed_req, prioritized_techs, matches
        )
        
        # Verify prompt validation
        mock_generator.prompt_generator.validate_prompt.assert_called_once()
        
        # Verify LLM call logging
        mock_log.assert_called_once()
        
        # Verify result
        assert result == ["FastAPI", "PostgreSQL"]
        assert mock_generator.generation_metrics['context_aware_selections'] == 1
    
    @pytest.mark.asyncio
    async def test_validate_and_enforce_explicit_inclusion(self, mock_generator):
        """Test explicit technology inclusion enforcement."""
        # Test case where inclusion rate is below 70%
        tech_stack = ["FastAPI", "Nginx"]  # Only 1 out of 3 explicit techs
        
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(name="FastAPI", canonical_name="FastAPI", confidence=0.95,
                           extraction_method=ExtractionMethod.NER, source_text="FastAPI", position=0),
                ExplicitTech(name="PostgreSQL", canonical_name="PostgreSQL", confidence=0.90,
                           extraction_method=ExtractionMethod.NER, source_text="PostgreSQL", position=10),
                ExplicitTech(name="Redis", canonical_name="Redis", confidence=0.85,
                           extraction_method=ExtractionMethod.NER, source_text="Redis", position=20)
            ],
            context_clues=ContextClues(),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(),
            confidence_score=0.8
        )
        
        tech_context = TechContext(
            explicit_technologies={"FastAPI": 0.95, "PostgreSQL": 0.90, "Redis": 0.85},
            contextual_technologies={},
            domain_context=DomainContext(),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        # Mock catalog manager to return True for technology lookup
        mock_generator.catalog_manager.lookup_technology.return_value = True
        
        result = await mock_generator._validate_and_enforce_explicit_inclusion(
            tech_stack, parsed_req, tech_context
        )
        
        # Should add missing explicit technologies to reach 70% threshold
        explicit_tech_names = {"FastAPI", "PostgreSQL", "Redis"}
        included_explicit = set(result) & explicit_tech_names
        inclusion_rate = len(included_explicit) / len(explicit_tech_names)
        
        assert inclusion_rate >= 0.7, f"Inclusion rate {inclusion_rate:.2%} should be >= 70%"
        assert "FastAPI" in result  # Original explicit tech should remain
        assert len(result) > len(tech_stack)  # Should have added technologies
    
    @pytest.mark.asyncio
    async def test_validate_and_enforce_explicit_inclusion_no_explicit_techs(self, mock_generator):
        """Test explicit inclusion enforcement when no explicit technologies exist."""
        tech_stack = ["FastAPI", "PostgreSQL"]
        
        parsed_req = ParsedRequirements(
            explicit_technologies=[],  # No explicit technologies
            context_clues=ContextClues(),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(),
            confidence_score=0.5
        )
        
        tech_context = TechContext(
            explicit_technologies={},
            contextual_technologies={"FastAPI": 0.8, "PostgreSQL": 0.7},
            domain_context=DomainContext(),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        result = await mock_generator._validate_and_enforce_explicit_inclusion(
            tech_stack, parsed_req, tech_context
        )
        
        # Should return original tech stack unchanged
        assert result == tech_stack
    
    @pytest.mark.asyncio
    async def test_auto_add_missing_technologies(self, mock_generator):
        """Test automatic addition of missing technologies to catalog."""
        tech_stack = ["NewFramework", "PostgreSQL"]
        tech_context = TechContext(
            explicit_technologies={"NewFramework": 0.9},
            contextual_technologies={"PostgreSQL": 0.8},
            domain_context=DomainContext(primary_domain="web_api"),
            ecosystem_preference="open_source",
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        # Mock catalog manager
        mock_generator.catalog_manager.lookup_technology.side_effect = lambda name: name != "NewFramework"
        mock_generator.catalog_manager.auto_add_technology.return_value = Mock()
        
        await mock_generator._auto_add_missing_technologies(tech_stack, tech_context)
        
        # Verify auto-addition was called for missing technology
        mock_generator.catalog_manager.auto_add_technology.assert_called_once_with(
            "NewFramework", 
            {
                'source': 'llm_generation',
                'domain': 'web_api',
                'ecosystem': 'open_source',
                'generation_timestamp': pytest.approx(str, abs=1)  # Approximate timestamp match
            }
        )
        
        # Verify metrics were updated
        assert mock_generator.generation_metrics['catalog_auto_additions'] == 1
    
    @pytest.mark.asyncio
    async def test_auto_add_missing_technologies_disabled(self, mock_generator):
        """Test that auto-addition is skipped when disabled."""
        mock_generator.auto_update_catalog = False
        
        tech_stack = ["NewFramework"]
        tech_context = TechContext(
            explicit_technologies={},
            contextual_technologies={},
            domain_context=DomainContext(),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        await mock_generator._auto_add_missing_technologies(tech_stack, tech_context)
        
        # Verify auto-addition was not called
        mock_generator.catalog_manager.auto_add_technology.assert_not_called()
    
    @pytest.mark.asyncio
    async def test_perform_final_validation(self, mock_generator):
        """Test final compatibility validation."""
        tech_stack = ["AWS Lambda", "Azure Functions"]  # Incompatible ecosystem mix
        tech_context = TechContext(
            explicit_technologies={},
            contextual_technologies={},
            domain_context=DomainContext(),
            ecosystem_preference="aws",
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        # Mock validation result with suggested fix
        from app.services.validation.models import ValidationReport, EcosystemConsistencyResult
        from datetime import datetime
        
        validation_result = ValidationReport(
            original_tech_stack=tech_stack.copy(),
            validated_tech_stack=["AWS Lambda"],  # After applying fix
            compatibility_result=CompatibilityResult(
                is_compatible=False,
                overall_score=0.6,
                conflicts=[TechnologyConflict(
                    tech1="AWS Lambda",
                    tech2="Azure Functions",
                    conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
                    severity=ConflictSeverity.MEDIUM,
                    description="Mixed AWS and Azure technologies",
                    explanation="Mixed cloud providers can cause integration issues"
                )],
                ecosystem_result=EcosystemConsistencyResult(
                    is_consistent=False,
                    primary_ecosystem=None,
                    ecosystem_distribution={"aws": 1, "azure": 1},
                    mixed_ecosystem_technologies=["AWS Lambda", "Azure Functions"],
                    recommendations=["Choose single cloud provider"]
                ),
                validated_technologies=["AWS Lambda"],
                removed_technologies=["Azure Functions"],
                suggestions=["Use AWS Lambda instead of Azure Functions"]
            ),
            validation_timestamp=datetime.now(),
            context_priority={},
            inclusion_explanations={},
            exclusion_explanations={},
            alternative_suggestions={}
        )
        
        mock_generator.compatibility_validator.validate_tech_stack.return_value = validation_result
        
        result = await mock_generator._perform_final_validation(tech_stack, tech_context)
        
        # Verify validation was called
        mock_generator.compatibility_validator.validate_tech_stack.assert_called_once_with(
            tech_stack, tech_context.priority_weights
        )
        
        # Should return the validated tech stack from the report
        assert result == validation_result.validated_tech_stack
    
    @pytest.mark.asyncio
    async def test_perform_final_validation_remove_action(self, mock_generator):
        """Test final validation with remove action."""
        tech_stack = ["FastAPI", "IncompatibleTech"]
        tech_context = TechContext(
            explicit_technologies={},
            contextual_technologies={},
            domain_context=DomainContext(),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        # Mock validation result with remove action
        validation_result = ValidationReport(
            original_tech_stack=tech_stack.copy(),
            validated_tech_stack=["FastAPI"],  # IncompatibleTech removed
            compatibility_result=CompatibilityResult(
                is_compatible=False,
                overall_score=0.5,
                conflicts=[TechnologyConflict(
                    tech1="IncompatibleTech",
                    tech2="FastAPI",
                    conflict_type=ConflictType.ARCHITECTURE_MISMATCH,
                    severity=ConflictSeverity.HIGH,
                    description="IncompatibleTech is not compatible",
                    explanation="Technology architecture mismatch"
                )],
                ecosystem_result=EcosystemConsistencyResult(
                    is_consistent=True,
                    primary_ecosystem=None,
                    ecosystem_distribution={},
                    mixed_ecosystem_technologies=[],
                    recommendations=[]
                ),
                validated_technologies=["FastAPI"],
                removed_technologies=["IncompatibleTech"],
                suggestions=["Remove IncompatibleTech"]
            ),
            validation_timestamp=datetime.now(),
            context_priority={},
            inclusion_explanations={},
            exclusion_explanations={},
            alternative_suggestions={}
        )
        
        mock_generator.compatibility_validator.validate_tech_stack.return_value = validation_result
        
        result = await mock_generator._perform_final_validation(tech_stack, tech_context)
        
        # Should return the validated tech stack (IncompatibleTech removed)
        assert result == ["FastAPI"]
        assert "IncompatibleTech" not in result
        assert "FastAPI" in result
    
    @pytest.mark.asyncio
    async def test_generate_enhanced_rule_based_tech_stack(self, mock_generator):
        """Test enhanced rule-based tech stack generation."""
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(name="FastAPI", canonical_name="FastAPI", confidence=0.95,
                           extraction_method=ExtractionMethod.NER, source_text="FastAPI", position=0)
            ],
            context_clues=ContextClues(),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(),
            confidence_score=0.8
        )
        
        tech_context = TechContext(
            explicit_technologies={"FastAPI": 0.95},
            contextual_technologies={"PostgreSQL": 0.8, "Redis": 0.7, "Docker": 0.6},
            domain_context=DomainContext(primary_domain="web_api"),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools={"MongoDB"},
            priority_weights={}
        )
        
        prioritized_techs = {"FastAPI": 0.95, "PostgreSQL": 0.8, "Redis": 0.7}
        matches = [Mock(blended_score=0.8, tech_stack=["Nginx"], constraints=None)]
        
        result = await mock_generator._generate_enhanced_rule_based_tech_stack(
            parsed_req, tech_context, prioritized_techs, matches
        )
        
        # Should include explicit technologies
        assert "FastAPI" in result
        
        # Should include contextual technologies (sorted by confidence)
        assert "PostgreSQL" in result
        
        # Should not include banned technologies
        assert "MongoDB" not in result
        
        # Should limit total technologies
        assert len(result) <= 12
    
    def test_parse_llm_response_structured(self, mock_generator):
        """Test parsing structured LLM response."""
        response = {
            "tech_stack": [
                {"name": "FastAPI", "reason": "API framework", "confidence": 0.9},
                {"name": "PostgreSQL", "reason": "Database", "confidence": 0.8}
            ]
        }
        
        result = mock_generator._parse_llm_response(response)
        
        assert result == ["FastAPI", "PostgreSQL"]
    
    def test_parse_llm_response_simple_list(self, mock_generator):
        """Test parsing simple list LLM response."""
        response = {"tech_stack": ["FastAPI", "PostgreSQL", "Redis"]}
        
        result = mock_generator._parse_llm_response(response)
        
        assert result == ["FastAPI", "PostgreSQL", "Redis"]
    
    def test_parse_llm_response_json_string(self, mock_generator):
        """Test parsing JSON string LLM response."""
        response = '{"tech_stack": ["FastAPI", "PostgreSQL"]}'
        
        result = mock_generator._parse_llm_response(response)
        
        assert result == ["FastAPI", "PostgreSQL"]
    
    def test_parse_llm_response_text_extraction(self, mock_generator):
        """Test extracting technologies from text response."""
        response = """
        Here are the recommended technologies:
        - FastAPI for the web framework
        - PostgreSQL for the database
        - Redis for caching
        """
        
        result = mock_generator._parse_llm_response(response)
        
        # Should extract some technologies from text
        assert len(result) > 0
        # Exact extraction depends on regex patterns, so we just verify it returns something
    
    def test_parse_llm_response_invalid(self, mock_generator):
        """Test parsing invalid LLM response."""
        response = {"invalid": "response"}
        
        result = mock_generator._parse_llm_response(response)
        
        # Should handle gracefully and return something
        assert isinstance(result, list)
    
    def test_update_generation_metrics(self, mock_generator):
        """Test generation metrics update."""
        # Setup initial state
        mock_generator.generation_metrics = {
            'total_generations': 2,
            'explicit_tech_inclusion_rate': 0.8,
            'context_aware_selections': 0,
            'catalog_auto_additions': 0
        }
        
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(name="FastAPI", canonical_name="FastAPI", confidence=0.95,
                           extraction_method=ExtractionMethod.NER, source_text="FastAPI", position=0),
                ExplicitTech(name="PostgreSQL", canonical_name="PostgreSQL", confidence=0.90,
                           extraction_method=ExtractionMethod.NER, source_text="PostgreSQL", position=10)
            ],
            context_clues=ContextClues(),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(),
            confidence_score=0.8
        )
        
        final_stack = ["FastAPI", "Redis"]  # 1 out of 2 explicit techs = 50%
        
        mock_generator._update_generation_metrics(parsed_req, final_stack)
        
        # Should update the running average: ((0.8 * 1) + 0.5) / 2 = 0.65
        expected_avg = ((0.8 * 1) + 0.5) / 2
        assert abs(mock_generator.generation_metrics['explicit_tech_inclusion_rate'] - expected_avg) < 0.01
    
    def test_get_generation_metrics(self, mock_generator):
        """Test getting generation metrics."""
        # Set some test metrics
        test_metrics = {
            'total_generations': 5,
            'explicit_tech_inclusion_rate': 0.75,
            'context_aware_selections': 3,
            'catalog_auto_additions': 2
        }
        mock_generator.generation_metrics = test_metrics
        
        result = mock_generator.get_generation_metrics()
        
        # Should return a copy of the metrics
        assert result == test_metrics
        assert result is not mock_generator.generation_metrics  # Should be a copy