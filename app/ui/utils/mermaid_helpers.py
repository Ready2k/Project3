"""Mermaid diagram utility functions."""

import re
import uuid
import base64
from typing import Dict, List, Optional, Any, Tuple

# Import logger for error handling
from app.utils.logger import app_logger


def clean_mermaid_code(code: str) -> str:
    """Clean and prepare Mermaid code for rendering."""
    if not code:
        return ""
    
    # Remove markdown code blocks if present
    cleaned = code.strip()
    if cleaned.startswith('```mermaid'):
        cleaned = cleaned.replace('```mermaid', '').replace('```', '').strip()
    elif cleaned.startswith('```'):
        cleaned = cleaned.replace('```', '').strip()
    
    # Extract actual Mermaid code from mixed responses
    cleaned = extract_mermaid_code(cleaned)
    
    # Remove problematic characters
    cleaned = sanitize_mermaid_code(cleaned)
    
    return cleaned


def extract_mermaid_code(text: str) -> str:
    """Extract Mermaid code from mixed LLM responses."""
    if not text:
        return ""
    
    # Try to find Mermaid code blocks first
    mermaid_block_pattern = r'```mermaid\s*(.*?)\s*```'
    match = re.search(mermaid_block_pattern, text, re.DOTALL | re.IGNORECASE)
    if match:
        return match.group(1).strip()
    
    # Try to find generic code blocks that might contain Mermaid
    code_block_pattern = r'```\s*(.*?)\s*```'
    match = re.search(code_block_pattern, text, re.DOTALL)
    if match:
        potential_code = match.group(1).strip()
        if looks_like_mermaid_code(potential_code):
            return potential_code
    
    # Look for Mermaid diagram declarations
    diagram_types = [
        'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
        'stateDiagram', 'erDiagram', 'journey', 'gantt',
        'pie', 'gitgraph', 'C4Context', 'C4Container', 'C4Component'
    ]
    
    lines = text.split('\n')
    mermaid_lines = []
    in_diagram = False
    
    for line in lines:
        line_stripped = line.strip()
        
        # Check if line starts a diagram
        if any(line_stripped.lower().startswith(dt.lower()) for dt in diagram_types):
            in_diagram = True
            mermaid_lines = [line_stripped]
        elif in_diagram:
            # Continue collecting lines until we hit explanatory text
            if (line_stripped and 
                not line_stripped.lower().startswith(('this diagram', 'the diagram', 'here', 'note:', 'explanation:')) and
                not re.match(r'^[a-zA-Z\s]+:$', line_stripped)):  # Avoid section headers
                mermaid_lines.append(line_stripped)
            elif line_stripped == "":
                # Empty line might be part of diagram
                mermaid_lines.append(line_stripped)
            else:
                # Hit explanatory text, stop collecting
                break
    
    if mermaid_lines:
        potential_code = '\n'.join(mermaid_lines).strip()
        if looks_like_mermaid_code(potential_code):
            return potential_code
    
    # If no clear Mermaid code found, return original text
    return text.strip()


def looks_like_mermaid_code(code: str) -> bool:
    """Check if code looks like valid Mermaid syntax."""
    if not code:
        return False
    
    # Check for basic Mermaid diagram types
    diagram_types = [
        'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
        'stateDiagram', 'erDiagram', 'journey', 'gantt',
        'pie', 'gitgraph', 'C4Context', 'C4Container', 'C4Component'
    ]
    
    first_line = code.split('\n')[0].strip().lower()
    
    # Check if it starts with a known diagram type
    for diagram_type in diagram_types:
        if first_line.startswith(diagram_type.lower()):
            return True
    
    # Check for common Mermaid syntax patterns
    mermaid_patterns = [
        r'-->', r'--->', r'-\.->', r'==>', r'-.->',  # Arrows
        r'\[\[.*\]\]', r'\[.*\]', r'\(.*\)', r'\{.*\}',  # Node shapes
        r'participant\s+\w+', r'activate\s+\w+',  # Sequence diagram
        r'class\s+\w+', r'<<.*>>',  # Class diagram
        r'state\s+\w+', r'\[\*\]',  # State diagram
    ]
    
    for pattern in mermaid_patterns:
        if re.search(pattern, code, re.IGNORECASE):
            return True
    
    return False


def sanitize_mermaid_code(code: str) -> str:
    """Sanitize Mermaid code for safe rendering."""
    if not code:
        return ""
    
    # Replace common problematic characters
    replacements = {
        '👤': 'User',
        '🤖': 'Agent',
        '💾': 'Database',
        '🌐': 'Web',
        '📱': 'Mobile',
        '🔒': 'Security',
        '⚡': 'Fast',
        '🔄': 'Process',
        '📊': 'Analytics',
        '🎯': 'Target',
        '🚀': 'Launch',
        '⭐': 'Star',
        '✅': 'Success',
        '❌': 'Error',
        '⚠️': 'Warning',
        '💡': 'Idea',
        '🔧': 'Tool',
        '📈': 'Growth',
        '🏗️': 'Build',
        '🎨': 'Design'
    }
    
    for emoji, replacement in replacements.items():
        code = code.replace(emoji, replacement)
    
    # Remove other problematic Unicode characters
    code = re.sub(r'[^\x00-\x7F]+', '', code)
    
    # Clean up node labels to be Mermaid-safe
    code = sanitize_node_labels(code)
    
    return code


def sanitize_node_labels(code: str) -> str:
    """Sanitize node labels in Mermaid code."""
    if not code:
        return ""
    
    # Pattern to match node definitions with labels
    node_patterns = [
        r'(\w+)\[([^\]]+)\]',  # node[label]
        r'(\w+)\(([^)]+)\)',   # node(label)
        r'(\w+)\{([^}]+)\}',   # node{label}
        r'(\w+)>([^<]+)<',     # node>label<
    ]
    
    for pattern in node_patterns:
        def replace_label(match):
            node_id = match.group(1)
            label = match.group(2)
            
            # Sanitize the label
            sanitized_label = sanitize_label(label)
            
            # Return with appropriate brackets
            if '[' in match.group(0):
                return f'{node_id}[{sanitized_label}]'
            elif '(' in match.group(0):
                return f'{node_id}({sanitized_label})'
            elif '{' in match.group(0):
                return f'{node_id}{{{sanitized_label}}}'
            elif '>' in match.group(0):
                return f'{node_id}>{sanitized_label}<'
            
            return match.group(0)
        
        code = re.sub(pattern, replace_label, code)
    
    return code


def sanitize_label(label: str) -> str:
    """Sanitize a single label for Mermaid compatibility."""
    if not label:
        return 'unknown'
    
    # Keep only safe characters for Mermaid
    allowed = set("abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.:()")
    sanitized = ''.join(ch if ch in allowed else '_' for ch in label)
    
    # Clean up multiple underscores and spaces
    sanitized = re.sub(r'[_\s]+', '_', sanitized).strip('_')
    
    return sanitized or 'unknown'


def validate_mermaid_syntax(code: str) -> Tuple[bool, List[str]]:
    """Validate Mermaid syntax and return validation results."""
    if not code:
        return False, ["Empty diagram code"]
    
    errors = []
    warnings = []
    
    # Check for basic structure
    if not looks_like_mermaid_code(code):
        errors.append("Does not appear to be valid Mermaid code")
        return False, errors
    
    lines = code.split('\n')
    
    # Check first line for diagram type
    first_line = lines[0].strip().lower()
    diagram_types = [
        'graph', 'flowchart', 'sequenceDiagram', 'classDiagram',
        'stateDiagram', 'erDiagram', 'journey', 'gantt',
        'pie', 'gitgraph', 'C4Context', 'C4Container', 'C4Component'
    ]
    
    if not any(first_line.startswith(dt.lower()) for dt in diagram_types):
        errors.append(f"First line should start with a diagram type: {', '.join(diagram_types)}")
    
    # Check for common syntax issues
    for i, line in enumerate(lines, 1):
        line_stripped = line.strip()
        if not line_stripped:
            continue
        
        # Check for unmatched brackets
        brackets = {'[': ']', '(': ')', '{': '}', '<': '>'}
        for open_bracket, close_bracket in brackets.items():
            if line_stripped.count(open_bracket) != line_stripped.count(close_bracket):
                warnings.append(f"Line {i}: Unmatched brackets '{open_bracket}' and '{close_bracket}'")
        
        # Check for problematic characters
        if re.search(r'[^\x00-\x7F]', line_stripped):
            warnings.append(f"Line {i}: Contains non-ASCII characters that may cause rendering issues")
    
    # Return validation results
    is_valid = len(errors) == 0
    all_issues = errors + warnings
    
    return is_valid, all_issues


def generate_mermaid_live_url(code: str) -> str:
    """Generate a URL for Mermaid Live Editor."""
    try:
        cleaned_code = clean_mermaid_code(code)
        encoded_code = base64.b64encode(cleaned_code.encode('utf-8')).decode('utf-8')
        return f"https://mermaid.live/edit#{encoded_code}"
    except Exception as e:
        app_logger.error(f"Failed to generate Mermaid Live URL: {str(e)}")
        return "https://mermaid.live/"


def create_standalone_html(code: str, title: str = "Mermaid Diagram") -> str:
    """Create standalone HTML file for Mermaid diagram."""
    cleaned_code = clean_mermaid_code(code)
    diagram_id = f"mermaid_{uuid.uuid4().hex[:8]}"
    
    html_template = f"""
    <!DOCTYPE html>
    <html>
    <head>
        <title>{title}</title>
        <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
        <style>
            body {{ 
                font-family: Arial, sans-serif; 
                margin: 20px; 
                background-color: #f5f5f5; 
            }}
            .container {{ 
                background: white; 
                padding: 20px; 
                border-radius: 8px; 
                box-shadow: 0 2px 4px rgba(0,0,0,0.1); 
                max-width: 1200px;
                margin: 0 auto;
            }}
            .mermaid {{ 
                text-align: center; 
                margin: 20px 0; 
            }}
            .controls {{ 
                text-align: center; 
                margin: 20px 0; 
            }}
            button {{ 
                margin: 5px; 
                padding: 10px 20px; 
                background: #007bff; 
                color: white; 
                border: none; 
                border-radius: 4px; 
                cursor: pointer; 
                font-size: 14px;
            }}
            button:hover {{ 
                background: #0056b3; 
            }}
            .code-section {{
                margin-top: 30px;
                padding: 20px;
                background: #f8f9fa;
                border-radius: 4px;
                display: none;
            }}
            .code-section.show {{
                display: block;
            }}
            pre {{
                background: #e9ecef;
                padding: 15px;
                border-radius: 4px;
                overflow-x: auto;
                font-family: 'Courier New', monospace;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1>{title}</h1>
            <div class="controls">
                <button onclick="window.print()">🖨️ Print</button>
                <button onclick="downloadSVG()">💾 Download SVG</button>
                <button onclick="copyCode()">📋 Copy Code</button>
                <button onclick="toggleCode()">👁️ View Code</button>
                <button onclick="openMermaidLive()">🔗 Edit Online</button>
            </div>
            <div class="mermaid" id="{diagram_id}">
                {cleaned_code}
            </div>
            <div class="code-section" id="code-section">
                <h3>Diagram Code</h3>
                <pre><code>{cleaned_code}</code></pre>
            </div>
        </div>
        
        <script>
            mermaid.initialize({{
                startOnLoad: true,
                theme: 'default',
                securityLevel: 'loose',
                fontFamily: 'Arial, sans-serif'
            }});
            
            function downloadSVG() {{
                const svg = document.querySelector('#{diagram_id} svg');
                if (svg) {{
                    const svgData = new XMLSerializer().serializeToString(svg);
                    const svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                    const svgUrl = URL.createObjectURL(svgBlob);
                    const downloadLink = document.createElement('a');
                    downloadLink.href = svgUrl;
                    downloadLink.download = '{title.replace(" ", "_")}.svg';
                    document.body.appendChild(downloadLink);
                    downloadLink.click();
                    document.body.removeChild(downloadLink);
                }} else {{
                    alert('SVG not found. Please wait for the diagram to render.');
                }}
            }}
            
            function copyCode() {{
                const code = `{cleaned_code}`;
                navigator.clipboard.writeText(code).then(() => {{
                    alert('Diagram code copied to clipboard!');
                }}).catch(() => {{
                    // Fallback for older browsers
                    const textArea = document.createElement('textarea');
                    textArea.value = code;
                    document.body.appendChild(textArea);
                    textArea.select();
                    document.execCommand('copy');
                    document.body.removeChild(textArea);
                    alert('Diagram code copied to clipboard!');
                }});
            }}
            
            function toggleCode() {{
                const codeSection = document.getElementById('code-section');
                codeSection.classList.toggle('show');
            }}
            
            function openMermaidLive() {{
                const code = `{cleaned_code}`;
                const encoded = btoa(unescape(encodeURIComponent(code)));
                const url = `https://mermaid.live/edit#${{encoded}}`;
                window.open(url, '_blank');
            }}
        </script>
    </body>
    </html>
    """
    
    return html_template


def get_diagram_type(code: str) -> str:
    """Extract diagram type from Mermaid code."""
    if not code:
        return "unknown"
    
    first_line = code.split('\n')[0].strip().lower()
    
    diagram_types = {
        'graph': 'Graph',
        'flowchart': 'Flowchart',
        'sequencediagram': 'Sequence Diagram',
        'classdiagram': 'Class Diagram',
        'statediagram': 'State Diagram',
        'erdiagram': 'Entity Relationship Diagram',
        'journey': 'User Journey',
        'gantt': 'Gantt Chart',
        'pie': 'Pie Chart',
        'gitgraph': 'Git Graph',
        'c4context': 'C4 Context Diagram',
        'c4container': 'C4 Container Diagram',
        'c4component': 'C4 Component Diagram'
    }
    
    for key, value in diagram_types.items():
        if first_line.startswith(key):
            return value
    
    return "Diagram"


def estimate_diagram_complexity(code: str) -> str:
    """Estimate the complexity of a Mermaid diagram."""
    if not code:
        return "Unknown"
    
    lines = [line.strip() for line in code.split('\n') if line.strip()]
    
    # Count nodes and connections
    node_count = 0
    connection_count = 0
    
    for line in lines:
        # Count arrows (connections)
        arrows = ['-->', '--->', '-.->', '==>', '-.->']
        for arrow in arrows:
            connection_count += line.count(arrow)
        
        # Count node definitions (rough estimate)
        if any(bracket in line for bracket in ['[', '(', '{', '>']):
            node_count += 1
    
    # Determine complexity
    if node_count <= 5 and connection_count <= 5:
        return "Simple"
    elif node_count <= 15 and connection_count <= 20:
        return "Medium"
    else:
        return "Complex"


def format_mermaid_code(code: str) -> str:
    """Format Mermaid code for better readability."""
    if not code:
        return ""
    
    lines = code.split('\n')
    formatted_lines = []
    indent_level = 0
    
    for line in lines:
        stripped = line.strip()
        if not stripped:
            formatted_lines.append("")
            continue
        
        # Adjust indentation for certain keywords
        if any(stripped.lower().startswith(keyword) for keyword in ['end', 'else', 'alt', 'opt']):
            indent_level = max(0, indent_level - 1)
        
        # Add indentation
        formatted_line = "    " * indent_level + stripped
        formatted_lines.append(formatted_line)
        
        # Increase indentation for certain keywords
        if any(stripped.lower().startswith(keyword) for keyword in ['if', 'alt', 'opt', 'loop', 'par']):
            indent_level += 1
    
    return '\n'.join(formatted_lines)