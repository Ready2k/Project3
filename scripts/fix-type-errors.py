#!/usr/bin/env python3
"""
Script to help fix common MyPy type errors incrementally.
This script identifies and suggests fixes for the most common type errors.
"""

import subprocess
import re
from collections import Counter
from pathlib import Path


def run_mypy():
    """Run mypy and capture output."""
    try:
        result = subprocess.run(
            ["mypy", "--config-file=mypy.ini"],
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent.parent
        )
        return result.stdout + result.stderr
    except subprocess.CalledProcessError as e:
        return e.stdout + e.stderr


def analyze_errors(mypy_output):
    """Analyze mypy output and categorize errors."""
    error_patterns = {
        'missing_logger': r'has no attribute "logger"',
        'no_any_return': r'Returning Any from function declared to return',
        'union_attr': r'has no attribute.*\[union-attr\]',
        'attr_defined': r'has no attribute.*\[attr-defined\]',
        'assignment': r'Incompatible types in assignment.*\[assignment\]',
        'arg_type': r'has incompatible type.*\[arg-type\]',
        'var_annotated': r'Need type annotation.*\[var-annotated\]',
        'no_untyped_def': r'Function is missing.*\[no-untyped-def\]',
        'import_untyped': r'Library stubs not installed.*\[import-untyped\]',
    }
    
    error_counts = Counter()
    error_files = {}
    
    for line in mypy_output.split('\n'):
        if ': error:' in line:
            for error_type, pattern in error_patterns.items():
                if re.search(pattern, line):
                    error_counts[error_type] += 1
                    if error_type not in error_files:
                        error_files[error_type] = []
                    # Extract file path
                    file_match = re.match(r'^([^:]+):', line)
                    if file_match:
                        error_files[error_type].append(file_match.group(1))
                    break
    
    return error_counts, error_files


def suggest_fixes(error_counts, error_files):
    """Suggest fixes for common error types."""
    suggestions = {
        'missing_logger': """
Missing Logger Attribute Errors: {count}
Fix: Add logger initialization in __init__ methods:
    
    from app.utils.imports import require_service
    
    def __init__(self):
        self.logger = require_service('logger', context=self.__class__.__name__)

Files to fix: {files}
""",
        'no_any_return': """
Any Return Type Errors: {count}
Fix: Add proper return type annotations:
    
    # Before
    def method(self):
        return some_function()
    
    # After  
    def method(self) -> dict[str, Any]:
        return some_function()

Files to fix: {files}
""",
        'var_annotated': """
Variable Annotation Errors: {count}
Fix: Add type annotations to variables:
    
    # Before
    data = {}
    
    # After
    data: dict[str, Any] = {}

Files to fix: {files}
""",
        'no_untyped_def': """
Untyped Function Errors: {count}
Fix: Add return type annotations:
    
    # Before
    def function(self, param):
        pass
    
    # After
    def function(self, param: str) -> None:
        pass

Files to fix: {files}
""",
        'import_untyped': """
Untyped Import Errors: {count}
Fix: Install type stubs or add to mypy.ini:
    
    pip install types-package-name
    
    Or add to mypy.ini:
    [mypy-package.*]
    ignore_missing_imports = True

Files to fix: {files}
"""
    }
    
    print("🔍 MyPy Error Analysis and Suggestions\n")
    print("=" * 50)
    
    total_errors = sum(error_counts.values())
    print(f"Total errors found: {total_errors}\n")
    
    for error_type, count in error_counts.most_common():
        if error_type in suggestions:
            files = list(set(error_files.get(error_type, [])))[:5]  # Show first 5 files
            file_list = '\n    '.join(files)
            if len(error_files.get(error_type, [])) > 5:
                file_list += f"\n    ... and {len(error_files[error_type]) - 5} more"
            
            try:
                print(suggestions[error_type].format(
                    count=count,
                    files=file_list
                ))
            except (KeyError, IndexError):
                print(f"{error_type}: {count} errors")
                print(f"Files: {file_list}")
            print("-" * 30)


def main():
    """Main function."""
    print("🚀 Running MyPy analysis...")
    mypy_output = run_mypy()
    
    if not mypy_output:
        print("✅ No MyPy output found. All types are correct!")
        return
    
    error_counts, error_files = analyze_errors(mypy_output)
    suggest_fixes(error_counts, error_files)
    
    print("\n💡 Recommended approach:")
    print("1. Start with 'missing_logger' errors - these are easiest to fix")
    print("2. Add return type annotations for 'no_any_return' errors")
    print("3. Install missing type stubs for 'import_untyped' errors")
    print("4. Add variable annotations for 'var_annotated' errors")
    print("5. Run 'make typecheck' after each batch of fixes")


if __name__ == "__main__":
    main()