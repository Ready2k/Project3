"""Session management component for session handling."""

from typing import Dict, List, Optional, Any

import streamlit as st

from app.ui.components.base import BaseComponent

# Import logger for error handling
from app.utils.logger import app_logger


class SessionManagementComponent(BaseComponent):
    """Component for session management and display."""
    
    def __init__(self, session_manager, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.session_manager = session_manager
    
    def render(self, **kwargs) -> Any:
        """Render the session management component."""
        if st.session_state.session_id:
            self.render_session_info()
        else:
            self.render_no_session_info()
    
    def render_session_info(self):
        """Render current session information."""
        st.markdown("**Current Session Information:**")
        
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.code(f"Session ID: {st.session_state.session_id}", language=None)
            st.caption("💡 Save this Session ID to resume this analysis later")
            
            # Additional session details
            session_data = self.session_manager.get_session_data()
            
            if session_data.get('current_phase'):
                st.write(f"**Current Phase:** {session_data['current_phase']}")
            
            if session_data.get('progress', 0) > 0:
                st.write(f"**Progress:** {session_data['progress']}%")
        
        with col2:
            # Copy to clipboard button
            if st.button("📋 Copy Session ID", key="copy_session_id"):
                self._copy_to_clipboard(st.session_state.session_id)
                st.success("✅ Session ID copied to clipboard!")
    
    def render_no_session_info(self):
        """Render when no session is active."""
        st.info("No active session. Start an analysis to create a session.")
    
    def render_session_actions(self):
        """Render session action buttons."""
        if not st.session_state.session_id:
            return
        
        col1, col2, col3 = st.columns(3)
        
        with col1:
            if st.button("🔄 Refresh Session", key="refresh_session"):
                self._refresh_session()
        
        with col2:
            if st.button("💾 Save Session", key="save_session"):
                self._save_session()
        
        with col3:
            if st.button("🗑️ Clear Session", key="clear_session"):
                self._clear_session()
    
    def render_session_history(self):
        """Render session history if available."""
        st.subheader("📚 Session History")
        
        # Get session history from local storage or API
        history = self._get_session_history()
        
        if history:
            for session in history[-5:]:  # Show last 5 sessions
                with st.expander(f"Session {session['id'][:8]}... - {session['created_at']}"):
                    st.write(f"**Phase:** {session.get('phase', 'Unknown')}")
                    st.write(f"**Progress:** {session.get('progress', 0)}%")
                    
                    if st.button(f"Resume", key=f"resume_{session['id']}"):
                        self._resume_session(session['id'])
        else:
            st.info("No session history available.")
    
    def render_session_export(self):
        """Render session export options."""
        if not st.session_state.session_id:
            return
        
        st.subheader("📤 Export Session")
        
        export_format = st.selectbox(
            "Export Format",
            ["JSON", "Markdown", "CSV"],
            key="session_export_format"
        )
        
        if st.button("📥 Export Session Data", key="export_session"):
            self._export_session(export_format.lower())
    
    def _copy_to_clipboard(self, text: str):
        """Copy text to clipboard using JavaScript."""
        copy_js = f"""
        <script>
        navigator.clipboard.writeText('{text}').then(function() {{
            console.log('Text copied to clipboard: {text}');
        }}).catch(function(err) {{
            console.error('Failed to copy text: ', err);
        }});
        </script>
        """
        st.components.v1.html(copy_js, height=0)
    
    def _refresh_session(self):
        """Refresh the current session data."""
        try:
            # This would typically make an API call to refresh session data
            st.success("✅ Session refreshed successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to refresh session: {str(e)}")
            app_logger.error(f"Session refresh failed: {str(e)}")
    
    def _save_session(self):
        """Save the current session."""
        try:
            # This would typically make an API call to save session data
            session_data = self.session_manager.get_session_data()
            
            # Save to local storage or API
            self._save_to_history(session_data)
            
            st.success("✅ Session saved successfully!")
        except Exception as e:
            st.error(f"Failed to save session: {str(e)}")
            app_logger.error(f"Session save failed: {str(e)}")
    
    def _clear_session(self):
        """Clear the current session."""
        try:
            self.session_manager.reset_session()
            st.success("✅ Session cleared successfully!")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to clear session: {str(e)}")
            app_logger.error(f"Session clear failed: {str(e)}")
    
    def _resume_session(self, session_id: str):
        """Resume a specific session."""
        try:
            # This would typically make an API call to resume the session
            st.session_state.session_id = session_id
            st.success(f"✅ Resumed session {session_id[:8]}...")
            st.rerun()
        except Exception as e:
            st.error(f"Failed to resume session: {str(e)}")
            app_logger.error(f"Session resume failed: {str(e)}")
    
    def _export_session(self, format_type: str):
        """Export session data in the specified format."""
        try:
            session_data = self.session_manager.get_session_data()
            
            if format_type == "json":
                import json
                export_data = json.dumps(session_data, indent=2)
                st.download_button(
                    label="📥 Download JSON",
                    data=export_data,
                    file_name=f"session_{st.session_state.session_id}.json",
                    mime="application/json"
                )
            
            elif format_type == "markdown":
                export_data = self._format_as_markdown(session_data)
                st.download_button(
                    label="📥 Download Markdown",
                    data=export_data,
                    file_name=f"session_{st.session_state.session_id}.md",
                    mime="text/markdown"
                )
            
            elif format_type == "csv":
                export_data = self._format_as_csv(session_data)
                st.download_button(
                    label="📥 Download CSV",
                    data=export_data,
                    file_name=f"session_{st.session_state.session_id}.csv",
                    mime="text/csv"
                )
            
            st.success(f"✅ Session exported as {format_type.upper()}!")
            
        except Exception as e:
            st.error(f"Failed to export session: {str(e)}")
            app_logger.error(f"Session export failed: {str(e)}")
    
    def _get_session_history(self) -> List[Dict]:
        """Get session history from storage."""
        # This would typically retrieve from local storage or API
        # For now, return empty list
        return []
    
    def _save_to_history(self, session_data: Dict):
        """Save session data to history."""
        # This would typically save to local storage or API
        pass
    
    def _format_as_markdown(self, session_data: Dict) -> str:
        """Format session data as Markdown."""
        markdown = f"""# Session Report
        
## Session Information
- **Session ID:** {session_data.get('session_id', 'N/A')}
- **Current Phase:** {session_data.get('current_phase', 'N/A')}
- **Progress:** {session_data.get('progress', 0)}%

## Provider Configuration
- **Provider:** {session_data.get('provider_config', {}).get('provider', 'N/A')}
- **Model:** {session_data.get('provider_config', {}).get('model', 'N/A')}

## Q&A Questions
"""
        
        qa_questions = session_data.get('qa_questions', [])
        if qa_questions:
            for i, question in enumerate(qa_questions, 1):
                markdown += f"{i}. {question.get('question', 'N/A')}\n"
        else:
            markdown += "No Q&A questions available.\n"
        
        return markdown
    
    def _format_as_csv(self, session_data: Dict) -> str:
        """Format session data as CSV."""
        import csv
        import io
        
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write headers
        writer.writerow(['Field', 'Value'])
        
        # Write session data
        writer.writerow(['Session ID', session_data.get('session_id', 'N/A')])
        writer.writerow(['Current Phase', session_data.get('current_phase', 'N/A')])
        writer.writerow(['Progress', f"{session_data.get('progress', 0)}%"])
        writer.writerow(['Provider', session_data.get('provider_config', {}).get('provider', 'N/A')])
        writer.writerow(['Model', session_data.get('provider_config', {}).get('model', 'N/A')])
        
        return output.getvalue()