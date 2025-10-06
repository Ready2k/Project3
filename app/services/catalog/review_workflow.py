"""Pending review queue and approval workflow for technology catalog."""

from typing import Dict, List, Optional, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from enum import Enum

from .models import TechEntry, ReviewStatus, ValidationResult
from .validator import CatalogValidator
from app.utils.imports import require_service


class ReviewPriority(Enum):
    """Priority levels for review queue."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    URGENT = "urgent"


@dataclass
class ReviewQueueItem:
    """Item in the review queue with metadata."""
    tech_entry: TechEntry
    priority: ReviewPriority
    days_pending: int
    validation_result: ValidationResult
    auto_priority_score: float  # 0.0-1.0, higher = more urgent
    
    def __post_init__(self):
        """Calculate auto priority score."""
        score = 0.0
        
        # Age factor (older = higher priority)
        if self.days_pending > 14:
            score += 0.4
        elif self.days_pending > 7:
            score += 0.2
        
        # Validation issues factor
        if self.validation_result.errors:
            score += 0.3
        elif self.validation_result.warnings:
            score += 0.1
        
        # Confidence factor (lower confidence = higher priority)
        if self.tech_entry.confidence_score < 0.5:
            score += 0.3
        elif self.tech_entry.confidence_score < 0.7:
            score += 0.1
        
        # Usage factor (mentioned more = higher priority)
        if self.tech_entry.mention_count > 5:
            score += 0.2
        elif self.tech_entry.mention_count > 2:
            score += 0.1
        
        self.auto_priority_score = min(1.0, score)


@dataclass
class ReviewAction:
    """Action taken during review process."""
    action_type: str  # "approve", "reject", "request_update", "comment"
    reviewer: str
    timestamp: datetime
    notes: Optional[str] = None
    changes_made: Optional[Dict[str, Any]] = None


@dataclass
class ReviewSession:
    """Review session tracking multiple actions."""
    session_id: str
    reviewer: str
    start_time: datetime
    end_time: Optional[datetime] = None
    actions: List[ReviewAction] = field(default_factory=list)
    technologies_reviewed: List[str] = field(default_factory=list)


class ReviewWorkflow:
    """Manages the technology review workflow and queue."""
    
    def __init__(self, catalog_manager):
        self.catalog_manager = catalog_manager
        self.validator = CatalogValidator()
        self.logger = require_service('logger', context='ReviewWorkflow')
        
        # Review configuration
        self.max_queue_size = 50
        self.urgent_threshold_days = 21
        self.high_priority_threshold_days = 14
        self.medium_priority_threshold_days = 7
    
    def get_review_queue(self, 
                        priority_filter: Optional[ReviewPriority] = None,
                        limit: Optional[int] = None) -> List[ReviewQueueItem]:
        """Get the current review queue with prioritization."""
        pending_techs = self.catalog_manager.get_pending_review_queue()
        queue_items = []
        
        for tech in pending_techs:
            # Calculate days pending
            days_pending = 0
            if tech.added_date:
                days_pending = (datetime.now() - tech.added_date).days
            
            # Validate the technology
            validation_result = self.validator.validate_technology_entry(tech)
            
            # Determine priority
            priority = self._calculate_priority(tech, days_pending, validation_result)
            
            # Create queue item
            queue_item = ReviewQueueItem(
                tech_entry=tech,
                priority=priority,
                days_pending=days_pending,
                validation_result=validation_result,
                auto_priority_score=0.0  # Will be calculated in __post_init__
            )
            
            # Filter by priority if specified
            if priority_filter is None or queue_item.priority == priority_filter:
                queue_items.append(queue_item)
        
        # Sort by priority and auto-priority score
        priority_order = {
            ReviewPriority.URGENT: 4,
            ReviewPriority.HIGH: 3,
            ReviewPriority.MEDIUM: 2,
            ReviewPriority.LOW: 1
        }
        
        queue_items.sort(
            key=lambda x: (priority_order[x.priority], x.auto_priority_score, x.days_pending),
            reverse=True
        )
        
        if limit:
            queue_items = queue_items[:limit]
        
        return queue_items
    
    def _calculate_priority(self, 
                          tech: TechEntry, 
                          days_pending: int, 
                          validation_result: ValidationResult) -> ReviewPriority:
        """Calculate review priority for a technology."""
        # Urgent: Critical errors or very old
        if validation_result.errors or days_pending >= self.urgent_threshold_days:
            return ReviewPriority.URGENT
        
        # High: Warnings or moderately old
        if validation_result.warnings or days_pending >= self.high_priority_threshold_days:
            return ReviewPriority.HIGH
        
        # Medium: Some age or low confidence
        if days_pending >= self.medium_priority_threshold_days or tech.confidence_score < 0.6:
            return ReviewPriority.MEDIUM
        
        # Low: Everything else
        return ReviewPriority.LOW
    
    def start_review_session(self, reviewer: str) -> str:
        """Start a new review session."""
        session_id = f"review_{datetime.now().strftime('%Y%m%d_%H%M%S')}_{reviewer}"
        
        # Note: In a full implementation, this would be stored in a database
        # For now, we'll just log the session start
        self.logger.info(f"Started review session {session_id} for reviewer {reviewer}")
        
        return session_id
    
    def approve_technology(self, 
                          tech_id: str, 
                          reviewer: str, 
                          notes: Optional[str] = None,
                          session_id: Optional[str] = None) -> bool:
        """Approve a technology entry."""
        success = self.catalog_manager.approve_technology(tech_id, reviewer, notes)
        
        if success:
            self.logger.info(f"Technology {tech_id} approved by {reviewer}")
            
            # Log review action
            action = ReviewAction(
                action_type="approve",
                reviewer=reviewer,
                timestamp=datetime.now(),
                notes=notes
            )
            self._log_review_action(tech_id, action, session_id)
        
        return success
    
    def reject_technology(self, 
                         tech_id: str, 
                         reviewer: str, 
                         notes: str,
                         session_id: Optional[str] = None) -> bool:
        """Reject a technology entry."""
        success = self.catalog_manager.reject_technology(tech_id, reviewer, notes)
        
        if success:
            self.logger.info(f"Technology {tech_id} rejected by {reviewer}")
            
            # Log review action
            action = ReviewAction(
                action_type="reject",
                reviewer=reviewer,
                timestamp=datetime.now(),
                notes=notes
            )
            self._log_review_action(tech_id, action, session_id)
        
        return success
    
    def request_technology_update(self, 
                                 tech_id: str, 
                                 reviewer: str, 
                                 notes: str,
                                 suggested_changes: Optional[Dict[str, Any]] = None,
                                 session_id: Optional[str] = None) -> bool:
        """Request updates to a technology entry."""
        success = self.catalog_manager.request_technology_update(tech_id, reviewer, notes)
        
        if success:
            self.logger.info(f"Update requested for technology {tech_id} by {reviewer}")
            
            # Log review action
            action = ReviewAction(
                action_type="request_update",
                reviewer=reviewer,
                timestamp=datetime.now(),
                notes=notes,
                changes_made=suggested_changes
            )
            self._log_review_action(tech_id, action, session_id)
        
        return success
    
    def bulk_approve_technologies(self, 
                                 tech_ids: List[str], 
                                 reviewer: str, 
                                 notes: Optional[str] = None) -> Dict[str, bool]:
        """Bulk approve multiple technologies."""
        results = {}
        
        for tech_id in tech_ids:
            results[tech_id] = self.approve_technology(tech_id, reviewer, notes)
        
        approved_count = sum(1 for success in results.values() if success)
        self.logger.info(f"Bulk approved {approved_count}/{len(tech_ids)} technologies by {reviewer}")
        
        return results
    
    def auto_approve_high_confidence_entries(self, 
                                           confidence_threshold: float = 0.9,
                                           max_auto_approvals: int = 10) -> List[str]:
        """Automatically approve high-confidence entries."""
        queue = self.get_review_queue()
        auto_approved = []
        
        for item in queue:
            if len(auto_approved) >= max_auto_approvals:
                break
            
            tech = item.tech_entry
            
            # Check if eligible for auto-approval
            if (tech.confidence_score >= confidence_threshold and
                tech.auto_generated and
                not item.validation_result.errors and
                len(item.validation_result.warnings) <= 1):
                
                success = self.approve_technology(
                    tech.id, 
                    "system_auto_approval", 
                    f"Auto-approved: high confidence ({tech.confidence_score:.2f})"
                )
                
                if success:
                    auto_approved.append(tech.id)
        
        if auto_approved:
            self.logger.info(f"Auto-approved {len(auto_approved)} high-confidence technologies")
        
        return auto_approved
    
    def get_review_statistics(self) -> Dict[str, Any]:
        """Get statistics about the review queue and process."""
        queue = self.get_review_queue()
        
        stats = {
            "total_pending": len(queue),
            "by_priority": {
                "urgent": len([item for item in queue if item.priority == ReviewPriority.URGENT]),
                "high": len([item for item in queue if item.priority == ReviewPriority.HIGH]),
                "medium": len([item for item in queue if item.priority == ReviewPriority.MEDIUM]),
                "low": len([item for item in queue if item.priority == ReviewPriority.LOW])
            },
            "avg_days_pending": sum(item.days_pending for item in queue) / len(queue) if queue else 0,
            "oldest_pending": max((item.days_pending for item in queue), default=0),
            "validation_issues": {
                "with_errors": len([item for item in queue if item.validation_result.errors]),
                "with_warnings": len([item for item in queue if item.validation_result.warnings])
            },
            "confidence_distribution": {
                "high": len([item for item in queue if item.tech_entry.confidence_score >= 0.8]),
                "medium": len([item for item in queue if 0.6 <= item.tech_entry.confidence_score < 0.8]),
                "low": len([item for item in queue if item.tech_entry.confidence_score < 0.6])
            }
        }
        
        return stats
    
    def get_review_recommendations(self) -> List[str]:
        """Get recommendations for review process optimization."""
        stats = self.get_review_statistics()
        recommendations = []
        
        # Queue size recommendations
        if stats["total_pending"] > self.max_queue_size:
            recommendations.append(
                f"Review queue is large ({stats['total_pending']} items). "
                f"Consider increasing review capacity or auto-approval thresholds."
            )
        
        # Priority recommendations
        urgent_count = stats["by_priority"]["urgent"]
        if urgent_count > 5:
            recommendations.append(
                f"{urgent_count} urgent items need immediate attention. "
                f"Focus on critical errors and old entries first."
            )
        
        # Age recommendations
        if stats["oldest_pending"] > 30:
            recommendations.append(
                f"Oldest pending item is {stats['oldest_pending']} days old. "
                f"Consider reviewing aging policies."
            )
        
        # Validation recommendations
        error_count = stats["validation_issues"]["with_errors"]
        if error_count > 0:
            recommendations.append(
                f"{error_count} items have validation errors. "
                f"These should be prioritized for review or rejection."
            )
        
        # Auto-approval recommendations
        high_confidence = stats["confidence_distribution"]["high"]
        if high_confidence > 10:
            recommendations.append(
                f"{high_confidence} high-confidence items could be auto-approved. "
                f"Consider running auto-approval process."
            )
        
        return recommendations
    
    def _log_review_action(self, 
                          tech_id: str, 
                          action: ReviewAction, 
                          session_id: Optional[str] = None) -> None:
        """Log a review action for audit purposes."""
        log_data = {
            "tech_id": tech_id,
            "action": action.action_type,
            "reviewer": action.reviewer,
            "timestamp": action.timestamp.isoformat(),
            "session_id": session_id
        }
        
        if action.notes:
            log_data["notes"] = action.notes
        
        if action.changes_made:
            log_data["changes"] = action.changes_made
        
        self.logger.info(f"Review action logged: {log_data}")
    
    def generate_review_report(self, 
                              reviewer: Optional[str] = None,
                              days_back: int = 30) -> Dict[str, Any]:
        """Generate a review activity report."""
        # Note: In a full implementation, this would query a database
        # For now, we'll return current queue statistics
        
        report = {
            "report_period": f"Last {days_back} days",
            "generated_at": datetime.now().isoformat(),
            "reviewer_filter": reviewer,
            "current_queue_stats": self.get_review_statistics(),
            "recommendations": self.get_review_recommendations()
        }
        
        return report
    
    def cleanup_old_rejected_entries(self, days_old: int = 90) -> List[str]:
        """Clean up old rejected entries to keep catalog tidy."""
        cutoff_date = datetime.now() - timedelta(days=days_old)
        cleaned_up = []
        
        for tech_id, tech in self.catalog_manager.technologies.items():
            if (tech.review_status == ReviewStatus.REJECTED and
                tech.reviewed_date and
                tech.reviewed_date < cutoff_date):
                
                # Remove from catalog
                del self.catalog_manager.technologies[tech_id]
                cleaned_up.append(tech_id)
        
        if cleaned_up:
            self.catalog_manager._rebuild_indexes()
            self.catalog_manager._save_catalog()
            self.logger.info(f"Cleaned up {len(cleaned_up)} old rejected entries")
        
        return cleaned_up