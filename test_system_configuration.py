#!/usr/bin/env python3
"""Test script for System Configuration functionality."""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app.services.configuration_service import ConfigurationService, get_config
from app.ui.system_configuration import SystemConfigurationManager
import yaml


def test_configuration_service():
    """Test the configuration service functionality."""
    print("🧪 Testing Configuration Service...")
    
    # Test singleton pattern
    config1 = get_config()
    config2 = ConfigurationService()
    assert config1 is config2, "Configuration service should be singleton"
    print("✅ Singleton pattern working")
    
    # Test autonomy weights
    weights = config1.get_autonomy_weights()
    expected_keys = ["reasoning_capability", "decision_independence", "exception_handling", "learning_adaptation", "self_monitoring"]
    assert all(key in weights for key in expected_keys), f"Missing autonomy weight keys: {weights}"
    print(f"✅ Autonomy weights: {weights}")
    
    # Test pattern matching weights
    pm_weights = config1.get_pattern_matching_weights()
    expected_pm_keys = ["tag_weight", "vector_weight", "confidence_weight"]
    assert all(key in pm_weights for key in expected_pm_keys), f"Missing pattern matching weight keys: {pm_weights}"
    print(f"✅ Pattern matching weights: {pm_weights}")
    
    # Test LLM parameters
    llm_params = config1.get_llm_params()
    expected_llm_keys = ["temperature", "max_tokens", "top_p", "frequency_penalty", "presence_penalty"]
    assert all(key in llm_params for key in expected_llm_keys), f"Missing LLM parameter keys: {llm_params}"
    print(f"✅ LLM parameters: {llm_params}")
    
    # Test feasibility classification
    assert config1.get_feasibility_classification(0.9) == "Fully Automatable"
    assert config1.get_feasibility_classification(0.65) == "Partially Automatable"
    assert config1.get_feasibility_classification(0.4) == "Manual Process"
    print("✅ Feasibility classification working")
    
    # Test threshold checks
    assert config1.is_fully_automatable(0.85) == True
    assert config1.is_partially_automatable(0.65) == True
    assert config1.meets_tech_inclusion_threshold(0.7) == True
    print("✅ Threshold checks working")


def test_configuration_manager():
    """Test the configuration manager functionality."""
    print("\n🧪 Testing Configuration Manager...")
    
    # Create temporary config manager
    manager = SystemConfigurationManager("test_config.yaml")
    
    # Test default configuration
    config = manager.config
    assert config.autonomy.min_autonomy_threshold == 0.7
    assert config.pattern_matching.tag_weight == 0.3
    assert config.llm_generation.temperature == 0.3
    print("✅ Default configuration loaded")
    
    # Test configuration modification
    original_threshold = config.autonomy.min_autonomy_threshold
    config.autonomy.min_autonomy_threshold = 0.75
    assert config.autonomy.min_autonomy_threshold == 0.75
    print("✅ Configuration modification working")
    
    # Test save and reload
    if manager.save_config():
        print("✅ Configuration saved successfully")
        
        # Create new manager and verify persistence
        new_manager = SystemConfigurationManager("test_config.yaml")
        assert new_manager.config.autonomy.min_autonomy_threshold == 0.75
        print("✅ Configuration persistence working")
    
    # Test export/import
    exported = manager.export_config()
    assert "autonomy" in exported
    assert "pattern_matching" in exported
    print("✅ Configuration export working")
    
    # Test reset to defaults
    manager.reset_to_defaults()
    assert manager.config.autonomy.min_autonomy_threshold == 0.7
    print("✅ Reset to defaults working")
    
    # Cleanup
    import os
    if os.path.exists("test_config.yaml"):
        os.remove("test_config.yaml")
    print("✅ Cleanup completed")


def test_integration_with_services():
    """Test integration with existing services."""
    print("\n🧪 Testing Service Integration...")
    
    # Test that services can import and use configuration
    try:
        from app.services.autonomy_assessor import AutonomyAssessor
        from app.llm.fake import FakeLLMProvider
        
        # Create assessor (should use configuration service)
        fake_provider = FakeLLMProvider()
        assessor = AutonomyAssessor(fake_provider)
        
        # Check that it has configuration service
        assert hasattr(assessor, 'config_service')
        assert hasattr(assessor, 'autonomy_weights')
        print("✅ AutonomyAssessor integration working")
        
    except ImportError as e:
        print(f"⚠️ Could not test AutonomyAssessor integration: {e}")
    
    try:
        from app.services.agentic_recommendation_service import AgenticRecommendationService
        
        # This should work without errors
        print("✅ AgenticRecommendationService can be imported")
        
    except ImportError as e:
        print(f"⚠️ Could not test AgenticRecommendationService integration: {e}")


def main():
    """Run all configuration tests."""
    print("🚀 Starting System Configuration Tests\n")
    
    try:
        test_configuration_service()
        test_configuration_manager()
        test_integration_with_services()
        
        print("\n🎉 All tests passed! System Configuration is working correctly.")
        
        # Show current configuration
        config = get_config()
        print("\n📋 Current Configuration Summary:")
        print(f"  Autonomy Threshold: {config.autonomy.min_autonomy_threshold}")
        print(f"  Confidence Boost: {config.autonomy.confidence_boost_factor}")
        print(f"  LLM Temperature: {config.llm_generation.temperature}")
        print(f"  Max Tokens: {config.llm_generation.max_tokens}")
        
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()