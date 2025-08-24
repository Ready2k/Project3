#!/usr/bin/env python3
"""
Test script for the new automation suitability assessment functionality.

This tests the enhanced Q&A flow that:
1. Tries agentic assessment first
2. Falls back to traditional automation assessment if agentic fails
3. Provides user choice when automation isn't suitable
"""

import asyncio
import sys
from pathlib import Path

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.automation_suitability_assessor import AutomationSuitabilityAssessor, AutomationSuitability
from app.llm.openai_provider import OpenAIProvider
from app.config import Settings


async def test_automation_suitability():
    """Test the automation suitability assessment."""
    
    # Load settings
    settings = Settings()
    
    # Get API key from environment
    import os
    api_key = os.getenv('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY environment variable not set")
        print("💡 Set it with: export OPENAI_API_KEY=your-key-here")
        return
    
    # Create LLM provider
    provider = OpenAIProvider(
        api_key=api_key,
        model="gpt-4o-mini",
        timeout=30
    )
    
    # Create assessor
    assessor = AutomationSuitabilityAssessor(provider)
    
    # Test cases
    test_cases = [
        {
            "name": "Physical Task (should be rejected)",
            "requirements": {
                "description": "I need a solution to feed my pet snail every morning",
                "constraints": {}
            },
            "expected_suitability": AutomationSuitability.NOT_SUITABLE
        },
        {
            "name": "Traditional Automation (should suggest traditional)",
            "requirements": {
                "description": "I need to automatically copy data from Excel files to our database every night",
                "constraints": {}
            },
            "expected_suitability": AutomationSuitability.TRADITIONAL
        },
        {
            "name": "Complex Digital Task (might suggest agentic or hybrid)",
            "requirements": {
                "description": "I need to automatically analyze customer support tickets and route them to the right team based on sentiment and complexity",
                "constraints": {}
            },
            "expected_suitability": [AutomationSuitability.AGENTIC, AutomationSuitability.HYBRID]
        },
        {
            "name": "Incomplete Food Order Task (original issue)",
            "requirements": {
                "description": "I need a solution that will take my manual food orders, from the wait on staff and then turn it into",
                "constraints": {}
            },
            "expected_suitability": [AutomationSuitability.TRADITIONAL, AutomationSuitability.HYBRID, AutomationSuitability.NOT_SUITABLE]
        }
    ]
    
    print("🧪 Testing Automation Suitability Assessment")
    print("=" * 60)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n{i}. {test_case['name']}")
        print(f"   Description: {test_case['requirements']['description']}")
        
        try:
            # Assess automation suitability (simulating agentic rejection)
            assessment = await assessor.assess_automation_suitability(
                test_case['requirements'],
                agentic_rejected=True
            )
            
            print(f"   ✅ Suitability: {assessment.suitability.value}")
            print(f"   📊 Confidence: {assessment.confidence:.1%}")
            print(f"   💭 Reasoning: {assessment.reasoning[:100]}...")
            print(f"   🎯 Approach: {assessment.recommended_approach[:80]}...")
            print(f"   🤔 User Choice Required: {assessment.user_choice_required}")
            
            if assessment.warning_message:
                print(f"   ⚠️  Warning: {assessment.warning_message}")
            
            # Check if result matches expectations
            expected = test_case['expected_suitability']
            if isinstance(expected, list):
                if assessment.suitability in expected:
                    print(f"   ✅ Result matches expectations")
                else:
                    print(f"   ❌ Expected one of {[s.value for s in expected]}, got {assessment.suitability.value}")
            else:
                if assessment.suitability == expected:
                    print(f"   ✅ Result matches expectations")
                else:
                    print(f"   ❌ Expected {expected.value}, got {assessment.suitability.value}")
            
            # Test decision methods
            should_proceed = assessor.should_proceed_with_traditional_patterns(assessment)
            requires_choice = assessor.should_require_user_choice(assessment)
            
            print(f"   🚀 Should proceed with traditional: {should_proceed}")
            print(f"   🤔 Requires user choice: {requires_choice}")
            
        except Exception as e:
            print(f"   ❌ Error: {str(e)}")
    
    print("\n" + "=" * 60)
    print("✅ Automation suitability assessment test completed!")


if __name__ == "__main__":
    asyncio.run(test_automation_suitability())