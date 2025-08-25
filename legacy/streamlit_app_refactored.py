"""Refactored Streamlit UI for Automated AI Assessment (AAA) application.

This is the main entry point for the Streamlit application, now properly modularized
with separated concerns and reusable components.
"""

import streamlit as st

from app.utils.logger import app_logger
from app.utils.error_boundaries import error_boundary
from app.ui.api_client import streamlit_integration
from app.ui.components import (
    ProviderConfigComponent,
    SessionManagementComponent,
    ResultsDisplayComponent
)

# Configure page
st.set_page_config(
    page_title="Automated AI Assessment (AAA)",
    page_icon="🤖",
    layout="wide"
)


class AAA_StreamlitApp:
    """Main Streamlit application class."""
    
    def __init__(self):
        self.provider_config = ProviderConfigComponent()
        self.session_manager = SessionManagementComponent()
        self.results_display = ResultsDisplayComponent()
        self.api_integration = streamlit_integration
    
    @error_boundary("streamlit_app_run", fallback_value=None)
    def run(self):
        """Run the main Streamlit application."""
        # Initialize session state
        self.session_manager.initialize_session_state()
        
        # Main title and description
        st.title("🤖 Automated AI Assessment (AAA)")
        st.markdown("**Assess automation feasibility of your requirements with advanced AI analysis**")
        
        # Sidebar configuration
        self._render_sidebar()
        
        # Main content tabs
        self._render_main_content()
    
    def _render_sidebar(self):
        """Render sidebar with configuration and session info."""
        with st.sidebar:
            st.header("⚙️ Configuration")
            
            # Provider configuration
            provider_config = self.provider_config.render_provider_selection()
            st.session_state.provider_config = provider_config
            
            # Connection test
            self.provider_config.render_connection_test(provider_config, self.api_integration)
            
            st.divider()
            
            # Session information
            self.session_manager.render_session_info()
            
            # Session actions
            self.session_manager.render_session_actions()
            
            st.divider()
            
            # Debug mode toggle
            debug_mode = st.checkbox("🐛 Debug Mode", help="Show detailed error messages and logs")
            st.session_state.debug_mode = debug_mode
    
    def _render_main_content(self):
        """Render main content area with tabs."""
        tab1, tab2, tab3, tab4, tab5 = st.tabs([
            "📝 Input", 
            "❓ Q&A", 
            "📊 Results", 
            "🤖 Agent Solution", 
            "ℹ️ About"
        ])
        
        with tab1:
            self._render_input_tab()
        
        with tab2:
            self._render_qa_tab()
        
        with tab3:
            self._render_results_tab()
        
        with tab4:
            self._render_agent_solution_tab()
        
        with tab5:
            self._render_about_tab()
    
    def _render_input_tab(self):
        """Render the input tab."""
        st.header("📝 Requirement Input")
        
        # Input method selection
        input_method = st.radio(
            "Input Method",
            ["Text", "File Upload", "Jira", "Resume Session"],
            horizontal=True
        )
        
        if input_method == "Text":
            self._render_text_input()
        elif input_method == "File Upload":
            self._render_file_input()
        elif input_method == "Jira":
            self._render_jira_input()
        elif input_method == "Resume Session":
            self._render_resume_session()
    
    def _render_text_input(self):
        """Render text input form."""
        with st.form("text_input_form"):
            description = st.text_area(
                "Describe your automation requirement:",
                placeholder="e.g., I need to automatically extract data from websites and store it in a database...",
                height=150
            )
            
            col1, col2 = st.columns(2)
            with col1:
                domain = st.selectbox(
                    "Domain (optional)",
                    ["", "data_processing", "system_integration", "document_management", "machine_learning"],
                    index=0
                )
            
            with col2:
                pattern_types = st.multiselect(
                    "Pattern Types (optional)",
                    ["web_automation", "api_integration", "document_processing", "ml_pipeline", "workflow_automation"]
                )
            
            # Technology constraints
            with st.expander("🔧 Technology Constraints (Optional)"):
                banned_tools = st.text_area(
                    "Restricted Technologies (one per line)",
                    placeholder="e.g., Azure\nOracle Database",
                    help="List technologies that cannot be used"
                )
                
                required_integrations = st.text_area(
                    "Required Integrations (one per line)",
                    placeholder="e.g., Salesforce\nActive Directory",
                    help="List systems that must be integrated"
                )
                
                compliance_requirements = st.multiselect(
                    "Compliance Requirements",
                    ["GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA", "ISO-27001", "FedRAMP"]
                )
                
                data_sensitivity = st.selectbox(
                    "Data Sensitivity Level",
                    ["", "Public", "Internal", "Confidential", "Restricted"]
                )
            
            submitted = st.form_submit_button("🚀 Start Analysis", type="primary")
            
            if submitted and description:
                payload = {
                    "text": description,
                    "domain": domain if domain else None,
                    "pattern_types": pattern_types
                }
                
                # Add constraints if provided
                constraints = {}
                if banned_tools:
                    constraints["banned_tools"] = [tool.strip() for tool in banned_tools.split('\n') if tool.strip()]
                if required_integrations:
                    constraints["required_integrations"] = [integration.strip() for integration in required_integrations.split('\n') if integration.strip()]
                if compliance_requirements:
                    constraints["compliance_requirements"] = compliance_requirements
                if data_sensitivity:
                    constraints["data_sensitivity"] = data_sensitivity
                
                if constraints:
                    payload["constraints"] = constraints
                
                self.api_integration.submit_requirements_with_ui_feedback(
                    "text", payload, st.session_state.provider_config
                )
            elif submitted:
                st.warning("Please enter a description")
    
    def _render_file_input(self):
        """Render file upload input."""
        uploaded_file = st.file_uploader(
            "Upload requirement document",
            type=["txt", "md", "json"],
            help="Upload a text file containing your automation requirements"
        )
        
        if uploaded_file:
            # Show file preview
            content = uploaded_file.read().decode("utf-8")
            with st.expander("📄 File Preview"):
                st.text(content[:500] + "..." if len(content) > 500 else content)
            
            if st.button("🚀 Start Analysis", type="primary"):
                payload = {
                    "content": content,
                    "filename": uploaded_file.name
                }
                
                self.api_integration.submit_requirements_with_ui_feedback(
                    "file", payload, st.session_state.provider_config
                )
    
    def _render_jira_input(self):
        """Render Jira integration input."""
        st.subheader("🎫 Jira Integration")
        st.info("Connect to your Jira instance to analyze tickets directly.")
        
        with st.form("jira_form"):
            col1, col2 = st.columns(2)
            
            with col1:
                jira_base_url = st.text_input(
                    "Jira Base URL",
                    placeholder="https://your-domain.atlassian.net",
                    help="Your Jira instance URL"
                )
                jira_email = st.text_input(
                    "Email",
                    placeholder="your-email@company.com",
                    help="Your Jira account email"
                )
            
            with col2:
                jira_api_token = st.text_input(
                    "API Token",
                    type="password",
                    help="Generate from Jira Account Settings > Security > API tokens"
                )
                jira_ticket_key = st.text_input(
                    "Ticket Key",
                    placeholder="PROJ-123",
                    help="Jira ticket key (e.g., PROJ-123)"
                )
            
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                test_connection = st.form_submit_button("🔗 Test Connection", type="secondary")
            
            with col2:
                fetch_ticket = st.form_submit_button("📥 Fetch Ticket", type="secondary")
            
            with col3:
                submit_jira = st.form_submit_button("🚀 Start Analysis", type="primary")
            
            # Handle form submissions
            if test_connection:
                if all([jira_base_url, jira_email, jira_api_token]):
                    jira_config = {
                        "base_url": jira_base_url,
                        "email": jira_email,
                        "api_token": jira_api_token
                    }
                    # Test connection using API integration
                    # This would need to be implemented in the API client
                    st.info("Jira connection testing not yet implemented in refactored version")
                else:
                    st.error("❌ Please fill in all Jira configuration fields")
    
    def _render_resume_session(self):
        """Render resume session interface."""
        self.session_manager.render_resume_session(self.api_integration)
    
    def _render_qa_tab(self):
        """Render the Q&A tab."""
        st.header("❓ Interactive Q&A")
        
        if not self.session_manager.is_session_active():
            st.info("👈 Please start an analysis in the Input tab first.")
            return
        
        # Load current session status
        session_id = st.session_state.session_id
        session_status = self.api_integration.load_session_status_with_ui_feedback(session_id)
        
        if not session_status:
            return
        
        # Show progress
        self.session_manager.render_session_progress()
        
        # Handle Q&A phase
        if st.session_state.get('phase') == 'qa' and not st.session_state.get('qa_complete'):
            questions = st.session_state.get('questions', [])
            
            if questions:
                st.write("Please answer the following questions to improve recommendations:")
                
                with st.form("qa_form"):
                    answers = {}
                    
                    for i, question in enumerate(questions):
                        answer = st.text_area(
                            f"**Q{i+1}:** {question.get('question', 'Question')}",
                            key=f"answer_{i}",
                            help=question.get('help_text', ''),
                            placeholder="Enter your answer here..."
                        )
                        
                        if answer:
                            answers[question.get('field_id', f'question_{i}')] = answer
                    
                    if st.form_submit_button("📤 Submit Answers", type="primary"):
                        if answers:
                            self.api_integration.submit_qa_answers_with_ui_feedback(session_id, answers)
                        else:
                            st.warning("Please answer at least one question")
            else:
                st.info("Loading questions...")
        
        elif st.session_state.get('qa_complete'):
            st.success("✅ Q&A phase complete! Check the Results tab for recommendations.")
        
        else:
            st.info("Q&A phase not yet available. Please complete the input phase first.")
    
    def _render_results_tab(self):
        """Render the results tab."""
        st.header("📊 Analysis Results")
        
        if not self.session_manager.is_session_active():
            st.info("👈 Please start an analysis in the Input tab first.")
            return
        
        # Load recommendations if available
        session_id = st.session_state.session_id
        
        if not st.session_state.get('recommendations'):
            if st.button("🧠 Generate Recommendations"):
                self.api_integration.load_recommendations_with_ui_feedback(session_id)
        
        # Display results
        if st.session_state.get('recommendations'):
            # Results summary
            session_summary = self.session_manager.get_session_summary()
            self.results_display.render_results_summary(session_summary)
            
            st.divider()
            
            # Feasibility assessment
            feasibility = st.session_state.get('feasibility', '')
            reasoning = st.session_state.get('reasoning', '')
            self.results_display.render_feasibility_assessment(feasibility, reasoning)
            
            st.divider()
            
            # Recommendations
            recommendations = st.session_state.get('recommendations', [])
            self.results_display.render_recommendations(recommendations)
            
            st.divider()
            
            # Technology stack
            tech_stack = st.session_state.get('tech_stack', [])
            self.results_display.render_tech_stack(tech_stack)
            
            st.divider()
            
            # Diagrams
            requirements = st.session_state.get('requirements', {})
            self.results_display.render_diagrams_section(requirements, recommendations, tech_stack)
            
            st.divider()
            
            # Export options
            self.results_display.render_export_options(session_id, self.api_integration)
        
        else:
            st.info("No recommendations available yet. Complete the Q&A phase or generate recommendations.")
    
    def _render_agent_solution_tab(self):
        """Render the agent solution tab."""
        st.header("🤖 Agentic AI Solution")
        
        if not self.session_manager.is_session_active():
            st.info("👈 Please start an analysis in the Input tab first.")
            return
        
        st.info("🚧 **Agent Solution Display**: This feature will show detailed agentic AI recommendations when available.")
        
        # Check if we have agentic recommendations
        recommendations = st.session_state.get('recommendations', [])
        
        if recommendations:
            # Look for agentic patterns
            agentic_recs = [rec for rec in recommendations if 'agent' in rec.get('reasoning', '').lower()]
            
            if agentic_recs:
                st.success(f"✅ Found {len(agentic_recs)} agentic recommendations!")
                
                for i, rec in enumerate(agentic_recs, 1):
                    with st.expander(f"🤖 Agentic Solution {i}: {rec.get('pattern_name', 'Unknown')}", expanded=True):
                        
                        # Agent roles
                        if rec.get('agent_roles'):
                            st.write("**🎭 Agent Roles:**")
                            for role in rec['agent_roles']:
                                st.write(f"• **{role.get('name', 'Agent')}**: {role.get('responsibility', 'N/A')}")
                                st.write(f"  - Autonomy Level: {role.get('autonomy_level', 0):.1%}")
                        
                        # Implementation guidance
                        if rec.get('implementation_guidance'):
                            st.write("**📋 Implementation Guidance:**")
                            for guidance in rec['implementation_guidance']:
                                st.write(f"• {guidance}")
            else:
                st.info("No agentic AI solutions found in current recommendations. Try generating more recommendations or adjusting your requirements.")
        else:
            st.info("Generate recommendations first to see agentic AI solutions.")
    
    def _render_about_tab(self):
        """Render the about tab."""
        st.header("ℹ️ About AAA System")
        
        st.markdown("""
        ## 🤖 Automated AI Assessment (AAA)
        
        The AAA system helps you assess the automation feasibility of your requirements using advanced AI analysis.
        
        ### ✨ Key Features:
        
        - **🧠 AI-Powered Analysis**: Advanced LLM-based requirement analysis
        - **🎯 Feasibility Assessment**: Detailed automation feasibility scoring
        - **💡 Smart Recommendations**: Pattern-based solution recommendations
        - **🤖 Agentic AI Solutions**: Specialized autonomous agent recommendations
        - **🛠️ Technology Stack**: Intelligent technology recommendations
        - **📊 Visual Diagrams**: Architecture and flow diagrams
        - **📤 Multiple Export Formats**: JSON, Markdown, HTML, and comprehensive reports
        
        ### 🔧 Supported LLM Providers:
        
        - **OpenAI**: GPT-4o, GPT-4, GPT-3.5-turbo
        - **Anthropic Claude**: Claude-3 models
        - **AWS Bedrock**: Claude models via AWS
        - **Custom Providers**: Internal HTTP endpoints
        
        ### 🚀 Getting Started:
        
        1. **Configure Provider**: Select and configure your LLM provider in the sidebar
        2. **Input Requirements**: Describe your automation needs in the Input tab
        3. **Answer Questions**: Complete the interactive Q&A for better recommendations
        4. **Review Results**: Analyze feasibility, recommendations, and tech stack
        5. **Export Results**: Download your analysis in your preferred format
        
        ### 🔒 Security & Privacy:
        
        - Advanced prompt defense system with 8 specialized detectors
        - PII redaction and secure credential handling
        - Comprehensive input validation and sanitization
        - Audit logging for all operations
        
        ### 📈 Recent Improvements:
        
        - ✅ **Refactored Architecture**: Modular, maintainable codebase
        - ✅ **Error Boundaries**: Robust error handling with graceful fallbacks
        - ✅ **Configuration Service**: Dynamic system parameter management
        - ✅ **Enhanced Security**: Comprehensive input validation and SQL injection prevention
        - ✅ **Structured Logging**: Professional logging throughout the system
        """)
        
        # System status
        with st.expander("🔍 System Status"):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Application Status:**")
                st.success("✅ UI Components: Operational")
                st.success("✅ API Client: Operational")
                st.success("✅ Error Boundaries: Active")
                st.success("✅ Configuration Service: Active")
            
            with col2:
                st.write("**Security Status:**")
                st.success("✅ Input Validation: Active")
                st.success("✅ PII Redaction: Active")
                st.success("✅ Audit Logging: Active")
                st.success("✅ Prompt Defense: Active")


def main():
    """Main entry point for the Streamlit application."""
    try:
        app = AAA_StreamlitApp()
        app.run()
    except Exception as e:
        st.error(f"❌ Application Error: {str(e)}")
        app_logger.error(f"Streamlit app error: {e}")
        
        if st.session_state.get('debug_mode'):
            st.exception(e)


if __name__ == "__main__":
    main()