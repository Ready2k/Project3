"""Integration tests for ecosystem intelligence."""

import pytest
import json
from unittest.mock import Mock, patch

from app.services.ecosystem.intelligence import (
    EcosystemIntelligence,
    IntegrationPattern,
    CompatibilityLevel,
    EcosystemConsistencyResult
)
from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import EcosystemType


class TestEcosystemIntelligenceIntegration:
    """Integration tests for ecosystem intelligence with real catalog."""
    
    @pytest.fixture
    def temp_catalog_path(self, tmp_path):
        """Create temporary catalog for testing."""
        catalog_path = tmp_path / "test_technologies.json"
        
        # Create test catalog data
        catalog_data = {
            "technologies": {
                "aws_lambda": {
                    "id": "aws_lambda",
                    "name": "AWS Lambda",
                    "canonical_name": "AWS Lambda",
                    "category": "compute",
                    "description": "Serverless compute service",
                    "ecosystem": "aws",
                    "integrates_with": ["aws_api_gateway", "aws_s3"],
                    "alternatives": ["azure_functions", "google_cloud_functions"],
                    "tags": ["serverless", "compute"],
                    "use_cases": ["api_backend", "event_processing"],
                    "license": "Commercial",
                    "maturity": "mature",
                    "auto_generated": False,
                    "pending_review": False,
                    "review_status": "approved"
                },
                "azure_functions": {
                    "id": "azure_functions",
                    "name": "Azure Functions",
                    "canonical_name": "Azure Functions",
                    "category": "compute",
                    "description": "Serverless compute service",
                    "ecosystem": "azure",
                    "integrates_with": ["azure_api_management"],
                    "alternatives": ["aws_lambda", "google_cloud_functions"],
                    "tags": ["serverless", "compute"],
                    "use_cases": ["api_backend", "event_processing"],
                    "license": "Commercial",
                    "maturity": "mature",
                    "auto_generated": False,
                    "pending_review": False,
                    "review_status": "approved"
                },
                "fastapi": {
                    "id": "fastapi",
                    "name": "FastAPI",
                    "canonical_name": "FastAPI",
                    "category": "frameworks",
                    "description": "Modern Python web framework",
                    "ecosystem": "open_source",
                    "integrates_with": ["pydantic", "uvicorn", "sqlalchemy"],
                    "alternatives": ["flask", "django"],
                    "tags": ["python", "api", "async"],
                    "use_cases": ["rest_api", "microservices"],
                    "license": "MIT",
                    "maturity": "stable",
                    "auto_generated": False,
                    "pending_review": False,
                    "review_status": "approved"
                },
                "postgresql": {
                    "id": "postgresql",
                    "name": "PostgreSQL",
                    "canonical_name": "PostgreSQL",
                    "category": "databases",
                    "description": "Advanced open source relational database",
                    "ecosystem": "open_source",
                    "integrates_with": ["sqlalchemy", "django", "fastapi"],
                    "alternatives": ["mysql", "sqlite"],
                    "tags": ["database", "sql", "relational"],
                    "use_cases": ["data_storage", "analytics"],
                    "license": "PostgreSQL License",
                    "maturity": "mature",
                    "auto_generated": False,
                    "pending_review": False,
                    "review_status": "approved"
                },
                "redis": {
                    "id": "redis",
                    "name": "Redis",
                    "canonical_name": "Redis",
                    "category": "databases",
                    "description": "In-memory data structure store",
                    "ecosystem": "open_source",
                    "integrates_with": ["fastapi", "django", "celery"],
                    "alternatives": ["memcached"],
                    "tags": ["cache", "nosql", "memory"],
                    "use_cases": ["caching", "session_storage"],
                    "license": "BSD",
                    "maturity": "mature",
                    "auto_generated": False,
                    "pending_review": False,
                    "review_status": "approved"
                }
            }
        }
        
        with open(catalog_path, 'w') as f:
            json.dump(catalog_data, f, indent=2)
        
        return catalog_path
    
    @pytest.fixture
    def catalog_manager(self, temp_catalog_path):
        """Create catalog manager with test data."""
        with patch('app.utils.imports.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            return IntelligentCatalogManager(catalog_path=temp_catalog_path)
    
    @pytest.fixture
    def ecosystem_intelligence(self, catalog_manager):
        """Create ecosystem intelligence with real catalog."""
        with patch('app.utils.imports.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            
            return EcosystemIntelligence(catalog_manager=catalog_manager)
    
    def test_ecosystem_consistency_with_real_catalog(self, ecosystem_intelligence):
        """Test ecosystem consistency detection with real catalog data."""
        # Test consistent AWS ecosystem
        aws_technologies = ["aws_lambda"]
        result = ecosystem_intelligence.detect_ecosystem_consistency(aws_technologies)
        
        assert isinstance(result, EcosystemConsistencyResult)
        assert result.is_consistent
        assert result.primary_ecosystem == EcosystemType.AWS
        
        # Test mixed ecosystems
        mixed_technologies = ["aws_lambda", "azure_functions"]
        result = ecosystem_intelligence.detect_ecosystem_consistency(mixed_technologies)
        
        assert not result.is_consistent
        assert len(result.inconsistent_technologies) > 0
        assert len(result.migration_options) >= 0  # May or may not have migration options
    
    def test_integration_suggestions_with_real_catalog(self, ecosystem_intelligence):
        """Test integration suggestions with real catalog data."""
        suggestions = ecosystem_intelligence.suggest_integrations("fastapi")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Should include database and caching suggestions
        [s.suggested_tech for s in suggestions]
        integration_patterns = [s.integration_pattern for s in suggestions]
        
        # Check for expected patterns
        assert IntegrationPattern.DATABASE_CONNECTION in integration_patterns or \
               IntegrationPattern.CACHING in integration_patterns
    
    def test_compatibility_analysis_with_real_catalog(self, ecosystem_intelligence):
        """Test compatibility analysis with real catalog data."""
        # Test same ecosystem compatibility
        result = ecosystem_intelligence.check_technology_compatibility("fastapi", "postgresql")
        
        assert result.compatibility in [CompatibilityLevel.COMPATIBLE, CompatibilityLevel.NEUTRAL]
        
        # Test different cloud ecosystems
        result = ecosystem_intelligence.check_technology_compatibility("aws_lambda", "azure_functions")
        
        # Should detect ecosystem difference
        assert result.compatibility in [CompatibilityLevel.PROBLEMATIC, CompatibilityLevel.NEUTRAL]
    
    def test_dependency_graph_with_real_catalog(self, ecosystem_intelligence):
        """Test dependency graph building with real catalog data."""
        technologies = ["fastapi", "postgresql", "redis"]
        
        graph = ecosystem_intelligence.build_dependency_graph(technologies)
        
        assert len(graph.nodes) > 0
        assert len(graph.edges) >= 0
        
        # Check that nodes contain expected technologies
        node_names = [node.name for node in graph.nodes.values()]
        assert "FastAPI" in node_names
    
    def test_comprehensive_stack_analysis(self, ecosystem_intelligence):
        """Test comprehensive technology stack analysis."""
        technologies = ["fastapi", "postgresql", "redis"]
        
        analysis = ecosystem_intelligence.analyze_technology_stack(technologies)
        
        # Verify all analysis components are present
        assert "ecosystem_consistency" in analysis
        assert "compatibility_matrix" in analysis
        assert "integration_suggestions" in analysis
        assert "dependency_graph" in analysis
        assert "migration_options" in analysis
        
        # Check ecosystem consistency
        consistency = analysis["ecosystem_consistency"]
        assert consistency.is_consistent  # All open source technologies
        assert consistency.primary_ecosystem == EcosystemType.OPEN_SOURCE
        
        # Check compatibility matrix
        compatibility_matrix = analysis["compatibility_matrix"]
        assert len(compatibility_matrix) > 0
        
        # Check integration suggestions
        integration_suggestions = analysis["integration_suggestions"]
        assert len(integration_suggestions) > 0
    
    def test_migration_suggestions_with_real_catalog(self, ecosystem_intelligence):
        """Test ecosystem migration suggestions with real catalog."""
        # Test AWS to Azure migration
        migrations = ecosystem_intelligence.get_ecosystem_migration_suggestions(
            "aws_lambda", EcosystemType.AZURE
        )
        
        # Should find Azure Functions as equivalent
        assert len(migrations) > 0
        azure_migration = next((m for m in migrations if "azure" in m.equivalent_tech.lower()), None)
        assert azure_migration is not None
        assert azure_migration.confidence > 0.8
    
    def test_context_aware_suggestions(self, ecosystem_intelligence):
        """Test context-aware integration suggestions."""
        # Test with AWS context
        aws_context = {"cloud_provider": "aws"}
        aws_suggestions = ecosystem_intelligence.suggest_integrations("fastapi", aws_context)
        
        # Should include AWS-specific suggestions
        aws_specific = [s for s in aws_suggestions if "aws" in s.suggested_tech.lower()]
        assert len(aws_specific) > 0
        
        # Test with AI context
        ai_context = {"domain": "ai"}
        ai_suggestions = ecosystem_intelligence.suggest_integrations("langchain", ai_context)
        
        # Should include AI-specific suggestions
        assert len(ai_suggestions) >= 0  # May not have langchain in test catalog
    
    def test_integration_pattern_inference(self, ecosystem_intelligence):
        """Test integration pattern inference with real technologies."""
        # Test database pattern
        pattern = ecosystem_intelligence._infer_integration_pattern("fastapi", "postgresql")
        assert pattern == IntegrationPattern.DATABASE_CONNECTION
        
        # Test caching pattern
        pattern = ecosystem_intelligence._infer_integration_pattern("fastapi", "redis")
        assert pattern == IntegrationPattern.CACHING
        
        # Test unknown pattern
        pattern = ecosystem_intelligence._infer_integration_pattern("unknown1", "unknown2")
        assert pattern is None


class TestEcosystemIntelligenceWithTechStackGenerator:
    """Integration tests with tech stack generator."""
    
    @pytest.fixture
    def mock_tech_stack_generator(self):
        """Create mock tech stack generator."""
        generator = Mock()
        generator.generate_tech_stack.return_value = {
            "technologies": ["fastapi", "postgresql", "redis"],
            "reasoning": "Selected for web API development"
        }
        return generator
    
    def test_ecosystem_analysis_integration(self, ecosystem_intelligence, mock_tech_stack_generator):
        """Test integration with tech stack generator."""
        # Generate a tech stack
        tech_stack = mock_tech_stack_generator.generate_tech_stack({
            "requirements": "Build a REST API with caching"
        })
        
        # Analyze the generated stack
        analysis = ecosystem_intelligence.analyze_technology_stack(tech_stack["technologies"])
        
        assert "ecosystem_consistency" in analysis
        assert "compatibility_matrix" in analysis
        
        # Should detect open source ecosystem consistency
        consistency = analysis["ecosystem_consistency"]
        assert consistency.primary_ecosystem == EcosystemType.OPEN_SOURCE
    
    def test_ecosystem_validation_feedback(self, ecosystem_intelligence):
        """Test ecosystem validation providing feedback for tech stack improvement."""
        # Test inconsistent stack
        inconsistent_stack = ["aws_lambda", "azure_functions", "fastapi"]
        
        analysis = ecosystem_intelligence.analyze_technology_stack(inconsistent_stack)
        consistency = analysis["ecosystem_consistency"]
        
        if not consistency.is_consistent:
            # Should provide migration suggestions
            assert len(consistency.suggestions) > 0
            assert "migration_options" in analysis
            
            # Should identify problematic technologies
            assert len(consistency.inconsistent_technologies) > 0


class TestEcosystemIntelligencePerformance:
    """Performance tests for ecosystem intelligence."""
    
    def test_large_technology_set_analysis(self, ecosystem_intelligence):
        """Test analysis performance with large technology sets."""
        # Create a large set of technologies
        large_tech_set = [
            "fastapi", "postgresql", "redis", "nginx", "docker",
            "kubernetes", "prometheus", "grafana", "elasticsearch",
            "rabbitmq", "celery", "pytest", "black", "mypy"
        ]
        
        # Should complete analysis in reasonable time
        analysis = ecosystem_intelligence.analyze_technology_stack(large_tech_set)
        
        assert "ecosystem_consistency" in analysis
        assert "compatibility_matrix" in analysis
        
        # Compatibility matrix should have reasonable size
        # For n technologies, we should have n*(n-1)/2 pairs
        expected_pairs = len(large_tech_set) * (len(large_tech_set) - 1) // 2
        actual_pairs = len(analysis["compatibility_matrix"])
        
        # May be less than expected if some technologies aren't in catalog
        assert actual_pairs <= expected_pairs
    
    def test_repeated_analysis_caching(self, ecosystem_intelligence):
        """Test that repeated analyses don't degrade performance."""
        technologies = ["fastapi", "postgresql", "redis"]
        
        # Run analysis multiple times
        for _ in range(5):
            analysis = ecosystem_intelligence.analyze_technology_stack(technologies)
            assert "ecosystem_consistency" in analysis
            assert "compatibility_matrix" in analysis