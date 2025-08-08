#!/usr/bin/env python3
"""
Example usage of the audit and observability system.

This example demonstrates how to:
1. Initialize the audit system
2. Log LLM calls and pattern matches
3. Query audit data and generate statistics
4. Clean up old records
"""

import asyncio
import sys
import tempfile
from pathlib import Path

# Add the parent directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.audit import AuditLogger, log_llm_call, log_pattern_match
from app.utils.audit_integration import AuditedLLMProvider
from app.llm.fakes import FakeLLM


async def main():
    """Demonstrate audit system usage."""
    print("🔍 Audit System Usage Example")
    print("=" * 50)
    
    # Create a temporary database for this example
    with tempfile.NamedTemporaryFile(suffix='.db', delete=False) as f:
        db_path = f.name
    
    try:
        # Initialize audit logger
        audit_logger = AuditLogger(db_path=db_path, redact_pii=True)
        print(f"📊 Initialized audit database: {db_path}")
        
        # Example 1: Direct audit logging
        print("\n1️⃣ Direct Audit Logging")
        print("-" * 30)
        
        session_id = "example-session-001"
        
        # Log some LLM calls
        await audit_logger.log_llm_call(
            session_id=session_id,
            provider="openai",
            model="gpt-4",
            latency_ms=1500,
            tokens=150
        )
        
        await audit_logger.log_llm_call(
            session_id=session_id,
            provider="bedrock",
            model="claude-3",
            latency_ms=2200,
            tokens=200
        )
        
        # Log some pattern matches
        await audit_logger.log_pattern_match(
            session_id=session_id,
            pattern_id="PAT-001",
            score=0.85,
            accepted=True
        )
        
        await audit_logger.log_pattern_match(
            session_id=session_id,
            pattern_id="PAT-002",
            score=0.65,
            accepted=False
        )
        
        print(f"✅ Logged 2 LLM calls and 2 pattern matches for session {session_id}")
        
        # Example 2: Using convenience functions
        print("\n2️⃣ Using Convenience Functions")
        print("-" * 30)
        
        # Set up global audit logger
        import app.utils.audit
        app.utils.audit._audit_logger = audit_logger
        
        session_id_2 = "example-session-002"
        
        await log_llm_call(session_id_2, "openai", "gpt-3.5-turbo", 800, 75)
        await log_pattern_match(session_id_2, "PAT-003", 0.92, True)
        
        print(f"✅ Used convenience functions for session {session_id_2}")
        
        # Example 3: Using audited LLM provider wrapper
        print("\n3️⃣ Using Audited LLM Provider")
        print("-" * 30)
        
        session_id_3 = "example-session-003"
        
        # Create a fake LLM and wrap it with audit logging
        fake_llm = FakeLLM(responses={})
        audited_provider = AuditedLLMProvider(fake_llm, session_id_3)
        
        # Make some calls - these will be automatically audited
        response1 = await audited_provider.generate("Analyze this requirement")
        response2 = await audited_provider.generate("Generate questions")
        
        print(f"✅ Made 2 audited LLM calls:")
        print(f"   Response 1: {response1[:50]}...")
        print(f"   Response 2: {response2[:50]}...")
        
        # Example 4: Querying audit data
        print("\n4️⃣ Querying Audit Data")
        print("-" * 30)
        
        # Get all runs
        all_runs = audit_logger.get_runs(limit=10)
        print(f"📈 Total LLM calls logged: {len(all_runs)}")
        
        # Get runs for specific session
        session_1_runs = audit_logger.get_runs(session_id=session_id)
        print(f"📊 Calls for {session_id}: {len(session_1_runs)}")
        
        # Get all matches
        all_matches = audit_logger.get_matches(limit=10)
        print(f"🎯 Total pattern matches logged: {len(all_matches)}")
        
        # Example 5: Statistics and analytics
        print("\n5️⃣ Statistics and Analytics")
        print("-" * 30)
        
        # Provider statistics
        provider_stats = audit_logger.get_provider_stats()
        print("🔧 Provider Statistics:")
        for stat in provider_stats['provider_stats']:
            print(f"   {stat['provider']}/{stat['model']}: "
                  f"{stat['call_count']} calls, "
                  f"avg latency: {stat['avg_latency']}ms")
        
        # Pattern statistics
        pattern_stats = audit_logger.get_pattern_stats()
        print("\n🎯 Pattern Statistics:")
        for stat in pattern_stats['pattern_stats']:
            print(f"   {stat['pattern_id']}: "
                  f"{stat['match_count']} matches, "
                  f"acceptance rate: {stat['acceptance_rate']:.1%}")
        
        # Example 6: Detailed record inspection
        print("\n6️⃣ Detailed Record Inspection")
        print("-" * 30)
        
        if all_runs:
            latest_run = all_runs[0]  # Most recent
            print(f"🔍 Latest LLM call:")
            print(f"   Session: {latest_run.session_id}")
            print(f"   Provider: {latest_run.provider}")
            print(f"   Model: {latest_run.model}")
            print(f"   Latency: {latest_run.latency_ms}ms")
            print(f"   Tokens: {latest_run.tokens}")
            print(f"   Time: {latest_run.created_at}")
        
        if all_matches:
            latest_match = all_matches[0]  # Most recent
            print(f"\n🎯 Latest pattern match:")
            print(f"   Session: {latest_match.session_id}")
            print(f"   Pattern: {latest_match.pattern_id}")
            print(f"   Score: {latest_match.score}")
            print(f"   Accepted: {latest_match.accepted}")
            print(f"   Time: {latest_match.created_at}")
        
        # Example 7: Cleanup old records
        print("\n7️⃣ Cleanup Operations")
        print("-" * 30)
        
        # This would normally clean up records older than 30 days
        # For demo purposes, we'll use 0 days to clean everything
        deleted_count = audit_logger.cleanup_old_records(days=0)
        print(f"🧹 Cleaned up {deleted_count} old records")
        
        # Verify cleanup
        remaining_runs = audit_logger.get_runs()
        remaining_matches = audit_logger.get_matches()
        print(f"📊 Remaining records: {len(remaining_runs)} runs, {len(remaining_matches)} matches")
        
        print("\n✨ Audit system example completed successfully!")
        
    finally:
        # Clean up the temporary database
        Path(db_path).unlink(missing_ok=True)
        print(f"🗑️  Cleaned up temporary database: {db_path}")


if __name__ == "__main__":
    asyncio.run(main())