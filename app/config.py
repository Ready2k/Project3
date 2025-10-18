"""Configuration management with Pydantic settings."""

import os
from pathlib import Path
from typing import List, Optional, Dict, Any
from enum import Enum

import yaml
from pydantic import BaseModel, Field, field_validator
from pydantic_settings import BaseSettings

from app.version import __version__, RELEASE_NAME


class EmbeddingProvider(str, Enum):
    """Enumeration of supported embedding providers."""

    SENTENCE_TRANSFORMERS = "sentence_transformers"
    LLM_BASED = "llm_based"
    HASH_BASED = "hash_based"


class EmbeddingConfig(BaseModel):
    """Configuration for embedding generation."""

    provider: EmbeddingProvider = EmbeddingProvider.SENTENCE_TRANSFORMERS
    model_name: str = "all-MiniLM-L6-v2"
    dimension: int = 384
    cache_embeddings: bool = True
    fallback_provider: Optional[EmbeddingProvider] = EmbeddingProvider.HASH_BASED


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
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_session_token: Optional[str] = None
    bedrock_api_key: Optional[str] = None


class JiraAuthType(str, Enum):
    """Enumeration of supported Jira authentication types."""

    API_TOKEN = "api_token"
    PERSONAL_ACCESS_TOKEN = "pat"
    SSO = "sso"
    BASIC = "basic"


class JiraDeploymentType(str, Enum):
    """Enumeration of supported Jira deployment types."""

    CLOUD = "cloud"
    DATA_CENTER = "data_center"
    SERVER = "server"


class JiraConfig(BaseModel):
    """Configuration for Jira integration with Data Center support."""

    base_url: Optional[str] = None
    deployment_type: Optional[JiraDeploymentType] = None
    auth_type: JiraAuthType = JiraAuthType.API_TOKEN

    # Existing fields for backward compatibility
    email: Optional[str] = None
    api_token: Optional[str] = None

    # New fields for Data Center authentication
    username: Optional[str] = None
    password: Optional[str] = None
    personal_access_token: Optional[str] = None

    # Network configuration with environment variable support
    verify_ssl: bool = Field(default=True)
    ca_cert_path: Optional[str] = None
    proxy_url: Optional[str] = None
    timeout: int = 30

    def __init__(self, **data):
        """Initialize with environment variable overrides for SSL settings."""
        # Check for environment variable override for SSL verification
        env_verify_ssl = os.getenv("JIRA_VERIFY_SSL", "").lower()
        if env_verify_ssl in ("false", "0", "no", "off", "disabled"):
            data["verify_ssl"] = False
            print(
                "🌍 Environment variable JIRA_VERIFY_SSL detected - SSL verification DISABLED"
            )
        elif env_verify_ssl in ("true", "1", "yes", "on", "enabled"):
            data["verify_ssl"] = True
            print(
                "🌍 Environment variable JIRA_VERIFY_SSL detected - SSL verification ENABLED"
            )

        # Check for environment variable override for CA certificate path
        env_ca_cert = os.getenv("JIRA_CA_CERT_PATH")
        if env_ca_cert:
            data["ca_cert_path"] = env_ca_cert
            print(
                f"🌍 Environment variable JIRA_CA_CERT_PATH detected - Using CA cert: {env_ca_cert}"
            )

        super().__init__(**data)

    # SSO configuration
    use_sso: bool = False
    sso_session_cookie: Optional[str] = None

    # Data Center specific configuration
    context_path: Optional[str] = None
    custom_port: Optional[int] = None

    # Retry and timeout configuration
    max_retries: int = 3
    retry_delay: float = 1.0
    max_retry_delay: float = 60.0
    retry_backoff_multiplier: float = 2.0
    total_timeout: Optional[int] = None

    @field_validator("base_url")
    @classmethod
    def validate_base_url(cls, v):
        """Validate and normalize base URL."""
        if v is not None:
            v = v.rstrip("/")
            if not v.startswith(("http://", "https://")):
                raise ValueError("Base URL must start with http:// or https://")
        return v

    @field_validator("custom_port")
    @classmethod
    def validate_custom_port(cls, v):
        """Validate custom port range."""
        if v is not None and (v < 1 or v > 65535):
            raise ValueError("Custom port must be between 1 and 65535")
        return v

    @field_validator("timeout")
    @classmethod
    def validate_timeout(cls, v):
        """Validate timeout value."""
        if v < 1:
            raise ValueError("Timeout must be at least 1 second")
        return v

    @field_validator("max_retries")
    @classmethod
    def validate_max_retries(cls, v):
        """Validate max retries value."""
        if v < 0:
            raise ValueError("Max retries must be non-negative")
        if v > 10:
            raise ValueError("Max retries should not exceed 10")
        return v

    @field_validator("retry_delay")
    @classmethod
    def validate_retry_delay(cls, v):
        """Validate retry delay value."""
        if v < 0:
            raise ValueError("Retry delay must be non-negative")
        return v

    @field_validator("retry_backoff_multiplier")
    @classmethod
    def validate_retry_backoff_multiplier(cls, v):
        """Validate retry backoff multiplier."""
        if v < 1.0:
            raise ValueError("Retry backoff multiplier must be at least 1.0")
        return v

    def validate_auth_config(self) -> List[str]:
        """Validate authentication configuration and return any errors."""
        errors = []

        if self.auth_type == JiraAuthType.API_TOKEN:
            if not self.email:
                errors.append("Email is required for API token authentication")
            if not self.api_token:
                errors.append("API token is required for API token authentication")

        elif self.auth_type == JiraAuthType.PERSONAL_ACCESS_TOKEN:
            if not self.personal_access_token:
                errors.append(
                    "Personal access token is required for PAT authentication"
                )

        elif self.auth_type == JiraAuthType.BASIC:
            if not self.username:
                errors.append("Username is required for basic authentication")
            if not self.password:
                errors.append("Password is required for basic authentication")

        elif self.auth_type == JiraAuthType.SSO:
            if not self.use_sso:
                errors.append("SSO must be enabled for SSO authentication")

        return errors

    def is_data_center_deployment(self) -> bool:
        """Check if this is a Data Center deployment."""
        return self.deployment_type == JiraDeploymentType.DATA_CENTER

    def is_cloud_deployment(self) -> bool:
        """Check if this is a Cloud deployment."""
        return self.deployment_type == JiraDeploymentType.CLOUD

    def get_normalized_base_url(self) -> Optional[str]:
        """Get normalized base URL with custom port and context path."""
        if not self.base_url:
            return None

        url = self.base_url

        # Add custom port if specified and not already in URL
        if self.custom_port and ":" not in url.split("://", 1)[1]:
            url = f"{url}:{self.custom_port}"

        # Add context path if specified
        if self.context_path:
            context = self.context_path.strip("/")
            if context:
                url = f"{url}/{context}"

        return url

    def disable_ssl_verification(self) -> None:
        """Convenience method to disable SSL verification for testing.

        Warning: This should only be used for testing with self-signed certificates.
        Never use this in production environments.
        """
        self.verify_ssl = False
        self.ca_cert_path = None

    def enable_ssl_verification(self, ca_cert_path: Optional[str] = None) -> None:
        """Convenience method to enable SSL verification.

        Args:
            ca_cert_path: Optional path to custom CA certificate bundle
        """
        self.verify_ssl = True
        self.ca_cert_path = ca_cert_path

    def get_ssl_config_summary(self) -> Dict[str, Any]:
        """Get a summary of SSL configuration for troubleshooting.

        Returns:
            Dictionary with SSL configuration details
        """
        return {
            "ssl_verification_enabled": self.verify_ssl,
            "custom_ca_certificate": bool(self.ca_cert_path),
            "ca_cert_path": self.ca_cert_path,
            "base_url_uses_https": bool(
                self.base_url and self.base_url.startswith("https://")
            ),
            "ssl_troubleshooting_tip": (
                "If you're having SSL issues with self-signed certificates, "
                "you can temporarily disable SSL verification by setting verify_ssl=False. "
                "For production, add your CA certificate to ca_cert_path instead."
            ),
        }


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
    embedding: EmbeddingConfig = Field(default_factory=EmbeddingConfig)
    advanced_prompt_defense: AdvancedPromptDefenseConfig = Field(
        default_factory=AdvancedPromptDefenseConfig
    )
    deployment: DeploymentConfig = Field(
        default_factory=lambda: DeploymentConfig(
            last_updated="2025-08-16T00:00:00.000000", updated_by="system"
        )
    )

    model_config = {
        "env_file": ".env",
        "env_nested_delimiter": "_",
        "extra": "ignore",
        "validate_default": True,
        "case_sensitive": False,
    }


def load_settings(config_path: Optional[str] = None) -> Settings:
    """Load settings from YAML file and environment variables.

    Environment variables take precedence over YAML configuration.
    """
    # Load .env file if it exists
    try:
        from dotenv import load_dotenv

        env_file = Path(".env")
        if env_file.exists():
            load_dotenv(env_file)
            print(f"✅ Loaded environment variables from {env_file}")
        else:
            print("ℹ️ No .env file found, using system environment variables only")
    except ImportError:
        print("⚠️ python-dotenv not installed, .env file will not be loaded")
    except Exception as e:
        print(f"⚠️ Error loading .env file: {e}")

    config_data = {}

    # Load from YAML if provided
    if config_path and Path(config_path).exists():
        with open(config_path, "r") as f:
            config_data = yaml.safe_load(f) or {}
    elif Path("config.yaml").exists():
        with open("config.yaml", "r") as f:
            config_data = yaml.safe_load(f) or {}

    # Override with environment variables
    env_overrides = {}
    for key in ["provider", "model", "logging_level"]:
        env_key = key.upper()
        if env_key in os.environ:
            if key == "logging_level":
                if "logging" not in env_overrides:
                    env_overrides["logging"] = {}
                env_overrides["logging"]["level"] = os.environ[env_key]
            else:
                env_overrides[key] = os.environ[env_key]

    # Handle Jira environment variables
    jira_env_vars = {
        "JIRA_BASE_URL": "base_url",
        "JIRA_EMAIL": "email",
        "JIRA_API_TOKEN": "api_token",
        "JIRA_TIMEOUT": "timeout",
        "JIRA_DEPLOYMENT_TYPE": "deployment_type",
        "JIRA_AUTH_TYPE": "auth_type",
        "JIRA_USERNAME": "username",
        "JIRA_PASSWORD": "password",
        "JIRA_PERSONAL_ACCESS_TOKEN": "personal_access_token",
        "JIRA_VERIFY_SSL": "verify_ssl",
        "JIRA_CA_CERT_PATH": "ca_cert_path",
        "JIRA_PROXY_URL": "proxy_url",
        "JIRA_USE_SSO": "use_sso",
        "JIRA_SSO_SESSION_COOKIE": "sso_session_cookie",
        "JIRA_CONTEXT_PATH": "context_path",
        "JIRA_CUSTOM_PORT": "custom_port",
    }

    jira_config = {}
    for env_key, config_key in jira_env_vars.items():
        if env_key in os.environ:
            value = os.environ[env_key]
            # Type conversions
            if config_key in ["timeout", "custom_port"]:
                value = int(value)
            elif config_key in ["verify_ssl", "use_sso"]:
                value = value.lower() in ("true", "1", "yes", "on")
            jira_config[config_key] = value

    if jira_config:
        env_overrides["jira"] = jira_config

    # Handle AWS Bedrock environment variables
    bedrock_env_vars = {
        "AWS_ACCESS_KEY_ID": "aws_access_key_id",
        "AWS_SECRET_ACCESS_KEY": "aws_secret_access_key",
        "AWS_SESSION_TOKEN": "aws_session_token",
        "BEDROCK_REGION": "region",
        "BEDROCK_API_KEY": "bedrock_api_key",
    }

    bedrock_config = {}
    for env_key, config_key in bedrock_env_vars.items():
        if env_key in os.environ:
            bedrock_config[config_key] = os.environ[env_key]

    if bedrock_config:
        env_overrides["bedrock"] = bedrock_config

    # Merge config data with environment overrides
    config_data.update(env_overrides)

    return Settings(**config_data)
