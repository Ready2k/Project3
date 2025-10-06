#!/usr/bin/env python3
"""Script to fix the final linting issues."""

import re
from pathlib import Path

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

def fix_ambiguous_variables(content: str) -> str:
    """Fix ambiguous variable names."""
    
    patterns = [
        # Replace single letter variables in comprehensions
        (r'for l in (\w+)', r'for latency in \1'),
        (r'if l < ', r'if latency < '),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def fix_type_comparison(content: str) -> str:
    """Fix type comparison issues."""
    
    patterns = [
        # type(obj) == type(other) -> isinstance(obj, type(other))
        (r'type\((\w+)\) == type\((\w+)\)', r'isinstance(\1, type(\2))'),
    ]
    
    for pattern, replacement in patterns:
        content = re.sub(pattern, replacement, content)
    
    return content

def remove_duplicate_functions(content: str) -> str:
    """Remove duplicate function definitions."""
    
    # Remove duplicate test_confidence_scoring_consistency
    if 'def test_confidence_scoring_consistency' in content:
        lines = content.split('\n')
        new_lines = []
        in_duplicate = False
        duplicate_count = 0
        
        for line in lines:
            if 'def test_confidence_scoring_consistency' in line:
                duplicate_count += 1
                if duplicate_count > 1:
                    in_duplicate = True
                    continue
            
            if in_duplicate and line.strip() and not line.startswith(' ') and not line.startswith('\t'):
                in_duplicate = False
            
            if not in_duplicate:
                new_lines.append(line)
        
        content = '\n'.join(new_lines)
    
    return content

def process_file(file_path: Path) -> bool:
    """Process a single Python file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        
        # Apply fixes
        content = fix_bare_except(content)
        content = fix_ambiguous_variables(content)
        content = fix_type_comparison(content)
        content = remove_duplicate_functions(content)
        
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