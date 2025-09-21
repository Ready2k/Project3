"""Test core enhanced functionality without complex mocking."""

import asyncio
import sys
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.base import (
    ParsedRequirements, ExplicitTech, ContextClues, RequirementConstraints,
    DomainContext, TechContext, ExtractionMethod
)


def test_parse_llm_response():
    """Test LLM response parsing functionality."""
    print("Testing LLM response parsing...")
    
    # Create a minimal generator instance for testing
    generator = TechStackGenerator.__new__(TechStackGenerator)
    
    # Test structured response
    structured_response = {
        "tech_stack": [
            {"name": "FastAPI", "reason": "API framework"},
            {"name": "PostgreSQL", "reason": "Database"}
        ]
    }
    result = generator._parse_llm_response(structured_response)
    assert result == ["FastAPI", "PostgreSQL"]
    print("✓ Structured response parsing works")
    
    # Test simple list response
    list_response = {"tech_stack": ["FastAPI", "PostgreSQL", "Redis"]}
    result = generator._parse_llm_response(list_response)
    assert result == ["FastAPI", "PostgreSQL", "Redis"]
    print("✓ Simple list response parsing works")
    
    # Test string response with JSON
    json_string = '{"tech_stack": ["FastAPI", "PostgreSQL"]}'
    result = generator._parse_llm_response(json_string)
    assert result == ["FastAPI", "PostgreSQL"]
    print("✓ JSON string response parsing works")
    
    # Test plain text response
    text_response = "- FastAPI\n- PostgreSQL\n- Redis"
    result = generator._parse_llm_response(text_response)
    assert len(result) > 0  # Should extract some technologies
    print("✓ Text response parsing works")
    
    print("✓ All LLM response parsing tests passed!")


def test_update_generation_metrics():
    """Test generation metrics update functionality."""
    print("Testing generation metrics update...")
    
    # Create a minimal generator instance
    generator = TechStackGenerator.__new__(TechStackGenerator)
    generator.generation_metrics = {
        'total_generations': 2,
        'explicit_tech_inclusion_rate': 0.8,
        'context_aware_selections': 0,
        'catalog_auto_additions': 0
    }
    
    # Create test data
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
    
    # Should update the running average: ((0.8 * 1) + 0.5) / 2 = 0.65
    expected_avg = ((0.8 * 1) + 0.5) / 2
    actual_avg = generator.generation_metrics['explicit_tech_inclusion_rate']
    
    assert abs(actual_avg - expected_avg) < 0.01
    print(f"✓ Metrics updated correctly: {actual_avg:.3f} ≈ {expected_avg:.3f}")


async def test_explicit_inclusion_enforcement():
    """Test explicit technology inclusion enforcement."""
    print("Testing explicit technology inclusion enforcement...")
    
    # Create a minimal generator instance
    generator = TechStackGenerator.__new__(TechStackGenerator)
    generator.auto_update_catalog = True
    
    # Mock catalog manager
    class MockCatalogManager:
        def lookup_technology(self, name):
            return True  # All technologies exist
    
    generator.catalog_manager = MockCatalogManager()
    
    # Mock logger
    class MockLogger:
        def info(self, msg): pass
        def warning(self, msg): pass
    
    generator.logger = MockLogger()
    
    # Test case where inclusion rate is below 70%
    tech_stack = ["FastAPI", "Nginx"]  # Only 1 out of 3 explicit techs
    original_length = len(tech_stack)
    
    parsed_req = ParsedRequirements(
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
        tech_stack, parsed_req, tech_context
    )
    
    # Should add missing explicit technologies to reach 70% threshold
    explicit_tech_names = {"FastAPI", "PostgreSQL", "Redis"}
    included_explicit = set(result) & explicit_tech_names
    inclusion_rate = len(included_explicit) / len(explicit_tech_names)
    
    print(f"Original stack: {tech_stack}")
    print(f"Enhanced stack: {result}")
    print(f"Inclusion rate: {inclusion_rate:.2%}")
    
    assert inclusion_rate >= 0.7, f"Inclusion rate {inclusion_rate:.2%} should be >= 70%"
    assert "FastAPI" in result  # Original explicit tech should remain
    assert len(result) > original_length  # Should have added technologies
    
    print("✓ Explicit technology inclusion enforcement works!")


def test_get_generation_metrics():
    """Test getting generation metrics."""
    print("Testing generation metrics retrieval...")
    
    # Create a minimal generator instance
    generator = TechStackGenerator.__new__(TechStackGenerator)
    
    # Set some test metrics
    test_metrics = {
        'total_generations': 5,
        'explicit_tech_inclusion_rate': 0.75,
        'context_aware_selections': 3,
        'catalog_auto_additions': 2
    }
    generator.generation_metrics = test_metrics
    
    result = generator.get_generation_metrics()
    
    # Should return a copy of the metrics
    assert result == test_metrics
    assert result is not generator.generation_metrics  # Should be a copy
    
    print("✓ Generation metrics retrieval works!")


async def main():
    """Run all tests."""
    print("Running enhanced TechStackGenerator core functionality tests...\n")
    
    try:
        test_parse_llm_response()
        print()
        
        test_update_generation_metrics()
        print()
        
        await test_explicit_inclusion_enforcement()
        print()
        
        test_get_generation_metrics()
        print()
        
        print("🎉 All core functionality tests passed!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False
    
    return True


if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)