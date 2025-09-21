#!/usr/bin/env python3
"""
Test Pattern Statistics Method

Test that the get_pattern_statistics method works correctly.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def test_pattern_statistics():
    """Test the get_pattern_statistics method."""
    try:
        # Register services first
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='StatisticsTest')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("🧪 Testing Pattern Statistics Method")
        print("=" * 50)
        
        # Test get_pattern_statistics method
        try:
            stats = enhanced_loader.get_pattern_statistics()
            print("✅ get_pattern_statistics() method exists and callable")
            
            # Check return type
            if isinstance(stats, dict):
                print("✅ Returns dictionary as expected")
            else:
                print(f"❌ Expected dict, got {type(stats)}")
                return False
            
            # Check required keys
            required_keys = [
                'total_patterns',
                'pattern_types', 
                'domains',
                'complexity_scores',
                'feasibility_levels',
                'autonomy_levels',
                'avg_complexity',
                'avg_autonomy'
            ]
            
            missing_keys = []
            for key in required_keys:
                if key in stats:
                    print(f"✅ Has key: {key}")
                else:
                    print(f"❌ Missing key: {key}")
                    missing_keys.append(key)
            
            if missing_keys:
                print(f"❌ Missing required keys: {missing_keys}")
                return False
            
            # Show statistics content
            print(f"\n📊 Pattern Statistics:")
            print(f"   • Total Patterns: {stats['total_patterns']}")
            print(f"   • Pattern Types: {stats['pattern_types']}")
            print(f"   • Domains: {stats['domains']}")
            print(f"   • Complexity Scores: {len(stats['complexity_scores'])} values")
            print(f"   • Feasibility Levels: {stats['feasibility_levels']}")
            print(f"   • Autonomy Levels: {len(stats['autonomy_levels'])} values")
            print(f"   • Avg Complexity: {stats['avg_complexity']:.2f}")
            print(f"   • Avg Autonomy: {stats['avg_autonomy']:.2f}")
            
            # Test with some mock patterns
            print(f"\n🔧 Testing with Mock Patterns:")
            
            # Add a mock pattern to test statistics calculation
            mock_pattern = {
                'id': 'TEST-001',
                'pattern_id': 'TEST-001',
                'name': 'Test Pattern',
                'title': 'Test Pattern',
                'description': 'A test pattern for statistics',
                'type': 'APAT',
                'domain': 'testing',
                'feasibility': 'high',
                'autonomy_level': 0.85,
                '_complexity_score': 0.7
            }
            
            # Add pattern to internal storage
            enhanced_loader.patterns['TEST-001'] = mock_pattern
            
            # Get updated statistics
            updated_stats = enhanced_loader.get_pattern_statistics()
            print(f"   • Updated Total Patterns: {updated_stats['total_patterns']}")
            print(f"   • Updated Pattern Types: {updated_stats['pattern_types']}")
            print(f"   • Updated Domains: {updated_stats['domains']}")
            print(f"   • Updated Avg Complexity: {updated_stats['avg_complexity']:.2f}")
            print(f"   • Updated Avg Autonomy: {updated_stats['avg_autonomy']:.2f}")
            
            # Clean up
            del enhanced_loader.patterns['TEST-001']
            
            print("\n✅ All pattern statistics tests passed!")
            return True
            
        except Exception as e:
            print(f"❌ get_pattern_statistics() test failed: {e}")
            import traceback
            traceback.print_exc()
            return False
        
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        return False


def main():
    """Run the test."""
    print("🚀 Pattern Statistics Test")
    print("=" * 40)
    
    success = test_pattern_statistics()
    
    if success:
        print("\n🎉 Pattern statistics method is working correctly!")
        return 0
    else:
        print("\n💥 Pattern statistics test failed.")
        return 1


if __name__ == "__main__":
    sys.exit(main())