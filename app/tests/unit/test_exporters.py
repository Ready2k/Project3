"""Unit tests for export functionality."""

import json
import tempfile
from datetime import datetime
from pathlib import Path
from unittest.mock import patch

import pytest
import jsonschema

from app.exporters.base import BaseExporter
from app.exporters.json_exporter import JSONExporter
from app.exporters.markdown_exporter import MarkdownExporter
from app.exporters.service import ExportService
from app.state.store import SessionState, Phase, QAExchange, PatternMatch, Recommendation


class TestJSONExporter:
    """Test cases for JSON exporter."""
    
    @pytest.fixture
    def temp_export_path(self):
        """Create temporary export directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session state for testing."""
        return SessionState(
            session_id="test-session-123",
            phase=Phase.DONE,
            progress=100,
            requirements={
                "description": "Automate user onboarding process",
                "domain": "HR",
                "frequency": "daily",
                "criticality": "high"
            },
            missing_fields=[],
            qa_history=[
                QAExchange(
                    questions=["What is the expected volume?"],
                    answers={"volume": "100 users per day"},
                    timestamp=datetime(2024, 1, 1, 12, 0, 0)
                )
            ],
            matches=[
                PatternMatch(
                    pattern_id="PAT-001",
                    score=0.85,
                    rationale="High match for workflow automation",
                    confidence=0.9
                )
            ],
            recommendations=[
                Recommendation(
                    pattern_id="PAT-001",
                    feasibility="Automatable",
                    confidence=0.9,
                    tech_stack=["Python", "FastAPI", "PostgreSQL"],
                    reasoning="Well-defined process with clear inputs and outputs"
                )
            ],
            created_at=datetime(2024, 1, 1, 10, 0, 0),
            updated_at=datetime(2024, 1, 1, 12, 0, 0)
        )
    
    def test_json_exporter_initialization(self, temp_export_path):
        """Test JSON exporter initialization."""
        exporter = JSONExporter(temp_export_path)
        
        assert exporter.export_path == temp_export_path
        assert temp_export_path.exists()
        assert exporter.export_schema is not None
        assert exporter.get_file_extension() == "json"
    
    def test_json_export_session_success(self, temp_export_path, sample_session):
        """Test successful JSON export."""
        exporter = JSONExporter(temp_export_path)
        
        file_path = exporter.export_session(sample_session)
        
        # Verify file was created
        assert Path(file_path).exists()
        assert file_path.endswith(".json")
        
        # Verify file content
        with open(file_path, 'r') as f:
            export_data = json.load(f)
        
        assert export_data["session_id"] == "test-session-123"
        assert export_data["feasibility_assessment"] == "Automatable"
        assert len(export_data["recommendations"]) == 1
        assert len(export_data["pattern_matches"]) == 1
        assert len(export_data["qa_history"]) == 1
    
    def test_json_export_schema_validation(self, temp_export_path, sample_session):
        """Test JSON export schema validation."""
        exporter = JSONExporter(temp_export_path)
        
        # Export should succeed with valid data
        file_path = exporter.export_session(sample_session)
        
        # Verify exported data validates against schema
        with open(file_path, 'r') as f:
            export_data = json.load(f)
        
        # Should not raise ValidationError
        jsonschema.validate(export_data, exporter.export_schema)
    
    def test_json_export_invalid_data(self, temp_export_path):
        """Test JSON export with invalid session data."""
        exporter = JSONExporter(temp_export_path)
        
        # Create session with invalid recommendation data (invalid feasibility)
        invalid_rec = Recommendation(
            pattern_id="PAT-001",
            feasibility="Invalid Feasibility",  # This should fail schema validation
            confidence=0.9,
            tech_stack=["Python"],
            reasoning="Test"
        )
        
        invalid_session = SessionState(
            session_id="test-invalid",
            phase=Phase.DONE,
            progress=100,
            requirements={"description": "test"},
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[invalid_rec],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        # Should raise ValueError due to schema validation
        with pytest.raises(ValueError, match="Export data validation failed"):
            exporter.export_session(invalid_session)
    
    def test_validate_export_data(self, temp_export_path):
        """Test export data validation method."""
        exporter = JSONExporter(temp_export_path)
        
        valid_data = {
            "session_id": "test-123",
            "export_timestamp": "2024-01-01T12:00:00",
            "requirements": {"description": "test"},
            "feasibility_assessment": "Automatable",
            "recommendations": [],
            "pattern_matches": [],
            "qa_history": [],
            "processing_phases": {"final_phase": "DONE", "progress": 100}
        }
        
        assert exporter.validate_export_data(valid_data) is True
        
        # Test invalid data
        invalid_data = {"invalid": "data"}
        assert exporter.validate_export_data(invalid_data) is False
    
    def test_get_overall_feasibility(self, temp_export_path, sample_session):
        """Test overall feasibility determination."""
        exporter = JSONExporter(temp_export_path)
        
        # Test with recommendations
        feasibility = exporter._get_overall_feasibility(sample_session)
        assert feasibility == "Automatable"
        
        # Test with no recommendations
        sample_session.recommendations = []
        feasibility = exporter._get_overall_feasibility(sample_session)
        assert feasibility == "Unknown"


class TestMarkdownExporter:
    """Test cases for Markdown exporter."""
    
    @pytest.fixture
    def temp_export_path(self):
        """Create temporary export directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session state for testing."""
        return SessionState(
            session_id="test-session-456",
            phase=Phase.DONE,
            progress=100,
            requirements={
                "description": "Automate invoice processing",
                "domain": "Finance",
                "frequency": "weekly",
                "criticality": "medium"
            },
            missing_fields=[],
            qa_history=[
                QAExchange(
                    questions=["What file formats are supported?"],
                    answers={"file_formats": "PDF, CSV, Excel"},
                    timestamp=datetime(2024, 1, 2, 14, 30, 0)
                )
            ],
            matches=[
                PatternMatch(
                    pattern_id="PAT-002",
                    score=0.75,
                    rationale="Good match for document processing",
                    confidence=0.8
                )
            ],
            recommendations=[
                Recommendation(
                    pattern_id="PAT-002",
                    feasibility="Partially Automatable",
                    confidence=0.8,
                    tech_stack=["Python", "OCR", "ML"],
                    reasoning="Requires human review for complex cases"
                )
            ],
            created_at=datetime(2024, 1, 2, 10, 0, 0),
            updated_at=datetime(2024, 1, 2, 14, 30, 0)
        )
    
    def test_markdown_exporter_initialization(self, temp_export_path):
        """Test Markdown exporter initialization."""
        exporter = MarkdownExporter(temp_export_path)
        
        assert exporter.export_path == temp_export_path
        assert temp_export_path.exists()
        assert exporter.get_file_extension() == "md"
    
    def test_markdown_export_session_success(self, temp_export_path, sample_session):
        """Test successful Markdown export."""
        exporter = MarkdownExporter(temp_export_path)
        
        file_path = exporter.export_session(sample_session)
        
        # Verify file was created
        assert Path(file_path).exists()
        assert file_path.endswith(".md")
        
        # Verify file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        assert "# Automated AI Assessment (AAA) - Automation Feasibility Report" in content
        assert "test-session-456" in content
        assert "Automate invoice processing" in content
        assert "Partially Automatable" in content
        assert "PAT-002" in content
        assert "Python" in content
        assert "OCR" in content
    
    def test_markdown_export_invalid_session(self, temp_export_path):
        """Test Markdown export with invalid session."""
        exporter = MarkdownExporter(temp_export_path)
        
        # Session with empty session_id
        invalid_session = SessionState(
            session_id="",
            phase=Phase.DONE,
            progress=100,
            requirements={},
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
        
        with pytest.raises(ValueError, match="Session ID is required"):
            exporter.export_session(invalid_session)
    
    def test_markdown_formatting_elements(self, temp_export_path, sample_session):
        """Test Markdown formatting elements."""
        exporter = MarkdownExporter(temp_export_path)
        
        file_path = exporter.export_session(sample_session)
        
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Check for proper Markdown formatting
        assert "| Field | Value |" in content  # Tables
        assert "|-------|-------|" in content  # Table separators
        assert "> Automate invoice processing" in content  # Blockquotes
        assert "- `Python`" in content  # Code formatting
        assert "**Feasibility:**" in content  # Bold text
        assert "---" in content  # Horizontal rules
        assert "✅" in content or "⚠️" in content or "❌" in content  # Emojis
    
    def test_confidence_bar_generation(self, temp_export_path):
        """Test confidence bar generation."""
        exporter = MarkdownExporter(temp_export_path)
        
        # Test various confidence levels
        assert exporter._generate_confidence_bar(0.0) == "`░░░░░░░░░░`"
        assert exporter._generate_confidence_bar(0.5) == "`█████░░░░░`"
        assert exporter._generate_confidence_bar(1.0) == "`██████████`"
        assert exporter._generate_confidence_bar(-0.1) == ""
        assert exporter._generate_confidence_bar(1.1) == ""
    
    def test_feasibility_emoji_mapping(self, temp_export_path):
        """Test feasibility emoji mapping."""
        exporter = MarkdownExporter(temp_export_path)
        
        assert exporter._get_feasibility_emoji("Automatable") == "✅"
        assert exporter._get_feasibility_emoji("Partially Automatable") == "⚠️"
        assert exporter._get_feasibility_emoji("Not Automatable") == "❌"
        assert exporter._get_feasibility_emoji("Unknown") == "❓"
        assert exporter._get_feasibility_emoji("Invalid") == "❓"


class TestBaseExporter:
    """Test cases for base exporter functionality."""
    
    @pytest.fixture
    def temp_export_path(self):
        """Create temporary export directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session state."""
        return SessionState(
            session_id="base-test-789",
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
    
    def test_filename_generation(self, temp_export_path, sample_session):
        """Test filename generation."""
        
        class TestExporter(BaseExporter):
            def export_session(self, session):
                return ""
            def get_file_extension(self):
                return "test"
        
        exporter = TestExporter(temp_export_path)
        
        # Test with timestamp
        filename = exporter.generate_filename(sample_session, include_timestamp=True)
        assert filename.startswith("agentic_or_not_base-test-789_")
        assert filename.endswith(".test")
        
        # Test without timestamp
        filename = exporter.generate_filename(sample_session, include_timestamp=False)
        assert filename == "agentic_or_not_base-test-789.test"
    
    def test_download_url_generation(self, temp_export_path):
        """Test download URL generation."""
        
        class TestExporter(BaseExporter):
            def export_session(self, session):
                return ""
            def get_file_extension(self):
                return "test"
        
        # Test file:// URL
        exporter = TestExporter(temp_export_path, base_url="file://")
        url = exporter.generate_download_url("/path/to/file.test")
        assert url.startswith("file://")
        
        # Test HTTP URL
        exporter = TestExporter(temp_export_path, base_url="https://example.com/exports/")
        test_file = temp_export_path / "test.txt"
        test_file.write_text("test")
        url = exporter.generate_download_url(str(test_file))
        assert url.startswith("https://example.com/exports/")
    
    def test_file_info_generation(self, temp_export_path):
        """Test file information generation."""
        
        class TestExporter(BaseExporter):
            def export_session(self, session):
                return ""
            def get_file_extension(self):
                return "test"
        
        exporter = TestExporter(temp_export_path)
        
        # Create test file
        test_file = temp_export_path / "test.txt"
        test_content = "test content for hashing"
        test_file.write_text(test_content)
        
        file_info = exporter.get_file_info(str(test_file))
        
        assert file_info["path"] == str(test_file)
        assert file_info["size_bytes"] == len(test_content)
        assert "created_at" in file_info
        assert "modified_at" in file_info
        assert "sha256" in file_info
        assert len(file_info["sha256"]) == 64  # SHA-256 hex length


class TestExportService:
    """Test cases for export service."""
    
    @pytest.fixture
    def temp_export_path(self):
        """Create temporary export directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def sample_session(self):
        """Create sample session state."""
        return SessionState(
            session_id="service-test-999",
            phase=Phase.DONE,
            progress=100,
            requirements={"description": "Service test"},
            missing_fields=[],
            qa_history=[],
            matches=[],
            recommendations=[
                Recommendation(
                    pattern_id="PAT-999",
                    feasibility="Automatable",
                    confidence=0.9,
                    tech_stack=["Test"],
                    reasoning="Test reasoning"
                )
            ],
            created_at=datetime.now(),
            updated_at=datetime.now()
        )
    
    def test_export_service_initialization(self, temp_export_path):
        """Test export service initialization."""
        service = ExportService(temp_export_path)
        
        assert service.export_path == temp_export_path
        assert "json" in service.exporters
        assert "md" in service.exporters
        assert "markdown" in service.exporters
    
    def test_get_supported_formats(self, temp_export_path):
        """Test getting supported formats."""
        service = ExportService(temp_export_path)
        
        formats = service.get_supported_formats()
        assert "json" in formats
        assert "md" in formats
        assert "markdown" in formats
    
    def test_export_session_json(self, temp_export_path, sample_session):
        """Test exporting session in JSON format."""
        service = ExportService(temp_export_path)
        
        file_path, download_url, file_info = service.export_session(sample_session, "json")
        
        assert Path(file_path).exists()
        assert file_path.endswith(".json")
        assert download_url.startswith("file://")
        assert file_info["size_bytes"] > 0
    
    def test_export_session_markdown(self, temp_export_path, sample_session):
        """Test exporting session in Markdown format."""
        service = ExportService(temp_export_path)
        
        file_path, download_url, file_info = service.export_session(sample_session, "md")
        
        assert Path(file_path).exists()
        assert file_path.endswith(".md")
        assert download_url.startswith("file://")
        assert file_info["size_bytes"] > 0
    
    def test_export_session_unsupported_format(self, temp_export_path, sample_session):
        """Test exporting with unsupported format."""
        service = ExportService(temp_export_path)
        
        with pytest.raises(ValueError, match="Unsupported format 'xml'"):
            service.export_session(sample_session, "xml")
    
    def test_validate_session_for_export(self, temp_export_path):
        """Test session validation for export."""
        service = ExportService(temp_export_path)
        
        # Valid session
        valid_session = SessionState(
            session_id="valid-123",
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
        
        assert service.validate_session_for_export(valid_session) is True
        
        # Invalid session - no session_id
        invalid_session = valid_session
        invalid_session.session_id = ""
        assert service.validate_session_for_export(invalid_session) is False
        
        # Invalid session - no requirements
        invalid_session.session_id = "valid-123"
        invalid_session.requirements = {}
        assert service.validate_session_for_export(invalid_session) is False
        
        # Invalid session - wrong phase
        invalid_session.requirements = {"description": "test"}
        invalid_session.phase = Phase.PARSING
        assert service.validate_session_for_export(invalid_session) is False
    
    def test_cleanup_old_exports(self, temp_export_path):
        """Test cleanup of old export files."""
        service = ExportService(temp_export_path)
        
        # Create some test files
        old_file = temp_export_path / "agentic_or_not_old_20240101_120000.json"
        new_file = temp_export_path / "agentic_or_not_new_20240102_120000.json"
        other_file = temp_export_path / "other_file.txt"
        
        old_file.write_text("{}")
        new_file.write_text("{}")
        other_file.write_text("test")
        
        # Mock file modification times
        import os
        import time
        
        # Set old file to be 25 hours old
        old_time = time.time() - (25 * 3600)
        os.utime(old_file, (old_time, old_time))
        
        # Cleanup files older than 24 hours
        deleted_count = service.cleanup_old_exports(max_age_hours=24)
        
        assert deleted_count == 1
        assert not old_file.exists()
        assert new_file.exists()
        assert other_file.exists()  # Non-export files should not be deleted