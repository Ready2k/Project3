"""Analysis tab component for requirement input functionality."""

# Standard library imports
import asyncio
from typing import Dict, List, Optional, Any

# Third-party imports
import httpx
import streamlit as st

# Local application imports
from app.ui.components.session_management import SessionManagementComponent
from app.ui.tabs.base import BaseTab
from app.utils.logger import app_logger
from app.utils.result import Result

# API configuration
API_BASE_URL = "http://localhost:8000"


class AnalysisTab(BaseTab):
    """Analysis tab for requirement input and processing."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__(
            tab_id="analysis",
            title="📝 Analysis",
            description="Input and analyze requirements for automation assessment"
        )
        self.session_manager = session_manager
        self.service_registry = service_registry
        self.session_component = None  # Will be initialized in initialize()
    
    def initialize(self) -> None:
        """Initialize the analysis tab resources."""
        if not self._initialized:
            self.session_component = SessionManagementComponent(self.session_manager)
            self._initialized = True
    

    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render the analysis tab content."""
        # Ensure tab is initialized
        self.ensure_initialized()
        
        # Input methods section
        if not st.session_state.get('session_id'):
            self._render_input_methods()
        
        # Progress tracking and results
        if st.session_state.session_id:
            self._render_progress_tracking()
            
            # Session information and actions
            st.divider()
            self.session_component.render_session_info()
            
            # Reset button
            if st.button("🔄 Start New Analysis", key="start_new_analysis_btn"):
                self.session_manager.reset_session()
                st.rerun()
    
    def _render_input_methods(self):
        """Render input method selection and forms."""
        st.header("📝 Input Methods")
        
        input_method = st.selectbox(
            "Choose your input method:",
            ["Text Input", "File Upload", "Jira Integration", "Resume Previous Session"],
            key="input_method_select"
        )
        
        if input_method == "Text Input":
            self._render_text_input()
        elif input_method == "File Upload":
            self._render_file_upload()
        elif input_method == "Jira Integration":
            self._render_jira_integration()
        elif input_method == "Resume Previous Session":
            self._render_resume_session()
    
    def _render_text_input(self):
        """Render text input form."""
        st.subheader("📝 Text Input")
        
        with st.form("text_input_form"):
            description = st.text_area(
                "Describe your requirement:",
                height=200,
                placeholder="Enter your business requirement or user story here...",
                help="Provide a detailed description of what you want to automate"
            )
            
            # Technology constraints
            st.subheader("🔧 Technology Constraints (Optional)")
            
            col1, col2 = st.columns(2)
            
            with col1:
                restricted_technologies = st.text_area(
                    "Restricted Technologies",
                    placeholder="Azure\nOracle Database\nSalesforce",
                    help="List technologies that cannot be used (one per line)"
                )
                
                required_integrations = st.text_area(
                    "Required Integrations",
                    placeholder="Active Directory\nSAP\nExisting CRM",
                    help="List existing systems that must be integrated (one per line)"
                )
            
            with col2:
                compliance_requirements = st.multiselect(
                    "Compliance Requirements",
                    ["GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA", "ISO-27001", "FedRAMP"],
                    help="Select applicable compliance requirements"
                )
                
                data_sensitivity = st.selectbox(
                    "Data Sensitivity Level",
                    ["Public", "Internal", "Confidential", "Restricted"],
                    help="Classification of data being processed"
                )
                
                budget_preference = st.selectbox(
                    "Budget Preference",
                    ["Open Source Preferred", "Enterprise Solutions OK", "No Preference"],
                    help="Budget constraints for technology selection"
                )
                
                deployment_preference = st.selectbox(
                    "Deployment Preference",
                    ["Cloud-only", "On-premises", "Hybrid", "No Preference"],
                    help="Preferred deployment model"
                )
            
            submitted = st.form_submit_button("🚀 Start Analysis")
            
            if submitted and description.strip():
                self._start_analysis({
                    'description': description.strip(),
                    'restricted_technologies': [tech.strip() for tech in restricted_technologies.split('\n') if tech.strip()],
                    'required_integrations': [integ.strip() for integ in required_integrations.split('\n') if integ.strip()],
                    'compliance_requirements': compliance_requirements,
                    'data_sensitivity': data_sensitivity,
                    'budget_preference': budget_preference,
                    'deployment_preference': deployment_preference
                })
            elif submitted:
                st.error("Please enter a requirement description.")
    
    def _render_file_upload(self):
        """Render file upload form."""
        st.subheader("📁 File Upload")
        
        uploaded_file = st.file_uploader(
            "Upload a file containing your requirements",
            type=['txt', 'md', 'docx', 'pdf'],
            help="Supported formats: TXT, Markdown, DOCX, PDF"
        )
        
        if uploaded_file is not None:
            try:
                # Read file content based on type
                if uploaded_file.type == "text/plain":
                    content = str(uploaded_file.read(), "utf-8")
                elif uploaded_file.type == "text/markdown":
                    content = str(uploaded_file.read(), "utf-8")
                else:
                    st.error("File type not yet supported. Please use TXT or Markdown files.")
                    return
                
                st.text_area("File Content Preview:", value=content, height=200, disabled=True)
                
                if st.button("🚀 Analyze File Content", key="analyze_file_content_btn"):
                    # For file uploads, we need to use a different approach
                    self._start_file_analysis(content, uploaded_file.name)
                    
            except Exception as e:
                st.error(f"Error reading file: {str(e)}")
    
    def _render_jira_integration(self):
        """Render enhanced Jira integration interface with Data Center support."""
        st.subheader("🎫 Jira Integration")
        
        with st.form("jira_form"):
            st.write("**Jira Configuration**")
            
            # Deployment Type Selection
            col1, col2 = st.columns(2)
            with col1:
                deployment_type = st.selectbox(
                    "Deployment Type",
                    options=["auto_detect", "cloud", "data_center", "server"],
                    format_func=lambda x: {
                        "auto_detect": "🔍 Auto-detect",
                        "cloud": "☁️ Jira Cloud",
                        "data_center": "🏢 Jira Data Center",
                        "server": "🖥️ Jira Server"
                    }[x],
                    help="Select your Jira deployment type or let the system auto-detect"
                )
            
            with col2:
                auth_type = st.selectbox(
                    "Authentication Method",
                    options=["api_token", "pat", "sso", "basic"],
                    format_func=lambda x: {
                        "api_token": "🔑 API Token (Cloud)",
                        "pat": "🎫 Personal Access Token (Data Center)",
                        "sso": "🔐 SSO/Current Session",
                        "basic": "👤 Username/Password"
                    }[x],
                    help="Choose authentication method based on your Jira deployment"
                )
            
            # Base URL Configuration
            jira_base_url = st.text_input(
                "Jira Base URL",
                placeholder="https://your-domain.atlassian.net or https://jira.company.com:8080",
                help="Your Jira instance URL (include custom port if needed)"
            )
            
            # Authentication Configuration (dynamic based on auth_type)
            st.write("**Authentication Details**")
            
            jira_email = None
            jira_api_token = None
            jira_username = None
            jira_password = None
            jira_personal_access_token = None
            
            if auth_type == "api_token":
                col1, col2 = st.columns(2)
                with col1:
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
            
            elif auth_type == "pat":
                jira_personal_access_token = st.text_input(
                    "Personal Access Token",
                    type="password",
                    help="Generate from Jira Data Center: Profile > Personal Access Tokens"
                )
            
            elif auth_type == "basic":
                col1, col2 = st.columns(2)
                with col1:
                    jira_username = st.text_input(
                        "Username",
                        placeholder="your-username",
                        help="Your Jira username"
                    )
                with col2:
                    jira_password = st.text_input(
                        "Password",
                        type="password",
                        help="Your Jira password (stored only for current session)"
                    )
            
            elif auth_type == "sso":
                st.info("🔐 SSO authentication will attempt to use your current browser session or Windows credentials")
                use_sso = True
            else:
                use_sso = False
            
            # Network Configuration (expandable section)
            with st.expander("🌐 Network Configuration (Optional)", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    verify_ssl = st.checkbox(
                        "Verify SSL Certificates",
                        value=True,
                        help="Uncheck for self-signed certificates (not recommended for production)"
                    )
                    
                    # Show security warning when SSL verification is disabled
                    if not verify_ssl:
                        st.warning("""
                        ⚠️  **Security Warning: SSL Verification Disabled**
                        
                        • Your connection is vulnerable to man-in-the-middle attacks
                        • Only use this setting for testing with self-signed certificates
                        • **NEVER disable SSL verification in production environments**
                        • Consider adding the server's certificate to 'Custom CA Certificate Path' instead
                        """)
                    else:
                        st.success("🔒 SSL verification enabled - connections are secure")
                    
                    ca_cert_path = st.text_input(
                        "Custom CA Certificate Path",
                        placeholder="/path/to/ca-bundle.crt",
                        help="Path to custom CA certificate bundle for internal certificates"
                    )
                    
                    proxy_url = st.text_input(
                        "Proxy URL",
                        placeholder="http://proxy.company.com:8080",
                        help="HTTP/HTTPS proxy URL if required"
                    )
                
                with col2:
                    timeout = st.number_input(
                        "Connection Timeout (seconds)",
                        min_value=5,
                        max_value=300,
                        value=30,
                        help="Timeout for network requests"
                    )
                    
                    context_path = st.text_input(
                        "Context Path",
                        placeholder="/jira",
                        help="Custom context path for Data Center installations"
                    )
                    
                    custom_port = st.number_input(
                        "Custom Port",
                        min_value=1,
                        max_value=65535,
                        value=None,
                        help="Custom port if not using standard HTTP/HTTPS ports"
                    )
            
            # Ticket Key Input
            jira_ticket_key = st.text_input(
                "Ticket Key",
                placeholder="PROJ-123",
                help="Jira ticket key (e.g., PROJ-123)"
            )
            
            # Form submission buttons
            col1, col2, col3 = st.columns([1, 1, 2])
            
            with col1:
                test_connection = st.form_submit_button("🔗 Test Connection", type="secondary")
            
            with col2:
                fetch_ticket = st.form_submit_button("📥 Fetch Ticket", type="secondary")
            
            with col3:
                submit_jira = st.form_submit_button("🚀 Start Analysis", type="primary")
        
        # Handle test connection
        if test_connection:
            self._handle_jira_test_connection(
                jira_base_url, auth_type, jira_email, jira_api_token, jira_username, 
                jira_password, jira_personal_access_token, verify_ssl, ca_cert_path, 
                proxy_url, timeout, context_path, custom_port
            )
        
        # Handle fetch ticket
        if fetch_ticket:
            self._handle_jira_fetch_ticket(
                jira_base_url, auth_type, jira_email, jira_api_token, jira_username, 
                jira_password, jira_personal_access_token, verify_ssl, ca_cert_path, 
                proxy_url, timeout, context_path, custom_port, jira_ticket_key
            )
        
        # Handle submit analysis
        if submit_jira:
            self._handle_jira_submit_analysis(
                jira_base_url, auth_type, jira_email, jira_api_token, jira_username, 
                jira_password, jira_personal_access_token, verify_ssl, ca_cert_path, 
                proxy_url, timeout, context_path, custom_port, jira_ticket_key
            )
    
    def _render_resume_session(self):
        """Render session resume form."""
        st.subheader("🔄 Resume Previous Session")
        
        with st.form("resume_session_form"):
            session_id = st.text_input(
                "Session ID",
                placeholder="Enter your session ID here...",
                help="The session ID from a previous analysis"
            )
            
            submitted = st.form_submit_button("🔄 Resume Session")
            
            if submitted and session_id.strip():
                self._resume_session(session_id.strip())
            elif submitted:
                st.error("Please enter a session ID.")
        
        # Help section
        with st.expander("❓ Where do I find my Session ID?"):
            st.markdown("""
            You can find your Session ID in several places:
            
            1. **During Analysis**: Look for the "Current Session Information" section
            2. **In Results**: The session ID is displayed at the top of results
            3. **In Export Files**: Session ID is included in exported JSON and Markdown files
            4. **In Browser URL**: Some pages include the session ID in the URL
            
            Session IDs look like: `f4920b10-1131-4d79-842f-80ab97998bea`
            """)
    
    def _render_progress_tracking(self):
        """Render progress tracking section."""
        if st.session_state.current_phase:
            st.header("📊 Analysis Progress")
            
            # Progress bar
            progress = st.session_state.progress / 100.0
            st.progress(progress)
            
            # Current phase
            st.info(f"Current Phase: {st.session_state.current_phase}")
            
            # Auto-refresh for active sessions using Streamlit's fragment approach
            if st.session_state.progress < 100 and not st.session_state.processing:
                # Check status on page load/refresh
                try:
                    response = asyncio.run(self._make_api_request("GET", f"/status/{st.session_state.session_id}"))
                    
                    # Update session state if there are changes
                    new_phase = response.get('phase', st.session_state.current_phase)
                    new_progress = response.get('progress', st.session_state.progress)
                    
                    if new_phase != st.session_state.current_phase or new_progress != st.session_state.progress:
                        st.session_state.current_phase = new_phase
                        st.session_state.progress = new_progress
                        # Don't rerun here to avoid infinite loop, let the user see the update
                        
                except Exception as e:
                    app_logger.error(f"Failed to check status: {str(e)}")
                
                # Show a message about auto-refresh
                st.info("💡 Refresh the page to check for progress updates, or use the button below.")
            
            # Processing indicator
            if st.session_state.processing:
                st.spinner("Processing...")
            
            # Auto-refresh controls
            if st.session_state.progress < 100:
                col1, col2 = st.columns([1, 1])
                
                with col1:
                    if st.button("🔄 Check Progress", key="check_progress_btn"):
                        try:
                            response = asyncio.run(self._make_api_request("GET", f"/status/{st.session_state.session_id}"))
                            st.session_state.current_phase = response.get('phase', st.session_state.current_phase)
                            st.session_state.progress = response.get('progress', st.session_state.progress)
                            st.rerun()
                        except Exception as e:
                            st.error(f"Failed to check progress: {str(e)}")
                
                with col2:
                    # Auto-refresh toggle
                    auto_refresh = st.checkbox("🔄 Auto-refresh (5s)", key="auto_refresh_toggle")
                    
                    if auto_refresh:
                        # JavaScript-based auto-refresh
                        st.markdown("""
                        <script>
                        setTimeout(function(){
                            window.location.reload();
                        }, 5000);
                        </script>
                        """, unsafe_allow_html=True)
                        st.info("⏱️ Page will auto-refresh in 5 seconds...")
            
            # Show results when analysis is complete
            elif st.session_state.progress >= 100:
                st.success("🎉 Analysis Complete!")
                self._render_analysis_results()
    
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
    
    def _start_analysis(self, data: Dict[str, Any]):
        """Start analysis with the provided data."""
        try:
            st.session_state.processing = True
            
            # Restructure data to match ingest endpoint expectations
            payload = {
                "text": data.get('description', ''),
                "domain": data.get('domain', ''),
                "pattern_types": data.get('pattern_types', [])
            }
            
            # Add constraints if they exist
            constraints = {}
            if data.get('restricted_technologies'):
                constraints['banned_tools'] = data['restricted_technologies']
            if data.get('required_integrations'):
                constraints['required_integrations'] = data['required_integrations']
            if data.get('compliance_requirements'):
                constraints['compliance_requirements'] = data['compliance_requirements']
            if data.get('data_sensitivity'):
                constraints['data_sensitivity'] = data['data_sensitivity']
            if data.get('budget_preference'):
                constraints['budget_constraints'] = data['budget_preference']
            if data.get('deployment_preference'):
                constraints['deployment_preference'] = data['deployment_preference']
            
            if constraints:
                payload['constraints'] = constraints
            
            # Prepare ingest request payload
            ingest_payload = {
                "source": "text",
                "payload": payload,
                "provider_config": st.session_state.get('provider_config')
            }
            
            # Make API request to the correct endpoint
            response = asyncio.run(self._make_api_request("POST", "/ingest", ingest_payload))
            
            # Update session state
            st.session_state.session_id = response.get('session_id')
            st.session_state.current_phase = "Analysis Started"
            st.session_state.progress = 10
            
            st.success(f"✅ Analysis started! Session ID: {st.session_state.session_id}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to start analysis: {str(e)}")
            app_logger.error(f"Analysis start failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _start_file_analysis(self, content: str, filename: str):
        """Start analysis with file content."""
        try:
            st.session_state.processing = True
            
            # Prepare ingest request payload for file source
            ingest_payload = {
                "source": "file",
                "payload": {
                    "content": content,
                    "filename": filename
                },
                "provider_config": st.session_state.get('provider_config')
            }
            
            # Make API request to the correct endpoint
            response = asyncio.run(self._make_api_request("POST", "/ingest", ingest_payload))
            
            # Update session state
            st.session_state.session_id = response.get('session_id')
            st.session_state.current_phase = "Analysis Started"
            st.session_state.progress = 10
            
            st.success(f"✅ File analysis started! Session ID: {st.session_state.session_id}")
            st.rerun()
            
        except Exception as e:
            st.error(f"Failed to start file analysis: {str(e)}")
            app_logger.error(f"File analysis start failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _handle_jira_test_connection(self, jira_base_url, auth_type, jira_email, jira_api_token, 
                                   jira_username, jira_password, jira_personal_access_token, 
                                   verify_ssl, ca_cert_path, proxy_url, timeout, context_path, custom_port):
        """Handle Jira connection test."""
        # Validate required fields based on auth type
        validation_errors = []
        
        if not jira_base_url:
            validation_errors.append("Base URL is required")
        
        if auth_type == "api_token":
            if not jira_email:
                validation_errors.append("Email is required for API token authentication")
            if not jira_api_token:
                validation_errors.append("API token is required for API token authentication")
        elif auth_type == "pat":
            if not jira_personal_access_token:
                validation_errors.append("Personal Access Token is required for PAT authentication")
        elif auth_type == "basic":
            if not jira_username:
                validation_errors.append("Username is required for basic authentication")
            if not jira_password:
                validation_errors.append("Password is required for basic authentication")
        # SSO doesn't require additional fields
        
        if validation_errors:
            st.error("❌ Please fix the following issues:\n" + "\n".join(f"• {error}" for error in validation_errors))
        else:
            with st.spinner("Testing Jira connection..."):
                try:
                    # Prepare request payload with all configuration options
                    test_payload = self._build_jira_payload(
                        jira_base_url, auth_type, jira_email, jira_api_token, jira_username, 
                        jira_password, jira_personal_access_token, verify_ssl, ca_cert_path, 
                        proxy_url, timeout, context_path, custom_port
                    )
                    
                    test_result = asyncio.run(self._make_api_request("POST", "/jira/test", test_payload))
                    
                    if test_result and test_result.get("success"):
                        st.success("✅ Jira connection successful!")
                        self._display_connection_details(test_result)
                    else:
                        error_msg = test_result.get("message", "Unknown error") if test_result else "Connection failed"
                        st.error(f"❌ Connection failed: {error_msg}")
                        self._display_error_details(test_result)
                        
                except Exception as e:
                    st.error(f"❌ Connection failed: {str(e)}")
    
    def _handle_jira_fetch_ticket(self, jira_base_url, auth_type, jira_email, jira_api_token, 
                                jira_username, jira_password, jira_personal_access_token, 
                                verify_ssl, ca_cert_path, proxy_url, timeout, context_path, 
                                custom_port, jira_ticket_key):
        """Handle Jira ticket fetch."""
        # Validate required fields
        validation_errors = []
        
        if not jira_base_url:
            validation_errors.append("Base URL is required")
        if not jira_ticket_key:
            validation_errors.append("Ticket key is required")
        
        if auth_type == "api_token":
            if not jira_email:
                validation_errors.append("Email is required for API token authentication")
            if not jira_api_token:
                validation_errors.append("API token is required for API token authentication")
        elif auth_type == "pat":
            if not jira_personal_access_token:
                validation_errors.append("Personal Access Token is required for PAT authentication")
        elif auth_type == "basic":
            if not jira_username:
                validation_errors.append("Username is required for basic authentication")
            if not jira_password:
                validation_errors.append("Password is required for basic authentication")
        
        if validation_errors:
            st.error("❌ Please fix the following issues:\n" + "\n".join(f"• {error}" for error in validation_errors))
        else:
            with st.spinner(f"Fetching ticket {jira_ticket_key}..."):
                try:
                    # Prepare request payload
                    fetch_payload = self._build_jira_payload(
                        jira_base_url, auth_type, jira_email, jira_api_token, jira_username, 
                        jira_password, jira_personal_access_token, verify_ssl, ca_cert_path, 
                        proxy_url, timeout, context_path, custom_port, jira_ticket_key
                    )
                    
                    fetch_result = asyncio.run(self._make_api_request("POST", "/jira/fetch", fetch_payload))
                    
                    if fetch_result:
                        ticket_data = fetch_result.get("ticket_data", {})
                        requirements = fetch_result.get("requirements", {})
                        
                        st.success(f"✅ Successfully fetched ticket: {ticket_data.get('key', 'Unknown')}")
                        self._display_ticket_preview(ticket_data, requirements)
                    else:
                        st.error("❌ Failed to fetch ticket. Please check your credentials and ticket key.")
                        
                except Exception as e:
                    st.error(f"❌ Failed to fetch ticket: {str(e)}")
    
    def _handle_jira_submit_analysis(self, jira_base_url, auth_type, jira_email, jira_api_token, 
                                   jira_username, jira_password, jira_personal_access_token, 
                                   verify_ssl, ca_cert_path, proxy_url, timeout, context_path, 
                                   custom_port, jira_ticket_key):
        """Handle Jira analysis submission."""
        # Validate required fields
        validation_errors = []
        
        if not jira_base_url:
            validation_errors.append("Base URL is required")
        if not jira_ticket_key:
            validation_errors.append("Ticket key is required")
        
        if auth_type == "api_token":
            if not jira_email:
                validation_errors.append("Email is required for API token authentication")
            if not jira_api_token:
                validation_errors.append("API token is required for API token authentication")
        elif auth_type == "pat":
            if not jira_personal_access_token:
                validation_errors.append("Personal Access Token is required for PAT authentication")
        elif auth_type == "basic":
            if not jira_username:
                validation_errors.append("Username is required for basic authentication")
            if not jira_password:
                validation_errors.append("Password is required for basic authentication")
        
        if validation_errors:
            st.error("❌ Please fix the following issues:\n" + "\n".join(f"• {error}" for error in validation_errors))
        else:
            with st.spinner("Starting Jira analysis..."):
                try:
                    st.session_state.processing = True
                    
                    # Prepare request payload
                    payload = self._build_jira_payload(
                        jira_base_url, auth_type, jira_email, jira_api_token, jira_username, 
                        jira_password, jira_personal_access_token, verify_ssl, ca_cert_path, 
                        proxy_url, timeout, context_path, custom_port, jira_ticket_key
                    )
                    
                    # Use the ingest endpoint with Jira source
                    response = asyncio.run(self._make_api_request("POST", "/ingest", {
                        "source": "jira",
                        "payload": payload,
                        "provider_config": st.session_state.get('provider_config')
                    }))
                    
                    # Update session state
                    st.session_state.session_id = response.get('session_id')
                    st.session_state.current_phase = response.get('phase', 'Jira Analysis Started')
                    st.session_state.progress = response.get('progress', 10)
                    
                    st.success(f"✅ Jira analysis started! Session ID: {st.session_state.session_id}")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Failed to start Jira analysis: {str(e)}")
                    app_logger.error(f"Jira analysis start failed: {str(e)}")
                finally:
                    st.session_state.processing = False
    
    def _build_jira_payload(self, jira_base_url, auth_type, jira_email, jira_api_token, 
                          jira_username, jira_password, jira_personal_access_token, 
                          verify_ssl, ca_cert_path, proxy_url, timeout, context_path, 
                          custom_port, jira_ticket_key=None):
        """Build Jira request payload."""
        payload = {
            "base_url": jira_base_url,
            "auth_type": auth_type,
            
            # Authentication fields
            "email": jira_email,
            "api_token": jira_api_token,
            "username": jira_username,
            "password": jira_password,
            "personal_access_token": jira_personal_access_token,
            
            # Network configuration
            "verify_ssl": verify_ssl,
            "ca_cert_path": ca_cert_path if ca_cert_path else None,
            "proxy_url": proxy_url if proxy_url else None,
            "timeout": int(timeout),
            
            # SSO configuration
            "use_sso": auth_type == "sso",
            
            # Data Center configuration
            "context_path": context_path if context_path else None,
            "custom_port": int(custom_port) if custom_port else None
        }
        
        if jira_ticket_key:
            payload["ticket_key"] = jira_ticket_key
        
        # Remove None values to avoid API issues
        return {k: v for k, v in payload.items() if v is not None}
    
    def _display_connection_details(self, test_result):
        """Display connection test details."""
        deployment_info = test_result.get("deployment_info")
        ssl_config = test_result.get("ssl_configuration")
        
        if deployment_info or ssl_config:
            with st.expander("📋 Connection Details", expanded=True):
                col1, col2 = st.columns(2)
                
                with col1:
                    if deployment_info:
                        st.write(f"**Deployment Type:** {deployment_info.get('deployment_type', 'Unknown').title()}")
                        st.write(f"**Version:** {deployment_info.get('version', 'Unknown')}")
                        if deployment_info.get('build_number'):
                            st.write(f"**Build:** {deployment_info['build_number']}")
                    
                    # SSL Configuration Information
                    if ssl_config:
                        st.write("**SSL Configuration:**")
                        security_level = ssl_config.get('security_level', 'Unknown')
                        if security_level == 'HIGH':
                            st.write("🔒 Security Level: HIGH (SSL verification enabled)")
                        else:
                            st.write("⚠️  Security Level: LOW (SSL verification disabled)")
                        
                        if ssl_config.get('custom_ca_certificate'):
                            st.write("📋 Custom CA certificate configured")
                
                with col2:
                    if deployment_info:
                        st.write(f"**API Version:** {test_result.get('api_version', 'Unknown')}")
                        auth_methods = test_result.get("auth_methods_available", [])
                        if auth_methods:
                            st.write(f"**Available Auth Methods:** {', '.join(auth_methods)}")
                
                # Show SSL warnings if any
                if ssl_config and ssl_config.get('warnings'):
                    st.warning("**SSL Security Warnings:**")
                    for warning in ssl_config['warnings']:
                        st.write(f"• {warning}")
                
                if deployment_info:
                    if deployment_info.get('supports_sso'):
                        st.info("🔐 This instance supports SSO authentication")
                    if deployment_info.get('supports_pat'):
                        st.info("🎫 This instance supports Personal Access Tokens")
    
    def _display_error_details(self, test_result):
        """Display error details and troubleshooting information."""
        if not test_result:
            return
            
        error_details = test_result.get("error_details")
        if error_details:
            with st.expander("🔍 Troubleshooting Information", expanded=True):
                error_type = error_details.get('error_type', 'Unknown')
                st.write(f"**Error Type:** {error_type}")
                
                if error_details.get('error_code'):
                    st.write(f"**Error Code:** {error_details['error_code']}")
                
                # Show SSL-specific warnings and guidance
                if "ssl" in error_type.lower() or "certificate" in error_type.lower():
                    st.warning("""
                    🔒 **SSL Certificate Issue Detected**
                    
                    This appears to be an SSL certificate problem. Consider these options:
                    • For self-signed certificates: Add the certificate to 'Custom CA Certificate Path'
                    • For testing only: Temporarily disable 'Verify SSL Certificates'
                    • For production: Contact your administrator to fix the certificate
                    """)
                
                troubleshooting_steps = error_details.get('troubleshooting_steps', [])
                if troubleshooting_steps:
                    st.write("**Troubleshooting Steps:**")
                    for step in troubleshooting_steps:
                        st.write(f"• {step}")
    
    def _display_ticket_preview(self, ticket_data, requirements):
        """Display ticket preview information."""
        with st.expander("📋 Ticket Preview", expanded=True):
            col1, col2 = st.columns(2)
            
            with col1:
                st.write(f"**Key:** {ticket_data.get('key', 'N/A')}")
                st.write(f"**Summary:** {ticket_data.get('summary', 'N/A')}")
                st.write(f"**Status:** {ticket_data.get('status', 'N/A')}")
                st.write(f"**Priority:** {ticket_data.get('priority', 'N/A')}")
            
            with col2:
                st.write(f"**Type:** {ticket_data.get('issue_type', 'N/A')}")
                st.write(f"**Assignee:** {ticket_data.get('assignee', 'N/A')}")
                st.write(f"**Reporter:** {ticket_data.get('reporter', 'N/A')}")
                
                if ticket_data.get('labels'):
                    st.write(f"**Labels:** {', '.join(ticket_data['labels'])}")
            
            if ticket_data.get('description'):
                st.write("**Description:**")
                description = ticket_data.get('description', '')
                st.write(description[:500] + "..." if len(description) > 500 else description)
            
            # Show inferred requirements
            st.write("**Inferred Requirements:**")
            if requirements.get('domain'):
                st.write(f"- **Domain:** {requirements['domain']}")
            if requirements.get('pattern_types'):
                st.write(f"- **Pattern Types:** {', '.join(requirements['pattern_types'])}")
    

    
    def _resume_session(self, session_id: str):
        """Resume a previous session."""
        try:
            st.session_state.processing = True
            
            # Validate session ID format
            import re
            if not re.match(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', session_id, re.IGNORECASE):
                st.error("Invalid session ID format. Please check and try again.")
                return
            
            # Make API request to get session status
            response = asyncio.run(self._make_api_request("GET", f"/status/{session_id}"))
            
            # Update session state
            st.session_state.session_id = session_id
            st.session_state.current_phase = response.get('phase', 'Session Resumed')
            st.session_state.progress = response.get('progress', 0)
            st.session_state.recommendations = response.get('recommendations')
            
            st.success(f"✅ Session resumed successfully!")
            st.rerun()
            
        except Exception as e:
            if "Session not found" in str(e):
                st.error("Session not found. Please check the session ID and try again.")
            else:
                st.error(f"Failed to resume session: {str(e)}")
            app_logger.error(f"Session resume failed: {str(e)}")
        finally:
            st.session_state.processing = False
    
    def _render_analysis_results(self):
        """Render the analysis results when complete."""
        try:
            # Get the latest session data
            response = asyncio.run(self._make_api_request("GET", f"/status/{st.session_state.session_id}"))
            
            if response.get('phase') == 'DONE':
                st.header("📊 Analysis Results")
                
                # Show basic session info
                st.info(f"✅ Analysis completed for session: `{st.session_state.session_id}`")
                
                # Show requirements
                requirements = response.get('requirements', {})
                if requirements:
                    with st.expander("📝 Requirements Summary", expanded=True):
                        description = requirements.get('description', 'No description available')
                        st.write(description)
                        
                        if requirements.get('filename'):
                            st.caption(f"Source: {requirements['filename']}")
                
                # Try to get recommendations from session status
                try:
                    # Recommendations are stored in the session, accessible via status endpoint
                    recommendations_response = response  # Use the same response we already have
                    
                    # Check if session has recommendations
                    session_data = recommendations_response
                    if session_data and hasattr(session_data, 'get'):
                        # Try to get recommendations from session data
                        recommendations = session_data.get('recommendations', [])
                        
                        st.subheader("🤖 AI Recommendations")
                        
                        if isinstance(recommendations, list) and recommendations:
                            for i, rec in enumerate(recommendations, 1):
                                with st.expander(f"Recommendation {i}", expanded=i == 1):
                                    if isinstance(rec, dict):
                                        st.write(f"**Feasibility:** {rec.get('feasibility', 'Unknown')}")
                                        st.write(f"**Confidence:** {rec.get('confidence', 'Unknown')}")
                                        
                                        if rec.get('description'):
                                            st.write("**Description:**")
                                            st.write(rec['description'])
                                        
                                        if rec.get('tech_stack'):
                                            st.write("**Technology Stack:**")
                                            if isinstance(rec['tech_stack'], list):
                                                for tech in rec['tech_stack']:
                                                    st.write(f"• {tech}")
                                            else:
                                                st.write(rec['tech_stack'])
                                    else:
                                        st.write(str(rec))
                        else:
                            st.info("No specific recommendations available yet.")
                    else:
                        st.info("Recommendations are being generated. Please check the other tabs for detailed results.")
                
                except Exception as e:
                    app_logger.error(f"Failed to get recommendations: {str(e)}")
                    st.info("💡 For detailed analysis results, please check the **Diagrams** and **Observability** tabs.")
                
                # Navigation hints
                st.markdown("---")
                st.markdown("### 🧭 Next Steps")
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.markdown("**📊 View Diagrams**")
                    st.markdown("Check the *Diagrams* tab for architecture visualizations")
                
                with col2:
                    st.markdown("**📈 View Analytics**")
                    st.markdown("Check the *Observability* tab for detailed metrics")
                
                with col3:
                    st.markdown("**📤 Export Results**")
                    st.markdown("Use the export functionality to save your analysis")
            
            else:
                st.warning(f"Analysis not yet complete. Current phase: {response.get('phase', 'Unknown')}")
                
        except Exception as e:
            st.error(f"Failed to load analysis results: {str(e)}")
            app_logger.error(f"Failed to render analysis results: {str(e)}")