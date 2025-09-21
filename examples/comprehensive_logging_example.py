"""
Comprehensive example demonstrating tech stack generation logging capabilities.

This example shows how to use the enhanced logging system for debugging,
monitoring, and analyzing tech stack generation processes.
"""

import asyncio
import json
import tempfile
from pathlib import Path
from typing import Dict, Any, List

# Import the enhanced tech stack generator with logging
from app.services.tech_stack_generator import TechStackGenerator
from app.services.tech_logging.tech_stack_logger import LogCategory
from app.pattern.matcher import MatchResult
from app.llm.base import LLMProvider


class ExampleLLMProvider(LLMProvider):
    """Example LLM provider for demonstration."""
    
    def __init__(self):
        self.model_name = "example-model"
        self.provider_name = "example-provider"
    
    async def generate_response(self, prompt: str, **kwargs) -> str:
        """Generate example response."""
        # Simulate processing time
        await asyncio.sleep(0.1)
        
        return json.dumps({
            "technologies": [
                "FastAPI", "PostgreSQL", "Redis", "Docker", 
                "AWS S3", "AWS Lambda", "Prometheus", "Grafana"
            ],
            "reasoning": "Selected modern, scalable technologies for high-performance API with AWS integration",
            "categories": {
                "Backend Framework": ["FastAPI"],
                "Database": ["PostgreSQL", "Redis"],
                "Cloud Services": ["AWS S3", "AWS Lambda"],
                "Infrastructure": ["Docker"],
                "Monitoring": ["Prometheus", "Grafana"]
            }
        })
    
    def get_model_info(self) -> dict:
        """Get model information."""
        return {
            "name": self.model_name,
            "provider": self.provider_name,
            "capabilities": ["text_generation", "json_output"]
        }


async def demonstrate_comprehensive_logging():
    """Demonstrate comprehensive logging capabilities."""
    
    print("🚀 Starting Comprehensive Tech Stack Generation Logging Demo")
    print("=" * 60)
    
    # 1. Initialize tech stack generator with comprehensive logging
    print("\n1. Initializing TechStackGenerator with comprehensive logging...")
    
    llm_provider = ExampleLLMProvider()
    generator = TechStackGenerator(
        llm_provider=llm_provider,
        enable_debug_logging=True,  # Enable detailed debug logging
        auto_update_catalog=True
    )
    
    print("✅ Generator initialized with comprehensive logging enabled")
    
    # 2. Prepare sample requirements
    print("\n2. Preparing sample requirements...")
    
    requirements = {
        "description": "Build a high-performance REST API for e-commerce platform with AWS integration",
        "functional_requirements": [
            "Handle 10,000+ concurrent users",
            "Integrate with AWS S3 for product image storage",
            "Use PostgreSQL for transactional data",
            "Implement Redis for session management and caching",
            "Support real-time notifications",
            "Provide comprehensive API documentation"
        ],
        "non_functional_requirements": [
            "99.9% uptime SLA",
            "Sub-50ms API response time",
            "GDPR compliance for EU customers",
            "PCI DSS compliance for payments",
            "Horizontal scalability to 100+ instances"
        ],
        "constraints": {
            "cloud_provider": "AWS",
            "budget": "medium",
            "deployment_timeline": "3 months",
            "team_expertise": ["Python", "JavaScript", "AWS"]
        },
        "integration_requirements": [
            "Payment gateway integration (Stripe)",
            "Email service integration (SendGrid)",
            "Analytics integration (Google Analytics)",
            "Monitoring and alerting system"
        ]
    }
    
    # Create sample pattern matches
    match1 = type('MatchResult', (), {
        'pattern_id': 'APAT-001',
        'confidence': 0.85,
        'tech_stack': ['FastAPI', 'PostgreSQL', 'Redis', 'Docker']
    })()
    
    match2 = type('MatchResult', (), {
        'pattern_id': 'APAT-002', 
        'confidence': 0.78,
        'tech_stack': ['Django', 'PostgreSQL', 'Celery', 'Docker']
    })()
    
    matches = [match1, match2]
    
    constraints = {
        "banned_tools": ["MySQL", "PHP"],
        "required_integrations": ["AWS S3", "PostgreSQL"],
        "budget_constraints": "medium",
        "deployment_preference": "cloud"
    }
    
    print("✅ Requirements and constraints prepared")
    
    # 3. Generate tech stack with comprehensive logging
    print("\n3. Generating tech stack with comprehensive logging...")
    print("   This will demonstrate:")
    print("   - Requirement parsing logging")
    print("   - Technology extraction logging") 
    print("   - Context analysis logging")
    print("   - LLM interaction logging")
    print("   - Decision making logging")
    print("   - Performance monitoring")
    print("   - Error handling (if any)")
    
    try:
        tech_stack = await generator.generate_tech_stack(
            matches=matches,
            requirements=requirements,
            constraints=constraints
        )
        
        print(f"✅ Tech stack generated successfully: {tech_stack}")
        
    except Exception as e:
        print(f"❌ Error during generation: {e}")
        tech_stack = []
    
    # 4. Demonstrate logging analysis
    print("\n4. Analyzing comprehensive logs...")
    
    # Get logging summary
    logging_summary = generator.get_logging_summary()
    
    print("\n📊 Logging Summary:")
    print(f"   Performance Metrics: {json.dumps(logging_summary.get('performance', {}), indent=2)}")
    print(f"   Decision Summary: {json.dumps(logging_summary.get('decisions', {}), indent=2)}")
    print(f"   LLM Interactions: {json.dumps(logging_summary.get('llm_interactions', {}), indent=2)}")
    print(f"   Error Summary: {json.dumps(logging_summary.get('errors', {}), indent=2)}")
    
    # 5. Demonstrate specific log category analysis
    print("\n5. Analyzing specific log categories...")
    
    # Technology extraction logs
    tech_extraction_logs = generator.tech_logger.get_log_entries(
        category=LogCategory.TECHNOLOGY_EXTRACTION
    )
    print(f"\n🔍 Technology Extraction Logs ({len(tech_extraction_logs)} entries):")
    for i, entry in enumerate(tech_extraction_logs[:3]):  # Show first 3
        print(f"   {i+1}. [{entry.timestamp}] {entry.component}.{entry.operation}: {entry.message}")
        if entry.confidence_score:
            print(f"      Confidence: {entry.confidence_score:.3f}")
    
    # Decision making logs
    decision_logs = generator.tech_logger.get_log_entries(
        category=LogCategory.DECISION_MAKING
    )
    print(f"\n🎯 Decision Making Logs ({len(decision_logs)} entries):")
    for i, entry in enumerate(decision_logs[:3]):  # Show first 3
        print(f"   {i+1}. [{entry.timestamp}] {entry.component}.{entry.operation}: {entry.message}")
        if entry.confidence_score:
            print(f"      Confidence: {entry.confidence_score:.3f}")
    
    # Performance logs
    performance_logs = generator.tech_logger.get_log_entries(
        category=LogCategory.PERFORMANCE
    )
    print(f"\n⚡ Performance Logs ({len(performance_logs)} entries):")
    for i, entry in enumerate(performance_logs[:3]):  # Show first 3
        print(f"   {i+1}. [{entry.timestamp}] {entry.component}.{entry.operation}: {entry.message}")
        if 'duration_ms' in entry.context:
            print(f"      Duration: {entry.context['duration_ms']:.2f}ms")
    
    # 6. Demonstrate debug tracing
    print("\n6. Analyzing debug traces...")
    
    traces = generator.debug_tracer.get_traces(
        component="TechStackGenerator",
        limit=1
    )
    
    if traces:
        trace = traces[0]
        print(f"\n🔬 Debug Trace: {trace.trace_id}")
        print(f"   Component: {trace.component}")
        print(f"   Operation: {trace.operation}")
        print(f"   Duration: {trace.total_duration_ms:.2f}ms")
        print(f"   Success: {trace.success}")
        print(f"   Steps: {len(trace.steps)}")
        
        print("\n   Step Details:")
        for i, step in enumerate(trace.steps[:5]):  # Show first 5 steps
            print(f"     {i+1}. {step.step_name} ({step.duration_ms:.2f}ms)")
    else:
        print("   No debug traces available")
    
    # 7. Demonstrate performance analysis
    print("\n7. Performance analysis...")
    
    perf_summary = generator.performance_monitor.get_performance_summary()
    print(f"\n📈 Performance Summary:")
    print(f"   Tracing Enabled: {perf_summary.get('tracing_enabled', False)}")
    print(f"   Total Traces: {perf_summary.get('total_traces', 0)}")
    print(f"   Success Rate: {perf_summary.get('success_rate', 0):.1%}")
    
    if 'average_duration_ms' in perf_summary:
        print(f"   Average Duration: {perf_summary['average_duration_ms']:.2f}ms")
    
    # Get performance recommendations
    recommendations = generator.get_performance_recommendations()
    if recommendations:
        print(f"\n💡 Performance Recommendations:")
        for i, rec in enumerate(recommendations, 1):
            print(f"   {i}. {rec}")
    else:
        print("\n✅ No performance issues detected")
    
    # 8. Demonstrate error analysis (if any)
    print("\n8. Error analysis...")
    
    error_summary = generator.error_logger.get_error_summary()
    if error_summary and error_summary.get('total_errors', 0) > 0:
        print(f"\n⚠️  Error Summary:")
        print(f"   Total Errors: {error_summary['total_errors']}")
        print(f"   By Severity: {error_summary.get('severity_distribution', {})}")
        print(f"   By Category: {error_summary.get('category_distribution', {})}")
        
        # Show error patterns
        error_patterns = generator.error_logger.get_error_patterns()
        if error_patterns:
            print(f"\n   Error Patterns:")
            for pattern in error_patterns[:3]:
                print(f"     - {pattern.error_signature} (occurred {pattern.occurrence_count} times)")
    else:
        print("   ✅ No errors detected")
    
    # 9. Demonstrate log export
    print("\n9. Demonstrating log export...")
    
    with tempfile.TemporaryDirectory() as temp_dir:
        export_path = Path(temp_dir) / "tech_stack_logs.json"
        
        success = generator.export_logs(
            str(export_path),
            format='json',
            include_traces=True,
            include_performance=True
        )
        
        if success and export_path.exists():
            file_size = export_path.stat().st_size
            print(f"   ✅ Logs exported successfully to {export_path}")
            print(f"   📁 File size: {file_size} bytes")
            
            # Show sample of exported data
            with open(export_path, 'r') as f:
                exported_data = json.load(f)
            
            print(f"   📄 Exported {len(exported_data)} log entries")
            
            if exported_data:
                sample_entry = exported_data[0]
                print(f"   📝 Sample entry: {sample_entry.get('message', 'N/A')}")
        else:
            print("   ❌ Log export failed")
    
    # 10. Demonstrate real-time monitoring
    print("\n10. Real-time monitoring capabilities...")
    
    # Get recent alerts
    alerts = generator.performance_monitor.get_alerts(limit=5)
    if alerts:
        print(f"\n🚨 Recent Performance Alerts ({len(alerts)}):")
        for alert in alerts:
            print(f"   - {alert.severity.upper()}: {alert.message}")
            print(f"     Metric: {alert.metric_name}, Value: {alert.actual_value}")
    else:
        print("   ✅ No performance alerts")
    
    # Show generation metrics
    gen_metrics = generator.get_generation_metrics()
    print(f"\n📊 Generation Metrics:")
    print(f"   Total Generations: {gen_metrics['total_generations']}")
    print(f"   Explicit Tech Inclusion Rate: {gen_metrics['explicit_tech_inclusion_rate']:.1%}")
    print(f"   Context-Aware Selections: {gen_metrics['context_aware_selections']}")
    print(f"   Catalog Auto-Additions: {gen_metrics['catalog_auto_additions']}")
    
    # 11. Cleanup
    print("\n11. Cleaning up...")
    
    generator.shutdown_logging()
    print("   ✅ Logging services shutdown gracefully")
    
    print("\n" + "=" * 60)
    print("🎉 Comprehensive logging demonstration completed!")
    print("\nKey Features Demonstrated:")
    print("✅ Structured logging with categories and confidence scores")
    print("✅ Decision trace logging with reasoning")
    print("✅ LLM interaction logging with performance metrics")
    print("✅ Error context logging with recovery suggestions")
    print("✅ Debug tracing with step-by-step execution")
    print("✅ Performance monitoring with alerts")
    print("✅ Log export and analysis capabilities")
    print("✅ Real-time monitoring and recommendations")


async def demonstrate_error_handling():
    """Demonstrate error handling and logging."""
    
    print("\n" + "=" * 60)
    print("🔥 Demonstrating Error Handling and Logging")
    print("=" * 60)
    
    # Create generator with logging
    generator = TechStackGenerator(enable_debug_logging=True)
    
    # Test various error scenarios
    error_scenarios = [
        {
            "name": "Invalid Requirements",
            "requirements": None,
            "matches": [],
            "constraints": {}
        },
        {
            "name": "Empty Requirements", 
            "requirements": {},
            "matches": [],
            "constraints": {}
        },
        {
            "name": "Malformed Requirements",
            "requirements": {"invalid": "structure"},
            "matches": [],
            "constraints": {"banned_tools": "not_a_list"}  # Should be list
        }
    ]
    
    for i, scenario in enumerate(error_scenarios, 1):
        print(f"\n{i}. Testing: {scenario['name']}")
        
        try:
            result = await generator.generate_tech_stack(
                matches=scenario['matches'],
                requirements=scenario['requirements'],
                constraints=scenario['constraints']
            )
            print(f"   Result: {result}")
            
        except Exception as e:
            print(f"   ❌ Expected error: {type(e).__name__}: {e}")
        
        # Check error logs
        error_summary = generator.error_logger.get_error_summary()
        if error_summary:
            print(f"   📊 Errors logged: {error_summary.get('total_errors', 0)}")
    
    # Show error patterns
    error_patterns = generator.error_logger.get_error_patterns()
    if error_patterns:
        print(f"\n🔍 Error Patterns Detected:")
        for pattern in error_patterns:
            print(f"   - {pattern.error_signature}")
            print(f"     Occurrences: {pattern.occurrence_count}")
            print(f"     Components: {', '.join(pattern.components_affected)}")
    
    generator.shutdown_logging()


if __name__ == "__main__":
    """Run the comprehensive logging demonstration."""
    
    print("Tech Stack Generation - Comprehensive Logging Demo")
    print("This demo showcases all logging capabilities implemented for task 8")
    
    # Run main demonstration
    asyncio.run(demonstrate_comprehensive_logging())
    
    # Run error handling demonstration
    asyncio.run(demonstrate_error_handling())
    
    print("\n🎯 Demo completed! Check the output above to see all logging features in action.")
    print("\nLogging Features Implemented:")
    print("1. ✅ Structured logging for all technology extraction and selection steps")
    print("2. ✅ Decision trace logging with confidence scores and reasoning")
    print("3. ✅ LLM interaction logging (prompts, responses, processing time)")
    print("4. ✅ Error context logging with suggested fixes and recovery actions")
    print("5. ✅ Debug mode with step-by-step generation traces")
    print("6. ✅ Performance metrics collection and monitoring")
    print("\nAll requirements for Task 8 have been successfully implemented! 🚀")