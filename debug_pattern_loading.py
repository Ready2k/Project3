#!/usr/bin/env python3
"""
Debug Pattern Loading

Debug why patterns are not being loaded by the enhanced pattern loader.
"""

import sys
from pathlib import Path

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))


def debug_pattern_loading():
    """Debug pattern loading issues."""
    
    print("🔍 Debugging Pattern Loading")
    print("=" * 50)
    
    try:
        # Register services
        from app.core.service_registration import register_core_services
        from app.core.registry import reset_registry
        
        reset_registry()
        register_core_services()
        
        # Get enhanced pattern loader
        from app.utils.imports import optional_service
        enhanced_loader = optional_service('enhanced_pattern_loader', context='Debug')
        
        if not enhanced_loader:
            print("❌ Enhanced pattern loader not available")
            return False
        
        print("✅ Enhanced pattern loader available")
        
        # Check pattern directory
        pattern_path = Path('./data/patterns')
        print(f"\n📁 Pattern Directory: {pattern_path}")
        print(f"   • Exists: {pattern_path.exists()}")
        
        if pattern_path.exists():
            all_files = list(pattern_path.glob("*.json"))
            print(f"   • Total JSON files: {len(all_files)}")
            
            # Check file filtering
            deleted_files = [f for f in all_files if f.name.startswith('.deleted_')]
            pattern_files = [f for f in all_files if (f.name.startswith('PAT-') or 
                                                     f.name.startswith('APAT-') or
                                                     f.name.startswith('TRAD-')) and 
                            not f.name.startswith('.deleted_')]
            other_files = [f for f in all_files if f not in deleted_files and f not in pattern_files]
            
            print(f"   • Deleted files: {len(deleted_files)}")
            print(f"   • Valid pattern files: {len(pattern_files)}")
            print(f"   • Other files: {len(other_files)}")
            
            if pattern_files:
                print(f"\n📋 Valid Pattern Files:")
                for i, f in enumerate(pattern_files[:5]):  # Show first 5
                    print(f"   • {f.name}")
                if len(pattern_files) > 5:
                    print(f"   • ... and {len(pattern_files) - 5} more")
        
        # Check current loaded patterns
        print(f"\n📊 Current Loaded Patterns:")
        print(f"   • Total patterns in memory: {len(enhanced_loader.patterns)}")
        
        if enhanced_loader.patterns:
            print(f"   • Pattern IDs: {list(enhanced_loader.patterns.keys())[:5]}")
        
        # Try to manually load patterns
        print(f"\n🔧 Manual Pattern Loading Test:")
        
        try:
            # Access the private method for testing
            import asyncio
            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            
            # Clear existing patterns
            enhanced_loader.patterns.clear()
            
            # Try to load patterns
            loop.run_until_complete(enhanced_loader._load_patterns())
            
            print(f"   • Patterns loaded after manual load: {len(enhanced_loader.patterns)}")
            
            if enhanced_loader.patterns:
                print(f"   • Sample pattern IDs: {list(enhanced_loader.patterns.keys())[:3]}")
                
                # Check a sample pattern
                sample_id = list(enhanced_loader.patterns.keys())[0]
                sample_pattern = enhanced_loader.patterns[sample_id]
                print(f"   • Sample pattern '{sample_id}':")
                print(f"     - Type: {sample_pattern.get('type', 'N/A')}")
                print(f"     - Domain: {sample_pattern.get('domain', 'N/A')}")
                print(f"     - Feasibility: {sample_pattern.get('feasibility', 'N/A')}")
                print(f"     - Autonomy Level: {sample_pattern.get('autonomy_level', 'N/A')}")
                print(f"     - Complexity Score: {sample_pattern.get('_complexity_score', sample_pattern.get('complexity_score', 'N/A'))}")
            
            loop.close()
            
        except Exception as e:
            print(f"   ❌ Manual loading failed: {e}")
            import traceback
            traceback.print_exc()
        
        # Test statistics after loading
        print(f"\n📈 Statistics After Loading:")
        try:
            stats = enhanced_loader.get_pattern_statistics()
            print(f"   • Total patterns: {stats['total_patterns']}")
            print(f"   • Pattern types: {stats['pattern_types']}")
            print(f"   • Domains: {stats['domains']}")
            print(f"   • Complexity scores: {len(stats['complexity_scores'])}")
            print(f"   • Autonomy levels: {len(stats['autonomy_levels'])}")
            
            if stats['total_patterns'] > 0:
                print("✅ Patterns loaded successfully!")
                return True
            else:
                print("❌ No patterns loaded")
                return False
                
        except Exception as e:
            print(f"   ❌ Statistics failed: {e}")
            return False
        
    except Exception as e:
        print(f"❌ Debug failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run the debug."""
    success = debug_pattern_loading()
    
    if success:
        print("\n🎉 Pattern loading is working!")
        return 0
    else:
        print("\n💥 Pattern loading has issues.")
        return 1


if __name__ == "__main__":
    sys.exit(main())