"""Markdown export functionality."""

from datetime import datetime
from pathlib import Path
from typing import Optional

from app.exporters.base import BaseExporter
from app.state.store import SessionState


class MarkdownExporter(BaseExporter):
    """Exports session results to Markdown format with proper formatting."""

    def __init__(self, export_path: Path, base_url: Optional[str] = None):
        super().__init__(export_path, base_url)

    def get_file_extension(self) -> str:
        """Get file extension for Markdown exports."""
        return "md"

    def export_session(self, session: SessionState) -> str:
        """Export session to Markdown file with proper formatting.

        Args:
            session: Session state to export

        Returns:
            Path to the exported file

        Raises:
            ValueError: If session data is invalid for export
        """
        # Validate session data
        if not session.session_id:
            raise ValueError("Session ID is required for export")

        # Generate Markdown content
        content = self._generate_markdown(session)

        # Validate content is not empty
        if not content.strip():
            raise ValueError("Generated Markdown content is empty")

        # Generate filename
        filename = self.generate_filename(session)
        file_path = self.export_path / filename

        # Write to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

        return str(file_path)

    def _generate_markdown(self, session: SessionState) -> str:
        """Generate Markdown content from session with proper formatting."""
        lines = []

        # Header with metadata table
        lines.append("# Automated AI Assessment (AAA) - Automation Feasibility Report")
        lines.append("")
        lines.append("| Field | Value |")
        lines.append("|-------|-------|")
        lines.append(f"| Session ID | `{session.session_id}` |")
        lines.append(f"| Generated | {datetime.now().strftime('%Y-%m-%d %H:%M:%S')} |")
        lines.append(f"| Processing Phase | {session.phase.value} |")
        lines.append(f"| Progress | {session.progress}% |")
        lines.append("")

        # Requirements section
        lines.append("## 📋 Requirements")
        lines.append("")
        description = session.requirements.get("description", "No description provided")
        lines.append("**Description:**")
        lines.append(f"> {description}")
        lines.append("")

        # Requirements details table
        req_details = []
        if session.requirements.get("domain"):
            req_details.append(("Domain", session.requirements["domain"]))
        if session.requirements.get("frequency"):
            req_details.append(("Frequency", session.requirements["frequency"]))
        if session.requirements.get("criticality"):
            req_details.append(("Criticality", session.requirements["criticality"]))
        if session.requirements.get("pattern_types"):
            req_details.append(
                ("Pattern Types", ", ".join(session.requirements["pattern_types"]))
            )

        if req_details:
            lines.append("| Attribute | Value |")
            lines.append("|-----------|-------|")
            for attr, value in req_details:
                lines.append(f"| {attr} | {value} |")
            lines.append("")

        # Overall Assessment with emoji
        overall_feasibility = self._get_overall_feasibility(session)
        feasibility_emoji = self._get_feasibility_emoji(overall_feasibility)
        lines.append(f"## {feasibility_emoji} Overall Assessment")
        lines.append("")
        lines.append(f"**Feasibility:** {overall_feasibility}")
        lines.append("")

        # Recommendations with detailed formatting
        if session.recommendations:
            lines.append("## 🎯 Recommendations")
            lines.append("")

            for i, rec in enumerate(session.recommendations, 1):
                confidence_bar = self._generate_confidence_bar(rec.confidence)
                lines.append(f"### {i}. Pattern {rec.pattern_id}")
                lines.append("")
                lines.append(f"**Feasibility:** {rec.feasibility}")
                lines.append(f"**Confidence:** {rec.confidence:.1%} {confidence_bar}")
                lines.append("")

                if rec.tech_stack:
                    lines.append("**Technology Stack:**")
                    for tech in rec.tech_stack:
                        lines.append(f"- `{tech}`")
                    lines.append("")

                lines.append("**Reasoning:**")
                lines.append(f"> {rec.reasoning}")
                lines.append("")
                lines.append("---")
                lines.append("")

        # Pattern Matches with scoring details
        if session.matches:
            lines.append("## 🔍 Pattern Analysis")
            lines.append("")

            for match in session.matches:
                score_bar = self._generate_confidence_bar(match.score)
                lines.append(f"### {match.pattern_id}")
                lines.append("")
                lines.append(f"**Match Score:** {match.score:.1%} {score_bar}")
                lines.append(f"**Confidence:** {match.confidence:.1%}")
                lines.append("")
                lines.append("**Analysis:**")
                lines.append(f"> {match.rationale}")
                lines.append("")

        # Q&A History with better formatting
        if session.qa_history:
            lines.append("## ❓ Questions & Answers")
            lines.append("")

            for i, qa in enumerate(session.qa_history, 1):
                lines.append(f"### Round {i}")
                lines.append("")

                if qa.questions:
                    lines.append("**Questions Asked:**")
                    for question in qa.questions:
                        lines.append(f"- {question}")
                    lines.append("")

                if qa.answers:
                    lines.append("**Responses:**")
                    for field, answer in qa.answers.items():
                        formatted_field = field.replace("_", " ").title()
                        lines.append(f"- **{formatted_field}:** {answer}")
                    lines.append("")

                lines.append(
                    f"*Timestamp: {qa.timestamp.strftime('%Y-%m-%d %H:%M:%S')}*"
                )
                lines.append("")

        # Footer
        lines.append("---")
        lines.append("")
        lines.append("*Generated by Automated AI Assessment (AAA)*")
        lines.append("")

        return "\n".join(lines)

    def _get_feasibility_emoji(self, feasibility: str) -> str:
        """Get emoji for feasibility status."""
        emoji_map = {
            "Automatable": "✅",
            "Partially Automatable": "⚠️",
            "Not Automatable": "❌",
            "Unknown": "❓",
        }
        return emoji_map.get(feasibility, "❓")

    def _generate_confidence_bar(self, confidence: float) -> str:
        """Generate a visual confidence bar using Unicode blocks."""
        if confidence < 0 or confidence > 1:
            return ""

        # Use Unicode block characters for visual representation
        filled_blocks = int(confidence * 10)
        empty_blocks = 10 - filled_blocks

        bar = "█" * filled_blocks + "░" * empty_blocks
        return f"`{bar}`"

    def _get_overall_feasibility(self, session: SessionState) -> str:
        """Determine overall feasibility from recommendations."""
        if not session.recommendations:
            return "Unknown"

        # Take the feasibility of the highest confidence recommendation
        best_rec = max(session.recommendations, key=lambda r: r.confidence)
        return best_rec.feasibility
