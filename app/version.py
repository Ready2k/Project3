"""Version information for AAA (Automated AI Assessment) system."""

__version__ = "2.4.0"
__version_info__ = (2, 4, 0)

# Release information
RELEASE_NAME = "Session Continuity & Service Reliability"
RELEASE_DATE = "2025-08-23"
RELEASE_NOTES = """
Major User Experience Features:
- Resume Previous Session: Complete session continuity allowing users to return to any previous analysis
- Session ID Management: Copy-to-clipboard functionality and comprehensive session information display
- Enhanced Collaboration: Share session IDs with team members for collaborative analysis review
- Workflow Continuity: Never lose analysis progress due to browser crashes or interruptions

Session Management Features:
- Session ID Validation: Robust UUID format validation with user-friendly error messages
- Complete State Restoration: Restores phase, progress, requirements, and recommendations from any session
- Cross-Input Compatibility: Works with Text Input, File Upload, and Jira Integration methods
- Help System: Comprehensive guidance on finding and using session IDs

Critical Bug Fixes:
- Agentic Recommendation Service: Fixed 'workflow_automation' attribute error preventing pattern saving
- Pattern Creation Stability: Resolved crashes during APAT pattern and multi-agent system saving
- Attribute Access Consistency: Corrected AutonomyAssessment attribute references throughout codebase
- Service Reliability: Enhanced stability of agentic recommendation generation and pattern persistence

Technical Improvements:
- Session Persistence: Leverages existing DiskCacheStore for reliable session management
- Error Handling: Comprehensive error messages with troubleshooting guidance
- API Integration: Uses existing endpoints for seamless session retrieval
- Testing Coverage: Extensive test suites for session validation and service reliability

User Interface Enhancements:
- New Input Method: "Resume Previous Session" option in Analysis tab
- Session Information Display: Current session ID with copy functionality at bottom of Analysis tab
- Validation Feedback: Clear success/error messages for session operations
- Help Integration: Contextual guidance for session management features
"""

def get_version():
    """Get the current version string."""
    return __version__

def get_version_info():
    """Get version information as a dictionary."""
    return {
        "version": __version__,
        "version_info": __version_info__,
        "release_name": RELEASE_NAME,
        "release_date": RELEASE_DATE,
        "release_notes": RELEASE_NOTES
    }