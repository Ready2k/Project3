"""Export controls component for export functionality."""

import json
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import streamlit as st

from app.ui.components.base import BaseComponent

# Import logger for error handling
from app.utils.logger import app_logger


class ExportControlsComponent(BaseComponent):
    """Component for exporting analysis results in various formats."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.export_formats = ["JSON", "Markdown", "HTML", "CSV"]
    
    def render(self, session_id: str, recommendations: Dict[str, Any], **kwargs) -> Any:
        """Render the export controls component."""
        if not recommendations:
            st.info("No data available for export.")
            return
        
        st.subheader("📤 Export Results")
        
        # Export format selection
        col1, col2 = st.columns([1, 1])
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                self.export_formats,
                key="export_format_select"
            )
        
        with col2:
            include_diagrams = st.checkbox(
                "Include Diagrams",
                value=True,
                help="Include diagram code in export"
            )
        
        # Export options
        st.write("**Export Options:**")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            include_metadata = st.checkbox("Include Metadata", value=True)
        
        with col2:
            include_raw_data = st.checkbox("Include Raw Data", value=False)
        
        with col3:
            compress_export = st.checkbox("Compress Export", value=False)
        
        # Export preview
        if st.button("👁️ Preview Export", key="preview_export"):
            self._show_export_preview(recommendations, export_format.lower(), {
                'include_diagrams': include_diagrams,
                'include_metadata': include_metadata,
                'include_raw_data': include_raw_data
            })
        
        st.divider()
        
        # Export buttons
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("📥 Download Export", key="download_export", type="primary"):
                self._download_export(session_id, recommendations, export_format.lower(), {
                    'include_diagrams': include_diagrams,
                    'include_metadata': include_metadata,
                    'include_raw_data': include_raw_data,
                    'compress': compress_export
                })
        
        with col2:
            if st.button("💾 Save to File", key="save_export"):
                self._save_export_file(session_id, recommendations, export_format.lower(), {
                    'include_diagrams': include_diagrams,
                    'include_metadata': include_metadata,
                    'include_raw_data': include_raw_data
                })
        
        with col3:
            if st.button("📧 Email Export", key="email_export"):
                self._email_export(session_id, recommendations, export_format.lower())
        
        # Export history
        st.divider()
        self._render_export_history()
    
    def _show_export_preview(self, recommendations: Dict[str, Any], format_type: str, options: Dict[str, bool]):
        """Show preview of export data."""
        st.subheader(f"👁️ {format_type.upper()} Export Preview")
        
        try:
            export_data = self._prepare_export_data(recommendations, options)
            
            if format_type == "json":
                preview_data = json.dumps(export_data, indent=2)
                st.code(preview_data, language="json")
            
            elif format_type == "markdown":
                preview_data = self._format_as_markdown(export_data)
                st.markdown("```markdown\n" + preview_data + "\n```")
            
            elif format_type == "html":
                preview_data = self._format_as_html(export_data)
                st.components.v1.html(preview_data, height=400, scrolling=True)
            
            elif format_type == "csv":
                preview_data = self._format_as_csv(export_data)
                st.code(preview_data, language="csv")
            
        except Exception as e:
            st.error(f"Failed to generate preview: {str(e)}")
            app_logger.error(f"Export preview failed: {str(e)}")
    
    def _download_export(self, session_id: str, recommendations: Dict[str, Any], format_type: str, options: Dict[str, Any]):
        """Download export file."""
        try:
            export_data = self._prepare_export_data(recommendations, options)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            if format_type == "json":
                content = json.dumps(export_data, indent=2)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.json"
                mime_type = "application/json"
            
            elif format_type == "markdown":
                content = self._format_as_markdown(export_data)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.md"
                mime_type = "text/markdown"
            
            elif format_type == "html":
                content = self._format_as_html(export_data)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.html"
                mime_type = "text/html"
            
            elif format_type == "csv":
                content = self._format_as_csv(export_data)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.csv"
                mime_type = "text/csv"
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            # Compress if requested
            if options.get('compress', False):
                content = self._compress_content(content, filename)
                filename = filename + ".gz"
                mime_type = "application/gzip"
            
            st.download_button(
                label=f"📥 Download {format_type.upper()}",
                data=content,
                file_name=filename,
                mime=mime_type
            )
            
            # Log export
            self._log_export(session_id, format_type, filename)
            
            st.success(f"✅ Export prepared! Click the download button above.")
            
        except Exception as e:
            st.error(f"Failed to prepare export: {str(e)}")
            app_logger.error(f"Export preparation failed: {str(e)}")
    
    def _save_export_file(self, session_id: str, recommendations: Dict[str, Any], format_type: str, options: Dict[str, Any]):
        """Save export file to exports directory."""
        try:
            export_data = self._prepare_export_data(recommendations, options)
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Create exports directory
            exports_dir = Path("exports")
            exports_dir.mkdir(exist_ok=True)
            
            if format_type == "json":
                content = json.dumps(export_data, indent=2)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.json"
            
            elif format_type == "markdown":
                content = self._format_as_markdown(export_data)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.md"
            
            elif format_type == "html":
                content = self._format_as_html(export_data)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.html"
            
            elif format_type == "csv":
                content = self._format_as_csv(export_data)
                filename = f"analysis_results_{session_id[:8]}_{timestamp}.csv"
            
            else:
                raise ValueError(f"Unsupported export format: {format_type}")
            
            # Save file
            filepath = exports_dir / filename
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            
            # Log export
            self._log_export(session_id, format_type, filename)
            
            st.success(f"✅ Export saved as `{filename}` in exports directory.")
            
        except Exception as e:
            st.error(f"Failed to save export: {str(e)}")
            app_logger.error(f"Export save failed: {str(e)}")
    
    def _email_export(self, session_id: str, recommendations: Dict[str, Any], format_type: str):
        """Email export (placeholder for future implementation)."""
        st.info("📧 Email export feature coming soon!")
        
        # For now, show instructions
        st.markdown("""
        **To email this export:**
        1. Download the export file using the "Download Export" button
        2. Attach the file to your email
        3. Send to the desired recipients
        
        **Future features:**
        - Direct email integration
        - Scheduled exports
        - Team sharing
        """)
    
    def _prepare_export_data(self, recommendations: Dict[str, Any], options: Dict[str, bool]) -> Dict[str, Any]:
        """Prepare data for export based on options."""
        export_data = {
            "export_info": {
                "timestamp": datetime.now().isoformat(),
                "session_id": st.session_state.get('session_id'),
                "export_version": "1.0"
            }
        }
        
        # Core recommendations data
        export_data["recommendations"] = recommendations.copy()
        
        # Include metadata if requested
        if options.get('include_metadata', True):
            export_data["metadata"] = {
                "provider_config": st.session_state.get('provider_config', {}),
                "current_phase": st.session_state.get('current_phase'),
                "progress": st.session_state.get('progress', 0),
                "qa_questions": st.session_state.get('qa_questions', []) if options.get('include_raw_data') else len(st.session_state.get('qa_questions', []))
            }
        
        # Include diagrams if requested
        if options.get('include_diagrams', True):
            diagrams = []
            
            # Check for various diagram types in session state
            diagram_keys = ['current_diagram', 'current_agent_diagram', 'context_diagram', 'container_diagram']
            
            for key in diagram_keys:
                if hasattr(st.session_state, key) and getattr(st.session_state, key):
                    diagrams.append(getattr(st.session_state, key))
            
            if diagrams:
                export_data["diagrams"] = diagrams
        
        # Include raw data if requested
        if options.get('include_raw_data', False):
            export_data["raw_data"] = {
                "session_state": {k: v for k, v in st.session_state.items() if not k.startswith('_')},
                "processing_logs": []  # Placeholder for processing logs
            }
        
        return export_data
    
    def _format_as_markdown(self, export_data: Dict[str, Any]) -> str:
        """Format export data as Markdown."""
        recommendations = export_data.get("recommendations", {})
        metadata = export_data.get("metadata", {})
        export_info = export_data.get("export_info", {})
        
        markdown = f"""# Analysis Results Export
        
**Export Information:**
- **Timestamp:** {export_info.get('timestamp', 'N/A')}
- **Session ID:** {export_info.get('session_id', 'N/A')}
- **Export Version:** {export_info.get('export_version', 'N/A')}

## Feasibility Assessment
"""
        
        feasibility = recommendations.get('feasibility', {})
        markdown += f"""
- **Score:** {feasibility.get('score', 0)}%
- **Status:** {feasibility.get('status', 'Unknown')}
- **Assessment:** {feasibility.get('assessment', 'No assessment available')}

### Key Insights
"""
        
        insights = feasibility.get('insights', [])
        for insight in insights:
            markdown += f"- {insight}\n"
        
        markdown += "\n### Challenges\n"
        challenges = feasibility.get('challenges', [])
        for challenge in challenges:
            markdown += f"- ⚠️ {challenge}\n"
        
        markdown += "\n## Technology Stack\n"
        tech_stack = recommendations.get('tech_stack', {})
        technologies = tech_stack.get('technologies', [])
        
        for tech in technologies:
            if isinstance(tech, dict):
                markdown += f"- **{tech.get('name', 'Unknown')}**: {tech.get('description', '')}\n"
            else:
                markdown += f"- {tech}\n"
        
        # Include diagrams if available
        diagrams = export_data.get('diagrams', [])
        if diagrams:
            markdown += "\n## Diagrams\n"
            for i, diagram in enumerate(diagrams, 1):
                markdown += f"\n### {diagram.get('title', f'Diagram {i}')}\n"
                markdown += f"```mermaid\n{diagram.get('code', '')}\n```\n"
        
        return markdown
    
    def _format_as_html(self, export_data: Dict[str, Any]) -> str:
        """Format export data as HTML."""
        recommendations = export_data.get("recommendations", {})
        metadata = export_data.get("metadata", {})
        export_info = export_data.get("export_info", {})
        
        html = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Analysis Results Export</title>
            <style>
                body {{ font-family: Arial, sans-serif; margin: 40px; line-height: 1.6; }}
                .header {{ background: #f8f9fa; padding: 20px; border-radius: 8px; margin-bottom: 30px; }}
                .section {{ margin-bottom: 30px; }}
                .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #e9ecef; border-radius: 5px; }}
                .tech-item {{ margin: 10px 0; padding: 10px; background: #f8f9fa; border-left: 4px solid #007bff; }}
                .challenge {{ color: #dc3545; }}
                .insight {{ color: #28a745; }}
                pre {{ background: #f8f9fa; padding: 15px; border-radius: 5px; overflow-x: auto; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 Analysis Results Export</h1>
                <p><strong>Session ID:</strong> {export_info.get('session_id', 'N/A')}</p>
                <p><strong>Export Date:</strong> {export_info.get('timestamp', 'N/A')}</p>
            </div>
        """
        
        feasibility = recommendations.get('feasibility', {})
        html += f"""
            <div class="section">
                <h2>📊 Feasibility Assessment</h2>
                <div class="metric">
                    <strong>Score:</strong> {feasibility.get('score', 0)}%
                </div>
                <div class="metric">
                    <strong>Status:</strong> {feasibility.get('status', 'Unknown')}
                </div>
                <p><strong>Assessment:</strong> {feasibility.get('assessment', 'No assessment available')}</p>
                
                <h3>Key Insights</h3>
                <ul>
        """
        
        insights = feasibility.get('insights', [])
        for insight in insights:
            html += f"<li class='insight'>{insight}</li>"
        
        html += "</ul><h3>Challenges</h3><ul>"
        
        challenges = feasibility.get('challenges', [])
        for challenge in challenges:
            html += f"<li class='challenge'>⚠️ {challenge}</li>"
        
        html += "</ul></div>"
        
        # Technology stack
        html += "<div class='section'><h2>🔧 Technology Stack</h2>"
        
        tech_stack = recommendations.get('tech_stack', {})
        technologies = tech_stack.get('technologies', [])
        
        for tech in technologies:
            if isinstance(tech, dict):
                html += f"<div class='tech-item'><strong>{tech.get('name', 'Unknown')}</strong><br>{tech.get('description', '')}</div>"
            else:
                html += f"<div class='tech-item'>{tech}</div>"
        
        html += "</div>"
        
        # Include diagrams if available
        diagrams = export_data.get('diagrams', [])
        if diagrams:
            html += "<div class='section'><h2>📊 Diagrams</h2>"
            for i, diagram in enumerate(diagrams, 1):
                html += f"<h3>{diagram.get('title', f'Diagram {i}')}</h3>"
                html += f"<pre><code>{diagram.get('code', '')}</code></pre>"
            html += "</div>"
        
        html += "</body></html>"
        
        return html
    
    def _format_as_csv(self, export_data: Dict[str, Any]) -> str:
        """Format export data as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Category', 'Field', 'Value'])
        
        # Export info
        export_info = export_data.get("export_info", {})
        writer.writerow(['Export Info', 'Timestamp', export_info.get('timestamp', 'N/A')])
        writer.writerow(['Export Info', 'Session ID', export_info.get('session_id', 'N/A')])
        
        # Feasibility data
        recommendations = export_data.get("recommendations", {})
        feasibility = recommendations.get('feasibility', {})
        
        writer.writerow(['Feasibility', 'Score', f"{feasibility.get('score', 0)}%"])
        writer.writerow(['Feasibility', 'Status', feasibility.get('status', 'Unknown')])
        writer.writerow(['Feasibility', 'Assessment', feasibility.get('assessment', 'N/A')])
        
        # Technology stack
        tech_stack = recommendations.get('tech_stack', {})
        technologies = tech_stack.get('technologies', [])
        
        for i, tech in enumerate(technologies, 1):
            if isinstance(tech, dict):
                writer.writerow(['Technology', f'Tech {i} Name', tech.get('name', 'Unknown')])
                writer.writerow(['Technology', f'Tech {i} Description', tech.get('description', '')])
            else:
                writer.writerow(['Technology', f'Tech {i}', tech])
        
        return output.getvalue()
    
    def _compress_content(self, content: str, filename: str) -> bytes:
        """Compress content using gzip."""
        import gzip
        
        return gzip.compress(content.encode('utf-8'))
    
    def _log_export(self, session_id: str, format_type: str, filename: str):
        """Log export activity."""
        try:
            app_logger.info(f"Export completed: session={session_id}, format={format_type}, file={filename}")
        except Exception as e:
            # Don't fail export if logging fails
            pass
    
    def _render_export_history(self):
        """Render export history."""
        st.subheader("📚 Export History")
        
        # This would typically load from a database or file
        # For now, show placeholder
        st.info("Export history will be available in future versions.")
        
        # Placeholder data
        history_data = [
            {"Date": "2025-01-15 10:30", "Format": "JSON", "Size": "2.3 KB", "Status": "✅ Success"},
            {"Date": "2025-01-15 09:15", "Format": "Markdown", "Size": "1.8 KB", "Status": "✅ Success"},
            {"Date": "2025-01-14 16:45", "Format": "HTML", "Size": "4.1 KB", "Status": "✅ Success"}
        ]
        
        if st.checkbox("Show Export History", key="show_export_history"):
            st.table(history_data)