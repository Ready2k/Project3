#!/usr/bin/env python3
"""Test script to verify enhanced agentic infrastructure diagram generation."""

import asyncio
import sys
from pathlib import Path

# Add the project root to the path
sys.path.insert(0, str(Path(__file__).parent))

from streamlit_app import build_infrastructure_diagram

async def test_agentic_infrastructure_diagram():
    """Test that infrastructure diagram properly handles agentic AI systems."""
    
    print("🧪 Testing Enhanced Agentic Infrastructure Diagram")
    print("=" * 60)
    
    # Test case matching your example
    test_recommendations = [{
        'pattern_id': 'APAT-001',
        'feasibility': 'Highly Automatable',
        'confidence': 0.95,
        'reasoning': 'This requirement involves complex multi-agent coordination for autonomous decision-making with minimal human oversight.',
        'tech_stack': ['Microsoft Semantic Kernel', 'Neo4j', 'Drools', 'Salesforce API integration', 'LangChain'],
        'agent_roles': [
            {'name': 'CoordinatorAgent', 'responsibility': 'Orchestrate multi-agent workflows'},
            {'name': 'DecisionAgent', 'responsibility': 'Make autonomous decisions using rules'},
            {'name': 'IntegrationAgent', 'responsibility': 'Handle Salesforce API interactions'}
        ]
    }]
    
    test_requirement = "Automate complex customer service workflows with multi-agent AI coordination"
    
    # Enhanced tech stack matching your example
    enhanced_tech_stack = [
        'Microsoft Semantic Kernel',
        'Neo4j', 
        'Drools',
        'Salesforce API integration',
        'LangChain',
        'LangChain multi-agent framework',
        'CrewAI',
        'Pega workflow orchestration',
        'GPT-4o for reasoning and communication',
        'Prolog'
    ]
    
    architecture_explanation = "Multi-agent system using LangChain orchestration with Neo4j for knowledge graphs, Drools for business rules, and Semantic Kernel for AI coordination."
    
    print("📋 Test Data:")
    print(f"  - Requirement: {test_requirement}")
    print(f"  - Pattern: {test_recommendations[0]['pattern_id']}")
    print(f"  - Enhanced Tech Stack: {len(enhanced_tech_stack)} agentic technologies")
    print(f"  - Agent Roles: {len(test_recommendations[0]['agent_roles'])} agents")
    print()
    
    print("🔍 Testing Infrastructure Diagram Generation...")
    
    try:
        # Call the enhanced infrastructure diagram function
        result = await build_infrastructure_diagram(
            requirement=test_requirement,
            recommendations=test_recommendations,
            enhanced_tech_stack=enhanced_tech_stack,
            architecture_explanation=architecture_explanation
        )
        
        print("✅ Infrastructure diagram generated successfully!")
        print()
        
        # Analyze the result for agentic components
        result_str = str(result).lower()
        
        print("🔍 Analyzing Agentic Component Coverage:")
        
        # Check for agentic technologies
        agentic_checks = {
            'LangChain': 'langchain' in result_str,
            'CrewAI': 'crewai' in result_str,
            'Semantic Kernel': 'semantic' in result_str or 'kernel' in result_str,
            'Neo4j': 'neo4j' in result_str,
            'Drools': 'drools' in result_str,
            'GPT-4o': 'gpt' in result_str or 'openai' in result_str,
            'Salesforce API': 'salesforce' in result_str,
            'Pega': 'pega' in result_str,
            'Agent Architecture': 'agent' in result_str or 'orchestrat' in result_str
        }
        
        covered_count = sum(agentic_checks.values())
        total_count = len(agentic_checks)
        
        print(f"📊 Agentic Technology Coverage: {covered_count}/{total_count}")
        
        for tech, covered in agentic_checks.items():
            status = "✅" if covered else "❌"
            print(f"  {status} {tech}")
        
        print()
        
        # Check diagram structure
        if isinstance(result, dict):
            print("🏗️ Diagram Structure Analysis:")
            
            structure_checks = {
                'Has Title': 'title' in result,
                'Has Clusters': 'clusters' in result and len(result.get('clusters', [])) > 0,
                'Has Nodes': 'nodes' in result and len(result.get('nodes', [])) > 0,
                'Has Edges': 'edges' in result and len(result.get('edges', [])) > 0
            }
            
            for check, passed in structure_checks.items():
                status = "✅" if passed else "❌"
                print(f"  {status} {check}")
            
            # Show cluster details
            if 'clusters' in result:
                print(f"\n📦 Clusters Found: {len(result['clusters'])}")
                for i, cluster in enumerate(result['clusters']):
                    provider = cluster.get('provider', 'unknown')
                    name = cluster.get('name', 'unnamed')
                    node_count = len(cluster.get('nodes', []))
                    print(f"  {i+1}. {name} ({provider}) - {node_count} nodes")
            
            # Show external nodes
            if 'nodes' in result:
                print(f"\n🔗 External Services: {len(result['nodes'])}")
                for node in result['nodes']:
                    label = node.get('label', 'unlabeled')
                    provider = node.get('provider', 'unknown')
                    print(f"  - {label} ({provider})")
        
        print()
        
        # Overall assessment
        if covered_count >= 6:
            print("🎉 EXCELLENT: Infrastructure diagram shows strong agentic technology integration!")
        elif covered_count >= 4:
            print("✅ GOOD: Infrastructure diagram includes key agentic components")
        elif covered_count >= 2:
            print("⚠️ FAIR: Infrastructure diagram has some agentic elements but could be improved")
        else:
            print("❌ POOR: Infrastructure diagram lacks agentic technology representation")
        
        print()
        print("📋 Generated Infrastructure Specification:")
        print("=" * 40)
        
        if isinstance(result, dict):
            import json
            print(json.dumps(result, indent=2))
        else:
            print(result)
            
    except Exception as e:
        print(f"❌ Infrastructure diagram generation failed: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print()
    print("🎯 Summary:")
    print("Enhanced infrastructure diagram should now:")
    print("  - Detect agentic AI systems from tech stack")
    print("  - Focus on agent orchestration platforms")
    print("  - Include AI model services and APIs")
    print("  - Show agent communication infrastructure")
    print("  - Represent workflow and rule engines")
    print("  - Display knowledge bases and vector databases")

if __name__ == "__main__":
    asyncio.run(test_agentic_infrastructure_diagram())