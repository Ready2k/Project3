"""
Pattern Status Utilities

Utility functions for checking and displaying pattern enhancement
and analytics status throughout the application.
"""

from typing import Dict, Any, Tuple
import logging

from app.utils.imports import optional_service


logger = logging.getLogger(__name__)


def check_pattern_enhancement_status() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if pattern enhancement services are available.

    Returns:
        Tuple of (is_available, status_message, details)
    """
    try:
        # First try to get the service
        enhanced_loader = optional_service(
            "enhanced_pattern_loader", context="PatternStatusUtils"
        )

        if enhanced_loader:
            # Get details if available
            details = {}
            try:
                if hasattr(enhanced_loader, "get_analytics_summary"):
                    details = enhanced_loader.get_analytics_summary()
            except Exception as e:
                logger.debug(f"Could not get enhancement details: {e}")

            return (
                True,
                "Pattern enhancement available: Enhanced pattern system services are registered.",
                details,
            )
        else:
            # Try to register services if they're not available
            try:
                from app.core.service_registration import register_core_services
                from app.core.registry import get_registry
                
                registry = get_registry()
                if not registry.has('enhanced_pattern_loader'):
                    logger.info("Attempting to register missing pattern services...")
                    register_core_services(registry, skip_async_services=False)
                
                # Try again after registration
                enhanced_loader = optional_service(
                    "enhanced_pattern_loader", context="PatternStatusUtils"
                )
                
                if enhanced_loader:
                    return (
                        True,
                        "Pattern enhancement available: Services registered on demand.",
                        {},
                    )
            except Exception as e:
                logger.debug(f"Could not register services on demand: {e}")
            
            return (
                False,
                "Pattern enhancement not available: Required services not registered.",
                {},
            )

    except Exception as e:
        logger.error(f"Error checking pattern enhancement status: {e}")
        return False, f"Error checking pattern enhancement: {str(e)}", {}


def check_pattern_analytics_status() -> Tuple[bool, str, Dict[str, Any]]:
    """
    Check if pattern analytics services are available.

    Returns:
        Tuple of (is_available, status_message, details)
    """
    try:
        analytics_service = optional_service(
            "pattern_analytics_service", context="PatternStatusUtils"
        )

        if analytics_service:
            # Get details if available
            details = {}
            try:
                if hasattr(analytics_service, "get_real_time_metrics"):
                    details = analytics_service.get_real_time_metrics()
            except Exception as e:
                logger.debug(f"Could not get analytics details: {e}")

            return (
                True,
                "Pattern analytics available: Enhanced pattern analytics service is registered.",
                details,
            )
        else:
            # Try to register services if they're not available
            try:
                from app.core.service_registration import register_core_services
                from app.core.registry import get_registry
                
                registry = get_registry()
                if not registry.has('pattern_analytics_service'):
                    logger.info("Attempting to register missing analytics services...")
                    register_core_services(registry, skip_async_services=False)
                
                # Try again after registration
                analytics_service = optional_service(
                    "pattern_analytics_service", context="PatternStatusUtils"
                )
                
                if analytics_service:
                    return (
                        True,
                        "Pattern analytics available: Services registered on demand.",
                        {},
                    )
            except Exception as e:
                logger.debug(f"Could not register analytics services on demand: {e}")
            
            return (
                False,
                "Pattern analytics not available: Enhanced pattern loader service not registered.",
                {},
            )

    except Exception as e:
        logger.error(f"Error checking pattern analytics status: {e}")
        return False, f"Error checking pattern analytics: {str(e)}", {}


def get_pattern_enhancement_message() -> str:
    """
    Get a user-friendly message about pattern enhancement status.

    Returns:
        Status message string
    """
    is_available, message, details = check_pattern_enhancement_status()

    if is_available:
        return f"✅ {message}"
    else:
        return f"💡 {message} This feature requires the enhanced pattern system services to be registered."


def get_pattern_analytics_message() -> str:
    """
    Get a user-friendly message about pattern analytics status.

    Returns:
        Status message string
    """
    is_available, message, details = check_pattern_analytics_status()

    if is_available:
        return f"✅ {message}"
    else:
        return f"💡 {message} This feature requires the enhanced pattern system services to be registered."


def get_combined_pattern_status() -> Dict[str, Any]:
    """
    Get combined status for both pattern enhancement and analytics.

    Returns:
        Dictionary with status information for both services
    """
    enhancement_available, enhancement_msg, enhancement_details = (
        check_pattern_enhancement_status()
    )
    analytics_available, analytics_msg, analytics_details = (
        check_pattern_analytics_status()
    )

    return {
        "enhancement": {
            "available": enhancement_available,
            "message": enhancement_msg,
            "details": enhancement_details,
        },
        "analytics": {
            "available": analytics_available,
            "message": analytics_msg,
            "details": analytics_details,
        },
        "overall_status": enhancement_available and analytics_available,
    }


def format_pattern_status_for_ui() -> str:
    """
    Format pattern status for display in UI components.

    Returns:
        Formatted status string for UI display
    """
    status = get_combined_pattern_status()

    lines = []

    # Enhancement status
    if status["enhancement"]["available"]:
        lines.append("✅ Pattern enhancement available")
        details = status["enhancement"]["details"]
        if details:
            lines.append(f"   • {details.get('total_patterns', 0)} patterns loaded")
            lines.append(
                f"   • Cache: {'Enabled' if details.get('cache_enabled') else 'Disabled'}"
            )
    else:
        lines.append(
            "❌ Pattern enhancement not available: Required services not registered."
        )
        lines.append(
            "💡 This feature requires the enhanced pattern system services to be registered."
        )

    lines.append("")  # Empty line

    # Analytics status
    if status["analytics"]["available"]:
        lines.append("✅ Pattern analytics available")
        details = status["analytics"]["details"]
        if details:
            lines.append(
                f"   • {details.get('total_patterns_accessed', 0)} patterns accessed"
            )
            lines.append(f"   • Success rate: {details.get('success_rate', 0.0):.1%}")
    else:
        lines.append(
            "❌ Pattern analytics not available: Enhanced pattern loader service not registered."
        )
        lines.append(
            "💡 This feature requires the enhanced pattern system services to be registered."
        )

    return "\n".join(lines)


# Convenience functions for backward compatibility with existing error messages
def pattern_enhancement_available() -> bool:
    """Check if pattern enhancement is available."""
    is_available, _, _ = check_pattern_enhancement_status()
    return is_available


def pattern_analytics_available() -> bool:
    """Check if pattern analytics is available."""
    is_available, _, _ = check_pattern_analytics_status()
    return is_available


# Functions that can replace hardcoded error messages
def get_pattern_enhancement_error_or_success() -> str:
    """Get either error or success message for pattern enhancement."""
    if pattern_enhancement_available():
        return "✅ Pattern enhancement available"
    else:
        return "❌ Pattern enhancement not available: Required services not registered.\n💡 This feature requires the enhanced pattern system services to be registered."


def get_pattern_analytics_error_or_success() -> str:
    """Get either error or success message for pattern analytics."""
    if pattern_analytics_available():
        return "✅ Pattern analytics available"
    else:
        return "❌ Pattern analytics not available: Enhanced pattern loader service not registered.\n💡 This feature requires the enhanced pattern system services to be registered."
