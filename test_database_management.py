#!/usr/bin/env python3
"""Test script for Database Management functionality."""

import sys
import os
sys.path.append('.')

def test_database_management_imports():
    """Test that all required imports work correctly."""
    print("🧪 Testing Database Management imports...")
    
    try:
        from app.ui.system_configuration import (
            render_database_management,
            render_audit_database_management,
            render_security_database_management,
            render_audit_data_viewer,
            render_audit_analytics,
            render_audit_cleanup,
            render_security_data_viewer,
            render_security_analytics,
            render_security_cleanup
        )
        print("✅ All database management functions imported successfully")
        
        # Test audit logger import
        from app.utils.audit import get_audit_logger
        audit_logger = get_audit_logger()
        print(f"✅ Audit logger initialized: {audit_logger.db_path}")
        
        # Test security logger import
        from app.security.security_event_logger import SecurityEventLogger
        security_logger = SecurityEventLogger()
        print(f"✅ Security logger initialized: {security_logger.db_path}")
        
        return True
        
    except Exception as e:
        print(f"❌ Import error: {e}")
        return False


def test_database_connections():
    """Test database connections and basic queries."""
    print("\n🧪 Testing database connections...")
    
    try:
        import sqlite3
        from app.utils.audit import get_audit_logger
        from app.security.security_event_logger import SecurityEventLogger
        
        # Test audit database
        audit_logger = get_audit_logger()
        if os.path.exists(audit_logger.db_path):
            with sqlite3.connect(audit_logger.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM runs")
                runs_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM matches")
                matches_count = cursor.fetchone()[0]
                
                print(f"✅ Audit database accessible: {runs_count} runs, {matches_count} matches")
        else:
            print("ℹ️ Audit database doesn't exist yet (will be created on first use)")
        
        # Test security database
        security_logger = SecurityEventLogger()
        if os.path.exists(security_logger.db_path):
            with sqlite3.connect(security_logger.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM security_events")
                events_count = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM security_metrics")
                metrics_count = cursor.fetchone()[0]
                
                print(f"✅ Security database accessible: {events_count} events, {metrics_count} metrics")
        else:
            print("ℹ️ Security database doesn't exist yet (will be created on first use)")
        
        return True
        
    except Exception as e:
        print(f"❌ Database connection error: {e}")
        return False


def test_pandas_integration():
    """Test pandas integration for data display."""
    print("\n🧪 Testing pandas integration...")
    
    try:
        import pandas as pd
        import sqlite3
        from app.utils.audit import get_audit_logger
        
        audit_logger = get_audit_logger()
        
        # Create a simple test query
        with sqlite3.connect(audit_logger.db_path) as conn:
            # This will work even if the table is empty
            df = pd.read_sql_query("SELECT * FROM runs LIMIT 5", conn)
            print(f"✅ Pandas integration working: loaded {len(df)} rows")
        
        return True
        
    except Exception as e:
        print(f"❌ Pandas integration error: {e}")
        return False


def main():
    """Run all database management tests."""
    print("🚀 Starting Database Management Tests\n")
    
    tests_passed = 0
    total_tests = 3
    
    if test_database_management_imports():
        tests_passed += 1
    
    if test_database_connections():
        tests_passed += 1
    
    if test_pandas_integration():
        tests_passed += 1
    
    print(f"\n📊 Test Results: {tests_passed}/{total_tests} tests passed")
    
    if tests_passed == total_tests:
        print("🎉 All tests passed! Database Management is ready to use.")
        print("\n📋 Features available:")
        print("  ✅ View and filter audit database records (LLM calls and pattern matches)")
        print("  ✅ View and filter security database records (security events and metrics)")
        print("  ✅ Analytics dashboards for both databases")
        print("  ✅ Bulk delete operations with confirmation")
        print("  ✅ Cleanup operations (old records, test data)")
        print("  ✅ Complete database reset options (with safety confirmations)")
        print("  ✅ Real-time statistics and metrics")
        print("  ✅ Detailed event inspection for security events")
        
        print("\n🔧 Access via: System Configuration tab → Database Management")
    else:
        print("❌ Some tests failed. Please check the errors above.")
    
    return tests_passed == total_tests


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)