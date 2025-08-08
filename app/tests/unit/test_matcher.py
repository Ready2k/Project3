import tempfile
from pathlib import Path
from unittest.mock import AsyncMock, Mock

import pytest

from app.pattern.matcher import PatternMatcher, MatchResult
from app.pattern.loader import PatternLoader
from app.embeddings.index import FAISSIndex
from app.llm.fakes import FakeEmbedder


class TestPatternMatcher:
    """Test pattern matching engine."""
    
    @pytest.fixture
    def sample_patterns(self):
        """Sample patterns for testing."""
        return [
            {
                "pattern_id": "PAT-001",
                "name": "Web Scraping",
                "description": "Automated web scraping with Python",
                "feasibility": "Automatable",
                "pattern_type": ["web_automation", "data_extraction"],
                "domain": "data_processing",
                "tech_stack": ["Python", "BeautifulSoup", "Scrapy"],
                "confidence_score": 0.9,
                "constraints": {"banned_tools": []}
            },
            {
                "pattern_id": "PAT-002",
                "name": "API Integration",
                "description": "REST API integration with authentication",
                "feasibility": "Automatable",
                "pattern_type": ["api_integration", "workflow_automation"],
                "domain": "system_integration",
                "tech_stack": ["Python", "FastAPI", "httpx"],
                "confidence_score": 0.95,
                "constraints": {"banned_tools": []}
            },
            {
                "pattern_id": "PAT-003",
                "name": "Document Processing",
                "description": "OCR and document text extraction",
                "feasibility": "Partially Automatable",
                "pattern_type": ["document_processing", "ml_pipeline"],
                "domain": "document_management",
                "tech_stack": ["Python", "Tesseract", "OpenCV"],
                "confidence_score": 0.75,
                "constraints": {"banned_tools": ["proprietary_ocr"]}
            }
        ]
    
    @pytest.fixture
    def mock_pattern_loader(self, sample_patterns):
        """Mock pattern loader."""
        loader = Mock(spec=PatternLoader)
        loader.load_patterns.return_value = sample_patterns
        return loader
    
    @pytest.fixture
    def mock_faiss_index(self):
        """Mock FAISS index."""
        index = Mock(spec=FAISSIndex)
        return index
    
    @pytest.fixture
    def fake_embedder(self):
        """Fake embedder for testing."""
        return FakeEmbedder(dimension=384, seed=42)
    
    @pytest.fixture
    def matcher(self, mock_pattern_loader, fake_embedder):
        """Pattern matcher instance."""
        with tempfile.TemporaryDirectory() as temp_dir:
            index_path = Path(temp_dir) / "test.faiss"
            faiss_index = FAISSIndex(embedder=fake_embedder, index_path=index_path)
            return PatternMatcher(
                pattern_loader=mock_pattern_loader,
                embedding_provider=fake_embedder,
                faiss_index=faiss_index
            )
    
    def test_filter_by_tags_exact_match(self, matcher, sample_patterns):
        """Test tag filtering with exact matches."""
        requirements = {
            "description": "Need web scraping automation",
            "domain": "data_processing",
            "pattern_types": ["web_automation"]
        }
        
        results = matcher._filter_by_tags(requirements, sample_patterns)
        
        assert len(results) == 1
        assert results[0]["pattern_id"] == "PAT-001"
    
    def test_filter_by_tags_domain_match(self, matcher, sample_patterns):
        """Test tag filtering by domain."""
        requirements = {
            "description": "System integration task",
            "domain": "system_integration"
        }
        
        results = matcher._filter_by_tags(requirements, sample_patterns)
        
        assert len(results) == 1
        assert results[0]["pattern_id"] == "PAT-002"
    
    def test_filter_by_tags_pattern_type_match(self, matcher, sample_patterns):
        """Test tag filtering by pattern type."""
        requirements = {
            "description": "Document processing needed",
            "pattern_types": ["document_processing"]
        }
        
        results = matcher._filter_by_tags(requirements, sample_patterns)
        
        assert len(results) == 1
        assert results[0]["pattern_id"] == "PAT-003"
    
    def test_filter_by_tags_no_match(self, matcher, sample_patterns):
        """Test tag filtering with no matches."""
        requirements = {
            "description": "Something completely different",
            "domain": "nonexistent_domain",
            "pattern_types": ["nonexistent_type"]
        }
        
        results = matcher._filter_by_tags(requirements, sample_patterns)
        
        assert len(results) == 0
    
    def test_filter_by_tags_multiple_matches(self, matcher, sample_patterns):
        """Test tag filtering with multiple matches."""
        requirements = {
            "description": "Automation task",
            "pattern_types": ["web_automation", "workflow_automation"]
        }
        
        results = matcher._filter_by_tags(requirements, sample_patterns)
        
        assert len(results) == 2
        pattern_ids = [r["pattern_id"] for r in results]
        assert "PAT-001" in pattern_ids
        assert "PAT-002" in pattern_ids
    
    def test_blend_scores_equal_weights(self, matcher):
        """Test score blending with equal weights."""
        tag_candidates = [
            {"pattern_id": "PAT-001", "tag_score": 0.8},
            {"pattern_id": "PAT-002", "tag_score": 0.6}
        ]
        
        vector_candidates = [
            {"pattern_id": "PAT-001", "score": 0.9},
            {"pattern_id": "PAT-002", "score": 0.7}
        ]
        
        pattern_confidences = {"PAT-001": 0.9, "PAT-002": 0.95}
        
        results = matcher._blend_scores(
            tag_candidates, vector_candidates, pattern_confidences,
            tag_weight=0.4, vector_weight=0.4, confidence_weight=0.2
        )
        
        assert len(results) == 2
        
        # Check PAT-001: (0.8 * 0.4) + (0.9 * 0.4) + (0.9 * 0.2) = 0.32 + 0.36 + 0.18 = 0.86
        pat_001 = next(r for r in results if r["pattern_id"] == "PAT-001")
        assert abs(pat_001["blended_score"] - 0.86) < 0.01
        
        # Check PAT-002: (0.6 * 0.4) + (0.7 * 0.4) + (0.95 * 0.2) = 0.24 + 0.28 + 0.19 = 0.71
        pat_002 = next(r for r in results if r["pattern_id"] == "PAT-002")
        assert abs(pat_002["blended_score"] - 0.71) < 0.01
    
    def test_blend_scores_missing_vector_candidate(self, matcher):
        """Test score blending when vector candidate is missing."""
        tag_candidates = [
            {"pattern_id": "PAT-001", "tag_score": 0.8},
            {"pattern_id": "PAT-002", "tag_score": 0.6}
        ]
        
        vector_candidates = [
            {"pattern_id": "PAT-001", "score": 0.9}
            # PAT-002 missing from vector results
        ]
        
        pattern_confidences = {"PAT-001": 0.9, "PAT-002": 0.95}
        
        results = matcher._blend_scores(
            tag_candidates, vector_candidates, pattern_confidences
        )
        
        assert len(results) == 2
        
        # PAT-002 should have vector_score = 0.0
        pat_002 = next(r for r in results if r["pattern_id"] == "PAT-002")
        assert pat_002["vector_score"] == 0.0
    
    def test_apply_constraints_banned_tools(self, matcher, sample_patterns):
        """Test constraint filtering for banned tools."""
        candidates = [
            {"pattern_id": "PAT-001", "blended_score": 0.9},
            {"pattern_id": "PAT-002", "blended_score": 0.8},
            {"pattern_id": "PAT-003", "blended_score": 0.7}
        ]
        
        constraints = {"banned_tools": ["proprietary_ocr"]}
        
        results = matcher._apply_constraints(candidates, sample_patterns, constraints)
        
        # PAT-003 should be filtered out due to banned tool
        assert len(results) == 2
        pattern_ids = [r["pattern_id"] for r in results]
        assert "PAT-001" in pattern_ids
        assert "PAT-002" in pattern_ids
        assert "PAT-003" not in pattern_ids
    
    def test_apply_constraints_banned_tech_stack(self, matcher, sample_patterns):
        """Test constraint filtering for banned tech stack items."""
        candidates = [
            {"pattern_id": "PAT-001", "blended_score": 0.9},
            {"pattern_id": "PAT-002", "blended_score": 0.8}
        ]
        
        constraints = {"banned_tools": ["FastAPI"]}
        
        results = matcher._apply_constraints(candidates, sample_patterns, constraints)
        
        # PAT-002 should be filtered out due to FastAPI in tech_stack
        assert len(results) == 1
        assert results[0]["pattern_id"] == "PAT-001"
    
    def test_apply_constraints_no_banned_tools(self, matcher, sample_patterns):
        """Test constraint filtering with no banned tools."""
        candidates = [
            {"pattern_id": "PAT-001", "blended_score": 0.9},
            {"pattern_id": "PAT-002", "blended_score": 0.8}
        ]
        
        constraints = {"banned_tools": []}
        
        results = matcher._apply_constraints(candidates, sample_patterns, constraints)
        
        # All candidates should remain
        assert len(results) == 2
    
    @pytest.mark.asyncio
    async def test_match_patterns_integration(self, matcher, sample_patterns):
        """Test complete pattern matching workflow."""
        # Setup FAISS index with pattern descriptions
        descriptions = [p["description"] for p in sample_patterns]
        await matcher.faiss_index.build_from_texts(descriptions)
        
        requirements = {
            "description": "I need to scrape data from websites automatically",
            "domain": "data_processing",
            "pattern_types": ["web_automation"]
        }
        
        constraints = {"banned_tools": []}
        
        results = await matcher.match_patterns(requirements, constraints, top_k=3)
        
        assert len(results) <= 3
        assert all(isinstance(r, MatchResult) for r in results)
        
        # Results should be sorted by blended score (descending)
        scores = [r.blended_score for r in results]
        assert scores == sorted(scores, reverse=True)
        
        # Should include pattern information
        for result in results:
            assert result.pattern_id.startswith("PAT-")
            assert result.pattern_name
            assert result.feasibility in ["Automatable", "Partially Automatable", "Not Automatable"]
            assert isinstance(result.tech_stack, list)
            assert 0 <= result.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_match_patterns_empty_requirements(self, matcher, sample_patterns):
        """Test pattern matching with empty requirements."""
        # Setup FAISS index
        descriptions = [p["description"] for p in sample_patterns]
        await matcher.faiss_index.build_from_texts(descriptions)
        
        requirements = {}
        constraints = {"banned_tools": []}
        
        results = await matcher.match_patterns(requirements, constraints, top_k=3)
        
        # Should still return results based on vector similarity
        assert len(results) <= 3
    
    @pytest.mark.asyncio
    async def test_match_patterns_with_constraints(self, matcher, sample_patterns):
        """Test pattern matching with constraints applied."""
        # Setup FAISS index
        descriptions = [p["description"] for p in sample_patterns]
        await matcher.faiss_index.build_from_texts(descriptions)
        
        requirements = {
            "description": "Document processing automation"
        }
        
        constraints = {"banned_tools": ["proprietary_ocr"]}
        
        results = await matcher.match_patterns(requirements, constraints, top_k=5)
        
        # PAT-003 should be filtered out due to constraints
        pattern_ids = [r.pattern_id for r in results]
        assert "PAT-003" not in pattern_ids


class TestMatchResult:
    """Test MatchResult data class."""
    
    def test_match_result_creation(self):
        """Test creating a MatchResult."""
        result = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Test Pattern",
            feasibility="Automatable",
            tech_stack=["Python", "FastAPI"],
            confidence=0.9,
            tag_score=0.8,
            vector_score=0.85,
            blended_score=0.82,
            rationale="High similarity in requirements"
        )
        
        assert result.pattern_id == "PAT-001"
        assert result.pattern_name == "Test Pattern"
        assert result.feasibility == "Automatable"
        assert len(result.tech_stack) == 2
        assert result.confidence == 0.9
        assert result.blended_score == 0.82
    
    def test_match_result_dict_conversion(self):
        """Test converting MatchResult to dictionary."""
        result = MatchResult(
            pattern_id="PAT-001",
            pattern_name="Test Pattern",
            feasibility="Automatable",
            tech_stack=["Python"],
            confidence=0.9,
            tag_score=0.8,
            vector_score=0.85,
            blended_score=0.82,
            rationale="Test rationale"
        )
        
        result_dict = result.to_dict()
        
        assert result_dict["pattern_id"] == "PAT-001"
        assert result_dict["pattern_name"] == "Test Pattern"
        assert result_dict["feasibility"] == "Automatable"
        assert result_dict["tech_stack"] == ["Python"]
        assert result_dict["confidence"] == 0.9
        assert result_dict["blended_score"] == 0.82