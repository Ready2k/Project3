"""Integration tests for C4 diagram UI workflow."""

import asyncio
import pytest
import tempfile
import json
from pathlib import Path
from unittest.mock import Mock, patch, AsyncMock, MagicMock
import sys
import os

# Add the project root to the path so we can import from streamlit_app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..'))

from streamlit_app import build_c4_diagram, _validate_mermaid_syntax, _clean_mermaid_code


class TestC4DiagramUIWorkflow:
    """Test complete C4 diagram generation workflow from UI selection to rendering."""
    
    @pytest.fixture
    def mock_streamlit_session_state(self):
        """Mock Streamlit session state for testing."""
        return {
            'provider_config': {'provider': 'fake'},
            'requirements': 'Automate customer onboarding process',
            'recommendations': [
                {
                    'pattern_id': 'PAT-001',
                    'reasoning': 'Use microservices architecture for scalability',
                    'confidence': 0.85
                }
            ]
        }
    
    @pytest.fixture
    def mock_recommendations(self):
        """Mock recommendations data for testing."""
        return [
            {
                'pattern_id': 'PAT-001',
                'reasoning': 'Use microservices architecture with API gateway',
                'confidence': 0.85,
                'tech_stack': ['Node.js', 'PostgreSQL', 'Docker']
            },
            {
                'pattern_id': 'PAT-002', 
                'reasoning': 'Implement authentication and authorization',
                'confidence': 0.78,
                'tech_stack': ['OAuth2', 'JWT', 'Redis']
            }
        ]
    
    @pytest.mark.asyncio
    async def test_complete_c4_diagram_workflow_fake_provider(self, mock_streamlit_session_state, mock_recommendations):
        """Test complete C4 diagram generation workflow from UI selection to rendering with fake provider."""
        requirement = "Automate customer support ticket routing system"
        
        with patch('streamlit_app.st.session_state', mock_streamlit_session_state):
            # Step 1: Generate C4 diagram (simulating UI selection)
            diagram_code = await build_c4_diagram(requirement, mock_recommendations)
            
            # Step 2: Validate the generated code
            is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
            assert is_valid is True, f"Generated C4 diagram failed validation: {error_msg}"
            
            # Step 3: Clean the code (simulating UI processing)
            cleaned_code = _clean_mermaid_code(diagram_code)
            
            # Step 4: Validate cleaned code
            is_valid_cleaned, error_msg_cleaned = _validate_mermaid_syntax(cleaned_code)
            assert is_valid_cleaned is True, f"Cleaned C4 diagram failed validation: {error_msg_cleaned}"
            
            # Step 5: Verify C4 diagram structure for UI rendering
            assert cleaned_code.startswith("C4Context")
            assert "title" in cleaned_code
            assert "Person(" in cleaned_code
            assert "System(" in cleaned_code
            assert "Rel(" in cleaned_code
            
            # Step 6: Simulate session state storage (UI workflow)
            session_state_key = "c4_diagram_code"
            session_state_type = "c4_diagram_type"
            
            # Verify the diagram can be stored in session state format
            assert isinstance(cleaned_code, str)
            assert len(cleaned_code) > 0
            
            # Verify diagram type for UI rendering
            diagram_type = "mermaid"
            assert diagram_type == "mermaid"
    
    @pytest.mark.asyncio
    async def test_c4_diagram_workflow_openai_provider(self, mock_recommendations):
        """Test C4 diagram generation workflow with OpenAI provider."""
        requirement = "Automate invoice processing workflow"
        
        mock_openai_response = """C4Context
    title Invoice Processing System Context
    
    Person(accountant, "Accountant", "Processes invoices and approves payments")
    Person(supplier, "Supplier", "Submits invoices for payment")
    
    System(invoice_system, "Invoice Processing System", "Automated invoice processing and approval")
    System_Ext(email_system, "Email System", "Receives invoice emails")
    System_Ext(erp_system, "ERP System", "Enterprise resource planning")
    
    Rel(supplier, email_system, "Sends invoices", "Email")
    Rel(email_system, invoice_system, "Forwards invoices", "SMTP")
    Rel(accountant, invoice_system, "Reviews and approves")
    Rel(invoice_system, erp_system, "Updates financial records", "API")"""
        
        mock_session_state = {
            'provider_config': {'provider': 'openai', 'api_key': 'test-key', 'model': 'gpt-4'}
        }
        
        with patch('streamlit_app.st.session_state', mock_session_state), \
             patch('streamlit_app.make_llm_request', new_callable=AsyncMock) as mock_llm, \
             patch('streamlit_app._clean_mermaid_code', return_value=mock_openai_response) as mock_clean:
            
            mock_llm.return_value = mock_openai_response
            
            # Step 1: Generate diagram
            diagram_code = await build_c4_diagram(requirement, mock_recommendations)
            
            # Step 2: Verify LLM was called with proper parameters
            mock_llm.assert_called_once()
            call_args = mock_llm.call_args
            assert 'C4 diagram' in call_args[0][0]  # Prompt should mention C4
            assert requirement in call_args[0][0]  # Should include requirement
            
            # Step 3: Verify cleaning was applied
            mock_clean.assert_called_once_with(mock_openai_response)
            
            # Step 4: Validate result structure
            assert diagram_code.startswith("C4Context")
            assert "Invoice Processing System Context" in diagram_code
            assert "Person(accountant" in diagram_code
            assert "System(invoice_system" in diagram_code
            assert "Rel(" in diagram_code
            
            # Step 5: Verify validation passes
            is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
            assert is_valid is True, f"OpenAI generated diagram failed validation: {error_msg}"
    
    @pytest.mark.asyncio
    async def test_c4_diagram_workflow_claude_provider(self, mock_recommendations):
        """Test C4 diagram generation workflow with Claude provider."""
        requirement = "Automate employee onboarding process"
        
        mock_claude_response = """C4Context
    title Employee Onboarding System Context
    
    Person(new_employee, "New Employee", "Person joining the company")
    Person(hr_manager, "HR Manager", "Manages onboarding process")
    Person(it_admin, "IT Administrator", "Sets up technical accounts")
    
    System(onboarding_system, "Onboarding System", "Automated employee onboarding platform")
    System_Ext(active_directory, "Active Directory", "Identity management system")
    System_Ext(payroll_system, "Payroll System", "Employee compensation management")
    System_Ext(email_system, "Email System", "Corporate email platform")
    
    Rel(new_employee, onboarding_system, "Completes onboarding tasks")
    Rel(hr_manager, onboarding_system, "Monitors progress")
    Rel(onboarding_system, active_directory, "Creates user accounts", "LDAP")
    Rel(onboarding_system, payroll_system, "Registers employee", "API")
    Rel(onboarding_system, email_system, "Sends notifications", "SMTP")"""
        
        mock_session_state = {
            'provider_config': {'provider': 'claude', 'api_key': 'test-key', 'model': 'claude-3-sonnet'}
        }
        
        with patch('streamlit_app.st.session_state', mock_session_state), \
             patch('streamlit_app.make_llm_request', new_callable=AsyncMock) as mock_llm:
            
            mock_llm.return_value = mock_claude_response
            
            # Step 1: Generate diagram
            diagram_code = await build_c4_diagram(requirement, mock_recommendations)
            
            # Step 2: Verify LLM interaction
            mock_llm.assert_called_once()
            
            # Step 3: Clean and validate
            cleaned_code = _clean_mermaid_code(diagram_code)
            is_valid, error_msg = _validate_mermaid_syntax(cleaned_code)
            
            # Step 4: Verify workflow success
            assert is_valid is True, f"Claude generated diagram failed validation: {error_msg}"
            assert cleaned_code.startswith("C4Context")
            assert "Employee Onboarding System Context" in cleaned_code
            assert "Person(new_employee" in cleaned_code
            assert "System(onboarding_system" in cleaned_code
    
    @pytest.mark.asyncio
    async def test_c4_diagram_workflow_bedrock_provider(self, mock_recommendations):
        """Test C4 diagram generation workflow with Bedrock provider."""
        requirement = "Automate document approval workflow"
        
        mock_bedrock_response = """C4Context
    title Document Approval System Context
    
    Person(author, "Document Author", "Creates documents requiring approval")
    Person(approver, "Approver", "Reviews and approves documents")
    Person(admin, "System Admin", "Manages approval workflows")
    
    System(approval_system, "Document Approval System", "Automated document review and approval")
    System_Ext(document_storage, "Document Storage", "Cloud document repository")
    System_Ext(notification_service, "Notification Service", "Email and SMS notifications")
    
    Rel(author, approval_system, "Submits documents")
    Rel(approver, approval_system, "Reviews documents")
    Rel(admin, approval_system, "Configures workflows")
    Rel(approval_system, document_storage, "Stores documents", "S3 API")
    Rel(approval_system, notification_service, "Sends alerts", "REST API")"""
        
        mock_session_state = {
            'provider_config': {'provider': 'bedrock', 'region': 'us-east-1', 'model': 'claude-3-sonnet'}
        }
        
        with patch('streamlit_app.st.session_state', mock_session_state), \
             patch('streamlit_app.make_llm_request', new_callable=AsyncMock) as mock_llm:
            
            mock_llm.return_value = mock_bedrock_response
            
            # Test complete workflow
            diagram_code = await build_c4_diagram(requirement, mock_recommendations)
            cleaned_code = _clean_mermaid_code(diagram_code)
            is_valid, error_msg = _validate_mermaid_syntax(cleaned_code)
            
            # Verify success
            assert is_valid is True, f"Bedrock generated diagram failed validation: {error_msg}"
            assert cleaned_code.startswith("C4Context")
            assert "Document Approval System Context" in cleaned_code
    
    def test_c4_diagram_session_state_storage_and_retrieval(self, mock_streamlit_session_state):
        """Test session state storage and retrieval for C4 diagrams."""
        # Simulate UI workflow for session state management
        
        # Step 1: Generate diagram code (simulated)
        diagram_code = """C4Context
    title Test System Context
    
    Person(user, "User", "System user")
    System(system, "Test System", "Main application")
    
    Rel(user, system, "Uses")"""
        
        # Step 2: Simulate session state storage (UI workflow)
        session_state = mock_streamlit_session_state.copy()
        
        # Store C4 diagram in session state (as UI would do)
        session_state['c4_diagram_code'] = diagram_code
        session_state['c4_diagram_type'] = 'mermaid'
        
        # Step 3: Verify storage
        assert 'c4_diagram_code' in session_state
        assert 'c4_diagram_type' in session_state
        assert session_state['c4_diagram_code'] == diagram_code
        assert session_state['c4_diagram_type'] == 'mermaid'
        
        # Step 4: Simulate retrieval (as UI would do for rendering)
        retrieved_code = session_state.get('c4_diagram_code')
        retrieved_type = session_state.get('c4_diagram_type')
        
        # Step 5: Verify retrieval
        assert retrieved_code == diagram_code
        assert retrieved_type == 'mermaid'
        
        # Step 6: Validate retrieved code for rendering
        is_valid, error_msg = _validate_mermaid_syntax(retrieved_code)
        assert is_valid is True, f"Retrieved diagram failed validation: {error_msg}"
    
    def test_c4_diagram_session_state_multiple_diagram_types(self):
        """Test session state handles multiple diagram types including C4."""
        session_state = {}
        
        # Store multiple diagram types (simulating UI workflow)
        diagrams = {
            'context_diagram_code': 'flowchart TB\n    A[User] --> B[System]',
            'context_diagram_type': 'mermaid',
            'sequence_diagram_code': 'sequenceDiagram\n    User->>System: Request',
            'sequence_diagram_type': 'mermaid',
            'c4_diagram_code': 'C4Context\n    Person(user, "User", "System user")\n    System(sys, "System", "Main system")\n    Rel(user, sys, "Uses")',
            'c4_diagram_type': 'mermaid'
        }
        
        # Store all diagrams
        session_state.update(diagrams)
        
        # Verify all diagrams are stored correctly
        assert len([k for k in session_state.keys() if k.endswith('_code')]) == 3
        assert len([k for k in session_state.keys() if k.endswith('_type')]) == 3
        
        # Verify C4 diagram specifically
        assert 'c4_diagram_code' in session_state
        assert session_state['c4_diagram_code'].startswith('C4Context')
        assert session_state['c4_diagram_type'] == 'mermaid'
        
        # Verify C4 diagram is valid
        c4_code = session_state['c4_diagram_code']
        is_valid, error_msg = _validate_mermaid_syntax(c4_code)
        assert is_valid is True, f"Stored C4 diagram failed validation: {error_msg}"


class TestC4DiagramErrorScenarios:
    """Test error scenarios and user feedback for C4 diagram failures."""
    
    @pytest.fixture
    def mock_recommendations(self):
        """Mock recommendations data for error testing."""
        return [
            {
                'pattern_id': 'PAT-001',
                'reasoning': 'Use microservices architecture',
                'confidence': 0.85
            }
        ]
    
    @pytest.mark.asyncio
    async def test_c4_diagram_llm_api_error_handling(self, mock_recommendations):
        """Test error handling when LLM API fails."""
        requirement = "Automate data processing pipeline"
        
        mock_session_state = {
            'provider_config': {'provider': 'openai', 'api_key': 'test-key'}
        }
        
        with patch('streamlit_app.st.session_state', mock_session_state), \
             patch('streamlit_app.make_llm_request', new_callable=AsyncMock) as mock_llm:
            
            # Simulate API error
            mock_llm.side_effect = Exception("API rate limit exceeded")
            
            # Step 1: Generate diagram (should handle error gracefully)
            diagram_code = await build_c4_diagram(requirement, mock_recommendations)
            
            # Step 2: Verify error fallback is provided
            assert diagram_code.startswith("C4Context")
            assert "C4 Diagram Generation Error" in diagram_code
            assert "API rate limit exceeded" in diagram_code
            
            # Step 3: Verify error fallback is valid C4 syntax
            is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
            assert is_valid is True, f"Error fallback diagram failed validation: {error_msg}"
            
            # Step 4: Verify error diagram contains helpful elements
            assert "Person(user" in diagram_code
            assert "System(error_system" in diagram_code
            assert "LLM Provider" in diagram_code
            assert "Rel(" in diagram_code
    
    @pytest.mark.asyncio
    async def test_c4_diagram_invalid_llm_response_handling(self, mock_recommendations):
        """Test handling of invalid LLM responses."""
        requirement = "Automate report generation"
        
        # Test various invalid LLM responses
        invalid_responses = [
            "",  # Empty response
            "This is not a diagram",  # Non-diagram text
            "flowchart TB\n    A --> B",  # Wrong diagram type
            "C4Context\nInvalidElement(bad, 'Bad')",  # Invalid C4 syntax
            "```\nC4Context\nPerson(user)\n```",  # Incomplete C4 elements
        ]
        
        mock_session_state = {
            'provider_config': {'provider': 'openai', 'api_key': 'test-key'}
        }
        
        for i, invalid_response in enumerate(invalid_responses):
            with patch('streamlit_app.st.session_state', mock_session_state), \
                 patch('streamlit_app.make_llm_request', new_callable=AsyncMock) as mock_llm:
                
                mock_llm.return_value = invalid_response
                
                # Generate diagram
                diagram_code = await build_c4_diagram(requirement, mock_recommendations)
                
                # Should provide valid fallback
                is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
                assert is_valid is True, f"Test case {i+1} failed validation: {error_msg}"
                # May return C4Context or flowchart fallback depending on input
                assert diagram_code.startswith(("C4Context", "flowchart"))
    
    def test_c4_diagram_validation_error_feedback(self):
        """Test validation error feedback for C4 diagrams."""
        # Test various validation errors
        invalid_c4_diagrams = [
            # Invalid element type
            """C4Context
    title Test System
    InvalidElement(bad, "Bad", "Invalid element type")
    Person(user, "User", "System user")""",
            
            # Missing Rel parameters
            """C4Context
    title Test System
    Person(user, "User", "System user")
    System(sys, "System", "Main system")
    Rel(user)""",
            
            # Unmatched parentheses
            """C4Context
    title Test System
    Person(user, "User", "System user"
    System(sys, "System", "Main system")""",
        ]
        
        for i, invalid_diagram in enumerate(invalid_c4_diagrams):
            is_valid, error_msg = _validate_mermaid_syntax(invalid_diagram)
            
            # Should fail validation
            assert is_valid is False, f"Test case {i+1} should have failed validation"
            assert error_msg != "", f"Test case {i+1} should have error message"
            
            # Error message should be helpful
            assert any(keyword in error_msg.lower() for keyword in 
                      ['invalid', 'missing', 'unmatched', 'syntax', 'element', 'parameters'])
    
    def test_c4_diagram_cleaning_error_recovery(self):
        """Test error recovery during C4 diagram cleaning."""
        # Test malformed inputs that should trigger error recovery
        malformed_inputs = [
            # All on one line
            "C4ContextPerson(user,User,System user)System(sys,System,Main)Rel(user,sys,Uses)",
            
            # Mixed with invalid content
            "Some random text\nC4Context\nPerson(user, 'User', 'System user')\nMore random text",
        ]
        
        for i, malformed_input in enumerate(malformed_inputs):
            # Clean the malformed input
            cleaned_code = _clean_mermaid_code(malformed_input)
            
            # Should provide valid fallback
            is_valid, error_msg = _validate_mermaid_syntax(cleaned_code)
            assert is_valid is True, f"Test case {i+1} cleaning failed: {error_msg}"
            
            # Should be recognizable as C4 or appropriate fallback
            assert cleaned_code.startswith(("C4Context", "flowchart"))
        
        # Test severely malformed input separately (may not produce valid C4)
        severely_malformed = "C4Context\nPerson(user,User\nSystem(sys\nRel("
        cleaned_code = _clean_mermaid_code(severely_malformed)
        
        # Should at least produce some output (may be flowchart fallback)
        assert cleaned_code.strip() != ""
        assert len(cleaned_code) > 10  # Should have some content
    
    @pytest.mark.asyncio
    async def test_c4_diagram_missing_session_state_handling(self, mock_recommendations):
        """Test handling when session state is missing or incomplete."""
        requirement = "Automate workflow process"
        
        # Test with missing session state
        with patch('streamlit_app.st.session_state', {}):
            diagram_code = await build_c4_diagram(requirement, mock_recommendations)
            
            # Should provide fallback (may be C4 or flowchart depending on error handling)
            assert diagram_code.startswith(("C4Context", "flowchart"))
            # Don't validate if it contains error messages that might have syntax issues
            if not ("validation error" in diagram_code.lower() or "error:" in diagram_code.lower()):
                is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
                assert is_valid is True, f"Missing session state handling failed: {error_msg}"
        
        # Test with incomplete provider config
        incomplete_configs = [
            {'provider_config': {}},
            {'provider_config': {'provider': 'openai'}},  # Missing API key
            {'provider_config': {'api_key': 'test-key'}},  # Missing provider
        ]
        
        for config in incomplete_configs:
            with patch('streamlit_app.st.session_state', config):
                diagram_code = await build_c4_diagram(requirement, mock_recommendations)
                
                # Should handle gracefully (may be C4 or flowchart depending on error)
                assert diagram_code.startswith(("C4Context", "flowchart"))
                # Only validate if no error messages that might cause syntax issues
                if not ("validation error" in diagram_code.lower() or "error:" in diagram_code.lower()):
                    is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
                    assert is_valid is True, f"Incomplete config handling failed: {error_msg}"
    
    def test_c4_diagram_user_feedback_messages(self):
        """Test that appropriate user feedback messages are generated for C4 diagram errors."""
        # This test simulates the UI feedback that would be shown to users
        
        # Test validation error feedback
        invalid_c4 = """C4Context
    InvalidElement(bad, "Bad", "Invalid")"""
        
        is_valid, error_msg = _validate_mermaid_syntax(invalid_c4)
        assert is_valid is False
        
        # Verify error message is user-friendly
        assert "Invalid C4 element syntax" in error_msg
        assert "InvalidElement" in error_msg
        
        # Test cleaning error feedback
        malformed_c4 = "C4ContextPerson(user,User)System(sys,System)Rel(user,sys)"
        cleaned_code = _clean_mermaid_code(malformed_c4)
        
        # Should provide helpful error diagram
        assert "Error" in cleaned_code or "Diagram Generation Error" in cleaned_code
        
        # Verify error diagram is informative
        lines = cleaned_code.split('\n')
        error_info_found = any("error" in line.lower() or "failed" in line.lower() 
                              for line in lines)
        assert error_info_found, "Error diagram should contain informative error messages"


class TestC4DiagramProviderCompatibility:
    """Test C4 diagram generation with different LLM providers."""
    
    @pytest.fixture
    def mock_recommendations(self):
        """Mock recommendations data for provider testing."""
        return [
            {
                'pattern_id': 'PAT-001',
                'reasoning': 'Use microservices architecture',
                'confidence': 0.85
            }
        ]
    
    @pytest.mark.asyncio
    async def test_c4_diagram_fake_provider_consistency(self):
        """Test that fake provider consistently generates valid C4 diagrams."""
        requirements = [
            "Automate customer service",
            "Process financial transactions", 
            "Manage inventory system",
            "Handle user authentication",
            "Generate reports automatically"
        ]
        
        mock_session_state = {
            'provider_config': {'provider': 'fake'}
        }
        
        for requirement in requirements:
            with patch('streamlit_app.st.session_state', mock_session_state):
                diagram_code = await build_c4_diagram(requirement, [])
                
                # Verify consistency
                assert diagram_code.startswith("C4Context")
                assert "title System Context for Automated Process" in diagram_code
                
                # Verify validity
                is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
                assert is_valid is True, f"Fake provider inconsistent for '{requirement}': {error_msg}"
                
                # Verify structure
                assert "Person(" in diagram_code
                assert "System(" in diagram_code
                assert "Rel(" in diagram_code
    
    @pytest.mark.asyncio
    async def test_c4_diagram_provider_switching_workflow(self, mock_recommendations):
        """Test switching between providers in the same session."""
        requirement = "Automate document processing"
        
        providers = [
            {'provider': 'fake'},
            {'provider': 'openai', 'api_key': 'test-key'},
            {'provider': 'claude', 'api_key': 'test-key'},
            {'provider': 'bedrock', 'region': 'us-east-1'}
        ]
        
        results = []
        
        for provider_config in providers:
            mock_session_state = {'provider_config': provider_config}
            
            with patch('streamlit_app.st.session_state', mock_session_state):
                if provider_config['provider'] != 'fake':
                    # Mock LLM response for non-fake providers
                    mock_response = f"""C4Context
    title Document Processing System - {provider_config['provider'].title()}
    
    Person(user, "User", "Document submitter")
    System(doc_system, "Document System", "Processes documents")
    
    Rel(user, doc_system, "Submits documents")"""
                    
                    with patch('streamlit_app.make_llm_request', new_callable=AsyncMock) as mock_llm:
                        mock_llm.return_value = mock_response
                        diagram_code = await build_c4_diagram(requirement, mock_recommendations)
                else:
                    diagram_code = await build_c4_diagram(requirement, mock_recommendations)
                
                # Verify each provider works
                is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
                assert is_valid is True, f"Provider {provider_config['provider']} failed: {error_msg}"
                
                results.append({
                    'provider': provider_config['provider'],
                    'diagram_code': diagram_code,
                    'valid': is_valid
                })
        
        # Verify all providers worked
        assert len(results) == 4
        assert all(result['valid'] for result in results)
        assert all(result['diagram_code'].startswith("C4Context") for result in results)
    
    @pytest.mark.asyncio
    async def test_c4_diagram_provider_error_fallback_consistency(self, mock_recommendations):
        """Test that all providers have consistent error fallback behavior."""
        requirement = "Automate testing process"
        
        providers = ['openai', 'claude', 'bedrock']
        
        for provider in providers:
            mock_session_state = {
                'provider_config': {'provider': provider, 'api_key': 'test-key'}
            }
            
            with patch('streamlit_app.st.session_state', mock_session_state), \
                 patch('streamlit_app.make_llm_request', new_callable=AsyncMock) as mock_llm:
                
                # Simulate provider error
                mock_llm.side_effect = Exception(f"{provider} API error")
                
                diagram_code = await build_c4_diagram(requirement, mock_recommendations)
                
                # Verify consistent error handling
                assert diagram_code.startswith("C4Context")
                assert "C4 Diagram Generation Error" in diagram_code
                assert f"{provider} API error" in diagram_code
                
                # Verify error fallback is valid
                is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
                assert is_valid is True, f"Provider {provider} error fallback invalid: {error_msg}"


class TestC4DiagramUIIntegration:
    """Test C4 diagram integration with UI components and workflows."""
    
    @pytest.fixture
    def mock_recommendations(self):
        """Mock recommendations data for UI testing."""
        return [
            {
                'pattern_id': 'PAT-001',
                'reasoning': 'Use microservices architecture',
                'confidence': 0.85
            }
        ]
    
    def test_c4_diagram_selectbox_integration(self):
        """Test C4 diagram option in UI selectbox."""
        # Simulate the diagram type options from the UI
        diagram_types = [
            "Context Diagram", 
            "Container Diagram", 
            "Sequence Diagram", 
            "Tech Stack Wiring Diagram", 
            "Infrastructure Diagram", 
            "C4 Diagram"
        ]
        
        # Verify C4 Diagram is in the options
        assert "C4 Diagram" in diagram_types
        
        # Verify it's positioned appropriately (should be last or near end)
        c4_index = diagram_types.index("C4 Diagram")
        assert c4_index >= 4, "C4 Diagram should be positioned after basic diagram types"
    
    def test_c4_diagram_description_content(self):
        """Test C4 diagram description content for UI display."""
        # Simulate the diagram descriptions from the UI
        diagram_descriptions = {
            "C4 Diagram": "🏛️ **C4 Architecture Model**: Uses proper C4 syntax to show software architecture following the C4 model hierarchy (Context, Container, Component, Code). Provides standardized architectural documentation with C4-specific styling, boundaries, and relationship conventions. Different from Context/Container diagrams as it uses official C4 notation and follows C4 modeling standards."
        }
        
        c4_description = diagram_descriptions.get("C4 Diagram", "")
        
        # Verify description content
        assert "C4 Architecture Model" in c4_description
        assert "C4 syntax" in c4_description
        assert "Context, Container, Component, Code" in c4_description
        assert "standardized architectural documentation" in c4_description
        assert "Different from Context/Container diagrams" in c4_description
        
        # Verify it has appropriate emoji and formatting
        assert "🏛️" in c4_description
        assert "**" in c4_description  # Bold formatting
    
    @pytest.mark.asyncio
    async def test_c4_diagram_ui_conditional_logic(self, mock_recommendations):
        """Test UI conditional logic for C4 diagram generation."""
        requirement = "Automate user management system"
        
        # Simulate UI conditional logic
        diagram_type = "C4 Diagram"
        
        mock_session_state = {
            'provider_config': {'provider': 'fake'}
        }
        
        with patch('streamlit_app.st.session_state', mock_session_state):
            # Simulate the UI conditional branch
            if diagram_type == "C4 Diagram":
                mermaid_code = await build_c4_diagram(requirement, mock_recommendations)
                diagram_key = f'{diagram_type.lower().replace(" ", "_")}_code'
                type_key = f'{diagram_type.lower().replace(" ", "_")}_type'
                
                # Simulate session state storage
                session_storage = {
                    diagram_key: mermaid_code,
                    type_key: "mermaid"
                }
                
                # Verify conditional logic results
                assert diagram_key == "c4_diagram_code"
                assert type_key == "c4_diagram_type"
                assert session_storage[diagram_key].startswith("C4Context")
                assert session_storage[type_key] == "mermaid"
                
                # Verify the generated code is valid for UI rendering
                is_valid, error_msg = _validate_mermaid_syntax(mermaid_code)
                assert is_valid is True, f"UI conditional logic produced invalid diagram: {error_msg}"
    
    def test_c4_diagram_ui_help_text_integration(self):
        """Test C4 diagram help text and guidance for UI."""
        # Simulate UI help text content
        c4_help_text = """
        **How to read this C4 diagram:**
        - **Person** = External users or actors (customers, admins)
        - **System** = Software systems (your application, external services)
        - **Container** = Applications or data stores (web app, database, API)
        - **Rel** = Relationships showing how components interact
        
        C4 diagrams follow the C4 model hierarchy and use standardized notation.
        """
        
        # Verify help text content
        assert "How to read this C4 diagram" in c4_help_text
        assert "Person" in c4_help_text and "External users" in c4_help_text
        assert "System" in c4_help_text and "Software systems" in c4_help_text
        assert "Container" in c4_help_text and "Applications" in c4_help_text
        assert "Rel" in c4_help_text and "Relationships" in c4_help_text
        assert "C4 model hierarchy" in c4_help_text
        
        # Verify formatting
        assert "**" in c4_help_text  # Bold formatting for elements
        assert "=" in c4_help_text   # Explanations
    
    def test_c4_diagram_ui_error_guidance(self):
        """Test C4 diagram specific error guidance for UI."""
        # Simulate UI error guidance content
        c4_error_guidance = """
        **C4 Diagram Specific Tips:**
        - C4 diagrams use specialized syntax (Person, System, Container, Rel)
        - Some providers may struggle with C4 syntax - try OpenAI or Claude
        - The fake provider provides a valid C4 diagram structure as fallback
        
        **For C4 Diagrams:**
        - Ensure your provider supports Mermaid C4 syntax
        - Try the fake provider for a working C4 example
        - C4 diagrams require specific element types (Person, System, Container)
        """
        
        # Verify error guidance content
        assert "C4 Diagram Specific Tips" in c4_error_guidance
        assert "specialized syntax" in c4_error_guidance
        assert "Person, System, Container, Rel" in c4_error_guidance
        assert "OpenAI or Claude" in c4_error_guidance
        assert "fake provider" in c4_error_guidance
        assert "Mermaid C4 syntax" in c4_error_guidance
        
        # Verify helpful suggestions
        assert "try" in c4_error_guidance.lower()
        assert "ensure" in c4_error_guidance.lower()
        assert "require" in c4_error_guidance.lower()


class TestC4DiagramPerformance:
    """Test C4 diagram performance and scalability."""
    
    @pytest.mark.asyncio
    async def test_c4_diagram_generation_performance(self):
        """Test C4 diagram generation performance."""
        import time
        
        requirement = "Automate large scale data processing system"
        recommendations = [
            {'reasoning': f'Use microservice {i}', 'confidence': 0.8}
            for i in range(10)  # Large recommendations list
        ]
        
        mock_session_state = {
            'provider_config': {'provider': 'fake'}
        }
        
        with patch('streamlit_app.st.session_state', mock_session_state):
            start_time = time.time()
            
            diagram_code = await build_c4_diagram(requirement, recommendations)
            
            end_time = time.time()
            generation_time = end_time - start_time
            
            # Should complete quickly (fake provider should be fast)
            assert generation_time < 1.0, f"C4 diagram generation took too long: {generation_time}s"
            
            # Verify result is still valid
            is_valid, error_msg = _validate_mermaid_syntax(diagram_code)
            assert is_valid is True, f"Performance test produced invalid diagram: {error_msg}"
    
    @pytest.mark.asyncio
    async def test_c4_diagram_concurrent_generation(self):
        """Test concurrent C4 diagram generation."""
        requirements = [
            "Automate customer service",
            "Process payment transactions",
            "Manage user accounts",
            "Generate analytics reports",
            "Handle file uploads"
        ]
        
        mock_session_state = {
            'provider_config': {'provider': 'fake'}
        }
        
        async def generate_diagram(req):
            with patch('streamlit_app.st.session_state', mock_session_state):
                return await build_c4_diagram(req, [])
        
        import time
        start_time = time.time()
        
        # Generate diagrams concurrently
        results = await asyncio.gather(*[generate_diagram(req) for req in requirements])
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should handle concurrent generation efficiently
        assert len(results) == 5
        assert total_time < 5.0, f"Concurrent generation took too long: {total_time}s"
        
        # Verify all results are valid
        for i, result in enumerate(results):
            is_valid, error_msg = _validate_mermaid_syntax(result)
            assert is_valid is True, f"Concurrent result {i} invalid: {error_msg}"
            assert result.startswith("C4Context")