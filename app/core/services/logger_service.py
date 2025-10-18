"""
Logger Service Implementation

Provides a centralized logging service that implements the Service interface
and can be registered in the service registry.
"""

import logging
import sys
from typing import Dict, Any, List, Optional
from pathlib import Path

from app.core.service import ConfigurableService
from app.utils.redact import PIIRedactor


class LoggerService(ConfigurableService):
    """
    Centralized logging service with PII redaction and structured logging.

    This service provides a unified logging interface for the entire application
    with configurable levels, formats, and PII redaction capabilities.
    """

    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the logger service.

        Args:
            config: Logger configuration dictionary
        """
        super().__init__(config, "logger")
        self._dependencies = ["config"]  # Depends on configuration service

        # Configuration with defaults
        self.level = self.get_config("level", "INFO")
        self.format_type = self.get_config("format", "structured")
        self.redact_pii = self.get_config("redact_pii", True)
        self.file_path = self.get_config("file_path")
        self.rotation = self.get_config("rotation", "1 day")
        self.retention = self.get_config("retention", "30 days")

        # Internal state
        self._logger: Optional[logging.Logger] = None
        self._pii_redactor: Optional[PIIRedactor] = None
        self._handlers: List[logging.Handler] = []

    def _do_initialize(self) -> None:
        """Initialize the logging system."""
        # Initialize PII redactor if enabled
        if self.redact_pii:
            self._pii_redactor = PIIRedactor()

        # Create the main logger
        self._logger = logging.getLogger("aaa")
        self._logger.setLevel(getattr(logging, self.level.upper()))

        # Clear any existing handlers
        self._logger.handlers.clear()

        # Set up formatters
        if self.format_type == "structured":
            formatter = logging.Formatter(
                '{"timestamp": "%(asctime)s", "level": "%(levelname)s", '
                '"logger": "%(name)s", "function": "%(funcName)s", '
                '"line": %(lineno)d, "message": "%(message)s"}'
            )
        elif self.format_type == "detailed":
            formatter = logging.Formatter(
                "%(asctime)s | %(levelname)-8s | %(name)s:%(funcName)s:%(lineno)d | %(message)s"
            )
        else:  # simple format
            formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")

        # Console handler
        console_handler = logging.StreamHandler(sys.stderr)
        console_handler.setFormatter(formatter)
        self._handlers.append(console_handler)
        self._logger.addHandler(console_handler)

        # File handler if configured
        if self.file_path:
            try:
                # Create directory if it doesn't exist
                file_path = Path(self.file_path)
                file_path.parent.mkdir(parents=True, exist_ok=True)

                # Use RotatingFileHandler for log rotation
                from logging.handlers import RotatingFileHandler

                file_handler = RotatingFileHandler(
                    self.file_path, maxBytes=10 * 1024 * 1024, backupCount=5  # 10MB
                )
                file_handler.setFormatter(formatter)
                self._handlers.append(file_handler)
                self._logger.addHandler(file_handler)

            except Exception as e:
                # Log to console if file logging fails
                self._logger.warning(f"Failed to set up file logging: {e}")

        # Set up root logger to use our logger
        root_logger = logging.getLogger()
        root_logger.setLevel(getattr(logging, self.level.upper()))

        if self._logger:
            self._logger.info(f"Logger service initialized with level {self.level}")

    def _do_shutdown(self) -> None:
        """Shutdown the logging system."""
        if self._logger:
            try:
                self._logger.info("Shutting down logger service")
            except Exception:
                pass  # Ignore logging errors during shutdown

            # Close all handlers
            for handler in self._handlers:
                try:
                    handler.close()
                except Exception as e:
                    print(f"Error closing log handler: {e}")

            # Clear handlers
            if self._logger:
                self._logger.handlers.clear()
            self._handlers.clear()

    def _do_health_check(self) -> bool:
        """Check if the logger is healthy."""
        try:
            # Test logging functionality
            if self._logger:
                # Try to log a test message at debug level
                self._logger.debug("Health check test message")
                return True
            return False
        except Exception:
            return False

    def _redact_message(self, message: str) -> str:
        """Redact PII from log message if redactor is enabled."""
        if self._pii_redactor and isinstance(message, str):
            return self._pii_redactor.redact(message)
        return message

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with PII redaction."""
        if self._logger:
            self._logger.debug(self._redact_message(message), **kwargs)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with PII redaction."""
        if self._logger:
            self._logger.info(self._redact_message(message), **kwargs)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with PII redaction."""
        if self._logger:
            self._logger.warning(self._redact_message(message), **kwargs)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with PII redaction."""
        if self._logger:
            self._logger.error(self._redact_message(message), **kwargs)

    def critical(self, message: str, **kwargs: Any) -> None:
        """Log critical message with PII redaction."""
        if self._logger:
            self._logger.critical(self._redact_message(message), **kwargs)

    def exception(self, message: str, **kwargs: Any) -> None:
        """Log exception with traceback and PII redaction."""
        if self._logger:
            self._logger.exception(self._redact_message(message), **kwargs)

    def get_logger(self, name: Optional[str] = None) -> logging.Logger:
        """
        Get a logger instance.

        Args:
            name: Logger name (defaults to main application logger)

        Returns:
            Logger instance
        """
        if name:
            return logging.getLogger(f"aaa.{name}")
        return self._logger or logging.getLogger("aaa")

    def set_level(self, level: str) -> None:
        """
        Change the logging level.

        Args:
            level: New logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        """
        if self._logger:
            self._logger.setLevel(getattr(logging, level.upper()))
            self.level = level.upper()
            self._logger.info(f"Logger level changed to {level}")

    def get_stats(self) -> Dict[str, Any]:
        """
        Get logging statistics.

        Returns:
            Dictionary with logging statistics
        """
        return {
            "level": self.level,
            "format": self.format_type,
            "pii_redaction_enabled": self.redact_pii,
            "file_logging_enabled": bool(self.file_path),
            "file_path": self.file_path,
            "handler_count": len(self._handlers),
            "logger_name": self._logger.name if self._logger else None,
        }
