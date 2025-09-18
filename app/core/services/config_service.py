"""
Configuration Service Implementation

Provides a centralized configuration service that implements the Service interface
and can be registered in the service registry.
"""

import os
import yaml
from typing import Dict, Any, List, Optional, Union
from pathlib import Path

from app.core.service import ConfigurableService
from app.config import Settings, load_settings


class ConfigService(ConfigurableService):
    """
    Centralized configuration service for the application.
    
    This service provides a unified interface for accessing configuration
    from various sources (files, environment variables, etc.) with
    validation and hot-reloading capabilities.
    """
    
    def __init__(self, config: Dict[str, Any]):
        """
        Initialize the configuration service.
        
        Args:
            config: Configuration service settings
        """
        super().__init__(config, "config")
        self._dependencies = []  # No dependencies - this is a foundational service
        
        # Configuration with defaults
        self.config_file = self.get_config("config_file", "config.yaml")
        self.environment_prefix = self.get_config("environment_prefix", "AAA")
        self.auto_reload = self.get_config("auto_reload", False)
        self.validation_enabled = self.get_config("validation_enabled", True)
        
        # Internal state
        self._settings: Optional[Settings] = None
        self._config_data: Dict[str, Any] = {}
        self._file_mtime: Optional[float] = None
    
    def _do_initialize(self) -> None:
        """Initialize the configuration system."""
        # Load initial configuration
        self._load_configuration()
        
        # Set up file monitoring if auto-reload is enabled
        if self.auto_reload:
            self._setup_file_monitoring()
        
        self._logger.info(f"Configuration service initialized from {self.config_file}")
    
    def _do_shutdown(self) -> None:
        """Shutdown the configuration system."""
        self._logger.info("Configuration service shutting down")
        # Clean up any file monitoring resources if needed
    
    def _do_health_check(self) -> bool:
        """Check if the configuration service is healthy."""
        try:
            # Check if settings are loaded
            if not self._settings:
                return False
            
            # Check if config file exists and is readable
            if self.config_file and Path(self.config_file).exists():
                config_path = Path(self.config_file)
                if not config_path.is_file() or not os.access(config_path, os.R_OK):
                    return False
            
            # Try to access a basic configuration value
            _ = self._settings.version
            return True
            
        except Exception:
            return False
    
    def _load_configuration(self) -> None:
        """Load configuration from file and environment variables."""
        try:
            # Load settings using the existing load_settings function
            self._settings = load_settings(self.config_file if Path(self.config_file).exists() else None)
            
            # Store raw config data for direct access
            if self.config_file and Path(self.config_file).exists():
                with open(self.config_file, 'r') as f:
                    self._config_data = yaml.safe_load(f) or {}
                
                # Track file modification time for auto-reload
                self._file_mtime = Path(self.config_file).stat().st_mtime
            
            # Validate configuration if enabled
            if self.validation_enabled:
                self._validate_configuration()
                
        except Exception as e:
            self._logger.error(f"Failed to load configuration: {e}")
            raise
    
    def _validate_configuration(self) -> None:
        """Validate the loaded configuration."""
        if not self._settings:
            raise ValueError("No configuration loaded")
        
        # Basic validation - ensure required fields are present
        required_fields = ['version', 'provider', 'model']
        for field in required_fields:
            if not hasattr(self._settings, field):
                raise ValueError(f"Required configuration field missing: {field}")
    
    def _setup_file_monitoring(self) -> None:
        """Set up file monitoring for auto-reload (placeholder for future implementation)."""
        # This would set up file system monitoring for hot-reloading
        # For now, we'll implement a simple check-on-access approach
        pass
    
    def _check_for_reload(self) -> None:
        """Check if configuration file has changed and reload if necessary."""
        if not self.auto_reload or not self.config_file:
            return
        
        try:
            config_path = Path(self.config_file)
            if config_path.exists():
                current_mtime = config_path.stat().st_mtime
                if self._file_mtime and current_mtime > self._file_mtime:
                    self._logger.info("Configuration file changed, reloading...")
                    self._load_configuration()
        except Exception as e:
            self._logger.warning(f"Failed to check for configuration reload: {e}")
    
    def get(self, key: str, default: Any = None) -> Any:
        """
        Get configuration value using dot notation.
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            default: Default value if key not found
            
        Returns:
            Configuration value or default
        """
        self._check_for_reload()
        
        # First try to get from Settings object
        if self._settings:
            try:
                # Handle dot notation for nested access
                keys = key.split('.')
                value = self._settings
                
                for k in keys:
                    if hasattr(value, k):
                        value = getattr(value, k)
                    elif isinstance(value, dict) and k in value:
                        value = value[k]
                    else:
                        # Key not found, return default
                        return default
                
                return value
            except (AttributeError, KeyError, TypeError):
                pass
        
        # Fallback to raw config data
        return self._get_from_dict(self._config_data, key, default)
    
    def _get_from_dict(self, data: Dict[str, Any], key: str, default: Any = None) -> Any:
        """Get value from dictionary using dot notation."""
        keys = key.split('.')
        value = data
        
        try:
            for k in keys:
                value = value[k]
            return value
        except (KeyError, TypeError):
            return default
    
    def set(self, key: str, value: Any) -> None:
        """
        Set configuration value (runtime only, not persisted).
        
        Args:
            key: Configuration key (supports dot notation for nested keys)
            value: Value to set
        """
        # Set in raw config data
        keys = key.split('.')
        config = self._config_data
        
        # Navigate to the parent of the target key
        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]
        
        # Set the final value
        config[keys[-1]] = value
        
        self._logger.debug(f"Configuration value set: {key} = {value}")
    
    def has(self, key: str) -> bool:
        """
        Check if configuration key exists.
        
        Args:
            key: Configuration key to check
            
        Returns:
            True if key exists, False otherwise
        """
        return self.get(key, None) is not None
    
    def get_section(self, section: str) -> Dict[str, Any]:
        """
        Get entire configuration section.
        
        Args:
            section: Section name
            
        Returns:
            Dictionary with section configuration
        """
        section_data = self.get(section, {})
        if isinstance(section_data, dict):
            return section_data
        else:
            # If it's a Pydantic model, convert to dict
            if hasattr(section_data, 'model_dump'):
                return section_data.model_dump()
            elif hasattr(section_data, 'dict'):
                return section_data.dict()
            else:
                return {}
    
    def reload(self) -> None:
        """Reload configuration from source."""
        self._logger.info("Manually reloading configuration")
        self._load_configuration()
    
    def get_settings(self) -> Settings:
        """
        Get the full Settings object.
        
        Returns:
            Pydantic Settings object
        """
        self._check_for_reload()
        if not self._settings:
            raise RuntimeError("Configuration not loaded")
        return self._settings
    
    def get_environment_variables(self, prefix: Optional[str] = None) -> Dict[str, str]:
        """
        Get environment variables with optional prefix filtering.
        
        Args:
            prefix: Environment variable prefix to filter by
            
        Returns:
            Dictionary of environment variables
        """
        prefix = prefix or self.environment_prefix
        env_vars = {}
        
        for key, value in os.environ.items():
            if prefix and key.startswith(f"{prefix}_"):
                # Remove prefix and convert to lowercase
                clean_key = key[len(prefix)+1:].lower()
                env_vars[clean_key] = value
            elif not prefix:
                env_vars[key] = value
        
        return env_vars
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get configuration service statistics.
        
        Returns:
            Dictionary with configuration statistics
        """
        config_file_exists = bool(self.config_file and Path(self.config_file).exists())
        
        return {
            "config_file": self.config_file,
            "config_file_exists": config_file_exists,
            "auto_reload_enabled": self.auto_reload,
            "validation_enabled": self.validation_enabled,
            "settings_loaded": self._settings is not None,
            "config_sections": list(self._config_data.keys()) if self._config_data else [],
            "environment_prefix": self.environment_prefix,
            "last_reload_time": self._file_mtime
        }