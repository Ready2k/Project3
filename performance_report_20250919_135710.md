Service Registry Performance and Reliability Report
============================================================
Generated: 2025-09-19 13:57:10

EXECUTIVE SUMMARY
--------------------
Total Tests: 6
Passed: 3
Failed: 3
Success Rate: 50.0%

PERFORMANCE REQUIREMENTS VALIDATION
----------------------------------------
✅ Startup Time: 1.155s (< 2.0s requirement)
✅ Memory Usage: 0.3MB (< 10MB requirement)
❌ Service Resolution: Test failed

DETAILED TEST RESULTS
-------------------------

1. STARTUP TIME PERFORMANCE
   Status: PASSED
   Average Time: 1.155s
   Min Time: 0.057s
   Max Time: 3.276s
   Iterations: 3

2. MEMORY USAGE PERFORMANCE
   Status: PASSED
   Total Overhead: 0.3MB
   Baseline Memory: 465.5MB
   Final Memory: 465.8MB

3. SERVICE RESOLUTION PERFORMANCE
   Status: FAILED - Can't instantiate abstract class MockService with abstract methods dependencies, initialize, name

4. CONCURRENT ACCESS RELIABILITY
   Status: FAILED - Can't instantiate abstract class MockService with abstract methods dependencies, initialize, name

5. DEPENDENCY SCENARIOS RELIABILITY
   Status: PASSED
   ✗ Normal Dependencies
     Resolution Time: 0.000000s
     Error: Can't instantiate abstract class MockService with abstract methods dependencies, initialize, name
   ✗ Missing Dependencies
     Error: Can't instantiate abstract class MockService with abstract methods dependencies, initialize, name
   ✓ Circular Dependencies
   ✓ Initialization Failure
     Resolution Time: 0.000017s
   ✗ Deep Dependency Chain
     Resolution Time: 0.000000s
     Error: Can't instantiate abstract class MockService with abstract methods dependencies, initialize, name

6. MEMORY LEAK DETECTION
   Status: FAILED - Can't instantiate abstract class MockService with abstract methods dependencies, initialize, name

RECOMMENDATIONS
---------------

• Consider optimizing service registration for faster startup

============================================================
End of Performance Report