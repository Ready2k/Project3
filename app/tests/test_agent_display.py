"""Tests for agent display components."""

import pytest
from unittest.mock import Mock, patch

from app.ui.agent_formatter import (
    AgentDataFormatter,
    AgentSystemDisplay,
    AgentRoleDisplay,
)
from app.ui.analysis_display import AgentRolesUIComponent, AgentDisplayErrorHandler
from app.services.tech_stack_enhancer import TechStackEnhancer
from app.services.multi_agent_designer import (
    MultiAgentSystemDesign,
    AgentRole,
    AgentArchitectureType,
)
from app.exporters.agent_exporter import AgentSystemExporter


class TestAgentDataFormatter:
    """Test agent data formatter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.formatter = AgentDataFormatter()

        # Create mock agent role
        self.mock_agent_role = AgentRole(
            name="Test Agent",
            responsibility="Test responsibility",
            capabilities=["test_capability_1", "test_capability_2"],
            decision_authority={
                "scope": "test_scope",
                "limits": [],
                "escalation_triggers": [],
            },
            autonomy_level=0.8,
            interfaces={"input": "test_input", "output": "test_output"},
            exception_handling="Test exception handling",
            learning_capabilities=["test_learning"],
            communication_requirements=["test_communication"],
        )

        # Create mock agent design
        self.mock_agent_design = MultiAgentSystemDesign(
            architecture_type=AgentArchitectureType.COORDINATOR_BASED,
            agent_roles=[self.mock_agent_role],
            communication_protocols=[],
            coordination_mechanisms=[],
            autonomy_score=0.8,
            recommended_frameworks=["LangChain"],
            deployment_strategy="Test deployment strategy",
            scalability_considerations=["Test scalability"],
            monitoring_requirements=["Test monitoring"],
        )

    def test_format_agent_system_with_valid_design(self):
        """Test formatting agent system with valid design."""

        tech_stack = ["LangChain", "Redis", "Prometheus"]
        session_data = {"session_id": "test_session"}

        result = self.formatter.format_agent_system(
            self.mock_agent_design, tech_stack, session_data
        )

        assert isinstance(result, AgentSystemDisplay)
        assert result.has_agents
        assert result.system_autonomy_score == 0.8
        assert len(result.agent_roles) == 1
        assert result.agent_roles[0].name == "Test Agent"

    def test_format_agent_system_with_none_design(self):
        """Test formatting agent system with None design."""

        result = self.formatter.format_agent_system(None, [], {})

        assert isinstance(result, AgentSystemDisplay)
        assert not result.has_agents
        assert result.system_autonomy_score == 0.0
        assert len(result.agent_roles) == 0

    def test_format_agent_role(self):
        """Test formatting individual agent role."""

        result = self.formatter._format_agent_role(self.mock_agent_role)

        assert isinstance(result, AgentRoleDisplay)
        assert result.name == "Test Agent"
        assert result.autonomy_level == 0.8
        assert "Highly Autonomous" in result.autonomy_description
        assert len(result.capabilities) == 2

    def test_get_autonomy_description(self):
        """Test autonomy description generation."""

        # Test different autonomy levels
        assert "Fully Autonomous" in self.formatter._get_autonomy_description(0.95)
        assert "Highly Autonomous" in self.formatter._get_autonomy_description(0.8)
        assert "Semi-Autonomous" in self.formatter._get_autonomy_description(0.6)
        assert "Assisted" in self.formatter._get_autonomy_description(0.4)
        assert "Manual" in self.formatter._get_autonomy_description(0.2)

    def test_validate_tech_stack_for_agents(self):
        """Test tech stack validation."""

        # Test with complete tech stack
        complete_stack = ["LangChain", "Redis", "Prometheus", "Neo4j"]
        result = self.formatter._validate_tech_stack_for_agents(
            complete_stack, self.mock_agent_design
        )

        assert result["is_agent_ready"]
        assert "LangChain" in result["deployment_frameworks"]
        assert "Redis" in result["orchestration_tools"]

        # Test with incomplete tech stack
        incomplete_stack = ["Python", "FastAPI"]
        result = self.formatter._validate_tech_stack_for_agents(
            incomplete_stack, self.mock_agent_design
        )

        assert not result["is_agent_ready"]
        assert len(result["missing_components"]) > 0

    def test_error_handling(self):
        """Test error handling in formatter."""

        # Test with invalid agent design that causes error
        with patch.object(
            self.formatter, "_format_agent_role", side_effect=Exception("Test error")
        ):
            result = self.formatter.format_agent_system(self.mock_agent_design, [], {})

            assert not result.has_agents
            assert "error" in result.tech_stack_validation


class TestTechStackEnhancer:
    """Test tech stack enhancer functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.enhancer = TechStackEnhancer()

        # Create mock agent design
        self.mock_agent_design = MultiAgentSystemDesign(
            architecture_type=AgentArchitectureType.MULTI_AGENT,
            agent_roles=[
                AgentRole(
                    name="Agent 1",
                    responsibility="Test",
                    capabilities=["api_integration"],
                    decision_authority={},
                    autonomy_level=0.9,
                    interfaces={},
                    exception_handling="Test",
                    learning_capabilities=[],
                    communication_requirements=[],
                )
            ],
            communication_protocols=[],
            coordination_mechanisms=[],
            autonomy_score=0.9,
            recommended_frameworks=[],
            deployment_strategy="",
            scalability_considerations=[],
            monitoring_requirements=[],
        )

    def test_enhance_tech_stack_for_agents(self):
        """Test tech stack enhancement."""

        base_stack = ["Python", "FastAPI"]
        result = self.enhancer.enhance_tech_stack_for_agents(
            base_stack, self.mock_agent_design
        )

        assert "base_technologies" in result
        assert "agent_enhancements" in result
        assert "deployment_ready" in result
        assert result["base_technologies"] == base_stack

    def test_validate_tech_stack_comprehensive(self):
        """Test comprehensive tech stack validation."""

        base_stack = ["LangChain", "Redis", "Prometheus"]
        result = self.enhancer.validate_tech_stack_comprehensive(
            base_stack, self.mock_agent_design
        )

        assert hasattr(result, "is_deployment_ready")
        assert hasattr(result, "readiness_score")
        assert hasattr(result, "enhancement_suggestions")

    def test_find_technologies_by_category(self):
        """Test technology categorization."""

        tech_stack = ["LangChain", "Redis", "Prometheus", "Neo4j"]

        frameworks = self.enhancer._find_technologies_by_category(
            tech_stack, "agent_framework"
        )
        assert "LangChain" in frameworks

        communication = self.enhancer._find_technologies_by_category(
            tech_stack, "communication"
        )
        assert "Redis" in communication


class TestAgentRolesUIComponent:
    """Test agent roles UI component."""

    def setup_method(self):
        """Set up test fixtures."""
        self.ui_component = AgentRolesUIComponent()

        # Create mock agent system display
        self.mock_agent_display = AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.85,
            agent_roles=[
                AgentRoleDisplay(
                    name="Test Agent",
                    responsibility="Test responsibility",
                    autonomy_level=0.8,
                    autonomy_description="Highly Autonomous",
                    capabilities=["test_capability"],
                    decision_authority={},
                    decision_boundaries=["test_boundary"],
                    learning_capabilities=["test_learning"],
                    exception_handling="Test handling",
                    communication_requirements=["test_comm"],
                    performance_metrics=["test_metric"],
                    infrastructure_requirements={"cpu": "4 cores"},
                    security_requirements=["test_security"],
                )
            ],
            coordination=None,
            deployment_requirements={},
            tech_stack_validation={"is_agent_ready": True},
            implementation_guidance=[],
        )

    @patch("streamlit.header")
    @patch("streamlit.subheader")
    @patch("streamlit.columns")
    @patch("streamlit.metric")
    def test_render_system_overview(
        self, mock_metric, mock_columns, mock_subheader, mock_header
    ):
        """Test system overview rendering."""

        # Mock streamlit columns
        mock_columns.return_value = [Mock(), Mock(), Mock()]

        self.ui_component._render_system_overview(self.mock_agent_display)

        # Verify streamlit functions were called
        mock_subheader.assert_called()
        mock_columns.assert_called_with(3)

    def test_get_autonomy_color(self):
        """Test autonomy color generation."""

        # Test different autonomy levels
        assert self.ui_component._get_autonomy_color(0.95) == "#00ff00"  # Green
        assert self.ui_component._get_autonomy_color(0.8) == "#90ee90"  # Light green
        assert self.ui_component._get_autonomy_color(0.6) == "#ffff00"  # Yellow
        assert self.ui_component._get_autonomy_color(0.4) == "#ffa500"  # Orange
        assert self.ui_component._get_autonomy_color(0.2) == "#ff0000"  # Red

    def test_generate_mock_performance_data(self):
        """Test mock performance data generation."""

        agent = self.mock_agent_display.agent_roles[0]
        performance_data = self.ui_component._generate_mock_performance_data(agent)

        assert "task_success_rate" in performance_data
        assert "avg_response_time" in performance_data
        assert "decision_accuracy" in performance_data
        assert "uptime" in performance_data

        # Verify values are reasonable
        assert 0 <= performance_data["task_success_rate"] <= 100
        assert performance_data["avg_response_time"] > 0

    def test_generate_performance_recommendations(self):
        """Test performance recommendations generation."""

        agent = self.mock_agent_display.agent_roles[0]

        # Test with poor performance data
        poor_performance = {
            "avg_response_time": 1000,  # High response time
            "decision_accuracy": 80,  # Low accuracy
            "autonomous_success": 70,  # Low autonomous success
        }

        recommendations = self.ui_component._generate_performance_recommendations(
            agent, poor_performance
        )

        assert len(recommendations) > 0
        assert any("response time" in rec.lower() for rec in recommendations)


class TestAgentSystemExporter:
    """Test agent system exporter functionality."""

    def setup_method(self):
        """Set up test fixtures."""
        self.exporter = AgentSystemExporter()

        # Create mock agent system display
        self.mock_agent_display = AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.85,
            agent_roles=[
                AgentRoleDisplay(
                    name="Test Agent",
                    responsibility="Test responsibility",
                    autonomy_level=0.8,
                    autonomy_description="Highly Autonomous",
                    capabilities=["test_capability"],
                    decision_authority={},
                    decision_boundaries=["test_boundary"],
                    learning_capabilities=["test_learning"],
                    exception_handling="Test handling",
                    communication_requirements=["test_comm"],
                    performance_metrics=["test_metric"],
                    infrastructure_requirements={"cpu": "4 cores"},
                    security_requirements=["test_security"],
                )
            ],
            coordination=None,
            deployment_requirements={"architecture": "single_agent"},
            tech_stack_validation={"is_agent_ready": True},
            implementation_guidance=[
                {"type": "test", "title": "Test", "content": "Test content"}
            ],
        )

    def test_export_to_json(self):
        """Test JSON export functionality."""

        result = self.exporter.export_to_json(self.mock_agent_display, "test_session")

        assert "export_metadata" in result
        assert "agent_system" in result
        assert "agent_roles" in result
        assert result["export_metadata"]["session_id"] == "test_session"
        assert result["agent_system"]["has_agents"]
        assert len(result["agent_roles"]) == 1

    def test_export_to_markdown(self):
        """Test Markdown export functionality."""

        result = self.exporter.export_to_markdown(
            self.mock_agent_display, "test_session"
        )

        assert isinstance(result, str)
        assert "# Agentic Solution Design" in result
        assert "test_session" in result
        assert "Test Agent" in result
        assert "System Overview" in result

    def test_export_to_html(self):
        """Test HTML export functionality."""

        result = self.exporter.export_to_html(self.mock_agent_display, "test_session")

        assert isinstance(result, str)
        assert "<!DOCTYPE html>" in result
        assert "test_session" in result
        assert "Test Agent" in result
        assert "<style>" in result  # CSS included

    def test_create_deployment_blueprint(self):
        """Test deployment blueprint creation."""

        result = self.exporter.create_deployment_blueprint(
            self.mock_agent_display, "test_session"
        )

        assert "metadata" in result
        assert "architecture" in result
        assert "agents" in result
        assert "deployment_configs" in result
        assert result["metadata"]["session_id"] == "test_session"
        assert len(result["agents"]) == 1

    def test_generate_docker_compose(self):
        """Test Docker Compose generation."""

        result = self.exporter._generate_docker_compose(self.mock_agent_display)

        assert isinstance(result, str)
        assert "version: '3.8'" in result
        assert "services:" in result
        assert "redis:" in result
        assert "prometheus:" in result


class TestAgentDisplayErrorHandler:
    """Test agent display error handler."""

    def test_handle_agent_formatting_error(self):
        """Test agent formatting error handling."""

        error = Exception("Test error")
        agent_data = {"test": "data"}

        result = AgentDisplayErrorHandler.handle_agent_formatting_error(
            error, agent_data
        )

        assert isinstance(result, AgentSystemDisplay)
        assert not result.has_agents
        assert "error" in result.tech_stack_validation

    def test_handle_tech_validation_error(self):
        """Test tech validation error handling."""

        error = Exception("Test error")
        tech_stack = ["Python", "FastAPI"]

        result = AgentDisplayErrorHandler.handle_tech_validation_error(
            error, tech_stack
        )

        assert isinstance(result, dict)
        assert not result["is_agent_ready"]
        assert "error" in result
        assert "fallback_recommendations" in result

    @patch("streamlit.error")
    @patch("streamlit.write")
    def test_handle_ui_rendering_error(self, mock_write, mock_error):
        """Test UI rendering error handling."""

        error = Exception("Test error")
        component_name = "Test Component"

        AgentDisplayErrorHandler.handle_ui_rendering_error(error, component_name)

        # Verify streamlit error function was called
        mock_error.assert_called()


# Integration tests
class TestAgentDisplayIntegration:
    """Integration tests for agent display components."""

    def setup_method(self):
        """Set up integration test fixtures."""
        self.formatter = AgentDataFormatter()
        self.enhancer = TechStackEnhancer()
        self.exporter = AgentSystemExporter()

    def test_end_to_end_agent_display_flow(self):
        """Test complete agent display flow from formatting to export."""

        # Create mock agent design
        mock_agent_design = MultiAgentSystemDesign(
            architecture_type=AgentArchitectureType.COORDINATOR_BASED,
            agent_roles=[
                AgentRole(
                    name="Coordinator",
                    responsibility="Orchestrate workflow",
                    capabilities=["coordination", "planning"],
                    decision_authority={"scope": "system_wide"},
                    autonomy_level=0.9,
                    interfaces={},
                    exception_handling="Autonomous resolution",
                    learning_capabilities=["optimization"],
                    communication_requirements=["broadcast"],
                )
            ],
            communication_protocols=[],
            coordination_mechanisms=[],
            autonomy_score=0.9,
            recommended_frameworks=["LangChain"],
            deployment_strategy="Containerized deployment",
            scalability_considerations=["Horizontal scaling"],
            monitoring_requirements=["Performance metrics"],
        )

        # Format agent system
        tech_stack = ["LangChain", "Redis", "Prometheus"]
        session_data = {"session_id": "integration_test"}

        agent_display = self.formatter.format_agent_system(
            mock_agent_design, tech_stack, session_data
        )

        # Verify formatting
        assert agent_display.has_agents
        assert len(agent_display.agent_roles) == 1
        assert agent_display.agent_roles[0].name == "Coordinator"

        # Test tech stack validation
        tech_validation = self.enhancer.validate_tech_stack_comprehensive(
            tech_stack, mock_agent_design
        )

        assert tech_validation.is_deployment_ready
        assert tech_validation.readiness_score > 0.7

        # Test export functionality
        json_export = self.exporter.export_to_json(agent_display, "integration_test")
        markdown_export = self.exporter.export_to_markdown(
            agent_display, "integration_test"
        )

        assert "integration_test" in json_export["export_metadata"]["session_id"]
        assert "Coordinator" in markdown_export
        assert "# Agentic Solution Design" in markdown_export


if __name__ == "__main__":
    pytest.main([__file__])
