"""Unit tests for diagram analysis integration functionality."""

import pytest
from unittest.mock import Mock, patch, AsyncMock
from typing import Dict, List, Any, Optional

# Import the functions we're testing
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from streamlit_app import (
    build_tech_stack_wiring_diagram,
    build_context_diagram,
    build_container_diagram,
    build_sequence_diagram,
    build_c4_diagram,
    build_infrastructure_diagram
)


class TestEnhancedDataRetrieval:
    """Test enhanced data retrieval from session state."""
    
    def test_get_enhanced_analysis_data_with_full_data(self):
        """Test retrieving enhanced data when both tech stack and explanation are available."""
        # Mock streamlit session state
        with patch('streamlit_app.st') as mock_st:
            mock_st.session_state.get.return_value = {
                'enhanced_tech_stack': ['Python', 'FastAPI', 'PostgreSQL', 'OAuth2'],
                'architecture_explanation': 'This system uses Python and FastAPI for the backend...'
            }
            
            # Import and create instance to test
            from streamlit_app import AAA_UI
            ui = AAA_UI()
            
            result = ui.get_enhanced_analysis_data()
            
            assert result['enhanced_tech_stack'] == ['Python', 'FastAPI', 'PostgreSQL', 'OAuth2']
            assert 'This system uses Python and FastAPI' in result['architecture_explanation']
            assert result['has_enhanced_data'] is True
    
    def test_get_enhanced_analysis_data_with_partial_data(self):
        """Test retrieving enhanced data when only tech stack is available."""
        with patch('streamlit_app.st') as mock_st:
            mock_st.session_state.get.return_value = {
                'enhanced_tech_stack': ['Python', 'FastAPI', 'PostgreSQL'],
                'architecture_explanation': None
            }
            
            from streamlit_app import AAA_UI
            ui = AAA_UI()
            
            result = ui.get_enhanced_analysis_data()
            
            assert result['enhanced_tech_stack'] == ['Python', 'FastAPI', 'PostgreSQL']
            assert result['architecture_explanation'] is None
            assert result['has_enhanced_data'] is True
    
    def test_get_enhanced_analysis_data_with_no_data(self):
        """Test retrieving enhanced data when no enhanced data is available."""
        with patch('streamlit_app.st') as mock_st:
            mock_st.session_state.get.return_value = {}
            
            from streamlit_app import AAA_UI
            ui = AAA_UI()
            
            result = ui.get_enhanced_analysis_data()
            
            assert result['enhanced_tech_stack'] is None
            assert result['architecture_explanation'] is None
            assert result['has_enhanced_data'] is False
    
    def test_get_enhanced_analysis_data_error_handling(self):
        """Test error handling when session state access fails."""
        with patch('streamlit_app.st') as mock_st:
            mock_st.session_state.get.side_effect = Exception("Session state error")
            
            from streamlit_app import AAA_UI
            ui = AAA_UI()
            
            result = ui.get_enhanced_analysis_data()
            
            assert result['enhanced_tech_stack'] is None
            assert result['architecture_explanation'] is None
            assert result['has_enhanced_data'] is False


class TestTechStackPriorityLogic:
    """Test tech stack priority logic in diagram functions."""
    
    @pytest.mark.asyncio
    async def test_tech_stack_wiring_diagram_uses_enhanced_tech_stack(self):
        """Test that tech stack wiring diagram prioritizes enhanced tech stack."""
        requirement = "Automate user authentication"
        recommendations = [{'tech_stack': ['Python', 'Flask'], 'reasoning': 'Basic stack'}]
        enhanced_tech_stack = ['Python', 'FastAPI', 'PostgreSQL', 'OAuth2']
        architecture_explanation = "This system uses OAuth2 for authentication..."
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = """flowchart TB
    user[User Interface]
    api[FastAPI Server]
    db[(PostgreSQL)]
    oauth[OAuth2 Service]
    
    user -->|HTTP Request| api
    api -->|Auth Check| oauth
    api -->|SQL Query| db"""
            
            result = await build_tech_stack_wiring_diagram(
                requirement, recommendations, enhanced_tech_stack, architecture_explanation
            )
            
            # Verify the LLM was called with enhanced tech stack
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]  # First argument (prompt)
            assert 'Python, FastAPI, PostgreSQL, OAuth2' in call_args
            assert 'This system uses OAuth2 for authentication' in call_args
            assert 'flowchart TB' in result
    
    @pytest.mark.asyncio
    async def test_tech_stack_wiring_diagram_fallback_to_recommendations(self):
        """Test that tech stack wiring diagram falls back to recommendations when no enhanced data."""
        requirement = "Automate user authentication"
        recommendations = [{'tech_stack': ['Python', 'Flask'], 'reasoning': 'Basic stack'}]
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = """flowchart TB
    user[User Interface]
    api[Flask Server]
    
    user -->|HTTP Request| api"""
            
            result = await build_tech_stack_wiring_diagram(requirement, recommendations)
            
            # Verify the LLM was called with recommendation tech stack
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]  # First argument (prompt)
            assert 'Python, Flask' in call_args
            assert 'flowchart TB' in result
    
    @pytest.mark.asyncio
    async def test_context_diagram_includes_tech_stack_context(self):
        """Test that context diagram includes tech stack context."""
        requirement = "Automate inventory management"
        recommendations = [{'tech_stack': ['Python', 'Django'], 'reasoning': 'Web framework'}]
        enhanced_tech_stack = ['Python', 'FastAPI', 'PostgreSQL', 'Redis']
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = """flowchart LR
    user([Warehouse Manager])
    system[Inventory System]
    db[(Database)]
    
    user --> system
    system --> db"""
            
            result = await build_context_diagram(
                requirement, recommendations, enhanced_tech_stack
            )
            
            # Verify the LLM was called with tech stack context
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]  # First argument (prompt)
            assert 'TECHNOLOGY CONTEXT: Python, FastAPI, PostgreSQL, Redis' in call_args
            assert 'flowchart LR' in result


class TestArchitectureExplanationIntegration:
    """Test architecture explanation integration in diagram prompts."""
    
    @pytest.mark.asyncio
    async def test_container_diagram_includes_architecture_explanation(self):
        """Test that container diagram includes architecture explanation in prompt."""
        requirement = "Build API gateway"
        recommendations = [{'reasoning': 'API gateway needed'}]
        enhanced_tech_stack = ['Python', 'FastAPI', 'Redis']
        architecture_explanation = "The FastAPI server handles routing and Redis provides caching for improved performance."
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = """flowchart TB
    subgraph "API Gateway"
        api[FastAPI Server]
        cache[Redis Cache]
    end
    
    api --> cache"""
            
            result = await build_container_diagram(
                requirement, recommendations, enhanced_tech_stack, architecture_explanation
            )
            
            # Verify the LLM was called with architecture explanation
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]  # First argument (prompt)
            assert 'ARCHITECTURE EXPLANATION: The FastAPI server handles routing' in call_args
            assert 'Use the architecture explanation above to understand component relationships' in call_args
            assert 'flowchart TB' in result
    
    @pytest.mark.asyncio
    async def test_sequence_diagram_without_architecture_explanation(self):
        """Test that sequence diagram works without architecture explanation."""
        requirement = "User login flow"
        recommendations = [{'reasoning': 'Authentication flow'}]
        enhanced_tech_stack = ['Python', 'FastAPI']
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = """sequenceDiagram
    participant U as User
    participant A as API
    
    U->>A: Login Request
    A->>U: Success Response"""
            
            result = await build_sequence_diagram(
                requirement, recommendations, enhanced_tech_stack, None
            )
            
            # Verify the LLM was called without architecture explanation
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]  # First argument (prompt)
            assert 'ARCHITECTURE EXPLANATION:' not in call_args
            assert 'TECHNOLOGY CONTEXT: Python, FastAPI' in call_args
            assert 'sequenceDiagram' in result


class TestFallbackBehavior:
    """Test fallback behavior when enhanced data is unavailable or invalid."""
    
    @pytest.mark.asyncio
    async def test_c4_diagram_with_invalid_enhanced_tech_stack(self):
        """Test C4 diagram handles invalid enhanced tech stack gracefully."""
        requirement = "System architecture"
        recommendations = [{'tech_stack': ['Python', 'Django'], 'reasoning': 'Web app'}]
        enhanced_tech_stack = "invalid_not_a_list"  # Invalid type
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = """C4Context
    title System Context
    
    Person(user, "User", "System user")
    System(app, "Application", "Main system")
    
    Rel(user, app, "Uses")"""
            
            # The function should handle invalid enhanced_tech_stack gracefully
            result = await build_c4_diagram(
                requirement, recommendations, enhanced_tech_stack
            )
            
            # Should still work and use recommendations
            mock_llm.assert_called_once()
            assert 'C4Context' in result
    
    @pytest.mark.asyncio
    async def test_infrastructure_diagram_with_empty_recommendations(self):
        """Test infrastructure diagram handles empty recommendations."""
        requirement = "Cloud infrastructure"
        recommendations = []
        enhanced_tech_stack = ['AWS', 'Lambda', 'DynamoDB']
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = '{"title": "Cloud Infrastructure", "clusters": []}'
            
            result = await build_infrastructure_diagram(
                requirement, recommendations, enhanced_tech_stack
            )
            
            # Should work with enhanced tech stack even with empty recommendations
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args[0][0]  # First argument (prompt)
            assert 'TECHNOLOGY CONTEXT: AWS, Lambda, DynamoDB' in call_args
            assert isinstance(result, dict)


class TestErrorHandling:
    """Test error handling in diagram generation with enhanced data."""
    
    @pytest.mark.asyncio
    async def test_diagram_generation_error_handling(self):
        """Test that diagram generation handles LLM errors gracefully."""
        requirement = "Test system"
        recommendations = [{'tech_stack': ['Python'], 'reasoning': 'Simple'}]
        enhanced_tech_stack = ['Python', 'FastAPI']
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.side_effect = Exception("LLM API error")
            
            # Should return error fallback diagram
            result = await build_tech_stack_wiring_diagram(
                requirement, recommendations, enhanced_tech_stack
            )
            
            assert 'flowchart TB' in result
            assert 'error' in result.lower() or 'failed' in result.lower()
    
    @pytest.mark.asyncio
    async def test_diagram_generation_with_malformed_enhanced_data(self):
        """Test diagram generation with malformed enhanced data."""
        requirement = "Test system"
        recommendations = [{'tech_stack': ['Python'], 'reasoning': 'Simple'}]
        enhanced_tech_stack = [None, '', 123, {'invalid': 'data'}]  # Mixed invalid data
        
        with patch('streamlit_app.make_llm_request') as mock_llm:
            mock_llm.return_value = """flowchart TB
    system[System]
    error[Handled malformed data]
    
    system --> error"""
            
            # Should handle malformed data gracefully
            result = await build_context_diagram(
                requirement, recommendations, enhanced_tech_stack
            )
            
            mock_llm.assert_called_once()
            assert 'flowchart' in result


if __name__ == "__main__":
    pytest.main([__file__])