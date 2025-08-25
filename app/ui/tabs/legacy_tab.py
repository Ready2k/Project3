"""Legacy tab wrapper for existing functionality."""

import streamlit as st

from app.ui.tabs.base import BaseTab

# Import logger for error handling
from app.utils.logger import app_logger


class LegacyTab(BaseTab):
    """Wrapper for legacy functionality that hasn't been migrated yet."""
    
    def __init__(self, title: str, render_function, session_manager=None, service_registry=None):
        super().__init__()
        self._title = title
        self.render_function = render_function
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return self._title
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render the legacy functionality."""
        try:
            if self.render_function:
                self.render_function()
            else:
                st.info(f"The {self._title} tab is being migrated to the new architecture. Please use the original app for now.")
        except Exception as e:
            st.error(f"Error rendering {self._title} tab: {str(e)}")
            app_logger.error(f"Legacy tab render error for {self._title}: {str(e)}")


class DiagramsTab(BaseTab):
    """Diagrams tab placeholder."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "📊 Diagrams"
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render diagrams functionality."""
        st.header("📊 Mermaid Diagrams")
        st.info("This tab is being migrated. For now, diagrams are available in the Results tab.")
        
        if st.session_state.get('session_id'):
            st.write("**Available in Results Tab:**")
            st.write("• Context Diagrams")
            st.write("• Container Diagrams") 
            st.write("• Sequence Diagrams")
            st.write("• Tech Stack Wiring Diagrams")
        else:
            st.write("Please start an analysis to generate diagrams.")


class ObservabilityTab(BaseTab):
    """Observability tab placeholder."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "📈 Observability"
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render observability functionality."""
        st.header("📈 Observability Dashboard")
        st.info("This tab is being migrated to the new architecture.")
        
        # Placeholder metrics
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric("Active Sessions", "0")
        
        with col2:
            st.metric("API Calls", "0")
        
        with col3:
            st.metric("Success Rate", "0%")
        
        with col4:
            st.metric("Avg Response Time", "0ms")


class PatternLibraryTab(BaseTab):
    """Pattern Library tab placeholder."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "📚 Pattern Library"
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render pattern library functionality."""
        st.header("📚 Pattern Library Management")
        st.info("This tab is being migrated to the new architecture.")
        
        # Show basic pattern info
        st.write("**Available Pattern Types:**")
        st.write("• PAT-* patterns (Standard patterns)")
        st.write("• APAT-* patterns (Agentic patterns)")
        st.write("• EPAT-* patterns (Enhanced patterns)")


class EnhancedPatternsTab(BaseTab):
    """Enhanced Patterns tab placeholder."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "🚀 Enhanced Patterns"
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render enhanced patterns functionality."""
        st.header("🚀 Enhanced Pattern Management")
        st.info("This tab is being migrated to the new architecture.")
        
        st.write("**Enhanced Pattern Features:**")
        st.write("• Pattern enhancement and merging")
        st.write("• Advanced pattern analytics")
        st.write("• Pattern quality scoring")


class TechnologyCatalogTab(BaseTab):
    """Technology Catalog tab placeholder."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "🔧 Technology Catalog"
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render technology catalog functionality."""
        st.header("🔧 Technology Catalog Management")
        st.info("This tab is being migrated to the new architecture.")
        
        st.write("**Technology Categories:**")
        st.write("• Languages & Frameworks")
        st.write("• Databases & Storage")
        st.write("• Cloud & Infrastructure")
        st.write("• AI/ML & Agent Frameworks")


class SchemaConfigTab(BaseTab):
    """Schema Config tab placeholder."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "⚙️ Schema Config"
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render schema config functionality."""
        st.header("⚙️ Schema Configuration")
        st.info("This tab is being migrated to the new architecture.")
        
        st.write("**Schema Management Features:**")
        st.write("• Dynamic schema configuration")
        st.write("• Enum value management")
        st.write("• Validation rule updates")


class SystemConfigTab(BaseTab):
    """System Config tab placeholder."""
    
    def __init__(self, session_manager, service_registry):
        super().__init__()
        self.session_manager = session_manager
        self.service_registry = service_registry
    
    @property
    def title(self) -> str:
        return "🔧 System Config"
    
    def can_render(self) -> bool:
        return True
    
    def render(self) -> None:
        """Render system config functionality."""
        st.header("🔧 System Configuration")
        st.info("This tab is being migrated to the new architecture.")
        
        st.write("**System Settings:**")
        st.write("• Provider configuration")
        st.write("• Performance settings")
        st.write("• Security configuration")