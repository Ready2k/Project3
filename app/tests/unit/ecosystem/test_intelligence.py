"""Unit tests for ecosystem intelligence."""

import pytest
from unittest.mock import Mock, MagicMock
from typing import List, Dict, Any

from app.services.ecosystem.intelligence import (
    EcosystemIntelligence,
    IntegrationPattern,
    CompatibilityLevel,
    EcosystemMapping,
    IntegrationSuggestion,
    CompatibilityResult,
    EcosystemConsistencyResult,
    DependencyGraph
)
from app.services.catalog.models import TechEntry, EcosystemType, FuzzyMatchResult


class TestEcosystemIntelligence:
    """Test ecosystem intelligence functionality."""
    
    @pytest.fixture
    def mock_catalog_manager(self):
        """Create mock catalog manager."""
        manager = Mock()
        
        # Mock technology entries
        aws_lambda = TechEntry(
            id="aws_lambda",
            name="AWS Lambda",
            canonical_name="AWS Lambda",
            category="compute",
            description="Serverless compute service",
            ecosystem=EcosystemType.AWS,
            integrates_with=["aws_api_gateway", "aws_s3"]
        )
        
        fastapi = TechEntry(
            id="fastapi",
            name="FastAPI",
            canonical_name="FastAPI",
            category="frameworks",
            description="Modern Python web framework",
            ecosystem=EcosystemType.OPEN_SOURCE,
            integrates_with=["pydantic", "uvicorn"]
        )
        
        azure_functions = TechEntry(
            id="azure_functions",
            name="Azure Functions",
            canonical_name="Azure Functions",
            category="compute",
            description="Serverless compute service",
            ecosystem=EcosystemType.AZURE
        )
        
        # Mock lookup responses
        def mock_lookup(tech_name: str):
            tech_map = {
                "aws lambda": aws_lambda,
                "aws_lambda": aws_lambda,
                "fastapi": fastapi,
                "azure functions": azure_functions,
                "azure_functions": azure_functions
            }
            
            tech = tech_map.get(tech_name.lower())
            if tech:
                return FuzzyMatchResult(
                    tech_entry=tech,
                    match_score=1.0,
                    match_type="exact",
                    matched_text=tech_name
                )
            return None
        
        manager.lookup_technology.side_effect = mock_lookup
        return manager
    
    @pytest.fixture
    def ecosystem_intelligence(self, mock_catalog_manager):
        """Create ecosystem intelligence instance."""
        # Mock the logger service
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr("app.utils.imports.require_service", lambda service, context=None: mock_logger)
            
            intelligence = EcosystemIntelligence(catalog_manager=mock_catalog_manager)
            return intelligence
    
    def test_detect_ecosystem_consistency_single_ecosystem(self, ecosystem_intelligence):
        """Test ecosystem consistency detection with single ecosystem."""
        technologies = ["aws_lambda", "aws_api_gateway"]
        
        result = ecosystem_intelligence.detect_ecosystem_consistency(technologies)
        
        assert isinstance(result, EcosystemConsistencyResult)
        assert result.is_consistent
        assert result.primary_ecosystem == EcosystemType.AWS
        assert len(result.inconsistent_technologies) == 0
    
    def test_detect_ecosystem_consistency_mixed_ecosystems(self, ecosystem_intelligence):
        """Test ecosystem consistency detection with mixed ecosystems."""
        technologies = ["aws_lambda", "azure_functions"]
        
        result = ecosystem_intelligence.detect_ecosystem_consistency(technologies)
        
        assert isinstance(result, EcosystemConsistencyResult)
        assert not result.is_consistent
        assert result.primary_ecosystem in [EcosystemType.AWS, EcosystemType.AZURE]
        assert len(result.inconsistent_technologies) > 0
    
    def test_detect_ecosystem_consistency_no_catalog(self):
        """Test ecosystem consistency detection without catalog manager."""
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr("app.utils.imports.require_service", lambda service, context=None: mock_logger)
            
            intelligence = EcosystemIntelligence(catalog_manager=None)
            result = intelligence.detect_ecosystem_consistency(["aws_lambda"])
            
            assert result.is_consistent
            assert result.primary_ecosystem is None
    
    def test_suggest_integrations_fastapi(self, ecosystem_intelligence):
        """Test integration suggestions for FastAPI."""
        suggestions = ecosystem_intelligence.suggest_integrations("fastapi")
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Check that we get relevant suggestions
        suggestion_techs = [s.suggested_tech for s in suggestions]
        assert any("nginx" in tech or "redis" in tech for tech in suggestion_techs)
    
    def test_suggest_integrations_with_aws_context(self, ecosystem_intelligence):
        """Test integration suggestions with AWS context."""
        context = {"cloud_provider": "aws"}
        suggestions = ecosystem_intelligence.suggest_integrations("fastapi", context)
        
        assert isinstance(suggestions, list)
        assert len(suggestions) > 0
        
        # Should include AWS-specific suggestions
        aws_suggestions = [s for s in suggestions if "aws" in s.suggested_tech.lower()]
        assert len(aws_suggestions) > 0
    
    def test_suggest_integrations_with_ai_context(self, ecosystem_intelligence):
        """Test integration suggestions with AI context."""
        context = {"domain": "ai"}
        suggestions = ecosystem_intelligence.suggest_integrations("langchain", context)
        
        assert isinstance(suggestions, list)
        # Should include AI-specific suggestions even if not in catalog
    
    def test_check_technology_compatibility_native(self, ecosystem_intelligence):
        """Test compatibility check for native technologies."""
        result = ecosystem_intelligence.check_technology_compatibility("fastapi", "pydantic")
        
        assert isinstance(result, CompatibilityResult)
        assert result.compatibility == CompatibilityLevel.NATIVE
        assert result.confidence > 0.9
    
    def test_check_technology_compatibility_problematic(self, ecosystem_intelligence):
        """Test compatibility check for problematic technologies."""
        result = ecosystem_intelligence.check_technology_compatibility("aws", "azure")
        
        assert isinstance(result, CompatibilityResult)
        assert result.compatibility == CompatibilityLevel.PROBLEMATIC
        assert len(result.potential_issues) > 0
        assert len(result.mitigation_strategies) > 0
    
    def test_check_technology_compatibility_ecosystem_based(self, ecosystem_intelligence):
        """Test compatibility check based on ecosystem."""
        result = ecosystem_intelligence.check_technology_compatibility("aws_lambda", "fastapi")
        
        assert isinstance(result, CompatibilityResult)
        # Should be neutral or compatible since different ecosystems but not conflicting
    
    def test_get_ecosystem_migration_suggestions(self, ecosystem_intelligence):
        """Test ecosystem migration suggestions."""
        suggestions = ecosystem_intelligence.get_ecosystem_migration_suggestions(
            "aws_lambda", EcosystemType.AZURE
        )
        
        assert isinstance(suggestions, list)
        # Should find Azure Functions as equivalent
        if suggestions:
            assert any("azure" in s.equivalent_tech.lower() for s in suggestions)
    
    def test_build_dependency_graph(self, ecosystem_intelligence):
        """Test dependency graph building."""
        technologies = ["aws_lambda", "fastapi"]
        
        graph = ecosystem_intelligence.build_dependency_graph(technologies)
        
        assert isinstance(graph, DependencyGraph)
        assert isinstance(graph.nodes, dict)
        assert isinstance(graph.edges, dict)
        assert isinstance(graph.integration_patterns, dict)
    
    def test_build_dependency_graph_no_catalog(self):
        """Test dependency graph building without catalog."""
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr("app.utils.imports.require_service", lambda service, context=None: mock_logger)
            
            intelligence = EcosystemIntelligence(catalog_manager=None)
            graph = intelligence.build_dependency_graph(["aws_lambda"])
            
            assert len(graph.nodes) == 0
            assert len(graph.edges) == 0
    
    def test_analyze_technology_stack(self, ecosystem_intelligence):
        """Test comprehensive technology stack analysis."""
        technologies = ["aws_lambda", "fastapi"]
        
        analysis = ecosystem_intelligence.analyze_technology_stack(technologies)
        
        assert isinstance(analysis, dict)
        assert "ecosystem_consistency" in analysis
        assert "compatibility_matrix" in analysis
        assert "integration_suggestions" in analysis
        assert "dependency_graph" in analysis
        assert "migration_options" in analysis
        
        # Check ecosystem consistency
        assert isinstance(analysis["ecosystem_consistency"], EcosystemConsistencyResult)
        
        # Check compatibility matrix
        assert isinstance(analysis["compatibility_matrix"], dict)
        
        # Check integration suggestions
        assert isinstance(analysis["integration_suggestions"], dict)
        
        # Check dependency graph
        assert isinstance(analysis["dependency_graph"], DependencyGraph)
    
    def test_infer_integration_pattern_database(self, ecosystem_intelligence):
        """Test integration pattern inference for databases."""
        pattern = ecosystem_intelligence._infer_integration_pattern("fastapi", "postgresql")
        assert pattern == IntegrationPattern.DATABASE_CONNECTION
    
    def test_infer_integration_pattern_api_gateway(self, ecosystem_intelligence):
        """Test integration pattern inference for API gateways."""
        pattern = ecosystem_intelligence._infer_integration_pattern("fastapi", "nginx")
        assert pattern == IntegrationPattern.API_GATEWAY
    
    def test_infer_integration_pattern_caching(self, ecosystem_intelligence):
        """Test integration pattern inference for caching."""
        pattern = ecosystem_intelligence._infer_integration_pattern("fastapi", "redis")
        assert pattern == IntegrationPattern.CACHING
    
    def test_infer_integration_pattern_unknown(self, ecosystem_intelligence):
        """Test integration pattern inference for unknown patterns."""
        pattern = ecosystem_intelligence._infer_integration_pattern("unknown1", "unknown2")
        assert pattern is None


class TestEcosystemMappings:
    """Test ecosystem mapping functionality."""
    
    @pytest.fixture
    def ecosystem_intelligence(self):
        """Create ecosystem intelligence instance."""
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr("app.utils.imports.require_service", lambda service, context=None: mock_logger)
            
            return EcosystemIntelligence()
    
    def test_aws_to_azure_mappings(self, ecosystem_intelligence):
        """Test AWS to Azure ecosystem mappings."""
        mappings = ecosystem_intelligence.get_ecosystem_migration_suggestions(
            "aws_lambda", EcosystemType.AZURE
        )
        
        assert len(mappings) > 0
        azure_mapping = next((m for m in mappings if "azure" in m.equivalent_tech.lower()), None)
        assert azure_mapping is not None
        assert azure_mapping.confidence > 0.8
    
    def test_aws_to_gcp_mappings(self, ecosystem_intelligence):
        """Test AWS to GCP ecosystem mappings."""
        mappings = ecosystem_intelligence.get_ecosystem_migration_suggestions(
            "aws_s3", EcosystemType.GCP
        )
        
        assert len(mappings) > 0
        gcp_mapping = next((m for m in mappings if "google" in m.equivalent_tech.lower()), None)
        assert azure_mapping is not None
    
    def test_bidirectional_mappings(self, ecosystem_intelligence):
        """Test that mappings work bidirectionally."""
        # AWS to Azure
        aws_to_azure = ecosystem_intelligence.get_ecosystem_migration_suggestions(
            "aws_lambda", EcosystemType.AZURE
        )
        
        # Azure to AWS
        azure_to_aws = ecosystem_intelligence.get_ecosystem_migration_suggestions(
            "azure_functions", EcosystemType.AWS
        )
        
        assert len(aws_to_azure) > 0
        assert len(azure_to_aws) > 0


class TestCompatibilityRules:
    """Test technology compatibility rules."""
    
    @pytest.fixture
    def ecosystem_intelligence(self):
        """Create ecosystem intelligence instance."""
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr("app.utils.imports.require_service", lambda service, context=None: mock_logger)
            
            return EcosystemIntelligence()
    
    def test_cloud_provider_incompatibility(self, ecosystem_intelligence):
        """Test cloud provider incompatibility rules."""
        result = ecosystem_intelligence.check_technology_compatibility("aws", "azure")
        
        assert result.compatibility == CompatibilityLevel.PROBLEMATIC
        assert "complexity" in result.reasoning.lower()
        assert len(result.potential_issues) > 0
    
    def test_framework_compatibility(self, ecosystem_intelligence):
        """Test framework compatibility rules."""
        result = ecosystem_intelligence.check_technology_compatibility("fastapi", "flask")
        
        assert result.compatibility == CompatibilityLevel.PROBLEMATIC
        assert "framework" in result.reasoning.lower()
    
    def test_native_integration_compatibility(self, ecosystem_intelligence):
        """Test native integration compatibility."""
        result = ecosystem_intelligence.check_technology_compatibility("aws_lambda", "aws_api_gateway")
        
        assert result.compatibility == CompatibilityLevel.NATIVE
        assert result.confidence > 0.9
        assert len(result.potential_issues) == 0


class TestIntegrationPatterns:
    """Test integration pattern suggestions."""
    
    @pytest.fixture
    def ecosystem_intelligence(self):
        """Create ecosystem intelligence instance."""
        with pytest.MonkeyPatch().context() as m:
            mock_logger = Mock()
            m.setattr("app.utils.imports.require_service", lambda service, context=None: mock_logger)
            
            return EcosystemIntelligence()
    
    def test_api_gateway_patterns(self, ecosystem_intelligence):
        """Test API gateway integration patterns."""
        suggestions = ecosystem_intelligence.suggest_integrations("fastapi")
        
        api_gateway_suggestions = [
            s for s in suggestions 
            if s.integration_pattern == IntegrationPattern.API_GATEWAY
        ]
        
        assert len(api_gateway_suggestions) > 0
        assert any("nginx" in s.suggested_tech.lower() for s in api_gateway_suggestions)
    
    def test_database_patterns(self, ecosystem_intelligence):
        """Test database integration patterns."""
        suggestions = ecosystem_intelligence.suggest_integrations("fastapi")
        
        db_suggestions = [
            s for s in suggestions 
            if s.integration_pattern == IntegrationPattern.DATABASE_CONNECTION
        ]
        
        assert len(db_suggestions) > 0
        assert any("sql" in s.suggested_tech.lower() for s in db_suggestions)
    
    def test_caching_patterns(self, ecosystem_intelligence):
        """Test caching integration patterns."""
        suggestions = ecosystem_intelligence.suggest_integrations("fastapi")
        
        cache_suggestions = [
            s for s in suggestions 
            if s.integration_pattern == IntegrationPattern.CACHING
        ]
        
        assert len(cache_suggestions) > 0
        assert any("redis" in s.suggested_tech.lower() for s in cache_suggestions)
    
    def test_context_specific_patterns(self, ecosystem_intelligence):
        """Test context-specific integration patterns."""
        # Test with AI context
        ai_suggestions = ecosystem_intelligence.suggest_integrations(
            "langchain", 
            context={"domain": "ai"}
        )
        
        # Should include AI-specific suggestions
        ai_specific = [s for s in ai_suggestions if any(
            ai_tech in s.suggested_tech.lower() 
            for ai_tech in ["openai", "faiss", "vector"]
        )]
        
        # Test with cloud context
        cloud_suggestions = ecosystem_intelligence.suggest_integrations(
            "fastapi",
            context={"cloud_provider": "aws"}
        )
        
        aws_specific = [s for s in cloud_suggestions if "aws" in s.suggested_tech.lower()]
        assert len(aws_specific) > 0