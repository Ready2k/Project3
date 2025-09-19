#!/usr/bin/env python3
"""
Type coverage checker script.

This script analyzes the codebase to report type hint coverage
and identify areas that need type annotations.
"""

import ast
import sys
from pathlib import Path
from typing import Dict, List, Tuple, Set
from dataclasses import dataclass


@dataclass
class TypeCoverageStats:
    """Statistics for type coverage analysis."""
    total_functions: int = 0
    typed_functions: int = 0
    total_methods: int = 0
    typed_methods: int = 0
    total_variables: int = 0
    typed_variables: int = 0
    files_analyzed: int = 0
    
    @property
    def function_coverage(self) -> float:
        """Calculate function type coverage percentage."""
        if self.total_functions == 0:
            return 100.0
        return (self.typed_functions / self.total_functions) * 100
    
    @property
    def method_coverage(self) -> float:
        """Calculate method type coverage percentage."""
        if self.total_methods == 0:
            return 100.0
        return (self.typed_methods / self.total_methods) * 100
    
    @property
    def variable_coverage(self) -> float:
        """Calculate variable type coverage percentage."""
        if self.total_variables == 0:
            return 100.0
        return (self.typed_variables / self.total_variables) * 100
    
    @property
    def overall_coverage(self) -> float:
        """Calculate overall type coverage percentage."""
        total_items = self.total_functions + self.total_methods + self.total_variables
        typed_items = self.typed_functions + self.typed_methods + self.typed_variables
        
        if total_items == 0:
            return 100.0
        return (typed_items / total_items) * 100


class TypeCoverageAnalyzer(ast.NodeVisitor):
    """AST visitor to analyze type hint coverage."""
    
    def __init__(self):
        self.stats = TypeCoverageStats()
        self.untyped_functions: List[Tuple[str, int]] = []
        self.untyped_methods: List[Tuple[str, int]] = []
        self.untyped_variables: List[Tuple[str, int]] = []
        self.current_file: str = ""
    
    def analyze_file(self, file_path: Path) -> None:
        """Analyze a single Python file."""
        self.current_file = str(file_path)
        
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            tree = ast.parse(content, filename=str(file_path))
            self.visit(tree)
            self.stats.files_analyzed += 1
            
        except (SyntaxError, UnicodeDecodeError) as e:
            print(f"Warning: Could not parse {file_path}: {e}")
    
    def visit_FunctionDef(self, node: ast.FunctionDef) -> None:
        """Visit function definitions."""
        self.stats.total_functions += 1
        
        # Check if function has return type annotation
        has_return_type = node.returns is not None
        
        # Check if all parameters have type annotations
        has_param_types = all(
            arg.annotation is not None 
            for arg in node.args.args
            if arg.arg != 'self'  # Skip 'self' parameter
        )
        
        if has_return_type and has_param_types:
            self.stats.typed_functions += 1
        else:
            self.untyped_functions.append((
                f"{self.current_file}:{node.lineno}:{node.name}",
                node.lineno
            ))
        
        self.generic_visit(node)
    
    def visit_AsyncFunctionDef(self, node: ast.AsyncFunctionDef) -> None:
        """Visit async function definitions."""
        # Treat async functions the same as regular functions
        self.visit_FunctionDef(node)
    
    def visit_ClassDef(self, node: ast.ClassDef) -> None:
        """Visit class definitions to analyze methods."""
        for item in node.body:
            if isinstance(item, (ast.FunctionDef, ast.AsyncFunctionDef)):
                self.stats.total_methods += 1
                
                # Check method type annotations
                has_return_type = item.returns is not None
                has_param_types = all(
                    arg.annotation is not None 
                    for arg in item.args.args
                    if arg.arg != 'self'
                )
                
                if has_return_type and has_param_types:
                    self.stats.typed_methods += 1
                else:
                    self.untyped_methods.append((
                        f"{self.current_file}:{item.lineno}:{node.name}.{item.name}",
                        item.lineno
                    ))
        
        self.generic_visit(node)
    
    def visit_AnnAssign(self, node: ast.AnnAssign) -> None:
        """Visit annotated assignments (typed variables)."""
        self.stats.total_variables += 1
        self.stats.typed_variables += 1
        self.generic_visit(node)
    
    def visit_Assign(self, node: ast.Assign) -> None:
        """Visit regular assignments (potentially untyped variables)."""
        # Only count module-level and class-level assignments
        if isinstance(node.targets[0], ast.Name):
            self.stats.total_variables += 1
            # This is untyped since it's not an AnnAssign
            self.untyped_variables.append((
                f"{self.current_file}:{node.lineno}",
                node.lineno
            ))
        
        self.generic_visit(node)


def analyze_directory(directory: Path, exclude_patterns: Set[str] = None) -> TypeCoverageStats:
    """Analyze type coverage for all Python files in a directory."""
    if exclude_patterns is None:
        exclude_patterns = {
            '__pycache__',
            '.mypy_cache',
            '.pytest_cache',
            'test_',
            '_test.py',
            'conftest.py'
        }
    
    analyzer = TypeCoverageAnalyzer()
    
    for py_file in directory.rglob('*.py'):
        # Skip excluded files
        if any(pattern in str(py_file) for pattern in exclude_patterns):
            continue
        
        analyzer.analyze_file(py_file)
    
    return analyzer.stats, analyzer


def print_coverage_report(stats: TypeCoverageStats, analyzer: TypeCoverageAnalyzer) -> None:
    """Print a detailed coverage report."""
    print("=" * 60)
    print("TYPE COVERAGE REPORT")
    print("=" * 60)
    print()
    
    print(f"Files analyzed: {stats.files_analyzed}")
    print()
    
    print("COVERAGE SUMMARY:")
    print(f"  Functions:  {stats.typed_functions:3d}/{stats.total_functions:3d} ({stats.function_coverage:5.1f}%)")
    print(f"  Methods:    {stats.typed_methods:3d}/{stats.total_methods:3d} ({stats.method_coverage:5.1f}%)")
    print(f"  Variables:  {stats.typed_variables:3d}/{stats.total_variables:3d} ({stats.variable_coverage:5.1f}%)")
    print(f"  Overall:    {stats.function_coverage + stats.method_coverage + stats.variable_coverage:5.1f}% ({stats.overall_coverage:5.1f}%)")
    print()
    
    # Show untyped items if any
    if analyzer.untyped_functions:
        print("UNTYPED FUNCTIONS:")
        for func, line in sorted(analyzer.untyped_functions, key=lambda x: x[1]):
            print(f"  {func}")
        print()
    
    if analyzer.untyped_methods:
        print("UNTYPED METHODS:")
        for method, line in sorted(analyzer.untyped_methods, key=lambda x: x[1]):
            print(f"  {method}")
        print()
    
    if analyzer.untyped_variables and len(analyzer.untyped_variables) < 20:
        print("UNTYPED VARIABLES (showing first 20):")
        for var, line in sorted(analyzer.untyped_variables[:20], key=lambda x: x[1]):
            print(f"  {var}")
        print()
    
    # Recommendations
    print("RECOMMENDATIONS:")
    if stats.function_coverage < 90:
        print("  • Add type hints to function parameters and return values")
    if stats.method_coverage < 90:
        print("  • Add type hints to class methods")
    if stats.variable_coverage < 80:
        print("  • Consider adding type annotations to important variables")
    if stats.overall_coverage >= 90:
        print("  • Great job! Consider enabling stricter MyPy settings")
    print()


def main():
    """Main entry point."""
    if len(sys.argv) > 1:
        directory = Path(sys.argv[1])
    else:
        directory = Path("app")
    
    if not directory.exists():
        print(f"Error: Directory {directory} does not exist")
        sys.exit(1)
    
    print(f"Analyzing type coverage in: {directory}")
    print()
    
    stats, analyzer = analyze_directory(directory)
    print_coverage_report(stats, analyzer)
    
    # Exit with error code if coverage is too low
    if stats.overall_coverage < 70:
        print("❌ Type coverage is below 70% - consider adding more type hints")
        sys.exit(1)
    elif stats.overall_coverage < 90:
        print("⚠️  Type coverage is below 90% - room for improvement")
    else:
        print("✅ Excellent type coverage!")


if __name__ == "__main__":
    main()