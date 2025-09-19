"""
Integration tests for the service system.

Tests cover:
- Complete service registration and startup
- Service lifecycle management  
- Error handling for missing services
- Graceful degradation scenarios

Requirements covered: 2.1, 2.5, 5.1, 5.3
"""

import pytest
import asyncio
import logging
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any, List, Optional

from app.core.registry import (
    ServiceRegistry, 
    get_registry, 
    reset_registry,
    ServiceNotFoundError,
    ServiceInitializationError,
    ServiceLifecycle
)
from app.core.service_registration import (
    register_core_services,
    initialize_core_services,
    get_core_service_health
)
from app.core.startup import ApplicationStartup, StartupError
from app.core.service import Service, ConfigurableService


class MockFailingService(Service):
    """Mock service that fails during initialization."""
    
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


class MockDependentService(Service):
    """Mock service with dependencies."""
    
    def __init__(self, name: str, dependencies: List[str], fail_on_missing_dep: bool = False):
        self._name = name
        self._dependencies = dependencies
        self._fail_on_missing_dep = fail_on_missing_dep
        self._initialized = False
        self._shutdown_called = False
        self._injected_deps = {}
    
    @property
    def name(self) -> str:
        return self._name
    
    @property
    def dependencies(self) -> List[str]:
        return self._dependencies
    
    def initialize(self) -> None:
        # Simulate dependency injection
        if self._fail_on_missing_dep:
            for dep in self._dependencies:
                if dep not in self._injected_deps:
                    raise RuntimeError(f"Missing dependency: {dep}")
        self._initialized = True
    
    def shutdown(self) -> None:
        self._shutdown_called = True
        self._initialized = False
    
    def health_check(self) -> bool:
        return self._initialized
    
    def inject_dependency(self, name: str, service: Any) -> None:
        """Simulate dependency injection."""
        self._injected_deps[name] = service


@pytest.fixture
def clean_registry():
    """Provide a clean registry for each test."""
    reset_registry()
    yield get_registry()
    reset_registry()


class TestServiceSystemIntegration:
    """Integration tests for the complete service system."""
    
    def test_complete_service_registration_and_startup(self, clean_registry):
        """Test complete service registration and startup sequence."""
        registry = clean_registry
        
        # Mock the service classes to avoid actual initialization
        with patch('app.core.service_registration.ConfigService') as mock_config, \
             patch('app.core.service_registration.LoggerService') as mock_logger, \
             patch('app.core.service_registration.CacheService') as mock_cache, \
             patch('app.core.service_registration.SecurityService') as mock_security, \
             patch('app.core.service_registration.AdvancedPromptDefenseService') as mock_defense:
            
            # Configure mocks to return service instances
            mock_config.return_value = Mock(name="config_service")
            mock_logger.return_value = Mock(name="logger_service")
            mock_cache.return_value = Mock(name="cache_service")
            mock_security.return_value = Mock(name="security_service")
            mock_defense.return_value = Mock(name="defense_service")
            
            # Add initialize methods to mocks
            for mock_service in [mock_config.return_value, mock_logger.return_value, 
                               mock_cache.return_value, mock_security.return_value, 
                               mock_defense.return_value]:
                mock_service.initialize = Mock()
                mock_service.health_check = Mock(return_value=True)
                mock_service.shutdown = Mock()
            
            # Register core services
            registered_services = register_core_services(registry)
            
            # Verify services were registered
            assert len(registered_services) >= 5  # At least core services
            assert "config" in registered_services
            assert "logger" in registered_services
            assert "cache" in registered_services
            assert "security_validator" in registered_services
            assert "advanced_prompt_defender" in registered_services
            
            # Verify services are in registry
            for service_name in registered_services:
                assert registry.has(service_name)
                service_info = registry.get_service_info(service_name)
                assert service_info is not None
                assert service_info.lifecycle in [ServiceLifecycle.REGISTERED, ServiceLifecycle.INITIALIZED]
            
            # Initialize services
            init_results = initialize_core_services(registry)
            
            # Verify initialization results
            assert isinstance(init_results, dict)
            assert len(init_results) > 0
            
            # Check that services can be retrieved
            config_service = registry.get("config")
            logger_service = registry.get("logger")
            cache_service = registry.get("cache")
            
            assert config_service is not None
            assert logger_service is not None
            assert cache_service is not None
    
    def test_service_lifecycle_management(self, clean_registry):
        """Test service lifecycle management including initialization and shutdown."""
        registry = clean_registry
        
        # Create mock services with lifecycle methods
        service1 = Mock(name="service1")
        service1.initialize = Mock()
        service1.shutdown = Mock()
        service1.health_check = Mock(return_value=True)
        
        service2 = Mock(name="service2")
        service2.initialize = Mock()
        service2.shutdown = Mock()
        service2.health_check = Mock(return_value=True)
        
        # Register services
        registry.register_singleton("service1", service1)
        registry.register_singleton("service2", service2)
        
        # Verify initial state
        service_info1 = registry.get_service_info("service1")
        service_info2 = registry.get_service_info("service2")
        
        assert service_info1.lifecycle == ServiceLifecycle.INITIALIZED
        assert service_info2.lifecycle == ServiceLifecycle.INITIALIZED
        
        # Test health checking
        health_status = registry.health_check()
        assert health_status["service1"] is True
        assert health_status["service2"] is True
        
        # Test shutdown
        registry.shutdown_all()
        
        # Verify shutdown was called
        service1.shutdown.assert_called_once()
        service2.shutdown.assert_called_once()
        
        # Verify lifecycle state changed
        assert service_info1.lifecycle == ServiceLifecycle.SHUTDOWN
        assert service_info2.lifecycle == ServiceLifecycle.SHUTDOWN
    
    def test_error_handling_for_missing_services(self, clean_registry):
        """Test error handling when services are missing or unavailable."""
        registry = clean_registry
        
        # Test getting non-existent service
        with pytest.raises(ServiceNotFoundError) as exc_info:
            registry.get("nonexistent_service")
        
        assert "Service 'nonexistent_service' not registered" in str(exc_info.value)
        
        # Test dependency validation with missing services
        registry.register_factory("dependent_service", lambda: Mock(), ["missing_dependency"])
        
        validation_errors = registry.validate_dependencies()
        assert len(validation_errors) > 0
        assert any("missing_dependency" in error for error in validation_errors)
        
        # Test health check for non-existent service
        health_status = registry.health_check("nonexistent_service")
        assert health_status["nonexistent_service"] is False
        
        # Test service with failing initialization
        def failing_factory():
            raise RuntimeError("Service creation failed")
        
        registry.register_factory("failing_service", failing_factory)
        
        with pytest.raises(ServiceInitializationError) as exc_info:
            registry.get("failing_service")
        
        assert "Failed to initialize service 'failing_service'" in str(exc_info.value)
        assert "Service creation failed" in str(exc_info.value)
        
        # Verify service is marked as failed
        service_info = registry.get_service_info("failing_service")
        assert service_info.lifecycle == ServiceLifecycle.FAILED
        assert "Service creation failed" in service_info.error_message
    
    def test_graceful_degradation_scenarios(self, clean_registry):
        """Test graceful degradation when services fail or are unavailable."""
        registry = clean_registry
        
        # Scenario 1: Service fails health check but system continues
        failing_service = Mock(name="failing_service")
        failing_service.health_check = Mock(side_effect=RuntimeError("Health check failed"))
        failing_service.shutdown = Mock()
        
        working_service = Mock(name="working_service")
        working_service.health_check = Mock(return_value=True)
        working_service.shutdown = Mock()
        
        registry.register_singleton("failing_service", failing_service)
        registry.register_singleton("working_service", working_service)
        
        # Health check should handle the failing service gracefully
        health_status = registry.health_check()
        
        assert health_status["failing_service"] is False
        assert health_status["working_service"] is True
        
        # Verify error is recorded
        service_info = registry.get_service_info("failing_service")
        assert "Health check failed" in service_info.error_message
        
        # Scenario 2: Service shutdown fails but system continues
        failing_shutdown_service = Mock(name="failing_shutdown")
        failing_shutdown_service.shutdown = Mock(side_effect=RuntimeError("Shutdown failed"))
        failing_shutdown_service.health_check = Mock(return_value=True)
        
        registry.register_singleton("failing_shutdown", failing_shutdown_service)
        
        # Shutdown should handle the failing service gracefully
        registry.shutdown_all()  # Should not raise exception
        
        # Verify other services were still shut down
        working_service.shutdown.assert_called_once()
        
        # Scenario 3: Optional dependency missing - service should still work
        def factory_with_optional_deps():
            # This factory tries to get a missing dependency
            registry.get("optional_dependency")  # This will fail
            service = Mock(name="optional_deps_service")
            service.health_check = Mock(return_value=True)
            return service
        
        registry.register_factory("optional_deps_service", factory_with_optional_deps, 
                                 ["optional_dependency"])
        
        # Service creation should fail due to missing dependency
        with pytest.raises(ServiceInitializationError):
            registry.get("optional_deps_service")
        
        # But registry should still be functional for other services
        assert registry.get("working_service") is not None
    
    def test_service_dependency_resolution(self, clean_registry):
        """Test complex service dependency resolution scenarios."""
        registry = clean_registry
        
        # Create a chain of dependencies: A -> B -> C
        service_c = Mock(name="service_c")
        service_c.health_check = Mock(return_value=True)
        service_c.shutdown = Mock()
        
        def factory_b():
            service_b = Mock(name="service_b")
            service_b.dependency_c = registry.get("service_c")
            service_b.health_check = Mock(return_value=True)
            service_b.shutdown = Mock()
            return service_b
        
        def factory_a():
            service_a = Mock(name="service_a")
            service_a.dependency_b = registry.get("service_b")
            service_a.health_check = Mock(return_value=True)
            service_a.shutdown = Mock()
            return service_a
        
        # Register in reverse order to test dependency resolution
        registry.register_singleton("service_c", service_c)
        registry.register_factory("service_b", factory_b, ["service_c"])
        registry.register_factory("service_a", factory_a, ["service_b"])
        
        # Validate dependencies
        validation_errors = registry.validate_dependencies()
        assert len(validation_errors) == 0
        
        # Get service A - should trigger creation of B and use existing C
        service_a = registry.get("service_a")
        assert service_a is not None
        assert hasattr(service_a, 'dependency_b')
        assert hasattr(service_a.dependency_b, 'dependency_c')
        assert service_a.dependency_b.dependency_c is service_c
    
    def test_circular_dependency_detection(self, clean_registry):
        """Test detection and handling of circular dependencies."""
        registry = clean_registry
        
        # Create circular dependency: A -> B -> A
        def factory_a():
            return registry.get("service_b")  # A depends on B
        
        def factory_b():
            return registry.get("service_a")  # B depends on A
        
        registry.register_factory("service_a", factory_a, ["service_b"])
        registry.register_factory("service_b", factory_b, ["service_a"])
        
        # Dependency validation should detect the cycle
        validation_errors = registry.validate_dependencies()
        assert len(validation_errors) > 0
        assert any("Circular dependency detected" in error for error in validation_errors)
        
        # Attempting to get either service should fail
        with pytest.raises(ServiceInitializationError) as exc_info:
            registry.get("service_a")
        
        assert "Circular dependency detected" in str(exc_info.value)
    
    @pytest.mark.asyncio
    async def test_async_service_integration(self, clean_registry):
        """Test integration with async services."""
        registry = clean_registry
        
        # Create mock async service
        async_service = Mock(name="async_service")
        async_service.health_check = Mock(return_value=True)
        async_service.shutdown = Mock()
        
        # Mock async method
        async def async_operation():
            return "async_result"
        
        async_service.async_operation = async_operation
        
        registry.register_singleton("async_service", async_service)
        
        # Test that async service can be retrieved and used
        retrieved_service = registry.get("async_service")
        assert retrieved_service is async_service
        
        # Test async operation
        result = await retrieved_service.async_operation()
        assert result == "async_result"
        
        # Test health check
        health_status = registry.health_check("async_service")
        assert health_status["async_service"] is True
    
    def test_service_configuration_integration(self, clean_registry):
        """Test integration with service configuration system."""
        registry = clean_registry
        
        # Mock configuration service
        config_service = Mock(name="config_service")
        config_service.get = Mock(side_effect=lambda key, default=None: {
            "service.timeout": 30,
            "service.retries": 3,
            "service.enabled": True
        }.get(key, default))
        config_service.health_check = Mock(return_value=True)
        config_service.shutdown = Mock()
        
        registry.register_singleton("config", config_service)
        
        # Create configurable service that depends on config
        def configurable_factory():
            config = registry.get("config")
            service = Mock(name="configurable_service")
            service.timeout = config.get("service.timeout", 10)
            service.retries = config.get("service.retries", 1)
            service.enabled = config.get("service.enabled", False)
            service.health_check = Mock(return_value=service.enabled)
            service.shutdown = Mock()
            return service
        
        registry.register_factory("configurable_service", configurable_factory, ["config"])
        
        # Get the configurable service
        service = registry.get("configurable_service")
        
        # Verify configuration was applied
        assert service.timeout == 30
        assert service.retries == 3
        assert service.enabled is True
        
        # Verify health check reflects configuration
        health_status = registry.health_check("configurable_service")
        assert health_status["configurable_service"] is True
    
    def test_service_factory_vs_singleton_behavior(self, clean_registry):
        """Test different behavior between factory and singleton services."""
        registry = clean_registry
        
        # Register singleton service
        singleton_service = Mock(name="singleton_service")
        singleton_service.health_check = Mock(return_value=True)
        singleton_service.shutdown = Mock()
        
        registry.register_singleton("singleton_service", singleton_service)
        
        # Register factory service
        factory_call_count = 0
        
        def factory():
            nonlocal factory_call_count
            factory_call_count += 1
            service = Mock(name=f"factory_service_{factory_call_count}")
            service.health_check = Mock(return_value=True)
            service.shutdown = Mock()
            return service
        
        registry.register_factory("factory_service", factory)
        
        # Test singleton behavior - same instance returned
        singleton1 = registry.get("singleton_service")
        singleton2 = registry.get("singleton_service")
        assert singleton1 is singleton2
        assert singleton1 is singleton_service
        
        # Test factory behavior - new instance each time
        factory1 = registry.get("factory_service")
        factory2 = registry.get("factory_service")
        assert factory1 is not factory2
        assert factory_call_count == 2
        
        # Test service info reflects correct types
        singleton_info = registry.get_service_info("singleton_service")
        factory_info = registry.get_service_info("factory_service")
        
        assert singleton_info.service_type == "singleton"
        assert factory_info.service_type == "factory"
        assert singleton_info.instance is singleton_service
        assert factory_info.instance is None  # Factory doesn't store instances


class TestApplicationStartupIntegration:
    """Integration tests for the application startup system."""
    
    def test_startup_sequence_success(self):
        """Test successful application startup sequence."""
        reset_registry()
        
        with patch('app.core.startup.validate_startup_configuration') as mock_config_val, \
             patch('app.core.service_registration.register_core_services') as mock_register, \
             patch('app.core.service_registration.initialize_core_services') as mock_init:
            
            # Mock successful configuration validation
            mock_config_val.return_value = {
                'service_errors': [],
                'dependency_validation': Mock(is_valid=True, missing_required=[])
            }
            
            # Mock successful service registration
            mock_register.return_value = ["config", "logger", "cache"]
            
            # Mock successful service initialization
            mock_init.return_value = {"config": True, "logger": True, "cache": True}
            
            # Mock registry validation
            registry = get_registry()
            registry.validate_dependencies = Mock(return_value=[])
            registry.list_services = Mock(return_value=["config", "logger", "cache"])
            registry.health_check = Mock(return_value={"config": True, "logger": True, "cache": True})
            
            startup = ApplicationStartup()
            results = startup.run_startup_sequence()
            
            # Verify startup was successful
            assert results['startup_successful'] is True
            assert 'configuration' in results
            assert 'services' in results
            assert 'registry' in results
            
            # Verify startup completion
            assert startup.is_startup_completed() is True
    
    def test_startup_sequence_failure(self):
        """Test application startup sequence failure handling."""
        reset_registry()
        
        with patch.object(ApplicationStartup, '_validate_configuration') as mock_config_val:
            
            # Mock configuration validation failure
            mock_config_val.side_effect = RuntimeError("Configuration validation failed")
            
            startup = ApplicationStartup()
            
            with pytest.raises(StartupError) as exc_info:
                startup.run_startup_sequence()
            
            assert "Application startup failed" in str(exc_info.value)
            assert "Configuration validation failed" in str(exc_info.value)
            
            # Verify startup was not completed
            assert startup.is_startup_completed() is False
            
            # Verify error is recorded in results
            results = startup.get_validation_results()
            assert results['startup_successful'] is False
            assert 'error' in results
    
    def test_startup_with_service_failures(self):
        """Test startup handling when some services fail to register."""
        reset_registry()
        
        with patch.object(ApplicationStartup, '_validate_configuration') as mock_config_val, \
             patch.object(ApplicationStartup, '_register_services') as mock_register:
            
            # Mock successful configuration validation
            mock_config_val.return_value = {
                'valid': True,
                'service_errors': [],
                'services_loaded': 0,
                'dependencies_loaded': 0,
                'environment': 'testing'
            }
            
            # Mock service registration failure
            mock_register.side_effect = RuntimeError("Failed to register security service")
            
            startup = ApplicationStartup()
            
            with pytest.raises(StartupError):
                startup.run_startup_sequence()
            
            # Verify error handling
            results = startup.get_validation_results()
            assert results['startup_successful'] is False
    
    def test_startup_report_generation(self):
        """Test startup report generation."""
        reset_registry()
        
        startup = ApplicationStartup()
        startup._validation_results = {
            'startup_successful': True,
            'environment': 'testing',
            'configuration': {
                'services_loaded': 5,
                'dependencies_loaded': 10,
                'service_errors': []
            },
            'dependencies': {
                'valid': True,
                'missing_required': [],
                'missing_optional': ['redis']
            },
            'services': {
                'registered_count': 5,
                'failed_count': 0,
                'registered_services': ['config', 'logger', 'cache', 'security', 'defense']
            },
            'registry': {
                'valid': True,
                'dependency_errors': [],
                'health_status': {'config': True, 'logger': True, 'cache': True}
            }
        }
        
        report = startup.get_startup_report()
        
        # Verify report contains expected sections
        assert "Application Startup Report" in report
        assert "✅ Startup Status: SUCCESS" in report
        assert "🌍 Environment: testing" in report
        assert "📋 Configuration:" in report
        assert "📦 Dependencies:" in report
        assert "🔧 Services:" in report
        assert "🏪 Service Registry:" in report
        
        # Verify specific details
        assert "Services loaded: 5" in report
        assert "Dependencies loaded: 10" in report
        assert "Registered: 5" in report
        assert "All dependencies resolved" in report


if __name__ == "__main__":
    """Run integration tests when executed directly."""
    pytest.main([__file__, "-v", "--tb=short"])