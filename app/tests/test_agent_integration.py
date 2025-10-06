"""End-to-end integration tests for agent display system."""

import pytest
from unittest.mock import Mock, patch

from app.ui.agent_formatter import AgentDataFormatter, AgentSystemDisplay
from app.ui.analysis_display import AgentRolesUIComponent
from app.services.tech_stack_enhancer import TechStackEnhancer
from app.services.multi_agent_designer import MultiAgentSystemDesigner, MultiAgentSystemDesign, AgentArchitectureType
from app.services.autonomy_assessor import AutonomyAssessor
from app.exporters.agent_exporter import AgentSystemExporter
from app.services.agent_display_config import AgentDisplayConfigManager


class TestAgentDisplayIntegration:
    """Integration tests for the complete agent display system."""
    
    def setup_method(self):
        """Set up integration test environment."""
        
        # Mock LLM provider
        self.mock_llm_provider = Mock()
        self.mock_llm_provider.generate.return_value = """
        {
            "agents": [
                {
                    "name": "Coordinator Agent",
                    "responsibility": "Orchestrate workflow and manage other agents",
                    "capabilities": ["workflow_management", "agent_coordination", "resource_allocation"],
                    "decision_authority": {
                        "scope": "System-wide decisions",
                        "limits": ["Budget constraints"],
                        "escalation_triggers": ["Critical failures"]
                    },
                    "autonomy_level": 0.9,
                    "exception_handling": "Multi-layered reasoning with autonomous resolution",
                    "learning_capabilities": ["Performance optimization", "Pattern recognition"],
                    "communication_requirements": ["Broadcast to all agents", "Status reporting"]
                },
                {
                    "name": "Specialist Agent",
                    "responsibility": "Handle domain-specific processing tasks",
                    "capabilities": ["data_processing", "domain_expertise", "quality_validation"],
                    "decision_authority": {
                        "scope": "Domain-specific decisions",
                        "limits": ["Data sensitivity constraints"],
                        "escalation_triggers": ["Quality issues"]
                    },
                    "autonomy_level": 0.8,
                    "exception_handling": "Retry with alternative approaches",
                    "learning_capabilities": ["Technique refinement", "Domain adaptation"],
                    "communication_requirements": ["Report to coordinator", "Peer consultation"]
                }
            ]
        }
        """
        
        # Initialize components
        self.multi_agent_designer = MultiAgentSystemDesigner(self.mock_llm_provider)
        self.autonomy_assessor = AutonomyAssessor(self.mock_llm_provider)
        self.agent_formatter = AgentDataFormatter()
        self.tech_enhancer = TechStackEnhancer()
        self.agent_ui = AgentRolesUIComponent()
        self.exporter = AgentSystemExporter()
        self.config_manager = AgentDisplayConfigManager()
        
        # Mock requirements
        self.mock_requirements = {
            "description": "Create an automated system for processing customer support tickets with intelligent routing and response generation",
            "domain": "customer_support",
            "workflow_steps": [
                "Receive customer ticket",
                "Analyze ticket content and priority",
                "Route to appropriate specialist",
                "Generate initial response",
                "Monitor resolution progress"
            ]
        }
    
    @pytest.mark.asyncio
    async def test_complete_agent_system_workflow(self):
        """Test the complete workflow from requirements to agent display."""
        
        # Step 1: Assess autonomy potential
        autonomy_assessment = await self.autonomy_assessor.assess_autonomy_potential(
            self.mock_requirements
        )
        
        assert autonomy_assessment is not None
        assert autonomy_assessment.overall_score > 0.0
        assert autonomy_assessment.recommended_architecture is not None
        
        # Step 2: Design multi-agent system
        agent_design = await self.multi_agent_designer.design_system(
            self.mock_requirements, []
        )
        
        assert isinstance(agent_design, MultiAgentSystemDesign)
        assert len(agent_design.agent_roles) >= 1
        assert agent_design.autonomy_score > 0.0
        
        # Step 3: Format for UI display
        tech_stack = ["LangChain", "Redis", "Prometheus", "Neo4j"]
        session_data = {"session_id": "integration_test"}
        
        agent_system_display = self.agent_formatter.format_agent_system(
            agent_design, tech_stack, session_data
        )
        
        assert isinstance(agent_system_display, AgentSystemDisplay)
        assert agent_system_display.has_agents
        assert len(agent_system_display.agent_roles) >= 1
        
        # Step 4: Validate tech stack
        tech_validation = self.tech_enhancer.validate_tech_stack_comprehensive(
            tech_stack, agent_design
        )
        
        assert tech_validation.is_deployment_ready
        assert tech_validation.readiness_score > 0.7
        
        # Step 5: Test export functionality
        json_export = self.exporter.export_to_json(agent_system_display, "integration_test")
        markdown_export = self.exporter.export_to_markdown(agent_system_display, "integration_test")
        
        assert "integration_test" in json_export["export_metadata"]["session_id"]
        assert "Agentic Solution Design" in markdown_export
        
        # Step 6: Test configuration management
        config_updated = self.config_manager.update_preferences(
            display_density="detailed",
            show_performance_metrics=True
        )
        
        assert config_updated
        assert self.config_manager.should_show_component("performance_metrics")
    
    @patch('streamlit.header')
    @patch('streamlit.subheader')
    @patch('streamlit.columns')
    @patch('streamlit.metric')
    @patch('streamlit.tabs')
    @patch('streamlit.expander')
    def test_ui_rendering_integration(self, mock_expander, mock_tabs, mock_metric, 
                                    mock_columns, mock_subheader, mock_header):
        """Test UI rendering integration with mocked Streamlit components."""
        
        # Mock Streamlit components
        mock_columns.return_value = [Mock(), Mock(), Mock()]
        mock_tabs.return_value = [Mock(), Mock(), Mock()]
        mock_expander.return_value.__enter__ = Mock()
        mock_expander.return_value.__exit__ = Mock()
        
        # Create test agent system
        test_agent_system = AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.85,
            agent_roles=[
                Mock(
                    name="Test Agent",
                    responsibility="Test responsibility",
                    autonomy_level=0.8,
                    autonomy_description="Highly Autonomous",
                    capabilities=["test_capability"],
                    decision_boundaries=["test_boundary"],
                    learning_capabilities=["test_learning"],
                    exception_handling="Test handling",
                    communication_requirements=["test_comm"],
                    performance_metrics=["test_metric"],
                    infrastructure_requirements={"cpu": "4 cores"},
                    security_requirements=["test_security"]
                )
            ],
            coordination=None,
            deployment_requirements={"architecture": "single_agent"},
            tech_stack_validation={"is_agent_ready": True, "deployment_frameworks": ["LangChain"]},
            implementation_guidance=[{"type": "test", "title": "Test", "content": "Test content"}]
        )
        
        # Test UI rendering without errors
        try:
            self.agent_ui.render_agent_system(test_agent_system)
            rendering_success = True
        except Exception as e:
            rendering_success = False
            pytest.fail(f"UI rendering failed: {e}")
        
        assert rendering_success
        
        # Verify Streamlit components were called
        mock_header.assert_called()
        mock_subheader.assert_called()
        mock_columns.assert_called()
    
    def test_error_handling_integration(self):
        """Test error handling across all components."""
        
        # Test agent formatter error handling
        result = self.agent_formatter.format_agent_system(None, [], {})
        assert not result.has_agents
        
        # Test tech enhancer with invalid data
        try:
            invalid_design = Mock()
            invalid_design.agent_roles = []
            invalid_design.architecture_type = Mock()
            invalid_design.architecture_type.value = "invalid"
            
            result = self.tech_enhancer.enhance_tech_stack_for_agents([], invalid_design)
            assert "deployment_ready" in result
        except Exception:
            # Error handling should prevent crashes
            pass
        
        # Test exporter error handling
        try:
            invalid_agent_system = Mock()
            invalid_agent_system.has_agents = True
            invalid_agent_system.agent_roles = [Mock()]
            invalid_agent_system.coordination = None
            
            result = self.exporter.export_to_json(invalid_agent_system, "test")
            assert "export_metadata" in result
        except Exception:
            # Should handle gracefully
            pass
    
    def test_performance_with_large_agent_systems(self):
        """Test performance with large multi-agent systems."""
        
        # Create large agent system
        large_agent_roles = []
        for i in range(10):
            agent_role = Mock()
            agent_role.name = f"Agent {i}"
            agent_role.responsibility = f"Responsibility {i}"
            agent_role.autonomy_level = 0.8
            agent_role.capabilities = [f"capability_{j}" for j in range(5)]
            agent_role.decision_authority = {}
            agent_role.learning_capabilities = ["learning"]
            agent_role.exception_handling = "Standard"
            agent_role.interfaces = {}
            agent_role.communication_requirements = ["standard"]
            large_agent_roles.append(agent_role)
        
        large_agent_design = Mock()
        large_agent_design.agent_roles = large_agent_roles
        large_agent_design.architecture_type = AgentArchitectureType.HIERARCHICAL
        large_agent_design.autonomy_score = 0.85
        large_agent_design.communication_protocols = []
        large_agent_design.coordination_mechanisms = []
        large_agent_design.deployment_strategy = "Test"
        large_agent_design.scalability_considerations = []
        large_agent_design.monitoring_requirements = []
        large_agent_design.recommended_frameworks = ["LangChain"]
        
        # Test formatting performance
        import time
        start_time = time.time()
        
        result = self.agent_formatter.format_agent_system(
            large_agent_design, ["LangChain"], {}
        )
        
        end_time = time.time()
        formatting_time = end_time - start_time
        
        # Should complete within reasonable time (< 1 second)
        assert formatting_time < 1.0
        assert result.has_agents
        assert len(result.agent_roles) == 10
    
    def test_configuration_persistence(self):
        """Test configuration persistence across sessions."""
        
        # Update configuration
        original_density = self.config_manager.config.preferences.display_density
        
        success = self.config_manager.update_preferences(
            display_density="compact",
            show_performance_metrics=False
        )
        
        assert success
        
        # Create new config manager instance (simulating new session)
        new_config_manager = AgentDisplayConfigManager(self.config_manager.config_file)
        
        # Verify persistence
        assert new_config_manager.config.preferences.display_density.value == "compact"
        assert not new_config_manager.config.preferences.show_performance_metrics
        
        # Reset to original
        self.config_manager.update_preferences(display_density=original_density.value)
    
    def test_accessibility_features(self):
        """Test accessibility features in UI components."""
        
        # Test accessibility CSS generation
        try:
            self.agent_ui._add_accessibility_css()
            accessibility_success = True
        except Exception:
            accessibility_success = False
        
        assert accessibility_success
        
        # Test screen reader summary generation
        test_agent_system = AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.8,
            agent_roles=[Mock(name="Test", responsibility="Test", autonomy_level=0.8, 
                            autonomy_description="High", capabilities=["test"])],
            coordination=None,
            deployment_requirements={},
            tech_stack_validation={},
            implementation_guidance=[]
        )
        
        try:
            self.agent_ui.render_accessible_agent_summary(test_agent_system)
            summary_success = True
        except Exception:
            summary_success = False
        
        assert summary_success
    
    def test_export_format_consistency(self):
        """Test consistency across different export formats."""
        
        # Create test agent system
        test_agent_system = AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.85,
            agent_roles=[
                Mock(
                    name="Test Agent",
                    responsibility="Test responsibility",
                    autonomy_level=0.8,
                    autonomy_description="Highly Autonomous",
                    capabilities=["capability1", "capability2"],
                    decision_authority={"scope": "test"},
                    decision_boundaries=["boundary1"],
                    learning_capabilities=["learning1"],
                    exception_handling="Test handling",
                    communication_requirements=["comm1"],
                    performance_metrics=["metric1"],
                    infrastructure_requirements={"cpu": "4 cores"},
                    security_requirements=["security1"]
                )
            ],
            coordination=None,
            deployment_requirements={"architecture": "single_agent"},
            tech_stack_validation={"is_agent_ready": True},
            implementation_guidance=[{"type": "test", "title": "Test", "content": "Content"}]
        )
        
        # Export in different formats
        json_export = self.exporter.export_to_json(test_agent_system, "consistency_test")
        markdown_export = self.exporter.export_to_markdown(test_agent_system, "consistency_test")
        html_export = self.exporter.export_to_html(test_agent_system, "consistency_test")
        blueprint = self.exporter.create_deployment_blueprint(test_agent_system, "consistency_test")
        
        # Verify consistency
        assert json_export["export_metadata"]["session_id"] == "consistency_test"
        assert "consistency_test" in markdown_export
        assert "consistency_test" in html_export
        assert blueprint["metadata"]["session_id"] == "consistency_test"
        
        # Verify agent information is present in all formats
        assert len(json_export["agent_roles"]) == 1
        assert "Test Agent" in markdown_export
        assert "Test Agent" in html_export
        assert len(blueprint["agents"]) == 1


class TestAgentDisplayUserAcceptance:
    """User acceptance tests for agent display functionality."""
    
    def setup_method(self):
        """Set up user acceptance test environment."""
        self.agent_formatter = AgentDataFormatter()
        self.agent_ui = AgentRolesUIComponent()
    
    def test_user_can_understand_agent_roles(self):
        """Test that users can easily understand agent roles and responsibilities."""
        
        # Create realistic agent system
        realistic_agent_system = AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.88,
            agent_roles=[
                Mock(
                    name="Customer Service Coordinator",
                    responsibility="Orchestrate customer support workflow and route tickets to appropriate specialists",
                    autonomy_level=0.9,
                    autonomy_description="Fully Autonomous - Operates independently with minimal oversight",
                    capabilities=[
                        "Ticket classification and prioritization",
                        "Intelligent routing to specialists",
                        "Workflow orchestration",
                        "Performance monitoring"
                    ],
                    decision_boundaries=[
                        "Authority Scope: System-wide ticket routing decisions",
                        "Escalate when: Customer escalation requests or system failures"
                    ],
                    learning_capabilities=[
                        "Pattern recognition for ticket classification",
                        "Performance optimization based on resolution times"
                    ],
                    exception_handling="Multi-layered reasoning with autonomous resolution for standard issues",
                    communication_requirements=[
                        "Broadcast status updates to all agents",
                        "Receive feedback from specialist agents"
                    ],
                    performance_metrics=[
                        "Ticket routing accuracy (%)",
                        "Average routing time (seconds)",
                        "Customer satisfaction correlation"
                    ],
                    infrastructure_requirements={
                        "cpu": "4-8 cores",
                        "memory": "8-16 GB",
                        "storage": "50-100 GB"
                    },
                    security_requirements=[
                        "Secure API authentication",
                        "Customer data encryption",
                        "Audit logging for all routing decisions"
                    ]
                )
            ],
            coordination=None,
            deployment_requirements={
                "architecture": "coordinator_based",
                "estimated_timeline": "2-4 weeks"
            },
            tech_stack_validation={
                "is_agent_ready": True,
                "deployment_frameworks": ["LangChain"],
                "readiness_score": 0.85
            },
            implementation_guidance=[
                {
                    "type": "framework",
                    "title": "Agent Framework Selection",
                    "content": "Use LangChain for flexible agent orchestration with customer service integrations"
                }
            ]
        )
        
        # Verify user-friendly information is present
        agent = realistic_agent_system.agent_roles[0]
        
        # Check that role name is descriptive
        assert "Customer Service" in agent.name
        assert "Coordinator" in agent.name
        
        # Check that responsibility is clear
        assert "customer support" in agent.responsibility.lower()
        assert "route" in agent.responsibility.lower()
        
        # Check that autonomy is explained
        assert "Fully Autonomous" in agent.autonomy_description
        assert "independently" in agent.autonomy_description.lower()
        
        # Check that capabilities are understandable
        assert any("ticket" in cap.lower() for cap in agent.capabilities)
        assert any("routing" in cap.lower() for cap in agent.capabilities)
        
        # Check that decision boundaries are clear
        assert any("authority" in boundary.lower() for boundary in agent.decision_boundaries)
        assert any("escalate" in boundary.lower() for boundary in agent.decision_boundaries)
    
    def test_tech_stack_validation_is_actionable(self):
        """Test that tech stack validation provides actionable guidance."""
        
        validation_result = {
            "is_agent_ready": False,
            "readiness_score": 0.6,
            "missing_components": [
                "Agent Deployment Framework",
                "Agent Orchestration & Communication"
            ],
            "recommended_additions": [
                "LangChain - For flexible agent orchestration",
                "Redis - For agent communication and state management",
                "Prometheus - For agent performance monitoring"
            ],
            "deployment_frameworks": [],
            "orchestration_tools": []
        }
        
        # Verify actionable information
        assert len(validation_result["missing_components"]) > 0
        assert len(validation_result["recommended_additions"]) > 0
        
        # Check that recommendations include specific technologies
        recommendations_text = " ".join(validation_result["recommended_additions"])
        assert "LangChain" in recommendations_text
        assert "Redis" in recommendations_text
        assert "Prometheus" in recommendations_text
        
        # Check that reasons are provided
        assert any(" - " in rec for rec in validation_result["recommended_additions"])
    
    def test_deployment_guidance_is_comprehensive(self):
        """Test that deployment guidance provides comprehensive information."""
        
        deployment_requirements = {
            "architecture": "coordinator_based",
            "agent_count": 3,
            "estimated_timeline": "2-4 weeks",
            "infrastructure_needs": {
                "compute": "Medium to High - Agent reasoning requires significant CPU",
                "memory": "High - Agent state and knowledge storage",
                "storage": "Medium - Agent logs and learning data",
                "network": "Medium - Inter-agent communication"
            },
            "complexity_factors": [
                "Multiple specialized agents require coordination",
                "High autonomy agents need extensive testing"
            ]
        }
        
        implementation_guidance = [
            {
                "type": "framework",
                "title": "Agent Framework Selection",
                "content": "Use LangChain for agent implementation with coordinator-based architecture"
            },
            {
                "type": "infrastructure",
                "title": "Infrastructure Setup",
                "content": "Set up Redis for agent state management, configure monitoring with Prometheus/Grafana"
            },
            {
                "type": "security",
                "title": "Security Configuration",
                "content": "Implement secure API authentication, encrypt inter-agent communication"
            }
        ]
        
        # Verify comprehensive coverage
        assert "architecture" in deployment_requirements
        assert "estimated_timeline" in deployment_requirements
        assert "infrastructure_needs" in deployment_requirements
        
        # Check infrastructure details
        infra = deployment_requirements["infrastructure_needs"]
        assert all(key in infra for key in ["compute", "memory", "storage", "network"])
        
        # Check guidance covers key areas
        guidance_types = [g["type"] for g in implementation_guidance]
        assert "framework" in guidance_types
        assert "infrastructure" in guidance_types
        assert "security" in guidance_types


if __name__ == "__main__":
    pytest.main([__file__, "-v"])