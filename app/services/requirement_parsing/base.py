"""Base classes and interfaces for enhanced requirement parsing."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Dict, List, Any, Optional, Set
from enum import Enum


class ConfidenceLevel(Enum):
    """Confidence levels for technology extraction."""

    HIGH = 1.0  # Explicit mentions
    MEDIUM = 0.8  # Strong context clues
    LOW = 0.6  # Pattern-based inferences
    VERY_LOW = 0.4  # Generic recommendations


class ExtractionMethod(Enum):
    """Methods used for technology extraction."""

    EXPLICIT_MENTION = "explicit_mention"
    NER_EXTRACTION = "ner_extraction"
    PATTERN_MATCHING = "pattern_matching"
    CONTEXT_INFERENCE = "context_inference"
    ALIAS_RESOLUTION = "alias_resolution"
    INTEGRATION_PATTERN = "integration_pattern"


@dataclass
class ExplicitTech:
    """Represents an explicitly mentioned technology with metadata."""

    name: str
    canonical_name: Optional[str] = None
    confidence: float = 1.0
    extraction_method: ExtractionMethod = ExtractionMethod.EXPLICIT_MENTION
    source_text: str = ""
    position: Optional[int] = None
    aliases: List[str] = field(default_factory=list)
    context: str = ""


@dataclass
class ContextClues:
    """Context clues extracted from requirements."""

    cloud_providers: List[str] = field(default_factory=list)
    domains: List[str] = field(default_factory=list)
    integration_patterns: List[str] = field(default_factory=list)
    technology_categories: List[str] = field(default_factory=list)
    programming_languages: List[str] = field(default_factory=list)
    deployment_preferences: List[str] = field(default_factory=list)
    data_patterns: List[str] = field(default_factory=list)


@dataclass
class RequirementConstraints:
    """Constraints extracted from requirements."""

    banned_tools: Set[str] = field(default_factory=set)
    required_integrations: List[str] = field(default_factory=list)
    compliance_requirements: List[str] = field(default_factory=list)
    data_sensitivity: Optional[str] = None
    budget_constraints: Optional[str] = None
    deployment_preference: Optional[str] = None
    performance_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class DomainContext:
    """Domain-specific context information."""

    primary_domain: Optional[str] = None
    sub_domains: List[str] = field(default_factory=list)
    industry: Optional[str] = None
    use_case_patterns: List[str] = field(default_factory=list)
    complexity_indicators: List[str] = field(default_factory=list)


@dataclass
class ParsedRequirements:
    """Complete parsed requirements with all extracted information."""

    explicit_technologies: List[ExplicitTech] = field(default_factory=list)
    context_clues: ContextClues = field(default_factory=ContextClues)
    constraints: RequirementConstraints = field(default_factory=RequirementConstraints)
    domain_context: DomainContext = field(default_factory=DomainContext)
    raw_text: str = ""
    confidence_score: float = 0.0
    extraction_metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class TechContext:
    """Technology context for LLM generation."""

    explicit_technologies: Dict[str, float] = field(
        default_factory=dict
    )  # tech_name -> confidence
    contextual_technologies: Dict[str, float] = field(default_factory=dict)
    domain_context: DomainContext = field(default_factory=DomainContext)
    ecosystem_preference: Optional[str] = None  # aws, azure, gcp
    integration_requirements: List[str] = field(default_factory=list)
    banned_tools: Set[str] = field(default_factory=set)
    priority_weights: Dict[str, float] = field(default_factory=dict)


class RequirementParser(ABC):
    """Abstract base class for requirement parsers."""

    @abstractmethod
    def parse_requirements(self, requirements: Dict[str, Any]) -> ParsedRequirements:
        """Parse requirements to extract technology context and constraints.

        Args:
            requirements: Raw requirements dictionary

        Returns:
            ParsedRequirements object with extracted information
        """
        pass

    @abstractmethod
    def extract_explicit_technologies(self, text: str) -> List[ExplicitTech]:
        """Extract explicitly mentioned technologies from text.

        Args:
            text: Text to analyze

        Returns:
            List of explicitly mentioned technologies with confidence scores
        """
        pass

    @abstractmethod
    def identify_context_clues(self, text: str) -> ContextClues:
        """Identify context clues from text.

        Args:
            text: Text to analyze

        Returns:
            ContextClues object with identified patterns
        """
        pass

    @abstractmethod
    def extract_constraints(
        self, requirements: Dict[str, Any]
    ) -> RequirementConstraints:
        """Extract constraints from requirements.

        Args:
            requirements: Requirements dictionary

        Returns:
            RequirementConstraints object
        """
        pass

    @abstractmethod
    def calculate_confidence(self, parsed_req: ParsedRequirements) -> float:
        """Calculate overall confidence score for parsed requirements.

        Args:
            parsed_req: Parsed requirements

        Returns:
            Overall confidence score (0.0 to 1.0)
        """
        pass


class TechnologyExtractor(ABC):
    """Abstract base class for technology extraction."""

    @abstractmethod
    def extract_technologies(self, text: str) -> List[ExplicitTech]:
        """Extract technologies from text using various methods.

        Args:
            text: Text to analyze

        Returns:
            List of extracted technologies with metadata
        """
        pass

    @abstractmethod
    def resolve_aliases(self, tech_name: str) -> Optional[str]:
        """Resolve technology aliases to canonical names.

        Args:
            tech_name: Technology name to resolve

        Returns:
            Canonical name if found, None otherwise
        """
        pass

    @abstractmethod
    def calculate_extraction_confidence(
        self, tech: str, method: ExtractionMethod, context: str
    ) -> float:
        """Calculate confidence score for extracted technology.

        Args:
            tech: Technology name
            method: Extraction method used
            context: Surrounding context

        Returns:
            Confidence score (0.0 to 1.0)
        """
        pass


class ContextExtractor(ABC):
    """Abstract base class for context extraction."""

    @abstractmethod
    def build_context(self, parsed_req: ParsedRequirements) -> TechContext:
        """Build comprehensive technology context from parsed requirements.

        Args:
            parsed_req: Parsed requirements

        Returns:
            TechContext object with prioritized technologies
        """
        pass

    @abstractmethod
    def prioritize_technologies(self, context: TechContext) -> Dict[str, float]:
        """Prioritize technologies based on context and explicit mentions.

        Args:
            context: Technology context

        Returns:
            Dictionary mapping technology names to priority scores
        """
        pass

    @abstractmethod
    def infer_ecosystem_preference(self, context_clues: ContextClues) -> Optional[str]:
        """Infer ecosystem preference from context clues.

        Args:
            context_clues: Context clues from requirements

        Returns:
            Preferred ecosystem (aws, azure, gcp) or None
        """
        pass
