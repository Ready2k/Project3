"""Tests for ReviewWorkflow."""

import pytest
from datetime import datetime, timedelta
from unittest.mock import Mock, patch, MagicMock

from app.services.catalog.review_workflow import (
    ReviewWorkflow, ReviewQueueItem, ReviewPriority, ReviewAction
)
from app.services.catalog.models import TechEntry, ReviewStatus, ValidationResult
from app.services.catalog.intelligent_manager import IntelligentCatalogManager


class TestReviewWorkflow:
    """Test cases for ReviewWorkflow."""
    
    @pytest.fixture
    def mock_catalog_manager(self):
        """Create a mock catalog manager."""
        manager = Mock(spec=IntelligentCatalogManager)
        manager.technologies = {}
        return manager
    
    @pytest.fixture
    def mock_logger(self):
        """Mock logger service."""
        with patch('app.services.catalog.review_workflow.require_service') as mock_require:
            mock_logger = Mock()
            mock_require.return_value = mock_logger
            yield mock_logger
    
    @pytest.fixture
    def review_workflow(self, mock_catalog_manager, mock_logger):
        """Create a ReviewWorkflow instance."""
        with patch('app.services.catalog.review_workflow.CatalogValidator') as mock_validator_class:
            mock_validator = Mock()
            mock_validator_class.return_value = mock_validator
            return ReviewWorkflow(mock_catalog_manager)
    
    @pytest.fixture
    def sample_pending_tech(self):
        """Create a sample pending technology."""
        return TechEntry(
            id="pending_tech",
            name="Pending Technology",
            canonical_name="Pending Technology",
            category="frameworks",
            description="A technology pending review",
            auto_generated=True,
            pending_review=True,
            confidence_score=0.7,
            added_date=datetime.now() - timedelta(days=5)
        )
    
    @pytest.fixture
    def urgent_pending_tech(self):
        """Create an urgent pending technology."""
        return TechEntry(
            id="urgent_tech",
            name="Urgent Technology",
            canonical_name="Urgent Technology",
            category="frameworks",
            description="An urgent technology",
            auto_generated=True,
            pending_review=True,
            confidence_score=0.3,  # Low confidence
            added_date=datetime.now() - timedelta(days=25)  # Very old
        )
    
    def test_calculate_priority_urgent(self, review_workflow):
        """Test priority calculation for urgent items."""
        # Test urgent due to age
        tech = TechEntry(
            id="old_tech",
            name="Old Technology",
            canonical_name="Old Technology",
            category="frameworks",
            description="Old technology"
        )
        
        validation_result = ValidationResult(is_valid=True)
        priority = review_workflow._calculate_priority(tech, 25, validation_result)  # 25 days old
        assert priority == ReviewPriority.URGENT
        
        # Test urgent due to errors
        validation_result = ValidationResult(is_valid=False, errors=["Critical error"])
        priority = review_workflow._calculate_priority(tech, 5, validation_result)
        assert priority == ReviewPriority.URGENT
    
    def test_calculate_priority_high(self, review_workflow):
        """Test priority calculation for high priority items."""
        tech = TechEntry(
            id="tech",
            name="Technology",
            canonical_name="Technology",
            category="frameworks",
            description="Technology"
        )
        
        # Test high due to warnings
        validation_result = ValidationResult(is_valid=True, warnings=["Warning"])
        priority = review_workflow._calculate_priority(tech, 5, validation_result)
        assert priority == ReviewPriority.HIGH
        
        # Test high due to moderate age
        validation_result = ValidationResult(is_valid=True)
        priority = review_workflow._calculate_priority(tech, 15, validation_result)  # 15 days old
        assert priority == ReviewPriority.HIGH
    
    def test_calculate_priority_medium(self, review_workflow):
        """Test priority calculation for medium priority items."""
        tech = TechEntry(
            id="tech",
            name="Technology",
            canonical_name="Technology",
            category="frameworks",
            description="Technology",
            confidence_score=0.5  # Low confidence
        )
        
        validation_result = ValidationResult(is_valid=True)
        priority = review_workflow._calculate_priority(tech, 8, validation_result)  # 8 days old
        assert priority == ReviewPriority.MEDIUM
    
    def test_calculate_priority_low(self, review_workflow):
        """Test priority calculation for low priority items."""
        tech = TechEntry(
            id="tech",
            name="Technology",
            canonical_name="Technology",
            category="frameworks",
            description="Technology",
            confidence_score=0.9
        )
        
        validation_result = ValidationResult(is_valid=True)
        priority = review_workflow._calculate_priority(tech, 2, validation_result)  # 2 days old
        assert priority == ReviewPriority.LOW
    
    def test_get_review_queue(self, review_workflow, mock_catalog_manager, sample_pending_tech, urgent_pending_tech):
        """Test getting the review queue."""
        # Setup mock catalog manager
        mock_catalog_manager.get_pending_review_queue.return_value = [sample_pending_tech, urgent_pending_tech]
        
        queue = review_workflow.get_review_queue()
        
        assert len(queue) == 2
        assert all(isinstance(item, ReviewQueueItem) for item in queue)
        
        # Should be sorted by priority (urgent first)
        assert queue[0].priority == ReviewPriority.URGENT
        assert queue[1].priority in [ReviewPriority.MEDIUM, ReviewPriority.LOW]
    
    def test_get_review_queue_with_filter(self, review_workflow, mock_catalog_manager, sample_pending_tech, urgent_pending_tech):
        """Test getting review queue with priority filter."""
        mock_catalog_manager.get_pending_review_queue.return_value = [sample_pending_tech, urgent_pending_tech]
        
        # Filter for urgent only
        queue = review_workflow.get_review_queue(priority_filter=ReviewPriority.URGENT)
        
        assert len(queue) == 1
        assert queue[0].priority == ReviewPriority.URGENT
        assert queue[0].tech_entry.name == "Urgent Technology"
    
    def test_get_review_queue_with_limit(self, review_workflow, mock_catalog_manager, sample_pending_tech, urgent_pending_tech):
        """Test getting review queue with limit."""
        mock_catalog_manager.get_pending_review_queue.return_value = [sample_pending_tech, urgent_pending_tech]
        
        queue = review_workflow.get_review_queue(limit=1)
        
        assert len(queue) == 1
        # Should get the highest priority item
        assert queue[0].priority == ReviewPriority.URGENT
    
    def test_start_review_session(self, review_workflow, mock_logger):
        """Test starting a review session."""
        session_id = review_workflow.start_review_session("test_reviewer")
        
        assert session_id.startswith("review_")
        assert "test_reviewer" in session_id
        mock_logger.info.assert_called_once()
    
    def test_approve_technology(self, review_workflow, mock_catalog_manager):
        """Test approving a technology."""
        mock_catalog_manager.approve_technology.return_value = True
        
        success = review_workflow.approve_technology("tech_id", "reviewer", "Looks good")
        
        assert success
        mock_catalog_manager.approve_technology.assert_called_once_with("tech_id", "reviewer", "Looks good")
    
    def test_reject_technology(self, review_workflow, mock_catalog_manager):
        """Test rejecting a technology."""
        mock_catalog_manager.reject_technology.return_value = True
        
        success = review_workflow.reject_technology("tech_id", "reviewer", "Not suitable")
        
        assert success
        mock_catalog_manager.reject_technology.assert_called_once_with("tech_id", "reviewer", "Not suitable")
    
    def test_request_technology_update(self, review_workflow, mock_catalog_manager):
        """Test requesting technology update."""
        mock_catalog_manager.request_technology_update.return_value = True
        
        success = review_workflow.request_technology_update("tech_id", "reviewer", "Needs more info")
        
        assert success
        mock_catalog_manager.request_technology_update.assert_called_once_with("tech_id", "reviewer", "Needs more info")
    
    def test_bulk_approve_technologies(self, review_workflow, mock_catalog_manager):
        """Test bulk approving technologies."""
        mock_catalog_manager.approve_technology.side_effect = [True, False, True]
        
        tech_ids = ["tech1", "tech2", "tech3"]
        results = review_workflow.bulk_approve_technologies(tech_ids, "reviewer", "Bulk approval")
        
        assert len(results) == 3
        assert results["tech1"] is True
        assert results["tech2"] is False
        assert results["tech3"] is True
        
        assert mock_catalog_manager.approve_technology.call_count == 3
    
    def test_auto_approve_high_confidence_entries(self, review_workflow, mock_catalog_manager):
        """Test auto-approving high confidence entries."""
        # Create high confidence pending tech
        high_confidence_tech = TechEntry(
            id="high_conf_tech",
            name="High Confidence Tech",
            canonical_name="High Confidence Tech",
            category="frameworks",
            description="High confidence technology",
            auto_generated=True,
            pending_review=True,
            confidence_score=0.95,
            added_date=datetime.now() - timedelta(days=2)
        )
        
        mock_catalog_manager.get_pending_review_queue.return_value = [high_confidence_tech]
        mock_catalog_manager.approve_technology.return_value = True
        
        approved = review_workflow.auto_approve_high_confidence_entries(confidence_threshold=0.9)
        
        assert len(approved) == 1
        assert approved[0] == "high_conf_tech"
        mock_catalog_manager.approve_technology.assert_called_once()
    
    def test_get_review_statistics(self, review_workflow, mock_catalog_manager, sample_pending_tech, urgent_pending_tech):
        """Test getting review statistics."""
        mock_catalog_manager.get_pending_review_queue.return_value = [sample_pending_tech, urgent_pending_tech]
        
        stats = review_workflow.get_review_statistics()
        
        assert stats["total_pending"] == 2
        assert "by_priority" in stats
        assert "urgent" in stats["by_priority"]
        assert "avg_days_pending" in stats
        assert "oldest_pending" in stats
        assert "validation_issues" in stats
        assert "confidence_distribution" in stats
    
    def test_get_review_recommendations(self, review_workflow, mock_catalog_manager):
        """Test getting review recommendations."""
        # Create many pending technologies to trigger recommendations
        many_pending = []
        for i in range(60):  # More than max_queue_size (50)
            tech = TechEntry(
                id=f"tech{i}",
                name=f"Technology {i}",
                canonical_name=f"Technology {i}",
                category="frameworks",
                description=f"Technology {i}",
                pending_review=True,
                added_date=datetime.now() - timedelta(days=35)  # Very old
            )
            many_pending.append(tech)
        
        mock_catalog_manager.get_pending_review_queue.return_value = many_pending
        
        recommendations = review_workflow.get_review_recommendations()
        
        assert len(recommendations) > 0
        assert any("queue is large" in rec.lower() for rec in recommendations)
        assert any("oldest pending" in rec.lower() for rec in recommendations)
    
    def test_generate_review_report(self, review_workflow, mock_catalog_manager):
        """Test generating review report."""
        mock_catalog_manager.get_pending_review_queue.return_value = []
        
        report = review_workflow.generate_review_report(reviewer="test_reviewer", days_back=30)
        
        assert "report_period" in report
        assert "generated_at" in report
        assert "reviewer_filter" in report
        assert "current_queue_stats" in report
        assert "recommendations" in report
        assert report["reviewer_filter"] == "test_reviewer"
    
    def test_cleanup_old_rejected_entries(self, review_workflow, mock_catalog_manager):
        """Test cleaning up old rejected entries."""
        # Create old rejected technology
        old_rejected = TechEntry(
            id="old_rejected",
            name="Old Rejected Tech",
            canonical_name="Old Rejected Tech",
            category="frameworks",
            description="Old rejected technology",
            review_status=ReviewStatus.REJECTED,
            reviewed_date=datetime.now() - timedelta(days=100)  # Very old
        )
        
        # Create recent rejected technology (should not be cleaned)
        recent_rejected = TechEntry(
            id="recent_rejected",
            name="Recent Rejected Tech",
            canonical_name="Recent Rejected Tech",
            category="frameworks",
            description="Recent rejected technology",
            review_status=ReviewStatus.REJECTED,
            reviewed_date=datetime.now() - timedelta(days=30)  # Recent
        )
        
        mock_catalog_manager.technologies = {
            "old_rejected": old_rejected,
            "recent_rejected": recent_rejected
        }
        mock_catalog_manager._rebuild_indexes = Mock()
        mock_catalog_manager._save_catalog = Mock()
        
        cleaned_up = review_workflow.cleanup_old_rejected_entries(days_old=90)
        
        assert len(cleaned_up) == 1
        assert cleaned_up[0] == "old_rejected"
        assert "old_rejected" not in mock_catalog_manager.technologies
        assert "recent_rejected" in mock_catalog_manager.technologies
        
        mock_catalog_manager._rebuild_indexes.assert_called_once()
        mock_catalog_manager._save_catalog.assert_called_once()
    
    def test_review_queue_item_auto_priority_score(self):
        """Test ReviewQueueItem auto priority score calculation."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="frameworks",
            description="Test technology",
            confidence_score=0.4,  # Low confidence
            mention_count=10,  # High mentions
            added_date=datetime.now() - timedelta(days=20)  # Old
        )
        
        validation_result = ValidationResult(
            is_valid=False,
            errors=["Critical error"],
            warnings=["Warning"]
        )
        
        item = ReviewQueueItem(
            tech_entry=tech,
            priority=ReviewPriority.URGENT,
            days_pending=20,
            validation_result=validation_result,
            auto_priority_score=0.0  # Will be calculated
        )
        
        # Should have high auto priority score due to:
        # - Age (20 days) = +0.4
        # - Errors = +0.3
        # - Low confidence = +0.3
        # - High mentions = +0.2
        # Total = 1.2, capped at 1.0
        assert item.auto_priority_score == 1.0