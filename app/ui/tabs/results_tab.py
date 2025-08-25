"""Results tab component for analysis results display."""

import asyncio
from typing import Dict, List, Optional, Any

import streamlit as st
import httpx

from app.ui.tabs.base import BaseTab
from app.ui.components.results_display import ResultsDisplayComponent
from app.ui.components.diagram_viewer import DiagramViewerComponent
from app.ui.components.export_controls import ExportControlsComponent

# Import logger for error handling
from app.utils.logger import app_logger

# API configuration
API_BASE_URL = "http://localhost:8000"


class ResultsTab(BaseTab):
    """Results tab for analysis results display."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__(
            tab_id="results",
            title="📊 Results",
            description="View analysis results and recommendations"
        )
        self.session_manager = session_manager
        self.service_registry = service_registry
        self.results_display = None
        self.diagram_viewer = None
        self.export_controls = None
    
    def initialize(self) -> None:
        """Initialize the results tab resources."""
        if not self._initialized:
            self.results_display = ResultsDisplayComponent()
            self.diagram_viewer = DiagramViewerComponent()
            self.export_controls = ExportControlsComponent()
            self._initialized = True
    

    
    def can_render(self) -> bool:
        return st.session_state.get('session_id') is not None
    
    def render(self) -> None:
        """Render the results tab content."""
        # Ensure tab is initialized
        self.ensure_initialized()
        
        if not st.session_state.get('session_id'):
            st.info("👈 Please start an analysis in the Analysis tab first.")
            return
        
        st.header("📊 Analysis Results")
        
        # Load results if not already loaded
        if not st.session_state.recommendations:
            self._load_results()
        
        if st.session_state.recommendations:
            self._render_results()
        else:
            self._render_no_results()
    
    def _load_results(self):
        """Load analysis results for the current session."""
        try:
            response = asyncio.run(self._make_api_request("GET", f"/status/{st.session_state.session_id}"))
            
            st.session_state.recommendations = response.get('recommendations')
            st.session_state.current_phase = response.get('phase', st.session_state.current_phase)
            st.session_state.progress = response.get('progress', st.session_state.progress)
            
            if st.session_state.recommendations:
                st.success("✅ Results loaded successfully")
            
        except Exception as e:
            st.error(f"Failed to load results: {str(e)}")
            app_logger.error(f"Results load failed: {str(e)}")
    
    def _render_results(self):
        """Render the analysis results."""
        recommendations = st.session_state.recommendations
        
        # Results overview
        self.results_display.render_overview(recommendations)
        
        st.divider()
        
        # Detailed results sections
        tab1, tab2, tab3, tab4 = st.tabs(["📋 Summary", "🏗️ Architecture", "📊 Diagrams", "📤 Export"])
        
        with tab1:
            self.results_display.render_summary(recommendations)
        
        with tab2:
            self.results_display.render_architecture(recommendations)
        
        with tab3:
            self._render_diagrams()
        
        with tab4:
            self.export_controls.render(st.session_state.session_id, recommendations)
    
    def _render_no_results(self):
        """Render when no results are available."""
        st.info("🔄 Analysis in progress or no results available yet.")
        
        # Show current phase and progress
        if st.session_state.current_phase:
            st.write(f"**Current Phase:** {st.session_state.current_phase}")
            
            if st.session_state.progress > 0:
                progress = st.session_state.progress / 100.0
                st.progress(progress)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🔄 Refresh Results", key="refresh_results_btn"):
                self._load_results()
                st.rerun()
        
        with col2:
            if st.button("⚡ Force Complete Analysis", key="force_complete_btn"):
                self._force_complete_analysis()
    
    def _render_diagrams(self):
        """Render diagrams section."""
        st.subheader("📊 Architecture Diagrams")
        
        if not st.session_state.session_id:
            st.info("No session available for diagram generation.")
            return
        
        # Diagram type selection
        diagram_types = [
            ("Context Diagram", "context"),
            ("Container Diagram", "container"),
            ("Sequence Diagram", "sequence"),
            ("Tech Stack Wiring", "tech_stack")
        ]
        
        selected_diagram = st.selectbox(
            "Select Diagram Type:",
            diagram_types,
            format_func=lambda x: x[0]
        )
        
        if st.button(f"🎨 Generate {selected_diagram[0]}", key="generate_results_diagram_btn"):
            self._generate_diagram(selected_diagram[1])
        
        # Display existing diagrams if any
        if hasattr(st.session_state, 'current_diagram') and st.session_state.current_diagram:
            st.divider()
            self.diagram_viewer.render(st.session_state.current_diagram)
    
    def _generate_diagram(self, diagram_type: str):
        """Generate a specific type of diagram."""
        try:
            st.session_state.processing = True
            
            with st.spinner(f"Generating {diagram_type} diagram..."):
                response = asyncio.run(self._make_api_request(
                    "POST",
                    f"/diagrams/{st.session_state.session_id}/{diagram_type}"
                ))
                
                diagram_code = response.get('diagram_code', '')
                
                if diagram_code:
                    st.session_state.current_diagram = {
                        'type': diagram_type,
                        'code': diagram_code,
                        'title': f"{diagram_type.replace('_', ' ').title()} Diagram"
                    }
                    st.success(f"✅ {diagram_type.replace('_', ' ').title()} diagram generated!")
                    st.rerun()
                else:
                    st.error("Failed to generate diagram - empty response")
                    
        except Exception as e:
            st.error(f"Failed to generate diagram: {str(e)}")
            app_logger.error(f"Diagram generation failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _force_complete_analysis(self):
        """Force complete the analysis."""
        try:
            st.session_state.processing = True
            
            response = asyncio.run(self._make_api_request(
                "POST",
                f"/analyze/{st.session_state.session_id}/complete"
            ))
            
            st.session_state.recommendations = response.get('recommendations')
            st.session_state.current_phase = response.get('phase', 'Analysis Completed')
            st.session_state.progress = 100
            
            st.success("✅ Analysis completed!")
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to complete analysis: {str(e)}")
            app_logger.error(f"Force complete analysis failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    async def _make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: float = 30.0) -> Dict:
        """Make async API request to FastAPI backend."""
        url = f"{API_BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            elif method.upper() == "PUT":
                response = await client.put(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 404:
                raise ValueError("Session not found")
            elif response.status_code != 200:
                raise ValueError(f"API error: {response.status_code} - {response.text}")
            
            return response.json()