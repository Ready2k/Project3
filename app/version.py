"""Version information for AAA (Automated AI Assessment) system."""

__version__ = "2.1.0"
__version_info__ = (2, 1, 0)

# Release information
RELEASE_NAME = "Technology Catalog"
RELEASE_DATE = "2025-08-14"
RELEASE_NOTES = """
Major Features:
- Dedicated Technology Catalog system with 55+ technologies
- Complete CRUD management interface in Streamlit
- 90% performance improvement in startup time
- Automatic LLM-suggested technology integration
- Import/Export functionality for technology catalogs
- Smart categorization across 17 technology categories

Improvements:
- Enhanced tech stack generation with rich metadata
- Backup safety for all catalog operations
- Advanced filtering and search capabilities
- Repository cleanup and documentation updates
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