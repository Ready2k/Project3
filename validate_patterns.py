#!/usr/bin/env python3
"""
Pattern validation script to check all patterns against the schema configuration.
"""

import json
import os
from pathlib import Path

def validate_patterns():
    """Validate all patterns in the data/patterns directory."""
    
    # Load schema configuration
    schema_config_path = Path('app/pattern/schema_config.json')
    if not schema_config_path.exists():
        print("❌ Schema configuration not found at app/pattern/schema_config.json")
        return False
    
    with open(schema_config_path, 'r') as f:
        schema_config = json.load(f)
    
    # Get all pattern files
    patterns_dir = Path('data/patterns')
    if not patterns_dir.exists():
        print("❌ Patterns directory not found at data/patterns")
        return False
    
    pattern_files = list(patterns_dir.glob('*.json'))
    if not pattern_files:
        print("❌ No pattern files found in data/patterns")
        return False
    
    print(f"🔍 Validating {len(pattern_files)} pattern files...")
    print()
    
    all_valid = True
    
    for pattern_file in sorted(pattern_files):
        try:
            with open(pattern_file, 'r') as f:
                pattern = json.load(f)
            
            pattern_id = pattern.get('pattern_id', pattern_file.stem)
            errors = []
            
            # Validate learning_mechanisms
            if 'learning_mechanisms' in pattern:
                learning_mechanisms = pattern['learning_mechanisms']
                valid_learning = schema_config['schema_enums']['learning_mechanisms']['values']
                invalid_learning = [lm for lm in learning_mechanisms if lm not in valid_learning]
                if invalid_learning:
                    errors.append(f"Invalid learning_mechanisms: {invalid_learning}")
            
            # Validate agent_architecture
            if 'agent_architecture' in pattern:
                agent_arch = pattern['agent_architecture']
                valid_arch = schema_config['schema_enums']['agent_architecture']['values']
                if agent_arch not in valid_arch:
                    errors.append(f"Invalid agent_architecture: '{agent_arch}'")
            
            # Check required fields
            if 'exception_handling_strategy' not in pattern:
                errors.append("Missing required field: exception_handling_strategy")
            
            # Validate reasoning_types
            if 'reasoning_types' in pattern:
                reasoning_types = pattern['reasoning_types']
                valid_reasoning = schema_config['schema_enums']['reasoning_types']['values']
                invalid_reasoning = [rt for rt in reasoning_types if rt not in valid_reasoning]
                if invalid_reasoning:
                    errors.append(f"Invalid reasoning_types: {invalid_reasoning}")
            
            # Validate self_monitoring_capabilities
            if 'self_monitoring_capabilities' in pattern:
                monitoring_caps = pattern['self_monitoring_capabilities']
                valid_monitoring = schema_config['schema_enums']['self_monitoring_capabilities']['values']
                invalid_monitoring = [mc for mc in monitoring_caps if mc not in valid_monitoring]
                if invalid_monitoring:
                    errors.append(f"Invalid self_monitoring_capabilities: {invalid_monitoring}")
            
            # Check for common invalid values that might slip through
            common_invalid_values = {
                'learning_mechanisms': ['inter_agent_learning', 'system_optimization', 'performance_adaptation'],
                'agent_architecture': ['coordinator_based'],
                'self_monitoring_capabilities': ['system_health_monitoring'],
                'reasoning_types': ['collaborative_reasoning']  # Should be 'collaborative'
            }
            
            for field, invalid_vals in common_invalid_values.items():
                if field in pattern:
                    field_values = pattern[field] if isinstance(pattern[field], list) else [pattern[field]]
                    found_invalid = [val for val in field_values if val in invalid_vals]
                    if found_invalid:
                        errors.append(f"Common invalid {field} values detected: {found_invalid}")
            
            if errors:
                print(f"❌ {pattern_id}:")
                for error in errors:
                    print(f"   • {error}")
                all_valid = False
            else:
                print(f"✅ {pattern_id}")
                
        except json.JSONDecodeError as e:
            print(f"❌ {pattern_file.name}: Invalid JSON - {e}")
            all_valid = False
        except Exception as e:
            print(f"❌ {pattern_file.name}: Error - {e}")
            all_valid = False
    
    print()
    if all_valid:
        print("🎉 All patterns are valid!")
    else:
        print("⚠️  Some patterns have validation errors.")
    
    return all_valid

if __name__ == "__main__":
    validate_patterns()