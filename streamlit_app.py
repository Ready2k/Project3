"""Streamlit UI for Automated AI Assessment (AAA) application."""

import asyncio
import json
import os
import re
import sqlite3
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any

import httpx
import streamlit as st
from streamlit.components.v1 import html

# Import service utilities (but don't access services at module level)
from app.utils.imports import require_service, optional_service

# Import API client for provider configuration
from app.ui.api_client import AAA_APIClient
import os

# Create a fresh API client instance to avoid caching issues
def get_fresh_api_client():
    api_base_url = os.getenv("API_BASE_URL", "http://localhost:8000")
    return AAA_APIClient(base_url=api_base_url)

api_client = get_fresh_api_client()

# Import streamlit_mermaid directly
try:
    import streamlit_mermaid as stmd
    MERMAID_AVAILABLE = True
except ImportError:
    MERMAID_AVAILABLE = False
    stmd = None

# Initialize services at module level
app_logger = None
llm_provider_service = None

def initialize_module_services():
    """Initialize services at module level when imported."""
    global app_logger, llm_provider_service
    
    try:
        from app.core.service_registration import register_core_services
        from app.core.registry import get_registry
        from app.utils.imports import require_service, optional_service
        
        registry = get_registry()
        
        # Check if services are already registered, if not register them
        if not registry.has('logger'):
            register_core_services(registry)
        
        # Get services
        app_logger = require_service('logger', context='streamlit_module')
        llm_provider_service = optional_service('llm_provider_factory', context='streamlit_module')
        
        return True
    except Exception as e:
        # Use fallback logger for error reporting
        import logging
        fallback_logger = logging.getLogger(__name__)
        fallback_logger.error(f"Failed to initialize module services: {e}")
        return False

# Initialize services when module is imported
_services_initialized = initialize_module_services()
OPENAI_AVAILABLE = False



# Custom exception for security feedback
class SecurityFeedbackException(Exception):
    """Exception for enhanced security feedback that should be displayed with formatting."""
    pass

# Mermaid diagram functions (LLM-generated for specific requirements)
async def make_llm_request(prompt: str, provider_config: Dict, purpose: str = "diagram_generation") -> str:
    """Make a request to the LLM for diagram generation using audited provider."""
    try:
        # Import here to avoid circular imports
        from app.api import create_llm_provider, ProviderConfig
        
        # Import configuration service for dynamic parameters
        from app.services.configuration_service import get_config
        config_service = get_config()
        llm_params = config_service.get_llm_params()
        
        # Create provider config object with dynamic parameters
        config = ProviderConfig(
            provider=provider_config.get('provider', 'openai'),
            model=provider_config.get('model', 'gpt-4o'),
            api_key=provider_config.get('api_key', ''),
            endpoint_url=provider_config.get('endpoint_url'),
            region=provider_config.get('region'),
            aws_access_key_id=provider_config.get('aws_access_key_id'),
            aws_secret_access_key=provider_config.get('aws_secret_access_key'),
            aws_session_token=provider_config.get('aws_session_token'),
            bedrock_api_key=provider_config.get('bedrock_api_key'),
            temperature=llm_params['temperature'],
            max_tokens=llm_params['max_tokens']
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
    if not label:
        return 'unknown'
    
    # Remove emojis and special Unicode characters that can cause Mermaid issues
    import re
    # Remove emojis and other problematic Unicode characters
    label = re.sub(r'[^\w\s\-_.:()[\]{}]', '', label)
    
    # Keep only safe characters for Mermaid
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.:()")
    sanitized = ''.join(ch if ch in allowed else '_' for ch in label)
    
    # Clean up multiple underscores and spaces
    sanitized = re.sub(r'[_\s]+', '_', sanitized).strip('_')
    
    return sanitized or 'unknown'

def _validate_mermaid_syntax(mermaid_code: str) -> tuple[bool, str]:
    """Validate basic Mermaid syntax and return (is_valid, error_message)."""
    if not mermaid_code.strip():
        return False, "Empty diagram code"
    
    # Check for severely malformed code (all on one line with no spaces around arrows)
    if '\n' not in mermaid_code and len(mermaid_code) > 200:
        return False, "Diagram code appears to be malformed (all on one line). This usually indicates an LLM formatting error."
    
    # Check for problematic Unicode characters that can cause Mermaid v10.2.4 issues
    import re
    if re.search(r'[^\x00-\x7F]', mermaid_code):
        # Contains non-ASCII characters - clean them
        app_logger.warning("Mermaid code contains non-ASCII characters that may cause rendering issues")
        # This is a warning, not an error - let the cleaning function handle it
    
    lines = [line.strip() for line in mermaid_code.split('\n') if line.strip()]
    
    # Check for valid diagram type
    first_line = lines[0].lower()
    valid_starts = ['flowchart', 'graph', 'sequencediagram', 'classdiagram', 'statediagram', 
                   'c4context', 'c4container', 'c4component', 'c4dynamic']
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
        
        # For C4 diagrams, skip curly brace validation on individual lines since System_Boundary spans multiple lines
        is_c4_diagram = any(first_line.startswith(c4_type) for c4_type in ['c4context', 'c4container', 'c4component', 'c4dynamic'])
        if not is_c4_diagram and line.count('{') != line.count('}'):
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
    
    # For C4 diagrams, validate C4-specific syntax
    elif any(first_line.startswith(c4_type) for c4_type in ['c4context', 'c4container', 'c4component', 'c4dynamic']):
        # Check for balanced curly braces across the entire C4 diagram
        total_open_braces = sum(line.count('{') for line in lines)
        total_close_braces = sum(line.count('}') for line in lines)
        if total_open_braces != total_close_braces:
            return False, f"Unmatched curly braces in C4 diagram: {total_open_braces} opening, {total_close_braces} closing"
        # Validate C4-specific elements
        valid_c4_elements = ['person', 'system', 'container', 'containerdb', 'component', 'rel', 'relnote', 
                           'system_ext', 'container_ext', 'component_ext', 'person_ext',
                           'enterprise_boundary', 'system_boundary', 'container_boundary',
                           'title', 'updatelayout']
        
        for i, line in enumerate(lines[1:], 2):  # Skip first line (diagram type)
            line_lower = line.lower().strip()
            
            # Skip empty lines and comments
            if not line_lower or line_lower.startswith('%%'):
                continue
                
            # Check if line contains a valid C4 element
            has_valid_element = False
            for element in valid_c4_elements:
                if line_lower.startswith(element + '(') or line_lower.startswith(element + ' '):
                    has_valid_element = True
                    break
            
            # Allow certain utility lines
            if (line_lower.startswith('updatelayout') or 
                line_lower.startswith('title ')):
                has_valid_element = True
            
            if not has_valid_element and line_lower not in ['', '%%']:
                # Check for lines that look like C4 elements but aren't valid
                if '(' in line_lower and ')' in line_lower:
                    return False, f"Invalid C4 element syntax on line {i}: {line}. Valid C4 elements: {', '.join(valid_c4_elements)}"
        
        # Validate C4 relationship syntax (Rel statements)
        for i, line in enumerate(lines):
            line_lower = line.lower().strip()
            if line_lower.startswith('rel('):
                # Basic validation for Rel syntax: Rel(from, to, label, [technology])
                if line_lower.count('(') != line_lower.count(')'):
                    return False, f"Unmatched parentheses in Rel statement on line {i+1}: {line}"
                # Check for minimum required parameters (from, to, label)
                content = line_lower[4:-1]  # Remove 'rel(' and ')'
                if content.count(',') < 2:
                    return False, f"Rel statement missing required parameters on line {i+1}: {line}. Format: Rel(from, to, label, [technology])"
    
    return True, ""

def _extract_mermaid_code(response: str) -> str:
    """Extract only the Mermaid code from LLM responses that may contain explanations."""
    if not response:
        return ""
    
    import re
    
    # First, try to find code within markdown blocks
    markdown_pattern = r'```(?:mermaid)?\s*\n?(.*?)\n?```'
    markdown_match = re.search(markdown_pattern, response, re.DOTALL | re.IGNORECASE)
    if markdown_match:
        return markdown_match.group(1).strip()
    
    # Define valid Mermaid diagram start patterns
    diagram_patterns = [
        r'(flowchart\s+(?:TB|TD|BT|RL|LR).*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)',
        r'(graph\s+(?:TB|TD|BT|RL|LR).*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)',
        r'(sequenceDiagram.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)',
        r'(C4Context.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)',
        r'(C4Container.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)',
        r'(C4Component.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)',
        r'(C4Dynamic.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)'
    ]
    
    # Try each pattern to extract the diagram
    for pattern in diagram_patterns:
        match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
        if match:
            extracted = match.group(1).strip()
            # Validate that this looks like actual Mermaid code
            if _looks_like_mermaid_code(extracted):
                return extracted
    
    # If no patterns match, try to find lines that look like Mermaid code
    lines = response.split('\n')
    mermaid_lines = []
    in_diagram = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check if this line starts a diagram
        if any(line_stripped.lower().startswith(start) for start in 
               ['flowchart', 'graph', 'sequencediagram', 'c4context', 'c4container', 'c4component', 'c4dynamic']):
            in_diagram = True
            mermaid_lines = [line]  # Start fresh
            continue
        
        # If we're in a diagram, keep collecting lines
        if in_diagram:
            # Stop if we hit explanatory text
            if (line_stripped.lower().startswith(('this diagram', 'the diagram', 'explanation:', 'note:', 'this shows', 'the above')) or
                (line_stripped and not line_stripped.startswith(('    ', '\t', '%%')) and 
                 not any(char in line_stripped for char in ['-->', '---', '(', ')', '[', ']', '{', '}', '|']) and
                 len(line_stripped.split()) > 5)):  # Likely explanatory text
                break
            
            # Skip empty lines but keep them for formatting
            if not line_stripped:
                mermaid_lines.append(line)
                continue
            
            # Keep lines that look like Mermaid syntax
            if (line_stripped.startswith(('    ', '\t', '%%')) or  # Indented or comments
                any(char in line_stripped for char in ['-->', '---', '(', ')', '[', ']', '{', '}', '|']) or  # Mermaid syntax
                any(line_stripped.lower().startswith(keyword) for keyword in 
                    ['person', 'system', 'container', 'component', 'rel', 'title', 'participant', 'note', 'alt', 'end', 'subgraph'])):
                mermaid_lines.append(line)
            else:
                # If this doesn't look like Mermaid syntax, we might be done
                break
    
    if mermaid_lines:
        extracted = '\n'.join(mermaid_lines).strip()
        if _looks_like_mermaid_code(extracted):
            return extracted
    
    # Last resort: return the original response and let the cleaning function handle it
    return response

def _looks_like_mermaid_code(code: str) -> bool:
    """Check if the extracted code looks like valid Mermaid syntax."""
    if not code:
        return False
    
    lines = [line.strip() for line in code.split('\n') if line.strip()]
    if len(lines) < 2:
        return False
    
    # Check if first line is a valid diagram declaration
    first_line = lines[0].lower()
    valid_starts = ['flowchart', 'graph', 'sequencediagram', 'c4context', 'c4container', 'c4component', 'c4dynamic']
    if not any(first_line.startswith(start) for start in valid_starts):
        return False
    
    # Check if it contains typical Mermaid syntax
    code_lower = code.lower()
    mermaid_indicators = ['-->', '---', '(', ')', '[', ']', 'rel(', 'person(', 'system(', 'participant', 'note']
    if not any(indicator in code_lower for indicator in mermaid_indicators):
        return False
    
    return True

def _fix_malformed_sequence_diagram(code: str) -> str:
    """Fix sequence diagrams that are generated without proper line breaks."""
    if not code:
        return code
    
    import re
    
    # Check if this is a sequence diagram
    lines = code.split('\n')
    first_line = lines[0].strip().lower()
    
    if not first_line.startswith('sequencediagram'):
        return code
    
    # If it's properly formatted (multiple lines with reasonable length), don't change it
    if len(lines) > 3 and all(len(line) < 150 for line in lines[:5]):
        return code
    
    # If it's all on one line or has very long lines, it needs fixing
    if len(lines) == 1 or any(len(line) > 150 for line in lines[:3]):
        # Simple but effective approach: use regex to add line breaks at key points
        content = code
        
        # Remove the initial 'sequenceDiagram' if present
        if content.lower().startswith('sequencediagram'):
            content = content[15:]
        
        # Add line breaks before key sequence diagram elements
        # Add line break before each participant
        content = re.sub(r'participant\s+', '\nparticipant ', content)
        
        # Add line break before each message (arrows) - simpler approach
        # Look for patterns like "ActorA->>ActorB:" or "ActorA-->>ActorB:"
        content = re.sub(r'([A-Za-z_][A-Za-z0-9_]*\s*(?:->>?\+?|-->>?\+?)\s*[A-Za-z_][A-Za-z0-9_]*\s*:)', r'\n\1', content)
        
        # Add line break before alt blocks
        content = re.sub(r'alt\s+', '\nalt ', content)
        
        # Add line break before else
        content = re.sub(r'else\s+', '\nelse ', content)
        
        # Add line break before end
        content = re.sub(r'end([A-Z])', r'\nend\n\1', content)
        content = re.sub(r'end$', r'\nend', content)
        
        # Add line break before notes
        content = re.sub(r'note\s+(over|left|right)', r'\nnote \1', content)
        
        # Reconstruct the diagram
        result = 'sequenceDiagram' + content
        
        # Clean up multiple consecutive newlines and add proper indentation
        lines = result.split('\n')
        fixed_lines = []
        in_alt_block = False
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            # Check for alt/else/end to manage indentation
            if line.startswith('alt '):
                in_alt_block = True
                fixed_lines.append(f'    {line}')
            elif line == 'else':
                fixed_lines.append(f'    {line}')
            elif line == 'end':
                fixed_lines.append(f'    {line}')
                in_alt_block = False
            elif line.startswith('sequenceDiagram'):
                fixed_lines.append(line)
            elif line.startswith('participant '):
                fixed_lines.append(f'    {line}')
            else:
                # Messages and other content
                if in_alt_block:
                    fixed_lines.append(f'        {line}')
                else:
                    fixed_lines.append(f'    {line}')
        
        # Add empty line after participants
        result_lines = []
        participant_section = True
        
        for line in fixed_lines:
            result_lines.append(line)
            
            # Add empty line after the last participant
            if participant_section and line.strip().startswith('participant '):
                # Check if next line is not a participant
                current_index = fixed_lines.index(line)
                if current_index + 1 < len(fixed_lines):
                    next_line = fixed_lines[current_index + 1].strip()
                    if not next_line.startswith('participant '):
                        result_lines.append('')
                        participant_section = False
        
        return '\n'.join(result_lines)
    
    return code

def _clean_mermaid_code(mermaid_code: str) -> str:
    """Ultra-minimal cleaning - just return the LLM response with basic cleanup."""
    if not mermaid_code:
        return "flowchart TB\n    error[No diagram generated]"
    
    code = mermaid_code.strip()
    
    # Remove markdown code blocks if present
    if code.startswith('```mermaid'):
        code = code.replace('```mermaid', '').replace('```', '').strip()
    elif code.startswith('```'):
        code = code.replace('```', '').strip()
    
    # Only remove problematic Unicode that breaks Mermaid
    import re
    code = re.sub(r'[^\x00-\x7F]+', '', code)
    
    # If empty after cleaning, return error
    if not code.strip():
        return "flowchart TB\n    error[Empty diagram generated]"
    
    # Return as-is - let Mermaid handle everything else
    return code


async def build_context_diagram(requirement: str, recommendations: List[Dict],
                               enhanced_tech_stack: Optional[List[str]] = None,
                               architecture_explanation: Optional[str] = None) -> str:
    """Build a context diagram using LLM based on the specific requirement."""
    # Get tech stack for context (enhanced takes priority)
    tech_stack_context = ""
    if enhanced_tech_stack:
        app_logger.info(f"Using enhanced tech stack context for context diagram: {len(enhanced_tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(enhanced_tech_stack)}"
    elif recommendations and recommendations[0].get('tech_stack'):
        tech_stack = recommendations[0]['tech_stack']
        app_logger.info(f"Using recommendation tech stack context for context diagram: {len(tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(tech_stack)}"
    
    # Build comprehensive recommendation context
    recommendation_context = ""
    if recommendations:
        rec = recommendations[0]
        recommendation_context = f"""
SOLUTION ANALYSIS:
- Pattern: {rec.get('pattern_id', 'Unknown')}
- Feasibility: {rec.get('feasibility', 'Unknown')}
- Confidence: {rec.get('confidence', 0):.1%}
- Reasoning: {rec.get('reasoning', 'No reasoning available')}"""
        
        # Add agent roles if available
        if rec.get('agent_roles'):
            agent_roles = rec['agent_roles']
            roles_text = ', '.join([role.get('name', 'Unknown Agent') for role in agent_roles])
            recommendation_context += f"\n- Agent Roles: {roles_text}"
    
    prompt = f"""Generate a Mermaid context diagram (C4 Level 1) for this automation requirement:

REQUIREMENT: {requirement}{recommendation_context}

{tech_stack_context}

{f'''
ARCHITECTURE EXPLANATION: {architecture_explanation}

Use the architecture explanation above to understand system boundaries and external integrations.''' if architecture_explanation else ''}

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
5. DO NOT include any explanations, descriptions, or text before/after the Mermaid code
6. Start your response immediately with the diagram declaration
7. End your response immediately after the last diagram line
5. DO NOT include any explanations, descriptions, or text before/after the Mermaid code
6. Start your response immediately with the diagram declaration (e.g., "flowchart LR")
7. End your response immediately after the last diagram line
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

async def build_container_diagram(requirement: str, recommendations: List[Dict],
                                 enhanced_tech_stack: Optional[List[str]] = None,
                                 architecture_explanation: Optional[str] = None) -> str:
    """Build a container diagram using LLM based on the specific requirement."""
    # Get tech stack for context (enhanced takes priority)
    tech_stack_context = ""
    if enhanced_tech_stack:
        app_logger.info(f"Using enhanced tech stack context for container diagram: {len(enhanced_tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(enhanced_tech_stack)}"
    elif recommendations and recommendations[0].get('tech_stack'):
        tech_stack = recommendations[0]['tech_stack']
        app_logger.info(f"Using recommendation tech stack context for container diagram: {len(tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(tech_stack)}"
    
    # Build comprehensive recommendation context
    recommendation_context = ""
    if recommendations:
        rec = recommendations[0]
        recommendation_context = f"""
SOLUTION ANALYSIS:
- Pattern: {rec.get('pattern_id', 'Unknown')}
- Feasibility: {rec.get('feasibility', 'Unknown')}
- Confidence: {rec.get('confidence', 0):.1%}
- Reasoning: {rec.get('reasoning', 'No reasoning available')}"""
        
        # Add agent roles if available
        if rec.get('agent_roles'):
            agent_roles = rec['agent_roles']
            roles_text = ', '.join([role.get('name', 'Unknown Agent') for role in agent_roles])
            recommendation_context += f"\n- Agent Roles: {roles_text}"
    
    prompt = f"""Generate a Mermaid container diagram (C4 Level 2) for this automation requirement:

REQUIREMENT: {requirement}{recommendation_context}

{tech_stack_context}

{f'''
ARCHITECTURE EXPLANATION: {architecture_explanation}

Use the architecture explanation above to understand component relationships and ensure the diagram reflects the same architectural insights.''' if architecture_explanation else ''}

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
6. Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)
7. DO NOT include any explanations, descriptions, or text before/after the Mermaid code
8. Start your response immediately with the diagram declaration
9. End your response immediately after the last diagram line"""

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

async def build_tech_stack_wiring_diagram(requirement: str, recommendations: List[Dict], 
                                         enhanced_tech_stack: Optional[List[str]] = None,
                                         architecture_explanation: Optional[str] = None) -> str:
    """Build a technical wiring diagram showing how tech stack components connect and interact."""
    
    # Implement tech stack priority logic: enhanced > recommendations > default
    if enhanced_tech_stack:
        app_logger.info(f"Using enhanced tech stack for wiring diagram: {len(enhanced_tech_stack)} technologies")
        unique_tech_stack = enhanced_tech_stack
        tech_stack_str = ', '.join(unique_tech_stack)
    else:
        app_logger.info("No enhanced tech stack available, extracting from recommendations")
        # Extract tech stack from recommendations (fallback)
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
        app_logger.info(f"Using recommendation tech stack for wiring diagram: {len(unique_tech_stack)} technologies")

    # Add architecture explanation context if available
    architecture_context = ""
    if architecture_explanation:
        app_logger.info(f"Including architecture explanation in wiring diagram context: {len(architecture_explanation)} chars")
        architecture_context = f"""
ARCHITECTURE EXPLANATION: {architecture_explanation}

Use the architecture explanation above to understand how components interact and ensure the diagram reflects the same architectural insights."""
    else:
        app_logger.info("No architecture explanation available for wiring diagram")

    # Build comprehensive recommendation context
    recommendation_context = ""
    if recommendations:
        rec = recommendations[0]
        recommendation_context = f"""
SOLUTION ANALYSIS:
- Pattern: {rec.get('pattern_id', 'Unknown')}
- Feasibility: {rec.get('feasibility', 'Unknown')}
- Confidence: {rec.get('confidence', 0):.1%}
- Reasoning: {rec.get('reasoning', 'No reasoning available')}"""
        
        # Add agent roles if available
        if rec.get('agent_roles'):
            agent_roles = rec['agent_roles']
            roles_text = ', '.join([role.get('name', 'Unknown Agent') for role in agent_roles])
            recommendation_context += f"\n- Agent Roles: {roles_text}"

    prompt = f"""Generate a Mermaid technical wiring diagram showing how technology components connect and interact for this automation requirement:

REQUIREMENT: {requirement}{recommendation_context}

TECHNOLOGY STACK: {tech_stack_str}{architecture_context}

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
- Hexagons for queues: queue{{Message Queue}}

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
    queue{{Message Queue}}
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
DO NOT include any explanations, descriptions, or text before/after the Mermaid code.
Start your response immediately with the diagram declaration and end immediately after the last diagram line.
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

async def build_sequence_diagram(requirement: str, recommendations: List[Dict],
                                enhanced_tech_stack: Optional[List[str]] = None,
                                architecture_explanation: Optional[str] = None) -> str:
    """Build a sequence diagram using LLM based on the specific requirement."""
    # Get tech stack for context (enhanced takes priority)
    tech_stack_context = ""
    if enhanced_tech_stack:
        app_logger.info(f"Using enhanced tech stack context for sequence diagram: {len(enhanced_tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(enhanced_tech_stack)}"
    elif recommendations and recommendations[0].get('tech_stack'):
        tech_stack = recommendations[0]['tech_stack']
        app_logger.info(f"Using recommendation tech stack context for sequence diagram: {len(tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(tech_stack)}"
    
    # Build comprehensive recommendation context
    recommendation_context = ""
    if recommendations:
        rec = recommendations[0]
        recommendation_context = f"""
SOLUTION ANALYSIS:
- Pattern: {rec.get('pattern_id', 'Unknown')}
- Feasibility: {rec.get('feasibility', 'Unknown')}
- Confidence: {rec.get('confidence', 0):.1%}
- Reasoning: {rec.get('reasoning', 'No reasoning available')}"""
        
        # Add agent roles if available
        if rec.get('agent_roles'):
            agent_roles = rec['agent_roles']
            roles_text = ', '.join([role.get('name', 'Unknown Agent') for role in agent_roles])
            recommendation_context += f"\n- Agent Roles: {roles_text}"
    
    prompt = f"""Generate a Mermaid sequence diagram for this automation requirement:

REQUIREMENT: {requirement}{recommendation_context}

{tech_stack_context}

{f'''
ARCHITECTURE EXPLANATION: {architecture_explanation}

Use the architecture explanation above to understand the data flow and component interactions for the sequence.''' if architecture_explanation else ''}

Create a DETAILED sequence diagram showing the comprehensive step-by-step flow of the automated process:
- Initial user interactions and input validation
- Authentication and authorization steps
- Data retrieval and validation from multiple sources
- Business logic processing and rule evaluation
- Database operations (queries, updates, transactions)
- External API calls with request/response details
- Error handling and exception scenarios
- Decision points with alternative flows (use alt/else blocks)
- Notifications and user feedback
- Logging and audit trail steps
- Final response and cleanup operations

IMPORTANT: Include 8-15 detailed interaction steps, not just 3-4 high-level ones. Show the internal system processing, data transformations, and all significant operations that would occur in a real implementation.

Use Mermaid sequenceDiagram syntax:
- participant A as Actor Name
- A->>B: Message
- B-->>A: Response
- alt/else for conditions
- Note over A: Comments

Example format (showing detailed interactions):
sequenceDiagram
    participant W as Worker (Android Scanner)
    participant API as FastAPI Orchestrator
    participant Auth as Authentication Service
    participant DB as PostgreSQL (Inventory/Thresholds)
    participant Cache as Redis Cache
    participant ERP as ERP API
    participant Notify as Notification Service
    participant Log as Audit Logger
    
    W->>API: POST /scan {{sku, qty, location, ts, worker_id}}
    API->>Auth: Validate worker credentials
    Auth-->>API: Authentication token valid
    API->>Log: Log scan attempt {{worker_id, sku, timestamp}}
    API->>Cache: Check cached inventory for SKU
    Cache-->>API: Cache miss - no data
    API->>DB: SELECT inventory, reorder_threshold, supplier WHERE sku = ?
    DB-->>API: {{current_qty: 45, threshold: 50, supplier: "ACME Corp"}}
    API->>DB: UPDATE inventory SET current_qty = current_qty + scanned_qty
    DB-->>API: Update successful
    API-->>API: Calculate reorder_needed = (45 + qty < 50)
    
    alt Reorder needed AND not seasonal item
        API->>ERP: POST /purchase-orders {{sku, qty: 100, supplier: "ACME Corp"}}
        ERP-->>API: {{po_id: "PO-2024-001", status: "pending"}}
        API->>DB: INSERT purchase_order {{po_id, sku, qty, status}}
        API->>Notify: Send notification to procurement team
        Notify-->>API: Notification sent
    else High-value item OR seasonal restriction
        API->>Notify: Send approval request to manager
        Notify-->>API: Approval request queued
        API-->>W: {{status: "approval_required", message: "Manager approval needed"}}
    end
    
    API->>Log: Log transaction completion {{sku, action, result}}
    API-->>W: {{status: "success", inventory_updated: true, po_created: true}}

CRITICAL FORMATTING REQUIREMENTS:
1. Start with "sequenceDiagram" on its own line
2. Put each participant definition on a separate line with 4-space indentation
3. Put each message/interaction on a separate line with 4-space indentation
4. Use 8-space indentation inside alt/else blocks
5. IMPORTANT: Only use "end" to close "alt" blocks - each "alt" needs exactly one "end"
6. Do NOT add extra "end" statements - they are only for closing alt/else blocks
7. Add blank lines between major sections for readability
8. Return ONLY the raw Mermaid code without markdown formatting (no ```mermaid blocks)
9. DO NOT include any explanations, descriptions, or text before/after the Mermaid code
10. Start your response immediately with the diagram declaration
11. End your response immediately after the last diagram line
12. NEVER put everything on one line - each element must be on its own line with proper line breaks
13. Each participant, message, and control structure must be on a separate line"""

    try:
        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            return """sequenceDiagram
    participant U as User (Colleague)
    participant UI as Web Interface
    participant Auth as Authentication Service
    participant API as FastAPI Backend
    participant Valid as Input Validator
    participant DB as PostgreSQL Database
    participant Cache as Redis Cache
    participant Ext as External Recording API
    participant Queue as Message Queue
    participant Notify as Notification Service
    participant Log as Audit Logger
    
    U->>UI: Initiate conversation recording
    UI->>Auth: Validate user session
    Auth-->>UI: Session valid - return user details
    UI->>API: POST /start-recording {{user_id, customer_id, call_type}}
    API->>Valid: Validate input parameters
    Valid-->>API: Validation successful
    API->>Log: Log recording initiation {{user_id, timestamp}}
    API->>Cache: Check for existing active recordings
    Cache-->>API: No active recordings found
    API->>DB: INSERT recording_session {{user_id, customer_id, status: 'starting'}}
    DB-->>API: Session ID: REC-2024-001
    API->>Ext: POST /api/recordings/start {{session_id, metadata}}
    Ext-->>API: {{recording_url, stream_key, status: 'active'}}
    API->>DB: UPDATE recording_session SET recording_url, status = 'active'
    API->>Cache: Cache active recording {{session_id, recording_url}}
    API->>Queue: Publish recording_started event
    Queue->>Notify: Send notification to supervisor
    Notify-->>Queue: Notification sent
    API-->>UI: {{session_id: 'REC-2024-001', status: 'recording', recording_url}}
    UI-->>U: Display recording status and controls"""
        
        response = await make_llm_request(prompt, provider_config)
        return _clean_mermaid_code(response.strip())
    except Exception as e:
        return f"""sequenceDiagram
  participant U as User
  participant E as Error
  
  U->>E: Sequence diagram generation failed: {str(e)}"""


async def build_agent_interaction_diagram(requirement: str, recommendations: List[Dict],
                                        enhanced_tech_stack: Optional[List[str]] = None,
                                        architecture_explanation: Optional[str] = None) -> str:
    """Build an agent interaction diagram showing how AI agents collaborate and make decisions."""
    try:
        # Get tech stack for context (enhanced takes priority)
        tech_stack_context = ""
        if enhanced_tech_stack:
            app_logger.info(f"Using enhanced tech stack context for agent interaction diagram: {len(enhanced_tech_stack)} technologies")
            tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(enhanced_tech_stack)}"
        elif recommendations and recommendations[0].get('tech_stack'):
            tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(recommendations[0]['tech_stack'])}"
        
        # Get architecture explanation for context
        architecture_context = ""
        if architecture_explanation:
            app_logger.info("Using architecture explanation context for agent interaction diagram")
            architecture_context = f"ARCHITECTURE CONTEXT: {architecture_explanation}"
        
        # Extract agent roles from recommendations
        agent_roles_context = ""
        agent_roles = []
        for rec in recommendations:
            if rec.get('agent_roles'):
                agent_roles.extend(rec['agent_roles'])
        
        if agent_roles:
            agent_roles_context = f"AGENT ROLES: {agent_roles}"
        
        # Extract more specific context from the requirement
        requirement_lower = requirement.lower()
        domain_context = ""
        
        # Identify the domain/industry for better agent naming
        if any(word in requirement_lower for word in ['customer', 'support', 'service', 'ticket']):
            domain_context = "DOMAIN: Customer Service/Support"
        elif any(word in requirement_lower for word in ['finance', 'payment', 'invoice', 'accounting']):
            domain_context = "DOMAIN: Finance/Accounting"
        elif any(word in requirement_lower for word in ['hr', 'employee', 'recruitment', 'hiring']):
            domain_context = "DOMAIN: Human Resources"
        elif any(word in requirement_lower for word in ['inventory', 'supply', 'warehouse', 'logistics']):
            domain_context = "DOMAIN: Supply Chain/Logistics"
        elif any(word in requirement_lower for word in ['marketing', 'campaign', 'lead', 'sales', 'data', 'analytics', 'report', 'dashboard']):
            if any(word in requirement_lower for word in ['sales', 'marketing', 'campaign', 'lead']):
                domain_context = "DOMAIN: Marketing/Sales"
            else:
                domain_context = "DOMAIN: Data Analytics"
        elif any(word in requirement_lower for word in ['security', 'compliance', 'audit', 'risk', 'monitor', 'threat']):
            domain_context = "DOMAIN: Security/Compliance"
        elif any(word in requirement_lower for word in ['resume', 'interview', 'candidate', 'hiring', 'recruitment']):
            domain_context = "DOMAIN: Human Resources"
        
        # Build comprehensive recommendation context
        recommendation_context = ""
        if recommendations:
            rec = recommendations[0]
            recommendation_context = f"""
SOLUTION ANALYSIS:
- Pattern: {rec.get('pattern_id', 'Unknown')}
- Feasibility: {rec.get('feasibility', 'Unknown')}
- Confidence: {rec.get('confidence', 0):.1%}
- Reasoning: {rec.get('reasoning', 'No reasoning available')}"""
        
        prompt = f"""Create a Mermaid flowchart diagram showing how autonomous AI agents interact, coordinate, and make decisions for this specific requirement:

REQUIREMENT: {requirement}{recommendation_context}

{domain_context}
{tech_stack_context}
{architecture_context}
{agent_roles_context}

CRITICAL REQUIREMENT: You MUST create agent names that are SPECIFIC to this requirement. DO NOT use generic names like "Primary_Agent", "Agent1", "Primary_Autonom", or similar generic placeholders.

GOOD examples based on requirement context:
- Customer support: "TicketAnalysisAgent", "CustomerContextAgent", "ResponseGeneratorAgent"
- Finance: "InvoiceProcessorAgent", "PaymentValidatorAgent", "ComplianceCheckerAgent"  
- HR: "ResumeScreenerAgent", "InterviewSchedulerAgent", "CandidateRankerAgent"
- Data: "DataCollectorAgent", "PatternAnalyzerAgent", "ReportGeneratorAgent"

BAD examples (DO NOT USE): "Primary_Agent", "Agent1", "Primary_Autonom", "GenericAgent"

Create a flowchart that shows:
1. Specific AI agents with descriptive names based on the requirement (NOT generic names like "Primary_Agent")
2. How agents communicate and coordinate with each other
3. Decision points where agents make autonomous choices
4. Data flow between agents with specific data types
5. External systems or APIs that agents interact with
6. Feedback loops and learning mechanisms

Use Mermaid flowchart syntax with:
- Rectangular nodes for agents: A[Specific Agent Name]
- Diamond nodes for decision points: D{{Decision Point}}
- Circular nodes for external systems: E((External System))
- Arrows showing communication: A --> B
- Labels on arrows showing specific data/messages: A -->|"specific data type"| B

Make the agent names and interactions SPECIFIC to the requirement context, not generic placeholders.

Return ONLY the Mermaid code, starting with 'flowchart TD' or 'flowchart LR'."""

        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            # Create a contextual fallback based on the requirement
            requirement_lower = requirement.lower()
            if any(word in requirement_lower for word in ['customer', 'support', 'service', 'ticket']):
                return """flowchart TD
    U[User Request] --> TA[Ticket Analysis Agent]
    TA --> CA[Customer Context Agent]
    TA --> KA[Knowledge Agent]
    CA -->|customer history| RG[Response Generator Agent]
    KA -->|relevant solutions| RG
    RG --> QA[Quality Assurance Agent]
    QA -->|approved| R[Customer Response]
    QA -->|needs revision| RG
    
    style TA fill:#FF6B6B,stroke:#E53E3E,stroke-width:3px
    style CA fill:#4ECDC4,stroke:#38B2AC,stroke-width:3px
    style KA fill:#45B7D1,stroke:#3182CE,stroke-width:3px
    style RG fill:#F7DC6F,stroke:#F1C40F,stroke-width:3px
    style QA fill:#DDA0DD,stroke:#9932CC,stroke-width:3px"""
            else:
                # Generic fallback for other domains
                return """flowchart TD
    U[User Request] --> CA[Coordinator Agent]
    CA --> DA[Data Processing Agent]
    CA --> AA[Analysis Agent]
    DA -->|processed data| AA
    AA -->|insights| EA[Execution Agent]
    EA --> VA[Validation Agent]
    VA -->|approved| R[Final Result]
    VA -->|needs revision| EA
    
    style CA fill:#FF6B6B,stroke:#E53E3E,stroke-width:3px
    style DA fill:#4ECDC4,stroke:#38B2AC,stroke-width:3px
    style AA fill:#45B7D1,stroke:#3182CE,stroke-width:3px
    style EA fill:#F7DC6F,stroke:#F1C40F,stroke-width:3px
    style VA fill:#DDA0DD,stroke:#9932CC,stroke-width:3px"""
        
        response = await make_llm_request(prompt, provider_config, purpose="agent_interaction_diagram")
        
        # Debug logging with more detail
        app_logger.info(f"Agent interaction diagram - Raw response length: {len(response) if response else 0}")
        if response:
            # Log first 200 characters to see what the LLM is generating
            app_logger.info(f"Agent interaction diagram - Response preview: {response[:200]}...")
            
            # Check if response contains generic agent names
            if "Primary_Autonom" in response or "Agent1" in response or "Agent2" in response:
                app_logger.warning("Agent interaction diagram contains generic agent names - LLM may not be following instructions")
        
        cleaned_code = _clean_mermaid_code(response.strip())
        app_logger.info(f"Agent interaction diagram - Cleaned code length: {len(cleaned_code) if cleaned_code else 0}")
        
        # Additional validation - if we detect generic names, try to improve them
        if cleaned_code and ("Primary_Autonom" in cleaned_code or "Agent1" in cleaned_code):
            app_logger.warning("Detected generic agent names in cleaned code, attempting to contextualize")
            # Try to replace generic names with more contextual ones
            requirement_lower = requirement.lower()
            if any(word in requirement_lower for word in ['customer', 'support', 'service', 'ticket']):
                replacements = {
                    "Primary_Autonom": "TicketAnalyzer",
                    "Primary_Autonom1": "CustomerContext", 
                    "Primary_Autonom2": "ResponseGenerator",
                    "Primary_Autonom3": "QualityChecker",
                    "Primary_Autonom4": "EscalationHandler"
                }
            elif any(word in requirement_lower for word in ['data', 'analytics', 'report', 'dashboard']):
                replacements = {
                    "Primary_Autonom": "DataCollector",
                    "Primary_Autonom1": "PatternAnalyzer",
                    "Primary_Autonom2": "ReportGenerator", 
                    "Primary_Autonom3": "QualityValidator",
                    "Primary_Autonom4": "InsightExtractor"
                }
            elif any(word in requirement_lower for word in ['finance', 'payment', 'invoice', 'accounting']):
                replacements = {
                    "Primary_Autonom": "InvoiceProcessor",
                    "Primary_Autonom1": "PaymentValidator",
                    "Primary_Autonom2": "ComplianceChecker",
                    "Primary_Autonom3": "FraudDetector", 
                    "Primary_Autonom4": "ReportGenerator"
                }
            elif any(word in requirement_lower for word in ['resume', 'interview', 'candidate', 'hiring', 'recruitment']):
                replacements = {
                    "Primary_Autonom": "ResumeScreener",
                    "Primary_Autonom1": "CandidateRanker",
                    "Primary_Autonom2": "InterviewScheduler",
                    "Primary_Autonom3": "SkillMatcher",
                    "Primary_Autonom4": "ReferenceChecker"
                }
            else:
                replacements = {
                    "Primary_Autonom": "CoordinatorAgent",
                    "Primary_Autonom1": "ProcessorAgent",
                    "Primary_Autonom2": "DecisionAgent",
                    "Primary_Autonom3": "ValidatorAgent",
                    "Primary_Autonom4": "ExecutorAgent"
                }
            
            # Apply replacements in order of specificity (longer names first to avoid partial matches)
            sorted_replacements = sorted(replacements.items(), key=lambda x: len(x[0]), reverse=True)
            for generic_name, specific_name in sorted_replacements:
                cleaned_code = cleaned_code.replace(generic_name, specific_name)
        
        # Final check for any remaining generic patterns
        generic_patterns = ["Agent1", "Agent2", "Agent3", "Agent4", "GenericAgent", "Primary_Agent"]
        for pattern in generic_patterns:
            if pattern in cleaned_code:
                app_logger.warning(f"Still found generic pattern '{pattern}' in agent diagram")
                # Replace with a contextual fallback
                cleaned_code = cleaned_code.replace(pattern, "SpecializedAgent")
        
        return cleaned_code
    except Exception as e:
        app_logger.error(f"Agent interaction diagram generation failed: {e}")
        # Create a contextual error fallback
        requirement_lower = requirement.lower()
        if any(word in requirement_lower for word in ['customer', 'support', 'service']):
            agent_type = "Customer Service"
            agents = ["Ticket Analyzer", "Customer Context", "Response Generator"]
        elif any(word in requirement_lower for word in ['finance', 'payment', 'invoice']):
            agent_type = "Finance"
            agents = ["Invoice Processor", "Payment Validator", "Compliance Checker"]
        elif any(word in requirement_lower for word in ['data', 'analytics', 'report']):
            agent_type = "Data Analytics"
            agents = ["Data Collector", "Pattern Analyzer", "Report Generator"]
        else:
            agent_type = "Generic"
            agents = ["Coordinator", "Processor", "Decision Maker"]
        
        return f"""flowchart TD
  U[User Request] --> A[{agents[0]} Agent]
  A --> B[{agents[1]} Agent]
  A --> C[{agents[2]} Agent]
  B -->|data| C
  C --> R[Result]
  
  note[{agent_type} agent interaction diagram - LLM generation failed: {str(e)}]
  
  style A fill:#FF6B6B,stroke:#E53E3E,stroke-width:3px
  style B fill:#4ECDC4,stroke:#38B2AC,stroke-width:3px
  style C fill:#45B7D1,stroke:#3182CE,stroke-width:3px"""


async def build_infrastructure_diagram(requirement: str, recommendations: List[Dict],
                                      enhanced_tech_stack: Optional[List[str]] = None,
                                      architecture_explanation: Optional[str] = None) -> Dict[str, Any]:
    """Build an infrastructure diagram specification using LLM based on the specific requirement."""
    # Get tech stack for context (enhanced takes priority)
    tech_stack_context = ""
    if enhanced_tech_stack:
        app_logger.info(f"Using enhanced tech stack context for infrastructure diagram: {len(enhanced_tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(enhanced_tech_stack)}"
    elif recommendations and recommendations[0].get('tech_stack'):
        tech_stack = recommendations[0]['tech_stack']
        app_logger.info(f"Using recommendation tech stack context for infrastructure diagram: {len(tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(tech_stack)}"
    
    # Build comprehensive recommendation context
    recommendation_context = ""
    if recommendations:
        rec = recommendations[0]
        recommendation_context = f"""
SOLUTION ANALYSIS:
- Pattern: {rec.get('pattern_id', 'Unknown')}
- Feasibility: {rec.get('feasibility', 'Unknown')}
- Confidence: {rec.get('confidence', 0):.1%}
- Reasoning: {rec.get('reasoning', 'No reasoning available')}"""
        
        # Add agent roles if available
        if rec.get('agent_roles'):
            agent_roles = rec['agent_roles']
            roles_text = ', '.join([role.get('name', 'Unknown Agent') for role in agent_roles])
            recommendation_context += f"\n- Agent Roles: {roles_text}"
    
    # Detect if this is an agentic AI system
    is_agentic_system = False
    agentic_keywords = ['langchain', 'crewai', 'langgraph', 'semantic kernel', 'agent', 'agentic', 'autonomous']
    
    if tech_stack_context:
        tech_lower = tech_stack_context.lower()
        is_agentic_system = any(keyword in tech_lower for keyword in agentic_keywords)
    
    if recommendation_context:
        rec_lower = recommendation_context.lower()
        is_agentic_system = is_agentic_system or any(keyword in rec_lower for keyword in agentic_keywords)

    if is_agentic_system:
        prompt = f"""Generate a detailed infrastructure diagram specification for this AGENTIC AI AUTOMATION requirement:

REQUIREMENT: {requirement}{recommendation_context}

{tech_stack_context}

{f'''
ARCHITECTURE EXPLANATION: {architecture_explanation}

Use the architecture explanation above to understand infrastructure requirements and component deployment.''' if architecture_explanation else ''}

CRITICAL: This is an AGENTIC AI SYSTEM. Focus on AI agent orchestration infrastructure, not traditional web services.

Create a JSON specification showing AGENTIC AI INFRASTRUCTURE:
- AI Agent Orchestration Platforms (LangChain, CrewAI, LangGraph, Semantic Kernel)
- AI Model Services (OpenAI, Claude, GPT-4o, Assistants API)
- Agent Communication & Coordination Systems
- Knowledge Bases & Vector Databases (Neo4j, Pinecone, Weaviate)
- Workflow Orchestration (Pega, Temporal, Airflow)
- Rule Engines & Decision Systems (Drools, business rules)
- Integration APIs (Salesforce, external systems)
- Agent Memory & State Management
- Multi-Agent Communication Buses

IMPORTANT: Represent agentic frameworks as specialized infrastructure components, not generic compute services.

Return a JSON object with this structure:
{{
  "title": "Infrastructure Diagram Title",
  "clusters": [
    {{
      "provider": "aws|gcp|azure|k8s|onprem|agentic",
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
- Agentic: langchain_orchestrator, crewai_coordinator, agent_memory, vector_db, rule_engine, workflow_engine
- SaaS: openai_api, claude_api, salesforce_api, semantic_kernel, assistants_api

IMPORTANT: Return ONLY valid JSON without markdown formatting."""
    else:
        prompt = f"""Generate a detailed and indepth infrastructure diagram specification for this automation requirement:

REQUIREMENT: {requirement}{recommendation_context}

{tech_stack_context}

{f'''
ARCHITECTURE EXPLANATION: {architecture_explanation}

Use the architecture explanation above to understand infrastructure requirements and component deployment.''' if architecture_explanation else ''}

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
            
            # Handle various markdown code block formats
            if cleaned_response.startswith('```json'):
                cleaned_response = cleaned_response[7:]
            elif cleaned_response.startswith('```'):
                cleaned_response = cleaned_response[3:]
            
            if cleaned_response.endswith('```'):
                cleaned_response = cleaned_response[:-3]
            
            cleaned_response = cleaned_response.strip()
            
            # Additional cleaning for any remaining formatting
            if not cleaned_response.startswith('{'):
                # Find the first { character
                start_idx = cleaned_response.find('{')
                if start_idx != -1:
                    cleaned_response = cleaned_response[start_idx:]
            
            if not cleaned_response.endswith('}'):
                # Find the last } character
                end_idx = cleaned_response.rfind('}')
                if end_idx != -1:
                    cleaned_response = cleaned_response[:end_idx + 1]
            
            app_logger.info(f"Parsing infrastructure JSON: {len(cleaned_response)} characters")
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

async def build_c4_diagram(requirement: str, recommendations: List[Dict],
                          enhanced_tech_stack: Optional[List[str]] = None,
                          architecture_explanation: Optional[str] = None) -> str:
    """Build a C4 diagram using LLM with proper Mermaid C4 syntax."""
    # Get tech stack for context (enhanced takes priority)
    tech_stack_context = ""
    if enhanced_tech_stack:
        app_logger.info(f"Using enhanced tech stack context for C4 diagram: {len(enhanced_tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(enhanced_tech_stack)}"
    elif recommendations and recommendations[0].get('tech_stack'):
        tech_stack = recommendations[0]['tech_stack']
        app_logger.info(f"Using recommendation tech stack context for C4 diagram: {len(tech_stack)} technologies")
        tech_stack_context = f"TECHNOLOGY CONTEXT: {', '.join(tech_stack)}"
    
    # Build comprehensive recommendation context
    recommendation_context = ""
    if recommendations:
        rec = recommendations[0]
        recommendation_context = f"""
SOLUTION ANALYSIS:
- Pattern: {rec.get('pattern_id', 'Unknown')}
- Feasibility: {rec.get('feasibility', 'Unknown')}
- Confidence: {rec.get('confidence', 0):.1%}
- Reasoning: {rec.get('reasoning', 'No reasoning available')}"""
        
        # Add agent roles if available
        if rec.get('agent_roles'):
            agent_roles = rec['agent_roles']
            roles_text = ', '.join([role.get('name', 'Unknown Agent') for role in agent_roles])
            recommendation_context += f"\n- Agent Roles: {roles_text}"
    
    prompt = f"""Generate a proper C4 diagram using Mermaid's C4 syntax for this automation requirement:

REQUIREMENT: {requirement}{recommendation_context}

{tech_stack_context}

{f'''
ARCHITECTURE EXPLANATION: {architecture_explanation}

Use the architecture explanation above to understand system architecture and component relationships.''' if architecture_explanation else ''}

Create a C4 Context or Container diagram using proper Mermaid C4 syntax. Choose the appropriate level:
- C4Context for high-level system overview showing external actors and systems
- C4Container for detailed view showing internal containers and their interactions

Use proper Mermaid C4 syntax with these elements:
- Person(id, "Name", "Description") for users/actors
- System(id, "Name", "Description") for internal systems
- System_Ext(id, "Name", "Description") for external systems
- Container(id, "Name", "Technology", "Description") for containers (if using C4Container)
- Rel(from, to, "Label") for relationships
- Rel(from, to, "Label", "Technology") for relationships with technology details
- ContainerDb(id, "Name", "Technology", "Description") for data stores

Relationships must be between elements (Person/System/Container). Do not use Rel() with System_Boundary.
Model cloud/platforms as System_Ext(...) and relate containers to them, or omit and use a C4Deployment diagram for runtime placement.

Example C4Context format:
C4Context
    title System Context for [System Name]
    
    Person(user, "End User", "Person using the automated system")
    System(main_system, "Automation System", "Core system handling the automation workflow")
    System_Ext(external_api, "External API", "Third-party service integration")
    System_Ext(database, "Database System", "Data storage and retrieval")
    
    Rel(user, main_system, "Uses", "Web/Mobile")
    Rel(main_system, external_api, "Integrates with", "REST API")
    Rel(main_system, database, "Stores/Retrieves data", "SQL")

Example C4Container format:
C4Container
    title Container Diagram for [System Name]
    
    Person(user, "End User", "Person using the system")
    Person_Ext(agent, "Support Agent", "Back-office user (if applicable)")
    
    System_Boundary(system, "Automation System") {{
        Container(web_app, "Web Application", "React/Angular", "User interface")
        Container(api, "API Service", "Node.js/Python", "REST API and business logic")
        Container(queue, "Message Queue", "RabbitMQ/SQS", "Async processing")
        ContainerDb(database, "Database", "PostgreSQL/MongoDB", "Transactional data")
        Container(indexer_worker, "Indexer Worker", "Python", "Consumes messages and updates search index")
        Container(search, "Search Engine", "Elasticsearch", "Full-text search")
    }}
    
    System_Ext(identity_provider, "Identity Provider", "OIDC/OAuth2 (e.g., Active Directory/Azure AD)")
    System_Ext(external_api, "External Service", "Third-party integration")
    System_Ext(cloud, "Cloud Platform", "e.g., AWS/Azure/GCP")
    
    Rel(user, web_app, "Uses", "HTTPS")
    Rel(web_app, api, "Makes API calls", "REST/JSON")
    Rel(web_app, api, "Sends JWT/OIDC token", "HTTPS")
    Rel(api, identity_provider, "Validates tokens", "OIDC/OAuth2/LDAP")
    Rel(api, queue, "Publishes messages", "AMQP")
    Rel(queue, indexer_worker, "Delivers messages", "AMQP")
    Rel(indexer_worker, search, "Indexes/updates", "Elasticsearch API")
    Rel(api, search, "Queries search index", "Elasticsearch API")
    Rel(api, database, "Reads/Writes", "SQL")
    Rel(api, external_api, "Integrates", "REST API")
    
    Rel(web_app, cloud, "Hosted on")
    Rel(api, cloud, "Runs on")
    Rel(database, cloud, "Managed database")
    Rel(queue, cloud, "Managed broker")
Make the diagram tight and realistic. Apply ALL of these rules:

TIGHTNESS RULES (enforced):
- Minimality: Only include elements explicitly present in REQUIREMENT, RECOMMENDATIONS, TECHNOLOGY CONTEXT, or ARCHITECTURE EXPLANATION. Do not invent extra systems.
- Diagram level: If ≥2 internal components/technologies are mentioned, use C4Container; otherwise use C4Context.
- IDs & params: Element IDs must be lowercase_snake_case and unique. Person/System/System_Ext use exactly 3 params. Container/ContainerDb use exactly 4 params in this order: ("Technology", "Description").
- Data stores: Use ContainerDb for databases only. Do not model databases as System_Ext unless clearly external/managed outside the solution boundary.
- Auth pattern: Frontend never talks LDAP. Use OIDC/OAuth2:
  Rel(frontend, backend, "Sends JWT/OIDC token", "HTTPS")
  Rel(backend, identity_provider, "Validates tokens", "OIDC/OAuth2/LDAP")
  Model the IdP as System_Ext(identity_provider, "Identity Provider", "Authentication and authorization").
- Messaging + search: If BOTH a message broker and Elasticsearch appear, add a dedicated worker that consumes from the broker and writes to Elasticsearch. Do NOT create Rel(queue, elasticsearch, ...).
  Example containers (names may vary):
  Container(indexer_worker, "Indexer Worker", "Python", "Consumes messages and updates search index")
- Cloud hosting: If a cloud is present, only create relations from containers TO the cloud (e.g., "Hosted on", "Runs on", "Managed"). Never from the cloud to containers.
- Relationship verbs: Prefer these labels where sensible—"Uses", "Reads/Writes", "Publishes", "Consumes", "Integrates", "Queries", "Indexes".
- No boundary relations: Never use Rel() with System_Boundary.
- De-duplication: No duplicate or contradictory relationships. Avoid cycles unless essential.
- Size cap (readability): Max 2 Person/Person_Ext, max 6 containers inside the boundary, max 5 System_Ext.

Validate before returning:
1) No Rel involving System_Boundary
2) Every Container/ContainerDb has 4 params with correct order
3) No direct Rel(queue, elasticsearch, ...) if both exist
4) No Rel(frontend, ldap, ...) or LDAP directly from frontend
5) All IDs are unique lowercase_snake_case
6) Output ONLY raw Mermaid C4 code (no backticks, no prose)

CRITICAL FORMATTING REQUIREMENTS:
1. Start with either "C4Context" or "C4Container" (choose based on detail level needed)
2. Include a descriptive title using "title [description]"
3. Each C4 element must be on its own line
4. Use proper C4 element syntax with parentheses and quotes
5. Relationships use Rel(from, to, "label") or Rel(from, to, "label", "technology")
6. For Container diagrams, use System_Boundary for grouping containers
7. System_Boundary must have matching curly braces: System_Boundary(id, "Name") { ... }
8. Return ONLY the raw Mermaid C4 code without markdown formatting (no ```mermaid blocks)
9. Ensure all element IDs are unique and referenced correctly in relationships"""

    try:
        # Use the current provider config to generate the diagram
        provider_config = st.session_state.get('provider_config', {})
        if provider_config.get('provider') == 'fake':
            # Fallback for fake provider - provide realistic C4 diagram structure
            return """C4Context
    title System Context for Automated Process
    
    Person(user, "Business User", "Person who initiates and monitors the automated process")
    Person(admin, "System Administrator", "Manages and configures the automation system")
    
    System(automation_system, "Automation System", "Core system that handles business process automation")
    
    System_Ext(external_api, "External API", "Third-party service for data integration")
    System_Ext(notification_service, "Notification Service", "Email/SMS service for alerts")
    System_Ext(audit_system, "Audit System", "Compliance and logging system")
    
    Rel(user, automation_system, "Initiates processes", "Web Interface")
    Rel(admin, automation_system, "Configures", "Admin Panel")
    Rel(automation_system, external_api, "Fetches data", "REST API")
    Rel(automation_system, notification_service, "Sends alerts", "SMTP/SMS")
    Rel(automation_system, audit_system, "Logs activities", "Secure API")"""
        
        response = await make_llm_request(prompt, provider_config)
        return _clean_mermaid_code(response.strip())
    except Exception as e:
        return f"""C4Context
    title C4 Diagram Generation Error
    
    Person(user, "User", "Person requesting C4 diagram")
    System(error_system, "Error System", "Diagram generation failed")
    System_Ext(llm_provider, "LLM Provider", "Failed to generate proper C4 syntax")
    
    Rel(user, error_system, "Encountered error")
    Rel(llm_provider, error_system, "Generated error: {str(e)}")
    
    %% Troubleshooting:
    %% 1. Try generating again
    %% 2. Switch to OpenAI provider (best C4 support)
    %% 3. Ensure requirement is suitable for C4 modeling"""


# Configuration
API_BASE_URL = "http://localhost:8000"
POLL_INTERVAL = 5  # seconds - reduced polling to stay under rate limits


class AutomatedAIAssessmentUI:
    """Main Streamlit UI class for Automated AI Assessment (AAA)."""
    
    def __init__(self):
        self.setup_page_config()
        self.initialize_services()
        self.initialize_session_state()
    
    def setup_page_config(self):
        """Configure Streamlit page settings."""
        st.set_page_config(
            page_title="Automated AI Assessment (AAA)",
            page_icon="🤖",
            layout="wide",
            initial_sidebar_state="expanded"
        )
    
    def initialize_services(self):
        """Initialize services through the service registry."""
        global app_logger, llm_provider_service, OPENAI_AVAILABLE
        
        # Always set up a fallback logger first
        import logging
        fallback_logger = logging.getLogger(__name__)
        app_logger = fallback_logger
        
        try:
            # Register core services if not already registered
            from app.core.service_registration import register_core_services
            from app.core.registry import get_registry
            
            registry = get_registry()
            
            # Check if services are already registered, if not register them
            if not registry.has('logger'):
                register_core_services()
            
            # Try to get the proper logger service
            try:
                service_logger = require_service('logger', context='streamlit_app initialization')
                if service_logger:
                    app_logger = service_logger
            except Exception as logger_error:
                fallback_logger.warning(f"Could not get logger service, using fallback: {logger_error}")
            
            # Get LLM provider service
            llm_provider_service = optional_service('llm_provider_factory', context='streamlit_app initialization')
            OPENAI_AVAILABLE = llm_provider_service is not None
            
            app_logger.info("🚀 Streamlit app services initialized successfully")
            app_logger.info(f"📊 LLM provider service available: {OPENAI_AVAILABLE}")
            
        except Exception as e:
            # Use fallback logger for error reporting
            fallback_logger.error(f"Failed to initialize services: {e}")
            
            # Set fallback values
            llm_provider_service = None
            OPENAI_AVAILABLE = False
    
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
            elif method.upper() == "PUT":
                response = await client.put(url, json=data)
            else:
                raise ValueError(f"Unsupported HTTP method: {method}")
            
            if response.status_code == 404:
                raise ValueError("Session not found")
            elif response.status_code != 200:
                # Try to parse the error response for enhanced security feedback
                try:
                    error_data = response.json()
                    if error_data.get("type") == "security_feedback":
                        # This is enhanced security feedback - format it nicely
                        message = error_data.get("message", "Security validation failed")
                        raise SecurityFeedbackException(message)
                    else:
                        # Standard error
                        error_msg = error_data.get("message", response.text)
                        raise ValueError(f"API error: {response.status_code} - {error_msg}")
                except (ValueError, KeyError):
                    # Fallback to raw response text
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
                                response = asyncio.run(api_client.discover_models({
                                    "provider": "openai",
                                    "api_key": api_key
                                }))
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
                                response = asyncio.run(api_client.discover_models({
                                    "provider": "claude",
                                    "api_key": api_key
                                }))
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
            
            # Authentication method selection
            auth_method = st.sidebar.radio(
                "Authentication Method",
                ["AWS Credentials", "Bedrock API Key"],
                help="Choose authentication method for Bedrock"
            )
            
            # Initialize variables
            aws_access_key_id = ""
            aws_secret_access_key = ""
            aws_session_token = ""
            bedrock_api_key = ""
            
            if auth_method == "AWS Credentials":
                st.sidebar.markdown("**AWS Credentials**")
                
                # Option to choose input method
                creds_input_method = st.sidebar.radio(
                    "Credentials Input Method",
                    ["Individual Fields", "Combined Format"],
                    help="Choose how to enter AWS credentials"
                )
            
                if creds_input_method == "Individual Fields":
                    aws_access_key_id = st.sidebar.text_input(
                        "AWS Access Key ID",
                        value=st.session_state.provider_config.get('aws_access_key_id', ''),
                        type="password",
                        help="Your AWS Access Key ID"
                    )
                    aws_secret_access_key = st.sidebar.text_input(
                        "AWS Secret Access Key", 
                        value=st.session_state.provider_config.get('aws_secret_access_key', ''),
                        type="password",
                        help="Your AWS Secret Access Key"
                    )
                    aws_session_token = st.sidebar.text_input(
                        "AWS Session Token (Optional)",
                        value=st.session_state.provider_config.get('aws_session_token', ''),
                        type="password",
                        help="Optional AWS Session Token for temporary credentials"
                    )
                else:
                    # Combined format
                    combined_creds = st.sidebar.text_area(
                        "AWS Credentials (Combined)",
                        value=st.session_state.provider_config.get('combined_aws_creds', ''),
                        height=100,
                        help="Enter credentials in format:\nAWS_ACCESS_KEY_ID=your_key_id\nAWS_SECRET_ACCESS_KEY=your_secret_key\nAWS_SESSION_TOKEN=your_token (optional)"
                    )
                    
                    # Parse combined credentials
                    if combined_creds:
                        for line in combined_creds.strip().split('\n'):
                            if '=' in line:
                                key, value = line.split('=', 1)
                                key = key.strip()
                                value = value.strip()
                                if key == "AWS_ACCESS_KEY_ID":
                                    aws_access_key_id = value
                                elif key == "AWS_SECRET_ACCESS_KEY":
                                    aws_secret_access_key = value
                                elif key == "AWS_SESSION_TOKEN":
                                    aws_session_token = value
                
                # Generate short-term credentials button
                if st.sidebar.button("🔑 Generate Short-term Credentials", key="generate_creds"):
                    if aws_access_key_id and aws_secret_access_key:
                        with st.sidebar:
                            with st.spinner("Generating short-term credentials..."):
                                try:
                                    response = asyncio.run(self.make_api_request(
                                        "POST",
                                        "/providers/bedrock/generate-credentials",
                                        {
                                            "aws_access_key_id": aws_access_key_id,
                                            "aws_secret_access_key": aws_secret_access_key,
                                            "aws_session_token": aws_session_token,
                                            "region": region,
                                            "duration_seconds": 3600
                                        }
                                    ))
                                    if response.get('ok'):
                                        creds = response.get('credentials', {})
                                        st.session_state.provider_config.update({
                                            'aws_access_key_id': creds.get('aws_access_key_id', ''),
                                            'aws_secret_access_key': creds.get('aws_secret_access_key', ''),
                                            'aws_session_token': creds.get('aws_session_token', ''),
                                        })
                                        st.success(f"✅ Short-term credentials generated! Valid until {creds.get('expiration', 'unknown')}")
                                        st.rerun()
                                    else:
                                        st.error(f"Failed to generate credentials: {response.get('message', 'Unknown error')}")
                                except Exception as e:
                                    st.error(f"Error generating credentials: {str(e)}")
                    else:
                        st.sidebar.error("AWS Access Key ID and Secret Access Key are required to generate short-term credentials")
            
            else:  # Bedrock API Key
                st.sidebar.markdown("**Bedrock API Key**")
                bedrock_api_key = st.sidebar.text_input(
                    "Bedrock API Key",
                    value=st.session_state.provider_config.get('bedrock_api_key', ''),
                    type="password",
                    help="Your long-term Bedrock API key (see AWS documentation)"
                )
            
            # Discover models button
            if st.sidebar.button("🔍 Discover Models", key="discover_bedrock"):
                with st.sidebar:
                    with st.spinner("Discovering Bedrock models..."):
                        try:
                            request_data = {
                                "provider": "bedrock",
                                "region": region
                            }
                            
                            if auth_method == "AWS Credentials":
                                request_data.update({
                                    "aws_access_key_id": aws_access_key_id,
                                    "aws_secret_access_key": aws_secret_access_key,
                                    "aws_session_token": aws_session_token
                                })
                            else:
                                request_data["bedrock_api_key"] = bedrock_api_key
                            
                            response = asyncio.run(api_client.discover_models(request_data))
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
                                response = asyncio.run(api_client.discover_models({
                                    "provider": "internal",
                                    "endpoint_url": endpoint_url,
                                    "api_key": api_key if api_key else None
                                }))
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
        config_update = {
            'provider': current_provider,
            'model': model,
            'api_key': api_key if api_key else None,  # Use None instead of empty string
            'endpoint_url': endpoint_url if endpoint_url else None,
            'region': region
        }
        
        # Add authentication details for Bedrock
        if current_provider == "bedrock":
            config_update.update({
                'auth_method': auth_method,
                'aws_access_key_id': aws_access_key_id,
                'aws_secret_access_key': aws_secret_access_key,
                'aws_session_token': aws_session_token,
                'bedrock_api_key': bedrock_api_key,
                'combined_aws_creds': combined_creds if auth_method == "AWS Credentials" and creds_input_method == "Combined Format" else ""
            })
        
        st.session_state.provider_config.update(config_update)
        
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
            st.session_state.debug_mode = st.checkbox(
                "Show agent role debug info",
                value=st.session_state.get('debug_mode', False),
                help="Show raw agent role data structure for debugging"
            )
            st.session_state.show_llm_debug = st.checkbox(
                "Show LLM analysis debug",
                value=st.session_state.get('show_llm_debug', False),
                help="Show detailed LLM analysis information in recommendations"
            )
        
        # Test connection button
        if st.sidebar.button("🔍 Test Connection"):
            test_provider_connection()
    
def test_provider_connection():
        """Test the current provider configuration."""
        with st.sidebar:
            with st.spinner("Testing connection..."):
                try:
                    config = st.session_state.provider_config
                    test_data = {
                        "provider": config['provider'],
                        "model": config['model'],
                        "api_key": config.get('api_key'),
                        "endpoint_url": config.get('endpoint_url'),
                        "region": config.get('region')
                    }
                    
                    # Add Bedrock-specific authentication details
                    if config['provider'] == "bedrock":
                        test_data.update({
                            "aws_access_key_id": config.get('aws_access_key_id'),
                            "aws_secret_access_key": config.get('aws_secret_access_key'),
                            "aws_session_token": config.get('aws_session_token'),
                            "bedrock_api_key": config.get('bedrock_api_key')
                        })
                    
                    response = asyncio.run(api_client.test_provider_connection(test_data))
                    
                    if response and response.get('ok'):
                        st.success("✅ Connection successful!")
                    elif response:
                        st.error(f"❌ Connection failed: {response.get('message', 'Unknown error')}")
                    else:
                        st.error("❌ Connection failed: No response from API")
                
                except Exception as e:
                    st.error(f"❌ Error testing connection: {str(e)}")
                    # Debug information
                    st.write(f"Debug - Exception type: {type(e).__name__}")
                    st.write(f"Debug - API client base URL: {api_client.base_url}")
                    import traceback
                    st.code(traceback.format_exc())
        

    
    def render_input_methods(self):
        """Render the input methods section."""
        st.header("📝 Input Requirements")
        
        input_method = st.radio(
            "Choose input method:",
            ["Text Input", "File Upload", "Jira Integration", "Resume Previous Session"],
            horizontal=True
        )
        
        if input_method == "Text Input":
            self.render_text_input()
        elif input_method == "File Upload":
            self.render_file_upload()
        elif input_method == "Jira Integration":
            self.render_jira_input()
        else:
            self.render_resume_session()
    
    def render_shared_constraints(self, key_prefix: str = ""):
        """Render shared technology constraints section for all input methods."""
        # Use form reset counter to ensure fresh form inputs
        reset_counter = st.session_state.get('form_reset_counter', 0)
        unique_key_prefix = f"{key_prefix}_{reset_counter}_"
        
        # Domain and Pattern Types
        col1, col2 = st.columns(2)
        
        with col1:
            domain = st.selectbox(
                "Domain (optional):",
                ["", "finance", "hr", "marketing", "operations", "it", "customer-service"],
                key=f"{unique_key_prefix}domain",
                help="Business domain for better pattern matching"
            )
        
        with col2:
            pattern_types = st.multiselect(
                "Pattern Types (optional):",
                ["workflow", "data-processing", "integration", "notification", "approval"],
                key=f"{unique_key_prefix}pattern_types",
                help="Types of automation patterns to focus on"
            )
        
        # Technology Constraints
        st.subheader("🚫 Technology Constraints")
        
        col3, col4 = st.columns(2)
        
        with col3:
            restricted_technologies = st.text_area(
                "Restricted/Banned Technologies:",
                height=100,
                placeholder="Enter technologies that cannot be used, one per line:\nAzure\nOracle Database\nSalesforce\nWindows Server",
                help="List any technologies, platforms, or tools that are banned or unavailable in your organization",
                key=f"{unique_key_prefix}restricted_tech"
            )
        
        with col4:
            required_integrations = st.text_area(
                "Required Integrations:",
                height=100,
                placeholder="Enter required systems to integrate with:\nActive Directory\nSAP\nExisting PostgreSQL\nAWS Lambda",
                help="List any existing systems or technologies that must be integrated with",
                key=f"{unique_key_prefix}required_int"
            )
        
        # Additional constraints
        with st.expander("🔒 Additional Constraints (Optional)"):
            col5, col6 = st.columns(2)
            
            with col5:
                compliance_requirements = st.multiselect(
                    "Compliance Requirements:",
                    ["GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA", "ISO-27001", "FedRAMP"],
                    help="Select applicable compliance standards",
                    key=f"{unique_key_prefix}compliance"
                )
                
                data_sensitivity = st.selectbox(
                    "Data Sensitivity Level:",
                    ["", "Public", "Internal", "Confidential", "Restricted"],
                    help="Classification level of data being processed",
                    key=f"{unique_key_prefix}data_sensitivity"
                )
            
            with col6:
                budget_constraints = st.selectbox(
                    "Budget Constraints:",
                    ["", "Low (Open source preferred)", "Medium (Some commercial tools OK)", "High (Enterprise solutions OK)"],
                    help="Budget level for technology solutions",
                    key=f"{unique_key_prefix}budget"
                )
                
                deployment_preference = st.selectbox(
                    "Deployment Preference:",
                    ["", "Cloud-only", "On-premises only", "Hybrid", "No preference"],
                    help="Preferred deployment model",
                    key=f"{unique_key_prefix}deployment"
                )
        
        return {
            "domain": domain if domain else None,
            "pattern_types": pattern_types,
            "restricted_technologies": restricted_technologies,
            "required_integrations": required_integrations,
            "compliance_requirements": compliance_requirements,
            "data_sensitivity": data_sensitivity,
            "budget_constraints": budget_constraints,
            "deployment_preference": deployment_preference
        }
    
    def build_constraints_object(self, constraint_data: Dict) -> Dict:
        """Build constraints object from constraint data."""
        constraints = {}
        
        # Parse restricted technologies and required integrations
        if constraint_data.get("restricted_technologies"):
            banned_tools = [tech.strip() for tech in constraint_data["restricted_technologies"].split('\n') if tech.strip()]
            if banned_tools:
                constraints["banned_tools"] = banned_tools
        
        if constraint_data.get("required_integrations"):
            required_ints = [tech.strip() for tech in constraint_data["required_integrations"].split('\n') if tech.strip()]
            if required_ints:
                constraints["required_integrations"] = required_ints
        
        # Add other constraints
        if constraint_data.get("compliance_requirements"):
            constraints["compliance_requirements"] = constraint_data["compliance_requirements"]
        if constraint_data.get("data_sensitivity"):
            constraints["data_sensitivity"] = constraint_data["data_sensitivity"]
        if constraint_data.get("budget_constraints"):
            constraints["budget_constraints"] = constraint_data["budget_constraints"]
        if constraint_data.get("deployment_preference"):
            constraints["deployment_preference"] = constraint_data["deployment_preference"]
        
        return constraints if constraints else None

    def render_text_input(self):
        """Render text input interface."""
        requirements_text = st.text_area(
            "Enter your requirements:",
            height=200,
            placeholder="Describe the process or workflow you want to automate..."
        )
        
        # Render shared constraints section
        constraint_data = self.render_shared_constraints("text_")
        
        if st.button("🚀 Analyze Requirements", disabled=st.session_state.processing):
            if requirements_text.strip():
                constraints = self.build_constraints_object(constraint_data)
                
                self.submit_requirements("text", {
                    "text": requirements_text,
                    "domain": constraint_data["domain"],
                    "pattern_types": constraint_data["pattern_types"],
                    "constraints": constraints
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
            
            # Render shared constraints section
            constraint_data = self.render_shared_constraints("file_")
            
            if st.button("🚀 Analyze File", disabled=st.session_state.processing):
                try:
                    content = uploaded_file.read().decode('utf-8')
                    constraints = self.build_constraints_object(constraint_data)
                    
                    self.submit_requirements("file", {
                        "content": content,
                        "filename": uploaded_file.name,
                        "domain": constraint_data["domain"],
                        "pattern_types": constraint_data["pattern_types"],
                        "constraints": constraints
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
        
        # Move deployment type and auth method outside form for dynamic updates
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
                help="Select your Jira deployment type or let the system auto-detect",
                key="jira_deployment_type"
            )
        
        with col2:
            auth_type = st.selectbox(
                "Authentication Method👤",
                options=["api_token", "pat", "sso", "basic"],
                format_func=lambda x: {
                    "api_token": "🔑 API Token (Cloud)",
                    "pat": "🎫 Personal Access Token (Data Center)",
                    "sso": "🔐 SSO/Current Session",
                    "basic": "👤 Username/Password"
                }[x],
                help="Choose authentication method based on your Jira deployment",
                key="jira_auth_type"
            )
        
        # Now create the form with the rest of the fields
        with st.form("jira_form"):
            
            # Base URL Configuration
            jira_base_url = st.text_input(
                "Jira Base URL",
                placeholder="https://your-domain.atlassian.net or https://jira.company.com:8080",
                help="Your Jira instance URL (include custom port if needed)"
            )
            
            # Authentication Configuration (dynamic based on auth_type)
            st.write("**Authentication Details**")
            
            # Get auth_type from session state since it's outside the form
            current_auth_type = st.session_state.get("jira_auth_type", "api_token")
            
            jira_email = None
            jira_api_token = None
            jira_username = None
            jira_password = None
            jira_personal_access_token = None
            
            if current_auth_type == "api_token":
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
            
            elif current_auth_type == "pat":
                jira_personal_access_token = st.text_input(
                    "Personal Access Token",
                    type="password",
                    help="Generate from Jira Data Center: Profile > Personal Access Tokens"
                )
            
            elif current_auth_type == "basic":
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
            
            elif current_auth_type == "sso":
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
            
            # Add constraints section inside the form
            st.write("---")  # Visual separator
            st.write("**Analysis Configuration**")
            
            # Domain and Pattern Types
            col1, col2 = st.columns(2)
            
            with col1:
                jira_domain = st.selectbox(
                    "Domain (optional):",
                    ["", "finance", "hr", "marketing", "operations", "it", "customer-service"],
                    help="Business domain for better pattern matching"
                )
            
            with col2:
                jira_pattern_types = st.multiselect(
                    "Pattern Types (optional):",
                    ["workflow", "data-processing", "integration", "notification", "approval"],
                    help="Types of automation patterns to focus on"
                )
            
            # Technology Constraints
            with st.expander("🚫 Technology Constraints (Optional)"):
                # Use form reset counter for unique keys
                reset_counter = st.session_state.get('form_reset_counter', 0)
                jira_key_prefix = f"jira_{reset_counter}_"
                
                col3, col4 = st.columns(2)
                
                with col3:
                    jira_restricted_technologies = st.text_area(
                        "Restricted/Banned Technologies:",
                        height=80,
                        placeholder="Enter technologies that cannot be used, one per line:\nAzure\nOracle Database\nSalesforce\nWindows Server",
                        help="List any technologies, platforms, or tools that are banned or unavailable in your organization",
                        key=f"{jira_key_prefix}restricted_tech"
                    )
                
                with col4:
                    jira_required_integrations = st.text_area(
                        "Required Integrations:",
                        height=80,
                        placeholder="Enter required systems to integrate with:\nActive Directory\nSAP\nExisting PostgreSQL\nAWS Lambda",
                        help="List any existing systems or technologies that must be integrated with",
                        key=f"{jira_key_prefix}required_int"
                    )
                
                # Additional constraints
                col5, col6 = st.columns(2)
                
                with col5:
                    jira_compliance_requirements = st.multiselect(
                        "Compliance Requirements:",
                        ["GDPR", "HIPAA", "SOX", "PCI-DSS", "CCPA", "ISO-27001", "FedRAMP"],
                        help="Select applicable compliance standards",
                        key=f"{jira_key_prefix}compliance"
                    )
                    
                    jira_data_sensitivity = st.selectbox(
                        "Data Sensitivity Level:",
                        ["", "Public", "Internal", "Confidential", "Restricted"],
                        help="Classification level of data being processed",
                        key=f"{jira_key_prefix}data_sensitivity"
                    )
                
                with col6:
                    jira_budget_constraints = st.selectbox(
                        "Budget Constraints:",
                        ["", "Low (Open source preferred)", "Medium (Some commercial tools OK)", "High (Enterprise solutions OK)"],
                        help="Budget level for technology solutions",
                        key=f"{jira_key_prefix}budget"
                    )
                    
                    jira_deployment_preference = st.selectbox(
                        "Deployment Preference:",
                        ["", "Cloud-only", "On-premises only", "Hybrid", "No preference"],
                        help="Preferred deployment model",
                        key=f"{jira_key_prefix}deployment"
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
            # Get current auth type from session state
            current_auth_type = st.session_state.get("jira_auth_type", "api_token")
            
            # Validate required fields based on auth type
            validation_errors = []
            
            if not jira_base_url:
                validation_errors.append("Base URL is required")
            
            if current_auth_type == "api_token":
                if not jira_email:
                    validation_errors.append("Email is required for API token authentication")
                if not jira_api_token:
                    validation_errors.append("API token is required for API token authentication")
            elif current_auth_type == "pat":
                if not jira_personal_access_token:
                    validation_errors.append("Personal Access Token is required for PAT authentication")
            elif current_auth_type == "basic":
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
                            "auth_type": current_auth_type,
                            
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
                            "use_sso": current_auth_type == "sso",
                            
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
                                            st.write(f"**API Version:** {test_result.get('api_version_detected', 'Unknown')}")
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
                        else:
                            error_msg = test_result.get("message", "Unknown error") if test_result else "Connection failed"
                            st.error(f"❌ Connection failed: {error_msg}")
                            
                            # Display detailed error information if available
                            error_details = test_result.get("error_details") if test_result else None
                            if error_details:
                                with st.expander("🔍 Troubleshooting Information", expanded=True):
                                    error_type = error_details.get('error_type', 'Unknown')
                                    st.write(f"**Error Type:** {error_type}")
                                    
                                    if error_details.get('error_code'):
                                        st.write(f"**Error Code:** {error_details['error_code']}")
                                    
                                    # Show SSL-specific warnings and guidance
                                    if "ssl" in error_type.lower() or "certificate" in error_type.lower():
                                        if not verify_ssl:
                                            st.info("""
                                            ℹ️  **SSL Configuration Note**
                                            
                                            SSL verification is currently disabled. If you're still getting SSL errors, 
                                            this might indicate a deeper connection issue.
                                            """)
                                        else:
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
                                    
                                    # Show suggested configuration changes for SSL issues
                                    suggested_config = error_details.get('suggested_config_changes')
                                    if suggested_config and ("ssl" in error_type.lower() or "certificate" in error_type.lower()):
                                        st.write("**Suggested Configuration:**")
                                        if suggested_config.get('verify_ssl') is False:
                                            st.code(f"""
# For testing only - disable SSL verification
verify_ssl = False

# Note: {suggested_config.get('note', 'Use with caution')}
                                            """)
                                        if suggested_config.get('ca_cert_path'):
                                            st.code(f"""
# Add custom CA certificate
ca_cert_path = "{suggested_config.get('ca_cert_path')}"
verify_ssl = True
                                            """)
                                    
                                    doc_links = error_details.get('documentation_links', [])
                                    if doc_links:
                                        st.write("**Documentation:**")
                                        for link in doc_links:
                                            st.write(f"• {link}")
                    except Exception as e:
                        st.error(f"❌ Connection failed: {str(e)}")
        
        # Handle fetch ticket
        if fetch_ticket:
            # Get current auth type from session state
            current_auth_type = st.session_state.get("jira_auth_type", "api_token")
            
            # Validate required fields based on auth type
            validation_errors = []
            
            if not jira_base_url:
                validation_errors.append("Base URL is required")
            if not jira_ticket_key:
                validation_errors.append("Ticket key is required")
            
            if current_auth_type == "api_token":
                if not jira_email:
                    validation_errors.append("Email is required for API token authentication")
                if not jira_api_token:
                    validation_errors.append("API token is required for API token authentication")
            elif current_auth_type == "pat":
                if not jira_personal_access_token:
                    validation_errors.append("Personal Access Token is required for PAT authentication")
            elif current_auth_type == "basic":
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
                            "auth_type": current_auth_type,
                            
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
                            "use_sso": current_auth_type == "sso",
                            
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
                            
                            # Store fetched data in session state for later use
                            st.session_state.jira_fetched_data = {
                                "ticket_data": ticket_data,
                                "requirements": requirements,
                                "fetch_timestamp": time.time(),
                                "ticket_key": ticket_data.get('key', jira_ticket_key)
                            }
                            
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
        
        # Show cached data status if available
        if hasattr(st.session_state, 'jira_fetched_data') and st.session_state.jira_fetched_data:
            cached_data = st.session_state.jira_fetched_data
            fetch_time = datetime.fromtimestamp(cached_data["fetch_timestamp"])
            
            col1, col2 = st.columns([3, 1])
            with col1:
                st.info(f"✅ Cached ticket data available for **{cached_data['ticket_key']}** (fetched at {fetch_time.strftime('%H:%M:%S')})")
            with col2:
                if st.button("🗑️ Clear Cache", help="Clear cached ticket data to fetch fresh data"):
                    del st.session_state.jira_fetched_data
                    st.rerun()
        
        # Handle submit analysis
        if submit_jira:
            # Get current auth type from session state
            current_auth_type = st.session_state.get("jira_auth_type", "api_token")
            
            # Validate required fields based on auth type
            validation_errors = []
            
            if not jira_base_url:
                validation_errors.append("Base URL is required")
            if not jira_ticket_key:
                validation_errors.append("Ticket key is required")
            
            if current_auth_type == "api_token":
                if not jira_email:
                    validation_errors.append("Email is required for API token authentication")
                if not jira_api_token:
                    validation_errors.append("API token is required for API token authentication")
            elif current_auth_type == "pat":
                if not jira_personal_access_token:
                    validation_errors.append("Personal Access Token is required for PAT authentication")
            elif current_auth_type == "basic":
                if not jira_username:
                    validation_errors.append("Username is required for basic authentication")
                if not jira_password:
                    validation_errors.append("Password is required for basic authentication")
            
            if validation_errors:
                st.error("❌ Please fix the following issues:\n" + "\n".join(f"• {error}" for error in validation_errors))
            else:
                # Check if we have fetched data available
                if hasattr(st.session_state, 'jira_fetched_data') and st.session_state.jira_fetched_data:
                    with st.spinner("Starting analysis with fetched ticket data..."):
                        # Use the already fetched ticket data
                        fetched_data = st.session_state.jira_fetched_data
                        ticket_data = fetched_data["ticket_data"]
                        requirements = fetched_data["requirements"]
                        
                        # Build constraints object from Jira form data
                        jira_constraint_data = {
                            "restricted_technologies": jira_restricted_technologies,
                            "required_integrations": jira_required_integrations,
                            "compliance_requirements": jira_compliance_requirements,
                            "data_sensitivity": jira_data_sensitivity,
                            "budget_constraints": jira_budget_constraints,
                            "deployment_preference": jira_deployment_preference
                        }
                        constraints = self.build_constraints_object(jira_constraint_data)
                        
                        # Create a simplified payload using the fetched data
                        payload = {
                            "ticket_key": ticket_data.get("key", jira_ticket_key),
                            "description": requirements.get("description", ""),
                            "domain": jira_domain if jira_domain else None,
                            "pattern_types": jira_pattern_types,
                            "constraints": constraints,
                            "use_cached_data": True,  # Flag to indicate we're using cached data
                            "ticket_data": ticket_data,
                            "requirements": requirements
                        }
                        
                        self.submit_requirements("jira_cached", payload)
                else:
                    st.error("❌ No ticket data available. Please fetch the ticket first using the 'Fetch Ticket' button above.")
                    st.info("💡 Use the 'Fetch Ticket' button to retrieve ticket data, then click 'Start Analysis'.")
    
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
                
                # Store current provider info for regenerate functionality
                provider_config = st.session_state.get('provider_config', {})
                st.session_state.current_provider = provider_config.get('provider', 'Unknown')
                st.session_state.current_model = provider_config.get('model', 'Unknown')
                
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
                        "domain": payload.get("domain"),
                        "pattern_types": payload.get("pattern_types", []),
                        "constraints": payload.get("constraints", {})
                    }
                elif source == "jira" or source == "jira_cached":
                    # For Jira, the payload contains credentials and ticket_key
                    # The actual ticket data will be fetched by the backend
                    st.session_state.requirements = {
                        "description": payload.get("description", f"Jira ticket: {payload.get('ticket_key', 'Unknown')}"),
                        "jira_key": payload.get("ticket_key"),
                        "domain": payload.get("domain"),
                        "pattern_types": payload.get("pattern_types", []),
                        "constraints": payload.get("constraints", {}),
                        "source": "jira"
                    }
                
                st.success(f"✅ Requirements submitted! Session ID: {st.session_state.session_id}")
                
                # Start polling for progress
                st.rerun()
        
        except SecurityFeedbackException as e:
            st.session_state.processing = False
            # Display enhanced security feedback with proper formatting
            st.error("❌ Error submitting requirements: Security validation failed")
            st.markdown(str(e))
        except Exception as e:
            st.session_state.processing = False
            st.error(f"❌ Error submitting requirements: {str(e)}")
    
    def render_resume_session(self):
        """Render resume previous session interface."""
        st.subheader("🔄 Resume Previous Session")
        
        st.markdown("""
        If you have a session ID from a previous analysis, you can resume it here to view 
        the results or continue where you left off.
        """)
        
        with st.form("resume_session_form"):
            session_id_input = st.text_input(
                "Session ID",
                placeholder="e.g., 7249c0d9-7896-4fdf-931b-4f4aafbc44e0",
                help="Enter the session ID from your previous analysis"
            )
            
            col1, col2 = st.columns([1, 3])
            
            with col1:
                resume_button = st.form_submit_button("🔄 Resume Session", type="primary")
            
            with col2:
                if st.form_submit_button("❓ Where do I find my Session ID?", type="secondary"):
                    st.info("""
                    **Finding Your Session ID:**
                    
                    • Look at the URL when viewing analysis results
                    • Check the "Processing Progress" section during analysis
                    • Session IDs are also shown in export file names
                    • Format: 8-4-4-4-12 characters (e.g., 7249c0d9-7896-4fdf-931b-4f4aafbc44e0)
                    """)
        
        if resume_button:
            if not session_id_input.strip():
                st.error("❌ Please enter a session ID")
                return
            
            # Validate session ID format
            session_id_pattern = r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$'
            if not re.match(session_id_pattern, session_id_input.strip().lower()):
                st.error("❌ Invalid session ID format. Expected format: 8-4-4-4-12 characters (e.g., 7249c0d9-7896-4fdf-931b-4f4aafbc44e0)")
                return
            
            with st.spinner(f"Loading session {session_id_input[:8]}..."):
                try:
                    # Try to get session status to validate it exists
                    response = asyncio.run(self.make_api_request(
                        "GET",
                        f"/status/{session_id_input.strip()}"
                    ))
                    
                    if response:
                        # Session exists, load it into current state
                        st.session_state.session_id = session_id_input.strip()
                        st.session_state.current_phase = response.get('phase')
                        st.session_state.progress = response.get('progress', 0)
                        
                        # Load requirements if available
                        requirements = response.get('requirements')
                        if requirements:
                            st.session_state.requirements = requirements
                        
                        # If session is complete, load recommendations
                        if response.get('phase') == 'DONE':
                            try:
                                self.load_recommendations()
                            except Exception as e:
                                st.warning(f"⚠️ Session loaded but couldn't load recommendations: {str(e)}")
                        
                        st.success(f"✅ Successfully resumed session {session_id_input[:8]}...")
                        st.info(f"📊 Session Status: {response.get('phase', 'Unknown')} ({response.get('progress', 0)}%)")
                        
                        # Show helpful message about provider configuration
                        current_provider_config = st.session_state.get('provider_config', {})
                        if current_provider_config and current_provider_config.get('provider'):
                            st.info(f"💡 **Note:** This session will use your current provider configuration ({current_provider_config.get('provider')} - {current_provider_config.get('model', 'default model')}) for any new operations like Q&A questions or regeneration.")
                        else:
                            st.warning("⚠️ **Important:** Please configure an LLM provider in the sidebar to enable Q&A questions and other AI features for this resumed session.")
                        
                        # Rerun to show the progress tracking
                        st.rerun()
                    else:
                        st.error("❌ Session not found or invalid response")
                        
                except Exception as e:
                    error_msg = str(e)
                    if "404" in error_msg or "Session not found" in error_msg:
                        st.error("❌ Session not found. Please check the session ID and try again.")
                        st.info("""
                        **Possible reasons:**
                        • Session ID is incorrect or mistyped
                        • Session has expired (sessions are kept for a limited time)
                        • Session was created on a different system/environment
                        """)
                    elif "timeout" in error_msg.lower():
                        st.error("❌ Request timed out. Please try again.")
                    else:
                        st.error(f"❌ Error loading session: {error_msg}")
    
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
                if st.button("🔄 Start Over", key="start_new_analysis_error"):
                    st.session_state.clear()
                    st.rerun()
            elif "timeout" in error_msg.lower():
                st.error("❌ Status check timed out. The system may be under heavy load.")
                st.info("💡 Please wait a moment and the page will refresh automatically.")
            else:
                st.error(f"❌ Error getting status: {error_msg}")
                st.info("🔄 The page will continue to refresh automatically.")
    
    def handle_automation_assessment(self, assessment, requires_user_decision, proceeding_with_traditional):
        """Handle automation suitability assessment results."""
        suitability = assessment.get('suitability', 'not_suitable')
        confidence = assessment.get('confidence', 0.0)
        reasoning = assessment.get('reasoning', '')
        recommended_approach = assessment.get('recommended_approach', '')
        challenges = assessment.get('challenges', [])
        next_steps = assessment.get('next_steps', [])
        warning_message = assessment.get('warning_message')
        
        st.subheader("🔍 Automation Suitability Assessment")
        
        # Show assessment results with appropriate styling
        if suitability == 'agentic':
            st.success("✅ **Suitable for Agentic AI Automation**")
        elif suitability == 'traditional':
            st.info("🔧 **Suitable for Traditional Automation**")
        elif suitability == 'hybrid':
            st.info("🔄 **Suitable for Hybrid Automation Approach**")
        else:
            st.warning("⚠️ **May Not Be Suitable for Automation**")
        
        # Show confidence level
        confidence_color = "green" if confidence >= 0.8 else "orange" if confidence >= 0.6 else "red"
        st.markdown(f"**Confidence Level:** :{confidence_color}[{confidence:.1%}]")
        
        # Show reasoning
        with st.expander("📋 Assessment Details", expanded=True):
            st.write("**Reasoning:**")
            st.write(reasoning)
            
            st.write("**Recommended Approach:**")
            st.write(recommended_approach)
            
            if challenges:
                st.write("**Potential Challenges:**")
                for challenge in challenges:
                    st.write(f"• {challenge}")
            
            if next_steps:
                st.write("**Recommended Next Steps:**")
                for step in next_steps:
                    st.write(f"• {step}")
        
        # Show warning if present
        if warning_message:
            st.warning(f"⚠️ **Warning:** {warning_message}")
        
        # Handle user decision requirement
        if requires_user_decision:
            st.markdown("---")
            st.subheader("🤔 Your Decision")
            
            if suitability == 'not_suitable':
                st.error("**This requirement appears to be unsuitable for automation.** However, you can still proceed if you'd like to explore potential solutions.")
            else:
                st.warning("**The automation assessment has some concerns.** Please review the details above before proceeding.")
            
            col1, col2 = st.columns(2)
            
            with col1:
                if st.button("🚀 Proceed Anyway", type="primary", help="Continue with analysis despite concerns"):
                    self.proceed_with_analysis_anyway()
            
            with col2:
                if st.button("🔄 Revise Requirement", help="Go back and modify your requirement"):
                    self.restart_analysis()
        
        elif proceeding_with_traditional:
            st.success("✅ **Proceeding with traditional automation analysis...**")
            st.info("The system will now analyze your requirement using traditional automation patterns instead of agentic AI.")
            # The session phase has already been updated to MATCHING, so the UI will refresh and show progress
        
        else:
            # Assessment complete, proceed automatically
            st.success("✅ **Assessment complete - proceeding to pattern matching...**")
    
    def proceed_with_analysis_anyway(self):
        """Proceed with analysis despite automation suitability concerns."""
        try:
            # Force advance the session to MATCHING phase
            asyncio.run(self.make_api_request(
                "POST",
                f"/sessions/{st.session_state.session_id}/force_advance",
                {"target_phase": "MATCHING", "user_override": True}
            ))
            
            st.success("✅ Proceeding with analysis...")
            st.rerun()
            
        except Exception as e:
            st.error(f"❌ Error proceeding with analysis: {str(e)}")
    
    def restart_analysis(self):
        """Restart the analysis process."""
        # Clear session state and return to input
        st.session_state.session_id = None
        st.session_state.current_phase = None
        st.session_state.progress = 0
        st.session_state.recommendations = None
        st.session_state.qa_questions = []
        st.session_state.requirements = None
        
        # Clear any cached constraint form values by incrementing a counter
        if 'form_reset_counter' not in st.session_state:
            st.session_state.form_reset_counter = 0
        st.session_state.form_reset_counter += 1
        
        st.success("✅ Analysis restarted - please provide a new requirement")
        st.rerun()

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
                with st.spinner("🤖 AI is analyzing your requirement for automation suitability..."):
                    # Include current provider config to ensure we use the latest API keys
                    current_provider_config = st.session_state.get('provider_config', {})
                    request_data = {}
                    if current_provider_config and current_provider_config.get('provider'):
                        request_data['provider_config'] = current_provider_config
                    
                    response = asyncio.run(self.make_api_request(
                        "POST",
                        f"/qa/{st.session_state.session_id}/questions",
                        request_data
                    ))
                    
                    questions = response.get('questions', [])
                    automation_assessment = response.get('automation_assessment')
                    requires_user_decision = response.get('requires_user_decision', False)
                    proceeding_with_traditional = response.get('proceeding_with_traditional', False)
                    
                    if questions:
                        # Normal Q&A flow - we have agentic questions to ask
                        st.session_state.qa_questions = questions
                        # Cache the questions to prevent regeneration
                        st.session_state[questions_cache_key] = questions
                        st.success(f"✅ Generated {len(questions)} questions for agentic AI assessment")
                    elif automation_assessment:
                        # Handle automation assessment results
                        self.handle_automation_assessment(automation_assessment, requires_user_decision, proceeding_with_traditional)
                        return
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
            # Use a form to prevent API calls on every keystroke
            with st.form(key="qa_form", clear_on_submit=False):
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
                
                # Submit button inside the form
                col1, col2, col3 = st.columns([1, 2, 1])
                with col2:
                    submit_button = st.form_submit_button("🚀 Submit Answers", type="primary", use_container_width=True)
                
                # Handle form submission
                if submit_button:
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
    
    def render_regenerate_section(self):
        """Render the regenerate analysis section."""
        # Simple regenerate button that uses current provider configuration
        col1, col2, col3 = st.columns([1, 1, 2])
        
        # Check if we have a valid provider configuration
        provider_config = st.session_state.get('provider_config', {})
        has_valid_provider = provider_config and provider_config.get('provider') and provider_config.get('model')
        
        with col1:
            button_disabled = not has_valid_provider
            button_help = "Re-run analysis with current LLM provider settings" if has_valid_provider else "Configure an LLM provider in the sidebar first"
            
            if st.button(
                "🔄 Regenerate Analysis", 
                type="primary", 
                help=button_help,
                disabled=button_disabled
            ):
                self.regenerate_analysis()
        
        with col3:
            # Show current provider info
            if has_valid_provider:
                current_provider = provider_config.get('provider', 'Unknown')
                current_model = provider_config.get('model', 'Unknown')
                st.caption(f"Using: {current_provider} - {current_model}")
            else:
                st.caption("⚠️ No LLM provider configured")
        
        if has_valid_provider:
            st.caption("💡 Change the LLM provider in the sidebar to test different models, then regenerate to compare results.")
        else:
            st.caption("💡 Configure an LLM provider in the sidebar to enable regeneration.")
    
    def regenerate_analysis(self):
        """Regenerate analysis using current provider configuration."""
        try:
            # Validate we have the necessary data
            requirements = st.session_state.get('requirements', {})
            if not requirements:
                st.error("❌ No requirements found. Please start a new analysis first.")
                return
            
            # Get current provider configuration
            provider_config = st.session_state.get('provider_config', {})
            if not provider_config:
                st.error("❌ No provider configuration found. Please configure an LLM provider in the sidebar.")
                return
            
            provider_name = provider_config.get('provider', 'Unknown')
            model_name = provider_config.get('model', 'Unknown')
            
            # Get Q&A answers from session state (may be empty for new sessions)
            qa_answers = {}
            
            # Try to extract Q&A answers from various sources
            if hasattr(st.session_state, 'qa_answers') and st.session_state.qa_answers:
                qa_answers = st.session_state.qa_answers
            elif st.session_state.get('requirements', {}).get('workflow_variability'):
                # Extract from requirements if they were merged there
                req = st.session_state.requirements
                for key in ['workflow_variability', 'data_sensitivity', 'human_oversight']:
                    if req.get(key):
                        qa_answers[key] = req[key]
            
            # Debug: Show what we're working with
            st.write("**Debug - Starting regeneration:**")
            st.write(f"- Provider config: {provider_config}")
            st.write(f"- Requirements: {len(requirements)} fields")
            st.write(f"- Q&A answers: {len(qa_answers)} answers")
            
            # Show progress with more detailed feedback
            progress_placeholder = st.empty()
            with progress_placeholder.container():
                st.info(f"🔄 **Regenerating analysis with {provider_name} - {model_name}...**")
                st.caption("This creates a new session with the same requirements but fresh analysis")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                try:
                    # Create a new session with the same requirements and Q&A answers
                    regenerate_request = {
                        "requirements": requirements,
                        "qa_answers": qa_answers,
                        "provider_override": {
                            "provider": provider_name,
                            "model": model_name
                        },
                        "regenerate": True
                    }
                    
                    status_text.text("Creating new session...")
                    progress_bar.progress(20)
                    
                    # Debug: Show what we're sending
                    if st.session_state.get('show_debug', False):
                        st.write(f"Debug: Calling /regenerate with provider {provider_name}")
                    
                    # Use the existing ingest endpoint instead of regenerate for better reliability
                    ingest_request = {
                        "source": "text",
                        "payload": {
                            "text": requirements.get("description", ""),
                            "domain": requirements.get("domain", ""),
                            "pattern_types": requirements.get("pattern_types", []),
                            "constraints": requirements.get("constraints", {})
                        },
                        "provider_config": {
                            "provider": provider_name,
                            "model": model_name
                        }
                    }
                    
                    # Call the ingest endpoint which we know works reliably
                    response = asyncio.run(self.make_api_request_with_timeout(
                        "POST",
                        "/ingest",
                        ingest_request,
                        timeout=30.0
                    ))
                    
                    status_text.text("Session created successfully!")
                    progress_bar.progress(100)
                    
                except Exception as e:
                    status_text.text("Error occurred during regeneration")
                    progress_bar.progress(100)
                    # Add more specific error info
                    if st.session_state.get('show_debug', False):
                        st.write(f"Debug: Error type: {type(e).__name__}")
                        st.write(f"Debug: Error message: {str(e)}")
                    raise e
            
            # Clear progress indicator
            progress_placeholder.empty()
            
            # Update session with new results (ingest response format)
            new_session_id = response.get('session_id')
            message = f"Analysis regenerated with {provider_name} - {model_name}"
            
            if new_session_id:
                # Store old session ID for reference
                old_session_id = st.session_state.get('session_id')
                
                # Update session state
                st.session_state.session_id = new_session_id
                st.session_state.recommendations = None  # Clear to force reload
                st.session_state.current_provider = provider_name
                st.session_state.current_model = model_name
                
                st.success(f"✅ Analysis regenerated with {provider_name} - {model_name}")
                
                # Show comparison info
                if old_session_id:
                    st.info(f"""
                    📊 **New Session Created:** `{new_session_id}`
                    
                    Previous session `{old_session_id}` is still available via "Resume Previous Session".
                    """)
                
                # Force reload of recommendations
                st.rerun()
            else:
                st.error("❌ Failed to regenerate analysis - no session ID returned")
                    
        except Exception as e:
            error_msg = str(e)
            
            # Show detailed error information for debugging
            st.error(f"❌ **Error regenerating analysis**")
            st.code(f"Error type: {type(e).__name__}")
            st.code(f"Error message: {error_msg}")
            
            # Show the actual error details instead of assuming it's a timeout
            if "timeout" in error_msg.lower() or "ReadTimeout" in error_msg:
                st.info("This appears to be a timeout issue.")
            elif "404" in error_msg:
                st.info("The API endpoint was not found.")
            elif "provider" in error_msg.lower() and "config" in error_msg.lower():
                st.info("There's an issue with the provider configuration.")
            elif "API error" in error_msg:
                st.info("The API returned an error response.")
            else:
                st.info("An unexpected error occurred.")
            
            # Show debugging info
            st.write("**Debug Info:**")
            st.write(f"- Provider: {provider_name}")
            st.write(f"- Model: {model_name}")
            st.write(f"- Requirements keys: {list(requirements.keys()) if requirements else 'None'}")
            st.write(f"- Q&A answers keys: {list(qa_answers.keys()) if qa_answers else 'None'}")
    
    def load_recommendations(self):
        """Load and display final recommendations."""
        if st.session_state.recommendations is None:
            try:
                # Show progress indicator for recommendation generation
                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    st.info("🔄 **Generating AI Recommendations...**")
                    st.caption("This may take up to 2 minutes for complex requirements")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    # Simulate progress during the long-running operation
                    import threading
                    import time
                    
                    # Set initial progress state
                    status_text.text("Generating recommendations...")
                    progress_bar.progress(10)
                    
                    try:
                        start_time = time.time()
                        response = asyncio.run(self.make_api_request_with_timeout(
                            "POST",
                            "/recommend",
                            {"session_id": st.session_state.session_id, "top_k": 3},
                            timeout=120.0  # 2 minutes for recommendation generation
                        ))
                        processing_time = time.time() - start_time
                        
                        # Record monitoring data for recommendation generation
                        self._record_recommendation_monitoring_data(
                            session_id=st.session_state.session_id,
                            processing_time=processing_time,
                            response=response
                        )
                        
                        # Complete the progress
                        status_text.text("Complete! ✅")
                        progress_bar.progress(100)
                        
                    except Exception as e:
                        # Update progress on error
                        status_text.text("Error occurred during generation")
                        progress_bar.progress(100)
                        raise e
                
                # Clear progress indicator
                progress_placeholder.empty()
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
        
        # Add regenerate functionality (only show if we have requirements and recommendations)
        if st.session_state.get('requirements') and st.session_state.get('recommendations'):
            self.render_regenerate_section()
        
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
            "Not Automatable": {"color": "🔴", "label": "Not Automatable", "desc": "This requirement is not suitable for automation at this time."},
            "Fully Automatable": {"color": "🟢", "label": "Fully Automatable", "desc": "This requirement can be completely automated with high confidence."}
        }
        
        feas_info = feasibility_info.get(feasibility, {"color": "⚪", "label": feasibility, "desc": "Assessment pending."})
        
        st.subheader(f"{feas_info['color']} Feasibility: {feas_info['label']}")
        st.write(feas_info['desc'])
        
        # Enhanced LLM Analysis Display
        session_requirements = st.session_state.get('requirements', {})
        if session_requirements:
            # Key Insights
            key_insights = session_requirements.get('llm_analysis_key_insights', [])
            if key_insights:
                st.markdown("**🔍 Key Insights:**")
                for insight in key_insights:
                    st.markdown(f"• {insight}")
            
            # Automation Challenges
            automation_challenges = session_requirements.get('llm_analysis_automation_challenges', [])
            if automation_challenges:
                st.markdown("**⚠️ Automation Challenges:**")
                for challenge in automation_challenges:
                    st.markdown(f"• {challenge}")
            
            # Recommended Approach
            recommended_approach = session_requirements.get('llm_analysis_recommended_approach', '')
            if recommended_approach:
                st.markdown("**🎯 Recommended Approach:**")
                st.markdown(recommended_approach)
            
            # Next Steps
            next_steps = session_requirements.get('llm_analysis_next_steps', [])
            if next_steps:
                st.markdown("**📋 Next Steps:**")
                for step in next_steps:
                    st.markdown(f"• {step}")
            
            # Confidence Level
            confidence_level = session_requirements.get('llm_analysis_confidence_level')
            if confidence_level:
                confidence_pct = int(float(confidence_level) * 100) if isinstance(confidence_level, (int, float)) else confidence_level
                st.markdown(f"**📊 Confidence Level:** {confidence_pct}%")
        
        st.markdown("---")
        
        # Solution Overview - Both Traditional and Agentic
        if rec.get('recommendations') and len(rec['recommendations']) > 0:
            # Check necessity assessment first
            necessity_assessment = None
            solution_type = None
            
            # Look for necessity assessment in recommendations
            for recommendation in rec['recommendations']:
                if hasattr(recommendation, 'necessity_assessment') and recommendation.necessity_assessment:
                    necessity_assessment = recommendation.necessity_assessment
                    solution_type = necessity_assessment.recommended_solution_type.value
                    break
            
            # Fallback to keyword-based detection if no necessity assessment
            if not necessity_assessment:
                reasoning = rec.get("reasoning", "").lower()
                # Use context-aware agentic detection
                is_agentic = self._is_agentic_by_context(reasoning)
            else:
                is_agentic = solution_type in ["agentic_ai", "hybrid"]
            
            # Also check recommendations for agent_roles
            agent_roles_found = []
            seen_agents = set()  # Track unique agents to prevent duplicates
            
            for recommendation in rec['recommendations']:
                agent_roles_data = recommendation.get("agent_roles", [])
                if agent_roles_data:
                    # Deduplicate agents based on name and responsibility
                    for agent in agent_roles_data:
                        agent_name = agent.get('name', 'Unknown Agent')
                        agent_responsibility = agent.get('responsibility', '')
                        
                        # Create a unique identifier for the agent
                        agent_id = f"{agent_name}|{agent_responsibility[:50]}"
                        
                        if agent_id not in seen_agents:
                            seen_agents.add(agent_id)
                            agent_roles_found.append(agent)
                        else:
                            # Log duplicate agent detection for debugging
                            if st.session_state.get('debug_mode', False):
                                st.warning(f"🔍 Debug: Duplicate agent detected and filtered: {agent_name}")
            
            # Only set is_agentic = True if we actually found agents (not just empty agent_roles)
            if agent_roles_found:
                is_agentic = True
            
            # Validate agent data completeness
            if agent_roles_found:
                validated_agents = []
                for agent in agent_roles_found:
                    # Ensure required fields are present
                    if not agent.get('name'):
                        agent['name'] = 'Unnamed Agent'
                    if not agent.get('responsibility'):
                        agent['responsibility'] = f"Autonomous agent responsible for {agent.get('name', 'task')} operations"
                    if not agent.get('capabilities'):
                        agent['capabilities'] = ['task_execution', 'decision_making', 'exception_handling']
                    if not isinstance(agent.get('autonomy_level'), (int, float)):
                        agent['autonomy_level'] = 0.8
                    
                    validated_agents.append(agent)
                
                agent_roles_found = validated_agents
                
                # Log agent team composition for debugging
                if st.session_state.get('debug_mode', False):
                    st.info(f"🔍 Debug: Found {len(agent_roles_found)} unique agents after deduplication and validation")
            
            # Display necessity assessment if available
            if necessity_assessment:
                st.subheader("🔍 Solution Type Assessment")
                
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Agentic Necessity", 
                        f"{necessity_assessment.agentic_necessity_score:.0%}",
                        help="How much this requirement needs autonomous agent capabilities"
                    )
                
                with col2:
                    st.metric(
                        "Traditional Suitability", 
                        f"{necessity_assessment.traditional_suitability_score:.0%}",
                        help="How well this fits traditional automation approaches"
                    )
                
                with col3:
                    st.metric(
                        "Assessment Confidence", 
                        f"{necessity_assessment.confidence_level:.0%}",
                        help="Confidence in the solution type recommendation"
                    )
                
                # Show recommendation reasoning
                if necessity_assessment.recommendation_reasoning:
                    st.info(f"**Assessment:** {necessity_assessment.recommendation_reasoning}")
                
                # Show detailed justifications in expandable sections
                with st.expander("📋 Detailed Assessment Factors"):
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.write("**Agentic AI Factors:**")
                        for justification in necessity_assessment.agentic_justification:
                            st.write(f"• {justification}")
                    
                    with col2:
                        st.write("**Traditional Automation Factors:**")
                        for justification in necessity_assessment.traditional_justification:
                            st.write(f"• {justification}")
                
                st.markdown("---")
            
            # Display solution type and overview
            if solution_type == "traditional_automation":
                st.subheader("⚙️ Traditional Automation Solution")
                st.success("✅ This requirement is best suited for traditional automation approaches.")
                
                st.markdown("""
                **Traditional Automation Approach:** Your solution will use established workflow automation, 
                business process management, and integration technologies. This approach is more cost-effective, 
                faster to implement, and easier to maintain for predictable, rule-based processes.
                """)
                
            elif solution_type == "hybrid":
                st.subheader("🔄 Hybrid Solution")
                st.info("🔀 This requirement benefits from a hybrid approach combining traditional automation with selective autonomous capabilities.")
                
                st.markdown("""
                **Hybrid Approach:** Your solution will combine traditional automation for predictable workflows 
                with autonomous AI agents for complex decision-making and exception handling. This provides 
                the reliability of traditional automation with the adaptability of agentic AI where needed.
                """)
                
            elif is_agentic:
                st.subheader("🤖 Agentic AI Solution")
                st.success("🎉 This requirement is suitable for autonomous AI agent implementation!")
                
                # Agentic solution explanation
                st.markdown("""
                **Agentic AI Approach:** Your solution will use autonomous AI agents that can make decisions, 
                reason through problems, and handle exceptions without constant human intervention. This provides 
                higher autonomy and adaptability compared to traditional automation.
                """)
                
                # Agent Roles & Responsibilities - Enhanced Interactive Display
                if agent_roles_found:
                    with st.expander("🤖 Agent Team & Interaction Flow", expanded=True):
                        st.markdown("""
                        **Your Multi-Agent System:** These specialized AI agents work together autonomously to handle your requirements.
                        """)
                        
                        # Debug info (can be removed later)
                        if st.session_state.get('debug_mode', False):
                            with st.expander("🔍 Debug: Agent Role Data", expanded=False):
                                st.json(agent_roles_found)
                        
                        # Create agent interaction flow diagram first
                        if len(agent_roles_found) > 1:
                            st.markdown("### 🔄 Agent Interaction Flow")
                            self._render_agent_interaction_flow(agent_roles_found)
                            st.markdown("---")
                        
                        # Display agents in an organized, visual way
                        st.markdown("### 👥 Meet Your Agent Team")
                        
                        # Organize agents by type/hierarchy
                        coordinator_agents = []
                        specialist_agents = []
                        support_agents = []
                        
                        for role in agent_roles_found:
                            role_name = self._extract_agent_name(role)
                            role_lower = role_name.lower()
                            
                            if any(keyword in role_lower for keyword in ['coordinator', 'manager', 'orchestrator', 'supervisor']):
                                coordinator_agents.append(role)
                            elif any(keyword in role_lower for keyword in ['specialist', 'expert', 'analyst', 'analytics', 'negotiator']):
                                specialist_agents.append(role)
                            else:
                                support_agents.append(role)
                        
                        # Team composition summary
                        total_agents = len(agent_roles_found)
                        coord_count = len(coordinator_agents)
                        spec_count = len(specialist_agents) 
                        supp_count = len(support_agents)
                        
                        st.markdown(f"""
                        **🏢 Team Composition:** {total_agents} agents total
                        • {coord_count} Coordinator{'s' if coord_count != 1 else ''} • {spec_count} Specialist{'s' if spec_count != 1 else ''} • {supp_count} Support Agent{'s' if supp_count != 1 else ''}
                        """)
                        st.markdown("---")
                        
                        # Display agents by hierarchy
                        if coordinator_agents:
                            st.markdown("#### 🎯 **Coordination Layer**")
                            st.markdown("*These agents orchestrate the overall workflow and make high-level decisions*")
                            for role in coordinator_agents:
                                self._render_agent_card(role, "coordinator")
                            st.markdown("")
                        
                        if specialist_agents:
                            st.markdown("#### 🔬 **Specialist Layer**") 
                            st.markdown("*These agents provide domain expertise and handle specialized tasks*")
                            cols = st.columns(min(len(specialist_agents), 2))
                            for i, role in enumerate(specialist_agents):
                                with cols[i % len(cols)]:
                                    self._render_agent_card(role, "specialist")
                            st.markdown("")
                        
                        if support_agents:
                            st.markdown("#### 🛠️ **Support Layer**")
                            st.markdown("*These agents handle supporting functions and monitoring*")
                            for role in support_agents:
                                self._render_agent_card(role, "support")
                        
                        # Show collaboration patterns
                        if len(agent_roles_found) > 1:
                            st.markdown("---")
                            st.markdown("### 🤝 Collaboration & Workflow")
                            
                            # Interactive workflow selector
                            workflow_view = st.radio(
                                "Choose workflow view:",
                                ["Communication Patterns", "Decision Flow", "Error Handling"],
                                horizontal=True
                            )
                            
                            if workflow_view == "Communication Patterns":
                                col1, col2 = st.columns(2)
                                with col1:
                                    st.markdown("""
                                    **🔄 Inter-Agent Communication:**
                                    • **Event-driven messaging** between agents
                                    • **Shared context** and state management  
                                    • **Real-time status updates** and progress tracking
                                    • **Conflict resolution** protocols
                                    """)
                                
                                with col2:
                                    st.markdown("""
                                    **📡 Message Types:**
                                    • **Task requests** and assignments
                                    • **Status updates** and progress reports
                                    • **Data sharing** and context updates
                                    • **Alert notifications** and escalations
                                    """)
                            
                            elif workflow_view == "Decision Flow":
                                st.markdown("""
                                **🧠 Decision-Making Process:**
                                
                                1. **Input Analysis** → Each agent evaluates incoming requests within their domain
                                2. **Autonomous Processing** → Agents make independent decisions for routine tasks
                                3. **Collaboration** → Complex decisions trigger inter-agent consultation
                                4. **Consensus Building** → Agents coordinate to reach optimal solutions
                                5. **Execution** → Coordinated action with real-time monitoring
                                """)
                            
                            else:  # Error Handling
                                st.markdown("""
                                **🛡️ Error Handling & Recovery:**
                                
                                **Agent-Level Recovery:**
                                • Self-diagnosis and automatic retry mechanisms
                                • Graceful degradation when capabilities are limited
                                • Alternative approach selection
                                
                                **System-Level Resilience:**
                                • Task redistribution when agents are unavailable
                                • Backup agent activation for critical functions
                                • Human escalation for unresolvable issues
                                """)
                
                # Multi-Agent Architecture - Enhanced Visual Display
                with st.expander("🏗️ System Architecture & Design Patterns", expanded=False):
                    st.markdown("### 🎯 Architecture Overview")
                    
                    # Architecture type indicator
                    if len(agent_roles_found) > 1:
                        arch_type = "Multi-Agent Collaborative System"
                        complexity = "High" if len(agent_roles_found) > 3 else "Medium"
                    else:
                        arch_type = "Single Agent Autonomous System"
                        complexity = "Low"
                    
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.metric("Architecture Type", arch_type)
                    with col2:
                        st.metric("Agent Count", len(agent_roles_found))
                    with col3:
                        st.metric("Complexity", complexity)
                    
                    st.markdown("---")
                    
                    # Visual architecture representation with Mermaid
                    if len(agent_roles_found) > 1:
                        st.markdown("**🔗 Agent Interaction Flow:**")
                        st.info("💡 **Interactive Diagram:** This shows how your agents communicate and coordinate. Each colored box represents a different agent with specialized capabilities.")
                        
                        # Create interactive Mermaid diagram
                        architecture_mermaid = self._create_agent_architecture_mermaid(agent_roles_found)
                        
                        # Debug mode: show raw Mermaid code
                        if st.session_state.get('debug_mode', False):
                            with st.expander("🔍 Debug: Mermaid Code", expanded=False):
                                st.code(architecture_mermaid, language="mermaid")
                                st.markdown("**Copy this code to [mermaid.live](https://mermaid.live) to test**")
                        
                        # Try to render the diagram
                        try:
                            # Add debug information
                            if st.session_state.get('debug_mode', False):
                                st.write(f"**Debug Info:** Generated {len(architecture_mermaid)} characters of Mermaid code")
                                st.write(f"**First line:** {architecture_mermaid.split(chr(10))[0] if architecture_mermaid else 'Empty'}")
                            
                            self.render_mermaid(architecture_mermaid, "Agent Architecture Diagram")
                        except Exception as e:
                            st.error(f"Error rendering Mermaid diagram: {e}")
                            st.info("The diagram code above should work in mermaid.live - there may be a rendering issue in our tool.")
                            
                            # Show additional debug info
                            if st.session_state.get('debug_mode', False):
                                st.write("**Debug - Full error details:**")
                                import traceback
                                st.code(traceback.format_exc())
                        
                        # Add diagram legend
                        with st.expander("📖 Diagram Legend", expanded=False):
                            st.markdown("""
                            **🎨 Color Coding:**
                            - 🔴 **Red**: User interactions and requests
                            - 🟠 **Orange/Red**: Coordinator agents (orchestrate workflow)
                            - 🔵 **Blue**: Specialist agents (domain expertise)
                            - 🟢 **Green**: Results and responses
                            - 🟡 **Yellow**: Supporting agents and processes
                            
                            **➡️ Arrow Types:**
                            - **Solid arrows**: Direct task delegation or data flow
                            - **Double arrows (↔)**: Bidirectional communication and collaboration
                            - **Dashed lines**: Monitoring or feedback loops
                            """)
                        
                        st.markdown("---")
                    elif len(agent_roles_found) == 1:
                        st.markdown("**🤖 Single Agent Workflow:**")
                        st.info("💡 **Autonomous Loop:** This shows how your single agent processes requests through continuous learning and adaptation.")
                        
                        single_agent_mermaid = self._create_single_agent_mermaid(agent_roles_found[0])
                        self.render_mermaid(single_agent_mermaid, "Single Agent Workflow")
                        st.markdown("---")
                    
                    # Architecture principles in columns
                    col1, col2 = st.columns(2)
                    
                    with col1:
                        st.markdown("""
                        #### 🔧 **Core Principles**
                        
                        **🎯 Specialization**  
                        Each agent has a focused domain of expertise
                        
                        **🤝 Coordination**  
                        Agents communicate and collaborate seamlessly
                        
                        **🧠 Autonomy**  
                        Independent decision-making within defined scope
                        """)
                    
                    with col2:
                        st.markdown("""
                        #### ⚡ **System Benefits**
                        
                        **🛡️ Resilience**  
                        System continues if individual agents have issues
                        
                        **📈 Scalability**  
                        New agents can be added as needs grow
                        
                        **🔄 Adaptability**  
                        Agents learn and improve over time
                        """)
                    
                    st.markdown("---")
                    
                    # Technical implementation details
                    with st.expander("🔧 Technical Implementation Details"):
                        st.markdown("""
                        **Communication Protocol:**
                        - Event-driven messaging system
                        - Asynchronous task processing
                        - Shared state management with conflict resolution
                        
                        **Decision Framework:**
                        - Hierarchical decision trees
                        - Consensus mechanisms for complex decisions
                        - Escalation paths for edge cases
                        
                        **Monitoring & Control:**
                        - Real-time performance metrics
                        - Automated health checks
                        - Human oversight interfaces
                        """)
            else:
                st.subheader("⚙️ Traditional Automation Solution")
                st.info("This requirement is best suited for traditional automation approaches.")
            
            # Get the best recommendation for solution overview
            best_rec = rec['recommendations'][0]
            
            # Generate solution explanation
            solution_explanation = self._generate_solution_explanation(best_rec, rec)
            
            with st.expander("📋 Detailed Solution Analysis", expanded=True):
                st.write(solution_explanation)
            

        
        # Tech stack with explanations
        if rec.get('tech_stack'):
            # Check again for agentic solution to show appropriate tech stack
            reasoning = rec.get("reasoning", "").lower()
            is_agentic = self._is_agentic_by_context(reasoning)
            
            if is_agentic:
                st.subheader("🤖 Agentic AI Tech Stack")
                st.markdown("**Specialized technologies for autonomous AI agent development:**")
                st.info("💡 **Agentic frameworks automatically added:** LangChain, CrewAI, LangGraph, and OpenAI Assistants API have been included to support autonomous agent functionality.")
            else:
                st.subheader("🛠️ Recommended Tech Stack")
            
            # Generate and show LLM-enhanced tech stack with explanations
            # Show progress indicator while generating tech stack
            progress_placeholder = st.empty()
            with progress_placeholder.container():
                st.info("🔄 **Generating Enhanced Tech Stack Recommendations...**")
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Update progress during generation
                status_text.text("Analyzing requirements and constraints...")
                progress_bar.progress(25)
                
            enhanced_tech_stack, architecture_explanation = asyncio.run(
                self._generate_llm_tech_stack_and_explanation_with_progress(
                    rec['tech_stack'], progress_bar, status_text
                )
            )
            
            # Clear progress indicator once complete
            progress_placeholder.empty()
            
            # If this is an agentic solution, ensure agentic frameworks are included
            if is_agentic:
                enhanced_tech_stack = self._ensure_agentic_frameworks(enhanced_tech_stack)
            
            # Store the enhanced data back to session state for export
            self._update_recommendations_with_enhanced_data(enhanced_tech_stack, architecture_explanation)
            
            self._render_tech_stack_explanation(enhanced_tech_stack)
            
            # Show architecture explanation
            if is_agentic:
                st.subheader("🏗️ Agentic Architecture Flow")
                st.markdown("**How your AI agents will work together:**")
            else:
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
        from app.utils.imports import optional_service
        tech_stack_service = optional_service('tech_stack_generator', context='tech stack categorization')
        
        if tech_stack_service:
            categorized_tech = tech_stack_service.categorize_tech_stack_with_descriptions(tech_stack)
            
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
                                tech_description = tech_stack_service.get_technology_description(tech_name) if tech_stack_service else f"Technology component: {tech_name}"
                            
                            st.info(f"**{tech_name}**\n\n{tech_description}")
            
        else:
            # Fallback to simple categorization if service not available
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
    
    async def _generate_llm_tech_stack_and_explanation_with_progress(
        self, 
        original_tech_stack: List[str], 
        progress_bar=None, 
        status_text=None
    ) -> tuple[List[str], str]:
        """Generate LLM-driven tech stack and explanation with progress updates."""
        import time
        start_time = time.time()
        
        # Check if we already have cached results for this session
        session_id = st.session_state.get('session_id', 'unknown')
        cache_key = f"llm_tech_stack_{session_id}"
        
        if cache_key in st.session_state:
            from app.utils.logger import app_logger
            app_logger.info("Using cached LLM tech stack and explanation")
            if status_text:
                status_text.text("Loading cached results...")
            if progress_bar:
                progress_bar.progress(100)
            return st.session_state[cache_key]
        
        try:
            # Import here to avoid circular imports
            from app.services.architecture_explainer import ArchitectureExplainer
            from app.api import create_llm_provider
            
            if status_text:
                status_text.text("Preparing LLM provider...")
            if progress_bar:
                progress_bar.progress(40)
            
            # Get session requirements for context
            requirements = st.session_state.get('requirements', {})
            session_id = st.session_state.get('session_id', 'unknown')
            
            # Create LLM provider if available
            llm_provider = None
            provider_config_dict = st.session_state.get('provider_config')
            if provider_config_dict:
                # Check if we have valid authentication for any provider
                provider = provider_config_dict.get('provider', '')
                has_auth = False
                
                if provider == 'bedrock':
                    # For Bedrock, check for either API key or AWS credentials
                    has_bedrock_api_key = bool(provider_config_dict.get('bedrock_api_key'))
                    has_aws_creds = bool(provider_config_dict.get('aws_access_key_id') and provider_config_dict.get('aws_secret_access_key'))
                    has_session_creds = bool(provider_config_dict.get('aws_session_token'))
                    has_auth = has_bedrock_api_key or has_aws_creds or has_session_creds
                else:
                    # For other providers, check for API key
                    has_auth = bool(provider_config_dict.get('api_key'))
                
                if has_auth:
                    try:
                        from app.api import ProviderConfig
                        
                        # Convert dict to ProviderConfig model
                        provider_config = ProviderConfig(**provider_config_dict)
                        llm_provider = create_llm_provider(provider_config, session_id)
                    except Exception as e:
                        st.warning(f"Could not create LLM provider for tech stack generation: {e}")
            
            if status_text:
                status_text.text("Generating enhanced tech stack recommendations...")
            if progress_bar:
                progress_bar.progress(60)
            
            # Create architecture explainer
            explainer = ArchitectureExplainer(llm_provider)
            
            if status_text:
                status_text.text("Analyzing architecture and generating explanations...")
            if progress_bar:
                progress_bar.progress(80)
            
            # Generate both tech stack and explanation
            enhanced_tech_stack, explanation = await explainer.explain_architecture(original_tech_stack, requirements, session_id)
            
            if status_text:
                status_text.text("Finalizing recommendations...")
            if progress_bar:
                progress_bar.progress(95)
            
            # Cache the results
            result = (enhanced_tech_stack, explanation)
            st.session_state[cache_key] = result
            
            # Record monitoring data
            processing_time = time.time() - start_time
            self._record_tech_stack_monitoring_data(
                session_id=session_id,
                original_tech_stack=original_tech_stack,
                enhanced_tech_stack=enhanced_tech_stack,
                processing_time=processing_time,
                requirements=requirements
            )
            
            if status_text:
                status_text.text("Complete! ✅")
            if progress_bar:
                progress_bar.progress(100)
            
            return result
            
        except Exception as e:
            if status_text:
                status_text.text(f"Error occurred: {str(e)}")
            if progress_bar:
                progress_bar.progress(100)
            st.error(f"Failed to generate tech stack and explanation: {e}")
            return original_tech_stack, self._generate_fallback_architecture_explanation(original_tech_stack)

    def _record_tech_stack_monitoring_data(
        self,
        session_id: str,
        original_tech_stack: List[str],
        enhanced_tech_stack: List[str],
        processing_time: float,
        requirements: Dict[str, Any]
    ) -> None:
        """Record tech stack generation data for monitoring."""
        try:
            # Try to get monitoring service
            if 'monitoring_service' not in st.session_state:
                from app.monitoring.integration_service import MonitoringIntegrationService
                st.session_state.monitoring_service = MonitoringIntegrationService()
            
            monitoring_service = st.session_state.monitoring_service
            
            # Extract explicit technologies from requirements
            explicit_technologies = []
            if requirements:
                req_text = requirements.get('description', '') + ' ' + requirements.get('constraints', '')
                # Simple extraction - look for technology names in requirements
                tech_keywords = ['python', 'javascript', 'react', 'node', 'aws', 'docker', 'kubernetes', 'postgresql', 'mongodb', 'redis']
                explicit_technologies = [tech for tech in tech_keywords if tech.lower() in req_text.lower()]
            
            # Record the monitoring data
            import asyncio
            asyncio.create_task(monitoring_service.monitor_tech_stack_generation(
                session_id=session_id,
                requirements=requirements,
                extracted_technologies=enhanced_tech_stack,
                expected_technologies=enhanced_tech_stack,  # For now, assume extracted = expected
                explicit_technologies=explicit_technologies,
                generated_stack=enhanced_tech_stack,
                processing_time=processing_time,
                llm_calls=1,
                catalog_additions=0
            ))
            
            # Update session state with monitoring info
            import time
            st.session_state.last_analysis_time = time.time()
            
        except Exception as e:
            # Don't fail the main process if monitoring fails
            from app.utils.logger import app_logger
            app_logger.warning(f"Failed to record monitoring data: {e}")

    def _record_recommendation_monitoring_data(
        self,
        session_id: str,
        processing_time: float,
        response: Dict[str, Any]
    ) -> None:
        """Record recommendation generation data for monitoring."""
        try:
            # Try to get monitoring service
            if 'monitoring_service' not in st.session_state:
                from app.monitoring.integration_service import MonitoringIntegrationService
                st.session_state.monitoring_service = MonitoringIntegrationService()
            
            monitoring_service = st.session_state.monitoring_service
            
            # Extract data from response
            recommendations = response.get('recommendations', [])
            if recommendations:
                best_rec = recommendations[0]
                tech_stack = best_rec.get('tech_stack', [])
                
                # Record catalog health metrics
                import asyncio
                # Update monitoring metrics (handle async properly)
                try:
                    loop = asyncio.get_event_loop()
                    if loop.is_running():
                        # If loop is running, schedule the task
                        asyncio.create_task(monitoring_service.update_catalog_health_metrics(
                            total_technologies=len(tech_stack),
                            missing_technologies=0,
                            inconsistent_entries=0,
                            pending_review=0
                        ))
                    else:
                        # If no loop, run synchronously
                        loop.run_until_complete(monitoring_service.update_catalog_health_metrics(
                            total_technologies=len(tech_stack),
                            missing_technologies=0,
                            inconsistent_entries=0,
                            pending_review=0
                        ))
                except Exception as monitoring_error:
                    # Silently ignore monitoring errors
                    pass
                
                # Update session state
                import time
                st.session_state.last_analysis_time = time.time()
                
        except Exception as e:
            # Don't fail the main process if monitoring fails
            from app.utils.logger import app_logger
            app_logger.warning(f"Failed to record recommendation monitoring data: {e}")

    async def _generate_llm_tech_stack_and_explanation(self, original_tech_stack: List[str]) -> tuple[List[str], str]:
        """Generate LLM-driven tech stack and explanation based on requirements."""
        return await self._generate_llm_tech_stack_and_explanation_with_progress(original_tech_stack)
    
    def _update_recommendations_with_enhanced_data(self, enhanced_tech_stack: List[str], architecture_explanation: str):
        """Update stored recommendations with enhanced tech stack and architecture explanation."""
        try:
            if 'recommendations' in st.session_state and st.session_state.recommendations:
                recommendations = st.session_state.recommendations
                
                # Update each recommendation with enhanced data
                if 'recommendations' in recommendations:
                    for rec in recommendations['recommendations']:
                        # Store enhanced data for export
                        rec['enhanced_tech_stack'] = enhanced_tech_stack
                        rec['architecture_explanation'] = architecture_explanation
                
                # Also store at the top level for backward compatibility
                recommendations['enhanced_tech_stack'] = enhanced_tech_stack
                recommendations['architecture_explanation'] = architecture_explanation
                
                # Update session state
                st.session_state.recommendations = recommendations
                
                # Also update the persistent session state via API
                asyncio.run(self._update_persistent_session_state())
                
        except Exception as e:
            from app.utils.logger import app_logger
            app_logger.error(f"Failed to update recommendations with enhanced data: {e}")
    
    def _ensure_agentic_frameworks(self, tech_stack: List[str]) -> List[str]:
        """Ensure agentic AI frameworks are included in the tech stack for agentic solutions."""
        # Convert to lowercase for comparison
        tech_stack_lower = [tech.lower() for tech in tech_stack]
        
        # Define essential agentic frameworks
        agentic_frameworks = {
            'langchain': 'LangChain',
            'crewai': 'CrewAI', 
            'autogen': 'AutoGen',
            'langgraph': 'LangGraph',
            'semantic kernel': 'Microsoft Semantic Kernel',
            'openai assistants': 'OpenAI Assistants API'
        }
        
        # Check if any agentic frameworks are already present
        has_agentic_framework = any(
            framework in ' '.join(tech_stack_lower) 
            for framework in agentic_frameworks.keys()
        )
        
        # If no agentic frameworks found, add recommended ones
        if not has_agentic_framework:
            enhanced_stack = tech_stack.copy()
            
            # Add core agentic frameworks based on use case
            enhanced_stack.extend([
                'LangChain',  # Most versatile
                'CrewAI',     # Multi-agent coordination
                'LangGraph',  # Complex workflows
                'OpenAI Assistants API'  # Easy integration
            ])
            
            # Add supporting technologies for agentic systems
            supporting_tech = {
                'vector database': 'FAISS Vector Database',
                'redis': 'Redis',
                'postgresql': 'PostgreSQL'
            }
            
            for tech_key, tech_name in supporting_tech.items():
                if not any(tech_key in tech.lower() for tech in tech_stack_lower):
                    enhanced_stack.append(tech_name)
            
            return enhanced_stack
        
        return tech_stack
    
    def _extract_agent_name(self, role) -> str:
        """Extract agent name from role data."""
        if isinstance(role, dict):
            return role.get('name') or role.get('role') or role.get('title') or 'Agent'
        elif isinstance(role, str):
            return role
        else:
            return 'Agent'
    
    def _render_agent_card(self, role, agent_type: str):
        """Render an individual agent card with visual styling."""
        # Extract agent information
        if isinstance(role, dict):
            role_name = role.get('name') or role.get('role') or role.get('title') or 'Agent'
            role_desc = (role.get('description') or 
                        role.get('responsibility') or 
                        role.get('purpose') or 
                        role.get('role_description') or
                        f"Specialized agent responsible for {role_name.lower()} tasks")
            responsibilities = (role.get('responsibilities') or 
                              role.get('tasks') or 
                              role.get('capabilities') or 
                              role.get('duties') or [])
            autonomy_level = role.get('autonomy_level', 0.8)
        elif isinstance(role, str):
            role_name = role
            role_desc = self._get_intelligent_description(role)
            responsibilities = []
            autonomy_level = 0.8
        else:
            role_name = 'Agent'
            role_desc = str(role)
            responsibilities = []
            autonomy_level = 0.8
        
        # Choose icon and color based on agent type and name
        icon, color = self._get_agent_icon_and_color(role_name, agent_type)
        
        # Create styled container
        with st.container():
            # Agent header with icon and name
            st.markdown(f"""
            <div style="
                background: linear-gradient(135deg, {color}20, {color}10);
                border-left: 4px solid {color};
                padding: 15px;
                border-radius: 8px;
                margin: 10px 0;
            ">
                <h4 style="margin: 0; color: {color};">{icon} {role_name}</h4>
                <p style="margin: 5px 0; color: #666; font-style: italic;">{role_desc}</p>
            </div>
            """, unsafe_allow_html=True)
            
            # Agent details in columns
            col1, col2 = st.columns([2, 1])
            
            with col1:
                if responsibilities:
                    st.markdown("**🎯 Key Capabilities:**")
                    for resp in responsibilities[:3]:  # Show top 3 to keep it clean
                        st.markdown(f"• {resp}")
                    if len(responsibilities) > 3:
                        with st.expander(f"View all {len(responsibilities)} capabilities"):
                            for resp in responsibilities[3:]:
                                st.markdown(f"• {resp}")
            
            with col2:
                # Autonomy level visualization
                st.markdown("**🤖 Autonomy Level**")
                autonomy_pct = autonomy_level if isinstance(autonomy_level, float) else 0.8
                st.progress(autonomy_pct)
                
                if autonomy_pct >= 0.9:
                    st.success("Fully Autonomous")
                elif autonomy_pct >= 0.7:
                    st.info("Highly Autonomous") 
                elif autonomy_pct >= 0.5:
                    st.warning("Semi-Autonomous")
                else:
                    st.error("Requires Oversight")
    
    def _get_intelligent_description(self, role_name: str) -> str:
        """Generate intelligent descriptions for string-based roles."""
        role_descriptions = {
            'procurement': 'Handles vendor negotiations, contract analysis, and purchasing decisions',
            'negotiation': 'Manages contract negotiations, pricing discussions, and deal structuring',
            'specialist': 'Provides domain expertise and specialized knowledge for complex decisions',
            'coordinator': 'Orchestrates multi-agent workflows and manages task distribution',
            'analyst': 'Performs data analysis, risk assessment, and decision support',
            'monitor': 'Tracks system performance, compliance, and quality metrics',
            'manager': 'Oversees agent coordination and strategic decision-making',
            'expert': 'Provides specialized knowledge and technical expertise',
            'advisor': 'Offers strategic guidance and recommendations',
            'executor': 'Handles task execution and implementation'
        }
        
        role_lower = role_name.lower()
        for key, desc in role_descriptions.items():
            if key in role_lower:
                return desc
        
        return f"Specialized autonomous agent responsible for {role_name.lower()} operations and decision-making"
    
    def _get_agent_icon_and_color(self, role_name: str, agent_type: str) -> tuple[str, str]:
        """Get appropriate icon and color for agent based on role and type."""
        role_lower = role_name.lower()
        
        # Icon mapping based on role keywords
        if any(keyword in role_lower for keyword in ['coordinator', 'manager', 'orchestrator']):
            return "🎯", "#FF6B6B"
        elif any(keyword in role_lower for keyword in ['negotiation', 'procurement', 'contract']):
            return "🤝", "#4ECDC4"
        elif any(keyword in role_lower for keyword in ['analyst', 'analysis', 'data']):
            return "📊", "#45B7D1"
        elif any(keyword in role_lower for keyword in ['specialist', 'expert']):
            return "🔬", "#96CEB4"
        elif any(keyword in role_lower for keyword in ['monitor', 'tracking', 'compliance']):
            return "👁️", "#FECA57"
        elif any(keyword in role_lower for keyword in ['advisor', 'consultant']):
            return "💡", "#FF9FF3"
        else:
            # Default based on agent type
            type_mapping = {
                "coordinator": ("🎯", "#FF6B6B"),
                "specialist": ("🔬", "#4ECDC4"), 
                "support": ("🛠️", "#96CEB4")
            }
            return type_mapping.get(agent_type, ("🤖", "#45B7D1"))
    
    def _render_agent_interaction_flow(self, agent_roles_found):
        """Render a visual flow showing how agents interact."""
        st.markdown("""
        <div style="
            background: #f8f9fa;
            padding: 20px;
            border-radius: 10px;
            border: 1px solid #e9ecef;
            text-align: center;
        ">
        """, unsafe_allow_html=True)
        
        # Create flow based on number of agents
        if len(agent_roles_found) == 2:
            agent1 = self._extract_agent_name(agent_roles_found[0])
            agent2 = self._extract_agent_name(agent_roles_found[1])
            
            st.markdown(f"""
            **Workflow:** `User Request` → **{agent1}** ↔️ **{agent2}** → `Coordinated Response`
            
            *The agents collaborate directly, sharing information and coordinating their specialized capabilities.*
            """)
            
        elif len(agent_roles_found) == 3:
            agents = [self._extract_agent_name(role) for role in agent_roles_found]
            
            st.markdown(f"""
            **Workflow:** `User Request` → **{agents[0]}** → **{agents[1]}** → **{agents[2]}** → `Final Result`
            
            *Sequential collaboration with feedback loops and cross-agent communication.*
            """)
            
        else:
            # Check if we actually have a coordinator agent
            has_coordinator = any(
                any(keyword in self._extract_agent_name(role).lower() 
                    for keyword in ['coordinator', 'manager', 'orchestrator', 'supervisor'])
                for role in agent_roles_found
            )
            
            if has_coordinator:
                st.markdown(f"""
                **Complex Multi-Agent Workflow** ({len(agent_roles_found)} agents)
                
                `User Request` → **Coordinator** → **Specialist Agents** → **Integration** → `Comprehensive Solution`
                
                *Hierarchical coordination with parallel processing and intelligent task distribution.*
                """)
            else:
                # Show collaborative workflow instead
                agent_names = [self._extract_agent_name(role) for role in agent_roles_found[:3]]
                if len(agent_names) > 3:
                    agent_display = f"{', '.join(agent_names[:2])}, and {len(agent_roles_found)-2} other agents"
                else:
                    agent_display = ' → '.join(agent_names)
                
                st.markdown(f"""
                **Collaborative Multi-Agent Workflow** ({len(agent_roles_found)} agents)
                
                `User Request` → **{agent_display}** → **Integration** → `Comprehensive Solution`
                
                *Collaborative processing with specialized agents working in parallel and coordination.*
                """)
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    def _is_agentic_by_context(self, reasoning_text: str) -> bool:
        """Context-aware detection of agentic solutions.
        
        This method looks for agentic keywords but considers the context to avoid
        false positives when keywords are used to describe traditional automation.
        
        Args:
            reasoning_text: The reasoning text to analyze (should be lowercase)
            
        Returns:
            True if the text indicates an agentic solution, False otherwise
        """
        # Traditional automation indicators (these override agentic keywords)
        traditional_indicators = [
            "traditional automation",
            "conventional workflow",
            "predefined rules",
            "without requiring complex reasoning",
            "rule-based decisions",
            "predictable steps",
            "matrix-led decisions",
            "structured logic",
            "threshold trigger",
            "simple automation"
        ]
        
        # Strong agentic indicators
        agentic_indicators = [
            "autonomous agent",
            "multi-agent",
            "agentic ai",
            "agent coordination",
            "agent collaboration",
            "intelligent reasoning",
            "adaptive decision",
            "learning agent",
            "agent-based"
        ]
        
        # Check for strong traditional indicators first
        for indicator in traditional_indicators:
            if indicator in reasoning_text:
                return False
        
        # Check for strong agentic indicators
        for indicator in agentic_indicators:
            if indicator in reasoning_text:
                return True
        
        # Fallback to basic keyword detection with context
        basic_keywords = ["agent", "autonomous", "agentic", "reasoning", "decision-making"]
        
        # Only consider it agentic if keywords appear in positive context
        for keyword in basic_keywords:
            if keyword in reasoning_text:
                # Check if it's in a negative context (indicating traditional automation)
                keyword_pos = reasoning_text.find(keyword)
                context_before = reasoning_text[max(0, keyword_pos-50):keyword_pos]
                context_after = reasoning_text[keyword_pos:keyword_pos+50]
                
                negative_context = [
                    "without", "not", "no", "avoid", "instead of", "rather than",
                    "doesn't require", "don't need", "not requiring", "without requiring",
                    "but not requiring", "mentioned but not", "but not"
                ]
                
                # If keyword is in negative context, it's traditional automation
                if any(neg in context_before or neg in context_after for neg in negative_context):
                    continue
                else:
                    return True
        
        return False
    
    def _create_agent_architecture_mermaid(self, agent_roles_found) -> str:
        """Create a Mermaid diagram showing agent architecture and interactions."""
        agents = []
        used_names = set()
        
        # Extract agent information and create unique, clean names for diagram
        for i, role in enumerate(agent_roles_found):
            agent_name = self._extract_agent_name(role)
            # Clean name for Mermaid (remove special characters, limit length)
            clean_name = ''.join(c for c in agent_name if c.isalnum() or c in ' -_')[:15]
            
            # Ensure unique names by adding numbers if needed
            original_clean_name = clean_name
            counter = 1
            while clean_name in used_names:
                clean_name = f"{original_clean_name}{counter}"
                counter += 1
            used_names.add(clean_name)
            
            agent_id = f"A{i+1}"
            agents.append((agent_id, clean_name, role))
        
        if len(agents) == 2:
            # Two-agent collaboration - use safer syntax without emojis in node IDs
            agent1_clean = _sanitize(agents[0][1])
            agent2_clean = _sanitize(agents[1][1])
            
            return f"""flowchart TD
    U[User Request] --> {agents[0][0]}[{agent1_clean}]
    U --> {agents[1][0]}[{agent2_clean}]
    {agents[0][0]} <-->|Collaborate| {agents[1][0]}
    {agents[0][0]} --> R[Coordinated Response]
    {agents[1][0]} --> R
    R --> U
    
    style {agents[0][0]} fill:#4ECDC4,stroke:#38B2AC,stroke-width:3px
    style {agents[1][0]} fill:#45B7D1,stroke:#3182CE,stroke-width:3px
    style R fill:#96CEB4,stroke:#68D391,stroke-width:2px
    style U fill:#FED7D7,stroke:#E53E3E,stroke-width:2px"""
        
        elif len(agents) == 3:
            # Three-agent hierarchy - use safer syntax
            agent1_clean = _sanitize(agents[0][1])
            agent2_clean = _sanitize(agents[1][1])
            agent3_clean = _sanitize(agents[2][1])
            
            return f"""flowchart TD
    U[User Request] --> {agents[0][0]}[{agent1_clean}]
    {agents[0][0]} -->|Delegate| {agents[1][0]}[{agent2_clean}]
    {agents[0][0]} -->|Delegate| {agents[2][0]}[{agent3_clean}]
    
    {agents[1][0]} <-->|Communicate| {agents[2][0]}
    
    {agents[1][0]} --> R[Integrated Results]
    {agents[2][0]} --> R
    {agents[0][0]} --> R
    R --> U
    
    style {agents[0][0]} fill:#FF6B6B,stroke:#E53E3E,stroke-width:3px
    style {agents[1][0]} fill:#4ECDC4,stroke:#38B2AC,stroke-width:3px
    style {agents[2][0]} fill:#45B7D1,stroke:#3182CE,stroke-width:3px
    style R fill:#96CEB4,stroke:#68D391,stroke-width:2px
    style U fill:#FED7D7,stroke:#E53E3E,stroke-width:2px"""
        
        else:
            # Complex multi-agent system (4+ agents)
            # Find coordinator or use first agent
            coordinator_idx = 0
            for i, (agent_id, agent_name, role) in enumerate(agents):
                if any(keyword in agent_name.lower() for keyword in ['coordinator', 'manager', 'orchestrator']):
                    coordinator_idx = i
                    break
            
            coordinator = agents[coordinator_idx]
            specialists = [agent for i, agent in enumerate(agents) if i != coordinator_idx]
            
            # For large numbers of agents, use a more organized layout
            if len(specialists) > 8:
                # Group specialists into logical clusters - use safer syntax
                coordinator_clean = _sanitize(coordinator[1])
                diagram = f"""flowchart TD
    U[User Request] --> {coordinator[0]}[{coordinator_clean}]
    
    %% Primary specialists
"""
                # Show first 6 specialists directly
                for i, spec in enumerate(specialists[:6]):
                    spec_clean = _sanitize(spec[1])
                    diagram += f"    {coordinator[0]} -->|Task {i+1}| {spec[0]}[{spec_clean}]\n"
                
                # Group remaining specialists
                if len(specialists) > 6:
                    diagram += f"\n    %% Additional specialists\n"
                    diagram += f"    {coordinator[0]} --> SG[Additional Specialists]\n"
                    for spec in specialists[6:]:
                        spec_clean = _sanitize(spec[1])
                        diagram += f"    SG --> {spec[0]}[{spec_clean}]\n"
                
                diagram += "\n    %% Collaboration patterns\n"
                # Add some strategic connections
                for i in range(min(3, len(specialists) - 1)):
                    diagram += f"    {specialists[i][0]} <-->|Communicate| {specialists[i+1][0]}\n"
                
                diagram += "\n    %% Results aggregation\n"
                for spec in specialists:
                    diagram += f"    {spec[0]} --> R[Coordinated Solution]\n"
                
                diagram += f"    {coordinator[0]} --> R\n    R --> U\n\n"
                
            else:
                # Standard layout for smaller numbers - use safer syntax
                coordinator_clean = _sanitize(coordinator[1])
                diagram = f"""flowchart TD
    U[User Request] --> {coordinator[0]}[{coordinator_clean}]
    
"""
                
                # Add ALL specialist nodes
                for spec in specialists:
                    spec_clean = _sanitize(spec[1])
                    diagram += f"    {coordinator[0]} -->|Delegate| {spec[0]}[{spec_clean}]\n"
                
                diagram += "\n"
                
                # Add strategic cross-communication
                for i in range(min(4, len(specialists) - 1)):
                    diagram += f"    {specialists[i][0]} <-->|Communicate| {specialists[i+1][0]}\n"
                
                diagram += "\n"
                
                # Results aggregation
                for spec in specialists:
                    diagram += f"    {spec[0]} --> R[Coordinated Solution]\n"
                
                diagram += f"    {coordinator[0]} --> R\n    R --> U\n\n"
            
            # Add styling for ALL agents
            diagram += f"    style {coordinator[0]} fill:#FF6B6B,stroke:#E53E3E,stroke-width:4px\n"
            
            colors = ["#4ECDC4,stroke:#38B2AC", "#45B7D1,stroke:#3182CE", "#F7DC6F,stroke:#F1C40F", "#DDA0DD,stroke:#9932CC", "#96CEB4,stroke:#68D391", "#FFA07A,stroke:#FF6347", "#20B2AA,stroke:#008B8B", "#9370DB,stroke:#8A2BE2"]
            for i, spec in enumerate(specialists):
                color = colors[i % len(colors)]
                diagram += f"    style {spec[0]} fill:{color},stroke-width:3px\n"
            
            diagram += "    style R fill:#96CEB4,stroke:#68D391,stroke-width:2px\n"
            diagram += "    style U fill:#FED7D7,stroke:#E53E3E,stroke-width:2px"
            
            # Debug: Add line breaks for better readability
            diagram = diagram.replace('\n\n', '\n').strip()
            
            return diagram
    
    def _create_single_agent_mermaid(self, agent_role) -> str:
        """Create a Mermaid diagram for single agent architecture."""
        agent_name = self._extract_agent_name(agent_role)
        clean_name = _sanitize(agent_name)
        
        return f"""flowchart TD
    U[User Request] --> A[{clean_name}]
    A --> P[Processing and Analysis]
    P --> D[Decision Making]
    D --> E[Action Execution]
    E --> M[Monitoring and Feedback]
    M --> R[Response and Results]
    R --> U
    
    %% Self-improvement loop
    M -->|Learn and Adapt| A
    
    style A fill:#4CAF50,stroke:#2E7D32,stroke-width:4px
    style P fill:#2196F3,stroke:#1565C0,stroke-width:2px
    style D fill:#FF9800,stroke:#E65100,stroke-width:2px
    style E fill:#9C27B0,stroke:#6A1B9A,stroke-width:2px
    style M fill:#607D8B,stroke:#37474F,stroke-width:2px
    style R fill:#96CEB4,stroke:#68D391,stroke-width:2px
    style U fill:#FED7D7,stroke:#E53E3E,stroke-width:2px"""
    
    async def _update_persistent_session_state(self):
        """Update the persistent session state with enhanced recommendation data."""
        try:
            if 'session_id' in st.session_state and 'recommendations' in st.session_state:
                # Call API to update session state
                await self.make_api_request(
                    "PUT",
                    f"/sessions/{st.session_state.session_id}/enhanced_data",
                    {
                        "enhanced_tech_stack": st.session_state.recommendations.get('enhanced_tech_stack'),
                        "architecture_explanation": st.session_state.recommendations.get('architecture_explanation')
                    }
                )
        except Exception as e:
            from app.utils.logger import app_logger
            app_logger.error(f"Failed to update persistent session state: {e}")

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
    
    def get_enhanced_analysis_data(self) -> Dict[str, Any]:
        """Retrieve enhanced tech stack and architecture explanation from session state.
        
        Returns:
            Dictionary containing enhanced analysis data with fallback handling
        """
        try:
            recommendations = st.session_state.get('recommendations', {})
            enhanced_tech_stack = recommendations.get('enhanced_tech_stack')
            architecture_explanation = recommendations.get('architecture_explanation')
            
            # Log enhanced data availability
            if enhanced_tech_stack:
                app_logger.info(f"Enhanced tech stack available for diagrams: {len(enhanced_tech_stack)} technologies")
            else:
                app_logger.info("No enhanced tech stack available, will use recommendation tech stack")
                
            if architecture_explanation:
                app_logger.info(f"Architecture explanation available for diagrams: {len(architecture_explanation)} chars")
            else:
                app_logger.info("No architecture explanation available")
            
            return {
                'enhanced_tech_stack': enhanced_tech_stack,
                'architecture_explanation': architecture_explanation,
                'has_enhanced_data': bool(enhanced_tech_stack or architecture_explanation)
            }
        except Exception as e:
            app_logger.error(f"Error retrieving enhanced analysis data: {e}")
            return {
                'enhanced_tech_stack': None,
                'architecture_explanation': None,
                'has_enhanced_data': False
            }

    def render_mermaid_diagrams(self):
        """Render Mermaid diagrams panel."""
        st.header("📊 System Diagrams")
        
        # Check if we have session data
        if not st.session_state.get('session_id'):
            st.info("Please submit a requirement first to generate diagrams.")
            return
        
        # Check if this is an agentic solution to show appropriate diagram options
        rec = st.session_state.recommendations
        reasoning = rec.get("reasoning", "").lower() if rec else ""
        is_agentic = self._is_agentic_by_context(reasoning)
        
        # Check if Graphviz is available for infrastructure diagrams
        def check_graphviz_available():
            """Check if Graphviz is available on the system."""
            import subprocess
            try:
                subprocess.run(['dot', '-V'], capture_output=True, check=True, timeout=5)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError, subprocess.TimeoutExpired):
                return False
        
        def is_infrastructure_diagram(diagram_type_str):
            """Check if the diagram type is Infrastructure Diagram (with or without warning)."""
            return diagram_type_str.startswith("Infrastructure Diagram")
        
        graphviz_available = check_graphviz_available()
        
        # Add agentic-specific diagram option if applicable
        diagram_options = ["Context Diagram", "Container Diagram", "Sequence Diagram", "Tech Stack Wiring Diagram"]
        
        # Add Infrastructure Diagram with warning if Graphviz not available
        if graphviz_available:
            diagram_options.append("Infrastructure Diagram")
        else:
            diagram_options.append("Infrastructure Diagram ⚠️ (Requires Graphviz)")
        
        diagram_options.append("C4 Diagram")
        
        if is_agentic:
            diagram_options.insert(3, "Agent Interaction Diagram")  # Insert after Sequence Diagram
        
        diagram_type = st.selectbox(
            "Select diagram type:",
            diagram_options
        )
        
        # Show description for selected diagram type
        diagram_descriptions = {
            "Context Diagram": "🌐 **System Context**: Shows the system boundaries, users, and external systems it integrates with.",
            "Container Diagram": "📦 **System Containers**: Shows the internal components, services, and how they interact within the system.",
            "Sequence Diagram": "🔄 **Process Flow**: Shows the step-by-step sequence of interactions and decision points in the automation.",
            "Agent Interaction Diagram": "🤖 **Agent Collaboration**: Shows how autonomous AI agents communicate, coordinate, and make decisions together. Displays agent roles, responsibilities, and interaction patterns in your multi-agent system.",
            "Tech Stack Wiring Diagram": "🔌 **Technical Wiring**: Shows how all the recommended technologies connect, communicate, and pass data between each other. Like a blueprint for developers showing API calls, database connections, authentication flows, and service integrations.",
            "Infrastructure Diagram": "🏗️ **Infrastructure Architecture**: Shows cloud infrastructure components with vendor-specific icons (AWS, GCP, Azure). Displays compute, storage, database, and networking services with realistic cloud architecture patterns.",
            "C4 Diagram": "🏛️ **C4 Architecture Model**: Uses proper C4 syntax to show software architecture following the official C4 model standards. Provides standardized architectural documentation with automatic C4 styling, system boundaries, and relationship conventions. Unlike the Context/Container diagrams above (which use flowchart syntax), C4 diagrams use official C4 notation with built-in styling and follow industry-standard C4 modeling practices."
        }
        
        st.info(diagram_descriptions[diagram_type])
        
        # Show Graphviz warning if Infrastructure Diagram is selected without Graphviz
        if is_infrastructure_diagram(diagram_type) and not graphviz_available:
            st.warning("""
            ⚠️ **Graphviz Required**: Infrastructure diagrams need Graphviz installed on your system.
            
            **Quick Install:**
            - **Windows**: `choco install graphviz` or `winget install graphviz`
            - **macOS**: `brew install graphviz`
            - **Linux**: `sudo apt-get install graphviz`
            
            After installation, restart the application. You can still generate the diagram - it will show installation instructions if Graphviz is missing.
            """)
        
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
                # Show authentication status based on provider
                provider = provider_config.get('provider', '')
                if provider == 'bedrock':
                    has_bedrock_api_key = bool(provider_config.get('bedrock_api_key'))
                    has_aws_creds = bool(provider_config.get('aws_access_key_id') and provider_config.get('aws_secret_access_key'))
                    has_session_creds = bool(provider_config.get('aws_session_token'))
                    auth_status = has_bedrock_api_key or has_aws_creds or has_session_creds
                    auth_method = "Bedrock API Key" if has_bedrock_api_key else ("AWS Credentials" if has_aws_creds else ("Session Credentials" if has_session_creds else "None"))
                    st.write(f"- Authentication: {auth_status} ({auth_method})")
                else:
                    st.write(f"- API Key present: {bool(provider_config.get('api_key'))}")
        
        requirement_text = requirements.get('description', 'No requirement available')
        
        if st.button(f"Generate {diagram_type}", type="primary"):
            try:
                # Additional validation
                if not requirement_text or requirement_text == 'No requirement available':
                    st.error("No requirement found. Please submit a requirement first.")
                    return
                
                # Check for valid authentication based on provider type
                provider = provider_config.get('provider', '')
                if provider == 'bedrock':
                    # For Bedrock, check for either API key or AWS credentials
                    has_bedrock_api_key = bool(provider_config.get('bedrock_api_key'))
                    has_aws_creds = bool(provider_config.get('aws_access_key_id') and provider_config.get('aws_secret_access_key'))
                    has_session_creds = bool(provider_config.get('aws_session_token'))  # Session credentials from AWS CLI/SSO
                    
                    if not (has_bedrock_api_key or has_aws_creds or has_session_creds):
                        st.error("No valid Bedrock authentication found. Please configure AWS credentials or Bedrock API key in the sidebar.")
                        return
                else:
                    # For other providers, check for API key
                    if not provider_config.get('api_key'):
                        st.error("No API key found. Please configure your provider in the sidebar.")
                        return
                
                # Show requirements in a collapsible expander to save space
                with st.expander("📋 View Original Requirements", expanded=False):
                    st.write(requirement_text)
                
                # Get enhanced analysis data for diagram generation
                enhanced_data = self.get_enhanced_analysis_data()
                enhanced_tech_stack = enhanced_data.get('enhanced_tech_stack')
                architecture_explanation = enhanced_data.get('architecture_explanation')
                
                # Validate enhanced data
                if enhanced_tech_stack and not isinstance(enhanced_tech_stack, list):
                    app_logger.warning(f"Enhanced tech stack is not a list: {type(enhanced_tech_stack)}, ignoring")
                    enhanced_tech_stack = None
                
                if architecture_explanation and not isinstance(architecture_explanation, str):
                    app_logger.warning(f"Architecture explanation is not a string: {type(architecture_explanation)}, ignoring")
                    architecture_explanation = None
                
                if enhanced_data.get('has_enhanced_data'):
                    st.info("✨ Using enhanced analysis data for more accurate diagrams")
                
                # Show progress indicator for diagram generation
                progress_placeholder = st.empty()
                with progress_placeholder.container():
                    st.info(f"🤖 **Generating {diagram_type}...**")
                    progress_bar = st.progress(0)
                    status_text = st.empty()
                    
                    status_text.text("Preparing diagram generation...")
                    progress_bar.progress(20)
                    
                    status_text.text(f"Analyzing requirements for {diagram_type.lower()}...")
                    progress_bar.progress(40)
                    
                    status_text.text("Generating diagram with AI...")
                    progress_bar.progress(60)
                    
                    if diagram_type == "Context Diagram":
                        mermaid_code = asyncio.run(build_context_diagram(requirement_text, recommendations, enhanced_tech_stack, architecture_explanation))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "Container Diagram":
                        mermaid_code = asyncio.run(build_container_diagram(requirement_text, recommendations, enhanced_tech_stack, architecture_explanation))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "Sequence Diagram":
                        mermaid_code = asyncio.run(build_sequence_diagram(requirement_text, recommendations, enhanced_tech_stack, architecture_explanation))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "Agent Interaction Diagram":
                        mermaid_code = asyncio.run(build_agent_interaction_diagram(requirement_text, recommendations, enhanced_tech_stack, architecture_explanation))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "Tech Stack Wiring Diagram":
                        mermaid_code = asyncio.run(build_tech_stack_wiring_diagram(requirement_text, recommendations, enhanced_tech_stack, architecture_explanation))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif diagram_type == "C4 Diagram":
                        mermaid_code = asyncio.run(build_c4_diagram(requirement_text, recommendations, enhanced_tech_stack, architecture_explanation))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                    elif is_infrastructure_diagram(diagram_type):  # Infrastructure Diagram
                        infrastructure_spec = asyncio.run(build_infrastructure_diagram(requirement_text, recommendations, enhanced_tech_stack, architecture_explanation))
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_spec'] = infrastructure_spec
                        st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "infrastructure"
                    
                    status_text.text("Finalizing diagram...")
                    progress_bar.progress(90)
                    
                    status_text.text("Complete! ✅")
                    progress_bar.progress(100)
                
                # Clear progress indicator
                progress_placeholder.empty()
                
                st.success("✅ Diagram generated successfully!")
                    
            except Exception as e:
                # If enhanced data was used and generation failed, try without enhanced data
                if enhanced_data.get('has_enhanced_data'):
                    st.warning(f"⚠️ Diagram generation failed with enhanced data. Retrying with basic data...")
                    app_logger.warning(f"Diagram generation failed with enhanced data: {e}. Retrying without enhanced data.")
                    
                    try:
                        # Show progress indicator for retry
                        retry_progress_placeholder = st.empty()
                        with retry_progress_placeholder.container():
                            st.info(f"🔄 **Retrying {diagram_type} generation with basic data...**")
                            retry_progress_bar = st.progress(0)
                            retry_status_text = st.empty()
                            
                            retry_status_text.text("Preparing retry with basic data...")
                            retry_progress_bar.progress(30)
                            
                            retry_status_text.text("Generating diagram...")
                            retry_progress_bar.progress(70)
                            
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
                            elif diagram_type == "Agent Interaction Diagram":
                                mermaid_code = asyncio.run(build_agent_interaction_diagram(requirement_text, recommendations))
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                            elif diagram_type == "Tech Stack Wiring Diagram":
                                mermaid_code = asyncio.run(build_tech_stack_wiring_diagram(requirement_text, recommendations))
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                            elif diagram_type == "C4 Diagram":
                                mermaid_code = asyncio.run(build_c4_diagram(requirement_text, recommendations))
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_code'] = mermaid_code
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "mermaid"
                            elif is_infrastructure_diagram(diagram_type):  # Infrastructure Diagram
                                infrastructure_spec = asyncio.run(build_infrastructure_diagram(requirement_text, recommendations))
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_spec'] = infrastructure_spec
                                st.session_state[f'{diagram_type.lower().replace(" ", "_")}_type'] = "infrastructure"
                            
                            retry_status_text.text("Retry complete! ✅")
                            retry_progress_bar.progress(100)
                        
                        # Clear retry progress indicator
                        retry_progress_placeholder.empty()
                        
                        st.success("✅ Diagram generated successfully (using basic data)!")
                            
                    except Exception as retry_e:
                        st.error(f"❌ Error generating diagram (retry also failed): {str(retry_e)}")
                        st.write(f"**Error details:** {type(retry_e).__name__}: {str(retry_e)}")
                        app_logger.error(f"Diagram generation failed even without enhanced data: {retry_e}")
                        return
                else:
                    st.error(f"❌ Error generating diagram: {str(e)}")
                    st.write(f"**Error details:** {type(e).__name__}: {str(e)}")
                    app_logger.error(f"Diagram generation failed: {e}")
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
                
                # Debug information for Agent Interaction Diagram
                if diagram_type == "Agent Interaction Diagram":
                    if st.session_state.get('debug_mode', False):
                        st.write(f"**Debug - Diagram Key:** {diagram_key}")
                        st.write(f"**Debug - Code Length:** {len(mermaid_code) if mermaid_code else 0}")
                        st.write(f"**Debug - First 100 chars:** {mermaid_code[:100] if mermaid_code else 'None'}")
                    
                    # Show code preview for Agent Interaction Diagram to help debug rendering issues
                    with st.expander("🔍 View Mermaid Code", expanded=False):
                        st.code(mermaid_code, language="mermaid")
                        st.info("💡 If the diagram above is blank, try copying this code to [mermaid.live](https://mermaid.live) to test it")
                
                self.render_mermaid(mermaid_code, diagram_type)
            
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
            
            # Add helpful context for C4 Diagrams
            elif diagram_type == "C4 Diagram":
                st.info("""
                **How to read this C4 diagram:**
                - **Person** = External users or actors (customers, admins)
                - **System** = Software systems (your application, external services)
                - **Container** = Applications, databases, file systems within a system
                - **Boundaries** = System or enterprise boundaries (dotted lines)
                - **Relationships** = Interactions between elements with descriptions
                
                This follows the official C4 model for software architecture documentation with standardized notation and styling.
                """)
            
            # Check if diagram generation failed and show helpful message (only for Mermaid diagrams)
            if diagram_render_type == "mermaid":
                mermaid_code = st.session_state[diagram_key]
                if "Diagram Generation Error" in mermaid_code:
                    error_message = """
                    **Diagram Generation Issue Detected**
                    
                    The LLM generated a diagram with formatting issues. This can happen with certain providers or complex tech stacks.
                    
                    **Suggestions:**
                    - Try generating the diagram again (click the Generate button)
                    - Switch to a different LLM provider (OpenAI usually works best for diagrams)
                    - Use the fake provider for a basic diagram structure
                    """
                    
                    # Add C4-specific guidance
                    if diagram_type == "C4 Diagram":
                        error_message += """
                    
                    **C4 Diagram Specific Tips:**
                    - C4 diagrams use specialized syntax (Person, System, Container, Rel)
                    - Some providers may struggle with C4 syntax - try OpenAI or Claude
                    - The fake provider provides a valid C4 diagram structure as fallback
                        """
                    
                    st.warning(error_message)
                elif "generation failed" in mermaid_code.lower():
                    error_message = """
                    **Diagram Generation Failed**
                    
                    There was an error generating the diagram. Please check:
                    - Your LLM provider is properly configured
                    - You have a valid API key
                    - Try switching providers or generating again
                    """
                    
                    # Add C4-specific guidance
                    if diagram_type == "C4 Diagram":
                        error_message += """
                    
                    **For C4 Diagrams:**
                    - Ensure your provider supports Mermaid C4 syntax
                    - Try the fake provider for a working C4 example
                    - C4 diagrams require specific element types (Person, System, Container)
                        """
                    
                    st.error(error_message)
                
                # Show code
                with st.expander("View Mermaid Code"):
                    st.code(mermaid_code, language="mermaid")
    
    def render_mermaid(self, mermaid_code: str, diagram_type: str = "Diagram"):
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
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        with col1:
            if st.button("🔄 Redraw", key=f"redraw_{diagram_id}", help="Re-render the diagram using existing code"):
                # Force re-render by incrementing a counter that changes the component key
                current_redraw_count = st.session_state.get(f"redraw_count_{diagram_id}", 0)
                st.session_state[f"redraw_count_{diagram_id}"] = current_redraw_count + 1
                st.rerun()
        
        with col2:
            if st.button("🔍 Large View", key=f"expand_{diagram_id}"):
                st.session_state[f"show_large_{diagram_id}"] = not st.session_state.get(f"show_large_{diagram_id}", False)
        
        with col3:
            if st.button("📐 Export Draw.io", key=f"drawio_{diagram_id}"):
                self.export_to_drawio(mermaid_code, f"AAA {diagram_type}", diagram_id)
        
        with col4:
            if st.button("🌐 Open in Browser", key=f"browser_{diagram_id}"):
                self.open_diagram_in_browser(mermaid_code, diagram_id)
        
        with col5:
            if st.button("📋 Show Code", key=f"code_{diagram_id}"):
                st.session_state[f"show_code_{diagram_id}"] = not st.session_state.get(f"show_code_{diagram_id}", False)
        
        # Get redraw counter to force component refresh
        redraw_count = st.session_state.get(f"redraw_count_{diagram_id}", 0)
        
        # Check if we should show large view
        show_large = st.session_state.get(f"show_large_{diagram_id}", False)
        
        if show_large:
            st.write("**🔍 Large View Mode** - Click 'Large View' again to return to normal size")
            
            # Use streamlit_mermaid for large view
            if MERMAID_AVAILABLE and stmd:
                try:
                    stmd.st_mermaid(mermaid_code, height=700, key=f"large_{diagram_id}_{redraw_count}")
                except Exception as e:
                    st.error(f"Error rendering large view: {e}")
                    st.info("💡 Try copying the code below to [mermaid.live](https://mermaid.live) to view the diagram")
                    st.code(mermaid_code, language="mermaid")
            else:
                st.info("💡 Mermaid diagrams require the streamlit-mermaid package. Showing code instead:")
                st.code(mermaid_code, language="mermaid")
        else:
            # Regular view - use streamlit_mermaid
            if MERMAID_AVAILABLE and stmd:
                try:
                    stmd.st_mermaid(mermaid_code, height=500, key=f"regular_{diagram_id}_{redraw_count}")
                except Exception as e:
                    st.error(f"Error rendering diagram: {e}")
                    st.code(mermaid_code, language="mermaid")
            else:
                st.info("💡 Mermaid diagrams require the streamlit-mermaid package. Showing code instead:")
                # Show code as fallback
                st.code(mermaid_code, language="mermaid")
        
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
                # Draw.io export button
                if st.button("📐 Export to Draw.io", key=f"drawio_expanded_{diagram_id}"):
                    self.export_to_drawio(mermaid_code, f"AAA Diagram", diagram_id)
            
            # Additional row for Mermaid Live link
            st.markdown("---")
            import urllib.parse
            encoded_code = urllib.parse.quote(mermaid_code)
            mermaid_live_url = f"https://mermaid.live/edit#{encoded_code}"
            st.markdown(f"🔗 **[Open in Mermaid Live Editor]({mermaid_live_url})** - Test and modify your diagram online", unsafe_allow_html=True)
    
    def open_diagram_in_browser(self, mermaid_code: str, diagram_id: str):
        """Create and save a standalone HTML file for the diagram and open it in browser."""
        html_content = self.create_standalone_html(mermaid_code, diagram_id)
        
        # Save to exports directory
        import os
        import base64
        import webbrowser
        from pathlib import Path
        
        os.makedirs("exports", exist_ok=True)
        file_path = f"exports/diagram_{diagram_id}.html"
        
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(html_content)
        
        # Get absolute path for browser opening
        abs_path = os.path.abspath(file_path)
        file_url = f"file://{abs_path}"
        
        # Escape HTML content for JavaScript
        escaped_html = html_content.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
        
        # Create JavaScript that will actually work in Streamlit
        open_js = f"""
        <div id="diagram-opener-{diagram_id}">
            <div style="padding: 15px; background-color: #d4edda; border: 1px solid #c3e6cb; border-radius: 4px; margin: 10px 0;">
                <strong>🌐 Opening diagram in new tab...</strong><br>
                <button onclick="openDiagramTab_{diagram_id}()" style="margin-top: 10px; padding: 8px 16px; background-color: #28a745; color: white; border: none; border-radius: 4px; cursor: pointer;">
                    🚀 Click to Open Diagram
                </button>
                <br><small style="margin-top: 5px; display: block;">Auto-opening in 1 second... or click the button above</small>
            </div>
        </div>
        
        <script>
        function openDiagramTab_{diagram_id}() {{
            try {{
                // Create a blob URL for the HTML content
                const htmlContent = `{escaped_html}`;
                const blob = new Blob([htmlContent], {{ type: 'text/html' }});
                const url = URL.createObjectURL(blob);
                
                // Open in new tab
                const newWindow = window.open(url, '_blank', 'noopener,noreferrer');
                
                if (newWindow && !newWindow.closed) {{
                    // Success message
                    document.getElementById('diagram-opener-{diagram_id}').innerHTML = `
                        <div style="padding: 15px; background-color: #d1ecf1; border: 1px solid #bee5eb; border-radius: 4px; margin: 10px 0;">
                            <strong>✅ Diagram opened successfully!</strong><br>
                            <small>Check your browser for the new tab with your diagram.</small>
                        </div>
                    `;
                    
                    // Clean up the blob URL after a delay
                    setTimeout(() => URL.revokeObjectURL(url), 2000);
                }} else {{
                    throw new Error('Popup blocked or failed to open');
                }}
            }} catch (error) {{
                // Popup blocked or error message
                document.getElementById('diagram-opener-{diagram_id}').innerHTML = `
                    <div style="padding: 15px; background-color: #f8d7da; border: 1px solid #f5c6cb; border-radius: 4px; margin: 10px 0;">
                        <strong>⚠️ Could not open new tab</strong><br>
                        <small>Your browser may have blocked the popup. Please use the download button or manual options below.</small>
                    </div>
                `;
                console.log('Failed to open diagram tab:', error);
            }}
        }}
        
        // Auto-trigger after a delay to allow page to load
        setTimeout(function() {{
            openDiagramTab_{diagram_id}();
        }}, 1000);
        </script>
        """
        
        # Display the JavaScript
        st.components.v1.html(open_js, height=120)
        
        # Also save file locally for backup
        st.info(f"💾 Diagram also saved to `{file_path}` for local access")
        
        # Show the file path as copyable text for manual opening
        with st.expander("🔧 Manual Options"):
            st.code(f"open {file_path}", language="bash")
            st.write("Or copy this path to open manually:", f"`{abs_path}`")
            
            # Add a download button as another option
            st.download_button(
                label="📥 Download HTML File",
                data=html_content,
                file_name=f"diagram_{diagram_id}.html",
                mime="text/html",
                key=f"download_html_{diagram_id}"
            )
    
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
    

    def export_to_drawio(self, mermaid_code: str, diagram_title: str, diagram_id: str):
        """Export Mermaid diagram for Draw.io import."""
        try:
            # Provide Mermaid file for Draw.io import
            st.success("✅ Export ready for Draw.io!")
            
            # Create download button for Mermaid file
            st.download_button(
                label="📝 Download Mermaid File (.mmd)",
                data=mermaid_code,
                file_name=f"{diagram_title.replace(' ', '_')}_{diagram_id}.mmd",
                mime="text/plain",
                key=f"download_mermaid_{diagram_id}"
            )
            
            # Create a simple Draw.io XML wrapper
            drawio_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="{datetime.now().isoformat()}" agent="AAA-Streamlit" version="21.6.5" etag="generated">
  <diagram name="{diagram_title}" id="diagram_{diagram_id}">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="mermaid-code" value="{mermaid_code.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')}" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily=Courier New;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="740" height="400" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
            
            st.download_button(
                label="📐 Download Draw.io File (.drawio)",
                data=drawio_xml,
                file_name=f"{diagram_title.replace(' ', '_')}_{diagram_id}.drawio",
                mime="application/xml",
                key=f"download_drawio_{diagram_id}"
            )
            
            st.info("""
            **📐 How to use in Draw.io:**
            
            **Option 1 - Import Mermaid directly:**
            1. Open [draw.io](https://app.diagrams.net/) or [diagrams.net](https://diagrams.net/)
            2. Click "+" to create new diagram
            3. Choose "Advanced" → "Mermaid"
            4. Paste the Mermaid code from the .mmd file
            5. Draw.io will convert it to an editable diagram
            
            **Option 2 - Open Draw.io file:**
            1. Open [draw.io](https://app.diagrams.net/)
            2. Click "Open Existing Diagram"
            3. Upload the downloaded .drawio file
            4. The Mermaid code will be displayed as text for reference
            
            **Tip:** Option 1 (Mermaid import) usually gives better results for editing.
            """)
            
        except Exception as e:
            st.error(f"❌ Failed to prepare export: {str(e)}")
            app_logger.error(f"Draw.io export preparation failed: {e}")
    
    def export_infrastructure_to_drawio(self, infrastructure_spec: Dict[str, Any], diagram_title: str, diagram_id: str):
        """Export Infrastructure diagram for Draw.io import."""
        try:
            import json
            
            st.success("✅ Export ready for Draw.io!")
            
            # Create download buttons
            col1, col2 = st.columns(2)
            
            with col1:
                # Create a simple Draw.io XML with infrastructure spec as text
                spec_json = json.dumps(infrastructure_spec, indent=2)
                drawio_xml = f"""<?xml version="1.0" encoding="UTF-8"?>
<mxfile host="app.diagrams.net" modified="{datetime.now().isoformat()}" agent="AAA-Streamlit" version="21.6.5" etag="generated">
  <diagram name="{diagram_title}" id="diagram_{diagram_id}">
    <mxGraphModel dx="1422" dy="794" grid="1" gridSize="10" guides="1" tooltips="1" connect="1" arrows="1" fold="1" page="1" pageScale="1" pageWidth="827" pageHeight="1169" math="0" shadow="0">
      <root>
        <mxCell id="0" />
        <mxCell id="1" parent="0" />
        <mxCell id="infrastructure-spec" value="{spec_json.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;')}" style="text;html=1;strokeColor=none;fillColor=none;align=left;verticalAlign=top;whiteSpace=wrap;rounded=0;fontFamily=Courier New;fontSize=10;" vertex="1" parent="1">
          <mxGeometry x="40" y="40" width="740" height="600" as="geometry" />
        </mxCell>
      </root>
    </mxGraphModel>
  </diagram>
</mxfile>"""
                
                st.download_button(
                    label="📐 Download Draw.io File",
                    data=drawio_xml,
                    file_name=f"{diagram_title.replace(' ', '_')}_{diagram_id}.drawio",
                    mime="application/xml",
                    key=f"download_infra_drawio_{diagram_id}"
                )
            
            with col2:
                st.download_button(
                    label="📋 Download JSON Spec",
                    data=json.dumps(infrastructure_spec, indent=2),
                    file_name=f"{diagram_title.replace(' ', '_')}_{diagram_id}.json",
                    mime="application/json",
                    key=f"download_infra_json_{diagram_id}"
                )
            
            st.info("""
            **📐 How to use with Draw.io:**
            
            **For Infrastructure Diagrams:**
            1. Open [draw.io](https://app.diagrams.net/) or [diagrams.net](https://diagrams.net/)
            2. Use the AWS, GCP, or Azure shape libraries for cloud components
            3. Reference the JSON specification to recreate the architecture
            4. The Draw.io file contains the specification as text for reference
            
            **💡 Tips:**
            - Use Draw.io's cloud provider libraries (AWS, GCP, Azure) for proper icons
            - The JSON specification shows all components and their relationships
            - Consider using Draw.io's "Import from" feature with cloud architecture templates
            
            **Alternative Tools:**
            - Use the JSON with Terraform or CloudFormation for infrastructure as code
            - Import into other architecture tools like Lucidchart or Visio
            """)
            
        except Exception as e:
            st.error(f"❌ Failed to prepare export: {str(e)}")
            app_logger.error(f"Infrastructure Draw.io export preparation failed: {e}")

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
        col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 1])
        with col1:
            if st.button("🔄 Redraw", key=f"infra_redraw_{diagram_id}", help="Re-render the diagram using existing specification"):
                # Force re-render by incrementing a counter that changes the component key
                current_redraw_count = st.session_state.get(f"infra_redraw_count_{diagram_id}", 0)
                st.session_state[f"infra_redraw_count_{diagram_id}"] = current_redraw_count + 1
                st.rerun()
        
        with col2:
            if st.button("🔍 Large View", key=f"infra_expand_{diagram_id}"):
                st.session_state[f"show_large_infra_{diagram_id}"] = not st.session_state.get(f"show_large_infra_{diagram_id}", False)
        
        with col3:
            if st.button("💾 Download", key=f"infra_download_{diagram_id}"):
                self.download_infrastructure_diagram(infrastructure_spec, diagram_id)
        
        with col4:
            if st.button("📐 Export Draw.io", key=f"infra_drawio_{diagram_id}"):
                self.export_infrastructure_to_drawio(infrastructure_spec, f"AAA {diagram_type}", diagram_id)
        
        with col5:
            if st.button("📋 Show Code", key=f"infra_code_{diagram_id}"):
                st.session_state[f"show_infra_code_{diagram_id}"] = not st.session_state.get(f"show_infra_code_{diagram_id}", False)
        
        # Get redraw counter to force diagram regeneration
        infra_redraw_count = st.session_state.get(f"infra_redraw_count_{diagram_id}", 0)
        
        # Try to generate and display the infrastructure diagram
        from app.utils.imports import optional_service
        infrastructure_diagram_service = optional_service('infrastructure_diagram_service', context='infrastructure diagram generation')
        
        if infrastructure_diagram_service:
            
            # Create temporary file for the diagram with redraw counter to ensure uniqueness
            with tempfile.NamedTemporaryFile(suffix=f'_{infra_redraw_count}.png', delete=False) as tmp_file:
                temp_path = tmp_file.name[:-4]  # Remove .png extension
            
            try:
                # Generate the diagram
                diagram_path, python_code = infrastructure_diagram_service.generate_diagram(
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
                error_str = str(e).lower()
                if any(keyword in error_str for keyword in ['dot', 'graphviz', 'windowspath']):
                    st.error("🔧 **Graphviz Required for Infrastructure Diagrams**")
                    st.markdown("""
                    Infrastructure diagrams require **Graphviz** to be installed on your system.
                    
                    **📥 Installation Instructions:**
                    
                    **Windows:**
                    ```powershell
                    # Option 1: Using Chocolatey (recommended)
                    choco install graphviz
                    
                    # Option 2: Using winget
                    winget install graphviz
                    ```
                    
                    **macOS:**
                    ```bash
                    brew install graphviz
                    ```
                    
                    **Linux (Ubuntu/Debian):**
                    ```bash
                    sudo apt-get install graphviz
                    ```
                    
                    **✅ Verify Installation:**
                    ```bash
                    dot -V
                    ```
                    
                    After installation, restart the application to use infrastructure diagrams.
                    """)
                    
                    st.info("💡 **Alternative:** Use other diagram types (Context, Container, Sequence, C4) which don't require Graphviz.")
                    
                else:
                    st.error(f"Error generating infrastructure diagram: {str(e)}")
                
                st.write("**📋 Diagram Specification (JSON):**")
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
                            
        else:
            st.warning("""
            **Infrastructure Diagrams Not Available**
            
            The infrastructure diagram service is not registered. This may be due to missing dependencies.
            
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
        from app.utils.imports import optional_service
        infrastructure_diagram_service = optional_service('infrastructure_diagram_service', context='infrastructure diagram download')
        
        if infrastructure_diagram_service:
            try:
                # Create exports directory with absolute path
                current_dir = os.getcwd()
                exports_dir = os.path.join(current_dir, "exports")
                os.makedirs(exports_dir, exist_ok=True)
                st.info(f"📁 Created exports directory: {exports_dir}")
                
                output_path = os.path.join(exports_dir, f"infrastructure_diagram_{diagram_id}")
                
                # Generate PNG first
                try:
                    png_path, python_code = infrastructure_diagram_service.generate_diagram(
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
                    svg_path, _ = infrastructure_diagram_service.generate_diagram(
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
        else:
            st.error("❌ Infrastructure diagram service not available. Cannot generate diagrams.")
            st.info("💡 The infrastructure diagram generator service is not registered.")
    
    def render_observability_dashboard(self):
        """Render the observability dashboard with metrics and analytics."""
        st.header("📈 System Observability")
        
        # Show info message if no session is active
        if not st.session_state.session_id:
            st.info("💡 Start an analysis in the Analysis tab to see observability data here.")
            return
        
        # Enhanced dashboard tabs with monitoring
        metrics_tab, monitoring_tab, patterns_tab, usage_tab, messages_tab, admin_tab = st.tabs([
            "🔧 Provider Metrics", 
            "🔍 System Monitoring", 
            "🎯 Pattern Analytics", 
            "📊 Usage Patterns", 
            "💬 LLM Messages", 
            "🧹 Admin"
        ])
        
        with metrics_tab:
            self.render_provider_metrics()
        
        with monitoring_tab:
            self.render_tech_stack_monitoring()
        
        with patterns_tab:
            self.render_pattern_analytics()
        
        with usage_tab:
            self.render_usage_patterns()
        
        with messages_tab:
            self.render_llm_messages()
        
        with admin_tab:
            self.render_observability_admin()
    
    def render_user_feedback_section(self):
        """Render user feedback section for monitoring data collection."""
        if st.session_state.get('recommendations'):
            st.subheader("📝 Rate This Analysis")
            st.write("Help us improve by rating this tech stack analysis:")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                relevance = st.slider("Relevance", 1, 5, 3, help="How relevant are the recommendations?")
            
            with col2:
                accuracy = st.slider("Accuracy", 1, 5, 3, help="How accurate are the technology selections?")
            
            with col3:
                completeness = st.slider("Completeness", 1, 5, 3, help="How complete is the recommended stack?")
            
            feedback_text = st.text_area("Additional Feedback (Optional)", placeholder="Any specific comments about the recommendations...")
            
            if st.button("📊 Submit Feedback"):
                self._record_user_feedback(
                    session_id=st.session_state.get('session_id', 'unknown'),
                    relevance_score=float(relevance),
                    accuracy_score=float(accuracy),
                    completeness_score=float(completeness),
                    feedback_text=feedback_text if feedback_text.strip() else None
                )
                st.success("✅ Thank you for your feedback!")
                st.rerun()
    
    def _record_user_feedback(
        self,
        session_id: str,
        relevance_score: float,
        accuracy_score: float,
        completeness_score: float,
        feedback_text: Optional[str] = None
    ) -> None:
        """Record user feedback for monitoring."""
        try:
            # Get monitoring service
            if 'monitoring_service' not in st.session_state:
                from app.monitoring.integration_service import MonitoringIntegrationService
                st.session_state.monitoring_service = MonitoringIntegrationService()
            
            monitoring_service = st.session_state.monitoring_service
            
            # Record user feedback
            import asyncio
            asyncio.create_task(monitoring_service.record_user_feedback(
                session_id=session_id,
                relevance_score=relevance_score,
                accuracy_score=accuracy_score,
                completeness_score=completeness_score,
                feedback_text=feedback_text
            ))
            
            # Store feedback in session state for immediate display
            st.session_state.user_feedback = {
                'relevance': relevance_score,
                'accuracy': accuracy_score,
                'completeness': completeness_score,
                'feedback': feedback_text,
                'timestamp': time.time()
            }
            
        except Exception as e:
            from app.utils.logger import app_logger
            app_logger.warning(f"Failed to record user feedback: {e}")
    
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
                    
                    # Provide helpful debugging information
                    with st.expander("🔍 Troubleshooting Pattern Analytics"):
                        st.write("**Why might this happen?**")
                        st.write("• You haven't completed an analysis in this session yet")
                        st.write("• The analysis failed before pattern matching occurred")
                        st.write("• You're viewing a different session than the one you analyzed")
                        
                        st.write("**To see pattern analytics:**")
                        st.write("1. Go to the **Analysis** tab")
                        st.write("2. Complete a full analysis (requirements → Q&A → recommendations)")
                        st.write("3. Return to this **Observability** tab")
                        st.write("4. Select **Current Session Only** to see your session's pattern matches")
                        
                        # Show current session info and diagnostic button
                        if current_session_id:
                            st.write(f"**Current Session ID:** `{current_session_id[:8]}...`")
                            
                            if st.button("🔍 Check Current Session Data", key="check_session_data"):
                                from app.utils.imports import optional_service
                                audit_logger = optional_service('audit_logger', context='session data check')
                                
                                if audit_logger:
                                    try:
                                        import sqlite3
                                        redacted_session = audit_logger._redact_session_id(current_session_id)
                                        
                                        with sqlite3.connect(audit_logger.db_path) as conn:
                                            # Check for pattern matches
                                            cursor = conn.execute("""
                                                SELECT pattern_id, score, accepted, created_at 
                                                FROM matches 
                                                WHERE session_id = ? 
                                                ORDER BY created_at DESC
                                            """, [redacted_session])
                                            matches = cursor.fetchall()
                                            
                                            # Check for LLM calls
                                            cursor = conn.execute("""
                                                SELECT provider, model, purpose, created_at 
                                                FROM runs 
                                                WHERE session_id = ? 
                                                ORDER BY created_at DESC 
                                                LIMIT 5
                                            """, [redacted_session])
                                            llm_calls = cursor.fetchall()
                                            
                                            if matches:
                                                st.success(f"✅ Found {len(matches)} pattern matches for this session:")
                                                for match in matches:
                                                    st.write(f"• **{match[0]}** (score: {match[1]:.3f}) at {match[3][:19]}")
                                                
                                                # Check if there's a discrepancy with what's shown on Analysis page
                                                pattern_ids = [match[0] for match in matches]
                                                if len(set(pattern_ids)) > 1:
                                                    st.info("ℹ️ **Multiple patterns matched**: This session has matches for different patterns, which may indicate multiple analyses or pattern updates.")
                                                
                                                # Show most recent pattern
                                                most_recent_pattern = matches[0][0]
                                                st.write(f"🎯 **Most recent pattern match**: {most_recent_pattern}")
                                            else:
                                                st.warning("❌ No pattern matches found for this session")
                                                
                                            if llm_calls:
                                                st.info(f"📡 Found {len(llm_calls)} recent LLM calls for this session:")
                                                for call in llm_calls[:3]:  # Show first 3
                                                    purpose = call[2] or "general"
                                                    st.write(f"• {call[0]} {call[1]} ({purpose}) at {call[3][:19]}")
                                            else:
                                                st.warning("❌ No LLM calls found for this session")
                                                
                                            if not matches and not llm_calls:
                                                st.error("🚨 This session has no recorded activity. You may need to complete an analysis first.")
                                            
                                    except Exception as e:
                                        st.error(f"Error checking session data: {str(e)}")
                        
                        # Show if there are any recent sessions with data
                        from app.utils.imports import optional_service
                        audit_logger = optional_service('audit_logger', context='recent sessions check')
                        
                        if audit_logger:
                            try:
                                import sqlite3
                                with sqlite3.connect(audit_logger.db_path) as conn:
                                    cursor = conn.execute("""
                                        SELECT session_id, COUNT(*) as match_count, MAX(created_at) as last_match
                                        FROM matches 
                                        WHERE created_at >= datetime('now', '-24 hours')
                                        GROUP BY session_id 
                                        ORDER BY last_match DESC 
                                        LIMIT 3
                                    """)
                                    recent_sessions = cursor.fetchall()
                                    
                                    if recent_sessions:
                                        st.write("**Recent sessions with pattern matches (last 24 hours):**")
                                        for session in recent_sessions:
                                            session_display = session[0][:8] + "..." if len(session[0]) > 8 else session[0]
                                            st.write(f"• Session `{session_display}`: {session[1]} matches (last: {session[2][:19]})")
                                        st.write("💡 Try selecting **Last 24 Hours** to see data from recent sessions")
                            except Exception as e:
                                st.write(f"Could not check recent sessions: {str(e)}")
                else:
                    st.info("No pattern analytics available yet. Run some analyses to see pattern matching data.")
                    
                    with st.expander("🔍 Getting Started with Pattern Analytics"):
                        st.write("**Pattern Analytics shows:**")
                        st.write("• How often each solution pattern is recommended")
                        st.write("• Average matching confidence scores")
                        st.write("• Pattern acceptance rates")
                        st.write("• Usage trends over time")
                        
                        st.write("**To generate analytics data:**")
                        st.write("1. Go to the **Analysis** tab")
                        st.write("2. Submit requirements for analysis")
                        st.write("3. Complete the Q&A process")
                        st.write("4. Review the generated recommendations")
                        st.write("5. Return here to see which patterns were matched")
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
                from app.utils.imports import optional_service
                pattern_loader = optional_service('pattern_loader', context='pattern library health')
                
                if pattern_loader:
                    try:
                        from pathlib import Path
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
        from app.utils.imports import optional_service
        audit_logger = optional_service('audit_logger', context='LLM messages fetch')
        
        if audit_logger:
            try:
                return audit_logger.get_llm_messages(
                    session_id=st.session_state.session_id if hasattr(st.session_state, 'session_id') else None,
                    limit=100
                )
            except Exception as e:
                st.error(f"Error fetching LLM messages: {str(e)}")
                return []
        else:
            return []
    
    async def get_provider_statistics(self, 
                                    time_filter: str = "All Time",
                                    include_test_providers: bool = False,
                                    current_session_only: bool = False) -> Dict[str, Any]:
        """Fetch provider statistics from audit system with filtering options."""
        from app.utils.imports import optional_service
        audit_logger = optional_service('audit_logger', context='provider metrics')
        
        if audit_logger:
            try:
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
        else:
            return {}
    
    async def get_pattern_statistics(self, session_filter: str = None, time_filter: str = "All Time") -> Dict[str, Any]:
        """Fetch pattern statistics from audit system with filtering options.
        
        Args:
            session_filter: Filter by specific session ID
            time_filter: Time period filter
            
        Returns:
            Pattern statistics dictionary
        """
        from app.utils.imports import optional_service
        audit_logger = optional_service('audit_logger', context='usage patterns')
        
        if audit_logger:
            try:
                import sqlite3
                from datetime import datetime, timedelta
                
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
        else:
            return {}
    
    def render_tech_stack_monitoring(self):
        """Render the comprehensive system monitoring dashboard with real-time metrics."""
        st.subheader("🔍 System Performance Monitoring")
        
        try:
            # Try to import and initialize monitoring services (without dashboard dependencies)
            from app.monitoring.integration_service import MonitoringIntegrationService
            from app.monitoring.simple_dashboard import render_simple_monitoring_dashboard
            
            # Initialize monitoring integration service
            if 'monitoring_service' not in st.session_state:
                st.session_state.monitoring_service = MonitoringIntegrationService()
            
            monitoring_service = st.session_state.monitoring_service
            
            # Render the simple monitoring dashboard
            render_simple_monitoring_dashboard(monitoring_service)
            
        except ImportError as e:
            st.error("🚫 Monitoring system not available. Please ensure monitoring components are properly installed.")
            st.info("The monitoring system requires additional dependencies. Please check the installation guide.")
            st.code(f"Import error: {e}")
            
            # Show basic monitoring info
            st.subheader("📊 Basic Monitoring Information")
            st.info("""
            The monitoring system provides:
            - Real-time technology extraction accuracy tracking
            - Automated alerting for catalog inconsistencies
            - User satisfaction tracking for tech stack relevance
            - Quality metrics dashboard for system performance
            - Automated quality assurance checks and reporting
            - Performance optimization recommendations
            
            To enable full monitoring, ensure all monitoring components are installed.
            """)
        
        except Exception as e:
            st.error(f"🚫 Error initializing monitoring dashboard: {e}")
            st.info("Please check the system logs for more details.")
            
            # Show fallback monitoring info
            st.subheader("📊 Monitoring System Overview")
            st.info("""
            The monitoring system is designed to provide:
            
            **Real-time Monitoring:**
            - Technology extraction accuracy tracking
            - Processing time monitoring
            - User satisfaction metrics
            
            **Automated Alerting:**
            - Catalog inconsistency detection
            - Missing technology alerts
            - Performance degradation warnings
            
            **Quality Assurance:**
            - Automated quality checks
            - Comprehensive system audits
            - Performance optimization recommendations
            
            **Dashboard Features:**
            - Live system health indicators
            - Alert management interface
            - Performance recommendations
            - Quality assurance reports
            
            To resolve this issue, please check the system configuration and ensure
            all monitoring dependencies are properly installed.
            """)

    def render_observability_admin(self):
        """Render observability administration tools."""
        st.subheader("🧹 Observability Administration")
        
        st.write("**Database Management**")
        
        # Show database statistics
        from app.utils.imports import optional_service
        audit_logger = optional_service('audit_logger', context='database statistics')
        
        if audit_logger:
            try:
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
                            import json
                            stats = audit_logger.get_provider_stats(include_test_providers=True)
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
        else:
            st.error("❌ Audit logger service not available.")
    
    def render_unified_pattern_management(self):
        """Render the unified pattern management interface."""
        st.header("📚 Pattern Library Management")
        
        # Color legend and quick navigation
        col1, col2 = st.columns([3, 1])
        with col1:
            st.markdown("""
            **🎨 Pattern Color Guide:**
            🔴 Not Automatable / Manual processes  •  🟡 Partially Automatable / Traditional automation  •  🟢 Fully Automatable / AI-enhanced  •  🔵 Autonomous Agentic AI
            """)
        with col2:
            st.markdown("""
            **🚀 Quick Actions:**
            • View & filter patterns
            • Enhance with AI
            • Analyze usage trends
            """)
        
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
            
            ### 🎨 **Pattern Categories by Color:**
            
            - **🔵 Blue (APAT-*)**: Autonomous Agentic AI patterns - fully autonomous agents that operate independently with 95%+ automation
            - **🟢 Green (PAT-*)**: Fully Automatable AI-enhanced solutions - can be completely automated with high confidence
            - **🟡 Yellow (PAT-*)**: Partially Automatable traditional automation - requires some human oversight or approval steps
            - **🔴 Red (PAT-*)**: Not Automatable manual processes - primarily human-driven with AI assistance
            
            ### 🏷️ **Pattern Components Explained:**
            
            - **Pattern ID**: Unique identifier (PAT-001 for traditional, APAT-001 for autonomous agents)
            - **Name**: Descriptive title of the automation pattern
            - **Description**: Detailed explanation of what the pattern automates
            - **Domain**: Business area (e.g., legal_compliance, finance, customer_service)
            - **Feasibility**: Automation potential (Fully Automatable, Partially Automatable, Not Automatable)
            - **Pattern Types**: Tags/categories describing the automation approach
            - **Tech Stack**: Technologies typically used to implement this pattern
            - **Complexity**: Implementation difficulty (Low, Medium, High)
            - **Estimated Effort**: Time required to implement (e.g., 2-4 weeks)
            - **Confidence Score**: How reliable this pattern is (0.0 to 1.0)
            
            ### 🎯 **How Patterns Are Used:**
            When you submit a requirement, the system:
            1. Matches your requirement against these patterns using AI similarity matching
            2. Suggests the most relevant automation approaches (traditional → AI-enhanced → autonomous)
            3. Provides technology recommendations based on proven solutions
            4. Estimates feasibility and generates implementation guidance
            
            ### 💡 **Common Pattern Types (Tags):**
            - **Autonomous Agents**: `agentic_reasoning`, `autonomous_decision`, `continuous_learning`
            - **AI Processing**: `nlp_processing`, `summarization`, `pii_detection`, `analysis`
            - **Integration**: `api_integration`, `data_extraction`, `workflow_automation`
            - **Human Oversight**: `human_in_loop`, `approval_workflow`, `manual_review`
            - **Security**: `pii_redaction`, `policy_enforcement`, `security_validation`
            """)
        
        # Load patterns using the pattern loader
        from app.utils.imports import optional_service
        pattern_loader = optional_service('pattern_loader', context='pattern management')
        patterns = []  # Initialize patterns as empty list
        
        if pattern_loader:
            try:
                # Auto-refresh cache when Pattern Library tab is opened to ensure we see current patterns
                # This prevents showing deleted patterns that are cached
                pattern_loader.refresh_cache()
                patterns = pattern_loader.load_patterns()
            except Exception as e:
                st.error(f"❌ Error loading patterns: {str(e)}")
                return
        else:
            st.warning("⚠️ Pattern loader service not available. Pattern management features will be limited.")
        
        # Unified management tabs - all pattern functionality in one place
        view_tab, edit_tab, create_tab, enhance_tab, analytics_tab = st.tabs([
            "👀 View Patterns", 
            "✏️ Edit Pattern", 
            "➕ Create Pattern", 
            "🚀 Enhance Patterns",
            "📊 Pattern Analytics"
        ])
        
        with view_tab:
            self.render_pattern_viewer(patterns)
        
        with edit_tab:
            self.render_pattern_editor(patterns, pattern_loader)
        
        with create_tab:
            self.render_pattern_creator(pattern_loader)
            
        with enhance_tab:
            self.render_pattern_enhancement_tab()
            
        with analytics_tab:
            self.render_pattern_analytics_tab()
    
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
            # Count both "Automatable" and "Fully Automatable" patterns
            fully_auto = len([p for p in patterns if p.get('feasibility') in ['Automatable', 'Fully Automatable']])
            st.metric("Fully Automatable", fully_auto)
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
            # Use the new color field if available, otherwise fall back to feasibility color
            pattern_color = pattern.get('color')
            if not pattern_color:
                # Fallback to feasibility-based color for patterns without color field
                pattern_id = pattern.get('pattern_id', '')
                feasibility = pattern.get('feasibility', 'Unknown')
                
                # APAT patterns get blue
                if pattern_id.startswith('APAT-'):
                    pattern_color = '🔵'
                else:
                    pattern_color = {
                        'Automatable': '🟢',
                        'Partially Automatable': '🟡', 
                        'Not Automatable': '🔴',
                        'Fully Automatable': '🟢'
                    }.get(feasibility, '🟡')
            
            pattern_id = pattern.get('pattern_id', 'Unknown')
            pattern_header = f"{pattern_color} {pattern_id} - {pattern.get('name', 'Unnamed Pattern')}"
            
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
                    feasibility = pattern.get('feasibility', 'Unknown')
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
                # Support both traditional and agentic feasibility values
                feasibility_options = ["Automatable", "Fully Automatable", "Partially Automatable", "Not Automatable"]
                current_feasibility = selected_pattern.get('feasibility', 'Automatable')
                
                # Handle legacy values
                if current_feasibility not in feasibility_options:
                    if current_feasibility == "Yes":
                        current_feasibility = "Automatable"
                    elif current_feasibility == "Partial":
                        current_feasibility = "Partially Automatable"
                    elif current_feasibility == "No":
                        current_feasibility = "Not Automatable"
                
                feasibility = st.selectbox("Feasibility", 
                                         feasibility_options,
                                         index=feasibility_options.index(current_feasibility))
            
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
        
        # Pattern type selection
        pattern_category = st.radio(
            "Pattern Category:",
            ["Traditional Pattern (PAT-*)", "Agentic Pattern (APAT-*)"],
            help="Traditional patterns focus on standard automation. Agentic patterns emphasize autonomous AI agents with reasoning capabilities."
        )
        
        # Adjust pattern ID based on selection
        if pattern_category.startswith("Agentic"):
            # Generate APAT ID
            agentic_numbers = []
            for pid in existing_ids:
                if pid.startswith('APAT-'):
                    try:
                        agentic_numbers.append(int(pid.split('-')[1]))
                    except (IndexError, ValueError):
                        continue
            next_agentic_number = max(agentic_numbers) + 1 if agentic_numbers else 1
            display_pattern_id = f"APAT-{next_agentic_number:03d}"

        else:
            display_pattern_id = next_pattern_id

        with st.form(key="create_pattern_form"):
            st.write(f"**Creating New Pattern: {display_pattern_id}**")
            
            # Basic information
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("Pattern Name", placeholder="Enter pattern name")
                domain = st.text_input("Domain", placeholder="e.g., legal_compliance, finance")
                feasibility = st.selectbox("Feasibility", ["Automatable", "Fully Automatable", "Partially Automatable", "Not Automatable"])
            
            with col2:
                complexity = st.selectbox("Complexity", ["Low", "Medium", "High"])
                estimated_effort = st.text_input("Estimated Effort", placeholder="e.g., 2-4 weeks")
                confidence_score = st.number_input("Confidence Score", min_value=0.0, max_value=1.0, value=0.5, step=0.01)
            
            # Description
            description = st.text_area("Description", placeholder="Describe what this pattern does and when to use it", height=100)
            
            # Agentic-specific fields
            if pattern_category.startswith("Agentic"):
                st.write("### 🤖 Agentic Capabilities")
                
                col3, col4 = st.columns(2)
                with col3:
                    autonomy_level = st.number_input("Autonomy Level", min_value=0.0, max_value=1.0, value=0.8, step=0.01,
                                                   help="Level of autonomous operation (0.0 = fully human-dependent, 1.0 = fully autonomous)")
                    agent_architecture = st.selectbox("Agent Architecture", 
                                                    ["single_agent", "multi_agent_collaborative", "hierarchical_agents", "swarm_intelligence"])
                
                with col4:
                    decision_authority = st.selectbox("Decision Authority Level", ["low", "medium", "high", "full"])
                    
                reasoning_types = st.multiselect("Reasoning Types", 
                                               ["logical", "causal", "temporal", "spatial", "analogical", "case_based", "probabilistic", "strategic"],
                                               default=["logical", "causal"])
                
                agentic_frameworks = st.multiselect("Agentic Frameworks",
                                                  ["LangChain", "AutoGPT", "CrewAI", "Microsoft Semantic Kernel", "OpenAI Assistants API", "LlamaIndex"],
                                                  default=["LangChain"])
                
                learning_mechanisms = st.multiselect("Learning Mechanisms",
                                                   ["feedback_incorporation", "pattern_recognition", "performance_optimization", "strategy_adaptation", "continuous_improvement"],
                                                   default=["feedback_incorporation", "performance_optimization"])
            
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
                    pattern_data = {
                        'pattern_id': display_pattern_id,
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
                    }
                    
                    # Add agentic-specific fields if creating an agentic pattern
                    if pattern_category.startswith("Agentic"):
                        pattern_data.update({
                            'autonomy_level': autonomy_level,
                            'reasoning_types': reasoning_types,
                            'decision_boundaries': {
                                'decision_authority_level': decision_authority,
                                'autonomous_decisions': [],
                                'escalation_triggers': []
                            },
                            'exception_handling_strategy': {
                                'autonomous_resolution_approaches': [],
                                'reasoning_fallbacks': [],
                                'escalation_criteria': []
                            },
                            'learning_mechanisms': learning_mechanisms,
                            'self_monitoring_capabilities': [],
                            'agent_architecture': agent_architecture,
                            'coordination_requirements': None,
                            'agentic_frameworks': agentic_frameworks,
                            'reasoning_engines': []
                        })
                    
                    self.create_new_pattern(pattern_data, pattern_loader)
    
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
    
    def render_pattern_enhancement_tab(self):
        """Render the pattern enhancement functionality."""
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='pattern enhancement')
        analytics_service = optional_service('pattern_analytics_service', context='pattern enhancement')
        
        if enhanced_loader:
            from app.ui.enhanced_pattern_management import render_pattern_overview, render_pattern_analytics
            
            # Show success message
            st.success("✅ Pattern enhancement available: Enhanced pattern system services are registered.")
            
            # Create tabs for different pattern management functions
            overview_tab, analytics_tab = st.tabs(["📊 Pattern Overview", "📈 Pattern Analytics"])
            
            with overview_tab:
                render_pattern_overview(enhanced_loader)
            
            with analytics_tab:
                render_pattern_analytics(enhanced_loader)
            
            # Show additional information about available features
            with st.expander("ℹ️ Available Pattern Enhancement Features"):
                st.markdown("""
                **Enhanced Pattern Management Features:**
                - 📊 **Pattern Overview**: Comprehensive statistics and capability matrix
                - 📈 **Pattern Analytics**: Usage analytics and performance insights
                - 🔍 **Pattern Search**: Advanced search and filtering capabilities
                - 📋 **Pattern Comparison**: Side-by-side pattern comparison
                - 💾 **Pattern Export**: Export patterns in multiple formats
                
                **Enhanced Pattern Loader Capabilities:**
                - ✅ Real-time analytics and performance tracking
                - ✅ Enhanced caching for improved performance
                - ✅ Comprehensive pattern validation
                - ✅ Usage statistics and monitoring
                - ✅ Health checks and status reporting
                """)
            
        else:
            # Use our utility function for dynamic status checking
            from app.utils.pattern_status_utils import get_pattern_enhancement_error_or_success
            status_msg = get_pattern_enhancement_error_or_success()
            
            if status_msg.startswith("✅"):
                st.success(status_msg)
                # If service is available but we couldn't get it, show debug info
                st.warning("⚠️ Enhanced pattern loader service appears to be available but couldn't be accessed. Please check service registration.")
            else:
                st.info(status_msg)
        
        # Handle any exceptions during enhancement
        try:
            pass  # Enhancement logic is now in the if block above
        except Exception as e:
            st.error(f"❌ Error loading pattern enhancement: {e}")
            app_logger.error(f"Pattern enhancement error: {e}")
    
    def render_pattern_analytics_tab(self):
        """Render the pattern analytics functionality."""
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='pattern analytics')
        
        if enhanced_loader:
            from app.ui.enhanced_pattern_management import render_pattern_analytics
            
            # Enhanced pattern loader is already available from service registry
            
            # Render the pattern analytics UI
            render_pattern_analytics(enhanced_loader)
            
        else:
            st.error("❌ Pattern analytics not available: Enhanced pattern loader service not registered.")
            st.info("💡 This feature requires the enhanced pattern system services to be registered.")
        
        # Handle any exceptions during analytics
        try:
            pass  # Analytics logic is now in the if block above
        except Exception as e:
            st.error(f"❌ Error loading pattern analytics: {e}")
            app_logger.error(f"Pattern analytics error: {e}")
    
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
                                st.write(f"  Description: {tech_info.get('description', 'No description')}")
                            
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
        tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8 = st.tabs(["📝 Analysis", "📊 Diagrams", "📈 Observability", "📚 Pattern Library", "� Technology Catalog", "⚙️ Schema Config", "🔧 System Config", "ℹ️ About"])
        
        with tab1:
            # Input methods
            if not st.session_state.session_id:
                self.render_input_methods()
            
            # Progress tracking and results
            if st.session_state.session_id:
                self.render_progress_tracking()
                
                # Session information and actions
                st.divider()
                
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.markdown("**Current Session Information:**")
                    st.code(f"Session ID: {st.session_state.session_id}", language=None)
                    st.caption("💡 Save this Session ID to resume this analysis later")
                    
                    # Debug: Show current session constraints if available
                    if hasattr(st.session_state, 'requirements') and st.session_state.requirements:
                        constraints = st.session_state.requirements.get('constraints', {})
                        if constraints:
                            with st.expander("🔍 Debug: Current Session Constraints"):
                                st.json(constraints)
                
                with col2:
                    # Copy to clipboard button with fallback
                    if st.button("📋 Copy Session ID"):
                        # Use JavaScript with better error handling and fallback
                        copy_js = f"""
                        <script>
                        function copyToClipboard() {{
                            const sessionId = '{st.session_state.session_id}';
                            
                            if (navigator.clipboard && window.isSecureContext) {{
                                // Use modern clipboard API
                                navigator.clipboard.writeText(sessionId).then(function() {{
                                    console.log('Session ID copied to clipboard successfully');
                                    window.parent.postMessage({{type: 'copy_success'}}, '*');
                                }}).catch(function(err) {{
                                    console.error('Failed to copy: ', err);
                                    window.parent.postMessage({{type: 'copy_failed'}}, '*');
                                }});
                            }} else {{
                                // Fallback for older browsers or non-secure contexts
                                const textArea = document.createElement('textarea');
                                textArea.value = sessionId;
                                document.body.appendChild(textArea);
                                textArea.select();
                                try {{
                                    document.execCommand('copy');
                                    console.log('Session ID copied using fallback method');
                                    window.parent.postMessage({{type: 'copy_success'}}, '*');
                                }} catch (err) {{
                                    console.error('Fallback copy failed: ', err);
                                    window.parent.postMessage({{type: 'copy_failed'}}, '*');
                                }}
                                document.body.removeChild(textArea);
                            }}
                        }}
                        copyToClipboard();
                        </script>
                        """
                        st.components.v1.html(copy_js, height=0)
                        
                        # Show manual copy option as primary method
                        st.info("💡 **Manual Copy Recommended**: Select and copy the Session ID above")
                        st.caption("Note: Automatic clipboard copying may not work in all browsers. If the copy button doesn't work, please manually select and copy the Session ID displayed above.")
                
                # Reset button
                if st.button("🔄 Start New Analysis", key="start_new_analysis_main"):
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
            self.render_unified_pattern_management()
        
        with tab5:
            self.render_technology_catalog_management()
        
        with tab6:
            from app.ui.schema_management import render_schema_management
            render_schema_management()
        
        with tab7:
            # System Configuration
            from app.ui.system_configuration import render_system_configuration
            render_system_configuration()
        
        with tab8:
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
            - 📊 **Feasibility Assessment**: Automatable, Fully Automatable, Partially Automatable, or Not Automatable
            - 📈 **AI-Generated Architecture Diagrams**: Context, Container, and Sequence diagrams
            - 📤 **Multi-Format Export**: JSON, Markdown, and interactive HTML
            - 🎯 **Constraint-Aware**: Filters banned tools and applies business constraints
            
            ### 🆕 Advanced Features:
            - 📚 **Unified Pattern Management**: Complete CRUD interface with pattern enhancement, analytics, and comparison tools
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
            
            ### 📚 Unified Pattern Management:
            Complete pattern lifecycle management in one place - view, edit, create, enhance, and analyze patterns with integrated analytics.
            
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


