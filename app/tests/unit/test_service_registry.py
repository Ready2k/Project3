"""
Unit tests for the Service Registry.

Tests cover:
- Singleton registration and retrieval
- Factory registration and lazy creation
- Dependency injection and resolution
- Circular dependency detection
- Service validation and health checking
"""

import pytest
from unittest.mock import Mock, patch
from typing import List, Optional

from app.core.registry import (
    ServiceRegistry,
    ServiceLifecycle,
    ServiceNotFoundError,
    ServiceInitializationError,
    get_registry,
    reset_registry,
)
from app.core.service import Service, ConfigurableService


class MockService(Service):
    """Mock service for testing."""

    def __init__(
        self, name: str = "mock_service", dependencies: Optional[List[str]] = None
    ):
        self._name = name
        self._dependencies = dependencies or []
        self._initialized = False
        self._healthy = True
        self._shutdown_called = False

    @property
    def name(self) -> str:
        return self._name

    @property
    def dependencies(self) -> List[str]:
        return self._dependencies

    def initialize(self) -> None:
        self._initialized = True

    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False

    def health_check(self) -> bool:
        return self._healthy

    def set_healthy(self, healthy: bool) -> None:
        self._healthy = healthy


class MockConfigurableService(ConfigurableService):
    """Mock configurable service for testing."""

    def __init__(
        self,
        config: dict,
        name: str = "mock_configurable",
        dependencies: Optional[List[str]] = None,
    ):
        super().__init__(config, name)
        if dependencies:
            self._dependencies = dependencies

    def _do_initialize(self) -> None:
        # Simulate initialization work
        pass

    def _do_shutdown(self) -> None:
        # Simulate shutdown work
        pass


class TestServiceRegistry:
    """Test cases for ServiceRegistry class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.registry = ServiceRegistry()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_registry()

    # Singleton Registration and Retrieval Tests

    def test_register_singleton_service(self):
        """Test registering a singleton service."""
        service = MockService("test_service")

        self.registry.register_singleton("test_service", service)

        assert self.registry.has("test_service")
        service_info = self.registry.get_service_info("test_service")
        assert service_info is not None
        assert service_info.name == "test_service"
        assert service_info.service_type == "singleton"
        assert service_info.lifecycle == ServiceLifecycle.INITIALIZED
        assert service_info.instance is service

    def test_register_singleton_with_dependencies(self):
        """Test registering a singleton service with dependencies."""
        service = MockService("test_service", ["dep1", "dep2"])

        self.registry.register_singleton("test_service", service, ["dep1", "dep2"])

        service_info = self.registry.get_service_info("test_service")
        assert service_info.dependencies == ["dep1", "dep2"]

    def test_get_singleton_service(self):
        """Test retrieving a singleton service."""
        service = MockService("test_service")
        self.registry.register_singleton("test_service", service)

        retrieved = self.registry.get("test_service")

        assert retrieved is service
        # Should return the same instance on subsequent calls
        assert self.registry.get("test_service") is service

    def test_singleton_health_check_on_registration(self):
        """Test that health check is performed on singleton registration."""
        service = MockService("test_service")
        service.set_healthy(False)

        self.registry.register_singleton("test_service", service)

        service_info = self.registry.get_service_info("test_service")
        assert service_info.health_status is False

    # Factory Registration and Lazy Creation Tests

    def test_register_factory_service(self):
        """Test registering a factory service."""

        def factory():
            return MockService("factory_service")

        self.registry.register_factory("factory_service", factory)

        assert self.registry.has("factory_service")
        service_info = self.registry.get_service_info("factory_service")
        assert service_info.name == "factory_service"
        assert service_info.service_type == "factory"
        assert service_info.lifecycle == ServiceLifecycle.REGISTERED
        assert service_info.factory is factory
        assert service_info.instance is None  # Not created yet

    def test_factory_lazy_creation(self):
        """Test that factory services are created lazily."""
        creation_count = 0

        def factory():
            nonlocal creation_count
            creation_count += 1
            return MockService(f"factory_service_{creation_count}")

        self.registry.register_factory("factory_service", factory)

        # Factory should not be called during registration
        assert creation_count == 0

        # Factory should be called when service is requested
        service1 = self.registry.get("factory_service")
        assert creation_count == 1
        assert service1.name == "factory_service_1"

        # Factory should be called again for each request (not singleton)
        service2 = self.registry.get("factory_service")
        assert creation_count == 2
        assert service2.name == "factory_service_2"
        assert service1 is not service2

    def test_factory_with_dependencies(self):
        """Test factory service with dependencies."""

        def factory():
            return MockService("factory_service", ["dep1"])

        self.registry.register_factory("factory_service", factory, ["dep1"])

        service_info = self.registry.get_service_info("factory_service")
        assert service_info.dependencies == ["dep1"]

    def test_factory_creation_error(self):
        """Test error handling during factory service creation."""

        def failing_factory():
            raise ValueError("Factory creation failed")

        self.registry.register_factory("failing_service", failing_factory)

        with pytest.raises(ServiceInitializationError) as exc_info:
            self.registry.get("failing_service")

        assert "Failed to initialize service 'failing_service'" in str(exc_info.value)
        assert "Factory creation failed" in str(exc_info.value)

    # Class Registration and Dependency Injection Tests

    def test_register_class_service(self):
        """Test registering a class service."""
        self.registry.register_class("class_service", MockService)

        assert self.registry.has("class_service")
        service_info = self.registry.get_service_info("class_service")
        assert service_info.name == "class_service"
        assert service_info.service_type == "class"
        assert service_info.service_class is MockService
        assert service_info.instance is None  # Not created yet

    def test_class_service_creation(self):
        """Test creating instance from class service."""
        self.registry.register_class("class_service", MockService)

        service = self.registry.get("class_service")

        assert isinstance(service, MockService)
        assert (
            service.name == "mock_service"
        )  # Default name from MockService constructor

        # Should return same instance on subsequent calls (singleton behavior)
        assert self.registry.get("class_service") is service

    def test_class_service_with_explicit_dependencies(self):
        """Test class service with explicitly specified dependencies."""
        self.registry.register_class("class_service", MockService, ["dep1", "dep2"])

        service_info = self.registry.get_service_info("class_service")
        assert service_info.dependencies == ["dep1", "dep2"]

    def test_dependency_injection_in_class_service(self):
        """Test automatic dependency injection for class services."""

        # Create a service that requires dependencies
        class ServiceWithDeps:
            def __init__(self, logger, config):
                self.logger = logger
                self.config = config

        # Register dependencies
        logger_service = MockService("logger")
        config_service = MockService("config")
        self.registry.register_singleton("logger", logger_service)
        self.registry.register_singleton("config", config_service)

        # Register class service with dependencies
        self.registry.register_class(
            "service_with_deps", ServiceWithDeps, ["logger", "config"]
        )

        # Get service and verify dependencies were injected
        service = self.registry.get("service_with_deps")
        assert service.logger is logger_service
        assert service.config is config_service

    def test_dependency_extraction_from_constructor(self):
        """Test automatic dependency extraction from class constructor."""

        class ServiceWithDeps:
            def __init__(self, logger, config, optional_param="default"):
                self.logger = logger
                self.config = config
                self.optional_param = optional_param

        # Register without explicit dependencies - should auto-detect
        self.registry.register_class("auto_deps_service", ServiceWithDeps)

        service_info = self.registry.get_service_info("auto_deps_service")
        # Should extract required parameters (those without defaults)
        assert "logger" in service_info.dependencies
        assert "config" in service_info.dependencies
        assert "optional_param" not in service_info.dependencies  # Has default value

    # Circular Dependency Detection Tests

    def test_circular_dependency_detection_direct(self):
        """Test detection of direct circular dependencies."""

        # Create services with circular dependencies
        def factory_a():
            return self.registry.get("service_b")  # A depends on B

        def factory_b():
            return self.registry.get("service_a")  # B depends on A

        self.registry.register_factory("service_a", factory_a, ["service_b"])
        self.registry.register_factory("service_b", factory_b, ["service_a"])

        with pytest.raises(ServiceInitializationError) as exc_info:
            self.registry.get("service_a")

        assert "Circular dependency detected" in str(exc_info.value)

    def test_circular_dependency_detection_indirect(self):
        """Test detection of indirect circular dependencies (A -> B -> C -> A)."""

        def factory_a():
            return self.registry.get("service_b")

        def factory_b():
            return self.registry.get("service_c")

        def factory_c():
            return self.registry.get("service_a")

        self.registry.register_factory("service_a", factory_a, ["service_b"])
        self.registry.register_factory("service_b", factory_b, ["service_c"])
        self.registry.register_factory("service_c", factory_c, ["service_a"])

        with pytest.raises(ServiceInitializationError) as exc_info:
            self.registry.get("service_a")

        assert "Circular dependency detected" in str(exc_info.value)

    def test_validate_dependencies_circular(self):
        """Test dependency validation detects circular dependencies."""
        self.registry.register_factory("service_a", lambda: None, ["service_b"])
        self.registry.register_factory("service_b", lambda: None, ["service_a"])

        errors = self.registry.validate_dependencies()

        assert len(errors) > 0
        assert any("Circular dependency detected" in error for error in errors)

    def test_validate_dependencies_missing(self):
        """Test dependency validation detects missing dependencies."""
        self.registry.register_factory("service_a", lambda: None, ["missing_service"])

        errors = self.registry.validate_dependencies()

        assert len(errors) > 0
        assert any(
            "depends on unregistered service 'missing_service'" in error
            for error in errors
        )

    def test_validate_dependencies_success(self):
        """Test dependency validation passes for valid dependencies."""
        self.registry.register_singleton("service_b", MockService("service_b"))
        self.registry.register_factory("service_a", lambda: None, ["service_b"])

        errors = self.registry.validate_dependencies()

        assert len(errors) == 0

    # Service Validation and Health Checking Tests

    def test_health_check_single_service(self):
        """Test health check for a single service."""
        service = MockService("test_service")
        service.set_healthy(True)
        self.registry.register_singleton("test_service", service)

        health_status = self.registry.health_check("test_service")

        assert health_status == {"test_service": True}

    def test_health_check_unhealthy_service(self):
        """Test health check for an unhealthy service."""
        service = MockService("test_service")
        service.set_healthy(False)
        self.registry.register_singleton("test_service", service)

        health_status = self.registry.health_check("test_service")

        assert health_status == {"test_service": False}

    def test_health_check_all_services(self):
        """Test health check for all services."""
        service1 = MockService("service1")
        service1.set_healthy(True)
        service2 = MockService("service2")
        service2.set_healthy(False)

        self.registry.register_singleton("service1", service1)
        self.registry.register_singleton("service2", service2)

        health_status = self.registry.health_check()

        assert health_status == {"service1": True, "service2": False}

    def test_health_check_nonexistent_service(self):
        """Test health check for non-existent service."""
        health_status = self.registry.health_check("nonexistent")

        assert health_status == {"nonexistent": False}

    def test_health_check_service_without_method(self):
        """Test health check for service without health_check method."""
        # Create a simple object without health_check method
        simple_service = object()
        self.registry.register_singleton("simple_service", simple_service)

        health_status = self.registry.health_check("simple_service")

        # Should consider it healthy if initialized (no health_check method)
        assert health_status == {"simple_service": True}

    def test_health_check_with_exception(self):
        """Test health check when service health_check method raises exception."""
        service = MockService("test_service")

        # Mock health_check to raise exception
        def failing_health_check():
            raise RuntimeError("Health check failed")

        service.health_check = failing_health_check
        self.registry.register_singleton("test_service", service)

        health_status = self.registry.health_check("test_service")

        assert health_status == {"test_service": False}

        # Check that error message is stored
        service_info = self.registry.get_service_info("test_service")
        assert "Health check failed" in service_info.error_message

    # Service Lifecycle Tests

    def test_service_lifecycle_states(self):
        """Test service lifecycle state transitions."""

        def factory():
            return MockService("lifecycle_service")

        self.registry.register_factory("lifecycle_service", factory)

        # Initially registered
        service_info = self.registry.get_service_info("lifecycle_service")
        assert service_info.lifecycle == ServiceLifecycle.REGISTERED

        # After creation, should be initialized
        self.registry.get("lifecycle_service")
        service_info = self.registry.get_service_info("lifecycle_service")
        assert service_info.lifecycle == ServiceLifecycle.INITIALIZED

    def test_service_initialization_failure(self):
        """Test service lifecycle when initialization fails."""

        def failing_factory():
            raise ValueError("Initialization failed")

        self.registry.register_factory("failing_service", failing_factory)

        with pytest.raises(ServiceInitializationError):
            self.registry.get("failing_service")

        service_info = self.registry.get_service_info("failing_service")
        assert service_info.lifecycle == ServiceLifecycle.FAILED
        assert "Initialization failed" in service_info.error_message

    def test_shutdown_all_services(self):
        """Test shutting down all services."""
        service1 = MockService("service1")
        service2 = MockService("service2")

        self.registry.register_singleton("service1", service1)
        self.registry.register_singleton("service2", service2)

        self.registry.shutdown_all()

        assert service1._shutdown_called
        assert service2._shutdown_called

        # Check lifecycle states
        service_info1 = self.registry.get_service_info("service1")
        service_info2 = self.registry.get_service_info("service2")
        assert service_info1.lifecycle == ServiceLifecycle.SHUTDOWN
        assert service_info2.lifecycle == ServiceLifecycle.SHUTDOWN

    def test_shutdown_service_without_method(self):
        """Test shutdown for service without shutdown method."""
        simple_service = object()
        self.registry.register_singleton("simple_service", simple_service)

        # Should not raise exception
        self.registry.shutdown_all()

    def test_shutdown_with_exception(self):
        """Test shutdown when service shutdown method raises exception."""
        service = MockService("test_service")

        def failing_shutdown():
            raise RuntimeError("Shutdown failed")

        service.shutdown = failing_shutdown
        self.registry.register_singleton("test_service", service)

        # Should not raise exception, just log error
        self.registry.shutdown_all()

    # Utility Method Tests

    def test_has_service(self):
        """Test checking if service exists."""
        assert not self.registry.has("nonexistent")

        self.registry.register_singleton("test_service", MockService())
        assert self.registry.has("test_service")

    def test_list_services(self):
        """Test listing all registered services."""
        assert self.registry.list_services() == []

        self.registry.register_singleton("service1", MockService())
        self.registry.register_factory("service2", lambda: MockService())

        services = self.registry.list_services()
        assert "service1" in services
        assert "service2" in services
        assert len(services) == 2

    def test_get_service_info_nonexistent(self):
        """Test getting service info for non-existent service."""
        assert self.registry.get_service_info("nonexistent") is None

    def test_get_nonexistent_service(self):
        """Test getting non-existent service raises appropriate error."""
        with pytest.raises(ServiceNotFoundError) as exc_info:
            self.registry.get("nonexistent")

        assert "Service 'nonexistent' not registered" in str(exc_info.value)

    # ConfigurableService Integration Tests

    def test_configurable_service_integration(self):
        """Test integration with ConfigurableService."""
        config = {"setting1": "value1", "setting2": 42}
        service = MockConfigurableService(config, "configurable_service")

        self.registry.register_singleton("configurable_service", service)

        retrieved = self.registry.get("configurable_service")
        assert retrieved is service
        assert retrieved.get_config("setting1") == "value1"
        assert retrieved.get_config("setting2") == 42

    def test_configurable_service_health_check(self):
        """Test health check integration with ConfigurableService."""
        config = {}
        service = MockConfigurableService(config, "configurable_service")

        # Initialize the service first
        service.initialize()

        self.registry.register_singleton("configurable_service", service)

        # Service should be healthy after initialization
        health_status = self.registry.health_check("configurable_service")
        assert health_status == {"configurable_service": True}


class TestGlobalRegistry:
    """Test cases for global registry functions."""

    def teardown_method(self):
        """Clean up after each test method."""
        reset_registry()

    def test_get_global_registry(self):
        """Test getting the global registry instance."""
        registry1 = get_registry()
        registry2 = get_registry()

        # Should return the same instance
        assert registry1 is registry2
        assert isinstance(registry1, ServiceRegistry)

    def test_reset_global_registry(self):
        """Test resetting the global registry."""
        registry1 = get_registry()
        registry1.register_singleton("test_service", MockService())

        assert registry1.has("test_service")

        reset_registry()

        registry2 = get_registry()
        # Should be a new instance
        assert registry2 is not registry1
        assert not registry2.has("test_service")

    def test_reset_calls_shutdown(self):
        """Test that reset_registry calls shutdown on existing registry."""
        registry = get_registry()
        service = MockService("test_service")
        registry.register_singleton("test_service", service)

        reset_registry()

        # Service should have been shut down
        assert service._shutdown_called


class TestServiceRegistryEdgeCases:
    """Test edge cases and error conditions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.registry = ServiceRegistry()

    def test_register_duplicate_service_name(self):
        """Test registering multiple services with the same name."""
        service1 = MockService("service1")
        service2 = MockService("service2")

        self.registry.register_singleton("duplicate_name", service1)
        # Should overwrite the first registration
        self.registry.register_singleton("duplicate_name", service2)

        retrieved = self.registry.get("duplicate_name")
        assert retrieved is service2

    def test_empty_dependencies_list(self):
        """Test service with empty dependencies list."""
        self.registry.register_factory("no_deps", lambda: MockService(), [])

        service_info = self.registry.get_service_info("no_deps")
        assert service_info.dependencies == []

        errors = self.registry.validate_dependencies()
        assert len(errors) == 0

    def test_none_dependencies(self):
        """Test service with None dependencies."""
        self.registry.register_factory("none_deps", lambda: MockService(), None)

        service_info = self.registry.get_service_info("none_deps")
        assert service_info.dependencies == []

    def test_class_with_no_constructor_params(self):
        """Test class service with no constructor parameters."""

        class SimpleClass:
            def __init__(self):
                pass

        self.registry.register_class("simple_class", SimpleClass)

        service_info = self.registry.get_service_info("simple_class")
        assert service_info.dependencies == []

        instance = self.registry.get("simple_class")
        assert isinstance(instance, SimpleClass)

    def test_class_with_complex_constructor(self):
        """Test class service with complex constructor signature."""

        class ComplexClass:
            def __init__(self, required_param, optional_param="default"):
                self.required_param = required_param
                self.optional_param = optional_param

        self.registry.register_class("complex_class", ComplexClass)

        service_info = self.registry.get_service_info("complex_class")
        # Should only extract required parameters
        assert service_info.dependencies == ["required_param"]

    @patch("app.core.registry.logging.getLogger")
    def test_logging_integration(self, mock_get_logger):
        """Test that registry properly logs operations."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        registry = ServiceRegistry()
        service = MockService("test_service")

        registry.register_singleton("test_service", service)

        # Verify debug logging was called
        mock_logger.debug.assert_called_with(
            "Registered singleton service: test_service"
        )

    @patch("app.core.registry.inspect.signature")
    def test_dependency_extraction_error_handling(self, mock_signature):
        """Test error handling in dependency extraction."""
        # Make inspect.signature raise an exception
        mock_signature.side_effect = ValueError("Signature extraction failed")

        class ProblematicClass:
            def __init__(self, param1, param2):
                pass

        # This should not raise an exception, just return empty list
        self.registry.register_class("problematic_class", ProblematicClass)

        service_info = self.registry.get_service_info("problematic_class")
        assert service_info.dependencies == []

    def test_factory_service_direct_call_error(self):
        """Test error handling in the direct factory call path."""

        def failing_factory():
            raise RuntimeError("Direct factory failure")

        self.registry.register_factory("direct_fail_service", failing_factory)

        # Manually set the instance to a non-None value to trigger the direct factory call path
        service_info = self.registry.get_service_info("direct_fail_service")
        service_info.instance = MockService(
            "dummy"
        )  # This forces the direct factory call path

        # Now the call should go through the direct factory call path and fail
        with pytest.raises(ServiceInitializationError) as exc_info:
            self.registry.get("direct_fail_service")

        assert "Failed to create factory instance 'direct_fail_service'" in str(
            exc_info.value
        )
        assert "Direct factory failure" in str(exc_info.value)

    def test_service_info_shared_reference(self):
        """Test that service info returns the same object reference."""
        original_deps = ["dep1", "dep2"]
        self.registry.register_factory(
            "test_service", lambda: MockService(), original_deps
        )

        service_info1 = self.registry.get_service_info("test_service")
        service_info2 = self.registry.get_service_info("test_service")

        # Should return the same object reference
        assert service_info1 is service_info2

        # Modifying one affects the other (shared reference)
        service_info1.dependencies.append("dep3")
        assert service_info2.dependencies == ["dep1", "dep2", "dep3"]
