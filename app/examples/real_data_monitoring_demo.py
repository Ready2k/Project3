"""
Demonstration of monitoring components connected to real tech stack generation data.

This example shows how the monitoring system now captures actual generation events
instead of using mock data.
"""

import asyncio

from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService
from app.monitoring.tech_stack_monitor import TechStackMonitor
from app.monitoring.quality_assurance import QualityAssuranceSystem
from app.monitoring.performance_monitor import PerformanceMonitor


class RealDataMonitoringDemo:
    """Demonstrates real data monitoring integration."""
    
    def __init__(self):
        self.monitoring_integration = TechStackMonitoringIntegrationService({
            'real_time_streaming': True,
            'buffer_size': 20
        })
        self.tech_monitor = TechStackMonitor()
        self.qa_system = QualityAssuranceSystem()
        self.performance_monitor = PerformanceMonitor()
    
    async def start_monitoring_systems(self):
        """Start all monitoring systems."""
        print("🚀 Starting monitoring systems...")
        
        await self.monitoring_integration.start_monitoring_integration()
        await self.tech_monitor.start_monitoring()
        await self.qa_system.start_qa_system()
        self.performance_monitor.start_monitoring()
        
        print("✅ All monitoring systems started")
    
    async def stop_monitoring_systems(self):
        """Stop all monitoring systems."""
        print("🛑 Stopping monitoring systems...")
        
        await self.monitoring_integration.stop_monitoring_integration()
        await self.tech_monitor.stop_monitoring()
        await self.qa_system.stop_qa_system()
        self.performance_monitor.stop_monitoring()
        
        print("✅ All monitoring systems stopped")
    
    async def simulate_real_tech_stack_generation(self):
        """Simulate a realistic tech stack generation process with real data."""
        print("\n📊 Simulating real tech stack generation with monitoring...")
        
        # Start generation session
        session = self.monitoring_integration.start_generation_monitoring(
            requirements={
                'business_requirements': 'Build a scalable e-commerce API',
                'technical_requirements': 'Use AWS services, Python, and microservices architecture',
                'constraints': {
                    'cloud_provider': 'aws',
                    'programming_language': 'python',
                    'architecture_pattern': 'microservices'
                }
            },
            metadata={
                'user_id': 'demo_user',
                'project_type': 'e-commerce',
                'complexity': 'high'
            }
        )
        
        print(f"📝 Started session: {session.session_id[:8]}...")
        
        # Step 1: Requirement parsing with real timing
        print("🔍 Parsing requirements...")
        await asyncio.sleep(0.12)  # Realistic parsing time
        
        await self.monitoring_integration.track_parsing_step(
            session_id=session.session_id,
            step_name='enhanced_requirement_parsing',
            input_data={
                'requirements_size': 156,
                'complexity_indicators': ['microservices', 'scalable', 'e-commerce']
            },
            output_data={
                'explicit_technologies': ['AWS', 'Python', 'microservices'],
                'confidence_score': 0.94,
                'context_clues': ['cloud', 'scalability', 'api'],
                'domain_indicators': ['e-commerce', 'web-services']
            },
            duration_ms=120.0,
            success=True
        )
        
        # Step 2: Technology extraction with realistic data
        print("⚙️ Extracting technologies...")
        await asyncio.sleep(0.18)
        
        await self.monitoring_integration.track_extraction_step(
            session_id=session.session_id,
            extraction_type='context_aware_extraction',
            extracted_technologies=[
                'AWS Lambda', 'Python', 'Amazon API Gateway', 
                'Amazon DynamoDB', 'Amazon RDS', 'Docker'
            ],
            confidence_scores={
                'AWS Lambda': 0.96,
                'Python': 0.95,
                'Amazon API Gateway': 0.92,
                'Amazon DynamoDB': 0.89,
                'Amazon RDS': 0.87,
                'Docker': 0.85
            },
            context_data={
                'ecosystem': 'aws',
                'domain': 'e-commerce',
                'architecture': 'microservices',
                'scalability_requirements': True
            },
            duration_ms=180.0,
            success=True
        )
        
        # Step 3: LLM interaction with realistic response
        print("🤖 Calling LLM for tech stack generation...")
        await asyncio.sleep(2.1)  # Realistic LLM response time
        
        await self.monitoring_integration.track_llm_interaction(
            session_id=session.session_id,
            provider='OpenAI',
            model='gpt-4',
            prompt_data={
                'prompt_type': 'context_aware_tech_stack_generation',
                'context_size': 1450,
                'explicit_technologies': ['AWS Lambda', 'Python', 'Amazon API Gateway'],
                'domain_context': 'e-commerce microservices'
            },
            response_data={
                'generated_technologies': [
                    'AWS Lambda', 'Python', 'Amazon API Gateway', 'Amazon DynamoDB',
                    'Amazon RDS', 'Docker', 'Amazon ECS', 'Amazon CloudWatch',
                    'AWS X-Ray', 'Amazon ElastiCache'
                ],
                'reasoning': 'Selected comprehensive microservices stack for e-commerce with monitoring and caching',
                'confidence': 0.91
            },
            token_usage={
                'prompt_tokens': 720,
                'completion_tokens': 280,
                'total_tokens': 1000
            },
            duration_ms=2100.0,
            success=True
        )
        
        # Step 4: Validation with conflict detection
        print("✅ Validating tech stack...")
        await asyncio.sleep(0.08)
        
        await self.monitoring_integration.track_validation_step(
            session_id=session.session_id,
            validation_type='ecosystem_compatibility_validation',
            input_technologies=[
                'AWS Lambda', 'Python', 'Amazon API Gateway', 'Amazon DynamoDB',
                'Amazon RDS', 'Docker', 'Amazon ECS', 'Amazon CloudWatch'
            ],
            validation_results={
                'ecosystem_consistency': True,
                'compatibility_score': 0.94,
                'conflicts_detected': 1,
                'performance_optimized': True
            },
            conflicts_detected=[
                {
                    'type': 'resource_overlap',
                    'description': 'Both DynamoDB and RDS selected - may be redundant',
                    'severity': 'low',
                    'technologies': ['Amazon DynamoDB', 'Amazon RDS']
                }
            ],
            resolutions_applied=[
                {
                    'conflict_id': 'resource_overlap_1',
                    'resolution': 'Keep both - DynamoDB for session data, RDS for transactional data',
                    'confidence': 0.88
                }
            ],
            duration_ms=80.0,
            success=True
        )
        
        # Step 5: Complete generation
        print("🎉 Completing generation...")
        
        final_tech_stack = [
            'AWS Lambda', 'Python', 'Amazon API Gateway', 'Amazon DynamoDB',
            'Amazon RDS', 'Docker', 'Amazon ECS', 'Amazon CloudWatch',
            'AWS X-Ray', 'Amazon ElastiCache'
        ]
        
        await self.monitoring_integration.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=final_tech_stack,
            generation_metrics={
                'extraction_accuracy': 0.94,
                'explicit_inclusion_rate': 0.90,
                'context_aware_selections': 7,
                'total_processing_time_ms': 2480,
                'generation_method': 'llm_enhanced',
                'explicit_technologies': ['AWS Lambda', 'Python', 'Amazon API Gateway'],
                'final_stack_size': len(final_tech_stack),
                'conflicts_resolved': 1
            },
            success=True
        )
        
        print(f"✨ Generated tech stack with {len(final_tech_stack)} technologies")
        return final_tech_stack
    
    async def demonstrate_real_time_monitoring(self):
        """Demonstrate real-time monitoring capabilities."""
        print("\n📈 Demonstrating real-time monitoring...")
        
        # Allow time for real-time processing
        await asyncio.sleep(2)
        
        # Get real-time metrics from tech monitor
        recent_metrics = self.tech_monitor._get_recent_metrics(hours=1)
        print(f"📊 Captured {len(recent_metrics)} real metrics")
        
        # Show metric types captured
        metric_types = set(metric.name for metric in recent_metrics)
        print(f"📋 Metric types: {', '.join(sorted(metric_types))}")
        
        # Get system health based on real data
        health_score = self.tech_monitor.get_system_health_score()
        print(f"💚 System health: {health_score['health_status']} (score: {health_score['overall_score']:.2f})")
        
        # Show active alerts
        alert_status = self.tech_monitor.get_alert_escalation_status()
        total_alerts = alert_status.get('total_alerts', 0)
        if total_alerts > 0:
            print(f"🚨 Active alerts: {total_alerts}")
            print(f"   - Critical: {alert_status.get('critical_alerts', 0)}")
            print(f"   - Errors: {alert_status.get('error_alerts', 0)}")
            print(f"   - Warnings: {alert_status.get('warning_alerts', 0)}")
        else:
            print("✅ No active alerts")
    
    async def demonstrate_quality_assurance(self):
        """Demonstrate quality assurance with real data."""
        print("\n🔍 Demonstrating quality assurance with real data...")
        
        # Run accuracy check with real data
        accuracy_check = await self.qa_system._check_accuracy()
        print(f"📊 Accuracy check: {accuracy_check.status.value} (score: {accuracy_check.score:.2f})")
        print(f"📈 Data source: {accuracy_check.details.get('data_source', 'unknown')}")
        
        if accuracy_check.recommendations:
            print("💡 Recommendations:")
            for rec in accuracy_check.recommendations[:2]:
                print(f"   - {rec}")
        
        # Show QA report summary
        latest_report = self.qa_system.get_latest_report()
        if latest_report:
            print(f"📋 Latest QA report: {latest_report.summary['health_status']} "
                  f"({latest_report.summary['passed']} passed, "
                  f"{latest_report.summary['failed']} failed)")
    
    async def demonstrate_performance_analytics(self):
        """Demonstrate performance analytics with real data."""
        print("\n⚡ Demonstrating performance analytics...")
        
        # Update system metrics (now includes real tech stack data)
        self.performance_monitor.update_system_metrics()
        
        # Get metrics summary
        metrics_summary = self.performance_monitor.get_metrics_summary()
        
        # Show real performance data
        gauges = metrics_summary['metrics']['gauges']
        
        if 'aaa_active_sessions' in gauges:
            print(f"👥 Active sessions: {gauges['aaa_active_sessions']}")
        
        if 'aaa_llm_request_duration_seconds' in gauges:
            duration = gauges['aaa_llm_request_duration_seconds']
            print(f"🤖 Average LLM response time: {duration:.2f}s")
        
        if 'aaa_memory_usage_percent' in gauges:
            memory = gauges['aaa_memory_usage_percent']
            print(f"💾 Memory usage: {memory:.1f}%")
        
        # Show active performance alerts
        active_alerts = metrics_summary.get('active_alerts', [])
        if active_alerts:
            print(f"⚠️ Performance alerts: {len(active_alerts)}")
        else:
            print("✅ No performance issues detected")
    
    async def demonstrate_dynamic_thresholds(self):
        """Demonstrate dynamic threshold adjustment based on real performance."""
        print("\n🎯 Demonstrating dynamic threshold adjustment...")
        
        # Show current thresholds
        current_thresholds = self.tech_monitor.alert_thresholds
        print("📊 Current alert thresholds:")
        for key, value in current_thresholds.items():
            print(f"   - {key}: {value}")
        
        # Trigger threshold update
        self.tech_monitor.update_alert_thresholds()
        
        # Show if thresholds changed
        updated_thresholds = self.tech_monitor.alert_thresholds
        changes = {}
        for key, new_value in updated_thresholds.items():
            old_value = current_thresholds.get(key, 0)
            if abs(new_value - old_value) > 0.001:
                changes[key] = {'old': old_value, 'new': new_value}
        
        if changes:
            print("🔄 Threshold updates based on real performance:")
            for key, change in changes.items():
                print(f"   - {key}: {change['old']:.3f} → {change['new']:.3f}")
        else:
            print("✅ Thresholds are optimal based on current performance")


async def main():
    """Run the real data monitoring demonstration."""
    print("🎯 Real Data Monitoring Integration Demo")
    print("=" * 50)
    
    demo = RealDataMonitoringDemo()
    
    try:
        # Start monitoring systems
        await demo.start_monitoring_systems()
        
        # Simulate real tech stack generation
        tech_stack = await demo.simulate_real_tech_stack_generation()
        
        # Demonstrate monitoring capabilities
        await demo.demonstrate_real_time_monitoring()
        await demo.demonstrate_quality_assurance()
        await demo.demonstrate_performance_analytics()
        await demo.demonstrate_dynamic_thresholds()
        
        print("\n🎉 Demo completed successfully!")
        print(f"📋 Final tech stack: {', '.join(tech_stack[:5])}{'...' if len(tech_stack) > 5 else ''}")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")
        raise
    
    finally:
        # Cleanup
        await demo.stop_monitoring_systems()
        print("\n👋 Demo cleanup completed")


if __name__ == "__main__":
    asyncio.run(main())