"""About tab component for system information."""

import streamlit as st
from pathlib import Path

from app.ui.tabs.base import BaseTab

# Import logger for error handling
from app.utils.logger import app_logger


class AboutTab(BaseTab):
    """About tab for system information."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__(
            tab_id="about",
            title="ℹ️ About",
            description="System information and documentation"
        )
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    def initialize(self) -> None:
        """Initialize the about tab resources."""
        if not self._initialized:
            # No heavy initialization needed for about tab
            self._initialized = True
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render the about tab content."""
        # Ensure tab is initialized
        self.ensure_initialized()
        
        st.header("ℹ️ About Automated AI Assessment (AAA)")
        
        # Main description
        st.markdown("""
        This application helps you assess whether your business requirements can be automated using agentic AI systems.
        
        ### 🚀 Core Features:
        - 📝 **Multiple Input Methods**: Text, file upload, Jira integration, session resume
        - 🤖 **Multi-Provider LLM Support**: OpenAI, Anthropic/Bedrock, Claude Direct, Internal HTTP
        - 🎯 **Intelligent Pattern Matching**: Tag filtering + vector similarity with FAISS
        - ❓ **LLM-Powered Q&A System**: AI-generated clarifying questions with caching
        - 🛠️ **LLM-Driven Tech Stack Generation**: Contextual technology recommendations
        - 🏗️ **AI-Generated Architecture Explanations**: How components work together
        - 📊 **Feasibility Assessment**: Automatable, Fully Automatable, Partially Automatable, or Not Automatable
        - 📈 **AI-Generated Architecture Diagrams**: Context, Container, Sequence, and Tech Stack Wiring diagrams
        - 🤖 **Agentic AI Solutions**: Autonomous agent recommendations and multi-agent system designs
        - 📤 **Multi-Format Export**: JSON, Markdown, and interactive HTML
        - 🎯 **Constraint-Aware**: Filters banned tools and applies business constraints
        - 🔒 **Advanced Security**: Multi-layered prompt defense with 8 specialized detectors
        """)
        
        st.divider()
        
        # System information tabs
        info_tab1, info_tab2, info_tab3, info_tab4 = st.tabs(["🏗️ Architecture", "🔧 Technology Stack", "📊 Analytics", "🔒 Security"])
        
        with info_tab1:
            self._render_architecture_info()
        
        with info_tab2:
            self._render_technology_stack()
        
        with info_tab3:
            self._render_analytics_info()
        
        with info_tab4:
            self._render_security_info()
    
    def _render_architecture_info(self):
        """Render architecture information."""
        st.subheader("🏗️ System Architecture")
        
        st.markdown("""
        ### Component Overview
        
        **Frontend (Streamlit)**
        - Interactive web interface with tabbed navigation
        - Real-time progress tracking and session management
        - Mermaid diagram rendering with browser export
        - Multi-format export capabilities
        
        **Backend (FastAPI)**
        - Async REST API with comprehensive endpoints
        - Multi-provider LLM integration with security validation
        - Pattern matching using FAISS vector similarity
        - Session persistence with diskcache/Redis
        
        **Data Layer**
        - Pattern library with JSON-based reusable solutions
        - Technology catalog with 55+ technologies and rich metadata
        - FAISS vector index for similarity search
        - SQLite audit database for analytics and security events
        
        **Security Layer**
        - Advanced prompt defense with 8 specialized detectors
        - Real-time attack detection and user education
        - Multi-language security validation (6 languages)
        - Performance-optimized with sub-100ms validation
        """)
    
    def _render_technology_stack(self):
        """Render technology stack information."""
        st.subheader("🔧 Technology Stack")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("""
            **Core Technologies**
            - **Python 3.10+**: Primary language
            - **FastAPI**: Async REST API framework
            - **Streamlit**: Interactive web UI framework
            - **Pydantic**: Data validation and settings
            - **FAISS**: Vector similarity search
            - **SQLAlchemy**: Database ORM with audit logging
            
            **AI/ML Stack**
            - **OpenAI**: GPT-4o, GPT-4, GPT-3.5-turbo
            - **Anthropic**: Claude-3 models via direct API
            - **AWS Bedrock**: Claude models via AWS
            - **Sentence Transformers**: Text embeddings
            - **Hugging Face**: Model hosting and inference
            """)
        
        with col2:
            st.markdown("""
            **Infrastructure**
            - **Docker**: Containerization
            - **Redis**: Session state management
            - **SQLite**: Audit and analytics database
            - **Diskcache**: Multi-layer caching
            - **Nginx**: Reverse proxy and load balancing
            
            **Development Tools**
            - **pytest**: Testing framework with asyncio
            - **black**: Code formatting
            - **ruff**: Fast Python linter
            - **mypy**: Static type checking
            - **coverage**: Test coverage reporting
            """)
    
    def _render_analytics_info(self):
        """Render analytics information."""
        st.subheader("📊 Analytics & Monitoring")
        
        st.markdown("""
        ### Pattern Analytics
        - **Real-time Tracking**: Pattern match frequency and acceptance rates
        - **Quality Scoring**: Pattern effectiveness and user satisfaction
        - **Usage Trends**: Time-based analysis with session filtering
        - **Performance Metrics**: Response times and success rates
        
        ### Security Monitoring
        - **Attack Detection**: Real-time monitoring of security events
        - **Threat Intelligence**: Pattern recognition for emerging attacks
        - **User Education**: Contextual guidance for security violations
        - **Compliance Reporting**: Audit trails for regulatory requirements
        
        ### System Health
        - **Performance Monitoring**: API response times and throughput
        - **Error Tracking**: Comprehensive error logging and alerting
        - **Resource Usage**: Memory, CPU, and storage monitoring
        - **Availability Metrics**: Uptime and service reliability
        """)
    
    def _render_security_info(self):
        """Render security information."""
        st.subheader("🔒 Security Features")
        
        st.markdown("""
        ### Advanced Prompt Defense System
        
        **8 Specialized Detectors:**
        1. **Overt Injection Detection**: Direct prompt manipulation attempts
        2. **Covert Injection Detection**: Hidden attacks (base64, markdown, zero-width chars)
        3. **Multilingual Attack Detection**: Security validation in 6 languages
        4. **Context Attack Detection**: Buried instructions and lorem ipsum attacks
        5. **Data Egress Protection**: System prompt and environment variable protection
        6. **Business Logic Protection**: Configuration access and safety toggle protection
        7. **Protocol Tampering Detection**: JSON validation and format manipulation protection
        8. **Scope Validation**: Business domain validation and enforcement
        
        ### Security Infrastructure
        - **Real-time Monitoring**: Comprehensive attack detection with alerting
        - **User Education**: Contextual guidance and educational messaging
        - **Performance Optimization**: Sub-100ms validation with intelligent caching
        - **Deployment Management**: Gradual rollout with automatic rollback
        - **Configuration Management**: Centralized security settings with validation
        
        ### Compliance & Privacy
        - **Data Protection**: PII redaction in logs and audit trails
        - **Audit Logging**: Comprehensive security event tracking
        - **Access Control**: Role-based permissions and authentication
        - **Encryption**: Data encryption in transit and at rest
        """)
        
        # Version information
        st.divider()
        self._render_version_info()
    
    def _render_version_info(self):
        """Render version and build information."""
        st.subheader("📋 Version Information")
        
        try:
            # Try to read version from file
            version_file = Path("VERSION")
            if version_file.exists():
                version = version_file.read_text().strip()
            else:
                version = "Development"
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric("Version", version)
            
            with col2:
                st.metric("Python", "3.10+")
            
            with col3:
                st.metric("Architecture", "Microservices")
            
        except Exception as e:
            st.warning(f"Could not load version information: {str(e)}")
        
        # Additional system info
        st.markdown("""
        ### Support & Documentation
        - **GitHub Repository**: [View Source Code](https://github.com/your-org/aaa-system)
        - **Documentation**: [User Guide & API Docs](https://docs.aaa-system.com)
        - **Support**: [Contact Support](mailto:support@aaa-system.com)
        - **License**: MIT License
        """)
        
        # Debug information (if enabled)
        if st.session_state.get('debug_mode', False):
            st.divider()
            st.subheader("🐛 Debug Information")
            
            debug_info = {
                'Session ID': st.session_state.get('session_id', 'None'),
                'Current Phase': st.session_state.get('current_phase', 'None'),
                'Progress': f"{st.session_state.get('progress', 0)}%",
                'Provider': st.session_state.get('provider_config', {}).get('provider', 'None'),
                'Processing': st.session_state.get('processing', False)
            }
            
            st.json(debug_info)