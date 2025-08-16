"""
Unit tests for deployment configuration management.
"""
import pytest
import tempfile
import yaml
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.security.deployment_config import (
    DeploymentConfig, FeatureFlag, RollbackConfig, AttackPackVersion,
    DeploymentStage, RollbackTrigger, get_deployment_config, reload_deployment_config
)


class TestFeatureFlag:
    """Test FeatureFlag functionality."""
    
    def test_feature_flag_creation(self):
        """Test creating a feature flag."""
        flag = FeatureFlag(
            name="test_feature",
            enabled=True,
            description="Test feature",
            stage=DeploymentStage.BETA,
            rollout_percentage=50.0
        )
        
        assert flag.name == "test_feature"
        assert flag.enabled is True
        assert flag.stage == DeploymentStage.BETA
        assert flag.rollout_percentage == 50.0
    
    def test_feature_flag_defaults(self):
        """Test feature flag default values."""
        flag = FeatureFlag(name="test")
        
        assert flag.enabled is False
        assert flag.stage == DeploymentStage.DISABLED
        assert flag.rollout_percentage == 0.0
        assert len(flag.target_groups) == 0


class TestRollbackConfig:
    """Test RollbackConfig functionality."""
    
    def test_rollback_config_defaults(self):
        """Test rollback config default values."""
        config = RollbackConfig()
        
        assert config.enabled is True
        assert config.cooldown_minutes == 30
        assert config.max_rollbacks_per_day == 5
        assert RollbackTrigger.HIGH_ERROR_RATE in config.triggers
        assert RollbackTrigger.HIGH_LATENCY in config.triggers
        assert RollbackTrigger.HIGH_FALSE_POSITIVE_RATE in config.triggers
    
    def test_rollback_trigger_thresholds(self):
        """Test rollback trigger threshold configuration."""
        config = RollbackConfig()
        
        error_rate_config = config.triggers[RollbackTrigger.HIGH_ERROR_RATE]
        assert error_rate_config['threshold'] == 0.05
        assert error_rate_config['window_minutes'] == 5
        assert error_rate_config['min_requests'] == 100
        
        latency_config = config.triggers[RollbackTrigger.HIGH_LATENCY]
        assert latency_config['threshold_ms'] == 200
        assert latency_config['window_minutes'] == 5
        assert latency_config['min_requests'] == 100


class TestAttackPackVersion:
    """Test AttackPackVersion functionality."""
    
    def test_attack_pack_version_creation(self):
        """Test creating an attack pack version."""
        version = AttackPackVersion(
            version="v3",
            file_path="/path/to/pack.json",
            checksum="abc123",
            deployed_at=datetime.utcnow(),
            is_active=True,
            validation_status="validated",
            pattern_count=50
        )
        
        assert version.version == "v3"
        assert version.file_path == "/path/to/pack.json"
        assert version.checksum == "abc123"
        assert version.is_active is True
        assert version.validation_status == "validated"
        assert version.pattern_count == 50


class TestDeploymentConfig:
    """Test DeploymentConfig functionality."""
    
    def test_deployment_config_defaults(self):
        """Test deployment config default values."""
        config = DeploymentConfig()
        
        assert config.deployment_environment == "production"
        assert config.gradual_rollout_enabled is True
        assert config.canary_user_percentage == 1.0
        assert config.beta_user_percentage == 10.0
        assert config.staged_user_percentage == 50.0
        assert config.health_check_enabled is True
        assert config.monitoring_enabled is True
    
    def test_feature_flag_defaults(self):
        """Test default feature flags."""
        config = DeploymentConfig()
        
        # Check that all expected feature flags exist
        expected_flags = [
            "advanced_prompt_defense",
            "overt_injection_detector",
            "covert_injection_detector",
            "scope_validator",
            "data_egress_detector",
            "protocol_tampering_detector",
            "context_attack_detector",
            "multilingual_attack_detector",
            "business_logic_protector",
            "performance_optimization",
            "user_education",
            "security_monitoring"
        ]
        
        for flag_name in expected_flags:
            assert flag_name in config.feature_flags
            flag = config.feature_flags[flag_name]
            assert isinstance(flag, FeatureFlag)
            assert flag.name == flag_name
    
    def test_is_feature_enabled_disabled(self):
        """Test feature enabled check for disabled features."""
        config = DeploymentConfig()
        config.feature_flags["test_feature"] = FeatureFlag(
            name="test_feature",
            enabled=False,
            stage=DeploymentStage.DISABLED
        )
        
        assert not config.is_feature_enabled("test_feature")
        assert not config.is_feature_enabled("test_feature", user_id="user123")
    
    def test_is_feature_enabled_full_rollout(self):
        """Test feature enabled check for full rollout."""
        config = DeploymentConfig()
        config.feature_flags["test_feature"] = FeatureFlag(
            name="test_feature",
            enabled=True,
            stage=DeploymentStage.FULL,
            rollout_percentage=100.0
        )
        
        assert config.is_feature_enabled("test_feature")
        assert config.is_feature_enabled("test_feature", user_id="user123")
    
    def test_is_feature_enabled_percentage_rollout(self):
        """Test feature enabled check for percentage rollout."""
        config = DeploymentConfig()
        config.feature_flags["test_feature"] = FeatureFlag(
            name="test_feature",
            enabled=True,
            stage=DeploymentStage.BETA,
            rollout_percentage=50.0
        )
        
        # Test with consistent user ID (should be deterministic)
        result1 = config.is_feature_enabled("test_feature", user_id="user123")
        result2 = config.is_feature_enabled("test_feature", user_id="user123")
        assert result1 == result2  # Should be consistent
        
        # Test with different user IDs
        results = []
        for i in range(100):
            result = config.is_feature_enabled("test_feature", user_id=f"user{i}")
            results.append(result)
        
        # Should have roughly 50% enabled (allow some variance)
        enabled_count = sum(results)
        assert 30 <= enabled_count <= 70  # Allow 20% variance
    
    def test_is_feature_enabled_target_groups(self):
        """Test feature enabled check for target groups."""
        config = DeploymentConfig()
        config.feature_flags["test_feature"] = FeatureFlag(
            name="test_feature",
            enabled=True,
            stage=DeploymentStage.CANARY,
            rollout_percentage=10.0,
            target_groups={"beta_users", "internal"}
        )
        
        # User in target group should be enabled
        assert config.is_feature_enabled("test_feature", user_groups={"beta_users"})
        assert config.is_feature_enabled("test_feature", user_groups={"internal", "other"})
        
        # User not in target group should follow percentage rollout
        result = config.is_feature_enabled("test_feature", user_id="user123", user_groups={"regular"})
        # This depends on the hash, but should be consistent
        assert isinstance(result, bool)
    
    def test_enable_feature(self):
        """Test enabling a feature."""
        config = DeploymentConfig()
        config.feature_flags["test_feature"] = FeatureFlag(name="test_feature", enabled=False)
        
        config.enable_feature("test_feature", DeploymentStage.BETA, 75.0, {"testers"})
        
        flag = config.feature_flags["test_feature"]
        assert flag.enabled is True
        assert flag.stage == DeploymentStage.BETA
        assert flag.rollout_percentage == 75.0
        assert "testers" in flag.target_groups
    
    def test_disable_feature(self):
        """Test disabling a feature."""
        config = DeploymentConfig()
        config.feature_flags["test_feature"] = FeatureFlag(
            name="test_feature",
            enabled=True,
            stage=DeploymentStage.FULL
        )
        
        config.disable_feature("test_feature")
        
        flag = config.feature_flags["test_feature"]
        assert flag.enabled is False
        assert flag.stage == DeploymentStage.DISABLED
    
    def test_rollback_feature(self):
        """Test rolling back a feature."""
        config = DeploymentConfig()
        config.feature_flags["test_feature"] = FeatureFlag(
            name="test_feature",
            enabled=True,
            stage=DeploymentStage.FULL,
            rollout_percentage=100.0
        )
        
        config.rollback_feature("test_feature", "test rollback")
        
        flag = config.feature_flags["test_feature"]
        assert flag.enabled is False
        assert flag.stage == DeploymentStage.DISABLED
        assert "rollback_history" in flag.metadata
        assert len(flag.metadata["rollback_history"]) == 1
        
        rollback_entry = flag.metadata["rollback_history"][0]
        assert rollback_entry["reason"] == "test rollback"
        assert rollback_entry["previous_stage"] == DeploymentStage.FULL.value
        assert rollback_entry["previous_rollout_percentage"] == 100.0
    
    def test_get_active_attack_pack(self):
        """Test getting active attack pack."""
        config = DeploymentConfig()
        config.active_attack_pack_version = "v2"
        config.attack_pack_versions["v2"] = AttackPackVersion(
            version="v2",
            file_path="/path/to/v2.json",
            checksum="def456",
            deployed_at=datetime.utcnow(),
            is_active=True
        )
        
        active_pack = config.get_active_attack_pack()
        assert active_pack is not None
        assert active_pack.version == "v2"
        assert active_pack.is_active is True
    
    def test_deploy_attack_pack(self):
        """Test deploying attack pack."""
        config = DeploymentConfig()
        
        with patch('pathlib.Path.exists', return_value=True):
            success = config.deploy_attack_pack("v3", "/path/to/v3.json", "ghi789")
            
            assert success is True
            assert "v3" in config.attack_pack_versions
            
            pack = config.attack_pack_versions["v3"]
            assert pack.version == "v3"
            assert pack.file_path == "/path/to/v3.json"
            assert pack.checksum == "ghi789"
            assert pack.is_active is False
    
    def test_activate_attack_pack(self):
        """Test activating attack pack."""
        config = DeploymentConfig()
        
        # Add two versions
        config.attack_pack_versions["v2"] = AttackPackVersion(
            version="v2", file_path="/v2.json", checksum="abc", 
            deployed_at=datetime.utcnow(), is_active=True
        )
        config.attack_pack_versions["v3"] = AttackPackVersion(
            version="v3", file_path="/v3.json", checksum="def", 
            deployed_at=datetime.utcnow(), is_active=False
        )
        config.active_attack_pack_version = "v2"
        
        success = config.activate_attack_pack("v3")
        
        assert success is True
        assert config.active_attack_pack_version == "v3"
        assert config.attack_pack_versions["v2"].is_active is False
        assert config.attack_pack_versions["v3"].is_active is True
    
    def test_validate_config_valid(self):
        """Test config validation with valid config."""
        config = DeploymentConfig()
        issues = config.validate_config()
        assert len(issues) == 0
    
    def test_validate_config_invalid_percentages(self):
        """Test config validation with invalid percentages."""
        config = DeploymentConfig()
        config.canary_user_percentage = -5.0
        config.beta_user_percentage = 150.0
        
        issues = config.validate_config()
        assert len(issues) >= 2
        assert any("canary_user_percentage" in issue for issue in issues)
        assert any("beta_user_percentage" in issue for issue in issues)
    
    def test_validate_config_invalid_thresholds(self):
        """Test config validation with invalid thresholds."""
        config = DeploymentConfig()
        config.feature_flags["test"] = FeatureFlag(
            name="test",
            rollout_percentage=150.0  # Invalid
        )
        
        issues = config.validate_config()
        assert len(issues) >= 1
        assert any("rollout_percentage" in issue for issue in issues)
    
    def test_validate_config_invalid_timing(self):
        """Test config validation with invalid timing values."""
        config = DeploymentConfig()
        config.health_check_interval_seconds = -10
        config.metrics_retention_days = 0
        
        issues = config.validate_config()
        assert len(issues) >= 2
        assert any("health_check_interval_seconds" in issue for issue in issues)
        assert any("metrics_retention_days" in issue for issue in issues)


class TestDeploymentConfigFileOperations:
    """Test file operations for deployment config."""
    
    def test_load_from_nonexistent_file(self):
        """Test loading from non-existent file."""
        with patch('app.utils.logger.app_logger'):
            config = DeploymentConfig.load_from_file("nonexistent.yaml")
            assert isinstance(config, DeploymentConfig)
            # Should use defaults
            assert config.deployment_environment == "production"
    
    def test_save_and_load_config(self):
        """Test saving and loading config."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_file = f.name
        
        try:
            # Create and save config
            original_config = DeploymentConfig()
            original_config.deployment_environment = "staging"
            original_config.canary_user_percentage = 2.5
            original_config.enable_feature("test_feature", DeploymentStage.BETA, 25.0)
            
            with patch('app.utils.logger.app_logger'):
                original_config.save_to_file(config_file)
            
            # Load config
            with patch('app.utils.logger.app_logger'):
                loaded_config = DeploymentConfig.load_from_file(config_file)
            
            # Verify loaded config
            assert loaded_config.deployment_environment == "staging"
            assert loaded_config.canary_user_percentage == 2.5
            assert loaded_config.feature_flags["test_feature"].enabled is True
            assert loaded_config.feature_flags["test_feature"].stage == DeploymentStage.BETA
            assert loaded_config.feature_flags["test_feature"].rollout_percentage == 25.0
            
        finally:
            Path(config_file).unlink(missing_ok=True)
    
    def test_save_preserves_existing_config(self):
        """Test that saving preserves other config sections."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            config_file = f.name
        
        try:
            # Create initial config with other sections
            initial_config = {
                'other_section': {
                    'setting1': 'value1',
                    'setting2': 42
                },
                'deployment': {
                    'deployment_environment': 'development'
                }
            }
            
            with open(config_file, 'w') as f:
                yaml.dump(initial_config, f)
            
            # Save deployment config
            config = DeploymentConfig()
            config.deployment_environment = "staging"
            
            with patch('app.utils.logger.app_logger'):
                config.save_to_file(config_file)
            
            # Verify other sections are preserved
            with open(config_file, 'r') as f:
                saved_config = yaml.safe_load(f)
            
            assert 'other_section' in saved_config
            assert saved_config['other_section']['setting1'] == 'value1'
            assert saved_config['other_section']['setting2'] == 42
            assert saved_config['deployment']['deployment_environment'] == 'staging'
            
        finally:
            Path(config_file).unlink(missing_ok=True)


class TestGlobalConfigFunctions:
    """Test global configuration functions."""
    
    @patch('app.security.deployment_config._deployment_config', None)
    def test_get_deployment_config(self):
        """Test getting global deployment config."""
        with patch('app.security.deployment_config.DeploymentConfig.load_from_file') as mock_load:
            mock_config = MagicMock()
            mock_load.return_value = mock_config
            
            config = get_deployment_config()
            
            assert config == mock_config
            mock_load.assert_called_once_with("config.yaml")
    
    @patch('app.security.deployment_config._deployment_config', MagicMock())
    def test_reload_deployment_config(self):
        """Test reloading deployment config."""
        with patch('app.security.deployment_config.DeploymentConfig.load_from_file') as mock_load:
            mock_config = MagicMock()
            mock_load.return_value = mock_config
            
            config = reload_deployment_config()
            
            assert config == mock_config
            mock_load.assert_called_once_with("config.yaml")


if __name__ == "__main__":
    pytest.main([__file__])