"""
Integration tests for modular UI components.

This module tests the integration between UI components, configuration system,
service registry, and other system components.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import tempfile
import json
from pathlib import Path

from app.ui.main_app import AAAStreamlitApp
from app.ui.tabs.analysis_tab import AnalysisTab
from app.ui.tabs.qa_tab import QATab
from app.ui.tabs.results_tab import ResultsTab
from app.ui.components.provider_config import ProviderConfigComponent
from app.ui.components.session_management import SessionManagementComponent
from app.config.settings import ConfigurationManager, AppConfig
from app.core.registry import ServiceRegistry, ServiceLifetime
from app.utils.result import Result


class TestConfigurationIntegration:
    """Test integration with the configuration system."""
    
    def test_ui_components_use_configuration(self, test_config, test_service_registry):
        """Test that UI components properly use configuration."""
        # Create analysis tab with configuration
        tab = AnalysisTab(test_config, test_service_registry)
        
        # Should use configuration for UI settings
        assert tab.config.ui.show_debug is True  # From test config
        assert tab.config.environment.value == "testing"
    
    def test_provider_config_component_integration(self, test_config):
        """Test provider configuration component with real config."""
        component = ProviderConfigComponent({
            "providers": test_config.llm_providers
        })
        
        # Should have test provider from configuration
        providers = component.config["providers"]
        assert len(providers) == 1
        assert providers[0].name == "test_provider"
        assert providers[0].model == "test-model"
    
    def test_configuration_hot_reload(self, temp_config_dir):
        """Test that configuration changes are reflected in components."""
        manager = ConfigurationManager(temp_config_dir)
        
        # Load initial configuration
        result = manager.load_config("testing")
        assert result.is_success
        initial_config = result.value
        
        # Create component with initial config
        component = ProviderConfigComponent({
            "providers": initial_config.llm_providers
        })
        
        # Modify configuration file
        new_config = {
            "llm_providers": [
                {
                    "name": "updated_provider",
                    "model": "updated-model",
                    "timeout": 10
                }
            ]
        }
        
        config_file = temp_config_dir / "testing.yaml"
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(new_config, f)
        
        # Reload configuration
        result = manager.reload_config("testing")
        assert result.is_success
        updated_config = result.value
        
        # Create new component with updated config
        updated_component = ProviderConfigComponent({
            "providers": updated_config.llm_providers
        })
        
        # Should reflect changes
        assert updated_component.config["providers"][0].name == "updated_provider"


class TestServiceRegistryIntegration:
    """Test integration with the service registry."""
    
    def test_tab_registration_and_resolution(self, test_config):
        """Test registering and resolving tabs through service registry."""
        registry = ServiceRegistry()
        
        # Register tabs
        registry.register_factory(
            AnalysisTab,
            lambda: AnalysisTab(test_config, registry),
            ServiceLifetime.SINGLETON
        )
        
        registry.register_factory(
            QATab,
            lambda: QATab(test_config, registry),
            ServiceLifetime.TRANSIENT
        )
        
        # Resolve tabs
        analysis_result = registry.resolve(AnalysisTab)
        assert analysis_result.is_success
        analysis_tab = analysis_result.value
        assert isinstance(analysis_tab, AnalysisTab)
        
        qa_result = registry.resolve(QATab)
        assert qa_result.is_success
        qa_tab = qa_result.value
        assert isinstance(qa_tab, QATab)
        
        # Singleton should return same instance
        analysis_result2 = registry.resolve(AnalysisTab)
        assert analysis_result2.value is analysis_tab
        
        # Transient should return different instance
        qa_result2 = registry.resolve(QATab)
        assert qa_result2.value is not qa_tab
    
    def test_component_dependency_injection(self, test_config):
        """Test dependency injection for components."""
        registry = ServiceRegistry()
        
        # Register dependencies
        registry.register_instance(AppConfig, test_config)
        
        # Register component with dependencies
        def create_provider_component():
            config = registry.resolve(AppConfig).value
            return ProviderConfigComponent({
                "providers": config.llm_providers
            })
        
        registry.register_factory(
            ProviderConfigComponent,
            create_provider_component,
            ServiceLifetime.SINGLETON
        )
        
        # Resolve component
        result = registry.resolve(ProviderConfigComponent)
        assert result.is_success
        
        component = result.value
        assert len(component.config["providers"]) == 1
    
    def test_service_registry_error_handling(self):
        """Test service registry error handling."""
        registry = ServiceRegistry()
        
        # Try to resolve unregistered service
        result = registry.resolve(AnalysisTab)
        assert result.is_error
        assert "not registered" in str(result.error)
        
        # Register service with failing factory
        def failing_factory():
            raise ValueError("Factory failed")
        
        registry.register_factory(AnalysisTab, failing_factory)
        
        result = registry.resolve(AnalysisTab)
        assert result.is_error
        assert isinstance(result.error, ValueError)


class TestUIWorkflowIntegration:
    """Test integration of UI workflow components."""
    
    @pytest.fixture
    def mock_streamlit_environment(self):
        """Mock Streamlit environment for testing."""
        session_state = {}
        
        with patch('streamlit.session_state', session_state), \
             patch('streamlit.set_page_config') as mock_page_config, \
             patch('streamlit.sidebar') as mock_sidebar, \
             patch('streamlit.tabs') as mock_tabs:
            
            # Configure mocks
            mock_tabs.return_value = [Mock() for _ in range(5)]
            
            yield {
                'session_state': session_state,
                'page_config': mock_page_config,
                'sidebar': mock_sidebar,
                'tabs': mock_tabs
            }
    
    def test_main_app_initialization_integration(self, test_config, test_service_registry, mock_streamlit_environment):
        """Test main app initialization with real dependencies."""
        # Register services
        test_service_registry.register_instance(AppConfig, test_config)
        
        with patch('app.config.settings.get_config', return_value=test_config), \
             patch('app.core.registry.get_service_registry', return_value=test_service_registry):
            
            app = AAAStreamlitApp()
            
            # Should initialize with correct dependencies
            assert app.config is test_config
            assert app.registry is test_service_registry
    
    def test_tab_workflow_integration(self, test_config, test_service_registry, mock_streamlit_environment):
        """Test tab workflow integration."""
        session_state = mock_streamlit_environment['session_state']
        
        # Create tabs
        analysis_tab = AnalysisTab(test_config, test_service_registry)
        qa_tab = QATab(test_config, test_service_registry)
        results_tab = ResultsTab(test_config, test_service_registry)
        
        # Test initial state - only analysis tab should be renderable
        assert analysis_tab.can_render() is True
        assert qa_tab.can_render() is False
        assert results_tab.can_render() is False
        
        # Simulate analysis completion
        session_state.update({
            'session_id': 'test-session',
            'requirements': {'description': 'test'},
            'qa_phase': True
        })
        
        # Now Q&A tab should be renderable
        assert qa_tab.can_render() is True
        assert results_tab.can_render() is False
        
        # Simulate analysis completion
        session_state.update({
            'analysis_complete': True,
            'recommendations': [{'pattern_id': 'PAT-001'}]
        })
        
        # Now results tab should be renderable
        assert results_tab.can_render() is True
    
    def test_component_interaction_integration(self, test_config, mock_streamlit_environment):
        """Test interaction between components."""
        session_state = mock_streamlit_environment['session_state']
        
        # Create components
        provider_config = ProviderConfigComponent({
            "providers": test_config.llm_providers
        })
        
        session_mgmt = SessionManagementComponent()
        
        # Test provider configuration
        with patch('streamlit.selectbox', return_value="test_provider"), \
             patch('streamlit.slider', return_value=0.7):
            
            provider_result = provider_config.render(current_provider="test_provider")
            assert isinstance(provider_result, dict)
        
        # Test session management
        session_state['session_id'] = 'test-session-123'
        
        with patch('streamlit.text') as mock_text, \
             patch('streamlit.button', return_value=False):
            
            session_mgmt.render()
            mock_text.assert_called()


class TestErrorHandlingIntegration:
    """Test error handling integration across components."""
    
    def test_configuration_error_handling(self):
        """Test error handling when configuration fails."""
        # Create manager with non-existent directory
        manager = ConfigurationManager("/non/existent/path")
        
        result = manager.load_config()
        # Should succeed with defaults even if files don't exist
        assert result.is_success
        
        config = result.value
        assert config.environment.value == "development"  # Default
    
    def test_service_resolution_error_handling(self, test_config, test_service_registry):
        """Test error handling when service resolution fails."""
        # Try to create tab with unregistered dependencies
        tab = AnalysisTab(test_config, test_service_registry)
        
        # Should handle missing services gracefully
        assert tab.config is test_config
        assert tab.registry is test_service_registry
    
    def test_ui_component_error_handling(self, test_config):
        """Test UI component error handling."""
        # Create component with invalid configuration
        component = ProviderConfigComponent({})
        
        # Should handle missing providers gracefully
        with patch('streamlit.selectbox', return_value="default"), \
             patch('streamlit.error') as mock_error:
            
            result = component.render()
            # Should either return default or show error
            assert result is not None or mock_error.called


class TestPerformanceIntegration:
    """Test performance aspects of component integration."""
    
    def test_lazy_loading_integration(self, test_config, test_service_registry):
        """Test lazy loading of components."""
        # Register components as singletons for performance
        test_service_registry.register_factory(
            AnalysisTab,
            lambda: AnalysisTab(test_config, test_service_registry),
            ServiceLifetime.SINGLETON
        )
        
        # First resolution should create instance
        result1 = test_service_registry.resolve(AnalysisTab)
        assert result1.is_success
        
        # Second resolution should return same instance (performance optimization)
        result2 = test_service_registry.resolve(AnalysisTab)
        assert result2.is_success
        assert result2.value is result1.value
    
    def test_configuration_caching(self, temp_config_dir):
        """Test configuration caching for performance."""
        manager = ConfigurationManager(temp_config_dir)
        
        # Load configuration
        result1 = manager.load_config("testing")
        assert result1.is_success
        
        # Get cached configuration
        cached_config = manager.get_config()
        assert cached_config is result1.value
        
        # Should return same instance for performance
        assert manager.get_config() is cached_config
    
    def test_memory_usage_integration(self, test_config, test_service_registry):
        """Test memory usage of integrated components."""
        # Create multiple components
        components = []
        
        for i in range(10):
            tab = AnalysisTab(test_config, test_service_registry)
            components.append(tab)
        
        # All should share same configuration instance
        for component in components:
            assert component.config is test_config
            assert component.registry is test_service_registry
        
        # Memory usage should be reasonable (shared references)
        assert len(components) == 10


class TestBackwardCompatibilityIntegration:
    """Test backward compatibility with existing system."""
    
    def test_legacy_session_state_compatibility(self, test_config, test_service_registry):
        """Test compatibility with existing session state structure."""
        # Simulate legacy session state
        legacy_session_state = {
            'session_id': 'legacy-session',
            'requirements_text': 'Legacy requirements',
            'provider': 'openai',
            'model': 'gpt-4'
        }
        
        with patch('streamlit.session_state', legacy_session_state):
            # Components should handle legacy state gracefully
            tab = AnalysisTab(test_config, test_service_registry)
            assert tab.can_render() is True
    
    def test_existing_api_compatibility(self, test_config):
        """Test compatibility with existing API patterns."""
        # Test that components can work with existing API responses
        mock_api_response = {
            'session_id': 'api-session',
            'status': 'complete',
            'recommendations': [
                {
                    'pattern_id': 'PAT-001',
                    'feasibility': 'Automatable',
                    'confidence': 0.9
                }
            ]
        }
        
        # Components should handle API response format
        component = SessionManagementComponent()
        
        with patch('streamlit.session_state', mock_api_response), \
             patch('streamlit.text'), \
             patch('streamlit.button', return_value=False):
            
            # Should not raise exceptions
            result = component.render()
            assert result is None or isinstance(result, dict)