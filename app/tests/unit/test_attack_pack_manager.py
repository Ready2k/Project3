"""
Unit tests for attack pack manager.
"""

import json
import pytest
import tempfile
import shutil
from datetime import datetime
from pathlib import Path
from unittest.mock import patch, MagicMock

from app.security.attack_pack_manager import (
    AttackPackManager,
    AttackPackValidationResult,
    get_attack_pack_manager,
)
from app.security.deployment_config import AttackPackVersion


class TestAttackPackValidationResult:
    """Test AttackPackValidationResult functionality."""

    def test_validation_result_creation(self):
        """Test creating validation result."""
        result = AttackPackValidationResult(
            is_valid=True,
            pattern_count=42,
            issues=[],
            warnings=["Low pattern count"],
            metadata={"version": "v3"},
        )

        assert result.is_valid is True
        assert result.pattern_count == 42
        assert len(result.issues) == 0
        assert len(result.warnings) == 1
        assert result.metadata["version"] == "v3"


class TestAttackPackManager:
    """Test AttackPackManager functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = AttackPackManager(attack_packs_dir=self.temp_dir)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_manager_initialization(self):
        """Test manager initialization."""
        assert self.manager.attack_packs_dir == Path(self.temp_dir)
        assert self.manager.attack_packs_dir.exists()

    def test_calculate_file_checksum(self):
        """Test file checksum calculation."""
        # Create test file
        test_file = Path(self.temp_dir) / "test.txt"
        test_content = "Hello, World!"
        test_file.write_text(test_content)

        checksum = self.manager.calculate_file_checksum(test_file)

        # Verify checksum is not empty and consistent
        assert checksum != ""
        assert len(checksum) == 64  # SHA-256 hex length

        # Should be consistent
        checksum2 = self.manager.calculate_file_checksum(test_file)
        assert checksum == checksum2

    def test_calculate_file_checksum_nonexistent(self):
        """Test checksum calculation for non-existent file."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.txt"

        with patch("app.utils.logger.app_logger"):
            checksum = self.manager.calculate_file_checksum(nonexistent_file)
            assert checksum == ""

    def test_validate_attack_pack_nonexistent(self):
        """Test validation of non-existent attack pack."""
        nonexistent_file = Path(self.temp_dir) / "nonexistent.json"

        result = self.manager.validate_attack_pack(nonexistent_file)

        assert result.is_valid is False
        assert result.pattern_count == 0
        assert len(result.issues) > 0
        assert "not found" in result.issues[0]

    def test_validate_attack_pack_json_format(self):
        """Test validation of JSON format attack pack."""
        # Create valid JSON attack pack
        attack_pack_data = {
            "metadata": {
                "version": "v3",
                "description": "Test attack pack",
                "created_at": "2024-01-01T00:00:00Z",
            },
            "patterns": [
                {
                    "id": "PAT-001",
                    "name": "Test Pattern 1",
                    "description": "A test pattern for validation",
                    "category": "overt_prompt_injection",
                    "severity": "high",
                    "examples": ["test example 1", "test example 2"],
                    "indicators": ["test", "pattern"],
                },
                {
                    "id": "PAT-002",
                    "name": "Test Pattern 2",
                    "description": "Another test pattern",
                    "category": "covert_injection",
                    "severity": "medium",
                    "examples": ["test example 3"],
                    "indicators": ["covert", "injection"],
                },
            ],
        }

        pack_file = Path(self.temp_dir) / "test_pack.json"
        with open(pack_file, "w") as f:
            json.dump(attack_pack_data, f)

        result = self.manager.validate_attack_pack(pack_file)

        assert result.is_valid is True
        assert result.pattern_count == 2
        assert len(result.issues) == 0
        assert result.metadata["version"] == "v3"

    def test_validate_attack_pack_invalid_json(self):
        """Test validation of invalid JSON."""
        pack_file = Path(self.temp_dir) / "invalid.json"
        pack_file.write_text("{ invalid json }")

        result = self.manager.validate_attack_pack(pack_file)

        assert result.is_valid is False
        assert result.pattern_count == 0
        assert len(result.issues) > 0

    def test_validate_attack_pack_text_format(self):
        """Test validation of text format attack pack."""
        text_content = """
# Attack Pack v2

## Pattern 1: Test Overt Injection
**Category:** overt_prompt_injection
**Description:** Test pattern for overt injection attacks
**Example:** Ignore all previous instructions
**Indicators:** ignore, instructions, override

## Pattern 2: Test Covert Injection
**Category:** covert_injection
**Description:** Test pattern for covert injection
**Example:** Base64 encoded malicious payload
**Indicators:** base64, encoded, payload
"""

        pack_file = Path(self.temp_dir) / "text_pack.txt"
        pack_file.write_text(text_content)

        result = self.manager.validate_attack_pack(pack_file)

        assert result.is_valid is True
        assert result.pattern_count == 2
        assert len(result.warnings) > 0  # Low pattern count warning

    def test_validate_pattern_missing_fields(self):
        """Test pattern validation with missing required fields."""
        pattern_data = {
            "id": "PAT-001",
            # Missing name, description, category
            "examples": ["test"],
        }

        issues = self.manager._validate_pattern(pattern_data, 0)

        assert len(issues) >= 3  # Missing name, description, category
        assert any("name" in issue for issue in issues)
        assert any("description" in issue for issue in issues)
        assert any("category" in issue for issue in issues)

    def test_validate_pattern_invalid_id(self):
        """Test pattern validation with invalid ID format."""
        pattern_data = {
            "id": "INVALID-001",
            "name": "Test",
            "description": "Test pattern",
            "category": "overt_prompt_injection",
            "examples": ["test"],
        }

        issues = self.manager._validate_pattern(pattern_data, 0)

        assert len(issues) >= 1
        assert any("should start with 'PAT-'" in issue for issue in issues)

    def test_validate_pattern_invalid_category(self):
        """Test pattern validation with invalid category."""
        pattern_data = {
            "id": "PAT-001",
            "name": "Test",
            "description": "Test pattern",
            "category": "invalid_category",
            "examples": ["test"],
        }

        issues = self.manager._validate_pattern(pattern_data, 0)

        assert len(issues) >= 1
        assert any("Invalid category" in issue for issue in issues)

    def test_validate_pattern_invalid_severity(self):
        """Test pattern validation with invalid severity."""
        pattern_data = {
            "id": "PAT-001",
            "name": "Test",
            "description": "Test pattern",
            "category": "overt_prompt_injection",
            "severity": "invalid_severity",
            "examples": ["test"],
        }

        issues = self.manager._validate_pattern(pattern_data, 0)

        assert len(issues) >= 1
        assert any("Invalid severity" in issue for issue in issues)

    def test_validate_pattern_no_examples(self):
        """Test pattern validation with no examples."""
        pattern_data = {
            "id": "PAT-001",
            "name": "Test",
            "description": "Test pattern",
            "category": "overt_prompt_injection",
            "examples": [],
        }

        issues = self.manager._validate_pattern(pattern_data, 0)

        assert len(issues) >= 1
        assert any("At least one example is required" in issue for issue in issues)

    @patch("app.security.deployment_config.get_deployment_config")
    def test_install_attack_pack_success(self, mock_get_config):
        """Test successful attack pack installation."""
        # Mock deployment config
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {}
        mock_get_config.return_value = mock_config

        # Create valid attack pack
        attack_pack_data = {
            "patterns": [
                {
                    "id": "PAT-001",
                    "name": "Test Pattern",
                    "description": "Test pattern",
                    "category": "overt_prompt_injection",
                    "examples": ["test example"],
                }
            ]
        }

        source_file = Path(self.temp_dir) / "source_pack.json"
        with open(source_file, "w") as f:
            json.dump(attack_pack_data, f)

        success, message = self.manager.install_attack_pack(source_file, "v3")

        assert success is True
        assert "installed successfully" in message

        # Verify version directory was created
        version_dir = Path(self.temp_dir) / "v3"
        assert version_dir.exists()
        assert (version_dir / "attack_pack.json").exists()
        assert (version_dir / "metadata.json").exists()

    @patch("app.security.deployment_config.get_deployment_config")
    def test_install_attack_pack_invalid(self, mock_get_config):
        """Test installation of invalid attack pack."""
        mock_config = MagicMock()
        mock_get_config.return_value = mock_config

        # Create invalid attack pack (missing required fields)
        attack_pack_data = {
            "patterns": [
                {
                    "id": "PAT-001",
                    # Missing required fields
                }
            ]
        }

        source_file = Path(self.temp_dir) / "invalid_pack.json"
        with open(source_file, "w") as f:
            json.dump(attack_pack_data, f)

        success, message = self.manager.install_attack_pack(source_file, "v3")

        assert success is False
        assert "validation failed" in message

    @patch("app.security.deployment_config.get_deployment_config")
    def test_activate_attack_pack_success(self, mock_get_config):
        """Test successful attack pack activation."""
        # Mock deployment config with existing versions
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {
            "v2": AttackPackVersion(
                version="v2",
                file_path=str(Path(self.temp_dir) / "v2.json"),
                checksum="abc123",
                deployed_at=datetime.utcnow(),
                is_active=True,
            ),
            "v3": AttackPackVersion(
                version="v3",
                file_path=str(Path(self.temp_dir) / "v3.json"),
                checksum="def456",
                deployed_at=datetime.utcnow(),
                is_active=False,
            ),
        }
        mock_config.active_attack_pack_version = "v2"
        mock_get_config.return_value = mock_config

        # Create the files
        v3_file = Path(self.temp_dir) / "v3.json"
        v3_file.write_text('{"patterns": []}')

        # Mock checksum calculation to match
        with patch.object(
            self.manager, "calculate_file_checksum", return_value="def456"
        ):
            success, message = self.manager.activate_attack_pack("v3")

        assert success is True
        assert "activated successfully" in message
        assert mock_config.active_attack_pack_version == "v3"
        assert mock_config.attack_pack_versions["v2"].is_active is False
        assert mock_config.attack_pack_versions["v3"].is_active is True

    @patch("app.security.deployment_config.get_deployment_config")
    def test_activate_attack_pack_not_found(self, mock_get_config):
        """Test activation of non-existent attack pack."""
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {}
        mock_get_config.return_value = mock_config

        success, message = self.manager.activate_attack_pack("nonexistent")

        assert success is False
        assert "not found" in message

    @patch("app.security.deployment_config.get_deployment_config")
    def test_activate_attack_pack_checksum_mismatch(self, mock_get_config):
        """Test activation with checksum mismatch."""
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {
            "v3": AttackPackVersion(
                version="v3",
                file_path=str(Path(self.temp_dir) / "v3.json"),
                checksum="expected_checksum",
                deployed_at=datetime.utcnow(),
                is_active=False,
            )
        }
        mock_get_config.return_value = mock_config

        # Create file with different content
        v3_file = Path(self.temp_dir) / "v3.json"
        v3_file.write_text('{"patterns": []}')

        success, message = self.manager.activate_attack_pack("v3")

        assert success is False
        assert "checksum mismatch" in message

    @patch("app.security.deployment_config.get_deployment_config")
    def test_rollback_attack_pack_success(self, mock_get_config):
        """Test successful attack pack rollback."""
        # Mock deployment config with versions
        v2_time = datetime.utcnow()
        v3_time = datetime.utcnow()

        mock_config = MagicMock()
        mock_config.attack_pack_versions = {
            "v2": AttackPackVersion(
                version="v2",
                file_path=str(Path(self.temp_dir) / "v2.json"),
                checksum="abc123",
                deployed_at=v2_time,
                is_active=False,
            ),
            "v3": AttackPackVersion(
                version="v3",
                file_path=str(Path(self.temp_dir) / "v3.json"),
                checksum="def456",
                deployed_at=v3_time,
                is_active=True,
            ),
        }
        mock_config.active_attack_pack_version = "v3"
        mock_get_config.return_value = mock_config

        # Create files
        v2_file = Path(self.temp_dir) / "v2.json"
        v2_file.write_text('{"patterns": []}')

        # Mock activate_attack_pack to succeed
        with patch.object(
            self.manager, "activate_attack_pack", return_value=(True, "Success")
        ):
            success, message = self.manager.rollback_attack_pack()

        assert success is True
        assert "Rolled back to attack pack version v2" in message

    @patch("app.security.deployment_config.get_deployment_config")
    def test_rollback_attack_pack_no_previous(self, mock_get_config):
        """Test rollback with no previous version."""
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {
            "v3": AttackPackVersion(
                version="v3",
                file_path=str(Path(self.temp_dir) / "v3.json"),
                checksum="def456",
                deployed_at=datetime.utcnow(),
                is_active=True,
            )
        }
        mock_get_config.return_value = mock_config

        success, message = self.manager.rollback_attack_pack()

        assert success is False
        assert "No previous version available" in message

    @patch("app.security.deployment_config.get_deployment_config")
    def test_list_available_versions(self, mock_get_config):
        """Test listing available versions."""
        v2_time = datetime.utcnow()
        v3_time = datetime.utcnow()

        mock_config = MagicMock()
        mock_config.attack_pack_versions = {
            "v2": AttackPackVersion(
                version="v2",
                file_path="/path/to/v2.json",
                checksum="abc123",
                deployed_at=v2_time,
                is_active=False,
                validation_status="validated",
                pattern_count=40,
                metadata={"test": "data"},
            ),
            "v3": AttackPackVersion(
                version="v3",
                file_path="/path/to/v3.json",
                checksum="def456",
                deployed_at=v3_time,
                is_active=True,
                validation_status="validated",
                pattern_count=42,
                metadata={},
            ),
        }
        mock_get_config.return_value = mock_config

        versions = self.manager.list_available_versions()

        assert len(versions) == 2

        # Should be sorted by deployment date (newest first)
        assert versions[0]["version"] in ["v2", "v3"]
        assert versions[1]["version"] in ["v2", "v3"]

        # Check structure
        for version in versions:
            assert "version" in version
            assert "file_path" in version
            assert "checksum" in version
            assert "deployed_at" in version
            assert "is_active" in version
            assert "validation_status" in version
            assert "pattern_count" in version
            assert "metadata" in version

    @patch("app.security.deployment_config.get_deployment_config")
    def test_get_version_info(self, mock_get_config):
        """Test getting version info."""
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {
            "v3": AttackPackVersion(
                version="v3",
                file_path="/path/to/v3.json",
                checksum="def456",
                deployed_at=datetime.utcnow(),
                is_active=True,
                validation_status="validated",
                pattern_count=42,
                metadata={"test": "data"},
            )
        }
        mock_get_config.return_value = mock_config

        # Create metadata file
        version_dir = Path(self.temp_dir) / "v3"
        version_dir.mkdir()
        metadata_file = version_dir / "metadata.json"
        metadata = {"additional": "metadata"}
        with open(metadata_file, "w") as f:
            json.dump(metadata, f)

        info = self.manager.get_version_info("v3")

        assert info is not None
        assert info["version"] == "v3"
        assert info["pattern_count"] == 42
        assert info["metadata"]["additional"] == "metadata"

    @patch("app.security.deployment_config.get_deployment_config")
    def test_get_version_info_not_found(self, mock_get_config):
        """Test getting info for non-existent version."""
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {}
        mock_get_config.return_value = mock_config

        info = self.manager.get_version_info("nonexistent")

        assert info is None

    @patch("app.security.deployment_config.get_deployment_config")
    def test_cleanup_old_versions(self, mock_get_config):
        """Test cleanup of old versions."""
        # Create multiple versions
        versions = {}
        for i in range(7):  # More than keep_count=5
            version_name = f"v{i+1}"
            versions[version_name] = AttackPackVersion(
                version=version_name,
                file_path=f"/path/to/{version_name}.json",
                checksum=f"checksum{i}",
                deployed_at=datetime.utcnow(),
                is_active=(i == 6),  # Last one is active
            )

            # Create version directory
            version_dir = Path(self.temp_dir) / version_name
            version_dir.mkdir()
            (version_dir / "attack_pack.json").write_text("{}")

        mock_config = MagicMock()
        mock_config.attack_pack_versions = versions
        mock_get_config.return_value = mock_config

        removed_count, removed_versions = self.manager.cleanup_old_versions(
            keep_count=3
        )

        # Should remove older versions, keeping active + 3 most recent
        assert removed_count > 0
        assert len(removed_versions) > 0

        # Verify directories were removed
        for version in removed_versions:
            version_dir = Path(self.temp_dir) / version
            assert not version_dir.exists()

    def test_check_for_updates(self):
        """Test checking for updates."""
        has_updates, version, message = self.manager.check_for_updates("test_source")

        # Currently returns no updates
        assert has_updates is False
        assert version is None
        assert "No updates available" in message

    @patch("app.security.deployment_config.get_deployment_config")
    def test_export_version_success(self, mock_get_config):
        """Test successful version export."""
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {
            "v3": AttackPackVersion(
                version="v3",
                file_path=str(Path(self.temp_dir) / "v3.json"),
                checksum="def456",
                deployed_at=datetime.utcnow(),
            )
        }
        mock_get_config.return_value = mock_config

        # Create source file
        source_file = Path(self.temp_dir) / "v3.json"
        source_file.write_text('{"patterns": []}')

        # Export to different location
        export_path = Path(self.temp_dir) / "exported.json"

        success, message = self.manager.export_version("v3", export_path)

        assert success is True
        assert "Exported version v3 successfully" in message
        assert export_path.exists()
        assert export_path.read_text() == '{"patterns": []}'

    @patch("app.security.deployment_config.get_deployment_config")
    def test_export_version_not_found(self, mock_get_config):
        """Test export of non-existent version."""
        mock_config = MagicMock()
        mock_config.attack_pack_versions = {}
        mock_get_config.return_value = mock_config

        export_path = Path(self.temp_dir) / "exported.json"

        success, message = self.manager.export_version("nonexistent", export_path)

        assert success is False
        assert "not found" in message


class TestGlobalAttackPackManager:
    """Test global attack pack manager functions."""

    @patch("app.security.attack_pack_manager._attack_pack_manager", None)
    def test_get_attack_pack_manager(self):
        """Test getting global attack pack manager."""
        manager = get_attack_pack_manager()

        assert isinstance(manager, AttackPackManager)

        # Should return same instance on subsequent calls
        manager2 = get_attack_pack_manager()
        assert manager is manager2


if __name__ == "__main__":
    pytest.main([__file__])
