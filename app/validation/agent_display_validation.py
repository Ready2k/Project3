"""Validation script for agent display system integration."""

import sys
import traceback
from typing import Dict, Any, List
import asyncio

# Add the app directory to the path
sys.path.append('.')

from app.ui.agent_formatter import AgentDataFormatter, AgentSystemDisplay
from app.ui.analysis_display import AgentRolesUIComponent
from app.services.tech_stack_enhancer import TechStackEnhancer
from app.services.multi_agent_designer import MultiAgentSystemDesigner, AgentRole, AgentArchitectureType
from app.services.autonomy_assessor import AutonomyAssessor
from app.exporters.agent_exporter import AgentSystemExporter
from app.services.agent_display_config import AgentDisplayConfigManager
from app.utils.logger import app_logger


class AgentDisplayValidator:
    """Validates the complete agent display system."""
    
    def __init__(self):
        self.validation_results = {
            "component_tests": {},
            "integration_tests": {},
            "performance_tests": {},
            "accessibility_tests": {},
            "overall_status": "UNKNOWN"
        }
    
    def run_validation(self) -> Dict[str, Any]:
        """Run complete validation suite."""
        
        print("🚀 Starting Agent Display System Validation...")
        print("=" * 60)
        
        try:
            # Component validation
            self._validate_components()
            
            # Integration validation
            self._validate_integration()
            
            # Performance validation
            self._validate_performance()
            
            # Accessibility validation
            self._validate_accessibility()
            
            # Determine overall status
            self._determine_overall_status()
            
            # Print results
            self._print_results()
            
        except Exception as e:
            print(f"❌ Validation failed with error: {e}")
            traceback.print_exc()
            self.validation_results["overall_status"] = "FAILED"
        
        return self.validation_results
    
    def _validate_components(self):
        """Validate individual components."""
        
        print("\n📦 Validating Individual Components...")
        
        # Test AgentDataFormatter
        try:
            formatter = AgentDataFormatter()
            
            # Test with None input
            result = formatter.format_agent_system(None, [], {})
            assert result.has_agents == False
            
            self.validation_results["component_tests"]["agent_formatter"] = "PASS"
            print("  ✅ AgentDataFormatter: PASS")
            
        except Exception as e:
            self.validation_results["component_tests"]["agent_formatter"] = f"FAIL: {e}"
            print(f"  ❌ AgentDataFormatter: FAIL - {e}")
        
        # Test TechStackEnhancer
        try:
            enhancer = TechStackEnhancer()
            
            # Test with basic tech stack
            mock_design = self._create_mock_agent_design()
            result = enhancer.enhance_tech_stack_for_agents(["Python"], mock_design)
            assert "deployment_ready" in result
            
            self.validation_results["component_tests"]["tech_stack_enhancer"] = "PASS"
            print("  ✅ TechStackEnhancer: PASS")
            
        except Exception as e:
            self.validation_results["component_tests"]["tech_stack_enhancer"] = f"FAIL: {e}"
            print(f"  ❌ TechStackEnhancer: FAIL - {e}")
        
        # Test AgentRolesUIComponent
        try:
            ui_component = AgentRolesUIComponent()
            
            # Test color generation
            color = ui_component._get_autonomy_color(0.8)
            assert color is not None
            
            self.validation_results["component_tests"]["ui_component"] = "PASS"
            print("  ✅ AgentRolesUIComponent: PASS")
            
        except Exception as e:
            self.validation_results["component_tests"]["ui_component"] = f"FAIL: {e}"
            print(f"  ❌ AgentRolesUIComponent: FAIL - {e}")
        
        # Test AgentSystemExporter
        try:
            exporter = AgentSystemExporter()
            
            # Test JSON export
            mock_agent_system = self._create_mock_agent_system()
            result = exporter.export_to_json(mock_agent_system, "test")
            assert "export_metadata" in result
            
            self.validation_results["component_tests"]["exporter"] = "PASS"
            print("  ✅ AgentSystemExporter: PASS")
            
        except Exception as e:
            self.validation_results["component_tests"]["exporter"] = f"FAIL: {e}"
            print(f"  ❌ AgentSystemExporter: FAIL - {e}")
        
        # Test Configuration Manager
        try:
            config_manager = AgentDisplayConfigManager("test_config.json")
            
            # Test configuration update
            success = config_manager.update_preferences(display_density="compact")
            assert success == True
            
            self.validation_results["component_tests"]["config_manager"] = "PASS"
            print("  ✅ AgentDisplayConfigManager: PASS")
            
        except Exception as e:
            self.validation_results["component_tests"]["config_manager"] = f"FAIL: {e}"
            print(f"  ❌ AgentDisplayConfigManager: FAIL - {e}")
    
    def _validate_integration(self):
        """Validate component integration."""
        
        print("\n🔗 Validating Component Integration...")
        
        try:
            # Test complete workflow
            formatter = AgentDataFormatter()
            enhancer = TechStackEnhancer()
            exporter = AgentSystemExporter()
            
            # Create test data
            mock_design = self._create_mock_agent_design()
            tech_stack = ["LangChain", "Redis", "Prometheus"]
            
            # Format agent system
            agent_system = formatter.format_agent_system(mock_design, tech_stack, {})
            assert agent_system.has_agents == True
            
            # Validate tech stack
            validation = enhancer.validate_tech_stack_comprehensive(tech_stack, mock_design)
            assert validation.is_deployment_ready == True
            
            # Export system
            json_export = exporter.export_to_json(agent_system, "integration_test")
            assert "integration_test" in json_export["export_metadata"]["session_id"]
            
            self.validation_results["integration_tests"]["workflow"] = "PASS"
            print("  ✅ Complete Workflow Integration: PASS")
            
        except Exception as e:
            self.validation_results["integration_tests"]["workflow"] = f"FAIL: {e}"
            print(f"  ❌ Complete Workflow Integration: FAIL - {e}")
        
        # Test error handling integration
        try:
            formatter = AgentDataFormatter()
            
            # Test with invalid data
            result = formatter.format_agent_system(None, [], {})
            assert result.has_agents == False
            
            # Test error display
            error_result = formatter._create_error_display("Test error")
            assert "error" in error_result.tech_stack_validation
            
            self.validation_results["integration_tests"]["error_handling"] = "PASS"
            print("  ✅ Error Handling Integration: PASS")
            
        except Exception as e:
            self.validation_results["integration_tests"]["error_handling"] = f"FAIL: {e}"
            print(f"  ❌ Error Handling Integration: FAIL - {e}")
    
    def _validate_performance(self):
        """Validate performance characteristics."""
        
        print("\n⚡ Validating Performance...")
        
        try:
            import time
            
            formatter = AgentDataFormatter()
            
            # Test with large agent system
            large_design = self._create_large_agent_design()
            
            start_time = time.time()
            result = formatter.format_agent_system(large_design, ["LangChain"], {})
            end_time = time.time()
            
            formatting_time = end_time - start_time
            
            # Should complete within 1 second
            assert formatting_time < 1.0
            assert result.has_agents == True
            
            self.validation_results["performance_tests"]["formatting_speed"] = f"PASS ({formatting_time:.3f}s)"
            print(f"  ✅ Formatting Performance: PASS ({formatting_time:.3f}s)")
            
        except Exception as e:
            self.validation_results["performance_tests"]["formatting_speed"] = f"FAIL: {e}"
            print(f"  ❌ Formatting Performance: FAIL - {e}")
        
        # Test export performance
        try:
            exporter = AgentSystemExporter()
            agent_system = self._create_mock_agent_system()
            
            start_time = time.time()
            markdown_export = exporter.export_to_markdown(agent_system, "perf_test")
            end_time = time.time()
            
            export_time = end_time - start_time
            
            # Should complete within 0.5 seconds
            assert export_time < 0.5
            assert len(markdown_export) > 0
            
            self.validation_results["performance_tests"]["export_speed"] = f"PASS ({export_time:.3f}s)"
            print(f"  ✅ Export Performance: PASS ({export_time:.3f}s)")
            
        except Exception as e:
            self.validation_results["performance_tests"]["export_speed"] = f"FAIL: {e}"
            print(f"  ❌ Export Performance: FAIL - {e}")
    
    def _validate_accessibility(self):
        """Validate accessibility features."""
        
        print("\n♿ Validating Accessibility Features...")
        
        try:
            ui_component = AgentRolesUIComponent()
            
            # Test accessibility CSS generation
            ui_component._add_accessibility_css()
            
            # Test screen reader summary
            agent_system = self._create_mock_agent_system()
            ui_component.render_accessible_agent_summary(agent_system)
            
            self.validation_results["accessibility_tests"]["features"] = "PASS"
            print("  ✅ Accessibility Features: PASS")
            
        except Exception as e:
            self.validation_results["accessibility_tests"]["features"] = f"FAIL: {e}"
            print(f"  ❌ Accessibility Features: FAIL - {e}")
        
        # Test keyboard navigation support
        try:
            ui_component = AgentRolesUIComponent()
            ui_component._add_keyboard_navigation_support()
            
            self.validation_results["accessibility_tests"]["keyboard_navigation"] = "PASS"
            print("  ✅ Keyboard Navigation: PASS")
            
        except Exception as e:
            self.validation_results["accessibility_tests"]["keyboard_navigation"] = f"FAIL: {e}"
            print(f"  ❌ Keyboard Navigation: FAIL - {e}")
    
    def _determine_overall_status(self):
        """Determine overall validation status."""
        
        all_tests = []
        
        # Collect all test results
        for category in ["component_tests", "integration_tests", "performance_tests", "accessibility_tests"]:
            for test_name, result in self.validation_results[category].items():
                all_tests.append(result.startswith("PASS"))
        
        # Determine status
        if all(all_tests):
            self.validation_results["overall_status"] = "PASS"
        elif any(all_tests):
            self.validation_results["overall_status"] = "PARTIAL"
        else:
            self.validation_results["overall_status"] = "FAIL"
    
    def _print_results(self):
        """Print validation results summary."""
        
        print("\n" + "=" * 60)
        print("📊 VALIDATION RESULTS SUMMARY")
        print("=" * 60)
        
        # Overall status
        status = self.validation_results["overall_status"]
        if status == "PASS":
            print("🎉 Overall Status: ✅ PASS - All systems operational!")
        elif status == "PARTIAL":
            print("⚠️  Overall Status: 🟡 PARTIAL - Some issues detected")
        else:
            print("💥 Overall Status: ❌ FAIL - Critical issues found")
        
        print()
        
        # Detailed results
        for category, tests in self.validation_results.items():
            if category == "overall_status":
                continue
            
            print(f"{category.replace('_', ' ').title()}:")
            if isinstance(tests, dict):
                for test_name, result in tests.items():
                    status_icon = "✅" if result.startswith("PASS") else "❌"
                    print(f"  {status_icon} {test_name}: {result}")
            print()
        
        # Recommendations
        if self.validation_results["overall_status"] != "PASS":
            print("🔧 RECOMMENDATIONS:")
            print("  - Check failed components and fix issues")
            print("  - Run validation again after fixes")
            print("  - Consider running individual component tests for debugging")
        else:
            print("🚀 READY FOR DEPLOYMENT:")
            print("  - All agent display components are working correctly")
            print("  - System is ready for production use")
            print("  - Performance and accessibility standards met")
    
    def _create_mock_agent_design(self):
        """Create mock agent design for testing."""
        
        from unittest.mock import Mock
        
        mock_design = Mock()
        # Create a proper mock agent role
        mock_role = Mock()
        mock_role.name = "Test Agent"
        mock_role.responsibility = "Test responsibility"
        mock_role.capabilities = ["test_capability"]
        mock_role.decision_authority = {"scope": "test_scope", "level": "medium"}
        mock_role.autonomy_level = 0.8
        mock_role.interfaces = {"input": "test_input", "output": "test_output"}
        mock_role.exception_handling = "Test handling"
        mock_role.learning_capabilities = ["test_learning"]
        mock_role.communication_requirements = ["test_comm"]
        
        mock_design.agent_roles = [mock_role]
        mock_design.architecture_type = AgentArchitectureType.HIERARCHICAL
        mock_design.autonomy_score = 0.8
        
        # Create proper mock objects for protocols and mechanisms
        mock_protocol = Mock()
        mock_protocol.protocol_type = Mock()
        mock_protocol.protocol_type.value = "message_passing"
        mock_protocol.participants = ["Test Agent"]
        mock_protocol.message_format = "JSON"
        mock_protocol.reliability_requirements = "high"
        mock_protocol.latency_requirements = "low"
        
        mock_mechanism = Mock()
        mock_mechanism.mechanism_type = Mock()
        mock_mechanism.mechanism_type.value = "consensus"
        mock_mechanism.participants = ["Test Agent"]
        mock_mechanism.decision_criteria = ["accuracy", "speed"]
        mock_mechanism.conflict_resolution = "voting"
        mock_mechanism.performance_metrics = ["response_time", "accuracy"]
        
        mock_design.communication_protocols = [mock_protocol]
        mock_design.coordination_mechanisms = [mock_mechanism]
        mock_design.deployment_strategy = "Test strategy"
        mock_design.scalability_considerations = []
        mock_design.monitoring_requirements = []
        mock_design.recommended_frameworks = ["LangChain"]
        
        return mock_design
    
    def _create_large_agent_design(self):
        """Create large agent design for performance testing."""
        
        from unittest.mock import Mock
        
        # Create 10 agents
        large_roles = []
        for i in range(10):
            role = Mock()
            role.name = f"Agent {i}"
            role.responsibility = f"Responsibility {i}"
            role.capabilities = [f"capability_{j}" for j in range(5)]
            role.decision_authority = {}
            role.autonomy_level = 0.8
            role.interfaces = {}
            role.exception_handling = "Standard"
            role.learning_capabilities = ["learning"]
            role.communication_requirements = ["standard"]
            large_roles.append(role)
        
        mock_design = Mock()
        mock_design.agent_roles = large_roles
        mock_design.architecture_type = AgentArchitectureType.HIERARCHICAL
        mock_design.autonomy_score = 0.85
        mock_design.communication_protocols = []
        mock_design.coordination_mechanisms = []
        mock_design.deployment_strategy = "Large system strategy"
        mock_design.scalability_considerations = ["Horizontal scaling"]
        mock_design.monitoring_requirements = ["Comprehensive monitoring"]
        mock_design.recommended_frameworks = ["LangChain", "CrewAI"]
        
        return mock_design
    
    def _create_mock_agent_system(self):
        """Create mock agent system display for testing."""
        
        from unittest.mock import Mock
        
        return AgentSystemDisplay(
            has_agents=True,
            system_autonomy_score=0.85,
            agent_roles=[
                Mock(
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
                    security_requirements=["test_security"]
                )
            ],
            coordination=None,
            deployment_requirements={"architecture": "single_agent"},
            tech_stack_validation={"is_agent_ready": True},
            implementation_guidance=[{"type": "test", "title": "Test", "content": "Test content"}]
        )


def main():
    """Main validation entry point."""
    
    validator = AgentDisplayValidator()
    results = validator.run_validation()
    
    # Exit with appropriate code
    if results["overall_status"] == "PASS":
        sys.exit(0)
    elif results["overall_status"] == "PARTIAL":
        sys.exit(1)
    else:
        sys.exit(2)


if __name__ == "__main__":
    main()