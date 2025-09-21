"""Requirement context prioritization logic for technology selection."""

from typing import Dict, List, Optional, Set, Tuple, Any
from dataclasses import dataclass, field
from enum import Enum
import re
from collections import defaultdict

from .base import (
    ParsedRequirements, TechContext, ContextClues, DomainContext,
    ExplicitTech, RequirementConstraints
)
from app.utils.imports import require_service


class RequirementSource(Enum):
    """Sources of requirements with different priority levels."""
    EXPLICIT_USER_INPUT = "explicit_user_input"  # Highest priority
    BUSINESS_REQUIREMENTS = "business_requirements"
    TECHNICAL_SPECIFICATIONS = "technical_specifications"
    PATTERN_INFERENCE = "pattern_inference"
    SYSTEM_DEFAULTS = "system_defaults"  # Lowest priority


class ContextPriority(Enum):
    """Priority levels for context elements."""
    CRITICAL = 1.0      # Must be included
    HIGH = 0.9          # Strong preference
    MEDIUM = 0.7        # Moderate preference
    LOW = 0.5           # Weak preference
    MINIMAL = 0.3       # Fallback option


class AmbiguityType(Enum):
    """Types of requirement ambiguity."""
    TECHNOLOGY_CONFLICT = "technology_conflict"
    ECOSYSTEM_MISMATCH = "ecosystem_mismatch"
    INCOMPLETE_SPECIFICATION = "incomplete_specification"
    CONTRADICTORY_REQUIREMENTS = "contradictory_requirements"
    UNCLEAR_DOMAIN = "unclear_domain"


@dataclass
class RequirementWeight:
    """Weight configuration for different requirement sources."""
    source: RequirementSource
    base_weight: float
    domain_multiplier: float = 1.0
    confidence_threshold: float = 0.5
    decay_factor: float = 1.0  # For learning adaptation


@dataclass
class ContextWeight:
    """Weight calculation for technology context."""
    technology: str
    base_priority: float
    source_weights: Dict[RequirementSource, float] = field(default_factory=dict)
    domain_boost: float = 0.0
    ecosystem_boost: float = 0.0
    user_preference_boost: float = 0.0
    final_weight: float = 0.0
    reasoning: List[str] = field(default_factory=list)


@dataclass
class AmbiguityDetection:
    """Detected ambiguity in requirements."""
    ambiguity_type: AmbiguityType
    description: str
    conflicting_elements: List[str]
    suggested_clarifications: List[str]
    confidence: float
    impact_level: str  # "high", "medium", "low"


@dataclass
class UserPreference:
    """User preference learning data."""
    technology: str
    domain: str
    selection_count: int = 0
    rejection_count: int = 0
    preference_score: float = 0.0
    last_updated: Optional[str] = None
    context_patterns: List[str] = field(default_factory=list)


class RequirementContextPrioritizer:
    """Implements requirement context prioritization logic."""
    
    def __init__(self):
        """Initialize the context prioritizer."""
        try:
            self.logger = require_service('logger', context='RequirementContextPrioritizer')
        except Exception:
            import logging
            self.logger = logging.getLogger('RequirementContextPrioritizer')
        
        self._init_weight_configurations()
        self._init_domain_preferences()
        self._init_ambiguity_patterns()
        self.user_preferences: Dict[str, UserPreference] = {}
        
    def _init_weight_configurations(self) -> None:
        """Initialize weight configurations for different requirement sources."""
        self.source_weights = {
            RequirementSource.EXPLICIT_USER_INPUT: RequirementWeight(
                source=RequirementSource.EXPLICIT_USER_INPUT,
                base_weight=1.0,
                domain_multiplier=1.2,
                confidence_threshold=0.9
            ),
            RequirementSource.BUSINESS_REQUIREMENTS: RequirementWeight(
                source=RequirementSource.BUSINESS_REQUIREMENTS,
                base_weight=0.8,
                domain_multiplier=1.1,
                confidence_threshold=0.7
            ),
            RequirementSource.TECHNICAL_SPECIFICATIONS: RequirementWeight(
                source=RequirementSource.TECHNICAL_SPECIFICATIONS,
                base_weight=0.7,
                domain_multiplier=1.0,
                confidence_threshold=0.6
            ),
            RequirementSource.PATTERN_INFERENCE: RequirementWeight(
                source=RequirementSource.PATTERN_INFERENCE,
                base_weight=0.5,
                domain_multiplier=0.9,
                confidence_threshold=0.5
            ),
            RequirementSource.SYSTEM_DEFAULTS: RequirementWeight(
                source=RequirementSource.SYSTEM_DEFAULTS,
                base_weight=0.3,
                domain_multiplier=0.8,
                confidence_threshold=0.4
            )
        }
    
    def _init_domain_preferences(self) -> None:
        """Initialize domain-specific technology preferences."""
        self.domain_tech_preferences = {
            'data_processing': {
                'critical': ['Apache Spark', 'Apache Kafka', 'Pandas'],
                'high': ['NumPy', 'Elasticsearch', 'Redis'],
                'medium': ['PostgreSQL', 'MongoDB'],
                'ecosystems': ['aws', 'gcp']
            },
            'web_api': {
                'critical': ['FastAPI', 'Express.js', 'Spring Boot'],
                'high': ['Nginx', 'Redis', 'PostgreSQL'],
                'medium': ['Docker', 'Kubernetes'],
                'ecosystems': ['aws', 'azure', 'gcp']
            },
            'ml_ai': {
                'critical': ['OpenAI API', 'Hugging Face Transformers', 'LangChain'],
                'high': ['PyTorch', 'TensorFlow', 'Pandas'],
                'medium': ['NumPy', 'Scikit-learn', 'FAISS'],
                'ecosystems': ['aws', 'gcp']
            },
            'automation': {
                'critical': ['Celery', 'Apache Kafka', 'RabbitMQ'],
                'high': ['Redis', 'PostgreSQL', 'Docker'],
                'medium': ['Jenkins', 'Kubernetes'],
                'ecosystems': ['aws', 'azure']
            },
            'monitoring': {
                'critical': ['Prometheus', 'Grafana', 'Jaeger'],
                'high': ['Elasticsearch', 'InfluxDB'],
                'medium': ['Redis', 'Docker'],
                'ecosystems': ['aws', 'gcp']
            },
            'security': {
                'critical': ['HashiCorp Vault', 'OAuth 2.0', 'JWT'],
                'high': ['Redis', 'PostgreSQL'],
                'medium': ['Docker', 'Nginx'],
                'ecosystems': ['aws', 'azure']
            }
        }
    
    def _init_ambiguity_patterns(self) -> None:
        """Initialize patterns for detecting requirement ambiguity."""
        self.ambiguity_patterns = {
            AmbiguityType.TECHNOLOGY_CONFLICT: [
                r'(?i)(both|either|or)\s+(\w+)\s+(and|or)\s+(\w+)',
                r'(?i)(prefer|want|need)\s+(\w+)\s+but\s+(also|alternatively)\s+(\w+)',
                r'(?i)(mysql|postgresql)\s+and\s+(mongodb|nosql)',
                r'(?i)(aws|azure|gcp)\s+and\s+(aws|azure|gcp)'
            ],
            AmbiguityType.ECOSYSTEM_MISMATCH: [
                r'(?i)(aws\s+\w+)\s+.*(azure|gcp)',
                r'(?i)(azure\s+\w+)\s+.*(aws|gcp)',
                r'(?i)(gcp\s+\w+)\s+.*(aws|azure)',
                r'(?i)(lambda|s3|dynamodb)\s+.*(azure|gcp)',
                r'(?i)(app\s+service|cosmos\s+db)\s+.*(aws|gcp)'
            ],
            AmbiguityType.INCOMPLETE_SPECIFICATION: [
                r'(?i)(database|storage|cache)\s+(?![\w\-]+)',
                r'(?i)(api|service|application)\s+(?![\w\-]+)',
                r'(?i)(monitoring|logging|security)\s+(?![\w\-]+)',
                r'(?i)(need|want|require)\s+(some|a|an)\s+(\w+)',
                r'(?i)(maybe|possibly|might|could)\s+(use|need|want)'
            ],
            AmbiguityType.CONTRADICTORY_REQUIREMENTS: [
                r'(?i)(simple|lightweight)\s+.*(enterprise|scalable|distributed)',
                r'(?i)(fast|quick)\s+.*(comprehensive|detailed|thorough)',
                r'(?i)(minimal|basic)\s+.*(advanced|complex|sophisticated)',
                r'(?i)(serverless)\s+.*(kubernetes|docker|container)'
            ],
            AmbiguityType.UNCLEAR_DOMAIN: [
                r'(?i)(general|generic|basic|simple)\s+(application|system|solution)',
                r'(?i)(various|multiple|different)\s+(use\s+cases|scenarios|requirements)',
                r'(?i)(flexible|adaptable|configurable)\s+(architecture|design|system)'
            ]
        }
    
    def calculate_context_weights(self, 
                                parsed_req: ParsedRequirements,
                                tech_context: TechContext) -> Dict[str, ContextWeight]:
        """Calculate context weights for different requirement sources.
        
        Args:
            parsed_req: Parsed requirements
            tech_context: Technology context
            
        Returns:
            Dictionary mapping technologies to their context weights
        """
        self.logger.info("Calculating context weights for technology prioritization")
        
        context_weights = {}
        
        # Process explicit technologies
        for tech in parsed_req.explicit_technologies:
            weight = self._calculate_technology_weight(
                tech.name, 
                RequirementSource.EXPLICIT_USER_INPUT,
                parsed_req.domain_context,
                tech_context,
                tech.confidence
            )
            context_weights[tech.name] = weight
        
        # Process contextual technologies
        for tech, confidence in tech_context.contextual_technologies.items():
            if tech not in context_weights:
                weight = self._calculate_technology_weight(
                    tech,
                    RequirementSource.PATTERN_INFERENCE,
                    parsed_req.domain_context,
                    tech_context,
                    confidence
                )
                context_weights[tech] = weight
        
        # Apply domain-specific preferences
        self._apply_domain_preferences(context_weights, parsed_req.domain_context)
        
        # Apply ecosystem consistency boosts
        self._apply_ecosystem_consistency(context_weights, tech_context)
        
        # Apply user preference learning
        self._apply_user_preferences(context_weights, parsed_req.domain_context)
        
        # Calculate final weights
        for tech, weight in context_weights.items():
            weight.final_weight = self._calculate_final_weight(weight)
        
        self.logger.info(f"Calculated context weights for {len(context_weights)} technologies")
        return context_weights
    
    def _calculate_technology_weight(self,
                                   technology: str,
                                   source: RequirementSource,
                                   domain_context: DomainContext,
                                   tech_context: TechContext,
                                   confidence: float) -> ContextWeight:
        """Calculate weight for a specific technology.
        
        Args:
            technology: Technology name
            source: Requirement source
            domain_context: Domain context
            tech_context: Technology context
            confidence: Confidence score
            
        Returns:
            ContextWeight object
        """
        source_config = self.source_weights[source]
        base_priority = source_config.base_weight * confidence
        
        weight = ContextWeight(
            technology=technology,
            base_priority=base_priority,
            source_weights={source: base_priority}
        )
        
        # Add reasoning
        weight.reasoning.append(f"Base priority from {source.value}: {base_priority:.2f}")
        
        return weight
    
    def _apply_domain_preferences(self, 
                                context_weights: Dict[str, ContextWeight],
                                domain_context: DomainContext) -> None:
        """Apply domain-specific technology preferences.
        
        Args:
            context_weights: Context weights to modify
            domain_context: Domain context information
        """
        if not domain_context.primary_domain:
            return
        
        domain_prefs = self.domain_tech_preferences.get(domain_context.primary_domain, {})
        
        for tech, weight in context_weights.items():
            boost = 0.0
            
            if tech in domain_prefs.get('critical', []):
                boost = 0.3
                weight.reasoning.append(f"Critical technology for {domain_context.primary_domain} domain: +{boost}")
            elif tech in domain_prefs.get('high', []):
                boost = 0.2
                weight.reasoning.append(f"High priority for {domain_context.primary_domain} domain: +{boost}")
            elif tech in domain_prefs.get('medium', []):
                boost = 0.1
                weight.reasoning.append(f"Medium priority for {domain_context.primary_domain} domain: +{boost}")
            
            weight.domain_boost = boost
    
    def _apply_ecosystem_consistency(self,
                                   context_weights: Dict[str, ContextWeight],
                                   tech_context: TechContext) -> None:
        """Apply ecosystem consistency boosts.
        
        Args:
            context_weights: Context weights to modify
            tech_context: Technology context
        """
        if not tech_context.ecosystem_preference:
            return
        
        # Define ecosystem mappings
        ecosystem_mappings = {
            'aws': {
                'Amazon Connect', 'Amazon Connect SDK', 'AWS Lambda', 'Amazon S3',
                'AWS Comprehend', 'AWS Bedrock', 'Amazon DynamoDB', 'Amazon RDS',
                'Amazon EC2', 'Amazon ECS', 'Amazon EKS', 'Amazon CloudWatch',
                'Amazon SNS', 'Amazon SQS', 'AWS API Gateway', 'AWS Step Functions'
            },
            'azure': {
                'Azure Cognitive Services', 'Azure App Service', 'Azure Functions',
                'Azure Cosmos DB', 'Azure SQL Database', 'Azure Storage Account',
                'Azure Service Bus', 'Azure Event Grid', 'Azure Monitor',
                'Azure Key Vault', 'Azure Active Directory'
            },
            'gcp': {
                'Google Cloud Functions', 'Google Cloud Run', 'Google BigQuery',
                'Google Firestore', 'Google Cloud Storage', 'Google Pub/Sub',
                'Google Kubernetes Engine'
            }
        }
        
        ecosystem_techs = ecosystem_mappings.get(tech_context.ecosystem_preference, set())
        
        for tech, weight in context_weights.items():
            if tech in ecosystem_techs:
                boost = 0.15
                weight.ecosystem_boost = boost
                weight.reasoning.append(f"Ecosystem consistency boost for {tech_context.ecosystem_preference}: +{boost}")
    
    def _apply_user_preferences(self,
                              context_weights: Dict[str, ContextWeight],
                              domain_context: DomainContext) -> None:
        """Apply user preference learning.
        
        Args:
            context_weights: Context weights to modify
            domain_context: Domain context
        """
        domain = domain_context.primary_domain or "general"
        
        for tech, weight in context_weights.items():
            pref_key = f"{domain}:{tech}"
            if pref_key in self.user_preferences:
                pref = self.user_preferences[pref_key]
                boost = pref.preference_score * 0.1  # Scale preference impact
                weight.user_preference_boost = boost
                weight.reasoning.append(f"User preference learning boost: +{boost:.2f}")
    
    def _calculate_final_weight(self, weight: ContextWeight) -> float:
        """Calculate final weight from all components.
        
        Args:
            weight: ContextWeight object
            
        Returns:
            Final calculated weight
        """
        final = (weight.base_priority + 
                weight.domain_boost + 
                weight.ecosystem_boost + 
                weight.user_preference_boost)
        
        # Ensure weight stays within bounds
        return min(max(final, 0.0), 1.0)
    
    def implement_domain_specific_preferences(self,
                                            tech_context: TechContext,
                                            domain_context: DomainContext) -> Dict[str, float]:
        """Implement domain-specific technology preference logic.
        
        Args:
            tech_context: Technology context
            domain_context: Domain context
            
        Returns:
            Dictionary mapping technologies to preference scores
        """
        self.logger.info(f"Implementing domain preferences for: {domain_context.primary_domain}")
        
        preferences = {}
        
        if not domain_context.primary_domain:
            return preferences
        
        domain_prefs = self.domain_tech_preferences.get(domain_context.primary_domain, {})
        
        # Apply critical technologies
        for tech in domain_prefs.get('critical', []):
            preferences[tech] = ContextPriority.CRITICAL.value
        
        # Apply high priority technologies
        for tech in domain_prefs.get('high', []):
            preferences[tech] = ContextPriority.HIGH.value
        
        # Apply medium priority technologies
        for tech in domain_prefs.get('medium', []):
            preferences[tech] = ContextPriority.MEDIUM.value
        
        # Apply ecosystem preferences
        preferred_ecosystems = domain_prefs.get('ecosystems', [])
        if tech_context.ecosystem_preference in preferred_ecosystems:
            # Boost all technologies in the preferred ecosystem
            ecosystem_boost = 0.1
            for tech in tech_context.explicit_technologies:
                if tech in preferences:
                    preferences[tech] = min(preferences[tech] + ecosystem_boost, 1.0)
        
        self.logger.debug(f"Applied domain preferences for {len(preferences)} technologies")
        return preferences
    
    def detect_requirement_ambiguity(self, 
                                   parsed_req: ParsedRequirements) -> List[AmbiguityDetection]:
        """Detect ambiguity in requirements and suggest clarifications.
        
        Args:
            parsed_req: Parsed requirements
            
        Returns:
            List of detected ambiguities
        """
        self.logger.info("Detecting requirement ambiguity")
        
        ambiguities = []
        text = parsed_req.raw_text.lower()
        
        for ambiguity_type, patterns in self.ambiguity_patterns.items():
            for pattern in patterns:
                matches = re.finditer(pattern, text)
                for match in matches:
                    ambiguity = self._create_ambiguity_detection(
                        ambiguity_type, match, text
                    )
                    if ambiguity:
                        ambiguities.append(ambiguity)
        
        # Detect technology conflicts
        tech_conflicts = self._detect_technology_conflicts(parsed_req.explicit_technologies)
        ambiguities.extend(tech_conflicts)
        
        # Detect ecosystem mismatches
        ecosystem_conflicts = self._detect_ecosystem_conflicts(parsed_req)
        ambiguities.extend(ecosystem_conflicts)
        
        self.logger.info(f"Detected {len(ambiguities)} potential ambiguities")
        return ambiguities
    
    def _create_ambiguity_detection(self,
                                  ambiguity_type: AmbiguityType,
                                  match: re.Match,
                                  text: str) -> Optional[AmbiguityDetection]:
        """Create ambiguity detection from regex match.
        
        Args:
            ambiguity_type: Type of ambiguity
            match: Regex match object
            text: Full text being analyzed
            
        Returns:
            AmbiguityDetection object or None
        """
        matched_text = match.group(0)
        
        # Generate description and suggestions based on ambiguity type
        if ambiguity_type == AmbiguityType.TECHNOLOGY_CONFLICT:
            return AmbiguityDetection(
                ambiguity_type=ambiguity_type,
                description=f"Conflicting technology preferences detected: '{matched_text}'",
                conflicting_elements=[matched_text],
                suggested_clarifications=[
                    "Please specify which technology is preferred",
                    "Clarify if both technologies are required or if one is an alternative"
                ],
                confidence=0.8,
                impact_level="high"
            )
        
        elif ambiguity_type == AmbiguityType.ECOSYSTEM_MISMATCH:
            return AmbiguityDetection(
                ambiguity_type=ambiguity_type,
                description=f"Mixed cloud ecosystem references: '{matched_text}'",
                conflicting_elements=[matched_text],
                suggested_clarifications=[
                    "Specify the preferred cloud provider",
                    "Clarify if multi-cloud deployment is intended"
                ],
                confidence=0.9,
                impact_level="high"
            )
        
        elif ambiguity_type == AmbiguityType.INCOMPLETE_SPECIFICATION:
            return AmbiguityDetection(
                ambiguity_type=ambiguity_type,
                description=f"Incomplete technology specification: '{matched_text}'",
                conflicting_elements=[matched_text],
                suggested_clarifications=[
                    "Specify the exact technology or service needed",
                    "Provide more details about requirements and constraints"
                ],
                confidence=0.7,
                impact_level="medium"
            )
        
        elif ambiguity_type == AmbiguityType.CONTRADICTORY_REQUIREMENTS:
            return AmbiguityDetection(
                ambiguity_type=ambiguity_type,
                description=f"Contradictory requirements detected: '{matched_text}'",
                conflicting_elements=[matched_text],
                suggested_clarifications=[
                    "Clarify the priority of conflicting requirements",
                    "Specify acceptable trade-offs between requirements"
                ],
                confidence=0.8,
                impact_level="high"
            )
        
        elif ambiguity_type == AmbiguityType.UNCLEAR_DOMAIN:
            return AmbiguityDetection(
                ambiguity_type=ambiguity_type,
                description=f"Unclear domain specification: '{matched_text}'",
                conflicting_elements=[matched_text],
                suggested_clarifications=[
                    "Specify the primary use case or domain",
                    "Provide more context about the application type"
                ],
                confidence=0.6,
                impact_level="medium"
            )
        
        return None
    
    def _detect_technology_conflicts(self, 
                                   explicit_techs: List[ExplicitTech]) -> List[AmbiguityDetection]:
        """Detect conflicts between explicitly mentioned technologies.
        
        Args:
            explicit_techs: List of explicitly mentioned technologies
            
        Returns:
            List of detected conflicts
        """
        conflicts = []
        
        # Define conflicting technology groups
        conflict_groups = [
            {'PostgreSQL', 'MySQL', 'MongoDB'},  # Database conflicts
            {'React', 'Vue.js', 'Angular'},      # Frontend framework conflicts
            {'Django', 'Flask', 'FastAPI'},      # Python framework conflicts
            {'AWS Lambda', 'Azure Functions', 'Google Cloud Functions'},  # Serverless conflicts
        ]
        
        tech_names = {tech.name for tech in explicit_techs}
        
        for group in conflict_groups:
            conflicts_in_group = tech_names.intersection(group)
            if len(conflicts_in_group) > 1:
                conflicts.append(AmbiguityDetection(
                    ambiguity_type=AmbiguityType.TECHNOLOGY_CONFLICT,
                    description=f"Multiple conflicting technologies specified: {', '.join(conflicts_in_group)}",
                    conflicting_elements=list(conflicts_in_group),
                    suggested_clarifications=[
                        "Choose one primary technology from the conflicting group",
                        "Clarify if multiple technologies are needed for different components"
                    ],
                    confidence=0.9,
                    impact_level="high"
                ))
        
        return conflicts
    
    def _detect_ecosystem_conflicts(self, 
                                  parsed_req: ParsedRequirements) -> List[AmbiguityDetection]:
        """Detect ecosystem conflicts in requirements.
        
        Args:
            parsed_req: Parsed requirements
            
        Returns:
            List of detected ecosystem conflicts
        """
        conflicts = []
        
        # Count ecosystem mentions
        ecosystem_counts = defaultdict(int)
        ecosystem_techs = defaultdict(list)
        
        ecosystem_mappings = {
            'aws': {'amazon', 'aws'},
            'azure': {'azure', 'microsoft'},
            'gcp': {'google', 'gcp'}
        }
        
        for tech in parsed_req.explicit_technologies:
            tech_lower = tech.name.lower()
            for ecosystem, keywords in ecosystem_mappings.items():
                if any(keyword in tech_lower for keyword in keywords):
                    ecosystem_counts[ecosystem] += 1
                    ecosystem_techs[ecosystem].append(tech.name)
        
        # Check for conflicts
        active_ecosystems = [eco for eco, count in ecosystem_counts.items() if count > 0]
        
        if len(active_ecosystems) > 1:
            conflicts.append(AmbiguityDetection(
                ambiguity_type=AmbiguityType.ECOSYSTEM_MISMATCH,
                description=f"Multiple cloud ecosystems detected: {', '.join(active_ecosystems)}",
                conflicting_elements=[tech for techs in ecosystem_techs.values() for tech in techs],
                suggested_clarifications=[
                    "Specify the primary cloud provider",
                    "Clarify if multi-cloud architecture is intended",
                    "Consider ecosystem consistency for better integration"
                ],
                confidence=0.8,
                impact_level="high"
            ))
        
        return conflicts
    
    def resolve_technology_conflicts(self,
                                   conflicts: List[AmbiguityDetection],
                                   tech_context: TechContext) -> Dict[str, str]:
        """Resolve technology conflicts using context-based tie-breaking.
        
        Args:
            conflicts: List of detected conflicts
            tech_context: Technology context for resolution
            
        Returns:
            Dictionary mapping conflicting technologies to resolution decisions
        """
        self.logger.info(f"Resolving {len(conflicts)} technology conflicts")
        
        resolutions = {}
        
        for conflict in conflicts:
            if conflict.ambiguity_type == AmbiguityType.TECHNOLOGY_CONFLICT:
                resolution = self._resolve_single_conflict(conflict, tech_context)
                resolutions.update(resolution)
        
        return resolutions
    
    def _resolve_single_conflict(self,
                               conflict: AmbiguityDetection,
                               tech_context: TechContext) -> Dict[str, str]:
        """Resolve a single technology conflict.
        
        Args:
            conflict: Conflict to resolve
            tech_context: Technology context
            
        Returns:
            Dictionary with resolution decisions
        """
        conflicting_techs = conflict.conflicting_elements
        resolution = {}
        
        # Score each technology based on context
        tech_scores = {}
        for tech in conflicting_techs:
            score = 0.0
            
            # Explicit mention score
            if tech in tech_context.explicit_technologies:
                score += tech_context.explicit_technologies[tech] * 0.5
            
            # Contextual score
            if tech in tech_context.contextual_technologies:
                score += tech_context.contextual_technologies[tech] * 0.3
            
            # Ecosystem consistency score
            if tech_context.ecosystem_preference:
                # This would need ecosystem mapping logic
                score += 0.2  # Placeholder
            
            tech_scores[tech] = score
        
        # Select the highest scoring technology
        if tech_scores:
            winner = max(tech_scores, key=tech_scores.get)
            for tech in conflicting_techs:
                if tech == winner:
                    resolution[tech] = f"Selected as primary choice (score: {tech_scores[tech]:.2f})"
                else:
                    resolution[tech] = f"Deprioritized in favor of {winner}"
        
        return resolution
    
    def learn_user_preferences(self,
                             selected_technologies: List[str],
                             rejected_technologies: List[str],
                             domain: str,
                             context_patterns: List[str]) -> None:
        """Learn and adapt user preferences based on selections.
        
        Args:
            selected_technologies: Technologies user selected
            rejected_technologies: Technologies user rejected
            domain: Domain context
            context_patterns: Context patterns from the session
        """
        self.logger.info(f"Learning user preferences for domain: {domain}")
        
        # Update preferences for selected technologies
        for tech in selected_technologies:
            pref_key = f"{domain}:{tech}"
            if pref_key not in self.user_preferences:
                self.user_preferences[pref_key] = UserPreference(
                    technology=tech,
                    domain=domain
                )
            
            pref = self.user_preferences[pref_key]
            pref.selection_count += 1
            pref.context_patterns.extend(context_patterns)
            pref.preference_score = self._calculate_preference_score(pref)
            pref.last_updated = self._get_current_timestamp()
        
        # Update preferences for rejected technologies
        for tech in rejected_technologies:
            pref_key = f"{domain}:{tech}"
            if pref_key not in self.user_preferences:
                self.user_preferences[pref_key] = UserPreference(
                    technology=tech,
                    domain=domain
                )
            
            pref = self.user_preferences[pref_key]
            pref.rejection_count += 1
            pref.preference_score = self._calculate_preference_score(pref)
            pref.last_updated = self._get_current_timestamp()
        
        self.logger.debug(f"Updated preferences for {len(selected_technologies + rejected_technologies)} technologies")
    
    def _calculate_preference_score(self, preference: UserPreference) -> float:
        """Calculate preference score based on selection/rejection history.
        
        Args:
            preference: User preference data
            
        Returns:
            Calculated preference score
        """
        total_interactions = preference.selection_count + preference.rejection_count
        if total_interactions == 0:
            return 0.0
        
        # Calculate score based on selection ratio with smoothing
        selection_ratio = preference.selection_count / total_interactions
        
        # Apply confidence based on number of interactions
        confidence = min(total_interactions / 10.0, 1.0)  # Max confidence at 10 interactions
        
        # Score ranges from -1.0 (always rejected) to 1.0 (always selected)
        raw_score = (selection_ratio - 0.5) * 2.0
        
        return raw_score * confidence
    
    def _get_current_timestamp(self) -> str:
        """Get current timestamp as string.
        
        Returns:
            Current timestamp
        """
        from datetime import datetime
        return datetime.now().isoformat()
    
    def get_prioritization_summary(self, 
                                 context_weights: Dict[str, ContextWeight]) -> Dict[str, Any]:
        """Get summary of prioritization decisions.
        
        Args:
            context_weights: Calculated context weights
            
        Returns:
            Summary dictionary
        """
        # Sort technologies by final weight
        sorted_techs = sorted(
            context_weights.items(),
            key=lambda x: x[1].final_weight,
            reverse=True
        )
        
        summary = {
            'total_technologies': len(context_weights),
            'top_technologies': [
                {
                    'technology': tech,
                    'weight': weight.final_weight,
                    'reasoning': weight.reasoning
                }
                for tech, weight in sorted_techs[:10]
            ],
            'weight_distribution': {
                'critical': len([w for w in context_weights.values() if w.final_weight >= 0.9]),
                'high': len([w for w in context_weights.values() if 0.7 <= w.final_weight < 0.9]),
                'medium': len([w for w in context_weights.values() if 0.5 <= w.final_weight < 0.7]),
                'low': len([w for w in context_weights.values() if w.final_weight < 0.5])
            },
            'average_weight': sum(w.final_weight for w in context_weights.values()) / len(context_weights) if context_weights else 0.0
        }
        
        return summary