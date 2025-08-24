"""Environment-specific configuration management for AAA system."""

import os
from typing import Dict, Any, Optional, Type, TypeVar
from pathlib import Path
from enum import Enum
import yaml
from dataclasses import dataclass, field

from app.config.system_config import (
    SystemConfiguration, AutonomyConfig, PatternMatchingConfig, 
    LLMGenerationConfig, RecommendationConfig, SystemConfigurationManager
)
from app.utils.logger import app_logger

T = TypeVar('T')


class Environment(Enum):
    """Application environments."""
    DEVELOPMENT = "development"
    TESTING = "testing"
    STAGING = "staging"
    PRODUCTION = "production"


@dataclass
class DatabaseConfig:
    """Database configuration."""
    url: str = "sqlite:///aaa.db"
    pool_size: int = 10
    max_overflow: int = 20
    pool_timeout: int = 30
    pool_recycle: int = 3600
    echo: bool = False


@dataclass
class RedisConfig:
    """Redis configuration."""
    host: str = "localhost"
    port: int = 6379
    db: int = 0
    password: Optional[str] = None
    ssl: bool = False
    socket_timeout: int = 30
    socket_connect_timeout: int = 30
    max_connections: int = 50


@dataclass
class SecurityConfig:
    """Security configuration."""
    secret_key: str = "dev-secret-key-change-in-production"
    jwt_algorithm: str = "HS256"
    jwt_expiration_hours: int = 24
    password_min_length: int = 8
    max_login_attempts: int = 5
    lockout_duration_minutes: int = 15
    enable_rate_limiting: bool = True
    rate_limit_per_minute: int = 60
    rate_limit_per_hour: int = 1000


@dataclass
class LoggingConfig:
    """Logging configuration."""
    level: str = "INFO"
    format: str = "{time:YYYY-MM-DD HH:mm:ss} | {level} | {name}:{function}:{line} | {message}"
    rotation: str = "1 day"
    retention: str = "30 days"
    compression: str = "gz"
    serialize: bool = False
    backtrace: bool = True
    diagnose: bool = True
    file_path: Optional[str] = None


@dataclass
class MonitoringConfig:
    """Monitoring and observability configuration."""
    enabled: bool = True
    metrics_port: int = 9090
    health_check_port: int = 8080
    check_interval_seconds: int = 30
    alert_webhook_url: Optional[str] = None
    export_interval_seconds: int = 300
    retention_days: int = 30
    enable_profiling: bool = False
    profiling_sample_rate: float = 0.01


@dataclass
class CacheConfig:
    """Caching configuration."""
    backend: str = "memory"  # memory, redis, disk
    default_ttl_seconds: int = 3600
    max_size_mb: int = 100
    cleanup_interval_seconds: int = 300
    redis_config: Optional[RedisConfig] = None


@dataclass
class APIConfig:
    """API server configuration."""
    host: str = "0.0.0.0"
    port: int = 8000
    workers: int = 1
    max_request_size: int = 10 * 1024 * 1024  # 10MB
    timeout_seconds: int = 30
    enable_cors: bool = True
    cors_origins: list = field(default_factory=lambda: ["*"])
    enable_docs: bool = True
    docs_url: str = "/docs"
    redoc_url: str = "/redoc"


@dataclass
class UIConfig:
    """UI configuration."""
    host: str = "0.0.0.0"
    port: int = 8501
    title: str = "Automated AI Assessment (AAA)"
    theme: str = "light"
    sidebar_state: str = "expanded"
    wide_mode: bool = True
    enable_debug: bool = False


@dataclass
class EnvironmentConfig:
    """Complete environment-specific configuration."""
    environment: Environment
    debug: bool = False
    
    # Core configurations  
    system: SystemConfiguration = field(default_factory=lambda: SystemConfiguration(
        autonomy=AutonomyConfig(),
        pattern_matching=PatternMatchingConfig(), 
        llm_generation=LLMGenerationConfig(),
        recommendations=RecommendationConfig()
    ))
    database: DatabaseConfig = field(default_factory=DatabaseConfig)
    redis: RedisConfig = field(default_factory=RedisConfig)
    security: SecurityConfig = field(default_factory=SecurityConfig)
    logging: LoggingConfig = field(default_factory=LoggingConfig)
    monitoring: MonitoringConfig = field(default_factory=MonitoringConfig)
    cache: CacheConfig = field(default_factory=CacheConfig)
    api: APIConfig = field(default_factory=APIConfig)
    ui: UIConfig = field(default_factory=UIConfig)
    
    # Custom settings
    custom: Dict[str, Any] = field(default_factory=dict)


class ConfigurationManager:
    """Manages environment-specific configurations with hierarchy and overrides."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.config_dir.mkdir(exist_ok=True)
        self._configs: Dict[Environment, EnvironmentConfig] = {}
        self._current_env: Optional[Environment] = None
        self._load_configurations()
    
    def _load_configurations(self):
        """Load all environment configurations."""
        # Create default configurations if they don't exist
        self._create_default_configs()
        
        # Load configurations from files
        for env in Environment:
            config_file = self.config_dir / f"{env.value}.yaml"
            if config_file.exists():
                self._configs[env] = self._load_config_file(config_file, env)
            else:
                self._configs[env] = self._get_default_config(env)
    
    def _create_default_configs(self):
        """Create default configuration files if they don't exist."""
        for env in Environment:
            config_file = self.config_dir / f"{env.value}.yaml"
            if not config_file.exists():
                default_config = self._get_default_config(env)
                self._save_config_file(config_file, default_config)
                app_logger.info(f"Created default configuration: {config_file}")
    
    def _get_default_config(self, env: Environment) -> EnvironmentConfig:
        """Get default configuration for an environment."""
        # Create default system configuration
        from app.config.system_config import (
            AutonomyConfig, PatternMatchingConfig, 
            LLMGenerationConfig, RecommendationConfig, SystemConfiguration
        )
        
        system_config = SystemConfiguration(
            autonomy=AutonomyConfig(),
            pattern_matching=PatternMatchingConfig(),
            llm_generation=LLMGenerationConfig(),
            recommendations=RecommendationConfig()
        )
        
        base_config = EnvironmentConfig(
            environment=env,
            system=system_config
        )
        
        if env == Environment.DEVELOPMENT:
            base_config.debug = True
            base_config.logging.level = "DEBUG"
            base_config.logging.file_path = "logs/aaa-dev.log"
            base_config.database.echo = True
            base_config.monitoring.enable_profiling = True
            base_config.ui.enable_debug = True
            base_config.api.enable_docs = True
            
        elif env == Environment.TESTING:
            base_config.debug = True
            base_config.logging.level = "DEBUG"
            base_config.logging.file_path = "logs/aaa-test.log"
            base_config.database.url = "sqlite:///:memory:"
            base_config.cache.backend = "memory"
            base_config.monitoring.enabled = False
            
        elif env == Environment.STAGING:
            base_config.debug = False
            base_config.logging.level = "INFO"
            base_config.logging.file_path = "logs/aaa-staging.log"
            base_config.database.url = "postgresql://user:pass@staging-db:5432/aaa"
            base_config.redis.host = "staging-redis"
            base_config.cache.backend = "redis"
            base_config.security.enable_rate_limiting = True
            base_config.monitoring.enabled = True
            
        elif env == Environment.PRODUCTION:
            base_config.debug = False
            base_config.logging.level = "WARNING"
            base_config.logging.file_path = "logs/aaa-prod.log"
            base_config.database.url = "postgresql://user:pass@prod-db:5432/aaa"
            base_config.redis.host = "prod-redis"
            base_config.cache.backend = "redis"
            base_config.security.secret_key = "CHANGE-THIS-IN-PRODUCTION"
            base_config.security.enable_rate_limiting = True
            base_config.monitoring.enabled = True
            base_config.monitoring.alert_webhook_url = "https://alerts.company.com/webhook"
            base_config.api.enable_docs = False
            base_config.ui.enable_debug = False
        
        return base_config
    
    def _load_config_file(self, config_file: Path, env: Environment) -> EnvironmentConfig:
        """Load configuration from a YAML file."""
        try:
            with open(config_file, 'r') as f:
                data = yaml.safe_load(f) or {}
            
            # Start with default config
            config = self._get_default_config(env)
            
            # Override with file data
            self._merge_config_data(config, data)
            
            app_logger.info(f"Loaded configuration from {config_file}")
            return config
            
        except Exception as e:
            app_logger.error(f"Failed to load config file {config_file}: {e}")
            return self._get_default_config(env)
    
    def _merge_config_data(self, config: EnvironmentConfig, data: Dict[str, Any]):
        """Merge configuration data into config object."""
        for section_name, section_data in data.items():
            if hasattr(config, section_name) and isinstance(section_data, dict):
                section_obj = getattr(config, section_name)
                
                if hasattr(section_obj, '__dataclass_fields__'):
                    # It's a dataclass, update fields
                    for field_name, field_value in section_data.items():
                        if hasattr(section_obj, field_name):
                            setattr(section_obj, field_name, field_value)
                elif section_name == 'custom':
                    # Custom section - merge dictionaries
                    config.custom.update(section_data)
    
    def _save_config_file(self, config_file: Path, config: EnvironmentConfig):
        """Save configuration to a YAML file."""
        try:
            # Convert config to dictionary
            config_dict = self._config_to_dict(config)
            
            with open(config_file, 'w') as f:
                yaml.dump(config_dict, f, default_flow_style=False, indent=2)
                
        except Exception as e:
            app_logger.error(f"Failed to save config file {config_file}: {e}")
    
    def _config_to_dict(self, config: EnvironmentConfig) -> Dict[str, Any]:
        """Convert configuration object to dictionary."""
        from dataclasses import asdict
        
        config_dict = {}
        
        # Convert each section
        for field_name in config.__dataclass_fields__:
            if field_name == 'environment':
                config_dict[field_name] = config.environment.value
            else:
                field_value = getattr(config, field_name)
                if hasattr(field_value, '__dataclass_fields__'):
                    config_dict[field_name] = asdict(field_value)
                else:
                    config_dict[field_name] = field_value
        
        return config_dict
    
    def get_current_environment(self) -> Environment:
        """Get the current environment."""
        if self._current_env is None:
            # Determine from environment variable
            env_name = os.getenv('AAA_ENVIRONMENT', 'development').lower()
            
            try:
                self._current_env = Environment(env_name)
            except ValueError:
                app_logger.warning(f"Unknown environment '{env_name}', defaulting to development")
                self._current_env = Environment.DEVELOPMENT
        
        return self._current_env
    
    def set_environment(self, env: Environment):
        """Set the current environment."""
        self._current_env = env
        app_logger.info(f"Environment set to: {env.value}")
    
    def get_config(self, env: Optional[Environment] = None) -> EnvironmentConfig:
        """Get configuration for an environment."""
        if env is None:
            env = self.get_current_environment()
        
        if env not in self._configs:
            self._configs[env] = self._get_default_config(env)
        
        return self._configs[env]
    
    def get_current_config(self) -> EnvironmentConfig:
        """Get configuration for the current environment."""
        return self.get_config()
    
    def override_config(self, overrides: Dict[str, Any], env: Optional[Environment] = None):
        """Override configuration values."""
        if env is None:
            env = self.get_current_environment()
        
        config = self.get_config(env)
        self._merge_config_data(config, overrides)
        
        app_logger.info(f"Applied configuration overrides for {env.value}")
    
    def reload_config(self, env: Optional[Environment] = None):
        """Reload configuration from file."""
        if env is None:
            env = self.get_current_environment()
        
        config_file = self.config_dir / f"{env.value}.yaml"
        if config_file.exists():
            self._configs[env] = self._load_config_file(config_file, env)
            app_logger.info(f"Reloaded configuration for {env.value}")
        else:
            app_logger.warning(f"Configuration file not found: {config_file}")
    
    def validate_config(self, env: Optional[Environment] = None) -> Dict[str, list]:
        """Validate configuration and return any issues."""
        if env is None:
            env = self.get_current_environment()
        
        config = self.get_config(env)
        issues = {}
        
        # Validate security settings
        security_issues = []
        if env == Environment.PRODUCTION:
            if config.security.secret_key == "CHANGE-THIS-IN-PRODUCTION":
                security_issues.append("Secret key must be changed in production")
            if config.debug:
                security_issues.append("Debug mode should be disabled in production")
            if config.api.enable_docs:
                security_issues.append("API documentation should be disabled in production")
        
        if security_issues:
            issues["security"] = security_issues
        
        # Validate database settings
        db_issues = []
        if not config.database.url:
            db_issues.append("Database URL is required")
        
        if db_issues:
            issues["database"] = db_issues
        
        # Validate logging settings
        log_issues = []
        if config.logging.file_path and not Path(config.logging.file_path).parent.exists():
            log_issues.append(f"Log directory does not exist: {Path(config.logging.file_path).parent}")
        
        if log_issues:
            issues["logging"] = log_issues
        
        return issues
    
    def export_config(self, env: Optional[Environment] = None, file_path: Optional[str] = None) -> str:
        """Export configuration to YAML string or file."""
        if env is None:
            env = self.get_current_environment()
        
        config = self.get_config(env)
        config_dict = self._config_to_dict(config)
        
        yaml_content = yaml.dump(config_dict, default_flow_style=False, indent=2)
        
        if file_path:
            with open(file_path, 'w') as f:
                f.write(yaml_content)
            app_logger.info(f"Configuration exported to {file_path}")
        
        return yaml_content
    
    def list_environments(self) -> list:
        """List all available environments."""
        return [env.value for env in Environment]
    
    def get_config_summary(self) -> Dict[str, Any]:
        """Get a summary of all configurations."""
        summary = {
            "current_environment": self.get_current_environment().value,
            "available_environments": self.list_environments(),
            "configurations": {}
        }
        
        for env in Environment:
            config = self.get_config(env)
            issues = self.validate_config(env)
            
            summary["configurations"][env.value] = {
                "debug": config.debug,
                "database_url": config.database.url,
                "cache_backend": config.cache.backend,
                "monitoring_enabled": config.monitoring.enabled,
                "validation_issues": len(issues),
                "issues": issues
            }
        
        return summary


# Global configuration manager
_global_config_manager: Optional[ConfigurationManager] = None


def get_config_manager() -> ConfigurationManager:
    """Get the global configuration manager."""
    global _global_config_manager
    if _global_config_manager is None:
        _global_config_manager = ConfigurationManager()
    return _global_config_manager


def get_current_config() -> EnvironmentConfig:
    """Get the current environment configuration."""
    return get_config_manager().get_current_config()


def set_environment(env: Environment):
    """Set the current environment."""
    get_config_manager().set_environment(env)


def reload_current_config():
    """Reload the current environment configuration."""
    get_config_manager().reload_config()


# Environment-specific configuration getters
def get_development_config() -> EnvironmentConfig:
    """Get development configuration."""
    return get_config_manager().get_config(Environment.DEVELOPMENT)


def get_testing_config() -> EnvironmentConfig:
    """Get testing configuration."""
    return get_config_manager().get_config(Environment.TESTING)


def get_staging_config() -> EnvironmentConfig:
    """Get staging configuration."""
    return get_config_manager().get_config(Environment.STAGING)


def get_production_config() -> EnvironmentConfig:
    """Get production configuration."""
    return get_config_manager().get_config(Environment.PRODUCTION)