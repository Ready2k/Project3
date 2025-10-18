"""Integration tests for diagram analysis consistency."""

import pytest
from unittest.mock import patch

# Import test utilities
from app.tests.fixtures.test_data import create_test_session


class TestAnalysisDiagramConsistency:
    """Test consistency between analysis results and diagram generation."""

    @pytest.mark.asyncio
    async def test_end_to_end_tech_stack_consistency(self):
        """Test that tech stack is consistent from analysis through diagram generation."""
        # Setup test data
        session = create_test_session()
        session.requirements = {
            "description": "Automate user authentication with OAuth2",
            "domain": "Security",
            "volume": {"users": 1000},
        }

        # Mock the architecture explainer to return enhanced tech stack
        enhanced_tech_stack = ["Python", "FastAPI", "PostgreSQL", "OAuth2", "Redis"]
        architecture_explanation = """This authentication system leverages Python and FastAPI for the backend API, 
        PostgreSQL for user data storage, OAuth2 for secure authentication flows, and Redis for session caching. 
        The FastAPI framework provides async capabilities for handling concurrent authentication requests efficiently."""

        with patch(
            "app.services.architecture_explainer.ArchitectureExplainer"
        ) as mock_explainer:
            mock_explainer.return_value.explain_architecture.return_value = (
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Mock LLM request for diagram generation
            with patch("streamlit_app.make_llm_request") as mock_llm:
                mock_llm.return_value = """flowchart TB
    user[User Interface]
    api[FastAPI Server]
    db[(PostgreSQL)]
    oauth[OAuth2 Service]
    cache[(Redis Cache)]
    
    user -->|HTTP Request| api
    api -->|Auth Check| oauth
    api -->|SQL Query| db
    api -->|Cache Check| cache"""

                # Import diagram functions
                from streamlit_app import build_tech_stack_wiring_diagram

                # Generate diagram with enhanced data
                recommendations = [
                    {
                        "tech_stack": ["Python", "Flask"],
                        "reasoning": "Basic web framework",
                    }
                ]

                diagram_result = await build_tech_stack_wiring_diagram(
                    session.requirements["description"],
                    recommendations,
                    enhanced_tech_stack,
                    architecture_explanation,
                )

                # Verify consistency
                mock_llm.assert_called_once()
                call_args = mock_llm.call_args[0][0]  # First argument (prompt)

                # Check that enhanced tech stack is used in diagram
                assert "Python, FastAPI, PostgreSQL, OAuth2, Redis" in call_args

                # Check that architecture explanation is included
                assert "ARCHITECTURE EXPLANATION:" in call_args
                assert "FastAPI framework provides async capabilities" in call_args

                # Verify diagram contains expected technologies
                assert "FastAPI" in diagram_result
                assert "PostgreSQL" in diagram_result
                assert "OAuth2" in diagram_result
                assert "Redis" in diagram_result

    @pytest.mark.asyncio
    async def test_multiple_diagram_types_use_same_enhanced_data(self):
        """Test that all diagram types use the same enhanced tech stack and explanation."""
        # Setup enhanced data
        enhanced_tech_stack = ["Python", "Django", "PostgreSQL", "Celery", "Redis"]
        architecture_explanation = """This system uses Django for web framework, PostgreSQL for data persistence, 
        Celery for background task processing, and Redis for both caching and message brokering."""

        requirement = "Build inventory management system"
        recommendations = [
            {"tech_stack": ["Python", "Flask"], "reasoning": "Simple web app"}
        ]

        # Mock LLM responses for different diagram types
        diagram_responses = {
            "context": """flowchart LR
    user([Manager])
    system[Inventory System]
    db[(Database)]
    
    user --> system
    system --> db""",
            "container": """flowchart TB
    subgraph "Inventory System"
        web[Django Web App]
        worker[Celery Worker]
        cache[Redis Cache]
    end
    
    db[(PostgreSQL)]
    
    web --> db
    worker --> db
    web --> cache""",
            "sequence": """sequenceDiagram
    participant U as User
    participant D as Django
    participant C as Celery
    participant P as PostgreSQL
    
    U->>D: Create Order
    D->>P: Save Order
    D->>C: Process Async
    C->>P: Update Status""",
        }

        with patch("streamlit_app.make_llm_request") as mock_llm:
            # Import diagram functions
            from streamlit_app import (
                build_context_diagram,
                build_container_diagram,
                build_sequence_diagram,
            )

            # Test context diagram
            mock_llm.return_value = diagram_responses["context"]
            context_result = await build_context_diagram(
                requirement,
                recommendations,
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Verify enhanced data was used
            context_call_args = mock_llm.call_args[0][0]
            assert (
                "TECHNOLOGY CONTEXT: Python, Django, PostgreSQL, Celery, Redis"
                in context_call_args
            )
            assert "Django for web framework" in context_call_args

            # Test container diagram
            mock_llm.return_value = diagram_responses["container"]
            container_result = await build_container_diagram(
                requirement,
                recommendations,
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Verify enhanced data was used
            container_call_args = mock_llm.call_args[0][0]
            assert (
                "TECHNOLOGY CONTEXT: Python, Django, PostgreSQL, Celery, Redis"
                in container_call_args
            )
            assert "Celery for background task processing" in container_call_args

            # Test sequence diagram
            mock_llm.return_value = diagram_responses["sequence"]
            sequence_result = await build_sequence_diagram(
                requirement,
                recommendations,
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Verify enhanced data was used
            sequence_call_args = mock_llm.call_args[0][0]
            assert (
                "TECHNOLOGY CONTEXT: Python, Django, PostgreSQL, Celery, Redis"
                in sequence_call_args
            )
            assert "Redis for both caching and message brokering" in sequence_call_args

            # Verify all diagrams were generated successfully
            assert "flowchart LR" in context_result
            assert "Django Web App" in container_result
            assert "sequenceDiagram" in sequence_result

    @pytest.mark.asyncio
    async def test_fallback_consistency_when_enhanced_data_unavailable(self):
        """Test that diagrams consistently fall back to recommendation data when enhanced data unavailable."""
        requirement = "Simple web application"
        recommendations = [
            {
                "tech_stack": ["Python", "Flask", "SQLite"],
                "reasoning": "Lightweight web application stack",
            }
        ]

        with patch("streamlit_app.make_llm_request") as mock_llm:
            mock_llm.return_value = """flowchart TB
    user[User]
    flask[Flask App]
    db[(SQLite)]
    
    user --> flask
    flask --> db"""

            # Import diagram functions
            from streamlit_app import (
                build_tech_stack_wiring_diagram,
                build_context_diagram,
            )

            # Test wiring diagram without enhanced data
            wiring_result = await build_tech_stack_wiring_diagram(
                requirement, recommendations
            )

            # Verify recommendation tech stack was used
            wiring_call_args = mock_llm.call_args[0][0]
            assert "Python, Flask, SQLite" in wiring_call_args
            assert "ARCHITECTURE EXPLANATION:" not in wiring_call_args

            # Test context diagram without enhanced data
            mock_llm.return_value = """flowchart LR
    user([User])
    app[Web App]
    
    user --> app"""

            context_result = await build_context_diagram(requirement, recommendations)

            # Verify recommendation tech stack was used consistently
            context_call_args = mock_llm.call_args[0][0]
            assert "TECHNOLOGY CONTEXT: Python, Flask, SQLite" in context_call_args

            # Verify both diagrams were generated
            assert "flowchart" in wiring_result
            assert "flowchart" in context_result


class TestSessionStateIntegration:
    """Test integration with session state for enhanced data persistence."""

    def test_enhanced_data_retrieval_from_session_state(self):
        """Test retrieving enhanced data from Streamlit session state."""
        # Mock session state with enhanced data
        mock_session_state = {
            "recommendations": {
                "enhanced_tech_stack": ["Python", "FastAPI", "PostgreSQL", "Docker"],
                "architecture_explanation": "Containerized microservice architecture with FastAPI and PostgreSQL.",
            }
        }

        with patch("streamlit_app.st") as mock_st:
            mock_st.session_state.get.return_value = mock_session_state[
                "recommendations"
            ]

            # Import and test the UI class
            from streamlit_app import AAA_UI

            ui = AAA_UI()

            enhanced_data = ui.get_enhanced_analysis_data()

            # Verify data retrieval
            assert enhanced_data["enhanced_tech_stack"] == [
                "Python",
                "FastAPI",
                "PostgreSQL",
                "Docker",
            ]
            assert (
                "Containerized microservice architecture"
                in enhanced_data["architecture_explanation"]
            )
            assert enhanced_data["has_enhanced_data"] is True

    @pytest.mark.asyncio
    async def test_diagram_generation_with_session_state_data(self):
        """Test complete flow from session state to diagram generation."""
        # Setup mock session state
        mock_session_state = {
            "session_id": "test-session-123",
            "requirements": {
                "description": "API gateway with rate limiting",
                "domain": "Infrastructure",
            },
            "recommendations": {
                "enhanced_tech_stack": ["Python", "FastAPI", "Redis", "Nginx"],
                "architecture_explanation": "FastAPI handles API routing, Redis provides rate limiting storage, Nginx acts as reverse proxy.",
            },
        }

        with patch("streamlit_app.st") as mock_st:
            # Setup session state mock
            mock_st.session_state.get.side_effect = (
                lambda key, default=None: mock_session_state.get(key, default)
            )

            # Mock LLM response
            with patch("streamlit_app.make_llm_request") as mock_llm:
                mock_llm.return_value = """flowchart TB
    client[Client]
    nginx[Nginx Proxy]
    api[FastAPI Gateway]
    redis[(Redis Rate Limiter)]
    
    client -->|Request| nginx
    nginx -->|Forward| api
    api -->|Check Rate| redis"""

                # Import and test diagram generation
                from streamlit_app import build_tech_stack_wiring_diagram

                # Simulate the UI flow
                from streamlit_app import AAA_UI

                ui = AAA_UI()
                enhanced_data = ui.get_enhanced_analysis_data()

                # Generate diagram with enhanced data
                recommendations = [
                    {"tech_stack": ["Python", "Flask"], "reasoning": "Basic API"}
                ]

                result = await build_tech_stack_wiring_diagram(
                    mock_session_state["requirements"]["description"],
                    recommendations,
                    enhanced_data["enhanced_tech_stack"],
                    enhanced_data["architecture_explanation"],
                )

                # Verify the complete flow worked
                mock_llm.assert_called_once()
                call_args = mock_llm.call_args[0][0]

                # Check enhanced tech stack was used
                assert "Python, FastAPI, Redis, Nginx" in call_args

                # Check architecture explanation was included
                assert "FastAPI handles API routing" in call_args
                assert "Redis provides rate limiting storage" in call_args

                # Verify diagram output
                assert "FastAPI Gateway" in result
                assert "Redis Rate Limiter" in result
                assert "Nginx Proxy" in result


class TestErrorRecoveryIntegration:
    """Test error recovery and fallback mechanisms in integration scenarios."""

    @pytest.mark.asyncio
    async def test_diagram_generation_fallback_on_enhanced_data_error(self):
        """Test that diagram generation falls back gracefully when enhanced data causes errors."""
        requirement = "Test application"
        recommendations = [
            {"tech_stack": ["Python", "Django"], "reasoning": "Web framework"}
        ]
        enhanced_tech_stack = ["Python", "FastAPI", "PostgreSQL"]
        architecture_explanation = "FastAPI with PostgreSQL backend"

        call_count = 0

        def mock_llm_side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1

            # First call (with enhanced data) fails
            if call_count == 1:
                if "FastAPI" in args[0]:  # Enhanced data call
                    raise Exception("Enhanced data caused LLM error")

            # Second call (fallback) succeeds
            return """flowchart TB
    user[User]
    django[Django App]
    
    user --> django"""

        with patch("streamlit_app.make_llm_request") as mock_llm:
            mock_llm.side_effect = mock_llm_side_effect

            # Import diagram function
            from streamlit_app import build_context_diagram

            # This should succeed with fallback
            result = await build_context_diagram(
                requirement,
                recommendations,
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Verify fallback was used (should have Django, not FastAPI)
            assert "Django App" in result
            assert "FastAPI" not in result
            assert call_count == 2  # First call failed, second succeeded

    @pytest.mark.asyncio
    async def test_multiple_diagram_generation_with_partial_failures(self):
        """Test generating multiple diagrams when some enhanced data causes issues."""
        requirement = "E-commerce platform"
        recommendations = [
            {
                "tech_stack": ["Python", "Django", "MySQL"],
                "reasoning": "E-commerce stack",
            }
        ]
        enhanced_tech_stack = ["Python", "FastAPI", "PostgreSQL", "Redis", "Stripe"]
        architecture_explanation = (
            "FastAPI backend with PostgreSQL, Redis caching, and Stripe payments"
        )

        # Mock different behaviors for different diagram types
        def mock_llm_side_effect(*args, **kwargs):
            prompt = args[0]

            if "context diagram" in prompt.lower():
                # Context diagram works with enhanced data
                return """flowchart LR
    customer([Customer])
    platform[E-commerce Platform]
    payment((Stripe))
    
    customer --> platform
    platform --> payment"""

            elif "container diagram" in prompt.lower():
                # Container diagram fails with enhanced data
                if "FastAPI" in prompt:
                    raise Exception("Container diagram enhanced data error")
                else:
                    # Fallback works
                    return """flowchart TB
    web[Django Web]
    db[(MySQL)]
    
    web --> db"""

            elif "wiring diagram" in prompt.lower():
                # Wiring diagram works with enhanced data
                return """flowchart TB
    api[FastAPI API]
    db[(PostgreSQL)]
    cache[(Redis)]
    stripe((Stripe API))
    
    api --> db
    api --> cache
    api --> stripe"""

            return "flowchart TB\n    default[Default]"

        with patch("streamlit_app.make_llm_request") as mock_llm:
            mock_llm.side_effect = mock_llm_side_effect

            # Import diagram functions
            from streamlit_app import (
                build_context_diagram,
                build_container_diagram,
                build_tech_stack_wiring_diagram,
            )

            # Generate context diagram (should work with enhanced data)
            context_result = await build_context_diagram(
                requirement,
                recommendations,
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Generate container diagram (should fallback to recommendations)
            container_result = await build_container_diagram(
                requirement,
                recommendations,
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Generate wiring diagram (should work with enhanced data)
            wiring_result = await build_tech_stack_wiring_diagram(
                requirement,
                recommendations,
                enhanced_tech_stack,
                architecture_explanation,
            )

            # Verify results
            assert "Stripe" in context_result  # Enhanced data used
            assert "Django" in container_result  # Fallback used
            assert "MySQL" in container_result  # Fallback used
            assert "FastAPI" in wiring_result  # Enhanced data used
            assert "PostgreSQL" in wiring_result  # Enhanced data used


if __name__ == "__main__":
    pytest.main([__file__])
