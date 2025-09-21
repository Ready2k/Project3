#!/usr/bin/env python3
"""
Test Pattern Capabilities Matrix

Test that individual patterns now have the _capabilities field for the UI matrix.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_pattern_capabilities_matrix():
    """Test that patterns have individual capabilities for the matrix display."""
    
    print("🔍 Testing Pattern Capabilities Matrix")
    print("=" * 50)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='MatrixTest')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("✅ Enhanced pattern loader available")
        
        # Get patterns
        patterns = enhanced_loader.load_patterns()
        print(f"📊 Total patterns loaded: {len(patterns)}")
        
        if not patterns:
            print("❌ No patterns loaded")
            return False
        
        # Test individual pattern capabilities
        print(f"\n🧪 Testing Individual Pattern Capabilities:")
        
        capabilities_summary = {
            'has_agentic_features': 0,
            'has_detailed_tech_stack': 0,
            'has_implementation_guidance': 0,
            'has_detailed_effort_breakdown': 0
        }
        
        # Test first few patterns
        for i, pattern in enumerate(patterns[:5]):
            pattern_id = pattern.get('pattern_id', f'Pattern-{i}')
            capabilities = pattern.get('_capabilities', {})
            
            print(f"\n   Pattern {pattern_id}:")
            print(f"     • _capabilities field exists: {bool(capabilities)}")
            
            if capabilities:
                agentic = capabilities.get('has_agentic_features', False)
                tech_stack = capabilities.get('has_detailed_tech_stack', False)
                guidance = capabilities.get('has_implementation_guidance', False)
                effort = capabilities.get('has_detailed_effort_breakdown', False)
                
                print(f"     • Agentic features: {'✅' if agentic else '❌'}")
                print(f"     • Tech stack: {'✅' if tech_stack else '❌'}")
                print(f"     • Implementation guidance: {'✅' if guidance else '❌'}")
                print(f"     • Effort breakdown: {'✅' if effort else '❌'}")
                
                # Count for summary
                if agentic:
                    capabilities_summary['has_agentic_features'] += 1
                if tech_stack:
                    capabilities_summary['has_detailed_tech_stack'] += 1
                if guidance:
                    capabilities_summary['has_implementation_guidance'] += 1
                if effort:
                    capabilities_summary['has_detailed_effort_breakdown'] += 1
            else:
                print(f"     • ❌ No _capabilities field found")
                return False
        
        # Test UI matrix simulation
        print(f"\n🎨 UI Matrix Simulation (first 5 patterns):")
        
        capability_data = []
        for pattern in patterns[:5]:
            capabilities = pattern.get("_capabilities", {})
            capability_data.append({
                "Pattern ID": pattern.get("pattern_id", "Unknown"),
                "Name": pattern.get("name", "Unknown")[:30] + "..." if len(pattern.get("name", "")) > 30 else pattern.get("name", "Unknown"),
                "Agentic": "✅" if capabilities.get("has_agentic_features") else "❌",
                "Tech Stack": "✅" if capabilities.get("has_detailed_tech_stack") else "❌",
                "Guidance": "✅" if capabilities.get("has_implementation_guidance") else "❌",
                "Effort Detail": "✅" if capabilities.get("has_detailed_effort_breakdown") else "❌",
                "Complexity": pattern.get("_complexity_score", 0.5)
            })
        
        print(f"   Matrix data generated for {len(capability_data)} patterns:")
        for row in capability_data:
            print(f"     • {row['Pattern ID']}: Agentic={row['Agentic']}, Tech={row['Tech Stack']}, Guidance={row['Guidance']}, Effort={row['Effort Detail']}")
        
        # Check if we have any green checkmarks
        has_green_marks = any(
            row['Agentic'] == '✅' or 
            row['Tech Stack'] == '✅' or 
            row['Guidance'] == '✅' or 
            row['Effort Detail'] == '✅'
            for row in capability_data
        )
        
        if has_green_marks:
            print(f"\n✅ SUCCESS: Patterns have capabilities - UI should show green checkmarks!")
            return True
        else:
            print(f"\n❌ ISSUE: All patterns show red X marks - capabilities not detected correctly")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the test."""
    print("🚀 Pattern Capabilities Matrix Test")
    print("=" * 60)
    
    success = test_pattern_capabilities_matrix()
    
    if success:
        print("\n🎉 SUCCESS: Pattern capabilities matrix should now show green checkmarks!")
        print("   The UI should display ✅ instead of ❌ for patterns with capabilities.")
        return 0
    else:
        print("\n💥 FAILURE: Pattern capabilities matrix still has issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())