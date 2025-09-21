#!/usr/bin/env python3
"""
Example demonstrating the Technology Compatibility Validation System.

This example shows how to use the TechnologyCompatibilityValidator to:
1. Validate technology stacks for compatibility
2. Detect and resolve conflicts
3. Check ecosystem consistency
4. Generate comprehensive validation reports
"""

import sys
import json
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.services.validation.compatibility_validator import TechnologyCompatibilityValidator
from app.services.validation.models import ConflictSeverity, ConflictType
from app.services.catalog.intelligent_manager import IntelligentCatalogManager


def setup_example_catalog():
    """Set up an example catalog for demonstration."""
    # Create a temporary catalog manager for the example
    catalog_manager = IntelligentCatalogManager()
    
    # Add some example technologies if they don't exist
    example_technologies = [
        {
            "name": "AWS S3",
            "context": {"ecosystem": "aws", "category": "storage"},
            "confidence": 1.0
        },
        {
            "name": "Azure Blob Storage", 
            "context": {"ecosystem": "azure", "category": "storage"},
            "confidence": 1.0
        },
        {
            "name": "FastAPI",
            "context": {"ecosystem": "open_source", "category": "frameworks"},
            "confidence": 1.0
        },
        {
            "name": "PostgreSQL",
            "context": {"ecosystem": "open_source", "category": "databases"},
            "confidence": 1.0
        },
        {
            "name": "MySQL",
            "context": {"ecosystem": "open_source", "category": "databases"},
            "confidence": 1.0
        }
    ]
    
    for tech in example_technologies:
        # Check if technology already exists
        existing = catalog_manager.lookup_technology(tech["name"])
        if not existing:
            catalog_manager.auto_add_technology(
                tech["name"], 
                tech["context"], 
                tech["confidence"]
            )
    
    return catalog_manager


def example_1_consistent_stack():
    """Example 1: Validate a consistent technology stack."""
    print("=" * 60)
    print("EXAMPLE 1: Consistent Technology Stack")
    print("=" * 60)
    
    catalog_manager = setup_example_catalog()
    validator = TechnologyCompatibilityValidator(catalog_manager)
    
    # Define a consistent tech stack (all open source)
    tech_stack = ["FastAPI", "PostgreSQL", "Redis"]
    context_priority = {
        "FastAPI": 0.9,      # High priority - explicitly mentioned
        "PostgreSQL": 0.8,   # High priority - database requirement
        "Redis": 0.7         # Medium priority - caching solution
    }
    
    print(f"Original Tech Stack: {tech_stack}")
    print(f"Context Priority: {context_priority}")
    print()
    
    # Validate the tech stack
    report = validator.validate_tech_stack(tech_stack, context_priority)
    
    # Display results
    print("VALIDATION RESULTS:")
    print(f"✅ Compatible: {report.compatibility_result.is_compatible}")
    print(f"📊 Overall Score: {report.compatibility_result.overall_score:.2f}")
    print(f"🏗️ Validated Stack: {report.validated_tech_stack}")
    print(f"❌ Removed Technologies: {report.compatibility_result.removed_technologies}")
    print(f"⚠️ Conflicts Detected: {len(report.compatibility_result.conflicts)}")
    print(f"🌐 Ecosystem Consistent: {report.compatibility_result.ecosystem_result.is_consistent}")
    
    if report.compatibility_result.ecosystem_result.primary_ecosystem:
        print(f"🎯 Primary Ecosystem: {report.compatibility_result.ecosystem_result.primary_ecosystem.value}")
    
    print()


def example_2_conflicting_stack():
    """Example 2: Validate a conflicting technology stack."""
    print("=" * 60)
    print("EXAMPLE 2: Conflicting Technology Stack")
    print("=" * 60)
    
    catalog_manager = setup_example_catalog()
    validator = TechnologyCompatibilityValidator(catalog_manager)
    
    # Define a conflicting tech stack (mixed cloud providers)
    tech_stack = ["AWS S3", "Azure Blob Storage", "FastAPI", "PostgreSQL", "MySQL"]
    context_priority = {
        "AWS S3": 0.9,              # High priority - explicitly mentioned
        "Azure Blob Storage": 0.3,  # Low priority - alternative option
        "FastAPI": 0.8,             # High priority - framework choice
        "PostgreSQL": 0.7,          # Medium priority - preferred database
        "MySQL": 0.4                # Low priority - alternative database
    }
    
    print(f"Original Tech Stack: {tech_stack}")
    print(f"Context Priority: {context_priority}")
    print()
    
    # Validate the tech stack
    report = validator.validate_tech_stack(tech_stack, context_priority)
    
    # Display results
    print("VALIDATION RESULTS:")
    print(f"✅ Compatible: {report.compatibility_result.is_compatible}")
    print(f"📊 Overall Score: {report.compatibility_result.overall_score:.2f}")
    print(f"🏗️ Validated Stack: {report.validated_tech_stack}")
    print(f"❌ Removed Technologies: {report.compatibility_result.removed_technologies}")
    print(f"⚠️ Conflicts Detected: {len(report.compatibility_result.conflicts)}")
    print(f"🌐 Ecosystem Consistent: {report.compatibility_result.ecosystem_result.is_consistent}")
    
    # Show conflicts
    if report.compatibility_result.conflicts:
        print("\nCONFLICTS DETECTED:")
        for i, conflict in enumerate(report.compatibility_result.conflicts, 1):
            print(f"  {i}. {conflict.severity.value.upper()}: {conflict.description}")
            print(f"     Technologies: {conflict.tech1} ↔ {conflict.tech2}")
            print(f"     Resolution: {conflict.suggested_resolution}")
            print()
    
    # Show removal explanations
    if report.exclusion_explanations:
        print("REMOVAL EXPLANATIONS:")
        for tech, explanation in report.exclusion_explanations.items():
            print(f"  ❌ {tech}: {explanation}")
            if tech in report.alternative_suggestions:
                alternatives = report.alternative_suggestions[tech]
                print(f"     💡 Alternatives: {', '.join(alternatives)}")
        print()
    
    # Show ecosystem analysis
    ecosystem_result = report.compatibility_result.ecosystem_result
    if ecosystem_result.ecosystem_distribution:
        print("ECOSYSTEM DISTRIBUTION:")
        for ecosystem, count in ecosystem_result.ecosystem_distribution.items():
            print(f"  🏷️ {ecosystem}: {count} technologies")
        print()
    
    if ecosystem_result.recommendations:
        print("RECOMMENDATIONS:")
        for rec in ecosystem_result.recommendations:
            print(f"  💡 {rec}")
        print()


def example_3_custom_compatibility_rules():
    """Example 3: Add custom compatibility rules."""
    print("=" * 60)
    print("EXAMPLE 3: Custom Compatibility Rules")
    print("=" * 60)
    
    catalog_manager = setup_example_catalog()
    validator = TechnologyCompatibilityValidator(catalog_manager)
    
    # Add custom compatibility rules
    print("Adding custom compatibility rules...")
    validator.add_compatibility_rule(
        "FastAPI", "Django", 0.2, 
        "Both are Python web frameworks - choose one"
    )
    validator.add_compatibility_rule(
        "PostgreSQL", "MySQL", 0.4,
        "Multiple relational databases - consider using one primary database"
    )
    
    # Test with conflicting frameworks
    tech_stack = ["FastAPI", "Django", "PostgreSQL"]
    context_priority = {
        "FastAPI": 0.8,
        "Django": 0.6,
        "PostgreSQL": 0.9
    }
    
    print(f"Tech Stack: {tech_stack}")
    print(f"Context Priority: {context_priority}")
    print()
    
    report = validator.validate_tech_stack(tech_stack, context_priority)
    
    print("VALIDATION RESULTS:")
    print(f"✅ Compatible: {report.compatibility_result.is_compatible}")
    print(f"📊 Overall Score: {report.compatibility_result.overall_score:.2f}")
    print(f"🏗️ Validated Stack: {report.validated_tech_stack}")
    print(f"❌ Removed Technologies: {report.compatibility_result.removed_technologies}")
    
    # Show integration conflicts
    integration_conflicts = [
        c for c in report.compatibility_result.conflicts 
        if c.conflict_type == ConflictType.INTEGRATION_CONFLICT
    ]
    
    if integration_conflicts:
        print("\nINTEGRATION CONFLICTS:")
        for conflict in integration_conflicts:
            print(f"  ⚠️ {conflict.tech1} ↔ {conflict.tech2}")
            print(f"     Issue: {conflict.explanation}")
            print(f"     Resolution: {conflict.suggested_resolution}")
    
    print()


def example_4_ecosystem_consistency():
    """Example 4: Ecosystem consistency checking."""
    print("=" * 60)
    print("EXAMPLE 4: Ecosystem Consistency Analysis")
    print("=" * 60)
    
    catalog_manager = setup_example_catalog()
    validator = TechnologyCompatibilityValidator(catalog_manager)
    
    # Test different ecosystem scenarios
    scenarios = [
        {
            "name": "Pure AWS Stack",
            "stack": ["AWS S3", "AWS Lambda", "Amazon RDS"]
        },
        {
            "name": "Mixed Cloud Stack", 
            "stack": ["AWS S3", "Azure Blob Storage", "Google Cloud Storage"]
        },
        {
            "name": "Open Source Stack",
            "stack": ["FastAPI", "PostgreSQL", "Redis", "Docker"]
        },
        {
            "name": "Hybrid Stack",
            "stack": ["AWS S3", "FastAPI", "PostgreSQL"]
        }
    ]
    
    for scenario in scenarios:
        print(f"\n📋 Scenario: {scenario['name']}")
        print(f"   Stack: {scenario['stack']}")
        
        result = validator.check_ecosystem_consistency(scenario['stack'])
        
        print(f"   ✅ Consistent: {result.is_consistent}")
        if result.primary_ecosystem:
            print(f"   🎯 Primary: {result.primary_ecosystem.value}")
        
        if result.ecosystem_distribution:
            print(f"   📊 Distribution: {result.ecosystem_distribution}")
        
        if result.mixed_ecosystem_technologies:
            print(f"   🔀 Mixed: {result.mixed_ecosystem_technologies}")
        
        if result.recommendations:
            print(f"   💡 Recommendations:")
            for rec in result.recommendations:
                print(f"      - {rec}")


def main():
    """Run all examples."""
    print("🔧 Technology Compatibility Validation System Examples")
    print("=" * 60)
    
    try:
        example_1_consistent_stack()
        example_2_conflicting_stack()
        example_3_custom_compatibility_rules()
        example_4_ecosystem_consistency()
        
        print("=" * 60)
        print("✅ All examples completed successfully!")
        print("=" * 60)
        
    except Exception as e:
        print(f"❌ Error running examples: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()