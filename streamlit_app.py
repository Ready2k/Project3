"""Streamlit UI for Automated AI Assessment (AAA) application."""

import asyncio
import json
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
import streamlit as st
from streamlit.components.v1 import html

# Import logger for error handling
try:
    from app.utils.logger import app_logger
except ImportError:
    # Fallback logger if app.utils.logger is not available
    import logging
    app_logger = logging.getLogger(__name__)

# Optional import for OpenAI (for diagram generation)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Mermaid diagram functions (LLM-generated for specific requirements)
async def make_llm_request(prompt: str, provider_config: Dict, purpose: str = "diagram_generation") -> str:
    """Make a request to the LLM for diagram generation using audited provider."""
    try:
        # Import here to avoid circular imports
        from app.api import create_llm_provider, ProviderConfig
        
        # Create provider config object
        config = ProviderConfig(
            provider=provider_config.get('provider', 'openai'),
            model=provider_config.get('model', 'gpt-4o'),
            api_key=provider_config.get('api_key', ''),
            temperature=0.3,
            max_tokens=1000
        )
        
        # Get session ID for audit logging
        session_id = st.session_state.get('session_id', 'mermaid-generation')
        
        # Create audited LLM provider
        llm_provider = create_llm_provider(config, session_id)
        
        # Make the request through the audited provider
        response = await llm_provider.generate(prompt, purpose=purpose)
        
        if not response:
            raise Exception("Empty response from LLM")
        
        # Clean the response - remove markdown code blocks if present
        content = response.strip()
        if content.startswith('```mermaid'):
            content = content.replace('```mermaid', '').replace('```', '').strip()
        elif content.startswith('```'):
            content = content.replace('```', '').strip()
        
        return content
        
    except Exception as e:
        raise Exception(f"LLM request failed: {str(e)}")

def _sanitize(label: str) -> str:
    """Sanitize labels for Mermaid diagrams."""
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.:")
    return ''.join(ch if ch in allowed else '_' for ch in (label or '')) or 'unknown'

async def build_context_diagram(requirement: str, recommendations: List[Dict]) -> str:
    """Build a context diagram using LLM based on the specific requirement."""
    prompt = f"""Generate a Mermaid context diagram (C4 Level 1) for this automation requirement:

REQUIREMENT: {requirement}

RECOMMENDATIONS: {recommendations[0].get('reasoning', 'No recommendations available') if recommendations else 'No recommendations available'}

Create a context diagram showing:
- The user/actor who will use the system
- The main system being automated
- External systems it needs to integrate with
- Data sources it needs to access

Use Mermaid flowchart syntax. Start with "flowchart LR" and use:
- Circles for people: user([User Name])
- Rectangles for systems: system[System Name]
- Cylinders for databases: db[(Database)]

Example format:
flowchart LR
  user([Warehouse Supervisor])
  scanner[Mobile Scanner App]
  api[Inventory API]
  db[(Inventory Database)]
  erp[ERP System]
  
  user --> scanner --> api
  api --> db
  api --> erp

IMPORTANT: Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)."""

    try:
        # Use the current provider config to generate the diagram
        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            # Fallback for fake provider
            return """flowchart LR
  user([User])
  system[Automated System]
  db[(Database)]
  api[External API]
  
  user --> system
  system --> db
  system --> api"""
        
        response = await make_llm_request(prompt, provider_config)
        return response.strip()
    except Exception as e:
        return f"""flowchart LR
  user([User])
  system[System]
  note[Diagram generation failed: {str(e)}]
  
  user --> system
  system --> note"""

async def build_container_diagram(requirement: str, recommendations: List[Dict]) -> str:
    """Build a container diagram using LLM based on the specific requirement."""
    prompt = f"""Generate a Mermaid container diagram (C4 Level 2) for this automation requirement:

REQUIREMENT: {requirement}

RECOMMENDATIONS: {recommendations[0].get('reasoning', 'No recommendations available') if recommendations else 'No recommendations available'}

Create a container diagram showing the internal components and how they interact:
- Web/mobile interfaces
- APIs and services
- Databases and data stores
- Background processes
- Integration points

Use Mermaid flowchart syntax with subgraphs. Start with "flowchart TB" and use:
- Rectangles for containers: api[API Service]
- Cylinders for databases: db[(Database)]
- Subgraphs for system boundaries

Example format:
flowchart TB
  subgraph "Inventory System"
    ui[Mobile Scanner UI]
    api[Inventory API]
    rules[Business Rules Engine]
    queue[Message Queue]
  end
  
  db[(Inventory DB)]
  erp[ERP System]
  
  ui --> api
  api --> rules
  api --> db
  rules --> queue
  queue --> erp

IMPORTANT: Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)."""

    try:
        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            return """flowchart TB
  subgraph "Automated System"
    ui[User Interface]
    api[API Layer]
    logic[Business Logic]
  end
  
  db[(Database)]
  external[External System]
  
  ui --> api
  api --> logic
  logic --> db
  logic --> external"""
        
        response = await make_llm_request(prompt, provider_config)
        return response.strip()
    except Exception as e:
        return f"""flowchart TB
  system[System]
  error[Container diagram generation failed: {str(e)}]
  
  system --> error"""

async def build_sequence_diagram(requirement: str, recommendations: List[Dict]) -> str:
    """Build a sequence diagram using LLM based on the specific requirement."""
    prompt = f"""Generate a Mermaid sequence diagram for this automation requirement:

REQUIREMENT: {requirement}

RECOMMENDATIONS: {recommendations[0].get('reasoning', 'No recommendations available') if recommendations else 'No recommendations available'}

Create a sequence diagram showing the step-by-step flow of the automated process:
- User interactions
- System calls and responses
- Database operations
- External API calls
- Decision points and alternatives

Use Mermaid sequenceDiagram syntax:
- participant A as Actor Name
- A->>B: Message
- B-->>A: Response
- alt/else for conditions
- Note over A: Comments

Example (like your warehouse example):
sequenceDiagram
  participant W as Worker (Android Scanner)
  participant API as FastAPI Orchestrator
  participant DB as PostgreSQL (Inventory/Thresholds)
  participant ERP as ERP API
  
  W->>API: POST /scan {{sku, qty, location, ts}}
  API->>DB: GET inventory, reorder_threshold, supplier
  API-->>API: Apply rules (seasonality, high-value gate)
  alt Below threshold & not seasonal
    API->>ERP: Create purchase order (sku, qty, supplier)
    ERP-->>API: PO ID
  else High-value item
    API-->>W: Event (Approval required)
  end

IMPORTANT: Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)."""

    try:
        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            return """sequenceDiagram
  participant U as User
  participant S as System
  participant D as Database
  participant E as External API
  
  U->>S: Trigger automation
  S->>D: Query data
  D-->>S: Return data
  S->>E: Process request
  E-->>S: Response
  S-->>U: Result"""
        
        response = await make_llm_request(prompt, provider_config)
        return response.strip()
    except Exception as e:
        return f"""sequenceDiagram
  participant U as User
  participant E as Error
  
  U->>E: Sequence diagram generation failed: {str(e)}"""

# Configuration
API_BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 2  # seconds


class AutomatedAIAssessmentUI:
    """Main Streamlit UI class for Automated AI Assessment (AAA)."""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Automated AI Assessment (AAA)",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        if 'session_id' not in st.session_state:
            st.session_state.session_id = None
        if 'current_phase' not in st.session_state:
            st.session_state.current_phase = None
        if 'progress' not in st.session_state:
            st.session_state.progress = 0
        if 'recommendations' not in st.session_state:
            st.session_state.recommendations = None
        if 'provider_config' not in st.session_state:
            st.session_state.provider_config = {
                'provider': 'openai',
                'model': 'gpt-4o',
                'api_key': '',
                'endpoint_url': '',
                'region': 'us-east-1'
            }
        if 'qa_questions' not in st.session_state:
            st.session_state.qa_questions = []
        if 'processing' not in st.session_state:
            st.session_state.processing = False
    
    async def make_api_request(self, method: str, endpoint: str, data: Optional[Dict] = None) -> Dict:
        """Make async API request to FastAPI backend."""
        url = f"{API_BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient(timeout=30.0) as client:
            if method.upper() == "GET":
                response = await client.get(url)
            elif method.upper() == "POST":
                response = await client.post(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 404:
                raise ValueError("Session not found")
            elif response.status_code != 200:
                raise ValueError(f"API error: {response.status_code} - {response.text}")
            
            return response.json()
    
    def render_provider_panel(self):
        """Render the provider selection and configuration panel."""
        st.sidebar.header("🔧 Provider Configuration")
        
        # Provider selection
        provider_options = ["openai", "bedrock", "claude", "internal", "fake"]
        current_provider = st.sidebar.selectbox(
            "LLM Provider",
            provider_options,
            index=provider_options.index(st.session_state.provider_config['provider'])
        )
        
        # Model selection based on provider
        if current_provider == "openai":
            model_options = ["gpt-4o", "gpt-4", "gpt-3.5-turbo", "gpt-4-turbo"]
            api_key = st.sidebar.text_input(
                "OpenAI API Key",
                value=st.session_state.provider_config.get('api_key', ''),
                type="password"
            )
            model = st.sidebar.selectbox("Model", model_options)
            endpoint_url = ""
            region = ""
        
        elif current_provider == "bedrock":
            model_options = ["claude-3-sonnet", "claude-3-haiku"]
            model = st.sidebar.selectbox("Model", model_options)
            region = st.sidebar.selectbox(
                "AWS Region",
                ["us-east-1", "us-west-2", "eu-west-1"],
                index=0
            )
            api_key = ""
            endpoint_url = ""
        
        elif current_provider == "claude":
            model_options = ["claude-3-opus", "claude-3-sonnet"]
            model = st.sidebar.selectbox("Model", model_options)
            api_key = st.sidebar.text_input(
                "Anthropic API Key",
                value=st.session_state.provider_config.get('api_key', ''),
                type="password"
            )
            endpoint_url = ""
            region = ""
        
        elif current_provider == "internal":
            model_options = ["internal-model"]
            model = st.sidebar.selectbox("Model", model_options)
            endpoint_url = st.sidebar.text_input(
                "Endpoint URL",
                value=st.session_state.provider_config.get('endpoint_url', '')
            )
            api_key = ""
            region = ""
        
        else:  # fake
            model_options = ["fake-model"]
            model = st.sidebar.selectbox("Model", model_options)
            api_key = ""
            endpoint_url = ""
            region = ""
            st.sidebar.info("🎭 Using FakeLLM for testing - no API key required")
        
        # Update session state
        st.session_state.provider_config.update({
            'provider': current_provider,
            'model': model,
            'api_key': api_key,
            'endpoint_url': endpoint_url,
            'region': region
        })
        
        # Advanced options (placeholder for future options)
        # with st.sidebar.expander("⚙️ Advanced Options"):
        #     pass
        
        # Test connection button
        if st.sidebar.button("🔍 Test Connection"):
            self.test_provider_connection()
    
    def test_provider_connection(self):
        """Test the current provider configuration."""
        with st.sidebar:
            with st.spinner("Testing connection..."):
                try:
                    config = st.session_state.provider_config
                    response = asyncio.run(self.make_api_request(
                        "POST",
                        "/providers/test",
                        {
                            "provider": config['provider'],
                            "model": config['model'],
                            "api_key": config.get('api_key'),
                            "endpoint_url": config.get('endpoint_url'),
                            "region": config.get('region')
                        }
                    ))
                    
                    if response['ok']:
                        st.success("✅ Connection successful!")
                    else:
                        st.error(f"❌ Connection failed: {response['message']}")
                
                except Exception as e:
                    st.error(f"❌ Error testing connection: {str(e)}")
    
    def render_input_methods(self):
        """Render the input methods section."""
        st.header("📝 Input Requirements")
        
        input_method = st.radio(
            "Choose input method:",
            ["Text Input", "File Upload", "Jira Integration"],
            horizontal=True
        )
        
        if input_method == "Text Input":
            self.render_text_input()
        elif input_method == "File Upload":
            self.render_file_upload()
        else:
            self.render_jira_input()
    
    def render_text_input(self):
        """Render text input interface."""
        col1, col2 = st.columns([2, 1])
        
        with col1:
            requirements_text = st.text_area(
                "Enter your requirements:",
                height=200,
                placeholder="Describe the process or workflow you want to automate..."
            )
        
        with col2:
            domain = st.selectbox(
                "Domain (optional):",
                ["", "finance", "hr", "marketing", "operations", "it", "customer-service"]
            )
            
            pattern_types = st.multiselect(
                "Pattern Types (optional):",
                ["workflow", "data-processing", "integration", "notification", "approval"]
            )
        
        if st.button("🚀 Analyze Requirements", disabled=st.session_state.processing):
            if requirements_text.strip():
                self.submit_requirements("text", {
                    "text": requirements_text,
                    "domain": domain if domain else None,
                    "pattern_types": pattern_types
                })
            else:
                st.error("Please enter some requirements text.")
    
    def render_file_upload(self):
        """Render file upload interface."""
        uploaded_file = st.file_uploader(
            "Upload requirements file:",
            type=['txt', 'docx', 'json', 'csv'],
            help="Supported formats: TXT, DOCX, JSON, CSV"
        )
        
        if uploaded_file is not None:
            st.info(f"File: {uploaded_file.name} ({uploaded_file.size} bytes)")
            
            if st.button("🚀 Analyze File", disabled=st.session_state.processing):
                try:
                    content = uploaded_file.read().decode('utf-8')
                    self.submit_requirements("file", {
                        "content": content,
                        "filename": uploaded_file.name
                    })
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
    
    def render_jira_input(self):
        """Render Jira integration interface."""
        st.subheader("🎫 Jira Integration")
        
        with st.form("jira_form"):
            st.write("**Jira Configuration**")
            
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
        
        # Handle test connection
        if test_connection:
            if not all([jira_base_url, jira_email, jira_api_token]):
                st.error("❌ Please fill in all Jira configuration fields")
            else:
                with st.spinner("Testing Jira connection..."):
                    try:
                        test_result = asyncio.run(self.make_api_request("POST", "/jira/test", {
                            "base_url": jira_base_url,
                            "email": jira_email,
                            "api_token": jira_api_token
                        }))
                        
                        if test_result and test_result.get("ok"):
                            st.success("✅ Jira connection successful!")
                        else:
                            error_msg = test_result.get("message", "Unknown error") if test_result else "Connection failed"
                            st.error(f"❌ Connection failed: {error_msg}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
        
        # Handle fetch ticket
        if fetch_ticket:
            if not all([jira_base_url, jira_email, jira_api_token, jira_ticket_key]):
                st.error("❌ Please fill in all fields including ticket key")
            else:
                with st.spinner(f"Fetching ticket {jira_ticket_key}..."):
                    try:
                        fetch_result = asyncio.run(self.make_api_request("POST", "/jira/fetch", {
                            "ticket_key": jira_ticket_key,
                            "base_url": jira_base_url,
                            "email": jira_email,
                            "api_token": jira_api_token
                        }))
                        
                        if fetch_result:
                            ticket_data = fetch_result.get("ticket_data", {})
                            requirements = fetch_result.get("requirements", {})
                            
                            st.success(f"✅ Successfully fetched ticket: {ticket_data.get('key', 'Unknown')}")
                            
                            # Display ticket preview
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
                                    st.write(ticket_data['description'][:500] + "..." if len(ticket_data.get('description', '')) > 500 else ticket_data.get('description', ''))
                                
                                # Show inferred requirements
                                st.write("**Inferred Requirements:**")
                                if requirements.get('domain'):
                                    st.write(f"- **Domain:** {requirements['domain']}")
                                if requirements.get('pattern_types'):
                                    st.write(f"- **Pattern Types:** {', '.join(requirements['pattern_types'])}")
                        else:
                            st.error("❌ Failed to fetch ticket. Please check your credentials and ticket key.")
                    except Exception as e:
                        st.error(f"❌ Failed to fetch ticket: {str(e)}")
        
        # Handle submit analysis
        if submit_jira:
            if not all([jira_base_url, jira_email, jira_api_token, jira_ticket_key]):
                st.error("❌ Please fill in all fields")
            else:
                with st.spinner("Starting Jira analysis..."):
                    # Use the ingest endpoint with Jira source
                    payload = {
                        "ticket_key": jira_ticket_key,
                        "base_url": jira_base_url,
                        "email": jira_email,
                        "api_token": jira_api_token
                    }
                    
                    # Add provider config if set
                    provider_config = None
                    if hasattr(st.session_state, "provider_config") and st.session_state.provider_config:
                        provider_config = st.session_state.provider_config
                    
                    self.submit_requirements("jira", payload)
    
    def submit_requirements(self, source: str, payload: Dict):
        """Submit requirements to the API."""
        try:
            st.session_state.processing = True
            
            with st.spinner("Submitting requirements..."):
                # Include provider configuration in the request
                request_data = {
                    "source": source, 
                    "payload": payload,
                    "provider_config": st.session_state.provider_config
                }
                
                response = asyncio.run(self.make_api_request(
                    "POST",
                    "/ingest",
                    request_data
                ))
                
                st.session_state.session_id = response['session_id']
                st.session_state.processing = False
                
                # Store requirements in session state for diagram generation
                if source == "text":
                    st.session_state.requirements = {
                        "description": payload.get("text", ""),
                        "domain": payload.get("domain"),
                        "pattern_types": payload.get("pattern_types", [])
                    }
                elif source == "file":
                    st.session_state.requirements = {
                        "description": payload.get("content", ""),
                        "filename": payload.get("filename")
                    }
                elif source == "jira":
                    # For Jira, the payload contains credentials and ticket_key
                    # The actual ticket data will be fetched by the backend
                    st.session_state.requirements = {
                        "description": f"Jira ticket: {payload.get('ticket_key', 'Unknown')}",
                        "jira_key": payload.get("ticket_key"),
                        "source": "jira"
                    }
                
                st.success(f"✅ Requirements submitted! Session ID: {st.session_state.session_id}")
                
                # Start polling for progress
                st.rerun()
        
        except Exception as e:
            st.session_state.processing = False
            st.error(f"❌ Error submitting requirements: {str(e)}")
    
    def render_progress_tracking(self):
        """Render progress tracking section."""
        if not st.session_state.session_id:
            return
        
        st.header("📊 Processing Progress")
        
        try:
            response = asyncio.run(self.make_api_request(
                "GET",
                f"/status/{st.session_state.session_id}"
            ))
            
            phase = response['phase']
            progress = response['progress']
            missing_fields = response.get('missing_fields', [])
            requirements = response.get('requirements', {})
            
            st.session_state.current_phase = phase
            st.session_state.progress = progress
            
            # Update requirements with actual data from backend if available
            if requirements and requirements.get('description'):
                st.session_state.requirements = requirements
            
            # Progress bar
            st.progress(progress / 100, text=f"Phase: {phase} ({progress}%)")
            
            # Phase descriptions
            phase_descriptions = {
                "PARSING": "🔍 Parsing and extracting requirements...",
                "VALIDATING": "✅ Validating input format and content...",
                "QNA": "❓ Asking clarifying questions...",
                "MATCHING": "🎯 Matching against pattern library...",
                "RECOMMENDING": "💡 Generating recommendations...",
                "DONE": "✨ Processing complete!"
            }
            
            st.info(phase_descriptions.get(phase, f"Processing phase: {phase}"))
            
            # Handle Q&A phase
            if phase == "QNA" and missing_fields:
                self.render_qa_section()
            
            # Auto-refresh if not done, but skip for Q&A phase (user-driven)
            if phase != "DONE" and phase != "QNA":
                time.sleep(POLL_INTERVAL)
                st.rerun()
            elif phase == "DONE":
                # Load final results
                self.load_recommendations()
        
        except Exception as e:
            st.error(f"❌ Error getting status: {str(e)}")
    
    def render_qa_section(self):
        """Render Q&A interaction section."""
        st.subheader("❓ Clarifying Questions")
        st.info("Please answer the following questions to improve recommendation accuracy:")
        
        # Load questions from API if not already loaded
        if not st.session_state.qa_questions:
            # Check if we already have questions cached for this session
            questions_cache_key = f"questions_{st.session_state.session_id}"
            if questions_cache_key in st.session_state:
                st.session_state.qa_questions = st.session_state[questions_cache_key]
                st.success(f"✅ Loaded {len(st.session_state.qa_questions)} cached questions")
                return
            
            # Prevent multiple concurrent calls with timestamp check
            generating_timestamp = st.session_state.get('generating_questions_timestamp', 0)
            import time
            current_time = time.time()
            
            if st.session_state.get('generating_questions', False):
                # If it's been more than 30 seconds, assume the previous call failed
                if current_time - generating_timestamp > 30:
                    st.session_state.generating_questions = False
                    st.warning("Previous question generation timed out, retrying...")
                else:
                    st.info("Questions are being generated, please wait...")
                    return
                
            try:
                st.session_state.generating_questions = True
                st.session_state.generating_questions_timestamp = current_time
                st.write(f"**Debug:** Generating questions for session {st.session_state.session_id}")
                with st.spinner("🤖 AI is generating personalized questions for your requirement..."):
                    response = asyncio.run(self.make_api_request(
                        "GET",
                        f"/qa/{st.session_state.session_id}/questions"
                    ))
                    questions = response.get('questions', [])
                    if questions:
                        st.session_state.qa_questions = questions
                        # Cache the questions to prevent regeneration
                        st.session_state[questions_cache_key] = questions
                        st.success(f"✅ Generated {len(questions)} questions")
                    else:
                        st.info("No additional questions needed - proceeding to analysis...")
                        return
            except Exception as e:
                st.error(f"❌ Error loading questions: {str(e)}")
                # Fallback to basic questions
                st.session_state.qa_questions = [
                    {
                        "id": "physical_vs_digital",
                        "question": "Does this process involve physical objects or digital/virtual entities?",
                        "type": "text"
                    },
                    {
                        "id": "current_process",
                        "question": "How is this process currently performed?",
                        "type": "text"
                    }
                ]
                st.warning("Using fallback questions due to error")
            finally:
                st.session_state.generating_questions = False
        
        # Show questions if we have them
        if st.session_state.qa_questions:
            answers = {}
            for idx, q in enumerate(st.session_state.qa_questions):
                # Create unique key using index and question hash to prevent Streamlit key conflicts
                # This handles cases where multiple questions might have the same field ID
                unique_key = f"qa_{idx}_{hash(q['question'])}"
                
                if q["type"] == "text":
                    answers[q["id"]] = st.text_input(q["question"], key=unique_key)
                elif q["type"] == "select":
                    answers[q["id"]] = st.selectbox(q["question"], q["options"], key=unique_key)
            
            # Check if all questions are answered
            answered_count = sum(1 for answer in answers.values() if answer and answer.strip())
            total_questions = len(st.session_state.qa_questions)
            
            st.write(f"📝 Answered: {answered_count}/{total_questions} questions")
            
            # Submit button
            col1, col2, col3 = st.columns([1, 2, 1])
            with col2:
                if st.button("🚀 Submit Answers", type="primary", use_container_width=True):
                    if answered_count == 0:
                        st.warning("Please answer at least one question before submitting.")
                    else:
                        # Clear questions cache when submitting answers
                        questions_cache_key = f"questions_{st.session_state.session_id}"
                        if questions_cache_key in st.session_state:
                            del st.session_state[questions_cache_key]
                        self.submit_qa_answers(answers)
    
    def submit_qa_answers(self, answers: Dict[str, str]):
        """Submit Q&A answers to the API."""
        try:
            with st.spinner("Processing answers..."):
                response = asyncio.run(self.make_api_request(
                    "POST",
                    f"/qa/{st.session_state.session_id}",
                    {"answers": answers}
                ))
                
                if response['complete']:
                    st.success("✅ All questions answered! Proceeding to matching...")
                    st.session_state.qa_questions = []
                    # Force a status refresh to pick up the phase change
                    st.session_state.phase = None  # Clear cached phase
                else:
                    st.info("Additional questions may be needed...")
                    # Update questions if provided
                    if response.get('next_questions'):
                        st.session_state.qa_questions = response['next_questions']
                
                st.rerun()
        
        except Exception as e:
            st.error(f"❌ Error submitting answers: {str(e)}")
    
    def load_recommendations(self):
        """Load and display final recommendations."""
        if st.session_state.recommendations is None:
            try:
                response = asyncio.run(self.make_api_request(
                    "POST",
                    "/recommend",
                    {"session_id": st.session_state.session_id, "top_k": 3}
                ))
                st.session_state.recommendations = response
            except Exception as e:
                st.error(f"❌ Error loading recommendations: {str(e)}")
                return
        
        self.render_results()
    
    def render_results(self):
        """Render the results section with feasibility and recommendations."""
        if not st.session_state.recommendations:
            return
        
        st.header("🎯 Results & Recommendations")
        
        # Show original requirements
        if st.session_state.get('requirements'):
            with st.expander("📋 Original Requirements", expanded=False):
                req = st.session_state.requirements
                
                if req.get('description'):
                    st.write(f"**Description:** {req['description']}")
                
                if req.get('domain'):
                    st.write(f"**Domain:** {req['domain']}")
                
                if req.get('pattern_types'):
                    st.write(f"**Pattern Types:** {', '.join(req['pattern_types'])}")
                
                if req.get('jira_key'):
                    st.write(f"**Jira Ticket:** {req['jira_key']}")
                
                if req.get('filename'):
                    st.write(f"**Source File:** {req['filename']}")
                
                # Show any additional requirement fields
                for key, value in req.items():
                    if key not in ['description', 'domain', 'pattern_types', 'jira_key', 'filename', 'source'] and value:
                        st.write(f"**{key.replace('_', ' ').title()}:** {value}")
            
            st.markdown("---")
        
        rec = st.session_state.recommendations
        
        # Overall feasibility with better display
        feasibility = rec['feasibility']
        feasibility_info = {
            "Yes": {"color": "🟢", "label": "Fully Automatable", "desc": "This requirement can be completely automated with high confidence."},
            "Partial": {"color": "🟡", "label": "Partially Automatable", "desc": "This requirement can be mostly automated, but may need human oversight for some steps."},
            "No": {"color": "🔴", "label": "Not Automatable", "desc": "This requirement is not suitable for automation at this time."},
            "Automatable": {"color": "🟢", "label": "Fully Automatable", "desc": "This requirement can be completely automated with high confidence."},
            "Partially Automatable": {"color": "🟡", "label": "Partially Automatable", "desc": "This requirement can be mostly automated, but may need human oversight for some steps."},
            "Not Automatable": {"color": "🔴", "label": "Not Automatable", "desc": "This requirement is not suitable for automation at this time."}
        }
        
        feas_info = feasibility_info.get(feasibility, {"color": "⚪", "label": feasibility, "desc": "Assessment pending."})
        
        st.subheader(f"{feas_info['color']} Feasibility: {feas_info['label']}")
        st.write(feas_info['desc'])
        
        # Solution Overview
        if rec.get('recommendations') and len(rec['recommendations']) > 0:
            st.subheader("💡 Recommended Solution")
            
            # Get the best recommendation for solution overview
            best_rec = rec['recommendations'][0]
            
            # Generate solution explanation
            solution_explanation = self._generate_solution_explanation(best_rec, rec)
            st.write(solution_explanation)
            
            # Debug: Show what LLM analysis we have
            session_requirements = st.session_state.get('requirements', {})
            if session_requirements.get('llm_analysis_automation_feasibility'):
                with st.expander("🔍 Debug: LLM Analysis", expanded=False):
                    st.write("**LLM Feasibility:**", session_requirements.get('llm_analysis_automation_feasibility'))
                    st.write("**LLM Reasoning:**", session_requirements.get('llm_analysis_feasibility_reasoning'))
                    st.write("**LLM Confidence:**", session_requirements.get('llm_analysis_confidence_level'))
        
        # Tech stack with explanations
        if rec.get('tech_stack'):
            st.subheader("🛠️ Recommended Tech Stack")
            
            # Generate and show LLM-enhanced tech stack with explanations
            enhanced_tech_stack, architecture_explanation = asyncio.run(self._generate_llm_tech_stack_and_explanation(rec['tech_stack']))
            self._render_tech_stack_explanation(enhanced_tech_stack)
            
            # Show architecture explanation
            st.subheader("🏗️ How It All Works Together")
            st.write(architecture_explanation)
        
        # Detailed reasoning
        if rec.get('reasoning'):
            st.subheader("💭 Technical Analysis")
            with st.expander("View detailed technical reasoning", expanded=False):
                st.write(rec['reasoning'])
        
        # Individual recommendations
        if rec.get('recommendations'):
            st.subheader("📋 Pattern Matches")
            
            for i, recommendation in enumerate(rec['recommendations']):
                with st.expander(f"Pattern {i+1}: {recommendation.get('pattern_id', 'Unknown')}"):
                    col1, col2 = st.columns([3, 1])
                    
                    with col1:
                        st.write(f"**Confidence:** {recommendation.get('confidence', 0):.2%}")
                        if recommendation.get('reasoning'):
                            st.write(f"**Rationale:** {recommendation['reasoning']}")
                    
                    with col2:
                        feasibility_badge = recommendation.get('feasibility', 'Unknown')
                        st.metric("Feasibility", feasibility_badge)
        
        # Export buttons
        self.render_export_buttons()
    
    def _generate_solution_explanation(self, best_recommendation: Dict, overall_rec: Dict) -> str:
        """Generate a user-friendly solution explanation using actual recommendation data."""
        # Use the detailed reasoning from the recommendation service if available
        reasoning = best_recommendation.get('reasoning', '')
        if reasoning:
            # The reasoning already contains comprehensive analysis, use it directly
            return reasoning
        
        # Fallback to pattern-based explanation if no reasoning available
        feasibility = overall_rec.get('feasibility', 'Unknown')
        confidence = best_recommendation.get('confidence', 0)
        pattern_id = best_recommendation.get('pattern_id', 'Unknown')
        
        # Create more specific explanation based on pattern and feasibility
        pattern_name = best_recommendation.get('pattern_name', 'automation pattern')
        
        if feasibility in ["Yes", "Automatable"]:
            base_explanation = f"Based on the '{pattern_name}' pattern, this solution can be fully automated. "
            if confidence > 0.8:
                confidence_text = "We have high confidence in this approach based on similar successful implementations. "
            elif confidence > 0.6:
                confidence_text = "This approach has been validated in similar scenarios, though some customization may be needed. "
            else:
                confidence_text = "This approach would require careful planning and possibly a proof-of-concept phase. "
            
            implementation = "The system would integrate with your existing tools, process data automatically, and provide real-time monitoring and alerts."
            
        elif feasibility in ["Partial", "Partially Automatable"]:
            base_explanation = f"Using the '{pattern_name}' pattern, this solution can be partially automated. "
            confidence_text = "The automated components would handle routine tasks while keeping humans in the loop for critical decisions. "
            implementation = "This hybrid approach balances efficiency with necessary human oversight and control."
            
        else:  # No or Not Automatable
            base_explanation = f"While the '{pattern_name}' pattern provides some guidance, full automation isn't recommended for this use case. "
            confidence_text = "However, there are opportunities to improve manual processes with better tooling and workflows. "
            implementation = "The focus would be on providing better tools and dashboards to make manual processes more efficient."
        
        return base_explanation + confidence_text + implementation
    
    def _render_tech_stack_explanation(self, tech_stack: List[str]):
        """Render tech stack with explanations of how components work together."""
        if not tech_stack:
            return
        
        # Categorize technologies
        categories = {
            "Backend/API": ["Python", "FastAPI", "Flask", "Django", "Node.js", "Express"],
            "Database": ["PostgreSQL", "MySQL", "MongoDB", "SQLAlchemy", "Redis"],
            "Message Queue": ["Celery", "RabbitMQ", "Apache Kafka", "AWS SQS"],
            "Cloud/Infrastructure": ["Docker", "Kubernetes", "AWS", "Azure", "GCP"],
            "Monitoring": ["Prometheus", "Grafana", "ELK Stack", "DataDog"],
            "Security": ["cryptography", "OAuth2", "JWT", "SSL/TLS"],
            "Integration": ["httpx", "requests", "Webhook", "REST API"],
            "Frontend": ["React", "Vue.js", "Streamlit", "HTML/CSS/JS"]
        }
        
        # Group technologies by category
        categorized_tech = {}
        uncategorized = []
        
        for tech in tech_stack:
            found_category = None
            for category, techs in categories.items():
                if any(t.lower() in tech.lower() or tech.lower() in t.lower() for t in techs):
                    found_category = category
                    break
            
            if found_category:
                if found_category not in categorized_tech:
                    categorized_tech[found_category] = []
                categorized_tech[found_category].append(tech)
            else:
                uncategorized.append(tech)
        
        # Display categorized tech stack
        for category, techs in categorized_tech.items():
            with st.expander(f"{category} ({len(techs)} technologies)", expanded=True):
                cols = st.columns(min(len(techs), 3))
                for i, tech in enumerate(techs):
                    with cols[i % 3]:
                        st.info(f"**{tech}**")
                
                # Add category explanation
                explanations = {
                    "Backend/API": "Handles business logic, data processing, and provides APIs for integration.",
                    "Database": "Stores and manages data with reliability and performance optimization.",
                    "Message Queue": "Enables asynchronous processing and reliable communication between components.",
                    "Cloud/Infrastructure": "Provides scalable hosting, deployment, and infrastructure management.",
                    "Monitoring": "Tracks system performance, errors, and provides operational insights.",
                    "Security": "Ensures data protection, authentication, and secure communications.",
                    "Integration": "Connects with external systems and APIs for data exchange.",
                    "Frontend": "Provides user interfaces for monitoring and manual interventions."
                }
                
                if category in explanations:
                    st.write(f"*{explanations[category]}*")
        
        # Show uncategorized technologies
        if uncategorized:
            with st.expander(f"Additional Technologies ({len(uncategorized)})", expanded=True):
                cols = st.columns(min(len(uncategorized), 4))
                for i, tech in enumerate(uncategorized):
                    with cols[i % 4]:
                        st.info(tech)
        
        # Architecture explanation is now handled in the main recommendation display
    
    async def _generate_llm_architecture_explanation(self, tech_stack: List[str]) -> str:
        """Generate LLM-driven explanation of how the tech stack components work together."""
        try:
            # Import here to avoid circular imports
            from app.services.architecture_explainer import ArchitectureExplainer
            from app.api import create_llm_provider
            
            # Get current session requirements for context
            requirements = st.session_state.get('requirements', {})
            session_id = st.session_state.get('session_id', 'unknown')
            
            # Create LLM provider
            provider_config_dict = st.session_state.get('provider_config')
            llm_provider = None
            
            if provider_config_dict:
                try:
                    # Import ProviderConfig here to avoid circular imports
                    from app.api import ProviderConfig
                    
                    # Convert dict to ProviderConfig model
                    provider_config = ProviderConfig(**provider_config_dict)
                    llm_provider = create_llm_provider(provider_config, session_id)
                except Exception as e:
                    st.warning(f"Could not create LLM provider for architecture explanation: {e}")
            
            # Create architecture explainer
            explainer = ArchitectureExplainer(llm_provider)
            
            # Generate explanation (now returns tuple)
            enhanced_tech_stack, explanation = await explainer.explain_architecture(tech_stack, requirements, session_id)
            return explanation
            
        except Exception as e:
            st.error(f"Failed to generate architecture explanation: {e}")
            return self._generate_fallback_architecture_explanation(tech_stack)
    
    def _generate_fallback_architecture_explanation(self, tech_stack: List[str]) -> str:
        """Generate fallback architecture explanation when LLM fails."""
        if not tech_stack:
            return "No technology stack specified for this recommendation."
        
        return (f"This technology stack combines {', '.join(tech_stack[:3])} "
                f"{'and others ' if len(tech_stack) > 3 else ''}"
                f"to create a comprehensive automation solution. "
                f"The components work together to handle data processing, "
                f"system integration, and monitoring requirements.")
    
    async def _generate_llm_tech_stack_and_explanation(self, original_tech_stack: List[str]) -> tuple[List[str], str]:
        """Generate LLM-driven tech stack and explanation based on requirements."""
        # Check if we already have cached results for this session
        session_id = st.session_state.get('session_id', 'unknown')
        cache_key = f"llm_tech_stack_{session_id}"
        
        if cache_key in st.session_state:
            from app.utils.logger import app_logger
            app_logger.info("Using cached LLM tech stack and explanation")
            return st.session_state[cache_key]
        
        try:
            # Import here to avoid circular imports
            from app.services.architecture_explainer import ArchitectureExplainer
            from app.api import create_llm_provider
            
            # Get session requirements for context
            requirements = st.session_state.get('requirements', {})
            session_id = st.session_state.get('session_id', 'unknown')
            
            # Create LLM provider if available
            llm_provider = None
            provider_config_dict = st.session_state.get('provider_config')
            if provider_config_dict and provider_config_dict.get('api_key'):
                try:
                    from app.api import ProviderConfig
                    
                    # Convert dict to ProviderConfig model
                    provider_config = ProviderConfig(**provider_config_dict)
                    llm_provider = create_llm_provider(provider_config, session_id)
                except Exception as e:
                    st.warning(f"Could not create LLM provider for tech stack generation: {e}")
            
            # Create architecture explainer
            explainer = ArchitectureExplainer(llm_provider)
            
            # Generate both tech stack and explanation
            enhanced_tech_stack, explanation = await explainer.explain_architecture(original_tech_stack, requirements, session_id)
            
            # Cache the results
            result = (enhanced_tech_stack, explanation)
            st.session_state[cache_key] = result
            
            return result
            
        except Exception as e:
            st.error(f"Failed to generate tech stack and explanation: {e}")
            return original_tech_stack, self._generate_fallback_architecture_explanation(original_tech_stack)
    
    def render_export_buttons(self):
        """Render export functionality."""
        st.subheader("📤 Export Results")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button("📄 Export as JSON"):
                self.export_results("json")
        
        with col2:
            if st.button("📝 Export as Markdown"):
                self.export_results("md")
    
    def export_results(self, format_type: str):
        """Export results in the specified format."""
        try:
            with st.spinner(f"Exporting as {format_type.upper()}..."):
                response = asyncio.run(self.make_api_request(
                    "POST",
                    "/export",
                    {
                        "session_id": st.session_state.session_id,
                        "format": format_type
                    }
                ))
                
                st.success(f"✅ Export successful!")
                st.info(f"**File:** {response['file_path']}")
                
                # Show download button
                if response.get('download_url'):
                    # Read the file content for download
                    try:
                        import requests
                        # Construct full URL for the API request
                        api_base = "http://localhost:8000"
                        download_url = response['download_url']
                        if not download_url.startswith('http'):
                            download_url = f"{api_base}{download_url}"
                        
                        file_response = requests.get(download_url)
                        if file_response.status_code == 200:
                            file_content = file_response.content
                            filename = response['file_path'].split('/')[-1]
                            
                            st.download_button(
                                label="📥 Download File",
                                data=file_content,
                                file_name=filename,
                                mime="application/octet-stream"
                            )
                        else:
                            st.markdown(f"[📥 Download File]({download_url})")
                    except Exception as e:
                        st.warning(f"Could not create download button: {e}")
                        # Fallback to direct link
                        download_url = response['download_url']
                        if not download_url.startswith('http'):
                            download_url = f"http://localhost:8000{download_url}"
                        st.markdown(f"[📥 Download File]({download_url})")
        
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
    
    def render_mermaid_diagrams(self):
        """Render Mermaid diagrams panel."""
        st.header("📊 System Diagrams")
        
        # Check if we have session data
        if not st.session_state.get('session_id'):
            st.info("Please submit a requirement first to generate diagrams.")
            return
        
        diagram_type = st.selectbox(
            "Select diagram type:",
            ["Context Diagram", "Container Diagram", "Sequence Diagram"]
        )
        
        # Get current session data
        requirements = st.session_state.get('requirements', {})
        recommendations_response = st.session_state.get('recommendations', {})
        provider_config = st.session_state.get('provider_config', {})
        
        # Extract recommendations list from the API response
        recommendations = recommendations_response.get('recommendations', []) if recommendations_response else []
        
        # Debug info
        st.write("**Debug Info:**")
        st.write(f"- Session ID: {st.session_state.get('session_id', 'None')}")
        st.write(f"- Requirements keys: {list(requirements.keys()) if requirements else 'None'}")
        st.write(f"- Recommendations count: {len(recommendations)}")
        st.write(f"- Provider: {provider_config.get('provider', 'None')}")
        st.write(f"- API Key present: {bool(provider_config.get('api_key'))}")
        
        requirement_text = requirements.get('description', 'No requirement available')
        
        if st.button(f"Generate {diagram_type}", type="primary"):
            try:
                # Additional validation
                if not requirement_text or requirement_text == 'No requirement available':
                    st.error("No requirement found. Please submit a requirement first.")
                    return
                
                if not provider_config.get('api_key'):
                    st.error("No API key found. Please configure your provider in the sidebar.")
                    return
                
                st.write(f"**Generating diagram for:** {requirement_text[:100]}...")
                
                with st.spinner(f"🤖 Generating {diagram_type.lower()} using AI..."):
                    if diagram_type == "Context Diagram":
                        mermaid_code = asyncio.run(build_context_diagram(requirement_text, recommendations))
                    elif diagram_type == "Container Diagram":
                        mermaid_code = asyncio.run(build_container_diagram(requirement_text, recommendations))
                    else:  # Sequence Diagram
                        mermaid_code = asyncio.run(build_sequence_diagram(requirement_text, recommendations))
                    
                    # Store the generated diagram
                    st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                    st.success("✅ Diagram generated successfully!")
                    
            except Exception as e:
                st.error(f"❌ Error generating diagram: {str(e)}")
                st.write(f"**Error details:** {type(e).__name__}: {str(e)}")
                return
        
        # Display the diagram if we have one
        diagram_key = f'{diagram_type.lower().replace(" ", "_")}_code'
        if diagram_key in st.session_state:
            mermaid_code = st.session_state[diagram_key]
            # Display Mermaid diagram
            self.render_mermaid(mermaid_code)
            
            # Show code
            with st.expander("View Mermaid Code"):
                st.code(mermaid_code, language="mermaid")
    
    def render_mermaid(self, mermaid_code: str):
        """Render a Mermaid diagram with better viewing options."""
        import hashlib
        diagram_id = hashlib.md5(mermaid_code.encode()).hexdigest()[:8]
        
        # Store diagram in session state
        if f"diagram_{diagram_id}" not in st.session_state:
            st.session_state[f"diagram_{diagram_id}"] = mermaid_code
        
        # Control buttons
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col2:
            if st.button("🔍 Large View", key=f"expand_{diagram_id}"):
                st.session_state[f"show_large_{diagram_id}"] = not st.session_state.get(f"show_large_{diagram_id}", False)
        
        with col3:
            if st.button("🌐 Open in Browser", key=f"browser_{diagram_id}"):
                self.open_diagram_in_browser(mermaid_code, diagram_id)
        
        with col4:
            if st.button("📋 Show Code", key=f"code_{diagram_id}"):
                st.session_state[f"show_code_{diagram_id}"] = not st.session_state.get(f"show_code_{diagram_id}", False)
        
        # Check if we should show large view
        show_large = st.session_state.get(f"show_large_{diagram_id}", False)
        
        if show_large:
            st.write("**🔍 Large View Mode** - Click 'Large View' again to return to normal size")
            
            # Use streamlit-mermaid if available, otherwise fallback to HTML
            try:
                import streamlit_mermaid as stmd
                stmd.st_mermaid(mermaid_code, height="800px")
            except ImportError:
                # Fallback to improved HTML rendering
                large_html = f"""
                <div style="width: 100%; height: 800px; border: 2px solid #4CAF50; border-radius: 12px; padding: 20px; background: white; overflow: auto;">
                    <div class="mermaid" style="width: 100%; height: 100%; font-size: 16px;">
                        {mermaid_code}
                    </div>
                </div>
                
                <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{
                        startOnLoad: true,
                        theme: 'default',
                        themeVariables: {{
                            fontSize: '16px',
                            fontFamily: 'Arial, sans-serif',
                            primaryColor: '#4CAF50',
                            primaryTextColor: '#333',
                            primaryBorderColor: '#4CAF50'
                        }},
                        flowchart: {{
                            useMaxWidth: false,
                            htmlLabels: true,
                            nodeSpacing: 80,
                            rankSpacing: 80
                        }},
                        sequence: {{
                            useMaxWidth: false,
                            boxMargin: 20,
                            actorMargin: 60
                        }}
                    }});
                </script>
                """
                html(large_html, height=850)
        else:
            # Regular view with better sizing
            try:
                import streamlit_mermaid as stmd
                stmd.st_mermaid(mermaid_code, height="400px")
            except ImportError:
                # Fallback to HTML
                regular_html = f"""
                <div style="width: 100%; height: 400px; border: 2px solid #e0e0e0; border-radius: 8px; padding: 15px; background: white; overflow: auto;">
                    <div class="mermaid" style="width: 100%; height: 100%; font-size: 14px;">
                        {mermaid_code}
                    </div>
                </div>
                
                <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
                <script>
                    mermaid.initialize({{
                        startOnLoad: true,
                        theme: 'default',
                        flowchart: {{ useMaxWidth: true }},
                        sequence: {{ useMaxWidth: true }}
                    }});
                </script>
                """
                html(regular_html, height=450)
        
        # Show code and download options
        if st.session_state.get(f"show_code_{diagram_id}", False):
            st.write("**📋 Mermaid Code:**")
            st.code(mermaid_code, language="mermaid")
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.download_button(
                    label="💾 Download Code (.mmd)",
                    data=mermaid_code,
                    file_name=f"diagram_{diagram_id}.mmd",
                    mime="text/plain",
                    key=f"download_mmd_{diagram_id}"
                )
            
            with col2:
                # Create HTML file for standalone viewing
                html_content = self.create_standalone_html(mermaid_code, diagram_id)
                st.download_button(
                    label="🌐 Download HTML",
                    data=html_content,
                    file_name=f"diagram_{diagram_id}.html",
                    mime="text/html",
                    key=f"download_html_{diagram_id}"
                )
            
            with col3:
                # Link to Mermaid Live Editor
                import urllib.parse
                encoded_code = urllib.parse.quote(mermaid_code)
                mermaid_live_url = f"https://mermaid.live/edit#{encoded_code}"
                st.markdown(f"[🔗 Open in Mermaid Live]({mermaid_live_url})", unsafe_allow_html=True)
    
    def open_diagram_in_browser(self, mermaid_code: str, diagram_id: str):
        """Create and save a standalone HTML file for the diagram."""
        html_content = self.create_standalone_html(mermaid_code, diagram_id)
        
        # Save to exports directory
        import os
        os.makedirs("exports", exist_ok=True)
        file_path = f"exports/diagram_{diagram_id}.html"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        st.success(f"✅ Diagram saved to `{file_path}` - Open this file in your browser for full-size viewing!")
        
        # Show the file path as copyable text
        st.code(f"open {file_path}", language="bash")
    
    def create_standalone_html(self, mermaid_code: str, diagram_id: str) -> str:
        """Create a standalone HTML file for viewing the diagram."""
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Architecture Diagram - {diagram_id}</title>
    <script src="https://cdn.jsdelivr.net/npm/mermaid@10/dist/mermaid.min.js"></script>
    <style>
        body {{
            font-family: Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .container {{
            max-width: 100%;
            background: white;
            border-radius: 12px;
            padding: 30px;
            box-shadow: 0 4px 12px rgba(0,0,0,0.1);
            overflow: auto;
        }}
        .mermaid {{
            width: 100%;
            min-height: 600px;
            font-size: 16px;
        }}
        .header {{
            text-align: center;
            margin-bottom: 30px;
            color: #333;
        }}
        .controls {{
            text-align: center;
            margin-bottom: 20px;
        }}
        .btn {{
            background: #4CAF50;
            color: white;
            border: none;
            padding: 10px 20px;
            border-radius: 5px;
            cursor: pointer;
            margin: 0 10px;
            font-size: 14px;
        }}
        .btn:hover {{
            background: #45a049;
        }}
        .code-section {{
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }}
        .code-section pre {{
            background: #2d3748;
            color: #e2e8f0;
            padding: 15px;
            border-radius: 5px;
            overflow-x: auto;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🏗️ Architecture Diagram</h1>
            <p>Generated by Automated AI Assessment (AAA)</p>
        </div>
        
        <div class="controls">
            <button class="btn" onclick="toggleCode()">📋 Toggle Code</button>
            <button class="btn" onclick="downloadSVG()">💾 Download SVG</button>
            <button class="btn" onclick="window.print()">🖨️ Print</button>
        </div>
        
        <div class="mermaid" id="diagram">
{mermaid_code}
        </div>
        
        <div class="code-section" id="codeSection">
            <h3>Mermaid Code:</h3>
            <pre><code>{mermaid_code}</code></pre>
        </div>
    </div>

    <script>
        mermaid.initialize({{
            startOnLoad: true,
            theme: 'default',
            themeVariables: {{
                fontSize: '16px',
                fontFamily: 'Arial, sans-serif',
                primaryColor: '#4CAF50',
                primaryTextColor: '#333',
                primaryBorderColor: '#4CAF50',
                lineColor: '#666',
                secondaryColor: '#f8f9fa',
                tertiaryColor: '#ffffff'
            }},
            flowchart: {{
                useMaxWidth: false,
                htmlLabels: true,
                curve: 'basis',
                nodeSpacing: 100,
                rankSpacing: 100
            }},
            sequence: {{
                useMaxWidth: false,
                boxMargin: 30,
                actorMargin: 80,
                messageMargin: 60
            }}
        }});
        
        function toggleCode() {{
            const codeSection = document.getElementById('codeSection');
            codeSection.style.display = codeSection.style.display === 'none' ? 'block' : 'none';
        }}
        
        function downloadSVG() {{
            const svg = document.querySelector('#diagram svg');
            if (svg) {{
                const svgData = new XMLSerializer().serializeToString(svg);
                const svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                const svgUrl = URL.createObjectURL(svgBlob);
                const downloadLink = document.createElement('a');
                downloadLink.href = svgUrl;
                downloadLink.download = 'diagram_{diagram_id}.svg';
                document.body.appendChild(downloadLink);
                downloadLink.click();
                document.body.removeChild(downloadLink);
            }}
        }}
    </script>
</body>
</html>"""
    

    
    def render_observability_dashboard(self):
        """Render the observability dashboard with metrics and analytics."""
        st.header("📈 System Observability")
        
        # Show info message if no session is active
        if not st.session_state.session_id:
            st.info("💡 Start an analysis in the Analysis tab to see observability data here.")
            return
        
        # Dashboard tabs
        metrics_tab, patterns_tab, usage_tab, messages_tab, admin_tab = st.tabs(["🔧 Provider Metrics", "🎯 Pattern Analytics", "📊 Usage Patterns", "💬 LLM Messages", "🧹 Admin"])
        
        with metrics_tab:
            self.render_provider_metrics()
        
        with patterns_tab:
            self.render_pattern_analytics()
        
        with usage_tab:
            self.render_usage_patterns()
        
        with messages_tab:
            self.render_llm_messages()
        
        with admin_tab:
            self.render_observability_admin()
    
    def render_provider_metrics(self):
        """Render LLM provider performance metrics."""
        st.subheader("🔧 LLM Provider Performance")
        
        # Add filtering options
        col1, col2, col3 = st.columns(3)
        with col1:
            time_filter = st.selectbox("Time Period", 
                                     ["All Time", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
                                     index=1)  # Default to last 24 hours
        with col2:
            show_test_providers = st.checkbox("Include Test/Mock Providers", value=False)
        with col3:
            current_session_only = st.checkbox("Current Session Only", value=False)
        
        try:
            # Fetch provider statistics with filters
            provider_stats = asyncio.run(self.get_provider_statistics(
                time_filter=time_filter,
                include_test_providers=show_test_providers,
                current_session_only=current_session_only
            ))
            
            if not provider_stats or not provider_stats.get('provider_stats'):
                st.info("💡 No provider metrics available for the selected filters. Try expanding the time period or including test providers.")
                return
            
            stats = provider_stats['provider_stats']
            
            # Provider comparison metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("📊 Call Volume by Provider")
                
                # Create call volume chart data
                providers = [f"{stat['provider']}/{stat['model']}" for stat in stats]
                call_counts = [stat['call_count'] for stat in stats]
                
                if providers and call_counts and any(count > 0 for count in call_counts):
                    chart_data = {
                        'Provider/Model': providers,
                        'Call Count': call_counts
                    }
                    st.bar_chart(chart_data, x='Provider/Model', y='Call Count')
                else:
                    st.info("No call data available")
            
            with col2:
                st.subheader("⚡ Average Latency by Provider")
                
                # Create latency chart data
                latencies = [stat['avg_latency'] for stat in stats]
                
                if providers and latencies and any(lat > 0 for lat in latencies):
                    chart_data = {
                        'Provider/Model': providers,
                        'Avg Latency (ms)': latencies
                    }
                    st.bar_chart(chart_data, x='Provider/Model', y='Avg Latency (ms)')
                else:
                    st.info("No latency data available")
            
            # Detailed metrics table
            st.subheader("📋 Detailed Provider Metrics")
            
            # Format data for display
            display_data = []
            for stat in stats:
                display_data.append({
                    'Provider': stat['provider'],
                    'Model': stat['model'],
                    'Calls': stat['call_count'],
                    'Avg Latency (ms)': f"{stat['avg_latency']:.1f}",
                    'Min Latency (ms)': stat['min_latency'],
                    'Max Latency (ms)': stat['max_latency'],
                    'Total Tokens': stat['total_tokens']
                })
            
            if display_data:
                st.dataframe(display_data, use_container_width=True)
            
            # Performance insights
            st.subheader("💡 Performance Insights")
            
            if len(stats) > 1:
                # Find fastest and slowest providers
                fastest = min(stats, key=lambda x: x['avg_latency'])
                slowest = max(stats, key=lambda x: x['avg_latency'])
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "🏆 Fastest Provider",
                        f"{fastest['provider']}/{fastest['model']}",
                        f"{fastest['avg_latency']:.1f}ms avg"
                    )
                
                with col2:
                    st.metric(
                        "🐌 Slowest Provider", 
                        f"{slowest['provider']}/{slowest['model']}",
                        f"{slowest['avg_latency']:.1f}ms avg"
                    )
                
                with col3:
                    total_calls = sum(stat['call_count'] for stat in stats)
                    st.metric("📞 Total API Calls", total_calls)
            
        except Exception as e:
            st.error(f"❌ Error loading provider metrics: {str(e)}")
    
    def render_pattern_analytics(self):
        """Render pattern matching analytics."""
        st.subheader("🎯 Pattern Matching Analytics")
        
        try:
            # Fetch pattern statistics from audit data
            pattern_stats = asyncio.run(self.get_pattern_statistics())
            
            if not pattern_stats or not pattern_stats.get('pattern_stats'):
                st.info("No pattern analytics available yet. Run some analyses to see pattern matching data.")
                return
            
            stats = pattern_stats['pattern_stats']
            
            # Pattern performance metrics
            col1, col2 = st.columns(2)
            
            with col1:
                st.subheader("🎯 Pattern Match Frequency")
                
                # Create pattern frequency chart
                patterns = [stat['pattern_id'] for stat in stats[:10]]  # Top 10
                match_counts = [stat['match_count'] for stat in stats[:10]]
                
                if patterns and match_counts and any(count > 0 for count in match_counts):
                    chart_data = {
                        'Pattern ID': patterns,
                        'Match Count': match_counts
                    }
                    st.bar_chart(chart_data, x='Pattern ID', y='Match Count')
                else:
                    st.info("No pattern match data available")
            
            with col2:
                st.subheader("✅ Pattern Acceptance Rates")
                
                # Create acceptance rate chart
                acceptance_rates = [stat['acceptance_rate'] * 100 for stat in stats[:10]]
                
                if patterns and acceptance_rates and any(rate >= 0 for rate in acceptance_rates):
                    chart_data = {
                        'Pattern ID': patterns,
                        'Acceptance Rate (%)': acceptance_rates
                    }
                    st.bar_chart(chart_data, x='Pattern ID', y='Acceptance Rate (%)')
                else:
                    st.info("No acceptance rate data available")
            
            # Pattern quality metrics
            st.subheader("📊 Pattern Quality Metrics")
            
            # Format data for display
            display_data = []
            for stat in stats:
                display_data.append({
                    'Pattern ID': stat['pattern_id'],
                    'Matches': stat['match_count'],
                    'Avg Score': f"{stat['avg_score']:.3f}",
                    'Min Score': f"{stat['min_score']:.3f}",
                    'Max Score': f"{stat['max_score']:.3f}",
                    'Accepted': stat['accepted_count'],
                    'Acceptance Rate': f"{stat['acceptance_rate']:.1%}"
                })
            
            if display_data:
                st.dataframe(display_data, use_container_width=True)
            
            # Pattern insights
            st.subheader("💡 Pattern Insights")
            
            if len(stats) > 0:
                # Find best and worst performing patterns
                best_pattern = max(stats, key=lambda x: x['acceptance_rate'])
                most_used = max(stats, key=lambda x: x['match_count'])
                highest_score = max(stats, key=lambda x: x['avg_score'])
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "🏆 Best Acceptance Rate",
                        best_pattern['pattern_id'],
                        f"{best_pattern['acceptance_rate']:.1%}"
                    )
                
                with col2:
                    st.metric(
                        "🔥 Most Used Pattern",
                        most_used['pattern_id'],
                        f"{most_used['match_count']} matches"
                    )
                
                with col3:
                    st.metric(
                        "⭐ Highest Avg Score",
                        highest_score['pattern_id'],
                        f"{highest_score['avg_score']:.3f}"
                    )
            
        except Exception as e:
            st.error(f"❌ Error loading pattern analytics: {str(e)}")
    
    def render_usage_patterns(self):
        """Render usage pattern analysis."""
        st.subheader("📊 Usage Pattern Analysis")
        
        try:
            # Get both provider and pattern stats for usage analysis
            provider_stats = asyncio.run(self.get_provider_statistics())
            pattern_stats = asyncio.run(self.get_pattern_statistics())
            
            if not provider_stats and not pattern_stats:
                st.info("No usage data available yet. Run some analyses to see usage patterns.")
                return
            
            # Usage overview
            col1, col2, col3 = st.columns(3)
            
            total_calls = 0
            total_patterns = 0
            total_tokens = 0
            
            if provider_stats and provider_stats.get('provider_stats'):
                total_calls = sum(stat['call_count'] for stat in provider_stats['provider_stats'])
                total_tokens = sum(stat['total_tokens'] for stat in provider_stats['provider_stats'])
            
            if pattern_stats and pattern_stats.get('pattern_stats'):
                total_patterns = sum(stat['match_count'] for stat in pattern_stats['pattern_stats'])
            
            with col1:
                st.metric("🔢 Total API Calls", total_calls)
            
            with col2:
                st.metric("🎯 Total Pattern Matches", total_patterns)
            
            with col3:
                st.metric("🪙 Total Tokens Used", total_tokens)
            
            # Usage trends (simulated - in real implementation would use time-series data)
            st.subheader("📈 Usage Trends")
            
            if provider_stats and provider_stats.get('provider_stats'):
                # Provider usage distribution
                st.subheader("🔧 Provider Usage Distribution")
                
                provider_usage = {}
                for stat in provider_stats['provider_stats']:
                    provider = stat['provider']
                    if provider in provider_usage:
                        provider_usage[provider] += stat['call_count']
                    else:
                        provider_usage[provider] = stat['call_count']
                
                if provider_usage:
                    # Create pie chart data
                    providers = list(provider_usage.keys())
                    usage_counts = list(provider_usage.values())
                    
                    # Display as columns for better visualization
                    usage_data = []
                    for provider, count in provider_usage.items():
                        percentage = (count / total_calls) * 100 if total_calls > 0 else 0
                        usage_data.append({
                            'Provider': provider,
                            'Calls': count,
                            'Percentage': f"{percentage:.1f}%"
                        })
                    
                    st.dataframe(usage_data, use_container_width=True)
            
            # System health indicators
            st.subheader("🏥 System Health")
            
            if provider_stats and provider_stats.get('provider_stats'):
                # Calculate health metrics
                avg_latencies = [stat['avg_latency'] for stat in provider_stats['provider_stats']]
                overall_avg_latency = sum(avg_latencies) / len(avg_latencies) if avg_latencies else 0
                
                # Health status based on latency
                if overall_avg_latency < 1000:
                    health_status = "🟢 Excellent"
                    health_color = "green"
                elif overall_avg_latency < 3000:
                    health_status = "🟡 Good"
                    health_color = "orange"
                else:
                    health_status = "🔴 Needs Attention"
                    health_color = "red"
                
                col1, col2 = st.columns(2)
                
                with col1:
                    st.metric(
                        "⚡ System Response Time",
                        f"{overall_avg_latency:.1f}ms",
                        delta=None
                    )
                
                with col2:
                    st.markdown(f"**System Health:** {health_status}")
            
            # Recommendations for optimization
            st.subheader("💡 Optimization Recommendations")
            
            recommendations = []
            
            if provider_stats and provider_stats.get('provider_stats'):
                # Check for slow providers
                slow_providers = [
                    stat for stat in provider_stats['provider_stats'] 
                    if stat['avg_latency'] > 3000
                ]
                
                if slow_providers:
                    for provider in slow_providers:
                        recommendations.append(
                            f"⚠️ Consider optimizing {provider['provider']}/{provider['model']} "
                            f"(avg latency: {provider['avg_latency']:.1f}ms)"
                        )
                
                # Check for underutilized providers
                if len(provider_stats['provider_stats']) > 1:
                    min_usage = min(stat['call_count'] for stat in provider_stats['provider_stats'])
                    max_usage = max(stat['call_count'] for stat in provider_stats['provider_stats'])
                    
                    if max_usage > min_usage * 5:  # Significant usage imbalance
                        recommendations.append(
                            "📊 Consider load balancing across providers for better performance"
                        )
            
            if pattern_stats and pattern_stats.get('pattern_stats'):
                # Check for low-performing patterns
                low_acceptance = [
                    stat for stat in pattern_stats['pattern_stats']
                    if stat['acceptance_rate'] < 0.3 and stat['match_count'] > 5
                ]
                
                if low_acceptance:
                    recommendations.append(
                        f"🎯 Review patterns with low acceptance rates: "
                        f"{', '.join([p['pattern_id'] for p in low_acceptance[:3]])}"
                    )
            
            if not recommendations:
                recommendations.append("✅ System is performing well - no immediate optimizations needed")
            
            for rec in recommendations:
                st.info(rec)
            
        except Exception as e:
            st.error(f"❌ Error loading usage patterns: {str(e)}")
    
    def render_llm_messages(self):
        """Render LLM messages (prompts and responses) for debugging and observability."""
        st.subheader("💬 LLM Messages & Responses")
        
        try:
            # Get LLM messages from audit system
            messages = asyncio.run(self.get_llm_messages())
            
            if not messages:
                st.info("No LLM messages available yet. Run some analyses to see LLM interactions.")
                return
            
            # Filter options
            col1, col2, col3 = st.columns(3)
            
            with col1:
                # Session filter
                session_ids = list(set([msg['session_id'] for msg in messages]))
                selected_session = st.selectbox(
                    "Filter by Session",
                    ["All Sessions"] + session_ids,
                    key="llm_session_filter"
                )
            
            with col2:
                # Provider filter
                providers = list(set([f"{msg['provider']}/{msg['model']}" for msg in messages]))
                selected_provider = st.selectbox(
                    "Filter by Provider",
                    ["All Providers"] + providers,
                    key="llm_provider_filter"
                )
            
            with col3:
                # Purpose filter
                purposes = list(set([msg.get('purpose', 'unknown') for msg in messages]))
                selected_purpose = st.selectbox(
                    "Filter by Purpose",
                    ["All Purposes"] + sorted(purposes),
                    key="llm_purpose_filter"
                )
            
            # Additional row for message limit
            col4, _, _ = st.columns(3)
            with col4:
                message_limit = st.selectbox(
                    "Messages to Show",
                    [10, 25, 50, 100],
                    index=1,
                    key="llm_message_limit"
                )
            
            # Apply filters
            filtered_messages = messages
            
            if selected_session != "All Sessions":
                filtered_messages = [msg for msg in filtered_messages if msg['session_id'] == selected_session]
            
            if selected_provider != "All Providers":
                provider, model = selected_provider.split('/', 1)
                filtered_messages = [msg for msg in filtered_messages if msg['provider'] == provider and msg['model'] == model]
            
            if selected_purpose != "All Purposes":
                filtered_messages = [msg for msg in filtered_messages if msg.get('purpose', 'unknown') == selected_purpose]
            
            # Limit results
            filtered_messages = filtered_messages[:message_limit]
            
            if not filtered_messages:
                st.info("No messages match the selected filters.")
                return
            
            # Display messages
            st.subheader(f"📋 Messages ({len(filtered_messages)} shown)")
            
            for i, msg in enumerate(filtered_messages):
                # Build the title string without nested f-strings
                tokens_text = f", {msg['tokens']} tokens" if msg['tokens'] else ""
                purpose_text = f" - {msg.get('purpose', 'unknown')}"
                title = f"🔹 {msg['provider']}/{msg['model']}{purpose_text} - {msg['timestamp']} ({msg['latency_ms']}ms{tokens_text})"
                
                with st.expander(title, expanded=False):
                    # Message metadata
                    col1, col2, col3, col4 = st.columns(4)
                    
                    with col1:
                        st.text(f"Session: {msg['session_id']}")
                    
                    with col2:
                        st.text(f"Purpose: {msg.get('purpose', 'unknown')}")
                    
                    with col3:
                        st.text(f"Latency: {msg['latency_ms']}ms")
                    
                    with col4:
                        if msg['tokens']:
                            st.text(f"Tokens: {msg['tokens']}")
                        else:
                            st.text("Tokens: N/A")
                    
                    # Prompt
                    if msg['prompt']:
                        st.subheader("📝 Prompt")
                        st.code(msg['prompt'], language="text")
                    else:
                        st.info("No prompt recorded")
                    
                    # Response
                    if msg['response']:
                        st.subheader("🤖 Response")
                        st.code(msg['response'], language="text")
                    else:
                        st.info("No response recorded")
                    
                    st.divider()
            
            # Summary statistics
            st.subheader("📊 Message Statistics")
            
            col1, col2, col3, col4 = st.columns(4)
            
            with col1:
                st.metric("Total Messages", len(filtered_messages))
            
            with col2:
                avg_latency = sum(msg['latency_ms'] for msg in filtered_messages) / len(filtered_messages)
                st.metric("Avg Latency", f"{avg_latency:.1f}ms")
            
            with col3:
                total_tokens = sum(msg['tokens'] or 0 for msg in filtered_messages)
                st.metric("Total Tokens", total_tokens)
            
            with col4:
                unique_sessions = len(set(msg['session_id'] for msg in filtered_messages))
                st.metric("Unique Sessions", unique_sessions)
            
        except Exception as e:
            st.error(f"❌ Error loading LLM messages: {str(e)}")
    
    async def get_llm_messages(self) -> List[Dict[str, Any]]:
        """Fetch LLM messages from audit system."""
        try:
            from app.utils.audit import get_audit_logger
            
            audit_logger = get_audit_logger()
            return audit_logger.get_llm_messages(
                session_id=st.session_state.session_id if hasattr(st.session_state, 'session_id') else None,
                limit=100
            )
            
        except Exception as e:
            st.error(f"Error fetching LLM messages: {str(e)}")
            return []
    
    async def get_provider_statistics(self, 
                                    time_filter: str = "All Time",
                                    include_test_providers: bool = False,
                                    current_session_only: bool = False) -> Dict[str, Any]:
        """Fetch provider statistics from audit system with filtering options."""
        try:
            # Import audit system
            from app.utils.audit import get_audit_logger
            
            audit_logger = get_audit_logger()
            
            # Get current session ID if filtering by current session
            session_id = st.session_state.get('session_id') if current_session_only else None
            
            return audit_logger.get_provider_stats(
                time_filter=time_filter,
                include_test_providers=include_test_providers,
                session_id=session_id
            )
            
        except Exception as e:
            st.error(f"Error fetching provider statistics: {str(e)}")
            return {}
    
    async def get_pattern_statistics(self) -> Dict[str, Any]:
        """Fetch pattern statistics from audit system."""
        try:
            # Import audit system
            from app.utils.audit import get_audit_logger
            
            audit_logger = get_audit_logger()
            return audit_logger.get_pattern_stats()
            
        except Exception as e:
            st.error(f"Error fetching pattern statistics: {str(e)}")
            return {}
    
    def render_observability_admin(self):
        """Render observability administration tools."""
        st.subheader("🧹 Observability Administration")
        
        st.write("**Database Management**")
        
        # Show database statistics
        try:
            from app.utils.audit import get_audit_logger
            audit_logger = get_audit_logger()
            
            # Get total counts
            with sqlite3.connect(audit_logger.db_path) as conn:
                cursor = conn.execute("SELECT COUNT(*) FROM runs")
                total_runs = cursor.fetchone()[0]
                
                cursor = conn.execute("SELECT COUNT(*) FROM matches")
                total_matches = cursor.fetchone()[0]
                
                # Get test provider counts
                cursor = conn.execute("""
                    SELECT COUNT(*) FROM runs 
                    WHERE provider IN ('fake', 'MockLLM', 'error-provider', 'AuditedLLMProvider')
                """)
                test_runs = cursor.fetchone()[0]
            
            col1, col2, col3 = st.columns(3)
            with col1:
                st.metric("Total LLM Calls", total_runs)
            with col2:
                st.metric("Pattern Matches", total_matches)
            with col3:
                st.metric("Test/Mock Calls", test_runs)
            
            # Cleanup options
            st.write("**🧹 Cleanup Options**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                st.write("**Remove Test/Mock Provider Data**")
                st.caption("Remove calls from fake, MockLLM, error-provider, and AuditedLLMProvider")
                
                if st.button("🗑️ Clean Test Data", type="secondary"):
                    try:
                        with sqlite3.connect(audit_logger.db_path) as conn:
                            cursor = conn.execute("""
                                DELETE FROM runs 
                                WHERE provider IN ('fake', 'MockLLM', 'error-provider', 'AuditedLLMProvider')
                            """)
                            deleted_count = cursor.rowcount
                            conn.commit()
                        
                        st.success(f"✅ Removed {deleted_count} test/mock provider records")
                        
                    except Exception as e:
                        st.error(f"❌ Error cleaning test data: {str(e)}")
            
            with col2:
                st.write("**Remove Old Records**")
                st.caption("Remove audit records older than specified days")
                
                days_to_keep = st.number_input("Days to keep", min_value=1, max_value=365, value=30)
                
                if st.button("🗑️ Clean Old Records", type="secondary"):
                    try:
                        deleted_count = audit_logger.cleanup_old_records(days=days_to_keep)
                        st.success(f"✅ Removed {deleted_count} old records (older than {days_to_keep} days)")
                        
                    except Exception as e:
                        st.error(f"❌ Error cleaning old records: {str(e)}")
            
            # Export options
            st.write("**📤 Export Options**")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("📊 Export Provider Stats", type="secondary"):
                    try:
                        stats = audit_logger.get_provider_stats(include_test_providers=True)
                        import json
                        stats_json = json.dumps(stats, indent=2, default=str)
                        
                        st.download_button(
                            label="💾 Download Provider Stats JSON",
                            data=stats_json,
                            file_name=f"provider_stats_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error exporting stats: {str(e)}")
            
            with col2:
                if st.button("💬 Export LLM Messages", type="secondary"):
                    try:
                        messages = audit_logger.get_llm_messages(limit=1000)
                        import json
                        messages_json = json.dumps(messages, indent=2, default=str)
                        
                        st.download_button(
                            label="💾 Download Messages JSON",
                            data=messages_json,
                            file_name=f"llm_messages_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                            mime="application/json"
                        )
                        
                    except Exception as e:
                        st.error(f"❌ Error exporting messages: {str(e)}")
            
        except Exception as e:
            st.error(f"❌ Error loading admin data: {str(e)}")
    
    def render_pattern_library_management(self):
        """Render the pattern library management interface."""
        st.header("📚 Pattern Library Management")
        
        # Add helpful documentation
        with st.expander("ℹ️ What is the Pattern Library?", expanded=False):
            st.markdown("""
            The **Pattern Library** is a collection of reusable solution templates that help assess automation feasibility. 
            Each pattern represents a proven approach to automating specific types of business processes.
            
            ### 🏷️ **Pattern Components Explained:**
            
            - **Pattern ID**: Unique identifier (e.g., PAT-001, PAT-002)
            - **Name**: Descriptive title of the automation pattern
            - **Description**: Detailed explanation of what the pattern automates
            - **Domain**: Business area (e.g., legal_compliance, finance, customer_service)
            - **Feasibility**: Automation potential (Automatable, Partially Automatable, Not Automatable)
            - **Pattern Types**: Tags/categories describing the automation approach (e.g., api_integration, nlp_processing, human_in_loop)
            - **Tech Stack**: Technologies typically used to implement this pattern
            - **Complexity**: Implementation difficulty (Low, Medium, High)
            - **Estimated Effort**: Time required to implement (e.g., 2-4 weeks)
            - **Confidence Score**: How reliable this pattern is (0.0 to 1.0)
            
            ### 🎯 **How Patterns Are Used:**
            When you submit a requirement, the system:
            1. Matches your requirement against these patterns
            2. Suggests the most relevant automation approaches
            3. Provides technology recommendations based on proven solutions
            4. Estimates feasibility based on similar past implementations
            
            ### 💡 **Pattern Types (Tags):**
            Pattern types are like tags that categorize the automation approach:
            - `api_integration` - Connects to external systems via APIs
            - `nlp_processing` - Uses natural language processing
            - `human_in_loop` - Requires human oversight or approval
            - `data_extraction` - Extracts information from documents
            - `workflow_automation` - Automates business processes
            - `pii_redaction` - Handles sensitive data protection
            - `summarization` - Creates summaries of content
            """)
        
        # Load patterns using the pattern loader
        try:
            from app.pattern.loader import PatternLoader
            pattern_loader = PatternLoader("data/patterns")
            
            # Auto-refresh cache when Pattern Library tab is opened to ensure we see current patterns
            # This prevents showing deleted patterns that are cached
            pattern_loader.refresh_cache()
            patterns = pattern_loader.load_patterns()
        except Exception as e:
            st.error(f"❌ Error loading patterns: {str(e)}")
            return
        
        # Management tabs
        view_tab, edit_tab, create_tab = st.tabs(["👀 View Patterns", "✏️ Edit Pattern", "➕ Create Pattern"])
        
        with view_tab:
            self.render_pattern_viewer(patterns)
        
        with edit_tab:
            self.render_pattern_editor(patterns, pattern_loader)
        
        with create_tab:
            self.render_pattern_creator(pattern_loader)
    
    def render_pattern_viewer(self, patterns: list):
        """Render the pattern viewer interface."""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("👀 Pattern Library Overview")
        with col2:
            if st.button("🔄 Refresh Patterns", help="Refresh the pattern list to show current patterns"):
                # Force refresh by clearing cache and reloading
                st.cache_data.clear()
                st.rerun()
        
        if not patterns:
            st.info("📝 No patterns found in the library.")
            return
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Patterns", len(patterns))
        with col2:
            automatable = len([p for p in patterns if p.get('feasibility') == 'Automatable'])
            st.metric("Automatable", automatable)
        with col3:
            partial = len([p for p in patterns if p.get('feasibility') == 'Partially Automatable'])
            st.metric("Partially Automatable", partial)
        with col4:
            not_auto = len([p for p in patterns if p.get('feasibility') == 'Not Automatable'])
            st.metric("Not Automatable", not_auto)
        
        # Filter options
        st.subheader("🔍 Filter Patterns")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            domains = list(set(p.get('domain', 'unknown') for p in patterns))
            selected_domain = st.selectbox("🏢 Domain", ["All"] + sorted(domains))
        
        with col2:
            feasibilities = list(set(p.get('feasibility', 'unknown') for p in patterns))
            selected_feasibility = st.selectbox("⚡ Feasibility", ["All"] + sorted(feasibilities))
        
        with col3:
            complexities = list(set(p.get('complexity', 'unknown') for p in patterns))
            selected_complexity = st.selectbox("🎯 Complexity", ["All"] + sorted(complexities))
        
        with col4:
            # Get all unique pattern types (tags)
            all_pattern_types = set()
            for p in patterns:
                pattern_types = p.get('pattern_type', [])
                if isinstance(pattern_types, list):
                    all_pattern_types.update(pattern_types)
            selected_pattern_type = st.selectbox("🏷️ Pattern Type", ["All"] + sorted(all_pattern_types))
        
        # Filter patterns
        filtered_patterns = patterns
        if selected_domain != "All":
            filtered_patterns = [p for p in filtered_patterns if p.get('domain') == selected_domain]
        if selected_feasibility != "All":
            filtered_patterns = [p for p in filtered_patterns if p.get('feasibility') == selected_feasibility]
        if selected_complexity != "All":
            filtered_patterns = [p for p in filtered_patterns if p.get('complexity') == selected_complexity]
        if selected_pattern_type != "All":
            filtered_patterns = [p for p in filtered_patterns 
                                if selected_pattern_type in p.get('pattern_type', [])]
        
        # Sort patterns by pattern_id for consistent ordering (PAT-001, PAT-002, etc.)
        filtered_patterns = sorted(filtered_patterns, key=lambda p: p.get('pattern_id', 'ZZZ'))
        
        # Show filtering results and pattern type overview
        col1, col2 = st.columns([1, 1])
        with col1:
            st.write(f"📊 Showing **{len(filtered_patterns)}** of **{len(patterns)}** patterns")
        
        with col2:
            if st.button("🏷️ Show Pattern Types Overview"):
                st.session_state.show_pattern_types_overview = not st.session_state.get('show_pattern_types_overview', False)
        
        # Pattern types overview
        if st.session_state.get('show_pattern_types_overview', False):
            with st.expander("🏷️ Pattern Types in Library", expanded=True):
                # Count pattern types across all patterns
                pattern_type_counts = {}
                for pattern in patterns:
                    for ptype in pattern.get('pattern_type', []):
                        pattern_type_counts[ptype] = pattern_type_counts.get(ptype, 0) + 1
                
                if pattern_type_counts:
                    st.write("**Available Pattern Types (Tags) and Usage:**")
                    
                    # Sort by usage count
                    sorted_types = sorted(pattern_type_counts.items(), key=lambda x: x[1], reverse=True)
                    
                    # Display in columns
                    cols = st.columns(3)
                    for i, (ptype, count) in enumerate(sorted_types):
                        with cols[i % 3]:
                            st.metric(ptype.replace('_', ' ').title(), f"{count} patterns")
                else:
                    st.info("No pattern types found in the library.")
        
        # Display patterns
        for idx, pattern in enumerate(filtered_patterns):
            # Create a more informative header with feasibility indicator
            feasibility = pattern.get('feasibility', 'Unknown')
            feasibility_emoji = {
                'Automatable': '🟢',
                'Partially Automatable': '🟡', 
                'Not Automatable': '🔴'
            }.get(feasibility, '⚪')
            
            pattern_header = f"{feasibility_emoji} {pattern.get('pattern_id', 'Unknown')} - {pattern.get('name', 'Unnamed Pattern')}"
            
            with st.expander(pattern_header):
                # Pattern types as prominent tags at the top
                pattern_types = pattern.get('pattern_type', [])
                if pattern_types:
                    st.write("**🏷️ Pattern Types (Tags):**")
                    # Display pattern types as colored badges
                    cols = st.columns(min(len(pattern_types), 5))
                    for i, ptype in enumerate(pattern_types):
                        with cols[i % 5]:
                            st.code(ptype, language=None)
                    st.divider()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**📝 Description:**")
                    st.write(pattern.get('description', 'No description available'))
                    
                    st.write("**🛠️ Tech Stack:**")
                    tech_stack = pattern.get('tech_stack', [])
                    if tech_stack:
                        # Display tech stack in a more organized way
                        tech_cols = st.columns(min(len(tech_stack), 3))
                        for i, tech in enumerate(tech_stack):
                            with tech_cols[i % 3]:
                                st.write(f"• {tech}")
                    else:
                        st.write("_No tech stack specified_")
                    
                    # Show input requirements if available
                    input_reqs = pattern.get('input_requirements', [])
                    if input_reqs:
                        st.write("**📋 Input Requirements:**")
                        for req in input_reqs:
                            st.write(f"• {req}")
                
                with col2:
                    st.write("**📊 Pattern Details:**")
                    
                    # Use metrics for key information
                    domain = pattern.get('domain', 'Unknown')
                    complexity = pattern.get('complexity', 'Unknown')
                    effort = pattern.get('estimated_effort', 'Unknown')
                    confidence = pattern.get('confidence_score', 'Unknown')
                    
                    st.metric("Domain", domain)
                    st.metric("Feasibility", feasibility)
                    st.metric("Complexity", complexity)
                    st.metric("Estimated Effort", effort)
                    
                    if isinstance(confidence, (int, float)):
                        st.metric("Confidence Score", f"{confidence:.2f}")
                    else:
                        st.metric("Confidence Score", str(confidence))
                    
                    # Show creation info if available
                    if pattern.get('created_at'):
                        st.write("**📅 Created:**")
                        st.write(pattern.get('created_at', 'Unknown')[:10])  # Just the date part
                    
                    if pattern.get('enhanced_by_llm'):
                        st.write("**🤖 Enhanced by LLM:** ✅")
                
                # Show LLM insights if available
                llm_insights = pattern.get('llm_insights', [])
                llm_challenges = pattern.get('llm_challenges', [])
                
                if llm_insights or llm_challenges:
                    st.divider()
                    insight_col1, insight_col2 = st.columns(2)
                    
                    with insight_col1:
                        if llm_insights:
                            st.write("**💡 LLM Insights:**")
                            for insight in llm_insights:
                                st.write(f"• {insight}")
                    
                    with insight_col2:
                        if llm_challenges:
                            st.write("**⚠️ LLM Challenges:**")
                            for challenge in llm_challenges:
                                st.write(f"• {challenge}")
                
                # Show recommended approach if available
                recommended_approach = pattern.get('llm_recommended_approach', '')
                if recommended_approach:
                    st.write("**🎯 Recommended Approach:**")
                    st.write(recommended_approach)
    
    def render_pattern_editor(self, patterns: list, pattern_loader):
        """Render the pattern editor interface."""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("✏️ Edit Existing Pattern")
        with col2:
            if st.button("🔄 Refresh List", help="Refresh the pattern list"):
                pattern_loader.refresh_cache()
                st.rerun()
        
        # No need for complex success message handling since we show them immediately
        
        if not patterns:
            st.info("📝 No patterns available to edit.")
            return
        
        # Pattern selection - sort patterns by pattern_id first
        sorted_patterns = sorted(patterns, key=lambda p: p.get('pattern_id', 'ZZZ'))
        pattern_options = {f"{p.get('pattern_id', 'Unknown')} - {p.get('name', 'Unnamed')}": p for p in sorted_patterns}
        
        if not pattern_options:
            st.info("📝 No patterns available to edit.")
            return
        
        selected_pattern_key = st.selectbox("Select Pattern to Edit", list(pattern_options.keys()))
        
        if not selected_pattern_key:
            return
        
        selected_pattern = pattern_options[selected_pattern_key]
        pattern_id = selected_pattern.get('pattern_id', '')
        
        # Double-check that the pattern file still exists
        import os
        pattern_file_path = f"data/patterns/{pattern_id}.json"
        if not os.path.exists(pattern_file_path):
            st.error(f"❌ Pattern {pattern_id} no longer exists. It may have been deleted.")
            st.info("🔄 Please use the 'Refresh List' button to update the pattern list.")
            return
        
        # Handle delete confirmation outside of form
        if st.session_state.get(f"confirm_delete_{pattern_id}", False):
            st.warning(f"⚠️ Are you sure you want to delete pattern {pattern_id}?")
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button(f"🗑️ Yes, Delete {pattern_id}", key=f"confirm_delete_yes_{pattern_id}"):
                    # Perform the deletion
                    with st.spinner("Deleting pattern..."):
                        success = self.delete_pattern_confirmed(pattern_id, pattern_loader)
                    
                    if success:
                        # Clear the confirmation state
                        st.session_state[f"confirm_delete_{pattern_id}"] = False
                        st.balloons()  # Visual feedback
                        # Don't auto-rerun, let user manually refresh if needed
                        st.info("🔄 Use the 'Refresh List' button to update the pattern list.")
                    else:
                        st.error("Failed to delete pattern. Please try again.")
            
            with col2:
                if st.button("❌ Cancel", key=f"confirm_delete_cancel_{pattern_id}"):
                    # Clear the confirmation state
                    st.session_state[f"confirm_delete_{pattern_id}"] = False
                    st.info("Deletion cancelled.")
            
            return  # Don't show the form while in delete confirmation mode
        
        # Create unique keys for form elements
        form_key = f"edit_pattern_{hash(pattern_id)}"
        
        with st.form(key=form_key):
            st.write(f"**Editing Pattern: {pattern_id}**")
            
            # Basic information
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Pattern Name", value=selected_pattern.get('name', ''))
                domain = st.text_input("Domain", value=selected_pattern.get('domain', ''))
                feasibility = st.selectbox("Feasibility", 
                                         ["Automatable", "Partially Automatable", "Not Automatable"],
                                         index=["Automatable", "Partially Automatable", "Not Automatable"].index(
                                             selected_pattern.get('feasibility', 'Automatable')))
            
            with col2:
                complexity = st.selectbox("Complexity", ["Low", "Medium", "High"],
                                        index=["Low", "Medium", "High"].index(selected_pattern.get('complexity', 'Medium')))
                estimated_effort = st.text_input("Estimated Effort", value=selected_pattern.get('estimated_effort', ''))
                confidence_score = st.number_input("Confidence Score", min_value=0.0, max_value=1.0, 
                                                 value=float(selected_pattern.get('confidence_score', 0.5)), step=0.01)
            
            # Description
            description = st.text_area("Description", value=selected_pattern.get('description', ''), height=100)
            
            # Tech stack
            tech_stack_text = st.text_area("Tech Stack (one per line)", 
                                         value='\n'.join(selected_pattern.get('tech_stack', [])), height=100)
            
            # Pattern types with guidance
            st.write("**🏷️ Pattern Types (Tags)**")
            st.caption("Tags that describe the automation approach (see Create tab for examples)")
            pattern_types_text = st.text_area("Pattern Types (one per line)", 
                                            value='\n'.join(selected_pattern.get('pattern_type', [])), height=80)
            
            # Form buttons
            col1, col2, col3 = st.columns(3)
            with col1:
                save_button = st.form_submit_button("💾 Save Changes", type="primary")
            with col2:
                delete_button = st.form_submit_button("🗑️ Delete Pattern", type="secondary")
            with col3:
                cancel_button = st.form_submit_button("❌ Cancel")
            
            if save_button:
                self.save_pattern_changes(selected_pattern, {
                    'name': name,
                    'domain': domain,
                    'feasibility': feasibility,
                    'complexity': complexity,
                    'estimated_effort': estimated_effort,
                    'confidence_score': confidence_score,
                    'description': description,
                    'tech_stack': [t.strip() for t in tech_stack_text.split('\n') if t.strip()],
                    'pattern_type': [t.strip() for t in pattern_types_text.split('\n') if t.strip()]
                }, pattern_loader)
            
            elif delete_button:
                # Set delete confirmation state instead of calling delete_pattern directly
                st.session_state[f"confirm_delete_{pattern_id}"] = True
    
    def render_pattern_creator(self, pattern_loader):
        """Render the pattern creator interface."""
        st.subheader("➕ Create New Pattern")
        
        # Generate next pattern ID
        try:
            patterns = pattern_loader.load_patterns()
            existing_ids = [p.get('pattern_id', '') for p in patterns]
            # Extract numbers from existing IDs and find the next one
            numbers = []
            for pid in existing_ids:
                if pid.startswith('PAT-'):
                    try:
                        numbers.append(int(pid.split('-')[1]))
                    except (IndexError, ValueError):
                        continue
            next_number = max(numbers) + 1 if numbers else 1
            next_pattern_id = f"PAT-{next_number:03d}"
        except Exception:
            next_pattern_id = "PAT-001"
        
        with st.form(key="create_pattern_form"):
            st.write(f"**Creating New Pattern: {next_pattern_id}**")
            
            # Basic information
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Pattern Name", placeholder="Enter pattern name")
                domain = st.text_input("Domain", placeholder="e.g., legal_compliance, finance")
                feasibility = st.selectbox("Feasibility", ["Automatable", "Partially Automatable", "Not Automatable"])
            
            with col2:
                complexity = st.selectbox("Complexity", ["Low", "Medium", "High"])
                estimated_effort = st.text_input("Estimated Effort", placeholder="e.g., 2-4 weeks")
                confidence_score = st.number_input("Confidence Score", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
            
            # Description
            description = st.text_area("Description", placeholder="Describe what this pattern does and when to use it", height=100)
            
            # Tech stack
            tech_stack_text = st.text_area("Tech Stack (one per line)", 
                                         placeholder="FastAPI\nPostgreSQL\nDocker", height=100)
            
            # Pattern types with helpful guidance
            st.write("**🏷️ Pattern Types (Tags)**")
            st.caption("Add tags that describe the automation approach. Common types include:")
            
            # Show common pattern types as examples
            with st.expander("💡 Common Pattern Types", expanded=False):
                st.write("""
                **Integration & APIs:**
                - `api_integration` - Connects to external systems
                - `webhook_processing` - Handles incoming webhooks
                - `database_sync` - Synchronizes data between systems
                
                **Data Processing:**
                - `data_extraction` - Extracts information from documents
                - `nlp_processing` - Natural language processing
                - `ocr_processing` - Optical character recognition
                - `pii_redaction` - Removes sensitive information
                
                **Workflow & Automation:**
                - `workflow_automation` - Automates business processes
                - `human_in_loop` - Requires human oversight
                - `approval_workflow` - Handles approval processes
                - `notification_system` - Sends alerts and notifications
                
                **Content & Communication:**
                - `summarization` - Creates content summaries
                - `translation` - Language translation
                - `content_generation` - Creates new content
                - `email_processing` - Handles email automation
                """)
            
            pattern_types_text = st.text_area("Pattern Types (one per line)", 
                                            placeholder="api_integration\nnlp_processing\nhuman_in_loop", height=80)
            
            # Input requirements
            input_requirements_text = st.text_area("Input Requirements (one per line)", 
                                                  placeholder="digital_documents\napi_access\nuser_permissions", height=80)
            
            # Create button
            create_button = st.form_submit_button("🚀 Create Pattern", type="primary")
            
            if create_button:
                if not name or not description:
                    st.error("❌ Pattern name and description are required!")
                else:
                    self.create_new_pattern({
                        'pattern_id': next_pattern_id,
                        'name': name,
                        'domain': domain,
                        'feasibility': feasibility,
                        'complexity': complexity,
                        'estimated_effort': estimated_effort,
                        'confidence_score': confidence_score,
                        'description': description,
                        'tech_stack': [t.strip() for t in tech_stack_text.split('\n') if t.strip()],
                        'pattern_type': [t.strip() for t in pattern_types_text.split('\n') if t.strip()],
                        'input_requirements': [t.strip() for t in input_requirements_text.split('\n') if t.strip()]
                    }, pattern_loader)
    
    def save_pattern_changes(self, original_pattern: dict, changes: dict, pattern_loader):
        """Save changes to an existing pattern with validation."""
        try:
            # Validate required fields
            if not changes.get('name') or not changes.get('description'):
                st.error("❌ Pattern name and description are required!")
                return
            
            # Update the pattern with changes
            updated_pattern = original_pattern.copy()
            updated_pattern.update(changes)
            
            # Add metadata
            from datetime import datetime
            updated_pattern['last_modified'] = datetime.now().isoformat()
            updated_pattern['modified_by'] = 'pattern_library_ui'
            
            # Validate pattern using schema
            try:
                pattern_loader._validate_pattern(updated_pattern)
            except Exception as validation_error:
                st.error(f"❌ Pattern validation failed: {str(validation_error)}")
                return
            
            # Create backup before saving
            pattern_id = updated_pattern.get('pattern_id')
            file_path = f"data/patterns/{pattern_id}.json"
            backup_path = f"data/patterns/.backup_{pattern_id}_{int(datetime.now().timestamp())}.json"
            
            import json
            import os
            import shutil
            
            # Create backup if original exists
            if os.path.exists(file_path):
                shutil.copy2(file_path, backup_path)
            
            # Save updated pattern
            with open(file_path, 'w') as f:
                json.dump(updated_pattern, f, indent=2)
            
            # Refresh cache
            pattern_loader.refresh_cache()
            
            st.success(f"✅ Pattern {pattern_id} saved successfully!")
            st.info(f"💾 Backup created: {backup_path}")
            
        except Exception as e:
            st.error(f"❌ Error saving pattern: {str(e)}")
            app_logger.error(f"Pattern save error: {e}")
    
    def delete_pattern_confirmed(self, pattern_id: str, pattern_loader) -> bool:
        """Actually delete a pattern from the library (called after confirmation)."""
        try:
            import os
            import shutil
            from datetime import datetime
            
            file_path = f"data/patterns/{pattern_id}.json"
            
            if not os.path.exists(file_path):
                st.warning(f"⚠️ Pattern {pattern_id} has already been deleted or moved.")
                st.info("🔄 Refreshing pattern list...")
                pattern_loader.refresh_cache()
                return True  # Consider this a "success" since the pattern is gone
            
            # Create backup before deletion
            backup_path = f"data/patterns/.deleted_{pattern_id}_{int(datetime.now().timestamp())}.json"
            shutil.copy2(file_path, backup_path)
            
            # Delete the file
            os.remove(file_path)
            pattern_loader.refresh_cache()
            
            # Show success message immediately
            st.success(f"✅ Pattern {pattern_id} deleted successfully!")
            st.info(f"💾 Backup created: {backup_path}")
            
            return True
                
        except Exception as e:
            st.error(f"❌ Error deleting pattern: {str(e)}")
            app_logger.error(f"Pattern deletion error: {e}")
            return False
    
    def create_new_pattern(self, pattern_data: dict, pattern_loader):
        """Create a new pattern in the library with validation."""
        try:
            from datetime import datetime
            import json
            import os
            
            pattern_id = pattern_data.get('pattern_id')
            file_path = f"data/patterns/{pattern_id}.json"
            
            # Check if pattern already exists
            if os.path.exists(file_path):
                st.error(f"❌ Pattern {pattern_id} already exists!")
                return
            
            # Add required metadata
            pattern_data.update({
                'created_at': datetime.now().isoformat(),
                'created_by': 'pattern_library_ui',
                'auto_generated': False,
                'related_patterns': [],
                'constraints': {
                    'banned_tools': [],
                    'required_integrations': []
                },
                'llm_insights': [],
                'llm_challenges': [],
                'llm_recommended_approach': '',
                'enhanced_by_llm': False
            })
            
            # Validate pattern using schema
            try:
                pattern_loader._validate_pattern(pattern_data)
            except Exception as validation_error:
                st.error(f"❌ Pattern validation failed: {str(validation_error)}")
                return
            
            # Ensure data/patterns directory exists
            os.makedirs("data/patterns", exist_ok=True)
            
            # Save to file
            with open(file_path, 'w') as f:
                json.dump(pattern_data, f, indent=2)
            
            # Refresh cache
            pattern_loader.refresh_cache()
            
            st.success(f"✅ Pattern {pattern_id} created successfully!")
            st.info(f"📁 Saved to: {file_path}")
            st.info("🔄 Use the 'Refresh List' button to see the new pattern in the edit list.")
            
        except Exception as e:
            st.error(f"❌ Error creating pattern: {str(e)}")
            app_logger.error(f"Pattern creation error: {e}")
    
    def run(self):
        """Main application entry point."""
        st.title("🤖 Automated AI Assessment (AAA)")
        st.markdown("*Assess automation feasibility of your requirements with AI*")
        
        # Sidebar with provider configuration
        self.render_provider_panel()
        
        # Main content area
        tab1, tab2, tab3, tab4, tab5 = st.tabs(["📝 Analysis", "📊 Diagrams", "📈 Observability", "📚 Pattern Library", "ℹ️ About"])
        
        with tab1:
            # Input methods
            if not st.session_state.session_id:
                self.render_input_methods()
            
            # Progress tracking and results
            if st.session_state.session_id:
                self.render_progress_tracking()
                
                # Reset button
                if st.button("🔄 Start New Analysis"):
                    # Clear session state
                    st.session_state.session_id = None
                    st.session_state.current_phase = None
                    st.session_state.progress = 0
                    st.session_state.recommendations = None
                    st.session_state.qa_questions = []
                    st.session_state.processing = False
                    st.rerun()
        
        with tab2:
            self.render_mermaid_diagrams()
        
        with tab3:
            self.render_observability_dashboard()
        
        with tab4:
            self.render_pattern_library_management()
        
        with tab5:
            st.markdown("""
            ## About Automated AI Assessment (AAA)
            
            This application helps you assess whether your business requirements can be automated using agentic AI systems.
            
            ### 🚀 Core Features:
            - 📝 **Multiple Input Methods**: Text, file upload, Jira integration
            - 🤖 **Multi-Provider LLM Support**: OpenAI, Anthropic/Bedrock, Claude Direct, Internal HTTP
            - 🎯 **Intelligent Pattern Matching**: Tag filtering + vector similarity with FAISS
            - ❓ **LLM-Powered Q&A System**: AI-generated clarifying questions with caching
            - 🛠️ **LLM-Driven Tech Stack Generation**: Contextual technology recommendations
            - 🏗️ **AI-Generated Architecture Explanations**: How components work together
            - 📊 **Feasibility Assessment**: Automatable, Partially Automatable, or Not Automatable
            - 📈 **AI-Generated Architecture Diagrams**: Context, Container, and Sequence diagrams
            - 📤 **Multi-Format Export**: JSON, Markdown, and interactive HTML
            - 🎯 **Constraint-Aware**: Filters banned tools and applies business constraints
            
            ### 🆕 Advanced Features:
            - 📚 **Pattern Library Management**: Complete CRUD interface for solution patterns
            - 📈 **Enhanced Observability Dashboard**: Provider metrics, usage analytics, LLM message tracking
            - 🔍 **Enhanced Diagram Viewing**: Browser export, interactive controls, SVG download
            - 🏷️ **Pattern Type Filtering**: Filter by automation approach tags
            - 🧹 **Admin Tools**: Database cleanup, export functionality, test data management
            
            ### 🔄 How it works:
            1. **Input**: Submit requirements via text, file upload, or Jira integration
            2. **LLM Analysis**: AI processes and validates your input with pattern awareness
            3. **Q&A Loop**: Answer AI-generated clarifying questions for better accuracy
            4. **Pattern Matching**: Requirements matched against 16+ solution patterns using vector similarity
            5. **Tech Stack Generation**: LLM recommends technologies based on requirements and constraints
            6. **Architecture Analysis**: AI generates explanations and visual diagrams
            7. **Feasibility Assessment**: Get detailed automation assessment with confidence scores
            8. **Export & Visualize**: Download results in multiple formats or view interactive diagrams
            
            ### 🛠️ Provider Configuration:
            Use the sidebar to configure your preferred LLM provider and test connectivity.
            
            ### 📊 Observability:
            Monitor system performance, LLM usage, and pattern analytics in the Observability tab.
            
            ### 📚 Pattern Management:
            View, edit, create, and delete solution patterns in the Pattern Library tab.
            
            ### 🎯 Built for Enterprise:
            - **Audit Logging**: Comprehensive tracking of all LLM interactions
            - **PII Redaction**: Automatic removal of sensitive information
            - **Constraint Handling**: Respects banned tools and required integrations
            - **Multi-Provider Fallback**: Robust LLM provider switching
            - **Session Management**: Persistent state across interactions
            
            ### 📈 Recent Enhancements:
            - **Enhanced Diagram Viewing**: Standalone HTML export with interactive controls
            - **Pattern Library CRUD**: Complete management interface for solution patterns
            - **Improved Observability**: Time-based filtering, admin tools, cleanup functionality
            - **LLM-Driven Analysis**: Replaced rule-based systems with intelligent AI analysis
            - **Better Caching**: Multi-layer caching with duplicate prevention
            - **UI Improvements**: Better error handling, visual feedback, and user guidance
            
            ### 🏗️ Architecture:
            - **FastAPI Backend**: Async REST API with robust caching
            - **Streamlit Frontend**: Interactive web interface with enhanced components
            - **FAISS Vector Search**: Semantic pattern matching
            - **SQLite Audit System**: Comprehensive logging and analytics
            - **Multi-Provider LLM**: Flexible AI provider integration
            - **Pattern-Based Matching**: Reusable solution templates
            """)


def main():
    """Main function to run the Streamlit app."""
    app = AutomatedAIAssessmentUI()
    app.run()


if __name__ == "__main__":
    main()