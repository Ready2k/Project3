#!/usr/bin/env python3
"""
Test script to verify the bug fixes are working correctly.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from datetime import datetime

# Test 1: Verify feasibility values are correct
def test_feasibility_values():
    """Test that recommendation service uses correct feasibility values."""
    print("🔍 Testing feasibility values...")
    
    from app.services.recommendation import RecommendationService
    from app.pattern.matcher import MatchResult
    
    # Create a test service
    service = RecommendationService(Path("data/patterns"))
    
    # Test match with "Partially Automatable" pattern
    match = MatchResult(
        pattern_id="PAT-001",
        pattern_name="Test Pattern",
        feasibility="Partially Automatable",
        tech_stack=["Python", "FastAPI"],
        confidence=0.8,
        tag_score=0.8,
        vector_score=0.8,
        blended_score=0.8,
        rationale="Test reasoning"
    )
    
    requirements = {
        "description": "Test requirement",
        "domain": "test",
        "complexity_factors": []
    }
    
    # Test feasibility determination
    feasibility = service._determine_feasibility(match, requirements)
    
    # Should return one of the valid values
    valid_values = ["Automatable", "Partially Automatable", "Not Automatable"]
    assert feasibility in valid_values, f"Invalid feasibility: {feasibility}"
    
    print(f"✅ Feasibility determination works: {feasibility}")
    return True

# Test 2: Verify audit logging includes purpose
def test_audit_purpose():
    """Test that audit logging includes purpose field."""
    print("🔍 Testing audit logging with purpose...")
    
    from app.utils.audit import AuditLogger
    import tempfile
    import os
    
    # Create temporary database
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as tmp:
        db_path = tmp.name
    
    try:
        audit_logger = AuditLogger(db_path=db_path, redact_pii=False)
        
        # Log a call with purpose
        asyncio.run(audit_logger.log_llm_call(
            session_id="test-session",
            provider="test-provider",
            model="test-model",
            latency_ms=100,
            tokens=50,
            prompt="test prompt",
            response="test response",
            purpose="test_purpose"
        ))
        
        # Retrieve messages
        messages = audit_logger.get_llm_messages(limit=1)
        
        assert len(messages) == 1, "Should have one message"
        assert messages[0]['purpose'] == 'test_purpose', f"Purpose should be 'test_purpose', got: {messages[0]['purpose']}"
        
        print("✅ Audit logging with purpose works")
        return True
        
    finally:
        # Clean up
        if os.path.exists(db_path):
            os.unlink(db_path)

# Test 3: Verify export schema validation
def test_export_validation():
    """Test that export validation accepts correct feasibility values."""
    print("🔍 Testing export validation...")
    
    from app.exporters.json_exporter import JSONExporter
    from app.state.store import SessionState, Phase, Recommendation
    import tempfile
    
    # Create temporary export directory
    with tempfile.TemporaryDirectory() as temp_dir:
        exporter = JSONExporter(Path(temp_dir))
        
        # Create test session with correct feasibility
        session = SessionState(
            session_id="test-session",
            phase=Phase.DONE,
            progress=100,
            requirements={"description": "Test requirement"},
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[
                Recommendation(
                    pattern_id="PAT-001",
                    feasibility="Partially Automatable",  # This should be valid now
                    confidence=0.8,
                    tech_stack=["Python"],
                    reasoning="Test reasoning"
                )
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        try:
            # This should not raise a validation error
            file_path = exporter.export_session(session)
            assert Path(file_path).exists(), "Export file should exist"
            
            # Verify the content has correct feasibility
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            assert data['feasibility_assessment'] == 'Partially Automatable', \
                f"Expected 'Partially Automatable', got: {data['feasibility_assessment']}"
            
            print("✅ Export validation works with correct feasibility values")
            return True
            
        except Exception as e:
            print(f"❌ Export validation failed: {e}")
            return False

def main():
    """Run all tests."""
    print("🚀 Running bug fix verification tests...\n")
    
    tests = [
        test_feasibility_values,
        test_audit_purpose,
        test_export_validation
    ]
    
    passed = 0
    failed = 0
    
    for test in tests:
        try:
            if test():
                passed += 1
            else:
                failed += 1
        except Exception as e:
            print(f"❌ Test {test.__name__} failed with exception: {e}")
            failed += 1
        print()
    
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All tests passed! Bug fixes are working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Please check the issues above.")
        return False

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)