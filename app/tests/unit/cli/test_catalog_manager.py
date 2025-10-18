"""Tests for catalog manager CLI."""

import pytest
from unittest.mock import Mock, patch

from app.cli.catalog_manager import CatalogManagerCLI, create_parser
from app.services.catalog.models import TechEntry, EcosystemType, MaturityLevel


class TestCatalogManagerCLI:
    """Test cases for CatalogManagerCLI."""

    @pytest.fixture
    def cli(self):
        """Create CLI instance with mocked manager."""
        with patch(
            "app.cli.catalog_manager.IntelligentCatalogManager"
        ) as mock_manager_class:
            mock_manager = Mock()
            mock_manager_class.return_value = mock_manager

            cli = CatalogManagerCLI()
            cli.manager = mock_manager

            return cli, mock_manager

    @pytest.fixture
    def sample_tech(self):
        """Create sample technology entry."""
        return TechEntry(
            id="fastapi",
            name="FastAPI",
            canonical_name="FastAPI",
            category="frameworks",
            description="Modern, fast web framework for building APIs with Python",
            ecosystem=EcosystemType.OPEN_SOURCE,
            maturity=MaturityLevel.STABLE,
        )

    def test_add_technology_success(self, cli, capsys):
        """Test successful technology addition."""
        cli_instance, mock_manager = cli

        # Mock arguments
        args = Mock()
        args.name = "FastAPI"
        args.id = None
        args.canonical_name = None
        args.category = "frameworks"
        args.description = "Modern Python web framework"
        args.ecosystem = "open_source"
        args.maturity = "stable"
        args.license = "MIT"
        args.aliases = ["fast-api"]
        args.integrates_with = ["python"]
        args.alternatives = ["django"]
        args.tags = ["python", "api"]
        args.use_cases = ["rest_api"]
        args.pending_review = False

        # Mock manager methods
        mock_manager._generate_tech_id.return_value = "fastapi"
        mock_manager.technologies = {}

        # Execute
        cli_instance.add_technology(args)

        # Verify
        captured = capsys.readouterr()
        assert "✓ Added technology: FastAPI (ID: fastapi)" in captured.out
        assert mock_manager._rebuild_indexes.called
        assert mock_manager._save_catalog.called

    def test_add_technology_error(self, cli, capsys):
        """Test technology addition with error."""
        cli_instance, mock_manager = cli

        args = Mock()
        args.name = "FastAPI"
        args.id = None
        args.canonical_name = None
        args.category = "frameworks"
        args.description = "Modern Python web framework"
        args.ecosystem = "invalid_ecosystem"  # Invalid ecosystem
        args.maturity = "stable"
        args.license = "MIT"
        args.aliases = []
        args.integrates_with = []
        args.alternatives = []
        args.tags = []
        args.use_cases = []
        args.pending_review = False

        # Execute and verify exception
        with pytest.raises(SystemExit):
            cli_instance.add_technology(args)

        captured = capsys.readouterr()
        assert "✗ Error adding technology:" in captured.out

    def test_update_technology_success(self, cli, sample_tech, capsys):
        """Test successful technology update."""
        cli_instance, mock_manager = cli

        # Setup
        mock_manager.technologies = {"fastapi": sample_tech}
        mock_manager.update_technology.return_value = True

        args = Mock()
        args.tech_id = "fastapi"
        args.name = "Updated FastAPI"
        args.canonical_name = None
        args.category = None
        args.description = None
        args.ecosystem = None
        args.maturity = None
        args.license = None
        args.add_alias = ["new-alias"]
        args.add_integration = ["sqlalchemy"]
        args.add_alternative = ["flask"]
        args.add_tag = ["production"]
        args.add_use_case = ["microservices"]

        # Execute
        cli_instance.update_technology(args)

        # Verify
        captured = capsys.readouterr()
        assert "✓ Updated technology: fastapi" in captured.out
        assert mock_manager.update_technology.called

    def test_update_technology_not_found(self, cli, capsys):
        """Test updating non-existent technology."""
        cli_instance, mock_manager = cli

        mock_manager.technologies = {}

        args = Mock()
        args.tech_id = "nonexistent"
        args.name = None
        args.canonical_name = None
        args.category = None
        args.description = None
        args.ecosystem = None
        args.maturity = None
        args.license = None
        args.add_alias = None
        args.add_integration = None
        args.add_alternative = None
        args.add_tag = None
        args.add_use_case = None

        # Execute and verify exception
        with pytest.raises(SystemExit):
            cli_instance.update_technology(args)

        captured = capsys.readouterr()
        assert "✗ Technology not found: nonexistent" in captured.out

    def test_validate_catalog_success(self, cli, capsys):
        """Test successful catalog validation."""
        cli_instance, mock_manager = cli

        # Mock validation result
        validation_result = Mock()
        validation_result.is_valid = True
        validation_result.errors = []
        validation_result.warnings = []
        validation_result.suggestions = []

        mock_manager.validate_catalog_consistency.return_value = validation_result

        args = Mock()
        args.detailed = False

        # Execute
        cli_instance.validate_catalog(args)

        # Verify
        captured = capsys.readouterr()
        assert "✓ Catalog validation passed" in captured.out

    def test_validate_catalog_with_errors(self, cli, capsys):
        """Test catalog validation with errors."""
        cli_instance, mock_manager = cli

        # Mock validation result with errors
        validation_result = Mock()
        validation_result.is_valid = False
        validation_result.errors = ["Duplicate technology found"]
        validation_result.warnings = ["Missing description"]
        validation_result.suggestions = ["Add more integrations"]

        mock_manager.validate_catalog_consistency.return_value = validation_result

        args = Mock()
        args.detailed = False

        # Execute
        cli_instance.validate_catalog(args)

        # Verify
        captured = capsys.readouterr()
        assert "✗ Catalog validation failed" in captured.out
        assert "Duplicate technology found" in captured.out
        assert "Missing description" in captured.out
        assert "Add more integrations" in captured.out

    def test_show_statistics(self, cli, capsys):
        """Test showing catalog statistics."""
        cli_instance, mock_manager = cli

        # Mock statistics
        stats = Mock()
        stats.total_entries = 100
        stats.pending_review = 5
        stats.auto_generated = 20
        stats.validation_errors = 2
        stats.by_ecosystem = {"aws": 30, "open_source": 50}
        stats.by_category = {"frameworks": 25, "databases": 15}
        stats.by_maturity = {"stable": 60, "beta": 20}

        mock_manager.get_catalog_statistics.return_value = stats

        args = Mock()

        # Execute
        cli_instance.show_statistics(args)

        # Verify
        captured = capsys.readouterr()
        assert "Total entries: 100" in captured.out
        assert "Pending review: 5" in captured.out
        assert "aws: 30" in captured.out
        assert "frameworks: 25" in captured.out

    def test_search_technologies(self, cli, sample_tech, capsys):
        """Test searching technologies."""
        cli_instance, mock_manager = cli

        # Mock search results
        search_result = Mock()
        search_result.tech_entry = sample_tech
        search_result.match_score = 0.95
        search_result.match_type = "exact"

        mock_manager.search_technologies.return_value = [search_result]

        args = Mock()
        args.query = "fastapi"
        args.limit = 10

        # Execute
        cli_instance.search_technologies(args)

        # Verify
        captured = capsys.readouterr()
        assert "Found 1 technologies matching: fastapi" in captured.out
        assert "FastAPI (ID: fastapi)" in captured.out
        assert "Match Score: 0.95" in captured.out

    def test_search_no_results(self, cli, capsys):
        """Test searching with no results."""
        cli_instance, mock_manager = cli

        mock_manager.search_technologies.return_value = []

        args = Mock()
        args.query = "nonexistent"
        args.limit = 10

        # Execute
        cli_instance.search_technologies(args)

        # Verify
        captured = capsys.readouterr()
        assert "No technologies found matching: nonexistent" in captured.out

    def test_show_technology(self, cli, sample_tech, capsys):
        """Test showing technology details."""
        cli_instance, mock_manager = cli

        mock_manager.get_technology_by_id.return_value = sample_tech

        args = Mock()
        args.tech_id = "fastapi"

        # Execute
        cli_instance.show_technology(args)

        # Verify
        captured = capsys.readouterr()
        assert "Technology: FastAPI" in captured.out
        assert "ID: fastapi" in captured.out
        assert "Category: frameworks" in captured.out

    def test_show_technology_not_found(self, cli, capsys):
        """Test showing non-existent technology."""
        cli_instance, mock_manager = cli

        mock_manager.get_technology_by_id.return_value = None

        args = Mock()
        args.tech_id = "nonexistent"

        # Execute and verify exception
        with pytest.raises(SystemExit):
            cli_instance.show_technology(args)

        captured = capsys.readouterr()
        assert "✗ Technology not found: nonexistent" in captured.out

    def test_list_technologies(self, cli, sample_tech, capsys):
        """Test listing technologies."""
        cli_instance, mock_manager = cli

        mock_manager.technologies = {"fastapi": sample_tech}

        args = Mock()
        args.category = None
        args.ecosystem = None
        args.pending_review = False
        args.auto_generated = False
        args.sort_by = "name"
        args.verbose = False

        # Execute
        cli_instance.list_technologies(args)

        # Verify
        captured = capsys.readouterr()
        assert "Found 1 technologies" in captured.out
        assert "fastapi" in captured.out
        assert "FastAPI" in captured.out

    def test_list_technologies_with_filters(self, cli, sample_tech, capsys):
        """Test listing technologies with filters."""
        cli_instance, mock_manager = cli

        mock_manager.technologies = {"fastapi": sample_tech}

        args = Mock()
        args.category = "frameworks"
        args.ecosystem = None
        args.pending_review = False
        args.auto_generated = False
        args.sort_by = "name"
        args.verbose = True

        # Execute
        cli_instance.list_technologies(args)

        # Verify
        captured = capsys.readouterr()
        assert "Found 1 technologies" in captured.out
        assert "Description:" in captured.out  # Verbose mode

    def test_delete_technology_success(self, cli, sample_tech, capsys, monkeypatch):
        """Test successful technology deletion."""
        cli_instance, mock_manager = cli

        mock_manager.technologies = {"fastapi": sample_tech}

        # Mock user input
        monkeypatch.setattr("builtins.input", lambda _: "y")

        args = Mock()
        args.tech_id = "fastapi"
        args.force = False

        # Execute
        cli_instance.delete_technology(args)

        # Verify
        captured = capsys.readouterr()
        assert "✓ Deleted technology: FastAPI (ID: fastapi)" in captured.out
        assert mock_manager._rebuild_indexes.called
        assert mock_manager._save_catalog.called

    def test_delete_technology_cancelled(self, cli, sample_tech, capsys, monkeypatch):
        """Test cancelled technology deletion."""
        cli_instance, mock_manager = cli

        mock_manager.technologies = {"fastapi": sample_tech}

        # Mock user input (cancel)
        monkeypatch.setattr("builtins.input", lambda _: "n")

        args = Mock()
        args.tech_id = "fastapi"
        args.force = False

        # Execute
        cli_instance.delete_technology(args)

        # Verify
        captured = capsys.readouterr()
        assert "Deletion cancelled" in captured.out
        assert not mock_manager._rebuild_indexes.called

    def test_delete_technology_force(self, cli, sample_tech, capsys):
        """Test forced technology deletion."""
        cli_instance, mock_manager = cli

        mock_manager.technologies = {"fastapi": sample_tech}

        args = Mock()
        args.tech_id = "fastapi"
        args.force = True

        # Execute
        cli_instance.delete_technology(args)

        # Verify
        captured = capsys.readouterr()
        assert "✓ Deleted technology: FastAPI (ID: fastapi)" in captured.out
        assert mock_manager._rebuild_indexes.called
        assert mock_manager._save_catalog.called


class TestCatalogManagerParser:
    """Test cases for catalog manager argument parser."""

    def test_parser_creation(self):
        """Test parser creation."""
        parser = create_parser()
        assert parser is not None
        assert "Technology Catalog Management CLI" in parser.description

    def test_add_command_parsing(self):
        """Test add command argument parsing."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "add",
                "--name",
                "FastAPI",
                "--category",
                "frameworks",
                "--description",
                "Modern Python web framework",
                "--ecosystem",
                "open_source",
                "--aliases",
                "fast-api",
                "fastapi",
            ]
        )

        assert args.command == "add"
        assert args.name == "FastAPI"
        assert args.category == "frameworks"
        assert args.description == "Modern Python web framework"
        assert args.ecosystem == "open_source"
        assert args.aliases == ["fast-api", "fastapi"]

    def test_update_command_parsing(self):
        """Test update command argument parsing."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "update",
                "fastapi",
                "--name",
                "Updated FastAPI",
                "--add-alias",
                "new-alias",
                "--add-tag",
                "production",
            ]
        )

        assert args.command == "update"
        assert args.tech_id == "fastapi"
        assert args.name == "Updated FastAPI"
        assert args.add_alias == ["new-alias"]
        assert args.add_tag == ["production"]

    def test_search_command_parsing(self):
        """Test search command argument parsing."""
        parser = create_parser()

        args = parser.parse_args(["search", "fastapi", "--limit", "5"])

        assert args.command == "search"
        assert args.query == "fastapi"
        assert args.limit == 5

    def test_list_command_parsing(self):
        """Test list command argument parsing."""
        parser = create_parser()

        args = parser.parse_args(
            [
                "list",
                "--category",
                "frameworks",
                "--ecosystem",
                "aws",
                "--pending-review",
                "--verbose",
            ]
        )

        assert args.command == "list"
        assert args.category == "frameworks"
        assert args.ecosystem == "aws"
        assert args.pending_review is True
        assert args.verbose is True

    def test_validate_command_parsing(self):
        """Test validate command argument parsing."""
        parser = create_parser()

        args = parser.parse_args(["validate", "--detailed"])

        assert args.command == "validate"
        assert args.detailed is True

    def test_delete_command_parsing(self):
        """Test delete command argument parsing."""
        parser = create_parser()

        args = parser.parse_args(["delete", "tech_id", "--force"])

        assert args.command == "delete"
        assert args.tech_id == "tech_id"
        assert args.force is True
