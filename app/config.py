"""Configuration management with Pydantic settings."""

import os
from pathlib import Path
from typing import List, Optional

import yaml
from pydantic import BaseModel, Field
from pydantic_settings import BaseSettings


class ConstraintsConfig(BaseModel):
    """Configuration for system constraints."""
    unavailable_tools: List[str] = Field(default_factory=list)


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