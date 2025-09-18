#!/usr/bin/env python3
"""
Test UI Service Integration

This script tests that the UI modules can properly integrate with the service registry
after the import pattern updates.
"""

import sys
import os
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def test_ui_service_integration():
    """Test that UI modules can integrate with the service registry."""
    
    print("🧪 Testing UI Service Integration...")
    
    # Import and set up the service registry
    from app.core.registry import get_registry
    from app.core.services.logger_service import LoggerService
    from app.core.services.config_service import ConfigService
    
    registry = get_registry()
    
    # Register required services
    print("📝 Registering core services...")
    
    # Register logger service with mock config
    logger_config = {"level": "INFO", "format": "simple"}
    logger_service = LoggerService(logger_config)
    registry.register_singleton('logger', logger_service)
    
    # Register config service with mock config
    config_data = {"test": True}
    config_service = ConfigService(config_data)
    registry.register_singleton('config_service', config_service)
    
    # Register a mock API service for testing
    class MockAPIService:
        def create_llm_provider(self, config, session_id):
            return MockLLMProvider()
    
    class MockLLMProvider:
        async def generate(self, prompt, purpose="test"):
            return "Mock LLM response"
    
    registry.register_singleton('api_service', MockAPIService())
    
    print("✅ Core services registered")
    
    # Test importing UI modules
    ui_modules_to_test = [
        'app.ui.mermaid_diagrams',
        'app.ui.analysis_display', 
        'app.ui.agent_formatter',
        'app.ui.enhanced_pattern_management',
        'app.ui.api_client',
        'app.ui.schema_management',
        'app.ui.system_configuration',
        'app.ui.components.results_display',
        'app.ui.components.provider_config',
        'app.ui.components.session_management'
    ]
    
    successful_imports = []
    failed_imports = []
    
    for module_name in ui_modules_to_test:
        try:
            print(f"📦 Testing import: {module_name}")
            __import__(module_name)
            successful_imports.append(module_name)
            print(f"✅ Successfully imported: {module_name}")
        except Exception as e:
            failed_imports.append((module_name, str(e)))
            print(f"❌ Failed to import {module_name}: {e}")
    
    # Test service resolution in UI modules
    print("\n🔍 Testing service resolution...")
    
    try:
        from app.utils.imports import require_service, optional_service
        
        # Test required service
        logger = require_service('logger', context="ui_test")
        print("✅ Successfully resolved logger service")
        
        # Test optional service
        optional_svc = optional_service('non_existent_service', default="fallback")
        if optional_svc == "fallback":
            print("✅ Optional service fallback working correctly")
        
        # Test service usage
        logger.info("UI service integration test completed")
        print("✅ Service usage working correctly")
        
    except Exception as e:
        print(f"❌ Service resolution test failed: {e}")
        failed_imports.append(("service_resolution", str(e)))
    
    # Test specific UI functionality
    print("\n🎨 Testing UI component functionality...")
    
    try:
        # Test MermaidDiagramGenerator
        from app.ui.mermaid_diagrams import MermaidDiagramGenerator
        generator = MermaidDiagramGenerator()
        
        # Test sanitize method
        sanitized = generator.sanitize_label("Test Label 🚀")
        if sanitized:
            print("✅ MermaidDiagramGenerator.sanitize_label working")
        
        # Test validation
        is_valid, error = generator.validate_mermaid_syntax("flowchart TD\n    A --> B")
        if is_valid:
            print("✅ MermaidDiagramGenerator.validate_mermaid_syntax working")
        
    except Exception as e:
        print(f"❌ MermaidDiagramGenerator test failed: {e}")
        failed_imports.append(("mermaid_generator", str(e)))
    
    try:
        # Test AgentDataFormatter
        from app.ui.agent_formatter import AgentDataFormatter
        formatter = AgentDataFormatter()
        
        # Test empty system formatting
        empty_display = formatter.format_agent_system(None, [], {})
        if not empty_display.has_agents:
            print("✅ AgentDataFormatter.format_agent_system working")
        
    except Exception as e:
        print(f"❌ AgentDataFormatter test failed: {e}")
        failed_imports.append(("agent_formatter", str(e)))
    
    try:
        # Test API client
        from app.ui.api_client import AAA_APIClient
        client = AAA_APIClient()
        
        if client.base_url:
            print("✅ AAA_APIClient initialization working")
        
    except Exception as e:
        print(f"❌ AAA_APIClient test failed: {e}")
        failed_imports.append(("api_client", str(e)))
    
    # Print summary
    print(f"\n📊 Test Summary:")
    print(f"✅ Successful imports: {len(successful_imports)}")
    print(f"❌ Failed imports: {len(failed_imports)}")
    
    if failed_imports:
        print(f"\n❌ Failed imports details:")
        for module, error in failed_imports:
            print(f"  • {module}: {error}")
        return False
    else:
        print(f"\n🎉 All UI modules successfully integrated with service registry!")
        return True

if __name__ == "__main__":
    success = test_ui_service_integration()
    sys.exit(0 if success else 1)