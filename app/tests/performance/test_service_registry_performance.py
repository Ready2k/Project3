"""
Performance and Reliability Tests for Service Registry System

This module tests the performance characteristics and reliability of the service registry
system under various conditions and dependency scenarios.
"""

import time
import psutil
import os
import concurrent.futures
from typing import Dict, Any, List, Optional
import pytest

from app.core.registry import get_registry, reset_registry
from app.core.startup import ApplicationStartup
from app.utils.imports import get_import_manager, reset_import_manager
from app.core.service import Service


class MockService(Service):
    """Mock service for testing."""

    def __init__(
        self,
        service_name: str,
        init_delay: float = 0.0,
        fail_init: bool = False,
        service_dependencies: Optional[List[str]] = None,
    ):
        self._name = service_name
        self.init_delay = init_delay
        self.fail_init = fail_init
        self.initialized = False
        self.shutdown_called = False
        self._dependencies = service_dependencies or []

        if init_delay > 0:
            time.sleep(init_delay)

        if fail_init:
            raise Exception(f"Mock service {service_name} failed to initialize")

        self.initialized = True

    def initialize(self) -> None:
        """Initialize the mock service."""
        if self.fail_init:
            raise Exception(f"Mock service {self._name} failed to initialize")
        self.initialized = True

    def shutdown(self) -> None:
        """Shutdown the mock service."""
        self.shutdown_called = True
        self.initialized = False

    def health_check(self) -> bool:
        """Check if the mock service is healthy."""
        return self.initialized and not self.shutdown_called

    @property
    def dependencies(self) -> List[str]:
        """Get service dependencies."""
        return self._dependencies.copy()

    @property
    def name(self) -> str:
        """Get service name."""
        return self._name


class PerformanceTestSuite:
    """Test suite for performance and reliability testing."""

    def __init__(self):
        self.process = psutil.Process(os.getpid())
        self.baseline_memory = None
        self.baseline_startup_time = None

    def get_memory_usage(self) -> float:
        """Get current memory usage in MB."""
        return self.process.memory_info().rss / 1024 / 1024

    def measure_startup_time(
        self, config_dir: str = "config", iterations: int = 5
    ) -> Dict[str, float]:
        """
        Measure startup time impact of service registry.

        Args:
            config_dir: Configuration directory
            iterations: Number of iterations to average

        Returns:
            Dictionary with timing measurements
        """
        times = []

        for i in range(iterations):
            # Reset registry for clean test
            reset_registry()
            reset_import_manager()

            start_time = time.perf_counter()

            try:
                # Run startup sequence
                startup = ApplicationStartup(config_dir)
                startup.run_startup_sequence(include_dev_deps=False)

                end_time = time.perf_counter()
                startup_time = end_time - start_time
                times.append(startup_time)

            except Exception as e:
                # Even if startup fails, measure the time
                end_time = time.perf_counter()
                startup_time = end_time - start_time
                times.append(startup_time)
                print(
                    f"Startup iteration {i+1} failed but took {startup_time:.3f}s: {e}"
                )

        return {
            "average_time": sum(times) / len(times),
            "min_time": min(times),
            "max_time": max(times),
            "times": times,
            "iterations": iterations,
        }

    def measure_memory_usage(self, config_dir: str = "config") -> Dict[str, float]:
        """
        Measure memory usage impact of service system.

        Args:
            config_dir: Configuration directory

        Returns:
            Dictionary with memory measurements
        """
        # Get baseline memory
        baseline_memory = self.get_memory_usage()

        # Reset registry for clean test
        reset_registry()
        reset_import_manager()

        # Measure memory after registry creation
        get_registry()
        registry_memory = self.get_memory_usage()

        # Run startup and measure memory
        try:
            startup = ApplicationStartup(config_dir)
            startup.run_startup_sequence(include_dev_deps=False)
            startup_memory = self.get_memory_usage()
        except Exception as e:
            startup_memory = self.get_memory_usage()
            print(f"Startup failed but memory measured: {e}")

        return {
            "baseline_memory": baseline_memory,
            "registry_memory": registry_memory,
            "startup_memory": startup_memory,
            "registry_overhead": registry_memory - baseline_memory,
            "total_overhead": startup_memory - baseline_memory,
        }

    def test_service_resolution_performance(
        self, num_services: int = 100, num_lookups: int = 1000
    ) -> Dict[str, float]:
        """
        Test service resolution performance.

        Args:
            num_services: Number of services to register
            num_lookups: Number of lookups to perform

        Returns:
            Dictionary with performance measurements
        """
        reset_registry()
        registry = get_registry()

        # Register services
        setup_start = time.perf_counter()
        for i in range(num_services):
            service = MockService(f"service_{i}")
            registry.register_singleton(f"service_{i}", service)
        setup_time = time.perf_counter() - setup_start

        # Measure lookup performance
        lookup_times = []
        for i in range(num_lookups):
            service_name = f"service_{i % num_services}"

            start_time = time.perf_counter()
            service = registry.get(service_name)
            end_time = time.perf_counter()

            lookup_times.append(end_time - start_time)

        return {
            "setup_time": setup_time,
            "average_lookup_time": sum(lookup_times) / len(lookup_times),
            "min_lookup_time": min(lookup_times),
            "max_lookup_time": max(lookup_times),
            "total_lookup_time": sum(lookup_times),
            "lookups_per_second": num_lookups / sum(lookup_times),
            "num_services": num_services,
            "num_lookups": num_lookups,
        }

    def test_concurrent_access(
        self, num_threads: int = 10, operations_per_thread: int = 100
    ) -> Dict[str, Any]:
        """
        Test concurrent access to service registry.

        Args:
            num_threads: Number of concurrent threads
            operations_per_thread: Number of operations per thread

        Returns:
            Dictionary with concurrency test results
        """
        reset_registry()
        registry = get_registry()

        # Register some services
        for i in range(10):
            service = MockService(f"service_{i}")
            registry.register_singleton(f"service_{i}", service)

        results = []
        errors = []

        def worker_thread(thread_id: int):
            """Worker thread function."""
            thread_results = []
            thread_errors = []

            for i in range(operations_per_thread):
                try:
                    start_time = time.perf_counter()

                    # Mix of operations
                    if i % 3 == 0:
                        # Service lookup
                        registry.get(f"service_{i % 10}")
                    elif i % 3 == 1:
                        # Health check
                        registry.health_check()
                    else:
                        # List services
                        registry.list_services()

                    end_time = time.perf_counter()
                    thread_results.append(end_time - start_time)

                except Exception as e:
                    thread_errors.append(f"Thread {thread_id}, operation {i}: {e}")

            return thread_results, thread_errors

        # Run concurrent operations
        start_time = time.perf_counter()

        with concurrent.futures.ThreadPoolExecutor(max_workers=num_threads) as executor:
            futures = [executor.submit(worker_thread, i) for i in range(num_threads)]

            for future in concurrent.futures.as_completed(futures):
                thread_results, thread_errors = future.result()
                results.extend(thread_results)
                errors.extend(thread_errors)

        end_time = time.perf_counter()

        return {
            "total_time": end_time - start_time,
            "total_operations": len(results),
            "average_operation_time": sum(results) / len(results) if results else 0,
            "operations_per_second": len(results) / (end_time - start_time),
            "errors": errors,
            "error_count": len(errors),
            "success_rate": (
                (len(results) - len(errors)) / len(results) if results else 0
            ),
            "num_threads": num_threads,
            "operations_per_thread": operations_per_thread,
        }

    def test_dependency_scenarios(self) -> Dict[str, Any]:
        """
        Test system behavior under various dependency scenarios.

        Returns:
            Dictionary with scenario test results
        """
        scenarios = {}

        # Scenario 1: Normal dependencies
        reset_registry()
        registry = get_registry()

        try:
            service_a = MockService("service_a")
            service_b = MockService("service_b", service_dependencies=["service_a"])

            registry.register_singleton("service_a", service_a)
            registry.register_singleton(
                "service_b", service_b, dependencies=["service_a"]
            )

            start_time = time.perf_counter()
            registry.get("service_b")
            resolution_time = time.perf_counter() - start_time

            scenarios["normal_dependencies"] = {
                "success": True,
                "resolution_time": resolution_time,
                "error": None,
            }
        except Exception as e:
            scenarios["normal_dependencies"] = {
                "success": False,
                "resolution_time": 0,
                "error": str(e),
            }

        # Scenario 2: Missing dependencies
        reset_registry()
        registry = get_registry()

        try:
            service_c = MockService(
                "service_c", service_dependencies=["missing_service"]
            )
            registry.register_singleton(
                "service_c", service_c, dependencies=["missing_service"]
            )

            validation_errors = registry.validate_dependencies()

            scenarios["missing_dependencies"] = {
                "success": len(validation_errors) > 0,  # Should detect missing deps
                "validation_errors": validation_errors,
                "error": None,
            }
        except Exception as e:
            scenarios["missing_dependencies"] = {
                "success": False,
                "validation_errors": [],
                "error": str(e),
            }

        # Scenario 3: Circular dependencies
        reset_registry()
        registry = get_registry()

        try:
            # Create circular dependency: A -> B -> A
            def factory_a():
                return MockService("service_a", service_dependencies=["service_b"])

            def factory_b():
                return MockService("service_b", service_dependencies=["service_a"])

            registry.register_factory(
                "service_a", factory_a, dependencies=["service_b"]
            )
            registry.register_factory(
                "service_b", factory_b, dependencies=["service_a"]
            )

            validation_errors = registry.validate_dependencies()

            scenarios["circular_dependencies"] = {
                "success": len(validation_errors) > 0,  # Should detect circular deps
                "validation_errors": validation_errors,
                "error": None,
            }
        except Exception as e:
            scenarios["circular_dependencies"] = {
                "success": False,
                "validation_errors": [],
                "error": str(e),
            }

        # Scenario 4: Service initialization failure
        reset_registry()
        registry = get_registry()

        try:

            def failing_factory():
                return MockService("failing_service", fail_init=True)

            registry.register_factory("failing_service", failing_factory)

            start_time = time.perf_counter()
            try:
                service = registry.get("failing_service")
                scenarios["initialization_failure"] = {
                    "success": False,  # Should have failed
                    "resolution_time": time.perf_counter() - start_time,
                    "error": "Service should have failed to initialize",
                }
            except Exception as e:
                scenarios["initialization_failure"] = {
                    "success": True,  # Correctly handled failure
                    "resolution_time": time.perf_counter() - start_time,
                    "error": str(e),
                }
        except Exception as e:
            scenarios["initialization_failure"] = {
                "success": False,
                "resolution_time": 0,
                "error": str(e),
            }

        # Scenario 5: High dependency chain
        reset_registry()
        registry = get_registry()

        try:
            # Create a chain of 10 services: service_0 -> service_1 -> ... -> service_9
            for i in range(10):
                deps = [f"chain_service_{i-1}"] if i > 0 else []
                service = MockService(f"chain_service_{i}", service_dependencies=deps)
                registry.register_singleton(
                    f"chain_service_{i}", service, dependencies=deps
                )

            start_time = time.perf_counter()
            registry.get("chain_service_9")
            resolution_time = time.perf_counter() - start_time

            scenarios["deep_dependency_chain"] = {
                "success": True,
                "resolution_time": resolution_time,
                "chain_length": 10,
                "error": None,
            }
        except Exception as e:
            scenarios["deep_dependency_chain"] = {
                "success": False,
                "resolution_time": 0,
                "chain_length": 10,
                "error": str(e),
            }

        return scenarios

    def test_memory_leaks(self, iterations: int = 100) -> Dict[str, Any]:
        """
        Test for memory leaks in service registry operations.

        Args:
            iterations: Number of iterations to test

        Returns:
            Dictionary with memory leak test results
        """
        memory_samples = []

        # Get baseline memory
        baseline_memory = self.get_memory_usage()
        memory_samples.append(baseline_memory)

        for i in range(iterations):
            # Reset and recreate registry
            reset_registry()
            reset_import_manager()

            registry = get_registry()

            # Register and use services
            for j in range(10):
                service = MockService(f"service_{j}")
                registry.register_singleton(f"service_{j}", service)

            # Perform operations
            for j in range(10):
                service = registry.get(f"service_{j}")
                registry.health_check()

            # Shutdown services
            registry.shutdown_all()

            # Sample memory every 10 iterations
            if i % 10 == 0:
                memory_samples.append(self.get_memory_usage())

        # Final memory measurement
        final_memory = self.get_memory_usage()
        memory_samples.append(final_memory)

        # Calculate memory growth
        memory_growth = final_memory - baseline_memory
        max_memory = max(memory_samples)
        min_memory = min(memory_samples)

        return {
            "baseline_memory": baseline_memory,
            "final_memory": final_memory,
            "memory_growth": memory_growth,
            "max_memory": max_memory,
            "min_memory": min_memory,
            "memory_samples": memory_samples,
            "iterations": iterations,
            "potential_leak": memory_growth > 10.0,  # More than 10MB growth
        }


class TestServiceRegistryPerformance:
    """Test class for service registry performance tests."""

    def setup_method(self):
        """Set up test environment."""
        self.performance_suite = PerformanceTestSuite()
        reset_registry()
        reset_import_manager()

    def teardown_method(self):
        """Clean up test environment."""
        reset_registry()
        reset_import_manager()

    def test_startup_time_performance(self):
        """Test that startup time is within acceptable limits."""
        # Use test config directory if available, otherwise skip
        config_dir = "config"
        if not os.path.exists(config_dir):
            pytest.skip("Config directory not available for startup testing")

        timing_results = self.performance_suite.measure_startup_time(
            config_dir, iterations=3
        )

        # Assertions
        assert (
            timing_results["average_time"] < 5.0
        ), f"Startup time too slow: {timing_results['average_time']:.3f}s"
        assert (
            timing_results["max_time"] < 10.0
        ), f"Maximum startup time too slow: {timing_results['max_time']:.3f}s"

        print(
            f"Startup performance: avg={timing_results['average_time']:.3f}s, max={timing_results['max_time']:.3f}s"
        )

    def test_memory_usage_performance(self):
        """Test that memory usage is within acceptable limits."""
        # Use test config directory if available, otherwise test with minimal setup
        config_dir = "config"

        if os.path.exists(config_dir):
            memory_results = self.performance_suite.measure_memory_usage(config_dir)
        else:
            # Minimal memory test without full startup
            baseline_memory = self.performance_suite.get_memory_usage()
            registry = get_registry()

            # Register some services
            for i in range(10):
                service = MockService(f"service_{i}")
                registry.register_singleton(f"service_{i}", service)

            final_memory = self.performance_suite.get_memory_usage()

            memory_results = {
                "baseline_memory": baseline_memory,
                "startup_memory": final_memory,
                "total_overhead": final_memory - baseline_memory,
            }

        # Assertions
        assert (
            memory_results["total_overhead"] < 50.0
        ), f"Memory overhead too high: {memory_results['total_overhead']:.1f}MB"

        print(f"Memory usage: overhead={memory_results['total_overhead']:.1f}MB")

    def test_service_resolution_performance(self):
        """Test service resolution performance."""
        performance_results = (
            self.performance_suite.test_service_resolution_performance(
                num_services=50, num_lookups=500
            )
        )

        # Assertions
        assert (
            performance_results["average_lookup_time"] < 0.001
        ), f"Service lookup too slow: {performance_results['average_lookup_time']:.6f}s"
        assert (
            performance_results["lookups_per_second"] > 1000
        ), f"Lookup rate too low: {performance_results['lookups_per_second']:.0f}/s"

        print(
            f"Service resolution: avg={performance_results['average_lookup_time']:.6f}s, rate={performance_results['lookups_per_second']:.0f}/s"
        )

    def test_concurrent_access_reliability(self):
        """Test concurrent access reliability."""
        concurrency_results = self.performance_suite.test_concurrent_access(
            num_threads=5, operations_per_thread=50
        )

        # Assertions
        assert (
            concurrency_results["error_count"] == 0
        ), f"Concurrent access errors: {concurrency_results['errors']}"
        assert (
            concurrency_results["success_rate"] >= 0.95
        ), f"Success rate too low: {concurrency_results['success_rate']:.2%}"
        assert (
            concurrency_results["operations_per_second"] > 100
        ), f"Concurrent operation rate too low: {concurrency_results['operations_per_second']:.0f}/s"

        print(
            f"Concurrent access: {concurrency_results['total_operations']} ops, {concurrency_results['operations_per_second']:.0f}/s, {concurrency_results['success_rate']:.2%} success"
        )

    def test_dependency_scenarios_reliability(self):
        """Test system behavior under various dependency scenarios."""
        scenario_results = self.performance_suite.test_dependency_scenarios()

        # Assertions for each scenario
        assert scenario_results["normal_dependencies"][
            "success"
        ], "Normal dependency resolution failed"
        assert scenario_results["missing_dependencies"][
            "success"
        ], "Missing dependency detection failed"
        assert scenario_results["circular_dependencies"][
            "success"
        ], "Circular dependency detection failed"
        assert scenario_results["initialization_failure"][
            "success"
        ], "Service initialization failure handling failed"
        assert scenario_results["deep_dependency_chain"][
            "success"
        ], "Deep dependency chain resolution failed"

        # Performance assertions
        assert (
            scenario_results["normal_dependencies"]["resolution_time"] < 0.1
        ), "Normal dependency resolution too slow"
        assert (
            scenario_results["deep_dependency_chain"]["resolution_time"] < 0.1
        ), "Deep dependency chain resolution too slow"

        print("Dependency scenarios: all tests passed")
        for scenario, result in scenario_results.items():
            if "resolution_time" in result:
                print(f"  {scenario}: {result['resolution_time']:.6f}s")

    def test_memory_leak_detection(self):
        """Test for memory leaks in service registry operations."""
        leak_results = self.performance_suite.test_memory_leaks(iterations=50)

        # Assertions
        assert not leak_results[
            "potential_leak"
        ], f"Potential memory leak detected: {leak_results['memory_growth']:.1f}MB growth"
        assert (
            leak_results["memory_growth"] < 5.0
        ), f"Memory growth too high: {leak_results['memory_growth']:.1f}MB"

        print(
            f"Memory leak test: {leak_results['memory_growth']:.1f}MB growth over {leak_results['iterations']} iterations"
        )

    def test_import_manager_performance(self):
        """Test import manager performance."""
        import_manager = get_import_manager()

        # Test safe import performance
        start_time = time.perf_counter()
        for i in range(100):
            # Test importing standard library modules
            result = import_manager.safe_import("os")
            assert result is not None
        import_time = time.perf_counter() - start_time

        # Test service resolution performance
        registry = get_registry()
        test_service = MockService("test_service")
        registry.register_singleton("test_service", test_service)

        start_time = time.perf_counter()
        for i in range(100):
            service = import_manager.require_service("test_service")
            assert service is not None
        service_time = time.perf_counter() - start_time

        # Assertions
        assert (
            import_time < 1.0
        ), f"Import operations too slow: {import_time:.3f}s for 100 imports"
        assert (
            service_time < 0.1
        ), f"Service resolution too slow: {service_time:.3f}s for 100 resolutions"

        print(
            f"Import manager: {import_time:.3f}s for imports, {service_time:.3f}s for service resolution"
        )


def run_performance_benchmark():
    """
    Run a comprehensive performance benchmark.

    Returns:
        Dictionary with benchmark results
    """
    print("Running Service Registry Performance Benchmark")
    print("=" * 60)

    suite = PerformanceTestSuite()
    results = {}

    # Startup time test
    print("\n1. Startup Time Performance...")
    try:
        config_dir = "config" if os.path.exists("config") else None
        if config_dir:
            timing_results = suite.measure_startup_time(config_dir, iterations=3)
            results["startup_time"] = timing_results
            print(f"   Average startup time: {timing_results['average_time']:.3f}s")
            print(
                f"   Range: {timing_results['min_time']:.3f}s - {timing_results['max_time']:.3f}s"
            )
        else:
            print("   Skipped (no config directory)")
            results["startup_time"] = {"skipped": True}
    except Exception as e:
        print(f"   Failed: {e}")
        results["startup_time"] = {"error": str(e)}

    # Memory usage test
    print("\n2. Memory Usage Performance...")
    try:
        if config_dir:
            memory_results = suite.measure_memory_usage(config_dir)
        else:
            # Minimal test
            baseline = suite.get_memory_usage()
            registry = get_registry()
            for i in range(10):
                service = MockService(f"service_{i}")
                registry.register_singleton(f"service_{i}", service)
            final = suite.get_memory_usage()
            memory_results = {"total_overhead": final - baseline}

        results["memory_usage"] = memory_results
        print(f"   Memory overhead: {memory_results['total_overhead']:.1f}MB")
    except Exception as e:
        print(f"   Failed: {e}")
        results["memory_usage"] = {"error": str(e)}

    # Service resolution performance
    print("\n3. Service Resolution Performance...")
    try:
        resolution_results = suite.test_service_resolution_performance(100, 1000)
        results["service_resolution"] = resolution_results
        print(
            f"   Average lookup time: {resolution_results['average_lookup_time']:.6f}s"
        )
        print(f"   Lookups per second: {resolution_results['lookups_per_second']:.0f}")
    except Exception as e:
        print(f"   Failed: {e}")
        results["service_resolution"] = {"error": str(e)}

    # Concurrent access test
    print("\n4. Concurrent Access Reliability...")
    try:
        concurrency_results = suite.test_concurrent_access(10, 100)
        results["concurrent_access"] = concurrency_results
        print(
            f"   Operations per second: {concurrency_results['operations_per_second']:.0f}"
        )
        print(f"   Success rate: {concurrency_results['success_rate']:.2%}")
        print(f"   Errors: {concurrency_results['error_count']}")
    except Exception as e:
        print(f"   Failed: {e}")
        results["concurrent_access"] = {"error": str(e)}

    # Dependency scenarios
    print("\n5. Dependency Scenarios...")
    try:
        scenario_results = suite.test_dependency_scenarios()
        results["dependency_scenarios"] = scenario_results

        passed_scenarios = sum(
            1 for result in scenario_results.values() if result.get("success", False)
        )
        total_scenarios = len(scenario_results)
        print(f"   Scenarios passed: {passed_scenarios}/{total_scenarios}")

        for scenario, result in scenario_results.items():
            status = "✓" if result.get("success", False) else "✗"
            print(f"   {status} {scenario}")
    except Exception as e:
        print(f"   Failed: {e}")
        results["dependency_scenarios"] = {"error": str(e)}

    # Memory leak test
    print("\n6. Memory Leak Detection...")
    try:
        leak_results = suite.test_memory_leaks(50)
        results["memory_leaks"] = leak_results
        print(f"   Memory growth: {leak_results['memory_growth']:.1f}MB")
        print(f"   Potential leak: {'Yes' if leak_results['potential_leak'] else 'No'}")
    except Exception as e:
        print(f"   Failed: {e}")
        results["memory_leaks"] = {"error": str(e)}

    print("\n" + "=" * 60)
    print("Benchmark completed!")

    return results


if __name__ == "__main__":
    """Run benchmark when executed directly."""
    results = run_performance_benchmark()

    # Save results to file
    import json

    with open("performance_benchmark_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print("\nResults saved to performance_benchmark_results.json")
