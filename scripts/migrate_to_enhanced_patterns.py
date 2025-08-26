#!/usr/bin/env python3
"""
Migration script to enhance existing patterns with detailed technical information and agentic capabilities.
This script will create enhanced versions of existing patterns while preserving the originals.
"""

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Dict, List, Any

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.pattern.enhanced_loader import EnhancedPatternLoader
from app.services.pattern_enhancement_service import PatternEnhancementService
from app.api import create_llm_provider, ProviderConfig
from app.utils.logger import app_logger


class PatternMigrationManager:
    """Manages the migration of patterns to enhanced versions."""
    
    def __init__(self):
        self.pattern_library_path = Path("data/patterns")
        self.enhanced_loader = EnhancedPatternLoader(str(self.pattern_library_path))
        
        # Initialize LLM provider
        provider_config = ProviderConfig(
            provider="openai",
            model="gpt-4o",
            api_key=os.getenv("OPENAI_API_KEY"),
            endpoint_url=None,
            region=None
        )
        self.llm_provider = create_llm_provider(provider_config)
        
        # Initialize enhancement service
        self.enhancement_service = PatternEnhancementService(
            self.enhanced_loader, 
            self.llm_provider
        )
    
    async def migrate_all_patterns(self, enhancement_type: str = "full", dry_run: bool = False):
        """Migrate all eligible patterns to enhanced versions."""
        
        print("🚀 Starting Pattern Migration to Enhanced System")
        print("=" * 60)
        
        # Get enhancement candidates
        candidates = self.enhancement_service.get_enhancement_candidates()
        
        if not candidates:
            print("✅ All patterns are already enhanced!")
            return
        
        print(f"📊 Found {len(candidates)} patterns eligible for enhancement")
        print(f"🔧 Enhancement type: {enhancement_type}")
        print(f"🧪 Dry run mode: {'ON' if dry_run else 'OFF'}")
        print()
        
        # Show candidates
        print("📋 Enhancement Candidates:")
        for i, candidate in enumerate(candidates, 1):
            print(f"  {i:2d}. {candidate['pattern_id']} - {candidate['name'][:50]}...")
            print(f"      Complexity: {candidate['complexity']}, Potential: {candidate['enhancement_potential']:.2f}")
            missing = candidate.get('missing_capabilities', [])
            if missing:
                print(f"      Missing: {', '.join(missing[:3])}")
            print()
        
        if dry_run:
            print("🧪 DRY RUN MODE - No actual changes will be made")
            return
        
        # Confirm migration
        response = input("🤔 Do you want to proceed with the migration? (y/N): ")
        if response.lower() != 'y':
            print("❌ Migration cancelled")
            return
        
        # Perform migration
        print("\n🔄 Starting migration process...")
        
        pattern_ids = [c['pattern_id'] for c in candidates]
        results = await self.enhancement_service.batch_enhance_patterns(pattern_ids, enhancement_type)
        
        # Report results
        print("\n📊 Migration Results:")
        print(f"✅ Successfully enhanced: {len(results['successful'])}")
        print(f"❌ Failed to enhance: {len(results['failed'])}")
        
        if results['successful']:
            print("\n✅ Successfully Enhanced Patterns:")
            for result in results['successful']:
                print(f"  • {result['original_id']} → {result['enhanced_id']}")
        
        if results['failed']:
            print("\n❌ Failed Enhancements:")
            for result in results['failed']:
                print(f"  • {result['pattern_id']}: {result['error']}")
        
        print(f"\n🎉 Migration completed! Enhanced {len(results['successful'])} patterns.")
    
    async def migrate_specific_patterns(self, pattern_ids: List[str], enhancement_type: str = "full"):
        """Migrate specific patterns by ID."""
        
        print(f"🚀 Migrating specific patterns: {', '.join(pattern_ids)}")
        print(f"🔧 Enhancement type: {enhancement_type}")
        
        results = await self.enhancement_service.batch_enhance_patterns(pattern_ids, enhancement_type)
        
        print("\n📊 Migration Results:")
        print(f"✅ Successfully enhanced: {len(results['successful'])}")
        print(f"❌ Failed to enhance: {len(results['failed'])}")
        
        if results['successful']:
            print("\n✅ Successfully Enhanced Patterns:")
            for result in results['successful']:
                print(f"  • {result['original_id']} → {result['enhanced_id']}")
        
        if results['failed']:
            print("\n❌ Failed Enhancements:")
            for result in results['failed']:
                print(f"  • {result['pattern_id']}: {result['error']}")
    
    def analyze_current_patterns(self):
        """Analyze the current pattern library and show enhancement opportunities."""
        
        print("🔍 Analyzing Current Pattern Library")
        print("=" * 40)
        
        patterns = self.enhanced_loader.load_patterns()
        stats = self.enhanced_loader.get_pattern_statistics()
        
        print(f"📊 Total Patterns: {stats['total_patterns']}")
        print(f"📈 Average Complexity Score: {stats['average_complexity_score']:.2f}")
        print()
        
        print("📋 Pattern Types:")
        for pattern_type, count in stats['by_type'].items():
            print(f"  • {pattern_type}: {count}")
        print()
        
        print("🎯 Pattern Capabilities:")
        for capability, count in stats['capabilities'].items():
            capability_name = capability.replace('has_', '').replace('_', ' ').title()
            percentage = (count / stats['total_patterns']) * 100 if stats['total_patterns'] > 0 else 0
            print(f"  • {capability_name}: {count} ({percentage:.1f}%)")
        print()
        
        # Enhancement opportunities
        candidates = self.enhancement_service.get_enhancement_candidates()
        print(f"🚀 Enhancement Opportunities: {len(candidates)} patterns")
        
        if candidates:
            print("\n🎯 Top Enhancement Candidates:")
            for candidate in candidates[:5]:
                print(f"  • {candidate['pattern_id']}: {candidate['enhancement_potential']:.2f} potential")
    
    def create_sample_enhanced_pattern(self):
        """Create a sample enhanced pattern to demonstrate the new structure."""
        
        print("📝 Creating Sample Enhanced Pattern")
        
        # Load the template
        template_path = Path("app/pattern/enhanced_pattern_template.json")
        if not template_path.exists():
            print("❌ Enhanced pattern template not found")
            return
        
        with open(template_path, 'r') as f:
            template = json.load(f)
        
        # Modify for sample
        template["pattern_id"] = "EPAT-SAMPLE"
        template["name"] = "Sample Enhanced Pattern"
        template["description"] = "This is a sample enhanced pattern demonstrating the new structure with rich technical details and agentic capabilities."
        template["created_from_session"] = "migration-sample"
        
        # Save sample pattern
        sample_path = self.pattern_library_path / "EPAT-SAMPLE.json"
        with open(sample_path, 'w') as f:
            json.dump(template, f, indent=2)
        
        print(f"✅ Sample enhanced pattern created: {sample_path}")
        print("💡 You can view this pattern in the Enhanced Pattern Management tab")


async def main():
    """Main migration script entry point."""
    
    import argparse
    
    parser = argparse.ArgumentParser(description="Migrate patterns to enhanced system")
    parser.add_argument("--type", choices=["full", "technical", "agentic"], default="full",
                       help="Type of enhancement to apply")
    parser.add_argument("--dry-run", action="store_true",
                       help="Show what would be migrated without making changes")
    parser.add_argument("--analyze", action="store_true",
                       help="Analyze current patterns and show enhancement opportunities")
    parser.add_argument("--sample", action="store_true",
                       help="Create a sample enhanced pattern")
    parser.add_argument("--patterns", nargs="+",
                       help="Specific pattern IDs to migrate (e.g., PAT-001 PAT-002)")
    
    args = parser.parse_args()
    
    # Check for required environment variables
    if not os.getenv("OPENAI_API_KEY") and not args.analyze and not args.sample:
        print("❌ OPENAI_API_KEY environment variable is required for pattern enhancement")
        print("💡 Set your OpenAI API key: export OPENAI_API_KEY='your-key-here'")
        return
    
    try:
        migration_manager = PatternMigrationManager()
        
        if args.analyze:
            migration_manager.analyze_current_patterns()
        elif args.sample:
            migration_manager.create_sample_enhanced_pattern()
        elif args.patterns:
            await migration_manager.migrate_specific_patterns(args.patterns, args.type)
        else:
            await migration_manager.migrate_all_patterns(args.type, args.dry_run)
            
    except Exception as e:
        print(f"❌ Migration failed: {e}")
        app_logger.error(f"Migration error: {e}")
        return 1
    
    return 0


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)