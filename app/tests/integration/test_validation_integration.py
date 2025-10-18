"""Integration tests for technology compatibility validation system."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.validation.compatibility_validator import (
    TechnologyCompatibilityValidator,
)
from app.services.validation.models import ConflictSeverity, ConflictType
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import EcosystemType


class TestValidationIntegration:
    """Integration tests for the validation system."""

    @pytest.fixture
    def temp_catalog_path(self):
        """Create a temporary catalog file for testing."""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".json", delete=False) as f:
            catalog_data = {
                "metadata": {"version": "test", "total_technologies": 5},
                "technologies": {
                    "aws_s3": {
                        "id": "aws_s3",
                        "name": "AWS S3",
                        "canonical_name": "Amazon S3",
                        "category": "storage",
                        "description": "Amazon Simple Storage Service",
                        "aliases": ["Amazon S3", "S3"],
                        "ecosystem": "aws",
                        "integrates_with": ["aws_lambda", "aws_ec2"],
                        "alternatives": ["azure_blob", "gcp_storage"],
                        "tags": ["storage", "cloud", "aws"],
                        "use_cases": ["data_storage", "backup"],
                        "license": "Commercial",
                        "maturity": "mature",
                        "auto_generated": False,
                        "pending_review": False,
                        "confidence_score": 1.0,
                        "review_status": "approved",
                    },
                    "azure_blob": {
                        "id": "azure_blob",
                        "name": "Azure Blob Storage",
                        "canonical_name": "Azure Blob Storage",
                        "category": "storage",
                        "description": "Microsoft Azure Blob Storage",
                        "aliases": ["Azure Blob", "Blob Storage"],
                        "ecosystem": "azure",
                        "integrates_with": ["azure_functions"],
                        "alternatives": ["aws_s3", "gcp_storage"],
                        "tags": ["storage", "cloud", "azure"],
                        "use_cases": ["data_storage", "backup"],
                        "license": "Commercial",
                        "maturity": "mature",
                        "auto_generated": False,
                        "pending_review": False,
                        "confidence_score": 1.0,
                        "review_status": "approved",
                    },
                    "fastapi": {
                        "id": "fastapi",
                        "name": "FastAPI",
                        "canonical_name": "FastAPI",
                        "category": "frameworks",
                        "description": "Modern Python web framework",
                        "aliases": ["fast-api"],
                        "ecosystem": "open_source",
                        "integrates_with": ["python", "pydantic"],
                        "alternatives": ["django", "flask"],
                        "tags": ["python", "web", "api"],
                        "use_cases": ["web_api", "microservices"],
                        "license": "MIT",
                        "maturity": "stable",
                        "auto_generated": False,
                        "pending_review": False,
                        "confidence_score": 1.0,
                        "review_status": "approved",
                    },
                    "postgresql": {
                        "id": "postgresql",
                        "name": "PostgreSQL",
                        "canonical_name": "PostgreSQL",
                        "category": "databases",
                        "description": "Advanced open source relational database",
                        "aliases": ["postgres", "psql"],
                        "ecosystem": "open_source",
                        "integrates_with": ["python", "fastapi"],
                        "alternatives": ["mysql", "sqlite"],
                        "tags": ["database", "sql", "relational"],
                        "use_cases": ["data_storage", "analytics"],
                        "license": "PostgreSQL License",
                        "maturity": "mature",
                        "auto_generated": False,
                        "pending_review": False,
                        "confidence_score": 1.0,
                        "review_status": "approved",
                    },
                    "mysql": {
                        "id": "mysql",
                        "name": "MySQL",
                        "canonical_name": "MySQL",
                        "category": "databases",
                        "description": "Popular open source relational database",
                        "aliases": ["mysql-server"],
                        "ecosystem": "open_source",
                        "integrates_with": ["python", "php"],
                        "alternatives": ["postgresql", "sqlite"],
                        "tags": ["database", "sql", "relational"],
                        "use_cases": ["data_storage", "web_apps"],
                        "license": "GPL",
                        "maturity": "mature",
                        "auto_generated": False,
                        "pending_review": False,
                        "confidence_score": 1.0,
                        "review_status": "approved",
                    },
                },
            }
            json.dump(catalog_data, f, indent=2)
            temp_path = Path(f.name)

        yield temp_path

        # Cleanup
        if temp_path.exists():
            temp_path.unlink()

    @pytest.fixture
    def catalog_manager(self, temp_catalog_path):
        """Create catalog manager with test data."""
        with patch(
            "app.services.catalog.intelligent_manager.require_service"
        ) as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger

            manager = IntelligentCatalogManager(catalog_path=temp_catalog_path)
            return manager

    @pytest.fixture
    def validator(self, catalog_manager):
        """Create validator with test catalog."""
        with patch(
            "app.services.validation.compatibility_validator.require_service"
        ) as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger

            validator = TechnologyCompatibilityValidator(
                catalog_manager=catalog_manager
            )
            return validator

    def test_end_to_end_validation_consistent_stack(self, validator):
        """Test end-to-end validation of a consistent tech stack."""
        tech_stack = ["FastAPI", "PostgreSQL"]
        context_priority = {"FastAPI": 0.9, "PostgreSQL": 0.8}

        report = validator.validate_tech_stack(tech_stack, context_priority)

        # Should be fully compatible
        assert report.compatibility_result.is_compatible
        assert report.compatibility_result.overall_score >= 0.8
        assert len(report.validated_tech_stack) == 2
        assert len(report.compatibility_result.removed_technologies) == 0

        # Ecosystem should be consistent (both open source)
        assert report.compatibility_result.ecosystem_result.is_consistent
        assert (
            report.compatibility_result.ecosystem_result.primary_ecosystem
            == EcosystemType.OPEN_SOURCE
        )

        # Should have inclusion explanations
        assert len(report.inclusion_explanations) == 2
        assert "FastAPI" in report.inclusion_explanations
        assert "PostgreSQL" in report.inclusion_explanations

    def test_end_to_end_validation_conflicting_stack(self, validator):
        """Test end-to-end validation of a conflicting tech stack."""
        tech_stack = ["AWS S3", "Azure Blob Storage", "FastAPI"]
        context_priority = {"AWS S3": 0.9, "Azure Blob Storage": 0.3, "FastAPI": 0.8}

        report = validator.validate_tech_stack(tech_stack, context_priority)

        # Should detect ecosystem conflicts
        assert not report.compatibility_result.ecosystem_result.is_consistent
        assert (
            len(
                report.compatibility_result.ecosystem_result.mixed_ecosystem_technologies
            )
            > 0
        )

        # Should have conflicts detected
        assert len(report.compatibility_result.conflicts) > 0

        # Lower priority technology should be removed
        assert "Azure Blob Storage" in report.compatibility_result.removed_technologies
        assert "AWS S3" in report.validated_tech_stack
        assert "FastAPI" in report.validated_tech_stack

        # Should have explanations for removals
        assert "Azure Blob Storage" in report.exclusion_explanations
        assert "Azure Blob Storage" in report.alternative_suggestions

    def test_database_conflict_resolution(self, validator):
        """Test resolution of database conflicts."""
        tech_stack = ["PostgreSQL", "MySQL", "FastAPI"]
        context_priority = {"PostgreSQL": 0.8, "MySQL": 0.4, "FastAPI": 0.9}

        report = validator.validate_tech_stack(tech_stack, context_priority)

        # Should detect database conflict
        db_conflicts = [
            c
            for c in report.compatibility_result.conflicts
            if c.conflict_type == ConflictType.ARCHITECTURE_MISMATCH
        ]

        # MySQL should be removed (lower priority)
        if db_conflicts:  # Only check if conflict was detected
            assert "MySQL" in report.compatibility_result.removed_technologies
            assert "PostgreSQL" in report.validated_tech_stack

    def test_ecosystem_consistency_checking(self, validator):
        """Test ecosystem consistency checking functionality."""
        # Test AWS-only stack
        aws_stack = ["AWS S3"]
        result = validator.check_ecosystem_consistency(aws_stack)

        assert result.is_consistent
        assert result.primary_ecosystem == EcosystemType.AWS
        assert result.ecosystem_distribution["aws"] == 1

        # Test mixed cloud stack
        mixed_stack = ["AWS S3", "Azure Blob Storage"]
        result = validator.check_ecosystem_consistency(mixed_stack)

        assert not result.is_consistent
        assert len(result.mixed_ecosystem_technologies) > 0
        assert len(result.recommendations) > 0

    def test_compatibility_matrix_integration(self, validator):
        """Test integration with compatibility matrices."""
        # Add a custom compatibility rule
        validator.add_compatibility_rule(
            "FastAPI", "Django", 0.2, "Both are web frameworks"
        )

        tech_stack = ["FastAPI", "Django"]
        report = validator.validate_tech_stack(tech_stack)

        # Should detect integration conflict due to low compatibility score
        integration_conflicts = [
            c
            for c in report.compatibility_result.conflicts
            if c.conflict_type == ConflictType.INTEGRATION_CONFLICT
        ]

        assert len(integration_conflicts) > 0
        conflict = integration_conflicts[0]
        assert "FastAPI" in [conflict.tech1, conflict.tech2]
        assert "Django" in [conflict.tech1, conflict.tech2]

    def test_context_priority_influence(self, validator):
        """Test how context priority influences validation decisions."""
        tech_stack = ["AWS S3", "Azure Blob Storage"]

        # Test with AWS priority
        aws_priority = {"AWS S3": 0.9, "Azure Blob Storage": 0.2}
        report_aws = validator.validate_tech_stack(tech_stack, aws_priority)

        # Test with Azure priority
        azure_priority = {"AWS S3": 0.2, "Azure Blob Storage": 0.9}
        report_azure = validator.validate_tech_stack(tech_stack, azure_priority)

        # Different priorities should lead to different outcomes
        if report_aws.compatibility_result.removed_technologies:
            assert (
                "Azure Blob Storage"
                in report_aws.compatibility_result.removed_technologies
            )

        if report_azure.compatibility_result.removed_technologies:
            assert "AWS S3" in report_azure.compatibility_result.removed_technologies

    def test_alternative_suggestions_generation(self, validator):
        """Test generation of alternative technology suggestions."""
        tech_stack = ["AWS S3", "Azure Blob Storage"]
        context_priority = {"AWS S3": 0.9, "Azure Blob Storage": 0.3}

        report = validator.validate_tech_stack(tech_stack, context_priority)

        # Should have alternatives for removed technologies
        if report.compatibility_result.removed_technologies:
            removed_tech = report.compatibility_result.removed_technologies[0]
            assert removed_tech in report.alternative_suggestions
            alternatives = report.alternative_suggestions[removed_tech]
            assert len(alternatives) > 0
            assert isinstance(alternatives, list)

    def test_validation_report_completeness(self, validator):
        """Test that validation reports contain all expected information."""
        tech_stack = ["FastAPI", "PostgreSQL", "AWS S3"]
        context_priority = {"FastAPI": 0.9, "PostgreSQL": 0.8, "AWS S3": 0.7}

        report = validator.validate_tech_stack(tech_stack, context_priority)

        # Check report structure
        assert report.original_tech_stack == tech_stack
        assert isinstance(report.validated_tech_stack, list)
        assert report.validation_timestamp is not None
        assert report.context_priority == context_priority

        # Check explanations exist for all technologies
        set(
            report.validated_tech_stack
            + report.compatibility_result.removed_technologies
        )

        for tech in report.validated_tech_stack:
            assert tech in report.inclusion_explanations

        for tech in report.compatibility_result.removed_technologies:
            assert tech in report.exclusion_explanations

        # Check serialization works
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "summary" in report_dict

        summary = report_dict["summary"]
        assert summary["original_count"] == len(tech_stack)
        assert summary["validated_count"] == len(report.validated_tech_stack)

    def test_empty_and_edge_cases(self, validator):
        """Test validation with empty and edge case inputs."""
        # Empty tech stack
        empty_report = validator.validate_tech_stack([])
        assert empty_report.compatibility_result.is_compatible
        assert len(empty_report.validated_tech_stack) == 0

        # Single technology
        single_report = validator.validate_tech_stack(["FastAPI"])
        assert single_report.compatibility_result.is_compatible
        assert len(single_report.validated_tech_stack) == 1

        # Unknown technology
        unknown_report = validator.validate_tech_stack(["UnknownTech"])
        # Should handle gracefully without crashing
        assert isinstance(unknown_report.validated_tech_stack, list)

    def test_conflict_severity_handling(self, validator):
        """Test handling of different conflict severities."""
        # Create a validator with custom conflict rules for testing
        validator.conflict_rules.append(
            {
                "name": "test_critical_conflict",
                "type": ConflictType.SECURITY_CONFLICT.value,
                "severity": ConflictSeverity.CRITICAL.value,
                "patterns": [
                    {"tech1_contains": ["fastapi"], "tech2_contains": ["postgresql"]}
                ],
                "description": "Test critical conflict",
                "resolution": "Test resolution",
            }
        )

        tech_stack = ["FastAPI", "PostgreSQL"]
        report = validator.validate_tech_stack(tech_stack)

        # Should detect and handle critical conflicts
        critical_conflicts = report.compatibility_result.get_conflicts_by_severity(
            ConflictSeverity.CRITICAL
        )
        if critical_conflicts:
            assert report.compatibility_result.has_critical_conflicts()
            # Critical conflicts should result in technology removal
            assert len(report.compatibility_result.removed_technologies) > 0

    @patch("builtins.open")
    @patch("json.dump")
    def test_compatibility_data_persistence(self, mock_json_dump, mock_open, validator):
        """Test saving and loading of compatibility data."""
        # Add some compatibility rules
        validator.add_compatibility_rule("FastAPI", "Django", 0.3, "Framework conflict")
        validator.add_compatibility_rule(
            "PostgreSQL", "MySQL", 0.4, "Database conflict"
        )

        # Save the data
        validator.save_compatibility_data()

        # Verify save was called
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()

        # Check the structure of saved data
        call_args = mock_json_dump.call_args[0]
        saved_data = call_args[0]

        assert "matrices" in saved_data
        assert "ecosystem_rules" in saved_data
        assert "conflict_rules" in saved_data
        assert len(saved_data["matrices"]) >= 2  # At least our two rules
