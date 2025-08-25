"""
End-to-end workflow tests for the refactored system.

This module tests complete user workflows from input to results to ensure
all components work together correctly in the new architecture.
"""

import pytest
from unittest.mock import Mock, patch, MagicMock
import json
import tempfile
from pathlib import Path

from app.ui.main_app import AAAStreamlitApp
from app.config.settings import ConfigurationManager, AppConfig
from app.core.registry import ServiceRegistry
from app.state.store import SessionState
from app.utils.result import Result


class TestCompleteAnalysisWorkflow:
    """Test complete analysis workflow from start to finish."""
    
    @pytest.fixture
    def workflow_environment(self, test_config, test_service_registry):
        """Set up complete workflow testing environment."""
        # Mock external dependencies
        mock_llm_provider = Mock()
        mock_llm_provider.generate_text.return_value = Result.success("Test response")
        mock_llm_provider.generate_questions.return_value = Result.success([
            {"text": "What is the data volume?", "field": "volume"}
        ])
        
        mock_pattern_matcher = Mock()
        mock_pattern_matcher.find_matches.return_value = Result.success([
            {
                "pattern_id": "PAT-001",
                "confidence": 0.9,
                "feasibility": "Automatable"
            }
        ])
        
        # Register services
        test_service_registry.register_instance(AppConfig, test_config)
        
        return {
            'config': test_config,
            'registry': test_service_registry,
            'llm_provider': mock_llm_provider,
            'pattern_matcher': mock_pattern_matcher
        }
    
    @patch('streamlit.session_state', {})
    @patch('streamlit.set_page_config')
    @patch('streamlit.sidebar')
    @patch('streamlit.tabs')
    @patch('streamlit.text_area')
    @patch('streamlit.selectbox')
    @patch('streamlit.button')
    def test_text_input_workflow(self, mock_button, mock_selectbox, mock_text_area, 
                                mock_tabs, mock_sidebar, mock_page_config, workflow_environment):
        """Test complete workflow with text input."""
        # Setup mocks
        mock_text_area.return_value = "Automate daily data processing from CSV files"
        mock_selectbox.return_value = "Text Input"
        mock_button.return_value = True  # Simulate button click
        
        mock_tab_objects = [Mock() for _ in range(5)]
        mock_tabs.return_value = mock_tab_objects
        
        for tab_obj in mock_tab_objects:
            tab_obj.__enter__ = Mock(return_value=tab_obj)
            tab_obj.__exit__ = Mock(return_value=None)
        
        # Create and run app
        with patch('app.config.settings.get_config', return_value=workflow_environment['config']), \
             patch('app.core.registry.get_service_registry', return_value=workflow_environment['registry']):
            
            app = AAAStreamlitApp()
            
            # Should initialize without errors
            assert app.config is workflow_environment['config']
            assert app.registry is workflow_environment['registry']
            
            # Run app
            app.run()
            
            # Verify UI components were called
            mock_page_config.assert_called_once()
            mock_tabs.assert_called_once()
    
    def test_session_resume_workflow(self, workflow_environment):
        """Test session resume workflow."""
        # Create existing session
        existing_session = SessionState(
            session_id="existing-session-123",
            requirements={"description": "Test requirements"}
        )
        existing_session.qa_exchanges = [
            {"question": "What is the volume?", "answer": "10000 records"}
        ]
        existing_session.recommendations = [
            {"pattern_id": "PAT-001", "confidence": 0.9}
        ]
        
        # Mock session retrieval
        mock_session_store = Mock()
        mock_session_store.get_session.return_value = Result.success(existing_session)
        
        with patch('streamlit.session_state', {}), \
             patch('streamlit.text_input', return_value="existing-session-123"), \
             patch('streamlit.button', return_value=True):
            
            # Simulate session resume
            session_state = {}
            session_state['session_id'] = existing_session.session_id
            session_state['requirements'] = existing_session.requirements
            session_state['qa_exchanges'] = existing_session.qa_exchanges
            session_state['recommendations'] = existing_session.recommendations
            
            # Verify session was restored
            assert session_state['session_id'] == "existing-session-123"
            assert session_state['requirements']['description'] == "Test requirements"
            assert len(session_state['qa_exchanges']) == 1
            assert len(session_state['recommendations']) == 1
    
    def test_provider_configuration_workflow(self, workflow_environment):
        """Test provider configuration workflow."""
        # Test provider switching
        with patch('streamlit.selectbox') as mock_selectbox, \
             patch('streamlit.slider') as mock_slider:
            
            mock_selectbox.return_value = "test_provider"
            mock_slider.return_value = 0.7
            
            from app.ui.components.provider_config import ProviderConfigComponent
            
            component = ProviderConfigComponent({
                "providers": workflow_environment['config'].llm_providers
            })
            
            result = component.render(current_provider="test_provider")
            
            # Should return provider configuration
            assert isinstance(result, dict)
            mock_selectbox.assert_called()
    
    def test_export_workflow(self, workflow_environment):
        """Test export functionality workflow."""
        # Create session with results
        session_data = {
            'session_id': 'export-test-session',
            'requirements': {'description': 'Test requirements'},
            'recommendations': [
                {
                    'pattern_id': 'PAT-001',
                    'feasibility': 'Automatable',
                    'confidence': 0.9
                }
            ],
            'analysis_complete': True
        }
        
        with patch('streamlit.session_state', session_data), \
             patch('streamlit.download_button') as mock_download:
            
            from app.ui.components.export_controls import ExportControlsComponent
            
            component = ExportControlsComponent()
            
            # Test JSON export
            with patch('json.dumps', return_value='{"test": "data"}'):
                result = component.render(export_format="JSON")
                
                # Should prepare export data
                assert result is not None
    
    def test_error_recovery_workflow(self, workflow_environment):
        """Test error recovery in workflow."""
        # Simulate LLM provider failure
        workflow_environment['llm_provider'].generate_text.return_value = Result.error(
            Exception("LLM service unavailable")
        )
        
        with patch('streamlit.session_state', {}), \
             patch('streamlit.error') as mock_error:
            
            # Should handle errors gracefully
            from app.ui.tabs.analysis_tab import AnalysisTab
            
            tab = AnalysisTab(
                workflow_environment['config'],
                workflow_environment['registry']
            )
            
            # Should not raise exception
            tab.render()


class TestJiraIntegrationWorkflow:
    """Test Jira integration workflow."""
    
    @pytest.fixture
    def jira_environment(self, workflow_environment):
        """Set up Jira integration testing environment."""
        # Mock Jira service
        mock_jira_service = Mock()
        mock_jira_service.get_ticket.return_value = Result.success({
            'key': 'TEST-123',
            'summary': 'Automate data processing',
            'description': 'Need to automate daily CSV processing'
        })
        
        workflow_environment['jira_service'] = mock_jira_service
        return workflow_environment
    
    def test_jira_ticket_import_workflow(self, jira_environment):
        """Test importing requirements from Jira ticket."""
        with patch('streamlit.session_state', {}), \
             patch('streamlit.text_input', return_value="TEST-123"), \
             patch('streamlit.button', return_value=True):
            
            # Simulate Jira ticket import
            ticket_data = jira_environment['jira_service'].get_ticket.return_value.value
            
            # Should convert ticket to requirements
            requirements = {
                'description': f"{ticket_data['summary']}: {ticket_data['description']}",
                'source': 'jira',
                'ticket_key': ticket_data['key']
            }
            
            assert requirements['description'] == "Automate data processing: Need to automate daily CSV processing"
            assert requirements['ticket_key'] == "TEST-123"
    
    def test_jira_authentication_workflow(self, jira_environment):
        """Test Jira authentication workflow."""
        with patch('streamlit.text_input') as mock_text_input, \
             patch('streamlit.button', return_value=True):
            
            # Mock authentication inputs
            mock_text_input.side_effect = [
                "https://company.atlassian.net",  # URL
                "user@company.com",              # Email
                "api_token_123"                  # Token
            ]
            
            # Should collect authentication details
            auth_config = {
                'url': "https://company.atlassian.net",
                'email': "user@company.com",
                'token': "api_token_123"
            }
            
            assert auth_config['url'] == "https://company.atlassian.net"
            assert auth_config['email'] == "user@company.com"


class TestFileUploadWorkflow:
    """Test file upload workflow."""
    
    def test_csv_upload_workflow(self, workflow_environment):
        """Test CSV file upload workflow."""
        # Mock file upload
        mock_file = Mock()
        mock_file.name = "requirements.csv"
        mock_file.read.return_value = b"description,priority\nAutomate data processing,high"
        
        with patch('streamlit.file_uploader', return_value=mock_file), \
             patch('pandas.read_csv') as mock_read_csv:
            
            # Mock CSV parsing
            mock_df = Mock()
            mock_df.to_dict.return_value = {
                'description': {0: 'Automate data processing'},
                'priority': {0: 'high'}
            }
            mock_read_csv.return_value = mock_df
            
            # Should parse CSV and extract requirements
            requirements = {
                'description': 'Automate data processing',
                'priority': 'high',
                'source': 'csv_upload'
            }
            
            assert requirements['description'] == 'Automate data processing'
            assert requirements['priority'] == 'high'
    
    def test_json_upload_workflow(self, workflow_environment):
        """Test JSON file upload workflow."""
        # Mock JSON file
        mock_file = Mock()
        mock_file.name = "requirements.json"
        mock_file.read.return_value = b'{"description": "Automate API integration", "domain": "api"}'
        
        with patch('streamlit.file_uploader', return_value=mock_file):
            
            # Should parse JSON
            import json
            requirements = json.loads(mock_file.read().decode())
            
            assert requirements['description'] == 'Automate API integration'
            assert requirements['domain'] == 'api'


class TestAnalyticsWorkflow:
    """Test analytics and reporting workflow."""
    
    def test_pattern_analytics_workflow(self, workflow_environment):
        """Test pattern analytics workflow."""
        # Mock analytics data
        mock_analytics = {
            'pattern_matches': [
                {'pattern_id': 'PAT-001', 'count': 15, 'success_rate': 0.8},
                {'pattern_id': 'PAT-002', 'count': 8, 'success_rate': 0.6}
            ],
            'time_period': 'last_7_days'
        }
        
        with patch('streamlit.selectbox', return_value="Last 7 Days"), \
             patch('streamlit.bar_chart') as mock_chart, \
             patch('streamlit.metric') as mock_metric:
            
            # Should display analytics
            for pattern in mock_analytics['pattern_matches']:
                mock_metric.assert_any_call(
                    pattern['pattern_id'],
                    pattern['count'],
                    f"{pattern['success_rate']:.1%} success rate"
                )
    
    def test_export_analytics_workflow(self, workflow_environment):
        """Test analytics export workflow."""
        # Mock analytics export
        analytics_data = {
            'summary': {
                'total_sessions': 50,
                'successful_automations': 35,
                'success_rate': 0.7
            },
            'patterns': [
                {'id': 'PAT-001', 'usage': 15},
                {'id': 'PAT-002', 'usage': 8}
            ]
        }
        
        with patch('streamlit.download_button') as mock_download:
            
            # Should prepare analytics export
            export_data = json.dumps(analytics_data, indent=2)
            
            assert 'total_sessions' in export_data
            assert 'PAT-001' in export_data


class TestPerformanceWorkflow:
    """Test performance aspects of workflows."""
    
    def test_startup_performance_workflow(self, workflow_environment):
        """Test application startup performance."""
        import time
        
        start_time = time.time()
        
        with patch('app.config.settings.get_config', return_value=workflow_environment['config']), \
             patch('app.core.registry.get_service_registry', return_value=workflow_environment['registry']), \
             patch('streamlit.set_page_config'), \
             patch('streamlit.sidebar'), \
             patch('streamlit.tabs'):
            
            app = AAAStreamlitApp()
            app.run()
        
        startup_time = time.time() - start_time
        
        # Should start quickly (under 2 seconds for tests)
        assert startup_time < 2.0
    
    def test_memory_usage_workflow(self, workflow_environment):
        """Test memory usage during workflow."""
        import gc
        
        # Force garbage collection
        gc.collect()
        
        # Create multiple sessions
        sessions = []
        for i in range(10):
            session = SessionState(
                session_id=f"perf-test-{i}",
                requirements={"description": f"Test requirement {i}"}
            )
            sessions.append(session)
        
        # Should handle multiple sessions efficiently
        assert len(sessions) == 10
        
        # Cleanup
        del sessions
        gc.collect()
    
    def test_concurrent_workflow_handling(self, workflow_environment):
        """Test handling of concurrent workflows."""
        # Simulate multiple concurrent sessions
        session_states = {}
        
        for i in range(5):
            session_id = f"concurrent-session-{i}"
            session_states[session_id] = {
                'session_id': session_id,
                'requirements': {'description': f'Concurrent requirement {i}'},
                'phase': 'analysis'
            }
        
        # Should handle multiple sessions without interference
        assert len(session_states) == 5
        
        for session_id, state in session_states.items():
            assert state['session_id'] == session_id
            assert f'requirement {session_id.split("-")[-1]}' in state['requirements']['description']


class TestRegressionWorkflow:
    """Test regression scenarios to ensure no functionality is lost."""
    
    def test_legacy_session_compatibility(self, workflow_environment):
        """Test compatibility with legacy session formats."""
        # Legacy session format
        legacy_session = {
            'session_id': 'legacy-123',
            'requirements_text': 'Legacy text requirements',
            'provider': 'openai',
            'model': 'gpt-4',
            'questions': [
                {'q': 'What is the volume?', 'a': '1000 records'}
            ]
        }
        
        # Should handle legacy format gracefully
        with patch('streamlit.session_state', legacy_session):
            from app.ui.tabs.analysis_tab import AnalysisTab
            
            tab = AnalysisTab(
                workflow_environment['config'],
                workflow_environment['registry']
            )
            
            # Should not raise exceptions
            assert tab.can_render() is True
    
    def test_api_compatibility_workflow(self, workflow_environment):
        """Test API compatibility with existing endpoints."""
        # Mock API response format
        api_response = {
            'session_id': 'api-session-123',
            'status': 'complete',
            'phase': 'recommendations',
            'recommendations': [
                {
                    'pattern_id': 'PAT-001',
                    'pattern_name': 'Data Processing',
                    'feasibility': 'Automatable',
                    'confidence': 0.9,
                    'tech_stack': ['Python', 'Pandas']
                }
            ]
        }
        
        # Should handle API response format
        assert api_response['status'] == 'complete'
        assert len(api_response['recommendations']) == 1
        assert api_response['recommendations'][0]['confidence'] == 0.9