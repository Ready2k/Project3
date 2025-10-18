"""Export service for coordinating different export formats."""

from pathlib import Path
from typing import Dict, Optional, Tuple

from app.exporters.base import BaseExporter
from app.exporters.json_exporter import JSONExporter
from app.exporters.markdown_exporter import MarkdownExporter
from app.exporters.comprehensive_exporter import ComprehensiveExporter
from app.state.store import SessionState


class ExportService:
    """Service for managing exports in multiple formats."""

    def __init__(
        self, export_path: Path, base_url: Optional[str] = None, llm_provider=None
    ):
        """Initialize export service.

        Args:
            export_path: Directory to store exported files
            base_url: Base URL for generating download URLs
            llm_provider: LLM provider for comprehensive analysis
        """
        self.export_path = export_path
        self.base_url = base_url
        self.llm_provider = llm_provider

        # Initialize exporters
        self.exporters: Dict[str, BaseExporter] = {
            "json": JSONExporter(export_path, base_url),
            "md": MarkdownExporter(export_path, base_url),
            "markdown": MarkdownExporter(export_path, base_url),  # Alias
            "comprehensive": ComprehensiveExporter(export_path, base_url, llm_provider),
            "report": ComprehensiveExporter(
                export_path, base_url, llm_provider
            ),  # Alias
        }

    def get_supported_formats(self) -> list:
        """Get list of supported export formats."""
        return list(self.exporters.keys())

    def export_session(
        self, session: SessionState, format: str
    ) -> Tuple[str, str, dict]:
        """Export session in specified format.

        Args:
            session: Session state to export
            format: Export format ("json" or "md"/"markdown")

        Returns:
            Tuple of (file_path, download_url, file_info)

        Raises:
            ValueError: If format is not supported
        """
        if format not in self.exporters:
            supported = ", ".join(self.get_supported_formats())
            raise ValueError(
                f"Unsupported format '{format}'. Supported formats: {supported}"
            )

        exporter = self.exporters[format]

        # Export the session
        file_path = exporter.export_session(session)

        # Generate download URL
        download_url = exporter.generate_download_url(file_path)

        # Get file information
        file_info = exporter.get_file_info(file_path)

        return file_path, download_url, file_info

    def validate_session_for_export(self, session: SessionState) -> bool:
        """Validate that session has required data for export.

        Args:
            session: Session state to validate

        Returns:
            True if session is valid for export
        """
        if not session.session_id:
            return False

        if not session.requirements:
            return False

        # Session should be in a completed or near-completed state
        if session.phase.value not in ["MATCHING", "RECOMMENDING", "DONE"]:
            return False

        return True

    def cleanup_old_exports(self, max_age_hours: int = 24) -> int:
        """Clean up old export files.

        Args:
            max_age_hours: Maximum age of files to keep in hours

        Returns:
            Number of files deleted
        """
        from datetime import datetime, timedelta

        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        cutoff_timestamp = cutoff_time.timestamp()

        deleted_count = 0

        for file_path in self.export_path.glob("agentic_or_not_*"):
            if file_path.is_file():
                file_mtime = file_path.stat().st_mtime
                if file_mtime < cutoff_timestamp:
                    try:
                        file_path.unlink()
                        deleted_count += 1
                    except OSError:
                        # Ignore files that can't be deleted
                        pass

        return deleted_count
