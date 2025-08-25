"""
Base tab interface for the AAA system.

This module defines the abstract base class that all tab implementations must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional
import streamlit as st


class BaseTab(ABC):
    """
    Abstract base class for all tab implementations.
    
    This class defines the standard interface that all tabs must implement,
    ensuring consistency across the application.
    """
    
    def __init__(self, tab_id: str, title: str, description: Optional[str] = None):
        """
        Initialize the base tab.
        
        Args:
            tab_id: Unique identifier for the tab
            title: Display title for the tab
            description: Optional description of the tab's purpose
        """
        self.tab_id = tab_id
        self.title = title
        self.description = description
        self._initialized = False
    
    @abstractmethod
    def render(self) -> None:
        """
        Render the tab content.
        
        This method must be implemented by all tab subclasses to define
        their specific UI rendering logic.
        """
        raise NotImplementedError("Subclasses must implement render()")
    
    @abstractmethod
    def initialize(self) -> None:
        """
        Initialize the tab's resources and state.
        
        This method is called once when the tab is first accessed and should
        handle any expensive initialization operations.
        """
        raise NotImplementedError("Subclasses must implement initialize()")
    
    def cleanup(self) -> None:
        """
        Clean up tab resources.
        
        This method is called when the tab is being destroyed or the
        application is shutting down. Override if cleanup is needed.
        """
        pass
    
    def get_state_key(self, key: str) -> str:
        """
        Generate a unique state key for this tab.
        
        Args:
            key: The base key name
            
        Returns:
            A unique key prefixed with the tab ID
        """
        return f"{self.tab_id}_{key}"
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Streamlit session state for this tab.
        
        Args:
            key: The state key
            default: Default value if key doesn't exist
            
        Returns:
            The state value or default
        """
        state_key = self.get_state_key(key)
        return st.session_state.get(state_key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        Set a value in Streamlit session state for this tab.
        
        Args:
            key: The state key
            value: The value to store
        """
        state_key = self.get_state_key(key)
        st.session_state[state_key] = value
    
    def ensure_initialized(self) -> None:
        """
        Ensure the tab is initialized, calling initialize() if needed.
        """
        if not self._initialized:
            self.initialize()
            self._initialized = True
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get tab metadata for debugging and analytics.
        
        Returns:
            Dictionary containing tab metadata
        """
        return {
            "tab_id": self.tab_id,
            "title": self.title,
            "description": self.description,
            "initialized": self._initialized
        }