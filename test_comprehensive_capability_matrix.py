#!/usr/bin/env python3
"""
Comprehensive Pattern Capabilities Matrix Test

Test that shows the full range of capability differentiation across pattern types.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_comprehensive_capability_matrix():
    """Test comprehensive capability differentiation across all pattern types."""
    
    print("🔍 Comprehensive Pattern Capabilities Matrix Test")
    print("=" * 60)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='ComprehensiveTest')
        
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
        
        # Group patterns by type
        pattern_groups = {
            'APAT': [],
            'PAT': [],
            'TRAD': []
        }
        
        for pattern in patterns:
            pattern_id = pattern.get('pattern_id', '')
            if pattern_id.startswith('APAT-'):
                pattern_groups['APAT'].append(pattern)
            elif pattern_id.startswith('PAT-'):
                pattern_groups['PAT'].append(pattern)
            elif pattern_id.startswith('TRAD-'):
                pattern_groups['TRAD'].append(pattern)
        
        print(f"\n📋 Pattern Distribution:")
        print(f"   • APAT patterns: {len(pattern_groups['APAT'])}")
        print(f"   • PAT patterns: {len(pattern_groups['PAT'])}")
        print(f"   • TRAD patterns: {len(pattern_groups['TRAD'])}")
        
        # Test capability differentiation
        print(f"\n🧪 Capability Differentiation Analysis:")
        
        capability_stats = {
            'APAT': {'agentic': 0, 'tech': 0, 'guidance': 0, 'effort': 0, 'total': 0},
            'PAT': {'agentic': 0, 'tech': 0, 'guidance': 0, 'effort': 0, 'total': 0},
            'TRAD': {'agentic': 0, 'tech': 0, 'guidance': 0, 'effort': 0, 'total': 0}
        }
        
        # Analyze each group
        for group_name, group_patterns in pattern_groups.items():
            if not group_patterns:
                continue
                
            print(f"\n   {group_name} Patterns:")
            
            for pattern in group_patterns[:3]:  # Show first 3 of each type
                pattern_id = pattern.get('pattern_id', 'Unknown')
                capabilities = pattern.get('_capabilities', {})
                complexity = pattern.get('_complexity_score', 0.5)
                autonomy = pattern.get('autonomy_level', 'N/A')
                
                agentic = capabilities.get('has_agentic_features', False)
                tech = capabilities.get('has_detailed_tech_stack', False)
                guidance = capabilities.get('has_implementation_guidance', False)
                effort = capabilities.get('has_detailed_effort_breakdown', False)
                
                print(f"     • {pattern_id}: {'✅' if agentic else '❌'}{'✅' if tech else '❌'}{'✅' if guidance else '❌'}{'✅' if effort else '❌'} | Complexity: {complexity:.2f} | Autonomy: {autonomy}")
                
                # Update stats
                stats = capability_stats[group_name]
                stats['total'] += 1
                if agentic: stats['agentic'] += 1
                if tech: stats['tech'] += 1
                if guidance: stats['guidance'] += 1
                if effort: stats['effort'] += 1
        
        # Calculate percentages and show summary
        print(f"\n📊 Capability Summary by Pattern Type:")
        
        for group_name, stats in capability_stats.items():
            if stats['total'] == 0:
                continue
                
            agentic_pct = (stats['agentic'] / stats['total']) * 100
            tech_pct = (stats['tech'] / stats['total']) * 100
            guidance_pct = (stats['guidance'] / stats['total']) * 100
            effort_pct = (stats['effort'] / stats['total']) * 100
            
            print(f"   {group_name} ({stats['total']} patterns):")
            print(f"     • Agentic Features: {agentic_pct:.0f}%")
            print(f"     • Detailed Tech Stack: {tech_pct:.0f}%")
            print(f"     • Implementation Guidance: {guidance_pct:.0f}%")
            print(f"     • Effort Breakdown: {effort_pct:.0f}%")
        
        # Test UI matrix simulation with diverse patterns
        print(f"\n🎨 UI Matrix Simulation (diverse pattern selection):")
        
        # Select representative patterns
        test_patterns = []
        
        # Add 2 APAT patterns
        if pattern_groups['APAT']:
            test_patterns.extend(pattern_groups['APAT'][:2])
        
        # Add 2 PAT patterns
        if pattern_groups['PAT']:
            test_patterns.extend(pattern_groups['PAT'][:2])
        
        # Add 1 TRAD pattern
        if pattern_groups['TRAD']:
            test_patterns.extend(pattern_groups['TRAD'][:1])
        
        capability_data = []
        for pattern in test_patterns:
            capabilities = pattern.get("_capabilities", {})
            capability_data.append({
                "Pattern ID": pattern.get("pattern_id", "Unknown"),
                "Name": pattern.get("name", "Unknown")[:25] + "..." if len(pattern.get("name", "")) > 25 else pattern.get("name", "Unknown"),
                "Agentic": "✅" if capabilities.get("has_agentic_features") else "❌",
                "Tech Stack": "✅" if capabilities.get("has_detailed_tech_stack") else "❌",
                "Guidance": "✅" if capabilities.get("has_implementation_guidance") else "❌",
                "Effort Detail": "✅" if capabilities.get("has_detailed_effort_breakdown") else "❌",
                "Complexity": pattern.get("_complexity_score", 0.5)
            })
        
        print(f"   Matrix Preview ({len(capability_data)} diverse patterns):")
        for row in capability_data:
            print(f"     • {row['Pattern ID']}: {row['Agentic']}{row['Tech Stack']}{row['Guidance']}{row['Effort Detail']} | {row['Complexity']:.2f}")
        
        # Check for meaningful differentiation
        unique_capability_patterns = set()
        for row in capability_data:
            pattern = f"{row['Agentic']}{row['Tech Stack']}{row['Guidance']}{row['Effort Detail']}"
            unique_capability_patterns.add(pattern)
        
        print(f"\n✅ Differentiation Analysis:")
        print(f"   • Unique capability patterns: {len(unique_capability_patterns)}")
        print(f"   • Patterns found: {list(unique_capability_patterns)}")
        
        if len(unique_capability_patterns) >= 3:
            print(f"\n🎉 SUCCESS: Excellent capability differentiation!")
            print(f"   The UI matrix will show meaningful differences between pattern types.")
            return True
        elif len(unique_capability_patterns) >= 2:
            print(f"\n✅ SUCCESS: Good capability differentiation!")
            print(f"   The UI matrix shows some meaningful differences.")
            return True
        else:
            print(f"\n⚠️  WARNING: Limited differentiation - all patterns look similar.")
            return False
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the comprehensive test."""
    print("🚀 Comprehensive Pattern Capabilities Matrix Test")
    print("=" * 70)
    
    success = test_comprehensive_capability_matrix()
    
    if success:
        print("\n🎉 SUCCESS: Pattern capabilities matrix shows meaningful differentiation!")
        print("   The UI should display varied ✅/❌ patterns instead of all identical.")
        return 0
    else:
        print("\n💥 FAILURE: Pattern capabilities matrix needs more work.")
        return 1


if __name__ == "__main__":
    sys.exit(main())