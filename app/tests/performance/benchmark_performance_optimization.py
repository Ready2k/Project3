"""
Performance benchmark for the advanced prompt defense system.

This script measures the performance impact of the optimization features
and verifies that the system meets the <50ms latency target.
"""

import asyncio
import time
import statistics
from typing import List, Dict, Any

from app.security.advanced_prompt_defender import AdvancedPromptDefender
from app.security.defense_config import AdvancedPromptDefenseConfig


class PerformanceBenchmark:
    """Performance benchmark for security validation."""
    
    def __init__(self):
        self.results: Dict[str, List[float]] = {}
    
    async def benchmark_caching_performance(self) -> Dict[str, Any]:
        """Benchmark caching performance improvement."""
        print("🔄 Benchmarking caching performance...")
        
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = True
        config.parallel_detection = True
        
        defender = AdvancedPromptDefender(config)
        test_input = "Evaluate the feasibility of automating our customer onboarding process with AI"
        
        # Measure cache miss performance (first validation)
        cache_miss_times = []
        for i in range(5):
            unique_input = f"{test_input} - iteration {i}"
            start_time = time.time()
            await defender.validate_input(unique_input, f"cache_miss_{i}")
            cache_miss_times.append((time.time() - start_time) * 1000)
        
        # Measure cache hit performance (repeated validations)
        cache_hit_times = []
        for i in range(10):
            start_time = time.time()
            await defender.validate_input(test_input, f"cache_hit_{i}")
            cache_hit_times.append((time.time() - start_time) * 1000)
        
        avg_cache_miss = statistics.mean(cache_miss_times)
        avg_cache_hit = statistics.mean(cache_hit_times)
        improvement_ratio = avg_cache_miss / avg_cache_hit
        
        metrics = defender.get_performance_metrics()
        
        return {
            'avg_cache_miss_ms': avg_cache_miss,
            'avg_cache_hit_ms': avg_cache_hit,
            'improvement_ratio': improvement_ratio,
            'cache_hit_rate': metrics['cache_metrics']['hit_rate_percent'],
            'total_validations': metrics['validation_metrics']['total_validations']
        }
    
    async def benchmark_parallel_vs_sequential(self) -> Dict[str, Any]:
        """Benchmark parallel vs sequential detection performance."""
        print("⚡ Benchmarking parallel vs sequential performance...")
        
        test_input = """
        I need to assess the automation potential for our complex business process that involves:
        1. Document verification and validation
        2. Multi-system data integration
        3. Approval workflow management
        4. Compliance checking and reporting
        5. Customer notification and follow-up
        Please evaluate the feasibility of AI automation for this comprehensive workflow.
        """
        
        # Test with parallel detection
        parallel_config = AdvancedPromptDefenseConfig()
        parallel_config.enable_caching = False  # Disable caching to measure pure parallel performance
        parallel_config.parallel_detection = True
        parallel_defender = AdvancedPromptDefender(parallel_config)
        
        parallel_times = []
        for i in range(5):
            start_time = time.time()
            await parallel_defender.validate_input(f"{test_input} - parallel {i}", f"parallel_{i}")
            parallel_times.append((time.time() - start_time) * 1000)
        
        # Test with sequential detection
        sequential_config = AdvancedPromptDefenseConfig()
        sequential_config.enable_caching = False
        sequential_config.parallel_detection = False
        sequential_defender = AdvancedPromptDefender(sequential_config)
        
        sequential_times = []
        for i in range(5):
            start_time = time.time()
            await sequential_defender.validate_input(f"{test_input} - sequential {i}", f"sequential_{i}")
            sequential_times.append((time.time() - start_time) * 1000)
        
        avg_parallel = statistics.mean(parallel_times)
        avg_sequential = statistics.mean(sequential_times)
        speedup_ratio = avg_sequential / avg_parallel
        
        return {
            'avg_parallel_ms': avg_parallel,
            'avg_sequential_ms': avg_sequential,
            'speedup_ratio': speedup_ratio,
            'parallel_efficiency': (speedup_ratio - 1) * 100  # Percentage improvement
        }
    
    async def benchmark_latency_target_compliance(self) -> Dict[str, Any]:
        """Benchmark compliance with <50ms latency target."""
        print("🎯 Benchmarking latency target compliance...")
        
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = True
        config.parallel_detection = True
        config.max_validation_time_ms = 50
        
        defender = AdvancedPromptDefender(config)
        
        # Test various input types
        test_cases = [
            ("Short input", "Simple automation request"),
            ("Medium input", "Evaluate the feasibility of automating our customer service workflow"),
            ("Long input", "I need a comprehensive assessment of automating our complex multi-step business process that involves document processing, data validation, system integration, approval workflows, compliance checking, and customer communications"),
            ("Repeated input", "Evaluate the feasibility of automating our customer service workflow"),  # Should hit cache
        ]
        
        all_latencies = []
        case_results = {}
        
        for case_name, test_input in test_cases:
            latencies = []
            for i in range(10):
                start_time = time.time()
                await defender.validate_input(test_input, f"{case_name}_{i}")
                latency_ms = (time.time() - start_time) * 1000
                latencies.append(latency_ms)
                all_latencies.append(latency_ms)
            
            case_results[case_name] = {
                'avg_latency_ms': statistics.mean(latencies),
                'max_latency_ms': max(latencies),
                'min_latency_ms': min(latencies),
                'meets_target': all(latency < 50 for latency in latencies)
            }
        
        overall_avg = statistics.mean(all_latencies)
        target_compliance = sum(1 for latency in all_latencies if latency < 50) / len(all_latencies) * 100
        
        return {
            'overall_avg_latency_ms': overall_avg,
            'target_compliance_percent': target_compliance,
            'meets_target_overall': overall_avg < 50,
            'case_results': case_results,
            'total_validations': len(all_latencies)
        }
    
    async def benchmark_memory_efficiency(self) -> Dict[str, Any]:
        """Benchmark memory usage efficiency."""
        print("💾 Benchmarking memory efficiency...")
        
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = True
        config.cache_size = 1000
        config.parallel_detection = True
        
        defender = AdvancedPromptDefender(config)
        
        # Perform many validations to test memory usage
        for i in range(100):
            test_input = f"Memory efficiency test input number {i} with varying content"
            await defender.validate_input(test_input, f"memory_test_{i}")
        
        metrics = defender.get_performance_metrics()
        
        return {
            'cache_size': metrics['cache_metrics']['size'],
            'cache_max_size': metrics['cache_metrics']['max_size'],
            'cache_utilization_percent': (metrics['cache_metrics']['size'] / metrics['cache_metrics']['max_size']) * 100,
            'memory_usage_mb': metrics['resource_metrics'].get('current_memory_mb', 0),
            'total_validations': metrics['validation_metrics']['total_validations']
        }
    
    async def benchmark_concurrent_performance(self) -> Dict[str, Any]:
        """Benchmark performance under concurrent load."""
        print("🚀 Benchmarking concurrent performance...")
        
        config = AdvancedPromptDefenseConfig()
        config.enable_caching = True
        config.parallel_detection = True
        
        defender = AdvancedPromptDefender(config)
        
        # Create concurrent validation tasks
        async def validate_task(task_id: int):
            test_input = f"Concurrent validation test {task_id} for business automation"
            start_time = time.time()
            result = await defender.validate_input(test_input, f"concurrent_{task_id}")
            return (time.time() - start_time) * 1000, result.action
        
        # Run 20 concurrent validations
        start_time = time.time()
        tasks = [validate_task(i) for i in range(20)]
        results = await asyncio.gather(*tasks)
        total_time = (time.time() - start_time) * 1000
        
        latencies = [result[0] for result in results]
        actions = [result[1] for result in results]
        
        return {
            'total_time_ms': total_time,
            'avg_latency_ms': statistics.mean(latencies),
            'max_latency_ms': max(latencies),
            'min_latency_ms': min(latencies),
            'concurrent_validations': len(results),
            'throughput_per_second': len(results) / (total_time / 1000),
            'all_successful': all(action is not None for action in actions)
        }
    
    async def run_full_benchmark(self) -> Dict[str, Any]:
        """Run complete performance benchmark suite."""
        print("🏁 Starting comprehensive performance benchmark...")
        print("=" * 60)
        
        results = {}
        
        # Run all benchmarks
        results['caching'] = await self.benchmark_caching_performance()
        results['parallel_vs_sequential'] = await self.benchmark_parallel_vs_sequential()
        results['latency_compliance'] = await self.benchmark_latency_target_compliance()
        results['memory_efficiency'] = await self.benchmark_memory_efficiency()
        results['concurrent_performance'] = await self.benchmark_concurrent_performance()
        
        return results
    
    def print_benchmark_results(self, results: Dict[str, Any]) -> None:
        """Print formatted benchmark results."""
        print("\n" + "=" * 60)
        print("📊 PERFORMANCE BENCHMARK RESULTS")
        print("=" * 60)
        
        # Caching Performance
        caching = results['caching']
        print("\n🔄 CACHING PERFORMANCE:")
        print(f"   Cache Miss Avg:     {caching['avg_cache_miss_ms']:.2f}ms")
        print(f"   Cache Hit Avg:      {caching['avg_cache_hit_ms']:.2f}ms")
        print(f"   Improvement Ratio:  {caching['improvement_ratio']:.2f}x faster")
        print(f"   Cache Hit Rate:     {caching['cache_hit_rate']:.1f}%")
        
        # Parallel vs Sequential
        parallel = results['parallel_vs_sequential']
        print("\n⚡ PARALLEL vs SEQUENTIAL:")
        print(f"   Parallel Avg:       {parallel['avg_parallel_ms']:.2f}ms")
        print(f"   Sequential Avg:     {parallel['avg_sequential_ms']:.2f}ms")
        print(f"   Speedup Ratio:      {parallel['speedup_ratio']:.2f}x faster")
        print(f"   Efficiency Gain:    {parallel['parallel_efficiency']:.1f}%")
        
        # Latency Target Compliance
        latency = results['latency_compliance']
        print("\n🎯 LATENCY TARGET COMPLIANCE:")
        print(f"   Overall Avg:        {latency['overall_avg_latency_ms']:.2f}ms")
        print(f"   Target Compliance:  {latency['target_compliance_percent']:.1f}%")
        print(f"   Meets <50ms Target: {'✅ YES' if latency['meets_target_overall'] else '❌ NO'}")
        
        for case_name, case_data in latency['case_results'].items():
            status = "✅" if case_data['meets_target'] else "❌"
            print(f"   {case_name:15} {case_data['avg_latency_ms']:6.2f}ms {status}")
        
        # Memory Efficiency
        memory = results['memory_efficiency']
        print("\n💾 MEMORY EFFICIENCY:")
        print(f"   Cache Utilization:  {memory['cache_utilization_percent']:.1f}%")
        print(f"   Memory Usage:       {memory['memory_usage_mb']:.1f}MB")
        print(f"   Total Validations:  {memory['total_validations']}")
        
        # Concurrent Performance
        concurrent = results['concurrent_performance']
        print("\n🚀 CONCURRENT PERFORMANCE:")
        print(f"   Total Time:         {concurrent['total_time_ms']:.2f}ms")
        print(f"   Avg Latency:        {concurrent['avg_latency_ms']:.2f}ms")
        print(f"   Throughput:         {concurrent['throughput_per_second']:.1f} validations/sec")
        print(f"   All Successful:     {'✅ YES' if concurrent['all_successful'] else '❌ NO'}")
        
        # Overall Assessment
        print("\n🏆 OVERALL ASSESSMENT:")
        meets_latency = latency['meets_target_overall']
        good_caching = caching['improvement_ratio'] > 2.0
        good_parallel = parallel['speedup_ratio'] > 1.2
        good_throughput = concurrent['throughput_per_second'] > 10
        
        score = sum([meets_latency, good_caching, good_parallel, good_throughput])
        
        print(f"   Latency Target:     {'✅' if meets_latency else '❌'} <50ms average")
        print(f"   Caching Effective:  {'✅' if good_caching else '❌'} >2x improvement")
        print(f"   Parallel Speedup:   {'✅' if good_parallel else '❌'} >1.2x faster")
        print(f"   High Throughput:    {'✅' if good_throughput else '❌'} >10 val/sec")
        print(f"   Overall Score:      {score}/4 {'🌟' if score >= 3 else '⚠️'}")
        
        print("\n" + "=" * 60)


async def main():
    """Run the performance benchmark."""
    benchmark = PerformanceBenchmark()
    results = await benchmark.run_full_benchmark()
    benchmark.print_benchmark_results(results)


if __name__ == "__main__":
    asyncio.run(main())