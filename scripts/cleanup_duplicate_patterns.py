#!/usr/bin/env python3
"""
Safe Pattern Cleanup Script
Removes duplicate auto-generated patterns while preserving high-value manual patterns.

Based on analysis:
- Current: 23 patterns
- Keep: 11 patterns (48% reduction)
- Remove: 12 duplicate patterns
"""

import os
import json
import shutil
from datetime import datetime
from pathlib import Path

# Patterns to KEEP (11 high-value patterns)
PATTERNS_TO_KEEP = {
    # High-Value Manual Patterns (7)
    "PAT-001.json",  # Legal contract summarization (unique, manual)
    "PAT-002.json",  # Invoice processing (foundational, manual)
    "PAT-003.json",  # Multilingual support (original, manual)
    "PAT-004.json",  # Brand-tone marketing (unique, manual)
    "PAT-005.json",  # Email order extraction (unique, manual)
    "PAT-006.json",  # PII redaction (security, manual)
    "PAT-009.json",  # Enhanced golf coaching (enhanced, unique)
    
    # Autonomous Agent Patterns - All Manual (4)
    "APAT-001.json", # Legal contract analysis agent
    "APAT-002.json", # Invoice processing agent
    "APAT-003.json", # Customer support agent
    "APAT-004.json", # Payment dispute agent
}

# Patterns to REMOVE (12 duplicates)
PATTERNS_TO_REMOVE = {
    # Golf Patterns - Remove 4 duplicates, keep PAT-009
    "PAT-010.json",  # Auto-generated golf duplicate
    "PAT-012.json",  # Auto-generated golf duplicate
    "PAT-015.json",  # Auto-generated golf duplicate
    "PAT-016.json",  # Auto-generated golf duplicate
    
    # Invoice/Payment Patterns - Remove 5 duplicates, keep PAT-002 & APAT-002
    "PAT-011.json",  # Auto-generated invoice variation
    "PAT-013.json",  # Auto-generated invoice variation
    "PAT-014.json",  # Auto-generated invoice variation
    "PAT-017.json",  # Auto-generated invoice variation
    "PAT-020.json",  # Duplicate of APAT-004 functionality
    
    # Customer Support Patterns - Remove 2 duplicates, keep PAT-003 & APAT-003
    "PAT-007.json",  # Auto-generated duplicate of PAT-003
    "PAT-019.json",  # Auto-generated generic messaging
    
    # Other Auto-Generated - Remove 1
    "PAT-008.json",  # Auto-generated simple card replacement
}

def backup_pattern(pattern_file: Path, backup_dir: Path) -> bool:
    """Create backup of pattern before deletion"""
    try:
        timestamp = int(datetime.now().timestamp())
        backup_name = f".deleted_{pattern_file.stem}_{timestamp}.json"
        backup_path = backup_dir / backup_name
        
        shutil.copy2(pattern_file, backup_path)
        print(f"✅ Backed up {pattern_file.name} → {backup_name}")
        return True
    except Exception as e:
        print(f"❌ Failed to backup {pattern_file.name}: {e}")
        return False

def validate_pattern_file(pattern_file: Path) -> dict:
    """Validate and load pattern file"""
    try:
        with open(pattern_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return data
    except Exception as e:
        print(f"⚠️  Warning: Could not validate {pattern_file.name}: {e}")
        return {}

def main():
    """Main cleanup function"""
    patterns_dir = Path("data/patterns")
    
    if not patterns_dir.exists():
        print(f"❌ Pattern directory not found: {patterns_dir}")
        return False
    
    print("🧹 Pattern Cleanup Script")
    print("=" * 50)
    print(f"📁 Pattern directory: {patterns_dir}")
    
    # Get current pattern files
    current_patterns = set(f.name for f in patterns_dir.glob("*.json") if not f.name.startswith('.deleted_'))
    
    print(f"📊 Current patterns: {len(current_patterns)}")
    print(f"🎯 Patterns to keep: {len(PATTERNS_TO_KEEP)}")
    print(f"🗑️  Patterns to remove: {len(PATTERNS_TO_REMOVE)}")
    
    # Validate our lists match reality
    missing_keep = PATTERNS_TO_KEEP - current_patterns
    missing_remove = PATTERNS_TO_REMOVE - current_patterns
    unexpected = current_patterns - PATTERNS_TO_KEEP - PATTERNS_TO_REMOVE
    
    if missing_keep:
        print(f"⚠️  Warning: Patterns to keep not found: {missing_keep}")
    
    if missing_remove:
        print(f"ℹ️  Info: Patterns to remove not found (already deleted?): {missing_remove}")
    
    if unexpected:
        print(f"⚠️  Warning: Unexpected patterns found: {unexpected}")
        print("   These will be preserved (not in removal list)")
    
    # Confirm before proceeding
    print("\n🔍 Pre-cleanup validation:")
    patterns_to_actually_remove = PATTERNS_TO_REMOVE & current_patterns
    print(f"   Will remove: {len(patterns_to_actually_remove)} patterns")
    print(f"   Will keep: {len(PATTERNS_TO_KEEP & current_patterns)} patterns")
    
    if not patterns_to_actually_remove:
        print("✅ No patterns to remove (already cleaned up?)")
        return True
    
    print(f"\n📋 Patterns to be removed:")
    for pattern in sorted(patterns_to_actually_remove):
        print(f"   - {pattern}")
    
    # Ask for confirmation
    response = input(f"\n❓ Remove {len(patterns_to_actually_remove)} duplicate patterns? (y/N): ").strip().lower()
    if response != 'y':
        print("❌ Cleanup cancelled by user")
        return False
    
    # Perform cleanup
    print("\n🗑️  Starting cleanup...")
    removed_count = 0
    failed_count = 0
    
    for pattern_name in sorted(patterns_to_actually_remove):
        pattern_file = patterns_dir / pattern_name
        
        # Validate pattern before removal
        pattern_data = validate_pattern_file(pattern_file)
        if pattern_data:
            pattern_id = pattern_data.get('pattern_id', 'unknown')
            name = pattern_data.get('name', 'unknown')
            print(f"\n🔍 Removing: {pattern_name} ({pattern_id}: {name})")
        
        # Create backup
        if backup_pattern(pattern_file, patterns_dir):
            try:
                pattern_file.unlink()
                print(f"✅ Removed: {pattern_name}")
                removed_count += 1
            except Exception as e:
                print(f"❌ Failed to remove {pattern_name}: {e}")
                failed_count += 1
        else:
            print(f"❌ Skipped removal of {pattern_name} (backup failed)")
            failed_count += 1
    
    # Summary
    print("\n" + "=" * 50)
    print("🎉 Cleanup Complete!")
    print(f"✅ Successfully removed: {removed_count} patterns")
    if failed_count > 0:
        print(f"❌ Failed to remove: {failed_count} patterns")
    
    # Final validation
    remaining_patterns = set(f.name for f in patterns_dir.glob("*.json") if not f.name.startswith('.deleted_'))
    print(f"📊 Remaining patterns: {len(remaining_patterns)}")
    
    kept_patterns = PATTERNS_TO_KEEP & remaining_patterns
    print(f"🎯 High-value patterns preserved: {len(kept_patterns)}")
    
    if len(kept_patterns) == len(PATTERNS_TO_KEEP & current_patterns):
        print("✅ All intended patterns preserved successfully!")
    else:
        print("⚠️  Warning: Some intended patterns may be missing")
    
    print(f"\n📈 Cleanup Results:")
    print(f"   Before: {len(current_patterns)} patterns")
    print(f"   After: {len(remaining_patterns)} patterns")
    print(f"   Reduction: {len(current_patterns) - len(remaining_patterns)} patterns ({((len(current_patterns) - len(remaining_patterns)) / len(current_patterns) * 100):.1f}%)")
    
    return removed_count > 0 and failed_count == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)