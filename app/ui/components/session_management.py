"""Session management UI component."""

import re
from typing import Dict, Any, Pattern
import streamlit as st

from app.utils.imports import require_service


class SessionManagementComponent:
    """Handles session management UI and state."""
    
    def __init__(self) -> None:
        self.session_id_pattern: Pattern[str] = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$', re.IGNORECASE)
    
    def initialize_session_state(self) -> None:
        """Initialize Streamlit session state variables."""
        default_values = {
            'session_id': None,
            'phase': 'input',
            'progress': 0,
            'requirements': {},
            'missing_fields': [],
            'questions': [],
            'qa_complete': False,
            'recommendations': [],
            'feasibility': '',
            'tech_stack': [],
            'reasoning': '',
            'processing': False,
            'provider_config': {
                'provider': 'fake',
                'model': 'fake-model'
            }
        }
        
        for key, default_value in default_values.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def render_session_info(self) -> None:
        """Render current session information."""
        if st.session_state.get('session_id'):
            with st.expander("📋 Session Information", expanded=False):
                col1, col2 = st.columns(2)
                
                with col1:
                    st.write(f"**Session ID:** `{st.session_state.session_id}`")
                    st.write(f"**Phase:** {st.session_state.get('phase', 'unknown').title()}")
                
                with col2:
                    st.write(f"**Progress:** {st.session_state.get('progress', 0)}%")
                    
                    # Copy session ID button
                    if st.button("📋 Copy Session ID"):
                        st.code(st.session_state.session_id)
                        st.success("Session ID copied to display!")
    
    def render_resume_session(self, api_integration: Any) -> bool:
        """Render resume session UI."""
        st.subheader("🔄 Resume Previous Session")
        
        with st.form("resume_session_form"):
            st.write("Enter a session ID to resume a previous analysis:")
            
            session_id_input = st.text_input(
                "Session ID",
                placeholder="e.g., 12345678-1234-1234-1234-123456789abc",
                help="Session IDs are available in analysis results, exports, and browser URLs"
            )
            
            submitted = st.form_submit_button("🔄 Resume Session", type="primary")
            
            if submitted:
                if self.validate_session_id(session_id_input):
                    return self._attempt_resume_session(session_id_input, api_integration)
                else:
                    st.error("❌ Invalid session ID format. Please check and try again.")
                    self._show_session_id_help()
                    return False
        
        return False
    
    def validate_session_id(self, session_id: str) -> bool:
        """Validate session ID format."""
        if not session_id or not isinstance(session_id, str):
            return False
        
        # Clean the input
        session_id = session_id.strip()
        
        # Check UUID format
        return bool(self.session_id_pattern.match(session_id))
    
    def _attempt_resume_session(self, session_id: str, api_integration: Any) -> bool:
        """Attempt to resume a session."""
        try:
            with st.spinner("🔍 Loading session..."):
                result = api_integration.load_session_status_with_ui_feedback(session_id)
                
                if result:
                    st.session_state.session_id = session_id
                    st.success("✅ Session resumed successfully!")
                    
                    # Show session details
                    phase = result.get('phase', 'unknown')
                    progress = result.get('progress', 0)
                    
                    st.info(f"📊 **Session Status**: {phase.title()} ({progress}% complete)")
                    
                    if result.get('requirements'):
                        st.write("**Requirements loaded:**")
                        st.json(result['requirements'])
                    
                    st.rerun()
                    return True
                else:
                    st.error("❌ Could not load session. Please check the session ID and try again.")
                    return False
                    
        except Exception as e:
            st.error(f"❌ Error resuming session: {str(e)}")
            # Get logger service for error logging
            app_logger = require_service('logger', context="resume_session")
            app_logger.error(f"Session resume error: {e}")
            return False
    
    def _show_session_id_help(self) -> None:
        """Show help information for finding session IDs."""
        with st.expander("❓ Where do I find my Session ID?"):
            st.write("**Session IDs can be found in several places:**")
            
            st.write("1. **Analysis Results Page**: Displayed at the top of results")
            st.write("2. **Export Files**: Included in JSON, Markdown, and HTML exports")
            st.write("3. **Browser URL**: Added to the URL during analysis")
            st.write("4. **Session Information**: Click the 📋 Session Information expander")
            
            st.write("**Session ID Format:**")
            st.code("12345678-1234-1234-1234-123456789abc")
            st.write("Session IDs are UUIDs with 8-4-4-4-12 character groups separated by hyphens.")
    
    def render_session_progress(self) -> None:
        """Render session progress indicator."""
        if st.session_state.get('session_id'):
            phase = st.session_state.get('phase', 'input')
            progress = st.session_state.get('progress', 0)
            
            # Progress bar
            st.progress(progress / 100)
            
            # Phase indicators
            phases = ['input', 'qa', 'analysis', 'complete']
            current_phase_index = phases.index(phase) if phase in phases else 0
            
            cols = st.columns(len(phases))
            for i, phase_name in enumerate(phases):
                with cols[i]:
                    if i <= current_phase_index:
                        st.success(f"✅ {phase_name.title()}")
                    else:
                        st.info(f"⏳ {phase_name.title()}")
    
    def clear_session(self) -> None:
        """Clear current session state."""
        keys_to_clear = [
            'session_id', 'phase', 'progress', 'requirements', 'missing_fields',
            'questions', 'qa_complete', 'recommendations', 'feasibility',
            'tech_stack', 'reasoning'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                del st.session_state[key]
        
        # Get logger service for info logging
        app_logger = require_service('logger', context="clear_session_state")
        app_logger.info("Session state cleared")
    
    def render_session_actions(self) -> None:
        """Render session action buttons."""
        if st.session_state.get('session_id'):
            col1, col2, col3 = st.columns(3)
            
            with col1:
                if st.button("🔄 Refresh Status"):
                    st.rerun()
            
            with col2:
                if st.button("📋 Show Session Info"):
                    self.render_session_info()
            
            with col3:
                if st.button("🗑️ Clear Session"):
                    self.clear_session()
                    st.success("Session cleared!")
                    st.rerun()
    
    def get_session_summary(self) -> Dict[str, Any]:
        """Get summary of current session state."""
        return {
            "session_id": st.session_state.get('session_id'),
            "phase": st.session_state.get('phase', 'input'),
            "progress": st.session_state.get('progress', 0),
            "has_requirements": bool(st.session_state.get('requirements')),
            "has_questions": bool(st.session_state.get('questions')),
            "qa_complete": st.session_state.get('qa_complete', False),
            "has_recommendations": bool(st.session_state.get('recommendations')),
            "processing": st.session_state.get('processing', False)
        }
    
    def update_session_progress(self, phase: str, progress: int) -> None:
        """Update session progress."""
        st.session_state.phase = phase
        st.session_state.progress = progress
        # Get logger service for info logging
        app_logger = require_service('logger', context="update_session_progress")
        app_logger.info(f"Session progress updated: {phase} ({progress}%)")
    
    def is_session_active(self) -> bool:
        """Check if there's an active session."""
        return bool(st.session_state.get('session_id'))
    
    def is_session_complete(self) -> bool:
        """Check if the current session is complete."""
        return (
            self.is_session_active() and
            st.session_state.get('phase') == 'complete' and
            st.session_state.get('progress', 0) >= 100
        )