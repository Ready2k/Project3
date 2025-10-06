"""Integration tests for complete end-to-end workflows."""

import pytest
import asyncio
import json
import tempfile
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock

from app.api import app
from app.config import Settings
from app.llm.fakes import FakeLLM, FakeEmbedder
from app.pattern.loader import PatternLoader
from app.pattern.matcher import PatternMatcher
from app.services.recommendation import RecommendationService
from app.qa.question_loop import QuestionLoop, TemplateLoader
from app.state.store import DiskCacheStore
from app.exporters.service import ExportService
from app.utils.audit import AuditLogger


class TestCompleteWorkflows:
    """Test complete end-to-end workflows."""
    
    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test data."""
        with tempfile.TemporaryDirectory() as temp_dir:
            yield Path(temp_dir)
    
    @pytest.fixture
    def mock_patterns(self, temp_dir):
        """Create mock pattern files."""
        patterns_dir = temp_dir / "patterns"
        patterns_dir.mkdir()
        
        # Create sample patterns
        pattern1 = {
            "pattern_id": "PAT-001",
            "name": "Data Processing Automation",
            "description": "Automate data processing workflows",
            "feasibility": "Automatable",
            "confidence_score": 0.9,
            "domain": "data_processing",
            "pattern_type": "workflow",
            "tech_stack": ["Python", "Pandas"],
            "tags": ["data", "processing", "automation"]
        }
        
        pattern2 = {
            "pattern_id": "PAT-002",
            "name": "API Integration",
            "description": "Integrate with external APIs",
            "feasibility": "Partially Automatable",
            "confidence_score": 0.7,
            "domain": "api_integration",
            "pattern_type": "integration",
            "tech_stack": ["Python", "Requests"],
            "tags": ["api", "integration", "external"]
        }
        
        with open(patterns_dir / "PAT-001.json", "w") as f:
            json.dump(pattern1, f)
        
        with open(patterns_dir / "PAT-002.json", "w") as f:
            json.dump(pattern2, f)
        
        return patterns_dir
    
    @pytest.fixture
    def mock_templates(self, temp_dir):
        """Create mock question templates."""
        templates_dir = temp_dir / "templates"
        templates_dir.mkdir()
        
        templates = {
            "data_processing_questions": {
                "domain": "data_processing",
                "questions": [
                    {
                        "text": "What is the data volume?",
                        "field": "data_volume",
                        "type": "text"
                    },
                    {
                        "text": "How sensitive is the data?",
                        "field": "data_sensitivity",
                        "type": "select",
                        "options": ["low", "medium", "high"]
                    }
                ]
            }
        }
        
        with open(templates_dir / "templates.json", "w") as f:
            json.dump(templates, f)
        
        return templates_dir
    
    @pytest.fixture
    def workflow_components(self, temp_dir, mock_patterns, mock_templates):
        """Set up all workflow components."""
        # Create cache directory
        cache_dir = temp_dir / "cache"
        cache_dir.mkdir()
        
        # Initialize components
        settings = Settings()
        llm_provider = FakeLLM()
        embedder = FakeEmbedder()
        pattern_loader = PatternLoader(str(mock_patterns))
        pattern_matcher = PatternMatcher(embedder)
        recommendation_service = RecommendationService()
        template_loader = TemplateLoader(str(mock_templates))
        session_store = DiskCacheStore(str(cache_dir))
        question_loop = QuestionLoop(llm_provider, template_loader, session_store)
        export_service = ExportService(temp_dir / "exports")
        audit_logger = AuditLogger(":memory:")  # In-memory SQLite for tests
        
        return {
            "settings": settings,
            "llm_provider": llm_provider,
            "embedder": embedder,
            "pattern_loader": pattern_loader,
            "pattern_matcher": pattern_matcher,
            "recommendation_service": recommendation_service,
            "template_loader": template_loader,
            "session_store": session_store,
            "question_loop": question_loop,
            "export_service": export_service,
            "audit_logger": audit_logger
        }
    
    @pytest.mark.asyncio
    async def test_complete_analysis_workflow(self, workflow_components):
        """Test complete analysis workflow from requirements to recommendations."""
        components = workflow_components
        
        # Step 1: Load patterns
        patterns = components["pattern_loader"].load_patterns()
        assert len(patterns) == 2
        
        # Step 2: Create session with requirements
        requirements = {
            "description": "Automate daily data processing from CSV files",
            "domain": "data_processing",
            "frequency": "daily"
        }
        
        session_id = "test-session-001"
        session = components["session_store"].create_session(session_id, requirements)
        assert session.session_id == session_id
        
        # Step 3: Pattern matching
        matches = await components["pattern_matcher"].match_patterns(requirements, patterns)
        assert len(matches) > 0
        
        # Step 4: Generate recommendations
        recommendations = components["recommendation_service"].generate_recommendations(matches, requirements)
        assert len(recommendations) > 0
        assert all(rec.confidence >= 0 for rec in recommendations)
        
        # Step 5: Update session with results
        session.pattern_matches = [match.to_dict() for match in matches]
        session.recommendations = [rec.to_dict() for rec in recommendations]
        components["session_store"].update_session(session)
        
        # Step 6: Export results
        json_export = await components["export_service"].export_session(session_id, "json")
        assert json_export is not None
        assert json_export["file_path"].endswith(".json")
        
        markdown_export = await components["export_service"].export_session(session_id, "markdown")
        assert markdown_export is not None
        assert markdown_export["file_path"].endswith(".md")
        
        # Verify exported files exist and contain data
        json_path = Path(json_export["file_path"])
        md_path = Path(markdown_export["file_path"])
        
        assert json_path.exists()
        assert md_path.exists()
        assert json_path.stat().st_size > 0
        assert md_path.stat().st_size > 0
    
    @pytest.mark.asyncio
    async def test_qa_workflow_integration(self, workflow_components):
        """Test Q&A workflow integration."""
        components = workflow_components
        
        # Create session with minimal requirements
        requirements = {
            "description": "Process customer data automatically"
        }
        
        session_id = "test-qa-session"
        components["session_store"].create_session(session_id, requirements)
        
        # Generate questions
        qa_result = await components["question_loop"].generate_questions(requirements, session_id)
        
        # Should generate questions for missing information
        assert isinstance(qa_result.next_questions, list)
        assert qa_result.confidence >= 0
        
        # Simulate answering questions
        if qa_result.next_questions:
            answers = {
                qa_result.next_questions[0].field: "high volume data processing"
            }
            
            # Process answers
            updated_result = await components["question_loop"].process_answers(answers, session_id)
            assert updated_result.confidence >= qa_result.confidence
    
    @pytest.mark.asyncio
    async def test_audit_integration_workflow(self, workflow_components):
        """Test audit logging throughout the workflow."""
        components = workflow_components
        audit_logger = components["audit_logger"]
        
        # Test LLM call auditing
        await audit_logger.log_llm_call(
            session_id="test-audit",
            provider="fake",
            model="fake-model",
            prompt="Test prompt",
            response="Test response",
            tokens_used=100,
            latency_ms=500
        )
        
        # Test pattern match auditing
        await audit_logger.log_pattern_match(
            session_id="test-audit",
            pattern_id="PAT-001",
            score=0.85,
            accepted=True
        )
        
        # Verify audit data
        runs = await audit_logger.get_runs(session_id="test-audit")
        assert len(runs) == 1
        
        matches = await audit_logger.get_matches(session_id="test-audit")
        assert len(matches) == 1
        
        # Test statistics
        provider_stats = await audit_logger.get_provider_stats()
        assert "provider_stats" in provider_stats
        
        pattern_stats = await audit_logger.get_pattern_stats()
        assert "pattern_stats" in pattern_stats
    
    @pytest.mark.asyncio
    async def test_error_handling_workflow(self, workflow_components):
        """Test error handling throughout the workflow."""
        components = workflow_components
        
        # Test with invalid requirements
        invalid_requirements = {}  # Missing required fields
        
        session_id = "test-error-session"
        
        # Should handle gracefully
        try:
            components["session_store"].create_session(session_id, invalid_requirements)
            # Pattern matching should still work with empty requirements
            patterns = components["pattern_loader"].load_patterns()
            matches = await components["pattern_matcher"].match_patterns(invalid_requirements, patterns)
            # Should return empty matches or handle gracefully
            assert isinstance(matches, list)
        except Exception as e:
            # Should not crash the entire workflow
            assert isinstance(e, (ValueError, KeyError))
    
    @pytest.mark.asyncio
    async def test_concurrent_sessions_workflow(self, workflow_components):
        """Test handling multiple concurrent sessions."""
        components = workflow_components
        
        # Create multiple sessions concurrently
        sessions = []
        for i in range(5):
            requirements = {
                "description": f"Test automation task {i}",
                "domain": "data_processing"
            }
            session_id = f"concurrent-session-{i}"
            session = components["session_store"].create_session(session_id, requirements)
            sessions.append(session)
        
        # Process all sessions concurrently
        patterns = components["pattern_loader"].load_patterns()
        
        async def process_session(session):
            matches = await components["pattern_matcher"].match_patterns(session.requirements, patterns)
            recommendations = components["recommendation_service"].generate_recommendations(matches, session.requirements)
            return len(recommendations)
        
        # Run concurrent processing
        results = await asyncio.gather(*[process_session(session) for session in sessions])
        
        # All sessions should have been processed
        assert len(results) == 5
        assert all(result >= 0 for result in results)
    
    @pytest.mark.asyncio
    async def test_provider_switching_workflow(self, workflow_components):
        """Test switching between different LLM providers."""
        components = workflow_components
        
        # Test with different provider configurations
        providers = [
            FakeLLM(model_name="fake-gpt-4"),
            FakeLLM(model_name="fake-claude"),
            FakeLLM(model_name="fake-internal")
        ]
        
        requirements = {
            "description": "Test provider switching",
            "domain": "workflow_automation"
        }
        
        results = []
        for i, provider in enumerate(providers):
            # Update question loop with new provider
            components["question_loop"].llm_provider = provider
            
            session_id = f"provider-test-{i}"
            components["session_store"].create_session(session_id, requirements)
            
            # Generate questions with different providers
            qa_result = await components["question_loop"].generate_questions(requirements, session_id)
            results.append(qa_result)
        
        # All providers should work
        assert len(results) == 3
        for result in results:
            assert isinstance(result.next_questions, list)
            assert 0 <= result.confidence <= 1
    
    @pytest.mark.asyncio
    async def test_large_dataset_workflow(self, workflow_components, temp_dir):
        """Test workflow with large datasets."""
        components = workflow_components
        
        # Create many patterns
        patterns_dir = temp_dir / "large_patterns"
        patterns_dir.mkdir()
        
        # Generate 50 patterns
        for i in range(50):
            pattern = {
                "pattern_id": f"PAT-{i:03d}",
                "name": f"Pattern {i}",
                "description": f"Test pattern {i} for automation",
                "feasibility": "Automatable" if i % 2 == 0 else "Partially Automatable",
                "confidence_score": 0.5 + (i % 5) * 0.1,
                "domain": ["data_processing", "api_integration", "workflow_automation"][i % 3],
                "pattern_type": "workflow",
                "tech_stack": ["Python", "JavaScript", "Java"][i % 3:i % 3 + 1],
                "tags": [f"tag{i}", f"category{i % 5}"]
            }
            
            with open(patterns_dir / f"PAT-{i:03d}.json", "w") as f:
                json.dump(pattern, f)
        
        # Load large pattern set
        large_pattern_loader = PatternLoader(str(patterns_dir))
        patterns = large_pattern_loader.load_patterns()
        assert len(patterns) == 50
        
        # Test pattern matching with large dataset
        requirements = {
            "description": "Large scale data processing automation",
            "domain": "data_processing"
        }
        
        matches = await components["pattern_matcher"].match_patterns(requirements, patterns)
        
        # Should handle large dataset efficiently
        assert len(matches) > 0
        assert len(matches) <= 10  # Should limit results
        
        # Generate recommendations
        recommendations = components["recommendation_service"].generate_recommendations(matches, requirements)
        assert len(recommendations) == len(matches)


class TestAPIWorkflows:
    """Test API endpoint workflows."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        from fastapi.testclient import TestClient
        return TestClient(app)
    
    def test_health_check_workflow(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        assert response.json()["status"] == "healthy"
    
    @patch('app.api.get_llm_provider')
    @patch('app.api.get_session_store')
    def test_ingest_requirements_workflow(self, mock_session_store, mock_llm_provider, client):
        """Test requirements ingestion workflow."""
        # Mock dependencies
        mock_store = Mock()
        mock_store.create_session.return_value = Mock(session_id="test-123")
        mock_session_store.return_value = mock_store
        
        mock_provider = Mock()
        mock_llm_provider.return_value = mock_provider
        
        # Test request
        request_data = {
            "requirements": "Automate data processing workflow",
            "source": "text"
        }
        
        response = client.post("/api/v1/ingest", json=request_data)
        
        # Should create session
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        mock_store.create_session.assert_called_once()
    
    @patch('app.api.get_export_service')
    def test_export_workflow(self, mock_export_service, client):
        """Test export workflow."""
        # Mock export service
        mock_service = Mock()
        mock_service.export_session = AsyncMock(return_value={
            "file_path": "/tmp/test.json",
            "download_url": "/downloads/test.json",
            "file_size": 1024
        })
        mock_export_service.return_value = mock_service
        
        # Test export request
        response = client.post("/api/v1/export", json={
            "session_id": "test-123",
            "format": "json"
        })
        
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data


class TestPerformanceWorkflows:
    """Test performance-related workflows."""
    
    @pytest.mark.asyncio
    async def test_pattern_matching_performance(self, workflow_components):
        """Test pattern matching performance with various input sizes."""
        components = workflow_components
        
        # Test with different requirement sizes
        test_cases = [
            {"description": "Short task"},
            {"description": "Medium length automation task with some details"},
            {"description": " ".join(["Long"] * 100) + " automation task with extensive details"}
        ]
        
        patterns = components["pattern_loader"].load_patterns()
        
        for requirements in test_cases:
            import time
            start_time = time.time()
            
            matches = await components["pattern_matcher"].match_patterns(requirements, patterns)
            
            end_time = time.time()
            processing_time = end_time - start_time
            
            # Should complete within reasonable time (< 5 seconds for test data)
            assert processing_time < 5.0
            assert isinstance(matches, list)
    
    @pytest.mark.asyncio
    async def test_concurrent_processing_performance(self, workflow_components):
        """Test concurrent processing performance."""
        components = workflow_components
        
        # Create multiple concurrent requests
        requirements_list = [
            {"description": f"Concurrent task {i}", "domain": "data_processing"}
            for i in range(10)
        ]
        
        patterns = components["pattern_loader"].load_patterns()
        
        async def process_requirement(req):
            return await components["pattern_matcher"].match_patterns(req, patterns)
        
        import time
        start_time = time.time()
        
        # Process all concurrently
        results = await asyncio.gather(*[process_requirement(req) for req in requirements_list])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Concurrent processing should be faster than sequential
        assert len(results) == 10
        assert total_time < 10.0  # Should complete within 10 seconds
        assert all(isinstance(result, list) for result in results)