#!/usr/bin/env python3
"""
Performance and Reliability Test Runner

This script runs comprehensive performance and reliability tests for the service registry system.
It measures startup time, memory usage, service resolution performance, and tests various
dependency scenarios to ensure the system meets performance requirements.
"""

import sys
import os
import json
import time
from pathlib import Path
from typing import Dict, Any

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.tests.performance.test_service_registry_performance import (
    PerformanceTestSuite,
    run_performance_benchmark
)


def generate_performance_report(results: Dict[str, Any]) -> str:
    """
    Generate a comprehensive performance report.
    
    Args:
        results: Performance test results
        
    Returns:
        Formatted report string
    """
    lines = [
        "Service Registry Performance and Reliability Report",
        "=" * 60,
        f"Generated: {time.strftime('%Y-%m-%d %H:%M:%S')}",
        "",
        "EXECUTIVE SUMMARY",
        "-" * 20
    ]
    
    # Overall assessment
    total_tests = 0
    passed_tests = 0
    failed_tests = 0
    
    for test_name, test_results in results.items():
        if isinstance(test_results, dict):
            total_tests += 1
            if test_results.get('error'):
                failed_tests += 1
            elif test_results.get('skipped'):
                # Don't count skipped tests
                total_tests -= 1
            else:
                passed_tests += 1
    
    lines.extend([
        f"Total Tests: {total_tests}",
        f"Passed: {passed_tests}",
        f"Failed: {failed_tests}",
        f"Success Rate: {(passed_tests/total_tests*100):.1f}%" if total_tests > 0 else "N/A",
        ""
    ])
    
    # Performance requirements check
    lines.extend([
        "PERFORMANCE REQUIREMENTS VALIDATION",
        "-" * 40
    ])
    
    # Startup time requirement: <2 seconds additional overhead
    startup_results = results.get('startup_time', {})
    if startup_results.get('error'):
        lines.append("❌ Startup Time: Test failed")
    elif startup_results.get('skipped'):
        lines.append("⏭️  Startup Time: Test skipped (no config)")
    else:
        avg_time = startup_results.get('average_time', 0)
        if avg_time < 2.0:
            lines.append(f"✅ Startup Time: {avg_time:.3f}s (< 2.0s requirement)")
        else:
            lines.append(f"❌ Startup Time: {avg_time:.3f}s (exceeds 2.0s requirement)")
    
    # Memory usage requirement: <10MB additional memory
    memory_results = results.get('memory_usage', {})
    if memory_results.get('error'):
        lines.append("❌ Memory Usage: Test failed")
    else:
        overhead = memory_results.get('total_overhead', 0)
        if overhead < 10.0:
            lines.append(f"✅ Memory Usage: {overhead:.1f}MB (< 10MB requirement)")
        else:
            lines.append(f"❌ Memory Usage: {overhead:.1f}MB (exceeds 10MB requirement)")
    
    # Service resolution requirement: <1ms average resolution time
    resolution_results = results.get('service_resolution', {})
    if resolution_results.get('error'):
        lines.append("❌ Service Resolution: Test failed")
    else:
        avg_lookup = resolution_results.get('average_lookup_time', 0)
        if avg_lookup < 0.001:
            lines.append(f"✅ Service Resolution: {avg_lookup:.6f}s (< 1ms requirement)")
        else:
            lines.append(f"❌ Service Resolution: {avg_lookup:.6f}s (exceeds 1ms requirement)")
    
    lines.append("")
    
    # Detailed results
    lines.extend([
        "DETAILED TEST RESULTS",
        "-" * 25,
        ""
    ])
    
    # 1. Startup Time Performance
    lines.append("1. STARTUP TIME PERFORMANCE")
    if startup_results.get('error'):
        lines.append(f"   Status: FAILED - {startup_results['error']}")
    elif startup_results.get('skipped'):
        lines.append("   Status: SKIPPED - No configuration directory available")
    else:
        lines.extend([
            "   Status: PASSED",
            f"   Average Time: {startup_results.get('average_time', 0):.3f}s",
            f"   Min Time: {startup_results.get('min_time', 0):.3f}s",
            f"   Max Time: {startup_results.get('max_time', 0):.3f}s",
            f"   Iterations: {startup_results.get('iterations', 0)}"
        ])
    lines.append("")
    
    # 2. Memory Usage Performance
    lines.append("2. MEMORY USAGE PERFORMANCE")
    if memory_results.get('error'):
        lines.append(f"   Status: FAILED - {memory_results['error']}")
    else:
        lines.extend([
            "   Status: PASSED",
            f"   Total Overhead: {memory_results.get('total_overhead', 0):.1f}MB"
        ])
        
        if 'baseline_memory' in memory_results:
            lines.extend([
                f"   Baseline Memory: {memory_results['baseline_memory']:.1f}MB",
                f"   Final Memory: {memory_results.get('startup_memory', 0):.1f}MB"
            ])
    lines.append("")
    
    # 3. Service Resolution Performance
    lines.append("3. SERVICE RESOLUTION PERFORMANCE")
    if resolution_results.get('error'):
        lines.append(f"   Status: FAILED - {resolution_results['error']}")
    else:
        lines.extend([
            "   Status: PASSED",
            f"   Average Lookup Time: {resolution_results.get('average_lookup_time', 0):.6f}s",
            f"   Min Lookup Time: {resolution_results.get('min_lookup_time', 0):.6f}s",
            f"   Max Lookup Time: {resolution_results.get('max_lookup_time', 0):.6f}s",
            f"   Lookups per Second: {resolution_results.get('lookups_per_second', 0):.0f}",
            f"   Test Scale: {resolution_results.get('num_services', 0)} services, {resolution_results.get('num_lookups', 0)} lookups"
        ])
    lines.append("")
    
    # 4. Concurrent Access Reliability
    lines.append("4. CONCURRENT ACCESS RELIABILITY")
    concurrent_results = results.get('concurrent_access', {})
    if concurrent_results.get('error'):
        lines.append(f"   Status: FAILED - {concurrent_results['error']}")
    else:
        lines.extend([
            "   Status: PASSED",
            f"   Total Operations: {concurrent_results.get('total_operations', 0)}",
            f"   Operations per Second: {concurrent_results.get('operations_per_second', 0):.0f}",
            f"   Success Rate: {concurrent_results.get('success_rate', 0):.2%}",
            f"   Errors: {concurrent_results.get('error_count', 0)}",
            f"   Test Scale: {concurrent_results.get('num_threads', 0)} threads, {concurrent_results.get('operations_per_thread', 0)} ops/thread"
        ])
    lines.append("")
    
    # 5. Dependency Scenarios
    lines.append("5. DEPENDENCY SCENARIOS RELIABILITY")
    scenario_results = results.get('dependency_scenarios', {})
    if scenario_results.get('error'):
        lines.append(f"   Status: FAILED - {scenario_results['error']}")
    else:
        lines.append("   Status: PASSED")
        
        for scenario_name, scenario_result in scenario_results.items():
            if isinstance(scenario_result, dict):
                status = "✓" if scenario_result.get('success', False) else "✗"
                lines.append(f"   {status} {scenario_name.replace('_', ' ').title()}")
                
                if 'resolution_time' in scenario_result:
                    lines.append(f"     Resolution Time: {scenario_result['resolution_time']:.6f}s")
                
                if scenario_result.get('error') and not scenario_result.get('success'):
                    lines.append(f"     Error: {scenario_result['error']}")
    lines.append("")
    
    # 6. Memory Leak Detection
    lines.append("6. MEMORY LEAK DETECTION")
    leak_results = results.get('memory_leaks', {})
    if leak_results.get('error'):
        lines.append(f"   Status: FAILED - {leak_results['error']}")
    else:
        leak_detected = leak_results.get('potential_leak', False)
        status = "FAILED" if leak_detected else "PASSED"
        lines.extend([
            f"   Status: {status}",
            f"   Memory Growth: {leak_results.get('memory_growth', 0):.1f}MB",
            f"   Baseline Memory: {leak_results.get('baseline_memory', 0):.1f}MB",
            f"   Final Memory: {leak_results.get('final_memory', 0):.1f}MB",
            f"   Test Iterations: {leak_results.get('iterations', 0)}",
            f"   Potential Leak: {'Yes' if leak_detected else 'No'}"
        ])
    lines.append("")
    
    # Recommendations
    lines.extend([
        "RECOMMENDATIONS",
        "-" * 15,
        ""
    ])
    
    recommendations = []
    
    # Check startup time
    if startup_results.get('average_time', 0) > 1.0:
        recommendations.append("• Consider optimizing service registration for faster startup")
    
    # Check memory usage
    if memory_results.get('total_overhead', 0) > 5.0:
        recommendations.append("• Monitor memory usage and consider optimizing service instances")
    
    # Check service resolution
    if resolution_results.get('average_lookup_time', 0) > 0.0005:
        recommendations.append("• Consider caching frequently accessed services")
    
    # Check concurrent access
    if concurrent_results.get('success_rate', 1.0) < 0.99:
        recommendations.append("• Investigate concurrent access issues and improve thread safety")
    
    # Check memory leaks
    if leak_results.get('potential_leak', False):
        recommendations.append("• Investigate potential memory leaks in service lifecycle management")
    
    if not recommendations:
        recommendations.append("• All performance metrics are within acceptable ranges")
        recommendations.append("• Continue monitoring performance in production environments")
    
    lines.extend(recommendations)
    lines.append("")
    
    # Footer
    lines.extend([
        "=" * 60,
        "End of Performance Report"
    ])
    
    return "\n".join(lines)


def main():
    """Main function to run performance tests and generate report."""
    print("Starting Service Registry Performance and Reliability Tests...")
    print("This may take a few minutes to complete.\n")
    
    try:
        # Run the performance benchmark
        results = run_performance_benchmark()
        
        # Generate report
        report = generate_performance_report(results)
        
        # Save results and report
        timestamp = time.strftime("%Y%m%d_%H%M%S")
        
        # Save raw results
        results_file = f"performance_results_{timestamp}.json"
        with open(results_file, 'w') as f:
            json.dump(results, f, indent=2, default=str)
        
        # Save report
        report_file = f"performance_report_{timestamp}.md"
        with open(report_file, 'w') as f:
            f.write(report)
        
        # Print report to console
        print("\n" + report)
        
        print(f"\nResults saved to:")
        print(f"  Raw data: {results_file}")
        print(f"  Report: {report_file}")
        
        # Determine exit code based on results
        failed_tests = sum(1 for result in results.values() 
                          if isinstance(result, dict) and result.get('error'))
        
        if failed_tests > 0:
            print(f"\n❌ {failed_tests} test(s) failed. See report for details.")
            return 1
        else:
            print("\n✅ All performance tests passed!")
            return 0
            
    except Exception as e:
        print(f"\n❌ Performance testing failed: {e}")
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())