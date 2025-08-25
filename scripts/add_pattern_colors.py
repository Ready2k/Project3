#!/usr/bin/env python3
"""
Add Color Coding to Pattern Library
Adds appropriate colored ball indicators to patterns based on their automation level and solution type.

Color Scheme:
- 🔴 Red: Not Automatable / Manual processes
- 🟡 Yellow: Partially Automatable / Traditional automation with human oversight
- 🟢 Green: Fully Automatable / AI-enhanced solutions
- 🔵 Blue: Autonomous Agentic AI (APAT patterns) - highest automation level
"""

import json
import os
from pathlib import Path
from typing import Dict, List

def determine_pattern_color(pattern: Dict) -> str:
    """Determine the appropriate color ball for a pattern based on automation level and solution type"""
    
    pattern_id = pattern.get('pattern_id', '')
    feasibility = pattern.get('feasibility', '').lower()
    name = pattern.get('name', '').lower()
    description = pattern.get('description', '').lower()
    
    # APAT patterns get blue balls (Autonomous Agentic AI - highest level)
    if pattern_id.startswith('APAT-'):
        return '🔵'
    
    # Check feasibility field first for explicit automation level
    if feasibility in ['fully automatable', 'automatable']:
        return '🟢'  # Green for fully automatable AI-enhanced solutions
    elif feasibility in ['partially automatable', 'partial']:
        return '🟡'  # Yellow for partially automatable traditional automation
    elif feasibility in ['not automatable', 'manual']:
        return '🔴'  # Red for not automatable/manual processes
    
    # Fallback: analyze content for automation indicators
    # Look for AI/automation keywords that suggest full automation capability
    ai_automation_keywords = [
        'autonomous', 'ai', 'machine learning', 'nlp', 'automated', 'automatic',
        'intelligent', 'smart', 'cognitive', 'neural', 'algorithm'
    ]
    
    # Look for human-in-the-loop keywords that suggest partial automation
    human_oversight_keywords = [
        'human-in-the-loop', 'human review', 'approval', 'oversight', 'manual review',
        'human intervention', 'supervised', 'assisted'
    ]
    
    # Look for manual process keywords
    manual_keywords = [
        'manual', 'human-driven', 'requires human', 'cannot automate'
    ]
    
    content = f"{name} {description}".lower()
    
    # Check for manual indicators first
    if any(keyword in content for keyword in manual_keywords):
        return '🔴'
    
    # Check for human oversight indicators (partial automation)
    if any(keyword in content for keyword in human_oversight_keywords):
        return '🟡'
    
    # Check for AI/automation indicators (full automation)
    if any(keyword in content for keyword in ai_automation_keywords):
        return '🟢'
    
    # Default to yellow for traditional business automation
    return '🟡'

def add_color_to_pattern(pattern_file: Path) -> bool:
    """Add color field to a pattern file"""
    try:
        # Load pattern
        with open(pattern_file, 'r', encoding='utf-8') as f:
            pattern = json.load(f)
        
        # Determine color
        color = determine_pattern_color(pattern)
        
        # Add color field
        pattern['color'] = color
        
        # Save updated pattern
        with open(pattern_file, 'w', encoding='utf-8') as f:
            json.dump(pattern, f, indent=2, ensure_ascii=False)
        
        pattern_id = pattern.get('pattern_id', pattern_file.stem)
        name = pattern.get('name', 'Unknown')
        print(f"{color} {pattern_id} - {name}")
        
        return True
        
    except Exception as e:
        print(f"❌ Failed to process {pattern_file.name}: {e}")
        return False

def main():
    """Main function to add colors to all patterns"""
    patterns_dir = Path("data/patterns")
    
    if not patterns_dir.exists():
        print(f"❌ Pattern directory not found: {patterns_dir}")
        return False
    
    print("🎨 Adding Color Coding to Pattern Library")
    print("=" * 50)
    
    # Get all active pattern files (not deleted ones)
    pattern_files = [f for f in patterns_dir.glob("*.json") if not f.name.startswith('.deleted_')]
    
    if not pattern_files:
        print("❌ No pattern files found")
        return False
    
    print(f"📁 Found {len(pattern_files)} patterns to process")
    print("\n🎨 Color Scheme:")
    print("🔴 Red: Not Automatable / Manual processes")
    print("🟡 Yellow: Partially Automatable / Traditional automation with human oversight")
    print("🟢 Green: Fully Automatable / AI-enhanced solutions")
    print("🔵 Blue: Autonomous Agentic AI (APAT-*) - highest automation level")
    
    print(f"\n📋 Processing patterns:")
    
    success_count = 0
    failed_count = 0
    
    # Sort patterns for consistent output
    pattern_files.sort(key=lambda f: f.name)
    
    for pattern_file in pattern_files:
        if add_color_to_pattern(pattern_file):
            success_count += 1
        else:
            failed_count += 1
    
    print("\n" + "=" * 50)
    print("🎉 Color Coding Complete!")
    print(f"✅ Successfully processed: {success_count} patterns")
    if failed_count > 0:
        print(f"❌ Failed to process: {failed_count} patterns")
    
    print(f"\n📊 Pattern Color Distribution:")
    
    # Count colors
    color_counts = {}
    for pattern_file in pattern_files:
        try:
            with open(pattern_file, 'r', encoding='utf-8') as f:
                pattern = json.load(f)
            color = pattern.get('color', '❓')
            color_counts[color] = color_counts.get(color, 0) + 1
        except:
            continue
    
    for color, count in sorted(color_counts.items()):
        print(f"   {color} {count} patterns")
    
    return success_count > 0 and failed_count == 0

if __name__ == "__main__":
    success = main()
    exit(0 if success else 1)