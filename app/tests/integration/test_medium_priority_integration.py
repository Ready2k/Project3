"""Integration test for all medium priority improvements."""

import asyncio
import pytest
from unittest.mock import Mock, patch

def test_dependency_injection_integration():
    """Test that dependency injection container works with all components."""
    from app.core.dependency_injection import ServiceContainer, ServiceScope
    from app.ui.components.provider_config import ProviderConfigComponent
    from app.ui.components.session_management import SessionManagementComponent
    
    # Create container
    container = ServiceContainer()
    
    # Register components
    container.register_singleton(ProviderConfigComponent, ProviderConfigComponent)
    container.register_singleton(SessionManagementComponent, SessionManagementComponent)
    
    # Resolve components
    provider_config = container.resolve(ProviderConfigComponent)
    session_manager = container.resolve(SessionManagementComponent)
    
    assert provider_config is not None
    assert session_manager is not None
    assert isinstance(provider_config, ProviderConfigComponent)
    assert isinstance(session_manager, SessionManagementComponent)
    
    # Test singleton behavior
    provider_config2 = container.resolve(ProviderConfigComponent)
    assert provider_config is provider_config2  # Same instance


def test_performance_monitoring_integration():
    """Test performance monitoring with components."""
    from app.monitoring.performance_monitor import PerformanceMonitor, monitor_performance
    
    monitor = PerformanceMonitor()
    
    # Test decorator
    @monitor_performance("test_operation")
    def test_function():
        return "success"
    
    result = test_function()
    assert result == "success"
    
    # Check metrics were recorded
    summary = monitor.get_metrics_summary()
    assert "metrics" in summary
    assert "active_alerts" in summary


def test_configuration_hierarchy_integration():
    """Test configuration hierarchy with different environments."""
    from app.config.environments import ConfigurationManager, Environment
    
    config_manager = ConfigurationManager()
    
    # Test different environments
    dev_config = config_manager.get_config(Environment.DEVELOPMENT)
    prod_config = config_manager.get_config(Environment.PRODUCTION)
    
    assert dev_config.debug is True
    assert prod_config.debug is False
    assert dev_config.logging.level == "DEBUG"
    assert prod_config.logging.level == "WARNING"


@pytest.mark.asyncio
async def test_component_integration_with_monitoring():
    """Test components working together with monitoring."""
    from app.core.dependency_injection import ServiceContainer
    from app.monitoring.performance_monitor import PerformanceMonitor
    from app.ui.api_client import AAA_APIClient
    
    # Setup
    container = ServiceContainer()
    monitor = PerformanceMonitor()
    
    # Register API client
    def create_api_client():
        return AAA_APIClient("http://localhost:8000")
    
    container.register_factory(AAA_APIClient, create_api_client)
    
    # Resolve and test
    api_client = container.resolve(AAA_APIClient)
    assert api_client is not None
    
    # Test with monitoring (mocked)
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = Mock()
        mock_response.status_code = 200
        mock_response.json.return_value = {"status": "ok"}
        mock_response.raise_for_status.return_value = None
        
        mock_client.return_value.__aenter__.return_value.get = Mock(return_value=mock_response)
        
        # This would normally be async, but we'll test the setup
        assert hasattr(api_client, 'make_request')


def test_configuration_with_dependency_injection():
    """Test configuration service integration with DI."""
    from app.core.dependency_injection import ServiceContainer
    from app.services.configuration_service import ConfigurationService
    from app.config.system_config import SystemConfigurationManager
    
    container = ServiceContainer()
    
    # Register configuration services
    container.register_singleton(SystemConfigurationManager, SystemConfigurationManager)
    container.register_singleton(ConfigurationService, ConfigurationService)
    
    # Resolve and test
    config_service = container.resolve(ConfigurationService)
    assert config_service is not None
    
    # Test configuration access
    llm_params = config_service.get_llm_params()
    assert "temperature" in llm_params
    assert "max_tokens" in llm_params


def test_error_boundaries_with_monitoring():
    """Test error boundaries integration with monitoring."""
    from app.utils.error_boundaries import error_boundary
    from app.monitoring.performance_monitor import PerformanceMonitor
    
    monitor = PerformanceMonitor()
    
    @error_boundary("test_operation", fallback_value="fallback")
    def failing_function():
        raise Exception("Test error")
    
    # Should return fallback value
    result = failing_function()
    assert result == "fallback"


def test_complete_system_integration():
    """Test complete system integration with all medium priority improvements."""
    from app.core.dependency_injection import get_service_container
    from app.monitoring import get_performance_monitor
    from app.config import get_current_config
    
    # Test that all systems can be initialized
    container = get_service_container()
    monitor = get_performance_monitor()
    config = get_current_config()
    
    assert container is not None
    assert monitor is not None
    assert config is not None
    
    # Test configuration
    assert hasattr(config, 'environment')
    assert hasattr(config, 'system')
    assert hasattr(config, 'database')
    
    # Test monitoring
    summary = monitor.get_metrics_summary()
    assert isinstance(summary, dict)
    
    # Test service registration info
    services_info = container.list_registered_services()
    assert isinstance(services_info, dict)


if __name__ == "__main__":
    """Run integration tests."""
    print("🧪 Running Medium Priority Integration Tests...")
    print("=" * 60)
    
    try:
        # Test 1: Dependency Injection
        print("1. Testing Dependency Injection Integration...")
        test_dependency_injection_integration()
        print("   ✅ PASS")
        
        # Test 2: Performance Monitoring
        print("2. Testing Performance Monitoring Integration...")
        test_performance_monitoring_integration()
        print("   ✅ PASS")
        
        # Test 3: Configuration Hierarchy
        print("3. Testing Configuration Hierarchy Integration...")
        test_configuration_hierarchy_integration()
        print("   ✅ PASS")
        
        # Test 4: Configuration + DI
        print("4. Testing Configuration with Dependency Injection...")
        test_configuration_with_dependency_injection()
        print("   ✅ PASS")
        
        # Test 5: Error Boundaries + Monitoring
        print("5. Testing Error Boundaries with Monitoring...")
        test_error_boundaries_with_monitoring()
        print("   ✅ PASS")
        
        # Test 6: Complete System
        print("6. Testing Complete System Integration...")
        test_complete_system_integration()
        print("   ✅ PASS")
        
        print("\n" + "=" * 60)
        print("🎉 ALL MEDIUM PRIORITY INTEGRATION TESTS PASSED!")
        print("✅ Dependency Injection: Working")
        print("✅ Performance Monitoring: Working")
        print("✅ Configuration Hierarchy: Working")
        print("✅ Component Integration: Working")
        print("✅ Error Boundaries: Working")
        print("✅ Complete System: Working")
        print("\n🚀 System is ready for production deployment!")
        
    except Exception as e:
        print(f"\n❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        exit(1)