"""Logger helper for consistent logger access across the application."""

from typing import Any, Optional
from app.utils.imports import optional_service
from app.utils.logger import app_logger as fallback_logger


def get_logger(context: Optional[str] = None) -> Any:
    """Get logger from service registry with fallback to app_logger."""
    try:
        service_logger = optional_service("logger", context=context)
        return service_logger if service_logger else fallback_logger
    except Exception:
        return fallback_logger


# Global logger instance for convenience
app_logger = get_logger()
