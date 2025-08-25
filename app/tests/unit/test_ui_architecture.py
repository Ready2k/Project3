"""
Tests for the new UI architecture components.

This module tests the modular UI components, tab system, and main application
orchestrator to ensure they work correctly with the new architecture.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, Any

from app.ui.main_app import AAAStreamlitApp
from app.ui.tabs.base import BaseTab
from app.ui.tabs.analysis_tab import AnalysisTab
from app.ui.tabs.qa_tab import QATab
from app.ui.tabs.results_tab import ResultsTab
from app.ui.components.base import BaseComponent
from app.ui.components.provider_config import ProviderConfigComponent
from app.ui.components.session_management import SessionManagementComponent
from app.config.settings import AppConfig
from app.core.registry import ServiceRegistry
from app.utils.result import Result


class TestBaseTab:
    """Test the base tab interface."""
    
    def test_base_tab_is_abstract(self):
        """Test that BaseTab cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseTab()
    
    def test_concrete_tab_implementation(self):
        """Test that concrete tabs implement the interface correctly."""
        
        class TestTab(BaseTab):
            def __init__(self):
                super().__init__("test_tab", "Test Tab", "A test tab")
            
            def render(self) -> None:
                pass
            
            def initialize(self) -> None:
                pass
        
        tab = TestTab()
        assert tab.title == "Test Tab"
        assert tab.tab_id == "test_tab"
        assert tab.description == "A test tab"
        # render() should not raise an exception
        tab.render()
        # initialize() should not raise an exception
        tab.initialize()


class TestBaseComponent:
    """Test the base component interface."""
    
    def test_base_component_initialization(self):
        """Test base component initialization."""
        
        class TestComponent(BaseComponent):
            def render(self, **kwargs):
                return "rendered"
        
        # Test with no config
        component = TestComponent()
        assert component.config == {}
        
        # Test with config
        config = {"key": "value"}
        component = TestComponent(config)
        assert component.config == config
    
    def test_component_validation(self):
        """Test component property validation."""
        
        class TestComponent(BaseComponent):
            def render(self, **kwargs):
                return kwargs.get("test", "default")
            
            def validate_props(self, **kwargs) -> bool:
                return "required_prop" in kwargs
        
        component = TestComponent()
        
        # Test validation passes
        assert component.validate_props(required_prop="value") is True
        
        # Test validation fails
        assert component.validate_props(other_prop="value") is False


class TestAnalysisTab:
    """Test the analysis tab component."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies for analysis tab."""
        return {
            'config': Mock(spec=AppConfig),
            'registry': Mock(spec=ServiceRegistry),
            'session_state': {}
        }
    
    def test_analysis_tab_initialization(self, mock_dependencies):
        """Test analysis tab initialization."""
        with patch('streamlit.session_state', mock_dependencies['session_state']):
            tab = AnalysisTab(
                config=mock_dependencies['config'],
                registry=mock_dependencies['registry']
            )
            
            assert tab.title == "Analysis"
            assert tab.config is mock_dependencies['config']
            assert tab.registry is mock_dependencies['registry']
    
    def test_analysis_tab_can_render(self, mock_dependencies):
        """Test analysis tab render conditions."""
        with patch('streamlit.session_state', mock_dependencies['session_state']):
            tab = AnalysisTab(
                config=mock_dependencies['config'],
                registry=mock_dependencies['registry']
            )
            
            # Should always be able to render (entry point)
            assert tab.can_render() is True
    
    @patch('streamlit.text_area')
    @patch('streamlit.selectbox')
    @patch('streamlit.button')
    def test_analysis_tab_render(self, mock_button, mock_selectbox, mock_text_area, mock_dependencies):
        """Test analysis tab rendering."""
        mock_text_area.return_value = "Test requirements"
        mock_selectbox.return_value = "Text Input"
        mock_button.return_value = False
        
        with patch('streamlit.session_state', mock_dependencies['session_state']):
            tab = AnalysisTab(
                config=mock_dependencies['config'],
                registry=mock_dependencies['registry']
            )
            
            # Should not raise an exception
            tab.render()
            
            # Verify UI components were called
            mock_text_area.assert_called()
            mock_selectbox.assert_called()


class TestQATab:
    """Test the Q&A tab component."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies for Q&A tab."""
        session_state = {
            'session_id': 'test-session',
            'requirements': {'description': 'test'},
            'qa_phase': True
        }
        return {
            'config': Mock(spec=AppConfig),
            'registry': Mock(spec=ServiceRegistry),
            'session_state': session_state
        }
    
    def test_qa_tab_initialization(self, mock_dependencies):
        """Test Q&A tab initialization."""
        with patch('streamlit.session_state', mock_dependencies['session_state']):
            tab = QATab(
                config=mock_dependencies['config'],
                registry=mock_dependencies['registry']
            )
            
            assert tab.title == "Q&A"
    
    def test_qa_tab_can_render(self, mock_dependencies):
        """Test Q&A tab render conditions."""
        with patch('streamlit.session_state', mock_dependencies['session_state']):
            tab = QATab(
                config=mock_dependencies['config'],
                registry=mock_dependencies['registry']
            )
            
            # Should be able to render when in Q&A phase
            assert tab.can_render() is True
            
            # Should not render without session
            mock_dependencies['session_state'].pop('session_id')
            assert tab.can_render() is False


class TestResultsTab:
    """Test the results tab component."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock dependencies for results tab."""
        session_state = {
            'session_id': 'test-session',
            'analysis_complete': True,
            'recommendations': [{'pattern_id': 'PAT-001'}]
        }
        return {
            'config': Mock(spec=AppConfig),
            'registry': Mock(spec=ServiceRegistry),
            'session_state': session_state
        }
    
    def test_results_tab_can_render(self, mock_dependencies):
        """Test results tab render conditions."""
        with patch('streamlit.session_state', mock_dependencies['session_state']):
            tab = ResultsTab(
                config=mock_dependencies['config'],
                registry=mock_dependencies['registry']
            )
            
            # Should be able to render when analysis is complete
            assert tab.can_render() is True
            
            # Should not render without results
            mock_dependencies['session_state']['analysis_complete'] = False
            assert tab.can_render() is False


class TestProviderConfigComponent:
    """Test the provider configuration component."""
    
    @pytest.fixture
    def mock_config(self):
        """Mock configuration with LLM providers."""
        config = Mock(spec=AppConfig)
        config.llm_providers = [
            Mock(name="openai", model="gpt-4"),
            Mock(name="claude", model="claude-3")
        ]
        config.default_llm_provider = "openai"
        return config
    
    def test_provider_config_initialization(self, mock_config):
        """Test provider config component initialization."""
        component = ProviderConfigComponent({"providers": mock_config.llm_providers})
        assert component.config["providers"] == mock_config.llm_providers
    
    @patch('streamlit.selectbox')
    @patch('streamlit.slider')
    def test_provider_config_render(self, mock_slider, mock_selectbox, mock_config):
        """Test provider config component rendering."""
        mock_selectbox.return_value = "openai"
        mock_slider.return_value = 0.7
        
        component = ProviderConfigComponent({"providers": mock_config.llm_providers})
        
        result = component.render(current_provider="openai")
        
        # Should return provider configuration
        assert isinstance(result, dict)
        mock_selectbox.assert_called()


class TestSessionManagementComponent:
    """Test the session management component."""
    
    @pytest.fixture
    def mock_session_state(self):
        """Mock session state."""
        return {
            'session_id': 'test-session-123',
            'created_at': '2024-01-01T00:00:00Z'
        }
    
    def test_session_management_initialization(self):
        """Test session management component initialization."""
        component = SessionManagementComponent()
        assert component.config == {}
    
    @patch('streamlit.text')
    @patch('streamlit.button')
    def test_session_management_render(self, mock_button, mock_text, mock_session_state):
        """Test session management component rendering."""
        mock_button.return_value = False
        
        with patch('streamlit.session_state', mock_session_state):
            component = SessionManagementComponent()
            
            result = component.render()
            
            # Should display session information
            mock_text.assert_called()
            assert result is None or isinstance(result, dict)


class TestAAAStreamlitApp:
    """Test the main Streamlit application orchestrator."""
    
    @pytest.fixture
    def mock_dependencies(self):
        """Mock all dependencies for the main app."""
        config = Mock(spec=AppConfig)
        config.ui.page_title = "Test App"
        config.ui.page_icon = "🧪"
        config.ui.layout = "wide"
        
        registry = Mock(spec=ServiceRegistry)
        registry.resolve.return_value = Result.success(Mock())
        
        return {
            'config': config,
            'registry': registry
        }
    
    def test_app_initialization(self, mock_dependencies):
        """Test main app initialization."""
        with patch('app.config.settings.get_config', return_value=mock_dependencies['config']), \
             patch('app.core.registry.get_service_registry', return_value=mock_dependencies['registry']):
            
            app = AAAStreamlitApp()
            
            assert app.config is mock_dependencies['config']
            assert app.registry is mock_dependencies['registry']
    
    @patch('streamlit.set_page_config')
    def test_setup_page_config(self, mock_set_page_config, mock_dependencies):
        """Test page configuration setup."""
        with patch('app.config.settings.get_config', return_value=mock_dependencies['config']), \
             patch('app.core.registry.get_service_registry', return_value=mock_dependencies['registry']):
            
            app = AAAStreamlitApp()
            app._setup_page_config()
            
            mock_set_page_config.assert_called_once_with(
                page_title="Test App",
                page_icon="🧪",
                layout="wide"
            )
    
    @patch('streamlit.sidebar')
    def test_render_sidebar(self, mock_sidebar, mock_dependencies):
        """Test sidebar rendering."""
        mock_sidebar.header = Mock()
        
        with patch('app.config.settings.get_config', return_value=mock_dependencies['config']), \
             patch('app.core.registry.get_service_registry', return_value=mock_dependencies['registry']):
            
            app = AAAStreamlitApp()
            app._render_sidebar()
            
            # Should render provider configuration
            mock_sidebar.header.assert_called()
    
    @patch('streamlit.tabs')
    def test_render_main_content(self, mock_tabs, mock_dependencies):
        """Test main content rendering with tabs."""
        # Mock tab objects
        mock_tab_objects = [Mock() for _ in range(5)]
        mock_tabs.return_value = mock_tab_objects
        
        # Configure each tab object as context manager
        for tab_obj in mock_tab_objects:
            tab_obj.__enter__ = Mock(return_value=tab_obj)
            tab_obj.__exit__ = Mock(return_value=None)
        
        with patch('app.config.settings.get_config', return_value=mock_dependencies['config']), \
             patch('app.core.registry.get_service_registry', return_value=mock_dependencies['registry']):
            
            app = AAAStreamlitApp()
            app._render_main_content()
            
            # Should create tabs
            mock_tabs.assert_called_once()
            
            # Should enter each tab context
            for tab_obj in mock_tab_objects:
                tab_obj.__enter__.assert_called_once()
    
    @patch('streamlit.set_page_config')
    @patch('streamlit.sidebar')
    @patch('streamlit.tabs')
    def test_full_app_run(self, mock_tabs, mock_sidebar, mock_set_page_config, mock_dependencies):
        """Test full application run."""
        # Setup mocks
        mock_tab_objects = [Mock() for _ in range(5)]
        mock_tabs.return_value = mock_tab_objects
        
        for tab_obj in mock_tab_objects:
            tab_obj.__enter__ = Mock(return_value=tab_obj)
            tab_obj.__exit__ = Mock(return_value=None)
        
        with patch('app.config.settings.get_config', return_value=mock_dependencies['config']), \
             patch('app.core.registry.get_service_registry', return_value=mock_dependencies['registry']):
            
            app = AAAStreamlitApp()
            app.run()
            
            # Verify all components were called
            mock_set_page_config.assert_called_once()
            mock_sidebar.header.assert_called()
            mock_tabs.assert_called_once()


class TestUIIntegration:
    """Test integration between UI components."""
    
    def test_tab_registry_integration(self, test_config, test_service_registry):
        """Test that tabs can be registered and retrieved."""
        # Register tabs in service registry
        test_service_registry.register_factory(
            AnalysisTab,
            lambda: AnalysisTab(test_config, test_service_registry)
        )
        
        # Resolve tab
        result = test_service_registry.resolve(AnalysisTab)
        assert result.is_success
        
        tab = result.value
        assert isinstance(tab, AnalysisTab)
        assert tab.title == "Analysis"
    
    def test_component_dependency_injection(self, test_config):
        """Test that components can receive dependencies."""
        # Create component with dependencies
        component = ProviderConfigComponent({
            "providers": test_config.llm_providers
        })
        
        assert component.config["providers"] == test_config.llm_providers
    
    @patch('streamlit.session_state', {})
    def test_session_state_integration(self, test_config, test_service_registry):
        """Test that components can access session state."""
        tab = AnalysisTab(test_config, test_service_registry)
        
        # Should be able to access session state
        assert tab.can_render() is True  # Entry point tab
        
        # Should handle missing session gracefully
        qa_tab = QATab(test_config, test_service_registry)
        assert qa_tab.can_render() is False  # Requires session