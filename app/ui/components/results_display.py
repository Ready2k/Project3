"""Results display UI component."""

from typing import Dict, Any, List, Optional
import streamlit as st

from app.utils.logger import app_logger
from app.ui.mermaid_diagrams import mermaid_generator


class ResultsDisplayComponent:
    """Handles display of analysis results and recommendations."""
    
    def __init__(self):
        self.export_formats = {
            "json": {"name": "JSON", "icon": "📄", "description": "Machine-readable format"},
            "markdown": {"name": "Markdown", "icon": "📝", "description": "Human-readable documentation"},
            "html": {"name": "HTML", "icon": "🌐", "description": "Interactive web format"},
            "comprehensive": {"name": "Comprehensive", "icon": "📊", "description": "Complete analysis report"}
        }
    
    def render_feasibility_assessment(self, feasibility: str, reasoning: str):
        """Render feasibility assessment section."""
        st.subheader("🎯 Feasibility Assessment")
        
        # Determine color based on feasibility
        if "fully automatable" in feasibility.lower():
            st.success(f"✅ **{feasibility}**")
        elif "partially automatable" in feasibility.lower():
            st.warning(f"⚠️ **{feasibility}**")
        else:
            st.error(f"❌ **{feasibility}**")
        
        if reasoning:
            with st.expander("🧠 Reasoning Details"):
                st.write(reasoning)
    
    def render_recommendations(self, recommendations: List[Dict[str, Any]]):
        """Render recommendations section."""
        st.subheader("💡 Recommendations")
        
        if not recommendations:
            st.info("No recommendations available yet.")
            return
        
        for i, rec in enumerate(recommendations, 1):
            with st.expander(f"📋 Recommendation {i}: {rec.get('pattern_name', 'Unknown Pattern')}", expanded=i==1):
                
                # Pattern information
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Pattern ID:** {rec.get('pattern_id', 'N/A')}")
                    st.write(f"**Confidence:** {rec.get('confidence', 0):.1%}")
                
                with col2:
                    st.write(f"**Complexity:** {rec.get('complexity', 'Unknown')}")
                    st.write(f"**Effort:** {rec.get('estimated_effort', 'Unknown')}")
                
                # Description
                if rec.get('description'):
                    st.write("**Description:**")
                    st.write(rec['description'])
                
                # Reasoning
                if rec.get('reasoning'):
                    st.write("**Why this pattern fits:**")
                    st.write(rec['reasoning'])
                
                # Implementation guidance
                if rec.get('implementation_guidance'):
                    st.write("**Implementation Guidance:**")
                    for guidance in rec['implementation_guidance']:
                        st.write(f"• {guidance}")
                
                # Agent roles (if available)
                if rec.get('agent_roles'):
                    self._render_agent_roles(rec['agent_roles'])
    
    def _render_agent_roles(self, agent_roles: List[Dict[str, Any]]):
        """Render agent roles information."""
        st.write("**🤖 Agent Roles:**")
        
        for role in agent_roles:
            with st.container():
                st.write(f"**{role.get('name', 'Unknown Agent')}**")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"*Autonomy Level:* {role.get('autonomy_level', 0):.1%}")
                    st.write(f"*Responsibility:* {role.get('responsibility', 'N/A')}")
                
                with col2:
                    if role.get('capabilities'):
                        st.write("*Capabilities:*")
                        for cap in role['capabilities']:
                            st.write(f"  • {cap}")
                
                st.divider()
    
    def render_tech_stack(self, tech_stack: List[str]):
        """Render technology stack section."""
        st.subheader("🛠️ Technology Stack")
        
        if not tech_stack:
            st.info("No technology recommendations available yet.")
            return
        
        # Group technologies by category (if possible)
        categorized_tech = self._categorize_technologies(tech_stack)
        
        if len(categorized_tech) > 1:
            # Show categorized view
            for category, technologies in categorized_tech.items():
                with st.expander(f"📦 {category}", expanded=True):
                    for tech in technologies:
                        st.write(f"• {tech}")
        else:
            # Show simple list
            for tech in tech_stack:
                st.write(f"• {tech}")
    
    def _categorize_technologies(self, tech_stack: List[str]) -> Dict[str, List[str]]:
        """Categorize technologies by type."""
        categories = {
            "Programming Languages": [],
            "Frameworks & Libraries": [],
            "Databases": [],
            "Cloud Services": [],
            "Tools & Utilities": [],
            "Other": []
        }
        
        # Simple categorization based on common patterns
        for tech in tech_stack:
            tech_lower = tech.lower()
            
            if any(lang in tech_lower for lang in ['python', 'javascript', 'java', 'go', 'rust', 'c++']):
                categories["Programming Languages"].append(tech)
            elif any(fw in tech_lower for fw in ['react', 'vue', 'angular', 'django', 'flask', 'fastapi', 'express']):
                categories["Frameworks & Libraries"].append(tech)
            elif any(db in tech_lower for db in ['postgresql', 'mysql', 'mongodb', 'redis', 'elasticsearch']):
                categories["Databases"].append(tech)
            elif any(cloud in tech_lower for cloud in ['aws', 'azure', 'gcp', 'docker', 'kubernetes']):
                categories["Cloud Services"].append(tech)
            elif any(tool in tech_lower for tool in ['git', 'jenkins', 'terraform', 'ansible']):
                categories["Tools & Utilities"].append(tech)
            else:
                categories["Other"].append(tech)
        
        # Remove empty categories
        return {k: v for k, v in categories.items() if v}
    
    def render_diagrams_section(self, requirements: Dict[str, Any], recommendations: List[Dict[str, Any]], tech_stack: List[str]):
        """Render diagrams section."""
        st.subheader("📊 Architecture Diagrams")
        
        diagram_types = [
            ("Context Diagram", "High-level system context"),
            ("Container Diagram", "System containers and relationships"),
            ("Sequence Diagram", "Process flow and interactions"),
            ("Tech Stack Wiring", "Technology connections and data flow")
        ]
        
        selected_diagram = st.selectbox(
            "Select Diagram Type",
            [dt[0] for dt in diagram_types],
            format_func=lambda x: f"{x} - {dict(diagram_types)[x]}"
        )
        
        if st.button(f"🎨 Generate {selected_diagram}"):
            self._generate_and_display_diagram(selected_diagram, requirements, recommendations, tech_stack)
    
    def _generate_and_display_diagram(self, diagram_type: str, requirements: Dict[str, Any], recommendations: List[Dict[str, Any]], tech_stack: List[str]):
        """Generate and display a specific diagram type."""
        try:
            with st.spinner(f"🎨 Generating {diagram_type}..."):
                
                # Get provider config from session state
                provider_config = st.session_state.get('provider_config', {})
                
                if diagram_type == "Context Diagram":
                    prompt = self._build_context_diagram_prompt(requirements, recommendations, tech_stack)
                elif diagram_type == "Container Diagram":
                    prompt = self._build_container_diagram_prompt(requirements, recommendations, tech_stack)
                elif diagram_type == "Sequence Diagram":
                    prompt = self._build_sequence_diagram_prompt(requirements, recommendations)
                elif diagram_type == "Tech Stack Wiring":
                    prompt = self._build_tech_wiring_prompt(tech_stack, requirements)
                else:
                    st.error(f"Unknown diagram type: {diagram_type}")
                    return
                
                # Generate diagram using async function
                import asyncio
                try:
                    loop = asyncio.get_event_loop()
                    mermaid_code = loop.run_until_complete(
                        mermaid_generator.make_llm_request(prompt, provider_config, f"{diagram_type.lower()}_generation")
                    )
                    
                    if mermaid_code:
                        st.success(f"✅ {diagram_type} generated successfully!")
                        mermaid_generator.render_mermaid_diagram(mermaid_code)
                    else:
                        st.error("Failed to generate diagram - empty response")
                        
                except Exception as e:
                    st.error(f"Failed to generate diagram: {str(e)}")
                    app_logger.error(f"Diagram generation error: {e}")
                    
        except Exception as e:
            st.error(f"Error generating {diagram_type}: {str(e)}")
            app_logger.error(f"Diagram generation error: {e}")
    
    def _build_context_diagram_prompt(self, requirements: Dict[str, Any], recommendations: List[Dict[str, Any]], tech_stack: List[str]) -> str:
        """Build prompt for context diagram generation."""
        requirement_text = requirements.get('description', 'Automation requirement')
        tech_context = ', '.join(tech_stack[:5]) if tech_stack else 'Various technologies'
        
        return f"""Generate a Mermaid context diagram (C4 Level 1) for this automation requirement:

REQUIREMENT: {requirement_text}

TECHNOLOGY CONTEXT: {tech_context}

Create a context diagram showing:
- The user/actor who will use the system
- The main system being automated
- External systems it needs to integrate with
- Data sources it needs to access

Use Mermaid flowchart syntax. Start with "flowchart LR" and use:
- Circles for people: user([User Name])
- Rectangles for systems: system[System Name]
- Cylinders for databases: db[(Database)]

Return ONLY the raw Mermaid code without markdown formatting."""
    
    def _build_container_diagram_prompt(self, requirements: Dict[str, Any], recommendations: List[Dict[str, Any]], tech_stack: List[str]) -> str:
        """Build prompt for container diagram generation."""
        requirement_text = requirements.get('description', 'Automation requirement')
        tech_context = ', '.join(tech_stack[:8]) if tech_stack else 'Various technologies'
        
        return f"""Generate a Mermaid container diagram for this automation requirement:

REQUIREMENT: {requirement_text}

TECHNOLOGIES: {tech_context}

Create a container diagram showing:
- Web applications, APIs, databases, and services
- How containers communicate with each other
- Technology choices for each container

Use Mermaid flowchart syntax with appropriate shapes and connections.
Return ONLY the raw Mermaid code without markdown formatting."""
    
    def _build_sequence_diagram_prompt(self, requirements: Dict[str, Any], recommendations: List[Dict[str, Any]]) -> str:
        """Build prompt for sequence diagram generation."""
        requirement_text = requirements.get('description', 'Automation requirement')
        
        return f"""Generate a Mermaid sequence diagram for this automation process:

REQUIREMENT: {requirement_text}

Create a sequence diagram showing:
- The main actors/participants in the process
- The sequence of interactions and API calls
- Decision points and alternative flows
- Error handling scenarios

Use Mermaid sequenceDiagram syntax.
Return ONLY the raw Mermaid code without markdown formatting."""
    
    def _build_tech_wiring_prompt(self, tech_stack: List[str], requirements: Dict[str, Any]) -> str:
        """Build prompt for technology wiring diagram."""
        tech_context = ', '.join(tech_stack) if tech_stack else 'Various technologies'
        requirement_text = requirements.get('description', 'Automation requirement')
        
        return f"""Generate a Mermaid tech stack wiring diagram showing how these technologies connect:

TECHNOLOGIES: {tech_context}

REQUIREMENT CONTEXT: {requirement_text}

Create a diagram showing:
- Data flow between components with labeled arrows (HTTP, SQL, API calls)
- Component types (services, databases, external APIs) with appropriate symbols
- Authentication flows and security layers
- Message queues and async processing connections

Use Mermaid flowchart syntax with clear labels and connection types.
Return ONLY the raw Mermaid code without markdown formatting."""
    
    def render_export_options(self, session_id: str, api_integration):
        """Render export options section."""
        st.subheader("📤 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            export_format = st.selectbox(
                "Export Format",
                list(self.export_formats.keys()),
                format_func=lambda x: f"{self.export_formats[x]['icon']} {self.export_formats[x]['name']}"
            )
        
        with col2:
            st.write(f"**{self.export_formats[export_format]['description']}**")
        
        if st.button(f"📥 Export as {self.export_formats[export_format]['name']}", type="primary"):
            api_integration.export_results_with_ui_feedback(session_id, export_format)
    
    def render_results_summary(self, session_summary: Dict[str, Any]):
        """Render a summary of current results."""
        st.subheader("📋 Results Summary")
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Session Progress", f"{session_summary.get('progress', 0)}%")
        
        with col2:
            recommendations_count = len(st.session_state.get('recommendations', []))
            st.metric("Recommendations", recommendations_count)
        
        with col3:
            tech_count = len(st.session_state.get('tech_stack', []))
            st.metric("Technologies", tech_count)
        
        # Status indicators
        status_items = [
            ("Requirements", session_summary.get('has_requirements', False)),
            ("Q&A Complete", session_summary.get('qa_complete', False)),
            ("Recommendations", session_summary.get('has_recommendations', False))
        ]
        
        st.write("**Analysis Status:**")
        for item, status in status_items:
            icon = "✅" if status else "⏳"
            st.write(f"{icon} {item}")