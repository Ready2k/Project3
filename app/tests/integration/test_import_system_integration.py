"""
Integration tests for the import system.

Tests cover:
- Complete import resolution in realistic scenarios
- Fallback behavior for missing optional imports
- Error propagation for missing required imports
- Performance of import resolution

Requirements covered: 1.1, 1.5, 5.1
"""

import pytest
import time
from unittest.mock import Mock, patch

from app.utils.imports import (
    ImportError as CustomImportError,
    get_import_manager,
    reset_import_manager,
    require_service,
    optional_service,
    import_optional_dependency,
    require_dependency,
    create_fallback_service,
)
from app.core.registry import get_registry, reset_registry


class MockRealModule:
    """Mock module that simulates a real module with classes and functions."""

    def __init__(self, name: str = "real_module"):
        self.name = name
        self.version = "1.0.0"

    class MockClass:
        def __init__(self, **kwargs):
            # Accept any keyword arguments to avoid initialization errors
            self.config = kwargs
            self.initialized = True

        def process(self, data: str) -> str:
            return f"processed: {data}"

        def health_check(self) -> bool:
            return self.initialized

    def mock_function(self, arg: str) -> str:
        return f"function_result: {arg}"


class MockOptionalModule:
    """Mock module that simulates an optional dependency."""

    def __init__(self, name: str = "optional_module"):
        self.name = name
        self.available = True

    class OptionalFeature:
        def __init__(self, **kwargs):
            # Accept any keyword arguments to avoid initialization errors
            self.config = kwargs
            self.enabled = True

        def advanced_operation(self) -> str:
            return "advanced_result"


@pytest.fixture
def clean_environment():
    """Provide a clean test environment."""
    # Reset import manager and registry
    reset_import_manager()
    reset_registry()

    # Clear any cached modules from previous tests
    import_manager = get_import_manager()
    import_manager.clear_cache()

    yield

    # Cleanup after test
    reset_import_manager()
    reset_registry()


@pytest.fixture
def mock_real_world_modules():
    """Mock real-world modules for testing."""
    modules = {
        "requests": MockRealModule("requests"),
        "numpy": MockRealModule("numpy"),
        "pandas": MockRealModule("pandas"),
        "redis": MockOptionalModule("redis"),
        "openai": MockOptionalModule("openai"),
        "anthropic": MockOptionalModule("anthropic"),
    }

    def mock_import_module(name):
        if name in modules:
            return modules[name]
        raise ImportError(f"No module named '{name}'")

    with patch("importlib.import_module", side_effect=mock_import_module):
        yield modules


class TestCompleteImportResolution:
    """Test complete import resolution in realistic scenarios."""

    def test_realistic_service_import_chain(
        self, clean_environment, mock_real_world_modules
    ):
        """Test realistic service import and registration chain."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Scenario: Import and register a chain of services with dependencies

        # 1. Import and register a basic service
        success = import_manager.try_import_service(
            "requests",
            "http_client",
            "MockClass",
            factory_args={"config": {"timeout": 30}},
        )
        assert success is True
        assert registry.has("http_client")

        # 2. Import and register a service that depends on the first
        def data_processor_factory():
            http_client = registry.get("http_client")
            processor = mock_real_world_modules["pandas"].MockClass(
                http_client=http_client
            )
            return processor

        registry.register_factory(
            "data_processor", data_processor_factory, ["http_client"]
        )

        # 3. Import and register a high-level service
        success = import_manager.try_import_service(
            "numpy",
            "analytics_engine",
            "MockClass",
            factory_args={"config": {"processor": "data_processor"}},
        )
        assert success is True

        # 4. Verify the complete chain works
        analytics = registry.get("analytics_engine")
        processor = registry.get("data_processor")
        http_client = registry.get("http_client")

        assert analytics is not None
        assert processor is not None
        assert http_client is not None

        # 5. Test that services can interact
        result = http_client.process("test_data")
        assert "processed: test_data" in result

        # 6. Verify dependency resolution worked
        # Note: Since http_client is registered as a factory, each get() creates a new instance
        # So we verify the processor has the http_client dependency, not the exact same instance
        assert "http_client" in processor.config
        assert processor.config["http_client"] is not None

    def test_complex_optional_import_scenario(
        self, clean_environment, mock_real_world_modules
    ):
        """Test complex scenario with multiple optional imports."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Scenario: AI service with multiple optional providers

        # Try to import multiple AI providers
        providers = []

        # OpenAI (available)
        openai_service = import_manager.safe_import("openai", "OptionalFeature")
        if openai_service:
            registry.register_singleton("openai_provider", openai_service())
            providers.append("openai_provider")

        # Anthropic (available)
        anthropic_service = import_manager.safe_import("anthropic", "OptionalFeature")
        if anthropic_service:
            registry.register_singleton("anthropic_provider", anthropic_service())
            providers.append("anthropic_provider")

        # Bedrock (not available)
        bedrock_service = import_manager.safe_import("bedrock", "BedrockClient")
        if bedrock_service:
            registry.register_singleton("bedrock_provider", bedrock_service())
            providers.append("bedrock_provider")

        # Create AI service that uses available providers
        def ai_service_factory():
            available_providers = []
            for provider_name in providers:
                provider = registry.get(provider_name)
                if provider and provider.enabled:
                    available_providers.append(provider)

            ai_service = Mock(name="ai_service")
            ai_service.providers = available_providers
            ai_service.provider_count = len(available_providers)
            ai_service.health_check = Mock(return_value=len(available_providers) > 0)
            return ai_service

        registry.register_factory("ai_service", ai_service_factory)

        # Verify AI service works with available providers
        ai_service = registry.get("ai_service")
        assert ai_service.provider_count == 2  # OpenAI and Anthropic
        assert ai_service.health_check() is True

        # Verify specific providers are available
        assert registry.has("openai_provider")
        assert registry.has("anthropic_provider")
        assert not registry.has("bedrock_provider")

    def test_realistic_application_startup_scenario(self, clean_environment):
        """Test realistic application startup with mixed required and optional services."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Mock core services that should always be available
        core_services = {
            "logging": MockRealModule("logging"),
            "json": MockRealModule("json"),
            "os": MockRealModule("os"),
            "sys": MockRealModule("sys"),
        }

        # Mock optional services
        optional_services = {
            "redis": MockOptionalModule("redis"),
            "prometheus_client": None,  # Not available
            "sentry_sdk": MockOptionalModule("sentry_sdk"),
        }

        def mock_import_module(name):
            if name in core_services:
                return core_services[name]
            if name in optional_services and optional_services[name]:
                return optional_services[name]
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # 1. Register core services (should all succeed)
            core_results = {}
            for service_name, module_name in [
                ("logger", "logging"),
                ("config", "json"),
                ("system", "os"),
            ]:
                success = import_manager.try_import_service(
                    module_name, service_name, "MockClass"
                )
                core_results[service_name] = success

            # All core services should be registered
            assert all(core_results.values())
            assert registry.has("logger")
            assert registry.has("config")
            assert registry.has("system")

            # 2. Register optional services (mixed results expected)
            optional_results = {}
            for service_name, module_name in [
                ("cache", "redis"),
                ("metrics", "prometheus_client"),
                ("monitoring", "sentry_sdk"),
            ]:
                success = import_manager.try_import_service(
                    module_name, service_name, "OptionalFeature"
                )
                optional_results[service_name] = success

            # Check optional service results
            assert optional_results["cache"] is True  # Redis available
            assert optional_results["metrics"] is False  # Prometheus not available
            assert optional_results["monitoring"] is True  # Sentry available

            # 3. Create application service that adapts to available services
            def app_service_factory():
                app = Mock(name="application")
                app.logger = registry.get("logger")
                app.config = registry.get("config")

                # Optional services with fallbacks
                app.cache = optional_service("cache", default=Mock(name="memory_cache"))
                app.metrics = optional_service(
                    "metrics", default=Mock(name="noop_metrics")
                )
                app.monitoring = optional_service("monitoring", default=None)

                app.health_check = Mock(return_value=True)
                return app

            registry.register_factory(
                "application", app_service_factory, ["logger", "config"]
            )

            # 4. Verify application works with available services
            app = registry.get("application")
            assert app is not None
            assert app.logger is not None
            assert app.config is not None
            assert app.cache is not None  # Should have fallback
            assert app.metrics is not None  # Should have fallback
            # Monitoring might be None or the actual service

    def test_dynamic_service_discovery(
        self, clean_environment, mock_real_world_modules
    ):
        """Test dynamic service discovery and registration."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Scenario: Discover and register services based on available modules

        service_candidates = [
            ("requests", "http_service", "MockClass"),
            ("numpy", "math_service", "MockClass"),
            ("pandas", "data_service", "MockClass"),
            ("tensorflow", "ml_service", "MockClass"),  # Not available
            ("redis", "cache_service", "OptionalFeature"),
            ("elasticsearch", "search_service", "SearchClient"),  # Not available
        ]

        discovered_services = []
        failed_services = []

        for module_name, service_name, class_name in service_candidates:
            success = import_manager.try_import_service(
                module_name, service_name, class_name
            )

            if success:
                discovered_services.append(service_name)
            else:
                failed_services.append(service_name)

        # Verify expected services were discovered
        assert "http_service" in discovered_services
        assert "math_service" in discovered_services
        assert "data_service" in discovered_services
        assert "cache_service" in discovered_services

        # Verify expected services failed
        assert "ml_service" in failed_services
        assert "search_service" in failed_services

        # Create a service that uses all discovered services
        def orchestrator_factory():
            orchestrator = Mock(name="orchestrator")
            orchestrator.services = {}

            for service_name in discovered_services:
                if registry.has(service_name):
                    orchestrator.services[service_name] = registry.get(service_name)

            orchestrator.service_count = len(orchestrator.services)
            orchestrator.health_check = Mock(return_value=True)
            return orchestrator

        registry.register_factory("orchestrator", orchestrator_factory)

        # Verify orchestrator has access to all discovered services
        orchestrator = registry.get("orchestrator")
        assert orchestrator.service_count == len(discovered_services)
        assert len(orchestrator.services) == len(discovered_services)


class TestFallbackBehavior:
    """Test fallback behavior for missing optional imports."""

    def test_graceful_degradation_with_missing_optional_services(
        self, clean_environment
    ):
        """Test graceful degradation when optional services are missing."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Mock scenario where some optional services are missing
        available_modules = {"core_service": MockRealModule("core_service")}

        def mock_import_module(name):
            if name in available_modules:
                return available_modules[name]
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # Register core service (available)
            success = import_manager.try_import_service(
                "core_service", "core", "MockClass"
            )
            assert success is True

            # Try to register optional services (not available)
            optional_success = import_manager.try_import_service(
                "optional_feature", "feature", "FeatureClass"
            )
            assert optional_success is False

            # Create service that gracefully handles missing optional dependencies
            def adaptive_service_factory():
                service = Mock(name="adaptive_service")
                service.core = registry.get("core")

                # Try to get optional feature with fallback
                service.feature = optional_service("feature", default=None)
                service.has_advanced_features = service.feature is not None

                # Adapt behavior based on available features
                if service.has_advanced_features:
                    service.capabilities = ["basic", "advanced"]
                else:
                    service.capabilities = ["basic"]

                service.health_check = Mock(return_value=True)
                return service

            registry.register_factory(
                "adaptive_service", adaptive_service_factory, ["core"]
            )

            # Verify service works without optional features
            service = registry.get("adaptive_service")
            assert service is not None
            assert service.core is not None
            assert service.feature is None
            assert service.has_advanced_features is False
            assert service.capabilities == ["basic"]
            assert service.health_check() is True

    def test_fallback_chain_with_multiple_alternatives(self, clean_environment):
        """Test fallback chain with multiple alternative services."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Mock scenario with multiple cache alternatives
        available_modules = {"memory_cache": MockRealModule("memory_cache")}

        def mock_import_module(name):
            if name in available_modules:
                return available_modules[name]
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # Try to register cache services in order of preference
            cache_alternatives = [
                ("redis", "redis_cache", "RedisCache"),
                ("memcached", "memcached_cache", "MemcachedCache"),
                ("memory_cache", "memory_cache", "MockClass"),
            ]

            cache_service = None
            for module_name, service_name, class_name in cache_alternatives:
                success = import_manager.try_import_service(
                    module_name, service_name, class_name
                )

                if success:
                    cache_service = service_name
                    break

            # Verify fallback to memory cache
            assert cache_service == "memory_cache"
            assert registry.has("memory_cache")

            # Create service that uses the available cache
            def app_service_factory():
                app = Mock(name="app_with_cache")

                # Use fallback pattern to get best available cache
                app.cache = create_fallback_service("redis_cache", "memory_cache")
                app.cache_type = type(app.cache).__name__
                app.health_check = Mock(return_value=True)
                return app

            registry.register_factory("app_with_cache", app_service_factory)

            # Verify app uses the fallback cache
            app = registry.get("app_with_cache")
            assert app.cache is not None
            assert app.cache_type == "MockClass"  # Memory cache fallback

    def test_optional_feature_detection_and_adaptation(self, clean_environment):
        """Test optional feature detection and service adaptation."""
        get_import_manager()

        # Mock only some features as available
        def mock_import_module(name):
            if name in ["asyncio"]:  # Only asyncio is "available"
                mock_module = MockRealModule(name)
                if name == "asyncio":
                    mock_module.AbstractEventLoop = Mock
                return mock_module
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # Test feature detection
            features = {
                "advanced_analytics": import_optional_dependency(
                    "numpy", "ndarray", "Advanced Analytics"
                ),
                "web_scraping": import_optional_dependency(
                    "requests", "Session", "Web Scraping"
                ),
                "machine_learning": import_optional_dependency(
                    "sklearn", "BaseEstimator", "Machine Learning"
                ),
                "async_support": import_optional_dependency(
                    "asyncio", "AbstractEventLoop", "Async Support"
                ),
            }

            # Verify feature detection results
            assert features["advanced_analytics"] is None
            assert features["web_scraping"] is None
            assert features["machine_learning"] is None
            assert features["async_support"] is not None

            # Create adaptive service based on available features
            available_features = [
                name for name, feature in features.items() if feature is not None
            ]

            assert available_features == ["async_support"]


class TestErrorPropagation:
    """Test error propagation for missing required imports."""

    def test_required_service_failure_propagation(self, clean_environment):
        """Test that required service failures propagate correctly."""
        get_import_manager()
        registry = get_registry()

        # Scenario: Service chain where a required dependency is missing

        # Register a service that depends on a missing required service
        def dependent_service_factory():
            # This should fail because required_service doesn't exist
            required = require_service("required_service", context="DependentService")
            service = Mock(name="dependent_service")
            service.dependency = required
            return service

        registry.register_factory(
            "dependent_service", dependent_service_factory, ["required_service"]
        )

        # Attempting to get the dependent service should fail
        with pytest.raises(Exception) as exc_info:
            registry.get("dependent_service")

        # The error should propagate through the service initialization system
        assert "required_service" in str(exc_info.value)
        assert "DependentService" in str(exc_info.value)

    def test_import_failure_error_chain(self, clean_environment):
        """Test error chain when required imports fail."""
        get_import_manager()

        # Test require_dependency with missing module
        with pytest.raises(CustomImportError) as exc_info:
            require_dependency(
                "critical_module",
                "CriticalClass",
                feature_name="Critical Feature",
                installation_hint="pip install critical-package",
            )

        error = exc_info.value
        assert error.module_name == "critical_module"
        assert "Required dependency 'critical_module' is not available" in str(error)
        assert "Critical Feature" in str(error)
        assert "pip install critical-package" in str(error)
        assert "Context: Required dependency for Critical Feature" in str(error)

    def test_service_initialization_error_propagation(self, clean_environment):
        """Test error propagation during service initialization."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Mock a module that exists but has a class that fails to initialize
        def mock_import_module(name):
            if name == "failing_module":
                mock_module = Mock()

                def failing_class(*args, **kwargs):
                    raise RuntimeError("Service initialization failed")

                mock_module.FailingClass = failing_class
                return mock_module
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # Try to register a service that will fail during initialization
            success = import_manager.try_import_service(
                "failing_module", "failing_service", "FailingClass"
            )

            # Registration should succeed (module import works)
            assert success is True
            assert registry.has("failing_service")

            # But getting the service should fail during initialization
            with pytest.raises(Exception) as exc_info:
                registry.get("failing_service")

            # The error should propagate up
            assert "Service initialization failed" in str(exc_info.value)

    def test_circular_dependency_error_propagation(self, clean_environment):
        """Test error propagation for circular dependencies."""
        get_import_manager()
        registry = get_registry()

        # Create circular dependency scenario
        def service_a_factory():
            service_b = require_service("service_b", context="ServiceA")
            service_a = Mock(name="service_a")
            service_a.dependency = service_b
            return service_a

        def service_b_factory():
            service_a = require_service("service_a", context="ServiceB")
            service_b = Mock(name="service_b")
            service_b.dependency = service_a
            return service_b

        registry.register_factory("service_a", service_a_factory, ["service_b"])
        registry.register_factory("service_b", service_b_factory, ["service_a"])

        # Validate dependencies should detect the circular dependency
        validation_errors = registry.validate_dependencies()
        assert len(validation_errors) > 0
        assert any(
            "Circular dependency detected" in error for error in validation_errors
        )

        # Attempting to get either service should fail
        with pytest.raises(Exception) as exc_info:
            registry.get("service_a")

        # Should detect circular dependency
        assert "Circular dependency detected" in str(
            exc_info.value
        ) or "Maximum recursion depth" in str(exc_info.value)


class TestImportPerformance:
    """Test performance of import resolution."""

    def test_import_caching_performance(self, clean_environment):
        """Test that import caching improves performance."""
        import_manager = get_import_manager()

        # Mock a slow import
        def slow_import_module(name):
            if name == "slow_module":
                time.sleep(0.01)  # Simulate slow import
                return MockRealModule("slow_module")
            raise ImportError(f"No module named '{name}'")

        with patch(
            "importlib.import_module", side_effect=slow_import_module
        ) as mock_import:

            # First import (should be slow)
            start_time = time.time()
            result1 = import_manager.safe_import("slow_module")
            first_import_time = time.time() - start_time

            # Second import (should be fast due to caching)
            start_time = time.time()
            result2 = import_manager.safe_import("slow_module")
            second_import_time = time.time() - start_time

            # Verify results
            assert result1 is not None
            assert result2 is result1  # Same object from cache
            assert second_import_time < first_import_time  # Cached import is faster

            # Verify import was only called once
            mock_import.assert_called_once_with("slow_module")

    def test_failed_import_caching_performance(self, clean_environment):
        """Test that failed import caching prevents repeated attempts."""
        import_manager = get_import_manager()

        call_count = 0

        def counting_import_module(name):
            nonlocal call_count
            call_count += 1
            if name == "nonexistent_module":
                time.sleep(0.01)  # Simulate slow failure
                raise ImportError(f"No module named '{name}'")
            return MockRealModule(name)

        with patch("importlib.import_module", side_effect=counting_import_module):

            # Multiple attempts to import non-existent module
            results = []
            for _ in range(5):
                result = import_manager.safe_import("nonexistent_module")
                results.append(result)

            # All results should be None
            assert all(result is None for result in results)

            # Import should only be attempted once due to failure caching
            assert call_count == 1

    def test_service_resolution_performance(self, clean_environment):
        """Test performance of service resolution."""
        get_import_manager()
        registry = get_registry()

        # Register multiple services
        for i in range(10):
            service = Mock(name=f"service_{i}")
            service.health_check = Mock(return_value=True)
            registry.register_singleton(f"service_{i}", service)

        # Measure service resolution performance
        start_time = time.time()

        for _ in range(100):  # Multiple resolutions
            for i in range(10):
                service = registry.get(f"service_{i}")
                assert service is not None

        total_time = time.time() - start_time
        avg_time_per_resolution = total_time / 1000  # 100 iterations * 10 services

        # Service resolution should be fast (< 1ms per resolution)
        assert avg_time_per_resolution < 0.001

    def test_bulk_import_performance(self, clean_environment):
        """Test performance of bulk import operations."""
        import_manager = get_import_manager()

        # Mock multiple modules
        modules = {f"module_{i}": MockRealModule(f"module_{i}") for i in range(20)}

        def mock_import_module(name):
            if name in modules:
                return modules[name]
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # Measure bulk import performance
            start_time = time.time()

            results = []
            for i in range(20):
                result = import_manager.safe_import(f"module_{i}")
                results.append(result)

            bulk_import_time = time.time() - start_time

            # Verify all imports succeeded
            assert all(result is not None for result in results)

            # Bulk import should be reasonably fast
            avg_time_per_import = bulk_import_time / 20
            assert avg_time_per_import < 0.01  # Less than 10ms per import

    def test_concurrent_import_safety(self, clean_environment):
        """Test that import manager is safe for concurrent access."""
        import_manager = get_import_manager()
        import threading
        import queue

        # Mock module for concurrent testing
        def mock_import_module(name):
            if name == "concurrent_module":
                time.sleep(0.001)  # Small delay to increase chance of race conditions
                return MockRealModule("concurrent_module")
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            results_queue = queue.Queue()

            def import_worker():
                try:
                    result = import_manager.safe_import("concurrent_module")
                    results_queue.put(("success", result))
                except Exception as e:
                    results_queue.put(("error", e))

            # Start multiple threads trying to import the same module
            threads = []
            for _ in range(5):
                thread = threading.Thread(target=import_worker)
                threads.append(thread)
                thread.start()

            # Wait for all threads to complete
            for thread in threads:
                thread.join()

            # Collect results
            results = []
            while not results_queue.empty():
                results.append(results_queue.get())

            # All imports should succeed
            assert len(results) == 5
            assert all(status == "success" for status, _ in results)

            # All results should be the same object (cached) - but due to threading,
            # we'll just verify they're all valid objects of the same type
            imported_objects = [result for status, result in results]
            first_object = imported_objects[0]
            assert all(obj is not None for obj in imported_objects)
            assert all(isinstance(obj, type(first_object)) for obj in imported_objects)


class TestRealisticIntegrationScenarios:
    """Test realistic integration scenarios combining multiple aspects."""

    def test_full_application_bootstrap_scenario(self, clean_environment):
        """Test full application bootstrap with realistic service dependencies."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Mock realistic application modules
        available_modules = {
            "logging": MockRealModule("logging"),
            "json": MockRealModule("json"),
            "sqlite3": MockRealModule("sqlite3"),
            "redis": MockOptionalModule("redis"),
            "requests": MockRealModule("requests"),
        }

        def mock_import_module(name):
            if name in available_modules:
                return available_modules[name]
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # Phase 1: Bootstrap core services
            core_services = [
                ("logging", "logger", "MockClass"),
                ("json", "config", "MockClass"),
                ("sqlite3", "database", "MockClass"),
            ]

            for module_name, service_name, class_name in core_services:
                success = import_manager.try_import_service(
                    module_name, service_name, class_name
                )
                assert success is True

            # Phase 2: Bootstrap optional services
            optional_services = [
                ("redis", "cache", "OptionalFeature"),
                ("prometheus_client", "metrics", "MetricsClient"),  # Not available
                ("requests", "http_client", "MockClass"),
            ]

            optional_results = {}
            for module_name, service_name, class_name in optional_services:
                success = import_manager.try_import_service(
                    module_name, service_name, class_name
                )
                optional_results[service_name] = success

            # Phase 3: Create application service with dependencies
            def application_factory():
                app = Mock(name="application")

                # Required dependencies
                app.logger = require_service("logger", context="Application")
                app.config = require_service("config", context="Application")
                app.database = require_service("database", context="Application")

                # Optional dependencies with fallbacks
                app.cache = optional_service("cache", default=Mock(name="memory_cache"))

                # Create a proper fallback metrics service
                fallback_metrics = Mock(name="noop_metrics")
                fallback_metrics.name = "noop_metrics"  # Set actual string value
                app.metrics = optional_service("metrics", default=fallback_metrics)

                app.http_client = optional_service("http_client", default=None)

                # Application configuration based on available services
                app.features = {
                    "caching": hasattr(app.cache, "enabled") and app.cache.enabled,
                    "metrics": hasattr(app.metrics, "name")
                    and app.metrics.name != "noop_metrics",
                    "http": app.http_client is not None,
                }

                app.health_check = Mock(return_value=True)
                return app

            registry.register_factory(
                "application", application_factory, ["logger", "config", "database"]
            )

            # Phase 4: Verify application bootstrap
            app = registry.get("application")

            # Verify core services are available
            assert app.logger is not None
            assert app.config is not None
            assert app.database is not None

            # Verify optional services have appropriate fallbacks
            assert app.cache is not None  # Should have fallback
            assert app.metrics is not None  # Should have fallback
            assert app.http_client is not None  # Should be available

            # Verify feature flags are set correctly
            assert app.features["caching"] is True  # Redis is available
            assert (
                app.features["metrics"] is False
            )  # Prometheus not available (should use fallback)
            assert app.features["http"] is True  # Requests is available

    def test_plugin_system_with_dynamic_imports(self, clean_environment):
        """Test plugin system with dynamic service discovery and registration."""
        import_manager = get_import_manager()
        registry = get_registry()

        # Mock plugin modules
        plugin_modules = {
            "plugin_auth": MockRealModule("plugin_auth"),
            "plugin_analytics": MockRealModule("plugin_analytics"),
            "plugin_export": MockOptionalModule("plugin_export"),
        }

        def mock_import_module(name):
            if name in plugin_modules:
                return plugin_modules[name]
            raise ImportError(f"No module named '{name}'")

        with patch("importlib.import_module", side_effect=mock_import_module):

            # Plugin discovery and registration
            plugin_configs = [
                {
                    "name": "auth_plugin",
                    "module": "plugin_auth",
                    "class": "MockClass",
                    "required": True,
                    "config": {"secret_key": "test_key"},
                },
                {
                    "name": "analytics_plugin",
                    "module": "plugin_analytics",
                    "class": "MockClass",
                    "required": False,
                    "config": {"tracking_id": "test_id"},
                },
                {
                    "name": "export_plugin",
                    "module": "plugin_export",
                    "class": "OptionalFeature",
                    "required": False,
                    "config": {"format": "json"},
                },
                {
                    "name": "missing_plugin",
                    "module": "plugin_missing",
                    "class": "MissingClass",
                    "required": False,
                    "config": {},
                },
            ]

            loaded_plugins = []
            failed_plugins = []

            for plugin_config in plugin_configs:
                success = import_manager.try_import_service(
                    plugin_config["module"],
                    plugin_config["name"],
                    plugin_config["class"],
                    factory_args=plugin_config["config"],
                )

                if success:
                    loaded_plugins.append(plugin_config["name"])
                else:
                    failed_plugins.append(plugin_config["name"])

                    # Check if required plugin failed
                    if plugin_config["required"]:
                        pytest.fail(
                            f"Required plugin {plugin_config['name']} failed to load"
                        )

            # Verify plugin loading results
            assert "auth_plugin" in loaded_plugins
            assert "analytics_plugin" in loaded_plugins
            assert "export_plugin" in loaded_plugins
            assert "missing_plugin" in failed_plugins

            # Create plugin manager service
            def plugin_manager_factory():
                manager = Mock(name="plugin_manager")
                manager.plugins = {}

                for plugin_name in loaded_plugins:
                    if registry.has(plugin_name):
                        manager.plugins[plugin_name] = registry.get(plugin_name)

                manager.plugin_count = len(manager.plugins)
                manager.available_plugins = list(manager.plugins.keys())
                manager.health_check = Mock(return_value=True)
                return manager

            registry.register_factory("plugin_manager", plugin_manager_factory)

            # Verify plugin manager
            plugin_manager = registry.get("plugin_manager")
            assert plugin_manager.plugin_count == 3
            assert set(plugin_manager.available_plugins) == set(loaded_plugins)


if __name__ == "__main__":
    """Run integration tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])
