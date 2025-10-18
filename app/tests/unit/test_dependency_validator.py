"""
Unit tests for the dependency validation system.

Tests cover:
- Validation of required dependencies
- Handling of missing optional dependencies
- Version constraint checking
- Installation instruction generation
"""

import pytest
from unittest.mock import Mock, patch

from app.core.dependencies import (
    DependencyValidator,
    DependencyInfo,
    DependencyType,
    ValidationResult,
    get_dependency_validator,
    validate_startup_dependencies,
    check_dependency,
)


class TestDependencyInfo:
    """Test DependencyInfo dataclass functionality."""

    def test_dependency_info_creation(self):
        """Test basic DependencyInfo creation."""
        dep = DependencyInfo(
            name="test_package",
            version_constraint=">=1.0.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="Testing purposes",
            alternatives=["alt1", "alt2"],
        )

        assert dep.name == "test_package"
        assert dep.version_constraint == ">=1.0.0"
        assert dep.dependency_type == DependencyType.REQUIRED
        assert dep.purpose == "Testing purposes"
        assert dep.alternatives == ["alt1", "alt2"]
        assert dep.import_name == "test_package"  # Default value
        assert dep.installation_name == "test_package"  # Default value

    def test_dependency_info_with_custom_names(self):
        """Test DependencyInfo with custom import and installation names."""
        dep = DependencyInfo(
            name="yaml_package",
            version_constraint=">=6.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="YAML parsing",
            alternatives=["ruamel.yaml"],
            import_name="yaml",
            installation_name="pyyaml",
        )

        assert dep.import_name == "yaml"
        assert dep.installation_name == "pyyaml"


class TestValidationResult:
    """Test ValidationResult dataclass functionality."""

    def test_validation_result_creation(self):
        """Test basic ValidationResult creation."""
        result = ValidationResult(
            is_valid=False,
            missing_required=["req1", "req2"],
            missing_optional=["opt1"],
            version_conflicts=["conflict1"],
            warnings=["warning1"],
        )

        assert not result.is_valid
        assert result.missing_required == ["req1", "req2"]
        assert result.missing_optional == ["opt1"]
        assert result.version_conflicts == ["conflict1"]
        assert result.warnings == ["warning1"]

    def test_has_errors(self):
        """Test has_errors method."""
        # No errors
        result = ValidationResult(
            is_valid=True,
            missing_required=[],
            missing_optional=["opt1"],
            version_conflicts=[],
            warnings=["warning1"],
        )
        assert not result.has_errors()

        # Has missing required
        result.missing_required = ["req1"]
        assert result.has_errors()

        # Has version conflicts
        result.missing_required = []
        result.version_conflicts = ["conflict1"]
        assert result.has_errors()

    def test_has_warnings(self):
        """Test has_warnings method."""
        # No warnings
        result = ValidationResult(
            is_valid=True,
            missing_required=[],
            missing_optional=[],
            version_conflicts=[],
            warnings=[],
        )
        assert not result.has_warnings()

        # Has warnings
        result.warnings = ["warning1"]
        assert result.has_warnings()

        # Has missing optional
        result.warnings = []
        result.missing_optional = ["opt1"]
        assert result.has_warnings()


class TestDependencyValidator:
    """Test DependencyValidator class functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DependencyValidator()
        # Clear any existing dependencies for clean tests
        self.validator.dependencies.clear()

    def test_add_dependency(self):
        """Test adding a new dependency."""
        dep = DependencyInfo(
            name="test_dep",
            version_constraint=">=1.0.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="Testing",
            alternatives=[],
        )

        self.validator.add_dependency(dep)
        assert "test_dep" in self.validator.dependencies
        assert self.validator.dependencies["test_dep"] == dep

    def test_remove_dependency(self):
        """Test removing a dependency."""
        dep = DependencyInfo(
            name="test_dep",
            version_constraint=">=1.0.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="Testing",
            alternatives=[],
        )

        self.validator.add_dependency(dep)
        assert "test_dep" in self.validator.dependencies

        # Remove existing dependency
        result = self.validator.remove_dependency("test_dep")
        assert result is True
        assert "test_dep" not in self.validator.dependencies

        # Try to remove non-existent dependency
        result = self.validator.remove_dependency("non_existent")
        assert result is False

    @patch("importlib.import_module")
    def test_validate_dependency_success(self, mock_import):
        """Test successful validation of a single dependency."""
        # Setup mock module with version
        mock_module = Mock()
        mock_module.__version__ = "1.5.0"
        mock_import.return_value = mock_module

        dep = DependencyInfo(
            name="test_dep",
            version_constraint=">=1.0.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="Testing",
            alternatives=[],
            import_name="test_dep",
        )

        self.validator.add_dependency(dep)

        is_valid, error = self.validator.validate_dependency("test_dep")
        assert is_valid is True
        assert error is None
        mock_import.assert_called_once_with("test_dep")

    @patch("importlib.import_module")
    def test_validate_dependency_import_error(self, mock_import):
        """Test validation with import error."""
        mock_import.side_effect = ImportError("Module not found")

        dep = DependencyInfo(
            name="missing_dep",
            version_constraint=">=1.0.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="Testing",
            alternatives=[],
            import_name="missing_dep",
        )

        self.validator.add_dependency(dep)

        is_valid, error = self.validator.validate_dependency("missing_dep")
        assert is_valid is False
        assert "Import failed: Module not found" in error

    @patch("importlib.import_module")
    def test_validate_dependency_version_conflict(self, mock_import):
        """Test validation with version conflict."""
        # Setup mock module with incompatible version
        mock_module = Mock()
        mock_module.__version__ = "0.5.0"
        mock_import.return_value = mock_module

        dep = DependencyInfo(
            name="old_dep",
            version_constraint=">=1.0.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="Testing",
            alternatives=[],
            import_name="old_dep",
        )

        self.validator.add_dependency(dep)

        is_valid, error = self.validator.validate_dependency("old_dep")
        assert is_valid is False
        assert "Version 0.5.0 does not satisfy constraint >=1.0.0" in error

    def test_validate_dependency_not_registered(self):
        """Test validation of unregistered dependency."""
        is_valid, error = self.validator.validate_dependency("unregistered")
        assert is_valid is False
        assert "Dependency 'unregistered' not registered" in error

    @patch("importlib.import_module")
    def test_validate_all_required_dependencies(self, mock_import):
        """Test validation of all required dependencies."""
        # Setup mock modules
        mock_modules = {
            "req1": Mock(__version__="1.0.0"),
            "req2": Mock(__version__="2.0.0"),
        }

        def import_side_effect(name):
            if name in mock_modules:
                return mock_modules[name]
            raise ImportError(f"No module named '{name}'")

        mock_import.side_effect = import_side_effect

        # Add required dependencies
        self.validator.add_dependency(
            DependencyInfo(
                name="req1",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Required 1",
                alternatives=[],
                import_name="req1",
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="req2",
                version_constraint=">=2.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Required 2",
                alternatives=[],
                import_name="req2",
            )
        )

        result = self.validator.validate_all()
        assert result.is_valid is True
        assert len(result.missing_required) == 0
        assert len(result.version_conflicts) == 0

    @patch("importlib.import_module")
    def test_validate_all_missing_required(self, mock_import):
        """Test validation with missing required dependencies."""
        mock_import.side_effect = ImportError("Module not found")

        # Add required dependency that will fail to import
        self.validator.add_dependency(
            DependencyInfo(
                name="missing_req",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Missing required",
                alternatives=[],
                import_name="missing_req",
            )
        )

        result = self.validator.validate_all()
        assert result.is_valid is False
        assert "missing_req" in result.missing_required
        assert len(result.missing_required) == 1

    @patch("importlib.import_module")
    def test_validate_all_missing_optional(self, mock_import):
        """Test validation with missing optional dependencies."""
        mock_import.side_effect = ImportError("Module not found")

        # Add optional dependency that will fail to import
        self.validator.add_dependency(
            DependencyInfo(
                name="missing_opt",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Missing optional feature",
                alternatives=["alternative1"],
                import_name="missing_opt",
            )
        )

        result = self.validator.validate_all()
        assert result.is_valid is True  # Still valid because it's optional
        assert "missing_opt" in result.missing_optional
        assert len(result.missing_optional) == 1
        assert len(result.warnings) > 0
        assert "Optional dependency 'missing_opt' not available" in result.warnings[0]

    @patch("importlib.import_module")
    def test_validate_all_version_conflicts(self, mock_import):
        """Test validation with version conflicts."""
        # Setup mock module with incompatible version
        mock_module = Mock()
        mock_module.__version__ = "0.5.0"
        mock_import.return_value = mock_module

        self.validator.add_dependency(
            DependencyInfo(
                name="old_version",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Testing version conflict",
                alternatives=[],
                import_name="old_version",
            )
        )

        result = self.validator.validate_all()
        assert result.is_valid is False
        assert len(result.version_conflicts) == 1
        assert (
            "old_version: installed version 0.5.0 does not satisfy constraint >=1.0.0"
            in result.version_conflicts[0]
        )

    @patch("importlib.import_module")
    def test_validate_all_include_dev_dependencies(self, mock_import):
        """Test validation including development dependencies."""
        mock_import.side_effect = ImportError("Module not found")

        # Add development dependency
        self.validator.add_dependency(
            DependencyInfo(
                name="dev_dep",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.DEVELOPMENT,
                purpose="Development tool",
                alternatives=[],
                import_name="dev_dep",
            )
        )

        # Validate without dev dependencies
        result = self.validator.validate_all(include_dev=False)
        assert result.is_valid is True
        assert len(result.missing_required) == 0

        # Validate with dev dependencies
        # Note: Development dependencies are treated as optional in the current implementation
        result = self.validator.validate_all(include_dev=True)
        assert (
            result.is_valid is True
        )  # Still valid because dev deps are treated as optional
        assert (
            "dev_dep" in result.missing_optional
        )  # Dev deps go to missing_optional, not missing_required
        assert len(result.warnings) > 0


class TestVersionComparison:
    """Test version comparison functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DependencyValidator()

    def test_compare_versions_equal(self):
        """Test comparing equal versions."""
        assert self.validator._compare_versions("1.0.0", "1.0.0") == 0
        assert self.validator._compare_versions("2.1.3", "2.1.3") == 0

    def test_compare_versions_greater(self):
        """Test comparing greater versions."""
        assert self.validator._compare_versions("1.1.0", "1.0.0") == 1
        assert self.validator._compare_versions("2.0.0", "1.9.9") == 1
        assert self.validator._compare_versions("1.0.1", "1.0.0") == 1

    def test_compare_versions_lesser(self):
        """Test comparing lesser versions."""
        assert self.validator._compare_versions("1.0.0", "1.1.0") == -1
        assert self.validator._compare_versions("1.9.9", "2.0.0") == -1
        assert self.validator._compare_versions("1.0.0", "1.0.1") == -1

    def test_compare_versions_different_lengths(self):
        """Test comparing versions with different lengths."""
        assert self.validator._compare_versions("1.0", "1.0.0") == 0
        assert self.validator._compare_versions("1.1", "1.0.0") == 1
        assert self.validator._compare_versions("1.0", "1.0.1") == -1

    def test_compare_versions_with_suffixes(self):
        """Test comparing versions with alpha/beta suffixes."""
        assert (
            self.validator._compare_versions("1.0.0a1", "1.0.0") == 0
        )  # Suffix ignored
        assert self.validator._compare_versions("1.1.0b2", "1.0.0") == 1
        assert self.validator._compare_versions("1.0.0rc1", "1.1.0") == -1

    def test_check_version_constraint_greater_equal(self):
        """Test >=constraint checking."""
        assert self.validator._check_version_constraint("1.0.0", ">=1.0.0") is True
        assert self.validator._check_version_constraint("1.1.0", ">=1.0.0") is True
        assert self.validator._check_version_constraint("0.9.0", ">=1.0.0") is False

    def test_check_version_constraint_less_equal(self):
        """Test <= constraint checking."""
        assert self.validator._check_version_constraint("1.0.0", "<=1.0.0") is True
        assert self.validator._check_version_constraint("0.9.0", "<=1.0.0") is True
        assert self.validator._check_version_constraint("1.1.0", "<=1.0.0") is False

    def test_check_version_constraint_equal(self):
        """Test == constraint checking."""
        assert self.validator._check_version_constraint("1.0.0", "==1.0.0") is True
        assert self.validator._check_version_constraint("1.1.0", "==1.0.0") is False
        assert self.validator._check_version_constraint("0.9.0", "==1.0.0") is False

    def test_check_version_constraint_not_equal(self):
        """Test != constraint checking."""
        assert self.validator._check_version_constraint("1.0.0", "!=1.0.0") is False
        assert self.validator._check_version_constraint("1.1.0", "!=1.0.0") is True
        assert self.validator._check_version_constraint("0.9.0", "!=1.0.0") is True

    def test_check_version_constraint_greater(self):
        """Test > constraint checking."""
        assert self.validator._check_version_constraint("1.1.0", ">1.0.0") is True
        assert self.validator._check_version_constraint("1.0.0", ">1.0.0") is False
        assert self.validator._check_version_constraint("0.9.0", ">1.0.0") is False

    def test_check_version_constraint_less(self):
        """Test < constraint checking."""
        assert self.validator._check_version_constraint("0.9.0", "<1.0.0") is True
        assert self.validator._check_version_constraint("1.0.0", "<1.0.0") is False
        assert self.validator._check_version_constraint("1.1.0", "<1.0.0") is False

    def test_check_version_constraint_no_operator(self):
        """Test constraint without operator (exact match)."""
        assert self.validator._check_version_constraint("1.0.0", "1.0.0") is True
        assert self.validator._check_version_constraint("1.1.0", "1.0.0") is False


class TestInstallationInstructions:
    """Test installation instruction generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DependencyValidator()
        self.validator.dependencies.clear()

    def test_get_installation_instructions_empty(self):
        """Test installation instructions for empty list."""
        instructions = self.validator.get_installation_instructions([])
        assert instructions == ""

    def test_get_installation_instructions_basic(self):
        """Test basic installation instructions."""
        # Add dependencies
        self.validator.add_dependency(
            DependencyInfo(
                name="requests",
                version_constraint=">=2.28.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="HTTP client",
                alternatives=["httpx"],
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="pyyaml",
                version_constraint=">=6.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="YAML parsing",
                alternatives=["ruamel.yaml"],
                import_name="yaml",
                installation_name="pyyaml",
            )
        )

        instructions = self.validator.get_installation_instructions(
            ["requests", "pyyaml"]
        )

        assert "Missing dependencies detected" in instructions
        assert "pip install" in instructions
        assert "requests>=2.28.0" in instructions
        assert "pyyaml>=6.0" in instructions
        assert "Alternative to requests: httpx" in instructions
        assert "Alternative to pyyaml: ruamel.yaml" in instructions

    def test_get_installation_instructions_special_packages(self):
        """Test installation instructions for packages with special requirements."""
        # Add graphviz dependency
        self.validator.add_dependency(
            DependencyInfo(
                name="graphviz",
                version_constraint=">=0.20.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Graph visualization",
                alternatives=["mermaid"],
            )
        )

        # Add redis dependency
        self.validator.add_dependency(
            DependencyInfo(
                name="redis",
                version_constraint=">=4.0.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Redis client",
                alternatives=["memory_cache"],
            )
        )

        instructions = self.validator.get_installation_instructions(
            ["graphviz", "redis"]
        )

        assert "graphviz also requires system-level installation" in instructions
        assert "sudo apt-get install graphviz" in instructions
        assert "brew install graphviz" in instructions
        assert "redis package requires a Redis server" in instructions
        assert "docker run -d -p 6379:6379 redis:alpine" in instructions

    def test_get_installation_instructions_version_constraints(self):
        """Test installation instructions with various version constraints."""
        # Add dependencies with different constraint types
        self.validator.add_dependency(
            DependencyInfo(
                name="exact_version",
                version_constraint="==1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Exact version test",
                alternatives=[],
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="min_version",
                version_constraint=">=2.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Minimum version test",
                alternatives=[],
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="complex_constraint",
                version_constraint="<3.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Complex constraint test",
                alternatives=[],
            )
        )

        instructions = self.validator.get_installation_instructions(
            ["exact_version", "min_version", "complex_constraint"]
        )

        assert "exact_version==1.0.0" in instructions
        assert "min_version>=2.0.0" in instructions
        # Complex constraints should be converted to >= format
        assert "complex_constraint>=3.0.0" in instructions


class TestDependencyReport:
    """Test dependency report generation."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DependencyValidator()
        self.validator.dependencies.clear()

    @patch("importlib.import_module")
    def test_get_dependency_report(self, mock_import):
        """Test comprehensive dependency report generation."""
        # Setup mock modules - need to handle both the report generation and validate_dependency calls
        mock_available = Mock(__version__="1.0.0")

        def import_side_effect(name):
            if name == "available":
                return mock_available
            else:
                raise ImportError(f"No module named '{name}'")

        mock_import.side_effect = import_side_effect

        # Add various types of dependencies
        self.validator.add_dependency(
            DependencyInfo(
                name="available",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Available dependency",
                alternatives=["alt1"],
                import_name="available",
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="missing",
                version_constraint=">=2.0.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Missing dependency",
                alternatives=["alt2"],
                import_name="missing",
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="dev_tool",
                version_constraint=">=3.0.0",
                dependency_type=DependencyType.DEVELOPMENT,
                purpose="Development tool",
                alternatives=[],
                import_name="dev_tool",
            )
        )

        report = self.validator.get_dependency_report()

        assert "Dependency Report" in report
        assert "Required Dependencies:" in report
        assert "Optional Dependencies:" in report
        assert "Development Dependencies:" in report
        assert "✓ available (v1.0.0)" in report
        assert "✗ missing (not installed)" in report
        assert "✗ dev_tool (not installed)" in report
        assert "Purpose: Available dependency" in report
        assert "Required: >=1.0.0" in report
        assert "Alternatives: alt1" in report


class TestUtilityFunctions:
    """Test utility functions."""

    @patch("app.core.dependencies._dependency_validator")
    def test_get_dependency_validator(self, mock_validator):
        """Test get_dependency_validator function."""
        result = get_dependency_validator()
        assert result == mock_validator

    @patch("app.core.dependencies._dependency_validator")
    def test_validate_startup_dependencies(self, mock_validator):
        """Test validate_startup_dependencies function."""
        mock_result = ValidationResult(
            is_valid=True,
            missing_required=[],
            missing_optional=[],
            version_conflicts=[],
            warnings=[],
        )
        mock_validator.validate_all.return_value = mock_result

        result = validate_startup_dependencies(include_dev=True)
        assert result == mock_result
        mock_validator.validate_all.assert_called_once_with(include_dev=True)

    @patch("app.core.dependencies._dependency_validator")
    def test_check_dependency(self, mock_validator):
        """Test check_dependency function."""
        mock_validator.validate_dependency.return_value = (True, None)

        result = check_dependency("test_dep")
        assert result is True
        mock_validator.validate_dependency.assert_called_once_with("test_dep")

        # Test failure case
        mock_validator.validate_dependency.return_value = (False, "Error message")
        result = check_dependency("test_dep")
        assert result is False


class TestModuleVersionExtraction:
    """Test module version extraction functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DependencyValidator()

    def test_get_module_version_with_version_attribute(self):
        """Test version extraction from __version__ attribute."""
        mock_module = Mock()
        mock_module.__version__ = "1.2.3"

        version = self.validator._get_module_version(mock_module, "test_module")
        assert version == "1.2.3"

    def test_get_module_version_with_version_property(self):
        """Test version extraction from version attribute."""
        mock_module = Mock()
        del mock_module.__version__  # Remove __version__
        mock_module.version = "2.3.4"

        version = self.validator._get_module_version(mock_module, "test_module")
        assert version == "2.3.4"

    def test_get_module_version_with_version_constant(self):
        """Test version extraction from VERSION constant."""
        mock_module = Mock()
        del mock_module.__version__  # Remove __version__
        del mock_module.version  # Remove version
        mock_module.VERSION = "3.4.5"

        version = self.validator._get_module_version(mock_module, "test_module")
        assert version == "3.4.5"

    def test_get_module_version_no_version(self):
        """Test version extraction when no version is available."""
        mock_module = Mock()
        del mock_module.__version__
        del mock_module.version
        del mock_module.VERSION

        version = self.validator._get_module_version(mock_module, "test_module")
        assert version is None

    def test_get_module_version_caching(self):
        """Test that version results are cached."""
        mock_module = Mock()
        mock_module.__version__ = "1.0.0"

        # First call
        version1 = self.validator._get_module_version(mock_module, "test_module")
        assert version1 == "1.0.0"

        # Second call should use cache
        mock_module.__version__ = "2.0.0"  # Change version
        version2 = self.validator._get_module_version(mock_module, "test_module")
        assert version2 == "1.0.0"  # Should still return cached version


class TestDependencyListing:
    """Test dependency listing functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.validator = DependencyValidator()
        self.validator.dependencies.clear()

    def test_list_dependencies_all(self):
        """Test listing all dependencies."""
        # Add various types of dependencies
        self.validator.add_dependency(
            DependencyInfo(
                name="req1",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Required 1",
                alternatives=[],
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="opt1",
                version_constraint=">=2.0.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Optional 1",
                alternatives=[],
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="dev1",
                version_constraint=">=3.0.0",
                dependency_type=DependencyType.DEVELOPMENT,
                purpose="Development 1",
                alternatives=[],
            )
        )

        all_deps = self.validator.list_dependencies()
        assert len(all_deps) == 3
        assert "req1" in all_deps
        assert "opt1" in all_deps
        assert "dev1" in all_deps

    def test_list_dependencies_by_type(self):
        """Test listing dependencies filtered by type."""
        # Add various types of dependencies
        self.validator.add_dependency(
            DependencyInfo(
                name="req1",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Required 1",
                alternatives=[],
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="req2",
                version_constraint=">=1.0.0",
                dependency_type=DependencyType.REQUIRED,
                purpose="Required 2",
                alternatives=[],
            )
        )

        self.validator.add_dependency(
            DependencyInfo(
                name="opt1",
                version_constraint=">=2.0.0",
                dependency_type=DependencyType.OPTIONAL,
                purpose="Optional 1",
                alternatives=[],
            )
        )

        required_deps = self.validator.list_dependencies(DependencyType.REQUIRED)
        assert len(required_deps) == 2
        assert "req1" in required_deps
        assert "req2" in required_deps
        assert "opt1" not in required_deps

        optional_deps = self.validator.list_dependencies(DependencyType.OPTIONAL)
        assert len(optional_deps) == 1
        assert "opt1" in optional_deps
        assert "req1" not in optional_deps

        dev_deps = self.validator.list_dependencies(DependencyType.DEVELOPMENT)
        assert len(dev_deps) == 0

    def test_get_dependency_info(self):
        """Test getting information about a specific dependency."""
        dep = DependencyInfo(
            name="test_dep",
            version_constraint=">=1.0.0",
            dependency_type=DependencyType.REQUIRED,
            purpose="Testing",
            alternatives=["alt1"],
        )

        self.validator.add_dependency(dep)

        # Get existing dependency
        info = self.validator.get_dependency_info("test_dep")
        assert info == dep

        # Get non-existent dependency
        info = self.validator.get_dependency_info("non_existent")
        assert info is None


if __name__ == "__main__":
    pytest.main([__file__])
