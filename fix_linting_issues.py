#!/usr/bin/env python3
"""Script to fix common linting issues."""

import re
from pathlib import Path

def fix_unused_variables(content: str) -> str:
    """Fix unused variables by prefixing with underscore."""
    
    # Common patterns for unused variables
    patterns = [
        # Variables that are clearly meant to be unused
        (r'(\s+)(\w+) = (.*?)  # F841', r'\1_\2 = \3'),
        
        # Mock variables in tests
        (r'(\s+)(mock_\w+) = (.*)', r'\1_\2 = \3'),
        
        # Result variables that aren't used
        (r'(\s+)(result) = (.*)', r'\1_ = \3'),
        
        # Task variables in async code
        (r'(\s+)(task) = (asyncio\.create_task.*)', r'\1_ = \3'),
        
        # Logger variables
        (r'(\s+)(logger) = (.*)', r'\1_ = \3'),
        
        # Service variables
        (r'(\s+)(service) = (.*)', r'\1_ = \3'),
        
        # Handler variables
        (r'(\s+)(handler) = (.*)', r'\1_ = \3'),
        
        # Client variables
        (r'(\s+)(client) = (.*)', r'\1_ = \3'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_boolean_comparisons(content: str) -> str:
    """Fix boolean comparisons."""
    
    patterns = [
        # == True -> direct check
        (r'assert (\w+(?:\.\w+)*) == True', r'assert \1'),
        
        # == False -> not check
        (r'assert (\w+(?:\.\w+)*) == False', r'assert not \1'),
        
        # More complex patterns
        (r'if (\w+(?:\.\w+)*) == True:', r'if \1:'),
        (r'if (\w+(?:\.\w+)*) == False:', r'if not \1:'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_bare_except(content: str) -> str:
    """Fix bare except clauses."""
    
    patterns = [
        # except: -> except Exception:
        (r'(\s+)except:\s*$', r'\1except Exception:'),
        (r'(\s+)except:\s*#', r'\1except Exception:  #'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def remove_unused_imports(content: str) -> str:
    """Remove some obvious unused imports."""
    
    lines = content.split('\n')
    filtered_lines = []
    
    for line in lines:
        # Skip obvious unused imports
        if any(pattern in line for pattern in [
            'import json  # F401',
            'import time  # F401', 
            'import asyncio  # F401',
            'from typing import Any  # F401',
            'from typing import Optional  # F401',
            'from typing import List  # F401',
            'from typing import Dict  # F401',
        ]):
            continue
        filtered_lines.append(line)
    
    return '\n'.join(filtered_lines)

def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_unused_variables(content)
        content = fix_boolean_comparisons(content)
        content = fix_bare_except(content)
        content = remove_unused_imports(content)
        
        # Only write if changes were made
        if content != original_content:
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        return False
    except Exception as e:
        print(f"Error processing {file_path}: {e}")
        return False

def main():
    """Main function."""
    app_dir = Path("app")
    if not app_dir.exists():
        print("app directory not found!")
        return
    
    files_changed = 0
    total_files = 0
    
    for py_file in app_dir.rglob("*.py"):
        total_files += 1
        if process_file(py_file):
            files_changed += 1
            print(f"Fixed: {py_file}")
    
    print(f"\nProcessed {total_files} files, modified {files_changed} files")

if __name__ == "__main__":
    main()