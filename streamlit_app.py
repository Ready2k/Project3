"""Streamlit UI for AgenticOrNot application."""

import asyncio
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
import streamlit as st
from streamlit.components.v1 import html

# Optional import for OpenAI (for diagram generation)
try:
    import openai
    OPENAI_AVAILABLE = True
except ImportError:
    OPENAI_AVAILABLE = False

# Mermaid diagram functions (LLM-generated for specific requirements)
async def make_llm_request(prompt: str, provider_config: Dict) -> str:
    """Make a request to the LLM for diagram generation."""
    if not OPENAI_AVAILABLE:
        raise Exception("OpenAI library not available. Please install: pip install openai")
    
    if provider_config.get('provider') == 'openai' and provider_config.get('api_key'):
        try:
            client = openai.AsyncOpenAI(api_key=provider_config['api_key'])
            response = await client.chat.completions.create(
                model=provider_config.get('model', 'gpt-4o'),
                messages=[{"role": "user", "content": prompt}],
                max_tokens=1000,
                temperature=0.3
            )
            content = response.choices[0].message.content
            if not content:
                raise Exception("Empty response from OpenAI")
            
            # Clean the response - remove markdown code blocks if present
            content = content.strip()
            if content.startswith('```mermaid'):
                content = content.replace('```mermaid', '').replace('```', '').strip()
            elif content.startswith('```'):
                content = content.replace('```', '').strip()
            
            return content
        except Exception as e:
            raise Exception(f"OpenAI request failed: {str(e)}")
    else:
        raise Exception("Only OpenAI provider supported for diagram generation")

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


class AgenticOrNotUI:
    """Main Streamlit UI class for AgenticOrNot."""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="AgenticOrNot v1.3.2",
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
        st.info("🚧 Jira integration is not yet implemented in the backend.")
        
        col1, col2 = st.columns(2)
        
        with col1:
            jira_url = st.text_input("Jira URL:", placeholder="https://company.atlassian.net")
            ticket_key = st.text_input("Ticket Key:", placeholder="PROJ-123")
        
        with col2:
            username = st.text_input("Username:")
            api_token = st.text_input("API Token:", type="password")
        
        if st.button("🚀 Fetch from Jira", disabled=True):
            st.warning("Jira integration will be implemented in task 10.")
    
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
                    st.session_state.requirements = {
                        "description": payload.get("summary", "") + " " + payload.get("description", ""),
                        "jira_key": payload.get("key"),
                        "priority": payload.get("priority")
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
            
            st.session_state.current_phase = phase
            st.session_state.progress = progress
            
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
            try:
                with st.spinner("🤖 AI is generating personalized questions for your requirement..."):
                    response = asyncio.run(self.make_api_request(
                        "GET",
                        f"/qa/{st.session_state.session_id}/questions"
                    ))
                    questions = response.get('questions', [])
                    if questions:
                        st.session_state.qa_questions = questions
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
        
        # Show questions if we have them
        if st.session_state.qa_questions:
            answers = {}
            for q in st.session_state.qa_questions:
                if q["type"] == "text":
                    answers[q["id"]] = st.text_input(q["question"], key=f"qa_{q['id']}")
                elif q["type"] == "select":
                    answers[q["id"]] = st.selectbox(q["question"], q["options"], key=f"qa_{q['id']}")
            
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
        
        rec = st.session_state.recommendations
        
        # Overall feasibility
        feasibility = rec['feasibility']
        feasibility_colors = {
            "Yes": "🟢",
            "Partial": "🟡", 
            "No": "🔴"
        }
        
        st.subheader(f"{feasibility_colors.get(feasibility, '⚪')} Feasibility: {feasibility}")
        
        # Tech stack
        if rec.get('tech_stack'):
            st.subheader("🛠️ Recommended Tech Stack")
            tech_cols = st.columns(min(len(rec['tech_stack']), 4))
            for i, tech in enumerate(rec['tech_stack']):
                with tech_cols[i % 4]:
                    st.info(tech)
        
        # Reasoning
        if rec.get('reasoning'):
            st.subheader("💭 Reasoning")
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
                
                # Show download link
                if response.get('download_url'):
                    st.markdown(f"[📥 Download File]({response['download_url']})")
        
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
        """Render a Mermaid diagram using HTML component."""
        mermaid_html = f"""
        <div class="mermaid">
            {mermaid_code}
        </div>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <script>
            mermaid.initialize({{startOnLoad: true}});
        </script>
        """
        
        html(mermaid_html, height=400)
    
    def render_observability_dashboard(self):
        """Render the observability dashboard with metrics and analytics."""
        st.header("📈 System Observability")
        
        # Show info message if no session is active
        if not st.session_state.session_id:
            st.info("💡 Start an analysis in the Analysis tab to see observability data here.")
            return
        
        # Dashboard tabs
        metrics_tab, patterns_tab, usage_tab = st.tabs(["🔧 Provider Metrics", "🎯 Pattern Analytics", "📊 Usage Patterns"])
        
        with metrics_tab:
            self.render_provider_metrics()
        
        with patterns_tab:
            self.render_pattern_analytics()
        
        with usage_tab:
            self.render_usage_patterns()
    
    def render_provider_metrics(self):
        """Render LLM provider performance metrics."""
        st.subheader("🔧 LLM Provider Performance")
        
        try:
            # Fetch provider statistics from audit data
            provider_stats = asyncio.run(self.get_provider_statistics())
            
            if not provider_stats or not provider_stats.get('provider_stats'):
                st.info("No provider metrics available yet. Run some analyses to see performance data.")
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
    
    async def get_provider_statistics(self) -> Dict[str, Any]:
        """Fetch provider statistics from audit system."""
        try:
            # Import audit system
            from app.utils.audit import get_audit_logger
            
            audit_logger = get_audit_logger()
            return audit_logger.get_provider_stats()
            
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
    
    def run(self):
        """Main application entry point."""
        st.title("🤖 AgenticOrNot v1.3.2")
        st.markdown("*Assess automation feasibility of your requirements with AI*")
        
        # Sidebar with provider configuration
        self.render_provider_panel()
        
        # Main content area
        tab1, tab2, tab3, tab4 = st.tabs(["📝 Analysis", "📊 Diagrams", "📈 Observability", "ℹ️ About"])
        
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
            st.markdown("""
            ## About AgenticOrNot v1.3.2
            
            This application helps you assess whether your business requirements can be automated using agentic AI systems.
            
            ### Features:
            - 📝 Multiple input methods (text, file upload, Jira integration)
            - 🤖 Pluggable LLM providers (OpenAI, Bedrock, Claude, Internal)
            - 🎯 Pattern matching against solution library
            - ❓ Interactive Q&A for clarification
            - 📊 Feasibility assessment with confidence scores
            - 📤 Export results in JSON and Markdown formats
            - 📈 System architecture diagrams
            
            ### How it works:
            1. **Input**: Submit your requirements through text, file, or Jira
            2. **Analysis**: The system processes and validates your input
            3. **Clarification**: Answer questions to improve accuracy
            4. **Matching**: Requirements are matched against pattern library
            5. **Recommendations**: Get feasibility assessment and tech stack suggestions
            6. **Export**: Download results for documentation
            
            ### Provider Configuration:
            Use the sidebar to configure your preferred LLM provider and test connectivity.
            """)


def main():
    """Main function to run the Streamlit app."""
    app = AgenticOrNotUI()
    app.run()


if __name__ == "__main__":
    main()