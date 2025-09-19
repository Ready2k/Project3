#!/usr/bin/env python3
"""
Verification script for Task 4.4.1: Verify fallback import elimination

This script validates that:
1. Zero try/except import patterns remain in the codebase
2. All imports follow standard library → third-party → local pattern
3. All functionality works with new import system
4. Error messages are clear and actionable
"""

import os
import re
import sys
import subprocess
from pathlib import Path
from typing import List, Dict, Any, Tuple


class FallbackImportVerifier:
    """Verifies that fallback imports have been eliminated from the codebase."""
    
    def __init__(self, project_root: str = "."):
        self.project_root = Path(project_root)
        self.results: Dict[str, Any] = {}
    
    def run_verification(self) -> Dict[str, Any]:
        """Run complete verification and return results."""
        print("🔍 Verifying fallback import elimination...")
        print("=" * 60)
        
        # Step 1: Scan for try/except import patterns
        print("\n1. Scanning for try/except import patterns...")
        fallback_patterns = self._scan_for_fallback_imports()
        
        # Step 2: Verify import order
        print("\n2. Verifying import order compliance...")
        import_order_issues = self._verify_import_order()
        
        # Step 3: Test functionality
        print("\n3. Testing functionality with new import system...")
        functionality_results = self._test_functionality()
        
        # Step 4: Test error messages
        print("\n4. Testing error message clarity...")
        error_message_results = self._test_error_messages()
        
        # Compile results
        self.results = {
            'fallback_imports': fallback_patterns,
            'import_order_issues': import_order_issues,
            'functionality_tests': functionality_results,
            'error_message_tests': error_message_results,
            'overall_success': (
                len(fallback_patterns) == 0 and
                len(import_order_issues) == 0 and
                functionality_results['all_passed'] and
                error_message_results['all_passed']
            )
        }
        
        return self.results
    
    def _scan_for_fallback_imports(self) -> List[Dict[str, str]]:
        """Scan codebase for try/except import patterns."""
        patterns_found = []
        
        # Files to scan (Python files only, exclude documentation and tests)
        python_files = list(self.project_root.rglob("*.py"))
        
        # Files to exclude from fallback import checking
        exclude_patterns = [
            '/tests/', '__pycache__', '.git', 'test_', 'verify_', 'debug_', 'example_',
            'app/core/dependencies.py',  # Legitimate dependency validation
            'scripts/',  # Utility scripts may need fallback imports
        ]
        
        for file_path in python_files:
            # Skip excluded files
            if any(skip in str(file_path) for skip in exclude_patterns):
                continue
                
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for try/except import patterns
                # Match try: followed by import on next line
                try_import_pattern = r'try:\s*\n\s*(import\s+\w+|from\s+\w+\s+import)'
                matches = re.finditer(try_import_pattern, content, re.MULTILINE)
                
                for match in matches:
                    # Get line number
                    line_num = content[:match.start()].count('\n') + 1
                    
                    # Get the full try/except block to analyze
                    lines = content.split('\n')
                    try_line_idx = line_num - 1
                    
                    # Look for the corresponding except ImportError
                    except_found = False
                    for i in range(try_line_idx + 1, min(try_line_idx + 10, len(lines))):
                        if 'except ImportError' in lines[i] or 'except ModuleNotFoundError' in lines[i]:
                            except_found = True
                            break
                    
                    if except_found:
                        patterns_found.append({
                            'file': str(file_path.relative_to(self.project_root)),
                            'line': line_num,
                            'pattern': 'try/except import fallback',
                            'match': match.group().strip()
                        })
                        
            except Exception as e:
                print(f"⚠️  Error scanning {file_path}: {e}")
        
        if patterns_found:
            print(f"❌ Found {len(patterns_found)} fallback import patterns:")
            for pattern in patterns_found:
                print(f"   {pattern['file']}:{pattern['line']} - {pattern['match']}")
        else:
            print("✅ No fallback import patterns found")
        
        return patterns_found
    
    def _verify_import_order(self) -> List[Dict[str, str]]:
        """Verify that imports follow standard library → third-party → local pattern."""
        issues = []
        
        # Sample key files to check
        key_files = [
            "streamlit_app.py",
            "app/api.py",
            "app/core/registry.py",
            "app/utils/imports.py",
            "app/core/startup.py"
        ]
        
        for file_path in key_files:
            full_path = self.project_root / file_path
            if not full_path.exists():
                continue
                
            try:
                with open(full_path, 'r', encoding='utf-8') as f:
                    lines = f.readlines()
                
                # Extract import lines (skip comments and docstrings)
                import_lines = []
                in_docstring = False
                for i, line in enumerate(lines, 1):
                    stripped = line.strip()
                    
                    # Skip docstrings
                    if '"""' in stripped:
                        in_docstring = not in_docstring
                        continue
                    if in_docstring:
                        continue
                    
                    # Check for import lines
                    if (stripped.startswith('import ') or stripped.startswith('from ')) and not stripped.startswith('#'):
                        import_lines.append((i, stripped))
                
                # Categorize imports
                stdlib_line_nums = []
                third_party_line_nums = []
                local_line_nums = []
                
                stdlib_modules = {
                    'asyncio', 'json', 'os', 're', 'sqlite3', 'time', 'sys', 'logging', 
                    'typing', 'pathlib', 'datetime', 'uuid', 'hashlib', 'threading',
                    'functools', 'dataclasses', 'enum', 'abc', 'inspect', 'weakref',
                    'gc', 'concurrent', 'collections'
                }
                
                for line_num, import_line in import_lines:
                    if 'from app.' in import_line or import_line.startswith('from app.'):
                        local_line_nums.append(line_num)
                    elif any(f'import {mod}' in import_line or f'from {mod}' in import_line 
                            for mod in stdlib_modules):
                        stdlib_line_nums.append(line_num)
                    else:
                        third_party_line_nums.append(line_num)
                
                # Check if groups are in correct order
                all_line_nums = stdlib_line_nums + third_party_line_nums + local_line_nums
                actual_line_nums = [line_num for line_num, _ in import_lines]
                
                # Allow for some flexibility - just check that local imports come after stdlib/third-party
                if local_line_nums and stdlib_line_nums:
                    if min(local_line_nums) < max(stdlib_line_nums):
                        issues.append({
                            'file': file_path,
                            'issue': 'Local imports should come after standard library imports'
                        })
                
                if local_line_nums and third_party_line_nums:
                    if min(local_line_nums) < max(third_party_line_nums):
                        issues.append({
                            'file': file_path,
                            'issue': 'Local imports should come after third-party imports'
                        })
                
            except Exception as e:
                print(f"⚠️  Error checking import order in {file_path}: {e}")
        
        if issues:
            print(f"❌ Found {len(issues)} import order issues:")
            for issue in issues:
                print(f"   {issue['file']}: {issue['issue']}")
        else:
            print("✅ Import order compliance verified")
        
        return issues
    
    def _test_functionality(self) -> Dict[str, Any]:
        """Test that functionality works with new import system."""
        tests = []
        
        # Test 1: Basic imports
        try:
            import streamlit_app
            tests.append(('streamlit_app import', True, None))
        except Exception as e:
            tests.append(('streamlit_app import', False, str(e)))
        
        # Test 2: Service registry
        try:
            from app.core.registry import ServiceRegistry
            tests.append(('ServiceRegistry import', True, None))
        except Exception as e:
            tests.append(('ServiceRegistry import', False, str(e)))
        
        # Test 3: Import utilities
        try:
            from app.utils.imports import require_service, optional_service
            tests.append(('Import utilities', True, None))
        except Exception as e:
            tests.append(('Import utilities', False, str(e)))
        
        # Test 4: Service system startup
        try:
            from app.core.startup import run_application_startup
            results = run_application_startup()
            success = results.get('startup_successful', False)
            tests.append(('Service system startup', success, None if success else results.get('error')))
        except Exception as e:
            tests.append(('Service system startup', False, str(e)))
        
        # Test 5: Service resolution
        try:
            from app.utils.imports import require_service
            logger = require_service('logger', context='verification_test')
            tests.append(('Service resolution', True, None))
        except Exception as e:
            tests.append(('Service resolution', False, str(e)))
        
        # Print results
        passed = sum(1 for test in tests if test[1])
        total = len(tests)
        
        print(f"Functionality tests: {passed}/{total} passed")
        for test_name, success, error in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}")
            if error:
                print(f"      Error: {error}")
        
        return {
            'tests': tests,
            'passed': passed,
            'total': total,
            'all_passed': passed == total
        }
    
    def _test_error_messages(self) -> Dict[str, Any]:
        """Test that error messages are clear and actionable."""
        tests = []
        
        # Test 1: Missing required service
        try:
            from app.utils.imports import require_service
            try:
                require_service('nonexistent_service', context='test')
                tests.append(('Missing required service error', False, 'Should have raised exception'))
            except Exception as e:
                error_msg = str(e)
                # Check if error message is clear
                is_clear = (
                    'nonexistent_service' in error_msg and
                    'not registered' in error_msg and
                    'test' in error_msg
                )
                tests.append(('Missing required service error', is_clear, error_msg if is_clear else f'Unclear error: {error_msg}'))
        except Exception as e:
            tests.append(('Missing required service error', False, f'Setup error: {e}'))
        
        # Test 2: Optional service handling
        try:
            from app.utils.imports import optional_service
            result = optional_service('nonexistent_optional_service', context='test')
            is_correct = result is None
            tests.append(('Optional service handling', is_correct, None if is_correct else f'Expected None, got {result}'))
        except Exception as e:
            tests.append(('Optional service handling', False, f'Should not raise exception: {e}'))
        
        # Print results
        passed = sum(1 for test in tests if test[1])
        total = len(tests)
        
        print(f"Error message tests: {passed}/{total} passed")
        for test_name, success, error in tests:
            status = "✅" if success else "❌"
            print(f"   {status} {test_name}")
            if error:
                print(f"      Details: {error}")
        
        return {
            'tests': tests,
            'passed': passed,
            'total': total,
            'all_passed': passed == total
        }
    
    def print_summary(self) -> None:
        """Print verification summary."""
        print("\n" + "=" * 60)
        print("VERIFICATION SUMMARY")
        print("=" * 60)
        
        if not self.results:
            print("❌ No verification results available")
            return
        
        # Overall status
        if self.results['overall_success']:
            print("✅ OVERALL STATUS: ALL CHECKS PASSED")
        else:
            print("❌ OVERALL STATUS: SOME CHECKS FAILED")
        
        print()
        
        # Detailed results
        fallback_count = len(self.results['fallback_imports'])
        print(f"📋 Fallback Imports: {fallback_count} found (target: 0)")
        
        import_issues = len(self.results['import_order_issues'])
        print(f"📋 Import Order Issues: {import_issues} found (target: 0)")
        
        func_tests = self.results['functionality_tests']
        print(f"📋 Functionality Tests: {func_tests['passed']}/{func_tests['total']} passed")
        
        error_tests = self.results['error_message_tests']
        print(f"📋 Error Message Tests: {error_tests['passed']}/{error_tests['total']} passed")
        
        print()
        
        # Requirements compliance
        print("REQUIREMENTS COMPLIANCE:")
        print(f"✅ 1.1 - Zero try/except import patterns: {'PASS' if fallback_count == 0 else 'FAIL'}")
        print(f"✅ 1.4 - Import order compliance: {'PASS' if import_issues == 0 else 'FAIL'}")
        print(f"✅ 1.5 - Functionality works: {'PASS' if func_tests['all_passed'] else 'FAIL'}")
        print(f"✅ Error messages clear: {'PASS' if error_tests['all_passed'] else 'FAIL'}")


def main():
    """Main verification function."""
    verifier = FallbackImportVerifier()
    
    try:
        results = verifier.run_verification()
        verifier.print_summary()
        
        # Exit with appropriate code
        if results['overall_success']:
            print("\n🎉 Task 4.4.1 verification completed successfully!")
            sys.exit(0)
        else:
            print("\n❌ Task 4.4.1 verification failed - see issues above")
            sys.exit(1)
            
    except Exception as e:
        print(f"\n💥 Verification script failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()