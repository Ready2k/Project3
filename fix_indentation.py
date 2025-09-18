#!/usr/bin/env python3
"""
Script to fix indentation issues in streamlit_app.py after service registry migration.
"""

import re

def fix_indentation():
    """Fix indentation issues in streamlit_app.py."""
    
    with open('streamlit_app.py', 'r') as f:
        content = f.read()
    
    # Split into lines
    lines = content.split('\n')
    
    # Track indentation level and fix orphaned except blocks
    fixed_lines = []
    i = 0
    
    while i < len(lines):
        line = lines[i]
        
        # Check for orphaned except blocks (except without matching try)
        if re.match(r'^\s*except\s+', line):
            # Look backwards to find the matching if block
            j = i - 1
            while j >= 0:
                prev_line = lines[j]
                if re.match(r'^\s*if\s+.*:', prev_line):
                    # Found the if block, need to add try after it
                    if_indent = len(prev_line) - len(prev_line.lstrip())
                    try_indent = if_indent + 4
                    
                    # Insert try block after the if
                    try_line = ' ' * try_indent + 'try:'
                    lines.insert(j + 1, try_line)
                    
                    # Adjust current index
                    i += 1
                    
                    # Adjust indentation of content between if and except
                    for k in range(j + 2, i):
                        if lines[k].strip():  # Don't indent empty lines
                            lines[k] = '    ' + lines[k]
                    
                    break
                j -= 1
        
        i += 1
    
    # Write back the fixed content
    with open('streamlit_app.py', 'w') as f:
        f.write('\n'.join(lines))
    
    print("Fixed indentation issues in streamlit_app.py")

if __name__ == "__main__":
    fix_indentation()