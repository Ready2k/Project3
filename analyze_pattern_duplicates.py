#!/usr/bin/env python3
"""
Analyze and fix duplicate patterns in the pattern library.
"""

import asyncio
import json
from pathlib import Path
from app.services.pattern_deduplication_service import PatternDeduplicationService


def print_similarity_report(duplicates):
    """Print a detailed similarity report."""
    if not duplicates:
        print("✅ No duplicate patterns found!")
        return
    
    print(f"\n📊 Pattern Similarity Analysis")
    print("=" * 60)
    
    # Categorize by similarity level
    exact_duplicates = [d for d in duplicates if d.overall_similarity >= 0.99]
    near_duplicates = [d for d in duplicates if 0.95 <= d.overall_similarity < 0.99]
    high_similarity = [d for d in duplicates if 0.85 <= d.overall_similarity < 0.95]
    
    print(f"🔴 Exact Duplicates (≥99%): {len(exact_duplicates)}")
    print(f"🟠 Near Duplicates (95-99%): {len(near_duplicates)}")
    print(f"🟡 High Similarity (85-95%): {len(high_similarity)}")
    
    # Show exact duplicates in detail
    if exact_duplicates:
        print(f"\n🔴 EXACT DUPLICATES (SHOULD BE REMOVED):")
        print("-" * 50)
        for dup in exact_duplicates:
            print(f"Pattern 1: {dup.pattern_id_1}")
            print(f"Pattern 2: {dup.pattern_id_2}")
            print(f"Overall Similarity: {dup.overall_similarity:.1%}")
            print(f"Tech Stack Similarity: {dup.tech_stack_similarity:.1%}")
            print(f"Pattern Type Similarity: {dup.pattern_type_similarity:.1%}")
            print(f"Recommended Action: {dup.recommended_action}")
            print()
    
    # Show near duplicates
    if near_duplicates:
        print(f"\n🟠 NEAR DUPLICATES (REVIEW FOR CONSOLIDATION):")
        print("-" * 50)
        for dup in near_duplicates:
            print(f"{dup.pattern_id_1} ↔ {dup.pattern_id_2}: {dup.overall_similarity:.1%} similarity")
    
    # Show high similarity patterns
    if high_similarity:
        print(f"\n🟡 HIGH SIMILARITY (CONSIDER CONSOLIDATION):")
        print("-" * 50)
        for dup in high_similarity:
            print(f"{dup.pattern_id_1} ↔ {dup.pattern_id_2}: {dup.overall_similarity:.1%} similarity")


def load_pattern_details(pattern_library_path: Path, pattern_id: str):
    """Load pattern details for display."""
    pattern_file = pattern_library_path / f"{pattern_id}.json"
    if pattern_file.exists():
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern = json.load(f)
                return {
                    'name': pattern.get('name', 'Unknown'),
                    'description': pattern.get('description', '')[:100] + '...',
                    'tech_stack': pattern.get('tech_stack', []),
                    'pattern_type': pattern.get('pattern_type', []),
                    'domain': pattern.get('domain', 'Unknown')
                }
        except Exception as e:
            return {'error': str(e)}
    return None


def interactive_duplicate_resolution(dedup_service: PatternDeduplicationService, duplicates):
    """Interactive resolution of duplicate patterns."""
    exact_duplicates = [d for d in duplicates if d.overall_similarity >= 0.99]
    
    if not exact_duplicates:
        print("No exact duplicates to resolve.")
        return
    
    print(f"\n🔧 INTERACTIVE DUPLICATE RESOLUTION")
    print("=" * 50)
    
    for i, dup in enumerate(exact_duplicates, 1):
        print(f"\nDuplicate {i}/{len(exact_duplicates)}:")
        print(f"Similarity: {dup.overall_similarity:.1%}")
        
        # Load pattern details
        pattern1_details = load_pattern_details(dedup_service.pattern_library_path, dup.pattern_id_1)
        pattern2_details = load_pattern_details(dedup_service.pattern_library_path, dup.pattern_id_2)
        
        print(f"\nPattern A: {dup.pattern_id_1}")
        if pattern1_details:
            print(f"  Name: {pattern1_details.get('name', 'Unknown')}")
            print(f"  Domain: {pattern1_details.get('domain', 'Unknown')}")
            print(f"  Tech Stack: {', '.join(pattern1_details.get('tech_stack', [])[:3])}...")
        
        print(f"\nPattern B: {dup.pattern_id_2}")
        if pattern2_details:
            print(f"  Name: {pattern2_details.get('name', 'Unknown')}")
            print(f"  Domain: {pattern2_details.get('domain', 'Unknown')}")
            print(f"  Tech Stack: {', '.join(pattern2_details.get('tech_stack', [])[:3])}...")
        
        print(f"\nOptions:")
        print(f"  1. Keep Pattern A ({dup.pattern_id_1}), remove Pattern B")
        print(f"  2. Keep Pattern B ({dup.pattern_id_2}), remove Pattern A")
        print(f"  3. Skip this duplicate")
        print(f"  4. Exit")
        
        while True:
            choice = input("\nEnter your choice (1-4): ").strip()
            
            if choice == '1':
                result = dedup_service.merge_duplicate_patterns(
                    dup.pattern_id_1, dup.pattern_id_2, dup.pattern_id_1
                )
                if result['success']:
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ {result['message']}")
                break
            elif choice == '2':
                result = dedup_service.merge_duplicate_patterns(
                    dup.pattern_id_1, dup.pattern_id_2, dup.pattern_id_2
                )
                if result['success']:
                    print(f"✅ {result['message']}")
                else:
                    print(f"❌ {result['message']}")
                break
            elif choice == '3':
                print("⏭️  Skipped this duplicate")
                break
            elif choice == '4':
                print("👋 Exiting duplicate resolution")
                return
            else:
                print("Invalid choice. Please enter 1, 2, 3, or 4.")


def main():
    """Main function to analyze and fix pattern duplicates."""
    print("🔍 Pattern Duplicate Analysis Tool")
    print("=" * 40)
    
    # Initialize deduplication service
    pattern_library_path = Path('data/patterns')
    if not pattern_library_path.exists():
        print(f"❌ Pattern library not found: {pattern_library_path}")
        return
    
    dedup_service = PatternDeduplicationService(pattern_library_path)
    
    # Find all duplicates
    print("Analyzing patterns for duplicates...")
    duplicates = dedup_service.find_all_duplicates()
    
    # Print similarity report
    print_similarity_report(duplicates)
    
    # Generate comprehensive report
    report = dedup_service.generate_deduplication_report()
    
    print(f"\n📋 SUMMARY REPORT")
    print("-" * 30)
    print(f"Total pattern comparisons: {report['total_comparisons']}")
    print(f"Exact duplicates: {report['exact_duplicates']}")
    print(f"Near duplicates: {report['near_duplicates']}")
    print(f"High similarity: {report['high_similarity']}")
    
    if report['recommendations']:
        print(f"\n💡 RECOMMENDATIONS:")
        for rec in report['recommendations']:
            print(f"  • {rec}")
    
    # Ask if user wants to resolve duplicates interactively
    if report['exact_duplicates'] > 0:
        print(f"\n🤔 Would you like to resolve exact duplicates interactively?")
        choice = input("Enter 'y' for yes, 'n' for no: ").strip().lower()
        
        if choice == 'y':
            interactive_duplicate_resolution(dedup_service, duplicates)
        else:
            print("💾 You can run this script again later to resolve duplicates.")
    
    print(f"\n✅ Analysis complete!")


if __name__ == '__main__':
    main()