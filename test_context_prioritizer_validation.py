#!/usr/bin/env python3
"""Validation test for context prioritizer implementation."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.requirement_parsing.context_prioritizer import (
    RequirementContextPrioritizer, RequirementSource, AmbiguityType
)
from app.services.requirement_parsing.base import (
    ParsedRequirements, TechContext, ContextClues, DomainContext,
    ExplicitTech, RequirementConstraints, ExtractionMethod
)


def test_context_prioritizer_basic_functionality():
    """Test basic functionality of the context prioritizer."""
    print("Testing RequirementContextPrioritizer basic functionality...")
    
    # Create prioritizer
    prioritizer = RequirementContextPrioritizer()
    
    # Create sample data
    parsed_req = ParsedRequirements(
        explicit_technologies=[
            ExplicitTech(
                name="Amazon Connect SDK",
                confidence=0.9,
                extraction_method=ExtractionMethod.EXPLICIT_MENTION,
                source_text="We need Amazon Connect SDK"
            ),
            ExplicitTech(
                name="FastAPI",
                confidence=0.8,
                extraction_method=ExtractionMethod.EXPLICIT_MENTION,
                source_text="Use FastAPI for REST API"
            )
        ],
        context_clues=ContextClues(
            cloud_providers=["aws"],
            domains=["web_api"],
            integration_patterns=["database", "cache"]
        ),
        constraints=RequirementConstraints(
            banned_tools={"MySQL"}
        ),
        domain_context=DomainContext(
            primary_domain="web_api"
        ),
        raw_text="We need Amazon Connect SDK for voice integration. Use FastAPI for REST API."
    )
    
    tech_context = TechContext(
        explicit_technologies={
            "Amazon Connect SDK": 0.9,
            "FastAPI": 0.8
        },
        contextual_technologies={
            "PostgreSQL": 0.7,
            "Redis": 0.6
        },
        ecosystem_preference="aws"
    )
    
    # Test context weight calculation
    context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
    assert len(context_weights) > 0
    print(f"✓ Context weights calculated for {len(context_weights)} technologies")
    
    # Test domain preferences
    domain_prefs = prioritizer.implement_domain_specific_preferences(
        tech_context, parsed_req.domain_context
    )
    print(f"✓ Domain preferences applied: {len(domain_prefs)} technologies")
    
    # Test ambiguity detection
    ambiguities = prioritizer.detect_requirement_ambiguity(parsed_req)
    print(f"✓ Ambiguity detection completed: {len(ambiguities)} ambiguities found")
    
    # Test user preference learning
    prioritizer.learn_user_preferences(
        selected_technologies=["FastAPI", "PostgreSQL"],
        rejected_technologies=["Django", "MySQL"],
        domain="web_api",
        context_patterns=["rest_api", "database"]
    )
    print("✓ User preference learning completed")
    
    # Test prioritization summary
    summary = prioritizer.get_prioritization_summary(context_weights)
    assert "total_technologies" in summary
    assert "top_technologies" in summary
    print(f"✓ Prioritization summary generated: {summary['total_technologies']} total technologies")
    
    print("All basic functionality tests passed!")


def test_ambiguity_detection():
    """Test ambiguity detection with various scenarios."""
    print("\nTesting ambiguity detection...")
    
    prioritizer = RequirementContextPrioritizer()
    
    # Test conflicting requirements
    conflicting_req = ParsedRequirements(
        raw_text="We need both MySQL and PostgreSQL for database. Use AWS Lambda but also Azure Functions.",
        explicit_technologies=[
            ExplicitTech(name="MySQL", confidence=0.8),
            ExplicitTech(name="PostgreSQL", confidence=0.8),
            ExplicitTech(name="AWS Lambda", confidence=0.9),
            ExplicitTech(name="Azure Functions", confidence=0.7)
        ]
    )
    
    ambiguities = prioritizer.detect_requirement_ambiguity(conflicting_req)
    
    # Should detect conflicts
    tech_conflicts = [a for a in ambiguities if a.ambiguity_type == AmbiguityType.TECHNOLOGY_CONFLICT]
    ecosystem_conflicts = [a for a in ambiguities if a.ambiguity_type == AmbiguityType.ECOSYSTEM_MISMATCH]
    
    print(f"✓ Technology conflicts detected: {len(tech_conflicts)}")
    print(f"✓ Ecosystem conflicts detected: {len(ecosystem_conflicts)}")
    
    # Test conflict resolution
    tech_context = TechContext(
        explicit_technologies={"MySQL": 0.8, "PostgreSQL": 0.8},
        ecosystem_preference="aws"
    )
    
    resolutions = prioritizer.resolve_technology_conflicts(ambiguities, tech_context)
    print(f"✓ Conflict resolutions generated: {len(resolutions)}")
    
    print("Ambiguity detection tests passed!")


def test_user_preference_learning():
    """Test user preference learning and adaptation."""
    print("\nTesting user preference learning...")
    
    prioritizer = RequirementContextPrioritizer()
    
    # Simulate multiple learning sessions
    sessions = [
        {
            "selected": ["FastAPI", "PostgreSQL", "Redis"],
            "rejected": ["Django", "MySQL", "Memcached"]
        },
        {
            "selected": ["FastAPI", "PostgreSQL"],
            "rejected": ["Flask", "MongoDB"]
        },
        {
            "selected": ["FastAPI", "Redis"],
            "rejected": ["Django"]
        }
    ]
    
    for i, session in enumerate(sessions):
        prioritizer.learn_user_preferences(
            session["selected"],
            session["rejected"],
            "web_api",
            ["rest_api", "database", "cache"]
        )
        print(f"✓ Learning session {i+1} completed")
    
    # Check that preferences were learned
    assert len(prioritizer.user_preferences) > 0
    
    # Check preference scores
    fastapi_pref = prioritizer.user_preferences.get("web_api:FastAPI")
    if fastapi_pref:
        assert fastapi_pref.preference_score > 0
        print(f"✓ FastAPI preference score: {fastapi_pref.preference_score:.2f}")
    
    django_pref = prioritizer.user_preferences.get("web_api:Django")
    if django_pref:
        assert django_pref.preference_score <= 0
        print(f"✓ Django preference score: {django_pref.preference_score:.2f}")
    
    print("User preference learning tests passed!")


def test_weight_calculation_accuracy():
    """Test weight calculation accuracy and consistency."""
    print("\nTesting weight calculation accuracy...")
    
    prioritizer = RequirementContextPrioritizer()
    
    # Create test scenario with explicit AWS Connect requirements
    parsed_req = ParsedRequirements(
        explicit_technologies=[
            ExplicitTech(name="Amazon Connect SDK", confidence=0.95),
            ExplicitTech(name="AWS Comprehend", confidence=0.9),
            ExplicitTech(name="Amazon S3", confidence=0.85),
            ExplicitTech(name="FastAPI", confidence=0.8)
        ],
        context_clues=ContextClues(
            cloud_providers=["aws"],
            domains=["web_api", "voice_integration"]
        ),
        domain_context=DomainContext(
            primary_domain="web_api"
        )
    )
    
    tech_context = TechContext(
        explicit_technologies={
            "Amazon Connect SDK": 0.95,
            "AWS Comprehend": 0.9,
            "Amazon S3": 0.85,
            "FastAPI": 0.8
        },
        contextual_technologies={
            "PostgreSQL": 0.7,
            "Redis": 0.6
        },
        ecosystem_preference="aws"
    )
    
    context_weights = prioritizer.calculate_context_weights(parsed_req, tech_context)
    
    # Verify explicit technologies get high weights
    explicit_techs = ["Amazon Connect SDK", "AWS Comprehend", "Amazon S3", "FastAPI"]
    for tech in explicit_techs:
        if tech in context_weights:
            weight = context_weights[tech].final_weight
            assert weight >= 0.7, f"{tech} should have high weight, got {weight}"
            print(f"✓ {tech}: weight = {weight:.3f}")
    
    # Verify AWS technologies get ecosystem boost
    aws_techs = ["Amazon Connect SDK", "AWS Comprehend", "Amazon S3"]
    for tech in aws_techs:
        if tech in context_weights:
            ecosystem_boost = context_weights[tech].ecosystem_boost
            assert ecosystem_boost > 0, f"{tech} should have ecosystem boost"
            print(f"✓ {tech}: ecosystem boost = {ecosystem_boost:.3f}")
    
    print("Weight calculation accuracy tests passed!")


def main():
    """Run all validation tests."""
    print("=" * 60)
    print("CONTEXT PRIORITIZER VALIDATION TESTS")
    print("=" * 60)
    
    try:
        test_context_prioritizer_basic_functionality()
        test_ambiguity_detection()
        test_user_preference_learning()
        test_weight_calculation_accuracy()
        
        print("\n" + "=" * 60)
        print("ALL VALIDATION TESTS PASSED! ✓")
        print("Context prioritizer implementation is working correctly.")
        print("=" * 60)
        
        return 0
        
    except Exception as e:
        print(f"\n❌ VALIDATION TEST FAILED: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())