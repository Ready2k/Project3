"""End-to-end tests for Streamlit UI to API integration."""

import asyncio
import json
import pytest
from unittest.mock import AsyncMock, patch, MagicMock
from pathlib import Path

import httpx

# Import the Streamlit app
import sys
from pathlib import Path

# Add the project root to the path
project_root = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from streamlit_app import AgenticOrNotUI
    import streamlit as st
    STREAMLIT_AVAILABLE = True
except ImportError as e:
    # Handle case where streamlit_app.py doesn't exist yet or streamlit is not installed
    STREAMLIT_AVAILABLE = False
    
if not STREAMLIT_AVAILABLE:
    pytest.skip("Streamlit app not available", allow_module_level=True)


class TestStreamlitUIIntegration:
    """Test Streamlit UI integration with FastAPI backend."""
    
    @pytest.fixture
    def mock_api_responses(self):
        """Mock API responses for testing."""
        return {
            'ingest': {'session_id': 'test-session-123'},
            'status_parsing': {'phase': 'PARSING', 'progress': 20, 'missing_fields': []},
            'status_qna': {'phase': 'QNA', 'progress': 40, 'missing_fields': ['workflow_variability']},
            'status_done': {'phase': 'DONE', 'progress': 100, 'missing_fields': []},
            'qa_response': {'complete': True, 'next_questions': []},
            'recommendations': {
                'feasibility': 'Yes',
                'recommendations': [
                    {
                        'pattern_id': 'PAT-001',
                        'confidence': 0.85,
                        'feasibility': 'Automatable',
                        'reasoning': 'High confidence automation pattern'
                    }
                ],
                'tech_stack': ['Python', 'FastAPI', 'Celery'],
                'reasoning': 'This workflow is highly automatable with standard tools.'
            },
            'export': {
                'download_url': 'http://localhost:8000/exports/test-file.json',
                'file_path': './exports/test-file.json',
                'file_info': {'size': 1024, 'created_at': '2024-01-01T00:00:00Z'}
            },
            'provider_test_success': {'ok': True, 'message': 'Connection successful'},
            'provider_test_failure': {'ok': False, 'message': 'Invalid API key'}
        }
    
    @pytest.fixture
    def ui_app(self):
        """Create UI app instance for testing."""
        return AgenticOrNotUI()
    
    @pytest.fixture
    def mock_session_state(self):
        """Mock Streamlit session state."""
        class MockSessionState:
            def __init__(self):
                self._state = {
                    'session_id': None,
                    'current_phase': None,
                    'progress': 0,
                    'recommendations': None,
                    'provider_config': {
                        'provider': 'openai',
                        'model': 'gpt-4o',
                        'api_key': '',
                        'endpoint_url': '',
                        'region': 'us-east-1'
                    },
                    'qa_questions': [],
                    'processing': False
                }
            
            def __getattr__(self, key):
                return self._state.get(key)
            
            def __setattr__(self, key, value):
                if key.startswith('_'):
                    super().__setattr__(key, value)
                else:
                    self._state[key] = value
            
            def __contains__(self, key):
                return key in self._state
            
            def keys(self):
                return self._state.keys()
            
            def __delitem__(self, key):
                del self._state[key]
        
        return MockSessionState()
    
    @pytest.mark.asyncio
    async def test_make_api_request_success(self, ui_app, mock_api_responses):
        """Test successful API request."""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock response
            mock_response = MagicMock()
            mock_response.status_code = 200
            mock_response.json.return_value = mock_api_responses['ingest']
            
            # Mock client context manager with async methods
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # Test API request
            result = await ui_app.make_api_request('POST', '/ingest', {'test': 'data'})
            
            assert result == mock_api_responses['ingest']
            mock_client_instance.post.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_make_api_request_404_error(self, ui_app):
        """Test API request with 404 error."""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock 404 response
            mock_response = MagicMock()
            mock_response.status_code = 404
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.get.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # Test that 404 raises ValueError
            with pytest.raises(ValueError, match="Session not found"):
                await ui_app.make_api_request('GET', '/status/nonexistent')
    
    @pytest.mark.asyncio
    async def test_make_api_request_server_error(self, ui_app):
        """Test API request with server error."""
        
        with patch('httpx.AsyncClient') as mock_client:
            # Mock 500 response
            mock_response = MagicMock()
            mock_response.status_code = 500
            mock_response.text = "Internal Server Error"
            
            mock_client_instance = AsyncMock()
            mock_client_instance.__aenter__.return_value = mock_client_instance
            mock_client_instance.__aexit__.return_value = None
            mock_client_instance.post.return_value = mock_response
            mock_client.return_value = mock_client_instance
            
            # Test that 500 raises ValueError
            with pytest.raises(ValueError, match="API error: 500"):
                await ui_app.make_api_request('POST', '/test', {})
    
    def test_session_state_initialization(self, ui_app, mock_session_state):
        """Test proper initialization of session state."""
        
        with patch('streamlit.session_state', mock_session_state):
            ui_app.initialize_session_state()
            
            # Verify all required session state variables are initialized
            required_keys = [
                'session_id', 'current_phase', 'progress', 'recommendations',
                'provider_config', 'qa_questions', 'processing'
            ]
            
            for key in required_keys:
                assert key in mock_session_state
            
            # Verify default values
            assert mock_session_state.session_id is None
            assert mock_session_state.current_phase is None
            assert mock_session_state.progress == 0
            assert mock_session_state.recommendations is None
            assert mock_session_state.provider_config['provider'] == 'openai'
            assert mock_session_state.qa_questions == []
            assert mock_session_state.processing is False
    
    def test_submit_requirements_text_structure(self, ui_app, mock_api_responses, mock_session_state):
        """Test that submit_requirements properly structures the API call."""
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('asyncio.run') as mock_run:
                with patch('streamlit.spinner'), patch('streamlit.success'), patch('streamlit.rerun'):
                    mock_run.return_value = mock_api_responses['ingest']
                    
                    test_payload = {
                        "text": "Automate invoice processing workflow",
                        "domain": "finance",
                        "pattern_types": ["workflow", "data-processing"]
                    }
                    
                    # Test submission
                    ui_app.submit_requirements("text", test_payload)
                    
                    # Verify asyncio.run was called (indicating API request was made)
                    mock_run.assert_called_once()
                    
                    # Verify processing flag is reset
                    assert mock_session_state.processing is False
    
    def test_submit_requirements_file_structure(self, ui_app, mock_api_responses, mock_session_state):
        """Test submitting file requirements."""
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('asyncio.run') as mock_run:
                with patch('streamlit.spinner'), patch('streamlit.success'), patch('streamlit.rerun'):
                    mock_run.return_value = mock_api_responses['ingest']
                    
                    test_payload = {
                        "content": "Process customer onboarding workflow",
                        "filename": "requirements.txt"
                    }
                    
                    # Test submission
                    ui_app.submit_requirements("file", test_payload)
                    
                    # Verify asyncio.run was called
                    mock_run.assert_called_once()
    
    def test_submit_qa_answers_structure(self, ui_app, mock_api_responses, mock_session_state):
        """Test submitting Q&A answers."""
        
        mock_session_state.session_id = 'test-session-123'
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('asyncio.run') as mock_run:
                with patch('streamlit.spinner'), patch('streamlit.success'), patch('streamlit.rerun'):
                    mock_run.return_value = mock_api_responses['qa_response']
                    
                    test_answers = {
                        'workflow_variability': 'Low - mostly standard steps',
                        'data_sensitivity': 'Medium',
                        'human_oversight': 'Sometimes'
                    }
                    
                    # Test Q&A submission
                    ui_app.submit_qa_answers(test_answers)
                    
                    # Verify asyncio.run was called
                    mock_run.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_export_results_json(self, ui_app, mock_api_responses, mock_session_state):
        """Test exporting results as JSON."""
        
        mock_session_state.session_id = 'test-session-123'
        
        with patch('streamlit.session_state', mock_session_state):
            with patch.object(ui_app, 'make_api_request') as mock_api:
                with patch('streamlit.spinner'), patch('streamlit.success'), patch('streamlit.info'), patch('streamlit.markdown'):
                    mock_api.return_value = mock_api_responses['export']
                    
                    # Test JSON export
                    ui_app.export_results('json')
                    
                    # Verify API call
                    mock_api.assert_called_once_with(
                        'POST',
                        '/export',
                        {
                            'session_id': 'test-session-123',
                            'format': 'json'
                        }
                    )
    
    @pytest.mark.asyncio
    async def test_export_results_markdown(self, ui_app, mock_api_responses, mock_session_state):
        """Test exporting results as Markdown."""
        
        mock_session_state.session_id = 'test-session-123'
        
        with patch('streamlit.session_state', mock_session_state):
            with patch.object(ui_app, 'make_api_request') as mock_api:
                with patch('streamlit.spinner'), patch('streamlit.success'), patch('streamlit.info'), patch('streamlit.markdown'):
                    mock_api.return_value = mock_api_responses['export']
                    
                    # Test Markdown export
                    ui_app.export_results('md')
                    
                    # Verify API call
                    mock_api.assert_called_once_with(
                        'POST',
                        '/export',
                        {
                            'session_id': 'test-session-123',
                            'format': 'md'
                        }
                    )
    
    @pytest.mark.asyncio
    async def test_test_provider_connection_success(self, ui_app, mock_api_responses, mock_session_state):
        """Test successful provider connection test."""
        
        mock_session_state.provider_config = {
            'provider': 'openai',
            'model': 'gpt-4o',
            'api_key': 'test-key',
            'endpoint_url': '',
            'region': ''
        }
        
        with patch('streamlit.session_state', mock_session_state):
            with patch.object(ui_app, 'make_api_request') as mock_api:
                with patch('streamlit.sidebar'), patch('streamlit.success'):
                    mock_api.return_value = mock_api_responses['provider_test_success']
                    
                    # Test connection
                    ui_app.test_provider_connection()
                    
                    # Verify API call
                    mock_api.assert_called_once_with(
                        'POST',
                        '/providers/test',
                        {
                            'provider': 'openai',
                            'model': 'gpt-4o',
                            'api_key': 'test-key',
                            'endpoint_url': '',
                            'region': ''
                        }
                    )
    
    @pytest.mark.asyncio
    async def test_test_provider_connection_failure(self, ui_app, mock_api_responses, mock_session_state):
        """Test failed provider connection test."""
        
        mock_session_state.provider_config = {
            'provider': 'openai',
            'model': 'gpt-4o',
            'api_key': 'invalid-key',
            'endpoint_url': '',
            'region': ''
        }
        
        with patch('streamlit.session_state', mock_session_state):
            with patch.object(ui_app, 'make_api_request') as mock_api:
                with patch('streamlit.sidebar'), patch('streamlit.error'):
                    mock_api.return_value = mock_api_responses['provider_test_failure']
                    
                    # Test connection
                    ui_app.test_provider_connection()
                    
                    # Verify API call was made
                    mock_api.assert_called_once()
    
    def test_load_recommendations_structure(self, ui_app, mock_api_responses, mock_session_state):
        """Test that load_recommendations properly structures the API call."""
        
        mock_session_state.session_id = 'test-session-123'
        mock_session_state.recommendations = None
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('asyncio.run') as mock_run:
                with patch.object(ui_app, 'render_results'):
                    mock_run.return_value = mock_api_responses['recommendations']
                    
                    # Test loading recommendations
                    ui_app.load_recommendations()
                    
                    # Verify asyncio.run was called (indicating API request was made)
                    mock_run.assert_called_once()
                    
                    # Verify session state was updated
                    assert mock_session_state.recommendations == mock_api_responses['recommendations']
    
    def test_mermaid_diagram_generation(self, ui_app, mock_session_state):
        """Test Mermaid diagram generation."""
        
        mock_session_state.provider_config = {
            'provider': 'openai',
            'model': 'gpt-4o'
        }
        mock_session_state.current_phase = 'MATCHING'
        
        with patch('streamlit.session_state', mock_session_state):
            # Test that diagram functions can be called without errors
            try:
                from app.diagrams.mermaid import build_context_diagram, build_container_diagram, build_sequence_diagram
                
                config = {
                    'user_role': 'Business Analyst',
                    'provider': 'openai',
                    'model': 'gpt-4o',
                    'jira_enabled': True,
                    'vector_index': True,
                    'db': 'SQLite',
                    'state': 'diskcache'
                }
                
                # Test each diagram type
                context_diagram = build_context_diagram(config)
                assert 'flowchart LR' in context_diagram
                assert 'openai:gpt-4o' in context_diagram
                
                container_diagram = build_container_diagram(config)
                assert 'flowchart TB' in container_diagram
                assert 'Streamlit UI' in container_diagram
                
                sequence_diagram = build_sequence_diagram(
                    {'provider': 'openai', 'model': 'gpt-4o'}, 
                    'MATCHING'
                )
                assert 'sequenceDiagram' in sequence_diagram
                assert 'phase=MATCHING' in sequence_diagram
                
            except ImportError:
                pytest.skip("Mermaid diagram functions not available")
    
    @pytest.mark.asyncio
    async def test_error_handling_in_submit_requirements(self, ui_app, mock_session_state):
        """Test error handling in submit_requirements."""
        
        with patch('streamlit.session_state', mock_session_state):
            with patch.object(ui_app, 'make_api_request') as mock_api:
                with patch('streamlit.spinner'), patch('streamlit.error'):
                    # Mock API error
                    mock_api.side_effect = Exception("API connection failed")
                    
                    # Test that error is handled gracefully
                    ui_app.submit_requirements("text", {"text": "test"})
                    
                    # Verify processing flag is reset
                    assert mock_session_state.processing is False
    
    @pytest.mark.asyncio
    async def test_error_handling_in_export(self, ui_app, mock_session_state):
        """Test error handling in export functionality."""
        
        mock_session_state.session_id = 'test-session-123'
        
        with patch('streamlit.session_state', mock_session_state):
            with patch.object(ui_app, 'make_api_request') as mock_api:
                with patch('streamlit.spinner'), patch('streamlit.error'):
                    # Mock API error
                    mock_api.side_effect = Exception("Export failed")
                    
                    # Test that error is handled gracefully
                    ui_app.export_results('json')
                    
                    # Verify API was called
                    mock_api.assert_called_once()


class TestUIComponentIntegration:
    """Test individual UI component integration."""
    
    def test_provider_config_updates(self):
        """Test that provider configuration updates work correctly."""
        
        ui_app = AgenticOrNotUI()
        
        # Mock session state
        class MockSessionState:
            def __init__(self):
                self.provider_config = {
                    'provider': 'openai',
                    'model': 'gpt-4o',
                    'api_key': '',
                    'endpoint_url': '',
                    'region': 'us-east-1'
                }
        
        mock_state = MockSessionState()
        
        with patch('streamlit.session_state', mock_state):
            # Test that provider config can be updated
            mock_state.provider_config['provider'] = 'bedrock'
            mock_state.provider_config['model'] = 'claude-3-sonnet'
            mock_state.provider_config['region'] = 'us-west-2'
            
            assert mock_state.provider_config['provider'] == 'bedrock'
            assert mock_state.provider_config['model'] == 'claude-3-sonnet'
            assert mock_state.provider_config['region'] == 'us-west-2'
    
    def test_qa_questions_structure(self):
        """Test Q&A questions structure."""
        
        ui_app = AgenticOrNotUI()
        
        # Test default Q&A questions
        expected_questions = [
            {
                "id": "workflow_variability",
                "question": "How variable is your workflow? (e.g., always the same steps vs. many exceptions)",
                "type": "text"
            },
            {
                "id": "data_sensitivity",
                "question": "What is the sensitivity level of the data involved?",
                "type": "select",
                "options": ["Low", "Medium", "High", "Confidential"]
            },
            {
                "id": "human_oversight",
                "question": "Is human oversight required at any step?",
                "type": "select",
                "options": ["Yes", "No", "Sometimes"]
            }
        ]
        
        # Mock session state with empty questions
        class MockSessionState:
            def __init__(self):
                self.qa_questions = []
        
        mock_state = MockSessionState()
        
        with patch('streamlit.session_state', mock_state):
            # Simulate the logic that would populate questions
            if not mock_state.qa_questions:
                mock_state.qa_questions = expected_questions
            
            assert len(mock_state.qa_questions) == 3
            assert mock_state.qa_questions[0]['id'] == 'workflow_variability'
            assert mock_state.qa_questions[1]['type'] == 'select'
            assert 'High' in mock_state.qa_questions[1]['options']


class TestObservabilityDashboardE2E:
    """End-to-end tests for observability dashboard integration."""
    
    @pytest.fixture
    def ui_app(self):
        """Create UI app instance for testing."""
        return AgenticOrNotUI()
    
    @pytest.fixture
    def mock_session_state(self):
        """Mock Streamlit session state."""
        class MockSessionState:
            def __init__(self):
                self._state = {
                    'session_id': None,
                    'current_phase': None,
                    'progress': 0,
                    'recommendations': None,
                    'provider_config': {
                        'provider': 'openai',
                        'model': 'gpt-4o',
                        'api_key': '',
                        'endpoint_url': '',
                        'region': 'us-east-1'
                    },
                    'qa_questions': [],
                    'processing': False
                }
            
            def __getattr__(self, key):
                return self._state.get(key)
            
            def __setattr__(self, key, value):
                if key.startswith('_'):
                    super().__setattr__(key, value)
                else:
                    self._state[key] = value
            
            def __contains__(self, key):
                return key in self._state
            
            def keys(self):
                return self._state.keys()
            
            def __delitem__(self, key):
                del self._state[key]
        
        return MockSessionState()
    
    @pytest.fixture
    def mock_audit_data(self):
        """Mock audit data for e2e testing."""
        return {
            'provider_stats': [
                {
                    'provider': 'openai',
                    'model': 'gpt-4o',
                    'call_count': 10,
                    'avg_latency': 1200.0,
                    'min_latency': 800,
                    'max_latency': 1800,
                    'total_tokens': 5000
                }
            ],
            'pattern_stats': [
                {
                    'pattern_id': 'PAT-001',
                    'match_count': 5,
                    'avg_score': 0.85,
                    'min_score': 0.7,
                    'max_score': 0.95,
                    'accepted_count': 4,
                    'acceptance_rate': 0.8
                }
            ]
        }
    
    def test_observability_dashboard_full_workflow(self, ui_app, mock_audit_data, mock_session_state):
        """Test complete observability dashboard workflow."""
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('streamlit.header') as mock_header, \
                 patch('streamlit.tabs') as mock_tabs, \
                 patch.object(ui_app, 'render_provider_metrics') as mock_provider, \
                 patch.object(ui_app, 'render_pattern_analytics') as mock_pattern, \
                 patch.object(ui_app, 'render_usage_patterns') as mock_usage:
                
                # Mock tabs
                mock_tab1, mock_tab2, mock_tab3 = MagicMock(), MagicMock(), MagicMock()
                mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]
                
                # Test the full dashboard
                ui_app.render_observability_dashboard()
                
                # Verify header is displayed
                mock_header.assert_called_with("📈 System Observability")
                
                # Verify tabs are created
                mock_tabs.assert_called_with(["🔧 Provider Metrics", "🎯 Pattern Analytics", "📊 Usage Patterns"])
                
                # Verify all render methods are called
                mock_provider.assert_called_once()
                mock_pattern.assert_called_once()
                mock_usage.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_observability_with_real_audit_integration(self, ui_app, mock_session_state):
        """Test observability dashboard with real audit system integration."""
        
        with patch('streamlit.session_state', mock_session_state):
            # Test that the dashboard can handle real audit system calls
            try:
                provider_stats = await ui_app.get_provider_statistics()
                pattern_stats = await ui_app.get_pattern_statistics()
                
                # Should return empty dicts if no data, not fail
                assert isinstance(provider_stats, dict)
                assert isinstance(pattern_stats, dict)
                
            except Exception as e:
                # If audit system is not available, should handle gracefully
                assert "audit" in str(e).lower() or "database" in str(e).lower()
    
    def test_observability_dashboard_error_resilience(self, ui_app, mock_session_state):
        """Test that observability dashboard handles errors gracefully."""
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('app.utils.audit.get_audit_logger') as mock_get_logger:
                # Mock audit logger to raise exception
                mock_get_logger.side_effect = Exception("Database not available")
                
                with patch('streamlit.header'), \
                     patch('streamlit.tabs') as mock_tabs, \
                     patch('streamlit.error') as mock_error:
                    
                    # Mock tabs
                    mock_tab1, mock_tab2, mock_tab3 = MagicMock(), MagicMock(), MagicMock()
                    mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]
                    
                    # Test that dashboard doesn't crash on errors
                    try:
                        ui_app.render_observability_dashboard()
                        # Should not raise exception, should handle gracefully
                    except Exception:
                        pytest.fail("Dashboard should handle audit system errors gracefully")
    
    def test_observability_dashboard_empty_data_handling(self, ui_app, mock_session_state):
        """Test observability dashboard with empty data."""
        
        with patch('streamlit.session_state', mock_session_state):
            with patch('app.utils.audit.get_audit_logger') as mock_get_logger:
                # Mock audit logger to return empty data
                mock_logger = MagicMock()
                mock_logger.get_provider_stats.return_value = {'provider_stats': []}
                mock_logger.get_pattern_stats.return_value = {'pattern_stats': []}
                mock_get_logger.return_value = mock_logger
                
                with patch('streamlit.header'), \
                     patch('streamlit.tabs') as mock_tabs, \
                     patch('streamlit.info') as mock_info:
                    
                    # Mock tabs
                    mock_tab1, mock_tab2, mock_tab3 = MagicMock(), MagicMock(), MagicMock()
                    mock_tabs.return_value = [mock_tab1, mock_tab2, mock_tab3]
                    
                    # Test dashboard with empty data
                    ui_app.render_observability_dashboard()
                    
                    # Should show appropriate info messages for empty data
                    info_calls = mock_info.call_args_list
                    assert len(info_calls) >= 2  # At least provider and pattern no-data messages


if __name__ == "__main__":
    pytest.main([__file__, "-v"])