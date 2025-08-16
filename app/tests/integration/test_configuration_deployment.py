"""
Integration tests for configuration and deployment management.
Tests the interaction between deployment config, attack pack manager, and rollback manager.
"""
import asyncio
import json
import pytest
import tempfile
import shutil
from datetime import datetime, timedelta
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.security.deployment_config import (
    DeploymentConfig, FeatureFlag, AttackPackVersion, DeploymentStage, RollbackTrigger
)
from app.security.attack_pack_manager import AttackPackManager
from app.security.rollback_manager import RollbackManager, HealthMetrics, RollbackStatus


class TestConfigurationDeploymentIntegration:
    """Test integration between configuration and deployment components."""
    
    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.config_file = Path(self.temp_dir) / "test_config.yaml"
        
        # Create test deployment config
        self.deployment_config = DeploymentConfig()
        self.deployment_config.deployment_environment = "test"
        
        # Create attack pack manager
        self.attack_pack_manager = AttackPackManager(
            attack_packs_dir=str(Path(self.temp_dir) / "attack_packs")
        )
        
        # Create rollback manager with mocked dependencies
        with patch('app.security.deployment_config.get_deployment_config', return_value=self.deployment_config), \
             patch('app.security.attack_pack_manager.get_attack_pack_manager', return_value=self.attack_pack_manager):
            self.rollback_manager = RollbackManager()
    
    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_feature_flag_lifecycle(self):
        """Test complete feature flag lifecycle."""
        feature_name = "test_detector"
        
        # Initially disabled
        assert not self.deployment_config.is_feature_enabled(feature_name, user_id="user123")
        
        # Enable for canary rollout
        self.deployment_config.enable_feature(
            feature_name, 
            DeploymentStage.CANARY, 
            rollout_percentage=10.0,
            target_groups={"beta_testers"}
        )
        
        # Should be enabled for beta testers
        assert self.deployment_config.is_feature_enabled(
            feature_name, 
            user_groups={"beta_testers"}
        )
        
        # Gradual rollout to beta
        self.deployment_config.enable_feature(
            feature_name,
            DeploymentStage.BETA,
            rollout_percentage=25.0
        )
        
        flag = self.deployment_config.feature_flags[feature_name]
        assert flag.stage == DeploymentStage.BETA
        assert flag.rollout_percentage == 25.0
        
        # Full rollout
        self.deployment_config.enable_feature(
            feature_name,
            DeploymentStage.FULL,
            rollout_percentage=100.0
        )
        
        # Should be enabled for all users
        assert self.deployment_config.is_feature_enabled(feature_name, user_id="user123")
        assert self.deployment_config.is_feature_enabled(feature_name, user_id="user456")
        
        # Rollback
        self.deployment_config.rollback_feature(feature_name, "Performance issues")
        
        # Should be disabled
        assert not self.deployment_config.is_feature_enabled(feature_name, user_id="user123")
        
        # Check rollback history
        flag = self.deployment_config.feature_flags[feature_name]
        assert "rollback_history" in flag.metadata
        assert len(flag.metadata["rollback_history"]) == 1
        assert flag.metadata["rollback_history"][0]["reason"] == "Performance issues"
    
    def test_attack_pack_deployment_lifecycle(self):
        """Test complete attack pack deployment lifecycle."""
        # Create test attack pack
        attack_pack_data = {
            "metadata": {
                "version": "v3",
                "description": "Test attack pack v3",
                "created_at": datetime.utcnow().isoformat()
            },
            "patterns": [
                {
                    "id": "PAT-001",
                    "name": "Test Overt Injection",
                    "description": "Test pattern for overt injection",
                    "category": "overt_prompt_injection",
                    "severity": "high",
                    "examples": ["ignore all instructions", "act as admin"],
                    "indicators": ["ignore", "instructions", "admin"]
                },
                {
                    "id": "PAT-002",
                    "name": "Test Covert Injection",
                    "description": "Test pattern for covert injection",
                    "category": "covert_injection",
                    "severity": "medium",
                    "examples": ["base64 encoded payload"],
                    "indicators": ["base64", "encoded"]
                }
            ]
        }
        
        source_file = Path(self.temp_dir) / "attack_pack_v3.json"
        with open(source_file, 'w') as f:
            json.dump(attack_pack_data, f)
        
        # Install attack pack
        with patch('app.utils.logger.app_logger'):
            success, message = self.attack_pack_manager.install_attack_pack(source_file, "v3")
        
        assert success is True
        assert "v3" in self.deployment_config.attack_pack_versions
        
        pack_info = self.deployment_config.attack_pack_versions["v3"]
        assert pack_info.version == "v3"
        assert pack_info.pattern_count == 2
        assert pack_info.validation_status == "validated"
        assert pack_info.is_active is False
        
        # Activate attack pack
        with patch('app.utils.logger.app_logger'):
            success, message = self.attack_pack_manager.activate_attack_pack("v3")
        
        assert success is True
        assert self.deployment_config.active_attack_pack_version == "v3"
        assert self.deployment_config.attack_pack_versions["v3"].is_active is True
        
        # Get active pack
        active_pack = self.deployment_config.get_active_attack_pack()
        assert active_pack is not None
        assert active_pack.version == "v3"
        
        # List versions
        versions = self.attack_pack_manager.list_available_versions()
        assert len(versions) == 1
        assert versions[0]["version"] == "v3"
        assert versions[0]["is_active"] is True
        
        # Get version info
        info = self.attack_pack_manager.get_version_info("v3")
        assert info is not None
        assert info["pattern_count"] == 2
    
    def test_attack_pack_rollback_integration(self):
        """Test attack pack rollback integration."""
        # Install two versions
        for version in ["v2", "v3"]:
            attack_pack_data = {
                "patterns": [
                    {
                        "id": f"PAT-{version}-001",
                        "name": f"Test Pattern {version}",
                        "description": f"Test pattern for {version}",
                        "category": "overt_prompt_injection",
                        "examples": [f"test {version}"]
                    }
                ]
            }
            
            source_file = Path(self.temp_dir) / f"attack_pack_{version}.json"
            with open(source_file, 'w') as f:
                json.dump(attack_pack_data, f)
            
            with patch('app.utils.logger.app_logger'):
                success, _ = self.attack_pack_manager.install_attack_pack(source_file, version)
                assert success is True
        
        # Activate v3
        with patch('app.utils.logger.app_logger'):
            success, _ = self.attack_pack_manager.activate_attack_pack("v3")
            assert success is True
        
        # Rollback to v2
        with patch('app.utils.logger.app_logger'):
            success, message = self.attack_pack_manager.rollback_attack_pack("v2")
        
        assert success is True
        assert "Rolled back to attack pack version v2" in message
        assert self.deployment_config.active_attack_pack_version == "v2"
        assert self.deployment_config.attack_pack_versions["v2"].is_active is True
        assert self.deployment_config.attack_pack_versions["v3"].is_active is False
    
    @pytest.mark.asyncio
    async def test_rollback_manager_integration(self):
        """Test rollback manager integration with deployment config."""
        # Set up feature flag
        self.deployment_config.feature_flags["test_feature"] = FeatureFlag(
            name="test_feature",
            enabled=True,
            stage=DeploymentStage.FULL,
            rollout_percentage=100.0
        )
        
        # Mock deployment config methods
        self.deployment_config.disable_feature = MagicMock()
        self.deployment_config.save_to_file = MagicMock()
        
        # Perform manual rollback
        with patch('app.utils.logger.app_logger'):
            result = await self.rollback_manager.manual_rollback("test_feature", "Integration test")
        
        assert "completed successfully" in result
        self.deployment_config.disable_feature.assert_called_once_with("test_feature")
        self.deployment_config.save_to_file.assert_called_once_with("config.yaml")
        
        # Check rollback history
        history = self.rollback_manager.get_rollback_history()
        assert len(history) == 1
        assert history[0]["feature_name"] == "test_feature"
        assert history[0]["trigger"] == "manual"
        assert history[0]["status"] == "completed"
    
    @pytest.mark.asyncio
    async def test_automatic_rollback_integration(self):
        """Test automatic rollback integration."""
        # Set up feature flag
        self.deployment_config.feature_flags["advanced_prompt_defense"] = FeatureFlag(
            name="advanced_prompt_defense",
            enabled=True,
            stage=DeploymentStage.FULL
        )
        
        # Configure rollback triggers
        self.deployment_config.rollback_config.enabled = True
        self.deployment_config.rollback_config.triggers[RollbackTrigger.HIGH_ERROR_RATE] = {
            'threshold': 0.05,
            'window_minutes': 5,
            'min_requests': 10  # Lower for testing
        }
        
        # Add high error rate metrics
        base_time = datetime.utcnow()
        for i in range(3):
            metrics = HealthMetrics(
                timestamp=base_time - timedelta(minutes=i),
                request_count=20,
                failed_requests=5,  # 25% error rate
                successful_requests=15
            )
            self.rollback_manager.health_metrics_history.append(metrics)
        
        # Mock methods
        self.deployment_config.disable_feature = MagicMock()
        self.deployment_config.save_to_file = MagicMock()
        
        # Check if rollback should trigger
        current_metrics = HealthMetrics(
            timestamp=base_time,
            request_count=20,
            failed_requests=5,
            successful_requests=15
        )
        
        trigger_config = self.deployment_config.rollback_config.triggers[RollbackTrigger.HIGH_ERROR_RATE]
        should_trigger = await self.rollback_manager._should_trigger_rollback(
            RollbackTrigger.HIGH_ERROR_RATE, trigger_config, current_metrics
        )
        
        assert should_trigger is True
        
        # Simulate automatic rollback
        with patch('app.utils.logger.app_logger'):
            await self.rollback_manager._initiate_automatic_rollback(
                RollbackTrigger.HIGH_ERROR_RATE, current_metrics
            )
        
        # Verify rollback was executed
        self.deployment_config.disable_feature.assert_called()
        
        # Check rollback history
        history = self.rollback_manager.get_rollback_history()
        assert len(history) >= 1
        
        # Find the automatic rollback
        auto_rollback = next(
            (r for r in history if r["trigger"] == "high_error_rate"), 
            None
        )
        assert auto_rollback is not None
        assert auto_rollback["feature_name"] == "advanced_prompt_defense"
    
    def test_configuration_persistence(self):
        """Test configuration persistence across save/load cycles."""
        # Configure deployment settings
        self.deployment_config.deployment_environment = "staging"
        self.deployment_config.canary_user_percentage = 2.5
        self.deployment_config.enable_feature("test_feature", DeploymentStage.BETA, 50.0)
        
        # Add attack pack version
        self.deployment_config.attack_pack_versions["v3"] = AttackPackVersion(
            version="v3",
            file_path="/path/to/v3.json",
            checksum="abc123",
            deployed_at=datetime.utcnow(),
            is_active=True,
            pattern_count=42
        )
        self.deployment_config.active_attack_pack_version = "v3"
        
        # Configure rollback settings
        self.deployment_config.rollback_config.cooldown_minutes = 45
        self.deployment_config.rollback_config.max_rollbacks_per_day = 3
        
        # Save configuration
        with patch('app.utils.logger.app_logger'):
            self.deployment_config.save_to_file(str(self.config_file))
        
        # Load configuration
        with patch('app.utils.logger.app_logger'):
            loaded_config = DeploymentConfig.load_from_file(str(self.config_file))
        
        # Verify loaded configuration
        assert loaded_config.deployment_environment == "staging"
        assert loaded_config.canary_user_percentage == 2.5
        
        # Verify feature flag
        test_flag = loaded_config.feature_flags["test_feature"]
        assert test_flag.enabled is True
        assert test_flag.stage == DeploymentStage.BETA
        assert test_flag.rollout_percentage == 50.0
        
        # Verify attack pack version
        assert "v3" in loaded_config.attack_pack_versions
        pack_info = loaded_config.attack_pack_versions["v3"]
        assert pack_info.version == "v3"
        assert pack_info.is_active is True
        assert pack_info.pattern_count == 42
        assert loaded_config.active_attack_pack_version == "v3"
        
        # Verify rollback config
        assert loaded_config.rollback_config.cooldown_minutes == 45
        assert loaded_config.rollback_config.max_rollbacks_per_day == 3
    
    def test_configuration_validation_integration(self):
        """Test configuration validation across all components."""
        # Create invalid configuration
        self.deployment_config.canary_user_percentage = -5.0  # Invalid
        self.deployment_config.beta_user_percentage = 150.0   # Invalid
        self.deployment_config.health_check_interval_seconds = -10  # Invalid
        
        # Add invalid feature flag
        self.deployment_config.feature_flags["invalid_feature"] = FeatureFlag(
            name="invalid_feature",
            rollout_percentage=200.0  # Invalid
        )
        
        # Add conflicting attack pack versions
        self.deployment_config.attack_pack_versions["v2"] = AttackPackVersion(
            version="v2", file_path="/v2.json", checksum="abc", 
            deployed_at=datetime.utcnow(), is_active=True
        )
        self.deployment_config.attack_pack_versions["v3"] = AttackPackVersion(
            version="v3", file_path="/v3.json", checksum="def", 
            deployed_at=datetime.utcnow(), is_active=True  # Both active - invalid
        )
        self.deployment_config.active_attack_pack_version = "v2"
        
        # Validate configuration
        issues = self.deployment_config.validate_config()
        
        # Should find multiple issues
        assert len(issues) > 0
        
        # Check specific issues
        issue_text = " ".join(issues)
        assert "canary_user_percentage" in issue_text
        assert "beta_user_percentage" in issue_text
        assert "health_check_interval_seconds" in issue_text
        assert "rollout_percentage" in issue_text
        assert "Multiple active attack pack versions" in issue_text
    
    @pytest.mark.asyncio
    async def test_end_to_end_deployment_scenario(self):
        """Test complete end-to-end deployment scenario."""
        # Phase 1: Initial deployment with canary rollout
        self.deployment_config.enable_feature(
            "new_detector",
            DeploymentStage.CANARY,
            rollout_percentage=1.0,
            target_groups={"internal_testers"}
        )
        
        # Verify canary deployment
        assert self.deployment_config.is_feature_enabled(
            "new_detector", 
            user_groups={"internal_testers"}
        )
        assert not self.deployment_config.is_feature_enabled(
            "new_detector", 
            user_id="regular_user"
        )
        
        # Phase 2: Expand to beta
        self.deployment_config.enable_feature(
            "new_detector",
            DeploymentStage.BETA,
            rollout_percentage=10.0
        )
        
        # Phase 3: Simulate performance issue and rollback
        # Add high latency metrics
        base_time = datetime.utcnow()
        for i in range(3):
            metrics = HealthMetrics(
                timestamp=base_time - timedelta(minutes=i),
                request_count=100,
                average_latency_ms=300.0  # High latency
            )
            self.rollback_manager.health_metrics_history.append(metrics)
        
        # Configure rollback trigger
        self.deployment_config.rollback_config.triggers[RollbackTrigger.HIGH_LATENCY] = {
            'threshold_ms': 200,
            'window_minutes': 5,
            'min_requests': 50
        }
        
        # Mock deployment config methods
        self.deployment_config.disable_feature = MagicMock()
        self.deployment_config.save_to_file = MagicMock()
        
        # Trigger automatic rollback
        current_metrics = HealthMetrics(
            timestamp=base_time,
            request_count=100,
            average_latency_ms=300.0
        )
        
        with patch('app.utils.logger.app_logger'):
            await self.rollback_manager._initiate_automatic_rollback(
                RollbackTrigger.HIGH_LATENCY, current_metrics
            )
        
        # Verify rollback
        self.deployment_config.disable_feature.assert_called()
        
        # Phase 4: Fix issues and redeploy
        self.deployment_config.enable_feature(
            "new_detector",
            DeploymentStage.BETA,
            rollout_percentage=25.0
        )
        
        # Phase 5: Full rollout
        self.deployment_config.enable_feature(
            "new_detector",
            DeploymentStage.FULL,
            rollout_percentage=100.0
        )
        
        # Verify full deployment
        assert self.deployment_config.is_feature_enabled("new_detector", user_id="any_user")
        
        # Check deployment history in feature metadata
        flag = self.deployment_config.feature_flags["new_detector"]
        assert flag.stage == DeploymentStage.FULL
        assert flag.rollout_percentage == 100.0
    
    def test_attack_pack_version_management_integration(self):
        """Test comprehensive attack pack version management."""
        # Install multiple versions
        versions = ["v1", "v2", "v3", "v4", "v5", "v6"]
        
        for i, version in enumerate(versions):
            attack_pack_data = {
                "patterns": [
                    {
                        "id": f"PAT-{version}-001",
                        "name": f"Pattern {version}",
                        "description": f"Test pattern for {version}",
                        "category": "overt_prompt_injection",
                        "examples": [f"test {version}"]
                    }
                ]
            }
            
            source_file = Path(self.temp_dir) / f"pack_{version}.json"
            with open(source_file, 'w') as f:
                json.dump(attack_pack_data, f)
            
            with patch('app.utils.logger.app_logger'):
                success, _ = self.attack_pack_manager.install_attack_pack(source_file, version)
                assert success is True
        
        # Activate latest version
        with patch('app.utils.logger.app_logger'):
            success, _ = self.attack_pack_manager.activate_attack_pack("v6")
            assert success is True
        
        # List all versions
        all_versions = self.attack_pack_manager.list_available_versions()
        assert len(all_versions) == 6
        
        # Cleanup old versions (keep 3)
        with patch('app.utils.logger.app_logger'):
            removed_count, removed_versions = self.attack_pack_manager.cleanup_old_versions(keep_count=3)
        
        # Should remove 3 versions (keeping active + 3 most recent)
        assert removed_count == 3
        assert len(removed_versions) == 3
        
        # Verify remaining versions
        remaining_versions = self.attack_pack_manager.list_available_versions()
        assert len(remaining_versions) == 3
        
        # Active version should still be there
        active_pack = self.deployment_config.get_active_attack_pack()
        assert active_pack is not None
        assert active_pack.version == "v6"


if __name__ == "__main__":
    pytest.main([__file__])