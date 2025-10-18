"""Enhanced data models for technology catalog management."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any
from datetime import datetime
from enum import Enum


class EcosystemType(Enum):
    """Technology ecosystem types."""

    AWS = "aws"
    AZURE = "azure"
    GCP = "gcp"
    OPEN_SOURCE = "open_source"
    PROPRIETARY = "proprietary"
    HYBRID = "hybrid"


class MaturityLevel(Enum):
    """Technology maturity levels."""

    EXPERIMENTAL = "experimental"
    BETA = "beta"
    STABLE = "stable"
    MATURE = "mature"
    DEPRECATED = "deprecated"


class ReviewStatus(Enum):
    """Review status for auto-generated entries."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_UPDATE = "needs_update"


@dataclass
class TechEntry:
    """Enhanced technology entry with intelligent management fields."""

    # Core identification
    id: str
    name: str
    canonical_name: str

    # Basic metadata
    category: str
    description: str

    # Enhanced fields for intelligent management
    aliases: List[str] = field(default_factory=list)
    ecosystem: Optional[EcosystemType] = None
    confidence_score: float = 1.0  # 0.0-1.0, confidence in entry accuracy
    pending_review: bool = False

    # Existing fields (enhanced)
    integrates_with: List[str] = field(default_factory=list)
    alternatives: List[str] = field(default_factory=list)
    tags: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)

    # Metadata
    license: str = "unknown"
    maturity: MaturityLevel = MaturityLevel.STABLE

    # Auto-generation tracking
    auto_generated: bool = False
    source_context: Optional[str] = None  # Context where technology was first mentioned
    added_date: Optional[datetime] = None
    last_updated: Optional[datetime] = None

    # Review workflow
    review_status: ReviewStatus = ReviewStatus.APPROVED
    review_notes: Optional[str] = None
    reviewed_by: Optional[str] = None
    reviewed_date: Optional[datetime] = None

    # Usage tracking
    mention_count: int = 0  # How often this tech is mentioned in requirements
    selection_count: int = 0  # How often this tech is selected in final stacks

    # Validation metadata
    validation_errors: List[str] = field(default_factory=list)
    last_validated: Optional[datetime] = None

    def __post_init__(self):
        """Post-initialization processing."""
        if not self.canonical_name:
            self.canonical_name = self.name

        if self.added_date is None:
            self.added_date = datetime.now()

        if self.auto_generated and not self.pending_review:
            self.pending_review = True
            self.review_status = ReviewStatus.PENDING

    def add_alias(self, alias: str) -> None:
        """Add an alias if not already present."""
        if alias not in self.aliases and alias != self.name:
            self.aliases.append(alias)

    def increment_mention(self) -> None:
        """Increment mention count."""
        self.mention_count += 1

    def increment_selection(self) -> None:
        """Increment selection count."""
        self.selection_count += 1

    def add_validation_error(self, error: str) -> None:
        """Add a validation error."""
        if error not in self.validation_errors:
            self.validation_errors.append(error)

    def clear_validation_errors(self) -> None:
        """Clear all validation errors."""
        self.validation_errors.clear()
        self.last_validated = datetime.now()

    def approve_review(self, reviewer: str, notes: Optional[str] = None) -> None:
        """Approve the technology entry."""
        self.review_status = ReviewStatus.APPROVED
        self.pending_review = False
        self.reviewed_by = reviewer
        self.reviewed_date = datetime.now()
        self.review_notes = notes
        self.last_updated = datetime.now()

    def reject_review(self, reviewer: str, notes: str) -> None:
        """Reject the technology entry."""
        self.review_status = ReviewStatus.REJECTED
        self.pending_review = False
        self.reviewed_by = reviewer
        self.reviewed_date = datetime.now()
        self.review_notes = notes

    def request_update(self, reviewer: str, notes: str) -> None:
        """Request updates to the technology entry."""
        self.review_status = ReviewStatus.NEEDS_UPDATE
        self.pending_review = True
        self.reviewed_by = reviewer
        self.reviewed_date = datetime.now()
        self.review_notes = notes

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization."""
        return {
            "id": self.id,
            "name": self.name,
            "canonical_name": self.canonical_name,
            "category": self.category,
            "description": self.description,
            "aliases": self.aliases,
            "ecosystem": self.ecosystem.value if self.ecosystem else None,
            "confidence_score": self.confidence_score,
            "pending_review": self.pending_review,
            "integrates_with": self.integrates_with,
            "alternatives": self.alternatives,
            "tags": self.tags,
            "use_cases": self.use_cases,
            "license": self.license,
            "maturity": self.maturity.value,
            "auto_generated": self.auto_generated,
            "source_context": self.source_context,
            "added_date": self.added_date.isoformat() if self.added_date else None,
            "last_updated": (
                self.last_updated.isoformat() if self.last_updated else None
            ),
            "review_status": self.review_status.value,
            "review_notes": self.review_notes,
            "reviewed_by": self.reviewed_by,
            "reviewed_date": (
                self.reviewed_date.isoformat() if self.reviewed_date else None
            ),
            "mention_count": self.mention_count,
            "selection_count": self.selection_count,
            "validation_errors": self.validation_errors,
            "last_validated": (
                self.last_validated.isoformat() if self.last_validated else None
            ),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "TechEntry":
        """Create TechEntry from dictionary."""
        # Handle datetime fields
        added_date = None
        if data.get("added_date"):
            added_date = datetime.fromisoformat(data["added_date"])

        last_updated = None
        if data.get("last_updated"):
            last_updated = datetime.fromisoformat(data["last_updated"])

        reviewed_date = None
        if data.get("reviewed_date"):
            reviewed_date = datetime.fromisoformat(data["reviewed_date"])

        last_validated = None
        if data.get("last_validated"):
            last_validated = datetime.fromisoformat(data["last_validated"])

        # Handle enum fields
        ecosystem = None
        if data.get("ecosystem"):
            ecosystem = EcosystemType(data["ecosystem"])

        maturity = MaturityLevel.STABLE
        if data.get("maturity"):
            maturity = MaturityLevel(data["maturity"])

        review_status = ReviewStatus.APPROVED
        if data.get("review_status"):
            review_status = ReviewStatus(data["review_status"])

        return cls(
            id=data["id"],
            name=data["name"],
            canonical_name=data.get("canonical_name", data["name"]),
            category=data["category"],
            description=data["description"],
            aliases=data.get("aliases", []),
            ecosystem=ecosystem,
            confidence_score=data.get("confidence_score", 1.0),
            pending_review=data.get("pending_review", False),
            integrates_with=data.get("integrates_with", []),
            alternatives=data.get("alternatives", []),
            tags=data.get("tags", []),
            use_cases=data.get("use_cases", []),
            license=data.get("license", "unknown"),
            maturity=maturity,
            auto_generated=data.get("auto_generated", False),
            source_context=data.get("source_context"),
            added_date=added_date,
            last_updated=last_updated,
            review_status=review_status,
            review_notes=data.get("review_notes"),
            reviewed_by=data.get("reviewed_by"),
            reviewed_date=reviewed_date,
            mention_count=data.get("mention_count", 0),
            selection_count=data.get("selection_count", 0),
            validation_errors=data.get("validation_errors", []),
            last_validated=last_validated,
        )


@dataclass
class ValidationResult:
    """Result of catalog validation."""

    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)


@dataclass
class FuzzyMatchResult:
    """Result of fuzzy matching operation."""

    tech_entry: TechEntry
    match_score: float  # 0.0-1.0
    match_type: str  # "exact", "alias", "fuzzy_name", "fuzzy_alias"
    matched_text: str  # The text that matched


@dataclass
class CatalogStats:
    """Statistics about the technology catalog."""

    total_entries: int
    pending_review: int
    auto_generated: int
    by_ecosystem: Dict[str, int] = field(default_factory=dict)
    by_category: Dict[str, int] = field(default_factory=dict)
    by_maturity: Dict[str, int] = field(default_factory=dict)
    validation_errors: int = 0
    last_updated: Optional[datetime] = None
