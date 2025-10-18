"""
Dynamic Component Mapping System for Infrastructure Diagrams.

This system automatically maps technologies to appropriate diagram components
based on technology metadata and configurable mapping rules, eliminating
the need for hardcoded mappings.
"""

import json
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from loguru import logger
from dataclasses import dataclass
from enum import Enum


class ComponentType(Enum):
    """Standard component types for infrastructure diagrams."""

    COMPUTE = "compute"
    DATABASE = "database"
    STORAGE = "storage"
    NETWORK = "network"
    INTEGRATION = "integration"
    SECURITY = "security"
    ANALYTICS = "analytics"
    ML = "ml"
    SAAS = "saas"


class DeploymentModel(Enum):
    """Deployment models for components."""

    CLOUD_AWS = "aws"
    CLOUD_GCP = "gcp"
    CLOUD_AZURE = "azure"
    KUBERNETES = "k8s"
    ON_PREMISE = "onprem"
    SAAS = "saas"


@dataclass
class ComponentMapping:
    """Represents a mapping from technology to diagram component."""

    technology_pattern: str  # Regex pattern to match technology names
    component_type: ComponentType
    deployment_model: DeploymentModel
    specific_component: Optional[str] = None  # Specific component class if needed
    tags: List[str] = None  # Technology tags that trigger this mapping

    def __post_init__(self):
        if self.tags is None:
            self.tags = []


class DynamicComponentMapper:
    """
    Maps technologies to diagram components dynamically based on:
    1. Technology metadata from the catalog
    2. Configurable mapping rules
    3. Intelligent pattern matching
    """

    def __init__(
        self,
        technology_catalog_path: str = "data/technologies.json",
        mapping_rules_path: str = "data/component_mapping_rules.json",
    ):
        self.technology_catalog_path = Path(technology_catalog_path)
        self.mapping_rules_path = Path(mapping_rules_path)

        self.technology_catalog = self._load_technology_catalog()
        self.mapping_rules = self._load_mapping_rules()

        # Cache for resolved mappings
        self._mapping_cache = {}

    def _load_technology_catalog(self) -> Dict[str, Any]:
        """Load the technology catalog."""
        try:
            with open(self.technology_catalog_path, "r") as f:
                return json.load(f)
        except FileNotFoundError:
            logger.warning(
                f"Technology catalog not found: {self.technology_catalog_path}"
            )
            return {"technologies": {}, "categories": {}}

    def _load_mapping_rules(self) -> List[ComponentMapping]:
        """Load component mapping rules from configuration."""
        if not self.mapping_rules_path.exists():
            return self._create_default_mapping_rules()

        try:
            with open(self.mapping_rules_path, "r") as f:
                rules_data = json.load(f)

            mappings = []
            for rule in rules_data.get("mappings", []):
                mappings.append(
                    ComponentMapping(
                        technology_pattern=rule["technology_pattern"],
                        component_type=ComponentType(rule["component_type"]),
                        deployment_model=DeploymentModel(rule["deployment_model"]),
                        specific_component=rule.get("specific_component"),
                        tags=rule.get("tags", []),
                    )
                )

            return mappings
        except Exception as e:
            logger.error(f"Failed to load mapping rules: {e}")
            return self._create_default_mapping_rules()

    def _create_default_mapping_rules(self) -> List[ComponentMapping]:
        """Create default mapping rules and save them."""
        default_rules = [
            # AI/ML Orchestration Frameworks
            ComponentMapping(
                technology_pattern=r"(langchain|crewai|autogen|semantic[_-]?kernel)",
                component_type=ComponentType.COMPUTE,
                deployment_model=DeploymentModel.ON_PREMISE,
                specific_component="Server",
                tags=["ai", "orchestration", "framework"],
            ),
            # AI Model APIs
            ComponentMapping(
                technology_pattern=r"(openai|claude|gpt|anthropic|huggingface).*api",
                component_type=ComponentType.SAAS,
                deployment_model=DeploymentModel.SAAS,
                specific_component="Snowflake",  # Generic SaaS icon
                tags=["ai", "api", "external"],
            ),
            # Vector Databases
            ComponentMapping(
                technology_pattern=r"(vector|embedding|faiss|pinecone|weaviate|chroma)",
                component_type=ComponentType.DATABASE,
                deployment_model=DeploymentModel.ON_PREMISE,
                specific_component="MongoDB",
                tags=["vector", "database", "ai"],
            ),
            # Knowledge Management
            ComponentMapping(
                technology_pattern=r"(knowledge[_-]?base|neo4j|graph)",
                component_type=ComponentType.DATABASE,
                deployment_model=DeploymentModel.ON_PREMISE,
                specific_component="PostgreSQL",
                tags=["knowledge", "graph", "database"],
            ),
            # Rule Engines
            ComponentMapping(
                technology_pattern=r"(rule[_-]?engine|drools|decision)",
                component_type=ComponentType.COMPUTE,
                deployment_model=DeploymentModel.ON_PREMISE,
                specific_component="Server",
                tags=["rules", "decision", "engine"],
            ),
            # Workflow Engines
            ComponentMapping(
                technology_pattern=r"(workflow|airflow|temporal|zeebe)",
                component_type=ComponentType.COMPUTE,
                deployment_model=DeploymentModel.ON_PREMISE,
                specific_component="Server",
                tags=["workflow", "orchestration"],
            ),
            # Memory Systems
            ComponentMapping(
                technology_pattern=r"(memory|cache|redis|memcached)",
                component_type=ComponentType.DATABASE,
                deployment_model=DeploymentModel.ON_PREMISE,
                specific_component="MongoDB",
                tags=["memory", "cache"],
            ),
            # External APIs (catch-all for SaaS integrations)
            ComponentMapping(
                technology_pattern=r".*api$",
                component_type=ComponentType.SAAS,
                deployment_model=DeploymentModel.SAAS,
                specific_component="Snowflake",
                tags=["api", "external", "integration"],
            ),
        ]

        # Save default rules
        self._save_mapping_rules(default_rules)
        return default_rules

    def _save_mapping_rules(self, rules: List[ComponentMapping]):
        """Save mapping rules to configuration file."""
        rules_data = {
            "version": "1.0",
            "description": "Dynamic component mapping rules for infrastructure diagrams",
            "mappings": [],
        }

        for rule in rules:
            rules_data["mappings"].append(
                {
                    "technology_pattern": rule.technology_pattern,
                    "component_type": rule.component_type.value,
                    "deployment_model": rule.deployment_model.value,
                    "specific_component": rule.specific_component,
                    "tags": rule.tags,
                }
            )

        # Ensure directory exists
        self.mapping_rules_path.parent.mkdir(parents=True, exist_ok=True)

        with open(self.mapping_rules_path, "w") as f:
            json.dump(rules_data, f, indent=2)

        logger.info(f"Saved {len(rules)} mapping rules to {self.mapping_rules_path}")

    def map_technology_to_component(
        self, technology_name: str, provider_hint: Optional[str] = None
    ) -> Tuple[str, str]:
        """
        Map a technology name to a diagram component.

        Args:
            technology_name: Name of the technology to map
            provider_hint: Optional hint about preferred provider (aws, gcp, etc.)

        Returns:
            Tuple of (provider, component_type) for diagram generation
        """
        # Check cache first
        cache_key = f"{technology_name}:{provider_hint or 'auto'}"
        if cache_key in self._mapping_cache:
            return self._mapping_cache[cache_key]

        # Normalize technology name
        tech_name_lower = technology_name.lower().replace("-", "_")

        # Try to find technology in catalog first
        tech_info = self._find_technology_in_catalog(tech_name_lower)

        # Apply mapping rules
        mapping = self._apply_mapping_rules(tech_name_lower, tech_info)

        if mapping:
            provider = provider_hint or mapping.deployment_model.value
            component = mapping.specific_component or mapping.component_type.value

            result = (provider, component.lower())
            self._mapping_cache[cache_key] = result
            return result

        # Fallback to generic server
        logger.warning(
            f"No mapping found for technology: {technology_name}, using generic server"
        )
        fallback = ("onprem", "server")
        self._mapping_cache[cache_key] = fallback
        return fallback

    def _find_technology_in_catalog(self, tech_name: str) -> Optional[Dict[str, Any]]:
        """Find technology information in the catalog."""
        technologies = self.technology_catalog.get("technologies", {})

        # Direct match
        if tech_name in technologies:
            return technologies[tech_name]

        # Fuzzy match
        for tech_id, tech_info in technologies.items():
            if tech_name in tech_id.lower() or tech_id.lower() in tech_name:
                return tech_info

            # Check aliases if they exist
            aliases = tech_info.get("aliases", [])
            if any(alias.lower() in tech_name for alias in aliases):
                return tech_info

        return None

    def _apply_mapping_rules(
        self, tech_name: str, tech_info: Optional[Dict[str, Any]]
    ) -> Optional[ComponentMapping]:
        """Apply mapping rules to determine component type."""
        import re

        for rule in self.mapping_rules:
            # Check pattern match
            if re.search(rule.technology_pattern, tech_name, re.IGNORECASE):
                return rule

            # Check tag match if we have tech info
            if tech_info and rule.tags:
                tech_tags = tech_info.get("tags", [])
                if any(tag in tech_tags for tag in rule.tags):
                    return rule

        return None

    def get_supported_providers(self) -> List[str]:
        """Get list of supported diagram providers."""
        return [model.value for model in DeploymentModel]

    def add_mapping_rule(self, rule: ComponentMapping):
        """Add a new mapping rule."""
        self.mapping_rules.append(rule)
        self._save_mapping_rules(self.mapping_rules)
        self._mapping_cache.clear()  # Clear cache

    def update_from_technology_catalog(self):
        """Update mappings based on new technologies in catalog."""
        # This could analyze new technologies and suggest mapping rules
        # For now, just clear cache to force re-evaluation
        self._mapping_cache.clear()
        logger.info("Updated component mappings from technology catalog")


def create_component_mapping_config():
    """Create the initial component mapping configuration."""
    mapper = DynamicComponentMapper()
    logger.info("Created dynamic component mapping system")
    return mapper


if __name__ == "__main__":
    # Test the dynamic mapper
    mapper = DynamicComponentMapper()

    test_technologies = [
        "langchain_orchestrator",
        "crewai_coordinator",
        "openai_api",
        "vector_db",
        "neo4j",
        "drools",
        "salesforce_api",
    ]

    print("Testing Dynamic Component Mapping:")
    print("=" * 50)

    for tech in test_technologies:
        provider, component = mapper.map_technology_to_component(tech)
        print(f"{tech:25} -> {provider:10} / {component}")
