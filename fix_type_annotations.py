#!/usr/bin/env python3
"""Script to automatically fix common type annotation issues."""

import re
import os
from pathlib import Path

def fix_init_methods(content: str) -> str:
    """Add -> None to __init__ methods."""
    # Pattern: def __init__(self, ...):
    pattern = r'(def __init__\([^)]*\)):'
    replacement = r'\1 -> None:'
    return re.sub(pattern, replacement, content)

def fix_setup_teardown_methods(content: str) -> str:
    """Add -> None to common setup/teardown methods."""
    methods = ['setUp', 'tearDown', 'setup', 'teardown', 'initialize', 'shutdown', 'close']
    for method in methods:
        pattern = rf'(def {method}\([^)]*\)):'
        replacement = r'\1 -> None:'
        content = re.sub(pattern, replacement, content)
    return content

def fix_property_setters(content: str) -> str:
    """Add -> None to property setters."""
    pattern = r'(@\w+\.setter\s+def \w+\([^)]*\)):'
    replacement = r'\1 -> None:'
    return re.sub(pattern, replacement, content)

def process_file(file_path: Path) -> bool:
    """Process a single Python file to add type annotations."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_init_methods(content)
        content = fix_setup_teardown_methods(content)
        content = fix_property_setters(content)
        
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
    """Main function to process all Python files."""
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