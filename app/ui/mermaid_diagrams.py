"""Mermaid diagram generation and utilities for Streamlit UI."""

import re
import time
from typing import Dict, Tuple

import streamlit as st

from app.utils.imports import require_service
from app.utils.error_boundaries import error_boundary

# Import streamlit_mermaid directly
try:
    import streamlit_mermaid as stmd

    MERMAID_AVAILABLE = True
except ImportError:
    MERMAID_AVAILABLE = False
    stmd = None


class MermaidDiagramGenerator:
    """Handles Mermaid diagram generation and rendering."""

    def __init__(self) -> None:
        self.diagram_cache: Dict[str, str] = {}

    @error_boundary("mermaid_llm_request", timeout_seconds=30.0, max_retries=2)
    async def make_llm_request(
        self, prompt: str, provider_config: Dict, purpose: str = "diagram_generation"
    ) -> str:
        """Make a request to the LLM for diagram generation using audited provider."""
        try:
            # Get services from registry
            api_service = require_service("api_service", context="mermaid_llm_request")
            config_service = require_service(
                "config_service", context="mermaid_llm_request"
            )
            llm_params = config_service.get_llm_params()

            # Create provider config object with dynamic parameters
            from app.llm.base import ProviderConfig

            config = ProviderConfig(
                provider=provider_config.get("provider", "openai"),
                model=provider_config.get("model", "gpt-4o"),
                api_key=provider_config.get("api_key", ""),
                endpoint_url=provider_config.get("endpoint_url"),
                region=provider_config.get("region"),
                aws_access_key_id=provider_config.get("aws_access_key_id"),
                aws_secret_access_key=provider_config.get("aws_secret_access_key"),
                aws_session_token=provider_config.get("aws_session_token"),
                bedrock_api_key=provider_config.get("bedrock_api_key"),
                temperature=llm_params["temperature"],
                max_tokens=llm_params["max_tokens"],
            )

            # Get session ID for audit logging
            session_id = st.session_state.get("session_id", "mermaid-generation")

            # Create audited LLM provider through API service
            llm_provider = api_service.create_llm_provider(config, session_id)

            # Make the request through the audited provider
            response = await llm_provider.generate(prompt, purpose=purpose)

            if not response:
                raise Exception("Empty response from LLM")

            # Clean the response - remove markdown code blocks if present
            content = response.strip()
            if content.startswith("```mermaid"):
                content = content.replace("```mermaid", "").replace("```", "").strip()
            elif content.startswith("```"):
                content = content.replace("```", "").strip()

            return content

        except Exception as e:
            raise Exception(f"LLM request failed: {str(e)}")

    def sanitize_label(self, label: str) -> str:
        """Sanitize labels for Mermaid diagrams."""
        if not label:
            return "unknown"

        # Remove emojis and special Unicode characters that can cause Mermaid issues
        label = re.sub(r"[^\w\s\-_.:()[\]{}]", "", label)

        # Keep only safe characters for Mermaid
        allowed = set(
            "abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789 -_.:()"
        )
        sanitized = "".join(ch if ch in allowed else "_" for ch in label)

        # Clean up multiple underscores and spaces
        sanitized = re.sub(r"[_\s]+", "_", sanitized).strip("_")

        return sanitized or "unknown"

    def validate_mermaid_syntax(self, mermaid_code: str) -> Tuple[bool, str]:
        """Validate basic Mermaid syntax and return (is_valid, error_message)."""
        if not mermaid_code.strip():
            return False, "Empty diagram code"

        # Check for severely malformed code (all on one line with no spaces around arrows)
        if "\n" not in mermaid_code and len(mermaid_code) > 200:
            return (
                False,
                "Diagram code appears to be malformed (all on one line). This usually indicates an LLM formatting error.",
            )

        # Check for problematic Unicode characters that can cause Mermaid v10.2.4 issues
        if re.search(r"[^\x00-\x7F]", mermaid_code):
            # Get logger service for warning
            app_logger = require_service("logger", context="validate_mermaid_syntax")
            app_logger.warning(
                "Mermaid code contains non-ASCII characters that may cause rendering issues"
            )

        lines = [line.strip() for line in mermaid_code.split("\n") if line.strip()]

        # Check for valid diagram type
        first_line = lines[0].lower()
        valid_starts = [
            "flowchart",
            "graph",
            "sequencediagram",
            "classdiagram",
            "statediagram",
            "c4context",
            "c4container",
            "c4component",
            "c4dynamic",
        ]
        if not any(first_line.startswith(start) for start in valid_starts):
            valid_starts_str = ", ".join(valid_starts)
            return (
                False,
                f"Invalid diagram type. Must start with one of: {valid_starts_str}",
            )

        # Check for common syntax issues
        for i, line in enumerate(lines):
            # Check for unmatched brackets/parentheses
            if line.count("[") != line.count("]"):
                return False, f"Unmatched square brackets on line {i+1}: {line}"
            if line.count("(") != line.count(")"):
                return False, f"Unmatched parentheses on line {i+1}: {line}"

            # For C4 diagrams, skip curly brace validation on individual lines since System_Boundary spans multiple lines
            is_c4_diagram = any(
                first_line.startswith(c4_type)
                for c4_type in ["c4context", "c4container", "c4component", "c4dynamic"]
            )
            if not is_c4_diagram and line.count("{") != line.count("}"):
                return False, f"Unmatched curly braces on line {i+1}: {line}"

        return True, ""

    def extract_mermaid_code(self, response: str) -> str:
        """Extract only the Mermaid code from LLM responses that may contain explanations."""
        if not response:
            return ""

        # First, try to find code within markdown blocks
        markdown_pattern = r"```(?:mermaid)?\s*\n?(.*?)\n?```"
        markdown_match = re.search(
            markdown_pattern, response, re.DOTALL | re.IGNORECASE
        )
        if markdown_match:
            return markdown_match.group(1).strip()

        # Define valid Mermaid diagram start patterns
        diagram_patterns = [
            r"(flowchart\s+(?:TB|TD|BT|RL|LR).*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)",
            r"(graph\s+(?:TB|TD|BT|RL|LR).*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)",
            r"(sequenceDiagram.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)",
            r"(C4Context.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)",
            r"(C4Container.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)",
            r"(C4Component.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)",
            r"(C4Dynamic.*?)(?=\n\n|\n[A-Z]|\n\*|\nNote:|\nExplanation:|\nThis diagram|\nThe diagram|$)",
        ]

        # Try each pattern to extract the diagram
        for pattern in diagram_patterns:
            match = re.search(pattern, response, re.DOTALL | re.IGNORECASE)
            if match:
                extracted = match.group(1).strip()
                # Validate that this looks like actual Mermaid code
                if self._looks_like_mermaid_code(extracted):
                    return extracted

        # Last resort: return the original response and let the cleaning function handle it
        return response

    def _looks_like_mermaid_code(self, code: str) -> bool:
        """Check if the extracted code looks like valid Mermaid syntax."""
        if not code:
            return False

        lines = [line.strip() for line in code.split("\n") if line.strip()]
        if len(lines) < 2:
            return False

        # Check if first line is a valid diagram declaration
        first_line = lines[0].lower()
        valid_starts = [
            "flowchart",
            "graph",
            "sequencediagram",
            "c4context",
            "c4container",
            "c4component",
            "c4dynamic",
        ]
        if not any(first_line.startswith(start) for start in valid_starts):
            return False

        # Check if it contains typical Mermaid syntax
        code_lower = code.lower()
        mermaid_indicators = [
            "-->",
            "---",
            "(",
            ")",
            "[",
            "]",
            "rel(",
            "person(",
            "system(",
            "participant",
            "note",
        ]
        if not any(indicator in code_lower for indicator in mermaid_indicators):
            return False

        return True

    def clean_mermaid_code(self, mermaid_code: str) -> str:
        """Clean and format Mermaid code to ensure proper syntax."""
        if not mermaid_code:
            return "flowchart TB\n    error[No diagram generated]"

        # First, extract only the Mermaid code from mixed responses
        code = self.extract_mermaid_code(mermaid_code.strip())

        # Remove any remaining markdown code blocks
        if code.startswith("```mermaid"):
            code = code.replace("```mermaid", "").replace("```", "").strip()
        elif code.startswith("```"):
            code = code.replace("```", "").strip()

        # Clean problematic Unicode characters that can cause Mermaid v10.2.4 issues
        unicode_replacements = {
            "👤": "User",
            "🤖": "Agent",
            "🎯": "Target",
            "🔬": "Specialist",
            "📋": "Task",
            "💬": "Comm",
            "🔄": "Loop",
            "⚡": "Action",
            "🧠": "Brain",
            "📊": "Monitor",
            "🔍": "Process",
        }

        for emoji, replacement in unicode_replacements.items():
            code = code.replace(emoji, replacement)

        # Remove any remaining non-ASCII characters
        code = re.sub(r"[^\x00-\x7F]+", "", code)

        # Validate the final result
        is_valid, error_msg = self.validate_mermaid_syntax(code)
        if not is_valid:
            # Get logger service for error logging
            app_logger = require_service("logger", context="clean_mermaid_code")
            app_logger.error(f"Mermaid validation failed: {error_msg}")
            return f"""flowchart TB
    error[Diagram Syntax Error]
    details[{error_msg}]
    
    error --> details
    
    note[Please try generating again with a different LLM provider]
    details --> note"""

        return code

    def render_mermaid_diagram(self, mermaid_code: str, height: int = 400) -> None:
        """Render Mermaid diagram in Streamlit with enhanced viewing options."""
        # Get logger service
        app_logger = require_service("logger", context="render_mermaid_diagram")

        # Use streamlit_mermaid directly
        if MERMAID_AVAILABLE and stmd:
            # Clean the code
            cleaned_code = self.clean_mermaid_code(mermaid_code)

            # Render with streamlit_mermaid
            try:
                stmd.st_mermaid(cleaned_code, height=height)
            except Exception as e:
                app_logger.error(f"Failed to render Mermaid diagram: {e}")
                st.error(f"Failed to render diagram: {e}")
                st.code(cleaned_code, language="mermaid")

            # Add enhanced viewing options
            self._add_diagram_controls(cleaned_code)
        else:
            st.info(
                "💡 Mermaid diagrams require the streamlit-mermaid package. Showing code instead:"
            )
            # Show code as fallback
            st.code(mermaid_code, language="mermaid")

    def _add_diagram_controls(self, mermaid_code: str) -> None:
        """Add controls for diagram viewing and export."""
        col1, col2, col3 = st.columns(3)

        with col1:
            if st.button(
                "🔍 Open in Browser", help="Open diagram in full-size browser window"
            ):
                self._create_standalone_html(mermaid_code)

        with col2:
            if st.button("📋 Copy Code", help="Copy Mermaid code to clipboard"):
                st.code(mermaid_code, language="mermaid")

        with col3:
            if st.button("🌐 Edit Online", help="Open in Mermaid Live Editor"):
                mermaid_live_url = f"https://mermaid.live/edit#{mermaid_code}"
                st.markdown(f"[Open in Mermaid Live Editor]({mermaid_live_url})")

    def _create_standalone_html(self, mermaid_code: str) -> None:
        """Create standalone HTML file for full-size diagram viewing."""
        html_content = f"""
        <!DOCTYPE html>
        <html>
        <head>
            <title>Mermaid Diagram</title>
            <script src="https://cdn.jsdelivr.net/npm/mermaid/dist/mermaid.min.js"></script>
            <style>
                body {{ margin: 20px; font-family: Arial, sans-serif; }}
                .controls {{ margin-bottom: 20px; }}
                .btn {{ 
                    padding: 8px 16px; 
                    margin-right: 10px; 
                    background: #0066cc; 
                    color: white; 
                    border: none; 
                    border-radius: 4px; 
                    cursor: pointer; 
                }}
                .btn:hover {{ background: #0052a3; }}
                #diagram {{ border: 1px solid #ddd; padding: 20px; }}
            </style>
        </head>
        <body>
            <div class="controls">
                <button class="btn" onclick="toggleCode()">📋 Toggle Code</button>
                <button class="btn" onclick="downloadSVG()">💾 Download SVG</button>
                <button class="btn" onclick="window.print()">🖨️ Print</button>
            </div>
            
            <div id="diagram">
                <div class="mermaid">
{mermaid_code}
                </div>
            </div>
            
            <div id="code" style="display:none;">
                <h3>Mermaid Code:</h3>
                <pre><code>{mermaid_code}</code></pre>
            </div>
            
            <script>
                mermaid.initialize({{ startOnLoad: true }});
                
                function toggleCode() {{
                    const code = document.getElementById('code');
                    code.style.display = code.style.display === 'none' ? 'block' : 'none';
                }}
                
                function downloadSVG() {{
                    const svg = document.querySelector('svg');
                    if (svg) {{
                        const svgData = new XMLSerializer().serializeToString(svg);
                        const svgBlob = new Blob([svgData], {{type: 'image/svg+xml;charset=utf-8'}});
                        const svgUrl = URL.createObjectURL(svgBlob);
                        const downloadLink = document.createElement('a');
                        downloadLink.href = svgUrl;
                        downloadLink.download = 'diagram.svg';
                        document.body.appendChild(downloadLink);
                        downloadLink.click();
                        document.body.removeChild(downloadLink);
                    }}
                }}
            </script>
        </body>
        </html>
        """

        # Save to exports directory
        from pathlib import Path

        exports_dir = Path("exports")
        exports_dir.mkdir(exist_ok=True)

        html_file = exports_dir / f"diagram_{int(time.time())}.html"
        with open(html_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        st.success(f"✅ Standalone diagram saved to: {html_file}")
        st.markdown(f"[Open Diagram]({html_file})")


# Global instance for convenience
mermaid_generator = MermaidDiagramGenerator()


# Convenience functions for backward compatibility
async def make_llm_request(
    prompt: str, provider_config: Dict, purpose: str = "diagram_generation"
) -> str:
    """Backward compatibility function."""
    return await mermaid_generator.make_llm_request(prompt, provider_config, purpose)


def _sanitize(label: str) -> str:
    """Backward compatibility function."""
    return mermaid_generator.sanitize_label(label)


def _validate_mermaid_syntax(mermaid_code: str) -> Tuple[bool, str]:
    """Backward compatibility function."""
    return mermaid_generator.validate_mermaid_syntax(mermaid_code)


def _extract_mermaid_code(response: str) -> str:
    """Backward compatibility function."""
    return mermaid_generator.extract_mermaid_code(response)


def _clean_mermaid_code(mermaid_code: str) -> str:
    """Backward compatibility function."""
    return mermaid_generator.clean_mermaid_code(mermaid_code)
