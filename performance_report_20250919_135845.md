Service Registry Performance and Reliability Report
============================================================
Generated: 2025-09-19 13:58:45

EXECUTIVE SUMMARY
--------------------
Total Tests: 6
Passed: 6
Failed: 0
Success Rate: 100.0%

PERFORMANCE REQUIREMENTS VALIDATION
----------------------------------------
✅ Startup Time: 1.135s (< 2.0s requirement)
✅ Memory Usage: 0.4MB (< 10MB requirement)
✅ Service Resolution: 0.000000s (< 1ms requirement)

DETAILED TEST RESULTS
-------------------------

1. STARTUP TIME PERFORMANCE
   Status: PASSED
   Average Time: 1.135s
   Min Time: 0.055s
   Max Time: 3.221s
   Iterations: 3

2. MEMORY USAGE PERFORMANCE
   Status: PASSED
   Total Overhead: 0.4MB
   Baseline Memory: 467.8MB
   Final Memory: 468.2MB

3. SERVICE RESOLUTION PERFORMANCE
   Status: PASSED
   Average Lookup Time: 0.000000s
   Min Lookup Time: 0.000000s
   Max Lookup Time: 0.000004s
   Lookups per Second: 5714939
   Test Scale: 100 services, 1000 lookups

4. CONCURRENT ACCESS RELIABILITY
   Status: PASSED
   Total Operations: 1000
   Operations per Second: 694887
   Success Rate: 100.00%
   Errors: 0
   Test Scale: 10 threads, 100 ops/thread

5. DEPENDENCY SCENARIOS RELIABILITY
   Status: PASSED
   ✓ Normal Dependencies
     Resolution Time: 0.000000s
   ✓ Missing Dependencies
   ✓ Circular Dependencies
   ✓ Initialization Failure
     Resolution Time: 0.000028s
   ✓ Deep Dependency Chain
     Resolution Time: 0.000001s

6. MEMORY LEAK DETECTION
   Status: PASSED
   Memory Growth: 0.0MB
   Baseline Memory: 468.2MB
   Final Memory: 468.2MB
   Test Iterations: 50
   Potential Leak: No

RECOMMENDATIONS
---------------

• Consider optimizing service registration for faster startup

============================================================
End of Performance Report