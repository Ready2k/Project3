"""Diagrams tab for the AAA application."""

import streamlit as st
from typing import Dict, Any, Optional

from app.ui.tabs.base import BaseTab
from app.core.registry import ServiceRegistry
from app.ui.main_app import SessionManager


class DiagramsTab(BaseTab):
    """Tab for viewing and managing diagrams."""
    
    def __init__(self, session_manager: SessionManager, service_registry: ServiceRegistry):
        super().__init__("diagrams", "📊 Diagrams", "View and generate architecture diagrams for your analysis")
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    def initialize(self) -> None:
        """Initialize the diagrams tab."""
        pass
    
    def render(self) -> None:
        """Render the diagrams tab."""
        st.header("📊 Architecture Diagrams")
        st.markdown("*View and generate architecture diagrams for your analysis*")
        
        # Check if we have session data
        session_data = self.session_manager.get_session_data()
        session_id = session_data.get('session_id')
        recommendations = session_data.get('recommendations')
        
        if not session_id or not recommendations:
            st.info("🔍 No active analysis session. Please run an analysis first in the Analysis tab.")
            return
        
        # Diagram type selection
        diagram_types = [
            "Context Diagram",
            "Container Diagram", 
            "Sequence Diagram",
            "Tech Stack Wiring Diagram",
            "Agent Interaction Flow"
        ]
        
        selected_diagram = st.selectbox(
            "Select Diagram Type:",
            diagram_types,
            key="diagram_type_select"
        )
        
        col1, col2 = st.columns([3, 1])
        
        with col2:
            if st.button("🎨 Generate Diagram", key="generate_diagram_btn"):
                self._generate_diagram(selected_diagram, session_id, recommendations)
        
        # Display existing diagram if available
        diagram_key = f"diagram_{selected_diagram.lower().replace(' ', '_')}"
        if diagram_key in st.session_state:
            st.subheader(f"{selected_diagram}")
            
            # Render the diagram
            try:
                import streamlit.components.v1 as components
                
                # Create Mermaid HTML
                mermaid_code = st.session_state[diagram_key]
                html_content = f"""
                <div class="mermaid">
                {mermaid_code}
                </div>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{startOnLoad: true}});
                </script>
                """
                
                components.html(html_content, height=600)
                
                # Show code in expander
                with st.expander("📝 View Mermaid Code"):
                    st.code(mermaid_code, language="mermaid")
                
                # Download options
                col1, col2, col3 = st.columns(3)
                with col1:
                    st.download_button(
                        "📥 Download Code",
                        mermaid_code,
                        file_name=f"{selected_diagram.lower().replace(' ', '_')}.mmd",
                        mime="text/plain"
                    )
                
                with col2:
                    if st.button("🌐 Open in Browser", key="open_diagram_browser_btn"):
                        self._open_in_browser(mermaid_code, selected_diagram)
                
                with col3:
                    mermaid_live_url = f"https://mermaid.live/edit#{mermaid_code}"
                    st.markdown(f"[🔗 Edit in Mermaid Live]({mermaid_live_url})")
                
            except Exception as e:
                st.error(f"Error rendering diagram: {str(e)}")
                st.code(st.session_state[diagram_key], language="mermaid")
    
    def _generate_diagram(self, diagram_type: str, session_id: str, recommendations: Dict[str, Any]) -> None:
        """Generate a diagram using the LLM."""
        try:
            with st.spinner(f"Generating {diagram_type}..."):
                # Import the diagram generation service
                from app.services.diagram_service import DiagramService
                
                diagram_service = DiagramService()
                
                # Generate the diagram based on type
                if diagram_type == "Context Diagram":
                    mermaid_code = diagram_service.generate_context_diagram(recommendations)
                elif diagram_type == "Container Diagram":
                    mermaid_code = diagram_service.generate_container_diagram(recommendations)
                elif diagram_type == "Sequence Diagram":
                    mermaid_code = diagram_service.generate_sequence_diagram(recommendations)
                elif diagram_type == "Tech Stack Wiring Diagram":
                    mermaid_code = diagram_service.generate_tech_stack_diagram(recommendations)
                elif diagram_type == "Agent Interaction Flow":
                    mermaid_code = diagram_service.generate_agent_interaction_diagram(recommendations)
                else:
                    raise ValueError(f"Unknown diagram type: {diagram_type}")
                
                # Store in session state
                diagram_key = f"diagram_{diagram_type.lower().replace(' ', '_')}"
                st.session_state[diagram_key] = mermaid_code
                
                st.success(f"✅ {diagram_type} generated successfully!")
                st.rerun()
                
        except Exception as e:
            st.error(f"Failed to generate {diagram_type}: {str(e)}")
    
    def _open_in_browser(self, mermaid_code: str, diagram_title: str) -> None:
        """Open diagram in a new browser window."""
        try:
            import tempfile
            import webbrowser
            
            html_content = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <title>{diagram_title}</title>
                <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            </head>
            <body>
                <h1>{diagram_title}</h1>
                <div class="mermaid">
                {mermaid_code}
                </div>
                <script>
                    mermaid.initialize({{startOnLoad: true}});
                </script>
            </body>
            </html>
            """
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.html', delete=False) as f:
                f.write(html_content)
                webbrowser.open(f'file://{f.name}')
            
            st.success("🌐 Diagram opened in browser!")
            
        except Exception as e:
            st.error(f"Failed to open in browser: {str(e)}")