"""
Real-Time Quality Monitor Demo

Demonstrates the capabilities of the RealTimeQualityMonitor including:
- Live quality assessment during tech stack generation
- Ecosystem consistency checking with real-time alerts
- User satisfaction prediction
- Quality trend analysis and degradation detection
"""

import asyncio
from datetime import datetime, timedelta

from app.monitoring.real_time_quality_monitor import (
    RealTimeQualityMonitor,
    QualityMetricType
)


class RealTimeQualityMonitorDemo:
    """Demo class for RealTimeQualityMonitor capabilities."""
    
    def __init__(self):
        """Initialize the demo."""
        self.quality_monitor = RealTimeQualityMonitor({
            'monitoring_enabled': True,
            'real_time_update_interval': 5,  # Fast updates for demo
            'alert_thresholds': {
                QualityMetricType.EXTRACTION_ACCURACY: 0.85,
                QualityMetricType.ECOSYSTEM_CONSISTENCY: 0.90,
                QualityMetricType.TECHNOLOGY_INCLUSION: 0.70,
                QualityMetricType.USER_SATISFACTION: 0.75
            }
        })
    
    async def run_demo(self):
        """Run the complete demo."""
        print("🔍 Real-Time Quality Monitor Demo")
        print("=" * 50)
        
        # Start monitoring
        await self.quality_monitor.start_real_time_monitoring()
        
        try:
            # Demo 1: Extraction Quality Validation
            await self.demo_extraction_quality_validation()
            
            # Demo 2: Ecosystem Consistency Checking
            await self.demo_ecosystem_consistency_checking()
            
            # Demo 3: User Satisfaction Prediction
            await self.demo_user_satisfaction_prediction()
            
            # Demo 4: Real-Time Alerting
            await self.demo_real_time_alerting()
            
            # Demo 5: Quality Trend Analysis
            await self.demo_quality_trend_analysis()
            
            # Demo 6: Monitoring Status and Metrics
            await self.demo_monitoring_status()
            
        finally:
            # Stop monitoring
            await self.quality_monitor.stop_real_time_monitoring()
    
    async def demo_extraction_quality_validation(self):
        """Demonstrate extraction quality validation."""
        print("\n📊 Demo 1: Extraction Quality Validation")
        print("-" * 40)
        
        test_scenarios = [
            {
                'name': 'High Quality Extraction',
                'extracted_techs': ['FastAPI', 'PostgreSQL', 'Redis', 'Docker'],
                'requirements': 'Build a REST API using FastAPI framework with PostgreSQL database, Redis for caching, and Docker for containerization'
            },
            {
                'name': 'Partial Extraction',
                'extracted_techs': ['FastAPI'],
                'requirements': 'Build a comprehensive web application with FastAPI, PostgreSQL, Redis, Docker, and authentication'
            },
            {
                'name': 'Poor Quality Extraction',
                'extracted_techs': ['UnknownTech1', 'UnknownTech2'],
                'requirements': 'Build a simple web API'
            }
        ]
        
        for scenario in test_scenarios:
            print(f"\n🔍 Testing: {scenario['name']}")
            
            quality_score = await self.quality_monitor.validate_extraction_quality(
                extracted_techs=scenario['extracted_techs'],
                requirements=scenario['requirements'],
                session_id=f"demo_{scenario['name'].lower().replace(' ', '_')}"
            )
            
            print(f"   Overall Score: {quality_score.overall_score:.2f}")
            print(f"   Confidence: {quality_score.confidence:.2f}")
            print("   Component Scores:")
            for component, score in quality_score.component_scores.items():
                print(f"     - {component}: {score:.2f}")
            
            # Check if alert was generated
            recent_alerts = [
                alert for alert in self.quality_monitor.quality_alerts
                if alert.session_id == quality_score.session_id
            ]
            
            if recent_alerts:
                alert = recent_alerts[-1]
                print(f"   🚨 Alert Generated: {alert.severity.value.upper()} - {alert.message}")
    
    async def demo_ecosystem_consistency_checking(self):
        """Demonstrate ecosystem consistency checking."""
        print("\n🏗️ Demo 2: Ecosystem Consistency Checking")
        print("-" * 40)
        
        test_stacks = [
            {
                'name': 'Consistent AWS Stack',
                'tech_stack': ['AWS Lambda', 'Amazon S3', 'Amazon RDS', 'AWS CloudFormation']
            },
            {
                'name': 'Mixed Cloud Stack',
                'tech_stack': ['AWS Lambda', 'Azure Functions', 'Google Cloud Storage', 'PostgreSQL']
            },
            {
                'name': 'Open Source Stack',
                'tech_stack': ['Docker', 'Kubernetes', 'PostgreSQL', 'Redis', 'Nginx']
            }
        ]
        
        for stack_info in test_stacks:
            print(f"\n🔍 Testing: {stack_info['name']}")
            
            consistency_score = await self.quality_monitor.check_ecosystem_consistency(
                tech_stack=stack_info['tech_stack'],
                session_id=f"demo_{stack_info['name'].lower().replace(' ', '_')}"
            )
            
            print(f"   Consistency Score: {consistency_score.consistency_score:.2f}")
            print(f"   Detected Ecosystem: {consistency_score.ecosystem_detected}")
            print(f"   Confidence: {consistency_score.confidence:.2f}")
            
            if consistency_score.inconsistencies:
                print(f"   🚨 Inconsistencies Found: {len(consistency_score.inconsistencies)}")
                for inconsistency in consistency_score.inconsistencies[:2]:  # Show first 2
                    print(f"     - {inconsistency['technology']}: conflicts with {inconsistency['conflicting_ecosystems']}")
            
            if consistency_score.recommendations:
                print("   💡 Recommendations:")
                for rec in consistency_score.recommendations[:2]:  # Show first 2
                    print(f"     - {rec}")
    
    async def demo_user_satisfaction_prediction(self):
        """Demonstrate user satisfaction prediction."""
        print("\n😊 Demo 3: User Satisfaction Prediction")
        print("-" * 40)
        
        test_results = [
            {
                'name': 'Excellent Result',
                'result': {
                    'tech_stack': ['FastAPI', 'PostgreSQL', 'Redis', 'Docker'],
                    'generation_metrics': {
                        'explicit_inclusion_rate': 0.95,
                        'catalog_coverage': 0.98,
                        'missing_technologies': 0
                    },
                    'processing_time': 5.2
                },
                'feedback': {'relevance': 5.0, 'accuracy': 4.8, 'completeness': 4.9}
            },
            {
                'name': 'Average Result',
                'result': {
                    'tech_stack': ['FastAPI', 'PostgreSQL'],
                    'generation_metrics': {
                        'explicit_inclusion_rate': 0.7,
                        'catalog_coverage': 0.8,
                        'missing_technologies': 2
                    },
                    'processing_time': 15.0
                },
                'feedback': {'relevance': 3.5, 'accuracy': 3.8, 'completeness': 3.2}
            },
            {
                'name': 'Poor Result',
                'result': {
                    'tech_stack': ['UnknownTech'],
                    'generation_metrics': {
                        'explicit_inclusion_rate': 0.3,
                        'catalog_coverage': 0.4,
                        'missing_technologies': 5
                    },
                    'processing_time': 45.0
                },
                'feedback': {'relevance': 2.0, 'accuracy': 2.2, 'completeness': 1.8}
            }
        ]
        
        for result_info in test_results:
            print(f"\n🔍 Testing: {result_info['name']}")
            
            satisfaction_score = await self.quality_monitor.calculate_user_satisfaction_score(
                result=result_info['result'],
                feedback=result_info['feedback'],
                session_id=f"demo_{result_info['name'].lower().replace(' ', '_')}"
            )
            
            print(f"   Predicted Satisfaction: {satisfaction_score:.2f}")
            print(f"   Actual Feedback Average: {sum(result_info['feedback'].values()) / len(result_info['feedback']):.2f}")
            print(f"   Processing Time: {result_info['result']['processing_time']:.1f}s")
            print(f"   Tech Stack Size: {len(result_info['result']['tech_stack'])}")
    
    async def demo_real_time_alerting(self):
        """Demonstrate real-time alerting system."""
        print("\n🚨 Demo 4: Real-Time Alerting System")
        print("-" * 40)
        
        print("\nGenerating scenarios that trigger alerts...")
        
        # Generate low-quality scenarios
        await self.quality_monitor.validate_extraction_quality(
            extracted_techs=[],
            requirements='Build a complex microservices architecture with multiple databases and caching layers',
            session_id='alert_demo_1'
        )
        
        await self.quality_monitor.check_ecosystem_consistency(
            tech_stack=['AWS Lambda', 'Azure Functions', 'Google Cloud Storage', 'IBM Watson'],
            session_id='alert_demo_2'
        )
        
        await self.quality_monitor.calculate_user_satisfaction_score(
            result={
                'tech_stack': ['UnknownFramework'],
                'generation_metrics': {'explicit_inclusion_rate': 0.1, 'catalog_coverage': 0.2},
                'processing_time': 60.0
            },
            session_id='alert_demo_3'
        )
        
        # Show generated alerts
        active_alerts = self.quality_monitor.get_active_alerts()
        
        print(f"\n📊 Generated {len(active_alerts)} alerts:")
        
        for alert in active_alerts[-5:]:  # Show last 5 alerts
            print(f"   🚨 {alert['severity'].upper()}: {alert['message']}")
            print(f"      Metric: {alert['metric_type']}")
            print(f"      Current: {alert['current_value']:.2f}, Threshold: {alert['threshold_value']:.2f}")
            print(f"      Session: {alert['session_id']}")
            print()
        
        # Demonstrate alert resolution
        if active_alerts:
            first_alert = active_alerts[0]
            print(f"🔧 Resolving alert: {first_alert['alert_id']}")
            
            resolved = await self.quality_monitor.resolve_alert(first_alert['alert_id'])
            print(f"   Resolution successful: {resolved}")
    
    async def demo_quality_trend_analysis(self):
        """Demonstrate quality trend analysis."""
        print("\n📈 Demo 5: Quality Trend Analysis")
        print("-" * 40)
        
        print("Generating historical data for trend analysis...")
        
        # Generate declining trend data
        base_time = datetime.now() - timedelta(hours=2)
        
        for i in range(15):
            # Simulate declining extraction accuracy
            score_value = 0.95 - (i * 0.03)  # Declining from 0.95 to 0.50
            
            quality_score = await self.quality_monitor.validate_extraction_quality(
                extracted_techs=['FastAPI'] if score_value > 0.7 else [],
                requirements='Build a web API',
                session_id=f'trend_demo_{i}'
            )
            
            # Override score and timestamp for controlled demo
            quality_score.overall_score = max(0.1, score_value)
            quality_score.timestamp = base_time + timedelta(minutes=i * 8)
            
            # Manually store for trend analysis
            self.quality_monitor.quality_scores.append(quality_score)
        
        # Analyze trend
        trend = await self.quality_monitor._analyze_quality_trend(QualityMetricType.EXTRACTION_ACCURACY)
        
        if trend:
            print("\n📊 Trend Analysis Results:")
            print(f"   Metric: {trend.metric_type.value}")
            print(f"   Direction: {trend.trend_direction}")
            print(f"   Strength: {trend.trend_strength:.2f}")
            print(f"   Change Rate: {trend.change_rate:.2f}")
            print(f"   Current Average: {trend.current_average:.2f}")
            print(f"   Previous Average: {trend.previous_average:.2f}")
            print(f"   Data Points: {trend.data_points}")
            
            # Check if degradation alert was created
            if trend.trend_direction == 'declining' and trend.trend_strength > 0.5:
                await self.quality_monitor._create_degradation_alert(trend)
                print("   🚨 Degradation alert created due to strong declining trend")
        else:
            print("   No trend data available (insufficient data points)")
    
    async def demo_monitoring_status(self):
        """Demonstrate monitoring status and metrics."""
        print("\n📊 Demo 6: Monitoring Status and Metrics")
        print("-" * 40)
        
        # Get current quality status
        status = self.quality_monitor.get_current_quality_status()
        
        print(f"Overall Status: {status['overall_status'].upper()}")
        print(f"Monitoring Enabled: {status['monitoring_enabled']}")
        print(f"Active Alerts: {status['active_alerts']}")
        print(f"Last Updated: {status['last_updated']}")
        
        print("\n📈 Quality Metrics:")
        for metric_name, metric_data in status['metrics'].items():
            print(f"   {metric_name}:")
            print(f"     Status: {metric_data['status']}")
            if metric_data['current_score'] is not None:
                print(f"     Score: {metric_data['current_score']:.2f}")
            print(f"     Threshold: {metric_data['threshold']:.2f}")
            print(f"     Samples: {metric_data['sample_count']}")
        
        # Get quality trends
        trends = self.quality_monitor.get_quality_trends()
        
        if trends['trends']:
            print("\n📊 Quality Trends:")
            for trend_name, trend_data in trends['trends'].items():
                print(f"   {trend_name}:")
                print(f"     Direction: {trend_data['trend_direction']}")
                print(f"     Strength: {trend_data['trend_strength']:.2f}")
                print(f"     Change: {trend_data['change_rate']:.2f}")
        
        # Show alert summary
        all_alerts = self.quality_monitor.get_active_alerts()
        
        if all_alerts:
            print("\n🚨 Alert Summary:")
            severity_counts = {}
            for alert in all_alerts:
                severity = alert['severity']
                severity_counts[severity] = severity_counts.get(severity, 0) + 1
            
            for severity, count in severity_counts.items():
                print(f"   {severity.upper()}: {count}")
        
        print("\n📊 System Statistics:")
        print(f"   Total Quality Scores: {len(self.quality_monitor.quality_scores)}")
        print(f"   Total Consistency Scores: {len(self.quality_monitor.consistency_scores)}")
        print(f"   Total Alerts Generated: {len(self.quality_monitor.quality_alerts)}")
        print(f"   Active Monitoring Tasks: {self.quality_monitor.is_monitoring}")


async def main():
    """Run the real-time quality monitor demo."""
    demo = RealTimeQualityMonitorDemo()
    
    try:
        await demo.run_demo()
        
        print("\n" + "=" * 50)
        print("✅ Real-Time Quality Monitor Demo Complete!")
        print("=" * 50)
        
        print("\n🎯 Key Features Demonstrated:")
        features = [
            "✅ Live quality assessment during tech stack generation",
            "✅ Ecosystem consistency checking with real-time alerts",
            "✅ User satisfaction prediction based on generation results",
            "✅ Quality threshold monitoring with automatic alerting",
            "✅ Quality trend analysis and degradation detection",
            "✅ Comprehensive monitoring status and metrics reporting",
            "✅ Alert management and resolution capabilities"
        ]
        
        for feature in features:
            print(f"   {feature}")
        
        print("\n💡 Next Steps:")
        next_steps = [
            "• Integrate with tech stack generation workflow",
            "• Connect to external alerting systems (email, Slack)",
            "• Add machine learning for improved satisfaction prediction",
            "• Implement custom quality metrics for specific domains",
            "• Add monitoring dashboard visualization",
            "• Configure quality thresholds based on business requirements"
        ]
        
        for step in next_steps:
            print(f"   {step}")
        
    except Exception as e:
        print(f"\n❌ Demo failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    asyncio.run(main())