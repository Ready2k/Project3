"""Version information for AAA (Automated AI Assessment) system."""

__version__ = "2.3.0"
__version_info__ = (2, 3, 0)

# Release information
RELEASE_NAME = "Advanced Prompt Defense System"
RELEASE_DATE = "2025-08-16"
RELEASE_NOTES = """
Major Security Features:
- Advanced Prompt Defense System with 8 specialized detectors
- Multi-layered security protecting against various attack vectors
- Multilingual attack detection (English, Spanish, French, German, Chinese, Japanese)
- Real-time security monitoring with comprehensive attack detection
- User education system with contextual guidance for security violations
- Performance-optimized security validation (sub-100ms with caching)

Security Components:
- Overt Injection Detection: Direct prompt manipulation attempts
- Covert Injection Detection: Hidden attacks via encoding, markdown, zero-width characters
- Context Attack Detection: Buried instructions and lorem ipsum attacks
- Data Egress Protection: System prompt and environment variable extraction prevention
- Business Logic Protection: Configuration access and safety toggle protection
- Protocol Tampering Detection: JSON validation and format manipulation protection
- Scope Validation: Business domain enforcement (feasibility, automation, assessment)
- Multilingual Attack Detection: Support for attacks in 6 languages

Infrastructure Improvements:
- Deployment Management: Gradual rollout with automatic rollback capabilities
- Configuration Integration: Full Pydantic model integration with YAML configuration
- Security Event Logging: Structured logging with PII redaction
- Performance Optimization: Intelligent caching and parallel detection
- Comprehensive Testing: 100% test coverage for all security components

Configuration Fix:
- Resolved Pydantic validation errors for advanced security settings
- Added missing configuration classes for deployment and security management
- Fixed Q&A system errors related to configuration validation
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