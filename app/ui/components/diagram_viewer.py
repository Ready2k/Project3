"""Diagram viewer component for Mermaid diagram rendering."""

import uuid
from typing import Dict, List, Optional, Any

import streamlit as st

from app.ui.components.base import BaseComponent

# Import logger for error handling
from app.utils.logger import app_logger


class DiagramViewerComponent(BaseComponent):
    """Component for viewing and interacting with Mermaid diagrams."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    def render(self, diagram_data: Dict[str, Any], **kwargs) -> Any:
        """Render the diagram viewer component."""
        if not diagram_data:
            st.info("No diagram data to display.")
            return
        
        diagram_code = diagram_data.get('code', '')
        diagram_title = diagram_data.get('title', 'Diagram')
        diagram_type = diagram_data.get('type', 'unknown')
        
        if not diagram_code:
            st.warning("No diagram code available.")
            return
        
        st.subheader(f"📊 {diagram_title}")
        
        # Render diagram with controls
        self._render_diagram_with_controls(diagram_code, diagram_type, diagram_title)
    
    def _render_diagram_with_controls(self, diagram_code: str, diagram_type: str, title: str):
        """Render diagram with interactive controls."""
        # Control buttons
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            if st.button("🔍 View Full Size", key=f"fullsize_{diagram_type}"):
                self._open_fullsize_diagram(diagram_code, title)
        
        with col2:
            if st.button("📝 Edit in Mermaid Live", key=f"edit_{diagram_type}"):
                self._open_mermaid_live(diagram_code)
        
        with col3:
            if st.button("💾 Download SVG", key=f"download_{diagram_type}"):
                self._download_diagram(diagram_code, title, "svg")
        
        with col4:
            if st.button("📋 Copy Code", key=f"copy_{diagram_type}"):
                self._copy_diagram_code(diagram_code)
        
        # Render the diagram
        try:
            # Try to use streamlit-mermaid if available
            try:
                from streamlit_mermaid import st_mermaid
                
                # Clean and validate diagram code
                cleaned_code = self._clean_mermaid_code(diagram_code)
                
                if self._validate_mermaid_syntax(cleaned_code):
                    st_mermaid(cleaned_code, height="400px")
                else:
                    self._render_fallback_diagram(cleaned_code, title)
                    
            except ImportError:
                # Fallback to HTML rendering
                self._render_html_diagram(diagram_code, title)
                
        except Exception as e:
            st.error(f"Failed to render diagram: {str(e)}")
            self._render_code_fallback(diagram_code)
    
    def _clean_mermaid_code(self, code: str) -> str:
        """Clean and prepare Mermaid code for rendering."""
        if not code:
            return ""
        
        # Remove markdown code blocks if present
        cleaned = code.strip()
        if cleaned.startswith('```mermaid'):
            cleaned = cleaned.replace('```mermaid', '').replace('```', '').strip()
        elif cleaned.startswith('```'):
            cleaned = cleaned.replace('```', '').strip()
        
        # Remove problematic characters
        cleaned = self._sanitize_mermaid_code(cleaned)
        
        return cleaned
    
    def _sanitize_mermaid_code(self, code: str) -> str:
        """Sanitize Mermaid code for safe rendering."""
        # Remove or replace problematic Unicode characters
        import re
        
        # Replace common problematic characters
        replacements = {
            '👤': 'User',
            '🤖': 'Agent',
            '💾': 'Database',
            '🌐': 'Web',
            '📱': 'Mobile',
            '🔒': 'Security',
            '⚡': 'Fast',
            '🔄': 'Process'
        }
        
        for emoji, replacement in replacements.items():
            code = code.replace(emoji, replacement)
        
        # Remove other non-ASCII characters that might cause issues
        code = re.sub(r'[^\x00-\x7F]+', '', code)
        
        return code
    
    def _validate_mermaid_syntax(self, code: str) -> bool:
        """Validate basic Mermaid syntax."""
        if not code:
            return False
        
        # Check for basic Mermaid diagram types
        diagram_types = [
            'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
            'stateDiagram', 'erDiagram', 'journey', 'gantt',
            'pie', 'gitgraph', 'C4Context', 'C4Container', 'C4Component'
        ]
        
        first_line = code.split('\n')[0].strip().lower()
        
        # Check if it starts with a known diagram type
        for diagram_type in diagram_types:
            if first_line.startswith(diagram_type.lower()):
                return True
        
        return False
    
    def _render_fallback_diagram(self, code: str, title: str):
        """Render fallback diagram when main rendering fails."""
        st.warning("⚠️ Diagram rendering encountered issues. Showing alternative view.")
        
        # Create a simple HTML fallback
        fallback_html = f"""
        <div style="border: 2px dashed #ccc; padding: 20px; text-align: center; margin: 10px 0;">
            <h3>{title}</h3>
            <p>Diagram could not be rendered. Please use the "Edit in Mermaid Live" button to view the diagram.</p>
            <p><strong>Diagram Type:</strong> {code.split()[0] if code else 'Unknown'}</p>
        </div>
        """
        
        st.components.v1.html(fallback_html, height=150)
        
        # Show code in expandable section
        with st.expander("View Diagram Code"):
            st.code(code, language="mermaid")
    
    def _render_html_diagram(self, code: str, title: str):
        """Render diagram using HTML and Mermaid.js."""
        cleaned_code = self._clean_mermaid_code(code)
        diagram_id = f"mermaid_{uuid.uuid4().hex[:8]}"
        
        html_content = f"""
        <div id="{diagram_id}" style="text-align: center; margin: 20px 0;">
            <h4>{title}</h4>
            <div class="mermaid">
                {cleaned_code}
            </div>
        </div>
        
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose'
            }});
        </script>
        """
        
        st.components.v1.html(html_content, height=500)
    
    def _render_code_fallback(self, code: str):
        """Render code as fallback when all else fails."""
        st.warning("Unable to render diagram. Showing code instead:")
        st.code(code, language="mermaid")
    
    def _open_fullsize_diagram(self, code: str, title: str):
        """Open diagram in full-size view."""
        cleaned_code = self._clean_mermaid_code(code)
        diagram_id = f"diagram_{uuid.uuid4().hex[:8]}"
        
        # Create standalone HTML file
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>{title}</title>
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <style>
                body {{ 
                    font-family: Arial, sans-serif; 
                    margin: 20px; 
                    background-color: #f5f5f5; 
                }}
                .container {{ 
                    background: white; 
                    padding: 20px; 
                    border-radius: 8px; 
                    box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                }}
                .mermaid {{ 
                    text-align: center; 
                    margin: 20px 0; 
                }}
                .controls {{ 
                    text-align: center; 
                    margin: 20px 0; 
                }}
                button {{ 
                    margin: 5px; 
                    padding: 10px 20px; 
                    background: #007bff; 
                    color: white; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer; 
                }}
                button:hover {{ 
                    background: #0056b3; 
                }}
            </style>
        </head>
        <body>
            <div class="container">
                <h1>{title}</h1>
                <div class="controls">
                    <button onclick="window.print()">🖨️ Print</button>
                    <button onclick="downloadSVG()">💾 Download SVG</button>
                    <button onclick="copyCode()">📋 Copy Code</button>
                </div>
                <div class="mermaid" id="{diagram_id}">
                    {cleaned_code}
                </div>
            </div>
            
            <script>
                mermaid.initialize({{
                    startOnLoad: true,
                    theme: 'default',
                    securityLevel: 'loose'
                }});
                
                function downloadSVG() {{
                    const svg = document.querySelector('#{diagram_id} svg');
                    if (svg) {{
                        const svgData = new XMLSerializer().serializeToString(svg);
                        const svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                        const svgUrl = URL.createObjectURL(svgBlob);
                        const downloadLink = document.createElement('a');
                        downloadLink.href = svgUrl;
                        downloadLink.download = '{title.replace(" ", "_")}.svg';
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        document.body.removeChild(downloadLink);
                    }}
                }}
                
                function copyCode() {{
                    const code = `{cleaned_code}`;
                    navigator.clipboard.writeText(code).then(() => {{
                        alert('Diagram code copied to clipboard!');
                    }});
                }}
            </script>
        </body>
        </html>
        """
        
        # Save to exports directory
        import os
        from pathlib import Path
        
        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)
        
        filename = f"{diagram_id}.html"
        filepath = exports_dir / filename
        
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        st.success(f"✅ Full-size diagram saved as `{filename}`")
        
        # Provide download link
        with open(filepath, 'r', encoding='utf-8') as f:
            st.download_button(
                label="📥 Download HTML File",
                data=f.read(),
                file_name=filename,
                mime="text/html"
            )
    
    def _open_mermaid_live(self, code: str):
        """Open diagram in Mermaid Live Editor."""
        import base64
        import urllib.parse
        
        cleaned_code = self._clean_mermaid_code(code)
        
        # Encode the diagram for Mermaid Live
        encoded_code = base64.b64encode(cleaned_code.encode('utf-8')).decode('utf-8')
        mermaid_live_url = f"https://mermaid.live/edit#{encoded_code}"
        
        st.markdown(f"[🔗 Open in Mermaid Live Editor]({mermaid_live_url})")
        st.info("Click the link above to edit this diagram in Mermaid Live Editor.")
    
    def _download_diagram(self, code: str, title: str, format_type: str):
        """Download diagram in specified format."""
        cleaned_code = self._clean_mermaid_code(code)
        
        if format_type == "svg":
            # For now, provide the code for manual conversion
            st.download_button(
                label="📥 Download Mermaid Code",
                data=cleaned_code,
                file_name=f"{title.replace(' ', '_')}.mmd",
                mime="text/plain"
            )
            st.info("💡 Use Mermaid CLI or online tools to convert to SVG: `mmdc -i diagram.mmd -o diagram.svg`")
    
    def _copy_diagram_code(self, code: str):
        """Copy diagram code to clipboard."""
        cleaned_code = self._clean_mermaid_code(code)
        
        copy_js = f"""
        <script>
        navigator.clipboard.writeText(`{cleaned_code}`).then(function() {{
            console.log('Diagram code copied to clipboard');
        }}).catch(function(err) {{
            console.error('Failed to copy diagram code: ', err);
        }});
        </script>
        """
        
        st.components.v1.html(copy_js, height=0)
        st.success("✅ Diagram code copied to clipboard!")
    
    def render_diagram_gallery(self, diagrams: List[Dict[str, Any]]):
        """Render a gallery of multiple diagrams."""
        if not diagrams:
            st.info("No diagrams to display.")
            return
        
        st.subheader("📊 Diagram Gallery")
        
        # Create tabs for different diagrams
        if len(diagrams) > 1:
            tab_names = [d.get('title', f'Diagram {i+1}') for i, d in enumerate(diagrams)]
            tabs = st.tabs(tab_names)
            
            for tab, diagram in zip(tabs, diagrams):
                with tab:
                    self.render(diagram)
        else:
            # Single diagram
            self.render(diagrams[0])
    
    def render_diagram_comparison(self, diagrams: List[Dict[str, Any]]):
        """Render side-by-side comparison of diagrams."""
        if len(diagrams) < 2:
            st.info("Need at least 2 diagrams for comparison.")
            return
        
        st.subheader("⚖️ Diagram Comparison")
        
        # Create columns for comparison
        cols = st.columns(len(diagrams))
        
        for col, diagram in zip(cols, diagrams):
            with col:
                self.render(diagram)