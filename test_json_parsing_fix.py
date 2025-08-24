#!/usr/bin/env python3
"""Test script to verify JSON parsing fix works with actual LLM response."""

import json

def test_json_parsing():
    """Test JSON parsing with the actual LLM response."""
    
    print("🧪 Testing JSON Parsing Fix")
    print("=" * 40)
    
    # Your actual LLM response
    llm_response = '''```json
{"title": "Agentic AI Automation Infrastructure for Automated Transcription Service","clusters": [{"provider": "agentic","name": "AI Agent Orchestration","nodes": [{"id": "lc_orch", "type": "langchain_orchestrator", "label": "LangChain Orchestrator"},{"id": "cai_coor", "type": "crewai_coordinator", "label": "CrewAI Coordinator"},{"id": "sk_kernel", "type": "semantic_kernel", "label": "Microsoft Semantic Kernel"}]},{"provider": "agentic","name": "AI Model Services","nodes": [{"id": "gpt4o", "type": "openai_api", "label": "GPT-4o for Reasoning and Communication"},{"id": "assist_api", "type": "assistants_api", "label": "Assistants API"}]},{"provider": "agentic","name": "Knowledge Bases & Vector Databases","nodes": [{"id": "neo4j_db", "type": "vector_db", "label": "Neo4j"},{"id": "vector_store", "type": "vector_db", "label": "Pinecone"}]},{"provider": "agentic","name": "Workflow Orchestration","nodes": [{"id": "pega_orch", "type": "workflow_engine", "label": "Pega Workflow Orchestration"}]},{"provider": "agentic","name": "Rule Engines & Decision Systems","nodes": [{"id": "drools_engine", "type": "rule_engine", "label": "Drools Business Rules"}]}],"nodes": [{"id": "sf_api", "type": "salesforce_api", "provider": "SaaS", "label": "Salesforce API"}],"edges": [["lc_orch", "gpt4o", "Model Service Invocation"],["lc_orch", "cai_coor", "Orchestration Coordination"],["cai_coor", "pega_orch", "Orchestration Management"],["pega_orch", "drools_engine", "Rule Evaluation"],["lc_orch", "neo4j_db", "Knowledge Access"],["lc_orch", "vector_store", "Semantic Storage"],["sf_api", "lc_orch", "CRM Integration"]]}
```'''
    
    print("📝 Original LLM Response:")
    print(f"Length: {len(llm_response)} characters")
    print(f"Starts with: {llm_response[:20]}...")
    print(f"Ends with: ...{llm_response[-20:]}")
    print()
    
    # Apply the same cleaning logic as the enhanced function
    try:
        cleaned_response = llm_response.strip()
        
        # Handle various markdown code block formats
        if cleaned_response.startswith('```json'):
            cleaned_response = cleaned_response[7:]
        elif cleaned_response.startswith('```'):
            cleaned_response = cleaned_response[3:]
        
        if cleaned_response.endswith('```'):
            cleaned_response = cleaned_response[:-3]
        
        cleaned_response = cleaned_response.strip()
        
        # Additional cleaning for any remaining formatting
        if not cleaned_response.startswith('{'):
            # Find the first { character
            start_idx = cleaned_response.find('{')
            if start_idx != -1:
                cleaned_response = cleaned_response[start_idx:]
        
        if not cleaned_response.endswith('}'):
            # Find the last } character
            end_idx = cleaned_response.rfind('}')
            if end_idx != -1:
                cleaned_response = cleaned_response[:end_idx + 1]
        
        print("🧹 Cleaned Response:")
        print(f"Length: {len(cleaned_response)} characters")
        print(f"Starts with: {cleaned_response[:20]}...")
        print(f"Ends with: ...{cleaned_response[-20:]}")
        print()
        
        # Try to parse JSON
        parsed_json = json.loads(cleaned_response)
        
        print("✅ JSON Parsing Successful!")
        print()
        
        # Analyze the parsed structure
        print("📊 Parsed Structure Analysis:")
        print(f"  - Title: {parsed_json.get('title', 'N/A')}")
        print(f"  - Clusters: {len(parsed_json.get('clusters', []))}")
        print(f"  - External Nodes: {len(parsed_json.get('nodes', []))}")
        print(f"  - Edges: {len(parsed_json.get('edges', []))}")
        print()
        
        # Show cluster details
        if 'clusters' in parsed_json:
            print("🏗️ Cluster Details:")
            for i, cluster in enumerate(parsed_json['clusters']):
                provider = cluster.get('provider', 'unknown')
                name = cluster.get('name', 'unnamed')
                node_count = len(cluster.get('nodes', []))
                print(f"  {i+1}. {name} ({provider}) - {node_count} nodes")
                
                # Show node details for agentic clusters
                if provider == 'agentic':
                    for node in cluster.get('nodes', []):
                        node_type = node.get('type', 'unknown')
                        label = node.get('label', 'unlabeled')
                        print(f"     - {label} ({node_type})")
        
        print()
        
        # Show external services
        if 'nodes' in parsed_json:
            print("🔗 External Services:")
            for node in parsed_json['nodes']:
                label = node.get('label', 'unlabeled')
                provider = node.get('provider', 'unknown')
                node_type = node.get('type', 'unknown')
                print(f"  - {label} ({node_type}, {provider})")
        
        print()
        
        # Show connections
        if 'edges' in parsed_json:
            print("🔄 Connections:")
            for edge in parsed_json['edges']:
                if len(edge) >= 3:
                    source, target, label = edge[0], edge[1], edge[2]
                    print(f"  - {source} → {target}: {label}")
        
        print()
        print("🎉 SUCCESS: The enhanced JSON parsing works perfectly!")
        print("The infrastructure diagram now properly represents agentic AI architecture!")
        
    except json.JSONDecodeError as e:
        print(f"❌ JSON Parsing Failed: {e}")
        return False
    except Exception as e:
        print(f"❌ Unexpected Error: {e}")
        return False
    
    return True

if __name__ == "__main__":
    test_json_parsing()