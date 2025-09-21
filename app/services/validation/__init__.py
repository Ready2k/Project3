"""Technology compatibility validation system."""

from .models import (
    CompatibilityResult,
    ConflictType,
    ConflictSeverity,
    TechnologyConflict,
    EcosystemConsistencyResult,
    ValidationReport
)
from .compatibility_validator import TechnologyCompatibilityValidator

__all__ = [
    'CompatibilityResult',
    'ConflictType', 
    'ConflictSeverity',
    'TechnologyConflict',
    'EcosystemConsistencyResult',
    'ValidationReport',
    'TechnologyCompatibilityValidator'
]