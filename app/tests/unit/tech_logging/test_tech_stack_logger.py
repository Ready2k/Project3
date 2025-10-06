"""Unit tests for TechStackLogger."""

import pytest
import json
import tempfile
from pathlib import Path

from app.services.tech_logging.tech_stack_logger import (
    TechStackLogger, LogCategory
)


class TestTechStackLogger:
    """Test cases for TechStackLogger."""
    
    @pytest.fixture
    def logger_config(self):
        """Basic logger configuration for testing."""
        return {
            'log_level': 'DEBUG',
            'output_format': 'structured',
            'enable_console': False,  # Disable console for tests
            'enable_debug_mode': True,
            'buffer_size': 100,
            'auto_flush': False  # Manual flush for testing
        }
    
    @pytest.fixture
    def tech_logger(self, logger_config):
        """Create TechStackLogger instance for testing."""
        logger = TechStackLogger(logger_config)
        logger.initialize()
        return logger
    
    def test_initialization(self, tech_logger):
        """Test logger initialization."""
        assert tech_logger.is_initialized()
        assert tech_logger._debug_mode is True
        assert tech_logger._buffer_size == 100
        assert tech_logger._auto_flush is False
    
    def test_log_info(self, tech_logger):
        """Test info logging."""
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Test message",
            {"key": "value"},
            confidence_score=0.8
        )
        
        entries = tech_logger.get_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry.level == "INFO"
        assert entry.category == LogCategory.TECHNOLOGY_EXTRACTION.value
        assert entry.component == "TestComponent"
        assert entry.operation == "test_operation"
        assert entry.message == "Test message"
        assert entry.context["key"] == "value"
        assert entry.confidence_score == 0.8
    
    def test_log_error_with_exception(self, tech_logger):
        """Test error logging with exception."""
        test_exception = ValueError("Test error")
        
        tech_logger.log_error(
            LogCategory.ERROR_HANDLING,
            "TestComponent",
            "test_operation",
            "Error occurred",
            {"input": "test"},
            exception=test_exception
        )
        
        entries = tech_logger.get_log_entries()
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry.level == "ERROR"
        assert entry.context["exception_type"] == "ValueError"
        assert entry.context["exception_message"] == "Test error"
    
    def test_session_context(self, tech_logger):
        """Test session context management."""
        session_id = "test_session_123"
        session_context = {"user_id": "user123", "project": "test_project"}
        
        tech_logger.set_session_context(session_id, session_context)
        
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Test message"
        )
        
        entries = tech_logger.get_log_entries()
        entry = entries[0]
        
        assert entry.session_id == session_id
        assert entry.context["user_id"] == "user123"
        assert entry.context["project"] == "test_project"
    
    def test_request_context(self, tech_logger):
        """Test request context management."""
        request_id = "req_123"
        request_context = {"operation_type": "generation", "priority": "high"}
        
        tech_logger.set_request_context(request_id, request_context)
        
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Test message"
        )
        
        entries = tech_logger.get_log_entries()
        entry = entries[0]
        
        assert entry.request_id == request_id
        assert entry.context["operation_type"] == "generation"
        assert entry.context["priority"] == "high"
        
        # Test context clearing
        tech_logger.clear_request_context()
        
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Another message"
        )
        
        entries = tech_logger.get_log_entries()
        assert entries[1].request_id is None
    
    def test_performance_tracking(self, tech_logger):
        """Test performance tracking functionality."""
        operation_id = "test_op_123"
        
        # Start tracking
        tech_logger.start_performance_tracking(operation_id)
        
        # Simulate some work
        import time
        time.sleep(0.01)  # 10ms
        
        # End tracking
        duration = tech_logger.end_performance_tracking(
            operation_id,
            LogCategory.PERFORMANCE,
            "TestComponent",
            "test_operation",
            {"test_data": "value"}
        )
        
        assert duration > 0
        assert duration >= 10  # At least 10ms
        
        # Check log entry was created
        entries = tech_logger.get_log_entries(category=LogCategory.PERFORMANCE)
        assert len(entries) == 1
        
        entry = entries[0]
        assert entry.context["operation_id"] == operation_id
        assert entry.context["duration_ms"] == duration
    
    def test_debug_mode_filtering(self, logger_config):
        """Test debug mode filtering."""
        # Test with debug mode disabled
        logger_config['enable_debug_mode'] = False
        tech_logger = TechStackLogger(logger_config)
        tech_logger.initialize()
        
        tech_logger.log_debug(
            LogCategory.DEBUG_TRACE,
            "TestComponent",
            "test_operation",
            "Debug message"
        )
        
        # Debug message should not be logged
        entries = tech_logger.get_log_entries()
        assert len(entries) == 0
        
        # Enable debug mode
        tech_logger.enable_debug_mode(True)
        
        tech_logger.log_debug(
            LogCategory.DEBUG_TRACE,
            "TestComponent",
            "test_operation",
            "Debug message"
        )
        
        # Debug message should now be logged
        entries = tech_logger.get_log_entries()
        assert len(entries) == 2  # Enable message + debug message
    
    def test_log_filtering(self, tech_logger):
        """Test log entry filtering."""
        # Create multiple log entries
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "Component1",
            "operation1",
            "Message 1"
        )
        
        tech_logger.log_info(
            LogCategory.LLM_INTERACTION,
            "Component2",
            "operation2",
            "Message 2"
        )
        
        tech_logger.set_session_context("session1", {})
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "Component1",
            "operation3",
            "Message 3"
        )
        
        # Test category filtering
        tech_entries = tech_logger.get_log_entries(
            category=LogCategory.TECHNOLOGY_EXTRACTION
        )
        assert len(tech_entries) == 2
        
        # Test component filtering
        comp1_entries = tech_logger.get_log_entries(component="Component1")
        assert len(comp1_entries) == 2
        
        # Test session filtering
        session_entries = tech_logger.get_log_entries(session_id="session1")
        assert len(session_entries) == 1
        
        # Test limit
        limited_entries = tech_logger.get_log_entries(limit=2)
        assert len(limited_entries) == 2
    
    def test_performance_summary(self, tech_logger):
        """Test performance summary generation."""
        # Create some performance entries
        for i in range(5):
            tech_logger.start_performance_tracking(f"op_{i}")
            import time
            time.sleep(0.001)  # 1ms
            tech_logger.end_performance_tracking(
                f"op_{i}",
                LogCategory.PERFORMANCE,
                "TestComponent",
                "test_operation"
            )
        
        summary = tech_logger.get_performance_summary(
            component="TestComponent",
            operation="test_operation"
        )
        
        assert summary['count'] == 5
        assert summary['min_ms'] > 0
        assert summary['max_ms'] > 0
        assert summary['avg_ms'] > 0
        assert summary['total_ms'] > 0
    
    def test_log_export_json(self, tech_logger):
        """Test JSON log export."""
        # Create test entries
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Test message 1"
        )
        
        tech_logger.log_error(
            LogCategory.ERROR_HANDLING,
            "TestComponent",
            "test_operation",
            "Test error",
            exception=ValueError("Test")
        )
        
        # Export to temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            tech_logger.export_logs(temp_path, format='json')
            
            # Verify export
            with open(temp_path, 'r') as f:
                exported_data = json.load(f)
            
            assert len(exported_data) == 2
            assert exported_data[0]['level'] == 'INFO'
            assert exported_data[1]['level'] == 'ERROR'
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_log_export_with_filters(self, tech_logger):
        """Test log export with filters."""
        # Create test entries
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "Component1",
            "operation1",
            "Message 1"
        )
        
        tech_logger.log_error(
            LogCategory.ERROR_HANDLING,
            "Component2",
            "operation2",
            "Error message"
        )
        
        # Export with filters
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = f.name
        
        try:
            tech_logger.export_logs(
                temp_path,
                format='json',
                filters={'level': 'ERROR'}
            )
            
            # Verify filtered export
            with open(temp_path, 'r') as f:
                exported_data = json.load(f)
            
            assert len(exported_data) == 1
            assert exported_data[0]['level'] == 'ERROR'
            
        finally:
            Path(temp_path).unlink(missing_ok=True)
    
    def test_auto_flush(self, logger_config):
        """Test auto-flush functionality."""
        logger_config['buffer_size'] = 2
        logger_config['auto_flush'] = True
        
        tech_logger = TechStackLogger(logger_config)
        tech_logger.initialize()
        
        # Add entries up to buffer size
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Message 1"
        )
        
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Message 2"
        )
        
        # Buffer should still have entries
        assert len(tech_logger._log_entries) == 2
        
        # Add one more to trigger flush
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Message 3"
        )
        
        # Buffer should be cleared after auto-flush
        assert len(tech_logger._log_entries) == 0
    
    def test_shutdown(self, tech_logger):
        """Test logger shutdown."""
        # Add some entries
        tech_logger.log_info(
            LogCategory.TECHNOLOGY_EXTRACTION,
            "TestComponent",
            "test_operation",
            "Test message"
        )
        
        # Shutdown should flush logs
        tech_logger.shutdown()
        
        # Buffer should be empty after shutdown
        assert len(tech_logger._log_entries) == 0