"""Integration tests for export functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from app.exporters.service import ExportService
from app.state.store import SessionState, Phase, Recommendation, DiskCacheStore


class TestExportIntegration:
    """Integration tests for export system."""
    
    @pytest.fixture
    def temp_dirs(self):
        """Create temporary directories for cache and exports."""
        with tempfile.TemporaryDirectory() as cache_dir, \
             tempfile.TemporaryDirectory() as export_dir:
            yield Path(cache_dir), Path(export_dir)
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session state."""
        return SessionState(
            session_id="integration-test-session",
            phase=Phase.DONE,
            progress=100,
            requirements={
                "description": "Integration test requirements",
                "domain": "Testing",
                "frequency": "once"
            },
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[
                Recommendation(
                    pattern_id="PAT-999",
                    feasibility="Automatable",
                    confidence=0.95,
                    tech_stack=["Python", "pytest"],
                    reasoning="Perfect for automated testing"
                )
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_export_service_json_integration(self, temp_dirs, sample_session):
        """Test complete JSON export integration."""
        cache_dir, export_dir = temp_dirs
        
        # Create export service
        export_service = ExportService(export_dir)
        
        # Export session
        file_path, download_url, file_info = export_service.export_session(sample_session, "json")
        
        # Verify file was created
        assert Path(file_path).exists()
        assert file_path.endswith(".json")
        assert download_url.startswith("file://")
        assert file_info["size_bytes"] > 0
        
        # Verify file content
        with open(file_path, 'r') as f:
            export_data = json.load(f)
        
        assert export_data["session_id"] == "integration-test-session"
        assert export_data["feasibility_assessment"] == "Automatable"
        assert len(export_data["recommendations"]) == 1
        assert export_data["recommendations"][0]["pattern_id"] == "PAT-999"
    
    def test_export_service_markdown_integration(self, temp_dirs, sample_session):
        """Test complete Markdown export integration."""
        cache_dir, export_dir = temp_dirs
        
        # Create export service
        export_service = ExportService(export_dir)
        
        # Export session
        file_path, download_url, file_info = export_service.export_session(sample_session, "md")
        
        # Verify file was created
        assert Path(file_path).exists()
        assert file_path.endswith(".md")
        assert download_url.startswith("file://")
        assert file_info["size_bytes"] > 0
        
        # Verify file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# AgenticOrNot - Automation Feasibility Report" in content
        assert "integration-test-session" in content
        assert "Integration test requirements" in content
        assert "✅" in content  # Automatable emoji
        assert "PAT-999" in content
        assert "Python" in content
        assert "pytest" in content
    
    def test_session_validation_integration(self, temp_dirs):
        """Test session validation integration."""
        cache_dir, export_dir = temp_dirs
        
        export_service = ExportService(export_dir)
        
        # Valid session
        valid_session = SessionState(
            session_id="valid-session",
            phase=Phase.DONE,
            progress=100,
            requirements={"description": "test"},
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        assert export_service.validate_session_for_export(valid_session) is True
        
        # Invalid session - wrong phase
        invalid_session = valid_session
        invalid_session.phase = Phase.PARSING
        assert export_service.validate_session_for_export(invalid_session) is False
    
    def test_cleanup_integration(self, temp_dirs):
        """Test cleanup functionality integration."""
        cache_dir, export_dir = temp_dirs
        
        export_service = ExportService(export_dir)
        
        # Create some test files
        old_file = export_dir / "agentic_or_not_old_20240101_120000.json"
        new_file = export_dir / "agentic_or_not_new_20240102_120000.json"
        
        old_file.write_text('{"test": "old"}')
        new_file.write_text('{"test": "new"}')
        
        # Mock file modification times
        import os
        import time
        
        # Set old file to be 25 hours old
        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))
        
        # Cleanup files older than 24 hours
        deleted_count = export_service.cleanup_old_exports(max_age_hours=24)
        
        assert deleted_count == 1
        assert not old_file.exists()
        assert new_file.exists()
    
    def test_multiple_format_support(self, temp_dirs, sample_session):
        """Test support for multiple export formats."""
        cache_dir, export_dir = temp_dirs
        
        export_service = ExportService(export_dir)
        
        # Test all supported formats
        formats = export_service.get_supported_formats()
        assert "json" in formats
        assert "md" in formats
        assert "markdown" in formats
        
        # Export in each format
        for format_name in ["json", "md", "markdown"]:
            file_path, download_url, file_info = export_service.export_session(sample_session, format_name)
            
            assert Path(file_path).exists()
            assert file_info["size_bytes"] > 0
            
            # Clean up
            Path(file_path).unlink()
    
    def test_unsupported_format_error(self, temp_dirs, sample_session):
        """Test error handling for unsupported formats."""
        cache_dir, export_dir = temp_dirs
        
        export_service = ExportService(export_dir)
        
        with pytest.raises(ValueError, match="Unsupported format 'xml'"):
            export_service.export_session(sample_session, "xml")