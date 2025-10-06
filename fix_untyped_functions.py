#!/usr/bin/env python3
"""Advanced script to fix untyped function definitions."""

import re
from pathlib import Path

def fix_advanced_function_patterns(content: str) -> str:
    """Fix more advanced function return type patterns."""
    
    # More comprehensive patterns for function return types
    patterns = [
        # Property methods
        (r'(@property\s+def \w+\([^)]*\)):', r'\1 -> Any:'),
        
        # Async methods that return None
        (r'(async def (?:setup|teardown|initialize|shutdown|close|start|stop|reset|clear|update|set_\w+|add_\w+|remove_\w+|delete_\w+|create_\w+|configure|validate|process|handle|execute|run|perform)\([^)]*\)):', r'\1 -> None:'),
        
        # Generator functions
        (r'(def \w*(?:generate|yield|iter)\w*\([^)]*\)):', r'\1 -> Any:'),
        
        # Context managers
        (r'(def __enter__\([^)]*\)):', r'\1 -> Any:'),
        (r'(def __exit__\([^)]*\)):', r'\1 -> None:'),
        
        # Magic methods
        (r'(def __str__\([^)]*\)):', r'\1 -> str:'),
        (r'(def __repr__\([^)]*\)):', r'\1 -> str:'),
        (r'(def __len__\([^)]*\)):', r'\1 -> int:'),
        (r'(def __bool__\([^)]*\)):', r'\1 -> bool:'),
        (r'(def __eq__\([^)]*\)):', r'\1 -> bool:'),
        (r'(def __ne__\([^)]*\)):', r'\1 -> bool:'),
        (r'(def __lt__\([^)]*\)):', r'\1 -> bool:'),
        (r'(def __le__\([^)]*\)):', r'\1 -> bool:'),
        (r'(def __gt__\([^)]*\)):', r'\1 -> bool:'),
        (r'(def __ge__\([^)]*\)):', r'\1 -> bool:'),
        (r'(def __hash__\([^)]*\)):', r'\1 -> int:'),
        (r'(def __call__\([^)]*\)):', r'\1 -> Any:'),
        
        # Factory methods
        (r'(def (?:create|build|make|construct|factory)\w*\([^)]*\)):', r'\1 -> Any:'),
        
        # Loader/parser methods
        (r'(def (?:load|parse|read|fetch|get)\w*\([^)]*\)):', r'\1 -> Any:'),
        
        # Converter methods
        (r'(def (?:to_\w+|as_\w+|convert\w*)\([^)]*\)):', r'\1 -> Any:'),
        
        # Validator methods that return bool
        (r'(def (?:validate|verify|check|test|match)\w*\([^)]*\)):', r'\1 -> bool:'),
        
        # Counter/calculator methods
        (r'(def (?:count|calculate|compute|sum)\w*\([^)]*\)):', r'\1 -> int:'),
        
        # Finder methods that return lists
        (r'(def (?:find|search|filter|select)\w*\([^)]*\)):', r'\1 -> list[Any]:'),
        
        # Setter methods that return None
        (r'(def set_\w+\([^)]*\)):', r'\1 -> None:'),
        
        # Event handlers that return None
        (r'(def (?:on_\w+|handle_\w+|process_\w+)\([^)]*\)):', r'\1 -> None:'),
        
        # Callback functions
        (r'(def callback\w*\([^)]*\)):', r'\1 -> None:'),
        
        # Helper/utility functions
        (r'(def (?:_\w+|helper\w*|util\w*)\([^)]*\)):', r'\1 -> Any:'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def fix_nested_functions(content: str) -> str:
    """Fix nested function definitions."""
    
    # Common nested function patterns
    patterns = [
        # Lambda-like nested functions
        (r'(\s+def \w+\([^)]*\)):\s*$', r'\1 -> Any:'),
        
        # Callback definitions
        (r'(\s+def callback\([^)]*\)):', r'\1 -> None:'),
        (r'(\s+def handler\([^)]*\)):', r'\1 -> None:'),
        
        # Logging functions
        (r'(\s+def log_\w+\([^)]*\)):', r'\1 -> None:'),
        
        # Helper functions
        (r'(\s+def _\w+\([^)]*\)):', r'\1 -> Any:'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content, flags=re.MULTILINE)
    
    return content

def add_comprehensive_imports(content: str) -> str:
    """Add comprehensive typing imports."""
    
    needs_any = ('-> Any:' in content or 
                 'list[Any]' in content or 
                 'dict[str, Any]' in content)
    
    if needs_any and 'from typing import' in content:
        # Add Any to existing typing import if not present
        if 'from typing import Any' not in content:
            content = re.sub(
                r'from typing import ([^\n]+)',
                lambda m: f'from typing import Any, {m.group(1)}' if 'Any' not in m.group(1) else m.group(0),
                content
            )
    elif needs_any and 'from typing import' not in content:
        # Add typing import at the top after docstring
        lines = content.split('\n')
        insert_index = 0
        
        # Skip docstring
        in_docstring = False
        for i, line in enumerate(lines):
            if line.strip().startswith('"""') or line.strip().startswith("'''"):
                if not in_docstring:
                    in_docstring = True
                elif line.strip().endswith('"""') or line.strip().endswith("'''"):
                    in_docstring = False
                    insert_index = i + 1
                    break
            elif not in_docstring and (line.startswith('import ') or line.startswith('from ')):
                insert_index = i
                break
        
        if insert_index < len(lines):
            lines.insert(insert_index, 'from typing import Any')
            content = '\n'.join(lines)
    
    return content

def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_advanced_function_patterns(content)
        content = fix_nested_functions(content)
        content = add_comprehensive_imports(content)
        
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