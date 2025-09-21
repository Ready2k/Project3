"""Unit tests for TechnologyCompatibilityValidator."""

import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from pathlib import Path

from app.services.validation.compatibility_validator import TechnologyCompatibilityValidator
from app.services.validation.models import (
    ConflictType, ConflictSeverity, TechnologyConflict, 
    EcosystemConsistencyResult, CompatibilityResult, ValidationReport
)
from app.services.catalog.models import TechEntry, EcosystemType, MaturityLevel


class TestTechnologyCompatibilityValidator:
    """Test cases for TechnologyCompatibilityValidator."""
    
    @pytest.fixture
    def mock_catalog_manager(self):
        """Create a mock catalog manager."""
        mock_manager = Mock()
        
        # Create sample tech entries
        aws_tech = TechEntry(
            id="aws_s3",
            name="AWS S3",
            canonical_name="Amazon S3",
            category="storage",
            description="Amazon Simple Storage Service",
            ecosystem=EcosystemType.AWS,
            maturity=MaturityLevel.MATURE,
            alternatives=["Azure Blob Storage", "Google Cloud Storage"]
        )
        
        azure_tech = TechEntry(
            id="azure_blob",
            name="Azure Blob Storage",
            canonical_name="Azure Blob Storage",
            category="storage",
            description="Microsoft Azure Blob Storage",
            ecosystem=EcosystemType.AZURE,
            maturity=MaturityLevel.MATURE,
            alternatives=["AWS S3", "Google Cloud Storage"]
        )
        
        fastapi_tech = TechEntry(
            id="fastapi",
            name="FastAPI",
            canonical_name="FastAPI",
            category="frameworks",
            description="Modern Python web framework",
            ecosystem=EcosystemType.OPEN_SOURCE,
            maturity=MaturityLevel.STABLE
        )
        
        # Mock lookup results
        def mock_lookup(tech_name, fuzzy_threshold=0.8):
            lookup_map = {
                "AWS S3": Mock(tech_entry=aws_tech, match_score=1.0),
                "Azure Blob Storage": Mock(tech_entry=azure_tech, match_score=1.0),
                "FastAPI": Mock(tech_entry=fastapi_tech, match_score=1.0)
            }
            return lookup_map.get(tech_name)
        
        mock_manager.lookup_technology.side_effect = mock_lookup
        mock_manager.get_technology_by_id.return_value = aws_tech
        mock_manager.get_technologies_by_category.return_value = [aws_tech, azure_tech]
        
        return mock_manager
    
    @pytest.fixture
    def validator(self, mock_catalog_manager):
        """Create validator instance with mocked dependencies."""
        with patch('app.services.validation.compatibility_validator.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            validator = TechnologyCompatibilityValidator(catalog_manager=mock_catalog_manager)
            return validator
    
    def test_initialization(self, validator):
        """Test validator initialization."""
        assert validator is not None
        assert validator.catalog_manager is not None
        assert isinstance(validator.compatibility_matrices, dict)
        assert isinstance(validator.ecosystem_rules, dict)
        assert isinstance(validator.conflict_rules, list)
    
    def test_ecosystem_consistency_single_ecosystem(self, validator):
        """Test ecosystem consistency with single ecosystem."""
        tech_stack = ["AWS S3", "AWS Lambda", "Amazon RDS"]
        
        result = validator.check_ecosystem_consistency(tech_stack)
        
        assert isinstance(result, EcosystemConsistencyResult)
        assert result.is_consistent
        assert result.primary_ecosystem == EcosystemType.AWS
        assert "aws" in result.ecosystem_distribution
        assert len(result.mixed_ecosystem_technologies) == 0
    
    def test_ecosystem_consistency_mixed_ecosystems(self, validator):
        """Test ecosystem consistency with mixed ecosystems."""
        tech_stack = ["AWS S3", "Azure Blob Storage", "FastAPI"]
        
        result = validator.check_ecosystem_consistency(tech_stack)
        
        assert isinstance(result, EcosystemConsistencyResult)
        assert not result.is_consistent  # Mixed cloud providers
        assert len(result.mixed_ecosystem_technologies) > 0
        assert len(result.recommendations) > 0
    
    def test_conflict_detection_cloud_providers(self, validator):
        """Test conflict detection between cloud providers."""
        tech_entries = {
            "AWS S3": Mock(ecosystem=EcosystemType.AWS, license="Commercial"),
            "Azure Blob Storage": Mock(ecosystem=EcosystemType.AZURE, license="Commercial")
        }
        
        conflicts = validator._detect_conflicts(tech_entries)
        
        # Should detect cloud provider conflict
        cloud_conflicts = [c for c in conflicts if c.conflict_type == ConflictType.ECOSYSTEM_MISMATCH]
        assert len(cloud_conflicts) > 0
        
        conflict = cloud_conflicts[0]
        assert conflict.severity in [ConflictSeverity.HIGH, ConflictSeverity.CRITICAL]
        assert "AWS S3" in [conflict.tech1, conflict.tech2]
        assert "Azure Blob Storage" in [conflict.tech1, conflict.tech2]
    
    def test_conflict_resolution_with_priority(self, validator):
        """Test conflict resolution using context priority."""
        tech_stack = ["AWS S3", "Azure Blob Storage"]
        conflicts = [
            TechnologyConflict(
                tech1="AWS S3",
                tech2="Azure Blob Storage",
                conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
                severity=ConflictSeverity.HIGH,
                description="Cloud provider conflict",
                explanation="Multiple cloud providers detected"
            )
        ]
        
        # AWS S3 has higher priority
        context_priority = {"AWS S3": 0.9, "Azure Blob Storage": 0.3}
        
        validated, removed = validator._resolve_conflicts(tech_stack, conflicts, context_priority)
        
        assert "AWS S3" in validated
        assert "Azure Blob Storage" in removed
        assert len(removed) == 1
    
    def test_conflict_resolution_equal_priority(self, validator):
        """Test conflict resolution with equal priorities."""
        tech_stack = ["AWS S3", "Azure Blob Storage"]
        conflicts = [
            TechnologyConflict(
                tech1="AWS S3",
                tech2="Azure Blob Storage",
                conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
                severity=ConflictSeverity.HIGH,
                description="Cloud provider conflict",
                explanation="Multiple cloud providers detected"
            )
        ]
        
        # Equal priorities - should use maturity as tiebreaker
        context_priority = {"AWS S3": 0.5, "Azure Blob Storage": 0.5}
        
        validated, removed = validator._resolve_conflicts(tech_stack, conflicts, context_priority)
        
        assert len(validated) == 1
        assert len(removed) == 1
    
    def test_compatibility_score_calculation(self, validator):
        """Test overall compatibility score calculation."""
        validated_technologies = ["FastAPI", "PostgreSQL", "Redis"]
        
        # No conflicts - high score
        conflicts = []
        ecosystem_result = EcosystemConsistencyResult(
            is_consistent=True,
            primary_ecosystem=EcosystemType.OPEN_SOURCE,
            ecosystem_distribution={"open_source": 3},
            mixed_ecosystem_technologies=[],
            recommendations=[]
        )
        
        score = validator._calculate_compatibility_score(validated_technologies, conflicts, ecosystem_result)
        assert score == 1.0
        
        # With conflicts - lower score
        conflicts = [
            TechnologyConflict(
                tech1="FastAPI",
                tech2="PostgreSQL",
                conflict_type=ConflictType.INTEGRATION_CONFLICT,
                severity=ConflictSeverity.HIGH,
                description="Test conflict",
                explanation="Test explanation"
            )
        ]
        
        score = validator._calculate_compatibility_score(validated_technologies, conflicts, ecosystem_result)
        assert score < 1.0
        assert score >= 0.0
    
    def test_validate_tech_stack_comprehensive(self, validator):
        """Test comprehensive tech stack validation."""
        tech_stack = ["FastAPI", "PostgreSQL", "Redis"]
        context_priority = {"FastAPI": 0.9, "PostgreSQL": 0.8, "Redis": 0.7}
        
        report = validator.validate_tech_stack(tech_stack, context_priority)
        
        assert isinstance(report, ValidationReport)
        assert report.original_tech_stack == tech_stack
        assert len(report.validated_tech_stack) <= len(tech_stack)
        assert isinstance(report.compatibility_result, CompatibilityResult)
        assert report.validation_timestamp is not None
        assert report.context_priority == context_priority
        
        # Check explanations
        assert isinstance(report.inclusion_explanations, dict)
        assert isinstance(report.exclusion_explanations, dict)
        assert isinstance(report.alternative_suggestions, dict)
    
    def test_add_compatibility_rule(self, validator):
        """Test adding custom compatibility rules."""
        tech1 = "FastAPI"
        tech2 = "Django"
        compatibility_score = 0.3  # Low compatibility
        notes = "Both are web frameworks - choose one"
        
        validator.add_compatibility_rule(tech1, tech2, compatibility_score, notes)
        
        assert (tech1, tech2) in validator.compatibility_matrices
        matrix = validator.compatibility_matrices[(tech1, tech2)]
        assert matrix.compatibility_score == compatibility_score
        assert matrix.notes == notes
        assert not matrix.is_compatible()  # Should be below default threshold
    
    def test_infer_ecosystem_from_name(self, validator):
        """Test ecosystem inference from technology names."""
        assert validator._infer_ecosystem_from_name("AWS Lambda") == "aws"
        assert validator._infer_ecosystem_from_name("Amazon S3") == "aws"
        assert validator._infer_ecosystem_from_name("Azure Functions") == "azure"
        assert validator._infer_ecosystem_from_name("Microsoft SQL Server") == "azure"
        assert validator._infer_ecosystem_from_name("Google Cloud Storage") == "gcp"
        assert validator._infer_ecosystem_from_name("GCP BigQuery") == "gcp"
        assert validator._infer_ecosystem_from_name("FastAPI") == "open_source"
    
    def test_generate_alternative_suggestions(self, validator):
        """Test generation of alternative technology suggestions."""
        removed_technologies = ["Azure Blob Storage"]
        tech_entries = {
            "Azure Blob Storage": Mock(
                alternatives=["AWS S3", "Google Cloud Storage", "MinIO"]
            )
        }
        
        alternatives = validator._generate_alternative_suggestions(removed_technologies, tech_entries)
        
        assert "Azure Blob Storage" in alternatives
        assert len(alternatives["Azure Blob Storage"]) <= 3  # Limited to top 3
        assert "AWS S3" in alternatives["Azure Blob Storage"]
    
    def test_conflict_pattern_matching(self, validator):
        """Test conflict pattern matching logic."""
        tech1 = "AWS S3"
        tech2 = "Azure Blob Storage"
        tech1_entry = Mock(license="Commercial")
        tech2_entry = Mock(license="Commercial")
        
        # Test cloud provider conflict pattern
        pattern = {
            "tech1_contains": ["aws"],
            "tech2_contains": ["azure"]
        }
        
        result = validator._matches_conflict_pattern(tech1, tech2, tech1_entry, tech2_entry, pattern)
        assert result is True
        
        # Test non-matching pattern
        pattern = {
            "tech1_contains": ["google"],
            "tech2_contains": ["azure"]
        }
        
        result = validator._matches_conflict_pattern(tech1, tech2, tech1_entry, tech2_entry, pattern)
        assert result is False
    
    def test_choose_technology_to_remove(self, validator):
        """Test technology removal choice logic."""
        conflict = TechnologyConflict(
            tech1="AWS S3",
            tech2="Azure Blob Storage",
            conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
            severity=ConflictSeverity.HIGH,
            description="Cloud provider conflict",
            explanation="Multiple cloud providers"
        )
        
        # Higher priority for AWS S3
        context_priority = {"AWS S3": 0.9, "Azure Blob Storage": 0.3}
        
        tech_to_remove = validator._choose_technology_to_remove(conflict, context_priority)
        assert tech_to_remove == "Azure Blob Storage"
        
        # Higher priority for Azure
        context_priority = {"AWS S3": 0.3, "Azure Blob Storage": 0.9}
        
        tech_to_remove = validator._choose_technology_to_remove(conflict, context_priority)
        assert tech_to_remove == "AWS S3"
    
    def test_validation_report_serialization(self, validator):
        """Test validation report serialization to dictionary."""
        tech_stack = ["FastAPI", "PostgreSQL"]
        
        report = validator.validate_tech_stack(tech_stack)
        report_dict = report.to_dict()
        
        assert isinstance(report_dict, dict)
        assert "original_tech_stack" in report_dict
        assert "validated_tech_stack" in report_dict
        assert "compatibility_result" in report_dict
        assert "validation_timestamp" in report_dict
        assert "summary" in report_dict
        
        # Check summary structure
        summary = report_dict["summary"]
        assert "original_count" in summary
        assert "validated_count" in summary
        assert "overall_compatibility_score" in summary
    
    @patch('builtins.open')
    @patch('json.dump')
    def test_save_compatibility_data(self, mock_json_dump, mock_open, validator):
        """Test saving compatibility data to file."""
        # Add some test data
        validator.add_compatibility_rule("FastAPI", "Django", 0.3, "Framework conflict")
        
        validator.save_compatibility_data()
        
        mock_open.assert_called_once()
        mock_json_dump.assert_called_once()
        
        # Check the data structure passed to json.dump
        call_args = mock_json_dump.call_args[0]
        data = call_args[0]
        
        assert "matrices" in data
        assert "ecosystem_rules" in data
        assert "conflict_rules" in data
        assert "last_updated" in data
    
    def test_ecosystem_consistency_with_tolerance(self, validator):
        """Test ecosystem consistency with tolerance thresholds."""
        # Mixed stack with AWS majority
        tech_stack = ["AWS S3", "AWS Lambda", "FastAPI"]  # 2 AWS, 1 open source
        
        result = validator.check_ecosystem_consistency(tech_stack)
        
        # With default 80% threshold, 2/3 (66.7%) is below threshold, so not consistent
        assert not result.is_consistent  # 66.7% < 80% threshold
        assert result.primary_ecosystem == EcosystemType.AWS
        assert len(result.recommendations) > 0
    
    def test_critical_conflict_handling(self, validator):
        """Test handling of critical conflicts."""
        tech_stack = ["TechA", "TechB"]
        
        # Create a critical conflict
        critical_conflict = TechnologyConflict(
            tech1="TechA",
            tech2="TechB",
            conflict_type=ConflictType.SECURITY_CONFLICT,
            severity=ConflictSeverity.CRITICAL,
            description="Critical security conflict",
            explanation="These technologies cannot coexist"
        )
        
        context_priority = {"TechA": 0.8, "TechB": 0.6}
        
        validated, removed = validator._resolve_conflicts(tech_stack, [critical_conflict], context_priority)
        
        # Critical conflicts should always be resolved
        assert len(removed) == 1
        assert "TechB" in removed  # Lower priority should be removed
        assert "TechA" in validated
    
    def test_empty_tech_stack_validation(self, validator):
        """Test validation of empty tech stack."""
        tech_stack = []
        
        report = validator.validate_tech_stack(tech_stack)
        
        assert report.original_tech_stack == []
        assert report.validated_tech_stack == []
        assert report.compatibility_result.is_compatible  # Empty stack is compatible
        assert report.compatibility_result.overall_score >= 0.0