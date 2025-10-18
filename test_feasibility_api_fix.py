#!/usr/bin/env python3
"""
Test script to verify the feasibility API fix.
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.core.session_store import get_session_store
from app.models.session import Session, Phase
from app.models.requirements import Requirements

async def test_feasibility_fix():
    """Test that the API now returns LLM feasibility correctly."""
    
    print("🧪 Testing feasibility API fix...")
    
    # Create a test session with LLM analysis
    store = get_session_store()
    
    # Create requirements with LLM analysis
    requirements_data = {
        "description": "Test customer support automation",
        "domain": "customer-service",
        "llm_analysis_automation_feasibility": "Automatable",
        "llm_analysis_feasibility_reasoning": "Digital process with API integrations",
        "llm_analysis_confidence_level": 0.85
    }
    
    requirements = Requirements(**requirements_data)
    
    # Create session
    session = Session(
        session_id="test-feasibility-fix",
        requirements=requirements,
        phase=Phase.DONE,
        progress=100
    )
    
    # Store session
    await store.store_session(session)
    
    print(f"✅ Created test session with LLM feasibility: {requirements_data['llm_analysis_automation_feasibility']}")
    
    # Now test the API endpoint logic
    from app.api import generate_recommendations
    from app.models.api import RecommendRequest
    from fastapi import Response
    
    try:
        request = RecommendRequest(session_id="test-feasibility-fix", top_k=3)
        response = Response()
        
        result = await generate_recommendations(request, response)
        
        print(f"📊 API Response:")
        print(f"   Feasibility: {result.feasibility}")
        print(f"   Expected: Automatable")
        
        if result.feasibility == "Automatable":
            print("✅ SUCCESS: API correctly returns LLM feasibility!")
        else:
            print("❌ FAILED: API still not using LLM feasibility")
            
    except Exception as e:
        print(f"❌ Error testing API: {e}")
    
    # Clean up
    await store.delete_session("test-feasibility-fix")
    print("🧹 Cleaned up test session")

if __name__ == "__main__":
    asyncio.run(test_feasibility_fix())