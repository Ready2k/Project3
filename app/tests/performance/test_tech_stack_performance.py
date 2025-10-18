"""
Performance benchmarks for tech stack generation system.

This module provides comprehensive performance testing for large requirement processing,
concurrent operations, and system scalability validation.
"""

import pytest
import time
import concurrent.futures
from typing import Dict, List, Any, Optional, Tuple
from unittest.mock import Mock
import json
import psutil
import gc
from dataclasses import dataclass

from app.services.tech_stack_generator import TechStackGenerator
from app.services.requirement_parsing.enhanced_parser import EnhancedRequirementParser


@dataclass
class PerformanceMetrics:
    """Performance metrics for tech stack generation operations."""

    operation_name: str
    execution_time: float
    memory_usage_mb: float
    cpu_usage_percent: float
    throughput_ops_per_sec: float
    success_rate: float
    error_count: int

    def to_dict(self) -> Dict[str, Any]:
        """Convert metrics to dictionary for reporting."""
        return {
            "operation": self.operation_name,
            "execution_time_ms": round(self.execution_time * 1000, 2),
            "memory_usage_mb": round(self.memory_usage_mb, 2),
            "cpu_usage_percent": round(self.cpu_usage_percent, 2),
            "throughput_ops_per_sec": round(self.throughput_ops_per_sec, 2),
            "success_rate": round(self.success_rate, 4),
            "error_count": self.error_count,
        }


class PerformanceTestSuite:
    """Comprehensive performance test suite for tech stack generation."""

    def __init__(self):
        self.metrics_history: List[PerformanceMetrics] = []
        self.baseline_metrics: Optional[Dict[str, PerformanceMetrics]] = None

    def measure_performance(
        self, operation_name: str, operation_func, *args, **kwargs
    ) -> PerformanceMetrics:
        """Measure performance metrics for a given operation."""
        # Get initial system state
        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        initial_cpu = process.cpu_percent()

        # Force garbage collection for consistent measurements
        gc.collect()

        # Execute operation and measure time
        start_time = time.time()
        success_count = 0
        error_count = 0

        try:
            operation_func(*args, **kwargs)
            success_count = 1
        except Exception:
            error_count = 1

        end_time = time.time()
        execution_time = end_time - start_time

        # Get final system state
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        final_cpu = process.cpu_percent()

        # Calculate metrics
        memory_usage = final_memory - initial_memory
        cpu_usage = max(final_cpu - initial_cpu, 0)  # Avoid negative values
        throughput = 1 / execution_time if execution_time > 0 else 0
        success_rate = success_count / (success_count + error_count)

        metrics = PerformanceMetrics(
            operation_name=operation_name,
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=cpu_usage,
            throughput_ops_per_sec=throughput,
            success_rate=success_rate,
            error_count=error_count,
        )

        self.metrics_history.append(metrics)
        return metrics

    def measure_batch_performance(
        self,
        operation_name: str,
        operation_func,
        batch_args: List[Tuple],
        iterations: int = 1,
    ) -> PerformanceMetrics:
        """Measure performance for batch operations."""
        start_time = time.time()
        success_count = 0
        error_count = 0

        process = psutil.Process()
        initial_memory = process.memory_info().rss / 1024 / 1024

        for _ in range(iterations):
            for args in batch_args:
                try:
                    operation_func(*args)
                    success_count += 1
                except Exception:
                    error_count += 1

        end_time = time.time()
        execution_time = end_time - start_time

        final_memory = process.memory_info().rss / 1024 / 1024
        memory_usage = final_memory - initial_memory

        total_operations = len(batch_args) * iterations
        throughput = total_operations / execution_time if execution_time > 0 else 0
        success_rate = success_count / total_operations if total_operations > 0 else 0

        metrics = PerformanceMetrics(
            operation_name=f"{operation_name}_batch",
            execution_time=execution_time,
            memory_usage_mb=memory_usage,
            cpu_usage_percent=0,  # Difficult to measure accurately for batch
            throughput_ops_per_sec=throughput,
            success_rate=success_rate,
            error_count=error_count,
        )

        self.metrics_history.append(metrics)
        return metrics

    def set_baseline(self, operation_name: str, metrics: PerformanceMetrics):
        """Set baseline metrics for comparison."""
        if self.baseline_metrics is None:
            self.baseline_metrics = {}
        self.baseline_metrics[operation_name] = metrics

    def compare_to_baseline(
        self, operation_name: str, current_metrics: PerformanceMetrics
    ) -> Dict[str, float]:
        """Compare current metrics to baseline."""
        if not self.baseline_metrics or operation_name not in self.baseline_metrics:
            return {}

        baseline = self.baseline_metrics[operation_name]

        return {
            "execution_time_ratio": current_metrics.execution_time
            / baseline.execution_time,
            "memory_usage_ratio": current_metrics.memory_usage_mb
            / max(baseline.memory_usage_mb, 0.1),
            "throughput_ratio": current_metrics.throughput_ops_per_sec
            / max(baseline.throughput_ops_per_sec, 0.1),
            "success_rate_diff": current_metrics.success_rate - baseline.success_rate,
        }


class TestTechStackPerformance:
    """Performance tests for tech stack generation system."""

    @pytest.fixture
    def performance_suite(self):
        """Create performance test suite."""
        return PerformanceTestSuite()

    @pytest.fixture
    def tech_stack_generator(self):
        """Create tech stack generator with mocked LLM."""
        generator = TechStackGenerator()

        # Mock LLM provider for consistent performance testing
        def mock_generate_response(prompt):
            # Simulate processing time based on prompt length
            processing_time = len(prompt) / 10000  # Simulate processing
            time.sleep(processing_time)

            return json.dumps(
                {
                    "tech_stack": [
                        "Python",
                        "FastAPI",
                        "PostgreSQL",
                        "Redis",
                        "Docker",
                    ],
                    "reasoning": {
                        "Python": "Primary programming language",
                        "FastAPI": "High-performance web framework",
                        "PostgreSQL": "Reliable database",
                        "Redis": "Fast caching solution",
                        "Docker": "Containerization",
                    },
                    "confidence_score": 0.9,
                }
            )

        generator.llm_provider = Mock()
        generator.llm_provider.generate_response = Mock(
            side_effect=mock_generate_response
        )
        return generator

    @pytest.fixture
    def requirement_parser(self):
        """Create requirement parser."""
        return EnhancedRequirementParser()

    @pytest.fixture
    def large_requirements(self):
        """Generate large, complex requirements for performance testing."""
        return {
            "description": """
            Build a comprehensive enterprise-scale microservices platform that handles
            high-volume financial transactions with real-time processing capabilities.
            The system must integrate with multiple external APIs, process streaming data,
            maintain ACID compliance, and provide sub-second response times.
            
            Core services include user authentication, payment processing, fraud detection,
            risk management, reporting, and analytics. The platform should support
            horizontal scaling, multi-region deployment, and disaster recovery.
            
            Technology requirements include containerization with Kubernetes,
            service mesh for inter-service communication, distributed caching,
            event-driven architecture, and comprehensive monitoring and observability.
            
            Data storage needs include relational databases for transactional data,
            time-series databases for metrics, document stores for flexible schemas,
            and data lakes for analytics. Real-time streaming processing is required
            for fraud detection and risk assessment.
            
            Security requirements include end-to-end encryption, OAuth 2.0 authentication,
            role-based access control, audit logging, and compliance with financial
            regulations including PCI DSS, SOX, and regional data protection laws.
            
            The system must handle peak loads of 100,000+ transactions per second,
            maintain 99.99% uptime, and provide real-time dashboards for business
            intelligence and operational monitoring.
            """,
            "domain": "financial_services",
            "architecture": "microservices",
            "explicit_technologies": [
                "Kubernetes",
                "Docker",
                "Istio",
                "Redis",
                "PostgreSQL",
                "MongoDB",
                "Apache Kafka",
                "Elasticsearch",
                "Prometheus",
                "Grafana",
                "Jaeger",
                "Vault",
                "Consul",
                "NGINX",
                "HAProxy",
                "RabbitMQ",
                "Apache Spark",
                "Apache Flink",
                "InfluxDB",
                "Cassandra",
                "MinIO",
                "Keycloak",
                "Spring Boot",
                "Node.js",
                "Python",
                "Go",
                "React",
                "Angular",
            ],
            "performance_requirements": {
                "throughput": "100k_tps",
                "latency": "sub_second",
                "availability": "99.99%",
            },
            "compliance": ["PCI DSS", "SOX", "GDPR", "CCPA"],
            "scalability": "horizontal",
            "deployment": "multi_region",
            "monitoring": "comprehensive",
        }

    @pytest.fixture
    def medium_requirements_batch(self):
        """Generate batch of medium-sized requirements."""
        base_requirements = [
            {
                "description": "Build web application with user authentication and data processing",
                "explicit_technologies": ["Python", "FastAPI", "PostgreSQL", "Redis"],
                "domain": "web_application",
            },
            {
                "description": "Create API gateway with rate limiting and monitoring",
                "explicit_technologies": ["NGINX", "Kong", "Prometheus", "Grafana"],
                "domain": "api_management",
            },
            {
                "description": "Implement data pipeline with batch and stream processing",
                "explicit_technologies": [
                    "Apache Kafka",
                    "Apache Spark",
                    "Elasticsearch",
                ],
                "domain": "data_processing",
            },
            {
                "description": "Deploy microservices with container orchestration",
                "explicit_technologies": ["Docker", "Kubernetes", "Istio", "Helm"],
                "domain": "microservices",
            },
            {
                "description": "Build analytics platform with machine learning",
                "explicit_technologies": ["Python", "TensorFlow", "Jupyter", "MLflow"],
                "domain": "machine_learning",
            },
        ]

        # Multiply to create larger batch
        return base_requirements * 10  # 50 requirements total

    # Single Operation Performance Tests

    def test_single_tech_stack_generation_performance(
        self, performance_suite, tech_stack_generator, large_requirements
    ):
        """Test performance of single tech stack generation with large requirements."""
        metrics = performance_suite.measure_performance(
            "single_tech_stack_generation",
            tech_stack_generator.generate_tech_stack,
            large_requirements,
        )

        # Performance assertions
        assert (
            metrics.execution_time < 10.0
        ), f"Single generation took too long: {metrics.execution_time:.2f}s"
        assert (
            metrics.memory_usage_mb < 100.0
        ), f"High memory usage: {metrics.memory_usage_mb:.2f}MB"
        assert metrics.success_rate == 1.0, f"Operation failed: {metrics.success_rate}"
        assert (
            metrics.throughput_ops_per_sec > 0.1
        ), f"Low throughput: {metrics.throughput_ops_per_sec:.2f} ops/s"

        # Set as baseline for future comparisons
        performance_suite.set_baseline("single_tech_stack_generation", metrics)

        print(f"Single Tech Stack Generation Performance: {metrics.to_dict()}")

    def test_requirement_parsing_performance(
        self, performance_suite, requirement_parser, large_requirements
    ):
        """Test performance of requirement parsing with large text."""
        metrics = performance_suite.measure_performance(
            "requirement_parsing",
            requirement_parser.parse_requirements,
            large_requirements,
        )

        # Performance assertions
        assert (
            metrics.execution_time < 5.0
        ), f"Parsing took too long: {metrics.execution_time:.2f}s"
        assert (
            metrics.memory_usage_mb < 50.0
        ), f"High memory usage: {metrics.memory_usage_mb:.2f}MB"
        assert metrics.success_rate == 1.0, f"Parsing failed: {metrics.success_rate}"

        print(f"Requirement Parsing Performance: {metrics.to_dict()}")

    # Batch Processing Performance Tests

    def test_batch_tech_stack_generation_performance(
        self, performance_suite, tech_stack_generator, medium_requirements_batch
    ):
        """Test performance of batch tech stack generation."""
        batch_args = [(req,) for req in medium_requirements_batch]

        metrics = performance_suite.measure_batch_performance(
            "batch_tech_stack_generation",
            tech_stack_generator.generate_tech_stack,
            batch_args,
            iterations=1,
        )

        # Performance assertions
        assert (
            metrics.execution_time < 60.0
        ), f"Batch processing took too long: {metrics.execution_time:.2f}s"
        assert (
            metrics.throughput_ops_per_sec > 1.0
        ), f"Low batch throughput: {metrics.throughput_ops_per_sec:.2f} ops/s"
        assert (
            metrics.success_rate >= 0.95
        ), f"High failure rate: {metrics.success_rate:.2%}"
        assert (
            metrics.memory_usage_mb < 200.0
        ), f"High memory usage: {metrics.memory_usage_mb:.2f}MB"

        print(f"Batch Tech Stack Generation Performance: {metrics.to_dict()}")

    # Concurrent Processing Performance Tests

    def test_concurrent_tech_stack_generation_performance(
        self, performance_suite, tech_stack_generator, medium_requirements_batch
    ):
        """Test performance under concurrent load."""

        def concurrent_operation():
            results = []
            errors = []

            def process_requirement(req):
                try:
                    return tech_stack_generator.generate_tech_stack(req)
                except Exception as e:
                    return e

            # Use ThreadPoolExecutor for concurrent processing
            with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
                futures = [
                    executor.submit(process_requirement, req)
                    for req in medium_requirements_batch[:20]
                ]

                for future in concurrent.futures.as_completed(futures):
                    result = future.result()
                    if isinstance(result, Exception):
                        errors.append(result)
                    else:
                        results.append(result)

            return {"results": results, "errors": errors}

        metrics = performance_suite.measure_performance(
            "concurrent_tech_stack_generation", concurrent_operation
        )

        # Performance assertions
        assert (
            metrics.execution_time < 30.0
        ), f"Concurrent processing took too long: {metrics.execution_time:.2f}s"
        assert (
            metrics.success_rate == 1.0
        ), f"Concurrent operation failed: {metrics.success_rate}"
        assert (
            metrics.memory_usage_mb < 150.0
        ), f"High memory usage: {metrics.memory_usage_mb:.2f}MB"

        print(f"Concurrent Tech Stack Generation Performance: {metrics.to_dict()}")

    # Memory and Resource Usage Tests

    def test_memory_usage_scaling(self, performance_suite, tech_stack_generator):
        """Test memory usage scaling with increasing requirement complexity."""
        complexity_levels = [
            (
                "simple",
                {
                    "description": "Build web app",
                    "explicit_technologies": ["Python", "FastAPI"],
                },
            ),
            (
                "medium",
                {
                    "description": "Build web app with database and caching",
                    "explicit_technologies": [
                        "Python",
                        "FastAPI",
                        "PostgreSQL",
                        "Redis",
                    ],
                },
            ),
            (
                "complex",
                {
                    "description": "Build microservices platform with monitoring",
                    "explicit_technologies": [
                        "Python",
                        "FastAPI",
                        "PostgreSQL",
                        "Redis",
                        "Docker",
                        "Kubernetes",
                        "Prometheus",
                        "Grafana",
                    ],
                },
            ),
            (
                "very_complex",
                {
                    "description": "Build enterprise platform with full stack",
                    "explicit_technologies": [
                        "Python",
                        "FastAPI",
                        "PostgreSQL",
                        "Redis",
                        "Docker",
                        "Kubernetes",
                        "Prometheus",
                        "Grafana",
                        "Elasticsearch",
                        "Kafka",
                        "NGINX",
                        "Vault",
                    ],
                },
            ),
        ]

        memory_usage_by_complexity = {}

        for complexity, requirements in complexity_levels:
            metrics = performance_suite.measure_performance(
                f"memory_scaling_{complexity}",
                tech_stack_generator.generate_tech_stack,
                requirements,
            )

            memory_usage_by_complexity[complexity] = metrics.memory_usage_mb

            # Memory usage should be reasonable for each complexity level
            max_memory_limits = {
                "simple": 20.0,
                "medium": 40.0,
                "complex": 80.0,
                "very_complex": 120.0,
            }

            assert (
                metrics.memory_usage_mb < max_memory_limits[complexity]
            ), f"High memory usage for {complexity}: {metrics.memory_usage_mb:.2f}MB"

        print(f"Memory Usage by Complexity: {memory_usage_by_complexity}")

    # Stress Testing

    def test_sustained_load_performance(self, performance_suite, tech_stack_generator):
        """Test performance under sustained load."""

        def sustained_load_operation():
            requirements = {
                "description": "Build application with standard stack",
                "explicit_technologies": ["Python", "FastAPI", "PostgreSQL", "Redis"],
            }

            results = []
            start_time = time.time()

            # Run for 30 seconds or 100 operations, whichever comes first
            while time.time() - start_time < 30 and len(results) < 100:
                try:
                    result = tech_stack_generator.generate_tech_stack(requirements)
                    results.append(result)
                except Exception as e:
                    results.append(e)

            return results

        metrics = performance_suite.measure_performance(
            "sustained_load", sustained_load_operation
        )

        # Sustained load assertions
        assert (
            metrics.execution_time <= 35.0
        ), f"Sustained load took too long: {metrics.execution_time:.2f}s"
        assert (
            metrics.success_rate == 1.0
        ), f"Sustained load failed: {metrics.success_rate}"
        assert (
            metrics.memory_usage_mb < 200.0
        ), f"High memory usage under load: {metrics.memory_usage_mb:.2f}MB"

        print(f"Sustained Load Performance: {metrics.to_dict()}")

    # Performance Regression Tests

    def test_performance_regression(
        self, performance_suite, tech_stack_generator, large_requirements
    ):
        """Test for performance regression compared to baseline."""
        # Run current performance test
        current_metrics = performance_suite.measure_performance(
            "regression_test",
            tech_stack_generator.generate_tech_stack,
            large_requirements,
        )

        # If we have baseline metrics, compare
        if (
            performance_suite.baseline_metrics
            and "single_tech_stack_generation" in performance_suite.baseline_metrics
        ):
            comparison = performance_suite.compare_to_baseline(
                "single_tech_stack_generation", current_metrics
            )

            # Performance regression thresholds
            assert (
                comparison.get("execution_time_ratio", 1.0) < 2.0
            ), f"Execution time regression: {comparison.get('execution_time_ratio', 1.0):.2f}x slower"
            assert (
                comparison.get("memory_usage_ratio", 1.0) < 2.0
            ), f"Memory usage regression: {comparison.get('memory_usage_ratio', 1.0):.2f}x more memory"
            assert (
                comparison.get("success_rate_diff", 0.0) >= -0.05
            ), f"Success rate regression: {comparison.get('success_rate_diff', 0.0):.2%} decrease"

            print(f"Performance Comparison to Baseline: {comparison}")
        else:
            print("No baseline metrics available for regression testing")

    # Scalability Tests

    def test_horizontal_scalability_simulation(
        self, performance_suite, tech_stack_generator
    ):
        """Simulate horizontal scalability by testing multiple instances."""

        def simulate_multiple_instances(instance_count: int):
            """Simulate multiple generator instances processing requests."""
            generators = [TechStackGenerator() for _ in range(instance_count)]

            # Mock all generators
            for gen in generators:
                gen.llm_provider = Mock()
                gen.llm_provider.generate_response = Mock(
                    return_value=json.dumps(
                        {
                            "tech_stack": ["Python", "FastAPI", "PostgreSQL"],
                            "confidence_score": 0.9,
                        }
                    )
                )

            requirements = {
                "description": "Build web application",
                "explicit_technologies": ["Python", "FastAPI", "PostgreSQL"],
            }

            # Process requests across instances
            results = []
            for i in range(instance_count * 5):  # 5 requests per instance
                generator = generators[i % instance_count]
                result = generator.generate_tech_stack(requirements)
                results.append(result)

            return results

        # Test different instance counts
        for instance_count in [1, 2, 4, 8]:
            metrics = performance_suite.measure_performance(
                f"scalability_{instance_count}_instances",
                simulate_multiple_instances,
                instance_count,
            )

            # Scalability assertions
            expected_throughput = (
                instance_count * 0.5
            )  # Expected minimum throughput per instance
            assert (
                metrics.throughput_ops_per_sec >= expected_throughput * 0.8
            ), f"Poor scalability with {instance_count} instances: {metrics.throughput_ops_per_sec:.2f} ops/s"

            print(f"Scalability with {instance_count} instances: {metrics.to_dict()}")


class TestTechStackPerformanceBenchmarks:
    """Benchmark tests for establishing performance baselines."""

    def test_establish_performance_baselines(self, tech_stack_generator):
        """Establish performance baselines for different operation types."""
        baselines = {}

        # Simple operation baseline
        simple_req = {
            "description": "Build simple web app",
            "explicit_technologies": ["Python", "FastAPI"],
        }

        start_time = time.time()
        result = tech_stack_generator.generate_tech_stack(simple_req)
        simple_time = time.time() - start_time

        baselines["simple_operation"] = {
            "execution_time": simple_time,
            "success": result is not None,
        }

        # Complex operation baseline
        complex_req = {
            "description": "Build enterprise microservices platform with monitoring and security",
            "explicit_technologies": [
                "Kubernetes",
                "Docker",
                "Istio",
                "Prometheus",
                "Grafana",
                "Vault",
                "PostgreSQL",
                "Redis",
                "Kafka",
                "Elasticsearch",
                "NGINX",
            ],
        }

        start_time = time.time()
        result = tech_stack_generator.generate_tech_stack(complex_req)
        complex_time = time.time() - start_time

        baselines["complex_operation"] = {
            "execution_time": complex_time,
            "success": result is not None,
        }

        # Batch operation baseline
        batch_reqs = [simple_req] * 10

        start_time = time.time()
        batch_results = []
        for req in batch_reqs:
            result = tech_stack_generator.generate_tech_stack(req)
            batch_results.append(result)
        batch_time = time.time() - start_time

        baselines["batch_operation"] = {
            "execution_time": batch_time,
            "throughput": len(batch_reqs) / batch_time,
            "success_rate": sum(1 for r in batch_results if r is not None)
            / len(batch_results),
        }

        # Performance baseline assertions
        assert (
            baselines["simple_operation"]["execution_time"] < 5.0
        ), "Simple operation baseline too slow"
        assert (
            baselines["complex_operation"]["execution_time"] < 15.0
        ), "Complex operation baseline too slow"
        assert (
            baselines["batch_operation"]["throughput"] > 0.5
        ), "Batch operation baseline too slow"

        # All operations should succeed
        assert baselines["simple_operation"]["success"], "Simple operation failed"
        assert baselines["complex_operation"]["success"], "Complex operation failed"
        assert (
            baselines["batch_operation"]["success_rate"] >= 0.9
        ), "Batch operation success rate too low"

        print("Performance Baselines Established:")
        for operation, metrics in baselines.items():
            print(f"  {operation}: {metrics}")

        return baselines


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short", "-m", "not performance"])
