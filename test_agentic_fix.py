#!/usr/bin/env python3
"""Test script to verify the agentic recommendation service bug fix."""

import asyncio
import sys
from pathlib import Path

# Add the app directory to the path
sys.path.insert(0, str(Path(__file__).parent))

from app.services.agentic_recommendation_service import AgenticRecommendationService
from app.llm.fakes import FakeLLM

async def test_agentic_service():
    """Test the agentic recommendation service to ensure the bug is fixed."""
    print("🧪 Testing Agentic Recommendation Service Bug Fix")
    print("=" * 60)
    
    try:
        # Create a fake LLM provider for testing
        fake_llm = FakeLLM({}, seed=42)
        
        # Create the agentic recommendation service
        service = AgenticRecommendationService(
            llm_provider=fake_llm,
            pattern_library_path=Path("data/patterns")
        )
        
        print("✅ Successfully created AgenticRecommendationService")
        
        # Test requirements that would trigger the bug
        test_requirements = {
            "description": "Create an AI-powered system for automated customer support",
            "domain": "customer_service",
            "pattern_types": ["workflow_automation"]
        }
        
        print("🔄 Testing agentic recommendations generation...")
        
        # This should not crash with the workflow_automation attribute error
        recommendations = await service.generate_agentic_recommendations(
            requirements=test_requirements,
            session_id="test-session-123"
        )
        
        print(f"✅ Successfully generated {len(recommendations)} recommendations")
        
        # Check if recommendations were created
        if recommendations:
            for i, rec in enumerate(recommendations):
                print(f"   {i+1}. Pattern: {rec.pattern_id}")
                print(f"      Feasibility: {rec.feasibility}")
                print(f"      Confidence: {rec.confidence:.2f}")
                print(f"      Tech Stack: {len(rec.tech_stack)} technologies")
                if rec.agent_roles:
                    print(f"      Agent Roles: {len(rec.agent_roles)} agents")
                print()
        
        print("🎉 Bug fix verification successful!")
        print("   - No 'workflow_automation' attribute errors")
        print("   - Agentic recommendations generated successfully")
        print("   - Pattern saving should work without crashes")
        
        return True
        
    except AttributeError as e:
        if "workflow_automation" in str(e):
            print(f"❌ Bug still exists: {e}")
            return False
        else:
            print(f"❌ Different AttributeError: {e}")
            return False
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        print(f"   Error type: {type(e).__name__}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_agentic_service())
    exit(0 if success else 1)