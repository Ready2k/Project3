"""Data models for technology compatibility validation."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Set, Any, Tuple
from enum import Enum
from datetime import datetime

from ..catalog.models import TechEntry, EcosystemType


class ConflictType(Enum):
    """Types of technology conflicts."""
    ECOSYSTEM_MISMATCH = "ecosystem_mismatch"
    LICENSE_INCOMPATIBILITY = "license_incompatibility"
    VERSION_CONFLICT = "version_conflict"
    ARCHITECTURE_MISMATCH = "architecture_mismatch"
    PERFORMANCE_CONFLICT = "performance_conflict"
    SECURITY_CONFLICT = "security_conflict"
    DEPLOYMENT_CONFLICT = "deployment_conflict"
    INTEGRATION_CONFLICT = "integration_conflict"


class ConflictSeverity(Enum):
    """Severity levels for conflicts."""
    CRITICAL = "critical"  # Prevents system from working
    HIGH = "high"         # Major issues, should be resolved
    MEDIUM = "medium"     # Potential issues, consider alternatives
    LOW = "low"          # Minor concerns, can be ignored
    INFO = "info"        # Informational, no action needed


@dataclass
class TechnologyConflict:
    """Represents a conflict between technologies."""
    
    tech1: str  # First technology name
    tech2: str  # Second technology name
    conflict_type: ConflictType
    severity: ConflictSeverity
    description: str
    explanation: str
    suggested_resolution: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "tech1": self.tech1,
            "tech2": self.tech2,
            "conflict_type": self.conflict_type.value,
            "severity": self.severity.value,
            "description": self.description,
            "explanation": self.explanation,
            "suggested_resolution": self.suggested_resolution,
            "alternatives": self.alternatives
        }


@dataclass
class EcosystemConsistencyResult:
    """Result of ecosystem consistency checking."""
    
    is_consistent: bool
    primary_ecosystem: Optional[EcosystemType]
    ecosystem_distribution: Dict[str, int]  # ecosystem -> count
    mixed_ecosystem_technologies: List[str]  # Technologies from different ecosystems
    recommendations: List[str]
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_consistent": self.is_consistent,
            "primary_ecosystem": self.primary_ecosystem.value if self.primary_ecosystem else None,
            "ecosystem_distribution": self.ecosystem_distribution,
            "mixed_ecosystem_technologies": self.mixed_ecosystem_technologies,
            "recommendations": self.recommendations
        }


@dataclass
class CompatibilityMatrix:
    """Technology compatibility matrix entry."""
    
    tech1: str
    tech2: str
    compatibility_score: float  # 0.0 (incompatible) to 1.0 (fully compatible)
    notes: Optional[str] = None
    last_updated: Optional[datetime] = None
    
    def is_compatible(self, threshold: float = 0.7) -> bool:
        """Check if technologies are compatible above threshold."""
        return self.compatibility_score >= threshold


@dataclass
class CompatibilityResult:
    """Result of technology compatibility validation."""
    
    is_compatible: bool
    overall_score: float  # 0.0 to 1.0
    conflicts: List[TechnologyConflict]
    ecosystem_result: EcosystemConsistencyResult
    validated_technologies: List[str]
    removed_technologies: List[str]  # Technologies removed due to conflicts
    suggestions: List[str]
    
    def get_conflicts_by_severity(self, severity: ConflictSeverity) -> List[TechnologyConflict]:
        """Get conflicts of specific severity."""
        return [c for c in self.conflicts if c.severity == severity]
    
    def has_critical_conflicts(self) -> bool:
        """Check if there are any critical conflicts."""
        return any(c.severity == ConflictSeverity.CRITICAL for c in self.conflicts)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "is_compatible": self.is_compatible,
            "overall_score": self.overall_score,
            "conflicts": [c.to_dict() for c in self.conflicts],
            "ecosystem_result": self.ecosystem_result.to_dict(),
            "validated_technologies": self.validated_technologies,
            "removed_technologies": self.removed_technologies,
            "suggestions": self.suggestions
        }


@dataclass
class ValidationReport:
    """Comprehensive validation report with explanations and alternatives."""
    
    original_tech_stack: List[str]
    validated_tech_stack: List[str]
    compatibility_result: CompatibilityResult
    validation_timestamp: datetime
    context_priority: Dict[str, float]  # tech -> priority score
    
    # Detailed explanations
    inclusion_explanations: Dict[str, str]  # tech -> why included
    exclusion_explanations: Dict[str, str]  # tech -> why excluded
    alternative_suggestions: Dict[str, List[str]]  # excluded_tech -> alternatives
    
    def get_summary(self) -> Dict[str, Any]:
        """Get a summary of the validation results."""
        return {
            "original_count": len(self.original_tech_stack),
            "validated_count": len(self.validated_tech_stack),
            "removed_count": len(self.compatibility_result.removed_technologies),
            "conflicts_count": len(self.compatibility_result.conflicts),
            "critical_conflicts": len(self.compatibility_result.get_conflicts_by_severity(ConflictSeverity.CRITICAL)),
            "overall_compatibility_score": self.compatibility_result.overall_score,
            "ecosystem_consistent": self.compatibility_result.ecosystem_result.is_consistent,
            "validation_timestamp": self.validation_timestamp.isoformat()
        }
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "original_tech_stack": self.original_tech_stack,
            "validated_tech_stack": self.validated_tech_stack,
            "compatibility_result": self.compatibility_result.to_dict(),
            "validation_timestamp": self.validation_timestamp.isoformat(),
            "context_priority": self.context_priority,
            "inclusion_explanations": self.inclusion_explanations,
            "exclusion_explanations": self.exclusion_explanations,
            "alternative_suggestions": self.alternative_suggestions,
            "summary": self.get_summary()
        }