"""
Unit tests for the Import Manager.

Tests cover:
- Safe import functionality
- Service requirement and optional service patterns
- Error handling for import failures
- Service resolution through registry
"""

import pytest
from unittest.mock import Mock, patch

from app.utils.imports import (
    ImportManager,
    ServiceRequiredError,
    ImportError as CustomImportError,
    get_import_manager,
    reset_import_manager,
    safe_import,
    require_service,
    optional_service,
    is_available,
    try_import_service,
    import_optional_dependency,
    require_dependency,
    create_fallback_service,
)
from app.core.registry import ServiceNotFoundError, get_registry, reset_registry


class MockModule:
    """Mock module for testing imports."""

    def __init__(self, name: str = "mock_module"):
        self.name = name
        self.MockClass = type(f"MockClass_{name}", (), {"module_name": name})


class MockService:
    """Mock service for testing service resolution."""

    def __init__(self, name: str = "mock_service"):
        self.name = name
        self.initialized = True

    def health_check(self) -> bool:
        return True


class TestImportManager:
    """Test cases for ImportManager class."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.import_manager = ImportManager()
        # Clear any existing registry
        reset_registry()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_import_manager()
        reset_registry()

    # Safe Import Functionality Tests

    def test_safe_import_successful_module(self):
        """Test successful module import."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("test_module")
            mock_import.return_value = mock_module

            result = self.import_manager.safe_import("test_module")

            assert result is mock_module
            mock_import.assert_called_once_with("test_module")

    def test_safe_import_successful_class(self):
        """Test successful class import from module."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("test_module")
            mock_import.return_value = mock_module

            result = self.import_manager.safe_import("test_module", "MockClass")

            assert result is mock_module.MockClass
            mock_import.assert_called_once_with("test_module")

    def test_safe_import_module_not_found(self):
        """Test safe import when module is not found."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("No module named 'nonexistent'")

            result = self.import_manager.safe_import("nonexistent")

            assert result is None
            mock_import.assert_called_once_with("nonexistent")

    def test_safe_import_class_not_found(self):
        """Test safe import when class is not found in module."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("test_module")
            mock_import.return_value = mock_module

            result = self.import_manager.safe_import("test_module", "NonexistentClass")

            assert result is None
            mock_import.assert_called_once_with("test_module")

    def test_safe_import_with_context(self):
        """Test safe import with context information."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            result = self.import_manager.safe_import(
                "test_module", context="Testing context"
            )

            assert result is None
            # Verify context is used in logging (check via failed imports cache)
            failed_imports = self.import_manager.get_import_status()["failed_imports"]
            assert "test_module" in failed_imports
            assert "Testing context" in failed_imports["test_module"]

    def test_safe_import_caching_enabled(self):
        """Test that successful imports are cached when caching is enabled."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("cached_module")
            mock_import.return_value = mock_module

            # First call
            result1 = self.import_manager.safe_import("cached_module", cache=True)
            # Second call
            result2 = self.import_manager.safe_import("cached_module", cache=True)

            assert result1 is mock_module
            assert result2 is mock_module
            # importlib.import_module should only be called once due to caching
            mock_import.assert_called_once_with("cached_module")

    def test_safe_import_caching_disabled(self):
        """Test that imports are not cached when caching is disabled."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("uncached_module")
            mock_import.return_value = mock_module

            # First call
            result1 = self.import_manager.safe_import("uncached_module", cache=False)
            # Second call
            result2 = self.import_manager.safe_import("uncached_module", cache=False)

            assert result1 is mock_module
            assert result2 is mock_module
            # importlib.import_module should be called twice (no caching)
            assert mock_import.call_count == 2

    def test_safe_import_failed_import_caching(self):
        """Test that failed imports are cached to avoid repeated attempts."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            # First call
            result1 = self.import_manager.safe_import("failed_module")
            # Second call
            result2 = self.import_manager.safe_import("failed_module")

            assert result1 is None
            assert result2 is None
            # importlib.import_module should only be called once due to failure caching
            mock_import.assert_called_once_with("failed_module")

    def test_safe_import_unexpected_error(self):
        """Test safe import handling of unexpected errors."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ValueError("Unexpected error")

            result = self.import_manager.safe_import("error_module")

            assert result is None
            # Error should be cached
            failed_imports = self.import_manager.get_import_status()["failed_imports"]
            assert "error_module" in failed_imports
            assert "Unexpected error" in failed_imports["error_module"]

    # Service Resolution Tests

    def test_require_service_success(self):
        """Test successful service requirement."""
        # Register a service in the registry
        registry = get_registry()
        mock_service = MockService("test_service")
        registry.register_singleton("test_service", mock_service)

        result = self.import_manager.require_service("test_service")

        assert result is mock_service

    def test_require_service_not_registered(self):
        """Test require_service when service is not registered."""
        with pytest.raises(ServiceRequiredError) as exc_info:
            self.import_manager.require_service("nonexistent_service")

        assert "Required service 'nonexistent_service' is not registered" in str(
            exc_info.value
        )
        assert exc_info.value.service_name == "nonexistent_service"

    def test_require_service_with_context(self):
        """Test require_service with context information."""
        with pytest.raises(ServiceRequiredError) as exc_info:
            self.import_manager.require_service(
                "nonexistent_service", context="Test context"
            )

        assert "Test context" in str(exc_info.value)

    def test_require_service_resolution_error(self):
        """Test require_service when service resolution fails."""
        registry = get_registry()

        # Mock the registry to raise ServiceNotFoundError
        with patch.object(registry, "has", return_value=True), patch.object(
            registry,
            "get",
            side_effect=ServiceNotFoundError("Service resolution failed"),
        ):

            with pytest.raises(ServiceRequiredError) as exc_info:
                self.import_manager.require_service("failing_service")

            assert "could not be resolved" in str(exc_info.value)

    def test_require_service_unexpected_error(self):
        """Test require_service handling of unexpected errors."""
        registry = get_registry()

        # Mock the registry to raise unexpected error
        with patch.object(
            registry, "has", side_effect=RuntimeError("Unexpected error")
        ):

            with pytest.raises(ServiceRequiredError) as exc_info:
                self.import_manager.require_service("error_service")

            assert "Unexpected error resolving required service" in str(exc_info.value)

    def test_optional_service_success(self):
        """Test successful optional service resolution."""
        registry = get_registry()
        mock_service = MockService("optional_service")
        registry.register_singleton("optional_service", mock_service)

        result = self.import_manager.optional_service("optional_service")

        assert result is mock_service

    def test_optional_service_not_available(self):
        """Test optional_service when service is not available."""
        result = self.import_manager.optional_service("nonexistent_service")

        assert result is None

    def test_optional_service_with_default(self):
        """Test optional_service with custom default value."""
        default_value = "custom_default"

        result = self.import_manager.optional_service(
            "nonexistent_service", default=default_value
        )

        assert result == default_value

    def test_optional_service_with_context(self):
        """Test optional_service with context information."""
        # This should not raise an error, just log the context
        result = self.import_manager.optional_service(
            "nonexistent_service", context="Test context"
        )

        assert result is None

    def test_optional_service_resolution_error(self):
        """Test optional_service when service resolution fails."""
        registry = get_registry()

        # Mock the registry to raise an error during get()
        with patch.object(registry, "has", return_value=True), patch.object(
            registry, "get", side_effect=RuntimeError("Resolution error")
        ):

            result = self.import_manager.optional_service(
                "failing_service", default="fallback"
            )

            assert result == "fallback"

    # Service Import and Registration Tests

    def test_try_import_service_success_class(self):
        """Test successful import and registration of a class service."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("service_module")
            mock_import.return_value = mock_module

            result = self.import_manager.try_import_service(
                "service_module", "imported_service", "MockClass"
            )

            assert result is True

            # Verify service was registered
            registry = get_registry()
            assert registry.has("imported_service")

    def test_try_import_service_success_module(self):
        """Test successful import and registration of a module service."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("service_module")
            mock_import.return_value = mock_module

            result = self.import_manager.try_import_service(
                "service_module", "imported_service"
            )

            assert result is True

            # Verify service was registered
            registry = get_registry()
            assert registry.has("imported_service")

    def test_try_import_service_with_factory_args(self):
        """Test import service with factory arguments."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("service_module")
            mock_import.return_value = mock_module

            factory_args = {"arg1": "value1", "arg2": "value2"}

            result = self.import_manager.try_import_service(
                "service_module", "imported_service", "MockClass", factory_args
            )

            assert result is True

            # Verify service was registered and can be created
            registry = get_registry()
            assert registry.has("imported_service")

    def test_try_import_service_import_failure(self):
        """Test try_import_service when import fails."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            result = self.import_manager.try_import_service(
                "nonexistent_module", "failed_service"
            )

            assert result is False

            # Verify service was not registered
            registry = get_registry()
            assert not registry.has("failed_service")

    def test_try_import_service_registration_failure(self):
        """Test try_import_service when registration fails."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("service_module")
            mock_import.return_value = mock_module

            registry = get_registry()

            # Mock registry to raise error during registration
            with patch.object(
                registry,
                "register_factory",
                side_effect=RuntimeError("Registration failed"),
            ):

                result = self.import_manager.try_import_service(
                    "service_module", "failing_service", "MockClass"
                )

                assert result is False

    # Utility Method Tests

    def test_is_available_cached_success(self):
        """Test is_available for cached successful import."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("available_module")
            mock_import.return_value = mock_module

            # First import to cache it
            self.import_manager.safe_import("available_module")

            # Check availability (should use cache)
            result = self.import_manager.is_available("available_module")

            assert result is True
            # Should only call import_module once (from the first safe_import)
            mock_import.assert_called_once()

    def test_is_available_cached_failure(self):
        """Test is_available for cached failed import."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            # First import to cache the failure
            self.import_manager.safe_import("unavailable_module")

            # Check availability (should use cache)
            result = self.import_manager.is_available("unavailable_module")

            assert result is False
            # Should only call import_module once (from the first safe_import)
            mock_import.assert_called_once()

    def test_is_available_fresh_check(self):
        """Test is_available for fresh import check."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("fresh_module")
            mock_import.return_value = mock_module

            # Check availability without prior caching
            result = self.import_manager.is_available("fresh_module")

            assert result is True
            mock_import.assert_called_once_with("fresh_module")

    def test_is_available_with_class(self):
        """Test is_available for class within module."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("module_with_class")
            mock_import.return_value = mock_module

            result = self.import_manager.is_available("module_with_class", "MockClass")

            assert result is True

    def test_is_available_class_not_found(self):
        """Test is_available when class is not found in module."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("module_without_class")
            mock_import.return_value = mock_module

            result = self.import_manager.is_available(
                "module_without_class", "NonexistentClass"
            )

            assert result is False

    def test_get_import_status(self):
        """Test getting import status information."""
        with patch("importlib.import_module") as mock_import:
            # Set up successful and failed imports
            mock_module = MockModule("success_module")
            mock_import.side_effect = [mock_module, ImportError("Failed import")]

            # Successful import
            self.import_manager.safe_import("success_module")
            # Failed import
            self.import_manager.safe_import("failed_module")

            status = self.import_manager.get_import_status()

            assert "success_module" in status["successful_imports"]
            assert "failed_module" in status["failed_imports"]
            assert status["cache_size"] == 1
            assert status["failed_count"] == 1

    def test_clear_cache(self):
        """Test clearing the import cache."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("cached_module")
            mock_import.return_value = mock_module

            # Import and cache
            self.import_manager.safe_import("cached_module")
            # Fail and cache
            mock_import.side_effect = ImportError("Failed")
            self.import_manager.safe_import("failed_module")

            # Verify cache has content
            status = self.import_manager.get_import_status()
            assert status["cache_size"] > 0
            assert status["failed_count"] > 0

            # Clear cache
            self.import_manager.clear_cache()

            # Verify cache is empty
            status = self.import_manager.get_import_status()
            assert status["cache_size"] == 0
            assert status["failed_count"] == 0

    def test_clear_failed_imports(self):
        """Test clearing only failed imports cache."""
        with patch("importlib.import_module") as mock_import:
            # Successful import
            mock_module = MockModule("success_module")
            mock_import.return_value = mock_module
            self.import_manager.safe_import("success_module")

            # Failed import
            mock_import.side_effect = ImportError("Failed")
            self.import_manager.safe_import("failed_module")

            # Clear only failed imports
            self.import_manager.clear_failed_imports()

            status = self.import_manager.get_import_status()
            assert status["cache_size"] == 1  # Successful import still cached
            assert status["failed_count"] == 0  # Failed imports cleared

    # Registry Integration Tests

    def test_registry_lazy_initialization(self):
        """Test that registry is lazily initialized."""
        # Create new import manager
        import_manager = ImportManager()

        # Registry should be None initially
        assert import_manager._registry is None

        # Accessing registry property should initialize it
        registry = import_manager.registry
        assert registry is not None
        assert import_manager._registry is registry

        # Subsequent access should return same instance
        assert import_manager.registry is registry


class TestGlobalImportManagerFunctions:
    """Test cases for global import manager functions."""

    def teardown_method(self):
        """Clean up after each test method."""
        reset_import_manager()
        reset_registry()

    def test_get_import_manager_singleton(self):
        """Test that get_import_manager returns singleton instance."""
        manager1 = get_import_manager()
        manager2 = get_import_manager()

        assert manager1 is manager2
        assert isinstance(manager1, ImportManager)

    def test_reset_import_manager(self):
        """Test resetting the global import manager."""
        manager1 = get_import_manager()

        reset_import_manager()

        manager2 = get_import_manager()
        assert manager2 is not manager1

    def test_safe_import_convenience_function(self):
        """Test safe_import convenience function."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("convenience_module")
            mock_import.return_value = mock_module

            result = safe_import("convenience_module")

            assert result is mock_module

    def test_require_service_convenience_function(self):
        """Test require_service convenience function."""
        registry = get_registry()
        mock_service = MockService("convenience_service")
        registry.register_singleton("convenience_service", mock_service)

        result = require_service("convenience_service")

        assert result is mock_service

    def test_optional_service_convenience_function(self):
        """Test optional_service convenience function."""
        result = optional_service("nonexistent_service", default="default_value")

        assert result == "default_value"

    def test_is_available_convenience_function(self):
        """Test is_available convenience function."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("available_module")
            mock_import.return_value = mock_module

            result = is_available("available_module")

            assert result is True

    def test_try_import_service_convenience_function(self):
        """Test try_import_service convenience function."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("service_module")
            mock_import.return_value = mock_module

            result = try_import_service("service_module", "test_service")

            assert result is True


class TestUtilityFunctions:
    """Test cases for utility functions."""

    def teardown_method(self):
        """Clean up after each test method."""
        reset_import_manager()
        reset_registry()

    def test_import_optional_dependency_success(self):
        """Test successful optional dependency import."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("optional_dep")
            mock_import.return_value = mock_module

            result = import_optional_dependency(
                "optional_dep", feature_name="Optional Feature"
            )

            assert result is mock_module

    def test_import_optional_dependency_failure(self):
        """Test optional dependency import failure."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            result = import_optional_dependency(
                "missing_dep", feature_name="Missing Feature"
            )

            assert result is None

    def test_require_dependency_success(self):
        """Test successful required dependency import."""
        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("required_dep")
            mock_import.return_value = mock_module

            result = require_dependency("required_dep", feature_name="Required Feature")

            assert result is mock_module

    def test_require_dependency_failure(self):
        """Test required dependency import failure."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            with pytest.raises(CustomImportError) as exc_info:
                require_dependency("missing_required", feature_name="Required Feature")

            assert "Required dependency 'missing_required' is not available" in str(
                exc_info.value
            )
            assert "pip install missing_required" in str(exc_info.value)

    def test_require_dependency_with_installation_hint(self):
        """Test required dependency failure with custom installation hint."""
        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            with pytest.raises(CustomImportError) as exc_info:
                require_dependency(
                    "custom_dep",
                    feature_name="Custom Feature",
                    installation_hint="conda install custom_dep",
                )

            assert "conda install custom_dep" in str(exc_info.value)

    def test_create_fallback_service_primary_available(self):
        """Test fallback service when primary service is available."""
        registry = get_registry()
        primary_service = MockService("primary")
        registry.register_singleton("primary_service", primary_service)

        result = create_fallback_service("primary_service", "fallback_service")

        assert result is primary_service

    def test_create_fallback_service_fallback_used(self):
        """Test fallback service when primary is not available but fallback is."""
        registry = get_registry()
        fallback_service = MockService("fallback")
        registry.register_singleton("fallback_service", fallback_service)

        result = create_fallback_service("primary_service", "fallback_service")

        assert result is fallback_service

    def test_create_fallback_service_neither_available(self):
        """Test fallback service when neither primary nor fallback is available."""
        with pytest.raises(ServiceRequiredError) as exc_info:
            create_fallback_service("primary_service", "fallback_service")

        assert (
            "Neither primary service 'primary_service' nor fallback service 'fallback_service'"
            in str(exc_info.value)
        )


class TestErrorHandling:
    """Test cases for error handling scenarios."""

    def teardown_method(self):
        """Clean up after each test method."""
        reset_import_manager()
        reset_registry()

    def test_service_required_error_creation(self):
        """Test ServiceRequiredError creation and attributes."""
        error = ServiceRequiredError("test_service", "Custom error message")

        assert error.service_name == "test_service"
        assert str(error) == "Custom error message"

    def test_service_required_error_default_message(self):
        """Test ServiceRequiredError with default message."""
        error = ServiceRequiredError("test_service")

        assert error.service_name == "test_service"
        assert "Required service 'test_service' is not available" in str(error)

    def test_custom_import_error_creation(self):
        """Test CustomImportError creation and attributes."""
        original_error = ImportError("Original error")
        error = CustomImportError("test_module", original_error, "Test context")

        assert error.module_name == "test_module"
        assert error.original_error is original_error
        assert error.context == "Test context"
        assert "Failed to import 'test_module'" in str(error)
        assert "Original error" in str(error)
        assert "Test context" in str(error)

    def test_custom_import_error_without_context(self):
        """Test CustomImportError without context."""
        original_error = ImportError("Original error")
        error = CustomImportError("test_module", original_error)

        assert error.context is None
        assert "Failed to import 'test_module'" in str(error)
        assert "Original error" in str(error)


class TestEdgeCases:
    """Test edge cases and boundary conditions."""

    def setup_method(self):
        """Set up test fixtures before each test method."""
        self.import_manager = ImportManager()

    def teardown_method(self):
        """Clean up after each test method."""
        reset_import_manager()
        reset_registry()

    def test_safe_import_empty_module_name(self):
        """Test safe import with empty module name."""
        result = self.import_manager.safe_import("")

        assert result is None

    def test_safe_import_none_module_name(self):
        """Test safe import with None module name."""
        result = self.import_manager.safe_import(None)

        assert result is None

    def test_require_service_empty_name(self):
        """Test require_service with empty service name."""
        with pytest.raises(ServiceRequiredError):
            self.import_manager.require_service("")

    def test_optional_service_empty_name(self):
        """Test optional_service with empty service name."""
        result = self.import_manager.optional_service("", default="default")

        assert result == "default"

    def test_safe_import_with_very_long_module_name(self):
        """Test safe import with very long module name."""
        long_name = "a" * 1000

        with patch("importlib.import_module") as mock_import:
            mock_import.side_effect = ImportError("Module not found")

            result = self.import_manager.safe_import(long_name)

            assert result is None

    def test_multiple_import_managers(self):
        """Test behavior with multiple ImportManager instances."""
        manager1 = ImportManager()
        manager2 = ImportManager()

        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("shared_module")
            mock_import.return_value = mock_module

            # Import with first manager
            result1 = manager1.safe_import("shared_module")
            # Import with second manager
            result2 = manager2.safe_import("shared_module")

            assert result1 is mock_module
            assert result2 is mock_module
            # Each manager should have its own cache
            assert mock_import.call_count == 2

    def test_concurrent_access_simulation(self):
        """Test simulated concurrent access to import manager."""
        import threading

        results = []
        errors = []

        def import_worker(module_name):
            try:
                with patch("importlib.import_module") as mock_import:
                    mock_module = MockModule(module_name)
                    mock_import.return_value = mock_module

                    result = self.import_manager.safe_import(module_name)
                    results.append(result)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=import_worker, args=(f"module_{i}",))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify no errors occurred
        assert len(errors) == 0
        assert len(results) == 5

    @patch("app.utils.imports.logging.getLogger")
    def test_logging_integration(self, mock_get_logger):
        """Test that import manager properly logs operations."""
        mock_logger = Mock()
        mock_get_logger.return_value = mock_logger

        import_manager = ImportManager()

        with patch("importlib.import_module") as mock_import:
            mock_module = MockModule("logged_module")
            mock_import.return_value = mock_module

            import_manager.safe_import("logged_module")

            # Verify debug logging was called
            mock_logger.debug.assert_called()

    def test_registry_property_multiple_access(self):
        """Test multiple accesses to registry property."""
        registry1 = self.import_manager.registry
        registry2 = self.import_manager.registry

        # Should return the same instance
        assert registry1 is registry2

    def test_import_status_with_empty_caches(self):
        """Test get_import_status with empty caches."""
        status = self.import_manager.get_import_status()

        assert status["successful_imports"] == []
        assert status["failed_imports"] == {}
        assert status["cache_size"] == 0
        assert status["failed_count"] == 0
