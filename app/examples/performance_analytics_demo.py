"""
Performance Analytics Demo

Demonstrates the comprehensive performance and usage analytics system
with real-time monitoring, bottleneck detection, and predictive insights.
"""

import asyncio
import json
import random
from datetime import datetime, timedelta
from typing import Dict, Any, List

from app.monitoring.performance_analytics import PerformanceAnalytics, BottleneckSeverity
from app.services.monitoring_integration_service import TechStackMonitoringIntegrationService


class PerformanceAnalyticsDemo:
    """Demo class for performance analytics system."""
    
    def __init__(self):
        self.analytics = PerformanceAnalytics({
            'analysis_interval_minutes': 1,  # Fast analysis for demo
            'bottleneck_detection_threshold': 0.6,
            'satisfaction_correlation_window_hours': 1,
            'prediction_confidence_threshold': 0.7,
            'max_stored_patterns': 200,
            'max_stored_bottlenecks': 100,
            'capacity_planning_horizon_days': 30
        })
        
        self.integration_service = TechStackMonitoringIntegrationService({
            'max_session_duration_hours': 2,
            'max_events_per_session': 200,
            'cleanup_interval_minutes': 30,
            'real_time_streaming': True,
            'buffer_size': 20
        })
    
    async def setup_demo(self):
        """Set up the demo environment."""
        print("🚀 Setting up Performance Analytics Demo...")
        
        # Start analytics system
        await self.analytics.start_analytics()
        
        # Start monitoring integration
        await self.integration_service.start_monitoring_integration()
        
        # Connect analytics to integration service
        self.integration_service.performance_analytics = self.analytics
        
        print("✅ Demo environment ready!")
        print()
    
    async def cleanup_demo(self):
        """Clean up demo resources."""
        print("\n🧹 Cleaning up demo environment...")
        await self.analytics.stop_analytics()
        await self.integration_service.stop_monitoring_integration()
        print("✅ Cleanup complete!")
    
    async def demonstrate_user_interaction_tracking(self):
        """Demonstrate user interaction tracking and pattern analysis."""
        print("👥 Demonstrating User Interaction Tracking...")
        print("=" * 50)
        
        # Simulate various user interactions
        user_segments = ['new_user', 'returning_user', 'power_user']
        interaction_types = ['session_start', 'tech_generation', 'pattern_matching', 'export', 'session_end']
        
        print("📊 Simulating user interactions...")
        
        for i in range(30):
            session_id = f"demo_session_{i % 8}"  # 8 different sessions
            user_segment = random.choice(user_segments)
            interaction_type = random.choice(interaction_types)
            
            interaction_data = {
                'feature': random.choice(['tech_stack_generation', 'pattern_analysis', 'diagram_export']),
                'requirements_count': random.randint(3, 15),
                'tech_stack_size': random.randint(5, 12),
                'processing_time': random.uniform(2.0, 8.0)
            }
            
            await self.analytics.track_user_interaction(
                session_id=session_id,
                user_segment=user_segment,
                interaction_type=interaction_type,
                interaction_data=interaction_data,
                timestamp=datetime.now() - timedelta(minutes=random.randint(0, 60))
            )
            
            if i % 10 == 9:
                print(f"  ✓ Tracked {i + 1} interactions")
        
        # Allow time for pattern analysis
        await asyncio.sleep(1)
        
        # Display results
        print(f"\n📈 Analysis Results:")
        print(f"  • Total interactions tracked: {len(self.analytics.user_interactions)}")
        print(f"  • Usage patterns detected: {len(self.analytics.usage_patterns)}")
        
        if self.analytics.usage_patterns:
            for pattern in self.analytics.usage_patterns[-3:]:  # Show last 3 patterns
                print(f"    - {pattern.pattern_type}: {pattern.metrics}")
        
        print()
    
    async def demonstrate_performance_bottleneck_detection(self):
        """Demonstrate performance bottleneck detection."""
        print("🔍 Demonstrating Performance Bottleneck Detection...")
        print("=" * 50)
        
        # Set up realistic baselines
        self.analytics.performance_baselines = {
            'response_time': {'mean': 4.0, 'median': 3.5, 'p95': 7.0, 'std': 1.5},
            'processing_time': {'mean': 2.5, 'median': 2.0, 'p95': 4.0, 'std': 1.0},
            'success_rate': {'mean': 0.95, 'std': 0.05},
            'accuracy': {'mean': 0.88, 'std': 0.08}
        }
        
        print("📊 Simulating performance metrics with bottlenecks...")
        
        components = ['LLMProvider', 'TechStackGenerator', 'TechnologyValidator', 'PatternMatcher']
        operations = ['generate_response', 'extract_technologies', 'validate_compatibility', 'match_patterns']
        
        # Simulate normal performance
        for i in range(20):
            component = random.choice(components)
            operation = random.choice(operations)
            
            await self.analytics.track_performance_metric(
                component=component,
                operation=operation,
                metric_name='response_time',
                metric_value=random.uniform(2.0, 6.0),  # Normal range
                context={'session_id': f'perf_session_{i}', 'model': 'gpt-4'},
                timestamp=datetime.now() - timedelta(minutes=random.randint(0, 30))
            )
        
        # Simulate performance bottlenecks
        bottleneck_scenarios = [
            {
                'component': 'LLMProvider',
                'operation': 'generate_response',
                'metric_name': 'response_time',
                'metric_value': 12.0,  # Way above p95
                'context': {'session_id': 'bottleneck_session_1', 'model': 'gpt-4', 'tokens': 2000}
            },
            {
                'component': 'TechStackGenerator',
                'operation': 'extract_technologies',
                'metric_name': 'processing_time',
                'metric_value': 8.5,  # Above p95
                'context': {'session_id': 'bottleneck_session_2', 'requirements_count': 20}
            },
            {
                'component': 'TechnologyValidator',
                'operation': 'validate_compatibility',
                'metric_name': 'success_rate',
                'metric_value': 0.65,  # Below baseline
                'context': {'session_id': 'bottleneck_session_3', 'tech_count': 15}
            },
            {
                'component': 'PatternMatcher',
                'operation': 'match_patterns',
                'metric_name': 'accuracy',
                'metric_value': 0.72,  # Below baseline
                'context': {'session_id': 'bottleneck_session_4', 'pattern_count': 50}
            }
        ]
        
        for scenario in bottleneck_scenarios:
            await self.analytics.track_performance_metric(**scenario)
            print(f"  ⚠️  Simulated bottleneck: {scenario['component']}.{scenario['operation']} - {scenario['metric_name']}: {scenario['metric_value']}")
        
        # Allow time for bottleneck detection
        await asyncio.sleep(1)
        
        # Display results
        print(f"\n🚨 Bottleneck Detection Results:")
        print(f"  • Total bottlenecks detected: {len(self.analytics.performance_bottlenecks)}")
        
        for bottleneck in self.analytics.performance_bottlenecks:
            print(f"    - {bottleneck.component}.{bottleneck.operation}")
            print(f"      Severity: {bottleneck.severity.value}")
            print(f"      Impact: {bottleneck.impact_analysis}")
            print(f"      Recommendations: {len(bottleneck.recommendations)} suggestions")
            if bottleneck.recommendations:
                print(f"        • {bottleneck.recommendations[0]}")
        
        print()
    
    async def demonstrate_user_satisfaction_correlation(self):
        """Demonstrate user satisfaction analysis and correlation with performance."""
        print("😊 Demonstrating User Satisfaction Analysis...")
        print("=" * 50)
        
        print("📊 Simulating user satisfaction data with performance correlation...")
        
        # Simulate sessions with varying performance and satisfaction
        satisfaction_scenarios = [
            {
                'session_id': 'satisfaction_session_1',
                'performance': {'response_time': 3.0, 'success_rate': 0.95, 'accuracy': 0.90},
                'satisfaction': {'relevance': 4.5, 'accuracy': 4.2, 'completeness': 4.0, 'speed': 4.3},
                'feedback': 'Excellent results, very fast and accurate!'
            },
            {
                'session_id': 'satisfaction_session_2',
                'performance': {'response_time': 8.0, 'success_rate': 0.90, 'accuracy': 0.85},
                'satisfaction': {'relevance': 3.8, 'accuracy': 3.5, 'completeness': 3.9, 'speed': 2.5},
                'feedback': 'Good results but took too long to generate'
            },
            {
                'session_id': 'satisfaction_session_3',
                'performance': {'response_time': 4.5, 'success_rate': 0.80, 'accuracy': 0.75},
                'satisfaction': {'relevance': 3.0, 'accuracy': 2.8, 'completeness': 3.2, 'speed': 3.5},
                'feedback': 'Results were not very accurate, missing some technologies'
            },
            {
                'session_id': 'satisfaction_session_4',
                'performance': {'response_time': 2.5, 'success_rate': 0.98, 'accuracy': 0.92},
                'satisfaction': {'relevance': 4.8, 'accuracy': 4.6, 'completeness': 4.4, 'speed': 4.7},
                'feedback': 'Perfect! Fast, accurate, and complete tech stack'
            }
        ]
        
        for scenario in satisfaction_scenarios:
            session_id = scenario['session_id']
            
            # Track performance metrics
            for metric_name, metric_value in scenario['performance'].items():
                await self.analytics.track_performance_metric(
                    component='TechStackGenerator',
                    operation='generate_stack',
                    metric_name=metric_name,
                    metric_value=metric_value,
                    context={'session_id': session_id}
                )
            
            # Track user satisfaction
            await self.analytics.track_user_satisfaction(
                session_id=session_id,
                satisfaction_scores=scenario['satisfaction'],
                feedback=scenario['feedback'],
                context={'tech_stack_size': random.randint(6, 10)}
            )
            
            print(f"  ✓ Session {session_id}: Satisfaction {sum(scenario['satisfaction'].values())/4:.1f}/5.0")
        
        # Display correlation analysis
        print(f"\n🔗 Satisfaction Correlation Analysis:")
        print(f"  • Total satisfaction analyses: {len(self.analytics.satisfaction_analyses)}")
        
        for analysis in self.analytics.satisfaction_analyses:
            print(f"    - Session: {analysis.analysis_id.split('_')[1]}")
            print(f"      Overall Score: {analysis.overall_score:.2f}/5.0")
            print(f"      Sentiment: {analysis.feedback_sentiment}")
            print(f"      Improvement Areas: {', '.join(analysis.improvement_areas) if analysis.improvement_areas else 'None'}")
            print(f"      Performance Correlations: {len(analysis.correlation_factors)} factors")
            if analysis.correlation_factors:
                for factor, value in analysis.correlation_factors.items():
                    print(f"        • {factor}: {value:.3f}")
        
        print()
    
    async def demonstrate_predictive_insights(self):
        """Demonstrate predictive analytics and capacity planning."""
        print("🔮 Demonstrating Predictive Analytics...")
        print("=" * 50)
        
        print("📊 Generating historical data for predictions...")
        
        # Generate historical usage data with trends
        current_time = datetime.now()
        
        # Simulate 14 days of usage data with growth trend
        for day in range(14):
            daily_interactions = 25 + day * 3 + random.randint(-5, 5)  # Growing usage with noise
            
            for interaction in range(daily_interactions):
                await self.analytics.track_user_interaction(
                    session_id=f'historical_session_{day}_{interaction}',
                    user_segment=random.choice(['new_user', 'returning_user', 'power_user']),
                    interaction_type=random.choice(['tech_generation', 'pattern_matching', 'export']),
                    interaction_data={'feature': f'feature_{interaction % 3}'},
                    timestamp=current_time - timedelta(days=14 - day, minutes=interaction * 2)
                )
        
        # Generate historical performance data with degradation trend
        for day in range(10):
            base_response_time = 3.5 + (day * 0.2) + random.uniform(-0.3, 0.3)  # Degrading trend
            
            for metric in range(20):
                await self.analytics.track_performance_metric(
                    component='TechStackGenerator',
                    operation='generate_stack',
                    metric_name='response_time',
                    metric_value=base_response_time + random.uniform(-0.5, 0.5),
                    context={'session_id': f'trend_session_{day}_{metric}'},
                    timestamp=current_time - timedelta(days=10 - day, minutes=metric * 20)
                )
        
        print("🔍 Generating predictive insights...")
        
        # Generate predictive insights
        await self.analytics._generate_predictive_insights()
        
        # Display results
        print(f"\n🎯 Predictive Insights Generated:")
        print(f"  • Total insights: {len(self.analytics.predictive_insights)}")
        
        for insight in self.analytics.predictive_insights:
            print(f"    - Type: {insight.insight_type}")
            print(f"      Horizon: {insight.prediction_horizon}")
            print(f"      Confidence: {insight.confidence_score:.2f}")
            print(f"      Predictions:")
            for metric, value in insight.predicted_metrics.items():
                if isinstance(value, (int, float)):
                    print(f"        • {metric}: {value:.2f}")
                else:
                    print(f"        • {metric}: {value}")
            print(f"      Recommendations: {len(insight.recommendations)} items")
            if insight.recommendations:
                for rec in insight.recommendations[:2]:  # Show first 2
                    print(f"        • {rec}")
            print()
    
    async def demonstrate_real_time_monitoring_integration(self):
        """Demonstrate integration with real-time monitoring system."""
        print("⚡ Demonstrating Real-Time Monitoring Integration...")
        print("=" * 50)
        
        print("🔄 Simulating tech stack generation workflow with monitoring...")
        
        # Start a monitoring session
        requirements = {
            'technologies': ['AWS', 'Python', 'FastAPI'],
            'domain': 'web_application',
            'requirements_count': 8
        }
        
        session = self.integration_service.start_generation_monitoring(
            requirements=requirements,
            metadata={'user_type': 'power_user', 'complexity': 'medium'}
        )
        
        print(f"  ✓ Started monitoring session: {session.session_id}")
        
        # Simulate parsing step
        await self.integration_service.track_parsing_step(
            session_id=session.session_id,
            step_name='extract_explicit_technologies',
            input_data={'requirements': requirements},
            output_data={
                'explicit_technologies': ['AWS Lambda', 'Python', 'FastAPI'],
                'context_clues': ['serverless', 'api', 'python']
            },
            duration_ms=1500,
            success=True
        )
        
        print("  ✓ Tracked parsing step")
        
        # Simulate LLM interaction
        await self.integration_service.track_llm_interaction(
            session_id=session.session_id,
            provider='openai',
            model='gpt-4',
            prompt_data={'prompt_length': 800, 'context_size': 3},
            response_data={'response_length': 400, 'tech_count': 10},
            token_usage={'prompt_tokens': 600, 'completion_tokens': 300, 'total_tokens': 900},
            duration_ms=5200,
            success=True
        )
        
        print("  ✓ Tracked LLM interaction")
        
        # Simulate validation step
        await self.integration_service.track_validation_step(
            session_id=session.session_id,
            validation_type='ecosystem_consistency',
            input_technologies=['AWS Lambda', 'Python', 'FastAPI', 'PostgreSQL', 'Redis'],
            validation_results={'consistency_score': 0.92, 'conflicts': 0},
            conflicts_detected=[],
            resolutions_applied=[],
            duration_ms=800,
            success=True
        )
        
        print("  ✓ Tracked validation step")
        
        # Complete the session
        final_tech_stack = ['AWS Lambda', 'Python', 'FastAPI', 'PostgreSQL', 'Redis', 'AWS API Gateway']
        await self.integration_service.complete_generation_monitoring(
            session_id=session.session_id,
            final_tech_stack=final_tech_stack,
            generation_metrics={
                'total_time': 7.5,
                'accuracy': 0.92,
                'explicit_tech_inclusion': 1.0,
                'catalog_hits': 6,
                'catalog_misses': 0
            },
            success=True
        )
        
        print("  ✓ Completed monitoring session")
        
        # Allow time for data processing
        await asyncio.sleep(1)
        
        # Show analytics data
        print(f"\n📊 Real-Time Analytics Data:")
        print(f"  • Performance metrics collected: {len(self.analytics.performance_metrics)}")
        print(f"  • User interactions tracked: {len(self.analytics.user_interactions)}")
        
        # Show recent metrics
        recent_metrics = list(self.analytics.performance_metrics)[-5:]  # Last 5 metrics
        for metric in recent_metrics:
            print(f"    - {metric['component']}.{metric['operation']}: {metric['metric_name']} = {metric['metric_value']}")
        
        print()
    
    async def demonstrate_analytics_reporting(self):
        """Demonstrate comprehensive analytics reporting."""
        print("📋 Demonstrating Analytics Reporting...")
        print("=" * 50)
        
        print("📊 Generating comprehensive analytics report...")
        
        # Generate report for the last hour
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=1)
        
        report = await self.analytics.generate_analytics_report((start_time, end_time))
        
        print(f"\n📈 Analytics Report Summary:")
        print(f"  • Report ID: {report.report_id}")
        print(f"  • Time Period: {report.time_period[0].strftime('%H:%M')} - {report.time_period[1].strftime('%H:%M')}")
        print(f"  • Generated At: {report.generated_at.strftime('%Y-%m-%d %H:%M:%S')}")
        
        print(f"\n📊 Summary Metrics:")
        for metric, value in report.summary_metrics.items():
            if isinstance(value, float):
                print(f"    • {metric}: {value:.2f}")
            else:
                print(f"    • {metric}: {value}")
        
        print(f"\n🎯 Key Findings:")
        print(f"  • Usage Patterns: {len(report.usage_patterns)} detected")
        print(f"  • Performance Bottlenecks: {len(report.performance_bottlenecks)} identified")
        print(f"  • Satisfaction Analyses: {len(report.satisfaction_analysis)} completed")
        print(f"  • Predictive Insights: {len(report.predictive_insights)} generated")
        
        if report.recommendations:
            print(f"\n💡 Recommendations:")
            for i, rec in enumerate(report.recommendations[:3], 1):  # Show first 3
                print(f"    {i}. {rec}")
        
        # Export report
        export_file = f"analytics_report_{int(datetime.now().timestamp())}.json"
        self.analytics.export_analytics_data(export_file)
        print(f"\n💾 Report exported to: {export_file}")
        
        print()
    
    async def demonstrate_system_health_dashboard(self):
        """Demonstrate system health monitoring dashboard."""
        print("🏥 Demonstrating System Health Dashboard...")
        print("=" * 50)
        
        # Get current analytics summary
        summary = self.analytics.get_analytics_summary()
        
        print("📊 System Health Dashboard:")
        print("=" * 30)
        
        # System Status
        print(f"🟢 System Status: {'Running' if summary['system_status']['analytics_running'] else 'Stopped'}")
        
        # Data Points
        data_points = summary['system_status']['data_points']
        print(f"📈 Data Collection:")
        print(f"  • User Interactions: {data_points['user_interactions']:,}")
        print(f"  • Performance Metrics: {data_points['performance_metrics']:,}")
        print(f"  • System Metrics: {data_points['system_metrics']:,}")
        
        # Recent Activity
        recent_summary = summary['summary']
        print(f"\n⏰ Recent Activity (Last Hour):")
        print(f"  • Usage Patterns: {recent_summary['recent_usage_patterns']}")
        print(f"  • Performance Bottlenecks: {recent_summary['recent_bottlenecks']}")
        print(f"  • Satisfaction Analyses: {recent_summary['recent_satisfaction_analyses']}")
        print(f"  • Predictive Insights: {recent_summary['recent_predictive_insights']}")
        
        # Performance Baselines
        if summary['baselines']['performance']:
            print(f"\n📏 Performance Baselines:")
            for metric, baseline in summary['baselines']['performance'].items():
                if isinstance(baseline, dict) and 'mean' in baseline:
                    print(f"  • {metric}: {baseline['mean']:.2f} ± {baseline.get('std', 0):.2f}")
        
        # Usage Baselines
        if summary['baselines']['usage']:
            print(f"\n👥 Usage Baselines:")
            for metric, baseline in summary['baselines']['usage'].items():
                if isinstance(baseline, dict):
                    for sub_metric, value in baseline.items():
                        print(f"  • {metric}.{sub_metric}: {value:.2f}")
        
        # Health Indicators
        print(f"\n🎯 Health Indicators:")
        
        # Calculate health scores
        total_bottlenecks = recent_summary['total_bottlenecks']
        critical_bottlenecks = len([
            b for b in self.analytics.performance_bottlenecks 
            if b.severity == BottleneckSeverity.CRITICAL
        ])
        
        if total_bottlenecks == 0:
            bottleneck_health = "🟢 Excellent"
        elif critical_bottlenecks > 0:
            bottleneck_health = "🔴 Critical"
        elif total_bottlenecks > 5:
            bottleneck_health = "🟡 Warning"
        else:
            bottleneck_health = "🟢 Good"
        
        print(f"  • Performance Health: {bottleneck_health}")
        
        # User satisfaction health
        if self.analytics.satisfaction_analyses:
            avg_satisfaction = sum(s.overall_score for s in self.analytics.satisfaction_analyses) / len(self.analytics.satisfaction_analyses)
            if avg_satisfaction >= 4.0:
                satisfaction_health = "🟢 Excellent"
            elif avg_satisfaction >= 3.5:
                satisfaction_health = "🟢 Good"
            elif avg_satisfaction >= 3.0:
                satisfaction_health = "🟡 Fair"
            else:
                satisfaction_health = "🔴 Poor"
            
            print(f"  • User Satisfaction: {satisfaction_health} ({avg_satisfaction:.1f}/5.0)")
        else:
            print(f"  • User Satisfaction: ⚪ No Data")
        
        # System load health
        data_load = data_points['user_interactions'] + data_points['performance_metrics']
        if data_load < 100:
            load_health = "🟢 Light"
        elif data_load < 500:
            load_health = "🟡 Moderate"
        else:
            load_health = "🔴 Heavy"
        
        print(f"  • System Load: {load_health} ({data_load:,} data points)")
        
        print()
    
    async def run_comprehensive_demo(self):
        """Run the complete performance analytics demo."""
        try:
            await self.setup_demo()
            
            print("🎬 Starting Comprehensive Performance Analytics Demo")
            print("=" * 60)
            print()
            
            # Run all demonstrations
            await self.demonstrate_user_interaction_tracking()
            await asyncio.sleep(1)
            
            await self.demonstrate_performance_bottleneck_detection()
            await asyncio.sleep(1)
            
            await self.demonstrate_user_satisfaction_correlation()
            await asyncio.sleep(1)
            
            await self.demonstrate_predictive_insights()
            await asyncio.sleep(1)
            
            await self.demonstrate_real_time_monitoring_integration()
            await asyncio.sleep(1)
            
            await self.demonstrate_analytics_reporting()
            await asyncio.sleep(1)
            
            await self.demonstrate_system_health_dashboard()
            
            print("🎉 Performance Analytics Demo Complete!")
            print("=" * 60)
            print()
            print("Key Features Demonstrated:")
            print("✅ Real-time user interaction tracking")
            print("✅ Performance bottleneck detection")
            print("✅ User satisfaction correlation analysis")
            print("✅ Predictive analytics and capacity planning")
            print("✅ Monitoring system integration")
            print("✅ Comprehensive analytics reporting")
            print("✅ System health monitoring dashboard")
            print()
            
        except Exception as e:
            print(f"❌ Demo error: {e}")
            import traceback
            traceback.print_exc()
        
        finally:
            await self.cleanup_demo()


async def main():
    """Run the performance analytics demo."""
    demo = PerformanceAnalyticsDemo()
    await demo.run_comprehensive_demo()


if __name__ == "__main__":
    asyncio.run(main())