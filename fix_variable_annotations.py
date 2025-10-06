#!/usr/bin/env python3
"""Script to fix variable type annotations."""

import re
from pathlib import Path

def fix_common_variable_patterns(content: str) -> str:
    """Fix common variable annotation patterns."""
    
    # Fix: errors = []
    content = re.sub(r'^(\s+)errors = \[\]$', r'\1errors: list[str] = []', content, flags=re.MULTILINE)
    
    # Fix: results = []
    content = re.sub(r'^(\s+)results = \[\]$', r'\1results: list[dict[str, Any]] = []', content, flags=re.MULTILINE)
    
    # Fix: items = []
    content = re.sub(r'^(\s+)items = \[\]$', r'\1items: list[Any] = []', content, flags=re.MULTILINE)
    
    # Fix: data = {}
    content = re.sub(r'^(\s+)data = \{\}$', r'\1data: dict[str, Any] = {}', content, flags=re.MULTILINE)
    
    # Fix: config = {}
    content = re.sub(r'^(\s+)config = \{\}$', r'\1config: dict[str, Any] = {}', content, flags=re.MULTILINE)
    
    # Fix: cache = {}
    content = re.sub(r'^(\s+)cache = \{\}$', r'\1cache: dict[str, Any] = {}', content, flags=re.MULTILINE)
    
    return content

def add_typing_import(content: str) -> str:
    """Add typing imports if needed."""
    if 'list[' in content or 'dict[' in content:
        if 'from typing import' not in content and 'import typing' not in content:
            # Find the first import line and add typing import before it
            lines = content.split('\n')
            for i, line in enumerate(lines):
                if line.startswith('import ') or line.startswith('from '):
                    lines.insert(i, 'from typing import Any')
                    return '\n'.join(lines)
            # If no imports found, add at the beginning after docstring
            for i, line in enumerate(lines):
                if not line.startswith('"""') and not line.startswith("'''") and line.strip():
                    lines.insert(i, 'from typing import Any')
                    return '\n'.join(lines)
    return content

def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_common_variable_patterns(content)
        content = add_typing_import(content)
        
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