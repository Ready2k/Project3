"""Logging configuration with PII redaction."""

import sys
from typing import Any, Optional

from loguru import logger

from app.utils.redact import PIIRedactor


class PIIRedactingLogger:
    """Logger wrapper that redacts PII from log messages."""
    
    def __init__(self, redact_pii: bool = True) -> None:
        self.redactor: Optional[PIIRedactor] = PIIRedactor() if redact_pii else None
        self._configure_logger()
    
    def _configure_logger(self) -> None:
        """Configure loguru logger."""
        logger.remove()  # Remove default handler
        logger.add(
            sys.stderr,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}",
            level="INFO"
        )
    
    def _redact_message(self, message: str) -> str:
        """Redact PII from log message if redactor is enabled."""
        if self.redactor:
            return self.redactor.redact(message)
        return message
    
    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with PII redaction."""
        logger.info(self._redact_message(message), **kwargs)
    
    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with PII redaction."""
        logger.error(self._redact_message(message), **kwargs)
    
    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with PII redaction."""
        logger.warning(self._redact_message(message), **kwargs)
    
    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with PII redaction."""
        logger.debug(self._redact_message(message), **kwargs)


# Global logger instance
app_logger: PIIRedactingLogger = PIIRedactingLogger()