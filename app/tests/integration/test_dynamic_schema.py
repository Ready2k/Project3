#!/usr/bin/env python3
"""
Test script for dynamic schema functionality.
"""

import sys
sys.path.append('app')

from pattern.dynamic_schema_loader import dynamic_schema_loader
import json

def test_dynamic_schema():
    """Test the dynamic schema functionality."""
    print("🧪 Testing Dynamic Schema Functionality")
    print("=" * 50)
    
    # Test 1: Load configuration
    print("\n1. Loading configuration...")
    try:
        config = dynamic_schema_loader.load_config()
        print(f"✅ Loaded config with {len(config.get('schema_enums', {}))} enums")
        
        # Show available enums
        for enum_name, enum_config in config.get('schema_enums', {}).items():
            values_count = len(enum_config.get('values', []))
            extensible = "✅" if enum_config.get('user_extensible', False) else "❌"
            print(f"   - {enum_name}: {values_count} values, extensible: {extensible}")
            
    except Exception as e:
        print(f"❌ Failed to load config: {e}")
        return False
    
    # Test 2: Generate dynamic schema
    print("\n2. Generating dynamic schema...")
    try:
        schema = dynamic_schema_loader.generate_dynamic_schema()
        print(f"✅ Generated schema with {len(schema.get('properties', {}))} properties")
        
        # Check specific enum fields
        properties = schema.get('properties', {})
        enum_fields = ['reasoning_types', 'self_monitoring_capabilities', 'learning_mechanisms']
        
        for field in enum_fields:
            if field in properties:
                prop = properties[field]
                if prop.get('type') == 'array' and 'items' in prop and 'enum' in prop['items']:
                    enum_values = prop['items']['enum']
                    print(f"   - {field}: {len(enum_values)} allowed values")
                    print(f"     Values: {', '.join(enum_values[:3])}{'...' if len(enum_values) > 3 else ''}")
                    
    except Exception as e:
        print(f"❌ Failed to generate schema: {e}")
        return False
    
    # Test 3: Validate enum values
    print("\n3. Testing enum validation...")
    test_cases = [
        ('reasoning_types', 'logical', True),
        ('reasoning_types', 'collaborative', True),  # Should be allowed now
        ('reasoning_types', 'invalid_type', False),
        ('self_monitoring_capabilities', 'performance_tracking', True),
        ('self_monitoring_capabilities', 'response_time_monitoring', True),  # Should be allowed now
    ]
    
    for enum_name, value, expected in test_cases:
        result = dynamic_schema_loader.validate_enum_value(enum_name, value)
        status = "✅" if result == expected else "❌"
        print(f"   {status} {enum_name}.{value} -> {result} (expected {expected})")
    
    # Test 4: Add new enum value
    print("\n4. Testing enum value addition...")
    try:
        success = dynamic_schema_loader.add_enum_value('reasoning_types', 'test_reasoning')
        if success:
            print("✅ Successfully added 'test_reasoning' to reasoning_types")
            
            # Verify it's in the list
            values = dynamic_schema_loader.get_enum_values('reasoning_types')
            if 'test_reasoning' in values:
                print("✅ New value confirmed in enum list")
            else:
                print("❌ New value not found in enum list")
        else:
            print("❌ Failed to add new enum value")
            
    except Exception as e:
        print(f"❌ Error adding enum value: {e}")
    
    print("\n🎉 Dynamic schema testing completed!")
    return True

def test_pattern_validation():
    """Test pattern validation with dynamic schema."""
    print("\n🧪 Testing Pattern Validation with Dynamic Schema")
    print("=" * 50)
    
    try:
        from pattern.loader import PatternLoader
        
        # Create a test pattern with new enum values
        test_pattern = {
            "pattern_id": "APAT-999",
            "name": "Test Pattern",
            "description": "Test pattern for dynamic schema validation",
            "feasibility": "Fully Automatable",
            "pattern_type": ["test_pattern"],
            "input_requirements": ["test_input"],
            "tech_stack": ["test_tech"],
            "related_patterns": [],
            "confidence_score": 0.9,
            "constraints": {},
            "autonomy_level": 0.9,
            "reasoning_types": ["logical", "collaborative"],  # collaborative should now be allowed
            "decision_boundaries": {
                "autonomous_decisions": ["test_decision"],
                "escalation_triggers": ["test_trigger"],
                "decision_authority_level": "medium"
            },
            "exception_handling_strategy": {
                "autonomous_resolution_approaches": ["test_approach"],
                "reasoning_fallbacks": ["test_fallback"],
                "escalation_criteria": ["test_criteria"]
            },
            "learning_mechanisms": ["feedback_incorporation"],
            "self_monitoring_capabilities": ["performance_tracking", "response_time_monitoring"],  # response_time_monitoring should now be allowed
            "agent_architecture": "single_agent",
            "coordination_requirements": None,
            "agentic_frameworks": ["test_framework"],
            "reasoning_engines": ["test_engine"]
        }
        
        # Test validation
        loader = PatternLoader("data/patterns")
        loader._validate_pattern(test_pattern)
        print("✅ Test pattern validated successfully with dynamic schema!")
        
    except Exception as e:
        print(f"❌ Pattern validation failed: {e}")
        return False
    
    return True

if __name__ == "__main__":
    success = test_dynamic_schema()
    if success:
        test_pattern_validation()