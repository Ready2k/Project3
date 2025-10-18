"""Base exporter functionality."""

import hashlib
import os
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

from app.state.store import SessionState


class BaseExporter(ABC):
    """Abstract base class for all exporters."""

    def __init__(self, export_path: Path, base_url: Optional[str] = None):
        """Initialize exporter.

        Args:
            export_path: Directory to store exported files
            base_url: Base URL for generating download URLs
        """
        self.export_path = export_path
        self.export_path.mkdir(parents=True, exist_ok=True)
        self.base_url = base_url or "file://"

    @abstractmethod
    def export_session(self, session: SessionState) -> str:
        """Export session to file.

        Args:
            session: Session state to export

        Returns:
            Path to the exported file
        """
        raise NotImplementedError("Subclasses must implement export_session")

    @abstractmethod
    def get_file_extension(self) -> str:
        """Get file extension for this exporter."""
        raise NotImplementedError("Subclasses must implement get_file_extension")

    def generate_filename(
        self, session: SessionState, include_timestamp: bool = True
    ) -> str:
        """Generate filename for export.

        Args:
            session: Session state
            include_timestamp: Whether to include timestamp in filename

        Returns:
            Generated filename
        """
        base_name = f"agentic_or_not_{session.session_id}"

        if include_timestamp:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            base_name += f"_{timestamp}"

        return f"{base_name}.{self.get_file_extension()}"

    def generate_download_url(self, file_path: str) -> str:
        """Generate download URL for exported file.

        Args:
            file_path: Path to the exported file

        Returns:
            Download URL
        """
        if self.base_url.startswith("file://"):
            return f"file://{os.path.abspath(file_path)}"

        # For HTTP URLs, use relative path from export directory
        relative_path = Path(file_path).relative_to(self.export_path)
        return urljoin(self.base_url, str(relative_path))

    def get_file_hash(self, file_path: str) -> str:
        """Generate SHA-256 hash of exported file.

        Args:
            file_path: Path to the file

        Returns:
            SHA-256 hash as hex string
        """
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                sha256_hash.update(chunk)
        return sha256_hash.hexdigest()

    def get_file_info(self, file_path: str) -> dict:
        """Get file information including size and hash.

        Args:
            file_path: Path to the file

        Returns:
            Dictionary with file information
        """
        file_stat = os.stat(file_path)
        return {
            "path": file_path,
            "size_bytes": file_stat.st_size,
            "created_at": datetime.fromtimestamp(file_stat.st_ctime).isoformat(),
            "modified_at": datetime.fromtimestamp(file_stat.st_mtime).isoformat(),
            "sha256": self.get_file_hash(file_path),
        }
