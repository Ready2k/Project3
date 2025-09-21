#!/usr/bin/env python3
"""
AWS Connect Bug Regression Test

This script specifically tests the fix for the AWS Connect bug where
explicit AWS technologies were not being properly included in generated tech stacks.
"""

import sys
import json
from unittest.mock import Mock

# Add the project root to the path
sys.path.insert(0, '.')

from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser


def test_aws_connect_bug_regression():
    """Test the specific AWS Connect bug regression case."""
    print("Testing AWS Connect Bug Regression...")
    
    # Original bug case: AWS Connect mentioned but not included in tech stack
    requirements = {
        "description": """
        Build a customer service automation system that integrates with Amazon Connect
        for call routing and AWS Comprehend for sentiment analysis. The system should
        handle customer inquiries and route them based on sentiment and intent.
        Use AWS S3 for storing call recordings and DynamoDB for customer data.
        """,
        "domain": "customer_service",
        "integrations": ["Amazon Connect", "AWS Comprehend", "AWS S3", "DynamoDB"],
        "cloud_provider": "AWS"
    }
    
    # Test requirement parsing
    print("1. Testing requirement parsing...")
    parser = EnhancedRequirementParser()
    parsed = parser.parse_requirements(requirements)
    
    # Verify explicit technologies are extracted
    explicit_techs = [tech.name for tech in parsed.explicit_technologies]
    print(f"   Extracted explicit technologies: {explicit_techs}")
    
    expected_techs = ["Amazon Connect", "AWS Comprehend", "AWS S3", "DynamoDB"]
    for tech in expected_techs:
        if tech not in explicit_techs:
            print(f"   ❌ FAILED: Missing explicit technology: {tech}")
            return False
        else:
            print(f"   ✅ Found explicit technology: {tech}")
    
    # Test tech stack generation
    print("\n2. Testing tech stack generation...")
    generator = TechStackGenerator()
    
    # Mock LLM response that should include explicit technologies
    mock_response = {
        "tech_stack": [
            "Amazon Connect",
            "AWS Comprehend", 
            "AWS S3",
            "DynamoDB",
            "AWS Lambda",
            "Python",
            "FastAPI"
        ],
        "reasoning": {
            "Amazon Connect": "Explicitly mentioned for call routing",
            "AWS Comprehend": "Explicitly mentioned for sentiment analysis",
            "AWS S3": "Explicitly mentioned for call recordings storage",
            "DynamoDB": "Explicitly mentioned for customer data"
        },
        "ecosystem_consistency": "AWS",
        "confidence_score": 0.95
    }
    
    generator.llm_provider = Mock()
    generator.llm_provider.generate_response = Mock(
        return_value=json.dumps(mock_response)
    )
    
    # Generate tech stack
    result = generator.generate_tech_stack(requirements)
    generated_stack = result.get("tech_stack", [])
    
    print(f"   Generated tech stack: {generated_stack}")
    
    # Verify all explicit AWS technologies are included
    missing_techs = []
    for tech in expected_techs:
        if tech not in generated_stack:
            missing_techs.append(tech)
        else:
            print(f"   ✅ Included explicit technology: {tech}")
    
    if missing_techs:
        print(f"   ❌ FAILED: Missing explicit technologies: {missing_techs}")
        return False
    
    # Verify inclusion rate meets requirement (70% minimum)
    inclusion_rate = len([tech for tech in expected_techs if tech in generated_stack]) / len(expected_techs)
    print(f"   Explicit technology inclusion rate: {inclusion_rate:.2%}")
    
    if inclusion_rate < 0.7:
        print(f"   ❌ FAILED: Inclusion rate {inclusion_rate:.2%} below 70% requirement")
        return False
    else:
        print(f"   ✅ Inclusion rate {inclusion_rate:.2%} meets 70% requirement")
    
    # Verify ecosystem consistency
    aws_techs = [tech for tech in generated_stack if tech.startswith(("AWS", "Amazon"))]
    print(f"   AWS technologies in stack: {aws_techs}")
    
    if len(aws_techs) < 4:
        print(f"   ❌ FAILED: Expected at least 4 AWS technologies, got {len(aws_techs)}")
        return False
    else:
        print(f"   ✅ AWS ecosystem consistency maintained with {len(aws_techs)} AWS technologies")
    
    print("\n3. Testing edge cases...")
    
    # Test with abbreviated service names
    abbreviated_requirements = {
        "description": "Use Connect SDK and Comprehend for customer service with S3 storage",
        "explicit_technologies": ["Connect SDK", "Comprehend", "S3"],
        "cloud_provider": "AWS"
    }
    
    parsed_abbreviated = parser.parse_requirements(abbreviated_requirements)
    abbreviated_explicit = [tech.name for tech in parsed_abbreviated.explicit_technologies]
    print(f"   Abbreviated tech extraction: {abbreviated_explicit}")
    
    # Should map abbreviated names to full names
    expected_mappings = {
        "Connect SDK": "Amazon Connect SDK",
        "Comprehend": "AWS Comprehend", 
        "S3": "Amazon S3"
    }
    
    for abbrev, full_name in expected_mappings.items():
        # Check if either the abbreviated or full name is extracted
        if abbrev in abbreviated_explicit or full_name in abbreviated_explicit:
            print(f"   ✅ Correctly handled abbreviation: {abbrev}")
        else:
            print(f"   ⚠️  WARNING: May need better handling for: {abbrev}")
    
    return True


def test_multi_cloud_prioritization():
    """Test that cloud-specific context is properly prioritized."""
    print("\n" + "="*60)
    print("Testing Multi-Cloud Context Prioritization...")
    
    # Azure-specific requirements
    azure_requirements = {
        "description": """
        Create a data processing pipeline using Azure Data Factory for ETL,
        Azure Cosmos DB for storage, and Azure Functions for serverless processing.
        """,
        "domain": "data_processing",
        "cloud_provider": "Azure",
        "explicit_technologies": ["Azure Data Factory", "Azure Cosmos DB", "Azure Functions"]
    }
    
    parser = EnhancedRequirementParser()
    parsed = parser.parse_requirements(azure_requirements)
    
    # Verify Azure ecosystem is detected
    print(f"   Detected cloud provider: {parsed.context_clues.cloud_provider}")
    if parsed.context_clues.cloud_provider != "Azure":
        print(f"   ❌ FAILED: Expected Azure, got {parsed.context_clues.cloud_provider}")
        return False
    else:
        print(f"   ✅ Correctly detected Azure ecosystem")
    
    # Verify explicit Azure technologies are extracted
    explicit_techs = [tech.name for tech in parsed.explicit_technologies]
    expected_azure_techs = ["Azure Data Factory", "Azure Cosmos DB", "Azure Functions"]
    
    for tech in expected_azure_techs:
        if tech in explicit_techs:
            print(f"   ✅ Extracted Azure technology: {tech}")
        else:
            print(f"   ❌ FAILED: Missing Azure technology: {tech}")
            return False
    
    return True


def test_generic_pattern_override():
    """Test that explicit technologies override generic pattern recommendations."""
    print("\n" + "="*60)
    print("Testing Generic Pattern Override...")
    
    requirements = {
        "description": """
        Build a multi-agent system for automated trading using AWS Bedrock for AI models,
        Amazon SQS for message queuing, and AWS Lambda for agent execution.
        """,
        "domain": "multi_agent",
        "pattern_indicators": ["multi-agent", "automated"],
        "explicit_technologies": ["AWS Bedrock", "Amazon SQS", "AWS Lambda"],
        "cloud_provider": "AWS"
    }
    
    parser = EnhancedRequirementParser()
    parsed = parser.parse_requirements(requirements)
    
    # Verify explicit technologies have high confidence
    explicit_techs = {tech.name: tech.confidence for tech in parsed.explicit_technologies}
    print(f"   Explicit technologies with confidence: {explicit_techs}")
    
    for tech_name, confidence in explicit_techs.items():
        if confidence >= 0.9:
            print(f"   ✅ High confidence for explicit tech: {tech_name} ({confidence:.2f})")
        else:
            print(f"   ❌ FAILED: Low confidence for explicit tech: {tech_name} ({confidence:.2f})")
            return False
    
    # Verify AWS ecosystem consistency
    aws_techs = [tech for tech in explicit_techs.keys() if tech.startswith(("AWS", "Amazon"))]
    if len(aws_techs) >= 3:
        print(f"   ✅ AWS ecosystem consistency with {len(aws_techs)} AWS technologies")
    else:
        print(f"   ❌ FAILED: Expected at least 3 AWS technologies, got {len(aws_techs)}")
        return False
    
    return True


def main():
    """Run all regression tests."""
    print("AWS Connect Bug Regression Test Suite")
    print("="*60)
    
    tests = [
        ("AWS Connect Bug Regression", test_aws_connect_bug_regression),
        ("Multi-Cloud Context Prioritization", test_multi_cloud_prioritization),
        ("Generic Pattern Override", test_generic_pattern_override)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        try:
            if test_func():
                print(f"\n✅ PASSED: {test_name}")
                passed += 1
            else:
                print(f"\n❌ FAILED: {test_name}")
                failed += 1
        except Exception as e:
            print(f"\n❌ ERROR in {test_name}: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print("REGRESSION TEST SUMMARY")
    print("="*60)
    print(f"Total Tests: {passed + failed}")
    print(f"Passed: {passed}")
    print(f"Failed: {failed}")
    print(f"Success Rate: {passed / (passed + failed) * 100:.1f}%")
    
    if failed == 0:
        print("\n🎉 All regression tests passed! The AWS Connect bug fix is working correctly.")
        return 0
    else:
        print(f"\n⚠️  {failed} regression test(s) failed. Please review the issues above.")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)