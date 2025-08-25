"""
Configuration management for the AAA system.

This module provides unified configuration management with hierarchical loading
and environment-specific overrides.
"""

# Import from the legacy config.py for backward compatibility
import sys
from pathlib import Path

# Add the parent directory to import the legacy config
sys.path.insert(0, str(Path(__file__).parent.parent))

try:
    from config import (
        Settings,
        JiraConfig,
        JiraAuthType,
        JiraDeploymentType,
        BedrockConfig,
        EmbeddingProvider,
        load_settings
    )
except ImportError:
    # Fallback to direct import
    import importlib.util
    config_path = Path(__file__).parent.parent / "config.py"
    spec = importlib.util.spec_from_file_location("config", config_path)
    config_module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(config_module)
    
    Settings = config_module.Settings
    JiraConfig = config_module.JiraConfig
    JiraAuthType = config_module.JiraAuthType
    JiraDeploymentType = config_module.JiraDeploymentType
    BedrockConfig = config_module.BedrockConfig
    EmbeddingProvider = config_module.EmbeddingProvider
    load_settings = config_module.load_settings

# Import from the new settings module
from .settings import (
    ConfigurationManager,
    AppConfig,
    get_config_manager,
    get_config,
    load_config
)

__version__ = "1.0.0"

# Expose the main classes for backward compatibility
__all__ = [
    'Settings',
    'JiraConfig', 
    'JiraAuthType',
    'JiraDeploymentType',
    'BedrockConfig',
    'EmbeddingProvider',
    'load_settings',
    'ConfigurationManager',
    'AppConfig',
    'get_config_manager',
    'get_config',
    'load_config'
]