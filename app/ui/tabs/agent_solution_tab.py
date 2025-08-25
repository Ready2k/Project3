"""Agent solution tab component for agentic AI solutions."""

import asyncio
from typing import Dict, List, Optional, Any

import streamlit as st
import httpx

from app.ui.tabs.base import BaseTab
from app.ui.components.results_display import ResultsDisplayComponent
from app.ui.components.diagram_viewer import DiagramViewerComponent

# Import logger for error handling
from app.utils.logger import app_logger

# API configuration
API_BASE_URL = "http://localhost:8000"


class AgentSolutionTab(BaseTab):
    """Agent solution tab for agentic AI solutions."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
        self.results_display = ResultsDisplayComponent()
        self.diagram_viewer = DiagramViewerComponent()
    
    @property
    def title(self) -> str:
        return "🤖 Agent Solutions"
    
    def can_render(self) -> bool:
        return st.session_state.get('session_id') is not None
    
    def render(self) -> None:
        """Render the agent solution tab content."""
        if not st.session_state.session_id:
            st.info("👈 Please start an analysis in the Analysis tab first.")
            return
        
        st.header("🤖 Agentic AI Solutions")
        st.markdown("Explore autonomous agent recommendations and multi-agent system designs.")
        
        # Load agentic recommendations if not already loaded
        if not hasattr(st.session_state, 'agentic_recommendations'):
            self._load_agentic_recommendations()
        
        if hasattr(st.session_state, 'agentic_recommendations') and st.session_state.agentic_recommendations:
            self._render_agentic_solutions()
        else:
            self._render_no_agentic_solutions()
    
    def _load_agentic_recommendations(self):
        """Load agentic AI recommendations for the current session."""
        try:
            response = asyncio.run(self._make_api_request("GET", f"/agentic/{st.session_state.session_id}"))
            
            st.session_state.agentic_recommendations = response.get('recommendations', [])
            
            if st.session_state.agentic_recommendations:
                st.success(f"✅ Loaded {len(st.session_state.agentic_recommendations)} agentic solutions")
            
        except Exception as e:
            st.error(f"Failed to load agentic recommendations: {str(e)}")
            app_logger.error(f"Agentic recommendations load failed: {str(e)}")
    
    def _render_agentic_solutions(self):
        """Render the agentic AI solutions."""
        recommendations = st.session_state.agentic_recommendations
        
        # Solutions overview
        st.subheader("🎯 Agentic Solutions Overview")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Solutions", len(recommendations))
        
        with col2:
            high_autonomy = sum(1 for r in recommendations if r.get('autonomy_score', 0) >= 90)
            st.metric("High Autonomy (90%+)", high_autonomy)
        
        with col3:
            avg_autonomy = sum(r.get('autonomy_score', 0) for r in recommendations) / len(recommendations) if recommendations else 0
            st.metric("Average Autonomy", f"{avg_autonomy:.1f}%")
        
        st.divider()
        
        # Detailed solutions
        tab1, tab2, tab3, tab4 = st.tabs(["🤖 Single Agents", "👥 Multi-Agent Systems", "🏗️ Architecture", "📊 Diagrams"])
        
        with tab1:
            self._render_single_agent_solutions(recommendations)
        
        with tab2:
            self._render_multi_agent_solutions(recommendations)
        
        with tab3:
            self._render_agent_architecture(recommendations)
        
        with tab4:
            self._render_agent_diagrams()
    
    def _render_no_agentic_solutions(self):
        """Render when no agentic solutions are available."""
        st.info("🤖 No agentic AI solutions available yet.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("🚀 Generate Agentic Solutions", key="generate_agentic_solutions_btn"):
                self._generate_agentic_solutions()
        
        with col2:
            if st.button("🔄 Refresh Solutions", key="refresh_agentic_solutions_btn"):
                self._load_agentic_recommendations()
                st.rerun()
    
    def _render_single_agent_solutions(self, recommendations: List[Dict]):
        """Render single agent solutions."""
        st.subheader("🤖 Single Agent Solutions")
        
        single_agents = [r for r in recommendations if r.get('solution_type') == 'single_agent']
        
        if not single_agents:
            st.info("No single agent solutions available.")
            return
        
        for i, agent in enumerate(single_agents):
            with st.expander(f"Agent {i+1}: {agent.get('name', 'Unnamed Agent')}", expanded=i == 0):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**Description:**")
                    st.write(agent.get('description', 'No description available'))
                    
                    st.write("**Capabilities:**")
                    capabilities = agent.get('capabilities', [])
                    for cap in capabilities:
                        st.write(f"• {cap}")
                
                with col2:
                    st.metric("Autonomy Score", f"{agent.get('autonomy_score', 0)}%")
                    st.metric("Complexity", agent.get('complexity', 'Unknown'))
                    
                    if agent.get('technologies'):
                        st.write("**Key Technologies:**")
                        for tech in agent.get('technologies', [])[:3]:
                            st.code(tech)
    
    def _render_multi_agent_solutions(self, recommendations: List[Dict]):
        """Render multi-agent system solutions."""
        st.subheader("👥 Multi-Agent System Solutions")
        
        multi_agents = [r for r in recommendations if r.get('solution_type') == 'multi_agent']
        
        if not multi_agents:
            st.info("No multi-agent system solutions available.")
            return
        
        for i, system in enumerate(multi_agents):
            with st.expander(f"System {i+1}: {system.get('name', 'Unnamed System')}", expanded=i == 0):
                st.write("**System Description:**")
                st.write(system.get('description', 'No description available'))
                
                # Agent roles
                agents = system.get('agents', [])
                if agents:
                    st.write("**Agent Roles:**")
                    
                    for j, agent in enumerate(agents):
                        st.write(f"**{j+1}. {agent.get('role', 'Unknown Role')}**")
                        st.write(f"   - {agent.get('description', 'No description')}")
                        
                        responsibilities = agent.get('responsibilities', [])
                        if responsibilities:
                            st.write("   - **Responsibilities:**")
                            for resp in responsibilities[:3]:
                                st.write(f"     • {resp}")
                
                # System metrics
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric("Total Agents", len(agents))
                
                with col2:
                    st.metric("System Autonomy", f"{system.get('autonomy_score', 0)}%")
                
                with col3:
                    st.metric("Coordination Type", system.get('coordination_type', 'Unknown'))
    
    def _render_agent_architecture(self, recommendations: List[Dict]):
        """Render agent architecture details."""
        st.subheader("🏗️ Agent Architecture")
        
        if not recommendations:
            st.info("No architecture information available.")
            return
        
        # Architecture patterns
        st.write("**Common Architecture Patterns:**")
        
        patterns = set()
        for rec in recommendations:
            if rec.get('architecture_pattern'):
                patterns.add(rec.get('architecture_pattern'))
        
        for pattern in patterns:
            st.write(f"• {pattern}")
        
        st.divider()
        
        # Technology stack
        st.write("**Recommended Technology Stack:**")
        
        all_technologies = set()
        for rec in recommendations:
            technologies = rec.get('technologies', [])
            all_technologies.update(technologies)
        
        # Group technologies by category
        tech_categories = {
            'AI/ML Frameworks': [],
            'Agent Frameworks': [],
            'Databases': [],
            'Communication': [],
            'Other': []
        }
        
        for tech in all_technologies:
            tech_lower = tech.lower()
            if any(keyword in tech_lower for keyword in ['langchain', 'autogen', 'crewai', 'semantic']):
                tech_categories['Agent Frameworks'].append(tech)
            elif any(keyword in tech_lower for keyword in ['tensorflow', 'pytorch', 'huggingface', 'openai']):
                tech_categories['AI/ML Frameworks'].append(tech)
            elif any(keyword in tech_lower for keyword in ['postgres', 'redis', 'mongodb', 'vector']):
                tech_categories['Databases'].append(tech)
            elif any(keyword in tech_lower for keyword in ['kafka', 'rabbitmq', 'websocket', 'api']):
                tech_categories['Communication'].append(tech)
            else:
                tech_categories['Other'].append(tech)
        
        for category, techs in tech_categories.items():
            if techs:
                st.write(f"**{category}:**")
                for tech in sorted(techs):
                    st.code(tech)
    
    def _render_agent_diagrams(self):
        """Render agent-specific diagrams."""
        st.subheader("📊 Agent System Diagrams")
        
        diagram_types = [
            ("Agent Interaction Flow", "agent_interaction"),
            ("Agent Team Structure", "agent_team"),
            ("Agent Communication", "agent_communication"),
            ("Agent Workflow", "agent_workflow")
        ]
        
        selected_diagram = st.selectbox(
            "Select Agent Diagram Type:",
            diagram_types,
            format_func=lambda x: x[0]
        )
        
        if st.button(f"🎨 Generate {selected_diagram[0]}", key="generate_agent_diagram_btn"):
            self._generate_agent_diagram(selected_diagram[1])
        
        # Display existing diagrams if any
        if hasattr(st.session_state, 'current_agent_diagram') and st.session_state.current_agent_diagram:
            st.divider()
            self.diagram_viewer.render(st.session_state.current_agent_diagram)
    
    def _generate_agentic_solutions(self):
        """Generate agentic AI solutions."""
        try:
            st.session_state.processing = True
            
            with st.spinner("Generating agentic AI solutions..."):
                response = asyncio.run(self._make_api_request(
                    "POST",
                    f"/agentic/{st.session_state.session_id}/generate"
                ))
                
                st.session_state.agentic_recommendations = response.get('recommendations', [])
                
                if st.session_state.agentic_recommendations:
                    st.success(f"✅ Generated {len(st.session_state.agentic_recommendations)} agentic solutions!")
                    st.rerun()
                else:
                    st.warning("No agentic solutions could be generated for this requirement.")
                    
        except Exception as e:
            st.error(f"Failed to generate agentic solutions: {str(e)}")
            app_logger.error(f"Agentic solution generation failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _generate_agent_diagram(self, diagram_type: str):
        """Generate agent-specific diagrams."""
        try:
            st.session_state.processing = True
            
            with st.spinner(f"Generating {diagram_type} diagram..."):
                response = asyncio.run(self._make_api_request(
                    "POST",
                    f"/diagrams/{st.session_state.session_id}/agent/{diagram_type}"
                ))
                
                diagram_code = response.get('diagram_code', '')
                
                if diagram_code:
                    st.session_state.current_agent_diagram = {
                        'type': diagram_type,
                        'code': diagram_code,
                        'title': f"{diagram_type.replace('_', ' ').title()} Diagram"
                    }
                    st.success(f"✅ {diagram_type.replace('_', ' ').title()} diagram generated!")
                    st.rerun()
                else:
                    st.error("Failed to generate diagram - empty response")
                    
        except Exception as e:
            st.error(f"Failed to generate agent diagram: {str(e)}")
            app_logger.error(f"Agent diagram generation failed: {str(e)}")
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