"""Configuration management with Pydantic settings."""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings

from app.version import __version__, RELEASE_NAME


class ConstraintsConfig(BaseModel):
    """Configuration for system constraints."""
    unavailable_tools: List[str] = Field(default_factory=list)


class DetectorConfig(BaseModel):
    """Configuration for individual security detectors."""
    enabled: bool = True
    confidence_threshold: float = 0.7
    sensitivity: str = "medium"
    custom_settings: Dict[str, Any] = Field(default_factory=dict)


class AdvancedPromptDefenseConfig(BaseModel):
    """Configuration for advanced prompt defense system."""
    enabled: bool = True
    detection_confidence_threshold: float = 0.7
    flag_threshold: float = 0.5
    block_threshold: float = 0.9
    max_validation_time_ms: int = 100
    enable_caching: bool = True
    cache_ttl_seconds: int = 300
    parallel_detection: bool = True
    log_all_detections: bool = True
    metrics_enabled: bool = True
    alert_on_attacks: bool = True
    educational_messages: bool = True
    provide_user_guidance: bool = True
    appeal_mechanism: bool = True
    attack_pack_version: str = "v2"
    
    # Individual detector configurations
    overt_injection: DetectorConfig = Field(default_factory=DetectorConfig)
    covert_injection: DetectorConfig = Field(default_factory=DetectorConfig)
    context_attack_detector: DetectorConfig = Field(default_factory=DetectorConfig)
    data_egress_detector: DetectorConfig = Field(default_factory=DetectorConfig)
    protocol_tampering_detector: DetectorConfig = Field(default_factory=DetectorConfig)
    scope_validator: DetectorConfig = Field(default_factory=DetectorConfig)
    multilingual_attack_detector: DetectorConfig = Field(default_factory=DetectorConfig)
    business_logic_protector: DetectorConfig = Field(default_factory=DetectorConfig)


class FeatureFlagConfig(BaseModel):
    """Configuration for individual feature flags."""
    enabled: bool = False
    rollout_percentage: float = 100.0
    stage: str = "full"
    target_groups: List[str] = Field(default_factory=list)
    metadata: Dict[str, Any] = Field(default_factory=dict)


class RollbackTriggerConfig(BaseModel):
    """Configuration for rollback triggers."""
    threshold: Optional[float] = None
    threshold_ms: Optional[int] = None
    window_minutes: Optional[int] = None
    min_requests: Optional[int] = None
    consecutive_failures: Optional[int] = None
    check_interval_seconds: Optional[int] = None


class RollbackConfig(BaseModel):
    """Configuration for automatic rollback system."""
    enabled: bool = True
    max_rollbacks_per_day: int = 5
    cooldown_minutes: int = 30
    notification_channels: List[str] = Field(default_factory=list)
    triggers: Dict[str, RollbackTriggerConfig] = Field(default_factory=dict)


class AttackPackMetadata(BaseModel):
    """Metadata for attack pack versions."""
    version: str
    pattern_count: int
    checksum: str
    source_file: str
    installed_at: str
    validation_result: Dict[str, Any] = Field(default_factory=dict)


class AttackPackVersion(BaseModel):
    """Configuration for attack pack versions."""
    file_path: str
    checksum: str
    pattern_count: int
    validation_status: str
    is_active: bool = False
    deployed_at: str
    metadata: AttackPackMetadata


class DeploymentConfig(BaseModel):
    """Configuration for deployment and feature management."""
    config_version: str = "1.0"
    deployment_environment: str = "production"
    last_updated: str
    updated_by: str = "system"
    
    # Feature flags
    feature_flags: Dict[str, FeatureFlagConfig] = Field(default_factory=dict)
    
    # Rollout configuration
    gradual_rollout_enabled: bool = True
    canary_user_percentage: float = 1.0
    beta_user_percentage: float = 10.0
    staged_user_percentage: float = 50.0
    
    # Attack pack management
    active_attack_pack_version: str = "v2"
    attack_pack_versions: Dict[str, AttackPackVersion] = Field(default_factory=dict)
    
    # Monitoring and health checks
    monitoring_enabled: bool = True
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    health_check_endpoints: List[str] = Field(default_factory=list)
    metrics_retention_days: int = 30
    alert_channels: List[str] = Field(default_factory=list)
    
    # Rollback configuration
    rollback_config: RollbackConfig = Field(default_factory=RollbackConfig)


class TimeoutConfig(BaseModel):
    """Configuration for timeouts."""
    llm: int = 20
    http: int = 10


class LoggingConfig(BaseModel):
    """Configuration for logging."""
    level: str = "INFO"
    redact_pii: bool = True


class AuditConfig(BaseModel):
    """Configuration for audit and observability."""
    enabled: bool = True
    db_path: str = "audit.db"
    redact_pii: bool = True
    cleanup_days: int = 30


class BedrockConfig(BaseModel):
    """Configuration for AWS Bedrock."""
    region: str = "eu-west-2"


class JiraConfig(BaseModel):
    """Configuration for Jira integration."""
    base_url: Optional[str] = None
    email: Optional[str] = None
    api_token: Optional[str] = None
    timeout: int = 30


class Settings(BaseSettings):
    """Main application settings."""
    version: str = __version__
    release_name: str = RELEASE_NAME
    provider: str = "openai"
    model: str = "gpt-4o"
    pattern_library_path: Path = Path("./data/patterns")
    export_path: Path = Path("./exports")
    disable_fake_llm: bool = False  # If True, never fallback to FakeLLM
    constraints: ConstraintsConfig = Field(default_factory=ConstraintsConfig)
    timeouts: TimeoutConfig = Field(default_factory=TimeoutConfig)
    logging: LoggingConfig = Field(default_factory=LoggingConfig)
    bedrock: BedrockConfig = Field(default_factory=BedrockConfig)
    jira: JiraConfig = Field(default_factory=JiraConfig)
    audit: AuditConfig = Field(default_factory=AuditConfig)
    advanced_prompt_defense: AdvancedPromptDefenseConfig = Field(default_factory=AdvancedPromptDefenseConfig)
    deployment: DeploymentConfig = Field(default_factory=lambda: DeploymentConfig(
        last_updated="2025-08-16T00:00:00.000000",
        updated_by="system"
    ))

    model_config = {"env_file": ".env", "env_nested_delimiter": "_"}


def load_settings(config_path: Optional[str] = None) -> Settings:
    """Load settings from YAML file and environment variables.
    
    Environment variables take precedence over YAML configuration.
    """
    config_data = {}
    
    # Load from YAML if provided
    if config_path and Path(config_path).exists():
        with open(config_path, 'r') as f:
            config_data = yaml.safe_load(f) or {}
    elif Path("config.yaml").exists():
        with open("config.yaml", 'r') as f:
            config_data = yaml.safe_load(f) or {}
    
    # Override with environment variables
    env_overrides = {}
    for key in ['provider', 'model', 'logging_level']:
        env_key = key.upper()
        if env_key in os.environ:
            if key == 'logging_level':
                if 'logging' not in env_overrides:
                    env_overrides['logging'] = {}
                env_overrides['logging']['level'] = os.environ[env_key]
            else:
                env_overrides[key] = os.environ[env_key]
    
    # Handle Jira environment variables
    jira_env_vars = {
        'JIRA_BASE_URL': 'base_url',
        'JIRA_EMAIL': 'email', 
        'JIRA_API_TOKEN': 'api_token',
        'JIRA_TIMEOUT': 'timeout'
    }
    
    jira_config = {}
    for env_key, config_key in jira_env_vars.items():
        if env_key in os.environ:
            value = os.environ[env_key]
            if config_key == 'timeout':
                value = int(value)
            jira_config[config_key] = value
    
    if jira_config:
        env_overrides['jira'] = jira_config
    
    # Merge config data with environment overrides
    config_data.update(env_overrides)
    
    return Settings(**config_data)