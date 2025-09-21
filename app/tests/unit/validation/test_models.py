"""Unit tests for validation models."""

import pytest
from datetime import datetime

from app.services.validation.models import (
    ConflictType, ConflictSeverity, TechnologyConflict,
    EcosystemConsistencyResult, CompatibilityMatrix, CompatibilityResult,
    ValidationReport
)
from app.services.catalog.models import EcosystemType


class TestValidationModels:
    """Test cases for validation data models."""
    
    def test_technology_conflict_creation(self):
        """Test TechnologyConflict creation and serialization."""
        conflict = TechnologyConflict(
            tech1="AWS S3",
            tech2="Azure Blob Storage",
            conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
            severity=ConflictSeverity.HIGH,
            description="Cloud provider conflict",
            explanation="Multiple cloud providers detected",
            suggested_resolution="Choose a single cloud provider",
            alternatives=["Google Cloud Storage"]
        )
        
        assert conflict.tech1 == "AWS S3"
        assert conflict.tech2 == "Azure Blob Storage"
        assert conflict.conflict_type == ConflictType.ECOSYSTEM_MISMATCH
        assert conflict.severity == ConflictSeverity.HIGH
        assert conflict.description == "Cloud provider conflict"
        assert conflict.explanation == "Multiple cloud providers detected"
        assert conflict.suggested_resolution == "Choose a single cloud provider"
        assert "Google Cloud Storage" in conflict.alternatives
        
        # Test serialization
        conflict_dict = conflict.to_dict()
        assert isinstance(conflict_dict, dict)
        assert conflict_dict["tech1"] == "AWS S3"
        assert conflict_dict["tech2"] == "Azure Blob Storage"
        assert conflict_dict["conflict_type"] == "ecosystem_mismatch"
        assert conflict_dict["severity"] == "high"
    
    def test_ecosystem_consistency_result(self):
        """Test EcosystemConsistencyResult creation and serialization."""
        result = EcosystemConsistencyResult(
            is_consistent=False,
            primary_ecosystem=EcosystemType.AWS,
            ecosystem_distribution={"aws": 2, "azure": 1},
            mixed_ecosystem_technologies=["Azure Blob Storage"],
            recommendations=["Consider standardizing on AWS"]
        )
        
        assert not result.is_consistent
        assert result.primary_ecosystem == EcosystemType.AWS
        assert result.ecosystem_distribution["aws"] == 2
        assert result.ecosystem_distribution["azure"] == 1
        assert "Azure Blob Storage" in result.mixed_ecosystem_technologies
        assert len(result.recommendations) == 1
        
        # Test serialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["is_consistent"] is False
        assert result_dict["primary_ecosystem"] == "aws"
        assert result_dict["ecosystem_distribution"]["aws"] == 2
    
    def test_compatibility_matrix(self):
        """Test CompatibilityMatrix functionality."""
        timestamp = datetime.now()
        
        matrix = CompatibilityMatrix(
            tech1="FastAPI",
            tech2="Django",
            compatibility_score=0.3,
            notes="Both are web frameworks",
            last_updated=timestamp
        )
        
        assert matrix.tech1 == "FastAPI"
        assert matrix.tech2 == "Django"
        assert matrix.compatibility_score == 0.3
        assert matrix.notes == "Both are web frameworks"
        assert matrix.last_updated == timestamp
        
        # Test compatibility checking
        assert not matrix.is_compatible()  # 0.3 < 0.7 (default threshold)
        assert not matrix.is_compatible(threshold=0.5)  # 0.3 < 0.5
        assert matrix.is_compatible(threshold=0.2)  # 0.3 >= 0.2
    
    def test_compatibility_result(self):
        """Test CompatibilityResult functionality."""
        conflicts = [
            TechnologyConflict(
                tech1="AWS S3",
                tech2="Azure Blob Storage",
                conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
                severity=ConflictSeverity.HIGH,
                description="Cloud conflict",
                explanation="Multiple clouds"
            ),
            TechnologyConflict(
                tech1="TechA",
                tech2="TechB",
                conflict_type=ConflictType.SECURITY_CONFLICT,
                severity=ConflictSeverity.CRITICAL,
                description="Security conflict",
                explanation="Security issue"
            )
        ]
        
        ecosystem_result = EcosystemConsistencyResult(
            is_consistent=False,
            primary_ecosystem=EcosystemType.AWS,
            ecosystem_distribution={"aws": 1, "azure": 1},
            mixed_ecosystem_technologies=["Azure Blob Storage"],
            recommendations=[]
        )
        
        result = CompatibilityResult(
            is_compatible=False,
            overall_score=0.6,
            conflicts=conflicts,
            ecosystem_result=ecosystem_result,
            validated_technologies=["AWS S3", "FastAPI"],
            removed_technologies=["Azure Blob Storage"],
            suggestions=["Consider single cloud provider"]
        )
        
        assert not result.is_compatible
        assert result.overall_score == 0.6
        assert len(result.conflicts) == 2
        assert len(result.validated_technologies) == 2
        assert len(result.removed_technologies) == 1
        
        # Test conflict filtering by severity
        high_conflicts = result.get_conflicts_by_severity(ConflictSeverity.HIGH)
        assert len(high_conflicts) == 1
        assert high_conflicts[0].severity == ConflictSeverity.HIGH
        
        critical_conflicts = result.get_conflicts_by_severity(ConflictSeverity.CRITICAL)
        assert len(critical_conflicts) == 1
        assert critical_conflicts[0].severity == ConflictSeverity.CRITICAL
        
        # Test critical conflict detection
        assert result.has_critical_conflicts()
        
        # Test serialization
        result_dict = result.to_dict()
        assert isinstance(result_dict, dict)
        assert result_dict["is_compatible"] is False
        assert result_dict["overall_score"] == 0.6
        assert len(result_dict["conflicts"]) == 2
    
    def test_validation_report(self):
        """Test ValidationReport functionality."""
        timestamp = datetime.now()
        
        compatibility_result = CompatibilityResult(
            is_compatible=True,
            overall_score=0.9,
            conflicts=[],
            ecosystem_result=EcosystemConsistencyResult(
                is_consistent=True,
                primary_ecosystem=EcosystemType.OPEN_SOURCE,
                ecosystem_distribution={"open_source": 3},
                mixed_ecosystem_technologies=[],
                recommendations=[]
            ),
            validated_technologies=["FastAPI", "PostgreSQL", "Redis"],
            removed_technologies=[],
            suggestions=[]
        )
        
        report = ValidationReport(
            original_tech_stack=["FastAPI", "PostgreSQL", "Redis"],
            validated_tech_stack=["FastAPI", "PostgreSQL", "Redis"],
            compatibility_result=compatibility_result,
            validation_timestamp=timestamp,
            context_priority={"FastAPI": 0.9, "PostgreSQL": 0.8, "Redis": 0.7},
            inclusion_explanations={
                "FastAPI": "High priority technology",
                "PostgreSQL": "Database requirement",
                "Redis": "Caching solution"
            },
            exclusion_explanations={},
            alternative_suggestions={}
        )
        
        assert len(report.original_tech_stack) == 3
        assert len(report.validated_tech_stack) == 3
        assert report.compatibility_result.is_compatible
        assert report.validation_timestamp == timestamp
        assert len(report.context_priority) == 3
        
        # Test summary generation
        summary = report.get_summary()
        assert isinstance(summary, dict)
        assert summary["original_count"] == 3
        assert summary["validated_count"] == 3
        assert summary["removed_count"] == 0
        assert summary["conflicts_count"] == 0
        assert summary["critical_conflicts"] == 0
        assert summary["overall_compatibility_score"] == 0.9
        assert summary["ecosystem_consistent"] is True
        
        # Test full serialization
        report_dict = report.to_dict()
        assert isinstance(report_dict, dict)
        assert "original_tech_stack" in report_dict
        assert "validated_tech_stack" in report_dict
        assert "compatibility_result" in report_dict
        assert "validation_timestamp" in report_dict
        assert "context_priority" in report_dict
        assert "inclusion_explanations" in report_dict
        assert "exclusion_explanations" in report_dict
        assert "alternative_suggestions" in report_dict
        assert "summary" in report_dict
    
    def test_conflict_type_enum(self):
        """Test ConflictType enum values."""
        assert ConflictType.ECOSYSTEM_MISMATCH.value == "ecosystem_mismatch"
        assert ConflictType.LICENSE_INCOMPATIBILITY.value == "license_incompatibility"
        assert ConflictType.VERSION_CONFLICT.value == "version_conflict"
        assert ConflictType.ARCHITECTURE_MISMATCH.value == "architecture_mismatch"
        assert ConflictType.PERFORMANCE_CONFLICT.value == "performance_conflict"
        assert ConflictType.SECURITY_CONFLICT.value == "security_conflict"
        assert ConflictType.DEPLOYMENT_CONFLICT.value == "deployment_conflict"
        assert ConflictType.INTEGRATION_CONFLICT.value == "integration_conflict"
    
    def test_conflict_severity_enum(self):
        """Test ConflictSeverity enum values."""
        assert ConflictSeverity.CRITICAL.value == "critical"
        assert ConflictSeverity.HIGH.value == "high"
        assert ConflictSeverity.MEDIUM.value == "medium"
        assert ConflictSeverity.LOW.value == "low"
        assert ConflictSeverity.INFO.value == "info"
    
    def test_compatibility_result_no_conflicts(self):
        """Test CompatibilityResult with no conflicts."""
        ecosystem_result = EcosystemConsistencyResult(
            is_consistent=True,
            primary_ecosystem=EcosystemType.OPEN_SOURCE,
            ecosystem_distribution={"open_source": 2},
            mixed_ecosystem_technologies=[],
            recommendations=[]
        )
        
        result = CompatibilityResult(
            is_compatible=True,
            overall_score=1.0,
            conflicts=[],
            ecosystem_result=ecosystem_result,
            validated_technologies=["FastAPI", "PostgreSQL"],
            removed_technologies=[],
            suggestions=[]
        )
        
        assert result.is_compatible
        assert result.overall_score == 1.0
        assert len(result.conflicts) == 0
        assert not result.has_critical_conflicts()
        
        # Test getting conflicts by severity (should return empty lists)
        for severity in ConflictSeverity:
            conflicts = result.get_conflicts_by_severity(severity)
            assert len(conflicts) == 0
    
    def test_validation_report_with_removals(self):
        """Test ValidationReport with removed technologies."""
        compatibility_result = CompatibilityResult(
            is_compatible=True,
            overall_score=0.8,
            conflicts=[
                TechnologyConflict(
                    tech1="AWS S3",
                    tech2="Azure Blob Storage",
                    conflict_type=ConflictType.ECOSYSTEM_MISMATCH,
                    severity=ConflictSeverity.HIGH,
                    description="Cloud conflict",
                    explanation="Multiple clouds"
                )
            ],
            ecosystem_result=EcosystemConsistencyResult(
                is_consistent=True,
                primary_ecosystem=EcosystemType.AWS,
                ecosystem_distribution={"aws": 2},
                mixed_ecosystem_technologies=[],
                recommendations=[]
            ),
            validated_technologies=["AWS S3", "FastAPI"],
            removed_technologies=["Azure Blob Storage"],
            suggestions=["Resolved cloud provider conflict"]
        )
        
        report = ValidationReport(
            original_tech_stack=["AWS S3", "Azure Blob Storage", "FastAPI"],
            validated_tech_stack=["AWS S3", "FastAPI"],
            compatibility_result=compatibility_result,
            validation_timestamp=datetime.now(),
            context_priority={"AWS S3": 0.9, "Azure Blob Storage": 0.3, "FastAPI": 0.8},
            inclusion_explanations={
                "AWS S3": "High priority cloud storage",
                "FastAPI": "Web framework requirement"
            },
            exclusion_explanations={
                "Azure Blob Storage": "Removed due to cloud provider conflict"
            },
            alternative_suggestions={
                "Azure Blob Storage": ["AWS S3", "Google Cloud Storage"]
            }
        )
        
        summary = report.get_summary()
        assert summary["original_count"] == 3
        assert summary["validated_count"] == 2
        assert summary["removed_count"] == 1
        assert summary["conflicts_count"] == 1
        assert summary["critical_conflicts"] == 0  # No critical conflicts
        
        assert "Azure Blob Storage" in report.exclusion_explanations
        assert "Azure Blob Storage" in report.alternative_suggestions
        assert len(report.alternative_suggestions["Azure Blob Storage"]) == 2