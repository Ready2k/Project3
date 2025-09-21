"""Tests for catalog models."""

import pytest
from datetime import datetime
from unittest.mock import patch

from app.services.catalog.models import (
    TechEntry, EcosystemType, MaturityLevel, ReviewStatus,
    ValidationResult, FuzzyMatchResult, CatalogStats
)


class TestTechEntry:
    """Test cases for TechEntry model."""
    
    def test_tech_entry_creation(self):
        """Test basic TechEntry creation."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="testing",
            description="A test technology"
        )
        
        assert tech.id == "test_tech"
        assert tech.name == "Test Technology"
        assert tech.canonical_name == "Test Technology"
        assert tech.category == "testing"
        assert tech.description == "A test technology"
        assert tech.confidence_score == 1.0
        assert not tech.pending_review
        assert tech.review_status == ReviewStatus.APPROVED
    
    def test_auto_generated_entry_defaults(self):
        """Test that auto-generated entries have correct defaults."""
        tech = TechEntry(
            id="auto_tech",
            name="Auto Technology",
            canonical_name="Auto Technology",
            category="testing",
            description="Auto-generated technology",
            auto_generated=True
        )
        
        assert tech.auto_generated
        assert tech.pending_review
        assert tech.review_status == ReviewStatus.PENDING
    
    def test_canonical_name_default(self):
        """Test that canonical_name defaults to name if not provided."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="",  # Empty canonical name
            category="testing",
            description="A test technology"
        )
        
        # Should be set to name in __post_init__
        assert tech.canonical_name == "Test Technology"
    
    def test_add_alias(self):
        """Test adding aliases to technology."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="testing",
            description="A test technology"
        )
        
        tech.add_alias("test-tech")
        tech.add_alias("TestTech")
        
        assert "test-tech" in tech.aliases
        assert "TestTech" in tech.aliases
        
        # Should not add duplicate
        tech.add_alias("test-tech")
        assert tech.aliases.count("test-tech") == 1
        
        # Should not add name as alias
        tech.add_alias("Test Technology")
        assert "Test Technology" not in tech.aliases
    
    def test_increment_counters(self):
        """Test incrementing mention and selection counters."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="testing",
            description="A test technology"
        )
        
        assert tech.mention_count == 0
        assert tech.selection_count == 0
        
        tech.increment_mention()
        tech.increment_selection()
        
        assert tech.mention_count == 1
        assert tech.selection_count == 1
    
    def test_validation_errors(self):
        """Test validation error management."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="testing",
            description="A test technology"
        )
        
        assert len(tech.validation_errors) == 0
        
        tech.add_validation_error("Test error")
        tech.add_validation_error("Another error")
        
        assert len(tech.validation_errors) == 2
        assert "Test error" in tech.validation_errors
        
        # Should not add duplicate
        tech.add_validation_error("Test error")
        assert len(tech.validation_errors) == 2
        
        tech.clear_validation_errors()
        assert len(tech.validation_errors) == 0
        assert tech.last_validated is not None
    
    def test_review_workflow(self):
        """Test review workflow methods."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="testing",
            description="A test technology",
            auto_generated=True
        )
        
        # Should start as pending
        assert tech.pending_review
        assert tech.review_status == ReviewStatus.PENDING
        
        # Test approval
        tech.approve_review("test_reviewer", "Looks good")
        assert not tech.pending_review
        assert tech.review_status == ReviewStatus.APPROVED
        assert tech.reviewed_by == "test_reviewer"
        assert tech.review_notes == "Looks good"
        assert tech.reviewed_date is not None
        assert tech.last_updated is not None
        
        # Test rejection
        tech.reject_review("test_reviewer", "Not suitable")
        assert not tech.pending_review
        assert tech.review_status == ReviewStatus.REJECTED
        assert tech.review_notes == "Not suitable"
        
        # Test update request
        tech.request_update("test_reviewer", "Needs more info")
        assert tech.pending_review
        assert tech.review_status == ReviewStatus.NEEDS_UPDATE
        assert tech.review_notes == "Needs more info"
    
    def test_to_dict_conversion(self):
        """Test conversion to dictionary."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="testing",
            description="A test technology",
            aliases=["test-tech"],
            ecosystem=EcosystemType.OPEN_SOURCE,
            confidence_score=0.8,
            integrates_with=["python"],
            alternatives=["other_tech"],
            tags=["test"],
            use_cases=["testing"],
            license="MIT",
            maturity=MaturityLevel.STABLE
        )
        
        data = tech.to_dict()
        
        assert data["id"] == "test_tech"
        assert data["name"] == "Test Technology"
        assert data["ecosystem"] == "open_source"
        assert data["confidence_score"] == 0.8
        assert data["aliases"] == ["test-tech"]
        assert data["maturity"] == "stable"
    
    def test_from_dict_conversion(self):
        """Test creation from dictionary."""
        data = {
            "id": "test_tech",
            "name": "Test Technology",
            "canonical_name": "Test Technology",
            "category": "testing",
            "description": "A test technology",
            "aliases": ["test-tech"],
            "ecosystem": "open_source",
            "confidence_score": 0.8,
            "pending_review": False,
            "integrates_with": ["python"],
            "alternatives": ["other_tech"],
            "tags": ["test"],
            "use_cases": ["testing"],
            "license": "MIT",
            "maturity": "stable",
            "auto_generated": False,
            "review_status": "approved",
            "mention_count": 5,
            "selection_count": 2,
            "validation_errors": [],
            "added_date": "2024-01-01T00:00:00",
            "last_updated": "2024-01-02T00:00:00"
        }
        
        tech = TechEntry.from_dict(data)
        
        assert tech.id == "test_tech"
        assert tech.name == "Test Technology"
        assert tech.ecosystem == EcosystemType.OPEN_SOURCE
        assert tech.confidence_score == 0.8
        assert tech.aliases == ["test-tech"]
        assert tech.maturity == MaturityLevel.STABLE
        assert tech.review_status == ReviewStatus.APPROVED
        assert tech.mention_count == 5
        assert tech.selection_count == 2
        assert tech.added_date.year == 2024


class TestValidationResult:
    """Test cases for ValidationResult model."""
    
    def test_validation_result_creation(self):
        """Test ValidationResult creation."""
        result = ValidationResult(
            is_valid=False,
            errors=["Error 1", "Error 2"],
            warnings=["Warning 1"],
            suggestions=["Suggestion 1"]
        )
        
        assert not result.is_valid
        assert len(result.errors) == 2
        assert len(result.warnings) == 1
        assert len(result.suggestions) == 1


class TestFuzzyMatchResult:
    """Test cases for FuzzyMatchResult model."""
    
    def test_fuzzy_match_result_creation(self):
        """Test FuzzyMatchResult creation."""
        tech = TechEntry(
            id="test_tech",
            name="Test Technology",
            canonical_name="Test Technology",
            category="testing",
            description="A test technology"
        )
        
        result = FuzzyMatchResult(
            tech_entry=tech,
            match_score=0.85,
            match_type="fuzzy_name",
            matched_text="test tech"
        )
        
        assert result.tech_entry == tech
        assert result.match_score == 0.85
        assert result.match_type == "fuzzy_name"
        assert result.matched_text == "test tech"


class TestCatalogStats:
    """Test cases for CatalogStats model."""
    
    def test_catalog_stats_creation(self):
        """Test CatalogStats creation."""
        stats = CatalogStats(
            total_entries=100,
            pending_review=5,
            auto_generated=20,
            by_ecosystem={"aws": 30, "azure": 25},
            by_category={"frameworks": 40, "databases": 20},
            by_maturity={"stable": 80, "beta": 15},
            validation_errors=2
        )
        
        assert stats.total_entries == 100
        assert stats.pending_review == 5
        assert stats.auto_generated == 20
        assert stats.by_ecosystem["aws"] == 30
        assert stats.validation_errors == 2