#!/usr/bin/env python3
"""Integration test for enhanced requirement parsing infrastructure."""

from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser
from app.services.requirement_parsing.context_extractor import TechnologyContextExtractor


def test_aws_connect_scenario():
    """Test the AWS Connect scenario that was failing."""
    print("=== Testing AWS Connect Scenario ===")
    
    parser = EnhancedRequirementParser()
    requirements = {
        'description': 'Integrate with Amazon Connect SDK to handle customer calls and use AWS Comprehend for sentiment analysis'
    }
    
    result = parser.parse_requirements(requirements)
    
    print(f"✓ Extracted {len(result.explicit_technologies)} explicit technologies:")
    for tech in result.explicit_technologies:
        print(f"  - {tech.canonical_name} (confidence: {tech.confidence:.2f}, method: {tech.extraction_method.value})")
    
    print(f"✓ Cloud providers identified: {result.context_clues.cloud_providers}")
    print(f"✓ Overall confidence score: {result.confidence_score:.2f}")
    
    # Verify key requirements
    tech_names = [tech.canonical_name for tech in result.explicit_technologies]
    assert 'Amazon Connect SDK' in tech_names, "Should extract Amazon Connect SDK"
    assert 'AWS Comprehend' in tech_names, "Should extract AWS Comprehend"
    assert 'aws' in result.context_clues.cloud_providers, "Should identify AWS as cloud provider"
    assert result.confidence_score > 0.7, f"Should have high confidence, got {result.confidence_score}"
    
    print("✓ AWS Connect scenario test passed!\n")


def test_multi_cloud_scenario():
    """Test a multi-cloud scenario."""
    print("=== Testing Multi-Cloud Scenario ===")
    
    parser = EnhancedRequirementParser()
    requirements = {
        'description': 'Build a web API using FastAPI, deploy on AWS Lambda, store data in Azure Cosmos DB, and monitor with Google Cloud Monitoring'
    }
    
    result = parser.parse_requirements(requirements)
    
    print(f"✓ Extracted {len(result.explicit_technologies)} explicit technologies:")
    for tech in result.explicit_technologies:
        print(f"  - {tech.canonical_name} (confidence: {tech.confidence:.2f})")
    
    print(f"✓ Cloud providers: {result.context_clues.cloud_providers}")
    print(f"✓ Domains: {result.context_clues.domains}")
    print(f"✓ Programming languages: {result.context_clues.programming_languages}")
    
    # Should identify multiple cloud providers
    assert len(result.context_clues.cloud_providers) >= 2, "Should identify multiple cloud providers"
    assert 'web_api' in result.context_clues.domains, "Should identify web API domain"
    
    print("✓ Multi-cloud scenario test passed!\n")


def test_context_extraction():
    """Test context extraction and prioritization."""
    print("=== Testing Context Extraction ===")
    
    parser = EnhancedRequirementParser()
    context_extractor = TechnologyContextExtractor()
    
    requirements = {
        'description': 'Build a scalable machine learning pipeline using Python, FastAPI, PostgreSQL, and Redis for caching',
        'constraints': {
            'banned_tools': ['selenium'],
            'required_integrations': ['database', 'cache']
        }
    }
    
    parsed_req = parser.parse_requirements(requirements)
    tech_context = context_extractor.build_context(parsed_req)
    priorities = context_extractor.prioritize_technologies(tech_context)
    
    print(f"✓ Explicit technologies: {list(tech_context.explicit_technologies.keys())}")
    print(f"✓ Contextual technologies: {list(tech_context.contextual_technologies.keys())}")
    print(f"✓ Ecosystem preference: {tech_context.ecosystem_preference}")
    print(f"✓ Integration requirements: {tech_context.integration_requirements}")
    print(f"✓ Banned tools: {tech_context.banned_tools}")
    
    print("✓ Top prioritized technologies:")
    sorted_priorities = sorted(priorities.items(), key=lambda x: x[1], reverse=True)
    for tech, priority in sorted_priorities[:5]:
        print(f"  - {tech}: {priority:.2f}")
    
    # Verify explicit technologies have high priority
    for tech in tech_context.explicit_technologies:
        assert priorities.get(tech, 0) >= 0.8, f"{tech} should have high priority"
    
    # Verify banned tools are excluded
    for banned in tech_context.banned_tools:
        assert banned not in priorities, f"Banned tool {banned} should not be in priorities"
    
    print("✓ Context extraction test passed!\n")


def test_confidence_scoring():
    """Test confidence scoring accuracy."""
    print("=== Testing Confidence Scoring ===")
    
    parser = EnhancedRequirementParser()
    
    # High confidence scenario
    high_conf_req = {
        'description': 'Use FastAPI, PostgreSQL, and Redis with AWS deployment'
    }
    high_result = parser.parse_requirements(high_conf_req)
    
    # Low confidence scenario
    low_conf_req = {
        'description': 'Build something'
    }
    low_result = parser.parse_requirements(low_conf_req)
    
    print(f"✓ High confidence scenario: {high_result.confidence_score:.2f}")
    print(f"✓ Low confidence scenario: {low_result.confidence_score:.2f}")
    
    assert high_result.confidence_score > low_result.confidence_score, "High confidence should be higher than low confidence"
    assert high_result.confidence_score > 0.6, "High confidence scenario should have good confidence"
    
    print("✓ Confidence scoring test passed!\n")


def test_alias_resolution():
    """Test technology alias resolution."""
    print("=== Testing Alias Resolution ===")
    
    parser = EnhancedRequirementParser()
    requirements = {
        'description': 'Use fastapi for API, connect to postgres database, cache with redis, and deploy with docker'
    }
    
    result = parser.parse_requirements(requirements)
    
    print(f"✓ Extracted technologies from aliases:")
    for tech in result.explicit_technologies:
        print(f"  - {tech.canonical_name} (from: {tech.source_text})")
    
    tech_names = [tech.canonical_name for tech in result.explicit_technologies]
    assert 'FastAPI' in tech_names, "Should resolve 'fastapi' to 'FastAPI'"
    assert 'PostgreSQL' in tech_names, "Should resolve 'postgres' to 'PostgreSQL'"
    assert 'Redis' in tech_names, "Should resolve 'redis' to 'Redis'"
    assert 'Docker' in tech_names, "Should resolve 'docker' to 'Docker'"
    
    print("✓ Alias resolution test passed!\n")


def main():
    """Run all integration tests."""
    print("Running Enhanced Requirement Parsing Integration Tests\n")
    
    try:
        test_aws_connect_scenario()
        test_multi_cloud_scenario()
        test_context_extraction()
        test_confidence_scoring()
        test_alias_resolution()
        
        print("🎉 All integration tests passed!")
        print("\nKey capabilities demonstrated:")
        print("✓ Technology name extraction using NER and pattern matching")
        print("✓ Confidence scoring system for extracted technologies")
        print("✓ Context clue identification (cloud providers, domains, patterns)")
        print("✓ Technology alias resolution with fuzzy matching")
        print("✓ Context-aware technology prioritization")
        print("✓ Ecosystem preference inference")
        print("✓ Constraint handling (banned tools, required integrations)")
        print("✓ AWS Connect SDK scenario working correctly")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        raise


if __name__ == "__main__":
    main()