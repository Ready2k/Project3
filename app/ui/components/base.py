"""
Base component interface for the AAA system.

This module defines the abstract base class that all UI components must follow.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional, List
import streamlit as st


class BaseComponent(ABC):
    """
    Abstract base class for all UI components.
    
    This class defines the standard interface that all components must implement,
    ensuring consistency and reusability across the application.
    """
    
    def __init__(self, component_id: str, **kwargs):
        """
        Initialize the base component.
        
        Args:
            component_id: Unique identifier for the component
            **kwargs: Additional component-specific parameters
        """
        self.component_id = component_id
        self.config = kwargs
        self._rendered = False
    
    @abstractmethod
    def render(self, **kwargs) -> Any:
        """
        Render the component.
        
        This method must be implemented by all component subclasses to define
        their specific rendering logic.
        
        Args:
            **kwargs: Runtime parameters for rendering
            
        Returns:
            The rendered component result (if any)
        """
        raise NotImplementedError("Subclasses must implement render()")
    
    def validate_config(self) -> List[str]:
        """
        Validate the component configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        return []
    
    def get_unique_key(self, suffix: str = "") -> str:
        """
        Generate a unique key for Streamlit components.
        
        Args:
            suffix: Optional suffix to append to the key
            
        Returns:
            A unique key for this component instance
        """
        if suffix:
            return f"{self.component_id}_{suffix}"
        return self.component_id
    
    def get_state(self, key: str, default: Any = None) -> Any:
        """
        Get a value from Streamlit session state for this component.
        
        Args:
            key: The state key
            default: Default value if key doesn't exist
            
        Returns:
            The state value or default
        """
        state_key = self.get_unique_key(key)
        return st.session_state.get(state_key, default)
    
    def set_state(self, key: str, value: Any) -> None:
        """
        Set a value in Streamlit session state for this component.
        
        Args:
            key: The state key
            value: The value to store
        """
        state_key = self.get_unique_key(key)
        st.session_state[state_key] = value
    
    def clear_state(self, key: Optional[str] = None) -> None:
        """
        Clear component state.
        
        Args:
            key: Specific key to clear, or None to clear all component state
        """
        if key:
            state_key = self.get_unique_key(key)
            if state_key in st.session_state:
                del st.session_state[state_key]
        else:
            # Clear all state keys for this component
            prefix = f"{self.component_id}_"
            keys_to_remove = [k for k in st.session_state.keys() if k.startswith(prefix)]
            for k in keys_to_remove:
                del st.session_state[k]
    
    def get_metadata(self) -> Dict[str, Any]:
        """
        Get component metadata for debugging and analytics.
        
        Returns:
            Dictionary containing component metadata
        """
        return {
            "component_id": self.component_id,
            "config": self.config,
            "rendered": self._rendered,
            "validation_errors": self.validate_config()
        }
    
    def __enter__(self):
        """Context manager entry."""
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit with cleanup."""
        self.clear_state()