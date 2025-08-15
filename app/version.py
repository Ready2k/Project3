"""Version information for AAA (Automated AI Assessment) system."""

__version__ = "2.2.0"
__version_info__ = (2, 2, 0)

# Release information
RELEASE_NAME = "Code Quality & Analytics"
RELEASE_DATE = "2025-08-15"
RELEASE_NOTES = """
Major Features:
- Fixed Pattern Analytics viewer with complete pattern match logging
- Comprehensive code quality improvements (removed TODO/FIXME, print statements)
- Enhanced debug controls with professional UI toggles
- Improved Pattern Library navigation with targeted expansion
- Fixed 'dict' object has no attribute 'lower' errors across the system

Code Quality Improvements:
- Replaced all print statements with structured loguru logging
- Fixed abstract base classes with proper NotImplementedError implementations
- Resolved Pydantic validation errors with centralized version management
- Added comprehensive pattern match audit logging for analytics
- Enhanced error handling and type safety throughout the codebase

User Experience Enhancements:
- Hidden debug information by default with optional sidebar toggles
- Improved Pattern Analytics → Pattern Library navigation flow
- Professional pattern highlighting without distracting animations
- Clean, organized Pattern Library with collapsed-by-default patterns
- Better user guidance and feedback throughout the application
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