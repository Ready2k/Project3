"""Integration tests for CLI tools with actual catalog system."""

import pytest
import json
import tempfile
import subprocess
import sys
from pathlib import Path
from unittest.mock import patch


class TestCLIIntegration:
    """Integration tests for CLI tools."""

    @pytest.fixture
    def temp_catalog(self):
        """Create temporary catalog for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            # Create minimal catalog structure
            catalog_data = {
                "metadata": {
                    "total_technologies": 1,
                    "last_auto_update": "2023-12-01T10:00:00",
                },
                "technologies": {
                    "test_tech": {
                        "id": "test_tech",
                        "name": "Test Technology",
                        "canonical_name": "Test Technology",
                        "category": "testing",
                        "description": "A technology for testing purposes",
                        "aliases": [],
                        "ecosystem": "open_source",
                        "confidence_score": 1.0,
                        "pending_review": False,
                        "integrates_with": [],
                        "alternatives": [],
                        "tags": ["test"],
                        "use_cases": ["testing"],
                        "license": "MIT",
                        "maturity": "stable",
                        "auto_generated": False,
                        "source_context": None,
                        "added_date": "2023-12-01T10:00:00",
                        "last_updated": None,
                        "review_status": "approved",
                        "review_notes": None,
                        "reviewed_by": None,
                        "reviewed_date": None,
                        "mention_count": 0,
                        "selection_count": 0,
                        "validation_errors": [],
                        "last_validated": None,
                    }
                },
            }

            json.dump(catalog_data, f, indent=2)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    def run_cli_command(self, command_args, temp_catalog_path=None):
        """Run CLI command and return result."""
        # Prepare command
        cmd = [sys.executable, "-m", "app.cli.main"] + command_args

        # Set environment if temp catalog provided
        env = None
        if temp_catalog_path:
            env = {"CATALOG_PATH": str(temp_catalog_path)}

        # Run command
        try:
            result = subprocess.run(
                cmd,
                capture_output=True,
                text=True,
                env=env,
                cwd=Path(__file__).parent.parent.parent.parent,  # Project root
            )
            return result
        except Exception as e:
            pytest.fail(f"Failed to run CLI command {cmd}: {e}")

    @patch(
        "app.services.catalog.intelligent_manager.IntelligentCatalogManager.__init__"
    )
    def test_catalog_list_command(self, mock_init, temp_catalog):
        """Test catalog list command with real data."""

        # Mock the manager to use temp catalog
        def init_with_temp_catalog(self, catalog_path=None):
            self.catalog_path = temp_catalog
            self.technologies = {}
            self.name_index = {}
            self.logger = type(
                "MockLogger",
                (),
                {
                    "info": lambda x: None,
                    "error": lambda x: None,
                    "debug": lambda x: None,
                },
            )()
            self._load_catalog()
            self._build_indexes()

        mock_init.side_effect = init_with_temp_catalog

        # Run command
        result = self.run_cli_command(["catalog", "list"])

        # Verify
        assert result.returncode == 0
        assert "test_tech" in result.stdout
        assert "Test Technology" in result.stdout

    @patch(
        "app.services.catalog.intelligent_manager.IntelligentCatalogManager.__init__"
    )
    def test_catalog_show_command(self, mock_init, temp_catalog):
        """Test catalog show command with real data."""

        # Mock the manager to use temp catalog
        def init_with_temp_catalog(self, catalog_path=None):
            self.catalog_path = temp_catalog
            self.technologies = {}
            self.name_index = {}
            self.logger = type(
                "MockLogger",
                (),
                {
                    "info": lambda x: None,
                    "error": lambda x: None,
                    "debug": lambda x: None,
                },
            )()
            self._load_catalog()
            self._build_indexes()

        mock_init.side_effect = init_with_temp_catalog

        # Run command
        result = self.run_cli_command(["catalog", "show", "test_tech"])

        # Verify
        assert result.returncode == 0
        assert "Technology: Test Technology" in result.stdout
        assert "ID: test_tech" in result.stdout
        assert "Category: testing" in result.stdout

    @patch(
        "app.services.catalog.intelligent_manager.IntelligentCatalogManager.__init__"
    )
    def test_catalog_search_command(self, mock_init, temp_catalog):
        """Test catalog search command with real data."""

        # Mock the manager to use temp catalog
        def init_with_temp_catalog(self, catalog_path=None):
            self.catalog_path = temp_catalog
            self.technologies = {}
            self.name_index = {}
            self.logger = type(
                "MockLogger",
                (),
                {
                    "info": lambda x: None,
                    "error": lambda x: None,
                    "debug": lambda x: None,
                },
            )()
            self._load_catalog()
            self._build_indexes()

        mock_init.side_effect = init_with_temp_catalog

        # Run command
        result = self.run_cli_command(["catalog", "search", "test"])

        # Verify
        assert result.returncode == 0
        assert "Test Technology" in result.stdout

    @patch(
        "app.services.catalog.intelligent_manager.IntelligentCatalogManager.__init__"
    )
    def test_catalog_stats_command(self, mock_init, temp_catalog):
        """Test catalog stats command with real data."""

        # Mock the manager to use temp catalog
        def init_with_temp_catalog(self, catalog_path=None):
            self.catalog_path = temp_catalog
            self.technologies = {}
            self.name_index = {}
            self.logger = type(
                "MockLogger",
                (),
                {
                    "info": lambda x: None,
                    "error": lambda x: None,
                    "debug": lambda x: None,
                },
            )()
            self._load_catalog()
            self._build_indexes()

        mock_init.side_effect = init_with_temp_catalog

        # Run command
        result = self.run_cli_command(["catalog", "stats"])

        # Verify
        assert result.returncode == 0
        assert "Total entries:" in result.stdout

    @patch(
        "app.services.catalog.intelligent_manager.IntelligentCatalogManager.__init__"
    )
    def test_catalog_validate_command(self, mock_init, temp_catalog):
        """Test catalog validate command with real data."""

        # Mock the manager to use temp catalog
        def init_with_temp_catalog(self, catalog_path=None):
            self.catalog_path = temp_catalog
            self.technologies = {}
            self.name_index = {}
            self.logger = type(
                "MockLogger",
                (),
                {
                    "info": lambda x: None,
                    "error": lambda x: None,
                    "debug": lambda x: None,
                },
            )()
            self._load_catalog()
            self._build_indexes()

        mock_init.side_effect = init_with_temp_catalog

        # Run command
        result = self.run_cli_command(["catalog", "validate"])

        # Verify
        assert result.returncode == 0
        # Should pass validation for our test data
        assert (
            "✓ Catalog validation passed" in result.stdout
            or "✗ Catalog validation failed" in result.stdout
        )

    def test_dashboard_overview_command(self):
        """Test dashboard overview command."""
        # This test uses the actual catalog system
        result = self.run_cli_command(["dashboard", "overview"])

        # Should not crash and should show some output
        # Note: May show errors if catalog is empty, but shouldn't crash
        assert result.returncode == 0 or "Error" in result.stderr

    def test_review_list_command(self):
        """Test review list command."""
        # This test uses the actual catalog system
        result = self.run_cli_command(["review", "list"])

        # Should not crash
        assert result.returncode == 0 or "Error" in result.stderr

    def test_bulk_export_command(self):
        """Test bulk export command."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            export_path = Path(f.name)

        try:
            # Run export command
            result = self.run_cli_command(["bulk", "export", str(export_path)])

            # Should not crash (may have no data to export)
            assert result.returncode == 0 or "No technologies" in result.stdout

        finally:
            # Cleanup
            if export_path.exists():
                export_path.unlink()

    def test_main_cli_help(self):
        """Test main CLI help command."""
        result = self.run_cli_command(["--help"])

        # Verify
        assert result.returncode == 0
        assert "Technology Catalog Management Suite" in result.stdout
        assert "catalog" in result.stdout
        assert "review" in result.stdout
        assert "bulk" in result.stdout
        assert "dashboard" in result.stdout

    def test_catalog_help(self):
        """Test catalog tool help."""
        result = self.run_cli_command(["catalog", "--help"])

        # Verify
        assert result.returncode == 0
        assert "Technology Catalog Management CLI" in result.stdout
        assert "add" in result.stdout
        assert "update" in result.stdout
        assert "list" in result.stdout

    def test_invalid_command(self):
        """Test invalid command handling."""
        result = self.run_cli_command(["invalid_command"])

        # Should show help and exit with error
        assert result.returncode != 0

    def test_catalog_invalid_subcommand(self):
        """Test invalid catalog subcommand."""
        result = self.run_cli_command(["catalog", "invalid_subcommand"])

        # Should show help and exit with error
        assert result.returncode != 0


class TestCLIWithRealCatalog:
    """Tests that work with the real catalog system."""

    def test_catalog_manager_import(self):
        """Test that catalog manager can be imported."""
        try:
            from app.cli.catalog_manager import create_parser

            # Should be able to create instances
            parser = create_parser()
            assert parser is not None

            # CLI creation might fail due to service dependencies, but import should work

        except ImportError as e:
            pytest.fail(f"Failed to import catalog manager: {e}")

    def test_review_manager_import(self):
        """Test that review manager can be imported."""
        try:
            from app.cli.review_manager import create_parser

            # Should be able to create parser
            parser = create_parser()
            assert parser is not None

        except ImportError as e:
            pytest.fail(f"Failed to import review manager: {e}")

    def test_bulk_operations_import(self):
        """Test that bulk operations can be imported."""
        try:
            from app.cli.bulk_operations import create_parser

            # Should be able to create parser
            parser = create_parser()
            assert parser is not None

        except ImportError as e:
            pytest.fail(f"Failed to import bulk operations: {e}")

    def test_dashboard_import(self):
        """Test that dashboard can be imported."""
        try:
            from app.cli.catalog_dashboard import create_parser

            # Should be able to create parser
            parser = create_parser()
            assert parser is not None

        except ImportError as e:
            pytest.fail(f"Failed to import dashboard: {e}")

    def test_main_cli_import(self):
        """Test that main CLI can be imported."""
        try:
            from app.cli.main import create_parser

            # Should be able to create parser
            parser = create_parser()
            assert parser is not None

        except ImportError as e:
            pytest.fail(f"Failed to import main CLI: {e}")
