"""Tests for IntelligentCatalogManager."""

import pytest
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch

from app.services.catalog.intelligent_manager import IntelligentCatalogManager
from app.services.catalog.models import EcosystemType, ReviewStatus


class TestIntelligentCatalogManager:
    """Test cases for IntelligentCatalogManager."""
    
    @pytest.fixture
    def temp_catalog_path(self):
        """Create a temporary catalog file path."""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            temp_path = Path(f.name)
        yield temp_path
        # Cleanup
        if temp_path.exists():
            temp_path.unlink()
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger service."""
        with patch('app.services.catalog.intelligent_manager.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            yield mock_logger
    
    @pytest.fixture
    def sample_catalog_data(self):
        """Sample catalog data for testing."""
        return {
            "metadata": {
                "version": "1.0.0",
                "total_technologies": 2
            },
            "technologies": {
                "fastapi": {
                    "id": "fastapi",
                    "name": "FastAPI",
                    "canonical_name": "FastAPI",
                    "category": "frameworks",
                    "description": "Modern web framework",
                    "aliases": ["fast-api"],
                    "ecosystem": "open_source",
                    "confidence_score": 1.0,
                    "pending_review": False,
                    "integrates_with": ["python"],
                    "alternatives": ["django", "flask"],
                    "tags": ["python", "web"],
                    "use_cases": ["api"],
                    "license": "MIT",
                    "maturity": "stable",
                    "auto_generated": False,
                    "review_status": "approved",
                    "mention_count": 10,
                    "selection_count": 5,
                    "validation_errors": []
                },
                "langchain": {
                    "id": "langchain",
                    "name": "LangChain",
                    "canonical_name": "LangChain",
                    "category": "agentic",
                    "description": "LLM framework",
                    "aliases": ["lang-chain"],
                    "ecosystem": "open_source",
                    "confidence_score": 0.9,
                    "pending_review": True,
                    "integrates_with": ["openai"],
                    "alternatives": ["llamaindex"],
                    "tags": ["llm", "ai"],
                    "use_cases": ["chatbots"],
                    "license": "MIT",
                    "maturity": "stable",
                    "auto_generated": True,
                    "review_status": "pending",
                    "mention_count": 8,
                    "selection_count": 3,
                    "validation_errors": []
                }
            }
        }
    
    def test_initialization_with_existing_catalog(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test initialization with existing catalog file."""
        # Write sample data to temp file
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        assert len(manager.technologies) == 2
        assert "fastapi" in manager.technologies
        assert "langchain" in manager.technologies
        
        # Check that indexes are built
        assert "fastapi" in manager.name_index
        assert "fast-api" in manager.name_index
        assert manager.name_index["fastapi"] == "fastapi"
    
    def test_initialization_without_catalog(self, temp_catalog_path, mock_logger):
        """Test initialization when catalog file doesn't exist."""
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Should create default catalog
        assert len(manager.technologies) >= 3  # Default techs
        assert temp_catalog_path.exists()
    
    def test_exact_lookup(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test exact technology lookup."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Test exact name match
        result = manager.lookup_technology("FastAPI")
        assert result is not None
        assert result.match_score == 1.0
        assert result.match_type == "exact"
        assert result.tech_entry.name == "FastAPI"
        
        # Test alias match
        result = manager.lookup_technology("fast-api")
        assert result is not None
        assert result.match_score == 1.0
        assert result.match_type == "exact"
        assert result.tech_entry.name == "FastAPI"
    
    def test_fuzzy_lookup(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test fuzzy technology lookup."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Test fuzzy match
        result = manager.lookup_technology("FastAP", fuzzy_threshold=0.7)
        assert result is not None
        assert result.match_score >= 0.7
        assert result.match_type.startswith("fuzzy")
        assert result.tech_entry.name == "FastAPI"
        
        # Test no match below threshold
        result = manager.lookup_technology("CompletelyDifferent", fuzzy_threshold=0.8)
        assert result is None
    
    def test_auto_add_technology(self, temp_catalog_path, mock_logger):
        """Test auto-adding missing technology."""
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        context = {
            "requirement_text": "We need to use AWS Lambda for serverless functions",
            "domain": "cloud",
            "mentioned_technologies": ["AWS Lambda"]
        }
        
        tech_entry = manager.auto_add_technology("AWS Lambda", context, confidence_score=0.8)
        
        assert tech_entry.name == "AWS Lambda"
        assert tech_entry.auto_generated
        assert tech_entry.pending_review
        assert tech_entry.confidence_score == 0.8
        assert tech_entry.review_status == ReviewStatus.PENDING
        assert tech_entry.source_context is not None
        
        # Should be in catalog now
        assert tech_entry.id in manager.technologies
        
        # Should be findable by lookup
        result = manager.lookup_technology("AWS Lambda")
        assert result is not None
        assert result.tech_entry.name == "AWS Lambda"
    
    def test_category_inference(self, temp_catalog_path, mock_logger):
        """Test technology category inference."""
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Test AWS service
        context = {"requirement_text": "AWS service"}
        category = manager._infer_category("AWS S3", context)
        assert category == "cloud"
        
        # Test framework
        category = manager._infer_category("FastAPI", {})
        assert category == "frameworks"
        
        # Test agentic
        category = manager._infer_category("LangChain", {})
        assert category == "agentic"
        
        # Test database
        category = manager._infer_category("PostgreSQL", {})
        assert category == "databases"
        
        # Test default
        category = manager._infer_category("Unknown Tech", {})
        assert category == "integration"
    
    def test_ecosystem_inference(self, temp_catalog_path, mock_logger):
        """Test technology ecosystem inference."""
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Test AWS
        ecosystem = manager._infer_ecosystem("AWS Lambda", {})
        assert ecosystem == EcosystemType.AWS
        
        # Test Azure
        ecosystem = manager._infer_ecosystem("Azure Functions", {})
        assert ecosystem == EcosystemType.AZURE
        
        # Test GCP
        ecosystem = manager._infer_ecosystem("Google Cloud Functions", {})
        assert ecosystem == EcosystemType.GCP
        
        # Test context-based inference
        context = {"requirement_text": "We use AWS for everything"}
        ecosystem = manager._infer_ecosystem("Some Service", context)
        assert ecosystem == EcosystemType.AWS
        
        # Test no inference
        ecosystem = manager._infer_ecosystem("Generic Tool", {})
        assert ecosystem is None
    
    def test_tech_id_generation(self, temp_catalog_path, mock_logger):
        """Test unique technology ID generation."""
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Test basic ID generation
        tech_id = manager._generate_tech_id("AWS Lambda")
        assert tech_id == "aws_lambda"
        
        # Test special character handling
        tech_id = manager._generate_tech_id("Test-Tech v2.0")
        assert tech_id == "testtech_v20"
        
        # Test uniqueness (add a tech first)
        manager.technologies["test_tech"] = Mock()
        tech_id = manager._generate_tech_id("Test Tech")
        assert tech_id == "test_tech_1"
    
    def test_pending_review_queue(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test getting pending review queue."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        pending = manager.get_pending_review_queue()
        assert len(pending) == 1
        assert pending[0].name == "LangChain"
        assert pending[0].pending_review
    
    def test_technology_approval(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test technology approval workflow."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Test approval
        success = manager.approve_technology("langchain", "test_reviewer", "Looks good")
        assert success
        
        tech = manager.technologies["langchain"]
        assert not tech.pending_review
        assert tech.review_status == ReviewStatus.APPROVED
        assert tech.reviewed_by == "test_reviewer"
        assert tech.review_notes == "Looks good"
        
        # Test approval of non-existent tech
        success = manager.approve_technology("nonexistent", "test_reviewer")
        assert not success
    
    def test_technology_rejection(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test technology rejection workflow."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        success = manager.reject_technology("langchain", "test_reviewer", "Not suitable")
        assert success
        
        tech = manager.technologies["langchain"]
        assert not tech.pending_review
        assert tech.review_status == ReviewStatus.REJECTED
        assert tech.reviewed_by == "test_reviewer"
        assert tech.review_notes == "Not suitable"
    
    def test_technology_update_request(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test requesting technology updates."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        success = manager.request_technology_update("langchain", "test_reviewer", "Needs more info")
        assert success
        
        tech = manager.technologies["langchain"]
        assert tech.pending_review
        assert tech.review_status == ReviewStatus.NEEDS_UPDATE
        assert tech.review_notes == "Needs more info"
    
    def test_technology_update(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test updating technology entries."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        updates = {
            "description": "Updated description",
            "confidence_score": 0.95,
            "tags": ["updated", "tag"]
        }
        
        success = manager.update_technology("fastapi", updates)
        assert success
        
        tech = manager.technologies["fastapi"]
        assert tech.description == "Updated description"
        assert tech.confidence_score == 0.95
        assert tech.tags == ["updated", "tag"]
        assert tech.last_updated is not None
    
    def test_add_technology_alias(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test adding technology aliases."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        success = manager.add_technology_alias("fastapi", "fast_api")
        assert success
        
        tech = manager.technologies["fastapi"]
        assert "fast_api" in tech.aliases
        
        # Should be in index
        assert "fast_api" in manager.name_index
        assert manager.name_index["fast_api"] == "fastapi"
    
    def test_catalog_statistics(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test catalog statistics generation."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        stats = manager.get_catalog_statistics()
        
        assert stats.total_entries == 2
        assert stats.pending_review == 1
        assert stats.auto_generated == 1
        assert stats.by_ecosystem["open_source"] == 2
        assert stats.by_category["frameworks"] == 1
        assert stats.by_category["agentic"] == 1
        assert stats.by_maturity["stable"] == 2
    
    def test_search_technologies(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test technology search functionality."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Test name search
        results = manager.search_technologies("Fast", limit=5)
        assert len(results) > 0
        assert any(result.tech_entry.name == "FastAPI" for result in results)
        
        # Test alias search
        results = manager.search_technologies("lang", limit=5)
        assert len(results) > 0
        assert any(result.tech_entry.name == "LangChain" for result in results)
    
    def test_get_technologies_by_category(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test getting technologies by category."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        frameworks = manager.get_technologies_by_category("frameworks")
        assert len(frameworks) == 1
        assert frameworks[0].name == "FastAPI"
        
        agentic = manager.get_technologies_by_category("agentic")
        assert len(agentic) == 1
        assert agentic[0].name == "LangChain"
    
    def test_get_technologies_by_ecosystem(self, temp_catalog_path, mock_logger, sample_catalog_data):
        """Test getting technologies by ecosystem."""
        with open(temp_catalog_path, 'w') as f:
            json.dump(sample_catalog_data, f)
        
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        open_source = manager.get_technologies_by_ecosystem(EcosystemType.OPEN_SOURCE)
        assert len(open_source) == 2
        
        aws_techs = manager.get_technologies_by_ecosystem(EcosystemType.AWS)
        assert len(aws_techs) == 0
    
    def test_catalog_save_and_load(self, temp_catalog_path, mock_logger):
        """Test catalog persistence."""
        manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Add a technology
        context = {"test": "context"}
        tech = manager.auto_add_technology("Test Tech", context)
        
        # Create new manager instance (should load from file)
        manager2 = IntelligentCatalogManager(temp_catalog_path)
        
        assert tech.id in manager2.technologies
        assert manager2.technologies[tech.id].name == "Test Tech"
        assert manager2.technologies[tech.id].auto_generated