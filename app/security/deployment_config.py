"""
Deployment configuration and management for advanced prompt defense system.
Handles feature flags, gradual rollout, and rollback mechanisms.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set
from pathlib import Path
from datetime import datetime
import yaml
from enum import Enum

from app.utils.logger import app_logger


class DeploymentStage(Enum):
    """Deployment stages for gradual rollout."""

    DISABLED = "disabled"
    CANARY = "canary"  # 1-5% of traffic
    BETA = "beta"  # 10-25% of traffic
    STAGED = "staged"  # 50% of traffic
    FULL = "full"  # 100% of traffic


class RollbackTrigger(Enum):
    """Triggers for automatic rollback."""

    HIGH_ERROR_RATE = "high_error_rate"
    HIGH_LATENCY = "high_latency"
    HIGH_FALSE_POSITIVE_RATE = "high_false_positive_rate"
    MANUAL = "manual"
    HEALTH_CHECK_FAILURE = "health_check_failure"


@dataclass
class FeatureFlag:
    """Configuration for individual feature flags."""

    name: str
    enabled: bool = False
    description: str = ""
    stage: DeploymentStage = DeploymentStage.DISABLED
    rollout_percentage: float = 0.0
    target_groups: Set[str] = field(default_factory=set)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    metadata: Dict = field(default_factory=dict)


@dataclass
class RollbackConfig:
    """Configuration for automatic rollback mechanisms."""

    enabled: bool = True
    triggers: Dict[RollbackTrigger, Dict] = field(
        default_factory=lambda: {
            RollbackTrigger.HIGH_ERROR_RATE: {
                "threshold": 0.05,  # 5% error rate
                "window_minutes": 5,
                "min_requests": 100,
            },
            RollbackTrigger.HIGH_LATENCY: {
                "threshold_ms": 200,  # 200ms average latency
                "window_minutes": 5,
                "min_requests": 100,
            },
            RollbackTrigger.HIGH_FALSE_POSITIVE_RATE: {
                "threshold": 0.10,  # 10% false positive rate
                "window_minutes": 10,
                "min_requests": 50,
            },
            RollbackTrigger.HEALTH_CHECK_FAILURE: {
                "consecutive_failures": 3,
                "check_interval_seconds": 30,
            },
        }
    )
    cooldown_minutes: int = 30  # Minimum time between rollbacks
    max_rollbacks_per_day: int = 5
    notification_channels: List[str] = field(default_factory=list)


@dataclass
class AttackPackVersion:
    """Configuration for attack pack version management."""

    version: str
    file_path: str
    checksum: str
    deployed_at: datetime
    is_active: bool = False
    validation_status: str = "pending"  # pending, validated, failed
    pattern_count: int = 0
    metadata: Dict = field(default_factory=dict)


@dataclass
class DeploymentConfig:
    """Main deployment configuration for advanced prompt defense."""

    # Feature flags for individual detectors
    feature_flags: Dict[str, FeatureFlag] = field(
        default_factory=lambda: {
            "advanced_prompt_defense": FeatureFlag(
                name="advanced_prompt_defense",
                description="Master switch for advanced prompt defense system",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "overt_injection_detector": FeatureFlag(
                name="overt_injection_detector",
                description="Detector for overt prompt injection attacks",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "covert_injection_detector": FeatureFlag(
                name="covert_injection_detector",
                description="Detector for covert and obfuscated injection attacks",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "scope_validator": FeatureFlag(
                name="scope_validator",
                description="Validator for out-of-scope task prevention",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "data_egress_detector": FeatureFlag(
                name="data_egress_detector",
                description="Detector for data egress and information disclosure",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "protocol_tampering_detector": FeatureFlag(
                name="protocol_tampering_detector",
                description="Detector for protocol and schema tampering",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "context_attack_detector": FeatureFlag(
                name="context_attack_detector",
                description="Detector for long-context burying attacks",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "multilingual_attack_detector": FeatureFlag(
                name="multilingual_attack_detector",
                description="Detector for multilingual attacks",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "business_logic_protector": FeatureFlag(
                name="business_logic_protector",
                description="Protector for business logic and safety toggles",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "performance_optimization": FeatureFlag(
                name="performance_optimization",
                description="Performance optimization features",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "user_education": FeatureFlag(
                name="user_education",
                description="User education and guidance system",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
            "security_monitoring": FeatureFlag(
                name="security_monitoring",
                description="Security event logging and monitoring",
                stage=DeploymentStage.FULL,
                rollout_percentage=100.0,
            ),
        }
    )

    # Rollback configuration
    rollback_config: RollbackConfig = field(default_factory=RollbackConfig)

    # Attack pack version management
    attack_pack_versions: Dict[str, AttackPackVersion] = field(default_factory=dict)
    active_attack_pack_version: str = "v2"

    # Deployment settings
    deployment_environment: str = "production"  # development, staging, production
    gradual_rollout_enabled: bool = True
    canary_user_percentage: float = 1.0
    beta_user_percentage: float = 10.0
    staged_user_percentage: float = 50.0

    # Health check settings
    health_check_enabled: bool = True
    health_check_interval_seconds: int = 30
    health_check_timeout_seconds: int = 10
    health_check_endpoints: List[str] = field(
        default_factory=lambda: [
            "/health/security",
            "/health/detectors",
            "/health/performance",
        ]
    )

    # Monitoring and alerting
    monitoring_enabled: bool = True
    alert_channels: List[str] = field(default_factory=list)
    metrics_retention_days: int = 30

    # Configuration metadata
    config_version: str = "1.0"
    last_updated: datetime = field(default_factory=datetime.utcnow)
    updated_by: str = "system"

    @classmethod
    def load_from_file(cls, config_file: str) -> "DeploymentConfig":
        """Load deployment configuration from YAML file."""
        try:
            config_path = Path(config_file)
            if not config_path.exists():
                app_logger.warning(
                    f"Deployment config file {config_file} not found, using defaults"
                )
                return cls()

            with open(config_path, "r", encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            # Extract deployment config
            deployment_data = config_data.get("deployment", {})

            config = cls()

            # Load feature flags
            if "feature_flags" in deployment_data:
                for flag_name, flag_data in deployment_data["feature_flags"].items():
                    if flag_name in config.feature_flags:
                        flag = config.feature_flags[flag_name]
                    else:
                        # Create new feature flag if it doesn't exist
                        flag = FeatureFlag(
                            name=flag_name,
                            description=flag_data.get(
                                "description", f"Feature flag for {flag_name}"
                            ),
                            created_at=datetime.utcnow(),
                        )
                        config.feature_flags[flag_name] = flag

                    flag.enabled = flag_data.get("enabled", flag.enabled)
                    flag.stage = DeploymentStage(
                        flag_data.get("stage", flag.stage.value)
                    )
                    flag.rollout_percentage = flag_data.get(
                        "rollout_percentage", flag.rollout_percentage
                    )
                    flag.target_groups = set(flag_data.get("target_groups", []))
                    flag.metadata = flag_data.get("metadata", {})

            # Load rollback config
            if "rollback_config" in deployment_data:
                rollback_data = deployment_data["rollback_config"]
                config.rollback_config.enabled = rollback_data.get(
                    "enabled", config.rollback_config.enabled
                )
                config.rollback_config.cooldown_minutes = rollback_data.get(
                    "cooldown_minutes", config.rollback_config.cooldown_minutes
                )
                config.rollback_config.max_rollbacks_per_day = rollback_data.get(
                    "max_rollbacks_per_day",
                    config.rollback_config.max_rollbacks_per_day,
                )
                config.rollback_config.notification_channels = rollback_data.get(
                    "notification_channels", []
                )

                # Load rollback triggers
                if "triggers" in rollback_data:
                    for trigger_name, trigger_config in rollback_data[
                        "triggers"
                    ].items():
                        try:
                            trigger = RollbackTrigger(trigger_name)
                            config.rollback_config.triggers[trigger] = trigger_config
                        except ValueError:
                            app_logger.warning(
                                f"Unknown rollback trigger: {trigger_name}"
                            )

            # Load attack pack versions
            if "attack_pack_versions" in deployment_data:
                for version, version_data in deployment_data[
                    "attack_pack_versions"
                ].items():
                    config.attack_pack_versions[version] = AttackPackVersion(
                        version=version,
                        file_path=version_data.get("file_path", ""),
                        checksum=version_data.get("checksum", ""),
                        deployed_at=datetime.fromisoformat(
                            version_data.get(
                                "deployed_at", datetime.utcnow().isoformat()
                            )
                        ),
                        is_active=version_data.get("is_active", False),
                        validation_status=version_data.get(
                            "validation_status", "pending"
                        ),
                        pattern_count=version_data.get("pattern_count", 0),
                        metadata=version_data.get("metadata", {}),
                    )

            # Load other settings
            for key, value in deployment_data.items():
                if hasattr(config, key) and key not in [
                    "feature_flags",
                    "rollback_config",
                    "attack_pack_versions",
                ]:
                    setattr(config, key, value)

            app_logger.info(f"Loaded deployment config from {config_file}")
            return config

        except Exception as e:
            app_logger.error(
                f"Failed to load deployment config from {config_file}: {e}"
            )
            app_logger.info("Using default deployment configuration")
            return cls()

    def save_to_file(self, config_file: str) -> None:
        """Save deployment configuration to YAML file."""
        try:
            # Load existing config file to preserve other settings
            config_path = Path(config_file)
            existing_config = {}

            if config_path.exists():
                with open(config_path, "r", encoding="utf-8") as f:
                    existing_config = yaml.safe_load(f) or {}

            # Convert feature flags to dict
            feature_flags_dict = {}
            for flag_name, flag in self.feature_flags.items():
                feature_flags_dict[flag_name] = {
                    "enabled": flag.enabled,
                    "stage": flag.stage.value,
                    "rollout_percentage": flag.rollout_percentage,
                    "target_groups": list(flag.target_groups),
                    "metadata": flag.metadata,
                }

            # Convert rollback config to dict
            rollback_dict = {
                "enabled": self.rollback_config.enabled,
                "cooldown_minutes": self.rollback_config.cooldown_minutes,
                "max_rollbacks_per_day": self.rollback_config.max_rollbacks_per_day,
                "notification_channels": self.rollback_config.notification_channels,
                "triggers": {
                    trigger.value: config
                    for trigger, config in self.rollback_config.triggers.items()
                },
            }

            # Convert attack pack versions to dict
            attack_pack_dict = {}
            for version, pack_info in self.attack_pack_versions.items():
                attack_pack_dict[version] = {
                    "file_path": pack_info.file_path,
                    "checksum": pack_info.checksum,
                    "deployed_at": (
                        pack_info.deployed_at.isoformat()
                        if isinstance(pack_info.deployed_at, datetime)
                        else pack_info.deployed_at
                    ),
                    "is_active": pack_info.is_active,
                    "validation_status": pack_info.validation_status,
                    "pattern_count": pack_info.pattern_count,
                    "metadata": pack_info.metadata,
                }

            # Create deployment config dict
            deployment_config = {
                "feature_flags": feature_flags_dict,
                "rollback_config": rollback_dict,
                "attack_pack_versions": attack_pack_dict,
                "active_attack_pack_version": self.active_attack_pack_version,
                "deployment_environment": self.deployment_environment,
                "gradual_rollout_enabled": self.gradual_rollout_enabled,
                "canary_user_percentage": self.canary_user_percentage,
                "beta_user_percentage": self.beta_user_percentage,
                "staged_user_percentage": self.staged_user_percentage,
                "health_check_enabled": self.health_check_enabled,
                "health_check_interval_seconds": self.health_check_interval_seconds,
                "health_check_timeout_seconds": self.health_check_timeout_seconds,
                "health_check_endpoints": self.health_check_endpoints,
                "monitoring_enabled": self.monitoring_enabled,
                "alert_channels": self.alert_channels,
                "metrics_retention_days": self.metrics_retention_days,
                "config_version": self.config_version,
                "last_updated": (
                    self.last_updated.isoformat()
                    if isinstance(self.last_updated, datetime)
                    else self.last_updated
                ),
                "updated_by": self.updated_by,
            }

            # Update existing config
            existing_config["deployment"] = deployment_config

            # Save to file
            with open(config_path, "w", encoding="utf-8") as f:
                yaml.dump(existing_config, f, default_flow_style=False, indent=2)

            app_logger.info(f"Saved deployment config to {config_file}")

        except Exception as e:
            app_logger.error(f"Failed to save deployment config to {config_file}: {e}")
            raise

    def is_feature_enabled(
        self,
        feature_name: str,
        user_id: Optional[str] = None,
        user_groups: Optional[Set[str]] = None,
    ) -> bool:
        """Check if a feature is enabled for a specific user/context."""
        if feature_name not in self.feature_flags:
            app_logger.warning(f"Unknown feature flag: {feature_name}")
            return False

        flag = self.feature_flags[feature_name]

        # Check if feature is globally disabled
        if not flag.enabled:
            return False

        # Check deployment stage
        if flag.stage == DeploymentStage.DISABLED:
            return False
        elif flag.stage == DeploymentStage.FULL:
            return True

        # Check target groups
        if user_groups and flag.target_groups:
            if flag.target_groups.intersection(user_groups):
                return True

        # Check rollout percentage
        if user_id:
            # Use consistent hash-based rollout
            import hashlib

            hash_value = int(
                hashlib.md5(f"{feature_name}:{user_id}".encode()).hexdigest(), 16
            )
            user_percentage = (hash_value % 100) + 1
            return user_percentage <= flag.rollout_percentage

        # Default fallback
        return flag.rollout_percentage >= 100.0

    def enable_feature(
        self,
        feature_name: str,
        stage: DeploymentStage = DeploymentStage.FULL,
        rollout_percentage: float = 100.0,
        target_groups: Optional[Set[str]] = None,
    ) -> None:
        """Enable a feature flag with specified parameters."""
        if feature_name not in self.feature_flags:
            # Create new feature flag if it doesn't exist
            self.feature_flags[feature_name] = FeatureFlag(
                name=feature_name,
                description=f"Feature flag for {feature_name}",
                created_at=datetime.utcnow(),
            )

        flag = self.feature_flags[feature_name]
        flag.enabled = True
        flag.stage = stage
        flag.rollout_percentage = rollout_percentage
        if target_groups:
            flag.target_groups = target_groups
        flag.updated_at = datetime.utcnow()

        app_logger.info(
            f"Enabled feature {feature_name} at stage {stage.value} with {rollout_percentage}% rollout"
        )

    def disable_feature(self, feature_name: str) -> None:
        """Disable a feature flag."""
        if feature_name not in self.feature_flags:
            app_logger.warning(f"Unknown feature flag: {feature_name}")
            return

        flag = self.feature_flags[feature_name]
        flag.enabled = False
        flag.stage = DeploymentStage.DISABLED
        flag.updated_at = datetime.utcnow()

        app_logger.info(f"Disabled feature {feature_name}")

    def rollback_feature(self, feature_name: str, reason: str = "manual") -> None:
        """Rollback a feature to disabled state."""
        if feature_name not in self.feature_flags:
            app_logger.warning(f"Unknown feature flag: {feature_name}")
            return

        flag = self.feature_flags[feature_name]

        # Capture current state before rollback
        previous_stage = flag.stage.value
        previous_rollout_percentage = flag.rollout_percentage

        # Disable the feature
        self.disable_feature(feature_name)

        # Log rollback event
        app_logger.warning(f"Rolled back feature {feature_name}, reason: {reason}")

        # Update metadata with rollback history
        if "rollback_history" not in flag.metadata:
            flag.metadata["rollback_history"] = []

        flag.metadata["rollback_history"].append(
            {
                "timestamp": datetime.utcnow().isoformat(),
                "reason": reason,
                "previous_stage": previous_stage,
                "previous_rollout_percentage": previous_rollout_percentage,
            }
        )

    def get_active_attack_pack(self) -> Optional[AttackPackVersion]:
        """Get the currently active attack pack version."""
        return self.attack_pack_versions.get(self.active_attack_pack_version)

    def deploy_attack_pack(self, version: str, file_path: str, checksum: str) -> bool:
        """Deploy a new attack pack version."""
        try:
            # Validate file exists
            if not Path(file_path).exists():
                app_logger.error(f"Attack pack file not found: {file_path}")
                return False

            # Create new version entry
            new_version = AttackPackVersion(
                version=version,
                file_path=file_path,
                checksum=checksum,
                deployed_at=datetime.utcnow(),
                is_active=False,
                validation_status="pending",
            )

            # Add to versions
            self.attack_pack_versions[version] = new_version

            app_logger.info(f"Deployed attack pack version {version}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to deploy attack pack version {version}: {e}")
            return False

    def activate_attack_pack(self, version: str) -> bool:
        """Activate a specific attack pack version."""
        if version not in self.attack_pack_versions:
            app_logger.error(f"Attack pack version {version} not found")
            return False

        try:
            # Deactivate current version
            if self.active_attack_pack_version in self.attack_pack_versions:
                self.attack_pack_versions[self.active_attack_pack_version].is_active = (
                    False
                )

            # Activate new version
            self.attack_pack_versions[version].is_active = True
            self.active_attack_pack_version = version

            app_logger.info(f"Activated attack pack version {version}")
            return True

        except Exception as e:
            app_logger.error(f"Failed to activate attack pack version {version}: {e}")
            return False

    def validate_config(self) -> List[str]:
        """Validate deployment configuration and return list of issues."""
        issues = []

        # Validate percentages
        for flag_name, flag in self.feature_flags.items():
            if not 0.0 <= flag.rollout_percentage <= 100.0:
                issues.append(
                    f"Feature {flag_name} rollout_percentage must be between 0.0 and 100.0"
                )

        if not 0.0 <= self.canary_user_percentage <= 100.0:
            issues.append("canary_user_percentage must be between 0.0 and 100.0")

        if not 0.0 <= self.beta_user_percentage <= 100.0:
            issues.append("beta_user_percentage must be between 0.0 and 100.0")

        if not 0.0 <= self.staged_user_percentage <= 100.0:
            issues.append("staged_user_percentage must be between 0.0 and 100.0")

        # Validate rollback config
        for trigger, config in self.rollback_config.triggers.items():
            if trigger == RollbackTrigger.HIGH_ERROR_RATE:
                if not 0.0 <= config.get("threshold", 0) <= 1.0:
                    issues.append(
                        "High error rate threshold must be between 0.0 and 1.0"
                    )
            elif trigger == RollbackTrigger.HIGH_FALSE_POSITIVE_RATE:
                if not 0.0 <= config.get("threshold", 0) <= 1.0:
                    issues.append(
                        "High false positive rate threshold must be between 0.0 and 1.0"
                    )

        # Validate health check settings
        if self.health_check_interval_seconds <= 0:
            issues.append("health_check_interval_seconds must be positive")

        if self.health_check_timeout_seconds <= 0:
            issues.append("health_check_timeout_seconds must be positive")

        if self.metrics_retention_days <= 0:
            issues.append("metrics_retention_days must be positive")

        # Validate attack pack versions
        active_version_exists = False
        for version, pack_info in self.attack_pack_versions.items():
            if pack_info.is_active:
                if active_version_exists:
                    issues.append("Multiple active attack pack versions found")
                active_version_exists = True

                if version != self.active_attack_pack_version:
                    issues.append(
                        f"Active version mismatch: {version} vs {self.active_attack_pack_version}"
                    )

        return issues


# Global deployment configuration instance
_deployment_config: Optional[DeploymentConfig] = None


def get_deployment_config() -> DeploymentConfig:
    """Get the global deployment configuration instance."""
    global _deployment_config
    if _deployment_config is None:
        _deployment_config = DeploymentConfig.load_from_file("config.yaml")
    return _deployment_config


def reload_deployment_config() -> DeploymentConfig:
    """Reload the deployment configuration from file."""
    global _deployment_config
    _deployment_config = DeploymentConfig.load_from_file("config.yaml")
    return _deployment_config


def is_feature_enabled(
    feature_name: str,
    user_id: Optional[str] = None,
    user_groups: Optional[Set[str]] = None,
) -> bool:
    """Check if a feature is enabled for a specific user/context."""
    config = get_deployment_config()
    return config.is_feature_enabled(feature_name, user_id, user_groups)
