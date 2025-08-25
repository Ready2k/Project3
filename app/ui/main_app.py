"""Main Streamlit application orchestrator for Automated AI Assessment (AAA)."""

# Standard library imports
import asyncio
from typing import Dict, List, Optional, Any

# Third-party imports
import streamlit as st

# Local application imports
from app.config.settings import ConfigurationManager
from app.core.registry import ServiceRegistry
from app.ui.tabs.base import BaseTab
from app.utils.error_handler import ErrorHandler
from app.utils.logger import app_logger
from app.utils.result import Result


class TabRegistry:
    """Registry for managing tab components."""
    
    def __init__(self):
        self._tabs: List[BaseTab] = []
    
    def register_tab(self, tab: BaseTab) -> None:
        """Register a tab component."""
        self._tabs.append(tab)
    
    def get_tabs(self) -> List[BaseTab]:
        """Get all registered tabs."""
        return self._tabs
    
    def get_tab_by_name(self, name: str) -> Optional[BaseTab]:
        """Get a tab by its title."""
        for tab in self._tabs:
            if tab.title == name:
                return tab
        return None


class SessionManager:
    """Manages Streamlit session state."""
    
    def __init__(self):
        self.initialize_session_state()
    
    def initialize_session_state(self):
        """Initialize Streamlit session state variables."""
        defaults = {
            'session_id': None,
            'current_phase': None,
            'progress': 0,
            'recommendations': None,
            'provider_config': {
                'provider': 'openai',
                'model': 'gpt-4o',
                'api_key': '',
                'endpoint_url': '',
                'region': 'us-east-1'
            },
            'qa_questions': [],
            'processing': False
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    def reset_session(self):
        """Reset session state for new analysis."""
        st.session_state.session_id = None
        st.session_state.current_phase = None
        st.session_state.progress = 0
        st.session_state.recommendations = None
        st.session_state.qa_questions = []
        st.session_state.processing = False
    
    def get_session_data(self) -> Dict[str, Any]:
        """Get current session data."""
        return {
            'session_id': st.session_state.get('session_id'),
            'current_phase': st.session_state.get('current_phase'),
            'progress': st.session_state.get('progress'),
            'recommendations': st.session_state.get('recommendations'),
            'provider_config': st.session_state.get('provider_config'),
            'qa_questions': st.session_state.get('qa_questions'),
            'processing': st.session_state.get('processing')
        }


class AAAStreamlitApp:
    """Main Streamlit application orchestrator."""
    
    def __init__(self):
        # Initialize configuration manager and load configuration
        self.config_manager = ConfigurationManager()
        config_result = self.config_manager.load_config()
        
        if config_result.is_error:
            app_logger.warning(f"Failed to load configuration: {config_result.error}")
            # Continue with defaults
        
        self.session_manager = SessionManager()
        self.tab_registry = TabRegistry()
        self.service_registry = ServiceRegistry()
        self.error_handler = ErrorHandler(app_logger)
        
        # Initialize lazy loader for heavy components
        from app.ui.lazy_loader import get_lazy_loader
        self.lazy_loader = get_lazy_loader()
        self._setup_lazy_components()
        
        # Initialize performance monitoring
        from app.utils.performance_metrics import get_performance_metrics
        self.performance_metrics = get_performance_metrics()
        
        # Initialize cache manager
        from app.utils.cache_manager import get_cache_manager
        self.cache_manager = get_cache_manager()
        
        self._setup_page_config()
        self._register_tabs()
    
    def _setup_lazy_components(self) -> None:
        """Set up lazy loading for heavy components."""
        # Register heavy components for lazy loading
        self.lazy_loader.register_module(
            component_id="enhanced_pattern_management",
            module_path="app.ui.enhanced_pattern_management",
            class_name="EnhancedPatternManager",
            priority=1,  # Lower priority for heavy components
            cache_result=True
        )
        
        self.lazy_loader.register_module(
            component_id="pattern_enhancement_service",
            module_path="app.services.pattern_enhancement_service",
            class_name="PatternEnhancementService",
            priority=1,
            cache_result=True
        )
        
        self.lazy_loader.register_module(
            component_id="diagram_infrastructure",
            module_path="app.diagrams.infrastructure",
            factory_function="create_diagram_generator",
            priority=2,  # Medium priority
            cache_result=True
        )
        
        app_logger.info("Lazy loading components registered")
    
    def _setup_page_config(self):
        """Configure Streamlit page settings."""
        config = self.config_manager.get_config()
        
        if config is None:
            # Load configuration if not already loaded
            result = self.config_manager.load_config()
            if result.is_success:
                config = result.value
            else:
                # Use defaults if configuration loading fails
                config = None
        
        if config and hasattr(config, 'ui'):
            ui_config = config.ui
            st.set_page_config(
                page_title=ui_config.page_title,
                page_icon=ui_config.page_icon,
                layout=ui_config.layout,
                initial_sidebar_state=ui_config.sidebar_state
            )
        else:
            # Fallback to defaults
            st.set_page_config(
                page_title="Automated AI Assessment (AAA)",
                page_icon="🤖",
                layout="wide",
                initial_sidebar_state="expanded"
            )
    
    def _register_tabs(self):
        """Register all tab components."""
        # Import tabs here to avoid circular imports
        from app.ui.tabs.analysis_tab import AnalysisTab
        from app.ui.tabs.diagrams_tab import DiagramsTab
        from app.ui.tabs.observability_tab import ObservabilityTab
        from app.ui.tabs.pattern_library_tab import PatternLibraryTab
        from app.ui.tabs.enhanced_patterns_tab import EnhancedPatternsTab
        from app.ui.tabs.technology_catalog_tab import TechnologyCatalogTab
        from app.ui.tabs.schema_config_tab import SchemaConfigTab
        from app.ui.tabs.system_config_tab import SystemConfigTab
        from app.ui.tabs.about_tab import AboutTab
        
        # Register all tabs in the correct order
        self.tab_registry.register_tab(AnalysisTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(DiagramsTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(ObservabilityTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(PatternLibraryTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(EnhancedPatternsTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(TechnologyCatalogTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(SchemaConfigTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(SystemConfigTab(self.session_manager, self.service_registry))
        self.tab_registry.register_tab(AboutTab(self.session_manager, self.service_registry))
    
    def _render_sidebar(self):
        """Render sidebar with provider configuration."""
        from app.ui.components.provider_config import ProviderConfigComponent
        
        provider_config = ProviderConfigComponent()
        provider_config.render()
    
    def _render_main_content(self):
        """Render main tabbed interface."""
        st.title("🤖 Automated AI Assessment (AAA)")
        st.markdown("*Assess automation feasibility of your requirements with AI*")
        
        tabs = self.tab_registry.get_tabs()
        if not tabs:
            st.error("No tabs available to render")
            return
        
        # Create tab objects
        tab_titles = [tab.title for tab in tabs]
        tab_objects = st.tabs(tab_titles)
        
        # Render each tab
        for tab_obj, tab_handler in zip(tab_objects, tabs):
            with tab_obj:
                try:
                    tab_handler.render()
                except Exception as e:
                    from app.utils.error_handler import ErrorContext
                    context = ErrorContext(
                        component="main_app",
                        operation="tab_render",
                        additional_data={"tab_title": tab_handler.title}
                    )
                    error_info = self.error_handler.handle_exception(e, context)
                    st.error(f"Error rendering tab '{tab_handler.title}': {error_info.user_message}")
    
    def run(self) -> None:
        """Run the main application."""
        with self.performance_metrics.timer("app_run_total"):
            try:
                with self.performance_metrics.timer("sidebar_render"):
                    self._render_sidebar()
                
                with self.performance_metrics.timer("main_content_render"):
                    self._render_main_content()
                    
                # Record successful run
                self.performance_metrics.record_counter("app_runs_total", 1.0, {"status": "success"})
                
            except Exception as e:
                # Record failed run
                self.performance_metrics.record_counter("app_runs_total", 1.0, {"status": "error"})
                
                from app.utils.error_handler import ErrorContext
                context = ErrorContext(
                    component="main_app",
                    operation="app_run",
                    additional_data={"error_type": type(e).__name__}
                )
                error_info = self.error_handler.handle_exception(e, context)
                st.error(f"Application error: {error_info.user_message}")
                st.info("Please refresh the page and try again.")


def create_app() -> AAAStreamlitApp:
    """Factory function to create the main application."""
    return AAAStreamlitApp()