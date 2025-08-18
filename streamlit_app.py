"""Streamlit UI for Automated AI Assessment (AAA) application."""

import asyncio
import json
import os
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

def _validate_mermaid_syntax(mermaid_code: str) -> tuple[bool, str]:
    """Validate basic Mermaid syntax and return (is_valid, error_message)."""
    if not mermaid_code.strip():
        return False, "Empty diagram code"
    
    # Check for severely malformed code (all on one line with no spaces around arrows)
    if '\n' not in mermaid_code and len(mermaid_code) > 200:
        return False, "Diagram code appears to be malformed (all on one line). This usually indicates an LLM formatting error."
    
    lines = [line.strip() for line in mermaid_code.split('\n') if line.strip()]
    
    # Check for valid diagram type
    first_line = lines[0].lower()
    valid_starts = ['flowchart', 'graph', 'sequencediagram', 'classDiagram', 'stateDiagram']
    if not any(first_line.startswith(start) for start in valid_starts):
        valid_starts_str = ', '.join(valid_starts)
        return False, f"Invalid diagram type. Must start with one of: {valid_starts_str}"
    
    # Check for common syntax issues
    for i, line in enumerate(lines):
        # Check for unmatched brackets/parentheses
        if line.count('[') != line.count(']'):
            return False, f"Unmatched square brackets on line {i+1}: {line}"
        if line.count('(') != line.count(')'):
            return False, f"Unmatched parentheses on line {i+1}: {line}"
        if line.count('{') != line.count('}'):
            return False, f"Unmatched curly braces on line {i+1}: {line}"
        
        # Skip arrow validation as Mermaid has many valid arrow syntaxes
        # (-->, ->>, ->, -->>:, etc.) and validation was too restrictive
    
    # Check for subgraph matching (only for flowcharts, not sequence diagrams)
    if first_line.startswith('flowchart') or first_line.startswith('graph'):
        subgraph_count = sum(1 for line in lines if line.strip().startswith('subgraph'))
        end_count = sum(1 for line in lines if line.strip() == 'end')
        if subgraph_count != end_count:
            return False, f"Mismatched subgraph/end statements: {subgraph_count} subgraphs, {end_count} ends"
    
    # For sequence diagrams, check alt/else/end matching
    elif first_line.startswith('sequencediagram'):
        alt_count = sum(1 for line in lines if line.strip().startswith('alt '))
        else_count = sum(1 for line in lines if line.strip().startswith('else'))
        end_count = sum(1 for line in lines if line.strip() == 'end')
        
        # Each alt block should have one end, else blocks don't need separate ends
        if alt_count != end_count:
            return False, f"Mismatched alt/end statements in sequence diagram: {alt_count} alt blocks, {end_count} end statements"
    
    return True, ""

def _clean_mermaid_code(mermaid_code: str) -> str:
    """Clean and format Mermaid code to ensure proper syntax."""
    if not mermaid_code:
        return "flowchart TB\n    error[No diagram generated]"
    
    # Remove any markdown code blocks
    code = mermaid_code.strip()
    if code.startswith('```mermaid'):
        code = code.replace('```mermaid', '').replace('```', '').strip()
    elif code.startswith('```'):
        code = code.replace('```', '').strip()
    
    # Handle malformed code that's all on one line or has missing line breaks
    # Look for common Mermaid patterns and add line breaks
    if '\n' not in code or (len(code.split('\n')) < 3 and len(code) > 100):
        # For severely malformed code, return a simple fallback
        # This handles cases where the LLM output is completely concatenated
        return """flowchart TB
    error[Diagram Generation Error]
    note[The LLM generated malformed diagram code]
    
    error --> note
    
    fix1[Try generating again]
    fix2[Switch to OpenAI provider]
    fix3[Simplify your requirement]
    
    note --> fix1
    note --> fix2
    note --> fix3"""
    
    # Basic cleaning: fix common issues
    import re
    
    lines = code.split('\n')
    cleaned_lines = []
    
    # Detect diagram type
    first_line = lines[0].lower().strip() if lines else ""
    is_sequence_diagram = first_line.startswith('sequencediagram')
    
    for i, line in enumerate(lines):
        # Skip empty lines and comments
        if not line.strip() or line.strip().startswith('%%'):
            cleaned_lines.append(line)
            continue
        
        # For sequence diagrams, remove stray 'end' statements that don't belong to alt blocks
        if is_sequence_diagram and line.strip() == 'end':
            # Look backwards to see if there's a matching 'alt' without an 'end'
            alt_count = 0
            end_count = 0
            for prev_line in cleaned_lines:
                if prev_line.strip().startswith('alt '):
                    alt_count += 1
                elif prev_line.strip() == 'end':
                    end_count += 1
            
            # Only keep this 'end' if we have more 'alt' than 'end' statements
            if alt_count > end_count:
                cleaned_lines.append(line)
            # Otherwise skip this stray 'end' statement
            continue
            
        # For flowchart arrows, ensure proper spacing
        if not is_sequence_diagram and '-->' in line and not ('-->>' in line or '-->|' in line):
            # Only fix simple arrows in flowcharts, not sequence diagrams or labeled arrows
            line = re.sub(r'(\w+)-->(\w+)', r'\1 --> \2', line)
        
        cleaned_lines.append(line)
    
    code = '\n'.join(cleaned_lines)
    
    # If still looks malformed, return a fallback
    lines = [line.strip() for line in code.split('\n') if line.strip()]
    if len(lines) < 2:
        return """flowchart TB
    error[Diagram Generation Error]
    note[The generated diagram had formatting issues]
    
    error --> note
    
    note2[Please try generating again or use a different LLM provider]
    note --> note2"""
    
    # Check if it starts with a flowchart declaration
    first_line = lines[0].lower()
    if not (first_line.startswith('flowchart') or first_line.startswith('graph') or first_line.startswith('sequencediagram')):
        lines.insert(0, 'flowchart TB')
    
    # Add proper indentation for non-declaration lines
    formatted_lines = []
    for i, line in enumerate(lines):
        if (i == 0 or 
            line.startswith('subgraph') or 
            line.startswith('end') or
            line.startswith('participant') or
            line.lower().startswith('flowchart') or
            line.lower().startswith('sequencediagram') or
            line.startswith('%%')):  # Comments
            formatted_lines.append(line)
        else:
            # Add indentation if not already present
            if not line.startswith('    ') and not line.startswith('\t'):
                formatted_lines.append('    ' + line)
            else:
                formatted_lines.append(line)
    
    result = '\n'.join(formatted_lines)
    
    # Validate the final result
    is_valid, error_msg = _validate_mermaid_syntax(result)
    if not is_valid:
        return f"""flowchart TB
    error[Diagram Syntax Error]
    details[{error_msg}]
    
    error --> details
    
    note[Please try generating again with a different LLM provider]
    details --> note"""
    
    return result

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
    
    user --> scanner
    scanner --> api
    api --> db
    api --> erp

CRITICAL FORMATTING REQUIREMENTS:
1. Each line must be on a separate line with proper line breaks
2. Use 4 spaces for indentation of nodes and connections
3. Put each node definition and connection on its own line
4. Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)
5. Ensure proper spacing and line breaks between elements"""

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
        return _clean_mermaid_code(response.strip())
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

CRITICAL FORMATTING REQUIREMENTS:
1. Each line must be on a separate line with proper line breaks
2. Use 4 spaces for indentation of nodes and connections
3. Use 8 spaces for indentation inside subgraphs
4. Put each node definition and connection on its own line
5. Add blank lines between major sections for readability
6. Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)"""

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
        return _clean_mermaid_code(response.strip())
    except Exception as e:
        return f"""flowchart TB
  system[System]
  error[Container diagram generation failed: {str(e)}]
  
  system --> error"""

async def build_tech_stack_wiring_diagram(requirement: str, recommendations: List[Dict]) -> str:
    """Build a technical wiring diagram showing how tech stack components connect and interact."""
    
    # Extract tech stack from recommendations
    tech_stack = []
    if recommendations:
        for rec in recommendations:
            if isinstance(rec, dict) and 'tech_stack' in rec:
                tech_stack.extend(rec['tech_stack'])
            elif hasattr(rec, 'tech_stack'):
                tech_stack.extend(rec.tech_stack)
    
    # Remove duplicates while preserving order
    seen = set()
    unique_tech_stack = []
    for tech in tech_stack:
        if tech not in seen:
            seen.add(tech)
            unique_tech_stack.append(tech)
    
    tech_stack_str = ', '.join(unique_tech_stack) if unique_tech_stack else 'Python, FastAPI, PostgreSQL, Redis'

    prompt = f"""Generate a Mermaid technical wiring diagram showing how technology components connect and interact for this automation requirement:

REQUIREMENT: {requirement}

TECHNOLOGY STACK: {tech_stack_str}

Create a technical wiring diagram that shows:
1. Data flow between components (arrows with labels)
2. API connections and protocols (HTTP, REST, WebSocket, etc.)
3. Database connections and data storage
4. External integrations and third-party services
5. Message queues and async processing flows
6. Authentication and security layers
7. Monitoring and logging connections

Use Mermaid flowchart syntax with:
- Rectangles for services: service[Service Name]
- Cylinders for databases: db[(Database)]
- Diamonds for decision points: decision{{Decision}}
- Circles for external systems: external((External API))
- Hexagons for queues: queue{{{{Message Queue}}}}

Show technical details like:
- HTTP/REST connections: A -->|REST API| B
- Database queries: API -->|SQL Query| DB
- Message passing: Service -->|Publish| Queue
- Authentication: User -->|OAuth2| Auth
- Monitoring: All -->|Metrics| Monitor

Example format:
flowchart TB
    user[User Interface]
    api[FastAPI Server]
    db[(PostgreSQL)]
    redis[(Redis Cache)]
    queue{{{{Message Queue}}}}
    external((External API))
    monitor[Monitoring]
    
    user -->|HTTP Request| api
    api -->|SQL Query| db
    api -->|Cache Check| redis
    api -->|Async Task| queue
    queue -->|Process| worker[Background Worker]
    worker -->|API Call| external
    api -->|Metrics| monitor
    db -->|Logs| monitor

Focus on the EXACT technologies listed above and show realistic technical connections.

CRITICAL FORMATTING REQUIREMENTS:
1. Start with "flowchart TB" on its own line
2. Put each node definition on a separate line with 4-space indentation
3. Put each connection on a separate line with 4-space indentation
4. Use proper Mermaid syntax with spaces around arrows
5. Example of correct formatting:

flowchart TB
    user[User Interface]
    api[FastAPI Server]
    db[(PostgreSQL)]
    
    user -->|HTTP Request| api
    api -->|SQL Query| db

IMPORTANT: Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks).
Ensure each line is properly separated and indented."""

    try:
        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            # Create a more sophisticated fake diagram based on actual tech stack
            tech_list = unique_tech_stack if unique_tech_stack else ['Python', 'FastAPI', 'PostgreSQL', 'Redis']
            
            # Identify component types (ensure all items are strings)
            safe_tech_list = []
            for t in tech_list:
                if isinstance(t, dict):
                    tech_name = t.get('name') or t.get('technology') or str(t)
                    safe_tech_list.append(tech_name)
                elif not isinstance(t, str):
                    safe_tech_list.append(str(t))
                else:
                    safe_tech_list.append(t)
            
            languages = [t for t in safe_tech_list if t.lower() in ['python', 'javascript', 'java', 'node.js']]
            frameworks = [t for t in safe_tech_list if t.lower() in ['fastapi', 'django', 'flask', 'express', 'react']]
            databases = [t for t in safe_tech_list if t.lower() in ['postgresql', 'mysql', 'mongodb', 'redis', 'sqlite']]
            services = [t for t in safe_tech_list if t.lower() in ['twilio', 'oauth2', 'docker', 'aws', 'kubernetes']]
            
            diagram_parts = ["flowchart TB"]
            
            # Add main components
            if frameworks:
                diagram_parts.append(f"    api[{frameworks[0]} API]")
            else:
                diagram_parts.append("    api[API Server]")
                
            if databases:
                for i, db in enumerate(databases):
                    # db is already a string from safe_tech_list
                    if 'redis' in db.lower():
                        diagram_parts.append(f"    cache[{db} Cache]")
                    else:
                        diagram_parts.append(f"    db{i}[({db})]")
            
            diagram_parts.append("    user[User Interface]")
            
            # Add external services
            for service in services:
                # service is already a string from safe_tech_list
                if service.lower() not in ['docker', 'kubernetes']:
                    diagram_parts.append(f"    {service.lower().replace(' ', '_')}(({service}))")
            
            # Add connections
            diagram_parts.append("")
            diagram_parts.append("    user -->|HTTP Request| api")
            
            if databases:
                for i, db in enumerate(databases):
                    # db is already a string from safe_tech_list
                    if 'redis' in db.lower():
                        diagram_parts.append("    api -->|Cache Check| cache")
                    else:
                        diagram_parts.append(f"    api -->|SQL Query| db{i}")
            
            for service in services:
                # service is already a string from safe_tech_list
                if service.lower() not in ['docker', 'kubernetes']:
                    service_key = service.lower().replace(' ', '_')
                    if 'oauth' in service.lower():
                        diagram_parts.append(f"    user -->|Authentication| {service_key}")
                    elif 'twilio' in service.lower():
                        diagram_parts.append(f"    api -->|SMS/Voice| {service_key}")
                    else:
                        diagram_parts.append(f"    api -->|API Call| {service_key}")
            
            return '\n'.join(diagram_parts)
        
        response = await make_llm_request(prompt, provider_config, purpose="tech_stack_wiring_diagram")
        # Clean and format the Mermaid code
        return _clean_mermaid_code(response.strip())
    except Exception as e:
        return f"""flowchart TB
    error[Tech Stack Wiring Diagram]
    note[Generation failed: {str(e)}]
    
    error --> note
    
    subgraph "Planned Tech Stack"
        """ + tech_stack_str.replace(', ', '\n        ') + """
    end"""

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

Example format:
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

CRITICAL FORMATTING REQUIREMENTS:
1. Start with "sequenceDiagram" on its own line
2. Put each participant definition on a separate line with 4-space indentation
3. Put each message/interaction on a separate line with 4-space indentation
4. Use 8-space indentation inside alt/else blocks
5. IMPORTANT: Only use "end" to close "alt" blocks - each "alt" needs exactly one "end"
6. Do NOT add extra "end" statements - they are only for closing alt/else blocks
7. Add blank lines between major sections for readability
8. Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)"""

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
        return _clean_mermaid_code(response.strip())
    except Exception as e:
        return f"""sequenceDiagram
  participant U as User
  participant E as Error
  
  U->>E: Sequence diagram generation failed: {str(e)}"""


async def build_infrastructure_diagram(requirement: str, recommendations: List[Dict]) -> Dict[str, Any]:
    """Build an infrastructure diagram specification using LLM based on the specific requirement."""
    prompt = f"""Generate an infrastructure diagram specification for this automation requirement:

REQUIREMENT: {requirement}

RECOMMENDATIONS: {recommendations[0].get('reasoning', 'No recommendations available') if recommendations else 'No recommendations available'}

Create a JSON specification for an infrastructure diagram showing:
- Cloud providers (AWS, GCP, Azure) or on-premises components
- Compute services (Lambda, EC2, Functions, VMs)
- Databases (RDS, DynamoDB, SQL, etc.)
- Storage (S3, GCS, Blob Storage)
- Networking (API Gateway, Load Balancers)
- Integration services (SQS, Pub/Sub, Service Bus)
- External SaaS services

Return a JSON object with this structure:
{{
  "title": "Infrastructure Diagram Title",
  "clusters": [
    {{
      "provider": "aws|gcp|azure|k8s|onprem",
      "name": "Cluster Name",
      "nodes": [
        {{"id": "unique_id", "type": "component_type", "label": "Display Label"}}
      ]
    }}
  ],
  "nodes": [
    {{"id": "external_id", "type": "component_type", "provider": "provider", "label": "External Service"}}
  ],
  "edges": [
    ["source_id", "target_id", "connection_label"]
  ]
}}

Component types by provider:
- AWS: lambda, ec2, rds, dynamodb, s3, apigateway, sqs, sns
- GCP: functions, gce, sql, firestore, gcs, loadbalancing
- Azure: functions, vm, sql, cosmosdb, storage, loadbalancer
- OnPrem: server, postgresql, mysql, mongodb, redis, nginx
- SaaS: auth0, okta, slack, teams, datadog

IMPORTANT: Return ONLY valid JSON without markdown formatting."""

    try:
        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            # Return a sample infrastructure spec for fake provider
            return {
                "title": "Sample Infrastructure",
                "clusters": [
                    {
                        "provider": "aws",
                        "name": "AWS Cloud",
                        "nodes": [
                            {"id": "api_gateway", "type": "apigateway", "label": "API Gateway"},
                            {"id": "lambda_func", "type": "lambda", "label": "Lambda Function"},
                            {"id": "database", "type": "dynamodb", "label": "Database"}
                        ]
                    }
                ],
                "nodes": [
                    {"id": "user", "type": "server", "provider": "onprem", "label": "User"}
                ],
                "edges": [
                    ["user", "api_gateway", "HTTPS"],
                    ["api_gateway", "lambda_func", "invoke"],
                    ["lambda_func", "database", "query"]
                ]
            }
        
        response = await make_llm_request(prompt, provider_config, purpose="infrastructure_diagram")
        
        # Try to parse JSON response
        import json
        try:
            # Clean the response of any markdown formatting
            cleaned_response = response.strip()
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            cleaned_response = cleaned_response.strip()
            
            return json.loads(cleaned_response)
        except json.JSONDecodeError as e:
            app_logger.error(f"Failed to parse infrastructure diagram JSON: {e}")
            # Return fallback spec
            return {
                "title": "Infrastructure Diagram (Parsing Error)",
                "clusters": [
                    {
                        "provider": "aws",
                        "name": "System Components",
                        "nodes": [
                            {"id": "app", "type": "lambda", "label": "Application"},
                            {"id": "db", "type": "dynamodb", "label": "Database"}
                        ]
                    }
                ],
                "nodes": [],
                "edges": [["app", "db", "data"]]
            }
            
    except Exception as e:
        app_logger.error(f"Infrastructure diagram generation failed: {e}")
        return {
            "title": "Infrastructure Diagram (Error)",
            "clusters": [
                {
                    "provider": "aws",
                    "name": "Error",
                    "nodes": [
                        {"id": "error", "type": "lambda", "label": f"Generation failed: {str(e)}"}
                    ]
                }
            ],
            "nodes": [],
            "edges": []
        }

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
        return await self.make_api_request_with_timeout(method, endpoint, data, timeout=30.0)
    
    async def make_api_request_with_timeout(self, method: str, endpoint: str, data: Optional[Dict] = None, timeout: float = 30.0) -> Dict:
        """Make async API request to FastAPI backend with configurable timeout."""
        url = f"{API_BASE_URL}{endpoint}"
        
        async with httpx.AsyncClient(timeout=timeout) as client:
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
        provider_options = ["openai", "claude", "bedrock", "internal", "fake"]
        current_provider = st.sidebar.selectbox(
            "LLM Provider",
            provider_options,
            index=provider_options.index(st.session_state.provider_config['provider'])
        )
        
        # Initialize variables
        api_key = ""
        endpoint_url = ""
        region = ""
        model_options = []
        available_models = []
        
        # Provider-specific configuration
        if current_provider == "openai":
            api_key = st.sidebar.text_input(
                "OpenAI API Key",
                value=st.session_state.provider_config.get('api_key', ''),
                type="password",
                help="Your OpenAI API key"
            )
            
            # Discover models button
            if st.sidebar.button("🔍 Discover Models", key="discover_openai"):
                if api_key:
                    with st.sidebar:
                        with st.spinner("Discovering OpenAI models..."):
                            try:
                                response = asyncio.run(self.make_api_request(
                                    "POST",
                                    "/providers/models",
                                    {
                                        "provider": "openai",
                                        "api_key": api_key
                                    }
                                ))
                                if response.get('ok'):
                                    available_models = response.get('models', [])
                                    st.session_state[f'discovered_models_{current_provider}'] = available_models
                                    st.success(f"Discovered {len(available_models)} models!")
                                else:
                                    st.error(f"Failed to discover models: {response.get('message', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error discovering models: {str(e)}")
                else:
                    st.sidebar.warning("Please enter your API key first")
            
            # Use discovered models or fallback
            if f'discovered_models_{current_provider}' in st.session_state:
                available_models = st.session_state[f'discovered_models_{current_provider}']
                model_options = [model['id'] for model in available_models]
            else:
                # Fallback models
                model_options = ["gpt-4o", "gpt-4o-mini", "gpt-4-turbo", "gpt-4", "gpt-3.5-turbo"]
        
        elif current_provider == "claude":
            api_key = st.sidebar.text_input(
                "Anthropic API Key",
                value=st.session_state.provider_config.get('api_key', ''),
                type="password",
                help="Your Anthropic API key"
            )
            
            # Discover models button
            if st.sidebar.button("🔍 Discover Models", key="discover_claude"):
                if api_key:
                    with st.sidebar:
                        with st.spinner("Discovering Claude models..."):
                            try:
                                response = asyncio.run(self.make_api_request(
                                    "POST",
                                    "/providers/models",
                                    {
                                        "provider": "claude",
                                        "api_key": api_key
                                    }
                                ))
                                if response.get('ok'):
                                    available_models = response.get('models', [])
                                    st.session_state[f'discovered_models_{current_provider}'] = available_models
                                    st.success(f"Discovered {len(available_models)} models!")
                                else:
                                    st.error(f"Failed to discover models: {response.get('message', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error discovering models: {str(e)}")
                else:
                    st.sidebar.warning("Please enter your API key first")
            
            # Use discovered models or fallback
            if f'discovered_models_{current_provider}' in st.session_state:
                available_models = st.session_state[f'discovered_models_{current_provider}']
                model_options = [model['id'] for model in available_models]
            else:
                # Fallback models
                model_options = ["claude-3-5-sonnet-20241022", "claude-3-5-haiku-20241022", "claude-3-opus-20240229", "claude-3-sonnet-20240229", "claude-3-haiku-20240307"]
        
        elif current_provider == "bedrock":
            region = st.sidebar.selectbox(
                "AWS Region",
                ["us-east-1", "us-west-2", "eu-west-1", "eu-west-2", "ap-southeast-1"],
                index=0,
                help="AWS region for Bedrock service"
            )
            
            # Discover models button
            if st.sidebar.button("🔍 Discover Models", key="discover_bedrock"):
                with st.sidebar:
                    with st.spinner("Discovering Bedrock models..."):
                        try:
                            response = asyncio.run(self.make_api_request(
                                "POST",
                                "/providers/models",
                                {
                                    "provider": "bedrock",
                                    "region": region
                                }
                            ))
                            if response.get('ok'):
                                available_models = response.get('models', [])
                                st.session_state[f'discovered_models_{current_provider}'] = available_models
                                st.success(f"Discovered {len(available_models)} models!")
                            else:
                                st.error(f"Failed to discover models: {response.get('message', 'Unknown error')}")
                        except Exception as e:
                            st.error(f"Error discovering models: {str(e)}")
            
            # Use discovered models or fallback
            if f'discovered_models_{current_provider}' in st.session_state:
                available_models = st.session_state[f'discovered_models_{current_provider}']
                model_options = [model['id'] for model in available_models]
            else:
                # Fallback models
                model_options = ["anthropic.claude-3-sonnet-20240229-v1:0", "anthropic.claude-3-haiku-20240307-v1:0", "anthropic.claude-v2:1"]
        
        elif current_provider == "internal":
            endpoint_url = st.sidebar.text_input(
                "Endpoint URL",
                value=st.session_state.provider_config.get('endpoint_url', ''),
                help="URL of your internal LLM API endpoint"
            )
            api_key = st.sidebar.text_input(
                "API Key (Optional)",
                value=st.session_state.provider_config.get('api_key', ''),
                type="password",
                help="Optional API key for authentication"
            )
            
            # Discover models button
            if st.sidebar.button("🔍 Discover Models", key="discover_internal"):
                if endpoint_url:
                    with st.sidebar:
                        with st.spinner("Discovering internal models..."):
                            try:
                                response = asyncio.run(self.make_api_request(
                                    "POST",
                                    "/providers/models",
                                    {
                                        "provider": "internal",
                                        "endpoint_url": endpoint_url,
                                        "api_key": api_key if api_key else None
                                    }
                                ))
                                if response.get('ok'):
                                    available_models = response.get('models', [])
                                    st.session_state[f'discovered_models_{current_provider}'] = available_models
                                    st.success(f"Discovered {len(available_models)} models!")
                                else:
                                    st.error(f"Failed to discover models: {response.get('message', 'Unknown error')}")
                            except Exception as e:
                                st.error(f"Error discovering models: {str(e)}")
                else:
                    st.sidebar.warning("Please enter the endpoint URL first")
            
            # Use discovered models or fallback
            if f'discovered_models_{current_provider}' in st.session_state:
                available_models = st.session_state[f'discovered_models_{current_provider}']
                model_options = [model['id'] for model in available_models]
            else:
                # Fallback models
                model_options = ["default", "custom-model"]
        
        else:  # fake
            model_options = ["fake-llm"]
            st.sidebar.info("🎭 Using FakeLLM for testing - no API key required")
        
        # Model selection
        if model_options:
            current_model = st.session_state.provider_config.get('model', model_options[0])
            if current_model not in model_options:
                current_model = model_options[0]
            
            model = st.sidebar.selectbox(
                "Model",
                model_options,
                index=model_options.index(current_model) if current_model in model_options else 0,
                help="Select the model to use for this provider"
            )
            
            # Show model details if available
            if available_models:
                selected_model_info = next((m for m in available_models if m['id'] == model), None)
                if selected_model_info:
                    with st.sidebar.expander("ℹ️ Model Details"):
                        st.write(f"**Name:** {selected_model_info.get('name', 'N/A')}")
                        if selected_model_info.get('description'):
                            st.write(f"**Description:** {selected_model_info['description']}")
                        if selected_model_info.get('context_length'):
                            st.write(f"**Context Length:** {selected_model_info['context_length']:,} tokens")
                        if selected_model_info.get('capabilities'):
                            st.write(f"**Capabilities:** {', '.join(selected_model_info['capabilities'])}")
        else:
            model = "default"
        
        # Update session state
        st.session_state.provider_config.update({
            'provider': current_provider,
            'model': model,
            'api_key': api_key,
            'endpoint_url': endpoint_url,
            'region': region
        })
        
        # Debug options (for troubleshooting)
        with st.sidebar.expander("🔍 Debug Options"):
            st.session_state.show_diagram_debug = st.checkbox(
                "Show diagram debug info",
                value=st.session_state.get('show_diagram_debug', False),
                help="Show technical debug information on the Systems Diagram page"
            )
            st.session_state.show_qa_debug = st.checkbox(
                "Show Q&A debug info",
                value=st.session_state.get('show_qa_debug', False),
                help="Show debug information during question generation and answering"
            )
            st.session_state.debug_qa = st.checkbox(
                "Show Q&A answer status",
                value=st.session_state.get('debug_qa', False),
                help="Show detailed answer status for each Q&A question"
            )
            st.session_state.show_llm_debug = st.checkbox(
                "Show LLM analysis debug",
                value=st.session_state.get('show_llm_debug', False),
                help="Show detailed LLM analysis information in recommendations"
            )
        
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
        
        # Add constraints section
        st.subheader("🚫 Technology Constraints")
        
        col3, col4 = st.columns(2)
        
        with col3:
            restricted_technologies = st.text_area(
                "Restricted/Banned Technologies:",
                height=100,
                placeholder="Enter technologies that cannot be used, one per line:\nAzure\nOracle Database\nSalesforce\nWindows Server",
                help="List any technologies, platforms, or tools that are banned or unavailable in your organization"
            )
        
        with col4:
            required_integrations = st.text_area(
                "Required Integrations:",
                height=100,
                placeholder="Enter required systems to integrate with:\nActive Directory\nSAP\nExisting PostgreSQL\nAWS Lambda",
                help="List any existing systems or technologies that must be integrated with"
            )
        
        # Additional constraints
        with st.expander("🔒 Additional Constraints (Optional)"):
            col5, col6 = st.columns(2)
            
            with col5:
                compliance_requirements = st.multiselect(
                    "Compliance Requirements:",
                    ["GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA", "ISO-27001", "FedRAMP"],
                    help="Select applicable compliance standards"
                )
                
                data_sensitivity = st.selectbox(
                    "Data Sensitivity Level:",
                    ["", "Public", "Internal", "Confidential", "Restricted"],
                    help="Classification level of data being processed"
                )
            
            with col6:
                budget_constraints = st.selectbox(
                    "Budget Constraints:",
                    ["", "Low (Open source preferred)", "Medium (Some commercial tools OK)", "High (Enterprise solutions OK)"],
                    help="Budget level for technology solutions"
                )
                
                deployment_preference = st.selectbox(
                    "Deployment Preference:",
                    ["", "Cloud-only", "On-premises only", "Hybrid", "No preference"],
                    help="Preferred deployment model"
                )
        
        if st.button("🚀 Analyze Requirements", disabled=st.session_state.processing):
            if requirements_text.strip():
                # Parse restricted technologies and required integrations
                banned_tools = [tech.strip() for tech in restricted_technologies.split('\n') if tech.strip()] if restricted_technologies else []
                required_ints = [tech.strip() for tech in required_integrations.split('\n') if tech.strip()] if required_integrations else []
                
                # Build constraints object
                constraints = {}
                if banned_tools:
                    constraints["banned_tools"] = banned_tools
                if required_ints:
                    constraints["required_integrations"] = required_ints
                if compliance_requirements:
                    constraints["compliance_requirements"] = compliance_requirements
                if data_sensitivity:
                    constraints["data_sensitivity"] = data_sensitivity
                if budget_constraints:
                    constraints["budget_constraints"] = budget_constraints
                if deployment_preference:
                    constraints["deployment_preference"] = deployment_preference
                
                self.submit_requirements("text", {
                    "text": requirements_text,
                    "domain": domain if domain else None,
                    "pattern_types": pattern_types,
                    "constraints": constraints if constraints else None
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
            
            # Add constraints section for file upload too
            with st.expander("🚫 Technology Constraints (Optional)"):
                col1, col2 = st.columns(2)
                
                with col1:
                    restricted_technologies = st.text_area(
                        "Restricted/Banned Technologies:",
                        height=80,
                        placeholder="Azure\nOracle Database\nSalesforce",
                        help="Technologies that cannot be used",
                        key="file_restricted_tech"
                    )
                
                with col2:
                    required_integrations = st.text_area(
                        "Required Integrations:",
                        height=80,
                        placeholder="Active Directory\nExisting PostgreSQL\nAWS Lambda",
                        help="Systems that must be integrated with",
                        key="file_required_int"
                    )
            
            if st.button("🚀 Analyze File", disabled=st.session_state.processing):
                try:
                    content = uploaded_file.read().decode('utf-8')
                    
                    # Parse constraints
                    banned_tools = [tech.strip() for tech in restricted_technologies.split('\n') if tech.strip()] if restricted_technologies else []
                    required_ints = [tech.strip() for tech in required_integrations.split('\n') if tech.strip()] if required_integrations else []
                    
                    constraints = {}
                    if banned_tools:
                        constraints["banned_tools"] = banned_tools
                    if required_ints:
                        constraints["required_integrations"] = required_ints
                    
                    self.submit_requirements("file", {
                        "content": content,
                        "filename": uploaded_file.name,
                        "constraints": constraints if constraints else None
                    })
                except Exception as e:
                    st.error(f"Error reading file: {str(e)}")
    
    def handle_authentication_fallback(self, base_url: str, initial_auth_type: str) -> Optional[Dict[str, Any]]:
        """Handle authentication fallback with user prompts."""
        st.warning("🔄 Initial authentication failed. Let's try alternative methods.")
        
        # Show available fallback options
        fallback_options = []
        if initial_auth_type != "sso":
            fallback_options.append("sso")
        if initial_auth_type != "basic":
            fallback_options.append("basic")
        if initial_auth_type != "pat":
            fallback_options.append("pat")
        
        if not fallback_options:
            st.error("❌ No alternative authentication methods available.")
            return None
        
        st.info("🔐 Please try one of the following authentication methods:")
        
        # Create fallback form
        with st.form("auth_fallback_form"):
            fallback_auth_type = st.selectbox(
                "Alternative Authentication Method",
                options=fallback_options,
                format_func=lambda x: {
                    "sso": "🔐 SSO/Current Session (try Windows credentials)",
                    "basic": "👤 Username/Password (temporary, session-only)",
                    "pat": "🎫 Personal Access Token"
                }[x],
                help="Select an alternative authentication method"
            )
            
            # Dynamic fields based on selected fallback method
            fallback_credentials = {}
            
            if fallback_auth_type == "basic":
                st.warning("⚠️ Credentials will be stored securely for this session only and will not be saved.")
                col1, col2 = st.columns(2)
                with col1:
                    fallback_username = st.text_input(
                        "Username",
                        placeholder="your-username",
                        help="Your Jira username"
                    )
                with col2:
                    fallback_password = st.text_input(
                        "Password",
                        type="password",
                        help="Your Jira password"
                    )
                fallback_credentials = {
                    "username": fallback_username,
                    "password": fallback_password
                }
            
            elif fallback_auth_type == "pat":
                fallback_pat = st.text_input(
                    "Personal Access Token",
                    type="password",
                    help="Generate from Jira Data Center: Profile > Personal Access Tokens"
                )
                fallback_credentials = {
                    "personal_access_token": fallback_pat
                }
            
            elif fallback_auth_type == "sso":
                st.info("🔐 SSO authentication will attempt to use your current browser session or Windows credentials")
                fallback_credentials = {"use_sso": True}
            
            try_fallback = st.form_submit_button("🔄 Try Alternative Authentication", type="primary")
            
            if try_fallback:
                # Validate fallback credentials
                validation_errors = []
                
                if fallback_auth_type == "basic":
                    if not fallback_credentials.get("username"):
                        validation_errors.append("Username is required")
                    if not fallback_credentials.get("password"):
                        validation_errors.append("Password is required")
                elif fallback_auth_type == "pat":
                    if not fallback_credentials.get("personal_access_token"):
                        validation_errors.append("Personal Access Token is required")
                
                if validation_errors:
                    st.error("❌ Please fix the following issues:\n" + "\n".join(f"• {error}" for error in validation_errors))
                    return None
                
                # Return fallback configuration
                return {
                    "auth_type": fallback_auth_type,
                    **fallback_credentials
                }
        
        return None
    
    def show_authentication_status(self, auth_result: Dict[str, Any]):
        """Display authentication status and guidance."""
        if auth_result.get("success"):
            st.success("✅ Authentication successful!")
            
            auth_type = auth_result.get("auth_type", "unknown")
            auth_type_names = {
                "api_token": "API Token",
                "pat": "Personal Access Token",
                "sso": "SSO/Current Session",
                "basic": "Username/Password"
            }
            
            st.info(f"🔐 Authenticated using: {auth_type_names.get(auth_type, auth_type)}")
            
            # Show security information for basic auth
            if auth_type == "basic":
                st.warning("⚠️ Username/password credentials are stored securely for this session only and will be cleared when you close the browser.")
        else:
            st.error("❌ Authentication failed")
            
            error_message = auth_result.get("error_message", "Unknown error")
            st.error(f"Error: {error_message}")
            
            # Show guidance based on error type
            if "401" in error_message or "unauthorized" in error_message.lower():
                st.info("💡 **Authentication Tips:**")
                st.write("• Verify your credentials are correct and not expired")
                st.write("• For Data Center: try Personal Access Token instead of API token")
                st.write("• For SSO: ensure you're logged into Jira in another browser tab")
                st.write("• Check if your account has the necessary permissions")
            elif "403" in error_message or "forbidden" in error_message.lower():
                st.info("💡 **Permission Tips:**")
                st.write("• Your account may not have permission to access this Jira instance")
                st.write("• Contact your Jira administrator to verify your access level")
                st.write("• Ensure you're using the correct Jira instance URL")
            elif "timeout" in error_message.lower() or "connection" in error_message.lower():
                st.info("💡 **Connection Tips:**")
                st.write("• Check your network connection")
                st.write("• Verify the Jira URL is correct and accessible")
                st.write("• Try increasing the timeout value in Network Configuration")
                st.write("• Check if you need proxy settings for your network")

    def render_jira_input(self):
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
                        test_payload = {
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
                        
                        # Remove None values to avoid API issues
                        test_payload = {k: v for k, v in test_payload.items() if v is not None}
                        
                        test_result = asyncio.run(self.make_api_request("POST", "/jira/test", test_payload))
                        
                        if test_result and test_result.get("ok"):
                            st.success("✅ Jira connection successful!")
                            
                            # Display deployment information if available
                            deployment_info = test_result.get("deployment_info")
                            if deployment_info:
                                with st.expander("📋 Connection Details", expanded=True):
                                    col1, col2 = st.columns(2)
                                    
                                    with col1:
                                        st.write(f"**Deployment Type:** {deployment_info.get('deployment_type', 'Unknown').title()}")
                                        st.write(f"**Version:** {deployment_info.get('version', 'Unknown')}")
                                        if deployment_info.get('build_number'):
                                            st.write(f"**Build:** {deployment_info['build_number']}")
                                    
                                    with col2:
                                        st.write(f"**API Version:** {test_result.get('api_version_detected', 'Unknown')}")
                                        auth_methods = test_result.get("auth_methods_available", [])
                                        if auth_methods:
                                            st.write(f"**Available Auth Methods:** {', '.join(auth_methods)}")
                                    
                                    if deployment_info.get('supports_sso'):
                                        st.info("🔐 This instance supports SSO authentication")
                                    if deployment_info.get('supports_pat'):
                                        st.info("🎫 This instance supports Personal Access Tokens")
                        else:
                            error_msg = test_result.get("message", "Unknown error") if test_result else "Connection failed"
                            st.error(f"❌ Connection failed: {error_msg}")
                            
                            # Display detailed error information if available
                            error_details = test_result.get("error_details") if test_result else None
                            if error_details:
                                with st.expander("🔍 Troubleshooting Information", expanded=False):
                                    st.write(f"**Error Type:** {error_details.get('error_type', 'Unknown')}")
                                    if error_details.get('error_code'):
                                        st.write(f"**Error Code:** {error_details['error_code']}")
                                    
                                    troubleshooting_steps = error_details.get('troubleshooting_steps', [])
                                    if troubleshooting_steps:
                                        st.write("**Troubleshooting Steps:**")
                                        for step in troubleshooting_steps:
                                            st.write(f"• {step}")
                                    
                                    doc_links = error_details.get('documentation_links', [])
                                    if doc_links:
                                        st.write("**Documentation:**")
                                        for link in doc_links:
                                            st.write(f"• {link}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
        
        # Handle fetch ticket
        if fetch_ticket:
            # Validate required fields based on auth type
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
                        # Prepare request payload with all configuration options
                        fetch_payload = {
                            "ticket_key": jira_ticket_key,
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
                        
                        # Remove None values to avoid API issues
                        fetch_payload = {k: v for k, v in fetch_payload.items() if v is not None}
                        
                        fetch_result = asyncio.run(self.make_api_request("POST", "/jira/fetch", fetch_payload))
                        
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
            # Validate required fields based on auth type
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
                    # Use the ingest endpoint with Jira source
                    payload = {
                        "ticket_key": jira_ticket_key,
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
                    
                    # Remove None values to avoid API issues
                    payload = {k: v for k, v in payload.items() if v is not None}
                    
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
                        "pattern_types": payload.get("pattern_types", []),
                        "constraints": payload.get("constraints", {})
                    }
                elif source == "file":
                    st.session_state.requirements = {
                        "description": payload.get("content", ""),
                        "filename": payload.get("filename"),
                        "constraints": payload.get("constraints", {})
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
        
        # Debug info (hidden by default)
        if st.session_state.get('show_debug', False):
            st.write(f"**Debug:** Checking status for session: {st.session_state.session_id[:8]}...")
        
        st.header("📊 Processing Progress")
        
        try:
            # Status endpoint should be fast, but add retry logic for robustness
            max_retries = 3
            for attempt in range(max_retries):
                try:
                    response = asyncio.run(self.make_api_request(
                        "GET",
                        f"/status/{st.session_state.session_id}"
                    ))
                    break  # Success, exit retry loop
                except Exception as e:
                    if attempt == max_retries - 1:  # Last attempt
                        raise e
                    else:
                        time.sleep(1)  # Wait 1 second before retry
            
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
            error_msg = str(e)
            if "404" in error_msg or "Session not found" in error_msg:
                st.error("❌ Session expired or not found. Please start a new analysis.")
                if st.button("🔄 Start New Analysis"):
                    st.session_state.clear()
                    st.rerun()
            elif "timeout" in error_msg.lower():
                st.error("❌ Status check timed out. The system may be under heavy load.")
                st.info("💡 Please wait a moment and the page will refresh automatically.")
            else:
                st.error(f"❌ Error getting status: {error_msg}")
                st.info("🔄 The page will continue to refresh automatically.")
    
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
                # Debug message (hidden by default)
                if st.session_state.get('show_qa_debug', False):
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
        
        # Debug toggle (moved to sidebar with other debug options)
        
        # Show questions if we have them
        if st.session_state.qa_questions:
            answers = {}
            for idx, q in enumerate(st.session_state.qa_questions):
                # Create unique key using index and question hash to prevent Streamlit key conflicts
                # This handles cases where multiple questions might have the same field ID
                unique_key = f"qa_{idx}_{hash(q['question'])}"
                
                if q["type"] == "text":
                    # Use text_area for longer responses and to avoid password manager interference
                    question_text = q["question"]
                    # Add context to prevent password manager confusion
                    if "api" in question_text.lower() or "password" in question_text.lower():
                        help_text = "This is not a password field - please describe your requirements"
                    else:
                        help_text = "Please provide details to help improve the recommendation accuracy"
                    
                    answers[q["id"]] = st.text_area(
                        question_text, 
                        key=unique_key,
                        height=100,
                        help=help_text,
                        placeholder="Enter your response here..."
                    )
                elif q["type"] == "select":
                    answers[q["id"]] = st.selectbox(q["question"], q["options"], key=unique_key)
            
            # Check if all questions are answered
            answered_count = sum(1 for answer in answers.values() if answer and answer.strip())
            total_questions = len(st.session_state.qa_questions)
            
            # Debug information
            if st.session_state.get('debug_qa', False):
                st.write("**Debug - Answer Status:**")
                for q_id, answer in answers.items():
                    status = "✅" if answer and answer.strip() else "❌"
                    st.write(f"{status} {q_id}: '{answer}'")
            
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
                # Show loading message for long operations
                with st.spinner("🔄 Generating recommendations... This may take up to 2 minutes for complex requirements."):
                    response = asyncio.run(self.make_api_request_with_timeout(
                        "POST",
                        "/recommend",
                        {"session_id": st.session_state.session_id, "top_k": 3},
                        timeout=120.0  # 2 minutes for recommendation generation
                    ))
                st.session_state.recommendations = response
            except Exception as e:
                error_msg = str(e)
                if "ReadTimeout" in error_msg or "timeout" in error_msg.lower():
                    st.error("❌ Request timed out. The system is still processing your request. Please try refreshing in a moment.")
                    st.info("💡 Complex requirements with novel technologies may take longer to analyze and create new patterns.")
                else:
                    st.error(f"❌ Error loading recommendations: {error_msg}")
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
                
                # Show constraints if any were specified
                constraints = req.get('constraints', {})
                if constraints:
                    st.write("**🚫 Applied Constraints:**")
                    
                    if constraints.get('banned_tools'):
                        # Unescape HTML entities for display
                        import html
                        banned_tech_display = [html.unescape(tech) for tech in constraints['banned_tools']]
                        st.write(f"  • **Banned Technologies:** {', '.join(banned_tech_display)}")
                    
                    if constraints.get('required_integrations'):
                        # Unescape HTML entities for display
                        import html
                        required_int_display = [html.unescape(integration) for integration in constraints['required_integrations']]
                        st.write(f"  • **Required Integrations:** {', '.join(required_int_display)}")
                    
                    if constraints.get('compliance_requirements'):
                        st.write(f"  • **Compliance:** {', '.join(constraints['compliance_requirements'])}")
                    
                    if constraints.get('data_sensitivity'):
                        st.write(f"  • **Data Sensitivity:** {constraints['data_sensitivity']}")
                    
                    if constraints.get('budget_constraints'):
                        st.write(f"  • **Budget:** {constraints['budget_constraints']}")
                    
                    if constraints.get('deployment_preference'):
                        st.write(f"  • **Deployment:** {constraints['deployment_preference']}")
                
                # Show any additional requirement fields
                for key, value in req.items():
                    if key not in ['description', 'domain', 'pattern_types', 'jira_key', 'filename', 'source', 'constraints'] and value:
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
            
            # Debug: Show what LLM analysis we have (hidden by default)
            if st.session_state.get('show_llm_debug', False):
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
            self._render_formatted_text(architecture_explanation)
        
        # Detailed reasoning
        if rec.get('reasoning'):
            st.subheader("💭 Technical Analysis")
            with st.expander("View detailed technical reasoning", expanded=False):
                self._render_formatted_text(rec['reasoning'])
        
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
        
        # Import tech stack generator for better categorization
        try:
            from app.services.tech_stack_generator import TechStackGenerator
            generator = TechStackGenerator()
            categorized_tech = generator.categorize_tech_stack_with_descriptions(tech_stack)
            
            # Display categorized tech stack with descriptions
            for category_name, category_info in categorized_tech.items():
                techs = category_info["technologies"]
                description = category_info["description"]
                
                with st.expander(f"{category_name} ({len(techs)})", expanded=True):
                    # Show category description
                    st.write(f"*{description}*")
                    st.write("")  # Add spacing
                    
                    # Display technologies in columns with descriptions
                    cols = st.columns(min(len(techs), 3))
                    for i, tech in enumerate(techs):
                        with cols[i % 3]:
                            # tech is now a dict with name, description, etc.
                            if isinstance(tech, dict):
                                tech_name = tech.get("name", "Unknown")
                                tech_description = tech.get("description", f"Technology component: {tech_name}")
                            else:
                                # Fallback for string tech names
                                tech_name = str(tech)
                                tech_description = generator.get_technology_description(tech_name)
                            
                            st.info(f"**{tech_name}**\n\n{tech_description}")
            
        except ImportError:
            # Fallback to simple categorization if import fails
            self._render_simple_tech_stack(tech_stack)
    
    def _render_simple_tech_stack(self, tech_stack: List[str]):
        """Simple fallback tech stack rendering."""
        # Basic categorization
        categories = {
            "Backend/API": ["Python", "FastAPI", "Flask", "Django", "Node.js", "Express"],
            "Database": ["PostgreSQL", "MySQL", "MongoDB", "SQLAlchemy", "Redis"],
            "Message Queue": ["Celery", "RabbitMQ", "Apache Kafka", "AWS SQS"],
            "Cloud/Infrastructure": ["Docker", "Kubernetes", "AWS", "Azure", "GCP"],
            "Communication": ["Twilio", "OAuth 2.0", "JWT", "Webhook", "REST API"],
            "Testing": ["Pytest", "Jest", "Selenium", "Postman"],
            "Data Processing": ["Pandas", "NumPy", "Jupyter", "Matplotlib"]
        }
        
        # Group technologies by category
        categorized_tech = {}
        uncategorized = []
        
        for tech in tech_stack:
            # Ensure tech is a string (handle cases where it might be a dict)
            if isinstance(tech, dict):
                tech_name = tech.get('name') or tech.get('technology') or str(tech)
                tech = tech_name
            elif not isinstance(tech, str):
                tech = str(tech)
            
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
            with st.expander(f"{category} ({len(techs)})", expanded=True):
                cols = st.columns(min(len(techs), 3))
                for i, tech in enumerate(techs):
                    with cols[i % 3]:
                        st.info(f"**{tech}**")
        
        # Show uncategorized technologies with better formatting
        if uncategorized:
            with st.expander(f"Other Technologies ({len(uncategorized)})", expanded=True):
                st.write("*Additional specialized tools and technologies*")
                st.write("")  # Add spacing
                
                cols = st.columns(min(len(uncategorized), 3))
                for i, tech in enumerate(uncategorized):
                    with cols[i % 3]:
                        st.info(f"**{tech}**\n\nSpecialized technology component")
    
    def _render_formatted_text(self, text: str):
        """Render text with proper formatting and paragraph breaks."""
        if not text:
            return
        
        # Split text into paragraphs and format
        paragraphs = text.split('\n\n')
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            # Check if this looks like a section header (starts with keywords)
            if any(paragraph.lower().startswith(keyword) for keyword in 
                   ['main challenges:', 'key challenges:', 'challenges:', 'implementation:', 
                    'architecture:', 'data flow:', 'integration:', 'security:', 'monitoring:']):
                # Format as a subheader
                st.write(f"**{paragraph}**")
            else:
                # Regular paragraph
                st.write(paragraph)
            
            # Add some spacing between paragraphs
            st.write("")
    
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
        
        # Export format selection
        export_format = st.selectbox(
            "Choose export format:",
            options=[
                ("comprehensive", "📊 Comprehensive Report - Complete analysis with all details"),
                ("json", "📄 JSON - Structured data format"),
                ("md", "📝 Markdown - Basic summary format")
            ],
            format_func=lambda x: x[1],
            help="Select the type of export you need"
        )
        
        format_key = export_format[0]
        
        # Export button with format-specific styling
        if format_key == "comprehensive":
            button_text = "📊 Generate Comprehensive Report"
            button_help = "Includes: Original Requirements, Feasibility Assessment, Recommended Solutions, Tech Stack Analysis, Architecture Explanations, Pattern Matches, Q&A History, and Implementation Guidance"
        elif format_key == "json":
            button_text = "📄 Export as JSON"
            button_help = "Structured data format suitable for integration with other systems"
        else:
            button_text = "📝 Export as Markdown"
            button_help = "Basic summary in Markdown format"
        
        if st.button(button_text, help=button_help, use_container_width=True):
            self.export_results(format_key)
        
        # Format descriptions
        with st.expander("ℹ️ Export Format Details"):
            st.markdown("""
            **📊 Comprehensive Report:**
            - Complete analysis with all page data
            - Original requirements and constraints
            - Detailed feasibility assessment
            - Tech stack recommendations with explanations
            - Architecture analysis and patterns
            - Pattern matching results
            - Q&A history and analysis
            - Implementation guidance and next steps
            - Risk assessment and success metrics
            
            **📄 JSON Format:**
            - Structured data for system integration
            - All session data in machine-readable format
            - Suitable for APIs and data processing
            
            **📝 Markdown Format:**
            - Basic summary in readable text format
            - Core recommendations and analysis
            - Suitable for documentation and sharing
            """)
    
    def export_results(self, format_type: str):
        """Export results in the specified format."""
        try:
            # Format-specific messaging
            if format_type == "comprehensive":
                spinner_text = "🔄 Generating comprehensive report with AI analysis..."
                success_text = "✅ Comprehensive report generated successfully!"
            elif format_type == "json":
                spinner_text = "📄 Exporting structured data..."
                success_text = "✅ JSON export completed!"
            else:
                spinner_text = "📝 Generating markdown summary..."
                success_text = "✅ Markdown export completed!"
            
            with st.spinner(spinner_text):
                response = asyncio.run(self.make_api_request(
                    "POST",
                    "/export",
                    {
                        "session_id": st.session_state.session_id,
                        "format": format_type
                    }
                ))
                
                st.success(success_text)
                
                # Show file info
                file_info = response.get('file_info', {})
                if file_info:
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("File Size", f"{file_info.get('size_bytes', 0):,} bytes")
                    with col2:
                        st.metric("Format", format_type.upper())
                
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
                            
                            # Format-specific download button styling
                            if format_type == "comprehensive":
                                button_label = "📊 Download Comprehensive Report"
                                mime_type = "text/markdown"
                            elif format_type == "json":
                                button_label = "📄 Download JSON Data"
                                mime_type = "application/json"
                            else:
                                button_label = "📝 Download Markdown"
                                mime_type = "text/markdown"
                            
                            st.download_button(
                                label=button_label,
                                data=file_content,
                                file_name=filename,
                                mime=mime_type,
                                use_container_width=True
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
                
                # Show preview for comprehensive reports
                if format_type == "comprehensive":
                    with st.expander("📋 Report Preview"):
                        st.info("The comprehensive report includes:")
                        st.markdown("""
                        - **Executive Summary** with overall assessment
                        - **Original Requirements** with detailed breakdown
                        - **Feasibility Assessment** with confidence metrics
                        - **Recommended Solutions** with tech stack analysis
                        - **Technical Analysis** with architecture patterns
                        - **Pattern Matches** with detailed scoring
                        - **Q&A History** with complete interaction log
                        - **Implementation Guidance** with next steps and risk assessment
                        """)
        
        except Exception as e:
            st.error(f"❌ Export failed: {str(e)}")
            if format_type == "comprehensive":
                st.info("💡 If comprehensive export fails, try the basic Markdown or JSON export options.")
    
    def render_mermaid_diagrams(self):
        """Render Mermaid diagrams panel."""
        st.header("📊 System Diagrams")
        
        # Check if we have session data
        if not st.session_state.get('session_id'):
            st.info("Please submit a requirement first to generate diagrams.")
            return
        
        diagram_type = st.selectbox(
            "Select diagram type:",
            ["Context Diagram", "Container Diagram", "Sequence Diagram", "Tech Stack Wiring Diagram", "Infrastructure Diagram"]
        )
        
        # Show description for selected diagram type
        diagram_descriptions = {
            "Context Diagram": "🌐 **System Context**: Shows the system boundaries, users, and external systems it integrates with.",
            "Container Diagram": "📦 **System Containers**: Shows the internal components, services, and how they interact within the system.",
            "Sequence Diagram": "🔄 **Process Flow**: Shows the step-by-step sequence of interactions and decision points in the automation.",
            "Tech Stack Wiring Diagram": "🔌 **Technical Wiring**: Shows how all the recommended technologies connect, communicate, and pass data between each other. Like a blueprint for developers showing API calls, database connections, authentication flows, and service integrations.",
            "Infrastructure Diagram": "🏗️ **Infrastructure Architecture**: Shows cloud infrastructure components with vendor-specific icons (AWS, GCP, Azure). Displays compute, storage, database, and networking services with realistic cloud architecture patterns."
        }
        
        st.info(diagram_descriptions[diagram_type])
        
        # Get current session data
        requirements = st.session_state.get('requirements', {})
        recommendations_response = st.session_state.get('recommendations', {})
        provider_config = st.session_state.get('provider_config', {})
        
        # Extract recommendations list from the API response
        recommendations = recommendations_response.get('recommendations', []) if recommendations_response else []
        
        # Debug info (hidden by default, can be enabled for troubleshooting)
        if st.session_state.get('show_diagram_debug', False):
            with st.expander("🔍 Debug Information", expanded=False):
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
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "Container Diagram":
                        mermaid_code = asyncio.run(build_container_diagram(requirement_text, recommendations))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "Sequence Diagram":
                        mermaid_code = asyncio.run(build_sequence_diagram(requirement_text, recommendations))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "Tech Stack Wiring Diagram":
                        mermaid_code = asyncio.run(build_tech_stack_wiring_diagram(requirement_text, recommendations))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    else:  # Infrastructure Diagram
                        infrastructure_spec = asyncio.run(build_infrastructure_diagram(requirement_text, recommendations))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_spec'] = infrastructure_spec
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "infrastructure"
                    
                    st.success("✅ Diagram generated successfully!")
                    
            except Exception as e:
                st.error(f"❌ Error generating diagram: {str(e)}")
                st.write(f"**Error details:** {type(e).__name__}: {str(e)}")
                return
        
        # Display the diagram if we have one
        diagram_key = f'{diagram_type.lower().replace(" ", "_")}_code'
        diagram_spec_key = f'{diagram_type.lower().replace(" ", "_")}_spec'
        diagram_type_key = f'{diagram_type.lower().replace(" ", "_")}_type'
        
        if diagram_key in st.session_state or diagram_spec_key in st.session_state:
            diagram_render_type = st.session_state.get(diagram_type_key, "mermaid")
            
            if diagram_render_type == "infrastructure":
                # Handle infrastructure diagram
                infrastructure_spec = st.session_state[diagram_spec_key]
                self.render_infrastructure_diagram(infrastructure_spec, diagram_type)
            else:
                # Handle Mermaid diagram
                mermaid_code = st.session_state[diagram_key]
                self.render_mermaid(mermaid_code)
            
            # Add helpful context for the Tech Stack Wiring Diagram
            if diagram_type == "Tech Stack Wiring Diagram":
                st.info("""
                **How to read this diagram:**
                - **Rectangles** = Services/Applications (FastAPI, etc.)
                - **Cylinders** = Databases/Storage (PostgreSQL, Redis)
                - **Circles** = External Services (Twilio, OAuth2)
                - **Arrows** = Data flow and connections (HTTP, SQL, API calls)
                - **Labels** = Communication protocols and data types
                
                This shows the technical "wiring" of your system - how each technology component connects to others.
                """)
            
            # Check if diagram generation failed and show helpful message (only for Mermaid diagrams)
            if diagram_render_type == "mermaid":
                mermaid_code = st.session_state[diagram_key]
                if "Diagram Generation Error" in mermaid_code:
                    st.warning("""
                    **Diagram Generation Issue Detected**
                    
                    The LLM generated a diagram with formatting issues. This can happen with certain providers or complex tech stacks.
                    
                    **Suggestions:**
                    - Try generating the diagram again (click the Generate button)
                    - Switch to a different LLM provider (OpenAI usually works best for diagrams)
                    - Use the fake provider for a basic diagram structure
                    """)
                elif "generation failed" in mermaid_code.lower():
                    st.error("""
                    **Diagram Generation Failed**
                    
                    There was an error generating the diagram. Please check:
                    - Your LLM provider is properly configured
                    - You have a valid API key
                    - Try switching providers or generating again
                    """)
                
                # Show code
                with st.expander("View Mermaid Code"):
                    st.code(mermaid_code, language="mermaid")
    
    def render_mermaid(self, mermaid_code: str):
        """Render a Mermaid diagram with better viewing options."""
        import hashlib
        
        # Validate the Mermaid code before rendering
        is_valid, error_msg = _validate_mermaid_syntax(mermaid_code)
        if not is_valid:
            st.error(f"**Mermaid Syntax Error:** {error_msg}")
            
            # Provide specific guidance based on error type
            if "malformed" in error_msg.lower() and "one line" in error_msg.lower():
                st.warning("""
                **Severely Malformed Diagram Code**
                
                The LLM generated diagram code without proper line breaks. This is a common issue with certain providers.
                
                **Recommended solutions:**
                1. **Switch to OpenAI provider** (best Mermaid syntax generation)
                2. **Try generating again** (sometimes works on retry)
                3. **Use fake provider** for a basic diagram structure
                """)
            elif "unmatched" in error_msg.lower():
                st.warning("""
                **Syntax Error in Diagram**
                
                The diagram has unmatched brackets or parentheses.
                
                **Recommended solutions:**
                1. **Generate again** (LLM may fix the syntax on retry)
                2. **Switch providers** (different models handle syntax differently)
                3. **Simplify your requirement** (complex requirements can cause syntax errors)
                """)
            else:
                st.warning("""
                **Diagram Syntax Issue**
                
                The generated diagram has syntax errors.
                
                **Try these solutions:**
                1. Generate the diagram again (sometimes works on retry)
                2. Switch to OpenAI provider (usually better at Mermaid syntax)
                3. Use a simpler requirement description
                """)
            
            with st.expander("View Generated Code (with errors)"):
                st.code(mermaid_code, language="mermaid")
            return
        
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
    

    def render_infrastructure_diagram(self, infrastructure_spec: Dict[str, Any], diagram_type: str):
        """Render an infrastructure diagram using mingrammer/diagrams."""
        import hashlib
        import json
        import tempfile
        import os
        from pathlib import Path
        
        # Create a unique ID for this diagram
        spec_str = json.dumps(infrastructure_spec, sort_keys=True)
        diagram_id = hashlib.md5(spec_str.encode()).hexdigest()[:8]
        
        # Control buttons
        col1, col2, col3, col4 = st.columns([2, 1, 1, 1])
        with col2:
            if st.button("🔍 Large View", key=f"infra_expand_{diagram_id}"):
                st.session_state[f"show_large_infra_{diagram_id}"] = not st.session_state.get(f"show_large_infra_{diagram_id}", False)
        
        with col3:
            if st.button("💾 Download", key=f"infra_download_{diagram_id}"):
                self.download_infrastructure_diagram(infrastructure_spec, diagram_id)
        
        with col4:
            if st.button("📋 Show Code", key=f"infra_code_{diagram_id}"):
                st.session_state[f"show_infra_code_{diagram_id}"] = not st.session_state.get(f"show_infra_code_{diagram_id}", False)
        
        # Try to generate and display the infrastructure diagram
        try:
            from app.diagrams.infrastructure import InfrastructureDiagramGenerator
            
            generator = InfrastructureDiagramGenerator()
            
            # Create temporary file for the diagram
            with tempfile.NamedTemporaryFile(suffix='.png', delete=False) as tmp_file:
                temp_path = tmp_file.name[:-4]  # Remove .png extension
            
            try:
                # Generate the diagram
                diagram_path, python_code = generator.generate_diagram(
                    infrastructure_spec, temp_path, format="png"
                )
                
                # Display the diagram
                if os.path.exists(diagram_path):
                    show_large = st.session_state.get(f"show_large_infra_{diagram_id}", False)
                    
                    if show_large:
                        st.write("**🔍 Large View Mode** - Click 'Large View' again to return to normal size")
                        st.image(diagram_path, use_container_width=True)
                    else:
                        st.image(diagram_path, width=600)
                    
                    # Store the python code for display
                    st.session_state[f"infra_python_code_{diagram_id}"] = python_code
                    
                    # Add helpful context for Infrastructure Diagram
                    st.info("""
                    **How to read this diagram:**
                    - **Cloud Provider Icons** = Vendor-specific services (AWS Lambda, GCP Functions, etc.)
                    - **Clusters** = Logical groupings (VPCs, Resource Groups, Projects)
                    - **Arrows** = Data flow and connections between services
                    - **Colors** = Different service categories (compute, storage, database, etc.)
                    
                    This shows your infrastructure using official cloud provider icons and realistic architecture patterns.
                    """)
                    
                else:
                    st.error("Failed to generate infrastructure diagram image")
                    
            except Exception as e:
                st.error(f"Error generating infrastructure diagram: {str(e)}")
                st.write("**Fallback:** Showing diagram specification as JSON")
                st.json(infrastructure_spec)
                
            finally:
                # Clean up temporary files
                for ext in ['.png', '.svg']:
                    temp_file_path = f"{temp_path}{ext}"
                    if os.path.exists(temp_file_path):
                        try:
                            os.unlink(temp_file_path)
                        except:
                            pass
                            
        except ImportError:
            st.warning("""
            **Infrastructure Diagrams Not Available**
            
            The `diagrams` library is not installed. To enable infrastructure diagrams:
            
            ```bash
            pip install diagrams
            # Also install Graphviz system dependency
            ```
            
            **Showing specification instead:**
            """)
            st.json(infrastructure_spec)
        
        # Show code if requested
        if st.session_state.get(f"show_infra_code_{diagram_id}", False):
            python_code = st.session_state.get(f"infra_python_code_{diagram_id}", "# Code not available")
            
            st.write("**📋 Python Code (mingrammer/diagrams):**")
            st.code(python_code, language="python")
            
            st.write("**📋 JSON Specification:**")
            st.code(json.dumps(infrastructure_spec, indent=2), language="json")
            
            # Download options
            col1, col2 = st.columns(2)
            with col1:
                st.download_button(
                    label="💾 Download Python Code",
                    data=python_code,
                    file_name=f"infrastructure_diagram_{diagram_id}.py",
                    mime="text/plain",
                    key=f"download_py_{diagram_id}"
                )
            
            with col2:
                st.download_button(
                    label="💾 Download JSON Spec",
                    data=json.dumps(infrastructure_spec, indent=2),
                    file_name=f"infrastructure_spec_{diagram_id}.json",
                    mime="application/json",
                    key=f"download_json_{diagram_id}"
                )
    
    def download_infrastructure_diagram(self, infrastructure_spec: Dict[str, Any], diagram_id: str):
        """Generate and save infrastructure diagram for download."""
        try:
            from app.diagrams.infrastructure import InfrastructureDiagramGenerator
            
            generator = InfrastructureDiagramGenerator()
            
            # Create exports directory with absolute path
            current_dir = os.getcwd()
            exports_dir = os.path.join(current_dir, "exports")
            os.makedirs(exports_dir, exist_ok=True)
            st.info(f"📁 Created exports directory: {exports_dir}")
            
            output_path = os.path.join(exports_dir, f"infrastructure_diagram_{diagram_id}")
            
            # Generate PNG first
            try:
                png_path, python_code = generator.generate_diagram(
                    infrastructure_spec, output_path, format="png"
                )
                st.info(f"✅ PNG generated: {png_path}")
                
                # Verify PNG file exists
                if not os.path.exists(png_path):
                    raise FileNotFoundError(f"PNG file not found after generation: {png_path}")
                
            except Exception as png_error:
                st.error(f"PNG generation failed: {str(png_error)}")
                raise
            
            # Generate SVG
            try:
                svg_path, _ = generator.generate_diagram(
                    infrastructure_spec, output_path, format="svg"
                )
                st.info(f"✅ SVG generated: {svg_path}")
                
                # Verify SVG file exists
                if not os.path.exists(svg_path):
                    st.warning(f"SVG file not found after generation: {svg_path}")
                    svg_path = "SVG generation failed"
                
            except Exception as svg_error:
                st.warning(f"SVG generation failed: {str(svg_error)}")
                svg_path = "SVG generation failed"
            
            # Save the Python code
            try:
                code_path = os.path.join(exports_dir, f"infrastructure_diagram_{diagram_id}.py")
                with open(code_path, 'w') as f:
                    f.write(python_code)
                st.info(f"✅ Python code saved: {code_path}")
            except Exception as code_error:
                st.warning(f"Python code save failed: {str(code_error)}")
                code_path = "Python code save failed"
            
            # Show success message
            st.success(f"✅ Infrastructure diagram saved to exports/ directory!")
            st.write(f"**Files created:**")
            st.write(f"- `{png_path}` (PNG image)")
            if svg_path != "SVG generation failed":
                st.write(f"- `{svg_path}` (SVG vector)")
            if code_path != "Python code save failed":
                st.write(f"- `{code_path}` (Python source)")
            
        except Exception as e:
            st.error(f"Failed to save infrastructure diagram: {str(e)}")
            
            # Show debugging information
            with st.expander("🔍 Debug Information"):
                st.write(f"**Error Type:** {type(e).__name__}")
                st.write(f"**Error Message:** {str(e)}")
                st.write(f"**Diagram ID:** {diagram_id}")
                st.write(f"**Output Path:** exports/infrastructure_diagram_{diagram_id}")
                st.write(f"**Current Directory:** {os.getcwd()}")
                st.write(f"**Exports Directory Exists:** {os.path.exists('exports')}")
                
                # Show infrastructure spec for debugging
                st.write("**Infrastructure Specification:**")
                st.json(infrastructure_spec)
    
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
        
        # Add explanation
        st.markdown("""
        **Pattern Analytics** shows how well your solution patterns are performing in real-world usage:
        - **Match Frequency**: How often each pattern is recommended
        - **Acceptance Rates**: How often users accept pattern recommendations  
        - **Quality Scores**: Average matching confidence scores
        - **Usage Trends**: Pattern performance over time
        """)
        
        # Add data filtering options
        col1, col2, col3 = st.columns([2, 2, 1])
        
        with col1:
            data_scope = st.selectbox(
                "📊 Data Scope:",
                ["All Time", "Current Session Only", "Last 24 Hours", "Last 7 Days", "Last 30 Days"],
                help="Filter analytics by time period"
            )
        
        with col2:
            current_session_id = st.session_state.get('session_id')
            if current_session_id and data_scope == "Current Session Only":
                st.info(f"Showing data for session: {current_session_id[:8]}...")
        
        with col3:
            if st.button("🔄 Refresh Data"):
                st.rerun()
        
        try:
            # Fetch pattern statistics with filtering
            pattern_stats = asyncio.run(self.get_pattern_statistics(
                session_filter=current_session_id if data_scope == "Current Session Only" else None,
                time_filter=data_scope
            ))
            
            if not pattern_stats or not pattern_stats.get('pattern_stats'):
                if data_scope == "Current Session Only":
                    st.info("No pattern analytics available for current session yet. Complete an analysis to see pattern matching data.")
                else:
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
            st.info("💡 **How to view pattern details:** Click the 👁️ **View** button, then switch to the **📚 Pattern Library** tab to see the highlighted pattern.")
            
            # Create clickable pattern table
            if stats:
                # Create columns for the table
                cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
                
                # Headers
                with cols[0]:
                    st.write("**Pattern ID**")
                with cols[1]:
                    st.write("**Matches**")
                with cols[2]:
                    st.write("**Avg Score**")
                with cols[3]:
                    st.write("**Min Score**")
                with cols[4]:
                    st.write("**Max Score**")
                with cols[5]:
                    st.write("**Accepted**")
                with cols[6]:
                    st.write("**Rate**")
                with cols[7]:
                    st.write("**Action**")
                
                # Data rows
                for stat in stats[:15]:  # Limit to top 15 patterns
                    cols = st.columns([2, 1, 1, 1, 1, 1, 1, 1])
                    
                    with cols[0]:
                        st.write(stat['pattern_id'])
                    with cols[1]:
                        st.write(stat['match_count'])
                    with cols[2]:
                        st.write(f"{stat['avg_score']:.3f}")
                    with cols[3]:
                        st.write(f"{stat['min_score']:.3f}")
                    with cols[4]:
                        st.write(f"{stat['max_score']:.3f}")
                    with cols[5]:
                        st.write(stat['accepted_count'])
                    with cols[6]:
                        st.write(f"{stat['acceptance_rate']:.1%}")
                    with cols[7]:
                        # Create unique key for each button
                        button_key = f"view_pattern_{stat['pattern_id']}_{hash(str(stat))}"
                        if st.button("👁️ View", key=button_key, help=f"View {stat['pattern_id']} in Pattern Library"):
                            # Set session state to navigate to pattern library
                            st.session_state.selected_pattern_id = stat['pattern_id']
                            st.session_state.navigate_to_pattern_library = True
                            st.success(f"✅ Pattern {stat['pattern_id']} is ready to view!")
                            st.info(f"👉 **Next Step:** Click the **📚 Pattern Library** tab above to see the detailed pattern information.")
                            st.rerun()
            else:
                st.info("No pattern quality data available")
            
            # Show navigation status if a pattern is selected
            if st.session_state.get('navigate_to_pattern_library') and st.session_state.get('selected_pattern_id'):
                selected_id = st.session_state.get('selected_pattern_id')
                st.warning(f"🎯 **Pattern {selected_id} is ready to view!** Switch to the **📚 Pattern Library** tab to see it highlighted.")
            
            # Pattern insights and recommendations
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
                
                # Add insights about pattern diversity
                st.markdown("---")
                st.subheader("📈 Pattern Library Health")
                
                # Load all patterns to compare with usage
                try:
                    from app.pattern.loader import PatternLoader
                    from pathlib import Path
                    pattern_loader = PatternLoader(Path("data/patterns"))
                    all_patterns = pattern_loader.load_patterns()
                    
                    total_patterns = len(all_patterns)
                    used_patterns = len(stats)
                    unused_patterns = total_patterns - used_patterns
                    
                    col1, col2, col3 = st.columns(3)
                    
                    with col1:
                        st.metric("📚 Total Patterns", total_patterns)
                    
                    with col2:
                        st.metric("✅ Used Patterns", used_patterns)
                    
                    with col3:
                        usage_rate = (used_patterns / total_patterns * 100) if total_patterns > 0 else 0
                        st.metric("📊 Usage Rate", f"{usage_rate:.1f}%")
                    
                    # Show unused patterns
                    if unused_patterns > 0:
                        used_pattern_ids = {stat['pattern_id'] for stat in stats}
                        unused_pattern_ids = [p['pattern_id'] for p in all_patterns if p['pattern_id'] not in used_pattern_ids]
                        
                        st.info(f"**📋 Unused Patterns ({unused_patterns}):** {', '.join(unused_pattern_ids[:10])}")
                        if len(unused_pattern_ids) > 10:
                            st.caption(f"... and {len(unused_pattern_ids) - 10} more")
                
                except Exception as e:
                    st.warning(f"Could not load pattern library for comparison: {e}")
            
            else:
                st.info("No pattern matching data available yet. Complete some analyses to see insights.")
            
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
    
    async def get_pattern_statistics(self, session_filter: str = None, time_filter: str = "All Time") -> Dict[str, Any]:
        """Fetch pattern statistics from audit system with filtering options.
        
        Args:
            session_filter: Filter by specific session ID
            time_filter: Time period filter
            
        Returns:
            Pattern statistics dictionary
        """
        try:
            # Import audit system
            from app.utils.audit import get_audit_logger
            import sqlite3
            from datetime import datetime, timedelta
            
            audit_logger = get_audit_logger()
            
            # Build custom query with filtering
            base_query = """
                SELECT 
                    pattern_id,
                    COUNT(*) as match_count,
                    AVG(score) as avg_score,
                    MIN(score) as min_score,
                    MAX(score) as max_score,
                    SUM(CASE WHEN accepted = 1 THEN 1 ELSE 0 END) as accepted_count
                FROM matches 
                WHERE 1=1
            """
            
            params = []
            
            # Add session filter (use redacted session ID for database query)
            if session_filter:
                base_query += " AND session_id = ?"
                # Redact the session ID to match what's stored in the database
                redacted_session_id = audit_logger._redact_session_id(session_filter)
                params.append(redacted_session_id)
            
            # Add time filter
            if time_filter != "All Time":
                if time_filter == "Last 24 Hours":
                    cutoff = datetime.now() - timedelta(hours=24)
                elif time_filter == "Last 7 Days":
                    cutoff = datetime.now() - timedelta(days=7)
                elif time_filter == "Last 30 Days":
                    cutoff = datetime.now() - timedelta(days=30)
                else:
                    cutoff = None
                
                if cutoff:
                    base_query += " AND created_at >= ?"
                    params.append(cutoff.isoformat())
            
            base_query += " GROUP BY pattern_id ORDER BY match_count DESC"
            
            # Execute custom query
            with sqlite3.connect(audit_logger.db_path) as conn:
                cursor = conn.execute(base_query, params)
                
                stats = []
                for row in cursor.fetchall():
                    stats.append({
                        'pattern_id': row[0],
                        'match_count': row[1],
                        'avg_score': round(row[2], 3) if row[2] else 0,
                        'min_score': row[3],
                        'max_score': row[4],
                        'accepted_count': row[5],
                        'acceptance_rate': round(row[5] / row[1], 3) if row[1] > 0 else 0
                    })
                
                return {'pattern_stats': stats}
            
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
        
        # Handle navigation from Pattern Analytics
        if st.session_state.get('navigate_to_pattern_library') and st.session_state.get('selected_pattern_id'):
            selected_pattern_id = st.session_state.selected_pattern_id
            st.success(f"🎯 **Pattern {selected_pattern_id}** is highlighted below (navigated from Pattern Analytics)")
            st.info(f"💡 Look for the **highlighted pattern** in the View Patterns section below.")
            
            # Clear navigation flags
            st.session_state.navigate_to_pattern_library = False
            st.session_state.selected_pattern_id = None
            
            # Highlight only the selected pattern (others will remain collapsed)
            st.session_state.highlight_pattern_id = selected_pattern_id
        
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
            
            pattern_id = pattern.get('pattern_id', 'Unknown')
            pattern_header = f"{feasibility_emoji} {pattern_id} - {pattern.get('name', 'Unnamed Pattern')}"
            
            # Check if this pattern should be highlighted (navigated from analytics)
            is_highlighted = st.session_state.get('highlight_pattern_id') == pattern_id
            # Only expand the specifically highlighted pattern, keep all others collapsed
            expanded = is_highlighted
            
            # Add highlighting for selected pattern
            if is_highlighted:
                st.success(f"🎯 **This is the pattern you selected from Pattern Analytics**: {pattern_id}")
                # Clear the highlight after showing it
                st.session_state.highlight_pattern_id = None
            
            with st.expander(pattern_header, expanded=expanded):
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
    
    def render_technology_catalog_management(self):
        """Render the technology catalog management interface."""
        st.header("🔧 Technology Catalog Management")
        
        # Add helpful documentation
        with st.expander("ℹ️ What is the Technology Catalog?", expanded=False):
            st.markdown("""
            The **Technology Catalog** is a comprehensive database of technologies used in automation solutions. 
            It provides detailed information about each technology including descriptions, categories, and relationships.
            
            ### 🏷️ **Technology Components Explained:**
            
            - **Technology ID**: Unique identifier (e.g., python, fastapi, postgresql)
            - **Name**: Display name of the technology
            - **Category**: Technology type (languages, frameworks, databases, cloud, etc.)
            - **Description**: Detailed explanation of what the technology does
            - **Tags**: Keywords describing the technology's characteristics
            - **Maturity**: Stability level (stable, beta, experimental, deprecated)
            - **License**: Licensing model (MIT, Apache 2.0, Commercial, etc.)
            - **Alternatives**: Similar technologies that could be used instead
            - **Integrates With**: Technologies that work well together
            - **Use Cases**: Common scenarios where this technology is used
            
            ### 🎯 **How the Catalog is Used:**
            - **LLM Recommendations**: When generating tech stacks, the LLM uses this catalog for context
            - **Automatic Updates**: New technologies suggested by LLM are automatically added
            - **Constraint Validation**: Banned technologies are filtered out during recommendations
            - **Categorization**: Technologies are organized for better user experience
            
            ### 🔄 **Automatic Updates:**
            When the LLM suggests new technologies not in the catalog, they are automatically:
            1. Added with inferred categories and descriptions
            2. Marked as `auto_generated: true`
            3. Saved to the catalog file with backup creation
            """)
        
        # Load technology catalog
        try:
            import sys
            sys.path.append('app')
            from services.tech_stack_generator import TechStackGenerator
            
            generator = TechStackGenerator()
            catalog = generator.technology_catalog
            technologies = catalog.get("technologies", {})
            categories = catalog.get("categories", {})
            
        except Exception as e:
            st.error(f"❌ Error loading technology catalog: {str(e)}")
            return
        
        # Management tabs
        view_tab, edit_tab, create_tab, import_tab = st.tabs(["👀 View Technologies", "✏️ Edit Technology", "➕ Add Technology", "📥 Import/Export"])
        
        with view_tab:
            self.render_technology_viewer(technologies, categories)
        
        with edit_tab:
            self.render_technology_editor(technologies, categories)
        
        with create_tab:
            self.render_technology_creator()
        
        with import_tab:
            self.render_technology_import_export(catalog)
    
    def render_technology_viewer(self, technologies: dict, categories: dict):
        """Render the technology viewer interface."""
        col1, col2 = st.columns([3, 1])
        with col1:
            st.subheader("👀 Technology Catalog Overview")
        with col2:
            if st.button("🔄 Refresh Catalog", help="Refresh the technology catalog"):
                st.cache_data.clear()
                st.rerun()
        
        if not technologies:
            st.info("📝 No technologies found in the catalog.")
            return
        
        # Summary statistics
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.metric("Total Technologies", len(technologies))
        with col2:
            auto_generated = len([t for t in technologies.values() if t.get('auto_generated')])
            st.metric("Auto-Generated", auto_generated)
        with col3:
            stable_count = len([t for t in technologies.values() if t.get('maturity') == 'stable'])
            st.metric("Stable", stable_count)
        with col4:
            st.metric("Categories", len(categories))
        
        # Filter options
        st.subheader("🔍 Filter Technologies")
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            category_names = {cat_id: cat_info.get('name', cat_id) for cat_id, cat_info in categories.items()}
            selected_category = st.selectbox("📂 Category", ["All"] + sorted(category_names.values()))
        
        with col2:
            maturities = list(set(t.get('maturity', 'unknown') for t in technologies.values()))
            selected_maturity = st.selectbox("🎯 Maturity", ["All"] + sorted(maturities))
        
        with col3:
            licenses = list(set(t.get('license', 'unknown') for t in technologies.values()))
            selected_license = st.selectbox("📄 License", ["All"] + sorted(licenses))
        
        with col4:
            auto_gen_filter = st.selectbox("🤖 Source", ["All", "Manual", "Auto-Generated"])
        
        # Search box
        search_term = st.text_input("🔍 Search technologies", placeholder="Search by name, description, or tags...")
        
        # Filter technologies
        filtered_technologies = {}
        
        for tech_id, tech_info in technologies.items():
            # Category filter
            if selected_category != "All":
                tech_category = tech_info.get('category', '')
                category_name = categories.get(tech_category, {}).get('name', tech_category)
                if category_name != selected_category:
                    continue
            
            # Maturity filter
            if selected_maturity != "All" and tech_info.get('maturity') != selected_maturity:
                continue
            
            # License filter
            if selected_license != "All" and tech_info.get('license') != selected_license:
                continue
            
            # Auto-generated filter
            if auto_gen_filter == "Manual" and tech_info.get('auto_generated'):
                continue
            elif auto_gen_filter == "Auto-Generated" and not tech_info.get('auto_generated'):
                continue
            
            # Search filter
            if search_term:
                search_lower = search_term.lower()
                name_match = search_lower in tech_info.get('name', '').lower()
                desc_match = search_lower in tech_info.get('description', '').lower()
                tags_match = any(search_lower in tag.lower() for tag in tech_info.get('tags', []))
                
                if not (name_match or desc_match or tags_match):
                    continue
            
            filtered_technologies[tech_id] = tech_info
        
        # Show filtering results
        st.write(f"📊 Showing **{len(filtered_technologies)}** of **{len(technologies)}** technologies")
        
        # Category overview
        if st.button("📂 Show Category Overview"):
            st.session_state.show_category_overview = not st.session_state.get('show_category_overview', False)
        
        if st.session_state.get('show_category_overview', False):
            with st.expander("📂 Technology Categories", expanded=True):
                for cat_id, cat_info in categories.items():
                    cat_name = cat_info.get('name', cat_id)
                    cat_desc = cat_info.get('description', '')
                    cat_techs = cat_info.get('technologies', [])
                    
                    st.write(f"**{cat_name}** ({len(cat_techs)} technologies)")
                    st.write(f"*{cat_desc}*")
                    
                    # Show first few technologies in this category
                    sample_techs = []
                    for tech_id in cat_techs[:5]:
                        if tech_id in technologies:
                            sample_techs.append(technologies[tech_id].get('name', tech_id))
                    
                    if sample_techs:
                        st.write(f"Examples: {', '.join(sample_techs)}")
                        if len(cat_techs) > 5:
                            st.write(f"... and {len(cat_techs) - 5} more")
                    st.write("")
        
        # Display technologies
        for tech_id, tech_info in sorted(filtered_technologies.items()):
            name = tech_info.get('name', tech_id)
            category = tech_info.get('category', 'unknown')
            category_name = categories.get(category, {}).get('name', category)
            maturity = tech_info.get('maturity', 'unknown')
            auto_gen = tech_info.get('auto_generated', False)
            
            # Create header with status indicators
            status_indicators = []
            if auto_gen:
                status_indicators.append("🤖 Auto")
            if maturity == 'stable':
                status_indicators.append("✅ Stable")
            elif maturity == 'beta':
                status_indicators.append("🚧 Beta")
            elif maturity == 'experimental':
                status_indicators.append("🧪 Experimental")
            elif maturity == 'deprecated':
                status_indicators.append("⚠️ Deprecated")
            
            status_str = " ".join(status_indicators)
            header = f"🔧 {name} ({category_name}) {status_str}"
            
            with st.expander(header):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write("**📝 Description:**")
                    st.write(tech_info.get('description', 'No description available'))
                    
                    tags = tech_info.get('tags', [])
                    if tags:
                        st.write("**🏷️ Tags:**")
                        cols = st.columns(min(len(tags), 4))
                        for i, tag in enumerate(tags):
                            with cols[i % 4]:
                                st.code(tag, language=None)
                    
                    use_cases = tech_info.get('use_cases', [])
                    if use_cases:
                        st.write("**💡 Use Cases:**")
                        for use_case in use_cases:
                            st.write(f"• {use_case}")
                
                with col2:
                    st.write("**ℹ️ Details:**")
                    st.write(f"**ID:** `{tech_id}`")
                    st.write(f"**Category:** {category_name}")
                    st.write(f"**Maturity:** {maturity}")
                    st.write(f"**License:** {tech_info.get('license', 'unknown')}")
                    
                    if auto_gen:
                        st.write(f"**Added:** {tech_info.get('added_date', 'unknown')}")
                    
                    alternatives = tech_info.get('alternatives', [])
                    if alternatives:
                        st.write("**🔄 Alternatives:**")
                        for alt in alternatives:
                            st.write(f"• {alt}")
                    
                    integrates_with = tech_info.get('integrates_with', [])
                    if integrates_with:
                        st.write("**🔗 Integrates With:**")
                        for integration in integrates_with:
                            st.write(f"• {integration}")
    
    def render_technology_editor(self, technologies: dict, categories: dict):
        """Render the technology editor interface."""
        st.subheader("✏️ Edit Technology")
        
        if not technologies:
            st.info("📝 No technologies available to edit.")
            return
        
        # Technology selection
        tech_options = {f"{info.get('name', tech_id)} ({tech_id})": tech_id 
                       for tech_id, info in technologies.items()}
        selected_display = st.selectbox("Select technology to edit:", [""] + sorted(tech_options.keys()))
        
        if not selected_display:
            st.info("👆 Select a technology to edit")
            return
        
        tech_id = tech_options[selected_display]
        tech_info = technologies[tech_id]
        
        st.write(f"**Editing:** {tech_info.get('name', tech_id)} (`{tech_id}`)")
        
        # Edit form
        with st.form(f"edit_tech_{tech_id}"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Name", value=tech_info.get('name', ''))
                
                category_options = list(categories.keys())
                current_category = tech_info.get('category', '')
                category_index = category_options.index(current_category) if current_category in category_options else 0
                category = st.selectbox("Category", category_options, index=category_index)
                
                maturity = st.selectbox("Maturity", 
                                      ["stable", "beta", "experimental", "deprecated", "unknown"],
                                      index=["stable", "beta", "experimental", "deprecated", "unknown"].index(tech_info.get('maturity', 'unknown')))
                
                license_val = st.text_input("License", value=tech_info.get('license', ''))
            
            with col2:
                description = st.text_area("Description", value=tech_info.get('description', ''), height=100)
                
                tags_str = ', '.join(tech_info.get('tags', []))
                tags = st.text_input("Tags (comma-separated)", value=tags_str)
                
                alternatives_str = ', '.join(tech_info.get('alternatives', []))
                alternatives = st.text_input("Alternatives (comma-separated)", value=alternatives_str)
                
                integrates_str = ', '.join(tech_info.get('integrates_with', []))
                integrates_with = st.text_input("Integrates With (comma-separated)", value=integrates_str)
            
            use_cases_str = '\n'.join(tech_info.get('use_cases', []))
            use_cases = st.text_area("Use Cases (one per line)", value=use_cases_str, height=80)
            
            if st.form_submit_button("💾 Save Changes"):
                try:
                    # Update technology info
                    updated_tech = {
                        "name": name,
                        "category": category,
                        "description": description,
                        "tags": [tag.strip() for tag in tags.split(',') if tag.strip()],
                        "maturity": maturity,
                        "license": license_val,
                        "alternatives": [alt.strip() for alt in alternatives.split(',') if alt.strip()],
                        "integrates_with": [int_tech.strip() for int_tech in integrates_with.split(',') if int_tech.strip()],
                        "use_cases": [uc.strip() for uc in use_cases.split('\n') if uc.strip()],
                        "auto_generated": tech_info.get('auto_generated', False),
                        "added_date": tech_info.get('added_date', ''),
                        "last_modified": datetime.now().strftime("%Y-%m-%d")
                    }
                    
                    # Save to catalog
                    self.save_technology_to_catalog(tech_id, updated_tech)
                    st.success(f"✅ Technology {name} updated successfully!")
                    st.rerun()
                    
                except Exception as e:
                    st.error(f"❌ Error updating technology: {str(e)}")
    
    def render_technology_creator(self):
        """Render the technology creator interface."""
        st.subheader("➕ Add New Technology")
        
        # Load categories for selection
        try:
            import sys
            sys.path.append('app')
            from services.tech_stack_generator import TechStackGenerator
            
            generator = TechStackGenerator()
            categories = generator.technology_catalog.get("categories", {})
            
        except Exception as e:
            st.error(f"❌ Error loading categories: {str(e)}")
            return
        
        # Creation form
        with st.form("create_technology"):
            col1, col2 = st.columns(2)
            
            with col1:
                name = st.text_input("Technology Name*", placeholder="e.g., React Native")
                
                category_options = list(categories.keys())
                category = st.selectbox("Category*", category_options)
                
                maturity = st.selectbox("Maturity", 
                                      ["stable", "beta", "experimental", "deprecated", "unknown"],
                                      index=0)
                
                license_val = st.text_input("License", placeholder="e.g., MIT, Apache 2.0, Commercial")
            
            with col2:
                description = st.text_area("Description*", 
                                         placeholder="Brief description of what this technology does...",
                                         height=100)
                
                tags = st.text_input("Tags (comma-separated)", 
                                    placeholder="e.g., mobile, react, javascript")
                
                alternatives = st.text_input("Alternatives (comma-separated)", 
                                           placeholder="e.g., Flutter, Xamarin, Ionic")
                
                integrates_with = st.text_input("Integrates With (comma-separated)", 
                                               placeholder="e.g., react, javascript, node.js")
            
            use_cases = st.text_area("Use Cases (one per line)", 
                                   placeholder="mobile_app_development\ncross_platform_apps\nreact_native_apps",
                                   height=80)
            
            if st.form_submit_button("➕ Add Technology"):
                if not name or not description:
                    st.error("❌ Name and description are required!")
                else:
                    try:
                        # Generate tech ID
                        tech_id = name.lower().replace(" ", "_").replace("/", "_").replace("-", "_")
                        tech_id = ''.join(c for c in tech_id if c.isalnum() or c == '_')
                        
                        # Create technology info
                        tech_info = {
                            "name": name,
                            "category": category,
                            "description": description,
                            "tags": [tag.strip() for tag in tags.split(',') if tag.strip()],
                            "maturity": maturity,
                            "license": license_val if license_val else "unknown",
                            "alternatives": [alt.strip() for alt in alternatives.split(',') if alt.strip()],
                            "integrates_with": [int_tech.strip() for int_tech in integrates_with.split(',') if int_tech.strip()],
                            "use_cases": [uc.strip() for uc in use_cases.split('\n') if uc.strip()],
                            "auto_generated": False,
                            "added_date": datetime.now().strftime("%Y-%m-%d")
                        }
                        
                        # Save to catalog
                        self.save_technology_to_catalog(tech_id, tech_info)
                        st.success(f"✅ Technology {name} added successfully with ID: {tech_id}")
                        
                    except Exception as e:
                        st.error(f"❌ Error creating technology: {str(e)}")
    
    def render_technology_import_export(self, catalog: dict):
        """Render the import/export interface."""
        st.subheader("📥 Import/Export Technologies")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**📤 Export Catalog**")
            
            if st.button("💾 Download Full Catalog"):
                # Create downloadable JSON
                import json
                catalog_json = json.dumps(catalog, indent=2)
                st.download_button(
                    label="📥 Download technologies.json",
                    data=catalog_json,
                    file_name=f"technologies_export_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                    mime="application/json"
                )
            
            # Export specific categories
            categories = catalog.get("categories", {})
            if categories:
                selected_categories = st.multiselect("Export specific categories:", 
                                                   list(categories.keys()))
                
                if selected_categories and st.button("📤 Export Selected Categories"):
                    # Filter technologies by selected categories
                    filtered_technologies = {}
                    for cat_id in selected_categories:
                        cat_techs = categories[cat_id].get("technologies", [])
                        for tech_id in cat_techs:
                            if tech_id in catalog.get("technologies", {}):
                                filtered_technologies[tech_id] = catalog["technologies"][tech_id]
                    
                    export_data = {
                        "metadata": {
                            "exported_categories": selected_categories,
                            "export_date": datetime.now().isoformat(),
                            "total_technologies": len(filtered_technologies)
                        },
                        "technologies": filtered_technologies,
                        "categories": {cat_id: categories[cat_id] for cat_id in selected_categories}
                    }
                    
                    export_json = json.dumps(export_data, indent=2)
                    st.download_button(
                        label=f"📥 Download {len(selected_categories)} categories",
                        data=export_json,
                        file_name=f"technologies_categories_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json",
                        mime="application/json"
                    )
        
        with col2:
            st.write("**📥 Import Technologies**")
            
            uploaded_file = st.file_uploader("Upload technology catalog:", type=['json'])
            
            if uploaded_file is not None:
                try:
                    import json
                    import_data = json.load(uploaded_file)
                    
                    # Validate structure
                    if "technologies" not in import_data:
                        st.error("❌ Invalid file format: missing 'technologies' section")
                    else:
                        technologies = import_data["technologies"]
                        st.success(f"✅ Found {len(technologies)} technologies to import")
                        
                        # Show preview
                        with st.expander("👀 Preview Import Data"):
                            for tech_id, tech_info in list(technologies.items())[:5]:
                                st.write(f"• **{tech_info.get('name', tech_id)}** ({tech_id})")
                                st.write(f"  Category: {tech_info.get('category', 'unknown')}")
                                st.write(f"  Description: {tech_info.get('description', 'No description')[:100]}...")
                            
                            if len(technologies) > 5:
                                st.write(f"... and {len(technologies) - 5} more technologies")
                        
                        # Import options
                        import_mode = st.radio("Import mode:", 
                                             ["Merge (keep existing, add new)", 
                                              "Replace (overwrite existing)"])
                        
                        if st.button("📥 Import Technologies"):
                            try:
                                self.import_technologies_to_catalog(import_data, import_mode == "Replace (overwrite existing)")
                                st.success(f"✅ Successfully imported {len(technologies)} technologies!")
                                st.rerun()
                            except Exception as e:
                                st.error(f"❌ Import failed: {str(e)}")
                
                except Exception as e:
                    st.error(f"❌ Error reading file: {str(e)}")
        
        # Catalog statistics
        st.write("---")
        st.write("**📊 Current Catalog Statistics**")
        
        col1, col2, col3, col4 = st.columns(4)
        technologies = catalog.get("technologies", {})
        categories = catalog.get("categories", {})
        
        with col1:
            st.metric("Technologies", len(technologies))
        with col2:
            st.metric("Categories", len(categories))
        with col3:
            auto_generated = len([t for t in technologies.values() if t.get('auto_generated')])
            st.metric("Auto-Generated", auto_generated)
        with col4:
            manual = len(technologies) - auto_generated
            st.metric("Manual", manual)
    
    def save_technology_to_catalog(self, tech_id: str, tech_info: dict):
        """Save a technology to the catalog file."""
        try:
            import sys
            sys.path.append('app')
            from services.tech_stack_generator import TechStackGenerator
            
            # Create generator and add technology
            generator = TechStackGenerator()
            
            # Update in-memory catalog
            generator.technology_catalog.setdefault("technologies", {})[tech_id] = tech_info
            
            # Update category
            category_id = tech_info.get("category", "integration")
            generator.technology_catalog.setdefault("categories", {}).setdefault(category_id, {
                "name": category_id.replace("_", " ").title(),
                "description": f"{category_id.replace('_', ' ').title()} technologies",
                "technologies": []
            })
            
            if tech_id not in generator.technology_catalog["categories"][category_id]["technologies"]:
                generator.technology_catalog["categories"][category_id]["technologies"].append(tech_id)
            
            # Update metadata
            total_techs = len(generator.technology_catalog.get("technologies", {}))
            generator.technology_catalog.setdefault("metadata", {}).update({
                "total_technologies": total_techs,
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "last_manual_update": datetime.now().isoformat()
            })
            
            # Save to file
            asyncio.run(generator._save_catalog_to_file())
            
        except Exception as e:
            raise Exception(f"Failed to save technology: {str(e)}")
    
    def import_technologies_to_catalog(self, import_data: dict, replace_existing: bool = False):
        """Import technologies from uploaded data."""
        try:
            import sys
            sys.path.append('app')
            from services.tech_stack_generator import TechStackGenerator
            
            generator = TechStackGenerator()
            
            # Import technologies
            import_technologies = import_data.get("technologies", {})
            import_categories = import_data.get("categories", {})
            
            for tech_id, tech_info in import_technologies.items():
                if replace_existing or tech_id not in generator.technology_catalog.get("technologies", {}):
                    generator.technology_catalog.setdefault("technologies", {})[tech_id] = tech_info
            
            # Import categories
            for cat_id, cat_info in import_categories.items():
                if replace_existing or cat_id not in generator.technology_catalog.get("categories", {}):
                    generator.technology_catalog.setdefault("categories", {})[cat_id] = cat_info
            
            # Update metadata
            total_techs = len(generator.technology_catalog.get("technologies", {}))
            generator.technology_catalog.setdefault("metadata", {}).update({
                "total_technologies": total_techs,
                "last_updated": datetime.now().strftime("%Y-%m-%d"),
                "last_import": datetime.now().isoformat()
            })
            
            # Save to file
            asyncio.run(generator._save_catalog_to_file())
            
        except Exception as e:
            raise Exception(f"Failed to import technologies: {str(e)}")
    
    def run(self):
        """Main application entry point."""
        st.title("🤖 Automated AI Assessment (AAA)")
        st.markdown("*Assess automation feasibility of your requirements with AI*")
        
        # Sidebar with provider configuration
        self.render_provider_panel()
        
        # Main content area
        tab1, tab2, tab3, tab4, tab5, tab6 = st.tabs(["📝 Analysis", "📊 Diagrams", "📈 Observability", "📚 Pattern Library", "🔧 Technology Catalog", "ℹ️ About"])
        
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
            self.render_technology_catalog_management()
        
        with tab6:
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