#!/usr/bin/env python3
"""
Mock test for automation suitability assessment functionality.

Tests the logic without requiring actual LLM calls.
"""

import asyncio
import sys
from pathlib import Path
from unittest.mock import AsyncMock

# Add the app directory to Python path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.automation_suitability_assessor import (
    AutomationSuitabilityAssessor, 
    AutomationSuitability,
    SuitabilityAssessment
)


class MockLLMProvider:
    """Mock LLM provider for testing."""
    
    def __init__(self, mock_responses):
        self.mock_responses = mock_responses
        self.call_count = 0
    
    async def generate(self, prompt, purpose=None):
        """Mock generate method."""
        if self.call_count < len(self.mock_responses):
            response = self.mock_responses[self.call_count]
            self.call_count += 1
            return response
        else:
            return '{"suitability": "not_suitable", "confidence": 0.3, "reasoning": "Mock fallback"}'


async def test_automation_suitability_mock():
    """Test the automation suitability assessment with mocked responses."""
    
    # Mock LLM responses for different scenarios
    mock_responses = [
        # Physical task - should be rejected
        '''{"suitability": "not_suitable", "confidence": 0.9, "reasoning": "This task involves physical interaction with pets which cannot be automated through software", "recommended_approach": "Manual care with optional reminder systems", "challenges": ["Physical world interaction", "Animal welfare requirements"], "next_steps": ["Consider reminder apps", "Explore pet care services"], "user_choice_required": true, "warning_message": "Physical pet care cannot be automated"}''',
        
        # Traditional automation task
        '''{"suitability": "traditional", "confidence": 0.85, "reasoning": "This is a structured data transfer task suitable for traditional automation tools", "recommended_approach": "Use RPA or ETL tools for scheduled data transfer", "challenges": ["File format variations", "Error handling"], "next_steps": ["Set up scheduled job", "Implement error monitoring"], "user_choice_required": false}''',
        
        # Complex digital task - might be agentic
        '''{"suitability": "agentic", "confidence": 0.8, "reasoning": "This requires complex reasoning about sentiment and routing decisions", "recommended_approach": "Deploy agentic AI system with NLP and decision-making capabilities", "challenges": ["Sentiment analysis accuracy", "Dynamic routing rules"], "next_steps": ["Implement sentiment analysis", "Design routing logic"], "user_choice_required": false}''',
        
        # Incomplete food order task
        '''{"suitability": "traditional", "confidence": 0.6, "reasoning": "While incomplete, this appears to be about digitizing manual orders which is suitable for traditional automation with OCR", "recommended_approach": "Use OCR and form processing automation", "challenges": ["Handwriting recognition", "Order format variations"], "next_steps": ["Implement OCR system", "Design order processing workflow"], "user_choice_required": true, "warning_message": "Requirement is incomplete - may need clarification"}'''
    ]
    
    # Create mock provider
    mock_provider = MockLLMProvider(mock_responses)
    
    # Create assessor
    assessor = AutomationSuitabilityAssessor(mock_provider)
    
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
            "name": "Complex Digital Task (might suggest agentic)",
            "requirements": {
                "description": "I need to automatically analyze customer support tickets and route them to the right team based on sentiment and complexity",
                "constraints": {}
            },
            "expected_suitability": AutomationSuitability.AGENTIC
        },
        {
            "name": "Incomplete Food Order Task (original issue)",
            "requirements": {
                "description": "I need a solution that will take my manual food orders, from the wait on staff and then turn it into",
                "constraints": {}
            },
            "expected_suitability": AutomationSuitability.TRADITIONAL
        }
    ]
    
    print("🧪 Testing Automation Suitability Assessment (Mock)")
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
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 60)
    print("✅ Mock automation suitability assessment test completed!")
    
    # Test the decision logic
    print("\n🧪 Testing Decision Logic")
    print("-" * 30)
    
    # Test case: Traditional with high confidence - should proceed
    assessment1 = SuitabilityAssessment(
        suitability=AutomationSuitability.TRADITIONAL,
        confidence=0.8,
        reasoning="Test",
        recommended_approach="Test",
        challenges=[],
        next_steps=[],
        user_choice_required=False
    )
    
    print(f"Traditional + High Confidence:")
    print(f"  Should proceed: {assessor.should_proceed_with_traditional_patterns(assessment1)}")
    print(f"  Requires choice: {assessor.should_require_user_choice(assessment1)}")
    
    # Test case: Not suitable - should require choice
    assessment2 = SuitabilityAssessment(
        suitability=AutomationSuitability.NOT_SUITABLE,
        confidence=0.9,
        reasoning="Test",
        recommended_approach="Test",
        challenges=[],
        next_steps=[],
        user_choice_required=True,
        warning_message="Not suitable"
    )
    
    print(f"Not Suitable:")
    print(f"  Should proceed: {assessor.should_proceed_with_traditional_patterns(assessment2)}")
    print(f"  Requires choice: {assessor.should_require_user_choice(assessment2)}")


if __name__ == "__main__":
    asyncio.run(test_automation_suitability_mock())