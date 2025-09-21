"""Simple test for enhanced TechStackGenerator functionality."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from unittest.mock import Mock, AsyncMock, patch
from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.base import (
    ParsedRequirements, ExplicitTech, ContextClues, RequirementConstraints,
    DomainContext, TechContext, ExtractionMethod
)
from app.llm.base import LLMProvider


class MockLLMProvider(LLMProvider):
    """Mock LLM provider for testing."""
    
    def __init__(self, response=None):
        self.response = response or {"tech_stack": ["FastAPI", "PostgreSQL"]}
    
    async def generate(self, prompt: str, purpose: str = None):
        return self.response
    
    @property
    def model(self) -> str:
        return "mock-model"
    
    def get_model_info(self):
        return {"name": "mock-model", "provider": "mock"}
    
    async def test_connection(self) -> bool:
        return True


async def test_enhanced_generation_flow():
    """Test the enhanced generation flow."""
    print("Testing enhanced tech stack generation flow...")
    
    # Mock all the service dependencies
    with patch('app.services.tech_stack_generator.require_service') as mock_require, \
         patch('app.services.requirement_parsing.enhanced_parser.require_service'), \
         patch('app.services.requirement_parsing.context_extractor.require_service'), \
         patch('app.services.catalog.intelligent_manager.require_service'), \
         patch('app.services.context_aware_prompt_generator.require_service'), \
         patch('app.services.validation.compatibility_validator.require_service'):
        
        # Mock logger
        mock_logger = Mock()
        mock_require.return_value = mock_logger
        
        # Create generator
        generator = TechStackGenerator(llm_provider=MockLLMProvider())
        
        # Mock the enhanced components with proper return values
        mock_parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(
                    name="FastAPI",
                    canonical_name="FastAPI",
                    confidence=0.95,
                    extraction_method=ExtractionMethod.NER_EXTRACTION,
                    source_text="FastAPI",
                    position=0,
                    context="Build API with FastAPI"
                )
            ],
            context_clues=ContextClues(domains=["web_api"]),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(primary_domain="web_api"),
            confidence_score=0.85
        )
        
        mock_tech_context = TechContext(
            explicit_technologies={"FastAPI": 0.95},
            contextual_technologies={"PostgreSQL": 0.8},
            domain_context=DomainContext(primary_domain="web_api"),
            ecosystem_preference="open_source",
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={"FastAPI": 1.0, "PostgreSQL": 0.8}
        )
        
        # Mock the enhanced parser
        generator.enhanced_parser.parse_requirements = Mock(return_value=mock_parsed_req)
        
        # Mock the context extractor
        generator.context_extractor.build_context = Mock(return_value=mock_tech_context)
        generator.context_extractor.prioritize_technologies = Mock(return_value={"FastAPI": 0.95, "PostgreSQL": 0.8})
        
        # Mock the prompt generator
        generator.prompt_generator.generate_tech_stack_prompt = Mock(return_value="test prompt")
        generator.prompt_generator.validate_prompt = Mock(return_value=Mock(is_valid=True, issues=[], suggestions=[]))
        
        # Mock the catalog manager
        generator.catalog_manager.lookup_technology = Mock(return_value=True)
        generator.catalog_manager.auto_add_technology = Mock(return_value=Mock())
        
        # Mock the compatibility validator
        from app.services.validation.models import ValidationReport, CompatibilityResult, EcosystemConsistencyResult
        from datetime import datetime
        
        mock_validation_report = ValidationReport(
            original_tech_stack=["FastAPI", "PostgreSQL"],
            validated_tech_stack=["FastAPI", "PostgreSQL"],
            compatibility_result=CompatibilityResult(
                is_compatible=True,
                overall_score=0.9,
                conflicts=[],
                ecosystem_result=EcosystemConsistencyResult(
                    is_consistent=True,
                    primary_ecosystem=None,
                    ecosystem_distribution={},
                    mixed_ecosystem_technologies=[],
                    recommendations=[]
                ),
                validated_technologies=["FastAPI", "PostgreSQL"],
                removed_technologies=[],
                suggestions=[]
            ),
            validation_timestamp=datetime.now(),
            context_priority={},
            inclusion_explanations={},
            exclusion_explanations={},
            alternative_suggestions={}
        )
        
        generator.compatibility_validator.validate_tech_stack = Mock(return_value=mock_validation_report)
        
        # Mock audit logging
        with patch('app.utils.audit.log_llm_call') as mock_log:
            # Test the generation
            requirements = {
                "description": "Build API with FastAPI and PostgreSQL",
                "domain": "web_api"
            }
            
            matches = []  # No pattern matches for this test
            
            result = await generator.generate_tech_stack(
                matches=matches,
                requirements=requirements
            )
            
            # Verify results
            print(f"Generated tech stack: {result}")
            assert isinstance(result, list)
            assert len(result) > 0
            assert "FastAPI" in result
            
            # Verify the enhanced flow was used
            generator.enhanced_parser.parse_requirements.assert_called_once()
            generator.context_extractor.build_context.assert_called_once()
            generator.context_extractor.prioritize_technologies.assert_called_once()
            generator.prompt_generator.generate_tech_stack_prompt.assert_called_once()
            generator.compatibility_validator.validate_tech_stack.assert_called_once()
            
            print("✓ Enhanced generation flow test passed!")


async def test_explicit_technology_inclusion():
    """Test explicit technology inclusion enforcement."""
    print("Testing explicit technology inclusion enforcement...")
    
    with patch('app.services.tech_stack_generator.require_service') as mock_require, \
         patch('app.services.requirement_parsing.enhanced_parser.require_service'), \
         patch('app.services.requirement_parsing.context_extractor.require_service'), \
         patch('app.services.catalog.intelligent_manager.require_service'), \
         patch('app.services.context_aware_prompt_generator.require_service'), \
         patch('app.services.validation.compatibility_validator.require_service'):
        
        mock_logger = Mock()
        mock_require.return_value = mock_logger
        
        # Create generator with LLM that doesn't include all explicit technologies
        mock_llm = MockLLMProvider({
            "tech_stack": [
                {"name": "FastAPI", "reason": "API framework"},
                {"name": "Nginx", "reason": "Load balancer"}  # Missing PostgreSQL and Redis
            ]
        })
        
        generator = TechStackGenerator(llm_provider=mock_llm)
        
        # Mock parsed requirements with multiple explicit technologies
        mock_parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(name="FastAPI", canonical_name="FastAPI", confidence=0.95,
                           extraction_method=ExtractionMethod.NER_EXTRACTION, source_text="FastAPI", position=0),
                ExplicitTech(name="PostgreSQL", canonical_name="PostgreSQL", confidence=0.90,
                           extraction_method=ExtractionMethod.NER_EXTRACTION, source_text="PostgreSQL", position=10),
                ExplicitTech(name="Redis", canonical_name="Redis", confidence=0.85,
                           extraction_method=ExtractionMethod.NER_EXTRACTION, source_text="Redis", position=20)
            ],
            context_clues=ContextClues(),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(),
            confidence_score=0.8
        )
        
        # Test the explicit inclusion enforcement
        tech_stack = ["FastAPI", "Nginx"]  # Only 1 out of 3 explicit techs
        
        # Mock catalog manager to return True for technology lookup
        generator.catalog_manager = Mock()
        generator.catalog_manager.lookup_technology = Mock(return_value=True)
        
        tech_context = TechContext(
            explicit_technologies={"FastAPI": 0.95, "PostgreSQL": 0.90, "Redis": 0.85},
            contextual_technologies={},
            domain_context=DomainContext(),
            ecosystem_preference=None,
            integration_requirements=[],
            banned_tools=set(),
            priority_weights={}
        )
        
        result = await generator._validate_and_enforce_explicit_inclusion(
            tech_stack, mock_parsed_req, tech_context
        )
        
        # Should add missing explicit technologies to reach 70% threshold
        explicit_tech_names = {"FastAPI", "PostgreSQL", "Redis"}
        included_explicit = set(result) & explicit_tech_names
        inclusion_rate = len(included_explicit) / len(explicit_tech_names)
        
        print(f"Inclusion rate: {inclusion_rate:.2%}")
        print(f"Result tech stack: {result}")
        
        assert inclusion_rate >= 0.7, f"Inclusion rate {inclusion_rate:.2%} should be >= 70%"
        assert "FastAPI" in result  # Original explicit tech should remain
        assert len(result) > len(tech_stack)  # Should have added technologies
        
        print("✓ Explicit technology inclusion test passed!")


async def test_generation_metrics():
    """Test generation metrics tracking."""
    print("Testing generation metrics tracking...")
    
    with patch('app.services.tech_stack_generator.require_service') as mock_require, \
         patch('app.services.requirement_parsing.enhanced_parser.require_service'), \
         patch('app.services.requirement_parsing.context_extractor.require_service'), \
         patch('app.services.catalog.intelligent_manager.require_service'), \
         patch('app.services.context_aware_prompt_generator.require_service'), \
         patch('app.services.validation.compatibility_validator.require_service'):
        
        mock_logger = Mock()
        mock_require.return_value = mock_logger
        
        generator = TechStackGenerator(llm_provider=MockLLMProvider())
        
        # Test initial metrics
        initial_metrics = generator.get_generation_metrics()
        print(f"Initial metrics: {initial_metrics}")
        
        assert 'total_generations' in initial_metrics
        assert 'explicit_tech_inclusion_rate' in initial_metrics
        assert 'context_aware_selections' in initial_metrics
        assert 'catalog_auto_additions' in initial_metrics
        
        # Test metrics update
        parsed_req = ParsedRequirements(
            explicit_technologies=[
                ExplicitTech(name="FastAPI", canonical_name="FastAPI", confidence=0.95,
                           extraction_method=ExtractionMethod.NER_EXTRACTION, source_text="FastAPI", position=0),
                ExplicitTech(name="PostgreSQL", canonical_name="PostgreSQL", confidence=0.90,
                           extraction_method=ExtractionMethod.NER_EXTRACTION, source_text="PostgreSQL", position=10)
            ],
            context_clues=ContextClues(),
            constraints=RequirementConstraints(),
            domain_context=DomainContext(),
            confidence_score=0.8
        )
        
        final_stack = ["FastAPI", "Redis"]  # 1 out of 2 explicit techs = 50%
        
        generator._update_generation_metrics(parsed_req, final_stack)
        
        updated_metrics = generator.get_generation_metrics()
        print(f"Updated metrics: {updated_metrics}")
        
        # Verify metrics were updated
        assert updated_metrics != initial_metrics
        
        print("✓ Generation metrics test passed!")


async def main():
    """Run all tests."""
    print("Running enhanced TechStackGenerator tests...\n")
    
    try:
        await test_enhanced_generation_flow()
        print()
        
        await test_explicit_technology_inclusion()
        print()
        
        await test_generation_metrics()
        print()
        
        print("🎉 All tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)