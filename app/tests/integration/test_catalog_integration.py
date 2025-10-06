"""Integration tests for catalog management system."""

import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, Mock

from app.services.catalog import (
    IntelligentCatalogManager, CatalogValidator, ReviewWorkflow,
    TechEntry, EcosystemType, ReviewStatus
)


class TestCatalogIntegration:
    """Integration tests for the complete catalog management system."""
    
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
        with patch('app.services.catalog.intelligent_manager.require_service') as mock_require1, \
             patch('app.services.catalog.validator.require_service') as mock_require2, \
             patch('app.services.catalog.review_workflow.require_service') as mock_require3:
            
            mock_logger = Mock()
            mock_require1.return_value = mock_logger
            mock_require2.return_value = mock_logger
            mock_require3.return_value = mock_logger
            yield mock_logger
    
    def test_complete_workflow_auto_addition_to_approval(self, temp_catalog_path, mock_logger):
        """Test complete workflow from auto-addition to approval."""
        # Initialize catalog manager
        catalog_manager = IntelligentCatalogManager(temp_catalog_path)
        validator = CatalogValidator()
        review_workflow = ReviewWorkflow(catalog_manager)
        
        # Step 1: Auto-add a new technology
        context = {
            "requirement_text": "We need to use AWS Lambda for serverless functions",
            "domain": "cloud",
            "mentioned_technologies": ["AWS Lambda"]
        }
        
        tech_entry = catalog_manager.auto_add_technology("AWS Lambda", context, confidence_score=0.8)
        
        # Verify auto-addition
        assert tech_entry.name == "AWS Lambda"
        assert tech_entry.auto_generated
        assert tech_entry.pending_review
        assert tech_entry.review_status == ReviewStatus.PENDING
        assert tech_entry.ecosystem == EcosystemType.AWS
        assert tech_entry.category == "cloud"
        
        # Step 2: Validate the technology
        validation_result = validator.validate_technology_entry(tech_entry)
        
        # Should be valid but may have suggestions
        assert validation_result.is_valid
        
        # Step 3: Get review queue
        queue = review_workflow.get_review_queue()
        
        assert len(queue) == 1
        assert queue[0].tech_entry.name == "AWS Lambda"
        assert queue[0].validation_result.is_valid
        
        # Step 4: Approve the technology
        success = review_workflow.approve_technology(tech_entry.id, "test_reviewer", "Looks good")
        
        assert success
        
        # Verify approval
        approved_tech = catalog_manager.get_technology_by_id(tech_entry.id)
        assert not approved_tech.pending_review
        assert approved_tech.review_status == ReviewStatus.APPROVED
        assert approved_tech.reviewed_by == "test_reviewer"
        
        # Step 5: Verify it's no longer in review queue
        queue_after_approval = review_workflow.get_review_queue()
        assert len(queue_after_approval) == 0
    
    def test_fuzzy_matching_and_alias_management(self, temp_catalog_path, mock_logger):
        """Test fuzzy matching and alias management integration."""
        catalog_manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Add a technology with aliases
        tech_entry = TechEntry(
            id="fastapi",
            name="FastAPI",
            canonical_name="FastAPI",
            category="frameworks",
            description="Modern web framework for Python",
            aliases=["fast-api", "fast_api"],
            ecosystem=EcosystemType.OPEN_SOURCE
        )
        
        catalog_manager.technologies["fastapi"] = tech_entry
        catalog_manager._rebuild_indexes()
        
        # Test exact lookup
        result = catalog_manager.lookup_technology("FastAPI")
        assert result is not None
        assert result.match_score == 1.0
        assert result.match_type == "exact"
        
        # Test alias lookup
        result = catalog_manager.lookup_technology("fast-api")
        assert result is not None
        assert result.match_score == 1.0
        assert result.match_type == "exact"
        
        # Test fuzzy lookup
        result = catalog_manager.lookup_technology("FastAP", fuzzy_threshold=0.7)
        assert result is not None
        assert result.match_score >= 0.7
        assert result.match_type.startswith("fuzzy")
        
        # Add new alias
        success = catalog_manager.add_technology_alias("fastapi", "fastapi_framework")
        assert success
        
        # Verify new alias works
        result = catalog_manager.lookup_technology("fastapi_framework")
        assert result is not None
        assert result.tech_entry.name == "FastAPI"
    
    def test_validation_and_consistency_checking(self, temp_catalog_path, mock_logger):
        """Test validation and consistency checking integration."""
        catalog_manager = IntelligentCatalogManager(temp_catalog_path)
        validator = CatalogValidator()
        
        # Add technologies with various issues
        tech1 = TechEntry(
            id="tech1",
            name="Technology One",
            canonical_name="Technology One",
            category="frameworks",
            description="First technology",
            integrates_with=["Technology Two", "Nonexistent Tech"]  # Broken reference
        )
        
        tech2 = TechEntry(
            id="tech2",
            name="Technology One",  # Duplicate name
            canonical_name="Technology One",
            category="frameworks",
            description="Second technology"
        )
        
        catalog_manager.technologies["tech1"] = tech1
        catalog_manager.technologies["tech2"] = tech2
        catalog_manager._rebuild_indexes()
        
        # Validate individual entries
        result1 = validator.validate_technology_entry(tech1)
        result2 = validator.validate_technology_entry(tech2)
        
        assert result1.is_valid  # Individual validation passes
        assert result2.is_valid
        
        # Check catalog consistency
        consistency_checks = validator.validate_catalog_consistency(catalog_manager.technologies)
        
        # Should find duplicate names
        duplicate_check = next((c for c in consistency_checks if "duplicate_names" in c.check_name), None)
        assert duplicate_check is not None
        assert not duplicate_check.passed
        
        # Should find broken integration reference
        integration_check = next((c for c in consistency_checks if "integration_references" in c.check_name), None)
        assert integration_check is not None
        assert not integration_check.passed
        
        # Assess overall health
        health = validator.assess_catalog_health(catalog_manager.technologies)
        assert health.overall_score < 1.0  # Should be penalized for issues
        assert health.errors > 0
    
    def test_bulk_operations_and_statistics(self, temp_catalog_path, mock_logger):
        """Test bulk operations and statistics integration."""
        catalog_manager = IntelligentCatalogManager(temp_catalog_path)
        review_workflow = ReviewWorkflow(catalog_manager)
        
        # Add multiple pending technologies
        pending_techs = []
        for i in range(5):
            context = {"test": f"context_{i}"}
            tech = catalog_manager.auto_add_technology(f"Technology {i}", context)
            pending_techs.append(tech)
        
        # Get statistics
        stats = catalog_manager.get_catalog_statistics()
        assert stats.total_entries >= 5
        assert stats.pending_review == 5
        assert stats.auto_generated == 5
        
        # Get review statistics
        review_stats = review_workflow.get_review_statistics()
        assert review_stats["total_pending"] == 5
        
        # Bulk approve some technologies
        tech_ids = [tech.id for tech in pending_techs[:3]]
        results = review_workflow.bulk_approve_technologies(tech_ids, "bulk_reviewer")
        
        assert sum(results.values()) == 3  # All should succeed
        
        # Verify statistics updated
        updated_stats = catalog_manager.get_catalog_statistics()
        assert updated_stats.pending_review == 2  # 5 - 3 approved
        
        updated_review_stats = review_workflow.get_review_statistics()
        assert updated_review_stats["total_pending"] == 2
    
    def test_auto_approval_workflow(self, temp_catalog_path, mock_logger):
        """Test auto-approval workflow integration."""
        catalog_manager = IntelligentCatalogManager(temp_catalog_path)
        review_workflow = ReviewWorkflow(catalog_manager)
        
        # Add high confidence technology
        context = {"high_quality": "context"}
        high_conf_tech = catalog_manager.auto_add_technology(
            "High Confidence Tech", 
            context, 
            confidence_score=0.95
        )
        
        # Add low confidence technology
        low_conf_tech = catalog_manager.auto_add_technology(
            "Low Confidence Tech", 
            context, 
            confidence_score=0.5
        )
        
        # Run auto-approval
        approved = review_workflow.auto_approve_high_confidence_entries(confidence_threshold=0.9)
        
        assert len(approved) == 1
        assert approved[0] == high_conf_tech.id
        
        # Verify high confidence tech is approved
        approved_tech = catalog_manager.get_technology_by_id(high_conf_tech.id)
        assert not approved_tech.pending_review
        assert approved_tech.review_status == ReviewStatus.APPROVED
        
        # Verify low confidence tech is still pending
        pending_tech = catalog_manager.get_technology_by_id(low_conf_tech.id)
        assert pending_tech.pending_review
        assert pending_tech.review_status == ReviewStatus.PENDING
    
    def test_search_and_filtering_integration(self, temp_catalog_path, mock_logger):
        """Test search and filtering integration."""
        catalog_manager = IntelligentCatalogManager(temp_catalog_path)
        
        # Add technologies in different categories and ecosystems
        aws_tech = TechEntry(
            id="aws_lambda",
            name="AWS Lambda",
            canonical_name="AWS Lambda",
            category="cloud",
            description="AWS serverless compute",
            ecosystem=EcosystemType.AWS,
            tags=["serverless", "compute"]
        )
        
        python_tech = TechEntry(
            id="fastapi",
            name="FastAPI",
            canonical_name="FastAPI",
            category="frameworks",
            description="Python web framework",
            ecosystem=EcosystemType.OPEN_SOURCE,
            tags=["python", "web", "api"]
        )
        
        catalog_manager.technologies["aws_lambda"] = aws_tech
        catalog_manager.technologies["fastapi"] = python_tech
        catalog_manager._rebuild_indexes()
        
        # Test category filtering
        cloud_techs = catalog_manager.get_technologies_by_category("cloud")
        assert len(cloud_techs) == 1
        assert cloud_techs[0].name == "AWS Lambda"
        
        framework_techs = catalog_manager.get_technologies_by_category("frameworks")
        assert len(framework_techs) == 1
        assert framework_techs[0].name == "FastAPI"
        
        # Test ecosystem filtering
        aws_techs = catalog_manager.get_technologies_by_ecosystem(EcosystemType.AWS)
        assert len(aws_techs) == 1
        assert aws_techs[0].name == "AWS Lambda"
        
        open_source_techs = catalog_manager.get_technologies_by_ecosystem(EcosystemType.OPEN_SOURCE)
        assert len(open_source_techs) == 1
        assert open_source_techs[0].name == "FastAPI"
        
        # Test search
        search_results = catalog_manager.search_technologies("lambda")
        assert len(search_results) >= 1
        assert any(result.tech_entry.name == "AWS Lambda" for result in search_results)
        
        api_results = catalog_manager.search_technologies("api")
        assert len(api_results) >= 1
        assert any(result.tech_entry.name == "FastAPI" for result in api_results)
    
    def test_persistence_and_reload(self, temp_catalog_path, mock_logger):
        """Test catalog persistence and reloading."""
        # Create first manager instance
        catalog_manager1 = IntelligentCatalogManager(temp_catalog_path)
        
        # Add some technologies
        context = {"test": "persistence"}
        tech1 = catalog_manager1.auto_add_technology("Persistent Tech 1", context)
        tech2 = catalog_manager1.auto_add_technology("Persistent Tech 2", context)
        
        # Approve one technology
        catalog_manager1.approve_technology(tech1.id, "test_reviewer", "Approved for persistence test")
        
        # Create second manager instance (should load from file)
        catalog_manager2 = IntelligentCatalogManager(temp_catalog_path)
        
        # Verify technologies are loaded
        assert len(catalog_manager2.technologies) >= 2
        assert tech1.id in catalog_manager2.technologies
        assert tech2.id in catalog_manager2.technologies
        
        # Verify state is preserved
        loaded_tech1 = catalog_manager2.get_technology_by_id(tech1.id)
        loaded_tech2 = catalog_manager2.get_technology_by_id(tech2.id)
        
        assert loaded_tech1.name == "Persistent Tech 1"
        assert not loaded_tech1.pending_review  # Was approved
        assert loaded_tech1.review_status == ReviewStatus.APPROVED
        
        assert loaded_tech2.name == "Persistent Tech 2"
        assert loaded_tech2.pending_review  # Still pending
        assert loaded_tech2.review_status == ReviewStatus.PENDING
        
        # Verify indexes are rebuilt
        result = catalog_manager2.lookup_technology("Persistent Tech 1")
        assert result is not None
        assert result.tech_entry.name == "Persistent Tech 1"