"""
Unified configuration management for the AAA system.

This module provides hierarchical configuration loading with environment-specific
overrides and validation using Pydantic models.
"""

import os
import yaml
from typing import Any, Dict, List, Optional, Union
from pathlib import Path
from pydantic import BaseModel, Field, validator
from enum import Enum

from app.utils.result import Result


class Environment(str, Enum):
    """Application environment types."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    PRODUCTION = "production"


class LogLevel(str, Enum):
    """Logging levels."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class DatabaseConfig(BaseModel):
    """Database configuration."""
    url: Optional[str] = None
    host: str = "localhost"
    port: int = 5432
    name: str = "aaa_db"
    username: Optional[str] = None
    password: Optional[str] = None
    pool_size: int = 10
    max_overflow: int = 20


class CacheConfig(BaseModel):
    """Cache configuration."""
    type: str = "diskcache"  # diskcache, redis, memory
    directory: str = "cache"
    size_limit: int = 1024 * 1024 * 1024  # 1GB
    redis_url: Optional[str] = None
    ttl_seconds: int = 3600


class SecurityConfig(BaseModel):
    """Security configuration."""
    enable_prompt_defense: bool = True
    max_input_length: int = 10000
    rate_limit_requests: int = 100
    rate_limit_window: int = 3600
    allowed_origins: List[str] = ["*"]
    secret_key: Optional[str] = None


class LLMProviderConfig(BaseModel):
    """LLM provider configuration."""
    name: str
    api_key: Optional[str] = None
    base_url: Optional[str] = None
    model: str
    timeout: int = 30
    max_retries: int = 3
    temperature: float = 0.7
    max_tokens: Optional[int] = None


class UIConfig(BaseModel):
    """UI configuration."""
    page_title: str = "Automated AI Assessment"
    page_icon: str = "🤖"
    layout: str = "wide"
    sidebar_state: str = "expanded"
    theme: str = "light"
    show_debug: bool = False


class AppConfig(BaseModel):
    """Main application configuration."""
    environment: Environment = Environment.DEVELOPMENT
    debug: bool = False
    log_level: LogLevel = LogLevel.INFO
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    
    # Component configurations
    database: DatabaseConfig = Field(default_factory=DatabaseConfig)
    cache: CacheConfig = Field(default_factory=CacheConfig)
    security: SecurityConfig = Field(default_factory=SecurityConfig)
    ui: UIConfig = Field(default_factory=UIConfig)
    
    # LLM providers
    llm_providers: List[LLMProviderConfig] = Field(default_factory=list)
    default_llm_provider: str = "openai"
    
    # Feature flags
    enable_analytics: bool = True
    enable_exports: bool = True
    enable_jira_integration: bool = True
    
    @validator('environment', pre=True)
    def validate_environment(cls, v):
        if isinstance(v, str):
            return Environment(v.lower())
        return v
    
    @validator('log_level', pre=True)
    def validate_log_level(cls, v):
        if isinstance(v, str):
            return LogLevel(v.upper())
        return v


class ConfigurationManager:
    """
    Manages hierarchical configuration loading and environment overrides.
    
    Configuration is loaded in the following order (later overrides earlier):
    1. base.yaml (default configuration)
    2. {environment}.yaml (environment-specific overrides)
    3. Environment variables (highest priority)
    """
    
    def __init__(self, config_dir: Union[str, Path] = None):
        """
        Initialize the configuration manager.
        
        Args:
            config_dir: Directory containing configuration files
        """
        self.config_dir = Path(config_dir) if config_dir else Path("config")
        self._config: Optional[AppConfig] = None
        self._config_files_loaded: List[str] = []
    
    def load_config(self, environment: Optional[str] = None) -> Result[AppConfig, Exception]:
        """
        Load configuration from files and environment variables.
        
        Args:
            environment: Environment name (defaults to APP_ENV or 'development')
            
        Returns:
            Result containing the loaded configuration or error
        """
        try:
            # Determine environment
            env = environment or os.getenv('APP_ENV', 'development')
            
            # Load base configuration
            config_data = {}
            base_config_path = self.config_dir / "base.yaml"
            
            if base_config_path.exists():
                with open(base_config_path, 'r') as f:
                    base_config = yaml.safe_load(f)
                    if base_config:
                        config_data.update(base_config)
                        self._config_files_loaded.append(str(base_config_path))
            
            # Load environment-specific configuration
            env_config_path = self.config_dir / f"{env}.yaml"
            if env_config_path.exists():
                with open(env_config_path, 'r') as f:
                    env_config = yaml.safe_load(f)
                    if env_config:
                        config_data = self._deep_merge(config_data, env_config)
                        self._config_files_loaded.append(str(env_config_path))
            
            # Load local configuration overrides (highest priority for files)
            local_config_path = self.config_dir / "local.yaml"
            if local_config_path.exists():
                with open(local_config_path, 'r') as f:
                    local_config = yaml.safe_load(f)
                    if local_config:
                        config_data = self._deep_merge(config_data, local_config)
                        self._config_files_loaded.append(str(local_config_path))
            
            # Apply environment variable overrides (highest priority overall)
            config_data = self._apply_env_overrides(config_data)
            
            # Set environment in config
            config_data['environment'] = env
            
            # Create and validate configuration
            self._config = AppConfig(**config_data)
            
            return Result.success(self._config)
            
        except Exception as e:
            return Result.error(e)
    
    def get_config(self) -> Optional[AppConfig]:
        """
        Get the current configuration.
        
        Returns:
            The current configuration or None if not loaded
        """
        return self._config
    
    def reload_config(self, environment: Optional[str] = None) -> Result[AppConfig, Exception]:
        """
        Reload configuration from files.
        
        Args:
            environment: Environment name
            
        Returns:
            Result containing the reloaded configuration or error
        """
        self._config = None
        self._config_files_loaded.clear()
        return self.load_config(environment)
    
    def get_loaded_files(self) -> List[str]:
        """
        Get list of configuration files that were loaded.
        
        Returns:
            List of loaded configuration file paths
        """
        return self._config_files_loaded.copy()
    
    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Deep merge two dictionaries.
        
        Args:
            base: Base dictionary
            override: Override dictionary
            
        Returns:
            Merged dictionary
        """
        result = base.copy()
        
        for key, value in override.items():
            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value
        
        return result
    
    def _apply_env_overrides(self, config_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Apply environment variable overrides to configuration.
        
        Environment variables should be prefixed with AAA_ and use double
        underscores to separate nested keys (e.g., AAA_DATABASE__HOST).
        
        Args:
            config_data: Base configuration data
            
        Returns:
            Configuration data with environment overrides applied
        """
        env_prefix = "AAA_"
        
        for key, value in os.environ.items():
            if not key.startswith(env_prefix):
                continue
            
            # Remove prefix and convert to lowercase
            config_key = key[len(env_prefix):].lower()
            
            # Split nested keys
            key_parts = config_key.split('__')
            
            # Navigate to the correct nested location
            current = config_data
            for part in key_parts[:-1]:
                if part not in current:
                    current[part] = {}
                current = current[part]
            
            # Set the value (attempt type conversion)
            final_key = key_parts[-1]
            current[final_key] = self._convert_env_value(value)
        
        return config_data
    
    def _convert_env_value(self, value: str) -> Any:
        """
        Convert environment variable string to appropriate type.
        
        Args:
            value: Environment variable value
            
        Returns:
            Converted value
        """
        # Boolean conversion
        if value.lower() in ('true', 'false'):
            return value.lower() == 'true'
        
        # Integer conversion
        try:
            return int(value)
        except ValueError:
            pass
        
        # Float conversion
        try:
            return float(value)
        except ValueError:
            pass
        
        # List conversion (comma-separated)
        if ',' in value:
            return [item.strip() for item in value.split(',')]
        
        # Return as string
        return value


# Global configuration manager instance
_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """
    Get the global configuration manager instance.
    
    Returns:
        The global configuration manager
    """
    global _config_manager
    
    if _config_manager is None:
        _config_manager = ConfigurationManager()
    
    return _config_manager


def get_config() -> Optional[AppConfig]:
    """
    Get the current application configuration.
    
    Returns:
        The current configuration or None if not loaded
    """
    manager = get_config_manager()
    return manager.get_config()


def load_config(environment: Optional[str] = None) -> Result[AppConfig, Exception]:
    """
    Load application configuration.
    
    Args:
        environment: Environment name
        
    Returns:
        Result containing the loaded configuration or error
    """
    manager = get_config_manager()
    return manager.load_config(environment)