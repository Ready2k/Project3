#!/usr/bin/env python3
"""Test script to verify the agentic necessity assessment is working correctly."""

import asyncio
import sys
sys.path.append('.')

from app.services.agentic_necessity_assessor import AgenticNecessityAssessor, SolutionType
from app.services.agentic_recommendation_service import AgenticRecommendationService
from app.llm.fakes import FakeLLM


async def test_necessity_assessment():
    """Test agentic necessity assessment for different scenarios."""
    
    # Create assessor with fake LLM
    assessor = AgenticNecessityAssessor(FakeLLM({}))
    
    print("🔍 Testing Agentic Necessity Assessment\n")
    
    # Test Case 1: Restaurant Order Management (should be traditional)
    print("1️⃣ Restaurant Order Management:")
    restaurant_requirements = {
        'description': 'I need a solution that will take my manual food orders, from the wait on staff and then turn it into an order for a chef to cook in the kitchen. At the moment we take orders via a paper and pen on a small notepad, write the order and then manually enter it on the till, once entered we hand the ticket to the kitchen staff.',
        'domain': 'Restaurant Operations'
    }
    
    assessment = await assessor.assess_agentic_necessity(restaurant_requirements)
    print(f"   Recommended Solution: {assessment.recommended_solution_type.value}")
    print(f"   Agentic Necessity: {assessment.agentic_necessity_score:.0%}")
    print(f"   Traditional Suitability: {assessment.traditional_suitability_score:.0%}")
    print(f"   Confidence: {assessment.confidence_level:.0%}")
    print(f"   Reasoning: {assessment.recommendation_reasoning}")
    print()
    
    # Test Case 2: Complex AI Research Assistant (should be agentic)
    print("2️⃣ Complex AI Research Assistant:")
    research_requirements = {
        'description': 'I need an intelligent research assistant that can analyze complex scientific papers, identify patterns across multiple domains, generate novel hypotheses, adapt its research strategy based on findings, and proactively suggest new research directions. It should handle unexpected scenarios and learn from each interaction.',
        'domain': 'Research & Analysis'
    }
    
    assessment = await assessor.assess_agentic_necessity(research_requirements)
    print(f"   Recommended Solution: {assessment.recommended_solution_type.value}")
    print(f"   Agentic Necessity: {assessment.agentic_necessity_score:.0%}")
    print(f"   Traditional Suitability: {assessment.traditional_suitability_score:.0%}")
    print(f"   Confidence: {assessment.confidence_level:.0%}")
    print(f"   Reasoning: {assessment.recommendation_reasoning}")
    print()
    
    # Test Case 3: Simple Data Processing (should be traditional)
    print("3️⃣ Simple Data Processing:")
    data_requirements = {
        'description': 'I need to convert CSV files to JSON format, validate the data according to predefined rules, and upload the results to a database. The process is the same every time with clear validation criteria.',
        'domain': 'Data Processing'
    }
    
    assessment = await assessor.assess_agentic_necessity(data_requirements)
    print(f"   Recommended Solution: {assessment.recommended_solution_type.value}")
    print(f"   Agentic Necessity: {assessment.agentic_necessity_score:.0%}")
    print(f"   Traditional Suitability: {assessment.traditional_suitability_score:.0%}")
    print(f"   Confidence: {assessment.confidence_level:.0%}")
    print(f"   Reasoning: {assessment.recommendation_reasoning}")
    print()
    
    # Test Case 4: Customer Service with Complex Reasoning (should be hybrid or agentic)
    print("4️⃣ Intelligent Customer Service:")
    service_requirements = {
        'description': 'I need a customer service system that can handle complex inquiries, understand context and emotions, make personalized recommendations, escalate appropriately, and learn from each interaction to improve responses. It should adapt to different customer personalities and handle unpredictable scenarios.',
        'domain': 'Customer Service'
    }
    
    assessment = await assessor.assess_agentic_necessity(service_requirements)
    print(f"   Recommended Solution: {assessment.recommended_solution_type.value}")
    print(f"   Agentic Necessity: {assessment.agentic_necessity_score:.0%}")
    print(f"   Traditional Suitability: {assessment.traditional_suitability_score:.0%}")
    print(f"   Confidence: {assessment.confidence_level:.0%}")
    print(f"   Reasoning: {assessment.recommendation_reasoning}")
    print()


async def test_integration_with_recommendation_service():
    """Test that the necessity assessment integrates properly with the recommendation service."""
    
    print("🔗 Testing Integration with Recommendation Service\n")
    
    # Create recommendation service
    service = AgenticRecommendationService(FakeLLM({}))
    
    # Test with restaurant order management (should get traditional automation)
    restaurant_requirements = {
        'description': 'I need a solution that will take my manual food orders, from the wait on staff and then turn it into an order for a chef to cook in the kitchen.',
        'domain': 'Restaurant Operations'
    }
    
    recommendations = await service.generate_agentic_recommendations(
        restaurant_requirements, 
        "test-session-123"
    )
    
    print(f"Generated {len(recommendations)} recommendations")
    
    if recommendations:
        rec = recommendations[0]
        print(f"Pattern ID: {rec.pattern_id}")
        print(f"Feasibility: {rec.feasibility}")
        print(f"Confidence: {rec.confidence:.0%}")
        
        if hasattr(rec, 'necessity_assessment') and rec.necessity_assessment:
            print(f"Solution Type: {rec.necessity_assessment.recommended_solution_type.value}")
            print(f"Assessment included: ✅")
        else:
            print("Assessment included: ❌")
        
        print(f"Reasoning: {rec.reasoning[:100]}...")
    
    print("\n✅ Integration test completed!")


if __name__ == "__main__":
    asyncio.run(test_necessity_assessment())
    print("\n" + "="*50 + "\n")
    asyncio.run(test_integration_with_recommendation_service())