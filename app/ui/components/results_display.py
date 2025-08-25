"""Results display component for results visualization."""

from typing import Dict, List, Optional, Any

import streamlit as st

from app.ui.components.base import BaseComponent

# Import logger for error handling
from app.utils.logger import app_logger


class ResultsDisplayComponent(BaseComponent):
    """Component for displaying analysis results."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
    
    def render(self, **kwargs) -> Any:
        """Render the results display component."""
        recommendations = kwargs.get('recommendations')
        
        if not recommendations:
            st.info("No results to display.")
            return
        
        self.render_overview(recommendations)
    
    def render_overview(self, recommendations: Dict[str, Any]):
        """Render results overview with key metrics."""
        st.subheader("📊 Analysis Overview")
        
        # Extract key metrics
        feasibility = recommendations.get('feasibility', {})
        pattern_matches = recommendations.get('pattern_matches', [])
        tech_stack = recommendations.get('tech_stack', {})
        
        # Metrics row
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            feasibility_score = feasibility.get('score', 0)
            st.metric(
                "Feasibility Score",
                f"{feasibility_score}%",
                delta=None,
                help="Overall automation feasibility score"
            )
        
        with col2:
            pattern_count = len(pattern_matches)
            st.metric(
                "Pattern Matches",
                pattern_count,
                delta=None,
                help="Number of matching solution patterns"
            )
        
        with col3:
            tech_count = len(tech_stack.get('technologies', []))
            st.metric(
                "Technologies",
                tech_count,
                delta=None,
                help="Number of recommended technologies"
            )
        
        with col4:
            confidence = recommendations.get('confidence', 0)
            st.metric(
                "Confidence",
                f"{confidence}%",
                delta=None,
                help="Confidence in the recommendations"
            )
        
        # Feasibility status
        st.divider()
        self._render_feasibility_status(feasibility)
    
    def render_summary(self, recommendations: Dict[str, Any]):
        """Render detailed summary of results."""
        st.subheader("📋 Analysis Summary")
        
        # Feasibility assessment
        feasibility = recommendations.get('feasibility', {})
        
        st.write("**Feasibility Assessment:**")
        st.write(feasibility.get('assessment', 'No assessment available'))
        
        # Key insights
        insights = feasibility.get('insights', [])
        if insights:
            st.write("**Key Insights:**")
            for insight in insights:
                st.write(f"• {insight}")
        
        # Challenges and considerations
        challenges = feasibility.get('challenges', [])
        if challenges:
            st.write("**Challenges & Considerations:**")
            for challenge in challenges:
                st.write(f"⚠️ {challenge}")
        
        # Recommended approach
        approach = feasibility.get('recommended_approach', '')
        if approach:
            st.write("**Recommended Approach:**")
            st.write(approach)
        
        # Next steps
        next_steps = feasibility.get('next_steps', [])
        if next_steps:
            st.write("**Next Steps:**")
            for i, step in enumerate(next_steps, 1):
                st.write(f"{i}. {step}")
    
    def render_architecture(self, recommendations: Dict[str, Any]):
        """Render architecture and technical details."""
        st.subheader("🏗️ Technical Architecture")
        
        # Technology stack
        tech_stack = recommendations.get('tech_stack', {})
        self._render_tech_stack(tech_stack)
        
        st.divider()
        
        # Pattern matches
        pattern_matches = recommendations.get('pattern_matches', [])
        self._render_pattern_matches(pattern_matches)
        
        st.divider()
        
        # Architecture explanation
        architecture = recommendations.get('architecture', {})
        self._render_architecture_explanation(architecture)
    
    def _render_feasibility_status(self, feasibility: Dict[str, Any]):
        """Render feasibility status with color coding."""
        status = feasibility.get('status', 'Unknown')
        score = feasibility.get('score', 0)
        
        # Color coding based on feasibility
        if score >= 80:
            status_color = "🟢"
            status_text = "Highly Automatable"
        elif score >= 60:
            status_color = "🟡"
            status_text = "Moderately Automatable"
        elif score >= 40:
            status_color = "🟠"
            status_text = "Partially Automatable"
        else:
            status_color = "🔴"
            status_text = "Limited Automation Potential"
        
        st.markdown(f"### {status_color} {status_text}")
        
        # Progress bar for feasibility score
        progress = score / 100.0
        st.progress(progress)
        
        # Status description
        description = feasibility.get('description', '')
        if description:
            st.write(description)
    
    def _render_tech_stack(self, tech_stack: Dict[str, Any]):
        """Render technology stack recommendations."""
        st.write("**🔧 Recommended Technology Stack**")
        
        technologies = tech_stack.get('technologies', [])
        categories = tech_stack.get('categories', {})
        
        if categories:
            # Group technologies by category
            for category, techs in categories.items():
                if techs:
                    with st.expander(f"{category} ({len(techs)} technologies)"):
                        for tech in techs:
                            if isinstance(tech, dict):
                                st.write(f"**{tech.get('name', 'Unknown')}**")
                                if tech.get('description'):
                                    st.write(f"   {tech['description']}")
                            else:
                                st.write(f"• {tech}")
        else:
            # Simple list of technologies
            for tech in technologies:
                if isinstance(tech, dict):
                    st.write(f"• **{tech.get('name', 'Unknown')}** - {tech.get('description', '')}")
                else:
                    st.write(f"• {tech}")
    
    def _render_pattern_matches(self, pattern_matches: List[Dict]):
        """Render matching solution patterns."""
        st.write("**📚 Matching Solution Patterns**")
        
        if not pattern_matches:
            st.info("No matching patterns found.")
            return
        
        for i, pattern in enumerate(pattern_matches):
            with st.expander(f"Pattern {i+1}: {pattern.get('name', 'Unnamed Pattern')}", expanded=i == 0):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**Description:**")
                    st.write(pattern.get('description', 'No description available'))
                    
                    # Pattern tags
                    tags = pattern.get('tags', [])
                    if tags:
                        st.write("**Tags:**")
                        tag_str = " • ".join([f"`{tag}`" for tag in tags])
                        st.markdown(tag_str)
                
                with col2:
                    # Pattern metrics
                    similarity = pattern.get('similarity_score', 0)
                    st.metric("Similarity", f"{similarity:.1%}")
                    
                    feasibility = pattern.get('feasibility', 'Unknown')
                    st.write(f"**Feasibility:** {feasibility}")
                    
                    pattern_id = pattern.get('pattern_id', 'Unknown')
                    st.write(f"**Pattern ID:** {pattern_id}")
    
    def _render_architecture_explanation(self, architecture: Dict[str, Any]):
        """Render architecture explanation."""
        st.write("**🏗️ Architecture Explanation**")
        
        explanation = architecture.get('explanation', '')
        if explanation:
            st.write(explanation)
        else:
            st.info("No architecture explanation available.")
        
        # Components
        components = architecture.get('components', [])
        if components:
            st.write("**System Components:**")
            for component in components:
                if isinstance(component, dict):
                    st.write(f"• **{component.get('name', 'Unknown')}** - {component.get('description', '')}")
                else:
                    st.write(f"• {component}")
        
        # Data flow
        data_flow = architecture.get('data_flow', '')
        if data_flow:
            st.write("**Data Flow:**")
            st.write(data_flow)
        
        # Integration points
        integrations = architecture.get('integrations', [])
        if integrations:
            st.write("**Integration Points:**")
            for integration in integrations:
                st.write(f"• {integration}")
    
    def render_comparison(self, recommendations_list: List[Dict[str, Any]]):
        """Render comparison between multiple recommendations."""
        if len(recommendations_list) < 2:
            st.info("Need at least 2 recommendations for comparison.")
            return
        
        st.subheader("⚖️ Recommendations Comparison")
        
        # Create comparison table
        comparison_data = []
        
        for i, rec in enumerate(recommendations_list):
            feasibility = rec.get('feasibility', {})
            tech_count = len(rec.get('tech_stack', {}).get('technologies', []))
            pattern_count = len(rec.get('pattern_matches', []))
            
            comparison_data.append({
                'Option': f'Option {i+1}',
                'Feasibility Score': f"{feasibility.get('score', 0)}%",
                'Status': feasibility.get('status', 'Unknown'),
                'Technologies': tech_count,
                'Patterns': pattern_count,
                'Confidence': f"{rec.get('confidence', 0)}%"
            })
        
        st.table(comparison_data)
        
        # Detailed comparison
        for i, rec in enumerate(recommendations_list):
            with st.expander(f"Option {i+1} Details"):
                self.render_summary(rec)
    
    def render_export_preview(self, recommendations: Dict[str, Any], format_type: str):
        """Render preview of export data."""
        st.subheader(f"📤 {format_type.upper()} Export Preview")
        
        if format_type == "json":
            import json
            preview_data = json.dumps(recommendations, indent=2)
            st.code(preview_data, language="json")
        
        elif format_type == "markdown":
            preview_data = self._format_as_markdown(recommendations)
            st.markdown(preview_data)
        
        elif format_type == "html":
            preview_data = self._format_as_html(recommendations)
            st.components.v1.html(preview_data, height=400, scrolling=True)
    
    def _format_as_markdown(self, recommendations: Dict[str, Any]) -> str:
        """Format recommendations as Markdown."""
        feasibility = recommendations.get('feasibility', {})
        
        markdown = f"""# Analysis Results
        
## Feasibility Assessment
- **Score:** {feasibility.get('score', 0)}%
- **Status:** {feasibility.get('status', 'Unknown')}
- **Assessment:** {feasibility.get('assessment', 'No assessment available')}

## Technology Stack
"""
        
        tech_stack = recommendations.get('tech_stack', {})
        technologies = tech_stack.get('technologies', [])
        
        for tech in technologies:
            if isinstance(tech, dict):
                markdown += f"- **{tech.get('name', 'Unknown')}**: {tech.get('description', '')}\n"
            else:
                markdown += f"- {tech}\n"
        
        return markdown
    
    def _format_as_html(self, recommendations: Dict[str, Any]) -> str:
        """Format recommendations as HTML."""
        feasibility = recommendations.get('feasibility', {})
        
        html = f"""
        <div style="font-family: Arial, sans-serif; padding: 20px;">
            <h1>Analysis Results</h1>
            
            <h2>Feasibility Assessment</h2>
            <p><strong>Score:</strong> {feasibility.get('score', 0)}%</p>
            <p><strong>Status:</strong> {feasibility.get('status', 'Unknown')}</p>
            <p><strong>Assessment:</strong> {feasibility.get('assessment', 'No assessment available')}</p>
            
            <h2>Technology Stack</h2>
            <ul>
        """
        
        tech_stack = recommendations.get('tech_stack', {})
        technologies = tech_stack.get('technologies', [])
        
        for tech in technologies:
            if isinstance(tech, dict):
                html += f"<li><strong>{tech.get('name', 'Unknown')}</strong>: {tech.get('description', '')}</li>"
            else:
                html += f"<li>{tech}</li>"
        
        html += """
            </ul>
        </div>
        """
        
        return html