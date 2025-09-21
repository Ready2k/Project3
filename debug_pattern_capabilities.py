#!/usr/bin/env python3
"""
Debug Pattern Capabilities

Debug why the pattern capabilities matrix is showing all X marks.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_pattern_capabilities():
    """Debug pattern capabilities detection."""
    
    print("🔍 Debugging Pattern Capabilities")
    print("=" * 50)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='CapabilitiesDebug')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("✅ Enhanced pattern loader available")
        
        # Get patterns
        patterns = enhanced_loader.load_patterns()
        print(f"📊 Total patterns loaded: {len(patterns)}")
        
        if patterns:
            # Check first pattern structure
            sample_pattern = patterns[0]
            pattern_id = sample_pattern.get('pattern_id', 'Unknown')
            print(f"\n🔍 Sample Pattern: {pattern_id}")
            print(f"   • Keys: {list(sample_pattern.keys())}")
            
            # Check for _capabilities field
            capabilities = sample_pattern.get("_capabilities", {})
            print(f"   • _capabilities field: {capabilities}")
            
            # Check individual capability fields
            print(f"\n🧪 Capability Detection Test:")
            
            # Test agentic features
            has_agentic = (
                pattern_id.startswith('APAT-') or 
                sample_pattern.get('autonomy_level') is not None or
                sample_pattern.get('reasoning_types') or
                sample_pattern.get('decision_boundaries')
            )
            print(f"   • Agentic features: {has_agentic}")
            print(f"     - APAT prefix: {pattern_id.startswith('APAT-')}")
            print(f"     - autonomy_level: {sample_pattern.get('autonomy_level')}")
            print(f"     - reasoning_types: {sample_pattern.get('reasoning_types')}")
            print(f"     - decision_boundaries: {sample_pattern.get('decision_boundaries')}")
            
            # Test tech stack
            tech_stack = sample_pattern.get('tech_stack', {})
            has_tech_stack = (
                isinstance(tech_stack, dict) and tech_stack.get('core_technologies') or
                isinstance(tech_stack, list) and len(tech_stack) > 0
            )
            print(f"   • Tech stack: {has_tech_stack}")
            print(f"     - tech_stack type: {type(tech_stack)}")
            print(f"     - tech_stack content: {tech_stack}")
            
            # Test implementation guidance
            has_guidance = (
                sample_pattern.get('implementation_guidance') or
                sample_pattern.get('llm_recommended_approach') or
                sample_pattern.get('estimated_effort')
            )
            print(f"   • Implementation guidance: {has_guidance}")
            print(f"     - implementation_guidance: {bool(sample_pattern.get('implementation_guidance'))}")
            print(f"     - llm_recommended_approach: {bool(sample_pattern.get('llm_recommended_approach'))}")
            print(f"     - estimated_effort: {bool(sample_pattern.get('estimated_effort'))}")
            
            # Check what the UI would show
            print(f"\n🎨 UI Display Logic:")
            ui_capabilities = sample_pattern.get("_capabilities", {})
            print(f"   • UI looks for _capabilities: {ui_capabilities}")
            print(f"   • Would show Agentic: {'✅' if ui_capabilities.get('has_agentic_features') else '❌'}")
            print(f"   • Would show Tech Stack: {'✅' if ui_capabilities.get('has_detailed_tech_stack') else '❌'}")
            print(f"   • Would show Guidance: {'✅' if ui_capabilities.get('has_implementation_guidance') else '❌'}")
            
            return True
        else:
            print("❌ No patterns loaded")
            return False
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the debug."""
    success = debug_pattern_capabilities()
    
    if success:
        print("\n🎯 Debug complete!")
        return 0
    else:
        print("\n💥 Debug failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())