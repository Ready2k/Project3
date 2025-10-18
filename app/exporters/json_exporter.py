"""JSON export functionality."""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

import jsonschema

from app.exporters.base import BaseExporter
from app.state.store import SessionState


class JSONExporter(BaseExporter):
    """Exports session results to JSON format with schema validation."""

    def __init__(self, export_path: Path, base_url: Optional[str] = None):
        super().__init__(export_path, base_url)

        # Load export schema for validation
        schema_path = Path(__file__).parent / "export_schema.json"
        with open(schema_path, "r") as f:
            self.export_schema = json.load(f)

    def get_file_extension(self) -> str:
        """Get file extension for JSON exports."""
        return "json"

    def export_session(self, session: SessionState) -> str:
        """Export session to JSON file with schema validation.

        Args:
            session: Session state to export

        Returns:
            Path to the exported file

        Raises:
            ValueError: If export data doesn't match schema
        """
        # Create export data
        export_data = {
            "session_id": session.session_id,
            "export_timestamp": datetime.now().isoformat(),
            "requirements": session.requirements,
            "feasibility_assessment": self._get_overall_feasibility(session),
            "recommendations": [rec.to_dict() for rec in session.recommendations],
            "pattern_matches": [match.to_dict() for match in session.matches],
            "qa_history": [qa.to_dict() for qa in session.qa_history],
            "processing_phases": {
                "final_phase": session.phase.value,
                "progress": session.progress,
            },
        }

        # Validate against schema
        try:
            jsonschema.validate(export_data, self.export_schema)
        except jsonschema.ValidationError as e:
            raise ValueError(f"Export data validation failed: {e.message}")

        # Generate filename
        filename = self.generate_filename(session)
        file_path = self.export_path / filename

        # Write to file
        with open(file_path, "w") as f:
            json.dump(export_data, f, indent=2, ensure_ascii=False)

        return str(file_path)

    def validate_export_data(self, export_data: Dict[str, Any]) -> bool:
        """Validate export data against schema.

        Args:
            export_data: Data to validate

        Returns:
            True if valid, False otherwise
        """
        try:
            jsonschema.validate(export_data, self.export_schema)
            return True
        except jsonschema.ValidationError:
            return False

    def _get_overall_feasibility(self, session: SessionState) -> str:
        """Determine overall feasibility from recommendations."""
        if not session.recommendations:
            return "Unknown"

        # Take the feasibility of the highest confidence recommendation
        best_rec = max(session.recommendations, key=lambda r: r.confidence)
        return best_rec.feasibility
