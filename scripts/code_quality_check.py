#!/usr/bin/env python3
"""
Code quality monitoring and reporting script.

This script runs various code quality checks and generates a comprehensive
report on code quality metrics, complexity, and potential issues.
"""

import subprocess
import json
import sys
import time
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import argparse

# Add the app directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from app.utils.logger import app_logger


@dataclass
class QualityMetric:
    """A single code quality metric."""
    name: str
    value: Any
    status: str  # "pass", "warning", "error"
    message: str
    details: Optional[Dict[str, Any]] = None


@dataclass
class QualityReport:
    """Comprehensive code quality report."""
    timestamp: float
    overall_score: float
    metrics: List[QualityMetric]
    summary: Dict[str, Any]
    recommendations: List[str]


class CodeQualityChecker:
    """
    Comprehensive code quality checker and reporter.
    
    Runs various code quality tools and aggregates results into
    a comprehensive quality report.
    """
    
    def __init__(self, project_root: Path = None):
        """
        Initialize the code quality checker.
        
        Args:
            project_root: Root directory of the project
        """
        self.project_root = project_root or Path(__file__).parent.parent
        self.metrics: List[QualityMetric] = []
        
    def run_ruff_check(self) -> QualityMetric:
        """Run Ruff linting and return metrics."""
        try:
            # Run ruff check with JSON output
            result = subprocess.run(
                ["ruff", "check", ".", "--format=json"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.returncode == 0:
                return QualityMetric(
                    name="ruff_linting",
                    value=0,
                    status="pass",
                    message="No linting issues found",
                    details={"violations": []}
                )
            else:
                # Parse JSON output
                violations = []
                if result.stdout:
                    try:
                        violations = json.loads(result.stdout)
                    except json.JSONDecodeError:
                        pass
                
                return QualityMetric(
                    name="ruff_linting",
                    value=len(violations),
                    status="warning" if len(violations) < 50 else "error",
                    message=f"Found {len(violations)} linting issues",
                    details={"violations": violations[:10]}  # Limit to first 10
                )
                
        except subprocess.TimeoutExpired:
            return QualityMetric(
                name="ruff_linting",
                value=-1,
                status="error",
                message="Ruff check timed out",
                details={"error": "timeout"}
            )
        except Exception as e:
            return QualityMetric(
                name="ruff_linting",
                value=-1,
                status="error",
                message=f"Ruff check failed: {e}",
                details={"error": str(e)}
            )
    
    def run_mypy_check(self) -> QualityMetric:
        """Run MyPy type checking and return metrics."""
        try:
            result = subprocess.run(
                ["mypy", "app", "--config-file=mypy.ini", "--json-report", "mypy-report"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=120
            )
            
            # Count type errors
            error_count = result.stdout.count("error:")
            
            if result.returncode == 0:
                return QualityMetric(
                    name="type_checking",
                    value=0,
                    status="pass",
                    message="No type checking issues found",
                    details={"errors": 0}
                )
            else:
                return QualityMetric(
                    name="type_checking",
                    value=error_count,
                    status="warning" if error_count < 20 else "error",
                    message=f"Found {error_count} type checking issues",
                    details={"errors": error_count, "output": result.stdout[:1000]}
                )
                
        except subprocess.TimeoutExpired:
            return QualityMetric(
                name="type_checking",
                value=-1,
                status="error",
                message="MyPy check timed out",
                details={"error": "timeout"}
            )
        except Exception as e:
            return QualityMetric(
                name="type_checking",
                value=-1,
                status="error",
                message=f"MyPy check failed: {e}",
                details={"error": str(e)}
            )
    
    def run_bandit_security_check(self) -> QualityMetric:
        """Run Bandit security analysis and return metrics."""
        try:
            result = subprocess.run(
                ["bandit", "-r", "app", "-f", "json", "-ll"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=60
            )
            
            if result.stdout:
                try:
                    report = json.loads(result.stdout)
                    high_issues = len([i for i in report.get("results", []) if i.get("issue_severity") == "HIGH"])
                    medium_issues = len([i for i in report.get("results", []) if i.get("issue_severity") == "MEDIUM"])
                    total_issues = len(report.get("results", []))
                    
                    if total_issues == 0:
                        status = "pass"
                        message = "No security issues found"
                    elif high_issues > 0:
                        status = "error"
                        message = f"Found {high_issues} high-severity security issues"
                    elif medium_issues > 5:
                        status = "warning"
                        message = f"Found {medium_issues} medium-severity security issues"
                    else:
                        status = "pass"
                        message = f"Found {total_issues} low-severity security issues"
                    
                    return QualityMetric(
                        name="security_analysis",
                        value=total_issues,
                        status=status,
                        message=message,
                        details={
                            "high_severity": high_issues,
                            "medium_severity": medium_issues,
                            "total_issues": total_issues
                        }
                    )
                except json.JSONDecodeError:
                    pass
            
            return QualityMetric(
                name="security_analysis",
                value=0,
                status="pass",
                message="No security issues found",
                details={"issues": 0}
            )
            
        except subprocess.TimeoutExpired:
            return QualityMetric(
                name="security_analysis",
                value=-1,
                status="error",
                message="Bandit security check timed out",
                details={"error": "timeout"}
            )
        except Exception as e:
            return QualityMetric(
                name="security_analysis",
                value=-1,
                status="error",
                message=f"Bandit security check failed: {e}",
                details={"error": str(e)}
            )
    
    def analyze_code_complexity(self) -> QualityMetric:
        """Analyze code complexity using radon."""
        try:
            # Try to run radon for complexity analysis
            result = subprocess.run(
                ["radon", "cc", "app", "-j"],
                cwd=self.project_root,
                capture_output=True,
                text=True,
                timeout=30
            )
            
            if result.returncode == 0 and result.stdout:
                try:
                    complexity_data = json.loads(result.stdout)
                    
                    # Calculate average complexity
                    total_complexity = 0
                    function_count = 0
                    high_complexity_functions = []
                    
                    for file_path, functions in complexity_data.items():
                        for func in functions:
                            complexity = func.get("complexity", 0)
                            total_complexity += complexity
                            function_count += 1
                            
                            if complexity > 10:  # High complexity threshold
                                high_complexity_functions.append({
                                    "file": file_path,
                                    "function": func.get("name", "unknown"),
                                    "complexity": complexity
                                })
                    
                    avg_complexity = total_complexity / max(function_count, 1)
                    
                    if avg_complexity < 3:
                        status = "pass"
                        message = f"Good code complexity (avg: {avg_complexity:.1f})"
                    elif avg_complexity < 5:
                        status = "warning"
                        message = f"Moderate code complexity (avg: {avg_complexity:.1f})"
                    else:
                        status = "error"
                        message = f"High code complexity (avg: {avg_complexity:.1f})"
                    
                    return QualityMetric(
                        name="code_complexity",
                        value=avg_complexity,
                        status=status,
                        message=message,
                        details={
                            "average_complexity": avg_complexity,
                            "function_count": function_count,
                            "high_complexity_functions": high_complexity_functions[:5]
                        }
                    )
                except json.JSONDecodeError:
                    pass
            
            # Fallback: simple line count analysis
            python_files = list(self.project_root.glob("app/**/*.py"))
            total_lines = 0
            large_files = []
            
            for file_path in python_files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        lines = len(f.readlines())
                        total_lines += lines
                        
                        if lines > 500:  # Large file threshold
                            large_files.append({
                                "file": str(file_path.relative_to(self.project_root)),
                                "lines": lines
                            })
                except Exception:
                    continue
            
            avg_file_size = total_lines / max(len(python_files), 1)
            
            return QualityMetric(
                name="code_complexity",
                value=avg_file_size,
                status="warning" if len(large_files) > 5 else "pass",
                message=f"Average file size: {avg_file_size:.0f} lines",
                details={
                    "average_file_size": avg_file_size,
                    "total_files": len(python_files),
                    "large_files": large_files[:5]
                }
            )
            
        except Exception as e:
            return QualityMetric(
                name="code_complexity",
                value=-1,
                status="error",
                message=f"Complexity analysis failed: {e}",
                details={"error": str(e)}
            )
    
    def check_test_coverage(self) -> QualityMetric:
        """Check test coverage if available."""
        try:
            # Look for coverage report
            coverage_file = self.project_root / ".coverage"
            if coverage_file.exists():
                result = subprocess.run(
                    ["coverage", "report", "--format=json"],
                    cwd=self.project_root,
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                if result.returncode == 0 and result.stdout:
                    try:
                        coverage_data = json.loads(result.stdout)
                        total_coverage = coverage_data.get("totals", {}).get("percent_covered", 0)
                        
                        if total_coverage >= 80:
                            status = "pass"
                            message = f"Good test coverage: {total_coverage:.1f}%"
                        elif total_coverage >= 60:
                            status = "warning"
                            message = f"Moderate test coverage: {total_coverage:.1f}%"
                        else:
                            status = "error"
                            message = f"Low test coverage: {total_coverage:.1f}%"
                        
                        return QualityMetric(
                            name="test_coverage",
                            value=total_coverage,
                            status=status,
                            message=message,
                            details={"coverage_percent": total_coverage}
                        )
                    except json.JSONDecodeError:
                        pass
            
            # No coverage data available
            return QualityMetric(
                name="test_coverage",
                value=0,
                status="warning",
                message="No test coverage data available",
                details={"coverage_available": False}
            )
            
        except Exception as e:
            return QualityMetric(
                name="test_coverage",
                value=-1,
                status="error",
                message=f"Coverage check failed: {e}",
                details={"error": str(e)}
            )
    
    def run_all_checks(self) -> QualityReport:
        """Run all quality checks and generate a comprehensive report."""
        app_logger.info("Starting comprehensive code quality analysis...")
        
        start_time = time.time()
        
        # Run all checks
        checks = [
            ("Ruff Linting", self.run_ruff_check),
            ("Type Checking", self.run_mypy_check),
            ("Security Analysis", self.run_bandit_security_check),
            ("Code Complexity", self.analyze_code_complexity),
            ("Test Coverage", self.check_test_coverage),
        ]
        
        metrics = []
        for check_name, check_func in checks:
            app_logger.info(f"Running {check_name}...")
            try:
                metric = check_func()
                metrics.append(metric)
                app_logger.info(f"{check_name}: {metric.status} - {metric.message}")
            except Exception as e:
                app_logger.error(f"{check_name} failed: {e}")
                metrics.append(QualityMetric(
                    name=check_name.lower().replace(" ", "_"),
                    value=-1,
                    status="error",
                    message=f"Check failed: {e}",
                    details={"error": str(e)}
                ))
        
        # Calculate overall score
        total_score = 0
        max_score = 0
        
        for metric in metrics:
            max_score += 100
            if metric.status == "pass":
                total_score += 100
            elif metric.status == "warning":
                total_score += 60
            elif metric.status == "error":
                total_score += 20
            # Failed checks get 0 points
        
        overall_score = (total_score / max_score * 100) if max_score > 0 else 0
        
        # Generate recommendations
        recommendations = []
        
        for metric in metrics:
            if metric.status == "error":
                recommendations.append(f"Fix critical issues in {metric.name}: {metric.message}")
            elif metric.status == "warning":
                recommendations.append(f"Improve {metric.name}: {metric.message}")
        
        if overall_score < 70:
            recommendations.append("Overall code quality needs significant improvement")
        elif overall_score < 85:
            recommendations.append("Code quality is good but has room for improvement")
        
        # Create summary
        summary = {
            "total_checks": len(metrics),
            "passed_checks": len([m for m in metrics if m.status == "pass"]),
            "warning_checks": len([m for m in metrics if m.status == "warning"]),
            "failed_checks": len([m for m in metrics if m.status == "error"]),
            "execution_time": time.time() - start_time
        }
        
        return QualityReport(
            timestamp=time.time(),
            overall_score=overall_score,
            metrics=metrics,
            summary=summary,
            recommendations=recommendations
        )
    
    def generate_report(self, report: QualityReport, output_file: Optional[Path] = None) -> str:
        """Generate a formatted quality report."""
        report_lines = [
            "=" * 80,
            "CODE QUALITY REPORT",
            "=" * 80,
            f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S', time.localtime(report.timestamp))}",
            f"Overall Score: {report.overall_score:.1f}/100",
            "",
            "SUMMARY:",
            f"  Total Checks: {report.summary['total_checks']}",
            f"  Passed: {report.summary['passed_checks']}",
            f"  Warnings: {report.summary['warning_checks']}",
            f"  Failed: {report.summary['failed_checks']}",
            f"  Execution Time: {report.summary['execution_time']:.1f}s",
            "",
            "DETAILED RESULTS:",
        ]
        
        for metric in report.metrics:
            status_icon = {"pass": "✅", "warning": "⚠️", "error": "❌"}.get(metric.status, "❓")
            report_lines.extend([
                f"  {status_icon} {metric.name.replace('_', ' ').title()}:",
                f"    Status: {metric.status.upper()}",
                f"    Value: {metric.value}",
                f"    Message: {metric.message}",
                ""
            ])
        
        if report.recommendations:
            report_lines.extend([
                "RECOMMENDATIONS:",
                *[f"  • {rec}" for rec in report.recommendations],
                ""
            ])
        
        report_lines.append("=" * 80)
        
        report_text = "\n".join(report_lines)
        
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(report_text)
            app_logger.info(f"Quality report saved to {output_file}")
        
        return report_text


def main():
    """Main entry point for the code quality checker."""
    parser = argparse.ArgumentParser(description="Run comprehensive code quality checks")
    parser.add_argument("--output", "-o", type=Path, help="Output file for the report")
    parser.add_argument("--json", action="store_true", help="Output report in JSON format")
    parser.add_argument("--fail-on-error", action="store_true", help="Exit with error code if quality issues found")
    
    args = parser.parse_args()
    
    checker = CodeQualityChecker()
    report = checker.run_all_checks()
    
    if args.json:
        # Output JSON report
        json_report = {
            "timestamp": report.timestamp,
            "overall_score": report.overall_score,
            "summary": report.summary,
            "metrics": [
                {
                    "name": m.name,
                    "value": m.value,
                    "status": m.status,
                    "message": m.message,
                    "details": m.details
                }
                for m in report.metrics
            ],
            "recommendations": report.recommendations
        }
        
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(json_report, f, indent=2)
        else:
            print(json.dumps(json_report, indent=2))
    else:
        # Output formatted text report
        report_text = checker.generate_report(report, args.output)
        if not args.output:
            print(report_text)
    
    # Exit with appropriate code
    if args.fail_on_error and report.overall_score < 70:
        sys.exit(1)
    elif report.summary['failed_checks'] > 0:
        sys.exit(2)
    else:
        sys.exit(0)


if __name__ == "__main__":
    main()