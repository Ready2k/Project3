"""Technology ecosystem intelligence and integration recommendations."""

from dataclasses import dataclass, field
from typing import Dict, List, Optional, Tuple, Any
from enum import Enum

from ..catalog.models import TechEntry, EcosystemType
from app.utils.imports import require_service


class IntegrationPattern(Enum):
    """Common integration patterns."""

    API_GATEWAY = "api_gateway"
    MESSAGE_QUEUE = "message_queue"
    DATABASE_CONNECTION = "database_connection"
    AUTHENTICATION = "authentication"
    MONITORING = "monitoring"
    LOGGING = "logging"
    CACHING = "caching"
    STORAGE = "storage"
    COMPUTE = "compute"
    NETWORKING = "networking"


class CompatibilityLevel(Enum):
    """Technology compatibility levels."""

    NATIVE = "native"  # Designed to work together
    COMPATIBLE = "compatible"  # Work well together
    NEUTRAL = "neutral"  # No specific compatibility
    PROBLEMATIC = "problematic"  # May have issues
    INCOMPATIBLE = "incompatible"  # Should not be used together


@dataclass
class EcosystemMapping:
    """Mapping between technologies across ecosystems."""

    source_tech: str
    target_ecosystem: EcosystemType
    equivalent_tech: str
    confidence: float  # 0.0-1.0
    notes: Optional[str] = None


@dataclass
class IntegrationSuggestion:
    """Suggestion for technology integration."""

    primary_tech: str
    suggested_tech: str
    integration_pattern: IntegrationPattern
    confidence: float
    reasoning: str
    required_components: List[str] = field(default_factory=list)


@dataclass
class CompatibilityResult:
    """Result of compatibility analysis."""

    tech1: str
    tech2: str
    compatibility: CompatibilityLevel
    confidence: float
    reasoning: str
    potential_issues: List[str] = field(default_factory=list)
    mitigation_strategies: List[str] = field(default_factory=list)


@dataclass
class EcosystemConsistencyResult:
    """Result of ecosystem consistency analysis."""

    is_consistent: bool
    primary_ecosystem: Optional[EcosystemType]
    inconsistent_technologies: List[str] = field(default_factory=list)
    suggestions: List[str] = field(default_factory=list)
    migration_options: List[EcosystemMapping] = field(default_factory=list)


@dataclass
class DependencyGraph:
    """Technology dependency graph."""

    nodes: Dict[str, TechEntry]
    edges: Dict[str, List[str]]  # tech_id -> list of dependent tech_ids
    integration_patterns: Dict[Tuple[str, str], IntegrationPattern]


class EcosystemIntelligence:
    """Technology ecosystem intelligence and integration recommendations."""

    def __init__(self, catalog_manager=None):
        self.catalog_manager = catalog_manager
        self.logger = require_service("logger", context="EcosystemIntelligence")

        # Load ecosystem mappings and compatibility rules
        self._load_ecosystem_mappings()
        self._load_compatibility_rules()
        self._load_integration_patterns()

    def _load_ecosystem_mappings(self) -> None:
        """Load ecosystem mapping data."""
        self.ecosystem_mappings = {
            # AWS to Azure mappings
            ("aws_lambda", EcosystemType.AZURE): EcosystemMapping(
                source_tech="aws_lambda",
                target_ecosystem=EcosystemType.AZURE,
                equivalent_tech="azure_functions",
                confidence=0.9,
                notes="Direct serverless function equivalent",
            ),
            ("aws_s3", EcosystemType.AZURE): EcosystemMapping(
                source_tech="aws_s3",
                target_ecosystem=EcosystemType.AZURE,
                equivalent_tech="azure_blob_storage",
                confidence=0.9,
                notes="Object storage equivalent",
            ),
            ("aws_rds", EcosystemType.AZURE): EcosystemMapping(
                source_tech="aws_rds",
                target_ecosystem=EcosystemType.AZURE,
                equivalent_tech="azure_sql_database",
                confidence=0.8,
                notes="Managed database service equivalent",
            ),
            ("aws_api_gateway", EcosystemType.AZURE): EcosystemMapping(
                source_tech="aws_api_gateway",
                target_ecosystem=EcosystemType.AZURE,
                equivalent_tech="azure_api_management",
                confidence=0.8,
                notes="API management service equivalent",
            ),
            # AWS to GCP mappings
            ("aws_lambda", EcosystemType.GCP): EcosystemMapping(
                source_tech="aws_lambda",
                target_ecosystem=EcosystemType.GCP,
                equivalent_tech="google_cloud_functions",
                confidence=0.9,
                notes="Direct serverless function equivalent",
            ),
            ("aws_s3", EcosystemType.GCP): EcosystemMapping(
                source_tech="aws_s3",
                target_ecosystem=EcosystemType.GCP,
                equivalent_tech="google_cloud_storage",
                confidence=0.9,
                notes="Object storage equivalent",
            ),
            ("aws_rds", EcosystemType.GCP): EcosystemMapping(
                source_tech="aws_rds",
                target_ecosystem=EcosystemType.GCP,
                equivalent_tech="google_cloud_sql",
                confidence=0.8,
                notes="Managed database service equivalent",
            ),
            # Azure to AWS mappings
            ("azure_functions", EcosystemType.AWS): EcosystemMapping(
                source_tech="azure_functions",
                target_ecosystem=EcosystemType.AWS,
                equivalent_tech="aws_lambda",
                confidence=0.9,
                notes="Direct serverless function equivalent",
            ),
            ("azure_blob_storage", EcosystemType.AWS): EcosystemMapping(
                source_tech="azure_blob_storage",
                target_ecosystem=EcosystemType.AWS,
                equivalent_tech="aws_s3",
                confidence=0.9,
                notes="Object storage equivalent",
            ),
            # GCP to AWS mappings
            ("google_cloud_functions", EcosystemType.AWS): EcosystemMapping(
                source_tech="google_cloud_functions",
                target_ecosystem=EcosystemType.AWS,
                equivalent_tech="aws_lambda",
                confidence=0.9,
                notes="Direct serverless function equivalent",
            ),
            ("google_cloud_storage", EcosystemType.AWS): EcosystemMapping(
                source_tech="google_cloud_storage",
                target_ecosystem=EcosystemType.AWS,
                equivalent_tech="aws_s3",
                confidence=0.9,
                notes="Object storage equivalent",
            ),
        }

    def _load_compatibility_rules(self) -> None:
        """Load technology compatibility rules."""
        self.compatibility_rules = {
            # Cloud provider compatibility
            ("aws", "azure"): CompatibilityResult(
                tech1="aws",
                tech2="azure",
                compatibility=CompatibilityLevel.PROBLEMATIC,
                confidence=0.9,
                reasoning="Different cloud providers require separate management",
                potential_issues=[
                    "Increased complexity",
                    "Multiple billing",
                    "Different APIs",
                ],
                mitigation_strategies=[
                    "Use multi-cloud management tools",
                    "Standardize on one provider",
                ],
            ),
            ("aws", "gcp"): CompatibilityResult(
                tech1="aws",
                tech2="gcp",
                compatibility=CompatibilityLevel.PROBLEMATIC,
                confidence=0.9,
                reasoning="Different cloud providers require separate management",
                potential_issues=[
                    "Increased complexity",
                    "Multiple billing",
                    "Different APIs",
                ],
                mitigation_strategies=[
                    "Use multi-cloud management tools",
                    "Standardize on one provider",
                ],
            ),
            # Framework compatibility
            ("fastapi", "flask"): CompatibilityResult(
                tech1="fastapi",
                tech2="flask",
                compatibility=CompatibilityLevel.PROBLEMATIC,
                confidence=0.8,
                reasoning="Both are Python web frameworks - typically use one",
                potential_issues=["Redundant functionality", "Different patterns"],
                mitigation_strategies=[
                    "Choose one framework",
                    "Use for different services",
                ],
            ),
            ("django", "fastapi"): CompatibilityResult(
                tech1="django",
                tech2="fastapi",
                compatibility=CompatibilityLevel.COMPATIBLE,
                confidence=0.7,
                reasoning="Can complement each other - Django for web, FastAPI for APIs",
                potential_issues=["Increased complexity"],
                mitigation_strategies=["Clear separation of concerns"],
            ),
            # Database compatibility
            ("postgresql", "mysql"): CompatibilityResult(
                tech1="postgresql",
                tech2="mysql",
                compatibility=CompatibilityLevel.PROBLEMATIC,
                confidence=0.8,
                reasoning="Multiple SQL databases increase complexity",
                potential_issues=["Different SQL dialects", "Multiple connections"],
                mitigation_strategies=[
                    "Use ORM abstraction",
                    "Standardize on one database",
                ],
            ),
            # AI/ML compatibility
            ("langchain", "llamaindex"): CompatibilityResult(
                tech1="langchain",
                tech2="llamaindex",
                compatibility=CompatibilityLevel.COMPATIBLE,
                confidence=0.7,
                reasoning="Both are LLM frameworks but serve different purposes",
                potential_issues=["Overlapping functionality"],
                mitigation_strategies=["Use for different use cases"],
            ),
            # Native integrations
            ("aws_lambda", "aws_api_gateway"): CompatibilityResult(
                tech1="aws_lambda",
                tech2="aws_api_gateway",
                compatibility=CompatibilityLevel.NATIVE,
                confidence=0.95,
                reasoning="Designed to work together in AWS ecosystem",
                potential_issues=[],
                mitigation_strategies=[],
            ),
            ("fastapi", "pydantic"): CompatibilityResult(
                tech1="fastapi",
                tech2="pydantic",
                compatibility=CompatibilityLevel.NATIVE,
                confidence=0.95,
                reasoning="FastAPI is built on Pydantic",
                potential_issues=[],
                mitigation_strategies=[],
            ),
        }

    def _load_integration_patterns(self) -> None:
        """Load integration pattern suggestions."""
        self.integration_patterns = {
            # API patterns
            ("fastapi", IntegrationPattern.API_GATEWAY): [
                IntegrationSuggestion(
                    primary_tech="fastapi",
                    suggested_tech="nginx",
                    integration_pattern=IntegrationPattern.API_GATEWAY,
                    confidence=0.8,
                    reasoning="Nginx as reverse proxy for FastAPI",
                    required_components=["uvicorn"],
                ),
                IntegrationSuggestion(
                    primary_tech="fastapi",
                    suggested_tech="aws_api_gateway",
                    integration_pattern=IntegrationPattern.API_GATEWAY,
                    confidence=0.9,
                    reasoning="AWS API Gateway for managed API routing",
                    required_components=["aws_lambda"],
                ),
            ],
            # Database patterns
            ("fastapi", IntegrationPattern.DATABASE_CONNECTION): [
                IntegrationSuggestion(
                    primary_tech="fastapi",
                    suggested_tech="sqlalchemy",
                    integration_pattern=IntegrationPattern.DATABASE_CONNECTION,
                    confidence=0.9,
                    reasoning="SQLAlchemy ORM for database operations",
                    required_components=["asyncpg", "psycopg2"],
                ),
                IntegrationSuggestion(
                    primary_tech="fastapi",
                    suggested_tech="postgresql",
                    integration_pattern=IntegrationPattern.DATABASE_CONNECTION,
                    confidence=0.8,
                    reasoning="PostgreSQL as primary database",
                    required_components=["sqlalchemy"],
                ),
            ],
            # Authentication patterns
            ("fastapi", IntegrationPattern.AUTHENTICATION): [
                IntegrationSuggestion(
                    primary_tech="fastapi",
                    suggested_tech="jwt",
                    integration_pattern=IntegrationPattern.AUTHENTICATION,
                    confidence=0.8,
                    reasoning="JWT tokens for API authentication",
                    required_components=["python-jose"],
                ),
                IntegrationSuggestion(
                    primary_tech="fastapi",
                    suggested_tech="oauth2",
                    integration_pattern=IntegrationPattern.AUTHENTICATION,
                    confidence=0.7,
                    reasoning="OAuth2 for third-party authentication",
                    required_components=["authlib"],
                ),
            ],
            # Caching patterns
            ("fastapi", IntegrationPattern.CACHING): [
                IntegrationSuggestion(
                    primary_tech="fastapi",
                    suggested_tech="redis",
                    integration_pattern=IntegrationPattern.CACHING,
                    confidence=0.9,
                    reasoning="Redis for high-performance caching",
                    required_components=["redis-py"],
                )
            ],
            # AI/ML patterns
            ("langchain", IntegrationPattern.STORAGE): [
                IntegrationSuggestion(
                    primary_tech="langchain",
                    suggested_tech="faiss",
                    integration_pattern=IntegrationPattern.STORAGE,
                    confidence=0.8,
                    reasoning="FAISS for vector storage and similarity search",
                    required_components=["sentence-transformers"],
                ),
                IntegrationSuggestion(
                    primary_tech="langchain",
                    suggested_tech="pinecone",
                    integration_pattern=IntegrationPattern.STORAGE,
                    confidence=0.7,
                    reasoning="Pinecone for managed vector database",
                    required_components=["pinecone-client"],
                ),
            ],
        }

    def detect_ecosystem_consistency(
        self, technologies: List[str]
    ) -> EcosystemConsistencyResult:
        """
        Detect ecosystem consistency in a list of technologies.

        Args:
            technologies: List of technology names/IDs

        Returns:
            EcosystemConsistencyResult with consistency analysis
        """
        if not self.catalog_manager:
            return EcosystemConsistencyResult(
                is_consistent=True,
                primary_ecosystem=None,
                suggestions=["Catalog manager not available for ecosystem analysis"],
            )

        # Get technology entries
        tech_entries = []
        for tech_name in technologies:
            tech_entry = self.catalog_manager.lookup_technology(tech_name)
            if tech_entry and tech_entry.tech_entry:
                tech_entries.append(tech_entry.tech_entry)

        if not tech_entries:
            return EcosystemConsistencyResult(
                is_consistent=True,
                primary_ecosystem=None,
                suggestions=["No technologies found in catalog"],
            )

        # Count ecosystems
        ecosystem_counts = {}
        ecosystem_techs = {}

        for tech in tech_entries:
            if tech.ecosystem:
                ecosystem = tech.ecosystem
                ecosystem_counts[ecosystem] = ecosystem_counts.get(ecosystem, 0) + 1
                if ecosystem not in ecosystem_techs:
                    ecosystem_techs[ecosystem] = []
                ecosystem_techs[ecosystem].append(tech.name)

        # Determine primary ecosystem
        primary_ecosystem = None
        if ecosystem_counts:
            primary_ecosystem = max(
                ecosystem_counts.keys(), key=lambda x: ecosystem_counts[x]
            )

        # Check consistency
        inconsistent_technologies = []
        migration_options = []

        if len(ecosystem_counts) > 1:
            # Multiple ecosystems detected
            for ecosystem, techs in ecosystem_techs.items():
                if ecosystem != primary_ecosystem:
                    inconsistent_technologies.extend(techs)

                    # Find migration options
                    for tech_name in techs:
                        mapping_key = (
                            tech_name.lower().replace(" ", "_"),
                            primary_ecosystem,
                        )
                        if mapping_key in self.ecosystem_mappings:
                            migration_options.append(
                                self.ecosystem_mappings[mapping_key]
                            )

        is_consistent = len(inconsistent_technologies) == 0

        suggestions = []
        if not is_consistent:
            suggestions.append(
                f"Consider migrating to {primary_ecosystem.value} ecosystem for consistency"
            )
            if migration_options:
                suggestions.append(
                    "Migration options available for inconsistent technologies"
                )

        return EcosystemConsistencyResult(
            is_consistent=is_consistent,
            primary_ecosystem=primary_ecosystem,
            inconsistent_technologies=inconsistent_technologies,
            suggestions=suggestions,
            migration_options=migration_options,
        )

    def suggest_integrations(
        self, primary_tech: str, context: Optional[Dict[str, Any]] = None
    ) -> List[IntegrationSuggestion]:
        """
        Suggest integration technologies for a primary technology.

        Args:
            primary_tech: Primary technology name
            context: Optional context for more targeted suggestions

        Returns:
            List of integration suggestions
        """
        suggestions = []

        # Get suggestions from pattern database
        for (tech, pattern), pattern_suggestions in self.integration_patterns.items():
            if tech.lower() == primary_tech.lower():
                suggestions.extend(pattern_suggestions)

        # Context-based suggestions
        if context:
            # Cloud context
            if context.get("cloud_provider"):
                cloud_provider = context["cloud_provider"].lower()
                if cloud_provider == "aws":
                    suggestions.extend(self._get_aws_integrations(primary_tech))
                elif cloud_provider == "azure":
                    suggestions.extend(self._get_azure_integrations(primary_tech))
                elif cloud_provider == "gcp":
                    suggestions.extend(self._get_gcp_integrations(primary_tech))

            # Domain context
            if context.get("domain"):
                domain = context["domain"].lower()
                if "ai" in domain or "ml" in domain:
                    suggestions.extend(self._get_ai_integrations(primary_tech))
                elif "web" in domain:
                    suggestions.extend(self._get_web_integrations(primary_tech))

        # Remove duplicates and sort by confidence
        unique_suggestions = {}
        for suggestion in suggestions:
            key = (suggestion.suggested_tech, suggestion.integration_pattern)
            if (
                key not in unique_suggestions
                or suggestion.confidence > unique_suggestions[key].confidence
            ):
                unique_suggestions[key] = suggestion

        return sorted(
            unique_suggestions.values(), key=lambda x: x.confidence, reverse=True
        )

    def _get_aws_integrations(self, primary_tech: str) -> List[IntegrationSuggestion]:
        """Get AWS-specific integration suggestions."""
        aws_suggestions = []

        if primary_tech.lower() in ["fastapi", "flask", "django"]:
            aws_suggestions.extend(
                [
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="aws_lambda",
                        integration_pattern=IntegrationPattern.COMPUTE,
                        confidence=0.8,
                        reasoning="Serverless deployment on AWS Lambda",
                        required_components=["mangum"],
                    ),
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="aws_api_gateway",
                        integration_pattern=IntegrationPattern.API_GATEWAY,
                        confidence=0.9,
                        reasoning="AWS API Gateway for managed API routing",
                        required_components=["aws_lambda"],
                    ),
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="aws_rds",
                        integration_pattern=IntegrationPattern.DATABASE_CONNECTION,
                        confidence=0.8,
                        reasoning="AWS RDS for managed database",
                        required_components=["sqlalchemy"],
                    ),
                ]
            )

        return aws_suggestions

    def _get_azure_integrations(self, primary_tech: str) -> List[IntegrationSuggestion]:
        """Get Azure-specific integration suggestions."""
        azure_suggestions = []

        if primary_tech.lower() in ["fastapi", "flask", "django"]:
            azure_suggestions.extend(
                [
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="azure_functions",
                        integration_pattern=IntegrationPattern.COMPUTE,
                        confidence=0.8,
                        reasoning="Serverless deployment on Azure Functions",
                        required_components=["azure-functions"],
                    ),
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="azure_api_management",
                        integration_pattern=IntegrationPattern.API_GATEWAY,
                        confidence=0.8,
                        reasoning="Azure API Management for API routing",
                        required_components=["azure_functions"],
                    ),
                ]
            )

        return azure_suggestions

    def _get_gcp_integrations(self, primary_tech: str) -> List[IntegrationSuggestion]:
        """Get GCP-specific integration suggestions."""
        gcp_suggestions = []

        if primary_tech.lower() in ["fastapi", "flask", "django"]:
            gcp_suggestions.extend(
                [
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="google_cloud_functions",
                        integration_pattern=IntegrationPattern.COMPUTE,
                        confidence=0.8,
                        reasoning="Serverless deployment on Google Cloud Functions",
                        required_components=["functions-framework"],
                    ),
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="google_cloud_run",
                        integration_pattern=IntegrationPattern.COMPUTE,
                        confidence=0.9,
                        reasoning="Containerized deployment on Google Cloud Run",
                        required_components=["docker"],
                    ),
                ]
            )

        return gcp_suggestions

    def _get_ai_integrations(self, primary_tech: str) -> List[IntegrationSuggestion]:
        """Get AI/ML-specific integration suggestions."""
        ai_suggestions = []

        if primary_tech.lower() in ["langchain", "llamaindex"]:
            ai_suggestions.extend(
                [
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="openai",
                        integration_pattern=IntegrationPattern.API_GATEWAY,
                        confidence=0.9,
                        reasoning="OpenAI API for language model access",
                        required_components=["openai"],
                    ),
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="faiss",
                        integration_pattern=IntegrationPattern.STORAGE,
                        confidence=0.8,
                        reasoning="FAISS for vector similarity search",
                        required_components=["sentence-transformers"],
                    ),
                ]
            )

        return ai_suggestions

    def _get_web_integrations(self, primary_tech: str) -> List[IntegrationSuggestion]:
        """Get web-specific integration suggestions."""
        web_suggestions = []

        if primary_tech.lower() in ["fastapi", "flask", "django"]:
            web_suggestions.extend(
                [
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="nginx",
                        integration_pattern=IntegrationPattern.API_GATEWAY,
                        confidence=0.8,
                        reasoning="Nginx as reverse proxy and load balancer",
                        required_components=["uvicorn"],
                    ),
                    IntegrationSuggestion(
                        primary_tech=primary_tech,
                        suggested_tech="redis",
                        integration_pattern=IntegrationPattern.CACHING,
                        confidence=0.8,
                        reasoning="Redis for session storage and caching",
                        required_components=["redis-py"],
                    ),
                ]
            )

        return web_suggestions

    def check_technology_compatibility(
        self, tech1: str, tech2: str
    ) -> CompatibilityResult:
        """
        Check compatibility between two technologies.

        Args:
            tech1: First technology name
            tech2: Second technology name

        Returns:
            CompatibilityResult with compatibility analysis
        """
        # Normalize technology names
        tech1_norm = tech1.lower().replace(" ", "_")
        tech2_norm = tech2.lower().replace(" ", "_")

        # Check direct compatibility rules
        for (t1, t2), result in self.compatibility_rules.items():
            if (t1 == tech1_norm and t2 == tech2_norm) or (
                t1 == tech2_norm and t2 == tech1_norm
            ):
                return result

        # Check ecosystem compatibility
        if self.catalog_manager:
            tech1_entry = self.catalog_manager.lookup_technology(tech1)
            tech2_entry = self.catalog_manager.lookup_technology(tech2)

            if (
                tech1_entry
                and tech2_entry
                and tech1_entry.tech_entry
                and tech2_entry.tech_entry
            ):
                eco1 = tech1_entry.tech_entry.ecosystem
                eco2 = tech2_entry.tech_entry.ecosystem

                if eco1 and eco2:
                    if eco1 == eco2:
                        return CompatibilityResult(
                            tech1=tech1,
                            tech2=tech2,
                            compatibility=CompatibilityLevel.COMPATIBLE,
                            confidence=0.7,
                            reasoning=f"Both technologies belong to {eco1.value} ecosystem",
                        )
                    elif (
                        eco1
                        in [EcosystemType.AWS, EcosystemType.AZURE, EcosystemType.GCP]
                        and eco2
                        in [EcosystemType.AWS, EcosystemType.AZURE, EcosystemType.GCP]
                        and eco1 != eco2
                    ):
                        return CompatibilityResult(
                            tech1=tech1,
                            tech2=tech2,
                            compatibility=CompatibilityLevel.PROBLEMATIC,
                            confidence=0.8,
                            reasoning="Different cloud ecosystems may increase complexity",
                            potential_issues=[
                                "Multiple cloud providers",
                                "Different APIs",
                                "Increased management overhead",
                            ],
                            mitigation_strategies=[
                                "Use multi-cloud tools",
                                "Consider ecosystem consistency",
                            ],
                        )

        # Default neutral compatibility
        return CompatibilityResult(
            tech1=tech1,
            tech2=tech2,
            compatibility=CompatibilityLevel.NEUTRAL,
            confidence=0.5,
            reasoning="No specific compatibility information available",
        )

    def get_ecosystem_migration_suggestions(
        self, current_tech: str, target_ecosystem: EcosystemType
    ) -> List[EcosystemMapping]:
        """
        Get migration suggestions for moving a technology to a different ecosystem.

        Args:
            current_tech: Current technology name
            target_ecosystem: Target ecosystem to migrate to

        Returns:
            List of ecosystem mappings for migration
        """
        suggestions = []

        # Normalize technology name
        tech_norm = current_tech.lower().replace(" ", "_")

        # Look for direct mappings
        mapping_key = (tech_norm, target_ecosystem)
        if mapping_key in self.ecosystem_mappings:
            suggestions.append(self.ecosystem_mappings[mapping_key])

        # Look for partial matches
        for (source_tech, target_eco), mapping in self.ecosystem_mappings.items():
            if target_eco == target_ecosystem and source_tech in tech_norm:
                suggestions.append(mapping)

        return suggestions

    def build_dependency_graph(self, technologies: List[str]) -> DependencyGraph:
        """
        Build a dependency graph for a set of technologies.

        Args:
            technologies: List of technology names

        Returns:
            DependencyGraph showing relationships
        """
        nodes = {}
        edges = {}
        integration_patterns = {}

        if not self.catalog_manager:
            return DependencyGraph(
                nodes=nodes, edges=edges, integration_patterns=integration_patterns
            )

        # Build nodes
        for tech_name in technologies:
            tech_entry = self.catalog_manager.lookup_technology(tech_name)
            if tech_entry and tech_entry.tech_entry:
                nodes[tech_entry.tech_entry.id] = tech_entry.tech_entry
                edges[tech_entry.tech_entry.id] = []

        # Build edges based on integrations
        for tech_id, tech_entry in nodes.items():
            for integration in tech_entry.integrates_with:
                # Find integration in our technology set
                for other_tech_name in technologies:
                    other_tech_entry = self.catalog_manager.lookup_technology(
                        other_tech_name
                    )
                    if (
                        other_tech_entry
                        and other_tech_entry.tech_entry
                        and (
                            other_tech_entry.tech_entry.name.lower()
                            == integration.lower()
                            or integration.lower()
                            in [
                                alias.lower()
                                for alias in other_tech_entry.tech_entry.aliases
                            ]
                        )
                    ):

                        edges[tech_id].append(other_tech_entry.tech_entry.id)

                        # Infer integration pattern
                        pattern = self._infer_integration_pattern(
                            tech_entry.name, other_tech_entry.tech_entry.name
                        )
                        if pattern:
                            integration_patterns[
                                (tech_id, other_tech_entry.tech_entry.id)
                            ] = pattern

        return DependencyGraph(
            nodes=nodes, edges=edges, integration_patterns=integration_patterns
        )

    def _infer_integration_pattern(
        self, tech1: str, tech2: str
    ) -> Optional[IntegrationPattern]:
        """Infer integration pattern between two technologies."""
        tech1.lower()
        tech2_lower = tech2.lower()

        # Database patterns
        if any(db in tech2_lower for db in ["postgres", "mysql", "mongodb", "redis"]):
            return IntegrationPattern.DATABASE_CONNECTION

        # API Gateway patterns
        if any(gw in tech2_lower for gw in ["nginx", "api_gateway", "gateway"]):
            return IntegrationPattern.API_GATEWAY

        # Authentication patterns
        if any(auth in tech2_lower for auth in ["jwt", "oauth", "auth"]):
            return IntegrationPattern.AUTHENTICATION

        # Caching patterns
        if "redis" in tech2_lower or "cache" in tech2_lower:
            return IntegrationPattern.CACHING

        # Storage patterns
        if any(
            storage in tech2_lower for storage in ["s3", "blob", "storage", "faiss"]
        ):
            return IntegrationPattern.STORAGE

        # Monitoring patterns
        if any(
            monitor in tech2_lower for monitor in ["prometheus", "grafana", "monitor"]
        ):
            return IntegrationPattern.MONITORING

        return None

    def analyze_technology_stack(self, technologies: List[str]) -> Dict[str, Any]:
        """
        Perform comprehensive analysis of a technology stack.

        Args:
            technologies: List of technology names

        Returns:
            Comprehensive analysis results
        """
        analysis = {
            "ecosystem_consistency": self.detect_ecosystem_consistency(technologies),
            "compatibility_matrix": {},
            "integration_suggestions": {},
            "dependency_graph": self.build_dependency_graph(technologies),
            "migration_options": {},
        }

        # Build compatibility matrix
        for i, tech1 in enumerate(technologies):
            for tech2 in technologies[i + 1 :]:
                compatibility = self.check_technology_compatibility(tech1, tech2)
                analysis["compatibility_matrix"][(tech1, tech2)] = compatibility

        # Get integration suggestions for each technology
        for tech in technologies:
            suggestions = self.suggest_integrations(tech)
            if suggestions:
                analysis["integration_suggestions"][tech] = suggestions[
                    :3
                ]  # Top 3 suggestions

        # Get migration options if ecosystem is inconsistent
        if not analysis["ecosystem_consistency"].is_consistent:
            primary_ecosystem = analysis["ecosystem_consistency"].primary_ecosystem
            if primary_ecosystem:
                for tech in analysis["ecosystem_consistency"].inconsistent_technologies:
                    migrations = self.get_ecosystem_migration_suggestions(
                        tech, primary_ecosystem
                    )
                    if migrations:
                        analysis["migration_options"][tech] = migrations

        return analysis
