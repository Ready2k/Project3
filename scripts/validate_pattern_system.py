#!/usr/bin/env python3
"""
Enhanced pattern system validation script.

This script validates the enhanced pattern system including pattern loading,
schema validation, and pattern enhancement functionality.
"""

import sys
import json
import time
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass
import traceback

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.logger import app_logger
from app.pattern.enhanced_loader import EnhancedPatternLoader
from app.pattern.dynamic_schema_loader import DynamicSchemaLoader
from app.services.pattern_enhancement_service import PatternEnhancementService


@dataclass
class ValidationResult:
    """Result of a validation test."""
    test_name: str
    success: bool
    message: str
    details: Optional[Dict[str, Any]] = None
    execution_time: float = 0.0
    error: Optional[str] = None


class PatternSystemValidator:
    """
    Comprehensive validator for the enhanced pattern system.
    
    Tests pattern loading, schema validation, enhancement functionality,
    and error handling across all pattern types.
    """
    
    def __init__(self, project_root: Path = None):
        """
        Initialize the pattern system validator.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.data_dir = self.project_root / "data"
        self.patterns_dir = self.data_dir / "patterns"
        self.results: List[ValidationResult] = []
        
        # Initialize components
        self.enhanced_loader = None
        self.schema_loader = None
        self.enhancement_service = None
    
    def setup_components(self) -> ValidationResult:
        """Set up pattern system components."""
        start_time = time.time()
        
        try:
            # Initialize enhanced pattern loader
            self.enhanced_loader = EnhancedPatternLoader(str(self.patterns_dir))
            
            # Initialize dynamic schema loader
            self.schema_loader = DynamicSchemaLoader()
            
            # Initialize pattern enhancement service
            self.enhancement_service = PatternEnhancementService()
            
            return ValidationResult(
                test_name="component_setup",
                success=True,
                message="All pattern system components initialized successfully",
                execution_time=time.time() - start_time
            )
            
        except Exception as e:
            return ValidationResult(
                test_name="component_setup",
                success=False,
                message=f"Failed to initialize components: {e}",
                error=traceback.format_exc(),
                execution_time=time.time() - start_time
            )
    
    def validate_pattern_loading(self) -> List[ValidationResult]:
        """Validate pattern loading for all pattern types."""
        results = []
        
        # Test loading different pattern types
        pattern_types = ["PAT", "APAT", "EPAT"]
        
        for pattern_type in pattern_types:
            start_time = time.time()
            
            try:
                # Find patterns of this type
                pattern_files = list(self.patterns_dir.glob(f"{pattern_type}-*.json"))
                
                if not pattern_files:
                    results.append(ValidationResult(
                        test_name=f"load_{pattern_type.lower()}_patterns",
                        success=False,
                        message=f"No {pattern_type} patterns found",
                        details={"pattern_type": pattern_type, "files_found": 0},
                        execution_time=time.time() - start_time
                    ))
                    continue
                
                loaded_patterns = []
                failed_patterns = []
                
                for pattern_file in pattern_files:
                    try:
                        pattern = self.enhanced_loader.load_pattern(str(pattern_file))
                        if pattern:
                            loaded_patterns.append(pattern_file.name)
                        else:
                            failed_patterns.append(pattern_file.name)
                    except Exception as e:
                        failed_patterns.append(f"{pattern_file.name}: {e}")
                
                success = len(failed_patterns) == 0
                message = f"Loaded {len(loaded_patterns)}/{len(pattern_files)} {pattern_type} patterns"
                
                if failed_patterns:
                    message += f", {len(failed_patterns)} failed"
                
                results.append(ValidationResult(
                    test_name=f"load_{pattern_type.lower()}_patterns",
                    success=success,
                    message=message,
                    details={
                        "pattern_type": pattern_type,
                        "total_files": len(pattern_files),
                        "loaded_successfully": len(loaded_patterns),
                        "failed_to_load": len(failed_patterns),
                        "loaded_patterns": loaded_patterns,
                        "failed_patterns": failed_patterns[:5]  # Limit to first 5
                    },
                    execution_time=time.time() - start_time
                ))
                
            except Exception as e:
                results.append(ValidationResult(
                    test_name=f"load_{pattern_type.lower()}_patterns",
                    success=False,
                    message=f"Failed to load {pattern_type} patterns: {e}",
                    error=traceback.format_exc(),
                    execution_time=time.time() - start_time
                ))
        
        return results
    
    def validate_schema_validation(self) -> List[ValidationResult]:
        """Validate schema validation for enhanced patterns."""
        results = []
        
        # Test dynamic schema loading
        start_time = time.time()
        
        try:
            schema = self.schema_loader.load_schema()
            
            if schema:
                results.append(ValidationResult(
                    test_name="dynamic_schema_loading",
                    success=True,
                    message="Dynamic schema loaded successfully",
                    details={
                        "schema_keys": list(schema.keys()) if isinstance(schema, dict) else None,
                        "schema_type": type(schema).__name__
                    },
                    execution_time=time.time() - start_time
                ))
            else:
                results.append(ValidationResult(
                    test_name="dynamic_schema_loading",
                    success=False,
                    message="Dynamic schema loading returned None",
                    execution_time=time.time() - start_time
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                test_name="dynamic_schema_loading",
                success=False,
                message=f"Dynamic schema loading failed: {e}",
                error=traceback.format_exc(),
                execution_time=time.time() - start_time
            ))
        
        # Test schema validation with actual patterns
        start_time = time.time()
        
        try:
            # Find APAT patterns for validation testing
            apat_files = list(self.patterns_dir.glob("APAT-*.json"))
            
            if apat_files:
                validation_results = []
                
                for pattern_file in apat_files[:3]:  # Test first 3 patterns
                    try:
                        with open(pattern_file, 'r', encoding='utf-8') as f:
                            pattern_data = json.load(f)
                        
                        # Validate using enhanced loader
                        is_valid = self.enhanced_loader.validate_pattern(pattern_data)
                        validation_results.append({
                            "file": pattern_file.name,
                            "valid": is_valid
                        })
                        
                    except Exception as e:
                        validation_results.append({
                            "file": pattern_file.name,
                            "valid": False,
                            "error": str(e)
                        })
                
                valid_count = len([r for r in validation_results if r.get("valid", False)])
                total_count = len(validation_results)
                
                results.append(ValidationResult(
                    test_name="schema_validation",
                    success=valid_count == total_count,
                    message=f"Schema validation: {valid_count}/{total_count} patterns valid",
                    details={
                        "validation_results": validation_results,
                        "valid_patterns": valid_count,
                        "total_patterns": total_count
                    },
                    execution_time=time.time() - start_time
                ))
            else:
                results.append(ValidationResult(
                    test_name="schema_validation",
                    success=False,
                    message="No APAT patterns found for schema validation testing",
                    execution_time=time.time() - start_time
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                test_name="schema_validation",
                success=False,
                message=f"Schema validation testing failed: {e}",
                error=traceback.format_exc(),
                execution_time=time.time() - start_time
            ))
        
        return results
    
    def validate_pattern_enhancement(self) -> List[ValidationResult]:
        """Validate pattern enhancement functionality."""
        results = []
        
        # Test pattern enhancement service
        start_time = time.time()
        
        try:
            # Create a test pattern for enhancement
            test_pattern = {
                "pattern_id": "TEST-001",
                "name": "Test Pattern",
                "description": "A test pattern for validation",
                "feasibility": {
                    "status": "Highly Feasible",
                    "score": 85,
                    "reasoning": "Test reasoning"
                },
                "tech_stack": ["Python", "FastAPI"],
                "pattern_type": ["api_development"],
                "compliance_requirements": ["GDPR"]
            }
            
            # Test enhancement
            enhanced_pattern = self.enhancement_service.enhance_pattern(
                test_pattern, 
                session_id="validation_test"
            )
            
            if enhanced_pattern:
                # Check if enhancement added expected fields
                has_autonomy = "autonomy_assessment" in enhanced_pattern
                has_reasoning = "reasoning_complexity" in enhanced_pattern
                has_monitoring = "monitoring_capabilities" in enhanced_pattern
                
                enhancement_score = sum([has_autonomy, has_reasoning, has_monitoring])
                
                results.append(ValidationResult(
                    test_name="pattern_enhancement",
                    success=enhancement_score >= 2,  # At least 2 out of 3 enhancements
                    message=f"Pattern enhancement added {enhancement_score}/3 expected fields",
                    details={
                        "original_keys": list(test_pattern.keys()),
                        "enhanced_keys": list(enhanced_pattern.keys()),
                        "has_autonomy_assessment": has_autonomy,
                        "has_reasoning_complexity": has_reasoning,
                        "has_monitoring_capabilities": has_monitoring,
                        "enhancement_score": enhancement_score
                    },
                    execution_time=time.time() - start_time
                ))
            else:
                results.append(ValidationResult(
                    test_name="pattern_enhancement",
                    success=False,
                    message="Pattern enhancement returned None",
                    execution_time=time.time() - start_time
                ))
                
        except Exception as e:
            results.append(ValidationResult(
                test_name="pattern_enhancement",
                success=False,
                message=f"Pattern enhancement failed: {e}",
                error=traceback.format_exc(),
                execution_time=time.time() - start_time
            ))
        
        return results
    
    def validate_error_handling(self) -> List[ValidationResult]:
        """Validate error handling in pattern operations."""
        results = []
        
        # Test loading invalid pattern
        start_time = time.time()
        
        try:
            # Create invalid pattern data
            invalid_pattern = {"invalid": "data", "missing": "required_fields"}
            
            # Test that validation properly rejects invalid patterns
            is_valid = self.enhanced_loader.validate_pattern(invalid_pattern)
            
            results.append(ValidationResult(
                test_name="invalid_pattern_rejection",
                success=not is_valid,  # Should be False for invalid pattern
                message=f"Invalid pattern validation: {'rejected' if not is_valid else 'accepted'}",
                details={"validation_result": is_valid},
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            # Exception during validation is also acceptable
            results.append(ValidationResult(
                test_name="invalid_pattern_rejection",
                success=True,
                message=f"Invalid pattern properly raised exception: {type(e).__name__}",
                details={"exception_type": type(e).__name__, "exception_message": str(e)},
                execution_time=time.time() - start_time
            ))
        
        # Test loading non-existent file
        start_time = time.time()
        
        try:
            non_existent_file = self.patterns_dir / "NON-EXISTENT-999.json"
            pattern = self.enhanced_loader.load_pattern(str(non_existent_file))
            
            results.append(ValidationResult(
                test_name="non_existent_file_handling",
                success=pattern is None,  # Should return None for non-existent file
                message=f"Non-existent file handling: {'proper' if pattern is None else 'improper'}",
                details={"result": pattern},
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            # Exception is also acceptable for non-existent files
            results.append(ValidationResult(
                test_name="non_existent_file_handling",
                success=True,
                message=f"Non-existent file properly raised exception: {type(e).__name__}",
                details={"exception_type": type(e).__name__, "exception_message": str(e)},
                execution_time=time.time() - start_time
            ))
        
        return results
    
    def validate_edge_cases(self) -> List[ValidationResult]:
        """Validate edge cases and boundary conditions."""
        results = []
        
        # Test empty pattern directory handling
        start_time = time.time()
        
        try:
            # Create temporary empty directory
            empty_dir = self.project_root / "temp_empty_patterns"
            empty_dir.mkdir(exist_ok=True)
            
            # Test loading from empty directory
            patterns = self.enhanced_loader.load_all_patterns(str(empty_dir))
            
            # Clean up
            empty_dir.rmdir()
            
            results.append(ValidationResult(
                test_name="empty_directory_handling",
                success=isinstance(patterns, (list, dict)) and len(patterns) == 0,
                message=f"Empty directory handling: returned {type(patterns).__name__} with {len(patterns)} items",
                details={"result_type": type(patterns).__name__, "result_length": len(patterns)},
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            results.append(ValidationResult(
                test_name="empty_directory_handling",
                success=False,
                message=f"Empty directory handling failed: {e}",
                error=traceback.format_exc(),
                execution_time=time.time() - start_time
            ))
        
        # Test large pattern handling
        start_time = time.time()
        
        try:
            # Create a large pattern for testing
            large_pattern = {
                "pattern_id": "LARGE-001",
                "name": "Large Test Pattern",
                "description": "A" * 10000,  # Large description
                "feasibility": {"status": "Feasible", "score": 75},
                "tech_stack": ["Tech" + str(i) for i in range(100)],  # Large tech stack
                "large_field": ["Item" + str(i) for i in range(1000)]  # Large array
            }
            
            # Test validation of large pattern
            is_valid = self.enhanced_loader.validate_pattern(large_pattern)
            
            results.append(ValidationResult(
                test_name="large_pattern_handling",
                success=True,  # Should handle large patterns gracefully
                message=f"Large pattern handling: validation {'passed' if is_valid else 'failed'}",
                details={
                    "pattern_size_bytes": len(json.dumps(large_pattern)),
                    "validation_result": is_valid
                },
                execution_time=time.time() - start_time
            ))
            
        except Exception as e:
            results.append(ValidationResult(
                test_name="large_pattern_handling",
                success=False,
                message=f"Large pattern handling failed: {e}",
                error=traceback.format_exc(),
                execution_time=time.time() - start_time
            ))
        
        return results
    
    def run_all_validations(self) -> Tuple[List[ValidationResult], Dict[str, Any]]:
        """Run all validation tests and return results with summary."""
        app_logger.info("Starting comprehensive pattern system validation...")
        
        start_time = time.time()
        all_results = []
        
        # Setup components
        setup_result = self.setup_components()
        all_results.append(setup_result)
        
        if not setup_result.success:
            app_logger.error("Component setup failed, skipping remaining tests")
            return all_results, self._generate_summary(all_results, time.time() - start_time)
        
        # Run validation tests
        test_suites = [
            ("Pattern Loading", self.validate_pattern_loading),
            ("Schema Validation", self.validate_schema_validation),
            ("Pattern Enhancement", self.validate_pattern_enhancement),
            ("Error Handling", self.validate_error_handling),
            ("Edge Cases", self.validate_edge_cases),
        ]
        
        for suite_name, test_func in test_suites:
            app_logger.info(f"Running {suite_name} tests...")
            try:
                suite_results = test_func()
                all_results.extend(suite_results)
                
                passed = len([r for r in suite_results if r.success])
                total = len(suite_results)
                app_logger.info(f"{suite_name}: {passed}/{total} tests passed")
                
            except Exception as e:
                app_logger.error(f"{suite_name} test suite failed: {e}")
                all_results.append(ValidationResult(
                    test_name=f"{suite_name.lower().replace(' ', '_')}_suite",
                    success=False,
                    message=f"Test suite failed: {e}",
                    error=traceback.format_exc()
                ))
        
        total_time = time.time() - start_time
        summary = self._generate_summary(all_results, total_time)
        
        return all_results, summary
    
    def _generate_summary(self, results: List[ValidationResult], total_time: float) -> Dict[str, Any]:
        """Generate a summary of validation results."""
        total_tests = len(results)
        passed_tests = len([r for r in results if r.success])
        failed_tests = total_tests - passed_tests
        
        # Calculate success rate
        success_rate = (passed_tests / total_tests * 100) if total_tests > 0 else 0
        
        # Get failed test details
        failed_test_names = [r.test_name for r in results if not r.success]
        
        # Calculate average execution time
        avg_execution_time = sum(r.execution_time for r in results) / max(total_tests, 1)
        
        return {
            "total_tests": total_tests,
            "passed_tests": passed_tests,
            "failed_tests": failed_tests,
            "success_rate": success_rate,
            "total_execution_time": total_time,
            "average_test_time": avg_execution_time,
            "failed_test_names": failed_test_names,
            "overall_status": "PASS" if failed_tests == 0 else "FAIL"
        }
    
    def generate_report(self, results: List[ValidationResult], summary: Dict[str, Any]) -> str:
        """Generate a formatted validation report."""
        report_lines = [
            "=" * 80,
            "ENHANCED PATTERN SYSTEM VALIDATION REPORT",
            "=" * 80,
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
            f"Overall Status: {summary['overall_status']}",
            f"Success Rate: {summary['success_rate']:.1f}%",
            "",
            "SUMMARY:",
            f"  Total Tests: {summary['total_tests']}",
            f"  Passed: {summary['passed_tests']}",
            f"  Failed: {summary['failed_tests']}",
            f"  Total Time: {summary['total_execution_time']:.2f}s",
            f"  Average Test Time: {summary['average_test_time']:.3f}s",
            "",
            "DETAILED RESULTS:",
        ]
        
        for result in results:
            status_icon = "✅" if result.success else "❌"
            report_lines.extend([
                f"  {status_icon} {result.test_name}:",
                f"    Status: {'PASS' if result.success else 'FAIL'}",
                f"    Message: {result.message}",
                f"    Time: {result.execution_time:.3f}s",
            ])
            
            if result.error:
                report_lines.append(f"    Error: {result.error.split(chr(10))[0]}")  # First line only
            
            report_lines.append("")
        
        if summary['failed_test_names']:
            report_lines.extend([
                "FAILED TESTS:",
                *[f"  • {name}" for name in summary['failed_test_names']],
                ""
            ])
        
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)


def main():
    """Main entry point for the pattern system validator."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Validate the enhanced pattern system")
    parser.add_argument("--output", "-o", type=Path, help="Output file for the report")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    validator = PatternSystemValidator()
    results, summary = validator.run_all_validations()
    
    if args.json:
        # Output JSON report
        json_report = {
            "summary": summary,
            "results": [
                {
                    "test_name": r.test_name,
                    "success": r.success,
                    "message": r.message,
                    "execution_time": r.execution_time,
                    "details": r.details,
                    "error": r.error
                }
                for r in results
            ]
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2)
        else:
            print(json.dumps(json_report, indent=2))
    else:
        # Output formatted text report
        report_text = validator.generate_report(results, summary)
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                f.write(report_text)
            app_logger.info(f"Validation report saved to {args.output}")
        else:
            print(report_text)
    
    # Exit with appropriate code
    if summary['overall_status'] == "FAIL":
        sys.exit(1)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()