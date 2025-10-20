#!/usr/bin/env python3
"""
Fix duplicate pattern names by generating unique, descriptive names based on pattern content.
"""

import json
import os
import re
from pathlib import Path
from typing import Dict, Any

def extract_domain_from_description(description: str) -> str:
    """Extract the main domain/use case from the pattern description."""
    # Common patterns to identify domains
    domain_patterns = {
        'investment': ['investment', 'portfolio', 'rebalancing', 'trading', 'financial'],
        'customer_support': ['customer support', 'customer service', 'crm', 'inquiries', 'helpdesk'],
        'data_processing': ['data processing', 'analytics', 'etl', 'data pipeline'],
        'workflow': ['workflow', 'process automation', 'business process'],
        'monitoring': ['monitoring', 'alerting', 'observability', 'metrics'],
        'content': ['content', 'document', 'text processing', 'nlp']
    }
    
    description_lower = description.lower()
    
    for domain, keywords in domain_patterns.items():
        if any(keyword in description_lower for keyword in keywords):
            return domain
    
    # Fallback: try to extract from first sentence
    first_sentence = description.split('.')[0].lower()
    if 'investment' in first_sentence or 'portfolio' in first_sentence:
        return 'investment'
    elif 'customer' in first_sentence or 'support' in first_sentence:
        return 'customer_support'
    elif 'data' in first_sentence:
        return 'data_processing'
    
    return 'general'

def generate_unique_name(pattern: Dict[str, Any]) -> str:
    """Generate a unique, descriptive name for the pattern."""
    pattern_id = pattern['pattern_id']
    description = pattern.get('description', '')
    domain = pattern.get('domain', '')
    pattern_type = pattern.get('pattern_type', [])
    session_id = pattern.get('metadata', {}).get('creation_session', '')
    
    # Extract domain from description if not explicitly set
    if not domain or domain in ['None', 'user_management', 'data_processing']:
        domain = extract_domain_from_description(description)
    
    # Determine architecture type
    if 'multi_agent_system' in pattern_type or 'hierarchical_agents' in pattern_type:
        arch_type = 'Multi-Agent'
    elif 'agentic_reasoning' in pattern_type:
        arch_type = 'Agentic Reasoning'
    elif 'workflow_automation' in pattern_type:
        arch_type = 'Workflow Automation'
    else:
        arch_type = 'Autonomous'
    
    # Create domain-specific names
    domain_names = {
        'investment': f'{arch_type} Investment Portfolio System',
        'customer_support': f'{arch_type} Customer Support System', 
        'data_processing': f'{arch_type} Data Processing System',
        'workflow': f'{arch_type} Workflow System',
        'monitoring': f'{arch_type} Monitoring System',
        'content': f'{arch_type} Content Processing System',
        'general': f'{arch_type} Solution System'
    }
    
    base_name = domain_names.get(domain, f'{arch_type} {domain.title()} System')
    
    # Add agent count if it's a multi-agent system
    if 'Multi-Agent' in arch_type and 'specialized agents' in description:
        # Extract agent count from description
        agent_match = re.search(r'(\d+)\s+specialized agents', description)
        if agent_match:
            agent_count = agent_match.group(1)
            base_name = f'{agent_count}-Agent {domain.title().replace("_", " ")} System'
    
    # Add unique identifier for patterns that might still conflict
    # Use last 4 characters of pattern ID for uniqueness
    unique_suffix = pattern_id[-4:]
    
    # For customer support systems, add more specific differentiation
    if domain == 'customer_support' and 'Multi-Agent' in arch_type:
        if 'crm' in description.lower():
            base_name = base_name.replace('Customer Support', 'CRM-Integrated Support')
        elif 'sentiment' in description.lower():
            base_name = base_name.replace('Customer Support', 'AI-Sentiment Support')
        elif 'analytics' in description.lower():
            base_name = base_name.replace('Customer Support', 'Analytics-Driven Support')
        
        # Always add unique suffix for customer support to avoid conflicts
        base_name = f'{base_name} (v{unique_suffix})'
    
    return base_name

def fix_pattern_names():
    """Fix duplicate pattern names in all pattern files."""
    patterns_dir = Path('data/patterns')
    
    if not patterns_dir.exists():
        print(f"Patterns directory not found: {patterns_dir}")
        return
    
    updated_count = 0
    name_conflicts = {}
    
    # First pass: identify all current names
    for pattern_file in patterns_dir.glob('*.json'):
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern = json.load(f)
            
            current_name = pattern.get('name', '')
            if current_name in name_conflicts:
                name_conflicts[current_name].append(pattern_file)
            else:
                name_conflicts[current_name] = [pattern_file]
                
        except Exception as e:
            print(f"Error reading {pattern_file}: {e}")
    
    # Report conflicts
    print("Pattern Name Analysis:")
    print("=" * 50)
    
    for name, files in name_conflicts.items():
        if len(files) > 1:
            print(f"DUPLICATE: '{name}' used by {len(files)} patterns:")
            for file in files:
                print(f"  - {file.name}")
        else:
            print(f"UNIQUE: '{name}' - {files[0].name}")
    
    print("\nFixing duplicate names...")
    print("=" * 50)
    
    # Second pass: fix duplicates
    for pattern_file in patterns_dir.glob('*.json'):
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern = json.load(f)
            
            current_name = pattern.get('name', '')
            
            # Only fix if it's a duplicate or generic name
            if (len(name_conflicts.get(current_name, [])) > 1 or 
                current_name == 'Multi-Agent Coordinator_Based System' or
                'Custom Agentic Solution - None' in current_name):
                
                new_name = generate_unique_name(pattern)
                old_name = pattern['name']
                pattern['name'] = new_name
                
                # Add metadata about the name change
                if 'metadata' not in pattern:
                    pattern['metadata'] = {}
                pattern['metadata']['name_updated'] = True
                pattern['metadata']['original_name'] = old_name
                
                # Write back to file
                with open(pattern_file, 'w', encoding='utf-8') as f:
                    json.dump(pattern, f, indent=2, ensure_ascii=False)
                
                print(f"✅ {pattern_file.name}: '{old_name}' → '{new_name}'")
                updated_count += 1
            else:
                print(f"⏭️  {pattern_file.name}: '{current_name}' (no change needed)")
                
        except Exception as e:
            print(f"❌ Error processing {pattern_file}: {e}")
    
    print(f"\nCompleted! Updated {updated_count} pattern names.")

if __name__ == '__main__':
    fix_pattern_names()