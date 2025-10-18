"""
Automated testing for catalog consistency and completeness.

This module provides comprehensive validation of the technology catalog,
including consistency checks, completeness validation, and quality assurance.
"""

import pytest
from typing import Dict, List, Any
from dataclasses import dataclass

from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import TechEntry


@dataclass
class CatalogConsistencyReport:
    """Report for catalog consistency validation."""

    total_entries: int
    valid_entries: int
    invalid_entries: int
    missing_integrations: List[str]
    orphaned_entries: List[str]
    duplicate_aliases: List[str]
    ecosystem_inconsistencies: List[str]
    completeness_score: float
    consistency_score: float

    def to_dict(self) -> Dict[str, Any]:
        """Convert report to dictionary."""
        return {
            "total_entries": self.total_entries,
            "valid_entries": self.valid_entries,
            "invalid_entries": self.invalid_entries,
            "missing_integrations": self.missing_integrations,
            "orphaned_entries": self.orphaned_entries,
            "duplicate_aliases": self.duplicate_aliases,
            "ecosystem_inconsistencies": self.ecosystem_inconsistencies,
            "completeness_score": round(self.completeness_score, 4),
            "consistency_score": round(self.consistency_score, 4),
        }


class CatalogConsistencyValidator:
    """Validator for catalog consistency and completeness."""

    def __init__(self, catalog_manager: IntelligentCatalogManager):
        self.catalog_manager = catalog_manager
        self.validation_rules = self._load_validation_rules()

    def _load_validation_rules(self) -> Dict[str, Any]:
        """Load validation rules for catalog entries."""
        return {
            "required_fields": ["name", "category", "description"],
            "optional_fields": [
                "aliases",
                "integrates_with",
                "alternatives",
                "ecosystem",
            ],
            "valid_categories": [
                "programming_language",
                "web_framework",
                "database",
                "cache",
                "message_queue",
                "container",
                "orchestration",
                "monitoring",
                "security",
                "api_gateway",
                "serverless",
                "storage",
                "cdn",
                "analytics",
                "machine_learning",
                "ci_cd",
                "testing",
                "logging",
            ],
            "valid_ecosystems": ["AWS", "Azure", "GCP", "open_source", "enterprise"],
            "integration_patterns": {
                "web_framework": ["database", "cache", "container"],
                "database": ["web_framework", "analytics", "backup"],
                "container": ["orchestration", "monitoring", "security"],
                "serverless": ["api_gateway", "database", "storage"],
                "message_queue": ["web_framework", "analytics", "monitoring"],
            },
        }

    def validate_catalog_consistency(self) -> CatalogConsistencyReport:
        """Perform comprehensive catalog consistency validation."""
        catalog_entries = self.catalog_manager.get_all_entries()

        total_entries = len(catalog_entries)
        valid_entries = 0
        invalid_entries = 0
        missing_integrations = []
        orphaned_entries = []
        duplicate_aliases = []
        ecosystem_inconsistencies = []

        # Track all aliases for duplicate detection
        alias_to_entries = {}

        # Validate each entry
        for entry_name, entry in catalog_entries.items():
            is_valid = True

            # Check required fields
            for field in self.validation_rules["required_fields"]:
                if not hasattr(entry, field) or not getattr(entry, field):
                    is_valid = False
                    break

            # Check category validity
            if (
                hasattr(entry, "category")
                and entry.category not in self.validation_rules["valid_categories"]
            ):
                is_valid = False

            # Check ecosystem validity
            if (
                hasattr(entry, "ecosystem")
                and entry.ecosystem
                and entry.ecosystem not in self.validation_rules["valid_ecosystems"]
            ):
                ecosystem_inconsistencies.append(
                    f"{entry_name}: invalid ecosystem '{entry.ecosystem}'"
                )
                is_valid = False

            # Track aliases for duplicate detection
            if hasattr(entry, "aliases") and entry.aliases:
                for alias in entry.aliases:
                    if alias in alias_to_entries:
                        alias_to_entries[alias].append(entry_name)
                    else:
                        alias_to_entries[alias] = [entry_name]

            # Check integration references
            if hasattr(entry, "integrates_with") and entry.integrates_with:
                for integration in entry.integrates_with:
                    if integration not in catalog_entries:
                        missing_integrations.append(f"{entry_name} -> {integration}")

            if is_valid:
                valid_entries += 1
            else:
                invalid_entries += 1

        # Find duplicate aliases
        for alias, entries in alias_to_entries.items():
            if len(entries) > 1:
                duplicate_aliases.append(f"'{alias}': {entries}")

        # Find orphaned entries (no incoming integrations)
        referenced_entries = set()
        for entry in catalog_entries.values():
            if hasattr(entry, "integrates_with") and entry.integrates_with:
                referenced_entries.update(entry.integrates_with)

        for entry_name in catalog_entries.keys():
            if entry_name not in referenced_entries:
                # Check if it's a foundational technology that doesn't need incoming references
                entry = catalog_entries[entry_name]
                if hasattr(entry, "category") and entry.category not in [
                    "programming_language",
                    "operating_system",
                ]:
                    orphaned_entries.append(entry_name)

        # Calculate scores
        completeness_score = self._calculate_completeness_score(catalog_entries)
        consistency_score = valid_entries / total_entries if total_entries > 0 else 0

        return CatalogConsistencyReport(
            total_entries=total_entries,
            valid_entries=valid_entries,
            invalid_entries=invalid_entries,
            missing_integrations=missing_integrations,
            orphaned_entries=orphaned_entries,
            duplicate_aliases=duplicate_aliases,
            ecosystem_inconsistencies=ecosystem_inconsistencies,
            completeness_score=completeness_score,
            consistency_score=consistency_score,
        )

    def _calculate_completeness_score(
        self, catalog_entries: Dict[str, TechEntry]
    ) -> float:
        """Calculate completeness score based on common technology coverage."""
        # Common technology stacks that should be in the catalog
        common_stacks = [
            # Web development stacks
            ["Python", "FastAPI", "PostgreSQL", "Redis"],
            ["Node.js", "Express", "MongoDB", "React"],
            ["Java", "Spring Boot", "MySQL", "Angular"],
            ["PHP", "Laravel", "MySQL", "Vue.js"],
            # Cloud stacks
            ["AWS Lambda", "AWS API Gateway", "DynamoDB", "Amazon S3"],
            [
                "Azure Functions",
                "Azure API Management",
                "Azure Cosmos DB",
                "Azure Storage",
            ],
            [
                "Google Cloud Functions",
                "Google Cloud API Gateway",
                "Google Firestore",
                "Google Cloud Storage",
            ],
            # Container stacks
            ["Docker", "Kubernetes", "NGINX", "Prometheus"],
            ["Docker", "Docker Swarm", "Traefik", "Grafana"],
            # Data processing stacks
            ["Apache Kafka", "Apache Spark", "Elasticsearch", "Kibana"],
            ["Apache Airflow", "Apache Beam", "Google BigQuery", "Apache Superset"],
            # Microservices stacks
            ["Spring Boot", "Eureka", "Zuul", "Hystrix"],
            ["Istio", "Envoy", "Jaeger", "Kiali"],
        ]

        total_technologies = set()
        for stack in common_stacks:
            total_technologies.update(stack)

        # Count how many are in the catalog
        covered_technologies = 0
        for tech in total_technologies:
            if self.catalog_manager.lookup_technology(tech):
                covered_technologies += 1

        return (
            covered_technologies / len(total_technologies) if total_technologies else 0
        )

    def validate_ecosystem_consistency(self) -> Dict[str, List[str]]:
        """Validate ecosystem consistency within technology stacks."""
        catalog_entries = self.catalog_manager.get_all_entries()
        ecosystem_groups = {}
        inconsistencies = {}

        # Group technologies by ecosystem
        for entry_name, entry in catalog_entries.items():
            if hasattr(entry, "ecosystem") and entry.ecosystem:
                ecosystem = entry.ecosystem
                if ecosystem not in ecosystem_groups:
                    ecosystem_groups[ecosystem] = []
                ecosystem_groups[ecosystem].append(entry_name)

        # Check for cross-ecosystem integrations that might be inconsistent
        for entry_name, entry in catalog_entries.items():
            if (
                hasattr(entry, "integrates_with")
                and entry.integrates_with
                and hasattr(entry, "ecosystem")
            ):
                entry_ecosystem = entry.ecosystem
                if entry_ecosystem and entry_ecosystem in ["AWS", "Azure", "GCP"]:
                    for integration in entry.integrates_with:
                        if integration in catalog_entries:
                            integration_entry = catalog_entries[integration]
                            if (
                                hasattr(integration_entry, "ecosystem")
                                and integration_entry.ecosystem
                            ):
                                integration_ecosystem = integration_entry.ecosystem
                                if (
                                    integration_ecosystem in ["AWS", "Azure", "GCP"]
                                    and integration_ecosystem != entry_ecosystem
                                ):
                                    if entry_name not in inconsistencies:
                                        inconsistencies[entry_name] = []
                                    inconsistencies[entry_name].append(
                                        f"Cross-ecosystem integration: {entry_ecosystem} -> {integration_ecosystem} ({integration})"
                                    )

        return inconsistencies

    def validate_integration_patterns(self) -> Dict[str, List[str]]:
        """Validate that integration patterns make sense."""
        catalog_entries = self.catalog_manager.get_all_entries()
        pattern_violations = {}

        for entry_name, entry in catalog_entries.items():
            if not hasattr(entry, "category") or not hasattr(entry, "integrates_with"):
                continue

            category = entry.category
            integrations = entry.integrates_with or []

            if category in self.validation_rules["integration_patterns"]:
                expected_categories = self.validation_rules["integration_patterns"][
                    category
                ]

                for integration in integrations:
                    if integration in catalog_entries:
                        integration_entry = catalog_entries[integration]
                        if hasattr(integration_entry, "category"):
                            integration_category = integration_entry.category
                            if integration_category not in expected_categories:
                                if entry_name not in pattern_violations:
                                    pattern_violations[entry_name] = []
                                pattern_violations[entry_name].append(
                                    f"Unexpected integration: {category} -> {integration_category} ({integration})"
                                )

        return pattern_violations


class TestCatalogConsistency:
    """Test suite for catalog consistency and completeness validation."""

    @pytest.fixture
    def catalog_manager(self):
        """Create catalog manager with test data."""
        manager = IntelligentCatalogManager()

        # Add test catalog entries
        test_entries = [
            TechEntry(
                name="Python",
                category="programming_language",
                description="High-level programming language",
                aliases=["python3", "py"],
                integrates_with=["FastAPI", "Django", "Flask"],
                ecosystem="open_source",
            ),
            TechEntry(
                name="FastAPI",
                category="web_framework",
                description="Modern Python web framework",
                aliases=["fastapi"],
                integrates_with=["Python", "PostgreSQL", "Redis"],
                ecosystem="open_source",
            ),
            TechEntry(
                name="PostgreSQL",
                category="database",
                description="Advanced open source relational database",
                aliases=["postgres", "psql"],
                integrates_with=["FastAPI", "Django", "Spring Boot"],
                ecosystem="open_source",
            ),
            TechEntry(
                name="Redis",
                category="cache",
                description="In-memory data structure store",
                aliases=["redis-server"],
                integrates_with=["FastAPI", "Node.js", "Spring Boot"],
                ecosystem="open_source",
            ),
            TechEntry(
                name="AWS Lambda",
                category="serverless",
                description="Serverless compute service",
                aliases=["Lambda"],
                integrates_with=["AWS API Gateway", "DynamoDB", "Amazon S3"],
                ecosystem="AWS",
            ),
            TechEntry(
                name="AWS API Gateway",
                category="api_gateway",
                description="Managed API gateway service",
                aliases=["API Gateway"],
                integrates_with=["AWS Lambda", "Amazon Cognito"],
                ecosystem="AWS",
            ),
            TechEntry(
                name="DynamoDB",
                category="database",
                description="NoSQL database service",
                aliases=["Amazon DynamoDB"],
                integrates_with=["AWS Lambda", "AWS API Gateway"],
                ecosystem="AWS",
            ),
            # Add an entry with issues for testing
            TechEntry(
                name="Problematic Service",
                category="invalid_category",  # Invalid category
                description="",  # Missing description
                aliases=["fastapi"],  # Duplicate alias
                integrates_with=["NonExistent Service"],  # Missing integration
                ecosystem="InvalidEcosystem",  # Invalid ecosystem
            ),
        ]

        # Mock the catalog entries
        manager.catalog_entries = {entry.name: entry for entry in test_entries}
        return manager

    @pytest.fixture
    def consistency_validator(self, catalog_manager):
        """Create consistency validator."""
        return CatalogConsistencyValidator(catalog_manager)

    def test_catalog_consistency_validation(self, consistency_validator):
        """Test comprehensive catalog consistency validation."""
        report = consistency_validator.validate_catalog_consistency()

        # Basic validation
        assert report.total_entries > 0, "Should have catalog entries"
        assert report.valid_entries > 0, "Should have some valid entries"
        assert report.consistency_score > 0, "Should have some consistency"

        # Check for expected issues in test data
        assert report.invalid_entries > 0, "Should detect invalid entries"
        assert (
            len(report.missing_integrations) > 0
        ), "Should detect missing integrations"
        assert len(report.duplicate_aliases) > 0, "Should detect duplicate aliases"
        assert (
            len(report.ecosystem_inconsistencies) > 0
        ), "Should detect ecosystem issues"

        # Consistency score should be reasonable
        assert (
            0 <= report.consistency_score <= 1
        ), "Consistency score should be between 0 and 1"
        assert (
            0 <= report.completeness_score <= 1
        ), "Completeness score should be between 0 and 1"

        print(f"Catalog Consistency Report: {report.to_dict()}")

    def test_ecosystem_consistency_validation(self, consistency_validator):
        """Test ecosystem consistency validation."""
        inconsistencies = consistency_validator.validate_ecosystem_consistency()

        # Should detect cross-ecosystem integrations
        assert isinstance(
            inconsistencies, dict
        ), "Should return dictionary of inconsistencies"

        # Print inconsistencies for review
        if inconsistencies:
            print("Ecosystem Inconsistencies:")
            for entry, issues in inconsistencies.items():
                print(f"  {entry}: {issues}")

    def test_integration_pattern_validation(self, consistency_validator):
        """Test integration pattern validation."""
        violations = consistency_validator.validate_integration_patterns()

        # Should return dictionary of pattern violations
        assert isinstance(violations, dict), "Should return dictionary of violations"

        # Print violations for review
        if violations:
            print("Integration Pattern Violations:")
            for entry, issues in violations.items():
                print(f"  {entry}: {issues}")

    def test_catalog_completeness_for_common_stacks(self, catalog_manager):
        """Test catalog completeness for common technology stacks."""
        common_stacks = [
            {
                "name": "Python Web Stack",
                "technologies": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                "expected_coverage": 0.8,
            },
            {
                "name": "AWS Serverless Stack",
                "technologies": [
                    "AWS Lambda",
                    "AWS API Gateway",
                    "DynamoDB",
                    "Amazon S3",
                ],
                "expected_coverage": 0.75,
            },
            {
                "name": "Container Stack",
                "technologies": ["Docker", "Kubernetes", "NGINX", "Prometheus"],
                "expected_coverage": 0.5,  # Lower expectation for test data
            },
        ]

        completeness_results = []

        for stack in common_stacks:
            found_technologies = 0
            missing_technologies = []

            for tech in stack["technologies"]:
                if catalog_manager.lookup_technology(tech):
                    found_technologies += 1
                else:
                    missing_technologies.append(tech)

            coverage = found_technologies / len(stack["technologies"])
            completeness_results.append(
                {
                    "stack": stack["name"],
                    "coverage": coverage,
                    "expected": stack["expected_coverage"],
                    "missing": missing_technologies,
                }
            )

            # Check if coverage meets expectations
            assert (
                coverage >= stack["expected_coverage"]
            ), f"Low coverage for {stack['name']}: {coverage:.2%} (expected {stack['expected_coverage']:.2%})"

        print("Stack Completeness Results:")
        for result in completeness_results:
            print(f"  {result['stack']}: {result['coverage']:.2%} coverage")
            if result["missing"]:
                print(f"    Missing: {result['missing']}")

    def test_catalog_entry_quality_validation(self, catalog_manager):
        """Test quality validation of individual catalog entries."""
        catalog_entries = catalog_manager.get_all_entries()
        quality_issues = []

        for entry_name, entry in catalog_entries.items():
            issues = []

            # Check description quality
            if hasattr(entry, "description"):
                description = entry.description or ""
                if len(description) < 10:
                    issues.append("Description too short")
                if not description[0].isupper() if description else True:
                    issues.append("Description should start with capital letter")

            # Check alias quality
            if hasattr(entry, "aliases") and entry.aliases:
                for alias in entry.aliases:
                    if alias == entry.name:
                        issues.append(f"Alias '{alias}' same as name")
                    if len(alias) < 2:
                        issues.append(f"Alias '{alias}' too short")

            # Check integration quality
            if hasattr(entry, "integrates_with") and entry.integrates_with:
                if len(entry.integrates_with) == 0:
                    issues.append("No integrations specified")
                elif len(entry.integrates_with) > 10:
                    issues.append("Too many integrations (>10)")

            if issues:
                quality_issues.append({"entry": entry_name, "issues": issues})

        # Quality assertions
        total_entries = len(catalog_entries)
        entries_with_issues = len(quality_issues)
        quality_score = (
            (total_entries - entries_with_issues) / total_entries
            if total_entries > 0
            else 0
        )

        assert quality_score >= 0.7, f"Low catalog quality score: {quality_score:.2%}"

        if quality_issues:
            print("Catalog Quality Issues:")
            for issue in quality_issues:
                print(f"  {issue['entry']}: {issue['issues']}")

    def test_catalog_coverage_for_domains(self, catalog_manager):
        """Test catalog coverage for different technology domains."""
        domain_requirements = {
            "web_development": {
                "required_categories": [
                    "programming_language",
                    "web_framework",
                    "database",
                ],
                "min_entries_per_category": 2,
            },
            "cloud_computing": {
                "required_categories": ["serverless", "storage", "database"],
                "min_entries_per_category": 1,
            },
            "data_processing": {
                "required_categories": ["database", "analytics", "message_queue"],
                "min_entries_per_category": 1,
            },
            "containerization": {
                "required_categories": ["container", "orchestration"],
                "min_entries_per_category": 1,
            },
        }

        catalog_entries = catalog_manager.get_all_entries()
        category_counts = {}

        # Count entries by category
        for entry in catalog_entries.values():
            if hasattr(entry, "category") and entry.category:
                category = entry.category
                category_counts[category] = category_counts.get(category, 0) + 1

        domain_coverage = {}

        for domain, requirements in domain_requirements.items():
            covered_categories = 0
            total_categories = len(requirements["required_categories"])

            for category in requirements["required_categories"]:
                count = category_counts.get(category, 0)
                if count >= requirements["min_entries_per_category"]:
                    covered_categories += 1

            coverage = covered_categories / total_categories
            domain_coverage[domain] = {
                "coverage": coverage,
                "covered_categories": covered_categories,
                "total_categories": total_categories,
            }

            # Domain coverage should be reasonable
            assert coverage >= 0.5, f"Low coverage for {domain}: {coverage:.2%}"

        print("Domain Coverage Results:")
        for domain, metrics in domain_coverage.items():
            print(
                f"  {domain}: {metrics['coverage']:.2%} ({metrics['covered_categories']}/{metrics['total_categories']})"
            )

    def test_catalog_maintenance_recommendations(self, consistency_validator):
        """Test generation of catalog maintenance recommendations."""
        report = consistency_validator.validate_catalog_consistency()

        recommendations = []

        # Generate recommendations based on validation results
        if report.missing_integrations:
            recommendations.append(
                {
                    "type": "missing_integrations",
                    "priority": "high",
                    "count": len(report.missing_integrations),
                    "action": "Add missing technology entries or remove invalid references",
                }
            )

        if report.duplicate_aliases:
            recommendations.append(
                {
                    "type": "duplicate_aliases",
                    "priority": "medium",
                    "count": len(report.duplicate_aliases),
                    "action": "Resolve alias conflicts by updating or removing duplicates",
                }
            )

        if report.orphaned_entries:
            recommendations.append(
                {
                    "type": "orphaned_entries",
                    "priority": "low",
                    "count": len(report.orphaned_entries),
                    "action": "Review orphaned entries and add appropriate integrations",
                }
            )

        if report.ecosystem_inconsistencies:
            recommendations.append(
                {
                    "type": "ecosystem_inconsistencies",
                    "priority": "medium",
                    "count": len(report.ecosystem_inconsistencies),
                    "action": "Fix ecosystem classifications and cross-ecosystem integrations",
                }
            )

        # Completeness recommendations
        if report.completeness_score < 0.8:
            recommendations.append(
                {
                    "type": "completeness",
                    "priority": "high",
                    "score": report.completeness_score,
                    "action": "Add missing technologies for common stacks",
                }
            )

        # Consistency recommendations
        if report.consistency_score < 0.9:
            recommendations.append(
                {
                    "type": "consistency",
                    "priority": "high",
                    "score": report.consistency_score,
                    "action": "Fix validation errors in catalog entries",
                }
            )

        # Should generate actionable recommendations
        assert len(recommendations) > 0, "Should generate maintenance recommendations"

        print("Catalog Maintenance Recommendations:")
        for rec in recommendations:
            print(f"  {rec['type']} ({rec['priority']} priority): {rec['action']}")
            if "count" in rec:
                print(f"    Issues: {rec['count']}")
            if "score" in rec:
                print(f"    Score: {rec['score']:.2%}")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])
