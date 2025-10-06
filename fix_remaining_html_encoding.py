#!/usr/bin/env python3
"""
Fix remaining HTML encoding issues in patterns.
"""

import json
import html
import re
from pathlib import Path
from app.utils.logger import app_logger


def fix_html_encoding_thoroughly():
    """Fix all HTML encoding issues in patterns."""
    
    pattern_dir = Path("data/patterns")
    patterns_fixed = 0
    
    for pattern_file in pattern_dir.glob("*.json"):
        if pattern_file.name.startswith('.deleted_'):
            continue
        
        try:
            with open(pattern_file, 'r') as f:
                content = f.read()
            
            # Check if file has HTML entities
            if any(entity in content for entity in ["&amp;", "&lt;", "&gt;", "&quot;", "&#"]):
                app_logger.info(f"Fixing HTML encoding in {pattern_file.name}")
                
                # Load as JSON
                pattern_data = json.loads(content)
                
                # Fix description field
                if "description" in pattern_data:
                    original_desc = pattern_data["description"]
                    
                    # Decode HTML entities
                    fixed_desc = html.unescape(original_desc)
                    
                    # Additional cleanup for specific patterns
                    if "Think hard about this one" in fixed_desc or "I need a solution that can dispute" in fixed_desc:
                        # Replace with proper pattern description
                        fixed_desc = (
                            "Multi-agent system for automated financial services dispute handling. "
                            "Enables customers to raise and track disputes through self-service voice and chat interfaces. "
                            "Integrates with Amazon Connect for customer interaction and Amazon Bedrock for intelligent processing. "
                            "Handles complex dispute scenarios with automated classification, assessment, and status tracking. "
                            "Supports natural language processing, regional accents, and DTMF input for comprehensive customer service automation."
                        )
                    
                    pattern_data["description"] = fixed_desc
                
                # Fix any other string fields that might have HTML encoding
                for key, value in pattern_data.items():
                    if isinstance(value, str) and any(entity in value for entity in ["&amp;", "&lt;", "&gt;", "&quot;", "&#"]):
                        pattern_data[key] = html.unescape(value)
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, str) and any(entity in item for entity in ["&amp;", "&lt;", "&gt;", "&quot;", "&#"]):
                                value[i] = html.unescape(item)
                    elif isinstance(value, dict):
                        for sub_key, sub_value in value.items():
                            if isinstance(sub_value, str) and any(entity in sub_value for entity in ["&amp;", "&lt;", "&gt;", "&quot;", "&#"]):
                                value[sub_key] = html.unescape(sub_value)
                
                # Save the fixed pattern
                with open(pattern_file, 'w') as f:
                    json.dump(pattern_data, f, indent=2)
                
                patterns_fixed += 1
                app_logger.info(f"Fixed HTML encoding in {pattern_file.name}")
        
        except Exception as e:
            app_logger.error(f"Error processing {pattern_file.name}: {e}")
            continue
    
    return patterns_fixed


def main():
    """Run the HTML encoding fix."""
    print("🔧 Fixing Remaining HTML Encoding Issues")
    print("=" * 50)
    
    patterns_fixed = fix_html_encoding_thoroughly()
    
    print(f"\n✅ Fixed HTML encoding in {patterns_fixed} patterns")
    
    # Verify the fix
    print("\n🧪 Verifying HTML encoding fix...")
    
    pattern_dir = Path("data/patterns")
    html_issues = []
    
    for pattern_file in pattern_dir.glob("*.json"):
        if pattern_file.name.startswith('.deleted_'):
            continue
        
        try:
            with open(pattern_file, 'r') as f:
                content = f.read()
            
            if any(entity in content for entity in ["&amp;", "&lt;", "&gt;", "&quot;", "&#"]):
                html_issues.append(pattern_file.name)
        
        except Exception as e:
            print(f"Error checking {pattern_file.name}: {e}")
    
    if not html_issues:
        print("✅ All HTML encoding issues resolved!")
    else:
        print(f"❌ Still have HTML encoding issues in: {html_issues}")
    
    return len(html_issues) == 0


if __name__ == "__main__":
    main()