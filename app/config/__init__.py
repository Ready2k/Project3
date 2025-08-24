"""Configuration package initialization."""

# Import legacy Settings from the old config.py file using importlib
import importlib.util
from pathlib import Path

# Load the legacy config.py file
config_path = Path(__file__).parent.parent / "config.py"
spec = importlib.util.spec_from_file_location("app.config_legacy", config_path)
config_module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(config_module)

# Import Settings and load_settings from the legacy config module
Settings = config_module.Settings
load_settings = config_module.load_settings

# Import other classes and enums from the legacy config module
EmbeddingProvider = config_module.EmbeddingProvider
EmbeddingConfig = config_module.EmbeddingConfig
ConstraintsConfig = config_module.ConstraintsConfig
DetectorConfig = config_module.DetectorConfig
AdvancedPromptDefenseConfig = config_module.AdvancedPromptDefenseConfig
FeatureFlagConfig = config_module.FeatureFlagConfig
RollbackTriggerConfig = config_module.RollbackTriggerConfig
RollbackConfig = config_module.RollbackConfig
AttackPackMetadata = config_module.AttackPackMetadata
AttackPackVersion = config_module.AttackPackVersion
DeploymentConfig = config_module.DeploymentConfig
TimeoutConfig = config_module.TimeoutConfig
LoggingConfig = config_module.LoggingConfig
AuditConfig = config_module.AuditConfig
BedrockConfig = config_module.BedrockConfig
JiraAuthType = config_module.JiraAuthType
JiraDeploymentType = config_module.JiraDeploymentType
JiraConfig = config_module.JiraConfig

from .system_config import (
    AutonomyConfig,
    PatternMatchingConfig, 
    LLMGenerationConfig,
    RecommendationConfig,
    SystemConfiguration,
    SystemConfigurationManager
)

from .environments import (
    Environment,
    EnvironmentConfig,
    ConfigurationManager,
    DatabaseConfig,
    RedisConfig,
    SecurityConfig,
    LoggingConfig,
    MonitoringConfig,
    CacheConfig,
    APIConfig,
    UIConfig,
    get_config_manager,
    get_current_config,
    set_environment,
    reload_current_config,
    get_development_config,
    get_testing_config,
    get_staging_config,
    get_production_config
)

__all__ = [
    # Legacy configuration (from config.py)
    'Settings',
    'load_settings',
    'EmbeddingProvider',
    'EmbeddingConfig',
    'ConstraintsConfig',
    'DetectorConfig',
    'AdvancedPromptDefenseConfig',
    'FeatureFlagConfig',
    'RollbackTriggerConfig',
    'RollbackConfig',
    'AttackPackMetadata',
    'AttackPackVersion',
    'DeploymentConfig',
    'TimeoutConfig',
    'LoggingConfig',
    'AuditConfig',
    'BedrockConfig',
    'JiraAuthType',
    'JiraDeploymentType',
    'JiraConfig',
    
    # System configuration
    'AutonomyConfig',
    'PatternMatchingConfig',
    'LLMGenerationConfig', 
    'RecommendationConfig',
    'SystemConfiguration',
    'SystemConfigurationManager',
    
    # Environment configuration
    'Environment',
    'EnvironmentConfig',
    'ConfigurationManager',
    'DatabaseConfig',
    'RedisConfig',
    'SecurityConfig',
    'MonitoringConfig',
    'CacheConfig',
    'APIConfig',
    'UIConfig',
    
    # Configuration functions
    'get_config_manager',
    'get_current_config',
    'set_environment',
    'reload_current_config',
    'get_development_config',
    'get_testing_config',
    'get_staging_config',
    'get_production_config'
]