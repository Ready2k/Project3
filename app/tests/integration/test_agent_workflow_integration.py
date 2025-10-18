"""Integration tests for multi-agent workflow functionality."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from app.services.agentic_recommendation_service import AgenticRecommendationService
from app.services.multi_agent_designer import MultiAgentSystemDesigner
from app.services.autonomy_assessor import (
    AutonomyAssessment,
    DecisionIndependence,
    AgentArchitectureRecommendation,
)


class TestAgentWorkflowIntegration:
    """Test end-to-end agent generation and display workflow."""

    @pytest.fixture
    def mock_llm_provider(self):
        """Create mock LLM provider."""
        mock_llm = AsyncMock()
        mock_llm.generate.return_value = '{"agents": []}'  # Default empty response
        return mock_llm

    @pytest.fixture
    def agentic_service(self, mock_llm_provider):
        """Create agentic recommendation service."""
        return AgenticRecommendationService(mock_llm_provider)

    @pytest.fixture
    def multi_agent_designer(self, mock_llm_provider):
        """Create multi-agent system designer."""
        return MultiAgentSystemDesigner(mock_llm_provider)

    @pytest.fixture
    def sample_requirements(self):
        """Sample requirements for testing."""
        return {
            "description": "As a BFA System I want an account that is marked as deceased and has an active care case to be marked as Deceased Care DNP and moved into Do Not Pursue",
            "domain": "customer-service",
            "pattern_types": ["workflow"],
        }

    @pytest.fixture
    def mock_autonomy_assessment(self):
        """Create mock autonomy assessment."""
        assessment = AutonomyAssessment(
            overall_score=0.87,
            decision_independence=DecisionIndependence.HIGH,
            reasoning_requirements=["logical_reasoning", "pattern_matching"],
            recommended_architecture=AgentArchitectureRecommendation.SINGLE_AGENT,
            automation_boundaries={"scope": "digital_workflow"},
            human_oversight_needs=["critical_errors"],
            confidence_score=0.85,
        )
        return assessment

    @pytest.mark.asyncio
    async def test_end_to_end_agent_generation_no_duplicates(
        self, agentic_service, sample_requirements, mock_autonomy_assessment
    ):
        """Test that end-to-end agent generation produces unique agents."""

        # Mock the autonomy assessor
        with patch.object(
            agentic_service.autonomy_assessor,
            "assess_autonomy_potential",
            return_value=mock_autonomy_assessment,
        ):
            # Mock the agentic pattern matcher to return multiple matches
            mock_matches = []
            for i in range(3):
                mock_match = MagicMock()
                mock_match.pattern_id = f"APAT-00{i+1}-workflow"
                mock_match.confidence = 0.8 + (i * 0.05)
                mock_match.autonomy_score = 0.85 + (i * 0.02)
                mock_match.reasoning_capabilities = [
                    "logical_reasoning",
                    "pattern_matching",
                ]
                mock_match.enhanced_pattern = {
                    "agentic_frameworks": ["LangChain"],
                    "tech_stack": ["FastAPI", "PostgreSQL"],
                }
                mock_match.decision_scope = {
                    "autonomous_decisions": ["status_updates", "workflow_management"]
                }
                mock_match.exception_handling = "Autonomous resolution with escalation"
                mock_match.multi_agent_potential = False
                mock_matches.append(mock_match)

            # Mock the agentic matcher
            with patch(
                "app.pattern.agentic_matcher.AgenticPatternMatcher"
            ) as mock_matcher_class:
                mock_matcher = AsyncMock()
                mock_matcher.match_agentic_patterns.return_value = mock_matches
                mock_matcher_class.return_value = mock_matcher

                # Generate recommendations
                recommendations = (
                    await agentic_service.generate_agentic_recommendations(
                        sample_requirements, session_id="test_session"
                    )
                )

                # Verify we got recommendations
                assert len(recommendations) > 0

                # Collect all agent roles from all recommendations
                all_agent_roles = []
                for rec in recommendations:
                    if rec.agent_roles:
                        all_agent_roles.extend(rec.agent_roles)

                # Verify agents are unique
                agent_names = [agent["name"] for agent in all_agent_roles]
                unique_names = set(agent_names)

                # Should have unique agent names (no duplicates)
                assert len(agent_names) == len(
                    unique_names
                ), f"Found duplicate agent names: {agent_names}"

                # Verify agents have different specializations
                for i, agent in enumerate(all_agent_roles):
                    assert (
                        agent["name"] != "User Management Agent" or i == 0
                    ), "Only first agent should be base User Management Agent"

    @pytest.mark.asyncio
    async def test_multi_agent_designer_creates_diverse_agents(
        self, multi_agent_designer, sample_requirements
    ):
        """Test that multi-agent designer creates diverse agents."""

        # Mock LLM response for agent role generation
        mock_response = """
        {
            "agents": [
                {
                    "name": "Account Status Manager",
                    "responsibility": "Manages deceased account status updates",
                    "capabilities": ["status_management", "account_updates"],
                    "decision_authority": {
                        "scope": "account_status_decisions",
                        "limits": ["no_financial_changes"],
                        "escalation_triggers": ["data_conflicts"]
                    },
                    "autonomy_level": 0.9,
                    "exception_handling": "Autonomous resolution with logging",
                    "learning_capabilities": ["pattern_recognition"],
                    "communication_requirements": ["status_notifications"]
                },
                {
                    "name": "Care Case Coordinator",
                    "responsibility": "Coordinates care case transitions",
                    "capabilities": ["case_management", "workflow_coordination"],
                    "decision_authority": {
                        "scope": "case_workflow_decisions",
                        "limits": ["no_policy_changes"],
                        "escalation_triggers": ["complex_cases"]
                    },
                    "autonomy_level": 0.85,
                    "exception_handling": "Escalate complex scenarios",
                    "learning_capabilities": ["workflow_optimization"],
                    "communication_requirements": ["case_updates"]
                },
                {
                    "name": "DNP Processing Agent",
                    "responsibility": "Handles Do Not Pursue processing",
                    "capabilities": ["dnp_processing", "compliance_checking"],
                    "decision_authority": {
                        "scope": "dnp_decisions",
                        "limits": ["compliance_requirements"],
                        "escalation_triggers": ["regulatory_issues"]
                    },
                    "autonomy_level": 0.8,
                    "exception_handling": "Compliance-first approach",
                    "learning_capabilities": ["regulatory_updates"],
                    "communication_requirements": ["compliance_reporting"]
                }
            ]
        }
        """

        multi_agent_designer.llm_provider.generate.return_value = mock_response

        # Create mock workflow analysis
        from app.services.multi_agent_designer import WorkflowAnalysis

        workflow_analysis = WorkflowAnalysis(
            complexity_score=0.7,
            parallel_potential=0.6,
            coordination_requirements=["status_sync", "case_handoff"],
            specialization_opportunities=[
                "account_management",
                "case_coordination",
                "dnp_processing",
            ],
            bottleneck_identification=["data_validation"],
        )

        # Generate agent roles
        agent_roles = await multi_agent_designer._define_agent_roles(
            sample_requirements,
            workflow_analysis,
            multi_agent_designer._determine_architecture(
                workflow_analysis, sample_requirements
            ),
        )

        # Verify diverse agents were created
        assert len(agent_roles) == 3

        agent_names = [role.name for role in agent_roles]
        assert "Account Status Manager" in agent_names
        assert "Care Case Coordinator" in agent_names
        assert "DNP Processing Agent" in agent_names

        # Verify agents have different responsibilities
        responsibilities = [role.responsibility for role in agent_roles]
        assert (
            len(set(responsibilities)) == 3
        ), "All agents should have unique responsibilities"

        # Verify agents have different capabilities
        all_capabilities = []
        for role in agent_roles:
            all_capabilities.extend(role.capabilities)

        # Should have diverse capabilities across agents
        unique_capabilities = set(all_capabilities)
        assert (
            len(unique_capabilities) >= 4
        ), "Should have diverse capabilities across agents"

    @pytest.mark.asyncio
    async def test_streamlit_deduplication_logic(self):
        """Test the Streamlit deduplication logic with mock data."""

        # Mock recommendations with duplicate and unique agents
        mock_recommendations = [
            {
                "agent_roles": [
                    {
                        "name": "User Management Agent",
                        "responsibility": "Main autonomous agent responsible for user account management",
                    }
                ]
            },
            {
                "agent_roles": [
                    {
                        "name": "User Management Agent",
                        "responsibility": "Main autonomous agent responsible for user account management",  # Duplicate
                    }
                ]
            },
            {
                "agent_roles": [
                    {
                        "name": "Workflow User Management Agent",
                        "responsibility": "Specialized autonomous agent for workflow pattern",
                    }
                ]
            },
            {
                "agent_roles": [
                    {
                        "name": "Data Processing User Management Agent",
                        "responsibility": "Specialized autonomous agent for data processing pattern",
                    }
                ]
            },
        ]

        # Apply the Streamlit deduplication logic
        agent_roles_found = []
        seen_agents = set()

        for recommendation in mock_recommendations:
            agent_roles_data = recommendation.get("agent_roles", [])
            if agent_roles_data:
                for agent in agent_roles_data:
                    agent_name = agent.get("name", "Unknown Agent")
                    agent_responsibility = agent.get("responsibility", "")

                    agent_id = f"{agent_name}|{agent_responsibility[:50]}"

                    if agent_id not in seen_agents:
                        seen_agents.add(agent_id)
                        agent_roles_found.append(agent)

        # Apply validation logic
        validated_agents = []
        for agent in agent_roles_found:
            if not agent.get("name"):
                agent["name"] = "Unnamed Agent"
            if not agent.get("responsibility"):
                agent["responsibility"] = (
                    f"Autonomous agent responsible for {agent.get('name', 'task')} operations"
                )
            if not agent.get("capabilities"):
                agent["capabilities"] = [
                    "task_execution",
                    "decision_making",
                    "exception_handling",
                ]
            if not isinstance(agent.get("autonomy_level"), (int, float)):
                agent["autonomy_level"] = 0.8

            validated_agents.append(agent)

        # Verify results
        assert (
            len(validated_agents) == 3
        ), "Should have 3 unique agents after deduplication"

        agent_names = [agent["name"] for agent in validated_agents]
        assert "User Management Agent" in agent_names
        assert "Workflow User Management Agent" in agent_names
        assert "Data Processing User Management Agent" in agent_names

        # Verify all agents have required fields
        for agent in validated_agents:
            assert agent.get("name")
            assert agent.get("responsibility")
            assert agent.get("capabilities")
            assert isinstance(agent.get("autonomy_level"), (int, float))

    @pytest.mark.asyncio
    async def test_bug_reproduction_scenario(
        self, agentic_service, sample_requirements, mock_autonomy_assessment
    ):
        """Test the specific bug scenario: 5 identical agents should become 5 unique agents."""

        # Mock the autonomy assessor
        with patch.object(
            agentic_service.autonomy_assessor,
            "assess_autonomy_potential",
            return_value=mock_autonomy_assessment,
        ):
            # Mock 5 pattern matches (simulating the original bug scenario)
            mock_matches = []
            pattern_types = ["workflow", "data", "integration", "monitoring", "user"]

            for i, pattern_type in enumerate(pattern_types):
                mock_match = MagicMock()
                mock_match.pattern_id = f"APAT-00{i+1}-{pattern_type}"
                mock_match.confidence = 0.8 + (i * 0.02)
                mock_match.autonomy_score = 0.85 + (i * 0.01)
                mock_match.reasoning_capabilities = [
                    "logical_reasoning",
                    "pattern_matching",
                ]
                mock_match.enhanced_pattern = {
                    "agentic_frameworks": ["LangChain"],
                    "tech_stack": ["FastAPI", "PostgreSQL"],
                }
                mock_match.decision_scope = {
                    "autonomous_decisions": ["status_updates", "workflow_management"]
                }
                mock_match.exception_handling = "Autonomous resolution with escalation"
                mock_match.multi_agent_potential = False
                mock_matches.append(mock_match)

            # Mock the agentic matcher
            with patch(
                "app.pattern.agentic_matcher.AgenticPatternMatcher"
            ) as mock_matcher_class:
                mock_matcher = AsyncMock()
                mock_matcher.match_agentic_patterns.return_value = mock_matches
                mock_matcher_class.return_value = mock_matcher

                # Generate recommendations
                recommendations = (
                    await agentic_service.generate_agentic_recommendations(
                        sample_requirements, session_id="bug_test_session"
                    )
                )

                # Collect all agent roles (simulating Streamlit logic)
                agent_roles_found = []
                seen_agents = set()

                for recommendation in recommendations:
                    agent_roles_data = recommendation.agent_roles or []
                    for agent in agent_roles_data:
                        agent_name = agent.get("name", "Unknown Agent")
                        agent_responsibility = agent.get("responsibility", "")

                        agent_id = f"{agent_name}|{agent_responsibility[:50]}"

                        if agent_id not in seen_agents:
                            seen_agents.add(agent_id)
                            agent_roles_found.append(agent)

                # The bug fix should ensure we have unique agents, not 5 identical ones
                assert len(agent_roles_found) >= 3, "Should have multiple unique agents"

                # Verify agents have different names
                agent_names = [agent["name"] for agent in agent_roles_found]
                unique_names = set(agent_names)

                # This is the key test: we should NOT have 5 identical "User Management Agent" entries
                user_management_count = agent_names.count("User Management Agent")
                assert (
                    user_management_count <= 1
                ), f"Should not have multiple identical 'User Management Agent' entries, found {user_management_count}"

                # Verify we have diverse agent names
                assert (
                    len(unique_names) >= 3
                ), f"Should have at least 3 unique agent names, got: {agent_names}"

                # Verify agents have specialized names based on patterns
                specialized_agents = [
                    name
                    for name in agent_names
                    if "Workflow" in name
                    or "Data Processing" in name
                    or "Integration" in name
                ]
                assert (
                    len(specialized_agents) >= 2
                ), f"Should have specialized agent names, got: {agent_names}"
