#!/usr/bin/env python3
"""Test script to verify agentic component mapping works."""

import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from app.diagrams.infrastructure import InfrastructureDiagramGenerator

def test_agentic_component_mapping():
    """Test that agentic component types are properly mapped."""
    
    print("🧪 Testing Agentic Component Mapping")
    print("=" * 50)
    
    # Create the generator
    generator = InfrastructureDiagramGenerator()
    
    print("📋 Component Mapping Analysis:")
    print()
    
    # Check if agentic provider exists
    if "agentic" in generator.component_mapping:
        print("✅ Agentic provider found in component mapping")
        
        agentic_components = generator.component_mapping["agentic"]
        print(f"📊 Agentic components available: {len(agentic_components)}")
        print()
        
        # Test each agentic component type
        test_components = [
            "langchain_orchestrator",
            "crewai_coordinator", 
            "agent_memory",
            "semantic_kernel",
            "openai_api",
            "claude_api",
            "assistants_api",
            "vector_db",
            "knowledge_base",
            "rule_engine",
            "workflow_engine",
            "salesforce_api"
        ]
        
        print("🔍 Testing Component Type Recognition:")
        for component_type in test_components:
            if component_type in agentic_components:
                component_class = agentic_components[component_type]
                print(f"  ✅ {component_type} → {component_class.__name__}")
            else:
                print(f"  ❌ {component_type} → NOT FOUND")
        
        print()
        
        # Test the _get_component_class method
        print("🔧 Testing Component Class Resolution:")
        for component_type in test_components:
            component_class = generator._get_component_class("agentic", component_type)
            if component_class:
                print(f"  ✅ agentic.{component_type} → {component_class}")
            else:
                print(f"  ❌ agentic.{component_type} → None")
        
    else:
        print("❌ Agentic provider NOT found in component mapping")
        print("Available providers:", list(generator.component_mapping.keys()))
    
    print()
    
    # Test with a sample agentic diagram spec
    print("🧪 Testing Sample Agentic Diagram Spec:")
    
    sample_spec = {
        "title": "Test Agentic Infrastructure",
        "clusters": [
            {
                "provider": "agentic",
                "name": "AI Agent Orchestration",
                "nodes": [
                    {"id": "lc_orch", "type": "langchain_orchestrator", "label": "LangChain Orchestrator"},
                    {"id": "cai_coor", "type": "crewai_coordinator", "label": "CrewAI Coordinator"}
                ]
            }
        ],
        "nodes": [
            {"id": "gpt4o", "type": "openai_api", "provider": "agentic", "label": "GPT-4o API"}
        ],
        "edges": [
            ["lc_orch", "gpt4o", "Model Service Invocation"]
        ]
    }
    
    try:
        # Generate Python code (don't execute, just test generation)
        python_code = generator._generate_python_code(sample_spec)
        
        print("✅ Python code generation successful!")
        print()
        print("📝 Generated Code Preview:")
        print("=" * 30)
        
        # Show first 20 lines
        lines = python_code.split('\n')
        for i, line in enumerate(lines[:20]):
            print(f"{i+1:2d}: {line}")
        
        if len(lines) > 20:
            print(f"... ({len(lines) - 20} more lines)")
        
        # Check for agentic components in the code
        print()
        print("🔍 Agentic Components in Generated Code:")
        
        agentic_found = []
        for component_type in test_components:
            if component_type in python_code:
                agentic_found.append(component_type)
        
        if agentic_found:
            print(f"  ✅ Found {len(agentic_found)} agentic components:")
            for comp in agentic_found:
                print(f"    - {comp}")
        else:
            print("  ⚠️ No agentic components found in generated code")
        
    except Exception as e:
        print(f"❌ Python code generation failed: {e}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🎯 Summary:")
    print("Agentic component mapping should now support:")
    print("  - AI Agent Orchestration (LangChain, CrewAI, Semantic Kernel)")
    print("  - AI Model Services (OpenAI, Claude, Assistants API)")
    print("  - Knowledge & Data (Vector DBs, Knowledge Bases)")
    print("  - Rules & Workflow (Rule Engines, Workflow Engines)")
    print("  - Integration (External APIs)")

if __name__ == "__main__":
    test_agentic_component_mapping()