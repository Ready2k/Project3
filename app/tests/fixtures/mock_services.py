"""
Mock services for testing purposes.

Provides mock service implementations for use in integration tests.
"""

from typing import List, Dict, Any, Optional
from app.core.service import Service


class TestService(Service):
    """Basic test service implementation."""

    def __init__(self, name: str = "test_service"):
        self._name = name
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return []

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized


class OptionalService(Service):
    """Service with optional dependencies for testing."""

    def __init__(self, name: str = "optional_service"):
        self._name = name
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return ["missing_dependency"]  # Intentionally missing dependency

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized


class ServiceA(Service):
    """Service A for circular dependency testing."""

    def __init__(self, name: str = "service_a"):
        self._name = name
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return ["service_b"]

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized


class ServiceB(Service):
    """Service B for circular dependency testing."""

    def __init__(self, name: str = "service_b"):
        self._name = name
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return ["service_a"]

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized


class FailingService(Service):
    """Service that fails during initialization."""

    def __init__(self, name: str = "failing_service", fail_on_init: bool = True):
        self._name = name
        self._fail_on_init = fail_on_init
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return []

    def initialize(self) -> None:
        if self._fail_on_init:
            raise RuntimeError("Service initialization failed")
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False

    def health_check(self) -> bool:
        return self._initialized


class ConfigurableTestService(Service):
    """Configurable test service for configuration testing."""

    def __init__(
        self,
        name: str = "configurable_service",
        config: Optional[Dict[str, Any]] = None,
    ):
        self._name = name
        self._config = config or {}
        self._initialized = False
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return self._config.get("dependencies", [])

    def initialize(self) -> None:
        if self._config.get("fail_on_init", False):
            raise RuntimeError("Configured to fail on initialization")
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False

    def health_check(self) -> bool:
        if self._config.get("fail_health_check", False):
            return False
        return self._initialized

    def get_config(self, key: str, default: Any = None) -> Any:
        """Get configuration value."""
        return self._config.get(key, default)
