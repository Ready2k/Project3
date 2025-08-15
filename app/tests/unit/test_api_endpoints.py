"""Unit tests for API endpoints."""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient

from app.api import app
from app.state.store import SessionState


class TestAPIEndpoints:
    """Test API endpoints."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_health_endpoint(self, client):
        """Test health check endpoint."""
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "version" in data
        assert data["version"] == "AAA-2.1.0"
        assert "release_name" in data
        assert data["release_name"] == "Technology Catalog"
    
    # No root endpoint exists in the current API
    
    @patch('app.api.get_session_store')
    def test_ingest_text_requirements(self, mock_session_store, client):
        """Test ingesting text requirements."""
        # Mock dependencies
        mock_store = Mock()
        mock_store.update_session = AsyncMock(return_value=None)
        mock_session_store.return_value = mock_store
        
        # No need to mock LLM provider for basic ingest
        
        # Test request
        request_data = {
            "source": "text",
            "payload": {
                "text": "Automate data processing workflow"
            }
        }
        
        response = client.post("/ingest", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        
        # Verify session updates were called
        assert mock_store.update_session.call_count >= 1
    
    @patch('app.api.get_jira_service')
    @patch('app.api.get_session_store')
    def test_ingest_jira_requirements(self, mock_session_store, mock_jira_service, client):
        """Test ingesting JIRA requirements."""
        # Mock dependencies
        mock_store = Mock()
        mock_session = Mock()
        mock_session.session_id = "jira-session-123"
        mock_store.create_session.return_value = mock_session
        mock_session_store.return_value = mock_store
        
        mock_jira = Mock()
        mock_jira.fetch_ticket = AsyncMock(return_value={
            "key": "TEST-123",
            "summary": "Test ticket",
            "description": "Test description"
        })
        mock_jira.map_ticket_to_requirements = Mock(return_value={
            "description": "JIRA ticket: Test description",
            "jira_key": "TEST-123"
        })
        mock_jira_service.return_value = mock_jira
        
        # Test request
        request_data = {
            "source": "jira",
            "payload": {
                "ticket_key": "TEST-123"
            }
        }
        
        response = client.post("/ingest", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "session_id" in data
        assert data["session_id"] == "jira-session-123"
        
        # Verify JIRA integration
        mock_jira.fetch_ticket.assert_called_once_with("TEST-123")
        mock_jira.map_ticket_to_requirements.assert_called_once()
    
    def test_ingest_invalid_source(self, client):
        """Test ingesting with invalid source."""
        request_data = {
            "source": "invalid_source",
            "payload": {
                "text": "Test requirements"
            }
        }
        
        response = client.post("/ingest", json=request_data)
        
        assert response.status_code == 422  # Pydantic validation error
        data = response.json()
        assert "detail" in data
    
    def test_ingest_missing_requirements(self, client):
        """Test ingesting without payload."""
        request_data = {
            "source": "text"
            # Missing payload
        }
        
        response = client.post("/ingest", json=request_data)
        
        assert response.status_code == 422  # Validation error
    
    @patch('app.api.get_question_loop')
    @patch('app.api.get_session_store')
    def test_generate_questions(self, mock_session_store, mock_question_loop, client):
        """Test generating questions."""
        # Mock dependencies
        mock_store = Mock()
        mock_session = Mock()
        mock_session.requirements = {"description": "Test requirements"}
        mock_store.get_session.return_value = mock_session
        mock_session_store.return_value = mock_store
        
        mock_qa_loop = Mock()
        mock_qa_result = Mock()
        mock_qa_result.to_dict.return_value = {
            "complete": False,
            "confidence": 0.6,
            "next_questions": [
                {"question": "What is the frequency?", "id": "frequency", "type": "text"}
            ]
        }
        mock_qa_loop.generate_questions = AsyncMock(return_value=mock_qa_result)
        mock_question_loop.return_value = mock_qa_loop
        
        # Test request
        session_id = "test-session-123"
        
        response = client.get(f"/qa/{session_id}/questions")
        
        assert response.status_code == 200
        data = response.json()
        assert "complete" in data
        assert "confidence" in data
        assert "next_questions" in data
        assert len(data["next_questions"]) == 1
        
        # Verify question generation
        mock_qa_loop.generate_questions.assert_called_once()
    
    def test_generate_questions_invalid_session(self, client):
        """Test generating questions with invalid session."""
        with patch('app.api.get_session_store') as mock_session_store:
            mock_store = Mock()
            mock_store.get_session.return_value = None
            mock_session_store.return_value = mock_store
            
            session_id = "invalid-session"
            
            response = client.get(f"/qa/{session_id}/questions")
            
            assert response.status_code == 404
            data = response.json()
            assert "error" in data
            assert "Session not found" in data["error"]
    
    @patch('app.api.get_question_loop')
    @patch('app.api.get_session_store')
    def test_submit_answers(self, mock_session_store, mock_question_loop, client):
        """Test submitting Q&A answers."""
        # Mock dependencies
        mock_store = Mock()
        mock_session = Mock()
        mock_store.get_session.return_value = mock_session
        mock_session_store.return_value = mock_store
        
        mock_qa_loop = Mock()
        mock_qa_result = Mock()
        mock_qa_result.to_dict.return_value = {
            "complete": True,
            "confidence": 0.9,
            "next_questions": []
        }
        mock_qa_loop.process_answers = AsyncMock(return_value=mock_qa_result)
        mock_question_loop.return_value = mock_qa_loop
        
        # Test request
        session_id = "test-session-123"
        request_data = {
            "answers": {
                "frequency": "daily",
                "data_sensitivity": "medium"
            }
        }
        
        response = client.post(f"/qa/{session_id}", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["complete"] is True
        assert data["confidence"] == 0.9
        
        # Verify answer processing
        mock_qa_loop.process_answers.assert_called_once()
    
    @patch('app.api.get_recommendation_service')
    @patch('app.api.get_pattern_matcher')
    @patch('app.api.get_pattern_loader')
    @patch('app.api.get_session_store')
    def test_generate_recommendations(self, mock_session_store, mock_pattern_loader, 
                                    mock_pattern_matcher, mock_recommendation_service, client):
        """Test generating recommendations."""
        # Mock dependencies
        mock_store = Mock()
        mock_session = Mock()
        mock_session.requirements = {"description": "Test automation"}
        mock_store.get_session.return_value = mock_session
        mock_session_store.return_value = mock_store
        
        mock_loader = Mock()
        mock_patterns = [{"pattern_id": "PAT-001", "name": "Test Pattern"}]
        mock_loader.load_patterns.return_value = mock_patterns
        mock_pattern_loader.return_value = mock_loader
        
        mock_matcher = Mock()
        mock_matches = [Mock()]
        mock_matches[0].to_dict.return_value = {"pattern_id": "PAT-001", "confidence": 0.8}
        mock_matcher.match_patterns = AsyncMock(return_value=mock_matches)
        mock_pattern_matcher.return_value = mock_matcher
        
        mock_service = Mock()
        mock_recommendations = [Mock()]
        mock_recommendations[0].to_dict.return_value = {
            "pattern_id": "PAT-001",
            "feasibility": "Automatable",
            "confidence": 0.85
        }
        mock_service.generate_recommendations.return_value = mock_recommendations
        mock_recommendation_service.return_value = mock_service
        
        # Test request
        request_data = {
            "session_id": "test-session-123"
        }
        
        response = client.post("/recommend", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "recommendations" in data
        assert len(data["recommendations"]) == 1
        assert data["recommendations"][0]["pattern_id"] == "PAT-001"
        
        # Verify recommendation generation
        mock_matcher.match_patterns.assert_called_once()
        mock_service.generate_recommendations.assert_called_once()
    
    @patch('app.api.get_export_service')
    def test_export_session(self, mock_export_service, client):
        """Test exporting session."""
        # Mock export service
        mock_service = Mock()
        mock_service.export_session = AsyncMock(return_value={
            "file_path": "/tmp/export.json",
            "download_url": "/downloads/export.json",
            "file_size": 1024
        })
        mock_export_service.return_value = mock_service
        
        # Test request
        request_data = {
            "session_id": "test-session-123",
            "format": "json"
        }
        
        response = client.post("/export", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert "download_url" in data
        assert "file_size" in data
        
        # Verify export
        mock_service.export_session.assert_called_once_with("test-session-123", "json")
    
    def test_export_invalid_format(self, client):
        """Test exporting with invalid format."""
        request_data = {
            "session_id": "test-session-123",
            "format": "invalid_format"
        }
        
        response = client.post("/export", json=request_data)
        
        assert response.status_code == 400
        data = response.json()
        assert "error" in data
        assert "Unsupported format" in data["error"]
    
    @patch('app.api.get_llm_provider')
    def test_test_provider_connection(self, mock_llm_provider, client):
        """Test testing provider connection."""
        # Mock provider
        mock_provider = Mock()
        mock_provider.test_connection = AsyncMock(return_value=True)
        mock_llm_provider.return_value = mock_provider
        
        # Test request
        request_data = {
            "provider_type": "openai",
            "config": {
                "model": "gpt-4",
                "api_key": "test-key"
            }
        }
        
        response = client.post("/providers/test", json=request_data)
        
        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "message" in data
        
        # Verify connection test
        mock_provider.test_connection.assert_called_once()
    
    def test_test_provider_connection_failure(self, client):
        """Test provider connection failure."""
        with patch('app.api.get_llm_provider') as mock_llm_provider:
            mock_provider = Mock()
            mock_provider.test_connection = AsyncMock(side_effect=Exception("Connection failed"))
            mock_llm_provider.return_value = mock_provider
            
            request_data = {
                "provider_type": "openai",
                "config": {
                    "model": "gpt-4",
                    "api_key": "invalid-key"
                }
            }
            
            response = client.post("/providers/test", json=request_data)
            
            assert response.status_code == 200
            data = response.json()
            assert data["success"] is False
            assert "error" in data
    
    # Session info and patterns endpoints don't exist in the current API


class TestAPIErrorHandling:
    """Test API error handling."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_invalid_json(self, client):
        """Test handling invalid JSON."""
        response = client.post(
            "/ingest",
            data="invalid json",
            headers={"Content-Type": "application/json"}
        )
        
        assert response.status_code == 422
    
    def test_missing_content_type(self, client):
        """Test handling missing content type."""
        response = client.post("/ingest", data="test data")
        
        assert response.status_code == 422
    
    def test_method_not_allowed(self, client):
        """Test method not allowed."""
        response = client.put("/ingest")
        
        assert response.status_code == 405
    
    def test_not_found_endpoint(self, client):
        """Test accessing non-existent endpoint."""
        response = client.get("/non-existent")
        
        assert response.status_code == 404
    
    @patch('app.api.get_session_store')
    def test_internal_server_error(self, mock_session_store, client):
        """Test internal server error handling."""
        # Mock store to raise exception
        mock_session_store.side_effect = Exception("Database connection failed")
        
        request_data = {
            "requirements": "Test requirements",
            "source": "text"
        }
        
        response = client.post("/ingest", json=request_data)
        
        assert response.status_code == 500
        data = response.json()
        assert "error" in data


class TestAPIValidation:
    """Test API request validation."""
    
    @pytest.fixture
    def client(self):
        """Create test client."""
        return TestClient(app)
    
    def test_ingest_validation(self, client):
        """Test ingest request validation."""
        # Missing required fields
        response = client.post("/ingest", json={})
        assert response.status_code == 422
        
        # Invalid source
        response = client.post("/ingest", json={
            "source": "invalid",
            "payload": {"text": "test"}
        })
        assert response.status_code == 422
        
        # Missing payload for text source
        response = client.post("/ingest", json={
            "source": "text"
        })
        assert response.status_code == 422
    
    def test_questions_validation(self, client):
        """Test questions request validation."""
        # Missing session_id in URL
        response = client.get("/qa//questions")  # Empty session_id
        assert response.status_code == 422
        
        # Invalid session_id format
        response = client.get("/qa/invalid-session/questions")
        assert response.status_code == 404  # Session not found
    
    def test_answers_validation(self, client):
        """Test answers request validation."""
        # Missing required fields
        response = client.post("/qa/test-session/", json={})
        assert response.status_code == 422
        
        # Invalid answers format
        response = client.post("/qa/test-session/", json={
            "answers": "not a dict"
        })
        assert response.status_code == 422
    
    def test_export_validation(self, client):
        """Test export request validation."""
        # Missing required fields
        response = client.post("/export", json={})
        assert response.status_code == 422
        
        # Invalid format
        response = client.post("/export", json={
            "session_id": "test",
            "format": "invalid"
        })
        assert response.status_code == 422  # Pydantic validation